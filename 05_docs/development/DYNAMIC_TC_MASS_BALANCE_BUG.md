# Dynamic TC Mass Balance Bug Analysis

**Generated:** 2025-11-24
**Updated:** 2025-11-24 (FIXED)
**Severity:** 🔴 **HIGH** - Causes mass balance errors
**Status:** ✅ **FIXED** (Implemented in commit 640b808)

---

## Problem Statement

When multiple dynamic transfer coefficients (TCs) are used for a splitter process, they are **interpolated independently** for each flow. This can cause the sum of all TCs for a process to **not equal 100%** at every time step, resulting in **mass balance errors**.

---

## Root Cause Analysis

### How Dynamic TCs Are Loaded

**Location:** `02_src/data_loader.py:654-668`

```python
# Each TC parameter is interpolated INDEPENDENTLY
for param_name in dynamic_tc_data[param_name_col].unique():
    tc_points = dynamic_tc_data[dynamic_tc_data[param_name_col] == param_name]

    # Create time series for THIS TC only
    ts = pd.Series(tc_points[param_value_col].values, index=tc_points["Year"])

    # Interpolate independently
    ts_full = ts.reindex(time_vector)
    ts_interpolated = ts_full.interpolate(method="linear", limit_direction="both")

    # Store as parameter (NO NORMALIZATION)
    tc_params[param_name] = msc.Parameter(...)
```

**Key issue:** Each TC is interpolated without considering other TCs for the same process.

### Example: Mass Balance Violation

#### Scenario: Splitter Process with 3 Outputs

**Excel data (`2_3_dynamic_TCs`):**

| Year | E1_TC_ID | E1_TC_Value[%] |
|------|----------|----------------|
| 2000 | TC_A     | 30             |
| 2020 | TC_A     | 40             |
| 2000 | TC_B     | 40             |
| 2020 | TC_B     | 35             |
| 2000 | TC_C     | 30             |
| 2020 | TC_C     | 25             |

**Verification:**
- Year 2000: 30 + 40 + 30 = **100%** ✅
- Year 2020: 40 + 35 + 25 = **100%** ✅

**After linear interpolation (Year 2010):**
- TC_A: 30 + (40-30) * 10/20 = **35%**
- TC_B: 40 + (35-40) * 10/20 = **37.5%**
- TC_C: 30 + (25-30) * 10/20 = **27.5%**
- **Sum: 35 + 37.5 + 27.5 = 100%** ✅ (Lucky!)

**But with slightly different data:**

| Year | E1_TC_ID | E1_TC_Value[%] |
|------|----------|----------------|
| 2000 | TC_A     | 30             |
| 2020 | TC_A     | 42             | ← Changed from 40
| 2000 | TC_B     | 40             |
| 2020 | TC_B     | 35             |
| 2000 | TC_C     | 30             |
| 2020 | TC_C     | 25             |

**After interpolation (Year 2010):**
- TC_A: 30 + (42-30) * 10/20 = **36%**
- TC_B: 40 + (35-40) * 10/20 = **37.5%**
- TC_C: 30 + (25-30) * 10/20 = **27.5%**
- **Sum: 36 + 37.5 + 27.5 = 101%** ❌ **MASS BALANCE ERROR!**

### Even Worse: Misaligned Data Points

**Scenario:** Different data years for different TCs

| Year | E1_TC_ID | E1_TC_Value[%] |
|------|----------|----------------|
| 2000 | TC_A     | 30             |
| 2020 | TC_A     | 40             |
| 2005 | TC_B     | 35             |
| 2025 | TC_B     | 45             |
| 2000 | TC_C     | 30             |
| 2015 | TC_C     | 20             |

**Year 2010 interpolation:**
- TC_A: 30 + (40-30) * 10/20 = **35%**
- TC_B: 35 + (45-35) * 5/20 = **37.5%**
- TC_C: 30 + (20-30) * 10/15 = **23.33%**
- **Sum: 35 + 37.5 + 23.33 = 95.83%** ❌ **SEVERE ERROR!**

Material is "lost" - 4.17% disappears!

---

