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

# These are imported by main.py and are available in this namespace
import ODYM_Classes as msc


def define_model_scope(start_year, end_year, elements):
    """
    Defines the temporal and elemental scope of the MFA model.

    Args:
        start_year (int): The first year of the analysis.
        end_year (int): The last year of the analysis.
        elements (list): A list of strings for the elements to be tracked.

    Returns:
        tuple: A tuple containing the ModelClassification dictionary
               and the IndexTable DataFrame, which are core ODYM objects.
    """
    ModelClassification = {}
    MyYears = list(np.arange(start_year, end_year + 1))

    ModelClassification['Time'] = msc.Classification(Name='Time', Dimension='Time', ID=1, Items=MyYears)
    ModelClassification['Element'] = msc.Classification(Name='Elements', Dimension='Element', ID=2, Items=elements)

    IndexTable = pd.DataFrame({
        'Aspect': ['Time', 'Element'],
        'Description': ['Model aspect "time"', 'Model aspect "Element"'],
        'Dimension': ['Time', 'Element'],
        'Classification': [ModelClassification[Aspect] for Aspect in ['Time', 'Element']],
        'IndexLetter': ['t', 'e']
    })
    IndexTable.set_index('Aspect', inplace=True)

    print("--> Model scope and classifications defined.")
    return ModelClassification, IndexTable


def initialize_mfa_system(model_classification, index_table):
    """
    Initializes the main MFAsystem object based on the defined scope.

    Args:
        model_classification (dict): The ModelClassification dictionary.
        index_table (pd.DataFrame): The IndexTable DataFrame.

    Returns:
        odym.MFAsystem: An empty but structured MFAsystem object.
    """
    start_time = model_classification['Time'].Items[0]
    end_time = model_classification['Time'].Items[-1]
    element_items = model_classification['Element'].Items

    mfa_system = msc.MFAsystem(
        Name='RyeStrawMFA',
        Geogr_Scope='Case_Study_Region',
        Unit='Mg',
        ProcessList=[],
        FlowDict={},
        StockDict={},
        ParameterDict={},
        Time_Start=start_time,
        Time_End=end_time,
        IndexTable=index_table,
        Elements=element_items
    )

    print("--> MFA system object initialized.")
    return mfa_system


def load_and_define_processes(mfa_system, excel_path, data_loader):
    """
    Loads all data from the Excel file, validates its structure, and defines
    the processes and empty stock objects in the MFA system.

    Args:
        mfa_system (odym.MFAsystem): The initialized MFA system object.
        excel_path (str): The file path to the input Excel data.
        data_loader (module): The imported data_loader module.

    Returns:
        tuple: A tuple containing the modified mfa_system object and a
               dictionary of all data read from the Excel file.
    """
    print("--> Defining process and stock structures...")
    input_data = pd.read_excel(excel_path, sheet_name=None, header=0,
                               engine='openpyxl', na_values=['N.A.', 'NA', 'n/a'])
    data_loader.validate_input_data(input_data)

    process_definitions = input_data['2_1_Definition_Processes']
    for _, row in process_definitions.iterrows():
        if pd.notna(row['Name(EN)']):
            process_id = int(row['ID'])
            has_tcs = 'TC' if 'TC?' in row and row['TC?'] == 'Yes' else 'None'
            mfa_system.ProcessList.append(msc.Process(Name=row['Name(EN)'],
                                                      ID=process_id,
                                                      Extensions=has_tcs))
            if 'Stock?' in row and row['Stock?'] == 'Yes':
                mfa_system.StockDict[f"dS_{process_id}"] = msc.Stock(Name=f"dS_{process_id}", P_Res=process_id, Type=1, Indices='t,e')
                mfa_system.StockDict[f"S_{process_id}"] = msc.Stock(Name=f"S_{process_id}", P_Res=process_id, Type=0, Indices='t,e')

    return mfa_system, input_data


