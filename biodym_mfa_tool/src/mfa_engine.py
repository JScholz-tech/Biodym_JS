# -*- coding: utf-8 -*-
"""
MFA Engine Module for the BioDYM Model.

This file contains the core calculation functions for the Material Flow
Analysis, including system setup, the iterative solver, and the specific
implementations for the Dynamic Stock Model (DSM) and First-Order Model
Process (FOMP).
"""
import numpy as np
import pandas as pd
import copy

# These are imported by main.py and are available in this namespace
import ODYM_Classes as msc
import dynamic_stock_model as dsm


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
    Defines flows, initializes ALL system values, populates them,
    and defines all model parameters (TCs, contents, etc.).
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

    # Step 4: Define ALL standard parameters
    parameter_id_counter = 1
    tc_definitions = all_excel_data['2_3_Process_TCs']
    for _, row in tc_definitions.iterrows():
        if 'TC_ID' in row and pd.notna(row['TC_ID']) and pd.notna(row['TC_Value']):
            mfa_system.ParameterDict[row['TC_ID']] = msc.Parameter(Name=row['TC_ID'], ID=parameter_id_counter, Values=row['TC_Value'], Unit='1')
            parameter_id_counter += 1

    dynamic_tc_sheet = all_excel_data.get('2_5_dynamic_tcs')
    if dynamic_tc_sheet is not None:
        # This function is now in the same module (mfa_engine.py)
        dynamic_tcs = create_dynamic_tc_parameters(dynamic_tc_sheet, mfa_system.IndexTable.Classification['Time'].Items)
        for name, values in dynamic_tcs.items():
            mfa_system.ParameterDict[name] = msc.Parameter(Name=name, ID=parameter_id_counter, Values=values, Unit='1')
            parameter_id_counter += 1

    content_definitions = all_excel_data['1_1_Definition_Flows']
    for _, row in content_definitions.iterrows():
        if pd.notna(row['Flow_ID']) and row['Flow_ID'] in mfa_system.FlowDict:
            for element in ['WC', 'DM', 'CC']:
                if element in row and pd.notna(row[element]):
                    param_name = f"{element}_{row['Flow_ID']}"
                    mfa_system.ParameterDict[param_name] = msc.Parameter(Name=param_name, ID=parameter_id_counter, Values=row[element], Unit='1')
                    parameter_id_counter += 1

    # --- Start of MC adaptation ---
    # Override standard TCs with values sampled for this MC run
    if tc_updates:
        print("    - Applying Monte Carlo updates to TC parameters...")
        for param_name, new_value in tc_updates.items():
            if param_name in mfa_system.ParameterDict:
                mfa_system.ParameterDict[param_name].Values = new_value
            else:
                print(f"      - WARNING: Sampled parameter '{param_name}' not found in system ParameterDict.")
    # --- End of MC adaptation ---

    print(f"--> Defined {len(mfa_system.ParameterDict)} parameters in total.")

    # Step 5: Calculate element contents for primary input flows
    for flow in mfa_system.FlowDict.values():
        if np.any(flow.Values[:, 0] != 0):
            for i_elem, element_name in enumerate(mfa_system.Elements[1:], 1):
                param_name = f"{element_name}_{flow.Name}"
                if param_name in mfa_system.ParameterDict:
                    content_value = mfa_system.ParameterDict[param_name].Values
                    flow.Values[:, i_elem] = flow.Values[:, 0] * content_value

    mfa_system.Consistency_Check()

    return mfa_system, all_excel_data


