# -*- coding: utf-8 -*-
"""Unit tests for 02_src/engine/element_utils.py element lookup helpers."""

import pytest

from engine.element_utils import (
    get_carbon_element_index,
    get_carbon_element_name,
    get_element_index,
)


def test_carbon_name_prefers_tc_over_cc():
    assert get_carbon_element_name(["material", "WC", "DM", "TC", "CC"]) == "TC"


def test_carbon_name_falls_back_to_legacy_cc():
    assert get_carbon_element_name(["material", "WC", "DM", "CC"]) == "CC"


def test_carbon_name_default_when_missing():
    assert get_carbon_element_name(["material", "WC", "DM"]) is None
    assert get_carbon_element_name(["material"], default="material") == "material"


def test_element_index_found():
    assert get_element_index(["material", "WC", "DM", "TC"], "DM") == 2


def test_element_index_missing_returns_default():
    assert get_element_index(["material", "WC"], "TOC") is None
    assert get_element_index(["material", "WC"], "TOC", default=-1) == -1


def test_element_index_none_name_returns_default():
    assert get_element_index(["material", "WC"], None) is None


def test_element_index_strict_raises():
    with pytest.raises(ValueError, match="'TOC' not found"):
        get_element_index(["material", "WC"], "TOC", strict=True)


def test_carbon_index_with_fallback():
    assert get_carbon_element_index(["material", "WC", "DM", "TC"]) == 3
    assert get_carbon_element_index(["material", "CC", "DM"]) == 1
    assert get_carbon_element_index(["material", "WC"]) is None


def test_carbon_index_strict_raises_when_missing():
    with pytest.raises(ValueError):
        get_carbon_element_index(["material", "WC"], strict=True)


# --------------------------------------------------------------------------
# recalculate_hierarchical_elements — time-varying composition (Fix 5)
# --------------------------------------------------------------------------

import numpy as np

from engine.element_utils import recalculate_hierarchical_elements

ELEMENTS = ["material", "WC", "DM", "TC"]
HIERARCHY = {
    2: {"name": "WC", "parent": "material"},
    3: {"name": "DM", "parent": "material"},
    4: {"name": "TC", "parent": "DM"},
}


def test_hierarchy_constant_composition_unchanged():
    """Time-invariant compositions behave exactly as before."""
    n = 5
    flow = np.zeros((n, 4))
    flow[:, 0] = 100.0
    flow[:, 2] = 40.0          # DM constant
    flow[:, 3] = 40.0 * 0.18   # TC = 18% of DM every year

    result = recalculate_hierarchical_elements(flow.copy(), ELEMENTS, HIERARCHY)
    np.testing.assert_allclose(result[:, 3], 40.0 * 0.18)


def test_hierarchy_time_varying_composition_preserved_per_year():
    """Each year keeps its own TC/DM ratio (was locked to first year)."""
    flow = np.zeros((3, 4))
    flow[:, 0] = 100.0
    flow[:, 2] = [40.0, 40.0, 40.0]
    flow[:, 3] = [40.0 * 0.10, 40.0 * 0.20, 40.0 * 0.30]  # ratio changes

    result = recalculate_hierarchical_elements(flow.copy(), ELEMENTS, HIERARCHY)
    np.testing.assert_allclose(result[:, 3], [4.0, 8.0, 12.0])


def test_hierarchy_zero_parent_years_forward_filled():
    """Years with parent == 0 reuse the nearest defined ratio."""
    flow = np.zeros((4, 4))
    flow[:, 0] = 100.0
    flow[:, 2] = [40.0, 0.0, 0.0, 50.0]
    flow[:, 3] = [40.0 * 0.20, 0.0, 0.0, 50.0 * 0.10]

    result = recalculate_hierarchical_elements(flow.copy(), ELEMENTS, HIERARCHY)
    # Defined years keep their own ratio; zero-parent years yield 0 TC
    np.testing.assert_allclose(result[:, 3], [8.0, 0.0, 0.0, 5.0])


def test_hierarchy_all_zero_parent_yields_zero():
    flow = np.zeros((3, 4))
    flow[:, 0] = 100.0  # material only, DM stays zero

    result = recalculate_hierarchical_elements(flow.copy(), ELEMENTS, HIERARCHY)
    np.testing.assert_allclose(result[:, 3], 0.0)
