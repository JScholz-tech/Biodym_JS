# -*- coding: utf-8 -*-
"""
Tests for engine.element_utils.build_element_children_map() and
validate_element_hierarchy() (bioDYM_mathematical_formulas.md §2.6).

The key regression test (`test_deep_violation_...`) proves the bug this
module fixes: a hierarchy violation below the top level (TC's children
TOC/TIC over-allocated) was mathematically invisible to the old aggregate
"sum to 100% of material" check, because summing every "Remaining X"
segment telescopes exactly to the top-level sum regardless of deeper-node
correctness. The test asserts both that the new validator catches it AND
that the backward-compatible `validate_flow_compositions()` wrapper still
does not (by construction — it only ever reports the "material" node),
documenting the blind spot rather than silently fixing it.
"""

from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from engine.element_utils import (
    build_element_children_map,
    validate_element_hierarchy,
    validate_exhaustive_hierarchy,
)
from plotting.composition import validate_flow_compositions
from system_setup import _infer_exhaustive_elements

# mat
# +-- WC
# +-- DM
#     +-- TC
#         +-- TOC
#         +-- TIC
ELEMENTS = ["material", "WC", "DM", "TC", "TOC", "TIC"]
ELEMENT_HIERARCHY = {
    1: {"name": "material", "parent": None},
    2: {"name": "WC", "parent": "material"},
    3: {"name": "DM", "parent": "material"},
    4: {"name": "TC", "parent": "DM"},
    5: {"name": "TOC", "parent": "TC"},
    6: {"name": "TIC", "parent": "TC"},
}


def _make_system(values_2025, years=(2025,)):
    """Builds a minimal duck-typed mfa_system with one flow "F_01_02"."""
    values = np.array([values_2025 for _ in years], dtype=float)
    flows = {"F_01_02": SimpleNamespace(P_Start=1, P_End=2, Values=values)}
    index_table = SimpleNamespace(Classification={"Time": SimpleNamespace(Items=list(years))})
    return SimpleNamespace(
        Elements=ELEMENTS,
        FlowDict=flows,
        IndexTable=index_table,
        _element_hierarchy=ELEMENT_HIERARCHY,
        _flow_descriptions={},
    )


# --------------------------------------------------------------------------
# build_element_children_map — ch(e)
# --------------------------------------------------------------------------

def test_children_map_reconstructs_the_tree():
    children = build_element_children_map(ELEMENT_HIERARCHY, ELEMENTS)
    assert set(children["material"]) == {"WC", "DM"}
    assert children["DM"] == ["TC"]
    assert set(children["TC"]) == {"TOC", "TIC"}
    assert "TOC" not in children  # leaf: no children of its own
    assert "WC" not in children  # leaf: no children of its own


def test_children_map_treats_none_and_material_parent_identically():
    hierarchy = {
        1: {"name": "material", "parent": None},
        2: {"name": "A", "parent": None},
        3: {"name": "B", "parent": "material"},
    }
    children = build_element_children_map(hierarchy, ["material", "A", "B"])
    assert set(children["material"]) == {"A", "B"}


def test_children_map_skips_untracked_elements():
    # "TIC" is defined in the hierarchy but not in this system's Elements.
    children = build_element_children_map(ELEMENT_HIERARCHY, ["material", "WC", "DM", "TC", "TOC"])
    assert children["TC"] == ["TOC"]


# --------------------------------------------------------------------------
# validate_element_hierarchy — ρ_f^e(t)
# --------------------------------------------------------------------------

def test_fully_consistent_system_has_no_violations():
    # WC+DM = 100 = material; DM = TC (its only tracked child, no slack);
    # TOC+TIC = 80 = TC.
    system = _make_system([100.0, 20.0, 80.0, 80.0, 50.0, 30.0])
    assert validate_element_hierarchy(system, tolerance=1.0) == {}


def test_deep_violation_is_caught_by_new_validator_but_invisible_to_old_check():
    # TOC+TIC = 100, but TC = 80 -> 125% at the TC node. Top level (WC+DM=100
    # = material) and the DM level (DM=TC=80) stay exactly correct, so this
    # violation exists ONLY below the top level -- exactly the class of bug
    # the old aggregate check could never detect (bioDYM_mathematical_formulas.md §2.6).
    system = _make_system([100.0, 20.0, 80.0, 80.0, 50.0, 50.0])

    violations = validate_element_hierarchy(system, tolerance=1.0)
    assert "TC" in violations
    assert violations["TC"]["over"], "TOC+TIC=125% of TC must be flagged"
    flow_label, year, pct = violations["TC"]["over"][0]
    assert flow_label == "F_01_02"
    assert year == 2025
    assert pct == pytest.approx(125.0)
    assert "material" not in violations, (
        "top level is perfectly consistent -- this violation must be "
        "attributed to node 'TC', not folded into the top-level check"
    )
    assert "DM" not in violations

    # The historical aggregate check (kept for backward compatibility)
    # reports the "material" node slice only, so it MUST NOT catch this --
    # documenting the blind spot the new validator fixes, not just testing
    # that it is fixed.
    old_result = validate_flow_compositions(system, tolerance=1.0, verbose=False)
    assert old_result["over_100"] == []
    assert old_result["under_100"] == []


