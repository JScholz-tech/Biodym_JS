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

# <div style="text-align: center;">
#   <img src="02_src/bioDYM_Logo.png" alt="BioDYM Logo" width="600"/>
# </div>
#
# # BioDYM - Material Flow Analysis Framework
#
# **A streamlined framework for dynamic Material Flow Analysis of bio-based systems**
#
# ---
#
# ### 👥 Authors
# **Johannes Scholz** • Technical University of Berlin
# **Lukas Hoppe** • Technical University of Berlin
# **Albrecht Fritze** • Technical University of Berlin
# **Vera Susanne Rotter** • Technical University of Berlin
# *Contributing authors and collaborators listed in CONTRIBUTORS.md*
#
# ### 📄 License
# This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.
# Built on the [ODYM Framework](https://github.com/IndEcol/ODYM) (Pauliuk & Heeren, 2020)
#
# ---
#
# ### 📖 Table of Contents
#
# * [0. Introduction](#0.-Introduction)
#   * [🚀 Quick Start Guide](#🚀-Quick-Start-Guide)
# * [1. Setup and Data Loading](#1.-Setup-and-Data-Loading)
#   * [1.1 Environment Setup](#1.1-Environment-Setup)
#   * [1.2 Data Input Configuration](#1.2-Data-Input-Configuration)
#   * [1.3 System Configuration Extraction](#1.3-System-Configuration-Extraction)
# * [2. Calculation & Mass Balance](#2.-Calculation-&-Mass-Balance)
#   * [2.1 Model Initialization & Calculation](#2.1-Model-Initialization-&-Calculation)
#   * [2.2 Data Validation Summary](#2.2-Data-Validation-Summary)
#   * [2.3 Mass Balance Verification](#2.3-Mass-Balance-Verification)
#   * [2.4 System Flow Diagram (Graphviz)](#2.4-System-Flow-Diagram-(Graphviz))
#   * [2.5 Flow Composition Validation](#2.5-Flow-Composition-Validation)
# * [3. Visualization](#3.-Visualization)
#   * [3.1 Sankey Diagrams](#3.1-Sankey-Diagrams)
#   * [3.2 Additional Visualizations](#3.2-Additional-Visualizations)
# * [4. Scenario & Uncertainty Manager](#4.-Scenario-&-Uncertainty-Manager)
#   * [4.1 Scenario Analysis & Comparison](#4.1-Scenario-Analysis-&-Comparison)
#   * [4.2 Monte Carlo Analysis](#4.2-Monte-Carlo-Analysis)
# * [5. Data Export](#5.-Data-Export)
#   * [5.1 KPI Dashboard and Export](#5.1-KPI-Dashboard-and-Export)
#
# ---
#
# ## 📋 Workflow Overview
#
# This notebook follows a structured approach to Material Flow Analysis:
#
# 1. **Setup and Data Loading** - Prepare environment and load input data
# 2. **Calculation & Mass Balance** - Execute MFA analysis and verify mass conservation
# 3. **Visualization** - Comprehensive analysis and exploration
# 4. **Scenario & Uncertainty Analysis** - Compare scenarios and run Monte Carlo simulations
# 5. **Data Export** - Save results and generate documentation
#
# ---
#
# # 0. Introduction
#
# ## 🚀 Quick Start Guide
#
# **Welcome to BioDYM!** This notebook performs a complete Material Flow Analysis from data loading to results export.
#
# ### Getting Started
#
# 1. **Required Input**: Only the **Excel file path** needs to be set (see Section 1.2 below)
# 2. **Full Documentation**: See [README.md](README.md) for detailed setup instructions
# 3. **Example Data**: Template files are provided in `01_data/01_input/`
#
# ### Prerequisites
# - Python 3.12+ with dependencies installed (`uv sync`)
# - Excel input file following the BioDYM template structure
#
# ### Support
# - **Documentation**: `05_docs/` folder
# - **Issues**: [GitHub Issues](https://github.com/TUB-bioDYM/bioDYM/issues)
#
# ### 🔧 Debug Mode
# Set `DEBUG_MODE = True` below to see detailed technical output during data loading and calculation.
# Default: `False` (clean, user-friendly output)

DEBUG_MODE = False  # Set to True for detailed technical output

# ---

# # 1. Setup and Data Loading
#
# This section prepares the analysis environment and loads the input data.

# ## 1.1 Environment Setup

import os
import sys
import warnings
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from IPython.display import display

# Suppress openpyxl data validation warnings (harmless, caused by Excel dropdown rules)
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

# Add BioDYM modules to path to make them importable
src_path = os.path.join(os.getcwd(), "02_src")
sys.path.insert(0, src_path)

