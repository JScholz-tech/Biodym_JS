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


# --------------------------------------------------------------------------
# Reproducibility — seeded MC runs must be deterministic
# --------------------------------------------------------------------------

def _run_t11(seed):
    yaml_path = os.path.join(CASE_STUDIES_DIR, "T11_Monte_Carlo", "config.yaml")
    parts = build_case_study_yaml(yaml_path)
    parts["config_obj"].MC_ITERATIONS = 3
    parts["config_obj"].MC_SEED = seed
    return run_mc_simulation(
        parts["mfa_system"],
        parts["all_excel_data"],
        parts["dsm_params"],
        parts["fomp_params"],
        parts["config_obj"],
        parts["process_logic_map"],
        parts["flow_tc_map"],
    )


def test_same_seed_reproduces_identical_results():
    a = _run_t11(seed=123)
    b = _run_t11(seed=123)
    numeric_cols = [
        c for c in a.columns if a[c].dtype.kind in "if" and c != "iteration"
    ]
    assert numeric_cols
    pd.testing.assert_frame_equal(a[numeric_cols], b[numeric_cols])
    assert a.attrs["mc_summary"]["seed"] == 123


def test_different_seeds_differ():
    a = _run_t11(seed=123)
    b = _run_t11(seed=456)
    sampled_cols = [c for c in a.columns if c.endswith("_sample")]
    varying_cols = sampled_cols or [
        c for c in a.columns if c.startswith("mb_input_")
    ]
    assert not a[varying_cols].equals(b[varying_cols])


def test_sample_parameters_accepts_seeded_generator():
    import numpy as np

    from utils import sample_parameters

    params = {
        "p_norm": {"distribution": "normal", "mean": 10, "std": 2},
        "p_trunc": {"distribution": "normal", "mean": 10, "std": 2, "min": 9},
        "p_uni": {"distribution": "uniform", "min": 0, "max": 1},
        "p_tri": {"distribution": "triangular", "min": 0, "max": 2, "mode": 1},
        "p_logn": {"distribution": "lognormal", "mean": 0, "std": 0.5},
    }
    a = sample_parameters(params, rng=np.random.default_rng(7))
    b = sample_parameters(params, rng=np.random.default_rng(7))
    assert a == b
    assert a["p_trunc"] >= 9


# --------------------------------------------------------------------------
# Physical bounds — sampled lifetimes / decay constants cannot be negative
# --------------------------------------------------------------------------

def test_enforce_physical_bounds_resamples_negative_lifetime():
    import numpy as np

    from engine.mc_simulation import _enforce_physical_bounds

    rng = np.random.default_rng(0)
    # Mean 5, std 2: negative draws are possible but resampling finds
    # positive ones easily
    defn = {"P08_DSM_Lifetime_Mean_Cat_1": {
        "distribution": "normal", "mean": 5, "std": 2,
    }}
    sampled = {"P08_DSM_Lifetime_Mean_Cat_1": -3.0}
    _enforce_physical_bounds(sampled, defn, rng=rng)
    assert sampled["P08_DSM_Lifetime_Mean_Cat_1"] > 0


def test_enforce_physical_bounds_clamps_hopeless_distribution():
    import numpy as np

    from engine.mc_simulation import _enforce_physical_bounds

    rng = np.random.default_rng(0)
    # Distribution entirely below zero — resampling cannot succeed
    defn = {"P08_decay_k1 (Labile pool)": {
        "distribution": "uniform", "min": -10, "max": -5,
    }}
    sampled = {"P08_decay_k1 (Labile pool)": -7.0}
    _enforce_physical_bounds(sampled, defn, rng=rng, max_retries=10)
    assert sampled["P08_decay_k1 (Labile pool)"] == 1e-9


def test_enforce_physical_bounds_leaves_other_params_alone():
    from engine.mc_simulation import _enforce_physical_bounds

    sampled = {"TC_05_06": -0.3, "F_00_01": -1.0}
    _enforce_physical_bounds(sampled, {})
    assert sampled == {"TC_05_06": -0.3, "F_00_01": -1.0}


# --------------------------------------------------------------------------
# Module params (LFG / BOM / FlowCap) must stay active during MC iterations
# --------------------------------------------------------------------------

