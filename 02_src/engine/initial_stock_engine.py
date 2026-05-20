# -*- coding: utf-8 -*-
"""
Initial Stock Engine Module for the BioDYM Engine.

Handles processes that start with a pre-existing stock at t=0. Only the stock
composition (element fractions) and t=0 values are written to the MFA system —
outflow behaviour is delegated to the normal TC-driven solver or DSM Cohort mode.

This is a BioDYM extension to the ODYM framework.
"""

import numpy as np
import pandas as pd


def _build_initial_stock_element_column_map(elements, initial_stock_df):
    """Builds column-name mapping for initial stock element compositions.

    Priority order (first match wins):
    1. Basic_E{id}_Fraction[%]   e.g. Basic_E2_Fraction[%]   (preferred)
    2. IS_E{id}_Fraction[%]      e.g. IS_E2_Fraction[%]
    3. IS_E{id}_[%]({element})   e.g. IS_E2_[%](WC)
    4. IS_E{id}[%]               e.g. IS_E2[%]
    5. IS_E{id}_[%]              e.g. IS_E2_[%]
    6. IS_{element}[%]           e.g. IS_WC[%]

    Returns
    -------
    dict
        {element_name: parameter_type_column_name}  (None when no match found)
    """
    param_type_map = {}

    available_params = (
        initial_stock_df["IS_Parameter_type"].unique().tolist()
        if "IS_Parameter_type" in initial_stock_df.columns
        else []
    )

    for elem_idx, element in enumerate(elements):
        if element == "material":
            continue

        element_id = elem_idx + 1  # 1-based in Excel

        candidates = [
            f"Basic_E{element_id}_Fraction[%]",
            f"IS_E{element_id}_Fraction[%]",
            f"IS_E{element_id}_[%]({element})",
            f"IS_E{element_id}[%]",
            f"IS_E{element_id}_[%]",
            f"IS_{element}[%]",
        ]
        match = next((c for c in candidates if c in available_params), None)
        param_type_map[element] = match

    return param_type_map


def load_initial_stock_parameters(excel_data, elements=None):
    """Loads initial stock configurations from the '2_4_Initial_Stock' sheet.

    Reads a long-table format, groups by Process_ID, and returns a structured
    dict per process containing the t=0 material quantity, element fractions,
    and (optionally) DSM cohort parameters.

    Parameters
    ----------
    excel_data : dict
        DataFrames keyed by sheet name.
    elements : list of str, optional
        Element names matching mfa_system.Elements.

    Returns
    -------
    dict
        Keys are process IDs (int). Values are config dicts.
    """
    if elements is None:
        elements = ["material", "WC", "DM", "CC"]
        print("  -> INFO: No elements list provided to initial stock loader, using default: ['material', 'WC', 'DM', 'CC']")

    sheet_name = "2_4_Initial_Stock"
    print(f"--> Loading initial stock parameters from sheet '{sheet_name}'...")

    if sheet_name not in excel_data:
        print(f"--> INFO: Sheet '{sheet_name}' not found. No initial stocks will be loaded.")
        return {}

    df = excel_data[sheet_name]
    if df.empty:
        print(f"--> INFO: Sheet '{sheet_name}' is empty. No initial stocks will be loaded.")
        return {}

    required_columns = ["Process_ID", "IS_Parameter_type", "IS_Parameter_Value"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"--> ERROR: Missing required columns in '{sheet_name}': {missing_columns}")
        return {}

    df = df.dropna(subset=["Process_ID", "IS_Parameter_type", "IS_Parameter_Value"])
    df["Process_ID"] = df["Process_ID"].astype(int)

    def safe_float(value):
        if pd.isna(value):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value.replace(",", "."))
            except ValueError:
                return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    df["IS_Parameter_Value_Numeric"] = df["IS_Parameter_Value"].apply(safe_float)

    element_param_map = _build_initial_stock_element_column_map(elements, df)
    print(f"  -> Element parameter mapping: {element_param_map}")

    initial_stock_configs = {}

    for process_id, group in df.groupby("Process_ID"):
        config = {
            "process_id": process_id,
            "initial_stock_values": {},
            "elements": elements,
        }

        for _, row in group.iterrows():
            param_name = str(row["IS_Parameter_type"]).strip()
            param_value_raw = row["IS_Parameter_Value"]
            param_value = row.get("IS_Parameter_Value_Numeric")
            unit = row.get("Unit", "")
            notes = row.get("Notes", "")

            # Material quantity — accept both old and new names
            if param_name in ("IS_material_quantity[UoM]", "Basic_Material_Quantity[UoM]"):
                if param_value is not None:
                    config["initial_stock_values"]["Initial_Stock_material"] = float(param_value)
                else:
                    print(f"    WARNING: Process {process_id} has non-numeric material quantity: {param_value_raw}")
                continue

            # Element composition fractions
            handled = False
            for element, mapped_param in element_param_map.items():
                if mapped_param and param_name == mapped_param:
                    if param_value is not None:
                        config["initial_stock_values"][f"Initial_Stock_{element}[%]"] = float(param_value)
                    else:
                        print(f"    WARNING: Process {process_id} has non-numeric {element} value: {param_value_raw}")
                    handled = True
                    break
            if handled:
                continue

            # DSM cohort parameters
            if param_name == "Cohort_Age_Distribution_Type":
                config["cohort_age_distribution_type"] = str(param_value_raw).strip()
            elif param_name == "Cohort_Max_Age[years]":
                if param_value is not None:
                    config["cohort_max_age"] = int(param_value)
                else:
                    print(f"    WARNING: Process {process_id} has non-numeric max age: {param_value_raw}")
            elif param_name == "Cohort_Decay_Constant[years]":
                if param_value is not None:
                    config["cohort_decay_constant"] = float(param_value)
                else:
                    print(f"    WARNING: Process {process_id} has non-numeric decay constant: {param_value_raw}")
            elif param_name == "Cohort_Mean_Age[years]":
                if param_value is not None:
                    config["cohort_mean_age"] = float(param_value)
                else:
                    print(f"    WARNING: Process {process_id} has non-numeric mean age: {param_value_raw}")
            elif param_name == "Cohort_StdDev_Age[years]":
                if param_value is not None:
                    config["cohort_std_age"] = float(param_value)
                else:
                    print(f"    WARNING: Process {process_id} has non-numeric std age: {param_value_raw}")
            else:
                config[
                    param_name.lower().replace(" ", "_").replace("[", "").replace("]", "")
                ] = {"value": param_value, "unit": unit, "notes": notes}

        if _validate_initial_stock_config(config):
            initial_stock_configs[process_id] = config
            print(f"  -> Loaded initial stock config for Process {process_id}")
        else:
            print(f"  -> WARNING: Invalid initial stock config for Process {process_id}")

    print(f"--> Successfully loaded initial stock configurations for {len(initial_stock_configs)} process(es).")
    return initial_stock_configs