# Add ODYM framework to path. ODYM is a foundational library for this project.
project_root = os.getcwd()
odym_path = os.path.join(
    project_root, "06_framework", "ODYM-master_20241127", "odym", "modules"
)
sys.path.insert(0, odym_path)

# Add bioDYM add-on to path for custom extensions.
biodym_addon_path = os.path.join(
    project_root, "06_framework", "bioDYM_add-on", "modules"
)
sys.path.insert(0, biodym_addon_path)

# Import BioDYM modules
try:
    import config
    import data_loader
    import system_setup
    import utils
    from engine import solver
    import plotting
    import ODYM_Classes as msc
    from plotting.composition import plot_flow_composition
    from reporting import kpi_dashboard

    # Import standard icons
    from constants import (
        Icons,
        format_header,
        format_step,
        format_success,
        format_error,
        format_file_path,
    )

    print(f"{Icons.SUCCESS} BioDYM modules imported successfully")
except ImportError as e:
    print(f"{Icons.ERROR} Import error: {e}")
    print(f"{Icons.ERROR} A required module could not be found.")
    print(
        f"{Icons.INFO} Please ensure all dependencies are installed by running: uv sync"
    )
    print("   Current Python path:")
    for i, path in enumerate(sys.path[:5]):  # Show first 5 paths
        print(f"   {i}: {path}")
    raise

# Set up plotting
plt.style.use("default")
print(f"{Icons.VISUALIZATION} Plotting environment ready")

# Initialize Plotly widgets to prevent empty plot issues
# This forces the widget communication channel to be established early
print(f"{Icons.CONFIGURATION} Initializing interactive widget system...")
import time
from ipywidgets import IntSlider

try:
    # Create dummy widgets to initialize the comm channel
    _dummy_fig = go.FigureWidget()
    _dummy_slider = IntSlider()
    time.sleep(0.5)  # Allow widget registration to complete
    del _dummy_fig, _dummy_slider
    print(f"{Icons.SUCCESS} Widget system initialized successfully")
except Exception as e:
    print(f"{Icons.WARNING} Widget initialization had issues: {e}")
    print(f"{Icons.INFO} Plots may take longer on first render")

# ## 1.2 Data Input Configuration
#
# ⚠️ **IMPORTANT**: Set your Excel file path below - this is the only required change to run the analysis!

input_file = "01_data/01_input/251104_BioDYM_ODYM_´CE-RISE.xlsm"
print(format_file_path(input_file))
if not os.path.exists(input_file):
    raise FileNotFoundError(f"Input file not found: {input_file}")

# ## 1.3 System Configuration Extraction

print(format_header("EXTRACTING CONFIGURATION FROM EXCEL"))

# Load the full dataset once. This will be passed to functions that need it.
# NOTE: Uses decimal=',' for European standard (comma as decimal separator)
input_data = pd.read_excel(
    input_file,
    sheet_name=None,
    header=0,
    engine="openpyxl",
    na_values=["N.A.", "NA", "n/a"],
    decimal=",",
)
print(format_success(f"Excel file loaded: {len(input_data)} sheets"))

# Use the robust loader from the config module. This function handles all errors
# and fallbacks, guaranteeing a valid config object is returned.
config_obj = config.load_configuration(input_file)
print(format_success("Configuration object loaded."))


# Phase 1b: Extract dimension lists from config
def get_config_list(config_obj, attribute_name, default=None):
    """Helper to extract comma-separated lists from config object."""
    if hasattr(config_obj, attribute_name):
        value = getattr(config_obj, attribute_name)
        if value and pd.notna(value):
            return [item.strip() for item in str(value).split(",") if item.strip()]
    return default


regions = get_config_list(config_obj, "Regions", ["Case_Study_Region"])
goods = get_config_list(config_obj, "Goods", None)
materials = get_config_list(config_obj, "Materials", None)
processes = get_config_list(config_obj, "Process_Types", None)

print(f"{Icons.VISUALIZATION} Dimensions loaded from configuration:")
print(f"   {Icons.ARROW} Regions: {regions}")
if materials:
    print(f"   - Materials: {materials}")
if goods:
    print(f"   - Goods: {goods}")
if processes:
    print(f"   - Process Types: {processes}")

# Extract core values from the config object, with fallbacks to data-driven values
try:
    start_year = int(config_obj.Start_Year)
    end_year = int(config_obj.End_Year)
    # Try different possible element attribute names
    if hasattr(config_obj, "Elements"):
        elements = [elem.strip() for elem in config_obj.Elements.split(",")]
    elif hasattr(config_obj, "Elements_comma_separated"):
        elements = [
            elem.strip() for elem in config_obj.Elements_comma_separated.split(",")
        ]
    elif hasattr(config_obj, "Element_list"):
        elements = [elem.strip() for elem in config_obj.Element_list.split(",")]
    else:
        raise AttributeError("No Elements attribute found in config object")
