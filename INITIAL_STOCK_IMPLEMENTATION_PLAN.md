# BioDYM Initial Stock Implementation Plan
## Addressing Reviewer Critiques on DSM Initial Stock Handling

**Date:** December 7, 2025
**Status:** In Progress

---

## Problem Summary

Reviewer #2 identified critical issues with DSM initial stock handling:

1. **Element Composition "Transmutation"**: Initial stock outflows get composition from **new inflows** instead of preserving original composition
2. **Mathematical Inconsistency**: Initial stock uses exponential decay (k=1/lifetime) while new inflows use cohort-based survival functions
3. **Lack of Rigor**: No option for proper age-cohort tracking as implemented in ODYM

---

## Solution: Dual-Mode DSM Initial Stock

We're implementing two explicit modes for DSM initial stock handling, selectable via `Stock_Configuration` column.

###Stock_Configuration** Values:

| Value | Process Logic | Description |
|-------|---------------|-------------|
| `No_Stock` | Any | No stock |
| `Stock` | Any | Standard stock (current default, backwards compatible) |
| **`Stock_with_InitialStock_Decay`** | **DSM** | **Simple exponential decay for initial stock** |
| **`Stock_with_InitialStock_Cohort`** | **DSM** | **ODYM age-cohort method for initial stock** |

---

## Mode 1: Stock_with_InitialStock_Decay

**Use Case:** Existing stocks where age structure is unknown, simple decay acceptable

**Behavior:**
- Initial stock decays via: `outflow = stock * (1/avg_lifetime)`
- Element composition **PRESERVED from initial stock definition** ← **FIX NEEDED**
- New inflows follow DSM lifetime distributions

**Required Input (2_4_Initial_Stock sheet):**
- `IS_material_quantity[UoM]` - Total initial stock
- `IS_E2_[%](WC)` - Water content
- `IS_E3_[%](DM)` - Dry matter
- `IS_E4_[%](CC)` - Carbon content
- etc.

**Example:**
```
Process: Compost Facility
Initial Stock: 100 Mg wood chips (45% carbon)
Decay rate: 1/5 years = 20% per year
Year 1 outflow: 20 Mg with 9 Mg carbon (45% preserved) ✅
```

---

## Mode 2: Stock_with_InitialStock_Cohort

**Use Case:** Stocks with known or assumed age structure, rigorous modeling required

**Behavior:**
- Initial stock distributed across age cohorts (uniform, exponential, or custom)
- Each cohort follows **same survival function** as new inflows
- Mathematically consistent with ODYM

**Required Input (2_4_Initial_Stock sheet):**
- `IS_material_quantity[UoM]` - Total initial stock
- `IS_E2_[%](WC)`, `IS_E3_[%](DM)`, `IS_E4_[%](CC)` - Composition
- **`IS_Age_Distribution_Type`** - `"uniform"` or `"exponential"`
- **`IS_Max_Age[years]`** - Maximum age in initial stock

**Optional:**
- `IS_Age_Decay_Constant[years]` - For exponential distribution tuning

**Age Distribution Types:**

1. **Uniform**: All ages equally represented
   ```
   100 Mg stock, max age 10 years:
   Age 0-1: 10 Mg, Age 1-2: 10 Mg, ..., Age 9-10: 10 Mg
   ```

2. **Exponential**: Recent ages more common (realistic for most stocks)
   ```
   100 Mg stock, max age 10 years:
   Age 0-1: 25 Mg, Age 1-2: 20 Mg, ..., Age 9-10: 2 Mg
   ```

**Example:**
```
Process: Building Stock
Initial Stock: 500 Mg (uniform age 0-50 years)
Lifetime: Normal(50, 10)

Buildings aged 45-50 years → High outflow in next 5-10 years
Buildings aged 0-10 years → Low outflow
```

---

## Implementation Status

### ✅ Completed

1. **Updated `data_loader.py` validation** (lines 448-458)
   - DSM processes now accept all three Stock_Configuration values
   - Clear error messages for invalid combinations

2. **Updated stock process identification** (lines 989-999)
   - All stock variants recognized and processed

