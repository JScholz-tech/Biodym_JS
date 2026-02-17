# BioDYM Pre-Publication Checklist

This comprehensive checklist ensures BioDYM v1.0 is publication-ready. Track progress systematically before releasing on GitHub.

## ✅ PRIORITY 1: Critical Blockers (Must Fix Before Publication)

### 1.1 Fix Testing Suite (87.5% COMPLETE - 2025-11-21)
- [x] Fix test collection error - **RESOLVED**
  - Issue: `test_sankey_simplified.py` had `sys.exit(1)` during import
  - Solution: Renamed to `sankey_validation_script.py` (not a pytest test)
- [x] Fix column name mismatches - **RESOLVED** (5 tests fixed)
  - Updated test data to use correct schema: Flow_Name, Flow_Output_Process_ID, Input_Process_ID
  - Updated sheet names: 2_2_static_TCs, 2_3_dynamic_TCs, 2_4_Initial_Stock
  - Added element fraction columns and Process_Logic columns
- [x] Fix DSM parameter loading - **RESOLVED** (1 test fixed)
  - Added 2_1_Definition_Processes sheet to test data with Process_Logic="DSM"
  - Updated expected output format (Type as list, parameter_based flag)
- [x] Fix dynamic TC schema - **RESOLVED** (2 tests fixed)
  - Added Flow_ID column to 2_3_dynamic_TCs test data
- [x] Fix element index issues - **RESOLVED** (2 tests fixed)
  - Corrected Flow_E4_Fraction[%] for CC (was incorrectly using E3)
  - Fixed ODYM import path (06_framework/ not framework/)
- [ ] **5 remaining test failures** (35/40 passing = 87.5%):
  - [ ] Golden dataset integration test (schema updates needed)
  - [ ] Sankey position clamping (logic issue)
  - [ ] DSM outflow calculation (minor mismatch)
  - [ ] Load and define processes (2x - file path mocking)
- [ ] Verify all tests pass: `uv run pytest`
- [ ] Check test coverage: `uv run pytest --cov=02_src`
- [ ] Document remaining 5 expected test failures with clear justification

### 1.2 Update LICENSE File ✅ (90% COMPLETE)
- [x] Update copyright holder: "Johannes Scholz (BioDYM Development Team)"
- [x] Update copyright year: 2025
- [x] Add ODYM attribution section with:
  - Link to ODYM repository: https://github.com/IndEcol/ODYM
  - Citation: Pauliuk, S., Heeren, N. (2020). ODYM framework. Journal of Industrial Ecology, 24(3), 446-458.
  - DOI: https://doi.org/10.1111/jiec.12952
- [x] Verify MIT license terms are complete
- [ ] Consider adding CONTRIBUTORS.md file listing all contributors (optional, can be part of metadata files)

### 1.3 Delete Unused/Conflicted Files ✅ COMPLETE
- [x] Delete: `README (conflicted copy 2025-10-21 140428).md` (NOT FOUND - already cleaned)
- [x] Delete: `01_data/01_input/~$251027_BioDYM_ODYM.xlsm` (NOT FOUND - already cleaned)
- [x] Run cleanup search: `find . -name "*conflicted*" -o -name "~$*" -o -name "*.tmp" -o -name "*.bak"`
- [x] Remove any files found by cleanup search (NONE FOUND)
- [x] Verify `.gitignore` prevents future temp file commits (Excel temp files already in .gitignore)

## ✅ PRIORITY 2: Documentation Quality (Essential for Users)

### 2.1 README.md Review
- [ ] Update project status (remove "beta" references)
- [ ] Verify installation instructions work from scratch
- [ ] Add proper ODYM citation in acknowledgments
- [ ] Update "Last updated" date
- [ ] Add badges: License, Python version, build status
- [ ] Verify all example commands work
- [ ] Add "Getting Help" section with issue tracker link
- [ ] Include example output screenshots/figures

### 2.2 USER_GUIDE.md Review
- [ ] Verify all sections are current and complete
- [ ] Test all tutorial examples work
- [ ] Add troubleshooting section from CLAUDE.md
- [ ] Include Excel template structure documentation
- [ ] Add FAQ section for common questions
- [ ] Verify all screenshots/figures are up-to-date

### 2.3 Code Documentation Audit
- [ ] Run docstring completeness check: `grep -r "^def " 02_src/ --include="*.py" | wc -l`
- [ ] Verify all functions have NumPy-style docstrings
- [ ] Check module-level docstrings in all `.py` files
- [ ] Verify docstring examples are correct
- [ ] Update any outdated parameter descriptions
- [ ] Remove placeholder docstrings ("TODO: Add description")

