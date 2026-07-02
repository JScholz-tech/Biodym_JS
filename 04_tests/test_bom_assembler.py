# -*- coding: utf-8 -*-
"""Unit tests for 02_src/engine/bom_assembler.py (BOM-constrained assembly)."""

import numpy as np

from engine.bom_assembler import (
    _build_primary_vector,
    _compute_absolute_bom_fractions_ts,
    _find_limiting_factor,
)

ELEMENTS = ["material", "WC", "DM", "TC"]

# WC and DM are children of material; TC is a child of DM — the standard
# BioDYM element hierarchy (material = WC + DM, DM = TC + Ash).
HIERARCHY = {
    "h1": {"name": "WC", "parent": "material"},
    "h2": {"name": "DM", "parent": "material"},
    "h3": {"name": "TC", "parent": "DM"},
}


def _bom_ts(n_time, wc, dm, tc):
    bom = np.zeros((n_time, 4))
    bom[:, 1] = wc
    bom[:, 2] = dm
    bom[:, 3] = tc
    return bom


# --------------------------------------------------------------------------
# _compute_absolute_bom_fractions_ts
# --------------------------------------------------------------------------

def test_absolute_fractions_without_hierarchy_pass_through():
    bom = _bom_ts(2, wc=0.6, dm=0.4, tc=0.18)
    abs_bom = _compute_absolute_bom_fractions_ts(bom, ELEMENTS, None)
    np.testing.assert_allclose(abs_bom[:, 0], 1.0)
    np.testing.assert_allclose(abs_bom[:, 1], 0.6)
    np.testing.assert_allclose(abs_bom[:, 2], 0.4)
    np.testing.assert_allclose(abs_bom[:, 3], 0.18)


def test_absolute_fractions_cascade_parent_relative():
    # TC fraction is relative to DM: absolute TC = 0.4 (DM) x 0.18 (TC of DM)
    bom = _bom_ts(3, wc=0.6, dm=0.4, tc=0.18)
    abs_bom = _compute_absolute_bom_fractions_ts(bom, ELEMENTS, HIERARCHY)
    np.testing.assert_allclose(abs_bom[:, 1], 0.6)
    np.testing.assert_allclose(abs_bom[:, 2], 0.4)
    np.testing.assert_allclose(abs_bom[:, 3], 0.4 * 0.18)


# --------------------------------------------------------------------------
# _find_limiting_factor
# --------------------------------------------------------------------------

def test_limiting_factor_scarcest_element_wins():
    n_time, n_elem = 2, 4
    abs_bom = _bom_ts(n_time, wc=0.6, dm=0.4, tc=0.072)
    abs_bom[:, 0] = 1.0
    available = np.tile([1000.0, 600.0, 40.0, 7.2], (n_time, 1))
    # DM allows only 40 / 0.4 = 100 Mg of product; WC would allow 1000
    result = _find_limiting_factor(available, abs_bom, n_time, n_elem)
    np.testing.assert_allclose(result, 100.0)


def test_limiting_factor_clamped_by_available_material():
    n_time, n_elem = 2, 4
    abs_bom = _bom_ts(n_time, wc=0.1, dm=0.1, tc=0.01)
    abs_bom[:, 0] = 1.0
    # Elements are abundant, but only 50 Mg of material arrived
    available = np.tile([50.0, 500.0, 500.0, 50.0], (n_time, 1))
    result = _find_limiting_factor(available, abs_bom, n_time, n_elem)
    np.testing.assert_allclose(result, 50.0)


def test_limiting_factor_no_positive_fractions_uses_material():
    n_time, n_elem = 2, 4
    abs_bom = np.zeros((n_time, n_elem))
    abs_bom[:, 0] = 1.0
    available = np.tile([75.0, 10.0, 10.0, 1.0], (n_time, 1))
    result = _find_limiting_factor(available, abs_bom, n_time, n_elem)
    np.testing.assert_allclose(result, 75.0)


# --------------------------------------------------------------------------
# _build_primary_vector + conservation
# --------------------------------------------------------------------------

def test_primary_vector_composition():
    n_time, n_elem = 2, 4
    abs_bom = _bom_ts(n_time, wc=0.6, dm=0.4, tc=0.072)
    abs_bom[:, 0] = 1.0
    max_assemblable = np.array([100.0, 50.0])
    primary = _build_primary_vector(max_assemblable, abs_bom, n_time, n_elem)
    np.testing.assert_allclose(primary[:, 0], max_assemblable)
    np.testing.assert_allclose(primary[:, 1], max_assemblable * 0.6)
    np.testing.assert_allclose(primary[:, 3], max_assemblable * 0.072)


def test_primary_plus_residue_conserves_mass():
    n_time, n_elem = 3, 4
    abs_bom = _bom_ts(n_time, wc=0.6, dm=0.4, tc=0.072)
    abs_bom[:, 0] = 1.0
    available = np.tile([1000.0, 600.0, 40.0, 7.2], (n_time, 1))

    max_assemblable = _find_limiting_factor(available, abs_bom, n_time, n_elem)
    primary = _build_primary_vector(max_assemblable, abs_bom, n_time, n_elem)
    residue = available - primary

    # Nothing negative, everything accounted for
    assert (primary >= 0).all()
    assert (residue >= -1e-12).all()
    np.testing.assert_allclose(primary + residue, available)
