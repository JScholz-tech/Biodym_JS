"""
Sankey Diagram Configuration

This file contains all the settings for the Sankey diagrams.
Optimized for readability and proper display in Jupyter notebooks.
"""

# General Layout - Optimized for readability
WINDOW_WIDTH = 2000  # Width in pixels (increased from 2000 for better label visibility)
WINDOW_HEIGHT = (
    1000  # Height in pixels (increased from 1000 for vertical breathing room)
)
BACKGROUND_COLOR = "#FFFFFF"
GRID_COLOR = "#E0E0E0"
PADDING_FACTOR = 0.2  # Factor of width/height for margins (0.02 = 2%)

# Node Settings
NODE_SPACING = 20  # Padding between nodes in pixels
NODE_THICKNESS = 50  # Node thickness in pixels
NODE_LABEL_WRAP = True  # Enable automatic line breaks for long labels
NODE_LABEL_MAX_CHARS = (
    15  # Maximum characters per line before wrapping (0 = no wrapping)
)

# Font Settings
FONT_SIZE_TITLE = 40  # Title font size in points
FONT_SIZE_LABELS = 25  # Node label font size in points
FONT_SIZE_SUBPLOT = 16  # Subplot title font size in points
FONT_COLOR_LABELS = "black"  # Node label text color (e.g., "black", "#333333", "white")
FONT_WEIGHT_LABELS = "normal"  # Node label font weight: "normal", "bold"

# Title Settings
# Main title template - Use {element} for element name, {year} for year
# Example: "Wood Material Flows - {element} ({year})"
TITLE_TEMPLATE = "bioDYM -  Case Study 1: Wheat Straw - Element: {element} Year: {year}"
# Element formatting in main title: "title" (Material), "upper" (MATERIAL), "lower" (material)
TITLE_ELEMENT_FORMAT = "upper"

# Subplot title template for multi-element diagrams
# Use {element} as placeholder for element name
# Example: "{element} Flows" or "Element: {element}"
SUBPLOT_TITLE_TEMPLATE = "{element}"
# Element formatting in subplot titles: "upper" (MATERIAL), "title" (Material), "lower" (material)
SUBPLOT_ELEMENT_FORMAT = "upper"

# Grid Settings (Vertical Reference Lines for Process Stages)
ENABLE_GRID = True  # Enable/disable grid
GRID_TYPE = "vertical_lines"  # Grid type (currently only vertical_lines)
GRID_LINE_COLOR = "#D0D0D0"  # Grid line color (light gray)
GRID_LINE_WIDTH = 1  # Grid line width in pixels
GRID_LINE_DASH = "dot"  # Line style: "solid", "dot", "dash", "dashdot"
GRID_LINE_OPACITY = 0.5  # Line opacity (0-1)
GRID_VERTICAL_POSITIONS = [
    0.25,
    0.5,
    0.75,
]  # Positions as fraction of width (e.g., 0.25 = 25% from left)

# Flow Settings
ENABLE_FLOW_ARROWS = True  # Show arrows on flow links to indicate direction
FLOW_ARROW_LENGTH = 15  # Arrow length in pixels (typical range: 10-30)

# Zoom and Pan (Future features)
AUTO_FIT_FRAME = False
MIN_ZOOM_FACTOR = 0.3
MAX_ZOOM_FACTOR = 3.0
ZOOM_FACTOR = 3
