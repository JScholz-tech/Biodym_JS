# -*- coding: utf-8 -*-
"""
Monte Carlo Control Board.

Provides functions to display MC parameter overviews, validation reports,
and post-run summary statistics in the Jupyter notebook.
"""

import pandas as pd
import numpy as np

from engine.mc_simulation import validate_mc_parameters


def build_parameter_overview_df(mc_params_df):
    """Build a display-ready parameter overview from the uncertainty sheet.

    Parameters
    ----------
    mc_params_df : pd.DataFrame
        Raw DataFrame from the 4_1_Uncertainty_Parameters Excel sheet.

    Returns
    -------
    pd.DataFrame
        Formatted overview with columns: Parameter, Category, Distribution,
        Min, Max, Mean, StdDev, Mode.
    """
    df = mc_params_df.dropna(subset=["Parameter_Name"]).copy()

    def classify(name):
        if name.startswith("TC_"):
            return "Transfer Coefficient"
        elif "_DSM_" in name:
            return "DSM Parameter"
        elif name.startswith("P") and (
            "_decay_" in name or "_Inflow_fraction_f" in name
        ):
            return "FOMP Parameter"
        return "Other"

    df["Category"] = df["Parameter_Name"].apply(classify)
    df = df.rename(
        columns={"Parameter_Name": "Parameter", "Distribution_Type": "Distribution"}
    )
    df["Distribution"] = df["Distribution"].str.capitalize()

    display_cols = ["Min", "Max", "Mean", "StdDev", "Mode"]
    for col in display_cols:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: f"{x:.4f}" if pd.notna(x) else "--")

    cols = ["Parameter", "Category", "Distribution"]
    cols += [c for c in display_cols if c in df.columns]
    return df[cols].reset_index(drop=True)


def generate_validation_report(
    uncertainty_params, mfa_system, dsm_params, fomp_params, mc_params_df
):
    """Generate a structured MC validation report.

    Parameters
    ----------
    uncertainty_params : dict
        Dictionary of uncertainty definitions from load_uncertainty_definitions().
    mfa_system : odym.MFAsystem
        The configured MFA system.
    dsm_params : dict
        DSM process parameters.
    fomp_params : dict
        FOMP process parameters.
    mc_params_df : pd.DataFrame
        Raw DataFrame from the 4_1_Uncertainty_Parameters Excel sheet.

    Returns
    -------
    dict
        Keys: "mapping_df" (pd.DataFrame), "warnings" (list[str]),
        "n_params" (int).
    """
    process_name_map = {p.ID: p.Name for p in mfa_system.ProcessList}

    # Build parameter-to-model mapping
    rows = []
    for name in uncertainty_params:
        target = "Unknown"
        if name.startswith("TC_"):
            try:
                parts = name.split("_")
                if parts[1].startswith("E") and len(parts) >= 4:
                    element_id = parts[1]
                    p_start, p_end = int(parts[2]), int(parts[3])
                    start_name = process_name_map.get(p_start, f"ID {p_start}")
                    end_name = process_name_map.get(p_end, f"ID {p_end}")
                    target = f"TC ({element_id}): {start_name} -> {end_name}"
                else:
                    p_start, p_end = int(parts[1]), int(parts[2])
                    start_name = process_name_map.get(p_start, f"ID {p_start}")
                    end_name = process_name_map.get(p_end, f"ID {p_end}")
                    target = f"TC: {start_name} -> {end_name}"
            except (ValueError, IndexError):
                target = "TC (could not parse)"
        elif "_DSM_" in name:
            try:
                process_id = int(name.split("_")[0][1:])
                proc_name = process_name_map.get(process_id, f"ID {process_id}")
                param_type = "_".join(name.split("_")[1:])
                if process_id in dsm_params:
                    target = f"DSM: {proc_name} ({param_type})"
                else:
                    target = f"DSM: {proc_name} ({param_type}) - IGNORED"
            except (ValueError, IndexError):
                target = "DSM (could not parse)"
        elif name.startswith("P") and (
            "_decay_" in name or "_Inflow_fraction_f" in name
        ):
            try:
                process_id = int(name[1:].split("_")[0])
                proc_name = process_name_map.get(process_id, f"ID {process_id}")
                param_type = name.split("_", 1)[1]
                if process_id in fomp_params:
                    target = f"FOMP: {proc_name} ({param_type})"
                else:
                    target = f"FOMP: {proc_name} ({param_type}) - IGNORED"
            except (ValueError, IndexError):
                target = "FOMP (could not parse)"

        rows.append({"Parameter": name, "Target": target})

    mapping_df = pd.DataFrame(rows)

    # Validation warnings (pass uncertainty_params for TC bounds checking)
    _, warnings = validate_mc_parameters(mc_params_df, mfa_system, uncertainty_params)

    return {
        "mapping_df": mapping_df,
        "warnings": warnings,
        "n_params": len(uncertainty_params),
    }


