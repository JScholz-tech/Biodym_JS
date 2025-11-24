# -*- coding: utf-8 -*-
"""
Dynamic Stock Model (DSM) Module for the BioDYM Engine.

This file contains the specific calculation logic for processes that are
modeled as dynamic stocks, where outflows are determined by the age
structure of the stock and a lifetime distribution.
"""

import numpy as np
import dynamic_stock_model as dsm


def _calculate_outflow_from_inflows(total_inflow_values, params, time_vector):
    """Calculate the stock and outflow generated from new inflows for all categories.

    Parameters
    ----------
    total_inflow_values : np.ndarray
        A 2D array of total inflow values over time for all elements.
    params : dict
        The DSM parameter configuration for the specific process.
    time_vector : np.ndarray
        The array of years for the model run.

    Returns
    -------
    tuple
        A tuple containing:
        - stock_from_inflows_by_cat (list): List of stock arrays for each category.
        - outflow_from_inflows_by_cat (list): List of outflow arrays for each category.
    """
    outflow_from_inflows_by_cat = []
    stock_from_inflows_by_cat = []
    num_years = len(time_vector)

    inflow_split = params.get("inflow_split", [1.0])
    lt_params = params.get("lifetimes", {})
    mean_lifetimes = lt_params.get("Mean", [])
    std_devs = lt_params.get("StdDev", [0] * len(mean_lifetimes))

    for i in range(len(inflow_split)):
        print(
            f"\n--- Processing Category {i + 1} ({params.get('category_names', [f'Category_{i + 1}'])[i]}) ---"
        )
        inflow_category = total_inflow_values[:, 0] * inflow_split[i]
        print(f"Inflow category {i + 1}: {inflow_category[:5]}... (first 5 years)")

        lifetime_type = lt_params.get("Type")
        lifetime_type = (
            lifetime_type[i] if isinstance(lifetime_type, list) else lifetime_type
        )
        if isinstance(lifetime_type, str):
            lifetime_type = lifetime_type.capitalize()

        if std_devs[i] == 0 and lifetime_type == "Normal":
            print(
                f"  INFO: StdDev is 0 for category {i + 1}. Using 'Fixed' lifetime model instead of 'Normal'."
            )
            lifetime_type = "Fixed"

        lt_dict = {
            "Type": lifetime_type,
            "Mean": np.array([mean_lifetimes[i]]),
            "StdDev": np.array([std_devs[i]]),
        }

        dsm_model_instance = dsm.DynamicStockModel(
            t=time_vector, i=inflow_category, lt=lt_dict
        )
        s_c = dsm_model_instance.compute_s_c_inflow_driven()
        o_c = dsm_model_instance.compute_o_c_from_s_c()

        stock_from_inflows_by_cat.append(
            s_c.sum(axis=1) if s_c is not None else np.zeros(num_years)
        )
        outflow_from_inflows_by_cat.append(
            o_c.sum(axis=1) if o_c is not None else np.zeros(num_years)
        )

    return stock_from_inflows_by_cat, outflow_from_inflows_by_cat


def _calculate_outflow_from_initial_stock(
    initial_stock_vector, mean_lifetimes, num_years, num_elements
):
    """Calculate the stock decay and outflow generated from the initial stock.

    This uses a simplified first-order decay model based on the average lifetime
    of all categories in the DSM process.

    Parameters
    ----------
    initial_stock_vector : np.ndarray
        An array representing the initial stock for all elements.
    mean_lifetimes : list
        A list of the mean lifetimes for each category.
    num_years : int
        The number of years in the simulation.
    num_elements : int
        The number of elements being tracked.

    Returns
    -------
    tuple
        A tuple containing:
        - decaying_stock_ts (np.ndarray): Time series of the decaying initial stock.
        - outflow_from_initial_stock_ts (np.ndarray): Time series of the outflow from the initial stock.
    """
    print("\n--- Initial Stock Processing ---")
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

    return decaying_stock_ts, outflow_from_initial_stock_ts


