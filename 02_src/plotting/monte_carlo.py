# -*- coding: utf-8 -*-
"""
Monte Carlo Plotting Module.

This file contains functions for plotting Monte Carlo analysis results.
Combines functionality from monte_carlo.py and mc_visuals.py with publication standards.
"""

import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from ipywidgets import (
    Dropdown,
    VBox,
    HBox,
    Output,
    SelectMultiple,
    Label,
    Button,
    Layout,
)
from IPython.display import display, clear_output

from .themes import (
    get_publication_layout,
    get_element_color,
    BIOYM_COLORS,
    apply_theme,
    get_mass_display,
    y_label,
)
from .export_publication import export_figure


def plot_interactive_mc_histogram(mc_results_df, mfa_system_results=None):
    """Creates an interactive histogram of stock distributions from Monte Carlo results.

    This function visualizes the probability distribution of a selected stock
    and element from Monte Carlo simulation results. It displays a histogram
    along with the mean and standard deviation, styled for publication quality.
    Process names are used for better readability when an MFA system is provided.

    Parameters
    ----------
    mc_results_df : pd.DataFrame
        DataFrame containing the detailed Monte Carlo simulation results.
        Expected columns follow the format 'S_X_ELEMENT' (e.g., 'S_0_CC').
    mfa_system_results : odym.MFAsystem, optional
        The MFA system object, used to map process IDs (e.g., 0 in 'S_0')
        to meaningful process names for display. Defaults to None.

    Notes
    -----
    The plot is interactive, allowing the user to select the process and
    the element to display. It includes a mean line and an annotation for
    mean and standard deviation. The histogram shows frequency (count) rather
    than probability density.
    """
    if mc_results_df is None or mc_results_df.empty:
        print("No Monte Carlo results to plot.")
        return

    # Extract unique stock and element names from column headers
    # MC simulation creates columns like: S_7_CC, S_8_DM, etc.
    stock_ids = sorted(
        list(
            set(
                col.split("_")[0] + "_" + col.split("_")[1]
                for col in mc_results_df.columns
                if col.startswith("S_")
                and len(col.split("_")) >= 2
                and not col.endswith("_timeseries")
            )
        )
    )
    elements = sorted(
        list(
            set(
                col.split("_")[2]
                for col in mc_results_df.columns
                if col.startswith("S_")
                and len(col.split("_")) >= 3
                and not col.endswith("_timeseries")
            )
        )
    )

    # Create process name mapping if MFA system is provided
    process_name_map = {}
    if mfa_system_results and hasattr(mfa_system_results, "ProcessList"):
        process_name_map = {p.ID: p.Name for p in mfa_system_results.ProcessList}

    # Create display names (process names if available, otherwise stock IDs)
    stock_display_names = []
    stock_id_to_display = {}
    for stock_id in stock_ids:
        if stock_id.startswith("S_"):
            process_id = int(stock_id.split("_")[1])
            if process_id in process_name_map:
                display_name = f"{process_name_map[process_id]} (S_{process_id})"
            else:
                display_name = stock_id
        else:
            display_name = stock_id

        stock_display_names.append(display_name)
        stock_id_to_display[stock_id] = display_name

    # --- Create Widgets ---
    stock_dropdown = Dropdown(options=stock_display_names, description="Process:")
    element_dropdown = Dropdown(options=elements, description="Element:")
    fig_widget = go.FigureWidget()

    def update_plot(change):
        """Callback to update the plot when a dropdown value changes."""
        display_name = stock_dropdown.value
        element = element_dropdown.value

        # Find the corresponding stock_id
        stock_id = None
        for sid, dname in stock_id_to_display.items():
            if dname == display_name:
                stock_id = sid
                break

        if not stock_id:
            return

        col_name = f"{stock_id}_{element}"

        with fig_widget.batch_update():
            fig_widget.data = []
            fig_widget.layout.shapes = []
            fig_widget.layout.annotations = []

            if col_name not in mc_results_df.columns:
                fig_widget.update_layout(title_text=f"No data available for {col_name}")
                return

            _sc, _unit = get_mass_display()
            data_series = mc_results_df[col_name] * _sc
            mean_val = data_series.mean()
            std_val = data_series.std()
            element_color = get_element_color(element)

            # Add Histogram Trace with frequency (count)
            fig_widget.add_trace(
                go.Histogram(
                    x=data_series,
                    nbinsx=30,
                    name="Distribution",
                    marker_color=element_color,
                    opacity=0.8,
                    histnorm="",  # Use count instead of probability density
                )
            )

            # Add Mean Line
            fig_widget.add_shape(
                type="line",
                x0=mean_val,
                x1=mean_val,
                y0=0,
                y1=1,
                yref="paper",
                line=dict(color=BIOYM_COLORS["dark"], width=2, dash="dash"),
            )

            # Add Mean and Std Annotation
            fig_widget.add_annotation(
                x=mean_val,
                y=1.05,
                yref="paper",
                text=f"Mean: {mean_val:.2f} {_unit}<br>Std: {std_val:.2f} {_unit}",
                showarrow=False,
                font=dict(color=BIOYM_COLORS["dark"], size=15),
                bgcolor="rgba(255, 255, 255, 0.9)",
                bordercolor=BIOYM_COLORS["dark"],
                borderwidth=1,
            )

            # Apply publication layout
            layout_config = get_publication_layout(
                size="large",
                show_grid=True,
                scientific_x=True,
                custom_title=f"Monte Carlo Distribution: {display_name} ({element.upper()})",
                x_title=y_label(element.upper()),
                y_title="Frequency",
            )
            apply_theme(layout_config)
            layout_config["xaxis"].pop("range", None)
            layout_config["xaxis"]["tickformat"] = ","  # comma thousands, no scientific
            layout_config["showlegend"] = False
            fig_widget.update_layout(**layout_config)

    # --- Link Widgets and Display ---
    stock_dropdown.observe(update_plot, names="value")
    element_dropdown.observe(update_plot, names="value")

    export_btn = Button(
        description="Export PNG/SVG",
        button_style="success",
        icon="download",
        layout=Layout(width="160px"),
    )

    def _do_export(b):
        try:
            name = (
                f"mc_histogram_{stock_dropdown.value}_{element_dropdown.value}".replace(
                    " ", "_"
                )
            )
            paths = export_figure(
                fig_widget,
                name,
                formats=["png", "svg"],
                quality="publication",
                size="large",
            )
            print(f"✅ Exported: {', '.join(paths)}")
        except Exception as e:
            print(f"❌ Export failed: {e}")

    export_btn.on_click(_do_export)

    # Initial plot call
    update_plot(None)

    # Display layout
    controls = HBox([stock_dropdown, element_dropdown, export_btn])
    display(VBox([controls, fig_widget]))


