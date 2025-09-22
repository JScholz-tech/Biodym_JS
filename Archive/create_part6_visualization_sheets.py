#!/usr/bin/env python3
"""
Create Part 6 Visualization Sheets for BioDYM System

This script creates the Part 6 visualization sheets that can be
copied into your main Excel file.
"""

import pandas as pd
import os

def create_part6_visualization_sheets():
    """Create Part 6 visualization sheets template."""
    
    print("📊 Creating Part 6 Visualization Sheets for BioDYM System")
    print("=" * 60)
    
    # Output file path
    output_path = "data/01_input/Part6_Visualization_Sheets.xlsx"
    
    try:
        # Create the Excel file with Part 6 visualization sheets
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            
            # 6_1_Process_Colors sheet
            process_colors_data = [
                ['Process_ID', 'Process_Name', 'Node_Color', 'Node_Size', 'X_Position', 'Y_Position', 'Layout_Type', 'Description'],
                ['P_01', 'Input Process', '#228B22', 'Large', '0.1', '0.5', 'Fixed', 'Primary system input'],
                ['P_02', 'Processing', '#4682B4', 'Medium', '0.5', '0.5', 'Circular', 'Main processing step'],
                ['P_03', 'Recycling', '#9370DB', 'Medium', '0.5', '0.5', 'Circular', 'Circular/recycling process'],
                ['P_04', 'Output Process', '#F5DEB3', 'Large', '0.9', '0.5', 'Fixed', 'Final system output'],
                ['', '', '', '', '', '', '', ''],
                ['# Instructions:', '', '', '', '', '', '', ''],
                ['# Process_ID: Must match your MFA system process IDs', '', '', '', '', '', '', ''],
                ['# Node_Color: Hex color codes (e.g., #228B22)', '', '', '', '', '', '', ''],
                ['# Node_Size: Small, Medium, Large, XLarge', '', '', '', '', '', '', ''],
                ['# X_Position: 0.0 to 1.0 (left to right)', '', '', '', '', '', '', ''],
                ['# Y_Position: 0.0 to 1.0 (bottom to top)', '', '', '', '', '', '', ''],
                ['# Layout_Type: Auto, Fixed, Circular, Radial', '', '', '', '', '', '', ''],
            ]
            
            process_df = pd.DataFrame(process_colors_data[1:], columns=process_colors_data[0])
            process_df.to_excel(writer, sheet_name='6_1_Process_Colors', index=False)
            
            # 6_2_Flow_Colors sheet
            flow_colors_data = [
                ['Flow_ID', 'Flow_Name', 'Flow_Color', 'Flow_Opacity', 'Flow_Width_Multiplier', 'Flow_Style', 'Description'],
                ['F_01_02', 'Input to Processing', '#228B22', '0.8', '1.0', 'Solid', 'Primary input flow'],
                ['F_02_03', 'Processing to Recycling', '#4682B4', '0.8', '1.0', 'Solid', 'Forward flow'],
                ['F_03_02', 'Recycling to Processing', '#9370DB', '0.6', '0.8', 'Dashed', 'Recycling flow (circular)'],
                ['F_02_04', 'Processing to Output', '#F5DEB3', '0.8', '1.0', 'Solid', 'Final output flow'],
                ['', '', '', '', '', '', ''],
                ['# Instructions:', '', '', '', '', '', ''],
                ['# Flow_ID: Must match your MFA system flow IDs', '', '', '', '', '', ''],
                ['# Flow_Color: Hex color codes', '', '', '', '', '', ''],
                ['# Flow_Opacity: 0.0 to 1.0 (transparent to opaque)', '', '', '', '', '', ''],
                ['# Flow_Width_Multiplier: 0.1 to 3.0 (relative to flow value)', '', '', '', '', '', ''],
                ['# Flow_Style: Solid, Dashed, Dotted', '', '', '', '', '', ''],
            ]
            
            flow_df = pd.DataFrame(flow_colors_data[1:], columns=flow_colors_data[0])
            flow_df.to_excel(writer, sheet_name='6_2_Flow_Colors', index=False)
            
            # 6_3_Layout_Settings sheet
            layout_data = [
                ['Setting', 'Value', 'Description', 'Options'],
                ['Default_Layout_Type', 'Circular', 'Default layout for circular systems', 'Linear, Circular, Radial, Custom'],
                ['Circular_Center_X', '0.5', 'Center X position for circular layout', '0.0 to 1.0'],
                ['Circular_Center_Y', '0.5', 'Center Y position for circular layout', '0.0 to 1.0'],
                ['Circular_Radius', '0.3', 'Radius for circular layout', '0.1 to 0.5'],
                ['Node_Spacing', '0.1', 'Minimum spacing between nodes', '0.05 to 0.2'],
                ['Flow_Curvature', '0.8', 'Curvature of flow lines (0=straight, 1=max curve)', '0.0 to 1.0'],
                ['Show_Flow_Labels', 'True', 'Show flow values on links', 'True, False'],
                ['Show_Node_Labels', 'True', 'Show process names on nodes', 'True, False'],
                ['Background_Color', '#FFFFFF', 'Background color', 'Hex color code'],
                ['Grid_Color', '#E0E0E0', 'Grid color', 'Hex color code'],
                ['', '', '', ''],
                ['# Circular Layout Options:', '', '', ''],
                ['# - Center position can be adjusted', '', '', ''],
                ['# - Radius controls the size of the circle', '', '', ''],
                ['# - Nodes are distributed evenly around the circle', '', '', ''],
                ['# - Flows follow curved paths between nodes', '', '', ''],
            ]
            
            layout_df = pd.DataFrame(layout_data[1:], columns=layout_data[0])
            layout_df.to_excel(writer, sheet_name='6_3_Layout_Settings', index=False)
            
            # 6_4_Element_Colors sheet
            element_data = [
                ['Element', 'Color', 'Opacity', 'Description', 'Usage'],
                ['material', '#1f77b4', '0.8', 'Material flows', 'Primary material content'],
                ['WC', '#ff7f0e', '0.8', 'Water content', 'Water content in flows'],
                ['DM', '#2ca02c', '0.8', 'Dry matter', 'Dry matter content'],
                ['CC', '#d62728', '0.8', 'Carbon content', 'Carbon content'],
                ['', '', '', '', ''],
                ['# Instructions:', '', '', '', ''],
                ['# Element colors are used for flow coloring', '', '', '', ''],
                ['# Opacity affects the transparency of flows', '', '', '', ''],
                ['# Use consistent colors across all visualizations', '', '', '', ''],
            ]
            
            element_df = pd.DataFrame(element_data[1:], columns=element_data[0])
            element_df.to_excel(writer, sheet_name='6_4_Element_Colors', index=False)
            
            # 6_5_Advanced_Settings sheet
            advanced_data = [
                ['Setting', 'Value', 'Description', 'Options'],
                ['Enable_Animation', 'True', 'Enable flow animations', 'True, False'],
                ['Animation_Duration', '1000', 'Animation duration in ms', '500 to 3000'],
                ['Enable_Zoom', 'True', 'Enable zoom and pan', 'True, False'],
                ['Enable_Selection', 'True', 'Enable node/flow selection', 'True, False'],
                ['Export_Resolution', 'High', 'Export resolution', 'Low, Medium, High, Ultra'],
                ['Export_Format', 'PNG', 'Export format', 'PNG, SVG, PDF'],
                ['Interactive_Mode', 'Full', 'Interactive features', 'Basic, Full, Custom'],
                ['', '', '', ''],
                ['# Advanced Features:', '', '', ''],
                ['# - Animation makes flows more dynamic', '', '', ''],
                ['# - Zoom allows detailed inspection', '', '', ''],
                ['# - Selection enables interactive analysis', '', '', ''],
            ]
            
            advanced_df = pd.DataFrame(advanced_data[1:], columns=advanced_data[0])
            advanced_df.to_excel(writer, sheet_name='6_5_Advanced_Settings', index=False)
            
            # 6_6_Color_Palette sheet (bonus)
            color_palette_data = [
                ['Category', 'Color_Name', 'Hex_Code', 'RGB', 'Usage'],
                ['Biomass & Natural', 'Forest Green', '#228B22', '(34, 139, 34)', 'Primary biomass, organic matter'],
                ['Biomass & Natural', 'Olive Green', '#6B8E23', '(107, 142, 35)', 'Secondary biomass, plant material'],
                ['Biomass & Natural', 'Sage Green', '#9CAF88', '(156, 175, 136)', 'Processed biomass, compost'],
                ['Biomass & Natural', 'Earth Brown', '#8B4513', '(139, 69, 19)', 'Soil, organic matter'],
                ['Biomass & Natural', 'Wheat Gold', '#F5DEB3', '(245, 222, 179)', 'Straw, agricultural waste'],
                ['Water & Liquid', 'Ocean Blue', '#0066CC', '(0, 102, 204)', 'Water content, liquid flows'],
                ['Water & Liquid', 'Aqua Blue', '#00CED1', '(0, 206, 209)', 'Process water, treatment'],
                ['Water & Liquid', 'Deep Blue', '#191970', '(25, 25, 112)', 'Deep water, storage'],
                ['Water & Liquid', 'Light Blue', '#87CEEB', '(135, 206, 235)', 'Water vapor, evaporation'],
                ['Energy & Processing', 'Fire Orange', '#FF4500', '(255, 69, 0)', 'Energy, heat, combustion'],
                ['Energy & Processing', 'Amber', '#FFBF00', '(255, 191, 0)', 'Energy storage, power'],
                ['Energy & Processing', 'Red Orange', '#FF6347', '(255, 99, 71)', 'High energy processes'],
                ['Energy & Processing', 'Dark Red', '#8B0000', '(139, 0, 0)', 'Waste, losses, emissions'],
                ['Recycling & Circular', 'Teal', '#008B8B', '(0, 139, 139)', 'Recycling processes'],
                ['Recycling & Circular', 'Mint Green', '#98FB98', '(152, 251, 152)', 'Circular flows, reuse'],
                ['Recycling & Circular', 'Purple', '#9370DB', '(147, 112, 219)', 'Circular economy processes'],
                ['Recycling & Circular', 'Indigo', '#4B0082', '(75, 0, 130)', 'Advanced recycling'],
                ['System & Flow', 'Steel Blue', '#4682B4', '(70, 130, 180)', 'System processes'],
                ['System & Flow', 'Slate Gray', '#708090', '(112, 128, 144)', 'Infrastructure, storage'],
                ['System & Flow', 'Dark Gray', '#2F4F4F', '(47, 79, 79)', 'System boundaries'],
            ]
            
            color_df = pd.DataFrame(color_palette_data[1:], columns=color_palette_data[0])
            color_df.to_excel(writer, sheet_name='6_6_Color_Palette', index=False)
        
        print(f"✅ Part 6 visualization sheets created: {output_path}")
        print("\n📊 Sheets created:")
        print("  - 6_1_Process_Colors: Process color and positioning settings")
        print("  - 6_2_Flow_Colors: Flow color and styling settings")
        print("  - 6_3_Layout_Settings: Global layout configuration")
        print("  - 6_4_Element_Colors: Element-specific color schemes")
        print("  - 6_5_Advanced_Settings: Advanced visualization options")
        print("  - 6_6_Color_Palette: Complete color palette (20 colors)")
        
        print("\n🎯 Next steps:")
        print("  1. Open the created Excel file: Part6_Visualization_Sheets.xlsx")
        print("  2. Copy the sheets to your main Excel file: 250909_CS1_Wheat_Straw.xlsx")
        print("  3. Edit the Process_ID and Flow_ID values to match your system")
        print("  4. Customize colors and settings as needed")
        print("  5. Use the integrated visualization in your notebook")
        
        print("\n📋 Integration with your notebook:")
        print("""
# Import the enhanced visualization functionality
from plotting import plot_circular_sankey

# Plot with integrated visualization configuration
plot_circular_sankey(
    mfa_system_results=mfa_results_baseline,
    dsm_params=dsm_params,
    fomp_params=fomp_params,
    config_file="data/01_input/250909_CS1_Wheat_Straw.xlsx"  # Uses your existing file
)
        """)
        
    except Exception as e:
        print(f"❌ Error creating Part 6 visualization sheets: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_part6_visualization_sheets()
