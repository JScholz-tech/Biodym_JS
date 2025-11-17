# QUICK FIX: CE-RISE Excel Template

**⏱️ 5 Minutes to Fix Critical Issues**

---

## 🔴 **Top 3 Critical Problems**

### 1. OVERLAPPING PROCESSES (Makes diagram unreadable!)

**At position (0.01, 0.2)**:
- Process 0 + Process 1 = STACKED!

**At position (0.70, 0.6)**:
- Process 7 + Process 8 = STACKED!

### 2. DSM INVISIBLE (Your key methodological contribution!)

**Process 3 (Use Phase - DSM)**:
- Current: Wheat color (#F5DEB3) - same as 6 other processes
- **PROBLEM**: Nobody can tell it's your DSM stock process!

### 3. TOO MUCH BROWN (14 out of 23 processes!)

- Makes cascading flow (Repair → Reuse → Reman) invisible
- No visual distinction between process types

---

## ✅ **QUICK FIX: Change Only 5 Values**

### Open Excel: `6_1_Visualization_Processes`

#### Fix #1: Process 3 (DSM) - MAKE IT GREEN!

```excel
Row with Process_ID = 3:
Node_Color_# → Change to: #28A745
```

**Result**: DSM now BRIGHT GREEN - impossible to miss!

#### Fix #2: Separate Overlap Group 1

```excel
Row with Process_ID = 0:
X_Position_Material → Change to: 0.05
Y_Position_Material → Change to: 0.50

Row with Process_ID = 1:
X_Position_Material → Change to: 0.25
Y_Position_Material → Change to: 0.50
```

**Result**: Input and Manufacturing now separated!

#### Fix #3: Separate Overlap Group 2

```excel
Row with Process_ID = 7:
X_Position_Material → Change to: 0.75
Y_Position_Material → Change to: 0.70

Row with Process_ID = 8:
X_Position_Material → Change to: 0.90
Y_Position_Material → Change to: 0.40
```

**Result**: Remanufacturing and Waste Treatment separated!

#### Fix #4: Delete Extra Rows

```excel
Find rows where Process_ID is blank/NaN → DELETE them
```

**Should have**: Exactly 11 data rows (Process 0-10)

---

## 📊 **Before vs After**

### BEFORE (Current)
```
Position (0.01, 0.2): TWO PROCESSES OVERLAPPING! ❌
Position (0.70, 0.6): TWO PROCESSES OVERLAPPING! ❌
DSM Process: Wheat color (invisible among 6 others) ❌
```

### AFTER (5-Minute Fix)
```
All positions unique ✅
DSM Process: BRIGHT GREEN (stands out!) ✅
Diagram readable ✅
```

---

## 💾 **Save & Test**

1. Save Excel file
2. Run notebook section 3.1.2 (Enhanced Sankey)
3. Look for **BRIGHT GREEN node** = That's your DSM!
4. Enable "Show Coordinates" checkbox to verify positions

---

## 🎯 **What You'll See**

The DSM process (Use Phase) will now be:
- **Bright green** node in the center
- Clearly separated from all other processes
- Visually obvious as your key stock process

Perfect for JIE publication! ✅

---

## ⏭️ **Optional: Complete Fix** (15 minutes)

For full optimization, see:
- `ISSUES_AND_FIXES_CE-RISE.md` - Complete analysis
- `recommended_positions_CE-RISE.csv` - All optimized positions

---

**Last Updated**: 2025-11-07
**Priority**: URGENT - Do this before running notebook!
