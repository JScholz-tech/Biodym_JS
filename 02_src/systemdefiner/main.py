from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from systemdefiner import storage
from systemdefiner.storage import CaseStudyNotFound
from systemdefiner.models.config_schema import (
    BomAssemblyEntry,
    DsmCategory,
    DsmComponentItem,
    BomAssemblyFlow,
    CaseStudyConfig,
    DsmParams,
    DynamicTCPoint,
    ElementHierarchyRule,
    Flow,
    FlowCapParams,
    FlowComposition,
    FlowDataEntry,
    FompParams,
    InitialStockEntry,
    LfgFraction,
    LfgParams,
    ModelSettings,
    Process,
    ProcessLogic,
    McParameter,
    ReferenceEntry,
    ScenarioDefinition,
    ScenarioModification,
    StockConfig,
    TCConfig,
    TransferCoefficient,
)

app = FastAPI(title="bioDYM SystemDefiner")

_HERE = Path(__file__).parent
app.mount("/static", StaticFiles(directory=_HERE / "static"), name="static")
templates = Jinja2Templates(directory=_HERE / "templates")

# Available in every template (base.html shows the diagram band when present).
templates.env.globals["study_has_diagram"] = (
    lambda name: storage.diagram_path(name) is not None
)


def _render_markdown(text: str) -> str:
    """Render a study description as sanitized HTML from Markdown.

    Falls back to escaped plain text (with line breaks preserved) if the
    optional markdown/bleach libraries are unavailable.
    """
    text = (text or "").strip()
    if not text:
        return ""
    try:
        import markdown as _md
        import bleach as _bleach

        html = _md.markdown(text, extensions=["extra", "sane_lists", "nl2br"])
        allowed_tags = {
            "p",
            "br",
            "hr",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "ul",
            "ol",
            "li",
            "strong",
            "em",
            "b",
            "i",
            "code",
            "pre",
            "blockquote",
            "a",
            "table",
            "thead",
            "tbody",
            "tr",
            "th",
            "td",
        }
        allowed_attrs = {"a": ["href", "title"]}
        clean = _bleach.clean(
            html, tags=allowed_tags, attributes=allowed_attrs, strip=True
        )
        return _bleach.linkify(clean)
    except Exception:
        from markupsafe import escape

        return str(escape(text)).replace("\n", "<br>")


templates.env.filters["markdown"] = _render_markdown


# ── Error handling ──────────────────────────────────────────────────────────
def _error_page(request: Request, code: int, message: str):
    return templates.TemplateResponse(
        request,
        "error.html",
        {"code": code, "message": message},
        status_code=code,
    )


@app.exception_handler(CaseStudyNotFound)
async def _handle_case_study_not_found(request: Request, exc: CaseStudyNotFound):
    return _error_page(request, 404, str(exc))


@app.exception_handler(StarletteHTTPException)
async def _handle_http_exception(request: Request, exc: StarletteHTTPException):
    # Render a friendly page for browser navigation; keep the status code.
    return _error_page(request, exc.status_code, exc.detail or "Request error")


@app.exception_handler(Exception)
async def _handle_unhandled(request: Request, exc: Exception):
    # Last resort: show the cause instead of a bare "Internal Server Error".
    return _error_page(request, 500, f"{type(exc).__name__}: {exc}")


def _ctx(**kwargs) -> dict:
    return kwargs


# ── Helpers ────────────────────────────────────────────────────────────────────


def _slug(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_\-]", "_", name.strip())


def _g(form, key: str) -> Optional[str]:
    v = form.get(key)
    return v.strip() if v and v.strip() else None


def _gf(form, key: str) -> Optional[float]:
    v = _g(form, key)
    return float(v) if v is not None else None


def _gi(form, key: str) -> Optional[int]:
    v = _g(form, key)
    return int(v) if v is not None else None


def _parse_tcs_from_yaml(raw_tcs: list) -> list[TransferCoefficient]:
    """Convert flat TC list from yaml_schema into TransferCoefficient objects."""
    result = []
    for tc in raw_tcs:
        tc_type = tc.get("tc_type", "static")
        if tc_type == "dynamic":
            points = [
                DynamicTCPoint(year=p["year"], values=p.get("values", {}))
                for p in tc.get("time_series", [])
            ]
            result.append(
                TransferCoefficient(
                    process_id=tc["process_id"],
                    flow_id=tc["flow_id"],
                    tc_type="dynamic",
                    time_series=points,
                )
            )
        else:
            result.append(
                TransferCoefficient(
                    process_id=tc["process_id"],
                    flow_id=tc["flow_id"],
                    tc_type="static",
                    values=tc.get("values", {}),
                )
            )
    return result


def _parse_bom_from_yaml(raw_bom: list) -> list[BomAssemblyEntry]:
    result = []
    for entry in raw_bom:
        pid = entry.get("process_id")
        if pid is None:
            continue
        flows = [
            BomAssemblyFlow(
                flow_id=f["flow_id"],
                output_flow_type=f.get("output_flow_type", ""),
                fractions=f.get("fractions", {}),
            )
            for f in entry.get("flows", [])
            if f.get("flow_id")
        ]
        result.append(BomAssemblyEntry(process_id=int(pid), flows=flows))
    return result


def _apply_extra_yaml(yaml_data: dict, cfg: "CaseStudyConfig") -> None:
    """Populate extra fields (compositions, hierarchy, flow_data, scenarios, MC) from yaml_data."""
    if yaml_data.get("element_hierarchy"):
        cfg.element_hierarchy = [
            ElementHierarchyRule(
                parent=str(r["parent"]),
                children=[str(c) for c in r.get("children", [])],
            )
            for r in yaml_data["element_hierarchy"]
        ]

    if yaml_data.get("flow_data"):
        cfg.flow_data = [
            FlowDataEntry(
                flow_id=str(fd["flow_id"]),
                element=str(fd.get("element", "material")),
                values={int(k): float(v) for k, v in fd.get("values", {}).items()},
            )
            for fd in yaml_data["flow_data"]
        ]

    if yaml_data.get("flow_compositions"):
        cfg.flow_compositions = [
            FlowComposition(
                flow_id=str(fc["flow_id"]),
                values={k: float(v) for k, v in fc.get("values", {}).items()},
            )
            for fc in yaml_data["flow_compositions"]
        ]

    if yaml_data.get("scenarios"):
        cfg.scenarios = []
        for s in yaml_data["scenarios"]:
            mods = [
                ScenarioModification(
                    parameter_name=m.get("parameter_name", ""),
                    parameter_type=m.get("parameter_type", ""),
                    operation=m.get("operation", "replace"),
                    new_value=float(m.get("new_value") or 0.0),
                    start_year=m.get("start_year"),
                    end_year=m.get("end_year"),
                )
                for m in s.get("modifications", [])
            ]
            cfg.scenarios.append(
                ScenarioDefinition(name=str(s["name"]), modifications=mods)
            )

    if yaml_data.get("mc_parameters"):
        cfg.mc_parameters = [
            McParameter(
                parameter_id=p.get("parameter_id", ""),
                enabled=bool(p.get("enabled", True)),
                distribution=p.get("distribution", "normal"),
                mean=p.get("mean"),
                std=p.get("std"),
                min=p.get("min"),
                max=p.get("max"),
                mode=p.get("mode"),
                operation=p.get("operation", "set"),
                start_year=p.get("start_year"),
                end_year=p.get("end_year"),
                flow_group=p.get("flow_group"),
            )
            for p in yaml_data["mc_parameters"]
        ]

    if yaml_data.get("initial_stocks"):
        cfg.initial_stocks = [
            InitialStockEntry(
                process_id=int(s["process_id"]),
                material_quantity=float(s.get("material_quantity", 0.0) or 0.0),
                composition={k: float(v) for k, v in s.get("composition", {}).items()},
                cohort_age_distribution_type=s.get(
                    "cohort_age_distribution_type", "Normal"
                ),
                cohort_mean_age=s.get("cohort_mean_age"),
                cohort_std_age=s.get("cohort_std_age"),
                cohort_max_age=s.get("cohort_max_age"),
                cohort_decay_constant=s.get("cohort_decay_constant"),
            )
            for s in yaml_data["initial_stocks"]
        ]


# ══════════════════════════════════════════════════════════════════════════════
# HOME — Case study list
# ══════════════════════════════════════════════════════════════════════════════


@app.get("/")
async def index(request: Request):
    studies = storage.list_case_studies()
    return templates.TemplateResponse(request, "index.html", _ctx(studies=studies))


@app.post("/create-from-excel")
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


@app.post("/new")
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


@app.post("/{name}/delete")
async def delete_case_study(name: str):
    storage.delete_case_study(name)
    return RedirectResponse("/", status_code=303)


