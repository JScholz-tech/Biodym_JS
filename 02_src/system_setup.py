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
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
odym_path = os.path.join(
    project_root, "06_framework", "ODYM-master_20241127", "odym", "modules"
)
if odym_path not in sys.path:
    sys.path.insert(0, odym_path)

# These are imported by main.py and are available in this namespace
import ODYM_Classes as msc
import data_loader


def define_model_scope(start_year, end_year, elements, regions=None, goods=None, materials=None, processes=None):
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
    classifications = [
        model_classification["Time"],
        model_classification["Element"]
    ]
    
    # Phase 1b: Add Material if defined (for future use)
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

    index_table = pd.DataFrame({
        "Aspect": aspects,
        "Description": descriptions,
        "Dimension": dimensions,
        "Classification": classifications,
        "IndexLetter": index_letters,
    })
    index_table.set_index("Aspect", inplace=True)

    print(f"--> Model scope and classifications defined with {len(aspects)} dimensions.")
    return model_classification, index_table


def initialize_mfa_system(model_classification, index_table):
    """Initializes the main MFAsystem object based on the defined scope.

    Parameters
    ----------
    model_classification : dict
        The ModelClassification dictionary created by `define_model_scope`.
    index_table : pd.DataFrame
        The IndexTable DataFrame created by `define_model_scope`.

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
        Unit="Mg",
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
        print("--> IndexTable validation passed.")
    except ValueError as e:
        print(f"--> WARNING: IndexTable validation failed: {e}")
        raise

    print("--> MFA system object initialized.")
    return mfa_system


def load_and_define_processes(mfa_system, input_data, data_loader):
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

    Returns
    -------
    tuple
        A tuple containing:
        - mfa_system (odym.MFAsystem): The modified MFAsystem object.
        - all_excel_data (dict): The dictionary of all data read from Excel.
    """
    print("--> Defining process and stock structures...")

    # Accept either a pre-loaded dict of DataFrames or a path to an Excel file
    if isinstance(input_data, dict):
        all_excel_data = input_data
    else:
        # Load all sheets into a dict; tests may patch pd.read_excel to return a dict
        all_excel_data = pd.read_excel(
            input_data,
            sheet_name=None,
            header=0,
            engine="openpyxl",
            na_values=["N.A.", "NA", "n/a"],
            decimal=',',
        )

    data_loader.validate_input_data(all_excel_data)

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
                should_create_stock = (stock_config == "Stock")
            
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
                    is_fomp_process = (process_logic == "FOMP" or fomp_legacy) and (not fomp_processes.empty)
                
                if is_fomp_process:
                    mfa_system.StockDict[f"S_{process_id}"]._fomp_process = True

    for stock_name, stock_obj in mfa_system.StockDict.items():
        # Mark FOMP processes for ODYM initialization (no manual np.zeros)
        if hasattr(stock_obj, '_fomp_process') and stock_obj._fomp_process:
            # Leave Values as None - ODYM's Initialize_StockValues() will handle this
            delattr(stock_obj, '_fomp_process')

    # Initialize stock values using ODYM method with error handling
    try:
        mfa_system.Initialize_StockValues()
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
    tc_data = dynamic_tc_data[['TC_material_ID', 'TC_Value_material', 'Year']].dropna()
    
    if tc_data.empty:
        print("  -> No valid TC data found in 2_4_dynamic_tcs format")
        return {}
    
    # Group by TC_ID and create time series
    dynamic_tc_dict = {}
    unique_tc_ids = tc_data['TC_material_ID'].unique()
    
    for tc_id in unique_tc_ids:
        tc_points = tc_data[tc_data['TC_material_ID'] == tc_id]
        
        # Create time series
        ts = pd.Series(tc_points['TC_Value_material'].values, index=tc_points['Year'])
        
        # Reindex to full time vector and interpolate
        ts_full = ts.reindex(time_vector)
        ts_interpolated = ts_full.interpolate(method="linear", limit_direction="both")
        
        # Handle edge cases where interpolation might fail
        if ts_interpolated.isna().any():
            # Fill remaining NaN values with the nearest available value
            ts_interpolated = ts_interpolated.ffill().bfill()
        
        dynamic_tc_dict[tc_id] = ts_interpolated.to_numpy()
        
        print(f"  -> Created time series for {tc_id}: {len(tc_points)} data points -> {len(ts_interpolated)} time steps")

    print(f"--> Generated {len(dynamic_tc_dict)} dynamic TC parameter(s) from 2_4 format.")
    return dynamic_tc_dict


