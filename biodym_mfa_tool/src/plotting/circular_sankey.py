# -*- coding: utf-8 -*-
"""
Circular Sankey Diagram Integration Module.

This module provides easy integration of enhanced Sankey diagrams
with circular system support into the BioDYM notebook.
"""

from .enhanced_sankey import plot_enhanced_sankey, load_visualization_config
import os

def plot_circular_sankey(mfa_system_results, dsm_params=None, fomp_params=None, 
                        config_file=None):
    """
    Plot a Sankey diagram optimized for circular/recycling systems.
    
    This function automatically detects circular flows and applies
    appropriate circular layout and styling.
    
    Args:
        mfa_system_results (odym.MFAsystem): The solved MFA system object
        dsm_params (dict, optional): DSM parameters to identify DSM processes
        fomp_params (dict, optional): FOMP parameters to identify FOMP processes
        config_file (str, optional): Path to visualization config Excel file
                                   If None, uses default config
    """
    
    # Default config file path - use the main Excel file
    if config_file is None:
        config_file = "data/01_input/250909_CS1_Wheat_Straw.xlsx"
    
    # Check if config file exists
    if not os.path.exists(config_file):
        print(f"⚠️ Visualization config file not found: {config_file}")
        print("Using default configuration for circular systems")
        config_file = None
    
    # Plot the enhanced Sankey diagram
    return plot_enhanced_sankey(
        mfa_system_results=mfa_system_results,
        dsm_params=dsm_params,
        fomp_params=fomp_params,
        visualization_config_path=config_file
    )

def create_circular_config_template(output_path="data/01_input/Circular_System_Config.xlsx"):
    """
    Create a specialized configuration template for circular systems.
    
    Args:
        output_path (str): Path where to save the configuration file
    """
    from .enhanced_sankey import get_default_visualization_config
    import pandas as pd
    
    # Load default config
    config = get_default_visualization_config()
    
    # Modify for circular systems
    config['layout']['Default_Layout_Type'] = 'Circular'
    config['layout']['Flow_Curvature'] = '0.8'  # More curved for circular flows
    config['layout']['Circular_Radius'] = '0.35'  # Larger radius for better visibility
    
    # Create Excel file
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # Process visualization with circular examples
        process_data = [
            ["Process_ID", "Process_Name", "Node_Color", "Node_Size", "X_Position", "Y_Position", "Layout_Type", "Description"],
            ["P_01", "Input", "#FF6B6B", "Large", "0.1", "0.5", "Fixed", "System input"],
            ["P_02", "Processing", "#4ECDC4", "Medium", "0.5", "0.5", "Circular", "Main processing (circular)"],
            ["P_03", "Recycling", "#96CEB4", "Medium", "0.5", "0.5", "Circular", "Recycling process (circular)"],
            ["P_04", "Output", "#FFEAA7", "Large", "0.9", "0.5", "Fixed", "System output"],
        ]
        
        process_df = pd.DataFrame(process_data[1:], columns=process_data[0])
        process_df.to_excel(writer, sheet_name='Process_Visualization', index=False)
        
        # Flow visualization with circular flow examples
        flow_data = [
            ["Flow_ID", "Flow_Name", "Flow_Color", "Flow_Opacity", "Flow_Width_Multiplier", "Flow_Style", "Description"],
            ["F_01_02", "Input to Processing", "#FF6B6B", "0.8", "1.0", "Solid", "Forward flow"],
            ["F_02_03", "Processing to Recycling", "#4ECDC4", "0.8", "1.0", "Solid", "Forward flow"],
            ["F_03_02", "Recycling to Processing", "#96CEB4", "0.6", "0.8", "Dashed", "Recycling flow (circular)"],
            ["F_02_04", "Processing to Output", "#FFEAA7", "0.8", "1.0", "Solid", "Forward flow"],
        ]
        
        flow_df = pd.DataFrame(flow_data[1:], columns=flow_data[0])
        flow_df.to_excel(writer, sheet_name='Flow_Visualization', index=False)
        
        # Layout configuration optimized for circular systems
        layout_data = [
            ["Setting", "Value", "Description"],
            ["Default_Layout_Type", "Circular", "Use circular layout for recycling systems"],
            ["Circular_Center_X", "0.5", "Center X position"],
            ["Circular_Center_Y", "0.5", "Center Y position"],
            ["Circular_Radius", "0.35", "Radius for circular layout"],
            ["Flow_Curvature", "0.8", "High curvature for circular flows"],
            ["Show_Flow_Labels", "True", "Show flow values"],
            ["Show_Node_Labels", "True", "Show process names"],
        ]
        
        layout_df = pd.DataFrame(layout_data[1:], columns=layout_data[0])
        layout_df.to_excel(writer, sheet_name='Layout_Configuration', index=False)
    
    print(f"✅ Circular system configuration template created: {output_path}")
    print("🎯 This template is optimized for circular/recycling systems")
    print("📝 Edit the Process_ID and Flow_ID values to match your system")

# Convenience function for easy import
def plot_sankey_circular(*args, **kwargs):
    """Alias for plot_circular_sankey for backward compatibility."""
    return plot_circular_sankey(*args, **kwargs)
