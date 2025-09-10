# -*- coding: utf-8 -*-
"""
Visualization Loader Module for BioDYM MFA Tool.

This module integrates with the existing Part 6 visualization sheets
and provides enhanced visualization configuration capabilities.
"""

import pandas as pd
import os
from typing import Dict, Any, Optional

def load_visualization_config_from_excel(excel_file_path: str) -> Dict[str, Any]:
    """
    Load visualization configuration from the main Excel file.
    
    This function integrates with the existing Part 6 visualization sheets
    and provides enhanced configuration capabilities.
    
    Args:
        excel_file_path (str): Path to the main Excel file with visualization sheets
        
    Returns:
        dict: Complete visualization configuration
    """
    config = {}
    
    try:
        print("📊 Loading visualization configuration from Excel...")
        
        # Load existing Part 6 visualization sheets
        part6_config = load_part6_visualization_sheets(excel_file_path)
        config.update(part6_config)
        
        # Load enhanced visualization configuration if available
        enhanced_config = load_enhanced_visualization_config(excel_file_path)
        config.update(enhanced_config)
        
        # Load color palette if available
        color_config = load_color_palette_config(excel_file_path)
        config.update(color_config)
        
        print("✅ Visualization configuration loaded successfully")
        
    except Exception as e:
        print(f"⚠️ Warning: Could not load visualization config: {e}")
        print("Using default configuration")
        config = get_default_visualization_config()
    
    return config

def _convert_df_decimal_columns(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    """
    Converts comma-based decimal strings to dot-based floats in specified columns.
    Also handles cases where data might already be numeric.
    """
    for col in columns:
        if col in df.columns:
            # Convert to string, replace comma, then convert to numeric, coercing errors
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(',', '.', regex=False), 
                errors='coerce'
            )
    return df

