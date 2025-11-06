# Dynamic Excel Headers Solution

## Problem Statement

Current Excel structure:
- **Config (0_Configuration)**: Element names defined as `Element_ID_1`, `Element_ID_2`, etc.
- **Flow Table (1_1_Definition_Flows)**: Headers are hardcoded: `Flow_WC[%]`, `Flow_DM[%]`, `Flow_CC_DM[%]`

**Goal**: Make config the **single source of truth** - when element names change in config, flow table headers automatically update.

---

## Current Configuration Structure (251030 File)

```
Row 29: Element_ID_1 = "material"
Row 30: Element_ID_2 = "WC"
Row 31: Parent_Element_ID_2 = "material"
Row 32: Element_ID_3 = "DM"
Row 33: Parent_Element_ID_3 = "material"
Row 34: Element_ID_4 = "CC"
Row 35: Parent_Element_ID_4 = "DM"
```

---

## Solution Options

### Option 1: Python Preprocessing (RECOMMENDED)

**Approach**: Add a validation/preprocessing step in Python that reads config and validates/renames columns before processing.

**Advantages**:
- ✅ Config is single source of truth
- ✅ Works with Excel tables (no formula limitations)
- ✅ Clear error messages if structure doesn't match
- ✅ No VBA macros needed

**Implementation**:
```python
# In system_setup.py or new file: excel_preprocessor.py

def validate_and_map_element_columns(config, flow_df):
    """
    Validates that flow table has correct element columns based on config.
    Maps legacy column names to current element names if needed.

    Returns: Updated DataFrame with standardized column names
    """
    elements = config.Elements  # e.g., ['material', 'WC', 'DM', 'CC']
    element_hierarchy = config.Element_Hierarchy  # e.g., {'WC': 'material', 'DM': 'material', 'CC': 'DM'}

    # Build expected column names
    expected_columns = {}
    for element in elements[1:]:  # Skip 'material'
        parent = element_hierarchy.get(element, 'material')

        if parent == 'material':
            # Standard: Flow_{element}[%]
            expected_columns[element] = f"Flow_{element}[%]"
        else:
            # Hierarchical: Flow_{element}_{parent}[%]
            expected_columns[element] = f"Flow_{element}_{parent}[%]"

    # Validate columns exist
    missing_columns = []
    for element, col_name in expected_columns.items():
        if col_name not in flow_df.columns:
            # Try alternative naming
            alt_name = f"Flow_{element}[%]"
            if alt_name in flow_df.columns:
                print(f"✓ Found {alt_name} for element {element}")
            else:
                missing_columns.append(col_name)

    if missing_columns:
        print(f"⚠️  Missing columns in 1_1_Definition_Flows:")
        for col in missing_columns:
            print(f"   - {col}")
        print(f"\n💡 Tip: Add these columns to match elements in config")
        print(f"   Config elements: {elements[1:]}")

    return flow_df, expected_columns
```

**Usage in Workflow**:
```python
# In 00_BioDYM_Workflow.py
config = load_configuration(excel_file)
flow_df = pd.read_excel(excel_file, sheet_name='1_1_Definition_Flows')

# Validate element columns match config
flow_df, element_map = validate_and_map_element_columns(config, flow_df)
```

---

### Option 2: Excel Formula in Secondary Header Row

**Approach**: Use formulas to create dynamic header labels that reference config.

**Structure**:
```
Row 1 (Static - for Python):  Flow_E2[%]  | Flow_E3[%]  | Flow_E4[%]
Row 2 (Dynamic - for users):  =Element_ID_2 | =Element_ID_3 | =Element_ID_4
Row 3+ (Data):                 0.50        | 0.50        | 0.80
```

**Advantages**:
- ✅ Visual: Users see current element names
- ✅ No code changes needed
- ✅ Works with Excel tables

**Disadvantages**:
- ⚠️ Python reads Row 1 (static codes), not Row 2 (dynamic names)
- ⚠️ Two-row header structure more complex

---

### Option 3: Named Ranges + Excel Table

**Approach**: Use Excel Named Ranges that reference config values.

