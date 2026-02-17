# Excel Configuration Reference for Enhanced Sankey

**Quick Reference**: All available configuration options from your Excel file

---

## Sheet: `6_3_Layout_Configuration`

### Spatial Layout Options

| Setting | Default | Description | Your Value |
|---------|---------|-------------|------------|
| **Circular_Center_X** | 0.5 | Center X position for circular layout (0.0 to 1.0) | 0.5 |
| **Circular_Center_Y** | 0.5 | Center Y position for circular layout (0.0 to 1.0) | 0.5 |
| **Circular_Radius** | 0.3 | Radius for circular layout (0.1 to 0.5) | 0.3 |
| **Node_Spacing** | 0.1 | Minimum spacing between nodes (0.05 to 0.2) | 0.1 |

### Visual Styling

| Setting | Default | Description | Your Value |
|---------|---------|-------------|------------|
| **Background_Color** | #FFFFFF | Background color (Hex code) | #FFFFFF |
| **Grid_Color** | #E0E0E0 | Grid color (Hex code) | #E0E0E0 |

### Window Dimensions

| Setting | Default | Description | Your Value |
|---------|---------|-------------|------------|
| **Window_Width** | 1600 | Sankey diagram width in pixels | 1600 |
| **Window_Height** | 1200 | Sankey diagram height in pixels | 1200 |

### Zoom & Scaling (Active)

| Setting | Default | Description | Your Value | Status |
|---------|---------|-------------|------------|--------|
| **Zoom_Factor** | 1.0 | Overall zoom (1.0 = normal, 0.5 = half, 2.0 = double) | 1 | ✅ Active |
| **Node_Scale_Factor** | 1.0 | Node size scale (1.0 = normal, 0.8 = smaller, 1.2 = larger) | 1 | ✅ Active |
| **Auto_Fit_Frame** | TRUE | Automatically adjust zoom to fit all flows | TRUE | ✅ Active |
| **Min_Zoom_Factor** | 0.3 | Minimum zoom to prevent too small diagrams | 0.3 | ✅ Active |
| **Max_Zoom_Factor** | 3.0 | Maximum zoom to prevent too large diagrams | 3 | ✅ Active |
| **Padding_Factor** | 0.1 | Extra padding around diagram (fraction of frame) | 0.1 | ✅ Active |

---

## Sheet: `6_1_Visualization_Processes`

### Process Node Configuration

Each process can have:

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| **Process_ID** | Integer | Process ID (from 2_1_Definition_Processes) | 3 |
| **Name(EN)** | Text | Process name for reference | Use Phase |
| **Color_Category** | Text | Category label for grouping | Biomass & Natural |
| **Node_Color** | Text | Color name for reference | Wheat Gold |
| **Node_Color_#** | Hex | Node color (Hex code) | #F5DEB3 |
| **X_Position_Material** | Float | X coordinate for Material element | 0.50 |
| **Y_Position_Material** | Float | Y coordinate for Material element | 0.20 |
| **X_Position_[Element]** | Float | X coordinate for specific element | 0.45 |
| **Y_Position_[Element]** | Float | Y coordinate for specific element | 0.30 |
| **Description** | Text | Optional notes | (empty) |

**Element-Specific Positions Available**:
- `X_Position_Material` / `Y_Position_Material`
- `X_Position_CU` / `Y_Position_CU`
- `X_Position_Fe` / `Y_Position_Fe`
- `X_Position_Al` / `Y_Position_Al`
- `X_Position_WC` / `Y_Position_WC` (if using)
- `X_Position_DM` / `Y_Position_DM` (if using)
- `X_Position_CC` / `Y_Position_CC` (if using)

---

## Sheet: `6_2_Visualization_Flows`

### Flow Styling Configuration

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| **Flow_ID** | Text | Flow ID (from 1_1_Definition_Flows) | F_01_03 |
| **Flow_Name** | Text | Flow name for reference | Input to Use |
| **Flow_Color_#** | Hex | Flow color (Hex code) | #00C851 |

---

## How These Settings Are Used

### 1. Position Loading (`X_Position_*` / `Y_Position_*`)

**Element-specific priority**:
1. First tries `X_Position_[Element]` (e.g., `X_Position_CU`)
2. Falls back to `X_Position_Material` if element-specific not found
3. Uses 0.5 (center) as final default

**⚠️ NEW: No Clamping** - Positions are no longer limited to [0.0, 1.0]:
- You can use negative values (e.g., -0.2) to position nodes outside standard frame
- You can use values > 1.0 (e.g., 1.3) to extend beyond frame
- Useful for special layouts or emphasizing certain flows

### 2. Zoom & Scaling (`6_3_Layout_Configuration`)

