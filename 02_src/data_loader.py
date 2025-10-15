# -*- coding: utf-8 -*-
"""
Data Loader Module for the BioDYM MFA Model.

This file contains all functions responsible for reading, validating, and
parsing the input data from the Excel template file. It acts as the
interface between the raw data and the core model logic.

UPDATED: Added column name mapping to handle naming convention changes.
"""

import pandas as pd
import numpy as np

# Import ODYM classes only when needed
try:
    import ODYM_Classes as msc
    ODYM_AVAILABLE = True
except ImportError:
    ODYM_AVAILABLE = False
    msc = None


# Column name mapping for backward compatibility and naming convention updates
COLUMN_NAME_MAPPING = {
    # Sheet: {old_name: new_name}
    "1_1_Definition_Flows": {
        "Flow_WC_ID ": "Flow_WC_ID",  # Remove trailing space
        # New [%] columns are already correctly named
    },
    "1_2_Data_Flows": {
        "Flow_Data_Year": "Flow_Data_Year",  # Keep as is
        "Flow_Material": "Flow_Material",  # Keep as is
        "WC_[%]": "WC_[%]",  # Keep as is
        "DM_[%]": "DM_[%]",  # Keep as is
        "CC_[%]": "CC_[%]",  # Keep as is
        "Author_Source": "Author_Source",  # Keep as is
        "Type_Source": "Type_Source",  # Keep as is
    },
    "2_1_Definition_Processes": {
        "Nr. Outflows": "Outflow_count",  # Standardize naming
    },
    "2_2_static_TCs": {
        "Nr. Outflows": "Outflow_count",  # Standardize naming
        "Titel_Source": "Titel_source",  # Standardize case
        "Author_Source": "Author_source",  # Standardize case
    },
    "2_3_dynamic_TCs": {
        "Nr. Outflows": "Outflow_count",  # Standardize naming
        "Titel_Source": "Titel_source",  # Standardize case
        "Author_Source": "Author_source",  # Standardize case
    },
    "2_4_Initial_Stock": {
        "Nr. Outflows": "Outflow_count",  # Standardize naming
        "Initial_Stock_WC[%]": "Initial_Stock_WC[%]",  # Keep as is
        "Initial_Stock_DM[%]": "Initial_Stock_DM[%]",  # Keep as is
        "Initial_Stock_CC[%]": "Initial_Stock_CC[%]",  # Keep as is
    },
    "3_1_Definition_DSM": {
        "Inflow_Split_[%]": "Inflow_Split_[%]",  # Keep as is
        "Lifetime_Type": "Lifetime_Type",  # Keep as is
        "Lifetime_Mean": "Lifetime_Mean",  # Keep as is
        "Lifetime_StdDev": "Lifetime_StdDev",  # Keep as is
        "Category_Name": "Category_Name",  # Keep as is
        "Category_ID": "Category_ID",  # Keep as is
        "DSM_Parameter": "DSM_Parameter_type",  # Updated to new name
        "DSM_Value": "DSM_Value",  # Keep as is
        "DSM_material_count": "DSM_material_count",  # New column
        "DSM_Parameter_ID": "DSM_Parameter_ID",  # New column
    },
    "3_2_Definition_FOMP": {
        "Pool_ID": "Pool_ID",  # Keep as is
        "Parameter_Name": "Parameter_Name",  # Keep as is
        "Value": "Value",  # Keep as is
        "FOMP_Parameter": "FOMP_Parameter_type",  # Updated to new name
        "FOMP_Value": "FOMP_Parameter_Value",  # Updated to new name
        "Nr._Decay_Pools": "Nr._Decay_Pools",  # New column
        "Pool": "Pool",  # New column
        "Decay_Pool_count": "Decay_Pool_count",  # New column
        "FOMP_Parameter_ID": "FOMP_Parameter_ID",  # New column
    },
    # Add more mappings as needed
}

# Sheet name mapping for backward compatibility
SHEET_NAME_MAPPING = {
    "PX - Template": "PX_Template",  # Standardize separator
    "2_3_static_TCs": "2_2_static_TCs",  # Handle sheet renumbering
    # Add more mappings as needed
}


def normalize_column_names(df, sheet_name):
    """
    Normalizes column names in a DataFrame based on the column mapping.
    
    Args:
        df (pd.DataFrame): The DataFrame to normalize
        sheet_name (str): The name of the sheet
        
    Returns:
        pd.DataFrame: DataFrame with normalized column names
    """
    if sheet_name in COLUMN_NAME_MAPPING:
        mapping = COLUMN_NAME_MAPPING[sheet_name]
        df = df.rename(columns=mapping)
    return df


