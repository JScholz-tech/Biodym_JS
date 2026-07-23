# -*- coding: utf-8 -*-
"""
System Setup Module for the BioDYM MFA Model.

This file contains all functions responsible for building and configuring
the MFAsystem object before the main calculation begins. This includes
defining the model scope, initializing the system, loading process and flow
definitions, and setting up all parameters.
"""

import numpy as np
import pandas as pd
import sys
import os

# Add ODYM framework to path to ensure ODYM_Classes can be found
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
odym_path = os.path.join(
    project_root, "06_framework", "ODYM-master_20241127", "odym", "modules"
)
if odym_path not in sys.path:
    sys.path.insert(0, odym_path)

# These are imported by main.py and are available in this namespace
import ODYM_Classes as msc  # noqa: E402
import data_loader  # noqa: E402

# Handle both direct import and package import
try:
    from . import utils
except ImportError:
    import utils


def define_model_scope(
    start_year,
    end_year,
    elements,
    regions=None,
    goods=None,
    materials=None,
    processes=None,
):
    """Defines the temporal and elemental scope of the MFA model with ODYM dimensions.

    Phase 1b: Adds support for Region, Good, Material, and Process dimensions.
    Maintains backward compatibility - all new dimensions are optional with defaults.

    Parameters
    ----------
    start_year : int
        The first year of the analysis.
    end_year : int
        The last year of the analysis.
    elements : list of str
        A list of strings for the elements to be tracked (e.g., ['material', 'WC']).
    regions : list of str, optional
        A list of region names. Defaults to ["Case_Study_Region"] if not provided.
    goods : list of str, optional
        A list of good categories. Defaults to None (not used initially).
    materials : list of str, optional
        A list of material categories. Defaults to None (not used initially).
    processes : list of str, optional
        A list of process types. Defaults to None (not used initially).

    Returns
    -------
    tuple
        A tuple containing:
        - model_classification (dict): The ModelClassification dictionary.
        - index_table (pd.DataFrame): The IndexTable DataFrame.
    """
    model_classification = {}
    my_years = list(np.arange(start_year, end_year + 1))

    # Default values for backward compatibility
    if regions is None:
        regions = ["Case_Study_Region"]  # Default single region

    # Existing dimensions
    model_classification["Time"] = msc.Classification(
        Name="Time", Dimension="Time", ID=1, Items=my_years
    )
    model_classification["Element"] = msc.Classification(
        Name="Elements", Dimension="Element", ID=2, Items=elements
    )

    # Build index table based on available dimensions
    aspects = ["Time", "Element"]
    descriptions = ['Model aspect "time"', 'Model aspect "Element"']
    dimensions = ["Time", "Element"]
    index_letters = ["t", "e"]
    classifications = [model_classification["Time"], model_classification["Element"]]

    # Add Material if defined (for future use)
    # For now, Materials dimension is not used - Elements handle WC, DM, CC
    # This keeps compatibility with existing solver code
    if materials is not None and len(materials) > 0:
        model_classification["Material"] = msc.Classification(
            Name="Materials", Dimension="Material", ID=3, Items=materials
        )
        aspects.append("Material")
        descriptions.append('Model aspect "Material"')
        dimensions.append("Material")
        index_letters.append("m")
        classifications.append(model_classification["Material"])

    index_table = pd.DataFrame(
        {
            "Aspect": aspects,
            "Description": descriptions,
            "Dimension": dimensions,
            "Classification": classifications,
            "IndexLetter": index_letters,
        }
    )
    index_table.set_index("Aspect", inplace=True)

    # Removed verbose print - model scope is shown in validation summary
    return model_classification, index_table


def initialize_mfa_system(model_classification, index_table, unit="Mg"):
    """Initializes the main MFAsystem object based on the defined scope.

    Parameters
    ----------
    model_classification : dict
        The ModelClassification dictionary created by `define_model_scope`.
    index_table : pd.DataFrame
        The IndexTable DataFrame created by `define_model_scope`.
    unit : str, optional
        Mass unit label stored on the ODYM system object (e.g. 'Mg', 'kg').
        Defaults to 'Mg'. Pass ``getattr(config_obj, 'Unit', 'Mg')`` from
        the loaded configuration to make it config-driven.

    Returns
    -------
    odym.MFAsystem
        An empty but structured MFAsystem object ready for configuration.
    """
    start_time = model_classification["Time"].Items[0]
    end_time = model_classification["Time"].Items[-1]
    element_items = model_classification["Element"].Items

    mfa_system = msc.MFAsystem(
        Name="RyeStrawMFA",
        Geogr_Scope="Case_Study_Region",
        Unit=unit,
        ProcessList=[],
        FlowDict={},
        StockDict={},
        ParameterDict={},
        Time_Start=start_time,
        Time_End=end_time,
        IndexTable=index_table,
        Elements=element_items,
    )

    # ODYM compliance: Check IndexTable consistency
    try:
        mfa_system.IndexTableCheck()
    except ValueError as e:
        print(f"--> WARNING: IndexTable validation failed: {e}")
        raise

    # Removed verbose print - initialization is shown in validation summary
    return mfa_system


