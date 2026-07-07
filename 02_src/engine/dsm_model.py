# -*- coding: utf-8 -*-
"""
Dynamic Stock Model (DSM) Module for the BioDYM Engine.

This file contains the specific calculation logic for processes that are
modeled as dynamic stocks, where outflows are determined by the age
structure of the stock and a lifetime distribution.

Mathematical notation (see bioDYM_mathematical_formulas.md §5-6):
    Paper symbol      Code variable
    α_i           ←→  inflow_split[i]      (category inflow split)
    μ_i, σ_i      ←→  lifetimes["Mean"/"StdDev"][i]
    κ, λ          ←→  lifetimes["Shape"/"Scale"][i]   (Weibull)
    s_c[t,t0]     ←→  s_c   (ODYM cohort stock matrix)
    o_c[t,t0]     ←→  o_c   (ODYM cohort outflow matrix)
    comp[t0,e]    ←→  comp  (vintage element composition)
    sf(t)         ←→  compute_sf()[:,0]   (initial-stock survival, Method A)
"""

import numpy as np
import scipy.special
import scipy.optimize
import dynamic_stock_model as dsm
from .element_utils import recalculate_hierarchical_elements


# ODYM's DynamicStockModel matches lifetime types by exact string ("Fixed",
# "Normal", "FoldedNormal", "LogNormal", "Weibull"). Earlier code used
# str.capitalize(), which silently turned "LogNormal" → "Lognormal" — a value
# ODYM never matches, so the survival function stayed zero. Normalise to the
# canonical spelling instead, preserving the embedded capital letters.
_DSM_LIFETIME_TYPES = {
    "fixed": "Fixed",
    "normal": "Normal",
    "foldednormal": "FoldedNormal",
    "lognormal": "LogNormal",
    "weibull": "Weibull",
}


def _canon_lifetime_type(name, default="Normal"):
    """Map any user/Excel spelling to ODYM's canonical lifetime-type string."""
    if not isinstance(name, str) or not name.strip():
        return default
    return _DSM_LIFETIME_TYPES.get(name.strip().lower(), name.strip())


def _weibull_shape_scale_from_mean_std(mean, std):
    """Derive Weibull shape k and scale λ from distribution mean and std.

    Solves Γ(1+2/k)/Γ(1+1/k)² - 1 = (std/mean)² numerically via brentq,
    then computes λ = mean / Γ(1+1/k).

    Returns (k=0, λ=mean) on failure — caller should fall back to Fixed lifetime.
    """
    if mean <= 0:
        return 0.0, 0.0
    if std <= 0:
        return 0.0, mean  # degenerate — signal Fixed
    cov_sq = (std / mean) ** 2

    def _eq(k):
        g1 = scipy.special.gamma(1.0 + 1.0 / k)
        g2 = scipy.special.gamma(1.0 + 2.0 / k)
        return g2 / (g1 * g1) - 1.0 - cov_sq

    try:
        k = scipy.optimize.brentq(_eq, 0.1, 200.0)
        lam = mean / scipy.special.gamma(1.0 + 1.0 / k)
        return float(k), float(lam)
    except ValueError:
        return 0.0, float(mean)


def _build_category_lt_dict(params, i):
    """Build the ODYM lifetime dict for DSM category ``i``.

    Shared by the inflow-driven cohort calculation and the initial-stock
    survival calculation, so both always decay with the same distribution.
    """
    lt_params = params.get("lifetimes", {})
    mean_lifetimes = lt_params.get("Mean", [])
    std_devs = lt_params.get("StdDev", [0] * len(mean_lifetimes))

    lifetime_type = lt_params.get("Type")
    lifetime_type = (
        lifetime_type[i] if isinstance(lifetime_type, list) else lifetime_type
    )
    lifetime_type = _canon_lifetime_type(lifetime_type)

    if std_devs[i] == 0 and lifetime_type not in ("Weibull", "Fixed"):
        print(
            f"  INFO: StdDev is 0 for category {i + 1}. Using 'Fixed' lifetime model instead of '{lifetime_type}'."
        )
        lifetime_type = "Fixed"

    if lifetime_type == "Weibull":
        # ODYM Weibull needs Shape (k) and Scale (λ), not Mean/StdDev.
        shape_list = lt_params.get("Shape", [])
        scale_list = lt_params.get("Scale", [])
        shape_val = (
            shape_list[i]
            if i < len(shape_list) and shape_list[i] is not None
            else None
        )
        scale_val = (
            scale_list[i]
            if i < len(scale_list) and scale_list[i] is not None
            else None
        )

        if shape_val is not None and scale_val is not None:
            print(f"  Weibull: Shape(k)={shape_val}, Scale(λ)={scale_val}")
            return {
                "Type": "Weibull",
                "Shape": np.array([float(shape_val)]),
                "Scale": np.array([float(scale_val)]),
            }
        # Derive from Mean/StdDev via moment matching
        k, lam = _weibull_shape_scale_from_mean_std(mean_lifetimes[i], std_devs[i])
        if k > 0:
            print(
                f"  Weibull: derived Shape(k)={k:.4f}, Scale(λ)={lam:.4f} "
                f"from Mean={mean_lifetimes[i]}, StdDev={std_devs[i]}"
            )
            return {
                "Type": "Weibull",
                "Shape": np.array([k]),
                "Scale": np.array([lam]),
            }
        print(
            f"  WARNING: Weibull moment-matching failed for Mean={mean_lifetimes[i]}, "
            f"StdDev={std_devs[i]} — falling back to Fixed lifetime"
        )
        return {"Type": "Fixed", "Mean": np.array([mean_lifetimes[i]])}

    return {
        "Type": lifetime_type,
        "Mean": np.array([mean_lifetimes[i]]),
        "StdDev": np.array([std_devs[i]]),
    }


