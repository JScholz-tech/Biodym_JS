"""Model-health checks shown on the case-study overview page.

Moved verbatim from ``main.py``.
"""
from __future__ import annotations

from systemdefiner.consistency import check_config_consistency
from systemdefiner.models.config_schema import (
    ProcessLogic,
    StockConfig,
    TCConfig,
)

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

    # Cross-reference invariants (dangling scenario/MC names, stale element
    # keys, TC ownership, ID drift, …) — shared with the test suite.
    issues.extend(check_config_consistency(cfg))

    return issues
