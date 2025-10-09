
# -*- coding: utf-8 -*-
"""
Sankey Diagram Plotting Module.

This file contains the functions for generating interactive Sankey diagrams.
"""

import plotly.graph_objects as go
from ipywidgets import FloatSlider, IntSlider, Button, HBox, VBox, HTML, Layout, Dropdown, SelectMultiple
from IPython.display import display
import os
from datetime import datetime
import collections
from .publication_style_simplified import (
    get_publication_layout,
    get_element_color,
    get_process_color,
    detect_biodym_process_type,
    get_stock_color,
    BIOYM_COLORS,
    ELEMENT_COLORS,
    PROCESS_COLORS,
    FONT_FAMILY,
    FONT_SIZE
)


def _calculate_node_positions(processes, flows):
    """
    Calculates node x-positions for a Sankey diagram using a topological sort.
    This helps in creating a structured, left-to-right flow.
    Handles cycles by assigning all nodes in a cycle to the same layer.

    Args:
        processes (list): List of process objects from the MFA system.
        flows (list): List of flow objects from the MFA system.

    Returns:
        dict: A dictionary mapping process ID to its x-coordinate (0 to 1).
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

def plot_interactive_sankey(mfa_system_results, dsm_params=None, fomp_params=None):
    """
    Enhanced interactive Sankey diagram with advanced customization options.
    
    Features:
    - Color coding for process types (Regular, DSM, FOMP)
    - Export functionality (PNG) with organized folder
    - Professional legend
    - Flow threshold filtering
    - Process selection (multi-select, all selected by default)
    - Proper zoom and frame controls
    - Manual node positioning

    Args:
        mfa_system_results (odym.MFAsystem): The solved MFA system object.
        dsm_params (dict, optional): DSM parameters to identify DSM processes.
        fomp_params (dict, optional): FOMP parameters to identify FOMP processes.
    """
    from ipywidgets import interactive
    
    all_process_names = [p.Name for p in mfa_system_results.ProcessList]
    all_flows = list(mfa_system_results.FlowDict.values())
    time_items = mfa_system_results.IndexTable.Classification["Time"].Items
    element_items = mfa_system_results.Elements

    # Determine max flow value for slider
    max_flow_value = (
        max(f.Values.max() for f in all_flows if f.Values is not None)
        if all_flows
        else 1
    )

    # Use shiny color schemes from publication standards
    # Process colors are now handled by get_process_color() function
    # Element colors are now handled by get_element_color() function

    # Create the FigureWidget with proper zoom controls
    fig = go.FigureWidget(
        data=[go.Sankey(
            node=dict(
                label=[],
                color=[],
                pad=20,
                thickness=15,
                line=dict(color="black", width=0.5)
            ),
            link=dict(
                source=[],
                target=[],
                value=[],
                color=[]
            ),
            arrangement="snap"
        )]
    )

    def get_process_type(process_id):
        """Determine process type for color coding using publication standards"""
        return detect_biodym_process_type(process_id, dsm_params=dsm_params, fomp_params=fomp_params)

    def update_sankey(year, element, processes_to_show, min_flow_value):
        if not processes_to_show:
            with fig.batch_update():
                fig.data[0].node.label = []
            return

        # --- STABLE LAYOUT CALCULATION ---
        # First, determine the stable set of processes and flows for layout
        filtered_processes = [p for p in mfa_system_results.ProcessList if p.Name in processes_to_show]
        process_id_map = {p.ID: i for i, p in enumerate(filtered_processes)}
        
        # Layout should be based on all flows between selected processes, regardless of year
        layout_flows = [f for f in all_flows if f.P_Start in process_id_map and f.P_End in process_id_map]
        
        # Calculate node positions ONCE based on the stable topology
        node_positions = _calculate_node_positions(filtered_processes, layout_flows)
        node_x_positions = [node_positions.get(p.ID, 0.5) for p in filtered_processes]

        # --- DYNAMIC VALUE FILTERING ---
        # Now, filter flows for the specific year and value threshold for display
        year_index = time_items.index(year)
        element_index = element_items.index(element)
        final_flows = [
            f for f in layout_flows
            if f.Values[year_index, element_index] >= min_flow_value
        ]

        with fig.batch_update():
            # Set node properties (positions are now stable)
            node_labels = []
            node_colors = []
            
            for p in filtered_processes:
                node_labels.append(p.Name)
                
                # Determine if this process has stocks
                has_stocks = f"S_{p.ID}" in mfa_system_results.StockDict
                is_dsm = dsm_params and p.ID in dsm_params
                is_fomp = fomp_params and p.ID in fomp_params
                
                # Prioritize DSM/FOMP colors, then stock color
                if is_dsm or is_fomp:
                    node_colors.append(get_process_color(get_process_type(p.ID)))
                elif has_stocks:
                    node_colors.append(get_stock_color())
                else:
                    # Regular processes without stocks
                    node_colors.append(get_process_color(get_process_type(p.ID)))
            
            fig.data[0].node.label = node_labels
            fig.data[0].node.x = node_x_positions
            fig.data[0].node.color = node_colors

            if not final_flows:
                fig.data[0].link.source = []
                fig.data[0].link.target = []
                fig.data[0].link.value = []
            else:
                # Set link properties for the visible flows
                flow_values = [f.Values[year_index, element_index] for f in final_flows]
                # Use shiny element colors from publication standards
                link_colors = [get_element_color(element)] * len(final_flows)
                # Use descriptive names if available, fallback to flow ID
                custom_data = [getattr(f, 'DescriptiveName', f.Name) for f in final_flows]

                fig.data[0].link.source = [process_id_map[f.P_Start] for f in final_flows]
                fig.data[0].link.target = [process_id_map[f.P_End] for f in final_flows]
                fig.data[0].link.value = flow_values
                fig.data[0].link.color = link_colors
                fig.data[0].link.customdata = custom_data
                fig.data[0].link.hovertemplate = 'Flow: %{customdata}<br />Source: %{source.label}<br />Target: %{target.label}<br />Value: %{value}<extra></extra>'

            # Update layout with publication standards
            title_text = f"BioDYM Material Flow Analysis - {element.title()} ({year})"
            layout_config = get_publication_layout(
                size='large',
                show_legend=False  # We have a custom legend widget
            )

            # Explicitly define title properties to ensure visibility
            title_layout = {
                'text': title_text,
                'x': 0.5,
                'xanchor': 'center',
                'font': {
                    'family': FONT_FAMILY,
                    'size': FONT_SIZE['title'],
                    'color': BIOYM_COLORS['dark']
                }
            }
            
            # Update the layout config with the explicit title
            layout_config['title'] = title_layout
            
            fig.update_layout(**layout_config)


    # Create widgets with better organization and longer sliders
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
    
    # Multi-select process selector, all selected by default
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
    


    # Create legend with colors from publication style guide
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
                <div style="display: flex; align-items: center;">
                    <div style="width: 20px; height: 20px; background-color: {get_element_color('material')}; margin-right: 5px;"></div>
                    <span>Material</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="width: 20px; height: 20px; background-color: {get_element_color('wc')}; margin-right: 5px;"></div>
                    <span>WC</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="width: 20px; height: 20px; background-color: {get_element_color('dm')}; margin-right: 5px;"></div>
                    <span>DM</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="width: 20px; height: 20px; background-color: {get_element_color('cc')}; margin-right: 5px;"></div>
                    <span>CC</span>
                </div>
            </div>
        </div>
    </div>
    """
    
    legend_widget = HTML(value=legend_html)

    # Set up interaction with all parameters
    
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
