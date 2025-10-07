# -*- coding: utf-8 -*-
"""
Simplified Publication-Style Plotting Standards for BioDYM

This module defines essential styling standards for BioDYM plots,
focusing on simplicity and consistency.
"""

import plotly.graph_objects as go
from datetime import datetime

# =============================================================================
# ESSENTIAL COLOR PALETTES
# =============================================================================

# Primary BioDYM Color Palette
BIOYM_COLORS = {
    'primary': '#2E86AB',      # Deep blue - main elements
    'secondary': '#A23B72',    # Deep pink - secondary elements  
    'accent': '#F18F01',       # Orange - highlights
    'neutral': '#6C757D',      # Gray - neutral elements
    'light': '#F8F9FA',        # Light gray - backgrounds
    'dark': '#212529',         # Dark gray - text
}

# Element-Specific Colors (for BioDYM multi-element analysis)
ELEMENT_COLORS = {
    'material': '#00C851',     # Bright Green - main material flow
    'wc': '#007BFF',           # Bright Blue - water content
    'dm': '#FF8C00',           # Bright Orange - dry matter
    'cc': '#FF4444',           # Bright Red - carbon content
}

# Process Type Colors (for BioDYM process logic)
PROCESS_COLORS = {
    'regular': '#2E86AB',       # Blue - standard MFA processes
    'splitter': '#A23B72',      # Pink - splitter processes
    'transformer': '#F18F01',   # Orange - transformer processes
    'dsm': '#28A745',           # Green - Dynamic Stock Model processes
    'fomp': '#C73E1D',          # Red - First-Order Mineralization Process
}

# =============================================================================
# TYPOGRAPHY & LAYOUT
# =============================================================================

# Font Settings
FONT_FAMILY = 'Arial, sans-serif'
FONT_SIZE = {
    'title': 16,
    'axis_title': 12,
    'axis_labels': 10,
    'legend': 10,
    'tick': 9
}

# Standard Figure Sizes (in pixels)
FIGURE_SIZES = {
    'small': (800, 600),
    'medium': (1000, 750),
    'large': (1200, 900),
    'publication': (1000, 800)
}

# Standard Margins
MARGINS = {
    'standard': dict(l=80, r=50, t=80, b=80),
    'publication': dict(l=100, r=50, t=100, b=100)
}

# Grid Settings
GRID_STYLE = {
    'color': '#E5E5E5',
    'width': 1,
    'dash': 'dot'
}

# Background Colors
BACKGROUND_COLORS = {
    'white': '#FFFFFF',
    'light_gray': '#FAFAFA'
}

# =============================================================================
# ESSENTIAL FUNCTIONS
# =============================================================================

def get_publication_layout(
    size='publication', 
    margin='publication', 
    show_grid=True, 
    background='white',
    scientific_y=False,
    scientific_x=False,
    zeroline=True,
    y_title=None,
    x_title=None,
    custom_title=None
):
    """
    Get a standardized layout configuration for publication-quality plots.
    
    Args:
        size (str): Figure size key from FIGURE_SIZES
        margin (str): Margin key from MARGINS
        show_grid (bool): Whether to show grid
        background (str): Background color key from BACKGROUND_COLORS
        scientific_y (bool): Whether to use scientific notation for y-axis
        scientific_x (bool): Whether to use scientific notation for x-axis
        zeroline (bool): Whether to show the zeroline
        y_title (str): Title for the y-axis
        x_title (str): Title for the x-axis
        custom_title (str): Title for the plot
        
    Returns:
        dict: Layout configuration for plotly figures
    """
    layout = {
        'width': FIGURE_SIZES[size][0],
        'height': FIGURE_SIZES[size][1],
        'margin': MARGINS[margin],
        'font': {
            'family': FONT_FAMILY,
            'size': FONT_SIZE['axis_labels'],
            'color': BIOYM_COLORS['dark']
        },
        'title': {
            'font': {
                'family': FONT_FAMILY,
                'size': FONT_SIZE['title'],
                'color': BIOYM_COLORS['dark']
            },
            'x': 0.5,  # Center title
            'xanchor': 'center'
        },
        'xaxis': {
            'title': {
                'text': x_title,
                'font': {
                    'family': FONT_FAMILY,
                    'size': FONT_SIZE['axis_title'],
                    'color': BIOYM_COLORS['dark']
                }
            },
            'tickfont': {
                'family': FONT_FAMILY,
                'size': FONT_SIZE['tick'],
                'color': BIOYM_COLORS['dark']
            },
            'gridcolor': GRID_STYLE['color'] if show_grid else 'rgba(0,0,0,0)',
            'gridwidth': GRID_STYLE['width'],
            'griddash': GRID_STYLE['dash'],
            'linecolor': BIOYM_COLORS['neutral'],
            'linewidth': 1,
            'zeroline': zeroline,
            'zerolinecolor': BIOYM_COLORS['neutral'] if zeroline else 'rgba(0,0,0,0)',
            'tickformat': ".2e" if scientific_x else None
        },
        'yaxis': {
            'title': {
                'text': y_title,
                'font': {
                    'family': FONT_FAMILY,
                    'size': FONT_SIZE['axis_title'],
                    'color': BIOYM_COLORS['dark']
                }
            },
            'tickfont': {
                'family': FONT_FAMILY,
                'size': FONT_SIZE['tick'],
                'color': BIOYM_COLORS['dark']
            },
            'gridcolor': GRID_STYLE['color'] if show_grid else 'rgba(0,0,0,0)',
            'gridwidth': GRID_STYLE['width'],
            'griddash': GRID_STYLE['dash'],
            'linecolor': BIOYM_COLORS['neutral'],
            'linewidth': 1,
            'zeroline': zeroline,
            'zerolinecolor': BIOYM_COLORS['neutral'] if zeroline else 'rgba(0,0,0,0)',
            'tickformat': ".2e" if scientific_y else None,
            'rangemode': 'tozero'
        },
        'plot_bgcolor': BACKGROUND_COLORS[background],
        'paper_bgcolor': BACKGROUND_COLORS[background],
        'legend': {
            'font': {
                'family': FONT_FAMILY,
                'size': FONT_SIZE['legend'],
                'color': BIOYM_COLORS['dark']
            },
            'bgcolor': 'rgba(255,255,255,0.8)',
            'bordercolor': BIOYM_COLORS['neutral'],
            'borderwidth': 1
        }
    }
    if custom_title:
        layout['title']['text'] = custom_title
    
    return layout