def test_top_level_violation_still_caught_by_both_old_and_new():
    # WC+DM = 110 vs material = 100 -> 110% at "material"; DM=TC and
    # TOC+TIC=TC=80 stay exactly consistent below the top level.
    system = _make_system([100.0, 30.0, 80.0, 80.0, 50.0, 30.0])

    violations = validate_element_hierarchy(system, tolerance=1.0)
    assert "material" in violations
    assert violations["material"]["over"]
    assert "TC" not in violations
    assert "DM" not in violations

    old_result = validate_flow_compositions(system, tolerance=1.0, verbose=False)
    assert len(old_result["over_100"]) == 1
    assert old_result["over_100"][0][2] == pytest.approx(110.0)


def test_under_allocation_reported_under_not_over():
    # TOC+TIC = 20 vs TC = 80 -> 25%: a genuine untracked remainder, not an
    # over-allocation bug.
    system = _make_system([100.0, 20.0, 80.0, 80.0, 10.0, 10.0])

    violations = validate_element_hierarchy(system, tolerance=1.0)
    assert "TC" in violations
    assert violations["TC"]["under"]
    assert not violations["TC"]["over"]
    pct = violations["TC"]["under"][0][2]
    assert pct == pytest.approx(25.0)


def test_within_tolerance_is_not_flagged():
    # TOC+TIC = 80.75 vs TC = 80 -> 100.9375%, inside the default 1% tolerance.
    system = _make_system([100.0, 20.0, 80.0, 80.0, 50.75, 30.0])
    assert validate_element_hierarchy(system, tolerance=1.0) == {}


def test_no_hierarchy_returns_empty():
    system = _make_system([100.0, 20.0, 80.0, 40.0, 25.0, 15.0])
    system._element_hierarchy = {}
    assert validate_element_hierarchy(system) == {}


# --------------------------------------------------------------------------
# validate_exhaustive_hierarchy — the solver-facing check
#
# validate_element_hierarchy() above reports EVERY deviation, which makes it
# unsafe to run unattended: a partially tracked node (DM -> {TC} with
# Ash_content not modelled) under-accounts permanently and legitimately.
# validate_exhaustive_hierarchy() therefore only inspects nodes that the input
# data declared complete, so the solver can run it on every study.
# --------------------------------------------------------------------------

def _exhaustive(system, nodes):
    system._exhaustive_elements = set(nodes)
    return system


def test_exhaustive_check_flags_parent_that_stopped_equalling_its_children():
    # TOC+TIC = 78 vs TC = 80 -> 97.5%. TC is declared exhaustive, so the
    # shortfall is a real inconsistency (the signature of an aggregate
    # parent-level TC fitted to a composition that has since changed).
    system = _exhaustive(_make_system([100.0, 20.0, 80.0, 80.0, 48.0, 30.0]), ["TC"])

    violations = validate_exhaustive_hierarchy(system, tolerance=0.1)
    assert "TC" in violations
    flow_label, year, pct = violations["TC"][0]
    assert flow_label == "F_01_02"
    assert year == 2025
    assert pct == pytest.approx(97.5)


def test_exhaustive_check_stays_silent_on_partially_tracked_nodes():
    # Same 97.5% shortfall at TC, but TC is NOT declared exhaustive -- this is
    # the canonical untracked-remainder case and must not be reported, or every
    # study using the standard DM -> {TC} hierarchy would emit false positives.
    system = _exhaustive(_make_system([100.0, 20.0, 80.0, 80.0, 48.0, 30.0]), ["material"])
    assert validate_exhaustive_hierarchy(system, tolerance=0.1) == {}


def test_exhaustive_check_flags_over_allocation_too():
    # TOC+TIC = 100 vs TC = 80 -> 125%.
    system = _exhaustive(_make_system([100.0, 20.0, 80.0, 80.0, 50.0, 50.0]), ["TC"])
    violations = validate_exhaustive_hierarchy(system, tolerance=0.1)
    assert violations["TC"][0][2] == pytest.approx(125.0)


def test_exhaustive_check_passes_when_children_account_exactly():
    system = _exhaustive(
        _make_system([100.0, 20.0, 80.0, 80.0, 50.0, 30.0]), ["material", "DM", "TC"]
    )
    assert validate_exhaustive_hierarchy(system, tolerance=0.1) == {}


def test_exhaustive_check_silent_without_a_declaration():
    # No _exhaustive_elements at all -> completeness unknown -> stay silent
    # rather than guess. Guessing from solved values is unsound: a pure-carbon
    # flow shows TC == DM exactly and is indistinguishable from a complete node.
    system = _make_system([100.0, 20.0, 80.0, 80.0, 48.0, 30.0])
    assert validate_exhaustive_hierarchy(system) == {}


