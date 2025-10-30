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

Run tests with pytest:
```bash
uv run pytest                           # Run all tests
uv run pytest 04_tests/test_solver.py  # Run specific test file
uv run pytest -v                        # Verbose output
```

Test structure:
- `04_tests/` - Main test directory
- `04_tests/unit/` - Unit tests
- `04_tests/integration/` - Integration tests
- `04_tests/conftest.py` - Pytest configuration and fixtures

**Master integration test**: The notebook `00_BioDYM_Workflow.ipynb` serves as the comprehensive integration test. It must run successfully from start to finish after any code changes.

### Code Quality

Format and lint with Ruff:
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
│   ├── plotting/                   # Visualization modules
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

### Engine Modules (`02_src/engine/`)

The engine is the heart of the calculation system:

- `solver.py` - Main MFA solver with iterative convergence
- `dsm_model.py` - Dynamic Stock Model calculations (product lifetimes)
- `fomp_model.py` - First-Order Mineralization Process (organic decomposition)
- `initial_stock_engine.py` - Initial stock processing
- `scenario_engine.py` - Scenario analysis and comparison
- `mc_simulation.py` - Monte Carlo uncertainty simulation

### Plotting Modules (`02_src/plotting/`)

- `sankey.py` - Traditional Sankey diagrams
- `enhanced_sankey.py` - Enhanced Sankey with custom layouts
- `graphviz_flow_charts.py` - System structure visualization
- `dynamics.py` - Time-series plots (processes, flows, stocks)
- `validation.py` - Mass balance validation plots
- `monte_carlo.py` - Monte Carlo result visualizations
- `composition.py` - Flow composition analysis
- `scenario.py` - Scenario comparison plots

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
- **Excel Configuration**: Defined in `2_5_Initial_Stock` sheet with columns:
  - `Stock_Outflow_TC`: Unique ID for stock-outflow TC
  - `Destination_Process`: Process receiving the outflow
  - `Annual_Consumption_Rate`: Fraction consumed per year (e.g., 0.1 = 10%/year)
- **Marked in Code**: All references to this feature include comments: `# BioDYM Extension`

## Complete Data Flow: Excel → Results

Understanding how data flows through BioDYM is critical for debugging and development.

### Data Flow Diagram

```
Excel Input File (.xlsx/.xlsm)
         ↓
[1] Configuration Loading (config.py)
    - 0_Configuration sheet → config_obj
    - Extract time range, elements, scenarios, MC settings
         ↓
[2] System Setup (system_setup.py)
    - define_model_scope() → Create IndexTable with dimensions
    - initialize_mfa_system() → Create empty MFAsystem object
         ↓
[3] Process & Stock Definition (system_setup.py)
    - load_and_define_processes() reads 2_1_Definition_Processes
    - Creates msc.Process() for each row
    - Creates msc.Stock() for processes with Stock_Configuration="Stock"
    - Calls mfa_system.Initialize_StockValues()
         ↓
[4] Flow Definition (system_setup.py → _initialize_flows)
    - Reads 1_1_Definition_Flows
    - Creates msc.Flow() for each flow with P_Start, P_End
    - Calls mfa_system.Initialize_FlowValues() → All flows = np.zeros((T, E))
         ↓
[5] Primary Flow Data (system_setup.py → _populate_primary_flow_data)
    - Reads 1_2_Data_Flows
    - Populates flow.Values[:, 0] (material column) with time-series data
         ↓
[6] Initial Stock Loading (system_setup.py → _apply_initial_stock)
    - Reads 2_5_Initial_Stock
    - Sets S_pid.Values[0, :] for processes with initial stocks
    - Creates stock-outflow flows (BioDYM extension)
         ↓
[7] Content Parameters (system_setup.py → _define_content_parameters)
    - Reads WC[%], DM[%], CC_DM[%] from 1_1_Definition_Flows
    - Creates msc.Parameter() for each (e.g., "WC_F_01")
    - Calls mfa_system.Initialize_ParameterValues()
         ↓
[8] Elemental Composition (_calculate_elemental_compositions)
    - For each flow: flow.Values[:, 1] = flow.Values[:, 0] * WC%
    - For each flow: flow.Values[:, 2] = flow.Values[:, 0] * DM%
    - For each flow: flow.Values[:, 3] = flow.Values[:, 0] * CC%
         ↓
[9] TC Parameter Loading (data_loader.py)
    - load_tc_parameters() reads 2_2_static_TCs and 2_3_dynamic_TCs
    - Creates Parameters for transfer coefficients
    - Dynamic TCs: interpolates between data points
         ↓
[10] DSM Parameter Loading (data_loader.py)
     - load_dsm_parameters() reads 3_1_Definition_DSM
     - Extracts lifetimes, inflow splits, output splits
         ↓
[11] FOMP Parameter Loading (data_loader.py)
     - load_fomp_parameters() reads 3_2_Definition_FOMP
     - Extracts decay rates, labile fractions
         ↓
[12] ITERATIVE SOLVER (engine/solver.py → run_mfa_calculation)
     - Loop until convergence (max 30 iterations):
       a. _calculate_tc_driven_flows() - Splitter & Transformer processes
       b. update_initial_stock_flows_during_solver() - Stock-outflow TCs
       c. _calculate_dsm_flows() - DSM processes (if enabled)
       d. _calculate_fomp_flows() - FOMP processes (if enabled)
       e. Check convergence: if no flows changed, break
         ↓
[13] Final Balance Calculation (solver.py → calculate_final_balances)
     - For each process: dS = sum(inflows) - sum(outflows)
     - For each process: S[t] = S[0] + cumsum(dS[0:t-1])
     - Calls mfa_system.Consistency_Check()
         ↓
[14] Visualization & Export
     - plotting/* modules create interactive plots
     - utils.export_results_to_excel() saves to Excel
     - kpi_dashboard.generate_kpi_dashboard() creates KPI summaries
```

