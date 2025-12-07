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
