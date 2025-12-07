"""
Tests for dynamic TC normalization to prevent mass balance errors.

This test suite verifies that the normalize_dynamic_tcs_by_process() function
correctly normalizes dynamic transfer coefficients to sum to 100% at each time step,
preventing mass balance errors caused by independent interpolation.

See: 05_docs/development/DYNAMIC_TC_MASS_BALANCE_BUG.md
"""

import numpy as np
import pandas as pd
import pytest
import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(project_root, "02_src"))

# Add ODYM to path with try-except for robustness
try:
    import ODYM_Classes as msc  # type: ignore
except ImportError:
    odym_path = os.path.join(
        project_root, "06_framework", "ODYM-master_20241127", "odym", "modules"
    )
    if odym_path not in sys.path:
        sys.path.insert(0, odym_path)
    import ODYM_Classes as msc  # type: ignore

from data_loader import normalize_dynamic_tcs_by_process, load_tc_parameters


@pytest.fixture
def mock_excel_data_aligned():
    """Mock Excel data with aligned data points (should sum to 100%)."""
    return {
        "2_1_Definition_Processes": pd.DataFrame(
            {
                "Process_ID": [5],
                "Process_Name": ["Splitter_A"],
                "Process_Logic": ["Splitter"],
                "TC_Configuration": ["Dynamic"],
                "Stock_Configuration": ["No Stock"],
            }
        ),
        "2_2_static_TCs": pd.DataFrame(
            {
                "Flow_ID": [10, 11, 12],
                "Process_ID": [5, 5, 5],
                "E1_TC_ID": ["TC_A", "TC_B", "TC_C"],
            }
        ),
        "2_3_dynamic_TCs": pd.DataFrame(
            {
                "Year": [2000, 2020, 2000, 2020, 2000, 2020],
                "E1_TC_ID": ["TC_A", "TC_A", "TC_B", "TC_B", "TC_C", "TC_C"],
                "E1_TC_Value[%]": [0.30, 0.40, 0.40, 0.35, 0.30, 0.25],
            }
        ),
    }


@pytest.fixture
def mock_excel_data_misaligned():
    """Mock Excel data with misaligned data points (will NOT sum to 100%)."""
    return {
        "2_1_Definition_Processes": pd.DataFrame(
            {
                "Process_ID": [5],
                "Process_Name": ["Splitter_A"],
                "Process_Logic": ["Splitter"],
                "TC_Configuration": ["Dynamic"],
                "Stock_Configuration": ["No Stock"],
            }
        ),
        "2_2_static_TCs": pd.DataFrame(
            {
                "Flow_ID": [10, 11, 12],
                "Process_ID": [5, 5, 5],
                "E1_TC_ID": ["TC_A", "TC_B", "TC_C"],
            }
        ),
        "2_3_dynamic_TCs": pd.DataFrame(
            {
                "Year": [2000, 2020, 2005, 2025, 2000, 2015],
                "E1_TC_ID": ["TC_A", "TC_A", "TC_B", "TC_B", "TC_C", "TC_C"],
                "E1_TC_Value[%]": [0.30, 0.40, 0.35, 0.45, 0.30, 0.20],
            }
        ),
    }


@pytest.fixture
def mock_excel_data_large_deviation():
    """Mock Excel data that sums to significantly != 100% (should trigger warning)."""
    return {
        "2_1_Definition_Processes": pd.DataFrame(
            {
                "Process_ID": [5],
                "Process_Name": ["Splitter_A"],
                "Process_Logic": ["Splitter"],
                "TC_Configuration": ["Dynamic"],
                "Stock_Configuration": ["No Stock"],
            }
        ),
        "2_2_static_TCs": pd.DataFrame(
            {
                "Flow_ID": [10, 11],
                "Process_ID": [5, 5],
                "E1_TC_ID": ["TC_A", "TC_B"],
            }
        ),
        "2_3_dynamic_TCs": pd.DataFrame(
            {
                "Year": [2000, 2020, 2000, 2020],
                "E1_TC_ID": ["TC_A", "TC_A", "TC_B", "TC_B"],
                "E1_TC_Value[%]": [0.30, 0.50, 0.40, 0.60],  # Sum: 70% -> 110%
            }
        ),
    }


