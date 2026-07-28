# Changelog

All notable changes to BioDYM will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.3.5] - 2026-07-28

Housekeeping release after v1.3.0 — bundles two ready feature branches and the
deferred Dashboard/Workflow parity fix. (`1.4.0` is reserved for the
Input_Substitution headline; the `1.3.5` number is a deliberate
bigger-than-patch signal.)

### Added
- SystemDefiner: study **grouping** — editable `group` field + Group column on the
  case-study index, with group-based collapsible sections
- SystemDefiner: **Tutorials auto-collapse** — shipped `T##` tutorials are detected by
  name and shown in a separate collapsed section from "Your Case Studies"
- SystemDefiner: **glossary page** (`/glossary`) and a copy-config-path navigation button
- Plotting: `plot_component_replacement_rate` (DSM component replacement dynamics) and a
  `print_cuf_summary` helper re-export
- Engine: **element-hierarchy consistency validation** after solve, and exhaustive
  derivation of parent elements from their children in the Transformer
- Tooling: `name-convention` skill for scanning/standardising flow & process name fields
- Tests: `test_yaml_loader_parity.py` — guards that the native YAML loaders and the
  Excel-style loaders agree on every shared key, per tracked study

### Fixed
- Dashboard: load **all** parameter domains (DSM/FOMP/LFG/FlowCap) through
  `load_all_parameters()` in YAML-only mode instead of the Excel-style shim, eliminating
  the two-parallel-parsers divergence class (YAML-only studies previously got Excel-shim
  parameter subsets in the Dashboard; only FOMP had been fixed on main)
- Tests: the tracked-studies round-trip test now scans only shipped `T##` studies, so local
  gitignored studies no longer redden developer runs

### Docs
- Rebuilt the shipped manual PDF with the "New in v1.3" section

---

## [1.3.0] - 2026-07-28

### Added
- Windows desktop launcher (`BioDYM_Launcher.py`): one-click startup, automatic recovery from
  port conflicts, persistent display of running service ports, graceful handling of dashboard
  startup failures
- SystemDefiner: config-consistency validator with a flow-pointer registry
  (`consistency.py::check_config_consistency` / `iter_flow_pointers`) — catches broken
  rename/delete cascades and cross-reference errors as part of the model health report
- SystemDefiner: CSV import + accordion layout for the flow-data editor
- SystemDefiner: user-extensible composition hierarchy depth (no longer fixed to 4 levels)
- SystemDefiner: flow IDs auto-sync when endpoints change on edit
- SystemDefiner: live rule feedback in the Hierarchy Matrix editor
- SystemDefiner: "Compact IDs" and per-domain editor improvements across elements/hierarchy
- Plotting: interactive, Voilà-safe sunburst view of flow composition; new golden tutorial T16
  (6-level composition) demonstrates it
- Monte Carlo: multiple year-windows per dynamic TC parameter
- Data loader: `DSM_Component` entries now load through the native YAML path

### Changed
- SystemDefiner: `main.py` (3,100 lines) split into per-domain routers
  (`studies`/`processes`/`flows`/`tcs`/`elements`/`scenarios`/`references`/`compositions`/`io`) +
  shared helper modules — router include order is now pinned by a route-inventory test
- SystemDefiner: config is normalized on every save (processes sorted by ID, orphan BOM/initial-
  stock entries pruned); folder name is authoritative over the YAML-internal name on load
- Reporting: exports made element-agnostic (previously assumed a fixed element set)
- Docs: `CLAUDE.md` updated for the SystemDefiner module split

### Fixed
- **FOMP**: was routing 100% of decayed DM onto the carbon outflow instead of splitting it with
  the paired environmental flow whenever the TC ratio is time-constant (the common case) —
  every FOMP study's Water & Nutrient Cycle flow was silently getting zero DM
- **FOMP / Dashboard**: the Voilà Dashboard silently used default decay parameters instead of a
  study's configured values for every YAML-only FOMP study, due to a parameter-key mismatch
  between `yaml_to_excel_dataframes()` and `calculate_fomp()` — the Workflow notebook was
  unaffected (different loading path)
