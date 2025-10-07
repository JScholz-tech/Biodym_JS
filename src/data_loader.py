# -*- coding: utf-8 -*-
"""
Data Loader Module for the BioDYM MFA Model.

This file contains all functions responsible for reading, validating, and
parsing the input data from the Excel template file. It acts as the
interface between the raw data and the core model logic.
"""

import pandas as pd
import numpy as np
import ODYM_Classes as msc


def validate_input_data(excel_data_dict):
    """
    Checks if the loaded Excel data has the expected structure.
    Raises a ValueError with a clear error message if something is missing.

    Args:
        excel_data_dict (dict): A dictionary where keys are sheet names and
                                values are pandas DataFrames.
    """
    print("--> Validating input data structure...")

    # Define the minimum required structure for the model to run.
    REQUIRED_STRUCTURE = {
        "1_1_Definition_Flows": ["Flow_ID", "Flow_Name", "Flow_Output_Process_ID", "Input_Process_ID"],
        "1_2_Data_Flows": ["Flow_ID", "Flow_Data_Year", "Flow_Material"],
        "2_1_Definition_Processes": ["ID", "Process_Name", "Process_Logic", "TC?", "TC_Type"],
        "2_3_static_TCs": ["Flow_ID", "Process_ID", "TC_material_ID", "TC_Value_material"],
        "2_4_dynamic_TCs": ["TC_material_ID", "TC_Value_material", "Year"],
        "2_5_Initial_Stock": [
            "Process_ID",
            "Initial_Stock_material",
            "Initial_Stock_WC[%]",
            "Initial_Stock_DM[%]",
            "Initial_Stock_CC[%]",
        ],
    }

    for sheet_name, required_columns in REQUIRED_STRUCTURE.items():
        if sheet_name not in excel_data_dict:
            # TC sheets are optional - only required if processes use TCs
            if sheet_name in ["2_3_static_TCs", "2_4_dynamic_TCs"]:
                print(f"  -> Optional sheet '{sheet_name}' not found (TCs may not be used)")
                continue
            else:
                raise ValueError(
                    f"ERROR: The required sheet '{sheet_name}' was not found in the Excel file!"
                )

        existing_columns = excel_data_dict[sheet_name].columns
        for col in required_columns:
            if col not in existing_columns:
                raise ValueError(
                    f"ERROR: The required column '{col}' is missing from sheet '{sheet_name}'!"
                )

    print("--> Input data validation successful.")


