# Sankey Diagram Positioning Manual

**Version**: 1.0
**Date**: 2025-11-07
**For**: BioDYM Enhanced Sankey Visualization

---

## Table of Contents

1. [Overview](#overview)
2. [Excel Configuration Structure](#excel-configuration-structure)
3. [Coordinate System](#coordinate-system)
4. [Node Positioning Strategy](#node-positioning-strategy)
5. [Element-Specific Layouts](#element-specific-layouts)
6. [Visual Configuration](#visual-configuration)
7. [Highlighting Special Processes (DSM, FOMP)](#highlighting-special-processes)
8. [Step-by-Step Positioning Guide](#step-by-step-positioning-guide)
9. [Common Layout Patterns](#common-layout-patterns)
10. [Troubleshooting](#troubleshooting)

---

## Overview

BioDYM's Enhanced Sankey diagrams allow you to **manually position nodes** in your Excel configuration file. This gives you complete control over the visual layout, enabling you to:

- ✅ Create publication-quality diagrams with optimal node placement
- ✅ Show different layouts for different elements (Material vs DM vs CC)
- ✅ Highlight key processes (DSM, FOMP, cascading flows)
- ✅ Create hierarchical layouts showing process stages
- ✅ Avoid overlapping flows and improve readability

---

## Excel Configuration Structure

Your configuration is spread across **3 Excel sheets**:

### Sheet 1: `6_1_Visualization_Processes`

**Purpose**: Define node positions and colors for each process

**Columns**:

| Column Name          | Type    | Description                                    | Example |
|----------------------|---------|------------------------------------------------|---------|
| Process_ID           | Integer | Process ID matching `2_1_Definition_Processes` | 3       |
| Name(EN)             | Text    | Process name for reference                     | Use Phase |
| Node_Color_#         | Hex     | Node color in hex format                       | #F5DEB3 |
| X_Position_Material  | Float   | X coordinate for Material element (0.0 - 1.0)  | 0.50    |
| Y_Position_Material  | Float   | Y coordinate for Material element (0.0 - 1.0)  | 0.20    |
| X_Position_CU        | Float   | X coordinate for CU element                    | 0.45    |
| Y_Position_CU        | Float   | Y coordinate for CU element                    | 0.30    |
| X_Position_Fe        | Float   | X coordinate for Fe element                    | 0.45    |
| Y_Position_Fe        | Float   | Y coordinate for Fe element                    | 0.30    |
| ...                  | ...     | Additional element-specific positions          | ...     |

**Key Points**:
- Each element (Material, CU, Fe, Al, etc.) can have its own X/Y positions
- Coordinates are **normalized**: 0.0 (left/bottom) to 1.0 (right/top)
- If element-specific positions are missing, falls back to `X_Position_Material`

### Sheet 2: `6_2_Visualization_Flows`

**Purpose**: Define flow colors and styling

**Columns**:

| Column Name   | Type | Description                      | Example |
|---------------|------|----------------------------------|---------|
| Flow_ID       | Text | Flow ID matching flow definitions| F_01_03 |
| Flow_Name     | Text | Flow name for reference          | Input to Use |
| Flow_Color_#  | Hex  | Flow color in hex format         | #00C851 |

### Sheet 3: `6_3_Layout_Configuration`

**Purpose**: Global layout settings (window size, zoom, padding)

**Key Settings**:

| Setting           | Default | Description                                           |
|-------------------|---------|-------------------------------------------------------|
| Window_Width      | 1600    | Sankey diagram width in pixels                        |
| Window_Height     | 1200    | Sankey diagram height in pixels                       |
| Zoom_Factor       | 1.0     | Overall zoom (1.0 = normal, 2.0 = 2× larger)         |
| Node_Scale_Factor | 1.0     | Node thickness scale (1.0 = normal, 1.5 = thicker)   |
| Padding_Factor    | 0.1     | Border padding as fraction of frame (0.1 = 10%)      |

---

## Coordinate System

### Normalized Coordinates

All positions use **normalized coordinates** (0.0 to 1.0):

```
(0.0, 1.0) ────────────────── (1.0, 1.0)  ← Top
    │                              │
    │                              │
    │         (0.5, 0.5)          │       ← Center
    │              •               │
    │                              │
(0.0, 0.0) ────────────────── (1.0, 0.0)  ← Bottom
    ↑                              ↑
   Left                          Right
```

### Coordinate Examples

| Position Description | X    | Y    |
|----------------------|------|------|
| Top-left corner      | 0.0  | 1.0  |
| Top-right corner     | 1.0  | 1.0  |
| Bottom-left corner   | 0.0  | 0.0  |
| Bottom-right corner  | 1.0  | 0.0  |
| Center               | 0.5  | 0.5  |
| Left-middle          | 0.1  | 0.5  |
| Right-middle         | 0.9  | 0.5  |

**IMPORTANT**: Y-axis grows **upward** (0.0 = bottom, 1.0 = top), like mathematical plots.

---

## Node Positioning Strategy

### Basic Principles

1. **Left-to-Right Flow**: Position input processes on the left (X ≈ 0.1), outputs on the right (X ≈ 0.9)
2. **Vertical Separation**: Use Y-position to separate parallel processes
3. **Avoid Overlaps**: Minimum spacing of 0.1 between nodes
4. **Stage Grouping**: Group processes by stage using X-position

### Recommended X-Positions by Stage

| Process Stage           | X Range     | Example Processes                   |
|-------------------------|-------------|-------------------------------------|
| Inputs/Sources          | 0.05 - 0.15 | Raw material production, Imports    |
| Primary Processing      | 0.25 - 0.35 | Manufacturing, Initial treatment    |
| Use/Storage/Stocks      | 0.45 - 0.55 | Use phase, DSM processes, Storage   |
| Secondary Processing    | 0.65 - 0.75 | Remanufacturing, Recycling, Repair  |
| Outputs/Sinks           | 0.85 - 0.95 | Waste treatment, Exports, Disposal  |

### Recommended Y-Positions by Function

| Function Type          | Y Range     | Use Case                             |
|------------------------|-------------|--------------------------------------|
| Primary flow           | 0.15 - 0.25 | Main material pathway                |
| Secondary flow         | 0.35 - 0.45 | Alternative processing routes        |
| Tertiary flow          | 0.55 - 0.65 | Recycling loops, Repair flows        |
| Stock/Storage          | 0.75 - 0.85 | Accumulation processes, Landfills    |

---

## Element-Specific Layouts

### Why Use Element-Specific Positions?

Different elements may flow through different process pathways:
- **Material**: Shows total mass flows through all processes
- **CU/Fe/Al**: May concentrate in specific processes (metals in manufacturing)
- **Plastics**: Different recycling pathways
- **Hazardous materials**: Special treatment processes

### Creating Hierarchical Layouts

For Journal of Industrial Ecology publication showing element hierarchy:

#### Material Layout (Top-Level)
```
X_Position_Material | Y_Position_Material | Process Type
0.10                | 0.50                | Input (centered vertical)
0.30                | 0.50                | Manufacturing (centered)
0.50                | 0.50                | Use Phase/DSM (centered)
0.70                | 0.30                | Repair (lower)
0.70                | 0.70                | Remanufacturing (upper)
0.90                | 0.50                | Output (centered)
```

#### CU Layout (Show Metal-Specific Pathways)
```
X_Position_CU | Y_Position_CU | Process Type
0.10          | 0.60          | Input (higher - emphasize source)
0.30          | 0.60          | Manufacturing (higher)
0.50          | 0.50          | Use Phase (center)
0.70          | 0.70          | Remanufacturing (emphasize recycling)
0.90          | 0.30          | Waste treatment (lower)
```

### Strategy for Multi-Element Multiplot

When using `plot_element_multiplot_sankey()`, all subplots use the same coordinate system:

**Best Practice**: Use **consistent X-positions** across elements, but **vary Y-positions** to show different pathways:

```python
# In Excel 6_1_Visualization_Processes:

Process_ID | X_Position_Material | Y_Position_Material | X_Position_CU | Y_Position_CU
3 (DSM)    | 0.50                | 0.50                | 0.50          | 0.40
4 (Repair) | 0.70                | 0.30                | 0.70          | 0.60
```

This creates alignment vertically across subplots (same X) while showing different flow patterns (different Y).

---

## Visual Configuration

### Node Colors

**Color Coding Strategy**:

| Process Type          | Recommended Color | Hex Code | Rationale                     |
|-----------------------|-------------------|----------|-------------------------------|
| Input processes       | Forest Green      | #228B22  | Natural sources, biomass      |
| Manufacturing         | Wheat Gold        | #F5DEB3  | Processing, transformation    |
| Use Phase             | Light Blue        | #87CEEB  | In-use stocks, consumer side  |
| DSM Process           | Green             | #28A745  | Stock accumulation (special)  |
| FOMP Process          | Brown             | #C73E1D  | Biological decay (special)    |
| Recycling/Reuse       | Blue              | #2E86AB  | Circular economy              |
| Waste Treatment       | Dark Gray         | #6C757D  | End-of-life, disposal         |
| Stocks                | Purple            | #6F42C1  | Material accumulation         |

**Publication-Ready B&W Strategy** (for journals without color):

| Process Type     | Grayscale | Hex Code | Pattern Alternative     |
|------------------|-----------|----------|-------------------------|
| Input            | Dark      | #333333  | Use in combination with |
| Processing       | Medium    | #808080  | position to distinguish |
| Output           | Light     | #CCCCCC  | different process types |
| Special (DSM)    | Black     | #000000  | Reserve for key process |

### Flow Colors

**Recommendation**: Use element-specific colors consistently across all diagrams:

| Element           | Color         | Hex Code |
|-------------------|---------------|----------|
| Material (total)  | Bright Green  | #00C851  |
| CU                | Copper Orange | #E67E22  |
| Fe                | Steel Blue    | #34495E  |
| Al                | Silver Gray   | #BDC3C7  |
| Plastics          | Teal          | #16A085  |
| Hazardous         | Red           | #E74C3C  |

---

## Highlighting Special Processes

### DSM Processes (Dynamic Stock Modeling)

**Visual Strategy**:
1. **Position**: Center-right (X ≈ 0.5-0.6) to show it's mid-chain
2. **Color**: Distinct color (#28A745 green) to stand out
3. **Size**: Increase node thickness via `Node_Scale_Factor = 1.5` in layout config

**Example Excel Entry**:
```
Process_ID | Name         | Node_Color_# | X_Position_Material | Y_Position_Material
3          | Use Phase    | #28A745      | 0.55                | 0.50
```

### FOMP Processes (First-Order Mineralization)

**Visual Strategy**:
1. **Position**: Bottom area (Y ≈ 0.2) to show decomposition/decay
2. **Color**: Earth brown (#C73E1D) to represent organic processes
3. **Annotation**: Add text labels (future enhancement)

### Cascading Utilization Flows

**Visual Strategy**:
1. **Vertical Arrangement**: Position cascading processes at different Y-levels
   - Primary use: Y = 0.7
   - Secondary use: Y = 0.5
   - Tertiary use: Y = 0.3
2. **X-Position Progression**: Gradually increase X as material cascades down
   - Primary: X = 0.3
   - Secondary: X = 0.5
   - Tertiary: X = 0.7

**Cascade Example**:
```
Process_ID | Process Name        | X_Position | Y_Position
5          | Primary Use         | 0.30       | 0.70
7          | Secondary Use       | 0.50       | 0.50
8          | Tertiary Use        | 0.70       | 0.30
```

---

## Step-by-Step Positioning Guide

### Step 1: Plan Your Layout on Paper

1. **Sketch your system** on paper with rough node positions
2. **Identify stages**: Input → Processing → Use → Outputs
3. **Group by function**: What processes are parallel? What are sequential?
4. **Mark special processes**: DSM, FOMP, cascading flows

### Step 2: Assign X-Positions (Horizontal)

1. Start with **leftmost processes** (inputs): X = 0.1
2. Work left-to-right through your system stages
3. Space stages evenly: 0.2 - 0.3 units apart
4. End with **rightmost processes** (outputs): X = 0.9

### Step 3: Assign Y-Positions (Vertical)

1. Identify **parallel processes** (same stage, different pathways)
2. Space them vertically: minimum 0.15 units apart
3. Use **Y-position to show hierarchy**:
   - Main pathway: Y = 0.5 (center)
   - Alternative pathways: Y = 0.3 or 0.7
   - Special processes: Y = 0.8 or 0.2 (top/bottom)

### Step 4: Enter Coordinates in Excel

Open `6_1_Visualization_Processes`:

1. Find row for Process_ID
2. Enter `X_Position_Material` and `Y_Position_Material`
3. **For hierarchical multi-element view**: Also fill `X_Position_CU`, etc.
4. Save the Excel file

### Step 5: Test in Notebook

Run your notebook:

```python
plotting.plot_enhanced_sankey(
    mfa_results_baseline,
    dsm_params=dsm_params,
    fomp_params=fomp_params,
    visualization_config_path=input_file
)
```

### Step 6: Iterate and Refine

1. **Check for overlaps**: Are any nodes overlapping?
2. **Check flow crossing**: Do flows cross unnecessarily?
3. **Adjust positions**: Modify Excel, save, re-run notebook
4. **Repeat** until layout is optimal

---

## Common Layout Patterns

### Pattern 1: Linear Flow (Simple Systems)

**Use Case**: Simple input → process → output systems

```
Process A ───► Process B ───► Process C ───► Process D
X: 0.1         X: 0.35        X: 0.65        X: 0.9
Y: 0.5         Y: 0.5         Y: 0.5         Y: 0.5
```

**Excel Entry**:
```
Process_ID | X_Position | Y_Position
1          | 0.10       | 0.50
2          | 0.35       | 0.50
3          | 0.65       | 0.50
4          | 0.90       | 0.50
```

### Pattern 2: Branching Flow (Multiple Outputs)

**Use Case**: One input splits into multiple treatment paths

```
                    ┌─► Process B (Upper)
Process A ──────────┤
                    └─► Process C (Lower)
X: 0.1              X: 0.5       Y: 0.7
Y: 0.5              X: 0.5       Y: 0.3
```

**Excel Entry**:
```
Process_ID | X_Position | Y_Position
1          | 0.10       | 0.50
2          | 0.50       | 0.70
3          | 0.50       | 0.30
```

### Pattern 3: Circular Economy Loop

**Use Case**: Material recycling back to earlier stage

```
Input → Manufacturing → Use → Remanufacturing
  ↑                              │
  └──────────────────────────────┘
```

**Strategy**: Position remanufacturing at same Y as input, but right side

**Excel Entry**:
```
Process_ID | Name              | X_Position | Y_Position
0          | Input             | 0.10       | 0.70
1          | Manufacturing     | 0.30       | 0.50
3          | Use Phase         | 0.50       | 0.50
7          | Remanufacturing   | 0.70       | 0.70  ← Same Y as Input
```

### Pattern 4: Hierarchical Multi-Stage (Complex Systems)

**Use Case**: CE-RISE type system with multiple processing stages

```
Stage 1:      Stage 2:       Stage 3:       Stage 4:
Input ──────► Processing ──► Use/DSM ──────► Recycling ──► Outputs
0.1           0.3            0.5            0.7           0.9

Within Stage 3 (Use):
  - Primary use:     Y = 0.7
  - Secondary use:   Y = 0.5
  - Tertiary use:    Y = 0.3
```

**Excel Entry**:
```
Process_ID | Name                | X_Position | Y_Position
0          | Input               | 0.10       | 0.50
1          | Manufacturing       | 0.30       | 0.50
3          | Use Phase (DSM)     | 0.50       | 0.70  ← Primary
5          | Decomissioning      | 0.50       | 0.50  ← Secondary
6          | Reuse               | 0.50       | 0.30  ← Tertiary
7          | Remanufacturing     | 0.70       | 0.60
8          | Waste Treatment     | 0.90       | 0.40
```

---

## Troubleshooting

### Problem: Nodes Are Overlapping

**Cause**: Positions too close together (< 0.1 units apart)

**Solution**:
1. Increase vertical spacing (Y-distance) between nodes
2. Or shift one node left/right (change X-position)
3. Or use `Node_Scale_Factor = 0.8` to make nodes smaller

### Problem: Flows Are Crossing Unnecessarily

**Cause**: Node order doesn't match flow topology

**Solution**:
1. Reorder Y-positions so nodes align with their connections
2. Move intermediate nodes to bridge between source and target
3. Use "Auto-Layout" mode temporarily to see optimal topology

### Problem: Custom Layout Doesn't Appear

**Cause**: Excel positions not loaded or Layout mode set to "Auto-Layout"

**Solution**:
1. Check that `visualization_config_path=input_file` is passed
2. Use Layout dropdown widget and select "Custom" mode
3. Verify Excel sheet `6_1_Visualization_Processes` exists and has position columns
4. Check for typos in column names (must be exact: `X_Position_Material`)

### Problem: Some Nodes Missing Element-Specific Positions

**Cause**: Not all `X_Position_[Element]` columns filled

**Solution**:
- Fill in missing element-specific columns, OR
- Leave empty to use Material positions as fallback (automatic)

### Problem: Diagram Too Small/Large

**Cause**: Zoom or window size incorrect

**Solution**:
1. Open `6_3_Layout_Configuration` sheet
2. Adjust `Zoom_Factor`:
   - Too small → Increase to 1.5 or 2.0
   - Too large → Decrease to 0.7 or 0.5
3. Or adjust `Window_Width` and `Window_Height` (in pixels)

### Problem: Nodes Too Thick/Thin

**Cause**: Node scale factor incorrect

**Solution**:
1. Open `6_3_Layout_Configuration` sheet
2. Adjust `Node_Scale_Factor`:
   - Too thin → Increase to 1.2 or 1.5
   - Too thick → Decrease to 0.7 or 0.8

---

## Example: CE-RISE Case Study Layout

### System Overview

Your CE-RISE system has these processes:
- 0: Materials and Parts Production (Input)
- 1: Manufacturing
- 2: Production_waste
- 3: Use Phase (DSM) ← **KEY PROCESS**
- 4: Repair
- 5: Decommissioning
- 6: Reuse
- 7: Remanufacturing ← **Cascading**
- 8: Waste Treatment
- 9: Spare parts production
- 10: Spare parts storage

### Recommended Layout for Publication

**Objective**: Highlight DSM process and show cascading utilization (Use → Repair → Remanufacturing → Reuse)

#### Material Element Layout

```excel
Process_ID | Name                           | Node_Color_# | X_Position | Y_Position
0          | Materials and Parts Production | #228B22      | 0.05       | 0.50
1          | Manufacturing                  | #F5DEB3      | 0.20       | 0.50
2          | Production_waste               | #6C757D      | 0.20       | 0.75
3          | Use Phase (DSM)                | #28A745      | 0.45       | 0.50  ← CENTER + GREEN
4          | Repair                         | #87CEEB      | 0.60       | 0.70  ← Upper cascade
5          | Decommissioning                | #87CEEB      | 0.60       | 0.50
6          | Reuse                          | #2E86AB      | 0.75       | 0.75  ← Top cascade
7          | Remanufacturing                | #2E86AB      | 0.75       | 0.55  ← Mid cascade
8          | Waste Treatment                | #6C757D      | 0.90       | 0.40  ← Output lower
9          | Spare parts production         | #F5DEB3      | 0.05       | 0.75
10         | Spare parts storage            | #87CEEB      | 0.20       | 0.85
```

**Key Features**:
- **DSM (Process 3)**: Centered (X=0.45, Y=0.50) with distinct green color
- **Cascading**: Vertical arrangement showing use hierarchy (Y: 0.75 → 0.70 → 0.55)
- **Input/Output**: Clear left (X=0.05) to right (X=0.90) flow
- **Secondary loops**: Production waste and spare parts positioned higher (Y > 0.7)

---

## Best Practices Summary

✅ **DO**:
- Plan layout on paper before editing Excel
- Use consistent X-positions for process stages
- Use Y-positions to separate parallel pathways
- Test frequently (Edit Excel → Save → Re-run notebook)
- Use distinct colors for special processes (DSM, FOMP)
- Use element-specific positions to show different flow pathways
- Keep coordinates between 0.05 and 0.95 (avoid edges)

❌ **DON'T**:
- Place nodes too close together (< 0.1 units)
- Use coordinates outside 0.0-1.0 range (will be clamped)
- Forget to save Excel file after editing
- Use too many different colors (creates visual clutter)
- Position key processes at diagram edges (hard to see)

---

## Quick Reference Card

### Common Coordinates

| Position          | X    | Y    |
|-------------------|------|------|
| Left-Top          | 0.1  | 0.8  |
| Left-Center       | 0.1  | 0.5  |
| Left-Bottom       | 0.1  | 0.2  |
| Center-Top        | 0.5  | 0.8  |
| Center-Center     | 0.5  | 0.5  |
| Center-Bottom     | 0.5  | 0.2  |
| Right-Top         | 0.9  | 0.8  |
| Right-Center      | 0.9  | 0.5  |
| Right-Bottom      | 0.9  | 0.2  |

### Standard Colors (Hex Codes)

| Color Name    | Hex Code | Use Case        |
|---------------|----------|-----------------|
| Forest Green  | #228B22  | Inputs          |
| Wheat Gold    | #F5DEB3  | Processing      |
| Light Blue    | #87CEEB  | Use phase       |
| Green (DSM)   | #28A745  | DSM special     |
| Brown (FOMP)  | #C73E1D  | FOMP special    |
| Blue          | #2E86AB  | Recycling       |
| Dark Gray     | #6C757D  | Waste/Output    |
| Purple        | #6F42C1  | Stocks          |

---

**Last Updated**: 2025-11-07
**Version**: 1.0
**Author**: BioDYM Development Team

For questions or issues, refer to:
- `CLAUDE.md` - Main project documentation
- `TROUBLESHOOTING.md` - Common issues and solutions
- `MULTIPLOT_SANKEY_USAGE.md` - Multi-element Sankey guide
