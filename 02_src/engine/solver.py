# -*- coding: utf-8 -*-
"""
Solver Module for the BioDYM MFA Model's Engine.

This file contains the core iterative solver that orchestrates the
calculation of the entire MFA system. It calls the specific model
functions (DSM, FOMP) in the correct sequence until the system converges.
"""

import collections
import numpy as np
import copy


# Import other engine components
from . import dsm_model
from . import fomp_model
from . import lfg_model
from . import bom_assembler as _bom_assembler
from . import flow_cap as _flow_cap


def _topological_sort_flows(mfa_system):
    """Sort FlowDict keys in topological dependency order (upstream processes first).

    Uses Kahn's BFS algorithm on the process graph derived from flow P_Start/P_End
    attributes. Flows originating from upstream (low-rank) processes are sorted
    before those from downstream processes.

    When flows are processed in this order inside the iterative solver, all
    resolvable flows in a chain can be calculated in a single pass, reducing
    the number of solver iterations from O(chain_depth) to O(1).

    Cycles (if present) are detected and placed last — they do not affect
    the correctness of acyclic parts of the graph.

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        The MFA system whose FlowDict will be sorted.

    Returns
    -------
    list of str
        Flow names sorted in topological order by their source process rank.
    """
    all_pids = {p.ID for p in mfa_system.ProcessList}
    adj = {pid: [] for pid in all_pids}
    in_degree = {pid: 0 for pid in all_pids}

    for flow in mfa_system.FlowDict.values():
        if flow.P_Start in all_pids and flow.P_End in all_pids:
            adj[flow.P_Start].append(flow.P_End)
            in_degree[flow.P_End] += 1

    # Kahn's BFS — start from source processes (no incoming flows)
    queue = collections.deque(pid for pid in all_pids if in_degree[pid] == 0)
    topo_rank = {}
    rank = 0
    while queue:
        pid = queue.popleft()
        topo_rank[pid] = rank
        rank += 1
        for downstream in adj[pid]:
            in_degree[downstream] -= 1
            if in_degree[downstream] == 0:
                queue.append(downstream)

    # Cyclic nodes (if any) get a rank beyond all acyclic nodes
    for pid in all_pids:
        if pid not in topo_rank:
            topo_rank[pid] = rank

    return sorted(
        mfa_system.FlowDict.keys(),
        key=lambda name: topo_rank.get(mfa_system.FlowDict[name].P_Start, rank),
    )


