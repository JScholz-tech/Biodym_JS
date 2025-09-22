# -*- coding: utf-8 -*-
"""
Dynamics Plotting Module.

This file contains functions for plotting time-series data, such as
stock and process dynamics.
"""

import numpy as np
import plotly.graph_objects as go
from ipywidgets import interact, IntSlider, Dropdown, SelectMultiple, Checkbox
from IPython.display import display
from plotly.subplots import make_subplots
import pandas as pd


def plot_dsm_stock_details(mfa_system_results, dsm_params, dsm_details):
    """
    Creates enhanced DSM stock evolution plots with both individual and cumulative views.
    Shows initial stock decay, new stock accumulation by category, and lifetime analysis.

    Args:
        mfa_system_results (odym.MFAsystem): The solved MFA system object.
        dsm_params (dict): DSM parameters configuration.
        dsm_details (dict): Detailed DSM calculation results.
    """
    if not dsm_params:
        print("No DSM processes found to plot.")
        return

    from ipywidgets import Dropdown, HBox, VBox, HTML, Layout, Button, Checkbox
    from IPython.display import display
    import os
    from datetime import datetime

    time_items = mfa_system_results.IndexTable.Classification["Time"].Items
    element_items = mfa_system_results.Elements

    # Define enhanced color scheme
    colors = {
        'initial_stock': '#ff7f0e',      # Orange for decaying initial stock
        'total_stock': '#d62728',        # Red for total stock
        'background': '#f9f9f9',         # Light background
        'grid': '#e1e1e1'               # Light grid
    }

    fig = go.FigureWidget()

    def update_plot(process_id, element, view_mode, show_lifetimes):
        if process_id not in dsm_details:
            print(f"No detailed results for process {process_id}")
            return

        element_index = element_items.index(element)
        details = dsm_details[process_id]

        with fig.batch_update():
            fig.data = []

            # Get stock components
            initial_stock_ts = details.get(
                "initial_stock_ts", np.zeros((len(time_items), len(element_items)))
            )
            inflow_stocks_material = details.get("inflow_stock_ts_by_cat", [])
            category_names = details.get("category_names", [])
            lifetimes = details.get("lifetimes", [])

            # Plot initial stock decay
            initial_stock_element = initial_stock_ts[:, element_index]
            fig.add_trace(
                go.Scatter(
                    x=time_items,
                    y=initial_stock_element,
                    mode="lines",
                    name="Initial Stock (Decaying)",
                    line=dict(color=colors['initial_stock'], width=2, dash="dash"),
                    hovertemplate="<b>Initial Stock</b><br>Year: %{x}<br>Mass: %{y:.2f} Mg<extra></extra>"
                )
            )

            # Plot new stock accumulation by category
            total_inflow_stock = np.zeros(len(time_items))
            for i, stock_ts_material in enumerate(inflow_stocks_material):
                # Convert material stock to element stock using composition
                inflows = [
                    f.Values
                    for f in mfa_system_results.FlowDict.values()
                    if f.P_End == process_id
                ]
                total_inflow_values = (
                    sum(inflows)
                    if inflows
                    else np.zeros((len(time_items), len(element_items)))
                )
                inflow_comp_factor = np.divide(
                    total_inflow_values[:, element_index],
                    total_inflow_values[:, 0],
                    out=np.zeros(len(time_items)),
                    where=total_inflow_values[:, 0] != 0,
                )

                stock_ts_element = stock_ts_material * inflow_comp_factor
                total_inflow_stock += stock_ts_element

                # Create category name with lifetime info if requested
                if show_lifetimes and i < len(lifetimes):
                    category_display = f"{category_names[i]} ({lifetimes[i]} yrs)"
                else:
                    category_display = category_names[i]

                if view_mode == "Individual":
                    # Show individual category lines
                    fig.add_trace(
                        go.Scatter(
                            x=time_items,
                            y=stock_ts_element,
                            mode="lines",
                            name=f"New Stock: {category_display}",
                            line=dict(width=2),
                            hovertemplate=f"<b>{category_display}</b><br>Year: %{{x}}<br>Mass: %{{y:.2f}} Mg<extra></extra>"
                        )
                    )
                else:  # Cumulative
                    # Show cumulative stock
                    cumulative_stock = np.cumsum(stock_ts_element)
                    fig.add_trace(
                        go.Scatter(
                            x=time_items,
                            y=cumulative_stock,
                            mode="lines",
                            name=f"Cumulative: {category_display}",
                            line=dict(width=2),
                            hovertemplate=f"<b>Cumulative {category_display}</b><br>Year: %{{x}}<br>Mass: %{{y:.2f}} Mg<extra></extra>"
                        )
                    )

            # Plot total stock
            total_stock = initial_stock_element + total_inflow_stock
            fig.add_trace(
                go.Scatter(
                    x=time_items,
                    y=total_stock,
                    mode="lines+markers",
                    name="Total Stock",
                    line=dict(color=colors['total_stock'], width=4),
                    marker=dict(size=6),
                    hovertemplate="<b>Total Stock</b><br>Year: %{x}<br>Mass: %{y:.2f} Mg<extra></extra>"
                )
            )

            # Update layout with enhanced styling
            process_name = next(
                (p.Name for p in mfa_system_results.ProcessList if p.ID == process_id),
                f"Process {process_id}",
            )
            
            view_title = "Individual Categories" if view_mode == "Individual" else "Cumulative Stock"
            fig.update_layout(
                title=f"DSM Stock Evolution: {process_name} ({element.upper()}) - {view_title}",
                xaxis_title="Year",
                yaxis_title="Stock in Mg",
                hovermode="x unified",
                plot_bgcolor=colors['background'],
                paper_bgcolor='white',
                font=dict(size=12),
                showlegend=True,
                legend=dict(
                    bgcolor='rgba(255,255,255,0.8)',
                    bordercolor='rgba(0,0,0,0.2)',
                    borderwidth=1
                ),
                xaxis=dict(
                    gridcolor=colors['grid'],
                    showgrid=True,
                    zeroline=True,
                    zerolinecolor='rgba(0,0,0,0.3)'
                ),
                yaxis=dict(
                    gridcolor=colors['grid'],
                    showgrid=True,
                    zeroline=True,
                    zerolinecolor='rgba(0,0,0,0.3)'
                )
            )

    # Create enhanced widgets
    process_dropdown = Dropdown(
        options=list(dsm_params.keys()), 
        description="DSM Process:",
        style={'description_width': '120px'}
    )
    element_dropdown = Dropdown(
        options=element_items, 
        value=element_items[0], 
        description="Element:",
        style={'description_width': '80px'}
    )
    view_dropdown = Dropdown(
        options=["Individual", "Cumulative"],
        value="Individual",
        description="View Mode:",
        style={'description_width': '100px'}
    )
    lifetime_checkbox = Checkbox(
        value=True,
        description="Show Lifetimes",
        style={'description_width': '120px'}
    )

    # Create export button
    export_button = Button(
        description="Export Plot",
        button_style='info',
        tooltip='Export current plot as PNG'
    )

    def export_plot():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"dsm_stock_analysis_{timestamp}.png"
        
        # Create export directory if it doesn't exist
        export_dir = "exports/dsm_analysis"
        os.makedirs(export_dir, exist_ok=True)
        
        filepath = os.path.join(export_dir, filename)
        
        try:
            fig.write_image(filepath, width=1200, height=800)
            print(f"✅ Plot exported to: {filepath}")
        except Exception as e:
            print(f"⚠️ Export failed: {e}")
            print("💡 Ensure 'kaleido' is available (uv sync)")

    export_button.on_click(lambda b: export_plot())

    # Create widget layout
    controls = HBox([
        VBox([process_dropdown, element_dropdown], layout=Layout(width='300px')),
        VBox([view_dropdown, lifetime_checkbox], layout=Layout(width='200px')),
        VBox([export_button], layout=Layout(width='150px'))
    ], layout=Layout(justify_content='space-between'))

    # Display controls and plot
    display(controls)
    display(fig)

    # Set up interactions
    interact(
        update_plot, 
        process_id=process_dropdown, 
        element=element_dropdown,
        view_mode=view_dropdown,
        show_lifetimes=lifetime_checkbox
    )