def create_dynamic_tc_parameters(dynamic_tc_data, time_vector):
    """
    Generates time-series parameters for dynamic Transfer Coefficients (TCs)
    by interpolating points defined in the input data. Includes data cleaning
    and validation to prevent errors from duplicate entries.
    """
    print("--> Generating dynamic TC time series via interpolation...")
    required_cols = ['TC_ID', 'Year', 'Value']
    if not all(col in dynamic_tc_data.columns for col in required_cols):
        print(f"--> FATAL ERROR: The '2_5_dynamic_tcs' sheet is missing one of the required columns: {required_cols}.")
        return {}

    cleaned_data = dynamic_tc_data.dropna(subset=['TC_ID', 'Year'])
    duplicates = cleaned_data[cleaned_data.duplicated(subset=['TC_ID', 'Year'], keep=False)]
    if not duplicates.empty:
        print("\\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("!!! FATAL ERROR: Duplicate entries found for the same TC in the same year. !!!")
        print("    The following rows in your '2_5_dynamic_tcs' sheet are conflicting:")
        print(duplicates.sort_values(by=['TC_ID', 'Year']))
        print("\\n    Please correct the Excel file. Aborting dynamic TC creation.")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\\n")
        return {}

    dynamic_tc_dict = {}
    unique_tc_ids = cleaned_data['TC_ID'].unique()
    for tc_id in unique_tc_ids:
        tc_points = cleaned_data[cleaned_data['TC_ID'] == tc_id]
        ts = pd.Series(tc_points['Value'].values, index=tc_points['Year'])
        ts_full = ts.reindex(time_vector)
        ts_interpolated = ts_full.interpolate(method='linear', limit_direction='both')
        dynamic_tc_dict[tc_id] = ts_interpolated.to_numpy()

    print(f"--> Generated {len(dynamic_tc_dict)} dynamic TC parameter(s).")
    return dynamic_tc_dict


def define_flows_and_parameters(mfa_system, all_excel_data):
    """
    Defines flows, initializes ALL system values, populates them with data,
    and defines all model parameters (TCs, contents, etc.). This function
    sets up the complete, deterministic state of the system before calculation.

    Args:
        mfa_system (odym.MFAsystem): The MFA system object.
        all_excel_data (dict): Dictionary of DataFrames from the input Excel file.

    Returns:
        tuple: A tuple containing the fully configured mfa_system and all_excel_data.
    """
    print("--> Defining flows, parameters, and setting all initial values...")

    flow_definitions = all_excel_data['1_1_Definition_Flows']
    for _, row in flow_definitions.iterrows():
        if pd.notna(row['Name(EN)']):
            start_id, end_id = int(row['Process_ID_O']), int(row['Process_ID_I'])
            mfa_system.FlowDict[row['Flow_ID']] = msc.Flow(Name=row['Flow_ID'], P_Start=start_id, P_End=end_id, Indices='t,e')

    mfa_system.Initialize_StockValues()
    mfa_system.Initialize_FlowValues()
    print("--> All stocks and flows initialized to zero.")

    flow_data = all_excel_data['1_2_Data_Flows']
    for flow_id, flow_obj in mfa_system.FlowDict.items():
        if flow_id in flow_data['Flow_ID'].values:
            flow_time_series = flow_data[flow_data['Flow_ID'] == flow_id]
            if len(flow_time_series) == len(mfa_system.IndexTable.Classification['Time'].Items):
                flow_obj.Values[:, 0] = np.array(flow_time_series['Flow_Py']).ravel()
    print("--> Populated data for primary input flows.")

    initial_stock_data = all_excel_data.get('2_4_Process_Stock_')
    process_definitions = all_excel_data['2_1_Definition_Processes']
    if initial_stock_data is not None:
        for _, row in process_definitions.iterrows():
            if pd.notna(row['ID']) and 'Initial_Stock?' in row and row['Initial_Stock?'] == 'Yes':
                process_id = int(row['ID'])
                stock_data_row = initial_stock_data[initial_stock_data['Process_ID'] == process_id]
                if not stock_data_row.empty:
                    stock_s = mfa_system.StockDict.get(f"S_{process_id}")
                    if stock_s:
                        mat = stock_data_row['Initial_Stock_material'].iloc[0]
                        wc_p = stock_data_row['Initial_Stock_WC[%]'].iloc[0]
                        dm_p = stock_data_row['Initial_Stock_DM[%]'].iloc[0]
                        cc_p = stock_data_row['Initial_Stock_CC[%]'].iloc[0]
                        stock_s.Values[0, :] = [mat, mat * wc_p, mat * dm_p, mat * cc_p]

    parameter_id_counter = 1
    tc_definitions = all_excel_data.get('2_3_Process_TCs')
    if tc_definitions is not None:
        for _, row in tc_definitions.iterrows():
            if 'TC_ID' in row and pd.notna(row['TC_ID']) and pd.notna(row['TC_Value']):
                mfa_system.ParameterDict[row['TC_ID']] = msc.Parameter(Name=row['TC_ID'], ID=parameter_id_counter, Values=row['TC_Value'], Unit='1')
                parameter_id_counter += 1

    for flow in mfa_system.FlowDict.values():
        if np.any(flow.Values[:, 0] != 0):
            for i_elem, element_name in enumerate(mfa_system.Elements[1:], 1):
                param_name = f"{element_name}_{flow.Name}"
                if param_name in mfa_system.ParameterDict:
                    content_value = mfa_system.ParameterDict[param_name].Values
                    flow.Values[:, i_elem] = flow.Values[:, 0] * content_value

    mfa_system.Consistency_Check()
    return mfa_system, all_excel_data