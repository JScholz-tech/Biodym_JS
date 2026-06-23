# -*- coding: utf-8 -*-
"""
FlowCap Process Logic for the BioDYM Engine.

A FlowCap process routes inflow through a capacity constraint:
  - If total inflow ≤ cap  → 100% goes to Capped_Output, 0% to Overflow
  - If total inflow  > cap → exactly `cap` Mg goes to Capped_Output,
                             the remainder goes to Overflow

The cap is defined as a year/value time series directly in the sheet
(Year column + Flow column, one row per data point per process).
Values between defined years are linearly interpolated; beyond the last
year the final value is held constant.

Mass balance is always maintained: Capped_Output + Overflow = total_inflow
at every element level.  Element proportions (WC, DM, TC …) are preserved
automatically because the split ratio is derived from the material column
and applied uniformly to all elements.

Excel configuration: sheet '3_4_Definition_FlowCap'
Multi-row layout — one block per process:

  Capped_Output rows (one per data point):
    Process_ID        int  — ID in 2_1_Definition_Processes
    Output_flow_type  str  — 'Capped_Output'
    Flow_ID           str  — FlowDict key (e.g. 'F_02_04')
    Year              int  — calendar year of this data point
    Flow              float — cap value in Mg/yr

  Overflow row (single):
    Process_ID        int  — same process
    Output_flow_type  str  — 'Overflow'
    Flow_ID           str  — FlowDict key for the overflow flow

Example:
    02 | Capped_Output | F_02_04 | 2025 | 2500
    02 | Capped_Output | F_02_04 | 2030 | 3000
    02 | Overflow      | F_02_07 |      |

In 2_1_Definition_Processes: Process_Logic = 'FlowCap',
                              Stock_Configuration = 'No_Stock'
"""

import numpy as np
import pandas as pd