def _calculate_outflow_from_inflows(total_inflow_values, params, time_vector):
    """Calculate the stock and outflow generated from new inflows for all categories.

    Uses cohort-matrix vintage weighting: the DSM is run once per category on the
    material inflow, producing cohort matrices s_c[t, t0] and o_c[t, t0]. A
    composition matrix comp[t0, elem] captures the element fractions at each
    installation year t0. Element-wise stock and outflow are then obtained by the
    matrix product:

        stock_cat  = s_c @ comp   # (T×T) @ (T×E) = (T×E)
        outflow_cat = o_c @ comp

    This ensures that a cohort installed in year t0 always carries the element
    composition of year t0, regardless of when it retires.

    Parameters
    ----------
    total_inflow_values : np.ndarray, shape (num_years, num_elements)
        Total inflow values over time for all elements.
    params : dict
        DSM parameter configuration for the specific process.
    time_vector : np.ndarray
        Array of years for the model run.

    Returns
    -------
    tuple
        - stock_from_inflows_by_cat (list): List of (num_years, num_elements) arrays.
        - outflow_from_inflows_by_cat (list): List of (num_years, num_elements) arrays.
    """
    outflow_from_inflows_by_cat = []
    stock_from_inflows_by_cat = []
    num_years = len(time_vector)
    num_elements = total_inflow_values.shape[1]

    inflow_split = params.get("inflow_split", [1.0])

    for i in range(len(inflow_split)):
        print(
            f"\n--- Processing Category {i + 1} ({params.get('category_names', [f'Category_{i + 1}'])[i]}) ---"
        )
        inflow_material = total_inflow_values[:, 0] * inflow_split[i]
        print(f"Inflow category {i + 1}: {inflow_material[:5]}... (first 5 years)")

        lt_dict = _build_category_lt_dict(params, i)

        # Run DSM on material inflow — retain full cohort matrices (T×T)
        dsm_model_instance = dsm.DynamicStockModel(
            t=time_vector, i=inflow_material, lt=lt_dict
        )
        s_c = dsm_model_instance.compute_s_c_inflow_driven()  # (T, T)
        o_c = dsm_model_instance.compute_o_c_from_s_c()  # (T, T)

        # Build composition matrix comp[t0, elem] = element fraction at installation year t0
        # Row t0 describes the composition of material entering in year t0.
        # Forward-fill: if no inflow in year t0, use last known composition.
        comp = np.zeros((num_years, num_elements))
        comp[:, 0] = 1.0  # material fraction is always 1
        for elem_idx in range(1, num_elements):
            elem_inflow = total_inflow_values[:, elem_idx] * inflow_split[i]
            with np.errstate(divide="ignore", invalid="ignore"):
                frac = np.where(inflow_material > 0, elem_inflow / inflow_material, 0.0)
            last = 0.0
            for t0 in range(num_years):
                if inflow_material[t0] > 0:
                    last = frac[t0]
                else:
                    frac[t0] = last
            comp[:, elem_idx] = frac

        # Vintage-weighted element arrays via matrix multiply: (T,T) @ (T,E) = (T,E)
        stock_cat = (
            s_c @ comp if s_c is not None else np.zeros((num_years, num_elements))
        )
        outflow_cat = (
            o_c @ comp if o_c is not None else np.zeros((num_years, num_elements))
        )

        stock_from_inflows_by_cat.append(stock_cat)
        outflow_from_inflows_by_cat.append(outflow_cat)

    return stock_from_inflows_by_cat, outflow_from_inflows_by_cat


