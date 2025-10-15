# BioDYM Color System Documentation

This document explains the comprehensive color system designed specifically for BioDYM's Material Flow Analysis (MFA) framework.

## 🎯 **Design Principles**

The color system is designed to:
1. **Match BioDYM's actual implementation** - Colors correspond to real elements and process types
2. **Ensure scientific clarity** - Colors have logical associations (blue=water, green=carbon, etc.)
3. **Support multi-element analysis** - Distinct colors for material, WC, DM, CC
4. **Distinguish process types** - Clear visual separation of different process logics
5. **Maintain accessibility** - Color-blind friendly palettes where possible

## 📊 **Element Colors (ELEMENT_COLORS)**

BioDYM tracks four primary elements in material flows:

| Element | Color | Hex Code | Rationale |
|---------|-------|----------|-----------|
| **material** | Bright Green | `#00C851` | Main material flow (organic/natural) |
| **WC** | Bright Blue | `#007BFF` | Water Content (blue = water) |
| **DM** | Bright Orange | `#FF8C00` | Dry Matter (earth/soil) |
| **CC** | Bright Red | `#FF4444` | Carbon Content (carbon/energy) |

### **Physical Relationships**
- **material = WC + DM** (mass balance constraint)
- **CC** is a fraction of **DM** (carbon content of dry matter)

## ⚙️ **Process Type Colors (PROCESS_COLORS)**

BioDYM implements five distinct process types:

| Process Type | Color | Hex Code | Description |
|--------------|-------|----------|-------------|
| **regular** | Primary Blue | `#2E86AB` | Standard MFA processes |
| **splitter** | Pink | `#A23B72` | Splits material into WC + DM |
| **transformer** | Orange | `#F18F01` | Uses transfer coefficients |
| **dsm** | Green | `#28A745` | Dynamic Stock Model (age-structured) |
| **fomp** | Red | `#C73E1D` | First-Order Mineralization Process |

### **Process Logic Details**

#### **Splitter Processes**
- **Function**: `material = WC + DM`
- **Use Case**: Physical separation of wet and dry components
- **Example**: Drying processes, dewatering

#### **Transformer Processes**
- **Function**: Uses transfer coefficients for each element
- **Use Case**: Chemical transformations, conversions
- **Example**: Composting, fermentation

#### **DSM Processes**
- **Function**: Age-structured stock with lifetime distributions
- **Use Case**: Long-term storage with aging
- **Example**: Product stocks, infrastructure

#### **FOMP Processes**
- **Function**: Two-pool carbon decay (labile + recalcitrant)
- **Use Case**: Soil carbon modeling, organic matter decomposition
- **Example**: Soil carbon stocks, compost maturation

## 🎨 **Primary Color Palette (BIOYM_COLORS)**

The core brand colors for BioDYM:

| Color | Hex Code | Usage |
|-------|----------|-------|
| **primary** | `#2E86AB` | Main elements, primary flows |
| **secondary** | `#A23B72` | Secondary elements, transformers |
| **accent** | `#F18F01` | Highlights, important annotations |
| **success** | `#C73E11D` | Important flows, critical processes |
| **neutral** | `#6C757D` | Neutral elements, backgrounds |
| **light** | `#F8F9FA` | Plot backgrounds |
| **dark** | `#212529` | Text, borders |

## 🔧 **Implementation Functions**

### **Element Color Functions**
```python
from plotting import get_element_color

# Get color for specific element
color = get_element_color('WC')  # Returns '#17A2B8'
color = get_element_color('CC')  # Returns '#28A745'
```

### **Process Color Functions**
```python
from plotting import get_process_color, detect_biodym_process_type

# Get color for process type
color = get_process_color('splitter')  # Returns '#A23B72'

# Auto-detect process type from BioDYM system
process_type = detect_biodym_process_type(
    process_id=5, 
    process_logic_map=process_logic_map,
    dsm_params=dsm_params,
    fomp_params=fomp_params
)
color = get_process_color(process_type)
```

### **Color Sequence Generation**
```python
from plotting import create_color_sequence

# Generate colors for multiple elements
colors = create_color_sequence(4, 'element')  
# Returns ['#2E86AB', '#17A2B8', '#6C757D', '#28A745']

# Generate colors for multiple processes
colors = create_color_sequence(3, 'process')
# Returns ['#2E86AB', '#A23B72', '#F18F01']
```

## 📈 **Usage in Plots**

### **Sankey Diagrams**
- **Nodes**: Process type colors (regular, splitter, transformer, dsm, fomp)
- **Links**: Element colors (material, WC, DM, CC)
- **Legend**: Shows both process types and element colors

### **Time Series Plots**
- **Lines**: Element colors for different elements
- **Markers**: Same colors as lines for consistency
- **Background**: Light gray for readability

### **Validation Plots**
- **Success**: Green (`#28A745`)
- **Warning**: Yellow (`#FFC107`)
- **Error**: Red (`#DC3545`)
- **Info**: Cyan (`#17A2B8`)

## 🎯 **Color Associations**

### **Logical Associations**
- **Blue** = Water (WC, water content)
- **Green** = Carbon/Organic (CC, carbon content, DSM)
- **Gray** = Dry/Neutral (DM, dry matter, regular processes)
- **Orange** = Transformation (transformer processes)
- **Pink** = Splitting (splitter processes)
- **Red** = Decay/Mineralization (FOMP processes)

### **Scientific Conventions**
- **Water**: Blue/Cyan (universal water symbol)
- **Carbon**: Green (organic matter, photosynthesis)
- **Dry Matter**: Gray (neutral, structural)
- **Material**: Primary Blue (main flow)

## 🔄 **Integration with BioDYM**

The color system integrates seamlessly with BioDYM's:

1. **Excel Configuration** - Colors are applied based on Excel-defined process logic
2. **Dynamic Detection** - Process types are automatically detected from system configuration
3. **Multi-Element Analysis** - Each element gets its distinct color
4. **Special Models** - DSM and FOMP processes have unique colors
5. **Export System** - Colors are preserved in all export formats

## 📋 **Migration Guide**

### **Updating Existing Plots**
1. Import the new color functions
2. Replace hardcoded colors with `get_element_color()` and `get_process_color()`
3. Use `detect_biodym_process_type()` for automatic process type detection
4. Apply publication styling with `apply_publication_style()`

### **Example Migration**
```python
# Old approach
fig.add_trace(go.Scatter(
    x=time, y=wc_data,
    line=dict(color='blue'),  # Hardcoded
    name='WC'
))

# New approach
from plotting import get_element_color, apply_publication_style

fig.add_trace(go.Scatter(
    x=time, y=wc_data,
    line=dict(color=get_element_color('WC')),  # Standardized
    name='WC'
))
fig = apply_publication_style(fig)
```

## 🎨 **Color Accessibility**

The color palette is designed to be:
- **Color-blind friendly** - Uses distinct hues and saturations
- **High contrast** - Sufficient contrast for readability
- **Print-friendly** - Works well in both color and grayscale
- **Screen-optimized** - Clear on both light and dark backgrounds

## 📚 **References**

- [BioDYM Framework Documentation](docs/ESSENTIAL_KNOWLEDGE_SUMMARY.md)
- [Plotly Color Guidelines](https://plotly.com/python/colors/)
- [Scientific Figure Standards](https://www.nature.com/articles/d41586-019-00199-6)
- [Color Accessibility Guidelines](https://webaim.org/articles/contrast/)

---

*This color system is maintained as part of the BioDYM framework. Please update this document when adding new elements or process types.*