def plot_interactive_tornado(mc_results_df):
    """Creates an interactive tornado plot for sensitivity analysis.

    This function visualizes the sensitivity of an output variable to various
    input parameters using a tornado plot. It calculates the absolute correlation
    between each input parameter and the selected output variable, displaying
    them in descending order of influence.

    Parameters
    ----------
    mc_results_df : pd.DataFrame
        DataFrame containing the detailed Monte Carlo simulation results.
        Expected columns include output variables (e.g., 'S_X_ELEMENT') and
        parameter samples (e.g., 'param_name_sample').

    Notes
    -----
    The plot is interactive, allowing the user to select the output variable
    for which to perform the sensitivity analysis. The plot is styled for
    publication quality, with a clear title and axis labels.
    """
    if mc_results_df is None or mc_results_df.empty:
        print("No Monte Carlo results to plot.")
        return

    output_vars = sorted(
        [
            col
            for col in mc_results_df.columns
            if col.startswith("S_") and not col.endswith("_timeseries")
        ]
    )
    param_vars = sorted(
        [col for col in mc_results_df.columns if col.endswith("_sample")]
    )

    if not output_vars or not param_vars:
        print("Insufficient data for tornado plot.")
        return

    # --- Create Widgets ---
    output_dropdown = Dropdown(options=output_vars, description="Output Variable:")
    fig_widget = go.FigureWidget()

    def update_plot(change):
        """Callback to update the plot when the dropdown value changes."""
        output_var = output_dropdown.value
        with np.errstate(invalid="ignore"):
            correlations = mc_results_df[param_vars].corrwith(mc_results_df[output_var])
        correlations = correlations.dropna()
        sorted_correlations = correlations.abs().sort_values(ascending=True)

        with fig_widget.batch_update():
            fig_widget.data = []
            fig_widget.add_trace(
                go.Bar(
                    y=sorted_correlations.index,
                    x=sorted_correlations.values,
                    orientation="h",
                    marker_color=BIOYM_COLORS["primary"],
                    opacity=0.8,
                )
            )

            # Apply publication layout
            layout_config = get_publication_layout(
                size="large",
                show_grid=True,
                custom_title=f"Sensitivity Analysis: {output_var}",
                x_title="Absolute Correlation",
                y_title="Input Parameter",
            )
            apply_theme(layout_config)
            layout_config["xaxis"].pop("range", None)
            layout_config["xaxis"]["tickformat"] = ","
            layout_config["height"] = 200 + len(param_vars) * 25  # data-driven override
            layout_config["margin"]["l"] = 150  # Adjust left margin for long labels
            fig_widget.update_layout(**layout_config)

    # --- Link Widgets and Display ---
    output_dropdown.observe(update_plot, names="value")

    export_btn = Button(
        description="Export PNG/SVG",
        button_style="success",
        icon="download",
        layout=Layout(width="160px"),
    )

    def _do_export(b):
        try:
            name = f"mc_tornado_{output_dropdown.value}".replace(" ", "_")
            paths = export_figure(
                fig_widget,
                name,
                formats=["png", "svg"],
                quality="publication",
                size="large",
            )
            print(f"✅ Exported: {', '.join(paths)}")
        except Exception as e:
            print(f"❌ Export failed: {e}")

    export_btn.on_click(_do_export)

    update_plot(None)  # Initial plot

    controls = HBox([output_dropdown, export_btn])
    display(VBox([controls, fig_widget]))


