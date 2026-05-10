import marimo

__generated_with = "0.23.5"
app = marimo.App(width="full", app_title="BioDYM Dashboard")


@app.cell
def _():
    import os
    import sys
    import warnings
    import marimo as mo
    import plotly.graph_objects as go

    warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.join(here, "02_src"))
    sys.path.insert(0, os.path.join(here, "06_framework", "ODYM-master_20241127", "odym", "modules"))
    sys.path.insert(0, os.path.join(here, "06_framework", "bioDYM_add-on", "modules"))

    import config as config_module
    import data_loader
    import system_setup
    import plotting
    from engine import solver, scenario_engine
    from engine.mc_simulation import run_mc_simulation
    from plotting.composition import plot_flow_composition
    from reporting.kpi_dashboard import (
        calculate_system_kpis,
        calculate_system_overview,
        calculate_stock_analysis,
    )

    return (
        calculate_stock_analysis,
        calculate_system_kpis,
        calculate_system_overview,
        config_module,
        data_loader,
        here,
        mo,
        os,
        plot_flow_composition,
        plotting,
        run_mc_simulation,
        scenario_engine,
        solver,
        system_setup,
    )


@app.cell
def _(mo):
    file_upload = mo.ui.file(
        filetypes=[".xlsm"],
        label="📂 Upload input file (.xlsm)",
        multiple=False,
    )
    run_btn = mo.ui.run_button(label="▶  Run Analysis")
    return file_upload, run_btn


@app.cell
def _(file_upload, mo, run_btn):
    mo.vstack([
        mo.md("# BioDYM Dashboard"),
        mo.md("*Upload your .xlsm file, then click Run Analysis.*"),
        mo.hstack([file_upload, run_btn], align="end", gap=2),
    ])
    return


