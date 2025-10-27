# -*- coding: utf-8 -*-
"""
Scenario Plotting Module.

This file contains functions for plotting scenario comparison data.
Uses publication standards with shiny colors and standardized export.
"""

import numpy as np
import plotly.graph_objects as go
from ipywidgets import Dropdown, VBox, SelectMultiple, HTML, Button, HBox
from IPython.display import display
import os
from datetime import datetime

from .publication_style import (
    get_publication_layout, 
    get_element_color, 
    create_color_sequence,
    BIOYM_COLORS
)


def plot_multi_scenario_comparison(baseline_results, all_scenario_results, scenario_definitions):
    """Creates an interactive comparison plot for multiple scenarios.

    This function generates a bar chart or line diagram to compare key metrics
    (final stock or total flow) across a baseline and multiple user-selected
    scenarios. It also displays the parameter changes for each selected scenario.

    Parameters
    ----------
    baseline_results : odym.MFAsystem
        The solved MFA system object representing the baseline scenario.
    all_scenario_results : dict
        A dictionary where keys are scenario names (str) and values are the
        corresponding solved `odym.MFAsystem` objects for each scenario.
    scenario_definitions : dict
        A dictionary where keys are scenario names (str) and values are lists
        of dictionaries, each describing a parameter change for that scenario.

    Notes
    -----
    The plot is interactive, allowing users to select the metric (final stock
    or total flow), the specific item (stock ID or flow ID), the element,
    the chart type (bar or line), and which scenarios to display. It uses
    publication standards for styling and includes a display of scenario
    parameter definitions.
    """
    if not all_scenario_results:
        print("No scenario results to compare.")
        return

    elements = baseline_results.Elements
    stocks = [s for s in baseline_results.StockDict.keys() if s.startswith('S_')]
    flows = list(baseline_results.FlowDict.keys())
    all_scenarios = list(all_scenario_results.keys())

    # Create mapping from stock IDs to process names for better titles
    stock_id_to_name = {}
    for stock_id in stocks:
        if stock_id.startswith('S_'):
            process_id = int(stock_id.split('_')[1])
            # Find process name from ProcessList
            for process in baseline_results.ProcessList:
                if process.ID == process_id:
                    stock_id_to_name[stock_id] = f"{process.Name} (P{process_id})"
                    break
            if stock_id not in stock_id_to_name:
                stock_id_to_name[stock_id] = f"Process {process_id}"

    # Create mapping from flow IDs to flow names for better titles
    flow_id_to_name = {}
    for flow_id in flows:
        flow_obj = baseline_results.FlowDict.get(flow_id)
        if flow_obj and hasattr(flow_obj, 'Name'):
            flow_id_to_name[flow_id] = f"{flow_obj.Name} ({flow_id})"
        else:
            flow_id_to_name[flow_id] = flow_id

    # --- Widgets ---
    metric_dropdown = Dropdown(options=['Final Stock', 'Total Flow'], description='Metric:')
    item_dropdown = Dropdown(options=stocks, description='Item:')
    element_dropdown = Dropdown(options=elements, description='Element:')
    chart_type_dropdown = Dropdown(options=['Bar Chart', 'Line Diagram'], description='Chart Type:')
    scenario_selector = SelectMultiple(options=all_scenarios, value=all_scenarios, description='Scenarios:', disabled=False)
    parameter_display = HTML(value="")

    def update_item_options(change):
        if change.new == 'Final Stock':
            item_dropdown.options = stocks
        else:
            item_dropdown.options = flows
    
    metric_dropdown.observe(update_item_options, names='value')

    fig = go.FigureWidget()

    def plot_comparison(metric, item, element, chart_type, selected_scenarios):
        with fig.batch_update():
            fig.data = []
            # Phase 1b: Handle element safely
            if element not in elements:
                print(f"⚠️ Element '{element}' not found in system. Available: {elements}")
                return
            element_index = elements.index(element)
            
            scenarios_to_plot = ['Baseline'] + list(selected_scenarios)
            values = []

            # Get baseline value
            if metric == 'Final Stock':
                values.append(baseline_results.StockDict[item].Values[-1, element_index])
            else: # Total Flow
                values.append(np.sum(baseline_results.FlowDict[item].Values[:, element_index]))

            # Get scenario values
            for scenario_name in selected_scenarios:
                scenario_result = all_scenario_results[scenario_name]
                if metric == 'Final Stock':
                    values.append(scenario_result.StockDict.get(item, type('obj', (object,), {'Values': np.zeros_like(baseline_results.StockDict[item].Values)})).Values[-1, element_index])
                else: # Total Flow
                    values.append(np.sum(scenario_result.FlowDict.get(item, type('obj', (object,), {'Values': np.zeros_like(baseline_results.FlowDict[item].Values)})).Values[:, element_index]))
            
            # Get meaningful item name for title
            if metric == 'Final Stock':
                item_display_name = stock_id_to_name.get(item, item)
            else:
                item_display_name = flow_id_to_name.get(item, item)
            
            # Use shiny element color
            element_color = get_element_color(element)
            colors = create_color_sequence(len(scenarios_to_plot), palette='primary')
            
            # Choose chart type
            if chart_type == 'Bar Chart':
                fig.add_trace(go.Bar(
                    x=scenarios_to_plot, 
                    y=values, 
                    name=item,
                    marker_color=colors,
                    opacity=0.8
                ))
            else:  # Line Diagram
                fig.add_trace(go.Scatter(
                    x=scenarios_to_plot, 
                    y=values, 
                    mode='lines+markers',
                    name=item,
                    line=dict(color=element_color, width=3),
                    marker=dict(color=element_color, size=8),
                    opacity=0.8
                ))
            
            # Apply publication layout
            layout_config = get_publication_layout(
                size='large',
                show_grid=True,
                scientific_y=True,
                custom_title=f'{metric} Comparison: {item_display_name} ({element.upper()})',
                y_title=f'Value ({element.upper()}) [Mg]'
            )
            layout_config['height'] = 500
            layout_config['showlegend'] = False
            fig.update_layout(**layout_config)
        
        # Update parameter display
        param_html = "<b>Scenario Definitions:</b><br>"
        for scenario_name in selected_scenarios:
            param_html += f"<b>{scenario_name}:</b><ul>"
            for param in scenario_definitions.get(scenario_name, []):
                param_html += f"<li>{param['Parameter_Name']} {param['Operation']} {param['New_Value']}</li>"
            param_html += "</ul>"
        parameter_display.value = param_html

    # Link widgets with observe pattern
    def update_plot():
        plot_comparison(
            metric_dropdown.value, 
            item_dropdown.value, 
            element_dropdown.value, 
            chart_type_dropdown.value,
            scenario_selector.value
        )
    
    metric_dropdown.observe(lambda change: update_plot(), names='value')
    item_dropdown.observe(lambda change: update_plot(), names='value')
    element_dropdown.observe(lambda change: update_plot(), names='value')
    chart_type_dropdown.observe(lambda change: update_plot(), names='value')
    scenario_selector.observe(lambda change: update_plot(), names='value')
    # Export button click handler is automatically set by create_export_button

    # Initial plot call
    update_plot()

    # Display layout
    controls = HBox([metric_dropdown, item_dropdown, element_dropdown, chart_type_dropdown, scenario_selector])
    display(VBox([controls, fig, parameter_display]))


