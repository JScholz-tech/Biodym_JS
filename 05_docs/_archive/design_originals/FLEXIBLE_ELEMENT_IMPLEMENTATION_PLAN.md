# Flexible Element Architecture - Implementation Plan

## Current State

**Excel Configuration** (0_Configuration sheet) ✅ Already flexible!
```
Row 28: Enable elements? | True
Row 29: Element ID 1     | material
Row 30: Element ID 2     | WC
Row 31: Element ID 3     | DM
Row 32: Element ID 4     | CC
Row 33: Element ID 5     | (unused - can add more!)
```

**Code** ❌ Currently hardcoded:
- Assumes exactly 4 elements: ['material', 'WC', 'DM', 'CC']
- Hardcoded column names: `Flow_WC[%]`, `Flow_DM[%]`, `Flow_CC_DM[%]`
- Hardcoded indices in solver: `wc_idx`, `dm_idx`, `cc_idx`

## Goal

Make code **dynamically adapt** to any elements defined in Excel configuration.

## Implementation Strategy

### Phase 1: Dynamic Element Reading (1-2 hours)

#### Step 1.1: Update Config Loader
**File**: `02_src/config.py`

**Add function**:
```python
def load_element_definitions(config_df):
    """
    Dynamically read element definitions from 0_Configuration sheet.

    Looks for rows with:
    - Column B starting with "Element ID"
    - Column C containing element name

    Returns
    -------
    list of str
        List of element names (e.g., ['material', 'WC', 'DM', 'CC'])
    """
    elements = []

    # Find "ODYM Dimension: Elements" section
    element_section_start = None
    for idx, row in config_df.iterrows():
        if 'Elements (e' in str(row.iloc[0]) or 'Element ID 1' in str(row.iloc[1]):
            element_section_start = idx
            break

    if element_section_start is None:
        # Fallback to default elements
        return ['material', 'WC', 'DM', 'CC']

    # Read element IDs (typically rows +1 to +10 from start)
    for i in range(element_section_start, element_section_start + 15):
        if i >= len(config_df):
            break

        cell_label = str(config_df.iloc[i, 1])  # Column B
        cell_value = config_df.iloc[i, 2]  # Column C

        # Check if this is an Element ID row
        if 'Element ID' in cell_label and pd.notna(cell_value):
            element_name = str(cell_value).strip()
            if element_name and element_name != 'nan':
                elements.append(element_name)

        # Stop at next section (e.g., "Unit_of_Measurement")
        if 'Unit_of_Measurement' in cell_label:
            break

    # Ensure 'material' is always first (required for total mass)
    if 'material' not in elements:
        elements.insert(0, 'material')
    elif elements[0] != 'material':
        elements.remove('material')
        elements.insert(0, 'material')

    print(f"✅ Loaded {len(elements)} elements: {elements}")
    return elements
```

**Update `load_configuration()`**:
```python
def load_configuration(input_file):
    # ... existing code ...

    # Load element definitions dynamically
    config_obj.elements = load_element_definitions(config_df)

    # ... rest of function ...
```

#### Step 1.2: Update Workflow to Use Dynamic Elements
**File**: `00_BioDYM_Workflow.py` or `.ipynb`

**Change from**:
```python
# Hardcoded
elements = ['material', 'WC', 'DM', 'CC']
```

**To**:
```python
# Dynamic from config
elements = config_obj.elements  # Loaded from Excel
print(f"🔬 Tracking elements: {elements}")
```

---

### Phase 2: Dynamic Column Mapping (2-3 hours)

#### Step 2.1: Update Flow Definition Loading
**File**: `02_src/system_setup.py` → `_define_content_parameters()`

**Current** (line ~407):
```python
column_map = {
    "WC": "Flow_WC[%]",
    "DM": "Flow_DM[%]",
    "CC": "Flow_CC_DM[%]"
}
```