def load_part6_visualization_sheets(excel_file_path: str) -> Dict[str, Any]:
    """
    Load existing Part 6 visualization sheets from the Excel file.
    
    Args:
        excel_file_path (str): Path to the Excel file
        
    Returns:
        dict: Part 6 visualization configuration
    """
    config = {}
    
    try:
        # Load Process Colors sheet (check multiple possible names)
        process_sheet_names = ['6_1_Process_Colors', '6_1_Visualization_Processes']
        for sheet_name in process_sheet_names:
            if sheet_exists(excel_file_path, sheet_name):
                process_colors_df = pd.read_excel(excel_file_path, sheet_name=sheet_name, dtype=str)
                
                # --- FIX: Convert decimal columns before processing ---
                # Convert both general and element-specific position columns
                position_columns = ['X_Position', 'Y_Position']
                element_specific_columns = [
                    'X_Position_Material', 'Y_Position_Material',
                    'X_Position_WC', 'Y_Position_WC',
                    'X_Position_DM', 'Y_Position_DM',
                    'X_Position_CC', 'Y_Position_CC'
                ]
                all_position_columns = position_columns + element_specific_columns
                
                process_colors_df = _convert_df_decimal_columns(
                    process_colors_df, all_position_columns
                )
                
                # Handle different column names and duplicate IDs
                key_col = None
                if 'Process_ID' in process_colors_df.columns:
                    key_col = 'Process_ID'
                    process_colors_df = process_colors_df.dropna(subset=[key_col])
                    process_colors_df = process_colors_df.drop_duplicates(subset=[key_col], keep='first')
                elif 'ID' in process_colors_df.columns:
                    key_col = 'ID'
                    process_colors_df = process_colors_df.dropna(subset=[key_col])
                    process_colors_df = process_colors_df.drop_duplicates(subset=[key_col], keep='first')

                if key_col:
                    # Normalize keys: strip and upper for robust matching
                    norm_keys = process_colors_df[key_col].astype(str).str.strip().str.upper()
                    process_colors_df = process_colors_df.assign(_NORM_KEY=norm_keys)
                    raw_map = process_colors_df.set_index('_NORM_KEY').to_dict('index')
                    config['process_colors'] = raw_map
                
                print(f"  ✅ Loaded and processed {sheet_name}")
                break
        
        # Load Flow Colors sheet (check multiple possible names)
        flow_sheet_names = ['6_2_Flow_Colors', '6_2_Visualization_Flows']
        for sheet_name in flow_sheet_names:
            if sheet_exists(excel_file_path, sheet_name):
                flow_colors_df = pd.read_excel(excel_file_path, sheet_name=sheet_name)
                if 'Flow_ID' in flow_colors_df.columns:
                    flow_colors_df = flow_colors_df.dropna(subset=['Flow_ID'])
                    flow_colors_df = flow_colors_df.drop_duplicates(subset=['Flow_ID'], keep='first')
                    config['flow_colors'] = flow_colors_df.set_index('Flow_ID').to_dict('index')
                elif 'ID' in flow_colors_df.columns:
                    flow_colors_df = flow_colors_df.dropna(subset=['ID'])
                    flow_colors_df = flow_colors_df.drop_duplicates(subset=['ID'], keep='first')
                    config['flow_colors'] = flow_colors_df.set_index('ID').to_dict('index')
                print(f"  ✅ Loaded {sheet_name}")
                break
        
        
        # Load Layout Settings sheet (check multiple possible names)
        layout_sheet_names = ['6_3_Layout_Settings', '6_3_Layout_Configuration']
        for sheet_name in layout_sheet_names:
            if sheet_exists(excel_file_path, sheet_name):
                layout_df = pd.read_excel(excel_file_path, sheet_name=sheet_name)
                if 'Setting' in layout_df.columns and 'Value' in layout_df.columns:
                    # Convert to dictionary, handling different data types
                    layout_dict = {}
                    for _, row in layout_df.iterrows():
                        setting = str(row['Setting']).strip()
                        value = row['Value']
                        
                        # Convert value based on type
                        if pd.isna(value):
                            continue
                        elif str(value).lower() in ['true', 'false']:
                            layout_dict[setting] = str(value).lower() == 'true'
                        elif str(value).replace('.', '').replace(',', '').isdigit():
                            # Handle both dot and comma decimal separators
                            try:
                                layout_dict[setting] = float(str(value).replace(',', '.'))
                            except ValueError:
                                layout_dict[setting] = str(value)
                        else:
                            layout_dict[setting] = str(value)
                    
                    config['layout_settings'] = layout_dict
                print(f"  ✅ Loaded {sheet_name}")
                break
        
        # Load Advanced Settings sheet (check multiple possible names)
        advanced_sheet_names = ['6_5_Advanced_Settings', '6_5_Advanced_Options']
        for sheet_name in advanced_sheet_names:
            if sheet_exists(excel_file_path, sheet_name):
                advanced_df = pd.read_excel(excel_file_path, sheet_name=sheet_name)
                if 'Setting' in advanced_df.columns and 'Value' in advanced_df.columns:
                    config['advanced_settings'] = advanced_df.set_index('Setting').to_dict('index')['Value']
                print(f"  ✅ Loaded {sheet_name}")
                break
        
    except Exception as e:
        print(f"  ⚠️ Warning: Could not load Part 6 visualization sheets: {e}")
    
    return config

def load_enhanced_visualization_config(excel_file_path: str) -> Dict[str, Any]:
    """
    Load enhanced visualization configuration sheets.
    
    Args:
        excel_file_path (str): Path to the Excel file
        
    Returns:
        dict: Enhanced visualization configuration
    """
    config = {}
    
    try:
        # Load Process Visualization sheet
        if sheet_exists(excel_file_path, 'Process_Visualization'):
            process_df = pd.read_excel(excel_file_path, sheet_name='Process_Visualization')
            config['processes'] = process_df.set_index('Process_ID').to_dict('index')
            print("  ✅ Loaded Process_Visualization")
        
        # Load Flow Visualization sheet
        if sheet_exists(excel_file_path, 'Flow_Visualization'):
            flow_df = pd.read_excel(excel_file_path, sheet_name='Flow_Visualization')
            config['flows'] = flow_df.set_index('Flow_ID').to_dict('index')
            print("  ✅ Loaded Flow_Visualization")
        
        # Load Layout Configuration sheet
        if sheet_exists(excel_file_path, 'Layout_Configuration'):
            layout_df = pd.read_excel(excel_file_path, sheet_name='Layout_Configuration')
            config['layout'] = layout_df.set_index('Setting').to_dict('index')['Value']
            print("  ✅ Loaded Layout_Configuration")
        
        # Load Element Colors sheet
        if sheet_exists(excel_file_path, 'Element_Colors'):
            element_df = pd.read_excel(excel_file_path, sheet_name='Element_Colors')
            config['elements'] = element_df.set_index('Element').to_dict('index')
            print("  ✅ Loaded Element_Colors")
        
        # Load Advanced Options sheet
        if sheet_exists(excel_file_path, 'Advanced_Options'):
            advanced_df = pd.read_excel(excel_file_path, sheet_name='Advanced_Options')
            config['advanced'] = advanced_df.set_index('Setting').to_dict('index')['Value']
            print("  ✅ Loaded Advanced_Options")
        
    except Exception as e:
        print(f"  ⚠️ Warning: Could not load enhanced visualization config: {e}")
    
    return config

