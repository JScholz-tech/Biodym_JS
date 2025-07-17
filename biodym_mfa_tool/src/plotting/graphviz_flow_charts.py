# -*- coding: utf-8 -*-
"""
Graphviz Flow Chart Plotting Module.

This module provides professional engineering flow charts using Graphviz
for better automatic layout of complex systems.
"""

import pandas as pd
import graphviz
import os
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
import numpy as np


def plot_graphviz_flow_chart(excel_file_path, title="BioDYM System Flow Chart", 
                            layout_engine="dot", rankdir="LR", figsize=(16, 12)):
    """
    Create a professional engineering flow chart using Graphviz.
    
    Args:
        excel_file_path (str): Path to the Excel file
        title (str): Chart title
        layout_engine (str): Graphviz layout engine ('dot', 'neato', 'fdp', 'sfdp')
        rankdir (str): Direction ('LR', 'TB', 'RL', 'BT')
        figsize (tuple): Figure size for matplotlib rendering
        
    Returns:
        graphviz.Digraph: Graphviz diagram object
    """
    try:
        # Read Excel data
        flows_df = pd.read_excel(excel_file_path, sheet_name='1_1_Definition_Flows')
        processes_df = pd.read_excel(excel_file_path, sheet_name='2_1_Definition_Processes')
        
        # Drop rows with missing IDs or names
        processes_df = processes_df.dropna(subset=['ID', 'Name(EN)'])
        flows_df = flows_df.dropna(subset=['Flow_ID', 'Name(EN)', 'Process_ID_O', 'Process_ID_I'])
        
        # Create Graphviz digraph
        dot = graphviz.Digraph(comment=title)
        dot.attr(rankdir=rankdir)
        dot.attr('node', shape='box', style='rounded,filled', fontname='Arial', fontsize='10')
        dot.attr('edge', fontname='Arial', fontsize='8')
        
        # Add processes as nodes
        for _, process in processes_df.iterrows():
            process_id = process['ID']
            process_name = process['Name(EN)']
            
            # Scalar-safe checks
            if (isinstance(process_id, float) and pd.isna(process_id)) or (isinstance(process_name, float) and pd.isna(process_name)) or str(process_name).strip() == '':
                continue
                
            process_name = str(process_name)
            is_stock = process.get('Stock?', False)
            is_initial_stock = process.get('Initial_Stock?', False)
            
            # Create node label
            node_label = f"{process_id}: {process_name}"
            
            # Set node attributes based on type
            if is_initial_stock:
                dot.node(str(process_id), node_label, 
                        fillcolor='#ffcccc', color='#cc0000', 
                        shape='box', style='filled,rounded')
            elif is_stock:
                dot.node(str(process_id), node_label, 
                        fillcolor='#ffeedd', color='#ff6600', 
                        shape='box', style='filled,rounded')
            else:
                dot.node(str(process_id), node_label, 
                        fillcolor='#e6f3ff', color='#0066cc', 
                        shape='box', style='filled,rounded')
        
        # Add flows as edges
        for _, flow in flows_df.iterrows():
            flow_id = flow['Flow_ID']
            flow_name = flow['Name(EN)']
            process_o = flow['Process_ID_O']
            process_i = flow['Process_ID_I']
            
            if ((isinstance(flow_id, float) and pd.isna(flow_id)) or
                (isinstance(flow_name, float) and pd.isna(flow_name)) or str(flow_name).strip() == '' or
                (isinstance(process_o, float) and pd.isna(process_o)) or
                (isinstance(process_i, float) and pd.isna(process_i))):
                continue
                
            flow_name = str(flow_name)
            edge_label = f"{flow_id}: {flow_name}"
            
            # Only add edge if both nodes exist
            if str(process_o) in [node.name for node in dot.body if node.startswith('node')] and \
               str(process_i) in [node.name for node in dot.body if node.startswith('node')]:
                dot.edge(str(process_o), str(process_i), label=edge_label)
        
        return dot
        
    except Exception as e:
        print(f"Error creating Graphviz flow chart: {e}")
        return None


