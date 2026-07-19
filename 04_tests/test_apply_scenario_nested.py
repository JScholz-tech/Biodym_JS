# -*- coding: utf-8 -*-
"""Regression test: apply_scenario composition recalc on nested hierarchies.

Bug: apply_scenario's post-modification recalculation computed every element
as ``material x content_fraction``, but content-fraction parameters are
PARENT-relative (the setup composition pass applies them depth-ordered
against the parent). For depth>=2 children (e.g. an alloy inside a
component) the recalculated value was ``material x (child/parent fraction)``
— orders of magnitude off. Flat hierarchies (all elements children of
material) were unaffected, which is why T08's wheat-straw-style tree with a
single depth-2 element (TC under DM) only drifted subtly and the golden pin
never flagged it.

The fix recalculates depth-ordered against the parent's value.
"""

from types import SimpleNamespace

import numpy as np
import pytest

import system_setup


def _fake_system():
    """1-year, 4-element nested system: material -> Comp -> Comp_Cu."""
    elements = ["material", "Comp", "Other", "Comp_Cu"]
    flow = SimpleNamespace(
        Name="F_00_01",
        P_Start=0,
        P_End=1,
        Values=np.array([[100.0, 40.0, 60.0, 8.0]]),
    )
    # Content parameters: PARENT-relative fractions (setup semantics).
    params = {
        "Comp_F_00_01": SimpleNamespace(Values=0.4),  # 40 % of material
        "Other_F_00_01": SimpleNamespace(Values=0.6),  # 60 % of material
        "Comp_Cu_F_00_01": SimpleNamespace(Values=0.2),  # 20 % of Comp
    }
    return SimpleNamespace(
        FlowDict={"F_00_01": flow},
        Elements=elements,
        ParameterDict=params,
        _element_hierarchy={
            1: {"name": "Comp", "parent": None},
            2: {"name": "Other", "parent": None},
            3: {"name": "Comp_Cu", "parent": "Comp"},
        },
    )


def test_nested_child_recalculated_against_parent():
    mfa = _fake_system()
    system_setup.apply_scenario(mfa, {"S": []}, "S")
    v = mfa.FlowDict["F_00_01"].Values[0]
    assert v[1] == pytest.approx(40.0)  # Comp = 100 x 0.4
    assert v[2] == pytest.approx(60.0)  # Other = 100 x 0.6
    # THE regression: Comp_Cu = Comp x 0.2 = 8, NOT material x 0.2 = 20
    assert v[3] == pytest.approx(8.0)


def test_flat_hierarchy_behaviour_unchanged():
    mfa = _fake_system()
    # Remove the nesting: Comp_Cu becomes a direct child of material with a
    # material-relative fraction — the pre-fix semantics for flat trees.
    mfa._element_hierarchy = {
        1: {"name": "Comp", "parent": None},
        2: {"name": "Other", "parent": None},
        3: {"name": "Comp_Cu", "parent": "material"},
    }
    mfa.ParameterDict["Comp_Cu_F_00_01"].Values = 0.08
    system_setup.apply_scenario(mfa, {"S": []}, "S")
    v = mfa.FlowDict["F_00_01"].Values[0]
    assert v[3] == pytest.approx(8.0)  # material x 0.08, as before the fix


def test_missing_hierarchy_falls_back_to_material_base():
    mfa = _fake_system()
    mfa._element_hierarchy = {}
    system_setup.apply_scenario(mfa, {"S": []}, "S")
    v = mfa.FlowDict["F_00_01"].Values[0]
    # Without hierarchy info every fraction is applied against material —
    # the exact legacy behaviour.
    assert v[3] == pytest.approx(20.0)
