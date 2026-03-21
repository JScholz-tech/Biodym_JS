# -*- coding: utf-8 -*-
"""
Simplified Publication-Style Plotting Standards for BioDYM

This module defines essential styling standards for BioDYM plots,
focusing on simplicity and consistency.
"""


# =============================================================================
# ESSENTIAL COLOR PALETTES
# =============================================================================

# Primary BioDYM Color Palette
BIOYM_COLORS = {
    "primary": "#2E86AB",  # Deep blue - main elements
    "secondary": "#A23B72",  # Deep pink - secondary elements
    "accent": "#F18F01",  # Orange - highlights
    "neutral": "#6C757D",  # Gray - neutral elements
    "light": "#F8F9FA",  # Light gray - backgrounds
    "dark": "#000000",  # Black - text (print-optimized)
    "stock": "#6F42C1",  # Purple - stock elements
}

# Element-Specific Colors — Okabe-Ito colorblind-safe palette
ELEMENT_COLORS = {
    "material": "#0173B2",  # Blue - main material flow
    "wc": "#56B4E9",  # Sky Blue - water content
    "dm": "#E69F00",  # Orange - dry matter
    "cc": "#CC79A7",  # Pink - carbon content
}

# Process Type Colors (for BioDYM process logic)
PROCESS_COLORS = {
    "regular": "#2E86AB",  # Blue - standard MFA processes
    "splitter": "#A23B72",  # Pink - splitter processes
    "transformer": "#F18F01",  # Orange - transformer processes
    "dsm": "#28A745",  # Green - Dynamic Stock Model processes
    "fomp": "#C73E1D",  # Red - First-Order Mineralization Process
}

# Stock Colors — muted Okabe-Ito variants for stock visualization
STOCK_COLORS = {
    "default": "#6F42C1",  # Purple - default stock color
    "material": "#015A8C",  # Dark Blue - material stocks
    "wc": "#3D8AB8",  # Muted Sky Blue - water content stocks
    "dm": "#B87D00",  # Dark Orange - dry matter stocks
    "cc": "#A35E84",  # Muted Pink - carbon content stocks
}

# =============================================================================
# TYPOGRAPHY & LAYOUT
# =============================================================================

# Font Settings
FONT_FAMILY = "Arial, sans-serif"
FONT_SIZE = {"title": 24, "axis_title": 20, "axis_labels": 18, "legend": 16, "tick": 16}

# Standard Figure Sizes (in pixels)
FIGURE_SIZES = {
    "small": (800, 600),
    "medium": (1000, 750),
    "large": (1200, 900),
    "publication": (1000, 800),
    "sankey_wide": (
        2600,
        500,
    ),  # Very wide Sankey (horizontal elongated flow) - increased for better visibility
}

# Standard Margins
MARGINS = {
    "standard": dict(l=80, r=50, t=80, b=80),
    "publication": dict(l=100, r=50, t=100, b=100),
}

# Grid Settings
GRID_STYLE = {"color": "#E5E5E5", "width": 1, "dash": "dot"}

# Background Colors
BACKGROUND_COLORS = {"white": "#FFFFFF", "light_gray": "#FAFAFA"}

# =============================================================================
# EXPORT SETTINGS
# =============================================================================

# High-resolution export settings
EXPORT_SETTINGS = {
    "png": {"width": 1200, "height": 900, "scale": 3, "format": "png"},
    "pdf": {"width": 1200, "height": 900, "format": "pdf"},
    "svg": {"width": 1200, "height": 900, "format": "svg"},
    "print": {"width": 1200, "height": 900, "scale": 4, "format": "png"},
}

# =============================================================================
# ESSENTIAL FUNCTIONS
# =============================================================================


