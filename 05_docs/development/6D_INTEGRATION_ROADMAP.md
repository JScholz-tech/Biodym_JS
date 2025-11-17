# BioDYM 6D Structure Integration Roadmap

**Created**: 2025-11-06
**Current Status**: BioDYM uses 2D (Time × Element)
**Target**: 6D (Time × Region × Good × Material × Element × Process)
**Estimated Effort**: Major architectural change - 3-6 months

---

## Executive Summary

Expanding BioDYM from 2D to 6D structure is a **major architectural upgrade** that will enable:
- Multi-regional MFA studies
- Multiple product categories (goods)
- Multiple material types simultaneously
- Process-type classification
- Full compatibility with complex ODYM studies

**Recommendation**: Implement incrementally (3D → 4D → 5D → 6D) rather than all at once.

---

## Current State Analysis

### Current Dimensions (2D)
```python
Indices = "t,e"  # Time × Element
Shape = (26, 4)  # 26 years × 4 elements
Total values per flow = 104
```

### Target Dimensions (6D)
```python
Indices = "t,r,g,m,e,p"  # Time × Region × Good × Material × Element × Process
Example shape = (26, 3, 4, 5, 4, 8)
Total values per flow = 124,800 (!)
```

### Impact Analysis

**Files requiring major changes**: 15+
**Code locations affected**: 50+
**Excel structure changes**: All data input sheets
**Backward compatibility**: Critical consideration

---

## Phase-by-Phase Implementation Plan

### Phase 1: Add Region Aspect (2D → 3D)
**Duration**: 4-6 weeks
**Priority**: High (enables multi-regional studies)

### Phase 2: Add Good Aspect (3D → 4D)
**Duration**: 4-6 weeks
**Priority**: Medium (enables product-level tracking)

### Phase 3: Add Material Aspect (4D → 5D)
**Duration**: 4-6 weeks
**Priority**: Medium (enables multi-feedstock studies)

### Phase 4: Add Process Aspect (5D → 6D)
**Duration**: 3-4 weeks
**Priority**: Low (mainly for classification/reporting)

**Total Estimated Time**: 4-6 months of focused development

---

## Detailed Step-by-Step Guide

## PHASE 1: Add Region Aspect (t,e → t,r,e)

### Step 1.1: Update Model Scope Definition

**File**: `02_src/system_setup.py`
**Function**: `define_model_scope()`

```python
# CURRENT (line 66-81)
aspects = ["Time", "Element"]
index_letters = ["t", "e"]

# NEW
def define_model_scope(start_year, end_year, elements, regions):
    """Add regions as required parameter, not optional."""

    aspects = ["Time", "Region", "Element"]
    index_letters = ["t", "r", "e"]

    # Add Region classification
    model_classification["Region"] = msc.Classification(
        Name="Regions",
        Dimension="Region",
        ID=3,
        Items=regions  # e.g., ["Germany", "France", "Poland"]
    )
```

**Changes required**:
- ✅ Add Region to aspects list
- ✅ Add Region Classification
- ✅ Update IndexTable construction
- ✅ Validate region names

### Step 1.2: Update Flow Definitions

**File**: `02_src/system_setup.py`
**Function**: `load_flows_and_stocks()`

```python
# CURRENT (line 343)
flow_obj = msc.Flow(Name=row["Flow_ID"], P_Start=start_id, P_End=end_id, Indices="t,e")

# NEW
flow_obj = msc.Flow(Name=row["Flow_ID"], P_Start=start_id, P_End=end_id, Indices="t,r,e")
# Shape changes from (26, 4) to (26, 3, 4) for 3 regions
```

**Impact**: ALL flows now need region-specific data

### Step 1.3: Update Stock Definitions

**File**: `02_src/system_setup.py`
**Function**: `load_processes()`

```python
# CURRENT (line 219, 222)
msc.Stock(Name=f"dS_{process_id}", P_Res=process_id, Type=1, Indices="t,e")
msc.Stock(Name=f"S_{process_id}", P_Res=process_id, Type=0, Indices="t,e")

# NEW
msc.Stock(Name=f"dS_{process_id}", P_Res=process_id, Type=1, Indices="t,r,e")
msc.Stock(Name=f"S_{process_id}", P_Res=process_id, Type=0, Indices="t,r,e")
```

### Step 1.4: Update Excel Data Loading

**File**: `02_src/data_loader.py`
**Function**: `load_flow_data()`

**CURRENT Excel structure**:
```
Flow_ID | Year | material | WC | DM | CC
F_01_02 | 2025 | 100     | 80 | 20 | 9
F_01_02 | 2026 | 105     | 82 | 23 | 10.35
```