def normalize_sheet_names(excel_data_dict):
    """
    Normalizes sheet names in the Excel data dictionary.
    
    Args:
        excel_data_dict (dict): Dictionary of DataFrames from Excel
        
    Returns:
        dict: Dictionary with normalized sheet names
    """
    normalized_data = {}
    for sheet_name, df in excel_data_dict.items():
        # Normalize sheet name
        normalized_sheet_name = SHEET_NAME_MAPPING.get(sheet_name, sheet_name)
        
        # Normalize column names
        df_normalized = normalize_column_names(df, sheet_name)
        
        normalized_data[normalized_sheet_name] = df_normalized
    
    return normalized_data


def validate_input_data(excel_data_dict):
    """
    Checks if the loaded Excel data has the expected structure.
    Raises a ValueError with a clear error message if something is missing.

    Args:
        excel_data_dict (dict): A dictionary where keys are sheet names and
                                values are pandas DataFrames.
    """
    print("--> Validating input data structure...")

    # Define the minimum required structure for the model to run.
    # Support both new unified columns and legacy columns for backward compatibility
    REQUIRED_STRUCTURE = {
        "1_1_Definition_Flows": ["Flow_ID", "Flow_Name", "Flow_Output_Process_ID", "Input_Process_ID", "Flow_WC[%]", "Flow_DM[%]", "Flow_CC_DM[%]"],
        "1_2_Data_Flows": ["Flow_ID", "Flow_Data_Year", "Flow_Material"],
        "2_1_Definition_Processes": ["ID", "Process_Name", "Process_Logic"],
        "2_2_static_TCs": ["Flow_ID", "Process_ID", "TC_material_ID", "TC_Value_material"],
        "2_3_dynamic_TCs": ["TC_material_ID", "TC_Value_material", "Year"],
        "2_4_Initial_Stock": [
            "Process_ID",
            "IS_Parameter_type", 
            "IS_Parameter_Value",
        ],
    }

    for sheet_name, required_columns in REQUIRED_STRUCTURE.items():
        if sheet_name not in excel_data_dict:
            # TC sheets are optional - only required if processes use TCs
            if sheet_name in ["2_2_static_TCs", "2_3_dynamic_TCs"]:
                print(f"  -> Optional sheet '{sheet_name}' not found (TCs may not be used)")
                continue
            else:
                raise ValueError(
                    f"ERROR: The required sheet '{sheet_name}' was not found in the Excel file!"
                )

        existing_columns = excel_data_dict[sheet_name].columns
        
        # Special handling for process definition sheet to support both unified and legacy columns
        if sheet_name == "2_1_Definition_Processes":
            # Check for unified columns first
            unified_columns = ["TC_Configuration", "Stock_Configuration"]
            legacy_columns = ["TC?", "TC_Type", "Stock?", "Initial_Stock?"]
            
            has_unified = all(col in existing_columns for col in unified_columns)
            has_legacy = all(col in existing_columns for col in legacy_columns)
            
            if not has_unified and not has_legacy:
                missing_unified = [col for col in unified_columns if col not in existing_columns]
                missing_legacy = [col for col in legacy_columns if col not in existing_columns]
                raise ValueError(
                    f"ERROR: Sheet '{sheet_name}' must have either unified columns {unified_columns} "
                    f"OR legacy columns {legacy_columns}. "
                    f"Missing unified: {missing_unified}, Missing legacy: {missing_legacy}"
                )
            elif has_unified:
                print(f"  -> Using unified configuration columns in '{sheet_name}'")
            elif has_legacy:
                print(f"  -> Using legacy configuration columns in '{sheet_name}'")
        else:
            # Standard validation for other sheets
            for col in required_columns:
                if col not in existing_columns:
                    raise ValueError(
                        f"ERROR: The required column '{col}' is missing from sheet '{sheet_name}'!"
                    )

    print("--> Input data validation successful.")


