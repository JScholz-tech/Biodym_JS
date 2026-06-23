# -*- coding: utf-8 -*-
"""
Scenario Plotting Module.

This file contains functions for plotting scenario comparison data.
Uses publication standards with shiny colors and standardized export.
"""

import numpy as np
import plotly.graph_objects as go
from ipywidgets import Button, Dropdown, HBox, HTML, Output, SelectMultiple, VBox
from IPython.display import display

from .export_publication import export_figure
from .themes import (
    apply_theme,
    get_publication_layout,
    get_element_color,
    create_color_sequence,
    get_mass_display,
    y_label,
    FONT_SIZE,
)

# Line dash patterns for distinguishing scenarios
_SCENARIO_DASHES = ["solid", "dash", "dot", "dashdot", "longdash", "longdashdot"]


def _build_flow_name_map(mfa_system):
    """Build descriptive flow names from process names: 'ProcessA -> ProcessB'."""
    process_name_by_id = {p.ID: p.Name for p in mfa_system.ProcessList}
    flow_map = {}
    for flow_id, flow_obj in mfa_system.FlowDict.items():
        src = process_name_by_id.get(flow_obj.P_Start, f"P{flow_obj.P_Start}")
        dst = process_name_by_id.get(flow_obj.P_End, f"P{flow_obj.P_End}")
        flow_map[flow_id] = f"{src} \u2192 {dst}"
    return flow_map


def _build_stock_name_map(mfa_system):
    """Build descriptive stock names from process names: 'ProcessName'."""
    stock_map = {}
    for stock_id in mfa_system.StockDict:
        if stock_id.startswith("S_"):
            pid = int(stock_id.split("_")[1])
            for p in mfa_system.ProcessList:
                if p.ID == pid:
                    stock_map[stock_id] = p.Name
                    break
            if stock_id not in stock_map:
                stock_map[stock_id] = f"Process {pid}"
    return stock_map


def _publication_legend():
    """Return a compact publication legend config."""
    return {
        "font": {"size": FONT_SIZE["legend"]},
        "bgcolor": "rgba(255,255,255,0.85)",
        "bordercolor": "#ccc",
        "borderwidth": 1,
        "orientation": "h",
        "yanchor": "top",
        "y": -0.18,
        "xanchor": "center",
        "x": 0.5,
    }