def plot_scenario_flow_dynamics(baseline_results, all_scenario_results, scenario_definitions):
    """Creates an interactive time-series plot showing flow dynamics for different scenarios.

    This function visualizes the time-series evolution of selected flows,
    comparing their dynamics across a baseline and multiple user-selected
    scenarios. It allows for multi-flow and multi-scenario selection.

    Parameters
    ----------
    baseline_results : odym.MFAsystem
        The solved MFA system object representing the baseline scenario.
    all_scenario_results : dict
        A dictionary where keys are scenario names (str) and values are the
        corresponding solved `odym.MFAsystem` objects for each scenario.
    scenario_definitions : dict
        A dictionary where keys are scenario names (str) and values are lists
        of dictionaries, each describing a parameter change for that scenario.
        (Note: This parameter is currently not directly used in the plot but
        is kept for API consistency).

    Notes
    -----
    The plot is interactive, allowing users to select multiple flows, the
    element, and which scenarios to display. Each scenario's flow is plotted
    as a distinct line, with the baseline clearly marked. Publication standards
    are applied for styling.
    """
    if not all_scenario_results:
        print("No scenario results to compare.")
        return

    elements = baseline_results.Elements
    flows = list(baseline_results.FlowDict.keys())
    all_scenarios = list(all_scenario_results.keys())
    time_axis = baseline_results.IndexTable.Classification["Time"].Items

    # Create mapping from flow IDs to flow names for better titles
    flow_id_to_name = {}
    for flow_id in flows:
        flow_obj = baseline_results.FlowDict.get(flow_id)
        if flow_obj and hasattr(flow_obj, 'Name'):
            flow_id_to_name[flow_id] = f"{flow_obj.Name} ({flow_id})"
        else:
            flow_id_to_name[flow_id] = flow_id

    # --- Widgets ---
    flow_selector = SelectMultiple(options=flows, value=flows[:3], description='Flows:', disabled=False)
    element_dropdown = Dropdown(options=elements, description='Element:')
    scenario_selector = SelectMultiple(options=all_scenarios, value=all_scenarios, description='Scenarios:', disabled=False)


    fig = go.FigureWidget()

    def plot_scenario_flows(selected_flows, element, selected_scenarios):
        with fig.batch_update():
            fig.data = []
            # Phase 1b: Handle element safely
            if element not in elements:
                print(f"⚠️ Element '{element}' not found in system. Available: {elements}")
                return
            element_index = elements.index(element)
            
            # Get element color
            element_color = get_element_color(element)
            
            # Generate distinct colors for scenarios
            scenarios_to_plot = ['Baseline'] + list(selected_scenarios)
            scenario_colors = create_color_sequence(len(scenarios_to_plot), palette='primary')
            
            # Plot each flow for each scenario
            for i, flow_id in enumerate(selected_flows):
                flow_obj = baseline_results.FlowDict.get(flow_id)
                if not flow_obj:
                    continue
                
                flow_name = flow_id_to_name.get(flow_id, flow_id)
                
                # Plot baseline
                fig.add_trace(go.Scatter(
                    x=time_axis,
                    y=flow_obj.Values[:, element_index],
                    mode='lines+markers',
                    name=f'Baseline: {flow_name}',
                    line=dict(color=scenario_colors[0], width=2),
                    marker=dict(color=scenario_colors[0], size=4),
                    opacity=0.8
                ))
                
                # Plot scenarios
                for j, scenario_name in enumerate(selected_scenarios):
                    scenario_result = all_scenario_results[scenario_name]
                    scenario_flow_obj = scenario_result.FlowDict.get(flow_id)
                    
                    if scenario_flow_obj:
                        fig.add_trace(go.Scatter(
                            x=time_axis,
                            y=scenario_flow_obj.Values[:, element_index],
                            mode='lines+markers',
                            name=f'{scenario_name}: {flow_name}',
                            line=dict(color=scenario_colors[j+1], width=2, dash='dash'),
                            marker=dict(color=scenario_colors[j+1], size=4),
                            opacity=0.8
                        ))
            
            # Apply publication layout
            layout_config = get_publication_layout(
                size='large',
                show_grid=True,
                scientific_y=True,
                custom_title=f'Scenario Flow Dynamics: {element.upper()} Over Time',
                x_title='Time (Years)',
                y_title=f'Value ({element.upper()}) [Mg]'
            )
            layout_config['height'] = 600
            layout_config['showlegend'] = True
            fig.update_layout(**layout_config)

    # Link widgets
    def update_plot():
        plot_scenario_flows(
            flow_selector.value,
            element_dropdown.value,
            scenario_selector.value
        )
    
    flow_selector.observe(lambda change: update_plot(), names='value')
    element_dropdown.observe(lambda change: update_plot(), names='value')
    scenario_selector.observe(lambda change: update_plot(), names='value')
    # Export button click handler is automatically set by create_export_button

    # Initial plot call
    update_plot()

    # Display layout
    controls = HBox([flow_selector, element_dropdown, scenario_selector])
    display(VBox([controls, fig]))


