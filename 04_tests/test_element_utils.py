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
