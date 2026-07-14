"""Export, diagram, and Excel/YAML import routes.

Moved verbatim from ``main.py``.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, RedirectResponse

from systemdefiner import storage
from systemdefiner.deps import _ctx, templates
from systemdefiner.forms import (
    _apply_extra_yaml,
    _parse_bom_from_yaml,
    _parse_tcs_from_yaml,
)
from systemdefiner.models.config_schema import (
    CaseStudyConfig,
    DsmParams,
    Flow,
    FlowCapParams,
    FompParams,
    LfgParams,
    Process,
    ProcessLogic,
    StockConfig,
    TCConfig,
)

router = APIRouter()


@router.get("/{name}/export")
async def export_yaml(name: str):
    from systemdefiner.storage import _config_path

    path = _config_path(name)
    return FileResponse(
        path, media_type="application/x-yaml", filename=f"{name}_config.yaml"
    )


# ── Model diagram (user-uploaded image shown in the page header) ────────────
@router.get("/{name}/diagram")
async def get_diagram(name: str):
    path = storage.diagram_path(name)
    if not path:
        raise HTTPException(404, "No diagram uploaded")
    return FileResponse(path)


@router.post("/{name}/diagram")
async def upload_diagram(request: Request, name: str, file: UploadFile):
    if not storage.case_study_exists(name):
        raise HTTPException(404)
    contents = await file.read()
    try:
        storage.save_diagram(name, file.filename or "", contents)
    except ValueError as exc:
        return templates.TemplateResponse(
            request,
            "error.html",
            {"code": 422, "message": str(exc)},
            status_code=422,
        )
    return RedirectResponse(f"/{name}", status_code=303)


@router.post("/{name}/diagram/delete")
async def remove_diagram(name: str):
    storage.delete_diagram(name)
    return RedirectResponse(f"/{name}", status_code=303)


@router.get("/{name}/import")
async def import_form(request: Request, name: str):
    cfg = storage.load_case_study(name)
    return templates.TemplateResponse(request, "import.html", _ctx(cfg=cfg))


@router.post("/{name}/import")
async def import_excel(request: Request, name: str, file: UploadFile):
    import tempfile

    import pandas as pd

    cfg = storage.load_case_study(name)
    suffix = Path(file.filename or "upload.xlsx").suffix.lower()

    # ── YAML import: load directly into CaseStudyConfig ──────────────────────
    if suffix in (".yaml", ".yml"):
        try:
            import yaml as _yaml

            contents = await file.read()
            raw = _yaml.safe_load(contents.decode("utf-8")) or {}
            raw.setdefault("name", name)
            imported = CaseStudyConfig.model_validate(raw)
            # Keep the current case study name; everything else is replaced
            imported.name = name
            storage.save_case_study(imported)
        except Exception as exc:
            return templates.TemplateResponse(
                request,
                "import.html",
                _ctx(cfg=cfg, error=f"YAML import failed: {exc}"),
                status_code=422,
            )
        return RedirectResponse(f"/{name}", status_code=303)

    # ── Excel import ──────────────────────────────────────────────────────────
    from systemdefiner.yaml_schema import model_to_yaml

    tmp_path: Optional[str] = None
    try:
        contents = await file.read()
        with tempfile.NamedTemporaryFile(suffix=suffix or ".xlsx", delete=False) as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

        sheets = pd.read_excel(tmp_path, sheet_name=None, header=0, engine="openpyxl")
        yaml_data = model_to_yaml(sheets, source_file=file.filename)
    except Exception as exc:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)
        return templates.TemplateResponse(
            request,
            "import.html",
            _ctx(cfg=cfg, error=f"Import failed: {exc}"),
            status_code=422,
        )
    finally:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)

    _valid_logics = {e.value for e in ProcessLogic}
    _valid_stocks = {e.value for e in StockConfig}
    _valid_tcs = {e.value for e in TCConfig}

    if "model" in yaml_data:
        m = yaml_data["model"]
        cfg.model.start_year = m.get("start_year", cfg.model.start_year)
        cfg.model.end_year = m.get("end_year", cfg.model.end_year)
        if "elements" in m:
            cfg.model.elements = m["elements"]

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

    imported_tcs = _parse_tcs_from_yaml(yaml_data.get("transfer_coefficients", []))
    imported_keys = {(tc.process_id, tc.flow_id) for tc in imported_tcs}
    # Preserve existing TCs for any (process, flow) pair not covered by the import.
    preserved = [
        tc for tc in cfg.transfer_coefficients
        if (tc.process_id, tc.flow_id) not in imported_keys
    ]
    cfg.transfer_coefficients = preserved + imported_tcs
    cfg.bom_assembly = _parse_bom_from_yaml(yaml_data.get("bom_assembly", []))
    _apply_extra_yaml(yaml_data, cfg)

    storage.save_case_study(cfg)
    return RedirectResponse(f"/{name}", status_code=303)
