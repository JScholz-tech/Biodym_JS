#!/usr/bin/env python3
"""
BioDYM Visualization Configuration Generator

This script creates a comprehensive Excel visualization configuration file
for customizing Sankey diagrams, especially for circular systems.
"""

import pandas as pd
import os
from datetime import datetime

def create_visualization_config_excel(output_path="data/01_input/BioDYM_Visualization_Config.xlsx"):
    """
    Creates a comprehensive Excel visualization configuration file for BioDYM MFA Tool.
    
    Args:
        output_path (str): Path where to save the Excel file
    """
    
    # Create the Excel file with multiple sheets
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        
        # Sheet 1: Process Colors and Positioning
        process_config = [
            ["Process_ID", "Process_Name", "Node_Color", "Node_Size", "X_Position", "Y_Position", "Layout_Type", "Description"],
            ["P_01", "Input Process", "#FF6B6B", "Large", "0.1", "0.5", "Fixed", "Primary system input"],
            ["P_02", "Processing 1", "#4ECDC4", "Medium", "0.3", "0.3", "Auto", "First processing step"],
            ["P_03", "Processing 2", "#45B7D1", "Medium", "0.3", "0.7", "Auto", "Second processing step"],
            ["P_04", "Circular Process", "#96CEB4", "Large", "0.5", "0.5", "Circular", "Circular/recycling process"],
            ["P_05", "Output Process", "#FFEAA7", "Medium", "0.9", "0.5", "Fixed", "Final system output"],
            ["", "", "", "", "", "", "", ""],
            ["# Instructions:", "", "", "", "", "", "", ""],
            ["# Node_Color: Hex color codes (e.g., #FF6B6B)", "", "", "", "", "", "", ""],
            ["# Node_Size: Small, Medium, Large, XLarge", "", "", "", "", "", "", ""],
            ["# X_Position: 0.0 to 1.0 (left to right)", "", "", "", "", "", "", ""],
            ["# Y_Position: 0.0 to 1.0 (bottom to top)", "", "", "", "", "", "", ""],
            ["# Layout_Type: Auto, Fixed, Circular, Radial", "", "", "", "", "", "", ""],
        ]
        
        process_df = pd.DataFrame(process_config[1:], columns=process_config[0])
        process_df.to_excel(writer, sheet_name='Process_Visualization', index=False)
        
        # Sheet 2: Flow Colors and Styling
        flow_config = [
            ["Flow_ID", "Flow_Name", "Flow_Color", "Flow_Opacity", "Flow_Width_Multiplier", "Flow_Style", "Description"],
            ["F_01_02", "Input to Process 1", "#FF6B6B", "0.8", "1.0", "Solid", "Primary input flow"],
            ["F_02_03", "Process 1 to 2", "#4ECDC4", "0.8", "1.0", "Solid", "Inter-process flow"],
            ["F_03_04", "Process 2 to Circular", "#45B7D1", "0.8", "1.0", "Solid", "To circular process"],
            ["F_04_02", "Circular to Process 1", "#96CEB4", "0.6", "0.8", "Dashed", "Recycling flow"],
            ["F_04_05", "Circular to Output", "#FFEAA7", "0.8", "1.0", "Solid", "Final output flow"],
            ["", "", "", "", "", "", ""],
            ["# Instructions:", "", "", "", "", "", ""],
            ["# Flow_Color: Hex color codes", "", "", "", "", "", ""],
            ["# Flow_Opacity: 0.0 to 1.0 (transparent to opaque)", "", "", "", "", "", ""],
            ["# Flow_Width_Multiplier: 0.1 to 3.0 (relative to flow value)", "", "", "", "", "", ""],
            ["# Flow_Style: Solid, Dashed, Dotted", "", "", "", "", "", ""],
        ]
        
        flow_df = pd.DataFrame(flow_config[1:], columns=flow_config[0])
        flow_df.to_excel(writer, sheet_name='Flow_Visualization', index=False)
        
        # Sheet 3: Layout Configuration
        layout_config = [
            ["Setting", "Value", "Description", "Options"],
            ["Default_Layout_Type", "Circular", "Default layout for circular systems", "Linear, Circular, Radial, Custom"],
            ["Circular_Center_X", "0.5", "Center X position for circular layout", "0.0 to 1.0"],
            ["Circular_Center_Y", "0.5", "Center Y position for circular layout", "0.0 to 1.0"],
            ["Circular_Radius", "0.3", "Radius for circular layout", "0.1 to 0.5"],
            ["Node_Spacing", "0.1", "Minimum spacing between nodes", "0.05 to 0.2"],
            ["Flow_Curvature", "0.5", "Curvature of flow lines (0=straight, 1=max curve)", "0.0 to 1.0"],
            ["Show_Flow_Labels", "True", "Show flow values on links", "True, False"],
            ["Show_Node_Labels", "True", "Show process names on nodes", "True, False"],
            ["Background_Color", "#FFFFFF", "Background color", "Hex color code"],
            ["Grid_Color", "#E0E0E0", "Grid color", "Hex color code"],
            ["", "", "", ""],
            ["# Circular Layout Options:", "", "", ""],
            ["# - Center position can be adjusted", "", "", ""],
            ["# - Radius controls the size of the circle", "", "", ""],
            ["# - Nodes are distributed evenly around the circle", "", "", ""],
            ["# - Flows follow curved paths between nodes", "", "", ""],
        ]
        
        layout_df = pd.DataFrame(layout_config[1:], columns=layout_config[0])
        layout_df.to_excel(writer, sheet_name='Layout_Configuration', index=False)
        
        # Sheet 4: Element Colors
        element_config = [
            ["Element", "Color", "Opacity", "Description"],
            ["material", "#1f77b4", "0.8", "Material flows"],
            ["WC", "#ff7f0e", "0.8", "Water content"],
            ["DM", "#2ca02c", "0.8", "Dry matter"],
            ["CC", "#d62728", "0.8", "Carbon content"],
            ["", "", "", ""],
            ["# Instructions:", "", "", ""],
            ["# Element colors are used for flow coloring", "", "", ""],
            ["# Opacity affects the transparency of flows", "", "", ""],
        ]
        
        element_df = pd.DataFrame(element_config[1:], columns=element_config[0])
        element_df.to_excel(writer, sheet_name='Element_Colors', index=False)
        
        # Sheet 5: Advanced Options
        advanced_config = [
            ["Setting", "Value", "Description", "Options"],
            ["Enable_Animation", "True", "Enable flow animations", "True, False"],
            ["Animation_Duration", "1000", "Animation duration in ms", "500 to 3000"],
            ["Enable_Zoom", "True", "Enable zoom and pan", "True, False"],
            ["Enable_Selection", "True", "Enable node/flow selection", "True, False"],
            ["Export_Resolution", "High", "Export resolution", "Low, Medium, High, Ultra"],
            ["Export_Format", "PNG", "Export format", "PNG, SVG, PDF"],
            ["Interactive_Mode", "Full", "Interactive features", "Basic, Full, Custom"],
            ["", "", "", ""],
            ["# Advanced Features:", "", "", ""],
            ["# - Animation makes flows more dynamic", "", "", ""],
            ["# - Zoom allows detailed inspection", "", "", ""],
            ["# - Selection enables interactive analysis", "", "", ""],
        ]
        
        advanced_df = pd.DataFrame(advanced_config[1:], columns=advanced_config[0])
        advanced_df.to_excel(writer, sheet_name='Advanced_Options', index=False)
        
        # Sheet 6: Documentation
        doc_config = [
            ["Section", "Description"],
            ["Overview", "This configuration file allows complete customization of Sankey diagrams"],
            ["", ""],
            ["Process_Visualization", "Configure individual process appearance and positioning"],
            ["- Process_ID: Must match your MFA system process IDs"],
            ["- Node_Color: Hex color codes for process nodes"],
            ["- Layout_Type: Auto (algorithmic), Fixed (manual), Circular (for circular systems)"],
            ["", ""],
            ["Flow_Visualization", "Configure flow appearance and styling"],
            ["- Flow_ID: Must match your MFA system flow IDs"],
            ["- Flow_Color: Hex color codes for flow lines"],
            ["- Flow_Style: Visual style of flow lines"],
            ["", ""],
            ["Layout_Configuration", "Global layout settings"],
            ["- Default_Layout_Type: Choose between Linear, Circular, Radial, or Custom"],
            ["- Circular settings: Configure circular layout parameters"],
            ["- Flow_Curvature: Control how curved the flow lines are"],
            ["", ""],
            ["Element_Colors", "Color scheme for different elements"],
            ["- Each element (material, WC, DM, CC) can have its own color"],
            ["- Used for flow coloring when element is selected"],
            ["", ""],
            ["Advanced_Options", "Additional features and export settings"],
            ["- Animation, zoom, selection controls"],
            ["- Export quality and format options"],
            ["", ""],
            ["Circular Systems", "Special considerations for circular/recycling systems"],
            ["- Use Layout_Type='Circular' for processes in circular flows"],
            ["- Adjust Circular_Center_X/Y and Circular_Radius for positioning"],
            ["- Use curved flow lines to show recycling connections"],
            ["- Consider using different colors for forward vs. recycling flows"],
        ]
        
        doc_df = pd.DataFrame(doc_config[1:], columns=doc_config[0])
        doc_df.to_excel(writer, sheet_name='Documentation', index=False)
    
    print(f"✅ Visualization configuration file created: {output_path}")
    print("📊 Sheets created:")
    print("  - Process_Visualization: Process colors and positioning")
    print("  - Flow_Visualization: Flow colors and styling")
    print("  - Layout_Configuration: Global layout settings")
    print("  - Element_Colors: Element color schemes")
    print("  - Advanced_Options: Additional features")
    print("  - Documentation: Usage instructions")
    print("\n🎯 Special features for circular systems:")
    print("  - Circular layout type for recycling processes")
    print("  - Custom positioning for optimal circular flow visualization")
    print("  - Curved flow lines to show circular connections")
    print("  - Different styling for forward vs. recycling flows")

if __name__ == "__main__":
    create_visualization_config_excel()
