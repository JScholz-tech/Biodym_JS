
# -*- coding: utf-8 -*-
"""
Sankey Diagram Plotting Module for BioDYM.

This module provides interactive Sankey diagram visualizations for Material Flow
Analysis (MFA) results, including:
- Interactive single-element Sankey diagrams with year/process/flow filtering
- Element-agnostic coloring (works with any element set)
- Multi-element vertical stacked visualizations
- Automatic node positioning using topological sorting
- Publication-quality styling and export

Author: BioDYM Development Team
Date: 2025-11-06
"""

import plotly.graph_objects as go
from ipywidgets import FloatSlider, IntSlider, Button, HBox, VBox, HTML, Layout, Dropdown, SelectMultiple
from IPython.display import display
import os
from datetime import datetime
import collections
from typing import Optional
from .publication_style_simplified import (
    get_publication_layout,
    get_process_color,
    detect_biodym_process_type,
    get_stock_color,
    BIOYM_COLORS,
    ELEMENT_COLORS,
    PROCESS_COLORS,
    FONT_FAMILY,
    FONT_SIZE
)
from .dynamic_colors import ElementColorManager


def _calculate_node_positions(processes, flows):
    """Calculates horizontal (x) positions for Sankey nodes using topological sort.

    This algorithm arranges nodes into layers to create a structured, left-to-right
    flow visualization. It can handle cycles in the graph by assigning all nodes
    within a cycle to the same layer.

    Parameters
    ----------
    processes : list of odym.Process
        The list of process objects to be included in the layout.
    flows : list of odym.Flow
        The list of flow objects connecting the processes.

    Returns
    -------
    dict
        A dictionary mapping each process ID to a normalized x-coordinate (0 to 1).
    """
    nodes = {p.ID for p in processes}
    if not nodes:
        return {}

    adj = {node: [] for node in nodes}
    in_degree = {node: 0 for node in nodes}

    for flow in flows:
        if flow.P_Start in nodes and flow.P_End in nodes:
            adj[flow.P_Start].append(flow.P_End)
            in_degree[flow.P_End] += 1

    # Kahn's algorithm for topological sorting
    queue = collections.deque([node for node in nodes if in_degree[node] == 0])
    layers = {node: 0 for node in nodes}
    max_layer = 0

    while queue:
        u = queue.popleft()
        for v in adj[u]:
            in_degree[v] -= 1
            # Assign layer based on the maximum layer of its predecessors
            layers[v] = max(layers.get(v, 0), layers[u] + 1)
            max_layer = max(max_layer, layers[v])
            if in_degree[v] == 0:
                queue.append(v)
    
    # Handle cycles: nodes left with non-zero in-degree are in cycles
    # Assign them to a layer just after their non-cyclic predecessors if possible
    # As a simple fix, we can place them in a layer beyond the max discovered layer
    remaining_nodes = [node for node in nodes if in_degree[node] > 0]
    if remaining_nodes:
        max_layer += 1
        for node in remaining_nodes:
            layers[node] = max_layer

    # Normalize positions to be between 0.1 and 0.9
    if max_layer == 0:
        return {node: 0.5 for node in nodes} # All nodes in one layer
    
    positions = {node: 0.1 + (layers[node] / max_layer) * 0.8 for node in nodes}
    return positions

def _create_sankey_widgets(all_process_names, time_items, element_items, max_flow_value):
    """Creates and returns all ipywidgets for the Sankey diagram UI.

    Parameters
    ----------
    all_process_names : list of str
        A list of all process names for the multi-select widget.
    time_items : list of int
        The list of years for the year slider.
    element_items : list of str
        The list of elements for the element dropdown.
    max_flow_value : float
        The maximum flow value in the dataset, used to set the slider range.

    Returns
    -------
    tuple
        A tuple of created ipywidgets: (year_slider, element_dropdown,
        process_selector, threshold_slider).
    """
    year_slider = IntSlider(
        min=time_items[0],
        max=time_items[-1],
        step=1,
        value=time_items[0],
        description="Year:",
        style={'description_width': '80px'},
        layout=Layout(width='400px')
    )
    
    element_dropdown = Dropdown(
        options=element_items, 
        value=element_items[0], 
        description="Element:",
        style={'description_width': '80px'},
        layout=Layout(width='200px')
    )
    
    process_selector = SelectMultiple(
        options=all_process_names,
        value=tuple(all_process_names),
        description="Processes:",
        style={'description_width': '100px'},
        layout=Layout(width='400px')
    )
    
    threshold_slider = FloatSlider(
        min=0,
        max=max_flow_value,
        step=max_flow_value / 100,
        value=0,
        description="Min Flow:",
        continuous_update=False,
        readout_format=".2f",
        style={'description_width': '80px'},
        layout=Layout(width='400px')
    )
    
    return year_slider, element_dropdown, process_selector, threshold_slider