- **Scenario engine**: `apply_scenario`'s post-modification composition recalc was material-
  relative instead of parent-relative, corrupting nested element-hierarchy trees on every
  scenario run (depth ≥ 2)
- Engine: static/dynamic material-TC parameter naming harmonized (`TC_E{n}_` convention for
  every element, including material, in both static and dynamic TC sheets)
- Monte Carlo: `sample_parameters` no longer crashes with `ZeroDivisionError` on a structural-
  zero (`std=0`) normal distribution — returns the mean as a constant draw
- Monte Carlo: `normalize_tc_updates` now warns (instead of silently skipping) when an
  uncertainty-parameter group doesn't cover every outgoing flow of a process — this previously
  risked silent mass creation
- Plotting: Monte Carlo dropdowns were truncating nested element names (`Rest_AlAlloy` → `Rest`)
  via a naive column split, making leaf elements unreachable
- Data loader: TCs referencing a missing flow are now skipped instead of exported under a junk
  shared ID that could collide with another dangling TC
- Engine / Plotting: mass-balance checks and error reporting are now indexed by process ID
  instead of list position
- SystemDefiner: numerous cascade-correctness fixes — hierarchy edges render fully (was
  corrupting on save-loop), element rename/reorder/delete cascades through the whole config,
  route-level consistency maintained on rewire/ID change/logic change/import
- Launcher: hardened Windows portability, isolated Jupyter runtime state, handles dashboard
  startup failures, reports killed processes as stopped on Windows

### Tests
- Golden regression: T01/T04 re-pinned after schema-default config normalization; T16 added
- SystemDefiner: route-inventory + full-page round-trip pinned as a guard before the router
  restructuring

---

## [1.2.2] - 2026-07-07

### Added
- SystemDefiner: reference manager rolled out across all parameter editors —
  reusable multi-select widget (shows titles) on transfer coefficients
  (static + dynamic), flow compositions, initial stock, FOMP/DSM, scenarios,
  Monte Carlo, flow data, LFG, FlowCap, and BOM_Assembler; standalone
  assumptions list with custom (non-Zotero) entries
- SystemDefiner: DSM_Component process logic for spare-part renewal, with
  per-category component replacement rates
- SystemDefiner: FoldedNormal DSM distribution option, dynamic TC status
  indicator, `expected_inflow_composition`
- SystemDefiner: MC seed and solver settings exposed in the editor and dashboard
- SystemDefiner: "Compact IDs" button to renumber process-ID gaps
- SystemDefiner: FlowCap cap made addressable in the Scenario Manager and
  Monte Carlo editors
- Reporting: parameter overview export for SystemDefiner-defined systems
- Plotting: interactive Monte Carlo box plot
- Engine: per-node element hierarchy composition validation
- Docs: mathematical notation convention, getting-started guide, notation
  tables, FOMP ignored-parameter warnings
- Tests: golden regression net covering tutorials T01-T15; unit tests for
  five previously-untested engine modules
- Tests: golden regression now also pins scenario-engine and Monte Carlo
  outputs (not just the baseline MFA solve), with a config-hash drift guard
  that fails fast if a tutorial's `config.yaml` changes without regenerating
  its reference

### Changed
- SystemDefiner: composition fractions are now stored parent-relative rather
  than absolute
- SystemDefiner: LFG entries hidden from the scenario/MC parameter dropdown
  (not applicable there)
- Engine: TC/CC fallback and element-index lookups consolidated
- FOMP: hierarchy-consistent carbon outflow composition

### Fixed
- Monte Carlo: LFG/BOM_Assembler/FlowCap module parameters are now forwarded
  into MC iterations (processes no longer go silently inactive during MC runs)
- Monte Carlo: reproducible runs via a seeded numpy Generator (`MC_Seed`);
  runs survive failed solver iterations, with a new `SOLVER_STRICT`
  non-convergence mode
- Dashboard: "no MC params defined" is now distinguished from "all iterations
  failed"
- Solver: process-ID parameters are validated; unphysical MC draws rejected
- Engine: robustness hardening; per-year hierarchical element fractions
  (previously locked to the first year)