except Exception as e:
    print(
        f"{Icons.WARNING} Could not get time/elements from config object: {e}. Falling back to data-driven values."
    )
    flow_data = input_data["1_2_Data_Flows"]
    # Fix: Use correct column name 'Flow_Data_Year' instead of 'Year_Flow'
    years = sorted(flow_data["Flow_Data_Year"].unique())
    start_year = int(min(years))
    end_year = int(max(years))
    elements = ["material", "WC", "DM", "CC"]

# Display final configuration summary
run_scenario = getattr(config_obj, "Run_Scenario_Analysis", False)
selected_scenario = getattr(
    config_obj,
    "Selected_Scenario_Name 1",
    getattr(config_obj, "Selected_Scenario_Name", "N/A"),
)

print(f"\n-- Configuration Summary --")
print(f"{Icons.TIME} Time range: {start_year} - {end_year}")
print(f"{Icons.ELEMENT} Elements: {elements}")
print(
    f"{Icons.MONTE_CARLO} Monte Carlo: {'Enabled' if config_obj.RUN_MONTE_CARLO else 'Disabled'}"
)
print(
    f"{Icons.DSM} DSM Calculation: {'Enabled' if config_obj.RUN_DSM_CALCULATION else 'Disabled'}"
)
print(
    f"{Icons.FOMP} FOMP Calculation: {'Enabled' if config_obj.RUN_FOMP_CALCULATION else 'Disabled'}"
)
print(
    f"{Icons.SCENARIO} Scenario Analysis: {'Enabled' if run_scenario else 'Disabled'}"
)
if run_scenario:
    print(f"   -> Selected Scenario: '{selected_scenario}'")

# # 2. Calculation & Mass Balance

# ## 2.1 Model Initialization & Calculation
print(format_header("RUNNING BASELINE MFA CALCULATION"))

print(format_step(Icons.SYSTEM, "2.1", "Setting up model scope..."))
model_classification, index_table = system_setup.define_model_scope(
    start_year, end_year, elements, regions, goods, materials, processes
)

# ### ODYM System Index Table
#
# The IndexTable defines all dimensions used in the MFA system following ODYM conventions.

index_table

print(format_step(Icons.SYSTEM, "2.2", "Initializing MFA system..."))
mfa_system_base = system_setup.initialize_mfa_system(model_classification, index_table)

print(format_step(Icons.DATA_LOADING, "2.3", "Loading processes and data..."))
mfa_system_base, all_excel_data = system_setup.load_and_define_processes(
    mfa_system_base, input_data, data_loader, debug_mode=DEBUG_MODE
)

print(format_step(Icons.DATA_LOADING, "2.4", "Defining flows and parameters..."))
mfa_system_configured, _, flow_tc_map, process_logic_map = (
    system_setup.define_flows_and_parameters(
        mfa_system_base, all_excel_data, debug_mode=DEBUG_MODE
    )
)

print(
    format_step(
        Icons.CONFIGURATION, "2.5", "Loading model parameters (TCs, DSM, FOMP)..."
    )
)

# Centralized call to the new, unified TC loader
time_vector = mfa_system_configured.IndexTable.Classification["Time"].Items
elements_list = mfa_system_configured.Elements
tc_params = data_loader.load_tc_parameters(
    all_excel_data, elements_list, time_vector, debug_mode=DEBUG_MODE
)
mfa_system_configured.ParameterDict.update(
    tc_params
)  # Add the new TC params to the system

# Load other special model parameters
dsm_params = data_loader.load_dsm_parameters(all_excel_data, debug_mode=DEBUG_MODE)
if config_obj.RUN_FOMP_CALCULATION:
    fomp_params = data_loader.load_fomp_parameters(
        all_excel_data, debug_mode=DEBUG_MODE
    )
else:
    fomp_params = {}
lfg_params = data_loader.load_lfg_parameters(all_excel_data, debug_mode=DEBUG_MODE)
uncertainty_params = data_loader.load_uncertainty_definitions(
    all_excel_data, debug_mode=DEBUG_MODE
)

print(format_success("All parameters loaded and configured."))

print(format_step(Icons.CALCULATION, "2.6", "Running baseline calculation..."))
mfa_results_baseline, dsm_details_baseline, _ = solver.run_mfa_calculation(
    mfa_system_configured,
    dsm_params,
    fomp_params,
    config_obj,
    flow_tc_map=flow_tc_map,
    process_logic_map=process_logic_map,
    lfg_params=lfg_params,
)
print(format_success("Baseline calculation completed successfully!"))