### Example: How a Single Flow is Calculated

**User Input in Excel** (`1_1_Definition_Flows` and `1_2_Data_Flows`):
```
Flow_ID: F_01_02
Flow_Name: "Wheat Straw to Processing"
Flow_Output_Process_ID: 1 (Harvest)
Input_Process_ID: 2 (Processing)
Flow_WC[%]: 0.15 (15% water content)
Flow_DM[%]: 0.85 (85% dry matter)
Flow_CC_DM[%]: 0.45 (45% carbon in dry matter)

Time-series data in 1_2_Data_Flows:
Year 2000: 1000 Mg
Year 2001: 1100 Mg
Year 2002: 1200 Mg
...
```

**Code Processing**:
```python
# Step 1: Flow creation (system_setup.py line 339)
flow_obj = msc.Flow(Name="F_01_02", P_Start=1, P_End=2, Indices="t,e")
mfa_system.FlowDict["F_01_02"] = flow_obj

# Step 2: Initialize to zeros (system_setup.py line 352)
mfa_system.Initialize_FlowValues()
# Result: flow_obj.Values = np.zeros((26, 4))  # 26 years × 4 elements

# Step 3: Populate material column (system_setup.py line 373)
flow_obj.Values[:, 0] = [1000, 1100, 1200, ...]  # From 1_2_Data_Flows

# Step 4: Create content parameters (system_setup.py line 416-422)
mfa_system.ParameterDict["WC_F_01_02"] = msc.Parameter(Name="WC_F_01_02", Values=0.15, Indices="")
mfa_system.ParameterDict["DM_F_01_02"] = msc.Parameter(Name="DM_F_01_02", Values=0.85, Indices="")
mfa_system.ParameterDict["CC_F_01_02"] = msc.Parameter(Name="CC_F_01_02", Values=0.45, Indices="")

# Step 5: Calculate elemental composition (system_setup.py line 438-443)
flow_obj.Values[:, 1] = flow_obj.Values[:, 0] * 0.15  # WC = [150, 165, 180, ...]
flow_obj.Values[:, 2] = flow_obj.Values[:, 0] * 0.85  # DM = [850, 935, 1020, ...]
flow_obj.Values[:, 3] = flow_obj.Values[:, 0] * 0.45  # CC = [382.5, 420.75, 459, ...]

# Final result:
# flow_obj.Values shape: (26, 4)
# [:, 0] = material (total mass)
# [:, 1] = water content
# [:, 2] = dry matter
# [:, 3] = carbon content
```

## Calculation Engine Deep Dive

### Iterative Solver Algorithm

The solver (`02_src/engine/solver.py → run_mfa_calculation()`) uses an iterative convergence approach:

**Why Iterative?**
- Processes depend on each other's outputs as inputs
- DSM and FOMP processes have feedback loops
- TC-driven flows depend on total inflows (which may include DSM/FOMP outputs)
- System must converge to a stable solution

**Algorithm** (max 30 iterations):
```python
1. for iteration in range(30):
2.     something_changed = False
3.
4.     # Calculate TC-driven flows (Splitter, Transformer)
5.     tc_changed = _calculate_tc_driven_flows(...)
6.     something_changed |= tc_changed
7.
8.     # Update initial stock outflows (BioDYM extension)
9.     update_initial_stock_flows_during_solver(mfa_system)
10.
11.    # Calculate DSM processes (if enabled)
12.    if RUN_DSM_CALCULATION:
13.        dsm_changed, dsm_details = _calculate_dsm_flows(...)
14.        something_changed |= dsm_changed
15.
16.    # Calculate FOMP processes (if enabled)
17.    if RUN_FOMP_CALCULATION:
18.        fomp_changed = _calculate_fomp_flows(...)
19.        something_changed |= fomp_changed
20.
21.    # Check convergence
22.    if not something_changed:
23.        print(f"Converged after {iteration + 1} iterations")
24.        break
25.
26. # Final balance calculation
27. calculate_final_balances(mfa_system)
```

**Convergence Criteria**:
- Iteration completes with NO flow values changing
- Uses `np.allclose(old_values, new_values)` to compare
- Typically converges in 3-10 iterations
- Warning if max iterations reached (30)

### TC-Driven Flow Calculation