def plot_fomp_stock_details(mfa_system_results, fomp_params):
    """
    Creates detailed stock evolution plots specifically for FOMP processes.
    Shows organic matter accumulation and mineralization with enhanced design.

    Args:
        mfa_system_results (odym.MFAsystem): The solved MFA system object.
        fomp_params (dict): FOMP parameters configuration.
    """
    if not fomp_params:
        print("No FOMP processes found to plot.")
        return

    from ipywidgets import Dropdown, HBox, VBox, HTML, Layout, Button
    from IPython.display import display
    import os
    from datetime import datetime

    time_items = mfa_system_results.IndexTable.Classification["Time"].Items
    element_items = mfa_system_results.Elements

    # Define consistent color scheme
    colors = {
        'stock': '#2ca02c',      # Green for organic matter stock
        'input': '#1f77b4',      # Blue for input
        'output': '#d62728',      # Red for mineralization
        'background': '#f9f9f9'   # Light background
    }

    fig = go.FigureWidget()

    def update_plot(process_id, element, show_cumulative):
        element_index = element_items.index(element)

        with fig.batch_update():
            fig.data = []

            # Get stock data
            stock_obj = mfa_system_results.StockDict.get(f"S_{process_id}")
            if stock_obj is None:
                print(f"No stock data for process {process_id}")
                return

            stock_values = stock_obj.Values[:, element_index]

            # Get inflow and outflow data
            inflow_ts = sum(
                f.Values[:, element_index]
                for f in mfa_system_results.FlowDict.values()
                if f.P_End == process_id
            )
            outflow_ts = sum(
                f.Values[:, element_index]
                for f in mfa_system_results.FlowDict.values()
                if f.P_Start == process_id
            )

            # Plot stock evolution (always shown)
            fig.add_trace(
                go.Scatter(
                    x=time_items,
                    y=stock_values,
                    mode="lines+markers",
                    name="Organic Matter Stock",
                    line=dict(color=colors['stock'], width=3),
                    marker=dict(size=4),
                    hovertemplate="<b>Stock</b><br>Year: %{x}<br>Mass: %{y:.2f} Mg<extra></extra>"
                )
            )

            if show_cumulative == "Cumulative Values":
                # Plot cumulative inflow and outflow
                cumulative_inflow = np.cumsum(inflow_ts)
                cumulative_outflow = np.cumsum(outflow_ts)

                fig.add_trace(
                    go.Scatter(
                        x=time_items,
                        y=cumulative_inflow,
                        mode="lines+markers",
                        name="Cumulative Input",
                        line=dict(color=colors['input'], width=2, dash="dash"),
                        marker=dict(size=3),
                        hovertemplate="<b>Cumulative Input</b><br>Year: %{x}<br>Mass: %{y:.2f}} Mg<extra></extra>"
                    )
                )

                fig.add_trace(
                    go.Scatter(
                        x=time_items,
                        y=cumulative_outflow,
                        mode="lines+markers",
                        name="Cumulative Mineralization",
                        line=dict(color=colors['output'], width=2, dash="dot"),
                        marker=dict(size=3),
                        hovertemplate="<b>Cumulative Mineralization</b><br>Year: %{x}<br>Mass: %{y:.2f}} Mg<extra></extra>"
                    )
                )
            else:
                # Plot annual inflow and outflow
                fig.add_trace(
                    go.Scatter(
                        x=time_items,
                        y=inflow_ts,
                        mode="lines+markers",
                        name="Annual Input",
                        line=dict(color=colors['input'], width=2, dash="dash"),
                        marker=dict(size=3),
                        hovertemplate="<b>Annual Input</b><br>Year: %{x}<br>Mass: %{y:.2f}} Mg<extra></extra>"
                    )
                )

                fig.add_trace(
                    go.Scatter(
                        x=time_items,
                        y=outflow_ts,
                        mode="lines+markers",
                        name="Annual Mineralization",
                        line=dict(color=colors['output'], width=2, dash="dot"),
                        marker=dict(size=3),
                        hovertemplate="<b>Annual Mineralization</b><br>Year: %{x}<br>Mass: %{y:.2f}} Mg<extra></extra>"
                    )
                )

            process_name = next(
                (p.Name for p in mfa_system_results.ProcessList if p.ID == process_id),
                f"Process {process_id}",
            )
            
            # Enhanced layout
            fig.update_layout(
                title=dict(
                    text=f"FOMP Analysis: {process_name} ({element.upper()})",
                    x=0.5,
                    font=dict(size=16, color='#2c3e50')
                ),
                xaxis_title="Year",
                yaxis_title=f"Mass ({element.upper()}) in Mg",
                hovermode="x unified",
                height=500,
                plot_bgcolor='white',
                paper_bgcolor='white',
                font=dict(size=12),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                margin=dict(l=80, r=80, t=100, b=80)
            )
            
            # Enhanced axes
            fig.update_xaxes(
                showgrid=True,
                gridwidth=1,
                gridcolor='#e1e5e9',
                zeroline=True,
                zerolinecolor='#2c3e50',
                zerolinewidth=1
            )
            fig.update_yaxes(
                showgrid=True,
                gridwidth=1,
                gridcolor='#e1e5e9',
                zeroline=True,
                zerolinecolor='#2c3e50',
                zerolinewidth=1
            )

    def export_plot():
        """Export the current plot with enhanced options"""
        try:
            # Create export folder with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_folder = f"exports/fomp_analysis/{timestamp}"
            os.makedirs(export_folder, exist_ok=True)
            
            # Generate filename with current parameters
            current_process = process_dropdown.value
            current_element = element_dropdown.value
            
            filename = f"fomp_{current_process}_{current_element}.png"
            filepath = os.path.join(export_folder, filename)
            
            # Export the plot
            fig.write_image(filepath, width=1200, height=600, scale=2)
            print(f"✅ FOMP analysis exported to: {filepath}")
            print(f"📁 Export folder: {export_folder}")
            
        except Exception as e:
            print(f"❌ Export failed: {e}")
            print("💡 Ensure 'kaleido' is available (uv sync)")

    # Create enhanced widgets
    process_dropdown = Dropdown(
        options=list(fomp_params.keys()),
        description="FOMP Process:",
        style={'description_width': '120px'},
        layout=Layout(width='300px')
    )
    
    element_dropdown = Dropdown(
        options=element_items,
        value=element_items[0],
        description="Element:",
        style={'description_width': '80px'},
        layout=Layout(width='200px')
    )
    
    cumulative_checkbox = Dropdown(
        options=["Annual Values", "Cumulative Values"],
        value="Annual Values",
        description="Display:",
        style={'description_width': '80px'},
        layout=Layout(width='200px')
    )
    
    export_button = Button(
        description="Export PNG",
        button_style='success',
        icon='download',
        layout=Layout(width='120px')
    )
    export_button.on_click(lambda b: export_plot())

    # Create legend
    legend_html = f"""
    <div style="margin: 10px; padding: 10px; border: 1px solid #ccc; border-radius: 5px; background-color: {colors['background']};">
        <h4 style="margin: 0 0 10px 0;">FOMP Analysis Legend</h4>
        <div style="display: flex; flex-wrap: wrap; gap: 15px;">
            <div style="display: flex; align-items: center;">
                <div style="width: 20px; height: 20px; background-color: {colors['stock']}; margin-right: 5px;"></div>
                <span>Organic Matter Stock</span>
            </div>
            <div style="display: flex; align-items: center;">
                <div style="width: 20px; height: 20px; background-color: {colors['input']}; margin-right: 5px;"></div>
                <span>Input (Annual/Cumulative)</span>
            </div>
            <div style="display: flex; align-items: center;">
                <div style="width: 20px; height: 20px; background-color: {colors['output']}; margin-right: 5px;"></div>
                <span>Mineralization (Annual/Cumulative)</span>
            </div>
        </div>
        <div style="margin-top: 10px; font-size: 12px; color: #666;">
            <strong>FOMP Process:</strong> First-Order Mineralization Process for organic matter dynamics
        </div>
    </div>
    """
    
    legend_widget = HTML(value=legend_html)

    # Set up interaction with enhanced layout
    from ipywidgets import interactive
    ui = VBox([
        HBox([process_dropdown, element_dropdown, cumulative_checkbox]),
        HBox([export_button]),
        legend_widget
    ])
    
    out = interactive(
        update_plot,
        process_id=process_dropdown,
        element=element_dropdown,
        show_cumulative=cumulative_checkbox
    )
    
    display(ui)
    display(fig)
    out.update()

