# -*- coding: utf-8 -*-
"""
Data Loader Module for the BioDYM MFA Model.

This file contains all functions responsible for reading, validating, and
parsing the input data from the Excel template file. It acts as the
interface between the raw data and the core model logic.

UPDATED: Added column name mapping to handle naming convention changes.
"""

import re
import pandas as pd
import numpy as np
from copy import deepcopy

# Import ODYM classes only when needed
try:
    import ODYM_Classes as msc

    ODYM_AVAILABLE = True
except ImportError:
    # Try to add ODYM path and import again
    import os
    import sys

    try:
        # Try to locate ODYM in the project structure
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        odym_path = os.path.join(
            project_root, "06_framework", "ODYM-master_20241127", "odym", "modules"
        )
        if os.path.exists(odym_path) and odym_path not in sys.path:
            sys.path.insert(0, odym_path)
        import ODYM_Classes as msc

        ODYM_AVAILABLE = True
    except ImportError:
        ODYM_AVAILABLE = False
        msc = None


def _sanitize_col_name(name):
    """Convert a string to a safe column identifier.

    Replaces any character that is not a letter, digit, or underscore with
    an underscore, then collapses runs of underscores to a single one.
    """
    result = re.sub(r"[^A-Za-z0-9_]", "_", str(name))
    return re.sub(r"_+", "_", result)


# Column name mapping for backward compatibility and naming convention updates
COLUMN_NAME_MAPPING = {
    # Sheet: {old_name: new_name}
    "1_1_Definition_Flows": {
        "Flow_WC_ID ": "Flow_WC_ID",  # Remove trailing space
        # New [%] columns are already correctly named
    },
    "1_2_Data_Flows": {
        "Flow_Data_Year": "Flow_Data_Year",  # Keep as is
        "Flow_Material": "Flow_Material",  # Keep as is
        "WC_[%]": "WC_[%]",  # Keep as is
        "DM_[%]": "DM_[%]",  # Keep as is
        "CC_[%]": "CC_[%]",  # Keep as is
        "Author_Source": "Author_Source",  # Keep as is
        "Type_Source": "Type_Source",  # Keep as is
    },
    "2_1_Definition_Processes": {
        "Nr. Outflows": "Outflow_count",  # Standardize naming
    },
    "2_2_static_TCs": {
        "Nr. Outflows": "Outflow_count",  # Standardize naming
        "Titel_Source": "Titel_source",  # Standardize case
        "Author_Source": "Author_source",  # Standardize case
    },
    "2_3_dynamic_TCs": {
        "Nr. Outflows": "Outflow_count",  # Standardize naming
        "Titel_Source": "Titel_source",  # Standardize case
        "Author_Source": "Author_source",  # Standardize case
    },
    "2_4_Initial_Stock": {
        "Nr. Outflows": "Outflow_count",  # Standardize naming
        "Initial_Stock_WC[%]": "Initial_Stock_WC[%]",  # Keep as is
        "Initial_Stock_DM[%]": "Initial_Stock_DM[%]",  # Keep as is
        "Initial_Stock_CC[%]": "Initial_Stock_CC[%]",  # Keep as is
    },
    "3_1_Definition_DSM": {
        "Inflow_Split_[%]": "Inflow_Split_[%]",  # Keep as is
        "Lifetime_Type": "Lifetime_Type",  # Keep as is
        "Lifetime_Mean": "Lifetime_Mean",  # Keep as is
        "Lifetime_StdDev": "Lifetime_StdDev",  # Keep as is
        "Category_Name": "Category_Name",  # Keep as is
        "Category_ID": "Category_ID",  # Keep as is
        "DSM_Parameter": "DSM_Parameter_type",  # Updated to new name
        "DSM_Value": "DSM_Value",  # Keep as is
        "DSM_material_count": "DSM_material_count",  # New column
        "DSM_Parameter_ID": "DSM_Parameter_ID",  # New column
    },
    "3_2_Definition_FOMP": {
        "Pool_ID": "Pool_ID",  # Keep as is
        "Parameter_Name": "Parameter_Name",  # Keep as is
        "Value": "Value",  # Keep as is
        "FOMP_Parameter": "FOMP_Parameter_type",  # Updated to new name
        "FOMP_Value": "FOMP_Parameter_Value",  # Updated to new name
        "Nr._Decay_Pools": "Nr._Decay_Pools",  # New column
        "Pool": "Pool",  # New column
        "Decay_Pool_count": "Decay_Pool_count",  # New column
        "FOMP_Parameter_ID": "FOMP_Parameter_ID",  # New column
    },
    "3_3_Definition_LFG": {
        "LFG_Parameter_ID": "LFG_Parameter_ID",
        "LFG_Parameter_type": "LFG_Parameter_type",
        "LFG_Parameter_Value": "LFG_Parameter_Value",
        "Process_ID": "Process_ID",
    },
    "3_3_Definition_BOM_Assembly": {
        "Process_ID": "Process_ID",
        "Output_flow_type": "Output_flow_type",
        "Flow_ID": "Flow_ID",
        "TC_Configuration": "TC_Configuration",
    },
    # Add more mappings as needed
}

# Sheet name mapping for backward compatibility
SHEET_NAME_MAPPING = {
    "PX - Template": "PX_Template",  # Standardize separator
    "2_3_static_TCs": "2_2_static_TCs",  # Handle sheet renumbering
    # Add more mappings as needed
}


def normalize_column_names(df, sheet_name=None, elements=None):
    """Normalizes column names in a DataFrame.

    Two passes:
    1. Static mapping from COLUMN_NAME_MAPPING (sheet-specific renames).
    2. Dynamic E{n}_TC_ID / E{n}_TC_Value[%] → <element>_TC_ID / <element>_Value[%]
       when `elements` is provided (omits 'material' at index 0).

    Also raises ValueError early if pandas-style duplicate-column suffixes
    (.1, .2, …) are detected — these indicate an Excel column-naming collision
    that must be fixed in the source file.

    Parameters
    ----------
    df : pd.DataFrame
    sheet_name : str, optional
    elements : list of str, optional
        Ordered element names (first entry is 'material').  When supplied,
        E{n}_TC_ID → <element>_TC_ID and E{n}_TC_Value[%] → <element>_Value[%]
        renames are applied (only when the named column does not already exist).

    Returns
    -------
    pd.DataFrame
    """
    # Guard: detect pandas duplicate-column suffix (.1, .2, …)
    # Warns rather than raises so existing files with accidental duplicates
    # still load; the warning surfaces the issue without crashing the model.
    import warnings as _warnings

    dupe_cols = [c for c in df.columns if re.search(r"\.\d+$", str(c))]
    if dupe_cols:
        _warnings.warn(
            f"duplicate columns detected (pandas .N suffix): {dupe_cols}. "
            "Fix the source Excel file before loading.",
            UserWarning,
            stacklevel=2,
        )

    # Pass 1: static sheet-specific renames
    if sheet_name and sheet_name in COLUMN_NAME_MAPPING:
        df = df.rename(columns=COLUMN_NAME_MAPPING[sheet_name])

    # Pass 2: dynamic E{n} → element-name renames
    if elements:
        rename_map = {}
        for elem_idx, element in enumerate(elements):
            if element == "material":
                continue
            n = elem_idx + 1
            tc_id_old = f"E{n}_TC_ID"
            tc_id_new = f"{element}_TC_ID"
            if tc_id_old in df.columns and tc_id_new not in df.columns:
                rename_map[tc_id_old] = tc_id_new

            val_old = f"E{n}_TC_Value[%]"
            val_new = f"{element}_Value[%]"
            if val_old in df.columns and val_new not in df.columns:
                rename_map[val_old] = val_new
        if rename_map:
            df = df.rename(columns=rename_map)

    return df


def normalize_sheet_names(excel_data_dict):
    """Normalizes sheet and column names in the Excel data dictionary.

    Iterates through a dictionary of DataFrames, first normalizing the sheet name
    (the dictionary key) and then normalizing the column names of the DataFrame
    itself.

    Parameters
    ----------
    excel_data_dict : dict
        A dictionary where keys are sheet names and values are pandas DataFrames.

    Returns
    -------
    dict
        A new dictionary with both sheet names and column names normalized.
    """
    normalized_data = {}
    for sheet_name, df in excel_data_dict.items():
        # Normalize sheet name
        normalized_sheet_name = SHEET_NAME_MAPPING.get(sheet_name, sheet_name)

        # Normalize column names
        df_normalized = normalize_column_names(df, sheet_name)

        normalized_data[normalized_sheet_name] = df_normalized

    return normalized_data


def validate_input_data(excel_data_dict, debug_mode=False):
    """Checks if the loaded Excel data has the minimum required structure.

    This function validates that all essential sheets and columns, as defined
    in the `REQUIRED_STRUCTURE` constant, are present in the input data.
    It provides clear error messages if a required item is missing.

    Parameters
    ----------
    excel_data_dict : dict
        A dictionary where keys are sheet names and values are pandas DataFrames.
    debug_mode : bool, optional
        If True, print detailed validation progress. Default is False.

    Raises
    ------
    ValueError
        If a required sheet or column is not found in the input data.
    """
    if debug_mode:
        print("--> Validating input data structure...")

    # Define the minimum required structure for the model to run.
    # Support both new E# format and legacy element-name columns for backward compatibility
    REQUIRED_STRUCTURE = {
        "1_1_Definition_Flows": [
            "Flow_ID",
            "Flow_Name",
            "Flow_Output_Process_ID",
            "Input_Process_ID",
        ],
        "1_2_Data_Flows": ["Flow_ID", "Flow_Data_Year"],
        "2_1_Definition_Processes": ["ID", "Process_Name", "Process_Logic"],
        "2_2_static_TCs": ["Flow_ID", "Process_ID"],
        "2_3_dynamic_TCs": ["Year"],
        "2_4_Initial_Stock": [
            "Process_ID",
            "IS_Parameter_type",
            "IS_Parameter_Value",
        ],
    }

    # Element-specific columns that can be in different formats
    # Old format: Flow_WC[%], Flow_DM[%], TC_Value_material
    # New format: Flow_E2_Fraction[%], E1_TC_Value[%]
    ELEMENT_COLUMN_PATTERNS = {
        "1_1_Definition_Flows": {
            "old": ["Flow_WC[%]", "Flow_DM[%]", "Flow_CC_DM[%]"],
            "new_pattern": ["Flow_E", "_Fraction[%]"],  # Pattern: Flow_E#_Fraction[%]
        },
        "1_2_Data_Flows": {
            "old": ["Flow_Material"],
            "new": [
                "E1_value",
                "E2_value",
                "E3_value",
                "E1_Fraction[%]",
            ],  # Direct match
        },
        "2_2_static_TCs": {
            "old": ["TC_material_ID", "TC_Value_material"],
            "new": ["E1_TC_ID", "E2_TC_ID", "E1_TC_Value[%]"],  # Direct match
        },
        "2_3_dynamic_TCs": {
            "old": ["TC_material_ID", "TC_Value_material"],
            "new": ["E1_TC_ID", "E2_TC_ID", "E1_TC_Value[%]"],
        },
    }

    for sheet_name, required_columns in REQUIRED_STRUCTURE.items():
        if sheet_name not in excel_data_dict:
            # TC sheets are optional - only required if processes use TCs
            if sheet_name in ["2_2_static_TCs", "2_3_dynamic_TCs"]:
                if debug_mode:
                    print(
                        f"  -> Optional sheet '{sheet_name}' not found (TCs may not be used)"
                    )
                continue
            else:
                raise ValueError(
                    f"ERROR: The required sheet '{sheet_name}' was not found in the Excel file!"
                )

        existing_columns = list(excel_data_dict[sheet_name].columns)

        # Special handling for process definition sheet to support both unified and legacy columns
        if sheet_name == "2_1_Definition_Processes":
            # Check for unified columns first
            unified_columns = ["TC_Configuration", "Stock_Configuration"]
            legacy_columns = ["TC?", "TC_Type", "Stock?", "Initial_Stock?"]

            has_unified = all(col in existing_columns for col in unified_columns)
            has_legacy = all(col in existing_columns for col in legacy_columns)

            if not has_unified and not has_legacy:
                missing_unified = [
                    col for col in unified_columns if col not in existing_columns
                ]
                missing_legacy = [
                    col for col in legacy_columns if col not in existing_columns
                ]
                raise ValueError(
                    f"ERROR: Sheet '{sheet_name}' must have either unified columns {unified_columns} "
                    f"OR legacy columns {legacy_columns}. "
                    f"Missing unified: {missing_unified}, Missing legacy: {missing_legacy}"
                )
            elif has_unified and debug_mode:
                print(f"  -> Using unified configuration columns in '{sheet_name}'")
            elif has_legacy and debug_mode:
                print(f"  -> Using legacy configuration columns in '{sheet_name}'")

        # Standard validation for core columns (non-element-specific)
        for col in required_columns:
            if col not in existing_columns:
                raise ValueError(
                    f"ERROR: The required column '{col}' is missing from sheet '{sheet_name}'!"
                )

        # Check for element-specific columns (old OR new format)
        if sheet_name in ELEMENT_COLUMN_PATTERNS:
            patterns = ELEMENT_COLUMN_PATTERNS[sheet_name]
            old_format = patterns.get("old", [])
            new_format = patterns.get("new", [])
            new_pattern = patterns.get("new_pattern", [])

            # Check if ANY old format columns exist
            has_old = any(col in existing_columns for col in old_format)

            # Check if ANY new format columns exist
            has_new = False

            # Pattern matching (e.g., "Flow_E" and "_Fraction[%]")
            if new_pattern:
                pattern_parts = new_pattern
                has_new = any(
                    all(part in str(col) for part in pattern_parts)
                    for col in existing_columns
                )

            # Direct column name matching
            if not has_new and new_format:
                has_new = any(col in existing_columns for col in new_format)

            if not has_old and not has_new:
                example_format = new_pattern if new_pattern else new_format
                raise ValueError(
                    f"ERROR: Sheet '{sheet_name}' must have element columns in either "
                    f"old format {old_format} OR new E# format (e.g., {example_format}). "
                    f"No element columns found!"
                )
            elif has_new and debug_mode:
                print(f"  -> Using new E# format for element columns in '{sheet_name}'")
            elif has_old and debug_mode:
                print(f"  -> Using legacy element-name format in '{sheet_name}'")

    if debug_mode:
        print("--> Input data validation successful.")


