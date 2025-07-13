#!/usr/bin/env python3
"""
Debug script to test Sankey export functionality.
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

def create_mock_system():
    """Create a mock MFA system for testing."""
    mock_system = Mock()
    
    # Mock processes
    mock_process1 = Mock()
    mock_process1.ID = 1
    mock_process1.Name = "Process 1"
    
    mock_process2 = Mock()
    mock_process2.ID = 2
    mock_process2.Name = "Process 2"
    
    mock_system.ProcessList = [mock_process1, mock_process2]
    
    # Mock flows
    mock_flow = Mock()
    mock_flow.P_Start = 1
    mock_flow.P_End = 2
    mock_flow.Values = np.array([[10.0, 5.0, 2.0, 1.0], [12.0, 6.0, 2.5, 1.2]])
    mock_flow.Name = "Flow_1_2"
    
    mock_system.FlowDict = {"Flow_1_2": mock_flow}
    
    # Mock time and elements
    mock_system.IndexTable = Mock()
    mock_system.IndexTable.Classification = {"Time": Mock()}
    mock_system.IndexTable.Classification["Time"].Items = [2020, 2021]
    mock_system.Elements = ["material", "WC", "DM", "CC"]
    
    return mock_system

def test_sankey_export():
    """Test the Sankey export functionality."""
    print("🧪 Testing Sankey export functionality...")
    
    try:
        import plotting
        
        # Create mock system
        mock_system = create_mock_system()
        
        # Test the Sankey function
        print("📊 Creating Sankey diagram...")
        plotting.plot_interactive_sankey(mock_system)
        
        print("✅ Sankey function called successfully")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sankey_export() 