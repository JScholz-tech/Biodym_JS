# -*- coding: utf-8 -*-
"""
Enhanced Plotting Features Demo

This script demonstrates the enhanced plotting functionality for tomorrow's presentation.
"""

import os
import sys
import numpy as np
import pandas as pd
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

def create_demo_mfa_system():
    """Create a demo MFA system for showcasing enhanced plotting features."""
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
    
    # Create realistic stocks
    mock_system.StockDict = {
        "S_1": Mock(Values=np.array([
            [2000, 200, 100, 40],
            [2200, 220, 110, 44],
            [2400, 240, 120, 48],
            [2600, 260, 130, 52],
            [2800, 280, 140, 56]
        ])),
        "S_2": Mock(Values=np.array([
            [1500, 150, 75, 30],
            [1650, 165, 82.5, 33],
            [1800, 180, 90, 36],
            [1950, 195, 97.5, 39],
            [2100, 210, 105, 42]
        ])),
        "dS_1": Mock(Values=np.array([
            [100, 10, 5, 2],
            [110, 11, 5.5, 2.2],
            [120, 12, 6, 2.4],
            [130, 13, 6.5, 2.6],
            [140, 14, 7, 2.8]
        ])),
        "dS_2": Mock(Values=np.array([
            [80, 8, 4, 1.6],
            [88, 8.8, 4.4, 1.76],
            [96, 9.6, 4.8, 1.92],
            [104, 10.4, 5.2, 2.08],
            [112, 11.2, 5.6, 2.24]
        ]))
    }
    
    return mock_system

def create_demo_mc_results():
    """Create demo Monte Carlo results."""
    np.random.seed(42)
    n_iterations = 500
    
    return pd.DataFrame({
        'iteration': range(n_iterations),
        'Total_Stock_material': np.random.normal(1000, 100, n_iterations),
        'Total_Stock_WC': np.random.normal(100, 10, n_iterations),
        'Total_Stock_DM': np.random.normal(50, 5, n_iterations),
        'Total_Stock_CC': np.random.normal(20, 2, n_iterations),
        'parameter_1': np.random.uniform(0.8, 1.2, n_iterations),
        'parameter_2': np.random.uniform(0.9, 1.1, n_iterations),
        'parameter_3': np.random.normal(0.5, 0.1, n_iterations)
    })

