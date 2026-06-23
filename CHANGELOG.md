# Changelog

All notable changes to BioDYM will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.2.1] - 2026-06-23

### Added
- Tutorial studies T01–T07 shipped with the repository — a fresh clone opens
  the bioDYM SystemDefiner with seven ready-to-run worked examples
- `GETTING_STARTED_FROM_ZERO.md` — step-by-step onboarding guide for new users
- SystemDefiner: DSM editor with category UX and model validation
- SystemDefiner: health-check panel flags incomplete processes before export
- SystemDefiner: per-study description displayed under the system diagram
- SystemDefiner: DSM, LFG, Initial Stock, and FlowCap parameters importable
  from an existing Excel Systemmanager
- `01_data/01_input/README.md` — documents both Excel and YAML input formats

### Fixed
- DSM engine: Fixed and LogNormal lifetime types now handled correctly
- SystemDefiner: 0-based process IDs, displayed as P{id}
- SystemDefiner: Transformer TCs correctly use element-level entries
- SystemDefiner: Duplicate (clone) button made reliable
- SystemDefiner: dynamic TC editor aligned with static editor
- SystemDefiner: material TC uses `TC_E1_` convention (matches Excel)
- data_loader: YAML→engine bridge now emits all required sheets
  (LFG, FlowCap, FOMP, DSM, Scenario Manager, empty TC sheets)
- export: Excel sheet names sanitised to ≤31 characters
- DGAW published case study input file restored (mistakenly removed in v1.2.0)
- Tutorial descriptions T05–T07 corrected (were copies of T04 description)

### Changed
- Notebook refactored: `sys.path` / widget bootstrap extracted to
  `02_src/bootstrap.py`; MC table styling moved into `mc_dashboard.py`
- Publication plots now honour the configured theme unit
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