def plot_scenario_stock_dynamics(baseline_results, all_scenario_results, scenario_definitions):
    """Creates an interactive time-series plot showing stock dynamics over time for different scenarios.

    This function visualizes the time-series evolution of selected stocks,
    comparing their dynamics across a baseline and multiple user-selected
    scenarios. It allows for multi-stock and multi-scenario selection.

    Parameters
    ----------
    baseline_results : odym.MFAsystem
        The solved MFA system object representing the baseline scenario.
    all_scenario_results : dict
        A dictionary where keys are scenario names (str) and values are the
        corresponding solved `odym.MFAsystem` objects for each scenario.
    scenario_definitions : dict
        A dictionary where keys are scenario names (str) and values are lists
        of dictionaries, each describing a parameter change for that scenario.
        (Note: This parameter is currently not directly used in the plot but
        is kept for API consistency).

    Notes
    -----
    The plot is interactive, allowing users to select multiple stocks, the
    element, and which scenarios to display. Each scenario's stock is plotted
    as a distinct line, with the baseline clearly marked. Publication standards
    are applied for styling.
    """
    if not all_scenario_results:
        print("No scenario results to compare.")
        return

    elements = baseline_results.Elements
    stocks = [s for s in baseline_results.StockDict.keys() if s.startswith('S_')]
    all_scenarios = list(all_scenario_results.keys())
    time_axis = baseline_results.IndexTable.Classification["Time"].Items

    # Create mapping from stock IDs to process names for better titles
    stock_id_to_name = {}
    for stock_id in stocks:
        if stock_id.startswith('S_'):
            process_id = int(stock_id.split('_')[1])
            for process in baseline_results.ProcessList:
                if process.ID == process_id:
                    stock_id_to_name[stock_id] = f"{process.Name} (P{process_id})"
                    break
            if stock_id not in stock_id_to_name:
                stock_id_to_name[stock_id] = f"Process {process_id}"

    # --- Widgets ---
    stock_selector = SelectMultiple(options=stocks, value=stocks[:3] if len(stocks) > 2 else stocks, description='Stocks:', disabled=False)
    element_dropdown = Dropdown(options=elements, description='Element:')
    scenario_selector = SelectMultiple(options=all_scenarios, value=all_scenarios, description='Scenarios:', disabled=False)

    fig = go.FigureWidget()

    def plot_scenario_stocks(selected_stocks, element, selected_scenarios):
        with fig.batch_update():
            fig.data = []
            # Phase 1b: Handle element safely
            if element not in elements:
                print(f"⚠️ Element '{element}' not found in system. Available: {elements}")
                return
            element_index = elements.index(element)
            
            scenarios_to_plot = ['Baseline'] + list(selected_scenarios)
            scenario_colors = create_color_sequence(len(scenarios_to_plot), palette='primary')
            
            for i, stock_id in enumerate(selected_stocks):
                stock_obj = baseline_results.StockDict.get(stock_id)
                if not stock_obj:
                    continue
                
                stock_name = stock_id_to_name.get(stock_id, stock_id)
                
                # Plot baseline
                fig.add_trace(go.Scatter(
                    x=time_axis,
                    y=stock_obj.Values[:, element_index],
                    mode='lines+markers',
                    name=f'Baseline: {stock_name}',
                    line=dict(color=scenario_colors[0], width=2),
                    marker=dict(color=scenario_colors[0], size=4),
                    opacity=0.8
                ))
                
                # Plot scenarios
                for j, scenario_name in enumerate(selected_scenarios):
                    scenario_result = all_scenario_results[scenario_name]
                    scenario_stock_obj = scenario_result.StockDict.get(stock_id)
                    
                    if scenario_stock_obj:
                        fig.add_trace(go.Scatter(
                            x=time_axis,
                            y=scenario_stock_obj.Values[:, element_index],
                            mode='lines+markers',
                            name=f'{scenario_name}: {stock_name}',
                            line=dict(color=scenario_colors[j+1], width=2, dash='dash'),
                            marker=dict(color=scenario_colors[j+1], size=4),
                            opacity=0.8
                        ))
            
            layout_config = get_publication_layout(
                size='large',
                show_grid=True,
                scientific_y=True,
                custom_title=f'Scenario Stock Dynamics: {element.upper()} Over Time',
                x_title='Time (Years)',
                y_title=f'Value ({element.upper()}) [Mg]'
            )
            layout_config['height'] = 600
            layout_config['showlegend'] = True
            fig.update_layout(**layout_config)

    def update_plot():
        plot_scenario_stocks(
            stock_selector.value,
            element_dropdown.value,
            scenario_selector.value
        )
    
    stock_selector.observe(lambda change: update_plot(), names='value')
    element_dropdown.observe(lambda change: update_plot(), names='value')
    scenario_selector.observe(lambda change: update_plot(), names='value')

    update_plot()

    controls = HBox([stock_selector, element_dropdown, scenario_selector])
    display(VBox([controls, fig]))