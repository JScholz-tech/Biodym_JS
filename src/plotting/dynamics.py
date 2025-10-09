# -*- coding: utf-8 -*-
"""
Dynamics Plotting Module.

This file contains functions for plotting time-series data, such as
stock and process dynamics.
"""

import numpy as np
import plotly.graph_objects as go
from ipywidgets import interact, IntSlider, Dropdown, SelectMultiple, Checkbox, HBox, VBox, Layout
from .publication_style_simplified import (
    get_publication_layout,
    get_element_color,
    get_stock_color,
    BIOYM_COLORS,
    ELEMENT_COLORS
)
from IPython.display import display
from plotly.subplots import make_subplots
import pandas as pd
import os
from datetime import datetime


def plot_dsm_process_dynamics(mfa_system_results, dsm_params, dsm_details):
    """
    Creates DSM Process Dynamics Analysis with a three-panel view: Input, Stock, and Output.
    Shows stacked area charts for flows by element and a line chart for stock evolution,
    styled according to the publication guide.

    Args:
        mfa_system_results (odym.MFAsystem): The solved MFA system object.
        dsm_params (dict): DSM parameters configuration.
        dsm_details (dict): Detailed DSM calculation results.
    """
    if not dsm_params:
        print("No DSM processes found to plot.")
        return

    from ipywidgets import Dropdown, HBox, VBox, Layout, Button, interactive
    from IPython.display import display
    import os
    from datetime import datetime

    time_items = mfa_system_results.IndexTable.Classification["Time"].Items
    element_items = mfa_system_results.Elements

    process_options = {p.Name: p.ID for p in mfa_system_results.ProcessList if p.ID in dsm_params}
    if not process_options:
        print("No DSM processes found in the system.")
        return

    fig = go.FigureWidget(make_subplots(rows=1, cols=3, subplot_titles=("Input Flows", "Stock Evolution", "Output Flows")))

    def update_plot(process_name, element):
        process_id = process_options[process_name]
        fig.data = []
        element_index = element_items.index(element)

        # 1. INPUT FLOWS (Left Panel) - Stacked Area Chart
        input_flows = [f for f in mfa_system_results.FlowDict.values() if f.P_End == process_id]
        if input_flows:
            for i, flow in enumerate(input_flows):
                fig.add_trace(
                    go.Scatter(
                        x=time_items, y=flow.Values[:, element_index], name=flow.Name,
                        stackgroup='input', fill='tonexty' if i > 0 else 'tozeroy',
                        mode='lines', line=dict(width=0.5),
                        hovertemplate=f"<b>{flow.Name}</b><br>Year: %{{x}}<br>{element}: %{{y:.2e}} Mg<extra></extra>"
                    ), row=1, col=1
                )

        # 2. STOCK EVOLUTION (Middle Panel) - Line Chart
        stock_name = f"S_{process_id}"
        if stock_name in mfa_system_results.StockDict:
            stock = mfa_system_results.StockDict[stock_name]
            fig.add_trace(
                go.Scatter(
                    x=time_items, y=stock.Values[:, element_index], name=f"Stock: {stock_name}",
                    mode='lines+markers', line=dict(width=3, color='#2E8B57'), marker=dict(size=4),
                    hovertemplate=f"<b>{stock_name}</b><br>Year: %{{x}}<br>{element}: %{{y:.2e}} Mg<extra></extra>"
                ), row=1, col=2
            )

        # 3. OUTPUT FLOWS (Right Panel) - Stacked Area Chart
        output_flows = [f for f in mfa_system_results.FlowDict.values() if f.P_Start == process_id]
        if output_flows:
            for i, flow in enumerate(output_flows):
                fig.add_trace(
                    go.Scatter(
                        x=time_items, y=flow.Values[:, element_index], name=flow.Name,
                        stackgroup='output', fill='tonexty' if i > 0 else 'tozeroy',
                        mode='lines', line=dict(width=0.5),
                        hovertemplate=f"<b>{flow.Name}</b><br>Year: %{{x}}<br>{element}: %{{y:.2e}} Mg<extra></extra>"
                    ), row=1, col=3
                )

        # Update layout using publication style guide for subplots
        layout_config = get_publication_layout(
            custom_title=f"DSM Process Dynamics: {process_name} ({element.upper()})",
            show_grid=True, scientific_y=True
        )
        
        # Pop axis styles and apply them globally to all subplots
        xaxis_style = layout_config.pop('xaxis')
        yaxis_style = layout_config.pop('yaxis')
        fig.update_layout(**layout_config)
        fig.update_xaxes(title_text="Year", **xaxis_style)
        fig.update_yaxes(title_text=f"{element} in Mg", **yaxis_style)

        # Restore subplot titles which can be overwritten by update_layout
        fig.update_layout(
            annotations=[
                dict(text="Input Flows", x=0.17, y=1.05, xref="paper", yref="paper", showarrow=False, font=dict(size=14)),
                dict(text="Stock Evolution", x=0.5, y=1.05, xref="paper", yref="paper", showarrow=False, font=dict(size=14)),
                dict(text="Output Flows", x=0.83, y=1.05, xref="paper", yref="paper", showarrow=False, font=dict(size=14))
            ]
        )

    process_dropdown = Dropdown(options=list(process_options.keys()), description="DSM Process:", style={'description_width': '120px'}, layout=Layout(width='300px'))
    element_dropdown = Dropdown(options=element_items, value=element_items[0], description="Element:", style={'description_width': '80px'}, layout=Layout(width='200px'))
    export_button = Button(description="Export Plot", button_style='info', tooltip='Export current plot as PNG')

    def export_plot():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"dsm_process_dynamics_{timestamp}.png"
        export_dir = "exports/dsm_analysis"
        os.makedirs(export_dir, exist_ok=True)
        filepath = os.path.join(export_dir, filename)
        try:
            fig.write_image(filepath, width=1400, height=600, scale=2)
            print(f"✅ Plot exported to: {filepath}")
        except Exception as e:
            print(f"⚠️ Export failed: {e}")
            print("💡 Ensure 'kaleido' is available (uv sync)")

    export_button.on_click(lambda b: export_plot())

    controls = HBox([VBox([process_dropdown, element_dropdown], layout=Layout(width='300px')), VBox([export_button], layout=Layout(width='200px'))], layout=Layout(justify_content='space-between'))
    
    out = interactive(update_plot, process_name=process_dropdown, element=element_dropdown)
    
    display(controls)
    display(fig)
    out.update()

