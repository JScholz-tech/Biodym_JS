# -*- coding: utf-8 -*-
"""
Tests for the system_setup.py module.

This file contains unit tests for the system setup and configuration functions
to ensure they build the MFA system object correctly.
"""

import sys
import os
import pytest
import pandas as pd
import numpy as np

# Add framework path to be able to import ODYM.
# This replicates the logic in main.py for the test environment.
try:
    import ODYM_Classes as msc
except ImportError:
    # Get the absolute path to the project's root directory (biodym_mfa_tool)
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    # Get the parent directory of the project root to find the 'framework' folder
    project_root_parent = os.path.dirname(project_root)
    # Construct the path to the ODYM modules
    odym_path = os.path.join(project_root_parent, 'framework', 'ODYM-master_20241127', 'odym', 'modules')
    sys.path.insert(0, odym_path)
    import ODYM_Classes as msc

from system_setup import (define_model_scope, initialize_mfa_system,
                          define_flows_and_parameters, create_dynamic_tc_parameters)


def test_define_model_scope_structure_and_content():
    """
    Tests that define_model_scope creates the correct ODYM classification
    and index table structures with the correct content.
    """
    # 1. ARRANGE: Define simple inputs for the test.
    start, end, elements = 2020, 2022, ['A', 'B']

    # 2. ACT: Run the function to get the actual output.
    model_class, index_table = define_model_scope(start, end, elements)

    # 3. ASSERT: Perform a series of checks on the output.
    assert isinstance(model_class, dict)
    assert isinstance(index_table, pd.DataFrame)
    assert 'Time' in model_class and 'Element' in model_class
    assert isinstance(model_class['Time'], msc.Classification)
    assert model_class['Time'].Items == [2020, 2021, 2022]
    assert model_class['Element'].Items == ['A', 'B']
    assert index_table.loc['Time']['IndexLetter'] == 't'
    assert index_table.loc['Element']['IndexLetter'] == 'e'


def test_initialize_mfa_system_creation():
    """
    Tests that initialize_mfa_system creates a correctly structured
    and initialized MFAsystem object.
    """
    # 1. ARRANGE: Use the define_model_scope function to create valid inputs.
    start, end, elements = 2020, 2022, ['A', 'B']
    model_class, index_table = define_model_scope(start, end, elements)

    # 2. ACT: Run the function to get the actual MFA system object.
    mfa_system = initialize_mfa_system(model_class, index_table)

    # 3. ASSERT: Check the properties of the created object.
    assert isinstance(mfa_system, msc.MFAsystem)
    assert mfa_system.Name == 'RyeStrawMFA'
    assert mfa_system.Unit == 'Mg'
    assert mfa_system.Time_Start == start
    assert mfa_system.Time_End == end
    assert mfa_system.Elements == elements
    assert mfa_system.ProcessList == []
    assert mfa_system.FlowDict == {}
    assert mfa_system.StockDict == {}
    assert mfa_system.ParameterDict == {}
    assert mfa_system.IndexTable.equals(index_table)


def test_define_flows_and_parameters_logic():
    """
    Tests that flows and parameters are correctly defined and that the
    elemental composition for primary input flows is calculated correctly.
    """
    # 1. ARRANGE
    # Setup a base MFA system
    elements = ['material', 'WC', 'CC']
    model_class, index_table = define_model_scope(2020, 2021, elements)
    mfa_system = initialize_mfa_system(model_class, index_table)
    # Manually add processes for the test, as load_and_define_processes is tested separately
    mfa_system.ProcessList.append(msc.Process(Name='Environment', ID=0))
    mfa_system.ProcessList.append(msc.Process(Name='Process 1', ID=1))
    mfa_system.ProcessList.append(msc.Process(Name='Process 2', ID=2))

    # Mock the Excel data dictionary with all necessary sheets
    mock_flow_def = pd.DataFrame({
        'Flow_ID': ['F_00_01', 'F_01_02'],
        'Name(EN)': ['Primary Input', 'Transfer'],
        'Process_ID_O': [0, 1],
        'Process_ID_I': [1, 2],
        'WC': [0.5, np.nan],  # 50% water content for the input flow
        'CC': [0.2, np.nan]   # 20% carbon content for the input flow
    })
    mock_flow_data = pd.DataFrame({
        'Flow_ID': ['F_00_01', 'F_00_01'],
        'Year_Flow': [2020, 2021],
        'Flow_Py': [100, 110]  # Material flow over time
    })
    mock_excel_data = {
        '1_1_Definition_Flows': mock_flow_def,
        '1_2_Data_Flows': mock_flow_data,
        # Add the process definitions sheet, which the function needs to check for initial stocks.
        '2_1_Definition_Processes': pd.DataFrame(columns=['ID', 'Initial_Stock?']),
        '2_5_dynamic_tcs': pd.DataFrame(columns=['TC_ID', 'Year', 'Value']) # Empty but present
    }

    # 2. ACT
    mfa_system_result, _ = define_flows_and_parameters(mfa_system, mock_excel_data)

    # 3. ASSERT
    # Check the elemental composition calculation for the primary input flow
    input_flow = mfa_system_result.FlowDict['F_00_01']
    np.testing.assert_array_almost_equal(input_flow.Values[:, 0], [100, 110]) # material
    np.testing.assert_array_almost_equal(input_flow.Values[:, 1], [50, 55])   # WC = material * 0.5
    np.testing.assert_array_almost_equal(input_flow.Values[:, 2], [20, 22])   # CC = material * 0.2


