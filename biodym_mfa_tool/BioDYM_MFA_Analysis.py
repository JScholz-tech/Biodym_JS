# -*- coding: utf-8 -*-
"""
BioDYM MFA Analysis Tool - Python Script Version

This script provides the same functionality as the Jupyter notebook but can be
run as individual cells in Jupyter. Copy and paste each section into separate
Jupyter cells.

Instructions:
1. Copy each section below into separate Jupyter cells
2. Run the cells in order
3. Modify the configuration in the second cell as needed
"""

# ==============================================================================
# CELL 1: Setup and Imports
# ==============================================================================
"""
Copy this entire section into your first Jupyter cell:
"""

# Import required libraries
import os
import sys
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# Add project paths - Jupyter notebook version
# Get the current working directory (where the notebook is located)
current_dir = os.getcwd()
src_path = os.path.join(current_dir, 'src')
sys.path.insert(0, src_path)

# Add ODYM framework path (adjust as needed)
project_root_parent = os.path.dirname(current_dir)
odym_path = os.path.join(project_root_parent, 'framework', 'ODYM-master_20241127', 'odym', 'modules')
sys.path.insert(0, odym_path)

# Import BioDYM modules
try:
    import config
    import data_loader
    import system_setup
    import utils
    from engine import solver
    import plotting
    import ODYM_Classes as msc
    print("✅ All modules imported successfully!")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please check your installation and paths.")
    raise

# ==============================================================================
# CELL 2: Data and Configuration Setup
# ==============================================================================


# ==============================================================================
# GOLDEN DATASET: Minimal End-to-End Test & Visualization
# ==============================================================================

import os
import sys
import pandas as pd
import numpy as np

# Add project and ODYM framework paths
current_dir = os.getcwd()
src_path = os.path.join(current_dir, 'src')
sys.path.insert(0, src_path)
project_root_parent = os.path.dirname(current_dir)
odym_path = os.path.join(project_root_parent, 'framework', 'ODYM-master_20241127', 'odym', 'modules')
sys.path.insert(0, odym_path)

# Import BioDYM modules
import config, data_loader, system_setup
from engine import solver
import plotting

# Set path to golden dataset
golden_path = 'test_data/golden_dataset.xlsx'

# --- Define config as a class instance ---
class AnalysisConfig:
    def __init__(self):
        self.excel_file_path = golden_path
        self.output_path = 'data/02_output/results.xlsx'
        self.start_year = 2025
        self.end_year = 2030
        self.elements = ['material', 'WC', 'DM', 'CC']
        self.run_monte_carlo = False
        self.mc_iterations = 100
        self.RUN_DSM_CALCULATION = False
        self.RUN_FOMP_CALCULATION = True

config = AnalysisConfig()
print("✅ Config loaded:", vars(config))

# Load and validate data
input_data = pd.read_excel(config.excel_file_path, sheet_name=None, header=0, engine='openpyxl', na_values=['N.A.', 'NA', 'n/a'])
data_loader.validate_input_data(input_data)
print("✅ Data validation passed!")

# Model setup
model_classification, index_table = system_setup.define_model_scope(
    config.start_year, config.end_year, config.elements
)
mfa_system_base = system_setup.initialize_mfa_system(model_classification, index_table)
mfa_system_base, all_excel_data = system_setup.load_and_define_processes(
    mfa_system_base, config.excel_file_path, data_loader
)
mfa_system_configured, all_excel_data = system_setup.define_flows_and_parameters(
    mfa_system_base, all_excel_data
)
dsm_params = data_loader.load_dsm_parameters(all_excel_data)
fomp_params = data_loader.load_fomp_parameters(all_excel_data)
uncertainty_params = data_loader.load_uncertainty_definitions(all_excel_data)

# Run calculation
mfa_system_with_results, dsm_details = solver.run_mfa_calculation(
    mfa_system_configured, dsm_params, fomp_params, config
)
print("✅ Calculation complete!")

