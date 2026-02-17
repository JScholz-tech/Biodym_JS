# BioDYM Project: Coding Standards & Development Guide

## 1. Guiding Philosophy

This project adheres to a simple philosophy to ensure the creation of high-quality, maintainable scientific software:

1.  **Make it work:** First, ensure the logic is correct and produces the right results.
2.  **Make it right:** Refactor the working code to be clean, readable, and well-structured. This is the phase we are in now.
3.  **Make it fast:** Only optimize for performance after the code is correct and clean, and only if necessary.

Our goal is **Clarity, Consistency, and Simplicity**.

## 2. Naming Conventions

We follow Python's official **PEP 8** style guide.

-   **Modules/Files:** `lowercase_with_underscores.py` (e.g., `system_setup.py`)
-   **Functions & Variables:** `lowercase_with_underscores` (e.g., `run_mfa_calculation`)
-   **Classes:** `PascalCase` (e.g., `MfaSystem`)
-   **Constants:** `ALL_CAPS_WITH_UNDERSCORES` (e.g., `DEFAULT_ITERATIONS`)

### Naming Principles:

-   **Be Descriptive:** Names must be unambiguous. Avoid generic names like `df`, `data`, `temp`, or single letters. `flow_definitions_df` is always better than `df1`.
-   **Functions are Verbs, Variables are Nouns:**
    -   Functions describe an action: `calculate_balance()`, `load_data()`.
    -   Variables describe a thing: `process_name`, `mfa_results`.
-   **Single Responsibility:** A function's name should describe its single purpose. If the name contains "and", it should be split into multiple functions.

## 3. Documentation Standards

Documentation is mandatory for all code. We follow the **NumPy docstring format**.

### NumPy Docstring Template

Every function must have a docstring that follows this template.

```python
def function_name(param1, param2):
    """A brief, one-line summary of the function's purpose.

    A more detailed explanation of the function's logic, its place in the
    workflow, and any scientific assumptions it makes.

    Parameters
    ----------
    param1 : type
        Description of the first parameter.
    param2 : type, optional
        Description of the second parameter. Default is None.

    Returns
    -------
    return_type
        Description of the value returned by the function.

    Examples
    --------
    >>> function_name(1, 'example')
    'Some output'
    """
    # ... function code ...
    return
```

## 4. Code Quality & Linting

To ensure consistency and find common errors, we use **Ruff**.

-   To automatically format all files: `ruff format .`
-   To check for errors and style issues: `ruff check .`

All code should be formatted and checked before committing.

## 5. Refactoring & Documentation Workflow

To improve the codebase, we will follow a safe, iterative process for each file in the `02_src` directory.

1.  **Select & Refactor:** A single Python file is chosen for refactoring. Names are improved and NumPy-style docstrings are added according to the standards above.
2.  **Run & Verify:** The main `00_BioDYM_Workflow.ipynb` notebook is run from start to finish (`Kernel` -> `Restart & Run All`). This acts as our master integration test.
3.  **Commit:**
    -   If the notebook runs successfully, the changes to the refactored file are committed with a specific message (e.g., `docs(data_loader): add docstrings and refactor names`).
    -   If the notebook fails, the error is diagnosed and fixed before attempting to commit.

This cycle is repeated for each file, ensuring the project remains in a working state at all times.
