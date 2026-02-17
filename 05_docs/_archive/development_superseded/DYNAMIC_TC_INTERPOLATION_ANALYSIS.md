# Dynamic Transfer Coefficient Interpolation Analysis

**Generated:** 2025-11-24
**Purpose:** Comprehensive documentation of dynamic TC handling and interpolation logic

---

## Overview

BioDYM supports **time-varying transfer coefficients** through the `2_3_dynamic_TCs` sheet. This allows modeling of processes where material splits or transformation efficiencies change over time (e.g., increasing recycling rates, improving technology efficiency).

---

## Excel Data Structure

### Sheet: `2_3_dynamic_TCs`

**Required Columns:**
- `Year` - The year for this data point (integer)
- `E#_TC_ID` - The TC parameter name (e.g., `TC_1`, `TC_rec_rate`)
- `E#_TC_Value[%]` - The TC value for that year (percentage, 0-100)

**Element Format:**
- New format: `E1_TC_ID`, `E1_TC_Value[%]` (E1=material, E2=WC, E3=DM, E4=CC)
- Old format: `TC_material_ID`, `TC_Value_material` (still supported)

### Example Data

| Year | E1_TC_ID | E1_TC_Value[%] | E2_TC_ID | E2_TC_Value[%] |
|------|----------|----------------|----------|----------------|
| 2000 | TC_rec   | 10.0           | TC_rec   | 10.0           |
| 2010 | TC_rec   | 25.0           | TC_rec   | 25.0           |
| 2020 | TC_rec   | 45.0           | TC_rec   | 45.0           |
| 2030 | TC_rec   | 60.0           | TC_rec   | 60.0           |

**Interpretation:** Recycling rate (`TC_rec`) increases from 10% in 2000 to 60% by 2030.

---

## Interpolation Algorithm

### Location
`02_src/data_loader.py:654-668`

### Step-by-Step Process

```python
# 1. Extract data points for specific TC parameter
tc_points = dynamic_tc_data[dynamic_tc_data[param_name_col] == param_name]

# 2. Create pandas Series with Year as index
ts = pd.Series(
    tc_points[param_value_col].values,
    index=tc_points["Year"]
)

# 3. Reindex to full model time vector (e.g., 2000-2050)
ts_full = ts.reindex(time_vector)

# 4. LINEAR INTERPOLATION between data points
ts_interpolated = ts_full.interpolate(
    method="linear",
    limit_direction="both"  # Extrapolate to start/end if needed
)

# 5. Handle edge cases (forward-fill then backward-fill)
if ts_interpolated.isna().any():
    ts_interpolated = ts_interpolated.ffill().bfill()

# 6. Store as ODYM Parameter
tc_params[param_name] = msc.Parameter(
    Name=param_name,
    ID=param_id_counter,
    Values=ts_interpolated.to_numpy(),  # Full time series array
    Unit="1",
)
```

---

## Interpolation Method Details

### Pandas `.interpolate(method="linear")`

**What it does:**
- Fills missing values between known data points using **linear interpolation**
- Formula: `value_at_year = value_before + (value_after - value_before) * (year - year_before) / (year_after - year_before)`

**Example:**
```
Data points:
  2000: 10%
  2010: 25%
  2020: 45%

Interpolated values:
  2005: 10 + (25-10) * (2005-2000)/(2010-2000) = 10 + 15*0.5 = 17.5%
  2015: 25 + (45-25) * (2015-2010)/(2020-2010) = 25 + 20*0.5 = 35.0%
```

### `limit_direction="both"`

- Extrapolates values **before** the first data point and **after** the last data point
- Uses linear trend from nearest two points
- **Important:** If only one data point exists, extrapolation fails → fallback to forward/backward fill

### Fallback: `ffill().bfill()`

If interpolation leaves NaN values (e.g., single data point, gaps at edges):
1. **Forward fill (`ffill`)**: Copy last known value forward
2. **Backward fill (`bfill`)**: Copy next known value backward

**Example (single data point):**
```
Data:      [NaN, NaN, 25%, NaN, NaN]
After ffill: [NaN, NaN, 25%, 25%, 25%]
After bfill: [25%, 25%, 25%, 25%, 25%]
```

---

## Use Cases and Scenarios

### 1. Increasing Recycling Rate

**Excel Data:**
| Year | E1_TC_ID | E1_TC_Value[%] |
|------|----------|----------------|
| 2000 | TC_rec   | 10             |
| 2020 | TC_rec   | 30             |
| 2040 | TC_rec   | 50             |

**Interpolated Result (2000-2050):**
- 2000: 10%
- 2010: 20% (interpolated)
- 2020: 30%
- 2030: 40% (interpolated)
- 2040: 50%
- 2050: 60% (extrapolated linearly)

### 2. Technology Improvement (Step Change)