def load_tc_parameters(all_excel_data, elements, time_vector):
    """
    Loads transfer coefficients based on the new unified structure.
    Uses TC_Type column to determine whether to load static or dynamic TCs.
    
    Process Definition Sheet Logic:
    - TC? = "Yes" and TC_Type = "Static" -> Load from 2_3_static_TCs
    - TC? = "Yes" and TC_Type = "Dynamic" -> Load from 2_4_dynamic_TCs
    - TC? = "No" -> Skip TCs for this process

    Args:
        all_excel_data (dict): Dictionary of DataFrames from Excel.
        elements (list): List of element names (e.g., ['material', 'WC', 'DM', 'CC']).
        time_vector (list): List of years for the analysis.

    Returns:
        dict: A dictionary of ODYM Parameter objects for all TCs.
    """
    print("--> Loading Transfer Coefficients using unified TC_Type logic...")
    
    process_defs = all_excel_data.get('2_1_Definition_Processes')
    static_tc_defs = all_excel_data.get('2_3_static_TCs')
    dynamic_tc_defs = all_excel_data.get('2_4_dynamic_TCs')

    if process_defs is None:
        print("-> No Process definitions found. Skipping TC loading.")
        return {}

    # Create process type mapping based on TC_Type column
    process_tc_types = {}
    for _, row in process_defs.iterrows():
        process_id = row.get('Process_ID')
        tc_enabled = str(row.get('TC?', '')).lower().strip() == 'yes'
        tc_type = str(row.get('TC_Type', '')).strip()
        
        if pd.notna(process_id) and tc_enabled:
            process_tc_types[int(process_id)] = tc_type

    tc_params = {}
    param_id_counter = 1000

    # Process Static TCs
    static_processes = [pid for pid, tc_type in process_tc_types.items() if tc_type == 'Static']
    if static_processes and static_tc_defs is not None:
        print(f"  -> Processing static TCs for {len(static_processes)} processes...")
        for _, row in static_tc_defs.iterrows():
            process_id = row.get('Process_ID')
            if pd.isna(process_id) or int(process_id) not in static_processes:
                continue

            for element in elements:
                param_name_col = f'TC_{element}_ID'
                param_value_col = f'TC_Value_{element}'
                
                if param_name_col in row and pd.notna(row[param_name_col]) and param_value_col in row and pd.notna(row[param_value_col]):
                    param_name = row[param_name_col]
                    value = row[param_value_col]
                    
                    if param_name not in tc_params:
                        tc_params[param_name] = msc.Parameter(Name=param_name, ID=param_id_counter, Values=value, Unit="1")
                        param_id_counter += 1
                        print(f"    -> Loaded static TC: {param_name} = {value}")
                    else:
                        print(f"⚠️ Warning: Duplicate static TC parameter name found: {param_name}. Using first value found.")

    # Process Dynamic TCs
    dynamic_processes = [pid for pid, tc_type in process_tc_types.items() if tc_type == 'Dynamic']
    if dynamic_processes and dynamic_tc_defs is not None:
        print(f"  -> Processing dynamic TCs for {len(dynamic_processes)} processes...")
        
        # Group dynamic TC data by parameter name
        dynamic_tc_data = dynamic_tc_defs[['TC_material_ID', 'TC_Value_material', 'Year']].dropna()
        
        for param_name in dynamic_tc_data['TC_material_ID'].unique():
            tc_points = dynamic_tc_data[dynamic_tc_data['TC_material_ID'] == param_name]
            
            # Create time series
            ts = pd.Series(tc_points['TC_Value_material'].values, index=tc_points['Year'])
            
            # Reindex to full time vector and interpolate
            ts_full = ts.reindex(time_vector)
            ts_interpolated = ts_full.interpolate(method="linear", limit_direction="both")
            
            # Handle edge cases where interpolation might fail
            if ts_interpolated.isna().any():
                ts_interpolated = ts_interpolated.ffill().bfill()
            
            tc_params[param_name] = msc.Parameter(Name=param_name, ID=param_id_counter, Values=ts_interpolated.to_numpy(), Unit="1")
            param_id_counter += 1
            print(f"    -> Loaded dynamic TC: {param_name} ({len(tc_points)} data points -> {len(ts_interpolated)} time steps)")

    print(f"--> TC loading completed: {len(tc_params)} parameters loaded")
    return tc_params


def load_dsm_parameters(excel_data):
    """
    Reads the '3_1_Definition_DSM' sheet and creates the DSM_PARAMS dictionary.
    """
    sheet_name = "3_1_Definition_DSM"
    print(f"--> Loading DSM parameters from sheet '{sheet_name}'...")

    if sheet_name not in excel_data:
        print(f"--> INFO: Sheet '{sheet_name}' not found. Using empty DSM configuration.")
        return {}

    df_dsm = excel_data[sheet_name]
    if "Process_ID" not in df_dsm.columns:
        print(f"--> FATAL ERROR: Column 'Process_ID' not found in sheet '{sheet_name}'.")
        return {}

    df_dsm = df_dsm.dropna(subset=["Process_ID"])
    df_dsm["Process_ID"] = df_dsm["Process_ID"].astype(int)

    dsm_params = {}
    for process_id, group in df_dsm.groupby("Process_ID"):
        group = group.sort_values(by="Category_ID")
        dsm_params[process_id] = {
            "inflow_split": list(group["Inflow_Split_[%]"]),
            "lifetimes": {
                "Type": list(group["Lifetime_Type"])[0],
                "Mean": list(group["Lifetime_Mean"]),
                "StdDev": list(group["Lifetime_StdDev"]),
            },
            "category_names": list(group["Category_Name"]),
        }

    print(f"--> Successfully loaded configurations for {len(dsm_params)} DSM process(es).")
    return dsm_params


