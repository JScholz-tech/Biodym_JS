# Implementation Plan: Data Reconciliation Module (Revised)

## 1. Objective

To implement a statistically robust data reconciliation feature to improve the accuracy and consistency of the MFA results. The engine will solve a constrained, weighted least-squares optimization problem to adjust measured data, ensuring adherence to mass balance while providing comprehensive diagnostics for model validation and gross error detection.

## 2. Core Concepts & Formulation

- **Formulation:** The problem will be formulated as a Quadratic Program (QP). Let **z** be the vector of measured flow values, **x** be the vector of reconciled values, and **Σ** be the covariance matrix of the measurements (diagonal by default, allowing for independent errors). The objective is to **Minimize (x - z)ᵀΣ⁻¹(x - z)**.
- **Constraints:** The optimization will be subject to:
    1.  **Mass Balance:** `Cx = 0`, where C is the matrix defining the mass balance equations (`Σin - Σout - dS = 0`) for each process at each time step.
    2.  **Bounds:** `l ≤ x ≤ u`, including a non-negativity constraint (`x ≥ 0`) on all flows.
- **Uncertainty Model:** The system will support uncertainties defined as standard deviations in the `4_1_Uncertainty_Parameters` sheet. It will handle percentage-based inputs, converting them to absolute variance. Zero-variance inputs will be treated as fixed values (not decision variables). The plan includes optional support for block-covariance to model correlated errors.

## 3. Proposed User Workflow

1.  **Enable Feature:** Set `RUN_DATA_RECONCILIATION = TRUE` in the `0_Config` sheet.
2.  **Define Data & Uncertainties:** Provide measured values and their corresponding uncertainties (as standard deviations or percentages) in the appropriate Excel sheets (`1_2_Data_Flows`, `4_1_Uncertainty_Parameters`).
3.  **Run Workflow:** Execute the `00_BioDYM_Workflow.ipynb` notebook.
4.  **Analyze Results:** The primary output will be a reconciled `mfa_system` object. A detailed report will be generated, including statistical diagnostics and a comparison of measured vs. reconciled values.

## 4. Technical Implementation Plan (Revised & Phased)

### Phase 1: Foundational Solver & Diagnostics

- **Dependencies:** Add `SciPy` and `OSQP` (or a similar sparse QP solver) to `pyproject.toml`.
- **New Module:** Create `02_src/engine/reconciliation.py`.
- **Solver Implementation:**
    - Implement a solver function that uses a sparse QP solver (e.g., OSQP) to handle the QP formulation with bounds and equality constraints.
    - Exploit the block-diagonal structure of the problem over time for performance.
    - Implement numerical scaling of variables and constraints to improve solver stability.
- **Initial Diagnostics:** Implement core statistical diagnostics:
    - **Chi-Square Test:** To assess the overall goodness-of-fit of the reconciled solution.
    - **Standardized Residuals:** To help identify potential gross errors (outliers) in the input data.
- **Scope:** The initial implementation will focus on systems with only linear, non-special processes.

### Phase 2: Advanced Reporting & Workflow Integration

- **Gross Error Detection:** Implement a workflow to automatically flag measurements where `|standardized residual| > threshold` (e.g., 3.0), suggesting they may be gross errors.
- **Enhanced Reporting:** Expand the reconciliation report to include:
    - **Summary:** Chi-square test result, number of flagged gross errors, degrees of freedom (DOF).
    - **Detailed View:** For each measurement: initial value, reconciled value, adjustment, std. dev., standardized residual, and uncertainty reduction.
    - **Node-Level View:** Before/after mass balance gaps for each process.
- **Workflow Integration:**
    - Modify `00_BioDYM_Workflow.py` to select between the `solver` and `reconciliation` engines.
    - Attach reconciliation metadata (diagnostics, convergence status) to the `mfa_system` object for provenance and use by downstream functions.
    - Add strict input validation for all reconciliation-related data.

### Phase 3: Handling Special Processes (DSM & FOMP)

- **Iterative Coupling:** Implement a fixed-point iteration loop to handle the non-linear DSM and FOMP models:
    1.  Reconcile the simple, linear parts of the system, keeping DSM/FOMP flows fixed.
    2.  Use the new reconciled flows as inputs to run the standard DSM/FOMP models, generating updated outflows.
    3.  Check for convergence using the maximum relative change in DSM/FOMP outflows.
    4.  **Safeguards:** Implement damping/relaxation (`x_new = α*x_calc + (1-α)*x_old`) to prevent oscillation, a max iteration limit, and clear reporting on non-convergence.
- **Variable Handling:** Clarify that stock changes (`dS`) for DSM/FOMP processes are calculated by their respective models, not treated as independent variables in the reconciliation.

### Phase 4: ODYM Compatibility & Finalization

- **Testing Strategy:** Implement a comprehensive testing suite:
    - Unit tests on synthetic networks with known analytical solutions.
    - Tests for gross error detection, bounds, and covariance support.
    - Integration tests for the iterative DSM/FOMP coupling.
- **ODYM Integration:** Ensure all data structures (indices, axes) are aligned with ODYM conventions. Provide a utility to export reconciled results into ODYM-compatible containers.
- **Provenance:** Record all reconciliation settings (solver choice, tolerances, weights) as attributes in the final `mfa_system` object.

## 5. Gross Error Detection Strategy

A key feature will be the ability to detect and handle gross errors (outliers). The proposed workflow is:

1.  **Run Reconciliation:** Perform an initial run.
2.  **Flag Outliers:** Automatically identify and flag all measurements with a high standardized residual (e.g., > 3.0).
3.  **Report:** Clearly list the flagged outliers in the summary report.
4.  **Optional: Reweight & Rerun:** Provide an option to automatically re-run the reconciliation after down-weighting (increasing the variance of) or excluding the flagged outliers, and document these actions in an audit trail.