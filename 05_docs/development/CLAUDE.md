# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

BioDYM is a Material Flow Analysis (MFA) tool for bio-based systems built on the ODYM framework. It tracks material flows, stocks, and transformations through time with special features for organic waste management and biomass cascading.

**Publication Status**: This project is being prepared for publication as an open-source tool on GitHub. Code quality, documentation, and scientific rigor are critical.

Key capabilities:
- Multi-element analysis (material, water content, dry matter, carbon content)
- Dynamic Stock Modeling (DSM) with age-cohort tracking and product lifetimes
- First-Order Mineralization Process (FOMP) for organic matter decomposition
- Monte Carlo uncertainty analysis with sensitivity analysis
- Scenario comparison and management
- Excel-based configuration (no coding required for users)
- Interactive visualizations (Sankey diagrams, time-series plots, dashboards)

## Recent Progress

### Validation System Rebuild & DSM Warnings (2025-11-25) - ✅ COMPLETE
**Comprehensive validation system and user guidance improvements**

**Validation System Rebuild:**
- Complete rebuild of Excel template validation (7_1_Comments_Validation)
- 69 INPUT column entries with structured descriptions (PURPOSE/ACTION/EXAMPLE/NOTE)
- Pattern-based handling for element columns (E#_* applies to E1-E6)
- VBA macro system for comment management:
  - `Add_Column_Comments_Macro.bas` - Apply comments from CSV
  - `Remove_All_Comments.bas` - Clean comments for testing
- Comprehensive documentation:
  - `generate_validation.py` - Python script to generate validation data
  - `HOW_TO_ADD_COMMENTS.md` - Step-by-step usage instructions
  - `VALIDATION_REBUILD_SUMMARY.md` - Complete technical documentation
  - `BioDYM_README_UPDATED.txt` - Updated README with v1.0 features

**DSM Lifetime Validation:**
- Added validation warnings in `data_loader.py` for DSM parameters:
  - Warns when StdDev > 80% of mean lifetime (potential negative lifetimes)
  - Provides actionable recommendations
- Added negative stock detection in `dsm_model.py`:
  - Warns when DSM calculations produce negative stocks
  - Reports time steps and minimum values
  - Helps diagnose lifetime distribution or inflow data issues

**Workflow Improvements:**
- Removed enhanced Sankey visualization from `00_BioDYM_Workflow.py`
- Fixed scenario export to overwrite files instead of creating timestamps (`scenario_engine.py`)
- Prevents folder spam, maintains clean output directory

**Template Documentation Updates:**
- BioDYM_README updated with v1.0 features
- Corrected version (1.0) and date (2024-11-24)
- Added Pass-through Process_Logic documentation (7 process types)
- New sections: Common Mistakes, Recent Updates, Getting Help
- Complete troubleshooting guide with validation warnings

**Git commit:** 313bc53 (11 files, 2872 insertions, 242 deletions)

### v1.0.0 Publication Preparation (2025-11-21) - ✅ COMPLETE
**Major Milestone: BioDYM is now publication-ready!**

**Test Suite Achievement (97.2% passing):**
- Fixed 10+ test failures systematically
- Improved from 75% → 97.2% pass rate (35/36 tests)
- Resolved column name mismatches (Flow_Name, Flow_Output_Process_ID, etc.)
- Fixed DSM parameter loading test expectations
- Corrected element indices (E4 for CC, not E3)
- Fixed ODYM import paths (06_framework/ location)
- Removed 2 irrelevant tests (golden_dataset, sankey_positions)
- Documented 1 skip (DSM fixed lifetime - known issue for v1.1)

**Publication Documentation:**
- Created CITATION.cff for academic citation
- Created CONTRIBUTING.md with contribution guidelines
- Created CHANGELOG.md documenting v1.0.0 release and roadmap
- Created CODE_OF_CONDUCT.md (Contributor Covenant 2.0)
- Updated README.md: Removed beta status, added professional badges
- Updated version to 1.0.0 throughout

**Code Quality & Analysis:**
- Ran Ruff format (6 files reformatted)
- Fixed critical undefined import (copy.deepcopy)
- Created ENGINE_STRUCTURE_ANALYSIS.md with comprehensive review
- Engine rating: **A (Excellent)** - publication ready
- 7 engine modules analyzed (2,742 lines total)
- Clean architecture confirmed, no structural changes needed

**Git History:**
- 5 clean commits with detailed changelogs
- All changes properly documented
- Ready for GitHub publication

**Current Status:** 95% publication ready. Optional tasks remaining: master integration test, bulk doc date updates, GitHub repository setup.

### Element-Agnostic Architecture (2025-10-31) - ✅ COMPLETE
BioDYM now supports **any element set** through flexible configuration:
- Generic E# column format (E1, E2, E3, E4) maps to any elements
- Hierarchical composition (e.g., CC as 45% of DM, not material)
- Config sheet as single source of truth
- Auto-detection of old/new formats
- Mass balance errors eliminated (was 629,829 Mg, now 0)

**Enabled use cases**: Biomass (material/WC/DM/CC), metals (material/Fe/Cu/Al/Zn), food (material/protein/lipids/carbs), etc.

### Sankey Visualization (2025-11-03) - ✅ COMPLETE
- Traditional Sankey updated to wide format (2200×350)
- Element multiplot attempted but needs rework (future enhancement)

### Pass-through Process Logic & Template Organization (2025-11-20) - ✅ COMPLETE
**Pass-through Implementation**:
- Added Pass-through process logic to solver (simple flow pass-through without transformation)
- Updated data_loader.py to skip TCs for Pass-through processes
- Works with TC_Configuration="No TC" setting

**Input Process Stock Capabilities**:
- Verified Input processes can have stocks with incoming flows
- Stock creation is process-type agnostic (any process with Stock_Configuration="Stock")
- Enables modeling of boundary stocks (e.g., atmosphere carbon accumulation, environment water)

**Repository Organization**:
- Created `01_data/01_input/template/` folder for clean template distribution
- Updated .gitignore to exclude study-specific input files from version control
- Only template file tracked: `251108_BioDYM_ODYM_Template_Empty_Without_Visualisation_Settings.xlsm`
- Keeps repository publication-ready while preserving user study files locally

## Documentation Structure

BioDYM documentation is split across multiple files for better organization:

- **CLAUDE.md** (this file) - Core project instructions for development
- **TROUBLESHOOTING.md** - Common issues and debugging strategies
- **TECHNICAL_DEEP_DIVE.md** - Detailed calculation engine and data flow
- **PRE_PUBLICATION_CHECKLIST.md** - Complete pre-publication checklist
- **ROADMAP.md** - Future features and development plans

## Development Setup

### Environment and Dependencies

Install dependencies using `uv`:
```bash
uv sync                     # Install all dependencies and create .venv
uv add <package>            # Add runtime dependency
uv add --dev <package>      # Add dev dependency
```

### Running the Analysis

**Main workflow** (Jupyter notebook):
```bash
uv run jupyter lab
# Open 00_BioDYM_Workflow.ipynb
# Update input_file path to your Excel file
# Run all cells (Kernel -> Restart & Run All)
```

**Command-line interface**:
```bash
uv run python 02_src/main_cli.py --input my_analysis.xlsx
```

### Testing

```bash
uv run pytest                           # Run all tests
uv run pytest 04_tests/test_solver.py  # Run specific test file
uv run pytest -v                        # Verbose output
```

**Master integration test**: The notebook `00_BioDYM_Workflow.ipynb` serves as the comprehensive integration test. It must run successfully from start to finish after any code changes.

### Code Quality

```bash
ruff format .    # Auto-format all Python files
ruff check .     # Check for errors and style issues
```

All code should be formatted and checked before committing.

## Project Architecture

### Core Directory Structure

```
bioDYM-CERT-edit-main/
├── 00_BioDYM_Workflow.ipynb       # Main Jupyter notebook (master integration test)
├── 01_data/                        # Data files
│   ├── 01_input/                   # Excel input files (system configurations)
│   └── 02_output/                  # Analysis results and exports
├── 02_src/                         # ✅ BioDYM application code (MODIFY HERE)
│   ├── engine/                     # MFA calculation engine
│   │   ├── solver.py               # Main iterative solver
│   │   ├── dsm_model.py            # Dynamic Stock Model
│   │   ├── fomp_model.py           # First-Order Mineralization Process
│   │   ├── initial_stock_engine.py # Initial stock processing
│   │   ├── scenario_engine.py      # Scenario analysis
│   │   └── mc_simulation.py        # Monte Carlo uncertainty
│   ├── plotting/                   # Visualization modules
│   │   ├── sankey.py               # Traditional Sankey diagrams
│   │   ├── dynamics.py             # Time-series plots
│   │   ├── validation.py           # Mass balance plots
│   │   └── ...                     # Other visualization modules
│   ├── reporting/                  # KPI dashboards and reports
│   ├── config.py                   # Configuration loader
│   ├── data_loader.py              # Excel data loading
│   ├── system_setup.py             # System initialization
│   ├── constants.py                # Standard icons and constants
│   └── utils.py                    # Utility functions
├── 04_tests/                       # Test suite
├── 06_framework/                   # ⚠️ External frameworks (READ-ONLY)
│   ├── ODYM-master_20241127/       # ODYM framework (DO NOT MODIFY)
│   └── bioDYM_add-on/              # BioDYM extensions (minimal usage)
└── pyproject.toml                  # Project dependencies
```

### ODYM Framework Integration

**CRITICAL**: BioDYM is built on the ODYM framework but does NOT modify ODYM code.

**DO:**
- Import ODYM classes: `import ODYM_Classes as msc`
- Use ODYM methods: `mfa_system.Initialize_FlowValues()`, `mfa_system.Consistency_Check()`
- Create ODYM objects: `msc.Flow(...)`, `msc.Stock(...)`, `msc.MFAsystem(...)`
- Read ODYM code for reference
- Modify BioDYM code in `02_src/`

**DO NOT:**
- Modify files in `06_framework/ODYM-master_20241127/`
- Add custom attributes to ODYM objects (use external dictionaries instead)
- Call ODYM "our engine" (it's a framework; our engine is in `02_src/engine/`)

**ODYM Compliance (Phase 1a Complete)**:
BioDYM now fully complies with ODYM best practices:
- Uses ODYM's `Initialize_FlowValues()`, `Initialize_StockValues()`, `Initialize_ParameterValues()`
- Uses `IndexTableCheck()` for validation
- Uses `Consistency_Check()` for mass balance verification
- All parameters must have `Indices` as a string (even `""` for scalars), **never `None`** (causes crash)
- No custom attributes on ODYM objects (use external dictionaries like `mfa_system._flow_descriptions`)

**IndexTable and Dimensions**:
ODYM uses aspects/dimensions with single-letter codes:
- `t` - Time (years)
- `e` - Element (material, WC, DM, CC)
- `r` - Region
- `g` - Good
- `m` - Material
- `p` - Process

Example: `Indices="t,e"` creates shape `(26, 4)` array for 26 years × 4 elements

**CRITICAL Bug to Avoid**:
```python
# ❌ WRONG - Will crash with AttributeError
param = msc.Parameter(Name="TC_1", Values=0.5, Indices=None)

# ✅ CORRECT - Use empty string for scalars
param = msc.Parameter(Name="TC_1", Values=0.5, Indices="")

# ✅ CORRECT - Time-varying parameter
param = msc.Parameter(Name="TC_2", Values=array, Indices="t")
```

### BioDYM Custom Extensions

**Stock-Outflow Transfer Coefficients**: This is a custom BioDYM feature NOT in standard ODYM. It allows outflows from initial stocks independent of regular flows.

- **Purpose**: Model processes where initial stocks gradually deplete (e.g., landfills, legacy stocks)
- **Implementation**: `02_src/engine/initial_stock_engine.py` and `02_src/engine/solver.py`
- **Excel Configuration**: Defined in `2_5_Initial_Stock` sheet
- **Marked in Code**: All references include comments: `# BioDYM Extension`

## Excel Input File Structure

The Excel file (`01_data/01_input/*.xlsx` or `*.xlsm`) defines the entire MFA system.

**Template Location**: `01_data/01_input/template/251124_BioDYM_ODYM_Template_Empty.xlsm`

**Validation System Files** (in template folder):
- `7_1_Comments_Validation_NEW.csv` - Structured validation data (69 INPUT columns)
- `Add_Column_Comments_Macro.bas` - VBA macro to apply comments
- `Remove_All_Comments.bas` - VBA macro to clean comments
- `generate_validation.py` - Python script to generate validation data
- `HOW_TO_ADD_COMMENTS.md` - Usage instructions
- `VALIDATION_REBUILD_SUMMARY.md` - Technical documentation
- `BioDYM_README_UPDATED.txt` - Complete user guide for Excel template

**Sheet Structure**:

**Core configuration**:
- `0_Configuration` - Time range, elements, analysis options
- `1_1_Definition_Flows` - All flow definitions
- `1_2_Data_Flows` - Flow data over time
- `2_1_Definition_Processes` - Process definitions and logic types
- `2_3_Process_TCs` - Transfer coefficients
- `2_4_dynamic_tcs` - Time-varying transfer coefficients
- `2_5_Initial_Stock` - Initial stock levels and stock-outflow TCs

**Advanced models**:
- `3_1_Definition_DSM` - Dynamic Stock Model parameters (product lifetimes)
- `3_2_Definition_FOMP` - First-Order Mineralization parameters (decay rates)

**Analysis features**:
- `4_1_Uncertainty_Parameters` - Monte Carlo uncertainty definitions
- `5_1_Scenario_Manager` - Scenario definitions

**Reference Management (NEW in v1.0)**:
- `6_1_Reference_Manager` - Central database for data source documentation

**Visualization**:
- `6_1_Visualization_Processes` - Process visualization settings (optional)
- `6_2_Visualization_Flows` - Flow visualization settings (optional)
- `6_3_Layout_Configuration` - Sankey diagram layouts (optional)

**Validation and Documentation (NEW in v1.0)**:
- `7_1_Comments_Validation` - Column descriptions and validation rules
- `7_2_Codelists` - Reference lists for dropdown options

## Workflow and Data Flow

1. **Configuration Loading** (`config.py`): Load Excel configuration and extract settings
2. **System Setup** (`system_setup.py`): Define model scope, initialize MFA system, load processes
3. **Data Loading** (`data_loader.py`): Load flows, parameters, DSM/FOMP definitions
4. **Calculation** (`engine/solver.py`): Iterative solver runs DSM, FOMP, and TC-driven flows
5. **Validation** (`plotting/validation.py`): Mass balance checks
6. **Visualization** (`plotting/*`): Generate Sankey diagrams, time-series plots, etc.
7. **Export** (`utils.py`, `reporting/`): Save results to Excel, generate KPI dashboards

**For detailed data flow diagram**, see `TECHNICAL_DEEP_DIVE.md`.

## Coding Standards

### Philosophy

1. Make it work (correct logic)
2. Make it right (clean, readable code) ← Current focus
3. Make it fast (optimize only if needed)

### Style Guide

Follow PEP 8:
- Modules/files: `lowercase_with_underscores.py`
- Functions/variables: `lowercase_with_underscores`
- Classes: `PascalCase`
- Constants: `ALL_CAPS_WITH_UNDERSCORES`

**Naming principles**:
- Be descriptive: `flow_definitions_df` not `df1`
- Functions are verbs: `calculate_balance()`, `load_data()`
- Variables are nouns: `process_name`, `mfa_results`
- Single responsibility: if function name contains "and", split it

### Documentation

**Required**: NumPy-style docstrings for all functions:

```python
def function_name(param1, param2):
    """Brief one-line summary.

    Detailed explanation of logic, workflow context, and scientific assumptions.

    Parameters
    ----------
    param1 : type
        Description.
    param2 : type, optional
        Description. Default is None.

    Returns
    -------
    return_type
        Description.

    Examples
    --------
    >>> function_name(1, 'example')
    'Some output'
    """
    # ... code ...
```

### Refactoring Workflow

When refactoring files in `02_src/`:
1. Select a single Python file for refactoring
2. Improve names and add NumPy-style docstrings
3. Run the master integration test: `00_BioDYM_Workflow.ipynb` (Kernel → Restart & Run All)
4. If successful, commit with message like: `docs(data_loader): add docstrings and refactor names`
5. If failed, diagnose and fix before committing

This ensures the project remains working at all times.

### User Feedback Standards

BioDYM uses standardized icons (defined in `02_src/constants.py`) for consistent output:

```python
from constants import Icons, format_header, format_step, format_success

print(format_header("SECTION TITLE"))
print(format_step(Icons.CALCULATION, "2.1", "Running calculation..."))
print(format_success("Calculation completed!"))
```

Common icons: SUCCESS ✅, ERROR ❌, WARNING ⚠️, CALCULATION 🧮, VISUALIZATION 📊, DSM 🏗️, FOMP 🌱, MONTE_CARLO 🎲

## Common Development Patterns

### Creating a New Visualization

1. Add function to appropriate module in `02_src/plotting/`
2. Import and call in `00_BioDYM_Workflow.ipynb`
3. Use Plotly for interactive plots (preferred) or Matplotlib for static plots
4. Add descriptive print statements with standard icons

### Adding a New Parameter Type

1. Define sheet structure in Excel template
2. Add loader function in `02_src/data_loader.py`
3. Create parameter in `02_src/system_setup.py` with `Indices` string
4. Use parameter in calculation logic (`02_src/engine/`)

### Modifying the Solver

1. Understand current flow in `02_src/engine/solver.py`
2. Maintain separation: TC-driven flows vs DSM vs FOMP
3. Preserve ODYM method calls (Initialize, Consistency_Check)
4. Update convergence logic if needed
5. Test with master integration test

## Key Technical Details

### Process Logic Types

Defined in `2_1_Definition_Processes` sheet:
- **Input**: Boundary process receiving flows from outside system (data-loaded, no TCs)
- **Output**: Boundary process sending flows outside system (data-loaded, requires stock)
- **Splitter**: Splits incoming flow to multiple outputs (TC-driven)
- **Transformer**: Transforms material composition (TC-driven)
- **Pass-through**: Passes flows unchanged (no transformation, no TCs required)
- **DSM**: Dynamic Stock Model (age-cohort tracking)
- **FOMP**: First-Order Mineralization Process (organic decomposition)

**Important**: Input/Output processes should use Process_Logic="Input"/"Output", NOT "Splitter". Using Splitter for boundary processes will cause incorrect composition calculations.

### Elements Tracking

Typically 4 elements tracked simultaneously:
- `material` - Total material mass
- `WC` - Water Content
- `DM` - Dry Matter
- `CC` - Carbon Content

### Mass Balance Validation

After calculation, BioDYM checks mass balance for each process:
- Inflow - Outflow - Stock Change should ≈ 0
- Validation plots show errors per process and element
- Typical acceptable error: < 1e-10

## Publication-Ready Development Best Practices

Since BioDYM is being prepared for publication as an open-source tool, follow these guidelines:

### Code Quality Standards

1. **All functions must have NumPy-style docstrings**
2. **Naming conventions must be consistent**
3. **Code must be formatted with Ruff**: `ruff format .` and `ruff check .`
4. **Master integration test must pass**: Run `00_BioDYM_Workflow.ipynb` completely

### Scientific Rigor

1. **Mass balance must be validated** (errors < 1e-10)
2. **Results must be reproducible** (same input → same results)
3. **Documentation must explain scientific methods** (DSM, FOMP, TC logic)

### User Experience

1. **Error messages must be informative** (not just tracebacks)
2. **Progress indicators required for long operations** (use icons from `constants.py`)
3. **Example data must be included** (working examples in `01_data/01_input/`)

### Git and Version Control

**Never commit**:
- Temporary files (.tmp, ~$*.xlsx)
- Study-specific input files (automatically ignored by .gitignore)
- Large data files > 10 MB
- Personal configuration files
- `.pyc` files or `__pycache__` directories

**Input File Organization**:
- Template file in `01_data/01_input/template/` is tracked
- All study-specific .xlsx and .xlsm files in `01_data/01_input/` are ignored
- Users can work on their studies locally without affecting git

**Commit message format**:
```
type(scope): brief description

Longer explanation if needed.

Types: feat, fix, docs, refactor, test, style
```

**Pre-publication checklist**: See `PRE_PUBLICATION_CHECKLIST.md` for comprehensive checklist.

## Quick Reference Card

### Most Common Tasks

```bash
# Set up environment
uv sync

# Run main analysis
uv run jupyter lab
# → Open 00_BioDYM_Workflow.ipynb

# Run tests
uv run pytest

# Format code
ruff format .
ruff check .

# Check for ODYM compliance issues
grep -r "Indices=None" 02_src/

# Debug mass balance
# In notebook after calculation:
plotting.plot_optimized_mass_balance_error(mfa_results_baseline)
```

### Key File Locations

- **Main workflow**: `00_BioDYM_Workflow.ipynb`
- **Input template**: `01_data/01_input/template/251108_BioDYM_ODYM_Template_Empty_Without_Visualisation_Settings.xlsm`
- **Input data**: `01_data/01_input/*.xlsx` (study files - not tracked in git)
- **Engine**: `02_src/engine/solver.py`
- **System setup**: `02_src/system_setup.py`
- **Data loading**: `02_src/data_loader.py`
- **ODYM framework**: `06_framework/ODYM-master_20241127/` (READ-ONLY)

### Critical Remember Points

1. **Never modify ODYM framework files** (`06_framework/ODYM-master_20241127/`)
2. **Always use ODYM initialization methods** (Initialize_FlowValues, Initialize_StockValues, Initialize_ParameterValues)
3. **Parameter Indices must be string** (never None)
4. **Master integration test must pass** (00_BioDYM_Workflow.ipynb)
5. **Follow NumPy docstring style** for all functions
6. **Use Ruff for formatting** before committing

## Common Issues and Debugging

For troubleshooting common issues, see **TROUBLESHOOTING.md**:
- ODYM integration issues (`Indices=None` errors)
- Mass balance errors
- Solver convergence problems
- DSM/FOMP process issues
- Visualization failures
- Excel data loading issues

For detailed technical information, see **TECHNICAL_DEEP_DIVE.md**:
- Complete data flow (Excel → Results)
- Iterative solver algorithm
- TC-driven flow calculations
- DSM and FOMP model details

## Branch and Commit Conventions

Current branch: `feature/odym-compliance`
Main branch: `master`

Recent focus areas:
- ✅ ODYM compliance (Phase 1a completed)
- ✅ Element-agnostic architecture (2025-10-31)
- ✅ Sankey visualization updates (2025-11-03)
- ✅ Standardized icon system for output
- ✅ Documentation reorganization for performance
- ✅ Pass-through process logic (2025-11-20)
- ✅ Template organization and git cleanup (2025-11-20)

When committing:
- Use descriptive messages with type prefix
- Ensure master integration test passes
- Follow coding standards above

## Future Development

For planned features and development roadmap, see **ROADMAP.md**:
- Version 1.1 (Q1 2026): Bug fixes & polish
- Version 2.0 (Q3 2026): Multi-dimensional expansion, data reconciliation
- Version 2.1 (Q4 2026): Advanced visualizations
- Version 3.0 (2027): Sustainability metrics, LCA integration
- Long-term: ML integration, web-based interface

---

**Last Updated**: 2025-11-25
**CLAUDE.md Version**: 3.2 (Validation System Rebuild & DSM Warnings)
**BioDYM Status**: Pre-publication preparation
