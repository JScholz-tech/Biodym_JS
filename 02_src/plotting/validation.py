# -*- coding: utf-8 -*-
"""
Validation Plotting Module for BioDYM.

This module provides publication-quality validation visualizations including:
- Mass balance error checking (interactive and static)
- Element-agnostic coloring (works with any element set)
- Standardized styling and export functionality

Author: BioDYM Development Team
Date: 2025-11-04
"""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ipywidgets import IntSlider, Dropdown, Button, HBox, VBox, Layout
from IPython.display import display
from typing import Optional

from .themes import (
    apply_theme,
    get_publication_layout,
    get_mass_display,
    y_label,
    BIOYM_COLORS,
)
from .dynamic_colors import ElementColorManager
from .export_publication import export_figure


def plot_optimized_mass_balance_error(
    mfa_system_results,
    color_manager: Optional[ElementColorManager] = None,
    enable_export: bool = True,
    dsm_params=None,
    fomp_params=None,
    lfg_params=None,
):
    """Creates an interactive plot of mass balance errors for each process.

    This function visualizes the mass balance error (inflow - outflow - dS)
    for each process in the MFA system for a selected year and element.
    It is optimized for performance by pre-calculating flow sums and supports
    element-agnostic coloring.

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
    dsm_params : dict, optional
        DSM process parameters dict (keyed by process ID). When provided,
        DSM processes are labelled [DSM] in the chart. Defaults to None.
    fomp_params : dict, optional
        FOMP process parameters dict (keyed by process ID). When provided,
        FOMP processes are labelled [FOMP] in the chart. Defaults to None.
    lfg_params : dict, optional
        LFG process parameters dict (keyed by process ID). When provided,
        LFG processes are labelled [LFG] in the chart. Defaults to None.

    Notes
    -----
    The plot is interactive, allowing the user to select the year and the
    element to display. Errors are shown as bar charts, with a horizontal
    line at zero for reference. The plot adheres to publication styling
    standards and works with any element configuration.

    Examples
    --------
    >>> # Basic usage
    >>> plot_optimized_mass_balance_error(mfa_results)

    >>> # With dynamic process labels
    >>> plot_optimized_mass_balance_error(
    ...     mfa_results, dsm_params=dsm_params, fomp_params=fomp_params)
    """
    time_items = mfa_system_results.IndexTable.Classification["Time"].Items
    element_items = [e.lower() for e in mfa_system_results.Elements]

    # Build dynamic process type map for labelling
    dynamic_labels = {}
    if dsm_params:
        for pid in dsm_params:
            dynamic_labels[pid] = "DSM"
    if fomp_params:
        for pid in fomp_params:
            dynamic_labels[pid] = "FOMP"
    if lfg_params:
        for pid in lfg_params:
            dynamic_labels[pid] = "LFG"

    # Create color manager if not provided
    if color_manager is None:
        color_manager = ElementColorManager(element_items)

    fig = go.FigureWidget()

    def update_plot(year, element):
        year_index = time_items.index(year)
        element_index = element_items.index(element.lower())
        _sc, _unit = get_mass_display()

        # Pre-calculate flow sums for better performance
        inflow_sums = {}
        outflow_sums = {}

        for flow_id, flow in mfa_system_results.FlowDict.items():
            flow_value = flow.Values[year_index, element_index]

            # Inflows
            if flow.P_End not in inflow_sums:
                inflow_sums[flow.P_End] = 0
            inflow_sums[flow.P_End] += flow_value

            # Outflows
            if flow.P_Start not in outflow_sums:
                outflow_sums[flow.P_Start] = 0
            outflow_sums[flow.P_Start] += flow_value

        errors = []
        process_labels = []
        bar_colors = []
        element_color = color_manager.get_element_color(element.lower())
        dynamic_color = BIOYM_COLORS["accent"]  # Orange for dynamic processes

        for p in mfa_system_results.ProcessList:
            in_val = inflow_sums.get(p.ID, 0)
            out_val = outflow_sums.get(p.ID, 0)

            ds_val = mfa_system_results.StockDict.get(f"dS_{p.ID}", None)
            ds_sum = (
                ds_val.Values[year_index, element_index] if ds_val is not None else 0
            )

            # Detect Input/Output processes (system boundaries)
            # Input process: no inflows, has outflows (material source)
            # Output process: has inflows, no outflows (material sink)
            is_input_process = (in_val == 0) and (out_val > 0) and (ds_sum == 0)
            is_output_process = (in_val > 0) and (out_val == 0) and (ds_sum == 0)

            # Calculate error
            error = in_val - out_val - ds_sum

            # Build label: boundary processes get *, dynamic processes get [type]
            dyn_type = dynamic_labels.get(p.ID, "")
            if is_input_process or is_output_process:
                errors.append(0)
                process_labels.append(f"{p.Name}*")
                bar_colors.append(BIOYM_COLORS["neutral"])
            elif dyn_type:
                errors.append(error)
                process_labels.append(f"{p.Name} [{dyn_type}]")
                bar_colors.append(dynamic_color)
            else:
                errors.append(error)
                process_labels.append(p.Name)
                bar_colors.append(element_color)

        scaled_errors = [e * _sc for e in errors]

        with fig.batch_update():
            fig.data = []  # Clear previous data
            fig.add_trace(
                go.Bar(
                    x=process_labels,
                    y=scaled_errors,
                    marker_color=bar_colors,
                    marker_line=dict(color=BIOYM_COLORS["dark"], width=1),
                    hovertemplate=f"<b>%{{x}}</b><br>Error: %{{y:.2e}} {_unit}<extra></extra>",
                )
            )

            # Apply publication layout with proper formatting
            layout_config = get_publication_layout(
                size="large",
                show_grid=True,
                scientific_y=True,
                custom_title=f"Mass Balance Error: {element.upper()} ({year})",
                x_title="Process",
                y_title=y_label(element.upper()),
            )
            apply_theme(layout_config)
            layout_config["xaxis"].pop("range", None)  # categorical axis, not time-series
            layout_config["xaxis"]["tickangle"] = -45
            layout_config["shapes"] = [
                dict(
                    type="line",
                    y0=0,
                    y1=0,
                    x0=-0.5,
                    x1=len(process_labels) - 0.5,
                    line=dict(color=BIOYM_COLORS["dark"], width=2, dash="dash"),
                )
            ]
            _footer = "* system boundaries — excluded from error calculation"
            if dynamic_labels:
                _footer += "  |  [DSM]/[FOMP]/[LFG] — dynamic stock processes"
            layout_config["annotations"] = [
                dict(
                    text=_footer,
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=-0.15,
                    showarrow=False,
                    font=dict(size=14, color=BIOYM_COLORS["neutral"]),
                    xanchor="center",
                )
            ]
            fig.update_layout(layout_config)

    def export_current_plot(btn):
        """Export current plot configuration."""
        year = year_slider.value
        element = element_dropdown.value
        update_plot(year, element)  # Ensure plot is current

        filename = f"mass_balance_error_{element}_{year}"
        try:
            paths = export_figure(
                fig,
                filename,
                formats=["png", "pdf"],
                quality="publication",
                size="large",
            )
            print(f"✅ Exported: {', '.join(paths)}")
        except Exception as e:
            print(f"❌ Export failed: {e}")

    # Create widgets
    year_slider = IntSlider(
        min=time_items[0],
        max=time_items[-1],
        step=1,
        value=time_items[0],
        description="Year:",
        style={"description_width": "60px"},
        layout=Layout(width="400px"),
    )
    element_dropdown = Dropdown(
        options=element_items,
        value=element_items[0],
        description="Element:",
        style={"description_width": "60px"},
        layout=Layout(width="300px"),
    )

    # Create control panel
    controls = [year_slider, element_dropdown]

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
        update_plot, {"year": year_slider, "element": element_dropdown}
    )

    # Display
    display(control_box)
    display(fig)

    # Initial plot
    update_plot(year_slider.value, element_dropdown.value)


