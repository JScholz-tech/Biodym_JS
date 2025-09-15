# -*- coding: utf-8 -*-
"""
Solver Module for the BioDYM MFA Model's Engine.

This file contains the core iterative solver that orchestrates the
calculation of the entire MFA system. It calls the specific model
functions (DSM, FOMP) in the correct sequence until the system converges.
"""

import numpy as np
import copy
import sys
import os

# Add ODYM path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'framework', 'ODYM-master_20241127', 'odym', 'modules'))
import ODYM_Classes as msc

# Import other engine components
from . import dsm_model
from . import fomp_model


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

    for pid in {p.ID for p in mfa_system.ProcessList}:
        if f"S_{pid}" in mfa_system.StockDict:
            stock_s, stock_ds = (
                mfa_system.StockDict[f"S_{pid}"],
                mfa_system.StockDict[f"dS_{pid}"],
            )

            inflows = [f.Values for f in mfa_system.FlowDict.values() if f.P_End == pid]
            outflows = [
                f.Values for f in mfa_system.FlowDict.values() if f.P_Start == pid
            ]
            total_inflows = sum(inflows) if inflows else np.zeros_like(stock_s.Values)
            total_outflows = (
                sum(outflows) if outflows else np.zeros_like(stock_s.Values)
            )
            dS_values = total_inflows - total_outflows
            stock_ds.Values = dS_values

            initial_stock_vector = stock_s.Values[0, :].copy()
            new_s_values = np.cumsum(
                np.vstack([initial_stock_vector, dS_values[:-1, :]]), axis=0
            )
            stock_s.Values = new_s_values

    print("--> Stock balance calculation finished.")
    return mfa_system


# --- BioDYM Extension: Stock-Outflow TCs ---
# This function is a custom addition to ODYM for handling
# outflows directly from initial stocks.
def process_stock_outflow_tcs(mfa_system):
    """
    BioDYM Extension to ODYM:
    Processes stock-outflow transfer coefficients to consume initial stocks.
    This is NOT part of the standard ODYM framework.
    """
    print("--> Processing stock-outflow transfer coefficients...")
    
    # Check if stock-outflow TCs were defined during setup
    if hasattr(mfa_system, 'stock_outflow_tcs'):
        for process_id, tc_info in mfa_system.stock_outflow_tcs.items():
            destination_process = tc_info['destination_process']
            consumption_rate = tc_info['consumption_rate']
            initial_stock = tc_info['initial_stock']
            
            # Create stock-outflow flow
            flow_name = f"F_{process_id}_{destination_process}_stock"
            if flow_name not in mfa_system.FlowDict:
                mfa_system.FlowDict[flow_name] = msc.Flow(
                    Name=flow_name, 
                    P_Start=process_id, 
                    P_End=destination_process, 
                    Indices="t,e"
                )
            
            # Initialize flow values if not already done
            flow = mfa_system.FlowDict[flow_name]
            if flow.Values is None:
                # Initialize with zeros: shape = (number of years, number of elements)
                n_years = len(mfa_system.IndexTable.Classification["Time"].Items)
                n_elements = len(mfa_system.Elements)
                flow.Values = np.zeros((n_years, n_elements))
            
            # Calculate annual consumption
            annual_consumption = initial_stock * consumption_rate
            
            # Set flow values (constant over time)
            for t in range(len(flow.Values)):
                flow.Values[t, :] = annual_consumption
            
            print(f"--> Created stock-outflow flow: {flow_name} = {annual_consumption[0]:.1f} Mg/year")
    else:
        print("--> No stock-outflow TCs found in system setup")
    
    print("--> Stock-outflow TC processing finished.")
    return mfa_system