**NEW Excel structure**:
```
Flow_ID | Region   | Year | material | WC | DM | CC
F_01_02 | Germany  | 2025 | 100     | 80 | 20 | 9
F_01_02 | France   | 2025 | 80      | 64 | 16 | 7.2
F_01_02 | Poland   | 2025 | 60      | 48 | 12 | 5.4
F_01_02 | Germany  | 2026 | 105     | 82 | 23 | 10.35
...
```

**Code changes**:
```python
# CURRENT
def load_flow_data(file_path, sheet_name, elements, years):
    # Pivot to create (time × element) arrays
    array_2d = df.pivot_table(values=elements, index='Year', aggfunc='first')
    return array_2d.values  # Shape (26, 4)

# NEW
def load_flow_data(file_path, sheet_name, elements, regions, years):
    # Pivot to create (time × region × element) arrays
    array_3d = np.zeros((len(years), len(regions), len(elements)))

    for r_idx, region in enumerate(regions):
        region_data = df[df['Region'] == region]
        for t_idx, year in enumerate(years):
            year_data = region_data[region_data['Year'] == year]
            if not year_data.empty:
                array_3d[t_idx, r_idx, :] = year_data[elements].values[0]

    return array_3d  # Shape (26, 3, 4)
```

### Step 1.5: Update Solver Array Indexing

**File**: `02_src/engine/solver.py`
**Critical Changes**: ALL array indexing must change

```python
# CURRENT - 2D indexing [time, element]
initial_stock_vector = stock_s.Values[0, :].copy()  # Shape (4,)
flow_values = flow.Values[t, :]  # Shape (4,) at time t

# NEW - 3D indexing [time, region, element]
initial_stock_vector = stock_s.Values[0, :, :].copy()  # Shape (3, 4)
flow_values = flow.Values[t, :, :]  # Shape (3, 4) at time t

# OR if operating on single region:
for r in range(num_regions):
    flow_values = flow.Values[t, r, :]  # Shape (4,) at time t, region r
```

**Estimated changes**: 50+ locations in solver.py need updating

### Step 1.6: Update Transfer Coefficients

**File**: `02_src/system_setup.py`
**Function**: `load_transfer_coefficients()`

**Current**: TCs are (time × element) → shape (26, 4)
**New**: TCs are (time × region × element) → shape (26, 3, 4)

**Decision point**: Do TCs vary by region?
- **Option A**: Same TC for all regions → broadcast TC across region dimension
- **Option B**: Region-specific TCs → load from Excel with Region column

```python
# Option A: Broadcast TCs (simpler, backward compatible)
tc_2d = load_tc_data()  # Shape (26, 4)
tc_3d = np.repeat(tc_2d[:, np.newaxis, :], num_regions, axis=1)  # Shape (26, 3, 4)

# Option B: Region-specific TCs (more flexible)
tc_3d = load_tc_data_with_regions()  # Load from Excel with Region column
```

### Step 1.7: Update DSM and FOMP Models

**Files**:
- `02_src/engine/dsm_model.py`
- `02_src/engine/fomp_model.py`

**Changes**: Both models need to handle 3D arrays

```python
# CURRENT - DSM operates on (time × element)
def run_dsm_process(mfa_system, process_id, parameters):
    inflow = inflow_obj.Values  # Shape (26, 4)
    outflow = np.zeros((26, 4))
    stock = np.zeros((26, 4))

    for t in range(len(years)):
        for e in range(len(elements)):
            # DSM calculation per element
            stock[t, e] = calculate_stock(inflow[:t+1, e], lifetime)

# NEW - DSM operates on (time × region × element)
def run_dsm_process(mfa_system, process_id, parameters):
    inflow = inflow_obj.Values  # Shape (26, 3, 4)
    outflow = np.zeros((26, 3, 4))
    stock = np.zeros((26, 3, 4))

    for t in range(len(years)):
        for r in range(len(regions)):
            for e in range(len(elements)):
                # DSM calculation per region per element
                stock[t, r, e] = calculate_stock(inflow[:t+1, r, e], lifetime)
```

### Step 1.8: Update Visualization Functions

**Files**: ALL files in `02_src/plotting/`

**Challenge**: How to visualize 3D+ data?

**Options**:
1. **Aggregate regions**: Sum across regions for traditional 2D plots
2. **Region selector**: Add dropdown to select region in interactive plots
3. **Multi-panel**: Show multiple regions in subplot grid
4. **Stacked plots**: Stack regions in Sankey/bar charts

