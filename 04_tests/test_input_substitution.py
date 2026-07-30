# -*- coding: utf-8 -*-
"""Unit tests for 02_src/engine/input_substitution.py (demand-substitution routing)."""

from types import SimpleNamespace

import numpy as np
import yaml

from engine.input_substitution import (
    calculate_input_substitution,
    load_input_substitution_from_yaml,
)


# --------------------------------------------------------------------------
# load_input_substitution_from_yaml — driven_elements auto-inference
# --------------------------------------------------------------------------

def _write_yaml(tmp_path, flow_data_entries, residual_flow_id="F_00_01"):
    config = {
        "processes": [
            {
                "id": 0,
                "input_substitution": {
                    "supply_flow_ids": ["F_03_00"],
                    "consumed_flow_id": "F_00_01_2",
                    "residual_flow_id": residual_flow_id,
                },
            },
        ],
        "flows": [
            {"id": "F_00_01", "from_process": 0, "to_process": 1},
            {"id": "F_00_01_2", "from_process": 0, "to_process": 1},
            {"id": "F_03_00", "from_process": 3, "to_process": 0},
        ],
        "flow_data": flow_data_entries,
    }
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    return str(path)


def test_load_infers_driven_element_from_own_flow_data(tmp_path):
    """An element with its own flow_data entry on the residual/System-input
    flow (beyond just "material") is auto-inferred as driven — no
    driven_elements field needed in the YAML at all."""
    path = _write_yaml(tmp_path, [
        {"flow_id": "F_00_01", "element": "material", "values": {2025: 100.0}},
        {"flow_id": "F_00_01", "element": "TC", "values": {2025: 20.0}},
    ])
    params = load_input_substitution_from_yaml(path)
    assert params[0]["driven_elements"] == ["TC"]


def test_load_no_driven_elements_when_only_material_target_exists(tmp_path):
    """Baseline case (T17/T18-style): only the demand target ("material")
    has its own flow_data — no deeper element is independently driven."""
    path = _write_yaml(tmp_path, [
        {"flow_id": "F_00_01", "element": "material", "values": {2025: 100.0}},
    ])
    params = load_input_substitution_from_yaml(path)
    assert params[0]["driven_elements"] == []


def test_load_infers_driven_elements_via_residual_discovery_fallback(tmp_path):
    """Inference still works when residual_flow_id is blank (back-compat
    configs) — the loader discovers it the same way the engine does."""
    path = _write_yaml(tmp_path, [
        {"flow_id": "F_00_01", "element": "material", "values": {2025: 100.0}},
        {"flow_id": "F_00_01", "element": "TC", "values": {2025: 20.0}},
    ], residual_flow_id="")
    params = load_input_substitution_from_yaml(path)
    assert params[0]["residual_flow_id"] is None  # not named, discovery is internal-only
    assert params[0]["driven_elements"] == ["TC"]


# --------------------------------------------------------------------------
# calculate_input_substitution — minimal fake MFA system (no ODYM dependency)
# --------------------------------------------------------------------------