def load_and_define_processes(mfa_system, input_data, data_loader, debug_mode=False):
    """Load data, validate, and define processes and stocks in the MFA system.

    This function reads all data from the source Excel file, validates the
    structure, and then iterates through the process definitions sheet to
    populate the MFAsystem object with Process and Stock objects.

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        The initialized MFA system object.
    input_data : dict or str
        A dictionary of DataFrames for each Excel sheet, or a path to the file.
    data_loader : module
        The imported data_loader module containing validation functions.
    debug_mode : bool, optional
        If True, print detailed loading progress. Default is False.

    Returns
    -------
    tuple
        A tuple containing:
        - mfa_system (odym.MFAsystem): The modified MFAsystem object.
        - all_excel_data (dict): The dictionary of all data read from Excel.
    """
    if debug_mode:
        print("--> Defining process and stock structures...")

    # Accept either a pre-loaded dict of DataFrames or a path to an Excel file
    if isinstance(input_data, dict):
        all_excel_data = input_data
    else:
        # Load all sheets into a dict; tests may patch pd.read_excel to return a dict
        # NOTE: Uses decimal=',' for European standard (comma as decimal separator)
        # Use safe_read_excel to avoid file locking issues
        all_excel_data = utils.safe_read_excel(
            input_data,
            sheet_name=None,
            header=0,
            engine="openpyxl",
            na_values=["N.A.", "NA", "n/a"],
            decimal=",",
        )
        if debug_mode:
            print("   ✓ Excel file loaded safely (original file remains unlocked)")

    data_loader.validate_input_data(all_excel_data, debug_mode=debug_mode)

    # Check which processes have initial stock configurations
    # This is needed to automatically create stocks for these processes
    initial_stock_process_ids = set()
    if "2_4_Initial_Stock" in all_excel_data:
        initial_stock_df = all_excel_data["2_4_Initial_Stock"]
        if not initial_stock_df.empty and "Process_ID" in initial_stock_df.columns:
            initial_stock_process_ids = set(
                initial_stock_df["Process_ID"].dropna().astype(int).unique()
            )
            if debug_mode and initial_stock_process_ids:
                print(
                    f"   ✓ Found initial stock definitions for processes: {sorted(initial_stock_process_ids)}"
                )

    process_definitions = all_excel_data["2_1_Definition_Processes"]
    for _, row in process_definitions.iterrows():
        if pd.notna(row["Process_Name"]):
            process_id = int(row["ID"])
            # Handle TC configuration - support both unified and legacy columns
            has_tcs = "None"
            if "TC_Configuration" in row and pd.notna(row["TC_Configuration"]):
                tc_config = str(row["TC_Configuration"]).strip()
                if tc_config in ["Static", "Dynamic"]:
                    has_tcs = "TC"

            mfa_system.ProcessList.append(
                msc.Process(Name=row["Process_Name"], ID=process_id, Extensions=has_tcs)
            )

            # Handle Stock configuration - support both unified and legacy columns
            should_create_stock = False
            if "Stock_Configuration" in row and pd.notna(row["Stock_Configuration"]):
                stock_config = str(row["Stock_Configuration"]).strip()
                should_create_stock = stock_config == "Stock"

            # IMPORTANT: If process has initial stock, it MUST have stock objects
            # Override should_create_stock if initial stock is defined
            if process_id in initial_stock_process_ids:
                if not should_create_stock:
                    print(
                        f"   → Process {process_id} has initial stock - automatically creating stock objects"
                    )
                should_create_stock = True

            if should_create_stock:
                mfa_system.StockDict[f"dS_{process_id}"] = msc.Stock(
                    Name=f"dS_{process_id}", P_Res=process_id, Type=1, Indices="t,e"
                )
                mfa_system.StockDict[f"S_{process_id}"] = msc.Stock(
                    Name=f"S_{process_id}", P_Res=process_id, Type=0, Indices="t,e"
                )

                fomp_sheet = all_excel_data.get("3_2_Definition_FOMP")
                is_fomp_process = False
                if fomp_sheet is not None:
                    fomp_processes = fomp_sheet[fomp_sheet["Process_ID"] == process_id]
                    # Check for FOMP process using unified Process_Logic or legacy FOMP? column
                    process_logic = str(row.get("Process_Logic", "")).strip()
                    fomp_legacy = str(row.get("FOMP?", "No")).strip() == "Yes"
                    is_fomp_process = (process_logic == "FOMP" or fomp_legacy) and (
                        not fomp_processes.empty
                    )

                if is_fomp_process:
                    mfa_system.StockDict[f"S_{process_id}"]._fomp_process = True

    for stock_name, stock_obj in mfa_system.StockDict.items():
        # Mark FOMP processes for ODYM initialization (no manual np.zeros)
        if hasattr(stock_obj, "_fomp_process") and stock_obj._fomp_process:
            # Leave Values as None - ODYM's Initialize_StockValues() will handle this
            delattr(stock_obj, "_fomp_process")

    # Initialize stock values using ODYM method with error handling
    try:
        mfa_system.Initialize_StockValues()
        if debug_mode:
            print("--> Stock values initialized.")
    except Exception as e:
        print(f"--> ERROR: Failed to initialize stock values: {e}")
        print(f"    Stock count: {len(mfa_system.StockDict)} stocks defined")
        raise

    return mfa_system, all_excel_data


def create_dynamic_tc_parameters_from_2_4_format(dynamic_tc_data, time_vector):
    """
    Generates time series for TCs from the 2_4_dynamic_tcs format.
    Expects columns: TC_material_ID, Year, TC_Value_material
    """
    print("--> Generating dynamic TC time series from 2_4 format...")

    # Extract the relevant columns
    tc_data = dynamic_tc_data[["TC_material_ID", "TC_Value_material", "Year"]].dropna()

    if tc_data.empty:
        print("  -> No valid TC data found in 2_4_dynamic_tcs format")
        return {}

    # Group by TC_ID and create time series
    dynamic_tc_dict = {}
    unique_tc_ids = tc_data["TC_material_ID"].unique()

    for tc_id in unique_tc_ids:
        tc_points = tc_data[tc_data["TC_material_ID"] == tc_id]

        # Create time series
        ts = pd.Series(tc_points["TC_Value_material"].values, index=tc_points["Year"])

        # Reindex to full time vector and interpolate
        ts_full = ts.reindex(time_vector)
        ts_interpolated = ts_full.interpolate(method="linear", limit_direction="both")

        # Handle edge cases where interpolation might fail
        if ts_interpolated.isna().any():
            # Fill remaining NaN values with the nearest available value
            ts_interpolated = ts_interpolated.ffill().bfill()

        dynamic_tc_dict[tc_id] = ts_interpolated.to_numpy()

        print(
            f"  -> Created time series for {tc_id}: {len(tc_points)} data points -> {len(ts_interpolated)} time steps"
        )

    print(
        f"--> Generated {len(dynamic_tc_dict)} dynamic TC parameter(s) from 2_4 format."
    )
    return dynamic_tc_dict


def create_dynamic_tc_parameters(dynamic_tc_data, time_vector):
    """
    Generates time series for TCs, with data cleaning and validation.
    """
    print("--> Generating dynamic TC time series via interpolation...")
    required_cols = ["TC_ID", "Year", "Value"]
    if not all(col in dynamic_tc_data.columns for col in required_cols):
        raise ValueError(
            f"The '2_5_dynamic_tcs' sheet is missing one of the required columns: {required_cols}."
        )

    cleaned_data = dynamic_tc_data.dropna(subset=["TC_ID", "Year"])
    duplicates = cleaned_data[
        cleaned_data.duplicated(subset=["TC_ID", "Year"], keep=False)
    ]
    if not duplicates.empty:
        raise ValueError(
            f"Duplicate entries found for the same TC in the same year in '2_5_dynamic_tcs'. Conflicting rows:\n{duplicates.sort_values(by=['TC_ID', 'Year'])}"
        )

    dynamic_tc_dict = {}
    unique_tc_ids = cleaned_data["TC_ID"].unique()
    for tc_id in unique_tc_ids:
        tc_points = cleaned_data[cleaned_data["TC_ID"] == tc_id]
        ts = pd.Series(tc_points["Value"].values, index=tc_points["Year"])
        ts_full = ts.reindex(time_vector)
        ts_interpolated = ts_full.interpolate(method="linear", limit_direction="both")
        dynamic_tc_dict[tc_id] = ts_interpolated.to_numpy()

    print(f"--> Generated {len(dynamic_tc_dict)} dynamic TC parameter(s).")
    return dynamic_tc_dict


def _initialize_flows(mfa_system, flow_definitions):
    """Initializes all flows in the MFAsystem from the definitions sheet.

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        The MFA system object to be modified.
    flow_definitions : pd.DataFrame
        DataFrame containing the flow definitions from Excel.
    """
    # Create external dictionary for flow descriptions (ODYM compliance)
    flow_descriptions = {}

    for _, row in flow_definitions.iterrows():
        # Check if row has valid flow name and process IDs
        if (
            pd.notna(row["Flow_Name"])
            and pd.notna(row.get("Flow_Output_Process_ID"))
            and pd.notna(row.get("Input_Process_ID"))
        ):
            start_id, end_id = (
                int(row["Flow_Output_Process_ID"]),
                int(row["Input_Process_ID"]),
            )
            flow_obj = msc.Flow(
                Name=row["Flow_ID"], P_Start=start_id, P_End=end_id, Indices="t,e"
            )
            flow_id = row["Flow_ID"]

            # Store descriptive name in external dict (ODYM compliance - no custom attributes)
            flow_descriptions[flow_id] = row["Flow_Name"]

            mfa_system.FlowDict[flow_id] = flow_obj

    # Store flow descriptions in mfa_system for later use (external to Flow objects)
    mfa_system._flow_descriptions = flow_descriptions

    # Initialize flow values using ODYM method with error handling
    try:
        mfa_system.Initialize_FlowValues()
        # Removed verbose print - flows are shown in validation summary
    except Exception as e:
        print(f"--> ERROR: Failed to initialize flow values: {e}")
        print(f"    Flow count: {len(flow_descriptions)} flows defined")
        raise


