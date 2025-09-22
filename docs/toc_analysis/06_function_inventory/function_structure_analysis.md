# BioDYM Tool - Function Structure Analysis

## 📋 Overview

**Analysis Date**: 2025-08-31  
**Purpose**: Examine existing function structure and organization  
**Status**: ✅ COMPLETED

## 🗂️ **Module Structure Overview**

```
src/
├── __init__.py                    # Package initialization
├── config.py                      # Configuration management (7565 bytes)
├── data_loader.py                 # Data loading functions (9329 bytes)
├── main.py                        # Main application entry (7934 bytes)
├── main_cli.py                    # Command-line interface (13144 bytes)
├── mfa_engine.py                  # MFA calculation engine (1865 bytes)
├── system_setup.py                # System initialization (13750 bytes)
├── utils.py                       # Utility functions (24269 bytes)
├── engine/                        # Calculation engine modules
│   ├── dsm_model.py              # Dynamic Stock Model (5869 bytes)
│   ├── fomp_model.py             # First-Order Mineralization Process (2186 bytes)
│   ├── mc_simulation.py          # Monte Carlo simulation (4456 bytes)
│   └── solver.py                 # Main solver (10090 bytes)
└── plotting/                      # Visualization modules
    ├── __init__.py               # Plotting package initialization
    ├── dynamics.py               # Process dynamics plotting (46359 bytes)
    ├── graphviz_flow_charts.py   # Graphviz-based flow charts (28737 bytes)
    ├── mc_visuals.py            # Monte Carlo visualizations (8132 bytes)
    ├── monte_carlo.py           # Monte Carlo plotting (10763 bytes)
    ├── sankey.py                # Sankey diagram creation (11683 bytes)
    ├── scenario.py              # Scenario comparison plotting (3588 bytes)
    ├── utils.py                 # Plotting utilities (1936 bytes)
    └── validation.py            # Validation plotting (6157 bytes)
```

## 🔍 **Function Inventory by Module**

### **1. config.py (7565 bytes)**
**Purpose**: Configuration management and Excel configuration loading

#### **Main Functions:**
- `load_config_from_excel(excel_file_path)` - Load config from Excel
- `get_default_config()` - Get default configuration values
- `create_config_object(config_dict)` - Create config object from dict
- `load_configuration(excel_file_path=None)` - Load config with fallback

#### **Status**: ✅ **USED** in entry points and MC simulation
The configuration module is actively used by `src/main.py`, `src/main_cli.py`, and `engine/mc_simulation.py` to load settings from Excel and drive model behavior.

### **2. data_loader.py (9329 bytes)**
**Purpose**: Load and process data from Excel files

#### **Main Functions:**
- `load_flow_definitions(all_excel_data)` - Load flow definitions
- `load_process_definitions(all_excel_data)` - Load process definitions
- `load_transfer_coefficients(all_excel_data)` - Load transfer coefficients
- `load_initial_stocks(all_excel_data)` - Load initial stock values
- `load_dsm_parameters(all_excel_data)` - Load DSM parameters
- `load_fomp_parameters(all_excel_data)` - Load FOMP parameters
- `load_uncertainty_definitions(all_excel_data)` - Load uncertainty parameters
- `load_codelists(all_excel_data)` - Load code lists

#### **Status**: ✅ **USED** in Step 2 (Calculation)

### **3. system_setup.py (13750 bytes)**
**Purpose**: System initialization and setup

#### **Main Functions:**
- `define_model_scope(start_year, end_year, elements)` - Define model scope
- `initialize_mfa_system(model_classification, index_table)` - Initialize MFA system
- `load_and_define_processes(mfa_system_base, input_file, data_loader)` - Load processes
- `define_flows_and_parameters(mfa_system_base, all_excel_data)` - Define flows
- `create_dynamic_tc_parameters(dynamic_tc_sheet, time_items)` - Create dynamic TCs

#### **Status**: ✅ **USED** in Step 2 (Calculation)

### **4. engine/solver.py (10090 bytes)**
**Purpose**: Main MFA calculation solver

#### **Main Functions:**
- `run_mfa_calculation(mfa_system_configured, dsm_params, fomp_params, config)` - Run MFA calculation

#### **Status**: ✅ **USED** in Step 2 (Calculation)

### **5. plotting/__init__.py (2937 bytes)**
**Purpose**: Plotting package initialization and function exports

#### **Exported Functions:**
- `plot_interactive_sankey()` - Interactive Sankey diagrams
- `plot_process_dynamics()` - Process dynamics analysis
- `plot_dynamic_stock_composition()` - DSM stock composition
- `plot_fomp_stock_details()` - FOMP process analysis
- `plot_flow_dynamics()` - Flow dynamics analysis
- `plot_stock_bar_chart()` - Stock bar charts
- `plot_mass_balance_error()` - Mass balance error plots
- `plot_interactive_mc_histogram()` - MC histogram plots
- `plot_interactive_tornado()` - MC tornado plots

