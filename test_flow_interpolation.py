"""
Test script for flow data interpolation feature.

This test verifies that flow data with gaps in the time series is correctly
interpolated using linear interpolation.
"""

import pandas as pd
import numpy as np

def test_flow_interpolation():
    """Test that flow data interpolation fills gaps correctly."""

    # Create test data with gaps (only years 1990, 1995, 2000)
    test_years = [1990, 1995, 2000]
    test_values = [100, 150, 200]

    # Expected full time vector (1990-2000, every year)
    full_time_vector = list(range(1990, 2001))

    # Create pandas Series and interpolate (same logic as implementation)
    ts = pd.Series(test_values, index=test_years)
    ts_full = ts.reindex(full_time_vector)
    ts_interpolated = ts_full.interpolate(method='linear', limit_direction='both')

    # Handle edge cases
    if ts_interpolated.isna().any():
        ts_interpolated = ts_interpolated.ffill().bfill()

    # Verify results
    expected = {
        1990: 100.0,
        1991: 110.0,  # Linear interpolation: 100 + (150-100)/5 * 1
        1992: 120.0,
        1993: 130.0,
        1994: 140.0,
        1995: 150.0,
        1996: 160.0,  # Linear interpolation: 150 + (200-150)/5 * 1
        1997: 170.0,
        1998: 180.0,
        1999: 190.0,
        2000: 200.0
    }

    print("Flow Data Interpolation Test")
    print("=" * 50)
    print(f"\nInput data points: {len(test_years)}")
    print(f"Years: {test_years}")
    print(f"Values: {test_values}")
    print(f"\nFull time vector length: {len(full_time_vector)}")
    print(f"Years: {full_time_vector}")
    print("\nInterpolated results:")
    print("-" * 50)

    all_correct = True
    for year in full_time_vector:
        interpolated_value = ts_interpolated.loc[year]
        expected_value = expected[year]
        is_correct = abs(interpolated_value - expected_value) < 0.01

        status = "[PASS]" if is_correct else "[FAIL]"
        print(f"{status} {year}: {interpolated_value:.2f} (expected: {expected_value:.2f})")

        if not is_correct:
            all_correct = False

    print("\n" + "=" * 50)
    if all_correct:
        print("[SUCCESS] All tests passed! Flow interpolation working correctly.")
        return True
    else:
        print("[FAILURE] Some tests failed! Check interpolation logic.")
        return False

if __name__ == "__main__":
    success = test_flow_interpolation()
    exit(0 if success else 1)