```python
# Example: Aggregate for backward compatibility
def plot_flow_dynamics(mfa_results, flow_id):
    flow_data = mfa_results['FlowDict'][flow_id].Values  # Shape (26, 3, 4)

    # Aggregate across regions
    flow_data_aggregated = flow_data.sum(axis=1)  # Shape (26, 4)

    # Plot as before
    plot_time_series(flow_data_aggregated)
```

### Step 1.9: Update Excel Templates

**All input sheets need Region column**:

1. **1_2_Data_Flows**: Add Region column
2. **2_3_Process_TCs**: Add Region column (if region-specific)
3. **2_4_dynamic_tcs**: Add Region column
4. **2_5_Initial_Stock**: Add Region column
5. **3_1_Definition_DSM**: Add Region column for inflows
6. **3_2_Definition_FOMP**: Add Region column for inflows

### Step 1.10: Backward Compatibility Strategy

**CRITICAL**: Don't break existing 2D studies!

```python
def define_model_scope(start_year, end_year, elements, regions=None):
    """Maintain backward compatibility with regions=None."""

    if regions is None or len(regions) == 0:
        # 2D mode: Single default region
        regions = ["Default_Region"]
        mode = "2D"
    else:
        # 3D mode: Multiple regions
        mode = "3D"

    # Store mode in system for conditional logic
    mfa_system._dimension_mode = mode  # "2D" or "3D"
```

### Step 1.11: Testing Strategy

**Create test cases**:
1. ✅ Simple 2-region, 2-year, 2-element test
2. ✅ Verify mass balance per region
3. ✅ Verify total mass balance (sum across regions)
4. ✅ Test with existing 2D case (backward compatibility)
5. ✅ Test DSM with regions
6. ✅ Test FOMP with regions

**Test file**: `04_tests/test_3d_regions.py`

---

## PHASE 2: Add Good Aspect (t,r,e → t,r,g,e)

### Step 2.1: Extend Model Scope

```python
def define_model_scope(start_year, end_year, elements, regions, goods):
    aspects = ["Time", "Region", "Good", "Element"]
    index_letters = ["t", "r", "g", "e"]

    model_classification["Good"] = msc.Classification(
        Name="Goods",
        Dimension="Good",
        ID=4,
        Items=goods  # e.g., ["Food", "Feed", "Energy", "Material"]
    )
```

### Step 2.2: Update Array Shapes

**From 3D → 4D**:
- Flow shape: (26, 3, 4) → (26, 3, 4, 4) for 4 goods
- Total values: 312 → 1,248 per flow

### Step 2.3: Excel Structure

Add **Good** column to all data sheets:
```
Flow_ID | Region   | Good     | Year | material | WC | DM | CC
F_01_02 | Germany  | Food     | 2025 | 100     | 80 | 20 | 9
F_01_02 | Germany  | Feed     | 2025 | 50      | 40 | 10 | 4.5
F_01_02 | Germany  | Energy   | 2025 | 30      | 20 | 10 | 4.5
...
```

### Step 2.4: Solver Updates

```python
# 4D indexing [time, region, good, element]
for t in range(len(years)):
    for r in range(len(regions)):
        for g in range(len(goods)):
            for e in range(len(elements)):
                flow_value = flow.Values[t, r, g, e]
```

**Performance concern**: Nested loops become expensive!
**Solution**: Vectorize operations using NumPy broadcasting where possible

---

## PHASE 3: Add Material Aspect (t,r,g,e → t,r,g,m,e)

### Step 3.1: Extend Model Scope

```python
model_classification["Material"] = msc.Classification(
    Name="Materials",
    Dimension="Material",
    ID=5,
    Items=materials  # e.g., ["Wheat", "Corn", "Wood", "Straw", "Manure"]
)

aspects = ["Time", "Region", "Good", "Material", "Element"]
index_letters = ["t", "r", "g", "m", "e"]
```

### Step 3.2: Array Shape

**From 4D → 5D**:
- Flow shape: (26, 3, 4, 4) → (26, 3, 4, 5, 4) for 5 materials
- Total values: 1,248 → 6,240 per flow

### Step 3.3: Conceptual Challenge

**Question**: How do materials and goods interact?
- Food good can be made from Wheat OR Corn material
- Feed good can be made from Straw OR Manure material

**Solution**: Not all (good, material) combinations are valid
→ Use sparse arrays or masking for invalid combinations

---

## PHASE 4: Add Process Aspect (t,r,g,m,e → t,r,g,m,e,p)

### Step 4.1: Process as Classification