class _CapParam:
    """Minimal parameter-like object stored in ParameterDict for FlowCap caps.

    apply_scenario only needs a .Values numpy array, so no full ODYM Parameter
    import is required here.  No __slots__ — deepcopy must work correctly when
    the scenario engine copies mfa_system_configured.
    """

    def __init__(self, name: str, values: np.ndarray):
        self.Name = name
        self.Values = values


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
            "capped_flow_id":   str,          # FlowDict key for capped output
            "overflow_flow_id": str | None,   # FlowDict key for overflow
            "cap_series":       {int: float}, # {year: cap_Mg/yr}
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

    df.columns = (
        df.columns.str.strip()
    )  # remove leading/trailing whitespace from header cells
    print(f"    Columns found: {list(df.columns)}")

    # Flow_ID is the only truly required column
    if "Flow_ID" not in df.columns:
        print(f"    ERROR: Missing required column 'Flow_ID' in '{sheet_name}'.")
        return {}

    has_process_id = "Process_ID" in df.columns
    has_flow_type = "Output_flow_type" in df.columns

    if not has_flow_type:
        print(
            "    INFO: 'Output_flow_type' column missing — all rows with cap values treated as 'Capped_Output'."
        )
    if not has_process_id:
        print(
            "    INFO: 'Process_ID' column missing — will infer from Flow_ID (first process index)."
        )

    # Infer Process_ID from Flow_ID when the column is absent.
    # F_02_04 → process 2 (the originating process of the capped output flow).
    if has_process_id:
        df = df.dropna(subset=["Process_ID", "Flow_ID"])
        df["Process_ID"] = df["Process_ID"].astype(int)
    else:
        df = df.dropna(subset=["Flow_ID"])

        def _pid_from_flow(fid):
            try:
                return int(str(fid).split("_")[1])
            except (IndexError, ValueError):
                return None

        df["Process_ID"] = df["Flow_ID"].apply(_pid_from_flow)
        df = df.dropna(subset=["Process_ID"])
        df["Process_ID"] = df["Process_ID"].astype(int)

    # Add a synthetic Output_flow_type when absent
    if not has_flow_type:
        df["Output_flow_type"] = "Capped_Output"

    # Accept "Flow" or legacy "Cap_Value[UoM]" as the cap value column
    cap_col = next((c for c in ["Flow", "Cap_Value[UoM]"] if c in df.columns), None)
    year_col = "Year" if "Year" in df.columns else None
    cap_tc_col = "Cap_TC_ID" if "Cap_TC_ID" in df.columns else None

    flow_cap_params = {}

    for process_id, group in df.groupby("Process_ID"):
        config = {
            "capped_flow_id": None,
            "overflow_flow_id": None,
            "cap_series": {},
            "cap_tc_id": None,  # optional: ParameterDict key for scenario switching
        }

        capped_rows = group[group["Output_flow_type"].str.strip() == "Capped_Output"]
        overflow_rows = group[group["Output_flow_type"].str.strip() == "Overflow"]

        # --- Capped_Output rows ---
        if not capped_rows.empty:
            config["capped_flow_id"] = str(capped_rows.iloc[0]["Flow_ID"]).strip()

            # Read Cap_TC_ID from first Capped_Output row if column exists
            if cap_tc_col:
                raw_tc = capped_rows.iloc[0].get(cap_tc_col)
                if (
                    raw_tc
                    and isinstance(raw_tc, str)
                    and raw_tc.strip() not in ("", "N.A.", "N/A")
                ):
                    config["cap_tc_id"] = raw_tc.strip()

            for _, row in capped_rows.iterrows():
                cap_val = row.get(cap_col) if cap_col else None
                year_val = row.get(year_col) if year_col else None

                if cap_val is None or (isinstance(cap_val, float) and pd.isna(cap_val)):
                    continue
                try:
                    cap_f = float(str(cap_val).replace(",", "."))
                except (ValueError, TypeError):
                    continue

                if year_val is not None and not (
                    isinstance(year_val, float) and pd.isna(year_val)
                ):
                    try:
                        config["cap_series"][int(year_val)] = cap_f
                    except (ValueError, TypeError):
                        config["cap_series"][0] = cap_f
                else:
                    config["cap_series"][0] = cap_f  # static — key 0 means "all years"

        # --- Overflow row ---
        if not overflow_rows.empty:
            config["overflow_flow_id"] = str(overflow_rows.iloc[0]["Flow_ID"]).strip()

        # --- Unknown row types ---
        known = {"Capped_Output", "Overflow"}
        for _, row in group[
            ~group["Output_flow_type"].str.strip().isin(known)
        ].iterrows():
            print(
                f"    WARNING: Process {process_id}: unknown Output_flow_type "
                f"'{row['Output_flow_type']}' — expected 'Capped_Output' or 'Overflow'."
            )

        # --- Validation ---
        if config["capped_flow_id"] is None:
            print(
                f"    WARNING: Process {process_id}: no 'Capped_Output' row — skipping."
            )
            continue
        if config["overflow_flow_id"] is None:
            print(
                f"    WARNING: Process {process_id}: no 'Overflow' row — "
                f"excess mass has nowhere to go and mass balance will be violated."
            )
        if not config["cap_series"]:
            print(
                f"    WARNING: Process {process_id}: no cap values found "
                f"(add Year and Flow columns to the Capped_Output rows)."
            )

        flow_cap_params[process_id] = config
        n_pts = len(config["cap_series"])
        tc_info = f", cap_tc_id={config['cap_tc_id']}" if config["cap_tc_id"] else ""
        print(
            f"    Loaded FlowCap for Process {process_id}: "
            f"{n_pts} cap data point(s), "
            f"capped={config['capped_flow_id']}, "
            f"overflow={config['overflow_flow_id']}{tc_info}"
        )

    print(f"--> FlowCap: loaded {len(flow_cap_params)} process(es).")
    return flow_cap_params


# ---------------------------------------------------------------------------
# ParameterDict registration — call once after system setup, before solver
# ---------------------------------------------------------------------------


