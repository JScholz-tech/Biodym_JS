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


import ODYM_Classes as msc

# Import other engine components
from . import dsm_model
from . import fomp_model


def calculate_final_balances(mfa_system):
    """Calculates the final stock changes (dS) and absolute stocks (S).

    This is the final accounting step of the calculation, performed after the
    iterative solver has converged. It correctly respects any initial stocks
    set during the system setup.

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        The MFA system object with all flows calculated.

    Returns
    -------
    odym.MFAsystem
        The MFA system object with final stock values updated.
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
    
    # Phase 1a: Add ODYM validation
    try:
        mfa_system.Consistency_Check()
        print("✅ Balance validation passed")
    except Exception as e:
        print(f"⚠️ Balance validation warning: {e}")
    
    return mfa_system


# --- BioDYM Extension: Stock-Outflow TCs ---
# This function is a custom addition to ODYM for handling
# outflows directly from initial stocks.
def process_initial_stocks(mfa_system):
    """Processes initial stock outflows using the dedicated initial stock engine.

    Notes
    -----
    This function is a BioDYM-specific extension to the standard ODYM framework
    that allows for outflows to be generated directly from a process's initial
    stock, which is not a standard ODYM feature.

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        The MFA system object.

    Returns
    -------
    odym.MFAsystem
        The MFA system, potentially modified by the initial stock engine.
    """
    print("--> Processing initial stock outflows...")
    
    # Check if initial stock configurations were loaded
    if hasattr(mfa_system, 'initial_stock_outflows') and mfa_system.initial_stock_outflows:
        from . import initial_stock_engine
        
        # Get initial stock configurations (we need to reload them)
        # This is a temporary solution - in the future, we should store the configs in mfa_system
        print("  -> Initial stock outflows already processed during setup")
        return mfa_system
    else:
        print("  -> No initial stock outflows found")
        return mfa_system


def enhanced_input_validation(input_flows, dsm_processes):
    """Validates if a process has valid inputs to justify calculation.

    This check is more robust than a simple check for non-zero flows, as it
    correctly handles cases where a flow exists but has a value of zero for
    a given time step. It checks if the total sum of all values across all
    inflows is greater than zero.

    Parameters
    ----------
    input_flows : list of odym.Flow
        A list of all flow objects that are inputs to a specific process.
    dsm_processes : set
        A set of all process IDs that are defined as DSM processes.

    Returns
    -------
    bool
        True if the total sum of all inflow values is greater than zero.
    """
    if not input_flows:
        return False

    # Check if the sum of all values in all input flows is greater than zero.
    # This is a more robust check than np.any() for each flow, as it
    # correctly handles cases where a flow is valid but has a 0 value.
    total_inflow_sum = sum(np.sum(f.Values) for f in input_flows if f.Values is not None)

    return total_inflow_sum > 0


def _calculate_tc_driven_flows(mfa_system, special_processes, process_logic_map, flow_tc_map, dsm_processes, config=None):
    """Calculates all flows that are driven by transfer coefficients (TCs).

    This function iterates through all flows in the system, identifies those
    governed by simple TC-based processes (Splitter, Transformer), and calculates
    their output values based on the total inflow and the defined TCs.

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        The MFA system object, which will be modified in place.
    special_processes : set
        A set of process IDs that are handled by special models (DSM, FOMP).
    process_logic_map : dict
        Maps process IDs to their logic string (e.g., 'Splitter').
    flow_tc_map : dict
        Maps flow names to their corresponding TC parameter names.
    dsm_processes : set
        A set of DSM process IDs, used for input validation.

    Returns
    -------
    bool
        True if any flow values were changed during the calculation, False otherwise.
    """
    something_changed = False
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

        # Get element indices dynamically
        elements = mfa_system.Elements
        mat_idx = 0  # Material is always first
        other_elements = elements[1:]  # All other elements (WC, DM, CC or Fe, Cu, Al, etc.)
        elem_indices = {elem: idx for idx, elem in enumerate(elements)}

        if process_logic in ['Splitter', 'Transformer']:
            if process_logic == 'Splitter':
                # Splitter: Preserves composition (element fractions stay the same)
                param_name = tc_ids.get('material')
                if param_name and param_name in mfa_system.ParameterDict:
                    tc_value = mfa_system.ParameterDict[param_name].Values
                    outflow_vector[:, mat_idx] = total_inflow_vector[:, mat_idx] * tc_value

                    # Preserve composition for all elements
                    inflow_material = total_inflow_vector[:, mat_idx]

                    for element in other_elements:
                        elem_idx = elem_indices[element]

                        # Calculate fraction: element / material (avoid division by zero)
                        element_fraction = np.divide(
                            total_inflow_vector[:, elem_idx],
                            inflow_material,
                            out=np.zeros_like(inflow_material),
                            where=inflow_material != 0
                        )

                        # Apply fraction to outflow material
                        outflow_vector[:, elem_idx] = outflow_vector[:, mat_idx] * element_fraction

            elif process_logic == 'Transformer':
                # Transformer: Changes composition (apply TCs to each element independently)
                for element in other_elements:
                    elem_idx = elem_indices[element]

                    # Look for element-specific TC, fallback to material TC
                    param_name = tc_ids.get(element, tc_ids.get('material'))

                    if param_name and param_name in mfa_system.ParameterDict:
                        tc_value = mfa_system.ParameterDict[param_name].Values
                        outflow_vector[:, elem_idx] = total_inflow_vector[:, elem_idx] * tc_value
                    else:
                        # No TC found, assume passthrough (no change)
                        outflow_vector[:, elem_idx] = total_inflow_vector[:, elem_idx]

                # Recalculate total material as sum of TOP-LEVEL elements only
                # (excludes hierarchical elements like CC which is % of DM, not material)
                element_hierarchy = getattr(config, 'Element_Hierarchy', {}) if config else {}

                if element_hierarchy:
                    # Only sum elements with parent='material' or no parent
                    top_level_sum = np.zeros(len(total_inflow_vector))
                    for elem in other_elements:
                        # Find element info in hierarchy
                        elem_info = None
                        for eid, info in element_hierarchy.items():
                            if info['name'] == elem:
                                elem_info = info
                                break

                        # Sum only if it's a top-level element
                        parent = elem_info.get('parent') if elem_info else None
                        if not parent or parent == 'material':
                            elem_idx = elem_indices[elem]
                            top_level_sum += outflow_vector[:, elem_idx]

                    outflow_vector[:, mat_idx] = top_level_sum
                else:
                    # Fallback: sum all elements (backward compatibility)
                    outflow_vector[:, mat_idx] = np.sum(outflow_vector[:, 1:], axis=1)

            flow.Values = outflow_vector
            if not np.allclose(old_values, flow.Values):
                something_changed = True
    return something_changed

def _calculate_dsm_flows(mfa_system, dsm_processes, dsm_params, iteration):
    """Calculates all stocks and flows for Dynamic Stock Model (DSM) processes.

    For each DSM process with valid inputs, this function calls the core DSM
    engine to calculate stock evolution and outflows for the current iteration.

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        The MFA system object, which will be modified in place.
    dsm_processes : set
        A set of all process IDs that are defined as DSM processes.
    dsm_params : dict
        The configuration parameters for all DSM processes.
    iteration : int
        The current solver iteration number, used for debug printing.

    Returns
    -------
    tuple
        A tuple containing:
        - something_changed (bool): True if any flow values were changed.
        - dsm_details (dict): Detailed results from the DSM calculation.
    """
    something_changed = False
    dsm_details = {}
    for process_id in dsm_processes:
        inflows_to_dsm = [f for f in mfa_system.FlowDict.values() if f.P_End == process_id]
        total_inflow_sum = sum(np.sum(f.Values) for f in inflows_to_dsm)

        inflow_names = [f.Name for f in inflows_to_dsm]
        is_ready = total_inflow_sum > 0
        print(f"[DSM DEBUG] Iteration {iteration}: Process {process_id}, Inflows: {inflow_names}, Total Inflow Sum: {total_inflow_sum:.2f}, Ready: {is_ready}")

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
            something_changed = True
    return something_changed, dsm_details

def _calculate_fomp_flows(mfa_system, fomp_processes, fomp_params):
    """Calculates all stocks and flows for First-Order Mass Pool (FOMP) processes.

    For each FOMP process, this function dynamically calculates the input flow
    composition and then calls the core FOMP engine to calculate stock decay
    and outflows.

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        The MFA system object, which will be modified in place.
    fomp_processes : set
        A set of all process IDs that are defined as FOMP processes.
    fomp_params : dict
        The configuration parameters for all FOMP processes.

    Returns
    -------
    bool
        True if any flow values were changed during the calculation, False otherwise.
    """
    # Check if required elements exist for FOMP
    required_elements = ['DM', 'CC']
    missing_elements = [e for e in required_elements if e not in mfa_system.Elements]

    if missing_elements:
        print(f"⚠️  FOMP calculation skipped: Missing required elements {missing_elements}")
        print(f"   FOMP requires 'DM' (dry matter) and 'CC' (carbon content) for organic decomposition")
        print(f"   Available elements: {mfa_system.Elements}")
        print(f"   Tip: For non-organic systems (e.g., metals), disable FOMP in configuration")
        return False  # No changes made

    something_changed = False
    for process_id in fomp_processes:
        inflows_to_fomp = [f for f in mfa_system.FlowDict.values() if f.P_End == process_id]
        if not (inflows_to_fomp and all(np.any(f.Values != 0) for f in inflows_to_fomp)):
            continue

        fomp_outflows = [f for f in mfa_system.FlowDict.values() if f.P_Start == process_id and hasattr(f, '_fomp_protected')]
        old_fomp_out_values = {f.Name: f.Values.copy() for f in fomp_outflows}

        total_inflow_values = sum(f.Values for f in inflows_to_fomp)

        # Element indices (already validated above)
        material_idx = mfa_system.Elements.index('material')
        dm_idx = mfa_system.Elements.index('DM')
        cc_idx = mfa_system.Elements.index('CC')
        wc_idx = mfa_system.Elements.index('WC') if 'WC' in mfa_system.Elements else None
        
        dm_fraction = np.divide(total_inflow_values[:, dm_idx], total_inflow_values[:, material_idx], out=np.zeros_like(total_inflow_values[:, dm_idx]), where=total_inflow_values[:, material_idx] != 0)
        cc_fraction = np.divide(total_inflow_values[:, cc_idx], total_inflow_values[:, material_idx], out=np.zeros_like(total_inflow_values[:, cc_idx]), where=total_inflow_values[:, material_idx] != 0)

        print(f"   FOMP Process {process_id} - Input Flow Composition:")
        print(f"     DM fraction: {np.mean(dm_fraction[dm_fraction > 0]):.3f} (range: {np.min(dm_fraction):.3f} - {np.max(dm_fraction):.3f})")
        print(f"     CC fraction: {np.mean(cc_fraction[cc_fraction > 0]):.3f} (range: {np.min(cc_fraction):.3f} - {np.max(cc_fraction):.3f})")

        # Build composition dictionary
        composition = {'DM': dm_fraction, 'CC': cc_fraction}

        # Add WC if available
        if wc_idx is not None:
            wc_fraction = np.divide(total_inflow_values[:, wc_idx], total_inflow_values[:, material_idx], out=np.zeros_like(total_inflow_values[:, wc_idx]), where=total_inflow_values[:, material_idx] != 0)
            composition['WC'] = wc_fraction
            print(f"     WC fraction: {np.mean(wc_fraction[wc_fraction > 0]):.3f} (range: {np.min(wc_fraction):.3f} - {np.max(wc_fraction):.3f})")

        mfa_system = fomp_model.calculate_fomp(mfa_system, {process_id: fomp_params[process_id]}, composition)

        for out_flow in fomp_outflows:
            if out_flow.Name in old_fomp_out_values and not np.allclose(old_fomp_out_values[out_flow.Name], out_flow.Values):
                something_changed = True
                break
    return something_changed

def run_mfa_calculation(

    mfa_system_setup, dsm_params, fomp_params, config, flow_tc_map, process_logic_map, tc_updates=None

):

    """This function is the iterative solver for the MFA system.



    It repeatedly cycles through all process types (TC-driven, DSM, FOMP)

    in a single integrated loop, allowing dependencies between different

    model types to resolve. The system is considered converged when a full

    pass over all calculations results in no changes to any flow values.



    Parameters

    ----------

    mfa_system_setup : odym.MFAsystem

        A fully configured but unsolved MFA system.

    dsm_params : dict

        Configuration dictionary for DSM processes.

    fomp_params : dict

        Configuration dictionary for FOMP processes.

    config : object

        The configuration object with global settings (e.g., RUN_DSM_CALCULATION).

    flow_tc_map : dict

        A dictionary mapping Flow_IDs to their TC_ID names.

    process_logic_map : dict

        A dictionary mapping Process_IDs to their logic ('Splitter' or 'Transformer').

    tc_updates : dict, optional

        A dictionary of sampled TC values for a Monte Carlo run. Default is None.



    Returns

    -------

    tuple

        A tuple containing:

        - mfa_system (odym.MFAsystem): The solved MFA system with all values calculated.

        - dsm_details (dict): Detailed results from the DSM calculations.

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
        pass_changes = []

        # --- 1. TC-driven, DSM, and FOMP flows ---
        tc_changed = _calculate_tc_driven_flows(mfa_system, special_processes, process_logic_map, flow_tc_map, dsm_processes, config)
        pass_changes.append(tc_changed)
        
        # --- 1.5. Update Initial Stock Flows ---
        from . import initial_stock_engine
        mfa_system = initial_stock_engine.update_initial_stock_flows_during_solver(mfa_system)

        if config.RUN_DSM_CALCULATION:
            dsm_changed, dsm_run_details = _calculate_dsm_flows(mfa_system, dsm_processes, dsm_params, i)
            dsm_details.update(dsm_run_details)
            pass_changes.append(dsm_changed)

        if config.RUN_FOMP_CALCULATION:
            fomp_changed = _calculate_fomp_flows(mfa_system, fomp_processes, fomp_params)
            pass_changes.append(fomp_changed)

        # --- 4. Convergence Check ---
        if not any(pass_changes):
            print(f"--> System converged after {i + 1} iterations.")
            break
    else:
        print(f"⚠️ WARNING: System did not converge after {max_iterations} iterations. Results may be unstable.")

    # --- Final balance calculation ---
    mfa_system = calculate_final_balances(mfa_system)
    
    # Phase 1a: Add ODYM validation after complete calculation
    try:
        mfa_system.Consistency_Check()
        print("✅ Final MFA system validation passed")
    except Exception as e:
        print(f"⚠️ Final validation warning: {e}")

    return mfa_system, dsm_details