#### **Status**: ✅ **USED** in Steps 2-3 (Calculation & Visualization)

### **6. utils.py (24269 bytes)**
**Purpose**: Utility functions for data processing and export

#### **Main Functions:**
- `export_results_to_excel(mfa_system_results, output_path)` - Export results to Excel
- `sample_parameters(uncertainty_params)` - Sample parameters for MC
- `create_parameter_samples(uncertainty_params, n_samples)` - Create MC samples
- `export_uncertainty_results(mc_results, output_path)` - Export MC results
- `create_summary_statistics(data)` - Create statistical summaries

#### **Status**: ✅ **USED** in Step 4 (Export)

### **7. engine/mc_simulation.py (4456 bytes)**
**Purpose**: Monte Carlo simulation engine

#### **Main Functions:**
- `run_mc_simulation(mfa_system_configured, input_data, dsm_params, fomp_params, config)` - Run MC simulation

#### **Status**: ✅ **USED** in Step 4 (Export)

## 📊 **Function Usage Analysis**

### **Functions Actually Used in Scientific Notebook:**
1. **system_setup.*** (5 functions) - Step 2
2. **data_loader.*** (3 functions) - Step 2
3. **solver.run_mfa_calculation()** (1 function) - Step 2
4. **plotting.*** (8+ functions) - Steps 2-3
5. **utils.export_results_to_excel()** (1 function) - Step 4
6. **run_mc_simulation()** (1 function) - Step 4

### **Functions Imported but Never Used:**
None critical. The `config` module is used to load Excel-based settings.

### **Functions Available but Not Imported:**
1. **utils.sample_parameters()** - Parameter sampling for MC
2. **utils.create_parameter_samples()** - MC sample creation
3. **utils.export_uncertainty_results()** - MC result export
4. **utils.create_summary_statistics()** - Statistical summaries

## 🚨 **Current Issues**

### **1. Configuration Integration Status (Revised)**
- **Excel config sheet**: 30 settings available
- **config module**: Used to read Excel config (active)
- **Notebook/CLI**: Import and use config; continue to reduce any remaining hardcoded defaults
- **Result**: Configuration sheet drives settings; minimize legacy hardcoding

### **2. Import Organization**
- **All modules imported at start** - No lazy loading
- **Unused imports** - `config` module imported but never used
- **Function availability** - Some utils functions not imported

### **3. Function Duplication**
- **Legacy functions** in plotting/__init__.py
- **Multiple export functions** in utils.py
- **Similar functionality** across different modules

## 🎯 **Optimization Opportunities**

### **1. Configuration Integration**
```python
# Current (hardcoded):
start_year = 2025
end_year = 2050
elements = ['material', 'WC', 'DM', 'CC']

# Proposed (config-driven):
config_dict = config.load_config_from_excel(input_file)
start_year = config_dict.get('Start Year', 2025)
end_year = config_dict.get('End Year', 2050)
elements = config_dict.get('Elements (comma-separated)', 'material,WC,DM,CC').split(',')
```

### **2. Lazy Imports**
```python
# Current (all at start):
import config, data_loader, system_setup, utils
from engine import solver
from src import plotting

# Proposed (lazy loading):
def load_config():
    import config
    return config.load_config_from_excel(input_file)

def run_calculation():
    from engine import solver
    return solver.run_mfa_calculation(...)
```

### **3. Function Consolidation**
- **Remove legacy functions** from plotting/__init__.py
- **Consolidate export functions** in utils.py
- **Standardize function naming** across modules

## 📈 **Function Efficiency Metrics**

| **Metric** | **Current** | **Target** | **Improvement** |
|------------|-------------|------------|-----------------|
| **Functions Imported** | 7 modules | 6 modules | -14% |
| **Functions Actually Used** | 6 modules | 6 modules | 0% |
| **Unused Functions** | 1 module | 0 modules | -100% |
| **Configuration Integration** | 0% | 100% | +100% |
| **Lazy Loading** | 0% | 50% | +50% |

## 🚀 **Next Steps for Cleanup**

### **Phase 1: Remove Unused Code**
1. **Remove legacy plotting functions** already deprecated
2. **Clean up duplicate functions** in utils.py

### **Phase 2: Optimize Imports**
1. **Implement lazy imports** for heavy modules
2. **Organize imports** by usage pattern
3. **Add import validation** for missing modules

### **Phase 3: Configuration Integration**
1. **Implement config loading** in notebook
2. **Replace hardcoded values** with config values
3. **Add config validation** and error handling

---

*Function Structure Analysis Completed: 2025-08-31*  
*Status: ✅ COMPLETE - Ready for cleanup implementation*