# ## 2.2 Data Validation Summary
#
# ### 📋 Summary of Loaded Data

print(format_header("DATA VALIDATION SUMMARY", level=2))

# Count loaded items
num_processes = len(mfa_system_configured.ProcessList)
num_flows = len(mfa_system_configured.FlowDict)
num_stocks = len([k for k in mfa_system_configured.StockDict.keys()])
num_elements = len(elements)
time_span = end_year - start_year + 1

# Count parameters
num_static_tcs = sum(
    1
    for p in mfa_system_configured.ParameterDict.values()
    if "TC" in p.Name and np.isscalar(p.Values)
)
num_dynamic_tcs = sum(
    1
    for p in mfa_system_configured.ParameterDict.values()
    if "TC" in p.Name and isinstance(p.Values, np.ndarray)
)
num_dsm_processes = len(dsm_params) if dsm_params else 0
num_fomp_processes = len(fomp_params) if fomp_params else 0
num_lfg_processes = len(lfg_params) if lfg_params else 0

# Display summary
print("\n📊 Configuration & Scope")
print(f"  ✅ Time range: {start_year}-{end_year} ({time_span} years)")
print(f"  ✅ Elements: {num_elements} defined ({', '.join(elements)})")
print(f"  ✅ Regions: {len(regions)} ({', '.join(regions)})")

print("\n🏗️  System Structure")
print(f"  ✅ Processes: {num_processes} loaded")
print(f"  ✅ Flows: {num_flows} defined")
print(f"  ✅ Stocks: {num_stocks} configured")

print("\n⚙️  Parameters")
print(f"  ✅ Transfer Coefficients:")
print(f"     • Static TCs: {num_static_tcs}")
print(f"     • Dynamic TCs: {num_dynamic_tcs}")
if num_dsm_processes > 0:
    print(f"  ✅ DSM Processes: {num_dsm_processes} configured")
else:
    print(f"  ⚠️  DSM Processes: None configured")
if num_fomp_processes > 0:
    print(f"  ✅ FOMP Processes: {num_fomp_processes} configured")
else:
    print(f"  ⚠️  FOMP Processes: None configured")
if num_lfg_processes > 0:
    print(f"  ✅ LFG Processes: {num_lfg_processes} configured")
else:
    print(f"     LFG Processes: None configured (optional)")

# Check for warnings
warnings_found = []
if num_dsm_processes == 0 and config_obj.RUN_DSM_CALCULATION:
    warnings_found.append("DSM calculation enabled but no processes configured")
if num_fomp_processes == 0 and config_obj.RUN_FOMP_CALCULATION:
    warnings_found.append("FOMP calculation enabled but no processes configured")

# Overall status
print("\n📍 Overall Status")
if len(warnings_found) == 0:
    print("  🟢 ALL SYSTEMS GO - No warnings detected")
    print("  ✅ All required data loaded successfully")
else:
    print(f"  🟡 READY WITH {len(warnings_found)} WARNING(S)")
    for warning in warnings_found:
        print(f"     ⚠️  {warning}")
    print("  ✅ Analysis can proceed (warnings are non-critical)")

print()

# ## 2.3 Mass Balance Verification

print(format_header("MASS BALANCE VERIFICATION (BASELINE)", level=2))
plotting.plot_total_mass_balance_error(mfa_results_baseline)
plotting.plot_optimized_mass_balance_error(mfa_results_baseline)

# ## 2.4 System Flow Diagram (Graphviz)
print(f"\n{Icons.ARROW} System Flow Diagram (Graphviz)")
try:
    from plotting.graphviz_flow_charts import plot_graphviz_flow_chart_sankey_style

    # Get the required dataframes from the loaded data
    processes_data = all_excel_data["2_1_Definition_Processes"]
    flows_data = all_excel_data["1_1_Definition_Flows"]

    # Generate and display the chart
    dot_chart = plot_graphviz_flow_chart_sankey_style(processes_data, flows_data)
    if dot_chart:
        display(dot_chart)
        print(format_success("Graphviz chart created successfully!"))
except ImportError:
    print(f"{Icons.WARNING} Graphviz library not found. Skipping this plot.")
except Exception as e:
    print(f"{Icons.WARNING} Graphviz chart failed: {e}")

# ## 2.5 Flow Composition Validation
print(f"\n{Icons.ARROW} Flow Composition Validation")
print("   • Validates completeness of element composition across all flows")
print("   • Interactive visualization of flow composition hierarchy")
plot_flow_composition(mfa_results_baseline)

