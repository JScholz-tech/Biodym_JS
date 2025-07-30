# -*- coding: utf-8 -%-
"""
Monte Carlo Simulation Engine.

This module provides functions for running Monte Carlo simulations based on
parameters defined in an Excel file.
"""

import pandas as pd
import numpy as np
import copy
from . import solver

def run_mc_simulation(
    mfa_system_configured, 
    input_data, 
    dsm_params, 
    fomp_params, 
    config
):
    """
    Runs a full Monte Carlo simulation by iterating through scenarios.

    For each iteration, it updates the parameters of a deep-copied MFA system,
    runs the solver, and collects the final stock values for all elements.

    Args:
        mfa_system_configured (odym.MFAsystem): The pre-configured MFA system.
        input_data (dict): Dictionary of DataFrames from the input Excel file.
        dsm_params (dict): DSM parameters.
        fomp_params (dict): FOMP parameters.
        config (module): The main configuration module.

    Returns:
        pd.DataFrame: A DataFrame containing the results of the Monte Carlo
                      simulation, with columns for each stock and element.
                      Returns None if no uncertainty parameters are defined.
    """
    if '4_1_Uncertainty_Parameters' not in input_data or input_data['4_1_Uncertainty_Parameters'].empty:
        print("INFO: No uncertainty parameters found or sheet is empty. Skipping Monte Carlo simulation.")
        return None

    mc_params_df = input_data['4_1_Uncertainty_Parameters'].dropna(subset=['Parameter_Name'])
    
    try:
        n_iterations = int(input_data['0_Configuration'].loc[
            input_data['0_Configuration'].iloc[:, 0] == 'Monte Carlo Iterations'
        ].iloc[0, 1])
    except (KeyError, IndexError, ValueError):
        n_iterations = 10  # Default fallback
    
    print(f"\n[MC] Running Monte Carlo simulation with {n_iterations} iterations...")

    all_results = []
    
    for i in range(n_iterations):
        print(f"  Running iteration {i + 1}/{n_iterations}...")
        mfa_system_iter = copy.deepcopy(mfa_system_configured)
        
        iter_params = {'iteration': i}

        for _, row in mc_params_df.iterrows():
            param_name = row['Parameter_Name']
            dist = row['Distribution'].lower()
            val = None

            if dist == 'normal':
                if 'Mean' in row and 'StdDev' in row and pd.notna(row['Mean']) and pd.notna(row['StdDev']):
                    val = np.random.normal(row['Mean'], row['StdDev'])
            elif dist == 'uniform':
                if 'Min' in row and 'Max' in row and pd.notna(row['Min']) and pd.notna(row['Max']):
                    val = np.random.uniform(row['Min'], row['Max'])

            if val is not None:
                iter_params[param_name] = val
                if param_name in mfa_system_iter.ParameterDict:
                    mfa_system_iter.ParameterDict[param_name].Values = np.array([val])
                elif param_name.startswith('TC_'):
                    for flow in mfa_system_iter.FlowDict.values():
                        if flow.Name == param_name:
                            flow.TC = val
                            break
                elif param_name.startswith('dS_'):
                    stock_id = param_name.split('_')[1]
                    stock_name = f"S_{stock_id}"
                    if stock_name in mfa_system_iter.StockDict:
                        mfa_system_iter.StockDict[stock_name].Values[0, 0] = val

        mfa_results_iter, _ = solver.run_mfa_calculation(
            mfa_system_iter, dsm_params, fomp_params, config
        )

        iter_stock_results = {}
        for stock_name, stock_obj in mfa_results_iter.StockDict.items():
            if stock_name.startswith('S_'):
                for el_idx, el_name in enumerate(mfa_results_iter.Elements):
                    col_name = f"{stock_name}_{el_name}_mc"
                    iter_stock_results[col_name] = stock_obj.Values[-1, el_idx]
        
        all_results.append({**iter_params, **iter_stock_results})

    print("[MC] Monte Carlo simulation completed.")
    
    results_df = pd.DataFrame(all_results)
    
    try:
        results_df.to_excel("data/02_output/mc_results_detailed.xlsx", index=False)
        print("[MC] Detailed Monte Carlo results exported to 'data/02_output/mc_results_detailed.xlsx'")
    except Exception as e:
        print(f"WARNING: Could not export MC results: {e}")
        
    return results_df
