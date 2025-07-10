# -*- coding: utf-8 -*-
"""
Tests for the engine/fomp_model.py module.

This file contains unit tests for the First-Order Model Process (FOMP)
calculation functions to ensure their numerical and scientific correctness.
"""

import sys
import os
import pytest
import numpy as np
import copy

# Add framework path to be able to import ODYM.
try:
    import ODYM_Classes as msc
except ImportError:
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    project_root_parent = os.path.dirname(project_root)
    odym_path = os.path.join(
        project_root_parent, "framework", "ODYM-master_20241127", "odym", "modules"
    )
    sys.path.insert(0, odym_path)
    import ODYM_Classes as msc

from system_setup import define_model_scope, initialize_mfa_system
from engine.fomp_model import calculate_fomp


def test_calculate_fomp_simple_decay():
    """
    Tests FOMP calculation with simple first-order decay (k1 only).
    This is a "known-results" test with a simple decay scenario.
    """
    # 1. ARRANGE
    # Define a simple 5-year system with one element
    start_year, end_year, elements = 2020, 2024, ["material"]
    model_class, index_table = define_model_scope(start_year, end_year, elements)
    mfa_system = initialize_mfa_system(model_class, index_table)

    # Add processes and stock
    mfa_system.ProcessList.append(msc.Process(Name="Environment", ID=0))
    mfa_system.ProcessList.append(msc.Process(Name="Decay Process", ID=1))
    mfa_system.ProcessList.append(msc.Process(Name="Output", ID=2))
    mfa_system.StockDict["S_1"] = msc.Stock(Name="S_1", P_Res=1, Type=0, Indices="t,e")
    mfa_system.Initialize_StockValues()

    # Set initial stock to 100 units
    mfa_system.StockDict["S_1"].Values[0, 0] = 100.0

    # Define constant inflow of 10 units per year
    inflow_values = np.array([10, 10, 10, 10, 10]).reshape(-1, 1)
    mfa_system.FlowDict["F_0_1"] = msc.Flow(
        Name="F_0_1", P_Start=0, P_End=1, Indices="t,e", Values=inflow_values
    )
    mfa_system.FlowDict["F_1_2"] = msc.Flow(
        Name="F_1_2", P_Start=1, P_End=2, Indices="t,e"
    )
    mfa_system.Initialize_FlowValues()  # Initialize F_1_2 to zeros

    # Define FOMP parameters: k1 = 0.2 (20% decay rate), f = 0, k2 = 0
    fomp_params = {
        1: {
            "outflow_id": "F_1_2",
            "f": 0.0,  # No direct outflow from inflow
            "k1": 0.2,  # 20% decay of existing stock
            "k2": 0.0,  # No decay of new inflow
        }
    }

    # Expected results (calculated by hand):
    # Year 0: Stock = 100, Outflow = 100 * 0.2 = 20, New Stock = 100 + 10 - 20 = 90
    # Year 1: Stock = 90, Outflow = 90 * 0.2 = 18, New Stock = 90 + 10 - 18 = 82
    # Year 2: Stock = 82, Outflow = 82 * 0.2 = 16.4, New Stock = 82 + 10 - 16.4 = 75.6
    # Year 3: Stock = 75.6, Outflow = 75.6 * 0.2 = 15.12, New Stock = 75.6 + 10 - 15.12 = 70.48
    # Year 4: Stock = 70.48, Outflow = 70.48 * 0.2 = 14.096, New Stock = 70.48 + 10 - 14.096 = 66.384
    expected_outflow = np.array([[20.0, 18.0, 16.4, 15.12, 14.096]]).reshape(-1, 1)

    # 2. ACT
    mfa_system_result = calculate_fomp(copy.deepcopy(mfa_system), fomp_params)

    # 3. ASSERT
    actual_outflow = mfa_system_result.FlowDict["F_1_2"].Values
    np.testing.assert_array_almost_equal(actual_outflow, expected_outflow, decimal=2)


