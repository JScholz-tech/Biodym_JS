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
# *See [README.md](README.md#-acknowledgments) for contributors and acknowledgments.*
#
# ### 📄 License
# This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.
# Built on the [ODYM Framework](https://github.com/IndEcol/ODYM) (Pauliuk & Heeren, 2020)
#
# ---
#
# ### 📖 Table of Contents
#
# 0. **Introduction** — quick start & key commands
# 1. **Setup and Data Loading** — environment, input file, system configuration
# 2. **Calculation & Mass Balance** — run the MFA and verify mass conservation
# 3. **Visualization** — Sankey, stocks, flows, and process dynamics
# 4. **Scenario & Uncertainty Manager** — scenario comparison & Monte Carlo
# 5. **Data Export** — KPI dashboard, results, and Sankey exports
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
# **Welcome to BioDYM!** This notebook runs a complete Material Flow Analysis — from
# data loading to results export. See [README.md](README.md) for full setup details.
#
# ### ⌨️ Most important commands
#
# | Purpose | Command |
# |---------|---------|
# | **First use** — install dependencies | `uv sync` |
# | Open this notebook | `uv run jupyter lab` |
# | _(optional)_ run the test suite | `uv run pytest` |
# | **bioDYM SystemDefiner** — define a system visually (→ http://localhost:8001) | `uv run python -m systemdefiner` |
# | **System Dashboard** (Voilà) | `uv run voila 01_BioDYM_Dashboard.ipynb` |
#
# ### Getting started in 3 steps
#
# 1. **Set your input** in Section 1.2 — a BioDYM Excel (`.xlsm`/`.xlsx`) **or** a
#    `config.yaml` exported from the SystemDefiner. The bundled template is the
#    default, so you can **Kernel → Restart & Run All** right away.
# 2. **Run all cells** in order.
# 3. **Explore** the interactive plots; results are written to `01_data/02_output/`.
#
# ### 🔧 Debug Mode
# Set `DEBUG_MODE = True` below for detailed technical output during data loading and
# calculation (default `False` = clean, user-friendly output).

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
from IPython.display import display

# Suppress openpyxl data validation warnings (harmless, caused by Excel dropdown rules)
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

# Put the source root + ODYM/bioDYM framework dirs on sys.path so the
# digit-prefixed packages import. 02_src must be added first so `bootstrap`
# itself is importable; setup_paths() then adds the framework module dirs.
sys.path.insert(0, os.path.join(os.getcwd(), "02_src"))
from bootstrap import setup_paths, init_widgets

project_root = setup_paths()

# Import BioDYM modules
try:
    import config
    import data_loader
    import system_setup
    import utils
    from engine import solver
    from engine import scenario_engine
    import plotting
    import ODYM_Classes as msc
    from plotting.composition import plot_flow_composition
    from plotting.composition_export import export_flow_composition
    from reporting import kpi_dashboard
    from reporting.validation_summary import display_system_summary

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

# ── Plot theme ───────────────────────────────────────────────────────────────
# 'exploratory' → 1000×800 px, large fonts, titles visible, legend below (default)
# 'jie'         → 672×432 px (7×4.5 in), 11 pt fonts, no title, legend below
PLOT_THEME = "exploratory"
plotting.set_theme(PLOT_THEME)
print(f"{Icons.CONFIGURATION} Plot theme: '{PLOT_THEME}'")

# Pre-initialise the interactive widget system (prevents the first plot from
# rendering empty in Jupyter / Voilà).
print(f"{Icons.CONFIGURATION} Initializing interactive widget system...")
if init_widgets():
    print(f"{Icons.SUCCESS} Widget system initialized successfully")
else:
    print(f"{Icons.INFO} Plots may take longer on first render")

# ## 1.2 Data Input Configuration
#
# ### ⚙️ EDIT THIS — your input file
#
# Set `input_file` to your BioDYM Excel (.xlsx / .xlsm) **or** to a YAML
# config produced by the bioDYM SystemDefiner (.yaml / .yml).
#
# Excel mode:  input_file = "01_data/01_input/myfile.xlsm"
# YAML mode:   input_file = "case_studies/my_study/config.yaml"
#              (Excel path is read from model.input_file inside the YAML)
#
# The default below is the bundled template — a complete, runnable example, so a
# fresh checkout runs end-to-end with no setup. Point it at your own file to
# analyse your own system.

