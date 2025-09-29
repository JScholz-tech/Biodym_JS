# BioDYM Publication Style Usage Guide

## Overview
The BioDYM plotting system includes a comprehensive publication style framework designed to create consistent, professional visualizations suitable for scientific publications. This guide explains how to use the publication style features effectively.

## Core Components

### 1. Publication Layout (`get_publication_layout()`)
**Purpose**: Provides standardized layout settings for all plots
**Usage**: Apply to any Plotly figure for consistent appearance

```python
from src.plotting.publication_style import get_publication_layout

# Apply to any figure
fig.update_layout(**get_publication_layout())
```

**What it includes**:
- Standardized margins and padding
- Professional font settings
- Consistent background colors
- Grid and axis styling
- Legend positioning

### 2. Color Palettes

#### Element Colors (`get_element_color()`)
**Purpose**: Get consistent colors for different elements (C, N, P, etc.)
**Usage**: 
```python
from src.plotting.publication_style import get_element_color

# Get color for specific element
carbon_color = get_element_color('C')      # Returns green
nitrogen_color = get_element_color('N')    # Returns blue
phosphorus_color = get_element_color('P')  # Returns orange
```

#### Process Differentiation Colors (`PROCESS_DIFFERENTIATION_COLORS`)
**Purpose**: Distinct colors for different processes, avoiding element colors
**Usage**:
```python
from src.plotting.publication_style import PROCESS_DIFFERENTIATION_COLORS

# Use in process-based plots
colors = PROCESS_DIFFERENTIATION_COLORS[:num_processes]
```

#### BioDYM Brand Colors (`BIOYM_COLORS`)
**Purpose**: Brand-consistent colors for BioDYM-specific elements
**Usage**:
```python
from src.plotting.publication_style import BIOYM_COLORS

# Use brand colors
primary_color = BIOYM_COLORS['primary']
secondary_color = BIOYM_COLORS['secondary']
dark_color = BIOYM_COLORS['dark']
```

### 3. Color Sequence Generation (`create_color_sequence()`)
**Purpose**: Generate harmonious color sequences for multiple data series
**Usage**:
```python
from src.plotting.publication_style import create_color_sequence

# Generate colors for multiple series
colors = create_color_sequence(
    num_colors=5,
    palette='primary',  # or 'element', 'process', 'differentiation'
    base_color=None      # optional base color
)
```

## Implementation Examples

### Example 1: Basic Plot with Publication Style
```python
import plotly.graph_objects as go
from src.plotting.publication_style import get_publication_layout, get_element_color

# Create basic plot
fig = go.Figure()

# Add traces with element colors
fig.add_trace(go.Scatter(
    x=time_data,
    y=carbon_data,
    name='Carbon',
    line=dict(color=get_element_color('C'), width=2)
))

fig.add_trace(go.Scatter(
    x=time_data,
    y=nitrogen_data,
    name='Nitrogen',
    line=dict(color=get_element_color('N'), width=2)
))

# Apply publication layout
fig.update_layout(**get_publication_layout())

# Display
fig.show()
```

### Example 2: Process-Based Plot with Differentiation Colors
```python
from src.plotting.publication_style import PROCESS_DIFFERENTIATION_COLORS, create_color_sequence

# For multiple processes
processes = ['Process A', 'Process B', 'Process C', 'Process D']
colors = create_color_sequence(len(processes), palette='differentiation')

for i, process in enumerate(processes):
    fig.add_trace(go.Bar(
        x=time_data,
        y=process_data[i],
        name=process,
        marker_color=colors[i]
    ))
```

### Example 3: Multi-Element Plot with Element Colors
```python
elements = ['C', 'N', 'P', 'K']
for element in elements:
    color = get_element_color(element)
    fig.add_trace(go.Scatter(
        x=time_data,
        y=element_data[element],
        name=f'{element} Content',
        line=dict(color=color, width=2),
        hovertemplate=f"<b>{element}</b><br>Year: %{{x}}<br>Content: %{{y:.2e}} Mg<extra></extra>"
    ))
```

## Advanced Features

### 1. Scientific Notation
**Purpose**: Consistent number formatting for scientific data
**Usage**:
```python
# Y-axis with scientific notation
fig.update_yaxes(
    tickformat=".2e",  # Scientific notation with 2 decimal places
    zeroline=True,
    zerolinecolor=BIOYM_COLORS['dark'],
    zerolinewidth=2
)
```

### 2. Grid Styling
**Purpose**: Professional grid appearance
**Usage**:
```python
# Add grid to both axes
fig.update_xaxes(
    showgrid=True,
    gridcolor='#e1e5e9',
    gridwidth=1
)
fig.update_yaxes(
    showgrid=True,
    gridcolor='#e1e5e9',
    gridwidth=1
)
```

