#!/usr/bin/env python3
"""
BioDYM Color Palette Generator

This script creates an Excel file with 20 recommended colors
for BioDYM system visualization, organized by category.
"""

import pandas as pd
import os

def create_color_palette_excel(output_path="data/01_input/BioDYM_Color_Palette.xlsx"):
    """
    Creates an Excel file with the BioDYM color palette.
    
    Args:
        output_path (str): Path where to save the Excel file
    """
    
    # Define the color palette
    colors = {
        'Biomass & Natural': [
            {'Name': 'Forest Green', 'Hex': '#228B22', 'RGB': '(34, 139, 34)', 'Usage': 'Primary biomass, organic matter'},
            {'Name': 'Olive Green', 'Hex': '#6B8E23', 'RGB': '(107, 142, 35)', 'Usage': 'Secondary biomass, plant material'},
            {'Name': 'Sage Green', 'Hex': '#9CAF88', 'RGB': '(156, 175, 136)', 'Usage': 'Processed biomass, compost'},
            {'Name': 'Earth Brown', 'Hex': '#8B4513', 'RGB': '(139, 69, 19)', 'Usage': 'Soil, organic matter'},
            {'Name': 'Wheat Gold', 'Hex': '#F5DEB3', 'RGB': '(245, 222, 179)', 'Usage': 'Straw, agricultural waste'},
        ],
        'Water & Liquid': [
            {'Name': 'Ocean Blue', 'Hex': '#0066CC', 'RGB': '(0, 102, 204)', 'Usage': 'Water content, liquid flows'},
            {'Name': 'Aqua Blue', 'Hex': '#00CED1', 'RGB': '(0, 206, 209)', 'Usage': 'Process water, treatment'},
            {'Name': 'Deep Blue', 'Hex': '#191970', 'RGB': '(25, 25, 112)', 'Usage': 'Deep water, storage'},
            {'Name': 'Light Blue', 'Hex': '#87CEEB', 'RGB': '(135, 206, 235)', 'Usage': 'Water vapor, evaporation'},
        ],
        'Energy & Processing': [
            {'Name': 'Fire Orange', 'Hex': '#FF4500', 'RGB': '(255, 69, 0)', 'Usage': 'Energy, heat, combustion'},
            {'Name': 'Amber', 'Hex': '#FFBF00', 'RGB': '(255, 191, 0)', 'Usage': 'Energy storage, power'},
            {'Name': 'Red Orange', 'Hex': '#FF6347', 'RGB': '(255, 99, 71)', 'Usage': 'High energy processes'},
            {'Name': 'Dark Red', 'Hex': '#8B0000', 'RGB': '(139, 0, 0)', 'Usage': 'Waste, losses, emissions'},
        ],
        'Recycling & Circular': [
            {'Name': 'Teal', 'Hex': '#008B8B', 'RGB': '(0, 139, 139)', 'Usage': 'Recycling processes'},
            {'Name': 'Mint Green', 'Hex': '#98FB98', 'RGB': '(152, 251, 152)', 'Usage': 'Circular flows, reuse'},
            {'Name': 'Purple', 'Hex': '#9370DB', 'RGB': '(147, 112, 219)', 'Usage': 'Circular economy processes'},
            {'Name': 'Indigo', 'Hex': '#4B0082', 'RGB': '(75, 0, 130)', 'Usage': 'Advanced recycling'},
        ],
        'System & Flow': [
            {'Name': 'Steel Blue', 'Hex': '#4682B4', 'RGB': '(70, 130, 180)', 'Usage': 'System processes'},
            {'Name': 'Slate Gray', 'Hex': '#708090', 'RGB': '(112, 128, 144)', 'Usage': 'Infrastructure, storage'},
            {'Name': 'Dark Gray', 'Hex': '#2F4F4F', 'RGB': '(47, 79, 79)', 'Usage': 'System boundaries'},
            {'Name': 'Silver', 'Hex': '#C0C0C0', 'RGB': '(192, 192, 192)', 'Usage': 'Neutral processes'},
        ]
    }
    
    # Create the Excel file
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        
        # Create a comprehensive color sheet
        all_colors = []
        for category, color_list in colors.items():
            for color in color_list:
                all_colors.append({
                    'Category': category,
                    'Color_Name': color['Name'],
                    'Hex_Code': color['Hex'],
                    'RGB_Values': color['RGB'],
                    'Usage': color['Usage']
                })
        
        colors_df = pd.DataFrame(all_colors)
        colors_df.to_excel(writer, sheet_name='Color_Palette', index=False)
        
        # Create process type recommendations
        process_colors = [
            {'Process_Type': 'Input Processes', 'Recommended_Colors': 'Forest Green (#228B22), Olive Green (#6B8E23)', 'Usage': 'Primary system inputs'},
            {'Process_Type': 'Processing', 'Recommended_Colors': 'Steel Blue (#4682B4), Teal (#008B8B)', 'Usage': 'Main processing steps'},
            {'Process_Type': 'Circular/Recycling', 'Recommended_Colors': 'Purple (#9370DB), Mint Green (#98FB98)', 'Usage': 'Recycling and circular processes'},
            {'Process_Type': 'Output', 'Recommended_Colors': 'Wheat Gold (#F5DEB3), Amber (#FFBF00)', 'Usage': 'Final system outputs'},
            {'Process_Type': 'Waste/Losses', 'Recommended_Colors': 'Dark Red (#8B0000), Red Orange (#FF6347)', 'Usage': 'Waste and loss processes'},
        ]
        
        process_df = pd.DataFrame(process_colors)
        process_df.to_excel(writer, sheet_name='Process_Type_Colors', index=False)
        
        # Create element-specific colors
        element_colors = [
            {'Element': 'Material (DM)', 'Color': 'Forest Green', 'Hex_Code': '#228B22', 'Usage': 'Dry matter content'},
            {'Element': 'Water Content (WC)', 'Color': 'Ocean Blue', 'Hex_Code': '#0066CC', 'Usage': 'Water content'},
            {'Element': 'Carbon Content (CC)', 'Color': 'Earth Brown', 'Hex_Code': '#8B4513', 'Usage': 'Carbon content'},
            {'Element': 'Ash Content', 'Color': 'Slate Gray', 'Hex_Code': '#708090', 'Usage': 'Ash and mineral content'},
        ]
        
        element_df = pd.DataFrame(element_colors)
        element_df.to_excel(writer, sheet_name='Element_Colors', index=False)
        
        # Create ready-to-use configuration template
        config_template = [
            {'Process_ID': 'P_01', 'Process_Name': 'Input', 'Node_Color': '#228B22', 'Description': 'Primary system input'},
            {'Process_ID': 'P_02', 'Process_Name': 'Processing', 'Node_Color': '#4682B4', 'Description': 'Main processing step'},
            {'Process_ID': 'P_03', 'Process_Name': 'Recycling', 'Node_Color': '#9370DB', 'Description': 'Circular process'},
            {'Process_ID': 'P_04', 'Process_Name': 'Output', 'Node_Color': '#F5DEB3', 'Description': 'Final output'},
        ]
        
        config_df = pd.DataFrame(config_template)
        config_df.to_excel(writer, sheet_name='Ready_to_Use_Config', index=False)
        
        # Create usage guidelines
        guidelines = [
            {'Guideline': 'Use darker colors for primary processes', 'Example': 'Forest Green for main inputs'},
            {'Guideline': 'Use lighter colors for secondary processes', 'Example': 'Sage Green for processed materials'},
            {'Guideline': 'Use contrasting colors for different flow types', 'Example': 'Blue for water, Green for material'},
            {'Guideline': 'Use consistent colors for similar process types', 'Example': 'All recycling processes in Purple tones'},
            {'Guideline': 'Use muted colors for background elements', 'Example': 'Slate Gray for infrastructure'},
        ]
        
        guidelines_df = pd.DataFrame(guidelines)
        guidelines_df.to_excel(writer, sheet_name='Usage_Guidelines', index=False)
    
    print(f"✅ Color palette Excel file created: {output_path}")
    print("\n📊 Sheets created:")
    print("  - Color_Palette: Complete color list with hex codes")
    print("  - Process_Type_Colors: Recommended colors by process type")
    print("  - Element_Colors: Element-specific color recommendations")
    print("  - Ready_to_Use_Config: Template for immediate use")
    print("  - Usage_Guidelines: Best practices for color usage")
    
    print("\n🎨 20 Recommended Colors:")
    for category, color_list in colors.items():
        print(f"\n{category}:")
        for color in color_list:
            print(f"  - {color['Name']}: {color['Hex']} - {color['Usage']}")
    
    print(f"\n🎯 Ready to use in your BioDYM system!")
    print(f"   Open: {output_path}")
    print(f"   Copy colors from 'Ready_to_Use_Config' sheet")
    print(f"   Paste into your visualization configuration")

if __name__ == "__main__":
    create_color_palette_excel()