**Excel Data:**
| Year | E1_TC_ID | E1_TC_Value[%] |
|------|----------|----------------|
| 2000 | TC_eff   | 60             |
| 2024 | TC_eff   | 60             |
| 2025 | TC_eff   | 85             |
| 2050 | TC_eff   | 85             |

**Interpolated Result:**
- 2000-2024: 60% (constant)
- 2024-2025: Linear ramp from 60% → 85%
- 2025-2050: 85% (constant)

### 3. Policy-Driven Change

**Excel Data:**
| Year | E1_TC_ID | E1_TC_Value[%] |
|------|----------|----------------|
| 2020 | TC_bio   | 5              |
| 2030 | TC_bio   | 15             |
| 2040 | TC_bio   | 30             |

**Use case:** Bio-based material substitution rate increases due to policy.

---

## Current Behavior Analysis

### ✅ Strengths

1. **Simple and predictable**: Linear interpolation is easy to understand and verify
2. **Robust fallback**: `ffill().bfill()` handles edge cases gracefully
3. **Element-aware**: Each element (E1, E2, E3, E4) can have independent time profiles
4. **Extrapolation support**: `limit_direction="both"` extends trends beyond data range

### ⚠️ Potential Limitations

1. **Linear only**: No support for non-linear trends (exponential, S-curves, etc.)
2. **Extrapolation risk**: Linear extrapolation can produce unrealistic values outside data range
   - Example: 10% → 50% → 90% extrapolates to 130% (impossible!)
3. **No bounds checking**: Interpolated values not checked for physical constraints (0-100%)
4. **Sparse data handling**: Single data point = constant value (may not be intended)

---

## Recommendations

### Short Term (v1.0.0 - Current) ✅

**Status:** Current implementation is **adequate** for most use cases.

**Best practices for users:**
1. Provide at least 2 data points per TC parameter
2. Include boundary years (first and last year of model) to avoid extrapolation
3. Verify interpolated values visually before running full analysis
4. Use small time steps between points for smooth transitions

### Medium Term (v1.1) - Enhancements

1. **Add interpolation method option**
   - Allow users to choose: `linear`, `polynomial`, `spline`, `pchip`
   - Store in `0_Configuration` sheet: `TC_Interpolation_Method = "linear"`

2. **Add bounds validation**
   - Check that all TC values are in [0, 100] range
   - Warn user if extrapolation produces invalid values
   - Option to clip to valid range

3. **Add visualization tool**
   - Plot interpolated TC profiles vs. original data points
   - Help users verify before running analysis
   - Example: `plot_dynamic_tc_preview(excel_data, "TC_rec")`

4. **Add support for constant extrapolation**
   - Option: `TC_Extrapolation_Method = "constant"` (use edge values, no linear trend)
   - Safer than linear for most physical systems

### Long Term (v2.0) - Advanced Features

1. **S-curve interpolation**
   - Model technology adoption curves (slow → fast → saturating)
   - Logistic function: `y = L / (1 + exp(-k*(t-t0)))`

2. **Scenario-specific TCs**
   - Allow different TC profiles per scenario
   - Sheet: `2_3_dynamic_TCs_scenario_baseline`, `2_3_dynamic_TCs_scenario_high_recycling`

3. **Data reconciliation**
   - Smooth noisy data points using optimization
   - Ensure mass balance closure with dynamic TCs

---

## Implementation Details

### Code Location

**Primary function:** `load_tc_parameters()`
**File:** `02_src/data_loader.py:469-688`
**Key section:** Lines 654-668 (interpolation)

### Dependencies

- **pandas**: `Series.reindex()`, `.interpolate()`, `.ffill()`, `.bfill()`
- **numpy**: Convert to array for ODYM Parameter
- **ODYM**: Store as `msc.Parameter` with time dimension

### Performance

- **Complexity:** O(n) per TC parameter, where n = number of time steps
- **Bottleneck:** None (interpolation is fast even for large time ranges)
- **Scalability:** Can handle hundreds of dynamic TCs without issue

---

## Testing

### Current Test Coverage

**Test file:** `04_tests/test_data_loader.py`
**Test:** `test_load_tc_parameters_dynamic_tcs`

