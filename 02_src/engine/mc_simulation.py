# -*- coding: utf-8 -%-
"""
Monte Carlo Simulation Engine.

This module provides functions for running Monte Carlo simulations based on
parameters defined in an Excel file.
"""

import pandas as pd
import numpy as np
import copy

from . import solver
import data_loader
from utils import sample_parameters


def validate_mc_parameters(mc_params_df, mfa_system):
    """Validates Monte Carlo parameters to ensure mass balance and prevent conflicts.

    Parameters
    ----------
    mc_params_df : pd.DataFrame
        DataFrame of Monte Carlo parameters loaded from Excel.
    mfa_system : odym.MFAsystem
        The MFA system to validate against.

    Returns
    -------
    tuple
        A tuple containing:
        - validated_params_df (pd.DataFrame): The validated parameters DataFrame.
        - warnings (list): A list of warning strings for any issues found.
    """
    warnings = []
    validated_params = mc_params_df.copy()

    # Check for dynamic TC conflicts
    dynamic_tc_processes = set()
    for flow in mfa_system.FlowDict.values():
        if hasattr(flow, "TC") and isinstance(flow.TC, np.ndarray) and len(flow.TC) > 1:
            process_id = flow.P_Start
            dynamic_tc_processes.add(process_id)

    # Check for TC mass balance issues
    tc_params = validated_params[
        validated_params["Parameter_Name"].str.startswith("TC_", na=False)
    ]

    for _, row in tc_params.iterrows():
        tc_name = row["Parameter_Name"]
        # Extract process ID from TC name (e.g., TC_05_06 -> process 5)
        try:
            process_id = int(tc_name.split("_")[1])

            # Check if this process has dynamic TCs
            if process_id in dynamic_tc_processes:
                warnings.append(
                    f"⚠️ WARNING: {tc_name} conflicts with dynamic TCs in process {process_id}"
                )

            # Check if this process has multiple outputs
            process_flows = [
                f for f in mfa_system.FlowDict.values() if f.P_Start == process_id
            ]
            if len(process_flows) > 1:
                # Check if all TCs for this process are defined in MC
                process_tcs = [
                    p
                    for p in tc_params["Parameter_Name"]
                    if p.startswith(f"TC_{process_id}_")
                ]
                if len(process_tcs) < len(process_flows):
                    missing_tcs = [
                        f.Name for f in process_flows if f.Name not in process_tcs
                    ]
                    warnings.append(
                        f"⚠️ WARNING: Process {process_id} has {len(process_flows)} outputs but only {len(process_tcs)} TCs in MC. Missing: {missing_tcs}"
                    )

        except (ValueError, IndexError):
            warnings.append(f"⚠️ WARNING: Could not parse process ID from {tc_name}")

    return validated_params, warnings