def plot_multi_scenario_comparison(
    baseline_results, all_scenario_results, scenario_definitions
):
    """Creates an interactive comparison plot for multiple scenarios.

    This function generates a bar chart or line diagram to compare key metrics
    (final stock or total flow) across a baseline and multiple user-selected
    scenarios. It also displays the parameter changes for each selected scenario.

    Parameters
    ----------
    baseline_results : odym.MFAsystem
        The solved MFA system object representing the baseline scenario.
    all_scenario_results : dict
        A dictionary where keys are scenario names (str) and values are the
        corresponding solved `odym.MFAsystem` objects for each scenario.
    scenario_definitions : dict
        A dictionary where keys are scenario names (str) and values are lists
        of dictionaries, each describing a parameter change for that scenario.

    Notes
    -----
    The plot is interactive, allowing users to select the metric (final stock
    or total flow), the specific item (stock ID or flow ID), the element,
    the chart type (bar or line), and which scenarios to display. It uses
    publication standards for styling and includes a display of scenario
    parameter definitions.
    """
    if not all_scenario_results:
        print("No scenario results to compare.")
        return

    elements = baseline_results.Elements
    stocks = [s for s in baseline_results.StockDict.keys() if s.startswith("S_")]
    flows = list(baseline_results.FlowDict.keys())
    all_scenarios = list(all_scenario_results.keys())

    stock_name_map = _build_stock_name_map(baseline_results)
    flow_name_map = _build_flow_name_map(baseline_results)

    # Build dropdown options with descriptive names
    stock_options = [(stock_name_map.get(sid, sid), sid) for sid in stocks]
    flow_options = [(flow_name_map.get(fid, fid), fid) for fid in flows]

    # --- Widgets ---
    metric_dropdown = Dropdown(
        options=["Final Stock", "Total Flow"], description="Metric:"
    )
    item_dropdown = Dropdown(options=stock_options, description="Item:")
    element_dropdown = Dropdown(options=elements, description="Element:")
    chart_type_dropdown = Dropdown(
        options=["Bar Chart", "Line Diagram"], description="Chart Type:"
    )
    scenario_selector = SelectMultiple(
        options=all_scenarios,
        value=all_scenarios,
        description="Scenarios:",
        disabled=False,
    )
    parameter_display = HTML(value="")

    def update_item_options(change):
        if change.new == "Final Stock":
            item_dropdown.options = stock_options
        else:
            item_dropdown.options = flow_options

    metric_dropdown.observe(update_item_options, names="value")

    fig = go.FigureWidget()

    def plot_comparison(metric, item, element, chart_type, selected_scenarios):
        with fig.batch_update():
            fig.data = []
            # Handle element safely
            if element not in elements:
                print(
                    f"⚠️ Element '{element}' not found in system. Available: {elements}"
                )
                return
            element_index = elements.index(element)

            scenarios_to_plot = ["Baseline"] + list(selected_scenarios)
            values = []

            _sc, _unit = get_mass_display()

            # Get baseline value
            if metric == "Final Stock":
                values.append(
                    baseline_results.StockDict[item].Values[-1, element_index] * _sc
                )
            else:  # Total Flow
                values.append(
                    np.sum(baseline_results.FlowDict[item].Values[:, element_index])
                    * _sc
                )

            # Get scenario values
            for scenario_name in selected_scenarios:
                scenario_result = all_scenario_results[scenario_name]
                if metric == "Final Stock":
                    values.append(
                        scenario_result.StockDict.get(
                            item,
                            type(
                                "obj",
                                (object,),
                                {
                                    "Values": np.zeros_like(
                                        baseline_results.StockDict[item].Values
                                    )
                                },
                            ),
                        ).Values[-1, element_index]
                        * _sc
                    )
                else:  # Total Flow
                    values.append(
                        np.sum(
                            scenario_result.FlowDict.get(
                                item,
                                type(
                                    "obj",
                                    (object,),
                                    {
                                        "Values": np.zeros_like(
                                            baseline_results.FlowDict[item].Values
                                        )
                                    },
                                ),
                            ).Values[:, element_index]
                        )
                        * _sc
                    )

            # Get meaningful item name for title
            if metric == "Final Stock":
                item_display_name = stock_name_map.get(item, item)
            else:
                item_display_name = flow_name_map.get(item, item)

            # Use shiny element color
            element_color = get_element_color(element)
            colors = create_color_sequence(len(scenarios_to_plot), palette="primary")

            # Choose chart type
            if chart_type == "Bar Chart":
                fig.add_trace(
                    go.Bar(
                        x=scenarios_to_plot,
                        y=values,
                        name=item,
                        marker_color=colors,
                        opacity=0.8,
                    )
                )
            else:  # Line Diagram
                fig.add_trace(
                    go.Scatter(
                        x=scenarios_to_plot,
                        y=values,
                        mode="lines+markers",
                        name=item,
                        line=dict(color=element_color, width=3),
                        marker=dict(color=element_color, size=8),
                        opacity=0.8,
                    )
                )

            # Apply publication layout
            layout_config = get_publication_layout(
                size="large",
                show_grid=True,
                scientific_y=True,
                custom_title=f"{metric} Comparison: {item_display_name} ({element.upper()})",
                y_title=y_label(element.upper()),
            )
            apply_theme(layout_config)
            layout_config["xaxis"].pop(
                "range", None
            )  # categorical axis, not time-series
            layout_config["showlegend"] = False
            fig.update_layout(**layout_config)

        # Update parameter display
        param_html = "<b>Scenario Definitions:</b><br>"
        for scenario_name in selected_scenarios:
            param_html += f"<b>{scenario_name}:</b><ul>"
            for param in scenario_definitions.get(scenario_name, []):
                param_html += f"<li>{param['Parameter_Name']} {param['Operation']} {param['New_Value']}</li>"
            param_html += "</ul>"
        parameter_display.value = param_html

    # Link widgets with observe pattern
    def update_plot():
        plot_comparison(
            metric_dropdown.value,
            item_dropdown.value,
            element_dropdown.value,
            chart_type_dropdown.value,
            scenario_selector.value,
        )

    metric_dropdown.observe(lambda change: update_plot(), names="value")
    item_dropdown.observe(lambda change: update_plot(), names="value")
    element_dropdown.observe(lambda change: update_plot(), names="value")
    chart_type_dropdown.observe(lambda change: update_plot(), names="value")
    scenario_selector.observe(lambda change: update_plot(), names="value")

    # Initial plot call
    update_plot()

    export_out = Output()
    export_btn = Button(
        description="Export Plot", button_style="info", layout={"width": "140px"}
    )

    def _export(b):
        export_out.clear_output()
        try:
            paths = export_figure(
                fig,
                "scenario_comparison",
                formats=["png", "svg"],
                quality="publication",
                size="large",
                timestamp=False,
            )
            with export_out:
                print(f"✅ Exported: {', '.join(paths)}")
        except Exception as e:
            with export_out:
                print(f"❌ Export failed: {e}")

    export_btn.on_click(_export)

    controls = HBox(
        [
            metric_dropdown,
            item_dropdown,
            element_dropdown,
            chart_type_dropdown,
            scenario_selector,
        ]
    )
    display(VBox([controls, fig, parameter_display, export_btn, export_out]))