def calculate_final_balances(mfa_system, dsm_processes=None, fomp_processes=None):
    """Calculates the final stock changes (dS) and absolute stocks (S).

    This is the final accounting step of the calculation, performed after the
    iterative solver has converged. It correctly respects any initial stocks
    set during the system setup.

    NOTE: DSM and FOMP processes already have their stocks fully calculated by their
    respective models, so they are skipped to avoid double-counting. Without this skip,
    the solver would treat the FOMP-written year-1 stock as an "initial stock offset"
    and add it again via cumsum(dS), causing a phantom doubling in year 1 and a
    persistent offset in all subsequent years.

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        The MFA system object with all flows calculated.
    dsm_processes : set, optional
        Set of process IDs that are DSM processes (already have stocks calculated).
    fomp_processes : set, optional
        Set of process IDs that are FOMP processes (already have stocks calculated).

    Returns
    -------
    odym.MFAsystem
        The MFA system object with final stock values updated.
    """
    if dsm_processes is None:
        dsm_processes = set()
    if fomp_processes is None:
        fomp_processes = set()

    # Skip DSM and FOMP processes — both models write correct stock values directly
    special_processes = dsm_processes | fomp_processes

    print("--> Calculating final stock balances for non-DSM processes...")
    print(f"    special_processes (skip list): {sorted(special_processes)}")

    for pid in {p.ID for p in mfa_system.ProcessList}:
        if f"S_{pid}" in mfa_system.StockDict:
            stock_s, stock_ds = (
                mfa_system.StockDict[f"S_{pid}"],
                mfa_system.StockDict[f"dS_{pid}"],
            )

            inflows = [f.Values for f in mfa_system.FlowDict.values() if f.P_End == pid]
            outflows = [
                f.Values for f in mfa_system.FlowDict.values() if f.P_Start == pid
            ]
            total_inflows = sum(inflows) if inflows else np.zeros_like(stock_s.Values)
            total_outflows = (
                sum(outflows) if outflows else np.zeros_like(stock_s.Values)
            )
            # DSM/FOMP processes write their own correct absolute stock values.
            # Derive dS from the stock derivative so that an initial stock at t=0
            # is reflected as a positive dS[0] rather than a large phantom outflow.
            if pid in special_processes:
                dS_values = np.zeros_like(stock_s.Values)
                dS_values[1:, :] = stock_s.Values[1:, :] - stock_s.Values[:-1, :]
                dS_values[0, :] = stock_s.Values[0, :]
                stock_ds.Values = dS_values
                print(f"  -> Skipping stock recalculation for Process {pid} (DSM/FOMP)")
                continue

            dS_values = total_inflows - total_outflows
            stock_ds.Values = dS_values

            initial_stock_vector = stock_s.Values[0, :].copy()
            # S[t] = initial_stock + cumulative_sum(dS[0:t+1])
            # This ensures S[0] includes dS[0], not just initial_stock
            new_s_values = initial_stock_vector + np.cumsum(dS_values, axis=0)
            stock_s.Values = new_s_values

    print("--> Stock balance calculation finished.")

    try:
        mfa_system.Consistency_Check()
        print("✅ Balance validation passed")
    except Exception as e:
        print(f"⚠️ Balance validation warning: {e}")

    return mfa_system


def enhanced_input_validation(input_flows, dsm_processes):
    """Validates if a process has valid inputs to justify calculation.

    This check is more robust than a simple check for non-zero flows, as it
    correctly handles cases where a flow exists but has a value of zero for
    a given time step. It checks if the total sum of all values across all
    inflows is greater than zero.

    Parameters
    ----------
    input_flows : list of odym.Flow
        A list of all flow objects that are inputs to a specific process.
    dsm_processes : set
        A set of all process IDs that are defined as DSM processes.

    Returns
    -------
    bool
        True if the total sum of all inflow values is greater than zero.
    """
    if not input_flows:
        return False

    # Check if the sum of all values in all input flows is greater than zero.
    # This is a more robust check than np.any() for each flow, as it
    # correctly handles cases where a flow is valid but has a 0 value.
    total_inflow_sum = sum(
        np.sum(f.Values) for f in input_flows if f.Values is not None
    )

    return total_inflow_sum > 0


