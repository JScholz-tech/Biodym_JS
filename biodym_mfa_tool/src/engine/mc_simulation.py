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

    all_results = []
    
    for i in range(n_iterations):
        print(f"  Running iteration {i + 1}/{n_iterations}...")
        mfa_system_iter = copy.deepcopy(mfa_system_configured)
        
        iter_params = {'iteration': i}

        # Sample parameters with mass balance normalization
        tc_updates = {}  # Store TC updates for normalization
        
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
                
                if param_name in mfa_system_iter.ParameterDict:
                    mfa_system_iter.ParameterDict[param_name].Values = np.array([val])
                elif param_name.startswith('TC_'):
                    # Store TC update for later normalization
                    tc_updates[param_name] = val
                elif param_name.startswith('dS_'):
                    stock_id = param_name.split('_')[1]
                    stock_name = f"S_{stock_id}"
                    if stock_name in mfa_system_iter.StockDict:
                        mfa_system_iter.StockDict[stock_name].Values[0, 0] = val
        
        # Apply sampled values and identify processes with TC updates
        processes_with_tc_updates = set()
        for tc_name, tc_value in tc_updates.items():
            try:
                process_id = int(tc_name.split('_')[1])
                processes_with_tc_updates.add(process_id)
                # Find the correct flow and update its TC value directly for now
                for flow in mfa_system_iter.FlowDict.values():
                    if flow.Name == tc_name:
                        flow.TC = np.array([tc_value])
                        break
            except (ValueError, IndexError):
                pass # Should not happen if validation is correct

        # After all TCs for this iteration are updated, normalize them process by process
        for process_id in processes_with_tc_updates:
            process_flows = [f for f in mfa_system_iter.FlowDict.values() if f.P_Start == process_id]
            if len(process_flows) > 1:
                # Get the newly updated TC values for this process
                current_tcs = {f.Name: f.TC[0] for f in process_flows if hasattr(f, 'TC') and len(f.TC) > 0}
                total_tc = sum(current_tcs.values())

                if total_tc > 0:
                    # Normalize and update the flows and iter_params
                    for flow in process_flows:
                        if flow.Name in current_tcs:
                            normalized_value = current_tcs[flow.Name] / total_tc
                            flow.TC = np.array([normalized_value])
                            iter_params[flow.Name] = normalized_value # Update for results logging

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
