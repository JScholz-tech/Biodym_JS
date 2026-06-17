# -*- coding: utf-8 -*-
"""
Plotting Themes and Style Standards for BioDYM

Central module for all plot styling. Provides:
- Named theme presets ('exploratory', 'jie') via set_theme() / get_active_theme()
- Color palettes, font settings, figure size presets
- get_publication_layout() for standardised Plotly layout dicts

Usage
-----
    import plotting
    plotting.set_theme('jie')       # once per session → all subsequent plots use JIE style
    plotting.set_theme('exploratory')  # back to wide interactive style
"""

# =============================================================================
# THEME SYSTEM
# =============================================================================

# Module-level active theme — default is 'exploratory' (wide, annotated)
_ACTIVE_THEME = "exploratory"

# Config-driven unit override — set by set_mass_unit_from_config().
# When not None, get_mass_display() always returns (1.0, _CONFIG_UNIT),
# regardless of which theme is active or in what order set_theme() is called.
_CONFIG_UNIT: str | None = None

THEMES = {
    # JIE (Springer Nature): single-column text area = 174 mm wide, max height 234 mm.
    # At 96 dpi screen: 174/25.4*96 = 658 px wide, 234/25.4*96 = 884 px max height.
    # Combination art (color + text) requires ≥600 DPI → export scale = 600/96 = 6.25
    # → final export: 658*6.25 = 4113 px wide = 174 mm at 600 DPI. Use SVG/EPS for vector.
    "jie": {
        "width": 658,
        "height": 440,
        "font_axis": 14,
        "font_tick": 14,
        "font_legend": 14,
        "legend_below": True,
        "show_title": False,
        "x_range": [2025, 2125],
        "grid_color": "#e8e8e8",
        "grid_dash": "solid",
        "margin": dict(l=70, r=30, t=20, b=100),
        "scientific_y": False,   # readable tick labels, not 2.00e+4
        "template": "plotly_white",
        "mass_scale": 1e-3,      # Mg → Gg
        "mass_unit": "Gg",
    },
    # Exploratory: wide, annotated, larger fonts — good for interactive notebook use.
    "exploratory": {
        "width": 1000,
        "height": 800,
        "font_axis": 18,
        "font_tick": 16,
        "font_legend": 16,
        "legend_below": True,
        "show_title": True,
        "x_range": None,
        "grid_color": "#E5E5E5",
        "grid_dash": "dot",
        "margin": dict(l=100, r=50, t=100, b=150),
        "scientific_y": True,    # 2.00e+4 format
        "template": "plotly_white",
        "mass_scale": 1.0,       # keep Mg
        "mass_unit": "Mg",
    },
}


def set_theme(name: str) -> None:
    """Set the global plot theme for all subsequent BioDYM plots.

    Call once per notebook session, typically near the top of the notebook:

        import plotting
        plotting.set_theme('jie')

    Parameters
    ----------
    name : str
        Theme name. One of:
        - 'exploratory' (default) — 1000×800 px, large fonts, title visible
        - 'jie' — 672×432 px (7×4.5 in), 11 pt fonts, no title, legend below
    """
    global _ACTIVE_THEME
    if name not in THEMES:
        raise ValueError(f"Unknown theme '{name}'. Choose from: {list(THEMES)}")
    _ACTIVE_THEME = name


def get_active_theme() -> dict:
    """Return the currently active theme configuration dict."""
    return THEMES[_ACTIVE_THEME]


def get_theme(name: str) -> dict:
    """Return a named theme config dict without changing the active theme.

    Parameters
    ----------
    name : str
        Theme name ('exploratory' or 'jie').
    """
    if name not in THEMES:
        raise ValueError(f"Unknown theme '{name}'. Choose from: {list(THEMES)}")
    return THEMES[name]