def get_publication_layout(
    size="publication",
    margin="publication",
    show_grid=True,
    background="white",
    scientific_y=False,
    scientific_x=False,
    zeroline=True,
    y_title=None,
    x_title=None,
    custom_title=None,
    width=None,
    height=None,
    x_range=None,
    y_range=None,
):
    """Generates a standardized layout configuration for publication-quality plots.

    This function provides a consistent visual style for Plotly figures,
    ensuring they meet publication standards. It configures aspects like
    figure size, margins, fonts, grid visibility, and axis properties.

    Parameters
    ----------
    size : str, optional
        A key from `FIGURE_SIZES` dict (e.g., 'small', 'medium', 'large',
        'publication') to set the overall dimensions of the figure.
        Defaults to 'publication'.
    margin : str, optional
        A key from `MARGINS` dict (e.g., 'standard', 'publication') to set
        the plot margins. Defaults to 'publication'.
    show_grid : bool, optional
        If True, displays grid lines on both x and y axes. Defaults to True.
    background : str, optional
        A key from `BACKGROUND_COLORS` dict (e.g., 'white', 'light_gray')
        to set the plot and paper background colors. Defaults to 'white'.
    scientific_y : bool, optional
        If True, formats the y-axis tick labels using scientific notation.
        Defaults to False.
    scientific_x : bool, optional
        If True, formats the x-axis tick labels using scientific notation.
        Defaults to False.
    zeroline : bool, optional
        If True, displays a zero line on the axes. Defaults to True.
    y_title : str, optional
        The title for the y-axis. Defaults to None.
    x_title : str, optional
        The title for the x-axis. Defaults to None.
    custom_title : str, optional
        A custom main title for the plot. If None, no main title is set.
        Defaults to None.
    width : int, optional
        Custom width for the figure. Overrides `size` parameter.
    height : int, optional
        Custom height for the figure. Overrides `size` parameter.
    x_range : list of two numbers or None, optional
        Explicit x-axis range, e.g. ``[2025, 2125]``. When None the axis
        auto-scales. Defaults to None.
    y_range : list of two numbers or None, optional
        Explicit y-axis range, e.g. ``[0, 6]``. When None the axis
        auto-scales (``rangemode="tozero"`` still applies). Defaults to None.

    Returns
    -------
    dict
        A dictionary representing the Plotly layout configuration.
    """
    layout = {
        "width": width if width else FIGURE_SIZES[size][0],
        "height": height if height else FIGURE_SIZES[size][1],
        "margin": MARGINS[margin],
        "font": {
            "family": FONT_FAMILY,
            "size": FONT_SIZE["axis_labels"],
            "color": BIOYM_COLORS["dark"],
        },
        "title": {
            "font": {
                "family": FONT_FAMILY,
                "size": FONT_SIZE["title"],
                "color": BIOYM_COLORS["dark"],
            },
            "x": 0.5,  # Center title
            "xanchor": "center",
        },
        "xaxis": {
            "title": {
                "text": x_title,
                "font": {
                    "family": FONT_FAMILY,
                    "size": FONT_SIZE["axis_title"],
                    "color": BIOYM_COLORS["dark"],
                },
            },
            "tickfont": {
                "family": FONT_FAMILY,
                "size": FONT_SIZE["tick"],
                "color": BIOYM_COLORS["dark"],
            },
            "gridcolor": GRID_STYLE["color"] if show_grid else "rgba(0,0,0,0)",
            "gridwidth": GRID_STYLE["width"],
            "griddash": GRID_STYLE["dash"],
            "linecolor": BIOYM_COLORS["neutral"],
            "linewidth": 1,
            "zeroline": zeroline,
            "zerolinecolor": BIOYM_COLORS["neutral"] if zeroline else "rgba(0,0,0,0)",
            "tickformat": ".2e" if scientific_x else None,
            **({"range": x_range} if x_range is not None else {}),
        },
        "yaxis": {
            "title": {
                "text": y_title,
                "font": {
                    "family": FONT_FAMILY,
                    "size": FONT_SIZE["axis_title"],
                    "color": BIOYM_COLORS["dark"],
                },
            },
            "tickfont": {
                "family": FONT_FAMILY,
                "size": FONT_SIZE["tick"],
                "color": BIOYM_COLORS["dark"],
            },
            "gridcolor": GRID_STYLE["color"] if show_grid else "rgba(0,0,0,0)",
            "gridwidth": GRID_STYLE["width"],
            "griddash": GRID_STYLE["dash"],
            "linecolor": BIOYM_COLORS["neutral"],
            "linewidth": 1,
            "zeroline": zeroline,
            "zerolinecolor": BIOYM_COLORS["neutral"] if zeroline else "rgba(0,0,0,0)",
            "tickformat": ".2e" if scientific_y else None,
            "rangemode": "tozero",
            **({"range": y_range} if y_range is not None else {}),
        },
        "plot_bgcolor": BACKGROUND_COLORS[background],
        "paper_bgcolor": BACKGROUND_COLORS[background],
        "legend": {
            "font": {
                "family": FONT_FAMILY,
                "size": FONT_SIZE["legend"],
                "color": BIOYM_COLORS["dark"],
            },
            "bgcolor": "rgba(255,255,255,0.8)",
            "bordercolor": BIOYM_COLORS["neutral"],
            "borderwidth": 1,
        },
    }
    if custom_title:
        layout["title"]["text"] = custom_title
    else:
        # If no title is provided, remove the title key to avoid conflicts
        del layout["title"]

    return layout


def get_element_color(element_name):
    """Retrieves the standardized color for a specific element.

    This function maps element names (e.g., 'material', 'wc', 'dm', 'cc')
    to predefined hexadecimal color codes, ensuring consistent coloring across
    all plots that visualize element-specific data.

    Parameters
    ----------
    element_name : str
        The name of the element (case-insensitive).

    Returns
    -------
    str
        The hexadecimal color code (e.g., '#0173B2') for the given element.
        If the element name is not found, it defaults to the primary BioDYM color.
    """
    return ELEMENT_COLORS.get(element_name.lower(), BIOYM_COLORS["primary"])