input_file = "01_data/01_input/template/260503_bioDYM_Systemmanager_template_final.xlsm"

# ### Advanced (optional) — leave as None for a normal run
#
# When input_file is a YAML and model.input_file inside it is empty or
# incorrect, set this to your Excel path to override it.
excel_file_override = None  # e.g. "01_data/01_input/myfile.xlsm"

# Optional: combine an Excel-based run with a separate YAML from the web app.
# Set automatically below when input_file is a YAML. Set manually when you
# want to use YAML scenarios/MC alongside an Excel-defined system.
yaml_config_file = None  # e.g. "case_studies/my_study/config.yaml"

# --- detect whether input_file is YAML or Excel and configure accordingly ---
_yaml_only_mode = False
_input_suffix = os.path.splitext(input_file)[1].lower()
if _input_suffix in (".yaml", ".yml"):
    import yaml as _yaml_mod
    with open(input_file, encoding="utf-8") as _f:
        _yaml_raw = _yaml_mod.safe_load(_f) or {}
    yaml_config_file = input_file
    _excel_from_yaml = (_yaml_raw.get("model") or {}).get("input_file", "")
    input_file = excel_file_override or _excel_from_yaml or None
    if input_file and os.path.exists(input_file):
        print(f"📋 YAML config: {yaml_config_file}")
        print(format_file_path(input_file))
    else:
        _yaml_only_mode = True
        input_file = None
        print(f"📋 YAML-only mode: {yaml_config_file}")
        print("   All model data synthesized from YAML — no Excel file needed.")
else:
    print(format_file_path(input_file))
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Excel file not found: {input_file}")

# ## 1.3 System Configuration Extraction

if _yaml_only_mode:
    print(format_header("EXTRACTING CONFIGURATION FROM YAML"))
    input_data = data_loader.yaml_to_excel_dataframes(yaml_config_file)
    print(format_success(f"YAML synthesized: {len(input_data)} sheet-equivalent DataFrames"))
    config_obj = config.load_config_from_yaml(yaml_config_file)
    print(format_success("Configuration object loaded from YAML."))
else:
    print(format_header("EXTRACTING CONFIGURATION FROM EXCEL"))
    # Load the full dataset once. NOTE: Uses decimal=',' for European standard.
    input_data = pd.read_excel(
        input_file,
        sheet_name=None,
        header=0,
        engine="openpyxl",
        na_values=["N.A.", "NA", "n/a"],
        decimal=",",
    )
    print(format_success(f"Excel file loaded: {len(input_data)} sheets"))
    config_obj = config.load_configuration(input_file)
    print(format_success("Configuration object loaded."))
plotting.set_mass_unit_from_config(config_obj)
plotting.set_theme(PLOT_THEME)  # re-assert theme so it wins over config unit

dims              = config.extract_workflow_dimensions(config_obj, input_data)
start_year        = dims["start_year"]
end_year          = dims["end_year"]
elements          = dims["elements"]
regions           = dims["regions"]
goods             = dims["goods"]
materials         = dims["materials"]
processes         = dims["processes"]
run_scenario      = dims["run_scenario"]
selected_scenario = dims["selected_scenario"]

# # 2. Calculation & Mass Balance

# ## 2.1 Model Initialization & Calculation
print(format_header("RUNNING BASELINE MFA CALCULATION"))

print(format_step(Icons.SYSTEM, "2.1.1", "Setting up model scope..."))
model_classification, index_table = system_setup.define_model_scope(
    start_year, end_year, elements, regions, goods, materials, processes
)

# ### ODYM System Index Table
#
# The IndexTable defines all dimensions used in the MFA system following ODYM conventions.

index_table

print(format_step(Icons.SYSTEM, "2.1.2", "Initializing MFA system..."))
mfa_system_base = system_setup.initialize_mfa_system(
    model_classification, index_table, unit=config.resolve_unit(config_obj)
)