def _populate_primary_flow_data(mfa_system, flow_data, debug_mode=False):
    """Populates flows with primary data from the '1_2_Data_Flows' sheet.

    Supports both old format (Flow_Material) and new E# format (E1_value).
    Automatically interpolates flow data to fill gaps in the time series.

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        The MFA system object to be modified.
    flow_data : pd.DataFrame
        DataFrame containing the flow data from Excel.
    debug_mode : bool, optional
        If True, print detailed loading progress. Default is False.
    """
    # Detect which column format is used for material flow data
    material_col = None
    if "Flow_Material" in flow_data.columns:
        material_col = "Flow_Material"
        if debug_mode:
            print("[INFO] Using legacy format 'Flow_Material' for flow data")
    elif "E1_value" in flow_data.columns:
        material_col = "E1_value"
        if debug_mode:
            print("[INFO] Using new E# format 'E1_value' for flow data")
    else:
        raise ValueError(
            "ERROR: Could not find material flow column in 1_2_Data_Flows sheet. "
            "Expected either 'Flow_Material' (old format) or 'E1_value' (new format)"
        )

    # Get the full time vector from the model
    time_vector = mfa_system.IndexTable.Classification["Time"].Items
    interpolation_count = 0

    for flow_id, flow_obj in mfa_system.FlowDict.items():
        if flow_id in flow_data["Flow_ID"].values:
            flow_time_series = flow_data[flow_data["Flow_ID"] == flow_id]

            # Check if we have complete data or need interpolation
            if len(flow_time_series) == len(time_vector):
                # Complete data - use directly
                flow_obj.Values[:, 0] = np.array(flow_time_series[material_col]).ravel()
            else:
                # Incomplete data - interpolate to fill gaps
                # Create a pandas Series indexed by year
                available_years = flow_time_series["Flow_Data_Year"].values
                available_values = flow_time_series[material_col].values

                ts = pd.Series(available_values, index=available_years)

                # Reindex to full time vector and interpolate
                ts_full = ts.reindex(time_vector)
                ts_interpolated = ts_full.interpolate(
                    method="linear", limit_direction="both"
                )

                # Handle edge cases where interpolation might fail
                if ts_interpolated.isna().any():
                    ts_interpolated = ts_interpolated.ffill().bfill()

                # Apply interpolated values
                flow_obj.Values[:, 0] = ts_interpolated.to_numpy()

                interpolation_count += 1
                if debug_mode:
                    print(
                        f"    -> Interpolated flow {flow_id}: "
                        f"{len(flow_time_series)} data points -> {len(time_vector)} time steps"
                    )

    if interpolation_count > 0:
        print(
            f"   ✓ Interpolated {interpolation_count} flow(s) to fill time series gaps"
        )

    if debug_mode:
        print("--> Populated data for primary input flows.")


def _apply_initial_stock(mfa_system, all_excel_data):
    """Loads and applies initial stock configurations to the system.

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        The MFA system object to be modified.
    all_excel_data : dict
        Dictionary of all data read from Excel.
    """
    # Load initial stock parameters, passing the elements list from the system
    initial_stock_configs = data_loader.load_initial_stock_parameters(
        all_excel_data, elements=mfa_system.Elements
    )
    if initial_stock_configs:
        from engine import initial_stock_engine

        mfa_system = initial_stock_engine.apply_initial_stock_values(
            mfa_system, initial_stock_configs
        )

        # Store initial_stock_configs on MFA system for later use by DSM Cohort mode
        mfa_system._process_initial_stock_configs = initial_stock_configs


def _define_content_parameters(mfa_system, content_definitions):
    """Defines content parameters (e.g., water content, metal fractions) for each flow.

    Dynamically builds column mapping based on available elements in the system.
    Supports standard naming (Flow_{element}[%]) and legacy naming conventions.

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        The MFA system object to be modified.
    content_definitions : pd.DataFrame
        DataFrame containing flow definitions, including content percentages.
    """
    # Build element-to-column mapping dynamically
    element_column_map = _build_element_column_map(
        mfa_system.Elements, content_definitions
    )

    parameter_id_counter = 1
    for _, row in content_definitions.iterrows():
        flow_id = row.get("Flow_ID")
        if pd.notna(flow_id) and flow_id in mfa_system.FlowDict:
            # Process all elements except 'material' (which is the total)
            for element in mfa_system.Elements[1:]:
                column_name = element_column_map.get(element)
                if column_name and column_name in row and pd.notna(row[column_name]):
                    param_name = f"{element}_{flow_id}"
                    # Priority 4: Scalar parameters need Indices="" to avoid crash in Initialize_ParameterValues()
                    mfa_system.ParameterDict[param_name] = msc.Parameter(
                        Name=param_name,
                        ID=parameter_id_counter,
                        Values=row[column_name],
                        Indices="",  # Empty string for scalar parameters (prevents AttributeError in Initialize_ParameterValues)
                        Unit="1",
                    )
                    parameter_id_counter += 1


def _build_element_column_map(elements, content_definitions):
    """
    Dynamically builds column name mapping based on elements in the system.

    For each element (except 'material'), looks for columns in this order:
    1. New format: Flow_E{id}_Fraction[%]                       (e.g., Flow_E2_Fraction[%])
    2. New with label: Flow_E{id}_[%]({element})                (e.g., Flow_E2_[%](WC))
    3. New simple: Flow_E{id}[%] or Flow_E{id}_[%]              (e.g., Flow_E2[%])
    4. Standard: Flow_{element}[%]                              (e.g., Flow_WC[%])
    5. Legacy: Flow_{element}_[%]                               (e.g., Flow_WC_[%])
    6. Special: Flow_CC_DM[%] for CC element

    Parameters
    ----------
    elements : list of str
        List of element names (e.g., ['material', 'WC', 'DM', 'CC'] or ['material', 'Fe', 'Cu', 'Al'])
    content_definitions : pd.DataFrame
        DataFrame with flow definitions to check available columns

    Returns
    -------
    dict
        Mapping from element name to Excel column name
        e.g., {'WC': 'Flow_E2_[%](WC)', 'DM': 'Flow_E3_[%](DM)', 'CC': 'Flow_E4_[%](CC)'}
        or {'WC': 'Flow_WC[%]', 'DM': 'Flow_DM[%]', 'CC': 'Flow_CC_DM[%]'} (fallback)
    """
    column_map = {}
    available_columns = list(content_definitions.columns)

    for elem_idx, element in enumerate(elements):
        if element == "material":
            continue  # Material is total, not a fraction column

        # Element index for E{id} format (1-based in Excel, 0-based in Python)
        element_id = elem_idx + 1

        # Try new format with "Fraction": Flow_E2_Fraction[%]
        e_format_fraction = f"Flow_E{element_id}_Fraction[%]"
        if e_format_fraction in available_columns:
            column_map[element] = e_format_fraction
            continue

        # Handle Excel duplicate suffix for Fraction format: Flow_E2_Fraction[%]2
        matching_fraction = [
            col
            for col in available_columns
            if col.startswith(f"Flow_E{element_id}_Fraction[%]")
        ]
        if matching_fraction:
            column_map[element] = matching_fraction[0]
            print(
                f"[INFO] Using column '{matching_fraction[0]}' for element '{element}'"
            )
            continue

        # Try new E{id} format with element name in parentheses: Flow_E2_[%](WC)
        e_format_with_name = f"Flow_E{element_id}_[%]({element})"
        if e_format_with_name in available_columns:
            column_map[element] = e_format_with_name
            continue

        # Handle Excel duplicate column suffix (e.g., Flow_E3_[%](DM)2)
        e_format_with_suffix_pattern = f"Flow_E{element_id}_[%]({element})"
        matching_cols = [
            col
            for col in available_columns
            if col.startswith(e_format_with_suffix_pattern)
        ]
        if matching_cols:
            column_map[element] = matching_cols[0]  # Use first match
            print(f"[INFO] Using column '{matching_cols[0]}' for element '{element}'")
            continue

        # Try new E{id} format without parentheses: Flow_E2[%]
        e_format_simple = f"Flow_E{element_id}[%]"
        if e_format_simple in available_columns:
            column_map[element] = e_format_simple
            continue

        # Try new E{id} format with underscore and brackets: Flow_E2_[%]
        e_format_underscore = f"Flow_E{element_id}_[%]"
        if e_format_underscore in available_columns:
            column_map[element] = e_format_underscore
            continue

        # Fallback: Try standard naming: Flow_{element}[%]
        standard_name = f"Flow_{element}[%]"
        if standard_name in available_columns:
            column_map[element] = standard_name
            continue

        # Try legacy naming with underscore: Flow_{element}_[%]
        legacy_name = f"Flow_{element}_[%]"
        if legacy_name in available_columns:
            column_map[element] = legacy_name
            continue

        # Special case: CC might be stored as "Flow_CC_DM[%]" (carbon of dry matter)
        if element == "CC" or element == "cc":
            cc_dm_name = "Flow_CC_DM[%]"
            if cc_dm_name in available_columns:
                column_map[element] = cc_dm_name
                continue

        # If not found, log warning (but don't fail - element might not be used)
        print(
            f"[WARNING] Column for element '{element}' (E{element_id}) not found in 1_1_Definition_Flows sheet"
        )
        print(f"    Expected: {e_format_with_name} or {standard_name} or {legacy_name}")
        # Don't add to map - will be skipped in parameter creation

    return column_map


