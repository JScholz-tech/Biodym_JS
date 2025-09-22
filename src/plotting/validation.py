
# -*- coding: utf-8 -*-
import numpy as np
"""
Validation Plotting Module.

This file contains functions for plotting model validation data, such as
mass balance errors.
"""

import plotly.graph_objects as go
from ipywidgets import interact, IntSlider, Dropdown
from IPython.display import display

from .utils import plot_enhanced_export_options

def plot_optimized_mass_balance_error(mfa_system_results):
    """
    Optimized version of mass balance error plot with enhanced performance.
    
    Args:
        mfa_system_results (odym.MFAsystem): The solved MFA system object.
    """
    process_names = [p.Name for p in mfa_system_results.ProcessList]
    time_items = mfa_system_results.IndexTable.Classification["Time"].Items
    element_items = mfa_system_results.Elements

    fig = go.FigureWidget()

    def update_plot(year, element):
        year_index = time_items.index(year)
        element_index = element_items.index(element)

        # Pre-calculate flow sums for better performance
        inflow_sums = {}
        outflow_sums = {}
        
        for flow_id, flow in mfa_system_results.FlowDict.items():
            flow_value = flow.Values[year_index, element_index]
            
            # Inflows
            if flow.P_End not in inflow_sums:
                inflow_sums[flow.P_End] = 0
            inflow_sums[flow.P_End] += flow_value
            
            # Outflows
            if flow.P_Start not in outflow_sums:
                outflow_sums[flow.P_Start] = 0
            outflow_sums[flow.P_Start] += flow_value

        errors = []
        for p in mfa_system_results.ProcessList:
            in_val = inflow_sums.get(p.ID, 0)
            out_val = outflow_sums.get(p.ID, 0)
            
            ds_val = mfa_system_results.StockDict.get(f"dS_{p.ID}", None)
            ds_sum = ds_val.Values[year_index, element_index] if ds_val is not None else 0

            error = in_val - out_val - ds_sum
            errors.append(error)

        # Color bars based on error direction
        colors = [
            "#d62728" if e > 1e-9 else "#2ca02c" if e < -1e-9 else "#7f7f7f"
            for e in errors
        ]

        with fig.batch_update():
            fig.data = []  # Clear previous data
            fig.add_trace(go.Bar(x=process_names, y=errors, marker_color=colors))
            fig.update_layout(
                title=f"Mass Balance Error Check for {element.upper()} in {year}",
                yaxis_title="Error in Mg (positive = mass created)",
                shapes=[
                    dict(
                        type="line",
                        y0=0,
                        y1=0,
                        x0=-0.5,
                        x1=len(process_names) - 0.5,
                        line=dict(color="black", width=2),
                    )
                ],  # Zero line
                height=500,
            )

    # Create widgets
    year_slider = IntSlider(
        min=time_items[0],
        max=time_items[-1],
        step=1,
        value=time_items[0],
        description="Year",
    )
    element_dropdown = Dropdown(
        options=element_items, value=element_items[0], description="Element:"
    )

    interact(update_plot, year=year_slider, element=element_dropdown)
    display(fig)
    
    # Add enhanced export options
    plot_enhanced_export_options(fig, "mass_balance_error")

def plot_total_mass_balance_error(mfa_system_results):
    """
    Creates a static bar chart showing the sum of absolute mass balance errors
    over all years for each process.
    This version calculates the balance manually to avoid bugs in the
    underlying ODYM MassBalance() function.

    Args:
        mfa_system_results (odym.MFAsystem): The solved MFA system object.
    """
    process_names = [p.Name for p in mfa_system_results.ProcessList]
    element_items = mfa_system_results.Elements
    num_processes = len(process_names)
    num_elements = len(element_items)
    num_years = len(mfa_system_results.IndexTable.Classification["Time"].Items)

    # Manually calculate the balance matrix to ensure correctness
    total_inflows = np.zeros((num_years, num_processes, num_elements))
    total_outflows = np.zeros((num_years, num_processes, num_elements))

    for flow in mfa_system_results.FlowDict.values():
        if flow.P_Start < num_processes and flow.P_End < num_processes:
            total_inflows[:, flow.P_End, :] += flow.Values
            total_outflows[:, flow.P_Start, :] += flow.Values

    total_ds = np.zeros((num_years, num_processes, num_elements))
    for p_idx, p in enumerate(mfa_system_results.ProcessList):
        ds_stock = mfa_system_results.StockDict.get(f"dS_{p.ID}")
        if ds_stock is not None:
            total_ds[:, p_idx, :] = ds_stock.Values

    manual_balance_matrix = total_inflows - total_outflows - total_ds

    # The rest of the function uses the manually calculated, correct balance matrix
    total_errors = {element: [] for element in element_items}
    for p_idx, p in enumerate(mfa_system_results.ProcessList):
        for e_idx, element in enumerate(element_items):
            total_error_for_element = np.sum(np.abs(manual_balance_matrix[:, p_idx, e_idx]))
            total_errors[element].append(total_error_for_element)

    fig = go.Figure()
    for element, errors in total_errors.items():
        fig.add_trace(go.Bar(name=element, x=process_names, y=errors))

    fig.update_layout(
        barmode='stack',
        title="General Overview: Total Absolute Mass Balance Error (All Years)",
        yaxis_title="Sum of Absolute Errors (Mg)",
        xaxis_title="Process",
        legend_title="Element"
    )
    fig.show()


def plot_mass_balance_error(mfa_system_results):
    """
    Creates an interactive bar chart showing the mass balance error for each process.
    Error = Inflows - Outflows - dS. An error of 0 means perfect balance.
    This is the FIRST and most important visualization for validation.

    Args:
        mfa_system_results (odym.MFAsystem): The solved MFA system object.
    """
    # Use optimized version
    plot_optimized_mass_balance_error(mfa_system_results)
