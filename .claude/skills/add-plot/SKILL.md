---
name: add-plot
description: Checklist routine for adding a new plot function to BioDYM
argument-hint: <plot_function_name> [module]
---

Follow this checklist to add a new plot function to BioDYM. The function name
(and optionally, the target plotting module) is given as `$ARGUMENTS`.

## Checklist

**Step 1 — Write the function**
- Determine the right module in `02_src/plotting/` (e.g. `dynamics.py` for time-series, `validation.py` for mass balance, `sankey.py` for flow diagrams)
- Use Plotly (`go.Figure`) and call `fig.show()` at the end — do NOT return the figure
- Accept `mfa_results` (the solver 3-tuple's first element) as the first argument
- Follow the existing function signature style in the target module

**Step 2 — Export from `__init__.py`**
- Add an import line in `02_src/plotting/__init__.py`
- Add the function name to `__all__`
- Exception: `plot_flow_composition` lives in `plotting.composition` and is intentionally NOT in `__init__`

**Step 3 — Add to the Voilà dashboard**
- Open `01_BioDYM_Dashboard.py`
- Place the call in the correct tab section inside `_build_dashboard()`
- Wrap in `try/except` like all other plot calls
- Run `/sync-notebook 01_BioDYM_Dashboard.py`

**Step 4 — Add to the main workflow notebook**
- Open `00_BioDYM_Workflow.py`
- Place the call in the matching section (3.x Visualization)
- Run `/sync-notebook 00_BioDYM_Workflow.py`

**Step 5 — Verify**
- Confirm the function is callable via `plotting.<function_name>(mfa_results, ...)`
- Check for `plot_flow_composition`-style exceptions (direct module import needed)