@app.post("/{name}/clone")
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


# ══════════════════════════════════════════════════════════════════════════════
# CASE STUDY OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════

# Supported units of measurement (mass). Used as a label only — the engine does
# not convert between units, so this just keeps the model's unit consistent.
_UOM_OPTIONS = [
    ("g", "g — grams"),
    ("kg", "kg — kilograms"),
    ("t", "t — tonnes"),
    ("Mg", "Mg — megagrams (= tonnes)"),
    ("kt", "kt — kilotonnes"),
    ("Gg", "Gg — gigagrams (= kilotonnes)"),
    ("Mt", "Mt — megatonnes"),
    ("Tg", "Tg — teragrams (= megatonnes)"),
]


def _model_health(cfg) -> list[dict]:
    """Return a list of {level, message} issues that would hinder a model run.

    level is 'error' (likely breaks the engine) or 'warn' (probably unintended).
    """
    issues: list[dict] = []

    def err(msg):
        issues.append({"level": "error", "message": msg})

    def warn(msg):
        issues.append({"level": "warn", "message": msg})

    proc_ids = {p.id for p in cfg.processes}
    flow_ids = {f.id for f in cfg.flows}
    boundary = proc_ids | {0}  # process 0 is the implicit system boundary

    if not cfg.processes:
        err("No processes defined.")
    if cfg.processes and not cfg.flows:
        warn("No flows defined.")

    # The first element is the conserved total-mass balance and the hierarchy
    # root. The engine hard-codes the name "material" (index lookups plus
    # element == "material" gates), so renaming it breaks FOMP, composition
    # plots, flow-data matching and hierarchy recalculation.
    elems = cfg.model.elements
    if elems and elems[0] != "material":
        err(
            f"First element is '{elems[0]}' but must be named 'material' "
            f"(the total mass balance / hierarchy root). Rename it back to 'material' "
            f"— use the hierarchy level names or process names for custom labels."
        )

    # Flows pointing at processes that don't exist
    for f in cfg.flows:
        if f.from_process not in boundary:
            err(f"Flow {f.id}: source process P{f.from_process} does not exist.")
        if f.to_process not in boundary:
            err(f"Flow {f.id}: target process P{f.to_process} does not exist.")

    # Disconnected processes
    touched = {f.from_process for f in cfg.flows} | {f.to_process for f in cfg.flows}
    for p in cfg.processes:
        if p.id not in touched:
            warn(f"P{p.id} {p.name}: no flows (disconnected).")

    # DSM inflow split must sum to 1
    for p in cfg.processes:
        if p.dsm and p.dsm.categories:
            s = sum((c.inflow_split or 0.0) for c in p.dsm.categories)
            if abs(s - 1.0) > 1e-6:
                warn(
                    f"P{p.id} {p.name}: DSM inflow split sums to {s * 100:.1f}% (should be 100%)."
                )

    # TC-eligible processes with outgoing flows but no TCs (or only empty TC stubs)
    _tc_elig = {ProcessLogic.splitter, ProcessLogic.transformer, ProcessLogic.dsm, ProcessLogic.dsm_component}
    tc_pids_with_data = {
        tc.process_id for tc in cfg.transfer_coefficients
        if tc.time_series or tc.values  # has actual data, not just an empty stub
    }
    for p in cfg.processes:
        if p.logic in _tc_elig and p.tc_config != TCConfig.no_tc:
            if any(f.from_process == p.id for f in cfg.flows) and p.id not in tc_pids_with_data:
                warn(
                    f"P{p.id} {p.name}: outgoing flows but no transfer coefficients defined."
                )

    # Input flows without flow data
    input_pids = {p.id for p in cfg.processes if p.logic == ProcessLogic.input} | {0}
    fd_ids = {fd.flow_id for fd in cfg.flow_data}
    for f in cfg.flows:
        if f.from_process in input_pids and f.id not in fd_ids:
            warn(f"Input flow {f.id} has no flow data.")

    # BOM processes without a target_Product
    for p in cfg.processes:
        if p.logic == ProcessLogic.bom_assembler:
            # The BOM Assembler derives its element split from transfer
            # coefficients — with TCs disabled the engine produces wrong
            # results silently, so TCs are mandatory here.
            if p.tc_config == TCConfig.no_tc:
                err(
                    f"P{p.id} {p.name}: BOM_Assembler requires transfer coefficients "
                    f"(set TC Configuration to Static or Dynamic in the process editor)."
                )
            entry = next((e for e in cfg.bom_assembly if e.process_id == p.id), None)
            if not entry or not any(
                bf.output_flow_type == "target_Product" for bf in entry.flows
            ):
                warn(f"P{p.id} {p.name}: BOM process has no target_Product flow.")

    # FOMP processes: must have parameters and a (sensible) primary outflow
    for p in cfg.processes:
        if p.logic == ProcessLogic.fomp:
            fm = p.fomp
            if not fm:
                warn(f"P{p.id} {p.name}: FOMP process has no FOMP parameters defined.")
                continue
            if not fm.outflow_id:
                warn(
                    f"P{p.id} {p.name}: FOMP process has no outflow flow defined "
                    f"(set the decay outflow in the process editor)."
                )
            if not (0.0 <= (fm.f_labile or 0.0) <= 1.0):
                warn(
                    f"P{p.id} {p.name}: FOMP labile fraction {fm.f_labile} is outside 0–1."
                )
            if (fm.k_labile or 0.0) < 0 or (fm.k_recalcitrant or 0.0) < 0:
                warn(f"P{p.id} {p.name}: FOMP decay rate is negative.")

    # Monte Carlo parameter sanity — catches the percentage-vs-fraction trap.
    # TC_… are fractions (0–1); F_… flows are absolute amounts (a multiplier near
    # 1.0 under 'multiply'). A flow has no normalisation safety net, so a wrong
    # magnitude there silently blows up the result.
    def _flow_baseline(fid: str):
        fd = next(
            (d for d in cfg.flow_data if d.flow_id == fid and d.element == "material"),
            None,
        )
        if fd and fd.values:
            return max(fd.values.values())
        return None

    for mp in cfg.mc_parameters:
        pid = (mp.parameter_id or "").strip()
        if not pid:
            continue
        vals = {
            k: v
            for k, v in (("mean", mp.mean), ("min", mp.min), ("max", mp.max), ("mode", mp.mode))
            if v is not None
        }
        op = (mp.operation or "").strip().lower()
        if pid.startswith("TC"):
            over = {k: v for k, v in vals.items() if v > 1.0}
            if over:
                shown = ", ".join(f"{k}={v:g}" for k, v in over.items())
                warn(
                    f"MC {pid}: transfer coefficients are fractions 0–1, but {shown} > 1 "
                    f"— did you enter a percentage? (use 0.3, not 30)."
                )
            if any(v < 0 for v in vals.values()):
                warn(f"MC {pid}: transfer coefficient has a negative value.")
        elif pid.startswith("F"):
            if op in ("multiply", "scale"):
                if mp.mean is not None and (mp.mean <= 0 or mp.mean > 5):
                    warn(
                        f"MC {pid}: 'multiply' expects a multiplier near 1.0 (e.g. 1.1 for +10%), "
                        f"but mean={mp.mean:g}. Did you enter an absolute amount or a percentage?"
                    )
            elif op in ("set", "replace", "add"):
                base = _flow_baseline(pid)
                if base and base > 0 and mp.mean and mp.mean > 0:
                    ratio = mp.mean / base
                    if ratio > 10 or ratio < 0.1:
                        warn(
                            f"MC {pid}: mean={mp.mean:g} is {ratio:.0f}× the baseline flow "
                            f"(~{base:g}) — check the units/magnitude."
                        )

    # InitialStock processes without a defined stock
    for p in cfg.processes:
        if p.stock in (
            StockConfig.initial_stock_cohort,
            StockConfig.initial_stock_decay,
        ):
            e = next((s for s in cfg.initial_stocks if s.process_id == p.id), None)
            if not e or (e.material_quantity or 0) <= 0:
                warn(
                    f"P{p.id} {p.name}: initial-stock process has no initial stock quantity."
                )
            elif p.logic not in (ProcessLogic.dsm, ProcessLogic.dsm_component):
                warn(
                    f"P{p.id} {p.name}: initial stock only depletes through a DSM process "
                    f"(set logic to DSM or DSM_Component); on '{p.logic.value}' the stock is placed but never released."
                )

    # Orphaned initial-stock entries: present in the config but the process is
    # gone or no longer an initial-stock process, so the engine ignores them.
    _is_proc = {p.id: p for p in cfg.processes}
    for s in cfg.initial_stocks:
        p = _is_proc.get(s.process_id)
        if p is None:
            warn(f"Initial stock references P{s.process_id}, which does not exist.")
        elif p.stock not in (
            StockConfig.initial_stock_cohort,
            StockConfig.initial_stock_decay,
        ):
            warn(
                f"P{s.process_id} {p.name}: has an initial-stock entry but its stock "
                f"config is '{p.stock.value}' — the entry is ignored (set an InitialStock "
                f"stock config, or remove it via the process editor)."
            )

    # FlowCap processes without a defined cap (otherwise the cap is silently ignored)
    for p in cfg.processes:
        if p.logic == ProcessLogic.flowcap:
            fc = p.flowcap
            if not fc or not fc.capped_flow_id:
                warn(
                    f"P{p.id} {p.name}: FlowCap process has no capped flow defined "
                    f"(set the capped/overflow flows in the process editor)."
                )
            elif not fc.cap_series:
                warn(
                    f"P{p.id} {p.name}: FlowCap has a capped flow but no cap values "
                    f"(add a Year + cap to the capacity series)."
                )

    # Dangling outflow pointers
    def _chk(pid, pname, label, fid):
        if fid and fid not in flow_ids:
            warn(f"P{pid} {pname}: {label} '{fid}' is not a defined flow.")

    for p in cfg.processes:
        if p.fomp:
            _chk(p.id, p.name, "FOMP outflow", p.fomp.outflow_id)
            _chk(p.id, p.name, "FOMP secondary outflow", p.fomp.outflow_id_2)
        if p.lfg:
            _chk(p.id, p.name, "LFG CH4 outflow", p.lfg.outflow_ch4_id)
            _chk(p.id, p.name, "LFG CO2 outflow", p.lfg.outflow_co2_id)
            _chk(p.id, p.name, "LFG leachate outflow", p.lfg.outflow_leachate_id)
        if p.flowcap:
            _chk(p.id, p.name, "FlowCap capped flow", p.flowcap.capped_flow_id)
            _chk(p.id, p.name, "FlowCap overflow flow", p.flowcap.overflow_flow_id)

    # Selected scenarios that aren't defined
    defined = {s.name for s in cfg.scenarios}
    for nm in cfg.model.selected_scenarios:
        if nm and nm not in defined:
            warn(f"Selected scenario '{nm}' is not defined in the Scenario Manager.")

    return issues