**Setup**:
1. Create named ranges: `Element_2`, `Element_3`, `Element_4` pointing to config cells
2. Use formulas in column headers (if not formatted as Table)
3. Python resolves named ranges when reading

**Advantages**:
- ✅ True dynamic linking in Excel

**Disadvantages**:
- ❌ Excel Tables don't support formula headers
- ❌ Complex setup
- ❌ Python openpyxl/pandas may not resolve named ranges in headers

---

### Option 4: VBA Macro (Auto-Update on Config Change)

**Approach**: VBA macro that monitors config changes and updates table headers.

**Excel VBA**:
```vba
Private Sub Worksheet_Change(ByVal Target As Range)
    ' Trigger: User changes Element_ID_X in config
    ' Action: Update Flow_{Element}[%] column headers in 1_1_Definition_Flows

    If Target.Address = "$B$30" Then  ' Element_ID_2 changed
        Dim newElement As String
        newElement = Target.Value

        ' Update column header in 1_1_Definition_Flows sheet
        Worksheets("1_1_Definition_Flows").Range("N1").Value = "Flow_" & newElement & "[%]"
    End If
End Sub
```

**Advantages**:
- ✅ True automation in Excel
- ✅ Instant updates when config changes

**Disadvantages**:
- ❌ Requires .xlsm file (macros enabled)
- ❌ Macros can be blocked by security settings
- ❌ Harder to maintain and debug
- ❌ Not compatible with all platforms

---

## RECOMMENDED SOLUTION: Hybrid Approach

**Best of both worlds**: Flexible Excel + Smart Python validation

### Excel Structure (Single Source of Truth)

**1. Config Sheet (0_Configuration)** - As you have it:
```
Element_ID_1 = material
Element_ID_2 = WC
Parent_Element_ID_2 = material
Element_ID_3 = DM
Parent_Element_ID_3 = material
Element_ID_4 = CC
Parent_Element_ID_4 = DM
```

**2. Flow Table (1_1_Definition_Flows)** - Use Generic IDs:
```
Flow_ID | Flow_Name | Flow_E2[%] | Flow_E3[%] | Flow_E4[%]
--------|-----------|------------|------------|------------
F_01_02 | Biomass   | 0.50       | 0.50       | 0.80
```

Where `E2` = Element_ID_2, `E3` = Element_ID_3, etc.

**3. Add Helper Row (Optional)** - For user readability:
```
Flow_ID | Flow_Name | Flow_E2[%]  | Flow_E3[%]  | Flow_E4[%]
        |           | (WC)        | (DM)        | (CC)         ← Helper labels
--------|-----------|-------------|-------------|-------------
F_01_02 | Biomass   | 0.50        | 0.50        | 0.80
```

### Python Implementation

**Update config.py** to build element-to-column mapping:
```python
def load_config_from_excel(excel_file_path):
    # ... existing code ...

    # Enhanced: Collect Elements with Parent + Column Mapping
    element_list = []
    element_hierarchy = {}
    element_column_map = {}

    for i in range(2, 10):  # Element_ID_2 through Element_ID_9
        element_key = f"Element_ID_{i}"
        parent_key = f"Parent_Element_ID_{i}"

        if element_key in config_dict:
            element_name = config_dict[element_key]
            if pd.notna(element_name) and str(element_name).strip():
                element_name = str(element_name).strip()
                element_list.append(element_name)

                # Get parent
                parent = config_dict.get(parent_key, 'material')
                if pd.notna(parent):
                    parent = str(parent).strip()
                else:
                    parent = 'material'

                element_hierarchy[element_name] = parent

                # Map to Excel column
                element_column_map[element_name] = f"Flow_E{i}[%]"

    # Ensure 'material' is first
    if 'material' not in element_list:
        element_list.insert(0, 'material')

    config_dict['Elements'] = ','.join(element_list)
    config_dict['Element_Hierarchy'] = element_hierarchy
    config_dict['Element_Column_Map'] = element_column_map

    print(f"✅ Loaded {len(element_list)} elements: {element_list}")
    print(f"   Hierarchy: {element_hierarchy}")
    print(f"   Column mapping: {element_column_map}")

    return config_dict
```

