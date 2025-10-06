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


def enhanced_input_validation(input_flows, dsm_processes):
    """
    Enhanced validation that handles mixed input processes safely by checking
    if the total sum of inflows is greater than zero.

    Args:
        input_flows (list): List of input flows to a process.
        dsm_processes (set): Set of DSM process IDs.

    Returns:
        bool: True if the total sum of all inflows is > 0, False otherwise.
    """
    if not input_flows:
        return False

    # Check if the sum of all values in all input flows is greater than zero.
    # This is a more robust check than np.any() for each flow, as it
    # correctly handles cases where a flow is valid but has a 0 value.
    total_inflow_sum = sum(np.sum(f.Values) for f in input_flows if f.Values is not None)

    return total_inflow_sum > 0


def run_mfa_calculation(
    mfa_system_setup, dsm_params, fomp_params, config, flow_tc_map, process_logic_map, tc_updates=None
):
    """
    This function is the iterative solver for the MFA system.

    It repeatedly cycles through all process types (TC-driven, DSM, FOMP)
    in a single integrated loop, allowing dependencies between different
    model types to resolve. The system is considered converged when a full
    pass over all calculations results in no changes to any flow values.

    Args:
        mfa_system_setup (odym.MFAsystem): A fully configured but unsolved MFA system.
        dsm_params (dict): Configuration dictionary for DSM processes.
        fomp_params (dict): Configuration dictionary for FOMP processes.
        config (module): The imported config module with calculation switches.
        flow_tc_map (dict): A dictionary mapping Flow_IDs to their TC_ID names.
        process_logic_map (dict): A dictionary mapping Process_IDs to their logic ('Splitter' or 'Transformer').
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

    max_iterations = 30  # Safeguard against infinite loops

    for i in range(max_iterations):
        something_changed_in_pass = False

        # --- 1. TC-driven flows ---
        for flow in mfa_system.FlowDict.values():
            if flow.P_Start in special_processes or hasattr(flow, '_fomp_protected'):
                continue

            process_logic = process_logic_map.get(flow.P_Start)
            tc_ids = flow_tc_map.get(flow.Name)

            if not process_logic or not tc_ids:
                continue

            input_flows = [f for f in mfa_system.FlowDict.values() if f.P_End == flow.P_Start]
            if not enhanced_input_validation(input_flows, dsm_processes):
                continue

            old_values = flow.Values.copy()
            total_inflow_vector = sum(f.Values for f in input_flows)
            outflow_vector = np.zeros_like(total_inflow_vector)

            try:
                mat_idx = mfa_system.Elements.index('material')
                wc_idx = mfa_system.Elements.index('WC')
                dm_idx = mfa_system.Elements.index('DM')
                cc_idx = mfa_system.Elements.index('CC')
            except ValueError as e:
                raise ValueError(f"The model's elements are not correctly defined. Missing one of ['material', 'WC', 'DM', 'CC']. Error: {e}")

            if process_logic == 'Splitter':
                param_name = tc_ids.get('material')
                if param_name and param_name in mfa_system.ParameterDict:
                    tc_value = mfa_system.ParameterDict[param_name].Values
                    outflow_vector[:, mat_idx] = total_inflow_vector[:, mat_idx] * tc_value
                    inflow_material = total_inflow_vector[:, mat_idx]
                    wc_fraction = np.divide(total_inflow_vector[:, wc_idx], inflow_material, out=np.zeros_like(inflow_material), where=inflow_material!=0)
                    dm_fraction = np.divide(total_inflow_vector[:, dm_idx], inflow_material, out=np.zeros_like(inflow_material), where=inflow_material!=0)
                    cc_fraction = np.divide(total_inflow_vector[:, cc_idx], inflow_material, out=np.zeros_like(inflow_material), where=inflow_material!=0)
                    outflow_vector[:, wc_idx] = outflow_vector[:, mat_idx] * wc_fraction
                    outflow_vector[:, dm_idx] = outflow_vector[:, mat_idx] * dm_fraction
                    outflow_vector[:, cc_idx] = outflow_vector[:, mat_idx] * cc_fraction
            elif process_logic == 'Transformer':
                for i_elem, element in [(wc_idx, 'WC'), (dm_idx, 'DM'), (cc_idx, 'CC')]:
                    param_name = tc_ids.get(element, tc_ids.get('material'))
                    if param_name and param_name in mfa_system.ParameterDict:
                        tc_value = mfa_system.ParameterDict[param_name].Values
                        outflow_vector[:, i_elem] = total_inflow_vector[:, i_elem] * tc_value
                outflow_vector[:, mat_idx] = outflow_vector[:, wc_idx] + outflow_vector[:, dm_idx]

            flow.Values = outflow_vector
            if not np.allclose(old_values, flow.Values):
                something_changed_in_pass = True

        # --- 2. Special Models (DSM) ---
        if config.RUN_DSM_CALCULATION:
            for process_id in dsm_processes:
                inflows_to_dsm = [f for f in mfa_system.FlowDict.values() if f.P_End == process_id]
                total_inflow_sum = sum(np.sum(f.Values) for f in inflows_to_dsm)

                # --- DEBUG PRINT --- #
                inflow_names = [f.Name for f in inflows_to_dsm]
                is_ready = total_inflow_sum > 0
                print(f"[DSM DEBUG] Iteration {i}: Process {process_id}, Inflows: {inflow_names}, Total Inflow Sum: {total_inflow_sum:.2f}, Ready: {is_ready}")

                if not is_ready:
                    continue

                outflow_flow_name = next((f.Name for f in mfa_system.FlowDict.values() if f.P_Start == process_id), None)
                if not outflow_flow_name:
                    continue
                
                old_out_values = mfa_system.FlowDict[outflow_flow_name].Values.copy()

                mfa_system, dsm_details_single_run = dsm_model.calculate_dynamic_stock(
                    mfa_system, {process_id: dsm_params[process_id]}
                )
                dsm_details.update(dsm_details_single_run)

                if not np.allclose(old_out_values, mfa_system.FlowDict[outflow_flow_name].Values):
                    something_changed_in_pass = True

        # --- 3. Special Models (FOMP) ---
        if config.RUN_FOMP_CALCULATION:
            for process_id in fomp_processes:
                inflows_to_fomp = [f for f in mfa_system.FlowDict.values() if f.P_End == process_id]
                if not (inflows_to_fomp and all(np.any(f.Values != 0) for f in inflows_to_fomp)):
                    continue
                
                fomp_outflows = [f for f in mfa_system.FlowDict.values() if f.P_Start == process_id and hasattr(f, '_fomp_protected')]
                old_fomp_out_values = {f.Name: f.Values.copy() for f in fomp_outflows}

                # Calculate composition dynamically from actual input flow values
                total_inflow_values = sum(f.Values for f in inflows_to_fomp)
                
                # Calculate composition fractions from actual flow values
                material_idx = mfa_system.Elements.index('material')
                dm_idx = mfa_system.Elements.index('DM')
                cc_idx = mfa_system.Elements.index('CC')
                wc_idx = mfa_system.Elements.index('WC')
                
                # Calculate composition fractions (avoid division by zero)
                dm_fraction = np.divide(
                    total_inflow_values[:, dm_idx], 
                    total_inflow_values[:, material_idx],
                    out=np.zeros_like(total_inflow_values[:, dm_idx]),
                    where=total_inflow_values[:, material_idx] != 0
                )
                cc_fraction = np.divide(
                    total_inflow_values[:, cc_idx], 
                    total_inflow_values[:, material_idx],
                    out=np.zeros_like(total_inflow_values[:, cc_idx]),
                    where=total_inflow_values[:, material_idx] != 0
                )
                wc_fraction = np.divide(
                    total_inflow_values[:, wc_idx], 
                    total_inflow_values[:, material_idx],
                    out=np.zeros_like(total_inflow_values[:, wc_idx]),
                    where=total_inflow_values[:, material_idx] != 0
                )
                
                # Print flow composition information
                print(f"   FOMP Process {process_id} - Input Flow Composition:")
                print(f"     DM fraction: {np.mean(dm_fraction[dm_fraction > 0]):.3f} (range: {np.min(dm_fraction):.3f} - {np.max(dm_fraction):.3f})")
                print(f"     CC fraction: {np.mean(cc_fraction[cc_fraction > 0]):.3f} (range: {np.min(cc_fraction):.3f} - {np.max(cc_fraction):.3f})")
                print(f"     WC fraction: {np.mean(wc_fraction[wc_fraction > 0]):.3f} (range: {np.min(wc_fraction):.3f} - {np.max(wc_fraction):.3f})")
                
                composition = {
                    'DM': dm_fraction,
                    'CC': cc_fraction,
                    'WC': wc_fraction,
                }

                mfa_system = fomp_model.calculate_fomp(
                    mfa_system, {process_id: fomp_params[process_id]}, composition
                )

                for out_flow in fomp_outflows:
                    if out_flow.Name in old_fomp_out_values:
                        if not np.allclose(old_fomp_out_values[out_flow.Name], out_flow.Values):
                            something_changed_in_pass = True
                            break

        # --- 4. Convergence Check ---
        if not something_changed_in_pass:
            print(f"--> System converged after {i + 1} iterations.")
            break
    else:
        print(f"⚠️ WARNING: System did not converge after {max_iterations} iterations. Results may be unstable.")

    # --- Final balance calculation ---
    mfa_system = calculate_final_balances(mfa_system)

    return mfa_system, dsm_details
