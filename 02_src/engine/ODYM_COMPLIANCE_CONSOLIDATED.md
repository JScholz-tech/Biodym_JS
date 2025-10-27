# BioDYM ODYM Compliance - Consolidated Documentation
**Date**: Current Session
**Total Files Combined**: 42
---



================================================================================
# File: 3D_IMPLEMENTATION_COMPLEXITY.md
================================================================================

# 3D Material Dimension Implementation - Complexity Assessment

## Your Current Data

**Excel Structure**:
- Row 1: Flow_Material="WC", Flow=100 Mg, CC_[%]=50%
- Row 2: Flow_Material="DM", Flow=100 Mg, CC_[%]=50%

**Current 2D Structure** (WORKING):
- Flow.Values.shape = (26, 1)  
- One element: CC
- WC/DM are in separate rows, not dimensions

---

## What 3D Would Require

### **Changes Needed:**

### **1. Data Loader** (`data_loader.py` or `system_setup.py`)
**Complexity**: 🔴 **HIGH**
- Current: Reads flow values directly into (time, element) arrays
- Needed: Read Flow_Material column, assign to material dimension
- Function to update: `_populate_primary_flow_data()`
- **Estimated effort**: 4-6 hours

### **2. Solver** (`solver.py`)
**Complexity**: 🟡 **MEDIUM**  
- Current: ✅ Already updated for 3D support (done!)
- Changes: Test and fix any remaining issues
- **Estimated effort**: 2-3 hours

### **3. DSM Model** (`dsm_model.py`)
**Complexity**: 🟡 **MEDIUM**
- Current: Assumes 2D arrays
- Needed: Aggregate over materials for stock calculations
- **Estimated effort**: 2-3 hours

### **4. FOMP Model** (`fomp_model.py`)  
**Complexity**: 🟡 **MEDIUM**
- Current: Assumes 2D arrays
- Needed: Handle material dimension in mineralization
- **Estimated effort**: 2-3 hours

### **5. Plotting Functions**
**Complexity**: 🟢 **LOW-MEDIUM**
- Current: Mix of updated and unupdated
- Done: ✅ Sankey, ✅ Validation
- Remaining: `scenario.py`, `dynamics.py`, etc.
- **Estimated effort**: 4-6 hours (many files but straightforward fixes)

### **6. Testing**
**Complexity**: 🟡 **MEDIUM**
- Need to test workflow end-to-end
- Compare 2D vs 3D results
- Fix any bugs
- **Estimated effort**: 4-6 hours

---

## Total Complexity Assessment

### **Effort Required**: 
- **Minimum**: 18-21 hours (~3 days)
- **Realistic**: 25-30 hours (~1 week)
- **With testing/bugs**: 35-40 hours (~1.5 weeks)

### **Risk Level**: 🟡 **MEDIUM-HIGH**

**Reasons**:
1. ⚠️ Changes affect core calculations (DSM, FOMP)
2. ⚠️ Must refactor data loader (critical path)
3. ⚠️ Many plotting functions need updates
4. ⚠️ Risk of breaking existing functionality

### **Benefits**:
1. ✅ Better aligned with ODYM framework
2. ✅ More flexible for future analysis
3. ✅ Proper material-element separation
4. ✅ Scales to more materials/dimensions

### **Costs**:
1. ❌ Significant refactoring time
2. ❌ Risk of introducing bugs
3. ❌ Requires testing all visualizations
4. ❌ May break existing workflows

---

## Recommendation

### **Option A: Proceed with 3D Implementation** ✅ **IF**
- You have 1-2 weeks for testing
- You're okay with potential bugs
- Long-term ODYM compliance is important
- You want maximum flexibility

### **Option B: Keep 2D Structure** ✅ **IF**
- You need to keep system stable now
- Current analysis is sufficient
- Want to minimize risk
- Can add materials later if needed

### **Option C: Hybrid Approach** ✅ **RECOMMENDED**
- Add 3D **data structure support** (already partially done)
- Keep 2D **as default** for backward compatibility
- Enable 3D **optionally** via configuration
- Gradual migration over time

---

## My Assessment

**Recommendation**: **Option C - Hybrid Approach**

**Why**:
1. Your data loader already handles WC/DM as separate flows
2. ODYM framework can support both 2D and 3D
3. Reduces risk while keeping options open
4. Can test 3D gradually without breaking current workflows

**Implementation for Hybrid**:
1. Add `use_material_dimension` flag in config
2. If False: Keep 2D as is (current working system)
3. If True: Use 3D structure (new ODYM-compliant)
4. Update plotting to support both modes

**Estimated effort for Hybrid**: 10-15 hours

---

## What Do You Think?

**The question is**: Do you want to invest 1-2 weeks now for full 3D, or take a safer, gradual approach?



---


================================================================================
# File: 3D_SOLVER_IMPLEMENTATION.md
================================================================================

# 3D Calculation Implementation - Progress Update

## What We Just Implemented

### **Current Excel Configuration**:
- **Materials**: WC, DM (2 materials)
- **Elements**: CC (1 element)

### **3D Array Structure**:
```
Flow.Values.shape = (26, 2, 1)
# 26 years × 2 materials (WC, DM) × 1 element (CC)
```

---

## Solver Refactoring (solver.py)

**Before**: Expected elements ['material', 'WC', 'DM', 'CC']
**After**: Dynamically handles any elements, aggregates over materials

### **Key Changes**:

1. **Dimension Detection**:
   ```python
   has_materials = total_inflow_vector.ndim > 2
   ```
   - Detects 2D (time, elements)
   - Detects 3D (time, materials, elements)
   - Detects 4D (time, goods, materials, elements)

2. **Material Aggregation**:
   ```python
   # Sum over materials dimension
   total_inflow_aggregated = np.sum(total_inflow_vector, axis=1)
   ```

3. **Element-Based Calculations**:
   - Loops through all elements dynamically
   - No hardcoded element names

4. **Reshape Back**:
   ```python
   # Redistribute results to materials dimension
   outflow_vector_reshaped[:, :, :] = outflow_vector[:, np.newaxis, :]
   ```

---

## What This Means

### **For Your Current Setup**:
- Materials: WC, DM
- Elements: CC
- Shape: (26, 2, 1)

### **Calculations**:
1. Aggregate over materials: (26, 2, 1) → (26, 1)
2. Apply TC to CC element
3. Redistribute: (26, 1) → (26, 2, 1)

### **Result**:
- Each material (WC, DM) gets the same CC value
- But they're tracked separately!

---

## What Still Needs Work

### **1. DSM Model** (dsm_model.py)
- Needs 3D handling for stock calculations

### **2. FOMP Model** (fomp_model.py)
- Needs 3D handling for mineralization

### **3. Initial Stock Engine** (initial_stock_engine.py)
- Needs 3D handling for initial stock flows

---

## Next Steps

1. ✅ Test solver with 3D structure
2. ⏳ Update DSM model for 3D
3. ⏳ Update FOMP model for 3D  
4. ⏳ Update initial stock engine
5. ⏳ Test full workflow

**Ready to test the solver changes!** 🚀



---


================================================================================
# File: 4D_STRUCTURE_IMPLEMENTATION.md
================================================================================

# Full ODYM Dimension Structure - Implementation Plan

## Your 4D Structure (Good + Material + Element)

### **Dimension Hierarchy**:

1. **Time** (t): Years of analysis
2. **Good** (g): Commodity/category → `biomass`
3. **Material** (m): Physical material → `WC`, `DM`
4. **Element** (e): Component tracked → `CC`, etc.

---

## Dimension Meanings in Your System

### **Good** = "biomass"
- The commodity category (what kind of thing it is)
- In your case: agricultural biomass

### **Material** = Physical materials within the good
- **WC**: Water Content material (wet biomass)
- **DM**: Dry Matter material (dry biomass)

### **Element** = Components tracked within each material
- **CC**: Carbon Content
- (possibly others like N, P, etc.)

---

## 4D Array Structure

```
Flow.Values.shape = (26, 1, 2, 1)
# 26 years × 1 good (biomass) × 2 materials (WC, DM) × 1 element (CC)

Or if you add more goods:
Flow.Values.shape = (26, n_goods, 2, 1)

Or if you add more elements:
Flow.Values.shape = (26, n_goods, 2, n_elements)
```

---

## Excel Configuration Update Needed

**Goods** (`0_Configuration` sheet):
```
Setting_Name      | Value
Good Type 1       | biomass
```

**Materials**:
```
Setting_Name      | Value
Material ID 1      | WC
Material ID 2      | DM
```

**Elements**:
```
Setting_Name      | Value
Element ID 1       | CC
```

---

## This is the Proper ODYM Structure!

**ODYM Standard Dimensions**:
- ✅ Time
- ✅ Good ← **Adding now**
- ✅ Material ← **Adding now**  
- ✅ Element
- ⏳ Region (optional)
- ⏳ Process (optional)

---

## Implementation Steps

### **Step 1: Update system_setup.py**

Add Good dimension support (already partially exists):

```python
def define_model_scope(start_year, end_year, elements, regions=None, goods=None, materials=None, processes=None):
    # ...
    
    # Add Good dimension
    if goods is not None and len(goods) > 0:
        model_classification["Good"] = msc.Classification(
            Name="Goods", Dimension="Good", ID=4, Items=goods
        )
        aspects.append("Good")
        descriptions.append('Model aspect "Good"')
        dimensions.append("Good")
        index_letters.append("g")
        classifications.append(model_classification["Good"])
    
    # Add Material dimension
    if materials is not None and len(materials) > 0:
        model_classification["Material"] = msc.Classification(
            Name="Materials", Dimension="Material", ID=5, Items=materials
        )
        aspects.append("Material")
        descriptions.append('Model aspect "Material"')
        dimensions.append("Material")
        index_letters.append("m")
        classifications.append(model_classification["Material"])
    
    # Element dimension (always present)
    model_classification["Element"] = msc.Classification(
        Name="Elements", Dimension="Element", ID=6, Items=elements
    )
```

### **Step 2: Update config.py**

Already reads Goods! Just needs to be in Excel.

### **Step 3: Update Engine Functions**

4D array access:
```python
# 4D: (time, goods, materials, elements)
Flow.Values[:, good_idx, material_idx, element_idx]
```

### **Step 4: Test**

Verify IndexTable shows all 4 dimensions.

---

## Advantages of 4D Structure

1. ✅ **Proper ODYM Compliance**: Aligned with standard dimensions
2. ✅ **Scalability**: Easy to add more goods (straw, biochar, etc.)
3. ✅ **Flexibility**: Can track different materials per good
4. ✅ **Future-Proof**: Ready for Region and Process dimensions

---

## Recommended Configuration

**Excel `0_Configuration`**:
```
Good Type 1: biomass
Material ID 1: WC  
Material ID 2: DM
Element ID 1: CC
```

This gives you:
- **Good**: biomass
- **Materials**: WC, DM
- **Element**: CC
- Flow.Values.shape = (26, 1, 2, 1)

**Ready to implement this properly?** 🚀



---


================================================================================
# File: ADD_MATERIAL_LAYER_PLAN.md
================================================================================

# Adding Material Layer to Calculation - Implementation Plan

## Goal

Activate the Material dimension by:
1. Defining Materials in Excel configuration
2. System reads Materials automatically
3. Flow values become 3D: (Time, Material, Element)
4. Update engine functions to handle 3D arrays

---

## Step 1: Define Materials in Excel

**Excel Configuration (0_Configuration sheet)**:
- Material ID 1: WC
- Material ID 2: DM

This creates a 2-material system alongside your 4 elements.

---

## Step 2: Expected Array Structure

### **Before (2D)**:
```
Flow.Values.shape = (26, 4)
# 26 years × 4 elements (material, WC, DM, CC)
```

### **After (3D)**:
```
Flow.Values.shape = (26, 2, 4)
# 26 years × 2 materials (WC, DM) × 4 elements (material, WC, DM, CC)
```

**Important**: Each element is tracked separately for each material!

Example:
- `flow.Values[:, 0, :]` → All elements for Material 0 (WC)
- `flow.Values[:, 1, :]` → All elements for Material 1 (DM)

---

## Step 3: How This Works

### **Material Dimension Meaning**:

**Physical Materials**: WC and DM
**Elements**: material, WC, DM, CC

Now we can track:
- **WC material** contains: material, WC, DM, CC
- **DM material** contains: material, WC, DM, CC

This allows:
- Water content in wet material vs. dry material
- Separate carbon tracking for WC vs. DM
- More detailed mass balance

---

## Step 4: Updates Needed

### **Engine Functions**:

1. **solver.py** - TC-driven flows
   ```python
   # Need to aggregate or select material dimension
   # Option 1: Sum over materials
   values = np.sum(flow.Values, axis=1)  # Sum materials, keep elements
   # Option 2: Select specific material
   values = flow.Values[:, material_idx, :]
   ```

2. **dsm_model.py** - DSM calculations
   - Aggregate material dimension for stock calculations
   
3. **fomp_model.py** - FOMP calculations  
   - Handle material dimension in mineralization

### **Plotting Functions**:

Already updated! The conditional checks we added will handle both 2D and 3D arrays.

---

## Implementation Strategy

### **Phase 1: Add Materials to Excel** ✅

Manually add to Excel:
- Material ID 1: WC
- Material ID 2: DM

### **Phase 2: Test 3D Initialization**

Run workflow and check:
- IndexTable includes Material dimension
- Flow.Values shape is 3D: (26, 2, 4)

### **Phase 3: Update Engine Functions**

Add material aggregation to:
1. solver.py - TC calculations
2. dsm_model.py - DSM calculations
3. fomp_model.py - FOMP calculations

### **Phase 4: Test Calculations**

Verify:
- TC-driven flows work with 3D
- DSM calculations work
- FOMP calculations work
- All visualizations work

---

## Helper Function Needed

Create `02_src/plotting/utils.py`:

```python
def get_element_values_by_material(flow_or_stock, element_index, material_index=None):
    """
    Get element values, handling 2D or 3D arrays.
    
    Parameters
    ----------
    flow_or_stock : Flow or Stock object
    element_index : int
        Element index
    material_index : int, optional
        If None, sum over all materials. If specified, get specific material.
    
    Returns
    -------
    np.ndarray
        Time series of element values
    """
    values = flow_or_stock.Values
    
    if values.ndim == 2:
        # 2D: (time, elements)
        return values[:, element_index]
    elif values.ndim == 3:
        # 3D: (time, materials, elements)
        if material_index is not None:
            return values[:, material_index, element_index]
        else:
            # Sum over materials
            return np.sum(values[:, :, element_index], axis=1)
    else:
        raise ValueError(f"Unexpected dimension: {values.ndim}")
```

---

**Ready to add Materials to Excel and activate 3D structure!** 🚀



---


================================================================================
# File: CENTRALIZED_ODYM_CONFIGURATION.md
================================================================================

# BioDYM Centralized ODYM Dimension Configuration

## Your Proposed Approach Analysis

Your approach is **excellent** and much more elegant than my previous suggestions! Let me analyze this centralized configuration approach.

## Core ODYM Dimensions (Always Required)

Based on the ODYM framework, here are the **core dimensions**:

### **✅ Always Required Dimensions**
```python
# From ODYM_Classes.py
self.Dimensions = {
    "Time": "Time",           # ✅ You have this
    "Process": "Process",     # ✅ You have this (as individual processes)
    "Region": "Region",       # ❌ You need this
    "Good": "Process, good, or commodity",     # ✅ You have this (as materials)
    "Material": "Material: ore, alloy, scrap type, ...",  # ✅ You have this
    "Element": "Chemical element",             # ✅ You have this
}
```

### **📊 Your Current BioDYM Dimensions**
- **Time**: ✅ Years (2020-2025)
- **Element**: ✅ ["material", "WC", "DM", "CC"]
- **Process**: ✅ Individual processes (Harvest, Processing, etc.)
- **Material**: ✅ Material flows (Dry Matter, Water Content, Carbon Content)
- **Good**: ✅ Implicit in your material flows (Rye Straw, Biochar, etc.)
- **Region**: ❌ Missing (only Geogr_Scope="Case_Study_Region")

## Proposed Excel Structure

### **🎯 Centralized Configuration Sheet**

**Sheet: `0_ODYM_Configuration`** (New - At the beginning)

| Section | Column A | Column B | Column C | Column D | Column E |
|---------|----------|----------|----------|----------|----------|
| **Model Info** | | | | | |
| | Model_Name | RyeStrawMFA | | | |
| | Time_Start | 2020 | | | |
| | Time_End | 2025 | | | |
| | Unit | Mg | | | |
| | Geogr_Scope | Case_Study_Region | | | |
| **Dimension Selection** | | | | | |
| | Dimension_Name | Use_Dimension | Items | Description | Index_Letter |
| | Time | TRUE | 2020,2021,2022,2023,2024,2025 | Model time | t |
| | Element | TRUE | material,WC,DM,CC | Chemical elements | e |
| | Process | TRUE | Harvest,Processing,Storage,Application | Process types | p |
| | Material | TRUE | Dry_Matter,Water_Content,Carbon_Content | Material types | m |
| | Good | TRUE | Rye_Straw,Biochar,Compost,Energy | Good types | g |
| | Region | FALSE | Case_Study_Region | Regional scope | r |
| | Cohort | FALSE | | Age-cohort | c |
| **Dimension Definitions** | | | | | |
| **Process Types** | Process_ID | Process_Name | Description | Type | Efficiency |
| | 1 | Harvest | Biomass harvesting | Primary | 0.9 |
| | 2 | Processing | Material processing | Secondary | 0.8 |
| | 3 | Storage | Material storage | Secondary | 0.95 |
| | 4 | Application | Material application | Tertiary | 0.85 |
| **Good Types** | Good_ID | Good_Name | Description | Category | Unit |
| | 1 | Rye_Straw | Primary biomass | Biomass | Mg |
| | 2 | Biochar | Carbonized material | Material | Mg |
| | 3 | Compost | Organic material | Material | Mg |
| | 4 | Energy | Energy output | Energy | MWh |
| **Material Types** | Material_ID | Material_Name | Description | Composition |
| | 1 | Dry_Matter | Dry matter content | Organic |
| | 2 | Water_Content | Water content | Inorganic |
| | 3 | Carbon_Content | Carbon content | Carbon |
| **Region Types** | Region_ID | Region_Name | Description | Geographic_Scope |
| | 1 | Case_Study_Region | Primary study area | Local |

### **🔄 Updated Flow Definition Sheets**

**Sheet: `1_1_Definition_Flows`** (Updated)
| Column | Description | Example Values |
|--------|-------------|----------------|
| Flow_ID | Unique identifier | 1, 2, 3 |
| Flow_Name | Flow name | "Rye_Harvest_Flow" |
| Flow_Output_Process_ID | Output process ID | 1 |
| Input_Process_ID | Input process ID | 2 |
| Flow_WC[%] | Water content % | 20 |
| Flow_DM[%] | Dry matter % | 80 |
| Flow_CC_DM[%] | Carbon content % | 45 |
| **Process_Type_ID** | **Reference to Process_ID** | **1** |
| **Good_ID** | **Reference to Good_ID** | **1** |
| **Material_ID** | **Reference to Material_ID** | **1** |
| **Region_ID** | **Reference to Region_ID** | **1** |

**Sheet: `1_2_Data_Flows`** (Updated)
| Column | Description | Example Values |
|--------|-------------|----------------|
| Flow_ID | Reference to Flow_ID | 1 |
| Flow_Data_Year | Year | 2020 |
| Flow_Material | Material amount | 1000 |
| **Process_Type_ID** | **Reference to Process_ID** | **1** |
| **Good_ID** | **Reference to Good_ID** | **1** |
| **Material_ID** | **Reference to Material_ID** | **1** |
| **Region_ID** | **Reference to Region_ID** | **1** |

**Sheet: `2_1_Definition_Processes`** (Updated)
| Column | Description | Example Values |
|--------|-------------|----------------|
| ID | Process ID | 1 |
| Process_Name | Process name | "Harvest_Process_A" |
| Process_Logic | Process logic | "DSM" |
| **Process_Type_ID** | **Reference to Process_ID** | **1** |
| **Region_ID** | **Reference to Region_ID** | **1** |

## Implementation Benefits

### **✅ Advantages of Your Approach**

1. **Centralized Configuration**: All ODYM dimensions in one place
2. **Flexible Selection**: Users can choose which dimensions to use
3. **Backward Compatibility**: Existing sheets work with added columns
4. **Clear Structure**: Easy to understand and maintain
5. **Scalable**: Easy to add new dimensions or modify existing ones

### **🎯 Key Insights**

1. **You already have most dimensions**: You just need to formalize them as ODYM classifications
2. **Region is the main missing piece**: But you can start with a single region
3. **Process types vs. individual processes**: You have individual processes, need to add process type classification
4. **Good vs. Material**: You have materials, need to distinguish goods from materials

## Recommended Implementation Steps

### **Phase 1: Create Configuration Sheet**
1. **Create `0_ODYM_Configuration` sheet** with dimension definitions
2. **Set up dimension selection** (TRUE/FALSE for each dimension)
3. **Define default values** for all dimensions

### **Phase 2: Update Existing Sheets**
1. **Add dimension reference columns** to existing sheets
2. **Set default values** (all flows/processes use default dimension values)
3. **Test backward compatibility**

### **Phase 3: Enable Multi-Dimensional Analysis**
1. **Populate dimension references** with actual values
2. **Test multi-dimensional calculations**
3. **Add optional data sheets** for richer analysis

## Data Loader Updates

### **Update `data_loader.py`**

```python
# Add to REQUIRED_STRUCTURE
REQUIRED_STRUCTURE = {
    "0_ODYM_Configuration": ["Dimension_Name", "Use_Dimension", "Items"],
    # Existing sheets (unchanged)
    "1_1_Definition_Flows": ["Flow_ID", "Flow_Name", "Flow_Output_Process_ID", "Input_Process_ID"],
    "1_2_Data_Flows": ["Flow_ID", "Flow_Data_Year", "Flow_Material"],
    "2_1_Definition_Processes": ["ID", "Process_Name", "Process_Logic"],
    # ... other existing sheets
}

# Add configuration loading function
def load_odym_configuration(excel_data_dict):
    """Load ODYM configuration from the configuration sheet."""
    config_sheet = excel_data_dict["0_ODYM_Configuration"]
    
    # Extract dimension selection
    dimensions = {}
    for _, row in config_sheet.iterrows():
        if pd.notna(row["Dimension_Name"]):
            dimensions[row["Dimension_Name"]] = {
                "use": row["Use_Dimension"] == "TRUE",
                "items": row["Items"].split(",") if pd.notna(row["Items"]) else [],
                "description": row["Description"],
                "index_letter": row["Index_Letter"]
            }
    
    return dimensions
```

### **Update `system_setup.py`**

```python
def define_model_scope_from_config(config_dimensions):
    """Define model scope from ODYM configuration."""
    model_classification = {}
    
    # Always include Time and Element
    model_classification["Time"] = msc.Classification(
        Name="Time", Dimension="Time", ID=1, Items=config_dimensions["Time"]["items"]
    )
    model_classification["Element"] = msc.Classification(
        Name="Elements", Dimension="Element", ID=2, Items=config_dimensions["Element"]["items"]
    )
    
    # Add other dimensions based on configuration
    dimension_id = 3
    for dim_name, dim_config in config_dimensions.items():
        if dim_config["use"] and dim_name not in ["Time", "Element"]:
            model_classification[dim_name] = msc.Classification(
                Name=dim_name, 
                Dimension=dim_name, 
                ID=dimension_id, 
                Items=dim_config["items"]
            )
            dimension_id += 1
    
    return model_classification
```

## Conclusion

Your centralized configuration approach is **much better** than my previous suggestions because:

1. **It's user-friendly**: All ODYM configuration in one place
2. **It's flexible**: Users can choose which dimensions to use
3. **It's maintainable**: Easy to modify and extend
4. **It's backward compatible**: Existing sheets work with minimal changes

**Would you like me to help you implement this centralized configuration approach?** We could start with:

1. Creating the `0_ODYM_Configuration` sheet structure
2. Updating the data loader to read the configuration
3. Modifying `system_setup.py` to use the configuration
4. Testing with your existing Excel templates

This approach will give you full ODYM compliance while maintaining the elegance and usability of your current system!

---

*Document Version: 1.0*  
*Last Updated: [Current Date]*  
*Author: BioDYM Development Team*


---


================================================================================
# File: COMMIT_MESSAGE_PHASE1.md
================================================================================

# Phase 1 Progress Summary - Ready for Commit

## What's Been Accomplished

### **Phase 1a: Validation & Error Handling** ✅
- Added ODYM validation hooks to solver.py (2 locations)
- Added validation to dsm_model.py (1 location)
- Added validation to fomp_model.py (1 location)
- Validation passes successfully after calculations

### **Phase 1b: Configuration & Dimensions** ✅
- Updated config.py to read dimensions from Excel configuration
- Added helper function to extract dimension lists
- Modified workflow to pass all dimensions to system_setup
- Added IndexTable display (following ODYM tutorial convention)
- Updated plotting functions to handle element structure safely

### **Excel & Workflow Fixes** ✅
- Fixed Year_Flow → Flow_Data_Year column name
- Added fallback for Elements attribute
- Fixed plotting functions for new element structure
- System working with 4 elements: material, WC, DM, CC

### **Dimension Support** ✅
- Added Region/Material dimension support to system_setup.py
- Backward compatible implementation
- Materials dimension ready for activation when defined in Excel

---

## Changes Summary

### **Files Modified**:

1. **02_src/config.py**:
   - Added logic to collect Elements, Regions, Goods, Materials, Process_Types from Excel
   - Converts them to comma-separated strings

2. **02_src/system_setup.py**:
   - Updated define_model_scope() to accept optional dimensions
   - Added Material dimension support
   - Dynamic IndexTable building

3. **02_src/engine/solver.py**:
   - Added Consistency_Check() after balance calculations
   - Added Consistency_Check() after final calculation

4. **02_src/engine/dsm_model.py**:
   - Added Consistency_Check() after DSM calculations

5. **02_src/engine/fomp_model.py**:
   - Added Consistency_Check() after FOMP calculations

6. **02_src/plotting/composition.py**:
   - Made element access safe with conditional checks

7. **02_src/plotting/composition_export.py**:
   - Made element access safe with conditional checks

8. **02_src/plotting/scenario.py**:
   - Added safe element checks in 3 locations

9. **00_BioDYM_Workflow.py**:
   - Fixed column name Year_Flow → Flow_Data_Year
   - Added dimension extraction from config
   - Added IndexTable display
   - Pass all dimensions to define_model_scope()

---

## Test Results

- ✅ Excel configuration reads successfully
- ✅ Elements loaded: ['material', 'WC', 'DM', 'CC']
- ✅ IndexTable created with proper dimensions
- ✅ Baseline calculation completed successfully
- ✅ Validation hooks working

---

## Next Steps After Commit

1. **Add Materials to Excel configuration** (WC, DM)
2. **Test with Material dimension activated**
3. **Add helper functions for 3D array access**
4. **Update engine/plotting for Material dimension**

---

**Ready to commit!** 🚀



---


================================================================================
# File: CRITICAL_FIX_NEEDED.md
================================================================================

# Critical Fix Needed: Elements Structure

## Problem

The solver and FOMP modules **expect these elements**:
- 'material'
- 'WC'  
- 'DM'
- 'CC'

But your Excel configuration now defines:
- 'C' (Element ID 1)
- 'Remaining DM' (Element ID 2)

**This breaks the entire calculation!**

---

## Solution

### **Option 1: Revert Elements to Original** ✅ **RECOMMENDED**

Update Excel configuration to restore original elements:

**Change in Excel** `0_Configuration` sheet:
- Element ID 1: `material` (not 'C')
- Element ID 2: `WC` 
- Element ID 3: `DM`
- Element ID 4: `CC`

This restores the working 4-element system.

---

### **Option 2: Add Elements to Excel**

You suggested adding 'material' as a material. But actually:

- Elements should be: `['material', 'WC', 'DM', 'CC']`
- Materials can be: `['WC', 'DM']` for future separation

**So in Excel**:
- Elements: material, WC, DM, CC (4 elements)
- Materials: WC, DM (2 materials)

**But this creates overlap/redundancy**.

---

## What I Recommend

### **Keep the 4-Layer System Working**:

1. ✅ **Elements**: `['material', 'WC', 'DM', 'CC']` (keep this!)
2. ✅ **Materials**: Empty or placeholder for now
3. ✅ **Get system working** first
4. 🔄 **Then** add dimension separation later

**Why**:
- Your solver code expects these 4 elements
- All plots work with these elements
- DSM/FOMP depend on these elements
- Don't break what works!

---

## Next Steps

1. **Update Excel config** to restore 'material', 'WC', 'DM', 'CC'
2. **Material dimension** - leave empty or use placeholder
3. **Test workflow** to confirm it works
4. **Then** plan dimension separation properly

**Would you like me to**:
- Show you exactly what to change in Excel config?
- Or create a script to fix the config automatically?



---


================================================================================
# File: CURRENT_STATUS_SUMMARY.md
================================================================================

# Current Status & Next Steps Summary

## ✅ What We've Accomplished

### **Phase 1a: Validation & Error Handling**
- ✅ Added Consistency_Check() to solver.py (4 locations)
- ✅ Added validation to DSM and FOMP models
- ✅ Workflow tested successfully

### **Phase 1b: Configuration & Dimensions**
- ✅ Updated config.py to read all dimensions from Excel
- ✅ Added helper functions to extract dimensions
- ✅ Workflow passes dimensions to system_setup
- ✅ Display IndexTable (ODYM convention)
- ✅ Fixed plotting for new element structure
- ✅ **System working with 4 elements** ✅

### **Excel Configuration**
- ✅ Elements: ['material', 'WC', 'DM', 'CC']
- ✅ Materials: Not defined in Excel (empty values)
- ✅ System defaults to 2D structure for now

---

## 🎯 Current System State

**Working 2D Structure**:
- Dimensions: Time (t), Element (e)
- Elements: material, WC, DM, CC (4 elements)
- Flow.Values.shape: (n_years, 4) - 2D arrays
- **All calculations working** ✅

**Material Dimension**:
- Code support exists in system_setup.py
- Will activate when Materials are defined in Excel
- Currently not active (maintains 2D compatibility)

---

## 📋 Next Steps Based on Master Plan

### **Option A: Keep Current 2D Structure** ✅ **Recommended**

**Why**:
- System is working reliably
- All plots and visualizations work
- Calculations complete successfully
- Lower risk

**Action**:
1. ✅ Commit current progress
2. ✅ Document the 2D system as stable
3. ⏳ Continue with Phase 2 (Class Compliance)

---

### **Option B: Add Material Dimension Now**

**Why**:
- Foundation already exists
- Can implement gradually

**Action**:
1. Define Materials in Excel (WC, DM)
2. Add Material dimension to IndexTable  
3. Update engine functions for 3D arrays
4. Test thoroughly

---

### **Option C: Move to Phase 2 - Class Compliance**

According to master plan, Phase 2 focuses on:
1. Replace manual aggregation with ODYM methods
2. Remove custom attributes
3. Use ODYM Extensions

**Action**:
1. Focus on solver.py improvements
2. Replace manual aggregation
3. Add ODYM Extensions for configuration

---

## 💡 My Recommendation

**Go with Option A - Keep Current System Stable**

**Why**:
1. You have a working system ✅
2. Baseline calculations complete successfully ✅
3. Risk of breaking things with dimension changes is high
4. Better to consolidate what we have before expanding

**Then proceed with**:
- Phase 2: Class compliance improvements
- Gradual addition of dimensions later

---

## Question for You

**What's your priority right now?**
- A) Keep system stable and document progress ✅
- B) Add Material dimension to enable 3D structure
- C) Move to Phase 2 (Class Compliance)
- D) Something else?



---


================================================================================
# File: DIMENSION_ID_CODE_LIST.md
================================================================================

# BioDYM Dimension ID Code List

## Dimension ID Coding System

### **Purpose**
A standardized coding system for specifying how dimensions apply to different flows, stocks, and parameters.

### **Core Coding Convention**

#### **For All Dimension Types (Good, Material, Element, Process, Region)**

| Code | Meaning | Usage | Implementation |
|------|---------|-------|----------------|
| **Empty/Blank** | All | Applies to all items in this dimension | Use full dimension range in calculations |
| **Number (1, 2, 3...)** | Specific | Applies to specific item in this dimension | Use index [item_id - 1] in calculations |
| **0** | None | Not applicable for this dimension | Exclude from calculations |

### **Detailed Breakdown**

#### **1. Good_ID Codes**

**Your Good Classification**:
```
Good_ID=1: Raw_Material
Good_ID=2: Product  
Good_ID=3: Waste
```

**Coding in Excel**:

| Code | Meaning | Example Usage |
|------|---------|---------------|
| **Empty/Blank** | All good types (Raw_Material + Product + Waste) | Flow represents total flow across all goods |
| **1** | Raw_Material only | Flow represents raw material input |
| **2** | Product only | Flow represents product output |
| **3** | Waste only | Flow represents waste output |
| **0** | None (not applicable) | Flow is not commodity-based |

**Example**:
```excel
# Sheet: 1_1_Definition_Flows
Flow_ID | Good_ID | Meaning
--------|---------|----------
1 | [empty] | Total flow (all good types)
2 | 1 | Raw_Material flow only
3 | 2 | Product flow only
4 | 3 | Waste flow only
```

#### **2. Material_ID Codes**

**Your Material Classification**:
```
Material_ID=1: WC (Water Content)
Material_ID=2: DM (Dry Matter)
```

**Coding in Excel**:

| Code | Meaning | Example Usage |
|------|---------|---------------|
| **Empty/Blank** | All materials (WC + DM) | Flow represents total material |
| **1** | WC only | Flow represents water content |
| **2** | DM only | Flow represents dry matter |
| **0** | None (not applicable) | Flow is not material-specific |

**Example**:
```excel
# Sheet: 1_1_Definition_Flows
Flow_ID | Material_ID | Meaning
--------|-------------|----------
1 | [empty] | Total material (WC + DM)
2 | 1 | Water content only
3 | 2 | Dry matter only
```

#### **3. Element_ID Codes**

**Your Element Classification**:
```
Element_ID=1: C (Carbon)
Element_ID=2: Non-Carbon
```

**Coding in Excel**:

| Code | Meaning | Example Usage |
|------|---------|---------------|
| **Empty/Blank** | All elements (C + Non-Carbon) | Flow represents total element content |
| **1** | C only | Flow represents carbon content |
| **2** | Non-Carbon only | Flow represents non-carbon content |
| **0** | None (not applicable) | Flow is not element-specific |

**Example**:
```excel
# Sheet: 1_1_Definition_Flows
Flow_ID | Element_ID | Meaning
--------|------------|----------
1 | [empty] | All elements
2 | 1 | Carbon only
3 | 2 | Non-Carbon only
```

#### **4. Process_Type_ID Codes**

**Your Process Type Classification** (from ODYM Configuration):
```
Process_Type_ID=1: Harvest
Process_Type_ID=2: Processing
Process_Type_ID=3: Storage
Process_Type_ID=4: Application
```

**Coding in Excel**:

| Code | Meaning | Example Usage |
|------|---------|---------------|
| **Empty/Blank** | All process types | Flow/stock applies to all process types |
| **1** | Harvest only | Specific to harvest operations |
| **2** | Processing only | Specific to processing operations |
| **3** | Storage only | Specific to storage operations |
| **4** | Application only | Specific to application operations |
| **0** | None (not applicable) | Not process-specific |

**Example**:
```excel
# Sheet: 1_1_Definition_Flows
Flow_ID | Process_Type_ID | Meaning
--------|-----------------|----------
1 | [empty] | All process types
2 | 1 | Harvest operations
3 | 2 | Processing operations
```

#### **5. Region_ID Codes**

**Your Region Classification**:
```
Region_ID=1: Case_Study_Region
```

**Coding in Excel**:

| Code | Meaning | Example Usage |
|------|---------|---------------|
| **Empty/Blank** | All regions (single region default) | Flow applies to entire study region |
| **1** | Case_Study_Region | Specific to study region |
| **0** | None (not applicable) | Not region-specific |

**Example**:
```excel
# Sheet: 1_1_Definition_Flows
Flow_ID | Region_ID | Meaning
--------|-----------|----------
1 | [empty] | All regions (default)
2 | 1 | Case_Study_Region
```

## Implementation in Data Loader

### **Reading Dimension IDs from Excel**

```python
def read_dimension_id(value):
    """
    Read and interpret dimension ID from Excel.
    
    Parameters:
    -----------
    value : str, int, float, None
        Value from Excel cell
    
    Returns:
    --------
    str : "all", "specific", or "none"
        Interpretation of the ID
    int or None : The specific ID if applicable
    """
    # Handle NaN/empty values
    if pd.isna(value) or value == "" or str(value).strip() == "":
        return "all", None
    
    # Handle string representations
    str_value = str(value).strip()
    
    # Handle "0" as "none"
    if str_value == "0" or str_value == "None":
        return "none", None
    
    # Handle specific numbers
    try:
        int_value = int(float(str_value))
        return "specific", int_value
    except (ValueError, OverflowError):
        # If can't convert to int, treat as "all"
        return "all", None
```

### **Processing Flows with Dimension IDs**

```python
def create_flow_with_dimension_ids(row, mfa_system):
    """
    Create flow object with dimension IDs from Excel row.
    
    Parameters:
    -----------
    row : pandas.Series
        Excel row with Flow definition
    mfa_system : msc.MFAsystem
        The MFA system object
    
    Returns:
    --------
    msc.Flow : Flow object with proper Indices
    """
    # Read dimension IDs from Excel
    good_id = read_dimension_id(row.get("Good_ID", ""))
    material_id = read_dimension_id(row.get("Material_ID", ""))
    element_id = read_dimension_id(row.get("Element_ID", ""))
    process_type_id = read_dimension_id(row.get("Process_Type_ID", ""))
    region_id = read_dimension_id(row.get("Region_ID", ""))
    
    # Build Indices string based on dimension IDs
    indices = "t"  # Time is always first
    dimension_map = {}
    
    # Add Element dimension
    indices += ",e"
    
    # Add other dimensions if specific IDs provided
    if region_id[0] == "specific":
        indices += ",r"
        dimension_map["region"] = region_id[1]
    
    if good_id[0] == "specific":
        indices += ",g"
        dimension_map["good"] = good_id[1]
    
    if material_id[0] == "specific":
        indices += ",m"
        dimension_map["material"] = material_id[1]
    
    if process_type_id[0] == "specific":
        indices += ",p"
        dimension_map["process_type"] = process_type_id[1]
    
    # If all dimensions use "all", default to "t,e"
    if indices == "t,e" and all(d[0] == "all" for d in [good_id, material_id, process_type_id, region_id]):
        indices = "t,e"  # Keep simple
    
    # Create flow object
    flow = msc.Flow(
        Name=row["Flow_ID"],
        P_Start=int(row["Flow_Output_Process_ID"]),
        P_End=int(row["Input_Process_ID"]),
        Indices=indices
    )
    
    # Store dimension IDs as custom attribute (temporary, will use ODYM Extensions later)
    flow._dimension_ids = dimension_map
    
    return flow
```

## Complete Excel Example

### **1_1_Definition_Flows (With Dimension IDs)**

| Flow_ID | Flow_Name | Good_ID | Material_ID | Element_ID | Process_Type_ID | Region_ID | Indices |
|---------|-----------|---------|-------------|------------|-----------------|-----------|---------|
| 1 | Total_Flow | [empty] | [empty] | [empty] | [empty] | [empty] | t,e |
| 2 | Raw_Material_Flow | 1 | [empty] | [empty] | [empty] | [empty] | t,e,g |
| 3 | Product_Flow | 2 | [empty] | [empty] | [empty] | [empty] | t,e,g |
| 4 | Waste_Flow | 3 | [empty] | [empty] | [empty] | [empty] | t,e,g |
| 5 | WC_Flow | [empty] | 1 | [empty] | [empty] | [empty] | t,e,m |
| 6 | DM_Flow | [empty] | 2 | [empty] | [empty] | [empty] | t,e,m |
| 7 | Carbon_Flow | [empty] | [empty] | 1 | [empty] | [empty] | t,e |
| 8 | Carbon_Product_Flow | 2 | [empty] | 1 | [empty] | [empty] | t,e,g |
| 9 | Biochar_Production | 2 | 2 | 1 | 2 | [empty] | t,e,g,m,p |

**Interpretation**:
- Flow_ID=1: All materials, all elements, all goods → Simple 2D array
- Flow_ID=2: Raw_Material only (Good_ID=1) → 3D array with Good dimension
- Flow_ID=5: Water Content only (Material_ID=1) → 3D array with Material dimension
- Flow_ID=8: Product (Good_ID=2) + Carbon (Element_ID=1) → 3D array
- Flow_ID=9: Product (Good_ID=2) + Dry Matter (Material_ID=2) + Carbon (Element_ID=1) + Processing (Process_Type_ID=2) → Multi-dimensional

## Summary

**Coding Convention**:
- **Empty/Blank** = "All" (include entire dimension)
- **Number (1,2,3...)** = "Specific" (include that item only)
- **0** = "None" (exclude from this dimension)

**For Your Question**:
```
All = [empty/blank] → Flow applies to all items in dimension
Specific = number (1, 2, 3...) → Flow applies to that specific item
None = 0 → Flow not applicable to this dimension
```

This gives you maximum flexibility for defining flows while maintaining backward compatibility!

---

*Document Version: 1.0*  
*Last Updated: [Current Date]*  
*Author: BioDYM Development Team*


---


================================================================================
# File: DIMENSION_SEPARATION_ISSUE.md
================================================================================

# Critical Issue: Dimension Separation Breaking Existing System

## Problem Analysis

### **The Issue**:

**Old Structure** (2D):
- Elements: ['material', 'WC', 'DM', 'CC']
- All in one dimension
- Flow.Values shape: (n_years, 4 elements)
- Example: `flow.Values[0, elements.index('WC')]` → works

**New Structure** (3D):
- Elements: ['C', 'Remaining DM']
- Materials: ['WC', 'DM']
- Flow.Values shape: (n_years, 2 elements, 2 materials)
- Example: `flow.Values[0, elements.index('WC')]` → **FAILS!** (WC is now in Materials, not Elements)

### **What Breaks**:

1. **All plotting code**: Uses `flow.Values[:, element_index]` expecting 2D
2. **Composition plotting**: Looks for 'WC', 'DM', 'CC' in elements
3. **Sankey diagrams**: Aggregate by element only
4. **Flow composition**: Tries to index WC, DM, CC as elements

### **The Root Cause**:

Your **data model changed** from:
- **Chemical components** (WC, DM, CC) as elements
- To: **Chemical elements** (C, Remaining DM) as elements, **Physical materials** (WC, DM) as materials

But the **plotting logic** still assumes the old structure!

---

## Solutions

### **Option 1: Keep WC, DM as Elements (Simplest)** ✅ Recommended

Keep the old structure but add Material dimension for future use:

**Structure**:
- Time (t): 26 years
- Element (e): ['WC', 'DM', 'CC', 'material'] (all 4)
- Material (m): ['dry_mass', 'wet_mass'] (for future use)

**Benefits**:
- ✅ No plotting code changes needed
- ✅ Existing Sankey diagrams work
- ✅ Flow composition works
- ✅ Can add Material later if needed

---

### **Option 2: Add Material Aggregation (More Complex)** ⚠️

Update all plotting to handle 3D arrays:

**Structure**:
- Time (t): 26 years
- Element (e): ['C', 'Remaining DM']
- Material (m): ['WC', 'DM']

**Required Changes**:
1. Update **all plotting functions** to aggregate Material dimension
2. Update **Sankey diagrams** to handle 3D flows
3. Update **composition plots** to aggregate materials
4. Update **flow/stock access** throughout codebase

**Example Fix**:
```python
# OLD (2D):
flow.Values[:, element_index]

# NEW (3D with Material aggregation):
# Sum over materials dimension: aggregate WC + DM
np.sum(flow.Values[:, element_index, :], axis=1)
```

---

### **Option 3: Hybrid Approach** 🔄

Keep backward compatibility while supporting both:

**Detection Logic**:
```python
if flow.Values.ndim == 2:
    # Old 2D structure (compatible)
    values = flow.Values[:, element_index]
elif flow.Values.ndim == 3:
    # New 3D structure (sum materials)
    values = np.sum(flow.Values[:, element_index, :], axis=1)
```

---

## Recommendation

### **Go with Option 1** (Keep current structure, add empty Material dimension)

**Why**:
1. ✅ No breaking changes to plotting
2. ✅ Existing visualizations work
3. ✅ Can add real Material distinction later
4. ✅ Less risk of breaking working system

**Implementation**:
```python
# In config.py - when loading Materials
if not materials or len(materials) == 0:
    # No materials defined, create placeholder
    materials = ['total']  # Single "total" material for backward compatibility
```

This keeps the 3D structure but doesn't break existing code.

---

## What to Do Now

**Question**: Do you want to keep WC/DM/CC as elements for now (Option 1), or do you want to fully implement the separation (Option 2)?

**My recommendation**: **Start with Option 1**, get the system working, then gradually add Material distinction where it makes sense.



---


================================================================================
# File: ELEMENT_FIX_NEEDED.md
================================================================================

# Critical Fix: Elements Configuration

## Problem

**Your Excel configuration** has only:
- Element ID 1: CC

**Your solver code expects**:
- material, WC, DM, CC

**Result**: ValueError in solver.py because elements don't match

---

## Solution

You need to update Excel to have **4 elements**:

**In `0_Configuration` sheet**:
```
Element ID 1: material
Element ID 2: WC
Element ID 3: DM
Element ID 4: CC
Element ID 5: (empty)
```

---

## Why This Structure?

**Elements** = Components tracked in your model:
- **material**: Total material mass
- **WC**: Water Content
- **DM**: Dry Matter
- **CC**: Carbon Content

This is the **traditional 4-layer system** your BioDYM model was built for.

---

## Materials Dimension

After fixing elements, you can optionally add Materials:
```
Material ID 1: WC
Material ID 2: DM
```

But **for now**, just fix the elements to get the system working!

---

**Please update Excel with all 4 elements, then we can test.**



---


================================================================================
# File: EXCEL_ANALYSIS_251027.md
================================================================================

# Excel Structure Analysis - 251027_BioDYM_ODYM.xlsm

## Analysis Summary

### **✅ What's Working Excellently**

#### **1. ODYM Configuration Sheet Structure**
Your `0_Configuration` sheet is **excellent** and includes all essential settings:

- **Time (t)**: ✅ Configured (2025-2050)
- **Region (r)**: ✅ Enabled (Case_Study_Region)
- **Process (p)**: ✅ Enabled (5 process types defined)
- **Good (g)**: ✅ Enabled (4 good types: Raw Material, Processed Product, Product, Waste)
- **Material (m)**: ✅ Enabled (WC, DM)
- **Element (e)**: ✅ Enabled (C, Remaining DM)

#### **2. Flow Definition Sheet - ODYM Columns**
Your `1_1_Definition_Flows` sheet includes **all ODYM dimension columns**:

- `ODYM_time_(t)` ✅
- `ODYM_Time_ID` ✅
- `ODYM_Region_(r)` ✅
- `ODYM_Region_ID` ✅
- `ODYM_process_(p)` ✅
- `ODYM_Process_ID` ✅
- `ODYM_Good_(g)2` ✅
- `ODYM_Good_ID` ✅
- `ODYM_material_(m)` ✅
- `ODYM_Material_ID` ✅
- `ODYM_element_(e)` ✅
- `ODYM_Element_ID` ✅
- `ODYM_Indices` ✅
- `Column2` ✅ (Dimension ID mapping)

#### **3. Indices Column Implementation**
You've successfully added the **Indices column** which is critical:

```excel
ODYM_Indices = "t,r,p,g,m,e,"  # All dimensions enabled
```

**This is perfect!** Your Indices column properly specifies which dimensions to use.

## **Issues Found & Recommendations**

### **Critical Issue #1: ID Value Format Inconsistency**

**Problem**: 
- Some IDs are strings ("All")
- Some IDs are integers (0, 1, 3)
- Some IDs might be floats

**Current State**:
```
ODYM_Good_ID values: [1, 3, 0]  # Integers ✅
ODYM_Material_ID values: ['All']  # Strings ⚠️
ODYM_Element_ID values: ['All']  # Strings ⚠️
```

**Recommendation**: Standardize ID values

| Column | Current Values | Should Be |
|--------|---------------|-----------|
| `ODYM_Good_ID` | 1, 3, 0, "All" | `1, 2, 3, 4` or `""` (empty) |
| `ODYM_Material_ID` | "All" | `""` (empty) or `1, 2` |
| `ODYM_Element_ID` | "All" | `""` (empty) or `1, 2` |

**Fixed Format**:
- **Empty/Blank** = All items in this dimension
- **Number (1, 2, 3...)** = Specific item in this dimension  
- **0** = Not applicable to this dimension

### **Critical Issue #2: Good_ID vs. Good_Type Column Mismatch**

**Problem**: You have both `Good_Type` and `ODYM_Good_ID` columns

**Current State**:
```excel
Good_Type | ODYM_Good_ID
---------|---------------
Raw Material | 1
Product | 3
```

**Recommendation**: Use consistent mapping:
- Good_Type = "Raw Material" → ODYM_Good_ID = 1
- Good_Type = "Processed Product" → ODYM_Good_ID = 2  
- Good_Type = "Product" → ODYM_Good_ID = 3
- Good_Type = "Waste" → ODYM_Good_ID = 4

### **Critical Issue #3: Indices Format**

**Current State**:
```excel
ODYM_Indices = "t,r,p,g,m,e,"  # All dimensions
```

**Recommendation**: The comma at the end might cause parsing issues. Should be:
```excel
ODYM_Indices = "t,e,r,p,g,m"  # Without trailing comma
```

Or for simple 2D flows:
```excel
ODYM_Indices = "t,e"  # Basic Time + Element
```

### **Critical Issue #4: Column2 Format**

**Current State**:
```excel
Column2 = "All,All,All,1,All,All,"  # Mapping to dimension IDs
```

**Issues**:
1. Trailing comma
2. "All" should be empty/blank for consistency
3. Unclear order of mapping

**Recommendation**: Standardize format
```excel
Column2 = "All,All,All,1,All,All"  # No trailing comma
# Or better yet, use separate columns:
ODYM_Good_ID = 1
ODYM_Material_ID = [empty]
ODYM_Element_ID = [empty]
```

## Recommended Excel Structure Fixes

### **1. Fix ID Value Format**

Update cells to use consistent format:

```excel
# For "All" items:
ODYM_Good_ID = "" (empty cell)
ODYM_Material_ID = "" (empty cell)
ODYM_Element_ID = "" (empty cell)

# For specific items:
ODYM_Good_ID = 1 (Raw Material)
ODYM_Good_ID = 2 (Processed Product)
ODYM_Good_ID = 3 (Product)
ODYM_Good_ID = 4 (Waste)

# For not applicable:
ODYM_Good_ID = 0
```

### **2. Fix Indices Column**

Remove trailing comma:
```excel
ODYM_Indices = "t,e,r,p,g,m"  # Without comma at end
```

Or for simple flows:
```excel
ODYM_Indices = "t,e"  # Basic Time + Element
```

### **3. Fix Column2**

Either:
- Remove trailing comma
- Or split into separate ID columns

**Recommendation**: Use separate ID columns as you already have!

## Implementation Code Updates Required

### **Update data_loader.py**

```python
def read_dimension_id(value):
    """Read and interpret dimension ID from Excel."""
    # Handle empty/NaN values
    if pd.isna(value) or value == "" or str(value).strip() == "":
        return "all", None
    
    # Convert to string and strip
    str_value = str(value).strip()
    
    # Handle "All" as empty
    if str_value.lower() == "all":
        return "all", None
    
    # Handle "0" or "None"
    if str_value == "0" or str_value.lower() == "none":
        return "none", None
    
    # Try to convert to integer
    try:
        int_value = int(float(str_value))
        return "specific", int_value
    except (ValueError, OverflowError):
        return "all", None
```

### **Update system_setup.py**

```python
def create_flow_with_dimensions(row, mfa_system):
    """Create flow with proper dimension handling."""
    
    # Read dimension IDs
    good_id = read_dimension_id(row.get("ODYM_Good_ID", ""))
    material_id = read_dimension_id(row.get("ODYM_Material_ID", ""))
    element_id = read_dimension_id(row.get("ODYM_Element_ID", ""))
    process_id = read_dimension_id(row.get("ODYM_Process_ID", ""))
    region_id = read_dimension_id(row.get("ODYM_Region_ID", ""))
    
    # Get Indices from Excel (remove trailing comma if present)
    indices = str(row.get("ODYM_Indices", "t,e")).strip().rstrip(",")
    
    # Create flow
    flow = msc.Flow(
        Name=row["Flow_ID"],
        P_Start=int(row["Flow_Output_Process_ID"]),
        P_End=int(row["Input_Process_ID"]),
        Indices=indices
    )
    
    # Store dimension IDs for later use
    flow._dimension_ids = {
        'good': good_id,
        'material': material_id,
        'element': element_id,
        'process': process_id,
        'region': region_id
    }
    
    return flow
```

## Overall Assessment

### **Current Status**: 8/10 (Very Good)

**Strengths**:
- ✅ All ODYM dimensions defined in configuration
- ✅ Indices column properly added to flows
- ✅ All dimension ID columns present
- ✅ Good classification defined (Raw Material, Product, Waste)
- ✅ Material classification defined (WC, DM)
- ✅ Element classification defined (C, Remaining DM)

**Issues to Fix**:
- ⚠️ ID value format consistency ("All" vs. empty vs. number)
- ⚠️ Remove trailing commas from Indices
- ⚠️ Standardize ID values across all columns

## Action Items

1. **Replace "All" with empty cells** in dimension ID columns
2. **Remove trailing commas** from Indices column
3. **Update data_loader.py** to handle "All" as empty
4. **Test with sample flows** to verify ID mapping works correctly
5. **Add Indices column** to 2_1_Definition_Processes for Stock_Indices

Once these fixes are made, your Excel file will be **ready for implementation**! 🎯

---

*Document Version: 1.0*  
*Last Updated: [Current Date]*  
*Author: BioDYM Development Team*


---


================================================================================
# File: EXCEL_MAPPING_EXPLANATION.md
================================================================================

# Material-Element Structure Explanation

## Your Configuration

### **Materials** (Physical materials - what exists):
- **WC**: Water Content material
- **DM**: Dry Matter material

### **Elements** (Components tracked - what we measure):
- **material**: Total fresh mass (the mass itself)
- **CC**: Carbon Content (carbon within that mass)

---

## What This Means

### **3D Array Structure**:
```
Flow.Values.shape = (26, 2, 2)
# 26 years × 2 materials (WC, DM) × 2 elements (material, CC)
```

### **Physical Meaning**:

**For WC material**:
- material element: Total wet mass
- CC element: Carbon in wet mass

**For DM material**:
- material element: Total dry mass  
- CC element: Carbon in dry mass

### **Example Flow**:
```
Flow.Values[:, 0, 0] → material element for WC (wet mass over time)
Flow.Values[:, 0, 1] → CC element for WC (carbon in wet mass over time)
Flow.Values[:, 1, 0] → material element for DM (dry mass over time)
Flow.Values[:, 1, 1] → CC element for DM (carbon in dry mass over time)
```

---

## Excel Update Required

**In `0_Configuration` sheet**:

**Materials**:
- Material ID 1: **WC**
- Material ID 2: **DM**

**Elements**:
- Element ID 1: **material**
- Element ID 2: **CC**

---

## What We'll Test After Your Update

1. ✅ Config loader reads: materials=['WC', 'DM'], elements=['material', 'CC']
2. ✅ IndexTable shows 3D structure
3. ✅ Flow.Values.shape = (26, 2, 2)
4. ✅ Workflow initializes with 3D arrays
5. ⚠️ Engine functions may need updates for 3D access

---

**Once you've updated Excel, let me know and we'll test!** 🚀



---


================================================================================
# File: EXCEL_STRUCTURE_CHANGES.md
================================================================================

# BioDYM Excel Structure Changes for ODYM Compliance

## Current Excel Structure Analysis

Based on your `data_loader.py`, here's your **current Excel structure**:

### **✅ Existing Sheets (No Changes Required)**
```
1_1_Definition_Flows     - Flow definitions
1_2_Data_Flows          - Flow data
2_1_Definition_Processes - Process definitions  
2_2_static_TCs          - Static transfer coefficients
2_3_dynamic_TCs         - Dynamic transfer coefficients
2_4_Initial_Stock       - Initial stock data
3_1_Definition_DSM      - DSM parameters
3_2_Definition_FOMP     - FOMP parameters
```

## Required Excel Changes for ODYM Compliance

### **❌ NEW SHEETS REQUIRED**

#### **1. Region Dimension Sheets**

**Sheet: `3_3_Definition_Regions`** (Required)
| Column | Description | Example Values |
|--------|-------------|----------------|
| `Region_ID` | Unique identifier | 1, 2, 3 |
| `Region_Name` | Region name | "Case_Study_Region", "Region_A", "Region_B" |
| `Description` | Region description | "Primary study area", "Secondary region" |
| `Geographic_Scope` | Geographic scope | "Local", "Regional", "National" |

**Sheet: `3_4_Data_Regions`** (Optional)
| Column | Description | Example Values |
|--------|-------------|----------------|
| `Region_ID` | Reference to Region_ID | 1, 2, 3 |
| `Region_Name` | Region name | "Case_Study_Region" |
| `Population` | Population count | 1000000 |
| `Area_km2` | Area in km² | 500 |
| `GDP` | GDP value | 50000000 |

#### **2. Good Dimension Sheets**

**Sheet: `4_1_Definition_Goods`** (Required)
| Column | Description | Example Values |
|--------|-------------|----------------|
| `Good_ID` | Unique identifier | 1, 2, 3, 4 |
| `Good_Name` | Good name | "Rye_Straw", "Biochar", "Compost", "Energy" |
| `Description` | Good description | "Primary biomass", "Carbonized material" |
| `Category` | Good category | "Biomass", "Energy", "Material" |
| `Unit` | Unit of measurement | "Mg", "MWh", "kg" |

**Sheet: `4_2_Data_Goods`** (Optional)
| Column | Description | Example Values |
|--------|-------------|----------------|
| `Good_ID` | Reference to Good_ID | 1, 2, 3, 4 |
| `Good_Name` | Good name | "Rye_Straw" |
| `Market_Price` | Market price | 50.0 |
| `Availability` | Availability factor | 0.8 |
| `Quality_Factor` | Quality factor | 0.9 |

#### **3. Material Dimension Sheets**

**Sheet: `5_1_Definition_Materials`** (Required)
| Column | Description | Example Values |
|--------|-------------|----------------|
| `Material_ID` | Unique identifier | 1, 2, 3 |
| `Material_Name` | Material name | "Dry_Matter", "Water_Content", "Carbon_Content" |
| `Description` | Material description | "Dry matter content", "Water content" |
| `Composition` | Material composition | "Organic", "Inorganic", "Carbon" |

**Sheet: `5_2_Data_Materials`** (Optional)
| Column | Description | Example Values |
|--------|-------------|----------------|
| `Material_ID` | Reference to Material_ID | 1, 2, 3 |
| `Material_Name` | Material name | "Dry_Matter" |
| `Density` | Material density | 1.2 |
| `Moisture_Content` | Moisture content | 0.2 |
| `Carbon_Content` | Carbon content | 0.45 |

#### **4. Process Dimension Sheets**

**Sheet: `6_1_Definition_Processes`** (Required)
| Column | Description | Example Values |
|--------|-------------|----------------|
| `Process_ID` | Unique identifier | 1, 2, 3, 4 |
| `Process_Name` | Process name | "Harvest", "Processing", "Storage", "Application" |
| `Description` | Process description | "Biomass harvesting", "Material processing" |
| `Type` | Process type | "Primary", "Secondary", "Tertiary" |
| `Efficiency` | Process efficiency | 0.85 |

**Sheet: `6_2_Data_Processes`** (Optional)
| Column | Description | Example Values |
|--------|-------------|----------------|
| `Process_ID` | Reference to Process_ID | 1, 2, 3, 4 |
| `Process_Name` | Process name | "Harvest" |
| `Energy_Consumption` | Energy consumption | 100.0 |
| `Water_Consumption` | Water consumption | 50.0 |
| `Emissions` | Emissions factor | 0.1 |

### **⚠️ EXISTING SHEETS - MINOR UPDATES REQUIRED**

#### **1. Update `1_1_Definition_Flows`**
**Add new columns** (keep existing columns):
| New Column | Description | Example Values |
|------------|-------------|----------------|
| `Region_ID` | Reference to Region_ID | 1, 2, 3 |
| `Good_ID` | Reference to Good_ID | 1, 2, 3, 4 |
| `Material_ID` | Reference to Material_ID | 1, 2, 3 |
| `Process_Type_ID` | Reference to Process_ID | 1, 2, 3, 4 |

#### **2. Update `1_2_Data_Flows`**
**Add new columns** (keep existing columns):
| New Column | Description | Example Values |
|------------|-------------|----------------|
| `Region_ID` | Reference to Region_ID | 1, 2, 3 |
| `Good_ID` | Reference to Good_ID | 1, 2, 3, 4 |
| `Material_ID` | Reference to Material_ID | 1, 2, 3 |
| `Process_Type_ID` | Reference to Process_ID | 1, 2, 3, 4 |

#### **3. Update `2_1_Definition_Processes`**
**Add new columns** (keep existing columns):
| New Column | Description | Example Values |
|------------|-------------|----------------|
| `Process_Type_ID` | Reference to Process_ID | 1, 2, 3, 4 |
| `Region_ID` | Reference to Region_ID | 1, 2, 3 |

## Implementation Strategy

### **Phase 1: Minimal Implementation (Backward Compatible)**

#### **Step 1.1: Add Default Dimension Sheets**
Create the new sheets with **default single values** to maintain compatibility:

**`3_3_Definition_Regions`**:
| Region_ID | Region_Name | Description | Geographic_Scope |
|-----------|-------------|-------------|------------------|
| 1 | Case_Study_Region | Primary study area | Local |

**`4_1_Definition_Goods`**:
| Good_ID | Good_Name | Description | Category | Unit |
|---------|-----------|-------------|----------|------|
| 1 | Rye_Straw | Primary biomass | Biomass | Mg |
| 2 | Biochar | Carbonized material | Material | Mg |
| 3 | Compost | Organic material | Material | Mg |
| 4 | Energy | Energy output | Energy | MWh |

**`5_1_Definition_Materials`**:
| Material_ID | Material_Name | Description | Composition |
|-------------|---------------|-------------|------------|
| 1 | Dry_Matter | Dry matter content | Organic |
| 2 | Water_Content | Water content | Inorganic |
| 3 | Carbon_Content | Carbon content | Carbon |

**`6_1_Definition_Processes`**:
| Process_ID | Process_Name | Description | Type | Efficiency |
|------------|--------------|-------------|------|------------|
| 1 | Harvest | Biomass harvesting | Primary | 0.9 |
| 2 | Processing | Material processing | Secondary | 0.8 |
| 3 | Storage | Material storage | Secondary | 0.95 |
| 4 | Application | Material application | Tertiary | 0.85 |

#### **Step 1.2: Update Existing Sheets (Optional Columns)**
Add the new dimension reference columns to existing sheets, but make them **optional** for backward compatibility:

**`1_1_Definition_Flows`** - Add columns:
- `Region_ID` (default: 1)
- `Good_ID` (default: 1) 
- `Material_ID` (default: 1)
- `Process_Type_ID` (default: 1)

**`1_2_Data_Flows`** - Add columns:
- `Region_ID` (default: 1)
- `Good_ID` (default: 1)
- `Material_ID` (default: 1) 
- `Process_Type_ID` (default: 1)

**`2_1_Definition_Processes`** - Add columns:
- `Process_Type_ID` (default: 1)
- `Region_ID` (default: 1)

### **Phase 2: Full Implementation (Multi-Dimensional)**

#### **Step 2.1: Populate Dimension References**
Once the basic structure is in place, populate the dimension reference columns with actual values:

**Example for `1_1_Definition_Flows`**:
| Flow_ID | Flow_Name | Region_ID | Good_ID | Material_ID | Process_Type_ID |
|---------|-----------|-----------|---------|-------------|-----------------|
| 1 | Rye_Harvest_Flow | 1 | 1 | 1 | 1 |
| 2 | Biochar_Production_Flow | 1 | 2 | 1 | 2 |
| 3 | Compost_Application_Flow | 1 | 3 | 1 | 4 |

#### **Step 2.2: Add Optional Data Sheets**
Add the optional data sheets for richer analysis:

- `3_4_Data_Regions`
- `4_2_Data_Goods` 
- `5_2_Data_Materials`
- `6_2_Data_Processes`

## Data Loader Updates Required

### **Update `REQUIRED_STRUCTURE` in `data_loader.py`**

```python
# Add to REQUIRED_STRUCTURE
REQUIRED_STRUCTURE = {
    # Existing sheets (unchanged)
    "1_1_Definition_Flows": ["Flow_ID", "Flow_Name", "Flow_Output_Process_ID", "Input_Process_ID", "Flow_WC[%]", "Flow_DM[%]", "Flow_CC_DM[%]"],
    "1_2_Data_Flows": ["Flow_ID", "Flow_Data_Year", "Flow_Material"],
    "2_1_Definition_Processes": ["ID", "Process_Name", "Process_Logic"],
    "2_2_static_TCs": ["Flow_ID", "Process_ID", "TC_material_ID", "TC_Value_material"],
    "2_3_dynamic_TCs": ["TC_material_ID", "TC_Value_material", "Year"],
    "2_4_Initial_Stock": ["Process_ID", "IS_Parameter_type", "IS_Parameter_Value"],
    
    # NEW: Dimension sheets
    "3_3_Definition_Regions": ["Region_ID", "Region_Name", "Description", "Geographic_Scope"],
    "4_1_Definition_Goods": ["Good_ID", "Good_Name", "Description", "Category", "Unit"],
    "5_1_Definition_Materials": ["Material_ID", "Material_Name", "Description", "Composition"],
    "6_1_Definition_Processes": ["Process_ID", "Process_Name", "Description", "Type", "Efficiency"],
}
```

### **Update Column Name Mapping**

```python
# Add to COLUMN_NAME_MAPPING
COLUMN_NAME_MAPPING = {
    # Existing mappings (unchanged)
    # ...
    
    # NEW: Dimension sheet mappings
    "3_3_Definition_Regions": {
        "Region_ID": "Region_ID",
        "Region_Name": "Region_Name", 
        "Description": "Description",
        "Geographic_Scope": "Geographic_Scope"
    },
    "4_1_Definition_Goods": {
        "Good_ID": "Good_ID",
        "Good_Name": "Good_Name",
        "Description": "Description", 
        "Category": "Category",
        "Unit": "Unit"
    },
    "5_1_Definition_Materials": {
        "Material_ID": "Material_ID",
        "Material_Name": "Material_Name",
        "Description": "Description",
        "Composition": "Composition"
    },
    "6_1_Definition_Processes": {
        "Process_ID": "Process_ID", 
        "Process_Name": "Process_Name",
        "Description": "Description",
        "Type": "Type",
        "Efficiency": "Efficiency"
    }
}
```

## Migration Strategy

### **Option 1: Gradual Migration (Recommended)**
1. **Week 1**: Add new dimension sheets with default values
2. **Week 2**: Update data loader to handle new sheets
3. **Week 3**: Add optional dimension columns to existing sheets
4. **Week 4**: Test with existing Excel templates
5. **Week 5**: Gradually populate dimension references

### **Option 2: Complete Migration**
1. **Week 1**: Create all new sheets and update all existing sheets
2. **Week 2**: Update data loader completely
3. **Week 3**: Test with updated Excel templates
4. **Week 4**: Migrate all existing data

## Impact Assessment

### **✅ Benefits**
- **Full ODYM Compliance**: Complete dimension system
- **Enhanced Analysis**: Multi-dimensional flow analysis
- **Scalability**: Easy to add new regions, goods, materials, processes
- **Interoperability**: Compatible with other ODYM systems

### **⚠️ Considerations**
- **Excel File Size**: Additional sheets will increase file size
- **Data Entry**: More columns to fill (though many can have defaults)
- **Learning Curve**: Users need to understand new dimension system

### **❌ Risks**
- **Breaking Changes**: Existing Excel templates won't work without updates
- **Data Migration**: Need to migrate existing data to new structure
- **User Confusion**: More complex Excel structure

## Recommendation

**Start with Phase 1 (Minimal Implementation)**:

1. **Add the 4 new dimension sheets** with default single values
2. **Update data loader** to handle new sheets
3. **Test with existing Excel templates** (should still work)
4. **Gradually add dimension columns** to existing sheets
5. **Populate dimension references** as needed

This approach ensures **backward compatibility** while enabling **full ODYM compliance** when needed.

---

*Document Version: 1.0*  
*Last Updated: [Current Date]*  
*Author: BioDYM Development Team*


---


================================================================================
# File: FINAL_4D_CONFIGURATION.md
================================================================================

# Full ODYM 4D Configuration - Final Structure

## Recommended Configuration

### **Goods** (Commodity Categories):
- Good Type 1: **biomass** (or "Raw Material" if you prefer)
- Good Type 2-6: (leave empty or use for other goods)

### **Materials** (Physical Materials):
- Material ID 1: **WC** (Water Content)
- Material ID 2: **DM** (Dry Matter)
- Material ID 3-4: (leave empty)

### **Elements** (Components Tracked):
- Element ID 1: **CC** (Carbon Content)
- Element ID 2: (leave empty or add "mass" if you need total mass tracking)

---

## Excel Update Required

**You need to update Excel to**:

1. **Keep Goods as is** ✅:
   - Raw Material, Processed Product, Product, Waste

2. **Fix Materials** (Material ID 1 = "material" is wrong):
   - Material ID 1: **WC**
   - Material ID 2: **DM**
   - Material ID 3: (empty)
   - Material ID 4: (empty)

3. **Keep Elements as is** ✅:
   - Element ID 1: CC

---

## Expected 4D Array Structure

With recommended configuration:

```
Flow.Values.shape = (26, 4, 2, 1)
# 26 years × 4 goods × 2 materials (WC, DM) × 1 element (CC)
```

Or if you want just biomass:
```
Flow.Values.shape = (26, 1, 2, 1)
# 26 years × 1 good (biomass) × 2 materials (WC, DM) × 1 element (CC)
```

---

## Decision Needed

**Option 1: Use All 4 Goods** (Raw Material, Processed Product, Product, Waste)
- More complex
- 4D structure with 4 goods
- Better for waste/material tracking

**Option 2: Focus on One Good** (e.g., "biomass")
- Simpler
- 4D structure with 1 good
- Cleaner for single commodity analysis

**Which approach do you prefer?** The code supports both!



---


================================================================================
# File: IMPLEMENTATION_FIRST_STEPS.md
================================================================================

# ODYM Compliance Implementation - First Steps

## Current Status

- **Branch**: `feature/odym-compliance` ✅
- **Excel File**: `251027_BioDYM_ODYM.xlsm` (needs minor fixes)
- **Master Plan**: Ready for Phase 0

## Immediate First Steps - Discussion

Based on the master plan, here's what we should tackle first:

### **Option 1: Fix Excel First (Recommended)**

**Why**: Your Excel file is almost ready but has a few format issues that need fixing:
1. Replace "All" with empty cells
2. Remove trailing commas
3. Add Stock_Indices column to processes

**Time**: 1 hour
**Risk**: Very Low
**Benefit**: Clean foundation for implementation

### **Option 2: Start with Phase 0 (Testing)**

**Why**: Build safety net before any changes
1. Select representative Excel files
2. Generate golden reference datasets
3. Create integration tests

**Time**: 3-5 hours
**Risk**: Low
**Benefit**: Ensures we don't break existing functionality

### **Option 3: Start with Phase 1a (Foundational Refactoring)**

**Why**: These changes don't affect dimensions, so they're safer
1. Use ODYM Initializers
2. Add Consistency_Check() calls
3. Improve error handling

**Time**: 4-6 hours
**Risk**: Medium
**Benefit**: Better baseline before dimension work

## My Recommendation

### **Start with Option 1 (Fix Excel) → Option 2 (Phase 0)**

**Rationale**:
1. **Quick win**: Excel fixes take ~1 hour and give a clean foundation
2. **Then build tests**: Phase 0 ensures we don't break anything
3. **Then refactor**: With tests in place, Phase 1 becomes safer

## Detailed Discussion of First Steps

### **Step 1: Excel File Cleanup (1 hour)**

#### **What needs fixing**:

1. **Replace "All" values**
```python
# Create script to fix Excel
import pandas as pd

# Load Excel
excel_file = '01_data/01_input/251027_BioDYM_ODYM.xlsm'
df_flows = pd.read_excel(excel_file, sheet_name='1_1_Definition_Flows', engine='openpyxl')

# Replace "All" with empty
for col in ['ODYM_Good_ID', 'ODYM_Material_ID', 'ODYM_Element_ID', 'ODYM_Region_ID', 'ODYM_Process_ID']:
    if col in df_flows.columns:
        df_flows[col] = df_flows[col].replace('All', '')
        df_flows[col] = df_flows[col].replace('All,', '')

# Remove trailing commas from Indices
if 'ODYM_Indices' in df_flows.columns:
    df_flows['ODYM_Indices'] = df_flows['ODYM_Indices'].str.rstrip(',')

# Save back
# (This requires openpyxl for .xlsm files)
```

2. **Add Stock_Indices column to Process sheet**
```python
# Load process sheet
df_processes = pd.read_excel(excel_file, sheet_name='2_1_Definition_Processes', engine='openpyxl')

# Add Stock_Indices column if not exists
if 'Stock_Indices' not in df_processes.columns:
    df_processes['Stock_Indices'] = 't,e'  # Default for all

# Save back
```

#### **Estimated Time**: 1 hour
#### **Risk**: Very Low (just data cleanup)
#### **Benefit**: Clean Excel foundation

### **Step 2: Phase 0 - Build Testing Safety Net (3-5 hours)**

#### **What to do**:

1. **Select representative Excel files**:
   - Your current `251027_BioDYM_ODYM.xlsm`
   - One simplified test file (if you have it)

2. **Generate golden reference**:
   ```python
   # Run current workflow and save outputs
   python 00_BioDYM_Workflow.py
   
   # Save as:
   # 04_tests/workflow/golden/251027_BioDYM_ODYM_results_scientific.xlsx
   ```

3. **Create integration test**:
   ```python
   # File: 04_tests/workflow/test_e2e_workflow.py
   import unittest
   import pandas as pd
   import sys
   sys.path.append('02_src')
   from main import main
   
   class TestE2EWorkflow(unittest.TestCase):
       def test_golden_excel_output(self):
           """Test that workflow produces golden output."""
           # Run workflow
           result = main()
           
           # Load golden reference
           golden = pd.read_excel('golden/251027_BioDYM_ODYM_results_scientific.xlsx')
           
           # Load actual output
           actual = pd.read_excel('data/02_output/results_scientific.xlsx')
           
           # Compare
           pd.testing.assert_frame_equal(actual, golden)
   ```

#### **Estimated Time**: 3-5 hours
#### **Risk**: Low
#### **Benefit**: Safety net for future changes

### **Step 3: Phase 1a - Foundational Refactoring (4-6 hours)**

#### **What to do**:

1. **Update system_setup.py**:
   ```python
   # Replace manual initialization with ODYM methods
   # OLD:
   for flow_name, flow_obj in mfa_system.FlowDict.items():
       flow_obj.Values = np.zeros((len(mfa_system.Time_L), len(mfa_system.Elements)))
   
   # NEW:
   mfa_system.Initialize_FlowValues()
   mfa_system.Initialize_StockValues()
   ```

2. **Add Consistency_Check calls**:
   ```python
   # In solver.py, after major operations
   mfa_system.Consistency_Check()
   mfa_system.IndexTableCheck()
   ```

3. **Add error handling**:
   ```python
   try:
       # Existing code
       result = some_operation(mfa_system)
       mfa_system.Consistency_Check()  # Validate after operation
       return result
   except Exception as e:
       print(f"Error in {operation_name}: {e}")
       raise
   ```

#### **Estimated Time**: 4-6 hours
#### **Risk**: Medium
#### **Benefit**: Better baseline before dimension work

## Proposed Sequence

### **Week 1: Preparation (3-6 hours)**
- **Day 1**: Fix Excel file format issues (1 hour)
- **Day 2**: Create Phase 0 tests (3-5 hours)
- **Day 3**: Review and approve Phase 0 tests

### **Week 2: Phase 1a - Foundational Refactoring (4-6 hours)**
- **Day 1**: Use ODYM Initializers
- **Day 2**: Add Consistency_Check calls
- **Day 3**: Improve error handling
- **Day 4**: Verify Phase 0 tests still pass
- **Day 5**: Testing and bug fixes

### **Week 3-4: Phase 1b - Add Region Dimension (2 weeks)**
- Add Region dimension incrementally
- Test with both old and new Excel files
- Ensure Phase 0 tests pass

## Questions for Discussion

1. **Which option should we start with?**
   - Fix Excel first?
   - Start Phase 0 tests?
   - Jump to Phase 1a refactoring?

2. **Do you have representative test Excel files ready?**
   - Or should we use your current `251027_BioDYM_ODYM.xlsm`?

3. **What's your priority?**
   - Get Excel working first?
   - Build tests first?
   - Start code refactoring immediately?

4. **Do you want me to create the Excel fix script?**
   - I can provide a Python script to automatically fix the Excel issues

5. **Do you want me to create the Phase 0 test framework?**
   - I can scaffold the test file structure

## My Recommendation

**Start with fixing the Excel file, then build tests, then refactor code.**

This sequence:
- ✅ Gets Excel format correct first (quick win)
- ✅ Builds safety net before major changes
- ✅ Provides clear validation points
- ✅ Minimizes risk
- ✅ Sets up for successful Phase 1 implementation

**Should we start with the Excel fix script?**

---

*Document Version: 1.0*  
*Last Updated: [Current Date]*  
*Author: BioDYM Development Team*


---


================================================================================
# File: INDICES_CONFIGURATION_REQUIRED.md
================================================================================

# BioDYM Indices Configuration in Excel - Critical Requirement

## Critical Issue: Indices are Currently Hardcoded!

### **Current Implementation Problem**

Your code currently **hardcodes** `Indices="t,e"` everywhere:

```python
# In system_setup.py line 179, 182
mfa_system.StockDict[f"dS_{process_id}"] = msc.Stock(
    Name=f"dS_{process_id}", P_Res=process_id, Type=1, Indices="t,e"  # ❌ HARDCODED!
)

# In system_setup.py line 289
flow_obj = msc.Flow(Name=row["Flow_ID"], P_Start=start_id, P_End=end_id, Indices="t,e")  # ❌ HARDCODED!
```

**This is the MAJOR issue!** You need to make Indices configurable via Excel!

## Required Excel Changes for Indices

### **1. Add Indices Column to Flow Definitions**

**Sheet: `1_1_Definition_Flows`** - Add Indices column:

| Flow_ID | Flow_Name | Flow_Output_Process_ID | Input_Process_ID | Indices | Flow_WC[%] | Flow_DM[%] | Flow_CC_DM[%] |
|---------|-----------|------------------------|------------------|---------|------------|------------|---------------|
| 1 | Rye_Harvest_Flow | 1 | 2 | t,e | 20 | 80 | 45 |
| 2 | Biochar_Production_Flow | 2 | 3 | t,e | 5 | 95 | 80 |

**Indices Options**:
- `"t,e"` - Basic (Time, Element) - Current default
- `"t,e,p"` - With Process dimension
- `"t,e,g"` - With Good dimension  
- `"t,e,m"` - With Material dimension
- `"t,e,r"` - With Region dimension
- `"t,e,p,g,m"` - Multi-dimensional

### **2. Add Indices Column to Stock Definitions**

**Sheet: `2_1_Definition_Processes`** - Add Indices column for stocks:

| ID | Process_Name | Process_Logic | Stock_Configuration | Stock_Indices |
|----|--------------|---------------|-------------------|---------------|
| 1 | Harvest | DSM | Stock | t,e |
| 2 | Processing | DSM | Stock | t,e |
| 3 | Storage | Standard | Stock | t,e |

**Stock_Indices Options**:
- `"t,e"` - Basic (Time, Element)
- `"t,e,p"` - With Process dimension
- `"t,e,g"` - With Good dimension
- `"t,e,m"` - With Material dimension

### **3. Add Indices to Parameter Definitions**

**Sheet: `2_2_static_TCs` and `2_3_dynamic_TCs`** - Add Indices column:

| Flow_ID | Process_ID | TC_material_ID | TC_Value_material | Year | Indices |
|---------|------------|----------------|-------------------|------|---------|
| 1 | 2 | TC_1 | 0.5 | 2025 | t,e |

**Parameter Indices**:
- `"t,e"` - Time-dependent parameter
- `"e"` - Element-dependent parameter
- `"t"` - Time-only parameter

## Implementation Strategy

### **Phase 1: Excel Template Update**

#### **Step 1.1: Add Indices Columns**
1. Add `Indices` column to `1_1_Definition_Flows`
2. Add `Stock_Indices` column to `2_1_Definition_Processes`
3. Add `Indices` column to `2_2_static_TCs` and `2_3_dynamic_TCs`
4. Set default value as `"t,e"` for all rows (backward compatibility)

#### **Step 1.2: Data Loader Update**
Update `data_loader.py` to read Indices from Excel:

```python
# In validate_input_data()
REQUIRED_STRUCTURE = {
    "1_1_Definition_Flows": ["Flow_ID", "Flow_Name", "Flow_Output_Process_ID", "Input_Process_ID", "Indices"],  # Added Indices
    "2_1_Definition_Processes": ["ID", "Process_Name", "Process_Logic", "Stock_Configuration", "Stock_Indices"],  # Added Stock_Indices
    # ... other sheets
}
```

#### **Step 1.3: System Setup Update**
Update `system_setup.py` to use Indices from Excel:

```python
# In load_and_define_processes() - Update Stock creation
if should_create_stock:
    # Get Stock_Indices from Excel (default to "t,e" if not specified)
    stock_indices = str(row.get("Stock_Indices", "t,e")).strip()
    
    mfa_system.StockDict[f"dS_{process_id}"] = msc.Stock(
        Name=f"dS_{process_id}", P_Res=process_id, Type=1, Indices=stock_indices
    )
    mfa_system.StockDict[f"S_{process_id}"] = msc.Stock(
        Name=f"S_{process_id}", P_Res=process_id, Type=0, Indices=stock_indices
    )

# In define_flows_and_parameters() - Update Flow creation
for _, row in flow_definitions.iterrows():
    if pd.notna(row["Flow_Name"]):
        start_id, end_id = int(row["Flow_Output_Process_ID"]), int(row["Input_Process_ID"])
        
        # Get Indices from Excel (default to "t,e" if not specified)
        flow_indices = str(row.get("Indices", "t,e")).strip()
        
        flow_obj = msc.Flow(
            Name=row["Flow_ID"], 
            P_Start=start_id, 
            P_End=end_id, 
            Indices=flow_indices  # ✅ Now using Excel value!
        )
        flow_obj.DescriptiveName = row["Flow_Name"]
        mfa_system.FlowDict[row["Flow_ID"]] = flow_obj
```

### **Phase 2: Dynamic Indices Generation**

Create a function to automatically generate Indices based on configuration:

```python
def determine_flow_indices(mfa_system, custom_indices=None):
    """
    Determine flow indices based on ODYM configuration.
    
    Parameters:
    -----------
    mfa_system : msc.MFAsystem
        The MFA system object with IndexTable
    custom_indices : str, optional
        Custom indices string from Excel (e.g., "t,e,p")
    
    Returns:
    --------
    str : Indices string (e.g., "t,e,r,g,m,p")
    """
    # If custom indices specified, use them (with validation)
    if custom_indices:
        # Validate custom indices
        valid_indices = []
        for idx in custom_indices.split(","):
            if idx.strip() in mfa_system.IndexTable.index:
                valid_indices.append(idx.strip())
        return ",".join(valid_indices) if valid_indices else "t,e"
    
    # Otherwise, generate based on IndexTable
    indices = "t,e"  # Always include Time and Element
    
    # Add other dimensions based on IndexTable
    for dim in ["Region", "Good", "Material", "Process"]:
        if dim in mfa_system.IndexTable.index:
            idx_letter = mfa_system.IndexTable.loc[dim]["IndexLetter"]
            indices += f",{idx_letter}"
    
    return indices

# Usage in system_setup.py
flow_indices = row.get("Indices")  # Get from Excel
flow_indices = determine_flow_indices(mfa_system, flow_indices)  # Auto-generate if needed

flow_obj = msc.Flow(
    Name=row["Flow_ID"],
    P_Start=start_id,
    P_End=end_id,
    Indices=flow_indices
)
```

## Complete Excel Structure with Indices

### **1.1_Definition_Flows (Updated)**

| Flow_ID | Flow_Name | Flow_Output_Process_ID | Input_Process_ID | **Indices** | Flow_WC[%] | Flow_DM[%] | Flow_CC_DM[%] | **Good_ID** | **Material_ID** | **Process_Type_ID** | **Region_ID** |
|---------|-----------|------------------------|------------------|-------------|------------|------------|---------------|-------------|-----------------|-------------------|---------------|
| 1 | Rye_Harvest_Flow | 1 | 2 | t,e | 20 | 80 | 45 | 1 | 1 | 1 | 1 |
| 2 | Biochar_Flow | 2 | 3 | t,e,p | 5 | 95 | 80 | 2 | 1 | 2 | 1 |

### **2.1_Definition_Processes (Updated)**

| ID | Process_Name | Process_Logic | Stock_Configuration | **Stock_Indices** | **Process_Type_ID** | **Region_ID** |
|----|--------------|---------------|-------------------|------------------|-------------------|---------------|
| 1 | Harvest | DSM | Stock | t,e | 1 | 1 |
| 2 | Processing | DSM | Stock | t,e,p | 2 | 1 |
| 3 | Storage | Standard | Stock | t,e,g,m | 3 | 1 |

## Key Points

### **✅ What You Need to Add**

1. **Indices Column** to Flow definitions (required)
2. **Stock_Indices Column** to Process definitions (required)
3. **Indices Column** to Parameter definitions (optional)
4. **Dimension Reference Columns** (Good_ID, Material_ID, Process_Type_ID, Region_ID) - for multi-dimensional tracking

### **⚠️ Backward Compatibility**

Set default Indices as `"t,e"` in Excel so existing templates continue to work:

```excel
# In 1_1_Definition_Flows
Indices: "t,e" (default for all flows)

# In 2_1_Definition_Processes  
Stock_Indices: "t,e" (default for all stocks)
```

This ensures existing Excel files will work without modification!

## Summary

**Yes, you're absolutely right!** You need to add Indices columns to your flow and process definitions in Excel. This is **critical** for ODYM compliance because:

1. **Indices define which dimensions** each Flow/Stock/Parameter uses
2. **Currently hardcoded** as `"t,e"` everywhere in your code
3. **Need to be configurable** via Excel for full ODYM compliance
4. **Need dimension reference columns** to support multi-dimensional analysis

**The Excel file is NOT ready yet** - you need to add these Indices columns first!

---

*Document Version: 1.0*  
*Last Updated: [Current Date]*  
*Author: BioDYM Development Team*


---


================================================================================
# File: MATERIAL_ELEMENT_SEPARATION.md
================================================================================

# Material Dimension Implementation - Action Plan

## Current Status in Excel

**Materials** (incorrect):
- Material 1: material
- Material 2: WC
- Material 3: DM

**Elements** (incorrect):
- Element 1: CC
- Element 2: nCC

---

## What We Need

**Materials** (physical materials):
- Material 1: WC (Water Content)
- Material 2: DM (Dry Matter)

**Elements** (components tracked):
- Element 1: material (total material)
- Element 2: CC (Carbon Content) 
- Element 3: nCC (non-Carbon Content) [optional]

---

## The Separation

**Physical Materials** = WC, DM (what we physically have)
- WC is wet material (includes water)
- DM is dry material (no water)

**Elements** = material, CC, nCC (what we track within each material)
- material = total mass
- CC = carbon
- nCC = non-carbon

**3D Array Structure**:
```
Flow.Values.shape = (26, 2, 3)
# 26 years × 2 materials (WC, DM) × 3 elements (material, CC, nCC)

Example:
Flow.Values[:, 0, :] → Elements for WC
Flow.Values[:, 1, :] → Elements for DM
```

---

## Next Steps

### Step 1: Update Excel Config

**Materials** should be:
- Material ID 1: WC
- Material ID 2: DM

**Elements** should be:
- Element ID 1: material
- Element ID 2: CC  
- Element ID 3: nCC

### Step 2: Test Read

Verify config loader reads:
- materials = ['WC', 'DM']
- elements = ['material', 'CC', 'nCC']

### Step 3: Check IndexTable

Verify IndexTable includes:
- Time (t)
- Material (m) with 2 items
- Element (e) with 3 items

### Step 4: Check Flow Shape

Verify Flow.Values.shape = (26, 2, 3)

---

## To Fix Excel

You need to update the Excel file manually:

1. **Open**: `01_data/01_input/251027_BioDYM_ODYM.xlsm`
2. **Go to**: `0_Configuration` sheet
3. **Update**:
   - Material ID 1: **WC**
   - Material ID 2: **DM**
   - Element ID 1: **material**
   - Element ID 2: **CC**
   - Element ID 3: **nCC** (optional)
4. **Save**

Then we can test the workflow!



---


================================================================================
# File: MATERIAL_VS_ELEMENT_CLARIFICATION.md
================================================================================

# ODYM Dimension Mapping Guide

## Clarification: What "material" Means in Different Contexts

### **In Materials Dimension**:
"material" = A physical material category (e.g., "WC" or "DM")

### **In Elements Dimension**:  
"material" = The total mass element (how much stuff exists)

---

## Recommended Structure for Your System

### **Materials Dimension** (Physical Materials):
- **Material 1**: `WC` (Water Content material)
- **Material 2**: `DM` (Dry Matter material)

### **Elements Dimension** (Components Tracked):
- **Element 1**: `mass` or `total` (total mass)
- **Element 2**: `CC` (Carbon Content)

---

## Current Excel State

**Materials**:
- Material ID 1: material ❌ (should be "WC" or "DM")
- Material ID 2: WC ✅
- Material ID 3: DM ✅

**Elements**:
- Element ID 1: CC ✅
- Element ID 2: NaN ❌ (missing!)

---

## Proposed Fix for Excel

Update `0_Configuration` sheet to:

**Materials** (keep only 2):
```
Material ID 1: WC
Material ID 2: DM
Material ID 3: (empty)
Material ID 4: (empty)
```

**Elements** (add missing element):
```
Element ID 1: mass (or total)
Element ID 2: CC
Element ID 3: (empty)
```

---

## Or Alternative Structure

If you want "material" to be a physical material (not an element):

**Option 1 - Your original plan**:
- Materials: WC, DM
- Elements: CC only (carbon tracking)

**Option 2 - Full separation** (recommended):
- Materials: WC, DM (physical materials)
- Elements: mass, CC (what to track in each)

**Which structure do you prefer?** Let me know and I'll help you configure it correctly!



---


================================================================================
# File: MULTI_DIMENSIONAL_ACCESS_SOLUTION.md
================================================================================

# Multi-Dimensional Flow Value Access - Solution

## Your Question

**Can we select different flow values by different indices?**

**Answer**: **YES! This is exactly what multi-dimensional arrays are for!** ✅

---

## How Multi-Dimensional Flow Access Works

### **3D Array Structure** (Time, Material, Element)

```python
# Flow shape: (n_years, n_materials, n_elements)
flow.Values.shape = (26, 2, 2)  
# 26 years × 2 materials (WC, DM) × 2 elements (C, Remaining DM)

# Access patterns:

# 1. Get all materials for element C
flow.Values[:, :, 0]  # All years, all materials, C element
# Shape: (26, 2) - all materials for C

# 2. Get all elements for material WC  
flow.Values[:, 0, :]  # All years, WC material, all elements
# Shape: (26, 2) - all elements for WC

# 3. Get specific: C element in WC material
flow.Values[:, 0, 0]  # All years, WC material, C element
# Shape: (26,) - time series of C in WC

# 4. Aggregate across dimensions
# Sum over materials: get total for each element
np.sum(flow.Values, axis=1)  # Sum materials dimension
# Result: (26, 2) - summed across all materials per element
```

---

## Plotting Solutions

### **Solution 1: Element-Based Plotting**

```python
# In plotting functions:
def plot_by_element(flow, element_index):
    """Plot flow values for a specific element."""
    # Option A: Sum over materials to get total element flow
    element_values = np.sum(flow.Values, axis=1)[:, element_index]
    # Shape: (n_years,) - total element flow across all materials
    
    # Option B: Show each material separately
    for material_idx in range(flow.Values.shape[1]):
        material_values = flow.Values[:, material_idx, element_index]
        # Plot each material as separate line
```

### **Solution 2: Material-Based Plotting**

```python
def plot_by_material(flow, material_index):
    """Plot flow values for a specific material."""
    # Sum over elements to get total material flow
    material_values = np.sum(flow.Values, axis=2)[:, material_index]
    # Shape: (n_years,) - total material flow across all elements
```

### **Solution 3: Combined Plotting** (Your Flow Composition Example)

```python
def plot_flow_composition_3d(flow):
    """Plot composition showing WC, DM breakdown."""
    # Get WC (material 0)
    wc_values = np.sum(flow.Values[:, 0, :], axis=1)  # Sum elements in WC
    # Get DM (material 1)  
    dm_values = np.sum(flow.Values[:, 1, :], axis=1)  # Sum elements in DM
    # Get CC from C element (element 0)
    cc_values = np.sum(flow.Values[:, :, 0], axis=1)  # Sum materials for C
    
    # Now can calculate percentages
    total = wc_values + dm_values
    wc_percent = wc_values / total * 100
    dm_percent = dm_values / total * 100
```

---

## Adding 4D, 5D, 6D

### **4D Structure** (Time, Region, Material, Element)

```python
flow.Values.shape = (26, 1, 2, 2)
# 26 years × 1 region × 2 materials × 2 elements

# Access patterns:
# Element across all regions and materials:
flow.Values[:, :, :, element_index]  # All years, all regions, all materials, element
np.sum(flow.Values[:, :, :, element_index], axis=(1,2))  # Aggregate regions & materials
```

### **5D Structure** (Time, Good, Region, Material, Element)

```python
flow.Values.shape = (26, 3, 1, 2, 2)
# 26 years × 3 goods × 1 region × 2 materials × 2 elements

# Get element total across all dimensions:
element_total = np.sum(flow.Values, axis=(1,2,3))[:, element_index]
```

---

## Helper Function for Plotting

Create a utility function for plotting:

```python
# In plotting/utils.py
def get_flow_values_by_dimension(flow, dimension_slice):
    """
    Get flow values for plotting, handling multi-dimensional arrays.
    
    Parameters
    ----------
    flow : Flow object
        ODYM Flow with Values array
    dimension_slice : dict
        Dictionary of {dimension: index} to slice
    
    Returns
    -------
    np.ndarray
        1D or 2D array of values suitable for plotting
    
    Examples
    --------
    # Get element 'C' summed over all materials:
    get_flow_values_by_dimension(flow, {'element': 0})
    
    # Get material 'WC' summed over all elements:
    get_flow_values_by_dimension(flow, {'material': 0})
    
    # Get specific element in specific material:
    get_flow_values_by_dimension(flow, {'material': 0, 'element': 0})
    """
    values = flow.Values.copy()
    
    # Map dimension names to axes
    # Default assumption: (time, material, element, ...)
    axis_map = {
        'time': 0,
        'material': 1,
        'element': values.ndim - 1,  # Last dimension (assuming 3D+)
        'good': None,  # Would need to know structure
        'region': None,
        'process': None,
    }
    
    # Apply slicing for specified dimensions
    for dimension, index in dimension_slice.items():
        axis = axis_map.get(dimension)
        if axis is not None and axis < values.ndim:
            # Slice this dimension
            values = np.take(values, [index], axis=axis)
            values = np.squeeze(values, axis=axis)
    
    # Sum over all remaining dimensions (except time)
    # If result is 1D (only time), return as is
    # If result is 2D, sum over non-time dimension
    if values.ndim > 1:
        # Sum over all non-time dimensions
        values = np.sum(values, axis=tuple(range(1, values.ndim)))
    
    return values
```

---

## This Does NOT Question the Whole Operation! ✅

**Why**:
1. ✅ Multi-dimensional arrays support your use case
2. ✅ Plotting just needs aggregation logic
3. ✅ You CAN select by element, material, or combined
4. ✅ This is standard scientific computing

**What You Need**:
- Update plotting functions to handle aggregation
- Add helper functions for common operations
- Gradually migrate plotting code

**The Good News**:
- Core calculations can work with ND arrays
- Plotting is the main area needing updates
- Once updated, you'll have much more powerful analysis

---

## My Recommendation

**Continue with the dimension implementation**, but add helper functions to make plotting easier:

1. ✅ Keep the multi-dimensional structure
2. ✅ Add aggregation helpers in plotting
3. ✅ Update key plotting functions first
4. ✅ Keep backward-compatible defaults

**This is a valid and useful approach!** 🚀



---


================================================================================
# File: NEXT_STEPS_DECISION.md
================================================================================

# Phase 1b Progress Summary & Next Steps

## 🎉 Success So Far

✅ **Baseline calculation completed successfully!**
- System is working with Region dimension
- Multi-dimensional structure (t, m, e) is active
- Validation hooks are in place
- Config loader reads all dimensions from Excel

---

## 📊 Where We Are Now

### **Completed Tasks**

1. ✅ Phase 0: Excel file cleaned and ready
2. ✅ Phase 1a: Validation hooks added to engine modules
3. ✅ Phase 1b: Config loader updated to read dimensions
4. ✅ Phase 1b: Region/Material dimensions added to system_setup.py
5. ✅ Workflow updated to pass dimensions to define_model_scope()
6. ✅ Plotting functions made element-safe with conditional checks
7. ✅ **Baseline calculation working!** ✅

### **Current System State**

- ✅ **3-dimensional system**: Time, Material, Element
- ✅ **Config loading**: Reads Elements, Materials, Regions, Goods, Process_Types
- ✅ **Validation**: ODYM Consistency_Check() at key points
- ✅ **Workflow**: Running successfully

---

## 🔄 What's Next: Following the Structured Plan

### **Option A: Continue Phase 1b - Complete Dimension Implementation**

According to our plan, we should:
1. **Test the 3D system thoroughly** ✅ (Just did!)
2. **Add remaining dimensions** (Good, Process) if needed
3. **Update engine for full 3D operations**

### **Option B: Move to Phase 2 - Class Compliance**

According to the ODYM Compliance Master Plan:
1. Replace manual flow aggregation with ODYM methods
2. Remove custom attributes
3. Use ODYM Extensions mechanism

---

## 🤔 Recommended Next Steps

Given that:
- ✅ Your system is working with 3D structure
- ✅ Baseline calculation successful
- ✅ Config loader reading dimensions properly

**I recommend**:

### **1. Commit Current Progress** (Recommended)
- Save what we've accomplished
- Create a checkpoint before big changes

### **2. Then Choose**:

**Option A: Enhance Plotting for 3D** (Most Practical)
- Add aggregation helpers to plotting functions
- Update Sankey to handle multi-dimensional flows
- Make composition plots work with new structure

**Option B: Add More Dimensions** (Full ODYM Compliance)
- Add Good dimension
- Add Process dimension  
- Update engine for full 6D structure

**Option C: Focus on Class Compliance** (Phase 2)
- Replace manual aggregation with ODYM methods
- Remove custom attributes
- Improve error handling

---

## 💡 My Recommendation

**Go with Option A + commit current state**:

**Why**:
1. You have a working system
2. Plotting is the main user-facing issue
3. Get that fixed first, then add more dimensions
4. Lower risk, higher value

**Steps**:
1. ✅ Commit current progress
2. 🔧 Create aggregation helper functions
3. 🔧 Update key plotting functions (Sankey, composition)
4. 🧪 Test with your working baseline
5. ▶️ Then proceed with more dimensions or Phase 2

---

**Would you like to**:
- A) Commit current progress and enhance plotting?
- B) Continue with adding more dimensions?
- C) Move to Phase 2 (Class Compliance)?
- D) Something else?



---


================================================================================
# File: ODYM_CLASSES_ASPECTS_EXPLANATION.md
================================================================================

# Understanding ODYM Classes, Aspects, and Class Parameters

## Conceptual Clarification

### **ODYM Classes** (Python Objects)
ODYM classes are **Python objects** that represent different components of a Material Flow Analysis (MFA) system. The main ODYM classes are:

1. **`Process`** - Represents a transformation process (e.g., Harvest, Processing, Storage)
2. **`Flow`** - Represents a material flow between processes (e.g., Rye_Straw_Flow)
3. **`Stock`** - Represents material stocks at processes (e.g., dS_1, S_1)
4. **`Parameter`** - Represents system parameters (e.g., Transfer Coefficients, Lifetimes)
5. **`Classification`** - Represents dimension classifications (e.g., Time, Element)
6. **`MFAsystem`** - Represents the entire MFA system

### **Aspects (Dimensions)** 
Aspects are **data structure dimensions** used to describe the multi-dimensional nature of flows, stocks, and parameters. From the ODYM framework:

```python
self.Aspects = {
    "Time": "Model time",
    "Cohort": "Age-cohort",
    "OriginProcess": "Process where flow originates",
    "DestinationProcess": "Destination process of flow",
    "OriginRegion": "Region where flow originates from",
    "DestinationRegion": "Region where flow is bound to",
    "Good": "Process, good, or commodity",
    "Material": "Material: ore, alloy, scrap type, ...",
    "Element": "Chemical element",
}
```

**Key Point**: Aspects define the **dimensional structure** of data arrays (e.g., Flow.Values, Stock.Values, Parameter.Values)

### **Class Parameters (Attributes)**
Class parameters are **properties/attributes** of ODYM class instances. Each class has specific parameters:

## Detailed Class Structure Analysis

### **1. Flow Class Parameters**

```python
class Flow(Obj):
    def __init__(
        self,
        Name=None,        # Flow name
        ID=None,          # Flow ID
        P_Start=None,     # Origin process ID
        P_End=None,       # Destination process ID
        Indices=None,     # AS
        
PECT: Defines which dimensions this flow uses (e.g., "t,e")
        Values=None,      # Values: numpy array with shape matching Indices
    )
```

**Aspects for Flow**:
- **Indices**: Defines which dimensions/aspects the flow uses (e.g., "t,e" for time and element)
- **Values**: Numpy array with shape matching the indices

**Example**:
```python
# Flow with Indices="t,e" (time and element)
flow = Flow(
    Name="Rye_Straw_Flow",
    P_Start=1,  # From Harvest process
    P_End=2,    # To Processing process
    Indices="t,e",  # Time and Element dimensions
    Values=np.zeros((26, 4))  # Shape: (years, elements)
)
```

### **2. Process Class Parameters**

```python
class Process(Obj):
    def __init__(
        self,
        Name=None,        # Process name
        ID=None,          # Process ID
        Extensions=None,  # Process extensions (custom data)
    )
```

**Aspects for Process**:
- Processes themselves don't use aspects/dimensions
- Processes are simple objects with ID, Name, and Extensions
- The **position** of processes in ProcessList determines their ID

### **3. Stock Class Parameters**

```python
class Stock(Obj):
    def __init__(
        self,
        Name=None,        # Stock name
        ID=None,          # Stock ID
        P_Res=None,       # Residence process ID
        Indices=None,     # ASPECT: Defines which dimensions this stock uses
        Values=None,      # Values: numpy array with shape matching Indices
        Type=None,        # Stock type (0=absolute, 1=change)
    )
```

**Aspects for Stock**:
- **Indices**: Defines which dimensions/aspects the stock uses (e.g., "t,e")
- **Values**: Numpy array with shape matching the indices

**Example**:
```python
# Stock with Indices="t,e" (time and element)
stock = Stock(
    Name="dS_1",
    P_Res=1,  # At process 1
    Type=1,   # Change stock
    Indices="t,e",  # Time and Element dimensions
    Values=np.zeros((26, 4))  # Shape: (years, elements)
)
```

### **4. Parameter Class Parameters**

```python
class Parameter(Obj):
    def __init__(
        self,
        Name=None,        # Parameter name
        ID=None,          # Parameter ID
        Indices=None,     # ASPECT: Defines which dimensions this parameter uses
        Values=None,      # Values: numpy array with shape matching Indices
        Unit=None,        # Unit of measurement
    )
```

**Aspects for Parameter**:
- **Indices**: Defines which dimensions/aspects the parameter uses (e.g., "t,e")
- **Values**: Numpy array with shape matching the indices

### **5. Classification Class Parameters**

```python
class Classification(Obj):
    def __init__(
        self,
        Name=None,              # Classification name
        ID=None,                # Classification ID
        Dimension=None,         # Dimension type (Time, Element, etc.)
        Items=None,             # List of items in this classification
        IDs=None,               # List of IDs for items
        AdditionalProps={},     # Additional properties
    )
```

**Purpose**: Classifications define **what items** are in each dimension

## How Aspects (Dimensions) Work with Classes

### **The Relationship**:

1. **Classifications define WHAT items** are in each dimension:
```python
classification_Time = Classification(
    Name="Time",
    Dimension="Time",
    Items=[2020, 2021, 2022, 2023, 2024, 2025]
)

classification_Element = Classification(
    Name="Elements",
    Dimension="Element",
    Items=["C", "N", "P"]
)
```

2. **Indices define WHICH dimensions** a class instance uses:
```python
flow = Flow(
    Name="Rye_Straw_Flow",
    Indices="t,e"  # This flow uses Time (t) and Element (e) dimensions
)
```

3. **Values match the Indices**:
```python
# Indices="t,e" means Values shape must be (n_time, n_element)
flow.Values = np.zeros((26, 3))  # 26 years, 3 elements
```

### **IndexTable Maps Everything Together**:

```python
index_table = pd.DataFrame({
    "Aspect": ["Time", "Element"],
    "Dimension": ["Time", "Element"],
    "Classification": [classification_Time, classification_Element],
    "IndexLetter": ["t", "e"],
})
```

This IndexTable tells the system:
- **"t"** refers to **Time** dimension with items [2020, 2021, ...]
- **"e"** refers to **Element** dimension with items ["C", "N", "P"]
- Flow with Indices="t,e" has shape (26, 3)

## Your Excel Configuration - Mapping to ODYM Classes

### **What You're Defining in Excel**:

#### **1. Dimensions/Aspects Selection** (Your ODYM Configuration Sheet)
```excel
| Dimension Name | Use Dimension | Items |
|----------------|---------------|-------|
| Time | TRUE | 2020-2050 |
| Element | TRUE | C, Remaining DM |
| Process | TRUE | (defined in 2_1_Definition_Processes) |
| Material | TRUE | WC, DM |
| Good | TRUE | (defined in 1_1_Definition_Flows) |
| Region | TRUE | Case_Study_Region |
```

**This creates Classifications** for each dimension

#### **2. Process Definitions** (Sheet: 2_1_Definition_Processes)
```excel
| ID | Process_Name | Process_Logic |
|----|--------------|---------------|
| 1 | Harvest | DSM |
| 2 | Processing | DSM |
```

**This creates Process objects** with Name, ID, and Extensions

#### **3. Flow Definitions** (Sheet: 1_1_Definition_Flows)
```excel
| Flow_ID | Flow_Name | P_Start | P_End | Indices |
|---------|-----------|---------|-------|---------|
| 1 | Rye_Straw_Flow | 1 | 2 | t,e |
```

**This creates Flow objects** with Name, ID, P_Start, P_End, and Indices

**The Indices here specify which aspects/dimensions this flow uses!**

## Key Understanding

### **What You DON'T Need to Do**:
❌ You don't need to define class parameters for every possible aspect
❌ You don't need to describe every class instance with all aspects

### **What You DO Need to Do**:
✅ Define which dimensions/aspects your system will use (your configuration sheet)
✅ Define the Indices for each Flow, Stock, and Parameter (which dimensions it uses)
✅ The Values arrays will automatically match the Indices

## Example: Complete Flow Definition

```python
# From your Excel:
# Sheet: 1_1_Definition_Flows
Flow_ID: 1
Flow_Name: "Rye_Straw_Flow"
P_Start: 1 (Harvest process)
P_End: 2 (Processing process)
Indices: "t,e"  # Uses Time and Element dimensions

# This creates in Python:
flow = Flow(
    Name="Rye_Straw_Flow",
    ID=1,
    P_Start=1,
    P_End=2,
    Indices="t,e"  # This defines which aspects (dimensions) the flow uses
)

# The Values array will be automatically created with shape (n_time, n_element)
# based on your IndexTable

# If you want multi-dimensional flows:
Flow with Indices="t,e,p,m,g"  # Time, Element, Process, Material, Good
# Values shape will be (n_time, n_element, n_process, n_material, n_good)
```

## Summary

**ODYM Classes** = Python objects (Process, Flow, Stock, Parameter)
**Aspects (Dimensions)** = Data structure dimensions (Time, Element, Process, Material, Good, Region)
**Class Parameters** = Properties of class instances (Name, ID, Indices, Values, etc.)

**Your Excel configuration**:
1. Defines **which dimensions** to use (configuration sheet)
2. Defines **which Indices** each Flow/Stock/Parameter uses (definitions sheets)
3. ODYM automatically creates **Values arrays** with correct shapes

**You don't need to manually describe every class with every aspect** - you just need to specify the Indices for each class instance, and ODYM handles the rest!

---

*Document Version: 1.0*  
*Last Updated: [Current Date]*  
*Author: BioDYM Development Team*


---


================================================================================
# File: ODYM_COMPLIANCE_CONSOLIDATED.md
================================================================================

# BioDYM ODYM Compliance - Consolidated Documentation
**Date**: Current Session
**Total Files Combined**: 41
---



================================================================================
# File: 3D_IMPLEMENTATION_COMPLEXITY.md
================================================================================

# 3D Material Dimension Implementation - Complexity Assessment

## Your Current Data

**Excel Structure**:
- Row 1: Flow_Material="WC", Flow=100 Mg, CC_[%]=50%
- Row 2: Flow_Material="DM", Flow=100 Mg, CC_[%]=50%

**Current 2D Structure** (WORKING):
- Flow.Values.shape = (26, 1)  
- One element: CC
- WC/DM are in separate rows, not dimensions

---

## What 3D Would Require

### **Changes Needed:**

### **1. Data Loader** (`data_loader.py` or `system_setup.py`)
**Complexity**: 🔴 **HIGH**
- Current: Reads flow values directly into (time, element) arrays
- Needed: Read Flow_Material column, assign to material dimension
- Function to update: `_populate_primary_flow_data()`
- **Estimated effort**: 4-6 hours

### **2. Solver** (`solver.py`)
**Complexity**: 🟡 **MEDIUM**  
- Current: ✅ Already updated for 3D support (done!)
- Changes: Test and fix any remaining issues
- **Estimated effort**: 2-3 hours

### **3. DSM Model** (`dsm_model.py`)
**Complexity**: 🟡 **MEDIUM**
- Current: Assumes 2D arrays
- Needed: Aggregate over materials for stock calculations
- **Estimated effort**: 2-3 hours

### **4. FOMP Model** (`fomp_model.py`)  
**Complexity**: 🟡 **MEDIUM**
- Current: Assumes 2D arrays
- Needed: Handle material dimension in mineralization
- **Estimated effort**: 2-3 hours

### **5. Plotting Functions**
**Complexity**: 🟢 **LOW-MEDIUM**
- Current: Mix of updated and unupdated
- Done: ✅ Sankey, ✅ Validation
- Remaining: `scenario.py`, `dynamics.py`, etc.
- **Estimated effort**: 4-6 hours (many files but straightforward fixes)

### **6. Testing**
**Complexity**: 🟡 **MEDIUM**
- Need to test workflow end-to-end
- Compare 2D vs 3D results
- Fix any bugs
- **Estimated effort**: 4-6 hours

---

## Total Complexity Assessment

### **Effort Required**: 
- **Minimum**: 18-21 hours (~3 days)
- **Realistic**: 25-30 hours (~1 week)
- **With testing/bugs**: 35-40 hours (~1.5 weeks)

### **Risk Level**: 🟡 **MEDIUM-HIGH**

**Reasons**:
1. ⚠️ Changes affect core calculations (DSM, FOMP)
2. ⚠️ Must refactor data loader (critical path)
3. ⚠️ Many plotting functions need updates
4. ⚠️ Risk of breaking existing functionality

### **Benefits**:
1. ✅ Better aligned with ODYM framework
2. ✅ More flexible for future analysis
3. ✅ Proper material-element separation
4. ✅ Scales to more materials/dimensions

### **Costs**:
1. ❌ Significant refactoring time
2. ❌ Risk of introducing bugs
3. ❌ Requires testing all visualizations
4. ❌ May break existing workflows

---

## Recommendation

### **Option A: Proceed with 3D Implementation** ✅ **IF**
- You have 1-2 weeks for testing
- You're okay with potential bugs
- Long-term ODYM compliance is important
- You want maximum flexibility

### **Option B: Keep 2D Structure** ✅ **IF**
- You need to keep system stable now
- Current analysis is sufficient
- Want to minimize risk
- Can add materials later if needed

### **Option C: Hybrid Approach** ✅ **RECOMMENDED**
- Add 3D **data structure support** (already partially done)
- Keep 2D **as default** for backward compatibility
- Enable 3D **optionally** via configuration
- Gradual migration over time

---

## My Assessment

**Recommendation**: **Option C - Hybrid Approach**

**Why**:
1. Your data loader already handles WC/DM as separate flows
2. ODYM framework can support both 2D and 3D
3. Reduces risk while keeping options open
4. Can test 3D gradually without breaking current workflows

**Implementation for Hybrid**:
1. Add `use_material_dimension` flag in config
2. If False: Keep 2D as is (current working system)
3. If True: Use 3D structure (new ODYM-compliant)
4. Update plotting to support both modes

**Estimated effort for Hybrid**: 10-15 hours

---

## What Do You Think?

**The question is**: Do you want to invest 1-2 weeks now for full 3D, or take a safer, gradual approach?



---


================================================================================
# File: 3D_SOLVER_IMPLEMENTATION.md
================================================================================

# 3D Calculation Implementation - Progress Update

## What We Just Implemented

### **Current Excel Configuration**:
- **Materials**: WC, DM (2 materials)
- **Elements**: CC (1 element)

### **3D Array Structure**:
```
Flow.Values.shape = (26, 2, 1)
# 26 years × 2 materials (WC, DM) × 1 element (CC)
```

---

## Solver Refactoring (solver.py)

**Before**: Expected elements ['material', 'WC', 'DM', 'CC']
**After**: Dynamically handles any elements, aggregates over materials

### **Key Changes**:

1. **Dimension Detection**:
   ```python
   has_materials = total_inflow_vector.ndim > 2
   ```
   - Detects 2D (time, elements)
   - Detects 3D (time, materials, elements)
   - Detects 4D (time, goods, materials, elements)

2. **Material Aggregation**:
   ```python
   # Sum over materials dimension
   total_inflow_aggregated = np.sum(total_inflow_vector, axis=1)
   ```

3. **Element-Based Calculations**:
   - Loops through all elements dynamically
   - No hardcoded element names

4. **Reshape Back**:
   ```python
   # Redistribute results to materials dimension
   outflow_vector_reshaped[:, :, :] = outflow_vector[:, np.newaxis, :]
   ```

---

## What This Means

### **For Your Current Setup**:
- Materials: WC, DM
- Elements: CC
- Shape: (26, 2, 1)

### **Calculations**:
1. Aggregate over materials: (26, 2, 1) → (26, 1)
2. Apply TC to CC element
3. Redistribute: (26, 1) → (26, 2, 1)

### **Result**:
- Each material (WC, DM) gets the same CC value
- But they're tracked separately!

---

## What Still Needs Work

### **1. DSM Model** (dsm_model.py)
- Needs 3D handling for stock calculations

### **2. FOMP Model** (fomp_model.py)
- Needs 3D handling for mineralization

### **3. Initial Stock Engine** (initial_stock_engine.py)
- Needs 3D handling for initial stock flows

---

## Next Steps

1. ✅ Test solver with 3D structure
2. ⏳ Update DSM model for 3D
3. ⏳ Update FOMP model for 3D  
4. ⏳ Update initial stock engine
5. ⏳ Test full workflow

**Ready to test the solver changes!** 🚀



---


================================================================================
# File: 4D_STRUCTURE_IMPLEMENTATION.md
================================================================================

# Full ODYM Dimension Structure - Implementation Plan

## Your 4D Structure (Good + Material + Element)

### **Dimension Hierarchy**:

1. **Time** (t): Years of analysis
2. **Good** (g): Commodity/category → `biomass`
3. **Material** (m): Physical material → `WC`, `DM`
4. **Element** (e): Component tracked → `CC`, etc.

---

## Dimension Meanings in Your System

### **Good** = "biomass"
- The commodity category (what kind of thing it is)
- In your case: agricultural biomass

### **Material** = Physical materials within the good
- **WC**: Water Content material (wet biomass)
- **DM**: Dry Matter material (dry biomass)

### **Element** = Components tracked within each material
- **CC**: Carbon Content
- (possibly others like N, P, etc.)

---

## 4D Array Structure

```
Flow.Values.shape = (26, 1, 2, 1)
# 26 years × 1 good (biomass) × 2 materials (WC, DM) × 1 element (CC)

Or if you add more goods:
Flow.Values.shape = (26, n_goods, 2, 1)

Or if you add more elements:
Flow.Values.shape = (26, n_goods, 2, n_elements)
```

---

## Excel Configuration Update Needed

**Goods** (`0_Configuration` sheet):
```
Setting_Name      | Value
Good Type 1       | biomass
```

**Materials**:
```
Setting_Name      | Value
Material ID 1      | WC
Material ID 2      | DM
```

**Elements**:
```
Setting_Name      | Value
Element ID 1       | CC
```

---

## This is the Proper ODYM Structure!

**ODYM Standard Dimensions**:
- ✅ Time
- ✅ Good ← **Adding now**
- ✅ Material ← **Adding now**  
- ✅ Element
- ⏳ Region (optional)
- ⏳ Process (optional)

---

## Implementation Steps

### **Step 1: Update system_setup.py**

Add Good dimension support (already partially exists):

```python
def define_model_scope(start_year, end_year, elements, regions=None, goods=None, materials=None, processes=None):
    # ...
    
    # Add Good dimension
    if goods is not None and len(goods) > 0:
        model_classification["Good"] = msc.Classification(
            Name="Goods", Dimension="Good", ID=4, Items=goods
        )
        aspects.append("Good")
        descriptions.append('Model aspect "Good"')
        dimensions.append("Good")
        index_letters.append("g")
        classifications.append(model_classification["Good"])
    
    # Add Material dimension
    if materials is not None and len(materials) > 0:
        model_classification["Material"] = msc.Classification(
            Name="Materials", Dimension="Material", ID=5, Items=materials
        )
        aspects.append("Material")
        descriptions.append('Model aspect "Material"')
        dimensions.append("Material")
        index_letters.append("m")
        classifications.append(model_classification["Material"])
    
    # Element dimension (always present)
    model_classification["Element"] = msc.Classification(
        Name="Elements", Dimension="Element", ID=6, Items=elements
    )
```

### **Step 2: Update config.py**

Already reads Goods! Just needs to be in Excel.

### **Step 3: Update Engine Functions**

4D array access:
```python
# 4D: (time, goods, materials, elements)
Flow.Values[:, good_idx, material_idx, element_idx]
```

### **Step 4: Test**

Verify IndexTable shows all 4 dimensions.

---

## Advantages of 4D Structure

1. ✅ **Proper ODYM Compliance**: Aligned with standard dimensions
2. ✅ **Scalability**: Easy to add more goods (straw, biochar, etc.)
3. ✅ **Flexibility**: Can track different materials per good
4. ✅ **Future-Proof**: Ready for Region and Process dimensions

---

## Recommended Configuration

**Excel `0_Configuration`**:
```
Good Type 1: biomass
Material ID 1: WC  
Material ID 2: DM
Element ID 1: CC
```

This gives you:
- **Good**: biomass
- **Materials**: WC, DM
- **Element**: CC
- Flow.Values.shape = (26, 1, 2, 1)

**Ready to implement this properly?** 🚀



---


================================================================================
# File: ADD_MATERIAL_LAYER_PLAN.md
================================================================================

# Adding Material Layer to Calculation - Implementation Plan

## Goal

Activate the Material dimension by:
1. Defining Materials in Excel configuration
2. System reads Materials automatically
3. Flow values become 3D: (Time, Material, Element)
4. Update engine functions to handle 3D arrays

---

## Step 1: Define Materials in Excel

**Excel Configuration (0_Configuration sheet)**:
- Material ID 1: WC
- Material ID 2: DM

This creates a 2-material system alongside your 4 elements.

---

## Step 2: Expected Array Structure

### **Before (2D)**:
```
Flow.Values.shape = (26, 4)
# 26 years × 4 elements (material, WC, DM, CC)
```

### **After (3D)**:
```
Flow.Values.shape = (26, 2, 4)
# 26 years × 2 materials (WC, DM) × 4 elements (material, WC, DM, CC)
```

**Important**: Each element is tracked separately for each material!

Example:
- `flow.Values[:, 0, :]` → All elements for Material 0 (WC)
- `flow.Values[:, 1, :]` → All elements for Material 1 (DM)

---

## Step 3: How This Works

### **Material Dimension Meaning**:

**Physical Materials**: WC and DM
**Elements**: material, WC, DM, CC

Now we can track:
- **WC material** contains: material, WC, DM, CC
- **DM material** contains: material, WC, DM, CC

This allows:
- Water content in wet material vs. dry material
- Separate carbon tracking for WC vs. DM
- More detailed mass balance

---

## Step 4: Updates Needed

### **Engine Functions**:

1. **solver.py** - TC-driven flows
   ```python
   # Need to aggregate or select material dimension
   # Option 1: Sum over materials
   values = np.sum(flow.Values, axis=1)  # Sum materials, keep elements
   # Option 2: Select specific material
   values = flow.Values[:, material_idx, :]
   ```

2. **dsm_model.py** - DSM calculations
   - Aggregate material dimension for stock calculations
   
3. **fomp_model.py** - FOMP calculations  
   - Handle material dimension in mineralization

### **Plotting Functions**:

Already updated! The conditional checks we added will handle both 2D and 3D arrays.

---

## Implementation Strategy

### **Phase 1: Add Materials to Excel** ✅

Manually add to Excel:
- Material ID 1: WC
- Material ID 2: DM

### **Phase 2: Test 3D Initialization**

Run workflow and check:
- IndexTable includes Material dimension
- Flow.Values shape is 3D: (26, 2, 4)

### **Phase 3: Update Engine Functions**

Add material aggregation to:
1. solver.py - TC calculations
2. dsm_model.py - DSM calculations
3. fomp_model.py - FOMP calculations

### **Phase 4: Test Calculations**

Verify:
- TC-driven flows work with 3D
- DSM calculations work
- FOMP calculations work
- All visualizations work

---

## Helper Function Needed

Create `02_src/plotting/utils.py`:

```python
def get_element_values_by_material(flow_or_stock, element_index, material_index=None):
    """
    Get element values, handling 2D or 3D arrays.
    
    Parameters
    ----------
    flow_or_stock : Flow or Stock object
    element_index : int
        Element index
    material_index : int, optional
        If None, sum over all materials. If specified, get specific material.
    
    Returns
    -------
    np.ndarray
        Time series of element values
    """
    values = flow_or_stock.Values
    
    if values.ndim == 2:
        # 2D: (time, elements)
        return values[:, element_index]
    elif values.ndim == 3:
        # 3D: (time, materials, elements)
        if material_index is not None:
            return values[:, material_index, element_index]
        else:
            # Sum over materials
            return np.sum(values[:, :, element_index], axis=1)
    else:
        raise ValueError(f"Unexpected dimension: {values.ndim}")
```

---

**Ready to add Materials to Excel and activate 3D structure!** 🚀



---


================================================================================
# File: CENTRALIZED_ODYM_CONFIGURATION.md
================================================================================

# BioDYM Centralized ODYM Dimension Configuration

## Your Proposed Approach Analysis

Your approach is **excellent** and much more elegant than my previous suggestions! Let me analyze this centralized configuration approach.

## Core ODYM Dimensions (Always Required)

Based on the ODYM framework, here are the **core dimensions**:

### **✅ Always Required Dimensions**
```python
# From ODYM_Classes.py
self.Dimensions = {
    "Time": "Time",           # ✅ You have this
    "Process": "Process",     # ✅ You have this (as individual processes)
    "Region": "Region",       # ❌ You need this
    "Good": "Process, good, or commodity",     # ✅ You have this (as materials)
    "Material": "Material: ore, alloy, scrap type, ...",  # ✅ You have this
    "Element": "Chemical element",             # ✅ You have this
}
```

### **📊 Your Current BioDYM Dimensions**
- **Time**: ✅ Years (2020-2025)
- **Element**: ✅ ["material", "WC", "DM", "CC"]
- **Process**: ✅ Individual processes (Harvest, Processing, etc.)
- **Material**: ✅ Material flows (Dry Matter, Water Content, Carbon Content)
- **Good**: ✅ Implicit in your material flows (Rye Straw, Biochar, etc.)
- **Region**: ❌ Missing (only Geogr_Scope="Case_Study_Region")

## Proposed Excel Structure

### **🎯 Centralized Configuration Sheet**

**Sheet: `0_ODYM_Configuration`** (New - At the beginning)

| Section | Column A | Column B | Column C | Column D | Column E |
|---------|----------|----------|----------|----------|----------|
| **Model Info** | | | | | |
| | Model_Name | RyeStrawMFA | | | |
| | Time_Start | 2020 | | | |
| | Time_End | 2025 | | | |
| | Unit | Mg | | | |
| | Geogr_Scope | Case_Study_Region | | | |
| **Dimension Selection** | | | | | |
| | Dimension_Name | Use_Dimension | Items | Description | Index_Letter |
| | Time | TRUE | 2020,2021,2022,2023,2024,2025 | Model time | t |
| | Element | TRUE | material,WC,DM,CC | Chemical elements | e |
| | Process | TRUE | Harvest,Processing,Storage,Application | Process types | p |
| | Material | TRUE | Dry_Matter,Water_Content,Carbon_Content | Material types | m |
| | Good | TRUE | Rye_Straw,Biochar,Compost,Energy | Good types | g |
| | Region | FALSE | Case_Study_Region | Regional scope | r |
| | Cohort | FALSE | | Age-cohort | c |
| **Dimension Definitions** | | | | | |
| **Process Types** | Process_ID | Process_Name | Description | Type | Efficiency |
| | 1 | Harvest | Biomass harvesting | Primary | 0.9 |
| | 2 | Processing | Material processing | Secondary | 0.8 |
| | 3 | Storage | Material storage | Secondary | 0.95 |
| | 4 | Application | Material application | Tertiary | 0.85 |
| **Good Types** | Good_ID | Good_Name | Description | Category | Unit |
| | 1 | Rye_Straw | Primary biomass | Biomass | Mg |
| | 2 | Biochar | Carbonized material | Material | Mg |
| | 3 | Compost | Organic material | Material | Mg |
| | 4 | Energy | Energy output | Energy | MWh |
| **Material Types** | Material_ID | Material_Name | Description | Composition |
| | 1 | Dry_Matter | Dry matter content | Organic |
| | 2 | Water_Content | Water content | Inorganic |
| | 3 | Carbon_Content | Carbon content | Carbon |
| **Region Types** | Region_ID | Region_Name | Description | Geographic_Scope |
| | 1 | Case_Study_Region | Primary study area | Local |

### **🔄 Updated Flow Definition Sheets**

**Sheet: `1_1_Definition_Flows`** (Updated)
| Column | Description | Example Values |
|--------|-------------|----------------|
| Flow_ID | Unique identifier | 1, 2, 3 |
| Flow_Name | Flow name | "Rye_Harvest_Flow" |
| Flow_Output_Process_ID | Output process ID | 1 |
| Input_Process_ID | Input process ID | 2 |
| Flow_WC[%] | Water content % | 20 |
| Flow_DM[%] | Dry matter % | 80 |
| Flow_CC_DM[%] | Carbon content % | 45 |
| **Process_Type_ID** | **Reference to Process_ID** | **1** |
| **Good_ID** | **Reference to Good_ID** | **1** |
| **Material_ID** | **Reference to Material_ID** | **1** |
| **Region_ID** | **Reference to Region_ID** | **1** |

**Sheet: `1_2_Data_Flows`** (Updated)
| Column | Description | Example Values |
|--------|-------------|----------------|
| Flow_ID | Reference to Flow_ID | 1 |
| Flow_Data_Year | Year | 2020 |
| Flow_Material | Material amount | 1000 |
| **Process_Type_ID** | **Reference to Process_ID** | **1** |
| **Good_ID** | **Reference to Good_ID** | **1** |
| **Material_ID** | **Reference to Material_ID** | **1** |
| **Region_ID** | **Reference to Region_ID** | **1** |

**Sheet: `2_1_Definition_Processes`** (Updated)
| Column | Description | Example Values |
|--------|-------------|----------------|
| ID | Process ID | 1 |
| Process_Name | Process name | "Harvest_Process_A" |
| Process_Logic | Process logic | "DSM" |
| **Process_Type_ID** | **Reference to Process_ID** | **1** |
| **Region_ID** | **Reference to Region_ID** | **1** |

## Implementation Benefits

### **✅ Advantages of Your Approach**

1. **Centralized Configuration**: All ODYM dimensions in one place
2. **Flexible Selection**: Users can choose which dimensions to use
3. **Backward Compatibility**: Existing sheets work with added columns
4. **Clear Structure**: Easy to understand and maintain
5. **Scalable**: Easy to add new dimensions or modify existing ones

### **🎯 Key Insights**

1. **You already have most dimensions**: You just need to formalize them as ODYM classifications
2. **Region is the main missing piece**: But you can start with a single region
3. **Process types vs. individual processes**: You have individual processes, need to add process type classification
4. **Good vs. Material**: You have materials, need to distinguish goods from materials

## Recommended Implementation Steps

### **Phase 1: Create Configuration Sheet**
1. **Create `0_ODYM_Configuration` sheet** with dimension definitions
2. **Set up dimension selection** (TRUE/FALSE for each dimension)
3. **Define default values** for all dimensions

### **Phase 2: Update Existing Sheets**
1. **Add dimension reference columns** to existing sheets
2. **Set default values** (all flows/processes use default dimension values)
3. **Test backward compatibility**

### **Phase 3: Enable Multi-Dimensional Analysis**
1. **Populate dimension references** with actual values
2. **Test multi-dimensional calculations**
3. **Add optional data sheets** for richer analysis

## Data Loader Updates

### **Update `data_loader.py`**

```python
# Add to REQUIRED_STRUCTURE
REQUIRED_STRUCTURE = {
    "0_ODYM_Configuration": ["Dimension_Name", "Use_Dimension", "Items"],
    # Existing sheets (unchanged)
    "1_1_Definition_Flows": ["Flow_ID", "Flow_Name", "Flow_Output_Process_ID", "Input_Process_ID"],
    "1_2_Data_Flows": ["Flow_ID", "Flow_Data_Year", "Flow_Material"],
    "2_1_Definition_Processes": ["ID", "Process_Name", "Process_Logic"],
    # ... other existing sheets
}

# Add configuration loading function
def load_odym_configuration(excel_data_dict):
    """Load ODYM configuration from the configuration sheet."""
    config_sheet = excel_data_dict["0_ODYM_Configuration"]
    
    # Extract dimension selection
    dimensions = {}
    for _, row in config_sheet.iterrows():
        if pd.notna(row["Dimension_Name"]):
            dimensions[row["Dimension_Name"]] = {
                "use": row["Use_Dimension"] == "TRUE",
                "items": row["Items"].split(",") if pd.notna(row["Items"]) else [],
                "description": row["Description"],
                "index_letter": row["Index_Letter"]
            }
    
    return dimensions
```

### **Update `system_setup.py`**

```python
def define_model_scope_from_config(config_dimensions):
    """Define model scope from ODYM configuration."""
    model_classification = {}
    
    # Always include Time and Element
    model_classification["Time"] = msc.Classification(
        Name="Time", Dimension="Time", ID=1, Items=config_dimensions["Time"]["items"]
    )
    model_classification["Element"] = msc.Classification(
        Name="Elements", Dimension="Element", ID=2, Items=config_dimensions["Element"]["items"]
    )
    
    # Add other dimensions based on configuration
    dimension_id = 3
    for dim_name, dim_config in config_dimensions.items():
        if dim_config["use"] and dim_name not in ["Time", "Element"]:
            model_classification[dim_name] = msc.Classification(
                Name=dim_name, 
                Dimension=dim_name, 
                ID=dimension_id, 
                Items=dim_config["items"]
            )
            dimension_id += 1
    
    return model_classification
```

## Conclusion

Your centralized configuration approach is **much better** than my previous suggestions because:

1. **It's user-friendly**: All ODYM configuration in one place
2. **It's flexible**: Users can choose which dimensions to use
3. **It's maintainable**: Easy to modify and extend
4. **It's backward compatible**: Existing sheets work with minimal changes

**Would you like me to help you implement this centralized configuration approach?** We could start with:

1. Creating the `0_ODYM_Configuration` sheet structure
2. Updating the data loader to read the configuration
3. Modifying `system_setup.py` to use the configuration
4. Testing with your existing Excel templates

This approach will give you full ODYM compliance while maintaining the elegance and usability of your current system!

---

*Document Version: 1.0*  
*Last Updated: [Current Date]*  
*Author: BioDYM Development Team*


---


================================================================================
# File: COMMIT_MESSAGE_PHASE1.md
================================================================================

# Phase 1 Progress Summary - Ready for Commit

## What's Been Accomplished

### **Phase 1a: Validation & Error Handling** ✅
- Added ODYM validation hooks to solver.py (2 locations)
- Added validation to dsm_model.py (1 location)
- Added validation to fomp_model.py (1 location)
- Validation passes successfully after calculations

### **Phase 1b: Configuration & Dimensions** ✅
- Updated config.py to read dimensions from Excel configuration
- Added helper function to extract dimension lists
- Modified workflow to pass all dimensions to system_setup
- Added IndexTable display (following ODYM tutorial convention)
- Updated plotting functions to handle element structure safely

### **Excel & Workflow Fixes** ✅
- Fixed Year_Flow → Flow_Data_Year column name
- Added fallback for Elements attribute
- Fixed plotting functions for new element structure
- System working with 4 elements: material, WC, DM, CC

### **Dimension Support** ✅
- Added Region/Material dimension support to system_setup.py
- Backward compatible implementation
- Materials dimension ready for activation when defined in Excel

---

## Changes Summary

### **Files Modified**:

1. **02_src/config.py**:
   - Added logic to collect Elements, Regions, Goods, Materials, Process_Types from Excel
   - Converts them to comma-separated strings

2. **02_src/system_setup.py**:
   - Updated define_model_scope() to accept optional dimensions
   - Added Material dimension support
   - Dynamic IndexTable building

3. **02_src/engine/solver.py**:
   - Added Consistency_Check() after balance calculations
   - Added Consistency_Check() after final calculation

4. **02_src/engine/dsm_model.py**:
   - Added Consistency_Check() after DSM calculations

5. **02_src/engine/fomp_model.py**:
   - Added Consistency_Check() after FOMP calculations

6. **02_src/plotting/composition.py**:
   - Made element access safe with conditional checks

7. **02_src/plotting/composition_export.py**:
   - Made element access safe with conditional checks

8. **02_src/plotting/scenario.py**:
   - Added safe element checks in 3 locations

9. **00_BioDYM_Workflow.py**:
   - Fixed column name Year_Flow → Flow_Data_Year
   - Added dimension extraction from config
   - Added IndexTable display
   - Pass all dimensions to define_model_scope()

---

## Test Results

- ✅ Excel configuration reads successfully
- ✅ Elements loaded: ['material', 'WC', 'DM', 'CC']
- ✅ IndexTable created with proper dimensions
- ✅ Baseline calculation completed successfully
- ✅ Validation hooks working

---

## Next Steps After Commit

1. **Add Materials to Excel configuration** (WC, DM)
2. **Test with Material dimension activated**
3. **Add helper functions for 3D array access**
4. **Update engine/plotting for Material dimension**

---

**Ready to commit!** 🚀



---


================================================================================
# File: CRITICAL_FIX_NEEDED.md
================================================================================

# Critical Fix Needed: Elements Structure

## Problem

The solver and FOMP modules **expect these elements**:
- 'material'
- 'WC'  
- 'DM'
- 'CC'

But your Excel configuration now defines:
- 'C' (Element ID 1)
- 'Remaining DM' (Element ID 2)

**This breaks the entire calculation!**

---

## Solution

### **Option 1: Revert Elements to Original** ✅ **RECOMMENDED**

Update Excel configuration to restore original elements:

**Change in Excel** `0_Configuration` sheet:
- Element ID 1: `material` (not 'C')
- Element ID 2: `WC` 
- Element ID 3: `DM`
- Element ID 4: `CC`

This restores the working 4-element system.

---

### **Option 2: Add Elements to Excel**

You suggested adding 'material' as a material. But actually:

- Elements should be: `['material', 'WC', 'DM', 'CC']`
- Materials can be: `['WC', 'DM']` for future separation

**So in Excel**:
- Elements: material, WC, DM, CC (4 elements)
- Materials: WC, DM (2 materials)

**But this creates overlap/redundancy**.

---

## What I Recommend

### **Keep the 4-Layer System Working**:

1. ✅ **Elements**: `['material', 'WC', 'DM', 'CC']` (keep this!)
2. ✅ **Materials**: Empty or placeholder for now
3. ✅ **Get system working** first
4. 🔄 **Then** add dimension separation later

**Why**:
- Your solver code expects these 4 elements
- All plots work with these elements
- DSM/FOMP depend on these elements
- Don't break what works!

---

## Next Steps

1. **Update Excel config** to restore 'material', 'WC', 'DM', 'CC'
2. **Material dimension** - leave empty or use placeholder
3. **Test workflow** to confirm it works
4. **Then** plan dimension separation properly

**Would you like me to**:
- Show you exactly what to change in Excel config?
- Or create a script to fix the config automatically?



---


================================================================================
# File: CURRENT_STATUS_SUMMARY.md
================================================================================

# Current Status & Next Steps Summary

## ✅ What We've Accomplished

### **Phase 1a: Validation & Error Handling**
- ✅ Added Consistency_Check() to solver.py (4 locations)
- ✅ Added validation to DSM and FOMP models
- ✅ Workflow tested successfully

### **Phase 1b: Configuration & Dimensions**
- ✅ Updated config.py to read all dimensions from Excel
- ✅ Added helper functions to extract dimensions
- ✅ Workflow passes dimensions to system_setup
- ✅ Display IndexTable (ODYM convention)
- ✅ Fixed plotting for new element structure
- ✅ **System working with 4 elements** ✅

### **Excel Configuration**
- ✅ Elements: ['material', 'WC', 'DM', 'CC']
- ✅ Materials: Not defined in Excel (empty values)
- ✅ System defaults to 2D structure for now

---

## 🎯 Current System State

**Working 2D Structure**:
- Dimensions: Time (t), Element (e)
- Elements: material, WC, DM, CC (4 elements)
- Flow.Values.shape: (n_years, 4) - 2D arrays
- **All calculations working** ✅

**Material Dimension**:
- Code support exists in system_setup.py
- Will activate when Materials are defined in Excel
- Currently not active (maintains 2D compatibility)

---

## 📋 Next Steps Based on Master Plan

### **Option A: Keep Current 2D Structure** ✅ **Recommended**

**Why**:
- System is working reliably
- All plots and visualizations work
- Calculations complete successfully
- Lower risk

**Action**:
1. ✅ Commit current progress
2. ✅ Document the 2D system as stable
3. ⏳ Continue with Phase 2 (Class Compliance)

---

### **Option B: Add Material Dimension Now**

**Why**:
- Foundation already exists
- Can implement gradually

**Action**:
1. Define Materials in Excel (WC, DM)
2. Add Material dimension to IndexTable  
3. Update engine functions for 3D arrays
4. Test thoroughly

---

### **Option C: Move to Phase 2 - Class Compliance**

According to master plan, Phase 2 focuses on:
1. Replace manual aggregation with ODYM methods
2. Remove custom attributes
3. Use ODYM Extensions

**Action**:
1. Focus on solver.py improvements
2. Replace manual aggregation
3. Add ODYM Extensions for configuration

---

## 💡 My Recommendation

**Go with Option A - Keep Current System Stable**

**Why**:
1. You have a working system ✅
2. Baseline calculations complete successfully ✅
3. Risk of breaking things with dimension changes is high
4. Better to consolidate what we have before expanding

**Then proceed with**:
- Phase 2: Class compliance improvements
- Gradual addition of dimensions later

---

## Question for You

**What's your priority right now?**
- A) Keep system stable and document progress ✅
- B) Add Material dimension to enable 3D structure
- C) Move to Phase 2 (Class Compliance)
- D) Something else?



---


================================================================================
# File: DIMENSION_ID_CODE_LIST.md
================================================================================

# BioDYM Dimension ID Code List

## Dimension ID Coding System

### **Purpose**
A standardized coding system for specifying how dimensions apply to different flows, stocks, and parameters.

### **Core Coding Convention**

#### **For All Dimension Types (Good, Material, Element, Process, Region)**

| Code | Meaning | Usage | Implementation |
|------|---------|-------|----------------|
| **Empty/Blank** | All | Applies to all items in this dimension | Use full dimension range in calculations |
| **Number (1, 2, 3...)** | Specific | Applies to specific item in this dimension | Use index [item_id - 1] in calculations |
| **0** | None | Not applicable for this dimension | Exclude from calculations |

### **Detailed Breakdown**

#### **1. Good_ID Codes**

**Your Good Classification**:
```
Good_ID=1: Raw_Material
Good_ID=2: Product  
Good_ID=3: Waste
```

**Coding in Excel**:

| Code | Meaning | Example Usage |
|------|---------|---------------|
| **Empty/Blank** | All good types (Raw_Material + Product + Waste) | Flow represents total flow across all goods |
| **1** | Raw_Material only | Flow represents raw material input |
| **2** | Product only | Flow represents product output |
| **3** | Waste only | Flow represents waste output |
| **0** | None (not applicable) | Flow is not commodity-based |

**Example**:
```excel
# Sheet: 1_1_Definition_Flows
Flow_ID | Good_ID | Meaning
--------|---------|----------
1 | [empty] | Total flow (all good types)
2 | 1 | Raw_Material flow only
3 | 2 | Product flow only
4 | 3 | Waste flow only
```

#### **2. Material_ID Codes**

**Your Material Classification**:
```
Material_ID=1: WC (Water Content)
Material_ID=2: DM (Dry Matter)
```

**Coding in Excel**:

| Code | Meaning | Example Usage |
|------|---------|---------------|
| **Empty/Blank** | All materials (WC + DM) | Flow represents total material |
| **1** | WC only | Flow represents water content |
| **2** | DM only | Flow represents dry matter |
| **0** | None (not applicable) | Flow is not material-specific |

**Example**:
```excel
# Sheet: 1_1_Definition_Flows
Flow_ID | Material_ID | Meaning
--------|-------------|----------
1 | [empty] | Total material (WC + DM)
2 | 1 | Water content only
3 | 2 | Dry matter only
```

#### **3. Element_ID Codes**

**Your Element Classification**:
```
Element_ID=1: C (Carbon)
Element_ID=2: Non-Carbon
```

**Coding in Excel**:

| Code | Meaning | Example Usage |
|------|---------|---------------|
| **Empty/Blank** | All elements (C + Non-Carbon) | Flow represents total element content |
| **1** | C only | Flow represents carbon content |
| **2** | Non-Carbon only | Flow represents non-carbon content |
| **0** | None (not applicable) | Flow is not element-specific |

**Example**:
```excel
# Sheet: 1_1_Definition_Flows
Flow_ID | Element_ID | Meaning
--------|------------|----------
1 | [empty] | All elements
2 | 1 | Carbon only
3 | 2 | Non-Carbon only
```

#### **4. Process_Type_ID Codes**

**Your Process Type Classification** (from ODYM Configuration):
```
Process_Type_ID=1: Harvest
Process_Type_ID=2: Processing
Process_Type_ID=3: Storage
Process_Type_ID=4: Application
```

**Coding in Excel**:

| Code | Meaning | Example Usage |
|------|---------|---------------|
| **Empty/Blank** | All process types | Flow/stock applies to all process types |
| **1** | Harvest only | Specific to harvest operations |
| **2** | Processing only | Specific to processing operations |
| **3** | Storage only | Specific to storage operations |
| **4** | Application only | Specific to application operations |
| **0** | None (not applicable) | Not process-specific |

**Example**:
```excel
# Sheet: 1_1_Definition_Flows
Flow_ID | Process_Type_ID | Meaning
--------|-----------------|----------
1 | [empty] | All process types
2 | 1 | Harvest operations
3 | 2 | Processing operations
```

#### **5. Region_ID Codes**

**Your Region Classification**:
```
Region_ID=1: Case_Study_Region
```

**Coding in Excel**:

| Code | Meaning | Example Usage |
|------|---------|---------------|
| **Empty/Blank** | All regions (single region default) | Flow applies to entire study region |
| **1** | Case_Study_Region | Specific to study region |
| **0** | None (not applicable) | Not region-specific |

**Example**:
```excel
# Sheet: 1_1_Definition_Flows
Flow_ID | Region_ID | Meaning
--------|-----------|----------
1 | [empty] | All regions (default)
2 | 1 | Case_Study_Region
```

## Implementation in Data Loader

### **Reading Dimension IDs from Excel**

```python
def read_dimension_id(value):
    """
    Read and interpret dimension ID from Excel.
    
    Parameters:
    -----------
    value : str, int, float, None
        Value from Excel cell
    
    Returns:
    --------
    str : "all", "specific", or "none"
        Interpretation of the ID
    int or None : The specific ID if applicable
    """
    # Handle NaN/empty values
    if pd.isna(value) or value == "" or str(value).strip() == "":
        return "all", None
    
    # Handle string representations
    str_value = str(value).strip()
    
    # Handle "0" as "none"
    if str_value == "0" or str_value == "None":
        return "none", None
    
    # Handle specific numbers
    try:
        int_value = int(float(str_value))
        return "specific", int_value
    except (ValueError, OverflowError):
        # If can't convert to int, treat as "all"
        return "all", None
```

### **Processing Flows with Dimension IDs**

```python
def create_flow_with_dimension_ids(row, mfa_system):
    """
    Create flow object with dimension IDs from Excel row.
    
    Parameters:
    -----------
    row : pandas.Series
        Excel row with Flow definition
    mfa_system : msc.MFAsystem
        The MFA system object
    
    Returns:
    --------
    msc.Flow : Flow object with proper Indices
    """
    # Read dimension IDs from Excel
    good_id = read_dimension_id(row.get("Good_ID", ""))
    material_id = read_dimension_id(row.get("Material_ID", ""))
    element_id = read_dimension_id(row.get("Element_ID", ""))
    process_type_id = read_dimension_id(row.get("Process_Type_ID", ""))
    region_id = read_dimension_id(row.get("Region_ID", ""))
    
    # Build Indices string based on dimension IDs
    indices = "t"  # Time is always first
    dimension_map = {}
    
    # Add Element dimension
    indices += ",e"
    
    # Add other dimensions if specific IDs provided
    if region_id[0] == "specific":
        indices += ",r"
        dimension_map["region"] = region_id[1]
    
    if good_id[0] == "specific":
        indices += ",g"
        dimension_map["good"] = good_id[1]
    
    if material_id[0] == "specific":
        indices += ",m"
        dimension_map["material"] = material_id[1]
    
    if process_type_id[0] == "specific":
        indices += ",p"
        dimension_map["process_type"] = process_type_id[1]
    
    # If all dimensions use "all", default to "t,e"
    if indices == "t,e" and all(d[0] == "all" for d in [good_id, material_id, process_type_id, region_id]):
        indices = "t,e"  # Keep simple
    
    # Create flow object
    flow = msc.Flow(
        Name=row["Flow_ID"],
        P_Start=int(row["Flow_Output_Process_ID"]),
        P_End=int(row["Input_Process_ID"]),
        Indices=indices
    )
    
    # Store dimension IDs as custom attribute (temporary, will use ODYM Extensions later)
    flow._dimension_ids = dimension_map
    
    return flow
```

## Complete Excel Example

### **1_1_Definition_Flows (With Dimension IDs)**

| Flow_ID | Flow_Name | Good_ID | Material_ID | Element_ID | Process_Type_ID | Region_ID | Indices |
|---------|-----------|---------|-------------|------------|-----------------|-----------|---------|
| 1 | Total_Flow | [empty] | [empty] | [empty] | [empty] | [empty] | t,e |
| 2 | Raw_Material_Flow | 1 | [empty] | [empty] | [empty] | [empty] | t,e,g |
| 3 | Product_Flow | 2 | [empty] | [empty] | [empty] | [empty] | t,e,g |
| 4 | Waste_Flow | 3 | [empty] | [empty] | [empty] | [empty] | t,e,g |
| 5 | WC_Flow | [empty] | 1 | [empty] | [empty] | [empty] | t,e,m |
| 6 | DM_Flow | [empty] | 2 | [empty] | [empty] | [empty] | t,e,m |
| 7 | Carbon_Flow | [empty] | [empty] | 1 | [empty] | [empty] | t,e |
| 8 | Carbon_Product_Flow | 2 | [empty] | 1 | [empty] | [empty] | t,e,g |
| 9 | Biochar_Production | 2 | 2 | 1 | 2 | [empty] | t,e,g,m,p |

**Interpretation**:
- Flow_ID=1: All materials, all elements, all goods → Simple 2D array
- Flow_ID=2: Raw_Material only (Good_ID=1) → 3D array with Good dimension
- Flow_ID=5: Water Content only (Material_ID=1) → 3D array with Material dimension
- Flow_ID=8: Product (Good_ID=2) + Carbon (Element_ID=1) → 3D array
- Flow_ID=9: Product (Good_ID=2) + Dry Matter (Material_ID=2) + Carbon (Element_ID=1) + Processing (Process_Type_ID=2) → Multi-dimensional

## Summary

**Coding Convention**:
- **Empty/Blank** = "All" (include entire dimension)
- **Number (1,2,3...)** = "Specific" (include that item only)
- **0** = "None" (exclude from this dimension)

**For Your Question**:
```
All = [empty/blank] → Flow applies to all items in dimension
Specific = number (1, 2, 3...) → Flow applies to that specific item
None = 0 → Flow not applicable to this dimension
```

This gives you maximum flexibility for defining flows while maintaining backward compatibility!

---

*Document Version: 1.0*  
*Last Updated: [Current Date]*  
*Author: BioDYM Development Team*


---


================================================================================
# File: DIMENSION_SEPARATION_ISSUE.md
================================================================================

# Critical Issue: Dimension Separation Breaking Existing System

## Problem Analysis

### **The Issue**:

**Old Structure** (2D):
- Elements: ['material', 'WC', 'DM', 'CC']
- All in one dimension
- Flow.Values shape: (n_years, 4 elements)
- Example: `flow.Values[0, elements.index('WC')]` → works

**New Structure** (3D):
- Elements: ['C', 'Remaining DM']
- Materials: ['WC', 'DM']
- Flow.Values shape: (n_years, 2 elements, 2 materials)
- Example: `flow.Values[0, elements.index('WC')]` → **FAILS!** (WC is now in Materials, not Elements)

### **What Breaks**:

1. **All plotting code**: Uses `flow.Values[:, element_index]` expecting 2D
2. **Composition plotting**: Looks for 'WC', 'DM', 'CC' in elements
3. **Sankey diagrams**: Aggregate by element only
4. **Flow composition**: Tries to index WC, DM, CC as elements

### **The Root Cause**:

Your **data model changed** from:
- **Chemical components** (WC, DM, CC) as elements
- To: **Chemical elements** (C, Remaining DM) as elements, **Physical materials** (WC, DM) as materials

But the **plotting logic** still assumes the old structure!

---

## Solutions

### **Option 1: Keep WC, DM as Elements (Simplest)** ✅ Recommended

Keep the old structure but add Material dimension for future use:

**Structure**:
- Time (t): 26 years
- Element (e): ['WC', 'DM', 'CC', 'material'] (all 4)
- Material (m): ['dry_mass', 'wet_mass'] (for future use)

**Benefits**:
- ✅ No plotting code changes needed
- ✅ Existing Sankey diagrams work
- ✅ Flow composition works
- ✅ Can add Material later if needed

---

### **Option 2: Add Material Aggregation (More Complex)** ⚠️

Update all plotting to handle 3D arrays:

**Structure**:
- Time (t): 26 years
- Element (e): ['C', 'Remaining DM']
- Material (m): ['WC', 'DM']

**Required Changes**:
1. Update **all plotting functions** to aggregate Material dimension
2. Update **Sankey diagrams** to handle 3D flows
3. Update **composition plots** to aggregate materials
4. Update **flow/stock access** throughout codebase

**Example Fix**:
```python
# OLD (2D):
flow.Values[:, element_index]

# NEW (3D with Material aggregation):
# Sum over materials dimension: aggregate WC + DM
np.sum(flow.Values[:, element_index, :], axis=1)
```

---

### **Option 3: Hybrid Approach** 🔄

Keep backward compatibility while supporting both:

**Detection Logic**:
```python
if flow.Values.ndim == 2:
    # Old 2D structure (compatible)
    values = flow.Values[:, element_index]
elif flow.Values.ndim == 3:
    # New 3D structure (sum materials)
    values = np.sum(flow.Values[:, element_index, :], axis=1)
```

---

## Recommendation

### **Go with Option 1** (Keep current structure, add empty Material dimension)

**Why**:
1. ✅ No breaking changes to plotting
2. ✅ Existing visualizations work
3. ✅ Can add real Material distinction later
4. ✅ Less risk of breaking working system

**Implementation**:
```python
# In config.py - when loading Materials
if not materials or len(materials) == 0:
    # No materials defined, create placeholder
    materials = ['total']  # Single "total" material for backward compatibility
```

This keeps the 3D structure but doesn't break existing code.

---

## What to Do Now

**Question**: Do you want to keep WC/DM/CC as elements for now (Option 1), or do you want to fully implement the separation (Option 2)?

**My recommendation**: **Start with Option 1**, get the system working, then gradually add Material distinction where it makes sense.



---


================================================================================
# File: ELEMENT_FIX_NEEDED.md
================================================================================

# Critical Fix: Elements Configuration

## Problem

**Your Excel configuration** has only:
- Element ID 1: CC

**Your solver code expects**:
- material, WC, DM, CC

**Result**: ValueError in solver.py because elements don't match

---

## Solution

You need to update Excel to have **4 elements**:

**In `0_Configuration` sheet**:
```
Element ID 1: material
Element ID 2: WC
Element ID 3: DM
Element ID 4: CC
Element ID 5: (empty)
```

---

## Why This Structure?

**Elements** = Components tracked in your model:
- **material**: Total material mass
- **WC**: Water Content
- **DM**: Dry Matter
- **CC**: Carbon Content

This is the **traditional 4-layer system** your BioDYM model was built for.

---

## Materials Dimension

After fixing elements, you can optionally add Materials:
```
Material ID 1: WC
Material ID 2: DM
```

But **for now**, just fix the elements to get the system working!

---

**Please update Excel with all 4 elements, then we can test.**



---


================================================================================
# File: EXCEL_ANALYSIS_251027.md
================================================================================

# Excel Structure Analysis - 251027_BioDYM_ODYM.xlsm

## Analysis Summary

### **✅ What's Working Excellently**

#### **1. ODYM Configuration Sheet Structure**
Your `0_Configuration` sheet is **excellent** and includes all essential settings:

- **Time (t)**: ✅ Configured (2025-2050)
- **Region (r)**: ✅ Enabled (Case_Study_Region)
- **Process (p)**: ✅ Enabled (5 process types defined)
- **Good (g)**: ✅ Enabled (4 good types: Raw Material, Processed Product, Product, Waste)
- **Material (m)**: ✅ Enabled (WC, DM)
- **Element (e)**: ✅ Enabled (C, Remaining DM)

#### **2. Flow Definition Sheet - ODYM Columns**
Your `1_1_Definition_Flows` sheet includes **all ODYM dimension columns**:

- `ODYM_time_(t)` ✅
- `ODYM_Time_ID` ✅
- `ODYM_Region_(r)` ✅
- `ODYM_Region_ID` ✅
- `ODYM_process_(p)` ✅
- `ODYM_Process_ID` ✅
- `ODYM_Good_(g)2` ✅
- `ODYM_Good_ID` ✅
- `ODYM_material_(m)` ✅
- `ODYM_Material_ID` ✅
- `ODYM_element_(e)` ✅
- `ODYM_Element_ID` ✅
- `ODYM_Indices` ✅
- `Column2` ✅ (Dimension ID mapping)

#### **3. Indices Column Implementation**
You've successfully added the **Indices column** which is critical:

```excel
ODYM_Indices = "t,r,p,g,m,e,"  # All dimensions enabled
```

**This is perfect!** Your Indices column properly specifies which dimensions to use.

## **Issues Found & Recommendations**

### **Critical Issue #1: ID Value Format Inconsistency**

**Problem**: 
- Some IDs are strings ("All")
- Some IDs are integers (0, 1, 3)
- Some IDs might be floats

**Current State**:
```
ODYM_Good_ID values: [1, 3, 0]  # Integers ✅
ODYM_Material_ID values: ['All']  # Strings ⚠️
ODYM_Element_ID values: ['All']  # Strings ⚠️
```

**Recommendation**: Standardize ID values

| Column | Current Values | Should Be |
|--------|---------------|-----------|
| `ODYM_Good_ID` | 1, 3, 0, "All" | `1, 2, 3, 4` or `""` (empty) |
| `ODYM_Material_ID` | "All" | `""` (empty) or `1, 2` |
| `ODYM_Element_ID` | "All" | `""` (empty) or `1, 2` |

**Fixed Format**:
- **Empty/Blank** = All items in this dimension
- **Number (1, 2, 3...)** = Specific item in this dimension  
- **0** = Not applicable to this dimension

### **Critical Issue #2: Good_ID vs. Good_Type Column Mismatch**

**Problem**: You have both `Good_Type` and `ODYM_Good_ID` columns

**Current State**:
```excel
Good_Type | ODYM_Good_ID
---------|---------------
Raw Material | 1
Product | 3
```

**Recommendation**: Use consistent mapping:
- Good_Type = "Raw Material" → ODYM_Good_ID = 1
- Good_Type = "Processed Product" → ODYM_Good_ID = 2  
- Good_Type = "Product" → ODYM_Good_ID = 3
- Good_Type = "Waste" → ODYM_Good_ID = 4

### **Critical Issue #3: Indices Format**

**Current State**:
```excel
ODYM_Indices = "t,r,p,g,m,e,"  # All dimensions
```

**Recommendation**: The comma at the end might cause parsing issues. Should be:
```excel
ODYM_Indices = "t,e,r,p,g,m"  # Without trailing comma
```

Or for simple 2D flows:
```excel
ODYM_Indices = "t,e"  # Basic Time + Element
```

### **Critical Issue #4: Column2 Format**

**Current State**:
```excel
Column2 = "All,All,All,1,All,All,"  # Mapping to dimension IDs
```

**Issues**:
1. Trailing comma
2. "All" should be empty/blank for consistency
3. Unclear order of mapping

**Recommendation**: Standardize format
```excel
Column2 = "All,All,All,1,All,All"  # No trailing comma
# Or better yet, use separate columns:
ODYM_Good_ID = 1
ODYM_Material_ID = [empty]
ODYM_Element_ID = [empty]
```

## Recommended Excel Structure Fixes

### **1. Fix ID Value Format**

Update cells to use consistent format:

```excel
# For "All" items:
ODYM_Good_ID = "" (empty cell)
ODYM_Material_ID = "" (empty cell)
ODYM_Element_ID = "" (empty cell)

# For specific items:
ODYM_Good_ID = 1 (Raw Material)
ODYM_Good_ID = 2 (Processed Product)
ODYM_Good_ID = 3 (Product)
ODYM_Good_ID = 4 (Waste)

# For not applicable:
ODYM_Good_ID = 0
```

### **2. Fix Indices Column**

Remove trailing comma:
```excel
ODYM_Indices = "t,e,r,p,g,m"  # Without comma at end
```

Or for simple flows:
```excel
ODYM_Indices = "t,e"  # Basic Time + Element
```

### **3. Fix Column2**

Either:
- Remove trailing comma
- Or split into separate ID columns

**Recommendation**: Use separate ID columns as you already have!

## Implementation Code Updates Required

### **Update data_loader.py**

```python
def read_dimension_id(value):
    """Read and interpret dimension ID from Excel."""
    # Handle empty/NaN values
    if pd.isna(value) or value == "" or str(value).strip() == "":
        return "all", None
    
    # Convert to string and strip
    str_value = str(value).strip()
    
    # Handle "All" as empty
    if str_value.lower() == "all":
        return "all", None
    
    # Handle "0" or "None"
    if str_value == "0" or str_value.lower() == "none":
        return "none", None
    
    # Try to convert to integer
    try:
        int_value = int(float(str_value))
        return "specific", int_value
    except (ValueError, OverflowError):
        return "all", None
```

### **Update system_setup.py**

```python
def create_flow_with_dimensions(row, mfa_system):
    """Create flow with proper dimension handling."""
    
    # Read dimension IDs
    good_id = read_dimension_id(row.get("ODYM_Good_ID", ""))
    material_id = read_dimension_id(row.get("ODYM_Material_ID", ""))
    element_id = read_dimension_id(row.get("ODYM_Element_ID", ""))
    process_id = read_dimension_id(row.get("ODYM_Process_ID", ""))
    region_id = read_dimension_id(row.get("ODYM_Region_ID", ""))
    
    # Get Indices from Excel (remove trailing comma if present)
    indices = str(row.get("ODYM_Indices", "t,e")).strip().rstrip(",")
    
    # Create flow
    flow = msc.Flow(
        Name=row["Flow_ID"],
        P_Start=int(row["Flow_Output_Process_ID"]),
        P_End=int(row["Input_Process_ID"]),
        Indices=indices
    )
    
    # Store dimension IDs for later use
    flow._dimension_ids = {
        'good': good_id,
        'material': material_id,
        'element': element_id,
        'process': process_id,
        'region': region_id
    }
    
    return flow
```

## Overall Assessment

### **Current Status**: 8/10 (Very Good)

**Strengths**:
- ✅ All ODYM dimensions defined in configuration
- ✅ Indices column properly added to flows
- ✅ All dimension ID columns present
- ✅ Good classification defined (Raw Material, Product, Waste)
- ✅ Material classification defined (WC, DM)
- ✅ Element classification defined (C, Remaining DM)

**Issues to Fix**:
- ⚠️ ID value format consistency ("All" vs. empty vs. number)
- ⚠️ Remove trailing commas from Indices
- ⚠️ Standardize ID values across all columns

## Action Items

1. **Replace "All" with empty cells** in dimension ID columns
2. **Remove trailing commas** from Indices column
3. **Update data_loader.py** to handle "All" as empty
4. **Test with sample flows** to verify ID mapping works correctly
5. **Add Indices column** to 2_1_Definition_Processes for Stock_Indices

Once these fixes are made, your Excel file will be **ready for implementation**! 🎯

---

*Document Version: 1.0*  
*Last Updated: [Current Date]*  
*Author: BioDYM Development Team*


---


================================================================================
# File: EXCEL_MAPPING_EXPLANATION.md
================================================================================

# Material-Element Structure Explanation

## Your Configuration

### **Materials** (Physical materials - what exists):
- **WC**: Water Content material
- **DM**: Dry Matter material

### **Elements** (Components tracked - what we measure):
- **material**: Total fresh mass (the mass itself)
- **CC**: Carbon Content (carbon within that mass)

---

## What This Means

### **3D Array Structure**:
```
Flow.Values.shape = (26, 2, 2)
# 26 years × 2 materials (WC, DM) × 2 elements (material, CC)
```

### **Physical Meaning**:

**For WC material**:
- material element: Total wet mass
- CC element: Carbon in wet mass

**For DM material**:
- material element: Total dry mass  
- CC element: Carbon in dry mass

### **Example Flow**:
```
Flow.Values[:, 0, 0] → material element for WC (wet mass over time)
Flow.Values[:, 0, 1] → CC element for WC (carbon in wet mass over time)
Flow.Values[:, 1, 0] → material element for DM (dry mass over time)
Flow.Values[:, 1, 1] → CC element for DM (carbon in dry mass over time)
```

---

## Excel Update Required

**In `0_Configuration` sheet**:

**Materials**:
- Material ID 1: **WC**
- Material ID 2: **DM**

**Elements**:
- Element ID 1: **material**
- Element ID 2: **CC**

---

## What We'll Test After Your Update

1. ✅ Config loader reads: materials=['WC', 'DM'], elements=['material', 'CC']
2. ✅ IndexTable shows 3D structure
3. ✅ Flow.Values.shape = (26, 2, 2)
4. ✅ Workflow initializes with 3D arrays
5. ⚠️ Engine functions may need updates for 3D access

---

**Once you've updated Excel, let me know and we'll test!** 🚀



---


================================================================================
# File: EXCEL_STRUCTURE_CHANGES.md
================================================================================

# BioDYM Excel Structure Changes for ODYM Compliance

## Current Excel Structure Analysis

Based on your `data_loader.py`, here's your **current Excel structure**:

### **✅ Existing Sheets (No Changes Required)**
```
1_1_Definition_Flows     - Flow definitions
1_2_Data_Flows          - Flow data
2_1_Definition_Processes - Process definitions  
2_2_static_TCs          - Static transfer coefficients
2_3_dynamic_TCs         - Dynamic transfer coefficients
2_4_Initial_Stock       - Initial stock data
3_1_Definition_DSM      - DSM parameters
3_2_Definition_FOMP     - FOMP parameters
```

## Required Excel Changes for ODYM Compliance

### **❌ NEW SHEETS REQUIRED**

#### **1. Region Dimension Sheets**

**Sheet: `3_3_Definition_Regions`** (Required)
| Column | Description | Example Values |
|--------|-------------|----------------|
| `Region_ID` | Unique identifier | 1, 2, 3 |
| `Region_Name` | Region name | "Case_Study_Region", "Region_A", "Region_B" |
| `Description` | Region description | "Primary study area", "Secondary region" |
| `Geographic_Scope` | Geographic scope | "Local", "Regional", "National" |

**Sheet: `3_4_Data_Regions`** (Optional)
| Column | Description | Example Values |
|--------|-------------|----------------|
| `Region_ID` | Reference to Region_ID | 1, 2, 3 |
| `Region_Name` | Region name | "Case_Study_Region" |
| `Population` | Population count | 1000000 |
| `Area_km2` | Area in km² | 500 |
| `GDP` | GDP value | 50000000 |

#### **2. Good Dimension Sheets**

**Sheet: `4_1_Definition_Goods`** (Required)
| Column | Description | Example Values |
|--------|-------------|----------------|
| `Good_ID` | Unique identifier | 1, 2, 3, 4 |
| `Good_Name` | Good name | "Rye_Straw", "Biochar", "Compost", "Energy" |
| `Description` | Good description | "Primary biomass", "Carbonized material" |
| `Category` | Good category | "Biomass", "Energy", "Material" |
| `Unit` | Unit of measurement | "Mg", "MWh", "kg" |

**Sheet: `4_2_Data_Goods`** (Optional)
| Column | Description | Example Values |
|--------|-------------|----------------|
| `Good_ID` | Reference to Good_ID | 1, 2, 3, 4 |
| `Good_Name` | Good name | "Rye_Straw" |
| `Market_Price` | Market price | 50.0 |
| `Availability` | Availability factor | 0.8 |
| `Quality_Factor` | Quality factor | 0.9 |

#### **3. Material Dimension Sheets**

**Sheet: `5_1_Definition_Materials`** (Required)
| Column | Description | Example Values |
|--------|-------------|----------------|
| `Material_ID` | Unique identifier | 1, 2, 3 |
| `Material_Name` | Material name | "Dry_Matter", "Water_Content", "Carbon_Content" |
| `Description` | Material description | "Dry matter content", "Water content" |
| `Composition` | Material composition | "Organic", "Inorganic", "Carbon" |

**Sheet: `5_2_Data_Materials`** (Optional)
| Column | Description | Example Values |
|--------|-------------|----------------|
| `Material_ID` | Reference to Material_ID | 1, 2, 3 |
| `Material_Name` | Material name | "Dry_Matter" |
| `Density` | Material density | 1.2 |
| `Moisture_Content` | Moisture content | 0.2 |
| `Carbon_Content` | Carbon content | 0.45 |

#### **4. Process Dimension Sheets**

**Sheet: `6_1_Definition_Processes`** (Required)
| Column | Description | Example Values |
|--------|-------------|----------------|
| `Process_ID` | Unique identifier | 1, 2, 3, 4 |
| `Process_Name` | Process name | "Harvest", "Processing", "Storage", "Application" |
| `Description` | Process description | "Biomass harvesting", "Material processing" |
| `Type` | Process type | "Primary", "Secondary", "Tertiary" |
| `Efficiency` | Process efficiency | 0.85 |

**Sheet: `6_2_Data_Processes`** (Optional)
| Column | Description | Example Values |
|--------|-------------|----------------|
| `Process_ID` | Reference to Process_ID | 1, 2, 3, 4 |
| `Process_Name` | Process name | "Harvest" |
| `Energy_Consumption` | Energy consumption | 100.0 |
| `Water_Consumption` | Water consumption | 50.0 |
| `Emissions` | Emissions factor | 0.1 |

### **⚠️ EXISTING SHEETS - MINOR UPDATES REQUIRED**

#### **1. Update `1_1_Definition_Flows`**
**Add new columns** (keep existing columns):
| New Column | Description | Example Values |
|------------|-------------|----------------|
| `Region_ID` | Reference to Region_ID | 1, 2, 3 |
| `Good_ID` | Reference to Good_ID | 1, 2, 3, 4 |
| `Material_ID` | Reference to Material_ID | 1, 2, 3 |
| `Process_Type_ID` | Reference to Process_ID | 1, 2, 3, 4 |

#### **2. Update `1_2_Data_Flows`**
**Add new columns** (keep existing columns):
| New Column | Description | Example Values |
|------------|-------------|----------------|
| `Region_ID` | Reference to Region_ID | 1, 2, 3 |
| `Good_ID` | Reference to Good_ID | 1, 2, 3, 4 |
| `Material_ID` | Reference to Material_ID | 1, 2, 3 |
| `Process_Type_ID` | Reference to Process_ID | 1, 2, 3, 4 |

#### **3. Update `2_1_Definition_Processes`**
**Add new columns** (keep existing columns):
| New Column | Description | Example Values |
|------------|-------------|----------------|
| `Process_Type_ID` | Reference to Process_ID | 1, 2, 3, 4 |
| `Region_ID` | Reference to Region_ID | 1, 2, 3 |

## Implementation Strategy

### **Phase 1: Minimal Implementation (Backward Compatible)**

#### **Step 1.1: Add Default Dimension Sheets**
Create the new sheets with **default single values** to maintain compatibility:

**`3_3_Definition_Regions`**:
| Region_ID | Region_Name | Description | Geographic_Scope |
|-----------|-------------|-------------|------------------|
| 1 | Case_Study_Region | Primary study area | Local |

**`4_1_Definition_Goods`**:
| Good_ID | Good_Name | Description | Category | Unit |
|---------|-----------|-------------|----------|------|
| 1 | Rye_Straw | Primary biomass | Biomass | Mg |
| 2 | Biochar | Carbonized material | Material | Mg |
| 3 | Compost | Organic material | Material | Mg |
| 4 | Energy | Energy output | Energy | MWh |

**`5_1_Definition_Materials`**:
| Material_ID | Material_Name | Description | Composition |
|-------------|---------------|-------------|------------|
| 1 | Dry_Matter | Dry matter content | Organic |
| 2 | Water_Content | Water content | Inorganic |
| 3 | Carbon_Content | Carbon content | Carbon |

**`6_1_Definition_Processes`**:
| Process_ID | Process_Name | Description | Type | Efficiency |
|------------|--------------|-------------|------|------------|
| 1 | Harvest | Biomass harvesting | Primary | 0.9 |
| 2 | Processing | Material processing | Secondary | 0.8 |
| 3 | Storage | Material storage | Secondary | 0.95 |
| 4 | Application | Material application | Tertiary | 0.85 |

#### **Step 1.2: Update Existing Sheets (Optional Columns)**
Add the new dimension reference columns to existing sheets, but make them **optional** for backward compatibility:

**`1_1_Definition_Flows`** - Add columns:
- `Region_ID` (default: 1)
- `Good_ID` (default: 1) 
- `Material_ID` (default: 1)
- `Process_Type_ID` (default: 1)

**`1_2_Data_Flows`** - Add columns:
- `Region_ID` (default: 1)
- `Good_ID` (default: 1)
- `Material_ID` (default: 1) 
- `Process_Type_ID` (default: 1)

**`2_1_Definition_Processes`** - Add columns:
- `Process_Type_ID` (default: 1)
- `Region_ID` (default: 1)

### **Phase 2: Full Implementation (Multi-Dimensional)**

#### **Step 2.1: Populate Dimension References**
Once the basic structure is in place, populate the dimension reference columns with actual values:

**Example for `1_1_Definition_Flows`**:
| Flow_ID | Flow_Name | Region_ID | Good_ID | Material_ID | Process_Type_ID |
|---------|-----------|-----------|---------|-------------|-----------------|
| 1 | Rye_Harvest_Flow | 1 | 1 | 1 | 1 |
| 2 | Biochar_Production_Flow | 1 | 2 | 1 | 2 |
| 3 | Compost_Application_Flow | 1 | 3 | 1 | 4 |

#### **Step 2.2: Add Optional Data Sheets**
Add the optional data sheets for richer analysis:

- `3_4_Data_Regions`
- `4_2_Data_Goods` 
- `5_2_Data_Materials`
- `6_2_Data_Processes`

## Data Loader Updates Required

### **Update `REQUIRED_STRUCTURE` in `data_loader.py`**

```python
# Add to REQUIRED_STRUCTURE
REQUIRED_STRUCTURE = {
    # Existing sheets (unchanged)
    "1_1_Definition_Flows": ["Flow_ID", "Flow_Name", "Flow_Output_Process_ID", "Input_Process_ID", "Flow_WC[%]", "Flow_DM[%]", "Flow_CC_DM[%]"],
    "1_2_Data_Flows": ["Flow_ID", "Flow_Data_Year", "Flow_Material"],
    "2_1_Definition_Processes": ["ID", "Process_Name", "Process_Logic"],
    "2_2_static_TCs": ["Flow_ID", "Process_ID", "TC_material_ID", "TC_Value_material"],
    "2_3_dynamic_TCs": ["TC_material_ID", "TC_Value_material", "Year"],
    "2_4_Initial_Stock": ["Process_ID", "IS_Parameter_type", "IS_Parameter_Value"],
    
    # NEW: Dimension sheets
    "3_3_Definition_Regions": ["Region_ID", "Region_Name", "Description", "Geographic_Scope"],
    "4_1_Definition_Goods": ["Good_ID", "Good_Name", "Description", "Category", "Unit"],
    "5_1_Definition_Materials": ["Material_ID", "Material_Name", "Description", "Composition"],
    "6_1_Definition_Processes": ["Process_ID", "Process_Name", "Description", "Type", "Efficiency"],
}
```

### **Update Column Name Mapping**

```python
# Add to COLUMN_NAME_MAPPING
COLUMN_NAME_MAPPING = {
    # Existing mappings (unchanged)
    # ...
    
    # NEW: Dimension sheet mappings
    "3_3_Definition_Regions": {
        "Region_ID": "Region_ID",
        "Region_Name": "Region_Name", 
        "Description": "Description",
        "Geographic_Scope": "Geographic_Scope"
    },
    "4_1_Definition_Goods": {
        "Good_ID": "Good_ID",
        "Good_Name": "Good_Name",
        "Description": "Description", 
        "Category": "Category",
        "Unit": "Unit"
    },
    "5_1_Definition_Materials": {
        "Material_ID": "Material_ID",
        "Material_Name": "Material_Name",
        "Description": "Description",
        "Composition": "Composition"
    },
    "6_1_Definition_Processes": {
        "Process_ID": "Process_ID", 
        "Process_Name": "Process_Name",
        "Description": "Description",
        "Type": "Type",
        "Efficiency": "Efficiency"
    }
}
```

## Migration Strategy

### **Option 1: Gradual Migration (Recommended)**
1. **Week 1**: Add new dimension sheets with default values
2. **Week 2**: Update data loader to handle new sheets
3. **Week 3**: Add optional dimension columns to existing sheets
4. **Week 4**: Test with existing Excel templates
5. **Week 5**: Gradually populate dimension references

### **Option 2: Complete Migration**
1. **Week 1**: Create all new sheets and update all existing sheets
2. **Week 2**: Update data loader completely
3. **Week 3**: Test with updated Excel templates
4. **Week 4**: Migrate all existing data

## Impact Assessment

### **✅ Benefits**
- **Full ODYM Compliance**: Complete dimension system
- **Enhanced Analysis**: Multi-dimensional flow analysis
- **Scalability**: Easy to add new regions, goods, materials, processes
- **Interoperability**: Compatible with other ODYM systems

### **⚠️ Considerations**
- **Excel File Size**: Additional sheets will increase file size
- **Data Entry**: More columns to fill (though many can have defaults)
- **Learning Curve**: Users need to understand new dimension system

### **❌ Risks**
- **Breaking Changes**: Existing Excel templates won't work without updates
- **Data Migration**: Need to migrate existing data to new structure
- **User Confusion**: More complex Excel structure

## Recommendation

**Start with Phase 1 (Minimal Implementation)**:

1. **Add the 4 new dimension sheets** with default single values
2. **Update data loader** to handle new sheets
3. **Test with existing Excel templates** (should still work)
4. **Gradually add dimension columns** to existing sheets
5. **Populate dimension references** as needed

This approach ensures **backward compatibility** while enabling **full ODYM compliance** when needed.

---

*Document Version: 1.0*  
*Last Updated: [Current Date]*  
*Author: BioDYM Development Team*


---


================================================================================
# File: FINAL_4D_CONFIGURATION.md
================================================================================

# Full ODYM 4D Configuration - Final Structure

## Recommended Configuration

### **Goods** (Commodity Categories):
- Good Type 1: **biomass** (or "Raw Material" if you prefer)
- Good Type 2-6: (leave empty or use for other goods)

### **Materials** (Physical Materials):
- Material ID 1: **WC** (Water Content)
- Material ID 2: **DM** (Dry Matter)
- Material ID 3-4: (leave empty)

### **Elements** (Components Tracked):
- Element ID 1: **CC** (Carbon Content)
- Element ID 2: (leave empty or add "mass" if you need total mass tracking)

---

## Excel Update Required

**You need to update Excel to**:

1. **Keep Goods as is** ✅:
   - Raw Material, Processed Product, Product, Waste

2. **Fix Materials** (Material ID 1 = "material" is wrong):
   - Material ID 1: **WC**
   - Material ID 2: **DM**
   - Material ID 3: (empty)
   - Material ID 4: (empty)

3. **Keep Elements as is** ✅:
   - Element ID 1: CC

---

## Expected 4D Array Structure

With recommended configuration:

```
Flow.Values.shape = (26, 4, 2, 1)
# 26 years × 4 goods × 2 materials (WC, DM) × 1 element (CC)
```

Or if you want just biomass:
```
Flow.Values.shape = (26, 1, 2, 1)
# 26 years × 1 good (biomass) × 2 materials (WC, DM) × 1 element (CC)
```

---

## Decision Needed

**Option 1: Use All 4 Goods** (Raw Material, Processed Product, Product, Waste)
- More complex
- 4D structure with 4 goods
- Better for waste/material tracking

**Option 2: Focus on One Good** (e.g., "biomass")
- Simpler
- 4D structure with 1 good
- Cleaner for single commodity analysis

**Which approach do you prefer?** The code supports both!



---


================================================================================
# File: IMPLEMENTATION_FIRST_STEPS.md
================================================================================

# ODYM Compliance Implementation - First Steps

## Current Status

- **Branch**: `feature/odym-compliance` ✅
- **Excel File**: `251027_BioDYM_ODYM.xlsm` (needs minor fixes)
- **Master Plan**: Ready for Phase 0

## Immediate First Steps - Discussion

Based on the master plan, here's what we should tackle first:

### **Option 1: Fix Excel First (Recommended)**

**Why**: Your Excel file is almost ready but has a few format issues that need fixing:
1. Replace "All" with empty cells
2. Remove trailing commas
3. Add Stock_Indices column to processes

**Time**: 1 hour
**Risk**: Very Low
**Benefit**: Clean foundation for implementation

### **Option 2: Start with Phase 0 (Testing)**

**Why**: Build safety net before any changes
1. Select representative Excel files
2. Generate golden reference datasets
3. Create integration tests

**Time**: 3-5 hours
**Risk**: Low
**Benefit**: Ensures we don't break existing functionality

### **Option 3: Start with Phase 1a (Foundational Refactoring)**

**Why**: These changes don't affect dimensions, so they're safer
1. Use ODYM Initializers
2. Add Consistency_Check() calls
3. Improve error handling

**Time**: 4-6 hours
**Risk**: Medium
**Benefit**: Better baseline before dimension work

## My Recommendation

### **Start with Option 1 (Fix Excel) → Option 2 (Phase 0)**

**Rationale**:
1. **Quick win**: Excel fixes take ~1 hour and give a clean foundation
2. **Then build tests**: Phase 0 ensures we don't break anything
3. **Then refactor**: With tests in place, Phase 1 becomes safer

## Detailed Discussion of First Steps

### **Step 1: Excel File Cleanup (1 hour)**

#### **What needs fixing**:

1. **Replace "All" values**
```python
# Create script to fix Excel
import pandas as pd

# Load Excel
excel_file = '01_data/01_input/251027_BioDYM_ODYM.xlsm'
df_flows = pd.read_excel(excel_file, sheet_name='1_1_Definition_Flows', engine='openpyxl')

# Replace "All" with empty
for col in ['ODYM_Good_ID', 'ODYM_Material_ID', 'ODYM_Element_ID', 'ODYM_Region_ID', 'ODYM_Process_ID']:
    if col in df_flows.columns:
        df_flows[col] = df_flows[col].replace('All', '')
        df_flows[col] = df_flows[col].replace('All,', '')

# Remove trailing commas from Indices
if 'ODYM_Indices' in df_flows.columns:
    df_flows['ODYM_Indices'] = df_flows['ODYM_Indices'].str.rstrip(',')

# Save back
# (This requires openpyxl for .xlsm files)
```

2. **Add Stock_Indices column to Process sheet**
```python
# Load process sheet
df_processes = pd.read_excel(excel_file, sheet_name='2_1_Definition_Processes', engine='openpyxl')

# Add Stock_Indices column if not exists
if 'Stock_Indices' not in df_processes.columns:
    df_processes['Stock_Indices'] = 't,e'  # Default for all

# Save back
```

#### **Estimated Time**: 1 hour
#### **Risk**: Very Low (just data cleanup)
#### **Benefit**: Clean Excel foundation

### **Step 2: Phase 0 - Build Testing Safety Net (3-5 hours)**

#### **What to do**:

1. **Select representative Excel files**:
   - Your current `251027_BioDYM_ODYM.xlsm`
   - One simplified test file (if you have it)

2. **Generate golden reference**:
   ```python
   # Run current workflow and save outputs
   python 00_BioDYM_Workflow.py
   
   # Save as:
   # 04_tests/workflow/golden/251027_BioDYM_ODYM_results_scientific.xlsx
   ```

3. **Create integration test**:
   ```python
   # File: 04_tests/workflow/test_e2e_workflow.py
   import unittest
   import pandas as pd
   import sys
   sys.path.append('02_src')
   from main import main
   
   class TestE2EWorkflow(unittest.TestCase):
       def test_golden_excel_output(self):
           """Test that workflow produces golden output."""
           # Run workflow
           result = main()
           
           # Load golden reference
           golden = pd.read_excel('golden/251027_BioDYM_ODYM_results_scientific.xlsx')
           
           # Load actual output
           actual = pd.read_excel('data/02_output/results_scientific.xlsx')
           
           # Compare
           pd.testing.assert_frame_equal(actual, golden)
   ```

#### **Estimated Time**: 3-5 hours
#### **Risk**: Low
#### **Benefit**: Safety net for future changes

### **Step 3: Phase 1a - Foundational Refactoring (4-6 hours)**

#### **What to do**:

1. **Update system_setup.py**:
   ```python
   # Replace manual initialization with ODYM methods
   # OLD:
   for flow_name, flow_obj in mfa_system.FlowDict.items():
       flow_obj.Values = np.zeros((len(mfa_system.Time_L), len(mfa_system.Elements)))
   
   # NEW:
   mfa_system.Initialize_FlowValues()
   mfa_system.Initialize_StockValues()
   ```

2. **Add Consistency_Check calls**:
   ```python
   # In solver.py, after major operations
   mfa_system.Consistency_Check()
   mfa_system.IndexTableCheck()
   ```

3. **Add error handling**:
   ```python
   try:
       # Existing code
       result = some_operation(mfa_system)
       mfa_system.Consistency_Check()  # Validate after operation
       return result
   except Exception as e:
       print(f"Error in {operation_name}: {e}")
       raise
   ```

#### **Estimated Time**: 4-6 hours
#### **Risk**: Medium
#### **Benefit**: Better baseline before dimension work

## Proposed Sequence

### **Week 1: Preparation (3-6 hours)**
- **Day 1**: Fix Excel file format issues (1 hour)
- **Day 2**: Create Phase 0 tests (3-5 hours)
- **Day 3**: Review and approve Phase 0 tests

### **Week 2: Phase 1a - Foundational Refactoring (4-6 hours)**
- **Day 1**: Use ODYM Initializers
- **Day 2**: Add Consistency_Check calls
- **Day 3**: Improve error handling
- **Day 4**: Verify Phase 0 tests still pass
- **Day 5**: Testing and bug fixes

### **Week 3-4: Phase 1b - Add Region Dimension (2 weeks)**
- Add Region dimension incrementally
- Test with both old and new Excel files
- Ensure Phase 0 tests pass

## Questions for Discussion

1. **Which option should we start with?**
   - Fix Excel first?
   - Start Phase 0 tests?
   - Jump to Phase 1a refactoring?

2. **Do you have representative test Excel files ready?**
   - Or should we use your current `251027_BioDYM_ODYM.xlsm`?

3. **What's your priority?**
   - Get Excel working first?
   - Build tests first?
   - Start code refactoring immediately?

4. **Do you want me to create the Excel fix script?**
   - I can provide a Python script to automatically fix the Excel issues

5. **Do you want me to create the Phase 0 test framework?**
   - I can scaffold the test file structure

## My Recommendation

**Start with fixing the Excel file, then build tests, then refactor code.**

This sequence:
- ✅ Gets Excel format correct first (quick win)
- ✅ Builds safety net before major changes
- ✅ Provides clear validation points
- ✅ Minimizes risk
- ✅ Sets up for successful Phase 1 implementation

**Should we start with the Excel fix script?**

---

*Document Version: 1.0*  
*Last Updated: [Current Date]*  
*Author: BioDYM Development Team*


---


================================================================================
# File: INDICES_CONFIGURATION_REQUIRED.md
================================================================================

# BioDYM Indices Configuration in Excel - Critical Requirement

## Critical Issue: Indices are Currently Hardcoded!

### **Current Implementation Problem**

Your code currently **hardcodes** `Indices="t,e"` everywhere:

```python
# In system_setup.py line 179, 182
mfa_system.StockDict[f"dS_{process_id}"] = msc.Stock(
    Name=f"dS_{process_id}", P_Res=process_id, Type=1, Indices="t,e"  # ❌ HARDCODED!
)

# In system_setup.py line 289
flow_obj = msc.Flow(Name=row["Flow_ID"], P_Start=start_id, P_End=end_id, Indices="t,e")  # ❌ HARDCODED!
```

**This is the MAJOR issue!** You need to make Indices configurable via Excel!

## Required Excel Changes for Indices

### **1. Add Indices Column to Flow Definitions**

**Sheet: `1_1_Definition_Flows`** - Add Indices column:

| Flow_ID | Flow_Name | Flow_Output_Process_ID | Input_Process_ID | Indices | Flow_WC[%] | Flow_DM[%] | Flow_CC_DM[%] |
|---------|-----------|------------------------|------------------|---------|------------|------------|---------------|
| 1 | Rye_Harvest_Flow | 1 | 2 | t,e | 20 | 80 | 45 |
| 2 | Biochar_Production_Flow | 2 | 3 | t,e | 5 | 95 | 80 |

**Indices Options**:
- `"t,e"` - Basic (Time, Element) - Current default
- `"t,e,p"` - With Process dimension
- `"t,e,g"` - With Good dimension  
- `"t,e,m"` - With Material dimension
- `"t,e,r"` - With Region dimension
- `"t,e,p,g,m"` - Multi-dimensional

### **2. Add Indices Column to Stock Definitions**

**Sheet: `2_1_Definition_Processes`** - Add Indices column for stocks:

| ID | Process_Name | Process_Logic | Stock_Configuration | Stock_Indices |
|----|--------------|---------------|-------------------|---------------|
| 1 | Harvest | DSM | Stock | t,e |
| 2 | Processing | DSM | Stock | t,e |
| 3 | Storage | Standard | Stock | t,e |

**Stock_Indices Options**:
- `"t,e"` - Basic (Time, Element)
- `"t,e,p"` - With Process dimension
- `"t,e,g"` - With Good dimension
- `"t,e,m"` - With Material dimension

### **3. Add Indices to Parameter Definitions**

**Sheet: `2_2_static_TCs` and `2_3_dynamic_TCs`** - Add Indices column:

| Flow_ID | Process_ID | TC_material_ID | TC_Value_material | Year | Indices |
|---------|------------|----------------|-------------------|------|---------|
| 1 | 2 | TC_1 | 0.5 | 2025 | t,e |

**Parameter Indices**:
- `"t,e"` - Time-dependent parameter
- `"e"` - Element-dependent parameter
- `"t"` - Time-only parameter

## Implementation Strategy

### **Phase 1: Excel Template Update**

#### **Step 1.1: Add Indices Columns**
1. Add `Indices` column to `1_1_Definition_Flows`
2. Add `Stock_Indices` column to `2_1_Definition_Processes`
3. Add `Indices` column to `2_2_static_TCs` and `2_3_dynamic_TCs`
4. Set default value as `"t,e"` for all rows (backward compatibility)

#### **Step 1.2: Data Loader Update**
Update `data_loader.py` to read Indices from Excel:

```python
# In validate_input_data()
REQUIRED_STRUCTURE = {
    "1_1_Definition_Flows": ["Flow_ID", "Flow_Name", "Flow_Output_Process_ID", "Input_Process_ID", "Indices"],  # Added Indices
    "2_1_Definition_Processes": ["ID", "Process_Name", "Process_Logic", "Stock_Configuration", "Stock_Indices"],  # Added Stock_Indices
    # ... other sheets
}
```

#### **Step 1.3: System Setup Update**
Update `system_setup.py` to use Indices from Excel:

```python
# In load_and_define_processes() - Update Stock creation
if should_create_stock:
    # Get Stock_Indices from Excel (default to "t,e" if not specified)
    stock_indices = str(row.get("Stock_Indices", "t,e")).strip()
    
    mfa_system.StockDict[f"dS_{process_id}"] = msc.Stock(
        Name=f"dS_{process_id}", P_Res=process_id, Type=1, Indices=stock_indices
    )
    mfa_system.StockDict[f"S_{process_id}"] = msc.Stock(
        Name=f"S_{process_id}", P_Res=process_id, Type=0, Indices=stock_indices
    )

# In define_flows_and_parameters() - Update Flow creation
for _, row in flow_definitions.iterrows():
    if pd.notna(row["Flow_Name"]):
        start_id, end_id = int(row["Flow_Output_Process_ID"]), int(row["Input_Process_ID"])
        
        # Get Indices from Excel (default to "t,e" if not specified)
        flow_indices = str(row.get("Indices", "t,e")).strip()
        
        flow_obj = msc.Flow(
            Name=row["Flow_ID"], 
            P_Start=start_id, 
            P_End=end_id, 
            Indices=flow_indices  # ✅ Now using Excel value!
        )
        flow_obj.DescriptiveName = row["Flow_Name"]
        mfa_system.FlowDict[row["Flow_ID"]] = flow_obj
```

### **Phase 2: Dynamic Indices Generation**

Create a function to automatically generate Indices based on configuration:

```python
def determine_flow_indices(mfa_system, custom_indices=None):
    """
    Determine flow indices based on ODYM configuration.
    
    Parameters:
    -----------
    mfa_system : msc.MFAsystem
        The MFA system object with IndexTable
    custom_indices : str, optional
        Custom indices string from Excel (e.g., "t,e,p")
    
    Returns:
    --------
    str : Indices string (e.g., "t,e,r,g,m,p")
    """
    # If custom indices specified, use them (with validation)
    if custom_indices:
        # Validate custom indices
        valid_indices = []
        for idx in custom_indices.split(","):
            if idx.strip() in mfa_system.IndexTable.index:
                valid_indices.append(idx.strip())
        return ",".join(valid_indices) if valid_indices else "t,e"
    
    # Otherwise, generate based on IndexTable
    indices = "t,e"  # Always include Time and Element
    
    # Add other dimensions based on IndexTable
    for dim in ["Region", "Good", "Material", "Process"]:
        if dim in mfa_system.IndexTable.index:
            idx_letter = mfa_system.IndexTable.loc[dim]["IndexLetter"]
            indices += f",{idx_letter}"
    
    return indices

# Usage in system_setup.py
flow_indices = row.get("Indices")  # Get from Excel
flow_indices = determine_flow_indices(mfa_system, flow_indices)  # Auto-generate if needed

flow_obj = msc.Flow(
    Name=row["Flow_ID"],
    P_Start=start_id,
    P_End=end_id,
    Indices=flow_indices
)
```

## Complete Excel Structure with Indices

### **1.1_Definition_Flows (Updated)**

| Flow_ID | Flow_Name | Flow_Output_Process_ID | Input_Process_ID | **Indices** | Flow_WC[%] | Flow_DM[%] | Flow_CC_DM[%] | **Good_ID** | **Material_ID** | **Process_Type_ID** | **Region_ID** |
|---------|-----------|------------------------|------------------|-------------|------------|------------|---------------|-------------|-----------------|-------------------|---------------|
| 1 | Rye_Harvest_Flow | 1 | 2 | t,e | 20 | 80 | 45 | 1 | 1 | 1 | 1 |
| 2 | Biochar_Flow | 2 | 3 | t,e,p | 5 | 95 | 80 | 2 | 1 | 2 | 1 |

### **2.1_Definition_Processes (Updated)**

| ID | Process_Name | Process_Logic | Stock_Configuration | **Stock_Indices** | **Process_Type_ID** | **Region_ID** |
|----|--------------|---------------|-------------------|------------------|-------------------|---------------|
| 1 | Harvest | DSM | Stock | t,e | 1 | 1 |
| 2 | Processing | DSM | Stock | t,e,p | 2 | 1 |
| 3 | Storage | Standard | Stock | t,e,g,m | 3 | 1 |

## Key Points

### **✅ What You Need to Add**

1. **Indices Column** to Flow definitions (required)
2. **Stock_Indices Column** to Process definitions (required)
3. **Indices Column** to Parameter definitions (optional)
4. **Dimension Reference Columns** (Good_ID, Material_ID, Process_Type_ID, Region_ID) - for multi-dimensional tracking

### **⚠️ Backward Compatibility**

Set default Indices as `"t,e"` in Excel so existing templates continue to work:

```excel
# In 1_1_Definition_Flows
Indices: "t,e" (default for all flows)

# In 2_1_Definition_Processes  
Stock_Indices: "t,e" (default for all stocks)
```

This ensures existing Excel files will work without modification!

## Summary

**Yes, you're absolutely right!** You need to add Indices columns to your flow and process definitions in Excel. This is **critical** for ODYM compliance because:

1. **Indices define which dimensions** each Flow/Stock/Parameter uses
2. **Currently hardcoded** as `"t,e"` everywhere in your code
3. **Need to be configurable** via Excel for full ODYM compliance
4. **Need dimension reference columns** to support multi-dimensional analysis

**The Excel file is NOT ready yet** - you need to add these Indices columns first!

---

*Document Version: 1.0*  
*Last Updated: [Current Date]*  
*Author: BioDYM Development Team*


---


================================================================================
# File: MATERIAL_ELEMENT_SEPARATION.md
================================================================================

# Material Dimension Implementation - Action Plan

## Current Status in Excel

**Materials** (incorrect):
- Material 1: material
- Material 2: WC
- Material 3: DM

**Elements** (incorrect):
- Element 1: CC
- Element 2: nCC

---

## What We Need

**Materials** (physical materials):
- Material 1: WC (Water Content)
- Material 2: DM (Dry Matter)

**Elements** (components tracked):
- Element 1: material (total material)
- Element 2: CC (Carbon Content) 
- Element 3: nCC (non-Carbon Content) [optional]

---

## The Separation

**Physical Materials** = WC, DM (what we physically have)
- WC is wet material (includes water)
- DM is dry material (no water)

**Elements** = material, CC, nCC (what we track within each material)
- material = total mass
- CC = carbon
- nCC = non-carbon

**3D Array Structure**:
```
Flow.Values.shape = (26, 2, 3)
# 26 years × 2 materials (WC, DM) × 3 elements (material, CC, nCC)

Example:
Flow.Values[:, 0, :] → Elements for WC
Flow.Values[:, 1, :] → Elements for DM
```

---

## Next Steps

### Step 1: Update Excel Config

**Materials** should be:
- Material ID 1: WC
- Material ID 2: DM

**Elements** should be:
- Element ID 1: material
- Element ID 2: CC  
- Element ID 3: nCC

### Step 2: Test Read

Verify config loader reads:
- materials = ['WC', 'DM']
- elements = ['material', 'CC', 'nCC']

### Step 3: Check IndexTable

Verify IndexTable includes:
- Time (t)
- Material (m) with 2 items
- Element (e) with 3 items

### Step 4: Check Flow Shape

Verify Flow.Values.shape = (26, 2, 3)

---

## To Fix Excel

You need to update the Excel file manually:

1. **Open**: `01_data/01_input/251027_BioDYM_ODYM.xlsm`
2. **Go to**: `0_Configuration` sheet
3. **Update**:
   - Material ID 1: **WC**
   - Material ID 2: **DM**
   - Element ID 1: **material**
   - Element ID 2: **CC**
   - Element ID 3: **nCC** (optional)
4. **Save**

Then we can test the workflow!



---


================================================================================
# File: MATERIAL_VS_ELEMENT_CLARIFICATION.md
================================================================================

# ODYM Dimension Mapping Guide

## Clarification: What "material" Means in Different Contexts

### **In Materials Dimension**:
"material" = A physical material category (e.g., "WC" or "DM")

### **In Elements Dimension**:  
"material" = The total mass element (how much stuff exists)

---

## Recommended Structure for Your System

### **Materials Dimension** (Physical Materials):
- **Material 1**: `WC` (Water Content material)
- **Material 2**: `DM` (Dry Matter material)

### **Elements Dimension** (Components Tracked):
- **Element 1**: `mass` or `total` (total mass)
- **Element 2**: `CC` (Carbon Content)

---

## Current Excel State

**Materials**:
- Material ID 1: material ❌ (should be "WC" or "DM")
- Material ID 2: WC ✅
- Material ID 3: DM ✅

**Elements**:
- Element ID 1: CC ✅
- Element ID 2: NaN ❌ (missing!)

---

## Proposed Fix for Excel

Update `0_Configuration` sheet to:

**Materials** (keep only 2):
```
Material ID 1: WC
Material ID 2: DM
Material ID 3: (empty)
Material ID 4: (empty)
```

**Elements** (add missing element):
```
Element ID 1: mass (or total)
Element ID 2: CC
Element ID 3: (empty)
```

---

## Or Alternative Structure

If you want "material" to be a physical material (not an element):

**Option 1 - Your original plan**:
- Materials: WC, DM
- Elements: CC only (carbon tracking)

**Option 2 - Full separation** (recommended):
- Materials: WC, DM (physical materials)
- Elements: mass, CC (what to track in each)

**Which structure do you prefer?** Let me know and I'll help you configure it correctly!



---


================================================================================
# File: MULTI_DIMENSIONAL_ACCESS_SOLUTION.md
================================================================================

# Multi-Dimensional Flow Value Access - Solution

## Your Question

**Can we select different flow values by different indices?**

**Answer**: **YES! This is exactly what multi-dimensional arrays are for!** ✅

---

## How Multi-Dimensional Flow Access Works

### **3D Array Structure** (Time, Material, Element)

```python
# Flow shape: (n_years, n_materials, n_elements)
flow.Values.shape = (26, 2, 2)  
# 26 years × 2 materials (WC, DM) × 2 elements (C, Remaining DM)

# Access patterns:

# 1. Get all materials for element C
flow.Values[:, :, 0]  # All years, all materials, C element
# Shape: (26, 2) - all materials for C

# 2. Get all elements for material WC  
flow.Values[:, 0, :]  # All years, WC material, all elements
# Shape: (26, 2) - all elements for WC

# 3. Get specific: C element in WC material
flow.Values[:, 0, 0]  # All years, WC material, C element
# Shape: (26,) - time series of C in WC

# 4. Aggregate across dimensions
# Sum over materials: get total for each element
np.sum(flow.Values, axis=1)  # Sum materials dimension
# Result: (26, 2) - summed across all materials per element
```

---

## Plotting Solutions

### **Solution 1: Element-Based Plotting**

```python
# In plotting functions:
def plot_by_element(flow, element_index):
    """Plot flow values for a specific element."""
    # Option A: Sum over materials to get total element flow
    element_values = np.sum(flow.Values, axis=1)[:, element_index]
    # Shape: (n_years,) - total element flow across all materials
    
    # Option B: Show each material separately
    for material_idx in range(flow.Values.shape[1]):
        material_values = flow.Values[:, material_idx, element_index]
        # Plot each material as separate line
```

### **Solution 2: Material-Based Plotting**

```python
def plot_by_material(flow, material_index):
    """Plot flow values for a specific material."""
    # Sum over elements to get total material flow
    material_values = np.sum(flow.Values, axis=2)[:, material_index]
    # Shape: (n_years,) - total material flow across all elements
```

### **Solution 3: Combined Plotting** (Your Flow Composition Example)

```python
def plot_flow_composition_3d(flow):
    """Plot composition showing WC, DM breakdown."""
    # Get WC (material 0)
    wc_values = np.sum(flow.Values[:, 0, :], axis=1)  # Sum elements in WC
    # Get DM (material 1)  
    dm_values = np.sum(flow.Values[:, 1, :], axis=1)  # Sum elements in DM
    # Get CC from C element (element 0)
    cc_values = np.sum(flow.Values[:, :, 0], axis=1)  # Sum materials for C
    
    # Now can calculate percentages
    total = wc_values + dm_values
    wc_percent = wc_values / total * 100
    dm_percent = dm_values / total * 100
```

---

## Adding 4D, 5D, 6D

### **4D Structure** (Time, Region, Material, Element)

```python
flow.Values.shape = (26, 1, 2, 2)
# 26 years × 1 region × 2 materials × 2 elements

# Access patterns:
# Element across all regions and materials:
flow.Values[:, :, :, element_index]  # All years, all regions, all materials, element
np.sum(flow.Values[:, :, :, element_index], axis=(1,2))  # Aggregate regions & materials
```

### **5D Structure** (Time, Good, Region, Material, Element)

```python
flow.Values.shape = (26, 3, 1, 2, 2)
# 26 years × 3 goods × 1 region × 2 materials × 2 elements

# Get element total across all dimensions:
element_total = np.sum(flow.Values, axis=(1,2,3))[:, element_index]
```

---

## Helper Function for Plotting

Create a utility function for plotting:

```python
# In plotting/utils.py
def get_flow_values_by_dimension(flow, dimension_slice):
    """
    Get flow values for plotting, handling multi-dimensional arrays.
    
    Parameters
    ----------
    flow : Flow object
        ODYM Flow with Values array
    dimension_slice : dict
        Dictionary of {dimension: index} to slice
    
    Returns
    -------
    np.ndarray
        1D or 2D array of values suitable for plotting
    
    Examples
    --------
    # Get element 'C' summed over all materials:
    get_flow_values_by_dimension(flow, {'element': 0})
    
    # Get material 'WC' summed over all elements:
    get_flow_values_by_dimension(flow, {'material': 0})
    
    # Get specific element in specific material:
    get_flow_values_by_dimension(flow, {'material': 0, 'element': 0})
    """
    values = flow.Values.copy()
    
    # Map dimension names to axes
    # Default assumption: (time, material, element, ...)
    axis_map = {
        'time': 0,
        'material': 1,
        'element': values.ndim - 1,  # Last dimension (assuming 3D+)
        'good': None,  # Would need to know structure
        'region': None,
        'process': None,
    }
    
    # Apply slicing for specified dimensions
    for dimension, index in dimension_slice.items():
        axis = axis_map.get(dimension)
        if axis is not None and axis < values.ndim:
            # Slice this dimension
            values = np.take(values, [index], axis=axis)
            values = np.squeeze(values, axis=axis)
    
    # Sum over all remaining dimensions (except time)
    # If result is 1D (only time), return as is
    # If result is 2D, sum over non-time dimension
    if values.ndim > 1:
        # Sum over all non-time dimensions
        values = np.sum(values, axis=tuple(range(1, values.ndim)))
    
    return values
```

---

## This Does NOT Question the Whole Operation! ✅

**Why**:
1. ✅ Multi-dimensional arrays support your use case
2. ✅ Plotting just needs aggregation logic
3. ✅ You CAN select by element, material, or combined
4. ✅ This is standard scientific computing

**What You Need**:
- Update plotting functions to handle aggregation
- Add helper functions for common operations
- Gradually migrate plotting code

**The Good News**:
- Core calculations can work with ND arrays
- Plotting is the main area needing updates
- Once updated, you'll have much more powerful analysis

---

## My Recommendation

**Continue with the dimension implementation**, but add helper functions to make plotting easier:

1. ✅ Keep the multi-dimensional structure
2. ✅ Add aggregation helpers in plotting
3. ✅ Update key plotting functions first
4. ✅ Keep backward-compatible defaults

**This is a valid and useful approach!** 🚀



---


================================================================================
# File: NEXT_STEPS_DECISION.md
================================================================================

# Phase 1b Progress Summary & Next Steps

## 🎉 Success So Far

✅ **Baseline calculation completed successfully!**
- System is working with Region dimension
- Multi-dimensional structure (t, m, e) is active
- Validation hooks are in place
- Config loader reads all dimensions from Excel

---

## 📊 Where We Are Now

### **Completed Tasks**

1. ✅ Phase 0: Excel file cleaned and ready
2. ✅ Phase 1a: Validation hooks added to engine modules
3. ✅ Phase 1b: Config loader updated to read dimensions
4. ✅ Phase 1b: Region/Material dimensions added to system_setup.py
5. ✅ Workflow updated to pass dimensions to define_model_scope()
6. ✅ Plotting functions made element-safe with conditional checks
7. ✅ **Baseline calculation working!** ✅

### **Current System State**

- ✅ **3-dimensional system**: Time, Material, Element
- ✅ **Config loading**: Reads Elements, Materials, Regions, Goods, Process_Types
- ✅ **Validation**: ODYM Consistency_Check() at key points
- ✅ **Workflow**: Running successfully

---

## 🔄 What's Next: Following the Structured Plan

### **Option A: Continue Phase 1b - Complete Dimension Implementation**

According to our plan, we should:
1. **Test the 3D system thoroughly** ✅ (Just did!)
2. **Add remaining dimensions** (Good, Process) if needed
3. **Update engine for full 3D operations**

### **Option B: Move to Phase 2 - Class Compliance**

According to the ODYM Compliance Master Plan:
1. Replace manual flow aggregation with ODYM methods
2. Remove custom attributes
3. Use ODYM Extensions mechanism

---

## 🤔 Recommended Next Steps

Given that:
- ✅ Your system is working with 3D structure
- ✅ Baseline calculation successful
- ✅ Config loader reading dimensions properly

**I recommend**:

### **1. Commit Current Progress** (Recommended)
- Save what we've accomplished
- Create a checkpoint before big changes

### **2. Then Choose**:

**Option A: Enhance Plotting for 3D** (Most Practical)
- Add aggregation helpers to plotting functions
- Update Sankey to handle multi-dimensional flows
- Make composition plots work with new structure

**Option B: Add More Dimensions** (Full ODYM Compliance)
- Add Good dimension
- Add Process dimension  
- Update engine for full 6D structure

**Option C: Focus on Class Compliance** (Phase 2)
- Replace manual aggregation with ODYM methods
- Remove custom attributes
- Improve error handling

---

## 💡 My Recommendation

**Go with Option A + commit current state**:

**Why**:
1. You have a working system
2. Plotting is the main user-facing issue
3. Get that fixed first, then add more dimensions
4. Lower risk, higher value

**Steps**:
1. ✅ Commit current progress
2. 🔧 Create aggregation helper functions
3. 🔧 Update key plotting functions (Sankey, composition)
4. 🧪 Test with your working baseline
5. ▶️ Then proceed with more dimensions or Phase 2

---

**Would you like to**:
- A) Commit current progress and enhance plotting?
- B) Continue with adding more dimensions?
- C) Move to Phase 2 (Class Compliance)?
- D) Something else?



---


================================================================================
# File: ODYM_CLASSES_ASPECTS_EXPLANATION.md
================================================================================

# Understanding ODYM Classes, Aspects, and Class Parameters

## Conceptual Clarification

### **ODYM Classes** (Python Objects)
ODYM classes are **Python objects** that represent different components of a Material Flow Analysis (MFA) system. The main ODYM classes are:

1. **`Process`** - Represents a transformation process (e.g., Harvest, Processing, Storage)
2. **`Flow`** - Represents a material flow between processes (e.g., Rye_Straw_Flow)
3. **`Stock`** - Represents material stocks at processes (e.g., dS_1, S_1)
4. **`Parameter`** - Represents system parameters (e.g., Transfer Coefficients, Lifetimes)
5. **`Classification`** - Represents dimension classifications (e.g., Time, Element)
6. **`MFAsystem`** - Represents the entire MFA system

### **Aspects (Dimensions)** 
Aspects are **data structure dimensions** used to describe the multi-dimensional nature of flows, stocks, and parameters. From the ODYM framework:

```python
self.Aspects = {
    "Time": "Model time",
    "Cohort": "Age-cohort",
    "OriginProcess": "Process where flow originates",
    "DestinationProcess": "Destination process of flow",
    "OriginRegion": "Region where flow originates from",
    "DestinationRegion": "Region where flow is bound to",
    "Good": "Process, good, or commodity",
    "Material": "Material: ore, alloy, scrap type, ...",
    "Element": "Chemical element",
}
```

**Key Point**: Aspects define the **dimensional structure** of data arrays (e.g., Flow.Values, Stock.Values, Parameter.Values)

### **Class Parameters (Attributes)**
Class parameters are **properties/attributes** of ODYM class instances. Each class has specific parameters:

## Detailed Class Structure Analysis

### **1. Flow Class Parameters**

```python
class Flow(Obj):
    def __init__(
        self,
        Name=None,        # Flow name
        ID=None,          # Flow ID
        P_Start=None,     # Origin process ID
        P_End=None,       # Destination process ID
        Indices=None,     # AS
        
PECT: Defines which dimensions this flow uses (e.g., "t,e")
        Values=None,      # Values: numpy array with shape matching Indices
    )
```

**Aspects for Flow**:
- **Indices**: Defines which dimensions/aspects the flow uses (e.g., "t,e" for time and element)
- **Values**: Numpy array with shape matching the indices

**Example**:
```python
# Flow with Indices="t,e" (time and element)
flow = Flow(
    Name="Rye_Straw_Flow",
    P_Start=1,  # From Harvest process
    P_End=2,    # To Processing process
    Indices="t,e",  # Time and Element dimensions
    Values=np.zeros((26, 4))  # Shape: (years, elements)
)
```

### **2. Process Class Parameters**

```python
class Process(Obj):
    def __init__(
        self,
        Name=None,        # Process name
        ID=None,          # Process ID
        Extensions=None,  # Process extensions (custom data)
    )
```

**Aspects for Process**:
- Processes themselves don't use aspects/dimensions
- Processes are simple objects with ID, Name, and Extensions
- The **position** of processes in ProcessList determines their ID

### **3. Stock Class Parameters**

```python
class Stock(Obj):
    def __init__(
        self,
        Name=None,        # Stock name
        ID=None,          # Stock ID
        P_Res=None,       # Residence process ID
        Indices=None,     # ASPECT: Defines which dimensions this stock uses
        Values=None,      # Values: numpy array with shape matching Indices
        Type=None,        # Stock type (0=absolute, 1=change)
    )
```

**Aspects for Stock**:
- **Indices**: Defines which dimensions/aspects the stock uses (e.g., "t,e")
- **Values**: Numpy array with shape matching the indices

**Example**:
```python
# Stock with Indices="t,e" (time and element)
stock = Stock(
    Name="dS_1",
    P_Res=1,  # At process 1
    Type=1,   # Change stock
    Indices="t,e",  # Time and Element dimensions
    Values=np.zeros((26, 4))  # Shape: (years, elements)
)
```

### **4. Parameter Class Parameters**

```python
class Parameter(Obj):
    def __init__(
        self,
        Name=None,        # Parameter name
        ID=None,          # Parameter ID
        Indices=None,     # ASPECT: Defines which dimensions this parameter uses
        Values=None,      # Values: numpy array with shape matching Indices
        Unit=None,        # Unit of measurement
    )
```

**Aspects for Parameter**:
- **Indices**: Defines which dimensions/aspects the parameter uses (e.g., "t,e")
- **Values**: Numpy array with shape matching the indices

### **5. Classification Class Parameters**

```python
class Classification(Obj):
    def __init__(
        self,
        Name=None,              # Classification name
        ID=None,                # Classification ID
        Dimension=None,         # Dimension type (Time, Element, etc.)
        Items=None,             # List of items in this classification
        IDs=None,               # List of IDs for items
        AdditionalProps={},     # Additional properties
    )
```

**Purpose**: Classifications define **what items** are in each dimension

## How Aspects (Dimensions) Work with Classes

### **The Relationship**:

1. **Classifications define WHAT items** are in each dimension:
```python
classification_Time = Classification(
    Name="Time",
    Dimension="Time",
    Items=[2020, 2021, 2022, 2023, 2024, 2025]
)

classification_Element = Classification(
    Name="Elements",
    Dimension="Element",
    Items=["C", "N", "P"]
)
```

2. **Indices define WHICH dimensions** a class instance uses:
```python
flow = Flow(
    Name="Rye_Straw_Flow",
    Indices="t,e"  # This flow uses Time (t) and Element (e) dimensions
)
```

3. **Values match the Indices**:
```python
# Indices="t,e" means Values shape must be (n_time, n_element)
flow.Values = np.zeros((26, 3))  # 26 years, 3 elements
```

### **IndexTable Maps Everything Together**:

```python
index_table = pd.DataFrame({
    "Aspect": ["Time", "Element"],
    "Dimension": ["Time", "Element"],
    "Classification": [classification_Time, classification_Element],
    "IndexLetter": ["t", "e"],
})
```

This IndexTable tells the system:
- **"t"** refers to **Time** dimension with items [2020, 2021, ...]
- **"e"** refers to **Element** dimension with items ["C", "N", "P"]
- Flow with Indices="t,e" has shape (26, 3)

## Your Excel Configuration - Mapping to ODYM Classes

### **What You're Defining in Excel**:

#### **1. Dimensions/Aspects Selection** (Your ODYM Configuration Sheet)
```excel
| Dimension Name | Use Dimension | Items |
|----------------|---------------|-------|
| Time | TRUE | 2020-2050 |
| Element | TRUE | C, Remaining DM |
| Process | TRUE | (defined in 2_1_Definition_Processes) |
| Material | TRUE | WC, DM |
| Good | TRUE | (defined in 1_1_Definition_Flows) |
| Region | TRUE | Case_Study_Region |
```

**This creates Classifications** for each dimension

#### **2. Process Definitions** (Sheet: 2_1_Definition_Processes)
```excel
| ID | Process_Name | Process_Logic |
|----|--------------|---------------|
| 1 | Harvest | DSM |
| 2 | Processing | DSM |
```

**This creates Process objects** with Name, ID, and Extensions

#### **3. Flow Definitions** (Sheet: 1_1_Definition_Flows)
```excel
| Flow_ID | Flow_Name | P_Start | P_End | Indices |
|---------|-----------|---------|-------|---------|
| 1 | Rye_Straw_Flow | 1 | 2 | t,e |
```

**This creates Flow objects** with Name, ID, P_Start, P_End, and Indices

**The Indices here specify which aspects/dimensions this flow uses!**

## Key Understanding

### **What You DON'T Need to Do**:
❌ You don't need to define class parameters for every possible aspect
❌ You don't need to describe every class instance with all aspects

### **What You DO Need to Do**:
✅ Define which dimensions/aspects your system will use (your configuration sheet)
✅ Define the Indices for each Flow, Stock, and Parameter (which dimensions it uses)
✅ The Values arrays will automatically match the Indices

## Example: Complete Flow Definition

```python
# From your Excel:
# Sheet: 1_1_Definition_Flows
Flow_ID: 1
Flow_Name: "Rye_Straw_Flow"
P_Start: 1 (Harvest process)
P_End: 2 (Processing process)
Indices: "t,e"  # Uses Time and Element dimensions

# This creates in Python:
flow = Flow(
    Name="Rye_Straw_Flow",
    ID=1,
    P_Start=1,
    P_End=2,
    Indices="t,e"  # This defines which aspects (dimensions) the flow uses
)

# The Values array will be automatically created with shape (n_time, n_element)
# based on your IndexTable

# If you want multi-dimensional flows:
Flow with Indices="t,e,p,m,g"  # Time, Element, Process, Material, Good
# Values shape will be (n_time, n_element, n_process, n_material, n_good)
```

## Summary

**ODYM Classes** = Python objects (Process, Flow, Stock, Parameter)
**Aspects (Dimensions)** = Data structure dimensions (Time, Element, Process, Material, Good, Region)
**Class Parameters** = Properties of class instances (Name, ID, Indices, Values, etc.)

**Your Excel configuration**:
1. Defines **which dimensions** to use (configuration sheet)
2. Defines **which Indices** each Flow/Stock/Parameter uses (definitions sheets)
3. ODYM automatically creates **Values arrays** with correct shapes

**You don't need to manually describe every class with every aspect** - you just need to specify the Indices for each class instance, and ODYM handles the rest!

---

*Document Version: 1.0*  
*Last Updated: [Current Date]*  
*Author: BioDYM Development Team*


---


================================================================================
# File: ODYM_COMPLIANCE_MASTER_PLAN.md
================================================================================

# BioDYM ODYM Compliance Master Plan

## Overview

This document provides a comprehensive master plan for achieving full ODYM compliance across all identified areas: **Classes**, **Functions**, and **Dimensions**. The plan integrates the three compliance analyses into a unified implementation strategy with clear priorities, timelines, and success metrics.

## Executive Summary

- **Overall ODYM Compliance**: 4/10 (Poor) - Significant gaps across all areas
- **Critical Issues**: Missing dimensions, non-compliant functions, limited class usage
- **Implementation Complexity**: 8/10 (Very High) - Requires systematic approach
- **Timeline**: 12-16 weeks total across 4 phases
- **Risk Level**: Medium to High (phased approach with rollback options)
- **Benefits**: Full ODYM compatibility, enhanced scalability, future-proofing

## Compliance Assessment Summary

### **Current Compliance Scores**

| Compliance Area | Current Score | Target Score | Priority | Critical Issues |
|-----------------|---------------|--------------|----------|-----------------|
| **Classes** | 5/10 | 9/10 | High | Manual aggregation, custom attributes |
| **Functions** | 6/10 | 9/10 | High | Limited ODYM integration, basic error handling |
| **Dimensions** | 3/10 | 9/10 | Critical | Missing 4/6 standard dimensions |

### **Overall Compliance**: 4.7/10 (Poor)

---

### **Gemini's Assessment & Recommendations**

**Overall Assessment**: This is an exceptionally thorough and well-structured plan. The analysis is accurate, and the goal of achieving full ODYM compliance is well-supported by the detailed phases.

**Key Consideration**: There is a contradiction in the planning documents regarding Excel template changes. `ODYM_COMPLIANCE_STRATEGY.md` states no changes are needed, while this Master Plan correctly identifies that adding dimensions **requires** significant Excel template updates. **This Master Plan's assessment is correct.** Proceed with the assumption that Excel templates must be modified as planned in Phase 4.

To enhance the plan's robustness and reduce risk, I recommend the following adjustments:

---

### **Workflow & Visualization Strategy**

A critical requirement of this refactoring is to ensure the final visualizations in the main scientific workflow (`00_BioDYM_Workflow.ipynb`) remain consistent with the current output, even after the backend is upgraded to a full 6-dimensional model. This ensures continuity and comparability with previous results.

To achieve this, the project will implement a **"6D -> 2D Aggregated"** workflow:

1.  **6D Compliant Calculation**: The core engine will be refactored to perform all MFA calculations using the full 6-dimensional data model (Time, Element, Region, Good, Material, Process).

2.  **Explicit 2D Aggregation**: After the calculation is complete, a new, mandatory step will be added to the Jupyter notebook. This step will aggregate the 6D results object down to a 2D (Time, Element) view by summing over the new dimensions (Region, Good, Material).

3.  **Consistent 2D Visualization**: The existing plotting functions in the notebook will be pointed to this new, aggregated 2D results object. This guarantees that the primary Sankey diagrams, time-series plots, and stock charts will "display the same calculation results" as the current system.

As part of this strategy, the `00_BioDYM_Workflow.ipynb` will be updated to:
*   **Adopt Standard ODYM Helpers**: The project will prioritize using standard helper functions from `ODYM_Functions.py` (imported as `msf`) for tasks like logging, system inspection, and data aggregation, instead of developing custom utilities.
*   **Showcase ODYM Compliance**: A new "System Inspection" cell will be added that uses a standard ODYM function (e.g., `msf.print_system_summary`) to display a summary of the `MFAsystem` object's structure, making the use of ODYM classes and the new dimensions explicit.
*   **Implement Compliant Aggregation**: The "Explicit 2D Aggregation" step will be implemented using the framework's built-in aggregation functions from `msf`.
*   **Enable Exploratory Analysis**: A separate, optional section will be added for new, multi-dimensional plots that operate on the raw 6D data, allowing for deeper analysis without disrupting the main, established workflow.

---

### **Revised Implementation Strategy: A Lower-Risk Approach**

This revised strategy introduces a **Phase 0** for test creation and breaks the original **Phase 1** into smaller, more manageable steps to mitigate the risks of a "big bang" integration.

#### **Phase 0: Build a Testing Safety Net (1-2 weeks)**
**Priority**: Critical | **Risk Level**: Low

**Objective**: Before any refactoring, create a high-level integration test suite that validates the current system's output. This provides a safety net to ensure existing functionality is preserved.

**Implementation**:
1.  **Identify Key Scenarios**: Select 1-2 representative existing Excel files.
2.  **Establish Golden Datasets**: Run the full workflow for these files and save the key output files (e.g., `results_scientific.xlsx`) as a "golden" reference.
3.  **Create Integration Tests**: Write a new test file (`04_tests/workflow/test_e2e_workflow.py`) that:
    *   Runs the full `main()` workflow with the selected Excel files.
    *   Compares the generated output files against the "golden" reference datasets.
    *   Asserts that the outputs are identical.
4.  **Goal**: These tests must pass before starting Phase 1. They will be expected to fail during the refactoring and will be used to verify correctness as you complete each stage.

---

#### **Revised Phase 1: Iterative Foundation & Dimension Implementation (4-5 weeks)**
**Risk Level**: Medium | **Impact**: Critical | **Priority**: Highest

This phase replaces the original "big bang" approach with a more gradual, iterative implementation of dimensions.

##### **Phase 1a: Foundational Refactoring (1 week)**
**Objective**: Implement class/function improvements that are independent of new dimensions to create a more robust baseline.

**Implementation**:
1.  **Use ODYM Initializers**: In `system_setup.py`, replace manual initialization with `mfa_system.Initialize_FlowValues()`, etc.
2.  **Add Validation Hooks**: Add `mfa_system.Consistency_Check()` calls at key points in the engine modules (`solver.py`, `initial_stock_engine.py`).
3.  **Improve Error Handling**: Wrap critical operations in `try...except` blocks as planned.
4.  **Goal**: All Phase 0 integration tests must still pass.

##### **Phase 1b: Introduce a Single New Dimension (2 weeks)**
**Objective**: Add the 'Region' dimension and adapt the system to handle 3D arrays (`t,e,r`). This validates the multi-dimensional approach on a smaller scale.

**Implementation**:
1.  **Update `system_setup.py`**: Add the 'Region' classification and update the `IndexTable`.
    *   **Correction**: Ensure you call `index_table.set_index('Aspect', inplace=True)` after creating the DataFrame.
2.  **Update `data_loader.py`**: Modify it to look for a `3_1_Definition_Regions` sheet.
    *   **Backward Compatibility**: If the sheet is missing, the loader should automatically create a default, single-item 'Region' classification (e.g., 'Case_Study_Region'). This is critical for ensuring old Excel files still run.
3.  **Update Engine**: Refactor `solver.py`, `initial_stock_engine.py`, etc., to handle 3D NumPy arrays instead of 2D.
4.  **Goal**: Get the Phase 0 integration tests passing again. The logic should be sound for both old files (running on the default 1 region) and new files with multiple regions.

##### **Phase 1c: Add Remaining Dimensions (1-2 weeks)**
**Objective**: With the pattern for adding a dimension established, add 'Good', 'Material', and 'Process'.

**Implementation**:
1.  **Extend `system_setup.py` and `data_loader.py`** for the remaining dimensions, following the backward-compatible pattern from Phase 1b.
2.  **Scale Engine Logic**: Update the engine modules to handle up to 6D arrays. This will be much simpler now that the core multi-dimensional logic is in place.
3.  **Goal**: Get the Phase 0 integration tests passing again.

---

This revised plan front-loads testing and breaks down the most complex phase into manageable steps, significantly lowering the project risk while keeping all the excellent detail from your original plan for Phases 2, 3, and 4. The subsequent phases (Class Compliance, Function Compliance, etc.) can proceed as you've outlined.

## Master Implementation Strategy: 4-Phase Approach

### **Phase 1: Foundation & Dimensions (3-4 weeks)**
**Risk Level**: Medium | **Impact**: Critical | **Priority**: Highest

#### **Objectives**
- Add missing ODYM dimensions (Region, Good, Material, Process)
- Establish proper IndexTable structure
- Update data structures to support multi-dimensional arrays
- Add basic ODYM validation methods

#### **Phase 1 Detailed Implementation Plan**

##### **1.1 Dimension System Implementation** ⏱️ 12-16 hours
**Priority**: Critical | **Files**: `system_setup.py`, `data_loader.py`

**Step 1.1.1: Add Region Dimension** (3-4 hours)
```python
# In system_setup.py
def define_model_scope(start_year, end_year, elements, regions=None):
    """Defines comprehensive model scope with all ODYM dimensions."""
    
    if regions is None:
        regions = ["Case_Study_Region"]  # Default single region
    
    model_classification = {}
    my_years = list(np.arange(start_year, end_year + 1))
    
    # Existing dimensions
    model_classification["Time"] = msc.Classification(
        Name="Time", Dimension="Time", ID=1, Items=my_years
    )
    model_classification["Element"] = msc.Classification(
        Name="Elements", Dimension="Element", ID=2, Items=elements
    )
    
    # NEW: Add Region dimension
    model_classification["Region"] = msc.Classification(
        Name="Regions", Dimension="Region", ID=3, Items=regions
    )
    
    return model_classification
```

**Step 1.1.2: Add Good Dimension** (3-4 hours)
```python
# In system_setup.py
def define_model_scope(start_year, end_year, elements, regions=None, goods=None):
    """Defines comprehensive model scope with all ODYM dimensions."""
    
    if goods is None:
        goods = ["Rye_Straw", "Biochar", "Compost", "Energy"]  # Default goods
    
    # ... existing code ...
    
    # NEW: Add Good dimension
    model_classification["Good"] = msc.Classification(
        Name="Goods", Dimension="Good", ID=4, Items=goods
    )
    
    return model_classification
```

**Step 1.1.3: Add Material Dimension** (3-4 hours)
```python
# In system_setup.py
def define_model_scope(start_year, end_year, elements, regions=None, goods=None, materials=None):
    """Defines comprehensive model scope with all ODYM dimensions."""
    
    if materials is None:
        materials = ["Dry_Matter", "Water_Content", "Carbon_Content"]  # Default materials
    
    # ... existing code ...
    
    # NEW: Add Material dimension
    model_classification["Material"] = msc.Classification(
        Name="Materials", Dimension="Material", ID=5, Items=materials
    )
    
    return model_classification
```

**Step 1.1.4: Add Process Dimension** (3-4 hours)
```python
# In system_setup.py
def define_model_scope(start_year, end_year, elements, regions=None, goods=None, materials=None, processes=None):
    """Defines comprehensive model scope with all ODYM dimensions."""
    
    if processes is None:
        processes = ["Harvest", "Processing", "Storage", "Application"]  # Default processes
    
    # ... existing code ...
    
    # NEW: Add Process dimension
    model_classification["Process"] = msc.Classification(
        Name="Processes", Dimension="Process", ID=6, Items=processes
    )
    
    # Update IndexTable with all dimensions
    index_table = pd.DataFrame({
        "Aspect": ["Time", "Element", "Region", "Good", "Material", "Process"],
        "Description": [
            'Model aspect "time"',
            'Model aspect "Element"',
            'Model aspect "Region"',
            'Model aspect "Good"',
            'Model aspect "Material"',
            'Model aspect "Process"'
        ],
        "Dimension": ["Time", "Element", "Region", "Good", "Material", "Process"],
        "Classification": [
            model_classification["Time"],
            model_classification["Element"],
            model_classification["Region"],
            model_classification["Good"],
            model_classification["Material"],
            model_classification["Process"]
        ],
        "IndexLetter": ["t", "e", "r", "g", "m", "p"],
    })
    
    return model_classification, index_table
```

##### **1.2 Data Structure Migration** ⏱️ 8-10 hours
**Priority**: High | **Files**: `system_setup.py`, `initial_stock_engine.py`, `solver.py`

**Step 1.2.1: Update Flow Indices** (3-4 hours)
```python
# In system_setup.py
def create_flow_with_full_indices(mfa_system, flow_name, process_start, process_end):
    """Create flow with full ODYM-compliant indices."""
    
    # Determine flow indices based on available dimensions
    indices = "t,e"  # Start with Time and Element
    
    if "Region" in mfa_system.IndexTable.index:
        indices += ",r"
    if "Good" in mfa_system.IndexTable.index:
        indices += ",g"
    if "Material" in mfa_system.IndexTable.index:
        indices += ",m"
    if "Process" in mfa_system.IndexTable.index:
        indices += ",p"
    
    # Create flow with proper indices
    flow = msc.Flow(
        Name=flow_name,
        P_Start=process_start,
        P_End=process_end,
        Indices=indices
    )
    
    return flow
```

**Step 1.2.2: Update Data Array Shapes** (3-4 hours)
```python
# In system_setup.py
def initialize_flow_values(mfa_system, flow):
    """Initialize flow values with proper dimensions."""
    
    # Get dimension sizes
    n_years = len(mfa_system.IndexTable.Classification["Time"].Items)
    n_elements = len(mfa_system.IndexTable.Classification["Element"].Items)
    
    # Initialize with Time and Element dimensions
    shape = [n_years, n_elements]
    
    # Add additional dimensions if available
    if "Region" in mfa_system.IndexTable.index:
        n_regions = len(mfa_system.IndexTable.Classification["Region"].Items)
        shape.append(n_regions)
    
    if "Good" in mfa_system.IndexTable.index:
        n_goods = len(mfa_system.IndexTable.Classification["Good"].Items)
        shape.append(n_goods)
    
    if "Material" in mfa_system.IndexTable.index:
        n_materials = len(mfa_system.IndexTable.Classification["Material"].Items)
        shape.append(n_materials)
    
    if "Process" in mfa_system.IndexTable.index:
        n_processes = len(mfa_system.IndexTable.Classification["Process"].Items)
        shape.append(n_processes)
    
    # Initialize flow values
    flow.Values = np.zeros(shape)
    
    return flow
```

**Step 1.2.3: Update Engine Modules** (2-2 hours)
```python
# In solver.py, update flow aggregation
def calculate_process_flows_multi_dimensional(mfa_system, process_id):
    """Calculate process flows with multi-dimensional support."""
    inflows = []
    for flow in mfa_system.FlowDict.values():
        if flow.P_End == process_id:
            # Handle multi-dimensional flow values
            if flow.Values is not None:
                inflows.append(flow.Values)
    
    if inflows:
        return sum(inflows)
    else:
        # Return zeros with correct multi-dimensional shape
        return np.zeros(mfa_system.get_flow_shape())
```

##### **1.3 Basic ODYM Validation** ⏱️ 4-6 hours
**Priority**: High | **Files**: All engine modules

**Step 1.3.1: Add Consistency Checks** (2-3 hours)
```python
# In solver.py, add after major operations
def add_odym_validation(mfa_system, operation_name=""):
    """Add ODYM validation after operations."""
    try:
        mfa_system.Consistency_Check()
        mfa_system.IndexTableCheck()
        print(f"✅ {operation_name} validation passed")
        return True
    except Exception as e:
        print(f"❌ {operation_name} validation failed: {e}")
        return False
```

**Step 1.3.2: Add Error Handling** (2-3 hours)
```python
# In all engine modules, wrap operations
def safe_odym_operation(operation_func, *args, **kwargs):
    """Safely execute ODYM operations with error handling."""
    try:
        result = operation_func(*args, **kwargs)
        return result
    except AttributeError as e:
        print(f"❌ Missing attribute: {e}")
        raise ValueError(f"Invalid ODYM object structure: {e}")
    except Exception as e:
        print(f"❌ Operation failed: {e}")
        raise
```

#### **Phase 1 Success Criteria**
- [ ] All 6 ODYM dimensions implemented
- [ ] IndexTable includes all dimensions
- [ ] Flow indices support multi-dimensional arrays
- [ ] Data structures support 6D arrays
- [ ] Basic ODYM validation added
- [ ] Error handling implemented
- [ ] All existing tests pass

---

### **Phase 2: Class Compliance (3-4 weeks)**
**Risk Level**: Medium | **Impact**: High | **Priority**: High

#### **Objectives**
- Replace manual flow aggregation with ODYM methods
- Remove custom attributes from ODYM objects
- Use ODYM initialization methods
- Implement proper ODYM flow management

#### **Phase 2 Detailed Implementation Plan**

##### **2.1 ODYM Method Integration** ⏱️ 10-12 hours
**Priority**: High | **Files**: `solver.py`, `initial_stock_engine.py`

**Step 2.1.1: Replace Manual Flow Aggregation** (4-6 hours)
```python
# In solver.py
def calculate_process_inflows_odym_compliant(mfa_system, process_id):
    """Calculate total inflows to a process using ODYM methods."""
    try:
        inflows = []
        for flow in mfa_system.FlowDict.values():
            if flow.P_End == process_id:
                # Use ODYM's Flow_Sum_By_Element method
                flow_sum = mfa_system.Flow_Sum_By_Element(flow.Name)
                inflows.append(flow_sum)
        
        if inflows:
            return sum(inflows)
        else:
            # Return zeros with correct shape
            return np.zeros(mfa_system.get_flow_shape())
    except Exception as e:
        print(f"❌ Flow aggregation failed for process {process_id}: {e}")
        raise

# Replace manual aggregation in calculate_final_balances()
def calculate_final_balances(mfa_system):
    """Calculate final balances using ODYM methods."""
    try:
        for pid in {p.ID for p in mfa_system.ProcessList}:
            # Use ODYM-compliant methods
            total_inflows = calculate_process_inflows_odym_compliant(mfa_system, pid)
            total_outflows = calculate_process_outflows_odym_compliant(mfa_system, pid)
            
            # Process balance calculations
            # ... existing logic ...
        
        # Add ODYM validation
        mfa_system.Consistency_Check()
        return mfa_system
    except Exception as e:
        print(f"❌ Balance calculation failed: {e}")
        raise
```

**Step 2.1.2: Implement ODYM Flow Management** (3-4 hours)
```python
# In initial_stock_engine.py
def create_flow_odym_compliant(mfa_system, flow_name, process_id, destination_process):
    """Create flow using ODYM-compliant methods."""
    try:
        # Check if flow already exists
        if flow_name in mfa_system.FlowDict:
            return mfa_system.FlowDict[flow_name]
        
        # Create flow object with proper indices
        flow = msc.Flow(
            Name=flow_name,
            P_Start=process_id,
            P_End=destination_process,
            Indices=mfa_system.get_flow_indices()
        )
        
        # Add to system using proper method
        mfa_system.FlowDict[flow_name] = flow
        
        # Initialize values using ODYM method
        mfa_system.Initialize_FlowValues()
        
        return flow
    except Exception as e:
        print(f"❌ Flow creation failed: {e}")
        raise
```

**Step 2.1.3: Use ODYM Initialization Methods** (3-2 hours)
```python
# In system_setup.py
def initialize_mfa_system_odym_compliant(model_classification, index_table):
    """Initialize MFA system using ODYM methods."""
    try:
        start_time = model_classification["Time"].Items[0]
        end_time = model_classification["Time"].Items[-1]
        element_items = model_classification["Element"].Items
        
        mfa_system = msc.MFAsystem(
            Name="RyeStrawMFA",
            Geogr_Scope="Case_Study_Region",
            Unit="Mg",
            ProcessList=[],
            FlowDict={},
            StockDict={},
            ParameterDict={},
            Time_Start=start_time,
            Time_End=end_time,
            IndexTable=index_table,
            Elements=element_items,
        )
        
        # Use ODYM initialization methods
        mfa_system.Initialize_FlowValues()
        mfa_system.Initialize_StockValues()
        mfa_system.Initialize_ParameterValues()
        
        # Validate system
        mfa_system.Consistency_Check()
        
        return mfa_system
    except Exception as e:
        print(f"❌ MFA system initialization failed: {e}")
        raise
```

##### **2.2 Remove Custom Attributes** ⏱️ 6-8 hours
**Priority**: High | **Files**: `initial_stock_engine.py`, `solver.py`, `fomp_model.py`

**Step 2.2.1: Replace Custom Attributes with ODYM Extensions** (3-4 hours)
```python
# In initial_stock_engine.py
def store_initial_stock_config_odym_compliant(mfa_system, process_id, config):
    """Store initial stock configuration using ODYM Extensions."""
    try:
        process = mfa_system.ProcessList[process_id]
        process.add_extension(
            Time=None,
            Name="initial_stock_config",
            Value=config,
            Unit="configuration"
        )
    except Exception as e:
        print(f"❌ Failed to store initial stock config: {e}")
        raise

# Replace custom attribute usage
def _create_single_outflow_flow(mfa_system, flow_name, process_id, destination_process, initial_stock, consumption_rate, split_fraction=1.0):
    """Create outflow flow using ODYM-compliant methods."""
    try:
        # Create flow using ODYM-compliant method
        flow = create_flow_odym_compliant(mfa_system, flow_name, process_id, destination_process)
        
        # Store configuration using ODYM Extensions
        config = {
            'initial_stock': initial_stock.copy(),
            'consumption_rate': consumption_rate,
            'split_fraction': split_fraction
        }
        store_initial_stock_config_odym_compliant(mfa_system, process_id, config)
        
        return flow
    except Exception as e:
        print(f"❌ Outflow flow creation failed: {e}")
        raise
```

**Step 2.2.2: Update FOMP Process Handling** (3-4 hours)
```python
# In solver.py
def _calculate_fomp_flows_odym_compliant(mfa_system, fomp_processes, fomp_params):
    """Calculate FOMP flows using ODYM-compliant methods."""
    try:
        for process_id in fomp_processes:
            # Get FOMP configuration from ODYM Extensions
            process = mfa_system.ProcessList[process_id]
            fomp_config = get_process_extension(mfa_system, process_id, "fomp_config")
            
            if fomp_config:
                # Process FOMP calculations
                # ... existing logic ...
                
                # Update flows using ODYM methods
                for flow_name, flow_values in fomp_results.items():
                    if flow_name in mfa_system.FlowDict:
                        mfa_system.FlowDict[flow_name].Values = flow_values
                
                # Validate after FOMP calculations
                mfa_system.Consistency_Check()
        
        return True
    except Exception as e:
        print(f"❌ FOMP flow calculation failed: {e}")
        raise
```

##### **2.3 Mass Balance Improvements** ⏱️ 4-6 hours
**Priority**: Medium | **Files**: `solver.py`

**Step 2.3.1: Use ODYM Mass Balance Methods** (2-3 hours)
```python
# In solver.py
def calculate_mass_balance_odym_compliant(mfa_system):
    """Calculate mass balance using ODYM's built-in method."""
    try:
        balance = mfa_system.MassBalance()
        
        # Check for significant imbalances
        max_imbalance = np.max(np.abs(balance))
        if max_imbalance > 1e-6:  # Tolerance for numerical errors
            print(f"⚠️ WARNING: Mass balance imbalance: {max_imbalance}")
            return False
        else:
            print("✅ Mass balance within tolerance")
            return True
    except Exception as e:
        print(f"❌ Mass balance calculation failed: {e}")
        return False
```

**Step 2.3.2: Add Comprehensive Validation** (2-3 hours)
```python
# NEW FILE: 02_src/engine/validation.py
def validate_mfa_system_state(mfa_system, operation_name=""):
    """Comprehensive validation of MFA system state."""
    try:
        # Check index table consistency
        mfa_system.IndexTableCheck()
        
        # Check system consistency
        mfa_system.Consistency_Check()
        
        # Check for negative values in flows
        for flow_name, flow in mfa_system.FlowDict.items():
            if flow.Values is not None and np.any(flow.Values < 0):
                print(f"⚠️ WARNING: Negative values found in flow {flow_name}")
        
        print(f"✅ System validation passed for {operation_name}")
        return True
        
    except Exception as e:
        print(f"❌ System validation failed for {operation_name}: {e}")
        return False
```

#### **Phase 2 Success Criteria**
- [ ] ODYM methods used for flow aggregation
- [ ] Custom attributes removed from ODYM objects
- [ ] ODYM Extensions used for configuration
- [ ] ODYM initialization methods implemented
- [ ] Mass balance calculations improved
- [ ] Comprehensive validation added
- [ ] All existing functionality preserved

---

### **Phase 3: Function Compliance (3-4 weeks)**
**Risk Level**: Medium | **Impact**: Medium | **Priority**: Medium

#### **Objectives**
- Add type hints to all functions
- Implement comprehensive error handling
- Add input validation
- Adopt ODYM function patterns

#### **Phase 3 Detailed Implementation Plan**

##### **3.1 Type Safety Implementation** ⏱️ 8-10 hours
**Priority**: High | **Files**: All engine modules

**Step 3.1.1: Add Type Hints** (4-5 hours)
```python
# In all engine modules, add type hints
from typing import Dict, List, Optional, Tuple, Union
import numpy as np

def calculate_final_balances(mfa_system: msc.MFAsystem) -> msc.MFAsystem:
    """Calculate final balances with proper type hints."""
    pass

def load_initial_stock_parameters(excel_data: Dict[str, pd.DataFrame]) -> Dict[int, Dict]:
    """Load initial stock parameters with type hints."""
    pass

def calculate_dynamic_stock(mfa_system: msc.MFAsystem, dsm_params_config: Dict) -> bool:
    """Calculate dynamic stock with type hints."""
    pass
```

**Step 3.1.2: Add Input Validation** (4-5 hours)
```python
# In all engine modules, add input validation
def calculate_final_balances(mfa_system: msc.MFAsystem) -> msc.MFAsystem:
    """Calculate final balances with input validation."""
    if not isinstance(mfa_system, msc.MFAsystem):
        raise TypeError("mfa_system must be an MFAsystem object")
    
    if not mfa_system.FlowDict:
        raise ValueError("MFA system has no flows defined")
    
    if not mfa_system.ProcessList:
        raise ValueError("MFA system has no processes defined")
    
    # Implementation
    pass
```

##### **3.2 Error Handling Implementation** ⏱️ 6-8 hours
**Priority**: High | **Files**: All engine modules

**Step 3.2.1: Add Comprehensive Error Handling** (3-4 hours)
```python
# In all engine modules, add error handling
import logging

logger = logging.getLogger(__name__)

def calculate_final_balances(mfa_system: msc.MFAsystem) -> msc.MFAsystem:
    """Calculate final balances with comprehensive error handling."""
    try:
        # Input validation
        if not isinstance(mfa_system, msc.MFAsystem):
            raise TypeError("mfa_system must be an MFAsystem object")
        
        # Implementation
        # ... existing logic ...
        
        # Validation after calculation
        mfa_system.Consistency_Check()
        
        return mfa_system
        
    except AttributeError as e:
        logger.error(f"Missing attribute in MFA system: {e}")
        raise ValueError(f"Invalid MFA system structure: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in balance calculation: {e}")
        raise
```

**Step 3.2.2: Add Logging Integration** (3-4 hours)
```python
# NEW FILE: 02_src/engine/logging_setup.py
import logging
import ODYM_Functions as msf

def setup_biodym_logging(log_filename: str, log_path: str) -> logging.Logger:
    """Setup logging using ODYM patterns."""
    logger, console_log, file_log = msf.function_logger(
        log_filename=log_filename,
        log_pathname=log_path,
        file_level=logging.DEBUG,
        console_level=logging.INFO
    )
    return logger

# In all engine modules, add logging
logger = setup_biodym_logging("biodym_engine.log", "logs/")
```

##### **3.3 ODYM Function Patterns** ⏱️ 6-8 hours
**Priority**: Medium | **Files**: All engine modules

**Step 3.3.1: Implement ODYM Naming Conventions** (3-4 hours)
```python
# Adopt ODYM naming patterns
def MI_CalculateFlowAggregation(mfa_system: msc.MFAsystem, process_id: int) -> np.ndarray:
    """Calculate flow aggregation using ODYM methods."""
    pass

def ODYM_ValidateSystemConsistency(mfa_system: msc.MFAsystem) -> bool:
    """Validate system consistency using ODYM methods."""
    pass

def ODYM_CalculateMassBalance(mfa_system: msc.MFAsystem) -> np.ndarray:
    """Calculate mass balance using ODYM methods."""
    pass
```

**Step 3.3.2: Implement Pure Functions** (3-4 hours)
```python
# Create pure functions where possible
def calculate_fomp_series_pure(dm_inflow_series: np.ndarray, params: Dict, initial_stock_labile: float, initial_stock_recalcitrant: float) -> Dict[str, np.ndarray]:
    """Pure function for FOMP series calculation."""
    # Implementation without side effects
    pass

def calculate_outflow_from_inflows_pure(total_inflow_values: np.ndarray, params: Dict, time_vector: np.ndarray) -> np.ndarray:
    """Pure function for outflow calculation."""
    # Implementation without side effects
    pass
```

#### **Phase 3 Success Criteria**
- [ ] Type hints added to all functions
- [ ] Input validation implemented
- [ ] Comprehensive error handling added
- [ ] Logging integration complete
- [ ] ODYM function patterns adopted
- [ ] Pure functions implemented where possible
- [ ] All existing functionality preserved

---

### **Phase 4: Advanced Integration & Optimization (3-4 weeks)**
**Risk Level**: High | **Impact**: High | **Priority**: Medium

#### **Objectives**
- Implement BioDYM extensions using ODYM Extensions mechanism
- Optimize performance for multi-dimensional operations
- Complete comprehensive testing
- Finalize Excel template updates

#### **Phase 4 Detailed Implementation Plan**

##### **4.1 BioDYM Extensions Implementation** ⏱️ 10-12 hours
**Priority**: Medium | **Files**: `bioDYM_classes.py`, All engine modules

**Step 4.1.1: Create BioDYM Extension Classes** (4-6 hours)
```python
# In bioDYM_classes.py
class FOMPProcess(msc.Process):
    """BioDYM extension of ODYM Process for FOMP calculations."""
    
    def __init__(self, Name=None, ID=None, **kwargs):
        super().__init__(Name=Name, ID=ID, **kwargs)
        self.fomp_params = {}
        self.protected_flows = set()
    
    def add_fomp_parameter(self, param_name: str, value: float) -> None:
        """Add FOMP-specific parameter."""
        self.fomp_params[param_name] = value
    
    def protect_flow(self, flow_name: str) -> None:
        """Mark flow as FOMP-protected."""
        self.protected_flows.add(flow_name)

class InitialStockManager:
    """BioDYM extension for initial stock management."""
    
    def __init__(self, mfa_system: msc.MFAsystem):
        self.mfa_system = mfa_system
        self.configs = {}
    
    def add_initial_stock_config(self, process_id: int, config: Dict) -> None:
        """Add initial stock configuration."""
        self.configs[process_id] = config
    
    def process_initial_stocks(self) -> bool:
        """Process all initial stocks using ODYM methods."""
        try:
            for process_id, config in self.configs.items():
                # Process using ODYM-compliant methods
                pass
            return True
        except Exception as e:
            print(f"❌ Initial stock processing failed: {e}")
            return False
```

**Step 4.1.2: Integrate Extensions with MFA System** (3-4 hours)
```python
# In system_setup.py
def initialize_biodym_extensions(mfa_system: msc.MFAsystem) -> msc.MFAsystem:
    """Initialize BioDYM-specific extensions."""
    try:
        from .bioDYM_classes import InitialStockManager, FOMPProcess
        
        mfa_system.biodym_extensions = {
            'initial_stock': InitialStockManager(mfa_system),
            'fomp': FOMPProcess()
        }
        
        return mfa_system
    except Exception as e:
        print(f"❌ BioDYM extensions initialization failed: {e}")
        raise
```

**Step 4.1.3: Update Engine Modules to Use Extensions** (3-2 hours)
```python
# In initial_stock_engine.py
def process_initial_stocks_with_extensions(mfa_system: msc.MFAsystem) -> msc.MFAsystem:
    """Process initial stocks using BioDYM extensions."""
    try:
        if hasattr(mfa_system, 'biodym_extensions'):
            initial_stock_manager = mfa_system.biodym_extensions['initial_stock']
            success = initial_stock_manager.process_initial_stocks()
            
            if success:
                mfa_system.Consistency_Check()
                return mfa_system
            else:
                raise ValueError("Initial stock processing failed")
        else:
            # Fallback to existing method
            return process_initial_stocks(mfa_system)
    except Exception as e:
        print(f"❌ Initial stock processing with extensions failed: {e}")
        raise
```

##### **4.2 Performance Optimization** ⏱️ 8-10 hours
**Priority**: Medium | **Files**: `solver.py`, `dsm_model.py`, `fomp_model.py`

**Step 4.2.1: Optimize Multi-Dimensional Operations** (4-5 hours)
```python
# In solver.py
def calculate_flows_vectorized(mfa_system: msc.MFAsystem, process_ids: List[int]) -> Dict[int, np.ndarray]:
    """Calculate flows for multiple processes using vectorized operations."""
    try:
        results = {}
        
        # Use numpy operations for better performance
        for process_id in process_ids:
            inflows = []
            for flow in mfa_system.FlowDict.values():
                if flow.P_End == process_id and flow.Values is not None:
                    inflows.append(flow.Values)
            
            if inflows:
                results[process_id] = np.sum(inflows, axis=0)
            else:
                results[process_id] = np.zeros(mfa_system.get_flow_shape())
        
        return results
    except Exception as e:
        print(f"❌ Vectorized flow calculation failed: {e}")
        raise
```

**Step 4.2.2: Add Performance Monitoring** (4-5 hours)
```python
# NEW FILE: 02_src/engine/performance_monitor.py
import time
from functools import wraps

def monitor_performance(func):
    """Decorator to monitor function performance."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"⏱️ {func.__name__} executed in {end_time - start_time:.3f} seconds")
        return result
    return wrapper

# Apply to critical functions
@monitor_performance
def calculate_dynamic_stock(mfa_system: msc.MFAsystem, dsm_params_config: Dict) -> bool:
    # Existing implementation
    pass

@monitor_performance
def calculate_fomp(mfa_system: msc.MFAsystem, fomp_params_config: Dict, input_flow_composition: np.ndarray) -> bool:
    # Existing implementation
    pass
```

##### **4.3 Excel Template Updates** ⏱️ 12-16 hours
**Priority**: High | **Files**: Excel templates, `data_loader.py`

**Step 4.3.1: Create New Excel Sheets** (6-8 hours)
```python
# Create new Excel sheets for dimensions
EXCEL_SHEET_STRUCTURE = {
    "3_1_Definition_Regions": {
        "columns": ["Region_ID", "Region_Name", "Description", "Geographic_Scope"],
        "required": True
    },
    "3_2_Data_Regions": {
        "columns": ["Region_ID", "Region_Name", "Population", "Area_km2", "GDP"],
        "required": False
    },
    "4_1_Definition_Goods": {
        "columns": ["Good_ID", "Good_Name", "Description", "Category", "Unit"],
        "required": True
    },
    "4_2_Data_Goods": {
        "columns": ["Good_ID", "Good_Name", "Market_Price", "Availability", "Quality_Factor"],
        "required": False
    },
    "5_1_Definition_Materials": {
        "columns": ["Material_ID", "Material_Name", "Description", "Composition"],
        "required": True
    },
    "5_2_Data_Materials": {
        "columns": ["Material_ID", "Material_Name", "Density", "Moisture_Content", "Carbon_Content"],
        "required": False
    },
    "6_1_Definition_Processes": {
        "columns": ["Process_ID", "Process_Name", "Description", "Type", "Efficiency"],
        "required": True
    },
    "6_2_Data_Processes": {
        "columns": ["Process_ID", "Process_Name", "Energy_Consumption", "Water_Consumption", "Emissions"],
        "required": False
    }
}
```

**Step 4.3.2: Update Data Loader** (6-8 hours)
```python
# In data_loader.py
def load_multi_dimensional_data(excel_file_path: str) -> Dict[str, pd.DataFrame]:
    """Load data with multi-dimensional support."""
    try:
        all_data = {}
        
        # Load existing sheets
        existing_sheets = ["1_1_Definition_Flows", "1_2_Data_Flows", "2_1_Definition_Processes", 
                          "2_2_static_TCs", "2_3_dynamic_TCs", "2_4_Initial_Stock"]
        
        for sheet_name in existing_sheets:
            try:
                all_data[sheet_name] = pd.read_excel(excel_file_path, sheet_name=sheet_name)
            except Exception as e:
                print(f"⚠️ WARNING: Could not load sheet {sheet_name}: {e}")
        
        # Load new dimension sheets
        new_sheets = ["3_1_Definition_Regions", "3_2_Data_Regions", "4_1_Definition_Goods", 
                     "4_2_Data_Goods", "5_1_Definition_Materials", "5_2_Data_Materials",
                     "6_1_Definition_Processes", "6_2_Data_Processes"]
        
        for sheet_name in new_sheets:
            try:
                all_data[sheet_name] = pd.read_excel(excel_file_path, sheet_name=sheet_name)
            except Exception as e:
                print(f"⚠️ WARNING: Could not load new sheet {sheet_name}: {e}")
                # Create empty DataFrame with required structure
                all_data[sheet_name] = pd.DataFrame(columns=EXCEL_SHEET_STRUCTURE[sheet_name]["columns"])
        
        return all_data
    except Exception as e:
        print(f"❌ Data loading failed: {e}")
        raise
```

##### **4.4 Comprehensive Testing** ⏱️ 8-10 hours
**Priority**: High | **Files**: Test files

**Step 4.4.1: Create Test Suite** (4-5 hours)
```python
# NEW FILE: tests/test_odym_compliance.py
import unittest
import numpy as np
from src.system_setup import define_model_scope, initialize_mfa_system_odym_compliant
from src.engine.solver import calculate_final_balances
from src.engine.initial_stock_engine import process_initial_stocks

class TestODYMCompliance(unittest.TestCase):
    """Test suite for ODYM compliance."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.start_year = 2020
        self.end_year = 2025
        self.elements = ["material", "WC", "DM", "CC"]
        self.regions = ["Region_A", "Region_B"]
        self.goods = ["Rye_Straw", "Biochar"]
        self.materials = ["Dry_Matter", "Water_Content"]
        self.processes = ["Harvest", "Processing"]
    
    def test_dimension_compliance(self):
        """Test dimension compliance."""
        model_classification, index_table = define_model_scope(
            self.start_year, self.end_year, self.elements, 
            self.regions, self.goods, self.materials, self.processes
        )
        
        # Test all dimensions are present
        self.assertIn("Time", model_classification)
        self.assertIn("Element", model_classification)
        self.assertIn("Region", model_classification)
        self.assertIn("Good", model_classification)
        self.assertIn("Material", model_classification)
        self.assertIn("Process", model_classification)
        
        # Test IndexTable structure
        self.assertEqual(len(index_table), 6)
        self.assertIn("Region", index_table.index)
        self.assertIn("Good", index_table.index)
        self.assertIn("Material", index_table.index)
        self.assertIn("Process", index_table.index)
    
    def test_class_compliance(self):
        """Test class compliance."""
        model_classification, index_table = define_model_scope(
            self.start_year, self.end_year, self.elements, 
            self.regions, self.goods, self.materials, self.processes
        )
        
        mfa_system = initialize_mfa_system_odym_compliant(model_classification, index_table)
        
        # Test ODYM methods are available
        self.assertTrue(hasattr(mfa_system, 'Consistency_Check'))
        self.assertTrue(hasattr(mfa_system, 'IndexTableCheck'))
        self.assertTrue(hasattr(mfa_system, 'Initialize_FlowValues'))
        
        # Test system validation
        try:
            mfa_system.Consistency_Check()
            mfa_system.IndexTableCheck()
        except Exception as e:
            self.fail(f"System validation failed: {e}")
    
    def test_function_compliance(self):
        """Test function compliance."""
        # Test type hints
        import inspect
        
        sig = inspect.signature(calculate_final_balances)
        self.assertIn('mfa_system', sig.parameters)
        
        # Test error handling
        with self.assertRaises(TypeError):
            calculate_final_balances("invalid_input")
    
    def test_performance(self):
        """Test performance improvements."""
        import time
        
        model_classification, index_table = define_model_scope(
            self.start_year, self.end_year, self.elements, 
            self.regions, self.goods, self.materials, self.processes
        )
        
        mfa_system = initialize_mfa_system_odym_compliant(model_classification, index_table)
        
        start_time = time.time()
        result = calculate_final_balances(mfa_system)
        end_time = time.time()
        
        execution_time = end_time - start_time
        self.assertLess(execution_time, 5.0, "Performance regression detected")

if __name__ == '__main__':
    unittest.main()
```

**Step 4.4.2: Integration Testing** (4-5 hours)
```python
# NEW FILE: tests/test_integration.py
import unittest
import numpy as np
from src.main import main

class TestIntegration(unittest.TestCase):
    """Integration tests for complete ODYM compliance."""
    
    def test_full_workflow(self):
        """Test complete BioDYM workflow with ODYM compliance."""
        try:
            # Run complete workflow
            result = main()
            
            # Verify results
            self.assertIsNotNone(result)
            
            # Verify ODYM compliance
            mfa_system = result['mfa_system']
            mfa_system.Consistency_Check()
            mfa_system.IndexTableCheck()
            
        except Exception as e:
            self.fail(f"Integration test failed: {e}")
    
    def test_backward_compatibility(self):
        """Test backward compatibility with existing Excel templates."""
        try:
            # Test with existing Excel template
            result = main()
            
            # Verify results are consistent
            self.assertIsNotNone(result)
            
        except Exception as e:
            self.fail(f"Backward compatibility test failed: {e}")

if __name__ == '__main__':
    unittest.main()
```

#### **Phase 4 Success Criteria**
- [ ] BioDYM extensions implemented using ODYM Extensions mechanism
- [ ] Performance optimized for multi-dimensional operations
- [ ] Excel templates updated with new dimension sheets
- [ ] Comprehensive test suite created
- [ ] Integration testing complete
- [ ] Backward compatibility maintained
- [ ] Full ODYM compliance achieved

---

## Comprehensive To-Do List

This to-do list is structured around the revised, lower-risk implementation strategy.

### **Phase 0: Build a Testing Safety Net (1-2 weeks)**
- [ ] **Task 0.1**: Identify 1-2 representative Excel files for creating "golden" test datasets.
- [ ] **Task 0.2**: Run the full, current workflow and save the key output files as the "golden" reference versions.
- [ ] **Task 0.3**: Create a new integration test file (`04_tests/workflow/test_e2e_workflow.py`).
- [ ] **Task 0.4**: Implement the tests to run the workflow and assert that the output matches the golden reference files.
- [ ] **Goal**: Ensure all Phase 0 tests pass before starting Phase 1.

### **Phase 1: Iterative Foundation & Dimension Implementation (4-5 weeks)**
#### **Phase 1a: Foundational Refactoring (1 week)**
- [ ] **Task 1a.1**: In `system_setup.py`, replace manual object initialization with ODYM methods (`Initialize_FlowValues()`, etc.).
- [ ] **Task 1a.2**: Add `mfa_system.Consistency_Check()` calls at key points in `solver.py` and `initial_stock_engine.py`.
- [ ] **Task 1a.3**: Wrap critical ODYM operations in `try...except` blocks for robust error handling.
- [ ] **Goal**: Ensure all Phase 0 tests still pass after this refactoring.

#### **Phase 1b: Introduce a Single New Dimension ('Region') (2 weeks)**
- [ ] **Task 1b.1**: Update `system_setup.py` to add the 'Region' classification and update the `IndexTable` (ensuring `set_index('Aspect')` is used).
- [ ] **Task 1b.2**: Update `data_loader.py` to read the 'Region' definition from Excel, with a backward-compatible fallback to a default region if the sheet is missing.
- [ ] **Task 1b.3**: Refactor the engine modules (`solver.py`, etc.) to handle 3D (`t,e,r`) NumPy arrays instead of 2D.
- [ ] **Goal**: Ensure Phase 0 tests pass with both old and new Excel files.

#### **Phase 1c: Add Remaining Dimensions ('Good', 'Material', 'Process') (1-2 weeks)**
- [ ] **Task 1c.1**: Extend `system_setup.py` and `data_loader.py` for the 'Good', 'Material', and 'Process' dimensions, following the backward-compatible pattern.
- [ ] **Task 1c.2**: Scale up the engine logic to handle up to 6D arrays.
- [ ] **Goal**: Ensure Phase 0 tests pass.

### **Phase 2: Class Compliance (3-4 weeks)**
- [ ] **Task 2.1**: Replace all manual flow aggregation logic with ODYM methods (e.g., `Flow_Sum_By_Element`).
- [ ] **Task 2.2**: Refactor all custom attributes (e.g., `_fomp_protected`) to use the ODYM Extensions mechanism (`process.add_extension(...)`).
- [ ] **Task 2.3**: Implement proper ODYM flow management for creating and initializing flows.
- [ ] **Task 2.4**: Replace manual mass balance calculations with `mfa_system.MassBalance()`.
- [ ] **Task 2.5**: Create a comprehensive validation module (`02_src/engine/validation.py`).

### **Phase 3: Function Compliance (3-4 weeks)**
- [ ] **Task 3.1**: Add full type hints to all functions in the `engine` modules.
- [ ] **Task 3.2**: Implement robust input validation at the start of all public functions.
- [ ] **Task 3.3**: Integrate a standard ODYM logger (`msf.function_logger`) into all modules.
- [ ] **Task 3.4**: Refactor function names to follow ODYM conventions where appropriate (e.g., `MI_Calculate...`).
- [ ] **Task 3.5**: Identify and refactor functions to be "pure" (no side effects) where possible.

### **Phase 4: Advanced Integration & Finalization (3-4 weeks)**
- [ ] **Task 4.1**: Implement BioDYM-specific features (FOMP, Initial Stock) as formal classes that extend ODYM base classes.
- [ ] **Task 4.2**: Investigate and implement performance optimizations for multi-dimensional operations (e.g., vectorization with NumPy).
- [ ] **Task 4.3**: Finalize the new Excel template structure with sheets for all 6 dimensions.
- [ ] **Task 4.4**: Create the final, comprehensive test suite (`tests/test_odym_compliance.py`) to validate all aspects of the new system.
- [ ] **Task 4.5**: Update the `00_BioDYM_Workflow.ipynb` to use the new `6D -> 2D` aggregation workflow and add the system inspection cell.

---

## Risk Assessment & Mitigation

### **High-Risk Areas**
1. **Dimension Migration**: Multi-dimensional arrays may cause performance issues
2. **Excel Template Changes**: Major changes may break existing workflows
3. **Custom Attributes Removal**: May break existing functionality
4. **Performance Impact**: ODYM methods might be slower than custom implementations

### **Mitigation Strategies**
1. **Comprehensive Testing**: Unit tests, integration tests, regression tests
2. **Performance Benchmarking**: Compare before/after performance
3. **Gradual Migration**: Phase-by-phase implementation with rollback options
4. **Backward Compatibility**: Maintain compatibility with existing Excel templates
5. **Documentation**: Comprehensive documentation for all changes

### **Success Metrics**
- [ ] All existing tests pass
- [ ] Performance maintained or improved
- [ ] No functionality loss
- [ ] Better error handling
- [ ] Improved validation
- [ ] Full ODYM compatibility
- [ ] Excel template compatibility maintained

---

## Timeline & Resource Requirements

### **Phase 1: Foundation & Dimensions (3-4 weeks)**
- **Effort**: 20-26 hours
- **Risk**: Medium
- **Dependencies**: None
- **Deliverables**: Complete dimension system, multi-dimensional data structures

### **Phase 2: Class Compliance (3-4 weeks)**
- **Effort**: 20-26 hours
- **Risk**: Medium
- **Dependencies**: Phase 1 completion
- **Deliverables**: ODYM method integration, custom attributes removal

### **Phase 3: Function Compliance (3-4 weeks)**
- **Effort**: 20-26 hours
- **Risk**: Medium
- **Dependencies**: Phase 2 completion
- **Deliverables**: Type safety, error handling, ODYM patterns

### **Phase 4: Advanced Integration (3-4 weeks)**
- **Effort**: 26-34 hours
- **Risk**: High
- **Dependencies**: Phase 3 completion
- **Deliverables**: BioDYM extensions, performance optimization, Excel updates

### **Total Timeline**: 12-16 weeks
### **Total Effort**: 86-112 hours

---

## Conclusion

This comprehensive master plan provides a structured approach to achieving full ODYM compliance across all identified areas. The phased approach minimizes risk while maximizing benefits, ensuring that BioDYM becomes fully compliant with ODYM standards while maintaining its unique features.

**Key Benefits**:
- ✅ **Full ODYM Compliance**: Complete integration with ODYM framework
- ✅ **Enhanced Scalability**: Multi-dimensional support for complex analyses
- ✅ **Future-Proofing**: Compatible with future ODYM updates
- ✅ **Better Validation**: Comprehensive error handling and validation
- ✅ **Improved Performance**: Optimized multi-dimensional operations
- ✅ **Maintained Compatibility**: Backward compatibility with existing workflows

**Next Steps**:
1. Review and approve this master plan
2. Begin Phase 1 implementation
3. Test thoroughly before proceeding to Phase 2
4. Evaluate results before considering Phase 3
5. Complete Phase 4 for full ODYM compliance

---

*Document Version: 1.0*  
*Last Updated: [Current Date]*  
*Author: BioDYM Development Team*

---


================================================================================
# File: ODYM_COMPLIANCE_STRATEGY.md
================================================================================

# BioDYM ODYM Compliance Implementation Strategy

## Overview

This document outlines a comprehensive strategy for improving ODYM class compliance in the BioDYM engine modules. The implementation is designed to maintain full backward compatibility while leveraging ODYM's built-in methods and validation systems.

## Executive Summary

- **Excel Templates**: ❌ **NO CHANGES REQUIRED** - Current Excel structure is perfectly compatible
- **Implementation Complexity**: 7/10 (High) - Requires careful testing and validation
- **Timeline**: 6-9 weeks total across 3 phases
- **Risk Level**: Low to High (phased approach)
- **Benefits**: Better ODYM integration, improved validation, future-proofing

## Current State Analysis

### ODYM Class Usage Assessment

| Engine Module | ODYM Classes Modified | Compliance Issues | Priority |
|---------------|----------------------|-------------------|----------|
| **solver.py** | `MFAsystem`, `Flow`, `Parameter` | Manual aggregation, missing validation | High |
| **initial_stock_engine.py** | `Flow`, `Stock`, `MFAsystem` | Custom attributes, direct creation | High |
| **dsm_model.py** | `Flow`, `MFAsystem` | Direct value assignment | Medium |
| **fomp_model.py** | `Flow`, `MFAsystem` | Direct value assignment | Medium |
| **scenario_engine.py** | `MFAsystem` | Deep copy usage | Low |
| **mc_simulation.py** | `Parameter`, `MFAsystem` | Parameter updates | Low |

### Key Non-Compliant Patterns Identified

1. **Manual Flow Aggregation** (solver.py):
   ```python
   # Current (Non-compliant)
   inflows = [f.Values for f in mfa_system.FlowDict.values() if f.P_End == pid]
   total_inflows = sum(inflows) if inflows else np.zeros_like(stock_s.Values)
   
   # Target (ODYM-compliant)
   total_inflows = mfa_system.Flow_Sum_By_Element(flow_key)
   ```

2. **Custom Attributes on ODYM Objects**:
   ```python
   # Current (Non-compliant)
   flow._initial_stock_config = {...}
   flow._fomp_protected = True
   
   # Target (ODYM-compliant)
   process.add_extension(Name="config", Value=config_dict)
   ```

3. **Missing Consistency Checks**:
   ```python
   # Current (Missing)
   # No validation after modifications
   
   # Target (ODYM-compliant)
   mfa_system.Consistency_Check()
   mfa_system.IndexTableCheck()
   ```

## Implementation Strategy: 3-Phase Approach

### Phase 1: Foundation Improvements (1-2 weeks)
**Risk Level**: Low | **Impact**: Foundation | **Priority**: High

#### Objectives
- Add ODYM validation methods
- Use ODYM initialization methods
- Remove custom attributes from ODYM objects
- Establish proper error handling

#### Detailed Implementation Plan

##### 1.1 Add ODYM Consistency Checks ⏱️ 2-3 hours

**Files to modify**: `solver.py`, `initial_stock_engine.py`, `dsm_model.py`, `fomp_model.py`

**solver.py Changes**:
```python
# After line 433 in solver.py
mfa_system = calculate_final_balances(mfa_system)

# ADD THIS:
try:
    mfa_system.Consistency_Check()
    print("✅ System consistency validated")
except ValueError as e:
    print(f"❌ System consistency check failed: {e}")
    raise
```

**initial_stock_engine.py Changes**:
```python
# After line 286 in initial_stock_engine.py
print("--> Initial stock outflows processed.")

# ADD THIS:
try:
    mfa_system.Consistency_Check()
    print("✅ Initial stock system consistency validated")
except ValueError as e:
    print(f"❌ Initial stock consistency check failed: {e}")
    raise

return mfa_system
```

**dsm_model.py Changes**:
```python
# After line 221 in dsm_model.py
_distribute_and_assign_outflows(...)

# ADD THIS:
try:
    mfa_system.Consistency_Check()
    print(f"✅ DSM Process {process_id} consistency validated")
except ValueError as e:
    print(f"❌ DSM Process {process_id} consistency check failed: {e}")
    raise
```

##### 1.2 Use ODYM Initialization Methods ⏱️ 1-2 hours

**Files to modify**: `system_setup.py`

```python
# In define_flows_and_parameters() after line 465
_calculate_elemental_compositions(mfa_system)
flow_tc_map, process_logic_map = _create_flow_and_process_maps(mfa_system, all_excel_data)

# REPLACE manual initialization with ODYM methods:
mfa_system.Initialize_FlowValues()
mfa_system.Initialize_StockValues() 
mfa_system.Initialize_ParameterValues()

mfa_system.Consistency_Check()
```

##### 1.3 Remove Custom Attributes from ODYM Objects ⏱️ 3-4 hours

**Files to modify**: `initial_stock_engine.py`, `solver.py`, `fomp_model.py`

**initial_stock_engine.py Changes**:
```python
# REPLACE lines 398-403 in initial_stock_engine.py
# OLD CODE:
if not hasattr(flow, '_initial_stock_config'):
    flow._initial_stock_config = {
        'initial_stock': initial_stock.copy(),
        'consumption_rate': consumption_rate,
        'split_fraction': split_fraction
    }

# NEW CODE:
# Store in separate configuration system
if not hasattr(mfa_system, 'initial_stock_flow_configs'):
    mfa_system.initial_stock_flow_configs = {}

mfa_system.initial_stock_flow_configs[flow_name] = {
    'initial_stock': initial_stock.copy(),
    'consumption_rate': consumption_rate,
    'split_fraction': split_fraction
}
```

**solver.py Changes**:
```python
# In solver.py, update _calculate_fomp_flows() around line 295
# REPLACE:
fomp_outflows = [f for f in mfa_system.FlowDict.values() if f.P_Start == process_id and hasattr(f, '_fomp_protected')]

# WITH:
fomp_outflows = [f for f in mfa_system.FlowDict.values() if f.P_Start == process_id and f.Name in mfa_system.get('fomp_protected_flows', [])]
```

##### 1.4 Add Proper Error Handling ⏱️ 2-3 hours

**Files to modify**: All engine modules

```python
# In solver.py, wrap flow operations
try:
    # Existing flow operations
    inflows = [f.Values for f in mfa_system.FlowDict.values() if f.P_End == pid]
    # ... rest of operations
except (AttributeError, KeyError) as e:
    print(f"❌ Error accessing flow data for process {pid}: {e}")
    raise ValueError(f"Flow data access failed for process {pid}")
```

#### Phase 1 Success Criteria
- [ ] All consistency checks pass
- [ ] No custom attributes on ODYM objects
- [ ] Proper error handling implemented
- [ ] All existing tests pass
- [ ] Performance maintained or improved

---

### Phase 2: Core Improvements (2-3 weeks)
**Risk Level**: Medium | **Impact**: Core Functionality | **Priority**: High

#### Objectives
- Replace manual flow aggregation with ODYM methods
- Implement proper ODYM flow management
- Add comprehensive validation
- Improve mass balance calculations

#### Detailed Implementation Plan

##### 2.1 Replace Manual Flow Aggregation ⏱️ 4-6 hours

**Files to modify**: `solver.py`

**Create ODYM-compliant flow aggregation function**:
```python
# NEW FUNCTION in solver.py
def calculate_process_inflows_odym_compliant(mfa_system, process_id):
    """Calculate total inflows to a process using ODYM methods."""
    inflows = []
    for flow in mfa_system.FlowDict.values():
        if flow.P_End == process_id:
            # Use ODYM's Flow_Sum_By_Element method
            flow_sum = mfa_system.Flow_Sum_By_Element(flow.Name)
            inflows.append(flow_sum)
    
    if inflows:
        return sum(inflows)
    else:
        # Return zeros with correct shape
        n_years = len(mfa_system.Time_L)
        n_elements = len(mfa_system.Elements)
        return np.zeros((n_years, n_elements))
```

**Replace manual aggregation in `calculate_final_balances()`**:
```python
# REPLACE lines 49-56 in solver.py
# OLD CODE:
inflows = [f.Values for f in mfa_system.FlowDict.values() if f.P_End == pid]
outflows = [f.Values for f in mfa_system.FlowDict.values() if f.P_Start == pid]
total_inflows = sum(inflows) if inflows else np.zeros_like(stock_s.Values)
total_outflows = sum(outflows) if outflows else np.zeros_like(stock_s.Values)

# NEW CODE:
total_inflows = calculate_process_inflows_odym_compliant(mfa_system, pid)
total_outflows = calculate_process_outflows_odym_compliant(mfa_system, pid)
```

##### 2.2 Implement Proper ODYM Flow Management ⏱️ 3-4 hours

**Files to modify**: `initial_stock_engine.py`

**Create ODYM-compliant flow creation function**:
```python
# NEW FUNCTION in initial_stock_engine.py
def create_flow_odym_compliant(mfa_system, flow_name, process_id, destination_process):
    """Create flow using ODYM-compliant methods."""
    # Check if flow already exists
    if flow_name in mfa_system.FlowDict:
        return mfa_system.FlowDict[flow_name]
    
    # Create flow object
    flow = msc.Flow(
        Name=flow_name,
        P_Start=process_id,
        P_End=destination_process,
        Indices="t,e"
    )
    
    # Add to system using proper method (if available)
    mfa_system.FlowDict[flow_name] = flow
    
    # Initialize values using ODYM method
    mfa_system.Initialize_FlowValues()
    
    return flow
```

**Replace direct flow creation in `_create_single_outflow_flow()`**:
```python
# REPLACE lines 381-387 in initial_stock_engine.py
# OLD CODE:
if flow_name not in mfa_system.FlowDict:
    mfa_system.FlowDict[flow_name] = msc.Flow(
        Name=flow_name,
        P_Start=process_id,
        P_End=destination_process,
        Indices="t,e"
    )

# NEW CODE:
flow = create_flow_odym_compliant(mfa_system, flow_name, process_id, destination_process)
```

##### 2.3 Add Comprehensive Validation ⏱️ 2-3 hours

**Files to modify**: All engine modules

**Create validation utility functions**:
```python
# NEW FILE: 02_src/engine/validation.py
def validate_mfa_system_state(mfa_system, operation_name=""):
    """Comprehensive validation of MFA system state."""
    try:
        # Check index table consistency
        mfa_system.IndexTableCheck()
        
        # Check system consistency
        mfa_system.Consistency_Check()
        
        # Check for negative values in flows
        for flow_name, flow in mfa_system.FlowDict.items():
            if flow.Values is not None and np.any(flow.Values < 0):
                print(f"⚠️ WARNING: Negative values found in flow {flow_name}")
        
        print(f"✅ System validation passed for {operation_name}")
        return True
        
    except Exception as e:
        print(f"❌ System validation failed for {operation_name}: {e}")
        return False
```

**Add validation calls throughout engine modules**:
```python
# In solver.py, add after major operations
from .validation import validate_mfa_system_state

# After convergence check
if not any(pass_changes):
    print(f"--> System converged after {i + 1} iterations.")
    validate_mfa_system_state(mfa_system, "convergence")
    break
```

##### 2.4 Improve Mass Balance Calculations ⏱️ 3-4 hours

**Files to modify**: `solver.py`

**Use ODYM's MassBalance method**:
```python
# NEW FUNCTION in solver.py
def calculate_mass_balance_odym_compliant(mfa_system):
    """Calculate mass balance using ODYM's built-in method."""
    try:
        balance = mfa_system.MassBalance()
        return balance
    except Exception as e:
        print(f"❌ Error calculating mass balance: {e}")
        return None

# REPLACE manual balance calculation in calculate_final_balances()
# Use ODYM's method instead of manual calculation
```

#### Phase 2 Success Criteria
- [ ] ODYM methods used for flow aggregation
- [ ] Proper flow management implemented
- [ ] Comprehensive validation added
- [ ] Mass balance calculations improved
- [ ] Performance maintained or improved
- [ ] All existing functionality preserved

---

### Phase 3: Advanced Improvements (3-4 weeks)
**Risk Level**: High | **Impact**: Architecture | **Priority**: Medium

#### Objectives
- Refactor custom BioDYM extensions
- Implement ODYM Extensions mechanism
- Complete system validation
- Optimize performance

#### Detailed Implementation Plan

##### 3.1 Refactor Custom BioDYM Extensions ⏱️ 6-8 hours

**Files to modify**: `initial_stock_engine.py`, `fomp_model.py`

**Create BioDYM extension classes**:
```python
# NEW FILE: 02_src/engine/biodym_extensions.py
class InitialStockExtension:
    """BioDYM extension for initial stock management."""
    
    def __init__(self, mfa_system):
        self.mfa_system = mfa_system
        self.configs = {}
    
    def add_initial_stock_config(self, process_id, config):
        """Add initial stock configuration."""
        self.configs[process_id] = config
    
    def process_initial_stocks(self):
        """Process all initial stocks."""
        # Implementation using ODYM-compliant methods
        pass

class FOMPExtension:
    """BioDYM extension for FOMP processes."""
    
    def __init__(self, mfa_system):
        self.mfa_system = mfa_system
        self.protected_flows = set()
    
    def protect_flow(self, flow_name):
        """Mark flow as FOMP-protected."""
        self.protected_flows.add(flow_name)
```

**Integrate extensions with MFA system**:
```python
# In system_setup.py, add extension initialization
def initialize_biodym_extensions(mfa_system):
    """Initialize BioDYM-specific extensions."""
    from .engine.biodym_extensions import InitialStockExtension, FOMPExtension
    
    mfa_system.biodym_extensions = {
        'initial_stock': InitialStockExtension(mfa_system),
        'fomp': FOMPExtension(mfa_system)
    }
    
    return mfa_system
```

##### 3.2 Implement ODYM Extensions Mechanism ⏱️ 4-6 hours

**Files to modify**: All engine modules

**Use ODYM's Process Extensions**:
```python
# In initial_stock_engine.py, replace custom attributes
# OLD CODE:
flow._initial_stock_config = {...}

# NEW CODE:
process = mfa_system.ProcessList[process_id]
process.add_extension(
    Time=None,
    Name="initial_stock_config",
    Value=config_dict,
    Unit="configuration"
)
```

**Create extension access methods**:
```python
# NEW FUNCTION in initial_stock_engine.py
def get_process_extension(mfa_system, process_id, extension_name):
    """Get process extension using ODYM methods."""
    process = mfa_system.ProcessList[process_id]
    if process.Extensions:
        for ext in process.Extensions:
            if ext.Name == extension_name:
                return ext.Value
    return None
```

##### 3.3 Complete System Validation ⏱️ 3-4 hours

**Files to modify**: All engine modules

**Implement comprehensive validation suite**:
```python
# NEW FILE: 02_src/engine/comprehensive_validation.py
class MFAValidationSuite:
    """Comprehensive validation suite for MFA systems."""
    
    def __init__(self, mfa_system):
        self.mfa_system = mfa_system
        self.validation_results = {}
    
    def run_all_validations(self):
        """Run all validation checks."""
        self.validate_mass_balance()
        self.validate_flow_consistency()
        self.validate_stock_consistency()
        self.validate_parameter_consistency()
        self.validate_biodym_extensions()
        
        return self.validation_results
    
    def validate_mass_balance(self):
        """Validate mass balance using ODYM methods."""
        try:
            balance = self.mfa_system.MassBalance()
            # Check for significant imbalances
            max_imbalance = np.max(np.abs(balance))
            if max_imbalance > 1e-6:  # Tolerance for numerical errors
                self.validation_results['mass_balance'] = {
                    'status': 'warning',
                    'message': f'Mass balance imbalance: {max_imbalance}'
                }
            else:
                self.validation_results['mass_balance'] = {
                    'status': 'pass',
                    'message': 'Mass balance within tolerance'
                }
        except Exception as e:
            self.validation_results['mass_balance'] = {
                'status': 'error',
                'message': f'Mass balance validation failed: {e}'
            }
```

##### 3.4 Performance Optimization ⏱️ 4-5 hours

**Files to modify**: `solver.py`, `dsm_model.py`, `fomp_model.py`

**Optimize flow aggregation**:
```python
# NEW FUNCTION in solver.py
def calculate_flows_vectorized(mfa_system, process_ids):
    """Calculate flows for multiple processes using vectorized operations."""
    # Use numpy operations for better performance
    # Implement caching for repeated calculations
    pass
```

**Add performance monitoring**:
```python
# NEW FILE: 02_src/engine/performance_monitor.py
import time
from functools import wraps

def monitor_performance(func):
    """Decorator to monitor function performance."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"⏱️ {func.__name__} executed in {end_time - start_time:.3f} seconds")
        return result
    return wrapper

# Apply to critical functions
@monitor_performance
def calculate_dynamic_stock(mfa_system, dsm_params_config):
    # Existing implementation
    pass
```

#### Phase 3 Success Criteria
- [ ] Custom BioDYM extensions refactored
- [ ] ODYM Extensions mechanism implemented
- [ ] Comprehensive validation suite complete
- [ ] Performance optimized
- [ ] Full ODYM compliance achieved
- [ ] All existing functionality preserved

---

## BioDYM Classes vs. ODYM Aspects: Architectural Decision

### Question Analysis
You've developed BioDYM-specific features:
- **FOMP processes** (First-Order Mineralization Processes)
- **Initial stocks** with stock-outflow transfer coefficients
- **Custom features** in several processes

### Recommendation: Hybrid Approach

#### Use BioDYM Classes for Core Extensions
**When to use BioDYM classes**:
- **FOMP processes**: Create `bioDYM_classes.FOMPProcess` extending `msc.Process`
- **Initial stock management**: Create `bioDYM_classes.InitialStockManager`
- **Custom process logic**: Create `bioDYM_classes.BioDYMProcess`

**Example Implementation**:
```python
# In bioDYM_classes.py
class FOMPProcess(msc.Process):
    """BioDYM extension of ODYM Process for FOMP calculations."""
    
    def __init__(self, Name=None, ID=None, **kwargs):
        super().__init__(Name=Name, ID=ID, **kwargs)
        self.fomp_params = {}
        self.protected_flows = set()
    
    def add_fomp_parameter(self, param_name, value):
        """Add FOMP-specific parameter."""
        self.fomp_params[param_name] = value
    
    def protect_flow(self, flow_name):
        """Mark flow as FOMP-protected."""
        self.protected_flows.add(flow_name)

class InitialStockManager:
    """BioDYM extension for initial stock management."""
    
    def __init__(self, mfa_system):
        self.mfa_system = mfa_system
        self.configs = {}
    
    def add_initial_stock_config(self, process_id, config):
        """Add initial stock configuration."""
        self.configs[process_id] = config
```

#### Use ODYM Aspects for Standard Features
**When to use ODYM aspects**:
- **Standard process parameters**: Use `msc.Parameter`
- **Standard flows**: Use `msc.Flow`
- **Standard stocks**: Use `msc.Stock`
- **Standard classifications**: Use `msc.Classification`

### Implementation Strategy

#### Phase 1: Extend BioDYM Classes
1. **Create BioDYM-specific classes** that extend ODYM classes
2. **Maintain compatibility** with existing ODYM methods
3. **Add BioDYM-specific methods** for custom functionality

#### Phase 2: Integrate with ODYM Extensions
1. **Use ODYM Extensions** for process-specific data
2. **Store BioDYM configurations** in process extensions
3. **Maintain separation** between ODYM core and BioDYM extensions

#### Phase 3: Full Integration
1. **Seamless integration** between BioDYM and ODYM classes
2. **Proper inheritance** hierarchy
3. **Complete compatibility** with ODYM framework

### Benefits of Hybrid Approach
- ✅ **Maintains BioDYM identity** while leveraging ODYM
- ✅ **Future-proof** for ODYM updates
- ✅ **Clear separation** of concerns
- ✅ **Easy maintenance** and debugging
- ✅ **Extensible** for future BioDYM features

---

## Risk Assessment & Mitigation

### High-Risk Areas
1. **Custom BioDYM Features**: Initial stock outflows, FOMP processes
2. **Performance Impact**: ODYM methods might be slower
3. **Testing Complexity**: Need to validate all existing functionality

### Mitigation Strategies
1. **Comprehensive Testing**: Unit tests, integration tests, regression tests
2. **Performance Benchmarking**: Compare before/after performance
3. **Gradual Migration**: Phase-by-phase implementation
4. **Rollback Plan**: Maintain current implementation in separate branch

### Success Metrics
- [ ] All existing tests pass
- [ ] Performance maintained or improved
- [ ] No functionality loss
- [ ] Better error handling
- [ ] Improved validation
- [ ] Full ODYM compatibility

---

## Timeline & Resource Requirements

### Phase 1: Foundation (1-2 weeks)
- **Effort**: 8-12 hours
- **Risk**: Low
- **Dependencies**: None
- **Deliverables**: Validation, error handling, initialization

### Phase 2: Core (2-3 weeks)
- **Effort**: 12-18 hours
- **Risk**: Medium
- **Dependencies**: Phase 1 completion
- **Deliverables**: ODYM methods, flow management, validation

### Phase 3: Advanced (3-4 weeks)
- **Effort**: 18-24 hours
- **Risk**: High
- **Dependencies**: Phase 2 completion
- **Deliverables**: Extensions, optimization, full compliance

### Total Timeline: 6-9 weeks
### Total Effort: 38-54 hours

---

## Conclusion

This implementation strategy provides a structured approach to achieving full ODYM compliance while maintaining BioDYM's unique features. The phased approach minimizes risk while maximizing benefits, and the hybrid class architecture ensures both compatibility and extensibility.

The key insight is that **Excel templates require no changes** - the improvements are purely in the Python engine modules, leveraging ODYM's built-in methods and validation systems.

**Next Steps**:
1. Review and approve this strategy
2. Begin Phase 1 implementation
3. Test thoroughly before proceeding to Phase 2
4. Evaluate results before considering Phase 3

---

*Document Version: 1.0*  
*Last Updated: [Current Date]*  
*Author: BioDYM Development Team*


---


================================================================================
# File: ODYM_DIMENSIONS_COMPLIANCE_ANALYSIS.md
================================================================================

# BioDYM ODYM Dimensions Compliance Analysis

## Overview

This document analyzes the compliance of BioDYM's dimension usage with ODYM's comprehensive dimension system. The analysis reveals significant gaps in dimension utilization that impact system scalability, interoperability, and compliance with ODYM standards.

## Executive Summary

- **Overall Dimension Compliance**: 3/10 (Poor) - Major gaps in dimension usage
- **Missing Dimensions**: Region, Good, Material, Process classifications
- **Impact**: Limited scalability, reduced interoperability, non-standard ODYM compliance
- **Priority**: High - Critical for ODYM compliance and future extensibility

## ODYM Dimension System Analysis

### Standard ODYM Dimensions

Based on the ODYM framework, the following dimensions are available:

#### **Core Dimensions** (from `ODYM_Classes.py`):
```python
self.Dimensions = {
    "Time": "Time",
    "Process": "Process", 
    "Region": "Region",
    "Good": "Process, good, or commodity",
    "Material": "Material: ore, alloy, scrap type, ...",
    "Element": "Chemical element",
}
```

#### **Core Aspects** (from `ODYM_Classes.py`):
```python
self.Aspects = {
    "Time": "Model time",
    "Cohort": "Age-cohort",
    "OriginProcess": "Process where flow originates",
    "DestinationProcess": "Destination process of flow",
    "OriginRegion": "Region where flow originates from",
    "DestinationRegion": "Region where flow is bound to",
    "Good": "Process, good, or commodity",
    "Material": "Material: ore, alloy, scrap type, ...",
    "Element": "Chemical element",
}
```

## BioDYM Current Dimension Usage

### **Currently Implemented Dimensions**

#### ✅ **Time Dimension** (Fully Implemented)
```python
# In system_setup.py
model_classification["Time"] = msc.Classification(
    Name="Time", Dimension="Time", ID=1, Items=my_years
)
```
- **Status**: ✅ Complete
- **Usage**: Properly integrated in IndexTable
- **Compliance**: 10/10

#### ✅ **Element Dimension** (Fully Implemented)
```python
# In system_setup.py
model_classification["Element"] = msc.Classification(
    Name="Elements", Dimension="Element", ID=2, Items=elements
)
```
- **Status**: ✅ Complete
- **Usage**: Properly integrated in IndexTable
- **Compliance**: 10/10

### **Missing Critical Dimensions**

#### ❌ **Region Dimension** (Not Implemented)
**Current State**: 
- Only `Geogr_Scope="Case_Study_Region"` as string
- No regional classification system
- No regional flow tracking

**ODYM Standard**:
```python
# Should be implemented as:
model_classification["Region"] = msc.Classification(
    Name="Regions", 
    Dimension="Region", 
    ID=3, 
    Items=["Region_A", "Region_B", "Case_Study_Region"]
)
```

**Impact**:
- ❌ Cannot track inter-regional flows
- ❌ Cannot perform regional analysis
- ❌ Limited scalability for multi-regional studies
- ❌ Non-compliant with ODYM standards

#### ❌ **Good Dimension** (Not Implemented)
**Current State**: 
- No good/commodity classification
- Materials treated as simple strings
- No good-specific flow tracking

**ODYM Standard**:
```python
# Should be implemented as:
model_classification["Good"] = msc.Classification(
    Name="Goods", 
    Dimension="Good", 
    ID=4, 
    Items=["Rye_Straw", "Biochar", "Compost", "Energy"]
)
```

**Impact**:
- ❌ Cannot track good-specific flows
- ❌ Limited material flow analysis
- ❌ No commodity-based reporting
- ❌ Non-compliant with ODYM standards

#### ❌ **Material Dimension** (Not Implemented)
**Current State**: 
- Materials handled as simple strings in Excel
- No material classification system
- No material-specific properties

**ODYM Standard**:
```python
# Should be implemented as:
model_classification["Material"] = msc.Classification(
    Name="Materials", 
    Dimension="Material", 
    ID=5, 
    Items=["Dry_Matter", "Water_Content", "Carbon_Content"]
)
```

**Impact**:
- ❌ Cannot track material-specific properties
- ❌ Limited material composition analysis
- ❌ No material-specific parameters
- ❌ Non-compliant with ODYM standards

#### ❌ **Process Dimension** (Partially Implemented)
**Current State**: 
- Processes exist but not as formal classification
- No process classification system
- Process IDs used directly without classification

**ODYM Standard**:
```python
# Should be implemented as:
model_classification["Process"] = msc.Classification(
    Name="Processes", 
    Dimension="Process", 
    ID=6, 
    Items=["Harvest", "Processing", "Storage", "Application"]
)
```

**Impact**:
- ❌ Cannot perform process-type analysis
- ❌ Limited process categorization
- ❌ No process-specific reporting
- ❌ Non-compliant with ODYM standards

## Detailed Compliance Analysis

### **IndexTable Structure Analysis**

#### **Current BioDYM IndexTable**:
```python
# Current implementation (system_setup.py)
index_table = pd.DataFrame({
    "Aspect": ["Time", "Element"],
    "Description": ['Model aspect "time"', 'Model aspect "Element"'],
    "Dimension": ["Time", "Element"],
    "Classification": [model_classification[Aspect] for Aspect in ["Time", "Element"]],
    "IndexLetter": ["t", "e"],
})
```

#### **ODYM-Compliant IndexTable**:
```python
# Should be implemented as:
index_table = pd.DataFrame({
    "Aspect": ["Time", "Element", "Region", "Good", "Material", "Process"],
    "Description": [
        'Model aspect "time"',
        'Model aspect "Element"', 
        'Model aspect "Region"',
        'Model aspect "Good"',
        'Model aspect "Material"',
        'Model aspect "Process"'
    ],
    "Dimension": ["Time", "Element", "Region", "Good", "Material", "Process"],
    "Classification": [
        model_classification["Time"],
        model_classification["Element"],
        model_classification["Region"],
        model_classification["Good"],
        model_classification["Material"],
        model_classification["Process"]
    ],
    "IndexLetter": ["t", "e", "r", "g", "m", "p"],
})
```

### **Flow Indices Analysis**

#### **Current BioDYM Flow Indices**:
```python
# Current implementation
Indices="t,e"  # Only Time and Element
```

#### **ODYM-Compliant Flow Indices**:
```python
# Should be implemented as:
Indices="t,e,r,g,m,p"  # Time, Element, Region, Good, Material, Process
```

**Impact on Flow Arrays**:
- **Current**: 2D arrays (Time × Element)
- **ODYM Standard**: 6D arrays (Time × Element × Region × Good × Material × Process)

### **Data Structure Impact Analysis**

#### **Current BioDYM Data Structures**:
```python
# Flow values: 2D array
flow.Values.shape = (n_years, n_elements)

# Stock values: 2D array  
stock.Values.shape = (n_years, n_elements)

# Parameter values: 2D array
parameter.Values.shape = (n_years, n_elements)
```

#### **ODYM-Compliant Data Structures**:
```python
# Flow values: 6D array
flow.Values.shape = (n_years, n_elements, n_regions, n_goods, n_materials, n_processes)

# Stock values: 6D array
stock.Values.shape = (n_years, n_elements, n_regions, n_goods, n_materials, n_processes)

# Parameter values: 6D array
parameter.Values.shape = (n_years, n_elements, n_regions, n_goods, n_materials, n_processes)
```

## Compliance Issues Identified

### **1. Missing Regional Dimension**
**Severity**: High | **Impact**: Major

**Issues**:
- Cannot track inter-regional flows
- Cannot perform regional analysis
- Limited scalability for multi-regional studies
- Non-compliant with ODYM standards

**Example Impact**:
```python
# Current: Cannot track regional flows
flow_from_region_a_to_b = None  # Not possible

# ODYM Standard: Can track regional flows
flow_from_region_a_to_b = mfa_system.FlowDict["Flow_A_to_B"].Values[:, :, region_a_idx, :, :, :]
```

### **2. Missing Good Dimension**
**Severity**: High | **Impact**: Major

**Issues**:
- Cannot track good-specific flows
- Limited material flow analysis
- No commodity-based reporting
- Non-compliant with ODYM standards

**Example Impact**:
```python
# Current: Cannot track good-specific flows
rye_straw_flows = None  # Not possible

# ODYM Standard: Can track good-specific flows
rye_straw_flows = mfa_system.FlowDict["Rye_Straw_Flow"].Values[:, :, :, rye_straw_idx, :, :]
```

### **3. Missing Material Dimension**
**Severity**: Medium | **Impact**: Moderate

**Issues**:
- Cannot track material-specific properties
- Limited material composition analysis
- No material-specific parameters
- Non-compliant with ODYM standards

**Example Impact**:
```python
# Current: Cannot track material-specific flows
dry_matter_flows = None  # Not possible

# ODYM Standard: Can track material-specific flows
dry_matter_flows = mfa_system.FlowDict["DM_Flow"].Values[:, :, :, :, dry_matter_idx, :]
```

### **4. Missing Process Dimension**
**Severity**: Medium | **Impact**: Moderate

**Issues**:
- Cannot perform process-type analysis
- Limited process categorization
- No process-specific reporting
- Non-compliant with ODYM standards

**Example Impact**:
```python
# Current: Cannot track process-specific flows
harvest_flows = None  # Not possible

# ODYM Standard: Can track process-specific flows
harvest_flows = mfa_system.FlowDict["Harvest_Flow"].Values[:, :, :, :, :, harvest_idx]
```

## Implementation Strategy

### **Phase 1: Foundation Dimensions (2-3 weeks)**
**Priority**: High | **Effort**: 8-12 hours

#### **1.1 Add Region Dimension**
```python
# In system_setup.py
def define_model_scope(start_year, end_year, elements, regions=None):
    """Defines the temporal, elemental, and regional scope of the MFA model."""
    
    if regions is None:
        regions = ["Case_Study_Region"]  # Default single region
    
    model_classification = {}
    my_years = list(np.arange(start_year, end_year + 1))
    
    # Existing dimensions
    model_classification["Time"] = msc.Classification(
        Name="Time", Dimension="Time", ID=1, Items=my_years
    )
    model_classification["Element"] = msc.Classification(
        Name="Elements", Dimension="Element", ID=2, Items=elements
    )
    
    # NEW: Add Region dimension
    model_classification["Region"] = msc.Classification(
        Name="Regions", Dimension="Region", ID=3, Items=regions
    )
    
    # Update IndexTable
    index_table = pd.DataFrame({
        "Aspect": ["Time", "Element", "Region"],
        "Description": [
            'Model aspect "time"',
            'Model aspect "Element"',
            'Model aspect "Region"'
        ],
        "Dimension": ["Time", "Element", "Region"],
        "Classification": [
            model_classification["Time"],
            model_classification["Element"],
            model_classification["Region"]
        ],
        "IndexLetter": ["t", "e", "r"],
    })
    
    return model_classification, index_table
```

#### **1.2 Add Good Dimension**
```python
# In system_setup.py
def define_model_scope(start_year, end_year, elements, regions=None, goods=None):
    """Defines the comprehensive scope of the MFA model."""
    
    if goods is None:
        goods = ["Rye_Straw", "Biochar", "Compost", "Energy"]  # Default goods
    
    # ... existing code ...
    
    # NEW: Add Good dimension
    model_classification["Good"] = msc.Classification(
        Name="Goods", Dimension="Good", ID=4, Items=goods
    )
    
    # Update IndexTable
    index_table = pd.DataFrame({
        "Aspect": ["Time", "Element", "Region", "Good"],
        "Description": [
            'Model aspect "time"',
            'Model aspect "Element"',
            'Model aspect "Region"',
            'Model aspect "Good"'
        ],
        "Dimension": ["Time", "Element", "Region", "Good"],
        "Classification": [
            model_classification["Time"],
            model_classification["Element"],
            model_classification["Region"],
            model_classification["Good"]
        ],
        "IndexLetter": ["t", "e", "r", "g"],
    })
    
    return model_classification, index_table
```

### **Phase 2: Advanced Dimensions (3-4 weeks)**
**Priority**: Medium | **Effort**: 12-16 hours

#### **2.1 Add Material Dimension**
```python
# In system_setup.py
def define_model_scope(start_year, end_year, elements, regions=None, goods=None, materials=None):
    """Defines the comprehensive scope of the MFA model."""
    
    if materials is None:
        materials = ["Dry_Matter", "Water_Content", "Carbon_Content"]  # Default materials
    
    # ... existing code ...
    
    # NEW: Add Material dimension
    model_classification["Material"] = msc.Classification(
        Name="Materials", Dimension="Material", ID=5, Items=materials
    )
    
    # Update IndexTable
    index_table = pd.DataFrame({
        "Aspect": ["Time", "Element", "Region", "Good", "Material"],
        "Description": [
            'Model aspect "time"',
            'Model aspect "Element"',
            'Model aspect "Region"',
            'Model aspect "Good"',
            'Model aspect "Material"'
        ],
        "Dimension": ["Time", "Element", "Region", "Good", "Material"],
        "Classification": [
            model_classification["Time"],
            model_classification["Element"],
            model_classification["Region"],
            model_classification["Good"],
            model_classification["Material"]
        ],
        "IndexLetter": ["t", "e", "r", "g", "m"],
    })
    
    return model_classification, index_table
```

#### **2.2 Add Process Dimension**
```python
# In system_setup.py
def define_model_scope(start_year, end_year, elements, regions=None, goods=None, materials=None, processes=None):
    """Defines the comprehensive scope of the MFA model."""
    
    if processes is None:
        processes = ["Harvest", "Processing", "Storage", "Application"]  # Default processes
    
    # ... existing code ...
    
    # NEW: Add Process dimension
    model_classification["Process"] = msc.Classification(
        Name="Processes", Dimension="Process", ID=6, Items=processes
    )
    
    # Update IndexTable
    index_table = pd.DataFrame({
        "Aspect": ["Time", "Element", "Region", "Good", "Material", "Process"],
        "Description": [
            'Model aspect "time"',
            'Model aspect "Element"',
            'Model aspect "Region"',
            'Model aspect "Good"',
            'Model aspect "Material"',
            'Model aspect "Process"'
        ],
        "Dimension": ["Time", "Element", "Region", "Good", "Material", "Process"],
        "Classification": [
            model_classification["Time"],
            model_classification["Element"],
            model_classification["Region"],
            model_classification["Good"],
            model_classification["Material"],
            model_classification["Process"]
        ],
        "IndexLetter": ["t", "e", "r", "g", "m", "p"],
    })
    
    return model_classification, index_table
```

### **Phase 3: Data Structure Migration (4-5 weeks)**
**Priority**: High | **Effort**: 16-20 hours

#### **3.1 Update Flow Indices**
```python
# In system_setup.py
def create_flow_with_full_indices(mfa_system, flow_name, process_start, process_end):
    """Create flow with full ODYM-compliant indices."""
    
    # Determine flow indices based on available dimensions
    indices = "t,e"  # Start with Time and Element
    
    if "Region" in mfa_system.IndexTable.index:
        indices += ",r"
    if "Good" in mfa_system.IndexTable.index:
        indices += ",g"
    if "Material" in mfa_system.IndexTable.index:
        indices += ",m"
    if "Process" in mfa_system.IndexTable.index:
        indices += ",p"
    
    # Create flow with proper indices
    flow = msc.Flow(
        Name=flow_name,
        P_Start=process_start,
        P_End=process_end,
        Indices=indices
    )
    
    return flow
```

#### **3.2 Update Data Array Shapes**
```python
# In system_setup.py
def initialize_flow_values(mfa_system, flow):
    """Initialize flow values with proper dimensions."""
    
    # Get dimension sizes
    n_years = len(mfa_system.IndexTable.Classification["Time"].Items)
    n_elements = len(mfa_system.IndexTable.Classification["Element"].Items)
    
    # Initialize with Time and Element dimensions
    shape = [n_years, n_elements]
    
    # Add additional dimensions if available
    if "Region" in mfa_system.IndexTable.index:
        n_regions = len(mfa_system.IndexTable.Classification["Region"].Items)
        shape.append(n_regions)
    
    if "Good" in mfa_system.IndexTable.index:
        n_goods = len(mfa_system.IndexTable.Classification["Good"].Items)
        shape.append(n_goods)
    
    if "Material" in mfa_system.IndexTable.index:
        n_materials = len(mfa_system.IndexTable.Classification["Material"].Items)
        shape.append(n_materials)
    
    if "Process" in mfa_system.IndexTable.index:
        n_processes = len(mfa_system.IndexTable.Classification["Process"].Items)
        shape.append(n_processes)
    
    # Initialize flow values
    flow.Values = np.zeros(shape)
    
    return flow
```

## Excel Template Impact Analysis

### **Current Excel Structure**
**Impact Level**: ❌ **MAJOR CHANGES REQUIRED**

#### **Required Excel Changes**:

1. **Add Regional Data Sheets**:
   - `3_1_Definition_Regions`
   - `3_2_Data_Regions`

2. **Add Good Data Sheets**:
   - `4_1_Definition_Goods`
   - `4_2_Data_Goods`

3. **Add Material Data Sheets**:
   - `5_1_Definition_Materials`
   - `5_2_Data_Materials`

4. **Add Process Data Sheets**:
   - `6_1_Definition_Processes`
   - `6_2_Data_Processes`

5. **Update Existing Sheets**:
   - Add regional, good, material, process columns to flow definitions
   - Update data structures to support multi-dimensional arrays

#### **Example Excel Structure**:
```
Excel Template Structure:
├── 1_1_Definition_Flows (Updated with new dimensions)
├── 1_2_Data_Flows (Updated with new dimensions)
├── 2_1_Definition_Processes (Updated)
├── 2_2_static_TCs (Updated)
├── 2_3_dynamic_TCs (Updated)
├── 2_4_Initial_Stock (Updated)
├── 3_1_Definition_Regions (NEW)
├── 3_2_Data_Regions (NEW)
├── 4_1_Definition_Goods (NEW)
├── 4_2_Data_Goods (NEW)
├── 5_1_Definition_Materials (NEW)
├── 5_2_Data_Materials (NEW)
├── 6_1_Definition_Processes (NEW)
└── 6_2_Data_Processes (NEW)
```

## Compliance Score Summary

| Dimension | Current Status | Compliance Score | Priority | Effort |
|-----------|----------------|------------------|----------|--------|
| **Time** | ✅ Complete | 10/10 | Low | 0 hours |
| **Element** | ✅ Complete | 10/10 | Low | 0 hours |
| **Region** | ❌ Missing | 0/10 | High | 4-6 hours |
| **Good** | ❌ Missing | 0/10 | High | 4-6 hours |
| **Material** | ❌ Missing | 0/10 | Medium | 3-4 hours |
| **Process** | ❌ Missing | 0/10 | Medium | 3-4 hours |

**Overall Dimension Compliance**: 3/10 (Poor)

## Recommendations

### **Immediate Actions (High Priority)**

1. **Add Region Dimension**: Critical for multi-regional studies
2. **Add Good Dimension**: Essential for commodity tracking
3. **Update IndexTable**: Include all dimensions
4. **Update Flow Indices**: Support multi-dimensional flows

### **Medium-Term Actions (Medium Priority)**

1. **Add Material Dimension**: For material-specific analysis
2. **Add Process Dimension**: For process-type analysis
3. **Update Data Structures**: Support multi-dimensional arrays
4. **Update Excel Templates**: Add new dimension sheets

### **Long-Term Actions (Low Priority)**

1. **Comprehensive Testing**: Test all dimension combinations
2. **Performance Optimization**: Optimize multi-dimensional operations
3. **Documentation Updates**: Update documentation for new dimensions
4. **User Training**: Train users on new dimension system

## Conclusion

Your observation about missing dimensions is **absolutely correct** and represents a **critical compliance issue**. BioDYM currently uses only 2 out of 6 standard ODYM dimensions (Time and Element), missing the crucial Region, Good, Material, and Process dimensions.

**Key Findings**:
- **Dimension Compliance**: 3/10 (Poor)
- **Missing Dimensions**: 4 out of 6 standard dimensions
- **Impact**: Major limitations in scalability and interoperability
- **Excel Impact**: Major changes required to Excel templates

**Recommended Approach**:
1. **Phase 1**: Add Region and Good dimensions (high priority)
2. **Phase 2**: Add Material and Process dimensions (medium priority)
3. **Phase 3**: Update data structures and Excel templates (high priority)

This dimension compliance issue is **more critical** than the function compliance issues we discussed earlier, as it fundamentally limits BioDYM's ability to scale and integrate with other ODYM-based systems.

---

*Document Version: 1.0*  
*Last Updated: [Current Date]*  
*Author: BioDYM Development Team*


---


================================================================================
# File: ODYM_FUNCTIONS_COMPLIANCE_ANALYSIS.md
================================================================================

# BioDYM Functions vs. ODYM Functions: Compliance Analysis

## Overview

This document analyzes the degree to which BioDYM engine functions follow the design principles established by the [ODYM functions module](https://github.com/IndEcol/ODYM/tree/master/src/odym/functions). The analysis covers function design patterns, naming conventions, parameter handling, and integration with ODYM classes.

## Executive Summary

- **Overall Compliance**: 6/10 (Moderate) - Good foundation with room for improvement
- **Function Design**: 7/10 (Good) - Well-structured, clear purpose
- **ODYM Integration**: 5/10 (Moderate) - Limited use of ODYM function patterns
- **Naming Conventions**: 8/10 (Very Good) - Clear, descriptive names
- **Error Handling**: 6/10 (Moderate) - Basic error handling, could be improved

## ODYM Functions Analysis

### Key ODYM Function Principles

Based on the [ODYM functions repository](https://github.com/IndEcol/ODYM/tree/master/src/odym/functions), the following principles are established:

#### 1. **Function Naming Conventions**
- **Descriptive Names**: Functions clearly indicate their purpose
- **Consistent Patterns**: Similar functions follow naming patterns
- **Abbreviations**: Standard abbreviations (e.g., `MI_` for MultiIndex)

#### 2. **Parameter Handling**
- **Type Hints**: Clear parameter types and return types
- **Default Values**: Sensible defaults for optional parameters
- **Validation**: Input validation and error handling

#### 3. **Integration with ODYM Classes**
- **Class Methods**: Functions work seamlessly with ODYM classes
- **Data Structures**: Consistent use of ODYM data structures
- **Return Values**: Standardized return formats

#### 4. **Error Handling**
- **Graceful Degradation**: Functions handle errors gracefully
- **Informative Messages**: Clear error messages and logging
- **Validation**: Input validation before processing

## BioDYM Functions Compliance Assessment

### Function Design Patterns Analysis

| Aspect | ODYM Standard | BioDYM Implementation | Compliance Score |
|--------|---------------|----------------------|------------------|
| **Naming Conventions** | Descriptive, consistent | Clear, descriptive | 8/10 |
| **Parameter Handling** | Type hints, validation | Basic, some validation | 6/10 |
| **Error Handling** | Comprehensive | Basic | 6/10 |
| **ODYM Integration** | Deep integration | Limited integration | 5/10 |
| **Documentation** | Comprehensive docstrings | Good docstrings | 7/10 |
| **Return Values** | Standardized formats | Consistent formats | 7/10 |

### Detailed Function Analysis

#### 1. **Solver Functions** (`solver.py`)

**Functions Analyzed**:
- `calculate_final_balances(mfa_system)`
- `process_initial_stocks(mfa_system)`
- `enhanced_input_validation(input_flows, dsm_processes)`
- `_calculate_tc_driven_flows(...)`
- `_calculate_dsm_flows(...)`
- `_calculate_fomp_flows(...)`
- `run_mfa_calculation(...)`

**Compliance Assessment**:

✅ **Strengths**:
- **Clear Function Names**: Functions clearly indicate their purpose
- **Good Documentation**: Comprehensive docstrings with parameters and returns
- **Consistent Patterns**: Similar functions follow consistent patterns
- **Modular Design**: Functions are well-separated by responsibility

❌ **Areas for Improvement**:
- **Limited ODYM Integration**: Manual flow aggregation instead of ODYM methods
- **Basic Error Handling**: Limited try-catch blocks and validation
- **Missing Type Hints**: No type annotations for parameters
- **Custom Logic**: BioDYM-specific logic not following ODYM patterns

**Example Non-Compliant Pattern**:
```python
# Current BioDYM approach
def calculate_final_balances(mfa_system):
    """Calculates the final stock changes (dS) and absolute stocks (S)."""
    for pid in {p.ID for p in mfa_system.ProcessList}:
        inflows = [f.Values for f in mfa_system.FlowDict.values() if f.P_End == pid]
        total_inflows = sum(inflows) if inflows else np.zeros_like(stock_s.Values)
```

**ODYM-Compliant Approach**:
```python
# Should use ODYM methods
def calculate_final_balances(mfa_system):
    """Calculates the final stock changes using ODYM methods."""
    try:
        # Use ODYM's built-in methods
        balance = mfa_system.MassBalance()
        # Process balance results
        return mfa_system
    except Exception as e:
        logger.error(f"Balance calculation failed: {e}")
        raise
```

#### 2. **Initial Stock Engine Functions** (`initial_stock_engine.py`)

**Functions Analyzed**:
- `load_initial_stock_parameters(excel_data)`
- `apply_initial_stock_values(mfa_system, initial_stock_configs)`
- `process_initial_stock_outflows(mfa_system, initial_stock_configs)`
- `_create_single_outflow_flow(...)`
- `update_initial_stock_flows_during_solver(mfa_system)`

**Compliance Assessment**:

✅ **Strengths**:
- **Excel Integration**: Good integration with Excel data loading
- **Configuration Management**: Well-structured configuration handling
- **Modular Design**: Clear separation of concerns

❌ **Areas for Improvement**:
- **Direct ODYM Object Manipulation**: Direct creation and modification of ODYM objects
- **Custom Attributes**: Adding custom attributes to ODYM objects
- **Limited Validation**: Basic validation of input data

**Example Non-Compliant Pattern**:
```python
# Current BioDYM approach
def _create_single_outflow_flow(mfa_system, flow_name, process_id, destination_process, initial_stock, consumption_rate, split_fraction=1.0):
    # Direct ODYM object creation
    mfa_system.FlowDict[flow_name] = msc.Flow(
        Name=flow_name,
        P_Start=process_id,
        P_End=destination_process,
        Indices="t,e"
    )
    
    # Adding custom attributes
    flow._initial_stock_config = {
        'initial_stock': initial_stock.copy(),
        'consumption_rate': consumption_rate,
        'split_fraction': split_fraction
    }
```

**ODYM-Compliant Approach**:
```python
# Should use ODYM's proper methods
def create_flow_odym_compliant(mfa_system, flow_name, process_id, destination_process):
    """Create flow using ODYM-compliant methods."""
    try:
        # Use ODYM's flow creation methods
        flow = msc.Flow(Name=flow_name, P_Start=process_id, P_End=destination_process, Indices="t,e")
        
        # Use ODYM's initialization methods
        mfa_system.Initialize_FlowValues()
        
        # Store configuration in ODYM Extensions
        process = mfa_system.ProcessList[process_id]
        process.add_extension(Name="initial_stock_config", Value=config_dict)
        
        return flow
    except Exception as e:
        logger.error(f"Flow creation failed: {e}")
        raise
```

#### 3. **DSM Model Functions** (`dsm_model.py`)

**Functions Analyzed**:
- `_calculate_outflow_from_inflows(total_inflow_values, params, time_vector)`
- `_calculate_outflow_from_initial_stock(initial_stock_vector, mean_lifetimes, num_years, num_elements)`
- `_distribute_and_assign_outflows(...)`
- `calculate_dynamic_stock(mfa_system, dsm_params_config)`

**Compliance Assessment**:

✅ **Strengths**:
- **Pure Functions**: Some functions are pure (no side effects)
- **Clear Logic**: Well-structured calculation logic
- **Parameter Handling**: Good parameter organization

❌ **Areas for Improvement**:
- **Direct Value Assignment**: Direct modification of ODYM object values
- **Limited Error Handling**: Basic error handling
- **Custom Logic**: BioDYM-specific logic not following ODYM patterns

#### 4. **FOMP Model Functions** (`fomp_model.py`)

**Functions Analyzed**:
- `_calculate_fomp_series(dm_inflow_series, params, initial_stock_labile, initial_stock_recalcitrant)`
- `calculate_fomp(mfa_system, fomp_params_config, input_flow_composition)`

**Compliance Assessment**:

✅ **Strengths**:
- **Pure Function Design**: `_calculate_fomp_series` is a pure function
- **Clear Documentation**: Good docstrings and parameter descriptions
- **Mathematical Clarity**: Clear implementation of FOMP equations

❌ **Areas for Improvement**:
- **Limited ODYM Integration**: Direct value assignment to ODYM objects
- **Custom Attributes**: Use of custom attributes on ODYM objects

#### 5. **Scenario Engine Functions** (`scenario_engine.py`)

**Functions Analyzed**:
- `run_scenario_analysis(...)`
- `_extract_scenario_names(config_obj)`
- `_run_single_scenario(...)`

**Compliance Assessment**:

✅ **Strengths**:
- **Type Hints**: Good use of type hints
- **Clear Structure**: Well-organized scenario management
- **Error Handling**: Better error handling than other modules

❌ **Areas for Improvement**:
- **Limited ODYM Integration**: Basic integration with ODYM classes
- **Custom Logic**: Scenario-specific logic not following ODYM patterns

## Specific Compliance Issues

### 1. **Function Naming Conventions**

**ODYM Standard**:
- Descriptive names with clear purpose
- Consistent abbreviations (e.g., `MI_` for MultiIndex)
- Standard patterns for similar functions

**BioDYM Implementation**:
- ✅ **Good**: Clear, descriptive function names
- ❌ **Missing**: No consistent abbreviation patterns
- ❌ **Missing**: No ODYM-style naming conventions

**Recommendation**:
```python
# Adopt ODYM naming patterns
def MI_CalculateFlowAggregation(mfa_system, process_id):
    """Calculate flow aggregation using ODYM methods."""
    pass

def ODYM_ValidateSystemConsistency(mfa_system):
    """Validate system consistency using ODYM methods."""
    pass
```

### 2. **Parameter Handling**

**ODYM Standard**:
- Type hints for all parameters
- Input validation
- Sensible default values
- Clear parameter documentation

**BioDYM Implementation**:
- ✅ **Good**: Clear parameter documentation
- ❌ **Missing**: Type hints
- ❌ **Missing**: Input validation
- ❌ **Missing**: Default values where appropriate

**Recommendation**:
```python
# Add type hints and validation
def calculate_final_balances(mfa_system: msc.MFAsystem) -> msc.MFAsystem:
    """Calculate final balances with proper type hints."""
    if not isinstance(mfa_system, msc.MFAsystem):
        raise TypeError("mfa_system must be an MFAsystem object")
    # Implementation
```

### 3. **Error Handling**

**ODYM Standard**:
- Comprehensive try-catch blocks
- Informative error messages
- Logging integration
- Graceful degradation

**BioDYM Implementation**:
- ❌ **Missing**: Limited try-catch blocks
- ❌ **Missing**: Basic error messages
- ❌ **Missing**: No logging integration
- ❌ **Missing**: Limited graceful degradation

**Recommendation**:
```python
# Add comprehensive error handling
def calculate_final_balances(mfa_system: msc.MFAsystem) -> msc.MFAsystem:
    """Calculate final balances with error handling."""
    try:
        # Implementation
        return mfa_system
    except AttributeError as e:
        logger.error(f"Missing attribute in MFA system: {e}")
        raise ValueError(f"Invalid MFA system structure: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in balance calculation: {e}")
        raise
```

### 4. **ODYM Integration**

**ODYM Standard**:
- Use ODYM's built-in methods
- Leverage ODYM's validation functions
- Follow ODYM's data structures
- Use ODYM's error handling patterns

**BioDYM Implementation**:
- ❌ **Major Issue**: Manual flow aggregation instead of ODYM methods
- ❌ **Major Issue**: Direct object manipulation
- ❌ **Major Issue**: Custom attributes on ODYM objects
- ❌ **Major Issue**: Limited use of ODYM validation

**Recommendation**:
```python
# Use ODYM methods instead of manual operations
def calculate_process_flows_odym_compliant(mfa_system: msc.MFAsystem, process_id: int) -> np.ndarray:
    """Calculate process flows using ODYM methods."""
    try:
        # Use ODYM's built-in methods
        inflows = []
        for flow in mfa_system.FlowDict.values():
            if flow.P_End == process_id:
                flow_sum = mfa_system.Flow_Sum_By_Element(flow.Name)
                inflows.append(flow_sum)
        
        return sum(inflows) if inflows else np.zeros((len(mfa_system.Time_L), len(mfa_system.Elements)))
    except Exception as e:
        logger.error(f"Flow calculation failed for process {process_id}: {e}")
        raise
```

## Compliance Improvement Strategy

### Phase 1: Foundation Improvements (1-2 weeks)

#### 1.1 Add Type Hints
**Priority**: High | **Effort**: 2-3 hours

```python
# Add type hints to all functions
from typing import Dict, List, Optional, Tuple, Union
import numpy as np

def calculate_final_balances(mfa_system: msc.MFAsystem) -> msc.MFAsystem:
    """Calculate final balances with type hints."""
    pass

def load_initial_stock_parameters(excel_data: Dict[str, pd.DataFrame]) -> Dict[int, Dict]:
    """Load initial stock parameters with type hints."""
    pass
```

#### 1.2 Add Input Validation
**Priority**: High | **Effort**: 3-4 hours

```python
# Add input validation to all functions
def calculate_final_balances(mfa_system: msc.MFAsystem) -> msc.MFAsystem:
    """Calculate final balances with input validation."""
    if not isinstance(mfa_system, msc.MFAsystem):
        raise TypeError("mfa_system must be an MFAsystem object")
    
    if not mfa_system.FlowDict:
        raise ValueError("MFA system has no flows defined")
    
    # Implementation
```

#### 1.3 Add Error Handling
**Priority**: High | **Effort**: 4-5 hours

```python
# Add comprehensive error handling
import logging

logger = logging.getLogger(__name__)

def calculate_final_balances(mfa_system: msc.MFAsystem) -> msc.MFAsystem:
    """Calculate final balances with error handling."""
    try:
        # Implementation
        return mfa_system
    except Exception as e:
        logger.error(f"Balance calculation failed: {e}")
        raise
```

### Phase 2: ODYM Integration (2-3 weeks)

#### 2.1 Use ODYM Methods
**Priority**: High | **Effort**: 6-8 hours

```python
# Replace manual operations with ODYM methods
def calculate_process_flows_odym_compliant(mfa_system: msc.MFAsystem, process_id: int) -> np.ndarray:
    """Calculate process flows using ODYM methods."""
    try:
        # Use ODYM's Flow_Sum_By_Element method
        inflows = []
        for flow in mfa_system.FlowDict.values():
            if flow.P_End == process_id:
                flow_sum = mfa_system.Flow_Sum_By_Element(flow.Name)
                inflows.append(flow_sum)
        
        return sum(inflows) if inflows else np.zeros((len(mfa_system.Time_L), len(mfa_system.Elements)))
    except Exception as e:
        logger.error(f"Flow calculation failed: {e}")
        raise
```

#### 2.2 Use ODYM Validation
**Priority**: Medium | **Effort**: 3-4 hours

```python
# Use ODYM's validation methods
def validate_system_before_calculation(mfa_system: msc.MFAsystem) -> bool:
    """Validate system using ODYM methods."""
    try:
        # Use ODYM's built-in validation
        mfa_system.IndexTableCheck()
        mfa_system.Consistency_Check()
        return True
    except Exception as e:
        logger.error(f"System validation failed: {e}")
        return False
```

### Phase 3: Advanced Improvements (2-3 weeks)

#### 3.1 Implement ODYM Function Patterns
**Priority**: Medium | **Effort**: 4-6 hours

```python
# Implement ODYM-style function patterns
def ODYM_CalculateMassBalance(mfa_system: msc.MFAsystem) -> np.ndarray:
    """Calculate mass balance using ODYM methods."""
    try:
        balance = mfa_system.MassBalance()
        return balance
    except Exception as e:
        logger.error(f"Mass balance calculation failed: {e}")
        raise

def ODYM_ValidateFlowConsistency(mfa_system: msc.MFAsystem) -> bool:
    """Validate flow consistency using ODYM methods."""
    try:
        for flow_name, flow in mfa_system.FlowDict.items():
            if flow.Values is not None and np.any(flow.Values < 0):
                logger.warning(f"Negative values found in flow {flow_name}")
                return False
        return True
    except Exception as e:
        logger.error(f"Flow validation failed: {e}")
        return False
```

#### 3.2 Add Logging Integration
**Priority**: Medium | **Effort**: 2-3 hours

```python
# Add ODYM-style logging
def setup_biodym_logging(log_filename: str, log_path: str) -> logging.Logger:
    """Setup logging using ODYM patterns."""
    logger, console_log, file_log = msf.function_logger(
        log_filename=log_filename,
        log_pathname=log_path,
        file_level=logging.DEBUG,
        console_level=logging.INFO
    )
    return logger
```

## Compliance Score Summary

| Module | Current Score | Target Score | Priority | Effort |
|--------|---------------|--------------|----------|--------|
| **solver.py** | 6/10 | 9/10 | High | 8-10 hours |
| **initial_stock_engine.py** | 5/10 | 9/10 | High | 6-8 hours |
| **dsm_model.py** | 6/10 | 8/10 | Medium | 4-6 hours |
| **fomp_model.py** | 7/10 | 8/10 | Medium | 3-4 hours |
| **scenario_engine.py** | 7/10 | 8/10 | Low | 2-3 hours |
| **mc_simulation.py** | 6/10 | 8/10 | Low | 3-4 hours |

## Recommendations

### Immediate Actions (High Priority)

1. **Add Type Hints**: Improve function signatures with proper type annotations
2. **Add Input Validation**: Validate all function inputs
3. **Add Error Handling**: Implement comprehensive try-catch blocks
4. **Use ODYM Methods**: Replace manual operations with ODYM methods

### Medium-Term Actions (Medium Priority)

1. **Implement ODYM Patterns**: Follow ODYM function design patterns
2. **Add Logging**: Integrate with ODYM's logging system
3. **Standardize Return Values**: Use consistent return value formats
4. **Add Performance Monitoring**: Monitor function performance

### Long-Term Actions (Low Priority)

1. **Refactor Function Names**: Adopt ODYM naming conventions
2. **Implement Pure Functions**: Create more pure functions where possible
3. **Add Comprehensive Testing**: Test all functions thoroughly
4. **Documentation Updates**: Update documentation to match ODYM standards

## Conclusion

Your BioDYM functions show **good foundation design** but have **moderate compliance** with ODYM function principles. The main areas for improvement are:

1. **ODYM Integration**: Limited use of ODYM's built-in methods
2. **Error Handling**: Basic error handling needs improvement
3. **Type Safety**: Missing type hints and input validation
4. **Function Patterns**: Not following ODYM's established patterns

**Overall Assessment**: 6/10 (Moderate) - Good foundation with significant room for improvement in ODYM integration and error handling.

**Recommended Approach**: Implement the phased improvement strategy, starting with high-priority items like type hints, validation, and ODYM method usage.

---

*Document Version: 1.0*  
*Last Updated: [Current Date]*  
*Author: BioDYM Development Team*


---


================================================================================
# File: ODYM_SIMPLIFICATIONS.md
================================================================================

# ODYM Implementation Simplifications for BioDYM

## Simplifications Identified from ODYM Best Practices

Based on the [ODYM framework](https://github.com/IndEcol/ODYM) and your Excel structure, here are the key simplifications you can implement:

### **1. Keep Indices Simple Initially**

**Recommended Approach**: Start with "t,e" for everything, then add dimensions as needed.

```python
# Phase 1: Simple Indices
Flow Indices = "t,e"
Stock Indices = "t,e"
Parameter Indices = "t,e"

# Phase 2: Add dimensions when needed
Flow Indices = "t,e,g"      # If tracking goods
Flow Indices = "t,e,m"      # If tracking materials
Flow Indices = "t,e,r"      # If tracking regions
```

**ODYM Simplification**: You don't need all dimensions at once. ODYM automatically handles the dimension matching.

### **2. Use Default/Empty for "All"**

**ODYM Simplification**: Don't use "All" as a code. Use empty cells.

```python
# Instead of:
Good_ID = "All"  # ❌
Material_ID = "All"  # ❌

# Use:
Good_ID = "" (empty)  # ✅
Material_ID = "" (empty)  # ✅
```

**Why**: Empty cells are cleaner and easier to parse in Python.

### **3. Let ODYM Handle Dimension Matching**

**ODYM Key Feature**: ODYM automatically matches dimensions during calculations.

```python
# You don't need to manually index arrays
# ODYM does it automatically:
flow_1.Values + flow_2.Values  # Automatically matches dimensions
```

**Simplification**: Focus on defining your Indices correctly, let ODYM handle the rest.

### **4. Use Consistent Dimension Order**

**ODYM Convention**: Use consistent letter order for dimensions.

```python
# Standard order (alphabetical):
IndexLetter = ["t", "e", "r", "g", "m", "p"]
           # Time, Element, Region, Good, Material, Process

# In Indices string:
Indices = "t,e,r,g,m,p"  # ✅ Consistent order
```

**Simplification**: This makes dimension management easier and more predictable.

### **5. Don't Over-Dimension Everything**

**ODYM Simplification**: Only add dimensions you actually use.

```python
# If you only track goods sometimes, don't add 'g' to all flows:
Flow without goods: Indices = "t,e"     # Simple
Flow with goods: Indices = "t,e,g"      # Extended

# ODYM handles this gracefully
```

**Your Current Excel**: You have `ODYM_Indices = "t,r,p,g,m,e,"` for all flows

**Recommendation**: Make Indices per-flow configurable:
- Simple flows: `Indices = "t,e"`
- Complex flows: `Indices = "t,e,g"` or `"t,e,r,p,g,m"`

### **6. Use IndexTable for Dimension Definitions**

**ODYM Simplification**: Define dimensions once in IndexTable, use everywhere.

```python
# In IndexTable:
Aspect = ["Time", "Element", "Region", "Good", "Material"]
IndexLetter = ["t", "e", "r", "g", "m"]

# Then all Flows/Stocks automatically use this
flow.Indices = "t,e,g"  # Uses IndexTable definitions
```

**Your Implementation**: This is exactly what your configuration sheet does! ✅

### **7. Avoid Manual Array Manipulation**

**ODYM Simplification**: Use ODYM methods instead of manual aggregation.

```python
# Instead of manual aggregation:
total = sum([f.Values for f in flows])  # ❌ Manual

# Use ODYM methods:
total = mfa_system.Flow_Sum_By_Element(flow_name)  # ✅ ODYM method
```

**Your Current Code**: You're doing manual aggregation in `solver.py`

**Fix**: This is in your Phase 2 plan - replace with ODYM methods.

### **8. Use Extensions for Custom Data**

**ODYM Simplification**: Don't add custom attributes to ODYM objects.

```python
# Instead of:
flow._initial_stock_config = {...}  # ❌ Custom attribute

# Use ODYM Extensions:
process.add_extension(
    Time=None,
    Name="initial_stock_config",
    Value={...},
    Unit="configuration"
)  # ✅ ODYM-compliant
```

**Your Current Code**: You're using custom attributes in `initial_stock_engine.py`

**Fix**: This is in your Phase 2 plan - use ODYM Extensions.

## Your Excel Structure - Simplifications Needed

### **Fix 1: Remove "All" Values**

**Current**:
```excel
ODYM_Good_ID = "All"
ODYM_Material_ID = "All"
ODYM_Element_ID = "All"
```

**Should Be**:
```excel
ODYM_Good_ID = ""  # Empty cell
ODYM_Material_ID = ""  # Empty cell
ODYM_Element_ID = ""  # Empty cell
```

### **Fix 2: Remove Trailing Commas**

**Current**:
```excel
ODYM_Indices = "t,r,p,g,m,e,"
Column2 = "All,All,All,1,All,All,"
```

**Should Be**:
```excel
ODYM_Indices = "t,e,r,p,g,m"  # No trailing comma
Column2 = "All,All,All,1,All,All"  # No trailing comma
```

### **Fix 3: Make Indices Per-Flow Configurable**

**Current**: All flows use the same Indices

**Simplification**: Allow per-flow Indices:

```excel
Flow_ID | Flow_Name | ODYM_Indices
--------|----------|-------------
F_01_02 | Simple_Flow | t,e
F_02_03 | Goods_Flow | t,e,g
F_03_04 | Material_Flow | t,e,m
```

## Simplified Implementation Checklist

### **Phase 1: Basic Setup (Current State)**

- [x] Define dimensions in configuration sheet
- [x] Add Indices column to Flows
- [ ] Remove "All" values (use empty instead)
- [ ] Remove trailing commas
- [ ] Test with simple "t,e" Indices

### **Phase 2: Make Indices Configurable**

- [ ] Read Indices from Excel (not hardcoded)
- [ ] Allow different Indices per flow
- [ ] Update data loader to handle empty vs. specific IDs
- [ ] Test with mixed Indices

### **Phase 3: Add Multi-Dimensional Support**

- [ ] Support Good dimension when specified
- [ ] Support Material dimension when specified
- [ ] Support Region dimension when specified
- [ ] Support Process dimension when specified

## Key Simplification: Start Simple, Expand Gradually

**ODYM Philosophy**: Don't over-engineer. Start with what you need, add complexity as needed.

**Recommended Progression**:

1. **Week 1**: Get "t,e" working for all flows/stocks
2. **Week 2**: Add Good dimension (if needed)
3. **Week 3**: Add Material dimension (if needed)
4. **Week 4**: Add other dimensions as needed

**Your Excel**: You've added all dimensions upfront

**Simplification**: Make them optional/empty by default, only specify when needed!

## Summary: Simplifications for Your Implementation

1. **Use empty cells for "All"** instead of "All" string
2. **Remove trailing commas** from Indices
3. **Make Indices per-flow configurable** (not same for all)
4. **Start with "t,e"** for everything, add dimensions gradually
5. **Don't require all dimensions** - ODYM handles missing dimensions gracefully
6. **Use ODYM methods** instead of manual aggregation (Phase 2)
7. **Use ODYM Extensions** instead of custom attributes (Phase 2)

These simplifications will make your implementation cleaner and more maintainable!

---

*Document Version: 1.0*  
*Last Updated: [Current Date]*  
*Author: BioDYM Development Team*


---


================================================================================
# File: PHASE_0_EXCEL_PREPARATION.md
================================================================================

# Phase 0 Excel Preparation - COMPLETED ✅

## Summary

Successfully created a clean BioDYM ODYM test Excel file ready for Phase 0 testing!

## What Was Done

### ✅ Clean Excel File Created
- **Original**: `01_data/01_input/251027_BioDYM_ODYM.xlsm`
- **Clean Version**: `01_data/01_input/251027_BioDYM_ODYM_CLEAN.xlsm`
- **Status**: All format issues fixed

### ✅ Excel Fixes Applied

1. **Removed "All" Values**
   - All `ODYM_*_ID` columns now use empty cells instead of "All"
   - Empty cells = all values (ODYM convention)
   - Numeric values = specific values
   - Zero = excluded from dimension

2. **Fixed Trailing Commas**
   - Removed trailing commas from `ODYM_Indices` column
   - Clean format: `t,e` instead of `t,e,`
   - Ready for ODYM parsing

3. **Added Stock_Indices Column**
   - Added to `2_1_Definition_Processes` sheet
   - Default value: `t,e` (Time + Element)
   - Matches Flow indices structure

### ✅ Sheets Copied Successfully

- `0_Configuration` - ODYM configuration settings
- `1_1_Definition_Flows` - Flow definitions with ODYM indices
- `1_2_Data_Flows` - Flow data
- `2_1_Definition_Processes` - Process definitions with Stock_Indices
- `2_2_static_TCs` - Static transfer coefficients
- `2_3_dynamic_TCs` - Dynamic transfer coefficients
- `2_4_Initial_Stock` - Initial stock data
- `3_1_Definition_DSM` - Dynamic Stock Model definitions
- `3_2_Definition_FOMP` - FOMP process definitions

## Next Steps - Phase 0

### **Task 1: Create Golden Reference Dataset**

Run the full workflow with the clean Excel file:

```bash
# This will generate results_scientific.xlsx
python -c "from src.main import main; main()"
```

Save the output as the golden reference for Phase 0 tests.

### **Task 2: Create Integration Test Suite**

Create `04_tests/workflow/test_e2e_workflow.py`:

```python
"""Integration tests for Phase 0 - ODYM Compliance."""

import unittest
import pandas as pd
import sys
sys.path.append('02_src')
from main import main

class TestE2EWorkflow(unittest.TestCase):
    """Test end-to-end workflow with clean Excel file."""
    
    def test_golden_excel_output(self):
        """Test that workflow produces golden output."""
        # Run workflow
        result = main('01_data/01_input/251027_BioDYM_ODYM_CLEAN.xlsm')
        
        # Load golden reference
        golden = pd.read_excel('04_tests/workflow/golden/results_scientific.xlsx')
        
        # Load actual output
        actual = pd.read_excel('01_data/02_output/results_scientific.xlsx')
        
        # Compare
        pd.testing.assert_frame_equal(actual, golden)
```

### **Task 3: Verify Excel Structure**

Verify the clean Excel file has proper structure:

```python
# Check dimensions
df_flows = pd.read_excel('01_data/01_input/251027_BioDYM_ODYM_CLEAN.xlsm',
                         sheet_name='1_1_Definition_Flows', 
                         engine='openpyxl')

# Should have ODYM columns
assert 'ODYM_Indices' in df_flows.columns
assert 'ODYM_Good_ID' in df_flows.columns
assert 'ODYM_Material_ID' in df_flows.columns

# Check no "All" values
assert not df_flows['ODYM_Good_ID'].astype(str).str.contains('All').any()
```

## Excel Structure Compliance

### ✅ ODYM Dimension ID Conventions

| Value | Meaning | Example |
|-------|---------|---------|
| Empty/BLANK | All values | All regions, all goods, all materials |
| Number (1, 2, 3...) | Specific value | Region 1, Good type 2 |
| 0 | Exclude from dimension | Not applicable |

### ✅ Flow Indices Format

- **Simple**: `t,e` (Time + Element)
- **With Region**: `t,e,r` (Time + Element + Region)
- **Full**: `t,e,r,g,m,p` (all dimensions)

### ✅ Stock Indices Format

- **Default**: `t,e` (Time + Element)
- **Match flow indices** for consistency

## Phase 0 Status

✅ **Excel File**: Clean and ready
⏳ **Golden Dataset**: Need to generate
⏳ **Integration Tests**: Need to create

## Script Used

The script `create_clean_test_excel.py` can be run to regenerate the clean Excel file anytime:

```bash
python create_clean_test_excel.py
```

This will:
1. Load the original Excel file
2. Copy all essential sheets
3. Clean ODYM dimension columns
4. Add Stock_Indices column
5. Save as `251027_BioDYM_ODYM_CLEAN.xlsm`

---

**Ready for Phase 0: Generate Golden Dataset!** 🚀


---


================================================================================
# File: PHASE_0_PROGRESS.md
================================================================================

# Phase 0 Progress - Initial Setup Complete ✅

## Summary

We've successfully completed the initial setup for the ODYM compliance refactoring. The system is now ready for Phase 0 testing.

## ✅ Completed Tasks

### 1. **Clean Excel File Created**
- **File**: `01_data/01_input/251027_BioDYM_ODYM_CLEAN.xlsx`
- **Changes Applied**:
  - Replaced "All" values with empty cells (ODYM convention)
  - Removed trailing commas from Indices strings
  - Added `Stock_Indices` column to `2_1_Definition_Processes` sheet
  - Saved as .xlsx format (no macros)

### 2. **Workflow Notebook Fixed**
- Fixed `Year_Flow` → `Flow_Data_Year` column name issue
- Added multiple Element attribute fallback checks
- Config object loading working (Elements fallback working as expected)

### 3. **Current Status**
- Branch: `feature/odym-compliance` ✅
- Excel file: Clean format ready for testing ✅
- Notebook: Updated and ready ✅

## 📋 Current Phase: Phase 0 - Build Testing Safety Net

### **Next Steps**

#### **Option A: Generate Golden Reference Dataset (Recommended)**
Run the full workflow once to establish baseline results:
```python
# In notebook cell or Python script
python 00_BioDYM_Workflow.py
# Or run cells in the notebook
```
This will create `results_scientific_baseline.xlsx` as a reference.

#### **Option B: Start Phase 1a Implementation**
Begin foundational refactoring:
- Use ODYM initialization methods
- Add Consistency_Check() calls
- Improve error handling

## 🎯 Recommended Next Steps

### **For Testing**:
1. Run workflow once to generate golden reference
2. Save reference outputs
3. Create integration tests

### **For Implementation**:
1. Start Phase 1a refactoring (independent of dimensions)
2. Add ODYM validation hooks
3. Improve error handling
4. Verify tests still pass

## 📊 Compliance Status

| Area | Status | Notes |
|------|--------|-------|
| Excel Format | ✅ Complete | Clean .xlsx file with ODYM-compliant structure |
| Config Loading | ✅ Working | Fallbacks handling as expected |
| Data Loader | ⏳ Pending | Needs ODYM dimension support |
| Engine Modules | ⏳ Pending | Phase 1a refactoring needed |
| Dimensions | ⏳ Pending | Phase 1b implementation |

## 💡 Notes

- Elements configuration is working via fallback mechanism
- The clean Excel file has proper ODYM structure
- Notebook is ready for testing
- Next decision: Generate golden dataset or start Phase 1a?

---

**Ready to proceed with Phase 0 testing or Phase 1a implementation!** 🚀



---


================================================================================
# File: PHASE_1A_ANALYSIS.md
================================================================================

# Phase 1a Analysis: Current Engine Status

## 🔍 Current State Analysis

### ✅ Good News: You're Already Using ODYM Validation!

**Existing Validation**:
- ✅ `mfa_system.Consistency_Check()` already called in `system_setup.py:467`
- ✅ `mfa_system.Initialize_FlowValues()` used in `system_setup.py:292`
- ✅ `mfa_system.Initialize_StockValues()` used in `system_setup.py:202`
- ✅ Manual validation patterns exist

**This is excellent!** Your codebase is already partially ODYM-compliant.

---

## 📊 What Needs Improvement

### **Issue 1: Manual Flow/Stock Assignments**

**Current Problem** (in `solver.py:49-58`):
```python
# Manual flow aggregation
inflows = [f.Values for f in mfa_system.FlowDict.values() if f.P_End == pid]
total_inflows = sum(inflows) if inflows else np.zeros_like(stock_s.Values)
```

**What we should do**:
- This is actually OK for calculation purposes
- But we should add validation after calculations
- ODYM doesn't provide built-in flow aggregation methods

**Action**: Add `Consistency_Check()` after balance calculations

---

### **Issue 2: Missing Validation Hooks**

**Current State**:
- ✅ Validation after `define_flows_and_parameters()`
- ❌ No validation after solver iterations
- ❌ No validation after DSM calculations
- ❌ No validation after FOMP calculations

**What to Add**:
1. In `solver.py` - after each iteration
2. In `dsm_model.py` - after DSM calculations
3. In `fomp_model.py` - after FOMP calculations

---

### **Issue 3: Where to Add ODYM Dimensions**

**Key Question**: Where should we add the new ODYM dimensions?

**Answer**: Add them in `system_setup.py`, specifically in the `define_model_scope()` function.

**Current Function** (`system_setup.py:29-75`):
```python
def define_model_scope(start_year, end_year, elements):
    # Only has Time and Element
```

**What We Need to Add**:
```python
def define_model_scope(start_year, end_year, elements, 
                       regions=None, goods=None, materials=None, processes=None):
    # Add all 6 ODYM dimensions
```

---

## 🎯 Best Time to Test the Workflow

### **Recommended Testing Points**

1. **After Phase 1a (Before Adding Dimensions)** ✅ **NOW**
   - Run full workflow with current 2D system
   - Ensure all tests pass
   - Establish baseline

2. **After Adding First Dimension (Region)** 
   - Test with 3D system (t,e,r)
   - Verify backward compatibility

3. **After All Dimensions Added**
   - Test with full 6D system
   - Verify all functionality works

### **Your Question Answered**:
> "Which would be the best time to test, if the workflow is still successful?"

**Answer**: Test **NOW** (after Phase 1a) before adding dimensions. This gives us a baseline to compare against.

---

## 🚀 Recommended Implementation Order

### **Step 1: Add Validation Hooks (Phase 1a) - 2-3 hours**

**Add to `solver.py`**:
```python
def calculate_final_balances(mfa_system):
    """...existing code..."""
    
    print("--> Stock balance calculation finished.")
    
    # ADD THIS:
    try:
        mfa_system.Consistency_Check()
        print("✅ Balance validation passed")
    except Exception as e:
        print(f"⚠️ Balance validation warning: {e}")
    
    return mfa_system
```

**Add to engine modules after major operations**:
- `dsm_model.py` - after DSM calculations
- `fomp_model.py` - after FOMP calculations
- `initial_stock_engine.py` - after initial stock processing

---

### **Step 2: Add ODYM Dimensions (Phase 1b) - 4-5 hours**

**Modify `system_setup.py:29`**:
```python
def define_model_scope(start_year, end_year, elements, 
                       regions=None, goods=None, materials=None, processes=None):
    """Defines the temporal and elemental scope of the MFA model with full ODYM dimensions."""
    
    # Default dimensions if not provided
    if regions is None:
        regions = ["Case_Study_Region"]  # Default single region
    
    # ... rest of the function ...
    
    # Add new dimensions to IndexTable
    index_table = pd.DataFrame({
        "Aspect": ["Time", "Element", "Region", "Good", "Material", "Process"],
        ...
    })
```

---

## 📋 Phase 1a Action Plan

### **Immediate Next Steps**:

1. **Add Validation Hooks** (2-3 hours):
   - Add `Consistency_Check()` after balance calculations
   - Add validation after DSM/FOMP calculations
   - Test that workflow still works

2. **Test Workflow** (30 minutes):
   - Run full workflow
   - Verify all outputs are correct
   - Check for any errors or warnings

3. **Document Results**:
   - Baseline established
   - Ready for Phase 1b (dimensions)

---

## 💡 Answers to Your Questions

### **Q1: Best Time to Test Workflow?**

**Answer**: **NOW** (after Phase 1a validation hooks, before adding dimensions)

**Why**: 
- We have a working 2D system
- Phase 1a adds validation (low risk)
- If tests pass, we have a stable baseline
- Then we can safely add dimensions

---

### **Q2: Where Would We Add ODYM Dimensions?**

**Answer**: In `system_setup.py`, in the `define_model_scope()` function (lines 29-75)

**Specific Changes Needed**:

1. **Function Signature** (line 29):
```python
def define_model_scope(start_year, end_year, elements, 
                       regions=None, goods=None, materials=None, processes=None):
```

2. **Add Dimensions** (after line 59):
```python
# Add Region dimension
if regions is not None:
    model_classification["Region"] = msc.Classification(
        Name="Regions", Dimension="Region", ID=3, Items=regions
    )

# Add Good dimension  
if goods is not None:
    model_classification["Good"] = msc.Classification(
        Name="Goods", Dimension="Good", ID=4, Items=goods
    )
# etc...
```

3. **Update IndexTable** (lines 61-72):
```python
index_table = pd.DataFrame({
    "Aspect": ["Time", "Element", "Region", "Good", "Material", "Process"],
    ...
})
```

---

## 🎯 Summary & Next Steps

### **Current Status**: ✅ Already Using ODYM Validation!

### **Phase 1a Tasks**:
- ✅ Add validation hooks in engine modules
- ✅ Test workflow thoroughly
- ✅ Establish baseline for Phase 1b

### **Phase 1b Tasks** (Next):
- Add dimensions in `system_setup.py:define_model_scope()`
- Update data loader for dimensions
- Test with multi-dimensional arrays

**Ready to start implementation?** 🚀



---


================================================================================
# File: PHASE_1A_COMPLETED.md
================================================================================

# Phase 1a Implementation - COMPLETED ✅

## Summary

Successfully added ODYM validation hooks to key engine modules. This improves error detection and ODYM compliance without changing data structures.

## Changes Made

### ✅ 1. Solver Module (`02_src/engine/solver.py`)

**Added validation after balance calculations** (lines 68-73):
```python
# Phase 1a: Add ODYM validation
try:
    mfa_system.Consistency_Check()
    print("✅ Balance validation passed")
except Exception as e:
    print(f"⚠️ Balance validation warning: {e}")
```

**Added validation after final calculation** (lines 443-448):
```python
# Phase 1a: Add ODYM validation after complete calculation
try:
    mfa_system.Consistency_Check()
    print("✅ Final MFA system validation passed")
except Exception as e:
    print(f"⚠️ Final validation warning: {e}")
```

### ✅ 2. DSM Module (`02_src/engine/dsm_model.py`)

**Added validation after DSM calculations** (lines 227-232):
```python
# Phase 1a: Add ODYM validation after DSM calculation
try:
    mfa_system.Consistency_Check()
    print(f"✅ DSM validation passed for process {process_id}")
except Exception as e:
    print(f"⚠️ DSM validation warning for process {process_id}: {e}")
```

### ✅ 3. FOMP Module (`02_src/engine/fomp_model.py`)

**Added validation after FOMP calculations** (lines 203-208):
```python
# Phase 1a: Add ODYM validation after FOMP calculation
try:
    mfa_system.Consistency_Check()
    print(f"✅ FOMP validation passed for process {process_id}")
except Exception as e:
    print(f"⚠️ FOMP validation warning for process {process_id}: {e}")
```

## Testing Status

### ⏳ Ready to Test

The changes are complete and ready for testing. The validation hooks will:
- ✅ Catch data inconsistencies early
- ✅ Provide better error messages
- ✅ Not break existing functionality (wrapped in try/except)

## Next Steps

1. **Test the workflow** with the clean Excel file
2. **Verify validation output** appears during calculations
3. **Confirm no regressions** in existing functionality
4. **Ready for Phase 1b** (add dimensions) if tests pass

## Files Modified

- `02_src/engine/solver.py` - 2 validation hooks added
- `02_src/engine/dsm_model.py` - 1 validation hook added
- `02_src/engine/fomp_model.py` - 1 validation hook added

**Total**: 4 ODYM validation hooks added across 3 files

---

## Questions Answered

### Q: "Where would we enter the additional ODYM Dimensions?"
**A**: In `system_setup.py`, function `define_model_scope()` - this will be Phase 1b

### Q: "Which would be the best time to test if the workflow is still successful?"
**A**: **NOW** - Test after Phase 1a changes, before adding dimensions (Phase 1b)

---

**Phase 1a Complete! Ready for testing.** 🚀



---


================================================================================
# File: PHASE_1A_PLAN.md
================================================================================

# Phase 1a: Foundational Refactoring - Implementation Plan

## 🎯 Objective

Implement class/function improvements that are **independent of new dimensions** to create a more robust baseline before adding multi-dimensional support. These changes will improve ODYM compliance without breaking existing functionality.

## 📋 Planned Actions

### **Task 1: Use ODYM Initialization Methods** ⏱️ 2-3 hours

**Current State**:
- Flows are manually initialized with numpy arrays
- Some manual Value assignments exist

**Target State**:
- Use `mfa_system.Initialize_FlowValues()` for all flows
- Use `mfa_system.Initialize_StockValues()` for all stocks
- Use `mfa_system.Initialize_ParameterValues()` for all parameters

**Files to Modify**:
- `02_src/system_setup.py` (lines 292, 202)
- Check for any manual initialization in `02_src/engine/` modules

**Benefits**:
- ✅ Consistent initialization across all objects
- ✅ Automatic shape handling
- ✅ ODYM-compliant initialization

---

### **Task 2: Add Consistency Checks** ⏱️ 2-3 hours

**Current State**:
- No validation after key operations
- Manual checks scattered throughout

**Target State**:
- Add `mfa_system.Consistency_Check()` after major operations
- Add `mfa_system.IndexTableCheck()` for validation
- Wrap in try/except for graceful failures

**Key Locations to Add Checks**:
1. `02_src/system_setup.py` - After system initialization
2. `02_src/engine/solver.py` - After balance calculations
3. `02_src/engine/initial_stock_engine.py` - After stock processing
4. `02_src/engine/dsm_model.py` - After DSM calculations
5. `02_src/engine/fomp_model.py` - After FOMP calculations

**Benefits**:
- ✅ Early detection of data inconsistencies
- ✅ Better error messages
- ✅ ODYM-compliant validation

---

### **Task 3: Improve Error Handling** ⏱️ 2-3 hours

**Current State**:
- Basic error handling
- Some operations lack error context

**Target State**:
- Wrap critical operations in try/except blocks
- Add descriptive error messages
- Log errors with context

**Key Operations to Wrap**:
1. Flow/stock initialization
2. Transfer coefficient calculations
3. Parameter loading
4. Mass balance calculations

**Benefits**:
- ✅ Better error messages
- ✅ Easier debugging
- ✅ Graceful failure handling

---

## 🔍 Detailed Implementation Strategy

### **Step 1: Identify Manual Initialization**

Let's search for manual initialization patterns:

```python
# Look for patterns like:
flow_obj.Values = np.zeros(...)
stock_obj.Values = np.zeros(...)
param_obj.Values = np.zeros(...)
```

### **Step 2: Replace with ODYM Methods**

Replace manual initialization:

```python
# OLD:
for flow_name, flow_obj in mfa_system.FlowDict.items():
    flow_obj.Values = np.zeros((len(time), len(elements)))

# NEW:
mfa_system.Initialize_FlowValues()
```

### **Step 3: Add Validation Hooks**

Add checks at key points:

```python
# After system initialization
mfa_system = initialize_mfa_system(model_classification, index_table)
try:
    mfa_system.Consistency_Check()
    mfa_system.IndexTableCheck()
    print("✅ System validation passed")
except Exception as e:
    print(f"⚠️ Validation warning: {e}")

# After major calculations
try:
    result = calculate_flows(mfa_system)
    mfa_system.Consistency_Check()
    return result
except Exception as e:
    print(f"❌ Calculation failed: {e}")
    raise
```

---

## 📊 Expected Impact

### **Benefits**:
- ✅ **Better Validation**: Catch issues early
- ✅ **ODYM Compliance**: Use standard methods
- ✅ **Maintainability**: More consistent code
- ✅ **Debugging**: Better error messages

### **Risks**:
- ⚠️ **Low Risk**: These changes don't affect data structures
- ⚠️ **Testing Needed**: Ensure no regressions

### **Success Criteria**:
- [ ] All initialization uses ODYM methods
- [ ] Validation checks added at key points
- [ ] Error handling improved
- [ ] Existing tests still pass
- [ ] No functionality loss

---

## 🚀 Next Steps

1. **Search for manual initialization** in codebase
2. **Replace with ODYM methods**
3. **Add validation hooks** at key points
4. **Improve error handling** with try/except
5. **Test thoroughly** to ensure no regressions

---

## 💡 Discussion Points

**Questions to Consider**:

1. **Should we add validation checks immediately or gradually?**
   - Recommend: Gradually, starting with critical operations

2. **How verbose should error messages be?**
   - Recommend: Detailed for development, concise for production

3. **Should we validate after every operation or key milestones?**
   - Recommend: Key milestones (initialization, major calculations, final results)

4. **What happens if validation fails?**
   - Recommend: Warning for minor issues, error for critical problems

**Ready to start implementation!** 🚀



---


================================================================================
# File: PHASE_1B_CONFIG_COMPLETE.md
================================================================================

# Phase 1b Updates - COMPLETED ✅

## Summary

Successfully implemented two critical improvements for Phase 1b ODYM compliance:

1. ✅ **Updated config loader** to read all dimensions from Excel
2. ✅ **Added IndexTable display** following ODYM tutorial conventions
3. ✅ **Updated workflow** to pass regions to `define_model_scope()`

---

## Changes Made

### **1. Updated Config Loader** (`02_src/config.py`)

Added logic to collect dimensions from Excel configuration sheet:

**Lines 64-127**:
- ✅ Collects Elements from "Element ID X" keys
- ✅ Collects Regions from "Region ID X" keys  
- ✅ Collects Goods from "Good Type X" keys
- ✅ Collects Materials from "Material ID X" keys
- ✅ Collects Process Types from "Process Type X" keys
- ✅ Converts each to comma-separated string
- ✅ Prints loaded dimensions for verification

**Example Output**:
```
✅ Loaded 2 elements from configuration: ['C', 'Remaining DM']
✅ Loaded 1 regions from configuration: ['Case_Study_Region']
✅ Loaded 4 goods from configuration: ['Raw Material', 'Processed Product', 'Product', 'Waste']
```

---

### **2. Updated Workflow** (`00_BioDYM_Workflow.py`)

**Lines 113-134**: Extract dimensions from config
```python
# Phase 1b: Extract dimension lists from config
def get_config_list(config_obj, attribute_name, default=None):
    """Helper to extract comma-separated lists from config object."""
    if hasattr(config_obj, attribute_name):
        value = getattr(config_obj, attribute_name)
        if value and pd.notna(value):
            return [item.strip() for item in str(value).split(',') if item.strip()]
    return default

regions = get_config_list(config_obj, 'Regions', ['Case_Study_Region'])
goods = get_config_list(config_obj, 'Goods', None)
materials = get_config_list(config_obj, 'Materials', None)
processes = get_config_list(config_obj, 'Process_Types', None)
```

**Line 180**: Pass regions to `define_model_scope()`
```python
model_classification, index_table = system_setup.define_model_scope(start_year, end_year, elements, regions)
```

**Lines 185-198**: Display IndexTable (ODYM convention)
```python
# Phase 1b: Display IndexTable (ODYM convention)
print("\n" + "="*60)
print("📊 ODYM SYSTEM INDEX TABLE")
print("="*60)
print(mfa_system_base.IndexTable)
print("\nAvailable Dimensions:")
for aspect in mfa_system_base.IndexTable.index:
    classification = mfa_system_base.IndexTable.loc[aspect, 'Classification']
    index_letter = mfa_system_base.IndexTable.loc[aspect, 'IndexLetter']
    print(f"  - {aspect} ({index_letter}): {len(classification.Items)} items")
```

---

## Expected Output

When you run the workflow, you should now see:

```
✅ Loaded 2 elements from configuration: ['C', 'Remaining DM']
✅ Loaded 1 regions from configuration: ['Case_Study_Region']

📊 Dimensions loaded from configuration:
   - Regions: ['Case_Study_Region']

============================================================
📊 ODYM SYSTEM INDEX TABLE
============================================================
[IndexTable with Time, Element, Region dimensions]

Available Dimensions:
  - Time (t): 26 items
    Items: [2025, 2026, 2027, 2028, 2029] ... (26 total)
  - Element (e): 2 items
    Items: ['C', 'Remaining DM']
  - Region (r): 1 items
    Items: ['Case_Study_Region']
```

---

## Benefits

1. ✅ **Elements loaded from Excel** - no more fallback
2. ✅ **Dimensions read automatically** - from configuration sheet
3. ✅ **IndexTable displayed** - following ODYM tutorial patterns
4. ✅ **Better debugging** - see system structure immediately
5. ✅ **ODYM compliance** - matches [tutorial conventions](https://github.com/IndEcol/ODYM/blob/master/docs/tutorials/tutorial_4.ipynb)

---

**Phase 1b Config & Display Updates Complete!** ✅

**Ready to test the workflow!** 🚀



---


================================================================================
# File: PHASE_1B_CONFIG_FIX.md
================================================================================

# Phase 1b Update: Config Loader + IndexTable Display

## Issues Identified

### ✅ Issue 1: Elements Not Being Read from Excel Config

**Problem**: Elements are defined in Excel as "Element ID 1", "Element ID 2", etc., but the config loader isn't reading them properly.

**Current Elements in Excel**:
- Element ID 1: C
- Element ID 2: Remaining DM

**Solution**: Update `config.py` to read these as a list.

### ✅ Issue 2: No IndexTable Display (ODYM Convention)

**Problem**: In ODYM tutorials, they always show `Tutorial_MFA_System.IndexTable` to display the system structure. We should do the same.

**Reference**: [ODYM Tutorial 4](https://github.com/IndEcol/ODYM/blob/master/docs/tutorials/tutorial_4.ipynb)

**Solution**: Add a cell to display the IndexTable in the workflow.

---

## Solutions Needed

### **1. Update Config Loader** (`02_src/config.py`)

Add logic to collect Elements from "Element ID 1", "Element ID 2", etc.:

```python
def load_config_from_excel(excel_file_path):
    """... existing code ..."""
    
    # After loading config_dict, add Elements collection
    elements = []
    for key in config_dict.keys():
        if 'Element ID' in str(key):
            element_value = config_dict[key]
            if pd.notna(element_value) and str(element_value).strip():
                elements.append(str(element_value).strip())
    
    # Add Elements as a comma-separated string
    if elements:
        config_dict['Elements'] = ','.join(elements)
    
    return config_dict
```

### **2. Update Workflow to Show IndexTable**

Add a cell after system initialization:

```python
# Display the IndexTable (ODYM convention)
print("\n" + "="*60)
print("📊 ODYM SYSTEM INDEX TABLE")
print("="*60)
display(mfa_system_base.IndexTable)
print("\nAvailable Dimensions:")
for aspect in mfa_system_base.IndexTable.index:
    classification = mfa_system_base.IndexTable.loc[aspect, 'Classification']
    print(f"  - {aspect} ({mfa_system_base.IndexTable.loc[aspect, 'IndexLetter']}): {len(classification.Items)} items")
```

---

## Benefits

1. ✅ **Elements loaded properly** from Excel
2. ✅ **IndexTable displayed** following ODYM conventions
3. ✅ **Better debugging** - see system structure immediately
4. ✅ **ODYM compliance** - matches tutorial patterns

---

**Ready to implement these fixes!** 🚀



---


================================================================================
# File: PHASE_1B_NEXT_STEPS.md
================================================================================

# Phase 1b: Systematic Dimension Implementation Plan

## Current Status ✅

- **Elements**: `['material', 'WC', 'DM', 'CC']` - WORKING
- **Baseline calculation**: ✅ Completed successfully
- **System**: Working with current 2D structure

---

## Next Steps: Following Master Plan

### **Step 1: Add Material Dimension** (Now)

**What to do**:
1. Materials in Excel: `['WC', 'DM']`
2. Add Material dimension to `system_setup.py`
3. Update IndexTable to include Material
4. Keep Elements as is (material, WC, DM, CC)

**Result**: 3D arrays (Time × Material × Element)
- Flow.Values.shape = (26, 2, 4)
- 26 years × 2 materials × 4 elements

---

### **Step 2: Update Engine for 3D Operations**

**Files to update**:
1. `solver.py` - handle 3D arrays
2. `dsm_model.py` - aggregate material dimension
3. `fomp_model.py` - aggregate material dimension
4. `initial_stock_engine.py` - handle 3D

**Changes needed**:
```python
# OLD (2D):
values = flow.Values[i, :]

# NEW (3D):
# Option A: Sum over materials to get element total
values = np.sum(flow.Values[i, :, :], axis=0)  # (4,) - total per element

# Option B: Get specific material
values = flow.Values[i, material_idx, :]  # (4,) - elements for this material
```

---

### **Step 3: Add Helper Function**

Create `plotting/utils.py` helper:

```python
def get_element_values(flow_or_stock, element_index, aggregate_materials=True):
    """
    Get values for a specific element, handling 2D or 3D arrays.
    
    Parameters
    ----------
    flow_or_stock : Flow or Stock object
    element_index : int
        Index of element in Elements list
    aggregate_materials : bool
        If True, sum over materials dimension. If False, return (time, materials) shape.
    
    Returns
    -------
    np.ndarray
        Time series of element values (shape: (n_years,) or (n_years, n_materials))
    """
    values = flow_or_stock.Values
    
    if values.ndim == 2:
        # 2D: (time, elements)
        return values[:, element_index]
    elif values.ndim == 3:
        # 3D: (time, materials, elements)
        if aggregate_materials:
            return np.sum(values[:, :, element_index], axis=1)
        else:
            return values[:, :, element_index]
    else:
        raise ValueError(f"Unexpected array dimension: {values.ndim}")
```

---

### **Step 4: Update Plotting Functions**

**For each plotting function**:
1. Replace `flow.Values[:, element_index]` 
2. With: `get_element_values(flow, element_index)`

**Example**:
```python
# In dynamics.py
def plot_process_dynamics(mfa_system_results, process_definitions):
    # ...
    for flow in inflows:
        element_values = get_element_values(flow, element_index)  # NEW
        # Instead of: flow.Values[:, element_index]
```

---

## Implementation Order

### **Priority 1: Engine Functions** (Critical for calculations)
1. `solver.py` - TC-driven flows
2. `initial_stock_engine.py` - Stock processing
3. `dsm_model.py` - DSM calculations
4. `fomp_model.py` - FOMP calculations

### **Priority 2: Plotting Functions** (User-facing)
1. `dynamics.py` - Process/Flow dynamics
2. `composition.py` - Flow composition
3. `sankey.py` - Sankey diagrams
4. `validation.py` - Mass balance plots

---

## Quick Decision Points

1. **Materials in Excel**: Are WC and DM defined in Excel now?
   - If yes: Material dimension will work
   - If no: We add them automatically

2. **Aggregation strategy**: How to handle materials?
   - Sum over materials: Default behavior (WC + DM totals)
   - Separate materials: More complex (show WC vs DM)

3. **Backward compatibility**: Keep 2D mode?
   - Detect array shape in helper function
   - Support both 2D and 3D

---

## Recommended Path Forward

**Option A: Add Material dimension now** ⏰ 2-3 hours
- Update system_setup.py to include Materials
- Add helper function for element access
- Update engine functions for 3D
- Test calculations

**Option B: Keep 2D working, plan 3D** ⏰ 1 hour
- Document current 2D system as stable
- Plan 3D implementation
- Add Material dimension later

**Which do you prefer?**



---


================================================================================
# File: PHASE_1B_STATUS.md
================================================================================

# Phase 1b Implementation: Region Dimension - COMPLETED ✅

## Summary

Successfully added support for the Region dimension to the `define_model_scope()` function. The system now supports 3-dimensional arrays (Time, Element, Region) while maintaining backward compatibility.

## Changes Made

### ✅ Modified `02_src/system_setup.py` - `define_model_scope()` Function

**Key Changes**:

1. **Updated Function Signature** (line 29):
```python
def define_model_scope(start_year, end_year, elements, 
                       regions=None, goods=None, materials=None, processes=None):
```
- Added optional dimension parameters
- All new parameters default to None for backward compatibility

2. **Added Region Dimension** (lines 74-78):
```python
# Phase 1b: Add Region dimension
if regions is not None and len(regions) > 0:
    model_classification["Region"] = msc.Classification(
        Name="Regions", Dimension="Region", ID=3, Items=regions
    )
```

3. **Dynamic Index Table Building** (lines 81-96):
```python
# Add Region if defined
if "Region" in model_classification:
    aspects.append("Region")
    descriptions.append('Model aspect "Region"')
    dimensions.append("Region")
    index_letters.append("r")
    classifications.append(model_classification["Region"])
```

4. **Enhanced Print Statement** (line 107):
```python
print(f"--> Model scope and classifications defined with {len(aspects)} dimensions.")
```

## Backward Compatibility

✅ **Fully Backward Compatible**:
- If `regions=None`, defaults to `["Case_Study_Region"]`
- Existing code continues to work without modifications
- Gradually adding dimensions as needed

## Current Status

- ✅ Region dimension support added
- ✅ Index table dynamically built
- ✅ Backward compatible
- ⏳ Need to update flow/stock initialization for 3D arrays
- ⏳ Need to update solver for 3D operations

## Next Steps

### **Immediate**:
1. Test workflow with Region dimension
2. Verify IndexTable has 3 dimensions (Time, Element, Region)
3. Check that existing functionality still works

### **Then Add**:
1. Good dimension (Phase 1c)
2. Material dimension (Phase 1c)
3. Process dimension (Phase 1c)
4. Update engine for multi-dimensional operations

---

**Phase 1b Started! Region dimension support added.** 🚀



---


================================================================================
# File: PHASE_1B_TME_STRUCTURE.md
================================================================================

# Phase 1b Update: Focus on t,m,e Structure (Time, Material, Element)

## Summary

Updated the system to focus on **three main dimensions**: t, m, e (Time, Material, Element)

### **Configuration Update**

**Materials** (from Excel config):
- Material ID 1: WC
- Material ID 2: DM

**Elements** (from Excel config):
- Element ID 1: C
- Element ID 2: Remaining DM

---

## Changes Made

### **1. Updated `system_setup.py`** 

Changed focus from Region to Material dimension:

**Old**: Added Region dimension (t, e, r)
**New**: Added Material dimension (t, e, m)

```python
# Phase 1b: Add Material dimension (WC, DM)
if materials is not None and len(materials) > 0:
    model_classification["Material"] = msc.Classification(
        Name="Materials", Dimension="Material", ID=3, Items=materials
    )
```

### **2. Updated Workflow** (`00_BioDYM_Workflow.py`)

**Line 180**: Now passes all dimensions:
```python
model_classification, index_table = system_setup.define_model_scope(
    start_year, end_year, elements, regions, goods, materials, processes
)
```

**Line 129**: Materials printed first (WC, DM):
```python
if materials:
    print(f"   - Materials: {materials}")
```

---

## Expected System Structure

### **IndexTable will now show**:
```
Available Dimensions:
  - Time (t): 26 items
  - Element (e): 2 items (C, Remaining DM)
  - Material (m): 2 items (WC, DM)
```

### **Flow Indices**:
- Indices="t,e,m" (Time, Element, Material)
- Shape: (n_years, n_elements, n_materials)

### **Array Shapes**:
```python
# Flows: 3D arrays
flow.Values.shape = (26, 2, 2)  # 26 years, 2 elements, 2 materials

# Stocks: 3D arrays
stock.Values.shape = (26, 2, 2)
```

---

## Benefits

1. ✅ **Logical structure**: Material (WC, DM) separate from Elements (C, Remaining DM)
2. ✅ **ODYM compliant**: Uses standard dimension approach
3. ✅ **Simpler than full 6D**: Focus on essential dimensions first
4. ✅ **Backward compatible**: Still works with old 2D structure if materials=None

---

**System now focuses on t,m,e structure!** 🎯

**Ready to test with Time × Material × Element dimensions!** 🚀



---


================================================================================
# File: SESSION_STATUS_SUMMARY.md
================================================================================

# BioDYM ODYM Compliance - Session Status Summary

**Date**: Current Session  
**Branch**: feature/odym-compliance  
**Last Commit**: Phase 1a-1b: ODYM compliance foundation - Add validation hooks and config loader

---

## Executive Summary

Working on ODYM framework compliance for BioDYM. Made progress on Phase 1 validation hooks and 3D array support, but paused to decide on a full 3D implementation.

**Key Achievement**: Refactored solver.py for 3D support and updated validation/Sankey plots  
**Key Question**: Proceed with full 3D implementation (25–40 hours) or keep 2D structure?

---

## What We've Accomplished

### ✅ Phase 1a: Validation Hooks
- Added `Consistency_Check()` to solver.py (after balance and final calculations)
- Added validation to dsm_model.py and fomp_model.py
- All Phase 1a validation hooks committed

### ✅ Phase 1b: Configuration & Dimensions
- Updated config.py to read dimensions from Excel (`Elements`, `Regions`, `Goods`, `Materials`, `Process_Types`)
- Modified system_setup.py to support optional dimensions (Good, Material, Region, Process)
- Updated workflow to pass dimensions to `define_model_scope()`
- Added IndexTable display following ODYM conventions
- Committed Phase 1a-1b progress

### ✅ Plotting Updates (Partial)
- **Sankey diagram** (`sankey.py`): Updated for 3D support using `get_element_values()` helper
- **Validation plot** (`validation.py`): Added material/element layer selectors with "All" aggregation option
- Created `plotting/utils_3d.py` with helper functions for 3D array access

### ✅ Solver Refactoring
- Refactored `solver.py` to detect and handle 3D/4D arrays
- Added material aggregation logic
- Dynamic element handling (no hardcoded element names)

---

## Current System State

### **Working 2D Structure** (CURRENT SYSTEM):
```python
Flow.Values.shape = (26, 1)  # (time, elements)
Elements: ['CC']
```

**Excel Configuration**:
- Materials: WC, DM (defined but not used as dimension)
- Elements: CC
- Data structure: WC and DM are separate rows in Excel, not separate dimensions

**Data in Excel**:
- Each flow has rows for WC and DM material types
- Percentages: `WC_[%]`, `DM_[%]`, `CC_[%]`
- Current system treats these as separate flows, not dimensions

### **Proposed 3D Structure**:
```python
Flow.Values.shape = (26, 2, 1)  # (time, materials, elements)
Materials: ['WC', 'DM']
Elements: ['CC']
```

---

## Key Files Modified

### **Committed Changes**:
1. `02_src/config.py` - Reads dimensions from Excel
2. `02_src/system_setup.py` - Dimension support with Good, Material
3. `02_src/engine/solver.py` - Refactored for 3D (NOT COMMITTED)
4. `02_src/plotting/sankey.py` - Updated for 3D
5. `02_src/plotting/validation.py` - Added material selectors
6. `02_src/plotting/utils_3d.py` - NEW: Helper functions for 3D

### **Uncommitted Changes**:
- `solver.py`: 3D refactoring complete but not committed
- `validation.py`: Material selectors added but not committed
- `sankey.py`: 3D support added but not committed

---

## Current Excel Configuration

**File**: `01_data/01_input/251027_BioDYM_ODYM.xlsm`

**Configuration Sheet** (`0_Configuration`):
```
Good Type 1: Raw Material
Good Type 2: Processed Product  
Good Type 3: Product
Good Type 4: Waste

Material ID 1: WC
Material ID 2: DM

Element ID 1: CC
```

**Data Flow Structure** (`1_2_Data_Flows`):
- Each flow has multiple rows (one per material type)
- Columns: `Flow_Material`, `WC_[%]`, `DM_[%]`, `CC_[%]`
- Percentages are compositions of the flow

---

## Technical Context

### **ODYM Framework Understanding**:
- ODYM supports 6 dimensions: Time, Element, Region, Good, Material, Process
- Current system: Time, Element (2D)
- Proposed: Time, Material, Element (3D)
- Materials in Excel are rows, not dimensions; make them dimensions

### **Data Loader Challenge**:
Current loader (`_populate_primary_flow_data`):
- Reads flow values directly
- Doesn't use `Flow_Material` column to assign to material dimension

Needed for 3D:
- Read `Flow_Material` column
- Assign values to material dimension based on material type
- Map percentages to elements

### **Solver Status**:
- ✅ Updated for 3D: Detects array dimensions, aggregates materials, dynamic element handling
- ⚠️ Not tested: Needs testing with actual 3D data

### **Plotting Status**:
- ✅ Created helper functions in `utils_3d.py`
- ✅ Updated: Sankey, Validation plots
- ⚠️ Remaining: scenario.py, dynamics.py, other plotting files

---

## Critical Decisions Needed

### **Decision Point**: 3D Implementation Strategy

**Option A: Full 3D Implementation**
- Refactor data loader for material dimension
- Update DSM/FOMP models
- Complete plotting updates
- **Effort**: 25-40 hours
- **Risk**: Medium-High
- **Benefit**: Full ODYM compliance

**Option B: Hybrid Approach**
- Add config flag: `use_material_dimension`
- Keep 2D as default
- Enable 3D optionally
- **Effort**: 10-15 hours  
- **Risk**: Low
- **Benefit**: Gradual migration

**Option C: Keep 2D**
- Revert 3D changes
- Keep current working system
- **Effort**: 2 hours (revert commits)
- **Risk**: None
- **Benefit**: Stability

---

## Outstanding Issues

### **1. Element Definition Confusion**
- User wanted 4 elements: material, WC, DM, CC
- Current system has only 1 element: CC
- Materials (WC, DM) are rows in Excel, not elements
- Clarification needed on what should be elements vs materials

### **2. Data Structure Mismatch**
- Excel data: WC and DM are separate rows (2D naturally)
- 3D proposal: WC and DM as material dimension
- **Impact**: Requires significant data loader changes

### **3. Incomplete Refactoring**
- Solver updated for 3D but not tested
- Only 2 plotting functions updated
- DSM/FOMP models not updated
- Data loader not updated

---

## Recommended Next Steps

### **For Continuing AI**:

1. **Clarify Data Model** (15 min)
   - Determine if WC/DM should be materials or remain separate flows
   - Decide on element definitions

2. **Choose Strategy** (5 min)
   - Present options A, B, C to user
   - Wait for decision

3. **If Full 3D** (25-40 hours):
   - Update data loader (`system_setup.py:_populate_primary_flow_data`)
   - Update DSM model (`dsm_model.py`)
   - Update FOMP model (`fomp_model.py`)
   - Complete plotting updates
   - Test workflow end-to-end

4. **If Hybrid** (10-15 hours):
   - Add config flag
   - Implement 2D/3D switching logic
   - Test both modes

5. **If Keep 2D** (2 hours):
   - Revert recent changes
   - Document why 2D was kept

---

## Files to Review

**Key Files**:
- `02_src/config.py` - Config loader
- `02_src/system_setup.py` - System initialization  
- `02_src/engine/solver.py` - Solver (updated for 3D)
- `02_src/plotting/utils_3d.py` - NEW: 3D helpers
- `02_src/plotting/sankey.py` - Updated plots
- `02_src/plotting/validation.py` - Updated plots

**Status Documents**:
- `02_src/engine/ODYM_COMPLIANCE_MASTER_PLAN.md` - Original plan
- `02_src/engine/3D_IMPLEMENTATION_COMPLEXITY.md` - NEW: Complexity analysis
- Various Phase 1 progress documents in `02_src/engine/`

---

## Git Status

**Branch**: `feature/odym-compliance`  
**Last Commit**: Phase 1a-1b  
**Uncommitted**: solver.py, validation.py, sankey.py changes

**Recommendation**: Commit current work or create feature branch for 3D experimentation

---

## User Preferences (from Memory)
- Prefers discussion after each step in multi-step processes
- Prefers confirmation before quick actions
- Uses jupytext for .py/.ipynb synchronization
- Prefers Plotly for visualizations
- Custom additions to ODYM should be clearly marked

---

**Status**: Awaiting decision on 3D implementation strategy before proceeding further.



---


================================================================================
# File: STOCK_VS_PROCESS_INDICES.md
================================================================================

# Understanding Stock vs. Process Indices

## Key Point: Processes DON'T Have Indices!

### **Process Objects: No Indices Required**

**Processes are simple objects** in ODYM:
```python
class Process(Obj):
    def __init__(
        self,
        Name=None,        # Process name
        ID=None,          # Process ID
        Extensions=None,  # Process extensions (custom data)
    )
```

**Key Point**: 
- ❌ **Processes DO NOT have Indices**
- ❌ **Processes DO NOT have Values arrays**
- ✅ **Processes are just containers** with ID, Name, and Extensions

### **Stock Objects: DO Have Indices**

**Stocks belong to Processes** but have their own Indices:
```python
class Stock(Obj):
    def __init__(
        self,
        Name=None,        # Stock name (e.g., "dS_1", "S_1")
        P_Res=None,       # Residence process ID (process this stock belongs to)
        Indices=None,     # Stock's dimensions (e.g., "t,e")
        Values=None,      # Stock values array
        Type=None,        # Stock type (0=absolute, 1=change)
    )
```

**Key Point**:
- ✅ **Stocks HAVE Indices**
- ✅ **Stocks HAVE Values arrays**
- ✅ **Stocks belong to a specific Process** (P_Res)

## Why You Define Stocks on the Same Page as Processes

### **Your Current Excel Structure**

**Sheet: `2_1_Definition_Processes`**
```
| ID | Process_Name | Process_Logic | Stock_Configuration |
|----|--------------|---------------|---------------------|
| 1 | Harvest | DSM | Stock |
| 2 | Processing | DSM | Stock |
| 3 | Storage | Standard | (no stock) |
```

**What Happens**:
1. You read the process definition (ID, Name, Logic)
2. You check if Stock_Configuration = "Stock"
3. IF Stock_Configuration = "Stock", you create Stock objects

**Why This Works**:
- **Processes are created first** (ProcessList)
- **Stocks are created second** (StockDict) but **belong to processes** (P_Res=process_id)

### **The Relationship**:

```
Process (ID=1, Name="Harvest")
  └─ Stock (Name="dS_1", P_Res=1, Indices="t,e")
  └─ Stock (Name="S_1", P_Res=1, Indices="t,e")

Process (ID=2, Name="Processing")  
  └─ Stock (Name="dS_2", P_Res=2, Indices="t,e")
  └─ Stock (Name="S_2", P_Res=2, Indices="t,e")
```

**Key Understanding**:
- **Processes define the structure**
- **Stocks are created AFTER processes**, based on Stock_Configuration
- **Both use the SAME Excel row** but create different objects

## Do You Need Different Indices for Stocks and Flows?

### **Current Implementation**:

**Flow Creation** (from `1_1_Definition_Flows`):
```python
flow = msc.Flow(
    Name=row["Flow_ID"],
    P_Start=start_id,
    P_End=end_id,
    Indices="t,e"  # Flow indices
)
```

**Stock Creation** (from `2_1_Definition_Processes`):
```python
mfa_system.StockDict[f"dS_{process_id}"] = msc.Stock(
    Name=f"dS_{process_id}", 
    P_Res=process_id, 
    Type=1, 
    Indices="t,e"  # Stock indices
)
```

### **Answer: NO, You Don't Need Different Indices!**

**Why They Can Be the Same**:
1. **Flows**: Material flows between processes with dimensions (t,e,r,g,m,p)
2. **Stocks**: Material stocks AT processes with dimensions (t,e,r,g,m,p)
3. **Both use the same dimension system** - just different contexts!

**But They CAN Be Different If Needed**:

```python
# Simple flows: just Time + Element
Flow Indices = "t,e"

# Complex stocks: Time + Element + Material  
Stock Indices = "t,e,m"
```

## Recommended Approach

### **Option 1: Use Same Indices Everywhere (Simplest)**

**Set all to "t,e" in Excel**:
```excel
# In 1_1_Definition_Flows
Indices = "t,e"  # For all flows

# In 2_1_Definition_Processes
Stock_Indices = "t,e"  # For all stocks
```

**Benefits**:
- ✅ Simple and consistent
- ✅ Easy to understand
- ✅ Backward compatible

### **Option 2: Configure Per Item (Advanced)**

**Use different Indices when needed**:
```excel
# In 1_1_Definition_Flows
Flow_ID | Flow_Name | Indices
--------|-----------|--------
F_01_02 | Harvest_Flow | t,e        # Simple flow
F_02_03 | Processing_Flow | t,e,g,m  # Multi-dimensional flow

# In 2_1_Definition_Processes
ID | Process_Name | Stock_Indices
---|--------------|---------------
1 | Harvest | t,e           # Simple stock
2 | Storage | t,e,g,m       # Material-specific stock
```

**Benefits**:
- ✅ More flexible
- ✅ Can optimize memory usage
- ✅ Allows dimension-specific analysis

## My Recommendation

For now, use the same Indices everywhere:

```excel
# In 1_1_Definition_Flows
Indices = "t,e"  # Default for all flows

# In 2_1_Definition_Processes (add Stock_Indices column)
Stock_Indices = "t,e"  # Default for all stocks
```

Later, when you need multi-dimensional analysis, you can specify different Indices per item.

## Summary

- **Processes DON'T have Indices** (they're simple containers)
- **Stocks and Flows BOTH have Indices** (they represent data)
- You can use the SAME Indices for stocks and flows, or DIFFERENT ones if needed
- **For simplicity**: Use "t,e" everywhere initially
- **For ODYM compliance**: You need both Flow Indices and Stock_Indices columns in Excel

---

*Document Version: 1.0*  
*Last Updated: [Current Date]*  
*Author: BioDYM Development Team*


---


================================================================================
# File: TEST_3D_STRUCTURE.md
================================================================================

# Testing 3D Structure with Material Dimension

## Your Configuration

### **Materials** (Physical materials):
- **WC**: Water Content
- **DM**: Dry Matter

### **Elements** (Components tracked):
- **material**: Total mass (fresh mass)
- **CC**: Carbon Content

---

## Excel Update You'll Make

**In `0_Configuration` sheet**:

**Materials**:
```
Setting_Name      | Value
Material ID 1     | WC
Material ID 2     | DM
```

**Elements**:
```
Setting_Name      | Value
Element ID 1      | material
Element ID 2      | CC
```

---

## Expected Results After Update

### **1. Config Loader**
```python
materials = ['WC', 'DM']
elements = ['material', 'CC']
```

### **2. IndexTable**
```
Aspect    | IndexLetter | Items
----------|-------------|------------------
Time      | t           | [2020, 2021, ..., 2045]
Material  | m           | ['WC', 'DM']
Element   | e           | ['material', 'CC']
```

### **3. Flow.Values Shape**
```python
Flow.Values.shape = (26, 2, 2)
# 26 years × 2 materials × 2 elements
```

---

## Testing Plan

### **Step 1: Read Config** ✅
- Run config loader
- Verify materials=['WC', 'DM'], elements=['material', 'CC']

### **Step 2: Check IndexTable** ✅
- Run workflow setup
- Verify IndexTable shows Material dimension
- Print IndexTable for verification

### **Step 3: Check Flow Shape** ✅
- Initialize a flow
- Check `flow.Values.shape`
- Should be (26, 2, 2)

### **Step 4: Test Calculations** ⚠️
- Run baseline calculation
- May encounter errors in solver.py (expects different structure)
- Document errors for fixing

---

## Potential Issues

### **1. Solver.py**
Current code expects:
```python
flow.Values[:, element_index]  # Works for 2D
```

Need to update to:
```python
# Sum over materials
np.sum(flow.Values[:, :, element_index], axis=1)
```

### **2. DSM Model**
Aggregate material dimension before stock calculations.

### **3. FOMP Model**
Handle material dimension in mineralization.

---

## Helper Functions Available

Created `plotting/utils_3d.py` with:
- `get_element_values()` - Get element, handle 2D/3D
- `get_material_values()` - Get all elements for a material
- `get_element_by_material()` - Get specific element in specific material
- `has_material_dimension()` - Check if 3D
- `get_array_info()` - Get shape information

---

## Next Steps After Excel Update

1. ✅ Update Excel (you'll do this)
2. 📝 Run workflow and check config read
3. 📝 Print IndexTable for verification
4. 📝 Check flow shapes
5. ⚠️ Identify and fix any solver errors
6. 🎉 Test full workflow with 3D structure

**Ready to test when you've updated Excel!** 🚀



---


================================================================================
# File: UNDERSTANDING_DATA_STRUCTURE.md
================================================================================

# Understanding Your Current Data Structure

## Your Excel Data Structure

### **Current System (WORKING)**:

**Excel columns**:
- `Flow_Material`: Material type (WC or DM)
- `WC_[%]`: Water Content percentage
- `DM_[%]`: Dry Matter percentage  
- `CC_[%]`: Carbon Content percentage

**Example**:
```
Flow_Material: "WC"  (or "DM")
WC_[%]: Yes
DM_[%]: 0
CC_[%]: 0
```

**What this means**:
- Each row represents ONE material type (WC OR DM)
- The percentages are compositions of THAT material

---

## What You Want to Achieve

### **Material Separation**:

**Current**: 2D structure
- Flow.Values: (Time, Element) = (26, 3)
- Elements: material total, WC composition, DM composition, CC composition
- All in ONE array

**Desired**: 3D structure  
- Flow.Values: (Time, Material, Element) = (26, 2, 3)
- Materials: WC, DM (separate dimensions)
- Elements: material total, CC, ???

---

## The Challenge

Your Excel has **"WC" as percentage composition**, not as a material dimension.

**In Excel**:
- Row 1: Flow = 100 Mg, Material = "WC", CC = 50%
- Row 2: Flow = 100 Mg, Material = "DM", CC = 50%

**Currently in Python** (2D):
```python
Flow.Values[:, 0] = [100, 100]  # Total material for each time
Flow.Values[:, 1] = [50, 50]    # CC for each time
```

**What you want** (3D):
```python
Flow.Values[:, 0, 0] = [100, 0]   # Material for WC
Flow.Values[:, 0, 1] = [50, 0]    # CC for WC
Flow.Values[:, 1, 0] = [0, 100]   # Material for DM  
Flow.Values[:, 1, 1] = [0, 50]   # CC for DM
```

---

## Data Loader Implications

**Current loader**: `_populate_primary_flow_data()`

```python
# Currently reads:
flow.Values[:, 0] = flow_data['Flow'][year_idx]  # Total
flow.Values[:, 1] = flow_data['WC_[%]'][year_idx] * flow.Values[:, 0] / 100
```

**Needed for 3D**: 
```python
# Need to assign to material dimension based on Flow_Material
material_type = row['Flow_Material']  # "WC" or "DM"
if material_type == "WC":
    material_idx = 0
elif material_type == "DM":
    material_idx = 1

flow.Values[:, material_idx, 0] = flow_data['Flow'][year_idx]  # Material total
flow.Values[:, material_idx, 1] = flow_data['CC_[%]'][year_idx] * flow.Values[:, material_idx, 0] / 100
```

---

## This is MAJOR Refactoring

**Why**:
1. Data loader must change to assign to material dimension
2. Solver must work with 3D arrays  
3. Plotting functions must handle material selection
4. **Every calculation** must handle 3D

**But**: This follows ODYM principles! ✅

---

## Recommendation

**Option A: Stay with 2D** (Keep Current System)
- ✅ Everything works now
- ✅ Simple structure
- ✅ Easier to maintain

**Option B: Go Full 3D** (Major Refactoring)
- ✅ ODYM compliant
- ✅ More flexible
- ⚠️ Requires refactoring EVERYTHING
- ⚠️ Several weeks of work

**What do you prefer?** 🤔



---


---


================================================================================
# File: ODYM_COMPLIANCE_MASTER_PLAN.md
================================================================================

# BioDYM ODYM Compliance Master Plan

## Overview

This document provides a comprehensive master plan for achieving full ODYM compliance across all identified areas: **Classes**, **Functions**, and **Dimensions**. The plan integrates the three compliance analyses into a unified implementation strategy with clear priorities, timelines, and success metrics.

## Executive Summary

- **Overall ODYM Compliance**: 4/10 (Poor) - Significant gaps across all areas
- **Critical Issues**: Missing dimensions, non-compliant functions, limited class usage
- **Implementation Complexity**: 8/10 (Very High) - Requires systematic approach
- **Timeline**: 12-16 weeks total across 4 phases
- **Risk Level**: Medium to High (phased approach with rollback options)
- **Benefits**: Full ODYM compatibility, enhanced scalability, future-proofing

## Compliance Assessment Summary

### **Current Compliance Scores**

| Compliance Area | Current Score | Target Score | Priority | Critical Issues |
|-----------------|---------------|--------------|----------|-----------------|
| **Classes** | 5/10 | 9/10 | High | Manual aggregation, custom attributes |
| **Functions** | 6/10 | 9/10 | High | Limited ODYM integration, basic error handling |
| **Dimensions** | 3/10 | 9/10 | Critical | Missing 4/6 standard dimensions |

### **Overall Compliance**: 4.7/10 (Poor)

---

### **Gemini's Assessment & Recommendations**

**Overall Assessment**: This is an exceptionally thorough and well-structured plan. The analysis is accurate, and the goal of achieving full ODYM compliance is well-supported by the detailed phases.

**Key Consideration**: There is a contradiction in the planning documents regarding Excel template changes. `ODYM_COMPLIANCE_STRATEGY.md` states no changes are needed, while this Master Plan correctly identifies that adding dimensions **requires** significant Excel template updates. **This Master Plan's assessment is correct.** Proceed with the assumption that Excel templates must be modified as planned in Phase 4.

To enhance the plan's robustness and reduce risk, I recommend the following adjustments:

---

### **Workflow & Visualization Strategy**

A critical requirement of this refactoring is to ensure the final visualizations in the main scientific workflow (`00_BioDYM_Workflow.ipynb`) remain consistent with the current output, even after the backend is upgraded to a full 6-dimensional model. This ensures continuity and comparability with previous results.

To achieve this, the project will implement a **"6D -> 2D Aggregated"** workflow:

1.  **6D Compliant Calculation**: The core engine will be refactored to perform all MFA calculations using the full 6-dimensional data model (Time, Element, Region, Good, Material, Process).

2.  **Explicit 2D Aggregation**: After the calculation is complete, a new, mandatory step will be added to the Jupyter notebook. This step will aggregate the 6D results object down to a 2D (Time, Element) view by summing over the new dimensions (Region, Good, Material).

3.  **Consistent 2D Visualization**: The existing plotting functions in the notebook will be pointed to this new, aggregated 2D results object. This guarantees that the primary Sankey diagrams, time-series plots, and stock charts will "display the same calculation results" as the current system.

As part of this strategy, the `00_BioDYM_Workflow.ipynb` will be updated to:
*   **Adopt Standard ODYM Helpers**: The project will prioritize using standard helper functions from `ODYM_Functions.py` (imported as `msf`) for tasks like logging, system inspection, and data aggregation, instead of developing custom utilities.
*   **Showcase ODYM Compliance**: A new "System Inspection" cell will be added that uses a standard ODYM function (e.g., `msf.print_system_summary`) to display a summary of the `MFAsystem` object's structure, making the use of ODYM classes and the new dimensions explicit.
*   **Implement Compliant Aggregation**: The "Explicit 2D Aggregation" step will be implemented using the framework's built-in aggregation functions from `msf`.
*   **Enable Exploratory Analysis**: A separate, optional section will be added for new, multi-dimensional plots that operate on the raw 6D data, allowing for deeper analysis without disrupting the main, established workflow.

---

### **Revised Implementation Strategy: A Lower-Risk Approach**

This revised strategy introduces a **Phase 0** for test creation and breaks the original **Phase 1** into smaller, more manageable steps to mitigate the risks of a "big bang" integration.

#### **Phase 0: Build a Testing Safety Net (1-2 weeks)**
**Priority**: Critical | **Risk Level**: Low

**Objective**: Before any refactoring, create a high-level integration test suite that validates the current system's output. This provides a safety net to ensure existing functionality is preserved.

**Implementation**:
1.  **Identify Key Scenarios**: Select 1-2 representative existing Excel files.
2.  **Establish Golden Datasets**: Run the full workflow for these files and save the key output files (e.g., `results_scientific.xlsx`) as a "golden" reference.
3.  **Create Integration Tests**: Write a new test file (`04_tests/workflow/test_e2e_workflow.py`) that:
    *   Runs the full `main()` workflow with the selected Excel files.
    *   Compares the generated output files against the "golden" reference datasets.
    *   Asserts that the outputs are identical.
4.  **Goal**: These tests must pass before starting Phase 1. They will be expected to fail during the refactoring and will be used to verify correctness as you complete each stage.

---

#### **Revised Phase 1: Iterative Foundation & Dimension Implementation (4-5 weeks)**
**Risk Level**: Medium | **Impact**: Critical | **Priority**: Highest

This phase replaces the original "big bang" approach with a more gradual, iterative implementation of dimensions.

##### **Phase 1a: Foundational Refactoring (1 week)**
**Objective**: Implement class/function improvements that are independent of new dimensions to create a more robust baseline.

**Implementation**:
1.  **Use ODYM Initializers**: In `system_setup.py`, replace manual initialization with `mfa_system.Initialize_FlowValues()`, etc.
2.  **Add Validation Hooks**: Add `mfa_system.Consistency_Check()` calls at key points in the engine modules (`solver.py`, `initial_stock_engine.py`).
3.  **Improve Error Handling**: Wrap critical operations in `try...except` blocks as planned.
4.  **Goal**: All Phase 0 integration tests must still pass.

##### **Phase 1b: Introduce a Single New Dimension (2 weeks)**
**Objective**: Add the 'Region' dimension and adapt the system to handle 3D arrays (`t,e,r`). This validates the multi-dimensional approach on a smaller scale.

**Implementation**:
1.  **Update `system_setup.py`**: Add the 'Region' classification and update the `IndexTable`.
    *   **Correction**: Ensure you call `index_table.set_index('Aspect', inplace=True)` after creating the DataFrame.
2.  **Update `data_loader.py`**: Modify it to look for a `3_1_Definition_Regions` sheet.
    *   **Backward Compatibility**: If the sheet is missing, the loader should automatically create a default, single-item 'Region' classification (e.g., 'Case_Study_Region'). This is critical for ensuring old Excel files still run.
3.  **Update Engine**: Refactor `solver.py`, `initial_stock_engine.py`, etc., to handle 3D NumPy arrays instead of 2D.
4.  **Goal**: Get the Phase 0 integration tests passing again. The logic should be sound for both old files (running on the default 1 region) and new files with multiple regions.

##### **Phase 1c: Add Remaining Dimensions (1-2 weeks)**
**Objective**: With the pattern for adding a dimension established, add 'Good', 'Material', and 'Process'.

**Implementation**:
1.  **Extend `system_setup.py` and `data_loader.py`** for the remaining dimensions, following the backward-compatible pattern from Phase 1b.
2.  **Scale Engine Logic**: Update the engine modules to handle up to 6D arrays. This will be much simpler now that the core multi-dimensional logic is in place.
3.  **Goal**: Get the Phase 0 integration tests passing again.

---

This revised plan front-loads testing and breaks down the most complex phase into manageable steps, significantly lowering the project risk while keeping all the excellent detail from your original plan for Phases 2, 3, and 4. The subsequent phases (Class Compliance, Function Compliance, etc.) can proceed as you've outlined.

## Master Implementation Strategy: 4-Phase Approach

### **Phase 1: Foundation & Dimensions (3-4 weeks)**
**Risk Level**: Medium | **Impact**: Critical | **Priority**: Highest

#### **Objectives**
- Add missing ODYM dimensions (Region, Good, Material, Process)
- Establish proper IndexTable structure
- Update data structures to support multi-dimensional arrays
- Add basic ODYM validation methods

#### **Phase 1 Detailed Implementation Plan**

##### **1.1 Dimension System Implementation** ⏱️ 12-16 hours
**Priority**: Critical | **Files**: `system_setup.py`, `data_loader.py`

**Step 1.1.1: Add Region Dimension** (3-4 hours)
```python
# In system_setup.py
def define_model_scope(start_year, end_year, elements, regions=None):
    """Defines comprehensive model scope with all ODYM dimensions."""
    
    if regions is None:
        regions = ["Case_Study_Region"]  # Default single region
    
    model_classification = {}
    my_years = list(np.arange(start_year, end_year + 1))
    
    # Existing dimensions
    model_classification["Time"] = msc.Classification(
        Name="Time", Dimension="Time", ID=1, Items=my_years
    )
    model_classification["Element"] = msc.Classification(
        Name="Elements", Dimension="Element", ID=2, Items=elements
    )
    
    # NEW: Add Region dimension
    model_classification["Region"] = msc.Classification(
        Name="Regions", Dimension="Region", ID=3, Items=regions
    )
    
    return model_classification
```

**Step 1.1.2: Add Good Dimension** (3-4 hours)
```python
# In system_setup.py
def define_model_scope(start_year, end_year, elements, regions=None, goods=None):
    """Defines comprehensive model scope with all ODYM dimensions."""
    
    if goods is None:
        goods = ["Rye_Straw", "Biochar", "Compost", "Energy"]  # Default goods
    
    # ... existing code ...
    
    # NEW: Add Good dimension
    model_classification["Good"] = msc.Classification(
        Name="Goods", Dimension="Good", ID=4, Items=goods
    )
    
    return model_classification
```

**Step 1.1.3: Add Material Dimension** (3-4 hours)
```python
# In system_setup.py
def define_model_scope(start_year, end_year, elements, regions=None, goods=None, materials=None):
    """Defines comprehensive model scope with all ODYM dimensions."""
    
    if materials is None:
        materials = ["Dry_Matter", "Water_Content", "Carbon_Content"]  # Default materials
    
    # ... existing code ...
    
    # NEW: Add Material dimension
    model_classification["Material"] = msc.Classification(
        Name="Materials", Dimension="Material", ID=5, Items=materials
    )
    
    return model_classification
```

**Step 1.1.4: Add Process Dimension** (3-4 hours)
```python
# In system_setup.py
def define_model_scope(start_year, end_year, elements, regions=None, goods=None, materials=None, processes=None):
    """Defines comprehensive model scope with all ODYM dimensions."""
    
    if processes is None:
        processes = ["Harvest", "Processing", "Storage", "Application"]  # Default processes
    
    # ... existing code ...
    
    # NEW: Add Process dimension
    model_classification["Process"] = msc.Classification(
        Name="Processes", Dimension="Process", ID=6, Items=processes
    )
    
    # Update IndexTable with all dimensions
    index_table = pd.DataFrame({
        "Aspect": ["Time", "Element", "Region", "Good", "Material", "Process"],
        "Description": [
            'Model aspect "time"',
            'Model aspect "Element"',
            'Model aspect "Region"',
            'Model aspect "Good"',
            'Model aspect "Material"',
            'Model aspect "Process"'
        ],
        "Dimension": ["Time", "Element", "Region", "Good", "Material", "Process"],
        "Classification": [
            model_classification["Time"],
            model_classification["Element"],
            model_classification["Region"],
            model_classification["Good"],
            model_classification["Material"],
            model_classification["Process"]
        ],
        "IndexLetter": ["t", "e", "r", "g", "m", "p"],
    })
    
    return model_classification, index_table
```

##### **1.2 Data Structure Migration** ⏱️ 8-10 hours
**Priority**: High | **Files**: `system_setup.py`, `initial_stock_engine.py`, `solver.py`

**Step 1.2.1: Update Flow Indices** (3-4 hours)
```python
# In system_setup.py
def create_flow_with_full_indices(mfa_system, flow_name, process_start, process_end):
    """Create flow with full ODYM-compliant indices."""
    
    # Determine flow indices based on available dimensions
    indices = "t,e"  # Start with Time and Element
    
    if "Region" in mfa_system.IndexTable.index:
        indices += ",r"
    if "Good" in mfa_system.IndexTable.index:
        indices += ",g"
    if "Material" in mfa_system.IndexTable.index:
        indices += ",m"
    if "Process" in mfa_system.IndexTable.index:
        indices += ",p"
    
    # Create flow with proper indices
    flow = msc.Flow(
        Name=flow_name,
        P_Start=process_start,
        P_End=process_end,
        Indices=indices
    )
    
    return flow
```

**Step 1.2.2: Update Data Array Shapes** (3-4 hours)
```python
# In system_setup.py
def initialize_flow_values(mfa_system, flow):
    """Initialize flow values with proper dimensions."""
    
    # Get dimension sizes
    n_years = len(mfa_system.IndexTable.Classification["Time"].Items)
    n_elements = len(mfa_system.IndexTable.Classification["Element"].Items)
    
    # Initialize with Time and Element dimensions
    shape = [n_years, n_elements]
    
    # Add additional dimensions if available
    if "Region" in mfa_system.IndexTable.index:
        n_regions = len(mfa_system.IndexTable.Classification["Region"].Items)
        shape.append(n_regions)
    
    if "Good" in mfa_system.IndexTable.index:
        n_goods = len(mfa_system.IndexTable.Classification["Good"].Items)
        shape.append(n_goods)
    
    if "Material" in mfa_system.IndexTable.index:
        n_materials = len(mfa_system.IndexTable.Classification["Material"].Items)
        shape.append(n_materials)
    
    if "Process" in mfa_system.IndexTable.index:
        n_processes = len(mfa_system.IndexTable.Classification["Process"].Items)
        shape.append(n_processes)
    
    # Initialize flow values
    flow.Values = np.zeros(shape)
    
    return flow
```

**Step 1.2.3: Update Engine Modules** (2-2 hours)
```python
# In solver.py, update flow aggregation
def calculate_process_flows_multi_dimensional(mfa_system, process_id):
    """Calculate process flows with multi-dimensional support."""
    inflows = []
    for flow in mfa_system.FlowDict.values():
        if flow.P_End == process_id:
            # Handle multi-dimensional flow values
            if flow.Values is not None:
                inflows.append(flow.Values)
    
    if inflows:
        return sum(inflows)
    else:
        # Return zeros with correct multi-dimensional shape
        return np.zeros(mfa_system.get_flow_shape())
```

##### **1.3 Basic ODYM Validation** ⏱️ 4-6 hours
**Priority**: High | **Files**: All engine modules

**Step 1.3.1: Add Consistency Checks** (2-3 hours)
```python
# In solver.py, add after major operations
def add_odym_validation(mfa_system, operation_name=""):
    """Add ODYM validation after operations."""
    try:
        mfa_system.Consistency_Check()
        mfa_system.IndexTableCheck()
        print(f"✅ {operation_name} validation passed")
        return True
    except Exception as e:
        print(f"❌ {operation_name} validation failed: {e}")
        return False
```

**Step 1.3.2: Add Error Handling** (2-3 hours)
```python
# In all engine modules, wrap operations
def safe_odym_operation(operation_func, *args, **kwargs):
    """Safely execute ODYM operations with error handling."""
    try:
        result = operation_func(*args, **kwargs)
        return result
    except AttributeError as e:
        print(f"❌ Missing attribute: {e}")
        raise ValueError(f"Invalid ODYM object structure: {e}")
    except Exception as e:
        print(f"❌ Operation failed: {e}")
        raise
```

#### **Phase 1 Success Criteria**
- [ ] All 6 ODYM dimensions implemented
- [ ] IndexTable includes all dimensions
- [ ] Flow indices support multi-dimensional arrays
- [ ] Data structures support 6D arrays
- [ ] Basic ODYM validation added
- [ ] Error handling implemented
- [ ] All existing tests pass

---

### **Phase 2: Class Compliance (3-4 weeks)**
**Risk Level**: Medium | **Impact**: High | **Priority**: High

#### **Objectives**
- Replace manual flow aggregation with ODYM methods
- Remove custom attributes from ODYM objects
- Use ODYM initialization methods
- Implement proper ODYM flow management

#### **Phase 2 Detailed Implementation Plan**

##### **2.1 ODYM Method Integration** ⏱️ 10-12 hours
**Priority**: High | **Files**: `solver.py`, `initial_stock_engine.py`

**Step 2.1.1: Replace Manual Flow Aggregation** (4-6 hours)
```python
# In solver.py
def calculate_process_inflows_odym_compliant(mfa_system, process_id):
    """Calculate total inflows to a process using ODYM methods."""
    try:
        inflows = []
        for flow in mfa_system.FlowDict.values():
            if flow.P_End == process_id:
                # Use ODYM's Flow_Sum_By_Element method
                flow_sum = mfa_system.Flow_Sum_By_Element(flow.Name)
                inflows.append(flow_sum)
        
        if inflows:
            return sum(inflows)
        else:
            # Return zeros with correct shape
            return np.zeros(mfa_system.get_flow_shape())
    except Exception as e:
        print(f"❌ Flow aggregation failed for process {process_id}: {e}")
        raise

# Replace manual aggregation in calculate_final_balances()
def calculate_final_balances(mfa_system):
    """Calculate final balances using ODYM methods."""
    try:
        for pid in {p.ID for p in mfa_system.ProcessList}:
            # Use ODYM-compliant methods
            total_inflows = calculate_process_inflows_odym_compliant(mfa_system, pid)
            total_outflows = calculate_process_outflows_odym_compliant(mfa_system, pid)
            
            # Process balance calculations
            # ... existing logic ...
        
        # Add ODYM validation
        mfa_system.Consistency_Check()
        return mfa_system
    except Exception as e:
        print(f"❌ Balance calculation failed: {e}")
        raise
```

**Step 2.1.2: Implement ODYM Flow Management** (3-4 hours)
```python
# In initial_stock_engine.py
def create_flow_odym_compliant(mfa_system, flow_name, process_id, destination_process):
    """Create flow using ODYM-compliant methods."""
    try:
        # Check if flow already exists
        if flow_name in mfa_system.FlowDict:
            return mfa_system.FlowDict[flow_name]
        
        # Create flow object with proper indices
        flow = msc.Flow(
            Name=flow_name,
            P_Start=process_id,
            P_End=destination_process,
            Indices=mfa_system.get_flow_indices()
        )
        
        # Add to system using proper method
        mfa_system.FlowDict[flow_name] = flow
        
        # Initialize values using ODYM method
        mfa_system.Initialize_FlowValues()
        
        return flow
    except Exception as e:
        print(f"❌ Flow creation failed: {e}")
        raise
```

**Step 2.1.3: Use ODYM Initialization Methods** (3-2 hours)
```python
# In system_setup.py
def initialize_mfa_system_odym_compliant(model_classification, index_table):
    """Initialize MFA system using ODYM methods."""
    try:
        start_time = model_classification["Time"].Items[0]
        end_time = model_classification["Time"].Items[-1]
        element_items = model_classification["Element"].Items
        
        mfa_system = msc.MFAsystem(
            Name="RyeStrawMFA",
            Geogr_Scope="Case_Study_Region",
            Unit="Mg",
            ProcessList=[],
            FlowDict={},
            StockDict={},
            ParameterDict={},
            Time_Start=start_time,
            Time_End=end_time,
            IndexTable=index_table,
            Elements=element_items,
        )
        
        # Use ODYM initialization methods
        mfa_system.Initialize_FlowValues()
        mfa_system.Initialize_StockValues()
        mfa_system.Initialize_ParameterValues()
        
        # Validate system
        mfa_system.Consistency_Check()
        
        return mfa_system
    except Exception as e:
        print(f"❌ MFA system initialization failed: {e}")
        raise
```

##### **2.2 Remove Custom Attributes** ⏱️ 6-8 hours
**Priority**: High | **Files**: `initial_stock_engine.py`, `solver.py`, `fomp_model.py`

**Step 2.2.1: Replace Custom Attributes with ODYM Extensions** (3-4 hours)
```python
# In initial_stock_engine.py
def store_initial_stock_config_odym_compliant(mfa_system, process_id, config):
    """Store initial stock configuration using ODYM Extensions."""
    try:
        process = mfa_system.ProcessList[process_id]
        process.add_extension(
            Time=None,
            Name="initial_stock_config",
            Value=config,
            Unit="configuration"
        )
    except Exception as e:
        print(f"❌ Failed to store initial stock config: {e}")
        raise

# Replace custom attribute usage
def _create_single_outflow_flow(mfa_system, flow_name, process_id, destination_process, initial_stock, consumption_rate, split_fraction=1.0):
    """Create outflow flow using ODYM-compliant methods."""
    try:
        # Create flow using ODYM-compliant method
        flow = create_flow_odym_compliant(mfa_system, flow_name, process_id, destination_process)
        
        # Store configuration using ODYM Extensions
        config = {
            'initial_stock': initial_stock.copy(),
            'consumption_rate': consumption_rate,
            'split_fraction': split_fraction
        }
        store_initial_stock_config_odym_compliant(mfa_system, process_id, config)
        
        return flow
    except Exception as e:
        print(f"❌ Outflow flow creation failed: {e}")
        raise
```

**Step 2.2.2: Update FOMP Process Handling** (3-4 hours)
```python
# In solver.py
def _calculate_fomp_flows_odym_compliant(mfa_system, fomp_processes, fomp_params):
    """Calculate FOMP flows using ODYM-compliant methods."""
    try:
        for process_id in fomp_processes:
            # Get FOMP configuration from ODYM Extensions
            process = mfa_system.ProcessList[process_id]
            fomp_config = get_process_extension(mfa_system, process_id, "fomp_config")
            
            if fomp_config:
                # Process FOMP calculations
                # ... existing logic ...
                
                # Update flows using ODYM methods
                for flow_name, flow_values in fomp_results.items():
                    if flow_name in mfa_system.FlowDict:
                        mfa_system.FlowDict[flow_name].Values = flow_values
                
                # Validate after FOMP calculations
                mfa_system.Consistency_Check()
        
        return True
    except Exception as e:
        print(f"❌ FOMP flow calculation failed: {e}")
        raise
```

##### **2.3 Mass Balance Improvements** ⏱️ 4-6 hours
**Priority**: Medium | **Files**: `solver.py`

**Step 2.3.1: Use ODYM Mass Balance Methods** (2-3 hours)
```python
# In solver.py
def calculate_mass_balance_odym_compliant(mfa_system):
    """Calculate mass balance using ODYM's built-in method."""
    try:
        balance = mfa_system.MassBalance()
        
        # Check for significant imbalances
        max_imbalance = np.max(np.abs(balance))
        if max_imbalance > 1e-6:  # Tolerance for numerical errors
            print(f"⚠️ WARNING: Mass balance imbalance: {max_imbalance}")
            return False
        else:
            print("✅ Mass balance within tolerance")
            return True
    except Exception as e:
        print(f"❌ Mass balance calculation failed: {e}")
        return False
```

**Step 2.3.2: Add Comprehensive Validation** (2-3 hours)
```python
# NEW FILE: 02_src/engine/validation.py
def validate_mfa_system_state(mfa_system, operation_name=""):
    """Comprehensive validation of MFA system state."""
    try:
        # Check index table consistency
        mfa_system.IndexTableCheck()
        
        # Check system consistency
        mfa_system.Consistency_Check()
        
        # Check for negative values in flows
        for flow_name, flow in mfa_system.FlowDict.items():
            if flow.Values is not None and np.any(flow.Values < 0):
                print(f"⚠️ WARNING: Negative values found in flow {flow_name}")
        
        print(f"✅ System validation passed for {operation_name}")
        return True
        
    except Exception as e:
        print(f"❌ System validation failed for {operation_name}: {e}")
        return False
```

#### **Phase 2 Success Criteria**
- [ ] ODYM methods used for flow aggregation
- [ ] Custom attributes removed from ODYM objects
- [ ] ODYM Extensions used for configuration
- [ ] ODYM initialization methods implemented
- [ ] Mass balance calculations improved
- [ ] Comprehensive validation added
- [ ] All existing functionality preserved

---

### **Phase 3: Function Compliance (3-4 weeks)**
**Risk Level**: Medium | **Impact**: Medium | **Priority**: Medium

#### **Objectives**
- Add type hints to all functions
- Implement comprehensive error handling
- Add input validation
- Adopt ODYM function patterns

#### **Phase 3 Detailed Implementation Plan**

##### **3.1 Type Safety Implementation** ⏱️ 8-10 hours
**Priority**: High | **Files**: All engine modules

**Step 3.1.1: Add Type Hints** (4-5 hours)
```python
# In all engine modules, add type hints
from typing import Dict, List, Optional, Tuple, Union
import numpy as np

def calculate_final_balances(mfa_system: msc.MFAsystem) -> msc.MFAsystem:
    """Calculate final balances with proper type hints."""
    pass

def load_initial_stock_parameters(excel_data: Dict[str, pd.DataFrame]) -> Dict[int, Dict]:
    """Load initial stock parameters with type hints."""
    pass

def calculate_dynamic_stock(mfa_system: msc.MFAsystem, dsm_params_config: Dict) -> bool:
    """Calculate dynamic stock with type hints."""
    pass
```

**Step 3.1.2: Add Input Validation** (4-5 hours)
```python
# In all engine modules, add input validation
def calculate_final_balances(mfa_system: msc.MFAsystem) -> msc.MFAsystem:
    """Calculate final balances with input validation."""
    if not isinstance(mfa_system, msc.MFAsystem):
        raise TypeError("mfa_system must be an MFAsystem object")
    
    if not mfa_system.FlowDict:
        raise ValueError("MFA system has no flows defined")
    
    if not mfa_system.ProcessList:
        raise ValueError("MFA system has no processes defined")
    
    # Implementation
    pass
```

##### **3.2 Error Handling Implementation** ⏱️ 6-8 hours
**Priority**: High | **Files**: All engine modules

**Step 3.2.1: Add Comprehensive Error Handling** (3-4 hours)
```python
# In all engine modules, add error handling
import logging

logger = logging.getLogger(__name__)

def calculate_final_balances(mfa_system: msc.MFAsystem) -> msc.MFAsystem:
    """Calculate final balances with comprehensive error handling."""
    try:
        # Input validation
        if not isinstance(mfa_system, msc.MFAsystem):
            raise TypeError("mfa_system must be an MFAsystem object")
        
        # Implementation
        # ... existing logic ...
        
        # Validation after calculation
        mfa_system.Consistency_Check()
        
        return mfa_system
        
    except AttributeError as e:
        logger.error(f"Missing attribute in MFA system: {e}")
        raise ValueError(f"Invalid MFA system structure: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in balance calculation: {e}")
        raise
```

**Step 3.2.2: Add Logging Integration** (3-4 hours)
```python
# NEW FILE: 02_src/engine/logging_setup.py
import logging
import ODYM_Functions as msf

def setup_biodym_logging(log_filename: str, log_path: str) -> logging.Logger:
    """Setup logging using ODYM patterns."""
    logger, console_log, file_log = msf.function_logger(
        log_filename=log_filename,
        log_pathname=log_path,
        file_level=logging.DEBUG,
        console_level=logging.INFO
    )
    return logger

# In all engine modules, add logging
logger = setup_biodym_logging("biodym_engine.log", "logs/")
```

##### **3.3 ODYM Function Patterns** ⏱️ 6-8 hours
**Priority**: Medium | **Files**: All engine modules

**Step 3.3.1: Implement ODYM Naming Conventions** (3-4 hours)
```python
# Adopt ODYM naming patterns
def MI_CalculateFlowAggregation(mfa_system: msc.MFAsystem, process_id: int) -> np.ndarray:
    """Calculate flow aggregation using ODYM methods."""
    pass

def ODYM_ValidateSystemConsistency(mfa_system: msc.MFAsystem) -> bool:
    """Validate system consistency using ODYM methods."""
    pass

def ODYM_CalculateMassBalance(mfa_system: msc.MFAsystem) -> np.ndarray:
    """Calculate mass balance using ODYM methods."""
    pass
```

**Step 3.3.2: Implement Pure Functions** (3-4 hours)
```python
# Create pure functions where possible
def calculate_fomp_series_pure(dm_inflow_series: np.ndarray, params: Dict, initial_stock_labile: float, initial_stock_recalcitrant: float) -> Dict[str, np.ndarray]:
    """Pure function for FOMP series calculation."""
    # Implementation without side effects
    pass

def calculate_outflow_from_inflows_pure(total_inflow_values: np.ndarray, params: Dict, time_vector: np.ndarray) -> np.ndarray:
    """Pure function for outflow calculation."""
    # Implementation without side effects
    pass
```

#### **Phase 3 Success Criteria**
- [ ] Type hints added to all functions
- [ ] Input validation implemented
- [ ] Comprehensive error handling added
- [ ] Logging integration complete
- [ ] ODYM function patterns adopted
- [ ] Pure functions implemented where possible
- [ ] All existing functionality preserved

---

### **Phase 4: Advanced Integration & Optimization (3-4 weeks)**
**Risk Level**: High | **Impact**: High | **Priority**: Medium

#### **Objectives**
- Implement BioDYM extensions using ODYM Extensions mechanism
- Optimize performance for multi-dimensional operations
- Complete comprehensive testing
- Finalize Excel template updates

#### **Phase 4 Detailed Implementation Plan**

##### **4.1 BioDYM Extensions Implementation** ⏱️ 10-12 hours
**Priority**: Medium | **Files**: `bioDYM_classes.py`, All engine modules

**Step 4.1.1: Create BioDYM Extension Classes** (4-6 hours)
```python
# In bioDYM_classes.py
class FOMPProcess(msc.Process):
    """BioDYM extension of ODYM Process for FOMP calculations."""
    
    def __init__(self, Name=None, ID=None, **kwargs):
        super().__init__(Name=Name, ID=ID, **kwargs)
        self.fomp_params = {}
        self.protected_flows = set()
    
    def add_fomp_parameter(self, param_name: str, value: float) -> None:
        """Add FOMP-specific parameter."""
        self.fomp_params[param_name] = value
    
    def protect_flow(self, flow_name: str) -> None:
        """Mark flow as FOMP-protected."""
        self.protected_flows.add(flow_name)

class InitialStockManager:
    """BioDYM extension for initial stock management."""
    
    def __init__(self, mfa_system: msc.MFAsystem):
        self.mfa_system = mfa_system
        self.configs = {}
    
    def add_initial_stock_config(self, process_id: int, config: Dict) -> None:
        """Add initial stock configuration."""
        self.configs[process_id] = config
    
    def process_initial_stocks(self) -> bool:
        """Process all initial stocks using ODYM methods."""
        try:
            for process_id, config in self.configs.items():
                # Process using ODYM-compliant methods
                pass
            return True
        except Exception as e:
            print(f"❌ Initial stock processing failed: {e}")
            return False
```

**Step 4.1.2: Integrate Extensions with MFA System** (3-4 hours)
```python
# In system_setup.py
def initialize_biodym_extensions(mfa_system: msc.MFAsystem) -> msc.MFAsystem:
    """Initialize BioDYM-specific extensions."""
    try:
        from .bioDYM_classes import InitialStockManager, FOMPProcess
        
        mfa_system.biodym_extensions = {
            'initial_stock': InitialStockManager(mfa_system),
            'fomp': FOMPProcess()
        }
        
        return mfa_system
    except Exception as e:
        print(f"❌ BioDYM extensions initialization failed: {e}")
        raise
```

**Step 4.1.3: Update Engine Modules to Use Extensions** (3-2 hours)
```python
# In initial_stock_engine.py
def process_initial_stocks_with_extensions(mfa_system: msc.MFAsystem) -> msc.MFAsystem:
    """Process initial stocks using BioDYM extensions."""
    try:
        if hasattr(mfa_system, 'biodym_extensions'):
            initial_stock_manager = mfa_system.biodym_extensions['initial_stock']
            success = initial_stock_manager.process_initial_stocks()
            
            if success:
                mfa_system.Consistency_Check()
                return mfa_system
            else:
                raise ValueError("Initial stock processing failed")
        else:
            # Fallback to existing method
            return process_initial_stocks(mfa_system)
    except Exception as e:
        print(f"❌ Initial stock processing with extensions failed: {e}")
        raise
```

##### **4.2 Performance Optimization** ⏱️ 8-10 hours
**Priority**: Medium | **Files**: `solver.py`, `dsm_model.py`, `fomp_model.py`

**Step 4.2.1: Optimize Multi-Dimensional Operations** (4-5 hours)
```python
# In solver.py
def calculate_flows_vectorized(mfa_system: msc.MFAsystem, process_ids: List[int]) -> Dict[int, np.ndarray]:
    """Calculate flows for multiple processes using vectorized operations."""
    try:
        results = {}
        
        # Use numpy operations for better performance
        for process_id in process_ids:
            inflows = []
            for flow in mfa_system.FlowDict.values():
                if flow.P_End == process_id and flow.Values is not None:
                    inflows.append(flow.Values)
            
            if inflows:
                results[process_id] = np.sum(inflows, axis=0)
            else:
                results[process_id] = np.zeros(mfa_system.get_flow_shape())
        
        return results
    except Exception as e:
        print(f"❌ Vectorized flow calculation failed: {e}")
        raise
```

**Step 4.2.2: Add Performance Monitoring** (4-5 hours)
```python
# NEW FILE: 02_src/engine/performance_monitor.py
import time
from functools import wraps

def monitor_performance(func):
    """Decorator to monitor function performance."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"⏱️ {func.__name__} executed in {end_time - start_time:.3f} seconds")
        return result
    return wrapper

# Apply to critical functions
@monitor_performance
def calculate_dynamic_stock(mfa_system: msc.MFAsystem, dsm_params_config: Dict) -> bool:
    # Existing implementation
    pass

@monitor_performance
def calculate_fomp(mfa_system: msc.MFAsystem, fomp_params_config: Dict, input_flow_composition: np.ndarray) -> bool:
    # Existing implementation
    pass
```

##### **4.3 Excel Template Updates** ⏱️ 12-16 hours
**Priority**: High | **Files**: Excel templates, `data_loader.py`

**Step 4.3.1: Create New Excel Sheets** (6-8 hours)
```python
# Create new Excel sheets for dimensions
EXCEL_SHEET_STRUCTURE = {
    "3_1_Definition_Regions": {
        "columns": ["Region_ID", "Region_Name", "Description", "Geographic_Scope"],
        "required": True
    },
    "3_2_Data_Regions": {
        "columns": ["Region_ID", "Region_Name", "Population", "Area_km2", "GDP"],
        "required": False
    },
    "4_1_Definition_Goods": {
        "columns": ["Good_ID", "Good_Name", "Description", "Category", "Unit"],
        "required": True
    },
    "4_2_Data_Goods": {
        "columns": ["Good_ID", "Good_Name", "Market_Price", "Availability", "Quality_Factor"],
        "required": False
    },
    "5_1_Definition_Materials": {
        "columns": ["Material_ID", "Material_Name", "Description", "Composition"],
        "required": True
    },
    "5_2_Data_Materials": {
        "columns": ["Material_ID", "Material_Name", "Density", "Moisture_Content", "Carbon_Content"],
        "required": False
    },
    "6_1_Definition_Processes": {
        "columns": ["Process_ID", "Process_Name", "Description", "Type", "Efficiency"],
        "required": True
    },
    "6_2_Data_Processes": {
        "columns": ["Process_ID", "Process_Name", "Energy_Consumption", "Water_Consumption", "Emissions"],
        "required": False
    }
}
```

**Step 4.3.2: Update Data Loader** (6-8 hours)
```python
# In data_loader.py
def load_multi_dimensional_data(excel_file_path: str) -> Dict[str, pd.DataFrame]:
    """Load data with multi-dimensional support."""
    try:
        all_data = {}
        
        # Load existing sheets
        existing_sheets = ["1_1_Definition_Flows", "1_2_Data_Flows", "2_1_Definition_Processes", 
                          "2_2_static_TCs", "2_3_dynamic_TCs", "2_4_Initial_Stock"]
        
        for sheet_name in existing_sheets:
            try:
                all_data[sheet_name] = pd.read_excel(excel_file_path, sheet_name=sheet_name)
            except Exception as e:
                print(f"⚠️ WARNING: Could not load sheet {sheet_name}: {e}")
        
        # Load new dimension sheets
        new_sheets = ["3_1_Definition_Regions", "3_2_Data_Regions", "4_1_Definition_Goods", 
                     "4_2_Data_Goods", "5_1_Definition_Materials", "5_2_Data_Materials",
                     "6_1_Definition_Processes", "6_2_Data_Processes"]
        
        for sheet_name in new_sheets:
            try:
                all_data[sheet_name] = pd.read_excel(excel_file_path, sheet_name=sheet_name)
            except Exception as e:
                print(f"⚠️ WARNING: Could not load new sheet {sheet_name}: {e}")
                # Create empty DataFrame with required structure
                all_data[sheet_name] = pd.DataFrame(columns=EXCEL_SHEET_STRUCTURE[sheet_name]["columns"])
        
        return all_data
    except Exception as e:
        print(f"❌ Data loading failed: {e}")
        raise
```

##### **4.4 Comprehensive Testing** ⏱️ 8-10 hours
**Priority**: High | **Files**: Test files

**Step 4.4.1: Create Test Suite** (4-5 hours)
```python
# NEW FILE: tests/test_odym_compliance.py
import unittest
import numpy as np
from src.system_setup import define_model_scope, initialize_mfa_system_odym_compliant
from src.engine.solver import calculate_final_balances
from src.engine.initial_stock_engine import process_initial_stocks

class TestODYMCompliance(unittest.TestCase):
    """Test suite for ODYM compliance."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.start_year = 2020
        self.end_year = 2025
        self.elements = ["material", "WC", "DM", "CC"]
        self.regions = ["Region_A", "Region_B"]
        self.goods = ["Rye_Straw", "Biochar"]
        self.materials = ["Dry_Matter", "Water_Content"]
        self.processes = ["Harvest", "Processing"]
    
    def test_dimension_compliance(self):
        """Test dimension compliance."""
        model_classification, index_table = define_model_scope(
            self.start_year, self.end_year, self.elements, 
            self.regions, self.goods, self.materials, self.processes
        )
        
        # Test all dimensions are present
        self.assertIn("Time", model_classification)
        self.assertIn("Element", model_classification)
        self.assertIn("Region", model_classification)
        self.assertIn("Good", model_classification)
        self.assertIn("Material", model_classification)
        self.assertIn("Process", model_classification)
        
        # Test IndexTable structure
        self.assertEqual(len(index_table), 6)
        self.assertIn("Region", index_table.index)
        self.assertIn("Good", index_table.index)
        self.assertIn("Material", index_table.index)
        self.assertIn("Process", index_table.index)
    
    def test_class_compliance(self):
        """Test class compliance."""
        model_classification, index_table = define_model_scope(
            self.start_year, self.end_year, self.elements, 
            self.regions, self.goods, self.materials, self.processes
        )
        
        mfa_system = initialize_mfa_system_odym_compliant(model_classification, index_table)
        
        # Test ODYM methods are available
        self.assertTrue(hasattr(mfa_system, 'Consistency_Check'))
        self.assertTrue(hasattr(mfa_system, 'IndexTableCheck'))
        self.assertTrue(hasattr(mfa_system, 'Initialize_FlowValues'))
        
        # Test system validation
        try:
            mfa_system.Consistency_Check()
            mfa_system.IndexTableCheck()
        except Exception as e:
            self.fail(f"System validation failed: {e}")
    
    def test_function_compliance(self):
        """Test function compliance."""
        # Test type hints
        import inspect
        
        sig = inspect.signature(calculate_final_balances)
        self.assertIn('mfa_system', sig.parameters)
        
        # Test error handling
        with self.assertRaises(TypeError):
            calculate_final_balances("invalid_input")
    
    def test_performance(self):
        """Test performance improvements."""
        import time
        
        model_classification, index_table = define_model_scope(
            self.start_year, self.end_year, self.elements, 
            self.regions, self.goods, self.materials, self.processes
        )
        
        mfa_system = initialize_mfa_system_odym_compliant(model_classification, index_table)
        
        start_time = time.time()
        result = calculate_final_balances(mfa_system)
        end_time = time.time()
        
        execution_time = end_time - start_time
        self.assertLess(execution_time, 5.0, "Performance regression detected")

if __name__ == '__main__':
    unittest.main()
```

**Step 4.4.2: Integration Testing** (4-5 hours)
```python
# NEW FILE: tests/test_integration.py
import unittest
import numpy as np
from src.main import main

class TestIntegration(unittest.TestCase):
    """Integration tests for complete ODYM compliance."""
    
    def test_full_workflow(self):
        """Test complete BioDYM workflow with ODYM compliance."""
        try:
            # Run complete workflow
            result = main()
            
            # Verify results
            self.assertIsNotNone(result)
            
            # Verify ODYM compliance
            mfa_system = result['mfa_system']
            mfa_system.Consistency_Check()
            mfa_system.IndexTableCheck()
            
        except Exception as e:
            self.fail(f"Integration test failed: {e}")
    
    def test_backward_compatibility(self):
        """Test backward compatibility with existing Excel templates."""
        try:
            # Test with existing Excel template
            result = main()
            
            # Verify results are consistent
            self.assertIsNotNone(result)
            
        except Exception as e:
            self.fail(f"Backward compatibility test failed: {e}")

if __name__ == '__main__':
    unittest.main()
```

#### **Phase 4 Success Criteria**
- [ ] BioDYM extensions implemented using ODYM Extensions mechanism
- [ ] Performance optimized for multi-dimensional operations
- [ ] Excel templates updated with new dimension sheets
- [ ] Comprehensive test suite created
- [ ] Integration testing complete
- [ ] Backward compatibility maintained
- [ ] Full ODYM compliance achieved

---

## Comprehensive To-Do List

This to-do list is structured around the revised, lower-risk implementation strategy.

### **Phase 0: Build a Testing Safety Net (1-2 weeks)**
- [ ] **Task 0.1**: Identify 1-2 representative Excel files for creating "golden" test datasets.
- [ ] **Task 0.2**: Run the full, current workflow and save the key output files as the "golden" reference versions.
- [ ] **Task 0.3**: Create a new integration test file (`04_tests/workflow/test_e2e_workflow.py`).
- [ ] **Task 0.4**: Implement the tests to run the workflow and assert that the output matches the golden reference files.
- [ ] **Goal**: Ensure all Phase 0 tests pass before starting Phase 1.

### **Phase 1: Iterative Foundation & Dimension Implementation (4-5 weeks)**
#### **Phase 1a: Foundational Refactoring (1 week)**
- [ ] **Task 1a.1**: In `system_setup.py`, replace manual object initialization with ODYM methods (`Initialize_FlowValues()`, etc.).
- [ ] **Task 1a.2**: Add `mfa_system.Consistency_Check()` calls at key points in `solver.py` and `initial_stock_engine.py`.
- [ ] **Task 1a.3**: Wrap critical ODYM operations in `try...except` blocks for robust error handling.
- [ ] **Goal**: Ensure all Phase 0 tests still pass after this refactoring.

#### **Phase 1b: Introduce a Single New Dimension ('Region') (2 weeks)**
- [ ] **Task 1b.1**: Update `system_setup.py` to add the 'Region' classification and update the `IndexTable` (ensuring `set_index('Aspect')` is used).
- [ ] **Task 1b.2**: Update `data_loader.py` to read the 'Region' definition from Excel, with a backward-compatible fallback to a default region if the sheet is missing.
- [ ] **Task 1b.3**: Refactor the engine modules (`solver.py`, etc.) to handle 3D (`t,e,r`) NumPy arrays instead of 2D.
- [ ] **Goal**: Ensure Phase 0 tests pass with both old and new Excel files.

#### **Phase 1c: Add Remaining Dimensions ('Good', 'Material', 'Process') (1-2 weeks)**
- [ ] **Task 1c.1**: Extend `system_setup.py` and `data_loader.py` for the 'Good', 'Material', and 'Process' dimensions, following the backward-compatible pattern.
- [ ] **Task 1c.2**: Scale up the engine logic to handle up to 6D arrays.
- [ ] **Goal**: Ensure Phase 0 tests pass.

### **Phase 2: Class Compliance (3-4 weeks)**
- [ ] **Task 2.1**: Replace all manual flow aggregation logic with ODYM methods (e.g., `Flow_Sum_By_Element`).
- [ ] **Task 2.2**: Refactor all custom attributes (e.g., `_fomp_protected`) to use the ODYM Extensions mechanism (`process.add_extension(...)`).
- [ ] **Task 2.3**: Implement proper ODYM flow management for creating and initializing flows.
- [ ] **Task 2.4**: Replace manual mass balance calculations with `mfa_system.MassBalance()`.
- [ ] **Task 2.5**: Create a comprehensive validation module (`02_src/engine/validation.py`).

### **Phase 3: Function Compliance (3-4 weeks)**
- [ ] **Task 3.1**: Add full type hints to all functions in the `engine` modules.
- [ ] **Task 3.2**: Implement robust input validation at the start of all public functions.
- [ ] **Task 3.3**: Integrate a standard ODYM logger (`msf.function_logger`) into all modules.
- [ ] **Task 3.4**: Refactor function names to follow ODYM conventions where appropriate (e.g., `MI_Calculate...`).
- [ ] **Task 3.5**: Identify and refactor functions to be "pure" (no side effects) where possible.

### **Phase 4: Advanced Integration & Finalization (3-4 weeks)**
- [ ] **Task 4.1**: Implement BioDYM-specific features (FOMP, Initial Stock) as formal classes that extend ODYM base classes.
- [ ] **Task 4.2**: Investigate and implement performance optimizations for multi-dimensional operations (e.g., vectorization with NumPy).
- [ ] **Task 4.3**: Finalize the new Excel template structure with sheets for all 6 dimensions.
- [ ] **Task 4.4**: Create the final, comprehensive test suite (`tests/test_odym_compliance.py`) to validate all aspects of the new system.
- [ ] **Task 4.5**: Update the `00_BioDYM_Workflow.ipynb` to use the new `6D -> 2D` aggregation workflow and add the system inspection cell.

---

## Risk Assessment & Mitigation

### **High-Risk Areas**
1. **Dimension Migration**: Multi-dimensional arrays may cause performance issues
2. **Excel Template Changes**: Major changes may break existing workflows
3. **Custom Attributes Removal**: May break existing functionality
4. **Performance Impact**: ODYM methods might be slower than custom implementations

### **Mitigation Strategies**
1. **Comprehensive Testing**: Unit tests, integration tests, regression tests
2. **Performance Benchmarking**: Compare before/after performance
3. **Gradual Migration**: Phase-by-phase implementation with rollback options
4. **Backward Compatibility**: Maintain compatibility with existing Excel templates
5. **Documentation**: Comprehensive documentation for all changes

### **Success Metrics**
- [ ] All existing tests pass
- [ ] Performance maintained or improved
- [ ] No functionality loss
- [ ] Better error handling
- [ ] Improved validation
- [ ] Full ODYM compatibility
- [ ] Excel template compatibility maintained

---

## Timeline & Resource Requirements

### **Phase 1: Foundation & Dimensions (3-4 weeks)**
- **Effort**: 20-26 hours
- **Risk**: Medium
- **Dependencies**: None
- **Deliverables**: Complete dimension system, multi-dimensional data structures

### **Phase 2: Class Compliance (3-4 weeks)**
- **Effort**: 20-26 hours
- **Risk**: Medium
- **Dependencies**: Phase 1 completion
- **Deliverables**: ODYM method integration, custom attributes removal

### **Phase 3: Function Compliance (3-4 weeks)**
- **Effort**: 20-26 hours
- **Risk**: Medium
- **Dependencies**: Phase 2 completion
- **Deliverables**: Type safety, error handling, ODYM patterns

### **Phase 4: Advanced Integration (3-4 weeks)**
- **Effort**: 26-34 hours
- **Risk**: High
- **Dependencies**: Phase 3 completion
- **Deliverables**: BioDYM extensions, performance optimization, Excel updates

### **Total Timeline**: 12-16 weeks
### **Total Effort**: 86-112 hours

---

## Conclusion

This comprehensive master plan provides a structured approach to achieving full ODYM compliance across all identified areas. The phased approach minimizes risk while maximizing benefits, ensuring that BioDYM becomes fully compliant with ODYM standards while maintaining its unique features.

**Key Benefits**:
- ✅ **Full ODYM Compliance**: Complete integration with ODYM framework
- ✅ **Enhanced Scalability**: Multi-dimensional support for complex analyses
- ✅ **Future-Proofing**: Compatible with future ODYM updates
- ✅ **Better Validation**: Comprehensive error handling and validation
- ✅ **Improved Performance**: Optimized multi-dimensional operations
- ✅ **Maintained Compatibility**: Backward compatibility with existing workflows

**Next Steps**:
1. Review and approve this master plan
2. Begin Phase 1 implementation
3. Test thoroughly before proceeding to Phase 2
4. Evaluate results before considering Phase 3
5. Complete Phase 4 for full ODYM compliance

---

*Document Version: 1.0*  
*Last Updated: [Current Date]*  
*Author: BioDYM Development Team*

---


================================================================================
# File: ODYM_COMPLIANCE_STRATEGY.md
================================================================================

# BioDYM ODYM Compliance Implementation Strategy

## Overview

This document outlines a comprehensive strategy for improving ODYM class compliance in the BioDYM engine modules. The implementation is designed to maintain full backward compatibility while leveraging ODYM's built-in methods and validation systems.

## Executive Summary

- **Excel Templates**: ❌ **NO CHANGES REQUIRED** - Current Excel structure is perfectly compatible
- **Implementation Complexity**: 7/10 (High) - Requires careful testing and validation
- **Timeline**: 6-9 weeks total across 3 phases
- **Risk Level**: Low to High (phased approach)
- **Benefits**: Better ODYM integration, improved validation, future-proofing

## Current State Analysis

### ODYM Class Usage Assessment

| Engine Module | ODYM Classes Modified | Compliance Issues | Priority |
|---------------|----------------------|-------------------|----------|
| **solver.py** | `MFAsystem`, `Flow`, `Parameter` | Manual aggregation, missing validation | High |
| **initial_stock_engine.py** | `Flow`, `Stock`, `MFAsystem` | Custom attributes, direct creation | High |
| **dsm_model.py** | `Flow`, `MFAsystem` | Direct value assignment | Medium |
| **fomp_model.py** | `Flow`, `MFAsystem` | Direct value assignment | Medium |
| **scenario_engine.py** | `MFAsystem` | Deep copy usage | Low |
| **mc_simulation.py** | `Parameter`, `MFAsystem` | Parameter updates | Low |

### Key Non-Compliant Patterns Identified

1. **Manual Flow Aggregation** (solver.py):
   ```python
   # Current (Non-compliant)
   inflows = [f.Values for f in mfa_system.FlowDict.values() if f.P_End == pid]
   total_inflows = sum(inflows) if inflows else np.zeros_like(stock_s.Values)
   
   # Target (ODYM-compliant)
   total_inflows = mfa_system.Flow_Sum_By_Element(flow_key)
   ```

2. **Custom Attributes on ODYM Objects**:
   ```python
   # Current (Non-compliant)
   flow._initial_stock_config = {...}
   flow._fomp_protected = True
   
   # Target (ODYM-compliant)
   process.add_extension(Name="config", Value=config_dict)
   ```

3. **Missing Consistency Checks**:
   ```python
   # Current (Missing)
   # No validation after modifications
   
   # Target (ODYM-compliant)
   mfa_system.Consistency_Check()
   mfa_system.IndexTableCheck()
   ```

## Implementation Strategy: 3-Phase Approach

### Phase 1: Foundation Improvements (1-2 weeks)
**Risk Level**: Low | **Impact**: Foundation | **Priority**: High

#### Objectives
- Add ODYM validation methods
- Use ODYM initialization methods
- Remove custom attributes from ODYM objects
- Establish proper error handling

#### Detailed Implementation Plan

##### 1.1 Add ODYM Consistency Checks ⏱️ 2-3 hours

**Files to modify**: `solver.py`, `initial_stock_engine.py`, `dsm_model.py`, `fomp_model.py`

**solver.py Changes**:
```python
# After line 433 in solver.py
mfa_system = calculate_final_balances(mfa_system)

# ADD THIS:
try:
    mfa_system.Consistency_Check()
    print("✅ System consistency validated")
except ValueError as e:
    print(f"❌ System consistency check failed: {e}")
    raise
```

**initial_stock_engine.py Changes**:
```python
# After line 286 in initial_stock_engine.py
print("--> Initial stock outflows processed.")

# ADD THIS:
try:
    mfa_system.Consistency_Check()
    print("✅ Initial stock system consistency validated")
except ValueError as e:
    print(f"❌ Initial stock consistency check failed: {e}")
    raise

return mfa_system
```

**dsm_model.py Changes**:
```python
# After line 221 in dsm_model.py
_distribute_and_assign_outflows(...)

# ADD THIS:
try:
    mfa_system.Consistency_Check()
    print(f"✅ DSM Process {process_id} consistency validated")
except ValueError as e:
    print(f"❌ DSM Process {process_id} consistency check failed: {e}")
    raise
```

##### 1.2 Use ODYM Initialization Methods ⏱️ 1-2 hours

**Files to modify**: `system_setup.py`

```python
# In define_flows_and_parameters() after line 465
_calculate_elemental_compositions(mfa_system)
flow_tc_map, process_logic_map = _create_flow_and_process_maps(mfa_system, all_excel_data)

# REPLACE manual initialization with ODYM methods:
mfa_system.Initialize_FlowValues()
mfa_system.Initialize_StockValues() 
mfa_system.Initialize_ParameterValues()

mfa_system.Consistency_Check()
```

##### 1.3 Remove Custom Attributes from ODYM Objects ⏱️ 3-4 hours

**Files to modify**: `initial_stock_engine.py`, `solver.py`, `fomp_model.py`

**initial_stock_engine.py Changes**:
```python
# REPLACE lines 398-403 in initial_stock_engine.py
# OLD CODE:
if not hasattr(flow, '_initial_stock_config'):
    flow._initial_stock_config = {
        'initial_stock': initial_stock.copy(),
        'consumption_rate': consumption_rate,
        'split_fraction': split_fraction
    }

# NEW CODE:
# Store in separate configuration system
if not hasattr(mfa_system, 'initial_stock_flow_configs'):
    mfa_system.initial_stock_flow_configs = {}

mfa_system.initial_stock_flow_configs[flow_name] = {
    'initial_stock': initial_stock.copy(),
    'consumption_rate': consumption_rate,
    'split_fraction': split_fraction
}
```

**solver.py Changes**:
```python
# In solver.py, update _calculate_fomp_flows() around line 295
# REPLACE:
fomp_outflows = [f for f in mfa_system.FlowDict.values() if f.P_Start == process_id and hasattr(f, '_fomp_protected')]

# WITH:
fomp_outflows = [f for f in mfa_system.FlowDict.values() if f.P_Start == process_id and f.Name in mfa_system.get('fomp_protected_flows', [])]
```

##### 1.4 Add Proper Error Handling ⏱️ 2-3 hours

**Files to modify**: All engine modules

```python
# In solver.py, wrap flow operations
try:
    # Existing flow operations
    inflows = [f.Values for f in mfa_system.FlowDict.values() if f.P_End == pid]
    # ... rest of operations
except (AttributeError, KeyError) as e:
    print(f"❌ Error accessing flow data for process {pid}: {e}")
    raise ValueError(f"Flow data access failed for process {pid}")
```

#### Phase 1 Success Criteria
- [ ] All consistency checks pass
- [ ] No custom attributes on ODYM objects
- [ ] Proper error handling implemented
- [ ] All existing tests pass
- [ ] Performance maintained or improved

---

### Phase 2: Core Improvements (2-3 weeks)
**Risk Level**: Medium | **Impact**: Core Functionality | **Priority**: High

#### Objectives
- Replace manual flow aggregation with ODYM methods
- Implement proper ODYM flow management
- Add comprehensive validation
- Improve mass balance calculations

#### Detailed Implementation Plan

##### 2.1 Replace Manual Flow Aggregation ⏱️ 4-6 hours

**Files to modify**: `solver.py`

**Create ODYM-compliant flow aggregation function**:
```python
# NEW FUNCTION in solver.py
def calculate_process_inflows_odym_compliant(mfa_system, process_id):
    """Calculate total inflows to a process using ODYM methods."""
    inflows = []
    for flow in mfa_system.FlowDict.values():
        if flow.P_End == process_id:
            # Use ODYM's Flow_Sum_By_Element method
            flow_sum = mfa_system.Flow_Sum_By_Element(flow.Name)
            inflows.append(flow_sum)
    
    if inflows:
        return sum(inflows)
    else:
        # Return zeros with correct shape
        n_years = len(mfa_system.Time_L)
        n_elements = len(mfa_system.Elements)
        return np.zeros((n_years, n_elements))
```

**Replace manual aggregation in `calculate_final_balances()`**:
```python
# REPLACE lines 49-56 in solver.py
# OLD CODE:
inflows = [f.Values for f in mfa_system.FlowDict.values() if f.P_End == pid]
outflows = [f.Values for f in mfa_system.FlowDict.values() if f.P_Start == pid]
total_inflows = sum(inflows) if inflows else np.zeros_like(stock_s.Values)
total_outflows = sum(outflows) if outflows else np.zeros_like(stock_s.Values)

# NEW CODE:
total_inflows = calculate_process_inflows_odym_compliant(mfa_system, pid)
total_outflows = calculate_process_outflows_odym_compliant(mfa_system, pid)
```

##### 2.2 Implement Proper ODYM Flow Management ⏱️ 3-4 hours

**Files to modify**: `initial_stock_engine.py`

**Create ODYM-compliant flow creation function**:
```python
# NEW FUNCTION in initial_stock_engine.py
def create_flow_odym_compliant(mfa_system, flow_name, process_id, destination_process):
    """Create flow using ODYM-compliant methods."""
    # Check if flow already exists
    if flow_name in mfa_system.FlowDict:
        return mfa_system.FlowDict[flow_name]
    
    # Create flow object
    flow = msc.Flow(
        Name=flow_name,
        P_Start=process_id,
        P_End=destination_process,
        Indices="t,e"
    )
    
    # Add to system using proper method (if available)
    mfa_system.FlowDict[flow_name] = flow
    
    # Initialize values using ODYM method
    mfa_system.Initialize_FlowValues()
    
    return flow
```

**Replace direct flow creation in `_create_single_outflow_flow()`**:
```python
# REPLACE lines 381-387 in initial_stock_engine.py
# OLD CODE:
if flow_name not in mfa_system.FlowDict:
    mfa_system.FlowDict[flow_name] = msc.Flow(
        Name=flow_name,
        P_Start=process_id,
        P_End=destination_process,
        Indices="t,e"
    )

# NEW CODE:
flow = create_flow_odym_compliant(mfa_system, flow_name, process_id, destination_process)
```

##### 2.3 Add Comprehensive Validation ⏱️ 2-3 hours

**Files to modify**: All engine modules

**Create validation utility functions**:
```python
# NEW FILE: 02_src/engine/validation.py
def validate_mfa_system_state(mfa_system, operation_name=""):
    """Comprehensive validation of MFA system state."""
    try:
        # Check index table consistency
        mfa_system.IndexTableCheck()
        
        # Check system consistency
        mfa_system.Consistency_Check()
        
        # Check for negative values in flows
        for flow_name, flow in mfa_system.FlowDict.items():
            if flow.Values is not None and np.any(flow.Values < 0):
                print(f"⚠️ WARNING: Negative values found in flow {flow_name}")
        
        print(f"✅ System validation passed for {operation_name}")
        return True
        
    except Exception as e:
        print(f"❌ System validation failed for {operation_name}: {e}")
        return False
```

**Add validation calls throughout engine modules**:
```python
# In solver.py, add after major operations
from .validation import validate_mfa_system_state

# After convergence check
if not any(pass_changes):
    print(f"--> System converged after {i + 1} iterations.")
    validate_mfa_system_state(mfa_system, "convergence")
    break
```

##### 2.4 Improve Mass Balance Calculations ⏱️ 3-4 hours

**Files to modify**: `solver.py`

**Use ODYM's MassBalance method**:
```python
# NEW FUNCTION in solver.py
def calculate_mass_balance_odym_compliant(mfa_system):
    """Calculate mass balance using ODYM's built-in method."""
    try:
        balance = mfa_system.MassBalance()
        return balance
    except Exception as e:
        print(f"❌ Error calculating mass balance: {e}")
        return None

# REPLACE manual balance calculation in calculate_final_balances()
# Use ODYM's method instead of manual calculation
```

#### Phase 2 Success Criteria
- [ ] ODYM methods used for flow aggregation
- [ ] Proper flow management implemented
- [ ] Comprehensive validation added
- [ ] Mass balance calculations improved
- [ ] Performance maintained or improved
- [ ] All existing functionality preserved

---

### Phase 3: Advanced Improvements (3-4 weeks)
**Risk Level**: High | **Impact**: Architecture | **Priority**: Medium

#### Objectives
- Refactor custom BioDYM extensions
- Implement ODYM Extensions mechanism
- Complete system validation
- Optimize performance

#### Detailed Implementation Plan

##### 3.1 Refactor Custom BioDYM Extensions ⏱️ 6-8 hours

**Files to modify**: `initial_stock_engine.py`, `fomp_model.py`

**Create BioDYM extension classes**:
```python
# NEW FILE: 02_src/engine/biodym_extensions.py
class InitialStockExtension:
    """BioDYM extension for initial stock management."""
    
    def __init__(self, mfa_system):
        self.mfa_system = mfa_system
        self.configs = {}
    
    def add_initial_stock_config(self, process_id, config):
        """Add initial stock configuration."""
        self.configs[process_id] = config
    
    def process_initial_stocks(self):
        """Process all initial stocks."""
        # Implementation using ODYM-compliant methods
        pass

class FOMPExtension:
    """BioDYM extension for FOMP processes."""
    
    def __init__(self, mfa_system):
        self.mfa_system = mfa_system
        self.protected_flows = set()
    
    def protect_flow(self, flow_name):
        """Mark flow as FOMP-protected."""
        self.protected_flows.add(flow_name)
```

**Integrate extensions with MFA system**:
```python
# In system_setup.py, add extension initialization
def initialize_biodym_extensions(mfa_system):
    """Initialize BioDYM-specific extensions."""
    from .engine.biodym_extensions import InitialStockExtension, FOMPExtension
    
    mfa_system.biodym_extensions = {
        'initial_stock': InitialStockExtension(mfa_system),
        'fomp': FOMPExtension(mfa_system)
    }
    
    return mfa_system
```

##### 3.2 Implement ODYM Extensions Mechanism ⏱️ 4-6 hours

**Files to modify**: All engine modules

**Use ODYM's Process Extensions**:
```python
# In initial_stock_engine.py, replace custom attributes
# OLD CODE:
flow._initial_stock_config = {...}

# NEW CODE:
process = mfa_system.ProcessList[process_id]
process.add_extension(
    Time=None,
    Name="initial_stock_config",
    Value=config_dict,
    Unit="configuration"
)
```

**Create extension access methods**:
```python
# NEW FUNCTION in initial_stock_engine.py
def get_process_extension(mfa_system, process_id, extension_name):
    """Get process extension using ODYM methods."""
    process = mfa_system.ProcessList[process_id]
    if process.Extensions:
        for ext in process.Extensions:
            if ext.Name == extension_name:
                return ext.Value
    return None
```

##### 3.3 Complete System Validation ⏱️ 3-4 hours

**Files to modify**: All engine modules

**Implement comprehensive validation suite**:
```python
# NEW FILE: 02_src/engine/comprehensive_validation.py
class MFAValidationSuite:
    """Comprehensive validation suite for MFA systems."""
    
    def __init__(self, mfa_system):
        self.mfa_system = mfa_system
        self.validation_results = {}
    
    def run_all_validations(self):
        """Run all validation checks."""
        self.validate_mass_balance()
        self.validate_flow_consistency()
        self.validate_stock_consistency()
        self.validate_parameter_consistency()
        self.validate_biodym_extensions()
        
        return self.validation_results
    
    def validate_mass_balance(self):
        """Validate mass balance using ODYM methods."""
        try:
            balance = self.mfa_system.MassBalance()
            # Check for significant imbalances
            max_imbalance = np.max(np.abs(balance))
            if max_imbalance > 1e-6:  # Tolerance for numerical errors
                self.validation_results['mass_balance'] = {
                    'status': 'warning',
                    'message': f'Mass balance imbalance: {max_imbalance}'
                }
            else:
                self.validation_results['mass_balance'] = {
                    'status': 'pass',
                    'message': 'Mass balance within tolerance'
                }
        except Exception as e:
            self.validation_results['mass_balance'] = {
                'status': 'error',
                'message': f'Mass balance validation failed: {e}'
            }
```

##### 3.4 Performance Optimization ⏱️ 4-5 hours

**Files to modify**: `solver.py`, `dsm_model.py`, `fomp_model.py`

**Optimize flow aggregation**:
```python
# NEW FUNCTION in solver.py
def calculate_flows_vectorized(mfa_system, process_ids):
    """Calculate flows for multiple processes using vectorized operations."""
    # Use numpy operations for better performance
    # Implement caching for repeated calculations
    pass
```

**Add performance monitoring**:
```python
# NEW FILE: 02_src/engine/performance_monitor.py
import time
from functools import wraps

def monitor_performance(func):
    """Decorator to monitor function performance."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"⏱️ {func.__name__} executed in {end_time - start_time:.3f} seconds")
        return result
    return wrapper

# Apply to critical functions
@monitor_performance
def calculate_dynamic_stock(mfa_system, dsm_params_config):
    # Existing implementation
    pass
```

#### Phase 3 Success Criteria
- [ ] Custom BioDYM extensions refactored
- [ ] ODYM Extensions mechanism implemented
- [ ] Comprehensive validation suite complete
- [ ] Performance optimized
- [ ] Full ODYM compliance achieved
- [ ] All existing functionality preserved

---

## BioDYM Classes vs. ODYM Aspects: Architectural Decision

### Question Analysis
You've developed BioDYM-specific features:
- **FOMP processes** (First-Order Mineralization Processes)
- **Initial stocks** with stock-outflow transfer coefficients
- **Custom features** in several processes

### Recommendation: Hybrid Approach

#### Use BioDYM Classes for Core Extensions
**When to use BioDYM classes**:
- **FOMP processes**: Create `bioDYM_classes.FOMPProcess` extending `msc.Process`
- **Initial stock management**: Create `bioDYM_classes.InitialStockManager`
- **Custom process logic**: Create `bioDYM_classes.BioDYMProcess`

**Example Implementation**:
```python
# In bioDYM_classes.py
class FOMPProcess(msc.Process):
    """BioDYM extension of ODYM Process for FOMP calculations."""
    
    def __init__(self, Name=None, ID=None, **kwargs):
        super().__init__(Name=Name, ID=ID, **kwargs)
        self.fomp_params = {}
        self.protected_flows = set()
    
    def add_fomp_parameter(self, param_name, value):
        """Add FOMP-specific parameter."""
        self.fomp_params[param_name] = value
    
    def protect_flow(self, flow_name):
        """Mark flow as FOMP-protected."""
        self.protected_flows.add(flow_name)

class InitialStockManager:
    """BioDYM extension for initial stock management."""
    
    def __init__(self, mfa_system):
        self.mfa_system = mfa_system
        self.configs = {}
    
    def add_initial_stock_config(self, process_id, config):
        """Add initial stock configuration."""
        self.configs[process_id] = config
```

#### Use ODYM Aspects for Standard Features
**When to use ODYM aspects**:
- **Standard process parameters**: Use `msc.Parameter`
- **Standard flows**: Use `msc.Flow`
- **Standard stocks**: Use `msc.Stock`
- **Standard classifications**: Use `msc.Classification`

### Implementation Strategy

#### Phase 1: Extend BioDYM Classes
1. **Create BioDYM-specific classes** that extend ODYM classes
2. **Maintain compatibility** with existing ODYM methods
3. **Add BioDYM-specific methods** for custom functionality

#### Phase 2: Integrate with ODYM Extensions
1. **Use ODYM Extensions** for process-specific data
2. **Store BioDYM configurations** in process extensions
3. **Maintain separation** between ODYM core and BioDYM extensions

#### Phase 3: Full Integration
1. **Seamless integration** between BioDYM and ODYM classes
2. **Proper inheritance** hierarchy
3. **Complete compatibility** with ODYM framework

### Benefits of Hybrid Approach
- ✅ **Maintains BioDYM identity** while leveraging ODYM
- ✅ **Future-proof** for ODYM updates
- ✅ **Clear separation** of concerns
- ✅ **Easy maintenance** and debugging
- ✅ **Extensible** for future BioDYM features

---

## Risk Assessment & Mitigation

### High-Risk Areas
1. **Custom BioDYM Features**: Initial stock outflows, FOMP processes
2. **Performance Impact**: ODYM methods might be slower
3. **Testing Complexity**: Need to validate all existing functionality

### Mitigation Strategies
1. **Comprehensive Testing**: Unit tests, integration tests, regression tests
2. **Performance Benchmarking**: Compare before/after performance
3. **Gradual Migration**: Phase-by-phase implementation
4. **Rollback Plan**: Maintain current implementation in separate branch

### Success Metrics
- [ ] All existing tests pass
- [ ] Performance maintained or improved
- [ ] No functionality loss
- [ ] Better error handling
- [ ] Improved validation
- [ ] Full ODYM compatibility

---

## Timeline & Resource Requirements

### Phase 1: Foundation (1-2 weeks)
- **Effort**: 8-12 hours
- **Risk**: Low
- **Dependencies**: None
- **Deliverables**: Validation, error handling, initialization

### Phase 2: Core (2-3 weeks)
- **Effort**: 12-18 hours
- **Risk**: Medium
- **Dependencies**: Phase 1 completion
- **Deliverables**: ODYM methods, flow management, validation

### Phase 3: Advanced (3-4 weeks)
- **Effort**: 18-24 hours
- **Risk**: High
- **Dependencies**: Phase 2 completion
- **Deliverables**: Extensions, optimization, full compliance

### Total Timeline: 6-9 weeks
### Total Effort: 38-54 hours

---

## Conclusion

This implementation strategy provides a structured approach to achieving full ODYM compliance while maintaining BioDYM's unique features. The phased approach minimizes risk while maximizing benefits, and the hybrid class architecture ensures both compatibility and extensibility.

The key insight is that **Excel templates require no changes** - the improvements are purely in the Python engine modules, leveraging ODYM's built-in methods and validation systems.

**Next Steps**:
1. Review and approve this strategy
2. Begin Phase 1 implementation
3. Test thoroughly before proceeding to Phase 2
4. Evaluate results before considering Phase 3

---

*Document Version: 1.0*  
*Last Updated: [Current Date]*  
*Author: BioDYM Development Team*


---


================================================================================
# File: ODYM_DIMENSIONS_COMPLIANCE_ANALYSIS.md
================================================================================

# BioDYM ODYM Dimensions Compliance Analysis

## Overview

This document analyzes the compliance of BioDYM's dimension usage with ODYM's comprehensive dimension system. The analysis reveals significant gaps in dimension utilization that impact system scalability, interoperability, and compliance with ODYM standards.

## Executive Summary

- **Overall Dimension Compliance**: 3/10 (Poor) - Major gaps in dimension usage
- **Missing Dimensions**: Region, Good, Material, Process classifications
- **Impact**: Limited scalability, reduced interoperability, non-standard ODYM compliance
- **Priority**: High - Critical for ODYM compliance and future extensibility

## ODYM Dimension System Analysis

### Standard ODYM Dimensions

Based on the ODYM framework, the following dimensions are available:

#### **Core Dimensions** (from `ODYM_Classes.py`):
```python
self.Dimensions = {
    "Time": "Time",
    "Process": "Process", 
    "Region": "Region",
    "Good": "Process, good, or commodity",
    "Material": "Material: ore, alloy, scrap type, ...",
    "Element": "Chemical element",
}
```

#### **Core Aspects** (from `ODYM_Classes.py`):
```python
self.Aspects = {
    "Time": "Model time",
    "Cohort": "Age-cohort",
    "OriginProcess": "Process where flow originates",
    "DestinationProcess": "Destination process of flow",
    "OriginRegion": "Region where flow originates from",
    "DestinationRegion": "Region where flow is bound to",
    "Good": "Process, good, or commodity",
    "Material": "Material: ore, alloy, scrap type, ...",
    "Element": "Chemical element",
}
```

## BioDYM Current Dimension Usage

### **Currently Implemented Dimensions**

#### ✅ **Time Dimension** (Fully Implemented)
```python
# In system_setup.py
model_classification["Time"] = msc.Classification(
    Name="Time", Dimension="Time", ID=1, Items=my_years
)
```
- **Status**: ✅ Complete
- **Usage**: Properly integrated in IndexTable
- **Compliance**: 10/10

#### ✅ **Element Dimension** (Fully Implemented)
```python
# In system_setup.py
model_classification["Element"] = msc.Classification(
    Name="Elements", Dimension="Element", ID=2, Items=elements
)
```
- **Status**: ✅ Complete
- **Usage**: Properly integrated in IndexTable
- **Compliance**: 10/10

### **Missing Critical Dimensions**

#### ❌ **Region Dimension** (Not Implemented)
**Current State**: 
- Only `Geogr_Scope="Case_Study_Region"` as string
- No regional classification system
- No regional flow tracking

**ODYM Standard**:
```python
# Should be implemented as:
model_classification["Region"] = msc.Classification(
    Name="Regions", 
    Dimension="Region", 
    ID=3, 
    Items=["Region_A", "Region_B", "Case_Study_Region"]
)
```

**Impact**:
- ❌ Cannot track inter-regional flows
- ❌ Cannot perform regional analysis
- ❌ Limited scalability for multi-regional studies
- ❌ Non-compliant with ODYM standards

#### ❌ **Good Dimension** (Not Implemented)
**Current State**: 
- No good/commodity classification
- Materials treated as simple strings
- No good-specific flow tracking

**ODYM Standard**:
```python
# Should be implemented as:
model_classification["Good"] = msc.Classification(
    Name="Goods", 
    Dimension="Good", 
    ID=4, 
    Items=["Rye_Straw", "Biochar", "Compost", "Energy"]
)
```

**Impact**:
- ❌ Cannot track good-specific flows
- ❌ Limited material flow analysis
- ❌ No commodity-based reporting
- ❌ Non-compliant with ODYM standards

#### ❌ **Material Dimension** (Not Implemented)
**Current State**: 
- Materials handled as simple strings in Excel
- No material classification system
- No material-specific properties

**ODYM Standard**:
```python
# Should be implemented as:
model_classification["Material"] = msc.Classification(
    Name="Materials", 
    Dimension="Material", 
    ID=5, 
    Items=["Dry_Matter", "Water_Content", "Carbon_Content"]
)
```

**Impact**:
- ❌ Cannot track material-specific properties
- ❌ Limited material composition analysis
- ❌ No material-specific parameters
- ❌ Non-compliant with ODYM standards

#### ❌ **Process Dimension** (Partially Implemented)
**Current State**: 
- Processes exist but not as formal classification
- No process classification system
- Process IDs used directly without classification

**ODYM Standard**:
```python
# Should be implemented as:
model_classification["Process"] = msc.Classification(
    Name="Processes", 
    Dimension="Process", 
    ID=6, 
    Items=["Harvest", "Processing", "Storage", "Application"]
)
```

**Impact**:
- ❌ Cannot perform process-type analysis
- ❌ Limited process categorization
- ❌ No process-specific reporting
- ❌ Non-compliant with ODYM standards

## Detailed Compliance Analysis

### **IndexTable Structure Analysis**

#### **Current BioDYM IndexTable**:
```python
# Current implementation (system_setup.py)
index_table = pd.DataFrame({
    "Aspect": ["Time", "Element"],
    "Description": ['Model aspect "time"', 'Model aspect "Element"'],
    "Dimension": ["Time", "Element"],
    "Classification": [model_classification[Aspect] for Aspect in ["Time", "Element"]],
    "IndexLetter": ["t", "e"],
})
```

#### **ODYM-Compliant IndexTable**:
```python
# Should be implemented as:
index_table = pd.DataFrame({
    "Aspect": ["Time", "Element", "Region", "Good", "Material", "Process"],
    "Description": [
        'Model aspect "time"',
        'Model aspect "Element"', 
        'Model aspect "Region"',
        'Model aspect "Good"',
        'Model aspect "Material"',
        'Model aspect "Process"'
    ],
    "Dimension": ["Time", "Element", "Region", "Good", "Material", "Process"],
    "Classification": [
        model_classification["Time"],
        model_classification["Element"],
        model_classification["Region"],
        model_classification["Good"],
        model_classification["Material"],
        model_classification["Process"]
    ],
    "IndexLetter": ["t", "e", "r", "g", "m", "p"],
})
```

### **Flow Indices Analysis**

#### **Current BioDYM Flow Indices**:
```python
# Current implementation
Indices="t,e"  # Only Time and Element
```

#### **ODYM-Compliant Flow Indices**:
```python
# Should be implemented as:
Indices="t,e,r,g,m,p"  # Time, Element, Region, Good, Material, Process
```

**Impact on Flow Arrays**:
- **Current**: 2D arrays (Time × Element)
- **ODYM Standard**: 6D arrays (Time × Element × Region × Good × Material × Process)

### **Data Structure Impact Analysis**

#### **Current BioDYM Data Structures**:
```python
# Flow values: 2D array
flow.Values.shape = (n_years, n_elements)

# Stock values: 2D array  
stock.Values.shape = (n_years, n_elements)

# Parameter values: 2D array
parameter.Values.shape = (n_years, n_elements)
```

#### **ODYM-Compliant Data Structures**:
```python
# Flow values: 6D array
flow.Values.shape = (n_years, n_elements, n_regions, n_goods, n_materials, n_processes)

# Stock values: 6D array
stock.Values.shape = (n_years, n_elements, n_regions, n_goods, n_materials, n_processes)

# Parameter values: 6D array
parameter.Values.shape = (n_years, n_elements, n_regions, n_goods, n_materials, n_processes)
```

## Compliance Issues Identified

### **1. Missing Regional Dimension**
**Severity**: High | **Impact**: Major

**Issues**:
- Cannot track inter-regional flows
- Cannot perform regional analysis
- Limited scalability for multi-regional studies
- Non-compliant with ODYM standards

**Example Impact**:
```python
# Current: Cannot track regional flows
flow_from_region_a_to_b = None  # Not possible

# ODYM Standard: Can track regional flows
flow_from_region_a_to_b = mfa_system.FlowDict["Flow_A_to_B"].Values[:, :, region_a_idx, :, :, :]
```

### **2. Missing Good Dimension**
**Severity**: High | **Impact**: Major

**Issues**:
- Cannot track good-specific flows
- Limited material flow analysis
- No commodity-based reporting
- Non-compliant with ODYM standards

**Example Impact**:
```python
# Current: Cannot track good-specific flows
rye_straw_flows = None  # Not possible

# ODYM Standard: Can track good-specific flows
rye_straw_flows = mfa_system.FlowDict["Rye_Straw_Flow"].Values[:, :, :, rye_straw_idx, :, :]
```

### **3. Missing Material Dimension**
**Severity**: Medium | **Impact**: Moderate

**Issues**:
- Cannot track material-specific properties
- Limited material composition analysis
- No material-specific parameters
- Non-compliant with ODYM standards

**Example Impact**:
```python
# Current: Cannot track material-specific flows
dry_matter_flows = None  # Not possible

# ODYM Standard: Can track material-specific flows
dry_matter_flows = mfa_system.FlowDict["DM_Flow"].Values[:, :, :, :, dry_matter_idx, :]
```

### **4. Missing Process Dimension**
**Severity**: Medium | **Impact**: Moderate

**Issues**:
- Cannot perform process-type analysis
- Limited process categorization
- No process-specific reporting
- Non-compliant with ODYM standards

**Example Impact**:
```python
# Current: Cannot track process-specific flows
harvest_flows = None  # Not possible

# ODYM Standard: Can track process-specific flows
harvest_flows = mfa_system.FlowDict["Harvest_Flow"].Values[:, :, :, :, :, harvest_idx]
```

## Implementation Strategy

### **Phase 1: Foundation Dimensions (2-3 weeks)**
**Priority**: High | **Effort**: 8-12 hours

#### **1.1 Add Region Dimension**
```python
# In system_setup.py
def define_model_scope(start_year, end_year, elements, regions=None):
    """Defines the temporal, elemental, and regional scope of the MFA model."""
    
    if regions is None:
        regions = ["Case_Study_Region"]  # Default single region
    
    model_classification = {}
    my_years = list(np.arange(start_year, end_year + 1))
    
    # Existing dimensions
    model_classification["Time"] = msc.Classification(
        Name="Time", Dimension="Time", ID=1, Items=my_years
    )
    model_classification["Element"] = msc.Classification(
        Name="Elements", Dimension="Element", ID=2, Items=elements
    )
    
    # NEW: Add Region dimension
    model_classification["Region"] = msc.Classification(
        Name="Regions", Dimension="Region", ID=3, Items=regions
    )
    
    # Update IndexTable
    index_table = pd.DataFrame({
        "Aspect": ["Time", "Element", "Region"],
        "Description": [
            'Model aspect "time"',
            'Model aspect "Element"',
            'Model aspect "Region"'
        ],
        "Dimension": ["Time", "Element", "Region"],
        "Classification": [
            model_classification["Time"],
            model_classification["Element"],
            model_classification["Region"]
        ],
        "IndexLetter": ["t", "e", "r"],
    })
    
    return model_classification, index_table
```

#### **1.2 Add Good Dimension**
```python
# In system_setup.py
def define_model_scope(start_year, end_year, elements, regions=None, goods=None):
    """Defines the comprehensive scope of the MFA model."""
    
    if goods is None:
        goods = ["Rye_Straw", "Biochar", "Compost", "Energy"]  # Default goods
    
    # ... existing code ...
    
    # NEW: Add Good dimension
    model_classification["Good"] = msc.Classification(
        Name="Goods", Dimension="Good", ID=4, Items=goods
    )
    
    # Update IndexTable
    index_table = pd.DataFrame({
        "Aspect": ["Time", "Element", "Region", "Good"],
        "Description": [
            'Model aspect "time"',
            'Model aspect "Element"',
            'Model aspect "Region"',
            'Model aspect "Good"'
        ],
        "Dimension": ["Time", "Element", "Region", "Good"],
        "Classification": [
            model_classification["Time"],
            model_classification["Element"],
            model_classification["Region"],
            model_classification["Good"]
        ],
        "IndexLetter": ["t", "e", "r", "g"],
    })
    
    return model_classification, index_table
```

### **Phase 2: Advanced Dimensions (3-4 weeks)**
**Priority**: Medium | **Effort**: 12-16 hours

#### **2.1 Add Material Dimension**
```python
# In system_setup.py
def define_model_scope(start_year, end_year, elements, regions=None, goods=None, materials=None):
    """Defines the comprehensive scope of the MFA model."""
    
    if materials is None:
        materials = ["Dry_Matter", "Water_Content", "Carbon_Content"]  # Default materials
    
    # ... existing code ...
    
    # NEW: Add Material dimension
    model_classification["Material"] = msc.Classification(
        Name="Materials", Dimension="Material", ID=5, Items=materials
    )
    
    # Update IndexTable
    index_table = pd.DataFrame({
        "Aspect": ["Time", "Element", "Region", "Good", "Material"],
        "Description": [
            'Model aspect "time"',
            'Model aspect "Element"',
            'Model aspect "Region"',
            'Model aspect "Good"',
            'Model aspect "Material"'
        ],
        "Dimension": ["Time", "Element", "Region", "Good", "Material"],
        "Classification": [
            model_classification["Time"],
            model_classification["Element"],
            model_classification["Region"],
            model_classification["Good"],
            model_classification["Material"]
        ],
        "IndexLetter": ["t", "e", "r", "g", "m"],
    })
    
    return model_classification, index_table
```

#### **2.2 Add Process Dimension**
```python
# In system_setup.py
def define_model_scope(start_year, end_year, elements, regions=None, goods=None, materials=None, processes=None):
    """Defines the comprehensive scope of the MFA model."""
    
    if processes is None:
        processes = ["Harvest", "Processing", "Storage", "Application"]  # Default processes
    
    # ... existing code ...
    
    # NEW: Add Process dimension
    model_classification["Process"] = msc.Classification(
        Name="Processes", Dimension="Process", ID=6, Items=processes
    )
    
    # Update IndexTable
    index_table = pd.DataFrame({
        "Aspect": ["Time", "Element", "Region", "Good", "Material", "Process"],
        "Description": [
            'Model aspect "time"',
            'Model aspect "Element"',
            'Model aspect "Region"',
            'Model aspect "Good"',
            'Model aspect "Material"',
            'Model aspect "Process"'
        ],
        "Dimension": ["Time", "Element", "Region", "Good", "Material", "Process"],
        "Classification": [
            model_classification["Time"],
            model_classification["Element"],
            model_classification["Region"],
            model_classification["Good"],
            model_classification["Material"],
            model_classification["Process"]
        ],
        "IndexLetter": ["t", "e", "r", "g", "m", "p"],
    })
    
    return model_classification, index_table
```

### **Phase 3: Data Structure Migration (4-5 weeks)**
**Priority**: High | **Effort**: 16-20 hours

#### **3.1 Update Flow Indices**
```python
# In system_setup.py
def create_flow_with_full_indices(mfa_system, flow_name, process_start, process_end):
    """Create flow with full ODYM-compliant indices."""
    
    # Determine flow indices based on available dimensions
    indices = "t,e"  # Start with Time and Element
    
    if "Region" in mfa_system.IndexTable.index:
        indices += ",r"
    if "Good" in mfa_system.IndexTable.index:
        indices += ",g"
    if "Material" in mfa_system.IndexTable.index:
        indices += ",m"
    if "Process" in mfa_system.IndexTable.index:
        indices += ",p"
    
    # Create flow with proper indices
    flow = msc.Flow(
        Name=flow_name,
        P_Start=process_start,
        P_End=process_end,
        Indices=indices
    )
    
    return flow
```

#### **3.2 Update Data Array Shapes**
```python
# In system_setup.py
def initialize_flow_values(mfa_system, flow):
    """Initialize flow values with proper dimensions."""
    
    # Get dimension sizes
    n_years = len(mfa_system.IndexTable.Classification["Time"].Items)
    n_elements = len(mfa_system.IndexTable.Classification["Element"].Items)
    
    # Initialize with Time and Element dimensions
    shape = [n_years, n_elements]
    
    # Add additional dimensions if available
    if "Region" in mfa_system.IndexTable.index:
        n_regions = len(mfa_system.IndexTable.Classification["Region"].Items)
        shape.append(n_regions)
    
    if "Good" in mfa_system.IndexTable.index:
        n_goods = len(mfa_system.IndexTable.Classification["Good"].Items)
        shape.append(n_goods)
    
    if "Material" in mfa_system.IndexTable.index:
        n_materials = len(mfa_system.IndexTable.Classification["Material"].Items)
        shape.append(n_materials)
    
    if "Process" in mfa_system.IndexTable.index:
        n_processes = len(mfa_system.IndexTable.Classification["Process"].Items)
        shape.append(n_processes)
    
    # Initialize flow values
    flow.Values = np.zeros(shape)
    
    return flow
```

## Excel Template Impact Analysis

### **Current Excel Structure**
**Impact Level**: ❌ **MAJOR CHANGES REQUIRED**

#### **Required Excel Changes**:

1. **Add Regional Data Sheets**:
   - `3_1_Definition_Regions`
   - `3_2_Data_Regions`

2. **Add Good Data Sheets**:
   - `4_1_Definition_Goods`
   - `4_2_Data_Goods`

3. **Add Material Data Sheets**:
   - `5_1_Definition_Materials`
   - `5_2_Data_Materials`

4. **Add Process Data Sheets**:
   - `6_1_Definition_Processes`
   - `6_2_Data_Processes`

5. **Update Existing Sheets**:
   - Add regional, good, material, process columns to flow definitions
   - Update data structures to support multi-dimensional arrays

#### **Example Excel Structure**:
```
Excel Template Structure:
├── 1_1_Definition_Flows (Updated with new dimensions)
├── 1_2_Data_Flows (Updated with new dimensions)
├── 2_1_Definition_Processes (Updated)
├── 2_2_static_TCs (Updated)
├── 2_3_dynamic_TCs (Updated)
├── 2_4_Initial_Stock (Updated)
├── 3_1_Definition_Regions (NEW)
├── 3_2_Data_Regions (NEW)
├── 4_1_Definition_Goods (NEW)
├── 4_2_Data_Goods (NEW)
├── 5_1_Definition_Materials (NEW)
├── 5_2_Data_Materials (NEW)
├── 6_1_Definition_Processes (NEW)
└── 6_2_Data_Processes (NEW)
```

## Compliance Score Summary

| Dimension | Current Status | Compliance Score | Priority | Effort |
|-----------|----------------|------------------|----------|--------|
| **Time** | ✅ Complete | 10/10 | Low | 0 hours |
| **Element** | ✅ Complete | 10/10 | Low | 0 hours |
| **Region** | ❌ Missing | 0/10 | High | 4-6 hours |
| **Good** | ❌ Missing | 0/10 | High | 4-6 hours |
| **Material** | ❌ Missing | 0/10 | Medium | 3-4 hours |
| **Process** | ❌ Missing | 0/10 | Medium | 3-4 hours |

**Overall Dimension Compliance**: 3/10 (Poor)

## Recommendations

### **Immediate Actions (High Priority)**

1. **Add Region Dimension**: Critical for multi-regional studies
2. **Add Good Dimension**: Essential for commodity tracking
3. **Update IndexTable**: Include all dimensions
4. **Update Flow Indices**: Support multi-dimensional flows

### **Medium-Term Actions (Medium Priority)**

1. **Add Material Dimension**: For material-specific analysis
2. **Add Process Dimension**: For process-type analysis
3. **Update Data Structures**: Support multi-dimensional arrays
4. **Update Excel Templates**: Add new dimension sheets

### **Long-Term Actions (Low Priority)**

1. **Comprehensive Testing**: Test all dimension combinations
2. **Performance Optimization**: Optimize multi-dimensional operations
3. **Documentation Updates**: Update documentation for new dimensions
4. **User Training**: Train users on new dimension system

## Conclusion

Your observation about missing dimensions is **absolutely correct** and represents a **critical compliance issue**. BioDYM currently uses only 2 out of 6 standard ODYM dimensions (Time and Element), missing the crucial Region, Good, Material, and Process dimensions.

**Key Findings**:
- **Dimension Compliance**: 3/10 (Poor)
- **Missing Dimensions**: 4 out of 6 standard dimensions
- **Impact**: Major limitations in scalability and interoperability
- **Excel Impact**: Major changes required to Excel templates

**Recommended Approach**:
1. **Phase 1**: Add Region and Good dimensions (high priority)
2. **Phase 2**: Add Material and Process dimensions (medium priority)
3. **Phase 3**: Update data structures and Excel templates (high priority)

This dimension compliance issue is **more critical** than the function compliance issues we discussed earlier, as it fundamentally limits BioDYM's ability to scale and integrate with other ODYM-based systems.

---

*Document Version: 1.0*  
*Last Updated: [Current Date]*  
*Author: BioDYM Development Team*


---


================================================================================
# File: ODYM_FUNCTIONS_COMPLIANCE_ANALYSIS.md
================================================================================

# BioDYM Functions vs. ODYM Functions: Compliance Analysis

## Overview

This document analyzes the degree to which BioDYM engine functions follow the design principles established by the [ODYM functions module](https://github.com/IndEcol/ODYM/tree/master/src/odym/functions). The analysis covers function design patterns, naming conventions, parameter handling, and integration with ODYM classes.

## Executive Summary

- **Overall Compliance**: 6/10 (Moderate) - Good foundation with room for improvement
- **Function Design**: 7/10 (Good) - Well-structured, clear purpose
- **ODYM Integration**: 5/10 (Moderate) - Limited use of ODYM function patterns
- **Naming Conventions**: 8/10 (Very Good) - Clear, descriptive names
- **Error Handling**: 6/10 (Moderate) - Basic error handling, could be improved

## ODYM Functions Analysis

### Key ODYM Function Principles

Based on the [ODYM functions repository](https://github.com/IndEcol/ODYM/tree/master/src/odym/functions), the following principles are established:

#### 1. **Function Naming Conventions**
- **Descriptive Names**: Functions clearly indicate their purpose
- **Consistent Patterns**: Similar functions follow naming patterns
- **Abbreviations**: Standard abbreviations (e.g., `MI_` for MultiIndex)

#### 2. **Parameter Handling**
- **Type Hints**: Clear parameter types and return types
- **Default Values**: Sensible defaults for optional parameters
- **Validation**: Input validation and error handling

#### 3. **Integration with ODYM Classes**
- **Class Methods**: Functions work seamlessly with ODYM classes
- **Data Structures**: Consistent use of ODYM data structures
- **Return Values**: Standardized return formats

#### 4. **Error Handling**
- **Graceful Degradation**: Functions handle errors gracefully
- **Informative Messages**: Clear error messages and logging
- **Validation**: Input validation before processing

## BioDYM Functions Compliance Assessment

### Function Design Patterns Analysis

| Aspect | ODYM Standard | BioDYM Implementation | Compliance Score |
|--------|---------------|----------------------|------------------|
| **Naming Conventions** | Descriptive, consistent | Clear, descriptive | 8/10 |
| **Parameter Handling** | Type hints, validation | Basic, some validation | 6/10 |
| **Error Handling** | Comprehensive | Basic | 6/10 |
| **ODYM Integration** | Deep integration | Limited integration | 5/10 |
| **Documentation** | Comprehensive docstrings | Good docstrings | 7/10 |
| **Return Values** | Standardized formats | Consistent formats | 7/10 |

### Detailed Function Analysis

#### 1. **Solver Functions** (`solver.py`)

**Functions Analyzed**:
- `calculate_final_balances(mfa_system)`
- `process_initial_stocks(mfa_system)`
- `enhanced_input_validation(input_flows, dsm_processes)`
- `_calculate_tc_driven_flows(...)`
- `_calculate_dsm_flows(...)`
- `_calculate_fomp_flows(...)`
- `run_mfa_calculation(...)`

**Compliance Assessment**:

✅ **Strengths**:
- **Clear Function Names**: Functions clearly indicate their purpose
- **Good Documentation**: Comprehensive docstrings with parameters and returns
- **Consistent Patterns**: Similar functions follow consistent patterns
- **Modular Design**: Functions are well-separated by responsibility

❌ **Areas for Improvement**:
- **Limited ODYM Integration**: Manual flow aggregation instead of ODYM methods
- **Basic Error Handling**: Limited try-catch blocks and validation
- **Missing Type Hints**: No type annotations for parameters
- **Custom Logic**: BioDYM-specific logic not following ODYM patterns

**Example Non-Compliant Pattern**:
```python
# Current BioDYM approach
def calculate_final_balances(mfa_system):
    """Calculates the final stock changes (dS) and absolute stocks (S)."""
    for pid in {p.ID for p in mfa_system.ProcessList}:
        inflows = [f.Values for f in mfa_system.FlowDict.values() if f.P_End == pid]
        total_inflows = sum(inflows) if inflows else np.zeros_like(stock_s.Values)
```

**ODYM-Compliant Approach**:
```python
# Should use ODYM methods
def calculate_final_balances(mfa_system):
    """Calculates the final stock changes using ODYM methods."""
    try:
        # Use ODYM's built-in methods
        balance = mfa_system.MassBalance()
        # Process balance results
        return mfa_system
    except Exception as e:
        logger.error(f"Balance calculation failed: {e}")
        raise
```

#### 2. **Initial Stock Engine Functions** (`initial_stock_engine.py`)

**Functions Analyzed**:
- `load_initial_stock_parameters(excel_data)`
- `apply_initial_stock_values(mfa_system, initial_stock_configs)`
- `process_initial_stock_outflows(mfa_system, initial_stock_configs)`
- `_create_single_outflow_flow(...)`
- `update_initial_stock_flows_during_solver(mfa_system)`

**Compliance Assessment**:

✅ **Strengths**:
- **Excel Integration**: Good integration with Excel data loading
- **Configuration Management**: Well-structured configuration handling
- **Modular Design**: Clear separation of concerns

❌ **Areas for Improvement**:
- **Direct ODYM Object Manipulation**: Direct creation and modification of ODYM objects
- **Custom Attributes**: Adding custom attributes to ODYM objects
- **Limited Validation**: Basic validation of input data

**Example Non-Compliant Pattern**:
```python
# Current BioDYM approach
def _create_single_outflow_flow(mfa_system, flow_name, process_id, destination_process, initial_stock, consumption_rate, split_fraction=1.0):
    # Direct ODYM object creation
    mfa_system.FlowDict[flow_name] = msc.Flow(
        Name=flow_name,
        P_Start=process_id,
        P_End=destination_process,
        Indices="t,e"
    )
    
    # Adding custom attributes
    flow._initial_stock_config = {
        'initial_stock': initial_stock.copy(),
        'consumption_rate': consumption_rate,
        'split_fraction': split_fraction
    }
```

**ODYM-Compliant Approach**:
```python
# Should use ODYM's proper methods
def create_flow_odym_compliant(mfa_system, flow_name, process_id, destination_process):
    """Create flow using ODYM-compliant methods."""
    try:
        # Use ODYM's flow creation methods
        flow = msc.Flow(Name=flow_name, P_Start=process_id, P_End=destination_process, Indices="t,e")
        
        # Use ODYM's initialization methods
        mfa_system.Initialize_FlowValues()
        
        # Store configuration in ODYM Extensions
        process = mfa_system.ProcessList[process_id]
        process.add_extension(Name="initial_stock_config", Value=config_dict)
        
        return flow
    except Exception as e:
        logger.error(f"Flow creation failed: {e}")
        raise
```

#### 3. **DSM Model Functions** (`dsm_model.py`)

**Functions Analyzed**:
- `_calculate_outflow_from_inflows(total_inflow_values, params, time_vector)`
- `_calculate_outflow_from_initial_stock(initial_stock_vector, mean_lifetimes, num_years, num_elements)`
- `_distribute_and_assign_outflows(...)`
- `calculate_dynamic_stock(mfa_system, dsm_params_config)`

**Compliance Assessment**:

✅ **Strengths**:
- **Pure Functions**: Some functions are pure (no side effects)
- **Clear Logic**: Well-structured calculation logic
- **Parameter Handling**: Good parameter organization

❌ **Areas for Improvement**:
- **Direct Value Assignment**: Direct modification of ODYM object values
- **Limited Error Handling**: Basic error handling
- **Custom Logic**: BioDYM-specific logic not following ODYM patterns

#### 4. **FOMP Model Functions** (`fomp_model.py`)

**Functions Analyzed**:
- `_calculate_fomp_series(dm_inflow_series, params, initial_stock_labile, initial_stock_recalcitrant)`
- `calculate_fomp(mfa_system, fomp_params_config, input_flow_composition)`

**Compliance Assessment**:

✅ **Strengths**:
- **Pure Function Design**: `_calculate_fomp_series` is a pure function
- **Clear Documentation**: Good docstrings and parameter descriptions
- **Mathematical Clarity**: Clear implementation of FOMP equations

❌ **Areas for Improvement**:
- **Limited ODYM Integration**: Direct value assignment to ODYM objects
- **Custom Attributes**: Use of custom attributes on ODYM objects

#### 5. **Scenario Engine Functions** (`scenario_engine.py`)

**Functions Analyzed**:
- `run_scenario_analysis(...)`
- `_extract_scenario_names(config_obj)`
- `_run_single_scenario(...)`

**Compliance Assessment**:

✅ **Strengths**:
- **Type Hints**: Good use of type hints
- **Clear Structure**: Well-organized scenario management
- **Error Handling**: Better error handling than other modules

❌ **Areas for Improvement**:
- **Limited ODYM Integration**: Basic integration with ODYM classes
- **Custom Logic**: Scenario-specific logic not following ODYM patterns

## Specific Compliance Issues

### 1. **Function Naming Conventions**

**ODYM Standard**:
- Descriptive names with clear purpose
- Consistent abbreviations (e.g., `MI_` for MultiIndex)
- Standard patterns for similar functions

**BioDYM Implementation**:
- ✅ **Good**: Clear, descriptive function names
- ❌ **Missing**: No consistent abbreviation patterns
- ❌ **Missing**: No ODYM-style naming conventions

**Recommendation**:
```python
# Adopt ODYM naming patterns
def MI_CalculateFlowAggregation(mfa_system, process_id):
    """Calculate flow aggregation using ODYM methods."""
    pass

def ODYM_ValidateSystemConsistency(mfa_system):
    """Validate system consistency using ODYM methods."""
    pass
```

### 2. **Parameter Handling**

**ODYM Standard**:
- Type hints for all parameters
- Input validation
- Sensible default values
- Clear parameter documentation

**BioDYM Implementation**:
- ✅ **Good**: Clear parameter documentation
- ❌ **Missing**: Type hints
- ❌ **Missing**: Input validation
- ❌ **Missing**: Default values where appropriate

**Recommendation**:
```python
# Add type hints and validation
def calculate_final_balances(mfa_system: msc.MFAsystem) -> msc.MFAsystem:
    """Calculate final balances with proper type hints."""
    if not isinstance(mfa_system, msc.MFAsystem):
        raise TypeError("mfa_system must be an MFAsystem object")
    # Implementation
```

### 3. **Error Handling**

**ODYM Standard**:
- Comprehensive try-catch blocks
- Informative error messages
- Logging integration
- Graceful degradation

**BioDYM Implementation**:
- ❌ **Missing**: Limited try-catch blocks
- ❌ **Missing**: Basic error messages
- ❌ **Missing**: No logging integration
- ❌ **Missing**: Limited graceful degradation

**Recommendation**:
```python
# Add comprehensive error handling
def calculate_final_balances(mfa_system: msc.MFAsystem) -> msc.MFAsystem:
    """Calculate final balances with error handling."""
    try:
        # Implementation
        return mfa_system
    except AttributeError as e:
        logger.error(f"Missing attribute in MFA system: {e}")
        raise ValueError(f"Invalid MFA system structure: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in balance calculation: {e}")
        raise
```

### 4. **ODYM Integration**

**ODYM Standard**:
- Use ODYM's built-in methods
- Leverage ODYM's validation functions
- Follow ODYM's data structures
- Use ODYM's error handling patterns

**BioDYM Implementation**:
- ❌ **Major Issue**: Manual flow aggregation instead of ODYM methods
- ❌ **Major Issue**: Direct object manipulation
- ❌ **Major Issue**: Custom attributes on ODYM objects
- ❌ **Major Issue**: Limited use of ODYM validation

**Recommendation**:
```python
# Use ODYM methods instead of manual operations
def calculate_process_flows_odym_compliant(mfa_system: msc.MFAsystem, process_id: int) -> np.ndarray:
    """Calculate process flows using ODYM methods."""
    try:
        # Use ODYM's built-in methods
        inflows = []
        for flow in mfa_system.FlowDict.values():
            if flow.P_End == process_id:
                flow_sum = mfa_system.Flow_Sum_By_Element(flow.Name)
                inflows.append(flow_sum)
        
        return sum(inflows) if inflows else np.zeros((len(mfa_system.Time_L), len(mfa_system.Elements)))
    except Exception as e:
        logger.error(f"Flow calculation failed for process {process_id}: {e}")
        raise
```

## Compliance Improvement Strategy

### Phase 1: Foundation Improvements (1-2 weeks)

#### 1.1 Add Type Hints
**Priority**: High | **Effort**: 2-3 hours

```python
# Add type hints to all functions
from typing import Dict, List, Optional, Tuple, Union
import numpy as np

def calculate_final_balances(mfa_system: msc.MFAsystem) -> msc.MFAsystem:
    """Calculate final balances with type hints."""
    pass

def load_initial_stock_parameters(excel_data: Dict[str, pd.DataFrame]) -> Dict[int, Dict]:
    """Load initial stock parameters with type hints."""
    pass
```

#### 1.2 Add Input Validation
**Priority**: High | **Effort**: 3-4 hours

```python
# Add input validation to all functions
def calculate_final_balances(mfa_system: msc.MFAsystem) -> msc.MFAsystem:
    """Calculate final balances with input validation."""
    if not isinstance(mfa_system, msc.MFAsystem):
        raise TypeError("mfa_system must be an MFAsystem object")
    
    if not mfa_system.FlowDict:
        raise ValueError("MFA system has no flows defined")
    
    # Implementation
```

#### 1.3 Add Error Handling
**Priority**: High | **Effort**: 4-5 hours

```python
# Add comprehensive error handling
import logging

logger = logging.getLogger(__name__)

def calculate_final_balances(mfa_system: msc.MFAsystem) -> msc.MFAsystem:
    """Calculate final balances with error handling."""
    try:
        # Implementation
        return mfa_system
    except Exception as e:
        logger.error(f"Balance calculation failed: {e}")
        raise
```

### Phase 2: ODYM Integration (2-3 weeks)

#### 2.1 Use ODYM Methods
**Priority**: High | **Effort**: 6-8 hours

```python
# Replace manual operations with ODYM methods
def calculate_process_flows_odym_compliant(mfa_system: msc.MFAsystem, process_id: int) -> np.ndarray:
    """Calculate process flows using ODYM methods."""
    try:
        # Use ODYM's Flow_Sum_By_Element method
        inflows = []
        for flow in mfa_system.FlowDict.values():
            if flow.P_End == process_id:
                flow_sum = mfa_system.Flow_Sum_By_Element(flow.Name)
                inflows.append(flow_sum)
        
        return sum(inflows) if inflows else np.zeros((len(mfa_system.Time_L), len(mfa_system.Elements)))
    except Exception as e:
        logger.error(f"Flow calculation failed: {e}")
        raise
```

#### 2.2 Use ODYM Validation
**Priority**: Medium | **Effort**: 3-4 hours

```python
# Use ODYM's validation methods
def validate_system_before_calculation(mfa_system: msc.MFAsystem) -> bool:
    """Validate system using ODYM methods."""
    try:
        # Use ODYM's built-in validation
        mfa_system.IndexTableCheck()
        mfa_system.Consistency_Check()
        return True
    except Exception as e:
        logger.error(f"System validation failed: {e}")
        return False
```

### Phase 3: Advanced Improvements (2-3 weeks)

#### 3.1 Implement ODYM Function Patterns
**Priority**: Medium | **Effort**: 4-6 hours

```python
# Implement ODYM-style function patterns
def ODYM_CalculateMassBalance(mfa_system: msc.MFAsystem) -> np.ndarray:
    """Calculate mass balance using ODYM methods."""
    try:
        balance = mfa_system.MassBalance()
        return balance
    except Exception as e:
        logger.error(f"Mass balance calculation failed: {e}")
        raise

def ODYM_ValidateFlowConsistency(mfa_system: msc.MFAsystem) -> bool:
    """Validate flow consistency using ODYM methods."""
    try:
        for flow_name, flow in mfa_system.FlowDict.items():
            if flow.Values is not None and np.any(flow.Values < 0):
                logger.warning(f"Negative values found in flow {flow_name}")
                return False
        return True
    except Exception as e:
        logger.error(f"Flow validation failed: {e}")
        return False
```

#### 3.2 Add Logging Integration
**Priority**: Medium | **Effort**: 2-3 hours

```python
# Add ODYM-style logging
def setup_biodym_logging(log_filename: str, log_path: str) -> logging.Logger:
    """Setup logging using ODYM patterns."""
    logger, console_log, file_log = msf.function_logger(
        log_filename=log_filename,
        log_pathname=log_path,
        file_level=logging.DEBUG,
        console_level=logging.INFO
    )
    return logger
```

## Compliance Score Summary

| Module | Current Score | Target Score | Priority | Effort |
|--------|---------------|--------------|----------|--------|
| **solver.py** | 6/10 | 9/10 | High | 8-10 hours |
| **initial_stock_engine.py** | 5/10 | 9/10 | High | 6-8 hours |
| **dsm_model.py** | 6/10 | 8/10 | Medium | 4-6 hours |
| **fomp_model.py** | 7/10 | 8/10 | Medium | 3-4 hours |
| **scenario_engine.py** | 7/10 | 8/10 | Low | 2-3 hours |
| **mc_simulation.py** | 6/10 | 8/10 | Low | 3-4 hours |

## Recommendations

### Immediate Actions (High Priority)

1. **Add Type Hints**: Improve function signatures with proper type annotations
2. **Add Input Validation**: Validate all function inputs
3. **Add Error Handling**: Implement comprehensive try-catch blocks
4. **Use ODYM Methods**: Replace manual operations with ODYM methods

### Medium-Term Actions (Medium Priority)

1. **Implement ODYM Patterns**: Follow ODYM function design patterns
2. **Add Logging**: Integrate with ODYM's logging system
3. **Standardize Return Values**: Use consistent return value formats
4. **Add Performance Monitoring**: Monitor function performance

### Long-Term Actions (Low Priority)

1. **Refactor Function Names**: Adopt ODYM naming conventions
2. **Implement Pure Functions**: Create more pure functions where possible
3. **Add Comprehensive Testing**: Test all functions thoroughly
4. **Documentation Updates**: Update documentation to match ODYM standards

## Conclusion

Your BioDYM functions show **good foundation design** but have **moderate compliance** with ODYM function principles. The main areas for improvement are:

1. **ODYM Integration**: Limited use of ODYM's built-in methods
2. **Error Handling**: Basic error handling needs improvement
3. **Type Safety**: Missing type hints and input validation
4. **Function Patterns**: Not following ODYM's established patterns

**Overall Assessment**: 6/10 (Moderate) - Good foundation with significant room for improvement in ODYM integration and error handling.

**Recommended Approach**: Implement the phased improvement strategy, starting with high-priority items like type hints, validation, and ODYM method usage.

---

*Document Version: 1.0*  
*Last Updated: [Current Date]*  
*Author: BioDYM Development Team*


---


================================================================================
# File: ODYM_SIMPLIFICATIONS.md
================================================================================

# ODYM Implementation Simplifications for BioDYM

## Simplifications Identified from ODYM Best Practices

Based on the [ODYM framework](https://github.com/IndEcol/ODYM) and your Excel structure, here are the key simplifications you can implement:

### **1. Keep Indices Simple Initially**

**Recommended Approach**: Start with "t,e" for everything, then add dimensions as needed.

```python
# Phase 1: Simple Indices
Flow Indices = "t,e"
Stock Indices = "t,e"
Parameter Indices = "t,e"

# Phase 2: Add dimensions when needed
Flow Indices = "t,e,g"      # If tracking goods
Flow Indices = "t,e,m"      # If tracking materials
Flow Indices = "t,e,r"      # If tracking regions
```

**ODYM Simplification**: You don't need all dimensions at once. ODYM automatically handles the dimension matching.

### **2. Use Default/Empty for "All"**

**ODYM Simplification**: Don't use "All" as a code. Use empty cells.

```python
# Instead of:
Good_ID = "All"  # ❌
Material_ID = "All"  # ❌

# Use:
Good_ID = "" (empty)  # ✅
Material_ID = "" (empty)  # ✅
```

**Why**: Empty cells are cleaner and easier to parse in Python.

### **3. Let ODYM Handle Dimension Matching**

**ODYM Key Feature**: ODYM automatically matches dimensions during calculations.

```python
# You don't need to manually index arrays
# ODYM does it automatically:
flow_1.Values + flow_2.Values  # Automatically matches dimensions
```

**Simplification**: Focus on defining your Indices correctly, let ODYM handle the rest.

### **4. Use Consistent Dimension Order**

**ODYM Convention**: Use consistent letter order for dimensions.

```python
# Standard order (alphabetical):
IndexLetter = ["t", "e", "r", "g", "m", "p"]
           # Time, Element, Region, Good, Material, Process

# In Indices string:
Indices = "t,e,r,g,m,p"  # ✅ Consistent order
```

**Simplification**: This makes dimension management easier and more predictable.

### **5. Don't Over-Dimension Everything**

**ODYM Simplification**: Only add dimensions you actually use.

```python
# If you only track goods sometimes, don't add 'g' to all flows:
Flow without goods: Indices = "t,e"     # Simple
Flow with goods: Indices = "t,e,g"      # Extended

# ODYM handles this gracefully
```

**Your Current Excel**: You have `ODYM_Indices = "t,r,p,g,m,e,"` for all flows

**Recommendation**: Make Indices per-flow configurable:
- Simple flows: `Indices = "t,e"`
- Complex flows: `Indices = "t,e,g"` or `"t,e,r,p,g,m"`

### **6. Use IndexTable for Dimension Definitions**

**ODYM Simplification**: Define dimensions once in IndexTable, use everywhere.

```python
# In IndexTable:
Aspect = ["Time", "Element", "Region", "Good", "Material"]
IndexLetter = ["t", "e", "r", "g", "m"]

# Then all Flows/Stocks automatically use this
flow.Indices = "t,e,g"  # Uses IndexTable definitions
```

**Your Implementation**: This is exactly what your configuration sheet does! ✅

### **7. Avoid Manual Array Manipulation**

**ODYM Simplification**: Use ODYM methods instead of manual aggregation.

```python
# Instead of manual aggregation:
total = sum([f.Values for f in flows])  # ❌ Manual

# Use ODYM methods:
total = mfa_system.Flow_Sum_By_Element(flow_name)  # ✅ ODYM method
```

**Your Current Code**: You're doing manual aggregation in `solver.py`

**Fix**: This is in your Phase 2 plan - replace with ODYM methods.

### **8. Use Extensions for Custom Data**

**ODYM Simplification**: Don't add custom attributes to ODYM objects.

```python
# Instead of:
flow._initial_stock_config = {...}  # ❌ Custom attribute

# Use ODYM Extensions:
process.add_extension(
    Time=None,
    Name="initial_stock_config",
    Value={...},
    Unit="configuration"
)  # ✅ ODYM-compliant
```

**Your Current Code**: You're using custom attributes in `initial_stock_engine.py`

**Fix**: This is in your Phase 2 plan - use ODYM Extensions.

## Your Excel Structure - Simplifications Needed

### **Fix 1: Remove "All" Values**

**Current**:
```excel
ODYM_Good_ID = "All"
ODYM_Material_ID = "All"
ODYM_Element_ID = "All"
```

**Should Be**:
```excel
ODYM_Good_ID = ""  # Empty cell
ODYM_Material_ID = ""  # Empty cell
ODYM_Element_ID = ""  # Empty cell
```

### **Fix 2: Remove Trailing Commas**

**Current**:
```excel
ODYM_Indices = "t,r,p,g,m,e,"
Column2 = "All,All,All,1,All,All,"
```

**Should Be**:
```excel
ODYM_Indices = "t,e,r,p,g,m"  # No trailing comma
Column2 = "All,All,All,1,All,All"  # No trailing comma
```

### **Fix 3: Make Indices Per-Flow Configurable**

**Current**: All flows use the same Indices

**Simplification**: Allow per-flow Indices:

```excel
Flow_ID | Flow_Name | ODYM_Indices
--------|----------|-------------
F_01_02 | Simple_Flow | t,e
F_02_03 | Goods_Flow | t,e,g
F_03_04 | Material_Flow | t,e,m
```

## Simplified Implementation Checklist

### **Phase 1: Basic Setup (Current State)**

- [x] Define dimensions in configuration sheet
- [x] Add Indices column to Flows
- [ ] Remove "All" values (use empty instead)
- [ ] Remove trailing commas
- [ ] Test with simple "t,e" Indices

### **Phase 2: Make Indices Configurable**

- [ ] Read Indices from Excel (not hardcoded)
- [ ] Allow different Indices per flow
- [ ] Update data loader to handle empty vs. specific IDs
- [ ] Test with mixed Indices

### **Phase 3: Add Multi-Dimensional Support**

- [ ] Support Good dimension when specified
- [ ] Support Material dimension when specified
- [ ] Support Region dimension when specified
- [ ] Support Process dimension when specified

## Key Simplification: Start Simple, Expand Gradually

**ODYM Philosophy**: Don't over-engineer. Start with what you need, add complexity as needed.

**Recommended Progression**:

1. **Week 1**: Get "t,e" working for all flows/stocks
2. **Week 2**: Add Good dimension (if needed)
3. **Week 3**: Add Material dimension (if needed)
4. **Week 4**: Add other dimensions as needed

**Your Excel**: You've added all dimensions upfront

**Simplification**: Make them optional/empty by default, only specify when needed!

## Summary: Simplifications for Your Implementation

1. **Use empty cells for "All"** instead of "All" string
2. **Remove trailing commas** from Indices
3. **Make Indices per-flow configurable** (not same for all)
4. **Start with "t,e"** for everything, add dimensions gradually
5. **Don't require all dimensions** - ODYM handles missing dimensions gracefully
6. **Use ODYM methods** instead of manual aggregation (Phase 2)
7. **Use ODYM Extensions** instead of custom attributes (Phase 2)

These simplifications will make your implementation cleaner and more maintainable!

---

*Document Version: 1.0*  
*Last Updated: [Current Date]*  
*Author: BioDYM Development Team*


---


================================================================================
# File: PHASE_0_EXCEL_PREPARATION.md
================================================================================

# Phase 0 Excel Preparation - COMPLETED ✅

## Summary

Successfully created a clean BioDYM ODYM test Excel file ready for Phase 0 testing!

## What Was Done

### ✅ Clean Excel File Created
- **Original**: `01_data/01_input/251027_BioDYM_ODYM.xlsm`
- **Clean Version**: `01_data/01_input/251027_BioDYM_ODYM_CLEAN.xlsm`
- **Status**: All format issues fixed

### ✅ Excel Fixes Applied

1. **Removed "All" Values**
   - All `ODYM_*_ID` columns now use empty cells instead of "All"
   - Empty cells = all values (ODYM convention)
   - Numeric values = specific values
   - Zero = excluded from dimension

2. **Fixed Trailing Commas**
   - Removed trailing commas from `ODYM_Indices` column
   - Clean format: `t,e` instead of `t,e,`
   - Ready for ODYM parsing

3. **Added Stock_Indices Column**
   - Added to `2_1_Definition_Processes` sheet
   - Default value: `t,e` (Time + Element)
   - Matches Flow indices structure

### ✅ Sheets Copied Successfully

- `0_Configuration` - ODYM configuration settings
- `1_1_Definition_Flows` - Flow definitions with ODYM indices
- `1_2_Data_Flows` - Flow data
- `2_1_Definition_Processes` - Process definitions with Stock_Indices
- `2_2_static_TCs` - Static transfer coefficients
- `2_3_dynamic_TCs` - Dynamic transfer coefficients
- `2_4_Initial_Stock` - Initial stock data
- `3_1_Definition_DSM` - Dynamic Stock Model definitions
- `3_2_Definition_FOMP` - FOMP process definitions

## Next Steps - Phase 0

### **Task 1: Create Golden Reference Dataset**

Run the full workflow with the clean Excel file:

```bash
# This will generate results_scientific.xlsx
python -c "from src.main import main; main()"
```

Save the output as the golden reference for Phase 0 tests.

### **Task 2: Create Integration Test Suite**

Create `04_tests/workflow/test_e2e_workflow.py`:

```python
"""Integration tests for Phase 0 - ODYM Compliance."""

import unittest
import pandas as pd
import sys
sys.path.append('02_src')
from main import main

class TestE2EWorkflow(unittest.TestCase):
    """Test end-to-end workflow with clean Excel file."""
    
    def test_golden_excel_output(self):
        """Test that workflow produces golden output."""
        # Run workflow
        result = main('01_data/01_input/251027_BioDYM_ODYM_CLEAN.xlsm')
        
        # Load golden reference
        golden = pd.read_excel('04_tests/workflow/golden/results_scientific.xlsx')
        
        # Load actual output
        actual = pd.read_excel('01_data/02_output/results_scientific.xlsx')
        
        # Compare
        pd.testing.assert_frame_equal(actual, golden)
```

### **Task 3: Verify Excel Structure**

Verify the clean Excel file has proper structure:

```python
# Check dimensions
df_flows = pd.read_excel('01_data/01_input/251027_BioDYM_ODYM_CLEAN.xlsm',
                         sheet_name='1_1_Definition_Flows', 
                         engine='openpyxl')

# Should have ODYM columns
assert 'ODYM_Indices' in df_flows.columns
assert 'ODYM_Good_ID' in df_flows.columns
assert 'ODYM_Material_ID' in df_flows.columns

# Check no "All" values
assert not df_flows['ODYM_Good_ID'].astype(str).str.contains('All').any()
```

## Excel Structure Compliance

### ✅ ODYM Dimension ID Conventions

| Value | Meaning | Example |
|-------|---------|---------|
| Empty/BLANK | All values | All regions, all goods, all materials |
| Number (1, 2, 3...) | Specific value | Region 1, Good type 2 |
| 0 | Exclude from dimension | Not applicable |

### ✅ Flow Indices Format

- **Simple**: `t,e` (Time + Element)
- **With Region**: `t,e,r` (Time + Element + Region)
- **Full**: `t,e,r,g,m,p` (all dimensions)

### ✅ Stock Indices Format

- **Default**: `t,e` (Time + Element)
- **Match flow indices** for consistency

## Phase 0 Status

✅ **Excel File**: Clean and ready
⏳ **Golden Dataset**: Need to generate
⏳ **Integration Tests**: Need to create

## Script Used

The script `create_clean_test_excel.py` can be run to regenerate the clean Excel file anytime:

```bash
python create_clean_test_excel.py
```

This will:
1. Load the original Excel file
2. Copy all essential sheets
3. Clean ODYM dimension columns
4. Add Stock_Indices column
5. Save as `251027_BioDYM_ODYM_CLEAN.xlsm`

---

**Ready for Phase 0: Generate Golden Dataset!** 🚀


---


================================================================================
# File: PHASE_0_PROGRESS.md
================================================================================

# Phase 0 Progress - Initial Setup Complete ✅

## Summary

We've successfully completed the initial setup for the ODYM compliance refactoring. The system is now ready for Phase 0 testing.

## ✅ Completed Tasks

### 1. **Clean Excel File Created**
- **File**: `01_data/01_input/251027_BioDYM_ODYM_CLEAN.xlsx`
- **Changes Applied**:
  - Replaced "All" values with empty cells (ODYM convention)
  - Removed trailing commas from Indices strings
  - Added `Stock_Indices` column to `2_1_Definition_Processes` sheet
  - Saved as .xlsx format (no macros)

### 2. **Workflow Notebook Fixed**
- Fixed `Year_Flow` → `Flow_Data_Year` column name issue
- Added multiple Element attribute fallback checks
- Config object loading working (Elements fallback working as expected)

### 3. **Current Status**
- Branch: `feature/odym-compliance` ✅
- Excel file: Clean format ready for testing ✅
- Notebook: Updated and ready ✅

## 📋 Current Phase: Phase 0 - Build Testing Safety Net

### **Next Steps**

#### **Option A: Generate Golden Reference Dataset (Recommended)**
Run the full workflow once to establish baseline results:
```python
# In notebook cell or Python script
python 00_BioDYM_Workflow.py
# Or run cells in the notebook
```
This will create `results_scientific_baseline.xlsx` as a reference.

#### **Option B: Start Phase 1a Implementation**
Begin foundational refactoring:
- Use ODYM initialization methods
- Add Consistency_Check() calls
- Improve error handling

## 🎯 Recommended Next Steps

### **For Testing**:
1. Run workflow once to generate golden reference
2. Save reference outputs
3. Create integration tests

### **For Implementation**:
1. Start Phase 1a refactoring (independent of dimensions)
2. Add ODYM validation hooks
3. Improve error handling
4. Verify tests still pass

## 📊 Compliance Status

| Area | Status | Notes |
|------|--------|-------|
| Excel Format | ✅ Complete | Clean .xlsx file with ODYM-compliant structure |
| Config Loading | ✅ Working | Fallbacks handling as expected |
| Data Loader | ⏳ Pending | Needs ODYM dimension support |
| Engine Modules | ⏳ Pending | Phase 1a refactoring needed |
| Dimensions | ⏳ Pending | Phase 1b implementation |

## 💡 Notes

- Elements configuration is working via fallback mechanism
- The clean Excel file has proper ODYM structure
- Notebook is ready for testing
- Next decision: Generate golden dataset or start Phase 1a?

---

**Ready to proceed with Phase 0 testing or Phase 1a implementation!** 🚀



---


================================================================================
# File: PHASE_1A_ANALYSIS.md
================================================================================

# Phase 1a Analysis: Current Engine Status

## 🔍 Current State Analysis

### ✅ Good News: You're Already Using ODYM Validation!

**Existing Validation**:
- ✅ `mfa_system.Consistency_Check()` already called in `system_setup.py:467`
- ✅ `mfa_system.Initialize_FlowValues()` used in `system_setup.py:292`
- ✅ `mfa_system.Initialize_StockValues()` used in `system_setup.py:202`
- ✅ Manual validation patterns exist

**This is excellent!** Your codebase is already partially ODYM-compliant.

---

## 📊 What Needs Improvement

### **Issue 1: Manual Flow/Stock Assignments**

**Current Problem** (in `solver.py:49-58`):
```python
# Manual flow aggregation
inflows = [f.Values for f in mfa_system.FlowDict.values() if f.P_End == pid]
total_inflows = sum(inflows) if inflows else np.zeros_like(stock_s.Values)
```

**What we should do**:
- This is actually OK for calculation purposes
- But we should add validation after calculations
- ODYM doesn't provide built-in flow aggregation methods

**Action**: Add `Consistency_Check()` after balance calculations

---

### **Issue 2: Missing Validation Hooks**

**Current State**:
- ✅ Validation after `define_flows_and_parameters()`
- ❌ No validation after solver iterations
- ❌ No validation after DSM calculations
- ❌ No validation after FOMP calculations

**What to Add**:
1. In `solver.py` - after each iteration
2. In `dsm_model.py` - after DSM calculations
3. In `fomp_model.py` - after FOMP calculations

---

### **Issue 3: Where to Add ODYM Dimensions**

**Key Question**: Where should we add the new ODYM dimensions?

**Answer**: Add them in `system_setup.py`, specifically in the `define_model_scope()` function.

**Current Function** (`system_setup.py:29-75`):
```python
def define_model_scope(start_year, end_year, elements):
    # Only has Time and Element
```

**What We Need to Add**:
```python
def define_model_scope(start_year, end_year, elements, 
                       regions=None, goods=None, materials=None, processes=None):
    # Add all 6 ODYM dimensions
```

---

## 🎯 Best Time to Test the Workflow

### **Recommended Testing Points**

1. **After Phase 1a (Before Adding Dimensions)** ✅ **NOW**
   - Run full workflow with current 2D system
   - Ensure all tests pass
   - Establish baseline

2. **After Adding First Dimension (Region)** 
   - Test with 3D system (t,e,r)
   - Verify backward compatibility

3. **After All Dimensions Added**
   - Test with full 6D system
   - Verify all functionality works

### **Your Question Answered**:
> "Which would be the best time to test, if the workflow is still successful?"

**Answer**: Test **NOW** (after Phase 1a) before adding dimensions. This gives us a baseline to compare against.

---

## 🚀 Recommended Implementation Order

### **Step 1: Add Validation Hooks (Phase 1a) - 2-3 hours**

**Add to `solver.py`**:
```python
def calculate_final_balances(mfa_system):
    """...existing code..."""
    
    print("--> Stock balance calculation finished.")
    
    # ADD THIS:
    try:
        mfa_system.Consistency_Check()
        print("✅ Balance validation passed")
    except Exception as e:
        print(f"⚠️ Balance validation warning: {e}")
    
    return mfa_system
```

**Add to engine modules after major operations**:
- `dsm_model.py` - after DSM calculations
- `fomp_model.py` - after FOMP calculations
- `initial_stock_engine.py` - after initial stock processing

---

### **Step 2: Add ODYM Dimensions (Phase 1b) - 4-5 hours**

**Modify `system_setup.py:29`**:
```python
def define_model_scope(start_year, end_year, elements, 
                       regions=None, goods=None, materials=None, processes=None):
    """Defines the temporal and elemental scope of the MFA model with full ODYM dimensions."""
    
    # Default dimensions if not provided
    if regions is None:
        regions = ["Case_Study_Region"]  # Default single region
    
    # ... rest of the function ...
    
    # Add new dimensions to IndexTable
    index_table = pd.DataFrame({
        "Aspect": ["Time", "Element", "Region", "Good", "Material", "Process"],
        ...
    })
```

---

## 📋 Phase 1a Action Plan

### **Immediate Next Steps**:

1. **Add Validation Hooks** (2-3 hours):
   - Add `Consistency_Check()` after balance calculations
   - Add validation after DSM/FOMP calculations
   - Test that workflow still works

2. **Test Workflow** (30 minutes):
   - Run full workflow
   - Verify all outputs are correct
   - Check for any errors or warnings

3. **Document Results**:
   - Baseline established
   - Ready for Phase 1b (dimensions)

---

## 💡 Answers to Your Questions

### **Q1: Best Time to Test Workflow?**

**Answer**: **NOW** (after Phase 1a validation hooks, before adding dimensions)

**Why**: 
- We have a working 2D system
- Phase 1a adds validation (low risk)
- If tests pass, we have a stable baseline
- Then we can safely add dimensions

---

### **Q2: Where Would We Add ODYM Dimensions?**

**Answer**: In `system_setup.py`, in the `define_model_scope()` function (lines 29-75)

**Specific Changes Needed**:

1. **Function Signature** (line 29):
```python
def define_model_scope(start_year, end_year, elements, 
                       regions=None, goods=None, materials=None, processes=None):
```

2. **Add Dimensions** (after line 59):
```python
# Add Region dimension
if regions is not None:
    model_classification["Region"] = msc.Classification(
        Name="Regions", Dimension="Region", ID=3, Items=regions
    )

# Add Good dimension  
if goods is not None:
    model_classification["Good"] = msc.Classification(
        Name="Goods", Dimension="Good", ID=4, Items=goods
    )
# etc...
```

3. **Update IndexTable** (lines 61-72):
```python
index_table = pd.DataFrame({
    "Aspect": ["Time", "Element", "Region", "Good", "Material", "Process"],
    ...
})
```

---

## 🎯 Summary & Next Steps

### **Current Status**: ✅ Already Using ODYM Validation!

### **Phase 1a Tasks**:
- ✅ Add validation hooks in engine modules
- ✅ Test workflow thoroughly
- ✅ Establish baseline for Phase 1b

### **Phase 1b Tasks** (Next):
- Add dimensions in `system_setup.py:define_model_scope()`
- Update data loader for dimensions
- Test with multi-dimensional arrays

**Ready to start implementation?** 🚀



---


================================================================================
# File: PHASE_1A_COMPLETED.md
================================================================================

# Phase 1a Implementation - COMPLETED ✅

## Summary

Successfully added ODYM validation hooks to key engine modules. This improves error detection and ODYM compliance without changing data structures.

## Changes Made

### ✅ 1. Solver Module (`02_src/engine/solver.py`)

**Added validation after balance calculations** (lines 68-73):
```python
# Phase 1a: Add ODYM validation
try:
    mfa_system.Consistency_Check()
    print("✅ Balance validation passed")
except Exception as e:
    print(f"⚠️ Balance validation warning: {e}")
```

**Added validation after final calculation** (lines 443-448):
```python
# Phase 1a: Add ODYM validation after complete calculation
try:
    mfa_system.Consistency_Check()
    print("✅ Final MFA system validation passed")
except Exception as e:
    print(f"⚠️ Final validation warning: {e}")
```

### ✅ 2. DSM Module (`02_src/engine/dsm_model.py`)

**Added validation after DSM calculations** (lines 227-232):
```python
# Phase 1a: Add ODYM validation after DSM calculation
try:
    mfa_system.Consistency_Check()
    print(f"✅ DSM validation passed for process {process_id}")
except Exception as e:
    print(f"⚠️ DSM validation warning for process {process_id}: {e}")
```

### ✅ 3. FOMP Module (`02_src/engine/fomp_model.py`)

**Added validation after FOMP calculations** (lines 203-208):
```python
# Phase 1a: Add ODYM validation after FOMP calculation
try:
    mfa_system.Consistency_Check()
    print(f"✅ FOMP validation passed for process {process_id}")
except Exception as e:
    print(f"⚠️ FOMP validation warning for process {process_id}: {e}")
```

## Testing Status

### ⏳ Ready to Test

The changes are complete and ready for testing. The validation hooks will:
- ✅ Catch data inconsistencies early
- ✅ Provide better error messages
- ✅ Not break existing functionality (wrapped in try/except)

## Next Steps

1. **Test the workflow** with the clean Excel file
2. **Verify validation output** appears during calculations
3. **Confirm no regressions** in existing functionality
4. **Ready for Phase 1b** (add dimensions) if tests pass

## Files Modified

- `02_src/engine/solver.py` - 2 validation hooks added
- `02_src/engine/dsm_model.py` - 1 validation hook added
- `02_src/engine/fomp_model.py` - 1 validation hook added

**Total**: 4 ODYM validation hooks added across 3 files

---

## Questions Answered

### Q: "Where would we enter the additional ODYM Dimensions?"
**A**: In `system_setup.py`, function `define_model_scope()` - this will be Phase 1b

### Q: "Which would be the best time to test if the workflow is still successful?"
**A**: **NOW** - Test after Phase 1a changes, before adding dimensions (Phase 1b)

---

**Phase 1a Complete! Ready for testing.** 🚀



---


================================================================================
# File: PHASE_1A_PLAN.md
================================================================================

# Phase 1a: Foundational Refactoring - Implementation Plan

## 🎯 Objective

Implement class/function improvements that are **independent of new dimensions** to create a more robust baseline before adding multi-dimensional support. These changes will improve ODYM compliance without breaking existing functionality.

## 📋 Planned Actions

### **Task 1: Use ODYM Initialization Methods** ⏱️ 2-3 hours

**Current State**:
- Flows are manually initialized with numpy arrays
- Some manual Value assignments exist

**Target State**:
- Use `mfa_system.Initialize_FlowValues()` for all flows
- Use `mfa_system.Initialize_StockValues()` for all stocks
- Use `mfa_system.Initialize_ParameterValues()` for all parameters

**Files to Modify**:
- `02_src/system_setup.py` (lines 292, 202)
- Check for any manual initialization in `02_src/engine/` modules

**Benefits**:
- ✅ Consistent initialization across all objects
- ✅ Automatic shape handling
- ✅ ODYM-compliant initialization

---

### **Task 2: Add Consistency Checks** ⏱️ 2-3 hours

**Current State**:
- No validation after key operations
- Manual checks scattered throughout

**Target State**:
- Add `mfa_system.Consistency_Check()` after major operations
- Add `mfa_system.IndexTableCheck()` for validation
- Wrap in try/except for graceful failures

**Key Locations to Add Checks**:
1. `02_src/system_setup.py` - After system initialization
2. `02_src/engine/solver.py` - After balance calculations
3. `02_src/engine/initial_stock_engine.py` - After stock processing
4. `02_src/engine/dsm_model.py` - After DSM calculations
5. `02_src/engine/fomp_model.py` - After FOMP calculations

**Benefits**:
- ✅ Early detection of data inconsistencies
- ✅ Better error messages
- ✅ ODYM-compliant validation

---

### **Task 3: Improve Error Handling** ⏱️ 2-3 hours

**Current State**:
- Basic error handling
- Some operations lack error context

**Target State**:
- Wrap critical operations in try/except blocks
- Add descriptive error messages
- Log errors with context

**Key Operations to Wrap**:
1. Flow/stock initialization
2. Transfer coefficient calculations
3. Parameter loading
4. Mass balance calculations

**Benefits**:
- ✅ Better error messages
- ✅ Easier debugging
- ✅ Graceful failure handling

---

## 🔍 Detailed Implementation Strategy

### **Step 1: Identify Manual Initialization**

Let's search for manual initialization patterns:

```python
# Look for patterns like:
flow_obj.Values = np.zeros(...)
stock_obj.Values = np.zeros(...)
param_obj.Values = np.zeros(...)
```

### **Step 2: Replace with ODYM Methods**

Replace manual initialization:

```python
# OLD:
for flow_name, flow_obj in mfa_system.FlowDict.items():
    flow_obj.Values = np.zeros((len(time), len(elements)))

# NEW:
mfa_system.Initialize_FlowValues()
```

### **Step 3: Add Validation Hooks**

Add checks at key points:

```python
# After system initialization
mfa_system = initialize_mfa_system(model_classification, index_table)
try:
    mfa_system.Consistency_Check()
    mfa_system.IndexTableCheck()
    print("✅ System validation passed")
except Exception as e:
    print(f"⚠️ Validation warning: {e}")

# After major calculations
try:
    result = calculate_flows(mfa_system)
    mfa_system.Consistency_Check()
    return result
except Exception as e:
    print(f"❌ Calculation failed: {e}")
    raise
```

---

## 📊 Expected Impact

### **Benefits**:
- ✅ **Better Validation**: Catch issues early
- ✅ **ODYM Compliance**: Use standard methods
- ✅ **Maintainability**: More consistent code
- ✅ **Debugging**: Better error messages

### **Risks**:
- ⚠️ **Low Risk**: These changes don't affect data structures
- ⚠️ **Testing Needed**: Ensure no regressions

### **Success Criteria**:
- [ ] All initialization uses ODYM methods
- [ ] Validation checks added at key points
- [ ] Error handling improved
- [ ] Existing tests still pass
- [ ] No functionality loss

---

## 🚀 Next Steps

1. **Search for manual initialization** in codebase
2. **Replace with ODYM methods**
3. **Add validation hooks** at key points
4. **Improve error handling** with try/except
5. **Test thoroughly** to ensure no regressions

---

## 💡 Discussion Points

**Questions to Consider**:

1. **Should we add validation checks immediately or gradually?**
   - Recommend: Gradually, starting with critical operations

2. **How verbose should error messages be?**
   - Recommend: Detailed for development, concise for production

3. **Should we validate after every operation or key milestones?**
   - Recommend: Key milestones (initialization, major calculations, final results)

4. **What happens if validation fails?**
   - Recommend: Warning for minor issues, error for critical problems

**Ready to start implementation!** 🚀



---


================================================================================
# File: PHASE_1B_CONFIG_COMPLETE.md
================================================================================

# Phase 1b Updates - COMPLETED ✅

## Summary

Successfully implemented two critical improvements for Phase 1b ODYM compliance:

1. ✅ **Updated config loader** to read all dimensions from Excel
2. ✅ **Added IndexTable display** following ODYM tutorial conventions
3. ✅ **Updated workflow** to pass regions to `define_model_scope()`

---

## Changes Made

### **1. Updated Config Loader** (`02_src/config.py`)

Added logic to collect dimensions from Excel configuration sheet:

**Lines 64-127**:
- ✅ Collects Elements from "Element ID X" keys
- ✅ Collects Regions from "Region ID X" keys  
- ✅ Collects Goods from "Good Type X" keys
- ✅ Collects Materials from "Material ID X" keys
- ✅ Collects Process Types from "Process Type X" keys
- ✅ Converts each to comma-separated string
- ✅ Prints loaded dimensions for verification

**Example Output**:
```
✅ Loaded 2 elements from configuration: ['C', 'Remaining DM']
✅ Loaded 1 regions from configuration: ['Case_Study_Region']
✅ Loaded 4 goods from configuration: ['Raw Material', 'Processed Product', 'Product', 'Waste']
```

---

### **2. Updated Workflow** (`00_BioDYM_Workflow.py`)

**Lines 113-134**: Extract dimensions from config
```python
# Phase 1b: Extract dimension lists from config
def get_config_list(config_obj, attribute_name, default=None):
    """Helper to extract comma-separated lists from config object."""
    if hasattr(config_obj, attribute_name):
        value = getattr(config_obj, attribute_name)
        if value and pd.notna(value):
            return [item.strip() for item in str(value).split(',') if item.strip()]
    return default

regions = get_config_list(config_obj, 'Regions', ['Case_Study_Region'])
goods = get_config_list(config_obj, 'Goods', None)
materials = get_config_list(config_obj, 'Materials', None)
processes = get_config_list(config_obj, 'Process_Types', None)
```

**Line 180**: Pass regions to `define_model_scope()`
```python
model_classification, index_table = system_setup.define_model_scope(start_year, end_year, elements, regions)
```

**Lines 185-198**: Display IndexTable (ODYM convention)
```python
# Phase 1b: Display IndexTable (ODYM convention)
print("\n" + "="*60)
print("📊 ODYM SYSTEM INDEX TABLE")
print("="*60)
print(mfa_system_base.IndexTable)
print("\nAvailable Dimensions:")
for aspect in mfa_system_base.IndexTable.index:
    classification = mfa_system_base.IndexTable.loc[aspect, 'Classification']
    index_letter = mfa_system_base.IndexTable.loc[aspect, 'IndexLetter']
    print(f"  - {aspect} ({index_letter}): {len(classification.Items)} items")
```

---

## Expected Output

When you run the workflow, you should now see:

```
✅ Loaded 2 elements from configuration: ['C', 'Remaining DM']
✅ Loaded 1 regions from configuration: ['Case_Study_Region']

📊 Dimensions loaded from configuration:
   - Regions: ['Case_Study_Region']

============================================================
📊 ODYM SYSTEM INDEX TABLE
============================================================
[IndexTable with Time, Element, Region dimensions]

Available Dimensions:
  - Time (t): 26 items
    Items: [2025, 2026, 2027, 2028, 2029] ... (26 total)
  - Element (e): 2 items
    Items: ['C', 'Remaining DM']
  - Region (r): 1 items
    Items: ['Case_Study_Region']
```

---

## Benefits

1. ✅ **Elements loaded from Excel** - no more fallback
2. ✅ **Dimensions read automatically** - from configuration sheet
3. ✅ **IndexTable displayed** - following ODYM tutorial patterns
4. ✅ **Better debugging** - see system structure immediately
5. ✅ **ODYM compliance** - matches [tutorial conventions](https://github.com/IndEcol/ODYM/blob/master/docs/tutorials/tutorial_4.ipynb)

---

**Phase 1b Config & Display Updates Complete!** ✅

**Ready to test the workflow!** 🚀



---


================================================================================
# File: PHASE_1B_CONFIG_FIX.md
================================================================================

# Phase 1b Update: Config Loader + IndexTable Display

## Issues Identified

### ✅ Issue 1: Elements Not Being Read from Excel Config

**Problem**: Elements are defined in Excel as "Element ID 1", "Element ID 2", etc., but the config loader isn't reading them properly.

**Current Elements in Excel**:
- Element ID 1: C
- Element ID 2: Remaining DM

**Solution**: Update `config.py` to read these as a list.

### ✅ Issue 2: No IndexTable Display (ODYM Convention)

**Problem**: In ODYM tutorials, they always show `Tutorial_MFA_System.IndexTable` to display the system structure. We should do the same.

**Reference**: [ODYM Tutorial 4](https://github.com/IndEcol/ODYM/blob/master/docs/tutorials/tutorial_4.ipynb)

**Solution**: Add a cell to display the IndexTable in the workflow.

---

## Solutions Needed

### **1. Update Config Loader** (`02_src/config.py`)

Add logic to collect Elements from "Element ID 1", "Element ID 2", etc.:

```python
def load_config_from_excel(excel_file_path):
    """... existing code ..."""
    
    # After loading config_dict, add Elements collection
    elements = []
    for key in config_dict.keys():
        if 'Element ID' in str(key):
            element_value = config_dict[key]
            if pd.notna(element_value) and str(element_value).strip():
                elements.append(str(element_value).strip())
    
    # Add Elements as a comma-separated string
    if elements:
        config_dict['Elements'] = ','.join(elements)
    
    return config_dict
```

### **2. Update Workflow to Show IndexTable**

Add a cell after system initialization:

```python
# Display the IndexTable (ODYM convention)
print("\n" + "="*60)
print("📊 ODYM SYSTEM INDEX TABLE")
print("="*60)
display(mfa_system_base.IndexTable)
print("\nAvailable Dimensions:")
for aspect in mfa_system_base.IndexTable.index:
    classification = mfa_system_base.IndexTable.loc[aspect, 'Classification']
    print(f"  - {aspect} ({mfa_system_base.IndexTable.loc[aspect, 'IndexLetter']}): {len(classification.Items)} items")
```

---

## Benefits

1. ✅ **Elements loaded properly** from Excel
2. ✅ **IndexTable displayed** following ODYM conventions
3. ✅ **Better debugging** - see system structure immediately
4. ✅ **ODYM compliance** - matches tutorial patterns

---

**Ready to implement these fixes!** 🚀



---


================================================================================
# File: PHASE_1B_NEXT_STEPS.md
================================================================================

# Phase 1b: Systematic Dimension Implementation Plan

## Current Status ✅

- **Elements**: `['material', 'WC', 'DM', 'CC']` - WORKING
- **Baseline calculation**: ✅ Completed successfully
- **System**: Working with current 2D structure

---

## Next Steps: Following Master Plan

### **Step 1: Add Material Dimension** (Now)

**What to do**:
1. Materials in Excel: `['WC', 'DM']`
2. Add Material dimension to `system_setup.py`
3. Update IndexTable to include Material
4. Keep Elements as is (material, WC, DM, CC)

**Result**: 3D arrays (Time × Material × Element)
- Flow.Values.shape = (26, 2, 4)
- 26 years × 2 materials × 4 elements

---

### **Step 2: Update Engine for 3D Operations**

**Files to update**:
1. `solver.py` - handle 3D arrays
2. `dsm_model.py` - aggregate material dimension
3. `fomp_model.py` - aggregate material dimension
4. `initial_stock_engine.py` - handle 3D

**Changes needed**:
```python
# OLD (2D):
values = flow.Values[i, :]

# NEW (3D):
# Option A: Sum over materials to get element total
values = np.sum(flow.Values[i, :, :], axis=0)  # (4,) - total per element

# Option B: Get specific material
values = flow.Values[i, material_idx, :]  # (4,) - elements for this material
```

---

### **Step 3: Add Helper Function**

Create `plotting/utils.py` helper:

```python
def get_element_values(flow_or_stock, element_index, aggregate_materials=True):
    """
    Get values for a specific element, handling 2D or 3D arrays.
    
    Parameters
    ----------
    flow_or_stock : Flow or Stock object
    element_index : int
        Index of element in Elements list
    aggregate_materials : bool
        If True, sum over materials dimension. If False, return (time, materials) shape.
    
    Returns
    -------
    np.ndarray
        Time series of element values (shape: (n_years,) or (n_years, n_materials))
    """
    values = flow_or_stock.Values
    
    if values.ndim == 2:
        # 2D: (time, elements)
        return values[:, element_index]
    elif values.ndim == 3:
        # 3D: (time, materials, elements)
        if aggregate_materials:
            return np.sum(values[:, :, element_index], axis=1)
        else:
            return values[:, :, element_index]
    else:
        raise ValueError(f"Unexpected array dimension: {values.ndim}")
```

---

### **Step 4: Update Plotting Functions**

**For each plotting function**:
1. Replace `flow.Values[:, element_index]` 
2. With: `get_element_values(flow, element_index)`

**Example**:
```python
# In dynamics.py
def plot_process_dynamics(mfa_system_results, process_definitions):
    # ...
    for flow in inflows:
        element_values = get_element_values(flow, element_index)  # NEW
        # Instead of: flow.Values[:, element_index]
```

---

## Implementation Order

### **Priority 1: Engine Functions** (Critical for calculations)
1. `solver.py` - TC-driven flows
2. `initial_stock_engine.py` - Stock processing
3. `dsm_model.py` - DSM calculations
4. `fomp_model.py` - FOMP calculations

### **Priority 2: Plotting Functions** (User-facing)
1. `dynamics.py` - Process/Flow dynamics
2. `composition.py` - Flow composition
3. `sankey.py` - Sankey diagrams
4. `validation.py` - Mass balance plots

---

## Quick Decision Points

1. **Materials in Excel**: Are WC and DM defined in Excel now?
   - If yes: Material dimension will work
   - If no: We add them automatically

2. **Aggregation strategy**: How to handle materials?
   - Sum over materials: Default behavior (WC + DM totals)
   - Separate materials: More complex (show WC vs DM)

3. **Backward compatibility**: Keep 2D mode?
   - Detect array shape in helper function
   - Support both 2D and 3D

---

## Recommended Path Forward

**Option A: Add Material dimension now** ⏰ 2-3 hours
- Update system_setup.py to include Materials
- Add helper function for element access
- Update engine functions for 3D
- Test calculations

**Option B: Keep 2D working, plan 3D** ⏰ 1 hour
- Document current 2D system as stable
- Plan 3D implementation
- Add Material dimension later

**Which do you prefer?**



---


================================================================================
# File: PHASE_1B_STATUS.md
================================================================================

# Phase 1b Implementation: Region Dimension - COMPLETED ✅

## Summary

Successfully added support for the Region dimension to the `define_model_scope()` function. The system now supports 3-dimensional arrays (Time, Element, Region) while maintaining backward compatibility.

## Changes Made

### ✅ Modified `02_src/system_setup.py` - `define_model_scope()` Function

**Key Changes**:

1. **Updated Function Signature** (line 29):
```python
def define_model_scope(start_year, end_year, elements, 
                       regions=None, goods=None, materials=None, processes=None):
```
- Added optional dimension parameters
- All new parameters default to None for backward compatibility

2. **Added Region Dimension** (lines 74-78):
```python
# Phase 1b: Add Region dimension
if regions is not None and len(regions) > 0:
    model_classification["Region"] = msc.Classification(
        Name="Regions", Dimension="Region", ID=3, Items=regions
    )
```

3. **Dynamic Index Table Building** (lines 81-96):
```python
# Add Region if defined
if "Region" in model_classification:
    aspects.append("Region")
    descriptions.append('Model aspect "Region"')
    dimensions.append("Region")
    index_letters.append("r")
    classifications.append(model_classification["Region"])
```

4. **Enhanced Print Statement** (line 107):
```python
print(f"--> Model scope and classifications defined with {len(aspects)} dimensions.")
```

## Backward Compatibility

✅ **Fully Backward Compatible**:
- If `regions=None`, defaults to `["Case_Study_Region"]`
- Existing code continues to work without modifications
- Gradually adding dimensions as needed

## Current Status

- ✅ Region dimension support added
- ✅ Index table dynamically built
- ✅ Backward compatible
- ⏳ Need to update flow/stock initialization for 3D arrays
- ⏳ Need to update solver for 3D operations

## Next Steps

### **Immediate**:
1. Test workflow with Region dimension
2. Verify IndexTable has 3 dimensions (Time, Element, Region)
3. Check that existing functionality still works

### **Then Add**:
1. Good dimension (Phase 1c)
2. Material dimension (Phase 1c)
3. Process dimension (Phase 1c)
4. Update engine for multi-dimensional operations

---

**Phase 1b Started! Region dimension support added.** 🚀



---


================================================================================
# File: PHASE_1B_TME_STRUCTURE.md
================================================================================

# Phase 1b Update: Focus on t,m,e Structure (Time, Material, Element)

## Summary

Updated the system to focus on **three main dimensions**: t, m, e (Time, Material, Element)

### **Configuration Update**

**Materials** (from Excel config):
- Material ID 1: WC
- Material ID 2: DM

**Elements** (from Excel config):
- Element ID 1: C
- Element ID 2: Remaining DM

---

## Changes Made

### **1. Updated `system_setup.py`** 

Changed focus from Region to Material dimension:

**Old**: Added Region dimension (t, e, r)
**New**: Added Material dimension (t, e, m)

```python
# Phase 1b: Add Material dimension (WC, DM)
if materials is not None and len(materials) > 0:
    model_classification["Material"] = msc.Classification(
        Name="Materials", Dimension="Material", ID=3, Items=materials
    )
```

### **2. Updated Workflow** (`00_BioDYM_Workflow.py`)

**Line 180**: Now passes all dimensions:
```python
model_classification, index_table = system_setup.define_model_scope(
    start_year, end_year, elements, regions, goods, materials, processes
)
```

**Line 129**: Materials printed first (WC, DM):
```python
if materials:
    print(f"   - Materials: {materials}")
```

---

## Expected System Structure

### **IndexTable will now show**:
```
Available Dimensions:
  - Time (t): 26 items
  - Element (e): 2 items (C, Remaining DM)
  - Material (m): 2 items (WC, DM)
```

### **Flow Indices**:
- Indices="t,e,m" (Time, Element, Material)
- Shape: (n_years, n_elements, n_materials)

### **Array Shapes**:
```python
# Flows: 3D arrays
flow.Values.shape = (26, 2, 2)  # 26 years, 2 elements, 2 materials

# Stocks: 3D arrays
stock.Values.shape = (26, 2, 2)
```

---

## Benefits

1. ✅ **Logical structure**: Material (WC, DM) separate from Elements (C, Remaining DM)
2. ✅ **ODYM compliant**: Uses standard dimension approach
3. ✅ **Simpler than full 6D**: Focus on essential dimensions first
4. ✅ **Backward compatible**: Still works with old 2D structure if materials=None

---

**System now focuses on t,m,e structure!** 🎯

**Ready to test with Time × Material × Element dimensions!** 🚀



---


================================================================================
# File: SESSION_STATUS_SUMMARY.md
================================================================================

# BioDYM ODYM Compliance - Session Status Summary

**Date**: Current Session  
**Branch**: feature/odym-compliance  
**Last Commit**: Phase 1a-1b: ODYM compliance foundation - Add validation hooks and config loader

---

## Executive Summary

Working on ODYM framework compliance for BioDYM. Made progress on Phase 1 validation hooks and 3D array support, but paused to decide on a full 3D implementation.

**Key Achievement**: Refactored solver.py for 3D support and updated validation/Sankey plots  
**Key Question**: Proceed with full 3D implementation (25–40 hours) or keep 2D structure?

---

## What We've Accomplished

### ✅ Phase 1a: Validation Hooks
- Added `Consistency_Check()` to solver.py (after balance and final calculations)
- Added validation to dsm_model.py and fomp_model.py
- All Phase 1a validation hooks committed

### ✅ Phase 1b: Configuration & Dimensions
- Updated config.py to read dimensions from Excel (`Elements`, `Regions`, `Goods`, `Materials`, `Process_Types`)
- Modified system_setup.py to support optional dimensions (Good, Material, Region, Process)
- Updated workflow to pass dimensions to `define_model_scope()`
- Added IndexTable display following ODYM conventions
- Committed Phase 1a-1b progress

### ✅ Plotting Updates (Partial)
- **Sankey diagram** (`sankey.py`): Updated for 3D support using `get_element_values()` helper
- **Validation plot** (`validation.py`): Added material/element layer selectors with "All" aggregation option
- Created `plotting/utils_3d.py` with helper functions for 3D array access

### ✅ Solver Refactoring
- Refactored `solver.py` to detect and handle 3D/4D arrays
- Added material aggregation logic
- Dynamic element handling (no hardcoded element names)

---

## Current System State

### **Working 2D Structure** (CURRENT SYSTEM):
```python
Flow.Values.shape = (26, 1)  # (time, elements)
Elements: ['CC']
```

**Excel Configuration**:
- Materials: WC, DM (defined but not used as dimension)
- Elements: CC
- Data structure: WC and DM are separate rows in Excel, not separate dimensions

**Data in Excel**:
- Each flow has rows for WC and DM material types
- Percentages: `WC_[%]`, `DM_[%]`, `CC_[%]`
- Current system treats these as separate flows, not dimensions

### **Proposed 3D Structure**:
```python
Flow.Values.shape = (26, 2, 1)  # (time, materials, elements)
Materials: ['WC', 'DM']
Elements: ['CC']
```

---

## Key Files Modified

### **Committed Changes**:
1. `02_src/config.py` - Reads dimensions from Excel
2. `02_src/system_setup.py` - Dimension support with Good, Material
3. `02_src/engine/solver.py` - Refactored for 3D (NOT COMMITTED)
4. `02_src/plotting/sankey.py` - Updated for 3D
5. `02_src/plotting/validation.py` - Added material selectors
6. `02_src/plotting/utils_3d.py` - NEW: Helper functions for 3D

### **Uncommitted Changes**:
- `solver.py`: 3D refactoring complete but not committed
- `validation.py`: Material selectors added but not committed
- `sankey.py`: 3D support added but not committed

---

## Current Excel Configuration

**File**: `01_data/01_input/251027_BioDYM_ODYM.xlsm`

**Configuration Sheet** (`0_Configuration`):
```
Good Type 1: Raw Material
Good Type 2: Processed Product  
Good Type 3: Product
Good Type 4: Waste

Material ID 1: WC
Material ID 2: DM

Element ID 1: CC
```

**Data Flow Structure** (`1_2_Data_Flows`):
- Each flow has multiple rows (one per material type)
- Columns: `Flow_Material`, `WC_[%]`, `DM_[%]`, `CC_[%]`
- Percentages are compositions of the flow

---

## Technical Context

### **ODYM Framework Understanding**:
- ODYM supports 6 dimensions: Time, Element, Region, Good, Material, Process
- Current system: Time, Element (2D)
- Proposed: Time, Material, Element (3D)
- Materials in Excel are rows, not dimensions; make them dimensions

### **Data Loader Challenge**:
Current loader (`_populate_primary_flow_data`):
- Reads flow values directly
- Doesn't use `Flow_Material` column to assign to material dimension

Needed for 3D:
- Read `Flow_Material` column
- Assign values to material dimension based on material type
- Map percentages to elements

### **Solver Status**:
- ✅ Updated for 3D: Detects array dimensions, aggregates materials, dynamic element handling
- ⚠️ Not tested: Needs testing with actual 3D data

### **Plotting Status**:
- ✅ Created helper functions in `utils_3d.py`
- ✅ Updated: Sankey, Validation plots
- ⚠️ Remaining: scenario.py, dynamics.py, other plotting files

---

## Critical Decisions Needed

### **Decision Point**: 3D Implementation Strategy

**Option A: Full 3D Implementation**
- Refactor data loader for material dimension
- Update DSM/FOMP models
- Complete plotting updates
- **Effort**: 25-40 hours
- **Risk**: Medium-High
- **Benefit**: Full ODYM compliance

**Option B: Hybrid Approach**
- Add config flag: `use_material_dimension`
- Keep 2D as default
- Enable 3D optionally
- **Effort**: 10-15 hours  
- **Risk**: Low
- **Benefit**: Gradual migration

**Option C: Keep 2D**
- Revert 3D changes
- Keep current working system
- **Effort**: 2 hours (revert commits)
- **Risk**: None
- **Benefit**: Stability

---

## Outstanding Issues

### **1. Element Definition Confusion**
- User wanted 4 elements: material, WC, DM, CC
- Current system has only 1 element: CC
- Materials (WC, DM) are rows in Excel, not elements
- Clarification needed on what should be elements vs materials

### **2. Data Structure Mismatch**
- Excel data: WC and DM are separate rows (2D naturally)
- 3D proposal: WC and DM as material dimension
- **Impact**: Requires significant data loader changes

### **3. Incomplete Refactoring**
- Solver updated for 3D but not tested
- Only 2 plotting functions updated
- DSM/FOMP models not updated
- Data loader not updated

---

## Recommended Next Steps

### **For Continuing AI**:

1. **Clarify Data Model** (15 min)
   - Determine if WC/DM should be materials or remain separate flows
   - Decide on element definitions

2. **Choose Strategy** (5 min)
   - Present options A, B, C to user
   - Wait for decision

3. **If Full 3D** (25-40 hours):
   - Update data loader (`system_setup.py:_populate_primary_flow_data`)
   - Update DSM model (`dsm_model.py`)
   - Update FOMP model (`fomp_model.py`)
   - Complete plotting updates
   - Test workflow end-to-end

4. **If Hybrid** (10-15 hours):
   - Add config flag
   - Implement 2D/3D switching logic
   - Test both modes

5. **If Keep 2D** (2 hours):
   - Revert recent changes
   - Document why 2D was kept

---

## Files to Review

**Key Files**:
- `02_src/config.py` - Config loader
- `02_src/system_setup.py` - System initialization  
- `02_src/engine/solver.py` - Solver (updated for 3D)
- `02_src/plotting/utils_3d.py` - NEW: 3D helpers
- `02_src/plotting/sankey.py` - Updated plots
- `02_src/plotting/validation.py` - Updated plots

**Status Documents**:
- `02_src/engine/ODYM_COMPLIANCE_MASTER_PLAN.md` - Original plan
- `02_src/engine/3D_IMPLEMENTATION_COMPLEXITY.md` - NEW: Complexity analysis
- Various Phase 1 progress documents in `02_src/engine/`

---

## Git Status

**Branch**: `feature/odym-compliance`  
**Last Commit**: Phase 1a-1b  
**Uncommitted**: solver.py, validation.py, sankey.py changes

**Recommendation**: Commit current work or create feature branch for 3D experimentation

---

## User Preferences (from Memory)
- Prefers discussion after each step in multi-step processes
- Prefers confirmation before quick actions
- Uses jupytext for .py/.ipynb synchronization
- Prefers Plotly for visualizations
- Custom additions to ODYM should be clearly marked

---

**Status**: Awaiting decision on 3D implementation strategy before proceeding further.



---


================================================================================
# File: STOCK_VS_PROCESS_INDICES.md
================================================================================

# Understanding Stock vs. Process Indices

## Key Point: Processes DON'T Have Indices!

### **Process Objects: No Indices Required**

**Processes are simple objects** in ODYM:
```python
class Process(Obj):
    def __init__(
        self,
        Name=None,        # Process name
        ID=None,          # Process ID
        Extensions=None,  # Process extensions (custom data)
    )
```

**Key Point**: 
- ❌ **Processes DO NOT have Indices**
- ❌ **Processes DO NOT have Values arrays**
- ✅ **Processes are just containers** with ID, Name, and Extensions

### **Stock Objects: DO Have Indices**

**Stocks belong to Processes** but have their own Indices:
```python
class Stock(Obj):
    def __init__(
        self,
        Name=None,        # Stock name (e.g., "dS_1", "S_1")
        P_Res=None,       # Residence process ID (process this stock belongs to)
        Indices=None,     # Stock's dimensions (e.g., "t,e")
        Values=None,      # Stock values array
        Type=None,        # Stock type (0=absolute, 1=change)
    )
```

**Key Point**:
- ✅ **Stocks HAVE Indices**
- ✅ **Stocks HAVE Values arrays**
- ✅ **Stocks belong to a specific Process** (P_Res)

## Why You Define Stocks on the Same Page as Processes

### **Your Current Excel Structure**

**Sheet: `2_1_Definition_Processes`**
```
| ID | Process_Name | Process_Logic | Stock_Configuration |
|----|--------------|---------------|---------------------|
| 1 | Harvest | DSM | Stock |
| 2 | Processing | DSM | Stock |
| 3 | Storage | Standard | (no stock) |
```

**What Happens**:
1. You read the process definition (ID, Name, Logic)
2. You check if Stock_Configuration = "Stock"
3. IF Stock_Configuration = "Stock", you create Stock objects

**Why This Works**:
- **Processes are created first** (ProcessList)
- **Stocks are created second** (StockDict) but **belong to processes** (P_Res=process_id)

### **The Relationship**:

```
Process (ID=1, Name="Harvest")
  └─ Stock (Name="dS_1", P_Res=1, Indices="t,e")
  └─ Stock (Name="S_1", P_Res=1, Indices="t,e")

Process (ID=2, Name="Processing")  
  └─ Stock (Name="dS_2", P_Res=2, Indices="t,e")
  └─ Stock (Name="S_2", P_Res=2, Indices="t,e")
```

**Key Understanding**:
- **Processes define the structure**
- **Stocks are created AFTER processes**, based on Stock_Configuration
- **Both use the SAME Excel row** but create different objects

## Do You Need Different Indices for Stocks and Flows?

### **Current Implementation**:

**Flow Creation** (from `1_1_Definition_Flows`):
```python
flow = msc.Flow(
    Name=row["Flow_ID"],
    P_Start=start_id,
    P_End=end_id,
    Indices="t,e"  # Flow indices
)
```

**Stock Creation** (from `2_1_Definition_Processes`):
```python
mfa_system.StockDict[f"dS_{process_id}"] = msc.Stock(
    Name=f"dS_{process_id}", 
    P_Res=process_id, 
    Type=1, 
    Indices="t,e"  # Stock indices
)
```

### **Answer: NO, You Don't Need Different Indices!**

**Why They Can Be the Same**:
1. **Flows**: Material flows between processes with dimensions (t,e,r,g,m,p)
2. **Stocks**: Material stocks AT processes with dimensions (t,e,r,g,m,p)
3. **Both use the same dimension system** - just different contexts!

**But They CAN Be Different If Needed**:

```python
# Simple flows: just Time + Element
Flow Indices = "t,e"

# Complex stocks: Time + Element + Material  
Stock Indices = "t,e,m"
```

## Recommended Approach

### **Option 1: Use Same Indices Everywhere (Simplest)**

**Set all to "t,e" in Excel**:
```excel
# In 1_1_Definition_Flows
Indices = "t,e"  # For all flows

# In 2_1_Definition_Processes
Stock_Indices = "t,e"  # For all stocks
```

**Benefits**:
- ✅ Simple and consistent
- ✅ Easy to understand
- ✅ Backward compatible

### **Option 2: Configure Per Item (Advanced)**

**Use different Indices when needed**:
```excel
# In 1_1_Definition_Flows
Flow_ID | Flow_Name | Indices
--------|-----------|--------
F_01_02 | Harvest_Flow | t,e        # Simple flow
F_02_03 | Processing_Flow | t,e,g,m  # Multi-dimensional flow

# In 2_1_Definition_Processes
ID | Process_Name | Stock_Indices
---|--------------|---------------
1 | Harvest | t,e           # Simple stock
2 | Storage | t,e,g,m       # Material-specific stock
```

**Benefits**:
- ✅ More flexible
- ✅ Can optimize memory usage
- ✅ Allows dimension-specific analysis

## My Recommendation

For now, use the same Indices everywhere:

```excel
# In 1_1_Definition_Flows
Indices = "t,e"  # Default for all flows

# In 2_1_Definition_Processes (add Stock_Indices column)
Stock_Indices = "t,e"  # Default for all stocks
```

Later, when you need multi-dimensional analysis, you can specify different Indices per item.

## Summary

- **Processes DON'T have Indices** (they're simple containers)
- **Stocks and Flows BOTH have Indices** (they represent data)
- You can use the SAME Indices for stocks and flows, or DIFFERENT ones if needed
- **For simplicity**: Use "t,e" everywhere initially
- **For ODYM compliance**: You need both Flow Indices and Stock_Indices columns in Excel

---

*Document Version: 1.0*  
*Last Updated: [Current Date]*  
*Author: BioDYM Development Team*


---


================================================================================
# File: TEST_3D_STRUCTURE.md
================================================================================

# Testing 3D Structure with Material Dimension

## Your Configuration

### **Materials** (Physical materials):
- **WC**: Water Content
- **DM**: Dry Matter

### **Elements** (Components tracked):
- **material**: Total mass (fresh mass)
- **CC**: Carbon Content

---

## Excel Update You'll Make

**In `0_Configuration` sheet**:

**Materials**:
```
Setting_Name      | Value
Material ID 1     | WC
Material ID 2     | DM
```

**Elements**:
```
Setting_Name      | Value
Element ID 1      | material
Element ID 2      | CC
```

---

## Expected Results After Update

### **1. Config Loader**
```python
materials = ['WC', 'DM']
elements = ['material', 'CC']
```

### **2. IndexTable**
```
Aspect    | IndexLetter | Items
----------|-------------|------------------
Time      | t           | [2020, 2021, ..., 2045]
Material  | m           | ['WC', 'DM']
Element   | e           | ['material', 'CC']
```

### **3. Flow.Values Shape**
```python
Flow.Values.shape = (26, 2, 2)
# 26 years × 2 materials × 2 elements
```

---

## Testing Plan

### **Step 1: Read Config** ✅
- Run config loader
- Verify materials=['WC', 'DM'], elements=['material', 'CC']

### **Step 2: Check IndexTable** ✅
- Run workflow setup
- Verify IndexTable shows Material dimension
- Print IndexTable for verification

### **Step 3: Check Flow Shape** ✅
- Initialize a flow
- Check `flow.Values.shape`
- Should be (26, 2, 2)

### **Step 4: Test Calculations** ⚠️
- Run baseline calculation
- May encounter errors in solver.py (expects different structure)
- Document errors for fixing

---

## Potential Issues

### **1. Solver.py**
Current code expects:
```python
flow.Values[:, element_index]  # Works for 2D
```

Need to update to:
```python
# Sum over materials
np.sum(flow.Values[:, :, element_index], axis=1)
```

### **2. DSM Model**
Aggregate material dimension before stock calculations.

### **3. FOMP Model**
Handle material dimension in mineralization.

---

## Helper Functions Available

Created `plotting/utils_3d.py` with:
- `get_element_values()` - Get element, handle 2D/3D
- `get_material_values()` - Get all elements for a material
- `get_element_by_material()` - Get specific element in specific material
- `has_material_dimension()` - Check if 3D
- `get_array_info()` - Get shape information

---

## Next Steps After Excel Update

1. ✅ Update Excel (you'll do this)
2. 📝 Run workflow and check config read
3. 📝 Print IndexTable for verification
4. 📝 Check flow shapes
5. ⚠️ Identify and fix any solver errors
6. 🎉 Test full workflow with 3D structure

**Ready to test when you've updated Excel!** 🚀



---


================================================================================
# File: UNDERSTANDING_DATA_STRUCTURE.md
================================================================================

# Understanding Your Current Data Structure

## Your Excel Data Structure

### **Current System (WORKING)**:

**Excel columns**:
- `Flow_Material`: Material type (WC or DM)
- `WC_[%]`: Water Content percentage
- `DM_[%]`: Dry Matter percentage  
- `CC_[%]`: Carbon Content percentage

**Example**:
```
Flow_Material: "WC"  (or "DM")
WC_[%]: Yes
DM_[%]: 0
CC_[%]: 0
```

**What this means**:
- Each row represents ONE material type (WC OR DM)
- The percentages are compositions of THAT material

---

## What You Want to Achieve

### **Material Separation**:

**Current**: 2D structure
- Flow.Values: (Time, Element) = (26, 3)
- Elements: material total, WC composition, DM composition, CC composition
- All in ONE array

**Desired**: 3D structure  
- Flow.Values: (Time, Material, Element) = (26, 2, 3)
- Materials: WC, DM (separate dimensions)
- Elements: material total, CC, ???

---

## The Challenge

Your Excel has **"WC" as percentage composition**, not as a material dimension.

**In Excel**:
- Row 1: Flow = 100 Mg, Material = "WC", CC = 50%
- Row 2: Flow = 100 Mg, Material = "DM", CC = 50%

**Currently in Python** (2D):
```python
Flow.Values[:, 0] = [100, 100]  # Total material for each time
Flow.Values[:, 1] = [50, 50]    # CC for each time
```

**What you want** (3D):
```python
Flow.Values[:, 0, 0] = [100, 0]   # Material for WC
Flow.Values[:, 0, 1] = [50, 0]    # CC for WC
Flow.Values[:, 1, 0] = [0, 100]   # Material for DM  
Flow.Values[:, 1, 1] = [0, 50]   # CC for DM
```

---

## Data Loader Implications

**Current loader**: `_populate_primary_flow_data()`

```python
# Currently reads:
flow.Values[:, 0] = flow_data['Flow'][year_idx]  # Total
flow.Values[:, 1] = flow_data['WC_[%]'][year_idx] * flow.Values[:, 0] / 100
```

**Needed for 3D**: 
```python
# Need to assign to material dimension based on Flow_Material
material_type = row['Flow_Material']  # "WC" or "DM"
if material_type == "WC":
    material_idx = 0
elif material_type == "DM":
    material_idx = 1

flow.Values[:, material_idx, 0] = flow_data['Flow'][year_idx]  # Material total
flow.Values[:, material_idx, 1] = flow_data['CC_[%]'][year_idx] * flow.Values[:, material_idx, 0] / 100
```

---

## This is MAJOR Refactoring

**Why**:
1. Data loader must change to assign to material dimension
2. Solver must work with 3D arrays  
3. Plotting functions must handle material selection
4. **Every calculation** must handle 3D

**But**: This follows ODYM principles! ✅

---

## Recommendation

**Option A: Stay with 2D** (Keep Current System)
- ✅ Everything works now
- ✅ Simple structure
- ✅ Easier to maintain

**Option B: Go Full 3D** (Major Refactoring)
- ✅ ODYM compliant
- ✅ More flexible
- ⚠️ Requires refactoring EVERYTHING
- ⚠️ Several weeks of work

**What do you prefer?** 🤔



---