**Splitter Process** (divides material between outputs):
```python
# Total inflow to process
total_inflow = sum(all_incoming_flows)

# Apply transfer coefficient
outflow_material = total_inflow_material * TC_value

# Preserve composition (WC, DM, CC fractions stay the same)
outflow_WC = outflow_material * (inflow_WC / inflow_material)
outflow_DM = outflow_material * (inflow_DM / inflow_material)
outflow_CC = outflow_material * (inflow_CC / inflow_material)
```

**Transformer Process** (changes elemental composition):
```python
# Apply element-specific TCs
outflow_WC = total_inflow_WC * TC_WC
outflow_DM = total_inflow_DM * TC_DM
outflow_CC = total_inflow_CC * TC_CC

# Recalculate total material
outflow_material = outflow_WC + outflow_DM
```

### Dynamic Stock Model (DSM) Details

**Purpose**: Model products with defined lifetimes that gradually exit the stock.

**Calculation Flow** (`02_src/engine/dsm_model.py`):
```python
1. Split incoming flow by categories (e.g., 70% short-lived, 30% long-lived)
2. For each category:
   - Create age-cohort stock structure
   - Apply lifetime distribution (Normal, Weibull, Fixed)
   - Calculate outflow based on cohort aging
3. Handle initial stock with simplified decay (1/mean_lifetime per year)
4. Combine all category outflows
5. Split combined outflow by output destinations
```

**Key Parameters** (from `3_1_Definition_DSM`):
- `Inflow_Split_[%]`: How to split incoming material (e.g., [0.7, 0.3])
- `Lifetime_Type`: Normal, Weibull, Fixed, Folded_Normal
- `Lifetime_Mean`: Average lifetime in years
- `Lifetime_StdDev`: Standard deviation (for Normal/Weibull)
- `Output_Split`: How to split outflows to destinations

**Example**:
```
Process: Wood Products (ID=5)
Inflow: 1000 Mg/year
Categories:
  - Short-lived (70%): Mean=5 years, StdDev=2 years
  - Long-lived (30%): Mean=25 years, StdDev=10 years
Output destinations: 50% to Recycling, 50% to Incineration

Result: Age-cohort tracking with lifetime-based outflows
```

### First-Order Mineralization Process (FOMP) Details

**Purpose**: Model organic matter decomposition in soil/compost with two decay pools.

**Two-Pool Model** (`02_src/engine/fomp_model.py`):
```python
# Labile pool: fast-decaying (months to years)
# Recalcitrant pool: slow-decaying (years to decades)

For each year t:
    1. Split incoming DM between pools:
       - Labile inflow = DM_inflow * f_labile
       - Recalcitrant inflow = DM_inflow * (1 - f_labile)

    2. Calculate decay (analytical solution):
       - Decay_labile = Stock_labile * (1 - exp(-k_labile))
       - Decay_recalcitrant = Stock_recalcitrant * (1 - exp(-k_recalcitrant))

    3. Update stocks:
       - Stock_labile[t] = Stock_labile[t-1] - Decay_labile + Labile_inflow
       - Stock_recalcitrant[t] = Stock_recalcitrant[t-1] - Decay_recalcitrant + Recalcitrant_inflow

    4. Calculate outputs:
       - CO2 outflow = Total_decay * cc_dm
       - Environmental outflow = Total_decay * (1 - cc_dm)
```

**Key Parameters** (from `3_2_Definition_FOMP`):
- `f_labile`: Fraction going to labile pool (e.g., 0.7 = 70%)
- `k_labile`: Decay rate for labile pool (year⁻¹, e.g., 0.3 = 30%/year)
- `k_recalcitrant`: Decay rate for recalcitrant pool (year⁻¹, e.g., 0.02 = 2%/year)
- `cc_dm`: Carbon fraction in dry matter (e.g., 0.45 = 45%)

**Dynamic Composition**: FOMP uses the dynamic composition of incoming flows (calculated in solver based on actual inflow mix).

## Common Troubleshooting Patterns

### Issue: `AttributeError: 'NoneType' object has no attribute 'split'`

**Cause**: Parameter created with `Indices=None` instead of `Indices=""`.

**Location**: Happens in `Initialize_ParameterValues()` at ODYM line 231.

**Solution**:
```python
# ❌ WRONG
param = msc.Parameter(Name="TC_1", Values=0.5, Indices=None)

# ✅ CORRECT
param = msc.Parameter(Name="TC_1", Values=0.5, Indices="")  # Empty string for scalars
```

**Finding Culprits**: Search for `Indices=None` in `02_src/`:
```bash
grep -r "Indices=None" 02_src/
```

### Issue: Mass Balance Errors / Inconsistent Results

**Symptoms**:
- Large errors in mass balance plots
- `Consistency_Check()` warnings
- Unexpected stock levels

**Common Causes**:

1. **Missing TC definitions**: Flow has no corresponding TC in Excel
   - Check `flow_tc_map` for missing flows
   - Verify `2_2_static_TCs` or `2_3_dynamic_TCs` sheets

2. **Incorrect Process_Logic**: Process type doesn't match its actual role
   - Verify `Process_Logic` column in `2_1_Definition_Processes`
   - Common mistake: DSM process marked as "Splitter"

