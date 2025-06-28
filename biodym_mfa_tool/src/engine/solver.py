# -*- coding: utf-8 -*-
"""
Solver Module for the BioDYM MFA Model's Engine.

This file contains the core iterative solver that orchestrates the
calculation of the entire MFA system. It calls the specific model
functions (DSM, FOMP) in the correct sequence until the system converges.
"""
import numpy as np
import copy

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
            stock_s, stock_ds = mfa_system.StockDict[f"S_{pid}"], mfa_system.StockDict[f"dS_{pid}"]

            inflows = [f.Values for f in mfa_system.FlowDict.values() if f.P_End == pid]
            outflows = [f.Values for f in mfa_system.FlowDict.values() if f.P_Start == pid]
            total_inflows = sum(inflows) if inflows else np.zeros_like(stock_s.Values)
            total_outflows = sum(outflows) if outflows else np.zeros_like(stock_s.Values)
            dS_values = total_inflows - total_outflows
            stock_ds.Values = dS_values

            initial_stock_vector = stock_s.Values[0, :].copy()
            new_s_values = np.cumsum(np.vstack([initial_stock_vector, dS_values[:-1, :]]), axis=0)
            stock_s.Values = new_s_values

    print("--> Stock balance calculation finished.")
    return mfa_system


def run_mfa_calculation(mfa_system_setup, dsm_params, fomp_params, config, tc_updates=None):
    """
    This function is the iterative solver for the MFA system.

    It repeatedly cycles through the system, calculating flows in a specific
    order (TCs first, then special models like DSM/FOMP) until no more
    changes occur, indicating that the system has converged to a stable state.

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
    dsm_processes_run = {pid: False for pid in dsm_processes}
    fomp_processes_run = {pid: False for pid in fomp_processes}

    for i in range(15):
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
                if not dsm_processes_run[process_id]:
                    inflows_to_dsm = [f for f in mfa_system.FlowDict.values() if f.P_End == process_id]
                    if inflows_to_dsm and all(np.any(f.Values != 0) for f in inflows_to_dsm):
                        mfa_system, dsm_details_single_run = dsm_model.calculate_dynamic_stock(mfa_system, {process_id: dsm_params[process_id]})
                        dsm_details.update(dsm_details_single_run)
                        dsm_processes_run[process_id] = True
                        something_changed_in_main_loop = True

        if config.RUN_FOMP_CALCULATION:
            for process_id in fomp_processes:
                if not fomp_processes_run[process_id]:
                    inflows_to_fomp = [f for f in mfa_system.FlowDict.values() if f.P_End == process_id]
                    if inflows_to_fomp and all(np.any(f.Values != 0) for f in inflows_to_fomp):
                        mfa_system = fomp_model.calculate_fomp(mfa_system, {process_id: fomp_params[process_id]})
                        fomp_processes_run[process_id] = True
                        something_changed_in_main_loop = True

        if not something_changed_in_main_loop and i > 0:
            break

    mfa_system = calculate_final_balances(mfa_system)
    return mfa_system, dsm_details