def _create_sankey_legend(element_items, color_manager):
    """Creates and returns the HTML legend widget for the Sankey diagram.

    The legend uses colors and labels defined in the publication style guide
    to explain the color coding of the processes, stocks, and flows. The flow
    legend is dynamically generated based on the actual elements in the system.

    Parameters
    ----------
    element_items : list of str
        List of element names from the MFA system.
    color_manager : ElementColorManager
        Color manager for element-agnostic coloring.

    Returns
    -------
    ipywidgets.HTML
        An HTML widget containing the formatted legend.
    """
    # Generate flow legend items dynamically
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
                    <div style="width: 20px; height: 20px; background-color: {get_process_color('regular')}; margin-right: 5px;"></div>
                    <span>Regular processes</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="width: 20px; height: 20px; background-color: {get_stock_color()}; margin-right: 5px;"></div>
                    <span>Stocks</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="width: 20px; height: 20px; background-color: {get_process_color('dsm')}; margin-right: 5px;"></div>
                    <span>DSM Process</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="width: 20px; height: 20px; background-color: {get_process_color('fomp')}; margin-right: 5px;"></div>
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

def _prepare_sankey_node_data(filtered_processes, mfa_system_results, dsm_params, fomp_params, node_positions):
    """Prepares the node data dictionary for the Plotly Sankey object.

    Parameters
    ----------
    filtered_processes : list of odym.Process
        The list of process objects to be displayed.
    mfa_system_results : odym.MFAsystem
        The solved MFA system object.
    dsm_params : dict
        DSM parameters, used to identify and color DSM processes.
    fomp_params : dict
        FOMP parameters, used to identify and color FOMP processes.
    node_positions : dict
        A dictionary mapping process IDs to their x-coordinates.

    Returns
    -------
    dict
        A dictionary formatted for the `node` attribute of a `go.Sankey` object.
    """
    node_labels = [p.Name for p in filtered_processes]
    node_x_positions = [node_positions.get(p.ID, 0.5) for p in filtered_processes]
    node_colors = []
    for p in filtered_processes:
        has_stocks = f"S_{p.ID}" in mfa_system_results.StockDict
        is_dsm = dsm_params and p.ID in dsm_params
        is_fomp = fomp_params and p.ID in fomp_params
        if is_dsm or is_fomp:
            node_colors.append(get_process_color(detect_biodym_process_type(p.ID, dsm_params=dsm_params, fomp_params=fomp_params)))
        elif has_stocks:
            node_colors.append(get_stock_color())
        else:
            node_colors.append(get_process_color(detect_biodym_process_type(p.ID, dsm_params=dsm_params, fomp_params=fomp_params)))
    return dict(label=node_labels, x=node_x_positions, color=node_colors, pad=20, thickness=15, line=dict(color="black", width=0.5))

def _prepare_sankey_link_data(final_flows, process_id_map, year_index, element_index, element, color_manager):
    """Prepares the link data dictionary for the Plotly Sankey object.

    Parameters
    ----------
    final_flows : list of odym.Flow
        The list of flow objects to be displayed after filtering.
    process_id_map : dict
        A mapping of process IDs to their index in the node list.
    year_index : int
        The index of the currently selected year.
    element_index : int
        The index of the currently selected element.
    element : str
        The name of the currently selected element.
    color_manager : ElementColorManager
        Color manager for element-agnostic coloring.

    Returns
    -------
    dict
        A dictionary formatted for the `link` attribute of a `go.Sankey` object.
    """
    if not final_flows:
        return dict(source=[], target=[], value=[])

    flow_values = [f.Values[year_index, element_index] for f in final_flows]
    link_colors = [color_manager.get_element_color(element.lower())] * len(final_flows)
    custom_data = [getattr(f, 'DescriptiveName', f.Name) for f in final_flows]

    return dict(
        source=[process_id_map[f.P_Start] for f in final_flows],
        target=[process_id_map[f.P_End] for f in final_flows],
        value=flow_values,
        color=link_colors,
        customdata=custom_data,
        hovertemplate='Flow: %{customdata}<br />Source: %{source.label}<br />Target: %{target.label}<br />Value: %{value}<extra></extra>'
    )

