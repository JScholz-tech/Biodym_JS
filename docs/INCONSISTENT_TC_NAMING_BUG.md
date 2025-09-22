# Bug Report: Inconsistent Transfer Coefficient (TC) Naming Convention

**Date:** 2025-09-16

## 1. Symptoms

- Monte Carlo simulations run but produce no uncertainty in the results; output values are identical across all iterations.
- Scenario Manager changes to Transfer Coefficients have no effect on the model output.
- The Monte Carlo simulation produces warnings like: `WARNING: Could not parse process ID from TC_P5_out_1_material`.

## 2. Root Cause Analysis

The core of the problem is a fundamental disconnect in how TC parameters are named by the `data_loader.py` module versus how they are used by the `solver.py` module.

- **Data Loader & Configuration Modules (`data_loader`, `mc_simulation`, `system_setup`):** These modules correctly create and look for TC parameters based on the **`TC_ID`** explicitly defined by the user in the `2_3_Process_TCs` Excel sheet. This results in parameter names like `TC_P5_out_1_material`.

- **Solver (`solver.py`):** The solver module **ignores** the `TC_ID`. It dynamically invents the TC parameter names it needs by using the flow's start and end process IDs. For a flow named `F_05_06`, the solver looks for a parameter named `TC_05_06_material`.

Because the parameter name created (`TC_P5_out_1_material`) does not match the name the solver is looking for (`TC_05_06_material`), any changes made to the parameter by the Monte Carlo engine or the Scenario Manager are silently ignored by the solver during the calculation.

## 3. Proposed Solution

The current design is not viable because the information required to construct the solver's expected names (`TC_05_06_material`) is not available in the TC definition sheet. 

The only robust solution is to **refactor `solver.py`** to use the `TC_ID`-based parameter names (e.g., `TC_P5_out_1_material`). This will create a single, consistent naming convention across the entire tool, ensuring that the user's definitions in the Excel file are the single source of truth.

This will require modifying the `run_mfa_calculation` function to look up the correct `TC_ID` for each flow it processes, rather than inventing a name.
