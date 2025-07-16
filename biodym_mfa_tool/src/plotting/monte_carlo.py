
# -*- coding: utf-8 -*-
"""
Monte Carlo Plotting Module.

This file contains functions for plotting Monte Carlo analysis results.
"""

import numpy as np
import plotly.graph_objects as go
from ipywidgets import interact, Dropdown
from IPython.display import display

def plot_monte_carlo_integrated_dashboard(mfa_system_results, mc_results=None, dsm_params=None, fomp_params=None):
    """
    Creates an integrated Monte Carlo dashboard that combines deterministic and MC results.
    
    Args:
        mfa_system_results (odym.MFAsystem): The solved MFA system object.
        mc_results (pd.DataFrame, optional): Monte Carlo results DataFrame.
        dsm_params (dict, optional): DSM parameters.
        fomp_params (dict, optional): FOMP parameters.
    """
    from plotly.subplots import make_subplots
    import pandas as pd
    
    # Check if MC results are available
    has_mc = mc_results is not None and hasattr(mc_results, 'empty') and not mc_results.empty
    
    # Create subplot layout
    if has_mc:
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                "Deterministic vs MC Stock Evolution",
                "MC Distribution Analysis", 
                "MC Sensitivity Analysis",
                "MC Confidence Intervals"
            ),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
    else:
        fig = make_subplots(
            rows=1, cols=1,
            subplot_titles=("Stock Evolution (Deterministic Only)")
        )
    
    time_items = mfa_system_results.IndexTable.Classification["Time"].Items
    element_items = mfa_system_results.Elements
    
    # Get stock data
    stock_names = [name for name in mfa_system_results.StockDict.keys() if name.startswith("S_")]
    
    def update_dashboard(element, stock_selection, mc_analysis_type):
        element_index = element_items.index(element)
        
        with fig.batch_update():
            fig.data = []
            
            # Plot 1: Stock Evolution (Deterministic + MC if available)
            if has_mc:
                # Deterministic line
                total_deterministic = np.zeros(len(time_items))
                for stock_name in stock_names:
                    stock_obj = mfa_system_results.StockDict[stock_name]
                    total_deterministic += stock_obj.Values[:, element_index]
                
                fig.add_trace(
                    go.Scatter(
                        x=time_items,
                        y=total_deterministic,
                        mode="lines",
                        name="Deterministic",
                        line=dict(color="#1f77b4", width=3),
                        showlegend=True
                    ),
                    row=1, col=1
                )
                
                # MC mean line
                if mc_results is not None and hasattr(mc_results, 'columns') and f"Total_Stock_{element}" in mc_results.columns:
                    mc_mean = mc_results[f"Total_Stock_{element}"].mean()
                    mc_std = mc_results[f"Total_Stock_{element}"].std()
                    
                    fig.add_trace(
                        go.Scatter(
                            x=time_items,
                            y=[mc_mean] * len(time_items),
                            mode="lines",
                            name="MC Mean",
                            line=dict(color="#ff7f0e", width=2, dash="dash"),
                            showlegend=True
                        ),
                        row=1, col=1
                    )
                    
                    # MC confidence bands
                    fig.add_trace(
                        go.Scatter(
                            x=time_items,
                            y=[mc_mean + 2*mc_std] * len(time_items),
                            mode="lines",
                            name="MC +2σ",
                            line=dict(color="#ff7f0e", width=1, dash="dot"),
                            showlegend=False
                        ),
                        row=1, col=1
                    )
                    
                    fig.add_trace(
                        go.Scatter(
                            x=time_items,
                            y=[mc_mean - 2*mc_std] * len(time_items),
                            mode="lines",
                            name="MC -2σ",
                            line=dict(color="#ff7f0e", width=1, dash="dot"),
                            fill="tonexty",
                            fillcolor="rgba(255,127,14,0.2)",
                            showlegend=False
                        ),
                        row=1, col=1
                    )
                
                # Plot 2: MC Distribution
                if mc_results is not None and hasattr(mc_results, 'columns') and f"Total_Stock_{element}" in mc_results.columns:
                    fig.add_trace(
                        go.Histogram(
                            x=mc_results[f"Total_Stock_{element}"],
                            nbinsx=30,
                            name="MC Distribution",
                            marker_color="#ff7f0e",
                            opacity=0.7
                        ),
                        row=1, col=2
                    )
                
                # Plot 3: MC Sensitivity (if parameter columns exist)
                if mc_analysis_type == "Sensitivity" and mc_results is not None and hasattr(mc_results, 'columns') and len(mc_results.columns) > 2:
                    # Find parameter columns (exclude result columns)
                    param_cols = [col for col in mc_results.columns 
                                if not col.startswith("Total_Stock") and col != "iteration"]
                    if param_cols:
                        param_col = param_cols[0]  # Use first parameter
                        fig.add_trace(
                            go.Scatter(
                                x=mc_results[param_col],
                                y=mc_results[f"Total_Stock_{element}"],
                                mode="markers",
                                name="Sensitivity",
                                marker=dict(color="#2ca02c", size=4, opacity=0.6)
                            ),
                            row=2, col=1
                        )
                
                # Plot 4: MC Confidence Intervals
                if mc_results is not None and hasattr(mc_results, 'columns') and f"Total_Stock_{element}" in mc_results.columns:
                    percentiles = [5, 25, 50, 75, 95]
                    values = [mc_results[f"Total_Stock_{element}"].quantile(p/100) for p in percentiles]
                    
                    fig.add_trace(
                        go.Box(
                            y=mc_results[f"Total_Stock_{element}"],
                            name="MC Distribution",
                            marker_color="#ff7f0e",
                            boxpoints="outliers"
                        ),
                        row=2, col=2
                    )
                
            else:
                # Deterministic only
                total_stock = np.zeros(len(time_items))
                for stock_name in stock_names:
                    stock_obj = mfa_system_results.StockDict[stock_name]
                    total_stock += stock_obj.Values[:, element_index]
                
                fig.add_trace(
                    go.Scatter(
                        x=time_items,
                        y=total_stock,
                        mode="lines",
                        name=f"Total Stock ({element.upper()})",
                        line=dict(color="#1f77b4", width=3)
                    )
                )
            
            # Update layout
            fig.update_layout(
                title=f"Monte Carlo Integrated Dashboard - {element.upper()}",
                height=800 if has_mc else 500,
                showlegend=True
            )
    
    # Create widgets
    element_dropdown = Dropdown(
        options=element_items,
        value=element_items[0],
        description="Element:"
    )
    
    stock_dropdown = Dropdown(
        options=["Total Stock"] + stock_names,
        value="Total Stock",
        description="Stock:"
    )
    
    mc_analysis_dropdown = Dropdown(
        options=["Distribution", "Sensitivity", "Confidence"],
        value="Distribution",
        description="MC Analysis:"
    )
    
    # Create interactive plot
    interact(update_dashboard, 
             element=element_dropdown,
             stock_selection=stock_dropdown,
             mc_analysis_type=mc_analysis_dropdown)
    
    display(fig)