def validate_process_logic(excel_data):
    """Validates that processes with 'Input' or 'Output' logic are configured correctly.

    Checks that processes defined with `Process_Logic` = 'Input' have no
    inflows defined in the flowsheet, and that 'Output' processes have no
    outflows. It prints warnings for any inconsistencies.

    Parameters
    ----------
    excel_data : dict
        Dictionary of DataFrames from the loaded Excel file.

    Returns
    -------
    dict
        The `process_logic_map` mapping process IDs to their logic strings.
    """
    print("--> Validating Process_Logic configuration...")

    process_defs = excel_data.get("2_1_Definition_Processes")
    flows_defs = excel_data.get("1_1_Definition_Flows")

    if process_defs is None or flows_defs is None:
        print("--> WARNING: Cannot validate Process_Logic - missing required sheets.")
        return

    # Get all process IDs and their logic
    process_logic_map = {}
    for _, row in process_defs.iterrows():
        if pd.notna(row.get("Process_ID")):
            process_logic_map[int(row["Process_ID"])] = str(
                row.get("Process_Logic", "")
            ).strip()

    # Get inflow/outflow connections
    inflows_by_process = {}
    outflows_by_process = {}

    for _, row in flows_defs.iterrows():
        if pd.notna(row.get("Flow_Output_Process_ID")) and pd.notna(
            row.get("Input_Process_ID")
        ):
            start_id = int(row["Flow_Output_Process_ID"])
            end_id = int(row["Input_Process_ID"])

            if start_id not in outflows_by_process:
                outflows_by_process[start_id] = []
            outflows_by_process[start_id].append(row["Flow_ID"])

            if end_id not in inflows_by_process:
                inflows_by_process[end_id] = []
            inflows_by_process[end_id].append(row["Flow_ID"])

    # Validate Input processes (should have no inflows)
    input_processes = [
        pid for pid, logic in process_logic_map.items() if logic == "Input"
    ]
    for pid in input_processes:
        if pid in inflows_by_process:
            print(
                f"--> WARNING: Input process {pid} has inflows: {inflows_by_process[pid]}"
            )
        else:
            print(f"--> OK: Input process {pid} correctly has no inflows")

    # Validate Output processes (should have no outflows)
    output_processes = [
        pid for pid, logic in process_logic_map.items() if logic == "Output"
    ]
    for pid in output_processes:
        if pid in outflows_by_process:
            print(
                f"--> WARNING: Output process {pid} has outflows: {outflows_by_process[pid]}"
            )
        else:
            print(f"--> OK: Output process {pid} correctly has no outflows")

    print("--> Process_Logic validation completed.")
    return process_logic_map


def validate_unified_configuration(excel_data):
    """Validates consistency between Process_Logic and the unified configuration columns.

    Checks for logical consistency between a process's defined `Process_Logic`
    (e.g., 'DSM') and its `TC_Configuration` and `Stock_Configuration` settings,
    printing warnings for any identified issues.

    Parameters
    ----------
    excel_data : dict
        Dictionary of DataFrames from the loaded Excel file.
    """
    print("--> Validating unified configuration columns...")

    process_defs = excel_data.get("2_1_Definition_Processes")
    if process_defs is None:
        print(
            "--> WARNING: Cannot validate unified configuration - missing process definitions."
        )
        return

    # Check TC_Configuration consistency
    print("--> Checking TC_Configuration consistency...")
    tc_issues = []
    for _, row in process_defs.iterrows():
        if pd.notna(row.get("Process_ID")):
            process_id = int(row["Process_ID"])
            process_logic = str(row.get("Process_Logic", "")).strip()
            tc_config = str(row.get("TC_Configuration", "")).strip()

            # Input/Output processes should have Static TC_Configuration
            if process_logic in ["Input", "Output"] and tc_config != "Static":
                tc_issues.append(
                    f"Process {process_id}: {process_logic} with {tc_config} TC_Configuration (should be Static)"
                )

    if tc_issues:
        print("--> TC_Configuration issues found:")
        for issue in tc_issues:
            print(f"    - {issue}")
    else:
        print("--> TC_Configuration is consistent! ✅")

    # Check Stock_Configuration consistency
    print("--> Checking Stock_Configuration consistency...")
    stock_issues = []
    for _, row in process_defs.iterrows():
        if pd.notna(row.get("Process_ID")):
            process_id = int(row["Process_ID"])
            process_logic = str(row.get("Process_Logic", "")).strip()
            stock_config = str(row.get("Stock_Configuration", "")).strip()

            # DSM processes should have Stock or DSM initial stock variants
            valid_dsm_stock_configs = [
                "Stock",
                "Stock_with_InitialStock_Cohort",
                "Stock_with_InitialStock_Decay",
            ]
            if process_logic in ("DSM", "DSM_Component") and stock_config not in valid_dsm_stock_configs:
                stock_issues.append(
                    f"Process {process_id}: DSM with invalid Stock_Configuration '{stock_config}' "
                    f"(should be one of: {', '.join(valid_dsm_stock_configs)})"
                )

            # Output processes should have Stock
            if process_logic == "Output" and stock_config != "Stock":
                stock_issues.append(
                    f"Process {process_id}: Output with {stock_config} Stock_Configuration (should be Stock)"
                )

    if stock_issues:
        print("--> Stock_Configuration issues found:")
        for issue in stock_issues:
            print(f"    - {issue}")
    else:
        print("--> Stock_Configuration is consistent! ✅")

    print("--> Unified configuration validation completed.")


def normalize_dynamic_tcs_by_process(
    tc_params, all_excel_data, elements, debug_mode=False
):
    """Normalize dynamic TCs so they sum to 100% for each process at each time step.

    When multiple dynamic TCs are interpolated independently for a splitter process,
    they may not sum to exactly 100% at every time step, causing mass balance errors.
    This function identifies TCs belonging to the same process and normalizes them
    proportionally to ensure they sum to 1.0 (100%) at each time step.

    Parameters
    ----------
    tc_params : dict
        Dictionary of ODYM Parameter objects (TC values), keyed by parameter name.
    all_excel_data : dict
        Dictionary of DataFrames from the loaded Excel file.
    elements : list of str
        List of element names being tracked in the model.
    debug_mode : bool, optional
        If True, print detailed normalization progress. Default is False.

    Returns
    -------
    dict
        Dictionary of normalized TC parameters.

    Notes
    -----
    This function implements the same normalization logic as the Monte Carlo
    simulation's `normalize_tcs_for_process()` function, but applies it to
    dynamic TCs after interpolation to prevent mass balance errors.

    See Also
    --------
    02_src/engine/mc_simulation.py : normalize_tcs_for_process
    05_docs/development/DYNAMIC_TC_MASS_BALANCE_BUG.md : Bug documentation
    """
    static_tc_defs = all_excel_data.get("2_2_static_TCs")
    if static_tc_defs is None or static_tc_defs.empty:
        return tc_params

    # Detect TC column format
    tc_format = "new" if "E1_TC_ID" in static_tc_defs.columns else "old"

    # Group TCs by process and element
    # Structure: {process_id: {element: [tc_names]}}
    process_element_tcs = {}

    for _, row in static_tc_defs.iterrows():
        process_id = row.get("Process_ID")
        if pd.isna(process_id):
            continue

        process_id = int(process_id)

        # Extract TC names for each element
        for elem_idx, element in enumerate(elements):
            if tc_format == "new":
                element_id = elem_idx + 1
                tc_id_col = f"E{element_id}_TC_ID"
            else:
                tc_id_col = f"TC_{element}_ID"

            if tc_id_col in row.index and pd.notna(row[tc_id_col]):
                tc_name = row[tc_id_col]

                if tc_name in tc_params:
                    if process_id not in process_element_tcs:
                        process_element_tcs[process_id] = {}
                    if element not in process_element_tcs[process_id]:
                        process_element_tcs[process_id][element] = []

                    if tc_name not in process_element_tcs[process_id][element]:
                        process_element_tcs[process_id][element].append(tc_name)

    # Normalize TCs for each process and element
    normalization_count = 0

    for process_id, element_tcs in process_element_tcs.items():
        for element, tc_names in element_tcs.items():
            if len(tc_names) <= 1:
                continue  # Single TC doesn't need normalization

            # Check if any TC is time-varying (has array values)
            has_dynamic = any(
                isinstance(tc_params[tc].Values, np.ndarray)
                for tc in tc_names
                if tc in tc_params
            )

            if not has_dynamic:
                continue  # Static TCs don't need time-based normalization

            # Get TC values (convert scalars to arrays if needed)
            tc_values = {}
            max_len = 1

            for tc_name in tc_names:
                if tc_name not in tc_params:
                    continue

                val = tc_params[tc_name].Values
                if isinstance(val, np.ndarray):
                    tc_values[tc_name] = val.copy()  # Copy to avoid modifying original
                    max_len = max(max_len, len(val))
                else:
                    # Static TC - will be broadcast
                    tc_values[tc_name] = float(val)

            if not tc_values:
                continue

            # Convert scalars to arrays
            for tc_name in tc_values:
                if not isinstance(tc_values[tc_name], np.ndarray):
                    tc_values[tc_name] = np.full(max_len, tc_values[tc_name])

            # Calculate sum at each time step
            tc_sum = np.zeros(max_len)
            for tc_name in tc_values:
                tc_sum += tc_values[tc_name]

            # Check for large deviations (more than 5%)
            max_deviation = np.max(np.abs(tc_sum - 1.0))
            if max_deviation > 0.05:
                print(
                    f"   ⚠️  WARNING: Process {process_id}, element {element}: "
                    f"TCs sum to {tc_sum.min() * 100:.1f}%-{tc_sum.max() * 100:.1f}% (not 100%)"
                )
                print(
                    f"      → Normalizing {len(tc_names)} TCs to ensure mass balance..."
                )

            # Normalize (avoid division by zero)
            for tc_name in tc_values:
                normalized = np.divide(
                    tc_values[tc_name],
                    tc_sum,
                    out=np.ones_like(tc_values[tc_name]) / len(tc_values),
                    where=tc_sum != 0,
                )

                # Update parameter
                tc_params[tc_name].Values = normalized

            normalization_count += 1

            if debug_mode:
                print(
                    f"   → Normalized {len(tc_names)} TCs for process {process_id}, "
                    f"element {element} (max deviation: {max_deviation * 100:.2f}%)"
                )

    if normalization_count > 0 and not debug_mode:
        print(
            f"   ✓ Normalized dynamic TCs for {normalization_count} process-element combinations"
        )

    return tc_params


