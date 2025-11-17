# -*- coding: utf-8 -*-
"""
Dynamic Element-Agnostic Color System for BioDYM

This module provides a flexible color assignment system that works with ANY
element configuration (not just material, WC, DM, CC). It supports:
- Automatic color assignment for custom element sets
- Color-blind friendly palettes
- Hierarchical element visualization
- Consistent styling across all plots

Author: BioDYM Development Team
Date: 2025-11-04
"""

import colorsys
from typing import List, Dict, Optional, Tuple


# =============================================================================
# COLOR PALETTES
# =============================================================================

# Default palette (bright, distinct colors)
DEFAULT_ELEMENT_PALETTE = [
    "#00C851",  # Bright Green - material
    "#007BFF",  # Bright Blue - water
    "#FF8C00",  # Bright Orange - dry matter
    "#FF4444",  # Bright Red - carbon
    "#9C27B0",  # Purple - nitrogen
    "#FFC107",  # Yellow - phosphorus
    "#00BCD4",  # Cyan - additional
    "#E91E63",  # Pink - additional
]

# Color-blind friendly palette (Okabe-Ito + extensions)
# Works for Protanopia, Deuteranopia, Tritanopia
COLORBLIND_ELEMENT_PALETTE = [
    "#0173B2",  # Blue - material (replaces green)
    "#56B4E9",  # Sky Blue - water
    "#E69F00",  # Orange - dry matter
    "#CC79A7",  # Pink - carbon (replaces red)
    "#009E73",  # Teal - nitrogen
    "#F0E442",  # Yellow - phosphorus
    "#D55E00",  # Vermillion - additional
    "#999999",  # Gray - additional
]

# Grayscale palette (for black & white printing)
GRAYSCALE_ELEMENT_PALETTE = [
    "#2C2C2C",  # Very dark gray
    "#5C5C5C",  # Dark gray
    "#8C8C8C",  # Medium gray
    "#BCBCBC",  # Light gray
    "#4C4C4C",  # Dark gray 2
    "#7C7C7C",  # Medium gray 2
    "#ACACAC",  # Light gray 2
    "#DCDCDC",  # Very light gray
]

# Stock colors (distinct from flow colors, more muted)
STOCK_PALETTE = [
    "#6F42C1",  # Purple - default stock
    "#28A745",  # Green - material stock
    "#17A2B8",  # Teal - water stock
    "#FD7E14",  # Dark orange - dry matter stock
    "#DC3545",  # Dark red - carbon stock
    "#6610F2",  # Indigo - additional
    "#20C997",  # Turquoise - additional
    "#E83E8C",  # Magenta - additional
]


# =============================================================================
# ELEMENT COLOR MANAGER
# =============================================================================