# --- Visualization ---
print("📊 Mass Balance Error Plot")
plotting.plot_mass_balance_error(mfa_system_with_results)

print("📊 Individual Flows")
plotting.plot_individual_flows(mfa_system_with_results)

print("📈 Individual Stocks")
plotting.plot_individual_stocks(mfa_system_with_results)

print("🌊 Sankey Diagram")
plotting.plot_interactive_sankey(mfa_system_with_results)





"""
Copy this entire section into your second Jupyter cell:
"""

# Configuration settings
class AnalysisConfig:
    def __init__(self):
        # File paths
        self.excel_file_path = 'data/01_input/250625_Template_CS0.xlsx'
        self.output_path = 'data/02_output/results.xlsx'
        
        # Model scope
        self.start_year = 2025
        self.end_year = 2050
        self.elements = ['material', 'WC', 'DM', 'CC']
        
        # Calculation options
        self.run_monte_carlo = False
        self.mc_iterations = 100
        
        # Model components - using uppercase names that solver expects
        self.RUN_DSM_CALCULATION = True
        self.RUN_FOMP_CALCULATION = True

# Create configuration instance
config = AnalysisConfig()

# Validate configuration
print("📋 Analysis Configuration:")
print(f"   Input file: {config.excel_file_path}")
print(f"   Time range: {config.start_year} - {config.end_year}")
print(f"   Elements: {', '.join(config.elements)}")
print(f"   Monte Carlo: {'Yes' if config.run_monte_carlo else 'No'}")
if config.run_monte_carlo:
    print(f"   MC iterations: {config.mc_iterations}")

# Validate configuration
print("\n🔍 Configuration Validation:")
is_valid = utils.print_configuration_summary(config)

if not is_valid:
    print("\n❌ Please fix configuration issues before proceeding.")
    raise ValueError("Configuration validation failed")

# ==============================================================================
# CELL 3: Data Validation
# ==============================================================================
"""
Copy this entire section into your third Jupyter cell:
"""

# Check input file
if os.path.exists(config.excel_file_path):
    print(f"✅ Input file found: {config.excel_file_path}")
    
    # Load and validate data
    try:
        input_data = pd.read_excel(config.excel_file_path, sheet_name=None, header=0,
                                   engine='openpyxl', na_values=['N.A.', 'NA', 'n/a'])
        data_loader.validate_input_data(input_data)
        print("✅ Data validation passed!")
        
        # Show available sheets
        print(f"\n📊 Available data sheets: {list(input_data.keys())}")
        
        # Show basic info
        if '0_Metadata' in input_data:
            metadata = input_data['0_Metadata']
            print(f"\n📋 Dataset: {metadata.get('Dataset_Name', 'Unknown').iloc[0] if len(metadata) > 0 else 'Unknown'}")
            print(f"   Version: {metadata.get('Version', 'Unknown').iloc[0] if len(metadata) > 0 else 'Unknown'}")
            print(f"   Author: {metadata.get('Author', 'Unknown').iloc[0] if len(metadata) > 0 else 'Unknown'}")
        
    except Exception as e:
        print(f"❌ Data validation failed: {e}")
        raise
else:
    print(f"❌ Input file not found: {config.excel_file_path}")
    print("Please check the file path in the configuration above.")

# ==============================================================================
# CELL 4: Model Setup
# ==============================================================================
"""
Copy this entire section into your fourth Jupyter cell:
"""

# Model setup and execution
print("🔧 Setting up MFA model...")

# 1. Define model scope
model_classification, index_table = system_setup.define_model_scope(
    config.start_year, config.end_year, config.elements
)

# 2. Initialize MFA system
mfa_system_base = system_setup.initialize_mfa_system(model_classification, index_table)

# 3. Load data and define processes
mfa_system_base, all_excel_data = system_setup.load_and_define_processes(
    mfa_system_base, config.excel_file_path, data_loader
)

