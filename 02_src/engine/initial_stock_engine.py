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
import sys



import ODYM_Classes as msc


def load_initial_stock_parameters(excel_data):
    """Loads and parses initial stock configurations from the Excel file.

    This function reads the '2_4_Initial_Stock' sheet, which is expected
    to be in a long-table format. It groups parameters by Process_ID and
    parses them into a structured dictionary for each process.

    Parameters
    ----------
    excel_data : dict
        A dictionary of DataFrames, where keys are sheet names.

    Returns
    -------
    dict
        A dictionary where keys are process IDs and values are the parsed
        initial stock configuration dictionaries for that process.
    """
    sheet_name = "2_4_Initial_Stock"
    print(f"--> Loading initial stock parameters from sheet '{sheet_name}'...")
    
    if sheet_name not in excel_data:
        print(f"--> INFO: Sheet '{sheet_name}' not found. No initial stocks will be loaded.")
        return {}
    
    df = excel_data[sheet_name]
    if df.empty:
        print(f"--> INFO: Sheet '{sheet_name}' is empty. No initial stocks will be loaded.")
        return {}
    
    # Validate required columns
    required_columns = ["Process_ID", "IS_Parameter_type", "IS_Parameter_Value"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"--> ERROR: Missing required columns in '{sheet_name}': {missing_columns}")
        return {}
    
    # Clean data
    df = df.dropna(subset=["Process_ID", "IS_Parameter_type", "IS_Parameter_Value"])
    df["Process_ID"] = df["Process_ID"].astype(int)
    
    initial_stock_configs = {}
    
    # Group by Process_ID
    for process_id, group in df.groupby("Process_ID"):
        config = {
            "process_id": process_id,
            "initial_stock_values": {},
            "outflow_configs": []
        }
        
        # Process each parameter
        for _, row in group.iterrows():
            param_name = str(row["IS_Parameter_type"]).strip()
            param_value = row["IS_Parameter_Value"]
            unit = row.get("Unit", "")
            destination_process = row.get("Destination_Process", None)
            destination_flow = row.get("Destination_Flow", None)
            notes = row.get("Notes", "")
            
            # Handle initial stock composition parameters
            if param_name in ["IS_material_quantity[UoM]", "IS_WC[%]", "IS_DM[%]", "IS_CC[%]"]:
                # Map to standard names
                if param_name == "IS_material_quantity[UoM]":
                    config["initial_stock_values"]["Initial_Stock_material"] = float(param_value)
                elif param_name == "IS_WC[%]":
                    config["initial_stock_values"]["Initial_Stock_WC[%]"] = float(param_value)
                elif param_name == "IS_DM[%]":
                    config["initial_stock_values"]["Initial_Stock_DM[%]"] = float(param_value)
                elif param_name == "IS_CC[%]":
                    config["initial_stock_values"]["Initial_Stock_CC[%]"] = float(param_value)
            
            # Handle consumption rate
            elif param_name == "Annual_Consumption_Rate[UoM/year]":
                outflow_config = {
                    "parameter_name": "Annual_Consumption_Rate",
                    "parameter_value": float(param_value),
                    "unit": unit,
                    "destination_process": None,  # Will be set by outflow parameters
                    "destination_flow": None,
                    "notes": notes
                }
                config["outflow_configs"].append(outflow_config)
            
            # Handle outflow destinations and splits
            elif param_name.startswith("IS_Outflow_") and not param_name.endswith("_TC_"):
                # Extract outflow number
                outflow_num = param_name.split("_")[-1]
                tc_param_name = f"IS_Outflow_TC_{outflow_num}"
                
                # Find corresponding TC value
                tc_row = group[group["IS_Parameter_type"] == tc_param_name]
                if not tc_row.empty:
                    tc_value = float(tc_row["IS_Parameter_Value"].iloc[0])
                    
                    # Only process if this is a flow name (not a TC value)
                    if isinstance(param_value, str) and param_value.startswith("F_"):
                        outflow_config = {
                            "parameter_name": "Outflow_Split[%]",
                            "parameter_value": tc_value * 100,  # Convert to percentage
                            "unit": "%",
                            "destination_process": None,  # Will be determined from flow name
                            "destination_flow": str(param_value),
                            "notes": f"Outflow {outflow_num}"
                        }
                        config["outflow_configs"].append(outflow_config)
            
            # Handle other parameters
            else:
                config[param_name.lower().replace(" ", "_").replace("[", "").replace("]", "")] = {
                    "value": param_value,
                    "unit": unit,
                    "notes": notes
                }
        
        # Validate configuration
        if _validate_initial_stock_config(config):
            initial_stock_configs[process_id] = config
            print(f"  -> Loaded initial stock config for Process {process_id}")
        else:
            print(f"  -> WARNING: Invalid initial stock config for Process {process_id}")
    
    print(f"--> Successfully loaded initial stock configurations for {len(initial_stock_configs)} process(es).")
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
        consumption_rates = [oc for oc in config["outflow_configs"] if oc["parameter_name"] == "Annual_Consumption_Rate"]
        if not consumption_rates:
            print(f"    WARNING: Process {config['process_id']} has outflow configs but no consumption rate")
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
            print(f"  -> WARNING: Stock S_{process_id} not found for Process {process_id}")
            continue
        
        # Calculate initial stock values
        initial_values = _calculate_initial_stock_values(config["initial_stock_values"])
        
        # Set initial stock values (first year only)
        stock_s.Values[0, :] = initial_values
        
        print(f"  -> Set initial stock for Process {process_id}: {initial_values[0]:.1f} Mg material")
    
    print("--> Initial stock values applied.")
    return mfa_system