def load_color_palette_config(excel_file_path: str) -> Dict[str, Any]:
    """
    Load color palette configuration if available.
    
    Args:
        excel_file_path (str): Path to the Excel file
        
    Returns:
        dict: Color palette configuration
    """
    config = {}
    
    try:
        # Load Color Palette sheet
        if sheet_exists(excel_file_path, 'Color_Palette'):
            color_df = pd.read_excel(excel_file_path, sheet_name='Color_Palette')
            config['color_palette'] = color_df.to_dict('records')
            print("  ✅ Loaded Color_Palette")
        
        # Load Process Type Colors sheet
        if sheet_exists(excel_file_path, 'Process_Type_Colors'):
            process_type_df = pd.read_excel(excel_file_path, sheet_name='Process_Type_Colors')
            config['process_type_colors'] = process_type_df.to_dict('records')
            print("  ✅ Loaded Process_Type_Colors")
        
    except Exception as e:
        print(f"  ⚠️ Warning: Could not load color palette config: {e}")
    
    return config

def sheet_exists(excel_file_path: str, sheet_name: str) -> bool:
    """
    Check if a sheet exists in the Excel file.
    
    Args:
        excel_file_path (str): Path to the Excel file
        sheet_name (str): Name of the sheet to check
        
    Returns:
        bool: True if sheet exists, False otherwise
    """
    try:
        excel_file = pd.ExcelFile(excel_file_path)
        return sheet_name in excel_file.sheet_names
    except Exception:
        return False

def get_default_visualization_config() -> Dict[str, Any]:
    """
    Get default visualization configuration.
    
    Returns:
        dict: Default visualization configuration
    """
    return {
        'processes': {},
        'flows': {},
        'layout': {
            'Default_Layout_Type': 'Circular',
            'Circular_Center_X': '0.5',
            'Circular_Center_Y': '0.5',
            'Circular_Radius': '0.3',
            'Node_Spacing': '0.1',
            'Flow_Curvature': '0.5',
            'Show_Flow_Labels': 'True',
            'Show_Node_Labels': 'True',
            'Background_Color': '#FFFFFF',
            'Grid_Color': '#E0E0E0'
        },
        'elements': {
            'material': {'Color': '#1f77b4', 'Opacity': '0.8'},
            'WC': {'Color': '#ff7f0e', 'Opacity': '0.8'},
            'DM': {'Color': '#2ca02c', 'Opacity': '0.8'},
            'CC': {'Color': '#d62728', 'Opacity': '0.8'}
        },
        'advanced': {
            'Enable_Animation': 'True',
            'Animation_Duration': '1000',
            'Enable_Zoom': 'True',
            'Enable_Selection': 'True',
            'Export_Resolution': 'High',
            'Export_Format': 'PNG'
        }
    }