### 3. Hover Templates
**Purpose**: Consistent hover information
**Usage**:
```python
# Standardized hover template
hovertemplate="<b>%{fullData.name}</b><br>Year: %{x}<br>Value: %{y:.2e} Mg<extra></extra>"
```

## Color Palette Reference

### Element Colors
- **Carbon (C)**: Green (`#2E8B57`)
- **Nitrogen (N)**: Blue (`#4169E1`)
- **Phosphorus (P)**: Orange (`#FF8C00`)
- **Potassium (K)**: Purple (`#9370DB`)
- **Sulfur (S)**: Yellow (`#FFD700`)

### Process Differentiation Colors
- **Process 1**: Teal (`#20B2AA`)
- **Process 2**: Coral (`#FF7F50`)
- **Process 3**: Gold (`#DAA520`)
- **Process 4**: Medium Purple (`#9370DB`)
- **Process 5**: Light Sea Green (`#20B2AA`)
- **Process 6**: Tomato (`#FF6347`)
- **Process 7**: Dark Khaki (`#BDB76B`)
- **Process 8**: Plum (`#DDA0DD`)
- **Process 9**: Cadet Blue (`#5F9EA0`)
- **Process 10**: Light Coral (`#F08080`)
- **Process 11**: Dark Goldenrod (`#B8860B`)
- **Process 12**: Medium Orchid (`#BA55D3`)

### BioDYM Brand Colors
- **Primary**: Dark Blue (`#1E3A8A`)
- **Secondary**: Light Blue (`#3B82F6`)
- **Dark**: Very Dark Blue (`#0F172A`)
- **Light**: Light Gray (`#F8FAFC`)

## Best Practices

### 1. Consistency
- Always use `get_publication_layout()` for plot layout
- Use element colors for element-based data
- Use process differentiation colors for process-based data
- Maintain consistent hover templates

### 2. Accessibility
- Ensure sufficient color contrast
- Use different line styles in addition to colors
- Include clear legends and labels

### 3. Scientific Standards
- Use scientific notation for large numbers
- Include units in axis labels
- Provide clear hover information
- Use consistent decimal places

### 4. Export Quality
- Use high resolution for publications
- Ensure colors are publication-friendly
- Test print quality

## Common Patterns

### Pattern 1: Time Series with Multiple Elements
```python
def create_element_time_series(data, elements):
    fig = go.Figure()
    
    for element in elements:
        fig.add_trace(go.Scatter(
            x=data['time'],
            y=data[element],
            name=f'{element} Content',
            line=dict(color=get_element_color(element), width=2),
            hovertemplate=f"<b>{element}</b><br>Year: %{{x}}<br>Content: %{{y:.2e}} Mg<extra></extra>"
        ))
    
    fig.update_layout(**get_publication_layout())
    fig.update_yaxes(tickformat=".2e")
    return fig
```

### Pattern 2: Process Comparison
```python
def create_process_comparison(data, processes):
    fig = go.Figure()
    colors = create_color_sequence(len(processes), palette='differentiation')
    
    for i, process in enumerate(processes):
        fig.add_trace(go.Bar(
            x=data['categories'],
            y=data[process],
            name=process,
            marker_color=colors[i]
        ))
    
    fig.update_layout(**get_publication_layout())
    return fig
```

### Pattern 3: Multi-Panel Plot
```python
def create_multi_panel_plot(data):
    from plotly.subplots import make_subplots
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=['Panel 1', 'Panel 2', 'Panel 3', 'Panel 4']
    )
    
    # Add traces to each subplot
    # ... add your traces here ...
    
    # Apply publication layout
    fig.update_layout(**get_publication_layout())
    return fig
```

## Troubleshooting

### Common Issues

1. **Colors not showing**: Ensure you're importing the color functions correctly
2. **Layout not applied**: Make sure to use `**get_publication_layout()` with unpacking
3. **Inconsistent styling**: Always use the publication style functions instead of manual styling

### Getting Help

If you encounter issues:
1. Check the import statements
2. Verify the function parameters
3. Test with a simple example first
4. Refer to the source code in `src/plotting/publication_style.py`

## Integration with Existing Plots

To convert existing plots to use publication style:

1. **Add imports**:
   ```python
   from src.plotting.publication_style import get_publication_layout, get_element_color
   ```

2. **Replace manual colors**:
   ```python
   # Instead of: color='red'
   # Use: color=get_element_color('C')
   ```

3. **Apply layout**:
   ```python
   fig.update_layout(**get_publication_layout())
   ```

4. **Add scientific notation**:
   ```python
   fig.update_yaxes(tickformat=".2e")
   ```

This guide should help you effectively use the publication style system for creating professional, consistent visualizations in your BioDYM analysis.