@app.get("/{name}")
async def case_study_overview(request: Request, name: str):
    if not storage.case_study_exists(name):
        raise HTTPException(404, f"Case study '{name}' not found")
    cfg = storage.load_case_study(name)
    return templates.TemplateResponse(
        request,
        "case_study.html",
        _ctx(cfg=cfg, health=_model_health(cfg), uom_options=_UOM_OPTIONS),
    )


@app.post("/{name}/settings")
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


# ══════════════════════════════════════════════════════════════════════════════
# PROCESSES
# ══════════════════════════════════════════════════════════════════════════════


@app.get("/{name}/processes")
async def processes_list(request: Request, name: str):
    cfg = storage.load_case_study(name)
    ids = sorted(p.id for p in cfg.processes)
    has_id_gap = ids != list(range(len(ids)))
    return templates.TemplateResponse(
        request,
        "processes.html",
        _ctx(
            cfg=cfg,
            logic_options=list(ProcessLogic),
            stock_options=list(StockConfig),
            tc_options=list(TCConfig),
            has_id_gap=has_id_gap,
        ),
    )


@app.post("/{name}/processes/new")
async def process_new(request: Request, name: str):
    form = await request.form()
    cfg = storage.load_case_study(name)

    # Process IDs are 0-based to match the BioDYM Excel convention (P0 is the
    # system boundary / Atmosphere). First process added gets id 0. Reuse the
    # lowest free id so a gap left by a deleted process gets filled instead of
    # leaving a permanent hole in the numbering.
    existing_ids = {p.id for p in cfg.processes}
    new_id = next(i for i in range(len(existing_ids) + 1) if i not in existing_ids)
    _valid_logic = {e.value for e in ProcessLogic}
    _valid_stock = {e.value for e in StockConfig}
    _valid_tc = {e.value for e in TCConfig}
    logic_raw = form.get("logic", ProcessLogic.splitter.value)
    logic = (
        ProcessLogic(logic_raw) if logic_raw in _valid_logic else ProcessLogic.splitter
    )
    stock_raw = form.get("stock", StockConfig.no_stock.value)
    tc_raw = form.get("tc_config", "No TC")
    process = Process(
        id=new_id,
        name=form.get("name", f"Process {new_id}"),
        logic=logic,
        stock=StockConfig(stock_raw)
        if stock_raw in _valid_stock
        else StockConfig.no_stock,
        tc_config=TCConfig(tc_raw) if tc_raw in _valid_tc else TCConfig.no_tc,
        fomp=_parse_fomp(form) if logic == ProcessLogic.fomp else None,
        dsm=_parse_dsm_component(form) if logic == ProcessLogic.dsm_component
            else _parse_dsm(form) if logic == ProcessLogic.dsm else None,
        lfg=_parse_lfg(form) if logic == ProcessLogic.lfg else None,
        flowcap=_parse_flowcap(form, new_id) if logic == ProcessLogic.flowcap else None,
    )
    cfg.processes.append(process)
    storage.save_case_study(cfg)
    # Land on the full editor so module parameters (FOMP/DSM/LFG/FlowCap) can
    # be configured in one complete place rather than a duplicated add form.
    return RedirectResponse(f"/{name}/processes/{new_id}/edit", status_code=303)


@app.get("/{name}/processes/{pid}/edit")
async def process_edit_form(request: Request, name: str, pid: int):
    cfg = storage.load_case_study(name)
    process = next((p for p in cfg.processes if p.id == pid), None)
    if not process:
        raise HTTPException(404)
    return templates.TemplateResponse(
        request,
        "process_edit.html",
        _ctx(
            cfg=cfg,
            process=process,
            logic_options=list(ProcessLogic),
            stock_options=list(StockConfig),
            tc_options=list(TCConfig),
        ),
    )


@app.post("/{name}/processes/{pid}/edit")
async def process_edit_save(request: Request, name: str, pid: int):
    form = await request.form()
    cfg = storage.load_case_study(name)
    process = next((p for p in cfg.processes if p.id == pid), None)
    if not process:
        raise HTTPException(404)

    _valid_logic = {e.value for e in ProcessLogic}
    _valid_stock = {e.value for e in StockConfig}
    _valid_tc = {e.value for e in TCConfig}
    logic_raw = form.get("logic", process.logic.value)
    logic = ProcessLogic(logic_raw) if logic_raw in _valid_logic else process.logic
    stock_raw = form.get("stock", process.stock.value)
    tc_raw = form.get("tc_config", process.tc_config.value)
    process.name = form.get("name", process.name)
    process.logic = logic
    process.stock = (
        StockConfig(stock_raw) if stock_raw in _valid_stock else process.stock
    )
    process.tc_config = TCConfig(tc_raw) if tc_raw in _valid_tc else TCConfig.no_tc
    process.fomp = _parse_fomp(form) if logic == ProcessLogic.fomp else None
    process.dsm = (
        _parse_dsm_component(form) if logic == ProcessLogic.dsm_component
        else _parse_dsm(form) if logic == ProcessLogic.dsm
        else None
    )
    process.lfg = _parse_lfg(form) if logic == ProcessLogic.lfg else None
    process.flowcap = _parse_flowcap(form, pid) if logic == ProcessLogic.flowcap else None

    # If the process no longer carries an initial stock, drop any orphaned entry
    # so it can't linger in the config (and silently feed the engine).
    if process.stock not in (
        StockConfig.initial_stock_cohort,
        StockConfig.initial_stock_decay,
    ):
        cfg.initial_stocks = [s for s in cfg.initial_stocks if s.process_id != pid]

    storage.save_case_study(cfg)
    return RedirectResponse(f"/{name}/processes", status_code=303)


@app.post("/{name}/processes/{pid}/delete")
async def process_delete(name: str, pid: int):
    cfg = storage.load_case_study(name)
    _delete_process_cascade(cfg, pid)
    storage.save_case_study(cfg)
    return RedirectResponse(f"/{name}/processes", status_code=303)


