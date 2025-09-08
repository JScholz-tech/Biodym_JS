# -*- coding: utf-8 -*- 
# --- 
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.17.2
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# --- 

# # BioDYM Material Flow Analysis - Scientific Notebook
# 
# A streamlined notebook for Material Flow Analysis using the BioDYM framework with enhanced plotting capabilities. 
# 
# ## Workflow Overview
# 
# This notebook follows a structured approach to Material Flow Analysis:
# 
# 1. **Setup and Data Loading** - Prepare environment and load input data
# 2. **Calculation & Validation** - Execute MFA analysis and verify results
# 3. **Visualization** - Comprehensive analysis and exploration
# 4. **Scenario Analysis** - (Optional) Compare a scenario against the baseline
# 5. **Export** - Save results and generate documentation
# 
# --- 

# # 1. Setup and Data Loading
# 
# This section prepares the analysis environment and loads the input data.

# ## 1.1 Environment Setup

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from IPython.display import display, HTML, Markdown
import copy

# Add BioDYM modules to path
src_path = os.path.join(os.getcwd(), 'src')
sys.path.insert(0, src_path)

# Add ODYM framework to path
biodym_mfa_tool_dir = os.getcwd()
odym_path = os.path.join(
    biodym_mfa_tool_dir, "framework", "ODYM-master_20241127", "odym", "modules"
)
sys.path.insert(0, odym_path)

# Add bioDYM add-on to path
biodym_addon_path = os.path.join(
    biodym_mfa_tool_dir, "framework", "bioDYM_add-on", "modules"
)
sys.path.insert(0, biodym_addon_path)