def _make_fake_system(supply_values, target_values, elements=("material",)):
    """Fake mfa_system: P9 -> P7 (supply) ; P7 -> P8 boundary/residual outflow
    (pre-populated exactly as flow_data + one-time setup composition would)
    + consumed ; P7 -> P10 surplus. Process 7 is the Input_Substitution
    process.

    ``target_values`` may be a 1D array (applied to column 0 only, other
    columns start at zero — for material-only tests) or a full 2D array
    matching ``supply_values``'s shape (for multi-element tests where every
    column needs a realistic, independently-meaningful starting value).
    """
    num_years, num_elements = supply_values.shape
    years = list(range(2025, 2025 + num_years))
    target_values = np.asarray(target_values)
    if target_values.ndim == 1:
        boundary_values = np.zeros((num_years, num_elements))
        boundary_values[:, 0] = target_values
    else:
        boundary_values = target_values.copy()
    flows = {
        "F_09_07": SimpleNamespace(
            P_Start=9, P_End=7, Name="F_09_07", Values=supply_values.copy()
        ),
        "F_07_08": SimpleNamespace(
            P_Start=7, P_End=8, Name="F_07_08", Values=boundary_values
        ),
        "F_07_08_consumed": SimpleNamespace(
            P_Start=7, P_End=8, Name="F_07_08_consumed",
            Values=np.zeros((num_years, num_elements)),
        ),
        "F_07_10_surplus": SimpleNamespace(
            P_Start=7, P_End=10, Name="F_07_10_surplus",
            Values=np.zeros((num_years, num_elements)),
        ),
    }
    index_table = SimpleNamespace(
        Classification={"Time": SimpleNamespace(Items=years)}
    )
    return SimpleNamespace(
        FlowDict=flows,
        ParameterDict={},
        IndexTable=index_table,
        Elements=list(elements),
    )


def _params(supply_ids=("F_09_07",), surplus=True, residual=True, driven=(), lag_years=0):
    return {
        7: {
            "supply_flow_ids": list(supply_ids),
            "consumed_flow_id": "F_07_08_consumed",
            "surplus_flow_id": "F_07_10_surplus" if surplus else None,
            "residual_flow_id": "F_07_08" if residual else None,
            "driven_elements": list(driven),
            "lag_years": lag_years,
        }
    }


def _hierarchy(*pairs):
    """Build the {element_id: {'name', 'parent'}} shape calculate_input_substitution expects.
    ``pairs`` is (name, parent) tuples."""
    return {str(i): {"name": name, "parent": parent} for i, (name, parent) in enumerate(pairs)}


def test_substitution_no_supply_passthrough():
    # The boundary flow already holds the flow_data-populated target (200) —
    # with no supply, consumed stays 0 and the residual just confirms the
    # same 200 is still needed, so nothing actually changes on this pass.
    supply = np.zeros((3, 1))
    target = np.full(3, 200.0)
    system = _make_fake_system(supply, target, elements=("material",))

    changed = calculate_input_substitution(system, {7}, _params(supply_ids=()))

    assert changed is False
    np.testing.assert_allclose(system.FlowDict["F_07_08"].Values[:, 0], 200.0)
    np.testing.assert_allclose(system.FlowDict["F_07_08_consumed"].Values, 0.0)
    np.testing.assert_allclose(system.FlowDict["F_07_10_surplus"].Values, 0.0)


def test_substitution_supply_below_target():
    supply = np.tile([100.0], (3, 1))
    target = np.full(3, 150.0)
    system = _make_fake_system(supply, target, elements=("material",))

    calculate_input_substitution(system, {7}, _params())

    # Supply fully consumed; the remaining 50 still needs virgin material.
    np.testing.assert_allclose(system.FlowDict["F_07_08_consumed"].Values[:, 0], 100.0)
    np.testing.assert_allclose(system.FlowDict["F_07_08"].Values[:, 0], 50.0)
    np.testing.assert_allclose(system.FlowDict["F_07_10_surplus"].Values[:, 0], 0.0)


def test_substitution_supply_above_target():
    supply = np.tile([100.0], (3, 1))
    target = np.full(3, 25.0)
    system = _make_fake_system(supply, target, elements=("material",))

    calculate_input_substitution(system, {7}, _params())

    # Target fully met from supply; virgin extraction drops to zero; excess is surplus.
    np.testing.assert_allclose(system.FlowDict["F_07_08_consumed"].Values[:, 0], 25.0)
    np.testing.assert_allclose(system.FlowDict["F_07_08"].Values[:, 0], 0.0)
    np.testing.assert_allclose(system.FlowDict["F_07_10_surplus"].Values[:, 0], 75.0)


