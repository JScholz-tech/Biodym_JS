# -*- coding: utf-8 -*-
"""
Element Utilities Module for the BioDYM Engine.

This module contains utility functions for handling element calculations,
particularly for hierarchical element relationships.

Mathematical notation (see bioDYM_mathematical_formulas.md §1.1, §2.3, §6.2):
    Paper symbol      Code variable
    φ_e (=e/p(e))  ←→  fraction_vector   (per-year child/parent ratio)
    p(e)           ←→  element_hierarchy[·]["parent"]
    e^TC           ←→  get_carbon_element_name (TC new / CC legacy)
    ch(e)          ←→  build_element_children_map(...)[e]
    ρ_f^e(t)       ←→  per-node residual in validate_element_hierarchy()
    exhaustive(e)  ←→  inferred node completeness in validate_exhaustive_hierarchy()
"""

import numpy as np


def get_carbon_element_name(elements, default=None):
    """Return the total-carbon element name: ``"TC"`` (new) or ``"CC"`` (legacy).

    BioDYM's canonical fallback for the element-naming split: newer systems
    call total carbon ``TC``, legacy input files use ``CC``. Never hardcode
    either — always resolve through this helper.

    Parameters
    ----------
    elements : sequence of str
        Element names, e.g. ``mfa_system.Elements``.
    default : any, optional
        Returned when neither ``TC`` nor ``CC`` is present (default None).
    """
    return next((e for e in ("TC", "CC") if e in elements), default)


def get_element_index(elements, name, default=None, strict=False):
    """Return the index of ``name`` in ``elements`` with unified error handling.

    Parameters
    ----------
    elements : sequence of str
    name : str or None
        Element name to look up (None simply yields ``default``).
    default : any, optional
        Returned when the element is missing and ``strict`` is False.
    strict : bool, optional
        When True, a missing element raises ValueError instead of
        returning ``default``.
    """
    if name is not None:
        elements = list(elements)
        if name in elements:
            return elements.index(name)
    if strict:
        raise ValueError(f"Element '{name}' not found in elements: {list(elements)}")
    return default


def get_carbon_element_index(elements, default=None, strict=False):
    """Index of the total-carbon element (TC/CC fallback), or ``default``."""
    return get_element_index(
        elements, get_carbon_element_name(elements), default=default, strict=strict
    )


def recalculate_hierarchical_elements(
    flow_values, elements, element_hierarchy, mfa_system=None
):
    """Recalculates hierarchical elements based on their parent element values.

    This function implements a 2-pass calculation to properly handle hierarchical
    element relationships (e.g., CC as % of DM, where DM is % of Material).

    Pass 1: Top-level elements are already calculated (% of material)
    Pass 2: Hierarchical elements are recalculated based on parent values

    Parameters
    ----------
    flow_values : np.ndarray
        Flow values array with shape (time, elements) to be modified in-place.
    elements : list of str
        List of element names (e.g., ['material', 'DM', 'CC']).
    element_hierarchy : dict
        Dictionary mapping element IDs to their structure:
        {element_id: {'name': str, 'parent': str or None}}
        If None or empty, no hierarchical recalculation is performed.
    mfa_system : odym.MFAsystem, optional
        The MFA system object (used to get fractions from ParameterDict).
        If None, assumes hierarchical elements are already proportional.

    Returns
    -------
    np.ndarray
        The modified flow_values array with hierarchical elements recalculated.

    Notes
    -----
    This function modifies flow_values in-place but also returns it for convenience.

    Example
    -------
    For a hierarchy: Material -> DM -> CC
    - DM is calculated as: DM = Material × DM_fraction (already done)
    - CC is recalculated as: CC = DM × CC_fraction (done here)
    """
    if not element_hierarchy:
        return flow_values  # No hierarchy defined, return as-is

    # Build mapping from element name to hierarchy info
    hierarchy_map = {}
    for elem_id, elem_info in element_hierarchy.items():
        elem_name = elem_info["name"]
        hierarchy_map[elem_name] = elem_info

    # Identify hierarchical elements (those with a parent that's not 'material')
    hierarchical_elements = []
    for elem_idx, element_name in enumerate(elements):
        if element_name == "material":
            continue

        elem_info = hierarchy_map.get(element_name, {})
        parent = elem_info.get("parent")

        # If parent exists and is not 'material', this is a hierarchical element
        if parent and parent != "material":
            hierarchical_elements.append((elem_idx, element_name, parent))

    # If no hierarchical elements, nothing to do
    if not hierarchical_elements:
        return flow_values

    # Recalculate each hierarchical element based on its parent
    for elem_idx, element_name, parent_element in hierarchical_elements:
        try:
            parent_idx = elements.index(parent_element)
        except ValueError:
            print(
                f"[WARNING] Parent element '{parent_element}' for '{element_name}' not found in elements list. Skipping."
            )
            continue

        parent_values = flow_values[:, parent_idx]

        # Per-year fraction relative to the parent element. Years where the
        # parent is zero leave the fraction undefined (NaN) and are filled
        # from the nearest defined year (forward-fill, then back-fill for a
        # leading gap). For time-invariant compositions this reduces to the
        # previous single-constant behaviour; for feedstock whose composition
        # changes over time, each year keeps its own ratio instead of being
        # locked to the first non-zero year.
        with np.errstate(divide="ignore", invalid="ignore"):
            fraction_vector = np.divide(
                flow_values[:, elem_idx],
                parent_values,
                out=np.full(len(parent_values), np.nan),
                where=parent_values != 0,
            )

        undefined = np.isnan(fraction_vector)
        if undefined.all():
            fraction_vector = np.zeros_like(fraction_vector)
        elif undefined.any():
            # Forward-fill: each undefined year takes the last defined ratio
            last_defined = np.where(~undefined, np.arange(len(undefined)), 0)
            np.maximum.accumulate(last_defined, out=last_defined)
            fraction_vector = fraction_vector[last_defined]
            # Back-fill a leading gap (years before the first defined ratio)
            first_defined = int(np.argmax(~undefined))
            fraction_vector[:first_defined] = fraction_vector[first_defined]

        # Recalculate: hierarchical_element(t) = parent(t) × fraction(t)
        flow_values[:, elem_idx] = parent_values * fraction_vector

    return flow_values


