# -*- coding: utf-8 -*-
"""Unit tests for 02_src/engine/mc_simulation.py (Monte Carlo machinery)."""

import os
from types import SimpleNamespace

import pandas as pd
import pytest

from engine.mc_simulation import (
    _group_tc_params,
    _parse_tc_group_key,
    apply_dsm_parameter_updates,
    apply_fomp_parameter_updates,
    normalize_tc_updates,
    run_mc_simulation,
)
from golden_utils import build_case_study_yaml

_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_TESTS_DIR)
CASE_STUDIES_DIR = os.path.join(
    _PROJECT_ROOT, "01_data", "01_input", "case_studies"
)


# --------------------------------------------------------------------------
# TC parameter name parsing / grouping
# --------------------------------------------------------------------------

def test_parse_tc_group_key_standard_name():
    assert _parse_tc_group_key("TC_05_06") == (None, 5)


def test_parse_tc_group_key_element_specific_name():
    assert _parse_tc_group_key("TC_E2_11_00") == ("E2", 11)


def test_parse_tc_group_key_garbage_returns_none():
    assert _parse_tc_group_key("TC_") is None
    assert _parse_tc_group_key("TC_ABC_DEF") is None


def test_group_tc_params_by_process():
    params = {
        "TC_05_06": {"distribution": "normal"},
        "TC_05_07": {"distribution": "normal"},
        "TC_E2_11_00": {"distribution": "uniform"},
        "F_00_01": {"distribution": "normal"},  # not a TC — ignored
    }
    groups = _group_tc_params(params)
    assert set(groups) == {(None, 5), ("E2", 11)}
    assert set(groups[(None, 5)]) == {"TC_05_06", "TC_05_07"}


# --------------------------------------------------------------------------
# DSM / FOMP parameter updates
# --------------------------------------------------------------------------

def _dsm_params():
    return {
        8: {
            "lifetimes": {"Mean": [20.0, 30.0], "StdDev": [5.0, 8.0]},
            "inflow_split": [0.5, 0.5],
            "output_splits": [[0.7, 0.3], [0.6, 0.4]],
        }
    }


def test_apply_dsm_updates_sets_lifetime_mean():
    updated = apply_dsm_parameter_updates(
        _dsm_params(), {"P08_DSM_Lifetime_Mean_Cat_1": 42.0}
    )
    assert updated[8]["lifetimes"]["Mean"] == [42.0, 30.0]
    # Original must not be mutated
    assert _dsm_params()[8]["lifetimes"]["Mean"] == [20.0, 30.0]


def test_apply_dsm_updates_renormalizes_inflow_split():
    updated = apply_dsm_parameter_updates(
        _dsm_params(), {"P08_DSM_Inflow_Split_Cat_1": 3.0}
    )
    splits = updated[8]["inflow_split"]
    assert sum(splits) == pytest.approx(1.0)
    assert splits[0] == pytest.approx(3.0 / 3.5)


def test_apply_dsm_updates_unknown_process_is_noop():
    original = _dsm_params()
    updated = apply_dsm_parameter_updates(
        original, {"P99_DSM_Lifetime_Mean_Cat_1": 42.0}
    )
    assert updated == original


def test_apply_fomp_updates_sets_decay_constant():
    fomp_params = {8: {"decay_k1 (Labile pool)": 0.5, "f_labile": 0.7}}
    updated = apply_fomp_parameter_updates(
        fomp_params, {"P08_decay_k1 (Labile pool)": 0.9}
    )
    assert updated[8]["decay_k1 (Labile pool)"] == 0.9
    assert fomp_params[8]["decay_k1 (Labile pool)"] == 0.5  # copy, not mutation


def test_apply_fomp_updates_ignores_non_fomp_params():
    fomp_params = {8: {"decay_k1 (Labile pool)": 0.5}}
    updated = apply_fomp_parameter_updates(
        fomp_params, {"TC_05_06": 0.3, "P08_DSM_Lifetime_Mean_Cat_1": 42.0}
    )
    assert updated == fomp_params


# --------------------------------------------------------------------------
# normalize_tc_updates
# --------------------------------------------------------------------------

def _fake_system_with_outflows(process_id, n_outgoing):
    flows = {
        f"F_{process_id:02d}_{i:02d}": SimpleNamespace(
            P_Start=process_id, P_End=i
        )
        for i in range(n_outgoing)
    }
    return SimpleNamespace(FlowDict=flows)