def validate_process_logic(excel_data):
    """
    Validates that processes with Input/Output logic are configured correctly.
    
    Args:
        excel_data (dict): Dictionary of DataFrames from Excel.
    """
    print("--> Validating Process_Logic configuration...")
    
    process_defs = excel_data.get('2_1_Definition_Processes')
    flows_defs = excel_data.get('1_1_Definition_Flows')
    
    if process_defs is None or flows_defs is None:
        print("--> WARNING: Cannot validate Process_Logic - missing required sheets.")
        return
    
    # Get all process IDs and their logic
    process_logic_map = {}
    for _, row in process_defs.iterrows():
        if pd.notna(row.get('Process_ID')):
            process_logic_map[int(row['Process_ID'])] = str(row.get('Process_Logic', '')).strip()
    
    # Get inflow/outflow connections
    inflows_by_process = {}
    outflows_by_process = {}
    
    for _, row in flows_defs.iterrows():
        if pd.notna(row.get('Flow_Output_Process_ID')) and pd.notna(row.get('Input_Process_ID')):
            start_id = int(row['Flow_Output_Process_ID'])
            end_id = int(row['Input_Process_ID'])
            
            if start_id not in outflows_by_process:
                outflows_by_process[start_id] = []
            outflows_by_process[start_id].append(row['Flow_ID'])
            
            if end_id not in inflows_by_process:
                inflows_by_process[end_id] = []
            inflows_by_process[end_id].append(row['Flow_ID'])
    
    # Validate Input processes (should have no inflows)
    input_processes = [pid for pid, logic in process_logic_map.items() if logic == 'Input']
    for pid in input_processes:
        if pid in inflows_by_process:
            print(f"--> WARNING: Input process {pid} has inflows: {inflows_by_process[pid]}")
        else:
            print(f"--> OK: Input process {pid} correctly has no inflows")
    
    # Validate Output processes (should have no outflows)
    output_processes = [pid for pid, logic in process_logic_map.items() if logic == 'Output']
    for pid in output_processes:
        if pid in outflows_by_process:
            print(f"--> WARNING: Output process {pid} has outflows: {outflows_by_process[pid]}")
        else:
            print(f"--> OK: Output process {pid} correctly has no outflows")
    
    print("--> Process_Logic validation completed.")
    return process_logic_map


def validate_unified_configuration(excel_data):
    """
    Validates the unified configuration columns (TC_Configuration, Stock_Configuration).
    
    Args:
        excel_data (dict): Dictionary of DataFrames from Excel.
    """
    print("--> Validating unified configuration columns...")
    
    process_defs = excel_data.get('2_1_Definition_Processes')
    if process_defs is None:
        print("--> WARNING: Cannot validate unified configuration - missing process definitions.")
        return
    
    # Check TC_Configuration consistency
    print("--> Checking TC_Configuration consistency...")
    tc_issues = []
    for _, row in process_defs.iterrows():
        if pd.notna(row.get('Process_ID')):
            process_id = int(row['Process_ID'])
            process_logic = str(row.get('Process_Logic', '')).strip()
            tc_config = str(row.get('TC_Configuration', '')).strip()
            
            # DSM processes should have Static TC_Configuration
            if process_logic == 'DSM' and tc_config != 'Static':
                tc_issues.append(f'Process {process_id}: DSM with {tc_config} TC_Configuration (should be Static)')
            
            # Input/Output processes should have Static TC_Configuration
            if process_logic in ['Input', 'Output'] and tc_config != 'Static':
                tc_issues.append(f'Process {process_id}: {process_logic} with {tc_config} TC_Configuration (should be Static)')
    
    if tc_issues:
        print("--> TC_Configuration issues found:")
        for issue in tc_issues:
            print(f"    - {issue}")
    else:
        print("--> TC_Configuration is consistent! ✅")
    
    # Check Stock_Configuration consistency
    print("--> Checking Stock_Configuration consistency...")
    stock_issues = []
    for _, row in process_defs.iterrows():
        if pd.notna(row.get('Process_ID')):
            process_id = int(row['Process_ID'])
            process_logic = str(row.get('Process_Logic', '')).strip()
            stock_config = str(row.get('Stock_Configuration', '')).strip()
            
            # DSM processes should have Stock
            if process_logic == 'DSM' and stock_config != 'Stock':
                stock_issues.append(f'Process {process_id}: DSM with {stock_config} Stock_Configuration (should be Stock)')
            
            # Output processes should have Stock
            if process_logic == 'Output' and stock_config != 'Stock':
                stock_issues.append(f'Process {process_id}: Output with {stock_config} Stock_Configuration (should be Stock)')
    
    if stock_issues:
        print("--> Stock_Configuration issues found:")
        for issue in stock_issues:
            print(f"    - {issue}")
    else:
        print("--> Stock_Configuration is consistent! ✅")
    
    print("--> Unified configuration validation completed.")


