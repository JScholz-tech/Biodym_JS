# -*- coding: utf-8 -*-
"""
Plotting Module for the BioDYM MFA Model.

This file contains all functions responsible for generating the various
interactive visualizations for the model results, including Sankey diagrams,
time-series plots, and Monte Carlo analysis plots.
"""
import numpy as np
import plotly.graph_objects as go
from ipywidgets import interact, IntSlider, Dropdown, SelectMultiple, Checkbox
from IPython.display import display


def plot_mass_balance_error(mfa_system_results):
    """
    Creates an interactive bar chart showing the mass balance error for each process.
    Error = Inflows - Outflows - dS. An error of 0 means perfect balance.
    This is the FIRST and most important visualization for validation.

    Args:
        mfa_system_results (odym.MFAsystem): The solved MFA system object.
    """
    process_names = [p.Name for p in mfa_system_results.ProcessList]
    time_items = mfa_system_results.IndexTable.Classification['Time'].Items
    element_items = mfa_system_results.Elements
    
    fig = go.FigureWidget()

    def update_plot(year, element):
        year_index = time_items.index(year)
        element_index = element_items.index(element)
        
        errors = []
        for p in mfa_system_results.ProcessList:
            in_val = sum(f.Values[year_index, element_index] for f in mfa_system_results.FlowDict.values() if f.P_End == p.ID)
            out_val = sum(f.Values[year_index, element_index] for f in mfa_system_results.FlowDict.values() if f.P_Start == p.ID)
            ds_val = mfa_system_results.StockDict.get(f'dS_{p.ID}', None)
            ds_sum = ds_val.Values[year_index, element_index] if ds_val is not None else 0
            
            error = in_val - out_val - ds_sum
            errors.append(error)
        
        # Color bars based on error direction
        colors = ['#d62728' if e > 1e-9 else '#2ca02c' if e < -1e-9 else '#7f7f7f' for e in errors]

        with fig.batch_update():
            fig.data = [] # Clear previous data
            fig.add_trace(go.Bar(x=process_names, y=errors, marker_color=colors))
            fig.update_layout(
                title=f"Mass Balance Error Check for {element.upper()} in {year}",
                yaxis_title="Error in Mg (positive = mass created)",
                shapes=[dict(type='line', y0=0, y1=0, x0=-0.5, x1=len(process_names)-0.5, line=dict(color='black', width=2))], # Zero line
                height=500
            )

    # Create widgets
    year_slider = IntSlider(min=time_items[0], max=time_items[-1], step=1, value=time_items[0], description='Year')
    element_dropdown = Dropdown(options=element_items, value=element_items[0], description='Element:')
    
    interact(update_plot, year=year_slider, element=element_dropdown)
    display(fig)


def plot_stock_evolution(mfa_system_results, dsm_params=None, fomp_params=None):
    """
    Creates an interactive plot showing the evolution of all stocks over time.
    Special highlighting for DSM and FOMP processes.

    Args:
        mfa_system_results (odym.MFAsystem): The solved MFA system object.
        dsm_params (dict, optional): DSM parameters to identify DSM processes.
        fomp_params (dict, optional): FOMP parameters to identify FOMP processes.
    """
    time_items = mfa_system_results.IndexTable.Classification['Time'].Items
    element_items = mfa_system_results.Elements
    
    # Identify process types
    dsm_processes = set(dsm_params.keys()) if dsm_params else set()
    fomp_processes = set(fomp_params.keys()) if fomp_params else set()
    
    # Get stocks (exclude delta stocks)
    stock_names = [name for name in mfa_system_results.StockDict.keys() if name.startswith('S_')]
    process_names = [p.Name for p in mfa_system_results.ProcessList if f'S_{p.ID}' in stock_names]
    
    fig = go.FigureWidget()

    def update_plot(element, show_individual):
        element_index = element_items.index(element)
        
        with fig.batch_update():
            fig.data = []
            
            if show_individual == 'Individual Stocks':
                # Show individual stock lines
                for i, stock_name in enumerate(stock_names):
                    stock_obj = mfa_system_results.StockDict[stock_name]
                    stock_values = stock_obj.Values[:, element_index]
                    
                    # Determine line style based on process type
                    process_id = int(stock_name.split('_')[1])
                    if process_id in dsm_processes:
                        line_style = dict(color='#ff7f0e', width=3, dash='dash')  # Orange, dashed
                        name_prefix = "DSM: "
                    elif process_id in fomp_processes:
                        line_style = dict(color='#2ca02c', width=3, dash='dot')   # Green, dot-dash
                        name_prefix = "FOMP: "
                    else:
                        line_style = dict(color='#1f77b4', width=2)              # Blue, solid
                        name_prefix = ""
                    
                    fig.add_trace(go.Scatter(
                        x=time_items, 
                        y=stock_values, 
                        mode='lines',
                        name=f"{name_prefix}{process_names[i]}",
                        line=line_style
                    ))
                
                fig.update_layout(
                    title=f"Individual Stock Evolution ({element.upper()})",
                    xaxis_title="Year",
                    yaxis_title=f"Stock in Mg",
                    hovermode="x unified"
                )
            else:
                # Show total stock
                total_stock = np.zeros(len(time_items))
                for stock_name in stock_names:
                    stock_obj = mfa_system_results.StockDict[stock_name]
                    total_stock += stock_obj.Values[:, element_index]
                
                fig.add_trace(go.Scatter(
                    x=time_items, 
                    y=total_stock, 
                    mode='lines',
                    name=f"Total Stock ({element.upper()})",
                    line=dict(color='#d62728', width=3)
                ))
                
                fig.update_layout(
                    title=f"Total System Stock Evolution ({element.upper()})",
                    xaxis_title="Year",
                    yaxis_title=f"Total Stock in Mg"
                )

    # Create widgets
    element_dropdown = Dropdown(options=element_items, value=element_items[0], description='Element:')
    view_checkbox = Dropdown(options=['Total Stock', 'Individual Stocks'], value='Total Stock', description='View:')
    
    interact(update_plot, element=element_dropdown, show_individual=view_checkbox)
    display(fig)


