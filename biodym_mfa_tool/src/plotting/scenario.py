# -*- coding: utf-8 -*-
"""
Scenario Plotting Module.

This file contains functions for plotting scenario comparison data.
"""

# -*- coding: utf-8 -*-
"""
Scenario Plotting Module.

This file contains functions for plotting scenario comparison data.
"""

import numpy as np
import plotly.graph_objects as go
from ipywidgets import interact, Dropdown
from IPython.display import display

def plot_stock_comparison(baseline_results, scenario_results, baseline_name="Baseline", scenario_name="Scenario"):
    """
    Creates an interactive line chart to compare a single stock between two model runs,
    with a dropdown to select the stock.
    """
    stock_names = [s for s in baseline_results.StockDict.keys() if s.startswith('S_')]

    def plot_selected_stock(stock_name):
        fig = go.Figure()
        time_vector = baseline_results.IndexTable.Classification['Time'].Items

        # Baseline trace
        baseline_stock = baseline_results.StockDict[stock_name].Values[:, 0]
        fig.add_trace(go.Scatter(x=time_vector, y=baseline_stock, mode='lines', name=baseline_name))

        # Scenario trace
        if stock_name in scenario_results.StockDict:
            scenario_stock = scenario_results.StockDict[stock_name].Values[:, 0]
            fig.add_trace(go.Scatter(x=time_vector, y=scenario_stock, mode='lines', name=scenario_name, line=dict(dash='dash')))
        else:
            fig.add_trace(go.Scatter(x=time_vector, y=np.zeros(len(time_vector)), mode='lines', name=f"{scenario_name} (Not Found)", line=dict(dash='dash')))

        fig.update_layout(
            title=f"Stock Comparison: {stock_name}",
            xaxis_title="Year",
            yaxis_title="Stock Level (Mg)",
            legend_title="Run"
        )
        fig.show()

    interact(plot_selected_stock, stock_name=Dropdown(options=stock_names, description='Select Stock:'))

def plot_flow_comparison(baseline_results, scenario_results, baseline_name="Baseline", scenario_name="Scenario"):
    """
    Creates an interactive line chart to compare a single flow between two model runs,
    with a dropdown to select the flow.
    """
    flow_names = list(baseline_results.FlowDict.keys())
    
    def plot_selected_flow(flow_name):
        fig = go.Figure()
        time_vector = baseline_results.IndexTable.Classification['Time'].Items

        # Baseline trace
        baseline_flow = baseline_results.FlowDict[flow_name].Values[:, 0]
        fig.add_trace(go.Scatter(x=time_vector, y=baseline_flow, mode='lines', name=baseline_name))

        # Scenario trace
        if flow_name in scenario_results.FlowDict:
            scenario_flow = scenario_results.FlowDict[flow_name].Values[:, 0]
            fig.add_trace(go.Scatter(x=time_vector, y=scenario_flow, mode='lines', name=scenario_name, line=dict(dash='dash')))
        else:
            fig.add_trace(go.Scatter(x=time_vector, y=np.zeros(len(time_vector)), mode='lines', name=f"{scenario_name} (Not Found)", line=dict(dash='dash')))

        fig.update_layout(
            title=f"Flow Comparison: {flow_name}",
            xaxis_title="Year",
            yaxis_title="Flow Rate (Mg/year)",
            legend_title="Run"
        )
        fig.show()

    interact(plot_selected_flow, flow_name=Dropdown(options=flow_names, description='Select Flow:'))