def load_tc_parameters(all_excel_data, elements, time_vector):
    """
    Loads transfer coefficients based on the unified TC_Configuration structure.
    Uses TC_Configuration column to determine TC loading strategy.
    
    TC Configuration:
    - TC_Configuration = "Static" -> Load from 2_2_static_TCs
    - TC_Configuration = "Dynamic" -> Load from 2_3_dynamic_TCs
    - TC_Configuration = "None" or missing -> Skip TCs
    - Process_Logic = "Input", "Output", "Pass-through" -> Skip TCs (regardless of TC_Configuration)

    Args:
        all_excel_data (dict): Dictionary of DataFrames from Excel.
        elements (list): List of element names (e.g., ['material', 'WC', 'DM', 'CC']).
        time_vector (list): List of years for the analysis.

    Returns:
        dict: A dictionary of ODYM Parameter objects for all TCs.
    """
    if not ODYM_AVAILABLE:
        print("--> WARNING: ODYM_Classes not available. TC parameters cannot be loaded.")
        return {}
    
    print("--> Loading Transfer Coefficients using unified TC_Configuration...")
    
    process_defs = all_excel_data.get('2_1_Definition_Processes')
    static_tc_defs = all_excel_data.get('2_2_static_TCs')
    dynamic_tc_defs = all_excel_data.get('2_3_dynamic_TCs')

    if process_defs is None:
        print("-> No Process definitions found. Skipping TC loading.")
        return {}

    # Create process type mapping based on TC_Configuration column
    process_tc_types = {}
    for _, row in process_defs.iterrows():
        process_id = row.get('Process_ID')
        process_logic = str(row.get('Process_Logic', '')).strip()
        tc_config = str(row.get('TC_Configuration', '')).strip()
        
        # Skip TCs for Input, Output, and Pass-through processes regardless of TC_Configuration
        if pd.notna(process_id) and process_logic in ['Input', 'Output', 'Pass-through']:
            print(f"--> INFO: Process {process_id} ({process_logic}) - skipping TCs (process type)")
            continue
            
        # Only processes with Splitter, Transformer, or DSM logic can have TCs
        if pd.notna(process_id) and process_logic in ['Splitter', 'Transformer', 'DSM']:
            if tc_config in ['Static', 'Dynamic']:
                process_tc_types[int(process_id)] = tc_config
            else:
                print(f"--> WARNING: Process {process_id} ({process_logic}) has TC_Configuration='{tc_config}' - skipping TCs")

    tc_params = {}
    param_id_counter = 1000

    # Process Static TCs
    static_processes = [pid for pid, tc_type in process_tc_types.items() if tc_type == 'Static']
    if static_processes and static_tc_defs is not None:
        print(f"  -> Processing static TCs for {len(static_processes)} processes...")
        for _, row in static_tc_defs.iterrows():
            process_id = row.get('Process_ID')
            if pd.isna(process_id) or int(process_id) not in static_processes:
                continue

            for element in elements:
                param_name_col = f'TC_{element}_ID'
                param_value_col = f'TC_Value_{element}'
                
                if param_name_col in row and pd.notna(row[param_name_col]) and param_value_col in row and pd.notna(row[param_value_col]):
                    param_name = row[param_name_col]
                    value = row[param_value_col]
                    
                    if param_name not in tc_params:
                        tc_params[param_name] = msc.Parameter(Name=param_name, ID=param_id_counter, Values=value, Unit="1")
                        param_id_counter += 1
                        print(f"    -> Loaded static TC: {param_name} = {value}")
                    else:
                        print(f"⚠️ Warning: Duplicate static TC parameter name found: {param_name}. Using first value found.")

    # Process Dynamic TCs
    dynamic_processes = [pid for pid, tc_type in process_tc_types.items() if tc_type == 'Dynamic']
    if dynamic_processes and dynamic_tc_defs is not None:
        print(f"  -> Processing dynamic TCs for {len(dynamic_processes)} processes...")
        
        # Group dynamic TC data by parameter name
        dynamic_tc_data = dynamic_tc_defs[['TC_material_ID', 'TC_Value_material', 'Year']].dropna()
        
        for param_name in dynamic_tc_data['TC_material_ID'].unique():
            tc_points = dynamic_tc_data[dynamic_tc_data['TC_material_ID'] == param_name]
            
            # Create time series
            ts = pd.Series(tc_points['TC_Value_material'].values, index=tc_points['Year'])
            
            # Reindex to full time vector and interpolate
            ts_full = ts.reindex(time_vector)
            ts_interpolated = ts_full.interpolate(method="linear", limit_direction="both")
            
            # Handle edge cases where interpolation might fail
            if ts_interpolated.isna().any():
                ts_interpolated = ts_interpolated.ffill().bfill()
            
            tc_params[param_name] = msc.Parameter(Name=param_name, ID=param_id_counter, Values=ts_interpolated.to_numpy(), Unit="1")
            param_id_counter += 1
            print(f"    -> Loaded dynamic TC: {param_name} ({len(tc_points)} data points -> {len(ts_interpolated)} time steps)")

    print(f"--> TC loading completed: {len(tc_params)} parameters loaded")
    return tc_params