def test_substitution_zero_target_edge_case():
    supply = np.tile([100.0], (3, 1))
    target = np.zeros(3)
    system = _make_fake_system(supply, target, elements=("material",))

    calculate_input_substitution(system, {7}, _params())

    np.testing.assert_allclose(system.FlowDict["F_07_08_consumed"].Values[:, 0], 0.0)
    np.testing.assert_allclose(system.FlowDict["F_07_08"].Values[:, 0], 0.0)
    np.testing.assert_allclose(system.FlowDict["F_07_10_surplus"].Values[:, 0], 100.0)


def test_substitution_balances_top_level_elements_independently():
    """WC and DM (both children of material) are each balanced on their own
    terms — not via a single material-wide ratio — and material is
    recomputed afterward as their sum (mirrors Transformer's own recompute)."""
    hierarchy = _hierarchy(("material", None), ("WC", "material"), ("DM", "material"))
    num_years = 3
    # Target: material=100 (=WC 40 + DM 60); supply: WC fully available (40),
    # DM only half available (30 of 60) — a real per-element divergence a
    # single material-level ratio could never represent.
    target = np.zeros((num_years, 3))
    target[:, 1] = 40.0  # WC
    target[:, 2] = 60.0  # DM
    target[:, 0] = target[:, 1] + target[:, 2]
    supply = np.zeros((num_years, 3))
    supply[:, 1] = 40.0
    supply[:, 2] = 30.0
    supply[:, 0] = supply[:, 1] + supply[:, 2]
    system = _make_fake_system(supply, target, elements=("material", "WC", "DM"))

    calculate_input_substitution(system, {7}, _params(), element_hierarchy=hierarchy)

    consumed = system.FlowDict["F_07_08_consumed"].Values[0]
    residual = system.FlowDict["F_07_08"].Values[0]
    np.testing.assert_allclose(consumed, [70.0, 40.0, 30.0])  # material, WC, DM
    np.testing.assert_allclose(residual, [30.0, 0.0, 30.0])  # WC fully met, DM half short
    # material always balances as the sum of its own top-level children.
    np.testing.assert_allclose(consumed[0], consumed[1] + consumed[2])
    np.testing.assert_allclose(residual[0], residual[1] + residual[2])


def test_substitution_passenger_element_rides_along_with_parent_ratio():
    """Regression: a deeper element with no independent target of its own
    (e.g. Cu, a tramp contaminant riding along with DM) must NOT be
    independently capped at whatever its own default target happens to be
    (often 0, since nobody ever configured a real "Cu demand") — it must
    scale with however much of its *parent* actually got consumed,
    preserving the supply's own contamination ratio. Reproduces the T18
    tutorial bug found in review: Cu silently vanished (stayed 0 forever)
    under a naive per-element-independent design."""
    hierarchy = _hierarchy(("material", None), ("DM", "material"), ("Cu", "DM"))
    num_years = 2
    target = np.zeros((num_years, 3))
    target[:, 1] = 100.0  # DM demand
    target[:, 2] = 0.0  # Cu "target" was never independently configured
    target[:, 0] = target[:, 1]
    supply = np.zeros((num_years, 3))
    supply[:, 1] = 100.0  # scrap fully covers DM demand
    supply[:, 2] = 60.0  # scrap's own 0.6% Cu content-equivalent (60/100)
    supply[:, 0] = supply[:, 1]
    system = _make_fake_system(supply, target, elements=("material", "DM", "Cu"))

    calculate_input_substitution(system, {7}, _params(), element_hierarchy=hierarchy)

    consumed = system.FlowDict["F_07_08_consumed"].Values[0]
    # DM fully consumed (100/100) -> Cu rides along at the same ratio (100%),
    # NOT capped at its own (irrelevant) target of 0.
    np.testing.assert_allclose(consumed[1], 100.0)  # DM
    np.testing.assert_allclose(consumed[2], 60.0)  # Cu — must NOT be 0


