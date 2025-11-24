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
# - **Issues**: [GitHub Issues](https://github.com/your-repo/BioDYM/issues)
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
import plotly.express as px
from plotly.subplots import make_subplots
from IPython.display import display, HTML, Markdown
import copy

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
# See 05_docs/DECIMAL_SEPARATOR_GUIDE.md for details
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

# ============================================================================
# DEBUG: Check TC Normalization for Dynamic TCs
# ============================================================================
if DEBUG_MODE or True:  # Always run this check for now
    print("\n" + "=" * 80)
    print("🔍 DIAGNOSTIC: Checking Dynamic TC Normalization")
    print("=" * 80)

    static_tc_defs = all_excel_data.get("2_2_static_TCs")
    process_defs = all_excel_data.get("2_1_Definition_Processes")

    if static_tc_defs is not None and process_defs is not None:
        # Group TCs by process and element
        process_tc_groups = {}

        for _, row in static_tc_defs.iterrows():
            pid = row.get("Process_ID")
            if pd.isna(pid):
                continue
            pid = int(pid)

            for elem_idx, element in enumerate(elements_list):
                tc_id_col = f"E{elem_idx + 1}_TC_ID"
                if tc_id_col not in row.index:
                    tc_id_col = f"TC_{element}_ID"

                if tc_id_col in row.index and pd.notna(row[tc_id_col]):
                    tc_name = row[tc_id_col]
                    if tc_name in tc_params:
                        key = (pid, element)
                        if key not in process_tc_groups:
                            process_tc_groups[key] = []
                        if tc_name not in process_tc_groups[key]:
                            process_tc_groups[key].append(tc_name)

        # Check each process-element group
        issues_found = False
        for (pid, element), tc_names in process_tc_groups.items():
            if len(tc_names) <= 1:
                continue  # Skip single-TC processes

            # Get process name
            proc_row = process_defs[process_defs["Process_ID"] == pid]
            proc_name = (
                proc_row["Process_Name"].values[0]
                if not proc_row.empty
                else f"Process_{pid}"
            )

            # Check if any TC is dynamic
            is_dynamic = any(
                isinstance(tc_params[tc].Values, np.ndarray)
                for tc in tc_names
                if tc in tc_params
            )

            if not is_dynamic:
                continue

            # Calculate sum
            tc_sum = np.zeros(len(time_vector))
            for tc_name in tc_names:
                if tc_name in tc_params:
                    val = tc_params[tc_name].Values
                    if isinstance(val, np.ndarray):
                        tc_sum += val
                    else:
                        tc_sum += val

            # Check deviation
            max_dev = np.max(np.abs(tc_sum - 1.0))

            if max_dev > 1e-6:
                issues_found = True
                print(
                    f"\n❌ Process {pid} ({proc_name}), {element}: TCs DO NOT sum to 1.0!"
                )
                print(f"   TCs: {tc_names}")
                print(f"   Sum range: {tc_sum.min():.6f} - {tc_sum.max():.6f}")
                print(f"   Max deviation: {max_dev:.6e}")

                # Show sample years
                sample_indices = [0, len(time_vector) // 2, len(time_vector) - 1]
                for idx in sample_indices:
                    year = time_vector[idx]
                    print(f"   Year {year}: Sum = {tc_sum[idx]:.6f}")
                    for tc in tc_names:
                        val = tc_params[tc].Values
                        tc_val = val[idx] if isinstance(val, np.ndarray) else val
                        print(f"      {tc} = {tc_val:.6f}")
            else:
                print(
                    f"✅ Process {pid} ({proc_name}), {element}: TCs sum to 1.0 (max dev: {max_dev:.6e})"
                )

        if not issues_found:
            print("\n✅ All dynamic TCs sum to 1.0 - normalization working correctly!")
        else:
            print(
                "\n⚠️  WARNING: Some TCs do not sum to 1.0 - check data or normalization!"
            )
    else:
        print("⚠️  Cannot check TCs: Missing static TC definitions or process list")

    print("=" * 80 + "\n")

# Load other special model parameters
dsm_params = data_loader.load_dsm_parameters(all_excel_data, debug_mode=DEBUG_MODE)
if config_obj.RUN_FOMP_CALCULATION:
    fomp_params = data_loader.load_fomp_parameters(
        all_excel_data, debug_mode=DEBUG_MODE
    )
else:
    fomp_params = {}
uncertainty_params = data_loader.load_uncertainty_definitions(
    all_excel_data, debug_mode=DEBUG_MODE
)

print(format_success("All parameters loaded and configured."))

print(format_step(Icons.CALCULATION, "2.6", "Running baseline calculation..."))
mfa_results_baseline, dsm_details_baseline = solver.run_mfa_calculation(
    mfa_system_configured,
    dsm_params,
    fomp_params,
    config_obj,
    flow_tc_map=flow_tc_map,
    process_logic_map=process_logic_map,
)
print(format_success("Baseline calculation completed successfully!"))

# ============================================================================
# DEBUG: Check Mass Balance Per Process
# ============================================================================
if DEBUG_MODE or True:  # Always run this check for now
    print("\n" + "=" * 80)
    print("🔍 DIAGNOSTIC: Mass Balance Check Per Process")
    print("=" * 80)

    significant_errors = []

    for process_id, process in mfa_results_baseline.ProcessDict.items():
        # Get inflows and outflows
        inflows = [
            f for f in mfa_results_baseline.FlowDict.values() if f.P_End == process_id
        ]
        outflows = [
            f for f in mfa_results_baseline.FlowDict.values() if f.P_Start == process_id
        ]

        if not inflows or not outflows:
            continue  # Skip boundary processes

        # Calculate balance for material element (E1)
        elem_idx = 0  # Material
        total_in = sum(
            f.Values[:, elem_idx] for f in inflows if f.Values is not None
        )
        total_out = sum(
            f.Values[:, elem_idx] for f in outflows if f.Values is not None
        )

        # Check for stock
        stock = mfa_results_baseline.StockDict.get(process_id)
        stock_change = np.zeros(len(time_vector))
        if stock and stock.Values is not None:
            if len(stock.Values.shape) > 1:
                stock_vals = stock.Values[:, elem_idx]
                stock_change = np.diff(stock_vals, prepend=0)

        balance = total_in - total_out - stock_change
        max_error = np.max(np.abs(balance))

        if max_error > 0.01:  # Significant error threshold
            significant_errors.append((process_id, process.Name, max_error, balance))

    # Report results
    if significant_errors:
        print(f"\n❌ Found {len(significant_errors)} processes with significant errors:\n")
        for pid, pname, max_err, balance in significant_errors:
            print(f"Process {pid} ({pname}): Max error = {max_err:.3f}")

            worst_idx = np.argmax(np.abs(balance))
            print(f"   Worst year: {time_vector[worst_idx]}")

            # Get flows for this process
            inflows = [
                f for f in mfa_results_baseline.FlowDict.values() if f.P_End == pid
            ]
            outflows = [
                f for f in mfa_results_baseline.FlowDict.values() if f.P_Start == pid
            ]

            total_in = sum(
                f.Values[worst_idx, 0] for f in inflows if f.Values is not None
            )
            total_out = sum(
                f.Values[worst_idx, 0] for f in outflows if f.Values is not None
            )

            print(f"   Total in:  {total_in:.6f}")
            print(f"   Total out: {total_out:.6f}")
            print(f"   Error:     {balance[worst_idx]:.6f}")

            # Show individual outflows
            print(f"   Outflows:")
            for f in outflows:
                if f.Values is not None:
                    val = f.Values[worst_idx, 0]
                    tc_effective = val / total_in if total_in > 0 else 0
                    print(f"      {f.Name}: {val:.6f} (TC ≈ {tc_effective:.4f})")

            # Check TC sum
            tc_names_for_process = []
            static_tc_defs = all_excel_data.get("2_2_static_TCs")
            if static_tc_defs is not None:
                proc_tcs = static_tc_defs[static_tc_defs["Process_ID"] == pid]
                if not proc_tcs.empty:
                    for col in proc_tcs.columns:
                        if col.endswith("_TC_ID"):
                            tc_names = proc_tcs[col].dropna().unique()
                            tc_names_for_process.extend(tc_names)

            if tc_names_for_process:
                print(f"   Expected TCs: {tc_names_for_process}")
                tc_sum = sum(
                    (
                        tc_params[tc].Values[worst_idx]
                        if isinstance(tc_params[tc].Values, np.ndarray)
                        else tc_params[tc].Values
                    )
                    for tc in tc_names_for_process
                    if tc in tc_params
                )
                print(f"   TC sum at worst year: {tc_sum:.6f}")

            print()
    else:
        print("\n✅ All processes have acceptable mass balance (errors < 0.01)")

    print("=" * 80 + "\n")

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

export_path = "01_data/02_output/composition_export/flow_composition.xlsx"
export_flow_composition(mfa_results_baseline, export_path)

# # 3. Visualization

print(format_header("VISUALIZATION (BASELINE)"))

# ## 3.1 Sankey Diagrams

# ### 3.1.1 Traditional Sankey (Auto-Layout)
print(f"\n{Icons.ARROW} Traditional Sankey Diagram (Auto-Layout)")
print("   • Single element selection with dropdown")
print("   • Automatic node positioning via topological sort")
print("   • Interactive filtering by year, process, and flow threshold")
plotting.plot_interactive_sankey(mfa_results_baseline, dsm_params, fomp_params)

# ### 3.1.2 Enhanced Sankey (Custom Positioning)
print(f"\n{Icons.ARROW} Enhanced Sankey Diagram (Custom Positioning)")
print("   • Custom node positioning from Excel configuration")
print("   • Toggle between Custom and Auto-Layout modes")
print("   • Element-specific layouts for showing hierarchy")
print("   • Special process highlighting (DSM, FOMP)")
plotting.plot_enhanced_sankey(
    mfa_results_baseline,
    dsm_params=dsm_params,
    fomp_params=fomp_params,
    visualization_config_path=input_file,
)


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

    # FOMP Process Dynamics - Three-panel view of FOMP processes
    print(f"\n{Icons.MFA} FOMP Process Dynamics:")
    print(
        "   • Three panels: Input Flows (DM), Stock Evolution (DM), Mineralization Output (DM)"
    )
    print("   • Decay rates displayed as percentages")
    print("   • Water Content (WC) excluded from mineralization")
    plotting.plot_fomp_dynamics(mfa_results_baseline, fomp_params)
else:
    print(f"   {Icons.INFO} No FOMP processes found - skipping FOMP analysis")


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

# Generate visualizations if scenarios were run
if all_scenario_results:
    scenario_engine.generate_scenario_comparison_visualizations(
        baseline_results=mfa_results_baseline,
        all_scenario_results=all_scenario_results,
        scenario_definitions=scenario_definitions,
    )

    # Export scenario results
    scenario_engine.export_scenario_results(
        all_scenario_results=all_scenario_results,
        scenario_definitions=scenario_definitions,
    )
else:
    print(f"{Icons.INFO} No scenarios were processed.")

# ## 4.2 Monte Carlo Analysis
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
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            mc_output_path = (
                f"01_data/02_output/mc_output/mc_results_detailed_{timestamp}.xlsx"
            )
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
                "   • Multiple Distribution Histograms: Interactively select and view histograms for multiple stocks."
            )
            print(
                "   • Sensitivity Tornado Plot: Identify which parameters most influence outcomes."
            )
            print(
                "   • Simulation Paths: Visualize the trajectories of all Monte Carlo runs."
            )
            print(
                "   • Stock Comparison: Compare distributions of several stocks in one plot."
            )

            # This new function allows selecting multiple histograms, making the old single one redundant.
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

# # 5. Data Export

print(format_header("EXPORTING BASELINE RESULTS"))

# ## 5.1 KPI Dashboard and Export

kpi_output_path = "01_data/02_output/kpi_dashboard/system_kpis.xlsx"
print(format_step(Icons.EXPORT, "5.1", "Generating KPI Dashboard..."))
kpi_dashboard.generate_kpi_dashboard(
    mfa_results_baseline, process_logic_map, kpi_output_path
)

print(format_step(Icons.EXPORT, "5.2", "Exporting baseline results..."))
output_file = "01_data/02_output/results_scientific_baseline.xlsx"
utils.export_results_to_excel(
    mfa_results_baseline, output_file, input_file_path=input_file
)
print(format_success(f"Baseline results exported to: {output_file}"))

print(format_header("ANALYSIS COMPLETE"))
