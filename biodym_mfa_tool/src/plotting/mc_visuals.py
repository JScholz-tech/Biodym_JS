# -*- coding: utf-8 -*-
"""
Monte Carlo Visualization Module.

This file contains functions for creating interactive visualizations of
Monte Carlo simulation results.
"""

import pandas as pd
import plotly.graph_objects as go
from ipywidgets import Dropdown, Button, VBox, HBox, Output
from IPython.display import display, clear_output
import os
from datetime import datetime

def plot_interactive_mc_histogram(mc_results_df):
    """
    Creates a polished, interactive histogram of stock distributions from MC results.

    Features a professional design, dropdowns for stock and element selection,
    and an export-to-PNG button.

    Args:
        mc_results_df (pd.DataFrame): DataFrame with detailed MC results.
    """
    if mc_results_df is None or mc_results_df.empty:
        print("No Monte Carlo results to plot.")
        return

    # Extract unique stock and element names from column headers
    stock_names = sorted(list(set(
        col.split('_')[0] + '_' + col.split('_')[1] 
        for col in mc_results_df.columns if col.startswith('S_') and col.endswith('_mc')
    )))
    elements = sorted(list(set(
        col.split('_')[2] 
        for col in mc_results_df.columns if col.startswith('S_') and col.endswith('_mc')
    )))

    if not stock_names or not elements:
        print("Could not parse stock and element names from MC results columns.")
        return

    # --- Create Widgets ---
    stock_dropdown = Dropdown(options=stock_names, description='Stock:')
    element_dropdown = Dropdown(options=elements, description='Element:')
    export_button = Button(description="Export PNG", button_style='success', icon='download')
    fig_widget = go.FigureWidget()

    def update_plot(change):
        """Callback to update the plot when a dropdown value changes."""
        stock = stock_dropdown.value
        element = element_dropdown.value
        col_name = f"{stock}_{element}_mc"

        with fig_widget.batch_update():
            fig_widget.data = [] # Clear previous traces
            if col_name not in mc_results_df.columns:
                fig_widget.update_layout(title_text=f"No data available for {col_name}")
                return

            data_series = mc_results_df[col_name]
            mean_val = data_series.mean()

            # Add Histogram Trace
            fig_widget.add_trace(go.Histogram(
                x=data_series, 
                nbinsx=30, 
                name='Distribution',
                marker_color='#1f77b4'
            ))

            # Add Mean Line
            fig_widget.add_shape(
                type="line", x0=mean_val, x1=mean_val, y0=0, y1=1, yref="paper",
                line=dict(color="red", width=2, dash="dash")
            )
            
            # Add Mean Annotation
            fig_widget.add_annotation(
                x=mean_val, y=1.05, yref="paper", text=f"Mean: {mean_val:.2f}",
                showarrow=False, font=dict(color="red", size=12),
                bgcolor="rgba(255, 255, 255, 0.8)"
            )

            # Update Layout
            fig_widget.update_layout(
                title=dict(
                    text=f"Monte Carlo Distribution for {stock} ({element})",
                    x=0.5,
                    font=dict(size=20, family="Arial, sans-serif")
                ),
                xaxis_title="Value (Mass Units)",
                yaxis_title="Frequency",
                template="plotly_white",
                font=dict(family="Arial, sans-serif", size=12),
                showlegend=False,
                xaxis=dict(linecolor='black', linewidth=1, showgrid=False),
                yaxis=dict(gridcolor='lightgrey', linecolor='black', linewidth=1)
            )

    def on_export_button_clicked(b):
        """Callback to handle the export button click."""
        stock = stock_dropdown.value
        element = element_dropdown.value
        
        # Create a dedicated export directory
        export_dir = "exports/mc_analysis"
        os.makedirs(export_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{export_dir}/mc_histogram_{stock}_{element}_{timestamp}.png"
        
        try:
            fig_widget.write_image(filename, width=1000, height=600, scale=2)
            print(f"✅ Plot exported successfully to: {filename}")
        except Exception as e:
            print(f"❌ Export failed: {e}")
            print("   Ensure 'kaleido' is available (uv sync).")

    # --- Link Widgets and Display ---
    stock_dropdown.observe(update_plot, names='value')
    element_dropdown.observe(update_plot, names='value')
    export_button.on_click(on_export_button_clicked)

    # Initial plot call
    update_plot(None)

    # Display layout
    controls = HBox([stock_dropdown, element_dropdown, export_button])
    display(VBox([controls, fig_widget]))

def plot_interactive_tornado(mc_results_df):
    """
    Creates a polished, interactive tornado plot for sensitivity analysis.

    Features a professional design, a dropdown to select the output variable,
    and an export-to-PNG button.

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

    # --- Create Widgets ---
    output_dropdown = Dropdown(options=output_vars, description='Output Variable:')
    export_button = Button(description="Export PNG", button_style='success', icon='download')
    fig_widget = go.FigureWidget()

    def update_plot(change):
        """Callback to update the plot when the dropdown value changes."""
        output_var = output_dropdown.value
        correlations = mc_results_df[param_vars].corrwith(mc_results_df[output_var])
        sorted_correlations = correlations.abs().sort_values(ascending=True)

        with fig_widget.batch_update():
            fig_widget.data = []
            fig_widget.add_trace(go.Bar(
                y=sorted_correlations.index,
                x=sorted_correlations.values,
                orientation='h',
                marker_color='#1f77b4'
            ))
            fig_widget.update_layout(
                title=dict(
                    text=f"Sensitivity Analysis for {output_var}",
                    x=0.5,
                    font=dict(size=20, family="Arial, sans-serif")
                ),
                xaxis_title="Absolute Correlation",
                yaxis_title="Input Parameter",
                template="plotly_white",
                font=dict(family="Arial, sans-serif", size=12),
                height=200 + len(param_vars) * 25,
                margin=dict(l=150) # Adjust left margin for long labels
            )

    def on_export_button_clicked(b):
        """Callback to handle the export button click."""
        output_var = output_dropdown.value
        
        export_dir = "exports/mc_analysis"
        os.makedirs(export_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{export_dir}/tornado_plot_{output_var}_{timestamp}.png"
        
        try:
            fig_widget.write_image(filename, width=800, height=200 + len(param_vars) * 25, scale=2)
            print(f"✅ Plot exported successfully to: {filename}")
        except Exception as e:
            print(f"❌ Export failed: {e}")
            print("   Ensure 'kaleido' is available (uv sync).")

    # --- Link Widgets and Display ---
    output_dropdown.observe(update_plot, names='value')
    export_button.on_click(on_export_button_clicked)

    update_plot(None) # Initial plot

    controls = HBox([output_dropdown, export_button])
    display(VBox([controls, fig_widget]))
