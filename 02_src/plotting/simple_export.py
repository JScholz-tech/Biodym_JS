# -*- coding: utf-8 -*-
"""
Simple Export Functions for BioDYM

Simple, clean export functionality that just works.
"""

import os
from datetime import datetime

def simple_export(fig, plot_name="plot", element=None, process=None):
    """
    Simple PNG export function that just works.
    
    Args:
        fig: Plotly figure object
        plot_name (str): Name of the plot (e.g., "sankey", "dynamics")
        element (str): Element name (optional)
        process (str): Process name (optional)
        
    Returns:
        str: Path to exported file, or None if failed
    """
    try:
        # Create exports directory if it doesn't exist
        export_dir = "exports"
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)
        
        # Generate simple filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        filename_parts = [plot_name]
        if element:
            filename_parts.append(element)
        if process:
            filename_parts.append(process)
        filename_parts.append(timestamp)
        
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
    """Export Sankey diagram."""
    return simple_export(fig, "sankey", element=element)

def export_dynamics(fig, element=None, process=None):
    """Export dynamics plot."""
    return simple_export(fig, "dynamics", element=element, process=process)

def export_monte_carlo(fig, element=None, process=None):
    """Export Monte Carlo plot."""
    return simple_export(fig, "monte_carlo", element=element, process=process)

def export_scenario(fig, element=None):
    """Export scenario comparison plot."""
    return simple_export(fig, "scenario", element=element)

def export_validation(fig, element=None):
    """Export validation plot."""
    return simple_export(fig, "validation", element=element)
