# -*- coding: utf-8 -*-
"""
FlowCap Process Logic for the BioDYM Engine.

A FlowCap process routes inflow through a capacity constraint:
  - If total inflow ≤ cap  → 100% goes to Capped_Output, 0% to Overflow
  - If total inflow  > cap → exactly `cap` Mg goes to Capped_Output,
                             the remainder goes to Overflow

The cap is defined in the same mass unit as all other flows (e.g. Mg/yr)
and can be time-varying via a ParameterDict TC entry (Cap_TC_ID) or a
static inline value (Cap_Value[UoM]).

Mass balance is always maintained: Capped_Output + Overflow = total_inflow
at every element level.  Element proportions (WC, DM, TC …) are preserved
automatically because the split ratio is derived from the material column
and applied uniformly to all elements.

Excel configuration: sheet '3_4_Definition_FlowCap'
Multi-row layout — one row per output flow per process:

    Process_ID        int   — ID in 2_1_Definition_Processes
    Output_flow_type  str   — 'Capped_Output' or 'Overflow'
    Flow_ID           str   — matches FlowDict key (e.g. 'F_05_06')
    Cap_TC_ID         str   — ParameterDict key for the annual cap (Mg/yr).
                              Only required on the 'Capped_Output' row.
    Cap_Value[UoM]    float — static fallback cap when Cap_TC_ID is absent.

Both output flow types are required; omitting Overflow breaks mass balance.
In 2_1_Definition_Processes: Process_Logic = 'FlowCap',
                              Stock_Configuration = 'No_Stock'
"""

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Public loader — called by data_loader.load_flow_cap_parameters()
# ---------------------------------------------------------------------------

