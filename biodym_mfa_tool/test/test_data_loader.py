# -*- coding: utf-8 -*-
"""
Tests for the data_loader.py module.

This file contains unit tests for the data loading and validation functions
to ensure they behave as expected under various conditions.
"""

import pytest
import pandas as pd

# We need to import the function we want to test
from src.data_loader import validate_input_data


def test_validate_input_data_success():
    """
    Tests that the validation function runs without error when provided with a
    correctly structured data dictionary.
    """
    # 1. ARRANGE: Create a mock dictionary that has the correct structure.
    correct_data = {
        '1_1_Definition_Flows': pd.DataFrame(columns=['Flow_ID', 'Name(EN)', 'Process_ID_O', 'Process_ID_I']),
        '1_2_Data_Flows': pd.DataFrame(columns=['Flow_ID', 'Year_Flow', 'Flow_Py']),
        '2_1_Definition_Processes': pd.DataFrame(columns=['ID', 'Name(EN)', 'Stock?', 'Initial_Stock?']),
        '2_4_Process_Stock_': pd.DataFrame(columns=['Process_ID', 'Initial_Stock_material']),
        '2_5_dynamic_tcs': pd.DataFrame(columns=['TC_ID', 'Year', 'Value'])
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
        '1_1_Definition_Flows': pd.DataFrame(columns=['Flow_ID', 'Name(EN)', 'Process_ID_O', 'Process_ID_I'])
    }

    # 2. ACT & 3. ASSERT: Use pytest.raises to assert that a ValueError is raised.
    with pytest.raises(ValueError, match="required sheet '1_2_Data_Flows' was not found"):
        validate_input_data(incorrect_data)