def apply_theme(layout: dict) -> dict:
    """Apply the active theme's size, fonts, grid, legend, and margin to a layout dict.

    Call immediately after get_publication_layout() to apply the current theme:

        layout_config = get_publication_layout(custom_title="...", ...)
        apply_theme(layout_config)
        fig.update_layout(**layout_config)

    Modifies the dict in-place and also returns it for chaining.
    Handles single-axis layouts. For multi-subplot figures (xaxis2, xaxis3, …)
    only the primary axes are updated; subplot axes keep their defaults.

    Parameters
    ----------
    layout : dict
        A layout dict as returned by get_publication_layout().

    Returns
    -------
    dict
        The same dict, modified in-place with theme overrides applied.
    """
    import re as _re
    _t = get_active_theme()
    _sci_fmt = ".3~e" if _t.get("scientific_y", True) else ","

    # Figure size
    layout["width"] = _t["width"]
    layout["height"] = _t["height"]

    # Plotly template (sets overall look before any overrides)
    layout["template"] = _t.get("template", "plotly_white")

    # Global tick font
    layout["font"]["size"] = _t["font_tick"]

    def _patch_xaxis(ax):
        if "title" in ax and isinstance(ax["title"], dict):
            ax["title"].setdefault("font", {})["size"] = _t["font_axis"]
        ax.setdefault("tickfont", {})["size"] = _t["font_tick"]
        ax["gridcolor"] = _t["grid_color"]
        ax["griddash"] = _t.get("grid_dash", "dot")
        if _t["x_range"] is not None:
            ax["range"] = _t["x_range"]
        elif "range" in ax:
            del ax["range"]

    def _patch_yaxis(ay):
        if "title" in ay and isinstance(ay["title"], dict):
            ay["title"].setdefault("font", {})["size"] = _t["font_axis"]
        ay.setdefault("tickfont", {})["size"] = _t["font_tick"]
        ay["gridcolor"] = _t["grid_color"]
        ay["griddash"] = _t.get("grid_dash", "dot")
        ay["tickformat"] = _sci_fmt

    # Primary axes
    if "xaxis" in layout:
        _patch_xaxis(layout["xaxis"])
    if "yaxis" in layout:
        _patch_yaxis(layout["yaxis"])

    # Numbered subplot axes (xaxis2, yaxis3, …)
    _ax_re = _re.compile(r"^([xy]axis)(\d+)$")
    for key, ax in list(layout.items()):
        m = _ax_re.match(key)
        if not m or not isinstance(ax, dict):
            continue
        if m.group(1) == "xaxis":
            _patch_xaxis(ax)
        else:
            _patch_yaxis(ax)

    # Legend font + optional below placement
    if "legend" in layout:
        layout["legend"]["font"]["size"] = _t["font_legend"]
        if _t["legend_below"]:
            layout["legend"].update(
                orientation="h", yanchor="top", y=-0.22,
                xanchor="center", x=0.5,
            )

    # Title visibility
    if not _t["show_title"]:
        layout.pop("title", None)

    # Margins
    layout["margin"] = _t["margin"]

    # Preserve widget state across tab switches / re-renders
    layout["uirevision"] = "constant"

    return layout


def get_mass_display() -> tuple:
    """Return (scale_factor, unit_string) for the active theme.

    Plot functions should multiply raw data values by scale_factor and use
    unit_string in axis labels and hover templates.

    If set_mass_unit_from_config() has been called, the config unit always
    takes precedence over the theme unit (scale=1.0, unit=config_unit).

    Returns
    -------
    (scale, unit) : tuple[float, str]
        e.g. (1e-3, 'Gg') for 'jie' theme, (1.0, 'Mg') for 'exploratory',
        or (1.0, 'kg') if config unit is 'kg'.
    """
    if _CONFIG_UNIT is not None:
        return 1.0, _CONFIG_UNIT
    _t = get_active_theme()
    return _t.get("mass_scale", 1.0), _t.get("mass_unit", "Mg")


