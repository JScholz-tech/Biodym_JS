# -*- coding: utf-8 -*-
"""
Graphviz Flow Chart Plotting Module.

This module provides a professional, minimalist black-and-white block flow diagram
using Graphviz to visualize the system structure.
"""

import pandas as pd
import graphviz

def plot_graphviz_flow_chart_sankey_style(processes_df, flows_df, title="BioDYM System - Sankey-Style Block Flow Diagram", 
                                         rankdir="LR", ranksep=1.0, nodesep=0.5):
    """
    Create a clean, professional Sankey-style block flow diagram using Graphviz.
    
    Args:
        processes_df (pd.DataFrame): DataFrame containing process definitions.
        flows_df (pd.DataFrame): DataFrame containing flow definitions.
        title (str): Chart title
        rankdir (str): Direction ('LR', 'TB', 'RL', 'BT')
        ranksep (float): Separation between ranks
        nodesep (float): Separation between nodes
        
    Returns:
        graphviz.Digraph: Graphviz diagram object
    """
    try:
        # Drop rows with missing IDs or names for robustness
        processes_df = processes_df.dropna(subset=['ID', 'Name(EN)'])
        flows_df = flows_df.dropna(subset=['Flow_ID', 'Name(EN)', 'Process_ID_O', 'Process_ID_I'])
        
        # Create Graphviz digraph with clean, professional styling
        dot = graphviz.Digraph(comment=title)
        dot.attr(rankdir=rankdir, ranksep=str(ranksep), nodesep=str(nodesep))
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
                penwidth='1.0',
                splines='ortho',
                arrowhead='box') # Use box-style arrows
        
        # Add processes as nodes
        for _, process in processes_df.iterrows():
            process_id = process['ID']
            process_name = process['Name(EN)']
            
            if pd.isna(process_id) or pd.isna(process_name) or str(process_name).strip() == '':
                continue
                
            node_label = f"{int(process_id)}: {str(process_name)}"
            dot.node(str(process_id), node_label)
        
        # Add flows as edges
        for _, flow in flows_df.iterrows():
            flow_id = flow['Flow_ID']
            flow_name = flow['Name(EN)']
            process_o = flow['Process_ID_O']
            process_i = flow['Process_ID_I']
            
            if pd.isna(flow_id) or pd.isna(flow_name) or pd.isna(process_o) or pd.isna(process_i):
                continue
                
            edge_label = f"{str(flow_id)}: {str(flow_name)}"
            dot.edge(str(process_o), str(process_i), label=edge_label)
        
        return dot
        
    except Exception as e:
        print(f"Error creating Sankey-style Graphviz flow chart: {e}")
        return None