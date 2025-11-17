# Sankey Configuration Recommendations

## Current Issues
- Default size (2000×1000) is too small - labels overlap
- NODE_SPACING = 0.1 is unclear (unit?)
- PADDING_FACTOR = 1 creates excessive margins

## Recommended Settings

### Based on Enhanced Sankey Defaults
Enhanced sankey uses: `window_width=1400, window_height=900`

### Our Testing Results
During testing, we found:
- **5000×2000** provides excellent readability for complex diagrams
- **30px node padding** gives good spacing
- **Node scale factor of 1.5-2.0** works well for most cases

## Suggested `sankey_config.py`

```python
"""
Sankey Diagram Configuration

This file contains all the settings for the Sankey diagrams.
"""

# General Layout - Optimized for readability
WINDOW_WIDTH = 3500        # Was: 2000 (increased for better label visibility)
WINDOW_HEIGHT = 1500       # Was: 1000 (increased for vertical breathing room)
BACKGROUND_COLOR = "#FFFFFF"
GRID_COLOR = "#E0E0E0"
PADDING_FACTOR = 0.02      # Was: 1 (reduced - factor of width/height for margins)

# Node Settings
NODE_SPACING = 30          # Was: 0.1 (now in pixels, matches enhanced_sankey)
NODE_SCALE_FACTOR = 1.5    # Was: 4 (reduced - multiplier for node thickness)

# Zoom and Pan (Future features)
AUTO_FIT_FRAME = False
MIN_ZOOM_FACTOR = 0.3
MAX_ZOOM_FACTOR = 3.0
ZOOM_FACTOR = 1
```

## Rationale

### Window Size: 3500×1500
- **Compromise** between 2000×1000 (too small) and 5000×2000 (very large)
- Works well in Jupyter notebooks without excessive scrolling
- Matches enhanced_sankey approach (1400×900 but we need larger)
- Readable labels without overwhelming the display

### NODE_SPACING: 30 pixels
- Clear unit (pixels, not abstract 0.1)
- Matches enhanced_sankey's node padding parameter
- Provides good visual separation between nodes

### NODE_SCALE_FACTOR: 1.5
- Base thickness is 20px, so 20 × 1.5 = 30px node thickness
- Previous value of 4 would create 80px thick nodes (too large)
- Provides visible nodes without dominating the diagram

### PADDING_FACTOR: 0.02
- Creates margins of 2% of width/height
- For 3500×1500: margins of ~70×30 pixels
- Previous value of 1 created margins equal to full width/height (excessive)

## Alternative Profiles

### Compact (for dashboards)
```python
WINDOW_WIDTH = 2500
WINDOW_HEIGHT = 1000
NODE_SPACING = 20
NODE_SCALE_FACTOR = 1.0
PADDING_FACTOR = 0.015
```

### Large (for publications)
```python
WINDOW_WIDTH = 5000
WINDOW_HEIGHT = 2000
NODE_SPACING = 40
NODE_SCALE_FACTOR = 2.0
PADDING_FACTOR = 0.025
```

### Enhanced Sankey Style
```python
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900
NODE_SPACING = 20
NODE_SCALE_FACTOR = 1.0
PADDING_FACTOR = 0.03
```
