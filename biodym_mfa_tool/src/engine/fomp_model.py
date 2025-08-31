# -*- coding: utf-8 -*-
"""
Enhanced First-Order Model Process (FOMP) Module for the BioDYM Engine.

This file contains the calculation logic for 2-pool FOMP processes that model
soil carbon dynamics with labile and recalcitrant pools, each with separate
decay rates and dual outflow handling.

The model follows the Century Model approach:
- Water content bypasses FOMP and goes directly to environment
- Dry matter enters the two pools (labile and recalcitrant)
- Decay affects entire dry matter, not just carbon
- Outputs are split by composition (carbon vs. non-carbon)
"""

import numpy as np


def calculate_fomp(mfa_system, fomp_params_config, input_flow_composition=None):
    """
    Calculates the outflows from a 2-pool First-Order Model Process (FOMP).

    This function models processes like soil carbon decay where biomass input
    is split into two pools (labile and recalcitrant) with different decay
    rates, producing two separate outflows.

    Args:
        mfa_system (odym.MFAsystem): The MFA system object.
        fomp_params_config (dict): A dictionary containing the configuration
                                   for the FOMP process to be calculated.
        input_flow_composition (dict): Composition of the input flow.

    Returns:
        odym.MFAsystem: The MFA system object with both FOMP outflows updated.
    """
    time_vector = mfa_system.IndexTable.Classification["Time"].Items
    num_years, num_elements = len(time_vector), len(mfa_system.Elements)

    # --- 1. Input Validation ---
    if input_flow_composition is None:
        raise ValueError("❌ FOMP Error: `input_flow_composition` is required but was not provided.")

    required_elements = {'DM', 'CC', 'WC'}
    if not required_elements.issubset(mfa_system.Elements):
        raise ValueError(f"❌ FOMP Error: MFA system is missing one of the required elements: {required_elements - set(mfa_system.Elements)}")

    process_id = list(fomp_params_config.keys())[0]
    params = fomp_params_config[process_id]

    stock_s = mfa_system.StockDict.get(f"S_{process_id}")
    if stock_s is None:
        print(f"⚠️ Warning: No stock found for process {process_id}")
        return mfa_system
    
    initial_stock_vector = stock_s.Values[0, :].copy()
    
    carbon_outflow_id = params.get("outflow_id")
    environmental_outflow_id = params.get("outflow_id_2")
    
    if not carbon_outflow_id or not environmental_outflow_id:
        print(f"⚠️ Warning: Missing outflow IDs for process {process_id}")
        return mfa_system

    labile_fraction = params.get("Inflow_fraction_f (Labile pool)", 0.7)
    recalcitrant_fraction = params.get("Inflow_fraction_f (Recalcitrant pool)", 0.3)
    k1 = params.get("decay_k1", 0.5)
    k2 = params.get("decay_k2", 0.025)
    
    dm_fraction = input_flow_composition.get('DM', 0.86)
    cc_fraction = input_flow_composition.get('CC', 0.4128)
    wc_fraction = input_flow_composition.get('WC', 0.14)
    
    if abs(labile_fraction + recalcitrant_fraction - 1.0) > 1e-6:
        print(f"⚠️ Warning: Pool fractions for process {process_id} don't sum to 1.0. Normalizing.")
        total = labile_fraction + recalcitrant_fraction
        labile_fraction /= total
        recalcitrant_fraction /= total

    inflows = [flow.Values for flow in mfa_system.FlowDict.values() if flow.P_End == process_id]
    inflow_values = sum(inflows) if inflows else np.zeros((num_years, num_elements))

    carbon_outflow_values = np.zeros_like(inflow_values, dtype=float)
    environmental_outflow_values = np.zeros_like(inflow_values, dtype=float)
    
    labile_stock = np.zeros_like(initial_stock_vector)
    recalcitrant_stock = np.zeros_like(initial_stock_vector)
    
    print(f"🌱 FOMP Process {process_id}: 2-Pool Model Initialized")
    print(f"   Elements: {mfa_system.Elements}")
    print(f"   Input composition: DM={dm_fraction:.3f}, CC={cc_fraction:.3f}, WC={wc_fraction:.3f}")
    print(f"   Labile: {labile_fraction*100:.1f}% (k={k1:.3f}), Recalcitrant: {recalcitrant_fraction*100:.1f}% (k={k2:.3f})")

    # Get element indices for correct separation
    try:
        material_idx = mfa_system.Elements.index('material')
        wc_idx = mfa_system.Elements.index('WC')
        dm_idx = mfa_system.Elements.index('DM')
        cc_idx = mfa_system.Elements.index('CC')
    except ValueError as e:
        raise ValueError(f"❌ FOMP Error: MFA system is missing a required element: {e}")

    new_stock_values = np.zeros_like(stock_s.Values)

    for t in range(num_years):
        # --- Corrected Input Splitting ---
        new_input = inflow_values[t, :]

        # 1. Isolate the water part of the input flow into its own vector
        input_water_vector = np.zeros_like(new_input)
        input_water_vector[wc_idx] = new_input[wc_idx]

        # 2. The dry matter part is everything else
        input_dm_vector = new_input - input_water_vector

        # --- Process Dry Matter in FOMP ---
        new_labile_dm = input_dm_vector * labile_fraction
        new_recalcitrant_dm = input_dm_vector * recalcitrant_fraction
        
        labile_decay = labile_stock * k1
        recalcitrant_decay = recalcitrant_stock * k2
        
        labile_stock = labile_stock + new_labile_dm - labile_decay
        recalcitrant_stock = recalcitrant_stock + new_recalcitrant_dm - recalcitrant_decay
        
        # --- Definitive, Corrected Output Calculation ---
        total_dm_decay = labile_decay + recalcitrant_decay

        # 1. Create a physically consistent carbon output flow.
        carbon_output = np.zeros_like(total_dm_decay)
        carbon_mass = total_dm_decay[cc_idx] # Get the scalar mass of carbon decay
        
        # A pure carbon flow is 100% material, 100% DM, and 100% CC
        carbon_output[material_idx] = carbon_mass
        carbon_output[dm_idx] = carbon_mass
        carbon_output[cc_idx] = carbon_mass

        # 2. The environmental output is the INPUT water + the NON-CARBON part of the decay.
        # The non-carbon part is the total decay minus the consistent carbon flow.
        non_carbon_decay = total_dm_decay - carbon_output
        environmental_output = input_water_vector + non_carbon_decay

        carbon_outflow_values[t, :] = carbon_output
        environmental_outflow_values[t, :] = environmental_output
        
        labile_stock = np.maximum(labile_stock, 0)
        recalcitrant_stock = np.maximum(recalcitrant_stock, 0)

        total_stock_t = labile_stock + recalcitrant_stock
        new_stock_values[t, :] = total_stock_t

    if carbon_outflow_id in mfa_system.FlowDict:
        mfa_system.FlowDict[carbon_outflow_id].Values = carbon_outflow_values
    
    if environmental_outflow_id in mfa_system.FlowDict:
        mfa_system.FlowDict[environmental_outflow_id].Values = environmental_outflow_values
    
    stock_s.Values = new_stock_values
    
    print(f"🎯 FOMP Process {process_id} calculation completed")
    print(f"   Total carbon output: {np.sum(carbon_outflow_values):.2f}")
    print(f"   Total environmental output: {np.sum(environmental_outflow_values):.2f}")
    
    return mfa_system


