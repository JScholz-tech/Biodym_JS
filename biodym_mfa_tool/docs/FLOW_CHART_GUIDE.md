# BioDYM Flow Chart Guide

This guide explains how to create flow charts from your process and flow data using the BioDYM framework.

## Overview

The BioDYM tool provides three types of flow chart visualizations:

1. **Basic Flow Chart** - Static visualization with process nodes and flow arrows
2. **Interactive Flow Chart** - Dynamic visualization with filtering controls
3. **System Architecture Diagram** - Hierarchical layout showing process categories

## Quick Start

### 1. Basic Flow Chart

```python
import plotting

# Create a basic flow chart
fig, G = plotting.plot_flow_chart(
    mfa_system_with_results, 
    title="My System Flow Chart",
    layout_type="hierarchical"  # Options: "hierarchical", "circular", "force_directed"
)
```

### 2. Interactive Flow Chart

```python
# Create an interactive flow chart with controls
fig, G = plotting.plot_interactive_flow_chart(
    mfa_system_with_results,
    title="Interactive System Flow Chart"
)
```

### 3. System Architecture Diagram

```python
# Create a system architecture diagram
fig = plotting.plot_system_architecture_diagram(
    mfa_system_with_results,
    title="System Architecture"
)
```

## Function Details

### `plot_flow_chart()`

Creates a comprehensive flow chart visualization using NetworkX and Matplotlib.

**Parameters:**
- `mfa_system_results`: The MFA system object with processes and flows
- `title`: Title for the flow chart (default: "System Flow Chart")
- `layout_type`: Layout algorithm ("hierarchical", "circular", "force_directed")

**Features:**
- Process nodes colored by type (boundary, input, treatment, use, output)
- Flow arrows with width proportional to flow values
- Edge labels showing flow values
- Legend showing process types
- System statistics display

### `plot_interactive_flow_chart()`

Creates an interactive flow chart using Plotly with filtering controls.

**Parameters:**
- `mfa_system_results`: The MFA system object
- `title`: Title for the flow chart

**Interactive Controls:**
- **Show Flow Values**: Toggle flow value labels on/off
- **Min Flow Threshold**: Filter flows below a certain value
- **Process Types**: Select which process types to display

**Features:**
- Real-time filtering and updates
- Hover information for processes and flows
- Export functionality
- Responsive design

### `plot_system_architecture_diagram()`

Creates a hierarchical system architecture diagram.

**Parameters:**
- `mfa_system_results`: The MFA system object
- `title`: Title for the diagram

**Features:**
- Hierarchical layout by process type
- Rounded rectangle process boxes
- Flow arrows with labels
- System statistics overview
- Color-coded process categories

## Process Type Classification

The flow chart functions automatically classify processes based on their names:

| Process Type | Keywords | Color |
|--------------|----------|-------|
| Boundary | ID = 0 | Light Red |
| Input | "input", "source" | Light Blue |
| Treatment | "treatment", "processing" | Light Green |
| Use | "use", "consumption" | Light Orange |
| Output | "output", "sink" | Light Pink |
| Process | (default) | Light Gray |

## Usage Examples

### Example 1: Basic Flow Chart from Excel Data

```python
# Load your Excel data and run calculations
input_file = "data/01_input/your_file.xlsx"
# ... (standard BioDYM workflow) ...

# Create flow chart
fig, G = plotting.plot_flow_chart(
    mfa_system_with_results,
    title="My BioDYM System",
    layout_type="hierarchical"
)
```

### Example 2: Interactive Flow Chart with Customization

```python
# Create interactive flow chart
fig, G = plotting.plot_interactive_flow_chart(
    mfa_system_with_results,
    title="Interactive System Analysis"
)

# The interactive controls will appear automatically
# - Use the checkboxes to show/hide flow values
# - Adjust the slider to filter by minimum flow
# - Select process types to focus on specific categories
```

### Example 3: System Architecture for Documentation