def test_calculate_fomp_direct_outflow():
    """
    Tests FOMP calculation with direct outflow from inflow (f parameter).
    """
    # 1. ARRANGE
    start_year, end_year, elements = 2020, 2022, ["material"]
    model_class, index_table = define_model_scope(start_year, end_year, elements)
    mfa_system = initialize_mfa_system(model_class, index_table)

    # Add processes and stock
    mfa_system.ProcessList.append(msc.Process(Name="Environment", ID=0))
    mfa_system.ProcessList.append(msc.Process(Name="Process", ID=1))
    mfa_system.ProcessList.append(msc.Process(Name="Output", ID=2))
    mfa_system.StockDict["S_1"] = msc.Stock(Name="S_1", P_Res=1, Type=0, Indices="t,e")
    mfa_system.Initialize_StockValues()

    # Define inflow: 100 units in year 0, 50 units in year 1, 25 units in year 2
    inflow_values = np.array([100, 50, 25]).reshape(-1, 1)
    mfa_system.FlowDict["F_0_1"] = msc.Flow(
        Name="F_0_1", P_Start=0, P_End=1, Indices="t,e", Values=inflow_values
    )
    mfa_system.FlowDict["F_1_2"] = msc.Flow(
        Name="F_1_2", P_Start=1, P_End=2, Indices="t,e"
    )
    mfa_system.Initialize_FlowValues()

    # Define FOMP parameters: f = 0.3 (30% direct outflow), k1 = 0, k2 = 0
    fomp_params = {
        1: {
            "outflow_id": "F_1_2",
            "f": 0.3,  # 30% direct outflow from inflow
            "k1": 0.0,  # No decay of existing stock
            "k2": 0.0,  # No decay of new inflow
        }
    }

    # Expected results: 30% of each inflow
    expected_outflow = np.array([[30.0, 15.0, 7.5]]).reshape(-1, 1)

    # 2. ACT
    mfa_system_result = calculate_fomp(copy.deepcopy(mfa_system), fomp_params)

    # 3. ASSERT
    actual_outflow = mfa_system_result.FlowDict["F_1_2"].Values
    np.testing.assert_array_almost_equal(actual_outflow, expected_outflow)


def test_calculate_fomp_multi_element():
    """
    Tests FOMP calculation with multiple elements (material, WC, CC).
    """
    # 1. ARRANGE
    start_year, end_year, elements = 2020, 2021, ["material", "WC", "CC"]
    model_class, index_table = define_model_scope(start_year, end_year, elements)
    mfa_system = initialize_mfa_system(model_class, index_table)

    # Add processes and stock
    mfa_system.ProcessList.append(msc.Process(Name="Environment", ID=0))
    mfa_system.ProcessList.append(msc.Process(Name="Process", ID=1))
    mfa_system.ProcessList.append(msc.Process(Name="Output", ID=2))
    mfa_system.StockDict["S_1"] = msc.Stock(Name="S_1", P_Res=1, Type=0, Indices="t,e")
    mfa_system.Initialize_StockValues()

    # Set initial stock: 100 material, 50 WC, 20 CC
    mfa_system.StockDict["S_1"].Values[0, :] = [100.0, 50.0, 20.0]

    # Define inflow: 10 material, 5 WC, 2 CC
    inflow_values = np.array([[10, 5, 2], [10, 5, 2]])
    mfa_system.FlowDict["F_0_1"] = msc.Flow(
        Name="F_0_1", P_Start=0, P_End=1, Indices="t,e", Values=inflow_values
    )
    mfa_system.FlowDict["F_1_2"] = msc.Flow(
        Name="F_1_2", P_Start=1, P_End=2, Indices="t,e"
    )
    mfa_system.Initialize_FlowValues()

    # Define FOMP parameters: f = 0.2, k1 = 0.1, k2 = 0.05
    fomp_params = {
        1: {
            "outflow_id": "F_1_2",
            "f": 0.2,  # 20% direct outflow
            "k1": 0.1,  # 10% decay of existing stock
            "k2": 0.05,  # 5% decay of new inflow
        }
    }

    # Expected results for year 0:
    # Direct outflow: 10*0.2 + 5*0.2 + 2*0.2 = 2 + 1 + 0.4 = 3.4
    # Stock decay: 100*0.1 + 50*0.1 + 20*0.1 = 10 + 5 + 2 = 17
    # Inflow decay: 10*0.05 + 5*0.05 + 2*0.05 = 0.5 + 0.25 + 0.1 = 0.85
    # Total: 3.4 + 17 + 0.85 = 21.25
    expected_outflow = np.array([[12.5, 6.25, 2.5], [12.25, 6.125, 2.45]])

    # 2. ACT
    mfa_system_result = calculate_fomp(copy.deepcopy(mfa_system), fomp_params)

    # 3. ASSERT
    actual_outflow = mfa_system_result.FlowDict["F_1_2"].Values
    np.testing.assert_array_almost_equal(actual_outflow, expected_outflow, decimal=2)