def set_mass_unit_from_config(config_obj) -> None:
    """Set the config-driven unit override from the configuration object.

    Call once after load_configuration(). The unit is stored at module level
    so it survives subsequent set_theme() calls — order of calls does not matter.

    Checks these attribute names in order (matching common Excel column names):
    ``Unit``, ``Unit_of_Measurement``, ``UoM``, ``Mass_Unit``.
    A blank, NaN, or missing value is a no-op.

    Parameters
    ----------
    config_obj : Config
        Loaded configuration object (e.g. 'kg', 'Mg', 'Gg').
    """
    global _CONFIG_UNIT
    _candidates = ("Unit", "Unit_of_Measurement", "UoM", "Mass_Unit")
    unit = None
    for attr in _candidates:
        val = getattr(config_obj, attr, None)
        if val and isinstance(val, str) and val.strip():
            unit = val.strip()
            break
    if unit is None:
        return
    _CONFIG_UNIT = unit
    print(f"  [themes] mass_unit set to '{_CONFIG_UNIT}' from config (overrides theme)")


def y_label(element: str, rate: bool = False) -> str:
    """Return a themed y-axis label in the form 'mass {element} ({unit})'.

    Parameters
    ----------
    element : str
        Element name, e.g. 'TC', 'DM', 'Material'.
    rate : bool
        If True, appends ' yr⁻¹' to the unit (for annual flow plots).

    Returns
    -------
    str
        e.g. 'mass TC (Gg)' or 'mass TC (Gg yr\u207b\u00b9)'
    """
    _, unit = get_mass_display()
    suffix = " yr\u207b\u00b9" if rate else ""
    return f"mass {element} ({unit}{suffix})"


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
    "regular": "#2E86AB",       # Blue - standard MFA processes
    "splitter": "#A23B72",      # Pink - splitter processes
    "transformer": "#F18F01",   # Orange - transformer processes
    "dsm": "#28A745",           # Green - Dynamic Stock Model processes
    "fomp": "#C73E1D",          # Red - First-Order Mineralization Process
    "bom_assembler": "#7B2D8B", # Purple - BOM Assembler (constrained assembly)
    "lfg": "#1A7A4A",           # Dark green - Landfill Gas processes
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
# JIE publication: SVG (vector, preferred by Springer) or PNG at scale=6.25 → 600 DPI at 174mm.
EXPORT_SETTINGS = {
    "png": {"width": 1200, "height": 900, "scale": 3, "format": "png"},
    "pdf": {"width": 1200, "height": 900, "format": "pdf"},
    "svg": {"width": 1200, "height": 900, "format": "svg"},
    "print": {"width": 1200, "height": 900, "scale": 4, "format": "png"},
    "jie_svg": {"width": 658, "height": 440, "format": "svg"},           # vector, preferred
    "jie_png": {"width": 658, "height": 440, "scale": 6.25, "format": "png"},  # 600 DPI
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
    process_id,
    process_logic_map=None,
    dsm_params=None,
    fomp_params=None,
    bom_params=None,
    lfg_params=None,
):
    """Automatically detects the BioDYM process type based on configuration.

    Parameters
    ----------
    process_id : int
        The unique identifier of the process.
    process_logic_map : dict, optional
        Maps process IDs to their logic type strings.
    dsm_params : dict, optional
        DSM process configurations (keyed by process ID).
    fomp_params : dict, optional
        FOMP process configurations (keyed by process ID).
    bom_params : dict, optional
        BOM Assembler configurations (keyed by process ID).
    lfg_params : dict, optional
        LFG process configurations (keyed by process ID).

    Returns
    -------
    str
        One of: 'regular', 'splitter', 'transformer', 'dsm', 'fomp',
        'bom_assembler', 'lfg'.
    """
    # Params dicts take priority — they are authoritative for active processes
    if dsm_params and process_id in dsm_params:
        return "dsm"
    if fomp_params and process_id in fomp_params:
        return "fomp"
    if bom_params and process_id in bom_params:
        return "bom_assembler"
    if lfg_params and process_id in lfg_params:
        return "lfg"

    # Fall back to process_logic_map for processes not in params dicts
    if process_logic_map and process_id in process_logic_map:
        logic_type = str(process_logic_map[process_id]).strip().lower()
        known = {"splitter", "transformer", "dsm", "fomp", "bom_assembler", "lfg"}
        if logic_type in known:
            return logic_type

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
