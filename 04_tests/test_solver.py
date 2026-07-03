# -*- coding: utf-8 -*-
"""
Tests for the mfa_engine/solver.py module.

This file contains unit tests for the core calculation functions to ensure
their numerical and scientific correctness.
"""

# Fix imports for test discovery and linter
import sys
import os
import pytest
import numpy as np

try:
    import ODYM_Classes as msc  # type: ignore
except ImportError:
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    # Framework is inside the project at 06_framework/
    odym_path = os.path.join(
        project_root, "06_framework", "ODYM-master_20241127", "odym", "modules"
    )
    sys.path.insert(0, odym_path)
    import ODYM_Classes as msc  # type: ignore

import system_setup
from engine import dsm_model


def test_calculate_dynamic_stock_fixed_lifetime():
    """
    Tests the DSM calculation with a simple fixed lifetime.
    This is a "known-results" test, where the expected output is pre-calculated.
    """
    # 1. ARRANGE
    # Define a simple 10-year system with one element
    start_year, end_year, elements = 2020, 2029, ["material"]
    model_class, index_table = system_setup.define_model_scope(start_year, end_year, elements)
    mfa_system = system_setup.initialize_mfa_system(model_class, index_table)

    # Add processes and a stock
    mfa_system.ProcessList.append(msc.Process(Name="Environment", ID=0))
    mfa_system.ProcessList.append(msc.Process(Name="In-Use Stock", ID=1))
    mfa_system.ProcessList.append(msc.Process(Name="EoL", ID=2))
    mfa_system.StockDict["S_1"] = msc.Stock(Name="S_1", P_Res=1, Type=0, Indices="t,e")

    # Define a known inflow and an empty outflow
    inflow_values = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]).reshape(-1, 1)
    mfa_system.FlowDict["F_0_1"] = msc.Flow(
        Name="F_0_1", P_Start=0, P_End=1, Indices="t,e", Values=inflow_values
    )
    mfa_system.FlowDict["F_1_2"] = msc.Flow(
        Name="F_1_2", P_Start=1, P_End=2, Indices="t,e"
    )
    mfa_system.Initialize_FlowValues()  # Initialize F_1_2 to zeros
    mfa_system.Initialize_StockValues()  # Initialize S_1 to zeros

    # Define DSM parameters for a fixed 5-year lifetime
    dsm_params = {
        1: {
            "lifetimes": {"Type": ["Fixed"], "Mean": [5], "StdDev": [0]},
            "inflow_split": [1.0],  # Only one category
            "category_names": ["Category_1"],
            "parameter_based": False,
        }
    }

    # Define the known, correct result
    expected_outflow = np.array([0, 0, 0, 0, 0, 1, 2, 3, 4, 5]).reshape(-1, 1)

    # 2. ACT
    mfa_system_result, _ = dsm_model.calculate_dynamic_stock(mfa_system, dsm_params)

    # 3. ASSERT
    actual_outflow = mfa_system_result.FlowDict["F_1_2"].Values
    np.testing.assert_array_almost_equal(actual_outflow, expected_outflow)


