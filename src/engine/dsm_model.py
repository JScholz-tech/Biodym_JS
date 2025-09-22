# -*- coding: utf-8 -*-
"""
Dynamic Stock Model (DSM) Module for the BioDYM Engine.

This file contains the specific calculation logic for processes that are
modeled as dynamic stocks, where outflows are determined by the age
structure of the stock and a lifetime distribution.
"""

import numpy as np
import dynamic_stock_model as dsm
import sys

sys.path.insert(
    0,
    r"C:\Users\Johannes\Nextcloud\BioDYM\bioDYM-CERT-edit-main\framework\ODYM-master_20241127\odym\modules",
)


def calculate_dynamic_stock(mfa_system, dsm_params_config):
    """
    Calculates the outflow from a single dynamic stock process.

    This function correctly handles two separate components of the outflow:
    1. The outflow from new inflows, calculated using the detailed lifetime
       distribution from the 'dynamic_stock_model' library.
    2. The outflow from any non-zero initial stock, calculated using a
       simplified first-order decay based on the average lifetime.

    It also returns a detailed dictionary for creating specialized plots.

    Args:
        mfa_system (odym.MFAsystem): The MFA system object.
        dsm_params_config (dict): A dictionary containing the configuration
                                  for the single DSM process to be calculated.
                                  Example: {6: {'inflow_split': ...}}

    Returns:
        tuple: A tuple containing the modified mfa_system and a dictionary
               with detailed results for plotting for the single process.
    """

    time_vector = np.array(mfa_system.IndexTable.Classification["Time"].Items)
    num_years, num_elements = len(time_vector), len(mfa_system.Elements)
    dsm_details_results = {}

    process_id = list(dsm_params_config.keys())[0]
    params = dsm_params_config[process_id]

    stock_s = mfa_system.StockDict.get(f"S_{process_id}")
    initial_stock_vector = (
        stock_s.Values[0, :].copy() if stock_s is not None else np.zeros(num_elements)
    )
    inflows = [f.Values for f in mfa_system.FlowDict.values() if f.P_End == process_id]
    total_inflow_values = (
        sum(inflows) if inflows else np.zeros((num_years, num_elements))
    )
    outflow_flow_name = next(
        (f.Name for f in mfa_system.FlowDict.values() if f.P_Start == process_id), None
    )
    if not outflow_flow_name:
        print(
            f"WARNING: No outflow defined for DSM process {process_id}. Cannot calculate."
        )
        return mfa_system, {}

    lt_params = params.get("lifetimes", {})
    mean_lifetimes = lt_params.get("Mean", [])

    outflow_from_inflows_material, stock_from_inflows_by_cat = np.zeros(num_years), []
    inflow_split = params.get("inflow_split", [1.0])
    mean_lifetimes = lt_params.get("Mean", [])
    std_devs = lt_params.get("StdDev", [0] * len(mean_lifetimes))

    for i in range(len(inflow_split)):
        inflow_category = total_inflow_values[:, 0] * inflow_split[i]
        print(
            "inflow_category:",
            inflow_category,
            type(inflow_category),
            inflow_category.shape,
        )
        inflow_category = np.array(inflow_category).flatten()
        dsm_model_instance = dsm.DynamicStockModel(
            t=time_vector,
            i=inflow_category,
            lt={
                "Type": lt_params.get("Type"),
                "Mean": [mean_lifetimes[i]],
                "StdDev": [std_devs[i]],
            },
        )
        print(
            "lt:",
            {
                "Type": lt_params.get("Type"),
                "Mean": [mean_lifetimes[i]],
                "StdDev": [std_devs[i]],
            },
        )
        s_c = dsm_model_instance.compute_s_c_inflow_driven()
        o_c = dsm_model_instance.compute_o_c_from_s_c()
        outflow_from_inflows_material += o_c.sum(axis=1) if o_c is not None else 0
        stock_from_inflows_by_cat.append(
            s_c.sum(axis=1) if s_c is not None else np.zeros(len(time_vector))
        )

    avg_lifetime = np.mean(mean_lifetimes) if mean_lifetimes else 0
    decay_rate_k = 1 / avg_lifetime if avg_lifetime > 0 else 0
    outflow_from_initial_stock_ts, decaying_stock_ts = (
        np.zeros_like(total_inflow_values),
        np.zeros_like(total_inflow_values),
    )
    if np.sum(initial_stock_vector) > 0:
        current_decaying_stock = initial_stock_vector.copy()
        for t in range(num_years):
            decaying_stock_ts[t, :] = current_decaying_stock
            outflow_t = current_decaying_stock * decay_rate_k
            outflow_from_initial_stock_ts[t, :] = outflow_t
            current_decaying_stock -= outflow_t

    total_outflow_material = (
        outflow_from_inflows_material + outflow_from_initial_stock_ts[:, 0]
    )
    mfa_system.FlowDict[outflow_flow_name].Values[:, 0] = total_outflow_material
    for elem_idx in range(1, total_inflow_values.shape[1]):
        factor = np.divide(
            total_inflow_values[:, elem_idx],
            total_inflow_values[:, 0],
            out=np.zeros_like(total_inflow_values[:, 0]),
            where=total_inflow_values[:, 0] != 0,
        )
        mfa_system.FlowDict[outflow_flow_name].Values[:, elem_idx] = (
            total_outflow_material * factor
        )

    dsm_details_results[process_id] = {
        "initial_stock_ts": decaying_stock_ts,
        "inflow_stock_ts_by_cat": stock_from_inflows_by_cat,
        "category_names": params.get("category_names", []),
        "mean_lifetimes": mean_lifetimes,
    }
    print("DSM outflow flow name:", outflow_flow_name)
    print("DSM inflow shape:", total_inflow_values.shape)
    print("DSM inflow values:", total_inflow_values)
    print("DSM params:", params)

    return mfa_system, dsm_details_results
