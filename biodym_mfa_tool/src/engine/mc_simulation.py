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
from src import data_loader
from src.utils import sample_parameters

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
    mfa_system_setup, input_data, dsm_params, fomp_params, config, process_logic_map, flow_tc_map
):
    """
    Runs a Monte Carlo simulation by repeatedly sampling parameters and running
    the MFA calculation.

    Args:
        mfa_system_setup (odym.MFAsystem): A fully configured but unsolved MFA system.
        input_data (dict): The complete dictionary of data from the Excel file.
        dsm_params (dict): Configuration dictionary for DSM processes.
        fomp_params (dict): Configuration dictionary for FOMP processes.
        config (object): The configuration object with simulation settings.
        process_logic_map (dict): A map from process ID to its logic ('Splitter'/'Transformer').

    Returns:
        pd.DataFrame: A DataFrame containing the results of all Monte Carlo iterations.
    """
    # --- 1. Configuration ---
    n_iterations = getattr(config, 'Monte_Carlo_Iterations', 100)
    uncertainty_params = data_loader.load_uncertainty_definitions(input_data)

    if not uncertainty_params:
        print("\n[MC] No uncertainty parameters defined. Skipping simulation.")
        return None

    print(f"\n[MC] Running Monte Carlo simulation with {n_iterations} iterations...")

    # --- 2. Build maps for efficient lookup ---
    # Map TC names back to their process ID and get all TC names for a flow
    tc_info_map = {}
    static_tc_defs = input_data.get('2_3_Process_TCs')
    if static_tc_defs is not None:
        for _, row in static_tc_defs.iterrows():
            process_id = row.get('Process_ID')
            material_tc = row.get('TC_material_ID')
            if pd.notna(process_id) and pd.notna(material_tc):
                all_tcs = [
                    row.get(f'TC_{elem}_ID')
                    for elem in mfa_system_setup.Elements
                    if f'TC_{elem}_ID' in row and pd.notna(row.get(f'TC_{elem}_ID'))
                ]
                # For any TC name in this flow, we can find its process and sibling TCs
                for tc_name in all_tcs:
                    tc_info_map[tc_name] = {
                        'process_id': int(process_id),
                        'sibling_tcs': all_tcs,
                    }

    # --- 3. Main Simulation Loop ---
    results_list = []
    print(f"[MC] Using {len(uncertainty_params)} validated parameters...")

    for i in range(n_iterations):
        if (i + 1) % 10 == 0:
            print(f"  ... iteration {i + 1}/{n_iterations}")

        # --- 3a. Sample parameters ---
        sampled_params = sample_parameters(uncertainty_params)
        tc_updates = sampled_params.copy()

        # --- 3b. Propagate Splitter Uncertainty ---
        for param_name, sample_value in sampled_params.items():
            if param_name in tc_info_map:
                info = tc_info_map[param_name]
                process_id = info['process_id']
                logic = process_logic_map.get(process_id)

                if logic == 'Splitter':
                    # For a splitter, apply the sampled value to all sibling TCs
                    for sibling_tc in info['sibling_tcs']:
                        tc_updates[sibling_tc] = sample_value

        # --- 3c. Run Solver ---
        mfa_system_run, _ = solver.run_mfa_calculation(
            mfa_system_setup,
            dsm_params,
            fomp_params,
            config,
            flow_tc_map=flow_tc_map, # Pass the map from the setup system
            process_logic_map=process_logic_map,
            tc_updates=tc_updates,
        )

        # --- 3d. Collect Results ---
        iteration_results = {"iteration": i + 1}
        for param, value in tc_updates.items():
            iteration_results[f"{param}_sample"] = value
        for stock in mfa_system_run.StockDict.values():
            for i_elem, element_name in enumerate(mfa_system_run.Elements):
                iteration_results[f"{stock.Name}_{element_name}"] = stock.Values[-1, i_elem]  # Final year, all element values
        results_list.append(iteration_results)

    print("[MC] Simulation finished.")
    return pd.DataFrame(results_list)
