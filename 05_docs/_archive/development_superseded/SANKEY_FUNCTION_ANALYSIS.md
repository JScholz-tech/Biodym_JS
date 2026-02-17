# Sankey.py Function Analysis

## Current Functions (6 total)

### 1. `_extract_manual_positions(viz_config, element, process_ids)`
**Purpose**: Loads manual X/Y positions from Excel configuration
**Lines**: ~70 lines
**Needed?**: ✅ YES - Required to read positions from Excel
**Issues**: None
**Simplification**: Could be slightly shorter but it's fine

---

### 2. `_prepare_sankey_data(filtered_processes, flows_data, ...)`
**Purpose**: Prepares node and link dictionaries for Plotly
**Lines**: ~110 lines
**Needed?**: ✅ YES - Core data preparation
**Issues**:
- **🔴 MAJOR BUG**: Lines 186-189 restrict free positioning
  ```python
  if has_manual_x:
      node_dict['x'] = node_x  # Only adds X
  if has_manual_y:
      node_dict['y'] = node_y  # Only adds Y
  ```
  **Problem**: Plotly needs BOTH x AND y for free positioning!
  If you only provide X, nodes are locked to vertical lines.

**Fix**: Always provide BOTH x and y if ANY manual position exists

---

### 3. `_create_sankey_widgets(all_process_names, time_items, ...)`
**Purpose**: Creates UI widgets (sliders, dropdowns, selectors)
**Lines**: ~40 lines
**Needed?**: ✅ YES - Required for interactive filtering
**Issues**: None
**Simplification**: None needed

---

### 4. `_create_sankey_legend(element_items, color_manager)`
**Purpose**: Generates HTML legend showing color codes
**Lines**: ~50 lines (mostly HTML strings)
**Needed?**: ⚠️ DEBATABLE
- Adds visual clarity for users
- But takes up screen space
- Could be optional parameter
**Simplification**: Could make legend optional (default: True)

---

### 5. `plot_interactive_sankey(...)`
**Purpose**: Main function - creates interactive Sankey diagram
**Lines**: ~140 lines
**Needed?**: ✅ YES - Core functionality
**Issues**:
- **🔴 Default size still small**: `width=2200, height=800`
- Should be `width=3000, height=1200` for readable labels
**Simplification**: None - this is the main interface

---

### 6. `plot_element_multiplot_sankey(...)`
**Purpose**: Creates multiple Sankey diagrams (one per element)
**Lines**: ~145 lines
**Needed?**: ✅ YES - Useful for comparing elements
**Issues**: Same size issue
**Simplification**: None - separate use case

---

## Key Issues to Fix

### 1. 🔴 **CRITICAL: Manual positioning limitation** (Lines 186-189)
**Current code:**
```python
if has_manual_x:
    node_dict['x'] = node_x
if has_manual_y:
    node_dict['y'] = node_y
```

**Problem**: This restricts nodes to vertical/horizontal lines!

**Solution**: Always provide BOTH if ANY manual position exists:
```python
if has_manual_x or has_manual_y:
    node_dict['x'] = node_x
    node_dict['y'] = node_y
```

### 2. 🟡 **Default sizes too small**
Change defaults:
- `width=2200` → `width=3000`
- `height=800` → `height=1200`

---

## Recommended Changes

### Priority 1: Fix Manual Positioning (Critical)
```python
# OLD (Lines 186-189):
if has_manual_x:
    node_dict['x'] = node_x
if has_manual_y:
    node_dict['y'] = node_y

# NEW:
if has_manual_x or has_manual_y:
    node_dict['x'] = node_x
    node_dict['y'] = node_y
```

### Priority 2: Increase Default Sizes
```python
# Function signatures
def plot_interactive_sankey(
    ...,
    width=3000,      # OLD: 2200
    height=1200,     # OLD: 800
    ...
)

def plot_element_multiplot_sankey(
    ...,
    subplot_width=3000,   # OLD: 2200
    subplot_height=500,   # OLD: 350
    ...
)
```

### Priority 3 (Optional): Make Legend Optional
```python
def plot_interactive_sankey(
    ...,
    show_legend=True,  # NEW parameter
    ...
)
```

---

## Total Line Count: 599 lines

### Breakdown:
- `_extract_manual_positions`: ~70 lines (12%)
- `_prepare_sankey_data`: ~110 lines (18%)
- `_create_sankey_widgets`: ~40 lines (7%)
- `_create_sankey_legend`: ~50 lines (8%)
- `plot_interactive_sankey`: ~140 lines (23%)
- `plot_element_multiplot_sankey`: ~145 lines (24%)
- Docstrings/imports: ~44 lines (8%)

### Can We Simplify Further?
Not really! Each function serves a clear purpose:
1. Load positions from Excel ✅
2. Prepare data for Plotly ✅
3. Create UI widgets ✅
4. Create legend ✅ (optional)
5. Main plotting function ✅
6. Multi-element variant ✅

The code is already quite streamlined after removing the 120-line topological sorting algorithm.

---

## Comparison to Plotly Examples

The Plotly documentation shows minimal examples (20-30 lines), but those don't include:
- ❌ Interactive widgets (year/element/process filtering)
- ❌ Excel configuration loading
- ❌ Element-agnostic coloring
- ❌ Legend generation
- ❌ DSM/FOMP/Stock detection and coloring
- ❌ Multiple layout options

Our 600 lines provide a **complete interactive MFA visualization system**, not just a basic Sankey diagram.

---

**Date**: 2025-11-10
**Analysis by**: BioDYM Development Team