def _compact_process_ids(cfg) -> dict:
    """Renumber process IDs to a contiguous 0..N-1 range (gaps left by deletions
    break the engine, which expects 0-based contiguous IDs).

    Cascades the renumber through every reference: flow endpoints, the
    ``F_<from>_<to>`` flow IDs and all string references to them (TCs, flow
    compositions, flow data, BOM flows, FOMP/LFG/FlowCap outflow IDs), plus the
    ``process_id`` on TCs, BOM entries and initial stocks. Returns the old→new
    id map (empty when already contiguous).
    """
    old_ids = sorted(p.id for p in cfg.processes)
    id_map = {old: new for new, old in enumerate(old_ids)}
    if all(o == n for o, n in id_map.items()):
        return {}

    for p in cfg.processes:
        p.id = id_map[p.id]
    for f in cfg.flows:
        f.from_process = id_map.get(f.from_process, f.from_process)
        f.to_process = id_map.get(f.to_process, f.to_process)

    # Rename F_<from>_<to> flow IDs to match new endpoints (collision-safe).
    existing = {f.id for f in cfg.flows}
    flow_rename: dict[str, str] = {}
    for f in cfg.flows:
        if not re.fullmatch(r"F_\d+_\d+", f.id):
            continue
        cand = f"F_{f.from_process:02d}_{f.to_process:02d}"
        if cand == f.id or cand in existing:
            continue
        existing.discard(f.id)
        existing.add(cand)
        flow_rename[f.id] = cand
        f.id = cand

    def _rn(fid):
        return flow_rename.get(fid, fid) if fid else fid

    for tc in cfg.transfer_coefficients:
        tc.process_id = id_map.get(tc.process_id, tc.process_id)
        tc.flow_id = _rn(tc.flow_id)
    for fc in cfg.flow_compositions:
        fc.flow_id = _rn(fc.flow_id)
    for fd in cfg.flow_data:
        fd.flow_id = _rn(fd.flow_id)
    for e in cfg.bom_assembly:
        e.process_id = id_map.get(e.process_id, e.process_id)
        for bf in e.flows:
            bf.flow_id = _rn(bf.flow_id)
    for s in cfg.initial_stocks:
        s.process_id = id_map.get(s.process_id, s.process_id)
    for p in cfg.processes:
        if p.fomp:
            p.fomp.outflow_id = _rn(p.fomp.outflow_id)
            p.fomp.outflow_id_2 = _rn(p.fomp.outflow_id_2)
        if p.lfg:
            p.lfg.outflow_ch4_id = _rn(p.lfg.outflow_ch4_id)
            p.lfg.outflow_co2_id = _rn(p.lfg.outflow_co2_id)
            p.lfg.outflow_leachate_id = _rn(p.lfg.outflow_leachate_id)
        if p.flowcap:
            p.flowcap.capped_flow_id = _rn(p.flowcap.capped_flow_id)
            p.flowcap.overflow_flow_id = _rn(p.flowcap.overflow_flow_id)
    return id_map


@app.post("/{name}/processes/renumber")
async def processes_renumber(name: str):
    cfg = storage.load_case_study(name)
    _compact_process_ids(cfg)
    storage.save_case_study(cfg)
    return RedirectResponse(f"/{name}/processes", status_code=303)


def _parse_fomp(form) -> FompParams:
    def _flt(key, default):
        v = (form.get(key) or "").strip()
        try:
            return float(v) if v else default
        except ValueError:
            return default

    return FompParams(
        f_labile=_flt("fomp_f_labile", 0.5),
        k_labile=_flt("fomp_k_labile", 1.0),
        k_recalcitrant=_flt("fomp_k_recalcitrant", 0.01),
        outflow_id=form.get("fomp_outflow_id", "") or "",
        outflow_id_2=form.get("fomp_outflow_id_2", "") or "",
        refs=[c.strip() for c in form.getlist("fomp_refs") if c.strip()],
    )


def _parse_dsm(form) -> DsmParams:
    categories: list[DsmCategory] = []
    i = 0
    while f"dsm_cat_{i}_lifetime_type" in form:

        def _flt(key, default=None):
            v = form.get(key, "").strip()
            try:
                return float(v) if v else default
            except ValueError:
                return default

        categories.append(
            DsmCategory(
                name=(form.get(f"dsm_cat_{i}_name") or f"Cat_{i + 1}").strip(),
                # UI shows split as a percent (0–100); stored as a 0–1 fraction.
                inflow_split=(_flt(f"dsm_cat_{i}_inflow_split", 100.0) or 0.0) / 100.0,
                lifetime_type=form.get(f"dsm_cat_{i}_lifetime_type", "Normal"),
                lifetime_mean=_flt(f"dsm_cat_{i}_lifetime_mean"),
                lifetime_std=_flt(f"dsm_cat_{i}_lifetime_std"),
                lifetime_shape=_flt(f"dsm_cat_{i}_lifetime_shape"),
                lifetime_scale=_flt(f"dsm_cat_{i}_lifetime_scale"),
            )
        )
        i += 1
    if not categories:
        categories = [DsmCategory()]
    return DsmParams(
        categories=categories,
        refs=[c.strip() for c in form.getlist("dsm_refs") if c.strip()],
    )


def _parse_dsm_component(form) -> DsmParams:
    """Parse DSM_Component form: device categories (dsmc_cat_*) + component rows (dsm_comp_*).

    Uses a separate dsmc_cat_* prefix to avoid colliding with the standard DSM block's
    dsm_cat_* fields — both blocks coexist in the DOM, only one is visible at a time.
    """
    def _s(key): return (form.get(key) or "").strip()
    def _f(key, default=None):
        v = _s(key)
        try: return float(v) if v else default
        except ValueError: return default

    # Read component element names first (needed to build per-category lifetime dicts)
    _comp_elems: list[str] = []
    _j = 0
    while f"dsm_comp_{_j}_element" in form:
        _comp_elems.append(_s(f"dsm_comp_{_j}_element"))
        _j += 1

    # Device lifetime categories (with optional per-component lifetime overrides)
    cats: list[DsmCategory] = []
    i = 0
    while f"dsmc_cat_{i}_name" in form:
        comp_lts: dict[str, float] = {}
        for j, elem in enumerate(_comp_elems):
            val = _f(f"dsmc_cat_{i}_comp_lt_{j}")
            if val is not None and val > 0 and elem:
                comp_lts[elem] = val
        cats.append(DsmCategory(
            name=_s(f"dsmc_cat_{i}_name") or "Default",
            inflow_split=(_f(f"dsmc_cat_{i}_inflow_split") or 0.0) / 100.0,
            lifetime_type=_s(f"dsmc_cat_{i}_lifetime_type") or "Normal",
            lifetime_mean=_f(f"dsmc_cat_{i}_lifetime_mean"),
            lifetime_std=_f(f"dsmc_cat_{i}_lifetime_std"),
            lifetime_shape=_f(f"dsmc_cat_{i}_lifetime_shape"),
            lifetime_scale=_f(f"dsmc_cat_{i}_lifetime_scale"),
            component_lifetimes=comp_lts,
        ))
        i += 1
    if not cats:
        cats = [DsmCategory(name="Default", inflow_split=1.0, lifetime_type="Normal")]

    # Component renewal rows
    components: list[DsmComponentItem] = []
    i = 0
    while f"dsm_comp_{i}_element" in form:
        elem = _s(f"dsm_comp_{i}_element")
        mean_lt = _f(f"dsm_comp_{i}_mean_lifetime")
        outflow = _s(f"dsm_comp_{i}_sparepart_outflow")
        inflow  = _s(f"dsm_comp_{i}_sparepart_inflow")
        if elem and mean_lt:
            components.append(DsmComponentItem(
                element=elem,
                mean_lifetime=mean_lt,
                sparepart_outflow=outflow,
                sparepart_inflow=inflow,
            ))
        i += 1

    refs = [v for v in form.getlist("dsm_refs") if v]
    return DsmParams(categories=cats, components=components, refs=refs)


def _parse_lfg(form) -> LfgParams:
    fractions: list[LfgFraction] = []
    # Collect row indices tolerantly (a removal can leave gaps in the numbering);
    # scanning until the first missing index would drop fractions past the gap.
    frac_indices = sorted(
        {
            int(m.group(1))
            for key in form.keys()
            if (m := re.fullmatch(r"lfg_frac_(\d+)_name", key))
        }
    )
    for idx in frac_indices:
        fractions.append(
            LfgFraction(
                name=form.get(f"lfg_frac_{idx}_name", "") or "",
                k_j=float(form.get(f"lfg_frac_{idx}_k_j", 0.1) or 0.1),
                doc_j=float(form.get(f"lfg_frac_{idx}_doc_j", 0.5) or 0.5),
                f_input_j=float(form.get(f"lfg_frac_{idx}_f_input_j", 1.0) or 1.0),
                f_ash_j=float(form.get(f"lfg_frac_{idx}_f_ash_j", 0.05) or 0.05),
            )
        )

    def _flt(key, default):
        v = (form.get(key) or "").strip()
        try:
            return float(v) if v else default
        except ValueError:
            return default

    return LfgParams(
        mcf=_flt("lfg_mcf", 1.0),
        doc_f=_flt("lfg_doc_f", 0.5),
        f_ch4=_flt("lfg_f_ch4", 0.5),
        ox=_flt("lfg_ox", 0.1),
        phi=_flt("lfg_phi", 1.0),
        f_capture=_flt("lfg_f_capture", 0.0),
        outflow_ch4_id=form.get("lfg_outflow_ch4_id", "") or "",
        outflow_co2_id=form.get("lfg_outflow_co2_id", "") or "",
        outflow_leachate_id=form.get("lfg_outflow_leachate_id", "") or "",
        fractions=fractions,
        refs=[c.strip() for c in form.getlist("lfg_refs") if c.strip()],
    )