def load_tc_parameters(all_excel_data, elements, time_vector, debug_mode=False):
    """Loads and constructs all transfer coefficient (TC) parameters.

    This function orchestrates the loading of both static and dynamic TCs
    based on the `TC_Configuration` column in the process definitions sheet.
    It handles different loading strategies and returns a unified dictionary
    of ODYM Parameter objects.

    Parameters
    ----------
    all_excel_data : dict
        Dictionary of DataFrames from the loaded Excel file.
    elements : list of str
        List of element names being tracked in the model.
    time_vector : list or np.ndarray
        The array of years for the model run, used for interpolating dynamic TCs.
    debug_mode : bool, optional
        If True, print detailed loading progress. Default is False.

    Returns
    -------
    dict
        A dictionary of ODYM Parameter objects, keyed by parameter name.
    """
    if not ODYM_AVAILABLE:
        print(
            "--> WARNING: ODYM_Classes not available. TC parameters cannot be loaded."
        )
        return {}

    if debug_mode:
        print("--> Loading Transfer Coefficients using unified TC_Configuration...")

    process_defs = all_excel_data.get("2_1_Definition_Processes")
    static_tc_defs = all_excel_data.get("2_2_static_TCs")
    dynamic_tc_defs = all_excel_data.get("2_3_dynamic_TCs")

    if process_defs is None:
        if debug_mode:
            print("-> No Process definitions found. Skipping TC loading.")
        return {}

    # Create process type mapping based on TC_Configuration column
    process_tc_types = {}
    for _, row in process_defs.iterrows():
        process_id = row.get("Process_ID")
        process_logic = str(row.get("Process_Logic", "")).strip()
        tc_config = str(row.get("TC_Configuration", "")).strip()

        # Skip TCs for Input, Output, and Pass-through processes regardless of TC_Configuration
        if pd.notna(process_id) and process_logic in [
            "Input",
            "Output",
            "Pass-through",
        ]:
            if debug_mode:
                print(
                    f"--> INFO: Process {process_id} ({process_logic}) - skipping TCs (process type)"
                )
            continue

        # Only processes with Splitter, Transformer, or DSM logic can have TCs
        if pd.notna(process_id) and process_logic in ["Splitter", "Transformer", "DSM", "DSM_Component"]:
            if tc_config in ["Static", "Dynamic"]:
                process_tc_types[int(process_id)] = tc_config
            else:
                if debug_mode:
                    print(
                        f"--> WARNING: Process {process_id} ({process_logic}) has TC_Configuration='{tc_config}' - skipping TCs"
                    )

    tc_params = {}
    param_id_counter = 1000

    # Detect TC column format (old: TC_material_ID, new: E1_TC_ID)
    tc_format = "old"  # default
    if static_tc_defs is not None and not static_tc_defs.empty:
        # Check if new E# format columns exist
        if "E1_TC_ID" in static_tc_defs.columns or "E2_TC_ID" in static_tc_defs.columns:
            tc_format = "new"
            if debug_mode:
                print("  -> Detected new E# format for TC columns")
        else:
            if debug_mode:
                print("  -> Detected legacy element-name format for TC columns")

    # Process Static TCs
    static_processes = [
        pid for pid, tc_type in process_tc_types.items() if tc_type == "Static"
    ]
    if static_processes and static_tc_defs is not None:
        if debug_mode:
            print(
                f"  -> Processing static TCs for {len(static_processes)} processes..."
            )
        for _, row in static_tc_defs.iterrows():
            process_id = row.get("Process_ID")
            if pd.isna(process_id) or int(process_id) not in static_processes:
                continue

            for elem_idx, element in enumerate(elements):
                # Build column names based on format
                if tc_format == "new":
                    # New format: E1_TC_ID, E1_TC_Value[%]
                    element_id = elem_idx + 1
                    param_name_col = f"E{element_id}_TC_ID"
                    param_value_col = f"E{element_id}_TC_Value[%]"
                else:
                    # Old format: TC_material_ID, TC_Value_material
                    param_name_col = f"TC_{element}_ID"
                    param_value_col = f"TC_Value_{element}"

                if (
                    param_name_col in row
                    and pd.notna(row[param_name_col])
                    and param_value_col in row
                    and pd.notna(row[param_value_col])
                ):
                    param_name = row[param_name_col]
                    value = row[param_value_col]

                    if param_name not in tc_params:
                        tc_params[param_name] = msc.Parameter(
                            Name=param_name, ID=param_id_counter, Values=value, Unit="1"
                        )
                        param_id_counter += 1
                        if debug_mode:
                            print(f"    -> Loaded static TC: {param_name} = {value}")
                    else:
                        print(
                            f"⚠️ Warning: Duplicate static TC parameter name found: {param_name}. Using first value found."
                        )

    # Process Dynamic TCs
    dynamic_processes = [
        pid for pid, tc_type in process_tc_types.items() if tc_type == "Dynamic"
    ]
    if dynamic_processes and dynamic_tc_defs is not None:
        if debug_mode:
            print(
                f"  -> Processing dynamic TCs for {len(dynamic_processes)} processes..."
            )

        # Detect format for dynamic TCs (same as static)
        dynamic_tc_format = "old"
        if (
            "E1_TC_ID" in dynamic_tc_defs.columns
            or "E2_TC_ID" in dynamic_tc_defs.columns
        ):
            dynamic_tc_format = "new"

        # Process each element
        for elem_idx, element in enumerate(elements):
            # Build column names based on format
            if dynamic_tc_format == "new":
                element_id = elem_idx + 1
                param_name_col = f"E{element_id}_TC_ID"
                param_value_col = f"E{element_id}_TC_Value[%]"
            else:
                param_name_col = f"TC_{element}_ID"
                param_value_col = f"TC_Value_{element}"

            # Check if columns exist
            if (
                param_name_col not in dynamic_tc_defs.columns
                or param_value_col not in dynamic_tc_defs.columns
            ):
                continue

            # Group dynamic TC data by parameter name
            try:
                dynamic_tc_data = dynamic_tc_defs[
                    [param_name_col, param_value_col, "Year"]
                ].dropna()
            except KeyError:
                continue

            if dynamic_tc_data.empty:
                continue

            for param_name in dynamic_tc_data[param_name_col].unique():
                tc_points = dynamic_tc_data[
                    dynamic_tc_data[param_name_col] == param_name
                ]

                # Create time series
                ts = pd.Series(
                    tc_points[param_value_col].values, index=tc_points["Year"]
                )

                # Reindex to full time vector and interpolate
                ts_full = ts.reindex(time_vector)
                ts_interpolated = ts_full.interpolate(
                    method="linear", limit_direction="both"
                )

                # Handle edge cases where interpolation might fail
                if ts_interpolated.isna().any():
                    ts_interpolated = ts_interpolated.ffill().bfill()

                tc_params[param_name] = msc.Parameter(
                    Name=param_name,
                    ID=param_id_counter,
                    Values=ts_interpolated.to_numpy(),
                    Unit="1",
                )
                param_id_counter += 1
                if debug_mode:
                    print(
                        f"    -> Loaded dynamic TC: {param_name} ({len(tc_points)} data points -> {len(ts_interpolated)} time steps)"
                    )

    # Normalize dynamic TCs to ensure they sum to 100% per process/element
    # This prevents mass balance errors when TCs are interpolated independently
    if len(tc_params) > 0 and dynamic_processes:
        tc_params = normalize_dynamic_tcs_by_process(
            tc_params, all_excel_data, elements, debug_mode
        )

    # Always print summary (not just debug mode)
    if len(tc_params) > 0:
        static_count = len([p for p in static_processes]) if static_processes else 0
        dynamic_count = len([p for p in dynamic_processes]) if dynamic_processes else 0
        print(
            f"   ✓ Loaded {len(tc_params)} transfer coefficients ({static_count} static, {dynamic_count} dynamic)"
        )
    return tc_params


def load_dsm_parameters(excel_data, debug_mode=False):
    """Reads and parses DSM parameters from the '3_1_Definition_DSM' sheet.

    This function identifies DSM processes from the main process sheet and then
    parses their corresponding parameters from the DSM definition sheet. It can
    handle both the new parameter-based format and the legacy category-based format.

    Parameters
    ----------
    excel_data : dict
        Dictionary of DataFrames from the loaded Excel file.
    debug_mode : bool, optional
        If True, print detailed loading progress. Default is False.

    Returns
    -------
    dict
        A dictionary where keys are process IDs and values are dictionaries
        of the parsed DSM parameters for that process.
    """
    sheet_name = "3_1_Definition_DSM"
    main_sheet_name = "2_1_Definition_Processes"
    if debug_mode:
        print(f"--> Loading DSM parameters from sheet '{sheet_name}'...")

    if sheet_name not in excel_data:
        if debug_mode:
            print(
                f"--> INFO: Sheet '{sheet_name}' not found. Using empty DSM configuration."
            )
        return {}

    df_dsm = excel_data[sheet_name]
    if "Process_ID" not in df_dsm.columns:
        print(
            f"--> FATAL ERROR: Column 'Process_ID' not found in sheet '{sheet_name}'."
        )
        return {}

    # Get DSM process IDs from the main process sheet
    dsm_process_ids = []
    if main_sheet_name in excel_data:
        main_df = excel_data[main_sheet_name]
        if "Process_Logic" in main_df.columns:
            dsm_processes = main_df[main_df["Process_Logic"].isin(["DSM", "DSM_Component"])]
            dsm_process_ids = dsm_processes["Process_ID"].dropna().astype(int).tolist()
            if debug_mode:
                print(
                    f"--> Using Process_Logic column from main sheet to identify DSM processes: {dsm_process_ids}"
                )
        elif "DSM?" in main_df.columns:
            dsm_processes = main_df[main_df["DSM?"] == "Yes"]
            dsm_process_ids = dsm_processes["Process_ID"].dropna().astype(int).tolist()
            if debug_mode:
                print(
                    f"--> Using legacy DSM? column from main sheet to identify DSM processes: {dsm_process_ids}"
                )

    if not dsm_process_ids:
        if debug_mode:
            print("--> INFO: No DSM processes found in main sheet.")
        return {}

    # Filter DSM sheet data for identified DSM processes
    dsm_df = df_dsm[df_dsm["Process_ID"].isin(dsm_process_ids)].copy()
    if dsm_df.empty:
        if debug_mode:
            print("--> INFO: No DSM parameter data found for identified DSM processes.")
        return {}

    dsm_df = dsm_df.dropna(subset=["Process_ID"])
    dsm_df["Process_ID"] = dsm_df["Process_ID"].astype(int)

    dsm_params = {}

    for process_id in dsm_df["Process_ID"].unique():
        process_data = dsm_df[dsm_df["Process_ID"] == process_id]

        # Check if this is the new parameter-based format
        if (
            "DSM_Parameter_type" in process_data.columns
            and "DSM_Value" in process_data.columns
        ):
            dsm_params[process_id] = _parse_parameter_based_dsm(process_data)
        else:
            # Fall back to old category-based format
            dsm_params[process_id] = _parse_category_based_dsm(process_data)

        # Add Stock_Configuration to DSM params for initial stock handling
        if main_sheet_name in excel_data:
            process_row = main_df[main_df["Process_ID"] == process_id]
            if not process_row.empty:
                stock_config = str(
                    process_row.iloc[0].get("Stock_Configuration", "Stock")
                ).strip()
                dsm_params[process_id]["stock_configuration"] = stock_config

    # Merge component params from the optional "3_1_DSM_Components" sheet.
    # Each row: Process_ID, Element_Name, Mean_Lifetime, SpareOutflow_ID, SpareInflow_ID
    comp_sheet = excel_data.get("3_1_DSM_Components")
    if comp_sheet is not None and not comp_sheet.empty:
        required_cols = {"Process_ID", "Element_Name", "Mean_Lifetime", "SpareOutflow_ID", "SpareInflow_ID"}
        if required_cols.issubset(comp_sheet.columns):
            for _, row in comp_sheet.iterrows():
                pid = int(row["Process_ID"])
                if pid not in dsm_params:
                    continue
                dsm_params[pid].setdefault("components", []).append({
                    "element": str(row["Element_Name"]),
                    "mean_lifetime": float(row["Mean_Lifetime"]),
                    "sparepart_outflow": str(row["SpareOutflow_ID"]),
                    "sparepart_inflow": str(row["SpareInflow_ID"]),
                })
        else:
            print(f"--> WARNING: '3_1_DSM_Components' sheet missing required columns: {required_cols - set(comp_sheet.columns)}")

    if debug_mode:
        print(
            f"--> Successfully loaded configurations for {len(dsm_params)} DSM process(es)."
        )
    return dsm_params


def load_stock_parameters(excel_data):
    """Reads stock configuration from the main process definitions sheet.

    Identifies processes that require stock management based on the
    `Stock_Configuration` column.

    Parameters
    ----------
    excel_data : dict
        Dictionary of DataFrames from the loaded Excel file.

    Returns
    -------
    dict
        A dictionary of stock configurations, keyed by process ID.
    """
    main_sheet_name = "2_1_Definition_Processes"
    print(f"--> Loading Stock configuration from sheet '{main_sheet_name}'...")

    if main_sheet_name not in excel_data:
        print(
            f"--> INFO: Sheet '{main_sheet_name}' not found. Using empty stock configuration."
        )
        return {}

    main_df = excel_data[main_sheet_name]
    if "Process_ID" not in main_df.columns:
        print(
            f"--> FATAL ERROR: Column 'Process_ID' not found in sheet '{main_sheet_name}'."
        )
        return {}

    # Get stock configuration from Stock_Configuration column
    # Include all stock types: Stock and DSM initial stock variants
    stock_configs_with_stock = [
        "Stock",
        "Stock_with_InitialStock_Cohort",
        "Stock_with_InitialStock_Decay",
    ]
    stock_processes = main_df[
        main_df["Stock_Configuration"].isin(stock_configs_with_stock)
    ]
    stock_process_ids = stock_processes["Process_ID"].dropna().astype(int).tolist()

    print(
        f"--> Using Stock_Configuration column to identify stock processes: {stock_process_ids}"
    )

    if not stock_process_ids:
        print("--> INFO: No stock processes found.")
        return {}

    # Create stock configuration dictionary
    stock_config = {}
    for process_id in stock_process_ids:
        process_info = main_df[main_df["Process_ID"] == process_id].iloc[0]
        stock_config[process_id] = {
            "process_name": process_info.get("Process_Name", f"Process_{process_id}"),
            "process_logic": process_info.get("Process_Logic", "Unknown"),
            "stock_configuration": process_info.get("Stock_Configuration", "Stock"),
        }

    print(
        f"--> Successfully loaded stock configuration for {len(stock_config)} process(es)."
    )
    return stock_config


def _parse_fomp_parameters(process_data):
    """Parses FOMP parameters for a given process.

    Note
    ----
    This is currently a placeholder and needs to be implemented based on the
    specific requirements of the FOMP model.

    Parameters
    ----------
    process_data : pd.DataFrame
        The subset of the FOMP definition DataFrame for a single process.

    Returns
    -------
    dict
        A dictionary of the parsed FOMP parameters.
    """
    return {"process_type": "FOMP", "parameters": process_data.to_dict("records")}