@app.cell
def _(
    config_module,
    data_loader,
    file_upload,
    here,
    mo,
    os,
    run_btn,
    scenario_engine,
    solver,
    system_setup,
):
    import pandas as pd
    import tempfile

    mo.stop(
        not run_btn.value,
        mo.callout(mo.md("Upload an **.xlsm** file above, then click **▶ Run Analysis**."), kind="info"),
    )

    _files = file_upload.value
    mo.stop(
        not _files,
        mo.callout(mo.md("Please **upload an .xlsm input file** first."), kind="warn"),
    )

    # Save uploaded bytes to a temp file so downstream code gets a real path
    _tmp = tempfile.NamedTemporaryFile(suffix=".xlsm", prefix="BioDYM_upload_", delete=False)
    _tmp.write(_files[0].contents)
    _tmp.close()
    _input_file = _tmp.name

    os.chdir(here)

    _input_data = pd.read_excel(
        _input_file, sheet_name=None, header=0, engine="openpyxl",
        na_values=["N.A.", "NA", "n/a"], decimal=",",
    )
    _cfg = config_module.load_configuration(_input_file)

    def _get_list(attr, default=None):
        v = getattr(_cfg, attr, None)
        if v and pd.notna(v):
            return [x.strip() for x in str(v).split(",") if x.strip()]
        return default

    _regions   = _get_list("Regions", ["Case_Study_Region"])
    _goods     = _get_list("Goods")
    _materials = _get_list("Materials")
    _processes = _get_list("Process_Types")
    _start     = int(_cfg.Start_Year)
    _end       = int(_cfg.End_Year)
    _elements  = [e.strip() for e in _cfg.Elements.split(",")]

    _model_cls, _idx_table = system_setup.define_model_scope(
        _start, _end, _elements, _regions, _goods, _materials, _processes
    )
    _mfa_base = system_setup.initialize_mfa_system(_model_cls, _idx_table)
    _mfa_base, _all_excel_data = system_setup.load_and_define_processes(
        _mfa_base, _input_data, data_loader, debug_mode=False
    )
    _mfa_cfg, _, _flow_tc_map, _process_logic_map = system_setup.define_flows_and_parameters(
        _mfa_base, _all_excel_data, debug_mode=False
    )
    _time_vec = _mfa_cfg.IndexTable.Classification["Time"].Items
    _elem_lst = _mfa_cfg.Elements
    _tc_params = data_loader.load_tc_parameters(_all_excel_data, _elem_lst, _time_vec)
    _mfa_cfg.ParameterDict.update(_tc_params)

    _dsm_params  = data_loader.load_dsm_parameters(_all_excel_data)
    _fomp_params = data_loader.load_fomp_parameters(_all_excel_data) if _cfg.RUN_FOMP_CALCULATION else {}
    _lfg_params  = data_loader.load_lfg_parameters(_all_excel_data)

    if _process_logic_map:
        _fomp_params = {pid: p for pid, p in _fomp_params.items() if _process_logic_map.get(pid) == "FOMP"}
        _lfg_params  = {pid: p for pid, p in _lfg_params.items()  if _process_logic_map.get(pid) == "LFG"}

    _mfa_results, _dsm_details, _solver_info = solver.run_mfa_calculation(
        _mfa_cfg, _dsm_params, _fomp_params, _cfg,
        flow_tc_map=_flow_tc_map, process_logic_map=_process_logic_map, lfg_params=_lfg_params,
    )
    _fomp_details = _solver_info.get("fomp_details", {})

    _scenario_defs_raw = data_loader.load_scenario_definitions(_all_excel_data)
    _has_scenarios = bool(_scenario_defs_raw)
    _all_scenario_results, _scenario_definitions = {}, {}
    if _has_scenarios:
        _all_scenario_results, _scenario_definitions = scenario_engine.run_scenario_analysis(
            config_obj=_cfg,
            mfa_system_configured=_mfa_cfg,
            all_excel_data=_all_excel_data,
            dsm_params=_dsm_params,
            fomp_params=_fomp_params,
            flow_tc_map=_flow_tc_map,
            process_logic_map=_process_logic_map,
        )

    # Expose as public names for downstream cells
    mfa_results          = _mfa_results
    dsm_params           = _dsm_params
    dsm_details          = _dsm_details
    fomp_params          = _fomp_params
    fomp_details         = _fomp_details
    lfg_params           = _lfg_params
    cfg                  = _cfg
    all_excel_data       = _all_excel_data
    input_data           = _input_data
    process_logic_map    = _process_logic_map
    flow_tc_map          = _flow_tc_map
    mfa_configured       = _mfa_cfg
    has_scenarios        = _has_scenarios
    all_scenario_results = _all_scenario_results
    scenario_definitions = _scenario_definitions
    return (
        all_excel_data,
        all_scenario_results,
        cfg,
        dsm_details,
        dsm_params,
        flow_tc_map,
        fomp_details,
        fomp_params,
        has_scenarios,
        input_data,
        lfg_params,
        mfa_configured,
        mfa_results,
        process_logic_map,
        scenario_definitions,
    )


@app.cell
def _(dsm_params, fomp_params, mfa_results, mo, plotting, run_btn):
    mo.stop(not run_btn.value)
    try:
        with mo.capture() as _cap_sankey:
            plotting.plot_interactive_sankey(mfa_results, dsm_params, fomp_params)
        t_sankey = _cap_sankey.as_html()
    except Exception as _e:
        t_sankey = mo.callout(mo.md(f"⚠️  Sankey plot failed: {_e}"), kind="warn")
    return (t_sankey,)


@app.cell
def _(all_excel_data, mfa_results, mo, plotting, run_btn):
    mo.stop(not run_btn.value)
    try:
        with mo.capture() as _cap_flows:
            plotting.plot_flow_dynamics(mfa_results)
            plotting.plot_process_dynamics(mfa_results, all_excel_data["2_1_Definition_Processes"])
        t_flows = _cap_flows.as_html()
    except Exception as _e:
        t_flows = mo.callout(mo.md(f"⚠️  Flows plot failed: {_e}"), kind="warn")
    return (t_flows,)


@app.cell
def _(mfa_results, mo, plot_flow_composition, run_btn):
    mo.stop(not run_btn.value)
    try:
        with mo.capture() as _cap_comp:
            plot_flow_composition(mfa_results)
        t_composition = _cap_comp.as_html()
    except Exception as _e:
        t_composition = mo.callout(mo.md(f"⚠️  Composition plot failed: {_e}"), kind="warn")
    return (t_composition,)