class ElementColorManager:
    """
    Manages dynamic color assignment for element-agnostic visualizations.

    This class automatically assigns colors to any set of elements, ensuring
    consistency across all plots. It supports multiple color schemes including
    color-blind friendly options.

    Attributes
    ----------
    elements : List[str]
        Ordered list of element names (e.g., ['material', 'WC', 'DM', 'CC'])
    color_scheme : str
        Active color scheme ('default', 'colorblind', 'grayscale')
    element_colors : Dict[str, str]
        Mapping of element names to hex color codes

    Examples
    --------
    >>> manager = ElementColorManager(['material', 'protein', 'lipids', 'carbs'])
    >>> color = manager.get_element_color('protein')
    >>> all_colors = manager.get_all_element_colors()
    """

    def __init__(
        self,
        elements: List[str],
        color_scheme: str = "default",
        custom_palette: Optional[List[str]] = None,
    ):
        """
        Initialize the element color manager.

        Parameters
        ----------
        elements : List[str]
            Ordered list of element names
        color_scheme : str, optional
            Color scheme to use ('default', 'colorblind', 'grayscale')
            Defaults to 'default'
        custom_palette : List[str], optional
            Custom color palette (hex codes). If provided, overrides color_scheme
            Defaults to None
        """
        self.elements = elements
        self.color_scheme = color_scheme
        self._custom_palette = custom_palette

        # Assign colors to elements
        self.element_colors = self._assign_colors()

        # Also create stock colors (more muted versions)
        self.stock_colors = self._assign_stock_colors()

    def _get_base_palette(self) -> List[str]:
        """Get the base color palette based on color scheme."""
        if self._custom_palette:
            return self._custom_palette
        elif self.color_scheme == "colorblind":
            return COLORBLIND_ELEMENT_PALETTE
        elif self.color_scheme == "grayscale":
            return GRAYSCALE_ELEMENT_PALETTE
        else:
            return DEFAULT_ELEMENT_PALETTE

    def _assign_colors(self) -> Dict[str, str]:
        """Assign colors to each element."""
        base_palette = self._get_base_palette()
        element_colors = {}

        # Assign colors from palette
        for i, element in enumerate(self.elements):
            if i < len(base_palette):
                element_colors[element] = base_palette[i]
            else:
                # Generate additional colors if needed
                element_colors[element] = self._generate_color(i, len(self.elements))

        return element_colors

    def _assign_stock_colors(self) -> Dict[str, str]:
        """Assign distinct stock colors (more muted than flow colors)."""
        stock_colors = {}

        for i, element in enumerate(self.elements):
            if i < len(STOCK_PALETTE):
                stock_colors[element] = STOCK_PALETTE[i]
            else:
                # Generate muted variation of element color
                stock_colors[element] = self._mute_color(self.element_colors[element])

        return stock_colors

    def _generate_color(self, index: int, total: int) -> str:
        """
        Generate a color using HSV color space for good distribution.

        Parameters
        ----------
        index : int
            Index of the color to generate
        total : int
            Total number of colors needed

        Returns
        -------
        str
            Hexadecimal color code
        """
        hue = (index / total) % 1.0
        saturation = 0.7 + (index % 3) * 0.1  # Vary saturation slightly
        value = 0.8 + (index % 2) * 0.1  # Vary brightness slightly

        rgb = colorsys.hsv_to_rgb(hue, saturation, value)
        return "#{:02x}{:02x}{:02x}".format(
            int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255)
        )

    def _mute_color(self, hex_color: str, factor: float = 0.6) -> str:
        """
        Create a muted version of a color (for stocks).

        Parameters
        ----------
        hex_color : str
            Hexadecimal color code (e.g., '#00C851')
        factor : float, optional
            Muting factor (0.0 = gray, 1.0 = original color)
            Defaults to 0.6

        Returns
        -------
        str
            Muted hexadecimal color code
        """
        # Convert hex to RGB
        hex_color = hex_color.lstrip("#")
        rgb = tuple(int(hex_color[i : i + 2], 16) / 255.0 for i in (0, 2, 4))

        # Convert to HSV
        h, s, v = colorsys.rgb_to_hsv(*rgb)

        # Reduce saturation and brightness
        s_new = s * factor
        v_new = v * 0.9

        # Convert back to RGB
        rgb_new = colorsys.hsv_to_rgb(h, s_new, v_new)

        return "#{:02x}{:02x}{:02x}".format(
            int(rgb_new[0] * 255), int(rgb_new[1] * 255), int(rgb_new[2] * 255)
        )

    def get_element_color(self, element: str, is_stock: bool = False) -> str:
        """
        Get the color for a specific element.

        Parameters
        ----------
        element : str
            Element name (case-insensitive)
        is_stock : bool, optional
            If True, return stock color instead of flow color
            Defaults to False

        Returns
        -------
        str
            Hexadecimal color code
        """
        element_lower = element.lower()

        # Try exact match first
        if is_stock:
            return self.stock_colors.get(element_lower, STOCK_PALETTE[0])
        else:
            return self.element_colors.get(element_lower, DEFAULT_ELEMENT_PALETTE[0])

    def get_all_element_colors(self, is_stock: bool = False) -> Dict[str, str]:
        """
        Get all element colors as a dictionary.

        Parameters
        ----------
        is_stock : bool, optional
            If True, return stock colors instead of flow colors
            Defaults to False

        Returns
        -------
        Dict[str, str]
            Mapping of element names to hex color codes
        """
        return self.stock_colors.copy() if is_stock else self.element_colors.copy()

    def get_color_sequence(self, is_stock: bool = False) -> List[str]:
        """
        Get ordered list of colors matching element order.

        Parameters
        ----------
        is_stock : bool, optional
            If True, return stock colors instead of flow colors
            Defaults to False

        Returns
        -------
        List[str]
            Ordered list of hex color codes
        """
        colors = self.stock_colors if is_stock else self.element_colors
        return [colors[elem] for elem in self.elements]

    def set_color_scheme(self, scheme: str):
        """
        Change the active color scheme.

        Parameters
        ----------
        scheme : str
            Color scheme name ('default', 'colorblind', 'grayscale')
        """
        self.color_scheme = scheme
        self.element_colors = self._assign_colors()
        self.stock_colors = self._assign_stock_colors()

    def get_legend_items(self) -> List[Tuple[str, str]]:
        """
        Get legend items with element names and colors.

        Returns
        -------
        List[Tuple[str, str]]
            List of (element_name, color) tuples for legend generation
        """
        return [(elem, self.element_colors[elem]) for elem in self.elements]


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def create_element_color_manager(
    config_obj, color_scheme: str = "default"
) -> ElementColorManager:
    """
    Create an ElementColorManager from a BioDYM config object.

    Parameters
    ----------
    config_obj : dict
        BioDYM configuration dictionary (from config.load_config_from_excel())
    color_scheme : str, optional
        Color scheme to use ('default', 'colorblind', 'grayscale')
        Defaults to 'default'

    Returns
    -------
    ElementColorManager
        Initialized color manager

    Examples
    --------
    >>> config = load_config_from_excel('my_system.xlsx')
    >>> color_manager = create_element_color_manager(config, 'colorblind')
    >>> material_color = color_manager.get_element_color('material')
    """
    # Extract elements from config
    elements_str = config_obj.get("Elements", "material,WC,DM,CC")
    elements = [e.strip().lower() for e in elements_str.split(",")]

    return ElementColorManager(elements, color_scheme)


