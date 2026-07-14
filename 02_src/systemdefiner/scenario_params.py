"""Catalog of scenario/MC-selectable parameters + editor constants.

Moved verbatim from ``main.py``.
"""
from __future__ import annotations

from systemdefiner.models.config_schema import ProcessLogic

_SCENARIO_OPERATIONS = ["replace", "multiply", "add"]
_SCENARIO_PARAM_TYPES = ["", "Flow", "TC", "DSM", "FOMP", "IS"]

_MC_DISTRIBUTIONS = ["normal", "lognormal", "uniform", "triangular"]
_MC_OPERATIONS = ["set", "multiply", "add"]

# Fields active for each distribution type
_DIST_FIELDS = {
    "normal": {"mean", "std", "min", "max"},
    "lognormal": {"mean", "std", "min", "max"},
    "uniform": {"min", "max"},
    "triangular": {"min", "mode", "max"},
}


def _build_scenario_params(cfg) -> list[dict]:
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
    _tc_lookup: dict[tuple, object] = {}
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
