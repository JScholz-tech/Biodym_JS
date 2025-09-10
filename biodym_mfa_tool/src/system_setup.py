# -*- coding: utf-8 -*-
"""
System Setup Module for the BioDYM MFA Model.

This file contains all functions responsible for building and configuring
the MFAsystem object before the main calculation begins. This includes
defining the model scope, initializing the system, loading process and flow
definitions, and setting up all parameters.
"""

import numpy as np
import pandas as pd

# These are imported by main.py and are available in this namespace
import ODYM_Classes as msc


def define_model_scope(start_year, end_year, elements):
    """
    Defines the temporal and elemental scope of the MFA model.

    Args:
        start_year (int): The first year of the analysis.
        end_year (int): The last year of the analysis.
        elements (list): A list of strings for the elements to be tracked.

    Returns:
        tuple: A tuple containing the ModelClassification dictionary
               and the IndexTable DataFrame, which are core ODYM objects.
    """
    ModelClassification = {}
    MyYears = list(np.arange(start_year, end_year + 1))

    ModelClassification["Time"] = msc.Classification(
        Name="Time", Dimension="Time", ID=1, Items=MyYears
    )
    ModelClassification["Element"] = msc.Classification(
        Name="Elements", Dimension="Element", ID=2, Items=elements
    )

    IndexTable = pd.DataFrame(
        {
            "Aspect": ["Time", "Element"],
            "Description": ['Model aspect "time"', 'Model aspect "Element"'],
            "Dimension": ["Time", "Element"],
            "Classification": [
                ModelClassification[Aspect] for Aspect in ["Time", "Element"]
            ],
            "IndexLetter": ["t", "e"],
        }
    )
    IndexTable.set_index("Aspect", inplace=True)

    print("--> Model scope and classifications defined.")
    return ModelClassification, IndexTable


def initialize_mfa_system(model_classification, index_table):
    """
    Initializes the main MFAsystem object based on the defined scope.

    Args:
        model_classification (dict): The ModelClassification dictionary.
        index_table (pd.DataFrame): The IndexTable DataFrame.

    Returns:
        odym.MFAsystem: An empty but structured MFAsystem object.
    """
    start_time = model_classification["Time"].Items[0]
    end_time = model_classification["Time"].Items[-1]
    element_items = model_classification["Element"].Items

    mfa_system = msc.MFAsystem(
        Name="RyeStrawMFA",
        Geogr_Scope="Case_Study_Region",
        Unit="Mg",
        ProcessList=[],
        FlowDict={},
        StockDict={},
        ParameterDict={},
        Time_Start=start_time,
        Time_End=end_time,
        IndexTable=index_table,
        Elements=element_items,
    )

    print("--> MFA system object initialized.")
    return mfa_system


def load_and_define_processes(mfa_system, input_data, data_loader):
    """
    Loads all data from the Excel file, validates its structure, and defines
    the processes and empty stock objects in the MFA system.

    Args:
        mfa_system (odym.MFAsystem): The initialized MFA system object.
        input_data (dict): A dictionary of DataFrames for each Excel sheet.
        data_loader (module): The imported data_loader module.

    Returns:
        tuple: A tuple containing the modified mfa_system object and the same input_data dict.
    """
    print("--> Defining process and stock structures...")

    # Accept either a pre-loaded dict of DataFrames or a path to an Excel file
    if isinstance(input_data, dict):
        all_excel_data = input_data
    else:
        # Load all sheets into a dict; tests may patch pd.read_excel to return a dict
        all_excel_data = pd.read_excel(
            input_data,
            sheet_name=None,
            header=0,
            engine="openpyxl",
            na_values=["N.A.", "NA", "n/a"],
        )

    data_loader.validate_input_data(all_excel_data)

    process_definitions = all_excel_data["2_1_Definition_Processes"]
    for _, row in process_definitions.iterrows():
        if pd.notna(row["Name(EN)"]):
            process_id = int(row["ID"])
            has_tcs = "TC" if "TC?" in row and row["TC?"] == "Yes" else "None"
            mfa_system.ProcessList.append(
                msc.Process(Name=row["Name(EN)"], ID=process_id, Extensions=has_tcs)
            )
            if "Stock?" in row and row["Stock?"] == "Yes":
                mfa_system.StockDict[f"dS_{process_id}"] = msc.Stock(
                    Name=f"dS_{process_id}", P_Res=process_id, Type=1, Indices="t,e"
                )
                mfa_system.StockDict[f"S_{process_id}"] = msc.Stock(
                    Name=f"S_{process_id}", P_Res=process_id, Type=0, Indices="t,e"
                )
                
                fomp_sheet = all_excel_data.get("3_2_Definition_FOMP")
                is_fomp_process = False
                if fomp_sheet is not None:
                    fomp_processes = fomp_sheet[fomp_sheet["Process_ID"] == process_id]
                    is_fomp_process = (row.get("FOMP?", "No") == "Yes") and (not fomp_processes.empty)
                
                if is_fomp_process:
                    mfa_system.StockDict[f"S_{process_id}"]._fomp_process = True

    for stock_name, stock_obj in mfa_system.StockDict.items():
        if hasattr(stock_obj, '_fomp_process') and stock_obj._fomp_process:
            stock_obj.Values = np.zeros((len(mfa_system.IndexTable.Classification['Time'].Items), len(mfa_system.Elements)))
            delattr(stock_obj, '_fomp_process')

    mfa_system.Initialize_StockValues()
    print("--> Stock values initialized.")

    return mfa_system, all_excel_data