```python
# Create architecture diagram for reports
fig = plotting.plot_system_architecture_diagram(
    mfa_system_with_results,
    title="System Architecture Overview"
)
```

## Integration with Scientific Notebook

The flow chart functions are integrated into the BioDYM Scientific Notebook:

1. **Section 3.5** automatically creates all three flow chart types
2. **Error handling** ensures the notebook continues even if flow charts fail
3. **Progress reporting** shows which charts are being created

## Customization Options

### Layout Types

- **hierarchical**: Spring layout optimized for hierarchical systems
- **circular**: Circular arrangement of processes
- **force_directed**: Force-directed layout for complex networks

### Color Schemes

The default color scheme can be modified in the plotting functions:

```python
color_map = {
    'boundary': '#ff9999',    # Light red
    'input': '#99ccff',       # Light blue
    'treatment': '#99ff99',   # Light green
    'use': '#ffcc99',         # Light orange
    'output': '#ff99cc',      # Light pink
    'process': '#cccccc'      # Light gray
}
```

### Export Options

All flow charts support export functionality:

- **PNG**: High-resolution static images
- **PDF**: Vector graphics for publications
- **SVG**: Scalable vector graphics
- **HTML**: Interactive web versions (Plotly charts)

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all required modules are installed
   ```bash
   pip install networkx matplotlib plotly ipywidgets
   ```

2. **Layout Issues**: Try different layout types for complex systems
   ```python
   layout_type="force_directed"  # Better for complex networks
   ```

3. **Performance**: For large systems, use filtering
   ```python
   # Use interactive flow chart with threshold filtering
   min_flow_threshold = 10.0  # Filter small flows
   ```

4. **Memory Issues**: Reduce figure size for large systems
   ```python
   fig, ax = plt.subplots(1, 1, figsize=(12, 8))  # Smaller size
   ```

### Debugging

Enable debug output by checking the console messages:

```
📊 Creating basic flow chart...
✅ Basic flow chart created
   📊 Features: Process nodes, flow arrows, value labels
   🎨 Color coding: Process types (boundary, input, treatment, use, output)
   📈 Edge width: Proportional to flow values
```

## Best Practices

1. **Process Naming**: Use descriptive names that indicate process type
2. **Flow Values**: Ensure flow values are properly calculated before visualization
3. **System Size**: For large systems (>20 processes), use interactive charts
4. **Documentation**: Include flow charts in reports and presentations
5. **Export**: Save high-resolution versions for publications

## Example Workflow

```python
# 1. Load and calculate your MFA system
# ... (standard BioDYM workflow) ...

# 2. Create basic flow chart for overview
fig1, G1 = plotting.plot_flow_chart(mfa_system_with_results)

# 3. Create interactive chart for detailed analysis
fig2, G2 = plotting.plot_interactive_flow_chart(mfa_system_with_results)

# 4. Create architecture diagram for documentation
fig3 = plotting.plot_system_architecture_diagram(mfa_system_with_results)

# 5. Export for reports
fig1.savefig("flow_chart.png", dpi=300, bbox_inches='tight')
```

## Advanced Usage

### Custom Process Classification

You can modify the process classification logic in the plotting functions:

```python
# In plotting.py, modify the process type determination
if "custom_keyword" in process_name.lower():
    process_type = "custom_type"
```

### Custom Color Schemes

Modify the color map in the plotting functions:

```python
custom_color_map = {
    'boundary': '#ff0000',    # Red
    'input': '#0000ff',       # Blue
    'treatment': '#00ff00',   # Green
    # ... add your custom colors
}
```

### Integration with Other Tools

The flow chart functions return NetworkX graph objects that can be used with other network analysis tools:

```python
fig, G = plotting.plot_flow_chart(mfa_system_with_results)

# Use the graph object for further analysis
print(f"Graph density: {nx.density(G)}")
print(f"Number of components: {nx.number_strongly_connected_components(G)}")
```

This comprehensive flow chart system provides powerful visualization capabilities for your BioDYM Material Flow Analysis projects. 