def compute_mc_summary_stats(mc_results_df, mfa_system=None):
    """Compute summary statistics for MC stock results.

    Parameters
    ----------
    mc_results_df : pd.DataFrame
        Results DataFrame from run_mc_simulation().
    mfa_system : odym.MFAsystem, optional
        MFA system for process name mapping.

    Returns
    -------
    pd.DataFrame
        Summary with columns: Stock, Element, Mean, Std, Median,
        CI95_Lower, CI95_Upper, Min, Max.
    """
    # Identify stock columns (S_* but not dS_*, _timeseries, or _sample)
    stock_cols = [
        col
        for col in mc_results_df.columns
        if col.startswith("S_")
        and not col.startswith("dS_")
        and not col.endswith("_timeseries")
        and "_sample" not in col
    ]

    # Build process name map
    process_name_map = {}
    if mfa_system and hasattr(mfa_system, "ProcessList"):
        process_name_map = {p.ID: p.Name for p in mfa_system.ProcessList}

    rows = []
    for col in sorted(stock_cols):
        # Parse column name: S_7_material -> process_id=7, element=material
        parts = col.split("_")
        try:
            process_id = int(parts[1])
        except (ValueError, IndexError):
            process_id = None
        element = "_".join(parts[2:]) if len(parts) >= 3 else "?"

        proc_name = process_name_map.get(process_id, f"Process {process_id}")

        data = pd.to_numeric(mc_results_df[col], errors="coerce").dropna()
        if data.empty:
            continue

        rows.append(
            {
                "Stock": f"{proc_name} ({element})",
                "Element": element,
                "Mean": data.mean(),
                "Std": data.std(),
                "Median": data.median(),
                "CI95_Lower": data.quantile(0.025),
                "CI95_Upper": data.quantile(0.975),
                "Min": data.min(),
                "Max": data.max(),
            }
        )

    return pd.DataFrame(rows)


def compute_mc_mass_balance_report(mc_results_df):
    """Compute mass balance statistics across all MC iterations.

    Parameters
    ----------
    mc_results_df : pd.DataFrame
        Results DataFrame from run_mc_simulation(), expected to contain
        ``mass_balance_error_abs`` and ``mass_balance_error_rel`` columns,
        plus per-element columns ``mb_error_{element}`` and
        ``mb_input_{element}``.

    Returns
    -------
    dict
        Keys:
        - ``"summary"`` (pd.DataFrame): Single-row system-level summary.
        - ``"per_element"`` (pd.DataFrame): Per-element breakdown with
          mean error, mean input, and relative error.
        Returns ``None`` if mass balance columns are not present.
    """
    if "mass_balance_error_abs" not in mc_results_df.columns:
        return None

    abs_err = mc_results_df["mass_balance_error_abs"]
    rel_err = mc_results_df["mass_balance_error_rel"]

    summary_df = pd.DataFrame([{
        "Mean Abs. Error": abs_err.mean(),
        "Max Abs. Error": abs_err.max(),
        "Mean Rel. Error (%)": rel_err.mean() * 100,
        "Max Rel. Error (%)": rel_err.max() * 100,
        "Iterations with Error > 1%": int((rel_err > 0.01).sum()),
    }])

    # Per-element breakdown
    element_cols = [
        c.replace("mb_error_", "")
        for c in mc_results_df.columns
        if c.startswith("mb_error_")
    ]

    element_rows = []
    for elem in element_cols:
        err = mc_results_df[f"mb_error_{elem}"]
        inp = mc_results_df[f"mb_input_{elem}"]
        mean_input = inp.mean()
        mean_abs_err = err.abs().mean()
        rel_pct = (mean_abs_err / mean_input * 100) if mean_input > 0 else 0.0

        element_rows.append({
            "Element": elem,
            "Mean Input": mean_input,
            "Mean Abs. Error": mean_abs_err,
            "Max Abs. Error": err.abs().max(),
            "Rel. Error (%)": rel_pct,
        })

    element_df = pd.DataFrame(element_rows)

    return {"summary": summary_df, "per_element": element_df}