def plot_dsm_stock_details(mfa_system_results, dsm_params, dsm_details):
    """
    Creates detailed stock evolution plots specifically for DSM processes.
    Shows initial stock decay and new stock accumulation.

    Args:
        mfa_system_results (odym.MFAsystem): The solved MFA system object.
        dsm_params (dict): DSM parameters configuration.
        dsm_details (dict): Detailed DSM calculation results.
    """
    if not dsm_params:
        print("No DSM processes found to plot.")
        return
    
    time_items = mfa_system_results.IndexTable.Classification['Time'].Items
    element_items = mfa_system_results.Elements
    
    fig = go.FigureWidget()

    def update_plot(process_id, element):
        if process_id not in dsm_details:
            print(f"No detailed results for process {process_id}")
            return
            
        element_index = element_items.index(element)
        details = dsm_details[process_id]
        
        with fig.batch_update():
            fig.data = []
            
            # Get stock components
            initial_stock_ts = details.get('initial_stock_ts', np.zeros((len(time_items), len(element_items))))
            inflow_stocks_material = details.get('inflow_stock_ts_by_cat', [])
            category_names = details.get('category_names', [])
            
            # Plot initial stock decay
            initial_stock_element = initial_stock_ts[:, element_index]
            fig.add_trace(go.Scatter(
                x=time_items, 
                y=initial_stock_element, 
                mode='lines',
                name='Initial Stock (Decaying)',
                line=dict(color='#ff7f0e', width=2, dash='dash')
            ))
            
            # Plot new stock accumulation by category
            total_inflow_stock = np.zeros(len(time_items))
            for i, stock_ts_material in enumerate(inflow_stocks_material):
                # Convert material stock to element stock using composition
                inflows = [f.Values for f in mfa_system_results.FlowDict.values() if f.P_End == process_id]
                total_inflow_values = sum(inflows) if inflows else np.zeros((len(time_items), len(element_items)))
                inflow_comp_factor = np.divide(total_inflow_values[:, element_index], total_inflow_values[:, 0], 
                                             out=np.zeros(len(time_items)), where=total_inflow_values[:, 0] != 0)
                
                stock_ts_element = stock_ts_material * inflow_comp_factor
                total_inflow_stock += stock_ts_element
                
                fig.add_trace(go.Scatter(
                    x=time_items, 
                    y=stock_ts_element, 
                    mode='lines',
                    name=f"New Stock: {category_names[i]}",
                    line=dict(width=1)
                ))
            
            # Plot total stock
            total_stock = initial_stock_element + total_inflow_stock
            fig.add_trace(go.Scatter(
                x=time_items, 
                y=total_stock, 
                mode='lines',
                name='Total Stock',
                line=dict(color='#d62728', width=3)
            ))
            
            process_name = next((p.Name for p in mfa_system_results.ProcessList if p.ID == process_id), f"Process {process_id}")
            fig.update_layout(
                title=f"DSM Stock Evolution: {process_name} ({element.upper()})",
                xaxis_title="Year",
                yaxis_title=f"Stock in Mg",
                hovermode="x unified"
            )

    # Create widgets
    process_dropdown = Dropdown(options=list(dsm_params.keys()), description='DSM Process:')
    element_dropdown = Dropdown(options=element_items, value=element_items[0], description='Element:')
    
    interact(update_plot, process_id=process_dropdown, element=element_dropdown)
    display(fig)


def plot_fomp_stock_details(mfa_system_results, fomp_params):
    """
    Creates detailed stock evolution plots specifically for FOMP processes.
    Shows organic matter accumulation and mineralization.

    Args:
        mfa_system_results (odym.MFAsystem): The solved MFA system object.
        fomp_params (dict): FOMP parameters configuration.
    """
    if not fomp_params:
        print("No FOMP processes found to plot.")
        return
    
    time_items = mfa_system_results.IndexTable.Classification['Time'].Items
    element_items = mfa_system_results.Elements
    
    fig = go.FigureWidget()

    def update_plot(process_id, element):
        element_index = element_items.index(element)
        
        with fig.batch_update():
            fig.data = []
            
            # Get stock data
            stock_obj = mfa_system_results.StockDict.get(f'S_{process_id}')
            if stock_obj is None:
                print(f"No stock data for process {process_id}")
                return
                
            stock_values = stock_obj.Values[:, element_index]
            
            # Get inflow and outflow data
            inflow_ts = sum(f.Values[:, element_index] for f in mfa_system_results.FlowDict.values() if f.P_End == process_id)
            outflow_ts = sum(f.Values[:, element_index] for f in mfa_system_results.FlowDict.values() if f.P_Start == process_id)
            
            # Plot stock evolution
            fig.add_trace(go.Scatter(
                x=time_items, 
                y=stock_values, 
                mode='lines',
                name='Organic Matter Stock',
                line=dict(color='#2ca02c', width=3)
            ))
            
            # Plot cumulative inflow and outflow
            cumulative_inflow = np.cumsum(inflow_ts)
            cumulative_outflow = np.cumsum(outflow_ts)
            
            fig.add_trace(go.Scatter(
                x=time_items, 
                y=cumulative_inflow, 
                mode='lines',
                name='Cumulative Input',
                line=dict(color='#1f77b4', width=2, dash='dash')
            ))
            
            fig.add_trace(go.Scatter(
                x=time_items, 
                y=cumulative_outflow, 
                mode='lines',
                name='Cumulative Mineralization',
                line=dict(color='#d62728', width=2, dash='dot')
            ))
            
            process_name = next((p.Name for p in mfa_system_results.ProcessList if p.ID == process_id), f"Process {process_id}")
            fig.update_layout(
                title=f"FOMP Stock Evolution: {process_name} ({element.upper()})",
                xaxis_title="Year",
                yaxis_title=f"Mass in Mg",
                hovermode="x unified"
            )

    # Create widgets
    process_dropdown = Dropdown(options=list(fomp_params.keys()), description='FOMP Process:')
    element_dropdown = Dropdown(options=element_items, value=element_items[0], description='Element:')
    
    interact(update_plot, process_id=process_dropdown, element=element_dropdown)
    display(fig)


def plot_system_efficiency_metrics(mfa_system_results):
    """
    Creates interactive plots showing system efficiency metrics:
    - Recycling rates
    - Recovery rates
    - Material efficiency indicators

    Args:
        mfa_system_results (odym.MFAsystem): The solved MFA system object.
    """
    time_items = mfa_system_results.IndexTable.Classification['Time'].Items
    element_items = mfa_system_results.Elements
    
    fig = go.FigureWidget()

    def update_plot(element, metric_type):
        element_index = element_items.index(element)
        
        with fig.batch_update():
            fig.data = []
            
            if metric_type == "Recycling Rate":
                # Calculate recycling rate for each year
                recycling_rates = []
                for year_idx in range(len(time_items)):
                    # Find flows that represent recycling (internal flows)
                    internal_flows = [f for f in mfa_system_results.FlowDict.values() 
                                    if f.P_Start != 0 and f.P_End != 0]  # Exclude external flows
                    total_internal_flow = sum(f.Values[year_idx, element_index] for f in internal_flows)
                    
                    # Find total system throughput
                    total_throughput = sum(f.Values[year_idx, element_index] for f in mfa_system_results.FlowDict.values())
                    
                    if total_throughput > 0:
                        recycling_rate = (total_internal_flow / total_throughput) * 100
                    else:
                        recycling_rate = 0
                    recycling_rates.append(recycling_rate)
                
                fig.add_trace(go.Scatter(
                    x=time_items, 
                    y=recycling_rates, 
                    mode='lines+markers',
                    name='Recycling Rate (%)',
                    line=dict(color='#1f77b4', width=3)
                ))
                
                fig.update_layout(
                    title=f"System Recycling Rate ({element.upper()})",
                    xaxis_title="Year",
                    yaxis_title="Recycling Rate (%)",
                    yaxis=dict(range=[0, 100])
                )
                
            elif metric_type == "Recovery Rate":
                # Calculate recovery rate (outputs / inputs)
                recovery_rates = []
                for year_idx in range(len(time_items)):
                    # Find external outputs (flows to environment/sinks)
                    external_outputs = [f for f in mfa_system_results.FlowDict.values() 
                                      if f.P_Start != 0 and f.P_End == 0]  # Internal to external
                    total_output = sum(f.Values[year_idx, element_index] for f in external_outputs)
                    
                    # Find external inputs
                    external_inputs = [f for f in mfa_system_results.FlowDict.values() 
                                     if f.P_Start == 0 and f.P_End != 0]  # External to internal
                    total_input = sum(f.Values[year_idx, element_index] for f in external_inputs)
                    
                    if total_input > 0:
                        recovery_rate = (total_output / total_input) * 100
                    else:
                        recovery_rate = 0
                    recovery_rates.append(recovery_rate)
                
                fig.add_trace(go.Scatter(
                    x=time_items, 
                    y=recovery_rates, 
                    mode='lines+markers',
                    name='Recovery Rate (%)',
                    line=dict(color='#2ca02c', width=3)
                ))
                
                fig.update_layout(
                    title=f"System Recovery Rate ({element.upper()})",
                    xaxis_title="Year",
                    yaxis_title="Recovery Rate (%)",
                    yaxis=dict(range=[0, 100])
                )
                
            elif metric_type == "Material Efficiency":
                # Calculate material efficiency (useful output / total input)
                efficiency_rates = []
                for year_idx in range(len(time_items)):
                    # Find useful outputs (e.g., to food, products)
                    useful_outputs = [f for f in mfa_system_results.FlowDict.values() 
                                    if f.P_Start != 0 and f.P_End == 0 and 
                                    any(keyword in f.Name.lower() for keyword in ['food', 'product', 'use'])]
                    total_useful = sum(f.Values[year_idx, element_index] for f in useful_outputs)
                    
                    # Find total inputs
                    total_input = sum(f.Values[year_idx, element_index] for f in mfa_system_results.FlowDict.values() 
                                    if f.P_Start == 0 and f.P_End != 0)
                    
                    if total_input > 0:
                        efficiency = (total_useful / total_input) * 100
                    else:
                        efficiency = 0
                    efficiency_rates.append(efficiency)
                
                fig.add_trace(go.Scatter(
                    x=time_items, 
                    y=efficiency_rates, 
                    mode='lines+markers',
                    name='Material Efficiency (%)',
                    line=dict(color='#d62728', width=3)
                ))
                
                fig.update_layout(
                    title=f"Material Efficiency ({element.upper()})",
                    xaxis_title="Year",
                    yaxis_title="Efficiency (%)",
                    yaxis=dict(range=[0, 100])
                )

    # Create widgets
    element_dropdown = Dropdown(options=element_items, value=element_items[0], description='Element:')
    metric_dropdown = Dropdown(
        options=['Recycling Rate', 'Recovery Rate', 'Material Efficiency'], 
        value='Recycling Rate', 
        description='Metric:'
    )
    
    interact(update_plot, element=element_dropdown, metric_type=metric_dropdown)
    display(fig)