# Export flow composition data
from plotting.composition_export import export_flow_composition

export_path = "01_data/02_output/composition/flow_composition.xlsx"
export_flow_composition(mfa_results_baseline, export_path)

# # 3. Visualization
#
# **Note:** All plots in this section are interactive — use the dropdown menus and sliders to
# explore different elements, years, and processes. Use the export buttons to save figures.

print(format_header("VISUALIZATION (BASELINE)"))

# ## 3.1 Sankey Diagrams

# ### 3.1.1 Traditional Sankey (Auto-Layout)
# *Sankey appearance settings (font sizes, node spacing, colors) can be customized in
# [`02_src/plotting/sankey_config.py`](02_src/plotting/sankey_config.py).*
print(f"\n{Icons.ARROW} Traditional Sankey Diagram (Auto-Layout)")
print("   • Single element selection with dropdown")
print("   • Automatic node positioning via topological sort")
print("   • Interactive filtering by year, process, and flow threshold")
plotting.plot_interactive_sankey(mfa_results_baseline, dsm_params, fomp_params)

# ## 3.2 Additional Visualizations
print(f"\n{Icons.ARROW} Additional Visualizations")

# ### 3.2.1 Core System Dynamics
print(f"\n{Icons.VISUALIZATION} Core System Dynamics:")
print("   • Process Dynamics: Interactive 3-panel view (Inflow/Stock/Outflow)")
print("   • Flow Dynamics: Multi-flow time series analysis")
print("   • Stock Analysis: Interactive bar charts with time slider")

# Process Dynamics - 3-panel view showing inflow, stock, and outflow for selected processes
print(f"\n{Icons.MFA} Process Dynamics Analysis:")
plotting.plot_process_dynamics(
    mfa_results_baseline, all_excel_data["2_1_Definition_Processes"]
)

# Flow Dynamics - Multi-flow time series with element selection
print(f"\n{Icons.SANKEY} Flow Dynamics Analysis:")
plotting.plot_flow_dynamics(mfa_results_baseline)

# Stock Bar Chart - Interactive stock levels with time slider
print(f"\n{Icons.BAR_CHART} Stock Levels Analysis:")
plotting.plot_stock_bar_chart(
    mfa_results_baseline, title="Stock Levels Over Time (Baseline)"
)

# System Stock Composition - Individual process stocks over time
print(f"\n{Icons.BAR_CHART} Individual Process Stocks Analysis:")
print("   • Individual process stocks over time")
print("   • Shows each process stock separately")
print("   • Element selection and bar/line chart options")
plotting.plot_system_stock_composition(mfa_results_baseline)

# ### 3.2.2 Specialized Process Analysis (if applicable)
print(f"\n{Icons.VISUALIZATION} Specialized Process Analysis:")

# DSM Stock Details - Detailed DSM stock evolution (if DSM processes exist)
if dsm_params and dsm_details_baseline:
    print(f"\n{Icons.DSM} DSM Stock Evolution Analysis:")
    print("   • Individual and cumulative stock views")
    print("   • Lifetime analysis and category breakdown")
    plotting.plot_dsm_stock_details(
        mfa_results_baseline, dsm_params, dsm_details_baseline
    )

    print(f"\n{Icons.MFA} DSM Process Dynamics Analysis:")
    print("   • Three-panel view: Input, Stock, Output")
    print("   • Stacked flows by element (Material, WC, DM, CC)")
    print("   • Dynamic material composition for DSM processes")
    plotting.plot_dsm_process_dynamics(
        mfa_results_baseline, dsm_params, dsm_details_baseline
    )
else:
    print(f"   {Icons.INFO} No DSM processes found - skipping DSM analysis")

# FOMP Analysis - FOMP mineralization analysis (if FOMP processes exist)
if fomp_params:
    print(f"\n{Icons.FOMP} FOMP Mineralization Analysis:")
    print("   • Organic matter accumulation and mineralization")
    print("   • Annual vs cumulative flow analysis")
    plotting.plot_fomp_stock_details(mfa_results_baseline, fomp_params)

    # FOMP Stock Comparison — all FOMP processes overlaid on one axes
    if len(fomp_params) > 1:
        print(f"\n{Icons.FOMP} FOMP Stock Comparison (all processes):")
        print("   • TC stock trajectories of all FOMP processes on one figure")
        plotting.plot_fomp_stock_comparison(mfa_results_baseline, fomp_params)

    # FOMP Process Dynamics - Three-panel view of FOMP processes
    print(f"\n{Icons.MFA} FOMP Process Dynamics:")
    print(
        "   • Three panels: Input Flows (DM), Stock Evolution (DM), Carbon Emissions (DM)"
    )
    print("   • Decay rates displayed as percentages")
    print("   • Water Content (WC) excluded from carbon emissions")
    plotting.plot_fomp_dynamics(mfa_results_baseline, fomp_params)