def create_dynamic_tc_parameters(dynamic_tc_data, time_vector):
    """
    Generates time series for TCs, with data cleaning and validation.
    """
    print("--> Generating dynamic TC time series via interpolation...")
    required_cols = ["TC_ID", "Year", "Value"]
    if not all(col in dynamic_tc_data.columns for col in required_cols):
        raise ValueError(f"The '2_5_dynamic_tcs' sheet is missing one of the required columns: {required_cols}.")

    cleaned_data = dynamic_tc_data.dropna(subset=["TC_ID", "Year"])
    duplicates = cleaned_data[cleaned_data.duplicated(subset=["TC_ID", "Year"], keep=False)]
    if not duplicates.empty:
        raise ValueError(f"Duplicate entries found for the same TC in the same year in '2_5_dynamic_tcs'. Conflicting rows:\n{duplicates.sort_values(by=['TC_ID', 'Year'])}")

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
        if pd.notna(row["Flow_Name"]):
            start_id, end_id = int(row["Flow_Output_Process_ID"]), int(row["Input_Process_ID"])
            flow_obj = msc.Flow(Name=row["Flow_ID"], P_Start=start_id, P_End=end_id, Indices="t,e")
            flow_id = row["Flow_ID"]
            
            # Store descriptive name in external dict (ODYM compliance - no custom attributes)
            flow_descriptions[flow_id] = row["Flow_Name"]
            
            mfa_system.FlowDict[flow_id] = flow_obj
    
    # Store flow descriptions in mfa_system for later use (external to Flow objects)
    mfa_system._flow_descriptions = flow_descriptions
    
    # Initialize flow values using ODYM method with error handling
    try:
        mfa_system.Initialize_FlowValues()
        print("--> All flows initialized to zero.")
    except Exception as e:
        print(f"--> ERROR: Failed to initialize flow values: {e}")
        print(f"    Flow count: {len(flow_descriptions)} flows defined")
        raise

def _populate_primary_flow_data(mfa_system, flow_data):
    """Populates flows with primary data from the '1_2_Data_Flows' sheet.

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        The MFA system object to be modified.
    flow_data : pd.DataFrame
        DataFrame containing the flow data from Excel.
    """
    for flow_id, flow_obj in mfa_system.FlowDict.items():
        if flow_id in flow_data["Flow_ID"].values:
            flow_time_series = flow_data[flow_data["Flow_ID"] == flow_id]
            if len(flow_time_series) == len(mfa_system.IndexTable.Classification['Time'].Items):
                flow_obj.Values[:, 0] = np.array(flow_time_series["Flow_Material"]).ravel()
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
    initial_stock_configs = data_loader.load_initial_stock_parameters(all_excel_data)
    if initial_stock_configs:
        from engine import initial_stock_engine
        mfa_system = initial_stock_engine.apply_initial_stock_values(mfa_system, initial_stock_configs)
        mfa_system = initial_stock_engine.process_initial_stock_outflows(mfa_system, initial_stock_configs)

def _define_content_parameters(mfa_system, content_definitions):
    """Defines content parameters (e.g., water content) for each flow.

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        The MFA system object to be modified.
    content_definitions : pd.DataFrame
        DataFrame containing flow definitions, including content percentages.
    """
    parameter_id_counter = 1
    for _, row in content_definitions.iterrows():
        flow_id = row.get("Flow_ID")
        if pd.notna(flow_id) and flow_id in mfa_system.FlowDict:
            element_column_map = {
                "WC": "Flow_WC[%]",
                "DM": "Flow_DM[%]", 
                "CC": "Flow_CC_DM[%]"
            }
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
                        Unit="1"
                    )
                    parameter_id_counter += 1

def _calculate_elemental_compositions(mfa_system):
    """Calculates elemental values for flows based on content parameters.

    Iterates through flows and applies the defined content percentages (e.g., WC, DM)
    to the primary material flow to calculate the values for each element.

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        The MFA system object to be modified.
    """
    for flow in mfa_system.FlowDict.values():
        if np.any(flow.Values[:, 0] != 0):
            for i_elem, element_name in enumerate(mfa_system.Elements[1:], 1):
                if element_name == "CC": continue
                param_name = f"{element_name}_{flow.Name}"
                if param_name in mfa_system.ParameterDict:
                    content_value = mfa_system.ParameterDict[param_name].Values
                    flow.Values[:, i_elem] = flow.Values[:, 0] * content_value
            if "CC" in mfa_system.Elements:
                cc_idx = mfa_system.Elements.index("CC")
                param_name = f"CC_{flow.Name}"
                if param_name in mfa_system.ParameterDict:
                    cc_fraction = mfa_system.ParameterDict[param_name].Values
                    flow.Values[:, cc_idx] = flow.Values[:, 0] * cc_fraction