def _infer_exhaustive_elements(
    all_excel_data, element_hierarchy, elements, tolerance=1e-6
):
    """Return parent elements whose tracked children are a COMPLETE decomposition.

    A node is *exhaustive* when its children account for the whole parent, and
    *partial* when they are only the tracked subset of it. BioDYM cannot infer
    this from solved values — the canonical partial node DM → {TC} (with
    Ash_content not modelled) is indistinguishable from a complete one, because
    a flow that happens to be pure carbon shows TC == DM legitimately.

    It is, however, already declared: composition fractions are parent-relative
    (see `_calculate_elemental_compositions`), so a parent whose children sum to
    1.0 on any declared flow composition has been stated to be fully accounted
    for by them. That is read here from '1_1_Definition_Flows'
    (``Flow_E{n}_Fraction[%]``, n = 1-based element index), which both the Excel
    and YAML input paths populate.

    Used by `engine.element_utils.validate_exhaustive_hierarchy` so the solver
    can flag a parent that stops equalling its own children — typically a
    hand-fitted aggregate transfer coefficient gone stale — without emitting
    false positives on legitimately partial nodes.

    Parameters
    ----------
    all_excel_data : dict
        Sheet-name → DataFrame mapping.
    element_hierarchy : dict
        {element_id: {'name': str, 'parent': str or None}}.
    elements : sequence of str
        Element names tracked by this system (``mfa_system.Elements``).
    tolerance : float, optional
        Absolute tolerance on the children sum vs 1.0 (default 1e-6).

    Returns
    -------
    set of str
        Parent element names judged exhaustive. Empty when unknown, which
        keeps the downstream check silent rather than guessing.
    """
    if not element_hierarchy:
        return set()

    elements = list(elements)
    children_map = {}
    for elem_info in element_hierarchy.values():
        name = elem_info.get("name")
        if not name or name not in elements or name == "material":
            continue
        parent = elem_info.get("parent") or "material"
        children_map.setdefault(parent, []).append(name)
    if not children_map:
        return set()

    flows_df = (all_excel_data or {}).get("1_1_Definition_Flows")
    if flows_df is None or getattr(flows_df, "empty", True):
        return set()

    # element name → its Flow_E{n}_Fraction[%] column
    frac_col = {}
    for idx, elem in enumerate(elements):
        col = f"Flow_E{idx + 1}_Fraction[%]"
        if col in flows_df.columns:
            frac_col[elem] = col

    exhaustive = set()
    for parent, child_names in children_map.items():
        if parent not in elements:
            continue
        cols = [frac_col[c] for c in child_names if c in frac_col]
        if not cols:
            continue
        for _, row in flows_df.iterrows():
            total = 0.0
            seen = False
            for col in cols:
                value = row.get(col)
                if pd.notna(value):
                    try:
                        total += float(value)
                        seen = True
                    except (TypeError, ValueError):
                        continue
            if seen and abs(total - 1.0) <= tolerance:
                exhaustive.add(parent)
                break

    return exhaustive


def _calculate_elemental_compositions(mfa_system, element_hierarchy=None):
    """Calculates elemental values for flows based on content parameters.

    Phase 5b: Now supports hierarchical element relationships where elements
    can be expressed as a percentage of other elements (e.g., CC as % of DM).

    Dynamically calculates composition for any elements defined in the system.
    Works for biomass (WC/DM/CC), metals (Fe/Cu/Al), or any custom elements.

    Iterates through flows and applies the defined content percentages/fractions
    to calculate the values for each element, respecting parent-child relationships.

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        The MFA system object to be modified.
    element_hierarchy : dict, optional
        Dictionary mapping element IDs to their structure:
        {element_id: {'name': str, 'parent': str or None}}
        If None, all elements are treated as % of material (flat structure).
    """
    elements = mfa_system.Elements
    mat_idx = 0  # Material is always first element

    # Build element name to hierarchy info mapping
    hierarchy_map = {}
    if element_hierarchy:
        for elem_id, elem_info in element_hierarchy.items():
            elem_name = elem_info["name"]
            hierarchy_map[elem_name] = elem_info

    # Process elements parents-before-children. A hierarchical element is
    # computed as parent × fraction, reading the parent's already-filled
    # values, so the parent MUST be evaluated first. The element list order is
    # arbitrary (e.g. "primary steel" may be listed before its parent "steel"),
    # so order by hierarchy depth: material=0, top-level=1, grandchildren=2, …
    # Without this, a child listed before its parent reads a still-zero parent
    # and collapses to 0 (all its downstream flows then stay 0 too).
    def _elem_depth(name):
        depth, cur, seen = 0, name, set()
        while cur and cur != "material" and cur not in seen:
            seen.add(cur)
            parent = (hierarchy_map.get(cur, {}) or {}).get("parent")
            if not parent or parent == "material":
                break
            cur, depth = parent, depth + 1
        return depth

    ordered_elems = sorted(
        ((i, e) for i, e in enumerate(elements) if e != "material"),
        key=lambda ie: _elem_depth(ie[1]),
    )

    for flow in mfa_system.FlowDict.values():
        material_values = flow.Values[:, mat_idx]

        # Skip flows with no material
        if not np.any(material_values != 0):
            continue

        # Calculate each element's values dynamically (parents before children)
        for elem_idx, element_name in ordered_elems:
            # Get parameter for this element-flow combination
            param_name = f"{element_name}_{flow.Name}"
            param = mfa_system.ParameterDict.get(param_name)

            if param is None:
                # No parameter found - element not defined for this flow
                # This is OK - not all elements need to be defined for all flows
                flow.Values[:, elem_idx] = 0.0
                continue

            # Determine parent element for hierarchical calculation
            elem_info = hierarchy_map.get(element_name, {})
            parent_element = elem_info.get("parent", "material")

            if parent_element is None or parent_element == "material":
                # Top-level element: calculate as % of material
                parent_values = material_values
            else:
                # Hierarchical element: calculate as % of parent element
                try:
                    parent_idx = elements.index(parent_element)
                    parent_values = flow.Values[:, parent_idx]
                except ValueError:
                    # Parent element not found - fallback to material
                    print(
                        f"[WARNING] Parent element '{parent_element}' for '{element_name}' not found. Using material instead."
                    )
                    parent_values = material_values

            # Calculate: element_mass = parent_mass * fraction
            fraction = param.Values
            flow.Values[:, elem_idx] = parent_values * fraction

        # Validate only TOP-LEVEL elements sum to <= material mass
        # Build list of top-level element indices
        top_level_indices = []
        for elem_idx, element_name in enumerate(elements):
            if element_name == "material":
                continue
            elem_info = hierarchy_map.get(element_name, {})
            parent = elem_info.get("parent", "material")
            if parent is None or parent == "material":
                top_level_indices.append(elem_idx)

        if top_level_indices:
            # Sum only top-level elements
            element_sum = np.sum(flow.Values[:, top_level_indices], axis=1)
            material_total = flow.Values[:, mat_idx]

            if np.any(element_sum > material_total * 1.01):
                max_overshoot = np.max(element_sum - material_total)
                if max_overshoot > 0.1:  # Only warn if significant (>0.1 Mg)
                    top_level_names = [elements[i] for i in top_level_indices]
                    print(
                        f"[WARNING] {flow.Name}: Top-level element sum exceeds material mass by {max_overshoot:.3f} Mg"
                    )
                    print(f"    Top-level elements: {top_level_names}")
                    print("    Check fraction values sum to ≤ 1.0")