def plot_graphviz_flow_chart_enhanced(excel_file_path, title="BioDYM System Flow Chart", 
                                     layout_engine="dot", rankdir="LR", 
                                     node_shape="box", show_flow_values=True):
    """
    Create an enhanced Graphviz flow chart with more customization options.
    
    Args:
        excel_file_path (str): Path to the Excel file
        title (str): Chart title
        layout_engine (str): Graphviz layout engine
        rankdir (str): Direction ('LR', 'TB', 'RL', 'BT')
        node_shape (str): Node shape ('box', 'ellipse', 'diamond', 'hexagon')
        show_flow_values (bool): Whether to show flow values on edges
        
    Returns:
        graphviz.Digraph: Graphviz diagram object
    """
    try:
        # Read Excel data
        flows_df = pd.read_excel(excel_file_path, sheet_name='1_1_Definition_Flows')
        processes_df = pd.read_excel(excel_file_path, sheet_name='2_1_Definition_Processes')
        
        # Drop rows with missing IDs or names
        processes_df = processes_df.dropna(subset=['ID', 'Name(EN)'])
        flows_df = flows_df.dropna(subset=['Flow_ID', 'Name(EN)', 'Process_ID_O', 'Process_ID_I'])
        
        # Create Graphviz digraph with enhanced styling
        dot = graphviz.Digraph(comment=title)
        dot.attr(rankdir=rankdir)
        dot.attr('node', shape=node_shape, style='filled,rounded', 
                fontname='Arial', fontsize='9', margin='0.2')
        dot.attr('edge', fontname='Arial', fontsize='7', 
                arrowsize='0.8', penwidth='1.5')
        
        # Define color schemes
        colors = {
            'input': {'fill': '#e6f7ff', 'border': '#0066cc'},
            'treatment': {'fill': '#f0f8ff', 'border': '#0066cc'},
            'use': {'fill': '#f0fff0', 'border': '#006600'},
            'output': {'fill': '#fff0f0', 'border': '#cc0000'},
            'default': {'fill': '#f5f5f5', 'border': '#666666'}  # Gray for all other processes (including stocks)
        }
        
        # Add processes as nodes with enhanced categorization
        for _, process in processes_df.iterrows():
            process_id = process['ID']
            process_name = process['Name(EN)']
            
            # Scalar-safe checks
            if (isinstance(process_id, float) and pd.isna(process_id)) or (isinstance(process_name, float) and pd.isna(process_name)) or str(process_name).strip() == '':
                continue
                
            process_name = str(process_name)
            is_stock = process.get('Stock?', False)
            is_initial_stock = process.get('Initial_Stock?', False)
            
            # Determine process category - move stock processes to default (gray)
            name_lower = process_name.lower()
            if any(keyword in name_lower for keyword in ['input', 'import', 'source']):
                category = 'input'
            elif any(keyword in name_lower for keyword in ['treatment', 'process', 'convert']):
                category = 'treatment'
            elif any(keyword in name_lower for keyword in ['use', 'consume', 'apply']):
                category = 'use'
            elif any(keyword in name_lower for keyword in ['output', 'export', 'sink']):
                category = 'output'
            else:
                # All other processes (including stocks) go to default (gray)
                category = 'default'
            
            # Create node label
            node_label = f"{process_id}: {process_name}"
            
            # Set node attributes
            color_scheme = colors[category]
            dot.node(str(process_id), node_label, 
                    fillcolor=color_scheme['fill'], 
                    color=color_scheme['border'])
        
        # Add flows as edges
        for _, flow in flows_df.iterrows():
            flow_id = flow['Flow_ID']
            flow_name = flow['Name(EN)']
            process_o = flow['Process_ID_O']
            process_i = flow['Process_ID_I']
            
            if ((isinstance(flow_id, float) and pd.isna(flow_id)) or
                (isinstance(flow_name, float) and pd.isna(flow_name)) or str(flow_name).strip() == '' or
                (isinstance(process_o, float) and pd.isna(process_o)) or
                (isinstance(process_i, float) and pd.isna(process_i))):
                continue
                
            flow_name = str(flow_name)
            
            # Create edge label
            if show_flow_values:
                edge_label = f"{flow_id}: {flow_name}"
            else:
                edge_label = flow_name
            
            # Add edge
            dot.edge(str(process_o), str(process_i), label=edge_label)
        
        return dot
        
    except Exception as e:
        print(f"Error creating enhanced Graphviz flow chart: {e}")
        return None