def calculate_dynamic_stock(mfa_system, dsm_params_config):
    """
    Calculates the outflow from a dynamic stock process.

    This function correctly handles two separate components of the outflow:
    1. The outflow from new inflows, calculated using the detailed lifetime
       distribution from the 'dynamic_stock_model' library.
    2. The outflow from any non-zero initial stock, calculated using a
       simplified first-order decay based on the average lifetime.

    It also returns a detailed dictionary for creating specialized plots.

    Args:
        mfa_system (odym.MFAsystem): The MFA system object.
        dsm_params_config (dict): A dictionary containing the configuration
                                  for the DSM processes to be calculated.

    Returns:
        tuple: A tuple containing the modified mfa_system and a dictionary
               with detailed results for plotting.
    """
    time_vector = np.array(mfa_system.IndexTable.Classification['Time'].Items)
    num_years, num_elements = len(time_vector), len(mfa_system.Elements)
    dsm_details_results = {}

    for process_id, params in dsm_params_config.items():
        stock_s = mfa_system.StockDict.get(f"S_{process_id}")
        initial_stock_vector = stock_s.Values[0, :].copy() if stock_s is not None else np.zeros(num_elements)
        inflows = [f.Values for f in mfa_system.FlowDict.values() if f.P_End == process_id]
        total_inflow_values = sum(inflows) if inflows else np.zeros((num_years, num_elements))
        outflow_flow_name = next((f.Name for f in mfa_system.FlowDict.values() if f.P_Start == process_id), None)
        if not outflow_flow_name: continue

        lt_params = params.get('lifetimes', {})
        mean_lifetimes = lt_params.get('Mean', [])

        # Calculate outflow from new inflows using the DSM library
        outflow_from_inflows_material, stock_from_inflows_by_cat = np.zeros(num_years), []
        inflow_split, std_devs = params.get('inflow_split', [1.0]), lt_params.get('StdDev', [])
        for i in range(len(inflow_split)):
            inflow_category = total_inflow_values[:, 0] * inflow_split[i]
            dsm_model_instance = dsm.DynamicStockModel(t=time_vector, i=inflow_category, lt={'Type': lt_params.get('Type'), 'Mean': [mean_lifetimes[i]], 'StdDev': [std_devs[i]]})
            s_c, o_c = dsm_model_instance.compute_s_c_inflow_driven(), dsm_model_instance.compute_o_c_from_s_c()
            if o_c is not None:
                outflow_from_inflows_material += o_c.sum(axis=1)
                stock_from_inflows_by_cat.append(s_c.sum(axis=1))
            else:
                stock_from_inflows_by_cat.append(np.zeros(len(time_vector)))

        # Calculate outflow from the initial stock using a simplified decay model
        avg_lifetime = np.mean(mean_lifetimes) if mean_lifetimes else 0
        decay_rate_k = 1 / avg_lifetime if avg_lifetime > 0 else 0
        outflow_from_initial_stock_ts, decaying_stock_ts = np.zeros_like(total_inflow_values), np.zeros_like(total_inflow_values)
        if np.sum(initial_stock_vector) > 0:
            current_decaying_stock = initial_stock_vector.copy()
            for t in range(num_years):
                decaying_stock_ts[t, :] = current_decaying_stock
                outflow_t = current_decaying_stock * decay_rate_k
                outflow_from_initial_stock_ts[t, :] = outflow_t
                current_decaying_stock -= outflow_t

        # Combine outflows and update the flow in the MFA system
        total_outflow_material = outflow_from_inflows_material + outflow_from_initial_stock_ts[:, 0]
        mfa_system.FlowDict[outflow_flow_name].Values[:, 0] = total_outflow_material
        for elem_idx in range(1, total_inflow_values.shape[1]):
            factor = np.divide(total_inflow_values[:, elem_idx], total_inflow_values[:, 0], out=np.zeros_like(total_inflow_values[:, 0]), where=total_inflow_values[:, 0] != 0)
            mfa_system.FlowDict[outflow_flow_name].Values[:, elem_idx] = total_outflow_material * factor

        # Store detailed results for plotting
        dsm_details_results[process_id] = {
            'initial_stock_ts': decaying_stock_ts,
            'inflow_stock_ts_by_cat': stock_from_inflows_by_cat,
            'category_names': params.get('category_names', []),
            'mean_lifetimes': mean_lifetimes
        }

    return mfa_system, dsm_details_results


    return mfa_system, dsm_details_results