3. **Initial stock issues**: Initial stock doesn't match first-year balance
   - Check `2_5_Initial_Stock` values
   - Verify stock-outflow TCs aren't depleting too fast

4. **Element composition errors**: WC% + DM% ≠ 100%
   - Check `Flow_WC[%]` and `Flow_DM[%]` columns
   - Water + Dry Matter should sum to ~1.0 (100%)

**Debugging Steps**:
```python
# 1. Check specific process balance
process_id = 5
inflows = [f for f in mfa_system.FlowDict.values() if f.P_End == process_id]
outflows = [f for f in mfa_system.FlowDict.values() if f.P_Start == process_id]
print(f"Inflows: {sum(f.Values[:, 0].sum() for f in inflows)}")
print(f"Outflows: {sum(f.Values[:, 0].sum() for f in outflows)}")

# 2. Check stock levels
if f"S_{process_id}" in mfa_system.StockDict:
    print(f"Stock: {mfa_system.StockDict[f'S_{process_id}'].Values[:, 0]}")

# 3. Run consistency check
try:
    mfa_system.Consistency_Check()
except Exception as e:
    print(f"Consistency error: {e}")
```

### Issue: Solver Not Converging

**Symptoms**: Warning "System did not converge after 30 iterations"

**Common Causes**:

1. **Circular dependencies**: Process A depends on B, B depends on C, C depends on A
   - Review process connections in Excel
   - Check for feedback loops

2. **Transfer coefficient > 1.0**: TC values should be ≤ 1.0 (fractions)
   - Check `TC_Value_material` columns
   - Common mistake: Using percentages instead of decimals (50 instead of 0.50)

3. **Dynamic TC oscillation**: Time-varying TCs causing instability
   - Review `2_3_dynamic_TCs` for abrupt changes
   - Consider smoothing TC transitions

**Debugging**:
- Add iteration counter: solver prints "[DSM DEBUG] Iteration X"
- Check which flows are still changing at iteration 30
- Increase `max_iterations` temporarily to see if it eventually converges

### Issue: DSM Process Not Calculating

**Symptoms**: DSM process has zero outflows despite having inflows

**Common Causes**:

1. **Missing DSM definition**: Process_ID not in `3_1_Definition_DSM`
2. **Incorrect lifetime parameters**: Mean/StdDev values unrealistic
3. **Missing inflow**: enhanced_input_validation() returns False

**Debugging**:
```python
# Check DSM parameters
print(f"DSM Params: {dsm_params}")
print(f"Process {process_id} in DSM params: {process_id in dsm_params}")

# Check inflows
inflows = [f for f in mfa_system.FlowDict.values() if f.P_End == process_id]
print(f"Inflows to DSM {process_id}: {[f.Name for f in inflows]}")
print(f"Total inflow sum: {sum(np.sum(f.Values) for f in inflows)}")
```

**Solution**: Verify `3_1_Definition_DSM` has entries for the process and lifetimes are reasonable (> 0).

### Issue: FOMP Process Missing Carbon Outflow

**Symptoms**: FOMP process has stock but no CO2 emissions

**Common Causes**:

1. **Missing FOMP outflow flow definitions**: Need flows for both carbon and environmental outputs
2. **Zero decay rates**: k_labile or k_recalcitrant = 0
3. **Missing `_fomp_protected` attribute**: Outflow flows not marked as FOMP-protected

**Solution**:
- Verify 2 outflow flows exist for FOMP process (one for CO2, one for environment)
- Check `3_2_Definition_FOMP` for decay rate parameters
- Verify flows have `_fomp_protected` attribute set in `fomp_model.py`

### Issue: Plotting Errors / Visualization Failures

**Common Causes**:

1. **Missing process/flow names**: Descriptive names not in Excel
2. **Graphviz limits exceeded**: Too many processes/flows for visualization
3. **Empty data**: Trying to plot processes with no activity

**Solutions**:
- Check `_flow_descriptions` dict exists: `mfa_system._flow_descriptions`
- Increase Graphviz limits in `02_src/plotting/graphviz_flow_charts.py` (currently 50 processes, 100 flows)
- Filter out zero-flow processes before plotting

### Issue: Excel File Changes Not Reflected

**Symptom**: Modified Excel values but results unchanged

**Common Causes**:

1. **Excel file cache**: Jupyter kernel holding old data in memory
2. **Wrong file path**: Loading old file instead of modified one
3. **Cached .pyc files**: Python bytecode not updated

**Solutions**:
```python
# 1. Restart Jupyter kernel
# Kernel → Restart & Run All

# 2. Verify file path
print(f"Loading: {input_file}")
print(f"File exists: {os.path.exists(input_file)}")
print(f"Last modified: {os.path.getmtime(input_file)}")

# 3. Clear Python cache
import sys
if '02_src' in sys.modules:
    del sys.modules['02_src']
```

### Issue: Monte Carlo Simulation Fails

**Common Causes**:

