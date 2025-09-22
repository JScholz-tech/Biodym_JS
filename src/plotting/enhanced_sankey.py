
# -*- coding: utf-8 -*-
"""
Enhanced Sankey Diagram Module for BioDYM MFA Tool.

This module provides advanced Sankey diagram functionality with support for:
- Excel-based visualization configuration
- Custom node positioning and styling
- Toggling between fixed, auto-layout, and interactive modes
"""

import collections
from datetime import datetime
import os
import math
from ipywidgets import FloatSlider, IntSlider, Button, HBox, VBox, HTML, Layout, Dropdown, SelectMultiple
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def _safe_float_convert(value, default=1.0):
    """Safely convert a value to a float, handling strings, commas, and errors."""
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).replace(',', '.'))
    except (ValueError, TypeError):
        return default

def _calculate_node_positions(processes, flows):
    """Calculates node x-positions for a Sankey diagram using a topological sort."""
    nodes = {p.ID for p in processes}
    if not nodes:
        return {}

    adj = {node: [] for node in nodes}
    in_degree = {node: 0 for node in nodes}

    for flow in flows:
        if flow.P_Start in nodes and flow.P_End in nodes:
            adj[flow.P_Start].append(flow.P_End)
            in_degree[flow.P_End] += 1

    queue = collections.deque([node for node in nodes if in_degree[node] == 0])
    layers = {node: 0 for node in nodes}
    max_layer = 0

    while queue:
        u = queue.popleft()
        for v in adj[u]:
            in_degree[v] -= 1
            layers[v] = max(layers.get(v, 0), layers[u] + 1)
            max_layer = max(max_layer, layers[v])
            if in_degree[v] == 0:
                queue.append(v)
    
    remaining_nodes = [node for node in nodes if in_degree[node] > 0]
    if remaining_nodes:
        max_layer += 1
        for node in remaining_nodes:
            layers[node] = max_layer

    if max_layer == 0:
        return {node: 0.5 for node in nodes}
    
    return {node: 0.1 + (layers[node] / max_layer) * 0.8 for node in nodes}

def load_visualization_config(excel_file_path):
    """Load visualization configuration from Excel file."""
    from .visualization_loader import load_visualization_config_from_excel
    return load_visualization_config_from_excel(excel_file_path)

def calculate_element_specific_positions(processes, config, element):
    """Calculate node positions based on element-specific settings in the config."""
    positions = {}
    for process in processes:
        viz_settings = get_process_visualization(process.ID, process.Name, config, element)
        x = _safe_float_convert(viz_settings.get('X_Position'), 0.5)
        y = _safe_float_convert(viz_settings.get('Y_Position'), 0.5)
        
        # Clamp positions to valid range [0.0, 1.0]
        x = max(0.0, min(1.0, x))
        y = max(0.0, min(1.0, y))
        
        positions[process.ID] = (x, y)
    return positions

def get_process_visualization(process_id: int, process_name: str, config: dict, element: str = None) -> dict:
    """Get visualization settings for a process, with robust element-specific positioning."""
    processes_config = config.get('process_colors', config.get('processes', {}))
    proc_key = str(process_id).strip().upper()
    proc_config = processes_config.get(proc_key)

    if not proc_config:
        for key, value in processes_config.items():
            config_name = value.get('Process_Name') or value.get('Name(EN)')
            if config_name and str(config_name).strip().upper() == str(process_name).strip().upper():
                proc_config = value
                break

    if not proc_config:
        return {'Node_Color_#': '#808080', 'X_Position': 0.5, 'Y_Position': 0.5}

    viz_settings = proc_config.copy()

    def get_valid_position(key_options):
        for key in key_options:
            for config_key in viz_settings:
                if config_key.upper() == key.upper():
                    val = viz_settings[config_key]
                    if val is not None and str(val).strip() not in ['', 'nan']:
                        try:
                            return float(str(val).replace(',', '.'))
                        except (ValueError, TypeError):
                            continue
        return None

    if element:
        x_keys = [f'X_Position_{element.upper()}', 'X_Position_Material', 'X_Position']
        y_keys = [f'Y_Position_{element.upper()}', 'Y_Position_Material', 'Y_Position']
        x_pos = get_valid_position(x_keys)
        y_pos = get_valid_position(y_keys)
        viz_settings['X_Position'] = x_pos if x_pos is not None else 0.5
        viz_settings['Y_Position'] = y_pos if y_pos is not None else 0.5
    else:
        viz_settings['X_Position'] = get_valid_position(['X_Position']) or 0.5
        viz_settings['Y_Position'] = get_valid_position(['Y_Position']) or 0.5

    return viz_settings

