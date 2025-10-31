# Element Hierarchy Design - Dynamic Header System

## ✅ STATUS: IMPLEMENTED (2025-10-31)

This document describes the **flexible, element-agnostic architecture** implemented in BioDYM where the configuration sheet (`0_Configuration`) is the **single source of truth** for all element definitions.

---

## Overview

BioDYM now supports dynamic element definitions that work with:
- **Biomass systems**: material, WC, DM, CC
- **Metal recycling**: material, Fe, Cu, Al, Zn
- **Any custom elements**: material, protein, lipids, carbohydrates, etc.

### Key Innovation

**Config is the single source of truth** → Excel headers use generic E1, E2, E3, E4 format → Code automatically maps elements to columns

---

## Implementation

### 1. Configuration Structure (`0_Configuration` Sheet)

**Element definitions with hierarchy**:
```
Row 29: Element_ID_1        material
Row 30: Element_ID_2        WC
Row 31: Parent_Element_ID_2 material
Row 32: Element_ID_3        DM
Row 33: Parent_Element_ID_3 material
Row 34: Element_ID_4        CC
Row 35: Parent_Element_ID_4 DM        ← Hierarchical relationship!
```

**Key points**:
- `Element_ID_X`: Defines element name (WC, DM, CC, Fe, Cu, etc.)
- `Parent_Element_ID_X`: Defines hierarchical relationships
  - Example: CC is % of DM, not material
- Numbers (X) map to Excel columns (E1, E2, E3, E4)

### 2. Generic Excel Column Headers (`1_1_Definition_Flows` Sheet)

**New generic format**:
| Flow_ID | Flow_Name | Flow_E1_[%](material) | Flow_E2_[%](WC) | Flow_E3_[%](DM) | Flow_E4_[%](CC) |
|---------|-----------|------------------------|-----------------|-----------------|-----------------|
| F_01_02 | Straw     | 1.0                    | 0.15            | 0.85            | 0.45            |

**Benefits**:
- `E1, E2, E3, E4` are **generic placeholders**
- Element names in parentheses `(WC)` are **optional helper labels**
- Same Excel template works for **any element set**
- Change biomass to metals? Just update config, same Excel structure!

### 3. Automatic Column Mapping (Implemented)

**File**: `02_src/system_setup.py:428-504`

**Priority order for detecting columns**:
1. ✅ **New E{id} format with labels**: `Flow_E2_[%](WC)`
2. **New E{id} simple**: `Flow_E2[%]` or `Flow_E2_[%]`
3. **Legacy element name**: `Flow_WC[%]` or `Flow_WC_[%]`
4. **Special cases**: `Flow_CC_DM[%]` (backward compatibility)

**Code snippet**:
```python
def _build_element_column_map(elements, content_definitions):
    """Dynamically maps element names to Excel columns."""
    for elem_idx, element in enumerate(elements):
        element_id = elem_idx + 1  # 1-based for Excel

        # Try: Flow_E2_[%](WC)
        if f"Flow_E{element_id}_[%]({element})" in columns:
            column_map[element] = f"Flow_E{element_id}_[%]({element})"

        # Handle Excel duplicate suffix: Flow_E3_[%](DM)2
        matching = [col for col in columns
                    if col.startswith(f"Flow_E{element_id}_[%]({element})")]
        if matching:
            column_map[element] = matching[0]

        # Fallback to legacy: Flow_WC[%]
        # ... (see full implementation in system_setup.py)
```

