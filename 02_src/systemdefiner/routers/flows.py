"""Flow routes (list/new/edit/delete) and the flow-data editor.

Two routers because the original ``main.py`` declared the flow-data routes at
the very end of the route table — ``flow_data_router`` is included last in
``main.py`` to keep the registration order identical.

Moved verbatim from ``main.py``.
"""
from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from systemdefiner import storage
from systemdefiner.cascades import (
    _next_flow_id,
    _process_name,
    _purge_flow_references,
    _rename_flow_id,
)
from systemdefiner.consistency import FLOW_ID_CONVENTION, input_substitution_residual_flow
from systemdefiner.deps import _ctx, templates
from systemdefiner.forms import _g
from systemdefiner.models.config_schema import (
    CaseStudyConfig,
    Flow,
    FlowDataEntry,
    ProcessLogic,
)

router = APIRouter()


def _convention_mismatch(fid: str, from_p: int, to_p: int) -> str | None:
    """Reject convention-shaped IDs (``F_<a>_<b>[_N]``) that name endpoints
    other than the flow's real ones — such IDs disguise the topology and can
    hide duplicate edges."""
    m = FLOW_ID_CONVENTION.fullmatch(fid)
    if m and (int(m.group(1)) != from_p or int(m.group(2)) != to_p):
        return (
            f"Flow ID '{fid}' names P{int(m.group(1))}→P{int(m.group(2))} but the "
            f"flow is wired P{from_p}→P{to_p}. Leave the ID blank to auto-generate "
            f"it, or choose a name that doesn't look like F_<from>_<to>."
        )
    return None


def _input_flows(cfg: CaseStudyConfig):
    """Return flows eligible for the flow_data (Input Flow Time Series) editor:
    outflows of plain Input processes, plus the discovered "virgin/residual"
    outflow of Input_Substitution processes — Input_Substitution is a drop-in
    variant of Input, and its demand target comes from the same flow_data
    mechanism rather than a bespoke field."""
    input_pids = {p.id for p in cfg.processes if p.logic == ProcessLogic.input}
    flows = [f for f in cfg.flows if f.from_process in input_pids]
    seen = {f.id for f in flows}
    for p in cfg.processes:
        if p.logic != ProcessLogic.input_substitution:
            continue
        residual = input_substitution_residual_flow(cfg, p)
        if residual is not None and residual.id not in seen:
            flows.append(residual)
            seen.add(residual.id)
    return flows


def _drop_stranded_flow_entries(cfg, flow_id: str) -> None:
    """Remove flow_data / composition entries for a flow that's no longer
    reachable as an Input-like outflow — the editors can't reach them
    anymore, but the engine would still apply them (phantom prescribed
    values)."""
    fl = next((f for f in cfg.flows if f.id == flow_id), None)
    if fl is None:
        return
    if fl.from_process == 0 or flow_id in {f.id for f in _input_flows(cfg)}:
        return
    cfg.flow_data = [fd for fd in cfg.flow_data if fd.flow_id != flow_id]
    cfg.flow_compositions = [
        fc for fc in cfg.flow_compositions if fc.flow_id != flow_id
    ]


@router.get("/{name}/flows")
async def flows_list(request: Request, name: str):
    cfg = storage.load_case_study(name)
    return templates.TemplateResponse(request, "flows.html", _ctx(cfg=cfg))