def plot_interactive_mc_paths(mc_results_df, mfa_system_results=None):
    """Creates an interactive Monte Carlo paths plot showing multiple simulation trajectories.

    This function visualizes the time-series evolution of a selected stock
    across multiple Monte Carlo simulation runs. It displays individual paths
    as a "fan" of uncertainty, along with the mean path and confidence bands
    (e.g., 75% and 95%).

    Parameters
    ----------
    mc_results_df : pd.DataFrame
        DataFrame containing the detailed Monte Carlo simulation results.
        Expected columns include 'S_X_ELEMENT' for aggregated results and
        'S_X_ELEMENT_timeseries' for the full time-series paths.
    mfa_system_results : odym.MFAsystem, optional
        The MFA system object, used to map process IDs (e.g., 0 in 'S_0')
        to meaningful process names for display. Defaults to None.

    Notes
    -----
    The plot is interactive, allowing the user to select the process and
    the element to display. For performance, the number of individual paths
    displayed is limited (e.g., to 100) by sampling evenly from all iterations.
    Confidence bands are calculated using percentiles of the simulation results.
    """
    if mc_results_df is None or mc_results_df.empty:
        print("No Monte Carlo results to plot.")
        return

    # Extract unique stock and element names from column headers
    # MC simulation creates columns like: S_7_CC, S_8_DM, etc.
    stock_ids = sorted(
        list(
            set(
                col.split("_")[0] + "_" + col.split("_")[1]
                for col in mc_results_df.columns
                if col.startswith("S_")
                and len(col.split("_")) >= 2
                and not col.endswith("_timeseries")
            )
        )
    )
    elements = sorted(
        list(
            set(
                col.split("_")[2]
                for col in mc_results_df.columns
                if col.startswith("S_")
                and len(col.split("_")) >= 3
                and not col.endswith("_timeseries")
            )
        )
    )

    # Create process name mapping if MFA system is provided
    process_name_map = {}
    if mfa_system_results and hasattr(mfa_system_results, "ProcessList"):
        process_name_map = {p.ID: p.Name for p in mfa_system_results.ProcessList}

    # Create display names (process names if available, otherwise stock IDs)
    stock_display_names = []
    stock_id_to_display = {}
    for stock_id in stock_ids:
        if stock_id.startswith("S_"):
            process_id = int(stock_id.split("_")[1])
            if process_id in process_name_map:
                display_name = f"{process_name_map[process_id]} (S_{process_id})"
            else:
                display_name = stock_id
        else:
            display_name = stock_id

        stock_display_names.append(display_name)
        stock_id_to_display[stock_id] = display_name

    # --- Create Widgets ---
    stock_dropdown = Dropdown(options=stock_display_names, description="Process:")
    element_dropdown = Dropdown(options=elements, description="Element:")
    fig_widget = go.FigureWidget()

    def update_plot(change):
        """Callback to update the plot when the dropdown value changes."""
        display_name = stock_dropdown.value
        element = element_dropdown.value

        # Find the corresponding stock_id
        stock_id = None
        for sid, dname in stock_id_to_display.items():
            if dname == display_name:
                stock_id = sid
                break

        if not stock_id:
            return

        col_name = f"{stock_id}_{element}"
        element_color = get_element_color(element)

        _sc, _unit = get_mass_display()

        with fig_widget.batch_update():
            fig_widget.data = []
            fig_widget.layout.annotations = []

            if col_name not in mc_results_df.columns:
                fig_widget.update_layout(title_text=f"No data available for {col_name}")
                return

            # Get the time series data from actual MC calculations
            timeseries_col_name = f"{col_name}_timeseries"

            if timeseries_col_name not in mc_results_df.columns:
                fig_widget.update_layout(
                    title_text=f"No time series data available for {col_name}"
                )
                return

            # Extract actual time series data from MC results
            paths_data = []
            time_points = None

            # Use real simulation years if available
            if mfa_system_results and hasattr(mfa_system_results, "IndexTable"):
                time_points = mfa_system_results.IndexTable.Classification["Time"].Items

            for i in range(len(mc_results_df)):
                # Get the actual time series for this iteration
                timeseries_data = mc_results_df[timeseries_col_name].iloc[i]

                # Convert to numpy array if it's stored as a list
                if isinstance(timeseries_data, list):
                    path_values = np.array(timeseries_data)
                else:
                    path_values = timeseries_data

                paths_data.append(path_values * _sc)

                # Fallback: use 0-based index if no system provided
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
                fig_widget.add_trace(
                    go.Scatter(
                        x=time_points,
                        y=path_values,
                        mode="lines",
                        line=dict(color=element_color, width=1),
                        opacity=0.6,
                        showlegend=False,
                        name=f"Path {i + 1}",
                    )
                )

            # Calculate and plot statistical summaries
            # Mean path
            mean_path = np.mean(paths_data, axis=0)
            fig_widget.add_trace(
                go.Scatter(
                    x=time_points,
                    y=mean_path,
                    mode="lines",
                    line=dict(color=BIOYM_COLORS["dark"], width=3),
                    name="Mean Path",
                    showlegend=True,
                )
            )

            # Confidence bands (95% and 75%)
            paths_array = np.array(paths_data)
            lower_95 = np.percentile(paths_array, 2.5, axis=0)
            upper_95 = np.percentile(paths_array, 97.5, axis=0)
            lower_75 = np.percentile(paths_array, 12.5, axis=0)
            upper_75 = np.percentile(paths_array, 87.5, axis=0)

            # 95% confidence band
            fig_widget.add_trace(
                go.Scatter(
                    x=time_points,
                    y=upper_95,
                    mode="lines",
                    line=dict(color=BIOYM_COLORS["dark"], width=1, dash="dot"),
                    showlegend=False,
                    name="95% Upper",
                )
            )
            fig_widget.add_trace(
                go.Scatter(
                    x=time_points,
                    y=lower_95,
                    mode="lines",
                    line=dict(color=BIOYM_COLORS["dark"], width=1, dash="dot"),
                    fill="tonexty",
                    fillcolor=f"rgba({int(BIOYM_COLORS['dark'][1:3], 16)}, {int(BIOYM_COLORS['dark'][3:5], 16)}, {int(BIOYM_COLORS['dark'][5:7], 16)}, 0.1)",
                    showlegend=False,
                    name="95% Confidence",
                )
            )

            # 75% confidence band
            fig_widget.add_trace(
                go.Scatter(
                    x=time_points,
                    y=upper_75,
                    mode="lines",
                    line=dict(color=BIOYM_COLORS["dark"], width=2, dash="dash"),
                    showlegend=False,
                    name="75% Upper",
                )
            )
            fig_widget.add_trace(
                go.Scatter(
                    x=time_points,
                    y=lower_75,
                    mode="lines",
                    line=dict(color=BIOYM_COLORS["dark"], width=2, dash="dash"),
                    fill="tonexty",
                    fillcolor=f"rgba({int(BIOYM_COLORS['dark'][1:3], 16)}, {int(BIOYM_COLORS['dark'][3:5], 16)}, {int(BIOYM_COLORS['dark'][5:7], 16)}, 0.2)",
                    showlegend=True,
                    name="75% Confidence",
                )
            )

            # Apply publication layout
            layout_config = get_publication_layout(
                size="large",
                show_grid=True,
                scientific_y=True,
                custom_title=f"Simulation Trajectories - {display_name} ({element.upper()})",
                x_title="Year",
                y_title=y_label(element.upper()),
            )
            apply_theme(layout_config)
            layout_config["xaxis"].pop("range", None)
            layout_config["xaxis"]["tickformat"] = (
                ","  # comma-formatted years e.g. 2,025
            )
            layout_config["showlegend"] = True
            fig_widget.update_layout(**layout_config)

    # --- Link Widgets and Display ---
    stock_dropdown.observe(update_plot, names="value")
    element_dropdown.observe(update_plot, names="value")

    export_btn = Button(
        description="Export PNG/SVG",
        button_style="success",
        icon="download",
        layout=Layout(width="160px"),
    )

    def _do_export(b):
        try:
            name = f"mc_paths_{stock_dropdown.value}_{element_dropdown.value}".replace(
                " ", "_"
            )
            paths = export_figure(
                fig_widget,
                name,
                formats=["png", "svg"],
                quality="publication",
                size="large",
            )
            print(f"✅ Exported: {', '.join(paths)}")
        except Exception as e:
            print(f"❌ Export failed: {e}")

    export_btn.on_click(_do_export)

    # Initial plot call
    update_plot(None)

    # Display layout
    controls = HBox([stock_dropdown, element_dropdown, export_btn])
    display(VBox([controls, fig_widget]))


