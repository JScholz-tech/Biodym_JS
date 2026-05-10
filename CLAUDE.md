# BioDYM — Claude Code Project Instructions

## Commands
- **Run anything**: always prefix with `uv run` (e.g. `uv run python`, `uv run jupyter`)
- **Sync notebook**: `uv run jupytext --to notebook <file>.py`
- **Launch dashboard (Marimo)**: `uv run marimo run 01_BioDYM_Dashboard.py`
- **Edit dashboard interactively**: `uv run marimo edit 01_BioDYM_Dashboard.py`
- **Launch dashboard (legacy Voilà)**: `uv run voila 01_BioDYM_Dashboard.ipynb`
- **Execute notebook**: `uv run jupyter nbconvert --to notebook --execute <file>.ipynb`
- **Run explorer tools**: `uv run marimo run tools/buf_explorer.py` (or `cuf_explorer.py`)

## Notebook workflow (Jupytext)
- The `.py` file is the **source of truth** — always edit `.py`, never `.ipynb` directly
- Light format (not percent): section markers are `# +` / `# -`, not `# %%`
- **After every edit to a `.py` notebook**, sync it: `uv run jupytext --to notebook <file>.py`
- After editing any module in `02_src/`, the Jupyter kernel must be restarted for changes to take effect — `%autoreload` is NOT configured
- Notebooks: `00_BioDYM_Workflow.py` (main analysis), `01_BioDYM_Dashboard.py` (Marimo dashboard)
- **IMPORTANT**: `01_BioDYM_Dashboard.py` uses `@app.cell` decorators (Marimo format) — it is NOT a Jupytext file. Do NOT run `jupytext` on it.

## Project structure
```
tools/
  buf_explorer.py      — Marimo: BUF (Biomass Utilisation Factor) interactive calculator
  cuf_explorer.py      — Marimo: CUF (Carbon Utilisation Factor) interactive calculator
02_src/
  config.py            — load_configuration() + extract_workflow_dimensions()
  data_loader.py       — load_*_parameters() functions
  system_setup.py      — define_model_scope / initialize_mfa_system / load_and_define_processes / define_flows_and_parameters
  analysis/
    cuf.py             — CUF (Carbon Utilization Factor) post-processing
  engine/
    solver.py          — run_mfa_calculation() → (mfa_system, dsm_details, solver_info)
    fomp_model.py      — two-pool first-order decay (labile / recalcitrant)
    lfg_model.py       — N-pool FOD, UNFCCC AM-Tool-04
    dsm_model.py       — dynamic stock model with cohort-matrix element tracking
  plotting/
    __init__.py        — all public plot functions exported here
    composition.py     — plot_flow_composition() (NOT in __init__, import directly)
    sankey.py          — Sankey plots + export_sankey_batch() for batch exports
  reporting/
    validation_summary.py — display_system_summary() for workflow 2.2 section
    kpi_dashboard.py   — KPI calculation functions
    mc_dashboard.py    — MC result display
```

## Element system
- **Hierarchy**: `material = WC + DM`, `DM = TC + Ash_content`, `TC = TOC + TIC`
- **TC/CC fallback** (always use this pattern):
  ```python
  _tc_name = next((e for e in ("TC", "CC") if e in mfa_system.Elements), None)
  ```
- Legacy input files may use `CC` instead of `TC` — never hardcode either
- Indices: `material_idx`, `dm_idx`, `wc_idx`, `cc_idx` (= TC index)

## Solver & MFA system
- `solver.run_mfa_calculation(mfa_system, dsm_params, fomp_params, config, flow_tc_map=None, process_logic_map=None, lfg_params=None)` → **3-tuple** `(mfa_system, dsm_details, solver_info)` — always unpack all three
- Process 0 is the system boundary (environment), labeled `"Input"` in `process_logic_map`
- No `"Output"` label exists — boundary processes serve as both source and sink
- `process_logic_map` keys come from `.to_dict()` (no stripping/type conversion)

## Module guard patterns
- FOMP: check `cfg.RUN_FOMP_CALCULATION` before calling FOMP
- LFG: `getattr(config, 'RUN_LFG_CALCULATION', True)` (attribute may not exist)
- DSM/FOMP/LFG params are dicts keyed by process ID; empty dict `{}` means disabled

## Adding a new plot function
1. Write the function in the appropriate `02_src/plotting/<module>.py`
2. Export it from `02_src/plotting/__init__.py` (both import line AND `__all__` list)
3. Add it to the relevant `@app.cell` tab in `01_BioDYM_Dashboard.py` (no sync needed — Marimo format)
4. Add it to `00_BioDYM_Workflow.py` in the matching section, then sync: `uv run jupytext --to notebook 00_BioDYM_Workflow.py`

## Adding a new engine module
1. Create `02_src/engine/<module>.py`
2. Add a `load_<module>_parameters()` function in `data_loader.py`
3. Add a `RUN_<MODULE>_CALCULATION` flag to config / Excel `1_1_Configuration` sheet
4. Add the module call in `solver.py` at the right point in the fixed-point loop
5. Expose results in `plotting/dynamics.py` and add to dashboard

## Git conventions
- Branch names: `feat/<topic>`, `fix/<topic>`, `chore/<topic>`
- Commit format: `type(scope): short description` (e.g. `feat(lfg): add N-pool FOD model`)
- Never commit `.xlsm` input data files — they belong in `01_data/01_input/` but are gitignored
- Always commit `.py` and `.ipynb` together for `00_BioDYM_Workflow.py` changes
- `01_BioDYM_Dashboard.py` has no `.ipynb` counterpart — commit the `.py` only

## Common pitfalls
- `plot_flow_composition` is in `plotting.composition`, not `plotting` — import separately
- `w.HTML(...)` (ipywidgets) for widget layouts in Voilà only; `IPython.display.HTML` for standalone display
- FOMP StockDict key: `f"S_{process_id}"` — must exist in system before writing
- Sankey export functions live in `02_src/plotting/sankey.py` — see memory/sankey_plotting.md
- `export_sankey_batch()` is in `02_src/plotting/sankey.py` — use this instead of the inline loop
- `extract_workflow_dimensions()` is in `02_src/config.py` — use in workflow and dashboard
- `display_system_summary()` is in `02_src/reporting/validation_summary.py`
- Marimo dashboard: `mo.capture()` context captures IPython `display()` calls for tab content
