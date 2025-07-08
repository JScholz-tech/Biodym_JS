# Gemini Project Briefing: BioDYM MFA Tool

## A. Project Foundation & High-Level Goals

1.  **Primary Purpose:** To provide a robust, extensible, and scientifically sound Material Flow Analysis (MFA) tool—based on the ODYM framework—for modeling, analyzing, and visualizing multi-dimensional material flows and stocks in complex systems, with support for dynamic stock modeling (DSM), FOMP, and Monte Carlo analysis.
2.  **Intended End-Users:** Researchers and analysts in environmental science and resource management who need to model, validate, and visualize material flows (carbon, water, etc.) in systems like agriculture or waste management.
3.  **Top Critical Features:**
    *   Accurate, multi-dimensional MFA calculations.
    *   Dynamic Stock Modeling (DSM) and FOMP support.
    *   Robust input validation and regression testing.
    *   Publication-ready visualizations (Sankey diagrams, etc.).
    *   Scenario management and Monte Carlo simulation.
4.  **Explicit Non-Goals:**
    *   Not a general-purpose process simulator (e.g., no chemical reaction modeling).
    *   Local/desktop use only; no web interface or cloud deployment.
    *   Data input via Excel/CSV only; no direct database integration.
    *   No support for non-MFA modeling paradigms (e.g., LCA, SFA).
5.  **Success in 3 Months:**
    *   Core MFA, DSM, and FOMP features are regression-tested and validated.
    *   90%+ test coverage on calculation logic.
    *   Visualizations are publication-ready and reproducible.
    *   A clean, maintainable codebase with clear documentation.

## B. Development Environment & Setup

6.  **Python Version:** Python 3.12.x
7.  **Dependency Manager:** pip
8.  **Install Dependencies:**
    *   **NOTE:** This is a temporary setup. The two requirement files will be consolidated into one in the future.
    *   `pip install -r requirements.txt`
    *   `pip install -r framework/ODYM-master_20241127/Requirements.txt`
9.  **Environment Variables:** None required.
10. **External Services:** None required.

## C. Codebase Architecture & Conventions

11. **Primary Architectural Pattern:** Layered architecture (Data -> Model -> Engine -> Visualization).
12. **Main Directory Responsibilities (`src/`):**
    *   `src/engine/`: Core calculation logic (DSM, FOMP, solver).
    *   `src/`: High-level orchestration (main CLI, data loading, plotting, system setup).
13. **Naming Conventions:**
    *   Files & Variables: `snake_case`
    *   Classes: `PascalCase`
    *   Test Files: `test_*.py`
14. **Formatter & Linter (Strict Policy):**
    *   This project uses **Ruff** for all formatting and linting. All code **MUST** be formatted and pass checks before commit.
    *   **To format all files:** `ruff format .`
    *   **To check for linting errors:** `ruff check .`
15. **Error & Exception Handling:**
    *   Use standard `try/except` blocks.
    *   Raise `ValueError` with clear messages for input validation errors.
16. **Logging Convention:**
    *   Use Python's built-in `logging` module instead of `print()`. A basic configuration in the main entry point is sufficient. This allows for different log levels (e.g., INFO, DEBUG, ERROR).
17. **Docstring Style (Strict Policy):**
    *   All functions and classes **MUST** be documented using the **NumPy docstring style** to ensure clarity for the scientific community.
    *   **Example:**
        ```python
        def my_function(param1, param2):
            """A brief summary of the function.

            A more detailed explanation of what the function does and its
            purpose.

            Parameters
            ----------
            param1 : int
                Description of the first parameter.
            param2 : str
                Description of the second parameter.

            Returns
            -------
            bool
                Description of the return value.
            """
            # function code here
            pass
        ```

## D. Testing & Quality Assurance

18. **Testing Framework:** pytest
19. **Run Entire Test Suite:** `pytest`
20. **Run Single Test File:** `pytest path/to/test_file.py`
21. **Test File Location:** All new tests go in the `test/` directory.
22. **Test Coverage:**
    *   Target: 90%+ for calculation logic in `src/`.
    *   To measure: `pytest --cov=src`

## E. My Role & Interaction Protocol

23. **Autonomy:** Proceed with best judgment for routine changes and bugfixes. Ask for confirmation before major refactors or changes to core calculation logic.
24. **Commit Message Format (Strict Requirement):**
    *   All commits **MUST** follow the **Conventional Commits** standard.
    *   **Example:**
        ```
        feat(dsm): add support for fixed lifetime in DSM parameter sheet

        - DSM now accepts 'Fixed' as a lifetime type for deterministic modeling.
        - Updated golden dataset and test logic to match.
        ```
25. **Final Output:** Summarize changes in chat and commit them locally.
26. **Handle with Care:**
    *   Do not modify `framework/ODYM-master_YYYYMMDD/`.
    *   Be careful with `test_data/golden_dataset.xlsx`.
    *   Do not overwrite user data in `data/`.
