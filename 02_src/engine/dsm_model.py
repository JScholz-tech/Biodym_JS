# -*- coding: utf-8 -*-
"""
Dynamic Stock Model (DSM) Module for the BioDYM Engine.

This file contains the specific calculation logic for processes that are
modeled as dynamic stocks, where outflows are determined by the age
structure of the stock and a lifetime distribution.
"""

import numpy as np
import dynamic_stock_model as dsm
from .element_utils import recalculate_hierarchical_elements


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


def _calculate_outflow_from_initial_stock_cohort(
    initial_stock_config, params, num_years, num_elements, time_vector
):
    """Calculate outflow from initial stock using age-cohort method (ODYM).

    This function uses ODYM's compute_evolution_initialstock method to properly
    track initial stock cohorts with the same survival function as new inflows.
    This ensures mathematical consistency.

    Parameters
    ----------
    initial_stock_config : dict
        Configuration from initial_stock_engine containing:
        - cohort_age_distribution_type: "uniform" or "exponential"
        - cohort_max_age: maximum age in years
        - cohort_decay_constant: optional decay constant for exponential
        - initial_stock_values: element fractions
        - elements: list of element names
    params : dict
        DSM parameters containing lifetime distributions.
    num_years : int
        Number of time steps.
    num_elements : int
        Number of elements tracked.
    time_vector : np.ndarray
        Time vector for the simulation.

    Returns
    -------
    tuple
        (stock_ts, outflow_ts) - Time series of stock and outflow with all elements
    """
    from odym.modules.dynamic_stock_model import DynamicStockModel
    from .age_cohort_utils import (
        generate_age_cohorts,
        apply_element_composition_to_cohorts,
        validate_age_cohort_parameters,
    )

    # Validate and extract cohort parameters
    cohort_params = validate_age_cohort_parameters(initial_stock_config, "DSM_Cohort")

    # Generate age cohorts for material only
    material_cohorts = generate_age_cohorts(
        total_stock=cohort_params["total_stock"],
        distribution_type=cohort_params["distribution_type"],
        max_age=cohort_params["max_age"],
        decay_constant=cohort_params["decay_constant"],
    )

    # Apply element composition to all cohorts
    initial_stock_cohort_matrix = apply_element_composition_to_cohorts(
        material_cohorts, cohort_params["element_fractions"]
    )

    # Initialize output arrays
    stock_ts = np.zeros((num_years, num_elements))
    outflow_ts = np.zeros((num_years, num_elements))

    # Process each element separately (ODYM handles one element at a time)
    for elem_idx in range(num_elements):
        # Create ODYM DSM for this element
        dsm = DynamicStockModel(t=time_vector, lt=params.get("lifetimes", {}))

        # Initial stock for this element (age cohorts)
        initial_stock_elem = initial_stock_cohort_matrix[:, elem_idx]

        # Compute evolution using ODYM method
        max_age = cohort_params["max_age"]
        s_c = dsm.compute_evolution_initialstock(
            InitialStock=initial_stock_elem, SwitchTime=max_age
        )

        # Compute outflow cohorts
        dsm.compute_o_c_from_s_c()

        # Sum across cohorts to get total stock and outflow
        if hasattr(dsm, "s"):
            stock_ts[:, elem_idx] = dsm.s
        if hasattr(dsm, "o"):
            outflow_ts[:, elem_idx] = dsm.o

    return stock_ts, outflow_ts


