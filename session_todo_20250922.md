# To-Do List: BioDYM Polishing Session - 2025-09-22

**Goal:** Prepare the codebase for sharing with a researcher. The focus is on correctness, understandability, and structure.

---

### Phase 1: Core Functionality & Structure (Highest Priority)
1.  **Fix Critical TC Naming Bug:** Correct the solver's calculation logic to ensure Monte Carlo and Scenario features work as intended. This is essential for the tool's scientific validity.
2.  **Restructure Project Directory:** Move the core tool files from the `biodym_mfa_tool` sub-folder to a more logical top-level structure. This will improve the project's layout and clarity.

### Phase 2: Cleanup & Refinement
3.  **Review and Remove Old Code:** Systematically scan the codebase for and remove any commented-out or obsolete code fragments left over from previous development sessions.
4.  **Integrate Excel Configuration:** Ensure the model is fully driven by the `0_Configuration` sheet, removing remaining hardcoded parameters.
5.  **Fix Visualization Issue:** Address the specific visualization bug you have on your list.

### Phase 3: Validation & Final Polish
6.  **Run Full Test Suite:** After all changes are made, execute the entire test suite to guarantee stability and catch any regressions.
7.  **Update Documentation & Excel:** Perform a final polish on the `README.md`, key documentation files, and the example Excel template.