# 4. Load model parameters
dsm_params = data_loader.load_dsm_parameters(all_excel_data)
fomp_params = data_loader.load_fomp_parameters(all_excel_data)
uncertainty_params = data_loader.load_uncertainty_definitions(all_excel_data)

# 5. Configure system with flows and parameters
mfa_system_configured, _ = system_setup.define_flows_and_parameters(mfa_system_base, all_excel_data)

print("✅ Model setup complete!")
print(f"   Processes: {len(mfa_system_configured.ProcessList)}")
print(f"   Flows: {len(mfa_system_configured.FlowDict)}")
print(f"   Stocks: {len(mfa_system_configured.StockDict)}")
print(f"   Parameters: {len(mfa_system_configured.ParameterDict)}")

# ==============================================================================
# CELL 5: Run Calculations
# ==============================================================================
"""
Copy this entire section into your fifth Jupyter cell:
"""

# Run calculations
print("\n🧮 Running MFA calculations...")

if config.run_monte_carlo:
    print(f"   Monte Carlo simulation ({config.mc_iterations} iterations)")
    
    # Monte Carlo simulation
    mc_run_results = []
    
    for i in range(config.mc_iterations):
        if i % 10 == 0:  # Progress indicator
            print(f"   Progress: {i}/{config.mc_iterations}")
        
        # Sample parameters
        sampled_values = utils.sample_parameters(uncertainty_params)
        tc_updates = {k: v for k, v in sampled_values.items() if k.startswith('TC_')}
        
        # Run calculation
        run_results, _ = solver.run_mfa_calculation(
            mfa_system_configured, dsm_params, fomp_params, config, tc_updates=tc_updates
        )
        
        # Extract KPIs
        if run_results:
            final_c_stock_soil = run_results.StockDict['S_8'].Values[-1, 3]
            current_run_data = sampled_values.copy()
            current_run_data['run_id'] = i
            current_run_data['final_C_stock_soil'] = final_c_stock_soil
            mc_run_results.append(current_run_data)
    
    df_mc_results = pd.DataFrame(mc_run_results)
    mfa_system_with_results = None
    dsm_details = None
    
    print("✅ Monte Carlo simulation complete!")
    
else:
    print("   Deterministic calculation")
    
    # Single deterministic run
    mfa_system_with_results, dsm_details = solver.run_mfa_calculation(
        mfa_system_configured, dsm_params, fomp_params, config
    )
    
    df_mc_results = None
    
    print("✅ Deterministic calculation complete!")

# ==============================================================================
# CELL 7: MASS BALANCE VALIDATION (MOST IMPORTANT - RUN FIRST!)
# ==============================================================================
"""
Copy this entire section into your seventh Jupyter cell:

## 🔍 Mass Balance Validation - CRITICAL FIRST STEP

**Why this comes first:** Mass balance validation is the most important check in MFA analysis. 
It ensures that material conservation is maintained throughout the system. 
- Green bars = balanced processes (good!)
- Red bars = mass created (error!)
- Gray bars = mass destroyed (error!)

**What to look for:** All bars should be close to zero (green). 
If you see red or gray bars, there's an issue with your model setup.
"""

# Mass Balance Check - CRITICAL FIRST STEP
print("🔍 MASS BALANCE VALIDATION - CRITICAL FIRST STEP")
print("=" * 60)
print("This is the MOST IMPORTANT validation step!")
print("Green bars = balanced, Red bars = mass created, Gray bars = mass destroyed")
print("All bars should be close to zero for a valid model.")
print("=" * 60)