def _calculate_outflow_from_initial_stock(
    initial_stock_vector, params, num_years, num_elements, time_vector
):
    """Calculate the stock decay and outflow generated from the initial stock.

    The initial stock is treated as a single cohort installed at t=0 that
    decays along the same lifetime distribution(s) as new inflows: one ODYM
    survival function per DSM category, weighted by ``inflow_split``.

    The former implementation used fixed-rate exponential decay with
    k = 1/mean(lifetimes), which is exact only for exponential lifetime
    distributions (Fix 4 of the mathematical validation review).

    Parameters
    ----------
    initial_stock_vector : np.ndarray
        An array representing the initial stock for all elements.
    params : dict
        DSM parameter configuration (lifetimes + inflow_split) — the same
        dict used for the inflow-driven cohorts.
    num_years : int
        The number of years in the simulation.
    num_elements : int
        The number of elements being tracked.
    time_vector : np.ndarray
        Array of years for the model run.

    Returns
    -------
    tuple
        A tuple containing:
        - decaying_stock_ts (np.ndarray): Time series of the decaying initial stock.
        - outflow_from_initial_stock_ts (np.ndarray): Time series of the outflow from the initial stock.
    """
    print("\n--- Initial Stock Processing (survival-function decay) ---")
    outflow_from_initial_stock_ts = np.zeros((num_years, num_elements))
    decaying_stock_ts = np.zeros((num_years, num_elements))

    if np.sum(initial_stock_vector) <= 0:
        return decaying_stock_ts, outflow_from_initial_stock_ts

    inflow_split = params.get("inflow_split", [1.0]) or [1.0]
    mean_lifetimes = params.get("lifetimes", {}).get("Mean", [])

    # Weighted survival function across categories (skip categories whose
    # mean lifetime is undefined — their split weight is redistributed).
    sf_combined = np.zeros(num_years)
    total_weight = 0.0
    for i, split in enumerate(inflow_split):
        mean_i = mean_lifetimes[i] if i < len(mean_lifetimes) else None
        if mean_i is None or np.isnan(float(mean_i)):
            continue
        lt_dict = _build_category_lt_dict(params, i)
        dsm_instance = dsm.DynamicStockModel(t=time_vector, lt=lt_dict)
        sf = dsm_instance.compute_sf()  # (T, T): sf[m, n] = survival at age m-n
        sf_combined += float(split) * sf[:, 0]
        total_weight += float(split)

    if total_weight <= 0:
        # No usable lifetime — stock persists unchanged (no decay information)
        decaying_stock_ts[:, :] = initial_stock_vector
        return decaying_stock_ts, outflow_from_initial_stock_ts
    sf_combined /= total_weight

    # The initial stock is established at t=0, so there is no outflow in the
    # first year. In every later year the amount leaving the stock is exactly
    # the stock's decrease, O[t] = S[t-1] - S[t], which keeps the process
    # mass-balanced.
    decaying_stock_ts[0, :] = initial_stock_vector
    for t in range(1, num_years):
        decaying_stock_ts[t, :] = initial_stock_vector * sf_combined[t]
        outflow_from_initial_stock_ts[t, :] = (
            decaying_stock_ts[t - 1, :] - decaying_stock_ts[t, :]
        )

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
    from dynamic_stock_model import DynamicStockModel
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
        mean_age=cohort_params.get("mean_age"),
        std_age=cohort_params.get("std_age"),
    )

    # Apply element composition to all cohorts
    initial_stock_cohort_matrix = apply_element_composition_to_cohorts(
        material_cohorts, cohort_params["element_fractions"]
    )

    max_age = cohort_params["max_age"]

    # ODYM's compute_evolution_initialstock places the initial stock at index
    # SwitchTime in the time array.  To make SwitchTime=max_age correspond to
    # the first simulation year (t=0), we build an extended time vector that
    # prepends max_age "past" steps.  We then take only the [max_age:] slice.
    n_extended = num_years + max_age
    t_extended = np.arange(n_extended)

    # Build a normalised single-category lt_dict for ODYM.
    # params["lifetimes"]["Type"] comes from _parse_parameter_based_dsm as a list
    # (e.g. ["Normal"]).  ODYM's __init__ tiles all keys EXCEPT "Type", so passing
    # a list as Type means lt["Type"] == "Normal" is always False → sf stays zeros
    # → NaN via 0/0 in compute_evolution_initialstock.  Extract the first element.
    lt_raw = params.get("lifetimes", {})
    type_raw = lt_raw.get("Type", "Normal")
    lt_type = (type_raw[0] if isinstance(type_raw, list) else type_raw) or "Normal"
    lt_type = _canon_lifetime_type(lt_type)

    lt_means = lt_raw.get("Mean", [0.0])
    lt_stds = lt_raw.get("StdDev", [0.0])
    lt_shapes = lt_raw.get("Shape", [None])
    lt_scales = lt_raw.get("Scale", [None])
    mean_val = float(lt_means[0]) if lt_means and lt_means[0] is not None else 0.0
    std_val = float(lt_stds[0]) if lt_stds and lt_stds[0] is not None else 0.0

    if lt_type == "Weibull":
        shape_val = lt_shapes[0] if lt_shapes and lt_shapes[0] is not None else None
        scale_val = lt_scales[0] if lt_scales and lt_scales[0] is not None else None
        if shape_val is not None and scale_val is not None:
            lt_dict = {
                "Type": "Weibull",
                "Shape": np.array([float(shape_val)]),
                "Scale": np.array([float(scale_val)]),
            }
        else:
            k, lam = _weibull_shape_scale_from_mean_std(mean_val, std_val)
            lt_dict = {
                "Type": "Weibull",
                "Shape": np.array([k]),
                "Scale": np.array([lam]),
            }
    elif std_val == 0 or lt_type == "Fixed":
        lt_dict = {"Type": "Fixed", "Mean": np.array([mean_val])}
    else:
        lt_dict = {
            "Type": lt_type,
            "Mean": np.array([mean_val]),
            "StdDev": np.array([std_val]),
        }

    if lt_dict["Type"] == "Weibull":
        print(
            f"  -> Cohort lt_dict: Type=Weibull, "
            f"Shape(k)={lt_dict['Shape'][0]:.4f}, Scale(lambda)={lt_dict['Scale'][0]:.4f}"
        )
    else:
        _mean_v = lt_dict.get("Mean", [None])[0]
        _std_v = lt_dict.get("StdDev", [None])[0] if "StdDev" in lt_dict else None
        _mean_s = f"{_mean_v:.1f}" if _mean_v is not None else "N/A"
        _std_s = f"{_std_v:.1f}" if _std_v is not None else "N/A"
        print(
            f"  -> Cohort lt_dict: Type={lt_dict['Type']}, Mean={_mean_s}, StdDev={_std_s}"
        )

    stock_ts = np.zeros((num_years, num_elements))
    outflow_ts = np.zeros((num_years, num_elements))

    for elem_idx in range(num_elements):
        dsm_obj = DynamicStockModel(t=t_extended, lt=lt_dict)
        initial_stock_elem = initial_stock_cohort_matrix[:, elem_idx]

        dsm_obj.compute_evolution_initialstock(
            InitialStock=initial_stock_elem, SwitchTime=max_age
        )
        # compute_evolution_initialstock pre-fills o_c with zeros, so
        # compute_o_c_from_s_c() would be a no-op.  Instead derive outflow
        # directly from the stock derivative: o[t] = max(0, s[t-1] - s[t]).
        dsm_obj.compute_stock_total()
        s_full = dsm_obj.s  # length = n_extended

        stock_ts[:, elem_idx] = s_full[max_age:]

        # Outflow = non-negative stock decrease per year
        o_full = np.zeros(n_extended)
        o_full[1:] = np.maximum(0.0, s_full[:-1] - s_full[1:])
        outflow_ts[:, elem_idx] = o_full[max_age:]

    if stock_ts[:, 0].max() > 0:
        print(
            f"  -> Cohort initial stock: S[0]={stock_ts[0, 0]:.1f}, "
            f"S[-1]={stock_ts[-1, 0]:.1f}, outflow[1]={outflow_ts[1, 0]:.2f}"
        )
    else:
        print(
            "  -> WARNING: cohort stock is all zeros — check lt_dict or age cohort params"
        )

    return stock_ts, outflow_ts


