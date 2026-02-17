# BioDYM Visualization System Improvements

**Date**: 2025-11-04
**Status**: In Progress - Validation Plots Complete

## 🎯 Overview

We're implementing a comprehensive visualization system upgrade to make BioDYM plots:
1. **Element-agnostic** - Works with ANY element set (not just material/WC/DM/CC)
2. **Color-blind friendly** - Accessible color schemes available
3. **Publication-ready** - Professional export with proper DPI/sizing
4. **Standardized** - Consistent styling across all plots

## ✅ Completed: Validation Plots (Priority 1)

### Files Created

#### 1. `02_src/plotting/dynamic_colors.py` - Element-Agnostic Color System

**Purpose**: Automatically assigns colors to ANY element configuration

**Key Features**:
- Works with unlimited elements (not just 4)
- Three color schemes:
  - `'default'` - Bright, distinct colors
  - `'colorblind'` - Accessible (Okabe-Ito palette, works for all color blindness types)
  - `'grayscale'` - Black & white printing
- Automatic color generation for unlimited elements
- Separate colors for flows vs stocks
- Element hierarchy support

**Usage**:
```python
from plotting.dynamic_colors import ElementColorManager

# Create color manager for any element set
elements = ['material', 'protein', 'lipids', 'carbohydrates']
color_manager = ElementColorManager(elements, color_scheme='default')

# Get color for specific element
protein_color = color_manager.get_element_color('protein')

# Switch to color-blind friendly
color_manager.set_color_scheme('colorblind')

# Get all colors as dictionary
all_colors = color_manager.get_all_element_colors()
```

#### 2. `02_src/plotting/export_publication.py` - Professional Export System

**Purpose**: THE unified export command for publication-quality figures

**Key Features**:
- Multiple formats: PNG, PDF, SVG, EPS, HTML
- Proper DPI: 300 (print) or 400 (publication)
- Smart sizing: single-column, double-column, full-page, slide, custom
- Automatic timestamping
- Batch export capability

**THE Good Printing Command You Asked For**:
```python
from plotting.export_publication import export_figure, export_for_paper

# Simple publication export (PNG + timestamp, 400 DPI)
export_figure(fig, 'my_sankey')

# For scientific paper (PNG + PDF, perfect sizing)
export_for_paper(fig, 'figure1', size='double_column')

# Multiple formats at once
export_figure(fig, 'results', formats=['png', 'pdf', 'svg', 'html'])

# Custom DPI and size
export_figure(fig, 'poster', dpi=600, size=(12, 9))

# Disable timestamp
export_figure(fig, 'final_version', timestamp=False)
```

**Export Presets**:
- `export_for_paper()` - PNG + PDF, publication quality
- `export_for_presentation()` - PNG + HTML, web quality
- `batch_export_figures()` - Export multiple figures at once

### Files Updated

#### 3. `02_src/plotting/validation.py` - Mass Balance Plots

**Changes**:
- ✅ Now element-agnostic (works with ANY element set)
- ✅ Dynamic color assignment
- ✅ Color-blind friendly option
- ✅ Built-in export button
- ✅ Standardized styling
- ✅ Better legend placement
- ✅ Professional grid/fonts

**Updated Functions**:

##### `plot_optimized_mass_balance_error()`
```python
# OLD (still works - backward compatible):
plotting.plot_optimized_mass_balance_error(mfa_results)

# NEW - With color-blind friendly colors:
color_mgr = ElementColorManager(elements, color_scheme='colorblind')
plotting.plot_optimized_mass_balance_error(mfa_results, color_manager=color_mgr)

# NEW - Disable auto-export:
plotting.plot_optimized_mass_balance_error(mfa_results, enable_export=False)
```

**New Features**:
- 📥 Export button in widget panel (exports current view to PNG + PDF)
- Automatic element color detection
- Works with any element configuration
- Better organized control panel

##### `plot_total_mass_balance_error()`
```python
# OLD (still works - backward compatible):
plotting.plot_total_mass_balance_error(mfa_results)

# NEW - Custom export filename:
fig = plotting.plot_total_mass_balance_error(mfa_results,
                                               export_filename="baseline_validation")

# NEW - Disable auto-export:
fig = plotting.plot_total_mass_balance_error(mfa_results, enable_export=False)

# NEW - Get figure for manual export:
fig = plotting.plot_total_mass_balance_error(mfa_results)
export_figure(fig, 'custom_name', formats=['png', 'svg'], dpi=600)
```

**New Features**:
- Automatic export to PNG + PDF after display
- Returns Plotly figure object for further customization
- Better legend formatting
- Element-agnostic coloring

## 📊 How to Use in Your Workflow

### Basic Usage (No Changes Needed!)

Your existing code still works:
```python
# This still works exactly as before:
plotting.plot_total_mass_balance_error(mfa_results_baseline)
plotting.plot_optimized_mass_balance_error(mfa_results_baseline)
```

### Advanced Usage (New Features)

#### 1. Use Color-Blind Friendly Colors Globally

At the start of your workflow:
```python
from plotting.dynamic_colors import ElementColorManager, set_global_color_manager

# Create color manager with color-blind friendly scheme
elements = [e.lower() for e in config['Elements'].split(',')]
color_manager = ElementColorManager(elements, color_scheme='colorblind')

# Set as global (all plots will use this)
set_global_color_manager(color_manager)

# Now all plots automatically use color-blind friendly colors
plotting.plot_total_mass_balance_error(mfa_results)
```

#### 2. Custom Export Settings