1. **Missing uncertainty definitions**: No entries in `4_1_Uncertainty_Parameters`
2. **Invalid distribution parameters**: StdDev < 0 or inappropriate ranges
3. **Memory issues**: Too many iterations for large systems

**Solutions**:
- Check `4_1_Uncertainty_Parameters` sheet exists and has valid entries
- Verify distribution parameters (Mean, StdDev, Min, Max) are reasonable
- Reduce MC iterations in configuration (e.g., 1000 → 100 for testing)

### General Debugging Strategy

1. **Start Simple**: Run baseline calculation first (no MC, no scenarios)
2. **Check Logs**: Read print statements carefully - they contain diagnostic info
3. **Verify Data**: Use `pd.read_excel()` to inspect Excel sheets directly
4. **Isolate Issues**: Comment out DSM/FOMP to isolate TC-driven flow problems
5. **Use Master Test**: `00_BioDYM_Workflow.ipynb` must run successfully
6. **Check Units**: All mass units should be consistent (typically Mg)

### When to Ask for Help

If you've tried the above and still have issues, provide:
1. Full error traceback
2. Excel file structure (sheet names, key columns)
3. Process IDs and flow IDs involved
4. Configuration settings (time range, elements, enabled features)
5. Steps to reproduce

## Excel Input File Structure

The Excel file (`01_data/01_input/*.xlsx` or `*.xlsm`) defines the entire MFA system:

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

**Visualization**:
- `6_1_Visualization_Processes` - Process visualization settings
- `6_2_Visualization_Flows` - Flow visualization settings
- `6_3_Layout_Configuration` - Sankey diagram layouts

## Workflow and Data Flow

1. **Configuration Loading** (`config.py`): Load Excel configuration and extract settings
2. **System Setup** (`system_setup.py`): Define model scope, initialize MFA system, load processes
3. **Data Loading** (`data_loader.py`): Load flows, parameters, DSM/FOMP definitions
4. **Calculation** (`engine/solver.py`): Iterative solver runs DSM, FOMP, and TC-driven flows
5. **Validation** (`plotting/validation.py`): Mass balance checks
6. **Visualization** (`plotting/*`): Generate Sankey diagrams, time-series plots, etc.
7. **Export** (`utils.py`, `reporting/`): Save results to Excel, generate KPI dashboards

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
- **Splitter**: Splits incoming flow to multiple outputs (TC-driven)
- **Transformer**: Transforms material composition (TC-driven)
- **DSM**: Dynamic Stock Model (age-cohort tracking)
- **FOMP**: First-Order Mineralization Process (organic decomposition)

### Elements Tracking

Typically 4 elements tracked simultaneously:
- `material` - Total material mass
- `WC` - Water Content
- `DM` - Dry Matter
- `CC` - Carbon Content

### Index Convention

ODYM uses single-letter indices in `Indices` strings:
- `t` - Time
- `e` - Element
- `r` - Region
- `g` - Good
- `m` - Material
- `p` - Process

Example: `Indices="t,e"` creates a 2D array with shape `(num_years, num_elements)`

### Mass Balance Validation

After calculation, BioDYM checks mass balance for each process:
- Inflow - Outflow - Stock Change should ≈ 0
- Validation plots show errors per process and element
- Typical acceptable error: < 1e-10

## Branch and Commit Conventions

Current branch: `feature/odym-compliance` (ODYM compliance improvements)
Main branch: `master`

Recent focus areas:
- ODYM compliance (Phase 1a completed)
- Standardized icon system for output
- Graphviz visualization improvements
- Documentation and architecture analysis

When committing:
- Use descriptive messages
- Prefix with type: `docs:`, `feat:`, `fix:`, `refactor:`
- Reference issues if applicable
- Ensure master integration test passes

## Publication-Ready Development Best Practices

Since BioDYM is being prepared for publication as an open-source tool, follow these guidelines:

### Code Quality Standards

1. **All functions must have NumPy-style docstrings**
   - One-line summary
   - Detailed explanation
   - Parameters section with types
   - Returns section
   - Examples (where helpful)

2. **Naming conventions must be consistent**
   - Descriptive names (no `df`, `temp`, `x`)
   - Functions use verbs: `calculate_balance()`, `load_data()`
   - Variables use nouns: `flow_definitions`, `mfa_results`

3. **Code must be formatted with Ruff**
   ```bash
   ruff format .
   ruff check .
   ```

4. **Master integration test must pass**
   - Run `00_BioDYM_Workflow.ipynb` completely
   - All cells execute without errors
   - Results are scientifically correct

### Scientific Rigor

1. **Mass balance must be validated**
   - Errors < 1e-10 for typical systems
   - Consistency checks must pass
   - Document any expected deviations

2. **Results must be reproducible**
   - Same Excel input → Same results
   - Random seeds for Monte Carlo
   - Version dependencies locked (pyproject.toml)

3. **Documentation must explain scientific methods**
   - DSM: Lifetime distributions, age-cohort tracking
   - FOMP: Two-pool decay model, analytical solution
   - TC logic: Splitter vs Transformer behavior

### User Experience