def _parse_flowcap(form, process_id: int) -> Optional[FlowCapParams]:
    capped = form.get("flowcap_capped_flow_id", "") or ""
    if not capped:
        return None
    cap_series: dict[int, float] = {}
    # Collect row indices tolerantly: a client-side row removal can leave gaps
    # in the flowcap_year_{i} numbering, so never stop at the first missing
    # index — that would silently drop every capacity point past the gap.
    cap_indices = sorted(
        {
            int(m.group(1))
            for key in form.keys()
            if (m := re.fullmatch(r"flowcap_year_(\d+)", key))
        }
    )
    for idx in cap_indices:
        try:
            year = int(float(form[f"flowcap_year_{idx}"]))
            cap = float(form.get(f"flowcap_cap_{idx}", 0) or 0)
            if year:
                cap_series[year] = cap
        except (ValueError, TypeError):
            pass
    # ParameterDict key under which the engine registers the cap series, so
    # the Scenario Manager and MC can switch the cap. Auto-derive the
    # canonical name when the form leaves it blank; keep hand-authored IDs.
    cap_tc_id = (form.get("flowcap_cap_tc_id", "") or "").strip()
    if not cap_tc_id:
        cap_tc_id = f"TC_Cap_{process_id:02d}"
    return FlowCapParams(
        capped_flow_id=capped,
        overflow_flow_id=form.get("flowcap_overflow_flow_id", "") or "",
        cap_series=cap_series,
        cap_tc_id=cap_tc_id,
        refs=[c.strip() for c in form.getlist("flowcap_refs") if c.strip()],
    )


# ══════════════════════════════════════════════════════════════════════════════
# FLOWS
# ══════════════════════════════════════════════════════════════════════════════


def _process_name(cfg, pid: int) -> str:
    """Return a process's name (falls back to ``P{id}`` if unnamed/unknown)."""
    p = next((p for p in cfg.processes if p.id == pid), None)
    return p.name if p and p.name else f"P{pid}"


def _next_flow_id(cfg, from_p: int, to_p: int) -> str:
    """Auto-generate a flow ID as ``F_{from}_{to}`` (Excel convention, e.g. F_12_16).

    Process IDs are zero-padded to at least two digits. If a flow with that ID
    already exists (e.g. a second flow between the same two processes), a numeric
    suffix is appended: ``F_12_16``, ``F_12_16_2``, ``F_12_16_3``, …
    """
    base = f"F_{from_p:02d}_{to_p:02d}"
    existing = {str(f.id) for f in cfg.flows}
    if base not in existing:
        return base
    i = 2
    while f"{base}_{i}" in existing:
        i += 1
    return f"{base}_{i}"


def _rename_flow_id(cfg, old_id: str, new_id: str) -> None:
    """Propagate a flow-ID rename to every place that references a flow ID.

    Keeps transfer coefficients, flow data, compositions, BOM flows, and the
    process outflow pointers (FOMP / LFG / FlowCap) consistent, plus any
    scenario / MC parameters keyed exactly by the old flow ID.
    """
    for tc in cfg.transfer_coefficients:
        if tc.flow_id == old_id:
            tc.flow_id = new_id
    for fc in cfg.flow_compositions:
        if fc.flow_id == old_id:
            fc.flow_id = new_id
    for fd in cfg.flow_data:
        if fd.flow_id == old_id:
            fd.flow_id = new_id
    for entry in cfg.bom_assembly:
        for bf in entry.flows:
            if bf.flow_id == old_id:
                bf.flow_id = new_id
    for p in cfg.processes:
        if p.fomp:
            if p.fomp.outflow_id == old_id:
                p.fomp.outflow_id = new_id
            if p.fomp.outflow_id_2 == old_id:
                p.fomp.outflow_id_2 = new_id
        if p.lfg:
            if p.lfg.outflow_ch4_id == old_id:
                p.lfg.outflow_ch4_id = new_id
            if p.lfg.outflow_co2_id == old_id:
                p.lfg.outflow_co2_id = new_id
            if p.lfg.outflow_leachate_id == old_id:
                p.lfg.outflow_leachate_id = new_id
        if p.flowcap:
            if p.flowcap.capped_flow_id == old_id:
                p.flowcap.capped_flow_id = new_id
            if p.flowcap.overflow_flow_id == old_id:
                p.flowcap.overflow_flow_id = new_id
    for sc in cfg.scenarios:
        for mod in sc.modifications:
            if mod.parameter_name == old_id:
                mod.parameter_name = new_id
    for mc in cfg.mc_parameters:
        if mc.parameter_id == old_id:
            mc.parameter_id = new_id


def _purge_flow_references(cfg, flow_ids: set) -> None:
    """Remove every reference to the given flow IDs across the config.

    Used when flows disappear (e.g. their process is deleted) so nothing is
    left pointing at a flow that no longer exists.
    """
    if not flow_ids:
        return
    cfg.transfer_coefficients = [
        tc for tc in cfg.transfer_coefficients if tc.flow_id not in flow_ids
    ]
    cfg.flow_compositions = [
        fc for fc in cfg.flow_compositions if fc.flow_id not in flow_ids
    ]
    cfg.flow_data = [fd for fd in cfg.flow_data if fd.flow_id not in flow_ids]
    for entry in cfg.bom_assembly:
        entry.flows = [bf for bf in entry.flows if bf.flow_id not in flow_ids]
    for p in cfg.processes:
        if p.fomp:
            if p.fomp.outflow_id in flow_ids:
                p.fomp.outflow_id = ""
            if p.fomp.outflow_id_2 in flow_ids:
                p.fomp.outflow_id_2 = None
        if p.lfg:
            if p.lfg.outflow_ch4_id in flow_ids:
                p.lfg.outflow_ch4_id = ""
            if p.lfg.outflow_co2_id in flow_ids:
                p.lfg.outflow_co2_id = ""
            if p.lfg.outflow_leachate_id in flow_ids:
                p.lfg.outflow_leachate_id = ""
        if p.flowcap:
            if p.flowcap.capped_flow_id in flow_ids:
                p.flowcap.capped_flow_id = ""
            if p.flowcap.overflow_flow_id in flow_ids:
                p.flowcap.overflow_flow_id = ""
    for sc in cfg.scenarios:
        sc.modifications = [
            m for m in sc.modifications if m.parameter_name not in flow_ids
        ]
    cfg.mc_parameters = [
        mc for mc in cfg.mc_parameters if mc.parameter_id not in flow_ids
    ]


def _delete_process_cascade(cfg, pid: int) -> None:
    """Delete a process and everything that depends on it.

    Removes the process, every flow touching it (in or out), its transfer
    coefficients and BOM entry, and then purges all remaining references to the
    now-removed flows (TCs, flow data, compositions, BOM flows, FOMP/LFG/FlowCap
    outflow pointers, scenario/MC parameters).
    """
    orphan_flow_ids = {
        f.id for f in cfg.flows if f.from_process == pid or f.to_process == pid
    }
    cfg.processes = [p for p in cfg.processes if p.id != pid]
    cfg.flows = [f for f in cfg.flows if f.from_process != pid and f.to_process != pid]
    cfg.transfer_coefficients = [
        tc for tc in cfg.transfer_coefficients if tc.process_id != pid
    ]
    cfg.bom_assembly = [e for e in cfg.bom_assembly if e.process_id != pid]
    cfg.initial_stocks = [s for s in cfg.initial_stocks if s.process_id != pid]
    _purge_flow_references(cfg, orphan_flow_ids)


@app.get("/{name}/flows")
async def flows_list(request: Request, name: str):
    cfg = storage.load_case_study(name)
    return templates.TemplateResponse(request, "flows.html", _ctx(cfg=cfg))


@app.post("/{name}/flows/new")
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


