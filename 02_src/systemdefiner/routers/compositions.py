"""Flow-composition, BOM-assembly, and initial-stock editor routes.

Moved verbatim from ``main.py``.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from systemdefiner import storage
from systemdefiner.deps import _ctx, templates
from systemdefiner.models.config_schema import (
    BomAssemblyEntry,
    BomAssemblyFlow,
    FlowComposition,
    InitialStockEntry,
    ProcessLogic,
    StockConfig,
)
from systemdefiner.routers.elements import _rules_to_paths

router = APIRouter()


@router.get("/{name}/compositions")
async def compositions_form(request: Request, name: str):
    import json as _json

    if not storage.case_study_exists(name):
        raise HTTPException(404)
    cfg = storage.load_case_study(name)
    # Only include flows from Input-logic processes (system boundary)
    input_pids = {p.id for p in cfg.processes if p.logic == ProcessLogic.input}
    input_pids.add(0)  # process 0 is always the boundary
    input_flows = [f for f in cfg.flows if f.from_process in input_pids]
    existing = {fc.flow_id: fc for fc in cfg.flow_compositions}
    rows = [
        {"flow": f, "comp_values": existing[f.id].values if f.id in existing else {}}
        for f in input_flows
    ]
    flow_refs = {
        f.id: (existing[f.id].refs if f.id in existing else []) for f in input_flows
    }
    hier_json = [
        {"parent": r.parent, "children": r.children} for r in cfg.element_hierarchy
    ]
    # Hierarchy matrix paths (same as elements page)
    paths_json = _json.dumps(_rules_to_paths(cfg.element_hierarchy))
    # Per-flow composition values as % (×100) keyed by flow id
    flow_comps_json = _json.dumps(
        {
            row["flow"].id: {
                e: round(row["comp_values"].get(e, 0.0) * 100, 4)
                for e in cfg.model.elements
            }
            for row in rows
        }
    )
    flow_list_json = _json.dumps(
        [{"id": row["flow"].id, "name": row["flow"].name} for row in rows]
    )
    return templates.TemplateResponse(
        request,
        "compositions.html",
        _ctx(
            cfg=cfg,
            rows=rows,
            hier_json=hier_json,
            paths_json=paths_json,
            flow_comps_json=flow_comps_json,
            flow_list_json=flow_list_json,
            flow_refs=flow_refs,
        ),
    )


@router.post("/{name}/compositions")
async def compositions_save(request: Request, name: str):
    form = await request.form()
    cfg = storage.load_case_study(name)
    elements = cfg.model.elements
    # Only process input flows; preserve compositions for non-input flows
    input_pids = {p.id for p in cfg.processes if p.logic == ProcessLogic.input}
    input_pids.add(0)
    input_flows = [f for f in cfg.flows if f.from_process in input_pids]
    # Keep existing compositions for flows not shown on this page
    kept = [
        fc
        for fc in cfg.flow_compositions
        if fc.flow_id not in {f.id for f in input_flows}
    ]
    new_comps: list[FlowComposition] = []
    for flow in input_flows:
        values: dict[str, float] = {}
        for elem in elements:
            key = f"comp_{flow.id}_{elem}"
            raw = form.get(key, "")
            try:
                v = float(raw) if raw else 0.0
            except ValueError:
                v = 0.0
            values[elem] = v
        refs = [c.strip() for c in form.getlist(f"refs_{flow.id}") if c.strip()]
        if any(v != 0.0 for v in values.values()):
            new_comps.append(FlowComposition(flow_id=flow.id, values=values, refs=refs))
    cfg.flow_compositions = kept + new_comps
    storage.save_case_study(cfg)
    return RedirectResponse(f"/{name}/compositions", status_code=303)


# ══════════════════════════════════════════════════════════════════════════════
# BOM ASSEMBLY
# ══════════════════════════════════════════════════════════════════════════════


@router.get("/{name}/bom/{pid}")
async def bom_edit_form(request: Request, name: str, pid: int):
    import json as _json

    if not storage.case_study_exists(name):
        raise HTTPException(404)
    cfg = storage.load_case_study(name)
    process = next((p for p in cfg.processes if p.id == pid), None)
    if not process:
        raise HTTPException(404)
    entry = next((e for e in cfg.bom_assembly if e.process_id == pid), None)
    outgoing_flows = [f for f in cfg.flows if f.from_process == pid]
    rows = []
    flow_map = {bf.flow_id: bf for bf in (entry.flows if entry else [])}
    for flow in outgoing_flows:
        bf = flow_map.get(flow.id)
        rows.append(
            {
                "flow": flow,
                "output_flow_type": bf.output_flow_type if bf else "",
                "frac_values": bf.fractions if bf else {},
            }
        )
    # Hierarchy-matrix context (same layout as Flow Compositions). BOM stores
    # parent-relative fractions, so display % = stored fraction × 100 (no cascade).
    hier_json = [
        {"parent": r.parent, "children": r.children} for r in cfg.element_hierarchy
    ]
    paths_json = _json.dumps(_rules_to_paths(cfg.element_hierarchy))
    bom_comps_json = _json.dumps(
        {
            row["flow"].id: {
                e: round(row["frac_values"].get(e, 0.0) * 100, 4)
                for e in cfg.model.elements
            }
            for row in rows
        }
    )
    flow_list_json = _json.dumps(
        [
            {
                "id": row["flow"].id,
                "name": row["flow"].name,
                "type": row["output_flow_type"],
            }
            for row in rows
        ]
    )
    return templates.TemplateResponse(
        request,
        "bom_edit.html",
        _ctx(
            cfg=cfg,
            process=process,
            rows=rows,
            hier_json=hier_json,
            paths_json=paths_json,
            bom_comps_json=bom_comps_json,
            flow_list_json=flow_list_json,
            bom_refs=(entry.refs if entry else []),
        ),
    )


@router.post("/{name}/bom/{pid}")
async def bom_save(request: Request, name: str, pid: int):
    form = await request.form()
    cfg = storage.load_case_study(name)
    process = next((p for p in cfg.processes if p.id == pid), None)
    if not process:
        raise HTTPException(404)
    elements = cfg.model.elements
    outgoing_flows = [f for f in cfg.flows if f.from_process == pid]
    bom_flows: list[BomAssemblyFlow] = []
    for flow in outgoing_flows:
        flow_type = (form.get(f"bom_{flow.id}_type") or "").strip()
        fractions: dict[str, float] = {}
        for elem in elements:
            raw = form.get(f"bom_{flow.id}_{elem}", "") or ""
            try:
                v = float(raw) if raw else 0.0
            except ValueError:
                v = 0.0
            if v:
                fractions[elem] = v
        bom_flows.append(
            BomAssemblyFlow(
                flow_id=flow.id,
                output_flow_type=flow_type,
                fractions=fractions,
            )
        )
    refs = [c.strip() for c in form.getlist("bom_refs") if c.strip()]
    cfg.bom_assembly = [e for e in cfg.bom_assembly if e.process_id != pid]
    cfg.bom_assembly.append(
        BomAssemblyEntry(process_id=pid, flows=bom_flows, refs=refs)
    )
    storage.save_case_study(cfg)
    return RedirectResponse(f"/{name}/bom/{pid}", status_code=303)


# ══════════════════════════════════════════════════════════════════════════════
# INITIAL STOCK
# ══════════════════════════════════════════════════════════════════════════════


def _stock_needs_initial(process) -> bool:
    """True when the process's stock config carries a t=0 initial stock."""
    return process.stock in (
        StockConfig.initial_stock_cohort,
        StockConfig.initial_stock_decay,
    )


