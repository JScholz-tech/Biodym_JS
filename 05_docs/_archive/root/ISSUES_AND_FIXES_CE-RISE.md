# CE-RISE Excel Template Analysis & Fixes

**File**: `251104_BioDYM_ODYM_´CE-RISE.xlsm`
**Date**: 2025-11-07
**System**: Heat Pump Circular Economy with DSM

---

## 🔴 **Critical Issues Found**

### Issue #1: OVERLAPPING PROCESSES ⚠️⚠️⚠️

**Severity**: CRITICAL - Makes diagram unreadable

#### Overlap Group 1: (0.01, 0.2)
- **Process 0**: Materials and Parts Production
- **Process 1**: Manufacturing

**Problem**: Two processes stacked at same position - completely overlap!

#### Overlap Group 2: (0.70, 0.6)
- **Process 7**: Remanufacturing
- **Process 8**: Waste Treatment

**Problem**: Two processes stacked - flows will cross confusingly!

### Issue #2: DSM NOT HIGHLIGHTED ⚠️⚠️

**Process 3: Use Phase (DSM)** - YOUR KEY STOCK PROCESS!

- **Current Color**: #F5DEB3 (Wheat Gold) - same as 6 other processes
- **Current Position**: (0.50, 0.2) - Lost among similar processes
- **Problem**: DSM process is indistinguishable from regular processing steps!

**This is your most important process** (Dynamic Stock Model showing heat pump accumulation over time) and it's **invisible**!

### Issue #3: POOR COLOR VARIETY

**Color Distribution**:
- **#8B4513** (Saddle Brown): **14 processes** ← Way too many!
- **#F5DEB3** (Wheat Gold): **7 processes**
- **#228B22** (Forest Green): 1 process
- **#87CEEB** (Sky Blue): 1 process

**Problem**:
- 61% of processes use the same brown color
- No differentiation between process types
- Cascading flow (Repair → Reuse → Remanufacturing) not visually distinct

### Issue #4: SPARSE LAYOUT

**Position Statistics**:
- Only **6 unique X positions** for 11 processes
- Only **4 unique Y positions** for 11 processes
- Many "layers" with multiple processes

**Problem**: Layout doesn't show the circular economy structure clearly

### Issue #5: EXTRA ROWS IN EXCEL

**Sheet `6_1_Visualization_Processes`** has:
- 4 rows with `Process_ID = NaN`
- Values: (0.70, 0.6), (0.70, 0.6), (0.01, 0.8), (0.90, 0.8)

**Problem**: These are leftover/template rows - should be deleted!

### Issue #6: NO FOMP PROCESSES

**Good News**: No FOMP processes in this system
**Note**: Only DSM (Process 3) needs highlighting

---

## ✅ **Recommended Solutions**

### Fix #1: Eliminate All Overlaps

**Separate overlapping processes**:

```excel
Process 0 (Input):          X=0.05, Y=0.50  (left-center)
Process 1 (Manufacturing):  X=0.15, Y=0.50  (slightly right)

Process 7 (Remanufacturing): X=0.75, Y=0.60  (right-upper)
Process 8 (Waste Treatment): X=0.90, Y=0.40  (far right-lower)
```

**Spacing**: Minimum 0.10 horizontal distance between all processes

### Fix #2: HIGHLIGHT DSM PROCESS ⭐

**Process 3 (Use Phase - DSM)**:

```excel
X_Position_Material: 0.50   (keep center - good position!)
Y_Position_Material: 0.50   (raise to mid-level for prominence)
Node_Color_#: #28A745       (BRIGHT GREEN - impossible to miss!)
```

**Why**:
- Bright green = Stock/accumulation (standard BioDYM convention)
- Center position (X=0.50) shows it's midpoint of circular flow
- Mid-height (Y=0.50) gives it prominence

### Fix #3: Improve Color Scheme

**Recommended Color Strategy**:

| Process Type | Color | Hex Code | Processes |
|--------------|-------|----------|-----------|
| **Inputs** | Forest Green | #228B22 | 0 (Materials), 9 (Spare Parts) |
| **Manufacturing** | Wheat Gold | #F5DEB3 | 1 (Manufacturing), 2 (Waste) |
| **DSM - Stock** | **Bright Green** | **#28A745** | **3 (Use Phase)** ⭐ |
| **Repair/Cascading** | Sky Blue | #87CEEB | 4 (Repair), 6 (Reuse) |
| **Remanufacturing** | Steel Blue | #4682B4 | 7 (Remanufacturing) |
| **Storage** | Light Slate Gray | #778899 | 5 (Decommissioning), 10 (Storage) |
| **Waste/Output** | Dim Gray | #696969 | 8 (Waste Treatment) |