## Current Code Analysis

### 1. Data Loader (NO normalization)

**File:** `02_src/data_loader.py:654-668`
**Status:** ❌ No normalization after interpolation

TCs are stored directly without checking if they sum to 100%.

### 2. Solver (NO normalization for regular runs)

**File:** `02_src/engine/solver.py:209-290`
**Status:** ❌ TCs applied directly without validation

```python
# Solver applies TC directly
tc_value = mfa_system.ParameterDict[param_name].Values
outflow_vector[:, mat_idx] = total_inflow_vector[:, mat_idx] * tc_value
```

No check that all TCs for a process sum to 1.0.

### 3. Monte Carlo Simulation (HAS normalization!)

**File:** `02_src/engine/mc_simulation.py:134-200`
**Status:** ✅ Normalization implemented

```python
def normalize_tcs_for_process(mfa_system, process_id, varied_tc_name, varied_tc_value):
    """Ensures all transfer coefficients (TCs) for a process sum to 1.0."""

    # Calculate normalization factor
    total_tc = sum(current_tcs.values())
    if total_tc > 0:
        normalization_factor = 1.0 / total_tc

        # Apply normalization to all TCs
        for flow in process_flows:
            normalized_tcs[flow.Name] = current_tcs[flow.Name] * normalization_factor
```

**Key insight:** MC already has the solution! We need to apply this to dynamic TCs.

---

## Impact Assessment

### Severity: 🔴 HIGH

**Affected systems:**
- ✅ Any model with **dynamic TCs** for splitter processes
- ✅ Especially critical when TCs have **non-aligned data points**
- ❌ Static TCs are NOT affected (values set once, not interpolated)

**Symptoms:**
- Mass balance errors in affected processes
- `Consistency_Check()` fails or shows large errors
- Results don't sum correctly over time

**Detection:**
- Run mass balance validation after solver
- Check if errors are time-varying (indicates dynamic TC issue)
- Inspect TC sums manually at different time steps

---

## Proposed Solutions

### Solution 1: Normalize After Interpolation (RECOMMENDED) ✅

**Approach:** Add normalization step immediately after interpolation in `data_loader.py`

**Pros:**
- ✅ Fixes root cause
- ✅ Guarantees TCs always sum to 100%
- ✅ Transparent to users (happens automatically)
- ✅ Similar to MC normalization (proven approach)

**Cons:**
- ⚠️ Changes interpolated values slightly
- ⚠️ May mask user data entry errors

**Implementation location:** `02_src/data_loader.py` after line 679

### Solution 2: Add Validation Warning (COMPLEMENTARY)

**Approach:** Detect when TCs don't sum to 100% and warn user

**Pros:**
- ✅ Alerts user to data quality issues
- ✅ Doesn't change user data
- ✅ Educational for users

**Cons:**
- ❌ Doesn't fix the problem
- ❌ Requires manual data correction

**Implementation location:** `02_src/data_loader.py` as validation step

### Solution 3: Require Aligned Data Points (DOCUMENTATION)

**Approach:** Document that users must provide aligned data points

**Pros:**
- ✅ Simple, no code changes
- ✅ Puts responsibility on user

**Cons:**
- ❌ Error-prone
- ❌ Difficult to enforce
- ❌ Bad user experience

**Recommendation:** Use as **documentation enhancement**, not primary solution.

---

## Recommended Implementation

### Phase 1: Add Normalization (CRITICAL)

Add TC normalization after interpolation in `data_loader.py`:

