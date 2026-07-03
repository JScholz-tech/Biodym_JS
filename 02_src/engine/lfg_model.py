# -*- coding: utf-8 -*-
"""
Landfill Gas (LFG) Module for the BioDYM Engine.

Implements the First-Order Decay (FOD) methodology for landfill gas production
following UNFCCC CDM AM-Tool-04 and IPCC 2019 Waste Sector guidelines.

Key differences from FOMP:
- N user-defined waste fractions (not hardcoded 2 pools)
- Gas outputs (CH4 + biogenic CO2) rather than mineralization flows
- Ash fraction per waste type (inert, accumulates permanently)
- Leachate output (water consumed as reactant in anaerobic decomposition)
- Site-level correction factors: MCF, DOCf, F_CH4, OX
"""

import numpy as np

try:
    from .element_utils import get_carbon_element_index, get_element_index
except ImportError:  # flat import with 02_src/engine directly on sys.path
    from element_utils import get_carbon_element_index, get_element_index


# ---------------------------------------------------------------------------
# IPCC 2019 default waste fraction parameters (temperate climate)
# for reference and documentation purposes
# ---------------------------------------------------------------------------
IPCC_2019_DEFAULTS = {
    "Food_waste": {"k_j": 0.185, "DOC_j": 0.15, "f_ash_j": 0.05},
    "Garden_waste": {"k_j": 0.100, "DOC_j": 0.20, "f_ash_j": 0.08},
    "Paper_cardboard": {"k_j": 0.040, "DOC_j": 0.40, "f_ash_j": 0.08},
    "Wood_straw": {"k_j": 0.020, "DOC_j": 0.43, "f_ash_j": 0.01},
    "Textile": {"k_j": 0.040, "DOC_j": 0.24, "f_ash_j": 0.05},
}