```python
model_classification["Process"] = msc.Classification(
    Name="ProcessTypes",
    Dimension="Process",
    ID=6,
    Items=process_types  # e.g., ["Splitter", "Transformer", "DSM", "FOMP", "Storage"]
)

aspects = ["Time", "Region", "Good", "Material", "Element", "Process"]
index_letters = ["t", "r", "g", "m", "e", "p"]
```

### Step 4.2: Array Shape

**From 5D → 6D**:
- Flow shape: (26, 3, 4, 5, 4) → (26, 3, 4, 5, 4, 8) for 8 process types
- Total values: 6,240 → 49,920 per flow

**Memory concern**: 50K values per flow × 50 flows = 2.5M values!

### Step 4.3: Use Case

Process aspect is mainly for:
- Classification and aggregation in reports
- Process-type specific analysis
- Not typically needed for flow calculations

**Recommendation**: Consider if this is truly needed, or if process tracking via IDs is sufficient

---

## Key Technical Considerations

### 1. Memory and Performance

**Current (2D)**: 104 values/flow × 50 flows = 5,200 values
**6D**: 49,920 values/flow × 50 flows = 2,496,000 values (480× increase!)

**Mitigation strategies**:
- Use sparse arrays for invalid combinations
- Lazy evaluation (calculate only when needed)
- Optimize with NumPy vectorization
- Consider using Dask for large datasets

### 2. Data Input Complexity

**Current**: Users fill ~500 Excel cells per case study
**6D**: Users fill ~250,000 Excel cells per case study (!!)

**Solutions**:
- Smart defaults and templates
- Bulk import from databases
- GUI for data entry
- Data validation tools
- Consider if all dimensions are always needed

### 3. Visualization Challenge

**Problem**: Can't visualize 6D data directly

**Solutions**:
- Interactive slicing (select region, good, material, view time × element)
- Aggregation (sum across selected dimensions)
- Multiple linked views
- Consider Plotly Dash for interactive dashboards

### 4. Backward Compatibility

**CRITICAL**: Existing 2D studies must still work!

**Strategy**:
```python
# Detect dimensionality from config
if regions is None:
    mode = "2D"
    indices = "t,e"
elif goods is None:
    mode = "3D"
    indices = "t,r,e"
elif materials is None:
    mode = "4D"
    indices = "t,r,g,e"
# ... etc

# Use mode-specific logic in solver
if mode == "2D":
    # Use existing 2D code paths
else:
    # Use new ND code paths
```

---

## Excel Template Changes Summary

### Current 2D Template Structure
```
1_2_Data_Flows:
Flow_ID | Year | material | WC | DM | CC
```

### 6D Template Structure
```
1_2_Data_Flows:
Flow_ID | Region | Good | Material | Year | material | WC | DM | CC | Process_Type
```

**Impact**: EVERY data input sheet needs restructuring

---

## Recommended Implementation Order

### Option A: Incremental (Recommended)
1. **Phase 1**: Add Region (3D) - 4-6 weeks
2. **Test and stabilize** - 2 weeks
3. **Phase 2**: Add Good (4D) - 4-6 weeks
4. **Test and stabilize** - 2 weeks
5. **Phase 3**: Add Material (5D) - 4-6 weeks
6. **Test and stabilize** - 2 weeks
7. **Phase 4**: Add Process (6D) - 3-4 weeks
8. **Final testing** - 3-4 weeks

**Total**: ~4-6 months

### Option B: Big Bang (Not Recommended)
- Implement all 6D at once
- Higher risk of bugs
- Difficult to test incrementally
- Estimated: 4-6 months (same time, but higher risk)

---

## Code Files Requiring Changes

### Critical Files (Major Changes)
1. ✅ `02_src/system_setup.py` - Model scope, flow/stock definitions
2. ✅ `02_src/data_loader.py` - Excel data loading
3. ✅ `02_src/engine/solver.py` - Array indexing throughout
4. ✅ `02_src/engine/dsm_model.py` - DSM calculations
5. ✅ `02_src/engine/fomp_model.py` - FOMP calculations
6. ✅ `02_src/engine/initial_stock_engine.py` - Initial stock handling

### Important Files (Moderate Changes)
7. ✅ `02_src/engine/scenario_engine.py` - Scenario analysis
8. ✅ `02_src/engine/mc_simulation.py` - Monte Carlo
9. ✅ `02_src/config.py` - Config loading
10. ✅ `02_src/utils.py` - Export functions

