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

### **Phase 1: Foundation & Dimensions (3-4 weeks)**

#### **Week 1: Dimension System Implementation**
- [ ] **Day 1-2**: Add Region dimension to system_setup.py
  - [ ] Create Region classification
  - [ ] Update IndexTable structure
  - [ ] Test Region dimension integration
- [ ] **Day 3-4**: Add Good dimension to system_setup.py
  - [ ] Create Good classification
  - [ ] Update IndexTable structure
  - [ ] Test Good dimension integration
- [ ] **Day 5**: Add Material dimension to system_setup.py
  - [ ] Create Material classification
  - [ ] Update IndexTable structure
  - [ ] Test Material dimension integration

#### **Week 2: Process Dimension & Data Structures**
- [ ] **Day 1-2**: Add Process dimension to system_setup.py
  - [ ] Create Process classification
  - [ ] Update IndexTable structure
  - [ ] Test Process dimension integration
- [ ] **Day 3-4**: Update Flow Indices
  - [ ] Implement create_flow_with_full_indices()
  - [ ] Update all flow creation calls
  - [ ] Test multi-dimensional flow indices
- [ ] **Day 5**: Update Data Array Shapes
  - [ ] Implement initialize_flow_values()
  - [ ] Update all flow initialization calls
  - [ ] Test multi-dimensional arrays

#### **Week 3: Engine Module Updates**
- [ ] **Day 1-2**: Update solver.py for multi-dimensional support
  - [ ] Update flow aggregation functions
  - [ ] Test multi-dimensional calculations
- [ ] **Day 3-4**: Update initial_stock_engine.py for multi-dimensional support
  - [ ] Update flow creation functions
  - [ ] Test multi-dimensional initial stocks
- [ ] **Day 5**: Update dsm_model.py and fomp_model.py
  - [ ] Update calculation functions
  - [ ] Test multi-dimensional calculations

#### **Week 4: Basic ODYM Validation**
- [ ] **Day 1-2**: Add Consistency Checks
  - [ ] Implement add_odym_validation()
  - [ ] Add validation calls to all engine modules
  - [ ] Test validation functionality
- [ ] **Day 3-4**: Add Error Handling
  - [ ] Implement safe_odym_operation()
  - [ ] Wrap all ODYM operations
  - [ ] Test error handling
- [ ] **Day 5**: Testing and Validation
  - [ ] Run all existing tests
  - [ ] Fix any issues
  - [ ] Validate Phase 1 success criteria

### **Phase 2: Class Compliance (3-4 weeks)**

#### **Week 5: ODYM Method Integration**
- [ ] **Day 1-2**: Replace Manual Flow Aggregation
  - [ ] Implement calculate_process_inflows_odym_compliant()
  - [ ] Update calculate_final_balances()
  - [ ] Test ODYM flow aggregation
- [ ] **Day 3-4**: Implement ODYM Flow Management
  - [ ] Implement create_flow_odym_compliant()
  - [ ] Update flow creation calls
  - [ ] Test ODYM flow management
- [ ] **Day 5**: Use ODYM Initialization Methods
  - [ ] Implement initialize_mfa_system_odym_compliant()
  - [ ] Update system initialization
  - [ ] Test ODYM initialization

#### **Week 6: Remove Custom Attributes**
- [ ] **Day 1-2**: Replace Custom Attributes with ODYM Extensions
  - [ ] Implement store_initial_stock_config_odym_compliant()
  - [ ] Update initial stock handling
  - [ ] Test ODYM Extensions
- [ ] **Day 3-4**: Update FOMP Process Handling
  - [ ] Implement _calculate_fomp_flows_odym_compliant()
  - [ ] Update FOMP flow calculations
  - [ ] Test FOMP ODYM compliance
- [ ] **Day 5**: Update All Custom Attributes
  - [ ] Find and replace all custom attributes
  - [ ] Test all replacements
  - [ ] Validate no custom attributes remain

#### **Week 7: Mass Balance Improvements**
- [ ] **Day 1-2**: Use ODYM Mass Balance Methods
  - [ ] Implement calculate_mass_balance_odym_compliant()
  - [ ] Update mass balance calculations
  - [ ] Test ODYM mass balance
- [ ] **Day 3-4**: Add Comprehensive Validation
  - [ ] Create validation.py module
  - [ ] Implement validate_mfa_system_state()
  - [ ] Add validation calls throughout
- [ ] **Day 5**: Testing and Validation
  - [ ] Run all existing tests
  - [ ] Fix any issues
  - [ ] Validate Phase 2 success criteria

#### **Week 8: Integration Testing**
- [ ] **Day 1-2**: Test Class Compliance Integration
  - [ ] Test all ODYM methods
  - [ ] Test ODYM Extensions
  - [ ] Test mass balance improvements
- [ ] **Day 3-4**: Performance Testing
  - [ ] Benchmark performance improvements
  - [ ] Test memory usage
  - [ ] Optimize if needed