def plot_graphviz_flow_chart_minimalist(excel_file_path, title="BioDYM System Flow Chart", 
                                       rankdir="LR", ranksep=1.0, nodesep=0.5):
    """
    Create a professional, minimalist black-and-white block flow diagram.
    
    Args:
        excel_file_path (str): Path to the Excel file
        title (str): Chart title
        rankdir (str): Direction ('LR', 'TB', 'RL', 'BT')
        ranksep (float): Separation between ranks
        nodesep (float): Separation between nodes
        
    Returns:
        graphviz.Digraph: Graphviz diagram object
    """
    try:
        # Read Excel data
        flows_df = pd.read_excel(excel_file_path, sheet_name='1_1_Definition_Flows')
        processes_df = pd.read_excel(excel_file_path, sheet_name='2_1_Definition_Processes')
        
        # Drop rows with missing IDs or names
        processes_df = processes_df.dropna(subset=['ID', 'Name(EN)'])
        flows_df = flows_df.dropna(subset=['Flow_ID', 'Name(EN)', 'Process_ID_O', 'Process_ID_I'])
        
        # Create Graphviz digraph with minimalist styling
        dot = graphviz.Digraph(comment=title)
        dot.attr(rankdir=rankdir, ranksep=str(ranksep), nodesep=str(nodesep))
        dot.attr(label=title, labelloc="t", fontname="Arial", fontsize="14")
        
        # Set global node and edge attributes for minimalist style
        dot.attr('node', 
                shape='box', 
                style='filled', 
                fillcolor='white', 
                color='black', 
                fontcolor='black',
                fontname='Arial', 
                fontsize='10',
                margin='0.2')
        dot.attr('edge', 
                color='black',
                fontcolor='black',
                fontname='Arial', 
                fontsize='8',
                arrowsize='0.8',
                penwidth='1.0',
                splines='ortho')
        
        # Add processes as nodes (all uniform)
        for _, process in processes_df.iterrows():
            process_id = process['ID']
            process_name = process['Name(EN)']
            
            # Scalar-safe checks
            if (isinstance(process_id, float) and pd.isna(process_id)) or (isinstance(process_name, float) and pd.isna(process_name)) or str(process_name).strip() == '':
                continue
                
            process_name = str(process_name)
            
            # Create node label
            node_label = f"{process_id}: {process_name}"
            
            # All nodes have uniform appearance
            dot.node(str(process_id), node_label)
        
        # Add flows as edges
        for _, flow in flows_df.iterrows():
            flow_id = flow['Flow_ID']
            flow_name = flow['Name(EN)']
            process_o = flow['Process_ID_O']
            process_i = flow['Process_ID_I']
            
            if ((isinstance(flow_id, float) and pd.isna(flow_id)) or
                (isinstance(flow_name, float) and pd.isna(flow_name)) or str(flow_name).strip() == '' or
                (isinstance(process_o, float) and pd.isna(process_o)) or
                (isinstance(process_i, float) and pd.isna(process_i))):
                continue
                
            flow_name = str(flow_name)
            edge_label = f"{flow_id}: {flow_name}"
            
            # Add edge with orthogonal routing
            dot.edge(str(process_o), str(process_i), label=edge_label)
        
        return dot
        
    except Exception as e:
        print(f"Error creating minimalist Graphviz flow chart: {e}")
        return None


