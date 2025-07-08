# -*- coding: utf-8 -*-
"""
Data Loader Module for the BioDYM MFA Model.

This file contains all functions responsible for reading, validating, and
parsing the input data from the Excel template file. It acts as the
interface between the raw data and the core model logic.
"""
import pandas as pd
import numpy as np


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
        '1_1_Definition_Flows': ['Flow_ID', 'Name(EN)', 'Process_ID_O', 'Process_ID_I'],
        '1_2_Data_Flows': ['Flow_ID', 'Year_Flow', 'Flow_Py'],
        '2_1_Definition_Processes': ['ID', 'Name(EN)', 'Stock?', 'Initial_Stock?'],
        '2_4_Initial_Stock': ['Process_ID', 'Initial_Stock_material', 'Initial_Stock_WC[%]', 'Initial_Stock_DM[%]', 'Initial_Stock_CC[%]'],
        '2_5_dynamic_tcs': ['TC_ID', 'Year', 'Value']
    }

    for sheet_name, required_columns in REQUIRED_STRUCTURE.items():
        # 1. Check if the sheet exists
        if sheet_name not in excel_data_dict:
            raise ValueError(f"ERROR: The required sheet '{sheet_name}' was not found in the Excel file!")

        # 2. Check if all required columns exist in the sheet
        existing_columns = excel_data_dict[sheet_name].columns
        for col in required_columns:
            if col not in existing_columns:
                raise ValueError(f"ERROR: The required column '{col}' is missing from sheet '{sheet_name}'!")

    print("--> Input data validation successful. All required sheets and columns are present.")


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
    sheet_name = '3_1_Definition_DSM'
    print(f"--> Loading DSM parameters from sheet '{sheet_name}'...")

    if sheet_name not in excel_data:
        print(f"--> INFO: Sheet '{sheet_name}' not found. Using empty DSM configuration.")
        return {}

    df_dsm = excel_data[sheet_name]

    if 'Process_ID' not in df_dsm.columns:
        print(f"--> FATAL ERROR: Column 'Process_ID' not found in sheet '{sheet_name}'.")
        return {}

    # Drop rows without a Process_ID and enforce integer type.
    # This is the crucial step to fix the 7 vs 7.0 bug.
    df_dsm = df_dsm.dropna(subset=['Process_ID'])
    df_dsm['Process_ID'] = df_dsm['Process_ID'].astype(int)

    dsm_params = {}
    for process_id, group in df_dsm.groupby('Process_ID'):
        group = group.sort_values(by='Category_ID')
        dsm_params[process_id] = {
            'inflow_split': list(group['Inflow_Split_[%]']),
            'lifetimes': {
                'Type': list(group['Lifetime_Type'])[0],
                'Mean': list(group['Lifetime_Mean']),
                'StdDev': list(group['Lifetime_StdDev'])
            },
            'category_names': list(group['Category_Name'])
        }

    print(f"--> Successfully loaded configurations for {len(dsm_params)} DSM process(es).")
    return dsm_params


def load_fomp_parameters(excel_data):
    """
    Reads the '3_2_Definition_FOMP' sheet and constructs the FOMP_PARAMS dictionary.
    This version ignores empty rows.

    Args:
        excel_data (dict): The dictionary of DataFrames loaded from Excel.

    Returns:
        dict: A dictionary containing the configuration for all FOMP processes.
    """
    sheet_name = '3_2_Definition_FOMP'
    print(f"--> Loading FOMP parameters from sheet '{sheet_name}'...")

    if sheet_name not in excel_data:
        print(f"--> INFO: Sheet '{sheet_name}' not found. Using empty FOMP configuration.")
        return {}

    df_fomp = excel_data[sheet_name]
    fomp_params = {}

    for _, row in df_fomp.iterrows():
        if pd.isna(row['Process_ID']):
            continue  # Skip this row and go to the next

        process_id = int(row['Process_ID'])
        param_name = row['Parameter_Name']
        value = row['Value']

        if process_id not in fomp_params:
            fomp_params[process_id] = {}

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

    Args:
        excel_data (dict): The dictionary of DataFrames loaded from Excel.

    Returns:
        dict: A dictionary containing the definitions for all uncertain parameters.
    """
    sheet_name = '4_1_Uncertainty_Parameters'
    print(f"--> Loading uncertainty definitions from sheet '{sheet_name}'...")

    if sheet_name not in excel_data:
        print(f"--> INFO: Sheet '{sheet_name}' not found. No uncertainties will be loaded.")
        return {}

    df_uncertainty = excel_data[sheet_name].dropna(subset=['Parameter_Name'])
    uncertainty_params = {}

    for _, row in df_uncertainty.iterrows():
        param_name = row['Parameter_Name']
        dist_type = row['Distribution']
        definition = {'distribution': dist_type}

        if dist_type == 'uniform':
            if pd.notna(row['Min']) and pd.notna(row['Max']):
                definition['min'] = row['Min']
                definition['max'] = row['Max']
        elif dist_type == 'normal':
            if pd.notna(row['Mean']) and pd.notna(row['StdDev']):
                definition['mean'] = row['Mean']
                definition['std'] = row['StdDev']
        elif dist_type == 'triangular':
            if pd.notna(row['Min']) and pd.notna(row['Mode']) and pd.notna(row['Max']):
                definition['min'] = row['Min']
                definition['mode'] = row['Mode']
                definition['max'] = row['Max']

        if len(definition) > 1:  # Add only if parameters were found
            uncertainty_params[param_name] = definition

    print(f"--> Successfully loaded {len(uncertainty_params)} uncertainty parameter definition(s).")
    return uncertainty_params
def load_and_define_processes(mfa_system, excel_path, data_loader):
    """
    Loads all data from the Excel file, validates its structure, and defines
    the processes and empty stock objects in the MFA system.

    Args:
        mfa_system (odym.MFAsystem): The initialized MFA system object.
        excel_path (str): The file path to the input Excel data.
        data_loader (module): The imported data_loader module, containing
                              the validation function.

    Returns:
        tuple: A tuple containing the modified mfa_system object and a
               dictionary of all data read from the Excel file.
    """
    print("--> Defining process and stock structures...")

    # Load all sheets from the Excel file into a dictionary of DataFrames
    input_data = pd.read_excel(excel_path, sheet_name=None, header=0,
                               engine='openpyxl', na_values=['N.A.', 'NA', 'n/a'])

    # Use the validation function from the data_loader module
    data_loader.validate_input_data(input_data)

    process_definitions = input_data['2_1_Definition_Processes']
    for index, row in process_definitions.iterrows():
        if pd.notna(row['Name(EN)']):
            process_id = int(row['ID'])
            has_tcs = 'TC' if 'TC?' in row and row['TC?'] == 'Yes' else 'None'
            mfa_system.ProcessList.append(msc.Process(Name=row['Name(EN)'],
                                                      ID=process_id,
                                                      Extensions=has_tcs))

            # Create stock objects if the process is defined as having a stock
            if 'Stock?' in row and row['Stock?'] == 'Yes':
                # Stock for stock-changes (dS)
                mfa_system.StockDict[f"dS_{process_id}"] = msc.Stock(Name=f"dS_{process_id}",
                                                                     P_Res=process_id, Type=1,
                                                                     Indices='t,e')
                # Stock for absolute stock values (S)
                mfa_system.StockDict[f"S_{process_id}"] = msc.Stock(Name=f"S_{process_id}",
                                                                    P_Res=process_id, Type=0,
                                                                    Indices='t,e')

    # The values for these objects will be set in a later function
    return mfa_system, input_data

