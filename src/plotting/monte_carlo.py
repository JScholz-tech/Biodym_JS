
# -*- coding: utf-8 -*-
"""
Monte Carlo Plotting Module.

This file contains functions for plotting Monte Carlo analysis results.
Combines functionality from monte_carlo.py and mc_visuals.py with publication standards.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from ipywidgets import Dropdown, Button, VBox, HBox, Checkbox
from IPython.display import display
import os
from datetime import datetime

from .publication_style import (
    get_publication_layout,
    get_element_color,
    BIOYM_COLORS
)

def plot_interactive_mc_histogram(mc_results_df):
    """
    Creates an interactive histogram of stock distributions from MC results.
    Uses publication standards with shiny colors and standardized export.
    
    Args:
        mc_results_df (pd.DataFrame): DataFrame with detailed MC results.
    """
    if mc_results_df is None or mc_results_df.empty:
        print("No Monte Carlo results to plot.")
        return

    # Extract unique stock and element names from column headers
    stock_names = sorted(list(set(
        col.split('_')[0] + '_' + col.split('_')[1] 
        for col in mc_results_df.columns if col.startswith('S_') and len(col.split('_')) > 2
    )))
    elements = sorted(list(set(
        col.split('_')[2] 
        for col in mc_results_df.columns if col.startswith('S_') and len(col.split('_')) > 2
    )))

    # --- Create Widgets ---
    stock_dropdown = Dropdown(options=stock_names, description='Stock:')
    element_dropdown = Dropdown(options=elements, description='Element:')
    export_button = Button(description="Export PNG", button_style='success', icon='download')
    fig_widget = go.FigureWidget()

    def update_plot(change):
        """Callback to update the plot when a dropdown value changes."""
        stock = stock_dropdown.value
        element = element_dropdown.value
        col_name = f"{stock}_{element}"

        with fig_widget.batch_update():
            fig_widget.data = []
            fig_widget.layout.shapes = []
            fig_widget.layout.annotations = []

            if col_name not in mc_results_df.columns:
                fig_widget.update_layout(title_text=f"No data available for {col_name}")
                return

            data_series = mc_results_df[col_name]
            mean_val = data_series.mean()
            element_color = get_element_color(element)

            # Add Histogram Trace with shiny element color
            fig_widget.add_trace(go.Histogram(
                x=data_series, 
                nbinsx=30, 
                name='Distribution',
                marker_color=element_color,
                opacity=0.8
            ))

            # Add Mean Line
            fig_widget.add_shape(
                type="line", x0=mean_val, x1=mean_val, y0=0, y1=1, yref="paper",
                line=dict(color=BIOYM_COLORS['dark'], width=2, dash="dash")
            )
            
            # Add Mean Annotation
            fig_widget.add_annotation(
                x=mean_val, y=1.05, yref="paper", text=f"Mean: {mean_val:.2e}",
                showarrow=False, font=dict(color=BIOYM_COLORS['dark'], size=12),
                bgcolor="rgba(255, 255, 255, 0.8)"
            )

            # Apply publication layout
            layout_config = get_publication_layout(size='large', show_grid=True)
            fig_widget.update_layout(**layout_config)
            fig_widget.update_layout(
                title=f"Monte Carlo Distribution: {stock} ({element.upper()})",
                xaxis_title=f"Value ({element.upper()}) [Mg]",
                yaxis_title="Frequency",
                height=500,
                            showlegend=False
            )
            
            # Apply scientific notation and grid
            fig_widget.update_xaxes(
                tickformat=".2e",
                zeroline=True,
                zerolinecolor=BIOYM_COLORS['dark'],
                zerolinewidth=2,
                showgrid=True,
                gridcolor='#e1e5e9',
                gridwidth=1
            )
            fig_widget.update_yaxes(
                zeroline=True,
                zerolinecolor=BIOYM_COLORS['dark'],
                zerolinewidth=2,
                showgrid=True,
                gridcolor='#e1e5e9',
                gridwidth=1
            )

    def on_export_button_clicked(b):
        """Callback to handle the export button click."""
        stock = stock_dropdown.value
        element = element_dropdown.value
        
        # Create organized export directory
        export_dir = "exports/mc_analysis"
        os.makedirs(export_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{export_dir}/mc_histogram_{stock}_{element}_{timestamp}.png"
        
        try:
            fig_widget.write_image(filename, width=1400, height=600, scale=2)
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
    Creates an interactive tornado plot for sensitivity analysis.
    Uses publication standards with shiny colors and standardized export.

    Args:
        mc_results_df (pd.DataFrame): DataFrame with detailed MC results.
    """
    if mc_results_df is None or mc_results_df.empty:
        print("No Monte Carlo results to plot.")
        return

    output_vars = sorted([col for col in mc_results_df.columns if col.startswith('S_')])
    param_vars = sorted([col for col in mc_results_df.columns if col.endswith('_sample')])

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
                marker_color=BIOYM_COLORS['primary'],
                opacity=0.8
            ))
            
            # Apply publication layout
            layout_config = get_publication_layout(size='large', show_grid=True)
            fig_widget.update_layout(**layout_config)
            fig_widget.update_layout(
                title=f"Sensitivity Analysis: {output_var}",
                xaxis_title="Absolute Correlation",
                yaxis_title="Input Parameter",
                height=200 + len(param_vars) * 25,
                margin=dict(l=150) # Adjust left margin for long labels
            )
            
            # Apply grid
            fig_widget.update_xaxes(
                zeroline=True,
                zerolinecolor=BIOYM_COLORS['dark'],
                zerolinewidth=2,
                showgrid=True,
                gridcolor='#e1e5e9',
                gridwidth=1
            )
            fig_widget.update_yaxes(
                zeroline=True,
                zerolinecolor=BIOYM_COLORS['dark'],
                zerolinewidth=2,
                showgrid=True,
                gridcolor='#e1e5e9',
                gridwidth=1
            )

    def on_export_button_clicked(b):
        """Callback to handle the export button click."""
        output_var = output_dropdown.value
        
        export_dir = "exports/mc_analysis"
        os.makedirs(export_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{export_dir}/tornado_plot_{output_var}_{timestamp}.png"
        
        try:
            fig_widget.write_image(filename, width=1400, height=200 + len(param_vars) * 25, scale=2)
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

def plot_interactive_mc_paths(mc_results_df):
    """
    Creates an interactive Monte Carlo paths plot showing multiple simulation trajectories.
    Based on the Python for Finance approach with publication standards.
    Shows all individual simulation paths creating a "fan" visualization of uncertainty.

    Args:
        mc_results_df (pd.DataFrame): DataFrame with detailed MC results.
    """
    if mc_results_df is None or mc_results_df.empty:
        print("No Monte Carlo results to plot.")
        return

    # Extract unique stock and element names from column headers
    stock_names = sorted(list(set(
        col.split('_')[0] + '_' + col.split('_')[1] 
        for col in mc_results_df.columns if col.startswith('S_') and len(col.split('_')) > 2
    )))
    elements = sorted(list(set(
        col.split('_')[2] 
        for col in mc_results_df.columns if col.startswith('S_') and len(col.split('_')) > 2
    )))

    # --- Create Widgets ---
    stock_dropdown = Dropdown(options=stock_names, description='Stock:')
    element_dropdown = Dropdown(options=elements, description='Element:')
    export_button = Button(description="Export PNG", button_style='success', icon='download')
    fig_widget = go.FigureWidget()

    def update_plot(change):
        """Callback to update the plot when the dropdown value changes."""
        stock = stock_dropdown.value
        element = element_dropdown.value
        col_name = f"{stock}_{element}"
        element_color = get_element_color(element)

        with fig_widget.batch_update():
            fig_widget.data = []
            fig_widget.layout.annotations = []

            if col_name not in mc_results_df.columns:
                fig_widget.update_layout(title_text=f"No data available for {col_name}")
                return

            # Get the time series data from actual MC calculations
            timeseries_col_name = f"{col_name}_timeseries"
            
            if timeseries_col_name not in mc_results_df.columns:
                fig_widget.update_layout(title_text=f"No time series data available for {col_name}")
                return
            
            # Extract actual time series data from MC results
            paths_data = []
            time_points = None
            
            for i in range(len(mc_results_df)):
                # Get the actual time series for this iteration
                timeseries_data = mc_results_df[timeseries_col_name].iloc[i]
                
                # Convert to numpy array if it's stored as a list
                if isinstance(timeseries_data, list):
                    path_values = np.array(timeseries_data)
                else:
                    path_values = timeseries_data
                
                paths_data.append(path_values)
                
                # Set time points from the first iteration (should be consistent)
                if time_points is None:
                    time_points = np.arange(len(path_values))
            
            # Limit to 100 paths for performance
            if len(paths_data) > 100:
                # Sample evenly across all iterations
                step = len(paths_data) // 100
                paths_data = paths_data[::step][:100]

            if not paths_data:
                fig_widget.update_layout(title_text=f"No data available for {col_name}")
                return

            # Plot all individual paths (like the Python for Finance approach)
            for i, path_values in enumerate(paths_data):
                fig_widget.add_trace(go.Scatter(
                    x=time_points,
                    y=path_values,
                    mode='lines',
                    line=dict(color=element_color, width=1),
                    opacity=0.6,
                    showlegend=False,
                    name=f'Path {i+1}'
                ))

            # Calculate and plot statistical summaries
            # Mean path
            mean_path = np.mean(paths_data, axis=0)
            fig_widget.add_trace(go.Scatter(
                x=time_points,
                y=mean_path,
                mode='lines',
                line=dict(color=BIOYM_COLORS['dark'], width=3),
                name='Mean Path',
                showlegend=True
            ))

            # Confidence bands (95% and 75%)
            paths_array = np.array(paths_data)
            lower_95 = np.percentile(paths_array, 2.5, axis=0)
            upper_95 = np.percentile(paths_array, 97.5, axis=0)
            lower_75 = np.percentile(paths_array, 12.5, axis=0)
            upper_75 = np.percentile(paths_array, 87.5, axis=0)

            # 95% confidence band
            fig_widget.add_trace(go.Scatter(
                x=time_points,
                y=upper_95,
                mode='lines',
                line=dict(color=BIOYM_COLORS['dark'], width=1, dash='dot'),
                showlegend=False,
                name='95% Upper'
            ))
            fig_widget.add_trace(go.Scatter(
                x=time_points,
                y=lower_95,
                mode='lines',
                line=dict(color=BIOYM_COLORS['dark'], width=1, dash='dot'),
                fill='tonexty',
                fillcolor=f'rgba({int(BIOYM_COLORS["dark"][1:3], 16)}, {int(BIOYM_COLORS["dark"][3:5], 16)}, {int(BIOYM_COLORS["dark"][5:7], 16)}, 0.1)',
                showlegend=False,
                name='95% Confidence'
            ))

            # 75% confidence band
            fig_widget.add_trace(go.Scatter(
                x=time_points,
                y=upper_75,
                mode='lines',
                line=dict(color=BIOYM_COLORS['dark'], width=2, dash='dash'),
                showlegend=False,
                name='75% Upper'
            ))
            fig_widget.add_trace(go.Scatter(
                x=time_points,
                y=lower_75,
                mode='lines',
                line=dict(color=BIOYM_COLORS['dark'], width=2, dash='dash'),
                fill='tonexty',
                fillcolor=f'rgba({int(BIOYM_COLORS["dark"][1:3], 16)}, {int(BIOYM_COLORS["dark"][3:5], 16)}, {int(BIOYM_COLORS["dark"][5:7], 16)}, 0.2)',
                showlegend=True,
                name='75% Confidence'
            ))

            # Apply publication layout
            layout_config = get_publication_layout(size='large', show_grid=True)
            fig_widget.update_layout(**layout_config)
            fig_widget.update_layout(
                title=f"Monte Carlo Paths: {stock} ({element.upper()}) - {len(paths_data)} Actual Simulations",
                xaxis_title="Time (Years)",
                yaxis_title=f"Value ({element.upper()}) [Mg]",
                height=500,
                showlegend=True
            )
            
            # Update axes
            fig_widget.update_xaxes(
                zeroline=True,
                zerolinecolor=BIOYM_COLORS['dark'],
                zerolinewidth=2,
                showgrid=True,
                gridcolor='#e1e5e9',
                gridwidth=1
            )
            fig_widget.update_yaxes(
                tickformat=".2e",
                zeroline=True,
                zerolinecolor=BIOYM_COLORS['dark'],
                zerolinewidth=2,
                showgrid=True,
                gridcolor='#e1e5e9',
                gridwidth=1
            )

    def on_export_button_clicked(b):
        """Callback to handle the export button click."""
        stock = stock_dropdown.value
        element = element_dropdown.value
        
        export_dir = "exports/mc_analysis"
        os.makedirs(export_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{export_dir}/mc_actual_paths_{stock}_{element}_{timestamp}.png"
        
        try:
            fig_widget.write_image(filename, width=1400, height=600, scale=2)
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
