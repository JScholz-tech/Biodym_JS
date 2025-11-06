# BioDYM Troubleshooting Guide

Common issues and their solutions when working with BioDYM.

## Table of Contents

- [ODYM Integration Issues](#odym-integration-issues)
- [Mass Balance Errors](#mass-balance-errors)
- [Solver Issues](#solver-issues)
- [Process-Specific Issues](#process-specific-issues)
- [Visualization Issues](#visualization-issues)
- [Data Loading Issues](#data-loading-issues)
- [General Debugging Strategy](#general-debugging-strategy)

## ODYM Integration Issues

### Issue: `AttributeError: 'NoneType' object has no attribute 'split'`

**Cause**: Parameter created with `Indices=None` instead of `Indices=""`.

**Location**: Happens in `Initialize_ParameterValues()` at ODYM line 231.

**Solution**:
```python
# ❌ WRONG - Will crash with AttributeError
param = msc.Parameter(Name="TC_1", Values=0.5, Indices=None)

# ✅ CORRECT - Use empty string for scalars
param = msc.Parameter(Name="TC_1", Values=0.5, Indices="")

# ✅ CORRECT - Time-varying parameter
param = msc.Parameter(Name="TC_2", Values=array, Indices="t")
```

**Finding Culprits**: Search for `Indices=None` in `02_src/`:
```bash
grep -r "Indices=None" 02_src/
```

## Mass Balance Errors

### Issue: Mass Balance Errors / Inconsistent Results

**Symptoms**:
- Large errors in mass balance plots
- `Consistency_Check()` warnings
- Unexpected stock levels

**Common Causes**:

1. **Missing TC definitions**: Flow has no corresponding TC in Excel
   - Check `flow_tc_map` for missing flows
   - Verify `2_2_static_TCs` or `2_3_dynamic_TCs` sheets

2. **Incorrect Process_Logic**: Process type doesn't match its actual role
   - Verify `Process_Logic` column in `2_1_Definition_Processes`
   - Common mistake: DSM process marked as "Splitter"

3. **Initial stock issues**: Initial stock doesn't match first-year balance
   - Check `2_5_Initial_Stock` values
   - Verify stock-outflow TCs aren't depleting too fast

4. **Element composition errors**: WC% + DM% ≠ 100%
   - Check `Flow_WC[%]` and `Flow_DM[%]` columns
   - Water + Dry Matter should sum to ~1.0 (100%)

**Debugging Steps**:
```python
# 1. Check specific process balance
process_id = 5
inflows = [f for f in mfa_system.FlowDict.values() if f.P_End == process_id]
outflows = [f for f in mfa_system.FlowDict.values() if f.P_Start == process_id]
print(f"Inflows: {sum(f.Values[:, 0].sum() for f in inflows)}")
print(f"Outflows: {sum(f.Values[:, 0].sum() for f in outflows)}")

# 2. Check stock levels
if f"S_{process_id}" in mfa_system.StockDict:
    print(f"Stock: {mfa_system.StockDict[f'S_{process_id}'].Values[:, 0]}")

# 3. Run consistency check
try:
    mfa_system.Consistency_Check()
except Exception as e:
    print(f"Consistency error: {e}")
```

## Solver Issues

### Issue: Solver Not Converging

**Symptoms**: Warning "System did not converge after 30 iterations"

**Common Causes**:

1. **Circular dependencies**: Process A depends on B, B depends on C, C depends on A
   - Review process connections in Excel
   - Check for feedback loops

2. **Transfer coefficient > 1.0**: TC values should be ≤ 1.0 (fractions)
   - Check `TC_Value_material` columns
   - Common mistake: Using percentages instead of decimals (50 instead of 0.50)

3. **Dynamic TC oscillation**: Time-varying TCs causing instability
   - Review `2_3_dynamic_TCs` for abrupt changes
   - Consider smoothing TC transitions

**Debugging**:
- Add iteration counter: solver prints "[DSM DEBUG] Iteration X"
- Check which flows are still changing at iteration 30
- Increase `max_iterations` temporarily to see if it eventually converges

## Process-Specific Issues

### Issue: DSM Process Not Calculating

**Symptoms**: DSM process has zero outflows despite having inflows

**Common Causes**:

1. **Missing DSM definition**: Process_ID not in `3_1_Definition_DSM`
2. **Incorrect lifetime parameters**: Mean/StdDev values unrealistic
3. **Missing inflow**: enhanced_input_validation() returns False

**Debugging**:
```python
# Check DSM parameters
print(f"DSM Params: {dsm_params}")
print(f"Process {process_id} in DSM params: {process_id in dsm_params}")

# Check inflows
inflows = [f for f in mfa_system.FlowDict.values() if f.P_End == process_id]
print(f"Inflows to DSM {process_id}: {[f.Name for f in inflows]}")
print(f"Total inflow sum: {sum(np.sum(f.Values) for f in inflows)}")
```

**Solution**: Verify `3_1_Definition_DSM` has entries for the process and lifetimes are reasonable (> 0).

### Issue: FOMP Process Missing Carbon Outflow

**Symptoms**: FOMP process has stock but no CO2 emissions

**Common Causes**:

1. **Missing FOMP outflow flow definitions**: Need flows for both carbon and environmental outputs
2. **Zero decay rates**: k_labile or k_recalcitrant = 0
3. **Missing `_fomp_protected` attribute**: Outflow flows not marked as FOMP-protected

**Solution**:
- Verify 2 outflow flows exist for FOMP process (one for CO2, one for environment)
- Check `3_2_Definition_FOMP` for decay rate parameters
- Verify flows have `_fomp_protected` attribute set in `fomp_model.py`

## Visualization Issues

### Issue: Plotting Errors / Visualization Failures

**Common Causes**:

1. **Missing process/flow names**: Descriptive names not in Excel
2. **Graphviz limits exceeded**: Too many processes/flows for visualization
3. **Empty data**: Trying to plot processes with no activity

**Solutions**:
- Check `_flow_descriptions` dict exists: `mfa_system._flow_descriptions`
- Increase Graphviz limits in `02_src/plotting/graphviz_flow_charts.py` (currently 50 processes, 100 flows)
- Filter out zero-flow processes before plotting

## Data Loading Issues

### Issue: Excel File Changes Not Reflected

**Symptom**: Modified Excel values but results unchanged

**Common Causes**:

1. **Excel file cache**: Jupyter kernel holding old data in memory
2. **Wrong file path**: Loading old file instead of modified one
3. **Cached .pyc files**: Python bytecode not updated

**Solutions**:
```python
# 1. Restart Jupyter kernel
# Kernel → Restart & Run All

# 2. Verify file path
print(f"Loading: {input_file}")
print(f"File exists: {os.path.exists(input_file)}")
print(f"Last modified: {os.path.getmtime(input_file)}")

# 3. Clear Python cache
import sys
if '02_src' in sys.modules:
    del sys.modules['02_src']
```

### Issue: Monte Carlo Simulation Fails

**Common Causes**:

1. **Missing uncertainty definitions**: No entries in `4_1_Uncertainty_Parameters`
2. **Invalid distribution parameters**: StdDev < 0 or inappropriate ranges
3. **Memory issues**: Too many iterations for large systems

**Solutions**:
- Check `4_1_Uncertainty_Parameters` sheet exists and has valid entries
- Verify distribution parameters (Mean, StdDev, Min, Max) are reasonable
- Reduce MC iterations in configuration (e.g., 1000 → 100 for testing)

## General Debugging Strategy

1. **Start Simple**: Run baseline calculation first (no MC, no scenarios)
2. **Check Logs**: Read print statements carefully - they contain diagnostic info
3. **Verify Data**: Use `pd.read_excel()` to inspect Excel sheets directly
4. **Isolate Issues**: Comment out DSM/FOMP to isolate TC-driven flow problems
5. **Use Master Test**: `00_BioDYM_Workflow.ipynb` must run successfully
6. **Check Units**: All mass units should be consistent (typically Mg)

## When to Ask for Help

If you've tried the above and still have issues, provide:
1. Full error traceback
2. Excel file structure (sheet names, key columns)
3. Process IDs and flow IDs involved
4. Configuration settings (time range, elements, enabled features)
5. Steps to reproduce

---

**Last Updated**: 2025-11-04