if mfa_system_with_results is not None:
    print("[Deterministic mode: Showing mass balance error plot]")
    plotting.plot_mass_balance_error(mfa_system_with_results)
    # Additional mass balance summary
    print("\n📊 Mass Balance Summary:")
    time_items = mfa_system_with_results.IndexTable.Classification['Time'].Items
    element_items = mfa_system_with_results.Elements
    # Check final year mass balance
    final_year_idx = -1
    for element in element_items:
        element_index = element_items.index(element)
        total_error = 0
        for p in mfa_system_with_results.ProcessList:
            in_val = sum(f.Values[final_year_idx, element_index] for f in mfa_system_with_results.FlowDict.values() if f.P_End == p.ID)
            out_val = sum(f.Values[final_year_idx, element_index] for f in mfa_system_with_results.FlowDict.values() if f.P_Start == p.ID)
            ds_val = mfa_system_with_results.StockDict.get(f'dS_{p.ID}', None)
            ds_sum = ds_val.Values[final_year_idx, element_index] if ds_val is not None else 0
            error = in_val - out_val - ds_sum
            total_error += abs(error)
        print(f"   {element.upper()}: Total absolute error = {total_error:.6f} Mg")
        if total_error < 1e-6:
            print(f"   ✅ {element.upper()} mass balance is excellent!")
        elif total_error < 1e-3:
            print(f"   ⚠️  {element.upper()} mass balance is acceptable.")
        else:
            print(f"   ❌ {element.upper()} mass balance has issues!")
elif df_mc_results is not None:
    print("[Monte Carlo mode: Showing MC output distribution for a key result]")
    try:
        if 'final_C_stock_soil' in df_mc_results.columns:
            plotting.plot_mc_distribution(df_mc_results, column_name='final_C_stock_soil', unit='Mg C')
            print(df_mc_results['final_C_stock_soil'].describe())
        else:
            print("No 'final_C_stock_soil' column found in MC results.")
    except Exception as e:
        print(f"Error plotting MC distribution: {e}")
else:
    print("❌ No results available for mass balance check")

# ==============================================================================
# CELL 8: INDIVIDUAL FLOW ANALYSIS
# ==============================================================================
"""
Copy this entire section into your eighth Jupyter cell:

## 📊 Individual Flow Analysis

**Purpose:** Analyze specific flows in detail to understand material movements.
**Features:**
- Select multiple flows to compare
- Choose between line and bar charts
- Option to show cumulative values
- Filter by element type

**Use cases:**
- Identify dominant flows in the system
- Track material pathways
- Compare flow magnitudes over time
- Analyze cumulative material movements
"""

print("📊 Individual Flow Analysis")
print("=" * 50)
print("Select specific flows to analyze their time evolution.")
print("Use the dropdown to choose flows and elements.")

if mfa_system_with_results is not None:
    print("[Deterministic mode: Showing individual flow analysis]")
    plotting.plot_individual_flows(mfa_system_with_results)
elif df_mc_results is not None:
    print("[Monte Carlo mode: Showing MC output distribution for a key flow]")
    # Example: Show histogram for a flow-related output if present
    try:
        # Replace 'final_flow_value' with your actual MC output column name for flows
        flow_col = [col for col in df_mc_results.columns if 'flow' in col.lower()]
        if flow_col:
            plotting.plot_mc_distribution(df_mc_results, column_name=flow_col[0], unit='Mg')
            print(df_mc_results[flow_col[0]].describe())
        else:
            print("No flow-related output column found in MC results.")
    except Exception as e:
        print(f"Error plotting MC flow distribution: {e}")
else:
    print("❌ No results available for flow analysis")

# ==============================================================================
# CELL 9: INDIVIDUAL STOCK ANALYSIS
# ==============================================================================
"""
Copy this entire section into your ninth Jupyter cell:

## 📈 Individual Stock Analysis

**Purpose:** Analyze specific stocks to understand material accumulation patterns.
**Features:**
- Select multiple stocks to compare
- Color-coded by process type (DSM, FOMP, Regular)
- Option to show stock changes (ΔS) instead of absolute stocks
- Choose between line and bar charts

**Use cases:**
- Track material accumulation in specific processes
- Compare stock evolution between different process types
- Analyze stock change rates
- Identify processes with significant material storage
"""

