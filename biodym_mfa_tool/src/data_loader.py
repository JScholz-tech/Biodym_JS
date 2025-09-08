# -*- coding: utf-8 -*-
"""
Data Loader Module for the BioDYM MFA Model.

This file contains all functions responsible for reading, validating, and
parsing the input data from the Excel template file. It acts as the
interface between the raw data and the core model logic.
"""

import pandas as pd
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
    # Format: { 'sheet_name': ['required_col_1', 'required_col_2', ...] }
    REQUIRED_STRUCTURE = {
        "1_1_Definition_Flows": ["Flow_ID", "Name(EN)", "Process_ID_O", "Process_ID_I"],
        "1_2_Data_Flows": ["Flow_ID", "Year_Flow", "Flow_Py"],
        "2_1_Definition_Processes": ["ID", "Name(EN)", "Stock?", "Initial_Stock?"],
        "2_4_Initial_Stock": [
            "Process_ID",
            "Initial_Stock_material",
            "Initial_Stock_WC[%]",
            "Initial_Stock_DM[%]",
            "Initial_Stock_CC[%]",
        ],
        "2_5_dynamic_tcs": ["TC_ID", "Year", "Value"],
    }

    for sheet_name, required_columns in REQUIRED_STRUCTURE.items():
        # 1. Check if the sheet exists
        if sheet_name not in excel_data_dict:
            raise ValueError(
                f"ERROR: The required sheet '{sheet_name}' was not found in the Excel file!"
            )

        # 2. Check if all required columns exist in the sheet
        existing_columns = excel_data_dict[sheet_name].columns
        for col in required_columns:
            if col not in existing_columns:
                raise ValueError(
                    f"ERROR: The required column '{col}' is missing from sheet '{sheet_name}'!"
                )

    print(
        "--> Input data validation successful. All required sheets and columns are present."
    )


def load_dsm_parameters(excel_data):
    """
    Reads the '3_1_Definition_DSM' sheet and creates the DSM_PARAMS dictionary.
    This version explicitly casts the 'Process_ID' column to integer to prevent
    lookup errors (e.g., 7.0 vs 7).

    Args:
        excel_data (dict): The dictionary of DataFrames loaded from Excel.

    Returns:
        dict: A dictionary containing the configuration for all DSM processes.
    """
    sheet_name = "3_1_Definition_DSM"
    print(f"--> Loading DSM parameters from sheet '{sheet_name}'...")

    if sheet_name not in excel_data:
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

    # Drop rows without a Process_ID and enforce integer type.
    # This is the crucial step to fix the 7 vs 7.0 bug.
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

    print(
        f"--> Successfully loaded configurations for {len(dsm_params)} DSM process(es)."
    )
    return dsm_params

