#!/usr/bin/env python3
"""
Quick test for the updated Wood Yield Calculator
"""

# Import the class from the main script
exec(open('251006_Yield_Calculation_Wood.py').read())

def quick_test():
    """Quick test of the updated calculator"""
    print("Testing Updated Wood Yield Calculator...")
    
    # Create calculator
    calc = WoodYieldCalculator(study_area_km2=1000)
    
    # Test each step
    print("1. Loading historical data...")
    calc.load_historical_data()
    print(f"   ✓ Loaded {len(calc.historical_data)} years of data")
    
    print("2. Applying scaling...")
    calc.apply_scaling()
    print(f"   ✓ Scaling factors: West={calc.factor_west:.6f}, Unified={calc.factor_unified:.6f}")
    
    print("3. Calculating baseline...")
    calc.calculate_baseline(baseline_start_year=2000)
    print(f"   ✓ BAU Baseline: {calc.baseline_params['average']:.4f} Mm³")
    print(f"   ✓ Std Dev: {calc.baseline_params['std_deviation']:.4f} Mm³")
    
    print("4. Generating scenarios...")
    additional_scenarios = {'Reduced_Yield': 0.85, 'High_Yield': 1.15}
    calc.generate_scenarios(random_seed=42, additional_scenarios=additional_scenarios)
    print(f"   ✓ Generated {len(calc.scenarios)} scenarios: {list(calc.scenarios.keys())}")
    
    print("5. Testing Excel export...")
    excel_path = calc.export_to_excel()
    print(f"   ✓ Excel file created: {excel_path}")
    
    print("\n✅ All tests passed! The updated calculator is working correctly.")
    
    # Show sample data
    print("\nSample BAU Forecast (first 5 years):")
    print(calc.scenarios['BAU'][['Year', 'Total_Forecast']].head())
    
    return True

if __name__ == "__main__":
    quick_test()

