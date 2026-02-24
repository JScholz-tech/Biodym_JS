# Changelog

All notable changes to BioDYM will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

## Future Releases

### [1.1.0] - Planned
- Enhanced error messages and user feedback
- Performance optimizations for large systems
- Additional validation test cases
- Benchmark comparison against published MFA studies

### [2.0.0] - Planned
- Composition hierarchy as proper 3D array structure (refactor metadata approach)
- Multi-regional MFA support (Time × Element × Region)
- Advanced data reconciliation module
- FOMP initial stock support via Excel configuration

### [2.1.0] - Planned
- Advanced Sankey layout algorithms
- Interactive dashboard improvements
- Additional export formats (SVG, HTML)

---

[1.0.0]: https://github.com/JScholz-tech/Biodym_JS/releases/tag/v1.0.0
