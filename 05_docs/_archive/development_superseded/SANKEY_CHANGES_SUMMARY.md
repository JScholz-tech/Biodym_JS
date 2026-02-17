# Sankey Module Changes Summary - 2025-11-11

## Overview
Major improvements to the Sankey diagram module for better readability, flexibility, and user control.

## Key Changes

### 1. ✅ Removed Plotly 'snap' Constraint
- **Before**: `arrangement='snap'` restricted node positioning to grid-like structure
- **After**: No arrangement constraint - Plotly has maximum flexibility for positioning
- **Benefit**: More natural flow layouts, especially for complex diagrams

### 2. ✅ Added Flow Filtering Feature
- **New**: Users can now filter by flows in addition to processes
- **UI**: New `flow_selector` widget (SelectMultiple)
- **Benefit**: Fine-grained control over which flows are displayed

### 3. ✅ Centralized Configuration (`sankey_config.py`)
- **New file**: `02_src/plotting/sankey_config.py`
- **Settings**:
  - `WINDOW_WIDTH = 3500` (increased from 2000)
  - `WINDOW_HEIGHT = 1500` (increased from 1000)
  - `NODE_SPACING = 30` (clearer: pixels instead of 0.1)
  - `NODE_SCALE_FACTOR = 1.5` (reduced from 4)
  - `PADDING_FACTOR = 0.02` (reduced from 1 - now 2% of dimensions)
- **Benefit**: Easy to adjust defaults without modifying code

### 4. ✅ Node Scale Factor Parameter
- **New**: `node_scale_factor` parameter in plotting functions
- **Usage**: Node thickness = `20 * node_scale_factor`
- **Benefit**: Dynamic control over node sizes

### 5. ✅ Improved Layout Management
- **Margins**: Now calculated as `width/height * PADDING_FACTOR`
- **Background**: Configurable via `sankey_config.BACKGROUND_COLOR`
- **Benefit**: Consistent, proportional margins across different diagram sizes

### 6. ✅ Better Control Panel Layout
- **Structure**: Matches `enhanced_sankey.py` for consistency
- **Display**: `VBox([controls, figure])` - better ratio of controls to diagram
- **Benefit**: Controls don't dominate the screen anymore

## Files Changed

### Modified
- `02_src/plotting/sankey.py` - Main sankey module with all improvements

### New Files
- `02_src/plotting/sankey_config.py` - Centralized configuration
- `SANKEY_CONFIG_RECOMMENDATIONS.md` - Configuration guide
- `test_sankey_simplified.py` - Test script for verification

### Backup Files (Not Committed)
- `02_src/plotting/sankey_backup_20251110.py` - Original version (723 lines)
- `02_src/plotting/sankey_conflict_backup.py` - Conflict resolution backup

## Function Signature Changes

### Before
```python
def plot_interactive_sankey(
    mfa_system_results,
    dsm_params=None,
    fomp_params=None,
    color_manager=None,
    width=5000,
    height=2000,
    node_pad=30
)
```

### After
```python
def plot_interactive_sankey(
    mfa_system_results,
    dsm_params=None,
    fomp_params=None,
    color_manager=None,
    width=sankey_config.WINDOW_WIDTH,        # 3500
    height=sankey_config.WINDOW_HEIGHT,      # 1500
    node_pad=sankey_config.NODE_SPACING,     # 30
    node_scale_factor=sankey_config.NODE_SCALE_FACTOR,  # 1.5 (NEW)
)
```

## Widget Changes

### Before (4 widgets)
```python
year_slider, element_dropdown, process_selector, threshold_slider
```

### After (5 widgets)
```python
year_slider, element_dropdown, process_selector, flow_selector, threshold_slider
```

## UI Layout Changes

### Before
```python
display(ui)
display(fig)
```

### After
```python
display(VBox([ui, fig]))  # Controls and figure in single container
```

## Testing

```bash
cd 02_src
python -c "from plotting import sankey; print('Import OK')"
# Output: Import OK

python test_sankey_simplified.py
# Output: All basic checks passed!
```

## Configuration Recommendations

See `SANKEY_CONFIG_RECOMMENDATIONS.md` for:
- Detailed rationale for each setting
- Alternative configuration profiles (Compact, Large, Enhanced Style)
- Comparison with enhanced_sankey defaults

## Breaking Changes

⚠️ **None** - All changes are backwards compatible. Existing code will continue to work with sensible defaults from `sankey_config.py`.

## Next Steps

1. Test with actual MFA data in `00_BioDYM_Workflow.ipynb`
2. Verify label readability at 3500×1500
3. Consider adding configuration profiles (compact/large/publication)
4. Update documentation for new flow filtering feature

---

**Date**: 2025-11-11
**Changes By**: Claude Code + User
**Status**: ✅ Ready for commit
