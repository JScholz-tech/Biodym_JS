# -*- coding: utf-8 -*-
"""
Visualization Loader Module for BioDYM MFA Tool.

This module integrates with the existing Part 6 visualization sheets
and provides enhanced visualization configuration capabilities.
"""

import pandas as pd
import os
from typing import Dict, Any, Optional

# Handle both direct import and package import
try:
    from .. import utils
except ImportError:
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    import utils


def load_visualization_config_from_excel(excel_file_path: str) -> Dict[str, Any]:
    """
    Load visualization configuration from the main Excel file.
    """
    config = {}
    try:
        print("Loading visualization configuration from Excel...")
        part6_config = load_part6_visualization_sheets(excel_file_path)
        config.update(part6_config)
        enhanced_config = load_enhanced_visualization_config(excel_file_path)
        config.update(enhanced_config)
        color_config = load_color_palette_config(excel_file_path)
        config.update(color_config)
        print("Visualization configuration loaded successfully")
    except Exception as e:
        print(f"Warning: Could not load visualization config: {e}")
        print("Using default configuration")
        config = get_default_visualization_config()
    return config


def _convert_df_decimal_columns(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    """
    Converts comma-based decimal strings to dot-based floats in specified columns.
    """
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(",", ".", regex=False), errors="coerce"
            )
    return df


def find_sheet_by_name(excel_file: pd.ExcelFile, possible_names: list) -> Optional[str]:
    """
    Find the actual name of a sheet in an Excel file from a list of possible names,
    ignoring leading/trailing whitespace.
    """
    trimmed_sheet_names = {name.strip(): name for name in excel_file.sheet_names}
    for name in possible_names:
        if name in trimmed_sheet_names:
            return trimmed_sheet_names[name]
    return None


def load_part6_visualization_sheets(excel_file_path: str) -> Dict[str, Any]:
    """
    Load existing Part 6 visualization sheets from the Excel file.
    """
    config = {}
    try:
        excel_file = pd.ExcelFile(excel_file_path)

        # Load Process Colors sheet
        process_sheet_names = ["6_1_Process_Colors", "6_1_Visualization_Processes"]
        actual_process_sheet = find_sheet_by_name(excel_file, process_sheet_names)
        if actual_process_sheet:
            process_colors_df = utils.safe_read_excel(
                excel_file_path, sheet_name=actual_process_sheet, dtype=str
            )
            process_colors_df = _convert_df_decimal_columns(
                process_colors_df,
                [
                    "X_Position",
                    "Y_Position",
                    "X_Position_Material",
                    "Y_Position_Material",
                    "X_Position_WC",
                    "Y_Position_WC",
                    "X_Position_DM",
                    "Y_Position_DM",
                    "X_Position_CC",
                    "Y_Position_CC",
                ],
            )
            key_col = (
                "Process_ID" if "Process_ID" in process_colors_df.columns else "ID"
            )
            if key_col in process_colors_df.columns:
                process_colors_df = process_colors_df.dropna(subset=[key_col])
                process_colors_df = process_colors_df.drop_duplicates(
                    subset=[key_col], keep="first"
                )
                norm_keys = (
                    process_colors_df[key_col].astype(str).str.strip().str.upper()
                )
                process_colors_df = process_colors_df.assign(_NORM_KEY=norm_keys)
                config["process_colors"] = process_colors_df.set_index(
                    "_NORM_KEY"
                ).to_dict("index")
            print(f"  Loaded and processed {actual_process_sheet.strip()}")

        # Load Flow Colors sheet
        flow_sheet_names = ["6_2_Flow_Colors", "6_2_Visualization_Flows"]
        actual_flow_sheet = find_sheet_by_name(excel_file, flow_sheet_names)
        if actual_flow_sheet:
            flow_colors_df = utils.safe_read_excel(
                excel_file_path, sheet_name=actual_flow_sheet
            )
            key_col = "Flow_ID" if "Flow_ID" in flow_colors_df.columns else "ID"
            if key_col in flow_colors_df.columns:
                flow_colors_df = flow_colors_df.dropna(subset=[key_col])
                flow_colors_df = flow_colors_df.drop_duplicates(
                    subset=[key_col], keep="first"
                )
                config["flow_colors"] = flow_colors_df.set_index(key_col).to_dict(
                    "index"
                )
            print(f"  Loaded {actual_flow_sheet.strip()}")

        # Load Layout Settings sheet
        layout_sheet_names = ["6_3_Layout_Settings", "6_3_Layout_Configuration"]
        actual_layout_sheet = find_sheet_by_name(excel_file, layout_sheet_names)
        if actual_layout_sheet:
            layout_df = utils.safe_read_excel(excel_file_path, sheet_name=actual_layout_sheet)
            if "Setting" in layout_df.columns and "Value" in layout_df.columns:
                layout_dict = {}
                for _, row in layout_df.iterrows():
                    setting = str(row["Setting"]).strip()
                    value = row["Value"]
                    if pd.isna(value):
                        continue
                    if str(value).lower() in ["true", "false"]:
                        layout_dict[setting] = str(value).lower() == "true"
                    else:
                        layout_dict[setting] = value
                config["layout_settings"] = layout_dict
            print(f"  Loaded {actual_layout_sheet.strip()}")

    except Exception as e:
        print(f"  Warning: Could not load Part 6 visualization sheets: {e}")
    return config