def _calculate_tc_driven_flows(
    mfa_system,
    special_processes,
    process_logic_map,
    flow_tc_map,
    dsm_processes,
    config=None,
    sorted_flow_names=None,
):
    """Calculates all flows that are driven by transfer coefficients (TCs).

    This function iterates through all flows in the system, identifies those
    governed by simple TC-based processes (Splitter, Transformer), and calculates
    their output values based on the total inflow and the defined TCs.

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        The MFA system object, which will be modified in place.
    special_processes : set
        A set of process IDs that are handled by special models (DSM, FOMP).
    process_logic_map : dict
        Maps process IDs to their logic string (e.g., 'Splitter').
    flow_tc_map : dict
        Maps flow names to their corresponding TC parameter names.
    dsm_processes : set
        A set of DSM process IDs, used for input validation.
    sorted_flow_names : list of str, optional
        Flow names in topological order. If provided, flows are processed
        upstream-first so dependency chains resolve in a single pass.

    Returns
    -------
    bool
        True if any flow values were changed during the calculation, False otherwise.
    """
    something_changed = False
    flow_iter = (
        (
            (name, mfa_system.FlowDict[name])
            for name in sorted_flow_names
            if name in mfa_system.FlowDict
        )
        if sorted_flow_names is not None
        else ((flow.Name, flow) for flow in mfa_system.FlowDict.values())
    )
    for _name, flow in flow_iter:
        if flow.P_Start in special_processes or hasattr(flow, "_fomp_protected"):
            continue

        process_logic = process_logic_map.get(flow.P_Start)
        tc_ids = flow_tc_map.get(flow.Name)

        # Pass-through processes don't need TCs, so allow them even without tc_ids
        if not process_logic:
            continue
        if not tc_ids and process_logic != "Pass-through":
            continue

        input_flows = [
            f for f in mfa_system.FlowDict.values() if f.P_End == flow.P_Start
        ]
        if not enhanced_input_validation(input_flows, dsm_processes):
            continue

        old_values = flow.Values.copy()
        total_inflow_vector = sum(f.Values for f in input_flows)
        outflow_vector = np.zeros_like(total_inflow_vector)

        # Get element indices dynamically
        elements = mfa_system.Elements
        mat_idx = 0  # Material is always first
        other_elements = elements[
            1:
        ]  # All other elements (WC, DM, CC or Fe, Cu, Al, etc.)
        elem_indices = {elem: idx for idx, elem in enumerate(elements)}

        if process_logic in ["Splitter", "Transformer", "Pass-through"]:
            if process_logic == "Splitter":
                # Splitter: Preserves composition (element fractions stay the same)
                param_name = tc_ids.get("material")
                if param_name and param_name in mfa_system.ParameterDict:
                    tc_value = mfa_system.ParameterDict[param_name].Values
                    outflow_vector[:, mat_idx] = (
                        total_inflow_vector[:, mat_idx] * tc_value
                    )

                    # Preserve composition for all elements
                    inflow_material = total_inflow_vector[:, mat_idx]

                    for element in other_elements:
                        elem_idx = elem_indices[element]

                        # Calculate fraction: element / material (avoid division by zero)
                        element_fraction = np.divide(
                            total_inflow_vector[:, elem_idx],
                            inflow_material,
                            out=np.zeros_like(inflow_material),
                            where=inflow_material != 0,
                        )

                        # Apply fraction to outflow material
                        outflow_vector[:, elem_idx] = (
                            outflow_vector[:, mat_idx] * element_fraction
                        )

            elif process_logic == "Pass-through":
                # Pass-through: Copy total inflow directly to outflow (no transformation)
                outflow_vector = total_inflow_vector.copy()

            elif process_logic == "Transformer":
                # Transformer: Changes composition (apply TCs to each element independently)
                for element in other_elements:
                    elem_idx = elem_indices[element]

                    # Look for element-specific TC, fallback to material TC
                    param_name = tc_ids.get(element, tc_ids.get("material"))

                    if param_name and param_name in mfa_system.ParameterDict:
                        tc_value = mfa_system.ParameterDict[param_name].Values
                        outflow_vector[:, elem_idx] = (
                            total_inflow_vector[:, elem_idx] * tc_value
                        )
                    else:
                        # No TC found, assume passthrough (no change)
                        outflow_vector[:, elem_idx] = total_inflow_vector[:, elem_idx]

                # Get element hierarchy (try config first, then mfa_system)
                element_hierarchy = (
                    getattr(config, "Element_Hierarchy", {}) if config else {}
                )
                if not element_hierarchy:
                    element_hierarchy = getattr(mfa_system, "_element_hierarchy", {})

                # Recalculate total material as sum of TOP-LEVEL elements only
                # (excludes hierarchical elements like CC which is % of DM, not material)
                if element_hierarchy:
                    # Only sum elements with parent='material' or no parent
                    top_level_sum = np.zeros(len(total_inflow_vector))
                    for elem in other_elements:
                        # Find element info in hierarchy
                        elem_info = None
                        for eid, info in element_hierarchy.items():
                            if info["name"] == elem:
                                elem_info = info
                                break

                        # Sum only if it's a top-level element
                        parent = elem_info.get("parent") if elem_info else None
                        if not parent or parent == "material":
                            elem_idx = elem_indices[elem]
                            top_level_sum += outflow_vector[:, elem_idx]

                    outflow_vector[:, mat_idx] = top_level_sum
                else:
                    # Fallback: sum all elements (backward compatibility)
                    outflow_vector[:, mat_idx] = np.sum(outflow_vector[:, 1:], axis=1)

            flow.Values = outflow_vector
            if not np.allclose(old_values, flow.Values):
                something_changed = True
    return something_changed