def test_aligned_data_points_sum_to_100(mock_excel_data_aligned):
    """Test normalization with aligned data points that already sum to 100%."""
    elements = ["material"]
    time_vector = np.arange(2000, 2021)  # 2000-2020

    # Load TCs (includes interpolation)
    tc_params = load_tc_parameters(
        mock_excel_data_aligned, elements, time_vector, debug_mode=False
    )

    # Check that we have 3 TCs
    assert "TC_A" in tc_params
    assert "TC_B" in tc_params
    assert "TC_C" in tc_params

    # Verify TCs are arrays (dynamic)
    assert isinstance(tc_params["TC_A"].Values, np.ndarray)
    assert len(tc_params["TC_A"].Values) == len(time_vector)

    # Check that TCs sum to 1.0 (100%) at ALL time steps
    for year_idx in range(len(time_vector)):
        tc_sum = (
            tc_params["TC_A"].Values[year_idx]
            + tc_params["TC_B"].Values[year_idx]
            + tc_params["TC_C"].Values[year_idx]
        )
        assert np.isclose(
            tc_sum, 1.0, atol=1e-6
        ), f"Year {time_vector[year_idx]}: sum={tc_sum}"


def test_misaligned_data_points_normalized(mock_excel_data_misaligned):
    """Test normalization with misaligned data points."""
    elements = ["material"]
    time_vector = np.arange(2000, 2026)  # 2000-2025

    # Load TCs (includes interpolation and normalization)
    tc_params = load_tc_parameters(
        mock_excel_data_misaligned, elements, time_vector, debug_mode=False
    )

    # Check that TCs sum to 1.0 (100%) at ALL time steps
    for year_idx in range(len(time_vector)):
        tc_sum = (
            tc_params["TC_A"].Values[year_idx]
            + tc_params["TC_B"].Values[year_idx]
            + tc_params["TC_C"].Values[year_idx]
        )
        assert np.isclose(
            tc_sum, 1.0, atol=1e-6
        ), f"Year {time_vector[year_idx]}: sum={tc_sum} (TCs: A={tc_params['TC_A'].Values[year_idx]:.3f}, B={tc_params['TC_B'].Values[year_idx]:.3f}, C={tc_params['TC_C'].Values[year_idx]:.3f})"


def test_large_deviation_triggers_warning(mock_excel_data_large_deviation, capsys):
    """Test that large deviations (>5%) trigger a warning message."""
    elements = ["material"]
    time_vector = np.arange(2000, 2021)  # 2000-2020

    # Load TCs (should print warning)
    tc_params = load_tc_parameters(
        mock_excel_data_large_deviation, elements, time_vector, debug_mode=False
    )

    # Capture printed output
    captured = capsys.readouterr()

    # Check that warning was printed
    assert "WARNING" in captured.out
    assert "Process 5" in captured.out
    assert "Normalizing" in captured.out

    # Verify TCs still sum to 100% after normalization
    for year_idx in range(len(time_vector)):
        tc_sum = (
            tc_params["TC_A"].Values[year_idx] + tc_params["TC_B"].Values[year_idx]
        )
        assert np.isclose(tc_sum, 1.0, atol=1e-6)


def test_single_tc_not_normalized():
    """Test that single TC (no normalization needed) is left unchanged."""
    mock_data = {
        "2_1_Definition_Processes": pd.DataFrame(
            {
                "Process_ID": [5],
                "Process_Name": ["Splitter_A"],
                "Process_Logic": ["Splitter"],
                "TC_Configuration": ["Dynamic"],
                "Stock_Configuration": ["No Stock"],
            }
        ),
        "2_2_static_TCs": pd.DataFrame(
            {
                "Flow_ID": [10],
                "Process_ID": [5],
                "E1_TC_ID": ["TC_A"],
            }
        ),
        "2_3_dynamic_TCs": pd.DataFrame(
            {
                "Year": [2000, 2020],
                "E1_TC_ID": ["TC_A", "TC_A"],
                "E1_TC_Value[%]": [0.80, 0.90],  # Not 100%, but single TC
            }
        ),
    }

    elements = ["material"]
    time_vector = np.arange(2000, 2021)

    tc_params = load_tc_parameters(mock_data, elements, time_vector, debug_mode=False)

    # Single TC should keep its original values (interpolated but not normalized)
    assert "TC_A" in tc_params

    # Check interpolated value at year 2010 (midpoint)
    year_2010_idx = 10
    expected_value = 0.80 + (0.90 - 0.80) * 0.5  # Linear interpolation
    assert np.isclose(tc_params["TC_A"].Values[year_2010_idx], expected_value, atol=1e-6)


def test_static_tcs_not_affected():
    """Test that static TCs are not affected by normalization."""
    mock_data = {
        "2_1_Definition_Processes": pd.DataFrame(
            {
                "Process_ID": [5],
                "Process_Name": ["Splitter_A"],
                "Process_Logic": ["Splitter"],
                "TC_Configuration": ["Static"],
                "Stock_Configuration": ["No Stock"],
            }
        ),
        "2_2_static_TCs": pd.DataFrame(
            {
                "Flow_ID": [10, 11],
                "Process_ID": [5, 5],
                "E1_TC_ID": ["TC_A", "TC_B"],
                "E1_TC_Value[%]": [0.60, 0.50],  # Sum = 110% (but static)
            }
        ),
    }

    elements = ["material"]
    time_vector = np.arange(2000, 2021)

    tc_params = load_tc_parameters(mock_data, elements, time_vector, debug_mode=False)

    # Static TCs should keep original values (no normalization for static)
    assert tc_params["TC_A"].Values == 0.60
    assert tc_params["TC_B"].Values == 0.50