def load_fomp_parameters(excel_data):
    """
    Reads the '3_2_Definition_FOMP' sheet and constructs the FOMP_PARAMS dictionary.
    Supports both Process_ID and Pool_ID systems.
    """
    sheet_name = "3_2_Definition_FOMP"
    print(f"--> Loading FOMP parameters from sheet '{sheet_name}'...")

    if sheet_name not in excel_data:
        print(f"--> INFO: Sheet '{sheet_name}' not found. Using empty FOMP configuration.")
        return {}

    df_fomp = excel_data[sheet_name]
    fomp_params = {}

    for _, row in df_fomp.iterrows():
        # Handle both Process_ID and Pool_ID systems
        process_id = None
        param_name = None
        value = None
        
        # Check if using Pool_ID system (new approach)
        if "Pool_ID" in df_fomp.columns and pd.notna(row.get("Pool_ID")):
            pool_id = str(row["Pool_ID"])
            param_name = row["Parameter_Name"]
            value = row["Value"]
            
            # Extract process ID from Pool_ID format (e.g., "P08_Inflow_fraction_f (Labile pool)" -> "08")
            try:
                if pool_id.startswith("P") and "_" in pool_id:
                    process_id = int(pool_id[1:].split("_")[0])
                else:
                    print(f"⚠️ WARNING: Could not extract process ID from Pool_ID: {pool_id}")
                    continue
            except (ValueError, IndexError):
                print(f"⚠️ WARNING: Could not parse Pool_ID format: {pool_id}")
                continue
                
        # Check if using Process_ID system (legacy approach)
        elif "Process_ID" in df_fomp.columns and pd.notna(row.get("Process_ID")):
            process_id = int(row["Process_ID"])
            param_name = row["Parameter_Name"]
            value = row["Value"]
            
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
    
    print(f"--> Successfully loaded configurations for {len(fomp_params)} FOMP process(es).")
    for process_id, params in fomp_params.items():
        print(f"   Process {process_id}: {len(params)} parameters")
    
    return fomp_params


def load_uncertainty_definitions(excel_data):
    """
    Reads the '4_1_Uncertainty_Parameters' sheet and converts it into the
    UNCERTAINTY_PARAMS dictionary format.
    """
    sheet_name = "4_1_Uncertainty_Parameters"
    print(f"--> Loading uncertainty definitions from sheet '{sheet_name}'...")

    if sheet_name not in excel_data:
        print(f"--> INFO: Sheet '{sheet_name}' not found. No uncertainties will be loaded.")
        return {}

    df_uncertainty = excel_data[sheet_name]
    print(f"  DEBUG: df_uncertainty before dropna:\n{df_uncertainty}")
    df_uncertainty = df_uncertainty.dropna(subset=["Parameter_Name"])
    print(f"  DEBUG: df_uncertainty after dropna (rows: {len(df_uncertainty)}):\n{df_uncertainty}")
    uncertainty_params = {}

    for _, row in df_uncertainty.iterrows():
        param_name = row["Parameter_Name"]
        dist_type = row["Distribution"].lower()
        definition = {"distribution": dist_type}

        if dist_type == "uniform":
            if pd.notna(row["Min"]) and pd.notna(row["Max"]):
                definition["min"] = row["Min"]
                definition["max"] = row["Max"]
        elif dist_type == "normal":
            if pd.notna(row["Mean"]) and pd.notna(row["StdDev"]):
                definition["mean"] = row["Mean"]
                definition["std"] = row["StdDev"]
        elif dist_type == "triangular":
            if pd.notna(row["Min"]) and pd.notna(row["Mode"]) and pd.notna(row["Max"]):
                definition["min"] = row["Min"]
                definition["mode"] = row["Mode"]
                definition["max"] = row["Max"]

        if len(definition) > 1:
            uncertainty_params[param_name] = definition

    print(f"--> Successfully loaded {len(uncertainty_params)} uncertainty parameter definition(s).")
    return uncertainty_params


