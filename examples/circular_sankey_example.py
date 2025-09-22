#!/usr/bin/env python3
"""
Example: Using Enhanced Sankey Diagrams for Circular Systems

This example shows how to use the enhanced Sankey diagram functionality
for visualizing circular/recycling material flow systems.
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from plotting.circular_sankey import plot_circular_sankey, create_circular_config_template

def example_circular_sankey():
    """
    Example of how to use circular Sankey diagrams in your notebook.
    """
    
    print("🎯 Enhanced Sankey Diagram Example for Circular Systems")
    print("=" * 60)
    
    # Step 1: Create a circular system configuration template
    print("\n1. Creating circular system configuration template...")
    create_circular_config_template("data/01_input/My_Circular_Config.xlsx")
    
    # Step 2: Show how to use in your notebook
    print("\n2. Integration example for your notebook:")
    print("""
    # In your BioDYM Scientific Notebook, add this cell:
    
    # Import the enhanced Sankey functionality
    from plotting.circular_sankey import plot_circular_sankey
    
    # Plot circular Sankey diagram (replace with your actual data)
    if 'mfa_results_baseline' in locals():
        # Use your existing MFA results
        plot_circular_sankey(
            mfa_system_results=mfa_results_baseline,
            dsm_params=dsm_params,
            fomp_params=fomp_params,
            config_file="data/01_input/My_Circular_Config.xlsx"  # Optional: use custom config
        )
    else:
        print("⚠️ MFA results not available. Run the analysis first.")
    """)
    
    # Step 3: Show configuration options
    print("\n3. Configuration options for circular systems:")
    print("""
    📊 Process_Visualization Sheet:
    - Process_ID: Must match your MFA system process IDs
    - Layout_Type: Use 'Circular' for recycling processes
    - Node_Color: Custom colors for each process
    - X_Position, Y_Position: Manual positioning (optional)
    
    📊 Flow_Visualization Sheet:
    - Flow_ID: Must match your MFA system flow IDs  
    - Flow_Style: Use 'Dashed' for recycling flows
    - Flow_Color: Different colors for forward vs. recycling flows
    - Flow_Opacity: Lower opacity for recycling flows
    
    📊 Layout_Configuration Sheet:
    - Default_Layout_Type: 'Circular' for circular systems
    - Circular_Radius: Adjust the size of the circle
    - Flow_Curvature: Higher values for more curved flows
    """)
    
    # Step 4: Show advanced features
    print("\n4. Advanced features for circular systems:")
    print("""
    🔄 Circular Layout Features:
    - Automatic detection of circular flows
    - Processes with recycling flows are positioned in a circle
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
    
    print("\n✅ Example complete! Check the generated configuration file:")
    print("   data/01_input/My_Circular_Config.xlsx")
    print("\n🎯 Next steps:")
    print("   1. Edit the configuration file to match your system")
    print("   2. Add the plotting code to your notebook")
    print("   3. Run the analysis and visualize your circular system!")

if __name__ == "__main__":
    example_circular_sankey()
