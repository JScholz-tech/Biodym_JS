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

def validate_mc_parameters(mc_params_df, mfa_system):
    """
    Validates MC parameters to ensure mass balance and prevent conflicts.
    
    Args:
        mc_params_df (pd.DataFrame): MC parameters from Excel
        mfa_system (odym.MFAsystem): The MFA system to validate against
        
    Returns:
        tuple: (validated_params_df, warnings_list)
    """
    warnings = []
    validated_params = mc_params_df.copy()
    
    # Check for dynamic TC conflicts
    dynamic_tc_processes = set()
    for flow in mfa_system.FlowDict.values():
        if hasattr(flow, 'TC') and isinstance(flow.TC, np.ndarray) and len(flow.TC) > 1:
            process_id = flow.P_Start
            dynamic_tc_processes.add(process_id)
    
    # Check for TC mass balance issues
    tc_params = validated_params[validated_params['Parameter_Name'].str.startswith('TC_', na=False)]
    
    for _, row in tc_params.iterrows():
        tc_name = row['Parameter_Name']
        # Extract process ID from TC name (e.g., TC_05_06 -> process 5)
        try:
            process_id = int(tc_name.split('_')[1])
            
            # Check if this process has dynamic TCs
            if process_id in dynamic_tc_processes:
                warnings.append(f"⚠️ WARNING: {tc_name} conflicts with dynamic TCs in process {process_id}")
            
            # Check if this process has multiple outputs
            process_flows = [f for f in mfa_system.FlowDict.values() if f.P_Start == process_id]
            if len(process_flows) > 1:
                # Check if all TCs for this process are defined in MC
                process_tcs = [p for p in tc_params['Parameter_Name'] if p.startswith(f'TC_{process_id}_')]
                if len(process_tcs) < len(process_flows):
                    missing_tcs = [f.Name for f in process_flows if f.Name not in process_tcs]
                    warnings.append(f"⚠️ WARNING: Process {process_id} has {len(process_flows)} outputs but only {len(process_tcs)} TCs in MC. Missing: {missing_tcs}")
                    
        except (ValueError, IndexError):
            warnings.append(f"⚠️ WARNING: Could not parse process ID from {tc_name}")
    
    return validated_params, warnings

