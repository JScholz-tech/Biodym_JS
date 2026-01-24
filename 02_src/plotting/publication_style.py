# -*- coding: utf-8 -*-
"""
Publication-Style Plotting Standards for BioDYM

This module defines comprehensive styling standards for all BioDYM plots,
ensuring consistency, professional appearance, and print-readiness.
"""

import matplotlib.pyplot as plt
import matplotlib as mpl
from datetime import datetime

# =============================================================================
# COLOR PALETTES
# =============================================================================

# Primary BioDYM Color Palette (Scientific/Professional)
BIOYM_COLORS = {
    "primary": "#2E86AB",  # Deep blue - main elements
    "secondary": "#A23B72",  # Deep pink - secondary elements
    "accent": "#F18F01",  # Orange - highlights
    "success": "#C73E1D",  # Red - important flows
    "neutral": "#6C757D",  # Gray - neutral elements
    "light": "#F8F9FA",  # Light gray - backgrounds
    "dark": "#212529",  # Dark gray - text
}

# Element-Specific Colors (for BioDYM multi-element analysis)
ELEMENT_COLORS = {
    "material": "#00C851",  # Bright Green - main material flow (organic/natural)
    "wc": "#007BFF",  # Bright Blue - water content (water = blue)
    "dm": "#FF8C00",  # Bright Orange - dry matter (earth/soil)
    "cc": "#FF4444",  # Bright Red - carbon content (carbon/energy)
    # Additional elements for future expansion
    "carbon": "#FF4444",  # Red for carbon (same as CC)
    "nitrogen": "#FFC107",  # Yellow for nitrogen
    "phosphorus": "#9C27B0",  # Purple for phosphorus
    "water": "#007BFF",  # Blue for water (same as WC)
    "energy": "#FF8C00",  # Orange for energy (same as DM)
}

# Process Type Colors (for BioDYM process logic)
PROCESS_COLORS = {
    "regular": "#2E86AB",  # Blue - standard MFA processes
    "splitter": "#A23B72",  # Pink - splitter processes (material = WC + DM)
    "transformer": "#F18F01",  # Orange - transformer processes (TC-based)
    "dsm": "#28A745",  # Green - Dynamic Stock Model processes
    "fomp": "#C73E1D",  # Red - First-Order Mineralization Process
    # Additional process types
    "storage": "#6C757D",  # Gray - storage processes
    "sink": "#DC3545",  # Red - sink processes
    "source": "#17A2B8",  # Cyan - source processes
}

# Process Differentiation Colors (avoids element colors: green, red, orange, blue)
PROCESS_DIFFERENTIATION_COLORS = [
    "#8B5A96",  # Purple - distinct from all elements
    "#A23B72",  # Deep Pink - distinct from all elements
    "#6C757D",  # Gray - neutral, distinct from all elements
    "#2E86AB",  # Deep Blue - different from bright blue element
    "#C73E1D",  # Dark Red - different from bright red element
    "#F18F01",  # Dark Orange - different from bright orange element
    "#28A745",  # Dark Green - different from bright green element
    "#17A2B8",  # Cyan - distinct from all elements
    "#6F42C1",  # Indigo - distinct from all elements
    "#E83E8C",  # Magenta - distinct from all elements
    "#20C997",  # Teal - distinct from all elements
    "#FD7E14",  # Dark Orange - distinct from bright orange
]

# Status Colors (for validation, errors, etc.)
STATUS_COLORS = {
    "success": "#28A745",  # Green
    "warning": "#FFC107",  # Yellow
    "error": "#DC3545",  # Red
    "info": "#17A2B8",  # Cyan
}

# =============================================================================
# TYPOGRAPHY
# =============================================================================

# Font Settings
FONT_FAMILY = "Arial, sans-serif"  # Professional, readable font
FONT_SIZE = {
    "title": 16,
    "subtitle": 14,
    "axis_title": 12,
    "axis_labels": 10,
    "legend": 10,
    "annotation": 9,
    "tick": 9,
}

# =============================================================================
# LAYOUT STANDARDS
# =============================================================================

# Standard Dimensions (in pixels)
FIGURE_SIZES = {
    "small": (800, 600),  # Small plots
    "medium": (1000, 750),  # Standard plots
    "large": (1200, 900),  # Large plots
    "wide": (1400, 700),  # Wide plots (dashboards)
    "tall": (800, 1200),  # Tall plots
    "square": (800, 800),  # Square plots
    "publication": (1000, 800),  # Publication standard
    "sankey_wide": (
        2600,
        500,
    ),  # Very wide Sankey (horizontal elongated flow) - increased for better visibility
}

# Print Dimensions (A4, Letter)
PRINT_SIZES = {
    "A4_portrait": (210, 297),  # mm
    "A4_landscape": (297, 210),  # mm
    "letter_portrait": (216, 279),  # mm
    "letter_landscape": (279, 216),  # mm
}

# Margins and Spacing
MARGINS = {
    "tight": dict(l=50, r=50, t=50, b=50),
    "standard": dict(l=80, r=50, t=80, b=80),
    "publication": dict(l=100, r=50, t=100, b=100),
    "wide": dict(l=50, r=50, t=80, b=50),
}

# =============================================================================
# GRID AND BACKGROUND
# =============================================================================