### Visualization Files (All require updates)
11. ✅ `02_src/plotting/sankey.py`
12. ✅ `02_src/plotting/dynamics.py`
13. ✅ `02_src/plotting/validation.py`
14. ✅ `02_src/plotting/monte_carlo.py`
15. ✅ All other plotting modules (15+ files)

### Test Files
16. ✅ `04_tests/test_solver.py`
17. ✅ `04_tests/test_system_setup.py`
18. ✅ New: `04_tests/test_3d_regions.py`
19. ✅ New: `04_tests/test_6d_integration.py`

**Estimated**: 20+ files, 200+ functions, 5,000+ lines of code changes

---

## Testing Strategy

### Unit Tests (Per Phase)
```python
def test_3d_flow_creation():
    """Test flow with t,r,e indices."""
    flow = msc.Flow(Name="F_01_02", P_Start=1, P_End=2, Indices="t,r,e")
    assert flow.Values.shape == (26, 3, 4)

def test_3d_mass_balance():
    """Verify mass balance holds per region."""
    for r in range(num_regions):
        inflow = sum(flows_in[:, r, :])
        outflow = sum(flows_out[:, r, :])
        stock_change = stocks[:, r, :]
        assert np.allclose(inflow - outflow, stock_change)

def test_backward_compatibility():
    """Ensure 2D mode still works."""
    system_2d = setup_2d_system()
    results_2d = run_solver(system_2d)
    assert results_2d is not None
```

### Integration Tests
1. ✅ Run complete case study in 3D mode
2. ✅ Verify results match sum of regional 2D studies
3. ✅ Test visualization with 3D+ data
4. ✅ Test Excel export/import round-trip

### Regression Tests
1. ✅ Existing 2D test cases must pass unchanged
2. ✅ Compare 2D vs 3D (single region) - should match
3. ✅ Verify Monte Carlo with 3D+ structure

---

## Risk Assessment

### High Risks
1. **Breaking existing studies** - Mitigate with backward compatibility
2. **Performance degradation** - Mitigate with profiling and optimization
3. **Data entry complexity** - Mitigate with smart templates and GUI
4. **Bugs in array indexing** - Mitigate with comprehensive testing

### Medium Risks
1. **Visualization becomes unwieldy** - Mitigate with aggregation options
2. **Excel file size explodes** - Mitigate with database option
3. **Memory usage too high** - Mitigate with sparse arrays

### Low Risks
1. **ODYM compatibility issues** - ODYM supports 6D natively
2. **User confusion** - Mitigate with documentation

---

## Alternative Approaches

### Option 1: Lazy Dimensions
- Only compute dimensions when needed
- Default to 2D, expand on demand
- More complex code, but better performance

### Option 2: Separate Models per Dimension Set
- Keep 2D solver for simple studies
- Create separate 6D solver for complex studies
- Duplicate code, but simpler logic

### Option 3: Database Backend
- Store data in relational database
- Query on demand
- Better for very large datasets

---

## Next Steps

### Immediate Actions
1. **Decide**: Is 6D truly needed for your research?
2. **Prioritize**: Which dimensions are most important? (Region? Good?)
3. **Pilot**: Start with Phase 1 (Region) on a small test case
4. **Review**: Present plan to research team for feedback

### Before Starting
- ✅ Create feature branch: `feature/multi-dimensional`
- ✅ Archive current 2D code as backup
- ✅ Set up comprehensive test suite
- ✅ Document current 2D behavior for regression tests

### Success Criteria
- ✅ All existing 2D studies run unchanged
- ✅ New 3D/4D/5D/6D modes work correctly
- ✅ Mass balance validated per dimension
- ✅ Performance acceptable (< 2× slowdown)
- ✅ Visualization functional
- ✅ Documentation updated

---

## Questions to Answer Before Starting

1. **Do you need ALL 6 dimensions?** Or just 3D (Region)?
2. **What's the use case?** Multi-country study? Multi-product?
3. **Data availability?** Do you have region × good × material data?
4. **Performance requirements?** How big will datasets be?
5. **Timeline?** When do you need this functionality?
6. **Resources?** Who will implement and test?

---

## Conclusion

Expanding to 6D is **technically feasible** but requires:
- **Significant development time** (4-6 months)
- **Careful testing** to avoid breaking existing functionality
- **Thoughtful design** for usability with high-dimensional data
- **Performance optimization** to handle larger arrays

**Recommendation**: Start with **Phase 1 (Region)** only, then evaluate if further dimensions are truly needed for your research goals.

---

**Document Status**: Draft roadmap for discussion
**Author**: Claude Code Analysis
**Next Review**: After team discussion of priorities and timeline
