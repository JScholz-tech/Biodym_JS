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
    """
    Creates an interactive grouped bar chart to compare a metric across multiple scenarios,
    allowing users to select which scenarios to display and view their parameters.
    Uses publication standards with shiny colors and standardized export.

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
    export_button = Button(description="Export PNG", button_style='success', icon='download')
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
            
            # Use shiny element color for bars
            element_color = get_element_color(element)
            colors = create_color_sequence(len(scenarios_to_plot), palette='primary')
            
            fig.add_trace(go.Bar(
                x=scenarios_to_plot, 
                y=values, 
                name=item,
                marker_color=colors,
                opacity=0.8
            ))
            
            # Apply publication layout
            layout_config = get_publication_layout(size='large', show_grid=True)
            fig.update_layout(**layout_config)
            fig.update_layout(
                title=f'{metric} Comparison: {item} ({element.upper()})',
                yaxis_title=f'Value ({element.upper()}) [Mg]',
                height=500,
                showlegend=False
            )
            
            # Update axes with scientific notation and grid
            fig.update_xaxes(
                zeroline=True,
                zerolinecolor=BIOYM_COLORS['dark'],
                zerolinewidth=2,
                showgrid=True,
                gridcolor='#e1e5e9',
                gridwidth=1
            )
            fig.update_yaxes(
                tickformat=".2e",
                zeroline=True,
                zerolinecolor=BIOYM_COLORS['dark'],
                zerolinewidth=2,
                showgrid=True,
                gridcolor='#e1e5e9',
                gridwidth=1
            )
        
        # Update parameter display
        param_html = "<b>Scenario Definitions:</b><br>"
        for scenario_name in selected_scenarios:
            param_html += f"<b>{scenario_name}:</b><ul>"
            for param in scenario_definitions.get(scenario_name, []):
                param_html += f"<li>{param['Parameter_Name']} {param['Operation']} {param['New_Value']}</li>"
            param_html += "</ul>"
        parameter_display.value = param_html

    def on_export_button_clicked(b):
        """Callback to handle the export button click."""
        metric = metric_dropdown.value
        item = item_dropdown.value
        element = element_dropdown.value
        
        # Create organized export directory
        export_dir = "exports/scenario_analysis"
        os.makedirs(export_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{export_dir}/scenario_comparison_{metric}_{item}_{element}_{timestamp}.png"
        
        try:
            fig.write_image(filename, width=1400, height=600, scale=2)
            print(f"✅ Plot exported successfully to: {filename}")
        except Exception as e:
            print(f"❌ Export failed: {e}")
            print("   Ensure 'kaleido' is available (uv sync).")

    # Link widgets with observe pattern instead of interact
    metric_dropdown.observe(lambda change: plot_comparison(metric_dropdown.value, item_dropdown.value, element_dropdown.value, scenario_selector.value), names='value')
    item_dropdown.observe(lambda change: plot_comparison(metric_dropdown.value, item_dropdown.value, element_dropdown.value, scenario_selector.value), names='value')
    element_dropdown.observe(lambda change: plot_comparison(metric_dropdown.value, item_dropdown.value, element_dropdown.value, scenario_selector.value), names='value')
    scenario_selector.observe(lambda change: plot_comparison(metric_dropdown.value, item_dropdown.value, element_dropdown.value, scenario_selector.value), names='value')
    export_button.on_click(on_export_button_clicked)

    # Initial plot call
    plot_comparison(metric_dropdown.value, item_dropdown.value, element_dropdown.value, scenario_selector.value)

    # Display layout
    controls = HBox([metric_dropdown, item_dropdown, element_dropdown, scenario_selector, export_button])
    display(VBox([controls, fig, parameter_display]))