# -*- coding: utf-8 -*-
"""
Dynamics Plotting Module.

This file contains functions for plotting time-series data, such as
stock and process dynamics.
"""

import math
import numpy as np
import plotly.graph_objects as go
from ipywidgets import (
    IntSlider,
    Dropdown,
    SelectMultiple,
    Checkbox,
    HBox,
    VBox,
    Layout,
    Button,
)
from .themes import (
    apply_theme,
    get_active_theme,
    get_publication_layout,
    get_mass_display,
    y_label,
    FONT_SIZE,
)
from .dynamic_colors import ElementColorManager
from .export_publication import export_figure
from IPython.display import display
from plotly.subplots import make_subplots
import pandas as pd
from typing import Optional


def plot_dsm_process_dynamics(mfa_system_results, dsm_params, dsm_details):
    """Creates a three-panel interactive plot for DSM process dynamics.

    This function visualizes the dynamics of a selected Dynamic Stock Model (DSM)
    process over time. It presents a comprehensive view with three subplots:
    1.  **Input Flows**: A stacked area chart of all flows entering the process.
    2.  **Stock Evolution**: A line chart showing the change in the process's stock.
    3.  **Output Flows**: A stacked area chart of all flows leaving the process.

    The plot is interactive, allowing the user to select the DSM process and
    the element to display. It also includes a button to export the current
    view as a high-resolution PNG image.

    Parameters
    ----------
    mfa_system_results : odym.MFAsystem
        The solved MFA system object, containing the results of the MFA
        calculation, including all flows and stocks over the simulation period.
    dsm_params : dict
        A dictionary containing the configuration parameters for all DSM
        processes in the model. The keys are process IDs.
    dsm_details : dict
        A dictionary containing detailed results from the DSM calculations,
        though this parameter is not directly used in this specific plotting
        function, it is part of the consistent API.

    Notes
    -----
    The function uses `ipywidgets` for interactivity and `plotly` for plotting.
    It is designed to be used within a Jupyter Notebook or JupyterLab environment.
    The styling of the plot is governed by the `get_publication_layout`
    function to ensure consistency with publication standards.
    """
    if not dsm_params:
        print("No DSM processes found to plot.")
        return

    from ipywidgets import Dropdown, HBox, VBox, Layout, Button
    from IPython.display import display

    time_items = mfa_system_results.IndexTable.Classification["Time"].Items
    element_items = mfa_system_results.Elements

    process_options = {
        p.Name: p.ID for p in mfa_system_results.ProcessList if p.ID in dsm_params
    }
    if not process_options:
        print("No DSM processes found in the system.")
        return

    # Build process name lookup for descriptive flow/stock names
    process_name_by_id = {p.ID: p.Name for p in mfa_system_results.ProcessList}

    def _flow_display_name(flow):
        """Create descriptive flow name: 'Source -> Destination'."""
        src = process_name_by_id.get(flow.P_Start, f"P{flow.P_Start}")
        dst = process_name_by_id.get(flow.P_End, f"P{flow.P_End}")
        return f"{src} \u2192 {dst}"

    fig = go.FigureWidget(
        make_subplots(
            rows=1,
            cols=3,
            subplot_titles=("Input Flows", "Stock Evolution", "Output Flows"),
            horizontal_spacing=0.08,
        )
    )

    def update_plot(process_name, element):
        process_id = process_options[process_name]
        fig.data = []
        element_index = element_items.index(element)
        _scale, _unit = get_mass_display()

        # 1. INPUT FLOWS (Left Panel) - Stacked Area Chart
        input_flows = [
            f for f in mfa_system_results.FlowDict.values() if f.P_End == process_id
        ]
        if input_flows:
            for i, flow in enumerate(input_flows):
                display_name = _flow_display_name(flow)
                fig.add_trace(
                    go.Scatter(
                        x=time_items,
                        y=flow.Values[:, element_index] * _scale,
                        name=display_name,
                        stackgroup="input",
                        fill="tonexty" if i > 0 else "tozeroy",
                        mode="lines",
                        line=dict(width=0.5),
                        hovertemplate=f"<b>{display_name}</b><br>Year: %{{x}}<br>{element}: %{{y:.3f}} {_unit}<extra></extra>",
                    ),
                    row=1,
                    col=1,
                )

        # 2. STOCK EVOLUTION (Middle Panel) - Line Chart
        stock_name = f"S_{process_id}"
        if stock_name in mfa_system_results.StockDict:
            stock = mfa_system_results.StockDict[stock_name]
            stock_display = process_name
            fig.add_trace(
                go.Scatter(
                    x=time_items,
                    y=stock.Values[:, element_index] * _scale,
                    name=f"Stock: {stock_display}",
                    mode="lines",
                    line=dict(width=3, color="#2E86AB"),
                    hovertemplate=f"<b>Stock: {stock_display}</b><br>Year: %{{x}}<br>{element}: %{{y:.3f}} {_unit}<extra></extra>",
                ),
                row=1,
                col=2,
            )

        # 3. OUTPUT FLOWS (Right Panel) - Stacked Area Chart
        output_flows = [
            f for f in mfa_system_results.FlowDict.values() if f.P_Start == process_id
        ]
        if output_flows:
            for i, flow in enumerate(output_flows):
                display_name = _flow_display_name(flow)
                fig.add_trace(
                    go.Scatter(
                        x=time_items,
                        y=flow.Values[:, element_index] * _scale,
                        name=display_name,
                        stackgroup="output",
                        fill="tonexty" if i > 0 else "tozeroy",
                        mode="lines",
                        line=dict(width=0.5),
                        hovertemplate=f"<b>{display_name}</b><br>Year: %{{x}}<br>{element}: %{{y:.3f}} {_unit}<extra></extra>",
                    ),
                    row=1,
                    col=3,
                )

        # Update layout using publication style guide for subplots
        layout_config = get_publication_layout(
            custom_title=f"DSM - Inflow, Stock, and Outflow - {process_name} ({element.upper()})",
            show_grid=True,
            scientific_y=True,
        )
        apply_theme(layout_config)
        # 3-panel subplot needs a wider canvas; override theme width/height/margin
        _t = get_active_theme()
        layout_config["width"] = 1400
        layout_config["height"] = 500
        layout_config["margin"] = {
            "t": 80,
            "b": 150 if _t["legend_below"] else 80,
            "l": 60,
            "r": 30,
        }

        # Pop axis styles and apply them globally to all subplots
        xaxis_style = layout_config.pop("xaxis")
        yaxis_style = layout_config.pop("yaxis")
        fig.update_layout(**layout_config)
        fig.update_xaxes(title_text="Year", **xaxis_style)
        fig.update_yaxes(title_text=f"{element} (Mg)", **yaxis_style)

        # Restore subplot titles which can be overwritten by update_layout
        fig.update_layout(
            annotations=[
                dict(
                    text="Input Flows",
                    x=0.12,
                    y=1.05,
                    xref="paper",
                    yref="paper",
                    showarrow=False,
                    font=dict(size=FONT_SIZE["axis_title"]),
                ),
                dict(
                    text="Stock Evolution",
                    x=0.5,
                    y=1.05,
                    xref="paper",
                    yref="paper",
                    showarrow=False,
                    font=dict(size=FONT_SIZE["axis_title"]),
                ),
                dict(
                    text="Output Flows",
                    x=0.88,
                    y=1.05,
                    xref="paper",
                    yref="paper",
                    showarrow=False,
                    font=dict(size=FONT_SIZE["axis_title"]),
                ),
            ]
        )

    process_dropdown = Dropdown(
        options=list(process_options.keys()),
        description="DSM Process:",
        style={"description_width": "120px"},
        layout=Layout(width="300px"),
    )
    element_dropdown = Dropdown(
        options=element_items,
        value=element_items[0],
        description="Element:",
        style={"description_width": "80px"},
        layout=Layout(width="200px"),
    )
    export_button = Button(
        description="Export Plot",
        button_style="info",
        tooltip="Export current plot as PNG",
    )

    def export_plot():
        try:
            paths = export_figure(
                fig,
                "dsm_process_dynamics",
                formats=["png", "svg"],
                quality="publication",
                size="large",
                timestamp=False,
            )
            print(f"✅ Exported: {', '.join(paths)}")
        except Exception as e:
            print(f"⚠️ Export failed: {e}")

    export_button.on_click(lambda b: export_plot())

    controls = HBox(
        [
            VBox([process_dropdown, element_dropdown], layout=Layout(width="300px")),
            VBox([export_button], layout=Layout(width="200px")),
        ],
        layout=Layout(justify_content="space-between"),
    )

    def _on_change(change):
        update_plot(process_dropdown.value, element_dropdown.value)

    process_dropdown.observe(_on_change, "value")
    element_dropdown.observe(_on_change, "value")

    display(controls)
    display(fig)
    update_plot(process_dropdown.value, element_dropdown.value)


def plot_dsm_stock_details(mfa_system_results, dsm_params, dsm_details):
    """Creates an enhanced, stacked line diagram of DSM stock evolution.

    This function visualizes the evolution of a Dynamic Stock Model (DSM)
    stock, separating the decay of the initial stock from the accumulation
    of new stock due to inflows. It provides a detailed view of how different
    application categories contribute to the overall stock over time.

    Parameters
    ----------
    mfa_system_results : odym.MFAsystem
        The solved MFA system object, containing the results of the MFA
        calculation, including all flows and stocks over the simulation period.
    dsm_params : dict
        A dictionary containing the configuration parameters for all DSM
        processes in the model. Used to identify relevant processes.
    dsm_details : dict
        A dictionary containing detailed results from the DSM calculations,
        including initial stock time series, inflow stock time series by
        category, category names, and mean lifetimes.

    Notes
    -----
    The plot is interactive, allowing the user to select the DSM process and
    the element to display. It also includes a button to export the current
    view as a high-resolution PNG image.
    """
    if not dsm_params:
        print("No DSM processes found to plot.")
        return

    from ipywidgets import Dropdown, HBox, VBox, Layout, Button
    from IPython.display import display

    time_items = mfa_system_results.IndexTable.Classification["Time"].Items
    element_items = mfa_system_results.Elements

    colors = {"initial_stock": "#ff7f0e"}

    fig = go.FigureWidget()

    def update_plot(process_id, element):
        if process_id not in dsm_details:
            print(f"No detailed results for process {process_id}")
            return

        element_index = element_items.index(element)
        details = dsm_details[process_id]

        with fig.batch_update():
            fig.data = []

            initial_stock_ts = details.get(
                "initial_stock_ts", np.zeros((len(time_items), len(element_items)))
            )
            inflow_stocks_material = details.get("inflow_stock_ts_by_cat", [])
            category_names = details.get("category_names", [])

            initial_stock_element = initial_stock_ts[:, element_index]
            _scale, _unit = get_mass_display()

            # Only add Initial Stock trace if there's actually any initial stock data
            # (i.e., not all zeros - which means Stock_Configuration doesn't use initial stock)
            if np.any(initial_stock_element > 1e-10):
                fig.add_trace(
                    go.Scatter(
                        x=time_items,
                        y=initial_stock_element * _scale,
                        mode="lines",
                        name="Initial Stock (Decaying)",
                        line=dict(
                            color=colors["initial_stock"], width=0.5, dash="dash"
                        ),
                        stackgroup="one",
                        fill="tozeroy",
                        hovertemplate=f"<b>Initial Stock</b><br>Year: %{{x}}<br>Mass: %{{y:.3f}} {_unit}<extra></extra>",
                    )
                )

            for i, stock_ts_material in enumerate(inflow_stocks_material):
                # stock_ts_material is (num_years, num_elements) — vintage composition
                # is already embedded via cohort-matrix weighting in the engine.
                stock_ts_element = stock_ts_material[:, element_index]
                category_display = category_names[i]

                fig.add_trace(
                    go.Scatter(
                        x=time_items,
                        y=stock_ts_element * _scale,
                        mode="lines",
                        name=category_display,
                        line=dict(width=0.5),
                        stackgroup="one",
                        fill="tonexty",
                        hovertemplate=f"<b>{category_display}</b><br>Year: %{{x}}<br>Mass: %{{y:.3f}} {_unit}<extra></extra>",
                    )
                )

            process_name = next(
                (p.Name for p in mfa_system_results.ProcessList if p.ID == process_id),
                f"Process {process_id}",
            )
            layout_config = get_publication_layout(
                custom_title=f"DSM - In-Use Stock by Cohort - {process_name} ({element.upper()})",
                x_title="Year",
                y_title=y_label(element.upper()),
                show_grid=True,
                scientific_y=True,
            )
            apply_theme(layout_config)
            fig.update_layout(**layout_config)

    # Dropdown shows process names but yields the process ID as its value, so
    # update_plot() still receives the integer ID it expects.
    process_name_by_id = {p.ID: p.Name for p in mfa_system_results.ProcessList}
    process_dropdown = Dropdown(
        options=[
            (process_name_by_id.get(pid, f"Process {pid}"), pid)
            for pid in dsm_params.keys()
        ],
        description="DSM Process:",
        style={"description_width": "120px"},
    )
    element_dropdown = Dropdown(
        options=element_items,
        value=element_items[0],
        description="Element:",
        style={"description_width": "80px"},
    )
    export_button = Button(
        description="Export Plot",
        button_style="info",
        tooltip="Export current plot as PNG",
    )

    def export_plot():
        try:
            paths = export_figure(
                fig,
                "dsm_stock_analysis",
                formats=["png", "svg"],
                quality="publication",
                size="large",
                timestamp=False,
            )
            print(f"✅ Exported: {', '.join(paths)}")
        except Exception as e:
            print(f"⚠️ Export failed: {e}")

    export_button.on_click(lambda b: export_plot())

    controls = HBox(
        [
            VBox([process_dropdown, element_dropdown], layout=Layout(width="300px")),
            VBox([export_button], layout=Layout(width="150px")),
        ],
        layout=Layout(justify_content="space-between"),
    )

    def _on_change(change):
        update_plot(process_dropdown.value, element_dropdown.value)

    process_dropdown.observe(_on_change, "value")
    element_dropdown.observe(_on_change, "value")

    display(controls)
    display(fig)
    update_plot(process_dropdown.value, element_dropdown.value)