- LFG: MCF/OX/phi now apply to the CH4 pathway only; `stable_stock` split by unit
- DSM: initial-stock decay follows the category lifetime distributions; shared
  spare flows accumulate correctly across components; suppressed a spurious
  divide-by-zero warning in the outflow composition calc
- Scenario: Weibull Shape/Scale now supported in the DSM branch of
  `apply_scenario`; NaN scenario names from empty Excel cells are skipped
- SystemDefiner: the 'material' first element is protected from edits

---

## [1.2.1] - 2026-06-25

### Added
- Tutorial studies **T01–T14** ship with the repository — a fresh clone opens
  the bioDYM SystemDefiner with fourteen ready-to-run worked examples, one per
  feature: first MFA, splitting, composition/hierarchy, DSM, dynamic TCs, FOMP,
  initial stock, scenarios, FlowCap, BOM assembly, Monte Carlo (process and
  input-flow group), LFG, and the reference manager
- `GETTING_STARTED_FROM_ZERO.md` — step-by-step onboarding guide for new users
- SystemDefiner: **reference manager** with two labelled lists — Literature
  (numbered) and Assumptions & notes (lettered) — plus an "Add assumption" form
  for self-authored, non-Zotero entries
- SystemDefiner: **multiple references per parameter** — a checkbox-dropdown
  multi-select (showing titles, with hover) on every editor: transfer
  coefficients (static + dynamic), flow compositions, DSM, FOMP, initial stock,
  scenarios, Monte Carlo, flow data, LFG, FlowCap and BOM
- SystemDefiner: study-configurable **Sankey diagram title** (`sankey_title`,
  falling back to the study name); applied in both the notebook and the Voilà dashboard
- SystemDefiner: study **description rendered as Markdown**; "Back to study"
  navigation link on every page
- SystemDefiner: DSM editor UX — distribution-aware fields (Normal/LogNormal/
  Weibull/Fixed), percent inflow split with a live sum-to-100 % check
- SystemDefiner: health checks — incomplete FlowCap/FOMP processes,
  BOM_Assembler requires transfer coefficients, Monte Carlo unit guards
  (TC fractions vs percentages, implausible flow magnitudes)
- SystemDefiner: per-study description displayed under the system diagram
- SystemDefiner: DSM, LFG, Initial Stock, and FlowCap parameters importable
  from an existing Excel Systemmanager
- `01_data/01_input/README.md` — documents both Excel and YAML input formats

### Fixed
- DSM engine: Fixed and LogNormal lifetime types now handled correctly
- DSM engine: exponential-decay initial stock is mass-balanced — removed a
  phantom first-year outflow that created material out of nowhere
- SystemDefiner: 0-based process IDs, displayed as P{id}; adding a process
  reuses the lowest free id, filling gaps left by deletions
- SystemDefiner: initial-stock entries removed when cleared, and pruned when
  orphaned; flagged when attached to a non-DSM process or the boundary
- SystemDefiner: numeric value fields accept arbitrary decimal precision
- SystemDefiner: case-study / diagram deletion tolerates Windows
  read-only / locked files
- SystemDefiner: Transformer TCs correctly use element-level entries
- SystemDefiner: Duplicate (clone) button made reliable
- SystemDefiner: dynamic TC editor aligned with static editor
- SystemDefiner: material TC uses `TC_E1_` convention (matches Excel)
- data_loader: YAML→engine bridge now emits all required sheets
  (LFG, FlowCap, FOMP, DSM, Scenario Manager, empty TC sheets)
- export: Excel sheet names sanitised to ≤31 characters
- DGAW published case study input file restored (mistakenly removed in v1.2.0)
- Tutorial descriptions corrected (some were copies of the T04 description)

### Changed
- References are now multi-valued (`refs` list) on every parameter, with a
  backward-compatible single-`ref` fallback; a parameter can cite both a
  literature source and a self-authored assumption
- Tutorial studies tracked in place via the `case_studies/T[0-9][0-9]_*` whitelist
- Notebook refactored: `sys.path` / widget bootstrap extracted to
  `02_src/bootstrap.py`; MC table styling moved into `mc_dashboard.py`