def plot_system_efficiency_metrics(mfa_system_results):
    """
    Creates interactive plots showing system efficiency metrics:
    - Recycling rates
    - Recovery rates
    - Material efficiency indicators

    Args:
        mfa_system_results (odym.MFAsystem): The solved MFA system object.
    """
    time_items = mfa_system_results.IndexTable.Classification["Time"].Items
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
                    internal_flows = [
                        f
                        for f in mfa_system_results.FlowDict.values()
                        if f.P_Start != 0 and f.P_End != 0
                    ]  # Exclude external flows
                    total_internal_flow = sum(
                        f.Values[year_idx, element_index] for f in internal_flows
                    )

                    # Find total system throughput
                    total_throughput = sum(
                        f.Values[year_idx, element_index]
                        for f in mfa_system_results.FlowDict.values()
                    )

                    if total_throughput > 0:
                        recycling_rate = (total_internal_flow / total_throughput) * 100
                    else:
                        recycling_rate = 0
                    recycling_rates.append(recycling_rate)

                fig.add_trace(
                    go.Scatter(
                        x=time_items,
                        y=recycling_rates,
                        mode="lines+markers",
                        name="Recycling Rate (%)",
                        line=dict(color="#1f77b4", width=3),
                    )
                )

                fig.update_layout(
                    title=f"System Recycling Rate ({element.upper()})",
                    xaxis_title="Year",
                    yaxis_title="Recycling Rate (%)",
                    yaxis=dict(range=[0, 100]),
                )

            elif metric_type == "Recovery Rate":
                # Calculate recovery rate (outputs / inputs)
                recovery_rates = []
                for year_idx in range(len(time_items)):
                    # Find external outputs (flows to environment/sinks)
                    external_outputs = [
                        f
                        for f in mfa_system_results.FlowDict.values()
                        if f.P_Start != 0 and f.P_End == 0
                    ]  # Internal to external
                    total_output = sum(
                        f.Values[year_idx, element_index] for f in external_outputs
                    )

                    # Find external inputs
                    external_inputs = [
                        f
                        for f in mfa_system_results.FlowDict.values()
                        if f.P_Start == 0 and f.P_End != 0
                    ]  # External to internal
                    total_input = sum(
                        f.Values[year_idx, element_index] for f in external_inputs
                    )

                    if total_input > 0:
                        recovery_rate = (total_output / total_input) * 100
                    else:
                        recovery_rate = 0
                    recovery_rates.append(recovery_rate)

                fig.add_trace(
                    go.Scatter(
                        x=time_items,
                        y=recovery_rates,
                        mode="lines+markers",
                        name="Recovery Rate (%)",
                        line=dict(color="#2ca02c", width=3),
                    )
                )

                fig.update_layout(
                    title=f"System Recovery Rate ({element.upper()})",
                    xaxis_title="Year",
                    yaxis_title="Recovery Rate (%)",
                    yaxis=dict(range=[0, 100]),
                )

            elif metric_type == "Material Efficiency":
                # Calculate material efficiency (useful output / total input)
                efficiency_rates = []
                for year_idx in range(len(time_items)):
                    # Find useful outputs (e.g., to food, products)
                    useful_outputs = [
                        f
                        for f in mfa_system_results.FlowDict.values()
                        if f.P_Start != 0
                        and f.P_End == 0
                        and any(
                            keyword in f.Name.lower()
                            for keyword in ["food", "product", "use"]
                        )
                    ]
                    total_useful = sum(
                        f.Values[year_idx, element_index] for f in useful_outputs
                    )

                    # Find total inputs
                    total_input = sum(
                        f.Values[year_idx, element_index]
                        for f in mfa_system_results.FlowDict.values()
                        if f.P_Start == 0 and f.P_End != 0
                    )

                    if total_input > 0:
                        efficiency = (total_useful / total_input) * 100
                    else:
                        efficiency = 0
                    efficiency_rates.append(efficiency)

                fig.add_trace(
                    go.Scatter(
                        x=time_items,
                        y=efficiency_rates,
                        mode="lines+markers",
                        name="Material Efficiency (%s)",
                        line=dict(color="#d62728", width=3),
                    )
                )

                fig.update_layout(
                    title=f"Material Efficiency ({element.upper()})",
                    xaxis_title="Year",
                    yaxis_title="Efficiency (%)",
                    yaxis=dict(range=[0, 100]),
                )

    # Create widgets
    element_dropdown = Dropdown(
        options=element_items, value=element_items[0], description="Element:"
    )
    metric_dropdown = Dropdown(
        options=["Recycling Rate", "Recovery Rate", "Material Efficiency"],
        value="Recycling Rate",
        description="Metric:",
    )

    interact(update_plot, element=element_dropdown, metric_type=metric_dropdown)
    display(fig)

