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
import pytest

from engine.element_utils import (
    build_element_children_map,
    validate_element_hierarchy,
)
from plotting.composition import validate_flow_compositions

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
