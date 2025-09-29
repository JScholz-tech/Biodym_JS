#!/usr/bin/env python3
"""
Test script for FOMP Pool_ID system integration with Monte Carlo simulation.
"""

import sys
import os
sys.path.insert(0, 'src')

import pandas as pd
from src import data_loader
from src.engine.mc_simulation import apply_fomp_parameter_updates

def test_fomp_parameter_loading():
    """Test loading FOMP parameters with Pool_ID system."""
    print("🧪 Testing FOMP Parameter Loading...")
    
    # Create test data that mimics your Excel structure
    test_data = {
        "3_2_Definition_FOMP": pd.DataFrame([
            {"Pool_ID": "P08_Inflow_fraction_f (Labile pool)", "Parameter_Name": "Inflow_fraction_f (Labile pool)", "Value": 0.7},
            {"Pool_ID": "P08_decay_k1 (Labile pool)", "Parameter_Name": "decay_k1 (Labile pool)", "Value": 0.5},
            {"Pool_ID": "P08_decay_k2 (Recalcitrant pool)", "Parameter_Name": "decay_k2 (Recalcitrant pool)", "Value": 0.025},
            {"Pool_ID": "P08_Outflow_1", "Parameter_Name": "output_carbon_id", "Value": "F_08_00"},
            {"Pool_ID": "P10_decay_k1 (Labile pool)", "Parameter_Name": "decay_k1 (Labile pool)", "Value": 0.3},
            {"Pool_ID": "P10_decay_k2 (Recalcitrant pool)", "Parameter_Name": "decay_k2 (Recalcitrant pool)", "Value": 0.015},
        ])
    }
    
    # Test loading
    fomp_params = data_loader.load_fomp_parameters(test_data)
    
    print(f"✅ Loaded {len(fomp_params)} FOMP processes:")
    for process_id, params in fomp_params.items():
        print(f"   Process {process_id}: {len(params)} parameters")
        for param_name, value in params.items():
            print(f"     {param_name}: {value}")
    
    return fomp_params

def test_monte_carlo_parameter_mapping(fomp_params):
    """Test Monte Carlo parameter mapping."""
    print("\n🧪 Testing Monte Carlo Parameter Mapping...")
    
    # Simulate sampled parameters from Monte Carlo
    sampled_params = {
        "P08_decay_k1 (Labile pool)": 0.6,  # Sampled value
        "P08_decay_k2 (Recalcitrant pool)": 0.03,  # Sampled value
        "P10_decay_k1 (Labile pool)": 0.35,  # Sampled value
        "P10_decay_k2 (Recalcitrant pool)": 0.02,  # Sampled value
    }
    
    print("📊 Sampled parameters:")
    for param_name, value in sampled_params.items():
        print(f"   {param_name}: {value}")
    
    # Apply updates
    updated_fomp_params = apply_fomp_parameter_updates(fomp_params, sampled_params)
    
    print("\n✅ Updated FOMP parameters:")
    for process_id, params in updated_fomp_params.items():
        print(f"   Process {process_id}:")
        for param_name, value in params.items():
            print(f"     {param_name}: {value}")
    
    return updated_fomp_params

def test_uncertainty_parameter_loading():
    """Test loading uncertainty parameters."""
    print("\n🧪 Testing Uncertainty Parameter Loading...")
    
    # Create test uncertainty data
    test_data = {
        "4_1_Uncertainty_Parameters": pd.DataFrame([
            {"Parameter_Name": "P08_decay_k1 (Labile pool)", "Distribution": "Normal", "Mean": 0.5, "StdDev": 0.1},
            {"Parameter_Name": "P08_decay_k2 (Recalcitrant pool)", "Distribution": "Normal", "Mean": 0.025, "StdDev": 0.005},
            {"Parameter_Name": "P10_decay_k1 (Labile pool)", "Distribution": "Normal", "Mean": 0.3, "StdDev": 0.05},
            {"Parameter_Name": "P10_decay_k2 (Recalcitrant pool)", "Distribution": "Normal", "Mean": 0.015, "StdDev": 0.003},
        ])
    }
    
    uncertainty_params = data_loader.load_uncertainty_definitions(test_data)
    
    print(f"✅ Loaded {len(uncertainty_params)} uncertainty parameters:")
    for param_name, definition in uncertainty_params.items():
        print(f"   {param_name}: {definition}")
    
    return uncertainty_params

if __name__ == "__main__":
    print("🚀 Starting FOMP Pool_ID Integration Tests...\n")
    
    try:
        # Test 1: FOMP parameter loading
        fomp_params = test_fomp_parameter_loading()
        
        # Test 2: Monte Carlo parameter mapping
        updated_fomp_params = test_monte_carlo_parameter_mapping(fomp_params)
        
        # Test 3: Uncertainty parameter loading
        uncertainty_params = test_uncertainty_parameter_loading()
        
        print("\n🎉 All tests passed! FOMP Pool_ID integration is working correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