def plot_dsm_stock_details(mfa_system_results, dsm_params, dsm_details):
    """
    Creates an enhanced, stacked line diagram of DSM stock evolution.
    Shows initial stock decay and new stock accumulation by individual application categories.

    Args:
        mfa_system_results (odym.MFAsystem): The solved MFA system object.
        dsm_params (dict): DSM parameters configuration.
        dsm_details (dict): Detailed DSM calculation results.
    """
    if not dsm_params:
        print("No DSM processes found to plot.")
        return

    from ipywidgets import Dropdown, HBox, VBox, interactive, Layout, Button
    from IPython.display import display
    import os
    from datetime import datetime

    time_items = mfa_system_results.IndexTable.Classification["Time"].Items
    element_items = mfa_system_results.Elements

    colors = {'initial_stock': '#ff7f0e'}

    fig = go.FigureWidget()

    def update_plot(process_id, element):
        if process_id not in dsm_details:
            print(f"No detailed results for process {process_id}")
            return

        element_index = element_items.index(element)
        details = dsm_details[process_id]

        with fig.batch_update():
            fig.data = []

            initial_stock_ts = details.get("initial_stock_ts", np.zeros((len(time_items), len(element_items))))
            inflow_stocks_material = details.get("inflow_stock_ts_by_cat", [])
            category_names = details.get("category_names", [])

            initial_stock_element = initial_stock_ts[:, element_index]
            fig.add_trace(
                go.Scatter(
                    x=time_items,
                    y=initial_stock_element,
                    mode="lines",
                    name="Initial Stock (Decaying)",
                    line=dict(color=colors['initial_stock'], width=0.5, dash='dash'),
                    stackgroup='one',
                    fill='tozeroy',
                    hovertemplate="<b>Initial Stock</b><br>Year: %{x}<br>Mass: %{y:.2f} Mg<extra></extra>"
                )
            )

            for i, stock_ts_material in enumerate(inflow_stocks_material):
                inflows = [f.Values for f in mfa_system_results.FlowDict.values() if f.P_End == process_id]
                total_inflow_values = sum(inflows) if inflows else np.zeros((len(time_items), len(element_items)))
                inflow_comp_factor = np.divide(
                    total_inflow_values[:, element_index],
                    total_inflow_values[:, 0],
                    out=np.zeros(len(time_items)),
                    where=total_inflow_values[:, 0] != 0,
                )
                stock_ts_element = stock_ts_material * inflow_comp_factor
                category_display = category_names[i]

                fig.add_trace(
                    go.Scatter(
                        x=time_items,
                        y=stock_ts_element,
                        mode="lines",
                        name=category_display,
                        line=dict(width=0.5),
                        stackgroup='one',
                        fill='tonexty',
                        hovertemplate=f"<b>{category_display}</b><br>Year: %{{x}}<br>Mass: %{{y:.2f}} Mg<extra></extra>"
                    )
                )

            process_name = next((p.Name for p in mfa_system_results.ProcessList if p.ID == process_id), f"Process {process_id}")
            layout_config = get_publication_layout(
                custom_title=f"DSM Stock Evolution: {process_name} ({element.upper()}) - Stacked by Application",
                x_title="Year",
                y_title="Stock in Mg",
                show_grid=True,
                scientific_y=True
            )
            fig.update_layout(**layout_config)

    process_dropdown = Dropdown(options=list(dsm_params.keys()), description="DSM Process:", style={'description_width': '120px'})
    element_dropdown = Dropdown(options=element_items, value=element_items[0], description="Element:", style={'description_width': '80px'})
    export_button = Button(description="Export Plot", button_style='info', tooltip='Export current plot as PNG')

    def export_plot():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"dsm_stock_analysis_{timestamp}.png"
        export_dir = "exports/dsm_stock_details"
        os.makedirs(export_dir, exist_ok=True)
        filepath = os.path.join(export_dir, filename)
        try:
            fig.write_image(filepath, width=1200, height=800)
            print(f"✅ Plot exported to: {filepath}")
        except Exception as e:
            print(f"⚠️ Export failed: {e}")
            print("💡 Ensure 'kaleido' is available (uv sync)")

    export_button.on_click(lambda b: export_plot())

    controls = HBox([
        VBox([process_dropdown, element_dropdown], layout=Layout(width='300px')),
        VBox([export_button], layout=Layout(width='150px'))
    ], layout=Layout(justify_content='space-between'))

    out = interactive(
        update_plot, 
        process_id=process_dropdown, 
        element=element_dropdown,
    )
    
    display(controls)
    display(fig)
    out.update()

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
            layout_config = get_publication_layout(
                custom_title=f"FOMP Analysis: {process_name} ({element.upper()})",
                x_title="Year",
                y_title=f"Mass ({element.upper()}) in Mg",
                show_grid=True,
                scientific_y=True,
                size='medium'
            )
            fig.update_layout(**layout_config)

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

                layout_config = get_publication_layout(
                    custom_title=f"System Recycling Rate ({element.upper()})",
                    x_title="Year",
                    y_title="Recycling Rate (%)",
                    show_grid=True
                )
                fig.update_layout(**layout_config)
                fig.update_yaxes(range=[0, 100])

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

                layout_config = get_publication_layout(
                    custom_title=f"System Recovery Rate ({element.upper()})",
                    x_title="Year",
                    y_title="Recovery Rate (%)",
                    show_grid=True
                )
                fig.update_layout(**layout_config)
                fig.update_yaxes(range=[0, 100])

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
                            keyword in getattr(f, 'DescriptiveName', f.Name).lower()
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

                layout_config = get_publication_layout(
                    custom_title=f"Material Efficiency ({element.upper()})",
                    x_title="Year",
                    y_title="Efficiency (%)",
                    show_grid=True
                )
                fig.update_layout(**layout_config)
                fig.update_yaxes(range=[0, 100])

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
    layout_config = get_publication_layout(
        custom_title="Stock Overview - Total System Stocks by Element",
        x_title="Year",
        y_title="Total Stock in Mg",
        show_grid=True,
        size='medium'
    )
    fig.update_layout(**layout_config)

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
            layout_config = get_publication_layout(
                custom_title=f"Process Dynamics: {process_name} ({element.upper()})",
                show_grid=True,
                scientific_y=True
            )
            xaxis_style = layout_config.pop('xaxis')
            yaxis_style = layout_config.pop('yaxis')
            fig.update_layout(**layout_config)
            fig.update_xaxes(**xaxis_style)
            fig.update_yaxes(**yaxis_style)

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
            layout_config = get_publication_layout(
                custom_title=f"Dynamic Stock Composition for Process: '{process_name}' ({element.upper()})",
                x_title="Year",
                y_title="Stock in Mg",
                show_grid=True,
                scientific_y=True
            )
            if show_as_bars:
                layout_config['barmode'] = 'stack'
            fig.update_layout(**layout_config)

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

            layout_config = get_publication_layout(
                custom_title=f"FOMP Dynamics for Process: '{process_name}' | Element: {element.upper()}",
                show_grid=True,
                scientific_y=True,
                size='small'
            )
            xaxis_style = layout_config.pop('xaxis')
            yaxis_style = layout_config.pop('yaxis')
            fig.update_layout(**layout_config)
            fig.update_xaxes(title_text="Year", **xaxis_style)
            fig.update_yaxes(title_text="Mass [Mg]", **yaxis_style)

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

    # Create options for the widgets with descriptive names
    flow_options = []
    flow_id_to_descriptive = {}
    
    for flow_id in sorted(mfa_system_results.FlowDict.keys()):
        flow_obj = mfa_system_results.FlowDict[flow_id]
        descriptive_name = getattr(flow_obj, 'DescriptiveName', flow_id)
        flow_options.append(descriptive_name)
        flow_id_to_descriptive[flow_id] = descriptive_name
    
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
            for descriptive_name in flows_to_show:
                # Find the flow ID that corresponds to this descriptive name
                flow_id = None
                for fid, desc_name in flow_id_to_descriptive.items():
                    if desc_name == descriptive_name:
                        flow_id = fid
                        break
                
                if flow_id:
                    flow_obj = mfa_system_results.FlowDict.get(flow_id)
                    if flow_obj:
                        trace_props = dict(
                            x=time_axis, y=flow_obj.Values[:, element_index], name=descriptive_name
                        )
                        if not show_as_bars:
                            trace_props.update(mode="lines")
                        fig.add_trace(chart_type(**trace_props))

            # Update layout and title
            layout_config = get_publication_layout(
                custom_title=f"Time Series for Selected Flows ({element.upper()})",
                x_title="Year",
                y_title="Mass in Mg",
                show_grid=True,
                scientific_y=True
            )
            if show_as_bars:
                layout_config['barmode'] = 'stack'
            else:
                layout_config['barmode'] = 'overlay'
            
            # Always show legend, even with single flow
            layout_config['showlegend'] = True
            
            fig.update_layout(**layout_config)

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

            layout_config = get_publication_layout(
                custom_title=f"{title} - {element.upper()} ({year})",
                x_title="Process Name",
                y_title="Stock Value (Mass Units)",
                show_grid=True,
                scientific_y=True
            )
            layout_config['showlegend'] = False
            layout_config['xaxis']['tickangle'] = -45
            fig.update_layout(**layout_config)

    # Create widgets
    year_slider = IntSlider(min=min(years), max=max(years), step=1, value=min(years), description='Year')
    element_dropdown = Dropdown(options=elements, value=elements[0], description='Element')

    # Display widgets and plot
    interact(update_plot, year=year_slider, element=element_dropdown)
    display(fig)