def plot_interactive_sankey(
    mfa_system_results,
    dsm_params=None,
    fomp_params=None,
    color_manager: Optional[ElementColorManager] = None
):
    """Displays a fully interactive Sankey diagram for MFA results.

    This function constructs a user interface using ipywidgets that allows for
    dynamic exploration of the MFA results. Users can filter by year, element,
    processes to display, and a minimum flow value threshold. Uses element-agnostic
    coloring for consistency across all visualizations.

    Parameters
    ----------
    mfa_system_results : odym.MFAsystem
        The solved MFA system object containing all calculated data.
    dsm_params : dict, optional
        DSM parameters, used to identify and color DSM processes.
        Default is None.
    fomp_params : dict, optional
        FOMP parameters, used to identify and color FOMP processes.
        Default is None.
    color_manager : ElementColorManager, optional
        Dynamic color manager for element colors. If None, creates one from
        mfa_system_results.Elements. Defaults to None.
    """
    from ipywidgets import interactive

    all_process_names = [p.Name for p in mfa_system_results.ProcessList]
    all_flows = list(mfa_system_results.FlowDict.values())
    time_items = mfa_system_results.IndexTable.Classification["Time"].Items
    element_items = mfa_system_results.Elements

    # Create color manager if not provided
    if color_manager is None:
        color_manager = ElementColorManager([e.lower() for e in element_items])

    max_flow_value = max(f.Values.max() for f in all_flows if f.Values is not None) if all_flows else 1

    fig = go.FigureWidget(
        data=[go.Sankey(node={}, link={}, arrangement="snap")]
    )

    def update_sankey(year, element, processes_to_show, min_flow_value):
        if not processes_to_show:
            with fig.batch_update():
                fig.data[0].node.label = []
            return

        filtered_processes = [p for p in mfa_system_results.ProcessList if p.Name in processes_to_show]
        process_id_map = {p.ID: i for i, p in enumerate(filtered_processes)}
        
        layout_flows = [f for f in all_flows if f.P_Start in process_id_map and f.P_End in process_id_map]
        node_positions = _calculate_node_positions(filtered_processes, layout_flows)

        year_index = time_items.index(year)
        element_index = element_items.index(element)
        final_flows = [f for f in layout_flows if f.Values[year_index, element_index] >= min_flow_value]

        with fig.batch_update():
            fig.data[0].node = _prepare_sankey_node_data(filtered_processes, mfa_system_results, dsm_params, fomp_params, node_positions)
            fig.data[0].link = _prepare_sankey_link_data(final_flows, process_id_map, year_index, element_index, element, color_manager)

            title_text = f"BioDYM Material Flow Analysis - {element.title()} ({year})"
            layout_config = get_publication_layout(size='sankey_wide', show_legend=False)
            title_layout = {'text': title_text, 'x': 0.5, 'xanchor': 'center', 'font': {'family': FONT_FAMILY, 'size': FONT_SIZE['title'], 'color': BIOYM_COLORS['dark']}}
            layout_config['title'] = title_layout
            fig.update_layout(**layout_config)

    year_slider, element_dropdown, process_selector, threshold_slider = _create_sankey_widgets(
        all_process_names, time_items, element_items, max_flow_value
    )
    legend_widget = _create_sankey_legend(element_items, color_manager)

    ui = VBox([
        HBox([year_slider, element_dropdown]),
        HBox([process_selector, threshold_slider]),
        legend_widget
    ])
    out = interactive(
        update_sankey,
        year=year_slider,
        element=element_dropdown,
        processes_to_show=process_selector,
        min_flow_value=threshold_slider
    )
    display(ui)
    display(fig)
    out.update()