def test_multi_element_normalization():
    """Test normalization works independently for each element."""
    mock_data = {
        "2_1_Definition_Processes": pd.DataFrame(
            {
                "Process_ID": [5],
                "Process_Name": ["Transformer_A"],
                "Process_Logic": ["Transformer"],
                "TC_Configuration": ["Dynamic"],
                "Stock_Configuration": ["No Stock"],
            }
        ),
        "2_2_static_TCs": pd.DataFrame(
            {
                "Flow_ID": [10, 11, 10, 11],
                "Process_ID": [5, 5, 5, 5],
                "E1_TC_ID": ["TC_A", "TC_B", None, None],
                "E2_TC_ID": [None, None, "TC_C", "TC_D"],
            }
        ),
        "2_3_dynamic_TCs": pd.DataFrame(
            {
                "Year": [2000, 2020, 2000, 2020, 2000, 2020, 2000, 2020],
                "E1_TC_ID": ["TC_A", "TC_A", "TC_B", "TC_B", None, None, None, None],
                "E1_TC_Value[%]": [0.30, 0.40, 0.40, 0.35, None, None, None, None],
                "E2_TC_ID": [None, None, None, None, "TC_C", "TC_C", "TC_D", "TC_D"],
                "E2_TC_Value[%]": [None, None, None, None, 0.50, 0.60, 0.50, 0.45],
            }
        ),
    }

    elements = ["material", "WC"]
    time_vector = np.arange(2000, 2021)

    tc_params = load_tc_parameters(mock_data, elements, time_vector, debug_mode=False)

    # Check E1 (material) TCs sum to 100%
    for year_idx in range(len(time_vector)):
        tc_sum_e1 = (
            tc_params["TC_A"].Values[year_idx] + tc_params["TC_B"].Values[year_idx]
        )
        assert np.isclose(tc_sum_e1, 1.0, atol=1e-6)

    # Check E2 (WC) TCs sum to 100%
    for year_idx in range(len(time_vector)):
        tc_sum_e2 = (
            tc_params["TC_C"].Values[year_idx] + tc_params["TC_D"].Values[year_idx]
        )
        assert np.isclose(tc_sum_e2, 1.0, atol=1e-6)


def test_normalization_preserves_proportions():
    """Test that normalization preserves relative proportions of TCs."""
    mock_data = {
        "2_1_Definition_Processes": pd.DataFrame(
            {
                "Process_ID": [5],
                "Process_Name": ["Splitter_A"],
                "Process_Logic": ["Splitter"],
                "TC_Configuration": ["Dynamic"],
                "Stock_Configuration": ["No Stock"],
            }
        ),
        "2_2_static_TCs": pd.DataFrame(
            {
                "Flow_ID": [10, 11, 12],
                "Process_ID": [5, 5, 5],
                "E1_TC_ID": ["TC_A", "TC_B", "TC_C"],
            }
        ),
        "2_3_dynamic_TCs": pd.DataFrame(
            {
                "Year": [2000, 2000, 2000],
                "E1_TC_ID": ["TC_A", "TC_B", "TC_C"],
                "E1_TC_Value[%]": [0.20, 0.40, 0.50],  # Sum = 110% (not 100%)
            }
        ),
    }

    elements = ["material"]
    time_vector = np.arange(2000, 2001)  # Single year

    tc_params = load_tc_parameters(mock_data, elements, time_vector, debug_mode=False)

    # Get normalized values
    tc_a = tc_params["TC_A"].Values[0]
    tc_b = tc_params["TC_B"].Values[0]
    tc_c = tc_params["TC_C"].Values[0]

    # Check sum is 100%
    assert np.isclose(tc_a + tc_b + tc_c, 1.0, atol=1e-6)

    # Check proportions are preserved
    # Original: A:B:C = 20:40:50 = 2:4:5
    # After normalization: should still be 2:4:5
    assert np.isclose(tc_a / tc_b, 20 / 40, atol=1e-6)  # A/B ratio preserved
    assert np.isclose(tc_b / tc_c, 40 / 50, atol=1e-6)  # B/C ratio preserved
    assert np.isclose(tc_a / tc_c, 20 / 50, atol=1e-6)  # A/C ratio preserved


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