def plot_dsm_stock_publication(
    mfa_system_results,
    dsm_details,
    process_id=None,
    element="material",
    category_colors=None,
    policy_year=2075,
    enable_export=True,
):
    """Publication-ready static stacked-area plot of DSM in-use stock by cohort category.

    Renders the cohort breakdown for a single DSM process in JIE single-column
    format: theme mass scale (Gg in JIE, Mg in exploratory), no title, inside legend, optional policy year vline.

    Parameters
    ----------
    mfa_system_results : odym.MFAsystem
        The solved MFA system object.
    dsm_details : dict
        Per-process DSM results from ``solver_info``-style dict. Keys are process
        IDs; values contain ``"inflow_stock_ts_by_cat"``, ``"category_names"``,
        ``"initial_stock_ts"``.
    process_id : int or None
        DSM process to plot. Defaults to the first key in ``dsm_details``.
    element : str
        Element name to display. Defaults to ``"material"``.
    category_colors : list[str] or None
        Explicit hex color per category (darkest first = bottom of stack).
        Defaults to a neutral blue-grey gradient.
    policy_year : int or None
        Year at which a vertical reference line is drawn (black dashed). Pass
        ``None`` to omit. Default: 2075.
    enable_export : bool
        Show PNG/SVG export button. Default: True.
    """
    if not dsm_details:
        print("⚠️  No DSM detail data available.")
        return

    if process_id is None:
        process_id = next(iter(dsm_details))

    if process_id not in dsm_details:
        print(f"⚠️  Process {process_id} not in dsm_details.")
        return

    element_items = mfa_system_results.Elements
    time_items = mfa_system_results.IndexTable.Classification["Time"].Items

    if element not in element_items:
        print(f"⚠️  Element '{element}' not available. Choose from: {element_items}")
        return
    elem_idx = element_items.index(element)

    details = dsm_details[process_id]
    initial_stock_ts = details.get(
        "initial_stock_ts", np.zeros((len(time_items), len(element_items)))
    )
    inflow_stocks = details.get("inflow_stock_ts_by_cat", [])
    category_names = details.get("category_names", [])

    process_name = next(
        (p.Name for p in mfa_system_results.ProcessList if p.ID == process_id),
        f"Process {process_id}",
    )

    # Y-scale: use theme mass scale (Gg in JIE, Mg in exploratory)
    _Y_SCALE, _Y_UNIT = get_mass_display()

    # Default color palette: dark-to-light blue-grey (bottom = darkest)
    _DEFAULT_COLORS = ["#2C5282", "#4A7C9E", "#7AADC4", "#A8C4DC", "#D0E4F0", "#EBF4FA"]
    colors = category_colors if category_colors is not None else _DEFAULT_COLORS

    fig = go.Figure()

    # Initial stock (decaying) — only if non-zero
    init_elem = initial_stock_ts[:, elem_idx] * _Y_SCALE
    if np.any(init_elem > 1e-10):
        fig.add_trace(
            go.Scatter(
                x=time_items,
                y=init_elem,
                mode="lines",
                name="Initial Stock (Decaying)",
                stackgroup="dsm",
                line=dict(color="#999999", width=0.8, dash="dash"),
                fillcolor="#CCCCCC",
                hovertemplate=(
                    "<b>Initial Stock (Decaying)</b><br>"
                    f"Year: %{{x}}<br>%{{y:.3f}} {_Y_UNIT}<extra></extra>"
                ),
            )
        )

    for i, stock_ts in enumerate(inflow_stocks):
        cat_name = category_names[i] if i < len(category_names) else f"Category {i + 1}"
        col = colors[i % len(colors)]
        elem_vals = stock_ts[:, elem_idx] * _Y_SCALE
        fig.add_trace(
            go.Scatter(
                x=time_items,
                y=elem_vals,
                mode="lines",
                name=cat_name,
                stackgroup="dsm",
                line=dict(color=col, width=0.8),
                fillcolor=col,
                opacity=0.85,
                hovertemplate=(
                    f"<b>{cat_name}</b><br>"
                    f"Year: %{{x}}<br>%{{y:.3f}} {_Y_UNIT}<extra></extra>"
                ),
            )
        )

    # Policy reference line
    if policy_year is not None:
        fig.add_vline(
            x=policy_year,
            line=dict(color="black", dash="dash", width=0.8),
            annotation_text=f"{policy_year}",
            annotation_position="top right",
            annotation_font_size=9,
        )

    layout_config = get_publication_layout(
        custom_title="",
        x_title="Year",
        y_title=f"In-Use Stock ({_Y_UNIT})",
        show_grid=True,
        y_range=[0, None],
    )
    apply_theme(layout_config)

    # Publication font overrides (10pt axis/tick, 9pt legend)
    layout_config["font"] = dict(size=10, family="Arial, sans-serif")
    layout_config["xaxis"]["title"]["font"] = dict(size=10)
    layout_config["yaxis"]["title"]["font"] = dict(size=10)
    layout_config["xaxis"]["tickfont"] = dict(size=10)
    layout_config["yaxis"]["tickfont"] = dict(size=10)
    layout_config["yaxis"]["tickformat"] = ","
    layout_config["yaxis"]["exponentformat"] = "none"

    # Legend inside bottom-right, horizontal, 9pt
    layout_config["legend"] = dict(
        x=0.98,
        y=0.04,
        xanchor="right",
        yanchor="bottom",
        orientation="h",
        font=dict(size=9),
        bgcolor="rgba(255,255,255,0.85)",
        bordercolor="#CCCCCC",
        borderwidth=1,
    )

    # No title in JIE mode
    layout_config["title"] = dict(text="")

    fig.update_layout(**layout_config)

    if not enable_export:
        display(fig)
        return

    export_btn = Button(
        description="Export PNG/SVG",
        button_style="success",
        icon="download",
        layout=Layout(width="160px"),
    )

    def _do_export(b):
        try:
            paths = export_figure(
                fig,
                f"dsm_stock_publication_{process_name.replace(' ', '_')}_{element}",
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


def plot_fomp_stock_details(mfa_system_results, fomp_params, comparison_process=None):
    """Creates detailed stock evolution plots specifically for FOMP processes.

    Publication-ready interactive plot (JIE single-column format). Values are
    scaled to 10⁶ Mg C on the y-axis. An optional second trajectory can be
    overlaid for scenario comparison.

    Parameters
    ----------
    mfa_system_results : odym.MFAsystem
        The solved MFA system object containing all flows and stocks.
    fomp_params : dict
        Configuration parameters for all FOMP processes (keyed by process ID).
    comparison_process : int or str or None
        Optional second FOMP process to overlay for direct comparison.
        Accepts a process ID (int) or process name (str). When provided, its
        TC stock is drawn as a steelblue solid line behind the primary traces.
    """
    if not fomp_params:
        print("No FOMP processes found to plot.")
        return

    from ipywidgets import Dropdown, HBox, VBox, Layout, Button
    from IPython.display import display

    time_items = mfa_system_results.IndexTable.Classification["Time"].Items
    element_items = mfa_system_results.Elements

    # Publication line style scheme (JIE single-column)
    _PUB = {
        "stock": dict(color="black", width=2, dash="solid"),
        "input": dict(color="grey", width=2, dash="dash"),
        "output": dict(color="darkred", width=2, dash="dot"),
        "comparison": dict(color="steelblue", width=1.5, dash="solid"),
    }
    # Resolve comparison process ID once (outside update_plot)
    _cmp_id = None
    _cmp_name = None
    if comparison_process is not None:
        if isinstance(comparison_process, int):
            _cmp_id = comparison_process
        else:
            _cmp_id = next(
                (
                    p.ID
                    for p in mfa_system_results.ProcessList
                    if p.Name == comparison_process
                ),
                None,
            )
        if _cmp_id is not None:
            _cmp_name = next(
                (p.Name for p in mfa_system_results.ProcessList if p.ID == _cmp_id),
                str(_cmp_id),
            )

    fig = go.FigureWidget()

    def update_plot(process_id, element, show_cumulative):
        element_index = element_items.index(element)

        # --- Pass 1: collect raw data to determine display scale ---
        stock_obj = mfa_system_results.StockDict.get(f"S_{process_id}")
        if stock_obj is None:
            print(f"No stock data for process {process_id}")
            return
        stock_raw = stock_obj.Values[:, element_index]

        inflow_ts = sum(
            f.Values[:, element_index]
            for f in mfa_system_results.FlowDict.values()
            if f.P_End == process_id
        )
        outflow_ts = sum(
            f.Values[:, element_index]
            for f in mfa_system_results.FlowDict.values()
            if f.P_Start == process_id
        )

        _raw_all = [
            stock_raw,
            np.cumsum(inflow_ts)
            if show_cumulative == "Cumulative Values"
            else inflow_ts,
            np.cumsum(outflow_ts)
            if show_cumulative == "Cumulative Values"
            else outflow_ts,
        ]
        if _cmp_id is not None:
            cmp_obj_raw = mfa_system_results.StockDict.get(f"S_{_cmp_id}")
            if cmp_obj_raw is not None:
                _raw_all.append(cmp_obj_raw.Values[:, element_index])

        _s, _unit_str = get_mass_display()
        is_carbon = element in ("TC", "CC")
        axis_unit = f"{_unit_str} C" if is_carbon else _unit_str
        _ylabel_str = y_label(element.upper())

        process_name = next(
            (p.Name for p in mfa_system_results.ProcessList if p.ID == process_id),
            f"Process {process_id}",
        )

        # --- Pass 2: build figure with computed scale ---
        with fig.batch_update():
            fig.data = []

            # Optional comparison overlay
            if _cmp_id is not None:
                cmp_stock_obj = mfa_system_results.StockDict.get(f"S_{_cmp_id}")
                if cmp_stock_obj is not None:
                    fig.add_trace(
                        go.Scatter(
                            x=time_items,
                            y=cmp_stock_obj.Values[:, element_index] * _s,
                            mode="lines",
                            name=f"Stock \u2013 {_cmp_name}",
                            line=_PUB["comparison"],
                            hovertemplate=(
                                f"<b>Stock \u2013 {_cmp_name}</b><br>"
                                f"Year: %{{x}}<br>Value: %{{y:.3f}} {axis_unit}<extra></extra>"
                            ),
                        )
                    )

            stock_label = (
                f"Stock \u2013 {process_name}"
                if _cmp_id is not None
                else "Carbon Stock"
            )
            fig.add_trace(
                go.Scatter(
                    x=time_items,
                    y=stock_raw * _s,
                    mode="lines",
                    name=stock_label,
                    line=_PUB["stock"],
                    hovertemplate=(
                        f"<b>Stock</b><br>Year: %{{x}}<br>Value: %{{y:.3f}} {axis_unit}<extra></extra>"
                    ),
                )
            )

            if show_cumulative == "Cumulative Values":
                fig.add_trace(
                    go.Scatter(
                        x=time_items,
                        y=np.cumsum(inflow_ts) * _s,
                        mode="lines",
                        name="Cumulative Input",
                        line=_PUB["input"],
                        hovertemplate=f"<b>Cumulative Input</b><br>Year: %{{x}}<br>Value: %{{y:.3f}} {axis_unit}<extra></extra>",
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=time_items,
                        y=np.cumsum(outflow_ts) * _s,
                        mode="lines",
                        name="Cumulative Carbon Emissions",
                        line=_PUB["output"],
                        hovertemplate=f"<b>Cumulative Carbon Emissions</b><br>Year: %{{x}}<br>Value: %{{y:.3f}} {axis_unit}<extra></extra>",
                    )
                )
            else:
                fig.add_trace(
                    go.Scatter(
                        x=time_items,
                        y=inflow_ts * _s,
                        mode="lines",
                        name="Annual Input",
                        line=_PUB["input"],
                        hovertemplate=f"<b>Annual Input</b><br>Year: %{{x}}<br>Value: %{{y:.3f}} {axis_unit}<extra></extra>",
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=time_items,
                        y=outflow_ts * _s,
                        mode="lines",
                        name="Annual Carbon Emissions",
                        line=_PUB["output"],
                        hovertemplate=f"<b>Annual Carbon Emissions</b><br>Year: %{{x}}<br>Value: %{{y:.3f}} {axis_unit}<extra></extra>",
                    )
                )

            _y_upper = (
                math.ceil(
                    (
                        max(
                            float(np.nanmax(np.abs(v)))
                            for v in _raw_all
                            if np.any(np.isfinite(v))
                        )
                        * _s
                    )
                    * 2
                )
                / 2
                + 0.5
            )
            layout_config = get_publication_layout(
                custom_title=f"FOMP - First-Order Decay Stock - {process_name}",
                x_title="Year",
                y_title=_ylabel_str,
                show_grid=True,
                y_range=[0, _y_upper],
            )
            apply_theme(layout_config)
            fig.update_layout(**layout_config)

    def export_plot():
        try:
            current_process_name = process_dropdown.value
            current_element = element_dropdown.value
            filename = (
                f"fomp_{current_process_name.replace(' ', '_')}_{current_element}"
            )
            paths = export_figure(
                fig,
                filename,
                formats=["png", "svg"],
                quality="publication",
                size="large",
                timestamp=False,
            )
            print(f"✅ Exported: {', '.join(paths)}")
        except Exception as e:
            print(f"❌ Export failed: {e}")

    # Build name→ID mapping, excluding the boundary process (ID 0)
    process_options = {
        p.Name: p.ID
        for p in mfa_system_results.ProcessList
        if p.ID in fomp_params and p.ID != 0
    }
    if not process_options:
        print("⚠️  No FOMP processes found in ProcessList.")
        return

    # Default element: prefer TC/CC, otherwise first in list
    from engine.element_utils import get_carbon_element_name

    _tc = get_carbon_element_name(element_items, default=element_items[0])

    process_dropdown = Dropdown(
        options=list(process_options.keys()),
        description="FOMP Process:",
        style={"description_width": "120px"},
        layout=Layout(width="300px"),
    )
    element_dropdown = Dropdown(
        options=element_items,
        value=_tc,
        description="Element:",
        style={"description_width": "80px"},
        layout=Layout(width="200px"),
    )
    cumulative_checkbox = Dropdown(
        options=["Annual Values", "Cumulative Values"],
        value="Annual Values",
        description="Display:",
        style={"description_width": "80px"},
        layout=Layout(width="200px"),
    )
    export_button = Button(
        description="Export PNG/PDF",
        button_style="success",
        icon="download",
        layout=Layout(width="140px"),
    )
    export_button.on_click(lambda b: export_plot())

    ui = VBox(
        [
            HBox([process_dropdown, element_dropdown, cumulative_checkbox]),
            HBox([export_button]),
        ]
    )

    def _on_change(change):
        update_plot(
            process_options[process_dropdown.value],
            element_dropdown.value,
            cumulative_checkbox.value,
        )

    process_dropdown.observe(_on_change, "value")
    element_dropdown.observe(_on_change, "value")
    cumulative_checkbox.observe(_on_change, "value")

    display(ui)
    display(fig)
    update_plot(
        process_options[process_dropdown.value],
        element_dropdown.value,
        cumulative_checkbox.value,
    )


def plot_fomp_stock_comparison(
    mfa_system_results,
    fomp_params,
    element=None,
    fomp_details=None,
    pool_colors=None,
    policy_year=2075,
    enable_export=True,
):
    """Overlay TC stock trajectories of all FOMP processes on one publication figure.

    Produces a JIE-compatible static Plotly figure showing per-pool carbon stock
    evolution (stacked labile/recalcitrant areas) and cumulative output (dashed
    lines) for every FOMP process.

    Parameters
    ----------
    mfa_system_results : odym.MFAsystem
    fomp_params : dict
        FOMP parameters keyed by process ID.
    element : str or None
        Element to plot. Defaults to TC/CC fallback.
    fomp_details : dict or None
        ``solver_info["fomp_details"]`` — enables pool breakdown and cumulative
        output lines. Falls back to single-line StockDict view when None.
    pool_colors : list[tuple[str, str]] or None
        Per-process ``(dark, light)`` hex pairs for recalcitrant/labile areas.
        Defaults to a two-process neutral scheme matching the case-study Sankey.
    policy_year : int or None
        Year for vertical reference line (black dashed). Pass None to omit.
    enable_export : bool
        Show export button. Default: True.
    """
    if not fomp_params:
        print("No FOMP processes found to plot.")
        return

    element_items = mfa_system_results.Elements
    time_items = mfa_system_results.IndexTable.Classification["Time"].Items

    # Element selection: prefer TC/CC
    if element is None:
        element = next(
            (e for e in ("TC", "CC") if e in element_items), element_items[0]
        )
    if element not in element_items:
        print(f"⚠️  Element '{element}' not in system — available: {element_items}")
        return
    elem_idx = element_items.index(element)

    # Use theme mass scale (Gg in JIE, Mg in exploratory)
    _Y_SCALE, _Y_UNIT_BASE = get_mass_display()
    _Y_UNIT = f"{_Y_UNIT_BASE} C"

    # Default two-process color scheme:
    #   Process 1 = SOC Wheat Straw: amber/yellow
    #   Process 2 = SOC Biochar:     steel blue
    _DEFAULT_COLORS = ["#D4A017", "#1A6FAA", "#4A6741", "#6B5B7B", "#7A4F3A"]
    colors = (
        pool_colors if pool_colors is not None else [(c, c) for c in _DEFAULT_COLORS]
    )

    # Gather FOMP processes in system order
    procs = [
        p for p in mfa_system_results.ProcessList if p.ID in fomp_params and p.ID != 0
    ]
    if not procs:
        print("⚠️  No FOMP processes found in ProcessList.")
        return

    use_pools = fomp_details is not None

    fig = go.Figure()

    for i, proc in enumerate(procs):
        color_dark = colors[i % len(colors)][0]
        pid = proc.ID

        if use_pools and fomp_details and pid in fomp_details:
            detail = fomp_details[pid]
            tc_rec = np.array(
                detail.get("stock_tc_recalcitrant", [0] * len(time_items))
            )
            tc_lab = np.array(detail.get("stock_tc_labile", [0] * len(time_items)))
            dec_rec = np.array(
                detail.get("decay_tc_recalcitrant", np.zeros(len(time_items)))
            )
            dec_lab = np.array(detail.get("decay_tc_labile", np.zeros(len(time_items))))
            tc_total = (tc_rec + tc_lab) * _Y_SCALE
            cum_out = np.cumsum(dec_rec + dec_lab) * _Y_SCALE

            # Stock as solid line
            fig.add_trace(
                go.Scatter(
                    x=time_items,
                    y=tc_total,
                    mode="lines",
                    name=f"{proc.Name} Stock",
                    line=dict(color=color_dark, width=1.8),
                    hovertemplate=(
                        f"<b>{proc.Name} Stock</b><br>"
                        f"Year: %{{x}}<br>%{{y:.2f}} {_Y_UNIT}<extra></extra>"
                    ),
                )
            )
            # Cumulative output as dashed line
            fig.add_trace(
                go.Scatter(
                    x=time_items,
                    y=cum_out,
                    mode="lines",
                    name=f"{proc.Name} Cumul. Output",
                    line=dict(color=color_dark, width=1.8, dash="dash"),
                    hovertemplate=(
                        f"<b>{proc.Name} Cumulative Output</b><br>"
                        f"Year: %{{x}}<br>%{{y:.2f}} {_Y_UNIT}<extra></extra>"
                    ),
                )
            )
        else:
            # Fallback: single total line from StockDict
            stock_obj = mfa_system_results.StockDict.get(f"S_{pid}")
            if stock_obj is None:
                continue
            y_vals = stock_obj.Values[:, elem_idx] * _Y_SCALE
            fig.add_trace(
                go.Scatter(
                    x=time_items,
                    y=y_vals,
                    mode="lines",
                    name=proc.Name,
                    line=dict(color=color_dark, width=1.8),
                    hovertemplate=(
                        f"<b>{proc.Name}</b><br>"
                        f"Year: %{{x}}<br>%{{y:.2f}} {_Y_UNIT}<extra></extra>"
                    ),
                )
            )

    # Policy reference line
    if policy_year is not None:
        fig.add_vline(
            x=policy_year,
            line=dict(color="black", dash="dash", width=0.8),
            annotation_text=str(policy_year),
            annotation_position="top right",
            annotation_font_size=9,
        )

    layout_config = get_publication_layout(
        custom_title="",
        x_title="Year",
        y_title=f"Carbon ({_Y_UNIT})",
        show_grid=True,
        y_range=[0, None],
    )
    apply_theme(layout_config)

    layout_config["title"] = dict(text="")
    layout_config["yaxis"]["tickformat"] = ","
    layout_config["yaxis"]["exponentformat"] = "none"

    # Legend directly below the plot, no extra gap
    layout_config["legend"] = dict(
        orientation="h",
        x=0.5,
        y=-0.12,
        xanchor="center",
        yanchor="top",
        font=dict(size=14),
        bgcolor="rgba(255,255,255,0.0)",
    )
    layout_config["margin"]["b"] = max(layout_config["margin"].get("b", 80), 100)

    fig.update_layout(**layout_config)

    if not enable_export:
        display(fig)
        return

    export_btn = Button(
        description="Export PNG/SVG",
        button_style="success",
        icon="download",
        layout=Layout(width="160px"),
    )

    def _do_export(b):
        try:
            paths = export_figure(
                fig,
                f"fomp_stock_comparison_{element}",
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


def plot_fomp_pool_breakdown(
    mfa_system_results, fomp_params, fomp_details, element=None
):
    """Two-panel plot: stacked pool stocks (top) and annual decay emissions per pool (bottom).

    The labile pool typically has a near-zero stock (fast turnover) but dominates
    annual carbon emissions. Showing both panels together reveals the full picture.
    Requires per-pool data from ``solver_info["fomp_details"]``.

    Parameters
    ----------
    mfa_system_results : odym.MFAsystem
    fomp_params : dict
        FOMP parameter dict keyed by process ID.
    fomp_details : dict
        ``solver_info["fomp_details"]`` — per-pool arrays keyed by process ID.
    element : str or None
        Element to display ('TC'/'CC' for carbon pools). Defaults to TC/CC fallback.
    """
    if not fomp_details:
        print("⚠️  No FOMP pool data available — run the solver first.")
        return

    time_items = mfa_system_results.IndexTable.Classification["Time"].Items
    element_items = mfa_system_results.Elements

    from engine.element_utils import get_carbon_element_name

    _tc_name = get_carbon_element_name(element_items)
    if element is None:
        element = _tc_name if _tc_name else element_items[0]
    use_tc = element in ("TC", "CC")

    procs = [
        p for p in mfa_system_results.ProcessList if p.ID in fomp_details and p.ID != 0
    ]
    if not procs:
        print("⚠️  No FOMP processes found in fomp_details.")
        return

    process_options = {p.Name: p.ID for p in procs}
    process_dropdown = Dropdown(
        options=list(process_options.keys()),
        description="Process:",
        style={"description_width": "80px"},
        layout=Layout(width="280px"),
    )

    _COLOR_LABILE = "#E69F00"
    _COLOR_RECALCITRANT = "#0072B2"

    fig = go.FigureWidget(
        make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.08,
            subplot_titles=["Pool Stocks", "Annual Decay Emissions"],
        )
    )

    def update_plot(process_name):
        process_id = process_options[process_name]
        d = fomp_details[process_id]

        if use_tc:
            s_lab = d["stock_tc_labile"]
            s_rec = d["stock_tc_recalcitrant"]
            e_lab = d["decay_tc_labile"]
            e_rec = d["decay_tc_recalcitrant"]
        else:
            s_lab = d["stock_labile"]
            s_rec = d["stock_recalcitrant"]
            # DM-level decay not stored separately — approximate from TC decay ratios
            e_lab = d["decay_tc_labile"]
            e_rec = d["decay_tc_recalcitrant"]

        _sc, _unit_base = get_mass_display()
        elem_label = "TC" if use_tc else "DM"
        unit_s = f"{_unit_base} C" if use_tc else _unit_base
        unit_e = (
            f"{_unit_base} C yr\u207b\u00b9"
            if use_tc
            else f"{_unit_base} yr\u207b\u00b9"
        )

        with fig.batch_update():
            fig.data = []

            # --- Row 1: stacked pool stocks ---
            fig.add_trace(
                go.Scatter(
                    x=time_items,
                    y=s_lab * _sc,
                    name="Labile Pool",
                    legendgroup="labile",
                    mode="lines",
                    fill="tozeroy",
                    line=dict(color=_COLOR_LABILE, width=1.5),
                    fillcolor="rgba(230,159,0,0.35)",
                    hovertemplate=f"<b>Labile Stock</b><br>Year: %{{x}}<br>%{{y:.4f}} {unit_s}<extra></extra>",
                ),
                row=1,
                col=1,
            )
            fig.add_trace(
                go.Scatter(
                    x=time_items,
                    y=(s_lab + s_rec) * _sc,
                    name="Recalcitrant Pool",
                    legendgroup="recalcitrant",
                    mode="lines",
                    fill="tonexty",
                    line=dict(color=_COLOR_RECALCITRANT, width=1.5),
                    fillcolor="rgba(0,114,178,0.35)",
                    hovertemplate=f"<b>Recalcitrant Stock</b><br>Year: %{{x}}<br>Total: %{{y:.4f}} {unit_s}<extra></extra>",
                ),
                row=1,
                col=1,
            )

            # --- Row 2: annual decay emissions — individual lines (not stacked) ---
            # Non-stacked so both pools are visible even when magnitudes differ greatly
            fig.add_trace(
                go.Scatter(
                    x=time_items,
                    y=e_lab * _sc,
                    name="Labile Pool",
                    legendgroup="labile",
                    showlegend=False,
                    mode="lines",
                    line=dict(color=_COLOR_LABILE, width=2, dash="solid"),
                    hovertemplate=f"<b>Labile Decay</b><br>Year: %{{x}}<br>%{{y:.4f}} {unit_e}<extra></extra>",
                ),
                row=2,
                col=1,
            )
            fig.add_trace(
                go.Scatter(
                    x=time_items,
                    y=e_rec * _sc,
                    name="Recalcitrant Pool",
                    legendgroup="recalcitrant",
                    showlegend=False,
                    mode="lines",
                    line=dict(color=_COLOR_RECALCITRANT, width=2, dash="dash"),
                    hovertemplate=f"<b>Recalcitrant Decay</b><br>Year: %{{x}}<br>%{{y:.4f}} {unit_e}<extra></extra>",
                ),
                row=2,
                col=1,
            )

            t = get_active_theme()
            fig.update_layout(
                title=dict(text=f"FOMP - First-Order Decay Pools - {process_name}")
                if t["show_title"]
                else {},
                width=t["width"],
                height=t["height"],
                margin=t["margin"],
                plot_bgcolor="white",
                paper_bgcolor="white",
                legend=dict(font=dict(size=t["font_legend"])),
                uirevision="constant",
            )
            if t["legend_below"]:
                fig.update_layout(
                    legend=dict(
                        orientation="h",
                        yanchor="top",
                        y=-0.12,
                        xanchor="center",
                        x=0.5,
                    )
                )
            grid = t["grid_color"]
            for row in (1, 2):
                fig.update_xaxes(
                    showgrid=True,
                    gridcolor=grid,
                    tickfont=dict(size=t["font_tick"]),
                    row=row,
                    col=1,
                )
            _tfmt = ".3~e" if t.get("scientific_y", True) else ","
            fig.update_yaxes(
                title_text=f"mass {elem_label} ({unit_s})",
                showgrid=True,
                gridcolor=grid,
                tickformat=_tfmt,
                title_font=dict(size=t["font_axis"]),
                tickfont=dict(size=t["font_tick"]),
                row=1,
                col=1,
            )
            fig.update_yaxes(
                title_text=f"mass {elem_label} ({unit_e})",
                showgrid=True,
                gridcolor=grid,
                tickformat=_tfmt,
                title_font=dict(size=t["font_axis"]),
                tickfont=dict(size=t["font_tick"]),
                row=2,
                col=1,
            )
            fig.update_xaxes(
                title_text="Year",
                title_font=dict(size=t["font_axis"]),
                row=2,
                col=1,
            )

    export_pool_btn = Button(
        description="Export PNG/SVG",
        button_style="success",
        icon="download",
        layout=Layout(width="160px"),
    )

    def _do_pool_export(b):
        try:
            proc_name = process_dropdown.value.replace(" ", "_")
            paths = export_figure(
                fig,
                f"fomp_pool_breakdown_{proc_name}",
                formats=["png", "svg"],
                quality="publication",
                size="large",
                timestamp=False,
            )
            print(f"✅ Exported: {', '.join(paths)}")
        except Exception as e:
            print(f"❌ Export failed: {e}")

    export_pool_btn.on_click(_do_pool_export)
    process_dropdown.observe(lambda c: update_plot(c["new"]), names="value")
    display(HBox([process_dropdown, export_pool_btn]))
    display(fig)
    update_plot(process_dropdown.value)


def plot_system_efficiency_metrics(mfa_system_results):
    """Creates interactive plots showing system efficiency metrics over time.

    This function allows for the visualization of key material efficiency
    indicators such as recycling rates, recovery rates, and overall material
    efficiency. Users can select the element and the specific metric to display,
    providing insights into the system's performance.

    Parameters
    ----------
    mfa_system_results : odym.MFAsystem
        The solved MFA system object, containing the results of the MFA
        calculation, including all flows and stocks over the simulation period.

    Notes
    -----
    The plot is interactive, allowing the user to select the element and the
    metric type (Recycling Rate, Recovery Rate, Material Efficiency).
    The y-axis for all metrics is set to a range of 0 to 100%.
    """
    time_items = mfa_system_results.IndexTable.Classification["Time"].Items
    element_items = mfa_system_results.Elements

    fig = go.FigureWidget()

    def update_plot(element, metric_type):
        element_index = element_items.index(element)

        with fig.batch_update():
            fig.data = []

            if metric_type == "Recycling Rate":
                # Calculate recycling rate for each year
                recycling_rates = []
                for year_idx in range(len(time_items)):
                    # Find flows that represent recycling (internal flows)
                    internal_flows = [
                        f
                        for f in mfa_system_results.FlowDict.values()
                        if f.P_Start != 0 and f.P_End != 0
                    ]  # Exclude external flows
                    total_internal_flow = sum(
                        f.Values[year_idx, element_index] for f in internal_flows
                    )

                    # Find total system throughput
                    total_throughput = sum(
                        f.Values[year_idx, element_index]
                        for f in mfa_system_results.FlowDict.values()
                    )

                    if total_throughput > 0:
                        recycling_rate = (total_internal_flow / total_throughput) * 100
                    else:
                        recycling_rate = 0
                    recycling_rates.append(recycling_rate)

                fig.add_trace(
                    go.Scatter(
                        x=time_items,
                        y=recycling_rates,
                        mode="lines",
                        name="Recycling Rate (%)",
                        line=dict(color="#1f77b4", width=3),
                    )
                )

                layout_config = get_publication_layout(
                    custom_title=f"System Recycling Rate ({element.upper()})",
                    x_title="Year",
                    y_title="Recycling Rate (%)",
                    show_grid=True,
                )
                fig.update_layout(**layout_config)
                fig.update_yaxes(range=[0, 100])

            elif metric_type == "Recovery Rate":
                # Calculate recovery rate (outputs / inputs)
                recovery_rates = []
                for year_idx in range(len(time_items)):
                    # Find external outputs (flows to environment/sinks)
                    external_outputs = [
                        f
                        for f in mfa_system_results.FlowDict.values()
                        if f.P_Start != 0 and f.P_End == 0
                    ]  # Internal to external
                    total_output = sum(
                        f.Values[year_idx, element_index] for f in external_outputs
                    )

                    # Find external inputs
                    external_inputs = [
                        f
                        for f in mfa_system_results.FlowDict.values()
                        if f.P_Start == 0 and f.P_End != 0
                    ]  # External to internal
                    total_input = sum(
                        f.Values[year_idx, element_index] for f in external_inputs
                    )

                    if total_input > 0:
                        recovery_rate = (total_output / total_input) * 100
                    else:
                        recovery_rate = 0
                    recovery_rates.append(recovery_rate)

                fig.add_trace(
                    go.Scatter(
                        x=time_items,
                        y=recovery_rates,
                        mode="lines",
                        name="Recovery Rate (%)",
                        line=dict(color="#E69F00", width=3),
                    )
                )

                layout_config = get_publication_layout(
                    custom_title=f"System Recovery Rate ({element.upper()})",
                    x_title="Year",
                    y_title="Recovery Rate (%)",
                    show_grid=True,
                )
                fig.update_layout(**layout_config)
                fig.update_yaxes(range=[0, 100])

            elif metric_type == "Material Efficiency":
                # Calculate material efficiency (useful output / total input)
                efficiency_rates = []
                for year_idx in range(len(time_items)):
                    # Find useful outputs (e.g., to food, products)
                    useful_outputs = [
                        f
                        for f in mfa_system_results.FlowDict.values()
                        if f.P_Start != 0
                        and f.P_End == 0
                        and any(
                            keyword in getattr(f, "DescriptiveName", f.Name).lower()
                            for keyword in ["food", "product", "use"]
                        )
                    ]
                    total_useful = sum(
                        f.Values[year_idx, element_index] for f in useful_outputs
                    )

                    # Find total inputs
                    total_input = sum(
                        f.Values[year_idx, element_index]
                        for f in mfa_system_results.FlowDict.values()
                        if f.P_Start == 0 and f.P_End != 0
                    )

                    if total_input > 0:
                        efficiency = (total_useful / total_input) * 100
                    else:
                        efficiency = 0
                    efficiency_rates.append(efficiency)

                fig.add_trace(
                    go.Scatter(
                        x=time_items,
                        y=efficiency_rates,
                        mode="lines",
                        name="Material Efficiency (%s)",
                        line=dict(color="#CC79A7", width=3),
                    )
                )

                layout_config = get_publication_layout(
                    custom_title=f"Material Efficiency ({element.upper()})",
                    x_title="Year",
                    y_title="Efficiency (%)",
                    show_grid=True,
                )
                fig.update_layout(**layout_config)
                fig.update_yaxes(range=[0, 100])

    # Create widgets
    element_dropdown = Dropdown(
        options=element_items, value=element_items[0], description="Element:"
    )
    metric_dropdown = Dropdown(
        options=["Recycling Rate", "Recovery Rate", "Material Efficiency"],
        value="Recycling Rate",
        description="Metric:",
    )

    def _on_change(change):
        update_plot(element_dropdown.value, metric_dropdown.value)

    element_dropdown.observe(_on_change, "value")
    metric_dropdown.observe(_on_change, "value")

    export_btn = Button(
        description="Export PNG/SVG",
        button_style="success",
        icon="download",
        layout=Layout(width="160px"),
    )

    def _do_export(b):
        try:
            name = f"efficiency_metrics_{element_dropdown.value}_{metric_dropdown.value}".replace(
                " ", "_"
            )
            paths = export_figure(
                fig, name, formats=["png", "svg"], quality="publication", size="large"
            )
            print(f"✅ Exported: {', '.join(paths)}")
        except Exception as e:
            print(f"❌ Export failed: {e}")

    export_btn.on_click(_do_export)

    display(HBox([element_dropdown, metric_dropdown, export_btn]))
    display(fig)
    update_plot(element_dropdown.value, metric_dropdown.value)


def plot_stock_overview(mfa_system_results, dsm_params=None, fomp_params=None):
    """Plots the total stock evolution for all elements in the system.

    This function creates a single, non-interactive plot showing the time-series
    of the total aggregated stock for each element across all processes.
    It provides a high-level overview of how the total material stock
    (for each element) changes within the entire system over the simulation period.

    Parameters
    ----------
    mfa_system_results : odym.MFAsystem
        The solved MFA system object containing all calculated data.
    dsm_params : dict, optional
        Unused in this function, but kept for API consistency with other
        plotting functions in this module. Defaults to None.
    fomp_params : dict, optional
        Unused in this function, but kept for API consistency with other
        plotting functions in this module. Defaults to None.

    Notes
    -----
    This plot is non-interactive and displays all elements simultaneously.
    The `dsm_params` and `fomp_params` are included for API consistency
    but do not influence the plot generated by this function.
    """
    from plotly.subplots import make_subplots

    time_items = mfa_system_results.IndexTable.Classification["Time"].Items
    element_items = mfa_system_results.Elements

    # Create a single subplot for stock evolution
    fig = make_subplots(
        rows=1,
        cols=1,
        subplot_titles=("Total Stock Evolution by Element"),
    )

    _scale, _unit = get_mass_display()

    # Plot total stock evolution for all elements
    for i, element in enumerate(element_items):
        element_index = element_items.index(element)
        total_stock = np.zeros(len(time_items))

        for stock_name in mfa_system_results.StockDict.keys():
            if stock_name.startswith("S_"):
                stock_obj = mfa_system_results.StockDict[stock_name]
                total_stock += stock_obj.Values[:, element_index]

        fig.add_trace(
            go.Scatter(
                x=time_items,
                y=total_stock * _scale,
                mode="lines",
                name=f"Total {element.upper()}",
                line=dict(width=3),
                marker=dict(size=4),
            ),
            row=1,
            col=1,
        )

    # Update layout
    layout_config = get_publication_layout(
        custom_title="Total Stocks by Element",
        x_title="Year",
        y_title=y_label("Material"),
        show_grid=True,
        size="medium",
    )
    fig.update_layout(**layout_config)

    export_btn = Button(
        description="Export PNG/SVG",
        button_style="success",
        icon="download",
        layout=Layout(width="160px"),
    )

    def _do_export(b):
        try:
            paths = export_figure(
                fig,
                "stock_overview",
                formats=["png", "svg"],
                quality="publication",
                size="medium",
            )
            print(f"✅ Exported: {', '.join(paths)}")
        except Exception as e:
            print(f"❌ Export failed: {e}")

    export_btn.on_click(_do_export)
    display(export_btn)
    fig.show()


def plot_process_dynamics(
    mfa_system_results,
    process_definitions,
    color_manager: Optional[ElementColorManager] = None,
    enable_export: bool = True,
):
    """Creates three side-by-side line charts showing the dynamics of a process.

    This function visualizes the time-series evolution of inflow, stock, and
    outflow for a selected process. It uses process type metadata from the
    `process_definitions` DataFrame to generate more informative subplot titles.
    Now supports element-agnostic coloring and publication-quality export.

    Parameters
    ----------
    mfa_system_results : odym.MFAsystem
        The solved MFA system object, containing the results of the MFA
        calculation, including all flows and stocks over the simulation period.
    process_definitions : pd.DataFrame
        A Pandas DataFrame loaded from the '2_1_Definition_Processes' sheet
        of the input Excel file. It contains metadata about each process,
        including a 'Process_Type' column used for smart title generation.
    color_manager : ElementColorManager, optional
        Dynamic color manager for element colors. If None, creates one from
        mfa_system_results.Elements. Defaults to None.
    enable_export : bool, optional
        If True, adds an export button for saving publication-quality figures.
        Defaults to True.

    Notes
    -----
    The plot is interactive, allowing the user to select the process and
    the element to display. If the 'Process_Type' column is not found in
    `process_definitions`, a warning is issued, and generic titles are used.
    Processes without an explicit stock are plotted with a flat line at zero.

    Examples
    --------
    >>> # Basic usage
    >>> plot_process_dynamics(mfa_results, process_defs)

    >>> # With color-blind friendly colors
    >>> color_mgr = ElementColorManager(elements, color_scheme='colorblind')
    >>> plot_process_dynamics(mfa_results, process_defs, color_manager=color_mgr)
    """
    from plotly.subplots import make_subplots

    PROCESS_TYPE_COLUMN_NAME = "Process_Type"
    has_type_column = PROCESS_TYPE_COLUMN_NAME in process_definitions.columns
    if not has_type_column:
        print(
            f"Warning: Column '{PROCESS_TYPE_COLUMN_NAME}' not found. Smart titles disabled."
        )

    process_options = {p.Name: p.ID for p in mfa_system_results.ProcessList}
    if not process_options:
        print("No processes found to plot.")
        return

    element_items = [e.lower() for e in mfa_system_results.Elements]
    time_axis = mfa_system_results.IndexTable.Classification["Time"].Items

    # Create color manager if not provided
    if color_manager is None:
        color_manager = ElementColorManager(element_items)

    fig = go.FigureWidget(
        make_subplots(
            rows=1,
            cols=3,
            subplot_titles=("Inflow", "Stock (S)", "Outflow"),
            horizontal_spacing=0.08,
        )
    )

    def update_plot(process_name, element):
        pid = process_options[process_name]
        element_index = element_items.index(element)
        _scale, _unit = get_mass_display()

        # If the sum is empty, it returns a scalar 0, which causes a Plotly error.
        # We provide a zero-array of the correct length as the start value for sum.
        inflow_ts = sum(
            (
                f.Values[:, element_index]
                for f in mfa_system_results.FlowDict.values()
                if f.P_End == pid
            ),
            np.zeros(len(time_axis)),
        )

        # Gracefully handle processes without a stock
        stock_obj = mfa_system_results.StockDict.get(f"S_{pid}")
        if stock_obj:
            stock_ts = stock_obj.Values[:, element_index]
        else:
            stock_ts = np.zeros(len(time_axis))  # Plot a flat line at zero

        outflow_ts = sum(
            (
                f.Values[:, element_index]
                for f in mfa_system_results.FlowDict.values()
                if f.P_Start == pid
            ),
            np.zeros(len(time_axis)),
        )

        subplot_titles = (
            f"Inflow to '{process_name}'",
            f"Stock in '{process_name}'",
            f"Outflow from '{process_name}'",
        )
        if has_type_column:
            process_type = process_definitions.loc[
                process_definitions["ID"] == pid, PROCESS_TYPE_COLUMN_NAME
            ].iloc[0]
            if process_type == "Input":
                subplot_titles = (
                    "Primary System Input",
                    subplot_titles[1],
                    subplot_titles[2],
                )
            elif process_type == "Output":
                subplot_titles = (
                    subplot_titles[0],
                    subplot_titles[1],
                    "Final System Output (Sink)",
                )

        # Get element-specific color
        element_color = color_manager.get_element_color(element.lower())

        with fig.batch_update():
            fig.data, fig.layout.annotations = [], []
            fig.add_trace(
                go.Scatter(
                    x=time_axis,
                    y=inflow_ts * _scale,
                    mode="lines",
                    name="Inflow",
                    line=dict(color=element_color, width=2),
                    marker=dict(size=4),
                ),
                row=1,
                col=1,
            )
            fig.add_trace(
                go.Scatter(
                    x=time_axis,
                    y=stock_ts * _scale,
                    mode="lines",
                    name="Stock",
                    line=dict(
                        color=color_manager.get_element_color(
                            element.lower(), is_stock=True
                        ),
                        width=2,
                    ),
                    marker=dict(size=4),
                ),
                row=1,
                col=2,
            )
            fig.add_trace(
                go.Scatter(
                    x=time_axis,
                    y=outflow_ts * _scale,
                    mode="lines",
                    name="Outflow",
                    line=dict(color=element_color, width=2, dash="dash"),
                    marker=dict(size=4),
                ),
                row=1,
                col=3,
            )
            layout_config = get_publication_layout(
                custom_title=f"Inflow, Stock, and Outflow - {process_name} ({element.upper()})",
                show_grid=True,
                scientific_y=True,
            )
            apply_theme(layout_config)
            xaxis_style = layout_config.pop("xaxis")
            yaxis_style = layout_config.pop("yaxis")
            yaxis_style["title"] = {
                "text": y_label(element.upper(), rate=True),
                "font": {"size": get_active_theme()["font_axis"]},
            }
            fig.update_layout(**layout_config)
            fig.update_xaxes(title_text="Year", **xaxis_style)
            fig.update_yaxes(**yaxis_style)

    def export_current_plot(btn):
        """Export current plot configuration."""
        process_name = process_dropdown.value
        element = element_dropdown.value
        update_plot(process_name, element)  # Ensure plot is current

        filename = f"process_dynamics_{process_name.replace(' ', '_')}_{element}"
        try:
            paths = export_figure(
                fig,
                filename,
                formats=["png", "svg"],
                quality="publication",
                size="large",
            )
            print(f"✅ Exported: {', '.join(paths)}")
        except Exception as e:
            print(f"❌ Export failed: {e}")

    process_dropdown = Dropdown(
        options=list(process_options.keys()),
        description="Process:",
        style={"description_width": "80px"},
        layout=Layout(width="400px"),
    )
    element_dropdown = Dropdown(
        options=element_items,
        value=element_items[0],
        description="Element:",
        style={"description_width": "80px"},
        layout=Layout(width="200px"),
    )

    # Create control panel
    controls = [process_dropdown, element_dropdown]

    if enable_export:
        export_btn = Button(
            description="📥 Export Figure",
            button_style="success",
            tooltip="Export current view to PNG and PDF",
            layout=Layout(width="150px"),
        )
        export_btn.on_click(export_current_plot)
        controls.append(export_btn)

    control_box = HBox(controls, layout=Layout(margin="10px 0"))

    # Set up interaction manually to avoid double widget display
    from ipywidgets import interactive_output

    interactive_output(
        update_plot, {"process_name": process_dropdown, "element": element_dropdown}
    )

    # Display
    display(control_box)
    display(fig)

    # Initial plot
    update_plot(process_dropdown.value, element_dropdown.value)


def plot_dynamic_stock_composition(dsm_details, mfa_system_results):
    """Plots the composition of a dynamic stock over time.

    This function visualizes how a dynamic stock is composed of its decaying
    initial stock and the stock built up from new inflows. It allows for
    analysis of the contributions from different inflow categories over time.

    Parameters
    ----------
    dsm_details : dict
        A dictionary containing detailed results from the DSM calculations,
        including initial stock time series, inflow stock time series by
        category, category names, and mean lifetimes.
    mfa_system_results : odym.MFAsystem
        The solved MFA system object, containing the results of the MFA
        calculation, including all flows and stocks over the simulation period.

    Notes
    -----
    The plot is interactive, allowing the user to select the DSM process,
    the element to display, and whether to show the data as a bar chart
    or a line chart. The inflow composition factor is used to correctly
    apportion elements to the new stock parts.
    """

    process_options = list(dsm_details.keys())
    if not process_options:
        print("No DSM processes with detailed results found to plot.")
        return

    element_items = mfa_system_results.Elements
    time_axis = mfa_system_results.IndexTable.Classification["Time"].Items
    fig = go.FigureWidget()

    def update_plot(process_id, element, show_as_bars):
        details = dsm_details.get(process_id, {})
        element_index = element_items.index(element)

        # Get data from the details dictionary
        initial_stock_ts_all_elements = details.get(
            "initial_stock_ts", np.zeros((len(time_axis), len(element_items)))
        )
        inflow_stocks_material = details.get("inflow_stock_ts_by_cat", [])
        category_names = details.get("category_names", [])
        mean_lifetimes = details.get("mean_lifetimes", [])

        with fig.batch_update():
            fig.data = []
            _scale, _unit = get_mass_display()
            chart_type = go.Bar if show_as_bars else go.Scatter
            stack_group_props = (
                {"mode": "lines", "line": dict(width=0.5), "stackgroup": "one"}
                if not show_as_bars
                else {}
            )

            # Plot the decaying initial stock
            initial_stock_ts_element = initial_stock_ts_all_elements[:, element_index]
            fig.add_trace(
                chart_type(
                    x=time_axis,
                    y=initial_stock_ts_element * _scale,
                    name="Initial Stock (Decaying)",
                    hoverinfo="x+y",
                    **stack_group_props,
                )
            )

            # Plot the stock from new inflows, category by category
            # stock_ts_material is (num_years, num_elements) — vintage composition embedded.
            for i, stock_ts_material in enumerate(inflow_stocks_material):
                stock_ts_element = stock_ts_material[:, element_index]
                label = f"{category_names[i]} ({mean_lifetimes[i]} yrs)"
                fig.add_trace(
                    chart_type(
                        x=time_axis,
                        y=stock_ts_element * _scale,
                        name=label,
                        hoverinfo="x+y",
                        **stack_group_props,
                    )
                )

            process_name = next(
                (p.Name for p in mfa_system_results.ProcessList if p.ID == process_id),
                "",
            )
            layout_config = get_publication_layout(
                custom_title=f"Stock Composition - {process_name} ({element.upper()})",
                x_title="Year",
                y_title=y_label(element.upper()),
                show_grid=True,
                scientific_y=True,
            )
            if show_as_bars:
                layout_config["barmode"] = "stack"
            fig.update_layout(**layout_config)

    process_dropdown = Dropdown(options=process_options, description="Process:")
    element_dropdown = Dropdown(
        options=element_items, value=element_items[0], description="Element:"
    )
    chart_type_checkbox = Checkbox(value=False, description="Show as Bar Chart")

    def _on_change(change):
        update_plot(
            process_dropdown.value, element_dropdown.value, chart_type_checkbox.value
        )

    process_dropdown.observe(_on_change, "value")
    element_dropdown.observe(_on_change, "value")
    chart_type_checkbox.observe(_on_change, "value")

    export_btn = Button(
        description="Export PNG/SVG",
        button_style="success",
        icon="download",
        layout=Layout(width="160px"),
    )

    def _do_export(b):
        try:
            name = f"dynamic_stock_composition_{process_dropdown.value}_{element_dropdown.value}".replace(
                " ", "_"
            )
            paths = export_figure(
                fig, name, formats=["png", "svg"], quality="publication", size="large"
            )
            print(f"✅ Exported: {', '.join(paths)}")
        except Exception as e:
            print(f"❌ Export failed: {e}")

    export_btn.on_click(_do_export)

    display(HBox([process_dropdown, element_dropdown, chart_type_checkbox, export_btn]))
    display(fig)
    update_plot(
        process_dropdown.value, element_dropdown.value, chart_type_checkbox.value
    )


def plot_component_replacement_rate(mfa_system_results, dsm_params, unit_weights=None):
    """Plots DSM_Component replacement flow rate per part, one line per component.

    Reads each component's ``sparepart_outflow`` flow directly (worn-part
    leaving the process) — decouples parts that share a physical outflow
    (e.g. Imaging Unit + Fuser both routed to the same WEEE flow) so "how
    often is part X replaced" is visible per part, not just as a combined
    mass total.

    Parameters
    ----------
    mfa_system_results : odym.MFAsystem
        Solved MFA system.
    dsm_params : dict
        DSM parameter dict keyed by process ID; only processes with a
        ``"components"`` list (DSM_Component logic) are offered.
    unit_weights : dict, optional
        {element_name: kg_per_unit}. When given for an element, that
        component's line is shown as units/yr instead of kg/yr. Missing
        entries fall back to kg/yr — this function makes no assumption
        about part weights (case-study-specific, not engine data).
    """
    process_options = [
        pid for pid, p in dsm_params.items() if p.get("components")
    ]
    if not process_options:
        print("No DSM_Component processes with tracked components found to plot.")
        return

    unit_weights = unit_weights or {}
    elements = mfa_system_results.Elements
    time_axis = mfa_system_results.IndexTable.Classification["Time"].Items
    fig = go.FigureWidget()

    def update_plot(process_id, log_y):
        components = dsm_params.get(process_id, {}).get("components", [])
        with fig.batch_update():
            fig.data = []
            any_units = False
            for comp in components:
                element = comp.get("element", "")
                outflow_id = comp.get("sparepart_outflow", "")
                flow = mfa_system_results.FlowDict.get(outflow_id)
                if flow is None or element not in elements:
                    continue
                elem_idx = elements.index(element)
                mass_per_year = flow.Values[:, elem_idx]
                weight = unit_weights.get(element)
                if weight:
                    y, suffix = mass_per_year / weight, "units/yr"
                    any_units = True
                else:
                    y, suffix = mass_per_year, "kg/yr"
                fig.add_trace(
                    go.Scatter(
                        x=time_axis,
                        y=y,
                        mode="lines",
                        name=f"{element} ({suffix})",
                        hoverinfo="x+y+name",
                    )
                )

            process_name = next(
                (p.Name for p in mfa_system_results.ProcessList if p.ID == process_id),
                "",
            )
            layout_config = get_publication_layout(
                custom_title=f"Component Replacement Rate - {process_name}",
                x_title="Year",
                y_title="units/yr" if any_units else "kg/yr",
                show_grid=True,
            )
            if log_y:
                layout_config["yaxis"] = {**layout_config.get("yaxis", {}), "type": "log"}
            fig.update_layout(**layout_config)

    process_dropdown = Dropdown(options=process_options, description="Process:")
    log_checkbox = Checkbox(value=True, description="Log scale")

    def _on_change(change):
        update_plot(process_dropdown.value, log_checkbox.value)

    process_dropdown.observe(_on_change, "value")
    log_checkbox.observe(_on_change, "value")

    export_btn = Button(
        description="Export PNG/SVG",
        button_style="success",
        icon="download",
        layout=Layout(width="160px"),
    )

    def _do_export(b):
        try:
            name = f"component_replacement_rate_{process_dropdown.value}"
            paths = export_figure(
                fig, name, formats=["png", "svg"], quality="publication", size="large"
            )
            print(f"✅ Exported: {', '.join(paths)}")
        except Exception as e:
            print(f"❌ Export failed: {e}")

    export_btn.on_click(_do_export)

    display(HBox([process_dropdown, log_checkbox, export_btn]))
    display(fig)
    update_plot(process_dropdown.value, log_checkbox.value)


def plot_fomp_dynamics(mfa_system_results, fomp_params_config):
    """Creates side-by-side line charts for Inflow, Stock, and Outflow for FOMP processes.

    This function visualizes the time-series dynamics of a selected First-Order
    Mineralization Process (FOMP), showing its total inflow, absolute stock,
    and outflow (mineralization) in three separate but linked subplots.

    Parameters
    ----------
    mfa_system_results : odym.MFAsystem
        The solved MFA system object, containing the results of the MFA
        calculation, including all flows and stocks over the simulation period.
    fomp_params_config : dict
        The configuration dictionary for FOMP processes, used to identify
        which processes are defined as FOMP and should be available for plotting.

    Notes
    -----
    The plot is interactive, allowing the user to select the FOMP process
    and the element to display. The y-axis is labeled as "Mass (Mg)" and
    uses scientific notation for better readability of potentially large values.
    """
    from plotly.subplots import make_subplots

    # Create a mapping of process names to IDs for the dropdown.
    # Exclude the boundary process (ID 0) — it is never a real FOMP process.
    process_options = {
        p.Name: p.ID
        for p in mfa_system_results.ProcessList
        if p.ID in fomp_params_config and p.ID != 0
    }
    if not process_options:
        print("No processes with FOMP parameters are defined in the configuration.")
        return

    element_items = mfa_system_results.Elements
    time_axis = mfa_system_results.IndexTable.Classification["Time"].Items
    fig = go.FigureWidget(
        make_subplots(
            rows=1,
            cols=3,
            subplot_titles=(
                "Total Inflow",
                "Absolute Stock (S)",
                "Outflow (Carbon Emissions)",
            ),
        )
    )

    def update_plot(process_name, element):
        pid = process_options[process_name]
        element_index = element_items.index(element)
        _sc, _unit = get_mass_display()

        # Get the time series data for the selected process
        inflow_ts = (
            sum(
                f.Values[:, element_index]
                for f in mfa_system_results.FlowDict.values()
                if f.P_End == pid
            )
            * _sc
        )
        stock_obj = mfa_system_results.StockDict.get(f"S_{pid}")
        stock_ts = (
            stock_obj.Values[:, element_index]
            if stock_obj is not None
            else np.zeros(len(time_axis))
        ) * _sc
        outflow_ts = (
            sum(
                f.Values[:, element_index]
                for f in mfa_system_results.FlowDict.values()
                if f.P_Start == pid
            )
            * _sc
        )

        with fig.batch_update():
            fig.data = []  # Clear existing data
            fig.add_trace(
                go.Scatter(x=time_axis, y=inflow_ts, mode="lines", name="Inflow"),
                row=1,
                col=1,
            )
            fig.add_trace(
                go.Scatter(x=time_axis, y=stock_ts, mode="lines", name="Stock"),
                row=1,
                col=2,
            )
            fig.add_trace(
                go.Scatter(x=time_axis, y=outflow_ts, mode="lines", name="Outflow"),
                row=1,
                col=3,
            )

            layout_config = get_publication_layout(
                custom_title=f"FOMP - First-Order Decay Flows - {process_name} ({element.upper()})",
                show_grid=True,
                scientific_y=True,
                size="small",
            )
            apply_theme(layout_config)
            xaxis_style = layout_config.pop("xaxis")
            yaxis_style = layout_config.pop("yaxis")
            fig.update_layout(**layout_config)
            fig.update_xaxes(title_text="Year", **xaxis_style)
            fig.update_yaxes(title_text=y_label(element.upper()), **yaxis_style)

    # Create widgets for interaction
    process_dropdown = Dropdown(
        options=list(process_options.keys()), description="Process:"
    )
    element_dropdown = Dropdown(
        options=element_items, value=element_items[0], description="Element:"
    )

    export_dyn_btn = Button(
        description="Export PNG/SVG",
        button_style="success",
        icon="download",
        layout=Layout(width="160px"),
    )

    def _do_dyn_export(b):
        try:
            proc_name = process_dropdown.value.replace(" ", "_")
            elem = element_dropdown.value
            paths = export_figure(
                fig,
                f"fomp_dynamics_{proc_name}_{elem}",
                formats=["png", "svg"],
                quality="publication",
                size="large",
                timestamp=False,
            )
            print(f"✅ Exported: {', '.join(paths)}")
        except Exception as e:
            print(f"❌ Export failed: {e}")

    export_dyn_btn.on_click(_do_dyn_export)

    def _on_change(change):
        update_plot(process_dropdown.value, element_dropdown.value)

    process_dropdown.observe(_on_change, "value")
    element_dropdown.observe(_on_change, "value")

    display(HBox([process_dropdown, element_dropdown, export_dyn_btn]))
    display(fig)
    update_plot(process_dropdown.value, element_dropdown.value)


def _resolve_input_substitution_residual_flow(mfa_system_results, pid, params):
    """Same discovery rule as engine.input_substitution.calculate_input_substitution
    and consistency.input_substitution_residual_flow: named via residual_flow_id
    when set, otherwise the sole other P_Start==pid flow not claimed by
    consumed_flow_id/surplus_flow_id."""
    residual_id = params.get("residual_flow_id")
    if residual_id:
        return mfa_system_results.FlowDict.get(residual_id)
    claimed = {params.get("consumed_flow_id"), params.get("surplus_flow_id")}
    candidates = [
        f
        for f in mfa_system_results.FlowDict.values()
        if f.P_Start == pid and f.Name not in claimed
    ]
    return candidates[0] if len(candidates) == 1 else None


def plot_input_substitution_dynamics(mfa_system_results, substitution_params):
    """Visualizes the Input_Substitution mechanism itself, over time.

    For a selected Input_Substitution process and element, shows the
    demand target, the raw (pre-lag) supply, and how the solver split that
    into consumed (recycled/secondary), residual (virgin), and surplus —
    the exact quantities `engine.input_substitution.calculate_input_substitution`
    computes each iteration. Meant as a diagnostic: `target` always equals
    `consumed + residual`, and `surplus` (if configured) always equals
    `supply - consumed` — if a trace looks wrong relative to those
    identities, that points at a config issue (see
    07_AI_Coding_Assistance/260720_Report_InputSubstitution_ReviewRequest.md
    and its §7/§10 follow-up) rather than the underlying flows themselves.

    Parameters
    ----------
    mfa_system_results : odym.MFAsystem
        The solved MFA system object.
    substitution_params : dict
        Input_Substitution process parameters dict (keyed by process ID),
        as returned by `engine.input_substitution.load_input_substitution_from_yaml`.
    """
    process_options = {
        p.Name: p.ID
        for p in mfa_system_results.ProcessList
        if p.ID in (substitution_params or {})
    }
    if not process_options:
        print("No processes with Input_Substitution parameters are defined in the configuration.")
        return

    element_items = mfa_system_results.Elements
    time_axis = mfa_system_results.IndexTable.Classification["Time"].Items
    fig = go.FigureWidget()

    def update_plot(process_name, element):
        pid = process_options[process_name]
        params = substitution_params[pid]
        element_index = element_items.index(element)
        _sc, _unit = get_mass_display()

        residual_flow = _resolve_input_substitution_residual_flow(
            mfa_system_results, pid, params
        )
        consumed_flow = mfa_system_results.FlowDict.get(params.get("consumed_flow_id"))
        surplus_id = params.get("surplus_flow_id")
        surplus_flow = mfa_system_results.FlowDict.get(surplus_id) if surplus_id else None
        supply_flows = [
            mfa_system_results.FlowDict[fid]
            for fid in (params.get("supply_flow_ids") or [])
            if fid in mfa_system_results.FlowDict
        ]

        if residual_flow is None or consumed_flow is None:
            print(
                f"Input_Substitution process '{process_name}': residual/consumed "
                f"flow not resolvable from the current config — check "
                f"residual_flow_id/consumed_flow_id."
            )
            return

        residual_ts = residual_flow.Values[:, element_index] * _sc
        consumed_ts = consumed_flow.Values[:, element_index] * _sc
        target_ts = residual_ts + consumed_ts  # always holds, by construction
        supply_ts = (
            sum(f.Values[:, element_index] for f in supply_flows)
            if supply_flows
            else np.zeros(len(time_axis))
        ) * _sc
        surplus_ts = (
            surplus_flow.Values[:, element_index] * _sc
            if surplus_flow is not None
            else None
        )

        with fig.batch_update():
            fig.data = []
            fig.add_trace(
                go.Scatter(
                    x=time_axis, y=target_ts, mode="lines", name="Target demand",
                    line=dict(color="black", dash="dash"),
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=time_axis, y=supply_ts, mode="lines", name="Supply (raw, pre-lag)",
                    line=dict(color="grey"),
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=time_axis, y=consumed_ts, mode="lines",
                    name="Consumed (recycled/secondary)",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=time_axis, y=residual_ts, mode="lines",
                    name="Residual (virgin)",
                )
            )
            if surplus_ts is not None:
                fig.add_trace(
                    go.Scatter(x=time_axis, y=surplus_ts, mode="lines", name="Surplus")
                )

            lag = params.get("lag_years", 0) or 0
            lag_note = f" — lag_years={lag}" if lag else ""
            layout_config = get_publication_layout(
                custom_title=f"Input_Substitution — {process_name} ({element.upper()}){lag_note}",
                show_grid=True,
                size="small",
            )
            apply_theme(layout_config)
            xaxis_style = layout_config.pop("xaxis")
            yaxis_style = layout_config.pop("yaxis")
            fig.update_layout(**layout_config)
            fig.update_xaxes(title_text="Year", **xaxis_style)
            fig.update_yaxes(title_text=y_label(element.upper()), **yaxis_style)

    process_dropdown = Dropdown(
        options=list(process_options.keys()), description="Process:"
    )
    element_dropdown = Dropdown(
        options=element_items, value=element_items[0], description="Element:"
    )

    export_btn = Button(
        description="Export PNG/SVG",
        button_style="success",
        icon="download",
        layout=Layout(width="160px"),
    )

    def _do_export(b):
        try:
            proc_name = process_dropdown.value.replace(" ", "_")
            elem = element_dropdown.value
            paths = export_figure(
                fig,
                f"input_substitution_dynamics_{proc_name}_{elem}",
                formats=["png", "svg"],
                quality="publication",
                size="large",
                timestamp=False,
            )
            print(f"✅ Exported: {', '.join(paths)}")
        except Exception as e:
            print(f"❌ Export failed: {e}")

    export_btn.on_click(_do_export)

    def _on_change(change):
        update_plot(process_dropdown.value, element_dropdown.value)

    process_dropdown.observe(_on_change, "value")
    element_dropdown.observe(_on_change, "value")

    display(HBox([process_dropdown, element_dropdown, export_btn]))
    display(fig)
    update_plot(process_dropdown.value, element_dropdown.value)


def plot_input_substitution_rate(mfa_system_results, substitution_params):
    """Bar chart: substitution rate for every Input_Substitution process, for
    a selected year and element.

    Complements ``plot_input_substitution_dynamics`` (one process, all
    years) with the opposite cut: all processes, one year — "how much of
    each process's demand was covered by secondary material this year."

      substitution % = consumed / target * 100
                        (target = residual + consumed, holds by
                        construction — see calculate_input_substitution)

    Bounded in [0, 100] by construction, since consumed <= target always.

    Parameters
    ----------
    mfa_system_results : odym.MFAsystem
        The solved MFA system object.
    substitution_params : dict
        Input_Substitution process parameters dict (keyed by process ID),
        as returned by `engine.input_substitution.load_input_substitution_from_yaml`.
    """
    process_options = {
        p.Name: p.ID
        for p in mfa_system_results.ProcessList
        if p.ID in (substitution_params or {})
    }
    if not process_options:
        print("No processes with Input_Substitution parameters are defined in the configuration.")
        return

    element_items = mfa_system_results.Elements
    time_axis = mfa_system_results.IndexTable.Classification["Time"].Items
    fig = go.FigureWidget()

    def update_plot(year, element):
        year_index = time_axis.index(year)
        element_index = element_items.index(element)

        process_names = []
        rates = []
        for name, pid in process_options.items():
            params = substitution_params[pid]
            residual_flow = _resolve_input_substitution_residual_flow(
                mfa_system_results, pid, params
            )
            consumed_flow = mfa_system_results.FlowDict.get(params.get("consumed_flow_id"))
            if residual_flow is None or consumed_flow is None:
                continue
            consumed = consumed_flow.Values[year_index, element_index]
            target = residual_flow.Values[year_index, element_index] + consumed
            rate = (consumed / target * 100.0) if target > 0 else 0.0
            process_names.append(name)
            rates.append(rate)

        with fig.batch_update():
            fig.data = []
            fig.add_trace(
                go.Bar(
                    x=process_names,
                    y=rates,
                    hovertemplate="<b>%{x}</b><br>Substituted: %{y:.1f}%<extra></extra>",
                )
            )

            layout_config = get_publication_layout(
                custom_title=f"Input_Substitution — Rate Substituted ({element.upper()}, {year})",
                show_grid=True,
                size="small",
            )
            apply_theme(layout_config)
            xaxis_style = layout_config.pop("xaxis")
            yaxis_style = layout_config.pop("yaxis")
            fig.update_layout(**layout_config)
            fig.update_xaxes(title_text="Process", **xaxis_style)
            fig.update_yaxes(
                title_text="% of demand met by secondary material",
                range=[0, 100],
                **yaxis_style,
            )

    year_slider = IntSlider(
        min=time_axis[0], max=time_axis[-1], step=1, value=time_axis[0],
        description="Year:", continuous_update=False,
    )
    element_dropdown = Dropdown(
        options=element_items, value=element_items[0], description="Element:"
    )

    export_btn = Button(
        description="Export PNG/SVG",
        button_style="success",
        icon="download",
        layout=Layout(width="160px"),
    )

    def _do_export(b):
        try:
            elem = element_dropdown.value
            yr = year_slider.value
            paths = export_figure(
                fig,
                f"input_substitution_rate_{elem}_{yr}",
                formats=["png", "svg"],
                quality="publication",
                size="large",
                timestamp=False,
            )
            print(f"✅ Exported: {', '.join(paths)}")
        except Exception as e:
            print(f"❌ Export failed: {e}")

    export_btn.on_click(_do_export)

    def _on_change(change):
        update_plot(year_slider.value, element_dropdown.value)

    year_slider.observe(_on_change, "value")
    element_dropdown.observe(_on_change, "value")

    display(HBox([year_slider, element_dropdown, export_btn]))
    display(fig)
    update_plot(year_slider.value, element_dropdown.value)


def plot_flow_dynamics(
    mfa_system_results,
    color_manager: Optional[ElementColorManager] = None,
    enable_export: bool = True,
):
    """Creates an interactive line/bar chart to show the development of selected flows over time.

    This function allows users to visualize the time-series evolution of one or
    more selected flows for a chosen element. It supports both line and bar
    chart representations and provides descriptive names for flows for better
    readability. Now supports element-agnostic coloring and publication-quality export.

    Parameters
    ----------
    mfa_system_results : odym.MFAsystem
        The solved MFA system object, containing the results of the MFA
        calculation, including all flows and stocks over the simulation period.
    color_manager : ElementColorManager, optional
        Dynamic color manager for element colors. If None, creates one from
        mfa_system_results.Elements. Defaults to None.
    enable_export : bool, optional
        If True, adds an export button for saving publication-quality figures.
        Defaults to True.

    Notes
    -----
    The plot is interactive, allowing the user to select multiple flows,
    the element to display, and whether to show the data as a bar chart
    or a line chart. The layout is configured for publication quality,
    including scientific notation for the y-axis and a visible legend.
    Element-specific colors are automatically applied for consistency.

    Examples
    --------
    >>> # Basic usage
    >>> plot_flow_dynamics(mfa_results)

    >>> # With color-blind friendly colors
    >>> color_mgr = ElementColorManager(elements, color_scheme='colorblind')
    >>> plot_flow_dynamics(mfa_results, color_manager=color_mgr)
    """

    # Create options for the widgets with descriptive names
    # Build process name lookup for "Source → Destination" style names
    process_name_by_id = {p.ID: p.Name for p in mfa_system_results.ProcessList}
    flow_options = []
    flow_id_to_descriptive = {}

    for flow_id in sorted(mfa_system_results.FlowDict.keys()):
        flow_obj = mfa_system_results.FlowDict[flow_id]
        src = process_name_by_id.get(flow_obj.P_Start, f"P{flow_obj.P_Start}")
        dst = process_name_by_id.get(flow_obj.P_End, f"P{flow_obj.P_End}")
        descriptive_name = f"{src} \u2192 {dst}"
        flow_options.append(descriptive_name)
        flow_id_to_descriptive[flow_id] = descriptive_name

    if not flow_options:
        print("No flows found in the system to plot.")
        return

    element_items = [e.lower() for e in mfa_system_results.Elements]
    time_axis = mfa_system_results.IndexTable.Classification["Time"].Items

    # Create color manager if not provided
    if color_manager is None:
        color_manager = ElementColorManager(element_items)

    # Use FigureWidget for efficient updates
    fig = go.FigureWidget()

    def update_plot(flows_to_show, element, show_as_bars):
        # Use batch_update for smooth interaction
        with fig.batch_update():
            fig.data = []  # Clear previous traces
            if not flows_to_show:
                fig.update_layout(
                    title_text="Please select one or more flows to display."
                )
                return

            element_index = element_items.index(element)
            _scale, _unit = get_mass_display()
            chart_type = go.Bar if show_as_bars else go.Scatter

            # Get element-specific color
            color_manager.get_element_color(element.lower())

            # Add a trace for each selected flow
            for i, descriptive_name in enumerate(flows_to_show):
                # Find the flow ID that corresponds to this descriptive name
                flow_id = None
                for fid, desc_name in flow_id_to_descriptive.items():
                    if desc_name == descriptive_name:
                        flow_id = fid
                        break

                if flow_id:
                    flow_obj = mfa_system_results.FlowDict.get(flow_id)
                    if flow_obj:
                        trace_props = dict(
                            x=time_axis,
                            y=flow_obj.Values[:, element_index] * _scale,
                            name=descriptive_name,
                            marker=dict(line=dict(width=0.5)),
                        )
                        if not show_as_bars:
                            # Line mode: use element color with slight variations for multiple flows
                            trace_props.update(
                                mode="lines",
                                line=dict(width=2),
                                marker=dict(size=4),
                            )
                        fig.add_trace(chart_type(**trace_props))

            # Update layout and title
            layout_config = get_publication_layout(
                custom_title=f"Flow Analysis - {element.upper()}",
                x_title="Year",
                y_title=y_label(element.upper(), rate=True),
                show_grid=True,
                scientific_y=True,
            )
            apply_theme(layout_config)
            if show_as_bars:
                layout_config["barmode"] = "stack"
            else:
                layout_config["barmode"] = "overlay"

            # Always show legend, even with single flow
            layout_config["showlegend"] = True

            fig.update_layout(**layout_config)

    def export_current_plot(btn):
        """Export current plot configuration."""
        flows_to_show = flow_selector.value
        element = element_dropdown.value
        update_plot(
            flows_to_show, element, chart_type_checkbox.value
        )  # Ensure plot is current

        flow_names = "_".join(
            [f[:10] for f in flows_to_show[:3]]
        )  # Limit filename length
        filename = f"flow_dynamics_{flow_names}_{element}"
        try:
            paths = export_figure(
                fig,
                filename,
                formats=["png", "svg"],
                quality="publication",
                size="large",
            )
            print(f"✅ Exported: {', '.join(paths)}")
        except Exception as e:
            print(f"❌ Export failed: {e}")

    # Create widgets
    flow_selector = SelectMultiple(
        options=flow_options,
        value=[flow_options[0]] if flow_options else [],
        description="Flows:",
        rows=10,
        style={"description_width": "60px"},
        layout=Layout(width="400px"),
    )
    element_dropdown = Dropdown(
        options=element_items,
        value=element_items[0],
        description="Element:",
        style={"description_width": "80px"},
        layout=Layout(width="200px"),
    )
    chart_type_checkbox = Checkbox(
        value=False,
        description="Show as Bar Chart",
        style={"description_width": "120px"},
    )

    # Create control panel
    controls_left = VBox([flow_selector], layout=Layout(width="400px"))
    controls_right = VBox(
        [element_dropdown, chart_type_checkbox], layout=Layout(width="200px")
    )

    if enable_export:
        export_btn = Button(
            description="📥 Export Figure",
            button_style="success",
            tooltip="Export current view to PNG and PDF",
            layout=Layout(width="150px", margin="10px 0 0 0"),
        )
        export_btn.on_click(export_current_plot)
        controls_right.children = list(controls_right.children) + [export_btn]

    control_box = HBox([controls_left, controls_right], layout=Layout(margin="10px 0"))

    # Set up interaction manually to avoid double widget display
    from ipywidgets import interactive_output

    interactive_output(
        update_plot,
        {
            "flows_to_show": flow_selector,
            "element": element_dropdown,
            "show_as_bars": chart_type_checkbox,
        },
    )

    # Display
    display(control_box)
    display(fig)

    # Initial plot
    update_plot(flow_selector.value, element_dropdown.value, chart_type_checkbox.value)


def plot_stock_bar_chart(mfa_system, title="Stock Levels Over Time"):
    """Generates an interactive bar chart of stock levels with time and element selection.

    This function creates a bar chart that displays the stock levels for each
    process at a selected year and for a chosen element. It uses process names
    instead of IDs for clarity and applies a color scheme based on whether
    the stock value is positive or negative.

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        The MFA system object containing calculated results, including stock data.
    title : str, optional
        The title for the plot. Defaults to "Stock Levels Over Time".

    Notes
    -----
    The plot is interactive, featuring a year slider and an element dropdown
    to dynamically update the displayed stock levels. The layout is configured
    for publication quality, with scientific notation for the y-axis and
    rotated x-axis labels for process names.
    """
    if not hasattr(mfa_system, "StockDict") or not mfa_system.StockDict:
        print("No stocks available to plot.")
        return

    years = mfa_system.IndexTable.Classification["Time"].Items
    elements = mfa_system.Elements

    # Create a mapping from process ID to process name
    process_id_to_name = {p.ID: p.Name for p in mfa_system.ProcessList}

    # Prepare the data in a long-format DataFrame for easier filtering
    all_stocks_data = []
    for stock_name, stock in mfa_system.StockDict.items():
        if stock_name.startswith("S_"):
            process_id = int(stock_name.split("_")[1])
            process_name = process_id_to_name.get(process_id, f"Process {process_id}")
            for i, year in enumerate(years):
                for j, element in enumerate(elements):
                    all_stocks_data.append(
                        {
                            "Year": year,
                            "Element": element,
                            "Process": process_name,
                            "Value": stock.Values[i, j],
                        }
                    )

    if not all_stocks_data:
        print("No absolute stock data found to plot.")
        return

    df = pd.DataFrame(all_stocks_data)
    fig = go.FigureWidget()

    def update_plot(year, element):
        with fig.batch_update():
            fig.data = []
            _scale, _unit = get_mass_display()
            df_filtered = df[(df["Year"] == year) & (df["Element"] == element)]

            # Determine colors based on value (positive/negative)
            colors = [
                "#0173B2" if val >= 0 else "#CC79A7" for val in df_filtered["Value"]
            ]

            fig.add_trace(
                go.Bar(
                    x=df_filtered["Process"],
                    y=df_filtered["Value"] * _scale,
                    marker_color=colors,
                    hovertemplate=f"<b>%{{x}}</b><br>Stock: %{{y:.3f}} {_unit}<extra></extra>",
                )
            )

            layout_config = get_publication_layout(
                custom_title=f"{title} - {element.upper()} ({year})",
                x_title="Process Name",
                y_title=y_label(element.upper()),
                show_grid=True,
                scientific_y=True,
            )
            apply_theme(layout_config)
            layout_config["xaxis"].pop(
                "range", None
            )  # categorical axis, not time-series
            layout_config["showlegend"] = False
            layout_config["xaxis"]["tickangle"] = -45
            fig.update_layout(**layout_config)

    # Create widgets
    year_slider = IntSlider(
        min=min(years), max=max(years), step=1, value=min(years), description="Year"
    )
    element_dropdown = Dropdown(
        options=elements, value=elements[0], description="Element"
    )

    def _on_change(change):
        update_plot(year_slider.value, element_dropdown.value)

    year_slider.observe(_on_change, "value")
    element_dropdown.observe(_on_change, "value")

    export_btn = Button(
        description="Export PNG/SVG",
        button_style="success",
        icon="download",
        layout=Layout(width="160px"),
    )

    def _do_export(b):
        try:
            name = (
                f"stock_bar_chart_{year_slider.value}_{element_dropdown.value}".replace(
                    " ", "_"
                )
            )
            paths = export_figure(
                fig, name, formats=["png", "svg"], quality="publication", size="large"
            )
            print(f"✅ Exported: {', '.join(paths)}")
        except Exception as e:
            print(f"❌ Export failed: {e}")

    export_btn.on_click(_do_export)

    display(HBox([year_slider, element_dropdown, export_btn]))
    display(fig)
    update_plot(year_slider.value, element_dropdown.value)


def plot_system_stock_composition(mfa_system_results, element=None):
    """Creates an interactive plot showing individual stocks in the system over time.

    This function provides a flexible visualization of stock composition within
    the MFA system. It displays individual process stocks as line or bar charts,
    allowing easy comparison of stock levels across processes and time. The plot
    is designed for publication quality with interactive element selection and
    clear labeling.

    Parameters
    ----------
    mfa_system_results : odym.MFAsystem
        The solved MFA system object, containing the results of the MFA
        calculation, including all flows and stocks over the simulation period.
    element : str, optional
        The default element to display when the plot is first rendered.
        If None, the first element from `mfa_system_results.Elements` is used.

    Notes
    -----
    The plot is highly interactive, allowing users to:
    - Select the element to visualize.
    - Toggle between bar chart and line chart display.

    Process names are used for better readability, and the y-axis starts at 0
    with scientific notation for stock values. Plot dimensions are optimized
    at 1600×600 pixels for clear visualization. Individual process stocks are
    shown separately to allow proper interpretation of positive and negative
    stocks in mass balance systems.
    """
    if not hasattr(mfa_system_results, "StockDict") or not mfa_system_results.StockDict:
        print("No stocks available to plot.")
        return

    time_items = mfa_system_results.IndexTable.Classification["Time"].Items
    element_items = mfa_system_results.Elements

    # Set default element
    if element is None:
        element = element_items[0]

    # Create a mapping from process ID to process name
    process_id_to_name = {p.ID: p.Name for p in mfa_system_results.ProcessList}

    fig = go.FigureWidget()

    def update_plot(element, show_as_bars):
        element_index = element_items.index(element)
        _scale, _unit = get_mass_display()

        with fig.batch_update():
            fig.data = []

            # Choose chart type
            chart_type = go.Bar if show_as_bars else go.Scatter

            # Regular bar chart or line chart
            for stock_name, stock_obj in mfa_system_results.StockDict.items():
                if stock_name.startswith("S_"):
                    process_id = int(stock_name.split("_")[1])
                    process_name = process_id_to_name.get(
                        process_id, f"Process {process_id}"
                    )

                    stock_values = stock_obj.Values[:, element_index]

                    # Skip processes with no stock
                    if np.all(stock_values == 0):
                        continue

                    if show_as_bars:
                        fig.add_trace(
                            chart_type(
                                x=time_items,
                                y=stock_values * _scale,
                                name=f"{process_name}",
                                hovertemplate=f"<b>{process_name}</b><br>Year: %{{x}}<br>Stock: %{{y:.3f}} {_unit}<extra></extra>",
                            )
                        )
                    else:
                        fig.add_trace(
                            chart_type(
                                x=time_items,
                                y=stock_values * _scale,
                                mode="lines",
                                name=f"{process_name}",
                                hovertemplate=f"<b>{process_name}</b><br>Year: %{{x}}<br>Stock: %{{y:.3f}} {_unit}<extra></extra>",
                            )
                        )

            # Apply publication layout
            layout_config = get_publication_layout(
                custom_title=f"Stock Composition by Process - {element.upper()}",
                x_title="Year",
                y_title=y_label(element.upper()),
                show_grid=True,
                scientific_y=True,
            )
            apply_theme(layout_config)
            fig.update_layout(**layout_config)

    # Create enhanced widgets
    element_dropdown = Dropdown(
        options=element_items,
        value=element,
        description="Element:",
        style={"description_width": "80px"},
        layout=Layout(width="200px"),
    )
    chart_type_checkbox = Checkbox(
        value=False,
        description="Show as Bar Chart",
        style={"description_width": "120px"},
    )

    # Create widget layout (single row for element and chart type selection)
    export_btn = Button(
        description="Export PNG/SVG",
        button_style="success",
        icon="download",
        layout=Layout(width="160px"),
    )

    def _do_export(b):
        try:
            name = f"system_stock_composition_{element_dropdown.value}".replace(
                " ", "_"
            )
            paths = export_figure(
                fig, name, formats=["png", "svg"], quality="publication", size="large"
            )
            print(f"✅ Exported: {', '.join(paths)}")
        except Exception as e:
            print(f"❌ Export failed: {e}")

    export_btn.on_click(_do_export)

    controls = HBox(
        [element_dropdown, chart_type_checkbox, export_btn],
        layout=Layout(padding="10px"),
    )

    # Set up interaction with custom widgets
    def on_change(change):
        update_plot(
            element_dropdown.value,
            chart_type_checkbox.value,
        )

    element_dropdown.observe(on_change, "value")
    chart_type_checkbox.observe(on_change, "value")

    # Display controls and plot
    display(controls)
    display(fig)

    # Initial plot
    update_plot(
        element_dropdown.value,
        chart_type_checkbox.value,
    )


def plot_lfg_gas_production(mfa_system_results, lfg_params):
    """Interactive plot of CH4 and biogenic CO2 production for LFG processes.

    Shows annual gas production (CH4-C and CO2-C in Mg C) over the simulation
    period for each configured LFG process. Users can toggle between processes
    and choose annual vs. cumulative view.

    Parameters
    ----------
    mfa_system_results : odym.MFAsystem
        The solved MFA system with all flows calculated.
    lfg_params : dict
        LFG parameter config from ``data_loader.load_lfg_parameters()``.
    """
    if not lfg_params:
        print("No LFG processes found to plot.")
        return

    import plotly.graph_objects as go
    from ipywidgets import Dropdown, Checkbox, HBox, Layout
    from IPython.display import display

    time_items = list(mfa_system_results.IndexTable.Classification["Time"].Items)
    elements = mfa_system_results.Elements

    # Accept "TOC" (new hierarchy) → "TC" → "CC" (legacy) for gas carbon values
    cc_idx = next(
        (elements.index(e) for e in ("TOC", "TC", "CC") if e in elements), None
    )
    if cc_idx is None:
        print("   ⚠️  No carbon element found (TOC/TC/CC) — skipping LFG gas plot.")
        return

    colors = {
        "ch4": "#E69F00",  # Orange for CH4
        "co2": "#56B4E9",  # Sky blue for CO2
        "stock": "#009E73",  # Green for stable stock
    }

    process_ids = list(lfg_params.keys())
    process_dropdown = Dropdown(
        options=[(f"Process {pid}", pid) for pid in process_ids],
        description="LFG Process:",
        layout=Layout(width="250px"),
    )
    cumulative_checkbox = Checkbox(value=False, description="Cumulative", indent=False)

    fig = go.FigureWidget()

    def update_plot(process_id, cumulative):
        params = lfg_params[process_id]
        ch4_id = params.get("outflow_ch4_id")
        co2_id = params.get("outflow_co2_id")

        ch4_vals = (
            mfa_system_results.FlowDict[ch4_id].Values[:, cc_idx]
            if ch4_id and ch4_id in mfa_system_results.FlowDict
            else [0] * len(time_items)
        )
        co2_vals = (
            mfa_system_results.FlowDict[co2_id].Values[:, cc_idx]
            if co2_id and co2_id in mfa_system_results.FlowDict
            else [0] * len(time_items)
        )

        import numpy as np

        if cumulative:
            ch4_plot = np.cumsum(ch4_vals)
            co2_plot = np.cumsum(co2_vals)
            y_label = "Cumulative Carbon (Mg C)"
        else:
            ch4_plot = ch4_vals
            co2_plot = co2_vals
            y_label = "Carbon (Mg C / year)"

        with fig.batch_update():
            fig.data = []
            fig.add_trace(
                go.Scatter(
                    x=time_items,
                    y=ch4_plot,
                    name="CH4 (Mg C)",
                    mode="lines+markers",
                    line=dict(color=colors["ch4"], width=2, dash="dash"),
                    marker=dict(symbol="circle", size=5),
                    hovertemplate="<b>CH4</b><br>Year: %{x}<br>%{y:.2f} Mg C<extra></extra>",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=time_items,
                    y=co2_plot,
                    name="biogenic CO2 (Mg C)",
                    mode="lines+markers",
                    line=dict(color=colors["co2"], width=2),
                    marker=dict(symbol="square", size=5),
                    hovertemplate="<b>CO2 (bio)</b><br>Year: %{x}<br>%{y:.2f} Mg C<extra></extra>",
                )
            )
            fig.layout.yaxis.title = y_label
            fig.layout.title = f"LFG Gas Production — Process {process_id}"

    _layout = get_publication_layout(
        x_title="Year",
        y_title="Carbon (Mg C / year)",
        show_grid=True,
        scientific_y=False,
    )
    apply_theme(_layout)
    fig.update_layout(**_layout)

    def on_change(_):
        update_plot(process_dropdown.value, cumulative_checkbox.value)

    process_dropdown.observe(on_change, "value")
    cumulative_checkbox.observe(on_change, "value")

    export_btn = Button(
        description="Export PNG/SVG",
        button_style="success",
        icon="download",
        layout=Layout(width="160px"),
    )

    def _do_lfg_export(b):
        try:
            name = f"lfg_gas_production_{process_dropdown.value}".replace(" ", "_")
            paths = export_figure(
                fig, name, formats=["png", "svg"], quality="publication", size="large"
            )
            print(f"✅ Exported: {', '.join(paths)}")
        except Exception as e:
            print(f"❌ Export failed: {e}")

    export_btn.on_click(_do_lfg_export)

    controls = HBox([process_dropdown, cumulative_checkbox, export_btn])
    display(controls)
    display(fig)
    update_plot(process_ids[0], False)


def plot_lfg_stock_details(mfa_system_results, lfg_params):
    """Interactive plot of LFG stable stock evolution.

    Shows the in-process stock (residual organic carbon + ash) per LFG process.
    Also shows inflow and total gas output for mass balance verification.

    Parameters
    ----------
    mfa_system_results : odym.MFAsystem
        The solved MFA system with all flows calculated.
    lfg_params : dict
        LFG parameter config from ``data_loader.load_lfg_parameters()``.
    """
    if not lfg_params:
        print("No LFG processes found to plot.")
        return

    import plotly.graph_objects as go
    import numpy as np
    from ipywidgets import Dropdown, HBox, Layout
    from IPython.display import display

    time_items = list(mfa_system_results.IndexTable.Classification["Time"].Items)
    elements = mfa_system_results.Elements
    mat_idx = elements.index("material")

    colors = {
        "stock": "#0173B2",
        "inflow": "#56B4E9",
        "gas_out": "#CC79A7",
    }

    process_ids = list(lfg_params.keys())
    process_dropdown = Dropdown(
        options=[(f"Process {pid}", pid) for pid in process_ids],
        description="LFG Process:",
        layout=Layout(width="250px"),
    )

    fig = go.FigureWidget()

    def update_plot(process_id):
        params = lfg_params[process_id]
        ch4_id = params.get("outflow_ch4_id")
        co2_id = params.get("outflow_co2_id")

        stock_obj = mfa_system_results.StockDict.get(f"S_{process_id}")
        stock_vals = (
            stock_obj.Values[:, mat_idx]
            if stock_obj is not None
            else np.zeros(len(time_items))
        )

        inflow_vals = sum(
            f.Values[:, mat_idx]
            for f in mfa_system_results.FlowDict.values()
            if f.P_End == process_id
        )

        gas_out = np.zeros(len(time_items))
        for fid in [ch4_id, co2_id]:
            if fid and fid in mfa_system_results.FlowDict:
                gas_out = gas_out + mfa_system_results.FlowDict[fid].Values[:, mat_idx]

        _sc, _unit = get_mass_display()
        with fig.batch_update():
            fig.data = []
            fig.add_trace(
                go.Scatter(
                    x=time_items,
                    y=stock_vals * _sc,
                    name=f"Stable Stock ({_unit})",
                    mode="lines",
                    line=dict(color=colors["stock"], width=3),
                    hovertemplate=f"<b>Stock</b><br>Year: %{{x}}<br>%{{y:.3f}} {_unit}<extra></extra>",
                )
            )
            fig.add_trace(
                go.Bar(
                    x=time_items,
                    y=inflow_vals * _sc,
                    name=f"Waste Inflow ({_unit})",
                    opacity=0.5,
                    marker_color=colors["inflow"],
                )
            )
            fig.add_trace(
                go.Bar(
                    x=time_items,
                    y=gas_out * _sc,
                    name=f"Gas Output CH4+CO2 ({_unit} C)",
                    opacity=0.5,
                    marker_color=colors["gas_out"],
                )
            )
            fig.layout.title = f"LFG Stable Stock — Process {process_id}"

    _sc0, _unit0 = get_mass_display()
    _layout = get_publication_layout(
        x_title="Year",
        y_title=y_label("Material"),
        show_grid=True,
        scientific_y=False,
    )
    apply_theme(_layout)
    _layout["barmode"] = "overlay"
    fig.update_layout(**_layout)

    process_dropdown.observe(lambda _: update_plot(process_dropdown.value), "value")

    export_btn = Button(
        description="Export PNG/SVG",
        button_style="success",
        icon="download",
        layout=Layout(width="160px"),
    )

    def _do_lfg_stock_export(b):
        try:
            name = f"lfg_stock_details_{process_dropdown.value}".replace(" ", "_")
            paths = export_figure(
                fig, name, formats=["png", "svg"], quality="publication", size="large"
            )
            print(f"✅ Exported: {', '.join(paths)}")
        except Exception as e:
            print(f"❌ Export failed: {e}")

    export_btn.on_click(_do_lfg_stock_export)

    display(HBox([process_dropdown, export_btn]))
    display(fig)
    update_plot(process_ids[0])


def plot_lfg_ipcc_vs_mfa_comparison(mfa_system_results, lfg_params):
    """Diagnostic comparison of IPCC-DOC-based vs MFA-TOC-based LFG gas estimates.

    Runs two carbon-accounting modes side-by-side for each LFG process:

    - **IPCC mode** (current engine default):
      ``active_C_j = W × f_input_j × DOC_j × DOCf``
      Uses literature-derived DOC_j per waste fraction.

    - **MFA/TOC mode**:
      ``active_C_j = TOC_inflow × f_input_j × DOCf``
      Uses the TOC element already tracked in the MFA system (from lab measurements).
      Requires ``TOC_[%]`` to be defined on the waste input flows.

    The DOC ratio (measured TOC / IPCC-implied DOC) quantifies whether the biomass
    carbon content matches IPCC defaults.  A ratio > 1 indicates that measured TOC
    is broader than IPCC DOC (e.g. includes recalcitrant organic carbon such as
    lignin or char).

    Parameters
    ----------
    mfa_system_results : odym.MFAsystem
        Solved MFA system.
    lfg_params : dict
        LFG parameter config from ``data_loader.load_lfg_parameters()``.
    """
    if not lfg_params:
        print("No LFG processes found to plot.")
        return

    import copy
    import importlib.util as _ilu
    import os as _os
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    from ipywidgets import Dropdown, HBox, Layout
    from IPython.display import display

    # Load _calculate_lfg_series fresh to avoid ODYM import chain
    _lfg_path = _os.path.join(
        _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
        "engine",
        "lfg_model.py",
    )
    _spec = _ilu.spec_from_file_location("lfg_model_cmp", _lfg_path)
    _mod = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    _calculate_lfg_series = _mod._calculate_lfg_series

    time_items = list(mfa_system_results.IndexTable.Classification["Time"].Items)
    elements = mfa_system_results.Elements
    mat_idx = elements.index("material")
    wc_idx = elements.index("WC") if "WC" in elements else None
    toc_idx = elements.index("TOC") if "TOC" in elements else None

    valid_ids = [
        pid
        for pid, p in lfg_params.items()
        if p.get("fractions") and p.get("outflow_ch4_id")
    ]
    if not valid_ids:
        print("No fully configured LFG processes found.")
        return

    process_dropdown = Dropdown(
        options=[(f"Process {pid}", pid) for pid in valid_ids],
        description="LFG Process:",
        style={"description_width": "120px"},
        layout=Layout(width="280px"),
    )

    fig = make_subplots(
        rows=1,
        cols=2,
        column_widths=[0.7, 0.3],
        subplot_titles=["Annual CH4 Production", "Avg. Carbon Input Comparison"],
        specs=[[{"type": "scatter"}, {"type": "bar"}]],
    )
    fig_widget = go.FigureWidget(fig)

    colors = {"ipcc": "#E69F00", "mfa": "#56B4E9", "implied": "#999999"}

    def _get_data(process_id):
        params = lfg_params[process_id]
        fractions = params.get("fractions", [])

        waste_in = np.zeros(len(time_items))
        wc_in = np.zeros(len(time_items))
        toc_in = np.zeros(len(time_items))

        for f in mfa_system_results.FlowDict.values():
            if f.P_End == process_id and f.Values is not None:
                waste_in += f.Values[:, mat_idx]
                if wc_idx is not None:
                    wc_in += f.Values[:, wc_idx]
                if toc_idx is not None:
                    toc_in += f.Values[:, toc_idx]

        # IPCC mode
        r_ipcc = _calculate_lfg_series(waste_in, wc_in, params)
        ch4_ipcc = r_ipcc["ch4_carbon_total"] * (16 / 12)  # Mg CH4

        # IPCC-implied TOC [Mg C/yr] for reference bar
        ipcc_implied_toc = waste_in * sum(
            f["f_input_j"] * f.get("DOC_j", 0.0) for f in fractions
        )

        toc_defined = toc_in.sum() > 0
        ch4_mfa = None
        doc_ratio = None

        if toc_defined:
            mfa_params = copy.deepcopy(params)
            for frac in mfa_params["fractions"]:
                frac["DOC_j"] = 1.0
            r_mfa = _calculate_lfg_series(toc_in, wc_in, mfa_params)
            ch4_mfa = r_mfa["ch4_carbon_total"] * (16 / 12)  # Mg CH4
            ipcc_total = ipcc_implied_toc.sum()
            doc_ratio = toc_in.sum() / ipcc_total if ipcc_total > 0 else float("nan")

        return {
            "time": time_items,
            "ch4_ipcc": ch4_ipcc,
            "ch4_mfa": ch4_mfa,
            "toc_in": toc_in,
            "ipcc_implied_toc": ipcc_implied_toc,
            "doc_ratio": doc_ratio,
            "toc_defined": toc_defined,
        }

    def update_plot(process_id):
        d = _get_data(process_id)
        params = lfg_params[process_id]

        with fig_widget.batch_update():
            fig_widget.data = []

            # --- Left panel: CH4 curves ---
            fig_widget.add_trace(
                go.Scatter(
                    x=d["time"],
                    y=d["ch4_ipcc"],
                    name="IPCC mode (DOC_j)",
                    line=dict(color=colors["ipcc"], width=2),
                    mode="lines",
                    hovertemplate="IPCC<br>Year: %{x}<br>%{y:.1f} Mg CH4<extra></extra>",
                ),
                row=1,
                col=1,
            )

            if d["toc_defined"] and d["ch4_mfa"] is not None:
                fig_widget.add_trace(
                    go.Scatter(
                        x=d["time"],
                        y=d["ch4_mfa"],
                        name="MFA/TOC mode",
                        line=dict(color=colors["mfa"], width=2, dash="dash"),
                        mode="lines",
                        hovertemplate="MFA/TOC<br>Year: %{x}<br>%{y:.1f} Mg CH4<extra></extra>",
                    ),
                    row=1,
                    col=1,
                )
            else:
                # Show IPCC-implied TOC as a dashed guidance line (in CH4-equivalent)
                # using mean DOCf and site params for conversion
                docf = float(params.get("DOCf", 0.5))
                F_CH4 = float(params.get("F_CH4", 0.5))
                MCF = float(params.get("MCF", 1.0))
                OX = float(params.get("OX", 0.1))
                phi = float(params.get("phi", 1.0))
                # Rough single-step conversion: implied TOC × DOCf × gas factors × 16/12
                implied_ch4 = (
                    d["ipcc_implied_toc"]
                    * docf
                    * F_CH4
                    * MCF
                    * (1 - OX)
                    * phi
                    * (16 / 12)
                )
                fig_widget.add_trace(
                    go.Scatter(
                        x=d["time"],
                        y=implied_ch4,
                        name="IPCC-implied TOC (calibration target)",
                        line=dict(color=colors["implied"], width=1.5, dash="dot"),
                        mode="lines",
                        hovertemplate="Implied<br>Year: %{x}<br>%{y:.1f} Mg CH4<extra></extra>",
                    ),
                    row=1,
                    col=1,
                )

            # --- Right panel: carbon input comparison bar ---
            avg_ipcc = float(np.mean(d["ipcc_implied_toc"]))
            bar_labels = ["IPCC DOC\n(literature)"]
            bar_values = [avg_ipcc]
            bar_colors = [colors["ipcc"]]

            if d["toc_defined"]:
                avg_toc = float(np.mean(d["toc_in"]))
                bar_labels.append("Measured TOC\n(MFA)")
                bar_values.append(avg_toc)
                bar_colors.append(colors["mfa"])

            fig_widget.add_trace(
                go.Bar(
                    x=bar_labels,
                    y=bar_values,
                    marker_color=bar_colors,
                    name="Carbon input [Mg C/yr avg]",
                    hovertemplate="%{x}<br>%{y:.1f} Mg C/yr<extra></extra>",
                    showlegend=False,
                ),
                row=1,
                col=2,
            )

            # --- Annotation ---
            if d["toc_defined"] and d["doc_ratio"] is not None:
                ratio = d["doc_ratio"]
                if ratio > 1.5:
                    note = f"⚠ DOC ratio: {ratio:.2f} — TOC likely includes recalcitrant OC; consider re-calibrating DOCf"
                elif ratio < 0.7:
                    note = f"ℹ DOC ratio: {ratio:.2f} — measured TOC is lower than IPCC defaults"
                else:
                    note = f"✓ DOC ratio: {ratio:.2f} — measured TOC is consistent with IPCC defaults"
            else:
                note = "ℹ TOC not defined on input flows — set TOC_[%] in flow definitions to enable MFA mode"

            fig_widget.update_layout(
                title=dict(
                    text=(
                        f"IPCC vs MFA Carbon Accounting — Process {process_id}"
                        f"<br><sup>{note}</sup>"
                    ),
                    font=dict(size=14),
                ),
                xaxis_title="Year",
                yaxis_title="CH4 [Mg CH4/yr]",
                yaxis2_title="Avg. Carbon Input [Mg C/yr]",
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.08, xanchor="left", x=0
                ),
                height=480,
                template="plotly_white",
            )

    process_dropdown.observe(lambda _: update_plot(process_dropdown.value), "value")

    export_btn = Button(
        description="Export PNG/SVG",
        button_style="success",
        icon="download",
        layout=Layout(width="160px"),
    )

    def _do_ipcc_export(b):
        try:
            name = f"lfg_ipcc_vs_mfa_{process_dropdown.value}".replace(" ", "_")
            paths = export_figure(
                fig_widget,
                name,
                formats=["png", "svg"],
                quality="publication",
                size="large",
            )
            print(f"✅ Exported: {', '.join(paths)}")
        except Exception as e:
            print(f"❌ Export failed: {e}")

    export_btn.on_click(_do_ipcc_export)

    display(HBox([process_dropdown, export_btn]))
    display(fig_widget)
    update_plot(valid_ids[0])