def calculate_fomp(mfa_system, fomp_params_config):
    """
    Calculates the outflow from a First-Order Model Process (FOMP).

    This function models processes like decay or mineralization where the
    outflow rate is dependent on the current stock level and inflow,
    governed by first-order decay constants.

    Args:
        mfa_system (odym.MFAsystem): The MFA system object.
        fomp_params_config (dict): A dictionary containing the configuration
                                   for the FOMP processes to be calculated.

    Returns:
        odym.MFAsystem: The MFA system object with the calculated FOMP
                        outflow updated.
    """
    print("--> Calculating FOMP outflows...")
    time_vector = mfa_system.IndexTable.Classification['Time'].Items
    num_years, num_elements = len(time_vector), len(mfa_system.Elements)

    for process_id, params in fomp_params_config.items():
        if not any(p.ID == process_id for p in mfa_system.ProcessList): continue
        stock_s = mfa_system.StockDict.get(f"S_{process_id}")
        if stock_s is None: continue

        print(f"    ... calculating outflow from FOMP process {process_id}")
        initial_stock_vector = stock_s.Values[0, :].copy()
        outflow_flow_name = params.get('outflow_id')
        if not outflow_flow_name: continue

        f, k1, k2 = params.get('f', 0), params.get('k1', 0), params.get('k2', 0)
        inflows = [flow.Values for flow in mfa_system.FlowDict.values() if flow.P_End == process_id]
        inflow_values = sum(inflows) if inflows else np.zeros((num_years, num_elements))

        new_outflow_values, current_stock = np.zeros_like(inflow_values), initial_stock_vector
        for t in range(num_years):
            outflow_t = (inflow_values[t, :] * f) + (current_stock * k1) + (inflow_values[t, :] * k2)
            new_outflow_values[t, :] = outflow_t
            current_stock = current_stock + inflow_values[t, :] - outflow_t

        mfa_system.FlowDict[outflow_flow_name].Values = new_outflow_values

    print("--> FOMP outflow calculation finished.")
    return mfa_system


    print("--> FOMP outflow calculation finished.")
    return mfa_system


def calculate_final_balances(mfa_system):
    """
    Calculates the final stock changes (dS) and absolute stocks (S) for ALL
    processes, correctly respecting any initial stocks set during setup.
    This is the final accounting step of the calculation.

    Args:
        mfa_system (odym.MFAsystem): The MFA system object with all flows
                                     calculated.

    Returns:
        odym.MFAsystem: The MFA system object with final stock values updated.
    """
    print("--> Calculating final stock balances for ALL processes...")
    num_years = len(mfa_system.IndexTable.Classification['Time'].Items)

    # Loop through all processes that have a stock defined
    for pid in {p.ID for p in mfa_system.ProcessList}:
        if f"S_{pid}" in mfa_system.StockDict:
            stock_s, stock_ds = mfa_system.StockDict[f"S_{pid}"], mfa_system.StockDict[f"dS_{pid}"]

            # 1. Calculate the final stock change (dS) for the entire period
            inflows = [f.Values for f in mfa_system.FlowDict.values() if f.P_End == pid]
            outflows = [f.Values for f in mfa_system.FlowDict.values() if f.P_Start == pid]
            total_inflows = sum(inflows) if inflows else np.zeros_like(stock_s.Values)
            total_outflows = sum(outflows) if outflows else np.zeros_like(stock_s.Values)
            dS_values = total_inflows - total_outflows
            stock_ds.Values = dS_values

            # 2. Iteratively calculate the absolute stock S: S(t) = S(t-1) + dS(t)
            initial_stock_vector = stock_s.Values[0, :].copy()
            new_s_values = np.cumsum(np.vstack([initial_stock_vector, dS_values[:-1, :]]), axis=0)
            stock_s.Values = new_s_values

    print("--> Stock balance calculation finished.")
    return mfa_system


    print("--> Stock balance calculation finished.")
    return mfa_system