def plot_stock_overview(mfa_system_results, dsm_params=None, fomp_params=None):
    """
    Creates a simplified stock overview showing total stock evolution for all elements.
    This is a streamlined version of the summary dashboard focusing only on stock dynamics.

    Args:
        mfa_system_results (odym.MFAsystem): The solved MFA system object.
        dsm_params (dict, optional): DSM parameters configuration.
        fomp_params (dict, optional): FOMP parameters configuration.
    """
    from plotly.subplots import make_subplots

    time_items = mfa_system_results.IndexTable.Classification["Time"].Items
    element_items = mfa_system_results.Elements

    # Create a single subplot for stock evolution
    fig = make_subplots(
        rows=1,
        cols=1,
        subplot_titles=("Total Stock Evolution by Element"),
    )

    # Plot total stock evolution for all elements
    for i, element in enumerate(element_items):
        element_index = element_items.index(element)
        total_stock = np.zeros(len(time_items))

        for stock_name in mfa_system_results.StockDict.keys():
            if stock_name.startswith("S_"):
                stock_obj = mfa_system_results.StockDict[stock_name]
                total_stock += stock_obj.Values[:, element_index]

        fig.add_trace(
            go.Scatter(
                x=time_items,
                y=total_stock,
                mode="lines+markers",
                name=f"Total {element.upper()}",
                line=dict(width=3),
                marker=dict(size=4)
            ),
            row=1,
            col=1,
        )

    # Update layout
    fig.update_layout(
        title="Stock Overview - Total System Stocks by Element",
        xaxis_title="Year",
        yaxis_title="Total Stock in Mg",
        height=500,
        showlegend=True,
        hovermode="x unified"
    )

    fig.show()