def plot_system_stock_composition(mfa_system_results, element=None):
    """
    Creates an interactive plot showing individual stocks in the system over time.
    Shows each process stock separately with shiny colors and publication standards.
    
    Features:
    - Interactive element selection
    - Shows individual process stocks over time
    - Bar chart or line chart display options
    - Stacked positive/negative bar chart option
    - NEW: Grouped by process type (positive vs negative stocks)
    - Shiny color scheme based on element types
    - Publication-quality layout and typography
    - Y-axis starts at 0 with scientific notation for small values
    - Process names instead of IDs for better readability

    Args:
        mfa_system_results (odym.MFAsystem): The solved MFA system object.
        element (str, optional): Default element to display. If None, uses first element.
    """
    if not hasattr(mfa_system_results, 'StockDict') or not mfa_system_results.StockDict:
        print("No stocks available to plot.")
        return

    time_items = mfa_system_results.IndexTable.Classification["Time"].Items
    element_items = mfa_system_results.Elements
    
    # Set default element
    if element is None:
        element = element_items[0]
    
    # Create a mapping from process ID to process name
    process_id_to_name = {p.ID: p.Name for p in mfa_system_results.ProcessList}

    fig = go.FigureWidget()

    def update_plot(element, show_as_bars, stacked_pos_neg, grouped_stacked):
        element_index = element_items.index(element)
        
        with fig.batch_update():
            fig.data = []
            
            # Choose chart type
            chart_type = go.Bar if show_as_bars else go.Scatter
            
            if show_as_bars and stacked_pos_neg and grouped_stacked:
                # --- Grouped Stacked Positive/Negative Bar Chart ---
                # This mode provides a high-level summary of positive vs. negative stock contributions.

                # 1. Collect and classify all stock data
                positive_processes_data = []
                negative_processes_data = []
                for stock_name, stock_obj in mfa_system_results.StockDict.items():
                    if stock_name.startswith('S_'):
                        process_id = int(stock_name.split('_')[1])
                        process_name = process_id_to_name.get(process_id, f"Process {process_id}")
                        stock_values = stock_obj.Values[:, element_index]

                        if np.all(stock_values == 0):
                            continue

                        # Classify process based on name patterns or average stock value
                        is_positive = False
                        if any(keyword in process_name.lower() for keyword in ['use', 'utilization', 'production', 'harvest']):
                            is_positive = True
                        elif any(keyword in process_name.lower() for keyword in ['environment', 'atmosphere', 'emission', 'waste']):
                            is_positive = False
                        else:
                            if np.mean(stock_values) >= 0:
                                is_positive = True
                        
                        if is_positive:
                            positive_processes_data.append(stock_values)
                        else:
                            negative_processes_data.append(stock_values)

                # 2. Calculate the total sum for each group across all years
                positive_total = np.sum([np.sum(vals) for vals in positive_processes_data])
                negative_total = np.sum([np.sum(vals) for vals in negative_processes_data])

                # 3. Add a single trace with two bars for the summary view
                fig.add_trace(
                    go.Bar(
                        x=['Positive Stocks', 'Negative Stocks'],
                        y=[positive_total, negative_total],
                        name='Grouped Stock Summary',
                        marker_color=['#2ca02c', '#d62728'],
                        text=[f'{positive_total:.2e}', f'{negative_total:.2e}'],
                        textposition='auto',
                        hovertemplate='<b>%{x}</b><br>Total Cumulative Stock: %{y:.2e} Mg<extra></extra>'
                    )
                )
                
                # 4. Update layout for a grouped bar chart summary
                fig.update_layout(barmode='group')
                
            elif show_as_bars and stacked_pos_neg:
                # Stacked positive/negative bar chart
                # Collect all stock data first
                all_stocks_data = []
                for stock_name, stock_obj in mfa_system_results.StockDict.items():
                    if stock_name.startswith('S_'):
                        process_id = int(stock_name.split('_')[1])
                        process_name = process_id_to_name.get(process_id, f"Process {process_id}")
                        
                        stock_values = stock_obj.Values[:, element_index]
                        
                        # Skip processes with no stock
                        if np.all(stock_values == 0):
                            continue
                            
                        all_stocks_data.append({
                            'process_name': process_name,
                            'values': stock_values
                        })
                
                # Create stacked traces for positive and negative values
                for stock_data in all_stocks_data:
                    process_name = stock_data['process_name']
                    stock_values = stock_data['values']
                    
                    # Separate positive and negative values
                    positive_values = np.where(stock_values >= 0, stock_values, 0)
                    negative_values = np.where(stock_values < 0, stock_values, 0)
                    
                    # Add positive values trace
                    fig.add_trace(
                        go.Bar(
                            x=time_items,
                            y=positive_values,
                            name=f"{process_name} (+)",
                            marker_color='#2ca02c',  # Green for positive
                            hovertemplate=f"<b>{process_name}</b><br>Year: %{{x}}<br>Positive Stock: %{{y:.2e}} Mg<extra></extra>"
                        )
                    )
                    
                    # Add negative values trace
                    fig.add_trace(
                        go.Bar(
                            x=time_items,
                            y=negative_values,
                            name=f"{process_name} (-)",
                            marker_color='#d62728',  # Red for negative
                            hovertemplate=f"<b>{process_name}</b><br>Year: %{{x}}<br>Negative Stock: %{{y:.2e}} Mg<extra></extra>"
                        )
                    )
            else:
                # Regular bar chart or line chart
                for stock_name, stock_obj in mfa_system_results.StockDict.items():
                    if stock_name.startswith('S_'):
                        process_id = int(stock_name.split('_')[1])
                        process_name = process_id_to_name.get(process_id, f"Process {process_id}")
                        
                        stock_values = stock_obj.Values[:, element_index]
                        
                        # Skip processes with no stock
                        if np.all(stock_values == 0):
                            continue
                        
                        if show_as_bars:
                            fig.add_trace(
                                chart_type(
                                    x=time_items,
                                    y=stock_values,
                                    name=f"{process_name}",
                                    hovertemplate=f"<b>{process_name}</b><br>Year: %{{x}}<br>Stock: %{{y:.2e}} Mg<extra></extra>"
                                )
                            )
                        else:
                            fig.add_trace(
                                chart_type(
                                    x=time_items,
                                    y=stock_values,
                                    mode="lines+markers",
                                    name=f"{process_name}",
                                    hovertemplate=f"<b>{process_name}</b><br>Year: %{{x}}<br>Stock: %{{y:.2e}} Mg<extra></extra>"
                                )
                            )

            # Update axes with scientific notation (matching validation style)
            if show_as_bars and stacked_pos_neg and grouped_stacked:
                fig.update_xaxes(title_text="Stock Category", showgrid=False)
            else:
                fig.update_xaxes(
                    title_text="Year",
                    showgrid=True,
                    gridwidth=1
                )
            fig.update_yaxes(
                title_text=f"Stock ({element.upper()}) [Mg]", 
                rangemode="tozero", 
                tickformat=".2e",
                zeroline=True,
                zerolinewidth=2,
                showgrid=True,
                gridwidth=1
            )

    # Create enhanced widgets
    element_dropdown = Dropdown(
        options=element_items, 
        value=element,
        description="Element:",
        style={'description_width': '80px'},
        layout=Layout(width='200px')
    )
    chart_type_checkbox = Checkbox(
        value=False, 
        description="Show as Bar Chart",
        style={'description_width': '120px'}
    )
    
    stacked_checkbox = Checkbox(
        value=False, 
        description="Stacked Positive/Negative",
        style={'description_width': '150px'}
    )
    
    grouped_stacked_checkbox = Checkbox(
        value=False, 
        description="Grouped by Process Type",
        style={'description_width': '150px'}
    )

    # Create widget layout
    controls = HBox([
        VBox([element_dropdown, chart_type_checkbox, stacked_checkbox, grouped_stacked_checkbox], layout=Layout(width='200px')),
    ], layout=Layout(justify_content='space-between'))

    # Set up interaction with custom widgets
    def on_change(change):
        update_plot(element_dropdown.value, chart_type_checkbox.value, stacked_checkbox.value, grouped_stacked_checkbox.value)
    
    element_dropdown.observe(on_change, 'value')
    chart_type_checkbox.observe(on_change, 'value')
    stacked_checkbox.observe(on_change, 'value')
    grouped_stacked_checkbox.observe(on_change, 'value')
    
    # Display controls and plot
    display(controls)
    display(fig)
    
    # Initial plot
    update_plot(element_dropdown.value, chart_type_checkbox.value, stacked_checkbox.value, grouped_stacked_checkbox.value)