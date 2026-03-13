# -*- coding: utf-8 -*-
# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# # BioDYM Dashboard
#
# Enter the path to your Excel input file and click **Run Analysis**.
# All plots will appear in the tabs below — no code editing required.

# +
import os
import sys
import warnings

import ipywidgets as w
import plotly.graph_objects as go
from IPython.display import display, clear_output

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

# Resolve paths relative to this file's directory so the notebook
# works regardless of where Voilà is launched from.
_here = os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else os.getcwd()
sys.path.insert(0, os.path.join(_here, "02_src"))
sys.path.insert(0, os.path.join(_here, "06_framework", "ODYM-master_20241127", "odym", "modules"))
sys.path.insert(0, os.path.join(_here, "06_framework", "bioDYM_add-on", "modules"))

import config as _config_module
import data_loader
import system_setup
import plotting
from engine import solver, scenario_engine
from engine.mc_simulation import run_mc_simulation
from constants import Icons
from plotting.composition import plot_flow_composition
from reporting.kpi_dashboard import (
    calculate_system_kpis,
    calculate_system_overview,
    calculate_stock_analysis,
)
# -

# +
# ── UI layout ─────────────────────────────────────────────────────────────

# Make all Plotly figures fill their container width in Voilà.
# Overrides hardcoded pixel widths set by get_publication_layout().
_PLOTLY_CSS = w.HTML("""<style>
  .plotly-graph-div { width: 100% !important; min-width: 0 !important; }
</style>""")

_HEADER = w.HTML("""
<div style="font-family:sans-serif; padding:20px 0 10px 0; border-bottom:2px solid #e0e0e0; margin-bottom:16px">
  <h2 style="margin:0; color:#2c3e50; font-size:24px">📊 BioDYM Dashboard</h2>
  <p style="color:#666; margin:6px 0 0 0; font-size:14px">
    Interactive results viewer — provide the Excel input file and click Run.
  </p>
</div>
""")

_file_input = w.Text(
    value=os.path.join(_here, "01_data", "01_input", ""),
    placeholder="path/to/your_input.xlsm",
    layout=w.Layout(width="640px"),
    style={"description_width": "0px"},
)

_run_btn = w.Button(
    description="▶  Run Analysis",
    button_style="success",
    icon="play",
    layout=w.Layout(width="170px", height="36px"),
)

_status    = w.Output()
_dashboard = w.Output()

# ── Monte Carlo section (hidden until baseline finishes) ──────────────────
_mc_run_btn = w.Button(
    description="🎲  Run Monte Carlo",
    button_style="warning",
    layout=w.Layout(width="200px", height="36px"),
)
_mc_status  = w.Output()
_mc_output  = w.Output()
_mc_section = w.VBox([
    w.HTML("<div style='border-top:1px solid #e0e0e0; margin:16px 0 8px 0'></div>"),
    w.HBox([_mc_run_btn]),
    _mc_status,
    _mc_output,
])
_mc_section.layout.visibility = "hidden"

display(w.VBox([
    _PLOTLY_CSS,
    _HEADER,
    w.HBox([
        w.HTML("<span style='font-family:sans-serif; line-height:36px; margin-right:10px; color:#444; font-size:14px'>📂 Input file:</span>"),
        _file_input,
        w.HTML("<div style='width:10px'></div>"),
        _run_btn,
    ]),
    _status,
    _dashboard,
    _mc_section,
]))
# -

# +
# ── Analysis + dashboard builder (runs on button click) ───────────────────

# Shared state dict — populated by _build_dashboard, consumed by _run_mc
_state: dict = {}