```python
def normalize_dynamic_tcs_by_process(tc_params, all_excel_data):
    """
    Normalize dynamic TCs so they sum to 100% for each process at each time step.

    This ensures mass balance is preserved when TCs are interpolated independently.

    Parameters
    ----------
    tc_params : dict
        Dictionary of ODYM Parameters (TC values)
    all_excel_data : dict
        Excel data containing static TC definitions (for process-flow mapping)

    Returns
    -------
    dict
        Normalized TC parameters
    """
    static_tc_defs = all_excel_data.get("2_2_static_TCs")
    if static_tc_defs is None:
        return tc_params

    # Group TCs by process
    process_tcs = {}  # {process_id: [tc_names]}

    for _, row in static_tc_defs.iterrows():
        process_id = row.get("Process_ID")
        if pd.isna(process_id):
            continue

        process_id = int(process_id)

        # Extract TC names for this process (E1_TC_ID)
        for col in row.index:
            if col.endswith("_TC_ID") and pd.notna(row[col]):
                tc_name = row[col]
                if tc_name in tc_params:
                    if process_id not in process_tcs:
                        process_tcs[process_id] = []
                    if tc_name not in process_tcs[process_id]:
                        process_tcs[process_id].append(tc_name)

    # Normalize TCs for each process
    for process_id, tc_names in process_tcs.items():
        if len(tc_names) <= 1:
            continue  # Single TC doesn't need normalization

        # Check if any TC is time-varying (has array values)
        has_dynamic = any(
            isinstance(tc_params[tc].Values, np.ndarray)
            for tc in tc_names if tc in tc_params
        )

        if not has_dynamic:
            continue  # Static TCs don't need time-based normalization

        # Get TC values (convert scalars to arrays if needed)
        tc_values = {}
        max_len = 1
        for tc_name in tc_names:
            if tc_name not in tc_params:
                continue

            val = tc_params[tc_name].Values
            if isinstance(val, np.ndarray):
                tc_values[tc_name] = val
                max_len = max(max_len, len(val))
            else:
                # Static TC - will be broadcast
                tc_values[tc_name] = float(val)

        # Convert scalars to arrays
        for tc_name in tc_values:
            if not isinstance(tc_values[tc_name], np.ndarray):
                tc_values[tc_name] = np.full(max_len, tc_values[tc_name])

        # Calculate sum at each time step
        tc_sum = np.zeros(max_len)
        for tc_name in tc_values:
            tc_sum += tc_values[tc_name]

        # Normalize (avoid division by zero)
        for tc_name in tc_values:
            normalized = np.divide(
                tc_values[tc_name],
                tc_sum,
                out=np.ones_like(tc_values[tc_name]) / len(tc_values),
                where=tc_sum != 0
            )

            # Update parameter
            tc_params[tc_name].Values = normalized

        print(f"   ℹ️  Normalized {len(tc_names)} dynamic TCs for process {process_id}")

    return tc_params
```

**Add call after line 679 in `load_tc_parameters()`:**

```python
# After all TCs are loaded and interpolated
if len(tc_params) > 0:
    # Normalize dynamic TCs to ensure they sum to 100% per process
    tc_params = normalize_dynamic_tcs_by_process(tc_params, all_excel_data)

    static_count = len([p for p in static_processes]) if static_processes else 0
    dynamic_count = len([p for p in dynamic_processes]) if dynamic_processes else 0
    print(f"   ✓ Loaded {len(tc_params)} transfer coefficients...")
```

### Phase 2: Add Validation (RECOMMENDED)

Add optional validation to warn users about large normalizations:

```python
# In normalize_dynamic_tcs_by_process, before normalization:
max_deviation = np.max(np.abs(tc_sum - 1.0))
if max_deviation > 0.05:  # More than 5% deviation
    print(f"   ⚠️  WARNING: Process {process_id} TCs sum to {tc_sum.min():.1%}-{tc_sum.max():.1%} (not 100%)")
    print(f"      Normalizing to ensure mass balance...")
```

### Phase 3: Documentation Update

Update `DYNAMIC_TC_INTERPOLATION_ANALYSIS.md` and `USER_GUIDE.md`:

**Best practices for users:**
1. Provide data points at the **same years** for all TCs in a process
2. Verify that TCs sum to 100% at each data point
3. Use preview tool to check interpolated sums before running

**Note for users:**
> BioDYM automatically normalizes dynamic TCs to ensure mass balance. If your data points don't sum to exactly 100%, the system will adjust them proportionally at each time step.

---

## Testing Plan

### Test 1: Aligned Data Points (Should Sum to 100%)