def load_dsm_parameters(excel_data):
    """
    Reads the '3_1_Definition_DSM' sheet and creates the DSM_PARAMS dictionary.
    Uses Process_Logic column from the main process sheet to identify DSM processes.
    Supports both the old category-based format and the new parameter-based format.
    """
    sheet_name = "3_1_Definition_DSM"
    main_sheet_name = "2_1_Definition_Processes"
    print(f"--> Loading DSM parameters from sheet '{sheet_name}'...")

    if sheet_name not in excel_data:
        print(f"--> INFO: Sheet '{sheet_name}' not found. Using empty DSM configuration.")
        return {}

    df_dsm = excel_data[sheet_name]
    if "Process_ID" not in df_dsm.columns:
        print(f"--> FATAL ERROR: Column 'Process_ID' not found in sheet '{sheet_name}'.")
        return {}

    # Get DSM process IDs from the main process sheet
    dsm_process_ids = []
    if main_sheet_name in excel_data:
        main_df = excel_data[main_sheet_name]
        if 'Process_Logic' in main_df.columns:
            dsm_processes = main_df[main_df['Process_Logic'] == 'DSM']
            dsm_process_ids = dsm_processes['Process_ID'].dropna().astype(int).tolist()
            print(f"--> Using Process_Logic column from main sheet to identify DSM processes: {dsm_process_ids}")
        elif 'DSM?' in main_df.columns:
            dsm_processes = main_df[main_df['DSM?'] == 'Yes']
            dsm_process_ids = dsm_processes['Process_ID'].dropna().astype(int).tolist()
            print(f"--> Using legacy DSM? column from main sheet to identify DSM processes: {dsm_process_ids}")
    
    if not dsm_process_ids:
        print(f"--> INFO: No DSM processes found in main sheet.")
        return {}

    # Filter DSM sheet data for identified DSM processes
    dsm_df = df_dsm[df_dsm['Process_ID'].isin(dsm_process_ids)].copy()
    if dsm_df.empty:
        print(f"--> INFO: No DSM parameter data found for identified DSM processes.")
        return {}

    dsm_df = dsm_df.dropna(subset=["Process_ID"])
    dsm_df["Process_ID"] = dsm_df["Process_ID"].astype(int)

    dsm_params = {}
    
    for process_id in dsm_df['Process_ID'].unique():
        process_data = dsm_df[dsm_df['Process_ID'] == process_id]
        
        # Check if this is the new parameter-based format
        if 'DSM_Parameter_type' in process_data.columns and 'DSM_Value' in process_data.columns:
            dsm_params[process_id] = _parse_parameter_based_dsm(process_data)
        else:
            # Fall back to old category-based format
            dsm_params[process_id] = _parse_category_based_dsm(process_data)

    print(f"--> Successfully loaded configurations for {len(dsm_params)} DSM process(es).")
    return dsm_params


def load_stock_parameters(excel_data):
    """
    Reads stock configuration from the main process sheet using Stock_Configuration column.
    Uses Stock_Configuration column to identify processes that need stock management.
    
    Stock Configuration:
    - Stock_Configuration = "Stock" -> Process has stock management
    - Stock_Configuration = "No_Stock" -> Process has no stock management
    """
    main_sheet_name = "2_1_Definition_Processes"
    print(f"--> Loading Stock configuration from sheet '{main_sheet_name}'...")

    if main_sheet_name not in excel_data:
        print(f"--> INFO: Sheet '{main_sheet_name}' not found. Using empty stock configuration.")
        return {}

    main_df = excel_data[main_sheet_name]
    if "Process_ID" not in main_df.columns:
        print(f"--> FATAL ERROR: Column 'Process_ID' not found in sheet '{main_sheet_name}'.")
        return {}

    # Get stock configuration from Stock_Configuration column
    stock_processes = main_df[main_df['Stock_Configuration'] == 'Stock']
    stock_process_ids = stock_processes['Process_ID'].dropna().astype(int).tolist()
    
    print(f"--> Using Stock_Configuration column to identify stock processes: {stock_process_ids}")
    
    if not stock_process_ids:
        print(f"--> INFO: No stock processes found.")
        return {}

    # Create stock configuration dictionary
    stock_config = {}
    for process_id in stock_process_ids:
        process_info = main_df[main_df['Process_ID'] == process_id].iloc[0]
        stock_config[process_id] = {
            "process_name": process_info.get('Process_Name', f'Process_{process_id}'),
            "process_logic": process_info.get('Process_Logic', 'Unknown'),
            "stock_configuration": process_info.get('Stock_Configuration', 'Stock')
        }

    print(f"--> Successfully loaded stock configuration for {len(stock_config)} process(es).")
    return stock_config


def _parse_fomp_parameters(process_data):
    """
    Parse FOMP parameters from the process data.
    This is a placeholder implementation - FOMP parsing logic needs to be defined.
    """
    # TODO: Implement FOMP parameter parsing based on your FOMP requirements
    return {
        "process_type": "FOMP",
        "parameters": process_data.to_dict('records')
    }