@router.get("/{name}/initial_stock/{pid}")
async def initial_stock_form(request: Request, name: str, pid: int):
    import json as _json

    cfg = storage.load_case_study(name)
    process = next((p for p in cfg.processes if p.id == pid), None)
    if not process:
        raise HTTPException(404)
    entry = next((s for s in cfg.initial_stocks if s.process_id == pid), None)
    comp = entry.composition if entry else {}
    hier_json = [
        {"parent": r.parent, "children": r.children} for r in cfg.element_hierarchy
    ]
    paths_json = _json.dumps(_rules_to_paths(cfg.element_hierarchy))
    # Composition is stored absolute; matrix displays parent-relative (× 100 here).
    comp_json = _json.dumps(
        {e: round(comp.get(e, 0.0) * 100, 4) for e in cfg.model.elements}
    )
    return templates.TemplateResponse(
        request,
        "initial_stock_edit.html",
        _ctx(
            cfg=cfg,
            process=process,
            entry=entry,
            is_cohort=(process.stock == StockConfig.initial_stock_cohort),
            hier_json=hier_json,
            paths_json=paths_json,
            comp_json=comp_json,
        ),
    )


@router.post("/{name}/initial_stock/{pid}")
async def initial_stock_save(request: Request, name: str, pid: int):
    form = await request.form()
    cfg = storage.load_case_study(name)
    process = next((p for p in cfg.processes if p.id == pid), None)
    if not process:
        raise HTTPException(404)

    def _flt(key, default=None):
        v = (form.get(key) or "").strip()
        try:
            return float(v) if v else default
        except ValueError:
            return default

    def _iv(key):
        v = (form.get(key) or "").strip()
        try:
            return int(float(v)) if v else None
        except ValueError:
            return None

    # The matrix submit handler writes absolute fractions (0–1) into is_{elem}.
    composition: dict[str, float] = {}
    for elem in cfg.model.elements:
        v = _flt(f"is_{elem}", 0.0) or 0.0
        if v:
            composition[elem] = v

    material_quantity = _flt("is_material_quantity", 0.0) or 0.0

    # Always drop any existing entry for this process first. An empty submission
    # (no quantity and no composition) therefore *removes* the initial stock
    # instead of leaving a zombie entry behind.
    cfg.initial_stocks = [s for s in cfg.initial_stocks if s.process_id != pid]
    if material_quantity > 0 or composition:
        cfg.initial_stocks.append(
            InitialStockEntry(
                process_id=pid,
                material_quantity=material_quantity,
                composition=composition,
                cohort_age_distribution_type=(
                    form.get("is_cohort_age_distribution_type") or "Normal"
                ),
                cohort_mean_age=_flt("is_cohort_mean_age"),
                cohort_std_age=_flt("is_cohort_std_age"),
                cohort_max_age=_iv("is_cohort_max_age"),
                cohort_decay_constant=_flt("is_cohort_decay_constant"),
                refs=[c.strip() for c in form.getlist("is_refs") if c.strip()],
            )
        )
    storage.save_case_study(cfg)
    return RedirectResponse(f"/{name}/processes", status_code=303)
