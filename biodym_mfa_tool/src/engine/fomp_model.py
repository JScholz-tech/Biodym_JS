# -*- coding: utf-8 -*-
"""
Enhanced First-Order Model Process (FOMP) Module for the BioDYM Engine.

This file contains the calculation logic for a two-pool soil carbon decay model,
based on a more precise analytical solution for first-order decay.
"""

import numpy as np

def _calculate_fomp_series(dm_inflow_series, params, initial_stock_labile, initial_stock_recalcitrant):
    """
    Implements the core two-pool, first-order decay model calculation.

    This is a pure function that takes time-series data and parameters as input,
    and returns a dictionary of calculated time-series arrays. It uses the
    analytical solution for first-order decay: decay = stock * (1 - exp(-k)).

    Args:
        dm_inflow_series (np.array): Time-series of total Dry Matter (DM) inflow.
        params (dict): Dictionary of model parameters (f_labile, k_labile, etc.).
        initial_stock_labile (float): Initial stock of the labile pool.
        initial_stock_recalcitrant (float): Initial stock of the recalcitrant pool.

    Returns:
        dict: A dictionary of NumPy arrays for calculated time-series.
    """
    num_years = len(dm_inflow_series)
    
    # Create result arrays
    stock_labile_series = np.zeros(num_years)
    stock_recalcitrant_series = np.zeros(num_years)
    outflow_carbon_series = np.zeros(num_years)
    outflow_environmental_series = np.zeros(num_years)

    # Get parameters from dict
    f_labile = params['f_labile']
    k_labile = params['k_labile']
    k_recalcitrant = params['k_recalcitrant']
    cc_dm = params['cc_dm']

    # Initialize stocks for the loop
    current_stock_labile = initial_stock_labile
    current_stock_recalcitrant = initial_stock_recalcitrant

    for t in range(num_years):
        # a. Determine Stocks at Start of Year
        stock_start_labile = current_stock_labile
        stock_start_recalcitrant = current_stock_recalcitrant

        # b. Calculate Decay for Each Pool using analytical solution
        decay_labile = stock_start_labile * (1 - np.exp(-k_labile))
        decay_recalcitrant = stock_start_recalcitrant * (1 - np.exp(-k_recalcitrant))

        # c. Calculate Inflows to Each Pool
        inflow_labile = dm_inflow_series[t] * f_labile
        inflow_recalcitrant = dm_inflow_series[t] * (1 - f_labile)

        # d. Calculate Stocks at End of Year
        end_of_year_labile = (stock_start_labile - decay_labile) + inflow_labile
        end_of_year_recalcitrant = (stock_start_recalcitrant - decay_recalcitrant) + inflow_recalcitrant
        
        stock_labile_series[t] = end_of_year_labile
        stock_recalcitrant_series[t] = end_of_year_recalcitrant

        # e. Calculate and Store Split Outflows
        total_decay_dm = decay_labile + decay_recalcitrant
        outflow_carbon_series[t] = total_decay_dm * cc_dm
        outflow_environmental_series[t] = total_decay_dm * (1 - cc_dm)

        # Update stocks for the next iteration
        current_stock_labile = end_of_year_labile
        current_stock_recalcitrant = end_of_year_recalcitrant

    results = {
        'stock_labile': stock_labile_series,
        'stock_recalcitrant': stock_recalcitrant_series,
        'outflow_carbon': outflow_carbon_series,
        'outflow_environmental': outflow_environmental_series,
    }
    return results