def plot_scenario_flow_dynamics(
    baseline_results, all_scenario_results, scenario_definitions
):
    """Creates an interactive time-series plot showing flow dynamics for different scenarios.

    Color encodes the flow (descriptive names from process names), line style
    encodes the scenario (solid = baseline, dashed variants = scenarios).

    Parameters
    ----------
    baseline_results : odym.MFAsystem
        The solved MFA system object representing the baseline scenario.
    all_scenario_results : dict
        A dictionary of solved MFA system objects keyed by scenario name.
    scenario_definitions : dict
        Scenario parameter definitions (kept for API consistency).
    """
    if not all_scenario_results:
        print("No scenario results to compare.")
        return

    elements = baseline_results.Elements
    flows = list(baseline_results.FlowDict.keys())
    all_scenarios = list(all_scenario_results.keys())
    time_axis = baseline_results.IndexTable.Classification["Time"].Items
    flow_name_map = _build_flow_name_map(baseline_results)

    # Widgets — show descriptive names in selector
    flow_display = {fid: flow_name_map.get(fid, fid) for fid in flows}
    flow_selector = SelectMultiple(
        options=[(name, fid) for fid, name in flow_display.items()],
        value=flows[:3],
        description="Flows:",
    )
    element_dropdown = Dropdown(options=elements, description="Element:")
    scenario_selector = SelectMultiple(
        options=all_scenarios,
        value=all_scenarios,
        description="Scenarios:",
    )

    fig = go.FigureWidget()

    def plot_scenario_flows(selected_flows, element, selected_scenarios):
        with fig.batch_update():
            fig.data = []
            if element not in elements:
                return
            element_index = elements.index(element)
            _sc, _unit = get_mass_display()

            # Color per flow, dash per scenario
            flow_colors = create_color_sequence(len(selected_flows), palette="primary")
            scenarios_with_baseline = ["Baseline"] + list(selected_scenarios)

            for i, flow_id in enumerate(selected_flows):
                flow_obj = baseline_results.FlowDict.get(flow_id)
                if not flow_obj:
                    continue
                color = flow_colors[i]
                display_name = flow_name_map.get(flow_id, flow_id)

                for j, scenario_label in enumerate(scenarios_with_baseline):
                    dash = _SCENARIO_DASHES[j % len(_SCENARIO_DASHES)]
                    if scenario_label == "Baseline":
                        values = flow_obj.Values[:, element_index] * _sc
                    else:
                        sc_flow = all_scenario_results[scenario_label].FlowDict.get(
                            flow_id
                        )
                        if sc_flow is None:
                            continue
                        values = sc_flow.Values[:, element_index] * _sc

                    # Show legend only for first scenario per flow (avoid duplicates)
                    show_legend = j == 0
                    fig.add_trace(
                        go.Scatter(
                            x=time_axis,
                            y=values,
                            mode="lines",
                            name=display_name,
                            legendgroup=flow_id,
                            showlegend=show_legend,
                            line=dict(color=color, width=2, dash=dash),
                            hovertemplate=(
                                f"<b>{display_name}</b> ({scenario_label})<br>"
                                f"Year: %{{x}}<br>Value: %{{y:.3f}} {_unit}<extra></extra>"
                            ),
                        )
                    )

            # Add invisible traces for scenario line-style legend
            for j, scenario_label in enumerate(scenarios_with_baseline):
                dash = _SCENARIO_DASHES[j % len(_SCENARIO_DASHES)]
                fig.add_trace(
                    go.Scatter(
                        x=[None],
                        y=[None],
                        mode="lines",
                        name=scenario_label,
                        legendgroup="__scenarios",
                        line=dict(color="#333", width=2, dash=dash),
                        showlegend=True,
                    )
                )

            layout_config = get_publication_layout(
                size="large",
                show_grid=True,
                scientific_y=True,
                custom_title=f"Annual Flows by Scenario - {element.upper()}",
                x_title="Year",
                y_title=y_label(element.upper(), rate=True),
            )
            apply_theme(layout_config)
            fig.update_layout(**layout_config)

    def update_plot():
        plot_scenario_flows(
            flow_selector.value, element_dropdown.value, scenario_selector.value
        )

    flow_selector.observe(lambda change: update_plot(), names="value")
    element_dropdown.observe(lambda change: update_plot(), names="value")
    scenario_selector.observe(lambda change: update_plot(), names="value")

    update_plot()

    export_out = Output()
    export_btn = Button(
        description="Export Plot", button_style="info", layout={"width": "140px"}
    )

    def _export(b):
        export_out.clear_output()
        try:
            paths = export_figure(
                fig,
                f"scenario_flow_dynamics_{element_dropdown.value}",
                formats=["png", "svg"],
                quality="publication",
                size="large",
                timestamp=False,
            )
            with export_out:
                print(f"✅ Exported: {', '.join(paths)}")
        except Exception as e:
            with export_out:
                print(f"❌ Export failed: {e}")

    export_btn.on_click(_export)

    controls = HBox([flow_selector, element_dropdown, scenario_selector])
    display(VBox([controls, fig, export_btn, export_out]))