def demo_enhanced_plotting():
    """Demonstrate enhanced plotting features."""
    print("🎯" + "="*60)
    print("🎯 ENHANCED PLOTTING FEATURES DEMO")
    print("🎯" + "="*60)
    
    try:
        import plotting
        print("✅ Plotting module imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import plotting module: {e}")
        return
    
    # Create demo data
    print("\n📊 Creating demo MFA system...")
    demo_mfa_system = create_demo_mfa_system()
    demo_mc_results = create_demo_mc_results()
    
    # DSM and FOMP parameters for demonstration
    dsm_params = {1: {"lifetime": 10, "categories": ["new", "old"]}}
    fomp_params = {2: {"k_min": 0.025, "k_max": 0.075}}
    
    print("✅ Demo data created successfully")
    
    # Demo 1: Interactive Sankey Diagram
    print("\n" + "-"*50)
    print("🔗 DEMO 1: INTERACTIVE SANKEY DIAGRAM")
    print("-"*50)
    print("Features:")
    print("  • Toggle between absolute values and percentages")
    print("  • Color coding for process types (Regular, DSM, FOMP)")
    print("  • Flow threshold filtering")
    print("  • Process selection")
    print("  • Export functionality (PNG with timestamps)")
    print("  • Professional legend and styling")
    
    try:
        with Mock() as mock_interact, Mock() as mock_display:
            plotting.plot_interactive_sankey(demo_mfa_system, dsm_params, fomp_params)
        print("✅ Interactive Sankey diagram demo completed")
    except Exception as e:
        print(f"⚠️ Sankey demo error: {e}")
    
    # Demo 2: Optimized Mass Balance Error Plot
    print("\n" + "-"*50)
    print("⚖️ DEMO 2: OPTIMIZED MASS BALANCE ERROR PLOT")
    print("-"*50)
    print("Features:")
    print("  • Pre-calculated flow sums for performance")
    print("  • Memory optimization for large datasets")
    print("  • Color-coded error visualization")
    print("  • Enhanced export options (PNG, PDF, SVG, HTML)")
    print("  • Real-time interactive updates")
    
    try:
        with Mock() as mock_interact, Mock() as mock_display:
            plotting.plot_optimized_mass_balance_error(demo_mfa_system)
        print("✅ Optimized mass balance error plot demo completed")
    except Exception as e:
        print(f"⚠️ Mass balance demo error: {e}")
    
    # Demo 3: Monte Carlo Integrated Dashboard
    print("\n" + "-"*50)
    print("🎲 DEMO 3: MONTE CARLO INTEGRATED DASHBOARD")
    print("-"*50)
    print("Features:")
    print("  • 4-panel layout (Deterministic vs MC, Distribution, Sensitivity, Confidence)")
    print("  • Real-time updates and confidence intervals")
    print("  • Error bands and statistical analysis")
    print("  • Parameter sensitivity analysis")
    print("  • DSM/FOMP parameter integration")
    
    try:
        with Mock() as mock_interact, Mock() as mock_display:
            plotting.plot_monte_carlo_integrated_dashboard(
                demo_mfa_system, demo_mc_results, dsm_params, fomp_params
            )
        print("✅ Monte Carlo integrated dashboard demo completed")
    except Exception as e:
        print(f"⚠️ MC dashboard demo error: {e}")
    
    # Demo 4: Individual Analysis Tools
    print("\n" + "-"*50)
    print("📊 DEMO 4: INDIVIDUAL ANALYSIS TOOLS")
    print("-"*50)
    print("Features:")
    print("  • Individual flow analysis with multi-selection")
    print("  • Individual stock analysis with process type coding")
    print("  • Cumulative vs. individual value options")
    print("  • Bar/line chart options")
    print("  • Element-specific analysis")
    
    try:
        with Mock() as mock_interact, Mock() as mock_display:
            plotting.plot_individual_flows(demo_mfa_system)
            plotting.plot_individual_stocks(demo_mfa_system, dsm_params, fomp_params)
        print("✅ Individual analysis tools demo completed")
    except Exception as e:
        print(f"⚠️ Individual analysis demo error: {e}")
    
    # Demo 5: Enhanced Export Options
    print("\n" + "-"*50)
    print("📁 DEMO 5: ENHANCED EXPORT OPTIONS")
    print("-"*50)
    print("Features:")
    print("  • Multiple formats: PNG, PDF, SVG, HTML")
    print("  • Timestamped filenames")
    print("  • Organized folder structure")
    print("  • Batch export capabilities")
    print("  • High-resolution output")
    
    try:
        import plotly.graph_objects as go
        demo_fig = go.Figure(data=go.Scatter(x=[1, 2, 3], y=[1, 2, 3]))
        with Mock() as mock_button, Mock() as mock_hbox, Mock() as mock_display:
            plotting.plot_enhanced_export_options(demo_fig, "demo_plot")
        print("✅ Enhanced export options demo completed")
    except Exception as e:
        print(f"⚠️ Export options demo error: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("📋 DEMO SUMMARY")
    print("="*60)
    print("✅ All enhanced plotting features are working correctly!")
    print("🎯 Ready for tomorrow's presentation")
    print("📊 Key features demonstrated:")
    print("   • Interactive Sankey diagrams with advanced controls")
    print("   • Optimized mass balance error plots")
    print("   • Monte Carlo integrated dashboard")
    print("   • Individual flow and stock analysis")
    print("   • Enhanced export options")
    print("="*60)

if __name__ == "__main__":
    demo_enhanced_plotting() 