**Handles edge cases**:
- Excel duplicate column suffixes (e.g., `Flow_E3_[%](DM)2`)
- Missing columns (warns but doesn't fail)
- Mixed old/new formats (backward compatible)

---

## Element Hierarchy Support

### What Is It?

Express one element as **percentage of another element**, not always material.

**Example - Carbon Content (CC)**:
- CC is % of Dry Matter (DM), **not** % of material
- Configuration: `Parent_Element_ID_4 = DM`

**Calculation**:
```
Flow: 100 Mg material
- DM = 85% of material = 85 Mg
- CC = 45% of DM = 0.45 × 85 = 38.25 Mg  ← Note: 45% of DM, not material!
```

### Config Loading (Implemented)

**File**: `02_src/config.py:64-128`

```python
# First pass: collect Element_ID_X
for key in config_dict.keys():
    if key.startswith('Element_ID_'):
        element_num = int(key.split('_')[-1])
        element_structure[element_num] = {
            'name': element_value,
            'parent': None
        }

# Second pass: collect Parent_Element_ID_X
for key in config_dict.keys():
    if key.startswith('Parent_Element_ID_'):
        element_num = int(key.split('_')[-1])
        element_structure[element_num]['parent'] = parent_value

config_dict['Element_Hierarchy'] = element_structure
```

**Output**:
```python
Element_Hierarchy = {
    1: {'name': 'material', 'parent': None},
    2: {'name': 'WC', 'parent': 'material'},
    3: {'name': 'DM', 'parent': 'material'},
    4: {'name': 'CC', 'parent': 'DM'}  ← Hierarchy!
}
```

---

## Data Flow

```
1. User defines elements in config
   └─> Element_ID_1 = material
   └─> Element_ID_2 = WC, Parent = material
   └─> Element_ID_3 = DM, Parent = material
   └─> Element_ID_4 = CC, Parent = DM
        ↓
2. config.py loads hierarchy
   └─> Element_Hierarchy dict created
   └─> Stored in config object
        ↓
3. User defines flows with E{id} columns
   └─> Flow_E2_[%](WC) = 0.15
   └─> Flow_E3_[%](DM) = 0.85
   └─> Flow_E4_[%](CC) = 0.45  (% of DM!)
        ↓
4. system_setup.py maps columns
   └─> WC → Flow_E2_[%](WC)
   └─> DM → Flow_E3_[%](DM)2  (handles Excel suffix)
   └─> CC → Flow_E4_[%](CC)
        ↓
5. Parameters created for each flow
   └─> WC_F_01_02 = 0.15
   └─> DM_F_01_02 = 0.85
   └─> CC_F_01_02 = 0.45
        ↓
6. Composition calculated (currently flat)
   └─> Flow.Values[:, 2] = material × 0.15  (WC)
   └─> Flow.Values[:, 3] = material × 0.85  (DM)
   └─> Flow.Values[:, 4] = material × 0.45  (CC)
   └─> ⚠️ TODO: Use parent hierarchy (CC should be DM × 0.45)
```

---

## Usage Examples

### Example 1: Biomass System (Current Implementation)

**Configuration (`0_Configuration`)**:
```
Element_ID_1 = material
Element_ID_2 = WC       (Water Content)
Element_ID_3 = DM       (Dry Matter)
Element_ID_4 = CC       (Carbon Content)
Parent_Element_ID_4 = DM
```

**Excel Columns (`1_1_Definition_Flows`)**:
```
Flow_E1_[%](material) | Flow_E2_[%](WC) | Flow_E3_[%](DM) | Flow_E4_[%](CC)
         1.0          |      0.15       |      0.85       |      0.45
```

**Result**: Tracks total mass, water, dry matter, carbon with CC hierarchy.

### Example 2: Metal Recycling (Future)

**Configuration**:
```
Element_ID_1 = material
Element_ID_2 = Fe
Element_ID_3 = Cu
Element_ID_4 = Al
Element_ID_5 = Zn
```

**Excel Columns**:
```
Flow_E1_[%] | Flow_E2_[%](Fe) | Flow_E3_[%](Cu) | Flow_E4_[%](Al) | Flow_E5_[%](Zn)
```

**Result**: Same template, different elements!

### Example 3: Food System (Future)

**Configuration**:
```
Element_ID_1 = material
Element_ID_2 = protein
Element_ID_3 = lipids
Element_ID_4 = carbs
Element_ID_5 = fiber
```

**Result**: Nutritional composition tracking!

---

## Migration Guide

### For New Users

✅ **Start with new format**:
1. Define elements in `0_Configuration`: `Element_ID_X` and `Parent_Element_ID_X`
2. Use generic headers: `Flow_E2_[%](element)` in `1_1_Definition_Flows`
3. Element names in parentheses are optional labels

### For Existing Users

✅ **Backward compatible**:
- Old files with `Flow_WC[%]`, `Flow_DM[%]` still work
- System auto-detects column format
- No immediate action required

⚠️ **Recommended migration**:
1. Update `0_Configuration` to `Element_ID_X` format (underscore, not space)
2. Optionally rename columns to `Flow_E2_[%](WC)` for future-proofing
3. Test with existing data

---

## Testing

### Test 1: Config Loading

**Command**:
```bash
python -c "
import sys
sys.path.insert(0, '02_src')
from config import load_config_from_excel
config = load_config_from_excel('01_data/01_input/251031_BioDYM_ODYM.xlsm')
print(config['Element_Hierarchy'])
"
```

**Expected Output**:
```
{1: {'name': 'material', 'parent': None},
 2: {'name': 'WC', 'parent': 'material'},
 3: {'name': 'DM', 'parent': 'material'},
 4: {'name': 'CC', 'parent': 'DM'}}
```

### Test 2: Column Mapping

**Command**:
```bash
python -c "
import sys, pandas as pd
sys.path.insert(0, '02_src')
from system_setup import _build_element_column_map
flow_df = pd.read_excel('01_data/01_input/251031_BioDYM_ODYM.xlsm',
                        sheet_name='1_1_Definition_Flows', header=0)
elements = ['material', 'WC', 'DM', 'CC']
column_map = _build_element_column_map(elements, flow_df)
for elem, col in column_map.items():
    print(f'{elem:10} -> {col}')
"
```

**Expected Output**:
```
WC         -> Flow_E2_[%](WC)
DM         -> Flow_E3_[%](DM)2
CC         -> Flow_E4_[%](CC)
```

---

## Benefits

### ✅ Single Source of Truth
- Config sheet defines all elements
- No hardcoding in Python
- Easy to understand and maintain

### ✅ Future-Proof
- Same template for any element set
- Add new elements: just add `Element_ID_5`, `Element_ID_6`
- No code changes needed

### ✅ Clear Hierarchy
- `Parent_Element_ID` explicitly shows relationships
- Supports complex compositions
- Easy to validate and document

### ✅ Backward Compatible
- Old files still work
- Auto-detection of column formats
- Gradual migration path

### ✅ Scientifically Rigorous
- Explicit about % of what (material vs DM)
- Prevents composition errors
- Clear documentation trail

---

## Current Limitations & Future Work

### Known Limitations

1. **⚠️ Hierarchy not yet used in calculations**
   - Config loads hierarchy correctly ✅
   - Columns map correctly ✅
   - Composition calculation still uses flat structure ❌
   - **Future**: Update `_calculate_elemental_compositions()` to use parent elements

2. **Hierarchy depth = 1**
   - Supports: CC % of DM, DM % of material
   - Future: Could support deeper (e.g., Cellulose % of Carbs % of DM)

3. **No cross-element validation**
   - Doesn't enforce WC + DM = material
   - Future: Add validation rules in config

### Planned Enhancements

**Phase 5b: Hierarchical Composition Calculation** (3-4 hours)

Update `_calculate_elemental_compositions()` to respect hierarchy:

```python
# Current (flat):
flow.Values[:, cc_idx] = material_values * cc_fraction  # WRONG!

# Planned (hierarchical):
parent_element = element_hierarchy[element]['parent']
parent_idx = elements.index(parent_element)
parent_values = flow.Values[:, parent_idx]
flow.Values[:, cc_idx] = parent_values * cc_fraction  # CORRECT!
```

**Other Future Features**:
1. Visual hierarchy editor (GUI)
2. Template generator for common domains
3. Validation rules for compositions
4. Unit conversions for different element types

---

## Files Modified

1. **`02_src/config.py`** (Lines 64-180)
   - Added `Element_ID_X` and `Parent_Element_ID_X` parsing (with underscore)
   - Stores `Element_Hierarchy` structure
   - Supports both old `"Element ID X"` (space) and new `Element_ID_X` (underscore)
   - Fixed emoji encoding for Windows console (`[OK]`, `[WARNING]` instead of ✅ ⚠️)

2. **`02_src/system_setup.py`** (Lines 428-504)
   - Updated `_build_element_column_map()` to detect E{id} format
   - Priority: E{id} format → Legacy element name → Special cases
   - Handles Excel duplicate suffixes (e.g., `Flow_E3_[%](DM)2`)
   - Backward compatible with `Flow_WC[%]` format
   - Improved warning messages with element ID

---

## FAQ

**Q: Do I need to rename all my columns?**
A: No! The system auto-detects old formats. But `Flow_E2_[%](WC)` is recommended for new files.

**Q: What if Excel creates duplicate column names?**
A: The system handles Excel's auto-suffix (e.g., `Flow_E3_[%](DM)2`) automatically.

**Q: Can I have more than 4 elements?**
A: Yes! Add `Element_ID_5`, `Element_ID_6`, etc. in config and corresponding `Flow_E5_[%]()` columns.

**Q: Do I need Parent_Element_ID for all elements?**
A: No, only for hierarchical elements (e.g., CC % of DM). Most elements default to % of material.

**Q: When will hierarchical calculations be implemented?**
A: Currently in design (Phase 5b). Config and column mapping are ready, just need to update the composition calculation logic.

**Q: Can I mix old and new formats?**
A: Yes, but not recommended. System uses priority order to find columns.

---

## Summary

### ✅ What's Implemented

- Config loading with `Element_ID_X` and `Parent_Element_ID_X`
- Element hierarchy structure stored in config
- Dynamic column mapping (E{id} format detection)
- Backward compatibility with legacy formats
- Handles Excel edge cases (duplicate suffixes)

### ⚠️ What's Next

- Use hierarchy in composition calculations (Phase 5b)
- Hierarchical validation (sum check per level)
- Deeper hierarchy support (multi-level)

### 🎯 Vision

**One codebase, any material system:**
- Biomass → Metals → Food → Waste → Chemicals
- Just change config, same Excel structure
- Scientifically rigorous, user-friendly

---

**Last Updated**: 2025-10-31
**Version**: 1.0 (Implementation Complete)
**Status**: ✅ Config & Mapping Implemented | ⚠️ Hierarchical Calculation Pending
**Authors**: BioDYM Development Team
