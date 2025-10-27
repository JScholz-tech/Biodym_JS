# Phase 1a: ODYM Compliance Analysis for 2D System

**Date**: 2025-10-27  
**Focus**: Complete ODYM compliance while maintaining 2D (Time, Element) structure

---

## Executive Summary

This document analyzes BioDYM's current ODYM compliance status and outlines specific improvements for Phase 1a that maintain the 2D data structure while enhancing compliance with ODYM best practices.

**Key Finding**: BioDYM already uses most ODYM classes correctly but has some manual initialization that should be replaced with ODYM methods.

---

## Current ODYM Compliance Status

### ✅ What's Already Compliant

1. **Class Usage**:
   - ✅ `MFAsystem` class initialized with proper parameters
   - ✅ `Flow` objects created with `Indices="t,e"`
   - ✅ `Stock` objects created with proper structure
   - ✅ `Parameter` objects for composition (WC, DM, CC)
   - ✅ `Classification` objects for Time, Element dimensions

2. **Validation**:
   - ✅ `Consistency_Check()` called in solver.py, dsm_model.py, fomp_model.py
   - ✅ `Initialize_StockValues()` called in system_setup.py (line 234)

3. **Structure**:
   - ✅ `IndexTable` properly constructed
   - ✅ `ModelClassification` dictionary created
   - ✅ FlowDict, StockDict, ParameterDict properly structured

---

## ⚠️ Areas for Improvement

### 1. **Manual vs. ODYM Initialization**

**Current State**: Mixed approach - some manual `np.zeros()`, some ODYM methods.

**Locations**:

```python
# ✅ USING ODYM METHOD (system_setup.py:234)
mfa_system.Initialize_StockValues()

# ⚠️ MANUAL INITIALIZATION (system_setup.py:231)
stock_obj.Values = np.zeros((len(mfa_system.IndexTable.Classification['Time'].Items), len(mfa_system.Elements)))

# ⚠️ MANUAL INITIALIZATION (initial_stock_engine.py:395)
flow.Values = np.zeros((n_years, n_elements))
```

**Fix Required**: Replace manual initialization with:
- `mfa_system.Initialize_FlowValues()` for flows
- `mfa_system.Initialize_StockValues()` for stocks  
- `mfa_system.Initialize_ParameterValues()` for parameters

---

### 2. **Custom Attributes**

**Current State**: Some custom attributes added to ODYM objects.

**Locations**:
- `flow_obj.DescriptiveName` (system_setup.py:322, 345)
- `flow._initial_stock_config` (initial_stock_engine.py:398-403)

**ODYM Compliance**: ODYM discourages adding custom attributes. Use standard ODYM fields or external dictionaries.

**Fix Required**: 
- Store descriptive names in external dict: `flow_descriptions = {}`
- Store initial stock config in external dict: `initial_stock_configs = {}`

---

### 3. **Parameter Creation**

**Current State**: Composition parameters (WC, DM, CC) created manually.

**Location**: `system_setup.py:370-420`

**Issue**: Manual Parameter creation instead of using ODYM's built-in structure.

**Fix Required**: Ensure Parameters have proper `Indices` and use `Initialize_ParameterValues()`.

---

## Recommended Actions for Phase 1a

### Priority 1: Replace Manual Initialization (⏱️ 1-2 hours)

**Files to Modify**:
1. `02_src/system_setup.py`
2. `02_src/engine/initial_stock_engine.py`

**Changes**:
- Remove `np.zeros()` in favor of `mfa_system.Initialize_FlowValues()`
- Remove manual `stock_obj.Values = np.zeros(...)` assignments
- Ensure all Flows/Stocks have `Values=None` initially, then call ODYM init methods

---

### Priority 2: Remove Custom Attributes (⏱️ 1-2 hours)

**Files to Modify**:
1. `02_src/system_setup.py`
2. `02_src/engine/initial_stock_engine.py`
3. `02_src/engine/solver.py`

**Changes**:
- Replace `flow_obj.DescriptiveName` with external dict: `flow_descriptions[flow_id]`
- Replace `flow._initial_stock_config` with external dict: `initial_stock_configs[flow_name]`
- Update solver.py to read from external dicts

---

### Priority 3: Enhanced Error Handling (⏱️ 1-2 hours)

**Add `try...except` blocks around**:
- `mfa_system.Initialize_FlowValues()`
- `mfa_system.Initialize_StockValues()`
- `mfa_system.Consistency_Check()`

