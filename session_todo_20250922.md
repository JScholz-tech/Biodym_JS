# To-Do List: BioDYM Polishing Session - 2025-09-22

**Goal:** Prepare the codebase for sharing with a researcher. The focus is on correctness, understandability, and structure.

---

## Session Summary (2025-09-22)

Today, we made significant progress on core functionality and debugging. Key achievements include:

*   **Critical TC Naming Bug:** Successfully fixed the fundamental inconsistency in Transfer Coefficient (TC) naming across `data_loader.py`, `system_setup.py`, `BioDYM_Scientific_Notebook.py`, `solver.py`, and `mc_simulation.py`. This involved:
    *   Implementing a new, robust TC naming convention (`TC_<P_Start>_<P_End>_<Element>`).
    *   Ensuring correct loading of TCs from Excel, including handling decimal separators and case-insensitive flags.
    *   Implementing distinct calculation logic for 'Splitter' and 'Transformer' processes in the solver.
    *   Refactoring the Monte Carlo (MC) simulation to correctly sample and propagate uncertainty for the new TC structure.
    *   Resolving several import errors and scope issues that arose during debugging.
*   **MC Plotting:** The Monte Carlo visualization functions (`mc_visuals.py`) were updated to correctly interpret the new MC results DataFrame, and plots are now displaying correctly with element dropdowns.

---

### Phase 1: Core Functionality & Structure (Highest Priority)
1.  ~~**Fix Critical TC Naming Bug:**~~ **COMPLETED**
2.  **Restructure Project Directory:** Move the core tool files from the `biodym_mfa_tool` sub-folder to a more logical top-level structure. This will improve the project's layout and clarity.
    *   **Status:** IN PROGRESS. Files have been manually moved. Currently addressing Git staging issues.

### Phase 2: Cleanup & Refinement
3.  **Review and Remove Old Code:** Systematically scan the codebase for and remove any commented-out or obsolete code fragments left over from previous development sessions.
    *   **Status:** NOT STARTED.
4.  **Integrate Excel Configuration:** Ensure the model is fully driven by the `0_Configuration` sheet, removing remaining hardcoded parameters.
    *   **Status:** NOT STARTED.
5.  ~~**Fix Visualization Issue:**~~ **COMPLETED** (MC plots are working, but other visualization issues may exist).

### Phase 3: Validation & Final Polish
6.  **Run Full Test Suite:** After all changes are made, execute the entire test suite to guarantee stability and catch any regressions.
    *   **Status:** PARTIALLY COMPLETED. `test_data_loader.py` fixed. Other failures (`test_golden_dataset.py`, `test_enhanced_sankey_positions.py`, `test_utils.py`, `test_system_setup.py`, `test/workflow/1_setup/test_setup.py`) are still present and were put on hold during debugging.
7.  **Update Documentation & Excel:** Perform a final polish on the `README.md`, key documentation files, and the example Excel template.
    *   **Status:** NOT STARTED.