def _calculate_lfg_series(
    waste_inflow_series,
    wc_inflow_series,
    params,
    initial_stocks=None,
):
    """Implements the N-pool first-order decay model for landfill gas production.

    This is a pure function following the UNFCCC AM-Tool-04 / IPCC FOD methodology.
    Each waste fraction maintains its own organic carbon stock, which decays
    independently at rate k_j. Gas outputs are expressed in Mg C (carbon mass),
    consistent with the FOMP carbon outflow convention in BioDYM.

    Note on water (WC): In anaerobic decomposition H₂O is a reactant (not bypassed).
    The WC inflow is consumed and exits as leachate. This differs from FOMP,
    which treats WC as a passive bypass (appropriate only for aerobic contexts).

    Parameters
    ----------
    waste_inflow_series : np.ndarray [T]
        Total wet waste input per year (Mg wet weight, material element).
    wc_inflow_series : np.ndarray [T]
        Water content inflow per year (Mg). Consumed as reactant; exits as leachate.
    params : dict
        Model parameters. Keys:
        - "fractions": list of dicts, each with
            "name" (str), "k_j" (float), "DOC_j" (float),
            "f_input_j" (float), "f_ash_j" (float)
        - "MCF": float — methane correction factor (0.4–1.0)
        - "DOCf": float — fraction of DOC that decomposes (≈ 0.5)
        - "F_CH4": float — CH4 vol fraction in landfill gas (≈ 0.5)
        - "OX": float — oxidation factor for cover soil (≈ 0.1)
        - "phi": float — UNFCCC model correction factor φ (default 1.0)
    initial_stocks : dict, optional
        {fraction_name: float} initial organic C stocks (Mg C). Defaults to 0.

    Returns
    -------
    dict
        {
          "stocks":           {fraction_name: np.ndarray [T]},  Mg C per fraction
          "ash_stock_total":  np.ndarray [T],  cumulative ash (inert DM), Mg
          "ch4_carbon_total": np.ndarray [T],  C emitted as CH4, Mg C
          "co2_carbon_total": np.ndarray [T],  C emitted as biogenic CO2, Mg C
          "leachate_total":   np.ndarray [T],  water exiting as leachate, Mg
          "organic_c_stock":  np.ndarray [T],  remaining organic C stock, Mg C
        }

    Note: the organic carbon stock (Mg C) and the ash stock (Mg DM) are
    returned separately — they carry different units and must not be summed
    (the former "stable_stock" key did exactly that and was removed).
    """
    T = len(waste_inflow_series)
    fractions = params.get("fractions", [])
    MCF = float(params.get("MCF", 0.8))
    DOCf = float(params.get("DOCf", 0.5))
    F_CH4 = float(params.get("F_CH4", 0.5))
    OX = float(params.get("OX", 0.1))
    # φ: UNFCCC model correction factor (default 1.0 = no correction).
    # Accounts for model uncertainty in the FOD methodology.
    phi = float(params.get("phi", 1.0))

    if initial_stocks is None:
        initial_stocks = {}

    # Per-fraction time-series arrays
    stocks = {f["name"]: np.zeros(T) for f in fractions}

    # Aggregated time-series arrays
    ash_stock_total = np.zeros(T)
    ch4_carbon_total = np.zeros(T)
    co2_carbon_total = np.zeros(T)

    # Initialize running state
    current_stocks = {
        f["name"]: float(initial_stocks.get(f["name"], 0.0)) for f in fractions
    }
    cumulative_ash = 0.0

    for t in range(T):
        W = float(waste_inflow_series[t])

        for frac in fractions:
            name = frac["name"]
            k_j = float(frac.get("k_j", 0.0))
            DOC_j = float(frac.get("DOC_j", 0.0))
            f_input_j = float(frac.get("f_input_j", 0.0))
            f_ash_j = float(frac.get("f_ash_j", 0.0))

            # a. Active degradable carbon entering this fraction's stock
            active_C_inflow = W * f_input_j * DOC_j * DOCf

            # b. Ash inflow — inert, accumulates permanently
            cumulative_ash += W * f_input_j * f_ash_j

            # c. Add inflow to stock first (start-of-period convention):
            #    waste deposited in year t starts decaying within the same year.
            #    This matches the UNFCCC/IPCC FOD formula which gives non-zero
            #    gas in the first year of operation (year 0 ≠ 0).
            pre_decay_stock = current_stocks[name] + active_C_inflow

            # d. First-order decay from the updated stock (analytical solution)
            decay = pre_decay_stock * (1.0 - np.exp(-k_j))

            # e. Update organic C stock
            new_stock = pre_decay_stock - decay  # = pre_decay_stock * exp(-k_j)
            stocks[name][t] = new_stock
            current_stocks[name] = new_stock

            # e. Carbon in gas outputs (Mg C, IPCC FOD equation)
            #    MCF, OX, and φ (UNFCCC model correction) apply to the methane
            #    pathway only — the CO2 share of decayed carbon is emitted
            #    directly and is not corrected. Consequently
            #    CH4_C + CO2_C <= decay_C whenever MCF·(1-OX)·φ <= 1.
            ch4_carbon_total[t] += decay * F_CH4 * MCF * (1.0 - OX) * phi
            co2_carbon_total[t] += decay * (1.0 - F_CH4)

        ash_stock_total[t] = cumulative_ash

    # Leachate = WC inflow (water consumed in anaerobic decomposition exits as leachate)
    leachate_total = wc_inflow_series.copy()

    # Organic carbon stock (Mg C) — kept separate from the ash stock (Mg DM);
    # the two quantities have different units and must not be summed.
    organic_c_stock = (
        sum(stocks[f["name"]] for f in fractions)
        if fractions
        else np.zeros(T)
    )

    return {
        "stocks": stocks,
        "ash_stock_total": ash_stock_total,
        "ch4_carbon_total": ch4_carbon_total,
        "co2_carbon_total": co2_carbon_total,
        "leachate_total": leachate_total,
        "organic_c_stock": organic_c_stock,
    }