def plot_mc_distribution(df_results, column_name, unit="Mg", title=None):
    """
    Plot Monte Carlo distribution for a specific output parameter.

    Args:
        df_results (pd.DataFrame): Monte Carlo results DataFrame.
        column_name (str): Name of the column to plot.
        unit (str): Unit for the y-axis label.
        title (str, optional): Custom title for the plot.
    """
    if column_name not in df_results.columns:
        print(f"Column '{column_name}' not found in Monte Carlo results.")
        return

    fig = go.Figure()

    fig.add_trace(
        go.Histogram(
            x=df_results[column_name],
            name="Distribution",
            marker_color="#1f77b4",
            opacity=0.7,
        )
    )

    mean_val = df_results[column_name].mean()
    median_val = df_results[column_name].median()
    std_dev = df_results[column_name].std()

    fig.add_vline(
        x=mean_val,
        line_width=3,
        line_dash="dash",
        line_color="#d62728",
        annotation_text=f"Mean: {mean_val:.2f}",
        annotation_position="top right",
    )

    fig.add_vline(
        x=median_val,
        line_width=2,
        line_dash="dot",
        line_color="#2ca02c",
        annotation_text=f"Median: {median_val:.2f}",
        annotation_position="top left",
    )

    if title is None:
        title = f"Monte Carlo Distribution of {column_name}"

    fig.update_layout(
        title_text=title,
        xaxis_title=f"{column_name} ({unit})",
        yaxis_title="Frequency",
        font=dict(size=12),
        showlegend=False,
    )

    fig.show()