#: Canonical Process_Logic values the engine dispatches on. Excel input is
#: normalized against this list (whitespace-stripped, case-insensitive) so a
#: trailing space or "fomp" instead of "FOMP" cannot silently disable a module.
_KNOWN_PROCESS_LOGICS = (
    "Input",
    "Output",
    "Splitter",
    "Transformer",
    "Pass-through",
    "DSM",
    "DSM_Component",
    "FOMP",
    "LFG",
    "BOM_Assembler",
    "FlowCap",
)
_LOGIC_LOOKUP = {logic.lower(): logic for logic in _KNOWN_PROCESS_LOGICS}


def _normalize_process_logic_map(process_logic_map):
    """Strip and canonicalize Process_Logic strings; warn on unknown values."""
    normalized = {}
    for process_id, logic in process_logic_map.items():
        if isinstance(logic, str):
            stripped = logic.strip()
            canonical = _LOGIC_LOOKUP.get(stripped.lower())
            if canonical is not None:
                if canonical != logic:
                    normalized[process_id] = canonical
                    continue
            elif stripped:
                print(
                    f"[WARNING] Process {process_id}: unrecognized Process_Logic "
                    f"'{logic}' — known values: {', '.join(_KNOWN_PROCESS_LOGICS)}."
                )
            normalized[process_id] = stripped
        else:
            normalized[process_id] = logic
    return normalized


def _create_flow_and_process_maps(mfa_system, all_excel_data, debug_mode=False):
    """Creates lookup maps for process logic and flow-to-TC mappings.

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        The MFA system, used to get the list of elements.
    all_excel_data : dict
        Dictionary of all data read from Excel.
    debug_mode : bool, optional
        If True, print detailed mapping progress. Default is False.

    Returns
    -------
    tuple
        A tuple containing:
        - flow_tc_map (dict): Maps Flow_IDs to their corresponding TC_IDs.
        - process_logic_map (dict): Maps Process_IDs to their Process_Logic.
    """
    process_definitions = all_excel_data.get("2_1_Definition_Processes")
    process_logic_map = {}
    if process_definitions is not None:
        process_logic_map = _normalize_process_logic_map(
            process_definitions.set_index("ID")["Process_Logic"].to_dict()
        )

    if debug_mode:
        print("--> Creating Flow-to-TC mapping...")
    flow_tc_map = {}

    # Detect TC column format (old: TC_material_ID, new: E1_TC_ID)
    tc_format = "old"  # default
    static_tc_definitions = all_excel_data.get("2_2_static_TCs")
    if static_tc_definitions is not None and not static_tc_definitions.empty:
        if (
            "E1_TC_ID" in static_tc_definitions.columns
            or "E2_TC_ID" in static_tc_definitions.columns
        ):
            tc_format = "new"
            if debug_mode:
                print("  -> Detected new E# format for TC mapping")
        else:
            if debug_mode:
                print("  -> Detected legacy element-name format for TC mapping")

    if static_tc_definitions is not None:
        static_tc_definitions_filtered = static_tc_definitions.dropna(
            subset=["Flow_ID"]
        )
        for _, row in static_tc_definitions_filtered.iterrows():
            flow_id = row["Flow_ID"]
            tc_ids = {}
            for elem_idx, element in enumerate(mfa_system.Elements):
                # Build column name based on format
                if tc_format == "new":
                    element_id = elem_idx + 1
                    tc_id_col = f"E{element_id}_TC_ID"
                else:
                    tc_id_col = f"TC_{element}_ID"

                if tc_id_col in row and pd.notna(row[tc_id_col]):
                    tc_ids[element] = row[tc_id_col]
            flow_tc_map[flow_id] = tc_ids

    dynamic_tc_definitions = all_excel_data.get("2_3_dynamic_TCs")
    if dynamic_tc_definitions is not None:
        # Detect format for dynamic TCs (might be different from static)
        dynamic_tc_format = "old"
        if not dynamic_tc_definitions.empty:
            if (
                "E1_TC_ID" in dynamic_tc_definitions.columns
                or "E2_TC_ID" in dynamic_tc_definitions.columns
            ):
                dynamic_tc_format = "new"

        dynamic_tc_definitions_filtered = dynamic_tc_definitions.dropna(
            subset=["Flow_ID"]
        )
        for _, row in dynamic_tc_definitions_filtered.iterrows():
            flow_id = row["Flow_ID"]
            if flow_id not in flow_tc_map:
                flow_tc_map[flow_id] = {}
            tc_ids = flow_tc_map[flow_id]
            for elem_idx, element in enumerate(mfa_system.Elements):
                # Build column name based on format
                if dynamic_tc_format == "new":
                    element_id = elem_idx + 1
                    tc_id_col = f"E{element_id}_TC_ID"
                else:
                    tc_id_col = f"TC_{element}_ID"

                if tc_id_col in row and pd.notna(row[tc_id_col]):
                    tc_ids[element] = row[tc_id_col]
            flow_tc_map[flow_id] = tc_ids

    if debug_mode:
        print(f"  -> Created TC mapping for {len(flow_tc_map)} flows")
    return flow_tc_map, process_logic_map