def _create_flow_and_process_maps(mfa_system, all_excel_data):
    """Creates lookup maps for process logic and flow-to-TC mappings.

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        The MFA system, used to get the list of elements.
    all_excel_data : dict
        Dictionary of all data read from Excel.

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
        process_logic_map = process_definitions.set_index('ID')['Process_Logic'].to_dict()

    print("--> Creating Flow-to-TC mapping...")
    flow_tc_map = {}
    static_tc_definitions = all_excel_data.get("2_2_static_TCs")
    if static_tc_definitions is not None:
        static_tc_definitions_filtered = static_tc_definitions.dropna(subset=['Flow_ID'])
        for _, row in static_tc_definitions_filtered.iterrows():
            flow_id = row["Flow_ID"]
            tc_ids = {}
            for element in mfa_system.Elements:
                tc_id_col = f"TC_{element}_ID"
                if tc_id_col in row and pd.notna(row[tc_id_col]):
                    tc_ids[element] = row[tc_id_col]
            flow_tc_map[flow_id] = tc_ids
    
    dynamic_tc_definitions = all_excel_data.get("2_3_dynamic_TCs")
    if dynamic_tc_definitions is not None:
        dynamic_tc_definitions_filtered = dynamic_tc_definitions.dropna(subset=['Flow_ID'])
        for _, row in dynamic_tc_definitions_filtered.iterrows():
            flow_id = row["Flow_ID"]
            if flow_id not in flow_tc_map:
                flow_tc_map[flow_id] = {}
            tc_ids = flow_tc_map[flow_id]
            for element in mfa_system.Elements:
                tc_id_col = f"TC_{element}_ID"
                if tc_id_col in row and pd.notna(row[tc_id_col]):
                    tc_ids[element] = row[tc_id_col]
            flow_tc_map[flow_id] = tc_ids
    return flow_tc_map, process_logic_map

def define_flows_and_parameters(mfa_system, all_excel_data):
    """Orchestrates the definition of flows and all model parameters.

    This function calls a series of helper functions to perform the setup
    of all flows and parameters in a structured sequence.

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        The MFA system object to be configured.
    all_excel_data : dict
        Dictionary of all data read from Excel.

    Returns
    -------
    tuple
        A tuple containing:
        - mfa_system (odym.MFAsystem): The fully configured MFA system.
        - all_excel_data (dict): The same input data dictionary.
        - flow_tc_map (dict): A map from Flow_IDs to their TC_IDs.
        - process_logic_map (dict): A map from Process_IDs to their logic.
    """
    print("--> Defining flows, parameters, and setting all initial values...")

    # Extract data sheets
    flow_definitions = all_excel_data["1_1_Definition_Flows"]
    flow_data = all_excel_data["1_2_Data_Flows"]

    # Step-by-step orchestration
    _initialize_flows(mfa_system, flow_definitions)
    _populate_primary_flow_data(mfa_system, flow_data)
    _apply_initial_stock(mfa_system, all_excel_data)
    _define_content_parameters(mfa_system, flow_definitions)
    
    # Initialize all parameter values using ODYM method with error handling
    try:
        mfa_system.Initialize_ParameterValues()
        print("--> Parameter values initialized successfully.")
    except Exception as e:
        print(f"--> ERROR: Failed to initialize parameter values: {e}")
        raise
    
    _calculate_elemental_compositions(mfa_system)
    flow_tc_map, process_logic_map = _create_flow_and_process_maps(mfa_system, all_excel_data)

    # ODYM compliance: Check system consistency with error handling
    try:
        mfa_system.Consistency_Check()
        print("--> Consistency check passed.")
    except Exception as e:
        print(f"--> ERROR: Consistency check failed: {e}")
        raise
    
    return mfa_system, all_excel_data, flow_tc_map, process_logic_map

def apply_scenario(mfa_system, scenario_definitions, selected_scenario_name):
    """
    Applies the modifications for a selected scenario to the MFA system object.
    Now supports year-specific modifications using start_year and end_year.

    Args:
        mfa_system (odym.MFAsystem): The configured MFA system object.
        scenario_definitions (dict): All available scenario rules from the Excel file.
        selected_scenario_name (str): The name of the scenario to apply.

    Returns:
        odym.MFAsystem: The MFA system with scenario modifications applied.
    """
    modifications = scenario_definitions.get(selected_scenario_name, [])

    for mod in modifications:
        param_name = mod['Parameter_Name']
        
        # Validate and clean operation field
        operation_raw = mod['Operation']
        if pd.isna(operation_raw) or operation_raw == '':
            print(f"       WARNING: Empty operation for parameter '{param_name}'. Skipping.")
            continue
        operation = str(operation_raw).lower().strip()
        
        # Validate and clean value field
        value_raw = mod['New_Value']
        if pd.isna(value_raw):
            print(f"       WARNING: Empty value for parameter '{param_name}'. Skipping.")
            continue
        value = float(value_raw)
        
        # Get year range (if specified)
        start_year = mod.get('start_year', None)
        end_year = mod.get('end_year', None)
        
        # Determine year range for modification
        if start_year is not None and end_year is not None:
            year_range_str = f" (years {start_year}-{end_year})"
        elif start_year is not None:
            year_range_str = f" (from year {start_year})"
        elif end_year is not None:
            year_range_str = f" (until year {end_year})"
        else:
            year_range_str = " (all years)"

        print(f"    -> Applying: {param_name} | Operation: {operation} | Value: {value}{year_range_str}")

        if param_name.startswith('F_') and param_name in mfa_system.FlowDict:
            flow_obj = mfa_system.FlowDict[param_name]
            
            # Get time indices for year range
            time_indices = _get_time_indices_for_year_range(mfa_system, start_year, end_year)
            
            # Skip if no valid time indices
            if len(time_indices) == 0:
                continue
            
            if operation == 'replace':
                flow_obj.Values[time_indices, 0] = float(value)
            elif operation == 'multiply':
                flow_obj.Values[time_indices, 0] *= float(value)
            elif operation == 'add':
                flow_obj.Values[time_indices, 0] += float(value)
            else:
                print(f"       WARNING: Unknown operation '{operation}' for Flow {param_name}")

        elif param_name in mfa_system.ParameterDict:
            param_obj = mfa_system.ParameterDict[param_name]
            is_dynamic = isinstance(param_obj.Values, np.ndarray)

            if is_dynamic:
                # For dynamic parameters, apply year-specific modifications
                time_indices = _get_time_indices_for_year_range(mfa_system, start_year, end_year)
                
                # Skip if no valid time indices
                if len(time_indices) == 0:
                    continue
                
                if operation == 'replace':
                    param_obj.Values[time_indices] = float(value)
                elif operation == 'multiply':
                    param_obj.Values[time_indices] *= float(value)
                elif operation == 'add':
                    param_obj.Values[time_indices] += float(value)
                else:
                    print(f"       WARNING: Unknown operation '{operation}' for Parameter {param_name}")
            else:
                # For static parameters, check if year range is specified
                if start_year is not None or end_year is not None:
                    print(f"       WARNING: Parameter '{param_name}' is static but year range specified ({start_year}-{end_year}). Static parameters apply to all years.")
                
                # For static parameters, apply to all values (backward compatibility)
                if operation == 'replace':
                    param_obj.Values = float(value)
                elif operation == 'multiply':
                    param_obj.Values *= float(value)
                elif operation == 'add':
                    param_obj.Values += float(value)
                else:
                    print(f"       WARNING: Unknown operation '{operation}' for Parameter {param_name}")
        
        else:
            print(f"       WARNING: Parameter or Flow '{param_name}' not found in the system.")

    print("\n    -> Recalculating elemental compositions for modified flows...")
    for flow in mfa_system.FlowDict.values():
        for i_elem, element_name in enumerate(mfa_system.Elements[1:], 1):
            param_name = f"{element_name}_{flow.Name}"
            if param_name in mfa_system.ParameterDict:
                content_value = mfa_system.ParameterDict[param_name].Values
                flow.Values[:, i_elem] = flow.Values[:, 0] * content_value

    print("\n✅ Scenario modifications applied successfully.")
    return mfa_system


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
        print(f"       WARNING: start_year ({start_year}) > end_year ({end_year}). Skipping modification.")
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
            print(f"       WARNING: start_year ({start_year}) is beyond the model time range ({time_items[0]}-{time_items[-1]}). Skipping modification.")
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
        print(f"       WARNING: No valid time indices found for year range {start_year}-{end_year}. Skipping modification.")
        return np.array([])
    
    # Return indices for the year range
    return np.arange(start_idx, end_idx)
