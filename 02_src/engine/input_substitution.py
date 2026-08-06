# -*- coding: utf-8 -*-
"""
Input_Substitution Process Logic for the BioDYM Engine.

Input_Substitution is a drop-in variant of a plain Input process: its fixed
demand target comes from a normal ``flow_data`` time series on its own
boundary/residual outflow — same mechanism, same editor, same mental model
as Input. The only difference is that secondary/recycled supply routed back
into the process meets part of that demand first, and virgin extraction
(the boundary/residual outflow) only carries whatever demand the secondary
supply cannot cover.

Elements fall into three tiers:

  1. "material" — when it has top-level children present in this study
     (e.g. WC/DM under a WC+DM=material hierarchy), it is a *derived*
     bookkeeping total, not an independently-computed quantity (mirrors
     Transformer's own ``material`` recompute in ``solver.py``): excluded
     from direct balancing, recomputed afterward as the sum of its
     top-level children's own just-computed values. If "material" has no
     children in this study (a single-element study, e.g. the T17
     tutorial), it is treated as an ordinary directly-balanced element.

  2. Directly-driven elements — material's top-level children (WC, DM, ...)
     plus any deeper element that has its own real ``flow_data`` series on
     the residual/System-input flow (auto-inferred at load time, see
     ``load_input_substitution_from_yaml`` — e.g. TC in a carbon-tracking
     model, where TC is itself the real independently-tracked quantity).
     Each is balanced on its own terms, independent of every other element:

       consumed[e] = min(target[e], available_supply[e])
       residual[e] = target[e] - consumed[e]   (written into the residual
                                                outflow)
       surplus[e]  = available_supply[e] - consumed[e]   (optional)

  3. Passenger elements — everything else (a deeper element with no
     independent target of its own, e.g. Cu riding along with DM in a
     tramp-element-accumulation study). These never get their own min/
     target comparison; they ride along with their immediate parent's own
     consumed:supply ratio, preserving the supply's own composition:

       consumed[e] = supply[e] * (consumed[parent] / supply[parent])
       surplus[e]  = supply[e] - consumed[e]
       residual[e] = residual[parent] * own_composition_fraction[e]
                     (the residual/boundary flow's own ParameterDict
                     fraction, ``{element}_{flow.Name}`` — same convention
                     used for every other flow's one-time setup
                     composition cascade)

Getting tier 2 vs. 3 wrong for a given element produces exactly the class of
silently-wrong result this module's design has already been burned by once
(see 07_AI_Coding_Assistance/260720_Report_InputSubstitution_ReviewRequest.md):
treating a passenger element as directly driven when its target was never
independently meaningful (e.g. a contaminant fraction defaulting to 0) makes
it vanish from the substitution entirely, silently, however much of its
parent actually gets consumed.

An optional ``lag_years`` delays when returning supply counts toward demand:
with ``lag_years=1``, a flow returned in year t only offsets demand in year
t+1, not the same year. This also structurally removes any same-year
self-referential dependency between a process's own return-supply and its
own residual — a lagged supply term can never affect its own year's demand.

Design: see 07_AI_Coding_Assistance/260720_Plan_InputSubstitution.md.

Config: web-app YAML only in v1 (no Excel sheet). Per process:
  supply_flow_ids   [Flow_ID, ...] secondary/recycled inflows, summed
  consumed_flow_id  Flow_ID        substituted amount -> same to_process
                                    as the boundary/residual outflow
  surplus_flow_id   Flow_ID | None excess secondary supply beyond target
  residual_flow_id  Flow_ID | None the boundary/residual outflow itself;
                                    if blank, discovered as the sole other
                                    P_Start==process_id flow (back-compat
                                    with configs saved before this field
                                    existed)
  lag_years         int            years of delay before returning supply
                                    counts toward demand (default 0)

Not a config field: ``driven_elements`` is computed fresh by
``load_input_substitution_from_yaml`` on every load (not stored in the
YAML) — any element with its own ``flow_data`` entry on the residual flow
is driven; everything else is a passenger. There is deliberately no manual
override: which tier an element belongs to was previously also a
user-editable field, and giving an element "its own independent demand"
while leaving that demand unconfigured (defaulting to 0) is exactly the
silent-failure mode described below — the field was removed rather than
documented harder.

Its target series is whatever ``flow_data``/normal system setup already
populated onto the residual flow before the solver loop starts (captured on
first use, since this module overwrites the flow's values every iteration
thereafter).

In 2_1_Definition_Processes / config.yaml: Process_Logic = 'Input_Substitution',
                                            Stock_Configuration = 'No_Stock' or 'Stock'

With ``Stock``, the process self-reports its absolute stock (initial stock +
cumulative net flux) at the end of every call, the same way DSM/FOMP do. This
is required because ``solver.calculate_final_balances`` unions
Input_Substitution processes into its special-process skip list; without the
self-report the stock would stay flat at zero. On a boundary input the stock
runs negative and reads as cumulative virgin extraction.
"""

