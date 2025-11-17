# Layout Recommendations for ODYM_1 System

**File**: `251031_BioDYM_ODYM_1.xlsm`
**Date**: 2025-11-07
**System**: Rye-based biomass cascading with FOMP and DSM

---

## Current Issues

### ❌ Problems with Current Layout

1. **Severe Overlapping**: 7+ processes at position (0.70, 0.6)
   - Biogas_Incineration, MBC_Production, MBC_Use-Phase (DSM!), MBC-EoL_Treatment, Ash_Treatment

2. **DSM Not Highlighted**: Process 15 (MBC_Use-Phase) has same brown color (#8B4513) as regular processes
   - This is your KEY STOCK PROCESS - should stand out!

3. **FOMP Not Highlighted**: Process 5 (Rye-Straw degradation) looks like regular process
   - Should have distinct color for organic decay

4. **No Clear Flow**: Hard to see the cascading pathway:
   - Rye → Grain (food) + Straw → Biogas → MBC → Use → End-of-life

5. **Mixed Stages**: Inputs, processing, and outputs all scattered

---

## Recommended Layout Strategy

### System Flow Overview

```
STAGE 1: INPUTS → STAGE 2: PRODUCTION → STAGE 3: PROCESSING → STAGE 4: USE → STAGE 5: END-OF-LIFE → STAGE 6: OUTPUTS

Environment     Rye            Grain          Biogas          MBC           End-of-life      Atmosphere
Atmosphere      Cultivation    Processing     Production      Use-Phase     Treatment        Environment
                Harvest        Straw Use                      (DSM)         Pyrolysis
                               FOMP                                         Incineration
```

### Horizontal Staging (X-axis)

| Stage | X Range | Processes | Rationale |
|-------|---------|-----------|-----------|
| **1. Inputs** | 0.05-0.10 | 0 (Environment)<br>1 (Atmosphere)<br>20 (Water Import) | Sources - far left |
| **2. Primary Production** | 0.20-0.25 | 2 (Rye Cultivation)<br>3 (Rye Harvest) | Agricultural stage |
| **3. Primary Processing** | 0.35-0.40 | 4 (Grain Processing)<br>6 (Straw Use)<br>10 (Cow Manure)<br>14 (Millet) | Initial conversion |
| **4. Secondary Processing** | 0.50-0.55 | 5 (FOMP - Straw Degradation) ⭐<br>9 (Biogas Production)<br>11 (MBC Production) | Advanced processing |
| **5. Use Phase** | 0.68-0.72 | 15 (MBC Use-Phase - DSM) ⭐⭐ | KEY PROCESS - Stock |
| **6. End-of-Life** | 0.82-0.88 | 7 (Biogas Incineration)<br>16 (MBC-EoL Treatment)<br>17 (Pyrolysis)<br>18 (Incineration)<br>19 (Ash Treatment) | Disposal/recycling |
| **7. Outputs** | 0.95 | 21 (Water Export)<br>22 (Lithosphere Stock) | Sinks - far right |

### Vertical Grouping (Y-axis)

| Level | Y Range | Purpose | Processes |
|-------|---------|---------|-----------|
| **Upper** | 0.75-0.85 | Supporting flows | Water (20, 21), Manure (10), Millet (14), Lithosphere (22) |
| **Mid-High** | 0.60-0.70 | MBC pathway | MBC Production (11), **MBC Use (15)**, MBC EoL (16, 17, 18) |
| **Mid** | 0.45-0.55 | Main biomass flow | Grain (4), Straw Use (6), Biogas (7, 9) |
| **Mid-Low** | 0.30-0.40 | Primary production | Cultivation (2), Harvest (3) |
| **Lower** | 0.15-0.25 | FOMP & emissions | **FOMP (5)**, Atmosphere (1), Environment (0) |

---

## Detailed Position Recommendations

### Excel Sheet: `6_1_Visualization_Processes`

Copy these values into your Excel file:

| Process_ID | Name | X_Position_Material | Y_Position_Material | Node_Color_# | Rationale |
|------------|------|---------------------|---------------------|--------------|-----------|
| **0** | Environment | **0.05** | **0.20** | **#228B22** | Input - bottom left |
| **1** | Atmosphere | **0.05** | **0.15** | **#87CEEB** | Input - near environment |
| **2** | Rye_Cultivation | **0.20** | **0.35** | **#90EE90** | Primary production - light green |
| **3** | Rye_Harvest | **0.25** | **0.35** | **#90EE90** | After cultivation |
| **4** | Rye-Grain Processing | **0.35** | **0.50** | **#F5DEB3** | Processing - main flow |
| **5** | Rye-Straw FOMP ⭐ | **0.50** | **0.25** | **#C73E1D** | FOMP - brown/red, lower (decay) |
| **6** | Rye-Straw Use | **0.38** | **0.45** | **#F5DEB3** | Straw utilization |
| **7** | Biogas Incineration | **0.85** | **0.50** | **#6C757D** | End-of-life - gray |
| **8** | Biogas Production-Delta | **0.48** | **0.52** | **#F5DEB3** | Near biogas prod |
| **9** | Biogas Production | **0.50** | **0.50** | **#F5DEB3** | Secondary processing |
| **10** | Cow-Manure Production | **0.35** | **0.80** | **#8B4513** | Supporting - upper |
| **11** | MBC Production | **0.55** | **0.65** | **#F5DEB3** | Pre-use processing |
| **12** | MBC Production Waste | **0.53** | **0.72** | **#6C757D** | Waste - gray |
| **13** | MBC Production-Delta | **0.52** | **0.68** | **#F5DEB3** | Near MBC prod |
| **14** | Millet Production | **0.38** | **0.82** | **#8B4513** | Supporting - upper |
| **15** | MBC Use-Phase (DSM) ⭐⭐ | **0.70** | **0.65** | **#28A745** | DSM - BRIGHT GREEN - centered |
| **16** | MBC-EoL Treatment | **0.82** | **0.65** | **#6C757D** | End-of-life - gray |
| **17** | MBC-EoL Pyrolysis | **0.85** | **0.70** | **#6C757D** | EoL option 1 |
| **18** | MBC-EoL Incineration | **0.85** | **0.60** | **#6C757D** | EoL option 2 |
| **19** | Ash Treatment | **0.88** | **0.65** | **#808080** | Final treatment |
| **20** | Water Import | **0.05** | **0.80** | **#1E90FF** | Input - blue water |
| **21** | Water Export | **0.95** | **0.80** | **#4682B4** | Output - blue water |
| **22** | Lithosphere Stock | **0.95** | **0.20** | **#654321** | Output - soil |

---

## Color Strategy (Publication-Ready)

### Special Processes

| Process Type | Color Name | Hex Code | Processes |
|--------------|------------|----------|-----------|
| **DSM (Stock)** | Bright Green | **#28A745** | 15 (MBC Use-Phase) |
| **FOMP (Decay)** | Earth Brown | **#C73E1D** | 5 (Rye-Straw Degradation) |

### Process Categories

| Category | Color Name | Hex Code | Processes |
|----------|------------|----------|-----------|
| **Inputs (Natural)** | Forest Green | #228B22 | 0 (Environment) |
| **Inputs (Atmosphere)** | Sky Blue | #87CEEB | 1 (Atmosphere) |
| **Inputs (Water)** | Dodger Blue | #1E90FF | 20 (Water Import) |
| **Primary Production** | Light Green | #90EE90 | 2, 3 (Cultivation, Harvest) |
| **Processing** | Wheat Gold | #F5DEB3 | 4, 6, 8, 9, 11, 13 |
| **Supporting Flows** | Saddle Brown | #8B4513 | 10, 14 (Manure, Millet) |
| **End-of-Life** | Dim Gray | #6C757D | 7, 12, 16, 17, 18 |
| **Final Treatment** | Gray | #808080 | 19 (Ash) |
| **Outputs (Water)** | Steel Blue | #4682B4 | 21 (Water Export) |
| **Outputs (Soil)** | Dark Brown | #654321 | 22 (Lithosphere) |

---

## Layout Configuration Settings

### Excel Sheet: `6_3_Layout_Configuration`

Recommended settings for publication:

| Setting | Recommended Value | Current | Rationale |
|---------|-------------------|---------|-----------|
| **Window_Width** | **2000** | 1600 | Wider for better spacing |
| **Window_Height** | **1400** | 1200 | Taller for vertical space |
| **Zoom_Factor** | **1.0** | 1.0 | Keep normal - let auto-fit work |
| **Node_Scale_Factor** | **1.2** | 1.0 | Slightly thicker nodes for visibility |
| **Auto_Fit_Frame** | **TRUE** | TRUE | Keep enabled |
| **Padding_Factor** | **0.12** | 0.1 | Slightly more border space |

---

## Key Features of Recommended Layout

### ✅ Clear Cascading Flow

```
Rye (0.20-0.25) → Processing (0.35-0.40) → Biogas (0.50) → MBC (0.55-0.70) → EoL (0.82-0.88)
     ↓ Y=0.35           ↓ Y=0.50              ↓ Y=0.50        ↓ Y=0.65         ↓ Y=0.65
```

Left-to-right progression clearly shows material cascade.

### ✅ DSM Process Highlighted

**Process 15 (MBC Use-Phase)**:
- **Position**: (0.70, 0.65) - Center-right, prominent
- **Color**: #28A745 - Bright green, stands out from all others
- **Purpose**: KEY STOCK - Material accumulation visible

### ✅ FOMP Process Highlighted

**Process 5 (Rye-Straw Degradation)**:
- **Position**: (0.50, 0.25) - Mid-left, lower (shows decay to soil)
- **Color**: #C73E1D - Earth brown/red, distinct from processing
- **Purpose**: Organic mineralization clearly differentiated

### ✅ No Overlaps

Every process has unique position:
- Minimum horizontal spacing: 0.03 units
- Minimum vertical spacing: 0.05 units
- Special processes have extra space (0.1+ units)

### ✅ Functional Grouping

**Y-position groups processes by function**:
- Supporting flows (top, Y ≈ 0.8)
- MBC pathway (upper-mid, Y ≈ 0.65)
- Main biomass (mid, Y ≈ 0.45-0.50)
- Primary production (lower-mid, Y ≈ 0.35)
- FOMP/emissions (bottom, Y ≈ 0.15-0.25)

---

## Implementation Steps

### Step 1: Backup Your File

```bash
# Copy current file before changes
cp "01_data/01_input/251031_BioDYM_ODYM_1.xlsm" "01_data/01_input/251031_BioDYM_ODYM_1_BACKUP.xlsm"
```

### Step 2: Update Excel Positions

1. Open `251031_BioDYM_ODYM_1.xlsm`
2. Go to sheet `6_1_Visualization_Processes`
3. Update columns `X_Position_Material`, `Y_Position_Material`, `Node_Color_#` with values from table above
4. **Focus on these key changes**:
   - **Process 15**: X=0.70, Y=0.65, Color=#28A745 (DSM - GREEN)
   - **Process 5**: X=0.50, Y=0.25, Color=#C73E1D (FOMP - BROWN)
   - **Spread out overlapping processes**: Separate 7, 8, 11, 12, 15, 16, 19

### Step 3: Update Layout Configuration

Go to sheet `6_3_Layout_Configuration`:
- **Window_Width**: 2000
- **Window_Height**: 1400
- **Node_Scale_Factor**: 1.2
- **Padding_Factor**: 0.12

### Step 4: Save and Test

1. Save Excel file
2. Convert Python script to notebook: `jupytext --to notebook 00_BioDYM_Workflow.py`
3. Run notebook section 3.1.2 (Enhanced Sankey)
4. Enable "Show Coordinates" checkbox to verify positions
5. Toggle Layout between "Auto" and "Custom" to compare

### Step 5: Refine if Needed

- Adjust Y-positions if flows still cross
- Modify colors if visibility is poor
- Change spacing if nodes too close/far

---

## Visual Mockup (ASCII)

```
Y=0.85  [Water(20)]──────────────────────────────────────────────────────→[Water(21)]
         [Manure(10)]        [Millet(14)]

Y=0.70                                  [MBC Prod(11)]──→[DSM-15]──→[EoL(16,17,18)]──→[Ash(19)]
                                           (wheat)        (GREEN!)      (gray)          (gray)

Y=0.50              [Grain(4)]    [Straw(6)]  [Biogas(9)]                    [Biogas Incin(7)]
                     (wheat)       (wheat)      (wheat)                         (gray)

Y=0.35         [Cultivation(2)]──→[Harvest(3)]
                (light green)      (light green)

Y=0.25  [Env(0)]                        [FOMP(5)]
        [Atm(1)]                     (BROWN/RED!)                            [Litho(22)]

         X=0.05     0.20    0.35    0.50      0.70      0.82        0.95
         Input    Primary  Process  Second.   USE      End-of-Life  Output
```

**Key Visual Features**:
- DSM (Process 15) at X=0.70 in BRIGHT GREEN - impossible to miss!
- FOMP (Process 5) at bottom (Y=0.25) in EARTH BROWN - shows decay to soil
- Clear left→right flow progression
- Vertical separation prevents overlaps
- Cascading visible: Rye → processing → MBC → use → disposal

---

## Publication Benefits

### For Journal of Industrial Ecology Submission

1. **Methodological Clarity**: DSM and FOMP processes visually distinct
2. **Cascading Visible**: Clear material cascade from biomass → biogas → MBC
3. **System Structure**: Functional stages (production → use → EoL) obvious
4. **Professional**: No overlaps, clean layout, publication colors

### Figure Caption Suggestion

> **Figure X. Sankey diagram of the rye-based biomass cascading system.**
> The system tracks material flows from cultivation through multiple utilization stages,
> including Dynamic Stock Modeling (DSM, green node) for MBC use-phase accumulation and
> First-Order Mineralization Process (FOMP, brown node) for straw degradation. Node
> positions are optimized to show the cascading hierarchy from primary biomass production
> through secondary biogas generation to tertiary MBC utilization. Colors distinguish
> process types: green (agriculture), wheat (processing), gray (end-of-life), bright
> green (DSM stock), and brown (FOMP decay).

---

## Comparison: Before vs After

### Before (Current Layout)

❌ **Issues**:
- 7 processes at (0.70, 0.6) - impossible to distinguish
- DSM uses same brown color as 10 other processes
- FOMP looks like regular processing
- No clear flow direction
- Inputs and outputs scattered

### After (Recommended Layout)

✅ **Improvements**:
- Every process has unique position
- DSM (15) stands out in bright green at prominent location (0.70, 0.65)
- FOMP (5) clearly differentiated with earth brown at bottom (0.50, 0.25)
- Left-to-right cascade clearly visible
- Functional grouping by Y-position
- Publication-ready colors and spacing

---

## Quick Start: Minimal Changes

**If you only want to fix the most critical issues**, change ONLY these 5 things:

### Critical Fixes

| Process | Current X | Current Y | Current Color | → New X | → New Y | → New Color |
|---------|-----------|-----------|---------------|---------|---------|-------------|
| **15 (DSM)** | 0.70 | 0.6 | #8B4513 | **0.70** | **0.65** | **#28A745** |
| **5 (FOMP)** | 0.20 | 0.5 | #F5DEB3 | **0.50** | **0.25** | **#C73E1D** |
| **11 (MBC Prod)** | 0.70 | 0.6 | #8B4513 | **0.55** | **0.65** | **#F5DEB3** |
| **16 (MBC EoL)** | 0.70 | 0.6 | #8B4513 | **0.82** | **0.65** | **#6C757D** |
| **7 (Biogas Incin)** | 0.70 | 0.6 | #8B4513 | **0.85** | **0.50** | **#6C757D** |

These 5 changes will:
✅ Eliminate the worst overlap (0.70, 0.6)
✅ Highlight DSM with green
✅ Highlight FOMP with brown
✅ Separate end-of-life processes

---

**Last Updated**: 2025-11-07
**Status**: Ready for implementation
**Priority**: HIGH - Current layout has severe overlaps