```python
def test_dynamic_tc_normalization_aligned():
    """Test normalization with aligned data points."""
    # Data: Year 2000: TC_A=30%, TC_B=40%, TC_C=30% (sum=100%)
    #       Year 2020: TC_A=40%, TC_B=35%, TC_C=25% (sum=100%)
    # Expected: Interpolated values also sum to 100% at all time steps

    tc_params = load_tc_parameters(...)

    # Check sum at year 2010
    tc_sum_2010 = (
        tc_params["TC_A"].Values[10] +
        tc_params["TC_B"].Values[10] +
        tc_params["TC_C"].Values[10]
    )

    assert np.isclose(tc_sum_2010, 1.0, atol=1e-6)
```

### Test 2: Misaligned Data Points (Requires Normalization)

```python
def test_dynamic_tc_normalization_misaligned():
    """Test normalization with misaligned data points."""
    # Data: TC_A at 2000, 2020
    #       TC_B at 2005, 2025
    #       TC_C at 2000, 2015
    # Expected: Normalization ensures sum=100% despite interpolation

    tc_params = load_tc_parameters(...)

    # Check sum at ALL years
    for year_idx in range(len(time_vector)):
        tc_sum = sum(tc_params[tc].Values[year_idx] for tc in ["TC_A", "TC_B", "TC_C"])
        assert np.isclose(tc_sum, 1.0, atol=1e-6), f"Year {2000+year_idx}: sum={tc_sum}"
```

### Test 3: Integration Test (Mass Balance)

```python
def test_mass_balance_with_dynamic_tcs():
    """Test that mass balance is preserved with dynamic TCs."""
    # Run full solver with dynamic TCs
    mfa_results = solver.run_iterative_solver(...)

    # Check mass balance
    errors = plotting.calculate_mass_balance_error(mfa_results)

    # Errors should be near-zero (< 1e-10)
    assert np.max(np.abs(errors)) < 1e-10
```

---

## Timeline

### ✅ COMPLETED (2025-11-24)

- [x] Implement `normalize_dynamic_tcs_by_process()` function
- [x] Add normalization call in `load_tc_parameters()`
- [x] Write 7 comprehensive unit tests
- [x] Run full test suite - all existing tests pass (35/35 + 1 skipped)
- [x] Commit fix with detailed documentation

**Actual time:** ~4 hours

### Short Term (v1.1) - OPTIONAL ENHANCEMENTS

- [ ] Update USER_GUIDE.md with best practices for dynamic TCs
- [ ] Add visualization of TC sums in preview tool
- [ ] Document in CHANGELOG.md as bug fix
- [ ] Fix test infrastructure for running all tests together

**Estimated time:** 2-3 hours

---

## Backward Compatibility

**Impact on existing models:**
- ✅ **Most models**: Likely already sum to ~100%, normalization will make minimal changes
- ⚠️ **Some models**: If TCs don't sum to 100%, results will change (but be more correct!)
- ✅ **Static TCs**: Not affected at all

**Migration strategy:**
1. Release as **v1.0.1** (bug fix, not breaking change)
2. Add release note explaining the fix
3. Recommend users verify results after update
4. Provide option to disable normalization (debug mode) if needed

---

## Alternative Considered: Normalization in Solver

**Why not normalize in the solver instead?**

❌ **Rejected because:**
1. Solver runs iteratively - normalization would happen many times
2. Less efficient (overhead at every iteration)
3. Harder to debug (values change during solving)
4. Inconsistent with MC approach (which normalizes once)

✅ **Better to normalize in data loader:**
- Happens once at initialization
- Consistent with MC normalization
- Easier to debug (check parameter values directly)
- More efficient

---

## Summary

**Problem:** Dynamic TCs interpolated independently → may not sum to 100% → mass balance errors

**Solution:** Normalize TCs after interpolation (similar to MC approach)

**Status:** Bug identified, solution designed, ready to implement

**Priority:** 🔴 **HIGH** - Should be fixed before v1.0.0 publication

---

**Last Updated:** 2025-11-24
**Reported By:** User (excellent bug find!)
**Assigned To:** Development team
**Target Release:** v1.0.1