def generate_dot_code_minimalist(excel_file_path, title="BioDYM System Flow Chart", 
                                rankdir="LR", ranksep=1.0, nodesep=0.5):
    """
    Generate the complete DOT language code for a minimalist flow chart.
    
    Args:
        excel_file_path (str): Path to the Excel file
        title (str): Chart title
        rankdir (str): Direction ('LR', 'TB', 'RL', 'BT')
        ranksep (float): Separation between ranks
        nodesep (float): Separation between nodes
        
    Returns:
        str: Complete DOT language code
    """
    try:
        # Read Excel data
        flows_df = pd.read_excel(excel_file_path, sheet_name='1_1_Definition_Flows')
        processes_df = pd.read_excel(excel_file_path, sheet_name='2_1_Definition_Processes')
        
        # Drop rows with missing IDs or names
        processes_df = processes_df.dropna(subset=['ID', 'Name(EN)'])
        flows_df = flows_df.dropna(subset=['Flow_ID', 'Name(EN)', 'Process_ID_O', 'Process_ID_I'])
        
        # Build DOT code manually for complete control
        dot_code = []
        dot_code.append(f'digraph G {{')
        dot_code.append(f'  // Graph attributes')
        dot_code.append(f'  rankdir={rankdir};')
        dot_code.append(f'  ranksep={ranksep};')
        dot_code.append(f'  nodesep={nodesep};')
        dot_code.append(f'  label="{title}";')
        dot_code.append(f'  labelloc="t";')
        dot_code.append(f'  fontname="Arial";')
        dot_code.append(f'  fontsize=14;')
        dot_code.append(f'')
        dot_code.append(f'  // Node attributes')
        dot_code.append(f'  node [shape=box, style=filled, fillcolor=white, color=black, fontcolor=black, fontname="Arial", fontsize=10, margin=0.2];')
        dot_code.append(f'')
        dot_code.append(f'  // Edge attributes')
        dot_code.append(f'  edge [color=black, fontcolor=black, fontname="Arial", fontsize=8, arrowsize=0.8, penwidth=1.0, splines=ortho];')
        dot_code.append(f'')
        dot_code.append(f'  // Nodes')
        
        # Add nodes
        for _, process in processes_df.iterrows():
            process_id = process['ID']
            process_name = process['Name(EN)']
            
            # Scalar-safe checks
            if (isinstance(process_id, float) and pd.isna(process_id)) or (isinstance(process_name, float) and pd.isna(process_name)) or str(process_name).strip() == '':
                continue
                
            process_name = str(process_name)
            node_label = f"{process_id}: {process_name}"
            dot_code.append(f'  "{process_id}" [label="{node_label}"];')
        
        dot_code.append(f'')
        dot_code.append(f'  // Edges')
        
        # Add edges
        for _, flow in flows_df.iterrows():
            flow_id = flow['Flow_ID']
            flow_name = flow['Name(EN)']
            process_o = flow['Process_ID_O']
            process_i = flow['Process_ID_I']
            
            if ((isinstance(flow_id, float) and pd.isna(flow_id)) or
                (isinstance(flow_name, float) and pd.isna(flow_name)) or str(flow_name).strip() == '' or
                (isinstance(process_o, float) and pd.isna(process_o)) or
                (isinstance(process_i, float) and pd.isna(process_i))):
                continue
                
            flow_name = str(flow_name)
            edge_label = f"{flow_id}: {flow_name}"
            dot_code.append(f'  "{process_o}" -> "{process_i}" [label="{edge_label}"];')
        
        dot_code.append(f'}}')
        
        return '\n'.join(dot_code)
        
    except Exception as e:
        print(f"Error generating DOT code: {e}")
        return None


def export_graphviz_chart(dot, filename_prefix="flow_chart", export_formats=None):
    """
    Export Graphviz chart to various formats.
    
    Args:
        dot (graphviz.Digraph): Graphviz diagram object
        filename_prefix (str): Prefix for exported files
        export_formats (list): List of formats to export ('png', 'pdf', 'svg', 'dot')
        
    Returns:
        list: List of exported file paths
    """
    if export_formats is None:
        export_formats = ['png', 'pdf', 'svg']
    
    exported_files = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create export directory
    export_dir = "exports/flow_charts"
    os.makedirs(export_dir, exist_ok=True)
    
    for format_type in export_formats:
        try:
            filename = f"{filename_prefix}_{timestamp}.{format_type}"
            filepath = os.path.join(export_dir, filename)
            
            if format_type == 'dot':
                # Export as DOT source
                with open(filepath, 'w') as f:
                    f.write(dot.source)
            else:
                # Render and export
                dot.render(filepath, format=format_type, cleanup=True)
            
            exported_files.append(filepath)
            print(f"✅ Exported as {format_type.upper()}: {filepath}")
            
        except Exception as e:
            print(f"❌ Failed to export {format_type}: {e}")
    
    return exported_files