def run_mfa_calculation(mfa_system_setup, dsm_params, fomp_params, config, tc_updates=None):
    """
    This function is the iterative solver for the MFA system.

    It repeatedly cycles through the system, calculating flows in a specific
    order (TCs first, then special models like DSM/FOMP) until no more
    changes occur, indicating that the system has converged to a stable state.
    This version is also adapted for Monte Carlo simulations.

    Args:
        mfa_system_setup (odym.MFAsystem): A fully configured but unsolved
                                           MFA system object.
        dsm_params (dict): Configuration dictionary for DSM processes.
        fomp_params (dict): Configuration dictionary for FOMP processes.
        config (module): The imported config module with calculation switches.
        tc_updates (dict, optional): A dictionary of sampled TC values for an
                                     MC run. Defaults to None.

    Returns:
        tuple: A tuple containing the solved mfa_system and a dictionary
               with detailed DSM results for plotting.
    """
    # Create a deep copy to avoid modifying the original configured system
    mfa_system = copy.deepcopy(mfa_system_setup)

    # Apply Monte Carlo updates if they are provided
    if tc_updates:
        print("    - Applying Monte Carlo updates to TC parameters...")
        for param_name, new_value in tc_updates.items():
            if param_name in mfa_system.ParameterDict:
                mfa_system.ParameterDict[param_name].Values = new_value

    # Initialize tracking variables
    dsm_details = {}
    dsm_processes = set(dsm_params.keys())
    fomp_processes = set(fomp_params.keys())
    special_processes = dsm_processes.union(fomp_processes)
    dsm_processes_run = {pid: False for pid in dsm_processes}
    fomp_processes_run = {pid: False for pid in fomp_processes}

    # The main solver loop
    for i in range(15):  # Max 15 iterations to prevent infinite loops
        something_changed_in_main_loop = False
        while True:
            something_changed_in_tc_loop = False
            for flow in mfa_system.FlowDict.values():
                if np.any(flow.Values != 0) or flow.P_Start in special_processes:
                    continue
                param_name = f"TC_{'_'.join(flow.Name.split('_')[1:3])}"
                if param_name in mfa_system.ParameterDict:
                    input_flows = [f for f in mfa_system.FlowDict.values() if f.P_End == flow.P_Start]
                    if input_flows and all(np.any(f.Values != 0) or f.P_Start == 0 for f in input_flows):
                        total_inflow_values = sum(f.Values for f in input_flows)
                        tc_value = mfa_system.ParameterDict[param_name].Values
                        flow.Values[:, 0] = total_inflow_values[:, 0] * tc_value
                        for i_elem in range(1, len(mfa_system.Elements)):
                            composition_factor = np.divide(total_inflow_values[:, i_elem], total_inflow_values[:, 0], out=np.zeros_like(total_inflow_values[:, 0]), where=total_inflow_values[:, 0] != 0)
                            flow.Values[:, i_elem] = flow.Values[:, 0] * composition_factor
                        something_changed_in_tc_loop = True
                        something_changed_in_main_loop = True
            if not something_changed_in_tc_loop:
                break

        if config.RUN_DSM_CALCULATION:
            for process_id in dsm_processes:
                if not dsm_processes_run[process_id] and all(np.any(f.Values != 0) for f in mfa_system.FlowDict.values() if f.P_End == process_id):
                    mfa_system, dsm_details_single_run = calculate_dynamic_stock(mfa_system, {process_id: dsm_params[process_id]})
                    dsm_details.update(dsm_details_single_run)
                    dsm_processes_run[process_id] = True
                    something_changed_in_main_loop = True

        if config.RUN_FOMP_CALCULATION:
            for process_id in fomp_processes:
                if not fomp_processes_run[process_id] and all(np.any(f.Values != 0) for f in mfa_system.FlowDict.values() if f.P_End == process_id):
                    mfa_system = calculate_fomp(mfa_system, {process_id: fomp_params[process_id]})
                    fomp_processes_run[process_id] = True
                    something_changed_in_main_loop = True

        if not something_changed_in_main_loop and i > 0:
            break

    mfa_system = calculate_final_balances(mfa_system)
    return mfa_system, dsm_details