1. **Error messages must be informative**
   ```python
   # ❌ BAD
   raise ValueError("Invalid parameter")

   # ✅ GOOD
   raise ValueError(f"Parameter 'TC_01_02' not found in ParameterDict. "
                    f"Available parameters: {list(mfa_system.ParameterDict.keys())[:5]}...")
   ```

2. **Progress indicators required for long operations**
   - Use standard icons from `constants.py`
   - Print step numbers: "[1.1]", "[2.3]"
   - Show completion status: "✅ Complete", "⚠️ Warning"

3. **Example data must be included**
   - Template file: `250625_Template_CS0.xlsx`
   - Working example: `250922_CS1_Wheat_Straw.xlsx`
   - Sample outputs in `01_data/02_output/`

### Git and Version Control

1. **Never commit**:
   - Temporary files (.tmp, ~$*.xlsx)
   - Large data files > 10 MB (use .gitignore)
   - Personal configuration files
   - `.pyc` files or `__pycache__` directories

2. **Always commit**:
   - Source code changes in `02_src/`
   - Documentation updates
   - Test files in `04_tests/`
   - Example Excel files (if reasonable size)

3. **Commit message format**:
   ```
   type(scope): brief description

   Longer explanation if needed.

   - Bullet points for multiple changes
   - Reference issues: Fixes #123
   ```

   Types: `feat`, `fix`, `docs`, `refactor`, `test`, `style`

### Testing Before Publication

**Pre-publication checklist**:
- [ ] All tests pass (`uv run pytest`)
- [ ] Master integration test passes (00_BioDYM_Workflow.ipynb)
- [ ] All code has docstrings
- [ ] Ruff formatting applied
- [ ] README.md is comprehensive
- [ ] Example data files included
- [ ] User guide updated (`05_docs/USER_GUIDE.md`)
- [ ] License file present (MIT)
- [ ] Requirements locked (pyproject.toml, uv.lock)
- [ ] No sensitive data in repo
- [ ] GitHub repository description and tags set

### Common Pre-Publication Issues

1. **Hardcoded file paths**:
   ```python
   # ❌ BAD
   input_file = "C:/Users/Johannes/data/file.xlsx"

   # ✅ GOOD
   input_file = "01_data/01_input/file.xlsx"  # Relative path
   ```

2. **Print statements without icons**:
   ```python
   # ❌ BAD
   print("Calculation complete")

   # ✅ GOOD
   print(format_success("Calculation complete"))
   ```

3. **Magic numbers**:
   ```python
   # ❌ BAD
   if value > 1e-10:

   # ✅ GOOD
   MASS_BALANCE_TOLERANCE = 1e-10
   if value > MASS_BALANCE_TOLERANCE:
   ```

### Help for Future Contributors

When opening issues or requesting features:
- **Bug reports**: Provide error traceback, Excel file structure, steps to reproduce
- **Feature requests**: Explain use case, provide example data if possible
- **Questions**: Check CLAUDE.md and USER_GUIDE.md first

When submitting pull requests:
- Create from feature branch (not master)
- Include tests for new functionality
- Update documentation
- Run full test suite
- Follow coding standards above

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
- **Input data**: `01_data/01_input/*.xlsx`
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

---

## Pre-Publication Checklist

This comprehensive checklist ensures BioDYM v1.0 is publication-ready. Track progress systematically before releasing on GitHub.

### ✅ PRIORITY 1: Critical Blockers (Must Fix Before Publication)

**1.1 Fix Testing Suite**
- [ ] Fix test collection errors in `03_studies/Casestudy_2_Wood/test_*.py`
  - Error: Missing file `251006_Yield_Calculation_Wood.py`
  - Action: Fix paths or exclude from pytest with `norecursedirs`
- [ ] Fix test collection error in `04_tests/integration/test_comprehensive_features.py`
  - Error: Import failures
  - Action: Debug import chain or fix module dependencies
- [ ] Verify all 35 tests pass: `uv run pytest`
- [ ] Check test coverage: `uv run pytest --cov=02_src`
- [ ] Document any expected test failures with clear justification

**1.2 Update LICENSE File**
- [ ] Update copyright holder: "Johannes Scholz (BioDYM Development Team)"
- [ ] Update copyright year: 2025
- [ ] Add ODYM attribution section with:
  - Link to ODYM repository: https://github.com/IndEcol/ODYM
  - Citation: Pauliuk, S., Heeren, N. (2020). ODYM framework. Journal of Industrial Ecology, 24(3), 446-458.
  - DOI: https://doi.org/10.1111/jiec.12952
- [ ] Verify MIT license terms are complete
- [ ] Consider adding CONTRIBUTORS.md file listing all contributors

**1.3 Delete Unused/Conflicted Files**
- [ ] Delete: `README (conflicted copy 2025-10-21 140428).md`
- [ ] Delete: `01_data/01_input/~$251027_BioDYM_ODYM.xlsm` (Excel temp file)
- [ ] Run cleanup search: `find . -name "*conflicted*" -o -name "~$*" -o -name "*.tmp" -o -name "*.bak"`
- [ ] Remove any files found by cleanup search
- [ ] Verify `.gitignore` prevents future temp file commits

