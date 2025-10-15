#!/usr/bin/env python3
"""
Test script for the Comprehensive Wood Yield Calculator
Demonstrates usage and validates functionality
"""

from 251011_Comprehensive_Wood_Yield_Calculator import ComprehensiveWoodYieldCalculator

def test_comprehensive_calculator():
    """
    Test the comprehensive wood yield calculator with different scenarios
    """
    print("Testing Comprehensive Wood Yield Calculator")
    print("=" * 60)
    
    # Create calculator instance
    calculator = ComprehensiveWoodYieldCalculator(study_area_km2=1000, random_seed=42)
    
    # Define test scenarios
    test_scenarios = {
        'Reduced_Yield': 0.85,      # 15% reduction
        'High_Yield': 1.15,         # 15% increase  
        'Low_Yield': 0.70,          # 30% reduction
        'Climate_Impact': 0.90,     # 10% reduction due to climate change
        'Sustainable_Forestry': 0.95 # 5% reduction for sustainable practices
    }
    
    # Run comprehensive analysis
    results = calculator.run_comprehensive_analysis(
        baseline_start_year=2000,
        forecast_end_year=2100,
        additional_scenarios=test_scenarios,
        save_plot=True,
        export_excel=True
    )
    
    # Display key results
    print("\nKey Results Summary:")
    print("-" * 40)
    print(f"Historical Baseline: {results['baseline_params']['average']:.4f} Mm³/year")
    print(f"BWI4 Validation: {results['baseline_params']['bwi4_baseline']:.4f} Mm³/year")
    print(f"Validation Deviation: {results['baseline_params']['bwi4_deviation_percent']:.1f}%")
    print(f"Volatility: {results['baseline_params']['std_deviation_percent']:.1%}")
    
    # Show scenario comparison
    print("\nScenario Comparison (Mean Annual Harvest 2023-2100):")
    print("-" * 60)
    for scenario_name, scenario_data in results['scenarios'].items():
        mean_harvest = scenario_data['Total_Forecast'].mean()
        print(f"{scenario_name:20}: {mean_harvest:8.4f} Mm³/year")
    
    # Display Excel report information
    if results['excel_path']:
        print(f"\nExcel Report Generated:")
        print("-" * 40)
        print(f"File: {results['excel_path']}")
        print("Sheets included:")
        print("  1. Executive_Summary - Key findings and metrics")
        print("  2. Historical_Data - Complete historical dataset (1950-2022)")
        print("  3. Scaled_Data - Area-scaled historical data")
        print("  4. Scenario_[Name] - Individual scenario forecasts")
        print("  5. Scenario_Comparison - All scenarios side-by-side")
        print("  6. Statistical_Analysis - Detailed statistics by scenario")
        print("  7. Validation_Results - Anchor point validation")
        print("  8. Baseline_Analysis - Detailed baseline methodology")
        print("  9. Forecast_Summary - Annual forecasts with statistics")
        print("  10. Comprehensive_Metadata - Complete methodology documentation")
    
    return results

if __name__ == "__main__":
    # Run the test
    test_results = test_comprehensive_calculator()
    
    print("\n" + "=" * 60)
    print("Test completed successfully!")
    print("Check the generated Excel file and PNG plot for detailed results.")
    print("=" * 60)