**New** (dynamic):
```python
def _build_element_column_map(elements, flow_definitions_df):
    """
    Dynamically builds column name mapping based on elements.

    For each element (except 'material'), looks for column:
    - Standard: Flow_{element}[%]
    - Legacy: Flow_{element}_[%] (with underscore)

    Special case: CC might be "Flow_CC_DM[%]" in legacy files
    """
    column_map = {}
    available_columns = flow_definitions_df.columns

    for element in elements:
        if element == 'material':
            continue  # Material is total, not a fraction

        # Try standard naming
        standard_name = f"Flow_{element}[%]"
        if standard_name in available_columns:
            column_map[element] = standard_name
            continue

        # Try legacy naming (e.g., "Flow_WC_[%]")
        legacy_name = f"Flow_{element}_[%]"
        if legacy_name in available_columns:
            column_map[element] = legacy_name
            continue

        # Special case: CC might be stored as "Flow_CC_DM[%]"
        if element == 'CC':
            cc_dm_name = "Flow_CC_DM[%]"
            if cc_dm_name in available_columns:
                column_map[element] = cc_dm_name
                continue

        # If not found, warn user
        print(f"⚠️  Column for element '{element}' not found in 1_1_Definition_Flows")
        print(f"    Expected: {standard_name} or {legacy_name}")
        print(f"    Available columns: {list(available_columns)}")

    return column_map


# In _define_content_parameters():
def _define_content_parameters(mfa_system, flow_definitions):
    """Creates parameters for flow content (WC, DM, CC, or any elements)."""

    # Build column map dynamically
    elements = mfa_system.Elements
    column_map = _build_element_column_map(elements, flow_definitions)

    for _, row in flow_definitions.iterrows():
        flow_id = row["Flow_ID"]

        # For each element, create parameter
        for element in elements:
            if element == 'material':
                continue  # Skip material (it's the total)

            if element not in column_map:
                continue  # Skip if column not found

            column_name = column_map[element]
            fraction_value = row.get(column_name, 0.0)

            # Create parameter
            param_name = f"{element}_{flow_id}"
            param = msc.Parameter(
                Name=param_name,
                Values=fraction_value,
                Indices=""  # Scalar parameter
            )
            mfa_system.ParameterDict[param_name] = param
```

#### Step 2.2: Update Composition Calculation
**File**: `02_src/system_setup.py` → `_calculate_elemental_compositions()`

**Current** (line ~438, hardcoded):
```python
wc_param = mfa_system.ParameterDict.get(f"WC_{flow_id}")
dm_param = mfa_system.ParameterDict.get(f"DM_{flow_id}")
cc_param = mfa_system.ParameterDict.get(f"CC_{flow_id}")

flow.Values[:, wc_idx] = flow.Values[:, mat_idx] * wc_fraction
flow.Values[:, dm_idx] = flow.Values[:, mat_idx] * dm_fraction
flow.Values[:, cc_idx] = flow.Values[:, mat_idx] * cc_fraction
```

**New** (dynamic):
```python
def _calculate_elemental_compositions(mfa_system):
    """Calculates elemental composition for all flows dynamically."""

    elements = mfa_system.Elements
    mat_idx = elements.index('material')

    for flow in mfa_system.FlowDict.values():
        flow_id = flow.Name
        material_values = flow.Values[:, mat_idx]

        # Calculate each element's values
        for elem_idx, element in enumerate(elements):
            if element == 'material':
                continue  # Skip material (already populated)

            # Get parameter for this element-flow combination
            param_name = f"{element}_{flow_id}"
            param = mfa_system.ParameterDict.get(param_name)

            if param is None:
                print(f"⚠️  No composition parameter for {element} in {flow_id}, assuming 0")
                flow.Values[:, elem_idx] = 0.0
                continue

            # Calculate: element_mass = material_mass * fraction
            fraction = param.Values
            flow.Values[:, elem_idx] = material_values * fraction

        # Validate: sum of elements should be <= material
        element_sum = np.sum(flow.Values[:, 1:], axis=1)  # Sum all except material
        material_total = flow.Values[:, mat_idx]

        if np.any(element_sum > material_total * 1.01):  # 1% tolerance
            print(f"⚠️  WARNING: {flow_id} - Element sum exceeds material mass!")
            print(f"    Max overshoot: {np.max(element_sum - material_total):.3f} Mg")
```

---

### Phase 3: Dynamic Solver (3-4 hours)

#### Step 3.1: Remove Hardcoded Element Indices
**File**: `02_src/engine/solver.py`

**Current approach** (lines 191-195):
```python
mat_idx = mfa_system.Elements.index('material')
wc_idx = mfa_system.Elements.index('WC')
dm_idx = mfa_system.Elements.index('DM')
cc_idx = mfa_system.Elements.index('CC')
```