def run_mfa_calculation(
    mfa_system_setup, dsm_params, fomp_params, config, tc_updates=None
):
    """
    This function is the iterative solver for the MFA system.

    It repeatedly cycles through the system a fixed number of times to ensure
    that systems with circular dependencies converge to a stable state.
    It uses a substance-level calculation for all TC-based flows.

    Args:
        mfa_system_setup (odym.MFAsystem): A fully configured but unsolved MFA system.
        dsm_params (dict): Configuration dictionary for DSM processes.
        fomp_params (dict): Configuration dictionary for FOMP processes.
        config (module): The imported config module with calculation switches.
        tc_updates (dict, optional): A dictionary of sampled TC values for an MC run.

    Returns:
        tuple: A tuple containing the solved mfa_system and a dictionary
               with detailed DSM results for plotting.
    """
    mfa_system = copy.deepcopy(mfa_system_setup)

    if tc_updates:
        for param_name, new_value in tc_updates.items():
            if param_name in mfa_system.ParameterDict:
                mfa_system.ParameterDict[param_name].Values = new_value

    dsm_details = {}
    dsm_processes = set(dsm_params.keys())
    fomp_processes = set(fomp_params.keys())
    special_processes = dsm_processes.union(fomp_processes)

    for i in range(15):
        something_changed_in_main_loop = False
        
        # Re-introduce the inner iterative loop for TCs to stabilize
        while True:
            something_changed_in_tc_loop = False
            
            for flow in mfa_system.FlowDict.values():
                if flow.P_Start in special_processes or hasattr(flow, '_fomp_protected'):
                    continue

                base_tc_name = f"TC_{'_'.join(flow.Name.split('_')[1:3])}"
                material_tc_param = f"{base_tc_name}_material"

                if material_tc_param in mfa_system.ParameterDict:
                    input_flows = [f for f in mfa_system.FlowDict.values() if f.P_End == flow.P_Start]
                    
                    if not input_flows or not all(np.any(f.Values != 0) or f.P_Start == 0 for f in input_flows):
                        continue

                    # Store old values to check for changes
                    old_values = flow.Values.copy()

                    # --- New Substance-Level Calculation with Physical Dependency ---
                    total_inflow_vector = sum(f.Values for f in input_flows)
                    outflow_vector = np.zeros_like(total_inflow_vector)

                    try:
                        mat_idx = mfa_system.Elements.index('material')
                        wc_idx = mfa_system.Elements.index('WC')
                        dm_idx = mfa_system.Elements.index('DM')
                        cc_idx = mfa_system.Elements.index('CC')
                    except ValueError as e:
                        raise ValueError(f"The model's elements are not correctly defined. Missing one of ['material', 'WC', 'DM', 'CC']. Error: {e}")

                    # Calculate independent components (WC, DM, CC) from their TCs
                    for i_elem, element in [(wc_idx, 'WC'), (dm_idx, 'DM'), (cc_idx, 'CC')]:
                        param_name = f"{base_tc_name}_{element}"
                        if param_name in mfa_system.ParameterDict:
                            tc_value = mfa_system.ParameterDict[param_name].Values
                            outflow_vector[:, i_elem] = total_inflow_vector[:, i_elem] * tc_value
                    
                    # Enforce physical dependency: material = WC + DM
                    outflow_vector[:, mat_idx] = outflow_vector[:, wc_idx] + outflow_vector[:, dm_idx]
                    
                    # Update the flow's values with the calculated substance vector
                    flow.Values = outflow_vector

                    if not np.allclose(old_values, flow.Values):
                        something_changed_in_tc_loop = True
                        something_changed_in_main_loop = True

            if not something_changed_in_tc_loop:
                break

        # --- Special Models (DSM and FOMP) ---
        if config.RUN_DSM_CALCULATION:
            for process_id in dsm_processes:
                inflows_to_dsm = [f for f in mfa_system.FlowDict.values() if f.P_End == process_id]
                if inflows_to_dsm and all(np.any(f.Values != 0) for f in inflows_to_dsm):
                    mfa_system, dsm_details_single_run = dsm_model.calculate_dynamic_stock(
                        mfa_system, {process_id: dsm_params[process_id]}
                    )
                    dsm_details.update(dsm_details_single_run)
                    something_changed_in_main_loop = True

        if config.RUN_FOMP_CALCULATION:
            for process_id in fomp_processes:
                inflows_to_fomp = [f for f in mfa_system.FlowDict.values() if f.P_End == process_id]
                if inflows_to_fomp and all(np.any(f.Values != 0) for f in inflows_to_fomp):
                    primary_input_flow = inflows_to_fomp[0]
                    flow_name = primary_input_flow.Name
                    try:
                        composition = {
                            'DM': mfa_system.ParameterDict[f'DM_{flow_name}'].Values,
                            'CC': mfa_system.ParameterDict[f'CC_{flow_name}'].Values,
                            'WC': mfa_system.ParameterDict[f'WC_{flow_name}'].Values,
                        }
                    except KeyError as e:
                        print(f"❌ Error: Missing composition parameter for FOMP input flow {flow_name}: {e}")
                        continue

                    mfa_system = fomp_model.calculate_fomp(
                        mfa_system, {process_id: fomp_params[process_id]}, input_flow_composition=composition
                    )
                    something_changed_in_main_loop = True
                    for f_out in [f for f in mfa_system.FlowDict.values() if f.P_Start == process_id]:
                        f_out._fomp_protected = True

        if not something_changed_in_main_loop and i > 0:
            break

    # --- 3. Finalization ---
    mfa_system = process_stock_outflow_tcs(mfa_system)
    mfa_system = calculate_final_balances(mfa_system)
    return mfa_system, dsm_details
