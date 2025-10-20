# Implementation Plan: Data Reconciliation Module

## 1. Objective

To implement a data reconciliation feature within the BioDYM MFA tool. This feature will improve the accuracy and consistency of the analysis by adjusting user-provided measurement data to ensure perfect adherence to mass balance constraints. The core of this feature will be a constrained optimization that minimizes the weighted, squared deviations from the original measurements.

## 2. Core Concepts

- **Least-Squares Optimization:** The engine will minimize the sum of squared errors between the initial measured values and the final reconciled values, weighted by the variance of each measurement.
- **Mass Balance Constraints:** The optimization will be constrained by the fundamental law of mass conservation (`Σin - Σout - dS = 0`), which must hold true for every process at every time step.
- **Uncertainty-Driven:** The process relies on user-defined uncertainties (standard deviations) for each measured flow. Flows with lower uncertainty will be adjusted less by the optimizer.
- **Overdetermined System:** The feature assumes the user provides enough measured data (including internal flows) to create a system with redundant information, which is the basis for reconciliation.

## 3. Proposed User Workflow

1.  **Enable Feature:** The user will enable data reconciliation by setting a new flag, `RUN_DATA_RECONCILIATION`, to `TRUE` in the `0_Config` sheet of the input Excel file.
2.  **Define Uncertainties:** The user will provide the necessary input data in the `4_1_Uncertainty_Parameters` sheet. For each flow they wish to include in the reconciliation, they will create a row specifying:
    - `Parameter_Name`: The ID of the flow (e.g., `F_1_2`).
    - `Distribution_Type`: `normal`.
    - `Mean`: The measured value of the flow.
    - `StdDev`: The standard deviation of the measurement, representing its uncertainty.
3.  **Run Notebook:** The user will run the `00_BioDYM_Workflow.ipynb` notebook as usual.
4.  **Analyze Results:** The system will produce a perfectly mass-balanced result. A new Excel file will be generated comparing the original measured values against the final reconciled values, showing the adjustments made.

## 4. Technical Implementation Plan

This feature will be developed in distinct phases:

### Phase 1: Foundation & Core Logic

- **Dependency:** Add the `SciPy` library to the `pyproject.toml` file to provide the necessary optimization solvers.
- **New Module:** Create a new file: `02_src/engine/reconciliation.py`.
- **Core Function:** Implement the main entry point: `run_reconciliation(mfa_system, uncertainty_params)`.
- **Objective Function:** Within the new module, create a function that calculates the least-squares objective `F = Σ Σ ( (x̃ᵢ,t - xᵢ,t)² / var(x̃ᵢ,t) )` across all flows and time steps.
- **Constraint Generation:** Implement a function that automatically generates the mass balance constraint equations for all non-special (TC-driven, Pass-through) processes across all time steps.
- **Initial Test:** The initial implementation will target systems *without* DSM or FOMP processes to validate the core optimization logic.

### Phase 2: Workflow Integration & Validation Output

- **Modify Workflow:** Edit `00_BioDYM_Workflow.py` to include the logic for selecting the calculation engine. Based on the `RUN_DATA_RECONCILIATION` flag, the workflow will call either the existing `solver.run_mfa_calculation` or the new `reconciliation.run_reconciliation`.
- **Validation Report:** Create a new function within `reconciliation.py` that generates an Excel report comparing `measured_value`, `reconciled_value`, `adjustment`, and `standard_deviation` for each reconciled flow. This is critical for user trust and transparency.

### Phase 3: Handling Special Processes (DSM & FOMP)

- **Iterative Reconciliation:** Refactor `run_reconciliation` to handle the complex, stateful nature of DSM and FOMP processes. This will be achieved with an iterative loop:
    1.  **Reconcile Simple System:** Run the optimizer on the linear parts of the system, treating DSM/FOMP outflows as temporarily fixed.
    2.  **Update Special Processes:** Use the newly reconciled flows as inputs to the standard `dsm_model.py` and `fomp_model.py` modules to calculate updated outflows.
    3.  **Check Convergence:** Compare the new DSM/FOMP outflows with the previous iteration's values. If they have converged, the process is complete. If not, repeat from step 1.

### Phase 4: Scenario Manager Integration

- **Verify Data Flow:** Confirm that the execution order in `00_BioDYM_Workflow.py` correctly applies scenario modifications to the baseline data *before* the reconciliation engine is called. This ensures that scenarios can be used to test the sensitivity of the reconciled solution to changes in input measurements and uncertainties.

## 5. Impact on Existing Code

- **New Files:**
    - `02_src/engine/reconciliation.py`
    - `IMPLEMENTATION_PLAN_DATA_RECONCILIATION.md`
- **Modified Files:**
    - `pyproject.toml` (to add `SciPy`).
    - `00_BioDYM_Workflow.py` (to add the `if/else` logic for engine selection).
- **No Impact:** The existing `solver.py`, `dsm_model.py`, `fomp_model.py`, and all `plotting` and `reporting` modules will not be directly modified. They will simply consume the reconciled `mfa_system` object, ensuring full compatibility.

## 6. Definition of Done

- A user can successfully enable and run a data reconciliation analysis via the Excel configuration.
- The feature produces a fully mass-balanced `mfa_system` object that can be used by all downstream plotting and KPI functions.
- The reconciliation correctly handles systems containing complex DSM and FOMP processes.
- A validation report is generated, allowing the user to inspect the adjustments made by the optimizer.
