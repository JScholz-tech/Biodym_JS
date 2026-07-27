"""Frameworks & Analysis routes — utilisation-framework (BUF/CUF) settings,
the per-process role map, and named cascade paths.

Fate is a per-process ``utilisation_role`` (what a process does with the carbon
entering it — its inflow is credited to that role); this page is where it is
edited. Paths are process sets; entry/scope are derived from the graph at
analysis time (see ``analysis.cascade_graph.path_flows``), not stored here.
"""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from systemdefiner import storage
from systemdefiner.deps import _ctx, templates
from systemdefiner.models.config_schema import (
    BufCategory,
    PathDefinition,
    ProcessLogic,
)

router = APIRouter()

# Process logic → default utilisation role (mirrors
# analysis.cascade_graph.auto_classify_processes, derived from the config alone
# since the SystemDefiner has no solved MFA system). Only the terminal-use logic
# types get an auto role; everything else defaults to blank (transit / boundary).
_LOGIC_ROLE = {
    ProcessLogic.dsm: "BBP",
    ProcessLogic.dsm_component: "BBP",
    ProcessLogic.fomp: "UF",
    ProcessLogic.lfg: "BE",
}


def _auto_roles(cfg) -> dict[int, str]:
    """process_id → auto-inferred utilisation role (the dropdown default)."""
    return {p.id: _LOGIC_ROLE.get(p.logic, "") for p in cfg.processes}


def _role_rows(cfg):
    """Non-boundary processes with their inflow/outflow counts, for the role
    table. Boundary (Input) processes are the environment — no role."""
    rows = []
    for p in cfg.processes:
        if p.logic == ProcessLogic.input:
            continue
        n_in = sum(1 for f in cfg.flows if f.to_process == p.id)
        rows.append({"process": p, "n_in": n_in})
    return rows


def _analysis_ctx(cfg):
    return _ctx(
        cfg=cfg,
        auto_roles=_auto_roles(cfg),
        proc_names={p.id: p.name for p in cfg.processes},
        role_rows=_role_rows(cfg),
        # Lightweight graph for the client-side path preview.
        flows_json=[
            {"id": f.id, "from": f.from_process, "to": f.to_process}
            for f in cfg.flows
        ],
    )


@router.get("/{name}/analysis")
async def analysis_page(request: Request, name: str):
    cfg = storage.load_case_study(name)
    return templates.TemplateResponse(
        request, "analysis.html", _analysis_ctx(cfg)
    )


@router.post("/{name}/analysis/settings")
async def analysis_settings(request: Request, name: str):
    form = await request.form()
    cfg = storage.load_case_study(name)
    a = cfg.analysis

    def _float(key, default):
        try:
            return float(form.get(key, default))
        except (ValueError, TypeError):
            return default

    def _int(key, default):
        try:
            return int(form.get(key, default))
        except (ValueError, TypeError):
            return default

    a.buf.enabled = "buf_enabled" in form
    a.buf.cutoff = _float("buf_cutoff", a.buf.cutoff)
    a.cuf.enabled = "cuf_enabled" in form
    a.cuf.t_ref = _int("cuf_t_ref", a.cuf.t_ref)
    a.cuf.include_labile_storage = "cuf_include_labile" in form
    storage.save_case_study(cfg)
    return RedirectResponse(f"/{name}/analysis", status_code=303)


@router.post("/{name}/analysis/roles")
async def analysis_roles(request: Request, name: str):
    """Bulk-save the process role map. Keyed by process ID (index-gap safe)."""
    form = await request.form()
    cfg = storage.load_case_study(name)
    for p in cfg.processes:
        raw = form.get(f"role_{p.id}", "")
        try:
            p.utilisation_role = BufCategory(raw or "")
        except ValueError:
            p.utilisation_role = BufCategory.unset
    storage.save_case_study(cfg)
    return RedirectResponse(f"/{name}/analysis", status_code=303)


@router.post("/{name}/analysis/paths/new")
async def analysis_path_new(request: Request, name: str):
    form = await request.form()
    cfg = storage.load_case_study(name)
    pname = (form.get("path_name", "") or "").strip()
    procs = []
    for raw in form.getlist("processes"):
        try:
            procs.append(int(raw))
        except (ValueError, TypeError):
            pass
    if pname and procs:
        cfg.analysis.paths.append(PathDefinition(name=pname, processes=procs))
        storage.save_case_study(cfg)
    return RedirectResponse(f"/{name}/analysis", status_code=303)


@router.post("/{name}/analysis/paths/{idx}/delete")
async def analysis_path_delete(name: str, idx: int):
    cfg = storage.load_case_study(name)
    if 0 <= idx < len(cfg.analysis.paths):
        cfg.analysis.paths.pop(idx)
        storage.save_case_study(cfg)
    return RedirectResponse(f"/{name}/analysis", status_code=303)
