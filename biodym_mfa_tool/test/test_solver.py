# -*- coding: utf-8 -*-
"""
Tests for the mfa_engine/solver.py module.

This file contains unit tests for the core calculation functions to ensure
their numerical and scientific correctness.
"""
import sys
import os
import pytest
import pandas as pd
import numpy as np

# Add framework path to be able to import ODYM.
try:
    import ODYM_Classes as msc
except ImportError:
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    project_root_parent = os.path.dirname(project_root)
    odym_path = os.path.join(project_root_parent, 'framework', 'ODYM-master_20241127', 'odym', 'modules')
    sys.path.insert(0, odym_path)
    import ODYM_Classes as msc

from system_setup import define_model_scope, initialize_mfa_system
from engine.dsm_model import calculate_dynamic_stock


def test_calculate_dynamic_stock_fixed_lifetime():
    """
    Tests the DSM calculation with a simple fixed lifetime.
    This is a "known-results" test, where the expected output is pre-calculated.
    """
    # 1. ARRANGE
    # Define a simple 10-year system with one element
    start_year, end_year, elements = 2020, 2029, ['material']
    model_class, index_table = define_model_scope(start_year, end_year, elements)
    mfa_system = initialize_mfa_system(model_class, index_table)

    # Add processes and a stock
    mfa_system.ProcessList.append(msc.Process(Name='Environment', ID=0))
    mfa_system.ProcessList.append(msc.Process(Name='In-Use Stock', ID=1))
    mfa_system.ProcessList.append(msc.Process(Name='EoL', ID=2))
    mfa_system.StockDict["S_1"] = msc.Stock(Name="S_1", P_Res=1, Type=0, Indices='t,e')

    # Define a known inflow and an empty outflow
    inflow_values = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]).reshape(-1, 1)
    mfa_system.FlowDict['F_0_1'] = msc.Flow(Name='F_0_1', P_Start=0, P_End=1, Indices='t,e', Values=inflow_values)
    mfa_system.FlowDict['F_1_2'] = msc.Flow(Name='F_1_2', P_Start=1, P_End=2, Indices='t,e')
    mfa_system.Initialize_FlowValues() # Initialize F_1_2 to zeros
    mfa_system.Initialize_StockValues() # Initialize S_1 to zeros

    # Define DSM parameters for a fixed 5-year lifetime
    dsm_params = {
        1: {
            'lifetimes': {'Type': 'Fixed', 'Mean': [5]},
            'inflow_split': [1.0] # Only one category
        }
    }

    # Define the known, correct result
    expected_outflow = np.array([0, 0, 0, 0, 0, 1, 2, 3, 4, 5]).reshape(-1, 1)

    # 2. ACT
    mfa_system_result, _ = calculate_dynamic_stock(mfa_system, dsm_params)

    # 3. ASSERT
    actual_outflow = mfa_system_result.FlowDict['F_1_2'].Values
    np.testing.assert_array_almost_equal(actual_outflow, expected_outflow)