**Key Changes**:
- DSM = Bright green (stands out!)
- Cascading (Repair/Reuse) = Blue tones (shows circularity)
- Manufacturing vs End-of-life clearly distinguished

### Fix #4: Optimized Layout for Circular Economy

**Circular Flow Visualization** (Heat Pump Life Cycle):

```
Stage 1: INPUT → Stage 2: PRODUCTION → Stage 3: USE → Stage 4: CASCADING → Stage 5: OUTPUT
X=0.05-0.15      X=0.25-0.35          X=0.50       X=0.65-0.80          X=0.90-0.95
```

**Vertical Layers** (Y-axis shows function):

```
Y=0.75+  Supporting: Spare Parts (9, 10)
Y=0.60   Cascading: Remanufacturing (7), Reuse (6)
Y=0.50   MAIN FLOW: Manufacturing (1) → USE/DSM (3) → Repair (4)
Y=0.40   End-of-Life: Waste Treatment (8), Decommissioning (5)
Y=0.30   By-products: Production Waste (2)
```

### Fix #5: Delete Extra Rows

**Action**: In Excel sheet `6_1_Visualization_Processes`:
- Delete all rows where `Process_ID` is blank/NaN
- Should have exactly 11 data rows (Process 0-10)

---

## 📊 **Complete Recommended Positions**

### Excel Sheet: `6_1_Visualization_Processes`

**Copy these values into your Excel file**:

| Process_ID | Name | X_Position_Material | Y_Position_Material | Node_Color_# | Rationale |
|------------|------|---------------------|---------------------|--------------|-----------|
| **0** | Materials and Parts Production | **0.05** | **0.50** | **#228B22** | Input - left side |
| **1** | Manufacturing | **0.25** | **0.50** | **#F5DEB3** | Primary processing |
| **2** | Production_waste | **0.25** | **0.30** | **#F5DEB3** | By-product - lower |
| **3** | Use Phase (DSM) ⭐ | **0.50** | **0.50** | **#28A745** | KEY STOCK - GREEN - CENTER |
| **4** | Repair | **0.65** | **0.50** | **#87CEEB** | Cascading - mid right |
| **5** | Decommissioning | **0.65** | **0.40** | **#778899** | End-of-use - lower |
| **6** | Reuse | **0.75** | **0.60** | **#87CEEB** | Cascading - upper |
| **7** | Remanufacturing | **0.75** | **0.70** | **#4682B4** | Cascading - highest |
| **8** | Waste Treatment | **0.90** | **0.40** | **#696969** | Output - far right |
| **9** | Spare parts production | **0.10** | **0.75** | **#228B22** | Supporting input - upper |
| **10** | Spare parts storage | **0.45** | **0.75** | **#778899** | Supporting storage - upper |

### Key Layout Features

**Horizontal Flow (X-axis)**:
```
0.05      0.25        0.50         0.65-0.75      0.90
Input → Production → USE/DSM → Repair/Reuse → Waste
                      (GREEN!)    (Cascading)
```

**Vertical Grouping (Y-axis)**:
```
Y=0.75  [Spare Parts Production (9)] ────→ [Spare Parts Storage (10)]
                                             ↓
Y=0.70                                  [Remanufacturing (7)]
                                             ↓
Y=0.60                                  [Reuse (6)]
                                             ↓
Y=0.50  [Input (0)] → [Mfg (1)] → [USE/DSM (3)] → [Repair (4)]
                          ↓            ↓              ↓
Y=0.40                [Decom (5)]                 [Waste (8)]
                          ↓
Y=0.30              [Prod Waste (2)]
```

**Visual**: Shows cascading clearly (Remanufacturing → Reuse → Repair) as vertical "waterfall" on right side!

---

## 🎨 **Layout Configuration Updates**

### Excel Sheet: `6_3_Layout_Configuration`

**Current values are actually GOOD**, but consider these tweaks:

| Setting | Current | Recommended | Why |
|---------|---------|-------------|-----|
| Window_Width | 1600 | **1800** | More horizontal space for clarity |
| Window_Height | 1200 | **1400** | More vertical space for cascading |
| Node_Scale_Factor | 1 | **1.3** | Thicker nodes for DSM visibility |
| Padding_Factor | 0.1 | **0.15** | More border space around diagram |

---

## 🔄 **Before vs After Comparison**

### BEFORE (Current Issues)

❌ Processes 0 & 1 overlap at (0.01, 0.2)
❌ Processes 7 & 8 overlap at (0.70, 0.6)
❌ DSM (Process 3) invisible - wheat color like 6 others
❌ 14 processes use same brown color
❌ No clear circular flow visible
❌ Cascading (Repair/Reuse/Reman) not differentiated
❌ Extra NaN rows clutter Excel