print(format_step(Icons.DATA_LOADING, "2.1.3", "Loading processes and data..."))
mfa_system_base, all_excel_data = system_setup.load_and_define_processes(
    mfa_system_base, input_data, data_loader, debug_mode=DEBUG_MODE
)

if yaml_config_file and not _yaml_only_mode:
    _flow_df = data_loader.load_flow_data_df_from_yaml(yaml_config_file)
    if not _flow_df.empty:
        all_excel_data["1_2_Data_Flows"] = _flow_df

print(format_step(Icons.DATA_LOADING, "2.1.4", "Defining flows and parameters..."))
mfa_system_configured, _, flow_tc_map, process_logic_map = (
    system_setup.define_flows_and_parameters(
        mfa_system_base, all_excel_data, debug_mode=DEBUG_MODE
    )
)

print(
    format_step(
        Icons.CONFIGURATION, "2.1.5", "Loading model parameters (TCs, DSM, FOMP)..."
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

# Load DSM/FOMP/LFG/FlowCap/BOM parameters — from YAML web-app config or Excel.
_params = data_loader.load_all_parameters(
    all_excel_data,
    config_obj,
    yaml_config_file=yaml_config_file,
    elements=mfa_system_configured.Elements,
    debug_mode=DEBUG_MODE,
)
dsm_params = _params["dsm"]
fomp_params = _params["fomp"]
lfg_params = _params["lfg"]
flow_cap_params = _params["flow_cap"]
bom_params = _params["bom"]
data_loader.register_flow_cap_parameters(mfa_system_configured, flow_cap_params)

# Filter fomp_params and lfg_params against process_logic_map so the Excel
# Process_Logic column acts as the authoritative enable/disable switch.
# (DSM is already filtered at load time inside load_dsm_parameters.)
if process_logic_map:
    fomp_params = {pid: p for pid, p in fomp_params.items()
                   if process_logic_map.get(pid) == "FOMP"}
    lfg_params  = {pid: p for pid, p in lfg_params.items()
                   if process_logic_map.get(pid) == "LFG"}

if yaml_config_file:
    uncertainty_params = data_loader.load_uncertainty_definitions_from_yaml(yaml_config_file)
else:
    uncertainty_params = data_loader.load_uncertainty_definitions(
        all_excel_data, debug_mode=DEBUG_MODE
    )

print(format_success("All parameters loaded and configured."))

print(format_step(Icons.CALCULATION, "2.1.6", "Running baseline calculation..."))
mfa_results_baseline, dsm_details_baseline, solver_info_baseline = solver.run_mfa_calculation(
    mfa_system_configured,
    dsm_params,
    fomp_params,
    config_obj,
    flow_tc_map=flow_tc_map,
    process_logic_map=process_logic_map,
    lfg_params=lfg_params,
    bom_params=bom_params,
    flow_cap_params=flow_cap_params,
)
fomp_details_baseline = solver_info_baseline.get("fomp_details", {})
print(format_success("Baseline calculation completed successfully!"))

# ## 2.2 Data Validation Summary
#
# ### 📋 Summary of Loaded Data

print(format_header("DATA VALIDATION SUMMARY", level=2))

display_system_summary(
    mfa_system_configured, config_obj, elements, regions,
    start_year, end_year, dsm_params, fomp_params, lfg_params,
)

# ## 2.3 Mass Balance Verification

print(format_header("MASS BALANCE VERIFICATION (BASELINE)", level=2))
plotting.plot_total_mass_balance_error(
    mfa_results_baseline,
    dsm_params=dsm_params,
    fomp_params=fomp_params,
)
plotting.plot_optimized_mass_balance_error(
    mfa_results_baseline,
    dsm_params=dsm_params,
    fomp_params=fomp_params,
)
plotting.plot_dynamic_process_balance(
    mfa_results_baseline,
    dsm_params=dsm_params,
    fomp_params=fomp_params,
)

# ## 2.4 System Flow Diagram (Graphviz)
#
# A static node-link overview of the system, laid out Sankey-style.
# Skipped automatically if the optional `graphviz` library isn't installed.

try:
    # Local import: graphviz is an optional dependency.
    from plotting.graphviz_flow_charts import plot_graphviz_flow_chart_sankey_style

    processes_data = all_excel_data["2_1_Definition_Processes"]
    flows_data = all_excel_data["1_1_Definition_Flows"]

    dot_chart = plot_graphviz_flow_chart_sankey_style(processes_data, flows_data)
    if dot_chart:
        display(dot_chart)
        print(format_success("Graphviz chart created successfully!"))
except ImportError:
    print(f"{Icons.WARNING} Graphviz library not found. Skipping this plot.")
except Exception as e:
    print(f"{Icons.WARNING} Graphviz chart failed: {e}")

# ## 2.5 Flow Composition Validation
#
# - Validates completeness of element composition across all flows
# - Interactive visualization of the flow composition hierarchy

plot_flow_composition(mfa_results_baseline)

# Export flow composition data
export_path = "01_data/02_output/composition/flow_composition.xlsx"
export_flow_composition(mfa_results_baseline, export_path)

# # 3. Visualization
#
# **Note:** All plots in this section are interactive — use the dropdown menus and
# sliders to explore different elements, years, and processes. Use the export buttons
# to save figures.

print(format_header("VISUALIZATION (BASELINE)"))
_t = plotting.get_active_theme()
print(f"  Theme '{PLOT_THEME}': {_t['width']}×{_t['height']}px | "
      f"fonts {_t['font_tick']}pt | legend {'below' if _t['legend_below'] else 'inside'} | "
      f"title {'hidden' if not _t['show_title'] else 'visible'}")

# ## 3.1 Sankey Diagrams
#
# ### 3.1.1 Traditional Sankey (Auto-Layout)
#
# - Single element selection with dropdown
# - Automatic node positioning via topological sort
# - Interactive filtering by year, process, and flow threshold
#
# *Appearance settings (fonts, node spacing, colors) live in
# [`02_src/plotting/sankey_config.py`](02_src/plotting/sankey_config.py).*

plotting.plot_interactive_sankey(mfa_results_baseline, dsm_params, fomp_params, bom_params=bom_params)

# ## 3.2 Additional Visualizations
#
# ### 3.2.1 Core System Dynamics
#
# - **Process Dynamics** — interactive 3-panel view (inflow / stock / outflow)
# - **Flow Dynamics** — multi-flow time series with element selection
# - **Stock Levels** — interactive bar charts with a time slider
# - **Process Stocks** — each process stock separately, bar/line + element selection

plotting.plot_process_dynamics(
    mfa_results_baseline, all_excel_data["2_1_Definition_Processes"]
)
plotting.plot_flow_dynamics(mfa_results_baseline)
plotting.plot_stock_bar_chart(
    mfa_results_baseline, title="Stock Levels Over Time (Baseline)"
)
plotting.plot_system_stock_composition(mfa_results_baseline)

# ### 3.2.2 Specialized Process Analysis (if applicable)
#
# DSM and FOMP plots below render only when the model contains such processes;
# otherwise the section prints a short "skipped" note.

# DSM Stock Details — detailed DSM stock evolution (if DSM processes exist)
if dsm_params and dsm_details_baseline:
    # Individual and cumulative stock views; lifetime + category breakdown.
    plotting.plot_dsm_stock_details(
        mfa_results_baseline, dsm_params, dsm_details_baseline
    )

    # Publication figure: JIE-format stacked cohort areas, policy line 2075.
    _dsm_pid = next(iter(dsm_params))
    plotting.plot_dsm_stock_publication(
        mfa_results_baseline,
        dsm_details_baseline,
        process_id=_dsm_pid,
        element="material",
        policy_year=2075,
    )

    # Three-panel input/stock/output, stacked by element.
    plotting.plot_dsm_process_dynamics(
        mfa_results_baseline, dsm_params, dsm_details_baseline
    )
else:
    print(f"   {Icons.INFO} No DSM processes found - skipping DSM analysis")

# FOMP mineralization analysis (if FOMP processes exist)
if fomp_params:
    # Organic-matter accumulation/mineralization; annual vs cumulative.
    plotting.plot_fomp_stock_details(mfa_results_baseline, fomp_params)

    # All FOMP processes' TC stock trajectories on one figure.
    if len(fomp_params) > 1:
        plotting.plot_fomp_stock_comparison(
            mfa_results_baseline,
            fomp_params,
            fomp_details=solver_info_baseline.get("fomp_details"),
        )

    # Labile vs recalcitrant pool stocks, stacked over time.
    if fomp_details_baseline:
        plotting.plot_fomp_pool_breakdown(
            mfa_results_baseline, fomp_params, fomp_details_baseline
        )

    # Three-panel input/stock/carbon-emissions (DM); WC excluded from emissions.
    plotting.plot_fomp_dynamics(mfa_results_baseline, fomp_params)
else:
    print(f"   {Icons.INFO} No FOMP processes found - skipping FOMP analysis")

# ### 3.2.3 Landfill Gas Analysis
#
# For all LFG processes (skipped automatically when none are configured):
# - CH₄ and biogenic CO₂ production over time (total)
# - Stacked area: CH₄ production by waste fraction
# - IPCC DOC-based vs MFA TOC-based carbon accounting comparison
# - Stable carbon stock evolution (residual organic C + ash)
if lfg_params:
    plotting.plot_lfg_gas_production(mfa_results_baseline, lfg_params)
    plotting.plot_lfg_fraction_breakdown(mfa_results_baseline, lfg_params)
    plotting.plot_lfg_ipcc_vs_mfa_comparison(mfa_results_baseline, lfg_params)
    plotting.plot_lfg_stock_details(mfa_results_baseline, lfg_params)
else:
    print(f"   {Icons.INFO} No LFG processes found - skipping LFG analysis")

# ### 3.2.4 BOM Assembler Analysis
#
# For all BOM_Assembler processes (skipped automatically when none are configured):
# - Assembled product vs. residue (stacked) per element
# - Assembly efficiency (%) — fraction of inflow becoming product
if bom_params:
    plotting.plot_bom_assembly_flows(mfa_results_baseline, bom_params)
else:
    print(f"   {Icons.INFO} No BOM Assembler processes found - skipping BOM analysis")


# # 4. Scenario & Uncertainty Manager

# ## 4.1 Scenario Analysis & Comparison
print(format_header("SCENARIO ANALYSIS"))

# Load scenario definitions — from YAML (web app) or Excel sheet
_scenario_defs_preloaded = (
    data_loader.load_scenario_definitions_from_yaml(yaml_config_file)
    if yaml_config_file else None
)

# Run scenario analysis using the new engine
all_scenario_results, scenario_definitions = scenario_engine.run_scenario_analysis(
    config_obj=config_obj,
    mfa_system_configured=mfa_system_configured,
    all_excel_data=all_excel_data,
    dsm_params=dsm_params,
    fomp_params=fomp_params,
    flow_tc_map=flow_tc_map,
    process_logic_map=process_logic_map,
    lfg_params=lfg_params,
    bom_params=bom_params,
    flow_cap_params=flow_cap_params,
    scenario_definitions=_scenario_defs_preloaded,
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
#
# Propagate input uncertainty through the model. This whole section runs only when
# `RUN_MONTE_CARLO` is enabled **and** a `4_1_Uncertainty_Parameters` sheet exists —
# captured once below as `mc_enabled` and reused by every sub-section.

from reporting import mc_dashboard

mc_enabled = bool(getattr(config_obj, "RUN_MONTE_CARLO", False)) and (
    "4_1_Uncertainty_Parameters" in input_data
)
mc_results = None  # populated by the simulation run (§4.2.3) when MC is enabled

# ### 4.2.1 MC Control Board: Parameter Overview

print(format_header("MONTE CARLO CONTROL BOARD", level=2))

if mc_enabled:
    param_overview = mc_dashboard.build_parameter_overview_df(
        input_data["4_1_Uncertainty_Parameters"]
    )

    n_iterations = getattr(config_obj, "MC_ITERATIONS", 100)
    print(f"{Icons.MONTE_CARLO} Uncertainty Parameters: {len(param_overview)} defined")
    print(f"   Iterations configured: {n_iterations}\n")

    display(mc_dashboard.style_parameter_overview(param_overview))
else:
    print(
        f"{Icons.INFO} Monte Carlo analysis is disabled or no uncertainty parameters defined."
    )

# ### 4.2.2 MC Control Board: Validation Report

if mc_enabled:
    validation = mc_dashboard.generate_validation_report(
        uncertainty_params,
        mfa_system_configured,
        dsm_params,
        fomp_params,
        input_data["4_1_Uncertainty_Parameters"],
    )

    print(f"\n{Icons.ANALYZING} Parameter-to-Model Mapping:")
    display(mc_dashboard.style_parameter_mapping(validation["mapping_df"]))

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
#
# Runs the simulation, exports results to `01_data/02_output/mc/mc_results.xlsx`,
# and shows four interactive views:
# - **Multiple histograms** — distributions for several stocks
# - **Tornado** — parameter sensitivity ranking
# - **Simulation paths** — all MC trajectories
# - **Stock comparison** — several stock distributions in one plot

print(format_header("MONTE CARLO SIMULATION (BASELINE)", level=2))

if mc_enabled:
    try:
        # Local imports: MC engine + plots are only needed when MC is enabled.
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

            mc_output_path = "01_data/02_output/mc/mc_results.xlsx"
            try:
                mc_results.to_excel(mc_output_path, index=False)
                print(format_success(f"Monte Carlo results exported to: {mc_output_path}"))
            except Exception as export_error:
                print(f"{Icons.WARNING} Could not export Monte Carlo results: {export_error}")

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

if mc_enabled and mc_results is not None and not mc_results.empty:
    print(format_header("MONTE CARLO SUMMARY STATISTICS", level=2))

    mc_summary = mc_dashboard.compute_mc_summary_stats(
        mc_results, mfa_system_configured
    )
    display(
        mc_dashboard.style_summary_stats(
            mc_summary, getattr(config_obj, "MC_ITERATIONS", 100)
        )
    )
    print(
        format_success(
            f"Summary statistics computed for {len(mc_summary)} stock-element combinations."
        )
    )

    # Mass balance check across all MC iterations
    mb_report = mc_dashboard.compute_mc_mass_balance_report(mc_results)
    if mb_report is not None:
        print(format_header("MASS BALANCE CHECK", level=2))
        print("System-level summary (across all elements):")
        display(mc_dashboard.style_mass_balance_summary(mb_report["summary"]))
        if not mb_report["per_element"].empty:
            print("\nPer-element breakdown:")
            display(
                mc_dashboard.style_mass_balance_per_element(mb_report["per_element"])
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
# | `.txt`  | `sankey/sankeymatic/` | **SankeyMATIC** — paste at sankeymatic.com |
# | `.xlsx` | `sankey/structuralcollective/` | **Structural Collective MFA Tool** — import at mfa.structuralcollective.nl |
#
# Files are named `sankey_{element}_{year}.ext` (e.g., `sankey_TC_2125.html`).

from plotting.sankey import export_sankey_batch

# ─── Sankey Export Configuration ─────────────────────────────────────────────
export_years    = [int(mfa_results_baseline.Time_V[-1])]   # add more years: [2025, 2030]

# All elements in the model (auto-detected) — or restrict: ["material", "CC"]
export_elements = list(mfa_results_baseline.IndexTable.Classification["Element"].Items)

min_flow        = 0.0   # omit flows below this absolute value (Mg)
# ─────────────────────────────────────────────────────────────────────────────

export_sankey_batch(
    mfa_results_baseline,
    export_years=export_years,
    export_elements=export_elements,
    sankey_root="01_data/02_output/sankey",
    dsm_params=dsm_details_baseline,
    process_logic_map=process_logic_map,
    min_flow=min_flow,
)

print(format_header("ANALYSIS COMPLETE"))