```python
# Disable auto-export, export manually with custom settings
fig = plotting.plot_total_mass_balance_error(mfa_results, enable_export=False)

# Custom export
from plotting.export_publication import export_figure
export_figure(fig, 'fig1_validation',
              formats=['png', 'pdf', 'eps'],
              dpi=600,
              size='single_column',
              timestamp=False)
```

#### 3. Compare Color Schemes

```python
from plotting.dynamic_colors import ElementColorManager

# Create managers with different schemes
default_mgr = ElementColorManager(elements, color_scheme='default')
colorblind_mgr = ElementColorManager(elements, color_scheme='colorblind')
grayscale_mgr = ElementColorManager(elements, color_scheme='grayscale')

# Use different schemes for different plots
plotting.plot_total_mass_balance_error(mfa_results, color_manager=default_mgr)
plotting.plot_total_mass_balance_error(mfa_results, color_manager=colorblind_mgr)
```

## 🔄 Migration Guide

### If You Have Custom Element Sets

**Before** (Hard-coded, only worked with material/WC/DM/CC):
```python
# Would fail with custom elements like protein, lipids, etc.
```

**After** (Works with ANY elements):
```python
# Automatically works with ANY element configuration
# Example: elements = ['material', 'protein', 'lipids', 'carbs', 'fiber']
plotting.plot_total_mass_balance_error(mfa_results)
# Colors automatically assigned!
```

### If You Need Color-Blind Accessibility

**Before**:
```python
# Had to manually edit color codes in source files
```

**After**:
```python
color_mgr = ElementColorManager(elements, color_scheme='colorblind')
plotting.plot_total_mass_balance_error(mfa_results, color_manager=color_mgr)
```

## 📝 Next Steps (Planned)

Following the order in `00_BioDYM_Workflow.ipynb`:

1. ✅ **Validation plots** (COMPLETE)
   - `plot_total_mass_balance_error()`
   - `plot_optimized_mass_balance_error()`

2. ⏳ **Dynamics plots** (NEXT)
   - `plot_process_dynamics()`
   - `plot_stock_dynamics()`
   - `plot_flow_dynamics()`

3. ⏳ **Sankey diagrams**
   - `create_sankey_diagram()`
   - `create_enhanced_sankey_diagram()`

4. ⏳ **Remaining plots**
   - Monte Carlo visualizations
   - Scenario comparisons
   - Flow composition
   - System structure diagrams

## 🎨 Color Scheme Comparison

### Default Scheme (Bright & Distinct)
- Material: `#00C851` (Bright Green)
- WC: `#007BFF` (Bright Blue)
- DM: `#FF8C00` (Bright Orange)
- CC: `#FF4444` (Bright Red)

### Color-Blind Friendly Scheme (Okabe-Ito)
- Material: `#0173B2` (Blue) - replaces green
- WC: `#56B4E9` (Sky Blue)
- DM: `#E69F00` (Orange)
- CC: `#CC79A7` (Pink) - replaces red

**Why?** Red-green color blindness affects ~5% of males. The new scheme is distinguishable for all types of color blindness.

### Grayscale Scheme (B&W Printing)
- Material: `#2C2C2C` (Very dark gray)
- WC: `#5C5C5C` (Dark gray)
- DM: `#8C8C8C` (Medium gray)
- CC: `#BCBCBC` (Light gray)

## 📖 Documentation

- **CLAUDE.md** - Updated with new module references
- **TROUBLESHOOTING.md** - Common visualization issues
- **This file** - Complete feature documentation

## 🐛 Testing

### Test with Your Current System

```python
# Run these in your workflow notebook:

# Test 1: Basic functionality
plotting.plot_total_mass_balance_error(mfa_results_baseline)

# Test 2: Export button
plotting.plot_optimized_mass_balance_error(mfa_results_baseline)
# Click the "📥 Export Figure" button

# Test 3: Color-blind mode
from plotting.dynamic_colors import ElementColorManager
color_mgr = ElementColorManager(['material', 'wc', 'dm', 'cc'],
                                color_scheme='colorblind')
plotting.plot_total_mass_balance_error(mfa_results_baseline,
                                        color_manager=color_mgr)
```

### Test with Custom Elements

```python
# If you have a system with custom elements:
# Example: Food system with protein, lipids, carbs
elements = ['material', 'protein', 'lipids', 'carbohydrates', 'fiber']
color_mgr = ElementColorManager(elements)

# Colors automatically assigned!
all_colors = color_mgr.get_all_element_colors()
print(all_colors)
# {'material': '#00C851', 'protein': '#007BFF', 'lipids': '#FF8C00', ...}
```

## 📦 Exported Files

When you use the export functionality, files are saved to:
```
01_data/02_output/figures/
```

File naming convention:
```
{filename}_{timestamp}.{format}

Examples:
mass_balance_total_20251104_143022.png
mass_balance_total_20251104_143022.pdf
mass_balance_error_material_2020_20251104_143045.png
```

## ❓ FAQ

**Q: Do I need to change my existing code?**
A: No! All functions are backward compatible. New features are optional.

**Q: How do I disable auto-export?**
A: Pass `enable_export=False` to the plotting function.

**Q: Can I use different color schemes for different plots?**
A: Yes! Create separate `ElementColorManager` instances with different schemes.

**Q: What if I have more than 8 elements?**
A: Colors are automatically generated for unlimited elements.

**Q: How do I export to EPS for LaTeX?**
A: `export_figure(fig, 'name', formats=['eps'])` (requires ghostscript)

**Q: Can I customize the export directory?**
A: Yes! `export_figure(fig, 'name', output_dir='my/custom/path')`

---

**Last Updated**: 2025-11-04
**Version**: 1.0 (Validation Plots Complete)
**Next Update**: After dynamics plots implementation