def plot_summary_dashboard(mfa_system_results, dsm_params=None, fomp_params=None):
    """
    Creates a comprehensive summary dashboard showing key KPIs and system status.

    Args:
        mfa_system_results (odym.MFAsystem): The solved MFA system object.
        dsm_params (dict, optional): DSM parameters configuration.
        fomp_params (dict, optional): FOMP parameters configuration.
    """
    # Use the simplified stock overview instead
    plot_stock_overview(mfa_system_results, dsm_params, fomp_params)

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

    PROCESS_TYPE_COLUMN_NAME = "Process_Type"
    has_type_column = PROCESS_TYPE_COLUMN_NAME in process_definitions.columns
    if not has_type_column:
        print(
            f"Warning: Column '{PROCESS_TYPE_COLUMN_NAME}' not found. Smart titles disabled."
        )

    process_options = {p.Name: p.ID for p in mfa_system_results.ProcessList}
    if not process_options:
        print("No processes found to plot.")
        return

    element_items = mfa_system_results.Elements
    time_axis = mfa_system_results.IndexTable.Classification["Time"].Items
    fig = go.FigureWidget(
        make_subplots(rows=1, cols=3, subplot_titles=("Inflow", "Stock (S)", "Outflow"))
    )

    def update_plot(process_name, element):
        pid = process_options[process_name]
        element_index = element_items.index(element)

        # If the sum is empty, it returns a scalar 0, which causes a Plotly error.
        # We provide a zero-array of the correct length as the start value for sum.
        inflow_ts = sum(
            (
                f.Values[:, element_index]
                for f in mfa_system_results.FlowDict.values()
                if f.P_End == pid
            ),
            np.zeros(len(time_axis)),
        )
        
        # Gracefully handle processes without a stock
        stock_obj = mfa_system_results.StockDict.get(f"S_{pid}")
        if stock_obj:
            stock_ts = stock_obj.Values[:, element_index]
        else:
            stock_ts = np.zeros(len(time_axis)) # Plot a flat line at zero

        outflow_ts = sum(
            (
                f.Values[:, element_index]
                for f in mfa_system_results.FlowDict.values()
                if f.P_Start == pid
            ),
            np.zeros(len(time_axis)),
        )

        subplot_titles = (
            f"Inflow to '{process_name}'",
            f"Stock in '{process_name}'",
            f"Outflow from '{process_name}'",
        )
        if has_type_column:
            process_type = process_definitions.loc[
                process_definitions["ID"] == pid, PROCESS_TYPE_COLUMN_NAME
            ].iloc[0]
            if process_type == "Input":
                subplot_titles = (
                    "Primary System Input",
                    subplot_titles[1],
                    subplot_titles[2],
                )
            elif process_type == "Output":
                subplot_titles = (
                    subplot_titles[0],
                    subplot_titles[1],
                    "Final System Output (Sink)",
                )

        with fig.batch_update():
            fig.data, fig.layout.annotations = [], []
            fig.add_trace(
                go.Scatter(x=time_axis, y=inflow_ts, mode="lines", name="Inflow"),
                row=1,
                col=1,
            )
            fig.add_trace(
                go.Scatter(x=time_axis, y=stock_ts, mode="lines", name="Stock"),
                row=1,
                col=2,
            )
            fig.add_trace(
                go.Scatter(x=time_axis, y=outflow_ts, mode="lines", name="Outflow"),
                row=1,
                col=3,
            )
            fig.update_yaxes(title_text="Mass [Mg]", rangemode="tozero")

    process_dropdown = Dropdown(
        options=list(process_options.keys()), description="Process:"
    )
    element_dropdown = Dropdown(
        options=element_items, value=element_items[0], description="Element:"
    )
    interact(update_plot, process_name=process_dropdown, element=element_dropdown)
    display(fig)