def calculate_fomp_legacy(mfa_system, fomp_params_config):
    """
    Legacy single-outflow FOMP calculation (kept for backward compatibility).
    
    This function maintains the original FOMP behavior for processes that
    don't use the 2-pool model.
    """
    time_vector = mfa_system.IndexTable.Classification["Time"].Items
    num_years, num_elements = len(time_vector), len(mfa_system.Elements)

    process_id = list(fomp_params_config.keys())[0]
    params = fomp_params_config[process_id]

    stock_s = mfa_system.StockDict.get(f"S_{process_id}")
    initial_stock_vector = stock_s.Values[0, :].copy()
    outflow_flow_name = params.get("outflow_id")

    f, k1, k2 = params.get("f", 0), params.get("k1", 0), params.get("k2", 0)
    inflows = [
        flow.Values for flow in mfa_system.FlowDict.values() if flow.P_End == process_id
    ]
    inflow_values = sum(inflows) if inflows else np.zeros((num_years, num_elements))

    new_outflow_values = np.zeros_like(inflow_values, dtype=float)
    current_stock = initial_stock_vector
    for t in range(num_years):
        outflow_t = (
            (inflow_values[t, :] * f)
            + (current_stock * k1)
            + (inflow_values[t, :] * k2)
        )
        new_outflow_values[t, :] = outflow_t
        current_stock = current_stock + inflow_values[t, :] - outflow_t

    if outflow_flow_name in mfa_system.FlowDict:
        mfa_system.FlowDict[outflow_flow_name].Values = new_outflow_values
    else:
        print(f"⚠️ Warning: Outflow {outflow_flow_name} not found in FlowDict")
    
    return mfa_system