def plot_lfg_fraction_breakdown(mfa_system_results, lfg_params):
    """Stacked area chart of LFG gas production broken down by waste fraction.

    Mirrors the DSM stock details style: each waste fraction is a separate
    coloured area. Works by re-running ``_calculate_lfg_series`` from the
    inflows already stored in the MFA system, so no extra solver output is
    needed.

    Parameters
    ----------
    mfa_system_results : odym.MFAsystem
        Solved MFA system.
    lfg_params : dict
        LFG parameter config from ``data_loader.load_lfg_parameters()``.
    """
    if not lfg_params:
        print("No LFG processes found to plot.")
        return

    import importlib.util as _ilu
    import os as _os

    # Load _calculate_lfg_series directly to avoid ODYM import chain
    _lfg_path = _os.path.join(
        _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
        "engine",
        "lfg_model.py",
    )
    _spec = _ilu.spec_from_file_location("lfg_model_plot", _lfg_path)
    _mod = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    _calculate_lfg_series = _mod._calculate_lfg_series

    time_items = list(mfa_system_results.IndexTable.Classification["Time"].Items)
    elements = mfa_system_results.Elements
    mat_idx = elements.index("material")
    try:
        wc_idx = elements.index("WC")
    except ValueError:
        wc_idx = None

    # Collect only processes that have complete params (fractions + outflow IDs)
    valid_ids = [
        pid
        for pid, p in lfg_params.items()
        if p.get("fractions") and p.get("outflow_ch4_id")
    ]
    if not valid_ids:
        print(
            "No fully configured LFG processes found (missing fractions or outflow IDs)."
        )
        return

    process_ids = valid_ids

    process_dropdown = Dropdown(
        options=[(f"Process {pid}", pid) for pid in process_ids],
        description="LFG Process:",
        style={"description_width": "120px"},
        layout=Layout(width="280px"),
    )
    gas_dropdown = Dropdown(
        options=[("CH4 [Mg CH4]", "ch4"), ("CO2 biogenic [Mg CO2]", "co2")],
        value="ch4",
        description="Gas:",
        style={"description_width": "80px"},
        layout=Layout(width="260px"),
    )
    cumulative_checkbox = Checkbox(value=False, description="Cumulative", indent=False)
    export_button = Button(
        description="Export Plot",
        button_style="info",
        tooltip="Export current plot as PNG",
    )

    fig = go.FigureWidget()

    # Fraction colours — cycle through a qualitative palette
    _PALETTE = [
        "#E64B35",
        "#4DBBD5",
        "#00A087",
        "#3C5488",
        "#F39B7F",
        "#8491B4",
        "#91D1C2",
        "#DC0000",
        "#7E6148",
        "#B09C85",
    ]

    def _get_series(process_id, gas):
        """Return per-fraction arrays and time labels for the chosen gas."""
        params = lfg_params[process_id]

        # Sum all material inflows to this process
        waste_in = np.zeros(len(time_items))
        wc_in = np.zeros(len(time_items))
        for f in mfa_system_results.FlowDict.values():
            if f.P_End == process_id and f.Values is not None:
                waste_in += f.Values[:, mat_idx]
                if wc_idx is not None:
                    wc_in += f.Values[:, wc_idx]

        # Per-fraction gas output (Mg C)
        F_CH4 = params.get("F_CH4", 0.5)
        MCF = params.get("MCF", 0.8)
        OX = params.get("OX", 0.1)
        fracs = params["fractions"]

        series = {}
        for frac in fracs:
            name = frac["name"]
            # Re-run single fraction to get exact decay (avoids re-implementing)
            single_params = {
                "fractions": [frac],
                "MCF": MCF,
                "DOCf": params.get("DOCf", 0.5),
                "F_CH4": F_CH4,
                "OX": OX,
                "phi": params.get("phi", 1.0),
            }
            r = _calculate_lfg_series(waste_in, wc_in, single_params)
            if gas == "ch4":
                # Convert CH4-C → Mg CH4:  ×16/12
                series[name] = r["ch4_carbon_total"] * (16 / 12)
            else:
                # Convert CO2-C → Mg CO2:  ×44/12
                series[name] = r["co2_carbon_total"] * (44 / 12)

        return series

    def update_plot(process_id, gas, cumulative):
        series = _get_series(process_id, gas)

        if not series:
            return

        with fig.batch_update():
            fig.data = []
            for i, (name, vals) in enumerate(series.items()):
                y = np.cumsum(vals) if cumulative else vals
                color = _PALETTE[i % len(_PALETTE)]
                fig.add_trace(
                    go.Scatter(
                        x=time_items,
                        y=y,
                        name=name,
                        mode="lines",
                        line=dict(color=color, width=0.5),
                        stackgroup="one",
                        fill="tonexty" if i > 0 else "tozeroy",
                        hovertemplate=(
                            f"<b>{name}</b><br>Year: %{{x}}<br>%{{y:.1f}}<extra></extra>"
                        ),
                    )
                )

            process_name = next(
                (p.Name for p in mfa_system_results.ProcessList if p.ID == process_id),
                f"Process {process_id}",
            )
            gas_label = "CH₄ [Mg CH4]" if gas == "ch4" else "CO₂ biogenic [Mg CO2]"
            cum_tag = " — Cumulative" if cumulative else ""
            layout_config = get_publication_layout(
                custom_title=f"LFG Gas Production: {process_name}{cum_tag} — Stacked by Fraction",
                x_title="Year",
                y_title=gas_label,
                show_grid=True,
                scientific_y=False,
            )
            fig.update_layout(**layout_config)

    def export_plot():
        try:
            paths = export_figure(
                fig,
                "lfg_fraction_breakdown",
                formats=["png", "svg"],
                quality="publication",
                size="large",
                timestamp=False,
            )
            print(f"Exported: {', '.join(paths)}")
        except Exception as e:
            print(f"Export failed: {e}")

    export_button.on_click(lambda b: export_plot())

    def on_change(_):
        update_plot(
            process_dropdown.value, gas_dropdown.value, cumulative_checkbox.value
        )

    process_dropdown.observe(on_change, "value")
    gas_dropdown.observe(on_change, "value")
    cumulative_checkbox.observe(on_change, "value")

    controls = HBox(
        [
            VBox(
                [process_dropdown, gas_dropdown, cumulative_checkbox],
                layout=Layout(width="320px"),
            ),
            VBox([export_button], layout=Layout(width="150px")),
        ],
        layout=Layout(justify_content="space-between"),
    )
    display(controls)
    display(fig)
    update_plot(process_ids[0], "ch4", False)


