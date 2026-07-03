# -*- coding: utf-8 -*-
"""
Enhanced First-Order Model Process (FOMP) Module for the BioDYM Engine.

This file contains the calculation logic for a two-pool soil carbon decay model,
based on a more precise analytical solution for first-order decay.
"""

import numpy as np

try:
    from .element_utils import get_carbon_element_name, get_element_index
except ImportError:  # flat import with 02_src/engine directly on sys.path
    from element_utils import get_carbon_element_name, get_element_index


def _calculate_fomp_series(
    dm_inflow_series, params, initial_stock_labile, initial_stock_recalcitrant
):
    """Implements the core two-pool, first-order decay model calculation.

    This is a pure function that takes time-series data and parameters as input
    and returns a dictionary of calculated time-series arrays. It uses the
    analytical solution for first-order decay for each time step:
    `decay = (stock + inflow) * (1 - exp(-k))`.

    The model follows the **start-of-period (add-before-decay) convention**:
    inflow at year t is added to the stock before decay is applied, so it begins
    decomposing within the same year. This is consistent with RothC, CENTURY,
    and the UNFCCC AM-Tool-04 landfill FOD model used in the LFG module.

    Carbon (TC) pools are tracked independently from DM pools using the same
    decay constants. This correctly handles time-varying carbon fractions
    (`cc_dm` as a time-series): each year's inflow carries its own CC/DM ratio
    into the pool and retains it through decay, rather than applying the current
    year's ratio to historically-accumulated pool material.

    Parameters
    ----------
    dm_inflow_series : np.ndarray
        Time-series array of total Dry Matter (DM) inflow to the process.
    params : dict
        Dictionary of model parameters, including `f_labile`, `k_labile`,
        `k_recalcitrant`, and `cc_dm`. `cc_dm` may be a scalar or a 1-D
        np.ndarray (one value per simulation year).
    initial_stock_labile : float
        The initial stock of the labile DM pool at the beginning of the simulation.
    initial_stock_recalcitrant : float
        The initial stock of the recalcitrant DM pool.

    Returns
    -------
    dict
        A dictionary of NumPy arrays for the calculated time-series, including
        `stock_labile`, `stock_recalcitrant`, `stock_tc_labile`,
        `stock_tc_recalcitrant`, `outflow_carbon`, and `outflow_environmental`.
    """
    num_years = len(dm_inflow_series)

    # Create result arrays
    stock_labile_series = np.zeros(num_years)
    stock_recalcitrant_series = np.zeros(num_years)
    stock_tc_labile_series = np.zeros(num_years)
    stock_tc_recalcitrant_series = np.zeros(num_years)
    decay_tc_labile_series = np.zeros(num_years)
    decay_tc_recalcitrant_series = np.zeros(num_years)
    outflow_carbon_series = np.zeros(num_years)
    outflow_environmental_series = np.zeros(num_years)

    # Get parameters from dict
    f_labile = params["f_labile"]
    k_labile = params["k_labile"]
    k_recalcitrant = params["k_recalcitrant"]
    cc_dm = params["cc_dm"]  # scalar or np.ndarray

    # Initialize stocks for the loop
    current_stock_labile = initial_stock_labile
    current_stock_recalcitrant = initial_stock_recalcitrant
    current_tc_labile = 0.0
    current_tc_recalcitrant = 0.0

    for t in range(num_years):
        # Extract year-specific cc_dm (handles both scalar and time-series)
        cc_dm_t = cc_dm[t] if isinstance(cc_dm, np.ndarray) else cc_dm

        # a. Add inflow first (start-of-period convention, consistent with RothC/CENTURY
        #    and UNFCCC AM-Tool-04 LFG model): organic matter deposited in year t starts
        #    decomposing within the same year.
        inflow_labile = dm_inflow_series[t] * f_labile
        inflow_recalcitrant = dm_inflow_series[t] * (1 - f_labile)
        pre_decay_labile = current_stock_labile + inflow_labile
        pre_decay_recalcitrant = current_stock_recalcitrant + inflow_recalcitrant

        # TC pools follow the same dynamics as DM pools.
        # Tracking TC separately preserves the vintage carbon fraction of each
        # year's inflow as it moves through the pool, avoiding the approximation
        # of applying the current year's cc_dm to all accumulated pool material.
        tc_inflow_labile = dm_inflow_series[t] * cc_dm_t * f_labile
        tc_inflow_recalcitrant = dm_inflow_series[t] * cc_dm_t * (1 - f_labile)
        pre_decay_tc_labile = current_tc_labile + tc_inflow_labile
        pre_decay_tc_recalcitrant = current_tc_recalcitrant + tc_inflow_recalcitrant

        # b. Calculate Decay for Each Pool using analytical solution
        decay_labile = pre_decay_labile * (1 - np.exp(-k_labile))
        decay_recalcitrant = pre_decay_recalcitrant * (1 - np.exp(-k_recalcitrant))
        tc_decay_labile = pre_decay_tc_labile * (1 - np.exp(-k_labile))
        tc_decay_recalcitrant = pre_decay_tc_recalcitrant * (
            1 - np.exp(-k_recalcitrant)
        )

        # c. Calculate Stocks at End of Year
        end_of_year_labile = pre_decay_labile - decay_labile
        end_of_year_recalcitrant = pre_decay_recalcitrant - decay_recalcitrant
        end_tc_labile = pre_decay_tc_labile - tc_decay_labile
        end_tc_recalcitrant = pre_decay_tc_recalcitrant - tc_decay_recalcitrant

        stock_labile_series[t] = end_of_year_labile
        stock_recalcitrant_series[t] = end_of_year_recalcitrant
        stock_tc_labile_series[t] = end_tc_labile
        stock_tc_recalcitrant_series[t] = end_tc_recalcitrant
        decay_tc_labile_series[t] = tc_decay_labile
        decay_tc_recalcitrant_series[t] = tc_decay_recalcitrant

        # d. Calculate and Store Split Outflows
        # Carbon outflow = total TC that decayed (all organic carbon → all TOC).
        # Environmental outflow = non-carbon fraction of decayed DM
        # (volatilised H, O, N, S etc. that are not CO₂/CH₄-C).
        total_tc_decay = tc_decay_labile + tc_decay_recalcitrant
        total_dm_decay = decay_labile + decay_recalcitrant
        outflow_carbon_series[t] = total_tc_decay
        outflow_environmental_series[t] = total_dm_decay - total_tc_decay

        # Update stocks for the next iteration
        current_stock_labile = end_of_year_labile
        current_stock_recalcitrant = end_of_year_recalcitrant
        current_tc_labile = end_tc_labile
        current_tc_recalcitrant = end_tc_recalcitrant

    results = {
        "stock_labile": stock_labile_series,
        "stock_recalcitrant": stock_recalcitrant_series,
        "stock_tc_labile": stock_tc_labile_series,
        "stock_tc_recalcitrant": stock_tc_recalcitrant_series,
        "decay_tc_labile": decay_tc_labile_series,
        "decay_tc_recalcitrant": decay_tc_recalcitrant_series,
        "outflow_carbon": outflow_carbon_series,
        "outflow_environmental": outflow_environmental_series,
    }
    return results