@app.cell
def _(mfa_results, mo, plotting, run_btn):
    mo.stop(not run_btn.value)
    try:
        with mo.capture() as _cap_stocks:
            plotting.plot_stock_bar_chart(mfa_results, title="Stock Levels Over Time")
            plotting.plot_system_stock_composition(mfa_results)
        t_stocks = _cap_stocks.as_html()
    except Exception as _e:
        t_stocks = mo.callout(mo.md(f"⚠️  Stocks plot failed: {_e}"), kind="warn")
    return (t_stocks,)


@app.cell
def _(
    dsm_details,
    dsm_params,
    fomp_details,
    fomp_params,
    lfg_params,
    mfa_results,
    mo,
    plotting,
    run_btn,
):
    mo.stop(not run_btn.value)
    _model_parts = []

    if dsm_params and dsm_details:
        try:
            with mo.capture() as _c:
                plotting.plot_dsm_stock_details(mfa_results, dsm_params, dsm_details)
                plotting.plot_dsm_process_dynamics(mfa_results, dsm_params, dsm_details)
            _model_parts.append(_c.as_html())
        except Exception as _e:
            _model_parts.append(mo.callout(mo.md(f"⚠️  DSM plot failed: {_e}"), kind="warn"))

    if fomp_params:
        try:
            with mo.capture() as _c:
                plotting.plot_fomp_stock_details(mfa_results, fomp_params)
                if fomp_details:
                    plotting.plot_fomp_pool_breakdown(mfa_results, fomp_params, fomp_details)
                plotting.plot_fomp_dynamics(mfa_results, fomp_params)
            _model_parts.append(_c.as_html())
        except Exception as _e:
            _model_parts.append(mo.callout(mo.md(f"⚠️  FOMP plot failed: {_e}"), kind="warn"))

    if lfg_params:
        try:
            with mo.capture() as _c:
                plotting.plot_lfg_gas_production(mfa_results, lfg_params)
                plotting.plot_lfg_fraction_breakdown(mfa_results, lfg_params)
                plotting.plot_lfg_ipcc_vs_mfa_comparison(mfa_results, lfg_params)
                plotting.plot_lfg_stock_details(mfa_results, lfg_params)
            _model_parts.append(_c.as_html())
        except Exception as _e:
            _model_parts.append(mo.callout(mo.md(f"⚠️  LFG plot failed: {_e}"), kind="warn"))

    t_models = mo.vstack(_model_parts) if _model_parts else mo.callout(
        mo.md("No DSM, FOMP, or LFG processes configured."), kind="info"
    )
    has_models = bool(_model_parts)
    return has_models, t_models


@app.cell
def _(
    all_scenario_results,
    has_scenarios,
    mfa_results,
    mo,
    plotting,
    run_btn,
    scenario_definitions,
):
    mo.stop(not run_btn.value)
    if has_scenarios and all_scenario_results:
        try:
            with mo.capture() as _cap_sc:
                plotting.plot_multi_scenario_comparison(mfa_results, all_scenario_results, scenario_definitions)
                plotting.plot_scenario_flow_dynamics(mfa_results, all_scenario_results, scenario_definitions)
                plotting.plot_scenario_stock_dynamics(mfa_results, all_scenario_results, scenario_definitions)
            t_scenarios = _cap_sc.as_html()
        except Exception as _e:
            t_scenarios = mo.callout(mo.md(f"⚠️  Scenario plot failed: {_e}"), kind="warn")
    else:
        t_scenarios = mo.callout(mo.md("No scenarios configured in this model."), kind="info")
    return (t_scenarios,)


@app.cell
def _(
    calculate_stock_analysis,
    calculate_system_kpis,
    calculate_system_overview,
    mfa_results,
    mo,
    process_logic_map,
    run_btn,
):
    mo.stop(not run_btn.value)
    try:
        _kpi_df      = calculate_system_kpis(mfa_results, process_logic_map)
        _overview_df = calculate_system_overview(mfa_results, process_logic_map, _kpi_df)
        _stock_df    = calculate_stock_analysis(mfa_results)
        t_kpi = mo.vstack([
            mo.md("### System Overview"),
            mo.ui.table(_overview_df) if hasattr(mo.ui, "table") else _overview_df,
            mo.md("### Stock Analysis"),
            mo.ui.table(_stock_df) if hasattr(mo.ui, "table") else _stock_df,
            mo.md("### Annual KPIs"),
            mo.ui.table(_kpi_df) if hasattr(mo.ui, "table") else _kpi_df,
        ])
    except Exception as _e:
        t_kpi = mo.callout(mo.md(f"⚠️  KPI calculation failed: {_e}"), kind="warn")
    return (t_kpi,)


