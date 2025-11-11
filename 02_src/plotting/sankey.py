# -*- coding: utf-8 -*-
"""
Simplified Sankey Diagram Plotting Module for BioDYM.

Pure automatic positioning using Plotly's built-in layout engine.
For manual positioning control, use enhanced_sankey.py instead.

Key features:
- Interactive single-element Sankey diagrams with year/process/flow filtering
- Element-agnostic coloring (works with any element set)
- Multi-element vertical stacked visualizations
- Automatic node positioning via Plotly's 'snap' arrangement
- Publication-quality styling

Author: BioDYM Development Team
Date: 2025-11-10 (Clean - Automatic Only)
"""

import plotly.graph_objects as go
from ipywidgets import (
    FloatSlider,
    IntSlider,
    HBox,
    VBox,
    HTML,
    Layout,
    Dropdown,
    SelectMultiple,
    interactive,
)
from IPython.display import display
from typing import Optional

from .publication_style_simplified import (
    get_publication_layout,
    get_process_color,
    detect_biodym_process_type,
    get_stock_color,
    BIOYM_COLORS,
    FONT_FAMILY,
    FONT_SIZE,
)
from . import sankey_config
from .dynamic_colors import ElementColorManager


def _prepare_sankey_data(
    filtered_processes,
    flows_data,
    mfa_system_results,
    dsm_params,
    fomp_params,
    node_pad,
    node_scale_factor,
):
    """Prepare node and link data for Plotly Sankey.

    Uses Plotly's automatic positioning exclusively - no manual overrides.

    Parameters
    ----------
    filtered_processes : list of odym.Process
        Processes to display
    flows_data : list of tuples
        List of (flow_obj, value) tuples for the current year/element
    mfa_system_results : odym.MFAsystem
        MFA system results
    dsm_params : dict or None
        DSM parameters
    fomp_params : dict or None
        FOMP parameters
    node_pad : int
        Padding between nodes in pixels
    node_scale_factor : float
        Scale factor for node sizes

    Returns
    -------
    dict, dict
        Node data dict and link data dict for go.Sankey
    """
    # Build process ID to index mapping
    process_id_map = {p.ID: i for i, p in enumerate(filtered_processes)}

    # Prepare node labels
    node_labels = [p.Name for p in filtered_processes]

    # Determine node colors based on process type
    node_colors = []
    for p in filtered_processes:
        has_stocks = f"S_{p.ID}" in mfa_system_results.StockDict
        is_dsm = dsm_params and p.ID in dsm_params
        is_fomp = fomp_params and p.ID in fomp_params

        if is_dsm or is_fomp:
            process_type = detect_biodym_process_type(
                p.ID, dsm_params=dsm_params, fomp_params=fomp_params
            )
            node_colors.append(get_process_color(process_type))
        elif has_stocks:
            node_colors.append(get_stock_color())
        else:
            node_colors.append(get_process_color("regular"))

    # Build node dict - Plotly handles ALL positioning automatically
    node_dict = {
        "label": node_labels,
        "color": node_colors,
        "pad": node_pad,
        "thickness": 20 * node_scale_factor,
        "line": {"color": "black", "width": 0.5},
    }

    # Prepare link data
    if not flows_data:
        return node_dict, {"source": [], "target": [], "value": []}

    link_sources = []
    link_targets = []
    link_values = []
    link_customdata = []

    for flow, value in flows_data:
        if flow.P_Start in process_id_map and flow.P_End in process_id_map:
            link_sources.append(process_id_map[flow.P_Start])
            link_targets.append(process_id_map[flow.P_End])
            link_values.append(value)
            link_customdata.append(getattr(flow, "DescriptiveName", flow.Name))

    link_dict = {
        "source": link_sources,
        "target": link_targets,
        "value": link_values,
        "customdata": link_customdata,
        "hovertemplate": "Flow: %{customdata}<br />Source: %{source.label}<br />Target: %{target.label}<br />Value: %{value}<extra></extra>",
    }

    return node_dict, link_dict


