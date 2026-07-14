"""Transfer-coefficient editor routes.

Moved verbatim from ``main.py``.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from systemdefiner import storage
from systemdefiner.deps import _ctx, templates
from systemdefiner.models.config_schema import (
    DynamicTCPoint,
    ProcessLogic,
    TCConfig,
    TransferCoefficient,
)
from systemdefiner.routers.elements import _rules_to_paths

router = APIRouter()


@router.get("/{name}/tcs")
async def tcs_overview(request: Request, name: str):
    cfg = storage.load_case_study(name)
    # Only Splitter, Transformer, and DSM processes use TCs in the engine
    _tc_eligible = {ProcessLogic.splitter, ProcessLogic.transformer, ProcessLogic.dsm, ProcessLogic.dsm_component}
    tc_processes = [p for p in cfg.processes if p.logic in _tc_eligible]
    return templates.TemplateResponse(
        request, "tcs.html", _ctx(cfg=cfg, tc_processes=tc_processes)
    )


@router.get("/{name}/tcs/{pid}")
async def tc_edit_form(request: Request, name: str, pid: int):
    cfg = storage.load_case_study(name)
    process = next((p for p in cfg.processes if p.id == pid), None)
    if not process:
        raise HTTPException(404)

    outgoing_flows = [f for f in cfg.flows if f.from_process == pid]
    existing_tcs = {
        tc.flow_id: tc for tc in cfg.transfer_coefficients if tc.process_id == pid
    }
    tc_refs = {
        f.id: (existing_tcs[f.id].refs if f.id in existing_tcs else [])
        for f in outgoing_flows
    }
    is_dynamic = process.tc_config == TCConfig.dynamic

    if is_dynamic:
        # Build per-flow rows: flat list of {flow_id, year, tc_values}
        dyn_rows = []
        for flow in outgoing_flows:
            tc = existing_tcs.get(flow.id)
            points = tc.time_series if tc else []
            for pt in points:
                dyn_rows.append(
                    {
                        "flow_id": flow.id,
                        "year": pt.year,
                        "tc_values": pt.values,
                    }
                )
        is_splitter = process.logic in (ProcessLogic.splitter, ProcessLogic.dsm, ProcessLogic.dsm_component)
        is_transformer = process.logic == ProcessLogic.transformer

        # Hierarchy consistency data (Transformer only)
        parent_to_children: dict = {}
        inflow_composition: dict = {}
        if is_transformer and cfg.element_hierarchy:
            parent_to_children = {
                rule.parent: list(rule.children)
                for rule in cfg.element_hierarchy
            }
            # Prefer user-saved composition override; fall back to auto-detection.
            if process.expected_inflow_composition:
                inflow_composition = process.expected_inflow_composition
            else:
                inflow_fids = [f.id for f in cfg.flows if f.to_process == pid]
                comp_map = {fc.flow_id: fc.values for fc in cfg.flow_compositions}
                for fid in inflow_fids:
                    cvals = comp_map.get(fid, {})
                    if any(v > 0 for k, v in cvals.items() if k != "material"):
                        inflow_composition = cvals
                        break
                if not inflow_composition:
                    for fc in cfg.flow_compositions:
                        if any(v > 0 for k, v in fc.values.items() if k != "material"):
                            inflow_composition = fc.values
                            break

        # Matrix context for the hierarchy composition check panel
        import json as _json
        hier_json = [
            {"parent": r.parent, "children": list(r.children)}
            for r in cfg.element_hierarchy
        ] if cfg.element_hierarchy else []
        paths_json = _json.dumps(_rules_to_paths(cfg.element_hierarchy)) if cfg.element_hierarchy else "[]"
        comp_values_json = _json.dumps(
            {e: round(inflow_composition.get(e, 0.0) * 100, 4) for e in cfg.model.elements}
        )
        return templates.TemplateResponse(
            request,
            "tc_edit_dynamic.html",
            _ctx(
                cfg=cfg,
                process=process,
                rows=dyn_rows,
                outgoing_flows=outgoing_flows,
                is_splitter=is_splitter,
                is_transformer=is_transformer,
                tc_refs=tc_refs,
                parent_to_children=parent_to_children,
                inflow_composition=inflow_composition,
                hier_json=hier_json,
                paths_json=paths_json,
                comp_values_json=comp_values_json,
            ),
        )
    else:
        rows = []
        for flow in outgoing_flows:
            tc = existing_tcs.get(flow.id)
            rows.append(
                {
                    "flow": flow,
                    "tc_values": tc.values if tc else {},
                }
            )
        is_splitter = process.logic in (ProcessLogic.splitter, ProcessLogic.dsm, ProcessLogic.dsm_component)
        is_transformer = process.logic == ProcessLogic.transformer
        return templates.TemplateResponse(
            request,
            "tc_edit.html",
            _ctx(
                cfg=cfg,
                process=process,
                rows=rows,
                is_splitter=is_splitter,
                is_transformer=is_transformer,
                tc_refs=tc_refs,
            ),
        )


@router.post("/{name}/tcs/{pid}")
async def tc_save(request: Request, name: str, pid: int):
    form = await request.form()
    cfg = storage.load_case_study(name)
    elements = cfg.model.elements
    process = next((p for p in cfg.processes if p.id == pid), None)
    if not process:
        raise HTTPException(404)

    outgoing_flows = [f for f in cfg.flows if f.from_process == pid]
    cfg.transfer_coefficients = [
        tc for tc in cfg.transfer_coefficients if tc.process_id != pid
    ]

    if process.tc_config == TCConfig.dynamic:
        # Dynamic TC save.
        # Year fields:  tc_{flow_id}_year_{idx}
        # Value fields: tc_{flow_id}_idx_{idx}_{elem}
        import re as _re

        # First collect all year values keyed by (flow_id, idx)
        year_map: dict[tuple[str, str], int] = {}
        for key in form.keys():
            m = _re.match(r"^tc_(.+?)_year_(\d+)$", key)
            if not m:
                continue
            fid, idx = m.group(1), m.group(2)
            raw = form.get(key, "")
            try:
                year_map[(fid, idx)] = int(float(raw))
            except (ValueError, TypeError):
                pass

        # Then collect element values keyed by (flow_id, idx, elem)
        val_data: dict[tuple[str, str], dict[str, float]] = {}
        for key in form.keys():
            m = _re.match(r"^tc_(.+?)_idx_(\d+)_(.+)$", key)
            if not m:
                continue
            fid, idx, elem = m.group(1), m.group(2), m.group(3)
            raw = form.get(key, "")
            try:
                val = float(raw) if raw else 0.0
            except ValueError:
                val = 0.0
            val_data.setdefault((fid, idx), {})[elem] = val

        # Build time series per flow
        for flow in outgoing_flows:
            # Collect (year, values) pairs where year is known
            points: list[DynamicTCPoint] = []
            for (fid, idx), year in year_map.items():
                if fid != flow.id:
                    continue
                values = val_data.get((fid, idx), {})
                if year and values:
                    points.append(DynamicTCPoint(year=year, values=values))
            points.sort(key=lambda p: p.year)
            refs = [c.strip() for c in form.getlist(f"refs_{flow.id}") if c.strip()]
            cfg.transfer_coefficients.append(
                TransferCoefficient(
                    process_id=pid,
                    flow_id=flow.id,
                    tc_type="dynamic",
                    time_series=points,
                    refs=refs,
                )
            )

        # Validation (mirrors static): at years defined for ALL flows, each
        # validated element must sum to 1.0 across flows. Splitter/DSM validate
        # material only; Transformer validates the non-material elements (material
        # is derived by the engine). Years not shared by every flow are
        # interpolated, so they're not validated.
        is_splitter = process.logic in (ProcessLogic.splitter, ProcessLogic.dsm, ProcessLogic.dsm_component)
        validate_elements = elements[:1] if is_splitter else elements[1:]
        proc_tcs = [tc for tc in cfg.transfer_coefficients if tc.process_id == pid]
        year_sets = [set(pt.year for pt in tc.time_series) for tc in proc_tcs]
        common_years = (
            sorted(set.intersection(*year_sets)) if year_sets and all(year_sets) else []
        )
        errors = []
        for year in common_years:
            for elem in validate_elements:
                total = sum(
                    next(
                        (
                            p.values.get(elem, 0.0)
                            for p in tc.time_series
                            if p.year == year
                        ),
                        0.0,
                    )
                    for tc in proc_tcs
                )
                if abs(total - 1.0) > 1e-6:
                    errors.append(
                        f"Year {year}, {elem}: sum = {total * 100:.2f}% (must be 100%)"
                    )

        if errors:
            dyn_rows = [
                {"flow_id": flow.id, "year": pt.year, "tc_values": pt.values}
                for flow in outgoing_flows
                for tc in proc_tcs
                if tc.flow_id == flow.id
                for pt in tc.time_series
            ]
            tc_refs = {
                f.id: [c.strip() for c in form.getlist(f"refs_{f.id}") if c.strip()]
                for f in outgoing_flows
            }
            return templates.TemplateResponse(
                request,
                "tc_edit_dynamic.html",
                _ctx(
                    cfg=cfg,
                    process=process,
                    rows=dyn_rows,
                    outgoing_flows=outgoing_flows,
                    is_splitter=is_splitter,
                    errors=errors,
                    tc_refs=tc_refs,
                ),
                status_code=422,
            )

        # Parse and save expected inflow composition (Transformer only)
        if process.logic == ProcessLogic.transformer:
            check_comp: dict = {}
            for key in form.keys():
                if key.startswith("check_comp_"):
                    elem = key[len("check_comp_"):]
                    try:
                        pct = float(form.get(key, "") or 0)
                        if pct != 0.0:
                            check_comp[elem] = round(pct / 100, 6)
                    except ValueError:
                        pass
            process.expected_inflow_composition = check_comp if check_comp else None

        storage.save_case_study(cfg)
        return RedirectResponse(f"/{name}/tcs", status_code=303)

    # Static TC save
    errors = []
    for flow in outgoing_flows:
        values = {}
        for elem in elements:
            key = f"tc_{flow.id}_{elem}"
            raw = form.get(key, "")
            try:
                values[elem] = float(raw) if raw else 0.0
            except ValueError:
                values[elem] = 0.0
        refs = [c.strip() for c in form.getlist(f"refs_{flow.id}") if c.strip()]
        cfg.transfer_coefficients.append(
            TransferCoefficient(
                process_id=pid,
                flow_id=flow.id,
                tc_type="static",
                refs=refs,
                values=values,
            )
        )

    # Splitter/DSM validate the material column; Transformer validates the
    # non-material elements (the engine derives material = sum of WC+DM).
    is_splitter = process.logic in (ProcessLogic.splitter, ProcessLogic.dsm, ProcessLogic.dsm_component)
    validate_elements = elements[:1] if is_splitter else elements[1:]
    for elem in validate_elements:
        total = sum(
            tc.values.get(elem, 0.0)
            for tc in cfg.transfer_coefficients
            if tc.process_id == pid
        )
        if abs(total - 1.0) > 1e-6:
            errors.append(f"{elem}: sum = {total:.4f} (must be 1.0)")

    if errors:
        existing_tcs = {
            tc.flow_id: tc for tc in cfg.transfer_coefficients if tc.process_id == pid
        }
        rows = [
            {
                "flow": f,
                "tc_values": existing_tcs.get(
                    f.id,
                    TransferCoefficient(
                        process_id=pid, flow_id=f.id, tc_type="static", values={}
                    ),
                ).values,
            }
            for f in outgoing_flows
        ]
        tc_refs = {
            f.id: (existing_tcs[f.id].refs if f.id in existing_tcs else [])
            for f in outgoing_flows
        }
        return templates.TemplateResponse(
            request,
            "tc_edit.html",
            _ctx(
                cfg=cfg,
                process=process,
                rows=rows,
                errors=errors,
                tc_refs=tc_refs,
                is_splitter=is_splitter,
            ),
            status_code=422,
        )

    storage.save_case_study(cfg)
    return RedirectResponse(f"/{name}/tcs", status_code=303)
