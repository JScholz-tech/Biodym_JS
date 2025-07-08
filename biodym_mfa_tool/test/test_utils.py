# -*- coding: utf-8 -*-
"""
Tests for the utils.py module.

This file contains unit tests for utility functions including parameter sampling
and result export functionality.
"""

import sys
import os
import pytest
import pandas as pd
import numpy as np
import tempfile
import shutil

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

from utils import sample_parameters, export_results_to_excel
from system_setup import define_model_scope, initialize_mfa_system


class TestSampleParameters:
    """Test cases for the sample_parameters function."""

    def test_sample_parameters_uniform_distribution(self):
        """
        Tests that uniform distribution sampling works correctly.
        """
        # 1. ARRANGE
        uncertainty_defs = {
            'param1': {
                'distribution': 'uniform',
                'min': 0.0,
                'max': 1.0
            }
        }
        np.random.seed(42)  # Set seed for reproducible results

        # 2. ACT
        result = sample_parameters(uncertainty_defs)

        # 3. ASSERT
        assert 'param1' in result
        assert isinstance(result['param1'], float)
        assert 0.0 <= result['param1'] <= 1.0

    def test_sample_parameters_normal_distribution(self):
        """
        Tests that normal distribution sampling works correctly.
        """
        # 1. ARRANGE
        uncertainty_defs = {
            'param2': {
                'distribution': 'normal',
                'mean': 10.0,
                'std': 2.0
            }
        }
        np.random.seed(42)  # Set seed for reproducible results

        # 2. ACT
        result = sample_parameters(uncertainty_defs)

        # 3. ASSERT
        assert 'param2' in result
        assert isinstance(result['param2'], float)
        # For a normal distribution, most values should be within 3 standard deviations
        assert abs(result['param2'] - 10.0) < 6.0

    def test_sample_parameters_triangular_distribution(self):
        """
        Tests that triangular distribution sampling works correctly.
        """
        # 1. ARRANGE
        uncertainty_defs = {
            'param3': {
                'distribution': 'triangular',
                'min': 0.0,
                'mode': 0.5,
                'max': 1.0
            }
        }
        np.random.seed(42)  # Set seed for reproducible results

        # 2. ACT
        result = sample_parameters(uncertainty_defs)

        # 3. ASSERT
        assert 'param3' in result
        assert isinstance(result['param3'], float)
        assert 0.0 <= result['param3'] <= 1.0

    def test_sample_parameters_lognormal_distribution(self):
        """
        Tests that lognormal distribution sampling works correctly.
        """
        # 1. ARRANGE
        uncertainty_defs = {
            'param4': {
                'distribution': 'lognormal',
                'mean': 0.0,
                'std': 1.0
            }
        }
        np.random.seed(42)  # Set seed for reproducible results

        # 2. ACT
        result = sample_parameters(uncertainty_defs)

        # 3. ASSERT
        assert 'param4' in result
        assert isinstance(result['param4'], float)
        assert result['param4'] > 0  # Lognormal always produces positive values

    def test_sample_parameters_multiple_distributions(self):
        """
        Tests that multiple parameters with different distributions can be sampled.
        """
        # 1. ARRANGE
        uncertainty_defs = {
            'uniform_param': {
                'distribution': 'uniform',
                'min': 0.0,
                'max': 10.0
            },
            'normal_param': {
                'distribution': 'normal',
                'mean': 5.0,
                'std': 1.0
            },
            'triangular_param': {
                'distribution': 'triangular',
                'min': 1.0,
                'mode': 5.0,
                'max': 9.0
            }
        }
        np.random.seed(42)  # Set seed for reproducible results

        # 2. ACT
        result = sample_parameters(uncertainty_defs)

        # 3. ASSERT
        assert len(result) == 3
        assert 'uniform_param' in result
        assert 'normal_param' in result
        assert 'triangular_param' in result
        assert 0.0 <= result['uniform_param'] <= 10.0
        assert 1.0 <= result['triangular_param'] <= 9.0

    def test_sample_parameters_unknown_distribution(self, capsys):
        """
        Tests that unknown distribution types are handled gracefully with a warning.
        """
        # 1. ARRANGE
        uncertainty_defs = {
            'unknown_param': {
                'distribution': 'unknown_distribution',
                'min': 0.0,
                'max': 1.0
            }
        }

        # 2. ACT
        result = sample_parameters(uncertainty_defs)
        captured = capsys.readouterr()

        # 3. ASSERT
        assert 'unknown_param' not in result  # Parameter should not be sampled
        assert "WARNING: Unknown distribution type" in captured.out
        assert "unknown_distribution" in captured.out