### 2.4 Fix TODO/FIXME Markers
- [ ] Review TODOs in `02_src/data_loader.py`
- [ ] Search entire codebase: `grep -r "# TODO\|# FIXME\|# HACK\|# XXX" 02_src/`
- [ ] Either implement, document, or remove each TODO
- [ ] Convert critical TODOs to GitHub issues for v1.1+

## ✅ PRIORITY 3: Visual Quality (Publication Standards)

### 3.1 Unified Figure Styling
- [ ] Verify `02_src/plotting/publication_style.py` is complete
- [ ] Audit all plotting modules for `publication_style.py` usage:
  - [ ] `sankey.py`
  - [ ] `enhanced_sankey.py`
  - [ ] `dynamics.py`
  - [ ] `validation.py`
  - [ ] `monte_carlo.py`
  - [ ] `composition.py`
  - [ ] `scenario.py`
  - [ ] `graphviz_flow_charts.py`
- [ ] Test all visualizations with publication settings
- [ ] Ensure color-blind friendly palettes used
- [ ] Verify figure export quality (DPI ≥ 300 for print)
- [ ] Add user configuration file for custom styling

### 3.2 Sankey Visualization Improvements
- [ ] Review layout algorithm in `enhanced_sankey.py`
- [ ] Test with complex systems (20+ processes, 50+ flows)
- [ ] Verify `6_3_Layout_Configuration` Excel sheet usage
- [ ] Implement manual node positioning overrides
- [ ] Add automatic layout optimization option
- [ ] Document layout best practices in USER_GUIDE.md
- [ ] Fix any overlapping nodes/flows issues

## ✅ PRIORITY 4: Code Quality (Professional Standards)

### 4.1 Code Quality Sweep
- [ ] Check for hardcoded paths: `grep -r "C:/" 02_src/ --include="*.py"`
- [ ] Check for hardcoded paths: `grep -r "/Users/" 02_src/ --include="*.py"`
- [ ] Check for debug prints: `grep -r "print(\"DEBUG" 02_src/ --include="*.py"`
- [ ] Find commented code blocks: `grep -r "^# def " 02_src/ --include="*.py"`
- [ ] Run Ruff format: `ruff format 02_src/`
- [ ] Run Ruff check: `ruff check 02_src/`
- [ ] Fix all Ruff warnings and errors
- [ ] Verify no secrets/API keys in code

### 4.2 Error Handling Review
- [ ] Audit all Excel loading for try/except blocks
- [ ] Verify error messages are informative (not just tracebacks)
- [ ] Test error handling with malformed Excel files
- [ ] Add user-friendly error messages with next steps
- [ ] Test graceful degradation when optional features fail
- [ ] Document expected error scenarios in USER_GUIDE.md

### 4.3 Performance Testing
- [ ] Test with large system (50+ processes, 100+ flows)
- [ ] Measure Monte Carlo performance (1000 iterations)
- [ ] Profile solver convergence time
- [ ] Document system requirements (RAM, CPU) in README
- [ ] Identify and document performance bottlenecks
- [ ] Add performance tips to documentation

## ✅ PRIORITY 5: Example Data & Reproducibility

### 5.1 Verify Example Files
- [ ] Test `250922_CS1_Wheat_Straw.xlsx` runs completely
- [ ] Test `250625_Template_CS0.xlsx` is clean and functional
- [ ] Verify sample outputs in `01_data/02_output/` are current
- [ ] Check example files for sensitive/personal data
- [ ] Ensure example files have proper documentation
- [ ] Add README in `01_data/01_input/` explaining examples
- [ ] Test examples on fresh Python environment

### 5.2 Master Integration Test
- [ ] Run `00_BioDYM_Workflow.ipynb` completely (Kernel → Restart & Run All)
- [ ] Verify all cells execute without errors
- [ ] Check all visualizations render correctly
- [ ] Verify exported results are scientifically correct
- [ ] Test with both `.xlsx` and `.xlsm` input files
- [ ] Document expected runtime in notebook

### 5.3 Reproducibility Checks
- [ ] Same input → same results (deterministic)
- [ ] Set random seeds for Monte Carlo
- [ ] Lock dependencies in `pyproject.toml` and `uv.lock`
- [ ] Test on fresh environment: `uv sync` from scratch
- [ ] Document Python version requirements (currently ≥3.12)
- [ ] Test on different OS (Windows/Mac/Linux if possible)