def plot_total_mass_balance_error(
    mfa_system_results,
    color_manager: Optional[ElementColorManager] = None,
    enable_export: bool = True,
    export_filename: str = "mass_balance_total",
    dsm_params=None,
    fomp_params=None,
    lfg_params=None,
):
    """Creates a static bar chart showing the sum of absolute mass balance errors.

    This function calculates and visualizes the total absolute mass balance
    error for each process and element, aggregated over all years. It manually
    calculates the balance to ensure correctness, bypassing potential issues
    with underlying ODYM functions. Supports element-agnostic coloring and
    publication-quality export.

    Parameters
    ----------
    mfa_system_results : odym.MFAsystem
        The solved MFA system object, containing the results of the MFA
        calculation, including all flows and stocks over the simulation period.
    color_manager : ElementColorManager, optional
        Dynamic color manager for element colors. If None, creates one from
        mfa_system_results.Elements. Defaults to None.
    enable_export : bool, optional
        If True, automatically exports the figure after display.
        Defaults to True.
    export_filename : str, optional
        Base filename for exported figure (without extension).
        Defaults to "mass_balance_total".
    dsm_params : dict, optional
        DSM process parameters dict (keyed by process ID). When provided,
        DSM processes are labelled [DSM] in the chart. Defaults to None.
    fomp_params : dict, optional
        FOMP process parameters dict (keyed by process ID). When provided,
        FOMP processes are labelled [FOMP] in the chart. Defaults to None.
    lfg_params : dict, optional
        LFG process parameters dict (keyed by process ID). When provided,
        LFG processes are labelled [LFG] in the chart. Defaults to None.

    Returns
    -------
    go.Figure
        Plotly figure object (can be used for further customization or export)

    Notes
    -----
    The plot is static and displays the sum of absolute errors for each element
    as stacked bars per process. It uses publication styling standards and
    element-specific colors for clarity. Works with any element configuration.

    Examples
    --------
    >>> # Basic usage
    >>> fig = plot_total_mass_balance_error(mfa_results)

    >>> # With dynamic process labels
    >>> fig = plot_total_mass_balance_error(
    ...     mfa_results, dsm_params=dsm_params, fomp_params=fomp_params)
    """
    process_names = [p.Name for p in mfa_system_results.ProcessList]
    element_items = [e.lower() for e in mfa_system_results.Elements]
    num_processes = len(process_names)
    num_elements = len(element_items)
    num_years = len(mfa_system_results.IndexTable.Classification["Time"].Items)

    # Build dynamic process type map for labelling
    dynamic_labels = {}
    if dsm_params:
        for pid in dsm_params:
            dynamic_labels[pid] = "DSM"
    if fomp_params:
        for pid in fomp_params:
            dynamic_labels[pid] = "FOMP"
    if lfg_params:
        for pid in lfg_params:
            dynamic_labels[pid] = "LFG"

    # Create color manager if not provided
    if color_manager is None:
        color_manager = ElementColorManager(element_items)

    # Manually calculate the balance matrix to ensure correctness
    total_inflows = np.zeros((num_years, num_processes, num_elements))
    total_outflows = np.zeros((num_years, num_processes, num_elements))

    for flow in mfa_system_results.FlowDict.values():
        if flow.P_Start < num_processes and flow.P_End < num_processes:
            total_inflows[:, flow.P_End, :] += flow.Values
            total_outflows[:, flow.P_Start, :] += flow.Values

    total_ds = np.zeros((num_years, num_processes, num_elements))
    for p_idx, p in enumerate(mfa_system_results.ProcessList):
        ds_stock = mfa_system_results.StockDict.get(f"dS_{p.ID}")
        if ds_stock is not None:
            total_ds[:, p_idx, :] = ds_stock.Values

    manual_balance_matrix = total_inflows - total_outflows - total_ds

    # Calculate total errors per element and process
    # Also detect Input/Output processes to exclude them
    total_errors = {element: [] for element in element_items}
    process_labels = []

    for p_idx, p in enumerate(mfa_system_results.ProcessList):
        # Check if this is an Input or Output process (system boundary)
        # Average over time and elements to detect pattern
        avg_inflow = np.mean(total_inflows[:, p_idx, :])
        avg_outflow = np.mean(total_outflows[:, p_idx, :])
        avg_ds = np.mean(total_ds[:, p_idx, :])

        is_input_process = (
            (avg_inflow == 0) and (avg_outflow > 0) and (abs(avg_ds) < 1e-10)
        )
        is_output_process = (
            (avg_inflow > 0) and (avg_outflow == 0) and (abs(avg_ds) < 1e-10)
        )

        # Add label: boundary processes get *, dynamic processes get [type]
        dyn_type = dynamic_labels.get(p.ID, "")
        if is_input_process or is_output_process:
            process_labels.append(f"{p.Name}*")
        elif dyn_type:
            process_labels.append(f"{p.Name} [{dyn_type}]")
        else:
            process_labels.append(p.Name)

        for e_idx, element in enumerate(element_items):
            # Exclude Input/Output processes from error calculation
            if is_input_process or is_output_process:
                total_error_for_element = 0  # Set to zero for system boundaries
            else:
                total_error_for_element = np.sum(
                    np.abs(manual_balance_matrix[:, p_idx, e_idx])
                )
            total_errors[element].append(total_error_for_element)

    _sc, _unit = get_mass_display()
    fig = go.Figure()

    # Use dynamic element colors for consistency
    for element, errors in total_errors.items():
        element_color = color_manager.get_element_color(element)

        fig.add_trace(
            go.Bar(
                name=element.upper(),
                x=process_labels,
                y=[e * _sc for e in errors],
                marker_color=element_color,
                marker_line=dict(color=BIOYM_COLORS["dark"], width=1),
                hovertemplate=f"<b>%{{x}}</b><br>{element.upper()}: %{{y:.2e}} {_unit}<extra></extra>",
            )
        )

    # Apply publication layout with proper formatting
    layout_config = get_publication_layout(
        size="large",
        show_grid=True,
        scientific_y=True,
        custom_title="Total Absolute Mass Balance Error (All Years)",
        x_title="Process",
        y_title=y_label("Material"),
    )
    apply_theme(layout_config)
    layout_config["xaxis"].pop("range", None)  # categorical axis, not time-series
    layout_config["barmode"] = "stack"
    layout_config["legend"] = {
        "title": {"text": "Element", "font": {"size": 16}},
        "font": {"size": 14},
        "bgcolor": "rgba(255,255,255,0.8)",
        "bordercolor": BIOYM_COLORS["neutral"],
        "borderwidth": 1,
        "orientation": "v",
        "yanchor": "top",
        "y": 1,
        "xanchor": "right",
        "x": 1,
    }
    layout_config["xaxis"]["tickangle"] = -60
    layout_config["margin"] = dict(l=100, r=50, t=100, b=200)
    _footer = "* system boundaries — excluded from error calculation"
    if dynamic_labels:
        _footer += "  |  [DSM]/[FOMP]/[LFG] — dynamic stock processes"
    layout_config["annotations"] = [
        dict(
            text=_footer,
            xref="paper",
            yref="paper",
            x=0.5,
            y=-0.35,
            showarrow=False,
            font=dict(size=14, color=BIOYM_COLORS["neutral"]),
            xanchor="center",
        )
    ]

    fig.update_layout(layout_config)

    # Show the figure
    fig.show()

    # Export if enabled
    if enable_export:
        try:
            paths = export_figure(
                fig,
                export_filename,
                formats=["png", "pdf"],
                quality="publication",
                size="large",
                timestamp=False,
            )
            print(f"\n✅ Figure exported: {', '.join(paths)}")
        except Exception as e:
            print(f"\n⚠️ Export failed: {e}")

    return fig


