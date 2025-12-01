# Hierarchical Element Calculation Fix

## Problem Summary

**Bug**: After inputs stopped (e.g., year 2032), hierarchical elements (DM, CC) were "frozen" at constant values while Material continued to decrease from DSM decay.

**Root Cause**: The DSM outflow calculation set element fractions to 0 when inputs were 0, causing elements to become 0 or frozen. The code didn't preserve the last valid composition when inputs stopped.

For example, after 2032 when inputs stop:
```
Year 2032: Input=100, Material=1000, DM=880, CC=440
Year 2033: Input=0,   Material=950 (DSM decay)
           DM=0 (factor=0!), CC=0 (factor=0!)  ← FROZEN/WRONG!
```

**The Fix**: Forward-fill the last valid composition fractions:
```
Year 2033: Input=0, Material=950 (DSM decay)
           DM_factor=0.88 (from 2032), DM=950×0.88=836 ✓
           CC=DM×0.5=418 ✓ (hierarchical recalculation)
```

## Solution Implemented

### 1. Created Helper Function (`solver.py`)
- Added `recalculate_hierarchical_elements()` function
- Implements 2-pass calculation:
  - Pass 1: Top-level elements (% of material) - already calculated
  - Pass 2: Hierarchical elements - recalculated based on parent values
- Handles division by zero safely
- Works with any element hierarchy configuration

### 2. Fixed Splitter Process Logic (`solver.py:332-339`)
- Added hierarchical recalculation after applying TCs
- Ensures element fractions are preserved correctly through splits

### 3. Fixed Transformer Process Logic (`solver.py:362-375`)
- Added hierarchical recalculation before summing material
- Critical for processes that change composition

### 4. Fixed DSM Outflow Logic (`dsm_model.py:202-238`)
- **MOST CRITICAL FIX** - Forward-fills element fractions when inputs stop
- Preserves last valid composition instead of setting fractions to 0
- Elements now decrease proportionally with Material during DSM decay
- Hierarchical recalculation ensures CC stays proportional to DM

## Files Modified

1. `02_src/engine/element_utils.py` **[NEW FILE]**
   - Created new utilities module to avoid circular imports
   - Contains: `recalculate_hierarchical_elements()` function
   - Reusable across all engine modules

2. `02_src/engine/solver.py`
   - Added: Import of `recalculate_hierarchical_elements` from element_utils
   - Modified: Splitter logic (lines 332-339)
   - Modified: Transformer logic (lines 362-375)

3. `02_src/engine/dsm_model.py`
   - Added: Import of helper function from element_utils (line 12)
   - Modified: DSM outflow assignment (lines 212-224)

## Testing Instructions

### Quick Test
Run the notebook with your current file:
```python
# In cell: 1.2 Data Input Configuration
input_file = "01_data/01_input/251201_BioDYM_ODYM_Reifen.xlsm"

# Run through Section 2 (Calculation & Mass Balance)
# Check the results for years 2024-2042
```

### Expected Results

**Before Fix**:
- Material: Changes normally ✓
- DM: Changes normally ✓
- CC: **FROZEN at 2023 value** ✗

**After Fix**:
- Material: Changes normally ✓
- DM: Changes proportional to Material ✓
- CC: Changes proportional to DM ✓ **FIXED!**

### Verification

Check a DSM outflow in the results:
```python
# Example: Check flow F_09_11 (DSM outflow)
flow = mfa_results_baseline.FlowDict['F_09_11']
years = mfa_results_baseline.IndexTable.Classification['Time'].Items

import pandas as pd
df = pd.DataFrame({
    'Year': years,
    'Material': flow.Values[:, 0],
    'DM': flow.Values[:, 2],  # Element index 2
    'CC': flow.Values[:, 3],  # Element index 3
})

# Calculate ratios
df['DM/Material'] = df['DM'] / df['Material']
df['CC/DM'] = df['CC'] / df['DM']

print(df[df['Year'] >= 2020])
```

**Expected**:
- `DM/Material` ratio should stay constant (~0.88)
- `CC/DM` ratio should stay constant (~0.50)
- CC value should change proportionally with DM

## Flexibility

This fix makes the system **fully flexible** for any element hierarchy:

### Supported Hierarchies

**Biomass Example** (Current):
```
Material
├─ DM (dry matter)
│  └─ CC (carbon in DM)
└─ WC (water content)
```

**Metal Alloy Example** (Hypothetical):
```
Material
├─ Fe (iron)
│  └─ C (carbon in steel)
├─ Cu (copper)
└─ Al (aluminum)
```

**Complex Waste** (Hypothetical):
```
Material
├─ Organic
│  ├─ DM (dry organic)
│  │  └─ CC (carbon)
│  └─ WC (water)
└─ Inorganic
```

Any hierarchy defined in `0_Configuration` sheet will now work correctly!

## Backward Compatibility

- Non-hierarchical systems: No change in behavior
- Flat element structures: No performance impact
- Empty hierarchy: Helper function returns immediately

## Notes

- The fix preserves mass balance
- Works with all process types (Splitter, Transformer, DSM)
- No changes needed to Excel template format
- Configuration remains the same

## Author

Fix implemented by Claude Code
Date: 2025-12-01
Issue: Hierarchical elements frozen after input cessation