def plot_interactive_mc_multiple_histograms(mc_results_df, mfa_system_results=None):
    """Creates multiple interactive histogram plots for selected Monte Carlo results.

    This function provides a multi-select interface to choose several stocks and
    displays a separate, interactive histogram for each one. The plots are
    rendered inside a Jupyter widget layout, updating dynamically when the
    selection changes. It uses `go.FigureWidget` to ensure compatibility with
    `ipywidgets`.

    Parameters
    ----------
    mc_results_df : pd.DataFrame
        DataFrame containing the Monte Carlo simulation results. Expected
        columns follow the format 'S_X_ELEMENT' (e.g., 'S_0_CC').
    mfa_system_results : odym.MFAsystem, optional
        The MFA system object, used to map process IDs (e.g., 0 in 'S_0')
        to meaningful process names for display. Defaults to None.

    Notes
    -----
    Each histogram includes a mean line and an annotation for mean and standard
    deviation, styled for publication quality. The plots are contained within
    a `VBox` widget, allowing for a flexible display of multiple distributions.
    """
    if mc_results_df is None or mc_results_df.empty:
        print("No Monte Carlo results to plot.")
        return

    # Extract unique stock IDs and elements from DataFrame columns
    stock_ids = sorted(
        list(
            set(
                f"{col.split('_')[0]}_{col.split('_')[1]}"
                for col in mc_results_df.columns
                if col.startswith("S_")
                and len(col.split("_")) >= 3
                and not col.endswith("_timeseries")
            )
        )
    )
    elements = sorted(
        list(
            set(
                col.split("_")[2]
                for col in mc_results_df.columns
                if col.startswith("S_")
                and len(col.split("_")) >= 3
                and not col.endswith("_timeseries")
            )
        )
    )

    if not stock_ids or not elements:
        print("No valid stock data found in Monte Carlo results.")
        return

    # Create a mapping from process ID to process name if the MFA system is provided
    process_name_map = {}
    if mfa_system_results and hasattr(mfa_system_results, "ProcessList"):
        process_name_map = {p.ID: p.Name for p in mfa_system_results.ProcessList}

    # Generate user-friendly display names for the selection widget
    stock_id_to_display = {
        stock_id: (
            f"{process_name_map.get(int(stock_id.split('_')[1]), stock_id)} ({stock_id})"
        )
        for stock_id in stock_ids
    }
    stock_display_names = [stock_id_to_display[sid] for sid in stock_ids]

    # --- Create Widgets ---
    element_dropdown = Dropdown(options=elements, description="Element:")
    stock_multiselect = SelectMultiple(
        options=stock_display_names,
        value=[stock_display_names[0]] if stock_display_names else [],
        description="Select Stocks:",
        rows=min(10, len(stock_display_names)),
        layout={"width": "400px"},
    )
    plot_container = VBox()  # Container for the histogram widgets

    def render_histogram(out, stock_id, element, display_name):
        """Render a single histogram into an Output widget."""
        col_name = f"{stock_id}_{element}"
        with out:
            clear_output(wait=True)
            if col_name not in mc_results_df.columns:
                print(f"No data for {col_name}")
                return

            _sc, _unit = get_mass_display()
            scaled_series = mc_results_df[col_name] * _sc
            mean_val = scaled_series.mean()
            std_val = scaled_series.std()
            element_color = get_element_color(element)

            fig = go.Figure()
            fig.add_trace(
                go.Histogram(
                    x=scaled_series,
                    nbinsx=30,
                    name="Distribution",
                    marker_color=element_color,
                    opacity=0.8,
                    histnorm="",
                )
            )
            fig.add_shape(
                type="line",
                x0=mean_val,
                x1=mean_val,
                y0=0,
                y1=1,
                yref="paper",
                line=dict(color=BIOYM_COLORS["dark"], width=2, dash="dash"),
            )
            fig.add_annotation(
                x=mean_val,
                y=1.05,
                yref="paper",
                text=f"Mean: {mean_val:.2f} {_unit}<br>Std: {std_val:.2f} {_unit}",
                showarrow=False,
                font=dict(color=BIOYM_COLORS["dark"], size=15),
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor=BIOYM_COLORS["dark"],
                borderwidth=1,
            )
            layout_config = get_publication_layout(
                size="medium",
                show_grid=True,
                custom_title=f"MC Distribution — {display_name} ({element.upper()})",
                x_title=y_label(element.upper()),
                y_title="Frequency",
            )
            apply_theme(layout_config)
            layout_config["xaxis"].pop("range", None)
            layout_config["xaxis"]["tickformat"] = ","  # comma thousands, no scientific
            layout_config["showlegend"] = False
            fig.update_layout(**layout_config)

            export_btn = Button(
                description="Export PNG/SVG",
                button_style="success",
                icon="download",
                layout=Layout(width="160px"),
            )

            def _do_export(b, _fig=fig, _stock_id=stock_id, _element=element):
                try:
                    name = f"mc_histogram_{_stock_id}_{_element}".replace(" ", "_")
                    paths = export_figure(
                        _fig,
                        name,
                        formats=["png", "svg"],
                        quality="publication",
                        size="medium",
                    )
                    print(f"✅ Exported: {', '.join(paths)}")
                except Exception as e:
                    print(f"❌ Export failed: {e}")

            export_btn.on_click(_do_export)
            display(export_btn)
            fig.show()

    def update_plots(change):
        """Rebuild Output widgets for each selected stock."""
        element = element_dropdown.value
        selected_display_names = stock_multiselect.value
        display_to_stock_id = {v: k for k, v in stock_id_to_display.items()}

        outputs = []
        for display_name in selected_display_names:
            stock_id = display_to_stock_id.get(display_name)
            if stock_id:
                out = Output()
                render_histogram(out, stock_id, element, display_name)
                outputs.append(out)

        plot_container.children = (
            tuple(outputs) if outputs else (Label("No data for selection."),)
        )

    # --- Link Widgets and Display ---
    element_dropdown.observe(update_plots, names="value")
    stock_multiselect.observe(update_plots, names="value")

    # Initial display
    update_plots(None)

    controls = HBox([stock_multiselect, element_dropdown])
    display(VBox([controls, plot_container]))


