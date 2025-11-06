# BioDYM Visualization System Overview

**Date**: 2025-10-31
**Status**: Production-ready for 2D arrays (time × elements)

---

## Overview

BioDYM includes a comprehensive visualization system with **20+ plotting functions** across 7 categories:
- Sankey diagrams (flow visualization)
- Time-series dynamics (stocks, flows, processes)
- Validation plots (mass balance checks)
- Monte Carlo uncertainty analysis
- Scenario comparisons
- Composition analysis
- System structure (Graphviz diagrams)

---

## Visualization Categories

### 1. Sankey Diagrams 🌊

**Purpose**: Visualize material flows through the system

**Modules**:
- `sankey.py` - Traditional Sankey diagrams (2200×350 wide format)
- `enhanced_sankey.py` - Custom layouts and advanced features
- `enhanced_sankey.py` - Element multiplot Sankey (NEW - 2025-10-31)

**Key Functions**:
```python
# Traditional wide Sankey (horizontal elongated)
plot_interactive_sankey(mfa_system, element='material', year=0)

# Enhanced Sankey with Excel configuration
plot_enhanced_sankey(mfa_system, visualization_config_path='file.xlsx')

# NEW: Element multiplot - vertically stacked elements
plot_element_multiplot_sankey(
    mfa_system,
    visualization_config_path='file.xlsx',
    elements_to_plot=['material', 'WC', 'DM', 'CC'],
    subplot_height=350
)
```

**Features**:
- Interactive (hover for values, click to filter)
- Multi-element support (material, WC, DM, CC)
- Time-series animation
- Custom color schemes
- Excel-based layout configuration
- **NEW**: Multiplot mode shows all elements stacked vertically
- **NEW**: Very wide format (2200×350) for horizontal flow visualization

**Element Compatibility**: ✅ **Fully compatible with E# system**
- Dynamically uses `mfa_system.Elements` from config
- No hardcoded element names

**Recent Updates (2025-10-31)**:
- ✅ Traditional Sankey now 2200×350 pixels (very wide, horizontal)
- ✅ Added `plot_element_multiplot_sankey()` function
- ✅ Multiplot shows multi-level element hierarchy
- ✅ Single time slider controls all subplots (dynamic evolution)

---

### 2. Time-Series Dynamics 📊

**Purpose**: Track changes over time for stocks, flows, and processes

**Module**: `dynamics.py` (67 KB - largest module)

**Key Functions**:
```python
# Process dynamics
plot_process_dynamics(mfa_system, process_id, elements=['material'])

# Flow dynamics
plot_flow_dynamics(mfa_system, flow_ids, elements=['material'])

# Stock dynamics
plot_stock_overview(mfa_system)
plot_dsm_process_dynamics(mfa_system, dsm_details, process_id)
plot_fomp_dynamics(mfa_system, fomp_details, process_id)

# System-level
plot_system_efficiency_metrics(mfa_system)
plot_dynamic_stock_composition(mfa_system)
```

**Features**:
- Multiple element tracking on same plot
- Stacked area charts for composition
- Line plots for individual flows/stocks
- Process-specific DSM and FOMP visualizations
- System-wide efficiency metrics

**Element Compatibility**: ⚠️ **Needs 3D array update**
- Currently assumes 2D: `flow.Values[:, element_index]`
- Works perfectly for current 2D system (time × elements)
- Will need update when Materials dimension added (see below)

---

### 3. Mass Balance Validation ✅

**Purpose**: Verify mass balance accuracy for each process

**Module**: `validation.py`

**Key Functions**:
```python
plot_total_mass_balance_error(mfa_system)
plot_optimized_mass_balance_error(mfa_system)
```

**Features**:
- Per-process error visualization
- Per-element error tracking
- Acceptable error thresholds (< 1e-10 Mg)
- Color-coded warnings (green/yellow/red)
- Detailed error breakdowns

**Element Compatibility**: ✅ **Compatible** (uses element loop)

---

### 4. Monte Carlo Uncertainty Analysis 🎲

**Purpose**: Visualize uncertainty propagation and sensitivity

**Module**: `monte_carlo.py` (30 KB)

**Key Functions**:
```python
# Uncertainty distributions
plot_interactive_mc_histogram(mc_results, flow_id, element='material')
plot_interactive_mc_multiple_histograms(mc_results, flow_ids)

# Sensitivity analysis
plot_interactive_tornado(mc_results, flow_id, element='material')

# Time-series with uncertainty bands
plot_interactive_mc_paths(mc_results, flow_id, element='material')

# Stock comparisons
plot_interactive_mc_stock_comparison(mc_results, stock_ids)
```

**Features**:
- Histograms with percentiles (5%, 25%, 50%, 75%, 95%)
- Tornado diagrams for sensitivity ranking
- Uncertainty bands on time-series
- Multiple realizations visualization
- Comparative analysis across scenarios