@app.get("/{name}/flows/{fid}/edit")
async def flow_edit_form(request: Request, name: str, fid: str):
    cfg = storage.load_case_study(name)
    flow = next((f for f in cfg.flows if f.id == fid), None)
    if not flow:
        raise HTTPException(404)
    return templates.TemplateResponse(
        request, "flow_edit.html", _ctx(cfg=cfg, flow=flow)
    )


@app.post("/{name}/flows/{fid}/edit")
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

    storage.save_case_study(cfg)
    return RedirectResponse(f"/{name}/flows", status_code=303)


@app.post("/{name}/flows/{fid}/delete")
async def flow_delete(name: str, fid: str):
    cfg = storage.load_case_study(name)
    cfg.flows = [f for f in cfg.flows if f.id != fid]
    _purge_flow_references(cfg, {fid})
    storage.save_case_study(cfg)
    return RedirectResponse(f"/{name}/flows", status_code=303)


# ══════════════════════════════════════════════════════════════════════════════
# TRANSFER COEFFICIENTS
# ══════════════════════════════════════════════════════════════════════════════


@app.get("/{name}/tcs")
async def tcs_overview(request: Request, name: str):
    cfg = storage.load_case_study(name)
    # Only Splitter, Transformer, and DSM processes use TCs in the engine
    _tc_eligible = {ProcessLogic.splitter, ProcessLogic.transformer, ProcessLogic.dsm, ProcessLogic.dsm_component}
    tc_processes = [p for p in cfg.processes if p.logic in _tc_eligible]
    return templates.TemplateResponse(
        request, "tcs.html", _ctx(cfg=cfg, tc_processes=tc_processes)
    )


@app.get("/{name}/tcs/{pid}")
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


@app.post("/{name}/tcs/{pid}")
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


# ══════════════════════════════════════════════════════════════════════════════
# SCENARIO MANAGER
# ══════════════════════════════════════════════════════════════════════════════

_SCENARIO_OPERATIONS = ["replace", "multiply", "add"]
_SCENARIO_PARAM_TYPES = ["", "Flow", "TC", "DSM", "FOMP", "IS"]


def _build_scenario_params(cfg: "CaseStudyConfig") -> list[dict]:
    """Build the list of known, selectable parameters for the scenario editor."""
    params: list[dict] = []
    unit = cfg.model.unit_of_measurement or "Mg"

    # ── Flows ──────────────────────────────────────────────────────────────────
    proc_names = {p.id: p.name for p in cfg.processes}
    for flow in cfg.flows:
        src = proc_names.get(flow.from_process, f"P{flow.from_process}")
        dst = proc_names.get(flow.to_process, f"P{flow.to_process}")
        params.append(
            {
                "name": flow.id,
                "label": f"{flow.id} — {flow.name} ({src} → {dst})",
                "group": "Flows",
                "type": "Flow",
                "hint": f"{unit}/yr",
                "step": "any",
                "min": "0",
                "max": "",
            }
        )

    # ── Transfer Coefficients ──────────────────────────────────────────────────
    # Iterate processes → outgoing flows so entries are generated even when no
    # TC is stored (e.g. Transformer with tc_config=Dynamic and empty 2_3 sheet).
    # BioDYM naming (matches the Excel template): every element uses
    # TC_E{n}_{from:02d}_{to:02d}, with E1 = material, E2 = WC, …
    _tc_eligible = {ProcessLogic.splitter, ProcessLogic.transformer, ProcessLogic.dsm, ProcessLogic.dsm_component}
    # Build TC lookup: (process_id, flow_id) → first matching TC (for current values)
    _tc_lookup: dict[tuple, "TransferCoefficient"] = {}
    for _tc in cfg.transfer_coefficients:
        _key = (_tc.process_id, _tc.flow_id)
        if _key not in _tc_lookup:
            _tc_lookup[_key] = _tc

    seen_flow_proc: set[tuple] = set()
    for proc in cfg.processes:
        if proc.logic not in _tc_eligible:
            continue
        outgoing = [f for f in cfg.flows if f.from_process == proc.id]
        for flow in outgoing:
            pair = (proc.id, flow.id)
            if pair in seen_flow_proc:
                continue
            seen_flow_proc.add(pair)

            from_p = flow.from_process
            to_p = flow.to_process
            src = proc_names.get(from_p, f"P{from_p}")
            dst = proc_names.get(to_p, f"P{to_p}")
            mat_tc_name = f"TC_E1_{from_p:02d}_{to_p:02d}"
            stored_tc = _tc_lookup.get((proc.id, flow.id))

            if proc.logic == ProcessLogic.transformer:
                # TC naming mirrors yaml_to_excel_dataframes: n = idx+1 (1-based)
                # material (idx=0): TC_from_to (no E prefix)
                # element idx≥1:   TC_E{idx+1}_from_to  (E2 for WC, E3 for DM, E4 for CC …)
                for e_idx, elem in enumerate(cfg.model.elements):
                    n = e_idx + 1
                    if e_idx == 0:
                        tc_pname = mat_tc_name
                    else:
                        tc_pname = f"TC_E{n}_{from_p:02d}_{to_p:02d}"
                    cur = (
                        stored_tc.values.get(elem)
                        if stored_tc and stored_tc.values
                        else None
                    )
                    cur_str = f"  [current: {cur:.3f}]" if cur is not None else ""
                    params.append(
                        {
                            "name": tc_pname,
                            "label": f"{tc_pname} — {flow.name} | {elem} (E{n}){cur_str}",
                            "group": "TCs — Transformer (per element)",
                            "type": "TC",
                            "hint": f"fraction 0–1  ({elem})",
                            "step": "0.001",
                            "min": "0",
                            "max": "1",
                        }
                    )
            else:
                # Splitter / DSM: material TC only
                cur = (
                    stored_tc.values.get("material")
                    if stored_tc and stored_tc.values
                    else None
                )
                cur_str = f"  [current: {cur:.3f}]" if cur is not None else ""
                params.append(
                    {
                        "name": mat_tc_name,
                        "label": f"{mat_tc_name} — {flow.name} | material{cur_str}",
                        "group": "TCs — Splitter / DSM (material)",
                        "type": "TC",
                        "hint": "fraction 0–1  (material)",
                        "step": "0.001",
                        "min": "0",
                        "max": "1",
                    }
                )

    # ── DSM Parameters ─────────────────────────────────────────────────────────
    for proc in cfg.processes:
        if proc.logic not in (ProcessLogic.dsm, ProcessLogic.dsm_component) or not proc.dsm:
            continue
        pid, pn = proc.id, proc.name
        cats = proc.dsm.categories if proc.dsm.categories else []
        n_cats = max(len(cats), 1)
        for ci in range(1, n_cats + 1):
            cat_label = cats[ci - 1].name if ci <= len(cats) else f"Cat {ci}"
            params.extend(
                [
                    {
                        "name": f"P{pid:02d}_DSM_Inflow_Split_[%]_Cat_{ci}",
                        "label": f"P{pid:02d} {pn} — Inflow Split Cat {ci} ({cat_label})",
                        "group": "DSM",
                        "type": "DSM",
                        "hint": "fraction 0–1",
                        "step": "0.01",
                        "min": "0",
                        "max": "1",
                    },
                    {
                        "name": f"P{pid:02d}_DSM_Lifetime_Mean_Cat_{ci}",
                        "label": f"P{pid:02d} {pn} — Lifetime Mean Cat {ci} ({cat_label})",
                        "group": "DSM",
                        "type": "DSM",
                        "hint": "years",
                        "step": "0.1",
                        "min": "0",
                        "max": "",
                    },
                    {
                        "name": f"P{pid:02d}_DSM_Lifetime_StdDev_Cat_{ci}",
                        "label": f"P{pid:02d} {pn} — Lifetime Std Dev Cat {ci} ({cat_label})",
                        "group": "DSM",
                        "type": "DSM",
                        "hint": "years",
                        "step": "0.1",
                        "min": "0",
                        "max": "",
                    },
                    {
                        "name": f"P{pid:02d}_DSM_Lifetime_Shape_Cat_{ci}",
                        "label": f"P{pid:02d} {pn} — Weibull Shape Cat {ci} ({cat_label})",
                        "group": "DSM",
                        "type": "DSM",
                        "hint": "shape k>0",
                        "step": "0.01",
                        "min": "0",
                        "max": "",
                    },
                    {
                        "name": f"P{pid:02d}_DSM_Lifetime_Scale_Cat_{ci}",
                        "label": f"P{pid:02d} {pn} — Weibull Scale Cat {ci} ({cat_label})",
                        "group": "DSM",
                        "type": "DSM",
                        "hint": "scale λ>0",
                        "step": "0.1",
                        "min": "0",
                        "max": "",
                    },
                ]
            )

    # ── FOMP Parameters ────────────────────────────────────────────────────────
    # Names match the Excel MC_Parameter_ID convention so imported YAMLs resolve
    for proc in cfg.processes:
        if proc.logic != ProcessLogic.fomp:
            continue
        pid, pn = proc.id, proc.name
        params.extend(
            [
                {
                    "name": f"P{pid:02d}_Inflow_fraction_f (Labile pool)",
                    "label": f"P{pid:02d} {pn} — Inflow frac labile",
                    "group": "FOMP",
                    "type": "FOMP",
                    "hint": "fraction 0–1",
                    "step": "0.001",
                    "min": "0",
                    "max": "1",
                },
                {
                    "name": f"P{pid:02d}_decay_k1 (Labile pool)",
                    "label": f"P{pid:02d} {pn} — k labile",
                    "group": "FOMP",
                    "type": "FOMP",
                    "hint": "yr⁻¹",
                    "step": "0.001",
                    "min": "0",
                    "max": "",
                },
                {
                    "name": f"P{pid:02d}_Inflow_fraction_f (Recalcitrant pool)",
                    "label": f"P{pid:02d} {pn} — Inflow frac recalcitrant (no effect: engine uses 1 − labile)",
                    "group": "FOMP",
                    "type": "FOMP",
                    "hint": "fraction 0–1 (inert — vary the labile fraction instead)",
                    "step": "0.001",
                    "min": "0",
                    "max": "1",
                },
                {
                    "name": f"P{pid:02d}_decay_k2 (Recalcitrant pool)",
                    "label": f"P{pid:02d} {pn} — k recalcitrant",
                    "group": "FOMP",
                    "type": "FOMP",
                    "hint": "yr⁻¹",
                    "step": "0.0001",
                    "min": "0",
                    "max": "",
                },
            ]
        )

    # ── LFG site parameters: intentionally NOT offered ─────────────────────────
    # The engine cannot apply LFG parameter modifications yet: apply_scenario
    # has no LFG branch and the MC engine has no apply_lfg_parameter_updates(),
    # so entries like "P{id}_MCF" would be selectable but silently ignored.
    # Re-add an "LFG" group here once both engine paths exist (Finding B in
    # 260706_Report_SystemDefiner_ScenarioMC_ParameterCoverage.md).

    # ── FlowCap capacity caps ──────────────────────────────────────────────────
    # The cap series is registered in ParameterDict under cap_tc_id, so both
    # the scenario engine (generic ParameterDict branch) and MC (tc_updates
    # path) can modify it. The name is intentionally NOT typed "TC": it must
    # bypass TC normalization, which it does because it has no process-pair.
    for proc in cfg.processes:
        if proc.logic != ProcessLogic.flowcap or not proc.flowcap:
            continue
        cap_id = proc.flowcap.cap_tc_id or f"TC_Cap_{proc.id:02d}"
        params.append(
            {
                "name": cap_id,
                "label": f"P{proc.id:02d} {proc.name} — capacity cap",
                "group": "FlowCap",
                "type": "",
                "hint": f"{unit}/yr cap",
                "step": "any",
                "min": "0",
                "max": "",
            }
        )

    # ── Initial stocks ─────────────────────────────────────────────────────────
    # Applied by apply_scenario's "IS" branch. The MC engine has no IS support,
    # so these are hidden on the MC Parameters page via scenario_only.
    for entry in cfg.initial_stocks:
        pid = entry.process_id
        pn = proc_names.get(pid, f"P{pid}")
        params.append(
            {
                "name": f"P{pid:02d}_IS_material_quantity[UoM]",
                "label": f"P{pid:02d} {pn} — initial stock quantity",
                "group": "Initial Stock",
                "type": "IS",
                "hint": unit,
                "step": "any",
                "min": "0",
                "max": "",
                "scenario_only": True,
            }
        )
        for e_idx, elem in enumerate(cfg.model.elements):
            if e_idx == 0 or elem not in (entry.composition or {}):
                continue
            params.append(
                {
                    "name": f"P{pid:02d}_IS_E{e_idx + 1}_[%]({elem})",
                    "label": f"P{pid:02d} {pn} — initial stock {elem} fraction",
                    "group": "Initial Stock",
                    "type": "IS",
                    "hint": f"fraction 0–1  ({elem})",
                    "step": "0.001",
                    "min": "0",
                    "max": "1",
                    "scenario_only": True,
                }
            )

    return params