def apply_dsm_parameter_updates(dsm_params, sampled_params):
    """Applies Monte Carlo sampled parameter values to DSM processes.

    Parameters
    ----------
    dsm_params : dict
        The original DSM parameters dictionary, keyed by process ID.
    sampled_params : dict
        A dictionary of parameter values sampled for a single MC iteration.

    Returns
    -------
    dict
        An updated copy of the DSM parameters dictionary with sampled values applied.
    """
    updated_dsm_params = copy.deepcopy(dsm_params)

    for param_name, sampled_value in sampled_params.items():
        # Check if this is a DSM parameter (contains _DSM_)
        if "_DSM_" not in param_name:
            continue

        try:
            # Extract process ID from parameter name (e.g., "P08_DSM_Lifetime_Mean_Cat_1" -> 8)
            if not param_name.startswith("P"):
                continue

            process_id = int(param_name.split("_")[0][1:])  # Extract ## from P##

            if process_id not in updated_dsm_params:
                print(
                    f"⚠️ WARNING: Process {process_id} not found in DSM parameters for {param_name}"
                )
                continue

            # Remove P##_ prefix and [%] if present
            param_name_clean = "_".join(param_name.split("_")[1:])
            param_name_clean = param_name_clean.replace("_[%]", "").replace("[%]", "")

            # Parse DSM parameter name (e.g., "DSM_Lifetime_Mean_Cat_1")
            if "_Cat_" not in param_name_clean:
                print(
                    f"⚠️ WARNING: DSM parameter '{param_name}' does not follow expected naming convention (P##_DSM_..._Cat_#)"
                )
                continue

            parts = param_name_clean.split("_Cat_")
            param_base = parts[0]  # e.g., "DSM_Lifetime_Mean"
            category_idx = int(parts[1]) - 1  # Convert to 0-based index

            # Map parameter to DSM structure and apply sampled value
            if param_base == "DSM_Lifetime_Mean":
                if category_idx < len(updated_dsm_params[process_id]["lifetimes"]["Mean"]):
                    old_value = updated_dsm_params[process_id]["lifetimes"]["Mean"][
                        category_idx
                    ]
                    updated_dsm_params[process_id]["lifetimes"]["Mean"][
                        category_idx
                    ] = sampled_value
                    print(
                        f"   Applied MC sample: {param_name} = {sampled_value:.4f} (was {old_value:.4f})"
                    )
            elif param_base == "DSM_Lifetime_StdDev":
                if category_idx < len(updated_dsm_params[process_id]["lifetimes"]["StdDev"]):
                    old_value = updated_dsm_params[process_id]["lifetimes"]["StdDev"][
                        category_idx
                    ]
                    updated_dsm_params[process_id]["lifetimes"]["StdDev"][
                        category_idx
                    ] = sampled_value
                    print(
                        f"   Applied MC sample: {param_name} = {sampled_value:.4f} (was {old_value:.4f})"
                    )
            elif param_base == "DSM_Inflow_Split":
                if category_idx < len(updated_dsm_params[process_id]["inflow_split"]):
                    old_value = updated_dsm_params[process_id]["inflow_split"][
                        category_idx
                    ]
                    updated_dsm_params[process_id]["inflow_split"][
                        category_idx
                    ] = sampled_value
                    print(
                        f"   Applied MC sample: {param_name} = {sampled_value:.4f} (was {old_value:.4f})"
                    )

                    # Note: Inflow splits should sum to 1.0 - normalization may be needed
                    # This could be added as a post-processing step if required

            elif param_base.startswith("DSM_Output_") and param_base.endswith("_Split"):
                # Extract output number (e.g., "DSM_Output_1_Split_Cat_2" -> output 0, cat 1)
                output_num = int(param_base.split("_")[2]) - 1
                if category_idx < len(updated_dsm_params[process_id]["output_splits"]):
                    if output_num < len(
                        updated_dsm_params[process_id]["output_splits"][category_idx]
                    ):
                        old_value = updated_dsm_params[process_id]["output_splits"][
                            category_idx
                        ][output_num]
                        updated_dsm_params[process_id]["output_splits"][category_idx][
                            output_num
                        ] = sampled_value
                        print(
                            f"   Applied MC sample: {param_name} = {sampled_value:.4f} (was {old_value:.4f})"
                        )

        except (ValueError, IndexError) as e:
            print(f"⚠️ WARNING: Could not parse DSM parameter name: {param_name} - {e}")
            continue

    return updated_dsm_params


def apply_fomp_parameter_updates(fomp_params, sampled_params):
    """Applies Monte Carlo sampled parameter values to FOMP processes.

    Parameters
    ----------
    fomp_params : dict
        The original FOMP parameters dictionary, keyed by process ID.
    sampled_params : dict
        A dictionary of parameter values sampled for a single MC iteration.

    Returns
    -------
    dict
        An updated copy of the FOMP parameters dictionary with sampled values applied.
    """
    updated_fomp_params = copy.deepcopy(fomp_params)

    for param_name, sampled_value in sampled_params.items():
        # Check if this is a FOMP parameter (starts with P and contains process info)
        if param_name.startswith("P") and "_decay_" in param_name:
            try:
                # Extract process ID from parameter name (e.g., "P08_decay_k1 (Labile pool)" -> 8)
                process_id = int(param_name[1:].split("_")[0])

                # Extract the base parameter name (e.g., "decay_k1 (Labile pool)")
                base_param_name = param_name.split("_", 1)[1]  # Remove "P08_" prefix

                # Apply the sampled value to the correct process and parameter
                if process_id in updated_fomp_params:
                    updated_fomp_params[process_id][base_param_name] = sampled_value
                    print(
                        f"   Applied MC sample: {param_name} = {sampled_value:.4f} to Process {process_id}"
                    )
                else:
                    print(
                        f"⚠️ WARNING: Process {process_id} not found in FOMP parameters for {param_name}"
                    )

            except (ValueError, IndexError) as e:
                print(
                    f"⚠️ WARNING: Could not parse FOMP parameter name: {param_name} - {e}"
                )
                continue

    return updated_fomp_params