**Element Compatibility**: ✅ **Compatible** (element passed as parameter)

---

### 5. Scenario Comparison 🔄

**Purpose**: Compare multiple scenarios side-by-side

**Module**: `scenario.py` (21 KB)

**Key Functions**:
```python
# Multi-scenario comparison
plot_multi_scenario_comparison(scenarios_dict, item='flow', item_id='F_01')

# Scenario flow dynamics
plot_scenario_flow_dynamics(scenarios_dict, flow_id, elements=['material'])

# Scenario stock dynamics
plot_scenario_stock_dynamics(scenarios_dict, stock_id, elements=['material'])
```

**Features**:
- Side-by-side bar charts
- Stacked comparisons
- Difference highlighting
- Time-series comparison
- Percentage change calculations

**Element Compatibility**: ⚠️ **Needs 3D array update** (same as dynamics.py)

---

### 6. Composition Analysis 🔬

**Purpose**: Analyze elemental composition of flows

**Module**: `composition.py`

**Key Functions**:
```python
plot_flow_composition(mfa_system, flow_id)
```

**Features**:
- Stacked area charts showing WC/DM/CC breakdown
- Percentage composition over time
- Total mass overlay
- Element fractions

**Element Compatibility**: ✅ **Already updated for 3D arrays!**

---

### 7. System Structure Diagrams 🗺️

**Purpose**: Visualize system structure with processes and flows

**Module**: `graphviz_flow_charts.py`

**Key Functions**:
```python
plot_graphviz_flow_chart_sankey_style(processes_df, flows_df)
```

**Features**:
- Node-and-edge diagrams
- Process types color-coded
- Flow weights shown
- Hierarchical layout
- Export to PNG/SVG

**Current Limits**:
- Max 50 processes (was 20, increased 2025-10-30)
- Max 100 flows (was 30, increased 2025-10-30)

**Element Compatibility**: ✅ **Element-agnostic** (structural view only)

---

## Publication-Quality Styling 📐

### Publication Style System

**Modules**:
- `publication_style.py` (22 KB) - Full styling system
- `publication_style_simplified.py` (15 KB) - Simplified version
- `publication_export.py` (20 KB) - Export utilities

**Features**:
```python
from plotting.publication_style import (
    get_publication_theme,
    format_axis_scientific,
    add_publication_legend,
    apply_grid_style
)

# Apply to Plotly figure
fig = get_publication_theme()
fig = format_axis_scientific(fig, x_format='year', y_format='mass')
```

**Styling Options**:
- DPI settings (300+ for print)
- Color-blind friendly palettes
- Consistent fonts (Arial, Times New Roman)
- Scientific notation formatting
- Legend positioning
- Grid styles

**Element Compatibility**: ✅ **Element-agnostic** (styling only)

---

## Element System Integration Status

### ✅ **Fully Compatible**

These modules work seamlessly with the new E# element system:
- ✅ `sankey.py` - Uses `mfa_system.Elements` dynamically
- ✅ `validation.py` - Loops over elements from system
- ✅ `monte_carlo.py` - Element passed as parameter
- ✅ `composition.py` - Already updated for flexibility
- ✅ `graphviz_flow_charts.py` - Element-agnostic (structural)
- ✅ `publication_style.py` - Styling only

### ⚠️ **Needs 3D Array Update**

These modules need updates when Materials dimension is added:
- ⚠️ `dynamics.py` - Uses `flow.Values[:, element_index]`
- ⚠️ `scenario.py` - Uses `flow.Values[:, element_index]`

**Current Status**: Works perfectly for 2D arrays (time × elements)

**When to Update**: When adding Materials dimension (creates 3D arrays: time × materials × elements)

**How to Update**: Use helper function from `utils_3d.py`:
```python
from plotting.utils_3d import get_element_values

# OLD: flow.Values[:, element_index]
# NEW: get_element_values(flow, element_index)
```

See `UPDATE_FOR_3D_NEEDED.md` for complete update plan.

---

## Known Issues & Improvements

### Issue 1: 3D Array Support ⚠️

**Status**: Documented in `UPDATE_FOR_3D_NEEDED.md`

**Impact**: Will cause errors when Materials dimension is added

**Solution**: Use `utils_3d.get_element_values()` helper function

**Effort**: 2-3 hours to update all locations

**Priority**: **Low** (only needed when adding Materials dimension)

---

### Issue 2: Sankey Layout Optimization

**Status**: Manual layout via Excel `6_3_Layout_Configuration` sheet

**Potential Improvement**:
- Automatic layout optimization algorithm
- AI-based node positioning
- Minimize edge crossings
- Hierarchical clustering

**Effort**: 1-2 weeks

**Priority**: **Medium** (nice-to-have for complex systems)

---

### Issue 3: Publication Style Consistency

