# -*- coding: utf-8 -*-
"""
Graphviz Flow Chart Plotting Module.

This module provides a professional, minimalist black-and-white block flow diagram
using Graphviz to visualize the system structure.
"""

import pandas as pd
import graphviz

def plot_graphviz_flow_chart_sankey_style(processes_df, flows_df, title="BioDYM System - Sankey-Style Block Flow Diagram", 
                                         rankdir="LR", ranksep=1.0, nodesep=0.5, max_processes=20, max_flows=30):
    """
    Create a clean, professional Sankey-style block flow diagram using Graphviz.
    
    Enhanced version that addresses data quality issues and Graphviz limitations:
    - Filters out incomplete data
    - Limits complexity for better visualization
    - Provides detailed diagnostics
    - Handles missing data gracefully
    
    Args:
        processes_df (pd.DataFrame): DataFrame containing process definitions.
        flows_df (pd.DataFrame): DataFrame containing flow definitions.
        title (str): Chart title
        rankdir (str): Direction ('LR', 'TB', 'RL', 'BT')
        ranksep (float): Separation between ranks
        nodesep (float): Separation between nodes
        max_processes (int): Maximum number of processes to include
        max_flows (int): Maximum number of flows to include
        
    Returns:
        graphviz.Digraph: Graphviz diagram object
    """
    try:
        print(f"🔍 Graphviz Analysis:")
        print(f"   Input: {len(processes_df)} processes, {len(flows_df)} flows")
        
        # Step 1: Data Quality Analysis and Filtering
        print(f"   Data Quality Check:")
        
        # Filter processes with complete data
        complete_processes = processes_df.dropna(subset=['ID', 'Name(EN)'])
        complete_processes = complete_processes[complete_processes['Name(EN)'].str.strip() != '']
        print(f"   - Complete processes: {len(complete_processes)}/{len(processes_df)}")
        
        # Filter flows with complete data
        complete_flows = flows_df.dropna(subset=['Flow_ID', 'Name(EN)', 'Process_ID_O', 'Process_ID_I'])
        complete_flows = complete_flows[complete_flows['Name(EN)'].str.strip() != '']
        print(f"   - Complete flows: {len(complete_flows)}/{len(flows_df)}")
        
        # Step 2: Identify Connected Processes
        connected_process_ids = set()
        for _, flow in complete_flows.iterrows():
            connected_process_ids.add(flow['Process_ID_O'])
            connected_process_ids.add(flow['Process_ID_I'])
        
        # Filter to only connected processes
        connected_processes = complete_processes[complete_processes['ID'].isin(connected_process_ids)]
        print(f"   - Connected processes: {len(connected_processes)}")
        
        # Step 3: Complexity Management
        if len(connected_processes) > max_processes:
            print(f"   ⚠️ Too many processes ({len(connected_processes)} > {max_processes})")
            print(f"   📊 Selecting most connected processes...")
            
            # Count connections per process
            process_connections = {}
            for _, flow in complete_flows.iterrows():
                process_o = flow['Process_ID_O']
                process_i = flow['Process_ID_I']
                process_connections[process_o] = process_connections.get(process_o, 0) + 1
                process_connections[process_i] = process_connections.get(process_i, 0) + 1
            
            # Select most connected processes
            sorted_processes = sorted(process_connections.items(), key=lambda x: x[1], reverse=True)
            selected_process_ids = [pid for pid, _ in sorted_processes[:max_processes]]
            connected_processes = connected_processes[connected_processes['ID'].isin(selected_process_ids)]
            print(f"   ✅ Selected {len(connected_processes)} most connected processes")
        
        # Step 4: Filter flows to only include selected processes
        selected_process_ids = set(connected_processes['ID'])
        filtered_flows = complete_flows[
            (complete_flows['Process_ID_O'].isin(selected_process_ids)) & 
            (complete_flows['Process_ID_I'].isin(selected_process_ids))
        ]
        
        if len(filtered_flows) > max_flows:
            print(f"   ⚠️ Too many flows ({len(filtered_flows)} > {max_flows})")
            print(f"   📊 Selecting most important flows...")
            # For now, just take the first max_flows
            filtered_flows = filtered_flows.head(max_flows)
            print(f"   ✅ Selected {len(filtered_flows)} flows")
        
        print(f"   Final: {len(connected_processes)} processes, {len(filtered_flows)} flows")
        
        # Step 5: Create Graphviz Diagram
        dot = graphviz.Digraph(comment=title)
        dot.attr(rankdir=rankdir, ranksep=str(ranksep), nodesep=str(nodesep))
        dot.attr(label=f"{title}\\n({len(connected_processes)} processes, {len(filtered_flows)} flows)", 
                labelloc="t", fontname="Arial", fontsize="12")
        
        # Enhanced styling for better readability
        dot.attr('node', 
                shape='box', 
                style='filled', 
                fillcolor='lightblue', 
                color='black', 
                fontcolor='black',
                fontname='Arial', 
                fontsize='9',
                margin='0.15',
                width='1.5',
                height='0.5')
        dot.attr('edge', 
                color='gray',
                fontcolor='black',
                fontname='Arial', 
                fontsize='7',
                arrowsize='0.7',
                penwidth='1.0',
                splines='ortho',
                arrowhead='normal')
        
        # Add processes as nodes with improved labels
        for _, process in connected_processes.iterrows():
            process_id = int(process['ID'])
            process_name = str(process['Name(EN)']).strip()
            
            # Truncate long names for better readability
            if len(process_name) > 20:
                process_name = process_name[:17] + "..."
            
            node_label = f"P{process_id}\\n{process_name}"
            dot.node(str(process_id), node_label)
        
        # Add flows as edges with improved labels
        for _, flow in filtered_flows.iterrows():
            flow_id = str(flow['Flow_ID']).strip()
            flow_name = str(flow['Name(EN)']).strip()
            process_o = int(flow['Process_ID_O'])
            process_i = int(flow['Process_ID_I'])
            
            # Truncate long flow names
            if len(flow_name) > 15:
                flow_name = flow_name[:12] + "..."
            
            edge_label = f"{flow_name}"
            dot.edge(str(process_o), str(process_i), label=edge_label)
        
        print(f"   ✅ Graphviz chart created successfully!")
        return dot
        
    except Exception as e:
        print(f"❌ Error creating Sankey-style Graphviz flow chart: {e}")
        import traceback
        traceback.print_exc()
        return None