### ✅ PRIORITY 2: Documentation Quality (Essential for Users)

**2.1 README.md Review**
- [ ] Update project status (remove "beta" references)
- [ ] Verify installation instructions work from scratch
- [ ] Add proper ODYM citation in acknowledgments
- [ ] Update "Last updated" date
- [ ] Add badges: License, Python version, build status
- [ ] Verify all example commands work
- [ ] Add "Getting Help" section with issue tracker link
- [ ] Include example output screenshots/figures

**2.2 USER_GUIDE.md Review**
- [ ] Verify all sections are current and complete
- [ ] Test all tutorial examples work
- [ ] Add troubleshooting section from CLAUDE.md
- [ ] Include Excel template structure documentation
- [ ] Add FAQ section for common questions
- [ ] Verify all screenshots/figures are up-to-date

**2.3 Code Documentation Audit**
- [ ] Run docstring completeness check: `grep -r "^def " 02_src/ --include="*.py" | wc -l`
- [ ] Verify all functions have NumPy-style docstrings
- [ ] Check module-level docstrings in all `.py` files
- [ ] Verify docstring examples are correct
- [ ] Update any outdated parameter descriptions
- [ ] Remove placeholder docstrings ("TODO: Add description")

**2.4 Fix TODO/FIXME Markers**
- [ ] Review TODOs in `02_src/data_loader.py`
- [ ] Search entire codebase: `grep -r "# TODO\|# FIXME\|# HACK\|# XXX" 02_src/`
- [ ] Either implement, document, or remove each TODO
- [ ] Convert critical TODOs to GitHub issues for v1.1+

### ✅ PRIORITY 3: Visual Quality (Publication Standards)

**3.1 Unified Figure Styling**
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

**3.2 Sankey Visualization Improvements**
- [ ] Review layout algorithm in `enhanced_sankey.py`
- [ ] Test with complex systems (20+ processes, 50+ flows)
- [ ] Verify `6_3_Layout_Configuration` Excel sheet usage
- [ ] Implement manual node positioning overrides
- [ ] Add automatic layout optimization option
- [ ] Document layout best practices in USER_GUIDE.md
- [ ] Fix any overlapping nodes/flows issues

### ✅ PRIORITY 4: Code Quality (Professional Standards)

**4.1 Code Quality Sweep**
- [ ] Check for hardcoded paths: `grep -r "C:/" 02_src/ --include="*.py"`
- [ ] Check for hardcoded paths: `grep -r "/Users/" 02_src/ --include="*.py"`
- [ ] Check for debug prints: `grep -r "print(\"DEBUG" 02_src/ --include="*.py"`
- [ ] Find commented code blocks: `grep -r "^# def " 02_src/ --include="*.py"`
- [ ] Run Ruff format: `ruff format 02_src/`
- [ ] Run Ruff check: `ruff check 02_src/`
- [ ] Fix all Ruff warnings and errors
- [ ] Verify no secrets/API keys in code

**4.2 Error Handling Review**
- [ ] Audit all Excel loading for try/except blocks
- [ ] Verify error messages are informative (not just tracebacks)
- [ ] Test error handling with malformed Excel files
- [ ] Add user-friendly error messages with next steps
- [ ] Test graceful degradation when optional features fail
- [ ] Document expected error scenarios in USER_GUIDE.md

**4.3 Performance Testing**
- [ ] Test with large system (50+ processes, 100+ flows)
- [ ] Measure Monte Carlo performance (1000 iterations)
- [ ] Profile solver convergence time
- [ ] Document system requirements (RAM, CPU) in README
- [ ] Identify and document performance bottlenecks
- [ ] Add performance tips to documentation

### ✅ PRIORITY 5: Example Data & Reproducibility

**5.1 Verify Example Files**
- [ ] Test `250922_CS1_Wheat_Straw.xlsx` runs completely
- [ ] Test `250625_Template_CS0.xlsx` is clean and functional
- [ ] Verify sample outputs in `01_data/02_output/` are current
- [ ] Check example files for sensitive/personal data
- [ ] Ensure example files have proper documentation
- [ ] Add README in `01_data/01_input/` explaining examples
- [ ] Test examples on fresh Python environment

**5.2 Master Integration Test**
- [ ] Run `00_BioDYM_Workflow.ipynb` completely (Kernel → Restart & Run All)
- [ ] Verify all cells execute without errors
- [ ] Check all visualizations render correctly
- [ ] Verify exported results are scientifically correct
- [ ] Test with both `.xlsx` and `.xlsm` input files
- [ ] Document expected runtime in notebook

**5.3 Reproducibility Checks**
- [ ] Same input → same results (deterministic)
- [ ] Set random seeds for Monte Carlo
- [ ] Lock dependencies in `pyproject.toml` and `uv.lock`
- [ ] Test on fresh environment: `uv sync` from scratch
- [ ] Document Python version requirements (currently ≥3.12)
- [ ] Test on different OS (Windows/Mac/Linux if possible)

### ✅ PRIORITY 6: Repository Metadata (GitHub Publication)