def _calculate_initial_stock_values(stock_values):
    """Calculates the elemental composition of an initial stock.

    Based on the material quantity and content percentages, this function
    returns a vector with the calculated mass for each element.

    Parameters
    ----------
    stock_values : dict
        A dictionary of initial stock parameter values for one process,
        e.g., {"Initial_Stock_material": 100, "Initial_Stock_WC[%]": 10}.

    Returns
    -------
    np.ndarray
        A 1D NumPy array representing the initial stock vector for all elements.
    """
    # Default values
    material = stock_values.get("Initial_Stock_material", 0.0)
    wc_pct = stock_values.get("Initial_Stock_WC[%]", 0.0) / 100.0
    dm_pct = stock_values.get("Initial_Stock_DM[%]", 100.0) / 100.0
    cc_pct = stock_values.get("Initial_Stock_CC[%]", 0.0) / 100.0
    
    # Calculate elemental compositions
    wc_amount = material * wc_pct
    dm_amount = material * dm_pct
    cc_amount = material * cc_pct
    
    return np.array([material, wc_amount, dm_amount, cc_amount])


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
        outflow_flows = _create_outflow_flows(mfa_system, process_id, config["outflow_configs"], initial_stock)
        
        # Store outflow information for later use
        if not hasattr(mfa_system, 'initial_stock_outflows'):
            mfa_system.initial_stock_outflows = {}
        mfa_system.initial_stock_outflows[process_id] = outflow_flows
        
        print(f"  -> Created {len(outflow_flows)} outflow flows for Process {process_id}")
    
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
    consumption_rate_config = next((oc for oc in outflow_configs if oc["parameter_name"] == "Annual_Consumption_Rate"), None)
    if consumption_rate_config is None:
        print(f"    WARNING: No consumption rate found for Process {process_id}")
        return outflow_flows
    
    consumption_rate = consumption_rate_config["parameter_value"]
    
    # Find outflow splits
    split_configs = [oc for oc in outflow_configs if oc["parameter_name"] == "Outflow_Split[%]"]
    
    if not split_configs:
        # No splits - create single outflow to first destination
        destination_process = consumption_rate_config["destination_process"]
        if destination_process is not None:
            flow_name = f"F_{process_id}_{destination_process}_stock"
            flow = _create_single_outflow_flow(mfa_system, flow_name, process_id, destination_process, initial_stock, consumption_rate)
            if flow:
                outflow_flows.append(flow)
    else:
        # Multiple splits - create multiple outflows
        total_split = sum(oc["parameter_value"] for oc in split_configs)
        
        for split_config in split_configs:
            split_pct = split_config["parameter_value"]
            destination_process = split_config["destination_process"]
            
            if destination_process is not None:
                # Calculate split fraction
                split_fraction = split_pct / 100.0 if total_split > 0 else 1.0 / len(split_configs)
                
                flow_name = f"F_{process_id}_{destination_process}_stock"
                flow = _create_single_outflow_flow(mfa_system, flow_name, process_id, destination_process, initial_stock, consumption_rate, split_fraction)
                if flow:
                    outflow_flows.append(flow)
    
    return outflow_flows


