#!/usr/bin/env python3
"""
Interactive Sankey Test Script

This script tests the enhanced Sankey function in an interactive environment.
Run this in Jupyter or VS Code interactive window to see the real interactive plots.
"""

import os
import sys
import numpy as np
from unittest.mock import Mock

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
    """Create a test MFA system for interactive Sankey testing."""
    mock_system = Mock()
    
    # Set up classification
    mock_system.IndexTable.Classification = {"Time": Mock()}
    mock_system.IndexTable.Classification["Time"].Items = [2020, 2021, 2022, 2023, 2024]
    mock_system.Elements = ["material", "WC", "DM", "CC"]
    
    # Create realistic processes
    mock_system.ProcessList = [
        Mock(Name="Environment", ID=0),
        Mock(Name="Production", ID=1),
        Mock(Name="Consumption", ID=2),
        Mock(Name="Recycling", ID=3),
        Mock(Name="Waste Management", ID=4)
    ]
    
    # Create realistic flows
    np.random.seed(42)
    mock_system.FlowDict = {
        "F_0_1": Mock(
            P_Start=0, P_End=1,
            Values=np.array([
                [1000, 100, 50, 20],
                [1100, 110, 55, 22],
                [1200, 120, 60, 24],
                [1300, 130, 65, 26],
                [1400, 140, 70, 28]
            ])
        ),
        "F_1_2": Mock(
            P_Start=1, P_End=2,
            Values=np.array([
                [900, 90, 45, 18],
                [990, 99, 49.5, 19.8],
                [1080, 108, 54, 21.6],
                [1170, 117, 58.5, 23.4],
                [1260, 126, 63, 25.2]
            ])
        ),
        "F_2_3": Mock(
            P_Start=2, P_End=3,
            Values=np.array([
                [800, 80, 40, 16],
                [880, 88, 44, 17.6],
                [960, 96, 48, 19.2],
                [1040, 104, 52, 20.8],
                [1120, 112, 56, 22.4]
            ])
        ),
        "F_3_4": Mock(
            P_Start=3, P_End=4,
            Values=np.array([
                [700, 70, 35, 14],
                [770, 77, 38.5, 15.4],
                [840, 84, 42, 16.8],
                [910, 91, 45.5, 18.2],
                [980, 98, 49, 19.6]
            ])
        ),
        "F_4_0": Mock(
            P_Start=4, P_End=0,
            Values=np.array([
                [600, 60, 30, 12],
                [660, 66, 33, 13.2],
                [720, 72, 36, 14.4],
                [780, 78, 39, 15.6],
                [840, 84, 42, 16.8]
            ])
        )
    }
    
    return mock_system

def test_interactive_sankey():
    """Test the interactive Sankey function."""
    print("🎯" + "="*60)
    print("🎯 INTERACTIVE SANKEY TEST")
    print("🎯" + "="*60)
    
    try:
        import plotting
        print("✅ Plotting module imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import plotting module: {e}")
        return
    
    # Create test data
    print("\n📊 Creating test MFA system...")
    test_mfa_system = create_test_mfa_system()
    
    # DSM and FOMP parameters for testing
    dsm_params = {1: {"lifetime": 10, "categories": ["new", "old"]}}
    fomp_params = {2: {"k_min": 0.025, "k_max": 0.075}}
    
    print("✅ Test data created successfully")
    
    print("\n🔗 Testing Enhanced Interactive Sankey...")
    print("Features to test:")
    print("  • Year slider (2020-2024)")
    print("  • Element dropdown (material, WC, DM, CC)")
    print("  • Flow representation toggle (Absolute/Percentages)")
    print("  • Process selection (multi-select)")
    print("  • Flow threshold slider")
    print("  • Export button")
    print("  • Color coding (Regular=blue, DSM=orange, FOMP=green)")
    
    try:
        # This should display the interactive Sankey diagram
        plotting.plot_interactive_sankey(test_mfa_system, dsm_params, fomp_params)
        print("\n✅ Interactive Sankey test completed!")
        print("📊 You should see:")
        print("  • Interactive Sankey diagram with controls")
        print("  • Color-coded processes and flows")
        print("  • Export button")
        print("  • All interactive widgets working")
        
    except Exception as e:
        print(f"\n❌ Interactive Sankey test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_interactive_sankey() 