def _parse_parameter_based_dsm(process_data):
    """
    Parse DSM parameters from the new parameter-based format.
    Each row represents a single parameter for a specific category.
    """
    categories = {}
    
    for _, row in process_data.iterrows():
        if pd.isna(row['DSM_Parameter_type']) or pd.isna(row['DSM_Value']):
            continue
            
        param_name = str(row['DSM_Parameter_type'])
        
        # Extract category number from parameter name
        if '_Cat_' in param_name:
            try:
                cat_num = int(param_name.split('_Cat_')[1])
                param_base = param_name.split('_Cat_')[0]
                
                if cat_num not in categories:
                    categories[cat_num] = {}
                
                # Map parameter to value
                categories[cat_num][param_base] = row['DSM_Value']
                
            except (ValueError, IndexError):
                print(f"--> WARNING: Could not parse parameter name: {param_name}")
                continue
        else:
            # Handle format without _Cat_ pattern - group by category based on order
            # This assumes categories are grouped together in the data
            if 'DSM_Category_Name' in param_name:
                # This is a category name row - start a new category
                category_name = str(row['DSM_Value'])
                if category_name not in categories:
                    categories[category_name] = {}
            else:
                # This is a parameter row - add to the current category
                # Find the most recent category (last one in the dict)
                if categories:
                    current_category = list(categories.keys())[-1]
                    categories[current_category][param_name] = row['DSM_Value']
    
    if not categories:
        print(f"--> WARNING: No valid DSM parameters found for process {process_data['Process_ID'].iloc[0]}")
        return {}
    
    # Convert to expected format
    sorted_categories = sorted(categories.items())
    
    # Extract basic parameters
    inflow_splits = []
    lifetime_types = []
    lifetime_means = []
    lifetime_stddevs = []
    category_names = []
    output_splits = []
    output_flow_ids = set()
    
    for cat_key, cat_params in sorted_categories:
        # Basic parameters - ensure numeric conversion
        inflow_split = cat_params.get('DSM_Inflow_Split_[%]', 0)
        inflow_splits.append(float(inflow_split) if inflow_split is not None else 0.0)
        
        lifetime_types.append(cat_params.get('DSM_Lifetime_Type', 'normal'))
        
        lifetime_mean = cat_params.get('DSM_Lifetime_Mean', 0)
        lifetime_means.append(float(lifetime_mean) if lifetime_mean is not None else 0.0)
        
        lifetime_stddev = cat_params.get('DSM_Lifetime_StdDev', 0)
        lifetime_stddevs.append(float(lifetime_stddev) if lifetime_stddev is not None else 0.0)
        
        # Use category name if available, otherwise use the key
        if isinstance(cat_key, str) and cat_key != 'DSM_Category_Name':
            category_names.append(cat_key)
        else:
            category_names.append(cat_params.get('DSM_Category_Name', f'Category_{len(category_names) + 1}'))
        
        # Output parameters - collect all output flows and ensure numeric conversion
        cat_output_splits = []
        for key, value in cat_params.items():
            if key.startswith('DSM_Output_') and key.endswith('_Split_[%]'):
                # Ensure numeric conversion for output splits
                numeric_value = float(value) if value is not None else 0.0
                cat_output_splits.append(numeric_value)
            elif key.startswith('DSM_Output_') and key.endswith('_Flow_ID'):
                output_flow_ids.add(value)
        
        output_splits.append(cat_output_splits)
    
    # Convert output_flow_ids to sorted list
    output_flow_ids = sorted(list(output_flow_ids))
    
    return {
        "inflow_split": inflow_splits,
        "lifetimes": {
            "Type": lifetime_types,
            "Mean": lifetime_means,
            "StdDev": lifetime_stddevs,
        },
        "category_names": category_names,
        "output_splits": output_splits,
        "output_flow_ids": output_flow_ids,
        "parameter_based": True  # Flag to indicate this is parameter-based format
    }


def _parse_category_based_dsm(process_data):
    """
    Parse DSM parameters from the old category-based format.
    Each row represents a complete category.
    """
    # Sort by Category_ID if available
    if 'Category_ID' in process_data.columns:
        process_data = process_data.sort_values(by="Category_ID")
    
    return {
        "inflow_split": list(process_data["Inflow_Split_[%]"]),
        "lifetimes": {
            "Type": list(process_data["Lifetime_Type"]),
            "Mean": list(process_data["Lifetime_Mean"]),
            "StdDev": list(process_data["Lifetime_StdDev"]),
        },
        "category_names": list(process_data["Category_Name"]),
        "parameter_based": False  # Flag to indicate this is category-based format
    }