def normalize_tcs_for_process(mfa_system, process_id, varied_tc_name, varied_tc_value):
    """Ensures all transfer coefficients (TCs) for a process sum to 1.0.

    When a single TC for a multi-output process is varied in a Monte Carlo
    simulation, the other TCs for that process must be adjusted to maintain
    a mass balance (i.e., they must all sum to 1.0). This function
    normalizes the TCs to enforce this constraint.

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        The MFA system object.
    process_id : int
        The ID of the process whose TCs need to be normalized.
    varied_tc_name : str
        The name of the TC that was just varied by the MC sampler.
    varied_tc_value : float
        The new value for the varied TC.

    Returns
    -------
    dict
        A dictionary of all TC names for the process and their new, normalized values.
    """
    # Get all flows for this process
    process_flows = [f for f in mfa_system.FlowDict.values() if f.P_Start == process_id]

    if len(process_flows) <= 1:
        # Single output process - no normalization needed
        return {varied_tc_name: varied_tc_value}

    # Get current TC values
    current_tcs = {}
    for flow in process_flows:
        if hasattr(flow, "TC"):
            if isinstance(flow.TC, np.ndarray):
                current_tcs[flow.Name] = flow.TC[0] if len(flow.TC) > 0 else 0.0
            else:
                current_tcs[flow.Name] = float(flow.TC)
        else:
            current_tcs[flow.Name] = 0.0

    # Update the varied TC
    current_tcs[varied_tc_name] = varied_tc_value

    # Calculate normalization factor
    total_tc = sum(current_tcs.values())
    if total_tc > 0:
        normalization_factor = 1.0 / total_tc

        # Apply normalization to all TCs
        normalized_tcs = {}
        for flow in process_flows:
            normalized_tcs[flow.Name] = current_tcs[flow.Name] * normalization_factor
            # Update the flow's TC value
            flow.TC = np.array([normalized_tcs[flow.Name]])

        return normalized_tcs
    else:
        # If total is 0, distribute equally
        equal_tc = 1.0 / len(process_flows)
        normalized_tcs = {}
        for flow in process_flows:
            normalized_tcs[flow.Name] = equal_tc
            flow.TC = np.array([equal_tc])

        return normalized_tcs


def _run_single_mc_iteration(
    iteration_num,
    mfa_system_setup,
    uncertainty_params,
    dsm_params,
    fomp_params,
    config,
    flow_tc_map,
    process_logic_map,
    tc_info_map,
):
    """Runs a single iteration of the Monte Carlo simulation.

    This function samples all stochastic parameters, applies them to the system,
    runs the solver, and collects the results for this single iteration.

    Parameters
    ----------
    iteration_num : int
        The current iteration number (e.g., 1, 2, 3...).
    mfa_system_setup : odym.MFAsystem
        A clean, configured MFA system to use as a base.
    uncertainty_params : dict
        The dictionary of uncertainty definitions.
    dsm_params : dict
        Configuration dictionary for DSM processes.
    fomp_params : dict
        Configuration dictionary for FOMP processes.
    config : object
        The main configuration object.
    flow_tc_map : dict
        A map from Flow_IDs to their TC_IDs.
    process_logic_map : dict
        A map from Process_IDs to their logic.
    tc_info_map : dict
        A map containing information about TC relationships.

    Returns
    -------
    dict
        A dictionary containing all the results for this single iteration.
    """
    # --- 3a. Sample parameters ---
    sampled_params = sample_parameters(uncertainty_params)
    tc_updates = sampled_params.copy()

    # --- 3b. Apply DSM parameter updates ---
    updated_dsm_params = apply_dsm_parameter_updates(dsm_params, sampled_params)

    # --- 3c. Apply FOMP parameter updates ---
    updated_fomp_params = apply_fomp_parameter_updates(fomp_params, sampled_params)

    # --- 3c. Propagate Splitter Uncertainty ---
    for param_name, sample_value in sampled_params.items():
        if param_name in tc_info_map:
            info = tc_info_map[param_name]
            process_id = info["process_id"]
            logic = process_logic_map.get(process_id)

            if logic == "Splitter":
                # For a splitter, apply the sampled value to all sibling TCs
                for sibling_tc in info["sibling_tcs"]:
                    tc_updates[sibling_tc] = sample_value

    # --- 3d. Run Solver ---
    mfa_system_run, _ = solver.run_mfa_calculation(
        mfa_system_setup,
        updated_dsm_params,  # Use updated DSM parameters from MC sampling
        updated_fomp_params,  # Use updated FOMP parameters
        config,
        flow_tc_map=flow_tc_map,
        process_logic_map=process_logic_map,
        tc_updates=tc_updates,
    )

    # --- 3e. Collect Results ---
    iteration_results = {"iteration": iteration_num}
    for param, value in tc_updates.items():
        iteration_results[f"{param}_sample"] = value

    for stock in mfa_system_run.StockDict.values():
        for i_elem, element_name in enumerate(mfa_system_run.Elements):
            iteration_results[f"{stock.Name}_{element_name}"] = stock.Values[-1, i_elem]
            iteration_results[f"{stock.Name}_{element_name}_timeseries"] = stock.Values[
                :, i_elem
            ].tolist()

    return iteration_results


