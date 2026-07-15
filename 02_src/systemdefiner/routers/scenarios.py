"""Scenario Manager routes and the MC-parameter editor.

Two routers because the original ``main.py`` declared the MC-parameter routes
after the elements editor — ``mc_router`` is included at that position in
``main.py`` to keep the registration order identical.

Moved verbatim from ``main.py``.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from systemdefiner import storage
from systemdefiner.deps import _ctx, templates
from systemdefiner.models.config_schema import (
    McParameter,
    ScenarioDefinition,
    ScenarioModification,
)
from systemdefiner.scenario_params import (
    _DIST_FIELDS,
    _MC_DISTRIBUTIONS,
    _MC_OPERATIONS,
    _SCENARIO_OPERATIONS,
    _SCENARIO_PARAM_TYPES,
    _build_scenario_params,
)

router = APIRouter()


@router.get("/{name}/scenarios")
async def scenarios_list(request: Request, name: str):
    cfg = storage.load_case_study(name)
    return templates.TemplateResponse(
        request,
        "scenarios.html",
        _ctx(
            cfg=cfg, operations=_SCENARIO_OPERATIONS, param_types=_SCENARIO_PARAM_TYPES
        ),
    )


@router.post("/{name}/scenarios/new")
async def scenario_new(request: Request, name: str):
    form = await request.form()
    scenario_name = (form.get("scenario_name") or "").strip()
    if not scenario_name:
        raise HTTPException(400, "Scenario name is required")
    # The name becomes a URL path segment (/{name}/scenarios/{sname}) — a
    # slash would make the scenario unreachable and undeletable.
    if "/" in scenario_name or "\\" in scenario_name:
        raise HTTPException(400, "Scenario name must not contain slashes")
    cfg = storage.load_case_study(name)
    if any(s.name == scenario_name for s in cfg.scenarios):
        raise HTTPException(400, f"Scenario '{scenario_name}' already exists")
    cfg.scenarios.append(ScenarioDefinition(name=scenario_name))
    storage.save_case_study(cfg)
    return RedirectResponse(f"/{name}/scenarios/{scenario_name}", status_code=303)


@router.get("/{name}/scenarios/{sname}")
async def scenario_edit_form(request: Request, name: str, sname: str):
    cfg = storage.load_case_study(name)
    scenario = next((s for s in cfg.scenarios if s.name == sname), None)
    if not scenario:
        raise HTTPException(404)
    import json as _json

    params_json = _json.dumps(_build_scenario_params(cfg))
    return templates.TemplateResponse(
        request,
        "scenario_edit.html",
        _ctx(
            cfg=cfg,
            scenario=scenario,
            operations=_SCENARIO_OPERATIONS,
            param_types=_SCENARIO_PARAM_TYPES,
            params_json=params_json,
        ),
    )


@router.post("/{name}/scenarios/{sname}")
async def scenario_save(request: Request, name: str, sname: str):
    form = await request.form()
    cfg = storage.load_case_study(name)
    scenario = next((s for s in cfg.scenarios if s.name == sname), None)
    if not scenario:
        raise HTTPException(404)

    # Collect all mod indices present in form
    import re as _re

    indices = sorted(
        {
            int(m.group(1))
            for k in form.keys()
            for m in [_re.match(r"^mod_(\d+)_", k)]
            if m
        }
    )

    mods = []
    for i in indices:
        pname = (form.get(f"mod_{i}_parameter_name") or "").strip()
        if not pname:
            continue

        def _opt_int(key):
            v = form.get(key, "").strip()
            try:
                return int(v) if v else None
            except ValueError:
                return None

        mods.append(
            ScenarioModification(
                parameter_name=pname,
                parameter_type=(form.get(f"mod_{i}_parameter_type") or "").strip(),
                operation=form.get(f"mod_{i}_operation", "replace"),
                new_value=float(form.get(f"mod_{i}_new_value", 0) or 0),
                start_year=_opt_int(f"mod_{i}_start_year"),
                end_year=_opt_int(f"mod_{i}_end_year"),
                refs=[c.strip() for c in form.getlist(f"mod_{i}_refs") if c.strip()],
            )
        )

    scenario.modifications = mods
    storage.save_case_study(cfg)
    return RedirectResponse(f"/{name}/scenarios", status_code=303)


@router.post("/{name}/scenarios/{sname}/delete")
async def scenario_delete(request: Request, name: str, sname: str):
    cfg = storage.load_case_study(name)
    cfg.scenarios = [s for s in cfg.scenarios if s.name != sname]
    storage.save_case_study(cfg)
    return RedirectResponse(f"/{name}/scenarios", status_code=303)


# ── MC Parameters ────────────────────────────────────────────────────────────

mc_router = APIRouter()


@mc_router.get("/{name}/mc_parameters")
async def mc_params_form(request: Request, name: str):
    import json as _json

    if not storage.case_study_exists(name):
        raise HTTPException(404)
    cfg = storage.load_case_study(name)
    params_json = _json.dumps(_build_scenario_params(cfg))
    return templates.TemplateResponse(
        request,
        "mc_parameters.html",
        _ctx(
            cfg=cfg,
            params_json=params_json,
            distributions=_MC_DISTRIBUTIONS,
            operations=_MC_OPERATIONS,
        ),
    )


@mc_router.post("/{name}/mc_parameters")
async def mc_params_save(request: Request, name: str):
    import re as _re

    if not storage.case_study_exists(name):
        raise HTTPException(404)
    form = await request.form()
    cfg = storage.load_case_study(name)

    indices: set[int] = set()
    for key in form.keys():
        m = _re.match(r"^mc_(\d+)_", key)
        if m:
            indices.add(int(m.group(1)))

    def _f(i: int, key: str):
        v = (form.get(f"mc_{i}_{key}") or "").strip()
        try:
            return float(v) if v else None
        except (ValueError, TypeError):
            return None

    def _iv(i: int, key: str):
        v = (form.get(f"mc_{i}_{key}") or "").strip()
        try:
            return int(v) if v else None
        except (ValueError, TypeError):
            return None

    mc_params: list[McParameter] = []
    for i in sorted(indices):
        pid = (form.get(f"mc_{i}_parameter_id") or "").strip()
        if not pid:
            continue
        dist = form.get(f"mc_{i}_distribution") or "normal"
        active = _DIST_FIELDS.get(dist, set())
        mc_params.append(
            McParameter(
                parameter_id=pid,
                enabled=(f"mc_{i}_enabled" in form),
                distribution=dist,
                mean=_f(i, "mean") if "mean" in active else None,
                std=_f(i, "std") if "std" in active else None,
                min=_f(i, "min") if "min" in active else None,
                max=_f(i, "max") if "max" in active else None,
                mode=_f(i, "mode") if "mode" in active else None,
                operation=(form.get(f"mc_{i}_operation") or "set"),
                start_year=_iv(i, "start_year"),
                end_year=_iv(i, "end_year"),
                flow_group=(form.get(f"mc_{i}_flow_group") or None) or None,
                refs=[c.strip() for c in form.getlist(f"mc_{i}_refs") if c.strip()],
            )
        )

    cfg.mc_parameters = mc_params
    storage.save_case_study(cfg)
    return RedirectResponse(f"/{name}/mc_parameters", status_code=303)