@app.get("/{name}/scenarios")
async def scenarios_list(request: Request, name: str):
    cfg = storage.load_case_study(name)
    return templates.TemplateResponse(
        request,
        "scenarios.html",
        _ctx(
            cfg=cfg, operations=_SCENARIO_OPERATIONS, param_types=_SCENARIO_PARAM_TYPES
        ),
    )


@app.post("/{name}/scenarios/new")
async def scenario_new(request: Request, name: str):
    form = await request.form()
    scenario_name = (form.get("scenario_name") or "").strip()
    if not scenario_name:
        raise HTTPException(400, "Scenario name is required")
    cfg = storage.load_case_study(name)
    if any(s.name == scenario_name for s in cfg.scenarios):
        raise HTTPException(400, f"Scenario '{scenario_name}' already exists")
    cfg.scenarios.append(ScenarioDefinition(name=scenario_name))
    storage.save_case_study(cfg)
    return RedirectResponse(f"/{name}/scenarios/{scenario_name}", status_code=303)


@app.get("/{name}/scenarios/{sname}")
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


@app.post("/{name}/scenarios/{sname}")
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


@app.post("/{name}/scenarios/{sname}/delete")
async def scenario_delete(request: Request, name: str, sname: str):
    cfg = storage.load_case_study(name)
    cfg.scenarios = [s for s in cfg.scenarios if s.name != sname]
    storage.save_case_study(cfg)
    return RedirectResponse(f"/{name}/scenarios", status_code=303)


# ══════════════════════════════════════════════════════════════════════════════
# ZOTERO INTEGRATION
# ══════════════════════════════════════════════════════════════════════════════

_ZOTERO_RPC = "http://localhost:23119/better-bibtex/json-rpc"


def _zotero_search(query: str) -> list[dict]:
    """Query local Better BibTeX JSON-RPC. Returns [] when Zotero is not running."""
    try:
        import httpx

        r = httpx.post(
            _ZOTERO_RPC,
            json={
                "jsonrpc": "2.0",
                "method": "item.search",
                "params": {"terms": query},
                "id": 1,
            },
            timeout=3.0,
        )
        data = r.json()
        return data.get("result", []) or []
    except Exception:
        return []


def _fmt_authors(item: dict) -> str:
    authors = item.get("author", [])
    if not authors:
        return ""
    if len(authors) == 1:
        return authors[0].get("family", "")
    if len(authors) == 2:
        return f"{authors[0].get('family', '')} & {authors[1].get('family', '')}"
    return f"{authors[0].get('family', '')} et al."


def _fmt_year(item: dict) -> str:
    issued = item.get("issued", {})
    parts = issued.get("date-parts", [[]])[0]
    return str(parts[0]) if parts else ""


def _item_to_ref(item: dict, note: str = "") -> "ReferenceEntry":
    return ReferenceEntry(
        cite_key=item.get("citekey") or item.get("citation-key", ""),
        title=item.get("title", ""),
        authors=_fmt_authors(item),
        year=_fmt_year(item),
        item_type=item.get("type", ""),
        doi=item.get("DOI", ""),
        note=note,
    )


@app.get("/api/zotero/search")
async def zotero_search(q: str = ""):
    if not q.strip():
        return []
    items = _zotero_search(q.strip())
    return [
        {
            "cite_key": it.get("citekey") or it.get("citation-key", ""),
            "title": it.get("title", ""),
            "authors": _fmt_authors(it),
            "year": _fmt_year(it),
            "item_type": it.get("type", ""),
            "doi": it.get("DOI", ""),
        }
        for it in items
        if it.get("citekey") or it.get("citation-key")
    ]


@app.get("/{name}/references")
async def references_get(request: Request, name: str, saved: bool = False):
    if not storage.case_study_exists(name):
        raise HTTPException(404)
    cfg = storage.load_case_study(name)
    return templates.TemplateResponse(
        request,
        "references.html",
        _ctx(cfg=cfg, saved=saved),
    )