**Status**: `publication_style.py` exists but not consistently used

**Current State** (from Pre-Publication Checklist):
- [ ] Audit all plotting modules for `publication_style.py` usage
- [ ] Ensure color-blind friendly palettes
- [ ] Verify DPI ≥ 300 for print quality

**Effort**: 3-4 hours to audit and update all modules

**Priority**: **Medium** (important for publication)

---

## Usage Examples

### Example 1: Basic Flow Visualization

```python
import plotting

# Sankey diagram
plotting.plot_interactive_sankey(
    mfa_results_baseline,
    element='material',
    year=0,
    title='Biomass Flow Network'
)

# Time-series
plotting.plot_flow_dynamics(
    mfa_results_baseline,
    flow_ids=['F_01_02', 'F_02_03'],
    elements=['material', 'CC']
)
```

### Example 2: Validation Checks

```python
# Mass balance validation
plotting.plot_optimized_mass_balance_error(mfa_results_baseline)

# Should show all green (errors < 1e-10)
```

### Example 3: Monte Carlo Analysis

```python
# Run Monte Carlo
mc_results = solver.run_monte_carlo_simulation(
    mfa_system, dsm_params, fomp_params, config,
    iterations=1000
)

# Visualize uncertainty
plotting.plot_interactive_mc_histogram(
    mc_results,
    flow_id='F_01_02',
    element='material'
)

plotting.plot_interactive_tornado(
    mc_results,
    flow_id='F_01_02',
    element='material'
)
```

### Example 4: Scenario Comparison

```python
# Compare scenarios
scenarios = {
    'baseline': mfa_results_baseline,
    'optimized': mfa_results_optimized,
    'pessimistic': mfa_results_pessimistic
}

plotting.plot_multi_scenario_comparison(
    scenarios,
    item='flow',
    item_id='F_01_02',
    element='material'
)
```

---

## Best Practices

### 1. Element Selection

**For overview plots**: Use `'material'` element
```python
plot_interactive_sankey(mfa_system, element='material')
```

**For detailed analysis**: Use specific elements
```python
plot_flow_dynamics(mfa_system, flow_ids, elements=['WC', 'DM', 'CC'])
```

### 2. Performance

**Large systems** (50+ processes, 100+ flows):
- Use Sankey diagram for overview (handles up to 50 processes)
- Use specific flow/process plots for details
- Consider filtering to top N flows by magnitude

**Monte Carlo** (1000+ iterations):
- Use sampling for histograms (plot every 10th iteration)
- Cache results for multiple plots
- Use simplified plots for quick checks

### 3. Publication Quality

**For papers/reports**:
```python
from plotting.publication_style import get_publication_theme
from plotting.publication_export import export_publication_figure

fig = get_publication_theme()
# ... create your plot ...
export_publication_figure(fig, 'my_figure', dpi=300, format='pdf')
```

---

## Recommendations

### ✅ **Ready to Use Now**

All visualization modules work perfectly with the new element system for 2D arrays (time × elements).

### 📋 **Pre-Publication Tasks** (Priority 3 from checklist)

1. **Unified Figure Styling** (3-4 hours)
   - Audit all modules for `publication_style.py` usage
   - Ensure consistent color schemes
   - Verify DPI ≥ 300 for exports

2. **Sankey Layout Testing** (1-2 hours)
   - Test with complex systems (20+ processes, 50+ flows)
   - Document layout best practices
   - Create example configurations

### 🔮 **Future Enhancements** (Post-Publication)

1. **3D Array Support** (2-3 hours)
   - Update `dynamics.py` and `scenario.py`
   - Use `utils_3d.get_element_values()` helper
   - Test with Materials dimension

2. **Interactive Dashboard** (1-2 weeks)
   - Combine multiple plots in single view
   - Dash or Streamlit app
   - Real-time filtering and exploration

3. **Automatic Layout Optimization** (1-2 weeks)
   - AI-based Sankey node positioning
   - Minimize edge crossings
   - Hierarchical clustering

---

## Summary

✅ **Visualization system is production-ready**

- 20+ plotting functions across 7 categories
- Fully compatible with new E# element system
- Works perfectly for current 2D structure (time × elements)
- Publication-quality styling system available
- Comprehensive coverage (flows, stocks, validation, uncertainty, scenarios)

⚠️ **Known limitation**: 3D array support needed when Materials dimension is added (documented with solution in `UPDATE_FOR_3D_NEEDED.md`)

📋 **Pre-publication tasks**: Styling consistency audit (Priority 3, 3-4 hours)

The visualization system is one of BioDYM's strongest features - comprehensive, interactive, and scientifically rigorous! 🎨

---

**Last Updated**: 2025-10-31
**Status**: ✅ Production-ready for 2D arrays
**Next Steps**: Styling consistency audit (Pre-Publication Priority 3)
