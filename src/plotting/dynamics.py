# -*- coding: utf-8 -*-
"""
Dynamics Plotting Module.

This file contains functions for plotting time-series data, such as
stock and process dynamics.
"""

import numpy as np
import plotly.graph_objects as go
from ipywidgets import interact, IntSlider, Dropdown, SelectMultiple, Checkbox, Button, HBox, VBox, Layout
from IPython.display import display
from plotly.subplots import make_subplots
import pandas as pd
import os
from datetime import datetime

# Import publication standards
from .publication_style import (
    get_publication_layout,
    get_element_color,
    get_process_color,
    detect_biodym_process_type,
    BIOYM_COLORS
)


def plot_dsm_stock_details(mfa_system_results, dsm_params, dsm_details):
    """
    Creates enhanced DSM stock evolution plots with publication standards and shiny colors.
    Shows initial stock decay, new stock accumulation by category, and lifetime analysis.
    
    Features:
    - Shiny element colors for total stock
    - Dotted lines for sub-stocks (categories)
    - Annual vs Stacked view options
    - Input/Output analysis with stacked elements
    - Publication-quality layout and typography
    - Single PNG export functionality

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

    # Additional shiny colors for sub-stocks (not yet used in system)
    additional_colors = [
        '#FF6B6B',  # Coral red
        '#4ECDC4',  # Turquoise
        '#45B7D1',  # Sky blue
        '#96CEB4',  # Mint green
        '#FFEAA7',  # Light yellow
        '#DDA0DD',  # Plum
        '#98D8C8',  # Seafoam
        '#F7DC6F',  # Golden yellow
    ]

    fig = go.FigureWidget()

    def update_plot(process_id, element, view_mode, show_as_bars):
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

            # Get shiny element color for total stock
            element_color = get_element_color(element)
            
            # Choose chart type
            chart_type = go.Bar if show_as_bars else go.Scatter

            # Plot initial stock decay (dotted line)
            initial_stock_element = initial_stock_ts[:, element_index]
            if show_as_bars:
                fig.add_trace(
                    chart_type(
                        x=time_items,
                        y=initial_stock_element,
                        name="Initial Stock (Decaying)",
                        marker_color=element_color,
                        hovertemplate="<b>Initial Stock</b><br>Year: %{x}<br>Mass: %{y:.2e} Mg<extra></extra>"
                    )
                )
            else:
                fig.add_trace(
                    chart_type(
                        x=time_items,
                        y=initial_stock_element,
                        mode="lines",
                        name="Initial Stock (Decaying)",
                        line=dict(color=element_color, width=2, dash="dot"),
                        hovertemplate="<b>Initial Stock</b><br>Year: %{x}<br>Mass: %{y:.2e} Mg<extra></extra>"
                    )
                )

            # Plot new stock accumulation by category
            total_inflow_stock = np.zeros(len(time_items))
            cumulative_stocks = []  # Store cumulative stocks for proper stacking
            
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

                # Create category name with lifetime info
                category_display = f"{category_names[i]} ({lifetimes[i]} yrs)" if i < len(lifetimes) else category_names[i]
                
                # Use additional shiny colors for sub-stocks
                sub_color = additional_colors[i % len(additional_colors)]

                if view_mode == "Annual Values":
                    # Show individual category lines/bars
                    if show_as_bars:
                        fig.add_trace(
                            chart_type(
                                x=time_items,
                                y=stock_ts_element,
                                name=f"New Stock: {category_display}",
                                marker_color=sub_color,
                                hovertemplate=f"<b>{category_display}</b><br>Year: %{{x}}<br>Mass: %{{y:.2e}} Mg<extra></extra>"
                            )
                        )
                    else:
                        fig.add_trace(
                            chart_type(
                                x=time_items,
                                y=stock_ts_element,
                                mode="lines",
                                name=f"New Stock: {category_display}",
                                line=dict(color=sub_color, width=2, dash="dash"),
                                hovertemplate=f"<b>{category_display}</b><br>Year: %{{x}}<br>Mass: %{{y:.2e}} Mg<extra></extra>"
                            )
                        )
                else:  # Stacked Values
                    # Calculate cumulative stock properly
                    if i == 0:
                        cumulative_stock = stock_ts_element.copy()
                    else:
                        cumulative_stock = cumulative_stocks[i-1] + stock_ts_element
                    
                    cumulative_stocks.append(cumulative_stock)
                    
                    if show_as_bars:
                        fig.add_trace(
                            chart_type(
                                x=time_items,
                                y=cumulative_stock,
                                name=f"Cumulative: {category_display}",
                                marker_color=sub_color,
                                hovertemplate=f"<b>Cumulative {category_display}</b><br>Year: %{{x}}<br>Mass: %{{y:.2e}} Mg<extra></extra>"
                            )
                        )
                    else:
                        fig.add_trace(
                            chart_type(
                                x=time_items,
                                y=cumulative_stock,
                                mode="lines",
                                name=f"Cumulative: {category_display}",
                                line=dict(color=sub_color, width=2, dash="dash"),
                                hovertemplate=f"<b>Cumulative {category_display}</b><br>Year: %{{x}}<br>Mass: %{{y:.2e}} Mg<extra></extra>"
                            )
                        )

            # Plot total stock (solid line/bar with element color)
            total_stock = initial_stock_element + total_inflow_stock
            if show_as_bars:
                fig.add_trace(
                    chart_type(
                        x=time_items,
                        y=total_stock,
                        name=f"Total {element.upper()} Stock",
                        marker_color=element_color,
                        hovertemplate="<b>Total Stock</b><br>Year: %{x}<br>Mass: %{y:.2e} Mg<extra></extra>"
                    )
                )
            else:
                fig.add_trace(
                    chart_type(
                        x=time_items,
                        y=total_stock,
                        mode="lines+markers",
                        name=f"Total {element.upper()} Stock",
                        line=dict(color=element_color, width=4),
                        marker=dict(color=element_color, size=6),
                        hovertemplate="<b>Total Stock</b><br>Year: %{x}<br>Mass: %{y:.2e} Mg<extra></extra>"
                    )
                )

            # Apply publication layout with reduced height and legend
            process_name = next(
                (p.Name for p in mfa_system_results.ProcessList if p.ID == process_id),
                f"Process {process_id}",
            )
            
            view_title = "Annual Values" if view_mode == "Annual Values" else "Stacked Values"
            layout_config = get_publication_layout(size='large', show_grid=True)
            layout_config['title'] = f"DSM Stock Evolution: {process_name} ({element.upper()}) - {view_title}"
            layout_config['showlegend'] = True
            layout_config['height'] = 500  # Reduced height
            layout_config['legend'] = {
                'orientation': 'h',
                'yanchor': 'bottom',
                'y': 1.02,
                'xanchor': 'right',
                'x': 1,
                'font': {'size': 10}
            }
            fig.update_layout(**layout_config)
            
            # Update axes with scientific notation (matching validation style)
            fig.update_xaxes(
                title_text="Year",
                showgrid=True,
                gridcolor='#e1e5e9',
                gridwidth=1
            )
            fig.update_yaxes(
                title_text=f"Stock ({element.upper()}) [Mg]", 
                rangemode="tozero", 
                tickformat=".2e",
                zeroline=True,
                zerolinecolor=BIOYM_COLORS['dark'],
                zerolinewidth=2,
                showgrid=True,
                gridcolor='#e1e5e9',
                gridwidth=1
            )
            
            # Set bar mode - use group for side-by-side bars instead of stack
            if show_as_bars:
                fig.update_layout(barmode="group")  # Side-by-side bars instead of stacked

    def export_plot():
        """Export the current plot as PNG with publication standards"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_folder = f"exports/dsm_analysis/{timestamp}"
            os.makedirs(export_folder, exist_ok=True)
            
            current_process = process_dropdown.value
            current_element = element_dropdown.value
            current_view = view_dropdown.value
            
            filename = f"dsm_stock_analysis_{current_process}_{current_element}_{current_view}.png"
            filepath = os.path.join(export_folder, filename)
            
            fig.write_image(filepath, width=1400, height=600, scale=2)
            print(f"✅ DSM stock analysis exported to: {filepath}")
            print(f"📁 Export folder: {export_folder}")
            print(f"🎨 Using shiny color scheme from publication standards")
            
        except Exception as e:
            print(f"❌ Export failed: {e}")
            print("💡 Ensure 'kaleido' is available (uv sync)")

    # Create enhanced widgets
    process_dropdown = Dropdown(
        options=list(dsm_params.keys()), 
        description="DSM Process:",
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
    view_dropdown = Dropdown(
        options=["Annual Values", "Stacked Values"],
        value="Annual Values",
        description="View Mode:",
        style={'description_width': '100px'},
        layout=Layout(width='200px')
    )
    chart_type_checkbox = Checkbox(
        value=False,
        description="Show as Bar Chart",
        style={'description_width': '120px'}
    )
    export_button = Button(
        description="Export PNG",
        button_style='success',
        icon='download',
        layout=Layout(width='120px')
    )
    export_button.on_click(lambda b: export_plot())

    # Create widget layout
    controls = HBox([
        VBox([process_dropdown, element_dropdown], layout=Layout(width='300px')),
        VBox([view_dropdown, chart_type_checkbox], layout=Layout(width='200px')),
        VBox([export_button], layout=Layout(width='120px'))
    ], layout=Layout(justify_content='space-between'))

    # Set up interaction with custom widgets
    def on_change(change):
        update_plot(process_dropdown.value, element_dropdown.value, view_dropdown.value, chart_type_checkbox.value)
    
    process_dropdown.observe(on_change, 'value')
    element_dropdown.observe(on_change, 'value')
    view_dropdown.observe(on_change, 'value')
    chart_type_checkbox.observe(on_change, 'value')
    
    # Display controls and plot
    display(controls)
    display(fig)
    
    # Initial plot
    update_plot(process_dropdown.value, element_dropdown.value, view_dropdown.value, chart_type_checkbox.value)

def plot_process_dynamics_stacked(mfa_system_results, process_definitions):
    """
    Creates a three-panel process dynamics plot showing Input, Stock, and Output
    with stacked elemental composition. Similar to Process Dynamics but shows
    all elements stacked in each subplot.
    
    Features:
    - Three subplots: Input, Stock, Output
    - Stacked flows by element (Material, WC, DM, CC)
    - Shiny element colors and publication standards
    - Bar chart or line chart display options
    - Single PNG export functionality
    - Y-axis starts at 0 with scientific notation for small values

    Args:
        mfa_system_results (odym.MFAsystem): The solved MFA system object.
        process_definitions (pd.DataFrame): The DataFrame from the '2_1_Definition_Processes' sheet.
    """
    from plotly.subplots import make_subplots

    PROCESS_TYPE_COLUMN_NAME = "Process_Type"
    has_type_column = PROCESS_TYPE_COLUMN_NAME in process_definitions.columns
    if not has_type_column:
        print(f"Warning: Column '{PROCESS_TYPE_COLUMN_NAME}' not found. Smart titles disabled.")

    process_options = {p.Name: p.ID for p in mfa_system_results.ProcessList}
    if not process_options:
        print("No processes found to plot.")
        return

    element_items = mfa_system_results.Elements
    # Filter out 'material' since it's composed of WC, DM, CC
    element_items = [elem for elem in element_items if elem.lower() != 'material']
    time_axis = mfa_system_results.IndexTable.Classification["Time"].Items
    
    fig = go.FigureWidget(
        make_subplots(
            rows=1, 
            cols=3, 
            subplot_titles=("Input Flows", "Stock Evolution", "Output Flows"),
            horizontal_spacing=0.1
        )
    )

    def update_plot(process_name, show_as_bars):
        pid = process_options[process_name]

        # Calculate time series data for all elements
        inflow_data = {}
        outflow_data = {}
        stock_data = {}
        
        for elem_idx, element in enumerate(element_items):
            # Get inflow data
            inflows = [
                f.Values[:, elem_idx]
                for f in mfa_system_results.FlowDict.values()
                if f.P_End == pid
            ]
            inflow_data[element] = sum(inflows) if inflows else np.zeros(len(time_axis))
            
            # Get outflow data
            outflows = [
                f.Values[:, elem_idx]
                for f in mfa_system_results.FlowDict.values()
                if f.P_Start == pid
            ]
            outflow_data[element] = sum(outflows) if outflows else np.zeros(len(time_axis))
            
            # Get stock data
            stock_obj = mfa_system_results.StockDict.get(f"S_{pid}")
            if stock_obj:
                stock_data[element] = stock_obj.Values[:, elem_idx]
            else:
                stock_data[element] = np.zeros(len(time_axis))

        # Smart titles based on process type
        subplot_titles = (
            f"Input Flows to '{process_name}'",
            f"Stock in '{process_name}'",
            f"Output Flows from '{process_name}'",
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

        # Choose chart type
        chart_type = go.Bar if show_as_bars else go.Scatter

        with fig.batch_update():
            fig.data, fig.layout.annotations = [], []
            
            # Plot Input Flows (stacked by element)
            for element in element_items:
                element_color = get_element_color(element)
                if show_as_bars:
                    fig.add_trace(
                        chart_type(
                            x=time_axis,
                            y=inflow_data[element],
                            name=f"Input: {element.upper()}",
                            marker_color=element_color,
                            hovertemplate=f"<b>Input {element.upper()}</b><br>Year: %{{x}}<br>Mass: %{{y:.2e}} Mg<extra></extra>"
                        ),
                        row=1, col=1
                    )
                else:
                    fig.add_trace(
                        chart_type(
                            x=time_axis,
                            y=inflow_data[element],
                            mode="lines",
                            name=f"Input: {element.upper()}",
                            line=dict(color=element_color, width=3),
                            hovertemplate=f"<b>Input {element.upper()}</b><br>Year: %{{x}}<br>Mass: %{{y:.2e}} Mg<extra></extra>"
                        ),
                        row=1, col=1
                    )

            # Plot Stock Evolution (stacked by element)
            for element in element_items:
                element_color = get_element_color(element)
                if show_as_bars:
                    fig.add_trace(
                        chart_type(
                            x=time_axis,
                            y=stock_data[element],
                            name=f"Stock: {element.upper()}",
                            marker_color=element_color,
                            hovertemplate=f"<b>Stock {element.upper()}</b><br>Year: %{{x}}<br>Mass: %{{y:.2e}} Mg<extra></extra>"
                        ),
                        row=1, col=2
                    )
                else:
                    fig.add_trace(
                        chart_type(
                            x=time_axis,
                            y=stock_data[element],
                            mode="lines",
                            name=f"Stock: {element.upper()}",
                            line=dict(color=element_color, width=3),
                            hovertemplate=f"<b>Stock {element.upper()}</b><br>Year: %{{x}}<br>Mass: %{{y:.2e}} Mg<extra></extra>"
                        ),
                        row=1, col=2
                    )

            # Plot Output Flows (stacked by element)
            for element in element_items:
                element_color = get_element_color(element)
                if show_as_bars:
                    fig.add_trace(
                        chart_type(
                            x=time_axis,
                            y=outflow_data[element],
                            name=f"Output: {element.upper()}",
                            marker_color=element_color,
                            hovertemplate=f"<b>Output {element.upper()}</b><br>Year: %{{x}}<br>Mass: %{{y:.2e}} Mg<extra></extra>"
                        ),
                        row=1, col=3
                    )
                else:
                    fig.add_trace(
                        chart_type(
                            x=time_axis,
                            y=outflow_data[element],
                            mode="lines",
                            name=f"Output: {element.upper()}",
                            line=dict(color=element_color, width=3),
                            hovertemplate=f"<b>Output {element.upper()}</b><br>Year: %{{x}}<br>Mass: %{{y:.2e}} Mg<extra></extra>"
                        ),
                        row=1, col=3
                    )

            # Apply publication layout with reduced height
            layout_config = get_publication_layout(size='large', show_grid=True)
            layout_config['title'] = f"Process Dynamics (Stacked Elements): {process_name}"
            layout_config['showlegend'] = True
            layout_config['height'] = 500  # Reduced height
            layout_config['legend'] = {
                'orientation': 'h',
                'yanchor': 'bottom',
                'y': 1.02,
                'xanchor': 'right',
                'x': 1,
                'font': {'size': 10}
            }
            fig.update_layout(**layout_config)
            
            # Update subplot titles
            fig.update_annotations(text=subplot_titles)
            
            # Ensure Y-axis starts at 0 and uses scientific notation
            fig.update_yaxes(
                title_text="Mass [Mg]", 
                rangemode="tozero", 
                tickformat=".2e",
                zeroline=True,
                zerolinecolor=BIOYM_COLORS['dark'],
                zerolinewidth=2,
                showgrid=True,
                gridcolor='#e1e5e9',
                gridwidth=1
            )
            
            # Set bar mode for stacking
            if show_as_bars:
                fig.update_layout(barmode="stack")

    def export_plot():
        """Export the current plot as PNG with publication standards"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_folder = f"exports/dynamics/{timestamp}"
            os.makedirs(export_folder, exist_ok=True)
            
            current_process = process_dropdown.value
            
            filename = f"process_dynamics_stacked_{current_process}.png"
            filepath = os.path.join(export_folder, filename)
            
            fig.write_image(filepath, width=1400, height=600, scale=2)
            print(f"✅ Process dynamics (stacked) exported to: {filepath}")
            print(f"📁 Export folder: {export_folder}")
            print(f"🎨 Using shiny color scheme from publication standards")
            
        except Exception as e:
            print(f"❌ Export failed: {e}")
            print("💡 Ensure 'kaleido' is available (uv sync)")

    # Create enhanced widgets
    process_dropdown = Dropdown(
        options=list(process_options.keys()), 
        description="Process:",
        style={'description_width': '80px'},
        layout=Layout(width='300px')
    )
    chart_type_checkbox = Checkbox(
        value=False, 
        description="Show as Bar Chart",
        style={'description_width': '120px'}
    )
    export_button = Button(
        description="Export PNG",
        button_style='success',
        icon='download',
        layout=Layout(width='120px')
    )
    export_button.on_click(lambda b: export_plot())

    # Create widget layout
    controls = HBox([
        VBox([process_dropdown], layout=Layout(width='300px')),
        VBox([chart_type_checkbox, export_button], layout=Layout(width='200px'))
    ], layout=Layout(justify_content='space-between'))

    # Set up interaction with custom widgets
    def on_change(change):
        update_plot(process_dropdown.value, chart_type_checkbox.value)
    
    process_dropdown.observe(on_change, 'value')
    chart_type_checkbox.observe(on_change, 'value')
    
    # Display controls and plot
    display(controls)
    display(fig)
    
    # Initial plot
    update_plot(process_dropdown.value, chart_type_checkbox.value)

def plot_dsm_process_dynamics(mfa_system_results, dsm_params, dsm_details):
    """
    Creates a three-panel DSM process dynamics plot showing Input, Stock, and Output
    with stacked flows by DSM product categories. Shows the different products/materials
    that form the dynamic stock instead of elemental composition.
    
    Features:
    - Three subplots: Input, Stock, Output
    - Stacked flows by DSM product categories (e.g., Insulation Material, Panel Board, Packaging)
    - Shows how different products contribute to the dynamic stock
    - Shiny colors for different product categories
    - Publication standards and typography
    - Bar chart or line chart display options
    - Single PNG export functionality

    Args:
        mfa_system_results (odym.MFAsystem): The solved MFA system object.
        dsm_params (dict): DSM parameters configuration.
        dsm_details (dict): Detailed DSM calculation results.
    """
    if not dsm_params:
        print("No DSM processes found to plot.")
        return

    from plotly.subplots import make_subplots
    from ipywidgets import Dropdown, HBox, VBox, Layout, Button, Checkbox
    from IPython.display import display
    import os
    from datetime import datetime

    time_items = mfa_system_results.IndexTable.Classification["Time"].Items
    
    # Additional shiny colors for DSM product categories
    product_colors = [
        '#FF6B6B',  # Coral red
        '#4ECDC4',  # Turquoise
        '#45B7D1',  # Sky blue
        '#96CEB4',  # Mint green
        '#FFEAA7',  # Light yellow
        '#DDA0DD',  # Plum
        '#98D8C8',  # Seafoam
        '#F7DC6F',  # Golden yellow
    ]

    fig = go.FigureWidget(
        make_subplots(
            rows=1, 
            cols=3, 
            subplot_titles=("Input Flows", "Stock Evolution", "Output Flows"),
            horizontal_spacing=0.1
        )
    )

    def update_plot(process_id, show_as_bars):
        if process_id not in dsm_details:
            print(f"No detailed results for process {process_id}")
            return

        with fig.batch_update():
            fig.data, fig.layout.annotations = [], []
            
            # Choose chart type
            chart_type = go.Bar if show_as_bars else go.Scatter
            
            # Get DSM details for this process
            details = dsm_details[process_id]
            inflow_stocks_material = details.get("inflow_stock_ts_by_cat", [])
            category_names = details.get("category_names", [])
            lifetimes = details.get("lifetimes", [])
            
            # Get total inflow and outflow (material basis)
            total_inflows = [
                f.Values[:, 0]  # Material column (index 0)
                for f in mfa_system_results.FlowDict.values()
                if f.P_End == process_id
            ]
            total_outflows = [
                f.Values[:, 0]  # Material column (index 0)
                for f in mfa_system_results.FlowDict.values()
                if f.P_Start == process_id
            ]
            
            total_inflow_ts = sum(total_inflows) if total_inflows else np.zeros(len(time_items))
            total_outflow_ts = sum(total_outflows) if total_outflows else np.zeros(len(time_items))
            
            # Calculate inflow split by category
            inflow_split = dsm_params[process_id].get('inflow_split', [])
            
            # Plot Input panel (stacked by product categories)
            cumulative_inflow = np.zeros(len(time_items))
            for i, (category_name, split_ratio) in enumerate(zip(category_names, inflow_split)):
                category_inflow = total_inflow_ts * split_ratio
                product_color = product_colors[i % len(product_colors)]
                
                if show_as_bars:
                    fig.add_trace(
                        chart_type(
                            x=time_items,
                            y=category_inflow,
                            name=f"Input: {category_name}",
                            marker_color=product_color,
                            hovertemplate=f"<b>{category_name}</b><br>Year: %{{x}}<br>Input: %{{y:.2e}} Mg<extra></extra>"
                        ),
                        row=1, col=1
                    )
                else:
                    fig.add_trace(
                        chart_type(
                            x=time_items,
                            y=category_inflow,
                            mode="lines+markers",
                            name=f"Input: {category_name}",
                            line=dict(color=product_color, width=3),
                            marker=dict(color=product_color, size=6),
                            hovertemplate=f"<b>{category_name}</b><br>Year: %{{x}}<br>Input: %{{y:.2e}} Mg<extra></extra>"
                        ),
                        row=1, col=1
                    )
            
            # Plot Stock panel (stacked by product categories)
            for i, stock_ts_material in enumerate(inflow_stocks_material):
                category_name = category_names[i] if i < len(category_names) else f"Category {i+1}"
                lifetime = lifetimes[i] if i < len(lifetimes) else "N/A"
                product_color = product_colors[i % len(product_colors)]
                
                if show_as_bars:
                    fig.add_trace(
                        chart_type(
                            x=time_items,
                            y=stock_ts_material,
                            name=f"Stock: {category_name}",
                            marker_color=product_color,
                            hovertemplate=f"<b>{category_name}</b><br>Year: %{{x}}<br>Stock: %{{y:.2e}} Mg<extra></extra>"
                        ),
                        row=1, col=2
                    )
                else:
                    fig.add_trace(
                        chart_type(
                            x=time_items,
                            y=stock_ts_material,
                            mode="lines+markers",
                            name=f"Stock: {category_name}",
                            line=dict(color=product_color, width=3),
                            marker=dict(color=product_color, size=6),
                            hovertemplate=f"<b>{category_name}</b><br>Year: %{{x}}<br>Stock: %{{y:.2e}} Mg<extra></extra>"
                        ),
                        row=1, col=2
                    )
            
            # Plot Output panel (proportional to stock by category)
            total_stock_by_category = sum(inflow_stocks_material) if inflow_stocks_material else np.zeros(len(time_items))
            
            for i, stock_ts_material in enumerate(inflow_stocks_material):
                category_name = category_names[i] if i < len(category_names) else f"Category {i+1}"
                product_color = product_colors[i % len(product_colors)]
                
                # Calculate output proportional to stock (simplified assumption)
                category_output = np.zeros(len(time_items))
                if len(total_stock_by_category) > 0:
                    # Output proportional to stock size
                    stock_ratio = np.divide(
                        stock_ts_material,
                        total_stock_by_category,
                        out=np.zeros(len(time_items)),
                        where=total_stock_by_category != 0
                    )
                    category_output = total_outflow_ts * stock_ratio
                
                if show_as_bars:
                    fig.add_trace(
                        chart_type(
                            x=time_items,
                            y=category_output,
                            name=f"Output: {category_name}",
                            marker_color=product_color,
                            hovertemplate=f"<b>{category_name}</b><br>Year: %{{x}}<br>Output: %{{y:.2e}} Mg<extra></extra>"
                        ),
                        row=1, col=3
                    )
                else:
                    fig.add_trace(
                        chart_type(
                            x=time_items,
                            y=category_output,
                            mode="lines+markers",
                            name=f"Output: {category_name}",
                            line=dict(color=product_color, width=3),
                            marker=dict(color=product_color, size=6),
                            hovertemplate=f"<b>{category_name}</b><br>Year: %{{x}}<br>Output: %{{y:.2e}} Mg<extra></extra>"
                        ),
                        row=1, col=3
                    )
            
            # Apply publication layout with reduced height and legend
            process_name = next(
                (p.Name for p in mfa_system_results.ProcessList if p.ID == process_id),
                f"Process {process_id}",
            )
            
            layout_config = get_publication_layout(size='large', show_grid=True)
            layout_config['title'] = f"DSM Process Dynamics: {process_name} - Product Categories"
            layout_config['showlegend'] = True
            layout_config['height'] = 500  # Reduced height
            layout_config['legend'] = {
                'orientation': 'h',
                'yanchor': 'bottom',
                'y': 1.02,
                'xanchor': 'right',
                'x': 1,
                'font': {'size': 10}
            }
            fig.update_layout(**layout_config)
            
            # Update subplot titles
            fig.update_xaxes(title_text="Year", showgrid=True, gridcolor='#e1e5e9', gridwidth=1)
            fig.update_yaxes(
                title_text="Mass [Mg]", 
                rangemode="tozero", 
                tickformat=".2e",
                zeroline=True,
                zerolinecolor=BIOYM_COLORS['dark'],
                zerolinewidth=2,
                showgrid=True,
                gridcolor='#e1e5e9',
                gridwidth=1
            )
            
            # Set bar mode for stacking
            if show_as_bars:
                fig.update_layout(barmode="stack")

            
            # Update subplot titles
            fig.update_annotations(text=[
                f"Input Flows to '{process_name}'",
                f"Stock in '{process_name}'",
                f"Output Flows from '{process_name}'"
            ])
            
            # Ensure Y-axis starts at 0 and uses scientific notation
            fig.update_yaxes(
                title_text="Mass [Mg]", 
                rangemode="tozero", 
                tickformat=".2e",
                zeroline=True,
                zerolinecolor=BIOYM_COLORS['dark'],
                zerolinewidth=2,
                showgrid=True,
                gridcolor='#e1e5e9',
                gridwidth=1
            )
            
            # Set bar mode for stacking
            if show_as_bars:
                fig.update_layout(barmode="stack")

    def export_plot():
        """Export the current plot as PNG with publication standards"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_folder = f"exports/dsm_analysis/{timestamp}"
            os.makedirs(export_folder, exist_ok=True)
            
            current_process = process_dropdown.value
            
            filename = f"dsm_process_dynamics_{current_process}.png"
            filepath = os.path.join(export_folder, filename)
            
            fig.write_image(filepath, width=1400, height=600, scale=2)
            print(f"✅ DSM process dynamics exported to: {filepath}")
            print(f"📁 Export folder: {export_folder}")
            print(f"🎨 Using shiny color scheme from publication standards")
            
        except Exception as e:
            print(f"❌ Export failed: {e}")
            print("💡 Ensure 'kaleido' is available (uv sync)")

    # Create enhanced widgets
    process_dropdown = Dropdown(
        options=list(dsm_params.keys()), 
        description="DSM Process:",
        style={'description_width': '120px'},
        layout=Layout(width='300px')
    )
    chart_type_checkbox = Checkbox(
        value=False,
        description="Show as Bar Chart",
        style={'description_width': '120px'}
    )
    export_button = Button(
        description="Export PNG",
        button_style='success',
        icon='download',
        layout=Layout(width='120px')
    )
    export_button.on_click(lambda b: export_plot())

    # Create widget layout
    controls = HBox([
        VBox([process_dropdown], layout=Layout(width='300px')),
        VBox([chart_type_checkbox, export_button], layout=Layout(width='200px'))
    ], layout=Layout(justify_content='space-between'))

    # Set up interaction with custom widgets
    def on_change(change):
        update_plot(process_dropdown.value, chart_type_checkbox.value)
    
    process_dropdown.observe(on_change, 'value')
    chart_type_checkbox.observe(on_change, 'value')
    
    # Display controls and plot
    display(controls)
    display(fig)
    
    # Initial plot
    update_plot(process_dropdown.value, chart_type_checkbox.value)

def plot_fomp_stock_details(mfa_system_results, fomp_params):
    """
    Creates detailed stock evolution plots specifically for FOMP processes.
    Shows organic matter accumulation and mineralization with publication standards and shiny colors.
    
    Features:
    - Shiny element colors for stock and flows
    - Stacked view of elements in inflow/outflow
    - Annual vs Cumulative view options
    - Bar chart or line chart display options
    - Publication-quality layout and typography
    - Single PNG export functionality

    Args:
        mfa_system_results (odym.MFAsystem): The solved MFA system object.
        fomp_params (dict): FOMP parameters configuration.
    """
    if not fomp_params:
        print("No FOMP processes found to plot.")
        return

    from ipywidgets import Dropdown, HBox, VBox, HTML, Layout, Button, Checkbox
    from IPython.display import display
    import os
    from datetime import datetime

    time_items = mfa_system_results.IndexTable.Classification["Time"].Items
    element_items = mfa_system_results.Elements

    fig = go.FigureWidget()

    def update_plot(process_id, element, view_mode, show_as_bars):
        # FOMP processes only work with DM (Dry Matter) - exclude WC from mineralization
        if element.lower() == 'wc':
            print("⚠️  Water Content (WC) cannot be mineralized in FOMP processes.")
            print("   Only Dry Matter (DM) undergoes mineralization.")
            print("   Please select DM or CC for FOMP analysis.")
            return
            
        element_index = element_items.index(element)

        with fig.batch_update():
            fig.data = []

            # Get stock data
            stock_obj = mfa_system_results.StockDict.get(f"S_{process_id}")
            if stock_obj is None:
                print(f"No stock data for process {process_id}")
                return

            stock_values = stock_obj.Values[:, element_index]

            # Get shiny element color for stock
            element_color = get_element_color(element)
            
            # Choose chart type
            chart_type = go.Bar if show_as_bars else go.Scatter

            # Plot stock evolution (always shown with element color)
            if show_as_bars:
                fig.add_trace(
                    chart_type(
                        x=time_items,
                        y=stock_values,
                        name=f"{element.upper()} Stock",
                        marker_color=element_color,
                        hovertemplate="<b>Stock</b><br>Year: %{x}<br>Mass: %{y:.2e} Mg<extra></extra>"
                    )
                )
            else:
                fig.add_trace(
                    chart_type(
                        x=time_items,
                        y=stock_values,
                        mode="lines+markers",
                        name=f"{element.upper()} Stock",
                        line=dict(color=element_color, width=3),
                        marker=dict(color=element_color, size=6),
                        hovertemplate="<b>Stock</b><br>Year: %{x}<br>Mass: %{y:.2e} Mg<extra></extra>"
                    )
                )

            # Get inflow and outflow data for all elements (for stacked view)
            inflow_data = {}
            outflow_data = {}
            
            for elem in element_items:
                elem_idx = element_items.index(elem)
                inflow_data[elem] = sum(
                    f.Values[:, elem_idx]
                    for f in mfa_system_results.FlowDict.values()
                    if f.P_End == process_id
                )
                outflow_data[elem] = sum(
                    f.Values[:, elem_idx]
                    for f in mfa_system_results.FlowDict.values()
                    if f.P_Start == process_id
                )

            if view_mode == "Elemental Composition":
                # Plot stacked inflow by element
                for elem in element_items:
                    elem_color = get_element_color(elem)
                    if show_as_bars:
                        fig.add_trace(
                            chart_type(
                                x=time_items,
                                y=inflow_data[elem],
                                name=f"Input: {elem.upper()}",
                                marker_color=elem_color,
                                hovertemplate=f"<b>Inflow {elem.upper()}</b><br>Year: %{{x}}<br>Mass: %{{y:.2e}} Mg<extra></extra>"
                            )
                        )
                    else:
                        fig.add_trace(
                            chart_type(
                                x=time_items,
                                y=inflow_data[elem],
                                mode="lines",
                                name=f"Inflow: {elem.upper()}",
                                line=dict(color=elem_color, width=2, dash="dash"),
                                hovertemplate=f"<b>Inflow {elem.upper()}</b><br>Year: %{{x}}<br>Mass: %{{y:.2e}} Mg<extra></extra>"
                            )
                        )
                
                # Plot stacked outflow by element
                for elem in element_items:
                    elem_color = get_element_color(elem)
                    if show_as_bars:
                        fig.add_trace(
                            chart_type(
                                x=time_items,
                                y=outflow_data[elem],
                                name=f"Outflow: {elem.upper()}",
                                marker_color=elem_color,
                                hovertemplate=f"<b>Outflow {elem.upper()}</b><br>Year: %{{x}}<br>Mass: %{{y:.2e}} Mg<extra></extra>"
                            )
                        )
                    else:
                        fig.add_trace(
                            chart_type(
                                x=time_items,
                                y=outflow_data[elem],
                                mode="lines",
                                name=f"Outflow: {elem.upper()}",
                                line=dict(color=elem_color, width=2, dash="dot"),
                                hovertemplate=f"<b>Outflow {elem.upper()}</b><br>Year: %{{x}}<br>Mass: %{{y:.2e}} Mg<extra></extra>"
                            )
                        )
            else:  # Annual/Cumulative Values
                if view_mode == "Cumulative Values":
                    # Plot cumulative inflow and outflow for selected element
                    cumulative_inflow = np.cumsum(inflow_data[element])
                    cumulative_outflow = np.cumsum(outflow_data[element])

                    if show_as_bars:
                        fig.add_trace(
                            chart_type(
                                x=time_items,
                                y=cumulative_inflow,
                                name="Cumulative Input",
                                marker_color=element_color,
                                hovertemplate="<b>Cumulative Input</b><br>Year: %{x}<br>Mass: %{y:.2e} Mg<extra></extra>"
                            )
                        )
                        fig.add_trace(
                            chart_type(
                                x=time_items,
                                y=cumulative_outflow,
                                name="Cumulative Mineralization",
                                marker_color=element_color,
                                hovertemplate="<b>Cumulative Mineralization</b><br>Year: %{x}<br>Mass: %{y:.2e} Mg<extra></extra>"
                            )
                        )
                    else:
                        fig.add_trace(
                            chart_type(
                                x=time_items,
                                y=cumulative_inflow,
                                mode="lines+markers",
                                name="Cumulative Input",
                                line=dict(color=element_color, width=2, dash="dash"),
                                marker=dict(color=element_color, size=4),
                                hovertemplate="<b>Cumulative Input</b><br>Year: %{x}<br>Mass: %{y:.2e} Mg<extra></extra>"
                            )
                        )
                        fig.add_trace(
                            chart_type(
                                x=time_items,
                                y=cumulative_outflow,
                                mode="lines+markers",
                                name="Cumulative Mineralization",
                                line=dict(color=element_color, width=2, dash="dot"),
                                marker=dict(color=element_color, size=4),
                                hovertemplate="<b>Cumulative Mineralization</b><br>Year: %{x}<br>Mass: %{y:.2e} Mg<extra></extra>"
                            )
                        )
                else:  # Annual Values
                    # Plot annual inflow and outflow for selected element
                    if show_as_bars:
                        fig.add_trace(
                            chart_type(
                                x=time_items,
                                y=inflow_data[element],
                                name="Annual Input",
                                marker_color=element_color,
                                hovertemplate="<b>Annual Input</b><br>Year: %{x}<br>Mass: %{y:.2e} Mg<extra></extra>"
                            )
                        )
                        fig.add_trace(
                            chart_type(
                                x=time_items,
                                y=outflow_data[element],
                                name="Annual Mineralization",
                                marker_color=element_color,
                                hovertemplate="<b>Annual Mineralization</b><br>Year: %{x}<br>Mass: %{y:.2e} Mg<extra></extra>"
                            )
                        )
                    else:
                        fig.add_trace(
                            chart_type(
                                x=time_items,
                                y=inflow_data[element],
                                mode="lines+markers",
                                name="Annual Input",
                                line=dict(color=element_color, width=2, dash="dash"),
                                marker=dict(color=element_color, size=4),
                                hovertemplate="<b>Annual Input</b><br>Year: %{x}<br>Mass: %{y:.2e} Mg<extra></extra>"
                            )
                        )
                        fig.add_trace(
                            chart_type(
                                x=time_items,
                                y=outflow_data[element],
                                mode="lines+markers",
                                name="Annual Mineralization",
                                line=dict(color=element_color, width=2, dash="dot"),
                                marker=dict(color=element_color, size=4),
                                hovertemplate="<b>Annual Mineralization</b><br>Year: %{x}<br>Mass: %{y:.2e} Mg<extra></extra>"
                            )
                        )

            # Apply publication layout with reduced height and legend
            process_name = next(
                (p.Name for p in mfa_system_results.ProcessList if p.ID == process_id),
                f"Process {process_id}",
            )
            
            layout_config = get_publication_layout(size='large', show_grid=True)
            layout_config['title'] = f"FOMP Analysis: {process_name} ({element.upper()}) - {view_mode}"
            layout_config['showlegend'] = True
            layout_config['height'] = 500  # Reduced height
            layout_config['legend'] = {
                'orientation': 'h',
                'yanchor': 'bottom',
                'y': 1.02,
                'xanchor': 'right',
                'x': 1,
                'font': {'size': 10}
            }
            fig.update_layout(**layout_config)
            
            # Update axes with scientific notation (matching validation style)
            fig.update_xaxes(
                title_text="Year",
                showgrid=True,
                gridcolor='#e1e5e9',
                gridwidth=1
            )
            fig.update_yaxes(
                title_text=f"Mass ({element.upper()}) [Mg]", 
                rangemode="tozero", 
                tickformat=".2e",
                zeroline=True,
                zerolinecolor=BIOYM_COLORS['dark'],
                zerolinewidth=2,
                showgrid=True,
                gridcolor='#e1e5e9',
                gridwidth=1
            )
            
            # Set bar mode for stacking
            if show_as_bars and view_mode == "Elemental Composition":
                fig.update_layout(barmode="stack")

    def export_plot():
        """Export the current plot as PNG with publication standards"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_folder = f"exports/fomp_analysis/{timestamp}"
            os.makedirs(export_folder, exist_ok=True)
            
            current_process = process_dropdown.value
            current_element = element_dropdown.value
            current_view = view_dropdown.value
            
            filename = f"fomp_analysis_{current_process}_{current_element}_{current_view}.png"
            filepath = os.path.join(export_folder, filename)
            
            fig.write_image(filepath, width=1400, height=600, scale=2)
            print(f"✅ FOMP analysis exported to: {filepath}")
            print(f"📁 Export folder: {export_folder}")
            print(f"🎨 Using shiny color scheme from publication standards")
            
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
    
    view_dropdown = Dropdown(
        options=["Annual Values", "Cumulative Values", "Elemental Composition"],
        value="Annual Values",
        description="View Mode:",
        style={'description_width': '100px'},
        layout=Layout(width='200px')
    )
    
    chart_type_checkbox = Checkbox(
        value=False,
        description="Show as Bar Chart",
        style={'description_width': '120px'}
    )
    
    export_button = Button(
        description="Export PNG",
        button_style='success',
        icon='download',
        layout=Layout(width='120px')
    )
    export_button.on_click(lambda b: export_plot())

    # Create widget layout
    controls = HBox([
        VBox([process_dropdown, element_dropdown], layout=Layout(width='300px')),
        VBox([view_dropdown, chart_type_checkbox], layout=Layout(width='200px')),
        VBox([export_button], layout=Layout(width='120px'))
    ], layout=Layout(justify_content='space-between'))

    # Set up interaction with custom widgets
    def on_change(change):
        update_plot(process_dropdown.value, element_dropdown.value, view_dropdown.value, chart_type_checkbox.value)
    
    process_dropdown.observe(on_change, 'value')
    element_dropdown.observe(on_change, 'value')
    view_dropdown.observe(on_change, 'value')
    chart_type_checkbox.observe(on_change, 'value')
    
    # Display controls and plot
    display(controls)
    display(fig)
    
    # Initial plot
    update_plot(process_dropdown.value, element_dropdown.value, view_dropdown.value, chart_type_checkbox.value)




def plot_process_dynamics(mfa_system_results, process_definitions, element=None):
    """
    Creates three side-by-side charts showing the dynamics of Inflow, Stock, and Outflow
    for a selected process. Uses shiny colors and publication standards.
    
    Features:
    - Interactive process and element selection
    - Bar chart or line chart display options
    - Shiny color scheme based on element types
    - Publication-quality layout and typography
    - Single PNG export functionality
    - Y-axis starts at 0 with scientific notation for small values

    Args:
        mfa_system_results (odym.MFAsystem): The solved MFA system object.
        process_definitions (pd.DataFrame): The DataFrame from the '2_1_Definition_Processes' sheet.
        element (str, optional): Default element to display. If None, uses first element.
    """
    from plotly.subplots import make_subplots

    PROCESS_TYPE_COLUMN_NAME = "Process_Type"
    has_type_column = PROCESS_TYPE_COLUMN_NAME in process_definitions.columns
    if not has_type_column:
        print(f"Warning: Column '{PROCESS_TYPE_COLUMN_NAME}' not found. Smart titles disabled.")

    process_options = {p.Name: p.ID for p in mfa_system_results.ProcessList}
    if not process_options:
        print("No processes found to plot.")
        return

    element_items = mfa_system_results.Elements
    time_axis = mfa_system_results.IndexTable.Classification["Time"].Items
    
    # Set default element
    if element is None:
        element = element_items[0]
    
    fig = go.FigureWidget(
        make_subplots(
            rows=1, 
            cols=3, 
            subplot_titles=("Inflow", "Stock (S)", "Outflow"),
            horizontal_spacing=0.1
        )
    )

    def update_plot(process_name, element, show_as_bars):
        pid = process_options[process_name]
        element_index = element_items.index(element)

        # Calculate time series data
        inflow_ts = sum(
            (
                f.Values[:, element_index]
                for f in mfa_system_results.FlowDict.values()
                if f.P_End == pid
            ),
            np.zeros(len(time_axis)),
        )
        
        # Handle processes without stock
        stock_obj = mfa_system_results.StockDict.get(f"S_{pid}")
        if stock_obj:
            stock_ts = stock_obj.Values[:, element_index]
        else:
            stock_ts = np.zeros(len(time_axis))

        outflow_ts = sum(
            (
                f.Values[:, element_index]
                for f in mfa_system_results.FlowDict.values()
                if f.P_Start == pid
            ),
            np.zeros(len(time_axis)),
        )

        # Smart titles based on process type
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

        # Get shiny element color
        element_color = get_element_color(element)

        with fig.batch_update():
            fig.data, fig.layout.annotations = [], []
            
            # Choose chart type
            chart_type = go.Bar if show_as_bars else go.Scatter
            
            # Add traces with shiny colors
            if show_as_bars:
                fig.add_trace(
                    chart_type(x=time_axis, y=inflow_ts, name="Inflow", marker_color=element_color),
                    row=1, col=1,
                )
                fig.add_trace(
                    chart_type(x=time_axis, y=stock_ts, name="Stock", marker_color=element_color),
                    row=1, col=2,
                )
                fig.add_trace(
                    chart_type(x=time_axis, y=outflow_ts, name="Outflow", marker_color=element_color),
                    row=1, col=3,
                )
            else:
                fig.add_trace(
                    chart_type(x=time_axis, y=inflow_ts, mode="lines", name="Inflow", 
                              line=dict(color=element_color, width=3)),
                    row=1, col=1,
                )
                fig.add_trace(
                    chart_type(x=time_axis, y=stock_ts, mode="lines", name="Stock", 
                              line=dict(color=element_color, width=3)),
                    row=1, col=2,
                )
                fig.add_trace(
                    chart_type(x=time_axis, y=outflow_ts, mode="lines", name="Outflow", 
                              line=dict(color=element_color, width=3)),
                    row=1, col=3,
                )
            
            # Apply publication layout with reduced height
            layout_config = get_publication_layout(size='large', show_grid=True)
            layout_config['title'] = f"Process Dynamics: {process_name} ({element.upper()})"
            layout_config['showlegend'] = True
            layout_config['height'] = 500  # Reduced height
            layout_config['legend'] = {
                'orientation': 'h',
                'yanchor': 'bottom',
                'y': 1.02,
                'xanchor': 'right',
                'x': 1,
                'font': {'size': 10}
            }
            fig.update_layout(**layout_config)
            
            # Update subplot titles
            fig.update_annotations(text=subplot_titles)
            
            # Ensure Y-axis starts at 0 and uses scientific notation (matching validation style)
            fig.update_yaxes(
                title_text=f"Mass ({element.upper()}) [Mg]", 
                rangemode="tozero", 
                tickformat=".2e",
                zeroline=True,
                zerolinecolor=BIOYM_COLORS['dark'],
                zerolinewidth=2,
                showgrid=True,
                gridcolor='#e1e5e9',
                gridwidth=1
            )
            
            # Also update X-axis for grid
            fig.update_xaxes(
                showgrid=True,
                gridcolor='#e1e5e9',
                gridwidth=1
            )

    def export_plot():
        """Export the current plot as PNG with publication standards"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_folder = f"exports/dynamics/{timestamp}"
            os.makedirs(export_folder, exist_ok=True)
            
            current_process = process_dropdown.value
            current_element = element_dropdown.value
            
            filename = f"process_dynamics_{current_process}_{current_element}.png"
            filepath = os.path.join(export_folder, filename)
            
            fig.write_image(filepath, width=1400, height=600, scale=2)
            print(f"✅ Process dynamics exported to: {filepath}")
            print(f"📁 Export folder: {export_folder}")
            print(f"🎨 Using shiny color scheme from publication standards")
            
        except Exception as e:
            print(f"❌ Export failed: {e}")
            print("💡 Ensure 'kaleido' is available (uv sync)")

    # Create enhanced widgets
    process_dropdown = Dropdown(
        options=list(process_options.keys()), 
        description="Process:",
        style={'description_width': '80px'},
        layout=Layout(width='300px')
    )
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
    export_button = Button(
        description="Export PNG",
        button_style='success',
        icon='download',
        layout=Layout(width='120px')
    )
    export_button.on_click(lambda b: export_plot())

    # Create widget layout
    controls = HBox([
        VBox([process_dropdown, element_dropdown], layout=Layout(width='300px')),
        VBox([chart_type_checkbox, export_button], layout=Layout(width='200px'))
    ], layout=Layout(justify_content='space-between'))

    # Set up interaction with custom widgets
    def on_change(change):
        update_plot(process_dropdown.value, element_dropdown.value, chart_type_checkbox.value)
    
    process_dropdown.observe(on_change, 'value')
    element_dropdown.observe(on_change, 'value')
    chart_type_checkbox.observe(on_change, 'value')
    
    # Display controls and plot
    display(controls)
    display(fig)
    
    # Initial plot
    update_plot(process_dropdown.value, element_dropdown.value, chart_type_checkbox.value)

def plot_system_stock_composition(mfa_system_results, element=None):
    """
    Creates an interactive plot showing individual stocks in the system over time.
    Shows each process stock separately with shiny colors and publication standards.
    
    Features:
    - Interactive element selection
    - Shows individual process stocks over time
    - Bar chart or line chart display options
    - Shiny color scheme based on element types
    - Publication-quality layout and typography
    - Single PNG export functionality
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

    def update_plot(element, show_as_bars):
        element_index = element_items.index(element)
        
        with fig.batch_update():
            fig.data = []
            
            # Get shiny element color
            element_color = get_element_color(element)
            
            # Choose chart type
            chart_type = go.Bar if show_as_bars else go.Scatter
            
            # Plot individual stocks for each process
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
                                marker_color=element_color,
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
                                line=dict(color=element_color, width=3),
                                marker=dict(color=element_color, size=6),
                                name=f"{process_name}",
                                hovertemplate=f"<b>{process_name}</b><br>Year: %{{x}}<br>Stock: %{{y:.2e}} Mg<extra></extra>"
                            )
                        )

            # Apply publication layout with reduced height and legend
            layout_config = get_publication_layout(size='large', show_grid=True)
            layout_config['title'] = f"Individual Process Stocks: {element.upper()} Over Time"
            layout_config['showlegend'] = True
            layout_config['height'] = 500  # Reduced height
            layout_config['legend'] = {
                'orientation': 'h',
                'yanchor': 'bottom',
                'y': 1.02,
                'xanchor': 'right',
                'x': 1,
                'font': {'size': 10}
            }
            fig.update_layout(**layout_config)
            
            # Update axes with scientific notation (matching validation style)
            fig.update_xaxes(
                title_text="Year",
                showgrid=True,
                gridcolor='#e1e5e9',
                gridwidth=1
            )
            fig.update_yaxes(
                title_text=f"Stock ({element.upper()}) [Mg]", 
                rangemode="tozero", 
                tickformat=".2e",
                zeroline=True,
                zerolinecolor=BIOYM_COLORS['dark'],
                zerolinewidth=2,
                showgrid=True,
                gridcolor='#e1e5e9',
                gridwidth=1
            )

    def export_plot():
        """Export the current plot as PNG with publication standards"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_folder = f"exports/dynamics/{timestamp}"
            os.makedirs(export_folder, exist_ok=True)
            
            current_element = element_dropdown.value
            
            filename = f"individual_process_stocks_{current_element}.png"
            filepath = os.path.join(export_folder, filename)
            
            fig.write_image(filepath, width=1400, height=600, scale=2)
            print(f"✅ Individual process stocks exported to: {filepath}")
            print(f"📁 Export folder: {export_folder}")
            print(f"🎨 Using shiny color scheme from publication standards")
            
        except Exception as e:
            print(f"❌ Export failed: {e}")
            print("💡 Ensure 'kaleido' is available (uv sync)")

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
    export_button = Button(
        description="Export PNG",
        button_style='success',
        icon='download',
        layout=Layout(width='120px')
    )
    export_button.on_click(lambda b: export_plot())

    # Create widget layout
    controls = HBox([
        VBox([element_dropdown, chart_type_checkbox], layout=Layout(width='200px')),
        VBox([export_button], layout=Layout(width='120px'))
    ], layout=Layout(justify_content='space-between'))

    # Set up interaction with custom widgets
    def on_change(change):
        update_plot(element_dropdown.value, chart_type_checkbox.value)
    
    element_dropdown.observe(on_change, 'value')
    chart_type_checkbox.observe(on_change, 'value')
    
    # Display controls and plot
    display(controls)
    display(fig)
    
    # Initial plot
    update_plot(element_dropdown.value, chart_type_checkbox.value)


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
                "Input Flows (DM)",
                "Stock Evolution (DM)", 
                "Mineralization Output (DM)",
            ),
        )
    )

    def update_plot(process_name, element):
        pid = process_options[process_name]
        
        # FOMP processes only work with DM (Dry Matter) - exclude WC from mineralization
        if element.lower() == 'wc':
            print("⚠️  Water Content (WC) cannot be mineralized in FOMP processes.")
            print("   Only Dry Matter (DM) undergoes mineralization.")
            print("   Please select DM or CC for FOMP analysis.")
            return
            
        element_index = element_items.index(element)

        # Get the time series data for the selected process
        inflow_ts = np.array([
            f.Values[:, element_index]
            for f in mfa_system_results.FlowDict.values()
            if f.P_End == pid
        ])
        inflow_ts = np.sum(inflow_ts, axis=0) if len(inflow_ts) > 0 else np.zeros(len(time_axis))
        
        stock_obj = mfa_system_results.StockDict.get(f"S_{pid}")
        stock_ts = stock_obj.Values[:, element_index] if stock_obj else np.zeros(len(time_axis))
        
        outflow_ts = np.array([
            f.Values[:, element_index]
            for f in mfa_system_results.FlowDict.values()
            if f.P_Start == pid
        ])
        outflow_ts = np.sum(outflow_ts, axis=0) if len(outflow_ts) > 0 else np.zeros(len(time_axis))

        with fig.batch_update():
            fig.data = []  # Clear existing data
            
            # Get shiny element color
            element_color = get_element_color(element)
            
            fig.add_trace(
                go.Scatter(
                    x=time_axis, 
                    y=inflow_ts, 
                    mode="lines+markers", 
                    name=f"Input ({element.upper()})",
                    line=dict(color=element_color, width=3),
                    marker=dict(color=element_color, size=6),
                    hovertemplate=f"<b>Input {element.upper()}</b><br>Year: %{{x}}<br>Mass: %{{y:.2e}} Mg<extra></extra>"
                ),
                row=1,
                col=1,
            )
            fig.add_trace(
                go.Scatter(
                    x=time_axis, 
                    y=stock_ts, 
                    mode="lines+markers", 
                    name=f"Stock ({element.upper()})",
                    line=dict(color=element_color, width=3),
                    marker=dict(color=element_color, size=6),
                    hovertemplate=f"<b>Stock {element.upper()}</b><br>Year: %{{x}}<br>Stock: %{{y:.2e}} Mg<extra></extra>"
                ),
                row=1,
                col=2,
            )
            fig.add_trace(
                go.Scatter(
                    x=time_axis, 
                    y=outflow_ts, 
                    mode="lines+markers", 
                    name=f"Mineralization Output ({element.upper()})",
                    line=dict(color=element_color, width=3),
                    marker=dict(color=element_color, size=6),
                    hovertemplate=f"<b>Mineralization Output {element.upper()}</b><br>Year: %{{x}}<br>Output: %{{y:.2e}} Mg/year<extra></extra>"
                ),
                row=1,
                col=3,
            )

            # Get FOMP parameters for decay rate display
            fomp_params = fomp_params_config.get(pid, {})
            k_labile = fomp_params.get("decay_k1", 0.5)
            k_recalcitrant = fomp_params.get("decay_k2", 0.025)
            
            # Apply publication layout with reduced height and legend
            layout_config = get_publication_layout(size='large', show_grid=True)
            title_with_rates = f"FOMP Process Dynamics: {process_name} ({element.upper()})<br><sub>Decay Rates: Labile {k_labile*100:.1f}%/year, Recalcitrant {k_recalcitrant*100:.1f}%/year</sub>"
            layout_config['title'] = title_with_rates
            layout_config['showlegend'] = True
            layout_config['height'] = 500  # Reduced height
            layout_config['legend'] = {
                'orientation': 'h',
                'yanchor': 'bottom',
                'y': 1.02,
                'xanchor': 'right',
                'x': 1,
                'font': {'size': 10}
            }
            fig.update_layout(**layout_config)
            
            # Update axes with scientific notation (matching validation style)
            fig.update_xaxes(title_text="Year", showgrid=True, gridcolor='#e1e5e9', gridwidth=1)
            fig.update_yaxes(
                title_text="Mass [Mg]", 
                rangemode="tozero", 
                tickformat=".2e",
                zeroline=True,
                zerolinecolor=BIOYM_COLORS['dark'],
                zerolinewidth=2,
                showgrid=True,
                gridcolor='#e1e5e9',
                gridwidth=1
            )

    # Create widgets for interaction
    process_dropdown = Dropdown(
        options=list(process_options.keys()), description="Process:"
    )
    element_dropdown = Dropdown(
        options=element_items, value=element_items[0], description="Element:"
    )

    # Set up interaction
    from ipywidgets import interact
    interact(
        update_plot,
        process_name=process_dropdown,
        element=element_dropdown,
    )
    display(fig)

