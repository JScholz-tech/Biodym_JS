# Quick Start: Extending BioDYM for Metals

## Minimal Viable Changes (1-2 hours)

### Step 1: Update Configuration (5 min)

In `00_BioDYM_Workflow.py` or `.ipynb`, change:

```python
# OLD (biomass)
elements = ['material', 'WC', 'DM', 'CC']

# NEW (metals - test with 3 elements first)
elements = ['material', 'Fe', 'Cu', 'Al']
```

### Step 2: Update Excel Template (30 min)

In `01_data/01_input/your_file.xlsx`:

**Sheet: 1_1_Definition_Flows**
- Rename column: `Flow_WC[%]` → `Flow_Fe[%]`
- Rename column: `Flow_DM[%]` → `Flow_Cu[%]`
- Rename column: `Flow_CC_DM[%]` → `Flow_Al[%]`

Example values for metal recycling:
```
Flow_ID  | Flow_Fe[%] | Flow_Cu[%] | Flow_Al[%]
---------|------------|------------|----------
F_01_02  |    0.70    |    0.15    |    0.10
F_02_03  |    0.95    |    0.03    |    0.00
```

### Step 3: Update Composition Calculation (15 min)

In `02_src/system_setup.py`, line ~407, change:

```python
# OLD
column_map = {
    "WC": "Flow_WC[%]",
    "DM": "Flow_DM[%]",
    "CC": "Flow_CC_DM[%]"
}

# NEW
column_map = {
    "Fe": "Flow_Fe[%]",
    "Cu": "Flow_Cu[%]",
    "Al": "Flow_Al[%]"
}
```

### Step 4: Update Solver Element References (30 min)

In `02_src/engine/solver.py`:

**Line ~191-195** (in `_calculate_tc_driven_flows`):
```python
# OLD
mat_idx = mfa_system.Elements.index('material')
wc_idx = mfa_system.Elements.index('WC')
dm_idx = mfa_system.Elements.index('DM')
cc_idx = mfa_system.Elements.index('CC')

# NEW
mat_idx = mfa_system.Elements.index('material')
fe_idx = mfa_system.Elements.index('Fe')
cu_idx = mfa_system.Elements.index('Cu')
al_idx = mfa_system.Elements.index('Al')
```

**Line ~206-210** (Splitter logic):
```python
# OLD
wc_fraction = np.divide(total_inflow_vector[:, wc_idx], ...)
dm_fraction = np.divide(total_inflow_vector[:, dm_idx], ...)
cc_fraction = np.divide(total_inflow_vector[:, cc_idx], ...)

outflow_vector[:, wc_idx] = outflow_vector[:, mat_idx] * wc_fraction
outflow_vector[:, dm_idx] = outflow_vector[:, mat_idx] * dm_fraction
outflow_vector[:, cc_idx] = outflow_vector[:, mat_idx] * cc_fraction

# NEW
fe_fraction = np.divide(total_inflow_vector[:, fe_idx], ...)
cu_fraction = np.divide(total_inflow_vector[:, cu_idx], ...)
al_fraction = np.divide(total_inflow_vector[:, al_idx], ...)

outflow_vector[:, fe_idx] = outflow_vector[:, mat_idx] * fe_fraction
outflow_vector[:, cu_idx] = outflow_vector[:, mat_idx] * cu_fraction
outflow_vector[:, al_idx] = outflow_vector[:, mat_idx] * al_fraction
```

**Line ~212-217** (Transformer logic):
```python
# OLD
for i_elem, element in [(wc_idx, 'WC'), (dm_idx, 'DM'), (cc_idx, 'CC')]:
    ...

# NEW
for i_elem, element in [(fe_idx, 'Fe'), (cu_idx, 'Cu'), (al_idx, 'Al')]:
    ...
```

### Step 5: Disable FOMP (5 min)

In `0_Configuration` sheet:
```
RUN_FOMP_CALCULATION = FALSE
```

Or comment out FOMP in workflow:
```python
# config.RUN_FOMP_CALCULATION = False  # Metals don't decay organically
```

### Step 6: Test Run! (10 min)

Run `00_BioDYM_Workflow.ipynb` and check:
- [ ] System initializes with 3 elements
- [ ] Flows have shape (T, 4) where 4 = material + Fe + Cu + Al
- [ ] Mass balance holds (Fe + Cu + Al ≤ material)
- [ ] Visualizations show metal elements

## Example Metal System

Simple recycling system:

```
Collection (P1) → Sorting (P2) → Smelting (P3) → Products (P4)

Initial composition:
- Fe: 70%
- Cu: 15%
- Al: 10%
- Other: 5%

After sorting:
- Fe-rich stream: 95% Fe
- Cu-rich stream: 90% Cu
- Al-rich stream: 85% Al
```

## Expected Issues & Fixes

### Issue 1: FOMP Model Crashes
**Error**: `KeyError: 'DM'` or `KeyError: 'CC'`

**Fix**: Disable FOMP or update lines 308-311 in `solver.py`:
```python
# Add try/except for FOMP
if config.RUN_FOMP_CALCULATION:
    try:
        dm_idx = mfa_system.Elements.index('DM')
        cc_idx = mfa_system.Elements.index('CC')
    except ValueError:
        print("⚠️ Skipping FOMP: Requires 'DM' and 'CC' elements (not available for metals)")
        config.RUN_FOMP_CALCULATION = False
```

### Issue 2: Composition > 100%
**Error**: Metal fractions sum to > 1.0

**Fix**: Ensure fractions in Excel sum to ≤ 1.0:
```python
# In system_setup.py, add validation:
total_frac = fe_frac + cu_frac + al_frac
if total_frac > 1.0:
    raise ValueError(f"Metal fractions sum to {total_frac:.2f} > 1.0 for flow {flow_id}")
```

### Issue 3: Visualization Labels Wrong
**Error**: Plots show "WC", "DM" labels

**Fix**: Update in plotting modules or add to config:
```python
ELEMENT_LABELS = {
    'material': 'Total Material',
    'Fe': 'Iron (Fe)',
    'Cu': 'Copper (Cu)',
    'Al': 'Aluminum (Al)'
}
```

## Next Steps After Quick Start

Once this works:
1. Generalize solver code (remove hardcoded element names)
2. Create proper metal template Excel file
3. Add metal-specific validation rules
4. Update documentation

## Estimated Time
- **Minimal changes**: 1-2 hours
- **Full generalization**: 3-5 days
- **Production template**: +2-3 days

Total: **~1 week** for complete metal extension