class TestExportResultsToExcel:
    """Test cases for the export_results_to_excel function."""

    def test_export_results_to_excel_with_valid_data(self):
        """
        Tests that results are correctly exported to Excel with valid MFA system data.
        """
        # 1. ARRANGE
        # Create a simple MFA system for testing
        elements = ['material', 'WC']
        model_class, index_table = define_model_scope(2020, 2021, elements)
        mfa_system = initialize_mfa_system(model_class, index_table)
        
        # Add some test flows
        mfa_system.ProcessList.append(msc.Process(Name='Environment', ID=0))
        mfa_system.ProcessList.append(msc.Process(Name='Process 1', ID=1))
        mfa_system.FlowDict['F_0_1'] = msc.Flow(Name='F_0_1', P_Start=0, P_End=1, Indices='t,e')
        mfa_system.Initialize_FlowValues()
        mfa_system.FlowDict['F_0_1'].Values[0, 0] = 100.0  # material in 2020
        mfa_system.FlowDict['F_0_1'].Values[0, 1] = 50.0   # WC in 2020
        mfa_system.FlowDict['F_0_1'].Values[1, 0] = 110.0  # material in 2021
        mfa_system.FlowDict['F_0_1'].Values[1, 1] = 55.0   # WC in 2021

        # Add some test stocks
        mfa_system.StockDict['S_1'] = msc.Stock(Name='S_1', P_Res=1, Type=0, Indices='t,e')
        mfa_system.Initialize_StockValues()
        mfa_system.StockDict['S_1'].Values[0, 0] = 200.0  # material in 2020
        mfa_system.StockDict['S_1'].Values[0, 1] = 100.0  # WC in 2020
        mfa_system.StockDict['S_1'].Values[1, 0] = 220.0  # material in 2021
        mfa_system.StockDict['S_1'].Values[1, 1] = 110.0  # WC in 2021

        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
            output_path = tmp_file.name

        try:
            # 2. ACT
            export_results_to_excel(mfa_system, output_path)

            # 3. ASSERT
            # Check that the file was created
            assert os.path.exists(output_path)
            
            # Read the exported Excel file and verify its contents
            with pd.ExcelFile(output_path) as xls:
                # Check that both sheets exist
                assert 'Flows_ts' in xls.sheet_names
                assert 'Stocks_ts' in xls.sheet_names
                
                # Read flows sheet
                flows_df = pd.read_excel(xls, 'Flows_ts')
                assert len(flows_df) == 2  # 2 years × 1 flow
                assert 'Flow_ID' in flows_df.columns
                assert 'Year' in flows_df.columns
                assert 'material' in flows_df.columns
                assert 'WC' in flows_df.columns
                
                # Check specific flow values
                flow_2020 = flows_df[(flows_df['Flow_ID'] == 'F_0_1') & (flows_df['Year'] == 2020)]
                assert len(flow_2020) == 1
                assert flow_2020['material'].iloc[0] == 100.0
                assert flow_2020['WC'].iloc[0] == 50.0
                
                # Read stocks sheet
                stocks_df = pd.read_excel(xls, 'Stocks_ts')
                assert len(stocks_df) == 2  # 2 years × 1 stock
                assert 'Stock_ID' in stocks_df.columns
                assert 'Year' in stocks_df.columns
                assert 'material' in stocks_df.columns
                assert 'WC' in stocks_df.columns
                
                # Check specific stock values
                stock_2021 = stocks_df[(stocks_df['Stock_ID'] == 'S_1') & (stocks_df['Year'] == 2021)]
                assert len(stock_2021) == 1
                assert stock_2021['material'].iloc[0] == 220.0
                assert stock_2021['WC'].iloc[0] == 110.0

        finally:
            # Clean up the temporary file
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_export_results_to_excel_with_none_input(self, capsys):
        """
        Tests that the function handles None input gracefully.
        """
        # 1. ARRANGE
        output_path = "test_output.xlsx"

        # 2. ACT
        export_results_to_excel(None, output_path)
        captured = capsys.readouterr()

        # 3. ASSERT
        assert "Export skipped: No results to export." in captured.out
        assert not os.path.exists(output_path)  # File should not be created

    def test_export_results_to_excel_empty_system(self):
        """
        Tests that the function handles an empty MFA system (no flows or stocks).
        """
        # 1. ARRANGE
        elements = ['material']
        model_class, index_table = define_model_scope(2020, 2021, elements)
        mfa_system = initialize_mfa_system(model_class, index_table)
        # Empty system with no flows or stocks

        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
            output_path = tmp_file.name

        try:
            # 2. ACT
            export_results_to_excel(mfa_system, output_path)

            # 3. ASSERT
            assert os.path.exists(output_path)
            
            # Read the exported Excel file
            with pd.ExcelFile(output_path) as xls:
                assert 'Flows_ts' in xls.sheet_names
                assert 'Stocks_ts' in xls.sheet_names
                
                # Check that sheets are empty (except headers)
                flows_df = pd.read_excel(xls, 'Flows_ts')
                stocks_df = pd.read_excel(xls, 'Stocks_ts')
                
                assert len(flows_df) == 0  # No flows to export
                assert len(stocks_df) == 0  # No stocks to export

        finally:
            # Clean up the temporary file
            if os.path.exists(output_path):
                os.unlink(output_path) 