def _distribute_and_assign_outflows(
    mfa_system,
    process_id,
    outflow_flows,
    outflow_from_inflows_by_cat,
    outflow_from_initial_stock_ts,
    params,
    total_inflow_values,
    initial_stock_vector,
    flow_tc_map,
):
    """Distributes and assigns all calculated outflows back to the MFA system.

    This function combines the outflows generated from new inflows and from the
    initial stock, splits them according to TCs (transfer coefficients), and updates
    the corresponding flow objects in the main MFA system.

    CRITICAL FIX: Composition preservation - outflows from initial stock maintain
    their original element composition, while outflows from new inflows use the
    composition of those inflows. This prevents "transmutation" of elements.

    NEW: Uses standard TC system instead of DSM-specific output_splits. This enables:
    - Dynamic (time-varying) output splits
    - Unified configuration with other process types
    - Monte Carlo uncertainty sampling of splits

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
        Time series of the outflow from the initial stock (all elements).
    params : dict
        The DSM parameter configuration for the process.
    total_inflow_values : np.ndarray
        A 2D array of total inflow values, used to calculate outflow composition.
    initial_stock_vector : np.ndarray
        1D array of initial stock values by element, used to preserve composition.
    flow_tc_map : dict
        Map from flow names to TC parameter names.
    """
    # Get TCs for each outflow (replaces output_splits)
    # Each outflow flow should have a TC defined in flow_tc_map
    num_years = len(mfa_system.IndexTable.Classification["Time"].Items)

    # Track material flows separately to preserve composition
    final_outflows_from_inflows = [np.zeros(num_years) for _ in outflow_flows]
    final_outflows_from_initial = [np.zeros(num_years) for _ in outflow_flows]

    # Get TC values for each outflow
    tc_values = []
    for flow in outflow_flows:
        tc_ids = flow_tc_map.get(flow.Name, {})
        tc_param_name = tc_ids.get("material")

        if tc_param_name and tc_param_name in mfa_system.ParameterDict:
            tc_value = mfa_system.ParameterDict[tc_param_name].Values
            # Handle both scalar and array TCs
            if isinstance(tc_value, (int, float)):
                tc_value = np.full(num_years, tc_value)
            tc_values.append(tc_value)
        else:
            # No TC defined - equal split among all flows
            print(f"  -> Warning: No TC defined for DSM outflow {flow.Name}, using equal split")
            tc_values.append(np.full(num_years, 1.0 / len(outflow_flows)))

    # Normalize TCs at each time step (handles dynamic TCs that may sum > 1)
    tc_array = np.array(tc_values)  # Shape: (num_flows, num_years)
    tc_sums = tc_array.sum(axis=0)  # Sum across flows for each year

    # Avoid division by zero
    tc_sums = np.where(tc_sums == 0, 1.0, tc_sums)
    normalized_tcs = tc_array / tc_sums  # Normalize each year

    # Distribute outflow from new inflows using normalized TCs
    for cat_idx, cat_outflow in enumerate(outflow_from_inflows_by_cat):
        for flow_idx in range(len(outflow_flows)):
            final_outflows_from_inflows[flow_idx] += cat_outflow * normalized_tcs[flow_idx]

    # Distribute outflow from initial stock using normalized TCs
    outflow_from_initial_stock_material = outflow_from_initial_stock_ts[:, 0]
    if np.sum(outflow_from_initial_stock_material) > 0:
        for flow_idx in range(len(outflow_flows)):
            final_outflows_from_initial[flow_idx] = (
                outflow_from_initial_stock_material * normalized_tcs[flow_idx]
            )

    # Assign final values to MFA system flows
    num_elements = len(mfa_system.Elements)
    elements = mfa_system.Elements

    # Calculate element fractions for initial stock (preserve original composition)
    initial_stock_fractions = np.zeros(num_elements)
    if initial_stock_vector[0] > 0:
        initial_stock_fractions = initial_stock_vector / initial_stock_vector[0]
    else:
        initial_stock_fractions[0] = 1.0  # Material fraction is always 1

    for flow_idx, outflow_flow in enumerate(outflow_flows):
        # Combine material flows
        total_material_flow = (
            final_outflows_from_inflows[flow_idx] + final_outflows_from_initial[flow_idx]
        )
        mfa_system.FlowDict[outflow_flow.Name].Values[:, 0] = total_material_flow

        # Apply element composition separately for each source
        # This prevents "transmutation" - each source maintains its composition
        for elem_idx in range(1, num_elements):
            # Calculate inflow composition with forward-fill
            inflow_factor = np.divide(
                total_inflow_values[:, elem_idx],
                total_inflow_values[:, 0],
                out=np.zeros(num_years),
                where=total_inflow_values[:, 0] != 0,
            )

            # Forward-fill: Use last valid fraction when input is zero
            last_valid_factor = 0.0
            for t in range(num_years):
                if total_inflow_values[t, 0] > 0:
                    last_valid_factor = inflow_factor[t]
                else:
                    inflow_factor[t] = last_valid_factor

            # Apply composition from inflows to inflow-sourced outflows
            outflow_from_inflows_elem = (
                final_outflows_from_inflows[flow_idx] * inflow_factor
            )

            # Apply original composition from initial stock to initial-stock-sourced outflows
            outflow_from_initial_elem = (
                final_outflows_from_initial[flow_idx] * initial_stock_fractions[elem_idx]
            )

            # Combine both sources
            mfa_system.FlowDict[outflow_flow.Name].Values[:, elem_idx] = (
                outflow_from_inflows_elem + outflow_from_initial_elem
            )

        # FIX: Recalculate hierarchical elements based on their parent
        # This ensures CC stays proportional to DM even when both are declining
        element_hierarchy = getattr(mfa_system, "_element_hierarchy", {})
        if element_hierarchy:
            mfa_system.FlowDict[outflow_flow.Name].Values = (
                recalculate_hierarchical_elements(
                    mfa_system.FlowDict[outflow_flow.Name].Values,
                    elements,
                    element_hierarchy,
                    mfa_system,
                )
            )

    print("\n--- Final Results Summary ---")
    total_outflow_from_inflows = np.sum(
        [np.sum(o) for o in outflow_from_inflows_by_cat]
    )
    print(f"Total outflow from inflows: {total_outflow_from_inflows}")
    print(
        f"Total outflow from initial stock: {np.sum(outflow_from_initial_stock_material)}"
    )
    total_material_combined = np.sum(
        [np.sum(final_outflows_from_inflows[i] + final_outflows_from_initial[i])
         for i in range(len(outflow_flows))]
    )
    print(f"Total outflow material (combined): {total_material_combined}")


