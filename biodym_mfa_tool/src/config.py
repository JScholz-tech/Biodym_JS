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
            if pd.notna(row.iloc[0]) and pd.notna(row.iloc[1]):
                key = str(row.iloc[0]).strip()
                value = row.iloc[1]

                # Convert string values to appropriate types
                if isinstance(value, str):
                    if value.lower() in ["yes", "no"]:
                        value = value.lower() == "yes"
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
        "Input File Path": "data/01_input/250625_Template_CS0.xlsx",
        "Output File Path": "data/02_output/results.xlsx",
        "Start Year": 2025,
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

            # Add uppercase aliases for backward compatibility
            # Map of Excel names to uppercase legacy names
            uppercase_aliases = {
                "Input File Path": "EXCEL_FILE_PATH",
                "Output File Path": "OUTPUT_FILE_PATH",
                "Start Year": "START_YEAR",
                "End Year": "END_YEAR",
                "Elements (comma-separated)": "ELEMENTS",
                "Run Monte Carlo Simulation": "RUN_MONTE_CARLO",
                "Monte Carlo Iterations": "MC_ITERATIONS",
                "Run DSM Calculation": "RUN_DSM_CALCULATION",
                "Run FOMP Calculation": "RUN_FOMP_CALCULATION",
                "Minimum Flow Threshold (Mg)": "MIN_FLOW_THRESHOLD",
                "Show Zero Flows in Plots": "SHOW_ZERO_FLOWS",
                "Export Format": "EXPORT_FORMAT",
                "Default Plot Style": "DEFAULT_PLOT_STYLE",
                "Color Scheme": "COLOR_SCHEME",
                "Export Plots as Images": "EXPORT_PLOTS_AS_IMAGES",
                "Dashboard Layout": "DASHBOARD_LAYOUT",
                "Mass Balance Tolerance": "MASS_BALANCE_TOLERANCE",
                "Data Validation Level": "DATA_VALIDATION_LEVEL",
                "Auto-save Results": "AUTO_SAVE_RESULTS",
            }

            # Set uppercase aliases
            for excel_key, uppercase_name in uppercase_aliases.items():
                if excel_key in config_dict:
                    setattr(self, uppercase_name, config_dict[excel_key])

    return Config(config_dict)


# ==============================================================================
# DEFAULT CONFIGURATION (for backward compatibility)
# ==============================================================================

# Path to the primary Excel input file containing all model definitions
# and data.
EXCEL_FILE_PATH = "250625_Template_CS0.xlsx"

# ==============================================================================
# MODEL SCOPE
# ==============================================================================
# The first year of the analysis.
START_YEAR = 2025
# The last year of the analysis.
END_YEAR = 2050
# List of elements/substances to be tracked throughout the system.
ELEMENTS = ["material", "WC", "DM", "CC"]

# ==============================================================================
# CALCULATION SWITCHES
# ==============================================================================
# Master switch to run a full Monte Carlo simulation.
RUN_MONTE_CARLO = False  # Set to True for uncertainty analysis.

# Number of iterations for the Monte Carlo simulation.
MC_ITERATIONS = 100

# Individual model component switches.
RUN_DSM_CALCULATION = True
RUN_FOMP_CALCULATION = True

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
