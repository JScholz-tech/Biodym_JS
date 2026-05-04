# -*- coding: utf-8 -*-
"""
Data Loader Module for the BioDYM MFA Model.

This file contains all functions responsible for reading, validating, and
parsing the input data from the Excel template file. It acts as the
interface between the raw data and the core model logic.

UPDATED: Added column name mapping to handle naming convention changes.
"""

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
    # Add more mappings as needed
}

# Sheet name mapping for backward compatibility
SHEET_NAME_MAPPING = {
    "PX - Template": "PX_Template",  # Standardize separator
    "2_3_static_TCs": "2_2_static_TCs",  # Handle sheet renumbering
    # Add more mappings as needed
}


def normalize_column_names(df, sheet_name):
    """Normalizes column names in a DataFrame based on a predefined mapping.

    This function checks for a mapping for the given sheet name in the global
    COLUMN_NAME_MAPPING constant and applies it. This allows for backward
    compatibility with older Excel template versions.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame whose columns are to be normalized.
    sheet_name : str
        The name of the sheet the DataFrame was read from.

    Returns
    -------
    pd.DataFrame
        A new DataFrame with normalized column names.
    """
    if sheet_name in COLUMN_NAME_MAPPING:
        mapping = COLUMN_NAME_MAPPING[sheet_name]
        df = df.rename(columns=mapping)
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
            if process_logic == "DSM" and stock_config not in valid_dsm_stock_configs:
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


def normalize_dynamic_tcs_by_process(tc_params, all_excel_data, elements, debug_mode=False):
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
                    f"TCs sum to {tc_sum.min()*100:.1f}%-{tc_sum.max()*100:.1f}% (not 100%)"
                )
                print(f"      → Normalizing {len(tc_names)} TCs to ensure mass balance...")

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
                    f"element {element} (max deviation: {max_deviation*100:.2f}%)"
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
        if pd.notna(process_id) and process_logic in ["Splitter", "Transformer", "DSM"]:
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
            dsm_processes = main_df[main_df["Process_Logic"] == "DSM"]
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
                stock_config = str(process_row.iloc[0].get("Stock_Configuration", "Stock")).strip()
                dsm_params[process_id]["stock_configuration"] = stock_config

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

    # Extract lifetime data for validation
    lifetime_means = list(process_data["Lifetime_Mean"])
    lifetime_stddevs = list(process_data["Lifetime_StdDev"])
    category_names = list(process_data["Category_Name"])

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

    if "LFG_Parameter_type" not in df_lfg.columns or "LFG_Parameter_Value" not in df_lfg.columns:
        if debug_mode:
            print(
                "   WARNING: Required columns 'LFG_Parameter_type' / "
                "'LFG_Parameter_Value' not found in sheet. Skipping LFG loading."
            )
        return {}

    # Map Excel parameter type strings → internal canonical names
    PARAM_MAP = {
        "F":                   "F_CH4",
        "F_CH4":               "F_CH4",
        "Φ":                   "phi",
        "φ":                   "phi",
        "phi":                 "phi",
        "f":                   "f_capture",
        "output_CH4_id":       "outflow_ch4_id",
        "output_CO2_id":       "outflow_co2_id",
        "output_leaching":     "outflow_leachate_id",
        "outflow_ch4_id":      "outflow_ch4_id",
        "outflow_co2_id":      "outflow_co2_id",
        "outflow_leachate_id": "outflow_leachate_id",
    }

    # Site-level scalar parameters (after PARAM_MAP normalisation)
    SITE_PARAMS = {"MCF", "DOCf", "F_CH4", "OX", "phi", "f_capture",
                   "outflow_ch4_id", "outflow_co2_id", "outflow_leachate_id"}

    # Fraction-level parameter types as they appear in the Excel
    FRAC_PARAM_TYPES = {"Waste_Fraction_j", "f_input_j", "DOC_j", "k_j", "f_ash_j"}

    # Regex to extract fraction index from LFG_Parameter_ID, e.g. "P01_k_j2" → 2
    _j_pattern = re.compile(r"_j(\d+)\b", re.IGNORECASE)

    lfg_params = {}       # {process_id: {"fractions": [...], "MCF": ..., ...}}
    frac_staging = {}     # {process_id: {frac_index: {param_type: value}}}

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
                "k_j":       _sf("k_j"),
                "DOC_j":     _sf("DOC_j"),
                "f_input_j": _sf("f_input_j"),
                "f_ash_j":   _sf("f_ash_j", default=0.0),
            }
            lfg_params[process_id]["fractions"].append(frac)

    if debug_mode:
        print(
            f"--> Successfully loaded configurations for {len(lfg_params)} LFG process(es)."
        )
        for process_id, params in lfg_params.items():
            n_frac = len(params.get("fractions", []))
            print(f"   Process {process_id}: {n_frac} fraction(s), "
                  f"site params: MCF={params.get('MCF')}, DOCf={params.get('DOCf')}, "
                  f"F_CH4={params.get('F_CH4')}, OX={params.get('OX')}")

    return lfg_params


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
    id_col = "MC_Parameter_ID" if "MC_Parameter_ID" in df_uncertainty.columns else "Parameter_Name"
    df_uncertainty = df_uncertainty.dropna(subset=[id_col])

    # Filter by MC_Parameter_Selection toggle — skip rows where it is empty/NaN
    sel_col = "MC_Parameter_Selection"
    if sel_col in df_uncertainty.columns:
        df_uncertainty = df_uncertainty[df_uncertainty[sel_col].notna() & (df_uncertainty[sel_col].astype(str).str.strip() != "")]

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
            print(f"⚠️ WARNING: Unknown distribution type '{dist_type}' for parameter '{param_name}' — skipping.")

        # --- Optional modifier columns (new names preferred, legacy fallback) ---
        op_col = "MC_Operation" if "MC_Operation" in df_uncertainty.columns else "Operation"
        raw_op = row.get(op_col)
        if raw_op is not None and pd.notna(raw_op) and str(raw_op).strip():
            definition["operation"] = str(raw_op).strip().lower()

        start_col = "MC_Start_Year" if "MC_Start_Year" in df_uncertainty.columns else "start_year"
        raw_start = row.get(start_col)
        if raw_start is not None and pd.notna(raw_start):
            try:
                definition["start_year"] = int(raw_start)
            except (ValueError, TypeError):
                print(f"⚠️ WARNING: Invalid {start_col} '{raw_start}' for '{param_name}' — ignoring.")

        end_col = "MC_End_Year" if "MC_End_Year" in df_uncertainty.columns else "end_year"
        raw_end = row.get(end_col)
        if raw_end is not None and pd.notna(raw_end):
            try:
                definition["end_year"] = int(raw_end)
            except (ValueError, TypeError):
                print(f"⚠️ WARNING: Invalid {end_col} '{raw_end}' for '{param_name}' — ignoring.")

        raw_group = row.get("MC_Flow_Group")
        if raw_group is not None and pd.notna(raw_group) and str(raw_group).strip():
            definition["flow_group"] = str(raw_group).strip()

        if len(definition) > 1:
            if param_name.startswith("F_"):
                definition["flow_id"] = param_name  # real flow name, preserved before any renaming
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

    try:
        df_scenarios = df.dropna(subset=["Scenario_Name", "Parameter_Name"])
    except KeyError:
        print(
            f"--> ERROR: Could not find 'Scenario_Name' or 'Parameter_Name' columns in sheet '{sheet_name}'."
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
