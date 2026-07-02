# -*- coding: utf-8 -*-
"""
Element Utilities Module for the BioDYM Engine.

This module contains utility functions for handling element calculations,
particularly for hierarchical element relationships.
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

        # Fraction is computed from current flow values (ParameterDict lookup not needed)
        original_fraction = None

        # Calculate the fraction from the flow values
        # For hierarchical elements, we want to preserve the ratio relative to parent
        # Use the first non-zero time step to get the "original" fraction
        with np.errstate(divide="ignore", invalid="ignore"):
            # Try to get fraction from first non-zero parent value
            fraction_vector = np.divide(
                flow_values[:, elem_idx],
                parent_values,
                out=np.zeros_like(parent_values, dtype=float),
                where=parent_values != 0,
            )

            # Use the first non-zero fraction as the "original" fraction
            # This assumes the initial setup was correct
            first_nonzero_idx = np.where(fraction_vector != 0)[0]
            if len(first_nonzero_idx) > 0:
                original_fraction = fraction_vector[first_nonzero_idx[0]]
            else:
                # If all fractions are zero, use zero
                original_fraction = 0.0

        # Recalculate: hierarchical_element = parent × ORIGINAL_fraction
        # This preserves the intended ratio even when parent changes
        flow_values[:, elem_idx] = parent_values * original_fraction

    return flow_values