def plot_element_multiplot_sankey(
    mfa_system_results,
    dsm_params=None,
    fomp_params=None,
    elements_to_plot=None,
    subplot_height=350,
    color_manager: Optional[ElementColorManager] = None
):
    """Display multiple Sankey diagrams stacked vertically, one per element.

    This function creates a vertically-stacked arrangement where each subplot shows
    a different element. All subplots share a single time slider, process selector,
    and min flow filter, allowing synchronized exploration of the multi-level
    elemental composition over time. Uses element-agnostic coloring for consistency.

    Parameters
    ----------
    mfa_system_results : odym.MFAsystem
        The solved MFA system object containing all calculated data.
    dsm_params : dict, optional
        DSM parameters for process coloring. Default is None.
    fomp_params : dict, optional
        FOMP parameters for process coloring. Default is None.
    elements_to_plot : list of str, optional
        List of element names to plot. If None, uses all elements from the system.
    subplot_height : int, optional
        Height in pixels for each subplot. Default is 350.
    color_manager : ElementColorManager, optional
        Dynamic color manager for element colors. If None, creates one from
        mfa_system_results.Elements. Defaults to None.

    Returns
    -------
    None
        Displays the interactive multiplot in the notebook.
    """
    from ipywidgets import interactive

    all_process_names = [p.Name for p in mfa_system_results.ProcessList]
    all_flows = list(mfa_system_results.FlowDict.values())
    time_items = mfa_system_results.IndexTable.Classification["Time"].Items
    element_items = mfa_system_results.Elements

    # Create color manager if not provided
    if color_manager is None:
        color_manager = ElementColorManager([e.lower() for e in element_items])

    # Determine which elements to plot
    if elements_to_plot is None:
        elements_to_plot = element_items
    else:
        # Validate requested elements exist
        elements_to_plot = [e for e in elements_to_plot if e in element_items]

    num_elements = len(elements_to_plot)
    max_flow_value = max(f.Values.max() for f in all_flows if f.Values is not None) if all_flows else 1

    # Create one FigureWidget per element
    figures = []
    for elem in elements_to_plot:
        fig = go.FigureWidget(data=[go.Sankey(node={}, link={}, arrangement="snap")])
        fig.update_layout(
            height=subplot_height,
            width=2200,
            title_text=f"{elem.upper()}",
            font_size=12,
            margin=dict(l=50, r=50, t=50, b=20)
        )
        figures.append(fig)

    def update_all_sankeys(year, processes_to_show, min_flow_value):
        """Update all element subplots for the selected year and filters."""
        if not processes_to_show:
            for fig in figures:
                with fig.batch_update():
                    fig.data[0].node.label = []
            return

        filtered_processes = [p for p in mfa_system_results.ProcessList if p.Name in processes_to_show]
        process_id_map = {p.ID: i for i, p in enumerate(filtered_processes)}

        layout_flows = [f for f in all_flows if f.P_Start in process_id_map and f.P_End in process_id_map]
        node_positions = _calculate_node_positions(filtered_processes, layout_flows)
        year_index = time_items.index(year)

        # Update each figure (one per element)
        for fig_idx, element in enumerate(elements_to_plot):
            element_index = element_items.index(element)
            final_flows = [f for f in layout_flows if f.Values[year_index, element_index] >= min_flow_value]

            with figures[fig_idx].batch_update():
                figures[fig_idx].data[0].node = _prepare_sankey_node_data(
                    filtered_processes, mfa_system_results, dsm_params, fomp_params, node_positions
                )
                figures[fig_idx].data[0].link = _prepare_sankey_link_data(
                    final_flows, process_id_map, year_index, element_index, element, color_manager
                )

    # Create shared widgets
    year_slider, element_dropdown, process_selector, threshold_slider = _create_sankey_widgets(
        all_process_names, time_items, element_items, max_flow_value
    )

    # Remove element dropdown (not needed for multiplot)
    year_slider.description = "Year:"
    threshold_slider.description = "Min Flow:"

    ui = VBox([
        HBox([year_slider, threshold_slider]),
        process_selector
    ])

    # Connect widgets to update function
    out = interactive(
        update_all_sankeys,
        year=year_slider,
        processes_to_show=process_selector,
        min_flow_value=threshold_slider
    )

    # Display UI and all figures stacked vertically
    display(ui)
    for fig in figures:
        display(fig)

    # Initial draw
    update_all_sankeys(year_slider.value, process_selector.value, threshold_slider.value)