def calculate_dynamic_stock(mfa_system, dsm_params_config, initial_stock_configs=None, flow_tc_map=None):
    """Calculates stock and outflow for a single Dynamic Stock Model (DSM) process.

    This function orchestrates the DSM calculation for one process. It separates
    the calculation into two main parts: the outflow resulting from new inflows
    and the outflow from the decay of any initial stock. It then assigns the
    combined outflows back to the appropriate flow objects in the MFA system.

    The function supports two modes for initial stock handling:
    - Stock_with_InitialStock_Decay: Simple exponential decay
    - Stock_with_InitialStock_Cohort: ODYM age-cohort method (rigorous)

    DSM outflows are now controlled via the standard TC (Transfer Coefficient) system,
    enabling dynamic (time-varying) splits and unified configuration.

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        The MFA system object, which will be modified in place.
    dsm_params_config : dict
        A dictionary containing the configuration for the single DSM process
        to be calculated. Example: `{6: {'inflow_split': ...}}`
    initial_stock_configs : dict, optional
        Dictionary of initial stock configurations, keyed by process ID.
        Required for Stock_with_InitialStock_Cohort mode.
    flow_tc_map : dict, optional
        Map from flow names to TC parameter names. If None, uses equal splits.

    Returns
    -------
    tuple
        A tuple containing:
        - mfa_system (odym.MFAsystem): The modified MFA system object.
        - dsm_details_results (dict): Detailed results for plotting.
    """
    if flow_tc_map is None:
        flow_tc_map = {}
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

    # Route to appropriate initial stock calculation method
    stock_configuration = params.get("stock_configuration", "Stock")

    if stock_configuration == "Stock_with_InitialStock_Cohort":
        # Use rigorous ODYM age-cohort method
        print(f"  -> Using ODYM age-cohort method for initial stock")

        # Retrieve initial_stock_configs from MFA system or parameter
        if initial_stock_configs is None:
            # Get from MFA system (stored in system_setup._apply_initial_stock)
            initial_stock_configs_resolved = getattr(
                mfa_system, "_process_initial_stock_configs", {}
            )
        else:
            initial_stock_configs_resolved = initial_stock_configs

        if process_id not in initial_stock_configs_resolved:
            raise ValueError(
                f"Process {process_id}: Stock_with_InitialStock_Cohort requires "
                f"initial stock configuration in 2_4_Initial_Stock sheet"
            )

        initial_stock_config = initial_stock_configs_resolved[process_id]
        decaying_stock_ts, outflow_from_initial_stock_ts = (
            _calculate_outflow_from_initial_stock_cohort(
                initial_stock_config, params, num_years, num_elements, time_vector
            )
        )
    else:
        # Use simple exponential decay method (Stock_with_InitialStock_Decay or Stock)
        if stock_configuration == "Stock_with_InitialStock_Decay":
            print(f"  -> Using exponential decay method for initial stock")

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
        initial_stock_vector,
        flow_tc_map,
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
