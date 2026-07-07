# -*- coding: utf-8 -*-
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


def validate_mc_parameters(mc_params_df, mfa_system, uncertainty_params=None):
    """Validates Monte Carlo parameters to ensure mass balance and prevent conflicts.

    Parameters
    ----------
    mc_params_df : pd.DataFrame
        DataFrame of Monte Carlo parameters loaded from Excel.
    mfa_system : odym.MFAsystem
        The MFA system to validate against.
    uncertainty_params : dict, optional
        Parsed uncertainty definitions (from load_uncertainty_definitions).
        When provided, enables TC group bounds compatibility checks.

    Returns
    -------
    tuple
        A tuple containing:
        - validated_params_df (pd.DataFrame): The validated parameters DataFrame.
        - warnings (list): A list of warning strings for any issues found.
    """
    warnings = []
    validated_params = mc_params_df.copy()
    # Normalise column name: new sheets use MC_Parameter_ID, legacy uses Parameter_Name
    if (
        "MC_Parameter_ID" in validated_params.columns
        and "Parameter_Name" not in validated_params.columns
    ):
        validated_params = validated_params.rename(
            columns={"MC_Parameter_ID": "Parameter_Name"}
        )

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
                    f for f in mfa_system.FlowDict.values() if f.P_Start == process_id
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

    # --- TC group bounds compatibility check ---
    if uncertainty_params:
        tc_groups = _group_tc_params(uncertainty_params)

        process_name_map = {p.ID: p.Name for p in mfa_system.ProcessList}

        for (elem_prefix, process_id), group in tc_groups.items():
            if len(group) < 2:
                continue

            proc_name = process_name_map.get(process_id, f"ID {process_id}")
            elem_label = f" [{elem_prefix}]" if elem_prefix else ""

            # Check if all TCs in this group have min/max bounds
            bounds = {}
            missing_bounds = []
            for tc_name, defn in group.items():
                tc_min = defn.get("min")
                tc_max = defn.get("max")
                if tc_min is not None and tc_max is not None:
                    bounds[tc_name] = (tc_min, tc_max)
                else:
                    missing_bounds.append(tc_name)

            if missing_bounds:
                warnings.append(
                    f"   TC group {proc_name}{elem_label}: "
                    f"{', '.join(missing_bounds)} missing Min/Max bounds "
                    f"-- rejection sampling disabled, using proportional normalization."
                )
                continue

            # Check feasibility: sum(min) <= 1.0 and sum(max) >= 1.0
            sum_min = sum(b[0] for b in bounds.values())
            sum_max = sum(b[1] for b in bounds.values())

            if sum_min > 1.0:
                warnings.append(
                    f"   INFEASIBLE: TC group {proc_name}{elem_label}: "
                    f"sum(Min) = {sum_min:.4f} > 1.0 -- no valid combination exists. "
                    f"Please widen the parameter ranges."
                )
            elif sum_max < 1.0:
                warnings.append(
                    f"   INFEASIBLE: TC group {proc_name}{elem_label}: "
                    f"sum(Max) = {sum_max:.4f} < 1.0 -- no valid combination exists. "
                    f"Please widen the parameter ranges."
                )
            else:
                warnings.append(
                    f"   TC group {proc_name}{elem_label}: bounds compatible "
                    f"(sum min={sum_min:.3f}, sum max={sum_max:.3f}). "
                    f"Rejection sampling enabled."
                )

    # --- Flow group validation ---
    if uncertainty_params:
        flow_group_registry: dict = {}
        for pname, defn in uncertainty_params.items():
            grp = defn.get("flow_group")
            if not grp:
                continue
            if not pname.startswith("F_"):
                warnings.append(
                    f"   ERROR: '{pname}' — MC_Flow_Group is only valid for F_... flow entries. "
                    f"Remove MC_Flow_Group for this parameter."
                )
                continue
            # Group by (name, time-window) so different windows of the same flow are validated separately
            _window = (defn.get("start_year"), defn.get("end_year"))
            flow_group_registry.setdefault((grp, _window), []).append(pname)

        for (grp, _window), members in flow_group_registry.items():
            _win_str = f" [years {_window[0]}–{_window[1]}]" if any(_window) else ""
            if len(members) == 1:
                warnings.append(
                    f"   WARNING: MC_Flow_Group '{grp}'{_win_str} has only one member ('{members[0]}'). "
                    f"A group needs at least two flows to have an effect."
                )
                continue

            # Check consistent operation across group members
            ops = {uncertainty_params[m].get("operation", "multiply") for m in members}
            if len(ops) > 1:
                warnings.append(
                    f"   ERROR: MC_Flow_Group '{grp}'{_win_str} — members have inconsistent MC_Operation "
                    f"values {ops}. All group members must use the same operation."
                )

            # Check consistent distribution type across group members
            dists = {uncertainty_params[m]["distribution"] for m in members}
            if len(dists) > 1:
                warnings.append(
                    f"   WARNING: MC_Flow_Group '{grp}'{_win_str} — members have different distribution "
                    f"types {dists}. Only the first member's draw is used; other distributions "
                    f"are ignored."
                )
            else:
                warnings.append(
                    f"   Flow group '{grp}'{_win_str}: {len(members)} members share one sample "
                    f"({list(dists)[0]}). Members: {members}"
                )

    # --- Operator and year-bound validation per parameter type ---
    if uncertainty_params:
        valid_ops = {"set", "multiply", "add"}
        dynamic_tc_names = set()
        for pname, param in mfa_system.ParameterDict.items():
            vals = getattr(param, "Values", None)
            if vals is not None and hasattr(vals, "__len__") and len(vals) > 1:
                dynamic_tc_names.add(pname)

        for pname, defn in uncertainty_params.items():
            op = defn.get("operation")
            has_start = "start_year" in defn
            has_end = "end_year" in defn
            has_window = has_start or has_end

            if pname.startswith("F_"):
                if op and op not in valid_ops:
                    warnings.append(
                        f"   ERROR: '{pname}' — unknown Operation '{op}'. "
                        f"Must be one of: set, multiply, add."
                    )

            elif pname.startswith("TC_"):
                if op and op not in ("set",):
                    warnings.append(
                        f"   ERROR: '{pname}' — Operation '{op}' is not valid for TC parameters. "
                        f"TC parameters are always sampled as absolute values (implicit 'set'). "
                        f"Remove the Operation field or set it to 'set'."
                    )
                if has_window and pname not in dynamic_tc_names:
                    warnings.append(
                        f"   WARNING: '{pname}' — start_year/end_year specified, but this TC "
                        f"does not appear to be a dynamic (time-series) TC. "
                        f"Year windowing only applies to dynamic TCs; the window will be ignored."
                    )

            else:
                # DSM or FOMP parameter
                if op and op not in ("set",):
                    warnings.append(
                        f"   ERROR: '{pname}' — Operation '{op}' is not valid for DSM/FOMP parameters. "
                        f"These parameters are always sampled as absolute values (implicit 'set'). "
                        f"Remove the Operation field or set it to 'set'."
                    )
                if has_window:
                    warnings.append(
                        f"   ERROR: '{pname}' — start_year/end_year is not applicable to "
                        f"DSM/FOMP parameters (they are time-invariant constants). "
                        f"Remove the year columns for this entry."
                    )

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
                if category_idx < len(
                    updated_dsm_params[process_id]["lifetimes"]["Mean"]
                ):
                    updated_dsm_params[process_id]["lifetimes"]["Mean"][
                        category_idx
                    ] = sampled_value
            elif param_base == "DSM_Lifetime_StdDev":
                if category_idx < len(
                    updated_dsm_params[process_id]["lifetimes"]["StdDev"]
                ):
                    updated_dsm_params[process_id]["lifetimes"]["StdDev"][
                        category_idx
                    ] = sampled_value
            elif param_base == "DSM_Lifetime_Shape":
                shapes = updated_dsm_params[process_id]["lifetimes"].setdefault(
                    "Shape",
                    [None] * len(updated_dsm_params[process_id]["inflow_split"]),
                )
                if category_idx < len(shapes):
                    shapes[category_idx] = sampled_value
            elif param_base == "DSM_Lifetime_Scale":
                scales = updated_dsm_params[process_id]["lifetimes"].setdefault(
                    "Scale",
                    [None] * len(updated_dsm_params[process_id]["inflow_split"]),
                )
                if category_idx < len(scales):
                    scales[category_idx] = sampled_value
            elif param_base == "DSM_Inflow_Split":
                if category_idx < len(updated_dsm_params[process_id]["inflow_split"]):
                    updated_dsm_params[process_id]["inflow_split"][category_idx] = (
                        sampled_value
                    )
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
            updated_dsm_params[process_id]["output_splits"][cat_idx] = [
                s / total for s in splits
            ]

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
        if param_name.startswith("P") and (
            "_decay_" in param_name or "_Inflow_fraction_f" in param_name
        ):
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


