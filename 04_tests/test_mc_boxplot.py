# -*- coding: utf-8 -*-
"""Unit test for plotting.plot_interactive_mc_boxplot."""

from types import SimpleNamespace

import numpy as np
import pandas as pd


def _fake_mc_df(n=50):
    rng = np.random.default_rng(0)
    return pd.DataFrame(
        {
            "iteration": np.arange(1, n + 1),
            "S_1_material": rng.normal(1000, 50, n),
            "S_1_TC": rng.normal(400, 20, n),
            "S_2_material": rng.normal(500, 30, n),
            "S_2_TC": rng.normal(200, 15, n),
            # timeseries columns must be ignored by the discovery logic
            "S_1_TC_timeseries": [list(range(5))] * n,
        }
    )


def _fake_mfa_system():
    stock1 = SimpleNamespace(Values=np.array([[900.0, 350.0]] * 3))
    stock2 = SimpleNamespace(Values=np.array([[480.0, 190.0]] * 3))
    return SimpleNamespace(
        Elements=["material", "TC"],
        ProcessList=[
            SimpleNamespace(ID=1, Name="Pedosphere"),
            SimpleNamespace(ID=2, Name="Landfill"),
        ],
        StockDict={"S_1": stock1, "S_2": stock2},
    )


def test_boxplot_builds_box_per_stock_plus_baseline(monkeypatch):
    import plotting

    captured = {}

    # Intercept the widget display and grab the FigureWidget it wraps.
    def fake_display(obj):
        captured["obj"] = obj

    monkeypatch.setattr(plotting.monte_carlo, "display", fake_display)

    plotting.plot_interactive_mc_boxplot(_fake_mc_df(), _fake_mfa_system())

    vbox = captured["obj"]
    # VBox([controls, fig_widget]) — the figure is the second child
    fig = vbox.children[1]
    box_traces = [t for t in fig.data if t.type == "box"]
    scatter_traces = [t for t in fig.data if t.type == "scatter"]

    # Default selection is up to 4 stocks — here both S_1 and S_2 for element TC
    assert len(box_traces) == 2
    # Deterministic baseline overlay present with one point per stock
    assert len(scatter_traces) == 1
    assert len(scatter_traces[0].x) == 2


def test_boxplot_empty_df_is_graceful(capsys):
    import plotting

    plotting.plot_interactive_mc_boxplot(pd.DataFrame())
    assert "No Monte Carlo results" in capsys.readouterr().out


def test_boxplot_exported_from_package():
    import plotting

    assert hasattr(plotting, "plot_interactive_mc_boxplot")
    assert "plot_interactive_mc_boxplot" in plotting.__all__
