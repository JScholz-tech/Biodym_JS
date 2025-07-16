# -*- coding: utf-8 -*-
"""
Flow Chart Plotting Module.

This file contains functions for generating simple, engineering-standard flow charts
based on Excel data before any calculations are performed.
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from ipywidgets import Button, HBox, VBox, HTML, Layout, Dropdown
from IPython.display import display
import os
from datetime import datetime
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import numpy as np


def plot_simple_flow_chart_from_excel(excel_file_path, title="System Flow Chart", 
                                     layout_type="left_to_right", figsize=(16, 10),
                                     show_flow_values=True, show_stocks=True):
    """
    Create a simple, engineering-standard flow chart from Excel data.
    
    Args:
        excel_file_path (str): Path to the Excel file
        title (str): Chart title
        layout_type (str): Layout type ('left_to_right', 'hierarchical')
        figsize (tuple): Figure size (width, height)
        show_flow_values (bool): Whether to show flow values on arrows
        show_stocks (bool): Whether to highlight stock processes
        
    Returns:
        tuple: (matplotlib figure, networkx graph)
    """
    try:
        # Read Excel data
        flows_df = pd.read_excel(excel_file_path, sheet_name='1_1_Definition_Flows')
        processes_df = pd.read_excel(excel_file_path, sheet_name='2_1_Definition_Processes')
        
        # Drop rows with missing IDs or names
        processes_df = processes_df.dropna(subset=['ID', 'Name(EN)'])
        flows_df = flows_df.dropna(subset=['Flow_ID', 'Name(EN)', 'Process_ID_O', 'Process_ID_I'])
        
        # Create NetworkX graph
        G = nx.DiGraph()
        
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
            
            # Create node label with ID and name
            node_label = f"{process_id}: {process_name}"
            
            # Add node with attributes
            G.add_node(process_id, 
                      name=process_name,
                      label=node_label,
                      is_stock=is_stock,
                      is_initial_stock=is_initial_stock)
        
        # Add flows as edges
        for _, flow in flows_df.iterrows():
            flow_id = flow['Flow_ID']
            flow_name = flow['Name(EN)']
            process_o = flow['Process_ID_O']  # Output process
            process_i = flow['Process_ID_I']  # Input process
            
            # Create edge label with flow ID and name
            edge_label = f"{flow_id}: {flow_name}"
            
            # Add edge with attributes
            if process_o in G.nodes and process_i in G.nodes:
                G.add_edge(process_o, process_i, 
                          flow_id=flow_id,
                          flow_name=flow_name,
                          label=edge_label)
        
        # Create matplotlib figure
        fig, ax = plt.subplots(figsize=figsize)
        
        # Set layout
        if layout_type == "left_to_right":
            pos = nx.spring_layout(G, k=3, iterations=50)
            # Adjust positions for left-to-right flow
            for node in pos:
                pos[node] = (pos[node][0] * 2, pos[node][1])
        else:
            pos = nx.spring_layout(G, k=3, iterations=50)
        
        # Draw nodes (processes)
        node_colors = []
        node_shapes = []
        
        for node in G.nodes():
            node_data = G.nodes[node]
            if node_data.get('is_stock', False):
                node_colors.append('#ff7f0e')  # Orange for stocks
                node_shapes.append('s')  # Square for stocks
            elif node_data.get('is_initial_stock', False):
                node_colors.append('#d62728')  # Red for initial stocks
                node_shapes.append('s')
            else:
                node_colors.append('#1f77b4')  # Blue for regular processes
                node_shapes.append('o')  # Circle for regular processes
        
        # Draw nodes with different shapes
        for i, (node, (x, y)) in enumerate(pos.items()):
            node_data = G.nodes[node]
            color = node_colors[i]
            shape = node_shapes[i]
            
            if shape == 's':  # Square for stocks
                rect = patches.Rectangle((x-0.3, y-0.2), 0.6, 0.4, 
                                       linewidth=2, edgecolor=color, 
                                       facecolor='lightgray', alpha=0.7)
                ax.add_patch(rect)
            else:  # Circle for regular processes
                circle = patches.Circle((x, y), 0.25, linewidth=2, 
                                      edgecolor=color, facecolor='lightgray', alpha=0.7)
                ax.add_patch(circle)
            
            # Add text label
            ax.text(x, y, node_data['label'], ha='center', va='center', 
                   fontsize=8, fontweight='bold', wrap=True)
        
        # Draw edges (flows)
        for edge in G.edges():
            start_pos = pos[edge[0]]
            end_pos = pos[edge[1]]
            
            # Create arrow
            arrow = patches.FancyArrowPatch(start_pos, end_pos,
                                          connectionstyle="arc3,rad=0.1",
                                          arrowstyle='->', 
                                          mutation_scale=20,
                                          linewidth=2,
                                          color='black')
            ax.add_patch(arrow)
            
            # Add flow label
            edge_data = G.edges[edge]
            label = edge_data['label']
            
            # Position label at midpoint
            mid_x = (start_pos[0] + end_pos[0]) / 2
            mid_y = (start_pos[1] + end_pos[1]) / 2
            
            ax.text(mid_x, mid_y, label, ha='center', va='center',
                   fontsize=6, bbox=dict(boxstyle="round,pad=0.3", 
                                        facecolor="white", alpha=0.8))
        
        # Set plot properties
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        ax.set_xlim(-1.5, 1.5)
        ax.set_ylim(-1, 1)
        ax.axis('off')
        
        # Add legend
        legend_elements = [
            patches.Patch(color='#1f77b4', label='Regular Process'),
            patches.Patch(color='#ff7f0e', label='Stock Process'),
            patches.Patch(color='#d62728', label='Initial Stock')
        ]
        ax.legend(handles=legend_elements, loc='upper right')
        
        plt.tight_layout()
        
        return fig, G
        
    except Exception as e:
        print(f"Error creating flow chart: {e}")
        return None, None


def plot_interactive_flow_chart_from_excel(excel_file_path, title="Interactive System Flow Chart"):
    """
    Create an interactive flow chart using Plotly.
    
    Args:
        excel_file_path (str): Path to the Excel file
        title (str): Chart title
        
    Returns:
        plotly.graph_objects.Figure: Interactive flow chart
    """
    try:
        # Read Excel data
        flows_df = pd.read_excel(excel_file_path, sheet_name='1_1_Definition_Flows')
        processes_df = pd.read_excel(excel_file_path, sheet_name='2_1_Definition_Processes')
        
        # Drop rows with missing IDs or names
        processes_df = processes_df.dropna(subset=['ID', 'Name(EN)'])
        flows_df = flows_df.dropna(subset=['Flow_ID', 'Name(EN)', 'Process_ID_O', 'Process_ID_I'])
        
        # Create NetworkX graph
        G = nx.DiGraph()
        
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
            
            node_label = f"{process_id}: {process_name}"
            
            G.add_node(process_id, 
                      name=process_name,
                      label=node_label,
                      is_stock=is_stock,
                      is_initial_stock=is_initial_stock)
        
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
            if process_o in G.nodes and process_i in G.nodes:
                G.add_edge(process_o, process_i, 
                          flow_id=flow_id,
                          flow_name=flow_name,
                          label=edge_label)
        
        # Create Plotly figure
        pos = nx.spring_layout(G, k=3, iterations=50)
        
        # Prepare node traces
        node_x = []
        node_y = []
        node_text = []
        node_colors = []
        node_sizes = []
        
        for node in G.nodes():
            x, y = pos[node]
            node_data = G.nodes[node]
            
            node_x.append(x)
            node_y.append(y)
            node_text.append(node_data['label'])
            
            if node_data.get('is_stock', False):
                node_colors.append('#ff7f0e')
                node_sizes.append(30)
            elif node_data.get('is_initial_stock', False):
                node_colors.append('#d62728')
                node_sizes.append(35)
            else:
                node_colors.append('#1f77b4')
                node_sizes.append(25)
        
        # Create node trace
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            text=node_text,
            textposition="middle center",
            marker=dict(
                size=node_sizes,
                color=node_colors,
                line=dict(width=2, color='black')
            )
        )
        
        # Prepare edge traces
        edge_x = []
        edge_y = []
        edge_text = []
        
        for edge in G.edges():
            start_pos = pos[edge[0]]
            end_pos = pos[edge[1]]
            
            edge_x.extend([start_pos[0], end_pos[0], None])
            edge_y.extend([start_pos[1], end_pos[1], None])
            
            edge_data = G.edges[edge]
            edge_text.append(edge_data['label'])
        
        # Create edge trace
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=2, color='black'),
            hoverinfo='none',
            mode='lines'
        )
        
        # Create figure
        fig = go.Figure(data=[edge_trace, node_trace],
                       layout=go.Layout(
                           title=title,
                           showlegend=False,
                           hovermode='closest',
                           margin=dict(b=20,l=5,r=5,t=40),
                           xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                       )
        
        return fig
        
    except Exception as e:
        print(f"Error creating interactive flow chart: {e}")
        return None


def plot_system_architecture_from_excel(excel_file_path, title="System Architecture Diagram"):
    """
    Create a system architecture diagram showing process categories.
    
    Args:
        excel_file_path (str): Path to the Excel file
        title (str): Chart title
        
    Returns:
        tuple: (matplotlib figure, networkx graph)
    """
    try:
        # Read Excel data
        flows_df = pd.read_excel(excel_file_path, sheet_name='1_1_Definition_Flows')
        processes_df = pd.read_excel(excel_file_path, sheet_name='2_1_Definition_Processes')
        
        # Drop rows with missing IDs or names
        processes_df = processes_df.dropna(subset=['ID', 'Name(EN)'])
        flows_df = flows_df.dropna(subset=['Flow_ID', 'Name(EN)', 'Process_ID_O', 'Process_ID_I'])
        
        # Create NetworkX graph
        G = nx.DiGraph()
        
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
            
            node_label = f"{process_id}: {process_name}"
            
            G.add_node(process_id, 
                      name=process_name,
                      label=node_label,
                      is_stock=is_stock,
                      is_initial_stock=is_initial_stock)
        
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
            if process_o in G.nodes and process_i in G.nodes:
                G.add_edge(process_o, process_i, 
                          flow_id=flow_id,
                          flow_name=flow_name,
                          label=edge_label)
        
        # Create matplotlib figure
        fig, ax = plt.subplots(figsize=(16, 10))
        
        # Categorize processes
        process_categories = {
            'input': [],
            'treatment': [],
            'use': [],
            'output': [],
            'default': []  # Add default category
        }
        
        # Simple categorization based on process names
        for node in G.nodes():
            node_data = G.nodes[node]
            name = str(node_data['name']).lower() if isinstance(node_data['name'], str) else str(node_data['name'])
            
            if any(keyword in name for keyword in ['input', 'import', 'source']):
                process_categories['input'].append(node)
            elif any(keyword in name for keyword in ['treatment', 'process', 'convert']):
                process_categories['treatment'].append(node)
            elif any(keyword in name for keyword in ['use', 'consume', 'apply']):
                process_categories['use'].append(node)
            elif any(keyword in name for keyword in ['output', 'export', 'sink']):
                process_categories['output'].append(node)
            else:
                process_categories['default'].append(node)
        
        # Create process boxes
        y_positions = {'input': 0.8, 'treatment': 0.6, 'use': 0.4, 'output': 0.2, 'default': 0.1}
        
        # Define colors for categories
        colors = {
            'input': '#ff7f0e',
            'treatment': '#1f77b4',
            'use': '#2ca02c',
            'output': '#d62728',
            'default': '#7f7f7f'
        }
        
        # Draw process boxes
        for category, processes in process_categories.items():
            if not processes:
                continue
                
            y_pos = y_positions[category]
            color = colors[category]
            
            # Calculate x positions for processes in this category
            x_positions = np.linspace(0.1, 0.9, len(processes))
            
            for i, process_id in enumerate(processes):
                x_pos = x_positions[i]
                node_data = G.nodes[process_id]
                
                # Create process box
                if node_data.get('is_stock', False):
                    # Stock process - different shape
                    rect = patches.Rectangle((x_pos-0.08, y_pos-0.05), 0.16, 0.1,
                                           linewidth=2, edgecolor=color,
                                           facecolor='lightgray', alpha=0.7)
                    ax.add_patch(rect)
                else:
                    # Regular process
                    rect = patches.Rectangle((x_pos-0.08, y_pos-0.05), 0.16, 0.1,
                                           linewidth=2, edgecolor=color,
                                           facecolor='white', alpha=0.7)
                    ax.add_patch(rect)
                
                # Add text
                ax.text(x_pos, y_pos, node_data['label'], ha='center', va='center',
                       fontsize=8, fontweight='bold', wrap=True)
        
        # Draw flows
        for edge in G.edges():
            start_node = edge[0]
            end_node = edge[1]
            
            # Find positions
            start_pos = None
            end_pos = None
            
            for category, processes in process_categories.items():
                if start_node in processes:
                    y_start = y_positions[category]
                    x_start = np.linspace(0.1, 0.9, len(processes))[processes.index(start_node)]
                    start_pos = (x_start, y_start)
                
                if end_node in processes:
                    y_end = y_positions[category]
                    x_end = np.linspace(0.1, 0.9, len(processes))[processes.index(end_node)]
                    end_pos = (x_end, y_end)
            
            if start_pos and end_pos:
                # Create arrow
                arrow = patches.FancyArrowPatch(start_pos, end_pos,
                                              connectionstyle="arc3,rad=0.1",
                                              arrowstyle='->',
                                              mutation_scale=15,
                                              linewidth=1.5,
                                              color='black')
                ax.add_patch(arrow)
                
                # Add flow label
                edge_data = G.edges[edge]
                label = edge_data['label']
                
                mid_x = (start_pos[0] + end_pos[0]) / 2
                mid_y = (start_pos[1] + end_pos[1]) / 2
                
                ax.text(mid_x, mid_y, label, ha='center', va='center',
                       fontsize=6, bbox=dict(boxstyle="round,pad=0.2",
                                            facecolor="white", alpha=0.8))
        
        # Set plot properties
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        # Add legend
        legend_elements = [
            patches.Patch(color=colors['input'], label='Input Processes'),
            patches.Patch(color=colors['treatment'], label='Treatment Processes'),
            patches.Patch(color=colors['use'], label='Use Processes'),
            patches.Patch(color=colors['output'], label='Output Processes'),
            patches.Patch(color=colors['default'], label='Other Processes')
        ]
        ax.legend(handles=legend_elements, loc='upper right')
        
        plt.tight_layout()
        
        return fig, G
        
    except Exception as e:
        print(f"Error creating system architecture diagram: {e}")
        return None, None


def create_flow_chart_export_controls(fig, filename_prefix="flow_chart"):
    """
    Create export controls for flow charts.
    
    Args:
        fig: Matplotlib figure
        filename_prefix (str): Prefix for exported files
        
    Returns:
        ipywidgets.VBox: Export controls widget
    """
    def export_png():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.png"
        fig.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"✅ Exported as PNG: {filename}")
    
    def export_pdf():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.pdf"
        fig.savefig(filename, bbox_inches='tight')
        print(f"✅ Exported as PDF: {filename}")
    
    def export_svg():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.svg"
        fig.savefig(filename, bbox_inches='tight')
        print(f"✅ Exported as SVG: {filename}")
    
    # Create buttons
    png_btn = Button(description="Export PNG", button_style='success')
    pdf_btn = Button(description="Export PDF", button_style='info')
    svg_btn = Button(description="Export SVG", button_style='warning')
    
    # Connect buttons to functions
    png_btn.on_click(lambda b: export_png())
    pdf_btn.on_click(lambda b: export_pdf())
    svg_btn.on_click(lambda b: export_svg())
    
    # Create layout
    controls = VBox([
        HTML("<h4>Export Options:</h4>"),
        HBox([png_btn, pdf_btn, svg_btn])
    ])
    
    return controls 