def _distribute_and_assign_outflows(
    mfa_system,
    process_id,
    outflow_flows,
    outflow_from_inflows_by_cat,
    outflow_from_initial_stock_ts,
    params,
    flow_tc_map,
):
    """Distributes and assigns all calculated outflows back to the MFA system.

    Outflow arrays from ``_calculate_outflow_from_inflows`` and from the initial
    stock functions are already shaped (num_years, num_elements) with vintage-correct
    element composition embedded. This function only needs to split them across
    outflow flows according to the TC (transfer coefficient) values.

    Uses the standard TC system, enabling dynamic (time-varying) splits and
    unified configuration with other process types.

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        The MFA system object to be modified.
    process_id : int
        The ID of the current DSM process.
    outflow_flows : list of odym.Flow
        The list of outflow flow objects for this process.
    outflow_from_inflows_by_cat : list of np.ndarray, each (num_years, num_elements)
        Outflow arrays per category from new inflows.
    outflow_from_initial_stock_ts : np.ndarray, shape (num_years, num_elements)
        Time series of outflow from the initial stock.
    params : dict
        DSM parameter configuration for the process.
    flow_tc_map : dict
        Map from flow names to TC parameter names.
    """
    num_years, num_elements = outflow_from_initial_stock_ts.shape
    elements = mfa_system.Elements

    # Buffers: (num_years, num_elements) per outflow flow
    final_outflows_from_inflows = [
        np.zeros((num_years, num_elements)) for _ in outflow_flows
    ]
    final_outflows_from_initial = [
        np.zeros((num_years, num_elements)) for _ in outflow_flows
    ]

    # --- TC lookup and normalization (material split drives all elements) ---
    # First pass: collect defined TC values; mark undefined flows with None.
    tc_values_raw = []
    any_tc_defined = False
    for flow in outflow_flows:
        tc_ids = flow_tc_map.get(flow.Name, {})
        tc_param_name = tc_ids.get("material")

        if tc_param_name and tc_param_name in mfa_system.ParameterDict:
            tc_value = mfa_system.ParameterDict[tc_param_name].Values
            if isinstance(tc_value, (int, float)):
                tc_value = np.full(num_years, float(tc_value))
            else:
                tc_value = np.asarray(tc_value).reshape(-1)
            any_tc_defined = True
        else:
            tc_value = None  # resolved in second pass
        tc_values_raw.append(tc_value)

    # Second pass: resolve None placeholders.
    # - If at least one flow has a TC → undefined flows receive 0 (they are simply
    #   not part of the split; the defined TCs are normalised among themselves).
    # - If NO flow has any TC → fall back to equal split across all flows.
    tc_values = []
    for i, tc_val in enumerate(tc_values_raw):
        if tc_val is not None:
            tc_values.append(tc_val)
        elif any_tc_defined:
            print(
                f"  -> Info: No TC for DSM outflow {outflow_flows[i].Name}; "
                f"assigning 0 (other TCs are defined and sum to 1)."
            )
            tc_values.append(np.zeros(num_years))
        else:
            print("  -> Info: No TCs defined for any DSM outflow; using equal split.")
            tc_values.append(np.full(num_years, 1.0 / max(len(outflow_flows), 1)))

    tc_array = np.vstack(tc_values)  # (num_flows, num_years)
    tc_sums = tc_array.sum(axis=0)  # (num_years,)
    tc_sums = np.where(tc_sums == 0, 1.0, tc_sums)
    normalized_tcs = tc_array / tc_sums  # (num_flows, num_years)

    # --- Distribute inflow-sourced outflows ---
    for cat_outflow in outflow_from_inflows_by_cat:
        for flow_idx in range(len(outflow_flows)):
            # tc scalar broadcast over element dimension: (num_years,1)
            final_outflows_from_inflows[flow_idx] += (
                cat_outflow * normalized_tcs[flow_idx][:, None]
            )

    # --- Distribute initial-stock outflows ---
    if np.sum(outflow_from_initial_stock_ts[:, 0]) > 0:
        for flow_idx in range(len(outflow_flows)):
            final_outflows_from_initial[flow_idx] = (
                outflow_from_initial_stock_ts * normalized_tcs[flow_idx][:, None]
            )

    # --- Assign to MFA system FlowDict ---
    for flow_idx, outflow_flow in enumerate(outflow_flows):
        mfa_system.FlowDict[outflow_flow.Name].Values[:, :] = (
            final_outflows_from_inflows[flow_idx]
            + final_outflows_from_initial[flow_idx]
        )

        # Recalculate hierarchical elements (e.g. TC as fraction of DM)
        element_hierarchy = getattr(mfa_system, "_element_hierarchy", {})
        if element_hierarchy:
            mfa_system.FlowDict[
                outflow_flow.Name
            ].Values = recalculate_hierarchical_elements(
                mfa_system.FlowDict[outflow_flow.Name].Values,
                elements,
                element_hierarchy,
                mfa_system,
            )

    print("\n--- Final Results Summary ---")
    total_outflow_from_inflows = sum(
        float(np.sum(o[:, 0])) for o in outflow_from_inflows_by_cat
    )
    print(f"Total outflow from inflows (material): {total_outflow_from_inflows:.2f}")
    print(
        f"Total outflow from initial stock (material): {float(np.sum(outflow_from_initial_stock_ts[:, 0])):.2f}"
    )
    total_assigned = sum(
        float(
            np.sum(
                (final_outflows_from_inflows[i] + final_outflows_from_initial[i])[:, 0]
            )
        )
        for i in range(len(outflow_flows))
    )
    print(f"Total outflow assigned to flows (material): {total_assigned:.2f}")