def apply_fomp_uncertainty_updates(fomp_params, uncertainty_updates):
    """
    Applies uncertainty parameter updates to FOMP parameters.
    Handles process-specific parameter names like 'P7_decay_k1 (Labile pool)'.
    
    Args:
        fomp_params (dict): Original FOMP parameters dictionary
        uncertainty_updates (dict): Sampled parameter values from Monte Carlo
        
    Returns:
        dict: Updated FOMP parameters with uncertainty applied
    """
    updated_fomp_params = copy.deepcopy(fomp_params)
    
    for param_name, sampled_value in uncertainty_updates.items():
        # Check if this is a process-specific FOMP parameter (starts with 'P' and contains '_decay_')
        if param_name.startswith('P') and '_decay_' in param_name:
            try:
                # Extract process ID and original parameter name
                # Format: P7_decay_k1 (Labile pool) -> process_id=7, original_name=decay_k1 (Labile pool)
                parts = param_name.split('_', 1)  # Split on first underscore only
                if len(parts) == 2:
                    process_id_str = parts[0][1:]  # Remove 'P' prefix
                    original_param_name = parts[1]  # Everything after P7_
                    
                    process_id = int(process_id_str)
                    
                    # Apply the update if this process exists in FOMP params
                    if process_id in updated_fomp_params:
                        updated_fomp_params[process_id][original_param_name] = sampled_value
                        print(f"  Applied uncertainty: {param_name} = {sampled_value:.4f} to Process {process_id}")
                    else:
                        print(f"  WARNING: Process {process_id} not found in FOMP parameters for {param_name}")
                        
            except (ValueError, IndexError) as e:
                print(f"  WARNING: Could not parse process-specific parameter {param_name}: {e}")
    
    return updated_fomp_params


def load_scenario_definitions(excel_data):
    """
    Reads the scenario definitions sheet and parses the definitions.
    """
    sheet_name = None
    if "5_1_Scenario_Manager" in excel_data:
        sheet_name = "5_1_Scenario_Manager"
    elif "Scenario Manager" in excel_data:
        sheet_name = "Scenario Manager"

    print(f"--> Loading scenario definitions from sheet '{sheet_name}'...")

    if not sheet_name or excel_data[sheet_name].empty:
        print(f"--> INFO: Scenario sheet not found or is empty. No scenarios loaded.")
        return {}

    df = excel_data[sheet_name]
    
    header_row = 0
    found = False
    for i in range(min(10, len(df))):
        if 'Scenario_Name' in df.iloc[i].values:
            header_row = i
            found = True
            break
    
    if found:
        df.columns = df.iloc[header_row]
        df = df.iloc[header_row + 1:].reset_index(drop=True)
    
    try:
        df_scenarios = df.dropna(subset=["Scenario_Name", "Parameter_Name"])
    except KeyError:
        print(f"--> ERROR: Could not find 'Scenario_Name' or 'Parameter_Name' columns in sheet '{sheet_name}'.")
        return {}

    scenario_definitions = {}
    for scenario_name, group in df_scenarios.groupby("Scenario_Name"):
        for record in group.to_dict('records'):
            if 'ID' in record and pd.notna(record['ID']):
                record['ID'] = int(record['ID'])
            
            # Handle year range columns
            if 'start_year' in record and pd.notna(record['start_year']):
                record['start_year'] = int(record['start_year'])
            else:
                record['start_year'] = None
                
            if 'end_year' in record and pd.notna(record['end_year']):
                record['end_year'] = int(record['end_year'])
            else:
                record['end_year'] = None
                
        scenario_definitions[scenario_name] = group.to_dict('records')

    print(f"--> Successfully loaded {len(scenario_definitions)} scenario(s).")
    return scenario_definitions