print("📈 Individual Stock Analysis")
print("=" * 50)
print("Select specific stocks to analyze their time evolution.")
print("DSM processes: Orange dashed lines")
print("FOMP processes: Green dot-dash lines")
print("Regular processes: Blue solid lines")

if mfa_system_with_results is not None:
    print("[Deterministic mode: Showing individual stock analysis]")
    plotting.plot_individual_stocks(mfa_system_with_results, dsm_params, fomp_params)
elif df_mc_results is not None:
    print("[Monte Carlo mode: Showing MC output distribution for a key stock]")
    try:
        # Replace 'final_C_stock_soil' with your actual MC output column name for stocks
        if 'final_C_stock_soil' in df_mc_results.columns:
            plotting.plot_mc_distribution(df_mc_results, column_name='final_C_stock_soil', unit='Mg C')
            print(df_mc_results['final_C_stock_soil'].describe())
        else:
            print("No 'final_C_stock_soil' column found in MC results.")
    except Exception as e:
        print(f"Error plotting MC stock distribution: {e}")
else:
    print("❌ No results available for stock analysis")

# ==============================================================================
# CELL 10: SYSTEM OVERVIEW - SANKEY DIAGRAM
# ==============================================================================
"""
Copy this entire section into your tenth Jupyter cell:

## 🌊 System Overview - Material Flow Network (Sankey)

**Purpose:** Visualize the entire material flow network in an interactive diagram.
**Features:**
- Interactive controls for year, element, and flow threshold
- Filter processes to focus on specific parts of the system
- Adjust minimum flow value to hide minor flows
- Real-time updates

**Use cases:**
- Understand overall system structure
- Identify major material pathways
- Communicate system complexity to stakeholders
- Identify bottlenecks or dominant flows
"""

print("🌊 Material Flow Network (Sankey Diagram)")
print("=" * 50)
print("This interactive diagram shows how materials flow between processes.")
print("Use the controls to filter by year, element, and minimum flow value.")

if mfa_system_with_results is not None:
    print("[Deterministic mode: Showing Sankey diagram]")
    plotting.plot_interactive_sankey(mfa_system_with_results)
elif df_mc_results is not None:
    print("[Monte Carlo mode: Showing MC summary statistics]")
    print(df_mc_results.describe())
else:
    print("❌ No results available for Sankey diagram")

# ==============================================================================
# CELL 11: STOCK EVOLUTION OVERVIEW
# ==============================================================================
"""
Copy this entire section into your eleventh Jupyter cell:

## 📊 Stock Evolution Overview

**Purpose:** Get a comprehensive view of all stock dynamics in the system.
**Features:**
- Total system stock evolution
- Individual stock breakdown
- Color-coded by process type
- Interactive element selection

**Use cases:**
- Understand overall system stock dynamics
- Compare stock evolution between elements
- Identify processes with significant stock changes
- Track long-term material accumulation trends
"""

print("📊 Stock Evolution Overview")
print("=" * 50)

if mfa_system_with_results is not None:
    print("[Deterministic mode: Showing stock evolution overview]")
    print("\n📈 Overall Stock Evolution")
    plotting.plot_stock_evolution(mfa_system_with_results, dsm_params, fomp_params)
elif df_mc_results is not None:
    print("[Monte Carlo mode: Showing MC boxplot for a key stock]")
    try:
        import matplotlib.pyplot as plt
        if 'final_C_stock_soil' in df_mc_results.columns:
            plt.figure()
            df_mc_results['final_C_stock_soil'].plot(kind='box', title='Final Soil Carbon Stock (MC)')
            plt.ylabel('Mg C')
            plt.show()
        else:
            print("No 'final_C_stock_soil' column found in MC results.")
    except Exception as e:
        print(f"Error plotting MC boxplot: {e}")