def _ancestors_in_hierarchy(element_name, element_hierarchy):
    """Return the set of element names on the path from element_name to the root.

    Given the mfa_system._element_hierarchy dict (elem_id → {"name": str, "parent": str|None}),
    walks upward through parent links and collects every ancestor including the
    element itself.  Used to build a replacement flow that is non-zero only for
    the replaced element and its ancestors (preserving hierarchy sums).
    """
    name_to_parent = {
        info["name"]: info.get("parent") for info in element_hierarchy.values()
    }
    ancestors = set()
    current = element_name
    while current is not None:
        ancestors.add(current)
        current = name_to_parent.get(current)
    return ancestors


def calculate_dynamic_stock_component(
    mfa_system, dsm_params_config, component_params, flow_tc_map=None
):
    """DSM with element-level component renewal flows (DSM_Component logic).

    Runs the standard product-level DSM first, then overlays replacement flows
    for each listed component using the stationary renewal approximation:

        replacement[t] = (1 / mean_lifetime_j) × stock_material[t] × fraction_j[t]

    Two flows are written per component:
    - sparepart_outflow: worn parts → downstream (WEEE / recycling)
    - sparepart_inflow:  new parts  ← upstream   (spare-parts storage)

    Both flows carry the same mass (immediate replacement, net-zero stock effect).
    The product outflow (device EoL) is handled entirely by the underlying DSM and
    carries the full defined flow composition unchanged.

    Parameters
    ----------
    mfa_system : odym.MFAsystem
    dsm_params_config : dict  — {process_id: params_dict}  (same as calculate_dynamic_stock)
    component_params : list   — list of component dicts for this process, each with keys:
                                  element, mean_lifetime, sparepart_outflow, sparepart_inflow
    flow_tc_map : dict, optional

    Returns
    -------
    tuple
        (mfa_system, dsm_details)  — same shape as calculate_dynamic_stock
    """
    # Zero spare flows before the DSM run and before the accumulation loop below.
    # Inflows must be zeroed so the device DSM doesn't count them as new product
    # inflow (self-amplifying feedback). Outflows must be zeroed so that multiple
    # components sharing the same flow ID accumulate correctly with += below.
    spare_inflow_ids  = {c.get("sparepart_inflow",  "") for c in component_params}
    spare_outflow_ids = {c.get("sparepart_outflow", "") for c in component_params}
    for fid in spare_inflow_ids | spare_outflow_ids:
        if fid and fid in mfa_system.FlowDict:
            mfa_system.FlowDict[fid].Values[:, :] = 0.0

    mfa_system, dsm_details = calculate_dynamic_stock(
        mfa_system, dsm_params_config, flow_tc_map=flow_tc_map,
        excluded_outflow_ids=spare_outflow_ids,
    )

    process_id = list(dsm_params_config.keys())[0]
    elements = mfa_system.Elements
    num_years = mfa_system.StockDict[f"S_{process_id}"].Values.shape[0]
    element_hierarchy = getattr(mfa_system, "_element_hierarchy", {})

    stock_material = mfa_system.StockDict[f"S_{process_id}"].Values[:, 0]

    # Pull per-category stock breakdown from dsm_details
    _det = dsm_details.get(process_id, {})
    inflow_stocks_by_cat = _det.get("inflow_stock_ts_by_cat", [])
    cat_names = _det.get("category_names", [])
    initial_stock_ts = _det.get("initial_stock_ts")  # (T, N_elem) or None

    for comp in component_params:
        element_name = comp.get("element", "")
        mean_lifetime = comp.get("mean_lifetime", 0.0)
        lifetime_per_cat = comp.get("lifetime_per_category", {})
        outflow_id = comp.get("sparepart_outflow", "")
        inflow_id = comp.get("sparepart_inflow", "")

        if element_name not in elements:
            print(f"  -> WARNING DSM_Component P{process_id}: element '{element_name}' not in system. Skipping.")
            continue
        if mean_lifetime <= 0:
            print(f"  -> WARNING DSM_Component P{process_id}: mean_lifetime must be > 0 for '{element_name}'. Skipping.")
            continue

        elem_idx = elements.index(element_name)
        stock_elem = mfa_system.StockDict[f"S_{process_id}"].Values[:, elem_idx]

        # Fraction of material that is this element (time-varying, from stock composition)
        with np.errstate(divide="ignore", invalid="ignore"):
            fraction_j = np.where(stock_material > 0, stock_elem / stock_material, 0.0)

        # Per-category replacement rate: Σ_i (cat_stock_i / μ_i_j)
        # Falls back to simple total-stock formula when no category data available.
        if lifetime_per_cat and cat_names and inflow_stocks_by_cat:
            rate_sum = np.zeros(num_years)
            for ci, cat_name in enumerate(cat_names):
                cat_lt = lifetime_per_cat.get(cat_name, mean_lifetime)
                if cat_lt > 0 and ci < len(inflow_stocks_by_cat):
                    rate_sum += inflow_stocks_by_cat[ci][:, 0] / cat_lt
            # Initial stock (pre-existing at t=0) uses the component's fallback lifetime
            if initial_stock_ts is not None and mean_lifetime > 0:
                rate_sum += initial_stock_ts[:, 0] / mean_lifetime
            replacement_mass = rate_sum * fraction_j
        else:
            replacement_mass = (1.0 / mean_lifetime) * stock_material * fraction_j  # (T,)

        # Build replacement flow: material root + element itself + all ancestor elements.
        # Multiple components may share a flow ID; += accumulates their contributions.
        replacement_flow = np.zeros((num_years, len(elements)))
        replacement_flow[:, 0] = replacement_mass        # material (root) always
        replacement_flow[:, elem_idx] = replacement_mass  # element itself
        if element_hierarchy:
            ancestors = _ancestors_in_hierarchy(element_name, element_hierarchy)
            for i, e in enumerate(elements):
                if e in ancestors and i != 0:  # root already set above
                    replacement_flow[:, i] = replacement_mass

        if outflow_id in mfa_system.FlowDict:
            mfa_system.FlowDict[outflow_id].Values[:, :] += replacement_flow  # accumulate
            mfa_system.FlowDict[outflow_id]._spare_protected = True  # skip TC solver
        else:
            print(f"  -> WARNING DSM_Component P{process_id}: outflow '{outflow_id}' not in FlowDict. Skipping.")
            continue

        if inflow_id in mfa_system.FlowDict:
            mfa_system.FlowDict[inflow_id].Values[:, :] += replacement_flow  # accumulate
            mfa_system.FlowDict[inflow_id]._spare_protected = True   # skip TC solver
        else:
            print(f"  -> WARNING DSM_Component P{process_id}: inflow '{inflow_id}' not in FlowDict. Skipping.")

        _avg_rate = float(np.mean(replacement_mass)) if np.any(stock_material > 0) else 0.0
        _mode = "per-category" if (lifetime_per_cat and cat_names) else "total-stock"
        print(
            f"  -> DSM_Component P{process_id} '{element_name}' [{_mode}]: "
            f"avg_r={_avg_rate:.3f}/yr, total replacement={float(np.sum(replacement_mass)):.1f}"
        )

    return mfa_system, dsm_details