def plot_summary_dashboard(mfa_system_results, dsm_params=None, fomp_params=None):
    """
    Creates a comprehensive summary dashboard showing key KPIs and system status.

    Args:
        mfa_system_results (odym.MFAsystem): The solved MFA system object.
        dsm_params (dict, optional): DSM parameters configuration.
        fomp_params (dict, optional): FOMP parameters configuration.
    """
    from plotly.subplots import make_subplots
    
    time_items = mfa_system_results.IndexTable.Classification['Time'].Items
    element_items = mfa_system_results.Elements
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Total Stock Evolution', 'System Flows', 'Process Types', 'Key Metrics'),
        specs=[[{"type": "scatter"}, {"type": "scatter"}],
               [{"type": "bar"}, {"type": "indicator"}]]
    )
    
    # 1. Total Stock Evolution (all elements)
    for i, element in enumerate(element_items):
        element_index = element_items.index(element)
        total_stock = np.zeros(len(time_items))
        
        for stock_name in mfa_system_results.StockDict.keys():
            if stock_name.startswith('S_'):
                stock_obj = mfa_system_results.StockDict[stock_name]
                total_stock += stock_obj.Values[:, element_index]
        
        fig.add_trace(
            go.Scatter(x=time_items, y=total_stock, mode='lines', name=f'Total {element.upper()}'),
            row=1, col=1
        )
    
    # 2. System Flows (material only)
    material_index = element_items.index('material') if 'material' in element_items else 0
    total_flows = np.zeros(len(time_items))
    
    for flow_name, flow_obj in mfa_system_results.FlowDict.items():
        total_flows += flow_obj.Values[:, material_index]
    
    fig.add_trace(
        go.Scatter(x=time_items, y=total_flows, mode='lines', name='Total System Flows'),
        row=1, col=2
    )
    
    # 3. Process Types Distribution
    process_types = ['Regular', 'DSM', 'FOMP']
    process_counts = [
        len([p for p in mfa_system_results.ProcessList if p.ID not in (dsm_params or {}) and p.ID not in (fomp_params or {})]),
        len(dsm_params or {}),
        len(fomp_params or {})
    ]
    
    fig.add_trace(
        go.Bar(x=process_types, y=process_counts, name='Process Count'),
        row=2, col=1
    )
    
    # 4. Key Metrics (latest year)
    latest_year_idx = -1
    total_stock_latest = sum(
        stock_obj.Values[latest_year_idx, 0] 
        for stock_name, stock_obj in mfa_system_results.StockDict.items() 
        if stock_name.startswith('S_')
    )
    
    fig.add_trace(
        go.Indicator(
            mode="gauge+number+delta",
            value=total_stock_latest,
            title={'text': f"Total Stock ({time_items[latest_year_idx]})"},
            gauge={'axis': {'range': [None, total_stock_latest * 1.2]},
                   'bar': {'color': "darkblue"},
                   'steps': [{'range': [0, total_stock_latest * 0.5], 'color': "lightgray"},
                            {'range': [total_stock_latest * 0.5, total_stock_latest], 'color': "gray"}]},
        ),
        row=2, col=2
    )
    
    fig.update_layout(height=800, title_text="BioDYM MFA System Dashboard")
    fig.show()


def plot_scenario_comparison(scenario_results, comparison_metric='final_stock'):
    """
    Creates a comparison plot for different scenarios.

    Args:
        scenario_results (dict): Dictionary with scenario names as keys and MFA system results as values.
        comparison_metric (str): Metric to compare ('final_stock', 'total_flow', 'efficiency').
    """
    if len(scenario_results) < 2:
        print("Need at least 2 scenarios for comparison.")
        return
    
    fig = go.FigureWidget()
    
    def update_comparison(metric_type, element):
        with fig.batch_update():
            fig.data = []
            
            for scenario_name, mfa_system in scenario_results.items():
                if metric_type == "Final Stock":
                    # Compare final stock values
                    final_stocks = []
                    for stock_name in mfa_system.StockDict.keys():
                        if stock_name.startswith('S_'):
                            stock_obj = mfa_system.StockDict[stock_name]
                            final_stocks.append(stock_obj.Values[-1, element_items.index(element)])
                    
                    fig.add_trace(go.Bar(
                        x=[f"Stock {i+1}" for i in range(len(final_stocks))],
                        y=final_stocks,
                        name=scenario_name
                    ))
                    
                    fig.update_layout(
                        title=f"Final Stock Comparison ({element.upper()})",
                        xaxis_title="Stock",
                        yaxis_title=f"Final Stock in Mg",
                        barmode='group'
                    )
                    
                elif metric_type == "Total Flow":
                    # Compare total system flows
                    time_items = mfa_system.IndexTable.Classification['Time'].Items
                    total_flows = np.zeros(len(time_items))
                    
                    for flow_obj in mfa_system.FlowDict.values():
                        total_flows += flow_obj.Values[:, element_items.index(element)]
                    
                    fig.add_trace(go.Scatter(
                        x=time_items,
                        y=total_flows,
                        mode='lines',
                        name=scenario_name
                    ))
                    
                    fig.update_layout(
                        title=f"Total System Flow Comparison ({element.upper()})",
                        xaxis_title="Year",
                        yaxis_title=f"Total Flow in Mg"
                    )
    
    # Get element items from first scenario
    first_system = list(scenario_results.values())[0]
    element_items = first_system.Elements
    
    # Create widgets
    metric_dropdown = Dropdown(
        options=['Final Stock', 'Total Flow'],
        value='Final Stock',
        description='Comparison Metric:'
    )
    element_dropdown = Dropdown(
        options=element_items,
        value=element_items[0],
        description='Element:'
    )
    
    interact(update_comparison, metric_type=metric_dropdown, element=element_dropdown)
    display(fig)