def _distribute_and_assign_outflows(
    mfa_system,
    process_id,
    outflow_flows,
    outflow_from_inflows_by_cat,
    outflow_from_initial_stock_ts,
    params,
    total_inflow_values,
):
    """Distributes and assigns all calculated outflows back to the MFA system.

    This function combines the outflows generated from new inflows and from the
    initial stock, splits them according to the defined output splits, and updates
    the corresponding flow objects in the main MFA system.

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        The MFA system object to be modified.
    process_id : int
        The ID of the current DSM process.
    outflow_flows : list of odym.Flow
        The list of outflow flow objects for this process.
    outflow_from_inflows_by_cat : list
        List of outflow arrays for each category from new inflows.
    outflow_from_initial_stock_ts : np.ndarray
        Time series of the outflow from the initial stock.
    params : dict
        The DSM parameter configuration for the process.
    total_inflow_values : np.ndarray
        A 2D array of total inflow values, used to calculate outflow composition.
    """
    output_splits = params.get("output_splits", [])
    final_outflows = [
        np.zeros(len(mfa_system.IndexTable.Classification["Time"].Items))
        for _ in outflow_flows
    ]

    # Distribute outflow from new inflows
    for cat_idx, cat_outflow in enumerate(outflow_from_inflows_by_cat):
        if cat_idx < len(output_splits):
            cat_splits = output_splits[cat_idx]
            cat_split_sum = sum(cat_splits)
            norm_splits = [
                s / cat_split_sum
                if cat_split_sum > 0
                else 1 / len(cat_splits)
                if len(cat_splits) > 0
                else 0
                for s in cat_splits
            ]
            for flow_idx, split_frac in enumerate(norm_splits):
                if flow_idx < len(final_outflows):
                    final_outflows[flow_idx] += cat_outflow * split_frac

    # Distribute outflow from initial stock
    outflow_from_initial_stock_material = outflow_from_initial_stock_ts[:, 0]
    if np.sum(outflow_from_initial_stock_material) > 0 and len(outflow_flows) > 0:
        equal_split_frac = 1.0 / len(outflow_flows)
        for flow_idx in range(len(final_outflows)):
            final_outflows[flow_idx] += (
                outflow_from_initial_stock_material * equal_split_frac
            )

    # Assign final values to MFA system flows
    num_elements = len(mfa_system.Elements)
    num_years = len(mfa_system.IndexTable.Classification["Time"].Items)
    for flow_idx, outflow_flow in enumerate(outflow_flows):
        total_material_flow = final_outflows[flow_idx]
        mfa_system.FlowDict[outflow_flow.Name].Values[:, 0] = total_material_flow
        # Apply element composition from total inflow
        for elem_idx in range(1, num_elements):
            factor = np.divide(
                total_inflow_values[:, elem_idx],
                total_inflow_values[:, 0],
                out=np.zeros(num_years),
                where=total_inflow_values[:, 0] != 0,
            )
            mfa_system.FlowDict[outflow_flow.Name].Values[:, elem_idx] = (
                total_material_flow * factor
            )

    print("\n--- Final Results Summary ---")
    total_outflow_from_inflows = np.sum(
        [np.sum(o) for o in outflow_from_inflows_by_cat]
    )
    print(f"Total outflow from inflows: {total_outflow_from_inflows}")
    print(
        f"Total outflow from initial stock: {np.sum(outflow_from_initial_stock_material)}"
    )
    print(f"Total outflow material: {np.sum([np.sum(f) for f in final_outflows])}")