def load_flow_cap_parameters(excel_data, debug_mode=False):
    """Load FlowCap configurations from sheet '3_4_Definition_FlowCap'.

    Parameters
    ----------
    excel_data : dict
        DataFrames keyed by sheet name.
    debug_mode : bool, optional

    Returns
    -------
    dict
        Keys are process IDs (int). Values are config dicts:
        {
            "capped_flow_id":   str,        # FlowDict key for capped output
            "overflow_flow_id": str | None, # FlowDict key for overflow
            "cap_tc_id":        str | None, # ParameterDict key (time-varying)
            "cap_value":        float,      # static fallback cap (Mg/yr)
        }
    """
    sheet_name = "3_4_Definition_FlowCap"
    print(f"--> Loading FlowCap parameters from sheet '{sheet_name}'...")

    if sheet_name not in excel_data:
        print(f"    INFO: Sheet '{sheet_name}' not found — no FlowCap processes.")
        return {}

    df = excel_data[sheet_name].copy()
    if df.empty:
        print(f"    INFO: Sheet '{sheet_name}' is empty.")
        return {}

    required_cols = ["Process_ID", "Output_flow_type", "Flow_ID"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        print(f"    ERROR: Missing required columns in '{sheet_name}': {missing}")
        return {}

    df = df.dropna(subset=["Process_ID", "Output_flow_type", "Flow_ID"])
    df["Process_ID"] = df["Process_ID"].astype(int)

    flow_cap_params = {}

    for process_id, group in df.groupby("Process_ID"):
        config = {
            "capped_flow_id":   None,
            "overflow_flow_id": None,
            "cap_tc_id":        None,
            "cap_value":        0.0,
        }

        for _, row in group.iterrows():
            flow_type = str(row["Output_flow_type"]).strip()
            flow_id   = str(row["Flow_ID"]).strip()

            if flow_type == "Capped_Output":
                config["capped_flow_id"] = flow_id

                cap_tc = row.get("Cap_TC_ID")
                if cap_tc is not None and not (isinstance(cap_tc, float) and pd.isna(cap_tc)):
                    config["cap_tc_id"] = str(cap_tc).strip()

                cap_val = row.get("Cap_Value[UoM]")
                if cap_val is not None and not (isinstance(cap_val, float) and pd.isna(cap_val)):
                    try:
                        config["cap_value"] = float(cap_val)
                    except (ValueError, TypeError):
                        pass

            elif flow_type == "Overflow":
                config["overflow_flow_id"] = flow_id

            else:
                print(f"    WARNING: Process {process_id}: unknown Output_flow_type "
                      f"'{flow_type}' — expected 'Capped_Output' or 'Overflow'.")

        if config["capped_flow_id"] is None:
            print(f"    WARNING: Process {process_id}: no 'Capped_Output' row — skipping.")
            continue
        if config["overflow_flow_id"] is None:
            print(f"    WARNING: Process {process_id}: no 'Overflow' row defined — "
                  f"excess mass has nowhere to go and mass balance will be violated.")
        if config["cap_tc_id"] is None and config["cap_value"] == 0.0:
            print(f"    WARNING: Process {process_id}: no Cap_TC_ID or Cap_Value — "
                  f"cap defaults to 0 Mg/yr (all inflow will overflow).")

        flow_cap_params[process_id] = config
        cap_src = config["cap_tc_id"] or f"{config['cap_value']:.1f} Mg/yr (static)"
        print(f"    Loaded FlowCap for Process {process_id}: "
              f"cap={cap_src}, "
              f"capped→{config['capped_flow_id']}, "
              f"overflow→{config['overflow_flow_id']}")

    print(f"--> FlowCap: loaded {len(flow_cap_params)} process(es).")
    return flow_cap_params


# ---------------------------------------------------------------------------
# Calculation engine
# ---------------------------------------------------------------------------

def calculate_flow_cap(mfa_system, flow_cap_processes, flow_cap_params):
    """Apply capacity-limited routing to all FlowCap processes.

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        Modified in place.
    flow_cap_processes : set of int
        Process IDs active as FlowCap (already filtered by process_logic_map).
    flow_cap_params : dict
        As returned by load_flow_cap_parameters().

    Returns
    -------
    bool
        True if any flow value changed from the previous iteration.
    """
    something_changed = False

    for process_id in flow_cap_processes:
        params = flow_cap_params[process_id]

        inflows = [f.Values for f in mfa_system.FlowDict.values()
                   if f.P_End == process_id]
        if not inflows:
            continue

        num_years, num_elements = inflows[0].shape
        total_inflow = sum(inflows)   # (num_years, num_elements)

        cap_values = _resolve_cap(mfa_system, params, num_years)

        # ratio[t] = min(1, cap / inflow_material[t])
        # When inflow == 0 the ratio stays 1.0 (nothing to split).
        material   = total_inflow[:, 0]
        safe_mat   = np.where(material > 0, material, 1.0)
        ratio      = np.where(material > 0, np.minimum(1.0, cap_values / safe_mat), 1.0)

        primary  = total_inflow * ratio[:, None]
        overflow = total_inflow - primary

        # --- Capped_Output flow ---
        capped_id = params["capped_flow_id"]
        if capped_id and capped_id in mfa_system.FlowDict:
            old = mfa_system.FlowDict[capped_id].Values.copy()
            mfa_system.FlowDict[capped_id].Values[:, :] = primary
            if not np.allclose(old, primary):
                something_changed = True
        else:
            print(f"  WARNING: FlowCap Process {process_id}: "
                  f"capped flow '{capped_id}' not found in FlowDict.")

        # --- Overflow flow ---
        overflow_id = params.get("overflow_flow_id")
        if overflow_id and overflow_id in mfa_system.FlowDict:
            old = mfa_system.FlowDict[overflow_id].Values.copy()
            mfa_system.FlowDict[overflow_id].Values[:, :] = overflow
            if not np.allclose(old, overflow):
                something_changed = True
        elif overflow_id:
            print(f"  WARNING: FlowCap Process {process_id}: "
                  f"overflow flow '{overflow_id}' not found in FlowDict.")

    return something_changed


def _resolve_cap(mfa_system, params, num_years):
    """Return a (num_years,) float array of cap values.

    Priority order: ParameterDict[cap_tc_id]  >  params["cap_value"] (static).
    If the TC array is shorter than num_years, the last value is repeated.
    """
    cap_tc_id = params.get("cap_tc_id")
    if cap_tc_id and cap_tc_id in mfa_system.ParameterDict:
        raw = np.asarray(mfa_system.ParameterDict[cap_tc_id].Values, dtype=float).reshape(-1)
        if len(raw) == 1:
            return np.full(num_years, raw[0])
        if len(raw) >= num_years:
            return raw[:num_years]
        padded = np.full(num_years, raw[-1])
        padded[:len(raw)] = raw
        return padded

    return np.full(num_years, float(params.get("cap_value", 0.0)))