def _parse_parameter_based_dsm(process_data):
    """Parses DSM parameters from the new parameter-based format.

    In this format, each row in the DataFrame represents a single parameter
    for a specific category within a DSM process.

    Parameters
    ----------
    process_data : pd.DataFrame
        The subset of the DSM definition DataFrame for a single process.

    Returns
    -------
    dict
        A dictionary of the parsed DSM parameters in the format expected by the engine.
    """
    categories = {}

    for _, row in process_data.iterrows():
        if pd.isna(row["DSM_Parameter_type"]) or pd.isna(row["DSM_Value"]):
            continue

        param_name = str(row["DSM_Parameter_type"])

        # Extract category number from parameter name
        if "_Cat_" in param_name:
            try:
                cat_num = int(param_name.split("_Cat_")[1])
                param_base = param_name.split("_Cat_")[0]

                if cat_num not in categories:
                    categories[cat_num] = {}

                # Map parameter to value
                categories[cat_num][param_base] = row["DSM_Value"]

            except (ValueError, IndexError):
                print(f"--> WARNING: Could not parse parameter name: {param_name}")
                continue
        else:
            # Handle format without _Cat_ pattern - group by category based on order
            # This assumes categories are grouped together in the data
            if "DSM_Category_Name" in param_name:
                # This is a category name row - start a new category
                category_name = str(row["DSM_Value"])
                if category_name not in categories:
                    categories[category_name] = {}
            else:
                # This is a parameter row - add to the current category
                # Find the most recent category (last one in the dict)
                if categories:
                    current_category = list(categories.keys())[-1]
                    categories[current_category][param_name] = row["DSM_Value"]

    if not categories:
        print(
            f"--> WARNING: No valid DSM parameters found for process {process_data['Process_ID'].iloc[0]}"
        )
        return {}

    # Convert to expected format
    sorted_categories = sorted(categories.items())

    # Extract basic parameters
    inflow_splits = []
    lifetime_types = []
    lifetime_means = []
    lifetime_stddevs = []
    lifetime_shapes = []
    lifetime_scales = []
    category_names = []
    output_splits = []
    output_flow_ids = set()

    for cat_key, cat_params in sorted_categories:
        # Basic parameters - ensure numeric conversion
        inflow_split = cat_params.get("DSM_Inflow_Split_[%]", 0)
        inflow_splits.append(float(inflow_split) if inflow_split is not None else 0.0)

        lifetime_types.append(cat_params.get("DSM_Lifetime_Type", "normal"))

        lifetime_mean = cat_params.get("DSM_Lifetime_Mean", 0)
        lifetime_means.append(
            float(lifetime_mean) if lifetime_mean is not None else 0.0
        )

        lifetime_stddev = cat_params.get("DSM_Lifetime_StdDev", 0)
        lifetime_stddevs.append(
            float(lifetime_stddev) if lifetime_stddev is not None else 0.0
        )

        raw_shape = cat_params.get("DSM_Lifetime_Shape")
        lifetime_shapes.append(
            float(raw_shape)
            if raw_shape is not None and str(raw_shape).strip() not in ("", "nan")
            else None
        )

        raw_scale = cat_params.get("DSM_Lifetime_Scale")
        lifetime_scales.append(
            float(raw_scale)
            if raw_scale is not None and str(raw_scale).strip() not in ("", "nan")
            else None
        )

        # Use category name if available, otherwise use the key
        if isinstance(cat_key, str) and cat_key != "DSM_Category_Name":
            category_names.append(cat_key)
        else:
            category_names.append(
                cat_params.get(
                    "DSM_Category_Name", f"Category_{len(category_names) + 1}"
                )
            )

        # Output parameters - collect all output flows and ensure numeric conversion
        cat_output_splits = []
        for key, value in cat_params.items():
            if key.startswith("DSM_Output_") and key.endswith("_Split_[%]"):
                # Ensure numeric conversion for output splits
                numeric_value = float(value) if value is not None else 0.0
                cat_output_splits.append(numeric_value)
            elif key.startswith("DSM_Output_") and key.endswith("_Flow_ID"):
                output_flow_ids.add(value)

        output_splits.append(cat_output_splits)

    # Convert output_flow_ids to sorted list
    output_flow_ids = sorted(list(output_flow_ids))

    # Validate DSM lifetime parameters and warn about potential issues
    process_id = process_data["Process_ID"].iloc[0]
    for i, (mean, stddev, cat_name) in enumerate(
        zip(lifetime_means, lifetime_stddevs, category_names)
    ):
        # Check for large standard deviation (> 80% of mean)
        if mean > 0 and stddev > 0.8 * mean:
            print(
                f"   ⚠️  WARNING: DSM Process {process_id}, Category '{cat_name}': "
                f"StdDev ({stddev:.2f}) > 80% of Mean ({mean:.2f})"
            )
            print(
                "      → Large standard deviation may cause negative lifetimes in normal distribution"
            )
            print(f"      → Consider reducing StdDev to max {0.8 * mean:.2f} years")

    return {
        "inflow_split": inflow_splits,
        "lifetimes": {
            "Type": lifetime_types,
            "Mean": lifetime_means,
            "StdDev": lifetime_stddevs,
            "Shape": lifetime_shapes,
            "Scale": lifetime_scales,
        },
        "category_names": category_names,
        "output_splits": output_splits,
        "output_flow_ids": output_flow_ids,
        "parameter_based": True,  # Flag to indicate this is parameter-based format
    }


def _parse_category_based_dsm(process_data):
    """Parses DSM parameters from the legacy category-based format.

    In this format, each row in the DataFrame represents a complete category
    with all its parameters.

    Parameters
    ----------
    process_data : pd.DataFrame
        The subset of the DSM definition DataFrame for a single process.

    Returns
    -------
    dict
        A dictionary of the parsed DSM parameters in the format expected by the engine.
    """
    # Sort by Category_ID if available
    if "Category_ID" in process_data.columns:
        process_data = process_data.sort_values(by="Category_ID")

    # Extract lifetime data for validation (sanitize None/NaN → 0.0)
    lifetime_means = [
        float(v) if v is not None and pd.notna(v) else 0.0
        for v in process_data["Lifetime_Mean"]
    ]
    lifetime_stddevs = [
        float(v) if v is not None and pd.notna(v) else 0.0
        for v in process_data["Lifetime_StdDev"]
    ]
    category_names = list(process_data["Category_Name"])

    # Optional Weibull-specific columns
    lifetime_shapes = [
        float(v) if pd.notna(v) else None
        for v in process_data.get(
            "Lifetime_Shape", pd.Series([None] * len(process_data))
        )
    ]
    lifetime_scales = [
        float(v) if pd.notna(v) else None
        for v in process_data.get(
            "Lifetime_Scale", pd.Series([None] * len(process_data))
        )
    ]

    # Validate DSM lifetime parameters and warn about potential issues
    process_id = process_data["Process_ID"].iloc[0]
    for i, (mean, stddev, cat_name) in enumerate(
        zip(lifetime_means, lifetime_stddevs, category_names)
    ):
        # Check for large standard deviation (> 80% of mean)
        if mean > 0 and stddev > 0.8 * mean:
            print(
                f"   ⚠️  WARNING: DSM Process {process_id}, Category '{cat_name}': "
                f"StdDev ({stddev:.2f}) > 80% of Mean ({mean:.2f})"
            )
            print(
                "      → Large standard deviation may cause negative lifetimes in normal distribution"
            )
            print(f"      → Consider reducing StdDev to max {0.8 * mean:.2f} years")

    return {
        "inflow_split": list(process_data["Inflow_Split_[%]"]),
        "lifetimes": {
            "Type": list(process_data["Lifetime_Type"]),
            "Mean": lifetime_means,
            "StdDev": lifetime_stddevs,
            "Shape": lifetime_shapes,
            "Scale": lifetime_scales,
        },
        "category_names": category_names,
        "parameter_based": False,  # Flag to indicate this is category-based format
    }


def load_fomp_parameters(excel_data, debug_mode=False):
    """Reads and parses FOMP parameters from the '3_2_Definition_FOMP' sheet.

    This function identifies FOMP processes and parses their parameters.
    It supports multiple legacy formats for backward compatibility, including
    systems based on `Process_ID`, `Pool_ID`, and the new `FOMP_Parameter_ID`.

    Parameters
    ----------
    excel_data : dict
        Dictionary of DataFrames from the loaded Excel file.
    debug_mode : bool, optional
        If True, print detailed loading progress. Default is False.

    Returns
    -------
    dict
        A dictionary where keys are process IDs and values are dictionaries
        of the parsed FOMP parameters for that process.
    """
    sheet_name = "3_2_Definition_FOMP"
    if debug_mode:
        print(f"--> Loading FOMP parameters from sheet '{sheet_name}'...")

    if sheet_name not in excel_data:
        if debug_mode:
            print(
                f"--> INFO: Sheet '{sheet_name}' not found. Using empty FOMP configuration."
            )
        return {}

    df_fomp = excel_data[sheet_name]
    fomp_params = {}

    for _, row in df_fomp.iterrows():
        # Handle both Process_ID and Pool_ID systems
        process_id = None
        param_name = None
        value = None

        # Check if using FOMP_Parameter_ID format (new system) - PRIORITY
        if "FOMP_Parameter_ID" in df_fomp.columns and pd.notna(
            row.get("FOMP_Parameter_ID")
        ):
            param_id = str(row["FOMP_Parameter_ID"])
            value = row["FOMP_Parameter_Value"]

            # Extract process ID from FOMP_Parameter_ID format (e.g., "P04_Inflow_fraction_f (Labile pool)" -> "04")
            try:
                if param_id.startswith("P") and "_" in param_id:
                    process_id = int(param_id[1:].split("_")[0])
                    # Extract parameter name by removing the process prefix
                    param_name = param_id.split("_", 1)[1]  # Remove "P04_" prefix
                else:
                    print(
                        f"⚠️ WARNING: Could not extract process ID from FOMP_Parameter_ID: {param_id}"
                    )
                    continue
            except (ValueError, IndexError):
                print(
                    f"⚠️ WARNING: Could not parse FOMP_Parameter_ID format: {param_id}"
                )
                continue

        # Check if using Pool_ID system (legacy approach)
        elif "Pool_ID" in df_fomp.columns and pd.notna(row.get("Pool_ID")):
            pool_id = str(row["Pool_ID"])
            param_name = row["Parameter_Name"]
            value = row["Value"]

            # Extract process ID from Pool_ID format (e.g., "P08_Inflow_fraction_f (Labile pool)" -> "08")
            try:
                if pool_id.startswith("P") and "_" in pool_id:
                    process_id = int(pool_id[1:].split("_")[0])
                else:
                    print(
                        f"⚠️ WARNING: Could not extract process ID from Pool_ID: {pool_id}"
                    )
                    continue
            except (ValueError, IndexError):
                print(f"⚠️ WARNING: Could not parse Pool_ID format: {pool_id}")
                continue

        # Check if using Process_ID system (legacy approach)
        elif "Process_ID" in df_fomp.columns and pd.notna(row.get("Process_ID")):
            process_id = int(row["Process_ID"])
            param_name = row.get("Parameter_Name", "")
            value = row.get("Value", "")

        # Check if using new FOMP column format (prefer FOMP_Parameter_type)
        elif "FOMP_Parameter_type" in df_fomp.columns and pd.notna(
            row.get("FOMP_Parameter_type")
        ):
            process_id = (
                int(row["Process_ID"]) if pd.notna(row.get("Process_ID")) else None
            )
            param_name = row["FOMP_Parameter_type"]
            value = row["FOMP_Parameter_Value"]

        else:
            continue

        # Initialize process dictionary if not exists
        if process_id not in fomp_params:
            fomp_params[process_id] = {}

        # Map parameter names to expected format
        if param_name == "output_carbon_id":
            fomp_params[process_id]["outflow_id"] = value
        elif param_name == "output_environmental_id":
            fomp_params[process_id]["outflow_id_2"] = value
        else:
            # Keep original parameter names for calculation
            try:
                fomp_params[process_id][param_name] = float(value)
            except (ValueError, TypeError):
                fomp_params[process_id][param_name] = value

    if debug_mode:
        print(
            f"--> Successfully loaded configurations for {len(fomp_params)} FOMP process(es)."
        )
        for process_id, params in fomp_params.items():
            print(f"   Process {process_id}: {len(params)} parameters")

    return fomp_params