def _parse_tc_group_key(tc_name):
    """Extracts (element_prefix, process_id) from a TC parameter name.

    Parameters
    ----------
    tc_name : str
        TC parameter name, e.g. ``TC_05_06`` or ``TC_E2_11_00``.

    Returns
    -------
    tuple or None
        ``(element_prefix, process_id)`` on success, ``None`` on parse failure.
    """
    parts = tc_name.split("_")
    try:
        if parts[1].startswith("E") and len(parts) >= 4:
            return (parts[1], int(parts[2]))
        else:
            return (None, int(parts[1]))
    except (ValueError, IndexError):
        return None


def _group_tc_params(uncertainty_params):
    """Groups TC uncertainty definitions by (element_prefix, process_id).

    Parameters
    ----------
    uncertainty_params : dict
        Full uncertainty definitions dict (keys are parameter names).

    Returns
    -------
    dict
        ``{(elem_prefix, process_id): {tc_name: definition_dict, ...}, ...}``
    """
    tc_groups = {}
    for tc_name, defn in uncertainty_params.items():
        if not tc_name.startswith("TC_"):
            continue
        key = _parse_tc_group_key(tc_name)
        if key is not None:
            tc_groups.setdefault(key, {})[tc_name] = defn
    return tc_groups


def normalize_tc_updates(
    tc_updates, mfa_system, uncertainty_params=None, max_retries=100, rng=None
):
    """Normalizes sampled TC values so they sum to 1.0 per process and element.

    When ``uncertainty_params`` is provided and **all** TCs in a group have
    Min/Max bounds, this function uses *rejection sampling*: it normalizes the
    sampled values and checks whether every normalized value still falls within
    its defined [min, max] range. If not, it resamples from the original
    distributions and tries again (up to ``max_retries`` attempts).

    Falls back to simple proportional normalization when bounds are missing or
    rejection sampling cannot find a valid combination.

    Parameters
    ----------
    tc_updates : dict
        Dictionary of parameter names to sampled values. Modified in-place.
        Only entries starting with ``TC_`` are considered.
    mfa_system : odym.MFAsystem
        The MFA system, used to count outgoing flows per process.
    uncertainty_params : dict, optional
        Parsed uncertainty definitions. When provided, enables rejection
        sampling for groups where all TCs have min/max bounds.
    max_retries : int, optional
        Maximum number of resample attempts before falling back to
        proportional normalization. Default 100.

    Returns
    -------
    dict
        The same ``tc_updates`` dictionary with normalized TC values.
    """
    # Group TC entries from tc_updates by (element_prefix, process_id)
    tc_groups = {}
    for tc_name, value in tc_updates.items():
        if not tc_name.startswith("TC_"):
            continue
        key = _parse_tc_group_key(tc_name)
        if key is not None:
            tc_groups.setdefault(key, {})[tc_name] = value

    for (elem_prefix, process_id), group in tc_groups.items():
        if len(group) < 2:
            continue  # Single TC — nothing to normalize

        # Count outgoing flows for this process
        n_outgoing = sum(
            1 for f in mfa_system.FlowDict.values() if f.P_Start == process_id
        )
        if len(group) < n_outgoing:
            continue  # Not all flows covered — skip normalization

        # Check if bounds are available for all TCs in this group
        bounds = {}
        if uncertainty_params:
            all_have_bounds = True
            for tc_name in group:
                defn = uncertainty_params.get(tc_name, {})
                tc_min = defn.get("min")
                tc_max = defn.get("max")
                if tc_min is not None and tc_max is not None:
                    bounds[tc_name] = (tc_min, tc_max)
                else:
                    all_have_bounds = False
                    break
            if not all_have_bounds:
                bounds = {}

        if not bounds:
            # No bounds available — proportional normalization only
            total = sum(group.values())
            if total > 0:
                for tc_name in group:
                    tc_updates[tc_name] = group[tc_name] / total
            continue

        # --- Rejection sampling with bounds ---
        accepted = False
        for attempt in range(max_retries):
            if attempt == 0:
                # First try: normalize the already-sampled values
                candidate = dict(group)
            else:
                # Resample just the TCs in this group from their distributions
                tc_subset = {tc_name: uncertainty_params[tc_name] for tc_name in group}
                candidate = sample_parameters(tc_subset, rng=rng)

            total = sum(candidate.values())
            if total <= 0:
                continue
            normalized = {k: v / total for k, v in candidate.items()}

            # Check if all normalized values are within bounds
            within_bounds = all(
                bounds[tc_name][0] <= normalized[tc_name] <= bounds[tc_name][1]
                for tc_name in normalized
            )

            if within_bounds:
                accepted = True
                for tc_name, value in normalized.items():
                    tc_updates[tc_name] = value
                break

        if not accepted:
            # Fallback to proportional normalization of original samples
            elem_label = f" [{elem_prefix}]" if elem_prefix else ""
            print(
                f"   [MC] Rejection sampling failed after {max_retries} attempts "
                f"for process {process_id}{elem_label}. "
                f"Using proportional normalization (values may exceed defined bounds)."
            )
            total = sum(group.values())
            if total > 0:
                for tc_name in group:
                    tc_updates[tc_name] = group[tc_name] / total

    return tc_updates