def load_fomp_parameters(excel_data):
    """
    Reads the '3_2_Definition_FOMP' sheet and constructs the FOMP_PARAMS dictionary.
    Supports both Process_ID and Pool_ID systems.
    """
    sheet_name = "3_2_Definition_FOMP"
    print(f"--> Loading FOMP parameters from sheet '{sheet_name}'...")

    if sheet_name not in excel_data:
        print(f"--> INFO: Sheet '{sheet_name}' not found. Using empty FOMP configuration.")
        return {}

    df_fomp = excel_data[sheet_name]
    fomp_params = {}

    for _, row in df_fomp.iterrows():
        # Handle both Process_ID and Pool_ID systems
        process_id = None
        param_name = None
        value = None
        
        # Check if using FOMP_Parameter_ID format (new system) - PRIORITY
        if "FOMP_Parameter_ID" in df_fomp.columns and pd.notna(row.get("FOMP_Parameter_ID")):
            param_id = str(row["FOMP_Parameter_ID"])
            value = row["FOMP_Parameter_Value"]
            
            # Extract process ID from FOMP_Parameter_ID format (e.g., "P04_Inflow_fraction_f (Labile pool)" -> "04")
            try:
                if param_id.startswith("P") and "_" in param_id:
                    process_id = int(param_id[1:].split("_")[0])
                    # Extract parameter name by removing the process prefix
                    param_name = param_id.split("_", 1)[1]  # Remove "P04_" prefix
                else:
                    print(f"⚠️ WARNING: Could not extract process ID from FOMP_Parameter_ID: {param_id}")
                    continue
            except (ValueError, IndexError):
                print(f"⚠️ WARNING: Could not parse FOMP_Parameter_ID format: {param_id}")
                continue
                
        # Check if using Pool_ID system (legacy approach)
        elif "Pool_ID" in df_fomp.columns and pd.notna(row.get("Pool_ID")):
            pool_id = str(row["Pool_ID"])
            param_name = row["Parameter_Name"]
            value = row["Value"]
            
            # Extract process ID from Pool_ID format (e.g., "P08_Inflow_fraction_f (Labile pool)" -> "08")
            try:
                if pool_id.startswith("P") and "_" in pool_id:
                    process_id = int(pool_id[1:].split("_")[0])
                else:
                    print(f"⚠️ WARNING: Could not extract process ID from Pool_ID: {pool_id}")
                    continue
            except (ValueError, IndexError):
                print(f"⚠️ WARNING: Could not parse Pool_ID format: {pool_id}")
                continue
                
        # Check if using Process_ID system (legacy approach)
        elif "Process_ID" in df_fomp.columns and pd.notna(row.get("Process_ID")):
            process_id = int(row["Process_ID"])
            param_name = row.get("Parameter_Name", "")
            value = row.get("Value", "")
            
        # Check if using new FOMP column format (prefer FOMP_Parameter_type)
        elif "FOMP_Parameter_type" in df_fomp.columns and pd.notna(row.get("FOMP_Parameter_type")):
            process_id = int(row["Process_ID"]) if pd.notna(row.get("Process_ID")) else None
            param_name = row["FOMP_Parameter_type"]
            value = row["FOMP_Parameter_Value"]
            
        else:
            continue

        # Initialize process dictionary if not exists
        if process_id not in fomp_params:
            fomp_params[process_id] = {}

        # Map parameter names to expected format
        if param_name == "output_carbon_id":
            fomp_params[process_id]["outflow_id"] = value
        elif param_name == "output_environmental_id":
            fomp_params[process_id]["outflow_id_2"] = value
        else:
            # Keep original parameter names for calculation
            try:
                fomp_params[process_id][param_name] = float(value)
            except (ValueError, TypeError):
                fomp_params[process_id][param_name] = value
    
    print(f"--> Successfully loaded configurations for {len(fomp_params)} FOMP process(es).")
    for process_id, params in fomp_params.items():
        print(f"   Process {process_id}: {len(params)} parameters")
    
    return fomp_params


def load_uncertainty_definitions(excel_data):
    """
    Reads the '4_1_Uncertainty_Parameters' sheet and converts it into the
    UNCERTAINTY_PARAMS dictionary format.
    """
    sheet_name = "4_1_Uncertainty_Parameters"
    print(f"--> Loading uncertainty definitions from sheet '{sheet_name}'...")

    if sheet_name not in excel_data:
        print(f"--> INFO: Sheet '{sheet_name}' not found. No uncertainties will be loaded.")
        return {}

    df_uncertainty = excel_data[sheet_name]
    print(f"  DEBUG: df_uncertainty before dropna:\n{df_uncertainty}")
    df_uncertainty = df_uncertainty.dropna(subset=["Parameter_Name"])
    print(f"  DEBUG: df_uncertainty after dropna (rows: {len(df_uncertainty)}):\n{df_uncertainty}")
    uncertainty_params = {}

    for _, row in df_uncertainty.iterrows():
        param_name = row["Parameter_Name"]
        dist_type = row["Distribution_Type"].lower()
        definition = {"distribution": dist_type}

        if dist_type == "uniform":
            if pd.notna(row["Min"]) and pd.notna(row["Max"]):
                definition["min"] = row["Min"]
                definition["max"] = row["Max"]
        elif dist_type == "normal":
            if pd.notna(row["Mean"]) and pd.notna(row["StdDev"]):
                definition["mean"] = row["Mean"]
                definition["std"] = row["StdDev"]
        elif dist_type == "triangular":
            if pd.notna(row["Min"]) and pd.notna(row["Mode"]) and pd.notna(row["Max"]):
                definition["min"] = row["Min"]
                definition["mode"] = row["Mode"]
                definition["max"] = row["Max"]

        if len(definition) > 1:
            uncertainty_params[param_name] = definition

    print(f"--> Successfully loaded {len(uncertainty_params)} uncertainty parameter definition(s).")
    return uncertainty_params