else:
    print("❌ No results available for stock evolution analysis")

# ==============================================================================
# CELL 12: SYSTEM EFFICIENCY METRICS
# ==============================================================================
"""
Copy this entire section into your twelfth Jupyter cell:

## 🔍 System Efficiency Metrics

**Purpose:** Analyze system performance through key efficiency indicators.
**Metrics:**
- **Recycling Rate:** Percentage of internal material flows
- **Recovery Rate:** Ratio of outputs to inputs
- **Material Efficiency:** Useful output per unit input

**Use cases:**
- Assess system circularity
- Compare efficiency between scenarios
- Identify improvement opportunities
- Track efficiency trends over time
"""

print("🔍 System Efficiency Metrics")
print("=" * 50)

if mfa_system_with_results is not None:
    print("[Deterministic mode: Showing system efficiency metrics]")
    plotting.plot_system_efficiency_metrics(mfa_system_with_results)
elif df_mc_results is not None:
    print("[Monte Carlo mode: Showing MC sensitivity scatter plot]")
    try:
        # Example: Sensitivity of 'fomp_8_k1' vs 'final_C_stock_soil'
        if 'fomp_8_k1' in df_mc_results.columns and 'final_C_stock_soil' in df_mc_results.columns:
            plotting.plot_mc_sensitivity_scatter(df_mc_results, input_param_name='fomp_8_k1', output_param_name='final_C_stock_soil', unit='Mg C')
        else:
            print("Required columns for sensitivity scatter not found in MC results.")
    except Exception as e:
        print(f"Error plotting MC sensitivity scatter: {e}")
else:
    print("❌ No results available for efficiency analysis")

# ==============================================================================
# CELL 13: PROCESS DYNAMICS (INFLOW-STOCK-OUTFLOW)
# ==============================================================================
"""
Copy this entire section into your thirteenth Jupyter cell:

## 📈 Process Dynamics (Inflow-Stock-Outflow)

**Purpose:** Analyze the complete dynamics of individual processes.
**Features:**
- Side-by-side view of inflow, stock, and outflow
- Process-specific analysis
- Element selection
- Smart titles based on process type

**Use cases:**
- Understand process behavior in detail
- Identify process bottlenecks
- Analyze process efficiency
- Compare process dynamics across the system
"""

# Process Dynamics
print("📈 Process Dynamics (Inflow-Stock-Outflow)")
print("=" * 50)
print("These plots show inflow, stock, and outflow dynamics for selected processes.")

if mfa_system_with_results is not None:
    plotting.plot_process_dynamics(mfa_system_with_results, all_excel_data['2_1_Definition_Processes'])
else:
    print("❌ No deterministic results available for process dynamics")

# ==============================================================================
# CELL 14: DSM STOCK DETAILS (IF APPLICABLE)
# ==============================================================================
"""
Copy this entire section into your fourteenth Jupyter cell:

## 🔄 DSM Stock Details (Dynamic Stock Model)

**Purpose:** Detailed analysis of DSM processes showing stock composition over time.
**Features:**
- Initial stock decay visualization
- New stock accumulation by category
- Total stock evolution
- Element-specific analysis

**Use cases:**
- Understand DSM process behavior
- Analyze stock turnover rates
- Track material aging in stocks
- Compare different DSM processes
"""

# DSM Stock Details (if DSM processes exist)
print("🔄 DSM Stock Details")
print("=" * 50)

if mfa_system_with_results is not None and dsm_params and dsm_details:
    plotting.plot_dsm_stock_details(mfa_system_with_results, dsm_params, dsm_details)
else:
    print("ℹ️  No DSM processes found or no detailed results available")