**Update system_setup.py** to use dynamic mapping:
```python
def _build_element_column_map(elements, content_definitions):
    """
    Builds column mapping using config's Element_Column_Map.
    Falls back to convention-based search if not found.
    """
    # Get mapping from config (if available)
    config_map = getattr(mfa_system, 'Element_Column_Map', {})

    column_map = {}
    available_columns = content_definitions.columns

    for element in elements[1:]:  # Skip 'material'
        # Priority 1: Use config mapping
        if element in config_map:
            expected_col = config_map[element]
            if expected_col in available_columns:
                column_map[element] = expected_col
                continue

        # Priority 2: Try convention-based naming
        standard_name = f"Flow_{element}[%]"
        if standard_name in available_columns:
            column_map[element] = standard_name
            continue

        # Priority 3: Try generic IDs (Flow_E2[%], Flow_E3[%])
        for i in range(2, 10):
            generic_name = f"Flow_E{i}[%]"
            if generic_name in available_columns:
                # Check if this matches element's position
                element_idx = elements.index(element)
                if i == element_idx:
                    column_map[element] = generic_name
                    break

        if element not in column_map:
            print(f"⚠️  Column for element '{element}' not found")
            print(f"    Expected: {config_map.get(element, standard_name)}")

    return column_map
```

---

## Implementation Benefits

### For Biomass System:
```
Config:
  Element_ID_2 = WC  →  Column: Flow_E2[%]  →  Python: WC = Flow_E2[%] * material
  Element_ID_3 = DM  →  Column: Flow_E3[%]  →  Python: DM = Flow_E3[%] * material
  Element_ID_4 = CC  →  Column: Flow_E4[%]  →  Python: CC = Flow_E4[%] * DM
```

### For Metal System:
```
Config:
  Element_ID_2 = Fe  →  Column: Flow_E2[%]  →  Python: Fe = Flow_E2[%] * material
  Element_ID_3 = Cu  →  Column: Flow_E3[%]  →  Python: Cu = Flow_E3[%] * material
  Element_ID_4 = Al  →  Column: Flow_E4[%]  →  Python: Al = Flow_E4[%] * material
```

### Key Advantages:
1. ✅ **Single Source of Truth**: Config defines elements
2. ✅ **Generic Excel**: Columns are `Flow_E2[%]`, `Flow_E3[%]` - never need renaming
3. ✅ **Smart Mapping**: Python links `E2` → `WC` or `Fe` based on config
4. ✅ **User-Friendly**: Optional helper row shows current element names
5. ✅ **Backward Compatible**: Still supports `Flow_WC[%]` naming if present
6. ✅ **Error Handling**: Clear messages if structure doesn't match

---

## Migration Path

### For Your Current File (251030):

**Option A: Minimal Changes** (Recommended for now)
1. Keep current column names: `Flow_WC[%]`, `Flow_DM[%]`, `Flow_CC_DM[%]`
2. Update Python to read from `Element_ID_X` and `Parent_Element_ID_X`
3. Python validates that columns match config elements
4. Works for both biomass and metals (with different configs)

**Option B: Future-Proof Template**
1. Rename columns to: `Flow_E2[%]`, `Flow_E3[%]`, `Flow_E4[%]`
2. Add helper row: "(WC)", "(DM)", "(CC)"
3. Python uses config mapping to link E2→WC, E3→DM, E4→CC
4. Fully generic - never need to touch Excel table structure again

---

## Recommendation for Your Next Step

**For immediate testing** (today):
1. Keep your current Excel structure (don't rename columns yet)
2. Let me update Python to read `Element_ID_X` and `Parent_Element_ID_X`
3. Python will validate and map columns dynamically
4. Test with biomass first (verify backward compatibility)

**For production template** (after testing):
1. Create generic template with `Flow_E2[%]`, `Flow_E3[%]`, etc.
2. Add VBA macro (optional) for auto-updating helper labels
3. Update documentation with examples for biomass/metals

---

## Next Implementation Steps

Would you like me to:

**A)** Update Python now to read your new `Element_ID_X` + `Parent_Element_ID_X` structure?

**B)** Create a generic template with `Flow_EX[%]` columns for future use?

**C)** Both - update Python for current file + create generic template?

Let me know which approach you prefer!