def plot_interactive_mc_stock_comparison(mc_results_df, mfa_system_results=None):
    """Creates an interactive plot to compare Monte Carlo result distributions.

    This function overlays histograms for multiple selected stocks on the same
    axes, allowing for direct comparison of their frequency distributions. It uses
    the project's publication style and is fully interactive within a Jupyter
    widget environment.

    Parameters
    ----------
    mc_results_df : pd.DataFrame
        DataFrame with detailed MC results, with columns like 'S_X_ELEMENT'.
    mfa_system_results : odym.MFAsystem, optional
        MFA system object to map process IDs to descriptive names. Defaults to None.

    Notes
    -----
    The plot is interactive, allowing the user to select multiple stocks and
    an element to compare their distributions. Histograms are overlaid with
    a degree of transparency to facilitate comparison, and a color cycle is
    used to distinguish between different stock distributions.
    """
    if mc_results_df is None or mc_results_df.empty:
        print("No Monte Carlo results to plot.")
        return

    # Extract unique stock IDs and elements from DataFrame columns
    stock_ids = sorted(
        [
            col.rsplit("_", 1)[0]
            for col in mc_results_df.columns
            if col.startswith("S_") and not col.endswith("_timeseries")
        ]
    )
    stock_ids = sorted(list(set(stock_ids)))
    elements = sorted(
        list(
            set(
                col.rsplit("_", 1)[1]
                for col in mc_results_df.columns
                if col.startswith("S_") and not col.endswith("_timeseries")
            )
        )
    )

    if not stock_ids or not elements:
        print("No valid stock data found in Monte Carlo results.")
        return

    # Create a mapping from process ID to process name
    process_name_map = (
        {p.ID: p.Name for p in mfa_system_results.ProcessList}
        if mfa_system_results
        else {}
    )

    # Generate user-friendly display names for the selection widget
    stock_id_to_display = {
        stock_id: f"{process_name_map.get(int(stock_id.split('_')[1]), stock_id)} ({stock_id})"
        for stock_id in stock_ids
    }
    stock_display_names = [stock_id_to_display[sid] for sid in stock_ids]

    # --- Create Widgets ---
    element_dropdown = Dropdown(options=elements, description="Element:")
    stock_multiselect = SelectMultiple(
        options=stock_display_names,
        value=[stock_display_names[0]] if stock_display_names else [],
        description="Compare Stocks:",
        rows=min(10, len(stock_display_names)),
        layout={"width": "400px"},
    )
    fig_widget = go.FigureWidget()

    def update_plot(change):
        """Callback to update the plot when widget values change."""
        element = element_dropdown.value
        selected_display_names = stock_multiselect.value

        with fig_widget.batch_update():
            fig_widget.data = []
            fig_widget.layout.annotations = []

            if not selected_display_names:
                fig_widget.layout.title = "Please select at least one stock to compare."
                return

            # Define a color cycle for the histograms
            color_cycle = px.colors.qualitative.Plotly

            # Reverse mapping from display name back to stock_id
            display_to_stock_id = {v: k for k, v in stock_id_to_display.items()}

            for i, display_name in enumerate(selected_display_names):
                stock_id = display_to_stock_id.get(display_name)
                if not stock_id:
                    continue

                col_name = f"{stock_id}_{element}"
                if col_name not in mc_results_df.columns:
                    continue

                data_series = mc_results_df[col_name]
                _sc, _unit = get_mass_display()
                color = color_cycle[i % len(color_cycle)]

                # Add histogram trace with a fixed opacity for visibility
                fig_widget.add_trace(
                    go.Histogram(
                        x=data_series * _sc,
                        nbinsx=30,
                        name=display_name,
                        marker_color=color,
                        opacity=0.6,
                        histnorm="",
                    )
                )

            # Apply publication layout
            layout_config = get_publication_layout(
                size="large",
                show_grid=True,
                scientific_x=True,
                custom_title=f"Stock Uncertainty Comparison - {element.upper()}",
                x_title=y_label(element.upper()),
                y_title="Frequency (Count)",
            )
            apply_theme(layout_config)
            layout_config["xaxis"].pop("range", None)
            layout_config["xaxis"]["tickformat"] = ","  # comma thousands, no scientific
            # CRITICAL FIX: Set barmode to 'overlay' for comparison
            layout_config["barmode"] = "overlay"
            fig_widget.update_layout(**layout_config)

    # --- Link Widgets and Display ---
    element_dropdown.observe(update_plot, names="value")
    stock_multiselect.observe(update_plot, names="value")

    export_btn = Button(
        description="Export PNG/SVG",
        button_style="success",
        icon="download",
        layout=Layout(width="160px"),
    )

    def _do_export(b):
        try:
            name = f"mc_stock_comparison_{element_dropdown.value}".replace(" ", "_")
            paths = export_figure(
                fig_widget,
                name,
                formats=["png", "svg"],
                quality="publication",
                size="large",
            )
            print(f"✅ Exported: {', '.join(paths)}")
        except Exception as e:
            print(f"❌ Export failed: {e}")

    export_btn.on_click(_do_export)

    # Initial plot call
    update_plot(None)

    # Display layout
    controls = HBox([stock_multiselect, element_dropdown, export_btn])
    display(VBox([controls, fig_widget]))
