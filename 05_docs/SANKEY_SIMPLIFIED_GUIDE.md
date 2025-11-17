# Simplified Sankey Diagram Guide

## Overview

The Sankey diagram module has been **dramatically simplified** (from 723 to 598 lines) by leveraging Plotly's built-in automatic positioning features instead of custom topological sorting algorithms.

## What Changed

### ✅ Removed (Simplified)
- **120+ lines of complex topological sorting code** - Plotly does this automatically
- **Custom vertical node distribution logic** - Plotly's `arrangement='snap'` handles this
- **Layer calculation algorithms** - Not needed
- **Complex coordinate calculation** - Simplified to direct passthrough

### ✅ Kept (Essential)
- Size parameters (`width`, `height`)
- Manual positioning from Excel (optional override)
- Element-agnostic coloring
- Interactive widgets for filtering
- Both single-element and multi-element plots

## How It Works Now

### Plotly's Automatic Positioning

Instead of custom algorithms, we use Plotly's built-in features:

```python
fig = go.Figure(data=[go.Sankey(
    arrangement='snap',  # Smart automatic positioning
    node={
        'label': node_labels,
        'color': node_colors,
        'pad': 20,  # Spacing between nodes (in pixels)
        'x': manual_x,  # Optional: only if manual positions provided
        'y': manual_y   # Optional: only if manual positions provided
    },
    link={...}
)])
```

**Key parameters:**
- `arrangement='snap'`: Plotly automatically positions nodes to prevent overlaps
- `node.pad`: Controls spacing between nodes (in pixels, not normalized)
- `node.x`, `node.y`: Optional manual positions (0-1 normalized), only used if provided

## Quick Start

### Basic Usage (Automatic Positioning)

```python
import plotting

# Plotly handles all positioning automatically
plotting.plot_interactive_sankey(
    mfa_results_baseline,
    dsm_params=dsm_params,
    fomp_params=fomp_params,
    width=2200,    # Default width
    height=800,    # Default height
    node_pad=20    # Spacing between nodes (pixels)
)
```

### Increase Size to Fix Overlaps

```python
# Make diagram larger with more spacing
plotting.plot_interactive_sankey(
    mfa_results_baseline,
    dsm_params=dsm_params,
    fomp_params=fomp_params,
    width=3000,     # Wider
    height=1200,    # Taller
    node_pad=30     # More spacing (pixels)
)
```

### Manual Positioning (Optional)

```python
# Override automatic positioning for specific nodes
manual_positions = {
    'Atmosphere': {'x': 0.05, 'y': 0.2},
    'Environment': {'x': 0.05, 'y': 0.8},
    'Harvest': {'x': 0.5, 'y': 0.5}
}

plotting.plot_interactive_sankey(
    mfa_results_baseline,
    manual_positions=manual_positions,
    width=3000,
    height=1200
)
```

### From Excel Configuration

```python
from plotting import visualization_loader

# Load positions from Excel file
viz_config = visualization_loader.load_visualization_config_from_excel(input_file)

plotting.plot_interactive_sankey(
    mfa_results_baseline,
    viz_config=viz_config,  # Loads positions from 6_1_Visualization_Processes
    width=3000,
    height=1200
)
```

## Parameter Reference

### `plot_interactive_sankey()`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `width` | int | 2200 | Width in pixels |
| `height` | int | 800 | Height in pixels |
| `node_pad` | int | 20 | Spacing between nodes (pixels) |
| `manual_positions` | dict | None | Optional manual positions |
| `viz_config` | dict | None | Config from Excel |

### `plot_element_multiplot_sankey()`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `subplot_width` | int | 2200 | Width per subplot (pixels) |
| `subplot_height` | int | 350 | Height per subplot (pixels) |
| `node_pad` | int | 20 | Spacing between nodes (pixels) |
| `viz_config` | dict | None | Config from Excel |

## Troubleshooting

### Issue: Labels still overlap

**Solution 1**: Increase diagram size
```python
width=3500, height=1500
```

**Solution 2**: Increase node spacing
```python
node_pad=40  # More pixels between nodes
```

**Solution 3**: Both
```python
width=3500, height=1500, node_pad=40
```

### Issue: Nodes in wrong positions

**Cause**: Plotly's automatic algorithm makes choices you don't like

**Solution**: Add manual positions for specific nodes
```python
manual_positions = {
    'problematic_node_1': {'x': 0.2, 'y': 0.3},
    'problematic_node_2': {'x': 0.8, 'y': 0.6}
}
```

## Advantages of Simplified Approach

1. **Less code to maintain** (125 fewer lines)
2. **Leverages Plotly's optimized algorithms** (tested and well-maintained)
3. **More flexible** (Plotly handles edge cases automatically)
4. **Easier to understand** (no complex topological sorting)
5. **Better performance** (Plotly's C++ backend vs Python loops)

## Migration Guide

If you were using the old parameters:

| Old Parameter | New Parameter | Notes |
|---------------|---------------|-------|
| `node_spacing=0.1` | `node_pad=20` | Changed from 0-1 normalized to pixels |
| _(automatic)_ | `arrangement='snap'` | Now explicit in code |
| _(complex calculation)_ | _(Plotly automatic)_ | Removed custom logic |

**No changes needed for**:
- `width`, `height` - Same as before
- `manual_positions` - Same format
- `viz_config` - Same usage

## Code Structure

### Simplified Functions

1. **`_extract_manual_positions()`** - Loads positions from Excel config (simplified)
2. **`_prepare_sankey_data()`** - Prepares node/link dicts (simplified)
3. **`_create_sankey_widgets()`** - Creates UI widgets (unchanged)
4. **`_create_sankey_legend()`** - Creates legend HTML (unchanged)
5. **`plot_interactive_sankey()`** - Main plotting function (simplified)
6. **`plot_element_multiplot_sankey()`** - Multi-element plots (simplified)

### Removed Functions

- ~~`_calculate_node_positions()`~~ - Replaced by Plotly's `arrangement='snap'`

## Backup

The old version is saved as: `02_src/plotting/sankey_backup_20251110.py`

You can revert if needed:
```bash
cp 02_src/plotting/sankey_backup_20251110.py 02_src/plotting/sankey.py
```

## Example Comparison

### Old Approach (Complex)
```python
# Custom topological sorting
def _calculate_node_positions(processes, flows, manual_positions=None, node_spacing=0.1):
    # 120+ lines of complex graph algorithms
    # Kahn's algorithm
    # Layer calculation
    # Vertical distribution
    # Manual override logic
    # ... (complex code)
```

### New Approach (Simple)
```python
# Let Plotly handle it
node_dict = {
    'label': node_labels,
    'x': manual_x if has_manual else None,  # Optional
    'y': manual_y if has_manual else None,  # Optional
    'pad': node_pad  # Simple spacing parameter
}

fig = go.Sankey(arrangement='snap', node=node_dict, link=link_dict)
```

## Recommendations

1. **Start with defaults** - Try without any parameters first
2. **Adjust size if needed** - Increase `width`/`height` if labels overlap
3. **Use `node_pad`** - Increase for more spacing (try 30-50 pixels)
4. **Manual positioning last resort** - Only if automatic positioning fails

---

**Last Updated**: 2025-11-10
**Simplified By**: BioDYM Development Team
**Original Lines**: 723 → **New Lines**: 598 (17% reduction)