**Provide clear error messages** for:
- Missing required columns in Excel
- Dimensional mismatches
- Invalid Indices strings

---

### Priority 4: Parameter Creation Compliance (⏱️ 2-3 hours)

**Review and standardize**:
- Ensure all Parameters have proper `Indices` attribute
- Call `mfa_system.Initialize_ParameterValues()` after creating parameters
- Validate parameter shapes match their `Indices`

---

## Comparison with Official ODYM Classes

### Official ODYM MFAsystem Methods (from ODYM_Classes.py)

```python
class MFAsystem(Obj):
    def Initialize_FlowValues(self):
        """Construct empty numpy arrays for flows with None values."""
    
    def Initialize_StockValues(self):
        """Construct empty numpy arrays for stocks with None values."""
    
    def Initialize_ParameterValues(self):
        """Construct empty numpy arrays for parameters with None values."""
    
    def Consistency_Check(self):
        """Check system for dimension consistency."""
    
    def IndexTableCheck(self):
        """Check IndexTable for dimension consistency."""
```

### BioDYM Current Usage

| Method | Called? | Location | Status |
|--------|---------|----------|--------|
| `Initialize_FlowValues()` | ❌ No | Should be in system_setup.py | **Missing** |
| `Initialize_StockValues()` | ✅ Yes | system_setup.py:234 | **Used** |
| `Initialize_ParameterValues()` | ❌ No | Should be in system_setup.py | **Missing** |
| `Consistency_Check()` | ✅ Yes | solver.py, dsm_model.py, fomp_model.py | **Used** |
| `IndexTableCheck()` | ❌ No | Should be called in initialize_mfa_system | **Missing** |

---

## Implementation Plan

### Step 1: Fix Manual Flow Initialization

**Current**:
```python
# initial_stock_engine.py:395
flow.Values = np.zeros((n_years, n_elements))
```

**Change to**:
```python
flow.Values = None  # Let ODYM initialize
# Then call:
mfa_system.Initialize_FlowValues()
```

---

### Step 2: Fix Manual Stock Initialization

**Current**:
```python
# system_setup.py:231
stock_obj.Values = np.zeros((len(time), len(elements)))
```

**Change to**:
```python
stock_obj.Values = None  # Let ODYM initialize
# Already calling Initialize_StockValues() at line 234
```

---

### Step 3: Add Missing Initialization Calls

**Add to `system_setup.py` after all Flows/Stocks created**:

```python
def initialize_mfa_system(model_classification, index_table):
    # ... existing code ...
    
    # ✅ Initialize all empty values
    mfa_system.Initialize_FlowValues()
    mfa_system.Initialize_StockValues()
    mfa_system.Initialize_ParameterValues()
    
    # ✅ Check consistency
    mfa_system.IndexTableCheck()
    
    return mfa_system
```

---

### Step 4: Remove Custom Attributes

**Replace**:
```python
flow_obj.DescriptiveName = row["Flow_Name"]
```

**With**:
```python
# Create external dict at module level
flow_descriptions = {}
flow_descriptions[flow_id] = row["Flow_Name"]
```

**Update plotting functions** to read from `flow_descriptions` dict instead of `flow.DescriptiveName`.

---

## Expected Benefits

1. **Cleaner Code**: Less manual array creation, more ODYM-native code
2. **Better Error Messages**: ODYM provides detailed dimension mismatch errors
3. **Future-Proof**: Ready for multi-dimensional expansion
4. **Standards Compliance**: Follows ODYM best practices exactly

---

## Testing Strategy

After implementation:

1. ✅ Run existing workflow - should work identically
2. ✅ Verify `Consistency_Check()` passes
3. ✅ Verify `IndexTableCheck()` passes
4. ✅ Check all plotting functions still work
5. ✅ Verify DSM and FOMP calculations unchanged

---

## Next Steps

1. **Review** this analysis with user
2. **Implement** Priority 1 fixes (manual initialization)
3. **Implement** Priority 2 fixes (custom attributes)
4. **Test** thoroughly
5. **Consider** Priority 3/4 if time permits

---

## References

- ODYM GitHub: https://github.com/IndEcol/ODYM/tree/master/src/odym/classes
- ODYM_Classes.py: `06_framework/ODYM-master_20241127/odym/modules/ODYM_Classes.py`
- BioDYM System: Current implementation in `02_src/`