def _create_sankey_widgets(
    all_process_names, all_flow_names, time_items, element_items, max_flow_value
):
    """Create UI widgets for interactive Sankey diagram."""
    year_slider = IntSlider(
        min=time_items[0],
        max=time_items[-1],
        step=1,
        value=time_items[0],
        description="Year:",
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

    process_selector = SelectMultiple(
        options=all_process_names,
        value=tuple(all_process_names),
        description="Processes:",
        style={"description_width": "100px"},
        layout=Layout(width="400px", height="120px"),
    )

    flow_selector = SelectMultiple(
        options=all_flow_names,
        value=tuple(all_flow_names),
        description="Flows:",
        style={"description_width": "100px"},
        layout=Layout(width="400px", height="120px"),
    )

    threshold_slider = FloatSlider(
        min=0,
        max=max_flow_value,
        step=max_flow_value / 100 if max_flow_value > 0 else 0.01,
        value=0,
        description="Min Flow:",
        continuous_update=False,
        readout_format=".2f",
        style={"description_width": "80px"},
        layout=Layout(width="400px"),
    )

    return (
        year_slider,
        element_dropdown,
        process_selector,
        flow_selector,
        threshold_slider,
    )


def _create_sankey_legend(element_items, color_manager):
    """Create HTML legend for Sankey diagram."""
    flow_legend_items = []
    for element in element_items:
        element_color = color_manager.get_element_color(element.lower())
        flow_legend_items.append(f"""
                <div style="display: flex; align-items: center;">
                    <div style="width: 20px; height: 20px; background-color: {element_color}; margin-right: 5px;"></div>
                    <span>{element.upper()}</span>
                </div>""")

    flow_legend_html = "\n".join(flow_legend_items)

    legend_html = f"""
    <div style="margin: 10px; padding: 10px; border: 1px solid #ccc; border-radius: 5px; background-color: #f9f9f9;">
        <h4 style="margin: 0 0 10px 0;">Legend</h4>
        <div style="margin-bottom: 10px;">
            <strong>Processes / Stocks:</strong><br>
            <div style="display: flex; flex-wrap: wrap; gap: 15px; margin-top: 5px;">
                <div style="display: flex; align-items: center;">
                    <div style="width: 20px; height: 20px; background-color: {get_process_color("regular")}; margin-right: 5px;"></div>
                    <span>Regular processes</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="width: 20px; height: 20px; background-color: {get_stock_color()}; margin-right: 5px;"></div>
                    <span>Stocks</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="width: 20px; height: 20px; background-color: {get_process_color("dsm")}; margin-right: 5px;"></div>
                    <span>DSM Process</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="width: 20px; height: 20px; background-color: {get_process_color("fomp")}; margin-right: 5px;"></div>
                    <span>FOMP Process</span>
                </div>
            </div>
        </div>
        <div>
            <strong>Flows:</strong><br>
            <div style="display: flex; flex-wrap: wrap; gap: 15px; margin-top: 5px;">
                {flow_legend_html}
            </div>
        </div>
    </div>
    """
    return HTML(value=legend_html)


def plot_interactive_sankey(
    mfa_system_results,
    dsm_params=None,
    fomp_params=None,
    color_manager: Optional[ElementColorManager] = None,
    width=sankey_config.WINDOW_WIDTH,
    height=sankey_config.WINDOW_HEIGHT,
    node_pad=sankey_config.NODE_SPACING,
    node_scale_factor=sankey_config.NODE_SCALE_FACTOR,
):
    """Display an interactive Sankey diagram for MFA results.

    Uses Plotly's automatic node positioning exclusively.
    For manual positioning control, use enhanced_sankey module instead.

    Parameters
    ----------
    mfa_system_results : odym.MFAsystem
        Solved MFA system with calculated data
    dsm_params : dict, optional
        DSM parameters for process coloring
    fomp_params : dict, optional
        FOMP parameters for process coloring
    color_manager : ElementColorManager, optional
        Color manager for elements (auto-created if None)
    width : int, optional
        Diagram width in pixels
    height : int, optional
        Diagram height in pixels
    node_pad : int, optional
        Padding between nodes in pixels
    node_scale_factor : float, optional
        Scale factor for node sizes

    Examples
    --------
    >>> plot_interactive_sankey(mfa_results_baseline)

    >>> plot_interactive_sankey(
    ...     mfa_results_baseline,
    ...     width=4000,
    ...     height=1500,
    ...     node_pad=30
    ... )
    """
    # Extract data from MFA system
    all_process_names = [p.Name for p in mfa_system_results.ProcessList]
    all_flow_names = [f.Name for f in mfa_system_results.FlowDict.values()]
    all_flows = list(mfa_system_results.FlowDict.values())
    time_items = mfa_system_results.IndexTable.Classification["Time"].Items
    element_items = mfa_system_results.Elements

    # Create color manager if needed
    if color_manager is None:
        color_manager = ElementColorManager([e.lower() for e in element_items])

    max_flow_value = (
        max(f.Values.max() for f in all_flows if f.Values is not None)
        if all_flows
        else 1
    )

    # Create figure widget - no arrangement constraint for maximum flexibility
    fig = go.FigureWidget(data=[go.Sankey(node={}, link={})])

    def update_sankey(year, element, processes_to_show, flows_to_show, min_flow_value):
        """Update callback for widget changes."""
        if not processes_to_show or not flows_to_show:
            with fig.batch_update():
                fig.data[0].node.label = []
            return

        # Filter processes
        filtered_processes = [
            p for p in mfa_system_results.ProcessList if p.Name in processes_to_show
        ]
        process_ids = [p.ID for p in filtered_processes]
        process_id_set = set(process_ids)

        # Get year and element indices
        year_index = time_items.index(year)
        element_index = element_items.index(element)

        # Filter flows
        flows_data = []
        for flow in all_flows:
            if (
                flow.Name in flows_to_show
                and flow.P_Start in process_id_set
                and flow.P_End in process_id_set
            ):
                flow_value = flow.Values[year_index, element_index]
                if flow_value >= min_flow_value:
                    flows_data.append((flow, flow_value))

        # Prepare node and link data (Plotly handles all positioning)
        node_dict, link_dict = _prepare_sankey_data(
            filtered_processes,
            flows_data,
            mfa_system_results,
            dsm_params,
            fomp_params,
            node_pad,
            node_scale_factor,
        )

        # Set link colors based on element
        element_color = color_manager.get_element_color(element.lower())
        if link_dict["value"]:
            link_dict["color"] = [element_color] * len(link_dict["value"])

        # Update figure
        with fig.batch_update():
            fig.data[0].node = node_dict
            fig.data[0].link = link_dict

            # Update layout
            title_text = f"BioDYM Material Flow Analysis - {element.title()} ({year})"
            layout_config = {
                "title": {
                    "text": title_text,
                    "x": 0.5,
                    "xanchor": "center",
                    "font": {
                        "family": FONT_FAMILY,
                        "size": FONT_SIZE["title"],
                        "color": BIOYM_COLORS["dark"],
                    },
                },
                "width": width,
                "height": height,
                "paper_bgcolor": sankey_config.BACKGROUND_COLOR,
                "plot_bgcolor": sankey_config.GRID_COLOR,
                "margin": dict(
                    l=width * sankey_config.PADDING_FACTOR,
                    r=width * sankey_config.PADDING_FACTOR,
                    t=height * sankey_config.PADDING_FACTOR,
                    b=height * sankey_config.PADDING_FACTOR,
                ),
            }
            fig.update_layout(**layout_config)

    # Create widgets
    year_slider, element_dropdown, process_selector, flow_selector, threshold_slider = (
        _create_sankey_widgets(
            all_process_names, all_flow_names, time_items, element_items, max_flow_value
        )
    )
    legend_widget = _create_sankey_legend(element_items, color_manager)

    # Layout widgets (matches enhanced_sankey structure)
    ui = VBox(
        [
            HBox([year_slider, element_dropdown]),
            HBox([process_selector, flow_selector]),
            HBox([threshold_slider]),
            legend_widget,
        ]
    )

    # Connect widgets
    out = interactive(
        update_sankey,
        year=year_slider,
        element=element_dropdown,
        processes_to_show=process_selector,
        flows_to_show=flow_selector,
        min_flow_value=threshold_slider,
    )

    # Display (matches enhanced_sankey: VBox with controls and figure)
    display(VBox([ui, fig]))
    out.update()


def plot_element_multiplot_sankey(
    mfa_system_results,
    dsm_params=None,
    fomp_params=None,
    elements_to_plot=None,
    subplot_height=sankey_config.WINDOW_HEIGHT,
    subplot_width=sankey_config.WINDOW_WIDTH,
    node_pad=sankey_config.NODE_SPACING,
    node_scale_factor=sankey_config.NODE_SCALE_FACTOR,
    color_manager: Optional[ElementColorManager] = None,
):
    """Display multiple Sankey diagrams stacked vertically (one per element).

    All subplots share time slider, process selector, and min flow filter.
    Uses automatic positioning exclusively.

    Parameters
    ----------
    mfa_system_results : odym.MFAsystem
        Solved MFA system
    dsm_params : dict, optional
        DSM parameters
    fomp_params : dict, optional
        FOMP parameters
    elements_to_plot : list of str, optional
        Elements to plot (default: all)
    subplot_height : int, optional
        Height per subplot in pixels
    subplot_width : int, optional
        Width per subplot in pixels
    node_pad : int, optional
        Padding between nodes in pixels
    node_scale_factor : float, optional
        Scale factor for node sizes
    color_manager : ElementColorManager, optional
        Color manager (auto-created if None)
    """
    # Extract data
    all_process_names = [p.Name for p in mfa_system_results.ProcessList]
    all_flow_names = [f.Name for f in mfa_system_results.FlowDict.values()]
    all_flows = list(mfa_system_results.FlowDict.values())
    time_items = mfa_system_results.IndexTable.Classification["Time"].Items
    element_items = mfa_system_results.Elements

    # Create color manager
    if color_manager is None:
        color_manager = ElementColorManager([e.lower() for e in element_items])

    # Determine elements to plot
    if elements_to_plot is None:
        elements_to_plot = element_items
    else:
        elements_to_plot = [e for e in elements_to_plot if e in element_items]

    max_flow_value = (
        max(f.Values.max() for f in all_flows if f.Values is not None)
        if all_flows
        else 1
    )

    # Create one figure per element
    figures = []
    for elem in elements_to_plot:
        fig = go.FigureWidget(data=[go.Sankey(node={}, link={})])
        fig.update_layout(
            height=subplot_height,
            width=subplot_width,
            title_text=f"{elem.upper()}",
            font_size=16,
            margin=dict(
                l=subplot_width * sankey_config.PADDING_FACTOR,
                r=subplot_width * sankey_config.PADDING_FACTOR,
                t=subplot_height * sankey_config.PADDING_FACTOR,
                b=subplot_height * sankey_config.PADDING_FACTOR,
            ),
            paper_bgcolor=sankey_config.BACKGROUND_COLOR,
            plot_bgcolor=sankey_config.GRID_COLOR,
        )
        figures.append(fig)

    def update_all_sankeys(year, processes_to_show, flows_to_show, min_flow_value):
        """Update all element subplots."""
        if not processes_to_show or not flows_to_show:
            for fig in figures:
                with fig.batch_update():
                    fig.data[0].node.label = []
            return

        # Filter processes
        filtered_processes = [
            p for p in mfa_system_results.ProcessList if p.Name in processes_to_show
        ]
        process_ids = [p.ID for p in filtered_processes]
        process_id_set = set(process_ids)
        year_index = time_items.index(year)

        # Update each figure
        for fig_idx, element in enumerate(elements_to_plot):
            element_index = element_items.index(element)

            # Filter flows for this element
            flows_data = []
            for flow in all_flows:
                if (
                    flow.Name in flows_to_show
                    and flow.P_Start in process_id_set
                    and flow.P_End in process_id_set
                ):
                    flow_value = flow.Values[year_index, element_index]
                    if flow_value >= min_flow_value:
                        flows_data.append((flow, flow_value))

            # Prepare data (Plotly handles all positioning)
            node_dict, link_dict = _prepare_sankey_data(
                filtered_processes,
                flows_data,
                mfa_system_results,
                dsm_params,
                fomp_params,
                node_pad,
                node_scale_factor,
            )

            # Set link colors
            element_color = color_manager.get_element_color(element.lower())
            if link_dict["value"]:
                link_dict["color"] = [element_color] * len(link_dict["value"])

            # Update figure
            with figures[fig_idx].batch_update():
                figures[fig_idx].data[0].node = node_dict
                figures[fig_idx].data[0].link = link_dict

    # Create widgets (no element dropdown for multiplot)
    year_slider, _, process_selector, flow_selector, threshold_slider = (
        _create_sankey_widgets(
            all_process_names, all_flow_names, time_items, element_items, max_flow_value
        )
    )

    ui = VBox(
        [HBox([year_slider, threshold_slider]), HBox([process_selector, flow_selector])]
    )

    # Connect widgets
    out = interactive(
        update_all_sankeys,
        year=year_slider,
        processes_to_show=process_selector,
        flows_to_show=flow_selector,
        min_flow_value=threshold_slider,
    )

    # Display
    display(ui)
    for fig in figures:
        display(fig)

    # Initial draw
    update_all_sankeys(
        year_slider.value,
        process_selector.value,
        flow_selector.value,
        threshold_slider.value,
    )