def _build_dashboard(btn):  # noqa: C901
    _run_btn.disabled = True
    _run_btn.description = "⏳  Running…"
    _mc_section.layout.visibility = "hidden"

    with _status:
        clear_output(wait=True)
        print("⏳  Loading data and running calculation — please wait (~30 s)…")

    with _dashboard:
        clear_output(wait=True)
    with _mc_output:
        clear_output(wait=True)

    input_file = _file_input.value.strip()

    # ── 1. Validate file path ────────────────────────────────────────────
    if not os.path.exists(input_file):
        with _status:
            clear_output(wait=True)
            print(f"❌  File not found: {input_file}")
        _run_btn.disabled = False
        _run_btn.description = "▶  Run Analysis"
        return

    # ── 2. Load & calculate ──────────────────────────────────────────────
    try:
        os.chdir(_here)  # ensure relative paths inside BioDYM work

        pd = __import__("pandas")
        input_data = pd.read_excel(
            input_file, sheet_name=None, header=0, engine="openpyxl",
            na_values=["N.A.", "NA", "n/a"], decimal=",",
        )
        cfg = _config_module.load_configuration(input_file)

        def _get_list(attr, default=None):
            v = getattr(cfg, attr, None)
            if v and pd.notna(v):
                return [x.strip() for x in str(v).split(",") if x.strip()]
            return default

        regions   = _get_list("Regions", ["Case_Study_Region"])
        goods     = _get_list("Goods")
        materials = _get_list("Materials")
        processes = _get_list("Process_Types")

        start_year = int(cfg.Start_Year)
        end_year   = int(cfg.End_Year)
        elements   = [e.strip() for e in cfg.Elements.split(",")]

        model_cls, idx_table = system_setup.define_model_scope(
            start_year, end_year, elements, regions, goods, materials, processes
        )
        mfa_base = system_setup.initialize_mfa_system(model_cls, idx_table)
        mfa_base, all_excel_data = system_setup.load_and_define_processes(
            mfa_base, input_data, data_loader, debug_mode=False
        )
        mfa_configured, _, flow_tc_map, process_logic_map = (
            system_setup.define_flows_and_parameters(mfa_base, all_excel_data, debug_mode=False)
        )
        time_vector   = mfa_configured.IndexTable.Classification["Time"].Items
        elements_list = mfa_configured.Elements
        tc_params = data_loader.load_tc_parameters(all_excel_data, elements_list, time_vector)
        mfa_configured.ParameterDict.update(tc_params)

        dsm_params  = data_loader.load_dsm_parameters(all_excel_data)
        fomp_params = (
            data_loader.load_fomp_parameters(all_excel_data)
            if cfg.RUN_FOMP_CALCULATION else {}
        )
        lfg_params = data_loader.load_lfg_parameters(all_excel_data)

        mfa_results, dsm_details, _ = solver.run_mfa_calculation(
            mfa_configured, dsm_params, fomp_params, cfg,
            flow_tc_map=flow_tc_map, process_logic_map=process_logic_map,
            lfg_params=lfg_params,
        )

        # ── Scenarios (fast, run with baseline) ─────────────────────────
        with _status:
            clear_output(wait=True)
            print("✅  Baseline done — running scenarios…")

        scenario_defs_raw = data_loader.load_scenario_definitions(all_excel_data)
        has_scenarios = bool(scenario_defs_raw)
        all_scenario_results, scenario_definitions = {}, {}
        if has_scenarios:
            all_scenario_results, scenario_definitions = scenario_engine.run_scenario_analysis(
                config_obj=cfg,
                mfa_system_configured=mfa_configured,
                all_excel_data=all_excel_data,
                dsm_params=dsm_params,
                fomp_params=fomp_params,
                flow_tc_map=flow_tc_map,
                process_logic_map=process_logic_map,
            )

    except Exception as exc:
        with _status:
            clear_output(wait=True)
            print(f"❌  Calculation failed: {exc}")
        _run_btn.disabled = False
        _run_btn.description = "▶  Run Analysis"
        return

    # Save state for the MC button
    _state.update(dict(
        mfa_configured=mfa_configured,
        input_data=input_data,
        dsm_params=dsm_params,
        fomp_params=fomp_params,
        cfg=cfg,
        process_logic_map=process_logic_map,
        flow_tc_map=flow_tc_map,
        mfa_results=mfa_results,
    ))

    # ── 3. Build tab widgets ─────────────────────────────────────────────
    with _status:
        clear_output(wait=True)
        print("✅  Calculations complete — building plots…")

    def _scrollable(out_widget):
        """Wrap an Output widget in a fixed-height scrollable box."""
        return w.Box(
            [out_widget],
            layout=w.Layout(overflow_y="auto", height="680px", width="100%"),
        )

    # Sankey
    t_sankey = w.Output()
    with t_sankey:
        try:
            plotting.plot_interactive_sankey(mfa_results, dsm_params, fomp_params)
        except Exception as e:
            print(f"⚠️  Sankey plot failed: {e}")

    # Flows & Processes
    t_flows = w.Output()
    with t_flows:
        try:
            plotting.plot_flow_dynamics(mfa_results)
            plotting.plot_process_dynamics(mfa_results, all_excel_data["2_1_Definition_Processes"])
        except Exception as e:
            print(f"⚠️  Flows/Processes plot failed: {e}")

    # Flow Composition
    t_composition = w.Output()
    with t_composition:
        try:
            plot_flow_composition(mfa_results)
        except Exception as e:
            print(f"⚠️  Flow Composition plot failed: {e}")

    # Stocks
    t_stocks = w.Output()
    with t_stocks:
        try:
            plotting.plot_stock_bar_chart(mfa_results, title="Stock Levels Over Time")
            plotting.plot_system_stock_composition(mfa_results)
        except Exception as e:
            print(f"⚠️  Stocks plot failed: {e}")

    # Process Models (DSM / FOMP / LFG — conditional)
    model_sections = []
    if dsm_params and dsm_details:
        dsm_out = w.Output()
        with dsm_out:
            try:
                plotting.plot_dsm_stock_details(mfa_results, dsm_params, dsm_details)
                plotting.plot_dsm_process_dynamics(mfa_results, dsm_params, dsm_details)
            except Exception as e:
                print(f"⚠️  DSM plot failed: {e}")
        model_sections.append(dsm_out)

    if fomp_params:
        fomp_out = w.Output()
        with fomp_out:
            try:
                plotting.plot_fomp_stock_details(mfa_results, fomp_params)
                plotting.plot_fomp_dynamics(mfa_results, fomp_params)
            except Exception as e:
                print(f"⚠️  FOMP plot failed: {e}")
        model_sections.append(fomp_out)

    if lfg_params:
        lfg_out = w.Output()
        with lfg_out:
            try:
                plotting.plot_lfg_gas_production(mfa_results, lfg_params)
                plotting.plot_lfg_fraction_breakdown(mfa_results, lfg_params)
                plotting.plot_lfg_ipcc_vs_mfa_comparison(mfa_results, lfg_params)
                plotting.plot_lfg_stock_details(mfa_results, lfg_params)
            except Exception as e:
                print(f"⚠️  LFG plot failed: {e}")
        model_sections.append(lfg_out)

    # Scenarios (conditional)
    t_scenarios = w.Output()
    if has_scenarios and all_scenario_results:
        with t_scenarios:
            try:
                plotting.plot_multi_scenario_comparison(
                    mfa_results, all_scenario_results, scenario_definitions
                )
                plotting.plot_scenario_flow_dynamics(
                    mfa_results, all_scenario_results, scenario_definitions
                )
                plotting.plot_scenario_stock_dynamics(
                    mfa_results, all_scenario_results, scenario_definitions
                )
            except Exception as e:
                print(f"⚠️  Scenario plot failed: {e}")

    # KPI
    t_kpi = w.Output()
    with t_kpi:
        try:
            kpi_df      = calculate_system_kpis(mfa_results, process_logic_map)
            overview_df = calculate_system_overview(mfa_results, process_logic_map, kpi_df)
            stock_df    = calculate_stock_analysis(mfa_results)
            display(overview_df.style.set_caption("System Overview"))
            display(stock_df.style.set_caption("Stock Analysis"))
            display(kpi_df.style.set_caption("Annual KPIs"))
        except Exception as e:
            print(f"⚠️  KPI failed: {e}")

    # Validation
    t_validation = w.Output()
    with t_validation:
        try:
            plotting.plot_total_mass_balance_error(mfa_results)
            plotting.plot_optimized_mass_balance_error(mfa_results)
        except Exception as e:
            print(f"⚠️  Validation plot failed: {e}")

    # ── 4. Assemble tabs ─────────────────────────────────────────────────
    tab_children = [
        _scrollable(t_sankey),
        _scrollable(t_flows),
        _scrollable(t_composition),
        _scrollable(t_stocks),
    ]
    tab_titles = ["🔀 Sankey", "📈 Flows & Processes", "🧪 Composition", "📦 Stocks"]

    if model_sections:
        tab_children.append(_scrollable(w.VBox(model_sections)))
        tab_titles.append("⚙️ Process Models")

    if has_scenarios and all_scenario_results:
        tab_children.append(_scrollable(t_scenarios))
        tab_titles.append("📊 Scenarios")

    tab_children.append(_scrollable(t_kpi))
    tab_titles.append("📋 KPI")

    tab_children.append(_scrollable(t_validation))
    tab_titles.append("✅ Validation")

    tabs = w.Tab(children=tab_children)
    for i, title in enumerate(tab_titles):
        tabs.set_title(i, title)

    with _dashboard:
        display(tabs)

    with _status:
        clear_output(wait=True)
        n_tabs = len(tab_titles)
        suffix = " (scenarios included)" if has_scenarios else ""
        print(f"✅  Dashboard ready — {n_tabs} tabs loaded{suffix}.")

    _run_btn.disabled = False
    _run_btn.description = "🔄  Re-run"
    _mc_section.layout.visibility = "visible"