@app.cell
def _(mfa_results, mo, plotting, run_btn):
    mo.stop(not run_btn.value)
    try:
        with mo.capture() as _cap_val:
            plotting.plot_total_mass_balance_error(mfa_results)
            plotting.plot_optimized_mass_balance_error(mfa_results)
        t_validation = _cap_val.as_html()
    except Exception as _e:
        t_validation = mo.callout(mo.md(f"⚠️  Validation plot failed: {_e}"), kind="warn")
    return (t_validation,)


@app.cell
def _(
    has_models,
    has_scenarios,
    mo,
    run_btn,
    t_composition,
    t_flows,
    t_kpi,
    t_models,
    t_sankey,
    t_scenarios,
    t_stocks,
    t_validation,
):
    mo.stop(not run_btn.value)
    _tab_dict = {
        "🔀 Sankey":            t_sankey,
        "📈 Flows & Processes": t_flows,
        "🧪 Composition":       t_composition,
        "📦 Stocks":            t_stocks,
    }
    if has_models:
        _tab_dict["⚙️ Process Models"] = t_models
    if has_scenarios:
        _tab_dict["📊 Scenarios"] = t_scenarios
    _tab_dict["📋 KPI"]         = t_kpi
    _tab_dict["✅ Validation"]  = t_validation
    return


@app.cell
def _(mo, run_btn):
    mo.stop(not run_btn.value)
    mc_btn = mo.ui.run_button(label="🎲  Run Monte Carlo")
    return (mc_btn,)


@app.cell
def _(
    cfg,
    dsm_params,
    flow_tc_map,
    fomp_params,
    input_data,
    mc_btn,
    mfa_configured,
    mfa_results,
    mo,
    plotting,
    process_logic_map,
    run_btn,
    run_mc_simulation,
):
    mo.stop(not run_btn.value)
    mo.stop(not mc_btn.value, mo.callout(mo.md("Click **🎲 Run Monte Carlo** to run the uncertainty analysis."), kind="info"))

    try:
        _mc_results = run_mc_simulation(
            mfa_configured, input_data, dsm_params, fomp_params, cfg,
            process_logic_map=process_logic_map, flow_tc_map=flow_tc_map,
        )
    except Exception as _e:
        mo.stop(True, mo.callout(mo.md(f"**MC failed:** {_e}"), kind="danger"))

    if _mc_results is None or (hasattr(_mc_results, "empty") and _mc_results.empty):
        mo.stop(True, mo.callout(mo.md("⚠️  MC returned no results. Check MC_ITERATIONS in configuration."), kind="warn"))

    try:
        with mo.capture() as _c_hist:
            plotting.plot_interactive_mc_multiple_histograms(_mc_results, mfa_results)
        _mc_hist = _c_hist.as_html()
    except Exception as _e:
        _mc_hist = mo.callout(mo.md(f"Histogram failed: {_e}"), kind="warn")

    try:
        with mo.capture() as _c_torn:
            plotting.plot_interactive_tornado(_mc_results)
        _mc_tornado = _c_torn.as_html()
    except Exception as _e:
        _mc_tornado = mo.callout(mo.md(f"Tornado failed: {_e}"), kind="warn")

    try:
        with mo.capture() as _c_paths:
            plotting.plot_interactive_mc_paths(_mc_results, mfa_results)
        _mc_paths = _c_paths.as_html()
    except Exception as _e:
        _mc_paths = mo.callout(mo.md(f"Paths failed: {_e}"), kind="warn")

    try:
        with mo.capture() as _c_comp:
            plotting.plot_interactive_mc_stock_comparison(_mc_results, mfa_results)
        _mc_compare = _c_comp.as_html()
    except Exception as _e:
        _mc_compare = mo.callout(mo.md(f"Comparison failed: {_e}"), kind="warn")
    return


if __name__ == "__main__":
    app.run()