def plot_scenario_stock_dynamics(
    baseline_results, all_scenario_results, scenario_definitions
):
    """Creates an interactive time-series plot showing stock dynamics for different scenarios.

    Color encodes the stock (named after process), line style encodes the
    scenario (solid = baseline, dashed variants = scenarios).

    Parameters
    ----------
    baseline_results : odym.MFAsystem
        The solved MFA system object representing the baseline scenario.
    all_scenario_results : dict
        A dictionary of solved MFA system objects keyed by scenario name.
    scenario_definitions : dict
        Scenario parameter definitions (kept for API consistency).
    """
    if not all_scenario_results:
        print("No scenario results to compare.")
        return

    elements = baseline_results.Elements
    stocks = [s for s in baseline_results.StockDict.keys() if s.startswith("S_")]
    all_scenarios = list(all_scenario_results.keys())
    time_axis = baseline_results.IndexTable.Classification["Time"].Items
    stock_name_map = _build_stock_name_map(baseline_results)

    # Widgets — show descriptive names
    stock_selector = SelectMultiple(
        options=[(stock_name_map.get(sid, sid), sid) for sid in stocks],
        value=stocks[:3] if len(stocks) > 2 else stocks,
        description="Stocks:",
    )
    element_dropdown = Dropdown(options=elements, description="Element:")
    scenario_selector = SelectMultiple(
        options=all_scenarios,
        value=all_scenarios,
        description="Scenarios:",
    )

    fig = go.FigureWidget()

    def plot_scenario_stocks(selected_stocks, element, selected_scenarios):
        with fig.batch_update():
            fig.data = []
            if element not in elements:
                return
            element_index = elements.index(element)
            _sc, _unit = get_mass_display()

            stock_colors = create_color_sequence(
                len(selected_stocks), palette="primary"
            )
            scenarios_with_baseline = ["Baseline"] + list(selected_scenarios)

            for i, stock_id in enumerate(selected_stocks):
                stock_obj = baseline_results.StockDict.get(stock_id)
                if not stock_obj:
                    continue
                color = stock_colors[i]
                display_name = stock_name_map.get(stock_id, stock_id)

                for j, scenario_label in enumerate(scenarios_with_baseline):
                    dash = _SCENARIO_DASHES[j % len(_SCENARIO_DASHES)]
                    if scenario_label == "Baseline":
                        values = stock_obj.Values[:, element_index] * _sc
                    else:
                        sc_stock = all_scenario_results[scenario_label].StockDict.get(
                            stock_id
                        )
                        if sc_stock is None:
                            continue
                        values = sc_stock.Values[:, element_index] * _sc

                    show_legend = j == 0
                    fig.add_trace(
                        go.Scatter(
                            x=time_axis,
                            y=values,
                            mode="lines",
                            name=display_name,
                            legendgroup=stock_id,
                            showlegend=show_legend,
                            line=dict(color=color, width=2, dash=dash),
                            hovertemplate=(
                                f"<b>{display_name}</b> ({scenario_label})<br>"
                                f"Year: %{{x}}<br>Value: %{{y:.3f}} {_unit}<extra></extra>"
                            ),
                        )
                    )

            # Scenario line-style legend
            for j, scenario_label in enumerate(scenarios_with_baseline):
                dash = _SCENARIO_DASHES[j % len(_SCENARIO_DASHES)]
                fig.add_trace(
                    go.Scatter(
                        x=[None],
                        y=[None],
                        mode="lines",
                        name=scenario_label,
                        legendgroup="__scenarios",
                        line=dict(color="#333", width=2, dash=dash),
                        showlegend=True,
                    )
                )

            layout_config = get_publication_layout(
                size="large",
                show_grid=True,
                scientific_y=True,
                custom_title=f"Stock Trajectories by Scenario - {element.upper()}",
                x_title="Year",
                y_title=y_label(element.upper()),
            )
            apply_theme(layout_config)
            fig.update_layout(**layout_config)

    def update_plot():
        plot_scenario_stocks(
            stock_selector.value, element_dropdown.value, scenario_selector.value
        )

    stock_selector.observe(lambda change: update_plot(), names="value")
    element_dropdown.observe(lambda change: update_plot(), names="value")
    scenario_selector.observe(lambda change: update_plot(), names="value")

    update_plot()

    export_out = Output()
    export_btn = Button(
        description="Export Plot", button_style="info", layout={"width": "140px"}
    )

    def _export(b):
        export_out.clear_output()
        try:
            paths = export_figure(
                fig,
                f"scenario_stock_dynamics_{element_dropdown.value}",
                formats=["png", "svg"],
                quality="publication",
                size="large",
                timestamp=False,
            )
            with export_out:
                print(f"✅ Exported: {', '.join(paths)}")
        except Exception as e:
            with export_out:
                print(f"❌ Export failed: {e}")

    export_btn.on_click(_export)

    controls = HBox([stock_selector, element_dropdown, scenario_selector])
    display(VBox([controls, fig, export_btn, export_out]))