def plot_dynamic_stock_composition(dsm_details, mfa_system_results):
    """
    Plots the composition of a dynamic stock over time, separating the
    decaying initial stock from the stock built up from new inflows.

    Args:
        dsm_details (dict): The detailed results dictionary from the DSM calculation.
        mfa_system_results (odym.MFAsystem): The solved MFA system object.
    """

    process_options = list(dsm_details.keys())
    if not process_options:
        print("No DSM processes with detailed results found to plot.")
        return

    element_items = mfa_system_results.Elements
    time_axis = mfa_system_results.IndexTable.Classification["Time"].Items
    fig = go.FigureWidget()

    def update_plot(process_id, element, show_as_bars):
        details = dsm_details.get(process_id, {})
        element_index = element_items.index(element)

        # Get data from the details dictionary
        initial_stock_ts_all_elements = details.get(
            "initial_stock_ts", np.zeros((len(time_axis), len(element_items)))
        )
        inflow_stocks_material = details.get("inflow_stock_ts_by_cat", [])
        category_names = details.get("category_names", [])
        mean_lifetimes = details.get("mean_lifetimes", [])

        # Get composition of the mixed inflow for the new stock parts
        inflows = [
            f.Values
            for f in mfa_system_results.FlowDict.values()
            if f.P_End == process_id
        ]
        total_inflow_values = (
            sum(inflows) if inflows else np.zeros((len(time_axis), len(element_items)))
        )
        inflow_comp_factor = np.divide(
            total_inflow_values[:, element_index],
            total_inflow_values[:, 0],
            out=np.zeros(len(time_axis)),
            where=total_inflow_values[:, 0] != 0,
        )

        with fig.batch_update():
            fig.data = []
            chart_type = go.Bar if show_as_bars else go.Scatter
            stack_group_props = (
                {"mode": "lines", "line": dict(width=0.5), "stackgroup": "one"}
                if not show_as_bars
                else {}
            )

            # Plot the decaying initial stock
            initial_stock_ts_element = initial_stock_ts_all_elements[:, element_index]
            fig.add_trace(
                chart_type(
                    x=time_axis,
                    y=initial_stock_ts_element,
                    name="Initial Stock (Decaying)",
                    hoverinfo="x+y",
                    **stack_group_props,
                )
            )

            # Plot the stock from new inflows, category by category
            for i, stock_ts_material in enumerate(inflow_stocks_material):
                stock_ts_element = stock_ts_material * inflow_comp_factor
                label = f"{category_names[i]} ({mean_lifetimes[i]} yrs)"
                fig.add_trace(
                    chart_type(
                        x=time_axis,
                        y=stock_ts_element,
                        name=label,
                        hoverinfo="x+y",
                        **stack_group_props,
                    )
                )

            process_name = next(
                (p.Name for p in mfa_system_results.ProcessList if p.ID == process_id),
                "",
            )
            fig.update_layout(
                barmode="stack" if show_as_bars else None,
                title=f"Dynamic Stock Composition for Process: '{process_name}' ({element.upper()})",
                xaxis_title="Year",
                yaxis_title="Stock in Mg",
            )

    process_dropdown = Dropdown(options=process_options, description="Process:")
    element_dropdown = Dropdown(
        options=element_items, value=element_items[0], description="Element:"
    )
    chart_type_checkbox = Checkbox(value=False, description="Show as Bar Chart")

    interact(
        update_plot,
        process_id=process_dropdown,
        element=element_dropdown,
        show_as_bars=chart_type_checkbox,
    )
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
    time_axis = mfa_system_results.IndexTable.Classification["Time"].Items
    fig = go.FigureWidget(
        make_subplots(
            rows=1,
            cols=3,
            subplot_titles=(
                "Total Inflow",
                "Absolute Stock (S)",
                "Outflow (Mineralization)",
            ),
        )
    )

    def update_plot(process_name, element):
        pid = process_options[process_name]
        element_index = element_items.index(element)

        # Get the time series data for the selected process
        inflow_ts = sum(
            f.Values[:, element_index]
            for f in mfa_system_results.FlowDict.values()
            if f.P_End == pid
        )
        stock_ts = mfa_system_results.StockDict.get(f"S_{pid}").Values[:, element_index]
        outflow_ts = sum(
            f.Values[:, element_index]
            for f in mfa_system_results.FlowDict.values()
            if f.P_Start == pid
        )

        with fig.batch_update():
            fig.data = []  # Clear existing data
            fig.add_trace(
                go.Scatter(x=time_axis, y=inflow_ts, mode="lines", name="Inflow"),
                row=1,
                col=1,
            )
            fig.add_trace(
                go.Scatter(x=time_axis, y=stock_ts, mode="lines", name="Stock"),
                row=1,
                col=2,
            )
            fig.add_trace(
                go.Scatter(x=time_axis, y=outflow_ts, mode="lines", name="Outflow"),
                row=1,
                col=3,
            )

            title_text = f"FOMP Dynamics for Process: '{process_name}' | Element: {element.upper()}"
            fig.update_layout(title_text=title_text, height=400, showlegend=False)
            fig.update_xaxes(title_text="Year")
            fig.update_yaxes(title_text="Mass [Mg]", row=1, col=1)

    # Create widgets for interaction
    process_dropdown = Dropdown(
        options=list(process_options.keys()), description="Process:"
    )
    element_dropdown = Dropdown(
        options=element_items, value=element_items[0], description="Element:"
    )

