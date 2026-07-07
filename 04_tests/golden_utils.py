# -*- coding: utf-8 -*-
"""
Shared pipeline helper for the golden regression tests.

Runs the full deterministic BioDYM pipeline (mirroring section 2.1 of
00_BioDYM_Workflow.py) from a SystemDefiner YAML config in YAML-only mode.
Both the golden reference generator (04_tests/golden/generate_references.py)
and the regression test (04_tests/test_golden_regression.py) use this exact
code path, so references and assertions can never drift apart.

Beyond the deterministic baseline solve, ``collect_full_results`` also runs
the scenario engine (if a tutorial has ``run_scenario_analysis: true``) and
the Monte Carlo engine (if it has ``run_monte_carlo: true``), so tutorials
like T08_Scenarios / T11_Monte_Carlo / T12_Monte_Carlo_Process actually pin
the numerics of the feature they are named after, not just the underlying
baseline MFA solve.
"""

import hashlib

import config
import data_loader
import system_setup
from engine import mc_simulation, scenario_engine, solver


def build_case_study_yaml(yaml_path):
    """Build a fully configured but unsolved MFA system from a YAML case study.

    Parameters
    ----------
    yaml_path : str
        Path to a SystemDefiner ``config.yaml`` (YAML-only mode — all model
        data is synthesized from the YAML, no Excel file involved).

    Returns
    -------
    dict
        Everything needed to call the solver (or the MC simulation):
        ``mfa_system``, ``config_obj``, ``all_excel_data``, ``flow_tc_map``,
        ``process_logic_map``, ``dsm_params``, ``fomp_params``, ``lfg_params``,
        ``bom_params``, ``flow_cap_params``.
    """
    yaml_path = str(yaml_path)

    # 1.3 — configuration extraction (YAML-only mode)
    input_data = data_loader.yaml_to_excel_dataframes(yaml_path)
    config_obj = config.load_config_from_yaml(yaml_path)

    dims = config.extract_workflow_dimensions(config_obj, input_data)

    # 2.1.1 — model scope
    model_classification, index_table = system_setup.define_model_scope(
        dims["start_year"],
        dims["end_year"],
        dims["elements"],
        dims["regions"],
        dims["goods"],
        dims["materials"],
        dims["processes"],
    )

    # 2.1.2 — MFA system
    mfa_system = system_setup.initialize_mfa_system(
        model_classification, index_table, unit=config.resolve_unit(config_obj)
    )

    # 2.1.3 — processes and data
    mfa_system, all_excel_data = system_setup.load_and_define_processes(
        mfa_system, input_data, data_loader
    )

    # 2.1.4 — flows and parameters
    mfa_system, _, flow_tc_map, process_logic_map = (
        system_setup.define_flows_and_parameters(mfa_system, all_excel_data)
    )

    # 2.1.5 — TC / DSM / FOMP / LFG / FlowCap / BOM parameters
    time_vector = mfa_system.IndexTable.Classification["Time"].Items
    tc_params = data_loader.load_tc_parameters(
        all_excel_data, mfa_system.Elements, time_vector
    )
    mfa_system.ParameterDict.update(tc_params)

    params = data_loader.load_all_parameters(
        all_excel_data,
        config_obj,
        yaml_config_file=yaml_path,
        elements=mfa_system.Elements,
    )
    dsm_params = params["dsm"]
    fomp_params = params["fomp"]
    lfg_params = params["lfg"]
    flow_cap_params = params["flow_cap"]
    bom_params = params["bom"]
    data_loader.register_flow_cap_parameters(mfa_system, flow_cap_params)

    # Process_Logic column is the authoritative enable/disable switch for
    # FOMP/LFG (DSM is already filtered at load time).
    if process_logic_map:
        fomp_params = {
            pid: p
            for pid, p in fomp_params.items()
            if process_logic_map.get(pid) == "FOMP"
        }
        lfg_params = {
            pid: p
            for pid, p in lfg_params.items()
            if process_logic_map.get(pid) == "LFG"
        }

    return {
        "mfa_system": mfa_system,
        "config_obj": config_obj,
        "all_excel_data": all_excel_data,
        "flow_tc_map": flow_tc_map,
        "process_logic_map": process_logic_map,
        "dsm_params": dsm_params,
        "fomp_params": fomp_params,
        "lfg_params": lfg_params,
        "bom_params": bom_params,
        "flow_cap_params": flow_cap_params,
    }


def run_case_study_yaml(yaml_path):
    """Run the full deterministic pipeline for a YAML case study.

    Returns
    -------
    tuple
        ``(mfa_system, dsm_details, solver_info)`` as returned by
        ``solver.run_mfa_calculation``.
    """
    parts = build_case_study_yaml(yaml_path)

    # 2.1.6 — baseline calculation
    return solver.run_mfa_calculation(
        parts["mfa_system"],
        parts["dsm_params"],
        parts["fomp_params"],
        parts["config_obj"],
        flow_tc_map=parts["flow_tc_map"],
        process_logic_map=parts["process_logic_map"],
        lfg_params=parts["lfg_params"],
        bom_params=parts["bom_params"],
        flow_cap_params=parts["flow_cap_params"],
    )