# Grid Settings
GRID_STYLE = {"show": True, "color": "#E5E5E5", "width": 1, "dash": "dot"}

# Background Colors
BACKGROUND_COLORS = {
    "white": "#FFFFFF",
    "light_gray": "#FAFAFA",
    "transparent": "rgba(0,0,0,0)",
}

# =============================================================================
# EXPORT SETTINGS
# =============================================================================

# High-resolution export settings
EXPORT_SETTINGS = {
    "png": {
        "width": 1200,
        "height": 900,
        "scale": 3,  # 3x for 300 DPI
        "format": "png",
    },
    "pdf": {"width": 1200, "height": 900, "format": "pdf"},
    "svg": {"width": 1200, "height": 900, "format": "svg"},
    "print": {
        "width": 1200,
        "height": 900,
        "scale": 4,  # 4x for 400 DPI (publication quality)
        "format": "png",
    },
}

# =============================================================================
# HELPER FUNCTIONS
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

    Returns
    -------
    dict
        A dictionary representing the Plotly layout configuration.
    """
    layout = {
        "width": FIGURE_SIZES[size][0],
        "height": FIGURE_SIZES[size][1],
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
            "rangemode": "tozero",  # Added this line
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
        The hexadecimal color code (e.g., '#00C851') for the given element.
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


def create_element_color_variations(base_color, n_variations):
    """Creates color variations based on a single element color.

    This function generates a list of color variations (shades and tints)
    from a given base color, which is useful for distinguishing sub-categories
    within a single element in a plot.

    Parameters
    ----------
    base_color : str
        The base hexadecimal color code (e.g., '#00C851').
    n_variations : int
        The number of color variations to generate.

    Returns
    -------
    list of str
        A list of hexadecimal color codes in the same color family as the
        base color.
    """
    import colorsys

    # Convert hex to RGB
    hex_color = base_color.lstrip("#")
    rgb = tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

    # Convert RGB to HSV for easier manipulation
    hsv = colorsys.rgb_to_hsv(rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0)
    h, s, v = hsv

    variations = []

    if n_variations == 1:
        return [base_color]

    # Generate variations by adjusting saturation and value
    for i in range(n_variations):
        # Create variation by adjusting saturation and brightness
        # Keep hue constant to maintain color family
        variation_s = max(0.3, min(1.0, s * (0.7 + 0.3 * i / (n_variations - 1))))
        variation_v = max(0.4, min(1.0, v * (0.8 + 0.2 * i / (n_variations - 1))))

        # Convert back to RGB
        rgb_variation = colorsys.hsv_to_rgb(h, variation_s, variation_v)

        # Convert to hex
        hex_variation = "#{:02x}{:02x}{:02x}".format(
            int(rgb_variation[0] * 255),
            int(rgb_variation[1] * 255),
            int(rgb_variation[2] * 255),
        )

        variations.append(hex_variation)

    return variations


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


# =============================================================================
# MATPLOTLIB STYLE SETTINGS
# =============================================================================


def setup_matplotlib_style():
    """Configures Matplotlib for publication-quality plots.

    This function sets the global `matplotlib.rcParams` to ensure that all
    subsequently created Matplotlib plots adhere to the BioDYM project's
    publication standards, including font, colors, grid style, and DPI.
    """
    plt.style.use("default")

    # Set font
    mpl.rcParams["font.family"] = "Arial"
    mpl.rcParams["font.size"] = 10

    # Set colors
    mpl.rcParams["axes.prop_cycle"] = mpl.cycler(color=list(BIOYM_COLORS.values()))

    # Set grid
    mpl.rcParams["axes.grid"] = True
    mpl.rcParams["grid.color"] = GRID_STYLE["color"]
    mpl.rcParams["grid.alpha"] = 0.3
    mpl.rcParams["grid.linewidth"] = GRID_STYLE["width"]

    # Set figure
    mpl.rcParams["figure.dpi"] = 300
    mpl.rcParams["savefig.dpi"] = 300
    mpl.rcParams["savefig.bbox"] = "tight"
    mpl.rcParams["savefig.pad_inches"] = 0.1


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================


def validate_color(color):
    """Validates that a color string is a valid hexadecimal color code.

    Parameters
    ----------
    color : str
        The color string to validate.

    Returns
    -------
    bool
        True if the color is a valid hexadecimal color code (e.g., '#RRGGBB'),
        False otherwise.
    """
    if color.startswith("#") and len(color) == 7:
        try:
            int(color[1:], 16)
            return True
        except ValueError:
            return False
    return False


def get_all_standards():
    """Retrieves all styling standards as a single dictionary.

    This function aggregates all the defined styling constants (colors, fonts,
    sizes, margins, and export settings) into a single dictionary, providing
    a convenient way to access or review all styling parameters at once.

    Returns
    -------
    dict
        A nested dictionary containing all styling standards.
    """
    return {
        "colors": {
            "bioym": BIOYM_COLORS,
            "elements": ELEMENT_COLORS,
            "processes": PROCESS_COLORS,
            "status": STATUS_COLORS,
        },
        "fonts": FONT_SIZE,
        "sizes": FIGURE_SIZES,
        "margins": MARGINS,
        "export": EXPORT_SETTINGS,
    }


# Initialize matplotlib style when module is imported
setup_matplotlib_style()