def _calculate_dsm_flows(
    mfa_system, dsm_processes, dsm_params, iteration, flow_tc_map=None
):
    """Calculates all stocks and flows for Dynamic Stock Model (DSM) processes.

    For each DSM process with valid inputs, this function calls the core DSM
    engine to calculate stock evolution and outflows for the current iteration.

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        The MFA system object, which will be modified in place.
    dsm_processes : set
        A set of all process IDs that are defined as DSM processes.
    dsm_params : dict
        The configuration parameters for all DSM processes.
    iteration : int
        The current solver iteration number, used for debug printing.
    flow_tc_map : dict, optional
        Map from flow names to TC parameter names.

    Returns
    -------
    tuple
        A tuple containing:
        - something_changed (bool): True if any flow values were changed.
        - dsm_details (dict): Detailed results from the DSM calculation.
    """
    if flow_tc_map is None:
        flow_tc_map = {}
    something_changed = False
    dsm_details = {}
    for process_id in dsm_processes:
        inflows_to_dsm = [
            f for f in mfa_system.FlowDict.values() if f.P_End == process_id
        ]
        total_inflow_sum = sum(np.sum(f.Values) for f in inflows_to_dsm)

        # Also run when initial stock exists, even if no new inflows yet
        _stock_cfg = dsm_params.get(process_id, {}).get("stock_configuration", "Stock")
        if _stock_cfg in (
            "Stock_with_InitialStock_Cohort",
            "Stock_with_InitialStock_Decay",
        ):
            _s_chk = mfa_system.StockDict.get(f"S_{process_id}")
            _has_initial = _s_chk is not None and float(_s_chk.Values[0, 0]) > 0
        else:
            _has_initial = False

        is_ready = total_inflow_sum > 0 or _has_initial
        if not is_ready:
            continue

        outflow_flow_name = next(
            (f.Name for f in mfa_system.FlowDict.values() if f.P_Start == process_id),
            None,
        )
        if not outflow_flow_name:
            continue

        old_out_values = mfa_system.FlowDict[outflow_flow_name].Values.copy()

        mfa_system, dsm_details_single_run = dsm_model.calculate_dynamic_stock(
            mfa_system, {process_id: dsm_params[process_id]}, flow_tc_map=flow_tc_map
        )
        dsm_details.update(dsm_details_single_run)

        if not np.allclose(
            old_out_values, mfa_system.FlowDict[outflow_flow_name].Values
        ):
            something_changed = True
    return something_changed, dsm_details