def plot_flow_dynamics(mfa_system_results, element=None):
    """
    Creates an interactive chart showing the development of selected flows over time
    for a chosen element. Uses shiny colors and publication standards.
    
    Features:
    - Multi-flow selection with checkboxes
    - Bar chart or line chart display options
    - Shiny color scheme based on element types
    - Publication-quality layout and typography
    - Single PNG export functionality
    - Y-axis starts at 0 with scientific notation for small values

    Args:
        mfa_system_results (odym.MFAsystem): The solved MFA system object.
        element (str, optional): Default element to display. If None, uses first element.
    """
    # Create options for the widgets
    flow_options = sorted(list(mfa_system_results.FlowDict.keys()))
    if not flow_options:
        print("No flows found in the system to plot.")
        return

    element_items = mfa_system_results.Elements
    time_axis = mfa_system_results.IndexTable.Classification["Time"].Items
    
    # Set default element
    if element is None:
        element = element_items[0]

    # Use FigureWidget for efficient updates
    fig = go.FigureWidget()

    def update_plot(flows_to_show, element, show_as_bars):
        # Use batch_update for smooth interaction
        with fig.batch_update():
            fig.data = []  # Clear previous traces
            if not flows_to_show:
                layout_config = get_publication_layout(
                    title="Please select one or more flows to display.",
                    size='large'
                )
                fig.update_layout(**layout_config)
                return

            element_index = element_items.index(element)
            chart_type = go.Bar if show_as_bars else go.Scatter
            
            # Get shiny element color
            element_color = get_element_color(element)

            # Add a trace for each selected flow
            for i, flow_id in enumerate(flows_to_show):
                flow_obj = mfa_system_results.FlowDict.get(flow_id)
                if flow_obj:
                    # Create color variation for multiple flows
                    if len(flows_to_show) > 1:
                        # Use color sequence for multiple flows
                        from .publication_style import create_color_sequence
                        colors = create_color_sequence(len(flows_to_show), base_color=element_color)
                        flow_color = colors[i]
                    else:
                        flow_color = element_color
                    
                    trace_props = dict(
                        x=time_axis, 
                        y=flow_obj.Values[:, element_index], 
                        name=flow_id
                    )
                    
                    if show_as_bars:
                        trace_props.update(marker_color=flow_color)
                    else:
                        trace_props.update(mode="lines", line=dict(color=flow_color, width=3))
                    
                    fig.add_trace(chart_type(**trace_props))

            # Apply publication layout with reduced height
            layout_config = get_publication_layout(size='large', show_grid=True)
            layout_config['title'] = f"Flow Dynamics: Selected Flows ({element.upper()})"
            layout_config['showlegend'] = True
            layout_config['height'] = 500  # Reduced height
            layout_config['legend'] = {
                'orientation': 'h',
                'yanchor': 'bottom',
                'y': 1.02,
                'xanchor': 'right',
                'x': 1,
                'font': {'size': 10}
            }
            fig.update_layout(**layout_config)
            
            # Update axes with scientific notation (matching validation style)
            fig.update_xaxes(title_text="Year")
            fig.update_yaxes(
                title_text=f"Mass ({element.upper()}) [Mg]", 
                rangemode="tozero", 
                tickformat=".2e",
                zeroline=True,
                zerolinecolor=BIOYM_COLORS['dark'],
                zerolinewidth=2
            )
            
            # Set bar mode for stacking
            if show_as_bars:
                fig.update_layout(barmode="stack")

    def export_plot():
        """Export the current plot as PNG with publication standards"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_folder = f"exports/dynamics/{timestamp}"
            os.makedirs(export_folder, exist_ok=True)
            
            current_element = element_dropdown.value
            current_flows = flow_selector.value
            
            # Create filename with flow info
            flows_str = "_".join([f.replace(" ", "_") for f in current_flows[:3]])  # Limit to 3 flows
            if len(current_flows) > 3:
                flows_str += f"_and_{len(current_flows)-3}_more"
            
            filename = f"flow_dynamics_{current_element}_{flows_str}.png"
            filepath = os.path.join(export_folder, filename)
            
            fig.write_image(filepath, width=1400, height=600, scale=2)
            print(f"✅ Flow dynamics exported to: {filepath}")
            print(f"📁 Export folder: {export_folder}")
            print(f"🎨 Using shiny color scheme from publication standards")
            
        except Exception as e:
            print(f"❌ Export failed: {e}")
            print("💡 Ensure 'kaleido' is available (uv sync)")

    # Create enhanced widgets
    flow_selector = SelectMultiple(
        options=flow_options,
        value=[flow_options[0]] if flow_options else [],
        description="Flows:",
        rows=8,
        style={'description_width': '80px'},
        layout=Layout(width='400px')
    )
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
    export_button = Button(
        description="Export PNG",
        button_style='success',
        icon='download',
        layout=Layout(width='120px')
    )
    export_button.on_click(lambda b: export_plot())

    # Create widget layout
    controls = HBox([
        VBox([flow_selector], layout=Layout(width='400px')),
        VBox([element_dropdown, chart_type_checkbox, export_button], layout=Layout(width='200px'))
    ], layout=Layout(justify_content='space-between'))

    # Set up interaction with custom widgets
    def on_change(change):
        update_plot(flow_selector.value, element_dropdown.value, chart_type_checkbox.value)
    
    flow_selector.observe(on_change, 'value')
    element_dropdown.observe(on_change, 'value')
    chart_type_checkbox.observe(on_change, 'value')
    
    # Display controls and plot
    display(controls)
    display(fig)
    
    # Initial plot
    update_plot(flow_selector.value, element_dropdown.value, chart_type_checkbox.value)

def plot_stock_bar_chart(mfa_system, title="Stock Levels Over Time", element=None):
    """
    Generates an interactive bar chart of stock levels with time slider and element selection.
    Uses shiny colors and publication standards.
    
    Features:
    - Interactive year slider and element selection
    - Shiny color scheme based on element types
    - Publication-quality layout and typography
    - Single PNG export functionality
    - Y-axis starts at 0 with scientific notation for small values
    - Process names instead of IDs for better readability

    Args:
        mfa_system (odym.MFAsystem): The MFA system object containing calculated results.
        title (str, optional): The title for the plot.
        element (str, optional): Default element to display. If None, uses first element.
    """
    if not hasattr(mfa_system, 'StockDict') or not mfa_system.StockDict:
        print("No stocks available to plot.")
        return

    years = mfa_system.IndexTable.Classification['Time'].Items
    elements = mfa_system.Elements
    
    # Set default element
    if element is None:
        element = elements[0]
    
    # Create a mapping from process ID to process name
    process_id_to_name = {p.ID: p.Name for p in mfa_system.ProcessList}

    # Prepare the data in a long-format DataFrame for easier filtering
    all_stocks_data = []
    for stock_name, stock in mfa_system.StockDict.items():
        if stock_name.startswith('S_'):
            process_id = int(stock_name.split('_')[1])
            process_name = process_id_to_name.get(process_id, f"Process {process_id}")
            for i, year in enumerate(years):
                for j, element_name in enumerate(elements):
                    all_stocks_data.append({
                        'Year': year,
                        'Element': element_name,
                        'Process': process_name,
                        'Value': stock.Values[i, j]
                    })

    if not all_stocks_data:
        print("No absolute stock data found to plot.")
        return

    df = pd.DataFrame(all_stocks_data)
    fig = go.FigureWidget()

    def update_plot(year, element, show_as_bars):
        with fig.batch_update():
            fig.data = []
            df_filtered = df[(df['Year'] == year) & (df['Element'] == element)]
            
            if df_filtered.empty:
                layout_config = get_publication_layout(
                    title=f"No stock data available for {element.upper()} in {year}",
                    size='large'
                )
                fig.update_layout(**layout_config)
                return
            
            # Get shiny element color
            element_color = get_element_color(element)
            
            # Separate positive and negative values for different styling
            positive_data = df_filtered[df_filtered['Value'] >= 0]
            negative_data = df_filtered[df_filtered['Value'] < 0]
            
            # Choose chart type
            chart_type = go.Bar if show_as_bars else go.Scatter
            
            # Add positive values trace
            if not positive_data.empty:
                if show_as_bars:
                    fig.add_trace(
                        chart_type(
                            x=positive_data['Process'],
                            y=positive_data['Value'],
                            marker_color=element_color,
                            name=f"Positive {element.upper()}",
                            hovertemplate="<b>%{x}</b><br>Stock: %{y:.2e} Mg<extra></extra>"
                        )
                    )
                else:
                    fig.add_trace(
                        chart_type(
                            x=positive_data['Process'],
                            y=positive_data['Value'],
                            mode='markers+lines',
                            marker=dict(color=element_color, size=8),
                            line=dict(color=element_color, width=3),
                            name=f"Positive {element.upper()}",
                            hovertemplate="<b>%{x}</b><br>Stock: %{y:.2e} Mg<extra></extra>"
                        )
                    )
            
            # Add negative values trace with black color
            if not negative_data.empty:
                if show_as_bars:
                    fig.add_trace(
                        chart_type(
                            x=negative_data['Process'],
                            y=negative_data['Value'],
                            marker_color="black",
                            name=f"Negative {element.upper()}",
                            hovertemplate="<b>%{x}</b><br>Stock: %{y:.2e} Mg<extra></extra>"
                        )
                    )
                else:
                    fig.add_trace(
                        chart_type(
                            x=negative_data['Process'],
                            y=negative_data['Value'],
                            mode='markers+lines',
                            marker=dict(color="black", size=8, symbol="diamond"),
                            line=dict(color="black", width=3, dash="dot"),
                            name=f"Negative {element.upper()}",
                            hovertemplate="<b>%{x}</b><br>Stock: %{y:.2e} Mg<extra></extra>"
                        )
                    )

            # Apply publication layout with reduced height and legend
            layout_config = get_publication_layout(size='large', show_grid=True)
            layout_config['title'] = f"{title} - {element.upper()} ({year})"
            layout_config['showlegend'] = True
            layout_config['height'] = 500  # Reduced height
            layout_config['legend'] = {
                'orientation': 'h',
                'yanchor': 'bottom',
                'y': 1.02,
                'xanchor': 'right',
                'x': 1,
                'font': {'size': 10}
            }
            fig.update_layout(**layout_config)
            
            # Update axes with scientific notation (matching validation style)
            fig.update_xaxes(
                title_text="Process Name",
                tickangle=-45,
                showgrid=False
            )
            fig.update_yaxes(
                title_text=f"Stock ({element.upper()}) [Mg]", 
                rangemode="tozero", 
                tickformat=".2e",
                zeroline=True,
                zerolinecolor=BIOYM_COLORS['dark'],
                zerolinewidth=2
            )

    def export_plot():
        """Export the current plot as PNG with publication standards"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_folder = f"exports/dynamics/{timestamp}"
            os.makedirs(export_folder, exist_ok=True)
            
            current_year = year_slider.value
            current_element = element_dropdown.value
            
            filename = f"stock_bar_chart_{current_element}_{current_year}.png"
            filepath = os.path.join(export_folder, filename)
            
            fig.write_image(filepath, width=1400, height=600, scale=2)
            print(f"✅ Stock bar chart exported to: {filepath}")
            print(f"📁 Export folder: {export_folder}")
            print(f"🎨 Using shiny color scheme from publication standards")
            
        except Exception as e:
            print(f"❌ Export failed: {e}")
            print("💡 Ensure 'kaleido' is available (uv sync)")

    # Create enhanced widgets
    year_slider = IntSlider(
        min=min(years), 
        max=max(years), 
        step=1, 
        value=min(years), 
        description='Year',
        style={'description_width': '60px'},
        layout=Layout(width='300px')
    )
    element_dropdown = Dropdown(
        options=elements, 
        value=element,
        description='Element',
        style={'description_width': '80px'},
        layout=Layout(width='200px')
    )
    chart_type_checkbox = Checkbox(
        value=True,  # Default to bar chart for this function
        description="Show as Bar Chart",
        style={'description_width': '120px'}
    )
    export_button = Button(
        description="Export PNG",
        button_style='success',
        icon='download',
        layout=Layout(width='120px')
    )
    export_button.on_click(lambda b: export_plot())

    # Create widget layout
    controls = HBox([
        VBox([year_slider, element_dropdown], layout=Layout(width='300px')),
        VBox([chart_type_checkbox, export_button], layout=Layout(width='200px'))
    ], layout=Layout(justify_content='space-between'))

    # Set up interaction with custom widgets
    def on_change(change):
        update_plot(year_slider.value, element_dropdown.value, chart_type_checkbox.value)
    
    year_slider.observe(on_change, 'value')
    element_dropdown.observe(on_change, 'value')
    chart_type_checkbox.observe(on_change, 'value')
    
    # Display controls and plot
    display(controls)
    display(fig)
    
    # Initial plot
    update_plot(year_slider.value, element_dropdown.value, chart_type_checkbox.value)