def test_calculate_fomp_missing_outflow_id():
    """
    Tests that the function handles missing outflow_id parameter gracefully.
    """
    # 1. ARRANGE
    start_year, end_year, elements = 2020, 2021, ["material"]
    model_class, index_table = define_model_scope(start_year, end_year, elements)
    mfa_system = initialize_mfa_system(model_class, index_table)

    # Add processes and stock
    mfa_system.ProcessList.append(msc.Process(Name="Environment", ID=0))
    mfa_system.ProcessList.append(msc.Process(Name="Process", ID=1))
    mfa_system.ProcessList.append(msc.Process(Name="Output", ID=2))
    mfa_system.StockDict["S_1"] = msc.Stock(Name="S_1", P_Res=1, Type=0, Indices="t,e")
    mfa_system.Initialize_StockValues()

    # Define inflow
    inflow_values = np.array([10, 10]).reshape(-1, 1)
    mfa_system.FlowDict["F_0_1"] = msc.Flow(
        Name="F_0_1", P_Start=0, P_End=1, Indices="t,e", Values=inflow_values
    )
    mfa_system.FlowDict["F_1_2"] = msc.Flow(
        Name="F_1_2", P_Start=1, P_End=2, Indices="t,e"
    )
    mfa_system.Initialize_FlowValues()

    # Define FOMP parameters without outflow_id
    fomp_params = {
        1: {
            "f": 0.2,
            "k1": 0.1,
            "k2": 0.05,
            # Missing 'outflow_id'
        }
    }

    # 2. ACT & 3. ASSERT
    # The function should handle this gracefully by using None as outflow_flow_name
    # and then trying to access mfa_system.FlowDict[None], which will raise a KeyError
    with pytest.raises(KeyError):
        calculate_fomp(mfa_system, fomp_params)


def test_calculate_fomp_no_inflows():
    """
    Tests FOMP calculation when there are no inflows to the process.
    """
    # 1. ARRANGE
    start_year, end_year, elements = 2020, 2021, ["material"]
    model_class, index_table = define_model_scope(start_year, end_year, elements)
    mfa_system = initialize_mfa_system(model_class, index_table)

    # Add processes and stock
    mfa_system.ProcessList.append(msc.Process(Name="Environment", ID=0))
    mfa_system.ProcessList.append(msc.Process(Name="Process", ID=1))
    mfa_system.ProcessList.append(msc.Process(Name="Output", ID=2))
    mfa_system.StockDict["S_1"] = msc.Stock(Name="S_1", P_Res=1, Type=0, Indices="t,e")
    mfa_system.Initialize_StockValues()

    # Set initial stock to 100 units
    mfa_system.StockDict["S_1"].Values[0, 0] = 100.0

    # No inflow flows defined
    mfa_system.FlowDict["F_1_2"] = msc.Flow(
        Name="F_1_2", P_Start=1, P_End=2, Indices="t,e"
    )
    mfa_system.Initialize_FlowValues()

    # Define FOMP parameters
    fomp_params = {
        1: {
            "outflow_id": "F_1_2",
            "f": 0.0,
            "k1": 0.2,  # 20% decay of existing stock
            "k2": 0.0,
        }
    }

    # Expected results: Only stock decay, no inflows
    # Year 0: Outflow = 100 * 0.2 = 20, New Stock = 100 - 20 = 80
    # Year 1: Outflow = 80 * 0.2 = 16, New Stock = 80 - 16 = 64
    expected_outflow = np.array([20.0, 16.0]).reshape(-1, 1)

    # 2. ACT
    mfa_system_result = calculate_fomp(copy.deepcopy(mfa_system), fomp_params)

    # 3. ASSERT
    actual_outflow = mfa_system_result.FlowDict["F_1_2"].Values
    np.testing.assert_array_almost_equal(actual_outflow, expected_outflow)