def plot_interactive_sankey(mfa_system_results):
    """
    Generates an interactive Sankey diagram with widgets to select the year,
    element, processes, and a value threshold to hide minor flows.

    Args:
        mfa_system_results (odym.MFAsystem): The solved MFA system object.
    """
    # Import necessary libraries inside the function for modularity
    from ipywidgets import SelectMultiple, FloatSlider
    
    all_process_names = [p.Name for p in mfa_system_results.ProcessList]
    all_flows = list(mfa_system_results.FlowDict.values())
    time_items = mfa_system_results.IndexTable.Classification['Time'].Items
    element_items = mfa_system_results.Elements
    
    # Determine a reasonable max for the slider based on calculated flows
    max_flow_value = max(f.Values.max() for f in all_flows if f.Values is not None) if all_flows else 1

    # Create the FigureWidget with an initial, empty Sankey trace
    fig = go.FigureWidget(data=[go.Sankey(node=dict(label=[]), link=dict(source=[], target=[], value=[]))])

    def update_sankey(year, element, processes_to_show, min_flow_value):
        if not processes_to_show:
            with fig.batch_update(): fig.data[0].node.label = []
            return

        label_map = {p.ID: i for i, p in enumerate(mfa_system_results.ProcessList) if p.Name in processes_to_show}
        filtered_labels = list(processes_to_show)
        
        year_index = time_items.index(year)
        element_index = element_items.index(element)

        candidate_flows = [f for f in all_flows if f.P_Start in label_map and f.P_End in label_map]
        
        # Filter flows based on the slider's threshold value
        final_flows = [f for f in candidate_flows if f.Values[year_index, element_index] >= min_flow_value]

        with fig.batch_update():
            if not final_flows:
                # If no flows are left after filtering, show nodes but no links
                fig.data[0].node.label = filtered_labels
                fig.data[0].link.source, fig.data[0].link.target, fig.data[0].link.value = [], [], []
            else:
                # Update all properties of the Sankey trace
                fig.data[0].node.label = filtered_labels
                fig.data[0].node.color = "blue"
                fig.data[0].link.source = [label_map[f.P_Start] for f in final_flows]
                fig.data[0].link.target = [label_map[f.P_End] for f in final_flows]
                fig.data[0].link.value = [f.Values[year_index, element_index] for f in final_flows]
            
            # Update layout title
            fig.update_layout(title_text=f"MFA Sankey for {element.upper()} in {year} (Flows > {min_flow_value:.2f} Mg)", 
                              font_size=12, height=700, margin=dict(l=10, r=10, b=20, t=50))

    # Create widgets, including the new FloatSlider
    year_slider = IntSlider(min=time_items[0], max=time_items[-1], step=1, value=time_items[0], description='Year')
    element_dropdown = Dropdown(options=element_items, value=element_items[0], description='Element')
    process_selector = SelectMultiple(options=all_process_names, value=list(all_process_names), description='Processes', rows=8)
    threshold_slider = FloatSlider(min=0, max=max_flow_value, step=max_flow_value/100, value=0, 
                                   description='Min Flow', continuous_update=False, readout_format='.2f')
    
    interact(update_sankey, year=year_slider, element=element_dropdown, processes_to_show=process_selector, min_flow_value=threshold_slider)
    display(fig)


def plot_process_dynamics(mfa_system_results, process_definitions):
    """
    Creates three side-by-side line charts showing the dynamics of
    Inflow, Stock, and Outflow, using process type metadata for smarter titles.

    Args:
        mfa_system_results (odym.MFAsystem): The solved MFA system object.
        process_definitions (pd.DataFrame): The DataFrame from the
                                            '2_1_Definition_Processes' sheet.
    """
    from plotly.subplots import make_subplots

    PROCESS_TYPE_COLUMN_NAME = 'Process_Type'
    has_type_column = PROCESS_TYPE_COLUMN_NAME in process_definitions.columns
    if not has_type_column:
        print(f"Warning: Column '{PROCESS_TYPE_COLUMN_NAME}' not found. Smart titles disabled.")

    process_options = {p.Name: p.ID for p in mfa_system_results.ProcessList if f"S_{p.ID}" in mfa_system_results.StockDict}
    if not process_options:
        print("No processes with stocks found to plot.")
        return

    element_items = mfa_system_results.Elements
    time_axis = mfa_system_results.IndexTable.Classification['Time'].Items
    fig = go.FigureWidget(make_subplots(rows=1, cols=3, subplot_titles=("Inflow", "Stock (S)", "Outflow")))

    def update_plot(process_name, element):
        pid = process_options[process_name]
        element_index = element_items.index(element)

        inflow_ts = sum(f.Values[:, element_index] for f in mfa_system_results.FlowDict.values() if f.P_End == pid)
        stock_ts = mfa_system_results.StockDict[f'S_{pid}'].Values[:, element_index]
        outflow_ts = sum(f.Values[:, element_index] for f in mfa_system_results.FlowDict.values() if f.P_Start == pid)

        subplot_titles = (f"Inflow to '{process_name}'", f"Stock in '{process_name}'", f"Outflow from '{process_name}'")
        if has_type_column:
            process_type = process_definitions.loc[process_definitions['ID'] == pid, PROCESS_TYPE_COLUMN_NAME].iloc[0]
            if process_type == 'Input': subplot_titles = ("Primary System Input", subplot_titles[1], subplot_titles[2])
            elif process_type == 'Output': subplot_titles = (subplot_titles[0], subplot_titles[1], "Final System Output (Sink)")

        with fig.batch_update():
            fig.data, fig.layout.annotations = [], []
            fig.add_trace(go.Scatter(x=time_axis, y=inflow_ts, mode='lines', name='Inflow'), row=1, col=1)
            fig.add_trace(go.Scatter(x=time_axis, y=stock_ts, mode='lines', name='Stock'), row=1, col=2)
            fig.add_trace(go.Scatter(x=time_axis, y=outflow_ts, mode='lines', name='Outflow'), row=1, col=3)
            fig.update_layout(title=f"Dynamics for Process: '{process_name}' | Element: {element.upper()}", height=400, showlegend=False)
            fig.update_xaxes(title_text="Year")
            fig.update_yaxes(title_text="Mass [Mg]", row=1, col=1)

    process_dropdown = Dropdown(options=list(process_options.keys()), description='Process:')
    element_dropdown = Dropdown(options=element_items, value=element_items[0], description='Element:')