def create_visualization_sheets_template(excel_file_path: str):
    """
    Create visualization sheets template in the main Excel file.
    
    Args:
        excel_file_path (str): Path to the Excel file
    """
    try:
        # Read existing Excel file
        excel_file = pd.ExcelFile(excel_file_path)
        existing_sheets = excel_file.sheet_names
        
        # Create new sheets if they don't exist
        with pd.ExcelWriter(excel_file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            
            # Create 6_1_Process_Colors sheet
            if '6_1_Process_Colors' not in existing_sheets:
                process_colors_data = [
                    ['Process_ID', 'Process_Name', 'Node_Color', 'Node_Size', 'X_Position', 'Y_Position', 'Layout_Type', 'Description'],
                    ['P_01', 'Input Process', '#228B22', 'Large', '0.1', '0.5', 'Fixed', 'Primary system input'],
                    ['P_02', 'Processing', '#4682B4', 'Medium', '0.5', '0.5', 'Circular', 'Main processing step'],
                    ['P_03', 'Output Process', '#F5DEB3', 'Large', '0.9', '0.5', 'Fixed', 'Final system output'],
                ]
                process_df = pd.DataFrame(process_colors_data[1:], columns=process_colors_data[0])
                process_df.to_excel(writer, sheet_name='6_1_Process_Colors', index=False)
                print("  ✅ Created 6_1_Process_Colors sheet")
            
            # Create 6_2_Flow_Colors sheet
            if '6_2_Flow_Colors' not in existing_sheets:
                flow_colors_data = [
                    ['Flow_ID', 'Flow_Name', 'Flow_Color', 'Flow_Opacity', 'Flow_Width_Multiplier', 'Flow_Style', 'Description'],
                    ['F_01_02', 'Input to Processing', '#228B22', '0.8', '1.0', 'Solid', 'Primary input flow'],
                    ['F_02_03', 'Processing to Output', '#4682B4', '0.8', '1.0', 'Solid', 'Main process flow'],
                ]
                flow_df = pd.DataFrame(flow_colors_data[1:], columns=flow_colors_data[0])
                flow_df.to_excel(writer, sheet_name='6_2_Flow_Colors', index=False)
                print("  ✅ Created 6_2_Flow_Colors sheet")
            
            # Create 6_3_Layout_Settings sheet
            if '6_3_Layout_Settings' not in existing_sheets:
                layout_data = [
                    ['Setting', 'Value', 'Description'],
                    ['Default_Layout_Type', 'Circular', 'Default layout for circular systems'],
                    ['Circular_Center_X', '0.5', 'Center X position for circular layout'],
                    ['Circular_Center_Y', '0.5', 'Center Y position for circular layout'],
                    ['Circular_Radius', '0.3', 'Radius for circular layout'],
                    ['Flow_Curvature', '0.8', 'High curvature for circular flows'],
                ]
                layout_df = pd.DataFrame(layout_data[1:], columns=layout_data[0])
                layout_df.to_excel(writer, sheet_name='6_3_Layout_Settings', index=False)
                print("  ✅ Created 6_3_Layout_Settings sheet")
            
            # Create 6_4_Element_Colors sheet
            if '6_4_Element_Colors' not in existing_sheets:
                element_data = [
                    ['Element', 'Color', 'Opacity', 'Description'],
                    ['material', '#1f77b4', '0.8', 'Material flows'],
                    ['WC', '#ff7f0e', '0.8', 'Water content'],
                    ['DM', '#2ca02c', '0.8', 'Dry matter'],
                    ['CC', '#d62728', '0.8', 'Carbon content'],
                ]
                element_df = pd.DataFrame(element_data[1:], columns=element_data[0])
                element_df.to_excel(writer, sheet_name='6_4_Element_Colors', index=False)
                print("  ✅ Created 6_4_Element_Colors sheet")
            
            # Create 6_5_Advanced_Settings sheet
            if '6_5_Advanced_Settings' not in existing_sheets:
                advanced_data = [
                    ['Setting', 'Value', 'Description'],
                    ['Enable_Animation', 'True', 'Enable flow animations'],
                    ['Animation_Duration', '1000', 'Animation duration in ms'],
                    ['Enable_Zoom', 'True', 'Enable zoom and pan'],
                    ['Export_Resolution', 'High', 'Export resolution'],
                ]
                advanced_df = pd.DataFrame(advanced_data[1:], columns=advanced_data[0])
                advanced_df.to_excel(writer, sheet_name='6_5_Advanced_Settings', index=False)
                print("  ✅ Created 6_5_Advanced_Settings sheet")
        
        print("✅ Visualization sheets template created successfully")
        
    except Exception as e:
        print(f"❌ Error creating visualization sheets template: {e}")

def integrate_with_existing_system(excel_file_path: str):
    """
    Integrate visualization configuration with the existing BioDYM system.
    
    Args:
        excel_file_path (str): Path to the main Excel file
    """
    print("🔧 Integrating visualization configuration with existing system...")
    
    # Create visualization sheets if they don't exist
    create_visualization_sheets_template(excel_file_path)
    
    # Load the configuration
    config = load_visualization_config_from_excel(excel_file_path)
    
    print("✅ Integration complete!")
    return config