@router.post("/{name}/flows/new")
async def flow_new(request: Request, name: str):
    form = await request.form()
    cfg = storage.load_case_study(name)

    from_p = int(form.get("from_process", 0))
    to_p = int(form.get("to_process", 0))

    # Manual ID overrides; blank → auto-generate F_{from}_{to}.
    requested = _g(form, "id")
    if requested and any(str(f.id) == requested for f in cfg.flows):
        return templates.TemplateResponse(
            request,
            "flows.html",
            _ctx(cfg=cfg, flow_error=f"Flow ID '{requested}' already exists."),
            status_code=400,
        )
    if requested and (msg := _convention_mismatch(requested, from_p, to_p)):
        return templates.TemplateResponse(
            request,
            "flows.html",
            _ctx(cfg=cfg, flow_error=msg),
            status_code=400,
        )
    flow_id = requested or _next_flow_id(cfg, from_p, to_p)

    # Blank name → "{from process}_{to process}".
    flow_name = (
        _g(form, "name") or f"{_process_name(cfg, from_p)}_{_process_name(cfg, to_p)}"
    )

    flow = Flow(
        id=flow_id,
        name=flow_name,
        from_process=from_p,
        to_process=to_p,
    )
    cfg.flows.append(flow)
    storage.save_case_study(cfg)
    return RedirectResponse(f"/{name}/flows", status_code=303)


@router.get("/{name}/flows/{fid}/edit")
async def flow_edit_form(request: Request, name: str, fid: str):
    cfg = storage.load_case_study(name)
    flow = next((f for f in cfg.flows if f.id == fid), None)
    if not flow:
        raise HTTPException(404)
    return templates.TemplateResponse(
        request, "flow_edit.html", _ctx(cfg=cfg, flow=flow)
    )


@router.post("/{name}/flows/{fid}/edit")
async def flow_edit_save(request: Request, name: str, fid: str):
    form = await request.form()
    cfg = storage.load_case_study(name)
    flow = next((f for f in cfg.flows if f.id == fid), None)
    if not flow:
        raise HTTPException(404)

    old_from, old_to = flow.from_process, flow.to_process
    new_from = int(form.get("from_process", flow.from_process))
    new_to = int(form.get("to_process", flow.to_process))

    # Flow ID is editable; a change cascades to all references.
    new_id = _g(form, "id") or fid
    id_edited_by_user = new_id != fid
    if id_edited_by_user:
        if not re.fullmatch(r"[A-Za-z0-9_\-]+", new_id):
            return templates.TemplateResponse(
                request,
                "flow_edit.html",
                _ctx(
                    cfg=cfg,
                    flow=flow,
                    flow_error="Invalid Flow ID — letters, numbers, underscores and dashes only.",
                ),
                status_code=400,
            )
        if any(str(f.id) == new_id for f in cfg.flows if f is not flow):
            return templates.TemplateResponse(
                request,
                "flow_edit.html",
                _ctx(
                    cfg=cfg, flow=flow, flow_error=f"Flow ID '{new_id}' already exists."
                ),
                status_code=400,
            )
        if msg := _convention_mismatch(new_id, new_from, new_to):
            return templates.TemplateResponse(
                request,
                "flow_edit.html",
                _ctx(cfg=cfg, flow=flow, flow_error=msg),
                status_code=400,
            )
        _rename_flow_id(cfg, fid, new_id)
        flow.id = new_id

    flow.name = form.get("name", flow.name)
    flow.from_process = new_from
    flow.to_process = new_to

    # Auto-sync the auto-generated ``F_<from>_<to>`` ID when the endpoints
    # change, so the ID can never silently drift from the actual source/target.
    # The solver builds the flow graph from from_process/to_process — the ID is
    # only a label — so a stale ID (e.g. F_09_17 wired 12→17) disguises the real
    # topology and can hide duplicate edges. Only re-derive when the user did
    # NOT type a custom ID this save AND the current ID is still the convention
    # ID for the *old* endpoints (``F_<old_from>_<old_to>`` with an optional
    # ``_N`` duplicate suffix). Deliberately custom IDs are left untouched.
    # Collision-safe: a second flow between the same processes becomes
    # ``F_<from>_<to>_2``, which surfaces genuine duplicate edges instead of
    # hiding them.
    if not id_edited_by_user and (new_from != old_from or new_to != old_to):
        old_base = f"F_{old_from:02d}_{old_to:02d}"
        if flow.id == old_base or re.fullmatch(re.escape(old_base) + r"_\d+", flow.id):
            synced = _next_flow_id(cfg, new_from, new_to)
            if synced != flow.id:
                _rename_flow_id(cfg, flow.id, synced)
                flow.id = synced

    # TC ownership follows the flow's source. Without this, the TC keeps its
    # old process_id, the new source's TC page shows the flow as TC-less, and
    # a later edit there leaves two TC rows exporting the same derived name —
    # the loader keeps the first (stale) value with only a console warning.
    if new_from != old_from:
        for tc in cfg.transfer_coefficients:
            if tc.flow_id == flow.id and tc.process_id == old_from:
                tc.process_id = new_from

    # If the rewire moved the flow off an Input process, its flow data and
    # composition become unreachable in the editors — drop them rather than
    # letting them silently prescribe an internal flow.
    if new_from != old_from:
        _drop_stranded_flow_entries(cfg, flow.id)

    storage.save_case_study(cfg)
    return RedirectResponse(f"/{name}/flows", status_code=303)


