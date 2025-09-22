# -*- coding: utf-8 -*-
"""
Scenario Plotting Module.

This file contains functions for plotting scenario comparison data.
"""

import numpy as np
import plotly.graph_objects as go
from ipywidgets import interact, Dropdown, VBox, SelectMultiple, HTML
from IPython.display import display

def plot_multi_scenario_comparison(baseline_results, all_scenario_results, scenario_definitions):
    """
    Creates an interactive grouped bar chart to compare a metric across multiple scenarios,
    allowing users to select which scenarios to display and view their parameters.

    Args:
        baseline_results (odym.MFAsystem): The baseline MFA system results.
        all_scenario_results (dict): Dict with scenario names as keys and results as values.
        scenario_definitions (dict): Dict with scenario names as keys and lists of parameter changes as values.
    """
    if not all_scenario_results:
        print("No scenario results to compare.")
        return

    elements = baseline_results.Elements
    stocks = [s for s in baseline_results.StockDict.keys() if s.startswith('S_')]
    flows = list(baseline_results.FlowDict.keys())
    all_scenarios = list(all_scenario_results.keys())

    # --- Widgets ---
    metric_dropdown = Dropdown(options=['Final Stock', 'Total Flow'], description='Metric:')
    item_dropdown = Dropdown(options=stocks, description='Item:')
    element_dropdown = Dropdown(options=elements, description='Element:')
    scenario_selector = SelectMultiple(options=all_scenarios, value=all_scenarios, description='Scenarios:', disabled=False)
    parameter_display = HTML(value="")

    def update_item_options(change):
        if change.new == 'Final Stock':
            item_dropdown.options = stocks
        else:
            item_dropdown.options = flows
    
    metric_dropdown.observe(update_item_options, names='value')

    fig = go.FigureWidget()

    def plot_comparison(metric, item, element, selected_scenarios):
        with fig.batch_update():
            fig.data = []
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
            
            fig.add_trace(go.Bar(x=scenarios_to_plot, y=values, name=item))
            fig.update_layout(
                title=f'{metric} Comparison: {item} ({element})',
                yaxis_title='Value (Mg)'
            )
        
        # Update parameter display
        param_html = "<b>Scenario Definitions:</b><br>"
        for scenario_name in selected_scenarios:
            param_html += f"<b>{scenario_name}:</b><ul>"
            for param in scenario_definitions.get(scenario_name, []):
                param_html += f"<li>{param['Parameter_Name']} {param['Operation']} {param['New_Value']}</li>"
            param_html += "</ul>"
        parameter_display.value = param_html

    interact(plot_comparison, metric=metric_dropdown, item=item_dropdown, element=element_dropdown, selected_scenarios=scenario_selector)
    display(VBox([metric_dropdown, item_dropdown, element_dropdown, scenario_selector, fig, parameter_display]))