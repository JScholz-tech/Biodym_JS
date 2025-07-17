# -*- coding: utf-8 -*-
"""
Monte Carlo Visualization Module.

This file contains functions for creating interactive visualizations of
Monte Carlo simulation results.
"""

import pandas as pd
import plotly.graph_objects as go
from ipywidgets import interact, Dropdown, Button, Output, VBox, HBox
from IPython.display import display, clear_output

def plot_interactive_mc_histogram(mc_results_df):
    """
    Creates an interactive histogram of stock distributions from MC results,
    with dropdowns for stock and element selection.

    Args:
        mc_results_df (pd.DataFrame): DataFrame with detailed MC results.
    """
    if mc_results_df is None or mc_results_df.empty:
        print("No Monte Carlo results to plot.")
        return

    # Extract unique stock and element names from column headers
    stock_names = sorted(list(set(
        col.split('_')[0] + '_' + col.split('_')[1] 
        for col in mc_results_df.columns if col.startswith('S_')
    )))
    elements = sorted(list(set(
        col.split('_')[2] 
        for col in mc_results_df.columns if col.startswith('S_')
    )))

    if not stock_names or not elements:
        print("Could not parse stock and element names from MC results.")
        return

    stock_dropdown = Dropdown(options=stock_names, description='Stock:')
    element_dropdown = Dropdown(options=elements, description='Element:')
    show_data_button = Button(description="Show/Hide Data")
    output_area = Output()
    fig_widget = go.FigureWidget()

    def update_plot(stock, element):
        col_name = f"{stock}_{element}_mc"
        if col_name not in mc_results_df.columns:
            with fig_widget.batch_update():
                fig_widget.data = []
                fig_widget.update_layout(title_text=f"No data for {col_name}")
            return

        with fig_widget.batch_update():
            fig_widget.data = []
            fig_widget.add_trace(go.Histogram(x=mc_results_df[col_name], nbinsx=30))
            mean_val = mc_results_df[col_name].mean()
            fig_widget.add_vline(x=mean_val, line_dash="dash", line_color="red", 
                               annotation_text=f"Mean: {mean_val:.2f}")
            fig_widget.update_layout(
                title=f"Distribution for {stock} ({element})",
                xaxis_title="Value", yaxis_title="Frequency"
            )

    def on_button_clicked(b):
        with output_area:
            clear_output()
            col_name = f"{stock_dropdown.value}_{element_dropdown.value}_mc"
            if col_name in mc_results_df.columns:
                display(mc_results_df[[col_name]].describe())
                display(mc_results_df[[col_name]].head())

    show_data_button.on_click(on_button_clicked)
    
    # Initial plot
    update_plot(stock_dropdown.value, element_dropdown.value)

    # Link widgets to update function
    interact(update_plot, stock=stock_dropdown, element=element_dropdown)
    
    display(VBox([HBox([stock_dropdown, element_dropdown]), show_data_button, output_area, fig_widget]))

def plot_interactive_tornado(mc_results_df):
    """
    Creates an interactive tornado plot for sensitivity analysis.

    Args:
        mc_results_df (pd.DataFrame): DataFrame with detailed MC results.
    """
    if mc_results_df is None or mc_results_df.empty:
        print("No Monte Carlo results to plot.")
        return

    output_vars = sorted([col for col in mc_results_df.columns if col.endswith('_mc')])
    param_vars = sorted([col for col in mc_results_df.columns if not col.endswith('_mc') and col != 'iteration'])

    if not output_vars or not param_vars:
        print("Insufficient data for tornado plot.")
        return

    output_dropdown = Dropdown(options=output_vars, description='Output:')
    fig_widget = go.FigureWidget()

    def update_plot(output_var):
        correlations = mc_results_df[param_vars].corrwith(mc_results_df[output_var])
        sorted_correlations = correlations.abs().sort_values(ascending=True)

        with fig_widget.batch_update():
            fig_widget.data = []
            fig_widget.add_trace(go.Bar(
                y=sorted_correlations.index,
                x=sorted_correlations.values,
                orientation='h'
            ))
            fig_widget.update_layout(
                title=f"Sensitivity of {output_var}",
                xaxis_title="Absolute Correlation",
                height=200 + len(param_vars) * 25
            )

    # Initial plot
    update_plot(output_dropdown.value)
    
    # Link widget to update function
    interact(update_plot, output_var=output_dropdown)
    display(VBox([output_dropdown, fig_widget]))
