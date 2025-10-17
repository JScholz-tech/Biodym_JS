# -*- coding: utf-8 -*-
"""
Publication-Quality Export Utilities for BioDYM

This module provides enhanced export functionality with publication-ready
styling, batch export capabilities, and print-optimized formats.
"""

import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ipywidgets import Button, HBox, VBox, Dropdown, Checkbox, Text, HTML
from IPython.display import display, clear_output
from datetime import datetime
import pandas as pd
from .publication_style import (
    get_publication_layout, 
    get_export_filename, 
    EXPORT_SETTINGS,
    FIGURE_SIZES,
    PRINT_SIZES
)

class PublicationExporter:
    """Manages the export of publication-quality figures.

    This class provides a centralized and consistent interface for exporting
    Plotly figures to various formats (PNG, PDF, SVG, HTML) with standardized
    filenames, directory structures, and quality settings. It is designed to
    unify export functionality across all plotting modules in the BioDYM tool.

    Parameters
    ----------
    export_dir : str, optional
        The root directory where all exported figures will be saved.
        Defaults to "exports".
    """
    
    def __init__(self, export_dir="exports"):
        """Initializes the PublicationExporter.

        Parameters
        ----------
        export_dir : str, optional
            The root directory to save exported figures. Defaults to "exports".
        """
        self.export_dir = export_dir
        self.ensure_export_dir()
        
    def ensure_export_dir(self):
        """Ensures the export directory exists.

        This method checks if the directory specified in `self.export_dir`
        exists, and creates it if it does not.
        """
        if not os.path.exists(self.export_dir):
            os.makedirs(self.export_dir)
    
    def get_standardized_filename(self, plot_type, parameters=None, timestamp=None):
        """Generates a standardized filename for a plot.

        This method creates a consistent, descriptive filename for an exported
        plot based on its type and the parameters used to generate it.

        Parameters
        ----------
        plot_type : str
            The type of plot (e.g., 'scenario_comparison', 'dsm_analysis').
        parameters : dict, optional
            A dictionary of plot parameters (e.g., element, process) to be
            included in the filename. Defaults to None.
        timestamp : str, optional
            A custom timestamp (YYYYMMDD_HHMMSS). If None, the current time is
            used. Defaults to None.

        Returns
        -------
        str
            The generated standardized filename (e.g.,
            'dsm_analysis_20251016_143000_carbon.png').
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Base filename with plot type and timestamp
        filename_parts = [plot_type, timestamp]
        
        # Add parameters in consistent order
        if parameters:
            # Standard parameter order: element, process, metric, chart_type
            for param_key in ['element', 'process', 'metric', 'chart_type']:
                if param_key in parameters and parameters[param_key]:
                    param_value = str(parameters[param_key]).replace(" ", "_").replace("(", "").replace(")", "").replace(":", "")
                    filename_parts.append(param_value)
        
        return "_".join(filename_parts) + ".png"
    
    def get_export_path(self, plot_type, parameters=None, timestamp=None, use_subdir=True):
        """Gets the standardized full export path for a plot.

        This method constructs the full file path for an exported plot,
        including the root export directory, an optional subdirectory for the
        plot type, and a standardized filename.

        Parameters
        ----------
        plot_type : str
            The type of plot (e.g., 'scenario_comparison').
        parameters : dict, optional
            Plot parameters for the filename. Defaults to None.
        timestamp : str, optional
            A custom timestamp (YYYYMMDD_HHMMSS). If None, the current time is
            used. Defaults to None.
        use_subdir : bool, optional
            If True, creates a timestamped subdirectory within the plot type
            directory for better organization. Defaults to True.

        Returns
        -------
        str
            The full, absolute path for the exported file.
        """
        filename = self.get_standardized_filename(plot_type, parameters, timestamp)
        
        if use_subdir:
            # Create timestamp subdirectory for better organization
            if timestamp is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path = os.path.join(self.export_dir, plot_type, timestamp, filename)
        else:
            # Direct to category folder
            export_path = os.path.join(self.export_dir, plot_type, filename)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(export_path), exist_ok=True)
        
        return export_path
    
    def export_plot(self, fig, plot_type, parameters=None, format='png', 
                   quality='publication', use_subdir=True):
        """Exports a Plotly figure with standardized settings.

        This is a unified export function that saves a given Plotly figure
        with a standardized filename and path, using predefined quality
        settings for consistent output.

        Parameters
        ----------
        fig : go.Figure
            The Plotly figure object to be exported.
        plot_type : str
            The type of plot (e.g., 'scenario_comparison', 'dsm_analysis').
        parameters : dict, optional
            Plot parameters for the filename. Defaults to None.
        format : str, optional
            The export format ('png', 'pdf', 'svg'). Defaults to 'png'.
        quality : str, optional
            The export quality setting ('publication', 'high', 'medium').
            Determines resolution and scale. Defaults to 'publication'.
        use_subdir : bool, optional
            If True, saves the plot in a timestamped subdirectory.
            Defaults to True.

        Returns
        -------
        str or None
            The full path to the exported file if successful, otherwise None.
        """
        try:
            # Get standardized export path
            export_path = self.get_export_path(plot_type, parameters, use_subdir=use_subdir)
            
            # Set export settings based on quality
            if quality == 'publication':
                width, height = 1400, 600
                scale = 2
            elif quality == 'high':
                width, height = 1200, 500
                scale = 1.5
            else:  # medium
                width, height = 1000, 400
                scale = 1
            
            # Export the figure
            fig.write_image(export_path, width=width, height=height, scale=scale)
            
            print(f"✅ Plot exported successfully!")
            print(f"📁 Path: {export_path}")
            print(f"📊 Quality: {quality} ({width}x{height}, scale={scale})")
            
            return export_path
            
        except Exception as e:
            print(f"❌ Export failed: {e}")
            print("💡 Ensure 'kaleido' is available (uv sync)")
            return None
    
    def export_figure(self, fig, plot_type, filename=None, format='png', 
                     quality='publication', element=None, process=None):
        """Exports a single figure with publication-quality settings.

        This method applies a publication-ready layout to a figure (if not
        already applied) and saves it to a specified format and quality.

        Parameters
        ----------
        fig : go.Figure
            The Plotly figure object to export.
        plot_type : str
            The type of plot (e.g., 'sankey', 'dynamics').
        filename : str, optional
            A custom filename (without extension). If None, a standardized
            filename is generated. Defaults to None.
        format : str, optional
            The export format ('png', 'pdf', 'svg', 'html'). Defaults to 'png'.
        quality : str, optional
            The quality setting ('standard', 'publication', 'print').
            Defaults to 'publication'.
        element : str, optional
            The element name, used for generating a standardized filename if
            `filename` is not provided. Defaults to None.
        process : str, optional
            The process name, used for generating a standardized filename if
            `filename` is not provided. Defaults to None.

        Returns
        -------
        str or None
            The full path to the exported file if successful, otherwise None.
        """
        if filename is None:
            filename = get_export_filename(plot_type, element, process)
        
        # Apply publication layout if not already applied
        if not hasattr(fig, '_publication_layout_applied'):
            fig.update_layout(get_publication_layout())
            fig._publication_layout_applied = True
        
        # Get export settings
        if quality == 'print':
            settings = EXPORT_SETTINGS['print']
        elif quality == 'publication':
            settings = EXPORT_SETTINGS['png'].copy()
            settings['scale'] = 3  # 300 DPI
        else:
            settings = EXPORT_SETTINGS[format]
        
        # Export based on format
        filepath = os.path.join(self.export_dir, f"{filename}.{format}")
        
        try:
            if format == 'png':
                fig.write_image(filepath, 
                              width=settings['width'], 
                              height=settings['height'],
                              scale=settings.get('scale', 2))
            elif format == 'pdf':
                fig.write_image(filepath,
                              width=settings['width'],
                              height=settings['height'])
            elif format == 'svg':
                fig.write_image(filepath,
                              width=settings['width'],
                              height=settings['height'])
            elif format == 'html':
                fig.write_html(filepath, include_plotlyjs=True)
            
            print(f"✅ Exported: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"❌ Export failed: {e}")
            return None
    
    def batch_export(self, figures_dict, base_filename=None, formats=['png', 'pdf']):
        """Exports multiple figures in a batch operation.

        This method iterates through a dictionary of named figures and exports
        each one to the specified formats, using a common base filename.

        Parameters
        ----------
        figures_dict : dict
            A dictionary where keys are descriptive names for the figures and
            values are the Plotly figure objects (e.g., {'dsm_plot': fig1}).
        base_filename : str, optional
            A base filename to be used for all exported files. If None, a
            timestamped default is generated. Defaults to None.
        formats : list of str, optional
            A list of formats to export each figure to. Defaults to ['png', 'pdf'].

        Returns
        -------
        list of str
            A list of file paths for all successfully exported files.
        """
        if base_filename is None:
            base_filename = f"BioDYM_BatchExport_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        exported_files = []
        
        for name, fig in figures_dict.items():
            for format_type in formats:
                filename = f"{base_filename}_{name}"
                filepath = self.export_figure(fig, name, filename, format_type)
                if filepath:
                    exported_files.append(filepath)
        
        print(f"🎉 Batch export completed: {len(exported_files)} files exported")
        return exported_files

def create_publication_export_widget(fig, plot_type, element=None, process=None):
    """Creates an enhanced export widget with publication-quality options.

    This function generates an `ipywidgets`-based user interface that allows
    for interactive exporting of a given Plotly figure. The widget provides
    options for format, quality, and filename, as well as a button for
    batch exporting to multiple formats at once.

    Parameters
    ----------
    fig : go.Figure
        The Plotly figure object to be exported.
    plot_type : str
        The type of plot (e.g., 'sankey', 'dynamics'), used for generating
        a default filename.
    element : str, optional
        The element name, used for the default filename. Defaults to None.
    process : str, optional
        The process name, used for the default filename. Defaults to None.

    Returns
    -------
    ipywidgets.VBox
        A VBox widget containing the complete export user interface.
    """
    exporter = PublicationExporter()
    
    # Create widgets
    format_dropdown = Dropdown(
        options=['png', 'pdf', 'svg', 'html'],
        value='png',
        description='Format:'
    )
    
    quality_dropdown = Dropdown(
        options=['standard', 'publication', 'print'],
        value='publication',
        description='Quality:'
    )
    
    filename_text = Text(
        value=get_export_filename(plot_type, element, process),
        description='Filename:',
        layout={'width': '300px'}
    )
    
    export_button = Button(
        description="Export Figure",
        button_style='success',
        icon='download'
    )
    
    export_all_button = Button(
        description="Export All Formats",
        button_style='info',
        icon='download'
    )
    
    status_html = HTML(value="<i>Ready to export</i>")
    
    def update_status(message, success=True):
        color = "green" if success else "red"
        status_html.value = f"<span style='color: {color}'>{message}</span>"
    
    def on_export_click(b):
        clear_output(wait=True)
        display(create_publication_export_widget(fig, plot_type, element, process))
        
        format_type = format_dropdown.value
        quality = quality_dropdown.value
        filename = filename_text.value
        
        filepath = exporter.export_figure(
            fig, plot_type, filename, format_type, quality, element, process
        )
        
        if filepath:
            update_status(f"✅ Exported: {os.path.basename(filepath)}")
        else:
            update_status("❌ Export failed", False)
    
    def on_export_all_click(b):
        clear_output(wait=True)
        display(create_publication_export_widget(fig, plot_type, element, process))
        
        filename = filename_text.value
        formats = ['png', 'pdf', 'svg']
        
        exported_files = []
        for format_type in formats:
            filepath = exporter.export_figure(
                fig, plot_type, filename, format_type, 'publication', element, process
            )
            if filepath:
                exported_files.append(filepath)
        
        if exported_files:
            update_status(f"✅ Exported {len(exported_files)} files")
        else:
            update_status("❌ Export failed", False)
    
    export_button.on_click(on_export_click)
    export_all_button.on_click(on_export_all_click)
    
    # Layout
    controls_row1 = HBox([format_dropdown, quality_dropdown])
    controls_row2 = HBox([export_button, export_all_button])
    
    widget = VBox([
        HTML("<h4>📊 Publication Export</h4>"),
        filename_text,
        controls_row1,
        controls_row2,
        status_html
    ])
    
    return widget

def apply_publication_style(fig, title=None, size='publication', show_grid=True):
    """Applies a publication-ready style to a Plotly figure.

    This function updates the layout of a given Plotly figure to match the
    project's defined publication standards, including font sizes, colors,
    and grid visibility.

    Parameters
    ----------
    fig : go.Figure
        The Plotly figure object to be styled.
    title : str, optional
        A custom title for the figure. If None, the existing title is used.
        Defaults to None.
    size : str, optional
        The figure size key ('publication', 'large', 'medium', 'small').
        Determines the overall dimensions and font sizes. Defaults to 'publication'.
    show_grid : bool, optional
        If True, displays the grid lines on the plot. Defaults to True.

    Returns
    -------
    go.Figure
        The Plotly figure with the publication style applied.
    """
    layout = get_publication_layout(size=size, show_grid=show_grid)
    
    if title:
        layout['title']['text'] = title
    
    fig.update_layout(layout)
    fig._publication_layout_applied = True
    
    return fig

def create_figure_summary(figures_dict):
    """Creates a summary widget for batch exporting multiple figures.

    This function generates an `ipywidgets`-based UI that displays a summary
    of all figures intended for batch export and provides a single button to
    export all of them at once.

    Parameters
    ----------
    figures_dict : dict
        A dictionary where keys are descriptive names for the figures and
        values are the Plotly figure objects (e.g., {'dsm_plot': fig1}).

    Returns
    -------
    ipywidgets.VBox
        A VBox widget containing the summary title and the export button.
    """
    exporter = PublicationExporter()
    
    summary_html = HTML(
        value=f"<h4>📋 Figure Summary ({len(figures_dict)} figures)</h4>"
    )
    
    export_all_button = Button(
        description=f"Export All {len(figures_dict)} Figures",
        button_style='success',
        icon='download'
    )
    
    def on_export_all_click(b):
        base_filename = f"BioDYM_CompleteAnalysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        exported_files = exporter.batch_export(figures_dict, base_filename)
        
        if exported_files:
            print(f"🎉 Complete analysis exported: {len(exported_files)} files")
            print("📁 Files saved to: exports/")
        else:
            print("❌ Export failed")
    
    export_all_button.on_click(on_export_all_click)
    
    return VBox([summary_html, export_all_button])

# Convenience function for quick export
def quick_export(fig, plot_type, element=None, process=None, format='png'):
    """Provides a simple, one-line function for exporting a single figure.

    This is a convenience wrapper around the `PublicationExporter.export_figure`
    method for quick, straightforward exports with default settings.

    Parameters
    ----------
    fig : go.Figure
        The Plotly figure object to export.
    plot_type : str
        The type of plot, used for generating a standardized filename.
    element : str, optional
        The element name for the filename. Defaults to None.
    process : str, optional
        The process name for the filename. Defaults to None.
    format : str, optional
        The export format. Defaults to 'png'.

    Returns
    -------
    str or None
        The full path to the exported file if successful, otherwise None.
    """
    exporter = PublicationExporter()
    return exporter.export_figure(fig, plot_type, format=format, 
                                 element=element, process=process)