def plot_dynamic_process_balance(
    mfa_system_results,
    dsm_params=None,
    fomp_params=None,
    lfg_params=None,
    color_manager: Optional[ElementColorManager] = None,
    enable_export: bool = True,
):
    """Time-series mass balance validation for dynamic stock processes (DSM/FOMP/LFG).

    Displays two panels per selected process and element:

    - **Top panel**: Inflow, ΔStock, and Outflow as line traces over time.
    - **Bottom panel**: Residual = Inflow − ΔStock − Outflow (should be ≈ 0 every year).

    A non-zero residual indicates a mass balance violation in the model, making
    regression detection easy. After the FOMP stock-doubling fix, all dynamic
    processes should show residuals at floating-point precision (< 1e-10).

    Parameters
    ----------
    mfa_system_results : odym.MFAsystem
        The solved MFA system object.
    dsm_params : dict, optional
        DSM process parameters dict (keyed by process ID). Defaults to None.
    fomp_params : dict, optional
        FOMP process parameters dict (keyed by process ID). Defaults to None.
    lfg_params : dict, optional
        LFG process parameters dict (keyed by process ID). Defaults to None.
    color_manager : ElementColorManager, optional
        Dynamic color manager for element colors. Defaults to None.
    enable_export : bool, optional
        If True, adds an export button. Defaults to True.

    Notes
    -----
    If no params dicts are provided the function will show all processes that
    have a StockDict entry, which may include regular MFA processes.
    Pass at least one params dict to restrict the dropdown to dynamic processes.
    """
    time_items = list(mfa_system_results.IndexTable.Classification["Time"].Items)
    element_items = mfa_system_results.Elements

    # Build process options: prefer known dynamic processes; fall back to all stocked
    process_options = {}
    type_map = {}
    if dsm_params:
        for pid in dsm_params:
            type_map[pid] = "DSM"
    if fomp_params:
        for pid in fomp_params:
            type_map[pid] = "FOMP"
    if lfg_params:
        for pid in lfg_params:
            type_map[pid] = "LFG"

    for p in mfa_system_results.ProcessList:
        if p.ID == 0:
            continue
        if type_map:
            if p.ID in type_map:
                label = f"{p.Name} [{type_map[p.ID]}]"
                process_options[label] = p.ID
        else:
            # Fallback: show all processes with a stock
            if f"S_{p.ID}" in mfa_system_results.StockDict:
                process_options[p.Name] = p.ID

    if not process_options:
        print("No dynamic processes found. Pass dsm_params, fomp_params, or lfg_params.")
        return

    if color_manager is None:
        color_manager = ElementColorManager([e.lower() for e in element_items])

    # Colours for the four traces
    _c_inflow  = BIOYM_COLORS["primary"]   # blue
    _c_ds      = BIOYM_COLORS["accent"]    # orange
    _c_outflow = BIOYM_COLORS["secondary"] # pink
    _c_resid   = BIOYM_COLORS["neutral"]   # grey

    fig = go.FigureWidget(
        make_subplots(
            rows=2, cols=1,
            row_heights=[0.7, 0.3],
            shared_xaxes=True,
            subplot_titles=("Inflow / ΔStock / Outflow", "Mass Balance Error (Inflow − ΔStock − Outflow)"),
            vertical_spacing=0.08,
        )
    )

    def update_plot(process_label, element):
        pid = process_options[process_label]
        elem_idx = element_items.index(element)
        _sc, _unit = get_mass_display()

        inflow_ts = np.zeros(len(time_items))
        outflow_ts = np.zeros(len(time_items))
        for f in mfa_system_results.FlowDict.values():
            if f.P_End == pid:
                inflow_ts += f.Values[:, elem_idx]
            if f.P_Start == pid:
                outflow_ts += f.Values[:, elem_idx]

        ds_obj = mfa_system_results.StockDict.get(f"dS_{pid}")
        ds_ts = ds_obj.Values[:, elem_idx] if ds_obj is not None else np.zeros(len(time_items))

        residual = inflow_ts - ds_ts - outflow_ts

        with fig.batch_update():
            fig.data = []
            # Top panel
            fig.add_trace(go.Scatter(
                x=time_items, y=inflow_ts * _sc,
                name="Inflow", mode="lines",
                line=dict(color=_c_inflow, width=2),
                hovertemplate=f"Inflow: %{{y:.4f}} {_unit}<extra></extra>",
            ), row=1, col=1)
            fig.add_trace(go.Scatter(
                x=time_items, y=ds_ts * _sc,
                name="ΔStock", mode="lines",
                line=dict(color=_c_ds, width=2, dash="dash"),
                hovertemplate=f"ΔStock: %{{y:.4f}} {_unit}<extra></extra>",
            ), row=1, col=1)
            fig.add_trace(go.Scatter(
                x=time_items, y=outflow_ts * _sc,
                name="Outflow", mode="lines",
                line=dict(color=_c_outflow, width=2, dash="dot"),
                hovertemplate=f"Outflow: %{{y:.4f}} {_unit}<extra></extra>",
            ), row=1, col=1)
            # Bottom panel — residual
            fig.add_trace(go.Scatter(
                x=time_items, y=residual * _sc,
                name="Mass Balance Error", mode="lines",
                line=dict(color=_c_resid, width=1.5),
                fill="tozeroy",
                fillcolor="rgba(108,117,125,0.15)",
                hovertemplate=f"Mass Balance Error: %{{y:.2e}} {_unit}<extra></extra>",
            ), row=2, col=1)

            layout_config = get_publication_layout(
                size="large",
                show_grid=True,
                scientific_y=False,
                custom_title=f"Dynamic Process Balance — {process_label} ({element.upper()})",
                x_title="Year",
                y_title=y_label(element.upper()),
            )
            apply_theme(layout_config)
            layout_config["xaxis2"] = {"title": "Year"}
            layout_config["yaxis2"] = {
                "title": f"Mass Balance Error ({_unit})",
                "tickformat": ",",
                "zeroline": True,
                "zerolinecolor": BIOYM_COLORS["dark"],
                "zerolinewidth": 2,
            }
            layout_config["showlegend"] = True
            fig.update_layout(**layout_config)

    # Widgets
    process_dropdown = Dropdown(
        options=list(process_options.keys()),
        value=list(process_options.keys())[0],
        description="Process:",
        style={"description_width": "70px"},
        layout=Layout(width="320px"),
    )
    element_dropdown = Dropdown(
        options=element_items,
        value=element_items[0],
        description="Element:",
        style={"description_width": "70px"},
        layout=Layout(width="200px"),
    )

    def _on_change(change):
        update_plot(process_dropdown.value, element_dropdown.value)

    process_dropdown.observe(_on_change, "value")
    element_dropdown.observe(_on_change, "value")

    controls = [process_dropdown, element_dropdown]

    if enable_export:
        export_btn = Button(
            description="Export PNG/SVG",
            button_style="success",
            icon="download",
            layout=Layout(width="160px"),
        )

        def _do_export(b):
            try:
                proc_safe = process_dropdown.value.replace(" ", "_").replace("[", "").replace("]", "")
                name = f"dynamic_process_balance_{proc_safe}_{element_dropdown.value}"
                paths = export_figure(fig, name, formats=["png", "svg"], quality="publication", size="large")
                print(f"✅ Exported: {', '.join(paths)}")
            except Exception as e:
                print(f"❌ Export failed: {e}")

        export_btn.on_click(_do_export)
        controls.append(export_btn)

    display(HBox(controls))
    display(fig)
    update_plot(process_dropdown.value, element_dropdown.value)
