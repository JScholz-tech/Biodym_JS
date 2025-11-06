# BioDYM Technical Deep Dive

Detailed technical documentation of BioDYM's calculation engine and data flow.

## Table of Contents

- [Complete Data Flow](#complete-data-flow)
- [Calculation Engine](#calculation-engine)
- [Process Models](#process-models)

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

## Calculation Engine

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

## Process Models

### Dynamic Stock Model (DSM)

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

### First-Order Mineralization Process (FOMP)

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

---

**Last Updated**: 2025-11-04