- [ ] **Day 5**: Documentation Updates
  - [ ] Update documentation for class compliance
  - [ ] Create migration guide
  - [ ] Prepare for Phase 3

### **Phase 3: Function Compliance (3-4 weeks)**

#### **Week 9: Type Safety Implementation**
- [ ] **Day 1-2**: Add Type Hints to solver.py
  - [ ] Add type hints to all functions
  - [ ] Test type hint functionality
- [ ] **Day 3-4**: Add Type Hints to Other Modules
  - [ ] Add type hints to initial_stock_engine.py
  - [ ] Add type hints to dsm_model.py
  - [ ] Add type hints to fomp_model.py
- [ ] **Day 5**: Add Input Validation
  - [ ] Implement input validation for all functions
  - [ ] Test input validation
  - [ ] Fix any validation issues

#### **Week 10: Error Handling Implementation**
- [ ] **Day 1-2**: Add Comprehensive Error Handling
  - [ ] Implement error handling for solver.py
  - [ ] Test error handling functionality
- [ ] **Day 3-4**: Add Error Handling to Other Modules
  - [ ] Implement error handling for all modules
  - [ ] Test error handling throughout
- [ ] **Day 5**: Add Logging Integration
  - [ ] Create logging_setup.py
  - [ ] Implement ODYM-style logging
  - [ ] Test logging functionality

#### **Week 11: ODYM Function Patterns**
- [ ] **Day 1-2**: Implement ODYM Naming Conventions
  - [ ] Adopt ODYM naming patterns
  - [ ] Update function names
  - [ ] Test naming conventions
- [ ] **Day 3-4**: Implement Pure Functions
  - [ ] Create pure functions where possible
  - [ ] Test pure function functionality
- [ ] **Day 5**: Function Pattern Testing
  - [ ] Test all ODYM function patterns
  - [ ] Validate function compliance
  - [ ] Prepare for Phase 4

#### **Week 12: Function Compliance Testing**
- [ ] **Day 1-2**: Test Function Compliance Integration
  - [ ] Test all type hints
  - [ ] Test all error handling
  - [ ] Test all ODYM patterns
- [ ] **Day 3-4**: Performance Testing
  - [ ] Benchmark function performance
  - [ ] Test error handling performance
  - [ ] Optimize if needed
- [ ] **Day 5**: Documentation Updates
  - [ ] Update documentation for function compliance
  - [ ] Create function migration guide
  - [ ] Prepare for Phase 4

### **Phase 4: Advanced Integration & Optimization (3-4 weeks)**

#### **Week 13: BioDYM Extensions Implementation**
- [ ] **Day 1-2**: Create BioDYM Extension Classes
  - [ ] Implement FOMPProcess class
  - [ ] Implement InitialStockManager class
  - [ ] Test extension classes
- [ ] **Day 3-4**: Integrate Extensions with MFA System
  - [ ] Implement initialize_biodym_extensions()
  - [ ] Update system initialization
  - [ ] Test extension integration
- [ ] **Day 5**: Update Engine Modules to Use Extensions
  - [ ] Update initial_stock_engine.py
  - [ ] Update fomp_model.py
  - [ ] Test extension usage

#### **Week 14: Performance Optimization**
- [ ] **Day 1-2**: Optimize Multi-Dimensional Operations
  - [ ] Implement calculate_flows_vectorized()
  - [ ] Test vectorized operations
- [ ] **Day 3-4**: Add Performance Monitoring
  - [ ] Create performance_monitor.py
  - [ ] Add performance decorators
  - [ ] Test performance monitoring
- [ ] **Day 5**: Performance Testing
  - [ ] Benchmark performance improvements
  - [ ] Test memory usage
  - [ ] Optimize if needed

#### **Week 15: Excel Template Updates**
- [ ] **Day 1-2**: Create New Excel Sheets
  - [ ] Create Region definition sheets
  - [ ] Create Good definition sheets
  - [ ] Create Material definition sheets
- [ ] **Day 3-4**: Create Process Definition Sheets
  - [ ] Create Process definition sheets
  - [ ] Update existing sheets
  - [ ] Test Excel template structure
- [ ] **Day 5**: Update Data Loader
  - [ ] Implement load_multi_dimensional_data()
  - [ ] Test data loading
  - [ ] Fix any loading issues

#### **Week 16: Comprehensive Testing & Finalization**
- [ ] **Day 1-2**: Create Test Suite
  - [ ] Create test_odym_compliance.py
  - [ ] Create test_integration.py
  - [ ] Test all compliance areas
- [ ] **Day 3-4**: Integration Testing
  - [ ] Test complete workflow
  - [ ] Test backward compatibility
  - [ ] Fix any integration issues
- [ ] **Day 5**: Final Validation
  - [ ] Validate all success criteria
  - [ ] Create final documentation
  - [ ] Prepare for deployment

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