def create_graphviz_flow_chart_demo(excel_file_path):
    """
    Create a demonstration of different Graphviz layout options.
    
    Args:
        excel_file_path (str): Path to the Excel file
        
    Returns:
        dict: Dictionary of different layout options
    """
    layouts = {
        'dot_lr': {'layout_engine': 'dot', 'rankdir': 'LR', 'description': 'Hierarchical Left-to-Right'},
        'dot_tb': {'layout_engine': 'dot', 'rankdir': 'TB', 'description': 'Hierarchical Top-to-Bottom'},
        'neato': {'layout_engine': 'neato', 'rankdir': 'LR', 'description': 'Force-directed Layout'},
        'fdp': {'layout_engine': 'fdp', 'rankdir': 'LR', 'description': 'Force-directed with Ports'},
        'sfdp': {'layout_engine': 'sfdp', 'rankdir': 'LR', 'description': 'Scalable Force-directed'}
    }
    
    results = {}
    
    for name, config in layouts.items():
        print(f"Creating {config['description']}...")
        try:
            dot = plot_graphviz_flow_chart(
                excel_file_path,
                title=f"BioDYM System - {config['description']}",
                layout_engine=config['layout_engine'],
                rankdir=config['rankdir']
            )
            
            if dot is not None:
                results[name] = {
                    'dot': dot,
                    'config': config,
                    'description': config['description']
                }
                print(f"✅ {config['description']} created successfully")
            else:
                print(f"❌ Failed to create {config['description']}")
                
        except Exception as e:
            print(f"❌ Error creating {config['description']}: {e}")
    
    return results


def compare_graphviz_layouts(excel_file_path):
    """
    Compare different Graphviz layout engines and export all options.
    
    Args:
        excel_file_path (str): Path to the Excel file
    """
    print("🔄 Comparing Graphviz layout engines...")
    print("=" * 60)
    
    layouts = create_graphviz_flow_chart_demo(excel_file_path)
    
    print(f"\n📊 Created {len(layouts)} different layouts:")
    for name, result in layouts.items():
        print(f"   • {result['description']} ({name})")
    
    # Export all layouts
    print(f"\n📁 Exporting all layouts...")
    for name, result in layouts.items():
        dot = result['dot']
        export_graphviz_chart(dot, f"flow_chart_{name}", ['png', 'pdf'])
    
    print(f"\n🎉 Layout comparison completed!")
    print(f"📁 Check the 'exports/flow_charts/' directory for all exported files")
    
    return layouts 


def plot_graphviz_flow_chart_sankey_style(excel_file_path, title="BioDYM System - Sankey-Style Block Flow Diagram", 
                                         rankdir="LR", ranksep=1.0, nodesep=0.5):
    """
    Create a clean, professional Sankey-style block flow diagram using Graphviz.
    
    This function creates a minimalist, engineering-standard flow chart that mimics
    Sankey diagram principles with clean, orthogonal edges and uniform nodes.
    
    Args:
        excel_file_path (str): Path to the Excel file
        title (str): Chart title
        rankdir (str): Direction ('LR', 'TB', 'RL', 'BT')
        ranksep (float): Separation between ranks
        nodesep (float): Separation between nodes
        
    Returns:
        graphviz.Digraph: Graphviz diagram object
    """
    try:
        # Read Excel data
        flows_df = pd.read_excel(excel_file_path, sheet_name='1_1_Definition_Flows')
        processes_df = pd.read_excel(excel_file_path, sheet_name='2_1_Definition_Processes')
        
        # Drop rows with missing IDs or names
        processes_df = processes_df.dropna(subset=['ID', 'Name(EN)'])
        flows_df = flows_df.dropna(subset=['Flow_ID', 'Name(EN)', 'Process_ID_O', 'Process_ID_I'])
        
        # Create Graphviz digraph with clean, professional styling
        dot = graphviz.Digraph(comment=title)
        dot.attr(rankdir=rankdir, ranksep=str(ranksep), nodesep=str(nodesep))
        dot.attr(label=title, labelloc="t", fontname="Arial", fontsize="14")
        
        # Set global node and edge attributes for clean, professional style
        dot.attr('node', 
                shape='box', 
                style='filled', 
                fillcolor='white', 
                color='black', 
                fontcolor='black',
                fontname='Arial', 
                fontsize='10',
                margin='0.2')
        dot.attr('edge', 
                color='black',
                fontcolor='black',
                fontname='Arial', 
                fontsize='8',
                arrowsize='0.8',
                penwidth='1.0',
                splines='ortho')
        
        # Add processes as nodes with uniform appearance
        for _, process in processes_df.iterrows():
            process_id = process['ID']
            process_name = process['Name(EN)']
            
            # Scalar-safe checks
            if (isinstance(process_id, float) and pd.isna(process_id)) or (isinstance(process_name, float) and pd.isna(process_name)) or str(process_name).strip() == '':
                continue
                
            process_name = str(process_name)
            
            # Create node label
            node_label = f"{process_id}: {process_name}"
            
            # All nodes have uniform appearance (clean, professional)
            dot.node(str(process_id), node_label)
        
        # Add flows as edges
        for _, flow in flows_df.iterrows():
            flow_id = flow['Flow_ID']
            flow_name = flow['Name(EN)']
            process_o = flow['Process_ID_O']
            process_i = flow['Process_ID_I']
            
            if ((isinstance(flow_id, float) and pd.isna(flow_id)) or
                (isinstance(flow_name, float) and pd.isna(flow_name)) or str(flow_name).strip() == '' or
                (isinstance(process_o, float) and pd.isna(process_o)) or
                (isinstance(process_i, float) and pd.isna(process_i))):
                continue
                
            flow_name = str(flow_name)
            edge_label = f"{flow_id}: {flow_name}"
            
            # Add edge with orthogonal routing for clean appearance
            dot.edge(str(process_o), str(process_i), label=edge_label)
        
        return dot
        
    except Exception as e:
        print(f"Error creating Sankey-style Graphviz flow chart: {e}")
        return None