def calculate_lfg(mfa_system, lfg_params_config):
    """Integrates the LFG calculation with the ODYM MFA system.

    Reads waste inflows from the MFA system, calls ``_calculate_lfg_series``
    for each LFG process, and writes CH4, CO2, and leachate flows back to
    the FlowDict.

    Gas outputs follow the FOMP carbon-outflow convention: material = DM = CC
    = C_mass (Mg C). This keeps BioDYM element mass balances consistent.
    To convert to actual gas mass: CH4_mass = C_in_CH4 × (16/12),
    CO2_mass = C_in_CO2 × (44/12).

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        The MFA system object, modified in place.
    lfg_params_config : dict
        {process_id: params_dict} for a single LFG process.
        Produced by ``data_loader.load_lfg_parameters()``.

    Returns
    -------
    odym.MFAsystem
        The modified MFA system with LFG output flows updated.
    """
    process_id = list(lfg_params_config.keys())[0]
    lfg_excel_params = lfg_params_config[process_id]

    num_years = len(mfa_system.IndexTable.Classification["Time"].Items)
    num_elements = len(mfa_system.Elements)

    # --- Element index lookup ---
    try:
        material_idx = mfa_system.Elements.index("material")
    except ValueError as e:
        raise ValueError(f"❌ LFG Error: MFA system missing required element: {e}")

    dm_idx = get_element_index(mfa_system.Elements, "DM")
    wc_idx = get_element_index(mfa_system.Elements, "WC")
    # Accept "TC" (new hierarchy) or "CC" (legacy) as the total-carbon element
    tc_idx = get_carbon_element_index(mfa_system.Elements)
    toc_idx = get_element_index(mfa_system.Elements, "TOC")

    # --- Read total inflows to this process ---
    inflows = [f.Values for f in mfa_system.FlowDict.values() if f.P_End == process_id]
    total_inflow_values = (
        sum(inflows) if inflows else np.zeros((num_years, num_elements))
    )

    waste_inflow_series = total_inflow_values[:, material_idx]
    wc_inflow_series = (
        total_inflow_values[:, wc_idx] if wc_idx is not None else np.zeros(num_years)
    )

    # --- Run pure calculation ---
    results = _calculate_lfg_series(
        waste_inflow_series, wc_inflow_series, lfg_excel_params
    )

    # --- Assign outputs back to FlowDict ---
    ch4_id = lfg_excel_params.get("outflow_ch4_id")
    co2_id = lfg_excel_params.get("outflow_co2_id")
    leachate_id = lfg_excel_params.get("outflow_leachate_id")

    ch4_values = np.zeros_like(total_inflow_values)
    co2_values = np.zeros_like(total_inflow_values)
    leachate_values = np.zeros_like(total_inflow_values)

    # CH4: material = DM = TC = TOC = C_in_CH4  (Mg C)
    # Carbon exits as gas — set on all applicable carbon hierarchy elements
    ch4_values[:, material_idx] = results["ch4_carbon_total"]
    if dm_idx is not None:
        ch4_values[:, dm_idx] = results["ch4_carbon_total"]
    if tc_idx is not None:
        ch4_values[:, tc_idx] = results["ch4_carbon_total"]
    if toc_idx is not None:
        ch4_values[:, toc_idx] = results["ch4_carbon_total"]

    # CO2: material = DM = TC = TOC = C_in_CO2  (Mg C biogenic)
    co2_values[:, material_idx] = results["co2_carbon_total"]
    if dm_idx is not None:
        co2_values[:, dm_idx] = results["co2_carbon_total"]
    if tc_idx is not None:
        co2_values[:, tc_idx] = results["co2_carbon_total"]
    if toc_idx is not None:
        co2_values[:, toc_idx] = results["co2_carbon_total"]

    # Leachate: material = WC = water  (DM = 0, CC = 0)
    leachate_values[:, material_idx] = results["leachate_total"]
    if wc_idx is not None:
        leachate_values[:, wc_idx] = results["leachate_total"]

    if ch4_id and ch4_id in mfa_system.FlowDict:
        mfa_system.FlowDict[ch4_id].Values = ch4_values
    if co2_id and co2_id in mfa_system.FlowDict:
        mfa_system.FlowDict[co2_id].Values = co2_values
    if leachate_id and leachate_id in mfa_system.FlowDict:
        mfa_system.FlowDict[leachate_id].Values = leachate_values

    print(
        f"   Total CH4 carbon output:   {np.sum(results['ch4_carbon_total']):.2f} Mg C"
    )
    print(
        f"   Total CO2 carbon output:   {np.sum(results['co2_carbon_total']):.2f} Mg C"
    )
    print(f"   Total leachate output:     {np.sum(results['leachate_total']):.2f} Mg")
    if len(results["organic_c_stock"]) > 0:
        print(
            f"   Final organic C stock:     {results['organic_c_stock'][-1]:.2f} Mg C"
        )
        print(
            f"   Final ash stock:           {results['ash_stock_total'][-1]:.2f} Mg"
        )

    try:
        mfa_system.Consistency_Check()
        print(f"✅ LFG validation passed for process {process_id}")
    except Exception as e:
        print(f"⚠️ LFG validation warning for process {process_id}: {e}")

    return mfa_system