def plot_flow_dynamics(mfa_system_results):
    """
    Creates an interactive line/bar chart to show the development of selected
    flows over time for a chosen element.

    Args:
        mfa_system_results (odym.MFAsystem): The solved MFA system object.
    """

    # Create options for the widgets
    flow_options = sorted(list(mfa_system_results.FlowDict.keys()))
    if not flow_options:
        print("No flows found in the system to plot.")
        return

    element_items = mfa_system_results.Elements
    time_axis = mfa_system_results.IndexTable.Classification["Time"].Items

    # Use FigureWidget for efficient updates
    fig = go.FigureWidget()

    def update_plot(flows_to_show, element, show_as_bars):
        # Use batch_update for smooth interaction
        with fig.batch_update():
            fig.data = []  # Clear previous traces
            if not flows_to_show:
                fig.update_layout(
                    title_text="Please select one or more flows to display."
                )
                return

            element_index = element_items.index(element)
            chart_type = go.Bar if show_as_bars else go.Scatter

            # Add a trace for each selected flow
            for flow_id in flows_to_show:
                flow_obj = mfa_system_results.FlowDict.get(flow_id)
                if flow_obj:
                    trace_props = dict(
                        x=time_axis, y=flow_obj.Values[:, element_index], name=flow_id
                    )
                    if not show_as_bars:
                        trace_props.update(mode="lines")
                    fig.add_trace(chart_type(**trace_props))

            # Update layout and title
            fig.update_layout(
                barmode="stack" if show_as_bars else "overlay",
                title=f"Time Series for Selected Flows ({element.upper()})",
                xaxis_title="Year",
                yaxis_title="Mass in Mg",
                hovermode="x unified",
            )

    # Create widgets
    flow_selector = SelectMultiple(
        options=flow_options,
        value=[flow_options[0]] if flow_options else [],
        description="Flows:",
        rows=10,
    )
    element_dropdown = Dropdown(
        options=element_items, value=element_items[0], description="Element:"
    )
    chart_type_checkbox = Checkbox(value=False, description="Show as Bar Chart")

    # Set up interaction and display the plot
    interact(
        update_plot,
        flows_to_show=flow_selector,
        element=element_dropdown,
        show_as_bars=chart_type_checkbox,
    )
    display(fig)