def _calculate_fomp_flows(mfa_system, fomp_processes, fomp_params):
    """Calculates all stocks and flows for First-Order Mass Pool (FOMP) processes.

    For each FOMP process, this function dynamically calculates the input flow
    composition and then calls the core FOMP engine to calculate stock decay
    and outflows.

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        The MFA system object, which will be modified in place.
    fomp_processes : set
        A set of all process IDs that are defined as FOMP processes.
    fomp_params : dict
        The configuration parameters for all FOMP processes.

    Returns
    -------
    tuple (bool, dict)
        (something_changed, fomp_details) where fomp_details is keyed by
        process_id and contains per-pool time-series arrays:
        'stock_labile', 'stock_recalcitrant', 'stock_tc_labile',
        'stock_tc_recalcitrant'.
    """
    # Check if required elements exist for FOMP
    # Accept "TC" (new hierarchy with TC/TOC/TIC) or "CC" (legacy naming)
    _tc_name = next((e for e in ("TC", "CC") if e in mfa_system.Elements), None)
    missing_elements = ["DM"] if "DM" not in mfa_system.Elements else []
    if _tc_name is None:
        missing_elements.append("TC or CC")

    if missing_elements:
        print(
            f"⚠️  FOMP calculation skipped: Missing required elements {missing_elements}"
        )
        print(
            "   FOMP requires 'DM' (dry matter) and 'TC' or 'CC' (carbon content) for organic decomposition"
        )
        print(f"   Available elements: {mfa_system.Elements}")
        print(
            "   Tip: For non-organic systems (e.g., metals), disable FOMP in configuration"
        )
        return False, {}  # No changes made

    something_changed = False
    fomp_details = {}
    for process_id in fomp_processes:
        inflows_to_fomp = [
            f for f in mfa_system.FlowDict.values() if f.P_End == process_id
        ]
        if not (
            inflows_to_fomp and all(np.any(f.Values != 0) for f in inflows_to_fomp)
        ):
            continue

        fomp_outflows = [
            f
            for f in mfa_system.FlowDict.values()
            if f.P_Start == process_id and hasattr(f, "_fomp_protected")
        ]
        old_fomp_out_values = {f.Name: f.Values.copy() for f in fomp_outflows}

        total_inflow_values = sum(f.Values for f in inflows_to_fomp)

        # Element indices (already validated above)
        material_idx = mfa_system.Elements.index("material")
        dm_idx = mfa_system.Elements.index("DM")
        cc_idx = mfa_system.Elements.index(_tc_name)  # "TC" or "CC"
        wc_idx = (
            mfa_system.Elements.index("WC") if "WC" in mfa_system.Elements else None
        )

        dm_fraction = np.divide(
            total_inflow_values[:, dm_idx],
            total_inflow_values[:, material_idx],
            out=np.zeros_like(total_inflow_values[:, dm_idx]),
            where=total_inflow_values[:, material_idx] != 0,
        )
        cc_fraction = np.divide(
            total_inflow_values[:, cc_idx],
            total_inflow_values[:, material_idx],
            out=np.zeros_like(total_inflow_values[:, cc_idx]),
            where=total_inflow_values[:, material_idx] != 0,
        )

        print(f"   FOMP Process {process_id} - Input Flow Composition:")
        print(
            f"     DM fraction: {np.mean(dm_fraction[dm_fraction > 0]):.3f} (range: {np.min(dm_fraction):.3f} - {np.max(dm_fraction):.3f})"
        )
        print(
            f"     {_tc_name} fraction: {np.mean(cc_fraction[cc_fraction > 0]):.3f} (range: {np.min(cc_fraction):.3f} - {np.max(cc_fraction):.3f})"
        )

        # Build composition dictionary — use the actual element name ("TC" or "CC")
        # so callers can look up carbon content by element name consistently.
        composition = {"DM": dm_fraction, _tc_name: cc_fraction}

        # Add WC if available
        if wc_idx is not None:
            wc_fraction = np.divide(
                total_inflow_values[:, wc_idx],
                total_inflow_values[:, material_idx],
                out=np.zeros_like(total_inflow_values[:, wc_idx]),
                where=total_inflow_values[:, material_idx] != 0,
            )
            composition["WC"] = wc_fraction
            print(
                f"     WC fraction: {np.mean(wc_fraction[wc_fraction > 0]):.3f} (range: {np.min(wc_fraction):.3f} - {np.max(wc_fraction):.3f})"
            )

        mfa_system, proc_pool_data = fomp_model.calculate_fomp(
            mfa_system, {process_id: fomp_params[process_id]}, composition
        )
        fomp_details[process_id] = {
            "stock_labile": proc_pool_data["stock_labile"],
            "stock_recalcitrant": proc_pool_data["stock_recalcitrant"],
            "stock_tc_labile": proc_pool_data["stock_tc_labile"],
            "stock_tc_recalcitrant": proc_pool_data["stock_tc_recalcitrant"],
            "decay_tc_labile": proc_pool_data["decay_tc_labile"],
            "decay_tc_recalcitrant": proc_pool_data["decay_tc_recalcitrant"],
        }

        for out_flow in fomp_outflows:
            if out_flow.Name in old_fomp_out_values and not np.allclose(
                old_fomp_out_values[out_flow.Name], out_flow.Values
            ):
                something_changed = True
                break
    return something_changed, fomp_details