def define_flows_and_parameters(mfa_system, all_excel_data, debug_mode=False):
    """Orchestrates the definition of flows and all model parameters.

    This function calls a series of helper functions to perform the setup
    of all flows and parameters in a structured sequence.

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        The MFA system object to be configured.
    all_excel_data : dict
        Dictionary of all data read from Excel.
    debug_mode : bool, optional
        If True, print detailed setup progress. Default is False.

    Returns
    -------
    tuple
        A tuple containing:
        - mfa_system (odym.MFAsystem): The fully configured MFA system.
        - all_excel_data (dict): The same input data dictionary.
        - flow_tc_map (dict): A map from Flow_IDs to their TC_IDs.
        - process_logic_map (dict): A map from Process_IDs to their logic.
    """
    if debug_mode:
        print("--> Defining flows, parameters, and setting all initial values...")

    # Extract data sheets
    flow_definitions = all_excel_data["1_1_Definition_Flows"]
    flow_data = all_excel_data["1_2_Data_Flows"]

    # Step-by-step orchestration
    _initialize_flows(mfa_system, flow_definitions)
    _populate_primary_flow_data(mfa_system, flow_data, debug_mode=debug_mode)
    _apply_initial_stock(mfa_system, all_excel_data)
    _define_content_parameters(mfa_system, flow_definitions)

    # Initialize all parameter values using ODYM method with error handling
    try:
        mfa_system.Initialize_ParameterValues()
        if debug_mode:
            print("--> Parameter values initialized successfully.")
    except Exception as e:
        print(f"--> ERROR: Failed to initialize parameter values: {e}")
        raise

    # Load element hierarchy from config for hierarchical composition calculation
    element_hierarchy = {}
    try:
        # Read configuration sheet to extract Element_Hierarchy
        config_sheet = None
        for sheet_name in ["Configuration", "0_Configuration", "Config"]:
            if sheet_name in all_excel_data:
                config_sheet = all_excel_data[sheet_name]
                break

        if config_sheet is not None:
            # Parse Element_ID_X and Parent_Element_ID_X from config sheet
            element_structure = {}

            # Convert sheet to key-value pairs (Column B = key, Column C = value)
            for _, row in config_sheet.iterrows():
                if pd.notna(row.iloc[1]) and pd.notna(row.iloc[2]):
                    key = str(row.iloc[1]).strip()
                    value = row.iloc[2]

                    # First pass: collect Element_ID_X
                    if key.startswith("Element_ID_"):
                        try:
                            element_num = int(key.split("_")[-1])
                            if pd.notna(value) and str(value).strip():
                                element_structure[element_num] = {
                                    "name": str(value).strip(),
                                    "parent": None,
                                }
                        except (ValueError, IndexError):
                            continue

            # Second pass: collect Parent_Element_ID_X
            for _, row in config_sheet.iterrows():
                if pd.notna(row.iloc[1]) and pd.notna(row.iloc[2]):
                    key = str(row.iloc[1]).strip()
                    value = row.iloc[2]

                    if key.startswith("Parent_Element_ID_"):
                        try:
                            element_num = int(key.split("_")[-1])
                            if pd.notna(value) and str(value).strip():
                                if element_num in element_structure:
                                    element_structure[element_num]["parent"] = str(
                                        value
                                    ).strip()
                        except (ValueError, IndexError):
                            continue

            element_hierarchy = element_structure

            if element_hierarchy and debug_mode:
                print("--> Using hierarchical element calculation (Phase 5b)")
                for eid in sorted(element_hierarchy.keys()):
                    elem = element_hierarchy[eid]
                    if elem.get("parent"):
                        print(f"    {elem['name']} = {elem['parent']} × fraction")
    except Exception as e:
        print(
            f"[INFO] Could not load Element_Hierarchy: {e}. Using flat element structure."
        )

    # Store hierarchy on mfa_system for plotting and analysis
    # NOTE: This is a BioDYM extension (not part of standard ODYM)
    # The '_' prefix indicates custom attribute
    mfa_system._element_hierarchy = element_hierarchy

    # Which hierarchy nodes are fully accounted for by their tracked children.
    # Declared via the composition fractions, not inferred from results — see
    # _infer_exhaustive_elements. Consumed by the solver's hierarchy validation.
    mfa_system._exhaustive_elements = _infer_exhaustive_elements(
        all_excel_data, element_hierarchy, mfa_system.Elements
    )
    if debug_mode and mfa_system._exhaustive_elements:
        print(
            f"--> Exhaustive element nodes: "
            f"{sorted(mfa_system._exhaustive_elements)}"
        )

    _calculate_elemental_compositions(mfa_system, element_hierarchy)
    flow_tc_map, process_logic_map = _create_flow_and_process_maps(
        mfa_system, all_excel_data, debug_mode=debug_mode
    )

    # ODYM compliance: Check system consistency with error handling
    try:
        mfa_system.Consistency_Check()
        if debug_mode:
            print("--> Consistency check passed.")
    except Exception as e:
        print(f"--> ERROR: Consistency check failed: {e}")
        raise

    return mfa_system, all_excel_data, flow_tc_map, process_logic_map


