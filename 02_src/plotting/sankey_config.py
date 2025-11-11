"""
Sankey Diagram Configuration

This file contains all the settings for the Sankey diagrams.
Optimized for readability and proper display in Jupyter notebooks.
"""

# General Layout - Optimized for readability
WINDOW_WIDTH = 3500        # Width in pixels (increased from 2000 for better label visibility)
WINDOW_HEIGHT = 1500       # Height in pixels (increased from 1000 for vertical breathing room)
BACKGROUND_COLOR = "#FFFFFF"
GRID_COLOR = "#E0E0E0"
PADDING_FACTOR = 0.02      # Factor of width/height for margins (0.02 = 2%)

# Node Settings
NODE_SPACING = 30          # Padding between nodes in pixels
NODE_SCALE_FACTOR = 1.5    # Multiplier for node thickness (base=20, so 20*1.5=30px)

# Zoom and Pan (Future features)
AUTO_FIT_FRAME = False
MIN_ZOOM_FACTOR = 0.3
MAX_ZOOM_FACTOR = 3.0
ZOOM_FACTOR = 1