def create_dynamic_tc_parameters(dynamic_tc_data, time_vector):
    """
    Generates time series for TCs, with data cleaning and validation.
    """
    print("--> Generating dynamic TC time series via interpolation...")
    required_cols = ["TC_ID", "Year", "Value"]
    if not all(col in dynamic_tc_data.columns for col in required_cols):
        raise ValueError(f"The '2_5_dynamic_tcs' sheet is missing one of the required columns: {required_cols}.")

    cleaned_data = dynamic_tc_data.dropna(subset=["TC_ID", "Year"])
    duplicates = cleaned_data[cleaned_data.duplicated(subset=["TC_ID", "Year"], keep=False)]
    if not duplicates.empty:
        raise ValueError(f"Duplicate entries found for the same TC in the same year in '2_5_dynamic_tcs'. Conflicting rows:\n{duplicates.sort_values(by=['TC_ID', 'Year'])}")

    dynamic_tc_dict = {}
    unique_tc_ids = cleaned_data["TC_ID"].unique()
    for tc_id in unique_tc_ids:
        tc_points = cleaned_data[cleaned_data["TC_ID"] == tc_id]
        ts = pd.Series(tc_points["Value"].values, index=tc_points["Year"])
        ts_full = ts.reindex(time_vector)
        ts_interpolated = ts_full.interpolate(method="linear", limit_direction="both")
        dynamic_tc_dict[tc_id] = ts_interpolated.to_numpy()

    print(f"--> Generated {len(dynamic_tc_dict)} dynamic TC parameter(s).")
    return dynamic_tc_dict


def define_flows_and_parameters(mfa_system, all_excel_data):
    """
    Defines flows, initializes ALL system values, populates them with data,
    and defines all model parameters (TCs, contents, etc.).
    """
    print("--> Defining flows, parameters, and setting all initial values...")
    parameter_id_counter = 1

    flow_definitions = all_excel_data["1_1_Definition_Flows"]
    for _, row in flow_definitions.iterrows():
        if pd.notna(row["Name(EN)"]):
            start_id, end_id = int(row["Process_ID_O"]), int(row["Process_ID_I"])
            mfa_system.FlowDict[row["Flow_ID"]] = msc.Flow(Name=row["Flow_ID"], P_Start=start_id, P_End=end_id, Indices="t,e")

    mfa_system.Initialize_FlowValues()
    print("--> All flows initialized to zero.")

    flow_data = all_excel_data["1_2_Data_Flows"]
    for flow_id, flow_obj in mfa_system.FlowDict.items():
        if flow_id in flow_data["Flow_ID"].values:
            flow_time_series = flow_data[flow_data["Flow_ID"] == flow_id]
            if len(flow_time_series) == len(mfa_system.IndexTable.Classification["Time"].Items):
                flow_obj.Values[:, 0] = np.array(flow_time_series["Flow_Py"]).ravel()
    print("--> Populated data for primary input flows.")

    initial_stock_data = all_excel_data.get("2_4_Initial_Stock")
    process_definitions = all_excel_data["2_1_Definition_Processes"]
    if initial_stock_data is not None:
        for _, row in process_definitions.iterrows():
            if pd.notna(row["ID"]) and "Initial_Stock?" in row and row["Initial_Stock?"] == "Yes":
                process_id = int(row["ID"])
                stock_data_row = initial_stock_data[initial_stock_data["Process_ID"] == process_id]
                if not stock_data_row.empty:
                    stock_s = mfa_system.StockDict.get(f"S_{process_id}")
                    if stock_s:
                        mat = stock_data_row["Initial_Stock_material"].iloc[0]
                        wc_p = stock_data_row["Initial_Stock_WC[%]"].iloc[0]
                        dm_p = stock_data_row["Initial_Stock_DM[%]"].iloc[0]
                        cc_p = stock_data_row["Initial_Stock_CC[%]"].iloc[0]
                        stock_s.Values[0, :] = [mat, mat * wc_p, mat * dm_p, mat * cc_p]
                        
                        if "Stock_Outflow_TC" in stock_data_row.columns and pd.notna(stock_data_row["Stock_Outflow_TC"].iloc[0]):
                            tc_id = stock_data_row["Stock_Outflow_TC"].iloc[0]
                            destination_process = int(stock_data_row["Destination_Process"].iloc[0])
                            consumption_rate = float(stock_data_row["Annual_Consumption_Rate"].iloc[0])
                            mfa_system.ParameterDict[tc_id] = msc.Parameter(Name=tc_id, ID=parameter_id_counter, Values=consumption_rate, Unit="1/year")
                            parameter_id_counter += 1
                            if not hasattr(mfa_system, 'stock_outflow_tcs'):
                                mfa_system.stock_outflow_tcs = {}
                            mfa_system.stock_outflow_tcs[process_id] = {
                                'tc_id': tc_id, 'destination_process': destination_process,
                                'consumption_rate': consumption_rate, 'initial_stock': stock_s.Values[0, :].copy()}

    tc_definitions = all_excel_data.get("2_3_Process_TCs")
    if tc_definitions is not None:
        for _, row in tc_definitions.iterrows():
            if "TC_ID" in row and pd.notna(row["TC_ID"]) and pd.notna(row["TC_Value"]):
                mfa_system.ParameterDict[row["TC_ID"]] = msc.Parameter(Name=row["TC_ID"], ID=parameter_id_counter, Values=row["TC_Value"], Unit="1")
                parameter_id_counter += 1

    content_definitions = all_excel_data["1_1_Definition_Flows"]
    for _, row in content_definitions.iterrows():
        flow_id = row.get("Flow_ID")
        if pd.notna(flow_id) and flow_id in mfa_system.FlowDict:
            for element in mfa_system.Elements[1:]:
                if element in row and pd.notna(row[element]):
                    param_name = f"{element}_{flow_id}"
                    mfa_system.ParameterDict[param_name] = msc.Parameter(Name=param_name, ID=parameter_id_counter, Values=row[element], Unit="1")
                    parameter_id_counter += 1

    for flow in mfa_system.FlowDict.values():
        if np.any(flow.Values[:, 0] != 0):
            for i_elem, element_name in enumerate(mfa_system.Elements[1:], 1):
                if element_name == "CC": continue
                param_name = f"{element_name}_{flow.Name}"
                if param_name in mfa_system.ParameterDict:
                    content_value = mfa_system.ParameterDict[param_name].Values
                    flow.Values[:, i_elem] = flow.Values[:, 0] * content_value
            if "CC" in mfa_system.Elements:
                cc_idx = mfa_system.Elements.index("CC")
                param_name = f"CC_{flow.Name}"
                if param_name in mfa_system.ParameterDict:
                    cc_fraction = mfa_system.ParameterDict[param_name].Values
                    flow.Values[:, cc_idx] = flow.Values[:, 0] * cc_fraction

    mfa_system.Consistency_Check()
    return mfa_system, all_excel_data

