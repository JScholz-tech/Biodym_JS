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

    # Debug: Check stock and inflow data
    print(f"=== DSM DEBUG for Process {process_id} ===")
    
    stock_s = mfa_system.StockDict.get(f"S_{process_id}")
    print(f"Stock object found: {stock_s is not None}")
    if stock_s is not None:
        print(f"Stock shape: {stock_s.Values.shape}")
        print(f"Stock values (first year): {stock_s.Values[0, :]}")
        print(f"Stock sum (first year): {np.sum(stock_s.Values[0, :])}")
    
    initial_stock_vector = (
        stock_s.Values[0, :].copy() if stock_s is not None else np.zeros(num_elements)
    )
    print(f"Initial stock vector: {initial_stock_vector}")
    print(f"Initial stock sum: {np.sum(initial_stock_vector)}")
    
    # Check inflows
    inflow_flows = [f for f in mfa_system.FlowDict.values() if f.P_End == process_id]
    print(f"Number of inflow flows: {len(inflow_flows)}")
    for flow in inflow_flows:
        print(f"  Inflow flow: {flow.Name}, shape: {flow.Values.shape}")
        print(f"  Inflow sum (first year): {np.sum(flow.Values[0, :])}")
        print(f"  Inflow material (first year): {flow.Values[0, 0]}")
    
    inflows = [f.Values for f in mfa_system.FlowDict.values() if f.P_End == process_id]
    total_inflow_values = (
        sum(inflows) if inflows else np.zeros((num_years, num_elements))
    )
    print(f"Total inflow shape: {total_inflow_values.shape}")
    print(f"Total inflow sum (first year): {np.sum(total_inflow_values[0, :])}")
    print(f"Total inflow material (first year): {total_inflow_values[0, 0]}")
    # Find all output flows for this process
    outflow_flows = [f for f in mfa_system.FlowDict.values() if f.P_Start == process_id]
    if not outflow_flows:
        print(
            f"WARNING: No outflow defined for DSM process {process_id}. Cannot calculate."
        )
        return mfa_system, {}

    lt_params = params.get("lifetimes", {})
    # --- 2. Calculate category-specific stock and outflow ---
    outflow_from_inflows_by_cat = []
    stock_from_inflows_by_cat = []
    inflow_split = params.get("inflow_split", [1.0])
    mean_lifetimes = lt_params.get("Mean", [])
    std_devs = lt_params.get("StdDev", [0] * len(mean_lifetimes))

    print(f"DSM Parameters:")
    print(f"  inflow_split: {inflow_split}")
    print(f"  mean_lifetimes: {mean_lifetimes}")
    print(f"  std_devs: {std_devs}")
    print(f"  category_names: {params.get('category_names', [])}")

    for i in range(len(inflow_split)):
        print(f"\n--- Processing Category {i+1} ({params.get('category_names', [f'Category_{i+1}'])[i]}) ---")
        inflow_category = total_inflow_values[:, 0] * inflow_split[i]
        print(f"Inflow category {i+1}: {inflow_category[:5]}... (first 5 years)")
        
        lifetime_type = lt_params.get("Type")
        if isinstance(lifetime_type, list):
            lifetime_type = lifetime_type[i]
        else:
            lifetime_type = lifetime_type

        if isinstance(lifetime_type, str):
            lifetime_type = lifetime_type.capitalize()

        # If StdDev is 0, a normal distribution is undefined. Treat it as a fixed lifetime.
        if std_devs[i] == 0 and lifetime_type == 'Normal':
            print(f"  INFO: StdDev is 0 for category {i+1}. Using 'Fixed' lifetime model instead of 'Normal'.")
            lifetime_type = 'Fixed'
        
        # The dynamic_stock_model library has brittle input handling. It expects
        # an array-like object for lifetime parameters. Passing a numpy array of
        # size 1 satisfies its constructor while allowing the internal stock
        # calculations to work correctly.
        lt_dict = {
            "Type": lifetime_type,
            "Mean": np.array([mean_lifetimes[i]]),
            "StdDev": np.array([std_devs[i]]),
        }

        dsm_model_instance = dsm.DynamicStockModel(t=time_vector, i=inflow_category, lt=lt_dict)
        s_c = dsm_model_instance.compute_s_c_inflow_driven()
        o_c = dsm_model_instance.compute_o_c_from_s_c()

        if s_c is not None:
            stock_sum = s_c.sum(axis=1)
            stock_from_inflows_by_cat.append(stock_sum)
        else:
            stock_from_inflows_by_cat.append(np.zeros(num_years))

        if o_c is not None:
            outflow_sum = o_c.sum(axis=1)
            outflow_from_inflows_by_cat.append(outflow_sum)
        else:
            outflow_from_inflows_by_cat.append(np.zeros(num_years))

    # --- 3. Process initial stock decay ---
    print(f"\n--- Initial Stock Processing ---")
    avg_lifetime = np.mean(mean_lifetimes) if mean_lifetimes else 0
    decay_rate_k = 1 / avg_lifetime if avg_lifetime > 0 else 0
    outflow_from_initial_stock_ts = np.zeros((num_years, num_elements))
    decaying_stock_ts = np.zeros((num_years, num_elements))

    if np.sum(initial_stock_vector) > 0:
        current_decaying_stock = initial_stock_vector.copy()
        for t in range(num_years):
            decaying_stock_ts[t, :] = current_decaying_stock
            outflow_t = current_decaying_stock * decay_rate_k
            outflow_from_initial_stock_ts[t, :] = outflow_t
            current_decaying_stock -= outflow_t
    
    outflow_from_initial_stock_material = outflow_from_initial_stock_ts[:, 0]

    # --- 4. Distribute outflows to respective flows ---
    output_splits = params.get("output_splits", [])
    final_outflows = [np.zeros(num_years) for _ in outflow_flows]

    # Distribute outflow from inflows based on category-specific splits
    for cat_idx, cat_outflow in enumerate(outflow_from_inflows_by_cat):
        if cat_idx < len(output_splits):
            cat_splits = output_splits[cat_idx]
            cat_split_sum = sum(cat_splits)
            # Normalize splits to prevent mass balance errors
            norm_splits = [s / cat_split_sum if cat_split_sum > 0 else 1/len(cat_splits) if len(cat_splits) > 0 else 0 for s in cat_splits]
            for flow_idx, split_frac in enumerate(norm_splits):
                if flow_idx < len(final_outflows):
                    final_outflows[flow_idx] += cat_outflow * split_frac

    # Distribute outflow from initial stock (assuming equal split)
    if np.sum(outflow_from_initial_stock_material) > 0 and len(outflow_flows) > 0:
        equal_split_frac = 1.0 / len(outflow_flows)
        for flow_idx in range(len(final_outflows)):
            final_outflows[flow_idx] += outflow_from_initial_stock_material * equal_split_frac

    # --- 5. Assign final values to MFA system ---
    for flow_idx, outflow_flow in enumerate(outflow_flows):
        total_material_flow = final_outflows[flow_idx]
        mfa_system.FlowDict[outflow_flow.Name].Values[:, 0] = total_material_flow
        # Apply element composition from total inflow
        for elem_idx in range(1, num_elements):
            factor = np.divide(total_inflow_values[:, elem_idx], total_inflow_values[:, 0], out=np.zeros(num_years), where=total_inflow_values[:, 0] != 0)
            mfa_system.FlowDict[outflow_flow.Name].Values[:, elem_idx] = total_material_flow * factor

    # --- 6. Prepare detailed results for plotting ---
    dsm_details_results[process_id] = {
        "initial_stock_ts": decaying_stock_ts,
        "inflow_stock_ts_by_cat": stock_from_inflows_by_cat,
        "category_names": params.get("category_names", []),
        "mean_lifetimes": mean_lifetimes,
    }

    print(f"\n--- Final Results Summary ---")
    total_outflow_from_inflows = np.sum([np.sum(o) for o in outflow_from_inflows_by_cat])
    print(f"Total outflow from inflows: {total_outflow_from_inflows}")
    print(f"Total outflow from initial stock: {np.sum(outflow_from_initial_stock_material)}")
    print(f"Total outflow material: {np.sum([np.sum(f) for f in final_outflows])}")
    total_stock_from_inflows = sum([np.sum(s) for s in stock_from_inflows_by_cat])
    print(f"Total stock accumulated from inflows: {total_stock_from_inflows}")
    print(f"=== END DSM DEBUG for Process {process_id} ===\n")

    return mfa_system, dsm_details_results
