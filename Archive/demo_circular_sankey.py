#!/usr/bin/env python3
"""
Demo: Enhanced Sankey Diagrams for Circular Systems

This script demonstrates the configuration files and shows how to use
the enhanced Sankey functionality in your BioDYM notebook.
"""

import pandas as pd
import os

def demo_circular_sankey():
    """Demonstrate the circular Sankey functionality."""
    
    print("🎯 Enhanced Sankey Diagrams for Circular Systems - Demo")
    print("=" * 60)
    
    # 1. Show the configuration files we created
    print("\n📊 Configuration Files Created:")
    config_files = [
        "data/01_input/BioDYM_Visualization_Config.xlsx",
        "data/01_input/Circular_Test_Config.xlsx",
        "data/01_input/My_Circular_Config.xlsx"
    ]
    
    for file_path in config_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} (not found)")
    
    # 2. Show the structure of the configuration
    print("\n📋 Configuration Structure:")
    print("""
    📊 Process_Visualization Sheet:
    - Process_ID: Must match your MFA system process IDs
    - Process_Name: Human-readable process name
    - Node_Color: Hex color code (e.g., #FF6B6B)
    - Node_Size: Small, Medium, Large, XLarge
    - X_Position, Y_Position: Manual positioning (0.0 to 1.0)
    - Layout_Type: Auto, Fixed, Circular, Radial
    
    📊 Flow_Visualization Sheet:
    - Flow_ID: Must match your MFA system flow IDs
    - Flow_Name: Human-readable flow name
    - Flow_Color: Hex color code
    - Flow_Opacity: Transparency (0.0 to 1.0)
    - Flow_Width_Multiplier: Width relative to flow value
    - Flow_Style: Solid, Dashed, Dotted
    
    📊 Layout_Configuration Sheet:
    - Default_Layout_Type: Linear, Circular, Radial, Custom
    - Circular_Center_X, Circular_Center_Y: Center position
    - Circular_Radius: Size of the circle
    - Flow_Curvature: How curved the flows are
    """)
    
    # 3. Show how to use in your notebook
    print("\n🚀 How to Use in Your BioDYM Notebook:")
    print("""
    # Step 1: Import the enhanced Sankey functionality
    from plotting import plot_circular_sankey
    
    # Step 2: Plot circular Sankey diagram
    plot_circular_sankey(
        mfa_system_results=mfa_results_baseline,
        dsm_params=dsm_params,
        fomp_params=fomp_params,
        config_file="data/01_input/My_Circular_Config.xlsx"  # Optional
    )
    """)
    
    # 4. Show the key features
    print("\n🎨 Key Features for Circular Systems:")
    print("""
    🔄 Circular Layout Features:
    - Automatic detection of circular flows
    - Processes with recycling flows positioned in a circle
    - Non-circular processes use linear layout
    - Curved flow lines show circular connections
    
    🎨 Visual Customization:
    - Different colors for forward vs. recycling flows
    - Different line styles (solid, dashed, dotted)
    - Custom node sizes and colors
    - Adjustable flow opacity and width
    
    📐 Layout Options:
    - Circular: Best for recycling systems
    - Radial: All processes in a circle
    - Linear: Traditional left-to-right
    - Custom: Manual positioning
    """)
    
    # 5. Show example configuration
    print("\n📝 Example Configuration for Circular System:")
    print("""
    Process_Visualization:
    Process_ID | Process_Name | Node_Color | Layout_Type
    P_01      | Input        | #FF6B6B    | Fixed
    P_02      | Processing   | #4ECDC4    | Circular
    P_03      | Recycling    | #96CEB4    | Circular
    P_04      | Output       | #FFEAA7    | Fixed
    
    Flow_Visualization:
    Flow_ID | Flow_Name              | Flow_Color | Flow_Style
    F_01_02 | Input to Processing    | #FF6B6B    | Solid
    F_02_03 | Processing to Recycling| #4ECDC4    | Solid
    F_03_02 | Recycling to Processing| #96CEB4    | Dashed
    F_02_04 | Processing to Output   | #FFEAA7    | Solid
    """)
    
    # 6. Show troubleshooting tips
    print("\n🔧 Troubleshooting Tips:")
    print("""
    Common Issues:
    1. Processes not showing in circle:
       - Check that Layout_Type='Circular' is set
       - Verify Process_ID matches your system exactly
    
    2. Flows not curved:
       - Increase Flow_Curvature value
       - Check that flows are properly configured
    
    3. Colors not applied:
       - Verify Process_ID and Flow_ID match your system
       - Check that configuration file is loaded correctly
    
    4. Layout too crowded:
       - Decrease Circular_Radius
       - Increase Node_Spacing
    """)
    
    print("\n✅ Demo completed!")
    print("\n🎯 Next Steps:")
    print("   1. Open your BioDYM Scientific Notebook")
    print("   2. Add the plotting code shown above")
    print("   3. Edit the configuration file to match your system")
    print("   4. Run the analysis and visualize your circular system!")

if __name__ == "__main__":
    demo_circular_sankey()
