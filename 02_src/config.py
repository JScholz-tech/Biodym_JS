# -*- coding: utf-8 -*-
"""
Configuration File for the BioDYM MFA Model.

This file contains all the high-level settings and switches to control
a model run. Users can define the input data, model scope, and
calculation modes (e.g., deterministic vs. Monte Carlo) here.
"""

import pandas as pd
import os

# Handle both direct import and package import
try:
    from . import utils
except ImportError:
    import utils


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
                config_df = utils.safe_read_excel(
                    excel_file_path, sheet_name=sheet_name, header=None
                )
                print(f"[OK] Found configuration sheet: '{sheet_name}'")
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
            if (
                pd.notna(row.iloc[1])
                and pd.notna(row.iloc[2])
                and str(row.iloc[1]).strip() != "Setting Name"
            ):  # Skip header row
                key = str(row.iloc[1]).strip()  # Column B: Setting Name
                value = row.iloc[2]  # Column C: Value

                # Convert string values to appropriate types
                if isinstance(value, str):
                    if value.lower() in ["yes", "no", "true", "false"]:
                        value = value.lower() in ["yes", "true"]
                    elif value.isdigit():
                        value = int(value)
                    elif value.replace(".", "").replace("-", "").isdigit():
                        value = float(value)

                config_dict[key] = value

        # Collect Elements from "Element_ID_X" keys with hierarchy support
        element_structure = {}  # {element_id: {'name': str, 'parent': str or None}}
        elements = []

        # First pass: collect all Element_ID_X entries
        for key in list(config_dict.keys()):
            if key.startswith("Element_ID_"):
                try:
                    # Extract element number from Element_ID_X
                    element_num = int(key.split("_")[-1])
                    element_value = config_dict[key]

                    if pd.notna(element_value) and str(element_value).strip():
                        element_name = str(element_value).strip()
                        element_structure[element_num] = {
                            "name": element_name,
                            "parent": None,  # Will be filled in second pass
                        }
                except (ValueError, IndexError):
                    continue

        # Second pass: collect Parent_Element_ID_X entries to build hierarchy
        for key in list(config_dict.keys()):
            if key.startswith("Parent_Element_ID_"):
                try:
                    # Extract element number from Parent_Element_ID_X
                    element_num = int(key.split("_")[-1])
                    parent_value = config_dict[key]

                    if pd.notna(parent_value) and str(parent_value).strip():
                        parent_name = str(parent_value).strip()
                        if element_num in element_structure:
                            element_structure[element_num]["parent"] = parent_name
                except (ValueError, IndexError):
                    continue

        # Build ordered element list (sorted by element_id)
        if element_structure:
            sorted_ids = sorted(element_structure.keys())
            elements = [element_structure[eid]["name"] for eid in sorted_ids]

            # Ensure 'material' is always first (required for total mass tracking)
            if "material" not in elements:
                elements.insert(0, "material")
                print(
                    "[WARNING] 'material' element added automatically (required for total mass)"
                )
            elif elements[0] != "material":
                elements.remove("material")
                elements.insert(0, "material")
                print("[WARNING] 'material' element moved to first position (required)")

            config_dict["Elements"] = ",".join(elements)
            config_dict["Element_Hierarchy"] = (
                element_structure  # Store hierarchy for later use
            )

            # Print hierarchy information
            print(
                f"[OK] Loaded {len(elements)} elements from configuration: {elements}"
            )
            for eid in sorted_ids:
                elem = element_structure[eid]
                if elem["parent"]:
                    print(
                        f"   |-- E{eid} ({elem['name']}) is expressed as % of {elem['parent']}"
                    )
        else:
            # Fallback to default biomass elements
            elements = ["material", "WC", "DM", "CC"]
            config_dict["Elements"] = ",".join(elements)
            config_dict["Element_Hierarchy"] = {}
            print(f"[WARNING] No elements found in config, using defaults: {elements}")

        # Collect Regions from "Region_ID_X" keys (supports both formats)
        regions = []
        for key in list(config_dict.keys()):
            if key.startswith("Region_ID_") or "Region ID" in str(key):
                region_value = config_dict[key]
                if pd.notna(region_value) and str(region_value).strip():
                    regions.append(str(region_value).strip())

        # Add Regions as a comma-separated string
        if regions:
            config_dict["Regions"] = ",".join(regions)
            print(f"[OK] Loaded {len(regions)} regions from configuration: {regions}")

        # Collect Goods from "Good_Type_X" keys (supports both formats)
        goods = []
        for key in list(config_dict.keys()):
            if (
                key.startswith("Good_Type_") or "Good Type" in str(key)
            ) and key != "Enable ODYM Dimension_Goods":
                good_value = config_dict[key]
                if pd.notna(good_value) and str(good_value).strip():
                    goods.append(str(good_value).strip())

        # Add Goods as a comma-separated string
        if goods:
            config_dict["Goods"] = ",".join(goods)
            print(f"[OK] Loaded {len(goods)} goods from configuration: {goods}")

        # Collect Materials from "Material_ID_X" keys (supports both formats)
        materials = []
        for key in list(config_dict.keys()):
            if key.startswith("Material_ID_") or "Material ID" in str(key):
                material_value = config_dict[key]
                if pd.notna(material_value) and str(material_value).strip():
                    materials.append(str(material_value).strip())

        # Add Materials as a comma-separated string
        if materials:
            config_dict["Materials"] = ",".join(materials)
            print(
                f"[OK] Loaded {len(materials)} materials from configuration: {materials}"
            )

        # Collect Process Types from "Process_Type_X" keys (supports both formats)
        process_types = []
        for key in list(config_dict.keys()):
            if (
                key.startswith("Process_Type_") or "Process Type" in str(key)
            ) and key != "Enable ODYM Dimension_Process":
                process_value = config_dict[key]
                if pd.notna(process_value) and str(process_value).strip():
                    process_types.append(str(process_value).strip())

        # Add Process Types as a comma-separated string
        if process_types:
            config_dict["Process_Types"] = ",".join(process_types)
            print(
                f"[OK] Loaded {len(process_types)} process types from configuration: {process_types}"
            )

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
        "Output File Path": "01_data/02_output/results.xlsx",
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
    Creates a configuration object from a dictionary, converting dictionary keys
    into accessible object attributes.

    This function takes a dictionary of configuration settings and transforms it
    into an object where each key-value pair becomes an attribute-value pair.
    It also handles the creation of uppercase aliases for backward compatibility.

    Parameters
    ----------
    config_dict : dict
        A dictionary containing configuration settings. Keys are expected to be
        strings representing setting names, and values are their corresponding
        settings.

    Returns
    -------
    Config
        An object with attributes corresponding to the keys in `config_dict`,
        plus additional uppercase aliases for some attributes.

    Examples
    --------
    >>> config_data = {"Start Year": 2020, "End Year": 2030}
    >>> config_obj = create_config_object(config_data)
    >>> config_obj.Start_Year
    2020
    >>> config_obj.START_YEAR
    2020
    """

    class Config:
        """
        A configuration object that holds settings as attributes.

        This inner class is designed to provide attribute-style access to
        configuration settings that are loaded from a dictionary. It also
        creates uppercase aliases for certain attributes to maintain backward
        compatibility.

        Parameters
        ----------
        config_dict : dict
            A dictionary where keys are configuration setting names (e.g., "Start Year")
            and values are the corresponding settings.

        Attributes
        ----------
        <setting_name> : any
            Each key from `config_dict` is converted into a snake_case attribute.
            For example, "Start Year" becomes `self.Start_Year`.
        <SETTING_NAME> : any
            For certain predefined settings, an uppercase alias is also created.
            For example, `self.START_YEAR`.

        Examples
        --------
        >>> config_data = {"Input File Path": "data.xlsx", "Start Year": 2020}
        >>> config_obj = create_config_object(config_data)
        >>> config_obj.Input_File_Path
        'data.xlsx'
        >>> config_obj.START_YEAR
        2020
        """

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


# ==============================================================================
# WORKFLOW DIMENSION EXTRACTION
# ==============================================================================


def _get_config_list(config_obj, attribute_name, default=None):
    """Extract a comma-separated list attribute from a config object."""
    if hasattr(config_obj, attribute_name):
        value = getattr(config_obj, attribute_name)
        if value and pd.notna(value):
            return [item.strip() for item in str(value).split(",") if item.strip()]
    return default


def resolve_unit(config_obj, default="Mg"):
    """Return the mass unit declared on a config object.

    Different config sources expose the unit under different attribute names;
    this returns the first non-empty string among the known aliases, falling back
    to ``default``.

    Parameters
    ----------
    config_obj : object
        Loaded configuration object.
    default : str, optional
        Unit to use when none is declared. Defaults to ``"Mg"``.

    Returns
    -------
    str
        The resolved mass unit.
    """
    for attr in ("Unit", "Unit_of_Measurement", "UoM", "Mass_Unit"):
        value = getattr(config_obj, attr, None)
        if isinstance(value, str) and value.strip():
            return value
    return default


def extract_workflow_dimensions(config_obj, input_data: dict) -> dict:
    """Extract all dimension lists and time range from a loaded config object.

    Prints a configuration summary to stdout. Falls back to data-driven values
    if config attributes are missing.

    Parameters
    ----------
    config_obj : Config
        Loaded configuration object (from load_configuration).
    input_data : dict
        Full Excel workbook as {sheet_name: DataFrame}, used only for the
        Elements/time fallback when config attributes are absent.

    Returns
    -------
    dict with keys: start_year, end_year, elements, regions, goods,
                    materials, processes, run_scenario, selected_scenario
    """
    try:
        from .constants import Icons
    except ImportError:
        from constants import Icons

    regions = _get_config_list(config_obj, "Regions", ["Case_Study_Region"])
    goods = _get_config_list(config_obj, "Goods", None)
    materials = _get_config_list(config_obj, "Materials", None)
    processes = _get_config_list(config_obj, "Process_Types", None)

    print(f"{Icons.VISUALIZATION} Dimensions loaded from configuration:")
    print(f"   {Icons.ARROW} Regions: {regions}")
    if materials:
        print(f"   - Materials: {materials}")
    if goods:
        print(f"   - Goods: {goods}")
    if processes:
        print(f"   - Process Types: {processes}")

    try:
        start_year = int(config_obj.Start_Year)
        end_year = int(config_obj.End_Year)
        for attr in ("Elements", "Elements_comma_separated", "Element_list"):
            if hasattr(config_obj, attr):
                elements = [e.strip() for e in getattr(config_obj, attr).split(",")]
                break
        else:
            raise AttributeError("No Elements attribute found in config object")
    except Exception as exc:
        print(
            f"{Icons.WARNING} Could not get time/elements from config: {exc}. Falling back to data-driven values."
        )
        flow_data = input_data["1_2_Data_Flows"]
        years = sorted(flow_data["Flow_Data_Year"].unique())
        start_year = int(min(years))
        end_year = int(max(years))
        elements = ["material", "WC", "DM", "CC"]

    run_scenario = getattr(config_obj, "Run_Scenario_Analysis", False)
    selected_scenario = getattr(
        config_obj,
        "Selected_Scenario_Name 1",
        getattr(config_obj, "Selected_Scenario_Name", "N/A"),
    )

    print("\n-- Configuration Summary --")
    print(f"{Icons.TIME} Time range: {start_year} - {end_year}")
    print(f"{Icons.ELEMENT} Elements: {elements}")
    print(
        f"{Icons.MONTE_CARLO} Monte Carlo: {'Enabled' if config_obj.RUN_MONTE_CARLO else 'Disabled'}"
    )
    print(
        f"{Icons.DSM} DSM Calculation: {'Enabled' if config_obj.RUN_DSM_CALCULATION else 'Disabled'}"
    )
    print(
        f"{Icons.FOMP} FOMP Calculation: {'Enabled' if config_obj.RUN_FOMP_CALCULATION else 'Disabled'}"
    )
    print(
        f"{Icons.SCENARIO} Scenario Analysis: {'Enabled' if run_scenario else 'Disabled'}"
    )
    if run_scenario:
        print(f"   -> Selected Scenario: '{selected_scenario}'")

    return {
        "start_year": start_year,
        "end_year": end_year,
        "elements": elements,
        "regions": regions,
        "goods": goods,
        "materials": materials,
        "processes": processes,
        "run_scenario": run_scenario,
        "selected_scenario": selected_scenario,
    }


def load_config_from_yaml(yaml_path: str):
    """Build a Config object from a BioDYM web-app config YAML.

    Produces the same Config object that ``load_configuration`` returns from
    Excel, so the rest of the workflow is unaware of the difference.

    Parameters
    ----------
    yaml_path : str
        Path to the ``config.yaml`` produced by the BioDYM config web app.

    Returns
    -------
    Config
        Configuration object with all standard attributes set.
    """
    import yaml as _yaml

    with open(yaml_path, encoding="utf-8") as f:
        raw = _yaml.safe_load(f) or {}

    model = raw.get("model") or {}
    elements = model.get("elements", ["material", "WC", "DM", "TC"])
    elements_str = ", ".join(elements)

    run_dsm = bool(model.get("run_dsm_calculation", True))
    run_fomp = bool(model.get("run_fomp_calculation", True))
    run_lfg = bool(model.get("run_lfg_calculation", True))
    run_mc = bool(model.get("run_monte_carlo", False))
    run_scen = bool(model.get("run_scenario_analysis", False))

    selected = model.get("selected_scenarios") or []

    config_dict = {
        # Time range
        "Start_Year": int(model.get("start_year", 2025)),
        "End_Year": int(model.get("end_year", 2125)),
        # Elements — all three aliases checked by extract_workflow_dimensions
        "Elements": elements_str,
        "Elements_comma_separated": elements_str,
        "Element_list": elements_str,
        # Unit
        "Unit": model.get("unit_of_measurement", "Mg"),
        "Unit_of_Measurement": model.get("unit_of_measurement", "Mg"),
        # Calculation flags
        "RUN_MONTE_CARLO": run_mc,
        "Run_Monte_Carlo": run_mc,
        "MC_Iterations": int(model.get("mc_iterations", 1000)),
        "Run_DSM_Calculation": run_dsm,
        "RUN_DSM_CALCULATION": run_dsm,
        "Run_FOMP_Calculation": run_fomp,
        "RUN_FOMP_CALCULATION": run_fomp,
        "RUN_LFG_CALCULATION": run_lfg,
        "Run_Scenario_Analysis": run_scen,
        # Scenario names
        "Selected_Scenario_Name 1": selected[0] if len(selected) > 0 else "",
        "Selected_Scenario_Name 2": selected[1] if len(selected) > 1 else "",
        "Selected_Scenario_Name 3": selected[2] if len(selected) > 2 else "",
        "Selected_Scenario_Name 4": selected[3] if len(selected) > 3 else "",
        # Defaults
        "Min_Flow_Threshold": 0.0,
        "Show_Zero_Flows": False,
    }

    return create_config_object(config_dict)