def _calculate_lfg_flows(mfa_system, lfg_processes, lfg_params):
    """Calculates all output flows for Landfill Gas (LFG) processes.

    For each LFG process, reads waste inflows from the MFA system and calls
    the LFG engine to calculate CH4, CO2, and leachate output flows.

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        The MFA system object, modified in place.
    lfg_processes : set
        Set of process IDs that are defined as LFG processes.
    lfg_params : dict
        Configuration parameters for all LFG processes.

    Returns
    -------
    bool
        True if any flow values changed, False otherwise.
    """
    if not lfg_processes:
        return False

    something_changed = False
    for process_id in lfg_processes:
        if process_id not in lfg_params:
            continue

        inflows_to_lfg = [
            f for f in mfa_system.FlowDict.values() if f.P_End == process_id
        ]
        if not (inflows_to_lfg and all(np.any(f.Values != 0) for f in inflows_to_lfg)):
            continue

        # Capture current outflow values for change detection
        lfg_outflow_ids = [
            lfg_params[process_id].get("outflow_ch4_id"),
            lfg_params[process_id].get("outflow_co2_id"),
            lfg_params[process_id].get("outflow_leachate_id"),
        ]
        old_values = {
            fid: mfa_system.FlowDict[fid].Values.copy()
            for fid in lfg_outflow_ids
            if fid and fid in mfa_system.FlowDict
        }

        print(f"   LFG Process {process_id}:")
        mfa_system = lfg_model.calculate_lfg(
            mfa_system, {process_id: lfg_params[process_id]}
        )

        # Mark LFG outputs as protected so TC solver skips them
        for fid in lfg_outflow_ids:
            if fid and fid in mfa_system.FlowDict:
                mfa_system.FlowDict[fid]._lfg_protected = True

        # Detect change
        for fid, old_val in old_values.items():
            if fid in mfa_system.FlowDict and not np.allclose(
                old_val, mfa_system.FlowDict[fid].Values
            ):
                something_changed = True
                break

    return something_changed