@app.post("/{name}/references/add")
async def references_add(request: Request, name: str):
    form = await request.form()
    cfg = storage.load_case_study(name)
    cite_key = (form.get("cite_key") or "").strip()
    if not cite_key:
        raise HTTPException(400, "cite_key is required")
    if any(r.cite_key == cite_key for r in cfg.references):
        return RedirectResponse(f"/{name}/references?saved=1", status_code=303)
    cfg.references.append(
        ReferenceEntry(
            cite_key=cite_key,
            title=(form.get("title") or "").strip(),
            authors=(form.get("authors") or "").strip(),
            year=(form.get("year") or "").strip(),
            item_type=(form.get("item_type") or "").strip(),
            doi=(form.get("doi") or "").strip(),
            note=(form.get("note") or "").strip(),
        )
    )
    storage.save_case_study(cfg)
    return RedirectResponse(f"/{name}/references?saved=1", status_code=303)


@app.post("/{name}/references/note")
async def references_note(request: Request, name: str):
    """Update the note on an existing reference."""
    form = await request.form()
    cfg = storage.load_case_study(name)
    cite_key = (form.get("cite_key") or "").strip()
    note = (form.get("note") or "").strip()
    for ref in cfg.references:
        if ref.cite_key == cite_key:
            ref.note = note
            break
    storage.save_case_study(cfg)
    return RedirectResponse(f"/{name}/references?saved=1", status_code=303)


@app.post("/{name}/references/delete")
async def references_delete(request: Request, name: str):
    form = await request.form()
    cfg = storage.load_case_study(name)
    cite_key = (form.get("cite_key") or "").strip()
    cfg.references = [r for r in cfg.references if r.cite_key != cite_key]
    storage.save_case_study(cfg)
    return RedirectResponse(f"/{name}/references", status_code=303)


# ══════════════════════════════════════════════════════════════════════════════
# EXPORT / IMPORT
# ══════════════════════════════════════════════════════════════════════════════


@app.get("/{name}/export")
async def export_yaml(name: str):
    from systemdefiner.storage import _config_path

    path = _config_path(name)
    return FileResponse(
        path, media_type="application/x-yaml", filename=f"{name}_config.yaml"
    )


# ── Model diagram (user-uploaded image shown in the page header) ────────────
@app.get("/{name}/diagram")
async def get_diagram(name: str):
    path = storage.diagram_path(name)
    if not path:
        raise HTTPException(404, "No diagram uploaded")
    return FileResponse(path)


@app.post("/{name}/diagram")
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


@app.post("/{name}/diagram/delete")
async def remove_diagram(name: str):
    storage.delete_diagram(name)
    return RedirectResponse(f"/{name}", status_code=303)


@app.get("/{name}/import")
async def import_form(request: Request, name: str):
    cfg = storage.load_case_study(name)
    return templates.TemplateResponse(request, "import.html", _ctx(cfg=cfg))


@app.post("/{name}/import")
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


# ══════════════════════════════════════════════════════════════════════════════
# ELEMENT HIERARCHY
# ══════════════════════════════════════════════════════════════════════════════


def _rules_to_paths(rules: list) -> list[list[str]]:
    """Convert ElementHierarchyRule list to path-rows for the matrix editor."""
    parent_to_children: dict[str, list] = {}
    child_to_parent: dict[str, str] = {}
    for rule in rules:
        parent_to_children[rule.parent] = list(rule.children)
        for child in rule.children:
            child_to_parent[child] = rule.parent

    all_elems: set[str] = set(parent_to_children.keys())
    for rule in rules:
        all_elems.update(rule.children)

    leaves = [e for e in all_elems if e not in parent_to_children]
    if not leaves and all_elems:
        leaves = list(all_elems)

    def get_path(elem: str) -> list[str]:
        path: list[str] = []
        cur: str | None = elem
        while cur:
            path.insert(0, cur)
            cur = child_to_parent.get(cur)
        return path

    # Pad all paths to the deepest path present (hierarchy depth is not capped).
    raw_paths = [get_path(leaf) for leaf in sorted(leaves)]
    depth = max((len(p) for p in raw_paths), default=0)
    paths = [p + [""] * (depth - len(p)) for p in raw_paths]
    paths.sort()
    return paths


@app.get("/{name}/elements")
async def elements_form(request: Request, name: str):
    if not storage.case_study_exists(name):
        raise HTTPException(404)
    cfg = storage.load_case_study(name)
    import json as _json

    paths_json = _json.dumps(_rules_to_paths(cfg.element_hierarchy))
    elements_json = _json.dumps(cfg.model.elements)
    return templates.TemplateResponse(
        request,
        "elements.html",
        _ctx(cfg=cfg, paths_json=paths_json, elements_json=elements_json),
    )


@app.post("/{name}/elements")
async def elements_save(request: Request, name: str):
    from collections import defaultdict as _defaultdict

    form = await request.form()
    cfg = storage.load_case_study(name)

    # ── Element list ─────────────────────────────────────────────────────────
    elements: list[str] = []
    idx = 0
    while True:
        key = f"element_{idx}"
        if key not in form:
            break
        val = (form[key] or "").strip()
        if val:
            elements.append(val)
        idx += 1
        if idx > 200:
            break
    if elements:
        # The first element is the conserved total-mass balance / hierarchy root;
        # the engine requires it to be named "material". Enforce it defensively
        # (the editor locks the field, but guard against import/manual edits).
        if elements[0] != "material":
            elements = ["material"] + [e for e in elements if e != "material"]
        cfg.model.elements = elements

    # ── Level names ──────────────────────────────────────────────────────────
    # Hierarchy depth is user-extensible: collect however many level_name_{i}
    # fields the editor submitted (tolerant of gaps), not a fixed 4.
    level_indices = sorted(
        {
            int(m.group(1))
            for key in form.keys()
            if (m := re.fullmatch(r"level_name_(\d+)", key))
        }
    )
    level_names = [(form.get(f"level_name_{i}") or "").strip() for i in level_indices]
    level_names = [n for n in level_names if n]
    if level_names:
        cfg.model.hierarchy_level_names = level_names
    n_levels = len(cfg.model.hierarchy_level_names)

    # ── Path rows → hierarchy rules ──────────────────────────────────────────
    # Collect row indices tolerantly: the client may leave gaps in the
    # path_{i}_* numbering (a removal followed by an add), so never stop at the
    # first missing index — that would silently truncate every row past the gap.
    parent_to_children: dict[str, set] = _defaultdict(set)
    path_indices = sorted(
        {
            int(m.group(1))
            for key in form.keys()
            if (m := re.fullmatch(r"path_(\d+)_l1", key))
        }
    )
    for pidx in path_indices:
        # Read as many level columns as the hierarchy has (l1..l{n_levels}).
        cells = [
            (form.get(f"path_{pidx}_l{level}") or "").strip()
            for level in range(1, n_levels + 1)
        ]
        # Collect consecutive non-empty pairs as parent→child
        for i in range(len(cells) - 1):
            if cells[i] and cells[i + 1]:
                parent_to_children[cells[i]].add(cells[i + 1])

    cfg.element_hierarchy = [
        ElementHierarchyRule(parent=p, children=sorted(ch))
        for p, ch in parent_to_children.items()
    ]

    storage.save_case_study(cfg)
    return RedirectResponse(f"/{name}/elements", status_code=303)


# Keep /hierarchy as alias for backwards compatibility
@app.get("/{name}/hierarchy")
async def hierarchy_redirect(name: str):
    return RedirectResponse(f"/{name}/elements", status_code=301)


# ══════════════════════════════════════════════════════════════════════════════
# MC PARAMETERS
# ══════════════════════════════════════════════════════════════════════════════

_MC_DISTRIBUTIONS = ["normal", "lognormal", "uniform", "triangular"]
_MC_OPERATIONS = ["set", "multiply", "add"]

# Fields active for each distribution type
_DIST_FIELDS = {
    "normal": {"mean", "std", "min", "max"},
    "lognormal": {"mean", "std", "min", "max"},
    "uniform": {"min", "max"},
    "triangular": {"min", "mode", "max"},
}


@app.get("/{name}/mc_parameters")
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


@app.post("/{name}/mc_parameters")
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


# ══════════════════════════════════════════════════════════════════════════════
# FLOW COMPOSITIONS
# ══════════════════════════════════════════════════════════════════════════════


@app.get("/{name}/compositions")
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


@app.post("/{name}/compositions")
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


@app.get("/{name}/bom/{pid}")
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


@app.post("/{name}/bom/{pid}")
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


@app.get("/{name}/initial_stock/{pid}")
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


@app.post("/{name}/initial_stock/{pid}")
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


# ── Flow Data (input time series) ──────────────────────────────────────────


def _input_flows(cfg: CaseStudyConfig):
    """Return flows whose source process has logic='Input'."""
    input_pids = {p.id for p in cfg.processes if p.logic == ProcessLogic.input}
    return [f for f in cfg.flows if f.from_process in input_pids]


@app.get("/{name}/flow_data")
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


@app.post("/{name}/flow_data")
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