def test_create_dynamic_tc_parameters_success():
    """
    Tests that dynamic TC parameters are correctly interpolated from input data.
    """
    # 1. ARRANGE
    # Define a time vector and some sparse data points for a TC.
    time_vector = [2020, 2021, 2022, 2023]
    dynamic_tc_data = pd.DataFrame({
        'TC_ID': ['TC_A', 'TC_A'],
        'Year': [2020, 2023],
        'Value': [0.1, 0.4]
    })
    # The expected result after linear interpolation over the time_vector.
    expected_result = {
        'TC_A': np.array([0.1, 0.2, 0.3, 0.4])
    }

    # 2. ACT
    actual_result = create_dynamic_tc_parameters(dynamic_tc_data, time_vector)

    # 3. ASSERT
    assert 'TC_A' in actual_result
    np.testing.assert_array_almost_equal(actual_result['TC_A'], expected_result['TC_A'])


def test_create_dynamic_tc_parameters_duplicate_error():
    """
    Tests that the function raises a ValueError when duplicate data is found.
    """
    # 1. ARRANGE
    # Define a time vector and data with a duplicate entry for TC_A in 2020.
    time_vector = [2020, 2021, 2022]
    duplicate_data = pd.DataFrame({
        'TC_ID': ['TC_A', 'TC_A'],
        'Year': [2020, 2020], # Duplicate year for the same TC_ID
        'Value': [0.1, 0.5]
    })

    # 2. ACT & 3. ASSERT
    # Use pytest.raises to confirm that a ValueError is raised.
    with pytest.raises(ValueError, match="Duplicate entries found"):
        create_dynamic_tc_parameters(duplicate_data, time_vector)

# Add framework path to be able to import ODYM.
# This replicates the logic in main.py for the test environment.
try:
    import ODYM_Classes as msc
except ImportError:
    # Get the absolute path to the project's root directory (biodym_mfa_tool)
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    # Get the parent directory of the project root to find the 'framework' folder
    project_root_parent = os.path.dirname(project_root)
    # Construct the path to the ODYM modules
    odym_path = os.path.join(project_root_parent, 'framework', 'ODYM-master_20241127', 'odym', 'modules')
    sys.path.insert(0, odym_path)
    import ODYM_Classes as msc

from system_setup import define_model_scope, initialize_mfa_system, load_and_define_processes
import data_loader # Import the module to create a mock


def test_define_model_scope_structure_and_content():
    """
    Tests that define_model_scope creates the correct ODYM classification
    and index table structures with the correct content.
    """
    # 1. ARRANGE: Define simple inputs for the test.
    start, end, elements = 2020, 2022, ['A', 'B']

    # 2. ACT: Run the function to get the actual output.
    model_class, index_table = define_model_scope(start, end, elements)

    # 3. ASSERT: Perform a series of checks on the output.
    assert isinstance(model_class, dict)
    assert isinstance(index_table, pd.DataFrame)
    assert 'Time' in model_class and 'Element' in model_class
    assert isinstance(model_class['Time'], msc.Classification)
    assert model_class['Time'].Items == [2020, 2021, 2022]
    assert model_class['Element'].Items == ['A', 'B']
    assert index_table.loc['Time']['IndexLetter'] == 't'
    assert index_table.loc['Element']['IndexLetter'] == 'e'