def load_lfg_parameters(excel_data, debug_mode=False):
    """Reads and parses LFG parameters from the '3_3_Definition_LFG' sheet.

    The sheet uses a row-per-parameter layout (same pattern as FOMP) with
    columns ``LFG_Parameter_ID``, ``LFG_Parameter_type``, and
    ``LFG_Parameter_Value``.

    Fraction rows are identified by a ``_j{n}`` suffix in the
    ``LFG_Parameter_ID`` column (e.g. ``P01_k_j1``).  All rows sharing the
    same process and the same suffix index belong to one waste fraction.
    Site-level scalar parameters (MCF, DOCf, F_CH4, OX, output flow IDs)
    have no ``_j{n}`` suffix.

    The ``Process_ID`` column is used as the primary source for the numeric
    process identifier (avoids template bugs where output-ID rows carry a
    wrong process prefix in ``LFG_Parameter_ID``).

    Parameters
    ----------
    excel_data : dict
        Dictionary of DataFrames from the loaded Excel file.
    debug_mode : bool, optional
        If True, print detailed loading progress. Default is False.

    Returns
    -------
    dict
        ``{process_id: {
            "fractions": [{"name": str, "k_j": float, "DOC_j": float,
                           "f_input_j": float, "f_ash_j": float}, ...],
            "MCF": float, "DOCf": float, "F_CH4": float, "OX": float,
            "outflow_ch4_id": str, "outflow_co2_id": str,
            "outflow_leachate_id": str,
        }}``
    """
    import re

    sheet_name = "3_3_Definition_LFG"
    if debug_mode:
        print(f"--> Loading LFG parameters from sheet '{sheet_name}'...")

    if sheet_name not in excel_data:
        if debug_mode:
            print(
                f"--> INFO: Sheet '{sheet_name}' not found. Using empty LFG configuration."
            )
        return {}

    df_lfg = excel_data[sheet_name]

    if (
        "LFG_Parameter_type" not in df_lfg.columns
        or "LFG_Parameter_Value" not in df_lfg.columns
    ):
        if debug_mode:
            print(
                "   WARNING: Required columns 'LFG_Parameter_type' / "
                "'LFG_Parameter_Value' not found in sheet. Skipping LFG loading."
            )
        return {}

    # Map Excel parameter type strings → internal canonical names
    PARAM_MAP = {
        "F": "F_CH4",
        "F_CH4": "F_CH4",
        "Φ": "phi",
        "φ": "phi",
        "phi": "phi",
        "f": "f_capture",
        "output_CH4_id": "outflow_ch4_id",
        "output_CO2_id": "outflow_co2_id",
        "output_leaching": "outflow_leachate_id",
        "outflow_ch4_id": "outflow_ch4_id",
        "outflow_co2_id": "outflow_co2_id",
        "outflow_leachate_id": "outflow_leachate_id",
    }

    # Site-level scalar parameters (after PARAM_MAP normalisation)
    SITE_PARAMS = {
        "MCF",
        "DOCf",
        "F_CH4",
        "OX",
        "phi",
        "f_capture",
        "outflow_ch4_id",
        "outflow_co2_id",
        "outflow_leachate_id",
    }

    # Fraction-level parameter types as they appear in the Excel
    FRAC_PARAM_TYPES = {"Waste_Fraction_j", "f_input_j", "DOC_j", "k_j", "f_ash_j"}

    # Regex to extract fraction index from LFG_Parameter_ID, e.g. "P01_k_j2" → 2
    _j_pattern = re.compile(r"_j(\d+)\b", re.IGNORECASE)

    lfg_params = {}  # {process_id: {"fractions": [...], "MCF": ..., ...}}
    frac_staging = {}  # {process_id: {frac_index: {param_type: value}}}

    has_pid_col = "Process_ID" in df_lfg.columns
    has_id_col = "LFG_Parameter_ID" in df_lfg.columns

    for _, row in df_lfg.iterrows():
        param_type = row.get("LFG_Parameter_type")
        param_value = row.get("LFG_Parameter_Value")
        param_id = row.get("LFG_Parameter_ID") if has_id_col else None

        if pd.isna(param_type):
            continue
        param_type = str(param_type).strip()

        # Resolve process ID — prefer explicit Process_ID column
        process_id = None
        if has_pid_col and pd.notna(row.get("Process_ID")):
            try:
                process_id = int(row["Process_ID"])
            except (ValueError, TypeError):
                pass

        if process_id is None and pd.notna(param_id):
            pid_str = str(param_id).strip()
            if pid_str.startswith("P") and "_" in pid_str:
                try:
                    process_id = int(pid_str[1:].split("_")[0])
                except (ValueError, IndexError):
                    pass

        if process_id is None:
            continue

        # Initialise process dicts
        if process_id not in lfg_params:
            lfg_params[process_id] = {"fractions": []}
        if process_id not in frac_staging:
            frac_staging[process_id] = {}

        # Normalise parameter name
        internal_name = PARAM_MAP.get(param_type, param_type)

        # Try to extract fraction index from LFG_Parameter_ID
        frac_index = None
        if pd.notna(param_id):
            m = _j_pattern.search(str(param_id))
            if m:
                frac_index = int(m.group(1))

        if param_type in FRAC_PARAM_TYPES and frac_index is not None:
            # Fraction-level parameter — accumulate in staging dict
            if frac_index not in frac_staging[process_id]:
                frac_staging[process_id][frac_index] = {}
            frac_staging[process_id][frac_index][param_type] = param_value

        elif internal_name in SITE_PARAMS:
            # Site-level scalar
            if pd.isna(param_value):
                continue
            try:
                lfg_params[process_id][internal_name] = float(param_value)
            except (ValueError, TypeError):
                lfg_params[process_id][internal_name] = str(param_value).strip()

        else:
            if debug_mode:
                print(
                    f"   INFO: Skipping unrecognised LFG parameter "
                    f"'{param_type}' (process {process_id})"
                )

    # Assemble fraction dicts from staging
    for process_id, fracs in frac_staging.items():
        for frac_idx in sorted(fracs.keys()):
            fd = fracs[frac_idx]

            def _sf(key, default=0.0):
                v = fd.get(key)
                if v is None or (isinstance(v, float) and pd.isna(v)):
                    return default
                try:
                    return float(v)
                except (ValueError, TypeError):
                    return default

            frac = {
                "name": str(fd.get("Waste_Fraction_j", f"Fraction_{frac_idx}")).strip(),
                "k_j": _sf("k_j"),
                "DOC_j": _sf("DOC_j"),
                "f_input_j": _sf("f_input_j"),
                "f_ash_j": _sf("f_ash_j", default=0.0),
            }
            lfg_params[process_id]["fractions"].append(frac)

    if debug_mode:
        print(
            f"--> Successfully loaded configurations for {len(lfg_params)} LFG process(es)."
        )
        for process_id, params in lfg_params.items():
            n_frac = len(params.get("fractions", []))
            print(
                f"   Process {process_id}: {n_frac} fraction(s), "
                f"site params: MCF={params.get('MCF')}, DOCf={params.get('DOCf')}, "
                f"F_CH4={params.get('F_CH4')}, OX={params.get('OX')}"
            )

    return lfg_params


def load_bom_parameters(excel_data, elements, debug_mode=False):
    """Wrapper: delegates to bom_assembler.load_bom_parameters().

    Parameters
    ----------
    excel_data : dict
        Dictionary of DataFrames keyed by sheet name.
    elements : list of str
        Ordered element names matching mfa_system.Elements.
    debug_mode : bool, optional

    Returns
    -------
    dict
        Keys are process IDs; values are BOM configuration dicts.
        See engine.bom_assembler.load_bom_parameters() for details.
    """
    from engine import bom_assembler as _bom  # local import avoids circular dependency

    return _bom.load_bom_parameters(excel_data, elements, debug_mode=debug_mode)


def load_flow_cap_parameters(excel_data, debug_mode=False):
    """Wrapper: delegates to flow_cap.load_flow_cap_parameters().

    Parameters
    ----------
    excel_data : dict
        Dictionary of DataFrames keyed by sheet name.
    debug_mode : bool, optional

    Returns
    -------
    dict
        Keys are process IDs (int); values are FlowCap configuration dicts
        with keys: capped_flow_id, overflow_flow_id, cap_series {year: Mg},
        cap_tc_id (str | None).
        See engine.flow_cap.load_flow_cap_parameters() for details.
    """
    from engine import flow_cap as _flow_cap  # local import avoids circular dependency

    return _flow_cap.load_flow_cap_parameters(excel_data, debug_mode=debug_mode)


def register_flow_cap_parameters(mfa_system, flow_cap_params) -> None:
    """Register FlowCap cap time series in mfa_system.ParameterDict.

    Call once after define_flows_and_parameters() and before the solver.
    Only processes with a Cap_TC_ID defined in the FlowCap sheet are registered.
    This makes cap values visible to apply_scenario() for scenario switching.

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        Configured system; ParameterDict is modified in place.
    flow_cap_params : dict
        As returned by load_flow_cap_parameters().
    """
    from engine import flow_cap as _flow_cap

    _flow_cap.register_cap_parameters(mfa_system, flow_cap_params)


def load_uncertainty_definitions(excel_data, debug_mode=False):
    """Reads the '4_1_Uncertainty_Parameters' sheet into a dictionary.

    Parses the sheet to create a dictionary of uncertainty parameter definitions
    formatted for use in the Monte Carlo simulation engine.

    Parameters
    ----------
    excel_data : dict
        Dictionary of DataFrames from the loaded Excel file.
    debug_mode : bool, optional
        If True, print detailed loading progress. Default is False.

    Returns
    -------
    dict
        A dictionary of uncertainty definitions, keyed by parameter name.
    """
    sheet_name = "4_1_Uncertainty_Parameters"
    if debug_mode:
        print(f"--> Loading uncertainty definitions from sheet '{sheet_name}'...")

    if sheet_name not in excel_data:
        if debug_mode:
            print(
                f"--> INFO: Sheet '{sheet_name}' not found. No uncertainties will be loaded."
            )
        return {}

    df_uncertainty = excel_data[sheet_name]
    if debug_mode:
        print(f"  DEBUG: df_uncertainty before dropna:\n{df_uncertainty}")

    # Support both new column names (MC_Parameter_ID) and legacy (Parameter_Name)
    id_col = (
        "MC_Parameter_ID"
        if "MC_Parameter_ID" in df_uncertainty.columns
        else "Parameter_Name"
    )
    df_uncertainty = df_uncertainty.dropna(subset=[id_col])

    # Filter by MC_Parameter_Selection toggle — skip rows where it is empty/NaN
    sel_col = "MC_Parameter_Selection"
    if sel_col in df_uncertainty.columns:
        df_uncertainty = df_uncertainty[
            df_uncertainty[sel_col].notna()
            & (df_uncertainty[sel_col].astype(str).str.strip() != "")
        ]

    if debug_mode:
        print(
            f"  DEBUG: df_uncertainty after filtering (rows: {len(df_uncertainty)}):\n{df_uncertainty}"
        )
    uncertainty_params = {}
    _seen_names: dict = {}  # tracks how many times each F_ name has appeared

    for _, row in df_uncertainty.iterrows():
        param_name = str(row[id_col]).strip()
        dist_type = row["Distribution_Type"].lower()
        definition = {"distribution": dist_type}

        if dist_type == "uniform":
            if pd.notna(row["Min"]) and pd.notna(row["Max"]):
                definition["min"] = row["Min"]
                definition["max"] = row["Max"]
        elif dist_type == "normal":
            if pd.notna(row["Mean"]) and pd.notna(row["StdDev"]):
                definition["mean"] = row["Mean"]
                definition["std"] = row["StdDev"]
                if pd.notna(row.get("Min")):
                    definition["min"] = row["Min"]
                if pd.notna(row.get("Max")):
                    definition["max"] = row["Max"]
        elif dist_type == "triangular":
            if pd.notna(row["Min"]) and pd.notna(row["Mode"]) and pd.notna(row["Max"]):
                definition["min"] = row["Min"]
                definition["mode"] = row["Mode"]
                definition["max"] = row["Max"]
        elif dist_type == "lognormal":
            if pd.notna(row["Mean"]) and pd.notna(row["StdDev"]):
                definition["mean"] = row["Mean"]
                definition["std"] = row["StdDev"]
                if pd.notna(row.get("Min")):
                    definition["min"] = row["Min"]
                if pd.notna(row.get("Max")):
                    definition["max"] = row["Max"]
        else:
            print(
                f"⚠️ WARNING: Unknown distribution type '{dist_type}' for parameter '{param_name}' — skipping."
            )

        # --- Optional modifier columns (new names preferred, legacy fallback) ---
        op_col = (
            "MC_Operation" if "MC_Operation" in df_uncertainty.columns else "Operation"
        )
        raw_op = row.get(op_col)
        if raw_op is not None and pd.notna(raw_op) and str(raw_op).strip():
            definition["operation"] = str(raw_op).strip().lower()

        start_col = (
            "MC_Start_Year"
            if "MC_Start_Year" in df_uncertainty.columns
            else "start_year"
        )
        raw_start = row.get(start_col)
        if raw_start is not None and pd.notna(raw_start):
            try:
                definition["start_year"] = int(raw_start)
            except (ValueError, TypeError):
                print(
                    f"⚠️ WARNING: Invalid {start_col} '{raw_start}' for '{param_name}' — ignoring."
                )

        end_col = (
            "MC_End_Year" if "MC_End_Year" in df_uncertainty.columns else "end_year"
        )
        raw_end = row.get(end_col)
        if raw_end is not None and pd.notna(raw_end):
            try:
                definition["end_year"] = int(raw_end)
            except (ValueError, TypeError):
                print(
                    f"⚠️ WARNING: Invalid {end_col} '{raw_end}' for '{param_name}' — ignoring."
                )

        raw_group = row.get("MC_Flow_Group")
        if raw_group is not None and pd.notna(raw_group) and str(raw_group).strip():
            definition["flow_group"] = str(raw_group).strip()

        if len(definition) > 1:
            if param_name.startswith("F_"):
                definition["flow_id"] = (
                    param_name  # real flow name, preserved before any renaming
                )
                count = _seen_names.get(param_name, 0)
                _seen_names[param_name] = count + 1
                if count > 0:
                    param_name = f"{param_name}::{count}"
            uncertainty_params[param_name] = definition

    if debug_mode:
        print(
            f"--> Successfully loaded {len(uncertainty_params)} uncertainty parameter definition(s)."
        )
    return uncertainty_params


def apply_fomp_uncertainty_updates(fomp_params, uncertainty_updates):
    """Applies sampled uncertainty values to FOMP parameters.

    This function is used during Monte Carlo simulations to update the FOMP
    parameters with values sampled from the defined uncertainty distributions.
    It handles process-specific parameter names (e.g., 'P04_decay_k1').

    Parameters
    ----------
    fomp_params : dict
        The original FOMP parameters dictionary.
    uncertainty_updates : dict
        A dictionary of sampled parameter values from a Monte Carlo iteration.

    Returns
    -------
    dict
        A new dictionary of FOMP parameters with the uncertainty updates applied.
    """
    updated_fomp_params = deepcopy(fomp_params)

    for param_name, sampled_value in uncertainty_updates.items():
        # Check if this is a process-specific FOMP parameter (starts with 'P' and contains '_decay_')
        if param_name.startswith("P") and "_decay_" in param_name:
            try:
                # Extract process ID and original parameter name
                # Format: P7_decay_k1 (Labile pool) -> process_id=7, original_name=decay_k1 (Labile pool)
                parts = param_name.split("_", 1)  # Split on first underscore only
                if len(parts) == 2:
                    process_id_str = parts[0][1:]  # Remove 'P' prefix
                    original_param_name = parts[1]  # Everything after P7_

                    process_id = int(process_id_str)

                    # Apply the update if this process exists in FOMP params
                    if process_id in updated_fomp_params:
                        updated_fomp_params[process_id][original_param_name] = (
                            sampled_value
                        )
                        print(
                            f"  Applied uncertainty: {param_name} = {sampled_value:.4f} to Process {process_id}"
                        )
                    else:
                        print(
                            f"  WARNING: Process {process_id} not found in FOMP parameters for {param_name}"
                        )

            except (ValueError, IndexError) as e:
                print(
                    f"  WARNING: Could not parse process-specific parameter {param_name}: {e}"
                )

    return updated_fomp_params


