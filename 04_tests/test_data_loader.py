# -*- coding: utf-8 -*-
"""
Tests for the data_loader.py module.

This file contains unit tests for the data loading and validation functions
to ensure they behave as expected under various conditions.
"""

import pytest
import pandas as pd

# We need to import the function we want to test
from data_loader import validate_input_data, load_dsm_parameters, load_fomp_parameters


def test_validate_input_data_success():
    """
    Tests that the validation function runs without error when provided with a
    correctly structured data dictionary.
    """
    # 1. ARRANGE: Create a mock dictionary that has the correct structure.
    correct_data = {
        "1_1_Definition_Flows": pd.DataFrame(
            columns=["Flow_ID", "Flow_Name", "Flow_Output_Process_ID", "Input_Process_ID", "Flow_E1_Fraction[%]"]
        ),
        "1_2_Data_Flows": pd.DataFrame(columns=["Flow_ID", "Flow_Data_Year", "E1_value"]),
        "2_1_Definition_Processes": pd.DataFrame(
            columns=["ID", "Process_Name", "Process_Logic", "TC_Configuration", "Stock_Configuration"]
        ),
        "2_2_static_TCs": pd.DataFrame(
            columns=["Flow_ID", "Process_ID", "E1_TC_ID", "E1_TC_Value[%]"]
        ),
        "2_4_Initial_Stock": pd.DataFrame(
            columns=[
                "Process_ID",
                "IS_Parameter_type",
                "IS_Parameter_Value",
            ]
        ),
    }
    # 2. ACT & 3. ASSERT: Run the function and assert that it does NOT raise an error.
    # If it raises an error, the test will fail automatically.
    validate_input_data(correct_data)


def test_validate_input_data_missing_sheet():
    """
    Tests that the validation function correctly raises a ValueError when a
    required sheet is missing from the input data.
    """
    # 1. ARRANGE: Create a mock dictionary that is missing a required sheet.
    incorrect_data = {
        "1_1_Definition_Flows": pd.DataFrame(
            columns=["Flow_ID", "Flow_Name", "Flow_Output_Process_ID", "Input_Process_ID", "Flow_E1_Fraction[%]"]
        )
    }

    # 2. ACT & 3. ASSERT: Use pytest.raises to assert that a ValueError is raised.
    with pytest.raises(
        ValueError, match="required sheet '1_2_Data_Flows' was not found"
    ):
        validate_input_data(incorrect_data)


def test_load_dsm_parameters_parsing():
    """
    Tests that the DSM parameter loading function correctly parses a DataFrame
    into the expected nested dictionary structure.
    """
    # 1. ARRANGE: Create a mock DataFrame that simulates the '3_1_Definition_DSM' sheet.
    # This includes multiple categories for one process to test the grouping logic.
    dsm_data = {
        "Process_ID": [6, 6, 7],
        "Category_ID": [1, 2, 1],
        "Inflow_Split_[%]": [0.8, 0.2, 1.0],
        "Lifetime_Type": ["Normal", "Normal", "Lognormal"],
        "Lifetime_Mean": [20, 5, 50],
        "Lifetime_StdDev": [2, 0.5, 10],
        "Category_Name": ["Category A", "Category B", "Category C"],
    }
    mock_df = pd.DataFrame(dsm_data)

    # Add process definitions to identify DSM processes
    process_data = {
        "Process_ID": [6, 7],
        "Process_Name": ["Process 6", "Process 7"],
        "Process_Logic": ["DSM", "DSM"],
        "Stock_Configuration": ["Stock", "Stock"],
    }
    process_df = pd.DataFrame(process_data)

    mock_excel_data = {
        "3_1_Definition_DSM": mock_df,
        "2_1_Definition_Processes": process_df,
    }

    # Define the exact dictionary structure we expect as output.
    # Note: Type is now a list, parameter_based flag and stock_configuration are included
    expected_result = {
        6: {
            "category_names": ["Category A", "Category B"],
            "inflow_split": [0.8, 0.2],
            "lifetimes": {"Type": ["Normal", "Normal"], "Mean": [20, 5], "StdDev": [2.0, 0.5]},
            "parameter_based": False,
            "stock_configuration": "Stock",
        },
        7: {
            "category_names": ["Category C"],
            "inflow_split": [1.0],
            "lifetimes": {"Type": ["Lognormal"], "Mean": [50], "StdDev": [10.0]},
            "parameter_based": False,
            "stock_configuration": "Stock",
        },
    }

    # 2. ACT: Run the function with our mock data.
    actual_result = load_dsm_parameters(mock_excel_data)

    # 3. ASSERT: Check if the actual result is identical to our expected result.
    # Convert numpy int64 keys to regular ints for comparison
    actual_result = {int(k): v for k, v in actual_result.items()}
    assert actual_result == expected_result


def test_load_fomp_parameters_parsing():
    """
    Tests that the FOMP parameter loading function correctly parses a DataFrame
    into the expected nested dictionary structure, handling mixed data types.
    """
    # 1. ARRANGE: Create a mock DataFrame that simulates the '3_2_Definition_FOMP' sheet.
    fomp_data = {
        "Process_ID": [8, 8, 8, 9],
        "Parameter_Name": ["outflow_id", "k1", "f", "k1"],
        "Value": ["F_08_00", 0.025, 0.1, 0.5],
    }
    mock_df = pd.DataFrame(fomp_data)
    mock_excel_data = {"3_2_Definition_FOMP": mock_df}

    # Define the exact dictionary structure we expect as output.
    expected_result = {
        8: {"outflow_id": "F_08_00", "k1": 0.025, "f": 0.1},
        9: {"k1": 0.5},
    }

    # 2. ACT: Run the function with our mock data.
    actual_result = load_fomp_parameters(mock_excel_data)

    # 3. ASSERT: Check if the actual result is identical to our expected result.
    assert actual_result == expected_result