def plot_dynamic_stock_composition(dsm_details, mfa_system_results):
    """
    Plots the composition of a dynamic stock over time, separating the
    decaying initial stock from the stock built up from new inflows.

    Args:
        dsm_details (dict): The detailed results dictionary from the DSM calculation.
        mfa_system_results (odym.MFAsystem): The solved MFA system object.
    """
    from ipywidgets import Checkbox

    process_options = list(dsm_details.keys())
    if not process_options:
        print("No DSM processes with detailed results found to plot.")
        return

    element_items = mfa_system_results.Elements
    time_axis = mfa_system_results.IndexTable.Classification['Time'].Items
    fig = go.FigureWidget()

    def update_plot(process_id, element, show_as_bars):
        details = dsm_details.get(process_id, {})
        element_index = element_items.index(element)

        # Get data from the details dictionary
        initial_stock_ts_all_elements = details.get('initial_stock_ts', np.zeros((len(time_axis), len(element_items))))
        inflow_stocks_material = details.get('inflow_stock_ts_by_cat', [])
        category_names = details.get('category_names', [])
        mean_lifetimes = details.get('mean_lifetimes', [])

        # Get composition of the mixed inflow for the new stock parts
        inflows = [f.Values for f in mfa_system_results.FlowDict.values() if f.P_End == process_id]
        total_inflow_values = sum(inflows) if inflows else np.zeros((len(time_axis), len(element_items)))
        inflow_comp_factor = np.divide(total_inflow_values[:, element_index], total_inflow_values[:, 0], out=np.zeros(len(time_axis)), where=total_inflow_values[:, 0] != 0)

        with fig.batch_update():
            fig.data = []
            chart_type = go.Bar if show_as_bars else go.Scatter
            stack_group_props = {'mode':'lines', 'line':dict(width=0.5), 'stackgroup':'one'} if not show_as_bars else {}

            # Plot the decaying initial stock
            initial_stock_ts_element = initial_stock_ts_all_elements[:, element_index]
            fig.add_trace(chart_type(x=time_axis, y=initial_stock_ts_element, name='Initial Stock (Decaying)', hoverinfo='x+y', **stack_group_props))

            # Plot the stock from new inflows, category by category
            for i, stock_ts_material in enumerate(inflow_stocks_material):
                stock_ts_element = stock_ts_material * inflow_comp_factor
                label = f"{category_names[i]} ({mean_lifetimes[i]} yrs)"
                fig.add_trace(chart_type(x=time_axis, y=stock_ts_element, name=label, hoverinfo='x+y', **stack_group_props))

            process_name = next((p.Name for p in mfa_system_results.ProcessList if p.ID == process_id), "")
            fig.update_layout(barmode='stack' if show_as_bars else None, title=f"Dynamic Stock Composition for Process: '{process_name}' ({element.upper()})",
                              xaxis_title="Year", yaxis_title=f"Stock in Mg")

    process_dropdown = Dropdown(options=process_options, description='Process:')
    element_dropdown = Dropdown(options=element_items, value=element_items[0], description='Element:')
    chart_type_checkbox = Checkbox(value=False, description='Show as Bar Chart')
    
    interact(update_plot, process_id=process_dropdown, element=element_dropdown, show_as_bars=chart_type_checkbox)
    display(fig)

def plot_fomp_dynamics(mfa_system_results, fomp_params_config):
    """
    Creates side-by-side line charts for Inflow, Stock, and Outflow
    for a process calculated with FOMP.

    Args:
        mfa_system_results (odym.MFAsystem): The solved MFA system object.
        fomp_params_config (dict): The configuration dictionary for FOMP processes,
                                   used to identify which processes to plot.
    """
    from plotly.subplots import make_subplots

    # Create a mapping of process names to IDs for the dropdown, only for FOMP processes
    process_options = {
        p.Name: p.ID
        for p in mfa_system_results.ProcessList
        if p.ID in fomp_params_config
    }
    if not process_options:
        print("No processes with FOMP parameters are defined in the configuration.")
        return

    element_items = mfa_system_results.Elements
    time_axis = mfa_system_results.IndexTable.Classification['Time'].Items
    fig = go.FigureWidget(make_subplots(rows=1, cols=3, subplot_titles=("Total Inflow", "Absolute Stock (S)", "Outflow (Mineralization)")))

    def update_plot(process_name, element):
        pid = process_options[process_name]
        element_index = element_items.index(element)

        # Get the time series data for the selected process
        inflow_ts = sum(f.Values[:, element_index] for f in mfa_system_results.FlowDict.values() if f.P_End == pid)
        stock_ts = mfa_system_results.StockDict.get(f'S_{pid}').Values[:, element_index]
        outflow_ts = sum(f.Values[:, element_index] for f in mfa_system_results.FlowDict.values() if f.P_Start == pid)

        with fig.batch_update():
            fig.data = [] # Clear existing data
            fig.add_trace(go.Scatter(x=time_axis, y=inflow_ts, mode='lines', name='Inflow'), row=1, col=1)
            fig.add_trace(go.Scatter(x=time_axis, y=stock_ts, mode='lines', name='Stock'), row=1, col=2)
            fig.add_trace(go.Scatter(x=time_axis, y=outflow_ts, mode='lines', name='Outflow'), row=1, col=3)

            title_text = f"FOMP Dynamics for Process: '{process_name}' | Element: {element.upper()}"
            fig.update_layout(title_text=title_text, height=400, showlegend=False)
            fig.update_xaxes(title_text="Year")
            fig.update_yaxes(title_text="Mass [Mg]", row=1, col=1)

    # Create widgets for interaction
    process_dropdown = Dropdown(options=list(process_options.keys()), description='Process:')
    element_dropdown = Dropdown(options=element_items, value=element_items[0], description='Element:')



def plot_flow_dynamics(mfa_system_results):
    """
    Creates an interactive line/bar chart to show the development of selected
    flows over time for a chosen element.

    Args:
        mfa_system_results (odym.MFAsystem): The solved MFA system object.
    """
    from ipywidgets import SelectMultiple, Checkbox

    # Create options for the widgets
    flow_options = sorted(list(mfa_system_results.FlowDict.keys()))
    if not flow_options:
        print("No flows found in the system to plot.")
        return
        
    element_items = mfa_system_results.Elements
    time_axis = mfa_system_results.IndexTable.Classification['Time'].Items
    
    # Use FigureWidget for efficient updates
    fig = go.FigureWidget()

    def update_plot(flows_to_show, element, show_as_bars):
        # Use batch_update for smooth interaction
        with fig.batch_update():
            fig.data = [] # Clear previous traces
            if not flows_to_show:
                fig.update_layout(title_text="Please select one or more flows to display.")
                return

            element_index = element_items.index(element)
            chart_type = go.Bar if show_as_bars else go.Scatter

            # Add a trace for each selected flow
            for flow_id in flows_to_show:
                flow_obj = mfa_system_results.FlowDict.get(flow_id)
                if flow_obj:
                    trace_props = dict(x=time_axis, y=flow_obj.Values[:, element_index], name=flow_id)
                    if not show_as_bars:
                        trace_props.update(mode='lines')
                    fig.add_trace(chart_type(**trace_props))
            
            # Update layout and title
            fig.update_layout(
                barmode='stack' if show_as_bars else 'overlay',
                title=f"Time Series for Selected Flows ({element.upper()})",
                xaxis_title="Year",
                yaxis_title="Mass in Mg",
                hovermode="x unified"
            )

    # Create widgets
    flow_selector = SelectMultiple(options=flow_options, value=[flow_options[0]] if flow_options else [], description='Flows:', rows=10)
    element_dropdown = Dropdown(options=element_items, value=element_items[0], description='Element:')
    chart_type_checkbox = Checkbox(value=False, description='Show as Bar Chart')




