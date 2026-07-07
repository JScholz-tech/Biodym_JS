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
    # Get the absolute path to the project's root directory
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    # Construct the path to the ODYM modules (framework is inside the project at 06_framework/)
    odym_path = os.path.join(
        project_root, "06_framework", "ODYM-master_20241127", "odym", "modules"
    )
    sys.path.insert(0, odym_path)
    import ODYM_Classes as msc

from system_setup import (
    define_model_scope,
    initialize_mfa_system,
    load_and_define_processes,
    define_flows_and_parameters,
    create_dynamic_tc_parameters,
)
import data_loader  # Import the module to mock its functions


def test_define_model_scope_structure_and_content():
    """
    Tests that define_model_scope creates the correct ODYM classification
    and index table structures with the correct content.
    """
    # 1. ARRANGE: Define simple inputs for the test.
    start, end, elements = 2020, 2022, ["A", "B"]

    # 2. ACT: Run the function to get the actual output.
    model_class, index_table = define_model_scope(start, end, elements)

    # 3. ASSERT: Perform a series of checks on the output.
    assert isinstance(model_class, dict)
    assert isinstance(index_table, pd.DataFrame)
    assert "Time" in model_class and "Element" in model_class
    assert isinstance(model_class["Time"], msc.Classification)
    assert model_class["Time"].Items == [2020, 2021, 2022]
    assert model_class["Element"].Items == ["A", "B"]
    assert index_table.loc["Time"]["IndexLetter"] == "t"
    assert index_table.loc["Element"]["IndexLetter"] == "e"


def test_initialize_mfa_system_creation():
    """
    Tests that initialize_mfa_system creates a correctly structured
    and initialized MFAsystem object.
    """
    # 1. ARRANGE: Use the define_model_scope function to create valid inputs.
    start, end, elements = 2020, 2022, ["A", "B"]
    model_class, index_table = define_model_scope(start, end, elements)

    # 2. ACT: Run the function to get the actual MFA system object.
    mfa_system = initialize_mfa_system(model_class, index_table)

    # 3. ASSERT: Check the properties of the created object.
    assert isinstance(mfa_system, msc.MFAsystem)
    assert mfa_system.Name == "RyeStrawMFA"
    assert mfa_system.Unit == "Mg"
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
    elements = ["material", "WC", "DM", "CC"]
    model_class, index_table = define_model_scope(2020, 2021, elements)
    mfa_system = initialize_mfa_system(model_class, index_table)
    # Manually add processes for the test, as load_and_define_processes is tested separately
    mfa_system.ProcessList.append(msc.Process(Name="Environment", ID=0))
    mfa_system.ProcessList.append(msc.Process(Name="Process 1", ID=1))
    mfa_system.ProcessList.append(msc.Process(Name="Process 2", ID=2))

    # Mock the Excel data dictionary with all necessary sheets
    mock_flow_def = pd.DataFrame(
        {
            "Flow_ID": ["F_00_01", "F_01_02"],
            "Flow_Name": ["Primary Input", "Transfer"],
            "Flow_Output_Process_ID": [0, 1],
            "Input_Process_ID": [1, 2],
            "Flow_E2_Fraction[%]": [0.5, np.nan],  # E2 = WC: 50% water content for the input flow
            "Flow_E4_Fraction[%]": [0.2, np.nan],  # E4 = CC: 20% carbon content for the input flow
        }
    )
    mock_flow_data = pd.DataFrame(
        {
            "Flow_ID": ["F_00_01", "F_00_01"],
            "Flow_Data_Year": [2020, 2021],
            "E1_value": [100, 110],  # Material flow over time
        }
    )
    mock_excel_data = {
        "1_1_Definition_Flows": mock_flow_def,
        "1_2_Data_Flows": mock_flow_data,
        # Add the process definitions sheet, which the function needs to check for initial stocks.
        "2_1_Definition_Processes": pd.DataFrame(columns=["ID", "TC_Configuration", "Stock_Configuration", "Process_Logic"]),
        "2_3_dynamic_TCs": pd.DataFrame(
            columns=["Flow_ID", "E1_TC_ID", "Year", "E1_TC_Value[%]"]
        ),  # Empty but present
    }

    # 2. ACT
    mfa_system_result, _, _, _ = define_flows_and_parameters(mfa_system, mock_excel_data)

    # 3. ASSERT
    # Check the elemental composition calculation for the primary input flow
    input_flow = mfa_system_result.FlowDict["F_00_01"]
    np.testing.assert_array_almost_equal(
        input_flow.Values[:, 0], [100, 110]
    )  # material
    np.testing.assert_array_almost_equal(
        input_flow.Values[:, 1], [50, 55]
    )  # WC = material * 0.5
    # Note: The order of elements is ["material", "WC", "DM", "CC"]
    # So index 3 is CC, not index 2
    np.testing.assert_array_almost_equal(
        input_flow.Values[:, 3], [20, 22]
    )  # CC = material * 0.2


