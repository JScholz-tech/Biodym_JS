# 🎯 Enhanced Sankey Diagrams for Circular Systems

## Overview

This guide explains how to use the enhanced Sankey diagram functionality for visualizing circular/recycling material flow systems in BioDYM.

## 🚀 Quick Start

### 1. Basic Usage

Add this to your BioDYM Scientific Notebook:

```python
# Import the enhanced Sankey functionality
from plotting import plot_circular_sankey

# Plot circular Sankey diagram
plot_circular_sankey(
    mfa_system_results=mfa_results_baseline,
    dsm_params=dsm_params,
    fomp_params=fomp_params
)
```

### 2. With Custom Configuration

```python
# Use custom visualization configuration
plot_circular_sankey(
    mfa_system_results=mfa_results_baseline,
    dsm_params=dsm_params,
    fomp_params=fomp_params,
    config_file="data/01_input/My_Circular_Config.xlsx"
)
```

## 📊 Excel Configuration

### Process_Visualization Sheet

| Column | Description | Example |
|--------|-------------|---------|
| Process_ID | Must match your MFA system process IDs | P_01, P_02, etc. |
| Process_Name | Human-readable process name | "Input Process" |
| Node_Color | Hex color code | #FF6B6B |
| Node_Size | Size category | Small, Medium, Large, XLarge |
| X_Position | X coordinate (0.0 to 1.0) | 0.5 |
| Y_Position | Y coordinate (0.0 to 1.0) | 0.5 |
| Layout_Type | Layout algorithm | Auto, Fixed, Circular, Radial |

### Flow_Visualization Sheet

| Column | Description | Example |
|--------|-------------|---------|
| Flow_ID | Must match your MFA system flow IDs | F_01_02, F_02_03, etc. |
| Flow_Name | Human-readable flow name | "Input to Processing" |
| Flow_Color | Hex color code | #FF6B6B |
| Flow_Opacity | Transparency (0.0 to 1.0) | 0.8 |
| Flow_Width_Multiplier | Width relative to flow value | 1.0 |
| Flow_Style | Line style | Solid, Dashed, Dotted |

### Layout_Configuration Sheet

| Setting | Description | Options |
|---------|-------------|---------|
| Default_Layout_Type | Main layout algorithm | Linear, Circular, Radial, Custom |
| Circular_Center_X | Center X for circular layout | 0.0 to 1.0 |
| Circular_Center_Y | Center Y for circular layout | 0.0 to 1.0 |
| Circular_Radius | Radius for circular layout | 0.1 to 0.5 |
| Flow_Curvature | How curved the flows are | 0.0 to 1.0 |

## 🔄 Circular System Features

### Automatic Circular Detection

The system automatically detects circular flows by:
1. Identifying processes that have flows back to previous processes
2. Positioning these processes in a circular layout
3. Using curved flow lines to show recycling connections

### Layout Types

- **Circular**: Best for recycling systems - processes with circular flows are arranged in a circle
- **Radial**: All processes arranged in a circle
- **Linear**: Traditional left-to-right layout
- **Custom**: Manual positioning using X_Position and Y_Position

### Visual Customization

- **Process Colors**: Custom colors for each process type
- **Flow Styling**: Different styles for forward vs. recycling flows
- **Flow Opacity**: Lower opacity for recycling flows to show hierarchy
- **Flow Width**: Proportional to flow values with customizable multipliers

## 🎨 Best Practices for Circular Systems

### 1. Color Coding
- Use **solid lines** for forward flows
- Use **dashed lines** for recycling flows
- Use **different colors** for different flow types
- Use **lower opacity** for recycling flows

### 2. Layout Optimization
- Set `Layout_Type='Circular'` for recycling processes
- Adjust `Circular_Radius` for optimal visibility
- Use `Flow_Curvature=0.8` for more curved flows
- Position input/output processes at fixed positions

### 3. Process Identification
- Use descriptive `Process_Name` values
- Match `Process_ID` exactly with your MFA system
- Use `Node_Size` to highlight important processes

## 📝 Example Configuration

### For a Simple Circular System:

**Process_Visualization:**
```
Process_ID | Process_Name | Node_Color | Layout_Type
P_01      | Input        | #FF6B6B    | Fixed
P_02      | Processing   | #4ECDC4    | Circular
P_03      | Recycling    | #96CEB4    | Circular
P_04      | Output       | #FFEAA7    | Fixed
```

**Flow_Visualization:**
```
Flow_ID | Flow_Name              | Flow_Color | Flow_Style
F_01_02 | Input to Processing    | #FF6B6B    | Solid
F_02_03 | Processing to Recycling| #4ECDC4    | Solid
F_03_02 | Recycling to Processing| #96CEB4    | Dashed
F_02_04 | Processing to Output   | #FFEAA7    | Solid
```

## 🔧 Troubleshooting

### Common Issues

1. **Processes not showing in circle**: Check that `Layout_Type='Circular'` is set
2. **Flows not curved**: Increase `Flow_Curvature` value
3. **Colors not applied**: Verify `Process_ID` and `Flow_ID` match your system exactly
4. **Layout too crowded**: Decrease `Circular_Radius` or increase `Node_Spacing`

### Debug Mode

Add this to see what's happening:

```python
# Enable debug output
import logging
logging.basicConfig(level=logging.DEBUG)

# Plot with debug info
plot_circular_sankey(mfa_system_results, debug=True)
```

## 🚀 Advanced Features

### Custom Positioning

For complex systems, use manual positioning:

```python
# In Process_Visualization sheet:
# Process_ID | X_Position | Y_Position | Layout_Type
# P_01      | 0.1        | 0.5        | Fixed
# P_02      | 0.5        | 0.3        | Fixed
# P_03      | 0.5        | 0.7        | Fixed
```

### Multiple Circular Groups

For systems with multiple circular groups, use different `Circular_Center_X` and `Circular_Center_Y` values for each group.

### Export Options

The enhanced Sankey supports high-resolution export:

```python
# Export as PNG (default)
fig.write_image("circular_sankey.png", width=1200, height=800, scale=2)

# Export as SVG (vector)
fig.write_image("circular_sankey.svg", width=1200, height=800)
```

## 📚 Further Reading

- [Plotly Sankey Documentation](https://plotly.com/python/sankey-diagram/)
- [BioDYM MFA Tool Documentation](manuscript_documentation.md)
- [Configuration Guide](ESSENTIAL_KNOWLEDGE_SUMMARY.md)
