# Sankey Diagram Size and Positioning Guide

## Overview

The Sankey diagram plotting functions in BioDYM now support:
1. **Custom sizing** (width, height)
2. **Automatic vertical node spacing** (prevents label overlap)
3. **Manual node positioning** (from Excel configuration)
4. **Element-specific positioning** (different layouts per element)

## Problem Solved

**Before**: Process labels overlapped and were unreadable due to:
- Fixed small diagram size
- No vertical spacing between nodes
- Nodes stacked at same y-coordinate

**After**:
- Adjustable diagram dimensions
- Automatic vertical distribution of nodes within layers
- Manual positioning via Excel configuration

---

## Quick Start: Adjusting Diagram Size

### Method 1: Direct Parameters (Easiest)

```python
# Single interactive Sankey with custom size
plotting.plot_interactive_sankey(
    mfa_results_baseline,
    dsm_params=dsm_params,
    fomp_params=fomp_params,
    width=3000,        # Wider diagram (default: 2200)
    height=1200,       # Taller diagram (default: 800)
    node_spacing=0.15  # More vertical space (default: 0.1)
)
```

### Method 2: Multiplot Sankey

```python
# Multiple element plots with custom size
plotting.plot_element_multiplot_sankey(
    mfa_results_baseline,
    dsm_params=dsm_params,
    fomp_params=fomp_params,
    subplot_height=500,  # Taller subplots (default: 350)
    subplot_width=3000,  # Wider subplots (default: 2200)
    node_spacing=0.15    # More vertical space
)
```

---

## Advanced: Manual Node Positioning

### Option 1: Via Excel Configuration

BioDYM can read node positions from your Excel file's visualization sheet (`6_1_Visualization_Processes`).

#### Column Format in Excel

| Process_ID | X_Position | Y_Position | X_Position_Material | Y_Position_Material | X_Position_WC | Y_Position_WC | ... |
|------------|------------|------------|---------------------|---------------------|---------------|---------------|-----|
| P1         | 0.1        | 0.5        | 0.15                | 0.3                 | 0.1           | 0.7           | ... |
| P2         | 0.5        | 0.5        | 0.5                 | 0.6                 | 0.5           | 0.4           | ... |
| P3         | 0.9        | 0.5        | 0.85                | 0.5                 | 0.9           | 0.5           | ... |

**Coordinate system**:
- X: 0 (left) to 1 (right)
- Y: 0 (top) to 1 (bottom)

**Column naming**:
- `X_Position`, `Y_Position` - General positions (used if element-specific not found)
- `X_Position_Material`, `Y_Position_Material` - Material-specific positions
- `X_Position_WC`, `Y_Position_WC` - Water content-specific positions
- `X_Position_DM`, `Y_Position_DM` - Dry matter-specific positions
- `X_Position_CC`, `Y_Position_CC` - Carbon content-specific positions

#### Using Excel Positions in Code

```python
from plotting import visualization_loader

# Load visualization config from Excel
viz_config = visualization_loader.load_visualization_config_from_excel(
    "01_data/01_input/251108_BioDYM_ODYM_CS1_Whaeat_Straw.xlsm"
)

# Use in Sankey plot
plotting.plot_interactive_sankey(
    mfa_results_baseline,
    dsm_params=dsm_params,
    fomp_params=fomp_params,
    viz_config=viz_config,  # Positions loaded automatically
    width=3000,
    height=1200
)
```

### Option 2: Manual Positions via Python Dictionary

```python
# Define manual positions in code
manual_positions = {
    'P1': {'x': 0.1, 'y': 0.3},   # Top-left
    'P2': {'x': 0.5, 'y': 0.6},   # Middle-right
    'P3': {'x': 0.9, 'y': 0.5},   # Bottom-right
    # Can specify just x or just y, missing coordinate uses automatic positioning
    'P4': {'x': 0.7, 'y': None},  # Auto y-position, manual x
}

plotting.plot_interactive_sankey(
    mfa_results_baseline,
    dsm_params=dsm_params,
    fomp_params=fomp_params,
    manual_positions=manual_positions,
    width=3000,
    height=1200
)
```

---

## Understanding Node Positioning Algorithm

### Automatic Positioning (Default)