**New approach** (dynamic):
```python
def _get_element_indices(mfa_system):
    """
    Get element indices dynamically.

    Returns
    -------
    dict
        Dictionary mapping element names to indices
        e.g., {'material': 0, 'WC': 1, 'DM': 2, 'CC': 3}
    """
    return {elem: idx for idx, elem in enumerate(mfa_system.Elements)}


# In _calculate_tc_driven_flows():
def _calculate_tc_driven_flows(mfa_system, ...):
    # Get indices dynamically
    elem_indices = _get_element_indices(mfa_system)
    mat_idx = elem_indices['material']

    # Get non-material element indices
    other_elements = [e for e in mfa_system.Elements if e != 'material']

    # ... rest of function ...
```

#### Step 3.2: Update Splitter Logic (Dynamic)
**File**: `02_src/engine/solver.py` (line ~199-210)

**Current** (hardcoded for 3 elements):
```python
if process_logic == 'Splitter':
    # ... TC calculation ...
    inflow_material = total_inflow_vector[:, mat_idx]
    wc_fraction = np.divide(total_inflow_vector[:, wc_idx], inflow_material, ...)
    dm_fraction = np.divide(total_inflow_vector[:, dm_idx], inflow_material, ...)
    cc_fraction = np.divide(total_inflow_vector[:, cc_idx], inflow_material, ...)

    outflow_vector[:, wc_idx] = outflow_vector[:, mat_idx] * wc_fraction
    outflow_vector[:, dm_idx] = outflow_vector[:, mat_idx] * dm_fraction
    outflow_vector[:, cc_idx] = outflow_vector[:, mat_idx] * cc_fraction
```

**New** (dynamic for any elements):
```python
if process_logic == 'Splitter':
    param_name = tc_ids.get('material')
    if param_name and param_name in mfa_system.ParameterDict:
        tc_value = mfa_system.ParameterDict[param_name].Values
        outflow_vector[:, mat_idx] = total_inflow_vector[:, mat_idx] * tc_value

        # Preserve composition for all other elements
        inflow_material = total_inflow_vector[:, mat_idx]

        for element in other_elements:
            elem_idx = elem_indices[element]

            # Calculate fraction: element / material (avoid division by zero)
            element_fraction = np.divide(
                total_inflow_vector[:, elem_idx],
                inflow_material,
                out=np.zeros_like(inflow_material),
                where=inflow_material != 0
            )

            # Apply fraction to outflow material
            outflow_vector[:, elem_idx] = outflow_vector[:, mat_idx] * element_fraction
```

#### Step 3.3: Update Transformer Logic (Dynamic)
**File**: `02_src/engine/solver.py` (line ~212-217)

**Current** (hardcoded):
```python
elif process_logic == 'Transformer':
    for i_elem, element in [(wc_idx, 'WC'), (dm_idx, 'DM'), (cc_idx, 'CC')]:
        param_name = tc_ids.get(element, tc_ids.get('material'))
        if param_name and param_name in mfa_system.ParameterDict:
            tc_value = mfa_system.ParameterDict[param_name].Values
            outflow_vector[:, i_elem] = total_inflow_vector[:, i_elem] * tc_value
    outflow_vector[:, mat_idx] = outflow_vector[:, wc_idx] + outflow_vector[:, dm_idx]
```

**New** (dynamic):
```python
elif process_logic == 'Transformer':
    # Apply TCs to each element independently
    for element in other_elements:
        elem_idx = elem_indices[element]

        # Look for element-specific TC, fallback to material TC
        param_name = tc_ids.get(element, tc_ids.get('material'))

        if param_name and param_name in mfa_system.ParameterDict:
            tc_value = mfa_system.ParameterDict[param_name].Values
            outflow_vector[:, elem_idx] = total_inflow_vector[:, elem_idx] * tc_value
        else:
            # No TC found, assume passthrough
            outflow_vector[:, elem_idx] = total_inflow_vector[:, elem_idx]

    # Recalculate total material as sum of elements
    outflow_vector[:, mat_idx] = np.sum(outflow_vector[:, 1:], axis=1)
```

---

### Phase 4: FOMP/DSM Compatibility (1-2 hours)

#### Step 4.1: Make FOMP Element-Aware
**File**: `02_src/engine/fomp_model.py`

**Issue**: FOMP currently requires 'DM' and 'CC' elements