**What it tests:**
- Correct loading of dynamic TC data
- Proper format detection (E# vs old format)
- Parameter creation with correct dimensions

**Not tested:**
- Interpolation correctness (actual values)
- Edge case handling (single point, extrapolation)
- Bounds validation

### Recommended Additional Tests (v1.1)

1. **Test interpolation correctness**
   ```python
   def test_dynamic_tc_interpolation():
       # Data: 2000=10%, 2010=20%
       # Expected: 2005=15%
       assert interpolated_value[5] == 15.0
   ```

2. **Test extrapolation behavior**
   ```python
   def test_dynamic_tc_extrapolation():
       # Data: 2000=10%, 2010=20%
       # Expected: 1995=5%, 2015=25%
       assert interpolated_value[-5] == 5.0
       assert interpolated_value[15] == 25.0
   ```

3. **Test edge cases**
   ```python
   def test_dynamic_tc_single_point():
       # Data: only 2010=50%
       # Expected: all years = 50%
       assert all(interpolated_value == 50.0)
   ```

4. **Test bounds validation**
   ```python
   def test_dynamic_tc_bounds():
       # Data: 2000=90%, 2010=110% (invalid!)
       # Expected: warning or error
   ```

---

## Example: Complete Workflow

### Step 1: Define Dynamic TC in Excel

**Sheet `2_3_dynamic_TCs`:**
| Year | E1_TC_ID | E1_TC_Value[%] |
|------|----------|----------------|
| 2000 | TC_1     | 20             |
| 2020 | TC_1     | 50             |
| 2040 | TC_1     | 80             |

### Step 2: Mark Process as Dynamic

**Sheet `2_1_Definition_Processes`:**
| Process_ID | Process_Name | Process_Logic | TC_Configuration |
|------------|--------------|---------------|------------------|
| 5          | Splitter_A   | Splitter      | Dynamic          |

### Step 3: Link TC to Flow

**Sheet `2_2_static_TCs`:**
| Flow_ID | Process_ID | E1_TC_ID |
|---------|------------|----------|
| 10      | 5          | TC_1     |

(Note: TC_ID defined, but values come from dynamic sheet)

### Step 4: Run Model

BioDYM automatically:
1. Loads data points (2000, 2020, 2040)
2. Interpolates for all years (2000-2050)
3. Applies time-varying TC during solver iterations

### Step 5: Verify Results

Check solver output for time-varying flow splits:
```python
# Flow 10 split in process 5 over time
print(mfa_system.ParameterDict["TC_1"].Values)
# Output: [20, 21.5, 23, ..., 50, ..., 80, 82, 84, ...] (51 values)
```

---

## Comparison with Alternatives

### Option 1: Linear Interpolation (Current) ✅

**Pros:**
- Simple, predictable
- Works for most use cases
- Fast

**Cons:**
- Can't model non-linear trends
- Extrapolation risk

### Option 2: Polynomial Interpolation

**Pros:**
- Smoother curves
- Better for gradual changes

**Cons:**
- Can overshoot (Runge's phenomenon)
- Requires more data points
- Less predictable

### Option 3: Spline Interpolation

**Pros:**
- Smooth, no overshooting
- Professional appearance

**Cons:**
- More complex
- Requires scipy
- Harder to understand for users

### Option 4: Step Function (Piecewise Constant)

**Pros:**
- No interpolation artifacts
- Clear policy changes

**Cons:**
- Discontinuities can cause solver issues
- Unrealistic for most physical systems

**Recommendation:** Keep linear as default, add spline as option in v1.1.

---

## Debugging Dynamic TCs

### How to Check Interpolated Values

1. **Enable debug mode:**
   ```python
   tc_params = load_tc_parameters(
       excel_data,
       elements,
       time_vector,
       debug_mode=True
   )
   ```

2. **Inspect parameter values:**
   ```python
   for param_name, param in tc_params.items():
       print(f"{param_name}: {param.Values}")
   ```

3. **Plot interpolated profile:**
   ```python
   import matplotlib.pyplot as plt
   plt.plot(time_vector, tc_params["TC_1"].Values)
   plt.xlabel("Year")
   plt.ylabel("TC Value [%]")
   plt.title("Dynamic TC: TC_1")
   plt.show()
   ```

### Common Issues

**Issue 1: TC constant despite dynamic data**
- **Cause:** Process not marked as `TC_Configuration="Dynamic"`
- **Fix:** Update `2_1_Definition_Processes` sheet

**Issue 2: Unexpected jumps in TC values**
- **Cause:** Missing data points, large gaps
- **Fix:** Add intermediate data points for smoother transition

**Issue 3: TC > 100% or < 0%**
- **Cause:** Linear extrapolation beyond data range
- **Fix:** Add boundary data points at model start/end years

**Issue 4: TC not applied to flow**
- **Cause:** TC_ID mismatch between `2_2_static_TCs` and `2_3_dynamic_TCs`
- **Fix:** Ensure TC_ID spelling is identical

---

## Summary

**Dynamic TC interpolation in BioDYM is:**
- ✅ **Simple and effective** for most use cases
- ✅ **Linear interpolation** with robust fallback
- ✅ **Element-aware** (each element independent)
- ✅ **Well-integrated** with ODYM Parameter framework

**Recommended improvements for future versions:**
- 🔧 Add interpolation method options (spline, polynomial)
- 🔧 Add bounds validation (0-100% range)
- 🔧 Add visualization tool for preview
- 🔧 Add constant extrapolation option (safer than linear)

---

**Last Updated:** 2025-11-24
**Version:** 1.0
**Author:** BioDYM Development Team