1. **Horizontal (X)**: Uses topological sort to arrange nodes in layers
   - Source processes → left
   - Sink processes → right
   - Intermediate processes → middle layers

2. **Vertical (Y)**: Distributes nodes within each layer
   - Nodes in the same layer are evenly spaced vertically
   - `node_spacing` parameter controls spacing (0 to 1)
   - Prevents overlapping labels

### Manual + Automatic Hybrid

- Specify positions for some processes
- Others use automatic positioning
- Useful for fixing problematic nodes while keeping others automatic

---

## Parameter Reference

### `plot_interactive_sankey()`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `width` | int | 2200 | Width in pixels |
| `height` | int | 800 | Height in pixels |
| `node_spacing` | float | 0.1 | Vertical spacing (0-1) |
| `manual_positions` | dict | None | Manual node positions |
| `viz_config` | dict | None | Config from Excel |

### `plot_element_multiplot_sankey()`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `subplot_height` | int | 350 | Height per subplot (px) |
| `subplot_width` | int | 2200 | Width per subplot (px) |
| `node_spacing` | float | 0.1 | Vertical spacing (0-1) |
| `viz_config` | dict | None | Config from Excel |

---

## Examples

### Example 1: Fix Overlapping Labels (Quick)

```python
# Just increase height and spacing
plotting.plot_interactive_sankey(
    mfa_results_baseline,
    dsm_params=dsm_params,
    fomp_params=fomp_params,
    height=1000,        # Taller diagram
    node_spacing=0.2    # Double spacing
)
```

### Example 2: Publication-Quality Layout

```python
# Load positions from Excel
viz_config = visualization_loader.load_visualization_config_from_excel(input_file)

plotting.plot_interactive_sankey(
    mfa_results_baseline,
    dsm_params=dsm_params,
    fomp_params=fomp_params,
    viz_config=viz_config,
    width=3500,
    height=1500,
    node_spacing=0.12
)
```

### Example 3: Custom Positioning for Specific Nodes

```python
# Position key processes manually, let others auto-arrange
manual_pos = {
    'Atmosphere': {'x': 0.05, 'y': 0.2},
    'Lithosphere_(P&I)': {'x': 0.95, 'y': 0.8},
    'Environment': {'x': 0.05, 'y': 0.5}
}

plotting.plot_interactive_sankey(
    mfa_results_baseline,
    dsm_params=dsm_params,
    fomp_params=fomp_params,
    manual_positions=manual_pos,
    width=3000,
    height=1200,
    node_spacing=0.15
)
```

---

## Tips & Recommendations

1. **Start with automatic positioning**
   - Try increasing `height` and `node_spacing` first
   - This solves most overlap issues without manual work

2. **Use element-specific positions in Excel**
   - Different elements may need different layouts
   - E.g., Material flow may be complex, while CC is simpler

3. **Export and refine iteratively**
   - Generate initial Sankey
   - Note which processes need repositioning
   - Add manual positions incrementally

4. **Coordinate ranges**
   - X: Keep between 0.05-0.95 (avoid edges)
   - Y: Keep between 0.1-0.9 (leave room for labels)

5. **For publication**
   - Use `width=3500`, `height=1500` or larger
   - Save manual positions in Excel for reproducibility
   - Use `node_spacing=0.12-0.15` for clarity

---

## Troubleshooting

### Issue: Labels still overlap
**Solution**: Increase `height` and `node_spacing` further

```python
height=1500,
node_spacing=0.25
```

### Issue: Manual positions not working
**Check**:
1. Process IDs match exactly (case-sensitive)
2. Coordinates are floats between 0 and 1
3. Excel sheet `6_1_Visualization_Processes` exists and has correct columns

### Issue: Some nodes disappear
**Cause**: Coordinates outside 0-1 range or filtering
**Solution**: Check coordinate values, ensure processes are selected in widget

---

## File Locations

- **Main code**: `02_src/plotting/sankey.py`
- **Visualization loader**: `02_src/plotting/visualization_loader.py`
- **Excel config sheet**: `6_1_Visualization_Processes` in input file
- **This guide**: `05_docs/SANKEY_SIZE_AND_POSITIONING_GUIDE.md`

---

**Last Updated**: 2025-11-10
**Author**: BioDYM Development Team