def run_mc_simulation(
    mfa_system_setup,
    input_data,
    dsm_params,
    fomp_params,
    config,
    process_logic_map,
    flow_tc_map,
):
    """Runs a Monte Carlo simulation by repeatedly sampling parameters.

    This function orchestrates the Monte Carlo simulation. It sets up the
    configuration, builds lookup maps, and then calls a helper function
    in a loop to run each iteration.

    Parameters
    ----------
    mfa_system_setup : odym.MFAsystem
        A fully configured but unsolved MFA system.
    input_data : dict
        The complete dictionary of data from the Excel file.
    dsm_params : dict
        Configuration dictionary for DSM processes.
    fomp_params : dict
        Configuration dictionary for FOMP processes.
    config : object
        The configuration object with simulation settings.
    process_logic_map : dict
        A map from process ID to its logic ('Splitter'/'Transformer').
    flow_tc_map : dict
        A map from Flow_IDs to their TC_IDs.

    Returns
    -------
    pd.DataFrame or None
        A DataFrame containing the results of all Monte Carlo iterations, or
        None if no uncertainty parameters are defined.
    """
    # --- 1. Configuration ---
    n_iterations = getattr(config, "MC_ITERATIONS", 100)
    uncertainty_params = data_loader.load_uncertainty_definitions(input_data)

    if not uncertainty_params:
        print("\n[MC] No uncertainty parameters defined. Skipping simulation.")
        return None

    print(f"\n[MC] Running Monte Carlo simulation with {n_iterations} iterations...")

    # --- 2. Build maps for efficient lookup ---
    tc_info_map = {}
    static_tc_defs = input_data.get("2_2_static_TCs")
    if static_tc_defs is not None:
        for _, row in static_tc_defs.iterrows():
            process_id = row.get("Process_ID")
            if pd.notna(process_id):
                all_tcs = [
                    row.get(f"TC_{elem}_ID")
                    for elem in mfa_system_setup.Elements
                    if f"TC_{elem}_ID" in row and pd.notna(row.get(f"TC_{elem}_ID"))
                ]
                for tc_name in all_tcs:
                    tc_info_map[tc_name] = {
                        "process_id": int(process_id),
                        "sibling_tcs": all_tcs,
                    }

    # --- 3. Main Simulation Loop ---
    results_list = []
    print(f"[MC] Using {len(uncertainty_params)} validated parameters...")

    for i in range(n_iterations):
        if (i + 1) % 10 == 0:
            print(f"  ... iteration {i + 1}/{n_iterations}")

        iteration_results = _run_single_mc_iteration(
            i + 1,
            mfa_system_setup,
            uncertainty_params,
            dsm_params,  # Pass DSM parameters for MC sampling
            fomp_params,
            config,
            flow_tc_map,
            process_logic_map,
            tc_info_map,
        )
        results_list.append(iteration_results)

    print("[MC] Simulation finished.")
    return pd.DataFrame(results_list)