def plot_stock_bar_chart(mfa_system, title="Stock Levels Over Time"):
    """
    Generates an interactive bar chart of stock levels with a time slider
    and element selection dropdown.

    Displays process names instead of IDs and allows for a polished,
    publication-ready visualization of stock evolution.

    Parameters
    ----------
    mfa_system : object
        The MFA system object containing calculated results.
    title : str, optional
        The title for the plot.
    """
    if not hasattr(mfa_system, 'StockDict') or not mfa_system.StockDict:
        print("No stocks available to plot.")
        return

    years = mfa_system.IndexTable.Classification['Time'].Items
    elements = mfa_system.Elements
    
    # Create a mapping from process ID to process name
    process_id_to_name = {p.ID: p.Name for p in mfa_system.ProcessList}

    # Prepare the data in a long-format DataFrame for easier filtering
    all_stocks_data = []
    for stock_name, stock in mfa_system.StockDict.items():
        if stock_name.startswith('S_'):
            process_id = int(stock_name.split('_')[1])
            process_name = process_id_to_name.get(process_id, f"Process {process_id}")
            for i, year in enumerate(years):
                for j, element in enumerate(elements):
                    all_stocks_data.append({
                        'Year': year,
                        'Element': element,
                        'Process': process_name,
                        'Value': stock.Values[i, j]
                    })

    if not all_stocks_data:
        print("No absolute stock data found to plot.")
        return

    df = pd.DataFrame(all_stocks_data)
    fig = go.FigureWidget()

    def update_plot(year, element):
        with fig.batch_update():
            fig.data = []
            df_filtered = df[(df['Year'] == year) & (df['Element'] == element)]
            
            # Determine colors based on value (positive/negative)
            colors = ['#2ca02c' if val >= 0 else '#d62728' for val in df_filtered['Value']]

            fig.add_trace(
                go.Bar(
                    x=df_filtered['Process'],
                    y=df_filtered['Value'],
                    marker_color=colors,
                    hovertemplate="<b>%{x}</b><br>Stock: %{y:.2f} Mg<extra></extra>"
                )
            )

            fig.update_layout(
                title=dict(
                    text=f"{title} - {element.upper()} ({year})",
                    x=0.5,
                    font=dict(size=20, family="Arial, sans-serif")
                ),
                xaxis_title="Process Name",
                yaxis_title="Stock Value (Mass Units)",
                template="plotly_white",
                font=dict(family="Arial, sans-serif", size=12),
                xaxis=dict(
                    tickangle=-45,
                    showgrid=False,
                    linecolor='black',
                    linewidth=1
                ),
                yaxis=dict(
                    gridcolor='lightgrey',
                    linecolor='black',
                    linewidth=1,
                    zeroline=True,
                    zerolinecolor='rgba(0,0,0,0.5)',
                    zerolinewidth=1
                ),
                showlegend=False
            )

    # Create widgets
    year_slider = IntSlider(min=min(years), max=max(years), step=1, value=min(years), description='Year')
    element_dropdown = Dropdown(options=elements, value=elements[0], description='Element')

    # Display widgets and plot
    interact(update_plot, year=year_slider, element=element_dropdown)
    display(fig)
