# -*- coding: utf-8 -*-
"""
Plotting Module for the BioDYM MFA Model.

This file contains all functions responsible for generating the various
interactive visualizations for the model results, including Sankey diagrams,
time-series plots, and Monte Carlo analysis plots.
"""
import numpy as np
import plotly.graph_objects as go
from ipywidgets import interact, IntSlider, Dropdown
from IPython.display import display


def plot_mass_balance_error(mfa_system_results):
    """
    Creates an interactive bar chart showing the mass balance error for each process.
    Error = Inflows - Outflows - dS. An error of 0 means perfect balance.

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
                shapes=[dict(type='line', y0=0, y1=0, x0=-0.5, x1=len(process_names)-0.5, line=dict(color='black', width=2))] # Zero line
            )

    # Create widgets
    year_slider = IntSlider(min=time_items[0], max=time_items[-1], step=1, value=time_items[0], description='Year')
    element_dropdown = Dropdown(options=element_items, value=element_items[0], description='Element:')
    
    interact(update_plot, year=year_slider, element=element_dropdown)
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




def plot_mc_distribution(df_results, column_name, unit='Mg'):
    """
    Creates an interactive histogram to show the distribution of a key output
    variable from the Monte Carlo simulation, including mean and CIs.

    Args:
        df_results (pd.DataFrame): The DataFrame containing MC results.
        column_name (str): The name of the KPI column to plot.
        unit (str): The unit of the KPI for labeling.
    """
    mean_val = df_results[column_name].mean()
    p5 = df_results[column_name].quantile(0.05)
    p95 = df_results[column_name].quantile(0.95)

    fig = go.Figure()
    fig.add_trace(go.Histogram(x=df_results[column_name], name='Distribution', nbinsx=50))
    fig.add_vline(x=mean_val, line_width=3, line_dash="dash", line_color="red",
                  annotation_text=f"Mean: {mean_val:.2f} {unit}", annotation_position="top right")
    fig.add_vline(x=p5, line_width=2, line_dash="dot", line_color="green",
                  annotation_text=f"5th Percentile: {p5:.2f}", annotation_position="top left")
    fig.add_vline(x=p95, line_width=2, line_dash="dot", line_color="green",
                  annotation_text=f"95th Percentile: {p95:.2f}")

    fig.update_layout(title_text=f'Distribution of "{column_name}"', xaxis_title_text=f'Value in {unit}',
                      yaxis_title_text='Frequency (Number of Runs)', legend_title_text='Metrics')
    fig.show()


def plot_mc_sensitivity_scatter(df_results, input_param_name, output_param_name, unit='Mg'):
    """
    Creates a scatter plot to visualize the relationship between an uncertain
    input parameter and a key output variable. Includes a trendline.

    Args:
        df_results (pd.DataFrame): The DataFrame containing MC results.
        input_param_name (str): The name of the uncertain input parameter (x-axis).
        output_param_name (str): The name of the output KPI (y-axis).
        unit (str): The unit of the output KPI for labeling.
    """
    import plotly.express as px

    if input_param_name not in df_results.columns:
        print(f"ERROR for scatter plot: Input parameter '{input_param_name}' was not stored in the results.")
        return

    fig = px.scatter(df_results, x=input_param_name, y=output_param_name,
                     title=f'Sensitivity of "{output_param_name}" to "{input_param_name}"',
                     labels={
                         input_param_name: f'Sampled Value of {input_param_name}',
                         output_param_name: f'Result for {output_param_name} [{unit}]'
                     },
                     trendline="ols",
                     trendline_color_override="red")
    fig.show()