3. **Pass Stock_Configuration to DSM params** (lines 950-955)
   - DSM model will receive `stock_configuration` parameter

### 🔄 In Progress

4. **Excel Template Update** (User doing this)
   - Add `Stock_with_InitialStock_Decay` option
   - Add `Stock_with_InitialStock_Cohort` option
   - Add example data for new parameters

### ⏳ To Do

5. **Create age cohort generation function**
   - Location: `02_src/engine/dsm_model.py` or new `age_cohort_utils.py`
   - Functions:
     ```python
     def generate_uniform_age_cohorts(total_stock, max_age)
     def generate_exponential_age_cohorts(total_stock, max_age, decay_constant)
     ```

6. **Update `initial_stock_engine.py`**
   - Read `IS_Age_Distribution_Type` and `IS_Max_Age` parameters
   - Validate parameters for cohort mode
   - Store in initial_stock_config

7. **Fix composition preservation in Decay mode**
   - Location: `02_src/engine/dsm_model.py` lines 202-225
   - Current problem: Uses `total_inflow_values` composition for initial stock outflow
   - Solution: Track initial stock composition separately
   ```python
   # Current (WRONG):
   factor = total_inflow_values[:, elem_idx] / total_inflow_values[:, 0]
   outflow[:, elem_idx] = (outflow_from_inflows + outflow_from_initial) * factor

   # Fixed (RIGHT):
   outflow_from_inflows[:, elem_idx] = outflow_from_inflows[:, 0] * inflow_factor
   outflow_from_initial[:, elem_idx] = outflow_from_initial[:, 0] * initial_stock_factor
   ```

8. **Implement cohort mode in DSM model**
   - Location: `02_src/engine/dsm_model.py`
   - Check `stock_configuration` parameter
   - If `"Stock_with_InitialStock_Cohort"`:
     - Generate age cohorts from distribution
     - Apply element composition to all cohorts
     - Use ODYM `compute_evolution_initialstock()`
     - Combine with new inflows properly

9. **Update DSM plotting**
   - Show which initial stock mode is used in legend
   - Conditionally display initial stock layer only if present

10. **Add validation**
    - Check: `Stock_with_InitialStock_*` requires data in `2_4_Initial_Stock`
    - Check: Cohort mode requires age distribution parameters
    - Warn if parameters missing

11. **Testing**
    - Test Decay mode with composition preservation
    - Test Cohort mode with uniform distribution
    - Test Cohort mode with exponential distribution
    - Verify backwards compatibility with `Stock` mode

12. **Documentation**
    - Update methodology chapter
    - Add examples for both modes
    - Document when to use which mode

---

## File Locations

| Component | File | Lines |
|-----------|------|-------|
| Validation | `02_src/data_loader.py` | 448-458 |
| Stock identification | `02_src/data_loader.py` | 989-999 |
| Stock_config passing | `02_src/data_loader.py` | 950-955 |
| Initial stock engine | `02_src/engine/initial_stock_engine.py` | Full file |
| DSM model | `02_src/engine/dsm_model.py` | 85-379 |
| Composition issue | `02_src/engine/dsm_model.py` | 202-225 |
| ODYM cohort method | `06_framework/ODYM-master_20241127/odym/modules/dynamic_stock_model.py` | 434-455 |

---

## Next Steps

1. **You:** Update Excel template with new Stock_Configuration options
2. **Me:** Create age cohort generation functions
3. **Me:** Fix composition preservation in Decay mode (CRITICAL)
4. **Me:** Implement Cohort mode integration
5. **Together:** Test with your case studies
6. **Together:** Update documentation for paper

---

## Benefits for Reviewers

✅ **Addresses Reviewer Concern #1**: Element composition preserved correctly
✅ **Addresses Reviewer Concern #2**: Mathematical consistency with ODYM (Cohort mode)
✅ **Addresses Reviewer Concern #3**: Rigorous age-cohort option available
✅ **Backwards Compatible**: Existing models still work with `Stock` mode
✅ **User Choice**: Simple decay vs rigorous cohort, user decides based on data availability