def apply_scenario(
    mfa_system,
    scenario_definitions,
    selected_scenario_name,
    dsm_params=None,
    fomp_params=None,
    initial_stock_configs=None,
):
    """
    Applies the modifications for a selected scenario to the MFA system object.
    Now supports year-specific modifications using start_year and end_year.
    Extended to support DSM, FOMP, and Initial Stock parameter modifications.

    Args:
        mfa_system (odym.MFAsystem): The configured MFA system object.
        scenario_definitions (dict): All available scenario rules from the Excel file.
        selected_scenario_name (str): The name of the scenario to apply.
        dsm_params (dict, optional): DSM parameter configuration dictionary.
        fomp_params (dict, optional): FOMP parameter configuration dictionary.
        initial_stock_configs (dict, optional): Initial stock configuration dictionary.

    Returns:
        tuple: (mfa_system, dsm_params, fomp_params, initial_stock_configs) with modifications applied.
    """
    import copy

    # Create deep copies to avoid modifying originals
    dsm_params = copy.deepcopy(dsm_params) if dsm_params else {}
    fomp_params = copy.deepcopy(fomp_params) if fomp_params else {}
    initial_stock_configs = (
        copy.deepcopy(initial_stock_configs) if initial_stock_configs else {}
    )

    modifications = scenario_definitions.get(selected_scenario_name, [])

    for mod in modifications:
        param_name = mod["Parameter_Name"]

        # Auto-detect Parameter_Type from parameter name if not explicitly provided
        param_type = mod.get("Parameter_Type", "").strip()
        if not param_type:
            # Auto-detect based on parameter name patterns
            if "_DSM_" in param_name:
                param_type = "DSM"
            elif param_name.startswith("F_"):
                param_type = "Flow"
            elif param_name.startswith("TC_"):
                param_type = "TC"
            elif (
                "_IS_" in param_name
                or param_name.startswith("P")
                and "IS_" in param_name
            ):
                param_type = "IS"
            elif "decay_k" in param_name or "Inflow_fraction" in param_name:
                param_type = "FOMP"
            else:
                # Default to TC if no clear pattern (backwards compatibility)
                param_type = "TC"

        # Extract Process ID from parameter name (format: P##_...)
        # Prefer P##_ prefix extraction over ID column
        process_id = None
        if param_name.startswith("P") and "_" in param_name:
            # New format: P##_ prefix in parameter name
            try:
                process_id_str = param_name.split("_")[0][1:]  # Extract ## from P##
                process_id = int(process_id_str)
            except (ValueError, IndexError):
                pass  # Not a valid P##_ format

        # Fall back to ID column if no prefix found (backwards compatibility)
        if process_id is None:
            process_id = mod.get("ID", None)

        # Validate and clean operation field
        operation_raw = mod["Operation"]
        if pd.isna(operation_raw) or operation_raw == "":
            print(
                f"       WARNING: Empty operation for parameter '{param_name}'. Skipping."
            )
            continue
        operation = str(operation_raw).lower().strip()

        # Validate and clean value field
        value_raw = mod["New_Value"]
        if pd.isna(value_raw):
            print(
                f"       WARNING: Empty value for parameter '{param_name}'. Skipping."
            )
            continue
        value = float(value_raw)

        # Get year range (if specified)
        start_year = mod.get("start_year", None)
        end_year = mod.get("end_year", None)

        # Determine year range for modification
        if start_year is not None and end_year is not None:
            year_range_str = f" (years {start_year}-{end_year})"
        elif start_year is not None:
            year_range_str = f" (from year {start_year})"
        elif end_year is not None:
            year_range_str = f" (until year {end_year})"
        else:
            year_range_str = " (all years)"

        print(
            f"    -> Applying: {param_name} | Type: {param_type} | Operation: {operation} | Value: {value}{year_range_str}"
        )

        # Handle DSM parameter modifications
        if param_type == "DSM":
            if process_id is None:
                print(
                    f"       WARNING: DSM modification requires Process ID (use P##_ prefix). Skipping '{param_name}'."
                )
                continue

            process_id = int(process_id)
            if process_id not in dsm_params:
                print(
                    f"       WARNING: Process {process_id} not found in DSM parameters. Skipping."
                )
                continue

            # Strip P##_ prefix if present (e.g., "P06_DSM_Lifetime_Mean_Cat_1" -> "DSM_Lifetime_Mean_Cat_1")
            param_name_clean = param_name
            if param_name.startswith("P") and "_" in param_name:
                param_name_clean = "_".join(param_name.split("_")[1:])

            # Remove [%] from parameter name if present (e.g., "DSM_Inflow_Split_[%]_Cat_1" -> "DSM_Inflow_Split_Cat_1")
            param_name_clean = param_name_clean.replace("_[%]", "").replace("[%]", "")

            # Parse DSM parameter name (e.g., "DSM_Lifetime_Mean_Cat_1" or "DSM_Inflow_Split_Cat_1")
            if "_Cat_" in param_name_clean:
                parts = param_name_clean.split("_Cat_")
                param_base = parts[0]  # e.g., "DSM_Lifetime_Mean"
                category_idx = int(parts[1]) - 1  # Convert to 0-based index

                # Map parameter to DSM structure
                if param_base == "DSM_Lifetime_Mean":
                    _apply_operation(
                        dsm_params[process_id]["lifetimes"]["Mean"],
                        category_idx,
                        operation,
                        value,
                    )
                elif param_base == "DSM_Lifetime_StdDev":
                    _apply_operation(
                        dsm_params[process_id]["lifetimes"]["StdDev"],
                        category_idx,
                        operation,
                        value,
                    )
                elif param_base in ("DSM_Lifetime_Shape", "DSM_Lifetime_Scale"):
                    # Weibull parameters may be absent for non-Weibull categories —
                    # create the list on demand (same pattern as the MC engine)
                    key = "Shape" if param_base.endswith("Shape") else "Scale"
                    target = dsm_params[process_id]["lifetimes"].setdefault(
                        key,
                        [None] * len(dsm_params[process_id]["inflow_split"]),
                    )
                    if (
                        category_idx < len(target)
                        and target[category_idx] is None
                        and operation != "replace"
                    ):
                        print(
                            f"       WARNING: {param_base} Cat {category_idx + 1} has no "
                            f"baseline value — '{operation}' requires one. Use 'replace'. Skipping."
                        )
                    else:
                        _apply_operation(target, category_idx, operation, value)
                elif param_base == "DSM_Inflow_Split":
                    _apply_operation(
                        dsm_params[process_id]["inflow_split"],
                        category_idx,
                        operation,
                        value,
                    )
                elif param_base.startswith("DSM_Output_") and param_base.endswith(
                    "_Split"
                ):
                    # Extract output number (e.g., "DSM_Output_1_Split_Cat_2" -> output 0, cat 1)
                    output_num = int(param_base.split("_")[2]) - 1
                    if category_idx < len(dsm_params[process_id]["output_splits"]):
                        if output_num < len(
                            dsm_params[process_id]["output_splits"][category_idx]
                        ):
                            _apply_operation(
                                dsm_params[process_id]["output_splits"][category_idx],
                                output_num,
                                operation,
                                value,
                            )
                else:
                    print(
                        f"       WARNING: Unknown DSM parameter type '{param_base}'. Skipping."
                    )
            else:
                print(
                    f"       WARNING: DSM parameter '{param_name}' does not follow expected naming convention (P##_DSM_..._Cat_#). Skipping."
                )

        # Handle FOMP parameter modifications
        elif param_type == "FOMP":
            if process_id is None:
                print(
                    f"       WARNING: FOMP modification requires Process ID (use P##_ prefix). Skipping '{param_name}'."
                )
                continue

            process_id = int(process_id)
            if process_id not in fomp_params:
                print(
                    f"       WARNING: Process {process_id} not found in FOMP parameters. Skipping."
                )
                continue

            # Strip P##_ prefix if present (e.g., "P04_decay_k1" -> "decay_k1")
            param_name_clean = param_name
            if param_name.startswith("P") and "_" in param_name:
                param_name_clean = "_".join(param_name.split("_")[1:])

            # Find matching parameter in FOMP params (case-insensitive partial match)
            matched_key = None
            for key in fomp_params[process_id].keys():
                if param_name_clean.lower() in key.lower():
                    matched_key = key
                    break

            if matched_key:
                old_value = fomp_params[process_id][matched_key]
                if operation == "replace":
                    fomp_params[process_id][matched_key] = value
                elif operation == "multiply":
                    fomp_params[process_id][matched_key] = old_value * value
                elif operation == "add":
                    fomp_params[process_id][matched_key] = old_value + value
                print(
                    f"       -> Modified FOMP parameter '{matched_key}': {old_value} -> {fomp_params[process_id][matched_key]}"
                )
            else:
                print(
                    f"       WARNING: FOMP parameter '{param_name}' not found in Process {process_id}. Skipping."
                )

        # Handle Initial Stock parameter modifications
        elif param_type == "Initial Stock" or param_type == "IS":
            if process_id is None:
                print(
                    f"       WARNING: Initial Stock modification requires Process ID (use P##_ prefix). Skipping '{param_name}'."
                )
                continue

            process_id = int(process_id)
            if process_id not in initial_stock_configs:
                print(
                    f"       WARNING: Process {process_id} not found in Initial Stock configs. Skipping."
                )
                continue

            # Strip P##_ prefix if present (e.g., "P02_IS_material_quantity" -> "IS_material_quantity")
            param_name_clean = param_name
            if param_name.startswith("P") and "_" in param_name:
                param_name_clean = "_".join(param_name.split("_")[1:])

            # Map parameter name to internal structure
            param_mapping = {
                "IS_material_quantity[UoM]": "Initial_Stock_material",
                "IS_material_quantity": "Initial_Stock_material",
                "IS_E2_[%](WC)": "Initial_Stock_WC[%]",
                "IS_WC[%]": "Initial_Stock_WC[%]",
                "IS_E3_[%](DM)": "Initial_Stock_DM[%]",
                "IS_DM[%]": "Initial_Stock_DM[%]",
                "IS_E4_[%](CC)": "Initial_Stock_CC[%]",
                "IS_CC[%]": "Initial_Stock_CC[%]",
            }

            internal_param_name = param_mapping.get(param_name_clean, None)
            if internal_param_name is None:
                # Generic patterns for any element name (TC, Ash_content, …):
                # "IS_E{n}_[%]({elem})" or "IS_{elem}[%]" → "Initial_Stock_{elem}[%]"
                import re as _re

                m = _re.match(r"IS_E\d+_\[%\]\((.+)\)$", param_name_clean) or _re.match(
                    r"IS_(.+)\[%\]$", param_name_clean
                )
                if m:
                    internal_param_name = f"Initial_Stock_{m.group(1)}[%]"
            if internal_param_name is None:
                print(
                    f"       WARNING: Unknown Initial Stock parameter '{param_name_clean}'. Skipping."
                )
                continue

            # Legacy TC/CC naming: the config may store the carbon fraction
            # under either element name — try the sibling before giving up.
            if (
                internal_param_name
                not in initial_stock_configs[process_id]["initial_stock_values"]
            ):
                for _a, _b in (("CC", "TC"), ("TC", "CC")):
                    _alt = internal_param_name.replace(f"_{_a}[", f"_{_b}[")
                    if (
                        _alt != internal_param_name
                        and _alt
                        in initial_stock_configs[process_id]["initial_stock_values"]
                    ):
                        internal_param_name = _alt
                        break

            if (
                internal_param_name
                in initial_stock_configs[process_id]["initial_stock_values"]
            ):
                old_value = initial_stock_configs[process_id]["initial_stock_values"][
                    internal_param_name
                ]
                if operation == "replace":
                    initial_stock_configs[process_id]["initial_stock_values"][
                        internal_param_name
                    ] = value
                elif operation == "multiply":
                    initial_stock_configs[process_id]["initial_stock_values"][
                        internal_param_name
                    ] = old_value * value
                elif operation == "add":
                    initial_stock_configs[process_id]["initial_stock_values"][
                        internal_param_name
                    ] = old_value + value
                print(
                    f"       -> Modified IS parameter '{internal_param_name}': {old_value} -> {initial_stock_configs[process_id]['initial_stock_values'][internal_param_name]}"
                )
            else:
                print(
                    f"       WARNING: Initial Stock parameter '{internal_param_name}' not found in Process {process_id}. Skipping."
                )

        # Handle Flow modifications (existing logic)
        elif param_name.startswith("F_") and param_name in mfa_system.FlowDict:
            flow_obj = mfa_system.FlowDict[param_name]

            # Get time indices for year range
            time_indices = _get_time_indices_for_year_range(
                mfa_system, start_year, end_year
            )

            # Skip if no valid time indices
            if len(time_indices) == 0:
                continue

            if operation == "replace":
                flow_obj.Values[time_indices, 0] = float(value)
            elif operation == "multiply":
                flow_obj.Values[time_indices, 0] *= float(value)
            elif operation == "add":
                flow_obj.Values[time_indices, 0] += float(value)
            else:
                print(
                    f"       WARNING: Unknown operation '{operation}' for Flow {param_name}"
                )

        elif param_name in mfa_system.ParameterDict:
            param_obj = mfa_system.ParameterDict[param_name]
            is_dynamic = isinstance(param_obj.Values, np.ndarray)

            if is_dynamic:
                # For dynamic parameters, apply year-specific modifications
                time_indices = _get_time_indices_for_year_range(
                    mfa_system, start_year, end_year
                )

                # Skip if no valid time indices
                if len(time_indices) == 0:
                    continue

                if operation == "replace":
                    param_obj.Values[time_indices] = float(value)
                elif operation == "multiply":
                    param_obj.Values[time_indices] *= float(value)
                elif operation == "add":
                    param_obj.Values[time_indices] += float(value)
                else:
                    print(
                        f"       WARNING: Unknown operation '{operation}' for Parameter {param_name}"
                    )
            else:
                # For static parameters, check if year range is specified
                if start_year is not None or end_year is not None:
                    print(
                        f"       WARNING: Parameter '{param_name}' is static but year range specified ({start_year}-{end_year}). Static parameters apply to all years."
                    )

                # For static parameters, apply to all values (backward compatibility)
                if operation == "replace":
                    param_obj.Values = float(value)
                elif operation == "multiply":
                    param_obj.Values *= float(value)
                elif operation == "add":
                    param_obj.Values += float(value)
                else:
                    print(
                        f"       WARNING: Unknown operation '{operation}' for Parameter {param_name}"
                    )

        else:
            print(
                f"       WARNING: Parameter or Flow '{param_name}' not found in the system."
            )

    print("\n    -> Recalculating elemental compositions for modified flows...")
    # Content-fraction parameters are PARENT-relative (same semantics as the
    # depth-ordered composition pass at setup): an element's fraction refers
    # to its parent in the element hierarchy, not to material. Recalculate
    # depth-ordered (parents before children) against the parent's value so
    # nested trees stay consistent. For flat hierarchies (every element a
    # child of material) this reduces exactly to the previous behaviour.
    elements = mfa_system.Elements
    element_hierarchy = getattr(mfa_system, "_element_hierarchy", {}) or {}
    parent_of = {}
    for info in element_hierarchy.values():
        name, parent = info.get("name"), info.get("parent")
        if name and parent:
            parent_of[name] = parent

    def _depth(element_name):
        depth, parent = 0, parent_of.get(element_name)
        while parent is not None and parent != "material":
            depth += 1
            parent = parent_of.get(parent)
        return depth

    ordered_elements = sorted(
        ((i, el) for i, el in enumerate(elements[1:], 1)),
        key=lambda item: _depth(item[1]),
    )
    elem_index = {el: i for i, el in enumerate(elements)}

    for flow in mfa_system.FlowDict.values():
        for i_elem, element_name in ordered_elements:
            param_name = f"{element_name}_{flow.Name}"
            if param_name in mfa_system.ParameterDict:
                content_value = mfa_system.ParameterDict[param_name].Values
                parent = parent_of.get(element_name)
                if parent and parent != "material" and parent in elem_index:
                    base = flow.Values[:, elem_index[parent]]
                else:
                    base = flow.Values[:, 0]
                flow.Values[:, i_elem] = base * content_value

    print("\n✅ Scenario modifications applied successfully.")
    return mfa_system, dsm_params, fomp_params, initial_stock_configs