else:
    print(f"   {Icons.INFO} No FOMP processes found - skipping FOMP analysis")

# ### 3.2.3 Landfill Gas Analysis
#
# Gas production curves and stable carbon stock evolution for all LFG processes.
# Skipped automatically when no LFG processes are configured.
if lfg_params:
    print(f"\n{Icons.LFG} Landfill Gas Analysis:")
    print("   • CH4 and biogenic CO2 production over time (total)")
    print("   • Stacked area chart: CH4 production by waste fraction")
    print("   • IPCC DOC-based vs MFA TOC-based carbon accounting comparison")
    print("   • Stable carbon stock evolution (residual organic C + ash)")
    plotting.plot_lfg_gas_production(mfa_results_baseline, lfg_params)
    plotting.plot_lfg_fraction_breakdown(mfa_results_baseline, lfg_params)
    plotting.plot_lfg_ipcc_vs_mfa_comparison(mfa_results_baseline, lfg_params)
    plotting.plot_lfg_stock_details(mfa_results_baseline, lfg_params)
else:
    print(f"   {Icons.INFO} No LFG processes found - skipping LFG analysis")


# # 4. Scenario & Uncertainty Manager

# ## 4.1 Scenario Analysis & Comparison
print(format_header("SCENARIO ANALYSIS"))

# Import the new scenario engine
from engine import scenario_engine

# Run scenario analysis using the new engine
all_scenario_results, scenario_definitions = scenario_engine.run_scenario_analysis(
    config_obj=config_obj,
    mfa_system_configured=mfa_system_configured,
    all_excel_data=all_excel_data,
    dsm_params=dsm_params,
    fomp_params=fomp_params,
    flow_tc_map=flow_tc_map,
    process_logic_map=process_logic_map,
)

# Mass balance verification for baseline and all scenarios
print(format_header("SCENARIO MASS BALANCE VERIFICATION", level=2))
scenario_engine.check_mass_balance(mfa_results_baseline, label="Baseline")
for sc_name, sc_result in all_scenario_results.items():
    scenario_engine.check_mass_balance(sc_result, label=sc_name)

# Generate visualizations if scenarios were run
if all_scenario_results:
    scenario_engine.generate_scenario_comparison_visualizations(
        baseline_results=mfa_results_baseline,
        all_scenario_results=all_scenario_results,
        scenario_definitions=scenario_definitions,
    )

    # Mass balance error plots for each scenario
    print(format_header("SCENARIO MASS BALANCE DETAILS", level=2))
    for sc_name, sc_result in all_scenario_results.items():
        print(f"\n{Icons.ARROW} Mass Balance Error: Scenario '{sc_name}'")
        plotting.plot_total_mass_balance_error(
            sc_result,
            enable_export=True,
            export_filename=f"mass_balance_scenario_{sc_name}",
        )

    # Export scenario results
    scenario_engine.export_scenario_results(
        all_scenario_results=all_scenario_results,
        scenario_definitions=scenario_definitions,
    )
else:
    print(f"{Icons.INFO} No scenarios were processed.")

# ## 4.2 Monte Carlo Analysis

# ### 4.2.1 MC Control Board: Parameter Overview

print(format_header("MONTE CARLO CONTROL BOARD", level=2))

if config_obj.RUN_MONTE_CARLO and "4_1_Uncertainty_Parameters" in input_data:
    from reporting.mc_dashboard import build_parameter_overview_df

    mc_params_df = input_data["4_1_Uncertainty_Parameters"]
    param_overview = build_parameter_overview_df(mc_params_df)

    n_iterations = getattr(config_obj, "MC_ITERATIONS", 100)
    print(f"{Icons.MONTE_CARLO} Uncertainty Parameters: {len(param_overview)} defined")
    print(f"   Iterations configured: {n_iterations}\n")

    display(
        param_overview.style.set_caption(
            "Monte Carlo Uncertainty Parameter Definitions"
        )
        .set_table_styles(
            [
                {
                    "selector": "caption",
                    "props": [("font-weight", "bold"), ("font-size", "14px")],
                },
            ]
        )
        .hide(axis="index")
    )
else:
    print(
        f"{Icons.INFO} Monte Carlo analysis is disabled or no uncertainty parameters defined."
    )

# ### 4.2.2 MC Control Board: Validation Report

