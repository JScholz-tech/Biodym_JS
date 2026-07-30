# -*- coding: utf-8 -*-
"""Tests for Input_Substitution-related plotting: the mass-balance-error
boundary-detection fix (validation.py) and the residual-flow resolver
helper shared with the new diagnostic plots (dynamics.py)."""

from types import SimpleNamespace

import numpy as np
import plotly.graph_objects as go

import plotting.dynamics as dynamics
from plotting.validation import plot_total_mass_balance_error
from plotting.dynamics import _resolve_input_substitution_residual_flow


def _make_fake_system():
    """Two-process system: P0 is Input_Substitution (residual + consumed,
    genuine inflow from P1's supply), P1 is a plain sink with no stock."""
    years = [2025, 2026]
    num_years, num_elements = len(years), 1

    flows = {
        "F_01_00": SimpleNamespace(
            Name="F_01_00", P_Start=1, P_End=0,
            Values=np.full((num_years, num_elements), 40.0),
        ),
        "F_00_01": SimpleNamespace(
            Name="F_00_01", P_Start=0, P_End=1,
            Values=np.full((num_years, num_elements), 60.0),  # residual (virgin)
        ),
        "F_00_01_2": SimpleNamespace(
            Name="F_00_01_2", P_Start=0, P_End=1,
            Values=np.full((num_years, num_elements), 40.0),  # consumed
        ),
    }
    processes = [
        SimpleNamespace(ID=0, Name="Substitution Process"),
        SimpleNamespace(ID=1, Name="Sink"),
    ]
    index_table = SimpleNamespace(Classification={"Time": SimpleNamespace(Items=years)})
    return SimpleNamespace(
        FlowDict=flows,
        StockDict={},
        ProcessList=processes,
        Elements=["material"],
        IndexTable=index_table,
    )


def test_mass_balance_error_zeroes_input_substitution_boundary():
    """Regression: Input_Substitution processes have a genuine physical
    inflow (recycled supply) AND an outflow that's partly manufactured with
    no inflow at all (the virgin/residual portion) — a pattern the old
    is_input_process/is_output_process heuristic couldn't recognize, so it
    flagged the residual as a large false-positive "imbalance". Found via a
    real case study where the reported "error" exactly equalled the
    residual flow's own value."""
    system = _make_fake_system()
    substitution_params = {0: {"consumed_flow_id": "F_00_01_2", "residual_flow_id": "F_00_01"}}

    fig = plot_total_mass_balance_error(
        system, enable_export=False, substitution_params=substitution_params
    )

    labels = list(fig.data[0].x)
    assert "Substitution Process*" in labels
    idx = labels.index("Substitution Process*")
    for trace in fig.data:
        assert trace.y[idx] == 0.0

    # Without substitution_params, the same process is NOT recognized as a
    # boundary and reports a (false-positive) imbalance — confirms the fix
    # is what's doing the work, not some other zeroing path.
    fig_unfixed = plot_total_mass_balance_error(system, enable_export=False)
    labels_unfixed = list(fig_unfixed.data[0].x)
    idx_unfixed = labels_unfixed.index("Substitution Process")
    assert fig_unfixed.data[0].y[idx_unfixed] != 0.0


def test_resolve_residual_flow_named():
    system = _make_fake_system()
    params = {"residual_flow_id": "F_00_01", "consumed_flow_id": "F_00_01_2"}
    flow = _resolve_input_substitution_residual_flow(system, 0, params)
    assert flow.Name == "F_00_01"


def test_resolve_residual_flow_discovery_fallback():
    """No residual_flow_id configured — falls back to discovering the sole
    other P_Start==pid outflow not claimed by consumed/surplus, same rule
    as engine.input_substitution and consistency.input_substitution_residual_flow."""
    system = _make_fake_system()
    params = {"residual_flow_id": None, "consumed_flow_id": "F_00_01_2", "surplus_flow_id": None}
    flow = _resolve_input_substitution_residual_flow(system, 0, params)
    assert flow.Name == "F_00_01"


def _capture_figurewidget(monkeypatch):
    """plot_input_substitution_rate builds its FigureWidget internally and
    never returns it (interactive-plot convention throughout this module,
    e.g. plot_fomp_dynamics) — capture the instance via the module's own
    go.FigureWidget reference so the resulting trace can be inspected."""
    captured = {}
    orig = go.FigureWidget

    def capturing(*args, **kwargs):
        fig = orig(*args, **kwargs)
        captured["fig"] = fig
        return fig

    monkeypatch.setattr(dynamics.go, "FigureWidget", capturing)
    return captured


def test_input_substitution_rate_computes_consumed_over_target(monkeypatch):
    """substitution % = consumed / (residual + consumed) * 100, per year/element."""
    captured = _capture_figurewidget(monkeypatch)
    system = _make_fake_system()  # residual=60, consumed=40 -> target=100
    substitution_params = {0: {"consumed_flow_id": "F_00_01_2", "residual_flow_id": "F_00_01"}}

    dynamics.plot_input_substitution_rate(system, substitution_params)

    fig = captured["fig"]
    assert list(fig.data[0].x) == ["Substitution Process"]
    np.testing.assert_allclose(list(fig.data[0].y), [40.0])  # 40 / (60+40) * 100