#: Sampled parameters matching these name markers must be strictly positive
#: (mean lifetimes, Weibull shape/scale, first-order decay constants) or
#: non-negative (lifetime standard deviations). Draws outside the valid range
#: are rejection-resampled to preserve the distribution shape within bounds.
_STRICTLY_POSITIVE_MARKERS = (
    "_DSM_Lifetime_Mean",
    "_DSM_Lifetime_Shape",
    "_DSM_Lifetime_Scale",
    "_decay_",
)
_NON_NEGATIVE_MARKERS = ("_DSM_Lifetime_StdDev",)


def _enforce_physical_bounds(
    sampled_params, uncertainty_params, rng=None, max_retries=100
):
    """Rejection-resample physically impossible draws (negative rates/lifetimes).

    Modifies ``sampled_params`` in place and returns it. If a valid draw
    cannot be found within ``max_retries`` (a distribution with almost all
    mass below zero), the value is clamped to a small positive epsilon and a
    warning is printed — such a distribution definition is almost certainly
    a data-entry error.
    """
    for param_name, value in sampled_params.items():
        strictly_positive = any(
            m in param_name for m in _STRICTLY_POSITIVE_MARKERS
        )
        non_negative = any(m in param_name for m in _NON_NEGATIVE_MARKERS)
        if not (strictly_positive or non_negative):
            continue

        def _valid(v):
            return v > 0 if strictly_positive else v >= 0

        if _valid(value):
            continue

        defn = uncertainty_params.get(param_name)
        resampled = False
        if defn:
            for _ in range(max_retries):
                value = sample_parameters({param_name: defn}, rng=rng)[param_name]
                if _valid(value):
                    resampled = True
                    break

        if not resampled:
            epsilon = 1e-9
            print(
                f"[MC] WARNING: {param_name} produced no physically valid draw "
                f"after {max_retries} attempts — clamped to {epsilon}. "
                f"Check its distribution definition."
            )
            value = epsilon if strictly_positive else 0.0

        sampled_params[param_name] = value

    return sampled_params


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
    rng=None,
    lfg_params=None,
    bom_params=None,
    flow_cap_params=None,
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
    lfg_params, bom_params, flow_cap_params : dict, optional
        Module configuration dicts passed through to the solver unmodified
        (not sampled), so these process logic types stay active during MC.

    Returns
    -------
    dict
        A dictionary containing all the results for this single iteration.
    """
    # --- 3a. Sample parameters ---
    sampled_params = sample_parameters(uncertainty_params, rng=rng)
    _enforce_physical_bounds(sampled_params, uncertainty_params, rng=rng)

    # --- 3a2. Flow group consolidation: all members share the first member's draw ---
    # Group by (flow_group, start_year, end_year) so different time windows are sampled independently
    _flow_groups: dict = {}
    for _pname, _defn in uncertainty_params.items():
        _grp = _defn.get("flow_group")
        if _grp and _pname.startswith("F_"):
            _window = (_defn.get("start_year"), _defn.get("end_year"))
            _flow_groups.setdefault((_grp, _window), []).append(_pname)
    for (_grp, _window), _members in _flow_groups.items():
        if len(_members) < 2:
            continue
        _shared = sampled_params.get(_members[0])
        if _shared is not None:
            for _m in _members[1:]:
                if _m in sampled_params:
                    sampled_params[_m] = _shared

    # TC/DSM/FOMP entries only — F_... flows are handled separately
    tc_updates = {k: v for k, v in sampled_params.items() if not k.startswith("F_")}

    # --- 3b. Apply DSM parameter updates ---
    updated_dsm_params = apply_dsm_parameter_updates(dsm_params, sampled_params)

    # --- 3b2. Apply FOMP parameter updates ---
    updated_fomp_params = apply_fomp_parameter_updates(fomp_params, sampled_params)

    # --- 3b3. Build flow updates from F_... entries ---
    # List of (flow_id, spec) tuples — allows multiple windowed specs for the same flow
    flow_updates = []
    for param_name, sampled_value in sampled_params.items():
        if not param_name.startswith("F_"):
            continue
        defn = uncertainty_params.get(param_name, {})
        flow_id = defn.get(
            "flow_id", param_name
        )  # strips ::N suffix to get real flow name
        entry = {
            "value": sampled_value,
            "operation": defn.get("operation", "multiply"),
        }
        if "start_year" in defn:
            entry["start_year"] = defn["start_year"]
        if "end_year" in defn:
            entry["end_year"] = defn["end_year"]
        flow_updates.append((flow_id, entry))

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
    # Pass uncertainty_params to enable rejection sampling with bounds checking
    normalize_tc_updates(
        tc_updates, mfa_system_setup, uncertainty_params=uncertainty_params, rng=rng
    )

    # --- 3d2. Upgrade year-windowed TC entries to dict format (after normalization) ---
    for param_name in list(tc_updates.keys()):
        if not param_name.startswith("TC_"):
            continue
        defn = uncertainty_params.get(param_name, {})
        start_y = defn.get("start_year")
        end_y = defn.get("end_year")
        if start_y is not None or end_y is not None:
            tc_updates[param_name] = {
                "value": tc_updates[param_name],
                "start_year": start_y,
                "end_year": end_y,
            }

    # Log sampled values for the first 3 iterations only (to verify without flooding)
    if iteration_num <= 3:
        print(
            f"\n   --- Iteration {iteration_num} sampled values (post-normalization) ---"
        )
        for param, value in sampled_params.items():
            if param.startswith("TC_"):
                tc_val = tc_updates.get(param, value)
                normalized_val = tc_val["value"] if isinstance(tc_val, dict) else tc_val
                if abs(normalized_val - value) > 1e-8:
                    print(
                        f"   {param} = {value:.6f} -> {normalized_val:.6f} (normalized)"
                    )
                else:
                    print(f"   {param} = {value:.6f}")
            elif param.startswith("F_"):
                defn_log = uncertainty_params.get(param, {})
                op = defn_log.get("operation", "multiply")
                sy = defn_log.get("start_year", "—")
                ey = defn_log.get("end_year", "—")
                window = f"  [{sy}–{ey}]" if (sy != "—" or ey != "—") else ""
                grp = defn_log.get("flow_group")
                grp_tag = f"  group={grp}" if grp else ""
                flow_id = defn_log.get("flow_id", param)
                display = flow_id if flow_id == param else f"{flow_id} [{param}]"
                print(f"   {display} = {value:.6f}  op={op}{window}{grp_tag}")
            else:
                print(f"   {param} = {value:.6f}")

    # --- 3e. Run Solver ---
    # LFG/BOM/FlowCap params are passed through unmodified (not yet sampled),
    # so that processes with these logic types stay active during MC runs.
    mfa_system_run, _, solver_info = solver.run_mfa_calculation(
        mfa_system_setup,
        updated_dsm_params,
        updated_fomp_params,
        config,
        flow_tc_map=flow_tc_map,
        process_logic_map=process_logic_map,
        tc_updates=tc_updates,
        flow_updates=flow_updates if flow_updates else None,
        lfg_params=lfg_params or {},
        bom_params=bom_params or {},
        flow_cap_params=flow_cap_params or {},
    )

    # --- 3f. Collect Results ---
    iteration_results = {
        "iteration": iteration_num,
        "converged": bool(solver_info.get("converged", True)),
    }
    for param, value in tc_updates.items():
        iteration_results[f"{param}_sample"] = value

    for stock in mfa_system_run.StockDict.values():
        for i_elem, element_name in enumerate(mfa_system_run.Elements):
            iteration_results[f"{stock.Name}_{element_name}"] = stock.Values[-1, i_elem]
            iteration_results[f"{stock.Name}_{element_name}_timeseries"] = stock.Values[
                :, i_elem
            ].tolist()

    # --- 3g. Per-process mass balance check ---
    # Uses S-based stock changes (S[t] - S[t-1]) instead of dS from StockDict.
    # The solver's calculate_final_balances overwrites dS = inflow - outflow for
    # every process, making any dS-based check tautologically zero.
    # Using the actual S trajectory preserves the DSM model's independent stock
    # calculation, enabling detection of real mass balance discrepancies.
    boundary_processes = {
        pid for pid, logic in process_logic_map.items() if logic in ("Input", "Output")
    }

    n_elements = len(mfa_system_run.Elements)
    num_years = len(mfa_system_run.IndexTable.Classification["Time"].Items)

    # Build per-process inflow/outflow sums (dict-based)
    process_inflows = {}
    process_outflows = {}
    for flow in mfa_system_run.FlowDict.values():
        if flow.P_End not in process_inflows:
            process_inflows[flow.P_End] = np.zeros((num_years, n_elements))
        process_inflows[flow.P_End] += flow.Values
        if flow.P_Start not in process_outflows:
            process_outflows[flow.P_Start] = np.zeros((num_years, n_elements))
        process_outflows[flow.P_Start] += flow.Values

    # Track total system input (outflows from boundary processes = system inputs)
    total_input = np.zeros(n_elements)
    for pid in boundary_processes:
        if pid in process_outflows:
            total_input += process_outflows[pid].sum(axis=0)

    # Per-process balance: error_p = inflow_p - outflow_p - delta_S_p
    # where delta_S is derived from actual S values, not from solver-overwritten dS
    total_abs_error = np.zeros(n_elements)
    for p in mfa_system_run.ProcessList:
        if p.ID in boundary_processes:
            continue

        inflow = process_inflows.get(p.ID, np.zeros((num_years, n_elements)))
        outflow = process_outflows.get(p.ID, np.zeros((num_years, n_elements)))

        # Derive stock change from actual S trajectory (not dS)
        s_stock = mfa_system_run.StockDict.get(f"S_{p.ID}")
        if s_stock is not None:
            S = s_stock.Values  # (num_years, n_elements)
            # delta_S[t] = S[t] - S[t-1], skipping year 0 (initial stock ambiguity)
            delta_S_from_S = np.diff(S, axis=0)  # (num_years-1, n_elements)
            process_error = inflow[1:] - outflow[1:] - delta_S_from_S
        else:
            # No stock entry: full check with delta_S = 0
            process_error = inflow - outflow

        total_abs_error += np.abs(process_error).sum(axis=0)

    # Store per-element errors for detailed reporting
    for i_elem, element_name in enumerate(mfa_system_run.Elements):
        iteration_results[f"mb_error_{element_name}"] = total_abs_error[i_elem]
        iteration_results[f"mb_input_{element_name}"] = total_input[i_elem]

    iteration_results["mass_balance_error_abs"] = total_abs_error.sum()
    iteration_results["mass_balance_error_rel"] = total_abs_error.sum() / max(
        total_input.sum(), 1e-10
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
                params = f"min={definition['min']}, mode={definition['mode']}, max={definition['max']}"
            elif dist == "lognormal":
                params = f"mean={definition['mean']}, std={definition['std']}"
            else:
                params = "unknown parameters"
            op = definition.get("operation")
            sy = definition.get("start_year")
            ey = definition.get("end_year")
            extras = ""
            if op:
                extras += f"  op={op}"
            if sy is not None or ey is not None:
                extras += f"  years={sy or '…'}–{ey or '…'}"
            report_lines.append(f"   - {name}: {dist.capitalize()}({params}){extras}")

    # 2. Parameter-to-Model Mapping
    report_lines.append("\n2. PARAMETER-TO-MODEL MAPPING:")
    process_name_map = {p.ID: p.Name for p in mfa_system.ProcessList}

    for name in uncertainty_params:
        target = "Unknown"
        defn = uncertainty_params[name]
        op = defn.get("operation", "multiply" if name.startswith("F_") else "set")
        sy = defn.get("start_year")
        ey = defn.get("end_year")
        window = f" [years {sy}–{ey}]" if (sy or ey) else ""

        if name.startswith("F_"):
            try:
                flow_id = defn.get(
                    "flow_id", name
                )  # real flow name (strips ::N suffix)
                parts = flow_id.split("_")
                p_start, p_end = int(parts[1]), int(parts[2])
                start_name = process_name_map.get(p_start, f"ID {p_start}")
                end_name = process_name_map.get(p_end, f"ID {p_end}")
                exists = flow_id in mfa_system.FlowDict
                status = "" if exists else " — WARNING: flow not found in system"
                grp = defn.get("flow_group")
                grp_tag = f"  [group: {grp}]" if grp else ""
                target = (
                    f"Flow ({op}): {start_name} -> {end_name}{window}{grp_tag}{status}"
                )
            except (ValueError, IndexError):
                target = "Flow (could not parse process IDs)"
        elif name.startswith("TC_"):
            try:
                parts = name.split("_")
                if parts[1].startswith("E") and len(parts) >= 4:
                    element_id = parts[1]
                    p_start, p_end = int(parts[2]), int(parts[3])
                    start_name = process_name_map.get(p_start, f"ID {p_start}")
                    end_name = process_name_map.get(p_end, f"ID {p_end}")
                    target = f"Transfer Coefficient ({element_id}) for flow: {start_name} -> {end_name}{window}"
                else:
                    p_start, p_end = int(parts[1]), int(parts[2])
                    start_name = process_name_map.get(p_start, f"ID {p_start}")
                    end_name = process_name_map.get(p_end, f"ID {p_end}")
                    target = f"Transfer Coefficient for flow: {start_name} -> {end_name}{window}"
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
        elif name.startswith("P") and (
            "_decay_" in name or "_Inflow_fraction_f" in name
        ):
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
    _, warnings = validate_mc_parameters(mc_params_df, mfa_system, uncertainty_params)
    if not warnings:
        report_lines.append("   No validation warnings. ✅")
    else:
        for warning in warnings:
            report_lines.append(f"   {warning}")

    report_lines.append("_" * 80)
    return "\n".join(report_lines)


#: Default MC seed — fixed so Monte Carlo runs are reproducible by default.
#: Override with a Configuration-sheet row "MC_Seed" (int), or set it to
#: "random" / "none" for unseeded, non-reproducible sampling.
DEFAULT_MC_SEED = 42


def _resolve_mc_seed(config):
    """Return the MC seed from config, or None for unseeded sampling."""
    seed = getattr(config, "MC_SEED", DEFAULT_MC_SEED)
    if seed is None:
        return None
    if isinstance(seed, str) and seed.strip().lower() in ("", "none", "random"):
        return None
    try:
        return int(seed)
    except (TypeError, ValueError):
        print(
            f"[MC] WARNING: invalid MC_Seed value {seed!r} — "
            f"using default seed {DEFAULT_MC_SEED}."
        )
        return DEFAULT_MC_SEED


def run_mc_simulation(
    mfa_system_setup,
    input_data,
    dsm_params,
    fomp_params,
    config,
    process_logic_map,
    flow_tc_map,
    lfg_params=None,
    bom_params=None,
    flow_cap_params=None,
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
    lfg_params : dict, optional
        Configuration dictionary for LFG processes. Not sampled, but required
        so LFG processes stay active during MC iterations.
    bom_params : dict, optional
        Configuration dictionary for BOM_Assembler processes (same reason).
    flow_cap_params : dict, optional
        Configuration dictionary for FlowCap processes (same reason).

    Returns
    -------
    pd.DataFrame or None
        A DataFrame containing the results of all Monte Carlo iterations, or
        None if no uncertainty parameters are defined.
    """
    # --- 1. Configuration ---
    # Re-register FlowCap cap parameters on the base system: the solver
    # deep-copies it each iteration, and register_cap_parameters is a no-op
    # for keys that already exist (same pattern as the scenario engine).
    if flow_cap_params:
        from engine import flow_cap as _fc

        _fc.register_cap_parameters(mfa_system_setup, flow_cap_params)

    n_iterations = getattr(config, "MC_ITERATIONS", 100)
    seed = _resolve_mc_seed(config)
    rng = np.random.default_rng(seed)
    uncertainty_params = data_loader.load_uncertainty_definitions(input_data)
    input_data.get("4_1_Uncertainty_Parameters", pd.DataFrame())

    if not uncertainty_params:
        print("\n[MC] No uncertainty parameters defined. Skipping simulation.")
        return None

    print(f"\n[MC] Running Monte Carlo simulation with {n_iterations} iterations...")
    if seed is not None:
        print(f"[MC] RNG seed: {seed} (set 'MC_Seed' in the configuration to change)")
    else:
        print("[MC] RNG seed: none (results are NOT reproducible across runs)")

    # --- 1b. Pre-flight check: verify all F_... entries exist in FlowDict ---
    known_flows = set(mfa_system_setup.FlowDict.keys())
    _seen_flow_ids: set = set()
    missing_flows = []
    for _name, _defn in uncertainty_params.items():
        if not _name.startswith("F_"):
            continue
        _flow_id = _defn.get("flow_id", _name)
        if _flow_id in _seen_flow_ids:
            continue
        _seen_flow_ids.add(_flow_id)
        if _flow_id not in known_flows:
            missing_flows.append(_flow_id)
    if missing_flows:
        print(
            "\n[MC] ERROR: The following flow IDs in MC_Parameter_ID were not found in the"
        )
        print(
            "     model's FlowDict. The MC run will produce NO uncertainty for these flows."
        )
        print(
            "     Check that MC_Parameter_ID exactly matches the Flow_ID in '1_2_Data_Flows'."
        )
        print(f"     Missing: {missing_flows}")
        print(f"     Available flows: {sorted(known_flows)}")

    # --- 1c. Pre-flight check: every parameter name must be classifiable ---
    # Consumers identify parameters purely by naming convention (TC_..., F_...,
    # P##_DSM_..., P##_decay_... / P##_Inflow_fraction_f...). A renamed or
    # malformed entry would otherwise be sampled but silently never applied.
    unclassified = []
    for _name in uncertainty_params:
        # Names registered directly in ParameterDict (FlowCap caps like
        # "TC_Cap_02", flow-content fractions like "WC_F_01_02") are applied
        # via the tc_updates path even though they match no TC/F_/P## pattern.
        if _name in mfa_system_setup.ParameterDict:
            continue
        if _name.startswith("TC_"):
            if _parse_tc_group_key(_name) is None:
                unclassified.append(f"{_name} (unparseable TC name)")
        elif _name.startswith("F_"):
            continue
        elif _name.startswith("P") and "_DSM_" in _name:
            continue
        elif _name.startswith("P") and (
            "_decay_" in _name or "_Inflow_fraction_f" in _name
        ):
            continue
        else:
            unclassified.append(_name)
    if unclassified:
        print(
            "\n[MC] WARNING: the following uncertainty parameters match no known "
            "naming convention and will be sampled but NEVER APPLIED:"
        )
        for _name in unclassified:
            print(f"     - {_name}")
        print(
            "     Expected: TC_<p>_<p> / TC_E<n>_<p>_<p>, F_<flow>, "
            "P<p>_DSM_..., P<p>_decay_... or P<p>_Inflow_fraction_f..."
        )

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
    failed_runs = []
    print(f"[MC] Using {len(uncertainty_params)} validated parameters...")

    # Scale progress reporting: ~20 progress updates total
    progress_interval = max(1, n_iterations // 20)

    for i in range(n_iterations):
        if (i + 1) % progress_interval == 0 or (i + 1) == n_iterations:
            print(f"  ... iteration {i + 1}/{n_iterations}")

        try:
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
                rng=rng,
                lfg_params=lfg_params,
                bom_params=bom_params,
                flow_cap_params=flow_cap_params,
            )
        except Exception as exc:
            # One bad sample must not kill the whole batch: record it, skip
            # the iteration (no partial/NaN row), and keep going.
            failed_runs.append({"iteration": i + 1, "error": repr(exc)})
            print(f"[MC] WARNING: iteration {i + 1} failed and was skipped: {exc!r}")
            continue
        results_list.append(iteration_results)

    # --- 4. Batch summary ---
    n_failed = len(failed_runs)
    n_success = len(results_list)
    n_nonconverged = sum(1 for r in results_list if not r.get("converged", True))
    print(
        f"[MC] Simulation finished: {n_success} succeeded, {n_failed} failed, "
        f"{n_nonconverged} did not converge."
    )
    if n_failed:
        print(f"[MC] Failed iterations: {[f['iteration'] for f in failed_runs]}")
    if n_nonconverged:
        print(
            "[MC] WARNING: non-converged iterations are included in the results "
            "(filter on the 'converged' column to exclude them)."
        )

    results_df = pd.DataFrame(results_list)
    results_df.attrs["mc_summary"] = {
        "n_iterations": n_iterations,
        "n_success": n_success,
        "n_failed": n_failed,
        "n_nonconverged": n_nonconverged,
        "failed_runs": failed_runs,
        "seed": seed,
    }
    return results_df