def collect_result_arrays(mfa_system):
    """Flatten a solved MFA system into {key: ndarray} for golden comparison.

    Keys are ``flow/<FlowID>`` and ``stock/<StockID>`` so a single .npz file
    holds the complete numerical result of a run.
    """
    arrays = {}
    for flow_id, flow in mfa_system.FlowDict.items():
        if flow.Values is not None:
            arrays[f"flow/{flow_id}"] = flow.Values
    for stock_id, stock in mfa_system.StockDict.items():
        if stock.Values is not None:
            arrays[f"stock/{stock_id}"] = stock.Values
    return arrays


def collect_scenario_result_arrays(all_scenario_results):
    """Flatten scenario-engine results into {key: ndarray}.

    Keys are ``scenario/<name>/flow/<FlowID>`` and
    ``scenario/<name>/stock/<StockID>``, one block per scenario.
    """
    arrays = {}
    for scenario_name, scenario_mfa_system in all_scenario_results.items():
        for key, value in collect_result_arrays(scenario_mfa_system).items():
            arrays[f"scenario/{scenario_name}/{key}"] = value
    return arrays


#: mc_simulation results carry per-iteration timeseries as Python lists
#: (variable-length, not natural ndarrays) — dropped from the golden pin.
#: The scalar per-iteration columns (sampled parameters, final stock values,
#: mass-balance error metrics) are what actually catch a numeric regression.
_MC_TIMESERIES_SUFFIX = "_timeseries"


def collect_mc_result_arrays(mc_results_df):
    """Flatten Monte Carlo batch results into {key: ndarray}.

    Keys are ``mc/<column>``, one per scalar per-iteration column. Returns
    an empty dict if MC produced no results (e.g. no uncertainty parameters
    defined).
    """
    if mc_results_df is None or mc_results_df.empty:
        return {}
    arrays = {}
    for column in mc_results_df.columns:
        if column.endswith(_MC_TIMESERIES_SUFFIX):
            continue
        arrays[f"mc/{column}"] = mc_results_df[column].to_numpy()
    return arrays


def config_file_hash(yaml_path):
    """SHA-256 hex digest of a case study's config.yaml contents.

    Pinned alongside each golden reference so a fixture edit that isn't
    followed by regenerating the reference fails loudly and immediately
    (rather than surfacing later as a numeric mismatch on main — see the
    T04 FoldedNormal staleness incident, af2b5f9 / c15c547).
    """
    with open(yaml_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def collect_full_results(yaml_path):
    """Run the complete pipeline for a tutorial and collect all pinned arrays.

    Runs the deterministic baseline solve, then — only if the tutorial's
    config enables them — the scenario engine and the Monte Carlo engine, so
    the golden reference actually exercises the feature each tutorial is
    named after.

    Returns
    -------
    tuple
        ``(arrays, solver_info)`` where ``arrays`` is the merged
        ``{key: ndarray}`` dict (baseline + scenario + MC) and
        ``solver_info`` is the baseline solve's convergence info.
    """
    parts = build_case_study_yaml(yaml_path)
    config_obj = parts["config_obj"]

    mfa_system, _, solver_info = solver.run_mfa_calculation(
        parts["mfa_system"],
        parts["dsm_params"],
        parts["fomp_params"],
        config_obj,
        flow_tc_map=parts["flow_tc_map"],
        process_logic_map=parts["process_logic_map"],
        lfg_params=parts["lfg_params"],
        bom_params=parts["bom_params"],
        flow_cap_params=parts["flow_cap_params"],
    )

    arrays = collect_result_arrays(mfa_system)

    if getattr(config_obj, "Run_Scenario_Analysis", False):
        all_scenario_results, _ = scenario_engine.run_scenario_analysis(
            config_obj,
            parts["mfa_system"],
            parts["all_excel_data"],
            parts["dsm_params"],
            parts["fomp_params"],
            parts["flow_tc_map"],
            parts["process_logic_map"],
            lfg_params=parts["lfg_params"],
            bom_params=parts["bom_params"],
            flow_cap_params=parts["flow_cap_params"],
        )
        arrays.update(collect_scenario_result_arrays(all_scenario_results))

    if getattr(config_obj, "RUN_MONTE_CARLO", False):
        mc_results_df = mc_simulation.run_mc_simulation(
            parts["mfa_system"],
            parts["all_excel_data"],
            parts["dsm_params"],
            parts["fomp_params"],
            config_obj,
            parts["process_logic_map"],
            parts["flow_tc_map"],
            lfg_params=parts["lfg_params"],
            bom_params=parts["bom_params"],
            flow_cap_params=parts["flow_cap_params"],
        )
        arrays.update(collect_mc_result_arrays(mc_results_df))

    return arrays, solver_info