def plot_mc_distribution(df_results, column_name, unit='Mg', title=None):
    """
    Plot Monte Carlo distribution for a specific output parameter.
    
    Args:
        df_results (pd.DataFrame): Monte Carlo results DataFrame.
        column_name (str): Name of the column to plot.
        unit (str): Unit for the y-axis label.
        title (str, optional): Custom title for the plot.
    """
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import numpy as np
    
    if column_name not in df_results.columns:
        print(f"❌ Column '{column_name}' not found in MC results.")
        return
    
    data = df_results[column_name].dropna()
    
    if len(data) == 0:
        print(f"❌ No valid data found for column '{column_name}'.")
        return
    
    # Create subplots: histogram and boxplot
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=(f'Distribution of {column_name}', f'Box Plot of {column_name}'),
        vertical_spacing=0.1
    )
    
    # Histogram
    fig.add_trace(
        go.Histogram(
            x=data,
            nbinsx=30,
            name='Distribution',
            marker_color='#1f77b4',
            opacity=0.7
        ),
        row=1, col=1
    )
    
    # Box plot
    fig.add_trace(
        go.Box(
            y=data,
            name=column_name,
            marker_color='#ff7f0e',
            boxpoints='outliers'
        ),
        row=2, col=1
    )
    
    # Update layout
    fig.update_layout(
        title=title or f'Monte Carlo Results: {column_name}',
        height=600,
        showlegend=False
    )
    
    # Update axes
    fig.update_xaxes(title_text=f'{column_name} ({unit})', row=1, col=1)
    fig.update_yaxes(title_text='Count', row=1, col=1)
    fig.update_yaxes(title_text=f'{column_name} ({unit})', row=2, col=1)
    
    # Add statistics as annotations
    mean_val = data.mean()
    std_val = data.std()
    median_val = data.median()
    q25 = data.quantile(0.25)
    q75 = data.quantile(0.75)
    
    fig.add_annotation(
        text=f"Mean: {mean_val:.3f} {unit}<br>Std: {std_val:.3f} {unit}<br>Median: {median_val:.3f} {unit}",
        xref="paper", yref="paper",
        x=0.02, y=0.98,
        showarrow=False,
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor="black",
        borderwidth=1
    )
    
    fig.show()

def plot_mc_sensitivity_scatter(df_results, input_param_name, output_param_name, unit='Mg', title=None):
    """
    Plot sensitivity analysis scatter plot for Monte Carlo results.
    
    Args:
        df_results (pd.DataFrame): Monte Carlo results DataFrame.
        input_param_name (str): Name of the input parameter column.
        output_param_name (str): Name of the output parameter column.
        unit (str): Unit for the output parameter.
        title (str, optional): Custom title for the plot.
    """
    import plotly.graph_objects as go
    import plotly.express as px
    
    if input_param_name not in df_results.columns or output_param_name not in df_results.columns:
        print(f"❌ Required columns not found in MC results.")
        return
    
    # Create scatter plot
    fig = px.scatter(
        df_results,
        x=input_param_name,
        y=output_param_name,
        title=title or f'Sensitivity: {input_param_name} vs {output_param_name}',
        labels={
            input_param_name: input_param_name,
            output_param_name: f'{output_param_name} ({unit})'
        }
    )
    
    # Add trend line
    fig.add_trace(
        go.Scatter(
            x=df_results[input_param_name],
            y=df_results[output_param_name].rolling(window=10).mean(),
            mode='lines',
            name='Trend',
            line=dict(color='red', width=2)
        )
    )
    
    # Calculate correlation
    correlation = df_results[input_param_name].corr(df_results[output_param_name])
    
    fig.add_annotation(
        text=f"Correlation: {correlation:.3f}",
        xref="paper", yref="paper",
        x=0.02, y=0.98,
        showarrow=False,
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor="black",
        borderwidth=1
    )
    
    fig.show()

def plot_mc_correlation_matrix(df_results, parameter_columns=None, title=None):
    """
    Plot correlation matrix for Monte Carlo parameters.
    
    Args:
        df_results (pd.DataFrame): Monte Carlo results DataFrame.
        parameter_columns (list, optional): List of parameter columns to include.
        title (str, optional): Custom title for the plot.
    """
    import plotly.graph_objects as go
    import numpy as np
    
    if parameter_columns is None:
        # Use all numeric columns
        parameter_columns = df_results.select_dtypes(include=[np.number]).columns.tolist()
    
    # Filter to only include columns that exist
    available_columns = [col for col in parameter_columns if col in df_results.columns]
    
    if len(available_columns) < 2:
        print("❌ Need at least 2 numeric columns for correlation matrix.")
        return
    
    # Calculate correlation matrix
    corr_matrix = df_results[available_columns].corr()
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=corr_matrix.columns,
        y=corr_matrix.columns,
        colorscale='RdBu',
        zmid=0,
        text=np.round(corr_matrix.values, 3),
        texttemplate="%{text}",
        textfont={"size": 10},
        hoverongaps=False
    ))
    
    fig.update_layout(
        title=title or 'Monte Carlo Parameter Correlation Matrix',
        xaxis_title="Parameters",
        yaxis_title="Parameters",
        height=600
    )
    
    fig.show()

def plot_mc_scenario_comparison(df_results_list, scenario_names, output_column, unit='Mg', title=None):
    """
    Compare Monte Carlo results across different scenarios.
    
    Args:
        df_results_list (list): List of Monte Carlo DataFrames for each scenario.
        scenario_names (list): List of scenario names.
        output_column (str): Name of the output column to compare.
        unit (str): Unit for the output parameter.
        title (str, optional): Custom title for the plot.
    """
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    
    if len(df_results_list) != len(scenario_names):
        print("❌ Number of DataFrames must match number of scenario names.")
        return
    
    # Create subplots: box plots and violin plots
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Box Plot Comparison', 'Violin Plot Comparison'),
        vertical_spacing=0.1
    )
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    for i, (df, scenario_name) in enumerate(zip(df_results_list, scenario_names)):
        if output_column not in df.columns:
            print(f"❌ Column '{output_column}' not found in scenario '{scenario_name}'.")
            continue
        
        data = df[output_column].dropna()
        
        # Box plot
        fig.add_trace(
            go.Box(
                y=data,
                name=scenario_name,
                marker_color=colors[i % len(colors)],
                boxpoints='outliers'
            ),
            row=1, col=1
        )
        
        # Violin plot
        fig.add_trace(
            go.Violin(
                y=data,
                name=scenario_name,
                marker_color=colors[i % len(colors)],
                opacity=0.7
            ),
            row=2, col=1
        )
    
    fig.update_layout(
        title=title or f'Scenario Comparison: {output_column}',
        height=700,
        showlegend=True
    )
    
    fig.update_yaxes(title_text=f'{output_column} ({unit})', row=1, col=1)
    fig.update_yaxes(title_text=f'{output_column} ({unit})', row=2, col=1)
    
    fig.show()