**6.1 Git Repository Cleanup**
- [ ] Review `.gitignore` completeness
- [ ] Verify no large files (>10 MB) committed
- [ ] Check no `.pyc` or `__pycache__` directories tracked
- [ ] Remove any committed temp files
- [ ] Clean up commit history if needed (squash/rebase)
- [ ] Ensure no sensitive data in git history

**6.2 GitHub Repository Setup**
- [ ] Set repository description (1-2 sentence summary)
- [ ] Add topics/tags: `mfa`, `material-flow-analysis`, `odym`, `python`, `jupyter`, `sustainability`, `circular-economy`
- [ ] Enable GitHub Issues
- [ ] Enable GitHub Discussions (optional)
- [ ] Set up GitHub Pages for documentation (optional)
- [ ] Configure branch protection rules for `master`

**6.3 Additional Files**
- [ ] Add `CONTRIBUTING.md` with contribution guidelines
- [ ] Add `CITATION.cff` for academic citation format
- [ ] Add `CHANGELOG.md` documenting version history
- [ ] Add `CODE_OF_CONDUCT.md` (optional but recommended)
- [ ] Create `.github/ISSUE_TEMPLATE/` for bug reports and features
- [ ] Create `.github/PULL_REQUEST_TEMPLATE.md`

### ✅ PRIORITY 7: Scientific Validation

**7.1 Mass Balance Validation**
- [ ] Run mass balance checks on all examples
- [ ] Verify errors < 1e-10 for typical systems
- [ ] Document any expected deviations
- [ ] Test edge cases (zero flows, empty processes)
- [ ] Verify `Consistency_Check()` passes
- [ ] Add mass balance validation to test suite

**7.2 Scientific Accuracy**
- [ ] Verify DSM lifetime calculations correct
- [ ] Verify FOMP decay calculations correct
- [ ] Check TC logic (Splitter vs Transformer)
- [ ] Validate elemental composition calculations
- [ ] Review initial stock handling
- [ ] Cross-reference with ODYM documentation

**7.3 Uncertainty Quantification**
- [ ] Verify Monte Carlo sampling correct
- [ ] Test sensitivity analysis accuracy
- [ ] Check distribution parameter handling
- [ ] Validate statistical outputs (mean, percentiles)
- [ ] Document uncertainty method in paper/docs

### ✅ PRIORITY 8: Final Pre-Publication Steps

**8.1 Version Management**
- [ ] Set version to `1.0.0` in `pyproject.toml`
- [ ] Update version references in documentation
- [ ] Create git tag: `v1.0.0`
- [ ] Write release notes for v1.0.0
- [ ] Plan versioning strategy for future releases

**8.2 Publication Checklist**
- [ ] All Priority 1-7 items completed
- [ ] Final test run: All tests pass
- [ ] Final notebook run: Master integration test passes
- [ ] Final documentation review
- [ ] Legal review: Licenses, attributions
- [ ] Create GitHub release with binaries/archives
- [ ] Register DOI via Zenodo or similar
- [ ] Announce on relevant channels (Twitter, LinkedIn, forums)

**8.3 Post-Publication**
- [ ] Monitor GitHub issues for first bug reports
- [ ] Respond to user questions promptly
- [ ] Plan v1.1 with bug fixes and minor improvements
- [ ] Begin work on v2.0 features (data reconciliation, multi-regional)

---

## Future Features (Document, Don't Implement for v1.0)

### Multi-Dimensional Expansion (v2.0)

**Current State**: 2D system (Time × Element)

**Required for Additional Dimensions** (e.g., Region):
```python
# 1. Update system_setup.py → define_model_scope()
model_classification["Region"] = msc.Classification(
    Name="Regions", Dimension="Region", ID=3, Items=regions
)

# 2. Update IndexTable
aspects.append("Region")
index_letters.append("r")

# 3. Update all Indices strings
# Before: Indices="t,e"  → shape (T, E)
# After:  Indices="t,e,r" → shape (T, E, R)

# 4. CRITICAL: All array operations must handle 3D+
# Affected: solver.py, dsm_model.py, fomp_model.py, all plotting
# Estimate: 2-4 weeks of refactoring
```

**Recommendation**:
- ✅ Architecture is ODYM-compliant and ready
- ❌ Don't implement before v1.0 (scope creep risk)
- ✅ Document in roadmap for v2.0

### Data Reconciliation Module (v2.0)

**Status**: Excellent implementation plan exists in `IMPLEMENTATION_PLAN_DATA_RECONCILIATION.md`

**Recommendation**:
- **Don't implement before v1.0** - Major feature (4-6 weeks)
- **Keep implementation plan** - Well-designed for future
- **Mention in roadmap** - Show planned development
- **Reference in paper** - "Future work will include statistical data reconciliation..."

**Key Features Planned**:
- Constrained weighted least-squares optimization
- Gross error detection with statistical diagnostics
- Integration with Monte Carlo uncertainty
- Phase 1-4 implementation strategy already defined

---

**Last Updated**: 2025-10-30
**CLAUDE.md Version**: 2.1 (Publication-Ready with Checklist)
**BioDYM Status**: Pre-publication preparation - Use checklist above to track progress
