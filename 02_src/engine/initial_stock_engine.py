# -*- coding: utf-8 -*-
"""
Initial Stock Engine Module for the BioDYM Engine.

This file contains the specific calculation logic for processes that have
initial stock values and stock-outflow transfer coefficients. It handles
multiple destination processes, outflow splits, and consumption rates.

This is a BioDYM extension to the ODYM framework.
"""

import numpy as np
import pandas as pd


import ODYM_Classes as msc


def _build_initial_stock_element_column_map(elements, initial_stock_df):
    """
    Dynamically builds column name mapping for initial stock element compositions.

    This follows the same E1-E6 naming convention as flows, looking for columns in this order:
    1. New format: IS_E{id}_Fraction[%]           (e.g., IS_E2_Fraction[%])
    2. New with label: IS_E{id}_[%]({element})    (e.g., IS_E2_[%](WC))
    3. New simple: IS_E{id}[%] or IS_E{id}_[%]    (e.g., IS_E2[%])
    4. Standard: IS_{element}[%]                  (e.g., IS_WC[%])
    5. Legacy: fallback patterns

    Parameters
    ----------
    elements : list of str
        List of element names (e.g., ['material', 'WC', 'DM', 'CC'])
    initial_stock_df : pd.DataFrame
        DataFrame with initial stock parameters to check available parameter types

    Returns
    -------
    dict
        Mapping from element name to parameter type name
        e.g., {'WC': 'IS_E2_[%](WC)', 'DM': 'IS_E3_[%](DM)', 'CC': 'IS_E4_[%](CC)'}
    """
    param_type_map = {}

    # Get unique parameter types from the dataframe
    if "IS_Parameter_type" in initial_stock_df.columns:
        available_params = initial_stock_df["IS_Parameter_type"].unique().tolist()
    else:
        available_params = []

    for elem_idx, element in enumerate(elements):
        if element == "material":
            continue  # Material quantity has its own parameter: IS_material_quantity[UoM]

        # Element ID for E{id} format (1-based in Excel, 0-based in Python)
        element_id = elem_idx + 1

        # Try new format with "Fraction": IS_E2_Fraction[%]
        e_format_fraction = f"IS_E{element_id}_Fraction[%]"
        if e_format_fraction in available_params:
            param_type_map[element] = e_format_fraction
            continue

        # Try new E{id} format with element name in parentheses: IS_E2_[%](WC)
        e_format_with_name = f"IS_E{element_id}_[%]({element})"
        if e_format_with_name in available_params:
            param_type_map[element] = e_format_with_name
            continue

        # Try new E{id} format without parentheses: IS_E2[%]
        e_format_simple = f"IS_E{element_id}[%]"
        if e_format_simple in available_params:
            param_type_map[element] = e_format_simple
            continue

        # Try new E{id} format with underscore and brackets: IS_E2_[%]
        e_format_underscore = f"IS_E{element_id}_[%]"
        if e_format_underscore in available_params:
            param_type_map[element] = e_format_underscore
            continue

        # Fallback: Try standard naming: IS_{element}[%]
        standard_name = f"IS_{element}[%]"
        if standard_name in available_params:
            param_type_map[element] = standard_name
            continue

        # No match found - will be handled later with warning
        param_type_map[element] = None

    return param_type_map