import numpy as np


# ---------------------------------------------------------------------------
# Public loader — called by data_loader.load_input_substitution_from_yaml()
# ---------------------------------------------------------------------------


def load_input_substitution_from_yaml(yaml_path: str) -> dict:
    """Load Input_Substitution configurations from a web-app config YAML.

    Parameters
    ----------
    yaml_path : str
        Path to the ``config.yaml`` produced by the BioDYM config web app.

    Returns
    -------
    dict
        Keys are process IDs (int). Values are config dicts:
        {
            "supply_flow_ids":  list[str],      # secondary/recycled inflows, summed
            "consumed_flow_id": str,
            "surplus_flow_id":  str | None,
            "residual_flow_id": str | None,
            "driven_elements":  list[str],      # auto-inferred, see below
            "lag_years":        int,
        }

    ``driven_elements`` is not a config field — it is auto-inferred here:
    any element (other than "material") with its own ``flow_data`` entry on
    the residual/System-input flow is treated as independently driven;
    everything else rides along with its parent as a passenger (see
    ``calculate_input_substitution``'s module docstring). This removes a
    GUI toggle that duplicated information already implied by whether a
    real target series was ever configured for that element.
    """
    import yaml as _yaml

    print(f"--> Loading Input_Substitution parameters from '{yaml_path}'...")
    with open(yaml_path, encoding="utf-8") as fh:
        data = _yaml.safe_load(fh) or {}

    all_flows = data.get("flows", []) or []
    all_flow_data = data.get("flow_data", []) or []

    substitution_params = {}
    for proc in data.get("processes", []):
        cfg = proc.get("input_substitution")
        if not cfg:
            continue
        pid = int(proc["id"])

        supply_flow_ids = [
            str(fid).strip()
            for fid in (cfg.get("supply_flow_ids") or [])
            if str(fid).strip()
        ]
        consumed_flow_id = str(cfg.get("consumed_flow_id", "") or "").strip()
        surplus_flow_id = str(cfg.get("surplus_flow_id", "") or "").strip() or None
        residual_flow_id = str(cfg.get("residual_flow_id", "") or "").strip() or None
        try:
            lag_years = int(cfg.get("lag_years", 0) or 0)
        except (TypeError, ValueError):
            lag_years = 0

        if not consumed_flow_id:
            print(
                f"    WARNING: Process {pid}: no 'consumed_flow_id' configured — skipping."
            )
            continue

        # Discover the residual/System-input flow if not named explicitly —
        # same "sole other P_Start==pid outflow" rule the engine and
        # consistency.input_substitution_residual_flow use — so
        # driven_elements can still be inferred for configs saved before
        # residual_flow_id existed.
        effective_residual_id = residual_flow_id
        if not effective_residual_id:
            claimed = {consumed_flow_id, surplus_flow_id}
            candidates = [
                f
                for f in all_flows
                if int(f.get("from_process", -1)) == pid and f.get("id") not in claimed
            ]
            if len(candidates) == 1:
                effective_residual_id = candidates[0].get("id")

        driven_elements = sorted(
            {
                str(fd.get("element", "")).strip()
                for fd in all_flow_data
                if fd.get("flow_id") == effective_residual_id
                and str(fd.get("element", "")).strip()
                and str(fd.get("element", "")).strip() != "material"
            }
        )

        substitution_params[pid] = {
            "supply_flow_ids": supply_flow_ids,
            "consumed_flow_id": consumed_flow_id,
            "surplus_flow_id": surplus_flow_id,
            "residual_flow_id": residual_flow_id,
            "driven_elements": driven_elements,
            "lag_years": lag_years,
        }
        print(
            f"    Loaded Input_Substitution for Process {pid}: "
            f"supply={supply_flow_ids}, consumed={consumed_flow_id}, "
            f"surplus={surplus_flow_id}, residual={residual_flow_id}, "
            f"driven_elements={driven_elements}, lag_years={lag_years}"
        )

    print(f"--> Input_Substitution: loaded {len(substitution_params)} process(es).")
    return substitution_params