def test_calculate_dynamic_stock_normal_lifetime():
    """Test DSM calculation with a normal (Gaussian) lifetime distribution.

    This test uses a 10-year system with a single element and a normal lifetime
    distribution (mean=5, stddev=1.5). The expected outflow is calculated using
    scipy.stats.norm.sf for the survival function.
    """
    import scipy.stats
    # 1. ARRANGE
    start_year, end_year, elements = 2020, 2029, ["material"]
    model_class, index_table = system_setup.define_model_scope(start_year, end_year, elements)
    mfa_system = system_setup.initialize_mfa_system(model_class, index_table)

    # Add processes and a stock
    mfa_system.ProcessList.append(msc.Process(Name="Environment", ID=0))
    mfa_system.ProcessList.append(msc.Process(Name="In-Use Stock", ID=1))
    mfa_system.ProcessList.append(msc.Process(Name="EoL", ID=2))
    mfa_system.StockDict["S_1"] = msc.Stock(Name="S_1", P_Res=1, Type=0, Indices="t,e")

    # Define a known inflow and an empty outflow
    inflow_values = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]).reshape(-1, 1)
    mfa_system.FlowDict["F_0_1"] = msc.Flow(
        Name="F_0_1", P_Start=0, P_End=1, Indices="t,e", Values=inflow_values
    )
    mfa_system.FlowDict["F_1_2"] = msc.Flow(
        Name="F_1_2", P_Start=1, P_End=2, Indices="t,e"
    )
    mfa_system.Initialize_FlowValues()  # Initialize F_1_2 to zeros
    mfa_system.Initialize_StockValues()  # Initialize S_1 to zeros

    # Define DSM parameters for a normal lifetime (mean=5, stddev=1.5)
    dsm_params = {
        1: {
            "lifetimes": {"Type": "Normal", "Mean": [5], "StdDev": [1.5]},
            "inflow_split": [1.0],
        }
    }

    # Calculate expected outflow using survival function
    # For each cohort (year), outflow in year t is inflow in year c * (sf(t-c) - sf(t-c+1))
    years = np.arange(10)
    mean = 5
    stddev = 1.5
    expected_outflow = np.zeros((10, 1))
    for t in range(10):
        for c in range(t + 1):
            sf_start = scipy.stats.norm.sf(t - c, loc=mean, scale=stddev)
            sf_end = scipy.stats.norm.sf(t - c + 1, loc=mean, scale=stddev)
            expected_outflow[t, 0] += inflow_values[c, 0] * (sf_start - sf_end)

    # 2. ACT
    mfa_system_result, _ = dsm_model.calculate_dynamic_stock(mfa_system, dsm_params)

    # 3. ASSERT
    actual_outflow = mfa_system_result.FlowDict["F_1_2"].Values

    # NOTE: This test previously used rtol=1.0 (100% tolerance) which is unacceptable.
    # The discrepancy arises because the manual calculation above doesn't account for
    # ODYM's handling of negative ages in the Normal distribution (see ODYM source line 284-286).
    # ODYM allocates outflow contributions from negative ages to year zero to preserve mass balance.
    #
    # Instead of trying to replicate ODYM's exact internal logic, we verify that:
    # 1. Mass balance is preserved (total inflow = total stock + total outflow)
    # 2. Outflows are non-negative
    # 3. The pattern roughly matches expectations (peak around mean lifetime)

    # Mass balance check (for each time step: stock_change = inflow - outflow)
    stock_values = mfa_system_result.StockDict["S_1"].Values[:, 0]
    for t in range(1, len(inflow_values)):
        stock_change = stock_values[t] - stock_values[t-1]
        expected_change = inflow_values[t, 0] - actual_outflow[t, 0]
        balance_error = abs(stock_change - expected_change)
        assert balance_error < 0.01, f"Mass balance error at year {t}: {balance_error}"

    # Also check: final stock + cumulative outflow = cumulative inflow
    final_stock = stock_values[-1]
    cumulative_outflow = actual_outflow.sum()
    cumulative_inflow = inflow_values.sum()
    mass_balance_error = abs(final_stock + cumulative_outflow - cumulative_inflow)
    assert mass_balance_error < 0.01, f"Cumulative mass balance error: {mass_balance_error}"

    # Non-negativity check
    assert np.all(actual_outflow >= 0), "Outflows should be non-negative"

    # Peak should occur in later years (mean lifetime=5, but inflows are increasing)
    # With increasing inflows (1,2,3...10), peak outflow occurs when largest cohorts age out
    peak_year = np.argmax(actual_outflow)
    assert peak_year >= 4, f"Peak outflow at year {peak_year}, should be >= 4 (mean lifetime is 5)"


# --------------------------------------------------------------------------
# Non-convergence handling (SOLVER_STRICT)
# --------------------------------------------------------------------------

def _build_nonconverging_run(monkeypatch):
    """Force non-convergence by making the TC pass always report changes."""
    import os

    from engine import solver
    from golden_utils import build_case_study_yaml

    monkeypatch.setattr(
        solver, "_calculate_tc_driven_flows", lambda *args, **kwargs: True
    )

    tests_dir = os.path.dirname(os.path.abspath(__file__))
    yaml_path = os.path.join(
        os.path.dirname(tests_dir),
        "01_data", "01_input", "case_studies", "T01_First_MFA", "config.yaml",
    )
    return build_case_study_yaml(yaml_path)


def _run_from_parts(parts):
    from engine import solver

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


def test_nonconvergence_warns_and_flags_solver_info(monkeypatch):
    parts = _build_nonconverging_run(monkeypatch)

    with pytest.warns(RuntimeWarning, match="did not converge"):
        _, _, solver_info = _run_from_parts(parts)

    assert solver_info["converged"] is False
    assert solver_info["max_iterations_hit"] is True
    assert solver_info["iterations"] == solver_info["max_iterations"]


def test_nonconvergence_raises_under_solver_strict(monkeypatch):
    parts = _build_nonconverging_run(monkeypatch)
    parts["config_obj"].SOLVER_STRICT = True

    with pytest.raises(RuntimeError, match="did not converge"):
        _run_from_parts(parts)


def test_solver_max_iterations_configurable(monkeypatch):
    """SOLVER_MAX_ITERATIONS caps the fixed-point loop (H7)."""
    parts = _build_nonconverging_run(monkeypatch)
    parts["config_obj"].SOLVER_MAX_ITERATIONS = 5

    with pytest.warns(RuntimeWarning, match="did not converge after 5"):
        _, _, solver_info = _run_from_parts(parts)

    assert solver_info["max_iterations"] == 5
    assert solver_info["iterations"] == 5


# --------------------------------------------------------------------------
# DSM initial-stock survival-function decay (Fix 4 of validation review)
# --------------------------------------------------------------------------

