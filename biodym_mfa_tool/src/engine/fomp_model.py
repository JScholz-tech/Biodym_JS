# -*- coding: utf-8 -*-
"""
First-Order Model Process (FOMP) Module for the BioDYM Engine.

This file contains the specific calculation logic for processes that are
modeled with first-order decay kinetics, such as mineralization.
"""
import numpy as np


def calculate_fomp(mfa_system, fomp_params_config):
    """
    Calculates the outflow from a single First-Order Model Process (FOMP).

    This function models processes like decay or mineralization where the
    outflow rate is dependent on the current stock level and inflow,
    governed by first-order decay constants.

    Args:
        mfa_system (odym.MFAsystem): The MFA system object.
        fomp_params_config (dict): A dictionary containing the configuration
                                   for the single FOMP process to be calculated.
                                   Example: {8: {'outflow_id': ...}}

    Returns:
        odym.MFAsystem: The MFA system object with the calculated FOMP
                        outflow updated.
    """
    time_vector = mfa_system.IndexTable.Classification['Time'].Items
    num_years, num_elements = len(time_vector), len(mfa_system.Elements)

    process_id = list(fomp_params_config.keys())[0]
    params = fomp_params_config[process_id]

    stock_s = mfa_system.StockDict.get(f"S_{process_id}")
    initial_stock_vector = stock_s.Values[0, :].copy()
    outflow_flow_name = params.get('outflow_id')

    f, k1, k2 = params.get('f', 0), params.get('k1', 0), params.get('k2', 0)
    inflows = [flow.Values for flow in mfa_system.FlowDict.values() if flow.P_End == process_id]
    inflow_values = sum(inflows) if inflows else np.zeros((num_years, num_elements))

    new_outflow_values = np.zeros_like(inflow_values, dtype=float)
    current_stock = initial_stock_vector
    for t in range(num_years):
        outflow_t = (inflow_values[t, :] * f) + (current_stock * k1) + (inflow_values[t, :] * k2)
        new_outflow_values[t, :] = outflow_t
        current_stock = current_stock + inflow_values[t, :] - outflow_t

    mfa_system.FlowDict[outflow_flow_name].Values = new_outflow_values
    return mfa_system