### AFTER (With Recommended Fixes)

✅ All 11 processes have unique positions
✅ DSM (Process 3) highlighted in BRIGHT GREEN
✅ 7 distinct colors showing process types
✅ Clear left→right flow with circular loops
✅ Cascading "waterfall" visible on right (Y: 0.70 → 0.60 → 0.50)
✅ Clean Excel with only valid rows
✅ Publication-ready for JIE

---

## 🚀 **Implementation Steps**

### Quick Fix (5 minutes)

**Minimum changes to make diagram readable**:

1. **Fix DSM color** (Process 3):
   ```excel
   Node_Color_#: #28A745  (change from #F5DEB3)
   ```

2. **Separate overlaps**:
   ```excel
   Process 0: X=0.05, Y=0.50  (was 0.01, 0.2)
   Process 1: X=0.25, Y=0.50  (was 0.01, 0.2)
   Process 7: X=0.75, Y=0.70  (was 0.70, 0.6)
   Process 8: X=0.90, Y=0.40  (was 0.70, 0.6)
   ```

3. **Delete NaN rows** in `6_1_Visualization_Processes`

**Result**: DSM visible, no overlaps!

### Complete Fix (15 minutes)

1. Open `251104_BioDYM_ODYM_´CE-RISE.xlsm`
2. Go to `6_1_Visualization_Processes`
3. **Delete rows** with Process_ID = NaN (4 rows)
4. **Update all positions** from table above
5. **Update all colors** from table above
6. Go to `6_3_Layout_Configuration`
7. Update: Window_Width=1800, Window_Height=1400, Node_Scale_Factor=1.3
8. **Save**
9. Re-run notebook section 3.1.2

---

## 📋 **CSV Import File**

I'll create a ready-to-paste CSV file for you...

---

## 🎯 **Expected Visual Result**

After implementing these changes, your Sankey will show:

```
Upper Level (Y=0.75):
[Spare Parts Prod] ───────→ [Spare Parts Storage]
                                      ↓
Main Flow (Y=0.50):                   ↓
[Input] → [Manufacturing] → [USE/DSM] → [Repair] ──┐
                ↓           (GREEN!)               │
                ↓                                   │
Lower (Y=0.30-0.40):                               │
          [Prod Waste]  [Decommissioning]          │
                              ↓                     │
                         [Waste Treatment] ←────────┤
                                                     │
Cascading "Waterfall" (Y: 0.70→0.60→0.50):         │
                                        [Remanufacturing] ← (Highest)
                                               ↓
                                          [Reuse]
                                               ↓
                                          (back to Repair) ←─┘
```

**Key Features**:
- **DSM (Use Phase) in bright green** - unmissable!
- **Circular loops clearly visible** (Repair→Use, Reuse→Use, Reman→Use)
- **Cascading hierarchy** shown vertically (Reman > Reuse > Repair)
- **Clean flow** from input (left) through use (center) to outputs (right)
- **Supporting flows** (spare parts) clearly separated at top

---

## ⚠️ **Critical Notes**

### 1. Why DSM Highlighting is Essential

**For JIE Publication**: Dynamic Stock Modeling (DSM) is a **methodological contribution**:
- Shows heat pump accumulation over 26 years (2025-2050)
- Tracks in-use stock with age-cohort structure
- Demonstrates BioDYM's advanced stock modeling

**Without highlighting**: Reviewers won't see that you're using DSM! It looks like a regular process.

**With bright green**: Immediately obvious you're modeling dynamic stocks - strengthens paper.

### 2. Cascading Visualization

Your system has **cascading utilization** (Repair → Reuse → Remanufacturing):
- Current layout: All same brown color, no hierarchy visible
- Recommended layout: Vertical "waterfall" with blue tones showing progression

**For JIE**: Cascading is a key circular economy strategy - needs to be visually obvious!

### 3. Color Accessibility

**Current**: 14 brown + 7 wheat = hard to distinguish
**Recommended**: 7 distinct colors that work in:
- Color printing
- Black & white (different brightness levels)
- Colorblind readers (blues vs greens vs grays)

---

## 📁 **Files Created**

I'm creating:
1. This analysis document (`ISSUES_AND_FIXES_CE-RISE.md`)
2. CSV import file (`recommended_positions_CE-RISE.csv`)
3. Visual reference guide (if needed)

---

**Priority**: URGENT - Current overlaps make diagram unusable!

**Recommended Action**: Implement "Quick Fix" immediately (5 min), then full fix when time permits.

**Last Updated**: 2025-11-07
