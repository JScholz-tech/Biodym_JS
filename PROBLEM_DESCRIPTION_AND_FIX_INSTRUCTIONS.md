# BioDYM Code Recovery Instructions

## Problem Summary
The BioDYM plotting system has persistent indentation errors in `src/plotting/dynamics.py` that prevent the module from importing. These errors occurred after implementing export functionality and attempting to fix widget definitions in the `plot_process_dynamics` function.

## Current Error
```
IndentationError: expected an indented block after 'if' statement on line 156
File: src/plotting/dynamics.py:157
```

## Root Cause Analysis
1. **Primary Issue**: Multiple indentation errors throughout `dynamics.py` file
2. **Secondary Issue**: Missing widget definitions in `plot_process_dynamics` function
3. **Tertiary Issue**: Incomplete export system integration

## Files Affected
- `src/plotting/dynamics.py` - Main file with indentation errors
- `src/plotting/__init__.py` - Import statements failing due to dynamics.py errors
- `src/plotting/simple_export.py` - New export system (may be incomplete)

## Recovery Strategy

### Option 1: Git Reset (Recommended)
```bash
# Reset to last working commit
git reset --hard HEAD~1
# Or reset to specific working commit
git reset --hard <commit-hash>
```

### Option 2: Manual Fix (If git reset not possible)

#### Step 1: Fix Indentation Errors
The `dynamics.py` file has multiple indentation issues. Key areas to check:

1. **Line 156-157**: Missing indentation after `if` statement
2. **Line 100-101**: Similar indentation issue in another function
3. **Widget definitions**: Missing widget creation code in `plot_process_dynamics`

#### Step 2: Restore Widget Definitions
In `plot_process_dynamics` function, add missing widget definitions before the `on_change` function:

```python
# Create enhanced widgets
process_dropdown = Dropdown(
    options=list(process_options.keys()), 
    description="Process:",
    style={'description_width': '80px'},
    layout=Layout(width='300px')
)
element_dropdown = Dropdown(
    options=element_items, 
    value=element,
    description="Element:",
    style={'description_width': '80px'},
    layout=Layout(width='200px')
)
chart_type_checkbox = Checkbox(
    value=False, 
    description="Show as Bar Chart",
    style={'description_width': '120px'}
)
```

#### Step 3: Fix Export Integration
Ensure `create_export_button` is properly imported and used:

```python
from .simple_export import create_export_button
```

## Specific Fix Instructions

### For Line 156-157 Error:
```python
# BEFORE (broken):
if show_as_bars:
fig.add_trace(

# AFTER (fixed):
if show_as_bars:
    fig.add_trace(
```

### For Line 100-101 Error:
```python
# BEFORE (broken):
if show_as_bars:
fig.add_trace(

# AFTER (fixed):
if show_as_bars:
    fig.add_trace(
```

### For Missing Widget Definitions:
Add this code block before the `on_change` function definition in `plot_process_dynamics`:

```python
# Create enhanced widgets
process_dropdown = Dropdown(
    options=list(process_options.keys()), 
    description="Process:",
    style={'description_width': '80px'},
    layout=Layout(width='300px')
)
element_dropdown = Dropdown(
    options=element_items, 
    value=element,
    description="Element:",
    style={'description_width': '80px'},
    layout=Layout(width='200px')
)
chart_type_checkbox = Checkbox(
    value=False, 
    description="Show as Bar Chart",
    style={'description_width': '120px'}
)

# Create export button using simple export system
export_button = create_export_button(
    fig, 
    plot_type='process_dynamics',
    element=element_dropdown.value,
    process=process_dropdown.value,
    additional_params={}
)

# Create widget layout
controls = HBox([
    VBox([process_dropdown, element_dropdown], layout=Layout(width='300px')),
    VBox([chart_type_checkbox, export_button], layout=Layout(width='200px'))
], layout=Layout(justify_content='space-between'))
```

## Testing Instructions

### Step 1: Test Import
```python
import sys
sys.path.insert(0, 'src')
import plotting
```

### Step 2: Test Function Availability
```python
print('plot_process_dynamics available:', hasattr(plotting, 'plot_process_dynamics'))
print('plot_flow_dynamics available:', hasattr(plotting, 'plot_flow_dynamics'))
```

### Step 3: Test Function Execution
```python
# Test with sample data
plotting.plot_process_dynamics(mfa_results_baseline, process_definitions)
```

## Required Imports
Ensure these imports are present in `dynamics.py`:

```python
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ipywidgets import Dropdown, Checkbox, HBox, VBox, Layout, interact, display
from .publication_style import get_publication_layout, get_element_color, BIOYM_COLORS
from .simple_export import create_export_button
```

## Success Criteria
1. `import plotting` executes without errors
2. All plotting functions are available and callable
3. Widgets display correctly in Jupyter notebook
4. Export buttons function properly

## Fallback Plan
If manual fixes fail:
1. Restore from git backup
2. Re-implement export system more carefully
3. Test each function individually before integration

## Notes
- The export system implementation was the trigger for these errors
- Focus on fixing indentation first, then widget definitions
- Test incrementally to avoid cascading errors
- Consider using a Python linter/formatter to catch indentation issues

## Files to Backup Before Fixing
- `src/plotting/dynamics.py`
- `src/plotting/__init__.py`
- `src/plotting/simple_export.py`

This document provides a complete recovery plan for the BioDYM plotting system issues.