def test_substitution_explicit_driven_element_gets_independent_target():
    """A deeper element with driven_elements set (e.g. TC in a carbon-cycle
    study, which genuinely has its own independent demand) is balanced on
    its own terms instead of riding along with its parent."""
    hierarchy = _hierarchy(("material", None), ("DM", "material"), ("TC", "DM"))
    num_years = 2
    target = np.zeros((num_years, 3))
    target[:, 1] = 100.0  # DM
    target[:, 2] = 20.0  # TC has its own genuine, smaller target
    target[:, 0] = target[:, 1]
    supply = np.zeros((num_years, 3))
    supply[:, 1] = 100.0
    supply[:, 2] = 80.0  # more TC available than its own target needs
    supply[:, 0] = supply[:, 1]
    system = _make_fake_system(supply, target, elements=("material", "DM", "TC"))

    calculate_input_substitution(
        system, {7}, _params(driven=("TC",)), element_hierarchy=hierarchy
    )

    consumed = system.FlowDict["F_07_08_consumed"].Values[0]
    residual = system.FlowDict["F_07_08"].Values[0]
    surplus = system.FlowDict["F_07_10_surplus"].Values[0]
    np.testing.assert_allclose(consumed[2], 20.0)  # capped at TC's own target
    np.testing.assert_allclose(residual[2], 0.0)
    np.testing.assert_allclose(surplus[2], 60.0)  # 80 available - 20 consumed


def test_substitution_passenger_residual_uses_own_composition_fraction():
    """The residual/boundary flow's passenger-element columns come from its
    OWN ParameterDict composition fraction (same convention every flow's
    one-time setup composition cascade uses), not from "target - consumed"."""
    hierarchy = _hierarchy(("material", None), ("DM", "material"), ("Cu", "DM"))
    num_years = 2
    target = np.zeros((num_years, 3))
    target[:, 1] = 100.0
    target[:, 0] = target[:, 1]
    supply = np.zeros((num_years, 3))
    supply[:, 1] = 40.0  # only partially covers demand -> virgin residual DM = 60
    supply[:, 2] = 24.0  # scrap Cu content (0.6 * 40)
    supply[:, 0] = supply[:, 1]
    system = _make_fake_system(supply, target, elements=("material", "DM", "Cu"))
    # Virgin material's own Cu content (0.05%), registered exactly like the
    # one-time setup composition cascade would.
    system.ParameterDict["Cu_F_07_08"] = SimpleNamespace(
        Values=np.full(num_years, 0.0005)
    )

    calculate_input_substitution(system, {7}, _params(), element_hierarchy=hierarchy)

    residual = system.FlowDict["F_07_08"].Values[0]
    np.testing.assert_allclose(residual[1], 60.0)  # DM: 100 target - 40 consumed
    np.testing.assert_allclose(residual[2], 0.03)  # Cu: 60 * 0.0005, not target(0)-consumed


def test_substitution_lag_years_delays_supply_by_one_year():
    """With lag_years=1, a return flow in year t only offsets demand in
    year t+1 — the same year's own supply must have zero effect on that
    year's own residual."""
    supply = np.array([[0.0], [100.0], [100.0]])  # nothing available in year 0
    target = np.full(3, 100.0)
    system = _make_fake_system(supply, target, elements=("material",))

    calculate_input_substitution(system, {7}, _params(lag_years=1))

    consumed = system.FlowDict["F_07_08_consumed"].Values[:, 0]
    residual = system.FlowDict["F_07_08"].Values[:, 0]
    # Year 0: no prior-year supply exists yet -> fully virgin.
    np.testing.assert_allclose([consumed[0], residual[0]], [0.0, 100.0])
    # Year 1: offset by year 0's supply (0) -> still fully virgin.
    np.testing.assert_allclose([consumed[1], residual[1]], [0.0, 100.0])
    # Year 2: offset by year 1's supply (100) -> fully substituted.
    np.testing.assert_allclose([consumed[2], residual[2]], [100.0, 0.0])


