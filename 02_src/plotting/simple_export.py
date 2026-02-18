# -*- coding: utf-8 -*-
"""
Simple Export Functions for BioDYM

Simple, clean export functionality that just works.
"""

import os


def simple_export(fig, plot_name="plot", element=None, process=None):
    """Exports a Plotly figure to a PNG file with a simple, standardized filename.

    This function provides a straightforward way to save any Plotly figure
    as a PNG image. It automatically creates an 'exports' directory if it
    doesn't exist and generates a descriptive filename based on the plot type,
    optional element, and process. Uses fixed filenames that overwrite previous
    exports.

    Parameters
    ----------
    fig : go.Figure
        The Plotly figure object to be exported.
    plot_name : str, optional
        A descriptive name for the plot (e.g., "sankey", "dynamics").
        Defaults to "plot".
    element : str, optional
        The name of the element relevant to the plot, to be included in the
        filename. Defaults to None.
    process : str, optional
        The name of the process relevant to the plot, to be included in the
        filename. Defaults to None.

    Returns
    -------
    str or None
        The full path to the exported file if successful, otherwise None.

    Notes
    -----
    The function exports the image with a default width of 1200 pixels,
    height of 800 pixels, and a scale factor of 2 for good quality. It also
    provides a hint to install 'kaleido' if the export fails.
    """
    try:
        # Create exports directory if it doesn't exist
        export_dir = "exports"
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)

        # Generate simple filename (fixed - no timestamp, overwrites previous)
        filename_parts = [plot_name]
        if element:
            filename_parts.append(element)
        if process:
            filename_parts.append(process)

        filename = "_".join(filename_parts) + ".png"
        filepath = os.path.join(export_dir, filename)

        # Export as PNG with good quality
        fig.write_image(filepath, width=1200, height=800, scale=2)

        print(f"✅ Exported: {filename}")
        return filepath

    except Exception as e:
        print(f"❌ Export failed: {e}")
        print("💡 Make sure kaleido is installed: pip install kaleido")
        return None


def export_sankey(fig, element=None):
    """Exports a Sankey diagram using the simple export function.

    This is a convenience function that wraps `simple_export` specifically
    for Sankey diagrams, setting the `plot_name` to "sankey".

    Parameters
    ----------
    fig : go.Figure
        The Plotly figure object representing the Sankey diagram.
    element : str, optional
        The name of the element relevant to the plot, to be included in the
        filename. Defaults to None.

    Returns
    -------
    str or None
        The full path to the exported file if successful, otherwise None.
    """
    return simple_export(fig, "sankey", element=element)


def export_dynamics(fig, element=None, process=None):
    """Exports a dynamics plot using the simple export function.

    This is a convenience function that wraps `simple_export` specifically
    for dynamics plots, setting the `plot_name` to "dynamics".

    Parameters
    ----------
    fig : go.Figure
        The Plotly figure object representing the dynamics plot.
    element : str, optional
        The name of the element relevant to the plot, to be included in the
        filename. Defaults to None.
    process : str, optional
        The name of the process relevant to the plot, to be included in the
        filename. Defaults to None.

    Returns
    -------
    str or None
        The full path to the exported file if successful, otherwise None.
    """
    return simple_export(fig, "dynamics", element=element, process=process)


def export_monte_carlo(fig, element=None, process=None):
    """Exports a Monte Carlo plot using the simple export function.

    This is a convenience function that wraps `simple_export` specifically
    for Monte Carlo plots, setting the `plot_name` to "monte_carlo".

    Parameters
    ----------
    fig : go.Figure
        The Plotly figure object representing the Monte Carlo plot.
    element : str, optional
        The name of the element relevant to the plot, to be included in the
        filename. Defaults to None.
    process : str, optional
        The name of the process relevant to the plot, to be included in the
        filename. Defaults to None.

    Returns
    -------
    str or None
        The full path to the exported file if successful, otherwise None.
    """
    return simple_export(fig, "monte_carlo", element=element, process=process)


def export_scenario(fig, element=None):
    """Exports a scenario comparison plot using the simple export function.

    This is a convenience function that wraps `simple_export` specifically
    for scenario comparison plots, setting the `plot_name` to "scenario".

    Parameters
    ----------
    fig : go.Figure
        The Plotly figure object representing the scenario comparison plot.
    element : str, optional
        The name of the element relevant to the plot, to be included in the
        filename. Defaults to None.

    Returns
    -------
    str or None
        The full path to the exported file if successful, otherwise None.
    """
    return simple_export(fig, "scenario", element=element)


def export_validation(fig, element=None):
    """Exports a validation plot using the simple export function.

    This is a convenience function that wraps `simple_export` specifically
    for validation plots, setting the `plot_name` to "validation".

    Parameters
    ----------
    fig : go.Figure
        The Plotly figure object representing the validation plot.
    element : str, optional
        The name of the element relevant to the plot, to be included in the
        filename. Defaults to None.

    Returns
    -------
    str or None
        The full path to the exported file if successful, otherwise None.
    """
    return simple_export(fig, "validation", element=element)
