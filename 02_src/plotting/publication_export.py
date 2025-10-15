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
    """
    Enhanced export functionality for publication-quality figures.
    Provides unified, consistent export management across all BioDYM plots.
    """
    
    def __init__(self, export_dir="exports"):
        """
        Initialize the exporter.
        
        Args:
            export_dir (str): Directory to save exported figures
        """
        self.export_dir = export_dir
        self.ensure_export_dir()
        
    def ensure_export_dir(self):
        """Create export directory if it doesn't exist."""
        if not os.path.exists(self.export_dir):
            os.makedirs(self.export_dir)
    
    def get_standardized_filename(self, plot_type, parameters=None, timestamp=None):
        """
        Generate standardized filename for all plot types.
        
        Args:
            plot_type (str): Type of plot (e.g., 'scenario_comparison', 'dsm_analysis')
            parameters (dict): Plot parameters (element, process, etc.)
            timestamp (str): Custom timestamp (optional)
            
        Returns:
            str: Standardized filename
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
        """
        Get standardized export path for any plot type.
        
        Args:
            plot_type (str): Type of plot
            parameters (dict): Plot parameters
            timestamp (str): Custom timestamp (optional)
            use_subdir (bool): Whether to use timestamp subdirectory
            
        Returns:
            str: Full export path
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
        """
        Unified export function for all BioDYM plots.
        
        Args:
            fig: Plotly figure object
            plot_type (str): Type of plot (e.g., 'scenario_comparison', 'dsm_analysis')
            parameters (dict): Plot parameters for filename
            format (str): Export format ('png', 'pdf', 'svg')
            quality (str): Export quality ('publication', 'high', 'medium')
            use_subdir (bool): Whether to use timestamp subdirectory
            
        Returns:
            str: Export path if successful, None if failed
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
        """
        Export a single figure with publication-quality settings.
        
        Args:
            fig: Plotly figure object
            plot_type (str): Type of plot (sankey, dynamics, etc.)
            filename (str): Custom filename (optional)
            format (str): Export format ('png', 'pdf', 'svg', 'html')
            quality (str): Quality setting ('standard', 'publication', 'print')
            element (str): Element name for filename (optional)
            process (str): Process name for filename (optional)
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
        """
        Export multiple figures in batch.
        
        Args:
            figures_dict (dict): Dictionary of {name: figure} pairs
            base_filename (str): Base filename for all exports
            formats (list): List of formats to export
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
    """
    Create an enhanced export widget with publication-quality options.
    
    Args:
        fig: Plotly figure object
        plot_type (str): Type of plot
        element (str): Element name (optional)
        process (str): Process name (optional)
        
    Returns:
        ipywidgets.VBox: Export widget
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
    """
    Apply publication styling to a plotly figure.
    
    Args:
        fig: Plotly figure object
        title (str): Figure title (optional)
        size (str): Figure size key
        show_grid (bool): Whether to show grid
        
    Returns:
        Plotly figure with applied styling
    """
    layout = get_publication_layout(size=size, show_grid=show_grid)
    
    if title:
        layout['title']['text'] = title
    
    fig.update_layout(layout)
    fig._publication_layout_applied = True
    
    return fig

def create_figure_summary(figures_dict):
    """
    Create a summary of all figures for batch export.
    
    Args:
        figures_dict (dict): Dictionary of {name: figure} pairs
        
    Returns:
        ipywidgets.VBox: Summary widget
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
    """
    Quick export function for single figures.
    
    Args:
        fig: Plotly figure object
        plot_type (str): Type of plot
        element (str): Element name (optional)
        process (str): Process name (optional)
        format (str): Export format
        
    Returns:
        str: Path to exported file
    """
    exporter = PublicationExporter()
    return exporter.export_figure(fig, plot_type, format=format, 
                                 element=element, process=process)
