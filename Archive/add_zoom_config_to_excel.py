#!/usr/bin/env python3
"""
Add zoom factor configuration to the Excel Layout Configuration sheet.

This script adds zoom and scaling settings to the 6_3_Layout_Configuration sheet
so you can control the Sankey diagram scale and ensure flows stay within the frame.
"""

import pandas as pd
import os

def add_zoom_config_to_excel(excel_file_path):
    """
    Add zoom factor configuration to the Excel file.
    
    Args:
        excel_file_path (str): Path to the Excel file
    """
    print(f"📊 Adding zoom configuration to: {excel_file_path}")
    
    try:
        # Load the existing Excel file
        excel_file = pd.ExcelFile(excel_file_path)
        existing_sheets = excel_file.sheet_names
        
        # Read the current layout configuration
        if '6_3_Layout_Configuration' in existing_sheets:
            layout_df = pd.read_excel(excel_file_path, sheet_name='6_3_Layout_Configuration')
            print(f"✅ Found existing 6_3_Layout_Configuration sheet with {len(layout_df)} settings")
        else:
            print("❌ 6_3_Layout_Configuration sheet not found!")
            return False
        
        # Define new zoom and scaling settings
        zoom_settings = [
            {
                'Setting': 'Zoom_Factor',
                'Value': 1.0,
                'Description': 'Overall zoom factor for the Sankey diagram (1.0 = normal, 0.5 = half size, 2.0 = double size)',
                'Category': 'Zoom_Scaling',
                'Status': 'Active'
            },
            {
                'Setting': 'Node_Scale_Factor', 
                'Value': 1.0,
                'Description': 'Scale factor for node sizes (1.0 = normal, 0.8 = smaller nodes, 1.2 = larger nodes)',
                'Category': 'Zoom_Scaling',
                'Status': 'Active'
            },
            {
                'Setting': 'Flow_Scale_Factor',
                'Value': 1.0,
                'Description': 'Scale factor for flow thickness (1.0 = normal, 0.5 = thinner flows, 1.5 = thicker flows)',
                'Category': 'Zoom_Scaling',
                'Status': 'Active'
            },
            {
                'Setting': 'Auto_Fit_Frame',
                'Value': True,
                'Description': 'Automatically adjust zoom to fit all flows within the frame',
                'Category': 'Zoom_Scaling',
                'Status': 'Active'
            },
            {
                'Setting': 'Min_Zoom_Factor',
                'Value': 0.3,
                'Description': 'Minimum zoom factor to prevent diagram from becoming too small',
                'Category': 'Zoom_Scaling',
                'Status': 'Active'
            },
            {
                'Setting': 'Max_Zoom_Factor',
                'Value': 3.0,
                'Description': 'Maximum zoom factor to prevent diagram from becoming too large',
                'Category': 'Zoom_Scaling',
                'Status': 'Active'
            },
            {
                'Setting': 'Padding_Factor',
                'Value': 0.1,
                'Description': 'Extra padding around the diagram as fraction of frame size',
                'Category': 'Zoom_Scaling',
                'Status': 'Active'
            },
            {
                'Setting': 'Center_Diagram',
                'Value': True,
                'Description': 'Center the diagram within the available frame',
                'Category': 'Zoom_Scaling',
                'Status': 'Active'
            }
        ]
        
        # Check if zoom settings already exist
        existing_settings = set(layout_df['Setting'].tolist())
        new_settings = [s for s in zoom_settings if s['Setting'] not in existing_settings]
        
        if not new_settings:
            print("ℹ️ Zoom scaling settings already exist in the Excel file")
            return True
        
        print(f"📝 Adding {len(new_settings)} new zoom scaling settings...")
        
        # Create new rows for zoom settings
        new_rows = []
        for setting in new_settings:
            new_row = {
                'Setting': setting['Setting'],
                'Value': setting['Value'],
                'Description': setting['Description'],
                'Category': setting['Category'],
                'Status': setting['Status']
            }
            new_rows.append(new_row)
        
        # Add new rows to the existing dataframe
        new_df = pd.DataFrame(new_rows)
        updated_layout_df = pd.concat([layout_df, new_df], ignore_index=True)
        
        # Save the updated configuration back to Excel
        with pd.ExcelWriter(excel_file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            updated_layout_df.to_excel(writer, sheet_name='6_3_Layout_Configuration', index=False)
        
        print("✅ Zoom configuration added successfully!")
        print("\n📋 New zoom settings added:")
        for setting in new_settings:
            print(f"   - {setting['Setting']}: {setting['Value']} ({setting['Description']})")
        
        print(f"\n💡 You can now control zoom and scaling in Excel:")
        print(f"   - Open: {excel_file_path}")
        print(f"   - Go to sheet: 6_3_Layout_Configuration")
        print(f"   - Modify Zoom_Factor (0.5 = small, 1.0 = normal, 2.0 = large)")
        print(f"   - Enable Auto_Fit_Frame to automatically fit flows within frame")
        
        return True
        
    except Exception as e:
        print(f"❌ Error adding zoom configuration: {e}")
        return False

def main():
    """Main function to add zoom configuration."""
    excel_file = "data/01_input/250909_CS1_Wheat_Straw.xlsx"
    
    if not os.path.exists(excel_file):
        print(f"❌ Excel file not found: {excel_file}")
        return False
    
    success = add_zoom_config_to_excel(excel_file)
    
    if success:
        print("\n🎉 Zoom configuration setup complete!")
        print("   The enhanced Sankey diagram will now use these Excel settings for zoom and scaling.")
    else:
        print("\n⚠️ Failed to add zoom configuration. Please check the error messages above.")
    
    return success

if __name__ == "__main__":
    main()