def apply_scenario(mfa_system, scenario_definitions, selected_scenario_name):
    """
    Applies the modifications for a selected scenario to the MFA system object.

    Args:
        mfa_system (odym.MFAsystem): The configured MFA system object.
        scenario_definitions (dict): All available scenario rules from the Excel file.
        selected_scenario_name (str): The name of the scenario to apply.

    Returns:
        odym.MFAsystem: The MFA system with scenario modifications applied.
    """
    modifications = scenario_definitions.get(selected_scenario_name, [])

    for mod in modifications:
        param_name = mod['Parameter_Name']
        operation = mod['Operation'].lower()
        value = mod['New_Value']

        print(f"    -> Applying: {param_name} | Operation: {operation} | Value: {value}")

        if param_name.startswith('F_') and param_name in mfa_system.FlowDict:
            flow_obj = mfa_system.FlowDict[param_name]
            if operation == 'replace':
                flow_obj.Values[:, 0] = float(value)
            elif operation == 'multiply':
                flow_obj.Values[:, 0] *= float(value)
            elif operation == 'add':
                flow_obj.Values[:, 0] += float(value)
            else:
                print(f"       WARNING: Unknown operation '{operation}' for Flow {param_name}")

        elif param_name in mfa_system.ParameterDict:
            param_obj = mfa_system.ParameterDict[param_name]
            is_dynamic = isinstance(param_obj.Values, np.ndarray)

            if operation == 'replace':
                param_obj.Values = float(value) if not is_dynamic else np.full_like(param_obj.Values, float(value))
            elif operation == 'multiply':
                param_obj.Values *= float(value)
            elif operation == 'add':
                param_obj.Values += float(value)
            else:
                print(f"       WARNING: Unknown operation '{operation}' for Parameter {param_name}")
        
        else:
            print(f"       WARNING: Parameter or Flow '{param_name}' not found in the system.")

    print("\n    -> Recalculating elemental compositions for modified flows...")
    for flow in mfa_system.FlowDict.values():
        for i_elem, element_name in enumerate(mfa_system.Elements[1:], 1):
            param_name = f"{element_name}_{flow.Name}"
            if param_name in mfa_system.ParameterDict:
                content_value = mfa_system.ParameterDict[param_name].Values
                flow.Values[:, i_elem] = flow.Values[:, 0] * content_value

    print("\n✅ Scenario modifications applied successfully.")
    return mfa_system