def _create_single_outflow_flow(mfa_system, flow_name, process_id, destination_process, initial_stock, consumption_rate, split_fraction=1.0):
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
            Name=flow_name,
            P_Start=process_id,
            P_End=destination_process,
            Indices="t,e"
        )
    
    flow = mfa_system.FlowDict[flow_name]
    
    # Initialize flow values using ODYM method (leave as None initially)
    # ODYM's Initialize_FlowValues() will handle this
    
    # Store initial stock configuration in external dict (ODYM compliance - no custom attributes)
    if not hasattr(mfa_system, '_initial_stock_configs'):
        mfa_system._initial_stock_configs = {}
    
    mfa_system._initial_stock_configs[flow_name] = {
        'initial_stock': initial_stock.copy(),
        'consumption_rate': consumption_rate,
        'split_fraction': split_fraction
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
        if hasattr(mfa_system, 'initial_stock_outflows') and process_id in mfa_system.initial_stock_outflows:
            for flow in mfa_system.initial_stock_outflows[process_id]:
                total_outflow += flow.Values[0, :]  # First year outflow
        
        # Update stock values (assuming constant consumption)
        n_years = len(mfa_system.IndexTable.Classification["Time"].Items)
        for t in range(n_years):
            remaining_stock = initial_stock - (total_outflow * t)
            stock_s.Values[t, :] = np.maximum(remaining_stock, 0)  # Prevent negative stocks
        
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
    if not hasattr(mfa_system, 'initial_stock_outflows'):
        return mfa_system
    
    for process_id, outflow_flows in mfa_system.initial_stock_outflows.items():
        for flow in outflow_flows:
            # Read from external dict (ODYM compliance)
            config = getattr(mfa_system, '_initial_stock_configs', {}).get(flow.Name)
            if config:
                # Calculate annual consumption with split
                annual_consumption = (config['initial_stock'] * 
                                    config['consumption_rate'] * 
                                    config['split_fraction'])
                
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
        "process_details": {}
    }
    
    for process_id, config in initial_stock_configs.items():
        stock_s = mfa_system.StockDict.get(f"S_{process_id}")
        if stock_s is None:
            continue
        
        initial_material = stock_s.Values[0, 0]
        summary["total_initial_material"] += initial_material
        
        # Calculate annual consumption
        annual_consumption = 0.0
        if hasattr(mfa_system, 'initial_stock_outflows') and process_id in mfa_system.initial_stock_outflows:
            for flow in mfa_system.initial_stock_outflows[process_id]:
                annual_consumption += flow.Values[0, 0]
        
        summary["total_annual_consumption"] += annual_consumption
        
        summary["process_details"][process_id] = {
            "initial_material": initial_material,
            "annual_consumption": annual_consumption,
            "num_outflows": len(mfa_system.initial_stock_outflows.get(process_id, [])) if hasattr(mfa_system, 'initial_stock_outflows') else 0
        }
    
    return summary
