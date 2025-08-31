# BioDYM Tool - Essential Knowledge Summary

## 🎯 **Core Purpose & Function**
**BioDYM** is a Material Flow Analysis (MFA) tool built on the ODYM framework, specifically designed for bio-based systems. It provides a complete workflow from data input through calculation, visualization, and export.

## 🏗️ **Architecture Overview**

### **Main Components:**
1. **Scientific Notebook** (`BioDYM_Scientific_Notebook.py`) - Main user interface and workflow orchestrator
2. **Core Engine** (`src/engine/`) - MFA calculation engine with solver, DSM, FOMP, and Monte Carlo
3. **Data Management** (`src/data_loader.py`, `src/system_setup.py`) - Excel data loading and system initialization
4. **Visualization** (`src/plotting/`) - Comprehensive plotting and analysis tools
5. **Utilities** (`src/utils.py`) - Export, parameter sampling, and helper functions

### **Key Features:**
- **Dynamic Stock Modeling (DSM)** - Material aging and product lifetime modeling
- **First-Order Mineralization Process (FOMP)** - Organic matter decomposition simulation
- **Monte Carlo Simulation** - Uncertainty quantification and sensitivity analysis
- **Interactive Visualizations** - Sankey diagrams, process dynamics, stock charts
- **Excel-based Configuration** - Comprehensive data input and configuration management

## 🔄 **Workflow Structure (4 Steps)**

### **Step 1: Setup & Data Loading (Lines 32-195)**
- **Purpose**: Environment preparation and data validation
- **Function Usage**: 0% BioDYM modules (standard library only)
- **Key Activities**: Import modules, set paths, load Excel file, validate sheets
- **Excel Usage**: 8 sheets for validation and feature detection

### **Step 2: Calculation & Validation (Lines 200-450)**
- **Purpose**: MFA calculation execution and mass balance verification
- **Function Usage**: 80% BioDYM modules (core calculation)
- **Key Activities**: Model initialization, MFA calculation, mass balance validation
- **Excel Usage**: 8+ sheets for heavy data processing
- **Key Functions**: `system_setup.*`, `data_loader.*`, `solver.*`

### **Step 3: Visualization (Lines 450-576)**
- **Purpose**: Comprehensive analysis and exploration
- **Function Usage**: 90% BioDYM modules (plotting heavy)
- **Key Activities**: System overview, process analysis, component analysis
- **Excel Usage**: 3 sheets (process definitions + parameters)
- **Key Functions**: `plotting.*` (all major plotting functions)

### **Step 4: Export (Lines 576-675)**
- **Purpose**: Results export and Monte Carlo analysis
- **Function Usage**: 95% BioDYM modules (utils activated)
- **Key Activities**: Results export, configuration export, MC simulation
- **Excel Usage**: All sheets (comprehensive export)
- **Key Functions**: `utils.*`, Monte Carlo functions

## 📊 **Excel Data Structure**

### **Core Data Sheets (Required):**
- `1_1_Definition_Flows` - Flow definitions and connections
- `1_2_Data_Flows` - Flow data over time
- `2_1_Definition_Processes` - Process definitions
- `2_3_Process_TCs` - Transfer coefficients
- `2_4_Initial_Stock` - Initial stock values
- `2_5_dynamic_tcs` - Dynamic transfer coefficients

### **Parameter Sheets (Optional):**
- `3_1_Definition_DSM` - Dynamic Stock Model parameters
- `3_2_Definition_FOMP` - First-Order Mineralization Process parameters
- `4_1_Uncertainty_Parameters` - Monte Carlo uncertainty definitions

### **Configuration Sheet:**
- `0_Configuration` - 30 settings for model configuration (currently unused)

## 🔧 **Key Functions & Usage Patterns**

### **High-Usage Functions:**
1. **`system_setup.define_model_scope()`** - Define analysis scope
2. **`system_setup.initialize_mfa_system()`** - Initialize MFA system
3. **`solver.run_mfa_calculation()`** - Execute MFA calculation
4. **`plotting.plot_interactive_sankey()`** - Create Sankey diagrams
5. **`utils.export_results_to_excel()`** - Export results

### **Function Usage Rate: 86% (6/7 modules used)**
- **Used**: `data_loader`, `system_setup`, `solver`, `plotting`, `utils`, `engine.mc_simulation`
- **Unused**: `config` (imported but never called)

## 🚨 **Current Issues & Optimization Opportunities**

### **Immediate Issues:**
1. **`config` module imported but never used** - Configuration sheet ignored
2. **Hardcoded values** instead of using Excel configuration
3. **All modules imported at start** - No lazy loading

### **Optimization Opportunities:**
1. **Configuration Integration** - Use Excel config sheet for dynamic settings
2. **Lazy Imports** - Import modules only when needed
3. **Function Consolidation** - Remove legacy and duplicate functions

## 📁 **File Organization**

### **Main Files:**
- `BioDYM_Scientific_Notebook.py` - Main workflow (675 lines)
- `data/01_input/250813_CS1_simple_V1.xlsx` - Primary input file (22 sheets)
- `src/` - Core Python modules
- `docs/toc_analysis/` - Complete analysis documentation

### **Output Files:**
- `data/02_output/results_scientific.xlsx` - Main results
- `data/02_output/results_scientific_config.xlsx` - Configuration summary

## 🎯 **Configuration Management**

### **Current State:**
- **Excel Config Sheet**: 30 settings available but ignored
- **Hardcoded Values**: Time range (2025-2050), elements, features
- **Config Module**: Functions available but never called

### **Target State:**
- **Dynamic Configuration**: All settings from Excel config sheet
- **Flexible Parameters**: Time range, elements, features configurable
- **Integrated Management**: Config module actively used

## 🚀 **Development Status**

### **Completed:**
- ✅ Complete workflow analysis (4/4 steps)
- ✅ Function usage mapping
- ✅ Excel data structure analysis
- ✅ Workflow visualization
- ✅ Function structure analysis

### **Next Steps:**
1. **Phase 1**: Remove unused code (`config` import, legacy functions)
2. **Phase 2**: Optimize imports (lazy loading, organization)
3. **Phase 3**: Configuration integration (Excel config usage)

## 🔑 **Critical Knowledge for AI Usage**

### **When Working with BioDYM:**
1. **Always check the 4-step workflow** - Each step has specific function usage patterns
2. **Excel data is central** - 22 sheets with specific purposes and usage patterns
3. **Configuration integration is key** - Excel config sheet should drive settings
4. **Function usage is phased** - Modules activate progressively through workflow
5. **Monte Carlo is optional** - Only runs when uncertainty parameters available

### **Common Patterns:**
- **Setup**: Standard library only
- **Calculation**: Heavy use of `system_setup`, `data_loader`, `solver`
- **Visualization**: Heavy use of `plotting` functions
- **Export**: Heavy use of `utils` and Monte Carlo functions

### **Key Constraints:**
- **ODYM Framework Dependency** - Core calculations depend on ODYM
- **Excel Input Requirement** - All data must come through Excel files
- **Python Path Setup** - Multiple framework paths must be configured
- **Memory Management** - Large datasets require efficient processing

---

*Essential Knowledge Summary Created: 2025-08-31*  
*Purpose: AI Context Optimization & Future Development*  
*Status: ✅ COMPLETE - Ready for Context Cleanup*