def build_element_children_map(element_hierarchy, elements):
    """Builds ch(e) = {parent_name: [child_name, ...]} from element_hierarchy.

    This is the inverse of the parent function p(e) already used by
    `recalculate_hierarchical_elements`: ch(e) := {e' : p(e') = e}
    (see bioDYM_mathematical_formulas.md §6.2). Both ``parent=None`` and
    ``parent="material"`` are treated as "child of mat" (top-level),
    matching the convention used throughout this module.

    Parameters
    ----------
    element_hierarchy : dict
        {element_id: {'name': str, 'parent': str or None}}, as stored on
        ``mfa_system._element_hierarchy``.
    elements : list of str
        Element names actually tracked by this mfa_system
        (``mfa_system.Elements``). Hierarchy entries whose name is not in
        this list are skipped — a hierarchy definition may reference an
        element that a particular system does not track.

    Returns
    -------
    dict
        {parent_name: [child_name, ...]}. A key is present only if at
        least one tracked child was found for it.
    """
    children_map = {}
    for elem_info in (element_hierarchy or {}).values():
        name = elem_info.get("name")
        if name is None or name not in elements:
            continue
        if name == "material":
            continue  # material is the root; it is never anyone's child
        parent = elem_info.get("parent") or "material"
        children_map.setdefault(parent, []).append(name)
    return children_map


def validate_element_hierarchy(mfa_system, tolerance=1.0):
    """Validates the local composition residual ρ_f^e(t) at every branching node.

    Generalizes the single top-level check performed once during setup
    (system_setup._calculate_elemental_compositions) to every node in the
    element hierarchy, not only children of "material". See
    bioDYM_mathematical_formulas.md §6.2 for the underlying formalism and
    for a proof that the previous aggregate "sum to 100%" check used by
    `plotting.composition` could never detect a violation below the top
    level (it telescopes to the top-level sum regardless of deeper-node
    correctness) — this function replaces that blind spot.

    For every node e with ch(e) != {}, and every flow f and year t:

        ρ_f^e(t) = F_f^e(t) - Σ_{e' in ch(e)} F_f^{e'}(t)

    reported as a percentage of F_f^e(t) (i.e. 100% means ch(e) exactly
    accounts for e's mass). A violation is flagged when that percentage
    falls outside [100-tolerance, 100+tolerance].

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        Must expose ``.Elements``, ``.FlowDict``, and
        ``._element_hierarchy`` (set by system_setup.py). Works on both
        solved and unsolved systems.
    tolerance : float, optional
        Tolerance in percentage points around 100%. Default 1.0 (i.e.
        99%-101% is considered valid).

    Returns
    -------
    dict
        {node_name: {"over": [(flow_label, year, pct)],
                     "under": [(flow_label, year, pct)]}}
        Only nodes with at least one violation are present.
        "over"  = ch(e) exceeds e (ρ_f^e(t) < 0 beyond tolerance) — a real
                  hierarchy-consistency bug (e.g. TOC+TIC > TC).
        "under" = ch(e) under-accounts for e — may be a genuine untracked
                  remainder (e.g. H/N/S not modelled) rather than an error;
                  reported for visibility, same convention as the
                  historical top-level-only check.
    """
    elements = list(mfa_system.Elements)
    element_hierarchy = getattr(mfa_system, "_element_hierarchy", None)
    if not element_hierarchy:
        return {}

    children_map = build_element_children_map(element_hierarchy, elements)
    if not children_map:
        return {}

    flow_descriptions = getattr(mfa_system, "_flow_descriptions", {})
    years = list(mfa_system.IndexTable.Classification["Time"].Items)

    violations = {}
    for parent_name, child_names in children_map.items():
        if parent_name not in elements:
            print(
                f"[WARNING] validate_element_hierarchy: parent '{parent_name}' "
                f"not found in elements list. Skipping ch({parent_name}) check."
            )
            continue

        parent_idx = elements.index(parent_name)
        child_idx = [elements.index(c) for c in child_names]

        node_over, node_under = [], []
        for flow_id, flow in mfa_system.FlowDict.items():
            values = flow.Values
            parent_values = values[:, parent_idx]
            children_sum = values[:, child_idx].sum(axis=1)

            valid = np.abs(parent_values) > 1e-10
            if not np.any(valid):
                continue

            pct = np.full(len(years), np.nan)
            pct[valid] = children_sum[valid] / parent_values[valid] * 100.0

            flow_label = flow_descriptions.get(flow_id, flow_id)
            for year_idx, year in enumerate(years):
                p = pct[year_idx]
                if np.isnan(p):
                    continue
                if p > 100.0 + tolerance:
                    node_over.append((flow_label, year, float(p)))
                elif p < 100.0 - tolerance:
                    node_under.append((flow_label, year, float(p)))

        if node_over or node_under:
            violations[parent_name] = {"over": node_over, "under": node_under}

    return violations


