# Changelog

All notable changes to BioDYM will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-11-21

### Added
- Initial public release of BioDYM
- Complete Material Flow Analysis (MFA) engine based on ODYM framework
- Dynamic Stock Model (DSM) implementation with multiple lifetime distributions (Fixed, Normal, Lognormal)
- First-Order Mineralization Process (FOMP) for organic matter decomposition
- Multi-element tracking system (material, water content, dry matter, carbon content, etc.)
- Monte Carlo uncertainty analysis with configurable distributions
- Scenario manager for comparing multiple analysis scenarios
- Interactive Sankey diagram visualization with automatic layout
- Excel-based configuration system (no programming required)
- Stock-outflow transfer coefficients (BioDYM custom extension to ODYM)
- Pass-through process logic for simple flow routing
- Comprehensive test suite (97.2% pass rate)
- Full documentation suite including USER_GUIDE, TECHNICAL_DEEP_DIVE, and CLAUDE.md
- Example datasets (Wheat Straw case study)
- Template Excel file for new projects

### Core Features
- **Element-agnostic architecture**: Support for any element set (not limited to predefined elements)
- **ODYM compliance**: Proper initialization methods and zero mass balance errors
- **Flexible process logic**: Splitter, Transformer, DSM, FOMP, and Pass-through processes
- **Composition tracking**: Hierarchical composition handling (WC, DM, CC as metadata)
- **Time-series analysis**: Dynamic modeling over multiple years
- **Validation system**: Automatic mass balance checks and consistency validation
- **Export capabilities**: Results exported to Excel with multiple output formats

### Technical Highlights
- 12,536 lines of well-documented Python code
- NumPy-style docstrings throughout
- Ruff code formatting and linting
- UV/Conda installation support
- Python 3.12+ compatibility

### Documentation
- README.md with quick start guide
- USER_GUIDE.md with comprehensive tutorials
- TECHNICAL_DEEP_DIVE.md for developers
- CLAUDE.md for AI-assisted development
- PRE_PUBLICATION_CHECKLIST.md for release management
- CODING_STANDARDS.md and TROUBLESHOOTING.md
- Complete API documentation in docstrings

### Known Issues
- Fixed lifetime DSM test has minor discrepancy (tracked for v1.1)
- Limited visualization customization (planned for v2.1)
- No multi-regional MFA support yet (planned for v2.0)

### Dependencies
- ODYM framework (v20241127)
- Python packages: numpy, pandas, matplotlib, plotly, scipy, openpyxl, and more

---

## Future Releases

### [1.1.0] - Planned (Q1 2026)
- Fix DSM fixed lifetime calculation edge case
- Enhanced error messages and user feedback
- Performance optimizations for large systems
- Additional test coverage

### [2.0.0] - Planned (Q3 2026)
- Composition hierarchy as proper 3D structure (refactor metadata approach)
- Multi-regional MFA support (3D+: Time × Element × Region)
- Advanced data reconciliation
- Enhanced visualization customization

### [2.1.0] - Planned (Q4 2026)
- Advanced Sankey layout algorithms
- Interactive dashboard improvements
- Additional export formats

---

[1.0.0]: https://github.com/JScholz-tech/Biodym_JS/releases/tag/v1.0.0