def test_substitution_reports_no_change_when_converged():
    supply = np.tile([100.0], (3, 1))
    target = np.full(3, 25.0)
    system = _make_fake_system(supply, target, elements=("material",))
    params = _params()

    assert calculate_input_substitution(system, {7}, params) is True
    # Second application with identical inputs must report convergence
    assert calculate_input_substitution(system, {7}, params) is False


def test_substitution_ignores_supply_flow_that_is_not_a_genuine_inflow():
    """Regression: a supply_flow_ids entry pointing at this process's own
    outflow (P_End != process_id) must be ignored, not summed as supply.
    Found via a real case study where supply_flow_ids was accidentally
    pointed at the boundary/residual flow itself — since that flow is
    rewritten every call, treating it as "supply" created a self-referential
    feedback loop that oscillated forever instead of converging."""
    supply = np.full((3, 1), 100.0)
    target = np.full(3, 100.0)
    system = _make_fake_system(supply, target, elements=("material",))
    # F_07_08 is this process's own boundary outflow (P_Start=7), not an
    # inflow (P_End=8) — must be rejected as a supply source.
    bad_params = {
        7: {
            "supply_flow_ids": ["F_07_08"],
            "consumed_flow_id": "F_07_08_consumed",
            "surplus_flow_id": "F_07_10_surplus",
            "residual_flow_id": "F_07_08",
            "driven_elements": [],
            "lag_years": 0,
        }
    }

    changed = calculate_input_substitution(system, {7}, bad_params)

    # Rejected supply treated as zero: nothing consumed, full target passes
    # through as residual — stable, not oscillating.
    np.testing.assert_allclose(system.FlowDict["F_07_08_consumed"].Values[:, 0], 0.0)
    np.testing.assert_allclose(system.FlowDict["F_07_08"].Values[:, 0], 100.0)
    assert changed is False  # boundary already held 100 (its own flow_data value)

    # Idempotent — a second call must not start oscillating either.
    changed_again = calculate_input_substitution(system, {7}, bad_params)
    assert changed_again is False


def test_substitution_target_survives_iteration_overwrite():
    """calculate_input_substitution overwrites the boundary flow's own Values
    every call (that's how the residual gets written). The *next* call — a
    later solver iteration, e.g. once an upstream chain resolves more supply —
    must keep using the ORIGINAL flow_data-populated target, not whatever
    residual value was left sitting in the flow by the previous call."""
    supply = np.full((3, 1), 60.0)
    target = np.full(3, 100.0)
    system = _make_fake_system(supply, target, elements=("material",))
    params = _params()

    calculate_input_substitution(system, {7}, params)
    np.testing.assert_allclose(system.FlowDict["F_07_08_consumed"].Values[:, 0], 60.0)
    np.testing.assert_allclose(system.FlowDict["F_07_08"].Values[:, 0], 40.0)

    # More supply "arrives" — if the target were re-read live from F_07_08
    # instead of cached, this would wrongly treat the leftover residual (40)
    # as the new target instead of the true original target (100).
    system.FlowDict["F_09_07"].Values[:, 0] = 100.0
    calculate_input_substitution(system, {7}, params)
    np.testing.assert_allclose(system.FlowDict["F_07_08_consumed"].Values[:, 0], 100.0)
    np.testing.assert_allclose(system.FlowDict["F_07_08"].Values[:, 0], 0.0)


def test_substitution_residual_flow_id_discovery_fallback():
    """Configs saved before residual_flow_id existed (residual_flow_id=None)
    must still work via the old discovery-by-elimination path."""
    supply = np.tile([100.0], (3, 1))
    target = np.full(3, 150.0)
    system = _make_fake_system(supply, target, elements=("material",))

    calculate_input_substitution(system, {7}, _params(residual=False))

    np.testing.assert_allclose(system.FlowDict["F_07_08_consumed"].Values[:, 0], 100.0)
    np.testing.assert_allclose(system.FlowDict["F_07_08"].Values[:, 0], 50.0)