def _validate_initial_stock_config(config):
    """Returns True if the config has at least a material quantity."""
    return "Initial_Stock_material" in config["initial_stock_values"]


def apply_initial_stock_values(mfa_system, initial_stock_configs):
    """Writes t=0 stock values into the MFA system's StockDict.

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        Modified in place.
    initial_stock_configs : dict
        As returned by load_initial_stock_parameters().

    Returns
    -------
    odym.MFAsystem
    """
    print("--> Applying initial stock values...")

    for process_id, config in initial_stock_configs.items():
        stock_s = mfa_system.StockDict.get(f"S_{process_id}")
        if stock_s is None:
            print(f"  -> WARNING: Stock S_{process_id} not found for Process {process_id}")
            continue

        elements = config.get("elements", ["material", "WC", "DM", "CC"])
        initial_values = _calculate_initial_stock_values(config["initial_stock_values"], elements)
        stock_s.Values[0, :] = initial_values

        print(f"  -> Set initial stock for Process {process_id}: {initial_values[0]:.1f} Mg material")

    print("--> Initial stock values applied.")
    return mfa_system


def _calculate_initial_stock_values(stock_values, elements):
    """Returns element-wise initial stock vector from material quantity and fractions.

    Fractions are expected as decimals (0–1), not percentages.
    """
    result = np.zeros(len(elements))
    material = stock_values.get("Initial_Stock_material", 0.0)
    result[0] = material
    for idx, element in enumerate(elements[1:], start=1):
        fraction = stock_values.get(f"Initial_Stock_{element}[%]", 0.0)
        result[idx] = material * fraction
    return result


def calculate_initial_stock_balances(mfa_system, initial_stock_configs):
    """Deprecated — stock balances are computed by solver.calculate_final_balances()."""
    import warnings
    warnings.warn(
        "calculate_initial_stock_balances() is deprecated and has no effect. "
        "Stock balances are computed inside solver.calculate_final_balances().",
        DeprecationWarning,
        stacklevel=2,
    )
    return mfa_system