**Auto_Fit_Frame = TRUE** (Your Setting):
- Automatically centers and scales all nodes to fit in frame
- Calculates bounding box of all positions
- Applies zoom and centering transformation
- Respects `Padding_Factor` for border space

**Zoom_Factor** (multiplied with Auto_Fit):
- Adjusts final size after auto-fit
- `Zoom_Factor = 2.0` → Everything 2× larger
- `Zoom_Factor = 0.5` → Everything 2× smaller

**Node_Scale_Factor**:
- Scales node thickness and padding independently
- Does NOT affect node positions
- `Node_Scale_Factor = 1.5` → Thicker nodes, more visible

### 3. Window Dimensions

**Window_Width** and **Window_Height**:
- Set figure size in pixels
- Current: 1600 × 1200 px (standard widescreen)
- Increase for higher resolution exports
- Decrease for notebook display

### 4. Color Loading

**Node colors** (`Node_Color_#`):
- Loaded from `6_1_Visualization_Processes`
- Applied to each process node
- Hex format: `#RRGGBB`

**Flow colors** (`Flow_Color_#`):
- Loaded from `6_2_Visualization_Flows`
- Applied to specific flows by Flow_ID
- Falls back to element default if not specified

---

## New Features (2025-11-07)

### ✅ Free Positioning (No Clamping)
- Positions no longer restricted to [0.0, 1.0] range
- Can position nodes outside visible frame if desired
- Useful for creating custom layouts

### ✅ Coordinate Display
- New checkbox: **"Show Coordinates"**
- Displays (X, Y) values above each node
- Shows **original positions** from Excel (before auto-fit scaling)
- Only visible in "Custom" layout mode

### ✅ Multiplot Removed
- Removed from workflow to focus on single enhanced Sankey
- Can still be used via direct function call if needed

---

## Quick Tips

### Highlighting Special Processes

**DSM Process** (Use Phase):
```excel
Process_ID: 3
Node_Color_#: #28A745  (Green - stands out)
X_Position_Material: 0.45  (Center-left)
Y_Position_Material: 0.50  (Vertical center)
```

**Cascading Flows** (Reuse → Repair → Remanufacturing):
```excel
Process 6 (Reuse):          X=0.75, Y=0.75  (Top right)
Process 4 (Repair):         X=0.60, Y=0.70  (Mid-high)
Process 7 (Remanufacturing): X=0.75, Y=0.55  (Mid right)
```

### Testing Position Changes

1. Edit Excel `6_1_Visualization_Processes`
2. Save Excel file
3. Re-run notebook cell with `plotting.plot_enhanced_sankey(...)`
4. Enable "Show Coordinates" checkbox to verify positions
5. Adjust until satisfied

### Troubleshooting Display

**Nodes too small?**
- Increase `Node_Scale_Factor` in `6_3_Layout_Configuration`

**Diagram too crowded?**
- Increase `Window_Width` and `Window_Height`
- Or decrease `Zoom_Factor`

**Flows overlapping?**
- Adjust Y-positions to separate vertical pathways
- Use free positioning (negative/> 1.0 values) to space out

**Can't see coordinates?**
- Check "Show Coordinates" checkbox
- Make sure Layout mode = "Custom" (not "Auto-Layout")

---

## Example: Your CE-RISE System

### Current Configuration (From Excel)

```
Process 0 (Materials & Parts): X=0.01, Y=0.20, Color=#228B22
Process 1 (Manufacturing):      X=0.01, Y=0.20, Color=#F5DEB3
Process 3 (Use Phase - DSM):    X=0.50, Y=0.20, Color=#F5DEB3  ← CENTER
Process 4 (Repair):             X=0.10, Y=0.50, Color=#F5DEB3
Process 7 (Remanufacturing):    X=0.70, Y=0.60, Color=#8B4513
Process 8 (Waste Treatment):    X=0.70, Y=0.60, Color=#F5DEB3
```

### Recommended Changes for JIE Publication

**Highlight DSM** (Process 3):
```excel
Process_ID: 3
Node_Color_#: #28A745  ← Change to bright green
X_Position_Material: 0.45  ← Keep center-ish
Y_Position_Material: 0.50  ← Move to vertical center for prominence
```

**Create Cascading Hierarchy**:
```excel
Process 4 (Repair):          Y=0.70  ← Upper cascade
Process 6 (Reuse):           Y=0.75  ← Top cascade
Process 7 (Remanufacturing): Y=0.55  ← Mid cascade
```

**Spread Horizontally** (avoid overlap):
```excel
Process 0 (Input):    X=0.10
Process 1 (Mfg):      X=0.25
Process 3 (Use/DSM):  X=0.45
Process 4-7 (EOL):    X=0.60-0.75
Process 8 (Output):   X=0.90
```

---

**Last Updated**: 2025-11-07
**Version**: 1.0
**Status**: Active configuration loaded from Excel
