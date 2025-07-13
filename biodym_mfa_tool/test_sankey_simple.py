# -*- coding: utf-8 -*-
"""
Simple Test Script for Sankey Diagram Functionality

This script tests the basic Sankey diagram functionality to ensure it works correctly.
"""

import os
import sys
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch

# Add project paths
current_dir = os.getcwd()
src_path = os.path.join(current_dir, "src")
sys.path.insert(0, src_path)

# Add framework paths
project_root_parent = os.path.dirname(os.path.dirname(src_path))
odym_path = os.path.join(
    project_root_parent, "framework", "ODYM-master_20241127", "odym", "modules"
)
sys.path.insert(0, odym_path)

biodym_addon_path = os.path.join(
    project_root_parent, "framework", "bioDYM_add-on", "modules"
)
sys.path.insert(0, biodym_addon_path)

def create_test_mfa_system():
    """Create a simple test MFA system for Sankey testing."""
    mock_system = Mock()
    
    # Set up basic classification
    mock_system.IndexTable.Classification = {"Time": Mock()}
    mock_system.IndexTable.Classification["Time"].Items = [2020, 2021, 2022]
    mock_system.Elements = ["material", "WC", "DM", "CC"]
    
    # Create simple processes
    mock_system.ProcessList = [
        Mock(Name="Environment", ID=0),
        Mock(Name="Production", ID=1),
        Mock(Name="Consumption", ID=2),
        Mock(Name="Recycling", ID=3)
    ]
    
    # Create simple flows
    mock_system.FlowDict = {
        "F_0_1": Mock(
            P_Start=0, P_End=1,
            Values=np.array([
                [1000, 100, 50, 20],
                [1100, 110, 55, 22],
                [1200, 120, 60, 24]
            ])
        ),
        "F_1_2": Mock(
            P_Start=1, P_End=2,
            Values=np.array([
                [900, 90, 45, 18],
                [990, 99, 49.5, 19.8],
                [1080, 108, 54, 21.6]
            ])
        ),
        "F_2_3": Mock(
            P_Start=2, P_End=3,
            Values=np.array([
                [800, 80, 40, 16],
                [880, 88, 44, 17.6],
                [960, 96, 48, 19.2]
            ])
        ),
        "F_3_0": Mock(
            P_Start=3, P_End=0,
            Values=np.array([
                [700, 70, 35, 14],
                [770, 77, 38.5, 15.4],
                [840, 84, 42, 16.8]
            ])
        )
    }
    
    return mock_system

def test_sankey_import():
    """Test that the plotting module can be imported."""
    print("🧪 Testing plotting module import...")
    
    try:
        import plotting
        print("✅ Plotting module imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import plotting module: {e}")
        return False

def test_sankey_function_exists():
    """Test that the Sankey function exists."""
    print("🧪 Testing Sankey function existence...")
    
    try:
        import plotting
        if hasattr(plotting, 'plot_interactive_sankey'):
            print("✅ plot_interactive_sankey function found")
            return True
        else:
            print("❌ plot_interactive_sankey function not found")
            return False
    except Exception as e:
        print(f"❌ Error checking Sankey function: {e}")
        return False

def test_sankey_basic_functionality():
    """Test basic Sankey functionality."""
    print("🧪 Testing basic Sankey functionality...")
    
    try:
        import plotting
        
        # Create test data
        mock_system = create_test_mfa_system()
        
        with patch('plotting.display') as mock_display, patch('plotting.interact') as mock_interact:
            plotting.plot_interactive_sankey(mock_system)
            
            # Should display controls and figure (2 calls)
            assert mock_display.call_count == 2
            mock_interact.assert_called_once()
            
            print("✅ Basic Sankey functionality test passed")
            return True
    except Exception as e:
        print(f"❌ Basic Sankey functionality test failed: {e}")
        return False

def test_sankey_with_dsm_fomp():
    """Test Sankey with DSM/FOMP parameters."""
    print("🧪 Testing Sankey with DSM/FOMP parameters...")
    
    try:
        import plotting
        
        # Create test data
        mock_system = create_test_mfa_system()
        dsm_params = {1: {"lifetime": 10}}
        fomp_params = {2: {"k_min": 0.025}}
        
        with patch('plotting.display') as mock_display, patch('plotting.interact') as mock_interact:
            plotting.plot_interactive_sankey(mock_system, dsm_params, fomp_params)
            
            # Should display controls and figure (2 calls)
            assert mock_display.call_count == 2
            mock_interact.assert_called_once()
            
            print("✅ Sankey with DSM/FOMP test passed")
            return True
            
    except Exception as e:
        print(f"❌ Sankey with DSM/FOMP test failed: {e}")
        return False

def test_sankey_export_functionality():
    """Test Sankey export functionality."""
    print("🧪 Testing Sankey export functionality...")
    
    try:
        import plotting
        
        # Create test data
        mock_system = create_test_mfa_system()
        
        # Test with mocked interact, display, and os functions
        with patch('plotting.interact') as mock_interact, \
             patch('plotting.display') as mock_display, \
             patch('plotting.os.makedirs') as mock_makedirs, \
             patch('plotting.datetime') as mock_datetime:
            
            # Mock datetime
            mock_datetime.now.return_value.strftime.return_value = "20250101_120000"
            
            plotting.plot_interactive_sankey(mock_system)
            
            # Should display controls and figure (2 calls)
            assert mock_display.call_count == 2
            mock_interact.assert_called_once()
            
            print("✅ Sankey export functionality test passed")
            return True
            
    except Exception as e:
        print(f"❌ Sankey export functionality test failed: {e}")
        return False

def main():
    """Run all Sankey tests."""
    print("🧪" + "="*50)
    print("🧪 SANKEY DIAGRAM FUNCTIONALITY TESTS")
    print("🧪" + "="*50)
    
    tests = [
        ("Module Import", test_sankey_import),
        ("Function Existence", test_sankey_function_exists),
        ("Basic Functionality", test_sankey_basic_functionality),
        ("DSM/FOMP Integration", test_sankey_with_dsm_fomp),
        ("Export Functionality", test_sankey_export_functionality)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Print results
    print("\n" + "="*50)
    print("📊 TEST RESULTS")
    print("="*50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    print(f"\n📈 Summary:")
    print(f"   Total tests: {total}")
    print(f"   Passed: {passed}")
    print(f"   Failed: {total - passed}")
    print(f"   Success rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n🎉 All Sankey tests passed!")
        return True
    else:
        print("\n⚠️ Some Sankey tests failed!")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1) 