def get_flow_visualization(flow_id, flow_name, config):
    """Get visualization settings for a flow."""
    flows_config = config.get('flow_colors', config.get('flows', {}))
    if flow_id in flows_config:
        return flows_config[flow_id]
    for fid, flow_config in flows_config.items():
        if flow_config.get('Flow_Name') == flow_name:
            return flow_config
    return {'Flow_Color_#': '#1f77b4'}

def plot_enhanced_sankey(mfa_system_results, dsm_params=None, fomp_params=None, visualization_config_path=None):
    """Enhanced interactive Sankey diagram with selectable layout modes."""
    if visualization_config_path and os.path.exists(visualization_config_path):
        config = load_visualization_config(visualization_config_path)
    else:
        config = {}
        print("Warning: Visualization config file not found. Using default settings.")

    all_processes = mfa_system_results.ProcessList
    all_flows = list(mfa_system_results.FlowDict.values())
    time_items = mfa_system_results.IndexTable.Classification["Time"].Items
    element_items = mfa_system_results.Elements
    max_flow_value = max(f.Values.max() for f in all_flows if f.Values is not None) if all_flows else 1

    fig = go.FigureWidget(go.Sankey(node={}, link={}))
    layout_settings = config.get('layout_settings', {})

    def _safe_int_convert(value, default=1200):
        return int(_safe_float_convert(value, default))

    # --- WIDGETS ---
    year_slider = IntSlider(min=time_items[0], max=time_items[-1], value=time_items[0], description="Year:", layout=Layout(width='300px'))
    element_dropdown = Dropdown(options=element_items, value=element_items[0], description='Element:', layout=Layout(width='200px'))
    process_selector = SelectMultiple(options=[p.Name for p in all_processes], value=[p.Name for p in all_processes], description='Processes:', layout=Layout(width='400px', height='100px'))
    min_flow_slider = FloatSlider(value=0, min=0, max=max_flow_value, step=max_flow_value / 100, description='Min Flow:', layout=Layout(width='300px'))
    layout_dropdown = Dropdown(options=['Custom', 'Auto-Layout'], value='Custom', description='Layout:', layout=Layout(width='150px'))

    # --- UI LAYOUT ---
    controls = VBox([
        HBox([year_slider, element_dropdown]),
        HBox([process_selector, min_flow_slider]),
        layout_dropdown
    ])

    # --- UPDATE FUNCTION ---
    def update_sankey(year, element, processes_to_show, min_flow_value, layout_type):
        with fig.batch_update():
            if not processes_to_show:
                fig.data[0].node.label = []
                fig.data[0].link.source = []
                return

            year_index = time_items.index(year)
            element_index = element_items.index(element)
            filtered_processes = [p for p in all_processes if p.Name in processes_to_show]
            process_id_to_index = {p.ID: i for i, p in enumerate(filtered_processes)}
            final_flows = [f for f in all_flows if f.P_Start in process_id_to_index and f.P_End in process_id_to_index and f.Values[year_index, element_index] >= min_flow_value]

            if layout_type == 'Auto-Layout':
                arrangement = 'snap'
                layout_flows = [f for f in all_flows if f.P_Start in process_id_to_index and f.P_End in process_id_to_index]
                node_positions = _calculate_node_positions(filtered_processes, layout_flows)
                node_x = [node_positions.get(p.ID, 0.5) for p in filtered_processes]
                node_y = None
                current_pad, current_thickness = 20, 15
                current_margin = dict(l=250, r=250, b=200, t=200)
                current_font_size, current_hovermode, current_dragmode = 12, 'closest', 'pan'
                show_axes = False
            else:  # 'Custom' mode
                arrangement = 'fixed'
                all_positions = calculate_element_specific_positions(all_processes, config, element)
                padding_factor = _safe_float_convert(layout_settings.get('Padding_Factor', 0.1), 0.1)
                zoom_factor = _safe_float_convert(layout_settings.get('Zoom_Factor', 1.0), 1.0)
                padding = max(0.05, padding_factor / zoom_factor)
                x_values = [pos[0] for pos in all_positions.values()]
                y_values = [pos[1] for pos in all_positions.values()]
                if x_values and y_values:
                    min_x, max_x = min(x_values), max(x_values)
                    min_y, max_y = min(y_values), max(y_values)
                    span_x, span_y = max_x - min_x, max_y - min_y
                    target_span = 1.0 - 2 * padding
                    scale = min(target_span / max(span_x, 0.1), target_span / max(span_y, 0.1))
                    center_x, center_y = (min_x + max_x) / 2, (min_y + max_y) / 2
                    for pid, pos in all_positions.items():
                        all_positions[pid] = (0.5 + (pos[0] - center_x) * scale, 0.5 + (pos[1] - center_y) * scale)
                node_x = [all_positions.get(p.ID, (0.5, 0.5))[0] for p in filtered_processes]
                node_y = [all_positions.get(p.ID, (0.5, 0.5))[1] for p in filtered_processes]
                node_scale_factor = _safe_float_convert(layout_settings.get('Node_Scale_Factor', 1.0))
                current_pad = int(15 * zoom_factor * node_scale_factor)
                current_thickness = int(20 * zoom_factor * node_scale_factor)
                current_margin = dict(l=50, r=50, t=80, b=50)
                current_font_size, current_hovermode, current_dragmode = 16, 'x', 'pan'
                show_axes = True

            node_colors = [get_process_visualization(p.ID, p.Name, config).get('Node_Color_#', '#808080') for p in filtered_processes]
            fig.data[0].arrangement = arrangement
            fig.data[0].node = dict(label=[p.Name for p in filtered_processes], x=node_x, y=node_y, color=node_colors, pad=current_pad, thickness=current_thickness, line=dict(color="black", width=0.5))

            if final_flows:
                flow_values = [f.Values[year_index, element_index] for f in final_flows]
                flow_sources = [process_id_to_index[f.P_Start] for f in final_flows]
                flow_targets = [process_id_to_index[f.P_End] for f in final_flows]
                default_flow_color = config.get('elements', {}).get(element, {}).get('Color', '#888')
                flow_colors = [get_flow_visualization(f.Name, f.Name, config).get('Flow_Color_#', default_flow_color) for f in final_flows]
                custom_data = [f.Name for f in final_flows]
                fig.data[0].link = dict(source=flow_sources, target=flow_targets, value=flow_values, color=flow_colors, customdata=custom_data, hovertemplate='Flow: %{customdata}<br>Source: %{source.label}<br>Target: %{target.label}<br>Value: %{value}<extra></extra>')
            else:
                fig.data[0].link = dict(source=[], target=[], value=[])

            total_flow = sum(flow_values) if final_flows else 0
            title_text = f"Sankey Diagram - {element} ({year}) - Total Flow: {total_flow:.1f} t"
            window_width = _safe_int_convert(layout_settings.get('Window_Width', 1400))
            window_height = _safe_int_convert(layout_settings.get('Window_Height', 900))

            fig.update_layout(title_text=title_text, font_size=current_font_size, height=window_height, width=window_width, margin=current_margin, hovermode=current_hovermode, dragmode=current_dragmode, xaxis=dict(showgrid=False, zeroline=False, showticklabels=show_axes), yaxis=dict(showgrid=False, zeroline=False, showticklabels=show_axes))

    # --- WIDGET INTERACTION ---
    def handle_change(change):
        update_sankey(year_slider.value, element_dropdown.value, process_selector.value, min_flow_slider.value, layout_dropdown.value)

    year_slider.observe(handle_change, names='value')
    element_dropdown.observe(handle_change, names='value')
    process_selector.observe(handle_change, names='value')
    min_flow_slider.observe(handle_change, names='value')
    layout_dropdown.observe(handle_change, names='value')

    display(VBox([controls, fig]))
    handle_change(None) # Initial plot draw