def test_create_dynamic_tc_parameters_success():
    """
    Tests that dynamic TC parameters are correctly interpolated from input data.
    """
    # 1. ARRANGE
    # Define a time vector and some sparse data points for a TC.
    time_vector = [2020, 2021, 2022, 2023]
    dynamic_tc_data = pd.DataFrame(
        {"TC_ID": ["TC_A", "TC_A"], "Year": [2020, 2023], "Value": [0.1, 0.4]}
    )
    # The expected result after linear interpolation over the time_vector.
    expected_result = {"TC_A": np.array([0.1, 0.2, 0.3, 0.4])}

    # 2. ACT
    actual_result = create_dynamic_tc_parameters(dynamic_tc_data, time_vector)

    # 3. ASSERT
    assert "TC_A" in actual_result
    np.testing.assert_array_almost_equal(actual_result["TC_A"], expected_result["TC_A"])


def test_create_dynamic_tc_parameters_duplicate_error():
    """
    Tests that the function raises a ValueError when duplicate data is found.
    """
    # 1. ARRANGE
    # Define a time vector and data with a duplicate entry for TC_A in 2020.
    time_vector = [2020, 2021, 2022]
    duplicate_data = pd.DataFrame(
        {
            "TC_ID": ["TC_A", "TC_A"],
            "Year": [2020, 2020],  # Duplicate year for the same TC_ID
            "Value": [0.1, 0.5],
        }
    )

    # 2. ACT & 3. ASSERT
    # Use pytest.raises to confirm that a ValueError is raised.
    with pytest.raises(ValueError, match="Duplicate entries found"):
        create_dynamic_tc_parameters(duplicate_data, time_vector)


def test_create_dynamic_tc_parameters_missing_columns():
    """
    Tests that the function raises a ValueError when required columns are missing.
    """
    # 1. ARRANGE
    # Define a time vector and data missing the 'Value' column.
    time_vector = [2020, 2021, 2022]
    incomplete_data = pd.DataFrame(
        {
            "TC_ID": ["TC_A", "TC_B"],
            "Year": [2020, 2021],
            # Missing 'Value' column
        }
    )

    # 2. ACT & 3. ASSERT
    # Use pytest.raises to confirm that a ValueError is raised.
    with pytest.raises(ValueError, match="missing one of the required columns"):
        create_dynamic_tc_parameters(incomplete_data, time_vector)


def test_load_and_define_processes(mocker):
    """
    Tests that processes and stocks are correctly defined from mock data.
    Uses mocking to isolate the function from file I/O and other modules.
    """
    # 1. ARRANGE
    # Create a base MFA system to be modified
    model_class, index_table = define_model_scope(2020, 2021, ["material"])
    mfa_system = initialize_mfa_system(model_class, index_table)

    # Create mock data that `pd.read_excel` will be forced to return
    mock_process_def = pd.DataFrame(
        {
            "ID": [0, 1, 2],
            "Process_Name": ["Environment", "Process A", "Process B (with stock)"],
            "Process_Logic": ["Pass-through", "Pass-through", "Pass-through"],
            "TC_Configuration": ["No TC", "No TC", "No TC"],
            "Stock_Configuration": ["No Stock", "No Stock", "Stock"],
        }
    )
    mock_excel_data = {"2_1_Definition_Processes": mock_process_def}

    # Use the mocker to replace external calls
    mocker.patch("utils.safe_read_excel", return_value=mock_excel_data)
    mocker.patch(
        "data_loader.validate_input_data", return_value=None
    )  # Assume validation works

    # 2. ACT
    mfa_system_result, _ = load_and_define_processes(
        mfa_system, "fake/path.xlsx", data_loader
    )

    # 3. ASSERT
    # Check that processes were added
    assert len(mfa_system_result.ProcessList) == 3
    assert mfa_system_result.ProcessList[1].Name == "Process A"

    # Check that stocks were created ONLY for the correct process
    assert "S_1" not in mfa_system_result.StockDict
    assert "S_2" in mfa_system_result.StockDict
    assert "dS_2" in mfa_system_result.StockDict
    assert isinstance(mfa_system_result.StockDict["S_2"], msc.Stock)


