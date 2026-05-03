# -*- coding: utf-8 -*-
"""
Plotting Utilities Module.

This file contains helper functions for the plotting modules.
"""

from ipywidgets import Button, HBox
from IPython.display import display


def plot_enhanced_export_options(fig, filename_prefix="plot"):
    """Provides interactive buttons for exporting a Plotly figure to various formats.

    This function generates a set of `ipywidgets` buttons that allow users to
    export a given Plotly figure to PNG, PDF, SVG, or HTML formats. Uses fixed
    filenames (overwrites previous exports).

    Parameters
    ----------
    fig : go.Figure
        The Plotly figure object to be exported.
    filename_prefix : str, optional
        A prefix for the exported filenames. Defaults to "plot".
    """

    # Create export buttons
    export_png_btn = Button(description="Export PNG")
    export_pdf_btn = Button(description="Export PDF")
    export_svg_btn = Button(description="Export SVG")
    export_html_btn = Button(description="Export HTML")

    def export_png(b):
        filename = f"{filename_prefix}.png"
        fig.write_image(filename, width=1200, height=800, scale=2)
        print(f"✅ Exported: {filename}")

    def export_pdf(b):
        filename = f"{filename_prefix}.pdf"
        fig.write_image(filename, width=1200, height=800)
        print(f"✅ Exported: {filename}")

    def export_svg(b):
        filename = f"{filename_prefix}.svg"
        fig.write_image(filename, width=1200, height=800)
        print(f"✅ Exported: {filename}")

    def export_html(b):
        filename = f"{filename_prefix}.html"
        fig.write_html(filename, include_plotlyjs=True)
        print(f"✅ Exported: {filename}")

    export_png_btn.on_click(export_png)
    export_pdf_btn.on_click(export_pdf)
    export_svg_btn.on_click(export_svg)
    export_html_btn.on_click(export_html)

    # Display export controls
    export_controls = HBox(
        [export_png_btn, export_pdf_btn, export_svg_btn, export_html_btn]
    )
    display(export_controls)