def calculate_fomp(mfa_system, fomp_params_config, input_flow_composition):
    """
    Wrapper function to integrate the pure FOMP calculation with the ODYM framework.

    This function extracts data from the MFA system, calls the pure calculation 
    function (_calculate_fomp_series), and assigns the resulting outflows back to 
    the system. It does NOT modify the stock directly, allowing the main solver 
    to handle final stock accounting.
    """
    time_vector = mfa_system.IndexTable.Classification["Time"].Items
    num_years, num_elements = len(time_vector), len(mfa_system.Elements)

    # --- 1. Extract data and parameters from the MFA System ---
    process_id = list(fomp_params_config.keys())[0]
    fomp_excel_params = fomp_params_config[process_id]

    try:
        material_idx = mfa_system.Elements.index('material')
        dm_idx = mfa_system.Elements.index('DM')
        cc_idx = mfa_system.Elements.index('CC')
    except ValueError as e:
        raise ValueError(f"❌ FOMP Error: MFA system is missing a required element: {e}")

    # Get the total Dry Matter (DM) inflow time-series
    inflows = [f.Values for f in mfa_system.FlowDict.values() if f.P_End == process_id]
    total_inflow_values = sum(inflows) if inflows else np.zeros((num_years, num_elements))
    dm_inflow_series = total_inflow_values[:, dm_idx]

    # Assemble parameters for the pure calculation function
    dm_fraction = input_flow_composition.get('DM', 1.0)
    cc_fraction = input_flow_composition.get('CC', 0.0)
    
    params_for_calc = {
        'f_labile': fomp_excel_params.get("Inflow_fraction_f (Labile pool)", 0.7),
        'k_labile': fomp_excel_params.get("decay_k1", 0.5),
        'k_recalcitrant': fomp_excel_params.get("decay_k2", 0.025),
        'cc_dm': np.divide(cc_fraction, dm_fraction, out=np.zeros_like(cc_fraction), where=dm_fraction!=0)
    }
    
    # Initial stocks for FOMP are always zero by definition in this model
    initial_stock_labile = 0.0
    initial_stock_recalcitrant = 0.0

    # --- 2. Call the pure calculation function ---
    fomp_results = _calculate_fomp_series(
        dm_inflow_series,
        params_for_calc,
        initial_stock_labile,
        initial_stock_recalcitrant
    )

    # --- 3. Assign results back to the MFA System in a physically consistent way ---
    carbon_outflow_id = fomp_excel_params.get("outflow_id")
    environmental_outflow_id = fomp_excel_params.get("outflow_id_2")

    # Create multi-element carbon outflow vector
    carbon_outflow_values = np.zeros_like(total_inflow_values)
    outflow_carbon_mass = fomp_results['outflow_carbon']
    carbon_outflow_values[:, material_idx] = outflow_carbon_mass
    carbon_outflow_values[:, dm_idx] = outflow_carbon_mass
    carbon_outflow_values[:, cc_idx] = outflow_carbon_mass
    
    # Create multi-element environmental outflow vector
    environmental_outflow_values = np.zeros_like(total_inflow_values)
    
    # Part 1: The non-carbon part of the DECAYED dry matter
    outflow_env_mass = fomp_results['outflow_environmental']
    environmental_outflow_values[:, material_idx] += outflow_env_mass
    environmental_outflow_values[:, dm_idx] += outflow_env_mass

    # Part 2: The water from the INITIAL INPUT (Water Bypass)
    wc_idx = mfa_system.Elements.index('WC')
    input_water_mass = total_inflow_values[:, wc_idx]
    environmental_outflow_values[:, material_idx] += input_water_mass
    environmental_outflow_values[:, wc_idx] += input_water_mass

    # Assign the final calculated flows to the system
    if carbon_outflow_id in mfa_system.FlowDict:
        mfa_system.FlowDict[carbon_outflow_id].Values = carbon_outflow_values
    
    if environmental_outflow_id in mfa_system.FlowDict:
        mfa_system.FlowDict[environmental_outflow_id].Values = environmental_outflow_values

    print(f"   Total carbon output: {np.sum(fomp_results['outflow_carbon']):.2f}")
    print(f"   Total environmental output: {np.sum(fomp_results['outflow_environmental']):.2f}")

    return mfa_system

def calculate_fomp_legacy(mfa_system, fomp_params_config):
    """
    Legacy single-outflow FOMP calculation (kept for backward compatibility).
    """
    # This function remains unchanged.
    time_vector = mfa_system.IndexTable.Classification["Time"].Items
    num_years, num_elements = len(time_vector), len(mfa_system.Elements)
    process_id = list(fomp_params_config.keys())[0]
    params = fomp_params_config[process_id]
    stock_s = mfa_system.StockDict.get(f"S_{process_id}")
    initial_stock_vector = stock_s.Values[0, :].copy()
    outflow_flow_name = params.get("outflow_id")
    f, k1, k2 = params.get("f", 0), params.get("k1", 0), params.get("k2", 0)
    inflows = [flow.Values for flow in mfa_system.FlowDict.values() if flow.P_End == process_id]
    inflow_values = sum(inflows) if inflows else np.zeros((num_years, num_elements))
    new_outflow_values = np.zeros_like(inflow_values, dtype=float)
    current_stock = initial_stock_vector
    for t in range(num_years):
        outflow_t = ((inflow_values[t, :] * f) + (current_stock * k1) + (inflow_values[t, :] * k2))
        new_outflow_values[t, :] = outflow_t
        current_stock = current_stock + inflow_values[t, :] - outflow_t
    if outflow_flow_name in mfa_system.FlowDict:
        mfa_system.FlowDict[outflow_flow_name].Values = new_outflow_values
    else:
        print(f"⚠️ Warning: Outflow {outflow_flow_name} not found in FlowDict")
    return mfa_system