def load_fomp_parameters(excel_data):
    """
    Reads the '3_2_Definition_FOMP' sheet and constructs the FOMP_PARAMS dictionary.
    This version handles the enhanced 2-pool FOMP structure with dual outflows.
    Also loads input flow composition for proper carbon/environmental separation.

    Args:
        excel_data (dict): The dictionary of DataFrames loaded from Excel.

    Returns:
        dict: A dictionary containing the configuration for all FOMP processes.
    """
    sheet_name = "3_2_Definition_FOMP"
    print(f"--> Loading FOMP parameters from sheet '{sheet_name}'...")

    if sheet_name not in excel_data:
        print(
            f"--> INFO: Sheet '{sheet_name}' not found. Using empty FOMP configuration."
        )
        return {}

    df_fomp = excel_data[sheet_name]
    fomp_params = {}

    for _, row in df_fomp.iterrows():
        if pd.isna(row["Process_ID"]):
            continue  # Skip this row and go to the next

        process_id = int(row["Process_ID"])
        param_name = row["Parameter_Name"]
        value = row["Value"]

        if process_id not in fomp_params:
            fomp_params[process_id] = {}

        # Handle special case for outflow IDs
        if param_name == "output_carbon_id":
            fomp_params[process_id]["outflow_id"] = value  # Primary outflow (carbon)
        elif param_name == "output_elemental_id":
            fomp_params[process_id]["outflow_id_2"] = value  # Secondary outflow (environmental)
        else:
            # Handle pool-specific parameters
            if "Labile pool" in param_name:
                if "Inflow_fraction_f" in param_name:
                    fomp_params[process_id]["Inflow_fraction_f (Labile pool)"] = float(value)
                elif "decay_k1" in param_name:
                    fomp_params[process_id]["decay_k1"] = float(value)
            elif "Recalcitrant pool" in param_name:
                if "Inflow_fraction_f" in param_name:
                    fomp_params[process_id]["Inflow_fraction_f (Recalcitrant pool)"] = float(value)
                elif "decay_k2" in param_name:
                    fomp_params[process_id]["decay_k2"] = float(value)
            else:
                # Handle legacy parameters for backward compatibility
                try:
                    fomp_params[process_id][param_name] = float(value)
                except (ValueError, TypeError):
                    fomp_params[process_id][param_name] = value

    # Load input flow composition for FOMP processes
    if "1_1_Definition_Flows" in excel_data:
        flows_df = excel_data["1_1_Definition_Flows"]
        
        # Find the input flow to FOMP process (assuming it's F_06_08 based on your case study)
        fomp_input_flow = flows_df[flows_df['Flow_ID'] == 'F_06_08']
        
        if not fomp_input_flow.empty:
            flow_row = fomp_input_flow.iloc[0]
            
            # Extract composition values
            dm_fraction = flow_row.get('DM', 0.86)
            cc_fraction = flow_row.get('CC', 0.4128)
            wc_fraction = flow_row.get('WC', 0.14)
            
            # Add composition to all FOMP processes
            for process_id in fomp_params:
                fomp_params[process_id]["input_flow_composition"] = {
                    'DM': float(dm_fraction) if pd.notna(dm_fraction) else 0.86,
                    'CC': float(cc_fraction) if pd.notna(cc_fraction) else 0.4128,
                    'WC': float(wc_fraction) if pd.notna(wc_fraction) else 0.14
                }
            
            print(f"--> Loaded input flow composition: DM={dm_fraction}, CC={cc_fraction}, WC={wc_fraction}")
        else:
            print("--> Warning: Input flow F_06_08 not found, using default composition")

    print(
        f"--> Successfully loaded configurations for {len(fomp_params)} FOMP process(es)."
    )
    
    # Validate FOMP configurations
    for process_id, params in fomp_params.items():
        print(f"   Process {process_id}:")
        if "outflow_id" in params:
            print(f"     Carbon outflow: {params['outflow_id']}")
        if "outflow_id_2" in params:
            print(f"     Environmental outflow: {params['outflow_id_2']}")
        if "decay_k1" in params:
            print(f"     Labile decay rate: {params['decay_k1']}")
        if "decay_k2" in params:
            print(f"     Recalcitrant decay rate: {params['decay_k2']}")
        if "input_flow_composition" in params:
            comp = params["input_flow_composition"]
            print(f"     Input composition: DM={comp['DM']:.3f}, CC={comp['CC']:.3f}, WC={comp['WC']:.3f}")
    
    return fomp_params

def load_uncertainty_definitions(excel_data):
    """
    Reads the '4_1_Uncertainty_Parameters' sheet and converts it into the
    UNCERTAINTY_PARAMS dictionary format.

    Args:
        excel_data (dict): The dictionary of DataFrames loaded from Excel.

    Returns:
        dict: A dictionary containing the definitions for all uncertain parameters.
    """
    sheet_name = "4_1_Uncertainty_Parameters"
    print(f"--> Loading uncertainty definitions from sheet '{sheet_name}'...")

    if sheet_name not in excel_data:
        print(
            f"--> INFO: Sheet '{sheet_name}' not found. No uncertainties will be loaded."
        )
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

        if len(definition) > 1:  # Add only if parameters were found
            uncertainty_params[param_name] = definition

    print(
        f"--> Successfully loaded {len(uncertainty_params)} uncertainty parameter definition(s)."
    )
    return uncertainty_params


def load_scenario_definitions(excel_data):
    """
    Reads the scenario definitions sheet and parses the definitions.
    It checks for both '5_1_Scenario_Manager' and 'Scenario Manager' sheet names
    and dynamically finds the header row.
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

    # Find the header row by searching for 'Scenario_Name' in the first few rows
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
    
    # Now we can safely access the columns
    try:
        df_scenarios = df.dropna(subset=["Scenario_Name", "Parameter_Name"])
    except KeyError:
        print(f"--> ERROR: Even after searching, could not find 'Scenario_Name' or 'Parameter_Name' columns in sheet '{sheet_name}'. Please check the Excel file.")
        return {}

    scenario_definitions = {}
    for scenario_name, group in df_scenarios.groupby("Scenario_Name"):
        # Convert float values from Excel that should be integers
        for record in group.to_dict('records'):
            if 'ID' in record and pd.notna(record['ID']):
                record['ID'] = int(record['ID'])
        scenario_definitions[scenario_name] = group.to_dict('records')

    print(f"--> Successfully loaded {len(scenario_definitions)} scenario(s).")
    return scenario_definitions