def get_process_color(process_type):
    """Retrieves the standardized color for a specific process type.

    This function maps process types (e.g., 'splitter', 'transformer', 'dsm',
    'fomp') to predefined hexadecimal color codes, ensuring consistent
    coloring across all plots that visualize process-specific data.

    Parameters
    ----------
    process_type : str
        The type of process (case-insensitive).

    Returns
    -------
    str
        The hexadecimal color code (e.g., '#A23B72') for the given process type.
        If the process type is not found, it defaults to the primary BioDYM color.
    """
    return PROCESS_COLORS.get(process_type.lower(), BIOYM_COLORS["primary"])


def get_stock_color(element_name=None):
    """Retrieves the standardized color for stock visualization.

    This function provides a consistent color for stocks, optionally allowing
    for element-specific stock colors if an element name is provided.

    Parameters
    ----------
    element_name : str, optional
        The name of the element for which to retrieve a stock color.
        If None, the default stock color is returned. Defaults to None.

    Returns
    -------
    str
        The hexadecimal color code for the stock.
    """
    if element_name:
        return STOCK_COLORS.get(element_name.lower(), STOCK_COLORS["default"])
    return STOCK_COLORS["default"]


def detect_biodym_process_type(
    process_id, process_logic_map=None, dsm_params=None, fomp_params=None
):
    """Automatically detects the BioDYM process type based on configuration.

    This function determines the classification of a given process (e.g.,
    'dsm', 'fomp', 'splitter', 'transformer', 'regular') by checking
    its presence in special model configurations (DSM, FOMP) or its defined
    logic type.

    Parameters
    ----------
    process_id : int
        The unique identifier of the process.
    process_logic_map : dict, optional
        A dictionary mapping process IDs to their logic types (e.g.,
        {'1': 'splitter'}). Defaults to None.
    dsm_params : dict, optional
        A dictionary containing the configuration parameters for all DSM
        processes. If a process_id is a key in this dict, it's a DSM process.
        Defaults to None.
    fomp_params : dict, optional
        A dictionary containing the configuration parameters for all FOMP
        processes. If a process_id is a key in this dict, it's a FOMP process.
        Defaults to None.

    Returns
    -------
    str
        A string indicating the detected process type ('regular', 'splitter',
        'transformer', 'dsm', 'fomp').
    """
    # Check for special models first (DSM and FOMP)
    if dsm_params and process_id in dsm_params:
        return "dsm"
    if fomp_params and process_id in fomp_params:
        return "fomp"

    # Check process logic from the system
    if process_logic_map and process_id in process_logic_map:
        logic_type = process_logic_map[process_id].lower()
        if logic_type in ["splitter", "transformer"]:
            return logic_type

    # Default to regular process
    return "regular"


def create_color_sequence(n_colors, palette="primary"):
    """Generates a sequence of colors for plotting multiple elements or processes.

    This function provides a flexible way to obtain a list of distinct colors
    from predefined palettes. If more colors are requested than available in
    the base palette, additional colors are procedurally generated to ensure
    sufficient variety.

    Parameters
    ----------
    n_colors : int
        The number of colors required in the sequence.
    palette : str, optional
        The name of the color palette to use ('primary', 'element',
        'process'). Defaults to 'primary'.

    Returns
    -------
    list of str
        A list of hexadecimal color codes.
    """
    if palette == "element":
        base_colors = list(ELEMENT_COLORS.values())
    elif palette == "process":
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
            hex_color = "#{:02x}{:02x}{:02x}".format(
                int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255)
            )
            additional_colors.append(hex_color)
        base_colors.extend(additional_colors)

    return base_colors[:n_colors]


def get_export_filename(plot_type, element=None, process=None, timestamp=None):
    """Generates a standardized filename for plot exports.

    This function creates a consistent, descriptive filename for an exported
    plot based on its type, optional element and process names. Uses fixed
    filenames that overwrite previous exports (no timestamp by default).

    Parameters
    ----------
    plot_type : str
        The type of plot (e.g., 'sankey', 'dynamics').
    element : str, optional
        The name of the element to include in the filename. Defaults to None.
    process : str, optional
        The name of the process to include in the filename. Defaults to None.
    timestamp : str, optional
        A custom timestamp (YYYYMMDD_HHMMSS). If provided, will be appended.
        If None, no timestamp is added. Defaults to None.

    Returns
    -------
    str
        The generated standardized filename (e.g.,
        'BioDYM_sankey_carbon_processA').
    """
    filename_parts = ["BioDYM", plot_type]

    if element:
        filename_parts.append(element)
    if process:
        filename_parts.append(process)

    # Only add timestamp if explicitly provided
    if timestamp is not None:
        filename_parts.append(timestamp)

    return "_".join(filename_parts)