def calculate_dynamic_stock(mfa_system, dsm_params_config):
    """Calculates stock and outflow for a single Dynamic Stock Model (DSM) process.

    This function orchestrates the DSM calculation for one process. It separates
    the calculation into two main parts: the outflow resulting from new inflows
    and the outflow from the decay of any initial stock. It then assigns the
    combined outflows back to the appropriate flow objects in the MFA system.

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        The MFA system object, which will be modified in place.
    dsm_params_config : dict
        A dictionary containing the configuration for the single DSM process
        to be calculated. Example: `{6: {'inflow_split': ...}}`

    Returns
    -------
    tuple
        A tuple containing:
        - mfa_system (odym.MFAsystem): The modified MFA system object.
        - dsm_details_results (dict): Detailed results for plotting.
    """
    time_vector = np.array(mfa_system.IndexTable.Classification["Time"].Items)
    num_years, num_elements = len(time_vector), len(mfa_system.Elements)

    process_id = list(dsm_params_config.keys())[0]
    params = dsm_params_config[process_id]

    print(f"=== DSM DEBUG for Process {process_id} ===")
    stock_s = mfa_system.StockDict.get(f"S_{process_id}")
    initial_stock_vector = (
        stock_s.Values[0, :].copy() if stock_s is not None else np.zeros(num_elements)
    )

    inflows = [f.Values for f in mfa_system.FlowDict.values() if f.P_End == process_id]
    total_inflow_values = (
        sum(inflows) if inflows else np.zeros((num_years, num_elements))
    )

    outflow_flows = [f for f in mfa_system.FlowDict.values() if f.P_Start == process_id]
    if not outflow_flows:
        print(
            f"WARNING: No outflow defined for DSM process {process_id}. Cannot calculate."
        )
        return mfa_system, {}

    # --- Calculations ---
    stock_from_inflows_by_cat, outflow_from_inflows_by_cat = (
        _calculate_outflow_from_inflows(total_inflow_values, params, time_vector)
    )
    decaying_stock_ts, outflow_from_initial_stock_ts = (
        _calculate_outflow_from_initial_stock(
            initial_stock_vector,
            params.get("lifetimes", {}).get("Mean", []),
            num_years,
            num_elements,
        )
    )

    # --- Assign values and prepare results ---
    _distribute_and_assign_outflows(
        mfa_system,
        process_id,
        outflow_flows,
        outflow_from_inflows_by_cat,
        outflow_from_initial_stock_ts,
        params,
        total_inflow_values,
    )

    total_stock_from_inflows = sum([np.sum(s) for s in stock_from_inflows_by_cat])
    print(f"Total stock accumulated from inflows: {total_stock_from_inflows}")

    # Check for negative stocks in calculated results
    has_negative_stock = False
    for cat_idx, stock_array in enumerate(stock_from_inflows_by_cat):
        negative_indices = np.where(stock_array < 0)[0]
        if len(negative_indices) > 0:
            has_negative_stock = True
            cat_name = params.get("category_names", [f"Category_{cat_idx + 1}"])[
                cat_idx
            ]
            print(
                f"   ⚠️  WARNING: Negative stock detected in Process {process_id}, Category '{cat_name}'"
            )
            print(f"      → {len(negative_indices)} time steps with negative values")
            print(
                f"      → Min value: {stock_array.min():.6f} at year {time_vector[np.argmin(stock_array)]}"
            )
            print(
                f"      → This may indicate issues with lifetime distribution or inflow data"
            )

    # Check decaying initial stock for negative values
    if np.any(decaying_stock_ts < 0):
        negative_indices = np.where(decaying_stock_ts[:, 0] < 0)[0]
        if len(negative_indices) > 0:
            has_negative_stock = True
            print(
                f"   ⚠️  WARNING: Negative decaying initial stock in Process {process_id}"
            )
            print(f"      → {len(negative_indices)} time steps with negative values")
            print(
                f"      → Min value: {decaying_stock_ts[:, 0].min():.6f} at year {time_vector[np.argmin(decaying_stock_ts[:, 0])]}"
            )

    if not has_negative_stock:
        print(f"✅ No negative stocks detected")

    print(f"=== END DSM DEBUG for Process {process_id} ===\n")

    # Phase 1a: Add ODYM validation after DSM calculation
    try:
        mfa_system.Consistency_Check()
        print(f"✅ DSM validation passed for process {process_id}")
    except Exception as e:
        print(f"⚠️ DSM validation warning for process {process_id}: {e}")

    dsm_details_results = {
        process_id: {
            "initial_stock_ts": decaying_stock_ts,
            "inflow_stock_ts_by_cat": stock_from_inflows_by_cat,
            "category_names": params.get("category_names", []),
            "mean_lifetimes": params.get("lifetimes", {}).get("Mean", []),
        }
    }

    return mfa_system, dsm_details_results