def get_element_color(element_name):
    """
    Get the standardized color for a specific element.
    
    Args:
        element_name (str): Name of the element
        
    Returns:
        str: Hex color code
    """
    return ELEMENT_COLORS.get(element_name.lower(), BIOYM_COLORS['primary'])

def get_process_color(process_type):
    """
    Get the standardized color for a specific process type.
    
    Args:
        process_type (str): Type of process (splitter, transformer, etc.)
        
    Returns:
        str: Hex color code
    """
    return PROCESS_COLORS.get(process_type.lower(), BIOYM_COLORS['primary'])

def detect_biodym_process_type(process_id, process_logic_map=None, dsm_params=None, fomp_params=None):
    """
    Automatically detect the BioDYM process type based on system configuration.
    
    Args:
        process_id (int): Process ID
        process_logic_map (dict): Map of process IDs to logic types
        dsm_params (dict): DSM parameters configuration
        fomp_params (dict): FOMP parameters configuration
        
    Returns:
        str: Process type ('regular', 'splitter', 'transformer', 'dsm', 'fomp')
    """
    # Check for special models first (DSM and FOMP)
    if dsm_params and process_id in dsm_params:
        return 'dsm'
    if fomp_params and process_id in fomp_params:
        return 'fomp'
    
    # Check process logic from the system
    if process_logic_map and process_id in process_logic_map:
        logic_type = process_logic_map[process_id].lower()
        if logic_type in ['splitter', 'transformer']:
            return logic_type
    
    # Default to regular process
    return 'regular'

def create_color_sequence(n_colors, palette='primary'):
    """
    Create a sequence of colors for multiple elements/processes.
    
    Args:
        n_colors (int): Number of colors needed
        palette (str): Color palette to use ('primary', 'element', 'process')
        
    Returns:
        list: List of hex color codes
    """
    if palette == 'element':
        base_colors = list(ELEMENT_COLORS.values())
    elif palette == 'process':
        base_colors = list(PROCESS_COLORS.values())
    else:
        base_colors = list(BIOYM_COLORS.values())
    
    # If we need more colors than available, generate additional ones
    if n_colors > len(base_colors):
        import colorsys
        additional_colors = []
        for i in range(n_colors - len(base_colors)):
            hue = i / (n_colors - len(base_colors))
            rgb = colorsys.hsv_to_rgb(hue, 0.7, 0.8)
            hex_color = '#{:02x}{:02x}{:02x}'.format(
                int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255)
            )
            additional_colors.append(hex_color)
        base_colors.extend(additional_colors)
    
    return base_colors[:n_colors]

def get_export_filename(plot_type, element=None, process=None, timestamp=None):
    """
    Generate standardized filename for plot exports.
    
    Args:
        plot_type (str): Type of plot (sankey, dynamics, etc.)
        element (str): Element name (optional)
        process (str): Process name (optional)
        timestamp (str): Custom timestamp (optional)
        
    Returns:
        str: Standardized filename
    """
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    filename_parts = ['BioDYM', plot_type]
    
    if element:
        filename_parts.append(element)
    if process:
        filename_parts.append(process)
    
    filename_parts.append(timestamp)
    
    return '_'.join(filename_parts)