def validate_exhaustive_hierarchy(mfa_system, tolerance=0.1):
    """Flag flows where a parent drifts from a child set declared COMPLETE.

    Complements `validate_element_hierarchy`, which reports every deviation of
    Σ ch(e) from e. That check cannot be run unattended: a node whose children
    are only a partially tracked subset (the canonical DM → {TC} with
    Ash_content not modelled) under-accounts permanently and *legitimately*, so
    it would raise a violation on nearly every flow of nearly every study.

    Completeness is therefore not guessed here. It is read from
    ``mfa_system._exhaustive_elements``, which `system_setup` derives from the
    declared composition fractions (a parent whose children sum to 1.0 has been
    stated to be fully accounted for by them). Inferring it from solved values
    instead does not work: a flow that happens to be pure carbon shows TC == DM
    exactly, which is indistinguishable from a genuinely complete node.

    For each declared-exhaustive node e, every flow f and year t is checked:

        ρ_f^e(t) = F_f^e(t) - Σ_{e' ∈ ch(e)} F_f^{e'}(t)

    and reported when it strays beyond ``tolerance``.

    The failure mode this catches is a hand-fitted **aggregate** (parent-level)
    transfer coefficient that has gone stale relative to the composition now
    reaching its process. Such a coefficient is invisible to every other check:
    ODYM's `Consistency_Check` validates the material balance, and `material`
    is itself derived as the sum of top-level elements, so it agrees with the
    model by construction while the parent quietly stops equalling its parts.

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        Must expose ``.Elements``, ``.FlowDict``, ``._element_hierarchy`` and
        ``._exhaustive_elements``. Returns ``{}`` when completeness is unknown,
        so the check stays silent rather than guessing.
    tolerance : float, optional
        Tolerance in percentage points. Default 0.1, which sits well clear of
        solver round-off (observed ≤ 0.003 pp on converged systems) while
        catching real drift.

    Returns
    -------
    dict
        ``{node_name: [(flow_label, year, pct), ...]}`` for declared-exhaustive
        nodes that have deviating flows. Empty when consistent.
    """
    elements = list(mfa_system.Elements)
    element_hierarchy = getattr(mfa_system, "_element_hierarchy", None)
    exhaustive_nodes = getattr(mfa_system, "_exhaustive_elements", None)
    if not element_hierarchy or not exhaustive_nodes:
        return {}

    children_map = build_element_children_map(element_hierarchy, elements)
    if not children_map:
        return {}

    flow_descriptions = getattr(mfa_system, "_flow_descriptions", {})
    years = list(mfa_system.IndexTable.Classification["Time"].Items)

    violations = {}
    for parent_name, child_names in children_map.items():
        if parent_name not in elements or parent_name not in exhaustive_nodes:
            continue  # partially tracked node — legitimate remainder, stay silent

        parent_idx = elements.index(parent_name)
        child_idx = [elements.index(c) for c in child_names]

        deviating = []
        for flow_id, flow in mfa_system.FlowDict.items():
            values = flow.Values
            parent_values = values[:, parent_idx]
            children_sum = values[:, child_idx].sum(axis=1)

            valid = np.abs(parent_values) > 1e-10
            if not np.any(valid):
                continue

            flow_label = flow_descriptions.get(flow_id, flow_id)
            for year_idx, year in enumerate(years):
                if not valid[year_idx]:
                    continue
                pct = children_sum[year_idx] / parent_values[year_idx] * 100.0
                if abs(pct - 100.0) > tolerance:
                    deviating.append((flow_label, year, float(pct)))

        if deviating:
            violations[parent_name] = deviating

    return violations
