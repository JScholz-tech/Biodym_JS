
# -*- coding: utf-8 -*-
"""
Scenario Plotting Module.

This file contains functions for plotting scenario comparison data.
"""

import numpy as np
import plotly.graph_objects as go
from ipywidgets import interact, Dropdown
from IPython.display import display

def plot_scenario_comparison(scenario_results, comparison_metric="final_stock"):
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
                        if stock_name.startswith("S_"):
                            stock_obj = mfa_system.StockDict[stock_name]
                            final_stocks.append(
                                stock_obj.Values[-1, element_items.index(element)]
                            )

                    fig.add_trace(
                        go.Bar(
                            x=[f"Stock {i + 1}" for i in range(len(final_stocks))],
                            y=final_stocks,
                            name=scenario_name,
                        )
                    )

                    fig.update_layout(
                        title=f"Final Stock Comparison ({element.upper()})",
                        xaxis_title="Stock",
                        yaxis_title="Final Stock in Mg",
                        barmode="group",
                    )

                elif metric_type == "Total Flow":
                    # Compare total system flows
                    time_items = mfa_system.IndexTable.Classification["Time"].Items
                    total_flows = np.zeros(len(time_items))

                    for flow_obj in mfa_system.FlowDict.values():
                        total_flows += flow_obj.Values[:, element_items.index(element)]

                    fig.add_trace(
                        go.Scatter(
                            x=time_items,
                            y=total_flows,
                            mode="lines",
                            name=scenario_name,
                        )
                    )

                    fig.update_layout(
                        title=f"Total System Flow Comparison ({element.upper()})",
                        xaxis_title="Year",
                        yaxis_title="Total Flow in Mg",
                    )

    # Get element items from first scenario
    first_system = list(scenario_results.values())[0]
    element_items = first_system.Elements

    # Create widgets
    metric_dropdown = Dropdown(
        options=["Final Stock", "Total Flow"],
        value="Final Stock",
        description="Comparison Metric:",
    )
    element_dropdown = Dropdown(
        options=element_items, value=element_items[0], description="Element:"
    )

    interact(update_comparison, metric_type=metric_dropdown, element=element_dropdown)
    display(fig)