**Solution A** (Conditional):
```python
def calculate_fomp(mfa_system, fomp_params_config, input_flow_composition):
    """Calculate FOMP with element checking."""

    # Check if required elements exist
    required_elements = ['DM', 'CC']
    available_elements = mfa_system.Elements

    missing_elements = [e for e in required_elements if e not in available_elements]

    if missing_elements:
        print(f"⚠️  FOMP disabled: Missing required elements {missing_elements}")
        print(f"   FOMP requires 'DM' (dry matter) and 'CC' (carbon content)")
        print(f"   Available elements: {available_elements}")
        return mfa_system  # Return unchanged

    # ... rest of FOMP calculation ...
```

**Solution B** (Generalize for any organic element):
```python
# Allow configuration of which element represents organic matter
# In config: FOMP_organic_element = "DM" (for biomass) or "organic_fraction" (for mixed waste)
```

#### Step 4.2: DSM Already Compatible
**File**: `02_src/engine/dsm_model.py`

**Good news**: DSM only uses material column (line 47), so it's already compatible! ✅

---

### Phase 5: Excel Template Updates (2-3 hours)

#### Step 5.1: Add Element Instructions
**Sheet**: `BioDYM_README`

Add section:
```
=== ELEMENT CONFIGURATION ===

1. Go to sheet "0_Configuration"
2. Find section "ODYM Dimension: Elements (e)"
3. Define your elements:
   - Element ID 1: material (required - always first!)
   - Element ID 2-5: Your tracked elements

Examples:

BIOMASS SYSTEMS:
  Element ID 1: material
  Element ID 2: WC (water content)
  Element ID 3: DM (dry matter)
  Element ID 4: CC (carbon content)

METAL SYSTEMS:
  Element ID 1: material
  Element ID 2: Fe (iron)
  Element ID 3: Cu (copper)
  Element ID 4: Al (aluminum)

MIXED WASTE:
  Element ID 1: material
  Element ID 2: organic_fraction
  Element ID 3: plastic_fraction
  Element ID 4: metal_fraction

4. Update column names in other sheets:
   - Sheet "1_1_Definition_Flows": Add columns Flow_{element}[%]
   - Example: Flow_Fe[%], Flow_Cu[%], Flow_Al[%]
```

#### Step 5.2: Create Metal Template
**New file**: `01_data/01_input/Template_Metals.xlsx`

Structure:
- 0_Configuration: Elements = ['material', 'Fe', 'Cu', 'Al', 'Zn']
- 1_1_Definition_Flows: Columns include Flow_Fe[%], Flow_Cu[%], etc.
- Simple metal recycling example

---

## Testing Strategy

### Test 1: Biomass (Existing)
- Elements: ['material', 'WC', 'DM', 'CC']
- Expected: Everything works as before (backward compatible)

### Test 2: Metals (New)
- Elements: ['material', 'Fe', 'Cu', 'Al']
- Expected: System tracks 3 metals through flows

### Test 3: Custom (New)
- Elements: ['material', 'plastic', 'organic', 'inert']
- Expected: Works for any element names

---

## Implementation Timeline

| Phase | Task | Time | Files |
|-------|------|------|-------|
| 1 | Dynamic element reading | 1-2 h | config.py |
| 2 | Dynamic column mapping | 2-3 h | system_setup.py |
| 3 | Dynamic solver | 3-4 h | solver.py |
| 4 | FOMP/DSM compatibility | 1-2 h | fomp_model.py |
| 5 | Excel templates | 2-3 h | Excel files |
| **Total** | **Full implementation** | **10-14 hours** | **~2 days** |

---

## Benefits

1. ✅ **True flexibility**: Any elements, any application domain
2. ✅ **Backward compatible**: Existing biomass files still work
3. ✅ **User-friendly**: Configure in Excel, code adapts automatically
4. ✅ **Publication-ready**: Demonstrates ODYM compliance
5. ✅ **Future-proof**: Ready for multi-material, multi-element studies

---

## Next Steps

**Would you like me to:**
1. ✅ **Implement Phase 1** (dynamic element reading) - 1-2 hours
2. ✅ **Implement Phase 2** (dynamic columns) - 2-3 hours
3. ✅ **Implement Phase 3** (dynamic solver) - 3-4 hours
4. ✅ **Create metal template** after testing
5. ✅ **All of the above** in sequence

This makes BioDYM truly element-agnostic! 🚀
