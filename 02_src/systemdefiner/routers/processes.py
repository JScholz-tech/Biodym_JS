"""Process routes: list, create, edit, delete, renumber.

Moved verbatim from ``main.py``.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from systemdefiner import storage
from systemdefiner.cascades import _compact_process_ids, _delete_process_cascade
from systemdefiner.deps import _ctx, templates
from systemdefiner.forms import (
    _parse_dsm,
    _parse_dsm_component,
    _parse_flowcap,
    _parse_fomp,
    _parse_lfg,
)
from systemdefiner.models.config_schema import (
    Process,
    ProcessLogic,
    StockConfig,
    TCConfig,
)

router = APIRouter()


@router.get("/{name}/processes")
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


@router.post("/{name}/processes/new")
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


@router.get("/{name}/processes/{pid}/edit")
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


@router.post("/{name}/processes/{pid}/edit")
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


@router.post("/{name}/processes/{pid}/delete")
async def process_delete(name: str, pid: int):
    cfg = storage.load_case_study(name)
    _delete_process_cascade(cfg, pid)
    storage.save_case_study(cfg)
    return RedirectResponse(f"/{name}/processes", status_code=303)


@router.post("/{name}/processes/renumber")
async def processes_renumber(name: str):
    cfg = storage.load_case_study(name)
    _compact_process_ids(cfg)
    storage.save_case_study(cfg)
    return RedirectResponse(f"/{name}/processes", status_code=303)