def calculate_dynamic_stock(
    mfa_system, dsm_params_config, initial_stock_configs=None, flow_tc_map=None,
    excluded_outflow_ids=None,
):
    """Calculates stock and outflow for a single Dynamic Stock Model (DSM) process.

    This function orchestrates the DSM calculation for one process. It separates
    the calculation into two main parts: the outflow resulting from new inflows
    and the outflow from the decay of any initial stock. It then assigns the
    combined outflows back to the appropriate flow objects in the MFA system.

    The function supports two modes for initial stock handling:
    - Stock_with_InitialStock_Decay: single cohort at t=0 decaying along the
      category lifetime distributions (ODYM survival function)
    - Stock_with_InitialStock_Cohort: ODYM age-cohort method (age-distributed
      initial stock)

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

    # Check stock configuration FIRST to determine if we should use initial stock
    stock_configuration = params.get("stock_configuration", "Stock")

    # Only read initial stock from StockDict if configuration requires it
    if stock_configuration in [
        "Stock_with_InitialStock_Decay",
        "Stock_with_InitialStock_Cohort",
    ]:
        initial_stock_vector = (
            stock_s.Values[0, :].copy()
            if stock_s is not None
            else np.zeros(num_elements)
        )
        print(
            f"  -> Stock_Configuration: {stock_configuration} - Reading initial stock from system"
        )
        print(f"  -> Initial stock material: {initial_stock_vector[0]:.1f} Mg")
    else:
        # Stock_Configuration = "Stock" means zero initial stock
        initial_stock_vector = np.zeros(num_elements)
        print(
            f"  -> Stock_Configuration: {stock_configuration} - Using ZERO initial stock"
        )

    inflows = [f.Values for f in mfa_system.FlowDict.values() if f.P_End == process_id]
    total_inflow_values = (
        sum(inflows) if inflows else np.zeros((num_years, num_elements))
    )

    _excluded = excluded_outflow_ids or set()
    outflow_flows = [
        f for fid, f in mfa_system.FlowDict.items()
        if f.P_Start == process_id and fid not in _excluded
    ]
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

    if stock_configuration == "Stock_with_InitialStock_Cohort":
        # Use rigorous ODYM age-cohort method
        print("  -> Using ODYM age-cohort method for initial stock")

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
        # Survival-function decay (Stock_with_InitialStock_Decay or Stock):
        # single cohort at t=0, same lifetime distribution as new inflows
        if stock_configuration == "Stock_with_InitialStock_Decay":
            print("  -> Using survival-function decay for initial stock")

        decaying_stock_ts, outflow_from_initial_stock_ts = (
            _calculate_outflow_from_initial_stock(
                initial_stock_vector,
                params,
                num_years,
                num_elements,
                time_vector,
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
        flow_tc_map,
    )

    # Assign stock values back to MFA system.
    # stock_from_inflows_by_cat items are (num_years, num_elements) — vintage composition
    # is already embedded via the cohort-matrix multiply in _calculate_outflow_from_inflows.
    for elem_idx in range(num_elements):
        elem_stock = (
            sum(s[:, elem_idx] for s in stock_from_inflows_by_cat)
            + decaying_stock_ts[:, elem_idx]
        )
        mfa_system.StockDict[f"S_{process_id}"].Values[:, elem_idx] = elem_stock

    total_stock_from_inflows = float(
        sum(np.sum(s[:, 0]) for s in stock_from_inflows_by_cat)
    )
    print(
        f"Total stock accumulated from inflows (material): {total_stock_from_inflows:.2f}"
    )

    # Check for negative stocks in calculated results (check material column only)
    has_negative_stock = False
    for cat_idx, stock_array in enumerate(stock_from_inflows_by_cat):
        material_stock = stock_array[:, 0]
        negative_indices = np.where(material_stock < 0)[0]
        if len(negative_indices) > 0:
            has_negative_stock = True
            cat_name = params.get("category_names", [f"Category_{cat_idx + 1}"])[
                cat_idx
            ]
            print(
                f"   WARNING: Negative stock detected in Process {process_id}, Category '{cat_name}'"
            )
            print(f"      → {len(negative_indices)} time steps with negative values")
            print(
                f"      → Min value: {material_stock.min():.6f} at year {time_vector[np.argmin(material_stock)]}"
            )
            print(
                "      → This may indicate issues with lifetime distribution or inflow data"
            )

    # Check decaying initial stock for negative values
    if np.any(decaying_stock_ts < 0):
        negative_indices = np.where(decaying_stock_ts[:, 0] < 0)[0]
        if len(negative_indices) > 0:
            has_negative_stock = True
            print(
                f"   WARNING: Negative decaying initial stock in Process {process_id}"
            )
            print(f"      → {len(negative_indices)} time steps with negative values")
            print(
                f"      → Min value: {decaying_stock_ts[:, 0].min():.6f} at year {time_vector[np.argmin(decaying_stock_ts[:, 0])]}"
            )

    if not has_negative_stock:
        print("OK: No negative stocks detected")

    print(f"=== END DSM DEBUG for Process {process_id} ===\n")

    # ODYM validation after DSM calculation
    try:
        mfa_system.Consistency_Check()
        print(f"OK: DSM validation passed for process {process_id}")
    except Exception as e:
        print(f"WARNING: DSM validation warning for process {process_id}: {e}")

    dsm_details_results = {
        process_id: {
            "initial_stock_ts": decaying_stock_ts,
            "inflow_stock_ts_by_cat": stock_from_inflows_by_cat,
            "category_names": params.get("category_names", []),
            "mean_lifetimes": params.get("lifetimes", {}).get("Mean", []),
        }
    }

    return mfa_system, dsm_details_results