if config_obj.RUN_MONTE_CARLO and "4_1_Uncertainty_Parameters" in input_data:
    from reporting.mc_dashboard import generate_validation_report

    mc_params_df = input_data["4_1_Uncertainty_Parameters"]

    validation = generate_validation_report(
        uncertainty_params,
        mfa_system_configured,
        dsm_params,
        fomp_params,
        mc_params_df,
    )

    print(f"\n{Icons.ANALYZING} Parameter-to-Model Mapping:")
    display(
        validation["mapping_df"]
        .style.set_caption("Parameter Target Mapping")
        .hide(axis="index")
    )

    if validation["warnings"]:
        print(
            f"\n{Icons.WARNING} Validation Warnings ({len(validation['warnings'])}):"
        )
        for w in validation["warnings"]:
            print(f"   {w}")
    else:
        print(format_success("Validation passed - no warnings detected."))

    print(
        format_success(
            f"MC setup validated: {validation['n_params']} parameters ready for simulation."
        )
    )

# ### 4.2.3 Monte Carlo Simulation Run

print(format_header("MONTE CARLO SIMULATION (BASELINE)", level=2))

if config_obj.RUN_MONTE_CARLO and "4_1_Uncertainty_Parameters" in input_data:
    try:
        from engine.mc_simulation import run_mc_simulation
        from plotting.monte_carlo import (
            plot_interactive_mc_multiple_histograms,
            plot_interactive_tornado,
            plot_interactive_mc_paths,
            plot_interactive_mc_stock_comparison,
        )

        mc_results = run_mc_simulation(
            mfa_system_configured,
            input_data,
            dsm_params,
            fomp_params,
            config_obj,
            process_logic_map=process_logic_map,
            flow_tc_map=flow_tc_map,
        )

        if mc_results is not None and not mc_results.empty:
            print(format_success("Monte Carlo simulation completed for baseline."))

            # --- Export MC Results ---
            print(f"\n{Icons.EXPORT} Exporting Monte Carlo results...")

            # Fixed filename - overwrites previous results
            mc_output_path = "01_data/02_output/mc/mc_results.xlsx"
            try:
                mc_results.to_excel(mc_output_path, index=False)
                print(
                    format_success(
                        f"Monte Carlo results successfully exported to: {mc_output_path}"
                    )
                )
            except Exception as export_error:
                print(
                    f"{Icons.WARNING} Could not export Monte Carlo results: {export_error}"
                )
            # -------------------------

            print(f"\n{Icons.VISUALIZATION} Monte Carlo Analysis Visualizations:")
            print(
                "   - Multiple Distribution Histograms: Interactively select and view histograms for multiple stocks."
            )
            print(
                "   - Sensitivity Tornado Plot: Identify which parameters most influence outcomes."
            )
            print(
                "   - Simulation Paths: Visualize the trajectories of all Monte Carlo runs."
            )
            print(
                "   - Stock Comparison: Compare distributions of several stocks in one plot."
            )

            plot_interactive_mc_multiple_histograms(mc_results, mfa_results_baseline)

            plot_interactive_tornado(mc_results)
            plot_interactive_mc_paths(mc_results, mfa_results_baseline)
            plot_interactive_mc_stock_comparison(mc_results, mfa_results_baseline)

    except Exception as e:
        print(f"{Icons.WARNING} Monte Carlo simulation failed: {e}")
        import traceback

        traceback.print_exc()
else:
    print(
        f"{Icons.INFO} Monte Carlo analysis is disabled or no uncertainty parameters are defined. Skipping."
    )

# ### 4.2.4 MC Summary Statistics

if (
    config_obj.RUN_MONTE_CARLO
    and "mc_results" in dir()
    and mc_results is not None
    and not mc_results.empty
):
    from reporting.mc_dashboard import compute_mc_summary_stats

    print(format_header("MONTE CARLO SUMMARY STATISTICS", level=2))

    mc_summary = compute_mc_summary_stats(mc_results, mfa_system_configured)

    display(
        mc_summary.style.format(
            {
                "Mean": "{:,.2f}",
                "Std": "{:,.2f}",
                "Median": "{:,.2f}",
                "CI95_Lower": "{:,.2f}",
                "CI95_Upper": "{:,.2f}",
                "Min": "{:,.2f}",
                "Max": "{:,.2f}",
            }
        )
        .set_caption(
            f"Stock Summary Statistics ({getattr(config_obj, 'MC_ITERATIONS', 100)} iterations)"
        )
        .hide(axis="index")
    )

    print(
        format_success(
            f"Summary statistics computed for {len(mc_summary)} stock-element combinations."
        )
    )

    # Mass balance check
    from reporting.mc_dashboard import compute_mc_mass_balance_report

    mb_report = compute_mc_mass_balance_report(mc_results)
    if mb_report is not None:
        print(format_header("MASS BALANCE CHECK", level=2))
        print("System-level summary (across all elements):")
        display(
            mb_report["summary"]
            .style.format(
                {
                    "Mean Abs. Error": "{:.2e}",
                    "Max Abs. Error": "{:.2e}",
                    "Mean Rel. Error (%)": "{:.2e}",
                    "Max Rel. Error (%)": "{:.2e}",
                    "Iterations with Error > 1%": "{:d}",
                }
            )
            .hide(axis="index")
        )
        if not mb_report["per_element"].empty:
            print("\nPer-element breakdown:")
            display(
                mb_report["per_element"]
                .style.format(
                    {
                        "Mean Input": "{:,.2f}",
                        "Mean Abs. Error": "{:.2e}",
                        "Max Abs. Error": "{:.2e}",
                        "Rel. Error (%)": "{:.2e}",
                    }
                )
                .hide(axis="index")
            )