def register_cap_parameters(mfa_system, flow_cap_params) -> None:
    """Register FlowCap cap time series in mfa_system.ParameterDict.

    For every process that has a ``cap_tc_id`` set, this creates a
    ``_CapParam`` entry in ParameterDict keyed by the cap_tc_id string
    (e.g. ``"TC_Cap_02"``).  The scenario engine's ``apply_scenario``
    function then finds and modifies it like any other dynamic parameter.

    Call this once after ``system_setup.define_flows_and_parameters`` and
    before the solver loop — same pattern as ``load_tc_parameters`` /
    ``ParameterDict.update()``.

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        The configured system whose ParameterDict will be updated in place.
    flow_cap_params : dict
        As returned by ``load_flow_cap_parameters()``.
    """
    time_items = mfa_system.IndexTable.Classification["Time"].Items
    time_vector = np.array(time_items, dtype=float)
    num_years = len(time_vector)

    for process_id, params in flow_cap_params.items():
        cap_tc_id = params.get("cap_tc_id")
        if not cap_tc_id:
            continue
        if cap_tc_id in mfa_system.ParameterDict:
            continue  # already registered (e.g. re-run without kernel restart)
        cap_array = _resolve_cap(params["cap_series"], time_vector, num_years)
        mfa_system.ParameterDict[cap_tc_id] = _CapParam(cap_tc_id, cap_array)
        print(
            f"  Registered FlowCap cap '{cap_tc_id}' in ParameterDict "
            f"(Process {process_id}, {num_years} years)."
        )


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

    time_items = mfa_system.IndexTable.Classification["Time"].Items
    time_vector = np.array(time_items, dtype=float)

    for process_id in flow_cap_processes:
        params = flow_cap_params[process_id]

        inflows = [
            f.Values for f in mfa_system.FlowDict.values() if f.P_End == process_id
        ]
        if not inflows:
            continue

        num_years, num_elements = inflows[0].shape
        total_inflow = sum(inflows)  # (num_years, num_elements)

        # Prefer ParameterDict (allows scenario engine to override cap values)
        cap_tc_id = params.get("cap_tc_id")
        if cap_tc_id and cap_tc_id in mfa_system.ParameterDict:
            raw = mfa_system.ParameterDict[cap_tc_id].Values
            cap_values = np.asarray(raw, dtype=float).ravel()[:num_years]
        else:
            cap_values = _resolve_cap(params["cap_series"], time_vector, num_years)

        # ratio[t] = min(1, cap[t] / inflow_material[t])
        # When inflow == 0 the ratio stays 1.0 (nothing to route).
        material = total_inflow[:, 0]
        safe_mat = np.where(material > 0, material, 1.0)
        ratio = np.where(material > 0, np.minimum(1.0, cap_values / safe_mat), 1.0)

        primary = total_inflow * ratio[:, None]
        overflow = total_inflow - primary

        # --- Capped_Output ---
        capped_id = params["capped_flow_id"]
        if capped_id and capped_id in mfa_system.FlowDict:
            old = mfa_system.FlowDict[capped_id].Values.copy()
            mfa_system.FlowDict[capped_id].Values[:, :] = primary
            if not np.allclose(old, primary):
                something_changed = True
        else:
            print(
                f"  WARNING: FlowCap Process {process_id}: "
                f"capped flow '{capped_id}' not found in FlowDict."
            )

        # --- Overflow ---
        overflow_id = params.get("overflow_flow_id")
        if overflow_id and overflow_id in mfa_system.FlowDict:
            old = mfa_system.FlowDict[overflow_id].Values.copy()
            mfa_system.FlowDict[overflow_id].Values[:, :] = overflow
            if not np.allclose(old, overflow):
                something_changed = True
        elif overflow_id:
            print(
                f"  WARNING: FlowCap Process {process_id}: "
                f"overflow flow '{overflow_id}' not found in FlowDict."
            )

    return something_changed


def _resolve_cap(cap_series, time_vector, num_years):
    """Convert cap_series {year: Mg} to a (num_years,) float array.

    If the series key is 0 (static fallback), the single value is broadcast.
    Otherwise values are linearly interpolated over the time vector; years
    outside the defined range use the nearest endpoint (no extrapolation).
    """
    if not cap_series:
        return np.zeros(num_years)

    keys = sorted(cap_series.keys())

    # Static fallback: single key = 0 means "apply to all years"
    if keys == [0]:
        return np.full(num_years, cap_series[0])

    years = np.array(keys, dtype=float)
    values = np.array([cap_series[k] for k in keys], dtype=float)

    # Linear interpolation, clamp to endpoints outside range
    return np.interp(
        time_vector[:num_years], years, values, left=values[0], right=values[-1]
    )