def test_exhaustive_check_tolerance_absorbs_solver_round_off():
    # 79.96/80 -> 99.95%, inside the 0.1pp default (converged systems were
    # measured at <= 0.003pp round-off).
    system = _exhaustive(_make_system([100.0, 20.0, 80.0, 80.0, 49.96, 30.0]), ["TC"])
    assert validate_exhaustive_hierarchy(system, tolerance=0.1) == {}


# --------------------------------------------------------------------------
# system_setup._infer_exhaustive_elements — where completeness is DECLARED
#
# Composition fractions are parent-relative, so a parent whose children sum to
# 1.0 on a declared flow has been stated to be fully accounted for by them.
# This is read from the input data rather than inferred from results, and the
# declaring flows must AGREE — see test_infer_rejects_contradicted_declaration.
# --------------------------------------------------------------------------

def _flows_sheet(*rows, **fracs):
    """Flow rows; kwargs (or per-row dicts) are element names -> fraction."""
    if not rows:
        rows = (fracs,)
    frame = []
    for n, row_fracs in enumerate(rows):
        row = {"Flow_ID": f"F_00_{n:02d}"}
        for elem, value in row_fracs.items():
            row[f"Flow_E{ELEMENTS.index(elem) + 1}_Fraction[%]"] = value
        frame.append(row)
    return pd.DataFrame(frame)


def test_infer_marks_node_exhaustive_when_children_sum_to_one():
    # TOC 0.6 + TIC 0.4 = 1.0 -> TC is completely accounted for by its children.
    sheet = _flows_sheet(material=1.0, WC=0.2, DM=0.8, TC=0.35, TOC=0.6, TIC=0.4)
    result = _infer_exhaustive_elements(
        {"1_1_Definition_Flows": sheet}, ELEMENT_HIERARCHY, ELEMENTS
    )
    assert "TC" in result
    # WC+DM = 1.0 as well, so material is exhaustive too.
    assert "material" in result
    # DM's only tracked child is TC at 0.35 -> partial, must NOT be claimed.
    assert "DM" not in result


def test_infer_leaves_partial_node_out():
    # The canonical case: DM -> {TC} at 30%, Ash_content untracked.
    sheet = _flows_sheet(material=1.0, WC=0.7, DM=0.3, TC=0.30, TOC=0.5, TIC=0.5)
    result = _infer_exhaustive_elements(
        {"1_1_Definition_Flows": sheet}, ELEMENT_HIERARCHY, ELEMENTS
    )
    assert "DM" not in result


def test_infer_rejects_contradicted_declaration():
    """A pure-carbon boundary flow must not make a partial DM look complete.

    Regression: a biomass model declares atmospheric C uptake as TC = 100% of
    DM on the boundary flow, while every real flow carries TC at ~45% of DM
    (Ash_content untracked). Reading only the boundary flow marked DM
    exhaustive, and the solver's Transformer branch then overwrites DM with
    TC on every transformation — deleting the ash fraction and breaking the
    mass balance (observed: -55% of DM across both drying processes of the
    JIE_Wood study, and all three Transformers of JIE_Wheat_Straw).
    """
    sheet = _flows_sheet(
        {"material": 1.0, "DM": 1.0, "TC": 1.0},  # pure-carbon uptake
        {"material": 1.0, "WC": 0.3, "DM": 0.7, "TC": 0.45},  # real biomass
    )
    result = _infer_exhaustive_elements(
        {"1_1_Definition_Flows": sheet}, ELEMENT_HIERARCHY, ELEMENTS
    )
    assert "DM" not in result
    # material is declared consistently (1.0 on the second row, and 1.0 on the
    # first where the undeclared WC counts as absent) and must survive.
    assert "material" in result


def test_infer_accepts_consistent_declaration_across_flows():
    """Agreement across several declaring flows still yields exhaustive."""
    sheet = _flows_sheet(
        {"material": 1.0, "WC": 0.2, "DM": 0.8, "TC": 0.5, "TOC": 0.6, "TIC": 0.4},
        {"material": 1.0, "WC": 0.4, "DM": 0.6, "TC": 0.3, "TOC": 0.9, "TIC": 0.1},
    )
    result = _infer_exhaustive_elements(
        {"1_1_Definition_Flows": sheet}, ELEMENT_HIERARCHY, ELEMENTS
    )
    assert "TC" in result
    assert "material" in result
    assert "DM" not in result


def test_infer_returns_empty_without_composition_data():
    assert _infer_exhaustive_elements({}, ELEMENT_HIERARCHY, ELEMENTS) == set()
    assert (
        _infer_exhaustive_elements(
            {"1_1_Definition_Flows": pd.DataFrame()}, ELEMENT_HIERARCHY, ELEMENTS
        )
        == set()
    )


def test_infer_returns_empty_without_hierarchy():
    sheet = _flows_sheet(material=1.0, WC=0.2, DM=0.8)
    assert _infer_exhaustive_elements({"1_1_Definition_Flows": sheet}, {}, ELEMENTS) == set()
