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
        "1_1_Definition_Flows": ["Flow_ID", "Name(EN)", "Process_ID_O", "Process_ID_I"],
        "1_2_Data_Flows": ["Flow_ID", "Year_Flow", "Flow_Py"],
        "2_1_Definition_Processes": ["ID", "Name(EN)", "Process_Logic"],
        "2_3_Process_TCs": ["TC_ID", "Process_ID", "TC_Value_material"],
        "2_4_Initial_Stock": [
            "Process_ID",
            "Initial_Stock_material",
            "Initial_Stock_WC[%]",
            "Initial_Stock_DM[%]",
            "Initial_Stock_CC[%]",
        ],
    }

    for sheet_name, required_columns in REQUIRED_STRUCTURE.items():
        if sheet_name not in excel_data_dict:
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
    Loads all static and dynamic transfer coefficients, handling the
    'Splitter' vs. 'Transformer' logic.

    Args:
        all_excel_data (dict): Dictionary of DataFrames from Excel.
        elements (list): List of element names (e.g., ['material', 'WC', 'DM', 'CC']).
        time_vector (list): List of years for the analysis.

    Returns:
        dict: A dictionary of ODYM Parameter objects for all TCs.
    """
    print("--> Loading Transfer Coefficients (TCs)...")
    
    process_defs = all_excel_data.get('2_1_Definition_Processes')
    static_tc_defs = all_excel_data.get('2_3_Process_TCs')
    dynamic_tc_defs = all_excel_data.get('2_5_dynamic_tcs')

    if static_tc_defs is None or process_defs is None:
        print("-> No TC definitions found. Skipping.")
        return {}

    # Create a mapping from Process_ID to Process_Logic for quick lookup
    logic_map = process_defs.set_index('ID')['Process_Logic'].to_dict()
    
    # Dictionary to hold the final ODYM Parameter objects
    tc_params = {}
    param_id_counter = 1000  # Start from a high number to avoid collisions

    # 1. Process Static TCs
    for _, row in static_tc_defs.iterrows():
        if pd.isna(row.get('TC_ID')) or pd.isna(row.get('Process_ID')):
            continue

        tc_id = row['TC_ID']
        process_id = int(row['Process_ID'])
        process_logic = logic_map.get(process_id)

        # --- DEBUG LOGGING ---
        print(f"  -> Loading TC: {tc_id} (from Process {process_id})... Applying '{process_logic}' logic.")

        for element in elements:
            param_name = f"{tc_id}_{element}"
            value = np.nan

            if process_logic == 'Splitter':
                value = row['TC_Value_material']
            elif process_logic == 'Transformer':
                col_name = f"TC_Value_{element}"
                if col_name in row:
                    value = row[col_name]
            
            if pd.notna(value):
                tc_params[param_name] = msc.Parameter(Name=param_name, ID=param_id_counter, Values=value, Unit="1")
                param_id_counter += 1

    # 2. Process Dynamic TCs
    if dynamic_tc_defs is not None and not dynamic_tc_defs.empty:
        # Robustly find required columns, ignoring extras
        required_dyn_cols = ['TC_ID', 'Year'] + [f'Value_{elem}' for elem in elements]
        
        for _, row in dynamic_tc_defs.iterrows():
            if pd.isna(row.get('TC_ID')) or pd.isna(row.get('Year')):
                continue
            
            tc_id = row['TC_ID']
            # Find the process logic for this TC
            # Ensure Process_ID is an integer before lookup
            process_id_static_tc_row = static_tc_defs[static_tc_defs['TC_ID'] == tc_id]
            if process_id_static_tc_row.empty:
                print(f"⚠️ Warning: Dynamic TC '{tc_id}' found without a corresponding static TC definition. Skipping.")
                continue
            process_id = int(process_id_static_tc_row['Process_ID'].iloc[0])
            process_logic = logic_map.get(process_id)

            for element in elements:
                param_name = f"{tc_id}_{element}"
                value_col = f"Value_{element}"

                # For splitters, if substance-specific value is missing, use the material value
                if process_logic == 'Splitter' and (value_col not in row or pd.isna(row[value_col])):
                    value_col = 'Value_material'

                if value_col in row and pd.notna(row[value_col]):
                    # This is one point in a time series
                    year = row['Year']
                    value = row[value_col]
                    
                    # Initialize the parameter if it's the first time we see it
                    if param_name not in tc_params:
                        # Create a placeholder Series with NaNs that we can fill
                        ts = pd.Series(index=time_vector, dtype=float)
                        tc_params[param_name] = msc.Parameter(Name=param_name, ID=param_id_counter, Values=ts, Unit="1")
                        param_id_counter += 1
                    elif not isinstance(tc_params[param_name].Values, pd.Series):
                        # It's a static TC that now has dynamic data, convert to Series
                        static_value = tc_params[param_name].Values # Get the existing static value
                        ts = pd.Series(index=time_vector, dtype=float)
                        # Fill the Series with the static value for all years before adding dynamic points
                        ts.loc[:] = static_value 
                        tc_params[param_name].Values = ts # Replace the float with the Series

                    # Set the value for the specific year
                    # Ensure year is in the time_vector index
                    if year in tc_params[param_name].Values.index:
                        tc_params[param_name].Values[year] = value
                    else:
                        print(f"⚠️ Warning: Year {year} for dynamic TC '{tc_id}' is outside the defined time range. Skipping.")

    # 3. Interpolate all dynamic TC time series
    for param in tc_params.values():
        if isinstance(param.Values, pd.Series):
            # Only interpolate if there are non-NaN values to interpolate from
            if param.Values.first_valid_index() is not None:
                param.Values = param.Values.interpolate(method='linear', limit_direction='both').to_numpy()
            else:
                # If all values are NaN (e.g., TC defined but no dynamic data points), set to 0
                param.Values = np.zeros_like(param.Values.to_numpy())

    print(f"--> TC loading complete. {len(tc_params)} substance-specific TC parameters created.")
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
    """
    sheet_name = "3_2_Definition_FOMP"
    print(f"--> Loading FOMP parameters from sheet '{sheet_name}'...")

    if sheet_name not in excel_data:
        print(f"--> INFO: Sheet '{sheet_name}' not found. Using empty FOMP configuration.")
        return {}

    df_fomp = excel_data[sheet_name]
    fomp_params = {}

    for _, row in df_fomp.iterrows():
        if pd.isna(row["Process_ID"]):
            continue

        process_id = int(row["Process_ID"])
        param_name = row["Parameter_Name"]
        value = row["Value"]

        if process_id not in fomp_params:
            fomp_params[process_id] = {}

        if param_name == "output_carbon_id":
            fomp_params[process_id]["outflow_id"] = value
        elif param_name == "output_environmental_id":
            fomp_params[process_id]["outflow_id_2"] = value
        else:
            try:
                fomp_params[process_id][param_name] = float(value)
            except (ValueError, TypeError):
                fomp_params[process_id][param_name] = value
    
    print(f"--> Successfully loaded configurations for {len(fomp_params)} FOMP process(es).")
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

    df_uncertainty = excel_data[sheet_name].dropna(subset=["Parameter_Name"])
    uncertainty_params = {}

    for _, row in df_uncertainty.iterrows():
        param_name = row["Parameter_Name"]
        dist_type = row["Distribution"]
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
        scenario_definitions[scenario_name] = group.to_dict('records')

    print(f"--> Successfully loaded {len(scenario_definitions)} scenario(s).")
    return scenario_definitions