# ==============================================================================
# CELL 15: FOMP STOCK DETAILS (IF APPLICABLE)
# ==============================================================================
"""
Copy this entire section into your fifteenth Jupyter cell:

## 🌱 FOMP Stock Details (First-Order Mineralization Process)

**Purpose:** Detailed analysis of FOMP processes showing organic matter dynamics.
**Features:**
- Organic matter stock evolution
- Cumulative input tracking
- Mineralization rate analysis
- Element-specific analysis

**Use cases:**
- Understand organic matter decomposition
- Analyze mineralization rates
- Track carbon sequestration
- Compare different FOMP processes
"""

# FOMP Stock Details (if FOMP processes exist)
print("🌱 FOMP Stock Details")
print("=" * 50)

if mfa_system_with_results is not None and fomp_params:
    plotting.plot_fomp_stock_details(mfa_system_with_results, fomp_params)
else:
    print("ℹ️  No FOMP processes found")

# ==============================================================================
# CELL 16: SUMMARY DASHBOARD
# ==============================================================================
"""
Copy this entire section into your sixteenth Jupyter cell:

## 📋 Summary Dashboard

**Purpose:** Comprehensive overview of key system indicators and KPIs.
**Features:**
- Multi-panel dashboard layout
- Total stock evolution for all elements
- System flows overview
- Process type distribution
- Key metrics gauge

**Use cases:**
- Quick system overview
- Presentation to stakeholders
- System status monitoring
- Comparison between scenarios
"""

# Summary Dashboard
print("📋 Summary Dashboard")
print("=" * 50)

if mfa_system_with_results is not None:
    plotting.plot_summary_dashboard(mfa_system_with_results, dsm_params, fomp_params)
else:
    print("❌ No deterministic results available for dashboard")

# ==============================================================================
# CELL 17: SCENARIO MANAGEMENT
# ==============================================================================
"""
Copy this entire section into your seventeenth Jupyter cell:

## 🎯 Scenario Management

**Purpose:** Save, load, and compare different parameter configurations.
**Features:**
- Save current scenario configuration
- Load existing scenarios
- Create alternative scenarios
- Scenario comparison tools

**Use cases:**
- Compare different policy scenarios
- Sensitivity analysis
- Parameter optimization
- Scenario archiving
"""

# Scenario Management
print("🎯 Scenario Management")
print("=" * 50)

# Initialize scenario manager
scenario_manager = utils.ScenarioManager()

# Save current scenario
current_scenario_name = "baseline_scenario"
scenario_manager.save_scenario(
    current_scenario_name, 
    config, 
    description="Baseline scenario with current parameters"
)

# List available scenarios
print("\n📋 Available Scenarios:")
scenarios = scenario_manager.list_scenarios()
for scenario in scenarios:
    print(f"   - {scenario['name']}: {scenario['description']}")

# Example: Create alternative scenarios
print("\n🔄 Creating Alternative Scenarios...")

# Scenario 1: High recycling
config_high_recycling = utils.create_config_from_scenario(AnalysisConfig, scenario_manager.load_scenario(current_scenario_name))
config_high_recycling.mc_iterations = 50  # Reduce MC iterations for faster testing
scenario_manager.save_scenario(
    "high_recycling", 
    config_high_recycling, 
    description="High recycling rate scenario"
)

# Scenario 2: Extended time horizon
config_extended = utils.create_config_from_scenario(AnalysisConfig, scenario_manager.load_scenario(current_scenario_name))
config_extended.end_year = 2060
scenario_manager.save_scenario(
    "extended_horizon", 
    config_extended, 
    description="Extended time horizon to 2060"
)

print("✅ Alternative scenarios created successfully!")

# ==============================================================================
# CELL 18: EXPORT RESULTS
# ==============================================================================
"""
Copy this entire section into your eighteenth Jupyter cell:

## 💾 Export Results

**Purpose:** Save analysis results to files for further analysis and reporting.
**Features:**
- Excel export with multiple sheets
- Comprehensive data export
- Monte Carlo results export
- Summary statistics

**Use cases:**
- Further analysis in Excel
- Report generation
- Data archiving
- Sharing results with stakeholders
"""