def get_element_color_legacy(element_name: str) -> str:
    """
    Legacy function for backward compatibility.

    This function provides the old hardcoded colors for the default
    biomass elements (material, wc, dm, cc).

    Parameters
    ----------
    element_name : str
        Element name

    Returns
    -------
    str
        Hexadecimal color code

    Notes
    -----
    DEPRECATED: Use ElementColorManager instead for new code.
    """
    legacy_colors = {
        "material": "#00C851",
        "wc": "#007BFF",
        "dm": "#FF8C00",
        "cc": "#FF4444",
    }
    return legacy_colors.get(element_name.lower(), "#2E86AB")


# =============================================================================
# COLOR SCHEME TESTING
# =============================================================================


def print_color_scheme_comparison(elements: List[str]):
    """
    Print a comparison of all color schemes for given elements.

    Useful for testing and visualization during development.

    Parameters
    ----------
    elements : List[str]
        List of element names to display
    """
    schemes = ["default", "colorblind", "grayscale"]

    print("=" * 80)
    print("ELEMENT COLOR SCHEME COMPARISON")
    print("=" * 80)
    print(f"Elements: {', '.join(elements)}\n")

    for scheme in schemes:
        manager = ElementColorManager(elements, color_scheme=scheme)
        print(f"\n{scheme.upper()} SCHEME:")
        print("-" * 40)

        for elem in elements:
            flow_color = manager.get_element_color(elem, is_stock=False)
            stock_color = manager.get_element_color(elem, is_stock=True)
            print(f"  {elem:15s} - Flow: {flow_color}  Stock: {stock_color}")

    print("\n" + "=" * 80)


# =============================================================================
# INITIALIZATION
# =============================================================================

# Global instance (optional, can be set by main workflow)
_global_color_manager: Optional[ElementColorManager] = None


def set_global_color_manager(manager: ElementColorManager):
    """Set the global color manager instance."""
    global _global_color_manager
    _global_color_manager = manager


def get_global_color_manager() -> Optional[ElementColorManager]:
    """Get the global color manager instance (if set)."""
    return _global_color_manager