# ---------------------------------------------------------------------------
# Calculation engine
# ---------------------------------------------------------------------------


def _top_level_child_indices(elements, hierarchy_map):
    """Indices of elements whose parent is "material" (or unspecified),
    excluding "material" itself — mirrors solver.py's Transformer branch,
    which recomputes ``material`` as the sum of exactly these columns."""
    indices = []
    for i, name in enumerate(elements):
        if name == "material":
            continue
        parent = (hierarchy_map.get(name, {}) or {}).get("parent")
        if not parent or parent == "material":
            indices.append(i)
    return indices


def calculate_input_substitution(
    mfa_system, substitution_processes, substitution_params, element_hierarchy=None
):
    """Apply demand-substitution routing to all Input_Substitution processes.

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        Modified in place.
    substitution_processes : set of int
        Process IDs active as Input_Substitution (already filtered by process_logic_map).
    substitution_params : dict
        As returned by load_input_substitution_from_yaml().
    element_hierarchy : dict, optional
        {element_id: {'name': str, 'parent': str or None}} — used to decide
        which elements are top-level (material's children), which are
        deeper "passenger" elements, and who each passenger's immediate
        parent is.

    Returns
    -------
    bool
        True if any flow value changed from the previous iteration.
    """
    something_changed = False

    elements = mfa_system.Elements
    num_elements = len(elements)
    mat_idx = elements.index("material") if "material" in elements else None
    hierarchy_map = {}
    if element_hierarchy:
        for elem_info in element_hierarchy.values():
            hierarchy_map[elem_info["name"]] = elem_info
    top_level_idx = _top_level_child_indices(elements, hierarchy_map) if mat_idx is not None else []
    material_is_derived = mat_idx is not None and len(top_level_idx) > 0

    for process_id in substitution_processes:
        params = substitution_params[process_id]

        consumed_id = params.get("consumed_flow_id")
        surplus_id = params.get("surplus_flow_id")
        residual_id = params.get("residual_flow_id")

        if not consumed_id or consumed_id not in mfa_system.FlowDict:
            print(
                f"  WARNING: Input_Substitution Process {process_id}: "
                f"consumed flow '{consumed_id}' not found in FlowDict — skipping."
            )
            continue

        if residual_id:
            boundary_flow = mfa_system.FlowDict.get(residual_id)
            if boundary_flow is None:
                print(
                    f"  WARNING: Input_Substitution Process {process_id}: "
                    f"residual flow '{residual_id}' not found in FlowDict — skipping."
                )
                continue
        else:
            # Back-compat: no residual_flow_id configured — discover the
            # boundary outflow as the sole P_Start==process_id flow not
            # already claimed by consumed_flow_id/surplus_flow_id.
            claimed = {consumed_id, surplus_id}
            boundary_candidates = [
                f
                for f in mfa_system.FlowDict.values()
                if f.P_Start == process_id and f.Name not in claimed
            ]
            if len(boundary_candidates) != 1:
                print(
                    f"  WARNING: Input_Substitution Process {process_id}: expected exactly "
                    f"one boundary outflow (P_Start={process_id}, excluding consumed/surplus), "
                    f"found {len(boundary_candidates)} — skipping."
                )
                continue
            boundary_flow = boundary_candidates[0]

        consumed_flow = mfa_system.FlowDict[consumed_id]
        num_years, _ = boundary_flow.Values.shape

        # The target series is whatever flow_data/system setup already put on
        # this flow — every element column, not just "material" — same as a
        # plain Input flow. Capture it once (this module overwrites the
        # flow's values on every subsequent call), scoped to this solve via a
        # plain attribute on the deep-copied per-run mfa_system, so it can
        # never leak across runs (mirrors the _lfg_protected/_fomp_protected/
        # _spare_protected pattern).
        if not hasattr(boundary_flow, "_is_target_cache"):
            boundary_flow._is_target_cache = boundary_flow.Values.copy()
        target_values = boundary_flow._is_target_cache

        # Only genuine inflows (P_End == this process) count as supply. Without
        # this check a misconfigured supply_flow_ids entry can silently point
        # at the process's own outflow (or any unrelated flow) and, if it's
        # the boundary flow itself, create a self-referential feedback loop
        # that oscillates forever instead of converging (found the hard way —
        # see 260720_Plan_InputSubstitution.md §8/§9).
        supply_flow_ids = params.get("supply_flow_ids") or []
        supply_flows = []
        for fid in supply_flow_ids:
            flow_obj = mfa_system.FlowDict.get(fid)
            if flow_obj is None:
                print(
                    f"  WARNING: Input_Substitution Process {process_id}: "
                    f"supply flow '{fid}' not found in FlowDict — skipping."
                )
                continue
            if flow_obj.P_End != process_id:
                print(
                    f"  WARNING: Input_Substitution Process {process_id}: "
                    f"supply flow '{fid}' is not an inflow of this process "
                    f"(P_End={flow_obj.P_End}, expected {process_id}) — skipping. "
                    f"A process's own outflow cannot be its own supply."
                )
                continue
            supply_flows.append(flow_obj)
        if supply_flows:
            supply_total = sum(f.Values for f in supply_flows)
        else:
            supply_total = np.zeros((num_years, num_elements))

        lag_years = int(params.get("lag_years", 0) or 0)
        if lag_years > 0:
            supply_lagged = np.zeros_like(supply_total)
            if lag_years < num_years:
                supply_lagged[lag_years:] = supply_total[: num_years - lag_years]
        else:
            supply_lagged = supply_total

        # --- tier assignment: driven vs. derived-material vs. passenger ---
        explicit_driven_names = set(params.get("driven_elements") or [])
        driven_idx = set(top_level_idx)
        if mat_idx is not None and not material_is_derived:
            driven_idx.add(mat_idx)
        for i, name in enumerate(elements):
            if name in explicit_driven_names and (mat_idx is None or i != mat_idx):
                driven_idx.add(i)
        passenger_idx = [
            i for i in range(num_elements)
            if i not in driven_idx and (mat_idx is None or i != mat_idx)
        ]

        if not hasattr(boundary_flow, "_is_derivation_logged"):
            boundary_flow._is_derivation_logged = True
            driven_names = [elements[i] for i in sorted(driven_idx)]
            passenger_names = [elements[i] for i in passenger_idx]
            msg = f"    Input_Substitution P{process_id}: driven={driven_names}"
            if material_is_derived:
                msg += f", 'material' = sum({[elements[i] for i in top_level_idx]})"
            if passenger_names:
                msg += f", passengers={passenger_names} (ride along with their parent)"
            print(msg)

        consumed_values = np.zeros((num_years, num_elements))
        residual_values = np.zeros((num_years, num_elements))
        surplus_values = np.zeros((num_years, num_elements))

        # 1. Directly-driven elements: independent elementwise balance.
        for i in driven_idx:
            consumed_values[:, i] = np.minimum(target_values[:, i], supply_lagged[:, i])
            residual_values[:, i] = target_values[:, i] - consumed_values[:, i]
            surplus_values[:, i] = supply_lagged[:, i] - consumed_values[:, i]

        # 2. "material" (when derived): sum of its top-level children's own
        # just-computed values — mirrors Transformer's own recompute.
        if material_is_derived:
            consumed_values[:, mat_idx] = consumed_values[:, top_level_idx].sum(axis=1)
            residual_values[:, mat_idx] = residual_values[:, top_level_idx].sum(axis=1)
            surplus_values[:, mat_idx] = surplus_values[:, top_level_idx].sum(axis=1)

        # 3. Passenger elements: ride along with their immediate parent —
        # never independently target-capped. consumed/surplus preserve the
        # supply's own composition (scaled by how much of the parent was
        # actually consumed); residual comes from the boundary/residual
        # flow's own composition fraction, same ParameterDict convention
        # every flow's one-time setup composition cascade already uses.
        for i in passenger_idx:
            name = elements[i]
            parent_name = (hierarchy_map.get(name, {}) or {}).get("parent") or "material"
            if parent_name not in elements:
                continue
            parent_idx = elements.index(parent_name)
            supply_parent = supply_lagged[:, parent_idx]
            safe_parent = np.where(supply_parent != 0, supply_parent, 1.0)
            consumed_ratio = np.where(
                supply_parent != 0, consumed_values[:, parent_idx] / safe_parent, 0.0
            )
            consumed_values[:, i] = supply_lagged[:, i] * consumed_ratio
            surplus_values[:, i] = supply_lagged[:, i] - consumed_values[:, i]

            param = mfa_system.ParameterDict.get(f"{name}_{boundary_flow.Name}")
            if param is not None:
                residual_values[:, i] = residual_values[:, parent_idx] * param.Values
            # else: no fraction configured for this passenger on the
            # residual flow — leave it at 0, same as the one-time setup
            # composition cascade would for an unconfigured element.

        # --- consumed_flow_id ---
        old_consumed = consumed_flow.Values.copy()
        consumed_flow.Values[:, :] = consumed_values
        if not np.allclose(old_consumed, consumed_flow.Values):
            something_changed = True

        # --- boundary/residual outflow (virgin material still needed) ---
        old_boundary = boundary_flow.Values.copy()
        boundary_flow.Values[:, :] = residual_values
        if not np.allclose(old_boundary, boundary_flow.Values):
            something_changed = True

        # --- surplus_flow_id (optional) ---
        if surplus_id and surplus_id in mfa_system.FlowDict:
            surplus_flow = mfa_system.FlowDict[surplus_id]
            old_surplus = surplus_flow.Values.copy()
            surplus_flow.Values[:, :] = surplus_values
            if not np.allclose(old_surplus, surplus_flow.Values):
                something_changed = True
        elif surplus_id:
            print(
                f"  WARNING: Input_Substitution Process {process_id}: "
                f"surplus flow '{surplus_id}' not found in FlowDict."
            )

        # --- stock self-reporting ---
        # Input_Substitution processes are unioned into calculate_final_balances'
        # special_processes, which skips the generic dS = inflow - outflow pass
        # (correct for DSM/FOMP/LFG, which write their own absolute stocks). This
        # module writes none, so without the block below a substitution process
        # configured with Stock reports a flat zero forever — silently erasing
        # the cumulative virgin-extraction figure that is the whole point of
        # running one of these on a boundary input. Mirrors the DSM/FOMP
        # convention: write the absolute stock, let the balance pass derive dS.
        stock = mfa_system.StockDict.get(f"S_{process_id}")
        if stock is not None and stock.Values is not None:
            # Capture the configured initial stock once. This runs every solver
            # iteration, so re-reading Values[0] each time would fold the
            # already-written year-0 balance back in as a fresh initial stock
            # and compound it away from any fixed point. Scoped to the
            # deep-copied per-run mfa_system, like _is_target_cache above.
            if not hasattr(stock, "_is_initial_stock_cache"):
                stock._is_initial_stock_cache = stock.Values[0, :].copy()
            initial_stock = stock._is_initial_stock_cache

            inflow_sum = sum(
                (f.Values for f in mfa_system.FlowDict.values() if f.P_End == process_id),
                np.zeros_like(stock.Values),
            )
            outflow_sum = sum(
                (f.Values for f in mfa_system.FlowDict.values() if f.P_Start == process_id),
                np.zeros_like(stock.Values),
            )
            new_stock = initial_stock + np.cumsum(inflow_sum - outflow_sum, axis=0)
            if not np.allclose(stock.Values, new_stock):
                stock.Values = new_stock
                something_changed = True

    return something_changed