# Import BioDYM modules
try:
    import config
    import data_loader
    import system_setup
    import utils
    from engine import solver
    from src import plotting
    from src.plotting import scenario
    import ODYM_Classes as msc
    print("✅ BioDYM modules imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("   Current Python path:")
    for i, path in enumerate(sys.path[:5]):  # Show first 5 paths
        print(f"   {i}: {path}")
    raise

# Set up plotting
plt.style.use('default')
print("📊 Plotting environment ready")

# ## 1.2 Data Input Configuration

# This is the only manual path setting required.
input_file = "data/01_input/250902_CS1_Wheat_Straw.xlsx"
print(f"📁 Input file: {input_file}")
if not os.path.exists(input_file):
    raise FileNotFoundError(f"Input file not found: {input_file}")

# ## 1.3 System Configuration Extraction

print("\n" + "="*60)
print("⚙️ EXTRACTING CONFIGURATION FROM EXCEL")
print("="*60)

# Load the full dataset once. This will be passed to functions that need it.
input_data = pd.read_excel(
    input_file, sheet_name=None, header=0, engine='openpyxl', na_values=['N.A.', 'NA', 'n/a']
)
print(f"✅ Excel file loaded: {len(input_data)} sheets")

# Use the robust loader from the config module. This function handles all errors
# and fallbacks, guaranteeing a valid config object is returned.
config_obj = config.load_configuration(input_file)
print("✅ Configuration object loaded.")

# Extract core values from the config object, with fallbacks to data-driven values
try:
    start_year = int(config_obj.Start_Year)
    end_year = int(config_obj.End_Year)
    elements = [elem.strip() for elem in config_obj.Elements_commaseparated.split(',')]
except Exception as e:
    print(f"⚠️ Could not get time/elements from config object: {e}. Falling back to data-driven values.")
    flow_data = input_data['1_2_Data_Flows']
    years = sorted(flow_data['Year_Flow'].unique())
    start_year = int(min(years))
    end_year = int(max(years))
    elements = ['material', 'WC', 'DM', 'CC']

# Display final configuration summary
run_scenario = getattr(config_obj, 'Run_Scenario_Analysis', False)
selected_scenario = getattr(config_obj, 'Selected_Scenario_Name 1', getattr(config_obj, 'Selected_Scenario_Name', 'N/A'))

print(f"\n-- Configuration Summary --")
print(f"📅 Time range: {start_year} - {end_year}")
print(f"🧪 Elements: {elements}")
print(f"🎲 Monte Carlo: {'Enabled' if config_obj.RUN_MONTE_CARLO else 'Disabled'}")
print(f"📊 DSM Calculation: {'Enabled' if config_obj.RUN_DSM_CALCULATION else 'Disabled'}")
print(f"🌱 FOMP Calculation: {'Enabled' if config_obj.RUN_FOMP_CALCULATION else 'Disabled'}")
print(f"🎭 Scenario Analysis: {'Enabled' if run_scenario else 'Disabled'}")
if run_scenario:
    print(f"   -> Selected Scenario: '{selected_scenario}'")

# # 2. Baseline Calculation & Validation

print("\n" + "="*60)
print("🚀 RUNNING BASELINE MFA CALCULATION")
print("="*60)

# ## 2.1 Model Initialization

print("📋 Setting up model scope...")
model_classification, index_table = system_setup.define_model_scope(start_year, end_year, elements)

print("🔧 Initializing MFA system...")
mfa_system_base = system_setup.initialize_mfa_system(model_classification, index_table)

# We pass the already loaded `input_data` to this function, no need to read the file again.
print("📊 Loading processes and data...")
mfa_system_base, all_excel_data = system_setup.load_and_define_processes(mfa_system_base, input_data, data_loader)

print("⚙️ Loading parameters...")
dsm_params = data_loader.load_dsm_parameters(all_excel_data)
if config_obj.RUN_FOMP_CALCULATION:
    fomp_params = data_loader.load_fomp_parameters(all_excel_data)
else:
    fomp_params = {}
uncertainty_params = data_loader.load_uncertainty_definitions(all_excel_data)

# ## 2.2 Baseline Calculation Execution

print("🔗 Defining flows and parameters...")
mfa_system_configured, _ = system_setup.define_flows_and_parameters(mfa_system_base, all_excel_data)

print("🔄 Processing dynamic transfer coefficients...")
dynamic_tc_sheet = all_excel_data.get('2_5_dynamic_tcs')
if dynamic_tc_sheet is not None and not dynamic_tc_sheet.empty:
    dynamic_tcs = system_setup.create_dynamic_tc_parameters(dynamic_tc_sheet, mfa_system_configured.IndexTable.Classification['Time'].Items)
    for name, values in dynamic_tcs.items():
        mfa_system_configured.ParameterDict[name] = msc.Parameter(Name=name, ID=len(mfa_system_configured.ParameterDict) + 1, Values=values, Unit="1")
    print(f"✅ Dynamic TCs processed: {len(dynamic_tcs)} parameters added")

print("🧮 Running baseline calculation...")
mfa_results_baseline, dsm_details_baseline = solver.run_mfa_calculation(mfa_system_configured, dsm_params, fomp_params, config_obj)
print("✅ Baseline calculation completed successfully!")

# ## 2.3 Mass Balance Validation

print("\n" + "="*60)
print("⚖️ MASS BALANCE VERIFICATION (BASELINE)")
print("="*60)
plotting.plot_total_mass_balance_error(mfa_results_baseline)
plotting.plot_optimized_mass_balance_error(mfa_results_baseline)

# # 3. Baseline Visualization

print("\n" + "="*60)
print("📊 VISUALIZATION (BASELINE)")
print("="*60)

plotting.plot_interactive_sankey(mfa_results_baseline, dsm_params, fomp_params)
plotting.plot_process_dynamics(mfa_results_baseline, all_excel_data['2_1_Definition_Processes'])
plotting.plot_stock_bar_chart(mfa_results_baseline, title="Stock Levels Over Time (Baseline)")
if dsm_params and dsm_details_baseline:
    plotting.plot_dsm_stock_details(mfa_results_baseline, dsm_params, dsm_details_baseline)
if fomp_params:
    plotting.plot_fomp_stock_details(mfa_results_baseline, fomp_params)

# # 4. Scenario Analysis

mfa_results_scenario = None  # Initialize scenario results to None

if getattr(config_obj, 'Run_Scenario_Analysis', False):
    SELECTED_SCENARIO_NAME = 'High_Recycling'  # WORKAROUND: Hardcoded scenario name
    print("\n" + "="*60)
    print(f"🎭 RUNNING SCENARIO: '{SELECTED_SCENARIO_NAME}'")
    print("="*60)

    print("📄 Loading scenario definitions...")
scenario_definitions = data_loader.load_scenario_definitions(all_excel_data)
if SELECTED_SCENARIO_NAME not in scenario_definitions:
    raise ValueError(f"Scenario '{SELECTED_SCENARIO_NAME}' not found in '5_1_Scenario_Manager' sheet!")

    print("🔧 Applying scenario...")
mfa_system_scenario = copy.deepcopy(mfa_system_configured)
mfa_system_scenario = system_setup.apply_scenario(mfa_system_scenario, scenario_definitions, SELECTED_SCENARIO_NAME)

scenario_config_obj = copy.deepcopy(config_obj)
scenario_config_obj.RUN_MONTE_CARLO = False
print("   -> Monte Carlo explicitly DISABLED for scenario run.")

print("🧮 Running scenario calculation...")
mfa_results_scenario, dsm_details_scenario = solver.run_mfa_calculation(mfa_system_scenario, dsm_params, fomp_params, scenario_config_obj)
print("✅ Scenario calculation completed successfully!")

# # 5. Scenario vs. Baseline Comparison

if mfa_results_scenario:
    SELECTED_SCENARIO_NAME = 'High_Recycling'  # WORKAROUND: Hardcoded scenario name
    print("\n" + "="*60)
    print("📊 SCENARIO VS. BASELINE COMPARISON")
    print("="*60)

    print("📈 Generating comparison plots...")
    plotting.scenario.plot_stock_comparison(
        baseline_results=mfa_results_baseline, 
        scenario_results=mfa_results_scenario,
        baseline_name='Baseline', 
        scenario_name=SELECTED_SCENARIO_NAME
    )
    plotting.scenario.plot_flow_comparison(
        baseline_results=mfa_results_baseline, 
        scenario_results=mfa_results_scenario,
        baseline_name='Baseline', 
        scenario_name=SELECTED_SCENARIO_NAME
    )

# # 6. Export & Final Summary

print("\n" + "="*60)
print("💾 EXPORTING BASELINE RESULTS")
print("="*60)

output_file = "data/02_output/results_scientific_baseline.xlsx"
utils.export_results_to_excel(mfa_results_baseline, output_file)
print(f"✅ Baseline results exported to: {output_file}")

# # 7. Monte Carlo Analysis (Baseline)

print("\n" + "="*60)
print("🎲 MONTE CARLO SIMULATION (BASELINE)")
print("="*60)

if config_obj.RUN_MONTE_CARLO and '4_1_Uncertainty_Parameters' in input_data:
    try:
        from engine.mc_simulation import run_mc_simulation
        from plotting.mc_visuals import plot_interactive_mc_histogram, plot_interactive_tornado
        mc_results = run_mc_simulation(mfa_system_configured, input_data, dsm_params, fomp_params, config_obj)
        if mc_results is not None and not mc_results.empty:
            print("✅ Monte Carlo simulation completed for baseline")
            plot_interactive_mc_histogram(mc_results)
            plot_interactive_tornado(mc_results)
    except Exception as e:
        print(f"⚠️ Monte Carlo simulation failed: {e}")
        import traceback
        traceback.print_exc()
else:
    print("ℹ️ Monte Carlo analysis is disabled or no uncertainty parameters are defined. Skipping.")

print("\n" + "="*60)
print("🎉 ANALYSIS COMPLETE")
print("="*60)