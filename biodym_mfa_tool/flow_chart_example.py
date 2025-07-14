#!/usr/bin/env python3
"""
Flow Chart Example for BioDYM MFA Tool

This script demonstrates how to create flow charts from process and flow data
using the BioDYM framework.

Usage:
    python flow_chart_example.py
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Add BioDYM modules to path
src_path = os.path.join(os.getcwd(), 'src')
sys.path.insert(0, src_path)

# Add ODYM framework to path
biodym_mfa_tool_dir = os.getcwd()
odym_path = os.path.join(
    biodym_mfa_tool_dir, "framework", "ODYM-master_20241127", "odym", "modules"
)
sys.path.insert(0, odym_path)

# Add bioDYM add-on to path
biodym_addon_path = os.path.join(
    biodym_mfa_tool_dir, "framework", "bioDYM_add-on", "modules"
)
sys.path.insert(0, biodym_addon_path)

# Import required modules
try:
    import config
    import data_loader
    import system_setup
    import utils
    from engine import solver
    import plotting
    import ODYM_Classes as msc
    print("✅ BioDYM modules imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    raise


def create_flow_charts_from_excel(input_file):
    """
    Creates flow charts from an Excel input file.
    
    Args:
        input_file (str): Path to the Excel input file
    """
    print(f"\n📊 Creating flow charts from: {input_file}")
    
    # 1. Setup model scope
    print("📋 Setting up model scope...")
    start_year, end_year = 2020, 2030
    elements = ['material', 'WC', 'DM', 'CC']
    
    model_classification, index_table = system_setup.define_model_scope(
        start_year, end_year, elements
    )
    
    # 2. Initialize MFA system
    print("🔧 Initializing MFA system...")
    mfa_system_base = system_setup.initialize_mfa_system(
        model_classification, index_table
    )
    
    # 3. Load and define processes
    print("📊 Loading processes and data...")
    mfa_system_base, all_excel_data = system_setup.load_and_define_processes(
        mfa_system_base, input_file, data_loader
    )
    
    # 4. Load parameters
    print("⚙️ Loading parameters...")
    dsm_params = data_loader.load_dsm_parameters(all_excel_data)
    fomp_params = data_loader.load_fomp_parameters(all_excel_data)
    uncertainty_params = data_loader.load_uncertainty_definitions(all_excel_data)
    
    # 5. Define flows and parameters
    print("🔗 Defining flows and parameters...")
    mfa_system_configured, _ = system_setup.define_flows_and_parameters(
        mfa_system_base, all_excel_data
    )
    
    # 6. Run calculation
    print("🧮 Running calculation...")
    mfa_system_with_results, dsm_details = solver.run_mfa_calculation(
        mfa_system_configured, dsm_params, fomp_params, config
    )
    
    print("✅ Calculation completed successfully!")
    
    # 7. Create flow charts
    print("\n🎨 Creating flow charts...")
    
    # Basic flow chart
    print("📊 Creating basic flow chart...")
    fig1, G1 = plotting.plot_flow_chart(
        mfa_system_with_results, 
        title="BioDYM System Flow Chart",
        layout_type="hierarchical"
    )
    
    # Interactive flow chart
    print("📊 Creating interactive flow chart...")
    fig2, G2 = plotting.plot_interactive_flow_chart(
        mfa_system_with_results,
        title="Interactive BioDYM System Flow Chart"
    )
    
    # System architecture diagram
    print("📊 Creating system architecture diagram...")
    fig3 = plotting.plot_system_architecture_diagram(
        mfa_system_with_results,
        title="BioDYM System Architecture"
    )
    
    print("\n✅ All flow charts created successfully!")
    
    # Print system statistics
    print(f"\n📈 System Statistics:")
    print(f"   • Processes: {len(mfa_system_with_results.ProcessList)}")
    print(f"   • Flows: {len(mfa_system_with_results.FlowDict)}")
    print(f"   • Stocks: {len(mfa_system_with_results.StockDict)}")
    
    return mfa_system_with_results


def create_simple_flow_chart():
    """
    Creates a simple flow chart with example data for demonstration.
    """
    print("\n🎨 Creating simple flow chart example...")
    
    # Create a simple MFA system for demonstration
    import ODYM_Classes as msc
    
    # Create processes
    processes = [
        msc.Process(Name="Input Source", ID=0),
        msc.Process(Name="Treatment Plant", ID=1),
        msc.Process(Name="Use Phase", ID=2),
        msc.Process(Name="Output Sink", ID=3)
    ]
    
    # Create flows
    flows = {
        "F_00_01": msc.Flow(Name="F_00_01", P_Start=0, P_End=1, Indices="t,e"),
        "F_01_02": msc.Flow(Name="F_01_02", P_Start=1, P_End=2, Indices="t,e"),
        "F_02_03": msc.Flow(Name="F_02_03", P_Start=2, P_End=3, Indices="t,e")
    }
    
    # Set flow values
    for flow in flows.values():
        flow.Values = np.array([[100.0], [110.0], [120.0]])  # 3 years, material dimension
    
    # Create a mock MFA system object
    class MockMFASystem:
        def __init__(self, processes, flows):
            self.ProcessList = processes
            self.FlowDict = flows
            self.IndexTable = None  # Not needed for flow chart
    
    mock_system = MockMFASystem(processes, flows)
    
    # Create flow chart
    fig, G = plotting.plot_flow_chart(
        mock_system,
        title="Simple Flow Chart Example",
        layout_type="hierarchical"
    )
    
    print("✅ Simple flow chart created!")
    return mock_system


def main():
    """
    Main function to demonstrate flow chart creation.
    """
    print("🎨 BioDYM Flow Chart Example")
    print("=" * 50)
    
    # Check if input file exists
    input_file = "data/01_input/250714_Template_CS1.xlsx"
    
    if os.path.exists(input_file):
        print(f"📁 Found input file: {input_file}")
        
        try:
            # Create flow charts from Excel data
            mfa_system = create_flow_charts_from_excel(input_file)
            print("\n✅ Flow charts created from Excel data!")
            
        except Exception as e:
            print(f"❌ Error creating flow charts from Excel: {e}")
            print("🔄 Falling back to simple example...")
            
            # Create simple flow chart as fallback
            create_simple_flow_chart()
    
    else:
        print(f"⚠️ Input file not found: {input_file}")
        print("🔄 Creating simple flow chart example...")
        
        # Create simple flow chart
        create_simple_flow_chart()
    
    print("\n🎉 Flow chart demonstration completed!")
    print("\n📝 Usage Notes:")
    print("   • Basic flow chart: Shows processes and flows with values")
    print("   • Interactive flow chart: Allows filtering and exploration")
    print("   • System architecture: Shows hierarchical process structure")
    print("   • All charts support export and customization")


if __name__ == "__main__":
    main() 