# -*- coding: utf-8 -*-
"""
Enhanced Sankey Diagram Module for Circular Systems.

This module provides advanced Sankey diagram functionality with support for:
- Circular and radial layouts for recycling systems
- Excel-based visualization configuration
- Custom node positioning and styling
- Advanced flow visualization options
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import math
from ipywidgets import FloatSlider, IntSlider, Button, HBox, VBox, HTML, Layout, Dropdown, SelectMultiple
import os
from datetime import datetime
import collections

def load_visualization_config(excel_file_path):
    """
    Load visualization configuration from Excel file.
    
    This function now integrates with the existing Part 6 visualization sheets
    and provides enhanced configuration capabilities.
    
    Args:
        excel_file_path (str): Path to Excel file with visualization config
        
    Returns:
        dict: Configuration dictionary with all visualization settings
    """
    from .visualization_loader import load_visualization_config_from_excel
    
    return load_visualization_config_from_excel(excel_file_path)

def get_default_visualization_config():
    """Get default visualization configuration."""
    return {
        'processes': {},
        'flows': {},
        'layout': {
            'Default_Layout_Type': 'Circular',
            'Circular_Center_X': '0,5',  # European decimal format
            'Circular_Center_Y': '0,5',  # European decimal format
            'Circular_Radius': '0,3',    # European decimal format
            'Node_Spacing': '0,1',       # European decimal format
            'Flow_Curvature': '0,5',     # European decimal format
            'Show_Flow_Labels': 'True',
            'Show_Node_Labels': 'True',
            'Background_Color': '#FFFFFF',
            'Grid_Color': '#E0E0E0'
        },
        'elements': {
            'material': {'Color': '#1f77b4', 'Opacity': '0.8'},
            'WC': {'Color': '#ff7f0e', 'Opacity': '0.8'},
            'DM': {'Color': '#2ca02c', 'Opacity': '0.8'},
            'CC': {'Color': '#d62728', 'Opacity': '0.8'}
        },
        'advanced': {
            'Enable_Animation': 'True',
            'Animation_Duration': '1000',
            'Enable_Zoom': 'True',
            'Enable_Selection': 'True',
            'Export_Resolution': 'High',
            'Export_Format': 'PNG'
        }
    }

def calculate_circular_positions(processes, flows, config):
    """
    Calculate node positions for circular layout.
    
    Args:
        processes (list): List of process objects
        flows (list): List of flow objects
        config (dict): Visualization configuration
        
    Returns:
        dict: Dictionary mapping process ID to (x, y) coordinates
    """
    positions = {}
    
    # Get circular layout parameters (handle both 'layout' and 'layout_settings')
    layout_settings = config.get('layout_settings', config.get('layout', {}))
    center_x = float(str(layout_settings.get('Circular_Center_X', '0,5')).replace(',', '.'))
    center_y = float(str(layout_settings.get('Circular_Center_Y', '0,5')).replace(',', '.'))
    radius = float(str(layout_settings.get('Circular_Radius', '0,3')).replace(',', '.'))
    
    # Identify circular processes (those with recycling flows)
    circular_processes = set()
    for flow in flows:
        # Check if this flow creates a cycle (goes to a process that has flows back)
        for other_flow in flows:
            if (other_flow.P_Start == flow.P_End and 
                other_flow.P_End == flow.P_Start):
                circular_processes.add(flow.P_Start)
                circular_processes.add(flow.P_End)
    
    # Position circular processes in a circle
    if circular_processes:
        circular_list = list(circular_processes)
        for i, process_id in enumerate(circular_list):
            angle = 2 * math.pi * i / len(circular_list)
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            positions[process_id] = (x, y)
    
    # Position non-circular processes using linear layout
    non_circular = [p for p in processes if p.ID not in circular_processes]
    if non_circular:
        # Simple linear positioning for non-circular processes
        for i, process in enumerate(non_circular):
            if process.ID not in positions:
                x = 0.1 + (i / max(1, len(non_circular) - 1)) * 0.8
                y = 0.5
                positions[process.ID] = (x, y)
    
    return positions

def calculate_radial_positions(processes, flows, config):
    """
    Calculate node positions for radial layout.
    
    Args:
        processes (list): List of process objects
        flows (list): List of flow objects
        config (dict): Visualization configuration
        
    Returns:
        dict: Dictionary mapping process ID to (x, y) coordinates
    """
    positions = {}
    
    # Get radial layout parameters (handle both 'layout' and 'layout_settings')
    layout_settings = config.get('layout_settings', config.get('layout', {}))
    center_x = float(str(layout_settings.get('Circular_Center_X', '0,5')).replace(',', '.'))
    center_y = float(str(layout_settings.get('Circular_Center_Y', '0,5')).replace(',', '.'))
    radius = float(str(layout_settings.get('Circular_Radius', '0,3')).replace(',', '.'))
    
    # Position all processes in a circle
    for i, process in enumerate(processes):
        angle = 2 * math.pi * i / len(processes)
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        positions[process.ID] = (x, y)
    
    return positions

def calculate_element_specific_positions(processes, flows, config, element, layout_type):
    """
    Calculate node positions with element-specific positioning support.
    
    This function prioritizes element-specific positions from Excel configuration,
    with fallback to general positions and calculated layouts.
    
    Args:
        processes (list): List of process objects
        flows (list): List of flow objects
        config (dict): Visualization configuration
        element (str): Current element (material, WC, DM, CC)
        layout_type (str): Layout type (Linear, Circular, Radial, Custom)
        
    Returns:
        dict: Dictionary mapping process ID to (x, y) coordinates
    """
    positions = {}
    
    print(f"🎯 Calculating element-specific positions for '{element}' with layout '{layout_type}'")
    
    # First, try to get element-specific positions from Excel
    element_positions_found = 0
    for process in processes:
        viz_settings = get_process_visualization(process.ID, process.Name, config, element)
        custom_x = viz_settings.get('X_Position')
        custom_y = viz_settings.get('Y_Position')
        
        if (custom_x is not None and custom_y is not None and 
            str(custom_x).strip() != '' and str(custom_y).strip() != '' and
            str(custom_x).strip() != '0,5' and str(custom_y).strip() != '0,5'):  # Check for meaningful values
            try:
                x = float(str(custom_x).replace(',', '.'))
                y = float(str(custom_y).replace(',', '.'))
                positions[process.ID] = (x, y)
                element_positions_found += 1
            except (ValueError, TypeError):
                positions[process.ID] = (0.5, 0.5)
        else:
            positions[process.ID] = (0.5, 0.5)
    
    print(f"  -> Found {element_positions_found}/{len(processes)} element-specific positions")
    
    # If we have element-specific positions, use them
    if element_positions_found > 0:
        print(f"  -> Using element-specific positions for '{element}'")
        return positions
    
    # Otherwise, fall back to calculated layout
    print(f"  -> No element-specific positions found, using calculated layout")
    if layout_type == 'Circular':
        return calculate_circular_positions(processes, flows, config)
    elif layout_type == 'Radial':
        return calculate_radial_positions(processes, flows, config)
    else:  # Linear or Custom
        positions = {}
        for i, process in enumerate(processes):
            x = 0.1 + (i / max(1, len(processes) - 1)) * 0.8
            y = 0.5
            positions[process.ID] = (x, y)
        return positions

def get_process_visualization(process_id, process_name, config, element=None):
    """
    Get visualization settings for a process, with optional element-specific positioning.
    
    Args:
        process_id (int): Process ID
        process_name (str): Process name
        config (dict): Visualization configuration
        element (str, optional): Element name for element-specific positioning
        
    Returns:
        dict: Process visualization settings
    """
    # Try to find in config first (handle both 'processes' and 'process_colors')
    processes_config = config.get('process_colors', config.get('processes', {}))
    
    # Try different ID formats to match Excel data
    id_formats = [
        str(process_id),           # "0", "1", "2"
        f"{process_id:02d}",       # "00", "01", "02"
        f"{process_id:03d}",       # "000", "001", "002"
    ]
    
    for id_format in id_formats:
        if id_format in processes_config:
            print(f"  -> Found process config for ID format: {id_format}")
            proc_config = processes_config[id_format].copy()
            
            # Handle element-specific positioning if element is specified
            if element:
                # Handle case sensitivity: material -> Material, but WC/DM/CC stay as-is
                if element.lower() == 'material':
                    element_name = 'Material'
                else:
                    element_name = element.upper()  # WC, DM, CC
                
                element_x_key = f'X_Position_{element_name}'
                element_y_key = f'Y_Position_{element_name}'
                
                # Check if element-specific positions exist and are not empty
                if (element_x_key in proc_config and element_y_key in proc_config and
                    proc_config[element_x_key] is not None and proc_config[element_y_key] is not None and
                    str(proc_config[element_x_key]).strip() != '' and str(proc_config[element_y_key]).strip() != '' and
                    str(proc_config[element_x_key]).strip() != '0,5' and str(proc_config[element_y_key]).strip() != '0,5'):
                    
                    # Use element-specific positions
                    proc_config['X_Position'] = proc_config[element_x_key]
                    proc_config['Y_Position'] = proc_config[element_y_key]
                    print(f"  -> Using element-specific positions for {element}: ({proc_config[element_x_key]}, {proc_config[element_y_key]})")
                else:
                    print(f"  -> No element-specific positions for {element}, using general positions")
            
            return proc_config
    
    # Try to find by process name
    for proc_id, proc_config in processes_config.items():
        if proc_config.get('Process_Name') == process_name:
            print(f"  -> Found process config by name: {process_name}")
            proc_config = proc_config.copy()
            
            # Handle element-specific positioning if element is specified
            if element:
                # Handle case sensitivity: material -> Material, but WC/DM/CC stay as-is
                if element.lower() == 'material':
                    element_name = 'Material'
                else:
                    element_name = element.upper()  # WC, DM, CC
                
                element_x_key = f'X_Position_{element_name}'
                element_y_key = f'Y_Position_{element_name}'
                
                # Check if element-specific positions exist and are not empty
                if (element_x_key in proc_config and element_y_key in proc_config and
                    proc_config[element_x_key] is not None and proc_config[element_y_key] is not None and
                    str(proc_config[element_x_key]).strip() != '' and str(proc_config[element_y_key]).strip() != '' and
                    str(proc_config[element_x_key]).strip() != '0,5' and str(proc_config[element_y_key]).strip() != '0,5'):
                    
                    # Use element-specific positions
                    proc_config['X_Position'] = proc_config[element_x_key]
                    proc_config['Y_Position'] = proc_config[element_y_key]
                    print(f"  -> Using element-specific positions for {element}: ({proc_config[element_x_key]}, {proc_config[element_y_key]})")
                else:
                    print(f"  -> No element-specific positions for {element}, using general positions")
            
            return proc_config
    
    # Return default settings
    return {
        'Node_Color': '#1f77b4',
        'Node_Color_#': '#1f77b4',  # Hex color code
        'Node_Size': 'Medium',
        'X_Position': '0,5',  # European decimal format
        'Y_Position': '0,5',  # European decimal format
        'Layout_Type': 'Auto'
    }

def get_flow_visualization(flow_id, flow_name, config):
    """
    Get visualization settings for a flow.
    
    Args:
        flow_id (str): Flow ID
        flow_name (str): Flow name
        config (dict): Visualization configuration
        
    Returns:
        dict: Flow visualization settings
    """
    # Try to find in config first (handle both 'flows' and 'flow_colors')
    flows_config = config.get('flow_colors', config.get('flows', {}))
    if flow_id in flows_config:
        return flows_config[flow_id]
    
    # Try to find by flow name
    for fid, flow_config in flows_config.items():
        if flow_config.get('Flow_Name') == flow_name:
            return flow_config
    
    # Return default settings
    return {
        'Flow_Color': '#1f77b4',
        'Flow_Color_#': '#1f77b4'  # Hex color code
    }

def plot_enhanced_sankey(mfa_system_results, dsm_params=None, fomp_params=None, 
                        visualization_config_path=None):
    """
    Enhanced interactive Sankey diagram with circular system support.
    
    This implementation addresses:
    - Dynamic value updates when switching between elements
    - Responsive window sizing
    - Proper node positioning that adapts to filtered flows
    - Layout type switching functionality
    """
    from ipywidgets import interactive
    
    # Load visualization configuration
    if visualization_config_path and os.path.exists(visualization_config_path):
        config = load_visualization_config(visualization_config_path)
    else:
        config = get_default_visualization_config()
        print("Using default visualization configuration")

    def get_process_type(process_id, dsm_params, fomp_params):
        """Determine process type for color coding."""
        if dsm_params and process_id in dsm_params:
            return 'DSM'
        elif fomp_params and process_id in fomp_params:
            return 'FOMP'
        else:
            return 'Regular'

    # --- DATA PREPARATION ---
    all_processes = mfa_system_results.ProcessList
    all_flows = list(mfa_system_results.FlowDict.values())
    time_items = mfa_system_results.IndexTable.Classification["Time"].Items
    element_items = mfa_system_results.Elements
    max_flow_value = max(f.Values.max() for f in all_flows if f.Values is not None) if all_flows else 1

    # --- FIGURE CREATION ---
    # Get zoom settings early for figure creation
    layout_settings = config.get('layout_settings', config.get('layout', {}))
    zoom_factor = float(layout_settings.get('Zoom_Factor', 1.0))
    node_scale_factor = float(layout_settings.get('Node_Scale_Factor', 1.0))
    flow_scale_factor = float(layout_settings.get('Flow_Scale_Factor', 1.0))
    
    # Apply zoom constraints
    min_zoom_factor = float(layout_settings.get('Min_Zoom_Factor', 0.3))
    max_zoom_factor = float(layout_settings.get('Max_Zoom_Factor', 3.0))
    zoom_factor = max(min_zoom_factor, min(zoom_factor, max_zoom_factor))
    
    # Calculate scaled dimensions
    scaled_pad = int(15 * zoom_factor * node_scale_factor)
    scaled_thickness = int(20 * zoom_factor * node_scale_factor)
    scaled_line_width = max(0.5, 0.5 * zoom_factor)
    
    # Create responsive figure with zoom-based sizing
    fig = go.FigureWidget(go.Sankey(
        node=dict(
            pad=scaled_pad, 
            thickness=scaled_thickness, 
            line=dict(color="black", width=scaled_line_width),
            label=[],
            x=[],
            y=[],
            color=[]
        ),
        link=dict(
            line=dict(color="black", width=scaled_line_width),
            source=[],
            target=[],
            value=[],
            color=[]
        )
    ))

    # --- EXCEL-BASED RESPONSIVE LAYOUT WITH ZOOM ---
    # Get window sizing and zoom configuration from Excel
    layout_settings = config.get('layout_settings', config.get('layout', {}))
    
    # Extract window dimensions from Excel
    window_width = int(layout_settings.get('Window_Width', 1200))
    window_height = int(layout_settings.get('Window_Height', 800))
    window_min_width = int(layout_settings.get('Window_Min_Width', 800))
    window_min_height = int(layout_settings.get('Window_Min_Height', 600))
    window_max_width = int(layout_settings.get('Window_Max_Width', 1600))
    window_max_height = int(layout_settings.get('Window_Max_Height', 1200))
    window_responsive = layout_settings.get('Window_Responsive', True)
    window_auto_size = layout_settings.get('Window_Auto_Size', True)
    
    # Extract zoom and scaling settings from Excel
    zoom_factor = float(layout_settings.get('Zoom_Factor', 1.0))
    node_scale_factor = float(layout_settings.get('Node_Scale_Factor', 1.0))
    flow_scale_factor = float(layout_settings.get('Flow_Scale_Factor', 1.0))
    auto_fit_frame = layout_settings.get('Auto_Fit_Frame', True)
    min_zoom_factor = float(layout_settings.get('Min_Zoom_Factor', 0.3))
    max_zoom_factor = float(layout_settings.get('Max_Zoom_Factor', 3.0))
    padding_factor = float(layout_settings.get('Padding_Factor', 0.1))
    center_diagram = layout_settings.get('Center_Diagram', True)
    
    # Apply zoom constraints
    zoom_factor = max(min_zoom_factor, min(zoom_factor, max_zoom_factor))
    
    # Apply constraints to window dimensions
    window_width = max(window_min_width, min(window_width, window_max_width))
    window_height = max(window_min_height, min(window_height, window_max_height))
    
    print(f"📐 Window sizing from Excel: {window_width}x{window_height} pixels")
    print(f"🔍 Zoom settings from Excel:")
    print(f"   - Zoom Factor: {zoom_factor} (range: {min_zoom_factor}-{max_zoom_factor})")
    print(f"   - Node Scale: {node_scale_factor}, Flow Scale: {flow_scale_factor}")
    print(f"   - Auto Fit Frame: {auto_fit_frame}, Center Diagram: {center_diagram}")
    print(f"   - Responsive: {window_responsive}, Auto-size: {window_auto_size}")
    
    # Calculate effective dimensions with zoom
    effective_width = int(window_width * zoom_factor)
    effective_height = int(window_height * zoom_factor)
    
    # Configure responsive layout with zoom
    layout_config = {
        'height': effective_height,
        'width': effective_width,
        'margin': dict(
            l=int(50 * zoom_factor), 
            r=int(50 * zoom_factor), 
            t=int(80 * zoom_factor), 
            b=int(50 * zoom_factor)
        ),
        'title': dict(
            text="Enhanced Sankey Diagram",
            font=dict(size=int(16 * zoom_factor)),
            x=0.5,
            xanchor='center'
        )
    }
    
    # Add responsive features based on Excel settings
    if window_responsive:
        layout_config['autosize'] = True
    if window_auto_size:
        layout_config['autosize'] = True
    
    fig.update_layout(**layout_config)

    # --- WIDGETS ---
    year_slider = IntSlider(
        min=time_items[0],
        max=time_items[-1],
        step=1,
        value=time_items[0],
        description="Year:",
        style={'description_width': 'initial'},
        layout=Layout(width='300px')
    )
    
    element_dropdown = Dropdown(
        options=element_items, 
        value=element_items[0], 
        description='Element:', 
        style={'description_width': 'initial'},
        layout=Layout(width='200px')
    )
    
    process_selector = SelectMultiple(
        options=[p.Name for p in all_processes], 
        value=[p.Name for p in all_processes], 
        description='Processes:', 
        style={'description_width': 'initial'},
        layout=Layout(width='400px', height='100px')
    )
    
    min_flow_slider = FloatSlider(
        value=0, 
        min=0, 
        max=max_flow_value, 
        step=max_flow_value / 100, 
        description='Min Flow:', 
        style={'description_width': 'initial'},
        layout=Layout(width='300px')
    )
    
    layout_dropdown = Dropdown(
        options=['Linear', 'Circular', 'Radial', 'Custom'], 
        value='Circular', 
        description='Layout:', 
        style={'description_width': 'initial'},
        layout=Layout(width='150px')
    )

    def calculate_dynamic_positions(processes_to_show, flows_to_show, layout_type, config, element=None):
        """
        Calculate node positions dynamically based on current selection and layout type.
        This fixes the positioning issues when switching between elements.
        Includes auto-fit frame functionality to ensure flows stay within bounds.
        Now supports element-specific positioning for different material levels.
        
        KEY FIX: Always use ALL processes for positioning to maintain consistent layouts
        across different elements, but only show flows for the selected processes.
        """
        if not processes_to_show:
            return {}, {}
        
        # Create process ID to index mapping for filtered processes (for flow display)
        filtered_processes = [p for p in all_processes if p.Name in processes_to_show]
        process_id_to_index = {p.ID: i for i, p in enumerate(filtered_processes)}
        
        # CRITICAL FIX: Always use ALL processes for positioning, not just filtered ones
        # This ensures consistent node positions across all elements
        if element:
            positions = calculate_element_specific_positions(all_processes, flows_to_show, config, element, layout_type)
        else:
            # Fallback to original logic if no element specified
            if layout_type == 'Circular':
                positions = calculate_circular_positions(all_processes, flows_to_show, config)
            elif layout_type == 'Radial':
                positions = calculate_radial_positions(all_processes, flows_to_show, config)
            elif layout_type == 'Custom':
                # Use custom positions from Excel configuration
                positions = {}
                for process in all_processes:
                    viz_settings = get_process_visualization(process.ID, process.Name, config)
                    custom_x = viz_settings.get('X_Position')
                    custom_y = viz_settings.get('Y_Position')
                    
                    if (custom_x is not None and custom_y is not None and 
                        str(custom_x).strip() != '' and str(custom_y).strip() != '' and
                        custom_x != '0,5' and custom_y != '0,5'):  # Check for meaningful values
                        try:
                            x = float(str(custom_x).replace(',', '.'))
                            y = float(str(custom_y).replace(',', '.'))
                            positions[process.ID] = (x, y)
                        except (ValueError, TypeError):
                            positions[process.ID] = (0.5, 0.5)
                    else:
                        positions[process.ID] = (0.5, 0.5)
            else:  # Linear layout
                positions = {}
                for i, process in enumerate(all_processes):
                    x = 0.1 + (i / max(1, len(all_processes) - 1)) * 0.8
                    y = 0.5
                    positions[process.ID] = (x, y)
        
        # Auto-fit frame functionality
        if auto_fit_frame and positions:
            # Calculate bounding box of all positions
            x_values = [pos[0] for pos in positions.values()]
            y_values = [pos[1] for pos in positions.values()]
            
            min_x, max_x = min(x_values), max(x_values)
            min_y, max_y = min(y_values), max(y_values)
            
            # Calculate current span
            span_x = max_x - min_x
            span_y = max_y - min_y
            
            # Add padding
            padding = padding_factor
            target_min_x = padding
            target_max_x = 1.0 - padding
            target_min_y = padding
            target_max_y = 1.0 - padding
            target_span_x = target_max_x - target_min_x
            target_span_y = target_max_y - target_min_y
            
            # Calculate scale factors
            scale_x = target_span_x / max(span_x, 0.1)  # Avoid division by zero
            scale_y = target_span_y / max(span_y, 0.1)
            scale = min(scale_x, scale_y)  # Use the more restrictive scale
            
            # Apply scaling and centering
            center_x = (min_x + max_x) / 2
            center_y = (min_y + max_y) / 2
            target_center_x = (target_min_x + target_max_x) / 2
            target_center_y = (target_min_y + target_max_y) / 2
            
            for process_id in positions:
                x, y = positions[process_id]
                # Scale around center
                new_x = target_center_x + (x - center_x) * scale
                new_y = target_center_y + (y - center_y) * scale
                positions[process_id] = (new_x, new_y)
        
        # Convert to arrays for Plotly - only for the processes that will be displayed
        node_x = []
        node_y = []
        for process in filtered_processes:
            x, y = positions.get(process.ID, (0.5, 0.5))
            node_x.append(x)
            node_y.append(y)
        
        return node_x, node_y, process_id_to_index

    def update_sankey(year, element, processes_to_show, min_flow_value, layout_type):
        """
        Update the Sankey diagram with proper dynamic behavior.
        This fixes the dynamic values and positioning issues.
        """
        if not processes_to_show:
            with fig.batch_update():
                fig.data[0].node.label = []
                fig.data[0].node.x = []
                fig.data[0].node.y = []
                fig.data[0].node.color = []
                fig.data[0].link.source = []
                fig.data[0].link.target = []
                fig.data[0].link.value = []
                fig.data[0].link.color = []
            return

        # Convert year and element to indices (exactly like traditional Sankey)
        year_index = time_items.index(year)
        element_index = element_items.index(element)
        
        # Flow values are now properly extracted and updated

        # Filter flows based on current selection (simplified like traditional Sankey)
        filtered_processes = [p for p in all_processes if p.Name in processes_to_show]
        process_id_to_index = {p.ID: i for i, p in enumerate(filtered_processes)}
        
        # Get candidate flows first
        candidate_flows = [
            f for f in all_flows if f.P_Start in process_id_to_index and f.P_End in process_id_to_index
        ]
        
        # Filter flows based on threshold
        final_flows = [
            f for f in candidate_flows
            if f.Values[year_index, element_index] >= min_flow_value
        ]

        # Calculate dynamic positions with element-specific support
        node_x, node_y, _ = calculate_dynamic_positions(processes_to_show, final_flows, layout_type, config, element)

        # Calculate node colors
        node_colors = []
        for process in filtered_processes:
            viz_settings = get_process_visualization(process.ID, process.Name, config)
            if viz_settings.get('Node_Color_#') and viz_settings.get('Node_Color_#').strip():
                node_colors.append(viz_settings['Node_Color_#'])
            elif viz_settings.get('Node_Color') and viz_settings.get('Node_Color').strip():
                node_colors.append(viz_settings['Node_Color'])
            else:
                process_type = get_process_type(process.ID, dsm_params, fomp_params)
                color_map = {'Regular': '#1f77b4', 'DSM': '#ff7f0e', 'FOMP': '#2ca02c'}
                node_colors.append(color_map.get(process_type, '#1f77b4'))

        # Update the figure with proper dynamic behavior
        with fig.batch_update():
            # Update nodes
            fig.data[0].node.label = [p.Name for p in filtered_processes]
            fig.data[0].node.x = node_x
            fig.data[0].node.y = node_y
            fig.data[0].node.color = node_colors

            if not final_flows:
                # No flows to show
                fig.data[0].link.source = []
                fig.data[0].link.target = []
                fig.data[0].link.value = []
                fig.data[0].link.color = []
            else:
                # Update flows with dynamic values
                flow_values = [f.Values[year_index, element_index] for f in final_flows]
                flow_sources = [process_id_to_index[f.P_Start] for f in final_flows]
                flow_targets = [process_id_to_index[f.P_End] for f in final_flows]
                
                # Flow values are dynamically calculated for the selected year and element
                
                # Calculate flow colors
                flow_colors = []
                for flow in final_flows:
                    flow_viz = get_flow_visualization(flow.Name, flow.Name, config)
                    if flow_viz.get('Flow_Color_#'):
                        flow_colors.append(flow_viz['Flow_Color_#'])
                    elif flow_viz.get('Flow_Color'):
                        flow_colors.append(flow_viz['Flow_Color'])
                    else:
                        elements_config = config.get('element_colors', config.get('elements', {}))
                        flow_colors.append(elements_config.get(element, {}).get('Color', '#1f77b4'))

                # Update links with dynamic values (like traditional Sankey)
                fig.data[0].link.source = flow_sources
                fig.data[0].link.target = flow_targets
                fig.data[0].link.value = flow_values  # This should now update dynamically
                fig.data[0].link.color = flow_colors

            # Update title with dynamic information
            total_flow = sum(flow_values) if final_flows else 0
            fig.update_layout(
                title_text=f"Sankey Diagram - {element} ({year}) - Total Flow: {total_flow:.1f} t",
                font_size=14
            )

    # Create interactive widget
    interactive_widget = interactive(
        update_sankey, 
        year=year_slider, 
        element=element_dropdown, 
        processes_to_show=process_selector, 
        min_flow_value=min_flow_slider, 
        layout_type=layout_dropdown
    )

    # Create export button
    def export_sankey(b):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sankey_enhanced_{timestamp}.png"
        filepath = os.path.join("exports", filename)
        
        # Ensure exports directory exists
        os.makedirs("exports", exist_ok=True)
        
        # Export with Excel-based dimensions, zoom, and high quality
        export_width = effective_width
        export_height = effective_height
        export_scale = max(1, int(2 * zoom_factor))  # Scale based on zoom factor
        fig.write_image(filepath, width=export_width, height=export_height, scale=export_scale)
        print(f"✅ Sankey diagram exported to: {filepath}")
        print(f"   - Export size: {export_width}x{export_height} pixels (with zoom factor {zoom_factor})")
        print(f"   - Export scale: {export_scale}x for high quality")

    export_button = Button(description="Export PNG", button_style='success')
    export_button.on_click(export_sankey)

    # Create responsive layout with better organization
    controls = VBox([
        HBox([year_slider, element_dropdown], layout=Layout(width='100%')),
        HBox([process_selector, min_flow_slider], layout=Layout(width='100%')),
        HBox([layout_dropdown, export_button], layout=Layout(width='100%'))
    ], layout=Layout(width='100%', padding='10px'))

    # Display the interactive widget
    display(VBox([controls, fig]))
    
    # Initial update with proper initialization
    update_sankey(
        year_slider.value,
        element_dropdown.value,
        process_selector.value,
        min_flow_slider.value,
        layout_dropdown.value
    )