def plot_mc_summary_dashboard(df_results, key_columns=None, title=None):
    """
    Create a comprehensive Monte Carlo summary dashboard.
    
    Args:
        df_results (pd.DataFrame): Monte Carlo results DataFrame.
        key_columns (list, optional): List of key output columns to highlight.
        title (str, optional): Custom title for the dashboard.
    """
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import numpy as np
    
    if key_columns is None:
        # Use columns that look like outputs (not inputs)
        numeric_cols = df_results.select_dtypes(include=[np.number]).columns.tolist()
        key_columns = [col for col in numeric_cols if 'final' in col.lower() or 'stock' in col.lower() or 'flow' in col.lower()]
    
    if len(key_columns) == 0:
        print("❌ No key output columns found for dashboard.")
        return
    
    # Create subplots
    n_cols = min(3, len(key_columns))
    n_rows = (len(key_columns) + n_cols - 1) // n_cols
    
    fig = make_subplots(
        rows=n_rows, cols=n_cols,
        subplot_titles=key_columns,
        vertical_spacing=0.1,
        horizontal_spacing=0.05
    )
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    for i, col in enumerate(key_columns):
        if col not in df_results.columns:
            continue
        
        row = (i // n_cols) + 1
        col_idx = (i % n_cols) + 1
        
        data = df_results[col].dropna()
        
        if len(data) > 0:
            # Histogram
            fig.add_trace(
                go.Histogram(
                    x=data,
                    nbinsx=20,
                    name=col,
                    marker_color=colors[i % len(colors)],
                    opacity=0.7,
                    showlegend=False
                ),
                row=row, col=col_idx
            )
    
    fig.update_layout(
        title=title or 'Monte Carlo Results Summary Dashboard',
        height=300 * n_rows,
        showlegend=False
    )
    
    fig.show()

def plot_mc_confidence_intervals(df_results, output_column, confidence_levels=[0.05, 0.25, 0.5, 0.75, 0.95], unit='Mg', title=None):
    """
    Plot confidence intervals for Monte Carlo results.
    
    Args:
        df_results (pd.DataFrame): Monte Carlo results DataFrame.
        output_column (str): Name of the output column.
        confidence_levels (list): List of confidence levels to plot.
        unit (str): Unit for the output parameter.
        title (str, optional): Custom title for the plot.
    """
    import plotly.graph_objects as go
    import numpy as np
    
    if output_column not in df_results.columns:
        print(f"❌ Column '{output_column}' not found in MC results.")
        return
    
    data = df_results[output_column].dropna()
    
    if len(data) == 0:
        print(f"❌ No valid data found for column '{output_column}'.")
        return
    
    # Calculate percentiles
    percentiles = [data.quantile(level) for level in confidence_levels]
    
    # Create confidence interval plot
    fig = go.Figure()
    
    # Add confidence intervals
    for i, (level, percentile) in enumerate(zip(confidence_levels, percentiles)):
        color_intensity = 1 - (i / len(confidence_levels)) * 0.7
        fig.add_trace(go.Scatter(
            x=[percentile, percentile],
            y=[0, 1],
            mode='lines',
            line=dict(color=f'rgba(0,0,255,{color_intensity})', width=3),
            name=f'{int(level*100)}% percentile',
            showlegend=True
        ))
    
    # Add mean line
    mean_val = data.mean()
    fig.add_trace(go.Scatter(
        x=[mean_val, mean_val],
        y=[0, 1],
        mode='lines',
        line=dict(color='red', width=4, dash='dash'),
        name='Mean',
        showlegend=True
    ))
    
    # Add histogram
    fig.add_trace(go.Histogram(
        x=data,
        nbinsx=30,
        name='Distribution',
        marker_color='rgba(0,0,255,0.3)',
        yaxis='y2'
    ))
    
    fig.update_layout(
        title=title or f'Confidence Intervals: {output_column}',
        xaxis_title=f'{output_column} ({unit})',
        yaxis_title='Confidence Level',
        yaxis2=dict(
            title='Count',
            overlaying='y',
            side='right'
        ),
        height=500
    )
    
    # Add statistics as annotations
    stats_text = f"Mean: {mean_val:.3f} {unit}<br>Std: {data.std():.3f} {unit}<br>Range: {data.min():.3f} - {data.max():.3f} {unit}"
    
    fig.add_annotation(
        text=stats_text,
        xref="paper", yref="paper",
        x=0.02, y=0.98,
        showarrow=False,
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor="black",
        borderwidth=1
    )
    
    fig.show()

def plot_mc_parameter_importance(df_results, output_column, input_columns=None, method='correlation', title=None):
    """
    Plot parameter importance analysis for Monte Carlo results.
    
    Args:
        df_results (pd.DataFrame): Monte Carlo results DataFrame.
        output_column (str): Name of the output column.
        input_columns (list, optional): List of input parameter columns.
        method (str): Method for importance calculation ('correlation' or 'regression').
        title (str, optional): Custom title for the plot.
    """
    import plotly.graph_objects as go
    import numpy as np
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import StandardScaler
    
    if output_column not in df_results.columns:
        print(f"❌ Column '{output_column}' not found in MC results.")
        return
    
    if input_columns is None:
        # Use all numeric columns except the output column
        numeric_cols = df_results.select_dtypes(include=[np.number]).columns.tolist()
        input_columns = [col for col in numeric_cols if col != output_column]
    
    # Filter to only include columns that exist
    available_inputs = [col for col in input_columns if col in df_results.columns]
    
    if len(available_inputs) == 0:
        print("❌ No input parameters found for importance analysis.")
        return
    
    # Calculate importance
    importance_scores = []
    
    if method == 'correlation':
        for col in available_inputs:
            correlation = abs(df_results[col].corr(df_results[output_column]))
            importance_scores.append(correlation)
    elif method == 'regression':
        # Use standardized regression coefficients
        X = df_results[available_inputs].fillna(0)
        y = df_results[output_column].fillna(0)
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        model = LinearRegression()
        model.fit(X_scaled, y)
        
        importance_scores = abs(model.coef_)
    else:
        print(f"❌ Unknown method '{method}'. Using correlation.")
        for col in available_inputs:
            correlation = abs(df_results[col].corr(df_results[output_column]))
            importance_scores.append(correlation)
    
    # Create importance plot
    fig = go.Figure(data=go.Bar(
        x=available_inputs,
        y=importance_scores,
        marker_color='#1f77b4'
    ))
    
    fig.update_layout(
        title=title or f'Parameter Importance: {output_column}',
        xaxis_title="Parameters",
        yaxis_title=f"Importance ({method})",
        height=500
    )
    
    fig.show()


def plot_individual_flows(mfa_system_results):
    """
    Creates an interactive plot for individual flow analysis with dropdown selection.
    Users can select specific flows to analyze their time evolution.

    Args:
        mfa_system_results (odym.MFAsystem): The solved MFA system object.
    """
    from ipywidgets import SelectMultiple, Dropdown, Checkbox
    
    # Get available flows and elements
    flow_options = sorted(list(mfa_system_results.FlowDict.keys()))
    element_items = mfa_system_results.Elements
    time_items = mfa_system_results.IndexTable.Classification['Time'].Items
    
    if not flow_options:
        print("No flows found in the system to plot.")
        return
    
    fig = go.FigureWidget()

    def update_plot(flows_to_show, element, show_as_bars, show_cumulative):
        with fig.batch_update():
            fig.data = []
            
            if not flows_to_show:
                fig.update_layout(title_text="Please select one or more flows to display.")
                return

            element_index = element_items.index(element)
            chart_type = go.Bar if show_as_bars else go.Scatter

            for flow_id in flows_to_show:
                flow_obj = mfa_system_results.FlowDict.get(flow_id)
                if flow_obj:
                    values = flow_obj.Values[:, element_index]
                    
                    if show_cumulative:
                        values = np.cumsum(values)
                        name_suffix = " (Cumulative)"
                    else:
                        name_suffix = ""
                    
                    trace_props = dict(
                        x=time_items, 
                        y=values, 
                        name=f"{flow_id}{name_suffix}"
                    )
                    
                    if not show_as_bars:
                        trace_props.update(mode='lines+markers')
                    
                    fig.add_trace(chart_type(**trace_props))
            
            # Update layout
            y_title = "Cumulative Mass in Mg" if show_cumulative else "Mass in Mg"
            title = f"Flow Analysis ({element.upper()})"
            if show_cumulative:
                title += " - Cumulative Values"
            
            fig.update_layout(
                barmode='stack' if show_as_bars else 'overlay',
                title=title,
                xaxis_title="Year",
                yaxis_title=y_title,
                hovermode="x unified",
                height=500
            )

    # Create widgets
    flow_selector = SelectMultiple(
        options=flow_options, 
        value=[flow_options[0]] if flow_options else [], 
        description='Select Flows:', 
        rows=8
    )
    element_dropdown = Dropdown(
        options=element_items, 
        value=element_items[0], 
        description='Element:'
    )
    chart_type_checkbox = Checkbox(
        value=False, 
        description='Show as Bar Chart'
    )
    cumulative_checkbox = Checkbox(
        value=False, 
        description='Show Cumulative Values'
    )

    interact(
        update_plot, 
        flows_to_show=flow_selector, 
        element=element_dropdown, 
        show_as_bars=chart_type_checkbox,
        show_cumulative=cumulative_checkbox
    )
    display(fig)


def plot_individual_stocks(mfa_system_results, dsm_params=None, fomp_params=None, df_mc_results=None):
    """
    Creates an interactive plot for individual stock analysis with dropdown selection.
    Users can select specific stocks to analyze their time evolution.

    Args:
        mfa_system_results (odym.MFAsystem): The solved MFA system object.
        dsm_params (dict, optional): DSM parameters to identify DSM processes.
        fomp_params (dict, optional): FOMP parameters to identify FOMP processes.
        df_mc_results (DataFrame, optional): MC results. If provided, function will print a message and return.
    """
    if df_mc_results is not None:
        print("[INFO] MC scenario plotting is not supported in plot_individual_stocks. Please use plot_mc_scenario_comparison directly.")
        return
    from ipywidgets import SelectMultiple, Dropdown, Checkbox
    
    # Get available stocks (exclude delta stocks)
    stock_names = [name for name in mfa_system_results.StockDict.keys() if name.startswith('S_')]
    process_names = [p.Name for p in mfa_system_results.ProcessList if f'S_{p.ID}' in stock_names]
    
    element_items = mfa_system_results.Elements
    time_items = mfa_system_results.IndexTable.Classification['Time'].Items
    
    if not stock_names:
        print("No stocks found in the system to plot.")
        return
    
    # Identify process types for color coding
    dsm_processes = set(dsm_params.keys()) if dsm_params else set()
    fomp_processes = set(fomp_params.keys()) if fomp_params else set()
    
    fig = go.FigureWidget()

    def update_plot(stocks_to_show, element, show_as_bars, show_delta):
        with fig.batch_update():
            fig.data = []
            
            if not stocks_to_show:
                fig.update_layout(title_text="Please select one or more stocks to display.")
                return

            element_index = element_items.index(element)
            chart_type = go.Bar if show_as_bars else go.Scatter

            for i, stock_name in enumerate(stocks_to_show):
                stock_obj = mfa_system_results.StockDict[stock_name]
                values = stock_obj.Values[:, element_index]
                
                # Determine line style based on process type
                process_id = int(stock_name.split('_')[1])
                if process_id in dsm_processes:
                    line_style = dict(color='#ff7f0e', width=3, dash='dash')  # Orange, dashed
                    name_prefix = "DSM: "
                elif process_id in fomp_processes:
                    line_style = dict(color='#2ca02c', width=3, dash='dot')   # Green, dot-dash
                    name_prefix = "FOMP: "
                else:
                    line_style = dict(color='#1f77b4', width=2)              # Blue, solid
                    name_prefix = ""
                
                # Show delta stocks if requested
                if show_delta:
                    delta_stock_name = f"dS_{process_id}"
                    if delta_stock_name in mfa_system_results.StockDict:
                        delta_obj = mfa_system_results.StockDict[delta_stock_name]
                        values = delta_obj.Values[:, element_index]
                        name_suffix = " (ΔS)"
                    else:
                        name_suffix = ""
                else:
                    name_suffix = ""
                
                trace_props = dict(
                    x=time_items, 
                    y=values, 
                    name=f"{name_prefix}{process_names[i]}{name_suffix}",
                    line=line_style
                )
                
                if not show_as_bars:
                    trace_props.update(mode='lines+markers')
                
                fig.add_trace(chart_type(**trace_props))
            
            # Update layout
            y_title = "Stock Change (ΔS) in Mg" if show_delta else "Stock (S) in Mg"
            title = f"Stock Analysis ({element.upper()})"
            if show_delta:
                title += " - Stock Changes"
            
            fig.update_layout(
                barmode='stack' if show_as_bars else 'overlay',
                title=title,
                xaxis_title="Year",
                yaxis_title=y_title,
                hovermode="x unified",
                height=500
            )

    # Create widgets
    stock_selector = SelectMultiple(
        options=process_names, 
        value=[process_names[0]] if process_names else [], 
        description='Select Stocks:', 
        rows=8
    )
    element_dropdown = Dropdown(
        options=element_items, 
        value=element_items[0], 
        description='Element:'
    )
    chart_type_checkbox = Checkbox(
        value=False, 
        description='Show as Bar Chart'
    )
    delta_checkbox = Checkbox(
        value=False, 
        description='Show Stock Changes (ΔS)'
    )

    interact(
        update_plot, 
        stocks_to_show=stock_selector, 
        element=element_dropdown, 
        show_as_bars=chart_type_checkbox,
        show_delta=delta_checkbox
    )
    display(fig)


def plot_stock_bars_by_year(mfa_system_results):
    """
    Plots a bar chart of all defined stocks for a selected year and element.
    Each bar represents the stock value for a process in the selected year/element.
    Supports both positive and negative values.

    Args:
        mfa_system_results (odym.MFAsystem): The solved MFA system object.
    """
    from ipywidgets import Dropdown
    import plotly.graph_objects as go
    from IPython.display import display

    # Get stock names and process names (exclude delta stocks)
    stock_names = [name for name in mfa_system_results.StockDict.keys() if name.startswith('S_')]
    process_names = [p.Name for p in mfa_system_results.ProcessList if f'S_{p.ID}' in stock_names]
    process_ids = [p.ID for p in mfa_system_results.ProcessList if f'S_{p.ID}' in stock_names]

    element_items = list(mfa_system_results.Elements)
    time_items = list(mfa_system_results.IndexTable.Classification['Time'].Items)

    fig = go.FigureWidget()

    def update_plot(year, element):
        year_index = time_items.index(year)
        element_index = element_items.index(element)
        stock_values = []
        for pid in process_ids:
            stock_obj = mfa_system_results.StockDict.get(f'S_{pid}', None)
            if stock_obj is not None:
                value = stock_obj.Values[year_index, element_index]
                stock_values.append(value)
            else:
                stock_values.append(0)
        # Color bars based on sign
        colors = ['#2ca02c' if v >= 0 else '#d62728' for v in stock_values]
        with fig.batch_update():
            fig.data = []
            fig.add_trace(go.Bar(x=process_names, y=stock_values, marker_color=colors))
            fig.update_layout(
                title=f"Stock Values by Process for {element.upper()} in {year}",
                yaxis_title="Stock in Mg (can be positive or negative)",
                xaxis_title="Process",
                height=500,
                shapes=[dict(type='line', y0=0, y1=0, x0=-0.5, x1=len(process_names)-0.5, line=dict(color='black', width=2))],
            )

    # Create widgets
    year_dropdown = Dropdown(options=time_items, value=time_items[0], description='Year:')
    element_dropdown = Dropdown(options=element_items, value=element_items[0], description='Element:')

    interact(update_plot, year=year_dropdown, element=element_dropdown)
    display(fig)
