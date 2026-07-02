# -*- coding: utf-8 -*-
"""
Shared pipeline helper for the golden regression tests.

Runs the full deterministic BioDYM pipeline (mirroring section 2.1 of
00_BioDYM_Workflow.py) from a SystemDefiner YAML config in YAML-only mode.
Both the golden reference generator (04_tests/golden/generate_references.py)
and the regression test (04_tests/test_golden_regression.py) use this exact
code path, so references and assertions can never drift apart.
"""

import config
import data_loader
import system_setup
from engine import solver


def run_case_study_yaml(yaml_path):
    """Run the full deterministic pipeline for a YAML case study.

    Parameters
    ----------
    yaml_path : str
        Path to a SystemDefiner ``config.yaml`` (YAML-only mode — all model
        data is synthesized from the YAML, no Excel file involved).

    Returns
    -------
    tuple
        ``(mfa_system, dsm_details, solver_info)`` as returned by
        ``solver.run_mfa_calculation``.
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

    # 2.1.6 — baseline calculation
    return solver.run_mfa_calculation(
        mfa_system,
        dsm_params,
        fomp_params,
        config_obj,
        flow_tc_map=flow_tc_map,
        process_logic_map=process_logic_map,
        lfg_params=lfg_params,
        bom_params=bom_params,
        flow_cap_params=flow_cap_params,
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
