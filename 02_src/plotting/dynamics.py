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
from .themes import apply_theme, get_active_theme, get_publication_layout, FONT_SIZE
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
                        y=flow.Values[:, element_index],
                        name=display_name,
                        stackgroup="input",
                        fill="tonexty" if i > 0 else "tozeroy",
                        mode="lines",
                        line=dict(width=0.5),
                        hovertemplate=f"<b>{display_name}</b><br>Year: %{{x}}<br>{element}: %{{y:.2e}} Mg<extra></extra>",
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
                    y=stock.Values[:, element_index],
                    name=f"Stock: {stock_display}",
                    mode="lines",
                    line=dict(width=3, color="#2E86AB"),
                    hovertemplate=f"<b>Stock: {stock_display}</b><br>Year: %{{x}}<br>{element}: %{{y:.2e}} Mg<extra></extra>",
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
                        y=flow.Values[:, element_index],
                        name=display_name,
                        stackgroup="output",
                        fill="tonexty" if i > 0 else "tozeroy",
                        mode="lines",
                        line=dict(width=0.5),
                        hovertemplate=f"<b>{display_name}</b><br>Year: %{{x}}<br>{element}: %{{y:.2e}} Mg<extra></extra>",
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
        layout_config["margin"] = {"t": 80, "b": 150 if _t["legend_below"] else 80, "l": 60, "r": 30}

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
                fig, "dsm_process_dynamics",
                formats=["png", "svg"], quality="publication", size="large", timestamp=False,
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

            # Only add Initial Stock trace if there's actually any initial stock data
            # (i.e., not all zeros - which means Stock_Configuration doesn't use initial stock)
            if np.any(initial_stock_element > 1e-10):
                fig.add_trace(
                    go.Scatter(
                        x=time_items,
                        y=initial_stock_element,
                        mode="lines",
                        name="Initial Stock (Decaying)",
                        line=dict(color=colors["initial_stock"], width=0.5, dash="dash"),
                        stackgroup="one",
                        fill="tozeroy",
                        hovertemplate="<b>Initial Stock</b><br>Year: %{x}<br>Mass: %{y:.2f} Mg<extra></extra>",
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
                        y=stock_ts_element,
                        mode="lines",
                        name=category_display,
                        line=dict(width=0.5),
                        stackgroup="one",
                        fill="tonexty",
                        hovertemplate=f"<b>{category_display}</b><br>Year: %{{x}}<br>Mass: %{{y:.2f}} Mg<extra></extra>",
                    )
                )

            process_name = next(
                (p.Name for p in mfa_system_results.ProcessList if p.ID == process_id),
                f"Process {process_id}",
            )
            layout_config = get_publication_layout(
                custom_title=f"DSM - In-Use Stock by Cohort - {process_name} ({element.upper()})",
                x_title="Year",
                y_title="Stock (Mg)",
                show_grid=True,
                scientific_y=True,
            )
            apply_theme(layout_config)
            fig.update_layout(**layout_config)

    process_dropdown = Dropdown(
        options=list(dsm_params.keys()),
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
                fig, "dsm_stock_analysis",
                formats=["png", "svg"], quality="publication", size="large", timestamp=False,
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

    from ipywidgets import Dropdown, HBox, VBox, HTML, Layout, Button
    from IPython.display import display

    time_items = mfa_system_results.IndexTable.Classification["Time"].Items
    element_items = mfa_system_results.Elements

    # Publication line style scheme (JIE single-column)
    def _auto_scale(max_val):
        """Return (scale_factor, prefix_str) so displayed values stay in 0.1–999 range."""
        if max_val >= 1e8:
            return 1e9, "×10⁹ "
        elif max_val >= 1e5:
            return 1e6, "×10⁶ "
        elif max_val >= 1e2:
            return 1e3, "×10³ "
        return 1.0, ""

    _PUB = {
        "stock":      dict(color="black",   width=2, dash="solid"),
        "input":      dict(color="grey",    width=2, dash="dash"),
        "output":     dict(color="darkred", width=2, dash="dot"),
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
                (p.ID for p in mfa_system_results.ProcessList
                 if p.Name == comparison_process),
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

        _raw_all = [stock_raw,
                    np.cumsum(inflow_ts) if show_cumulative == "Cumulative Values" else inflow_ts,
                    np.cumsum(outflow_ts) if show_cumulative == "Cumulative Values" else outflow_ts]
        if _cmp_id is not None:
            cmp_obj_raw = mfa_system_results.StockDict.get(f"S_{_cmp_id}")
            if cmp_obj_raw is not None:
                _raw_all.append(cmp_obj_raw.Values[:, element_index])
        _max_raw = max(float(np.nanmax(np.abs(v))) for v in _raw_all if np.any(np.isfinite(v)))
        _scale, _prefix = _auto_scale(_max_raw)

        is_carbon = element in ("TC", "CC")
        base = "Mg C" if is_carbon else "Mg"
        axis_unit = f"{_prefix}{base}".strip()
        y_label = (f"Carbon Stock ({axis_unit})" if is_carbon
                   else f"{element} ({axis_unit})")

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
                    fig.add_trace(go.Scatter(
                        x=time_items,
                        y=cmp_stock_obj.Values[:, element_index] / _scale,
                        mode="lines",
                        name=f"Stock \u2013 {_cmp_name}",
                        line=_PUB["comparison"],
                        hovertemplate=(
                            f"<b>Stock \u2013 {_cmp_name}</b><br>"
                            f"Year: %{{x}}<br>Value: %{{y:.3f}} {axis_unit}<extra></extra>"
                        ),
                    ))

            stock_label = f"Stock \u2013 {process_name}" if _cmp_id is not None else "Carbon Stock"
            fig.add_trace(go.Scatter(
                x=time_items,
                y=stock_raw / _scale,
                mode="lines",
                name=stock_label,
                line=_PUB["stock"],
                hovertemplate=(
                    f"<b>Stock</b><br>Year: %{{x}}<br>Value: %{{y:.3f}} {axis_unit}<extra></extra>"
                ),
            ))

            if show_cumulative == "Cumulative Values":
                fig.add_trace(go.Scatter(
                    x=time_items, y=np.cumsum(inflow_ts) / _scale,
                    mode="lines", name="Cumulative Input", line=_PUB["input"],
                    hovertemplate=f"<b>Cumulative Input</b><br>Year: %{{x}}<br>Value: %{{y:.3f}} {axis_unit}<extra></extra>",
                ))
                fig.add_trace(go.Scatter(
                    x=time_items, y=np.cumsum(outflow_ts) / _scale,
                    mode="lines", name="Cumulative Carbon Emissions", line=_PUB["output"],
                    hovertemplate=f"<b>Cumulative Carbon Emissions</b><br>Year: %{{x}}<br>Value: %{{y:.3f}} {axis_unit}<extra></extra>",
                ))
            else:
                fig.add_trace(go.Scatter(
                    x=time_items, y=inflow_ts / _scale,
                    mode="lines", name="Annual Input", line=_PUB["input"],
                    hovertemplate=f"<b>Annual Input</b><br>Year: %{{x}}<br>Value: %{{y:.3f}} {axis_unit}<extra></extra>",
                ))
                fig.add_trace(go.Scatter(
                    x=time_items, y=outflow_ts / _scale,
                    mode="lines", name="Annual Carbon Emissions", line=_PUB["output"],
                    hovertemplate=f"<b>Annual Carbon Emissions</b><br>Year: %{{x}}<br>Value: %{{y:.3f}} {axis_unit}<extra></extra>",
                ))

            _y_upper = math.ceil((_max_raw / _scale) * 2) / 2 + 0.5
            layout_config = get_publication_layout(
                custom_title=f"FOMP - First-Order Decay Stock - {process_name}",
                x_title="Year",
                y_title=y_label,
                show_grid=True,
                y_range=[0, _y_upper],
            )
            apply_theme(layout_config)
            layout_config["yaxis"]["tickformat"] = None
            fig.update_layout(**layout_config)

    def export_plot():
        try:
            current_process_name = process_dropdown.value
            current_element = element_dropdown.value
            filename = f"fomp_{current_process_name.replace(' ', '_')}_{current_element}"
            paths = export_figure(
                fig, filename,
                formats=["png", "svg"], quality="publication", size="large", timestamp=False,
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
    _tc = next((e for e in ("TC", "CC") if e in element_items), element_items[0])

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

    ui = VBox([
        HBox([process_dropdown, element_dropdown, cumulative_checkbox]),
        HBox([export_button]),
    ])

    def _on_change(change):
        update_plot(process_options[process_dropdown.value], element_dropdown.value, cumulative_checkbox.value)

    process_dropdown.observe(_on_change, "value")
    element_dropdown.observe(_on_change, "value")
    cumulative_checkbox.observe(_on_change, "value")

    display(ui)
    display(fig)
    update_plot(process_options[process_dropdown.value], element_dropdown.value, cumulative_checkbox.value)


def plot_fomp_stock_comparison(mfa_system_results, fomp_params, element=None):
    """Overlay TC stock trajectories of all FOMP processes on one figure.

    Produces a publication-ready static Plotly figure (JIE single-column
    format) showing the carbon stock evolution of every FOMP process in a
    single diagram. Useful for direct scenario / process comparison.

    Parameters
    ----------
    mfa_system_results : odym.MFAsystem
        The solved MFA system object.
    fomp_params : dict
        FOMP parameters dict (keyed by process ID) — used to identify which
        processes to include.
    element : str or None
        Element to plot. Defaults to TC/CC (with legacy fallback). Pass any
        element name present in ``mfa_system_results.Elements`` to override.
    """
    if not fomp_params:
        print("No FOMP processes found to plot.")
        return

    from IPython.display import display
    import math

    element_items = mfa_system_results.Elements
    time_items = mfa_system_results.IndexTable.Classification["Time"].Items

    # Element selection: honour explicit arg, else prefer TC/CC
    if element is None:
        element = next((e for e in ("TC", "CC") if e in element_items), element_items[0])
    if element not in element_items:
        print(f"⚠️  Element '{element}' not in system — available: {element_items}")
        return
    elem_idx = element_items.index(element)
    # Color sequence for up to 8 processes (colorblind-friendly)
    _COLORS = [
        "black", "steelblue", "#E69F00", "#009E73",
        "#CC79A7", "#56B4E9", "#D55E00", "#F0E442",
    ]
    _DASHES = ["solid", "solid", "dash", "dash", "dot", "dot", "dashdot", "dashdot"]

    # Gather processes: iterate ProcessList in definition order
    procs = [
        p for p in mfa_system_results.ProcessList
        if p.ID in fomp_params and p.ID != 0
    ]
    if not procs:
        print("⚠️  No FOMP processes found in ProcessList.")
        return

    # --- Pass 1: find raw max across all processes to determine scale ---
    raw_maxes = []
    for proc in procs:
        s = mfa_system_results.StockDict.get(f"S_{proc.ID}")
        if s is not None:
            raw_maxes.append(float(np.nanmax(np.abs(s.Values[:, elem_idx]))))
    if not raw_maxes:
        print("⚠️  No stock data found for any FOMP process.")
        return

    def _auto_scale_cmp(max_val):
        if max_val >= 1e8:
            return 1e9, "×10⁹ "
        elif max_val >= 1e5:
            return 1e6, "×10⁶ "
        elif max_val >= 1e2:
            return 1e3, "×10³ "
        return 1.0, ""

    _scale, _prefix = _auto_scale_cmp(max(raw_maxes))
    is_carbon = element in ("TC", "CC")
    base = "Mg C" if is_carbon else "Mg"
    axis_unit = f"{_prefix}{base}".strip()
    y_label = f"Carbon Stock ({axis_unit})" if is_carbon else f"{element} ({axis_unit})"

    # --- Pass 2: build figure ---
    fig = go.Figure()

    for i, proc in enumerate(procs):
        stock_obj = mfa_system_results.StockDict.get(f"S_{proc.ID}")
        if stock_obj is None:
            continue
        y = stock_obj.Values[:, elem_idx] / _scale
        color = _COLORS[i % len(_COLORS)]
        dash = _DASHES[i % len(_DASHES)]
        fig.add_trace(go.Scatter(
            x=time_items, y=y,
            mode="lines", name=proc.Name,
            line=dict(color=color, width=2, dash=dash),
            hovertemplate=(
                f"<b>{proc.Name}</b><br>"
                f"Year: %{{x}}<br>Value: %{{y:.3f}} {axis_unit}<extra></extra>"
            ),
        ))

    _y_upper = math.ceil((max(raw_maxes) / _scale) * 2) / 2 + 0.5

    layout_config = get_publication_layout(
        custom_title="FOMP - First-Order Decay Stock Comparison",
        x_title="Year",
        y_title=y_label,
        show_grid=True,
        y_range=[0, _y_upper],
    )
    apply_theme(layout_config)
    layout_config["yaxis"]["tickformat"] = None
    fig.update_layout(**layout_config)

    display(fig)


def plot_fomp_pool_breakdown(mfa_system_results, fomp_params, fomp_details, element=None):
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

    _tc_name = next((e for e in ("TC", "CC") if e in element_items), None)
    if element is None:
        element = _tc_name if _tc_name else element_items[0]
    use_tc = element in ("TC", "CC")

    procs = [
        p for p in mfa_system_results.ProcessList
        if p.ID in fomp_details and p.ID != 0
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

    _COLOR_LABILE       = "#E69F00"
    _COLOR_RECALCITRANT = "#0072B2"

    fig = go.FigureWidget(make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=["Pool Stocks", "Annual Decay Emissions"],
    ))

    def _auto_scale_val(max_val):
        if max_val >= 1e8:
            return 1e9, "×10⁹ "
        elif max_val >= 1e5:
            return 1e6, "×10⁶ "
        elif max_val >= 1e2:
            return 1e3, "×10³ "
        return 1.0, ""

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

        base = "Mg C" if use_tc else "Mg"
        sc_s, pfx_s = _auto_scale_val(float(np.nanmax(s_lab + s_rec)))
        sc_e, pfx_e = _auto_scale_val(float(np.nanmax(e_lab + e_rec)))
        unit_s = f"{pfx_s}{base}".strip()
        unit_e = f"{pfx_e}{base}/yr".strip()

        with fig.batch_update():
            fig.data = []

            # --- Row 1: stacked pool stocks ---
            fig.add_trace(go.Scatter(
                x=time_items, y=s_lab / sc_s,
                name="Labile Pool", legendgroup="labile",
                mode="lines", fill="tozeroy",
                line=dict(color=_COLOR_LABILE, width=1.5),
                fillcolor="rgba(230,159,0,0.35)",
                hovertemplate=f"<b>Labile Stock</b><br>Year: %{{x}}<br>%{{y:.4f}} {unit_s}<extra></extra>",
            ), row=1, col=1)
            fig.add_trace(go.Scatter(
                x=time_items, y=(s_lab + s_rec) / sc_s,
                name="Recalcitrant Pool", legendgroup="recalcitrant",
                mode="lines", fill="tonexty",
                line=dict(color=_COLOR_RECALCITRANT, width=1.5),
                fillcolor="rgba(0,114,178,0.35)",
                hovertemplate=f"<b>Recalcitrant Stock</b><br>Year: %{{x}}<br>Total: %{{y:.4f}} {unit_s}<extra></extra>",
            ), row=1, col=1)

            # --- Row 2: annual decay emissions — individual lines (not stacked) ---
            # Non-stacked so both pools are visible even when magnitudes differ greatly
            fig.add_trace(go.Scatter(
                x=time_items, y=e_lab / sc_e,
                name="Labile Pool", legendgroup="labile", showlegend=False,
                mode="lines",
                line=dict(color=_COLOR_LABILE, width=2, dash="solid"),
                hovertemplate=f"<b>Labile Decay</b><br>Year: %{{x}}<br>%{{y:.4f}} {unit_e}<extra></extra>",
            ), row=2, col=1)
            fig.add_trace(go.Scatter(
                x=time_items, y=e_rec / sc_e,
                name="Recalcitrant Pool", legendgroup="recalcitrant", showlegend=False,
                mode="lines",
                line=dict(color=_COLOR_RECALCITRANT, width=2, dash="dash"),
                hovertemplate=f"<b>Recalcitrant Decay</b><br>Year: %{{x}}<br>%{{y:.4f}} {unit_e}<extra></extra>",
            ), row=2, col=1)

            t = get_active_theme()
            fig.update_layout(
                title=dict(text=f"FOMP - First-Order Decay Pools - {process_name}")
                      if t["show_title"] else {},
                width=t["width"], height=t["height"],
                margin=t["margin"],
                plot_bgcolor="white",
                paper_bgcolor="white",
                legend=dict(font=dict(size=t["font_legend"])),
                uirevision="constant",
            )
            if t["legend_below"]:
                fig.update_layout(legend=dict(
                    orientation="h", yanchor="top", y=-0.12,
                    xanchor="center", x=0.5,
                ))
            grid = t["grid_color"]
            for row in (1, 2):
                fig.update_xaxes(
                    showgrid=True, gridcolor=grid,
                    tickfont=dict(size=t["font_tick"]),
                    row=row, col=1,
                )
            fig.update_yaxes(
                title_text=f"Stock ({unit_s})",
                showgrid=True, gridcolor=grid, tickformat=None,
                title_font=dict(size=t["font_axis"]),
                tickfont=dict(size=t["font_tick"]),
                row=1, col=1,
            )
            fig.update_yaxes(
                title_text=f"Decay ({unit_e})",
                showgrid=True, gridcolor=grid, tickformat=None,
                title_font=dict(size=t["font_axis"]),
                tickfont=dict(size=t["font_tick"]),
                row=2, col=1,
            )
            fig.update_xaxes(
                title_text="Year",
                title_font=dict(size=t["font_axis"]),
                row=2, col=1,
            )

    process_dropdown.observe(lambda c: update_plot(c["new"]), names="value")
    display(HBox([process_dropdown]))
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

    display(HBox([element_dropdown, metric_dropdown]))
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
                y=total_stock,
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
        y_title="Total Stock (Mg)",
        show_grid=True,
        size="medium",
    )
    fig.update_layout(**layout_config)

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
            rows=1, cols=3,
            subplot_titles=("Inflow", "Stock (S)", "Outflow"),
            horizontal_spacing=0.08,
        )
    )

    def update_plot(process_name, element):
        pid = process_options[process_name]
        element_index = element_items.index(element)

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
                    y=inflow_ts,
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
                    y=stock_ts,
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
                    y=outflow_ts,
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

        # Get composition of the mixed inflow for the new stock parts
        inflows = [
            f.Values
            for f in mfa_system_results.FlowDict.values()
            if f.P_End == process_id
        ]
        total_inflow_values = (
            sum(inflows) if inflows else np.zeros((len(time_axis), len(element_items)))
        )
        with fig.batch_update():
            fig.data = []
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
                    y=initial_stock_ts_element,
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
                        y=stock_ts_element,
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
                y_title="Stock (Mg)",
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
        update_plot(process_dropdown.value, element_dropdown.value, chart_type_checkbox.value)

    process_dropdown.observe(_on_change, "value")
    element_dropdown.observe(_on_change, "value")
    chart_type_checkbox.observe(_on_change, "value")

    display(HBox([process_dropdown, element_dropdown, chart_type_checkbox]))
    display(fig)
    update_plot(process_dropdown.value, element_dropdown.value, chart_type_checkbox.value)


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

        # Get the time series data for the selected process
        inflow_ts = sum(
            f.Values[:, element_index]
            for f in mfa_system_results.FlowDict.values()
            if f.P_End == pid
        )
        stock_obj = mfa_system_results.StockDict.get(f"S_{pid}")
        stock_ts = stock_obj.Values[:, element_index] if stock_obj is not None else np.zeros(len(time_axis))
        outflow_ts = sum(
            f.Values[:, element_index]
            for f in mfa_system_results.FlowDict.values()
            if f.P_Start == pid
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
            xaxis_style = layout_config.pop("xaxis")
            yaxis_style = layout_config.pop("yaxis")
            fig.update_layout(**layout_config)
            fig.update_xaxes(title_text="Year", **xaxis_style)
            fig.update_yaxes(title_text="Mass (Mg)", **yaxis_style)

    # Create widgets for interaction
    process_dropdown = Dropdown(
        options=list(process_options.keys()), description="Process:"
    )
    element_dropdown = Dropdown(
        options=element_items, value=element_items[0], description="Element:"
    )

    def _on_change(change):
        update_plot(process_dropdown.value, element_dropdown.value)

    process_dropdown.observe(_on_change, "value")
    element_dropdown.observe(_on_change, "value")

    display(HBox([process_dropdown, element_dropdown]))
    display(fig)
    update_plot(process_dropdown.value, element_dropdown.value)


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
                            y=flow_obj.Values[:, element_index],
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
                y_title="Mass (Mg)",
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
            df_filtered = df[(df["Year"] == year) & (df["Element"] == element)]

            # Determine colors based on value (positive/negative)
            colors = [
                "#0173B2" if val >= 0 else "#CC79A7" for val in df_filtered["Value"]
            ]

            fig.add_trace(
                go.Bar(
                    x=df_filtered["Process"],
                    y=df_filtered["Value"],
                    marker_color=colors,
                    hovertemplate="<b>%{x}</b><br>Stock: %{y:.2f} Mg<extra></extra>",
                )
            )

            layout_config = get_publication_layout(
                custom_title=f"{title} - {element.upper()} ({year})",
                x_title="Process Name",
                y_title="Stock (Mg)",
                show_grid=True,
                scientific_y=True,
            )
            apply_theme(layout_config)
            layout_config["xaxis"].pop("range", None)  # categorical axis, not time-series
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

    display(HBox([year_slider, element_dropdown]))
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
                                y=stock_values,
                                name=f"{process_name}",
                                hovertemplate=f"<b>{process_name}</b><br>Year: %{{x}}<br>Stock: %{{y:.2e}} Mg<extra></extra>",
                            )
                        )
                    else:
                        fig.add_trace(
                            chart_type(
                                x=time_items,
                                y=stock_values,
                                mode="lines",
                                name=f"{process_name}",
                                hovertemplate=f"<b>{process_name}</b><br>Year: %{{x}}<br>Stock: %{{y:.2e}} Mg<extra></extra>",
                            )
                        )

            # Apply publication layout
            layout_config = get_publication_layout(
                custom_title=f"Stock Composition by Process - {element.upper()}",
                x_title="Year",
                y_title=f"Stock ({element.upper()}) (Mg)",
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
    controls = HBox(
        [element_dropdown, chart_type_checkbox],
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
    from ipywidgets import Dropdown, Checkbox, HBox, VBox, Layout
    from IPython.display import display

    time_items = list(mfa_system_results.IndexTable.Classification["Time"].Items)
    elements = mfa_system_results.Elements

    # Accept "TOC" (new hierarchy) → "TC" → "CC" (legacy) for gas carbon values
    cc_idx = next((elements.index(e) for e in ("TOC", "TC", "CC") if e in elements), None)
    if cc_idx is None:
        print("   ⚠️  No carbon element found (TOC/TC/CC) — skipping LFG gas plot.")
        return

    colors = {
        "ch4": "#E69F00",   # Orange for CH4
        "co2": "#56B4E9",   # Sky blue for CO2
        "stock": "#009E73", # Green for stable stock
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
            fig.add_trace(go.Scatter(
                x=time_items, y=ch4_plot,
                name="CH4 (Mg C)", mode="lines+markers",
                line=dict(color=colors["ch4"], width=2, dash="dash"),
                marker=dict(symbol="circle", size=5),
                hovertemplate="<b>CH4</b><br>Year: %{x}<br>%{y:.2f} Mg C<extra></extra>",
            ))
            fig.add_trace(go.Scatter(
                x=time_items, y=co2_plot,
                name="biogenic CO2 (Mg C)", mode="lines+markers",
                line=dict(color=colors["co2"], width=2),
                marker=dict(symbol="square", size=5),
                hovertemplate="<b>CO2 (bio)</b><br>Year: %{x}<br>%{y:.2f} Mg C<extra></extra>",
            ))
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

    controls = HBox([process_dropdown, cumulative_checkbox])
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
    from ipywidgets import Dropdown, Checkbox, HBox, Layout
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
        stock_vals = stock_obj.Values[:, mat_idx] if stock_obj is not None else np.zeros(len(time_items))

        inflow_vals = sum(
            f.Values[:, mat_idx]
            for f in mfa_system_results.FlowDict.values()
            if f.P_End == process_id
        )

        gas_out = np.zeros(len(time_items))
        for fid in [ch4_id, co2_id]:
            if fid and fid in mfa_system_results.FlowDict:
                gas_out = gas_out + mfa_system_results.FlowDict[fid].Values[:, mat_idx]

        with fig.batch_update():
            fig.data = []
            fig.add_trace(go.Scatter(
                x=time_items, y=stock_vals,
                name="Stable Stock (Mg)", mode="lines",
                line=dict(color=colors["stock"], width=3),
                hovertemplate="<b>Stock</b><br>Year: %{x}<br>%{y:.2f} Mg<extra></extra>",
            ))
            fig.add_trace(go.Bar(
                x=time_items, y=inflow_vals,
                name="Waste Inflow (Mg)", opacity=0.5,
                marker_color=colors["inflow"],
            ))
            fig.add_trace(go.Bar(
                x=time_items, y=gas_out,
                name="Gas Output (CH4+CO2, Mg C)", opacity=0.5,
                marker_color=colors["gas_out"],
            ))
            fig.layout.title = f"LFG Stable Stock — Process {process_id}"

    _layout = get_publication_layout(
        x_title="Year",
        y_title="Mass (Mg)",
        show_grid=True,
        scientific_y=False,
    )
    apply_theme(_layout)
    _layout["barmode"] = "overlay"
    fig.update_layout(**_layout)

    process_dropdown.observe(lambda _: update_plot(process_dropdown.value), "value")

    display(process_dropdown)
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
        "engine", "lfg_model.py",
    )
    _spec = _ilu.spec_from_file_location("lfg_model_cmp", _lfg_path)
    _mod = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    _calculate_lfg_series = _mod._calculate_lfg_series

    time_items = list(mfa_system_results.IndexTable.Classification["Time"].Items)
    elements = mfa_system_results.Elements
    mat_idx = elements.index("material")
    wc_idx  = elements.index("WC") if "WC" in elements else None
    toc_idx = elements.index("TOC") if "TOC" in elements else None

    valid_ids = [
        pid for pid, p in lfg_params.items()
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
        rows=1, cols=2,
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
        wc_in    = np.zeros(len(time_items))
        toc_in   = np.zeros(len(time_items))

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
            fig_widget.add_trace(go.Scatter(
                x=d["time"], y=d["ch4_ipcc"],
                name="IPCC mode (DOC_j)",
                line=dict(color=colors["ipcc"], width=2),
                mode="lines",
                hovertemplate="IPCC<br>Year: %{x}<br>%{y:.1f} Mg CH4<extra></extra>",
            ), row=1, col=1)

            if d["toc_defined"] and d["ch4_mfa"] is not None:
                fig_widget.add_trace(go.Scatter(
                    x=d["time"], y=d["ch4_mfa"],
                    name="MFA/TOC mode",
                    line=dict(color=colors["mfa"], width=2, dash="dash"),
                    mode="lines",
                    hovertemplate="MFA/TOC<br>Year: %{x}<br>%{y:.1f} Mg CH4<extra></extra>",
                ), row=1, col=1)
            else:
                # Show IPCC-implied TOC as a dashed guidance line (in CH4-equivalent)
                # using mean DOCf and site params for conversion
                docf = float(params.get("DOCf", 0.5))
                F_CH4 = float(params.get("F_CH4", 0.5))
                MCF   = float(params.get("MCF", 1.0))
                OX    = float(params.get("OX", 0.1))
                phi   = float(params.get("phi", 1.0))
                # Rough single-step conversion: implied TOC × DOCf × gas factors × 16/12
                implied_ch4 = (
                    d["ipcc_implied_toc"] * docf * F_CH4 * MCF * (1 - OX) * phi * (16 / 12)
                )
                fig_widget.add_trace(go.Scatter(
                    x=d["time"], y=implied_ch4,
                    name="IPCC-implied TOC (calibration target)",
                    line=dict(color=colors["implied"], width=1.5, dash="dot"),
                    mode="lines",
                    hovertemplate="Implied<br>Year: %{x}<br>%{y:.1f} Mg CH4<extra></extra>",
                ), row=1, col=1)

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

            fig_widget.add_trace(go.Bar(
                x=bar_labels, y=bar_values,
                marker_color=bar_colors,
                name="Carbon input [Mg C/yr avg]",
                hovertemplate="%{x}<br>%{y:.1f} Mg C/yr<extra></extra>",
                showlegend=False,
            ), row=1, col=2)

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
                    text=(f"IPCC vs MFA Carbon Accounting — Process {process_id}"
                          f"<br><sup>{note}</sup>"),
                    font=dict(size=14),
                ),
                xaxis_title="Year",
                yaxis_title="CH4 [Mg CH4/yr]",
                yaxis2_title="Avg. Carbon Input [Mg C/yr]",
                legend=dict(orientation="h", yanchor="bottom", y=1.08,
                            xanchor="left", x=0),
                height=480,
                template="plotly_white",
            )

    process_dropdown.observe(lambda _: update_plot(process_dropdown.value), "value")
    display(process_dropdown)
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
        "engine", "lfg_model.py",
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
        pid for pid, p in lfg_params.items()
        if p.get("fractions") and p.get("outflow_ch4_id")
    ]
    if not valid_ids:
        print("No fully configured LFG processes found (missing fractions or outflow IDs).")
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
        "#E64B35", "#4DBBD5", "#00A087", "#3C5488",
        "#F39B7F", "#8491B4", "#91D1C2", "#DC0000",
        "#7E6148", "#B09C85",
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

        results = _calculate_lfg_series(waste_in, wc_in, params)

        # Per-fraction gas output (Mg C)
        F_CH4 = params.get("F_CH4", 0.5)
        MCF = params.get("MCF", 0.8)
        OX = params.get("OX", 0.1)
        fracs = params["fractions"]

        series = {}
        for frac in fracs:
            name = frac["name"]
            decay_j = np.zeros(len(time_items))
            stock_j = results["stocks"].get(name, np.zeros(len(time_items)))
            # Reconstruct decay from stock: decay_j[t] = stock_j[t-1] * (1-exp(-k))
            # Re-run single fraction to get exact decay (avoids re-implementing)
            single_params = {
                "fractions": [frac],
                "MCF": MCF, "DOCf": params.get("DOCf", 0.5),
                "F_CH4": F_CH4, "OX": OX,
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
                fig.add_trace(go.Scatter(
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
                ))

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
                fig, "lfg_fraction_breakdown",
                formats=["png", "svg"], quality="publication", size="large", timestamp=False,
            )
            print(f"Exported: {', '.join(paths)}")
        except Exception as e:
            print(f"Export failed: {e}")

    export_button.on_click(lambda b: export_plot())

    def on_change(_):
        update_plot(process_dropdown.value, gas_dropdown.value, cumulative_checkbox.value)

    process_dropdown.observe(on_change, "value")
    gas_dropdown.observe(on_change, "value")
    cumulative_checkbox.observe(on_change, "value")

    controls = HBox(
        [
            VBox([process_dropdown, gas_dropdown, cumulative_checkbox],
                 layout=Layout(width="320px")),
            VBox([export_button], layout=Layout(width="150px")),
        ],
        layout=Layout(justify_content="space-between"),
    )
    display(controls)
    display(fig)
    update_plot(process_ids[0], "ch4", False)