def plot_scenario_stock_publication(
    baseline_results,
    all_scenario_results,
    scenario_name=None,
    element=None,
    stock_ids=None,
    stock_labels=None,
    stock_colors=None,
    scenario_label=None,
    policy_year=2075,
    enable_export=True,
):
    """Static JIE-ready publication figure for scenario vs. baseline stock comparison.

    Shows baseline (solid) and one scenario (dashed) for selected stocks, with
    a vertical policy-year line and horizontal dotted reference lines at each
    stock's baseline value at policy_year.

    Parameters
    ----------
    baseline_results : odym.MFAsystem
    all_scenario_results : dict
        Keyed by scenario name.
    scenario_name : str or None
        Scenario to plot. Defaults to first key in all_scenario_results.
    element : str or None
        Element to plot. Defaults to TC/CC fallback, then first element.
    stock_ids : list[str] or None
        Stock IDs (e.g. ["S_3", "S_4", "S_5"]). Defaults to all S_* stocks.
    stock_labels : dict or None
        {stock_id: display_name}. Defaults to process names.
    stock_colors : list[str] or None
        Hex colours per stock (same order as stock_ids).
        Defaults to [teal-blue, magenta, amber] matching the case-study scheme.
    scenario_label : str or None
        Short legend label for the scenario line. Defaults to "Application Stop (2075)".
    policy_year : int or None
        Year for vertical reference line and horizontal dotted references. None = omit.
    enable_export : bool
        Show PNG/SVG export button.
    """
    if not all_scenario_results:
        print("No scenario results to plot.")
        return

    if scenario_name is None:
        scenario_name = next(iter(all_scenario_results))
    if scenario_name not in all_scenario_results:
        print(f"⚠️  Scenario '{scenario_name}' not found.")
        return

    scenario_results = all_scenario_results[scenario_name]
    elements = baseline_results.Elements
    time_axis = list(baseline_results.IndexTable.Classification["Time"].Items)

    # Element selection
    if element is None:
        element = next((e for e in ("TC", "CC") if e in elements), elements[0])
    if element not in elements:
        print(f"⚠️  Element '{element}' not found. Available: {elements}")
        return
    elem_idx = elements.index(element)

    # Stock selection
    all_stock_ids = [s for s in baseline_results.StockDict if s.startswith("S_")]
    if stock_ids is None:
        stock_ids = all_stock_ids
    stock_name_map = _build_stock_name_map(baseline_results)
    if stock_labels is None:
        stock_labels = stock_name_map

    # Colours: default matches case-study scheme (teal-blue, magenta, amber)
    _DEFAULT_COLORS = ["#1A6FAA", "#B0306A", "#D4A017", "#4A6741", "#6B5B7B"]
    colors = list(stock_colors) if stock_colors is not None else _DEFAULT_COLORS

    _sc, _unit = get_mass_display()

    # Policy year index for reference lines
    policy_idx = None
    if policy_year is not None and policy_year in time_axis:
        policy_idx = time_axis.index(policy_year)

    fig = go.Figure()

    # ── Baseline + scenario traces ────────────────────────────────────────────
    for i, sid in enumerate(stock_ids):
        color = colors[i % len(colors)]
        label = stock_labels.get(sid, stock_name_map.get(sid, sid))
        baseline_obj = baseline_results.StockDict.get(sid)
        scenario_obj = scenario_results.StockDict.get(sid)

        if baseline_obj is not None:
            y_base = baseline_obj.Values[:, elem_idx] * _sc
            fig.add_trace(
                go.Scatter(
                    x=time_axis,
                    y=y_base.tolist(),
                    mode="lines",
                    name=label,
                    legendgroup=f"color_{i}",
                    legendgrouptitle_text=None,
                    line=dict(color=color, width=2),
                    hovertemplate=f"<b>{label} – Baseline</b><br>Year: %{{x}}<br>%{{y:,.0f}} {_unit}<extra></extra>",
                )
            )

            # Horizontal dotted reference at policy_year baseline value
            if policy_idx is not None:
                y_ref = float(y_base[policy_idx])
                x_ref_start = time_axis[policy_idx]
                x_ref_end = time_axis[-1]
                fig.add_trace(
                    go.Scatter(
                        x=[x_ref_start, x_ref_end],
                        y=[y_ref, y_ref],
                        mode="lines",
                        name=label,
                        legendgroup=f"color_{i}",
                        showlegend=False,
                        line=dict(color=color, width=1.2, dash="dot"),
                        hoverinfo="skip",
                    )
                )

        if scenario_obj is not None:
            y_sc = scenario_obj.Values[:, elem_idx] * _sc
            fig.add_trace(
                go.Scatter(
                    x=time_axis,
                    y=y_sc.tolist(),
                    mode="lines",
                    name=label,
                    legendgroup=f"color_{i}",
                    showlegend=False,
                    line=dict(color=color, width=2, dash="dash"),
                    hovertemplate=f"<b>{label} – Scenario</b><br>Year: %{{x}}<br>%{{y:,.0f}} {_unit}<extra></extra>",
                )
            )

    # ── Line-style legend entries (Baseline / Scenario) ────────────────────
    sc_short = scenario_label or "Application Stop (2075)"
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="lines",
            name="Baseline",
            legendgroup="__linestyle",
            line=dict(color="#333", width=2, dash="solid"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="lines",
            name=sc_short,
            legendgroup="__linestyle",
            line=dict(color="#333", width=2, dash="dash"),
        )
    )

    # ── Policy year vertical line ─────────────────────────────────────────
    if policy_year is not None:
        fig.add_vline(
            x=policy_year,
            line=dict(color="black", dash="dash", width=0.8),
            annotation_text=str(policy_year),
            annotation_position="top right",
            annotation_font_size=9,
        )

    # ── Layout ────────────────────────────────────────────────────────────
    layout_config = get_publication_layout(
        custom_title="",
        x_title="Year",
        y_title=f"mass TC ({_unit})",
        show_grid=True,
        y_range=[0, None],
    )
    apply_theme(layout_config)
    layout_config["title"] = dict(text="")
    layout_config["yaxis"]["tickformat"] = ","
    layout_config["yaxis"]["exponentformat"] = "none"
    layout_config["legend"] = dict(
        orientation="h",
        x=0.5,
        y=-0.18,
        xanchor="center",
        yanchor="top",
        font=dict(size=10),
        bgcolor="rgba(255,255,255,0.85)",
        bordercolor="#ccc",
        borderwidth=1,
    )
    layout_config["margin"]["b"] = max(layout_config["margin"].get("b", 80), 110)
    fig.update_layout(**layout_config)

    if not enable_export:
        display(fig)
        return

    export_btn = Button(
        description="Export PNG/SVG",
        button_style="success",
        icon="download",
        layout={"width": "160px"},
    )

    def _do_export(b):
        try:
            paths = export_figure(
                fig,
                f"scenario_stock_publication_{element}",
                formats=["png", "svg"],
                quality="publication",
                size="publication",
                timestamp=False,
            )
            print(f"✅ Exported: {', '.join(paths)}")
        except Exception as e:
            print(f"❌ Export failed: {e}")

    export_btn.on_click(_do_export)
    display(HBox([export_btn]))
    display(fig)