def run_mfa_calculation(
    mfa_system_setup,
    dsm_params,
    fomp_params,
    config,
    flow_tc_map=None,
    process_logic_map=None,
    tc_updates=None,
    flow_updates=None,
    lfg_params=None,
    bom_params=None,
    flow_cap_params=None,
):
    """This function is the iterative solver for the MFA system.



    It repeatedly cycles through all process types (TC-driven, DSM, FOMP)

    in a single integrated loop, allowing dependencies between different

    model types to resolve. The system is considered converged when a full

    pass over all calculations results in no changes to any flow values.



    Parameters

    ----------

    mfa_system_setup : odym.MFAsystem

        A fully configured but unsolved MFA system.

    dsm_params : dict

        Configuration dictionary for DSM processes.

    fomp_params : dict

        Configuration dictionary for FOMP processes.

    config : object

        The configuration object with global settings (e.g., RUN_DSM_CALCULATION).

    flow_tc_map : dict

        A dictionary mapping Flow_IDs to their TC_ID names.

    process_logic_map : dict

        A dictionary mapping Process_IDs to their logic ('Splitter' or 'Transformer').

    tc_updates : dict, optional

        Sampled TC values for a Monte Carlo run. Values may be scalars (applied
        to the full time axis) or dicts with keys ``value``, ``start_year``,
        ``end_year`` for year-windowed dynamic-TC perturbations. Default None.

    flow_updates : dict, optional

        Flow modifications for a Monte Carlo run. Keys are Flow_IDs (e.g.
        ``"F_0_2"``). Each value is a dict with keys:
        ``value`` (float), ``operation`` (``"multiply"``/``"add"``/``"set"``),
        and optional ``start_year``/``end_year`` (int). Only the material
        column (index 0) is modified; element propagation runs as normal.
        Default None.



    Returns

    -------

    tuple

        A tuple containing:

        - mfa_system (odym.MFAsystem): The solved MFA system with all values calculated.

        - dsm_details (dict): Detailed results from the DSM calculations.

    """
    mfa_system = copy.deepcopy(mfa_system_setup)

    if tc_updates:
        time_items_tc = mfa_system.IndexTable.Classification["Time"].Items
        time_arr_tc = np.array(time_items_tc)
        for param_name, new_value in tc_updates.items():
            if param_name not in mfa_system.ParameterDict:
                continue
            if isinstance(new_value, dict):
                # Year-windowed dynamic-TC update
                val = new_value["value"]
                start_y = new_value.get("start_year")
                end_y = new_value.get("end_year")
                mask = np.ones(len(time_arr_tc), dtype=bool)
                if start_y is not None:
                    mask &= time_arr_tc >= start_y
                if end_y is not None:
                    mask &= time_arr_tc <= end_y
                mfa_system.ParameterDict[param_name].Values[mask] = val
            else:
                mfa_system.ParameterDict[param_name].Values = new_value

    if flow_updates:
        time_items_f = mfa_system.IndexTable.Classification["Time"].Items
        time_arr_f = np.array(time_items_f)
        for flow_name, upd in flow_updates:
            if flow_name not in mfa_system.FlowDict:
                continue  # pre-flight check in run_mc_simulation() already reported this
            val = upd["value"]
            op = upd.get("operation", "multiply")
            start_y = upd.get("start_year")
            end_y = upd.get("end_year")
            mask = np.ones(len(time_arr_f), dtype=bool)
            if start_y is not None:
                mask &= time_arr_f >= start_y
            if end_y is not None:
                mask &= time_arr_f <= end_y
            flow_vals = mfa_system.FlowDict[flow_name].Values
            n_elem = flow_vals.shape[1]
            if op == "multiply":
                flow_vals[mask, :] *= val
            elif op == "add":
                old_mat = flow_vals[mask, 0].copy()
                flow_vals[mask, 0] += val
                if n_elem > 1:
                    ratio = np.where(old_mat > 0, flow_vals[mask, 0] / old_mat, 1.0)
                    for e in range(1, n_elem):
                        flow_vals[mask, e] *= ratio
            elif op == "set":
                old_mat = flow_vals[mask, 0].copy()
                flow_vals[mask, 0] = val
                if n_elem > 1:
                    ratio = np.where(old_mat > 0, flow_vals[mask, 0] / old_mat, 1.0)
                    for e in range(1, n_elem):
                        flow_vals[mask, e] *= ratio

    if lfg_params is None:
        lfg_params = {}
    if bom_params is None:
        bom_params = {}
    if flow_cap_params is None:
        flow_cap_params = {}

    dsm_details = {}
    fomp_details = {}
    dsm_processes = set(dsm_params.keys())
    fomp_processes = set(fomp_params.keys())
    lfg_processes = set(lfg_params.keys())
    bom_processes = set(bom_params.keys())
    flow_cap_processes = set(flow_cap_params.keys())

    # Cross-check against process_logic_map so that the Excel Process_Logic
    # column acts as the authoritative switch.  DSM is already filtered at
    # load time (load_dsm_parameters filters by Process_Logic == "DSM");
    # FOMP, LFG, BOM_Assembler, and FlowCap are loaded from their dedicated
    # sheets without that filter, so we apply it here.
    if process_logic_map:
        fomp_processes = {
            pid for pid in fomp_processes if process_logic_map.get(pid) == "FOMP"
        }
        lfg_processes = {
            pid for pid in lfg_processes if process_logic_map.get(pid) == "LFG"
        }
        bom_processes = {
            pid
            for pid in bom_processes
            if process_logic_map.get(pid) == "BOM_Assembler"
        }
        flow_cap_processes = {
            pid for pid in flow_cap_processes if process_logic_map.get(pid) == "FlowCap"
        }

    special_processes = (
        dsm_processes.union(fomp_processes)
        .union(lfg_processes)
        .union(bom_processes)
        .union(flow_cap_processes)
    )

    # Pre-sort flows in topological order so upstream flows are calculated
    # before downstream flows within each pass. This reduces the number of
    # iterations needed for convergence from O(chain_depth) to O(1).
    sorted_flow_names = _topological_sort_flows(mfa_system)
    print(
        f"--> Flow dependency graph sorted ({len(sorted_flow_names)} flows in topological order)."
    )

    max_iterations = 30  # Safeguard against infinite loops
    convergence_log = []
    converged = False

    for i in range(max_iterations):
        pass_changes = []

        # --- 1. TC-driven, DSM, and FOMP flows ---
        tc_changed = _calculate_tc_driven_flows(
            mfa_system,
            special_processes,
            process_logic_map,
            flow_tc_map,
            dsm_processes,
            config,
            sorted_flow_names=sorted_flow_names,
        )
        pass_changes.append(tc_changed)

        dsm_changed = False
        if config.RUN_DSM_CALCULATION:
            dsm_changed, dsm_run_details = _calculate_dsm_flows(
                mfa_system, dsm_processes, dsm_params, i, flow_tc_map
            )
            dsm_details.update(dsm_run_details)
            pass_changes.append(dsm_changed)

        fomp_changed = False
        if config.RUN_FOMP_CALCULATION:
            fomp_changed, fomp_run_details = _calculate_fomp_flows(
                mfa_system, fomp_processes, fomp_params
            )
            fomp_details.update(fomp_run_details)
            pass_changes.append(fomp_changed)

        lfg_changed = False
        if getattr(config, "RUN_LFG_CALCULATION", True) and lfg_processes:
            lfg_changed = _calculate_lfg_flows(mfa_system, lfg_processes, lfg_params)
            pass_changes.append(lfg_changed)

        # --- 2.5. BOM Assembler processes ---
        bom_changed = False
        if bom_processes:
            element_hierarchy = getattr(mfa_system, "_element_hierarchy", None)
            bom_changed = _bom_assembler.calculate_bom_assembly(
                mfa_system, bom_processes, bom_params, element_hierarchy
            )
            pass_changes.append(bom_changed)

        # --- 2.6. FlowCap processes ---
        flow_cap_changed = False
        if flow_cap_processes:
            flow_cap_changed = _flow_cap.calculate_flow_cap(
                mfa_system, flow_cap_processes, flow_cap_params
            )
            pass_changes.append(flow_cap_changed)

        # Record per-iteration diagnostics
        convergence_log.append(
            {
                "iteration": i + 1,
                "tc_changed": bool(tc_changed),
                "dsm_changed": bool(dsm_changed),
                "fomp_changed": bool(fomp_changed),
                "lfg_changed": bool(lfg_changed),
                "bom_changed": bool(bom_changed),
                "flow_cap_changed": bool(flow_cap_changed),
                "any_changed": any(pass_changes),
            }
        )

        # --- Convergence Check ---
        if not any(pass_changes):
            converged = True
            print(f"--> System converged after {i + 1} iterations.")
            break
    else:
        print(
            f"⚠️ WARNING: System did not converge after {max_iterations} iterations. Results may be unstable."
        )

    solver_info = {
        "iterations": i + 1,
        "converged": converged,
        "max_iterations": max_iterations,
        "convergence_log": convergence_log,
        "method": "Fixed-point iteration",
        "fomp_details": fomp_details,
    }

    # --- Final balance calculation ---
    mfa_system = calculate_final_balances(
        mfa_system,
        dsm_processes,
        fomp_processes.union(lfg_processes)
        .union(bom_processes)
        .union(flow_cap_processes),
    )

    # ODYM validation after complete calculation
    try:
        mfa_system.Consistency_Check()
        print("✅ Final MFA system validation passed")
    except Exception as e:
        print(f"⚠️ Final validation warning: {e}")

    return mfa_system, dsm_details, solver_info