def load_enhanced_visualization_config(excel_file_path: str) -> Dict[str, Any]:
    """Load enhanced visualization configuration sheets."""
    config = {}
    try:
        excel_file = pd.ExcelFile(excel_file_path)
        sheet_name = find_sheet_by_name(excel_file, ["Process_Visualization"])
        if sheet_name:
            process_df = utils.safe_read_excel(excel_file_path, sheet_name=sheet_name)
            config["processes"] = process_df.set_index("Process_ID").to_dict("index")
            print("  Loaded Process_Visualization")
        sheet_name = find_sheet_by_name(excel_file, ["Flow_Visualization"])
        if sheet_name:
            flow_df = utils.safe_read_excel(excel_file_path, sheet_name=sheet_name)
            config["flows"] = flow_df.set_index("Flow_ID").to_dict("index")
            print("  Loaded Flow_Visualization")
        sheet_name = find_sheet_by_name(excel_file, ["Layout_Configuration"])
        if sheet_name:
            layout_df = utils.safe_read_excel(excel_file_path, sheet_name=sheet_name)
            config["layout"] = layout_df.set_index("Setting").to_dict("index")["Value"]
            print("  Loaded Layout_Configuration")
        sheet_name = find_sheet_by_name(excel_file, ["Element_Colors"])
        if sheet_name:
            element_df = utils.safe_read_excel(excel_file_path, sheet_name=sheet_name)
            config["elements"] = element_df.set_index("Element").to_dict("index")
            print("  Loaded Element_Colors")
        sheet_name = find_sheet_by_name(excel_file, ["Advanced_Options"])
        if sheet_name:
            advanced_df = utils.safe_read_excel(excel_file_path, sheet_name=sheet_name)
            config["advanced"] = advanced_df.set_index("Setting").to_dict("index")[
                "Value"
            ]
            print("  Loaded Advanced_Options")
    except Exception as e:
        print(f"  Warning: Could not load enhanced visualization config: {e}")
    return config


def load_color_palette_config(excel_file_path: str) -> Dict[str, Any]:
    """Load color palette configuration if available."""
    config = {}
    try:
        excel_file = pd.ExcelFile(excel_file_path)
        sheet_name = find_sheet_by_name(excel_file, ["Color_Palette"])
        if sheet_name:
            color_df = utils.safe_read_excel(excel_file_path, sheet_name=sheet_name)
            config["color_palette"] = color_df.to_dict("records")
            print("  Loaded Color_Palette")
        sheet_name = find_sheet_by_name(excel_file, ["Process_Type_Colors"])
        if sheet_name:
            process_type_df = utils.safe_read_excel(excel_file_path, sheet_name=sheet_name)
            config["process_type_colors"] = process_type_df.to_dict("records")
            print("  Loaded Process_Type_Colors")
    except Exception as e:
        print(f"  Warning: Could not load color palette config: {e}")
    return config


def get_default_visualization_config() -> Dict[str, Any]:
    """Get default visualization configuration."""
    return {
        "processes": {},
        "flows": {},
        "layout": {
            "Default_Layout_Type": "Circular",
            "Circular_Center_X": "0.5",
            "Circular_Center_Y": "0.5",
            "Circular_Radius": "0.3",
            "Node_Spacing": "0.1",
            "Flow_Curvature": "0.5",
            "Show_Flow_Labels": "True",
            "Show_Node_Labels": "True",
            "Background_Color": "#FFFFFF",
            "Grid_Color": "#E0E0E0",
        },
        "elements": {
            "material": {"Color": "#1f77b4", "Opacity": "0.8"},
            "WC": {"Color": "#ff7f0e", "Opacity": "0.8"},
            "DM": {"Color": "#2ca02c", "Opacity": "0.8"},
            "CC": {"Color": "#d62728", "Opacity": "0.8"},
        },
        "advanced": {
            "Enable_Animation": "True",
            "Animation_Duration": "1000",
            "Enable_Zoom": "True",
            "Enable_Selection": "True",
            "Export_Resolution": "High",
            "Export_Format": "PNG",
        },
    }


def create_visualization_sheets_template(excel_file_path: str):
    """Create visualization sheets template in the main Excel file."""
    # This function is not fully implemented to avoid accidental overwrites
    pass


def integrate_with_existing_system(excel_file_path: str):
    """Integrate visualization configuration with the existing BioDYM system."""
    print("Integrating visualization configuration with existing system...")
    create_visualization_sheets_template(excel_file_path)
    config = load_visualization_config_from_excel(excel_file_path)
    print("Integration complete!")
    return config