## ✅ PRIORITY 6: Repository Metadata (GitHub Publication)

### 6.1 Git Repository Cleanup
- [ ] Review `.gitignore` completeness
- [ ] Verify no large files (>10 MB) committed
- [ ] Check no `.pyc` or `__pycache__` directories tracked
- [ ] Remove any committed temp files
- [ ] Clean up commit history if needed (squash/rebase)
- [ ] Ensure no sensitive data in git history

### 6.2 GitHub Repository Setup
- [ ] Set repository description (1-2 sentence summary)
- [ ] Add topics/tags: `mfa`, `material-flow-analysis`, `odym`, `python`, `jupyter`, `sustainability`, `circular-economy`
- [ ] Enable GitHub Issues
- [ ] Enable GitHub Discussions (optional)
- [ ] Set up GitHub Pages for documentation (optional)
- [ ] Configure branch protection rules for `master`

### 6.3 Additional Files
- [ ] Add `CONTRIBUTING.md` with contribution guidelines
- [ ] Add `CITATION.cff` for academic citation format
- [ ] Add `CHANGELOG.md` documenting version history
- [ ] Add `CODE_OF_CONDUCT.md` (optional but recommended)
- [ ] Create `.github/ISSUE_TEMPLATE/` for bug reports and features
- [ ] Create `.github/PULL_REQUEST_TEMPLATE.md`

## ✅ PRIORITY 7: Scientific Validation

### 7.1 Mass Balance Validation
- [ ] Run mass balance checks on all examples
- [ ] Verify errors < 1e-10 for typical systems
- [ ] Document any expected deviations
- [ ] Test edge cases (zero flows, empty processes)
- [ ] Verify `Consistency_Check()` passes
- [ ] Add mass balance validation to test suite

### 7.2 Scientific Accuracy
- [ ] Verify DSM lifetime calculations correct
- [ ] Verify FOMP decay calculations correct
- [ ] Check TC logic (Splitter vs Transformer)
- [ ] Validate elemental composition calculations
- [ ] Review initial stock handling
- [ ] Cross-reference with ODYM documentation

### 7.3 Uncertainty Quantification
- [ ] Verify Monte Carlo sampling correct
- [ ] Test sensitivity analysis accuracy
- [ ] Check distribution parameter handling
- [ ] Validate statistical outputs (mean, percentiles)
- [ ] Document uncertainty method in paper/docs

## ✅ PRIORITY 8: Final Pre-Publication Steps

### 8.1 Version Management
- [ ] Set version to `1.0.0` in `pyproject.toml`
- [ ] Update version references in documentation
- [ ] Create git tag: `v1.0.0`
- [ ] Write release notes for v1.0.0
- [ ] Plan versioning strategy for future releases

### 8.2 Publication Checklist
- [ ] All Priority 1-7 items completed
- [ ] Final test run: All tests pass
- [ ] Final notebook run: Master integration test passes
- [ ] Final documentation review
- [ ] Legal review: Licenses, attributions
- [ ] Create GitHub release with binaries/archives
- [ ] Register DOI via Zenodo or similar
- [ ] Announce on relevant channels (Twitter, LinkedIn, forums)

### 8.3 Post-Publication
- [ ] Monitor GitHub issues for first bug reports
- [ ] Respond to user questions promptly
- [ ] Plan v1.1 with bug fixes and minor improvements
- [ ] Begin work on v2.0 features (data reconciliation, multi-regional)

---

**Last Updated**: 2025-11-21

---

## 📊 Current Status Summary (2025-11-21)

### Overall Progress: ~75-80% Complete

**Major Accomplishments Since Last Update:**
- ✅ Template organization completed (2025-11-20)
- ✅ Pass-through process logic implemented (2025-11-20)
- ✅ ODYM compliance Phase 1a complete
- ✅ LICENSE file exists with proper ODYM attribution
- ✅ Comprehensive documentation (CLAUDE.md v3.1, USER_GUIDE.md, etc.)
- ✅ Code quality strong (12,536 lines, NumPy docstrings)

**Critical Blockers Identified:**
1. **Testing**: 3 test failures need resolution (test collection errors, import failures)
2. **Metadata**: Missing CONTRIBUTING.md, CITATION.cff, CHANGELOG.md, CODE_OF_CONDUCT.md
3. **Documentation**: Update dates, remove beta status, add badges
4. **GitHub**: Repository setup not yet done

**Recommended Completion Timeline:** 1-2 weeks

---