def _t09_parts_with_mc_param():
    """T09_FlowCap with one injected flow uncertainty (the tutorial has none)."""
    yaml_path = os.path.join(CASE_STUDIES_DIR, "T09_FlowCap", "config.yaml")
    parts = build_case_study_yaml(yaml_path)
    parts["config_obj"].MC_ITERATIONS = 2
    parts["all_excel_data"]["4_1_Uncertainty_Parameters"] = pd.DataFrame(
        [{
            "MC_Parameter_ID": "F_00_01",
            "MC_Parameter_Selection": "x",
            "Distribution_Type": "normal",
            "Mean": 1.0,
            "StdDev": 0.05,
            "Min": 0.8,
            "Max": 1.2,
            "Mode": None,
            "MC_Operation": "multiply",
        }]
    )
    return parts


def test_mc_keeps_flowcap_process_active():
    # Without flow_cap_params the FlowCap process gets no logic applied at
    # all during MC iterations (outflows stay 0), which shows up as a large
    # per-process mass balance error.
    parts = _t09_parts_with_mc_param()

    results = run_mc_simulation(
        parts["mfa_system"],
        parts["all_excel_data"],
        parts["dsm_params"],
        parts["fomp_params"],
        parts["config_obj"],
        parts["process_logic_map"],
        parts["flow_tc_map"],
        lfg_params=parts["lfg_params"],
        bom_params=parts["bom_params"],
        flow_cap_params=parts["flow_cap_params"],
    )

    assert len(results) == 2
    assert (results["mb_error_material"] < 1e-6).all()


def test_mc_forwards_module_params_to_solver(monkeypatch):
    from engine import mc_simulation

    parts = _t09_parts_with_mc_param()
    captured = {}
    original = mc_simulation.solver.run_mfa_calculation

    def spy(*args, **kwargs):
        captured.update(kwargs)
        return original(*args, **kwargs)

    monkeypatch.setattr(mc_simulation.solver, "run_mfa_calculation", spy)

    run_mc_simulation(
        parts["mfa_system"],
        parts["all_excel_data"],
        parts["dsm_params"],
        parts["fomp_params"],
        parts["config_obj"],
        parts["process_logic_map"],
        parts["flow_tc_map"],
        lfg_params=parts["lfg_params"],
        bom_params=parts["bom_params"],
        flow_cap_params=parts["flow_cap_params"],
    )

    assert captured["lfg_params"] == parts["lfg_params"]
    assert captured["bom_params"] == parts["bom_params"]
    assert captured["flow_cap_params"] == parts["flow_cap_params"]


# --------------------------------------------------------------------------
# Process-ID validation in the solver
# --------------------------------------------------------------------------

def test_unknown_process_id_warns():
    import pytest

    yaml_path = os.path.join(CASE_STUDIES_DIR, "T01_First_MFA", "config.yaml")
    parts = build_case_study_yaml(yaml_path)
    from engine import solver

    with pytest.warns(UserWarning, match=r"dsm_params\[999\]"):
        solver.run_mfa_calculation(
            parts["mfa_system"],
            {999: {"lifetimes": {}}},  # typo'd process ID
            parts["fomp_params"],
            parts["config_obj"],
            flow_tc_map=parts["flow_tc_map"],
            process_logic_map=parts["process_logic_map"],
        )


def test_unknown_process_id_raises_under_strict():
    import pytest

    yaml_path = os.path.join(CASE_STUDIES_DIR, "T01_First_MFA", "config.yaml")
    parts = build_case_study_yaml(yaml_path)
    parts["config_obj"].SOLVER_STRICT = True
    from engine import solver

    with pytest.raises(ValueError, match="unknown process IDs"):
        solver.run_mfa_calculation(
            parts["mfa_system"],
            {999: {"lifetimes": {}}},
            parts["fomp_params"],
            parts["config_obj"],
            flow_tc_map=parts["flow_tc_map"],
            process_logic_map=parts["process_logic_map"],
        )


def test_non_dict_params_raise_type_error():
    import pytest

    yaml_path = os.path.join(CASE_STUDIES_DIR, "T01_First_MFA", "config.yaml")
    parts = build_case_study_yaml(yaml_path)
    from engine import solver

    with pytest.raises(TypeError, match="dsm_params must be a dict"):
        solver.run_mfa_calculation(
            parts["mfa_system"],
            [1, 2, 3],  # wrong type
            parts["fomp_params"],
            parts["config_obj"],
            flow_tc_map=parts["flow_tc_map"],
            process_logic_map=parts["process_logic_map"],
        )