@router.post("/{name}/flows/{fid}/delete")
async def flow_delete(name: str, fid: str):
    cfg = storage.load_case_study(name)
    cfg.flows = [f for f in cfg.flows if f.id != fid]
    _purge_flow_references(cfg, {fid})
    storage.save_case_study(cfg)
    return RedirectResponse(f"/{name}/flows", status_code=303)


# ── Flow Data (input time series) ──────────────────────────────────────────

flow_data_router = APIRouter()


@flow_data_router.get("/{name}/flow_data")
async def get_flow_data(request: Request, name: str, saved: bool = False):
    cfg = storage.load_case_study(name)
    flows = _input_flows(cfg)
    flow_data_map = {
        fd.flow_id: dict(sorted(fd.values.items())) for fd in cfg.flow_data
    }
    flow_data_refs = {fd.flow_id: fd.refs for fd in cfg.flow_data}
    return templates.TemplateResponse(
        request,
        "flow_data.html",
        _ctx(
            cfg=cfg,
            input_flows=flows,
            flow_data_map=flow_data_map,
            flow_data_refs=flow_data_refs,
            saved=saved,
        ),
    )


@flow_data_router.post("/{name}/flow_data")
async def post_flow_data(request: Request, name: str):
    cfg = storage.load_case_study(name)
    form = await request.form()

    flows = _input_flows(cfg)
    input_flow_ids = {f.id for f in flows}

    new_entries: list[FlowDataEntry] = []
    j = 0
    while True:
        fid = form.get(f"fd_{j}_id")
        if fid is None:
            break
        values: dict[int, float] = {}
        # Collect year-row indices tolerantly: a removed point can leave a gap in
        # the fd_{j}_y_{i} numbering, so never stop at the first missing index.
        year_indices = sorted(
            {
                int(m.group(1))
                for key in form.keys()
                if (m := re.fullmatch(rf"fd_{j}_y_(\d+)", key))
            }
        )
        for i in year_indices:
            y_raw = form.get(f"fd_{j}_y_{i}")
            v_raw = form.get(f"fd_{j}_v_{i}")
            if y_raw is None:
                continue
            try:
                year = int(float(y_raw))
                val = float(v_raw or 0)
                values[year] = val
            except (ValueError, TypeError):
                pass
        refs = [c.strip() for c in form.getlist(f"fd_{j}_refs") if c.strip()]
        if values:
            new_entries.append(
                FlowDataEntry(
                    flow_id=fid, element="material", values=values, refs=refs
                )
            )
        j += 1

    # Keep non-input-flow entries; replace input-flow entries with submitted data
    cfg.flow_data = [fd for fd in cfg.flow_data if fd.flow_id not in input_flow_ids]
    cfg.flow_data.extend(new_entries)
    storage.save_case_study(cfg)
    return RedirectResponse(f"/{name}/flow_data?saved=1", status_code=303)