def plot_graphviz_flow_chart_force_directed(excel_file_path, title="BioDYM System Flow Chart", 
                                           layout_engine="neato", rankdir="LR"):
    """
    Create a Graphviz flow chart using force-directed layout similar to Sankey.
    
    Args:
        excel_file_path (str): Path to the Excel file
        title (str): Chart title
        layout_engine (str): Force-directed layout engine ('neato', 'fdp', 'sfdp')
        rankdir (str): Direction ('LR', 'TB', 'RL', 'BT')
        
    Returns:
        graphviz.Digraph: Graphviz diagram object
    """
    try:
        # Read Excel data
        flows_df = pd.read_excel(excel_file_path, sheet_name='1_1_Definition_Flows')
        processes_df = pd.read_excel(excel_file_path, sheet_name='2_1_Definition_Processes')
        
        # Drop rows with missing IDs or names
        processes_df = processes_df.dropna(subset=['ID', 'Name(EN)'])
        flows_df = flows_df.dropna(subset=['Flow_ID', 'Name(EN)', 'Process_ID_O', 'Process_ID_I'])
        
        # Create Graphviz digraph with force-directed layout
        dot = graphviz.Digraph(comment=title)
        dot.attr(rankdir=rankdir)
        dot.attr(label=title, labelloc="t", fontname="Arial", fontsize="14")
        
        # Set global node and edge attributes
        dot.attr('node', 
                shape='box', 
                style='filled', 
                fillcolor='white', 
                color='black', 
                fontcolor='black',
                fontname='Arial', 
                fontsize='10',
                margin='0.2')
        dot.attr('edge', 
                color='black',
                fontcolor='black',
                fontname='Arial', 
                fontsize='8',
                arrowsize='0.8',
                penwidth='1.0')
        
        # Add processes as nodes
        for _, process in processes_df.iterrows():
            process_id = process['ID']
            process_name = process['Name(EN)']
            
            if (isinstance(process_id, float) and pd.isna(process_id)) or (isinstance(process_name, float) and pd.isna(process_name)) or str(process_name).strip() == '':
                continue
                
            process_name = str(process_name)
            node_label = f"{process_id}: {process_name}"
            dot.node(str(process_id), node_label)
        
        # Add flows as edges
        for _, flow in flows_df.iterrows():
            flow_id = flow['Flow_ID']
            flow_name = flow['Name(EN)']
            process_o = flow['Process_ID_O']
            process_i = flow['Process_ID_I']
            
            if ((isinstance(flow_id, float) and pd.isna(flow_id)) or
                (isinstance(flow_name, float) and pd.isna(flow_name)) or str(flow_name).strip() == '' or
                (isinstance(process_o, float) and pd.isna(process_o)) or
                (isinstance(process_i, float) and pd.isna(process_i))):
                continue
                
            flow_name = str(flow_name)
            edge_label = f"{flow_id}: {flow_name}"
            
            # Add edge with weight (using flow ID as proxy)
            flow_id_str = str(flow_id)
            weight = float(flow_id_str.split('_')[-1]) if '_' in flow_id_str else 1.0
            dot.edge(str(process_o), str(process_i), label=edge_label, weight=str(weight))
        
        return dot
        
    except Exception as e:
        print(f"Error creating force-directed Graphviz flow chart: {e}")
        return None 