# --------------------------------------------------------------------------
# Process_Logic normalization (whitespace / case tolerance)
# --------------------------------------------------------------------------

def test_process_logic_map_strips_and_canonicalizes():
    from system_setup import _normalize_process_logic_map

    raw = {
        0: "Input",
        1: " FOMP ",       # trailing/leading whitespace
        2: "fomp",         # wrong case
        3: "Bom_assembler",
        4: "Exotic_Logic",  # unknown — kept as stripped string, warned
        5: float("nan"),    # non-string passes through
    }
    result = _normalize_process_logic_map(raw)
    assert result[0] == "Input"
    assert result[1] == "FOMP"
    assert result[2] == "FOMP"
    assert result[3] == "BOM_Assembler"
    assert result[4] == "Exotic_Logic"
    assert result[5] is raw[5]


# --------------------------------------------------------------------------
# apply_scenario — Weibull lifetime Shape/Scale (DSM)
# --------------------------------------------------------------------------

def _weibull_dsm_params():
    return {
        6: {
            "lifetimes": {"Mean": [50.0], "StdDev": [15.0]},
            "inflow_split": [1.0],
            "output_splits": [[1.0]],
        }
    }


def _fake_mfa_system():
    from types import SimpleNamespace

    return SimpleNamespace(FlowDict={}, Elements=["material"])


def _weibull_mod(base, operation, value):
    return {
        "Parameter_Name": f"P06_DSM_Lifetime_{base}_Cat_1",
        "Parameter_Type": "DSM",
        "Operation": operation,
        "New_Value": value,
    }


def test_apply_scenario_sets_weibull_shape_and_scale():
    from system_setup import apply_scenario

    scenario_defs = {
        "S": [_weibull_mod("Shape", "replace", 3.0),
              _weibull_mod("Scale", "replace", 20.0)]
    }
    _, dsm, _, _ = apply_scenario(
        _fake_mfa_system(), scenario_defs, "S", dsm_params=_weibull_dsm_params()
    )
    assert dsm[6]["lifetimes"]["Shape"] == [3.0]
    assert dsm[6]["lifetimes"]["Scale"] == [20.0]


def test_apply_scenario_multiplies_existing_weibull_scale():
    from system_setup import apply_scenario

    params = _weibull_dsm_params()
    params[6]["lifetimes"]["Shape"] = [3.0]
    params[6]["lifetimes"]["Scale"] = [20.0]
    scenario_defs = {"S": [_weibull_mod("Scale", "multiply", 1.5)]}
    _, dsm, _, _ = apply_scenario(
        _fake_mfa_system(), scenario_defs, "S", dsm_params=params
    )
    assert dsm[6]["lifetimes"]["Scale"] == [30.0]
    assert params[6]["lifetimes"]["Scale"] == [20.0]  # original untouched


def test_apply_scenario_weibull_multiply_without_baseline_is_skipped():
    from system_setup import apply_scenario

    scenario_defs = {"S": [_weibull_mod("Shape", "multiply", 1.5)]}
    _, dsm, _, _ = apply_scenario(
        _fake_mfa_system(), scenario_defs, "S", dsm_params=_weibull_dsm_params()
    )
    assert dsm[6]["lifetimes"]["Shape"] == [None]  # created but not modified
