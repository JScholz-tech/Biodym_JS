---
name: new-module
description: Routine for adding a new process model module to the BioDYM engine (like LFG or FOMP)
argument-hint: <module_name>
---

Follow this integration checklist to add a new engine module to BioDYM.
Module name: `$ARGUMENTS`

## Checklist

**Step 1 — Excel input sheet**
- Add a new sheet `3_X_Definition_<Module>` to the template `.xlsm`
- Define required columns: process ID, parameters, flags

**Step 2 — Data loader**
- Add `load_<module>_parameters(all_excel_data)` in `02_src/data_loader.py`
- Return a dict keyed by process ID, or `{}` if the sheet is absent/empty

**Step 3 — Config flag**
- Add `RUN_<MODULE>_CALCULATION` to the `1_1_Configuration` Excel sheet
- Read it via `getattr(config, 'RUN_<MODULE>_CALCULATION', True)` (safe default)

**Step 4 — Engine module**
- Create `02_src/engine/<module>_model.py`
- Implement `calculate_<module>(mfa_system, params_config)` → returns modified `mfa_system`
- Follow the FOMP/LFG pattern: extract inflows from `FlowDict`, run pure calculation function, assign results back to `FlowDict` and `StockDict`
- Write pool stocks to `StockDict[f"S_{process_id}"]` to satisfy `Consistency_Check()`
- Call `mfa_system.Consistency_Check()` at the end and print a warning (not exception) on failure

**Step 5 — Solver integration**
- Import the new module at the top of `02_src/engine/solver.py`
- Add the call inside `run_mfa_calculation()` at the appropriate point in the fixed-point loop
- Guard with the config flag: `if cfg.RUN_<MODULE>_CALCULATION and <module>_params:`

**Step 6 — Plotting**
- Add plot functions in `02_src/plotting/dynamics.py` (or a new sub-module)
- Export from `02_src/plotting/__init__.py`
- Add to workflow notebook section 3.x (conditional on params being non-empty)
- Add to dashboard Process Models tab (conditional)

**Step 7 — Tests / verification**
- Load the example `.xlsm` and confirm `load_<module>_parameters` returns expected dict
- Run the full solver and check `Consistency_Check` passes
- Verify plots render without errors
