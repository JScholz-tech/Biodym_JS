# -*- coding: utf-8 -*-
"""Unit tests for 02_src/engine/flow_cap.py (capacity-limited routing)."""

from types import SimpleNamespace

import numpy as np

from engine.flow_cap import _resolve_cap, calculate_flow_cap


# --------------------------------------------------------------------------
# _resolve_cap
# --------------------------------------------------------------------------

def test_resolve_cap_empty_series_is_zero():
    result = _resolve_cap({}, np.arange(2025, 2030, dtype=float), 5)
    np.testing.assert_array_equal(result, np.zeros(5))


def test_resolve_cap_static_key_zero_broadcasts():
    result = _resolve_cap({0: 500.0}, np.arange(2025, 2030, dtype=float), 5)
    np.testing.assert_array_equal(result, np.full(5, 500.0))


def test_resolve_cap_interpolates_and_clamps():
    time_vector = np.arange(2024, 2031, dtype=float)  # 2024..2030
    cap_series = {2025: 100.0, 2029: 500.0}
    result = _resolve_cap(cap_series, time_vector, 7)
    # Before the first defined year: clamp to first value
    assert result[0] == 100.0
    # Defined years exact
    assert result[1] == 100.0
    assert result[5] == 500.0
    # Midpoint 2027 linearly interpolated
    assert result[3] == 300.0
    # After the last defined year: clamp to last value
    assert result[6] == 500.0


# --------------------------------------------------------------------------
# calculate_flow_cap — minimal fake MFA system (no ODYM dependency needed)
# --------------------------------------------------------------------------

def _make_fake_system(inflow_values):
    """Fake mfa_system: P0 -> P1 (FlowCap) -> P2 (capped) / P3 (overflow)."""
    num_years = inflow_values.shape[0]
    years = list(range(2025, 2025 + num_years))
    flows = {
        "F_00_01": SimpleNamespace(P_Start=0, P_End=1, Values=inflow_values.copy()),
        "F_01_02": SimpleNamespace(P_Start=1, P_End=2, Values=np.zeros_like(inflow_values)),
        "F_01_03": SimpleNamespace(P_Start=1, P_End=3, Values=np.zeros_like(inflow_values)),
    }
    index_table = SimpleNamespace(
        Classification={"Time": SimpleNamespace(Items=years)}
    )
    return SimpleNamespace(
        FlowDict=flows, ParameterDict={}, IndexTable=index_table
    )


def _params(cap, overflow=True):
    return {
        1: {
            "cap_series": {0: cap},
            "cap_tc_id": None,
            "capped_flow_id": "F_01_02",
            "overflow_flow_id": "F_01_03" if overflow else None,
        }
    }


def test_flow_cap_splits_inflow_above_cap():
    inflow = np.tile([100.0, 60.0, 40.0, 10.0], (3, 1))  # material, WC, DM, TC
    system = _make_fake_system(inflow)

    changed = calculate_flow_cap(system, {1}, _params(cap=25.0))

    assert changed is True
    capped = system.FlowDict["F_01_02"].Values
    overflow = system.FlowDict["F_01_03"].Values
    # Material capped at 25, elements scaled proportionally (ratio 0.25)
    np.testing.assert_allclose(capped, inflow * 0.25)
    # Conservation: capped + overflow == inflow
    np.testing.assert_allclose(capped + overflow, inflow)


def test_flow_cap_passthrough_below_cap():
    inflow = np.tile([10.0, 6.0, 4.0, 1.0], (3, 1))
    system = _make_fake_system(inflow)

    calculate_flow_cap(system, {1}, _params(cap=999.0))

    np.testing.assert_allclose(system.FlowDict["F_01_02"].Values, inflow)
    np.testing.assert_allclose(
        system.FlowDict["F_01_03"].Values, np.zeros_like(inflow)
    )


def test_flow_cap_zero_inflow_stays_zero():
    inflow = np.zeros((3, 4))
    system = _make_fake_system(inflow)

    calculate_flow_cap(system, {1}, _params(cap=25.0))

    np.testing.assert_array_equal(system.FlowDict["F_01_02"].Values, inflow)
    np.testing.assert_array_equal(system.FlowDict["F_01_03"].Values, inflow)


def test_flow_cap_reports_no_change_when_converged():
    inflow = np.tile([100.0, 60.0, 40.0, 10.0], (3, 1))
    system = _make_fake_system(inflow)
    params = _params(cap=25.0)

    assert calculate_flow_cap(system, {1}, params) is True
    # Second application with identical inputs must report convergence
    assert calculate_flow_cap(system, {1}, params) is False