def test_normalize_tc_updates_proportional():
    system = _fake_system_with_outflows(5, n_outgoing=2)
    tc_updates = {"TC_05_06": 0.9, "TC_05_07": 0.3}
    normalize_tc_updates(tc_updates, system)
    assert tc_updates["TC_05_06"] == pytest.approx(0.75)
    assert tc_updates["TC_05_07"] == pytest.approx(0.25)
    assert sum(tc_updates.values()) == pytest.approx(1.0)


def test_normalize_tc_updates_single_tc_untouched():
    system = _fake_system_with_outflows(5, n_outgoing=2)
    tc_updates = {"TC_05_06": 0.9}
    normalize_tc_updates(tc_updates, system)
    assert tc_updates["TC_05_06"] == 0.9


def test_normalize_tc_updates_incomplete_group_skipped():
    # 3 outgoing flows but only 2 TCs sampled — normalization must not run
    system = _fake_system_with_outflows(5, n_outgoing=3)
    tc_updates = {"TC_05_06": 0.9, "TC_05_07": 0.3}
    normalize_tc_updates(tc_updates, system)
    assert tc_updates["TC_05_06"] == 0.9
    assert tc_updates["TC_05_07"] == 0.3


# --------------------------------------------------------------------------
# run_mc_simulation — end-to-end on the T11 Monte Carlo tutorial
# --------------------------------------------------------------------------

def test_run_mc_simulation_t11_smoke():
    yaml_path = os.path.join(CASE_STUDIES_DIR, "T11_Monte_Carlo", "config.yaml")
    parts = build_case_study_yaml(yaml_path)

    config_obj = parts["config_obj"]
    config_obj.MC_ITERATIONS = 5

    results = run_mc_simulation(
        parts["mfa_system"],
        parts["all_excel_data"],
        parts["dsm_params"],
        parts["fomp_params"],
        config_obj,
        parts["process_logic_map"],
        parts["flow_tc_map"],
    )

    assert isinstance(results, pd.DataFrame)
    assert len(results) == 5
    assert "iteration" in results.columns
    assert list(results["iteration"]) == [1, 2, 3, 4, 5]
    # Final-year stock outputs and mass-balance diagnostics are recorded
    assert "mass_balance_error_abs" in results.columns
    assert any(col.startswith("mb_error_") for col in results.columns)


# --------------------------------------------------------------------------
# Batch robustness — one failed sample must not kill the batch
# --------------------------------------------------------------------------

def test_run_mc_simulation_survives_failed_iteration(monkeypatch):
    from engine import mc_simulation

    yaml_path = os.path.join(CASE_STUDIES_DIR, "T11_Monte_Carlo", "config.yaml")
    parts = build_case_study_yaml(yaml_path)
    parts["config_obj"].MC_ITERATIONS = 4

    original = mc_simulation._run_single_mc_iteration

    def poisoned(iteration_num, *args, **kwargs):
        if iteration_num == 2:
            raise ValueError("poisoned sample")
        return original(iteration_num, *args, **kwargs)

    monkeypatch.setattr(mc_simulation, "_run_single_mc_iteration", poisoned)

    results = run_mc_simulation(
        parts["mfa_system"],
        parts["all_excel_data"],
        parts["dsm_params"],
        parts["fomp_params"],
        parts["config_obj"],
        parts["process_logic_map"],
        parts["flow_tc_map"],
    )

    assert len(results) == 3  # iteration 2 skipped, batch completed
    assert list(results["iteration"]) == [1, 3, 4]

    summary = results.attrs["mc_summary"]
    assert summary["n_failed"] == 1
    assert summary["n_success"] == 3
    assert summary["failed_runs"][0]["iteration"] == 2
    assert "poisoned sample" in summary["failed_runs"][0]["error"]


def test_mc_results_carry_converged_column():
    yaml_path = os.path.join(CASE_STUDIES_DIR, "T11_Monte_Carlo", "config.yaml")
    parts = build_case_study_yaml(yaml_path)
    parts["config_obj"].MC_ITERATIONS = 2

    results = run_mc_simulation(
        parts["mfa_system"],
        parts["all_excel_data"],
        parts["dsm_params"],
        parts["fomp_params"],
        parts["config_obj"],
        parts["process_logic_map"],
        parts["flow_tc_map"],
    )

    assert "converged" in results.columns
    assert results["converged"].all()
    assert results.attrs["mc_summary"]["n_nonconverged"] == 0
