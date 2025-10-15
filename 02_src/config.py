# -*- coding: utf-8 -*-
"""
Configuration File for the BioDYM MFA Model.

This file contains all the high-level settings and switches to control
a model run. Users can define the input data, model scope, and
calculation modes (e.g., deterministic vs. Monte Carlo) here.
"""

import pandas as pd
import os


def load_config_from_excel(excel_file_path):
    """
    Load configuration settings from Excel file.

    Args:
        excel_file_path (str): Path to the Excel file containing configuration.

    Returns:
        dict: Configuration dictionary with all settings.
    """
    try:
        # Read the Configuration sheet (try different possible names)
        config_sheet_names = ["Configuration", "0_Configuration", "Config"]
        config_df = None

        for sheet_name in config_sheet_names:
            try:
                config_df = pd.read_excel(
                    excel_file_path, sheet_name=sheet_name, header=None
                )
                print(f"✅ Found configuration sheet: '{sheet_name}'")
                break
            except Exception:
                continue

        if config_df is None:
            raise ValueError("No configuration sheet found")

        # Convert to dictionary
        config_dict = {}
        for _, row in config_df.iterrows():
            # New format: Category_Settings | Setting Name | Value | Description | Category | Status
            # We need Column B (Setting Name) and Column C (Value)
            if (pd.notna(row.iloc[1]) and pd.notna(row.iloc[2]) and 
                str(row.iloc[1]).strip() != "Setting Name"):  # Skip header row
                
                key = str(row.iloc[1]).strip()      # Column B: Setting Name
                value = row.iloc[2]                 # Column C: Value

                # Convert string values to appropriate types
                if isinstance(value, str):
                    if value.lower() in ["yes", "no", "true", "false"]:
                        value = value.lower() in ["yes", "true"]
                    elif value.isdigit():
                        value = int(value)
                    elif value.replace(".", "").replace("-", "").isdigit():
                        value = float(value)

                config_dict[key] = value

        return config_dict

    except Exception as e:
        print(f"Warning: Could not load configuration from Excel: {e}")
        print("Using default configuration values.")
        return get_default_config()


def get_default_config():
    """
    Get default configuration values.

    Returns:
        dict: Default configuration dictionary.
    """
    return {
            "Input File Path": "01_data/01_input/250625_Template_CS0.xlsx",
            "Output File Path": "01_data/02_output/results.xlsx",        "Start Year": 2025,
        "End Year": 2050,
        "Elements (comma-separated)": "material,WC,DM,CC",
        "Run Monte Carlo Simulation": False,
        "Monte Carlo Iterations": 100,
        "Run DSM Calculation": True,
        "Run FOMP Calculation": True,
        "Minimum Flow Threshold (Mg)": 0.1,
        "Show Zero Flows in Plots": False,
        "Export Format": "Excel",
        "Default Plot Style": "Line",
        "Color Scheme": "Default",
        "Export Plots as Images": True,
        "Dashboard Layout": "Grid",
        "Mass Balance Tolerance": 0.001,
        "Data Validation Level": "Strict",
        "Auto-save Results": True,
    }


def create_config_object(config_dict):
    """
    Create a configuration object from dictionary.

    Args:
        config_dict (dict): Configuration dictionary.

    Returns:
        object: Configuration object with attributes.
    """

    class Config:
        def __init__(self, config_dict):
            # First, set all the normal attributes from Excel
            for key, value in config_dict.items():
                # Convert Excel column names to Python attributes
                attr_name = key.replace(" ", "_").replace("(", "").replace(")", "")
                setattr(self, attr_name, value)
                # Also set uppercase version for backward compatibility
                setattr(self, attr_name.upper(), value)

            # Add uppercase aliases for backward compatibility
            # Map of setting names (as they appear in config_dict) to uppercase legacy names
            uppercase_aliases = {
                "Input_File": "EXCEL_FILE_PATH",
                "Output_File": "OUTPUT_FILE_PATH",
                "Start_Year": "START_YEAR",
                "End_Year": "END_YEAR",
                "Elements": "ELEMENTS",
                "RUN_MONTE_CARLO": "RUN_MONTE_CARLO",  # Already uppercase in Excel
                "MC_Iterations": "MC_ITERATIONS",
                "Run_DSM_Calculation": "RUN_DSM_CALCULATION",
                "Run_FOMP_Calculation": "RUN_FOMP_CALCULATION",
                "Min_Flow_Threshold": "MIN_FLOW_THRESHOLD",
                "Show_Zero_Flows": "SHOW_ZERO_FLOWS",
                "Export_Format": "EXPORT_FORMAT",
                "Color_Scheme": "COLOR_SCHEME",
                "Export_Plots_As_Images": "EXPORT_PLOTS_AS_IMAGES",
                "Mass_Balance_Tolerance": "MASS_BALANCE_TOLERANCE",
                "Data_Validation_Level": "DATA_VALIDATION_LEVEL",
                "Auto_Save_Results": "AUTO_SAVE_RESULTS",
            }

            # Set uppercase aliases
            for excel_key, uppercase_name in uppercase_aliases.items():
                if excel_key in config_dict:
                    setattr(self, uppercase_name, config_dict[excel_key])

    return Config(config_dict)


# ==============================================================================
# DEFAULT CONFIGURATION (for backward compatibility)
# ==============================================================================
# Note: All configuration values are now loaded from Excel files.
# These hardcoded values are only used as fallbacks if Excel loading fails.

# ==============================================================================
# CONFIGURATION LOADER FUNCTION
# ==============================================================================


def load_configuration(excel_file_path=None):
    """
    Load configuration from Excel file or use defaults.

    Args:
        excel_file_path (str, optional): Path to Excel file with configuration.

    Returns:
        object: Configuration object.
    """
    if excel_file_path and os.path.exists(excel_file_path):
        try:
            config_dict = load_config_from_excel(excel_file_path)
            return create_config_object(config_dict)
        except Exception as e:
            print(f"Error loading configuration from Excel: {e}")
            print("Using default configuration.")

    # Use default configuration
    default_config = get_default_config()
    return create_config_object(default_config)