- Publication plots now honour the configured theme unit + thousands formatting
- CI and first-run environment parity improvements

---

## [1.2.0] - 2026-06-18

### Added
- **bioDYM SystemDefiner** — interactive web app for configuring case studies visually
  (`uv run python -m systemdefiner`, opens at http://localhost:8001)
  - Full YAML-based system definition: processes, flows, TCs, DSM/FOMP/LFG/FlowCap/BOM parameters
  - Scenario and Monte Carlo parameter management with named-parameter dropdowns
  - Zotero reference manager integration (linked to every TC, flow, and parameter)
  - Export to `config.yaml`; import from BioDYM Excel Systemmanager
  - Case studies stored under `01_data/01_input/case_studies/` (gitignored — user-local data)
- **YAML-only workflow** — engine runs entirely from a `config.yaml` without an Excel file
  (`yaml_to_excel_dataframes()` synthesises all DataFrames; `load_config_from_yaml()` builds config)
- **LFG module** (`02_src/engine/lfg_model.py`) — N-pool first-order decay landfill gas model
  (UNFCCC AM-Tool-04); supports CH4 capture fraction, oxidation factor, UNFCCC φ correction
- **BOM Assembler** process logic — product composition tracking through a bill-of-materials
- **FlowCap** process logic — capacity-limited flow routing with year/flow time series
- **Multi-category DSM** — multiple lifetime cohorts per DSM process with per-category
  Inflow Split, Mean/StdDev (Normal/LogNormal) or Shape/Scale (Weibull) parameters
- **Voilà dashboard YAML support** — `01_BioDYM_Dashboard.ipynb` now accepts a `.yaml` path
  in the file input field (YAML-only or YAML + Excel hybrid)
- **MC parameter improvements**: per-category DSM Shape/Scale in dropdown; correct
  "set/multiply/add" operation terminology (separate from scenario "replace/multiply/add")
- Named element columns (`E{n}` format) in TC Excel sheets with legacy fallback
- Initial stock engine improvements: cohort-based age distribution; depletion model

### Changed
- `app/` renamed and relocated → `02_src/systemdefiner/` (all source code in `02_src/`)
- Launch command: `uv run python -m systemdefiner` (was `python -m app`)
- `case_studies/` moved to `01_data/01_input/case_studies/` and gitignored
- Web app branding updated to "bioDYM SystemDefiner" throughout
- `pyproject.toml`: added `[build-system]` (setuptools) so `02_src/` packages are
  installable; added `httpx`, `pydantic`, `jupytext` as explicit dependencies

### Fixed
- DSM Weibull TypeError: `load_dsm_from_yaml()` stored `None` for missing mean/std
  (now defaults to `0.0`); guard added in `_calculate_outflow_from_initial_stock`
- MC parameter dropdown showing "Custom…" for all entries (FOMP naming, TC E-numbering,
  DSM Shape/Scale were missing or mis-keyed)
- `validate_mc_parameters()` and `build_parameter_overview_df()` now accept both
  `MC_Parameter_ID` (new) and `Parameter_Name` (legacy Excel) column names
- `yaml_to_excel_dataframes()` now generates `4_1_Uncertainty_Parameters` sheet
  so the notebook MC condition passes in YAML-only mode
- `recalculate_hierarchical_elements` removed from Splitter/Transformer branches
  (caused double-counting in element mass balance)

---

## [1.1.0] - 2026-05-04

Intermediate development release. Introduced the LFG landfill-gas module,
multi-format Sankey export, DSM vintage cohort tracking, Voilà dashboard,
and a plotting theme system. Not formally announced — superseded by v1.2.0.

---

## [1.0.0] - 2026-02-24

### Added
- Complete Material Flow Analysis (MFA) engine based on ODYM framework
- Dynamic Stock Model (DSM) with multiple lifetime distributions (Fixed, Normal, Lognormal, Weibull)
- First-Order Mineralization Process (FOMP) for two-pool organic matter decomposition (labile/recalcitrant)
- Multi-element tracking system (material, water content, dry matter, carbon content — configurable)
- Monte Carlo uncertainty analysis with configurable distributions
- Scenario manager for comparing multiple analysis configurations
- Interactive Sankey diagram visualization with automatic layout
- Excel-based configuration system (`xlsm` — no programming required for users)
- Stock-outflow transfer coefficients (BioDYM custom extension to ODYM)
- Pass-through process logic for simple flow routing
- Dual-mode initial stock system: exponential decay (`Stock_with_InitialStock_Decay`) and
  mathematically consistent ODYM age-cohort method (`Stock_with_InitialStock_Cohort`)
- Comprehensive test suite — **43/43 tests passing (100%)**
- Published case study: Wheat Straw Cascading System (DGAW 2026, DOI: 10.15203/99106-187-8)
- BioDYM Systemmanager template (`01_data/01_input/template/`)
- User manual (`05_docs/biodym_manual.pdf`, 37 pages)
- CITATION.cff with ORCID and Zenodo DOI placeholder
- Colorblind-safe publication-quality plot palette

### Core Features
- **Element-agnostic architecture**: Any element set supported (biomass, metals, packaging, etc.)
- **ODYM compliance**: Proper initialization methods, zero mass balance errors
- **Flexible process logic**: Input, Splitter, Transformer, DSM, FOMP, Pass-through
- **Composition tracking**: Hierarchical element handling (WC/DM/CC as configurable hierarchy)
- **Time-series analysis**: Dynamic modeling over multiple years with linear interpolation
- **Validation system**: Automatic mass balance checks and consistency warnings
- **Export capabilities**: Results to Excel (results, composition, KPI, MC, scenarios, figures)

### Technical Highlights
- Python 3.12+, UV and Conda installation supported
- NumPy-style docstrings throughout
- Ruff code formatting and linting
- Structured output folders: `results/`, `composition/`, `kpi/`, `mc/`, `figures/`, `scenarios/`

### Documentation
- `README.md` — Quick start guide with installation, template usage, and citation
- `05_docs/biodym_manual.pdf` — 37-page LaTeX user manual
- `CITATION.cff` — Machine-readable citation (ORCID, Zenodo DOI placeholder)
- `03_studies/26_Weizenstroh_DGAW/` — Published case study with input, output, README, LICENSE, CITATION.bib
- Inline docstrings and mass balance documentation throughout `02_src/`

### Reviewer Feedback Addressed (pre-release)
- **Test coverage**: Fixed all import failures; raised from 81.4% → 100% (43/43)
- **DSM fixed lifetime**: Removed `@pytest.mark.skip`, test now passes with exact validation
- **DSM Normal lifetime**: Replaced `rtol=1.0` tolerance with proper mass balance validation
- **DSM mathematical consistency**: Added dual-mode initial stock (decay vs. age-cohort)
- **FOMP limitation documented**: Zero-initial-stock assumption clearly stated in `fomp_model.py`
- **Convergence criterion documented**: `rtol=1e-05, atol=1e-08`, max 30 iterations (solver.py)
- **Dependencies**: `uv.lock` ensures full reproducibility

### Known Limitations
- FOMP initial stocks are fixed at zero (appropriate for fresh-application case studies)
- FOMP uses time-averaged CC/DM ratio as a constant (~2% CC mass balance error — by design)
- No multi-regional MFA support (planned for v2.0)
- Limited Sankey layout customization (planned for v2.1)

### Repository
- Branch: `main` (renamed from `master`)
- GitHub topics: `material-flow-analysis`, `mfa`, `odym`, `bio-based-materials`,
  `circular-economy`, `dynamic-stock-model`, `monte-carlo`, `sustainability`, `python`, `jupyter`
- Auto-delete merged branches enabled
- Draft release `v1.0.0` created on GitHub

---



---

[1.2.1]: https://github.com/JScholz-tech/Biodym_JS/releases/tag/v1.2.1
[1.2.0]: https://github.com/JScholz-tech/Biodym_JS/releases/tag/v1.2.0
[1.1.0]: https://github.com/JScholz-tech/Biodym_JS/releases/tag/v1.1.0
[1.0.0]: https://github.com/JScholz-tech/Biodym_JS/releases/tag/v1.0.0