def load_scenario_definitions(excel_data):
    """Reads and parses scenario definitions from the scenario manager sheet.

    This function looks for '5_1_Scenario_Manager' or 'Scenario Manager' and
    parses the rules for each defined scenario into a structured dictionary.

    Parameters
    ----------
    excel_data : dict
        Dictionary of DataFrames from the loaded Excel file.

    Returns
    -------
    dict
        A dictionary where keys are scenario names and values are lists of
        the modification rules for that scenario.
    """
    sheet_name = None
    if "5_1_Scenario_Manager" in excel_data:
        sheet_name = "5_1_Scenario_Manager"
    elif "Scenario Manager" in excel_data:
        sheet_name = "Scenario Manager"

    print(f"--> Loading scenario definitions from sheet '{sheet_name}'...")

    if not sheet_name or excel_data[sheet_name].empty:
        print("--> INFO: Scenario sheet not found or is empty. No scenarios loaded.")
        return {}

    df = excel_data[sheet_name]

    header_row = 0
    found = False
    for i in range(min(10, len(df))):
        if "Scenario_Name" in df.iloc[i].values:
            header_row = i
            found = True
            break

    if found:
        df.columns = df.iloc[header_row]
        df = df.iloc[header_row + 1 :].reset_index(drop=True)

    # Normalise column name aliases so apply_scenario always sees consistent keys
    col_aliases = {
        "Parameter_ID": "Parameter_Name",  # user column → internal name
        "Scenario_Operation": "Operation",
    }
    df = df.rename(
        columns={src: dst for src, dst in col_aliases.items() if src in df.columns}
    )

    try:
        df_scenarios = df.dropna(subset=["Scenario_Name", "Parameter_Name"])
    except KeyError:
        print(
            f"--> ERROR: Could not find 'Scenario_Name' or 'Parameter_Name'/'Parameter_ID' columns in sheet '{sheet_name}'."
        )
        return {}

    scenario_definitions = {}
    for scenario_name, group in df_scenarios.groupby("Scenario_Name"):
        for record in group.to_dict("records"):
            if "ID" in record and pd.notna(record["ID"]):
                record["ID"] = int(record["ID"])

            # Handle year range columns
            if "start_year" in record and pd.notna(record["start_year"]):
                record["start_year"] = int(record["start_year"])
            else:
                record["start_year"] = None

            if "end_year" in record and pd.notna(record["end_year"]):
                record["end_year"] = int(record["end_year"])
            else:
                record["end_year"] = None

        scenario_definitions[scenario_name] = group.to_dict("records")

    print(f"--> Successfully loaded {len(scenario_definitions)} scenario(s).")
    return scenario_definitions


def load_yaml_config(yaml_path: str) -> dict:
    """Load a BioDYM web-app config YAML file and return the raw dict.

    Parameters
    ----------
    yaml_path : str
        Path to the ``config.yaml`` produced by the BioDYM config web app
        (e.g. ``"case_studies/wheat_straw/config.yaml"``).

    Returns
    -------
    dict
        Full parsed YAML contents.
    """
    import yaml as _yaml

    with open(yaml_path, encoding="utf-8") as fh:
        return _yaml.safe_load(fh) or {}


def load_uncertainty_definitions_from_yaml(yaml_path: str) -> dict:
    """Load MC uncertainty definitions from a web-app config YAML.

    Drop-in replacement for :func:`load_uncertainty_definitions` when
    scenarios and MC parameters are managed in the config web app instead
    of (or in addition to) the Excel sheet ``4_1_Uncertainty_Parameters``.

    Only rows with ``enabled: true`` are included.

    Parameters
    ----------
    yaml_path : str
        Path to the ``config.yaml`` produced by the BioDYM config web app.

    Returns
    -------
    dict
        Same structure as :func:`load_uncertainty_definitions`:
        ``{parameter_id: {"distribution": str, "mean": float, ...}}``.
    """
    data = load_yaml_config(yaml_path)
    mc_list = data.get("mc_parameters", [])

    uncertainty_params: dict = {}
    for p in mc_list:
        if not p.get("enabled", True):
            continue
        pid = str(p.get("parameter_id", "")).strip()
        if not pid:
            continue

        dist = str(p.get("distribution", "normal")).lower()
        defn: dict = {"distribution": dist}

        for field in ("mean", "std", "min", "max", "mode"):
            val = p.get(field)
            if val is not None:
                defn[field] = float(val)

        op = str(p.get("operation", "replace") or "replace").lower()
        if op:
            defn["operation"] = op

        for year_field in ("start_year", "end_year"):
            val = p.get(year_field)
            if val is not None:
                defn[year_field] = int(val)

        fg = p.get("flow_group")
        if fg:
            defn["flow_group"] = str(fg)

        if pid.startswith("F_"):
            defn["flow_id"] = pid

        if len(defn) > 1:
            uncertainty_params[pid] = defn

    print(
        f"   ✓ Loaded {len(uncertainty_params)} MC uncertainty parameter(s) from YAML."
    )
    return uncertainty_params


def load_scenario_definitions_from_yaml(yaml_path: str) -> dict:
    """Load scenario definitions from a web-app config YAML.

    Drop-in replacement for :func:`load_scenario_definitions` when
    scenarios are managed in the config web app instead of (or in addition
    to) the Excel sheet ``5_1_Scenario_Manager``.

    Parameters
    ----------
    yaml_path : str
        Path to the ``config.yaml`` produced by the BioDYM config web app.

    Returns
    -------
    dict
        Same structure as :func:`load_scenario_definitions`:
        ``{scenario_name: [{"Parameter_Name": str, "Operation": str,
        "New_Value": float, "start_year": int|None, "end_year": int|None}]}``.
    """
    data = load_yaml_config(yaml_path)
    scenario_list = data.get("scenarios", [])

    scenario_definitions: dict = {}
    for s in scenario_list:
        sname = str(s.get("name", "")).strip()
        if not sname:
            continue
        records = []
        for m in s.get("modifications", []):
            pname = str(m.get("parameter_name", "")).strip()
            if not pname:
                continue
            records.append(
                {
                    "Parameter_Name": pname,
                    "Operation": str(m.get("operation", "replace") or "replace"),
                    "New_Value": float(m.get("new_value") or 0.0),
                    "start_year": m.get("start_year"),
                    "end_year": m.get("end_year"),
                    "parameter_type": str(m.get("parameter_type", "") or ""),
                }
            )
        scenario_definitions[sname] = records

    print(f"   ✓ Loaded {len(scenario_definitions)} scenario definition(s) from YAML.")
    return scenario_definitions


def load_fomp_from_yaml(yaml_path: str) -> dict:
    """Load FOMP parameters from a web-app config YAML.

    Drop-in replacement for :func:`load_fomp_parameters` when FOMP process
    params are managed in the config web app.  The dict uses the internal
    Excel-style key names expected by ``fomp_model.calculate_fomp()``.

    Parameters
    ----------
    yaml_path : str
        Path to the ``config.yaml`` produced by the BioDYM config web app.

    Returns
    -------
    dict
        ``{process_id: {"Inflow_fraction_f (Labile pool)": float, ...}}``
    """
    data = load_yaml_config(yaml_path)
    fomp_params: dict = {}
    for proc in data.get("processes", []):
        fomp = proc.get("fomp")
        if not fomp:
            continue
        pid = int(proc["id"])
        outflow_2 = str(fomp.get("outflow_id_2", "") or "").strip() or None
        fomp_params[pid] = {
            "Inflow_fraction_f (Labile pool)": float(fomp.get("f_labile", 0.5)),
            "decay_k1 (Labile pool)": float(fomp.get("k_labile", 1.0)),
            "decay_k2 (Recalcitrant pool)": float(fomp.get("k_recalcitrant", 0.01)),
            "outflow_id": str(fomp.get("outflow_id", "")),
            "outflow_id_2": outflow_2,
        }
    print(f"   ✓ Loaded {len(fomp_params)} FOMP process config(s) from YAML.")
    return fomp_params


def load_dsm_from_yaml(yaml_path: str) -> dict:
    """Load DSM parameters from a web-app config YAML.

    Drop-in replacement for :func:`load_dsm_parameters` (single-category only).
    ``stock_configuration`` is read from the process ``stock`` field.

    Parameters
    ----------
    yaml_path : str
        Path to the ``config.yaml`` produced by the BioDYM config web app.

    Returns
    -------
    dict
        ``{process_id: {"inflow_split": [...], "lifetimes": {...}, ...}}``
    """
    data = load_yaml_config(yaml_path)
    dsm_params: dict = {}
    for proc in data.get("processes", []):
        dsm = proc.get("dsm")
        if not dsm:
            continue
        pid = int(proc["id"])
        stock_config = str(proc.get("stock", "Stock"))
        cats = dsm.get("categories", [])
        if not cats:
            # Legacy single-category flat format
            cats = [
                {
                    "name": "Default",
                    "inflow_split": 1.0,
                    "lifetime_type": dsm.get("lifetime_distribution", "Normal"),
                    "lifetime_mean": dsm.get("lifetime_mean"),
                    "lifetime_std": dsm.get("lifetime_std"),
                    "lifetime_shape": None,
                    "lifetime_scale": None,
                }
            ]
        inflow_splits, types, means, stds, shapes, scales, names = (
            [],
            [],
            [],
            [],
            [],
            [],
            [],
        )
        for cat in cats:
            inflow_splits.append(float(cat.get("inflow_split", 1.0)))
            lt = str(cat.get("lifetime_type", "Normal"))
            types.append(lt)
            names.append(str(cat.get("name", "Default")))
            means.append(
                float(cat["lifetime_mean"])
                if cat.get("lifetime_mean") is not None
                else 0.0
            )
            stds.append(
                float(cat["lifetime_std"])
                if cat.get("lifetime_std") is not None
                else 0.0
            )
            shapes.append(
                float(cat["lifetime_shape"])
                if cat.get("lifetime_shape") is not None
                else None
            )
            scales.append(
                float(cat["lifetime_scale"])
                if cat.get("lifetime_scale") is not None
                else None
            )
        dsm_params[pid] = {
            "inflow_split": inflow_splits,
            "lifetimes": {
                "Type": types,
                "Mean": means,
                "StdDev": stds,
                "Shape": shapes,
                "Scale": scales,
            },
            "category_names": names,
            "output_splits": [[] for _ in cats],
            "output_flow_ids": [],
            "parameter_based": False,
            "stock_configuration": stock_config,
        }
    print(f"   ✓ Loaded {len(dsm_params)} DSM process config(s) from YAML.")
    return dsm_params


def load_lfg_from_yaml(yaml_path: str) -> dict:
    """Load LFG parameters from a web-app config YAML.

    Drop-in replacement for :func:`load_lfg_parameters`.

    Parameters
    ----------
    yaml_path : str
        Path to the ``config.yaml`` produced by the BioDYM config web app.

    Returns
    -------
    dict
        ``{process_id: {"fractions": [...], "MCF": float, "DOCf": float, ...}}``
    """
    data = load_yaml_config(yaml_path)
    lfg_params: dict = {}
    for proc in data.get("processes", []):
        lfg = proc.get("lfg")
        if not lfg:
            continue
        pid = int(proc["id"])
        fractions = []
        for frac in lfg.get("fractions", []):
            fractions.append(
                {
                    "name": str(frac.get("name", "")),
                    "k_j": float(frac.get("k_j", 0.1)),
                    "DOC_j": float(frac.get("doc_j", 0.5)),
                    "f_input_j": float(frac.get("f_input_j", 1.0)),
                    "f_ash_j": float(frac.get("f_ash_j", 0.05)),
                }
            )
        lfg_params[pid] = {
            "fractions": fractions,
            "MCF": float(lfg.get("mcf", 1.0)),
            "DOCf": float(lfg.get("doc_f", 0.5)),
            "F_CH4": float(lfg.get("f_ch4", 0.5)),
            "OX": float(lfg.get("ox", 0.1)),
            "phi": float(lfg.get("phi", 1.0)),
            "f_capture": float(lfg.get("f_capture", 0.0)),
            "outflow_ch4_id": str(lfg.get("outflow_ch4_id", "")),
            "outflow_co2_id": str(lfg.get("outflow_co2_id", "")),
            "outflow_leachate_id": str(lfg.get("outflow_leachate_id", "")),
        }
    print(f"   ✓ Loaded {len(lfg_params)} LFG process config(s) from YAML.")
    return lfg_params


def load_flow_cap_from_yaml(yaml_path: str) -> dict:
    """Load FlowCap parameters from a web-app config YAML.

    Drop-in replacement for :func:`load_flow_cap_parameters`.

    Parameters
    ----------
    yaml_path : str
        Path to the ``config.yaml`` produced by the BioDYM config web app.

    Returns
    -------
    dict
        ``{process_id: {"capped_flow_id": str, "cap_series": {year: float}, ...}}``
    """
    data = load_yaml_config(yaml_path)
    flow_cap_params: dict = {}
    for proc in data.get("processes", []):
        fc = proc.get("flowcap")
        if not fc:
            continue
        pid = int(proc["id"])
        cap_series = {int(y): float(v) for y, v in fc.get("cap_series", {}).items()}
        overflow_id = str(fc.get("overflow_flow_id", "") or "").strip() or None
        cap_tc_id = str(fc.get("cap_tc_id", "") or "").strip() or None
        flow_cap_params[pid] = {
            "capped_flow_id": str(fc.get("capped_flow_id", "")),
            "overflow_flow_id": overflow_id,
            "cap_series": cap_series,
            "cap_tc_id": cap_tc_id,
        }
    print(f"   ✓ Loaded {len(flow_cap_params)} FlowCap config(s) from YAML.")
    return flow_cap_params


