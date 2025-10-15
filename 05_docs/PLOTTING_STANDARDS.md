# BioDYM Plotting Standards

This document defines the comprehensive styling standards for all BioDYM plots, ensuring consistency, professional appearance, and print-readiness across the entire framework.

## 🎨 Color Palettes

### Primary BioDYM Colors
- **Primary Blue**: `#2E86AB` - Main elements, primary flows
- **Secondary Pink**: `#A23B72` - Secondary elements, transformers
- **Accent Orange**: `#F18F01` - Highlights, important annotations
- **Success Red**: `#C73E1D` - Important flows, critical processes
- **Neutral Gray**: `#6C757D` - Neutral elements, backgrounds
- **Light Gray**: `#F8F9FA` - Plot backgrounds
- **Dark Gray**: `#212529` - Text, borders

### Element-Specific Colors
- **Material**: `#2E86AB` (Primary blue)
- **Carbon**: `#28A745` (Green)
- **Nitrogen**: `#FFC107` (Yellow)
- **Phosphorus**: `#DC3545` (Red)
- **Water**: `#17A2B8` (Cyan)
- **Energy**: `#FD7E14` (Orange)
- **WC (Water Content)**: `#28A745` (Green)
- **DM (Dry Matter)**: `#6C757D` (Gray)
- **CC (Carbon Content)**: `#FFC107` (Yellow)

### Process Type Colors
- **Splitter**: `#2E86AB` (Blue)
- **Transformer**: `#A23B72` (Pink)
- **Storage**: `#6C757D` (Gray)
- **Sink**: `#DC3545` (Red)
- **Source**: `#28A745` (Green)

### Status Colors
- **Success**: `#28A745` (Green)
- **Warning**: `#FFC107` (Yellow)
- **Error**: `#DC3545` (Red)
- **Info**: `#17A2B8` (Cyan)

## 📝 Typography

### Font Family
- **Primary**: Arial, sans-serif
- **Fallback**: System default sans-serif fonts

### Font Sizes
- **Title**: 16pt
- **Subtitle**: 14pt
- **Axis Title**: 12pt
- **Axis Labels**: 10pt
- **Legend**: 10pt
- **Annotation**: 9pt
- **Tick Labels**: 9pt

## 📐 Layout Standards

### Figure Sizes (pixels)
- **Small**: 800×600 - Small plots, thumbnails
- **Medium**: 1000×750 - Standard plots
- **Large**: 1200×900 - Large plots, detailed views
- **Wide**: 1400×700 - Dashboards, multi-panel plots
- **Tall**: 800×1200 - Vertical layouts
- **Square**: 800×800 - Balanced plots
- **Publication**: 1000×800 - Standard publication size

### Print Sizes (millimeters)
- **A4 Portrait**: 210×297mm
- **A4 Landscape**: 297×210mm
- **Letter Portrait**: 216×279mm
- **Letter Landscape**: 279×216mm

### Margins
- **Tight**: 50px all sides
- **Standard**: 80px top/bottom, 50px left/right
- **Publication**: 100px top/bottom, 50px left/right
- **Wide**: 50px left/right, 80px top/bottom

## 🔲 Grid and Background

### Grid Style
- **Color**: `#E5E5E5` (Light gray)
- **Width**: 1px
- **Style**: Dotted
- **Opacity**: 0.3

### Background Colors
- **White**: `#FFFFFF` (Default)
- **Light Gray**: `#FAFAFA` (Subtle background)
- **Transparent**: `rgba(0,0,0,0)` (No background)

## 📤 Export Settings

### High-Resolution Export
- **PNG Standard**: 1200×900px, 2x scale (150 DPI)
- **PNG Publication**: 1200×900px, 3x scale (300 DPI)
- **PNG Print**: 1200×900px, 4x scale (400 DPI)
- **PDF**: 1200×900px (Vector format)
- **SVG**: 1200×900px (Scalable vector)

### File Naming Convention
```
BioDYM_{PlotType}_{Element}_{Process}_{Timestamp}
```

Examples:
- `BioDYM_Sankey_material_20250115_143022.png`
- `BioDYM_Dynamics_carbon_20250115_143022.pdf`
- `BioDYM_MassBalance_20250115_143022.svg`

## 🛠️ Implementation Guidelines

### 1. Always Use Publication Layout
```python
from plotting import get_publication_layout, apply_publication_style

# Apply to new figures
fig.update_layout(get_publication_layout())

# Or use convenience function
fig = apply_publication_style(fig, title="My Plot")
```

### 2. Use Standardized Colors
```python
from plotting import get_element_color, get_process_color

# For elements
color = get_element_color('carbon')  # Returns #28A745

# For processes
color = get_process_color('splitter')  # Returns #2E86AB
```

### 3. Export with Publication Quality
```python
from plotting import quick_export, create_publication_export_widget

# Quick export
quick_export(fig, 'sankey', element='material')

# Interactive export widget
export_widget = create_publication_export_widget(fig, 'dynamics')
display(export_widget)
```

### 4. Batch Export Multiple Figures
```python
from plotting import PublicationExporter

exporter = PublicationExporter()
figures = {'sankey': fig1, 'dynamics': fig2, 'validation': fig3}
exporter.batch_export(figures, 'MyAnalysis')
```

## 📋 Checklist for New Plots

### Before Creating a Plot
- [ ] Import publication style functions
- [ ] Choose appropriate figure size
- [ ] Select colors from standard palettes
- [ ] Plan layout and margins

### During Plot Creation
- [ ] Apply publication layout
- [ ] Use standardized fonts and sizes
- [ ] Apply consistent grid styling
- [ ] Use appropriate color schemes
- [ ] Add proper titles and labels

### After Creating a Plot
- [ ] Test export functionality
- [ ] Verify print quality
- [ ] Check color accessibility
- [ ] Validate file naming
- [ ] Test interactive features

## 🎯 Quality Standards

### Visual Consistency
- All plots must use the same color palette
- Font sizes must be consistent across plot types
- Grid styling must be uniform
- Margins must follow standard guidelines

### Print Readability
- Minimum 300 DPI for publication
- Sufficient contrast between colors
- Readable font sizes at print scale
- Proper spacing between elements

### Accessibility
- Color-blind friendly palettes
- Sufficient contrast ratios
- Clear labels and legends
- Alternative text for complex plots

## 🔄 Migration Guide

### Updating Existing Plots
1. Import publication style functions
2. Replace custom colors with standard palettes
3. Apply publication layout
4. Update export functions
5. Test print quality

### Example Migration
```python
# Old approach
fig.update_layout(
    title="My Plot",
    font=dict(size=12),
    plot_bgcolor='white'
)

# New approach
from plotting import apply_publication_style
fig = apply_publication_style(fig, title="My Plot")
```

## 📚 References

- [Plotly Documentation](https://plotly.com/python/)
- [Matplotlib Style Guide](https://matplotlib.org/stable/tutorials/introductory/customizing.html)
- [Scientific Figure Guidelines](https://www.nature.com/articles/d41586-019-00199-6)
- [Color Accessibility Guidelines](https://webaim.org/articles/contrast/)

---

*This document is maintained as part of the BioDYM framework. Please update it when adding new plotting standards or modifying existing ones.*