# ---------------------------------------------------------------------------
# BOM Assembler
# ---------------------------------------------------------------------------


def plot_bom_assembly_flows(mfa_system_results, bom_params):
    """Interactive assembly efficiency plot for BOM_Assembler processes.

    Shows — per process and element:
      • Assembled product (target_Product flows, stacked)
      • Residue / unused material (Unused_Material flows, stacked)
      • Total inflow as a reference line
      • Assembly efficiency (%) on a secondary y-axis

    Parameters
    ----------
    mfa_system_results : odym.MFAsystem
        Solved MFA system with calculated flow values.
    bom_params : dict
        BOM configuration as returned by ``data_loader.load_bom_parameters()``.
    """
    if not bom_params:
        print("No BOM Assembler processes found to plot.")
        return

    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    from ipywidgets import Dropdown, HBox, Layout
    from IPython.display import display

    time_items = list(mfa_system_results.IndexTable.Classification["Time"].Items)
    elements = mfa_system_results.Elements
    n_time = len(time_items)

    # Colours consistent with Sankey theme
    _ASSEMBLED_COLOR = "#7B2D8B"  # purple — matches BOM_Assembler Sankey node
    _RESIDUE_COLOR = "#B0B0B0"  # grey
    _INFLOW_COLOR = "#333333"  # near-black reference line
    _EFFICIENCY_COLOR = "#F18F01"  # orange for efficiency trace

    # Build process name map
    process_name = {p.ID: p.Name for p in mfa_system_results.ProcessList}

    process_ids = list(bom_params.keys())
    process_opts = [
        (f"{process_name.get(pid, str(pid))} (P{pid})", pid) for pid in process_ids
    ]
    process_dropdown = Dropdown(
        options=process_opts, description="Process:", layout=Layout(width="320px")
    )
    element_dropdown = Dropdown(
        options=elements,
        value=elements[0],
        description="Element:",
        layout=Layout(width="200px"),
    )

    fig = go.FigureWidget(
        make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            row_heights=[0.65, 0.35],
            vertical_spacing=0.08,
            subplot_titles=["Mass Flow (Mg)", "Assembly Efficiency (%)"],
        )
    )
    # Add dummy traces for legend ordering
    fig.add_trace(
        go.Bar(
            name="Assembled product",
            marker_color=_ASSEMBLED_COLOR,
            x=time_items,
            y=[0] * n_time,
            showlegend=True,
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Bar(
            name="Unused material (residue)",
            marker_color=_RESIDUE_COLOR,
            x=time_items,
            y=[0] * n_time,
            showlegend=True,
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            name="Total inflow",
            line=dict(color=_INFLOW_COLOR, width=2, dash="dash"),
            x=time_items,
            y=[0] * n_time,
            showlegend=True,
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            name="Efficiency (%)",
            line=dict(color=_EFFICIENCY_COLOR, width=2),
            x=time_items,
            y=[0] * n_time,
            showlegend=True,
        ),
        row=2,
        col=1,
    )

    fig.update_layout(
        barmode="stack",
        height=600,
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=60, r=40, t=80, b=40),
    )
    fig.update_yaxes(title_text="Mass (Mg)", row=1, col=1)
    fig.update_yaxes(title_text="Efficiency (%)", range=[0, 105], row=2, col=1)

    def update_plot(process_id, element):
        cfg = bom_params[process_id]
        elem_idx = elements.index(element)

        # --- Sum all inflows ---
        inflow_vals = sum(
            (
                f.Values[:, elem_idx]
                for f in mfa_system_results.FlowDict.values()
                if f.P_End == process_id
            ),
            start=__import__("numpy").zeros(n_time),
        )

        # --- Sum target_Product flows ---
        target_fids = [tf["flow_id"] for tf in cfg.get("target_flows", [])]
        assembled_vals = sum(
            (
                mfa_system_results.FlowDict[fid].Values[:, elem_idx]
                for fid in target_fids
                if fid in mfa_system_results.FlowDict
            ),
            start=__import__("numpy").zeros(n_time),
        )

        # --- Sum Unused_Material flows ---
        residue_fids = cfg.get("residue_flows", [])
        residue_vals = sum(
            (
                mfa_system_results.FlowDict[fid].Values[:, elem_idx]
                for fid in residue_fids
                if fid in mfa_system_results.FlowDict
            ),
            start=__import__("numpy").zeros(n_time),
        )

        # --- Assembly efficiency ---
        import numpy as np

        with np.errstate(divide="ignore", invalid="ignore"):
            efficiency = np.where(
                inflow_vals > 0, assembled_vals / inflow_vals * 100, 0.0
            )

        pname = process_name.get(process_id, str(process_id))
        with fig.batch_update():
            fig.data[0].x = time_items
            fig.data[0].y = assembled_vals.tolist()
            fig.data[1].x = time_items
            fig.data[1].y = residue_vals.tolist()
            fig.data[2].x = time_items
            fig.data[2].y = inflow_vals.tolist()
            fig.data[3].x = time_items
            fig.data[3].y = efficiency.tolist()
            fig.layout.title = f"BOM Assembly — {pname} | Element: {element}"

    def on_change(_):
        update_plot(process_dropdown.value, element_dropdown.value)

    process_dropdown.observe(on_change, "value")
    element_dropdown.observe(on_change, "value")

    controls = HBox([process_dropdown, element_dropdown], layout=Layout(gap="10px"))
    display(controls)
    display(fig)
    update_plot(process_ids[0], elements[0])
