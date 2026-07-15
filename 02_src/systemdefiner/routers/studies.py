"""Case-study lifecycle routes: list, create (blank / from Excel), delete,
clone, overview, settings. Moved verbatim from ``main.py``.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Form, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse

from systemdefiner import storage
from systemdefiner.deps import _ctx, templates
from systemdefiner.forms import (
    _apply_extra_yaml,
    _parse_bom_from_yaml,
    _parse_tcs_from_yaml,
    _slug,
)
from systemdefiner.health import _UOM_OPTIONS, _model_health
from systemdefiner.models.config_schema import (
    CaseStudyConfig,
    DsmParams,
    Flow,
    FlowCapParams,
    FompParams,
    LfgParams,
    ModelSettings,
    Process,
    ProcessLogic,
    StockConfig,
    TCConfig,
)

router = APIRouter()


@router.get("/")
async def index(request: Request):
    studies = storage.list_case_studies()
    return templates.TemplateResponse(request, "index.html", _ctx(studies=studies))


@router.post("/create-from-excel")
async def create_from_excel(
    request: Request, name: str = Form(...), file: UploadFile = None
):
    """Create a new case study and populate it from an Excel file in one step."""
    import tempfile

    import pandas as pd

    from systemdefiner.yaml_schema import model_to_yaml

    slug = _slug(name)
    if not slug:
        studies = storage.list_case_studies()
        return templates.TemplateResponse(
            request,
            "index.html",
            _ctx(studies=studies, import_error="Invalid name."),
            status_code=400,
        )
    if storage.case_study_exists(slug):
        studies = storage.list_case_studies()
        return templates.TemplateResponse(
            request,
            "index.html",
            _ctx(studies=studies, import_error=f"Case study '{slug}' already exists."),
            status_code=400,
        )

    tmp_path: Optional[str] = None
    try:
        contents = await file.read()
        suffix = Path(file.filename or "upload.xlsx").suffix or ".xlsx"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

        sheets = pd.read_excel(tmp_path, sheet_name=None, header=0, engine="openpyxl")
        yaml_data = model_to_yaml(sheets, source_file=file.filename)
    except Exception as exc:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)
        studies = storage.list_case_studies()
        return templates.TemplateResponse(
            request,
            "index.html",
            _ctx(studies=studies, import_error=f"Import failed: {exc}"),
            status_code=422,
        )
    finally:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)

    m = yaml_data.get("model", {})
    cfg = CaseStudyConfig(
        name=slug,
        model=ModelSettings(
            start_year=m.get("start_year", 2025),
            end_year=m.get("end_year", 2125),
            elements=m.get("elements", ["material", "WC", "DM", "TC"]),
        ),
    )

    _valid_logics = {e.value for e in ProcessLogic}
    _valid_stocks = {e.value for e in StockConfig}
    _valid_tcs = {e.value for e in TCConfig}

    if yaml_data.get("processes"):

        def _proc_from_yaml(p: dict) -> Process:
            fomp_d = p.get("fomp")
            dsm_d = p.get("dsm")
            lfg_d = p.get("lfg")
            fc_d = p.get("flowcap")
            return Process(
                id=p["id"],
                name=p.get("name", ""),
                logic=ProcessLogic(p["logic"])
                if p.get("logic") in _valid_logics
                else ProcessLogic.splitter,
                stock=StockConfig(p["stock"])
                if p.get("stock") in _valid_stocks
                else StockConfig.no_stock,
                tc_config=TCConfig(p["tc_config"])
                if p.get("tc_config") in _valid_tcs
                else TCConfig.no_tc,
                fomp=FompParams(**fomp_d) if fomp_d else None,
                dsm=DsmParams(**dsm_d) if dsm_d else None,
                lfg=LfgParams(**lfg_d) if lfg_d else None,
                flowcap=FlowCapParams(**fc_d) if fc_d else None,
            )

        cfg.processes = [_proc_from_yaml(p) for p in yaml_data["processes"]]

    if yaml_data.get("flows"):
        cfg.flows = [
            Flow(
                id=str(f["id"]),
                name=f.get("name", str(f["id"])),
                from_process=f.get("from_process", 0),
                to_process=f.get("to_process", 0),
            )
            for f in yaml_data["flows"]
        ]

    cfg.transfer_coefficients = _parse_tcs_from_yaml(
        yaml_data.get("transfer_coefficients", [])
    )
    cfg.bom_assembly = _parse_bom_from_yaml(yaml_data.get("bom_assembly", []))
    _apply_extra_yaml(yaml_data, cfg)

    storage.save_case_study(cfg)
    return RedirectResponse(f"/{slug}", status_code=303)


@router.post("/new")
async def new_case_study(
    name: str = Form(...),
    start_year: int = Form(2025),
    end_year: int = Form(2125),
    elements: str = Form("material, WC, DM, TC"),
):
    slug = _slug(name)
    if not slug:
        raise HTTPException(400, "Invalid name")
    if storage.case_study_exists(slug):
        raise HTTPException(400, f"Case study '{slug}' already exists")
    cfg = CaseStudyConfig(
        name=slug,
        model=ModelSettings(
            start_year=start_year,
            end_year=end_year,
            elements=[e.strip() for e in elements.split(",") if e.strip()],
        ),
    )
    storage.save_case_study(cfg)
    return RedirectResponse(f"/{slug}", status_code=303)


@router.post("/{name}/delete")
async def delete_case_study(name: str):
    storage.delete_case_study(name)
    return RedirectResponse("/", status_code=303)


@router.post("/{name}/clone")
async def clone_case_study(request: Request, name: str):
    form = await request.form()
    new_name = _slug((form.get("new_name") or "").strip())
    if not new_name:
        # Auto-name the copy ({name}_copy, _copy_2, …) so the button works
        # without any client-side input.
        base = _slug(f"{name}_copy")
        new_name = base
        i = 2
        while storage.case_study_exists(new_name):
            new_name = f"{base}_{i}"
            i += 1
    try:
        storage.clone_case_study(name, new_name)
    except ValueError as exc:
        studies = storage.list_case_studies()
        return templates.TemplateResponse(
            request,
            "index.html",
            _ctx(studies=studies, import_error=str(exc)),
            status_code=400,
        )
    return RedirectResponse(f"/{new_name}", status_code=303)


@router.get("/{name}")
async def case_study_overview(request: Request, name: str):
    if not storage.case_study_exists(name):
        raise HTTPException(404, f"Case study '{name}' not found")
    cfg = storage.load_case_study(name)
    return templates.TemplateResponse(
        request,
        "case_study.html",
        _ctx(cfg=cfg, health=_model_health(cfg), uom_options=_UOM_OPTIONS),
    )


@router.post("/{name}/settings")
async def update_settings(request: Request, name: str):
    form = await request.form()
    cfg = storage.load_case_study(name)
    m = cfg.model

    def _int(key, default):
        try:
            return int(form.get(key, default))
        except (ValueError, TypeError):
            return default

    def _bool(key):
        return key in form  # checkbox: present = True, absent = False

    cfg.description = form.get("description", cfg.description)
    m.start_year = _int("start_year", m.start_year)
    m.end_year = _int("end_year", m.end_year)
    m.unit_of_measurement = form.get(
        "unit_of_measurement", m.unit_of_measurement
    ).strip()
    m.sankey_title = form.get("sankey_title", m.sankey_title).strip()
    m.input_file = form.get("input_file", m.input_file).strip()
    m.output_file = form.get("output_file", m.output_file).strip()
    m.run_dsm_calculation = _bool("run_dsm_calculation")
    m.run_fomp_calculation = _bool("run_fomp_calculation")
    m.run_monte_carlo = _bool("run_monte_carlo")
    m.mc_iterations = _int("mc_iterations", m.mc_iterations)
    m.mc_seed = (form.get("mc_seed", m.mc_seed) or "42").strip()
    m.solver_strict = _bool("solver_strict")
    m.solver_max_iterations = _int("solver_max_iterations", m.solver_max_iterations)
    m.run_scenario_analysis = _bool("run_scenario_analysis")
    m.selected_scenarios = [
        (form.get(f"scenario_{i}", "") or "").strip() for i in range(4)
    ]

    storage.save_case_study(cfg)
    return RedirectResponse(f"/{name}", status_code=303)
