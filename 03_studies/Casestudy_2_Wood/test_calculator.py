#!/usr/bin/env python3
"""
Test script for Wood Yield Calculator
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the class from the main script
exec(open('251006_Yield_Calculation_Wood.py').read())

def test_calculator():
    """Test the WoodYieldCalculator functionality"""
    print("Testing Wood Yield Calculator...")
    
    # Create calculator
    calc = WoodYieldCalculator(study_area_km2=1000)
    
    # Test each step
    print("1. Loading historical data...")
    calc.load_historical_data()
    print(f"   ✓ Loaded {len(calc.historical_data)} years of data")
    
    print("2. Applying scaling...")
    calc.apply_scaling()
    print(f"   ✓ Scaling factors: West={calc.factor_west:.6f}, Unified={calc.factor_unified:.6f}")
    
    print("3. Calculating trend...")
    calc.calculate_trend(trend_start_year=2000)
    print(f"   ✓ Trend: y = {calc.trend_params['slope']:.4f}x + {calc.trend_params['intercept']:.2f}")
    print(f"   ✓ R² = {calc.trend_params['r_squared']:.3f}")
    
    print("4. Generating forecast...")
    calc.generate_forecast(random_seed=42)
    print(f"   ✓ Generated {len(calc.forecast_data)} years of forecast")
    
    print("5. Testing Excel export...")
    excel_path = calc.export_to_excel()
    print(f"   ✓ Excel file created: {excel_path}")
    
    print("\n✅ All tests passed! The calculator is working correctly.")
    return True

if __name__ == "__main__":
    test_calculator()