def load_flow_data_df_from_yaml(yaml_path: str):
    """Load flow time-series data from a web-app config YAML as a DataFrame.

    Returns a DataFrame in the format of the ``1_2_Data_Flows`` Excel sheet
    so it can be injected into ``all_excel_data`` before calling
    ``define_flows_and_parameters()``.

    Columns: ``Flow_ID``, ``Flow_Data_Year``, ``E1_value`` (material element).

    Parameters
    ----------
    yaml_path : str
        Path to the ``config.yaml`` produced by the BioDYM config web app.

    Returns
    -------
    pd.DataFrame
        Rows sorted by Flow_ID then year.  Empty DataFrame if no flow_data.
    """
    data = load_yaml_config(yaml_path)
    rows = []
    for entry in data.get("flow_data", []):
        fid = str(entry.get("flow_id", "")).strip()
        elem = str(entry.get("element", "material"))
        if elem != "material" or not fid:
            continue
        for year_raw, val in entry.get("values", {}).items():
            rows.append(
                {
                    "Flow_ID": fid,
                    "Flow_Data_Year": int(year_raw),
                    "E1_value": float(val),
                }
            )
    if not rows:
        return pd.DataFrame(columns=["Flow_ID", "Flow_Data_Year", "E1_value"])
    df = (
        pd.DataFrame(rows)
        .sort_values(["Flow_ID", "Flow_Data_Year"])
        .reset_index(drop=True)
    )
    print(
        f"   ✓ Loaded {len(df)} flow data point(s) for {df['Flow_ID'].nunique()} flow(s) from YAML."
    )
    return df


def yaml_to_excel_dataframes(yaml_path: str) -> dict:
    """Convert a BioDYM web-app config YAML into Excel-format DataFrames.

    Returns a dict keyed by sheet name (same keys as ``pd.read_excel`` with
    ``sheet_name=None``).  Pass this dict as ``input_data`` to
    ``system_setup.load_and_define_processes`` to run the engine without an
    Excel file.

    Parameters
    ----------
    yaml_path : str
        Path to the ``config.yaml`` produced by the BioDYM config web app.

    Returns
    -------
    dict[str, pd.DataFrame]
        Sheet-name → DataFrame mapping for all sheets the engine consumes.
    """
    data = load_yaml_config(yaml_path)

    model = data.get("model") or {}
    elements = model.get("elements", ["material", "WC", "DM", "TC"])
    processes = data.get("processes", [])
    flows = data.get("flows", [])
    tcs = data.get("transfer_coefficients", [])
    compositions = data.get("flow_compositions", [])
    hierarchy = data.get("element_hierarchy", [])

    # Build lookup: flow_id → flow dict
    flow_map = {f["id"]: f for f in flows}

    # Build lookup: flow_id → {element: fraction}
    comp_map: dict[str, dict] = {}
    for fc in compositions:
        comp_map[fc.get("flow_id", "")] = fc.get("values", {})

    # Build lookup: child_element → parent_element
    child_to_parent: dict[str, str] = {}
    for rule in hierarchy:
        parent = rule.get("parent", "")
        for child in rule.get("children", []):
            child_to_parent[child] = parent

    result: dict[str, pd.DataFrame] = {}

    # ── 0_Configuration ──────────────────────────────────────────────────────
    # system_setup reads this via row.iloc[1] (key) and row.iloc[2] (value),
    # so we need 3 columns (col0 is a label column, col1=key, col2=value).
    elem_idx_map = {e: i + 1 for i, e in enumerate(elements)}
    cfg_rows = []
    cfg_rows.append(
        {"_lbl": "", "_key": "Start_Year", "_val": model.get("start_year", 2025)}
    )
    cfg_rows.append(
        {"_lbl": "", "_key": "End_Year", "_val": model.get("end_year", 2125)}
    )
    for i, elem in enumerate(elements, 1):
        cfg_rows.append({"_lbl": "", "_key": f"Element_ID_{i}", "_val": elem})
    for child, parent in child_to_parent.items():
        if child in elem_idx_map:
            cfg_rows.append(
                {
                    "_lbl": "",
                    "_key": f"Parent_Element_ID_{elem_idx_map[child]}",
                    "_val": parent,
                }
            )
    result["0_Configuration"] = pd.DataFrame(cfg_rows)

    # ── 2_1_Definition_Processes ─────────────────────────────────────────────
    # system_setup uses "ID"; data_loader/load_tc_parameters uses "Process_ID"
    proc_rows = []
    for p in processes:
        pid = p.get("id")
        logic = p.get("logic", "Splitter")
        stock = p.get("stock", "No_Stock")
        tc_cfg = p.get("tc_config", "No TC")
        # "No TC" → NaN (engine skips TC loading for such processes)
        tc_cfg_val = tc_cfg if tc_cfg in ("Static", "Dynamic") else None
        proc_rows.append(
            {
                "ID": pid,
                "Process_ID": pid,  # alias for load_tc_parameters
                "Process_Name": p.get("name", f"P{pid}"),
                "Process_Logic": logic,
                "Stock_Configuration": stock,
                "TC_Configuration": tc_cfg_val,
            }
        )
    result["2_1_Definition_Processes"] = pd.DataFrame(proc_rows)

    # ── 1_1_Definition_Flows ─────────────────────────────────────────────────
    # Composition columns: Flow_E{n}_Fraction[%]  (n = 1-based element index)
    flow_rows = []
    for fl in flows:
        fid = fl.get("id", "")
        comp = comp_map.get(fid, {})
        row = {
            "Flow_ID": fid,
            "Flow_Name": fl.get("name", fid),
            "Flow_Output_Process_ID": fl.get("from_process"),
            "Input_Process_ID": fl.get("to_process"),
        }
        for idx, elem in enumerate(elements):
            n = idx + 1  # 1-based
            row[f"Flow_E{n}_Fraction[%]"] = comp.get(elem)
        flow_rows.append(row)
    result["1_1_Definition_Flows"] = (
        pd.DataFrame(flow_rows) if flow_rows else pd.DataFrame()
    )

    # ── 2_2_static_TCs ───────────────────────────────────────────────────────
    # New E# format: E{n}_TC_ID, E{n}_TC_Value[%]
    # TC ID convention (matches the BioDYM Excel template): every element,
    # including material (E1), uses TC_E{n}_{from:02d}_{to:02d}.
    static_rows = []
    for tc in tcs:
        if tc.get("tc_type", "static") != "static":
            continue
        pid = tc.get("process_id")
        fid = tc.get("flow_id", "")
        values = tc.get("values", {})
        if not values:
            continue
        fl = flow_map.get(fid, {})
        from_p = fl.get("from_process", 0)
        to_p = fl.get("to_process", 0)
        row = {"Process_ID": pid, "Flow_ID": fid}
        for idx, elem in enumerate(elements):
            n = idx + 1
            # BioDYM convention: every element (incl. material, E1) → TC_E{n}_{from}_{to}
            tc_id = f"TC_E{n}_{from_p:02d}_{to_p:02d}"
            val = values.get(elem)
            row[f"E{n}_TC_ID"] = tc_id if val is not None else None
            row[f"E{n}_TC_Value[%]"] = val
        static_rows.append(row)
    # Empty sheet must still carry the required columns so validate_input_data
    # passes (e.g. a model with only dynamic TCs).
    _tc_cols = ["Process_ID", "Flow_ID"]
    for _i in range(len(elements)):
        _tc_cols += [f"E{_i + 1}_TC_ID", f"E{_i + 1}_TC_Value[%]"]
    result["2_2_static_TCs"] = (
        pd.DataFrame(static_rows) if static_rows else pd.DataFrame(columns=_tc_cols)
    )

    # ── 2_3_dynamic_TCs ──────────────────────────────────────────────────────
    dyn_rows = []
    for tc in tcs:
        if tc.get("tc_type") != "dynamic":
            continue
        pid = tc.get("process_id")
        fid = tc.get("flow_id", "")
        fl = flow_map.get(fid, {})
        from_p = fl.get("from_process", 0)
        to_p = fl.get("to_process", 0)
        for point in tc.get("time_series", []):
            year = point.get("year")
            values = point.get("values", {})
            row = {"Process_ID": pid, "Flow_ID": fid, "Year": year}
            for idx, elem in enumerate(elements):
                n = idx + 1
                tc_id = (
                    f"TC_{from_p:02d}_{to_p:02d}"
                    if elem == "material"
                    else f"TC_E{n}_{from_p:02d}_{to_p:02d}"
                )
                val = values.get(elem)
                row[f"E{n}_TC_ID"] = tc_id if val is not None else None
                row[f"E{n}_TC_Value[%]"] = val
            dyn_rows.append(row)
    _dyn_cols = ["Process_ID", "Flow_ID", "Year"]
    for _i in range(len(elements)):
        _dyn_cols += [f"E{_i + 1}_TC_ID", f"E{_i + 1}_TC_Value[%]"]
    result["2_3_dynamic_TCs"] = (
        pd.DataFrame(dyn_rows) if dyn_rows else pd.DataFrame(columns=_dyn_cols)
    )

    # ── 1_2_Data_Flows ───────────────────────────────────────────────────────
    result["1_2_Data_Flows"] = load_flow_data_df_from_yaml(yaml_path)

    # ── 2_4_Initial_Stock ──────────────────────────────────────────────────────
    # Tall format: one row per (process, parameter). The initial-stock engine
    # reads Basic_Material_Quantity[UoM], Basic_E{n}_Fraction[%] (absolute, of
    # material), and the Cohort_* params. Material (n=1) is the total, not a
    # fraction.
    is_rows = []
    for entry in data.get("initial_stocks", []):
        pid = entry.get("process_id")
        if pid is None:
            continue

        def _is_row(ptype, value):
            is_rows.append(
                {
                    "Process_ID": pid,
                    "IS_Parameter_type": ptype,
                    "IS_Parameter_Value": value,
                }
            )

        _is_row("Basic_Material_Quantity[UoM]", entry.get("material_quantity", 0.0))
        comp = entry.get("composition", {})
        for idx, elem in enumerate(elements):
            if elem == "material":
                continue
            if elem in comp:
                _is_row(f"Basic_E{idx + 1}_Fraction[%]", comp[elem])
        if entry.get("cohort_age_distribution_type"):
            _is_row(
                "Cohort_Age_Distribution_Type", entry["cohort_age_distribution_type"]
            )
        if entry.get("cohort_mean_age") is not None:
            _is_row("Cohort_Mean_Age[years]", entry["cohort_mean_age"])
        if entry.get("cohort_std_age") is not None:
            _is_row("Cohort_StdDev_Age[years]", entry["cohort_std_age"])
        if entry.get("cohort_max_age") is not None:
            _is_row("Cohort_Max_Age[years]", entry["cohort_max_age"])
        if entry.get("cohort_decay_constant") is not None:
            _is_row("Cohort_Decay_Constant[years]", entry["cohort_decay_constant"])
    result["2_4_Initial_Stock"] = (
        pd.DataFrame(is_rows)
        if is_rows
        else pd.DataFrame(
            columns=["Process_ID", "IS_Parameter_type", "IS_Parameter_Value"]
        )
    )

    # ── Empty placeholder sheets ─────────────────────────────────────────────
    # Must include required column names so validate_input_data passes even
    # though there are zero rows (feature disabled in YAML-only mode).
    # ── 3_2_Definition_FOMP ────────────────────────────────────────────────────
    # Process_ID / Parameter_Name / Value rows (load_fomp_parameters legacy format).
    # The engine model reads keys f_labile / k_labile / k_recalcitrant; outflow IDs
    # map via output_carbon_id → outflow_id, output_environmental_id → outflow_id_2.
    fomp_rows = []
    for p in processes:
        if p.get("logic") != "FOMP":
            continue
        fomp = p.get("fomp") or {}
        pid = p.get("id")

        def _fr(pname, val):
            fomp_rows.append({"Process_ID": pid, "Parameter_Name": pname, "Value": val})

        _fr("f_labile", fomp.get("f_labile", 0.5))
        _fr("k_labile", fomp.get("k_labile", 1.0))
        _fr("k_recalcitrant", fomp.get("k_recalcitrant", 0.01))
        if fomp.get("outflow_id"):
            _fr("output_carbon_id", fomp["outflow_id"])
        if fomp.get("outflow_id_2"):
            _fr("output_environmental_id", fomp["outflow_id_2"])
    result["3_2_Definition_FOMP"] = (
        pd.DataFrame(fomp_rows)
        if fomp_rows
        else pd.DataFrame(columns=["Process_ID", "Parameter_Name", "Value"])
    )

    # ── 3_1_Definition_DSM ─────────────────────────────────────────────────────
    # One row per category (load_dsm_parameters category-based format). Note the
    # correct sheet name is 3_1_Definition_DSM (the loader reads this exact name).
    dsm_rows = []
    comp_rows = []
    for p in processes:
        if p.get("logic") not in ("DSM", "DSM_Component"):
            continue
        pid = p.get("id")
        cats = (p.get("dsm") or {}).get("categories") or [{}]
        for ci, cat in enumerate(cats, 1):
            dsm_rows.append(
                {
                    "Process_ID": pid,
                    "Category_ID": ci,
                    "Category_Name": cat.get("name", f"Cat_{ci}"),
                    "Inflow_Split_[%]": cat.get("inflow_split", 1.0),
                    "Lifetime_Type": cat.get("lifetime_type", "Normal"),
                    "Lifetime_Mean": cat.get("lifetime_mean"),
                    "Lifetime_StdDev": cat.get("lifetime_std"),
                    "Lifetime_Shape": cat.get("lifetime_shape"),
                    "Lifetime_Scale": cat.get("lifetime_scale"),
                }
            )
        # Component rows (DSM_Component only)
        if p.get("logic") == "DSM_Component":
            for comp in (p.get("dsm") or {}).get("components", []):
                comp_rows.append(
                    {
                        "Process_ID": pid,
                        "Element_Name": comp.get("element", ""),
                        "Mean_Lifetime": comp.get("mean_lifetime"),
                        "SpareOutflow_ID": comp.get("sparepart_outflow", ""),
                        "SpareInflow_ID": comp.get("sparepart_inflow", ""),
                    }
                )
    result["3_1_Definition_DSM"] = (
        pd.DataFrame(dsm_rows)
        if dsm_rows
        else pd.DataFrame(
            columns=[
                "Process_ID",
                "Category_ID",
                "Category_Name",
                "Inflow_Split_[%]",
                "Lifetime_Type",
                "Lifetime_Mean",
                "Lifetime_StdDev",
                "Lifetime_Shape",
                "Lifetime_Scale",
            ]
        )
    )
    result["3_1_DSM_Components"] = (
        pd.DataFrame(comp_rows)
        if comp_rows
        else pd.DataFrame(
            columns=["Process_ID", "Element_Name", "Mean_Lifetime", "SpareOutflow_ID", "SpareInflow_ID"]
        )
    )

    # ── 3_3_Definition_LFG ─────────────────────────────────────────────────────
    # Row-per-parameter layout (load_lfg_parameters): site scalars (MCF, DOCf,
    # F_CH4, OX, phi, f_capture, outflow_*_id) + per-fraction rows whose
    # LFG_Parameter_ID carries a _j{n} suffix (k_j, DOC_j, f_input_j, f_ash_j,
    # Waste_Fraction_j).
    lfg_rows = []
    for p in processes:
        if p.get("logic") != "LFG":
            continue
        lfg = p.get("lfg") or {}
        pid = p.get("id")

        def _lr(ptype, val, suffix=""):
            lfg_rows.append(
                {
                    "Process_ID": pid,
                    "LFG_Parameter_ID": f"P{pid:02d}_{ptype}{suffix}",
                    "LFG_Parameter_type": ptype,
                    "LFG_Parameter_Value": val,
                }
            )

        for ptype, key in (
            ("MCF", "mcf"),
            ("DOCf", "doc_f"),
            ("F_CH4", "f_ch4"),
            ("OX", "ox"),
            ("phi", "phi"),
            ("f_capture", "f_capture"),
        ):
            _lr(ptype, lfg.get(key))
        for ptype, key in (
            ("outflow_ch4_id", "outflow_ch4_id"),
            ("outflow_co2_id", "outflow_co2_id"),
            ("outflow_leachate_id", "outflow_leachate_id"),
        ):
            if lfg.get(key):
                _lr(ptype, lfg[key])
        for n, frac in enumerate(lfg.get("fractions", []), 1):
            j = f"_j{n}"
            _lr("Waste_Fraction_j", frac.get("name", f"Fraction_{n}"), j)
            _lr("k_j", frac.get("k_j"), j)
            _lr("DOC_j", frac.get("doc_j"), j)
            _lr("f_input_j", frac.get("f_input_j"), j)
            _lr("f_ash_j", frac.get("f_ash_j"), j)
    result["3_3_Definition_LFG"] = (
        pd.DataFrame(lfg_rows)
        if lfg_rows
        else pd.DataFrame(
            columns=[
                "Process_ID",
                "LFG_Parameter_ID",
                "LFG_Parameter_type",
                "LFG_Parameter_Value",
            ]
        )
    )

    # ── 3_4_Definition_FlowCap ─────────────────────────────────────────────────
    # Capped_Output rows (one per cap-series year) + an Overflow row, per process
    # (load_flow_cap_parameters).
    fc_rows = []
    for p in processes:
        if p.get("logic") != "FlowCap":
            continue
        fc = p.get("flowcap") or {}
        pid = p.get("id")
        capped = fc.get("capped_flow_id")
        if not capped:
            continue
        cap_series = fc.get("cap_series") or {}
        cap_tc = fc.get("cap_tc_id") or ""
        if cap_series:
            for year, cap in cap_series.items():
                fc_rows.append(
                    {
                        "Process_ID": pid,
                        "Flow_ID": capped,
                        "Output_flow_type": "Capped_Output",
                        "Year": (None if str(year) == "0" else int(year)),
                        "Flow": cap,
                        "Cap_TC_ID": cap_tc,
                    }
                )
        else:
            fc_rows.append(
                {
                    "Process_ID": pid,
                    "Flow_ID": capped,
                    "Output_flow_type": "Capped_Output",
                    "Year": None,
                    "Flow": None,
                    "Cap_TC_ID": cap_tc,
                }
            )
        if fc.get("overflow_flow_id"):
            fc_rows.append(
                {
                    "Process_ID": pid,
                    "Flow_ID": fc["overflow_flow_id"],
                    "Output_flow_type": "Overflow",
                    "Year": None,
                    "Flow": None,
                    "Cap_TC_ID": "",
                }
            )
    result["3_4_Definition_FlowCap"] = (
        pd.DataFrame(fc_rows)
        if fc_rows
        else pd.DataFrame(
            columns=[
                "Process_ID",
                "Flow_ID",
                "Output_flow_type",
                "Year",
                "Flow",
                "Cap_TC_ID",
            ]
        )
    )

    # ── 4_1_Uncertainty_Parameters ────────────────────────────────────────────
    mc_params_yaml = data.get("mc_parameters", [])
    mc_rows = []
    for p in mc_params_yaml:
        enabled = p.get("enabled", True)
        mc_rows.append(
            {
                "MC_Parameter_ID": p.get("parameter_id", ""),
                "MC_Parameter_Selection": "✓" if enabled else None,
                "Distribution_Type": p.get("distribution", "normal"),
                "Mean": p.get("mean"),
                "StdDev": p.get("std"),
                "Min": p.get("min"),
                "Max": p.get("max"),
                "Mode": p.get("mode"),
                "MC_Operation": p.get("operation", "set"),
                "MC_Start_Year": p.get("start_year"),
                "MC_End_Year": p.get("end_year"),
                "MC_Flow_Group": p.get("flow_group"),
            }
        )
    result["4_1_Uncertainty_Parameters"] = (
        pd.DataFrame(mc_rows)
        if mc_rows
        else pd.DataFrame(
            columns=[
                "MC_Parameter_ID",
                "MC_Parameter_Selection",
                "Distribution_Type",
                "Mean",
                "StdDev",
                "Min",
                "Max",
                "Mode",
                "MC_Operation",
                "MC_Start_Year",
                "MC_End_Year",
                "MC_Flow_Group",
            ]
        )
    )

    # ── 5_1_Scenario_Manager ───────────────────────────────────────────────────
    # One row per scenario modification. Columns match what load_scenario_
    # definitions expects (Scenario_Name, Parameter_Name, Operation, New_Value,
    # start/end year). Without this, scenarios defined in a YAML config never
    # reach the scenario engine.
    scen_rows = []
    for sc in data.get("scenarios", []):
        sname = (sc.get("name") or "").strip()
        if not sname:
            continue
        for m in sc.get("modifications", []):
            pname = (m.get("parameter_name") or "").strip()
            if not pname:
                continue
            scen_rows.append(
                {
                    "Scenario_Name": sname,
                    "Parameter_Name": pname,
                    "Parameter_Type": m.get("parameter_type", "") or "",
                    "Operation": (m.get("operation") or "replace"),
                    "New_Value": float(m.get("new_value") or 0.0),
                    "start_year": m.get("start_year"),
                    "end_year": m.get("end_year"),
                }
            )
    result["5_1_Scenario_Manager"] = (
        pd.DataFrame(scen_rows)
        if scen_rows
        else pd.DataFrame(
            columns=[
                "Scenario_Name",
                "Parameter_Name",
                "Parameter_Type",
                "Operation",
                "New_Value",
                "start_year",
                "end_year",
            ]
        )
    )

    # ── 3_3_Definition_BOM_Assembly ────────────────────────────────────────────
    # One row per output flow per BOM_Assembler process. target_Product flows
    # carry the parent-relative element fractions as inline E{n}_TC_Value[%]
    # values (the engine reads these and cascades them to absolute via the
    # element hierarchy). Material (n=1) is the total mass, never a BOM fraction.
    proc_tc_cfg = {
        p.get("id"): (
            p.get("tc_config")
            if p.get("tc_config") in ("Static", "Dynamic")
            else "No TC"
        )
        for p in processes
    }
    bom_rows = []
    for entry in data.get("bom_assembly", []):
        pid = entry.get("process_id")
        tc_cfg = proc_tc_cfg.get(pid, "No TC")
        for bf in entry.get("flows", []):
            fid = bf.get("flow_id", "")
            if not fid:
                continue
            ftype = bf.get("output_flow_type", "")
            row = {
                "Process_ID": pid,
                "Flow_ID": fid,
                "Output_flow_type": ftype,
                "TC_Configuration": tc_cfg,
            }
            if ftype == "target_Product":
                fracs = bf.get("fractions", {})
                for idx, elem in enumerate(elements):
                    if elem == "material":
                        continue
                    row[f"E{idx + 1}_TC_Value[%]"] = fracs.get(elem)
            bom_rows.append(row)
    result["3_3_Definition_BOM_Assembly"] = (
        pd.DataFrame(bom_rows)
        if bom_rows
        else pd.DataFrame(
            columns=["Process_ID", "Flow_ID", "Output_flow_type", "TC_Configuration"]
        )
    )

    n_static = len(static_rows)
    n_dyn = len(dyn_rows)
    print(
        f"   ✓ YAML→DataFrames: {len(processes)} processes, {len(flows)} flows, "
        f"{n_static} static-TC rows, {n_dyn} dynamic-TC rows, {len(mc_rows)} MC params, "
        f"{len(bom_rows)} BOM rows, {len(is_rows)} initial-stock rows, "
        f"{len(fomp_rows)} FOMP rows, {len(dsm_rows)} DSM rows, "
        f"{len(lfg_rows)} LFG rows, {len(fc_rows)} FlowCap rows, "
        f"{len(scen_rows)} scenario rows"
    )
    return result