def calculate_fomp(mfa_system, fomp_params_config, input_flow_composition):
    """Integrates the pure FOMP calculation with the ODYM MFA system.

    This function acts as a wrapper. It extracts the required data (like total
    dry matter inflow) from the `mfa_system` object, calls the pure
    `_calculate_fomp_series` function to get the decay results, and then assigns
    the calculated outflows back to the appropriate flow objects in the system.

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        The MFA system object, which will be modified.
    fomp_params_config : dict
        A dictionary containing the configuration for the FOMP process.
    input_flow_composition : dict
        A dictionary containing the dynamically calculated composition of the
        inflow, including keys like 'DM', 'CC', and 'WC'.

    Returns
    -------
    tuple (odym.MFAsystem, dict)
        The modified MFA system object with FOMP outflows updated, and a dict
        of per-pool time-series arrays with keys: 'stock_labile',
        'stock_recalcitrant', 'stock_tc_labile', 'stock_tc_recalcitrant',
        'outflow_carbon', 'outflow_environmental'.
    """
    time_vector = mfa_system.IndexTable.Classification["Time"].Items
    num_years, num_elements = len(time_vector), len(mfa_system.Elements)

    # --- 1. Extract data and parameters from the MFA System ---
    process_id = list(fomp_params_config.keys())[0]
    fomp_excel_params = fomp_params_config[process_id]

    try:
        material_idx = mfa_system.Elements.index("material")
        dm_idx = mfa_system.Elements.index("DM")
        wc_idx = mfa_system.Elements.index("WC")
    except ValueError as e:
        raise ValueError(
            f"❌ FOMP Error: MFA system is missing a required element: {e}"
        )
    # Accept "TC" (new hierarchy) or "CC" (legacy) as the carbon element
    _tc_name = get_carbon_element_name(mfa_system.Elements)
    if _tc_name is None:
        raise ValueError(
            "❌ FOMP Error: MFA system is missing carbon element (TC or CC)"
        )
    cc_idx = get_element_index(mfa_system.Elements, _tc_name)

    # Get the total Dry Matter (DM) inflow time-series
    inflows = [f.Values for f in mfa_system.FlowDict.values() if f.P_End == process_id]
    total_inflow_values = (
        sum(inflows) if inflows else np.zeros((num_years, num_elements))
    )
    dm_inflow_series = total_inflow_values[:, dm_idx]

    # Compute per-year carbon-to-dry-matter ratio directly from inflow data.
    # Using a time-series (not a time-average) correctly propagates vintage carbon
    # fractions when feedstock composition changes over time — the same motivation
    # as the DSM cohort-matrix weighting fix.
    cc_inflow_series = total_inflow_values[:, cc_idx]
    with np.errstate(divide="ignore", invalid="ignore"):
        cc_dm_series = np.where(
            dm_inflow_series > 0, cc_inflow_series / dm_inflow_series, 0.0
        )

    params_for_calc = {
        "f_labile": fomp_excel_params.get("Inflow_fraction_f (Labile pool)", 0.7),
        "k_labile": fomp_excel_params.get("decay_k1 (Labile pool)", 0.5),
        "k_recalcitrant": fomp_excel_params.get("decay_k2 (Recalcitrant pool)", 0.025),
        "cc_dm": cc_dm_series,
    }

    # LIMITATION: Initial stocks for FOMP are currently set to zero
    # This is appropriate for systems where carbon sequestration starts from time zero
    # (e.g., new agricultural land, fresh compost systems).
    #
    # For systems with existing soil organic carbon or legacy landfills, initial stocks
    # would need to be specified. Future versions could support this via the
    # 2_4_Initial_Stock sheet, similar to DSM processes.
    #
    # Scientific justification: For the case studies in the accompanying paper
    # (wheat straw, wood products), the FOMP models carbon sequestration in fresh
    # applications where initial carbon stocks are negligible or part of the baseline.
    initial_stock_labile = 0.0
    initial_stock_recalcitrant = 0.0

    # --- 2. Call the pure calculation function ---
    fomp_results = _calculate_fomp_series(
        dm_inflow_series,
        params_for_calc,
        initial_stock_labile,
        initial_stock_recalcitrant,
    )

    # --- 3. Assign results back to the MFA System in a physically consistent way ---

    # Normalize outflow IDs: map all absent/null representations → Python None.
    # Excel empty cells arrive as float NaN; users may also type "None" or leave
    # the row out entirely (→ dict.get returns None).
    def _normalize_flow_id(raw):
        if raw is None:
            return None
        if isinstance(raw, float) and np.isnan(raw):
            return None
        if isinstance(raw, str) and raw.strip().lower() in ("none", ""):
            return None
        return raw

    carbon_outflow_id = _normalize_flow_id(fomp_excel_params.get("outflow_id"))
    environmental_outflow_id = _normalize_flow_id(fomp_excel_params.get("outflow_id_2"))

    # Guard: carbon outflow ID is mandatory
    if carbon_outflow_id is None:
        raise ValueError(
            f"FOMP Error (process {process_id}): 'output_carbon_id' is missing or blank "
            f"in the Excel sheet. A carbon outflow flow ID is required."
        )
    if carbon_outflow_id not in mfa_system.FlowDict:
        raise ValueError(
            f"FOMP Error (process {process_id}): Flow '{carbon_outflow_id}' "
            f"(output_carbon_id) not found in the MFA system FlowDict. "
            f"Check that the flow is defined in the Excel flow definition sheet."
        )

    # Create multi-element carbon outflow vector.
    # Flexible output composition: the emitted carbon is propagated UP the
    # element hierarchy using the inflow TC/DM ratio r_TC(t) = cc_dm_series,
    # so the carbon flow carries the dry matter it originated from
    # (DM = TC / r_TC, material = DM, WC = 0) instead of the former
    # pure-carbon convention material = DM = TC = C_mass which bypassed the
    # hierarchy. The DM carried by the carbon flow is capped at the total
    # decayed DM; the environmental flow receives the remainder, so the
    # per-element TOTAL over both flows is unchanged.
    carbon_outflow_values = np.zeros_like(total_inflow_values)
    outflow_carbon_mass = fomp_results["outflow_carbon"]
    outflow_env_mass = fomp_results["outflow_environmental"]
    total_dm_decay = outflow_carbon_mass + outflow_env_mass

    with np.errstate(divide="ignore", invalid="ignore"):
        dm_equivalent = np.where(
            cc_dm_series > 0, outflow_carbon_mass / cc_dm_series, 0.0
        )
    dm_equivalent = np.minimum(dm_equivalent, total_dm_decay)

    carbon_outflow_values[:, material_idx] = dm_equivalent
    carbon_outflow_values[:, dm_idx] = dm_equivalent
    carbon_outflow_values[:, cc_idx] = outflow_carbon_mass

    # Create multi-element environmental outflow vector.
    # Part 1: decayed dry matter NOT carried by the carbon flow
    #         (H, O, N, S volatilisation)
    # Part 2: water from the INITIAL INPUT (water bypass — not retained in the pool)
    environmental_outflow_values = np.zeros_like(total_inflow_values)
    env_dm_mass = total_dm_decay - dm_equivalent
    environmental_outflow_values[:, material_idx] += env_dm_mass
    environmental_outflow_values[:, dm_idx] += env_dm_mass
    input_water_mass = total_inflow_values[:, wc_idx]
    environmental_outflow_values[:, material_idx] += input_water_mass
    environmental_outflow_values[:, wc_idx] += input_water_mass

    # Set TOC sub-element on the carbon outflow.
    # Decomposed organic carbon is entirely from organic oxidation: all emitted TC
    # is TOC (biogenic CO₂). TIC stays at zero — aerobic soil OC decomposition
    # does not release inorganic carbonates to the atmosphere.
    if "TOC" in mfa_system.Elements:
        toc_idx = mfa_system.Elements.index("TOC")
        carbon_outflow_values[:, toc_idx] = outflow_carbon_mass

    # Mode detection: single-flow vs dual-flow output routing.
    # Single-flow: outflow_id_2 absent/None OR same as outflow_id → merge both
    #              output vectors into the single carbon outflow flow.
    # Dual-flow:   both IDs defined and distinct → write each vector separately.
    _env_missing = environmental_outflow_id is None
    _same_id = environmental_outflow_id == carbon_outflow_id
    _single_flow_mode = _env_missing or _same_id

    if _single_flow_mode:
        _reason = (
            "outflow_id_2 is absent/None"
            if _env_missing
            else f"outflow_id_2 == outflow_id ('{carbon_outflow_id}')"
        )
        mfa_system.FlowDict[carbon_outflow_id].Values = (
            carbon_outflow_values + environmental_outflow_values
        )
        print(
            f"   FOMP (process {process_id}): single-flow mode ({_reason}). "
            f"Carbon and environmental outputs merged into '{carbon_outflow_id}'."
        )
    else:
        if environmental_outflow_id not in mfa_system.FlowDict:
            raise ValueError(
                f"FOMP Error (process {process_id}): Flow '{environmental_outflow_id}' "
                f"(output_environmental_id) not found in the MFA system FlowDict. "
                f"Either define this flow or leave output_environmental_id blank to "
                f"use single-flow mode."
            )
        mfa_system.FlowDict[carbon_outflow_id].Values = carbon_outflow_values
        mfa_system.FlowDict[
            environmental_outflow_id
        ].Values = environmental_outflow_values
        print(
            f"   FOMP (process {process_id}): dual-flow mode. "
            f"Carbon → '{carbon_outflow_id}', "
            f"environmental → '{environmental_outflow_id}'."
        )

    # Write FOMP pool stocks to the MFA system StockDict.
    # Without this, accumulated soil carbon is invisible to ODYM: inflow ≠ outflow
    # and Consistency_Check raises a warning every iteration.
    # The pool stock at year t is the end-of-year value from the pool model.
    # TC pool stock uses the independently-tracked TC series (not DM × cc_dm),
    # which correctly reflects the vintage-weighted carbon content of the pool.
    stock_key = f"S_{process_id}"
    if stock_key in mfa_system.StockDict:
        pool_dm_stock = (
            fomp_results["stock_labile"] + fomp_results["stock_recalcitrant"]
        )
        pool_tc_stock = (
            fomp_results["stock_tc_labile"] + fomp_results["stock_tc_recalcitrant"]
        )
        stock_values = np.zeros((num_years, num_elements))
        stock_values[:, material_idx] = pool_dm_stock
        stock_values[:, dm_idx] = pool_dm_stock
        stock_values[:, cc_idx] = pool_tc_stock
        if "TOC" in mfa_system.Elements:
            toc_idx = mfa_system.Elements.index("TOC")
            stock_values[:, toc_idx] = pool_tc_stock

        # Ash_content does not decay — it accumulates permanently in the pool stock.
        # It is excluded from both outflows (it never leaves the FOMP process).
        if "Ash_content" in mfa_system.Elements:
            ash_idx = mfa_system.Elements.index("Ash_content")
            ash_inflow_series = total_inflow_values[:, ash_idx]
            stock_values[:, ash_idx] = np.cumsum(ash_inflow_series)
            # Ash mass is part of DM and material — update totals accordingly
            stock_values[:, dm_idx] += stock_values[:, ash_idx]
            stock_values[:, material_idx] += stock_values[:, ash_idx]

        # TIC (inorganic carbon) is treated as an inert mineral in FOMP — aerobic
        # soil OC decomposition does not mobilise inorganic carbonates. TIC from
        # the inflow accumulates permanently in the stock alongside Ash_content.
        if "TIC" in mfa_system.Elements:
            tic_idx = mfa_system.Elements.index("TIC")
            tic_inflow_series = total_inflow_values[:, tic_idx]
            stock_values[:, tic_idx] = np.cumsum(tic_inflow_series)
            # TIC is part of TC (and DM, material) — update totals accordingly
            stock_values[:, cc_idx] += stock_values[:, tic_idx]
            stock_values[:, dm_idx] += stock_values[:, tic_idx]
            stock_values[:, material_idx] += stock_values[:, tic_idx]

        mfa_system.StockDict[stock_key].Values[:, :] = stock_values

    print(f"   Total carbon output: {np.sum(fomp_results['outflow_carbon']):.2f}")
    print(
        f"   Total environmental output: {np.sum(fomp_results['outflow_environmental']):.2f}"
    )

    # ODYM validation after FOMP calculation
    try:
        mfa_system.Consistency_Check()
        print(f"✅ FOMP validation passed for process {process_id}")
    except Exception as e:
        print(f"⚠️ FOMP validation warning for process {process_id}: {e}")

    return mfa_system, fomp_results
