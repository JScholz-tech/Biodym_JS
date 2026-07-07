# BioDYM — Claude Code Project Instructions

## Commands
- **Run anything**: always prefix with `uv run` (e.g. `uv run python`, `uv run jupyter`)
- **Sync notebook**: `uv run jupytext --to notebook <file>.py`
- **Launch dashboard (Voilà — primary)**: `uv run voila 01_BioDYM_Dashboard.ipynb`
- **Launch bioDYM SystemDefiner**: `uv run python -m systemdefiner` → opens at http://localhost:8001
- **Execute notebook**: `uv run jupyter nbconvert --to notebook --execute <file>.ipynb`
- **Launch dashboard (Marimo — WIP, local-only)**: `uv run marimo run tools/marimo_dashboard.py`
- **Edit Marimo dashboard**: `uv run marimo edit tools/marimo_dashboard.py`
- **Run explorer tools (local-only)**: `uv run marimo run tools/buf_explorer.py` (or `cuf_explorer.py`)
- **NOTE**: `tools/` is gitignored (WIP/experimental, not part of the shipped package). The files exist locally but are not tracked — do NOT rely on them in `02_src/` code.

## Notebook workflow (Jupytext)
- The `.py` file is the **source of truth** — always edit `.py`, never `.ipynb` directly
- Light format (not percent): section markers are `# +` / `# -`, not `# %%`
- **After every edit to a `.py` notebook**, sync it: `uv run jupytext --to notebook <file>.py`
- After editing any module in `02_src/`, the Jupyter kernel must be restarted for changes to take effect — `%autoreload` is NOT configured
- Notebooks: `00_BioDYM_Workflow.py` (main analysis)
- **IMPORTANT**: `tools/marimo_dashboard.py` uses `@app.cell` decorators (Marimo format) — it is NOT a Jupytext file. Do NOT run `jupytext` on it.

## Project structure
```
01_BioDYM_Dashboard.ipynb — Voilà dashboard (primary); launch with `uv run voila 01_BioDYM_Dashboard.ipynb`
tools/                   — WIP/experimental, gitignored (local-only): marimo_dashboard.py, buf_explorer.py, cuf_explorer.py
02_src/
  config.py            — load_configuration() + extract_workflow_dimensions()
  data_loader.py       — load_*_parameters() functions + yaml_to_excel_dataframes() (YAML-only mode)
  system_setup.py      — define_model_scope / initialize_mfa_system / load_and_define_processes / define_flows_and_parameters
  systemdefiner/       — bioDYM SystemDefiner FastAPI web app (`uv run python -m systemdefiner`, port 8001)
    main.py            — routes; storage.py — case-study persistence (01_data/01_input/case_studies/)
    yaml_schema.py     — model_to_yaml() etc. — YAML config schema (SystemDefiner dependency; moved from tools/)
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
3. Add it to the relevant `@app.cell` tab in `tools/marimo_dashboard.py` (no sync needed — Marimo format)
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
- Never commit `.xlsm` user data files from `01_data/01_input/` — they are gitignored (exception: `01_data/01_input/template/` and `03_studies/` published case study inputs ARE tracked)
- Always commit `.py` and `.ipynb` together for `00_BioDYM_Workflow.py` changes
- Voilà dashboard: `01_BioDYM_Dashboard.ipynb` is the primary dashboard — commit standalone (no paired `.py`)
- Marimo dashboard: `tools/marimo_dashboard.py` is WIP — commit standalone (no `.ipynb` counterpart)

## Mathematical Notation Convention

All equations in BioDYM documentation and code comments follow these rules.
Full formula reference: `Writing project/Monographie/bioDYM_mathematical_formulas.md`

### Position convention (Rule 3)
In any physical quantity symbol, the **superscript** always identifies *what substance* (the element), and the **subscript** always identifies *where or which* (process, flow, pool, fraction, category). Time is always a function argument `(t)`, never a sub- or superscript.

Example: `D_L^DM(t)` — subscript `L` = labile pool (which pool), superscript `DM` = dry matter (what element), `(t)` = time-varying.

### Quantity notation
- **Flows**: `F_f^e(t)` — subscript = flow ID `f`, superscript = element `e`; shorthand `F_f(t) := F_f^mat(t)`
- **Stocks**: `S_p^e(t)` — subscript = process `p`, superscript = element `e`; shorthand `S_p(t) := S_p^mat(t)`
- Rule applies to all physical quantities: `F`, `S`, `I`, `O`, `D`, `G`
- `(t)` marks a time-varying quantity — omit for constants (e.g. `φ_f^e`, `k_L`, `α_L`)

### Reserved symbols — do not reassign
| Symbol | Reserved for |
|--------|-------------|
| `f` (subscript) | Flow identifier only — never a fraction prefix |
| `φ_f^e` | Static parent-relative content fraction; `p(e)` = parent element of `e` |
| `ψ` | UNFCCC correction factor (LFG only) — avoids collision with `φ` |
| `α` | Dimensionless split fractions: `α_L` (FOMP labile), `α_i` (DSM category) |
| `k` (subscripted) | First-order decay constants [yr⁻¹]: `k_L`, `k_R`, `k_j` |
| `κ` | Weibull shape parameter — avoids collision with `k` |
| `i` | General numbering index — DSM lifetime categories, process outflows (TC routing, MC normalisation), neighbouring processes in mass balance sums; local context defines what is counted |
| `j` | LFG waste fraction index |
| `c` | DSM_Component component type index |

### Element superscript abbreviations
`mat` (material), `WC` (water content), `DM` (dry matter), `TC` (total carbon), `TOC`, `TIC`, `Ash`

### Known exception
LFG gas outputs `G_CH4(t)` and `G_CO2(t)` embed the chemical species in the subscript. Element TC is implied by the unit [Mg C yr⁻¹] — no superscript applied here.

### Code↔paper bridge
Each engine module must contain a notation table in its module or function docstring:
```python
# Mathematical notation (see bioDYM_mathematical_formulas.md §<N>):
#   Paper symbol    Code variable
#   α_L          ←→  f_labile
#   k_L          ←→  k_labile
#   r_TC(t)      ←→  cc_dm_series
```

## Common pitfalls
- `plot_flow_composition` is in `plotting.composition`, not `plotting` — import separately
- `w.HTML(...)` (ipywidgets) for widget layouts in Voilà only; `IPython.display.HTML` for standalone display
- FOMP StockDict key: `f"S_{process_id}"` — must exist in system before writing
- Sankey export functions live in `02_src/plotting/sankey.py` — see memory/sankey_plotting.md
- `export_sankey_batch()` is in `02_src/plotting/sankey.py` — use this instead of the inline loop
- `extract_workflow_dimensions()` is in `02_src/config.py` — use in workflow and dashboard
- `display_system_summary()` is in `02_src/reporting/validation_summary.py`
- Marimo dashboard (`tools/marimo_dashboard.py`): uses `mo.state()` for result persistence; `mo.capture()` captures IPython `display()` calls for tab content