def _apply_operation(target_list, index, operation, value):
    """Helper function to apply an operation to a list element.

    Args:
        target_list: The list containing the value to modify
        index: The index of the element to modify
        operation: Operation to perform ('replace', 'multiply', 'add')
        value: The value to use in the operation
    """
    if index >= len(target_list):
        print(
            f"       WARNING: Index {index} out of range for list of length {len(target_list)}. Skipping."
        )
        return

    old_value = target_list[index]
    if operation == "replace":
        target_list[index] = value
    elif operation == "multiply":
        target_list[index] = old_value * value
    elif operation == "add":
        target_list[index] = old_value + value

    print(f"       -> Modified list[{index}]: {old_value} -> {target_list[index]}")


def _get_time_indices_for_year_range(mfa_system, start_year, end_year):
    """
    Get time indices for a specific year range.

    Args:
        mfa_system: MFA system object
        start_year: Start year (None means from beginning)
        end_year: End year (None means to end)

    Returns:
        numpy array of time indices
    """
    time_items = mfa_system.IndexTable.Classification["Time"].Items

    # Validate year range
    if start_year is not None and end_year is not None and start_year > end_year:
        print(
            f"       WARNING: start_year ({start_year}) > end_year ({end_year}). Skipping modification."
        )
        return np.array([])

    if start_year is None and end_year is None:
        # Apply to all years
        return np.arange(len(time_items))

    # Find start index
    if start_year is None:
        start_idx = 0
    else:
        start_idx = None
        for i, year in enumerate(time_items):
            if year >= start_year:
                start_idx = i
                break
        if start_idx is None:
            print(
                f"       WARNING: start_year ({start_year}) is beyond the model time range ({time_items[0]}-{time_items[-1]}). Skipping modification."
            )
            return np.array([])

    # Find end index
    if end_year is None:
        end_idx = len(time_items)
    else:
        end_idx = None
        for i, year in enumerate(time_items):
            if year > end_year:
                end_idx = i
                break
        if end_idx is None:
            end_idx = len(time_items)  # Beyond range

    # Validate that we have a valid range
    if start_idx >= end_idx:
        print(
            f"       WARNING: No valid time indices found for year range {start_year}-{end_year}. Skipping modification."
        )
        return np.array([])

    # Return indices for the year range
    return np.arange(start_idx, end_idx)