# # 5. Data Export

print(format_header("EXPORTING BASELINE RESULTS"))

# ## 5.1 KPI Dashboard and Export

kpi_output_path = "01_data/02_output/kpi/system_kpis.xlsx"
print(format_step(Icons.EXPORT, "5.1", "Generating KPI Dashboard..."))
kpi_dashboard.generate_kpi_dashboard(
    mfa_results_baseline, process_logic_map, kpi_output_path
)

print(format_step(Icons.EXPORT, "5.2", "Exporting baseline results..."))
output_file = "01_data/02_output/results/results_baseline.xlsx"
utils.export_results_to_excel(
    mfa_results_baseline, output_file, input_file_path=input_file
)
print(format_success(f"Baseline results exported to: {output_file}"))

# ## 5.2 Sankey Export
#
# Export the Sankey diagram in four formats for use in external tools.
#
# > **Element layers:** Each element (material, WC, DM, CC) produces a separate
# > Sankey file — Sankey tools display one flow layer at a time. All elements are
# > exported by default; restrict via `export_elements` in the config block below.
#
# | Format | Subfolder | Use with |
# |--------|-----------|----------|
# | `.html` | `sankey/html/` | Any browser — share interactively |
# | `.json` | `sankey/json/` | Web developers, D3.js-based viewers |
# | `.csv`  | `sankey/esankey/` | **e!Sankey** by ifu Hamburg — import via *Data → Import* |
# | `.txt`  | `sankey/sankeymatic/` | **SankeyMATIC** — paste at sankeymatic.com |
#
# Files are named `sankey_{element}_{year}.ext` (e.g., `sankey_CC_2030.html`).

from pathlib import Path
from plotting.sankey import (
    export_sankey_json,
    export_sankey_html,
    export_sankey_csv,
    export_sankey_sankeymatic,
)

# ─── Sankey Export Configuration ─────────────────────────────────────────────
export_years    = [int(mfa_results_baseline.Time_V[-1])]   # add more years: [2025, 2030]

# All elements in the model (auto-detected) — or restrict: ["material", "CC"]
all_elements    = list(mfa_results_baseline.IndexTable.Classification["Element"].Items)
export_elements = all_elements

min_flow        = 0.0   # omit flows below this absolute value (Mg)
# ─────────────────────────────────────────────────────────────────────────────

sankey_root = Path("01_data/02_output/sankey")

for year in export_years:
    for element in export_elements:
        base = f"sankey_{element}_{year}"
        print(f"\n{Icons.SANKEY} Exporting Sankey — {element} | {year}")

        export_sankey_html(
            mfa_results_baseline, year, element,
            filepath=sankey_root / "html" / f"{base}.html",
            dsm_params=dsm_details_baseline, fomp_params=None,
            min_flow=min_flow,
            title=f"BioDYM — {element} ({year})",
        )
        export_sankey_json(
            mfa_results_baseline, year, element,
            filepath=sankey_root / "json" / f"{base}.json",
            dsm_params=dsm_details_baseline, fomp_params=None,
            min_flow=min_flow,
        )
        export_sankey_csv(
            mfa_results_baseline, year, element,
            filepath=sankey_root / "esankey" / f"{base}.csv",
            min_flow=min_flow,
        )
        export_sankey_sankeymatic(
            mfa_results_baseline, year, element,
            filepath=sankey_root / "sankeymatic" / f"{base}.txt",
            min_flow=min_flow,
        )

print(f"\n{Icons.SUCCESS} All Sankey exports saved to: {sankey_root.resolve()}")

print(format_header("ANALYSIS COMPLETE"))