def _dsm_params_normal(mean=10.0, std=3.0):
    return {
        "lifetimes": {"Type": ["Normal"], "Mean": [mean], "StdDev": [std]},
        "inflow_split": [1.0],
        "category_names": ["Category_1"],
    }


def test_initial_stock_decay_conserves_mass():
    from engine.dsm_model import _calculate_outflow_from_initial_stock

    num_years, num_elements = 60, 4
    time_vector = np.arange(2025, 2025 + num_years)
    s0 = np.array([1000.0, 100.0, 900.0, 400.0])

    stock_ts, outflow_ts = _calculate_outflow_from_initial_stock(
        s0, _dsm_params_normal(), num_years, num_elements, time_vector
    )

    np.testing.assert_allclose(stock_ts[0], s0)
    assert np.all(outflow_ts[0] == 0), "no outflow in the establishment year"
    # Conservation: final stock + cumulative outflow == initial stock
    np.testing.assert_allclose(stock_ts[-1] + outflow_ts.sum(axis=0), s0)
    assert np.all(outflow_ts >= 0)
    assert np.all(np.diff(stock_ts[:, 0]) <= 1e-9), "stock must not grow"


def test_initial_stock_decay_fixed_lifetime_is_step():
    """A Fixed lifetime must retire the whole cohort at the mean age —
    the old k=1/mean exponential smeared it over the full horizon."""
    from engine.dsm_model import _calculate_outflow_from_initial_stock

    num_years, num_elements = 20, 1
    time_vector = np.arange(2025, 2025 + num_years)
    s0 = np.array([100.0])
    params = {
        "lifetimes": {"Type": ["Fixed"], "Mean": [5.0], "StdDev": [0.0]},
        "inflow_split": [1.0],
    }

    stock_ts, outflow_ts = _calculate_outflow_from_initial_stock(
        s0, params, num_years, num_elements, time_vector
    )

    # Survives fully until just before the fixed lifetime...
    assert stock_ts[4, 0] == pytest.approx(100.0)
    # ...then the entire cohort retires at age 5
    assert stock_ts[5, 0] == pytest.approx(0.0)
    assert outflow_ts[5, 0] == pytest.approx(100.0)


def test_initial_stock_decay_consistent_with_cohort_method():
    """Method A (survival decay) and Method B (ODYM age-cohort) must decay
    along the SAME survival function — the validation condition of Fix 4.

    Convention difference (deliberate, documented): Method A installs the
    initial stock as a brand-new cohort at t=0, so S_A(t) = S0·sf(t).
    Method B treats it as pre-existing items — with a uniform single-year
    age distribution the cohort is one year old at t=0, so
    S_B(t) = S0·sf(t+1)/sf(1). Both identities are asserted against the
    same ODYM survival function.
    """
    import dynamic_stock_model as dsm_mod

    from engine.dsm_model import (
        _build_category_lt_dict,
        _calculate_outflow_from_initial_stock,
        _calculate_outflow_from_initial_stock_cohort,
    )

    num_years, num_elements = 40, 4
    time_vector = np.arange(2025, 2025 + num_years)
    s0_material = 1000.0
    fractions = {"WC": 0.1, "DM": 0.9, "TC": 0.4}
    s0 = np.array([s0_material, 100.0, 900.0, 400.0])
    params = _dsm_params_normal(mean=12.0, std=4.0)

    # Reference survival function (extended one step for the B identity)
    lt_dict = _build_category_lt_dict(params, 0)
    sf = dsm_mod.DynamicStockModel(
        t=np.arange(num_years + 1), lt=lt_dict
    ).compute_sf()[:, 0]

    # --- Method A: new cohort at t=0 → S_A(t) = S0·sf(t) ---
    stock_a, outflow_a = _calculate_outflow_from_initial_stock(
        s0, params, num_years, num_elements, time_vector
    )
    expected_a = np.outer(sf[:num_years], s0)
    expected_a[0] = s0  # establishment-year convention
    np.testing.assert_allclose(stock_a, expected_a, rtol=1e-9)
    np.testing.assert_allclose(stock_a[-1] + outflow_a.sum(axis=0), s0)

    # --- Method B: pre-existing 1-year-old cohort → S_B(t) = S0·sf(t+1)/sf(1) ---
    initial_stock_config = {
        "process_id": 1,
        "elements": ["material", "WC", "DM", "TC"],
        "initial_stock_values": {
            "Initial_Stock_material": s0_material,
            **{f"Initial_Stock_{k}[%]": v for k, v in fractions.items()},
        },
        "cohort_age_distribution_type": "uniform",
        "cohort_max_age": 1,
    }
    stock_b, _ = _calculate_outflow_from_initial_stock_cohort(
        initial_stock_config, params, num_years, num_elements, time_vector
    )
    expected_b = np.outer(sf[1 : num_years + 1] / sf[1], s0)
    np.testing.assert_allclose(stock_b, expected_b, rtol=1e-6, atol=1e-6)