def normalize_tcs_for_process(mfa_system, process_id, varied_tc_name, varied_tc_value):
    """
    Ensures all TCs for a process sum to 1.0 by normalizing them.
    
    Args:
        mfa_system (odym.MFAsystem): The MFA system
        process_id (int): Process ID to normalize
        varied_tc_name (str): Name of the TC that was varied
        varied_tc_value (float): New value for the varied TC
        
    Returns:
        dict: Dictionary of normalized TC values
    """
    # Get all flows for this process
    process_flows = [f for f in mfa_system.FlowDict.values() if f.P_Start == process_id]
    
    if len(process_flows) <= 1:
        # Single output process - no normalization needed
        return {varied_tc_name: varied_tc_value}
    
    # Get current TC values
    current_tcs = {}
    for flow in process_flows:
        if hasattr(flow, 'TC'):
            if isinstance(flow.TC, np.ndarray):
                current_tcs[flow.Name] = flow.TC[0] if len(flow.TC) > 0 else 0.0
            else:
                current_tcs[flow.Name] = float(flow.TC)
        else:
            current_tcs[flow.Name] = 0.0
    
    # Update the varied TC
    current_tcs[varied_tc_name] = varied_tc_value
    
    # Calculate normalization factor
    total_tc = sum(current_tcs.values())
    if total_tc > 0:
        normalization_factor = 1.0 / total_tc
        
        # Apply normalization to all TCs
        normalized_tcs = {}
        for flow in process_flows:
            normalized_tcs[flow.Name] = current_tcs[flow.Name] * normalization_factor
            # Update the flow's TC value
            flow.TC = np.array([normalized_tcs[flow.Name]])
        
        return normalized_tcs
    else:
        # If total is 0, distribute equally
        equal_tc = 1.0 / len(process_flows)
        normalized_tcs = {}
        for flow in process_flows:
            normalized_tcs[flow.Name] = equal_tc
            flow.TC = np.array([equal_tc])
        
        return normalized_tcs

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
    
    IMPORTANT: This function ensures mass balance by normalizing TCs to sum to 1.0
    and prevents conflicts between dynamic TCs and MC simulation.
    
    ## BioDYM Refactoring Note ##
    This function has been modified to correctly handle uncertainty for 'Splitter'
    processes. When a '..._material' TC is made uncertain, the sampled value is
    propagated to the corresponding '_WC', '_DM', and '_CC' parameters to ensure
    the solver uses the uncertain value.
    """
    if '4_1_Uncertainty_Parameters' not in input_data or input_data['4_1_Uncertainty_Parameters'].empty:
        print("INFO: No uncertainty parameters found or sheet is empty. Skipping Monte Carlo simulation.")
        return None

    mc_params_df = input_data['4_1_Uncertainty_Parameters'].dropna(subset=['Parameter_Name'])
    
    # Validate MC parameters and check for conflicts
    validated_params, warnings = validate_mc_parameters(mc_params_df, mfa_system_configured)
    
    # Print warnings if any
    if warnings:
        print("\n[MC] Parameter Validation Warnings:")
        for warning in warnings:
            print(f"  {warning}")
        print()
    
    # Get MC iterations from config object (preferred) or fallback to Excel data
    try:
        n_iterations = int(config.MC_ITERATIONS)
    except (AttributeError, ValueError):
        try:
            n_iterations = int(input_data['0_Configuration'].loc[
                input_data['0_Configuration'].iloc[:, 0].str.strip() == 'MC_Iterations'
            ].iloc[0, 1])
        except (KeyError, IndexError, ValueError):
            n_iterations = 10  # Default fallback
    
    print(f"\n[MC] Running Monte Carlo simulation with {n_iterations} iterations...")
    print(f"[MC] Using {len(validated_params)} validated parameters...")

    # --- FIX: Build mappings to check for Splitter TCs ---
    process_defs = input_data.get('2_1_Definition_Processes')
    static_tc_defs = input_data.get('2_3_Process_TCs')
    
    logic_map = {}
    if process_defs is not None:
        logic_map = process_defs.set_index('ID')['Process_Logic'].to_dict()

    tc_to_process_map = {}
    if static_tc_defs is not None:
        clean_tc_defs = static_tc_defs.dropna(subset=['TC_ID', 'Process_ID'])
        tc_to_process_map = clean_tc_defs.set_index('TC_ID')['Process_ID'].astype(int).to_dict()
    # --- END FIX ---

    all_results = []
    
    for i in range(n_iterations):
        print(f"  Running iteration {i + 1}/{n_iterations}...")
        mfa_system_iter = copy.deepcopy(mfa_system_configured)
        
        iter_params = {'iteration': i}

        # Sample parameters
        for _, row in validated_params.iterrows():
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
                
                # --- FIX: Check if this is a material TC for a Splitter process ---
                is_splitter_material_tc = False
                tc_id = None
                if param_name.endswith('_material'):
                    _tc_id = param_name.replace('_material', '')
                    if _tc_id in tc_to_process_map:
                        process_id = tc_to_process_map[_tc_id]
                        if logic_map.get(process_id) == 'Splitter':
                            is_splitter_material_tc = True
                            tc_id = _tc_id
                
                # If it is, propagate the sampled value to all substance TCs
                if is_splitter_material_tc:
                    elements_to_update = ['material', 'WC', 'DM', 'CC']
                    for element in elements_to_update:
                        full_param_name = f"{tc_id}_{element}"
                        if full_param_name in mfa_system_iter.ParameterDict:
                            mfa_system_iter.ParameterDict[full_param_name].Values = np.array([val])
                
                # If not a special splitter case, use original logic
                else:
                    if param_name in mfa_system_iter.ParameterDict:
                        mfa_system_iter.ParameterDict[param_name].Values = np.array([val])
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