def load_initial_stock_parameters(excel_data, elements=None):
    """Loads and parses initial stock configurations from the Excel file.

    This function reads the '2_4_Initial_Stock' sheet, which is expected
    to be in a long-table format. It groups parameters by Process_ID and
    parses them into a structured dictionary for each process.

    Now supports modular E1-E6 element naming convention, matching the system
    used for flows. Element compositions can be specified using E{id} format
    (e.g., IS_E2_[%](WC)) or legacy format (e.g., IS_WC[%]).

    Parameters
    ----------
    excel_data : dict
        A dictionary of DataFrames, where keys are sheet names.
    elements : list of str, optional
        List of element names (e.g., ['material', 'WC', 'DM', 'CC']).
        If None, defaults to ['material', 'WC', 'DM', 'CC'].

    Returns
    -------
    dict
        A dictionary where keys are process IDs and values are the parsed
        initial stock configuration dictionaries for that process.
    """
    # Default to legacy elements if not provided
    if elements is None:
        elements = ["material", "WC", "DM", "CC"]
        print(
            "  -> INFO: No elements list provided to initial stock loader, using default: ['material', 'WC', 'DM', 'CC']"
        )

    sheet_name = "2_4_Initial_Stock"
    print(f"--> Loading initial stock parameters from sheet '{sheet_name}'...")

    if sheet_name not in excel_data:
        print(
            f"--> INFO: Sheet '{sheet_name}' not found. No initial stocks will be loaded."
        )
        return {}

    df = excel_data[sheet_name]
    if df.empty:
        print(
            f"--> INFO: Sheet '{sheet_name}' is empty. No initial stocks will be loaded."
        )
        return {}

    # Validate required columns
    required_columns = ["Process_ID", "IS_Parameter_type", "IS_Parameter_Value"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(
            f"--> ERROR: Missing required columns in '{sheet_name}': {missing_columns}"
        )
        return {}

    # Clean data
    df = df.dropna(subset=["Process_ID", "IS_Parameter_type", "IS_Parameter_Value"])
    df["Process_ID"] = df["Process_ID"].astype(int)

    # IMPORTANT: Handle European decimal separator (comma) in parameter values
    # Convert IS_Parameter_Value to numeric, replacing commas with dots if needed
    def safe_float_conversion(value):
        """Safely convert value to float, handling comma as decimal separator.

        Returns None if conversion fails (e.g., for flow names like 'F_1_2').
        """
        if pd.isna(value):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        # If string, try to convert to float
        if isinstance(value, str):
            try:
                # Replace comma with dot for European decimal notation
                return float(value.replace(",", "."))
            except ValueError:
                # Not a numeric value (e.g., flow name "F_1_2")
                return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    # Apply conversion to ensure all numeric values are properly read
    df["IS_Parameter_Value_Numeric"] = df["IS_Parameter_Value"].apply(
        safe_float_conversion
    )

    # Build element-to-parameter mapping (E1-E6 system)
    element_param_map = _build_initial_stock_element_column_map(elements, df)
    print(f"  -> Element parameter mapping: {element_param_map}")

    initial_stock_configs = {}

    # Group by Process_ID
    for process_id, group in df.groupby("Process_ID"):
        config = {
            "process_id": process_id,
            "initial_stock_values": {},
            "outflow_configs": [],
            "elements": elements,  # Store elements list for later use
        }

        # Process each parameter
        for _, row in group.iterrows():
            param_name = str(row["IS_Parameter_type"]).strip()
            param_value_raw = row["IS_Parameter_Value"]  # Keep original for flow names
            param_value = row.get(
                "IS_Parameter_Value_Numeric"
            )  # Use numeric conversion for values
            unit = row.get("Unit", "")
            destination_process = row.get("Destination_Process", None)
            destination_flow = row.get("Destination_Flow", None)
            notes = row.get("Notes", "")

            # Handle material quantity (always required)
            if param_name == "IS_material_quantity[UoM]":
                if param_value is not None:
                    config["initial_stock_values"]["Initial_Stock_material"] = float(
                        param_value
                    )
                else:
                    print(
                        f"    WARNING: Process {process_id} has non-numeric material quantity: {param_value_raw}"
                    )
                continue

            # Handle element composition parameters using dynamic mapping
            handled = False
            for element, mapped_param in element_param_map.items():
                if mapped_param and param_name == mapped_param:
                    if param_value is not None:
                        config["initial_stock_values"][
                            f"Initial_Stock_{element}[%]"
                        ] = float(param_value)
                    else:
                        print(
                            f"    WARNING: Process {process_id} has non-numeric {element} value: {param_value_raw}"
                        )
                    handled = True
                    break

            if handled:
                continue

            # Handle consumption rate
            elif param_name == "Annual_Consumption_Rate[UoM/year]":
                if param_value is not None:
                    outflow_config = {
                        "parameter_name": "Annual_Consumption_Rate",
                        "parameter_value": float(param_value),
                        "unit": unit,
                        "destination_process": destination_process,  # From row data
                        "destination_flow": destination_flow,  # From row data
                        "notes": notes,
                    }
                    config["outflow_configs"].append(outflow_config)
                else:
                    print(
                        f"    WARNING: Process {process_id} has non-numeric consumption rate: {param_value_raw}"
                    )

            # Handle outflow destinations and splits
            elif param_name.startswith("IS_Outflow_") and not param_name.endswith(
                "_TC_"
            ):
                # Extract outflow number
                outflow_num = param_name.split("_")[-1]
                tc_param_name = f"IS_Outflow_TC_{outflow_num}"

                # Find corresponding TC value
                tc_row = group[group["IS_Parameter_type"] == tc_param_name]
                if not tc_row.empty:
                    tc_value_numeric = tc_row["IS_Parameter_Value_Numeric"].iloc[0]
                    if tc_value_numeric is None:
                        print(
                            f"    WARNING: Process {process_id} has non-numeric TC value for {tc_param_name}"
                        )
                        continue
                    tc_value = float(tc_value_numeric)

                    # Only process if this is a flow name (not a TC value)
                    if isinstance(param_value_raw, str) and str(
                        param_value_raw
                    ).startswith("F_"):
                        # Extract destination process from flow name (e.g., "F_1_2" -> destination = 2)
                        flow_parts = str(param_value_raw).split("_")
                        extracted_destination = None
                        if len(flow_parts) >= 3:
                            try:
                                extracted_destination = int(flow_parts[2])
                            except (ValueError, IndexError):
                                print(
                                    f"    WARNING: Could not parse destination process from flow name '{param_value_raw}'"
                                )

                        outflow_config = {
                            "parameter_name": "Outflow_Split[%]",
                            "parameter_value": tc_value * 100,  # Convert to percentage
                            "unit": "%",
                            "destination_process": extracted_destination,
                            "destination_flow": str(param_value_raw),
                            "notes": f"Outflow {outflow_num}",
                        }
                        config["outflow_configs"].append(outflow_config)

            # Handle other parameters
            else:
                config[
                    param_name.lower()
                    .replace(" ", "_")
                    .replace("[", "")
                    .replace("]", "")
                ] = {"value": param_value, "unit": unit, "notes": notes}

        # Validate configuration
        if _validate_initial_stock_config(config):
            initial_stock_configs[process_id] = config
            print(f"  -> Loaded initial stock config for Process {process_id}")
        else:
            print(
                f"  -> WARNING: Invalid initial stock config for Process {process_id}"
            )

    print(
        f"--> Successfully loaded initial stock configurations for {len(initial_stock_configs)} process(es)."
    )
    return initial_stock_configs


def _validate_initial_stock_config(config):
    """Validates a single initial stock configuration dictionary.

    Parameters
    ----------
    config : dict
        The initial stock configuration dictionary for a single process.

    Returns
    -------
    bool
        True if the configuration is valid, False otherwise.
    """
    # Check if we have at least the material amount
    if "Initial_Stock_material" not in config["initial_stock_values"]:
        return False

    # Check if outflow configs are valid
    if config["outflow_configs"]:
        consumption_rates = [
            oc
            for oc in config["outflow_configs"]
            if oc["parameter_name"] == "Annual_Consumption_Rate"
        ]
        if not consumption_rates:
            print(
                f"    WARNING: Process {config['process_id']} has outflow configs but no consumption rate"
            )
            return False

    return True


def apply_initial_stock_values(mfa_system, initial_stock_configs):
    """Applies the parsed initial stock values to the MFA system object.

    This function takes the parsed configurations and sets the stock values
    for the first time step (t=0) in the corresponding stock objects within
    the MFA system.

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        The MFA system object to be modified.
    initial_stock_configs : dict
        A dictionary of initial stock configurations, keyed by process ID.

    Returns
    -------
    odym.MFAsystem
        The modified MFA system with initial stock values set.
    """
    print("--> Applying initial stock values...")

    for process_id, config in initial_stock_configs.items():
        stock_s = mfa_system.StockDict.get(f"S_{process_id}")
        if stock_s is None:
            print(
                f"  -> WARNING: Stock S_{process_id} not found for Process {process_id}"
            )
            continue

        # Calculate initial stock values using the elements list stored in config
        elements = config.get("elements", ["material", "WC", "DM", "CC"])
        initial_values = _calculate_initial_stock_values(
            config["initial_stock_values"], elements
        )

        # Set initial stock values (first year only)
        stock_s.Values[0, :] = initial_values

        print(
            f"  -> Set initial stock for Process {process_id}: {initial_values[0]:.1f} Mg material"
        )

    print("--> Initial stock values applied.")
    return mfa_system


def _calculate_initial_stock_values(stock_values, elements):
    """Calculates the elemental composition of an initial stock.

    Based on the material quantity and content fractions, this function
    returns a vector with the calculated mass for each element. Now supports
    dynamic element lists.

    Element fractions should be entered as decimals (0-1 range), not percentages.
    For example: 0.7 for 70% water content, not 70.

    Parameters
    ----------
    stock_values : dict
        A dictionary of initial stock parameter values for one process,
        e.g., {"Initial_Stock_material": 100, "Initial_Stock_WC[%]": 0.7}.
    elements : list of str
        List of element names (e.g., ['material', 'WC', 'DM', 'CC']).

    Returns
    -------
    np.ndarray
        A 1D NumPy array representing the initial stock vector for all elements,
        in the same order as the elements list.
    """
    # Initialize result array
    result = np.zeros(len(elements))

    # Material is always first element
    material = stock_values.get("Initial_Stock_material", 0.0)
    result[0] = material

    # Calculate composition for other elements
    # NOTE: Element values are expected as FRACTIONS (0-1), not percentages (0-100)
    for idx, element in enumerate(elements[1:], start=1):
        # Get fraction for this element (default 0.0)
        element_fraction = stock_values.get(f"Initial_Stock_{element}[%]", 0.0)
        result[idx] = material * element_fraction

    return result


def process_initial_stock_outflows(mfa_system, initial_stock_configs):
    """Processes and creates the outflow flows from initial stocks.

    This function reads the outflow configurations (e.g., consumption rates,
    splits) and creates the necessary `Flow` objects in the MFA system.
    It does not calculate the flow values, which is handled by the solver.

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        The MFA system object to be modified.
    initial_stock_configs : dict
        A dictionary of initial stock configurations, keyed by process ID.

    Returns
    -------
    odym.MFAsystem
        The modified MFA system with new outflow objects added.
    """
    print("--> Processing initial stock outflows...")

    for process_id, config in initial_stock_configs.items():
        if not config["outflow_configs"]:
            continue

        # Get initial stock values
        stock_s = mfa_system.StockDict.get(f"S_{process_id}")
        if stock_s is None:
            continue

        initial_stock = stock_s.Values[0, :].copy()

        # Process outflow configurations
        outflow_flows = _create_outflow_flows(
            mfa_system, process_id, config["outflow_configs"], initial_stock
        )

        # Store outflow information for later use
        if not hasattr(mfa_system, "initial_stock_outflows"):
            mfa_system.initial_stock_outflows = {}
        mfa_system.initial_stock_outflows[process_id] = outflow_flows

        print(
            f"  -> Created {len(outflow_flows)} outflow flows for Process {process_id}"
        )

    # Initialize flow values using ODYM method with error handling
    try:
        mfa_system.Initialize_FlowValues()
        print("--> Initial stock flow values initialized.")
    except Exception as e:
        print(f"--> ERROR: Failed to initialize initial stock flow values: {e}")
        raise

    print("--> Initial stock outflows processed.")
    return mfa_system


def _create_outflow_flows(mfa_system, process_id, outflow_configs, initial_stock):
    """Creates all outflow flow objects for a single process's initial stock.

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        The MFA system object.
    process_id : int
        The ID of the process owning the initial stock.
    outflow_configs : list
        A list of outflow configuration dictionaries for this process.
    initial_stock : np.ndarray
        The initial stock vector for the process.

    Returns
    -------
    list
        A list of the newly created `odym.Flow` objects.
    """
    outflow_flows = []

    # Find consumption rate
    consumption_rate_config = next(
        (
            oc
            for oc in outflow_configs
            if oc["parameter_name"] == "Annual_Consumption_Rate"
        ),
        None,
    )
    if consumption_rate_config is None:
        print(f"    WARNING: No consumption rate found for Process {process_id}")
        return outflow_flows

    consumption_rate = consumption_rate_config["parameter_value"]

    # Find outflow splits
    split_configs = [
        oc for oc in outflow_configs if oc["parameter_name"] == "Outflow_Split[%]"
    ]

    if not split_configs:
        # No splits - create single outflow to first destination
        destination_process = consumption_rate_config["destination_process"]
        destination_flow = consumption_rate_config.get("destination_flow")

        # If destination_process is None, try to extract from destination_flow
        if destination_process is None and destination_flow:
            if isinstance(destination_flow, str) and destination_flow.startswith("F_"):
                flow_parts = destination_flow.split("_")
                if len(flow_parts) >= 3:
                    try:
                        destination_process = int(flow_parts[2])
                        print(
                            f"    -> Extracted destination process {destination_process} from flow name '{destination_flow}'"
                        )
                    except (ValueError, IndexError):
                        pass

        if destination_process is not None:
            flow_name = f"F_{process_id}_{destination_process}_stock"
            flow = _create_single_outflow_flow(
                mfa_system,
                flow_name,
                process_id,
                destination_process,
                initial_stock,
                consumption_rate,
            )
            if flow:
                outflow_flows.append(flow)
        else:
            print(
                f"    WARNING: No valid destination found for Process {process_id} consumption rate"
            )
    else:
        # Multiple splits - create multiple outflows
        total_split = sum(oc["parameter_value"] for oc in split_configs)

        for split_config in split_configs:
            split_pct = split_config["parameter_value"]
            destination_process = split_config["destination_process"]
            destination_flow = split_config.get("destination_flow")

            # If destination_process is None, try to extract from destination_flow
            if destination_process is None and destination_flow:
                if isinstance(destination_flow, str) and destination_flow.startswith(
                    "F_"
                ):
                    flow_parts = destination_flow.split("_")
                    if len(flow_parts) >= 3:
                        try:
                            destination_process = int(flow_parts[2])
                            print(
                                f"    -> Extracted destination process {destination_process} from split flow name '{destination_flow}'"
                            )
                        except (ValueError, IndexError):
                            pass

            if destination_process is not None:
                # Calculate split fraction
                split_fraction = (
                    split_pct / 100.0 if total_split > 0 else 1.0 / len(split_configs)
                )

                flow_name = f"F_{process_id}_{destination_process}_stock"
                flow = _create_single_outflow_flow(
                    mfa_system,
                    flow_name,
                    process_id,
                    destination_process,
                    initial_stock,
                    consumption_rate,
                    split_fraction,
                )
                if flow:
                    outflow_flows.append(flow)
            else:
                print(
                    f"    WARNING: Could not determine destination for outflow split from Process {process_id}"
                )

    return outflow_flows


def _create_single_outflow_flow(
    mfa_system,
    flow_name,
    process_id,
    destination_process,
    initial_stock,
    consumption_rate,
    split_fraction=1.0,
):
    """Creates and configures a single outflow flow from an initial stock.

    This function creates the `Flow` object if it doesn't exist and attaches the
    initial stock configuration to it. This configuration is later used by the
    solver to calculate the flow's values during each iteration.

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        The MFA system object.
    flow_name : str
        The name/ID for the new flow.
    process_id : int
        The ID of the source process (where the stock is).
    destination_process : int
        The ID of the destination process for the outflow.
    initial_stock : np.ndarray
        The initial stock vector of the source process.
    consumption_rate : float
        The annual consumption rate of the stock.
    split_fraction : float, optional
        The fraction of the total outflow directed to this specific flow.
        Default is 1.0.

    Returns
    -------
    odym.Flow or None
        The created and configured `odym.Flow` object, or None if creation fails.
    """
    # Create flow if it doesn't exist
    if flow_name not in mfa_system.FlowDict:
        mfa_system.FlowDict[flow_name] = msc.Flow(
            Name=flow_name, P_Start=process_id, P_End=destination_process, Indices="t,e"
        )

    flow = mfa_system.FlowDict[flow_name]

    # Initialize flow values using ODYM method (leave as None initially)
    # ODYM's Initialize_FlowValues() will handle this

    # Store initial stock configuration in external dict (ODYM compliance - no custom attributes)
    if not hasattr(mfa_system, "_initial_stock_configs"):
        mfa_system._initial_stock_configs = {}

    mfa_system._initial_stock_configs[flow_name] = {
        "initial_stock": initial_stock.copy(),
        "consumption_rate": consumption_rate,
        "split_fraction": split_fraction,
    }

    print(f"    -> Created flow {flow_name} (values will be set during solver)")
    return flow


def calculate_initial_stock_balances(mfa_system, initial_stock_configs):
    """Calculates the time-series stock balance for processes with initial stocks.

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        The MFA system object.
    initial_stock_configs : dict
        A dictionary of initial stock configurations, keyed by process ID.

    Returns
    -------
    odym.MFAsystem
        The modified MFA system with updated stock balance time-series.
    """
    print("--> Calculating initial stock balances...")

    for process_id, config in initial_stock_configs.items():
        stock_s = mfa_system.StockDict.get(f"S_{process_id}")
        if stock_s is None:
            continue

        # Get initial stock
        initial_stock = stock_s.Values[0, :].copy()

        # Calculate total outflow from initial stock
        total_outflow = np.zeros_like(initial_stock)
        if (
            hasattr(mfa_system, "initial_stock_outflows")
            and process_id in mfa_system.initial_stock_outflows
        ):
            for flow in mfa_system.initial_stock_outflows[process_id]:
                total_outflow += flow.Values[0, :]  # First year outflow

        # Update stock values (assuming constant consumption)
        n_years = len(mfa_system.IndexTable.Classification["Time"].Items)
        for t in range(n_years):
            remaining_stock = initial_stock - (total_outflow * t)
            stock_s.Values[t, :] = np.maximum(
                remaining_stock, 0
            )  # Prevent negative stocks

        print(f"  -> Updated stock balance for Process {process_id}")

    print("--> Initial stock balances calculated.")
    return mfa_system


def update_initial_stock_flows_during_solver(mfa_system):
    """Updates the values of initial stock outflow flows during solver iterations.

    This function is called during each solver iteration to calculate and set
    the values for flows originating from initial stocks, based on the
    configuration attached to the flow object.

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        The MFA system object.

    Returns
    -------
    odym.MFAsystem
        The modified MFA system with updated initial stock flow values.
    """
    if not hasattr(mfa_system, "initial_stock_outflows"):
        return mfa_system

    for process_id, outflow_flows in mfa_system.initial_stock_outflows.items():
        for flow in outflow_flows:
            # Read from external dict (ODYM compliance)
            config = getattr(mfa_system, "_initial_stock_configs", {}).get(flow.Name)
            if config:
                # Calculate annual consumption with split
                annual_consumption = (
                    config["initial_stock"]
                    * config["consumption_rate"]
                    * config["split_fraction"]
                )

                # Set flow values (constant over time)
                for t in range(len(flow.Values)):
                    flow.Values[t, :] = annual_consumption

    return mfa_system


def get_initial_stock_summary(mfa_system, initial_stock_configs):
    """Generates a summary dictionary of initial stock configurations and results.

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        The solved MFA system object.
    initial_stock_configs : dict
        A dictionary of initial stock configurations, keyed by process ID.

    Returns
    -------
    dict
        A summary dictionary containing key statistics about the initial stocks.
    """
    summary = {
        "total_processes": len(initial_stock_configs),
        "total_initial_material": 0.0,
        "total_annual_consumption": 0.0,
        "process_details": {},
    }

    for process_id, config in initial_stock_configs.items():
        stock_s = mfa_system.StockDict.get(f"S_{process_id}")
        if stock_s is None:
            continue

        initial_material = stock_s.Values[0, 0]
        summary["total_initial_material"] += initial_material

        # Calculate annual consumption
        annual_consumption = 0.0
        if (
            hasattr(mfa_system, "initial_stock_outflows")
            and process_id in mfa_system.initial_stock_outflows
        ):
            for flow in mfa_system.initial_stock_outflows[process_id]:
                annual_consumption += flow.Values[0, 0]

        summary["total_annual_consumption"] += annual_consumption

        summary["process_details"][process_id] = {
            "initial_material": initial_material,
            "annual_consumption": annual_consumption,
            "num_outflows": len(mfa_system.initial_stock_outflows.get(process_id, []))
            if hasattr(mfa_system, "initial_stock_outflows")
            else 0,
        }

    return summary
