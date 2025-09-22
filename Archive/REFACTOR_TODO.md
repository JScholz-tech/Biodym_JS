### Refactoring To-Do List for Circular Flow Solver

1.  **Establish a Clean Baseline:**
    *   Create this `REFACTOR_TODO.md` file.
    *   Revert any temporary changes made to the notebook during our debugging session.
    *   Remove the temporary `read_excel_data.py` script.
    *   Commit this plan to establish a clean starting point for the refactor.

2.  **Update Data Structures (Excel):**
    *   Add the new `Process_Logic` column to the `2_1_Definition_Processes` sheet in the main Excel template (`BioDYM_MFA_Input_Template.xlsx`).
    *   Add the new substance-specific TC columns (`TC_Value_material`, `TC_Value_WC`, etc.) to the `2_3_Process_TCs` sheet in the template.

3.  **Update Data Loader (`data_loader.py`):**
    *   Modify the data loading functions to read the new columns.
    *   Implement the logic to create substance-specific TC parameters in the `ParameterDict` based on the `Process_Logic` flag (`Splitter` vs. `Transformer`).

4.  **Refactor the Solver Engine (`solver.py`):**
    *   Overhaul the main TC processing loop in `run_mfa_calculation`.
    *   Remove the old logic for calculating mass and composition separately.
    *   Implement the new vector-based calculation that operates on all substances simultaneously.

5.  **Testing and Validation:**
    *   Update the user's `250915_CS2_Wood_V3.xlsx` file to match the new format.
    *   Run the notebook and verify that the circular flow is now calculated correctly.
    *   (Optional) Create a new unit test for the solver to validate the circular calculation logic.