def apply_fomp_uncertainty_updates(fomp_params, uncertainty_updates):
    """
    Applies uncertainty parameter updates to FOMP parameters.
    Handles process-specific parameter names like 'P7_decay_k1 (Labile pool)'.
    
    Args:
        fomp_params (dict): Original FOMP parameters dictionary
        uncertainty_updates (dict): Sampled parameter values from Monte Carlo
        
    Returns:
        dict: Updated FOMP parameters with uncertainty applied
    """
    updated_fomp_params = copy.deepcopy(fomp_params)
    
    for param_name, sampled_value in uncertainty_updates.items():
        # Check if this is a process-specific FOMP parameter (starts with 'P' and contains '_decay_')
        if param_name.startswith('P') and '_decay_' in param_name:
            try:
                # Extract process ID and original parameter name
                # Format: P7_decay_k1 (Labile pool) -> process_id=7, original_name=decay_k1 (Labile pool)
                parts = param_name.split('_', 1)  # Split on first underscore only
                if len(parts) == 2:
                    process_id_str = parts[0][1:]  # Remove 'P' prefix
                    original_param_name = parts[1]  # Everything after P7_
                    
                    process_id = int(process_id_str)
                    
                    # Apply the update if this process exists in FOMP params
                    if process_id in updated_fomp_params:
                        updated_fomp_params[process_id][original_param_name] = sampled_value
                        print(f"  Applied uncertainty: {param_name} = {sampled_value:.4f} to Process {process_id}")
                    else:
                        print(f"  WARNING: Process {process_id} not found in FOMP parameters for {param_name}")
                        
            except (ValueError, IndexError) as e:
                print(f"  WARNING: Could not parse process-specific parameter {param_name}: {e}")
    
    return updated_fomp_params


def load_scenario_definitions(excel_data):
    """
    Reads the scenario definitions sheet and parses the definitions.
    """
    sheet_name = None
    if "5_1_Scenario_Manager" in excel_data:
        sheet_name = "5_1_Scenario_Manager"
    elif "Scenario Manager" in excel_data:
        sheet_name = "Scenario Manager"

    print(f"--> Loading scenario definitions from sheet '{sheet_name}'...")

    if not sheet_name or excel_data[sheet_name].empty:
        print(f"--> INFO: Scenario sheet not found or is empty. No scenarios loaded.")
        return {}

    df = excel_data[sheet_name]
    
    header_row = 0
    found = False
    for i in range(min(10, len(df))):
        if 'Scenario_Name' in df.iloc[i].values:
            header_row = i
            found = True
            break
    
    if found:
        df.columns = df.iloc[header_row]
        df = df.iloc[header_row + 1:].reset_index(drop=True)
    
    try:
        df_scenarios = df.dropna(subset=["Scenario_Name", "Parameter_Name"])
    except KeyError:
        print(f"--> ERROR: Could not find 'Scenario_Name' or 'Parameter_Name' columns in sheet '{sheet_name}'.")
        return {}

    scenario_definitions = {}
    for scenario_name, group in df_scenarios.groupby("Scenario_Name"):
        for record in group.to_dict('records'):
            if 'ID' in record and pd.notna(record['ID']):
                record['ID'] = int(record['ID'])
            
            # Handle year range columns
            if 'start_year' in record and pd.notna(record['start_year']):
                record['start_year'] = int(record['start_year'])
            else:
                record['start_year'] = None
                
            if 'end_year' in record and pd.notna(record['end_year']):
                record['end_year'] = int(record['end_year'])
            else:
                record['end_year'] = None
                
        scenario_definitions[scenario_name] = group.to_dict('records')

    print(f"--> Successfully loaded {len(scenario_definitions)} scenario(s).")
    return scenario_definitions


def load_initial_stock_parameters(excel_data):
    """
    Loads initial stock parameters using the new initial stock engine.
    
    This function delegates to the initial_stock_engine module for consistency
    with the new long table structure.
    
    Args:
        excel_data (dict): Dictionary of DataFrames from Excel.
        
    Returns:
        dict: Initial stock configurations per process.
    """
    # Import here to avoid circular imports
    from engine import initial_stock_engine
    
    return initial_stock_engine.load_initial_stock_parameters(excel_data)