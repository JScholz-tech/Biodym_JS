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

    # Extract process IDs from all TC params and check once per process
    checked_processes = set()
    for _, row in tc_params.iterrows():
        tc_name = row["Parameter_Name"]
        # Extract process ID from TC name
        # Supports both formats: TC_05_06 -> process 5, TC_E2_11_00 -> process 11
        try:
            parts = tc_name.split("_")
            if parts[1].startswith("E") and len(parts) >= 4:
                # Element-specific format: TC_E2_11_00
                process_id = int(parts[2])
            else:
                # Standard format: TC_05_06
                process_id = int(parts[1])

            # Check if this process has dynamic TCs
            if process_id in dynamic_tc_processes:
                warnings.append(
                    f"⚠️ WARNING: {tc_name} conflicts with dynamic TCs in process {process_id}"
                )

            # Check multi-output processes only once per process_id
            if process_id not in checked_processes:
                checked_processes.add(process_id)
                process_flows = [
                    f
                    for f in mfa_system.FlowDict.values()
                    if f.P_Start == process_id
                ]
                if len(process_flows) > 1:
                    # Count TCs for this process (both standard and element-specific formats)
                    process_tcs = set()
                    for p in tc_params["Parameter_Name"]:
                        p_parts = p.split("_")
                        try:
                            if p_parts[1].startswith("E") and len(p_parts) >= 4:
                                if int(p_parts[2]) == process_id:
                                    # Element-specific: extract destination to identify unique flows
                                    process_tcs.add(f"F_{process_id}_{p_parts[3]}")
                            elif int(p_parts[1]) == process_id:
                                process_tcs.add(f"F_{p_parts[1]}_{p_parts[2]}")
                        except (ValueError, IndexError):
                            pass

                    flow_names = {f.Name for f in process_flows}
                    if process_tcs and not flow_names.issubset(process_tcs):
                        missing = flow_names - process_tcs
                        if missing:
                            warnings.append(
                                f"⚠️ WARNING: Process {process_id} has {len(process_flows)} outputs "
                                f"but MC only covers flows {process_tcs}. Missing: {sorted(missing)}"
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

    # Track which splits were modified so we can normalize them afterward
    modified_inflow_splits = set()
    modified_output_splits = set()  # (process_id, category_idx)

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
                    updated_dsm_params[process_id]["lifetimes"]["Mean"][
                        category_idx
                    ] = sampled_value
            elif param_base == "DSM_Lifetime_StdDev":
                if category_idx < len(updated_dsm_params[process_id]["lifetimes"]["StdDev"]):
                    updated_dsm_params[process_id]["lifetimes"]["StdDev"][
                        category_idx
                    ] = sampled_value
            elif param_base == "DSM_Inflow_Split":
                if category_idx < len(updated_dsm_params[process_id]["inflow_split"]):
                    updated_dsm_params[process_id]["inflow_split"][
                        category_idx
                    ] = sampled_value
                    modified_inflow_splits.add(process_id)

            elif param_base.startswith("DSM_Output_") and param_base.endswith("_Split"):
                # Extract output number (e.g., "DSM_Output_1_Split_Cat_2" -> output 0, cat 1)
                output_num = int(param_base.split("_")[2]) - 1
                if category_idx < len(updated_dsm_params[process_id]["output_splits"]):
                    if output_num < len(
                        updated_dsm_params[process_id]["output_splits"][category_idx]
                    ):
                        updated_dsm_params[process_id]["output_splits"][category_idx][
                            output_num
                        ] = sampled_value
                        modified_output_splits.add((process_id, category_idx))

        except (ValueError, IndexError) as e:
            print(f"⚠️ WARNING: Could not parse DSM parameter name: {param_name} - {e}")
            continue

    # Normalize modified splits so they sum to 1.0
    for process_id in modified_inflow_splits:
        splits = updated_dsm_params[process_id]["inflow_split"]
        total = sum(splits)
        if total > 0:
            updated_dsm_params[process_id]["inflow_split"] = [s / total for s in splits]

    for process_id, cat_idx in modified_output_splits:
        splits = updated_dsm_params[process_id]["output_splits"][cat_idx]
        total = sum(splits)
        if total > 0:
            updated_dsm_params[process_id]["output_splits"][cat_idx] = [s / total for s in splits]

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
        # Check if this is a FOMP parameter (starts with P and contains FOMP-specific keywords)
        if param_name.startswith("P") and ("_decay_" in param_name or "_Inflow_fraction_f" in param_name):
            try:
                # Extract process ID from parameter name (e.g., "P08_decay_k1 (Labile pool)" -> 8)
                process_id = int(param_name[1:].split("_")[0])

                # Extract the base parameter name (e.g., "decay_k1 (Labile pool)")
                base_param_name = param_name.split("_", 1)[1]  # Remove "P08_" prefix

                # Apply the sampled value to the correct process and parameter
                if process_id in updated_fomp_params:
                    updated_fomp_params[process_id][base_param_name] = sampled_value
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


def normalize_tc_updates(tc_updates, mfa_system):
    """Normalizes sampled TC values so they sum to 1.0 per process and element.

    When multiple TCs for the same process (and element) are varied independently
    in a Monte Carlo iteration, their sampled values will generally not sum to 1.0.
    This function groups TCs by (element, process_id), checks whether the group
    covers all outgoing flows for that process, and if so normalizes proportionally.

    Parameters
    ----------
    tc_updates : dict
        Dictionary of parameter names to sampled values. Modified in-place.
        Only entries starting with ``TC_`` are considered.
    mfa_system : odym.MFAsystem
        The MFA system, used to count outgoing flows per process.

    Returns
    -------
    dict
        The same ``tc_updates`` dictionary with normalized TC values.
    """
    # Group TC entries by (element_prefix, process_id)
    # TC_05_06      -> (None, 5)
    # TC_E2_11_00   -> ("E2", 11)
    tc_groups = {}

    for tc_name, value in tc_updates.items():
        if not tc_name.startswith("TC_"):
            continue
        parts = tc_name.split("_")
        try:
            if parts[1].startswith("E") and len(parts) >= 4:
                elem_prefix = parts[1]
                process_id = int(parts[2])
            else:
                elem_prefix = None
                process_id = int(parts[1])

            key = (elem_prefix, process_id)
            if key not in tc_groups:
                tc_groups[key] = {}
            tc_groups[key][tc_name] = value
        except (ValueError, IndexError):
            continue

    # Normalize each group if it covers all outgoing flows
    for (elem_prefix, process_id), group in tc_groups.items():
        if len(group) < 2:
            continue  # Single TC — nothing to normalize

        # Count outgoing flows for this process
        n_outgoing = sum(
            1 for f in mfa_system.FlowDict.values() if f.P_Start == process_id
        )

        if len(group) >= n_outgoing:
            # All outgoing flows are covered — normalize to sum to 1.0
            total = sum(group.values())
            if total > 0:
                for tc_name in group:
                    tc_updates[tc_name] = group[tc_name] / total

    return tc_updates


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

    # Log all sampled values for this iteration
    print(f"\n   --- Iteration {iteration_num} sampled values ---")
    for param, value in sampled_params.items():
        print(f"   {param} = {value:.6f}")

    # --- 3b. Apply DSM parameter updates ---
    updated_dsm_params = apply_dsm_parameter_updates(dsm_params, sampled_params)

    # --- 3b2. Apply FOMP parameter updates ---
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

    # --- 3d. Normalize TCs per process to maintain mass balance ---
    normalize_tc_updates(tc_updates, mfa_system_setup)

    # --- 3e. Run Solver ---
    mfa_system_run, _ = solver.run_mfa_calculation(
        mfa_system_setup,
        updated_dsm_params,  # Use updated DSM parameters from MC sampling
        updated_fomp_params,  # Use updated FOMP parameters
        config,
        flow_tc_map=flow_tc_map,
        process_logic_map=process_logic_map,
        tc_updates=tc_updates,
    )

    # --- 3f. Collect Results ---
    iteration_results = {"iteration": iteration_num}
    for param, value in tc_updates.items():
        iteration_results[f"{param}_sample"] = value

    for stock in mfa_system_run.StockDict.values():
        for i_elem, element_name in enumerate(mfa_system_run.Elements):
            iteration_results[f"{stock.Name}_{element_name}"] = stock.Values[-1, i_elem]
            iteration_results[f"{stock.Name}_{element_name}_timeseries"] = stock.Values[
                :, i_elem
            ].tolist()

    # --- 3g. System-level mass balance check ---
    # Boundary processes are labeled "Input" and/or "Output".
    # In many ODYM systems, the environment (process 0) is labeled "Input"
    # and serves as both source and sink — flows FROM it are system inputs,
    # flows TO it are system outputs.
    boundary_processes = {
        pid for pid, logic in process_logic_map.items()
        if logic in ("Input", "Output")
    }

    n_elements = len(mfa_system_run.Elements)
    total_input = np.zeros(n_elements)
    total_output = np.zeros(n_elements)
    for flow in mfa_system_run.FlowDict.values():
        if flow.P_Start in boundary_processes:
            total_input += flow.Values.sum(axis=0)
        if flow.P_End in boundary_processes:
            total_output += flow.Values.sum(axis=0)

    # Only count internal process stocks — boundary process stocks (dS_0, dS_1)
    # would double-count the input/output already measured above.
    net_stock_change = np.zeros(n_elements)
    for stock in mfa_system_run.StockDict.values():
        if stock.Name.startswith("dS_"):
            pid = int(stock.Name.split("_")[1])
            if pid not in boundary_processes:
                net_stock_change += stock.Values.sum(axis=0)

    mb_error = total_input - total_output - net_stock_change

    # Store per-element errors for detailed reporting
    for i_elem, element_name in enumerate(mfa_system_run.Elements):
        iteration_results[f"mb_error_{element_name}"] = mb_error[i_elem]
        iteration_results[f"mb_input_{element_name}"] = total_input[i_elem]

    iteration_results["mass_balance_error_abs"] = np.abs(mb_error).sum()
    iteration_results["mass_balance_error_rel"] = (
        np.abs(mb_error).sum() / max(total_input.sum(), 1e-10)
    )

    return iteration_results


def generate_mc_setup_report(
    uncertainty_params, mfa_system, dsm_params, fomp_params, mc_params_df
):
    """Generates a detailed report of the Monte Carlo simulation setup.

    Parameters
    ----------
    uncertainty_params : dict
        Dictionary of uncertainty definitions.
    mfa_system : odym.MFAsystem
        The MFA system to validate against.
    dsm_params : dict
        Configuration dictionary for DSM processes.
    fomp_params : dict
        Configuration dictionary for FOMP processes.
    mc_params_df : pd.DataFrame
        DataFrame of Monte Carlo parameters loaded from Excel.

    Returns
    -------
    str
        A formatted string containing the setup report.
    """
    report_lines = [
        "_" * 80,
        "MONTE CARLO SIMULATION SETUP REPORT".center(80),
        "_" * 80,
    ]

    # 1. Uncertainty Parameter Summary
    report_lines.append("\n1. UNCERTAINTY PARAMETERS LOADED:")
    if not uncertainty_params:
        report_lines.append("   No uncertainty parameters defined.")
    else:
        for name, definition in uncertainty_params.items():
            dist = definition["distribution"]
            if dist == "normal":
                params = f"mean={definition['mean']}, std={definition['std']}"
            elif dist == "uniform":
                params = f"min={definition['min']}, max={definition['max']}"
            elif dist == "triangular":
                params = (
                    f"min={definition['min']}, mode={definition['mode']}, max={definition['max']}"
                )
            elif dist == "lognormal":
                params = f"mean={definition['mean']}, std={definition['std']}"
            else:
                params = "unknown parameters"
            report_lines.append(f"   - {name}: {dist.capitalize()}({params})")

    # 2. Parameter-to-Model Mapping
    report_lines.append("\n2. PARAMETER-TO-MODEL MAPPING:")
    process_name_map = {p.ID: p.Name for p in mfa_system.ProcessList}

    for name in uncertainty_params:
        target = "Unknown"
        if name.startswith("TC_"):
            try:
                parts = name.split("_")
                if parts[1].startswith("E") and len(parts) >= 4:
                    # Element-specific format: TC_E2_11_00
                    element_id = parts[1]
                    p_start, p_end = int(parts[2]), int(parts[3])
                    start_name = process_name_map.get(p_start, f"ID {p_start}")
                    end_name = process_name_map.get(p_end, f"ID {p_end}")
                    target = f"Transfer Coefficient ({element_id}) for flow: {start_name} -> {end_name}"
                else:
                    # Standard format: TC_05_06
                    p_start, p_end = int(parts[1]), int(parts[2])
                    start_name = process_name_map.get(p_start, f"ID {p_start}")
                    end_name = process_name_map.get(p_end, f"ID {p_end}")
                    target = f"Transfer Coefficient for flow: {start_name} -> {end_name}"
            except (ValueError, IndexError):
                target = "Transfer Coefficient (could not parse process IDs)"
        elif "_DSM_" in name:
            try:
                process_id = int(name.split("_")[0][1:])
                proc_name = process_name_map.get(process_id, f"ID {process_id}")
                if process_id in dsm_params:
                    param_type = "_".join(name.split("_")[1:])
                    target = f"DSM parameter '{param_type}' for Process {process_id} ('{proc_name}')"
                else:
                    target = f"DSM parameter for non-DSM Process {process_id} ('{proc_name}') - WILL BE IGNORED"
            except (ValueError, IndexError):
                target = "DSM parameter (could not parse process ID)"
        elif name.startswith("P") and ("_decay_" in name or "_Inflow_fraction_f" in name):
            try:
                process_id = int(name[1:].split("_")[0])
                proc_name = process_name_map.get(process_id, f"ID {process_id}")
                if process_id in fomp_params:
                    param_type = "_".join(name.split("_")[1:])
                    target = f"FOMP parameter '{param_type}' for Process {process_id} ('{proc_name}')"
                else:
                    target = f"FOMP parameter for non-FOMP Process {process_id} ('{proc_name}') - WILL BE IGNORED"
            except (ValueError, IndexError):
                target = "FOMP parameter (could not parse process ID)"

        report_lines.append(f"   - {name} -> {target}")

    # 3. Validation and Warnings
    report_lines.append("\n3. VALIDATION AND WARNINGS:")
    _, warnings = validate_mc_parameters(mc_params_df, mfa_system)
    if not warnings:
        report_lines.append("   No validation warnings. ✅")
    else:
        for warning in warnings:
            report_lines.append(f"   {warning}")

    report_lines.append("_" * 80)
    return "\n".join(report_lines)


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
    mc_params_df = input_data.get("4_1_Uncertainty_Parameters", pd.DataFrame())


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