# Export results
print("💾 Exporting Results")
print("=" * 30)

# Create output directory if it doesn't exist
output_dir = os.path.dirname(config.output_path)
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
    print(f"📁 Created output directory: {output_dir}")

# Export deterministic results
if mfa_system_with_results is not None:
    utils.export_results_to_excel(mfa_system_with_results, config.output_path)
    print(f"✅ Results exported to: {config.output_path}")
    
    # Show what was exported
    print("\n📊 Exported data includes:")
    print(f"   - Flows time series ({len(mfa_system_with_results.FlowDict)} flows)")
    print(f"   - Stocks time series ({len(mfa_system_with_results.StockDict)} stocks)")
    print(f"   - Time range: {config.start_year} - {config.end_year}")
    print(f"   - Elements: {', '.join(config.elements)}")

# Export Monte Carlo results
if config.run_monte_carlo and df_mc_results is not None:
    mc_output_path = config.output_path.replace('.xlsx', '_MonteCarlo.xlsx')
    with pd.ExcelWriter(mc_output_path) as writer:
        df_mc_results.to_excel(writer, sheet_name='MC_Results', index=False)
        
        # Add summary statistics
        if 'final_C_stock_soil' in df_mc_results.columns:
            summary_stats = df_mc_results['final_C_stock_soil'].describe()
            summary_stats.to_frame('final_C_stock_soil').to_excel(writer, sheet_name='Summary_Stats')
    
    print(f"✅ Monte Carlo results exported to: {mc_output_path}")
    print(f"   - {len(df_mc_results)} simulation runs")
    print(f"   - {len(df_mc_results.columns)} parameters tracked")

print("\n🎉 Analysis complete!")
print("You can now:")
print("  - Review the interactive plots above")
print("  - Open the exported Excel files for detailed data")
print("  - Use scenario management to compare different configurations")
print("  - Modify the configuration and re-run for different scenarios")

# ==============================================================================
# APPENDIX: Publication-Ready Sankey Diagram Enhancements (for Jupyter)
# ==============================================================================
"""
Copy these code snippets into your Jupyter cells as needed to enhance your Sankey diagrams for publication.
"""

# --- Export Button for Plotly Figures (SVG/PNG) ---
import plotly.graph_objects as go
import ipywidgets as widgets

def show_export_buttons(fig, filename_base="sankey_diagram"):
    def export_svg(_):
        fig.write_image(f"{filename_base}.svg")
        print(f"Exported as {filename_base}.svg")
    def export_png(_):
        fig.write_image(f"{filename_base}.png")
        print(f"Exported as {filename_base}.png")
    btn_svg = widgets.Button(description="Export as SVG")
    btn_png = widgets.Button(description="Export as PNG")
    btn_svg.on_click(export_svg)
    btn_png.on_click(export_png)
    display(widgets.HBox([btn_svg, btn_png]))
    fig.show()

# Usage example (after creating your Sankey fig):
# show_export_buttons(fig)

# --- Example Color Mapping for Sankey Nodes/Links by Type ---
# Define your process types and assign colors
process_types = ["DSM", "FOMP", "Regular"]
type_colors = {
    'DSM': '#ff7f0e',      # Orange
    'FOMP': '#2ca02c',    # Green
    'Regular': '#1f77b4'  # Blue
}
# Suppose you have a list of node types in node_types
# node_colors = [type_colors.get(t, '#cccccc') for t in node_types]
# fig.update_traces(node=dict(color=node_colors))

# --- Markdown Best Practices for Publication Graphics ---
"""
**Best Practices for Publication-Ready Sankey Diagrams:**
- Use SVG export for vector quality.
- Set font to Arial or Times New Roman, size 12+.
- Use high-contrast colors for clarity.
- Remove unnecessary gridlines and backgrounds.
- Label nodes and flows clearly.
""" 