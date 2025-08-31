# BioDYM Tool - Workflow Visualization

## 📊 **Complete Workflow Overview**

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           BioDYM MFA Tool - Complete Workflow                      │
└─────────────────────────────────────────────────────────────────────────────────────┘

                                    📁 Excel Input File
                                    (250813_CS1_simple_V1.xlsx)
                                           │
                                           ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           STEP 1: Setup & Data Loading                            │
│                           Lines 32-195 | Function Usage: 0%                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  🔧 Environment Setup                    📊 Data Loading & Validation            │
│  • Import all modules                    • Load Excel file (22 sheets)            │
│  • Set Python paths                      • Validate required sheets (5)           │
│  • Configure plotting                     • Extract time range (2025-2050)        │
│  • Add ODYM framework                    • Detect features (DSM/FOMP/MC)          │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           STEP 2: Calculation & Validation                        │
│                           Lines 200-450 | Function Usage: 80%                    │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  🚀 Model Initialization               ⚖️ Mass Balance Validation               │
│  • Define model scope                  • Check all processes                     │
│  • Initialize MFA system               • Validate mass balance errors            │
│  • Load processes & data               • Create error visualizations             │
│  • Load parameters (DSM/FOMP/MC)      • Generate Sankey diagrams                │
│  • Define flows & parameters           • Display results overview                │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           STEP 3: Visualization                                   │
│                           Lines 450-576 | Function Usage: 90%                    │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  📊 System Overview                    📈 Individual Process Analysis            │
│  • Interactive Sankey diagrams         • DSM process analysis                   │
│  • Process dynamics analysis           • FOMP process analysis                  │
│  • Stock levels bar charts             • Stock composition analysis             │
│  • Multi-process selection             • Flow dynamics analysis                 │
│  • Export options                      • Interactive features                    │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           STEP 4: Export                                          │
│                           Lines 576-675 | Function Usage: 95%                    │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  💾 Results Export                     🎲 Monte Carlo Analysis                  │
│  • Export to Excel                     • Run MC simulation (if enabled)         │
│  • Configuration summary               • Create histogram plots                 │
│  • Analysis summary                    • Generate tornado plots                  │
│  • File organization                   • Sensitivity analysis                   │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                                    📁 Output Files
                                    • results_scientific.xlsx
                                    • results_scientific_config.xlsx
```

## 🔄 **Data Flow Diagram**

```
Excel File (22 sheets)
    │
    ├── 0_Configuration (30 settings) ──┐
    │                                   │
    ├── 1_1_Definition_Flows ──────────┤
    │                                   │
    ├── 1_2_Data_Flows ────────────────┤
    │                                   │
    ├── 2_1_Definition_Processes ──────┤
    │                                   │
    ├── 2_3_Process_TCs ───────────────┤
    │                                   │
    ├── 2_4_Initial_Stock ─────────────┤
    │                                   │
    ├── 2_5_dynamic_tcs ───────────────┤
    │                                   │
    ├── 3_1_Definition_DSM ────────────┤
    │                                   │
    ├── 3_2_Definition_FOMP ───────────┤
    │                                   │
    ├── 4_1_Uncertainty_Parameters ────┤
    │                                   │
    └── 5_1_Scenario_Manager ──────────┘
                                    │
                                    ▼
                            pd.read_excel()
                                    │
                                    ▼
                            input_data dictionary
                                    │
                                    ▼
                    ┌─────────────────────────────────┐
                    │        BioDYM Engine            │
                    │  ┌─────────────────────────┐    │
                    │  │   system_setup.*        │    │
                    │  │   • define_model_scope  │    │
                    │  │   • initialize_mfa      │    │
                    │  │   • load_processes      │    │
                    │  └─────────────────────────┘    │
                    │  ┌─────────────────────────┐    │
                    │  │   data_loader.*         │    │
                    │  │   • load_dsm_params     │    │
                    │  │   • load_fomp_params    │    │
                    │  │   • load_uncertainty    │    │
                    │  └─────────────────────────┘    │
                    │  ┌─────────────────────────┐    │
                    │  │   solver.*              │    │
                    │  │   • run_mfa_calculation │    │
                    │  └─────────────────────────┘    │
                    └─────────────────────────────────┘
                                    │
                                    ▼
                            MFA System with Results
                                    │
                                    ▼
                    ┌─────────────────────────────────┐
                    │      Visualization Engine       │
                    │  ┌─────────────────────────┐    │
                    │  │   plotting.*            │    │
                    │  │   • Sankey diagrams     │    │
                    │  │   • Process dynamics    │    │
                    │  │   • Stock charts        │    │
                    │  │   • DSM/FOMP analysis   │    │
                    │  └─────────────────────────┘    │
                    └─────────────────────────────────┘
                                    │
                                    ▼
                    ┌─────────────────────────────────┐
                    │       Export Engine             │
                    │  ┌─────────────────────────┐    │
                    │  │   utils.*               │    │
                    │  │   • export_results      │    │
                    │  └─────────────────────────┘    │
                    │  ┌─────────────────────────┐    │
                    │  │   Monte Carlo           │    │
                    │  │   • run_mc_simulation   │    │
                    │  │   • create visualizations│    │
                    │  └─────────────────────────┘    │
                    └─────────────────────────────────┘
                                    │
                                    ▼
                            Output Files & Results
```

## 📈 **Function Usage Timeline**

```
Timeline: 0% → 80% → 90% → 95%
           │     │     │     │
           │     │     │     └── Step 4: Export (utils.*, MC)
           │     │     └──────── Step 3: Visualization (plotting.*)
           │     └────────────── Step 2: Calculation (system_setup.*, data_loader.*, solver.*)
           └──────────────────── Step 1: Setup (standard library only)
```

## 🎯 **Module Activation Pattern**

```
Step 1: Setup (0% BioDYM usage)
├── Standard library: os, sys, pandas, numpy, matplotlib, plotly
└── BioDYM modules: ❌ NOT USED

Step 2: Calculation (80% BioDYM usage)
├── system_setup.*: ✅ ACTIVATED
├── data_loader.*: ✅ ACTIVATED  
├── solver.*: ✅ ACTIVATED
├── plotting.*: ✅ PARTIALLY ACTIVATED
├── utils.*: ❌ NOT USED
└── config.*: ❌ NOT USED

Step 3: Visualization (90% BioDYM usage)
├── plotting.*: ✅ FULLY ACTIVATED
├── system_setup.*: ❌ NOT USED
├── data_loader.*: ❌ NOT USED
├── solver.*: ❌ NOT USED
├── utils.*: ❌ NOT USED
└── config.*: ❌ NOT USED

Step 4: Export (95% BioDYM usage)
├── utils.*: ✅ ACTIVATED
├── Monte Carlo: ✅ ACTIVATED
├── plotting.*: ❌ NOT USED
├── system_setup.*: ❌ NOT USED
├── data_loader.*: ❌ NOT USED
├── solver.*: ❌ NOT USED
└── config.*: ❌ NOT USED
```

## 🚨 **Current Issues & Opportunities**

### **Issues:**
1. **`config` module imported but never used** - Configuration sheet ignored
2. **Hardcoded values** instead of using Excel configuration
3. **All modules imported at start** - No lazy loading

### **Opportunities:**
1. **Use configuration sheet** for dynamic settings
2. **Implement lazy imports** for better performance
3. **Replace hardcoded values** with config-driven values

---

*Workflow Visualization Created: 2025-08-31*
*Status: ✅ COMPLETE - Ready for cleanup planning*