_run_btn.on_click(_build_dashboard)


# ── Monte Carlo on-demand handler ─────────────────────────────────────────

def _run_mc(btn):  # noqa: C901
    _mc_run_btn.disabled = True
    _mc_run_btn.description = "⏳  Running…"

    with _mc_status:
        clear_output(wait=True)
        print("⏳  Running Monte Carlo simulation — this may take several minutes…")
    with _mc_output:
        clear_output(wait=True)

    s = _state
    if not s:
        with _mc_status:
            clear_output(wait=True)
            print("❌  Run baseline analysis first.")
        _mc_run_btn.disabled = False
        _mc_run_btn.description = "🎲  Run Monte Carlo"
        return

    try:
        mc_results = run_mc_simulation(
            s["mfa_configured"],
            s["input_data"],
            s["dsm_params"],
            s["fomp_params"],
            s["cfg"],
            process_logic_map=s["process_logic_map"],
            flow_tc_map=s["flow_tc_map"],
        )
    except Exception as exc:
        with _mc_status:
            clear_output(wait=True)
            print(f"❌  MC failed: {exc}")
        _mc_run_btn.disabled = False
        _mc_run_btn.description = "🎲  Run Monte Carlo"
        return

    if mc_results is None or (hasattr(mc_results, "empty") and mc_results.empty):
        with _mc_status:
            clear_output(wait=True)
            print("⚠️  MC returned no results. Check MC_ITERATIONS in configuration.")
        _mc_run_btn.disabled = False
        _mc_run_btn.description = "🔄  Re-run MC"
        return

    mfa_results = s["mfa_results"]

    mc_hist = w.Output()
    with mc_hist:
        try:
            plotting.plot_interactive_mc_multiple_histograms(mc_results, mfa_results)
        except Exception as e:
            print(f"⚠️  MC histogram failed: {e}")

    mc_tornado = w.Output()
    with mc_tornado:
        try:
            plotting.plot_interactive_tornado(mc_results)
        except Exception as e:
            print(f"⚠️  Tornado plot failed: {e}")

    mc_paths = w.Output()
    with mc_paths:
        try:
            plotting.plot_interactive_mc_paths(mc_results, mfa_results)
        except Exception as e:
            print(f"⚠️  MC paths failed: {e}")

    mc_compare = w.Output()
    with mc_compare:
        try:
            plotting.plot_interactive_mc_stock_comparison(mc_results, mfa_results)
        except Exception as e:
            print(f"⚠️  MC comparison failed: {e}")

    mc_tabs = w.Tab(children=[
        w.Box([mc_hist],    layout=w.Layout(overflow_y="auto", height="680px", width="100%")),
        w.Box([mc_tornado], layout=w.Layout(overflow_y="auto", height="680px", width="100%")),
        w.Box([mc_paths],   layout=w.Layout(overflow_y="auto", height="680px", width="100%")),
        w.Box([mc_compare], layout=w.Layout(overflow_y="auto", height="680px", width="100%")),
    ])
    for i, title in enumerate(["📊 Distributions", "🌪️ Sensitivity", "📈 Time Paths", "🔀 Comparison"]):
        mc_tabs.set_title(i, title)

    with _mc_output:
        display(mc_tabs)

    with _mc_status:
        clear_output(wait=True)
        n_iter = len(mc_results)
        print(f"✅  MC complete — {n_iter} iterations, 4 tabs loaded.")

    _mc_run_btn.disabled = False
    _mc_run_btn.description = "🔄  Re-run MC"


_mc_run_btn.on_click(_run_mc)
# -