def load_initial_stock_parameters(excel_data, elements=None):
    """Loads initial stock parameters by delegating to the initial stock engine.

    This function acts as a wrapper to ensure consistency, calling the
    `load_initial_stock_parameters` function from the dedicated
    `initial_stock_engine` module.

    Parameters
    ----------
    excel_data : dict
        Dictionary of DataFrames from the loaded Excel file.
    elements : list of str, optional
        List of element names (e.g., ['material', 'WC', 'DM', 'CC']).
        If None, defaults to ['material', 'WC', 'DM', 'CC'].

    Returns
    -------
    dict
        A dictionary of initial stock configurations, keyed by process ID.
    """
    # Import here to avoid circular imports
    from engine import initial_stock_engine

    return initial_stock_engine.load_initial_stock_parameters(excel_data, elements)


def load_all_parameters(
    all_excel_data,
    config_obj,
    yaml_config_file=None,
    elements=None,
    debug_mode=False,
):
    """Load DSM / FOMP / LFG / FlowCap / BOM parameters from YAML or Excel.

    Dispatches to the YAML web-app loaders when ``yaml_config_file`` is given,
    otherwise to the Excel-sheet loaders. FOMP is only loaded when
    ``config_obj.RUN_FOMP_CALCULATION`` is truthy (matching the engine guard).
    BOM parameters are loaded the same way regardless of source.

    Parameters
    ----------
    all_excel_data : dict
        Loaded (or YAML-synthesised) sheet DataFrames.
    config_obj : object
        Configuration object (used for ``RUN_FOMP_CALCULATION``).
    yaml_config_file : str, optional
        Path to a SystemDefiner YAML config; when set, YAML loaders are used.
    elements : list, optional
        Element names, passed to the BOM loader.
    debug_mode : bool, optional
        Verbose loader output.

    Returns
    -------
    dict
        Keys ``"dsm"``, ``"fomp"``, ``"lfg"``, ``"flow_cap"``, ``"bom"``.
    """
    if yaml_config_file:
        dsm = load_dsm_from_yaml(yaml_config_file)
        fomp = (
            load_fomp_from_yaml(yaml_config_file)
            if config_obj.RUN_FOMP_CALCULATION
            else {}
        )
        lfg = load_lfg_from_yaml(yaml_config_file)
        flow_cap = load_flow_cap_from_yaml(yaml_config_file)
    else:
        dsm = load_dsm_parameters(all_excel_data, debug_mode=debug_mode)
        fomp = (
            load_fomp_parameters(all_excel_data, debug_mode=debug_mode)
            if config_obj.RUN_FOMP_CALCULATION
            else {}
        )
        lfg = load_lfg_parameters(all_excel_data, debug_mode=debug_mode)
        flow_cap = load_flow_cap_parameters(all_excel_data, debug_mode=debug_mode)

    bom = load_bom_parameters(all_excel_data, elements=elements, debug_mode=debug_mode)

    return {"dsm": dsm, "fomp": fomp, "lfg": lfg, "flow_cap": flow_cap, "bom": bom}
