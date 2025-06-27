# -*- coding: utf-8 -*-
"""
Refactored MFA Rye Straw Cascading Treatment System Model

This script models a cascading treatment system for rye straw using ODYM
and the bioDYM_addon. It reads configuration and data from an Excel file,
performs calculations including dynamic stock modeling (DSM) for MBC products
and first-order modeling process (FOMP) for biochar mineralization,
and provides options for results presentation and export.

Improvements include:
- Centralized configuration section.
- Robust Excel file and sheet handling.
- Improved parsing of IDs and parameters from Excel.
- Fixed flow input data handling (assuming start year + growth rate).
- Added checks for missing parameters and zero inputs during calculations.
- Controlled verbose output for debugging.
- Enhanced comments for clarity.
"""

# %% [markdown]
# # MFA rye straw cascading treatment system
#
# This model presents a cascading treatment system for rye straw. After rye harvest, the straw is used for biogas production. The resulting by-products are further processed to produce mycelium-based composites (MBC), biodegradable materials that can substitute various synthetic products made from petroleum. Dynamic stock modelling is applied in the MBC use phase to account for different lifetimes of MBC products. From the MBC EoL-Treatment, biochar is obtained as a soil enhancement product. The mineralization process of the biochar in the litosphere is calculatated via a first order modelling process. The data used for the model is based on a research biogas plant from the chair of circular economy and recycling technology, TU Berlin. For the dynamic model, an increase of input flows of 2% per year is assumed.

# %% [markdown]
# `<img src="system_flow_diagram.svg" alt="system_flow_diagram">`

# %% [markdown]
# ## 0 Load packages & Configuration
#
# This cell imports necessary packages, loads ODYM and bioDYM_addon,
# and defines configuration parameters for the model run.

# %% Configuration Section
import os
import sys
from pathlib import Path # For potentially cleaner path handling

# --- Core Configuration ---
# File Paths
# Use Path for better cross-platform compatibility if needed
# BASE_DIR = Path(os.getcwd()) # Or specify explicitly if notebook isn't in project root
BASE_DIR = Path().cwd() # Assumes script run from the notebook's directory
EXCEL_FILE_PATH = BASE_DIR / '250414_Scenario2_Data.xlsx'
# Construct framework paths relative to the *parent* of the current working directory
FRAMEWORK_DIR = BASE_DIR.parent / 'framework'
ODYM_FRAMEWORK_PATH = FRAMEWORK_DIR / 'ODYM-master_20241127' / 'odym' / 'modules'
BIODYM_ADDON_PATH = FRAMEWORK_DIR / 'bioDYM_add-on' / 'modules'

# Excel Sheet Names (Adjust if your Excel file uses different names)
PROCESS_DEF_SHEET = '2_1_Definition_Processes'
FLOW_DEF_SHEET = '1_1_Definition_Flows'
FLOW_DATA_SHEET = '1_2_Data_Flows'
TC_DATA_SHEET = '2_3_Process_TCs'

# Model Parameters
START_YEAR = 2022
END_YEAR = 2036 # Inclusive end year
ANNUAL_GROWTH_RATE = 0.02 # e.g., 2% growth for known input flows from FLOW_DATA_SHEET

# Model Elements (Ensure this matches the order in calculations/Excel)
ELEMENTS = ['material', 'WC', 'DM', 'CC']

# DSM Parameters for MBC Use Phase (Process ID 3 assumed)
# These could potentially be read from a dedicated Excel sheet
MBC_PROCESS_ID = 3
# Lifetimes for different MBC product categories (long, medium, short)
MBC_LIFETIMES_TAU = [10, 5, 1] # years
# Standard deviation as a fraction of the mean lifetime
MBC_LIFETIME_STDDEV_FACTOR = 0.2
MBC_LIFETIMES_SIGMA = [MBC_LIFETIME_STDDEV_FACTOR * tau for tau in MBC_LIFETIMES_TAU] # years
# Assumed split of inflow F_02_03 into the lifetime categories
MBC_LIFETIME_SPLITS = [0.2, 0.2, 0.6] # Fractions must sum to 1

# FOMP Parameters for Biochar Mineralization (Process ID 17 assumed, Input from P9)
# Values based on Cayuela et al., 2010 for green waste biochar
FOMP_PROCESS_ID = 17 # Lithosphere process
FOMP_INPUT_PROCESS_ID = 9 # Pyrolysis process sending biochar
FOMP_PARAM_F = 0.0     # Fraction of labile pool
FOMP_PARAM_K1 = 0.0    # Decay rate of labile pool (1/year)
FOMP_PARAM_K2 = 0.03212 # Decay rate of stable pool (1/year)

# Plotting / Debugging
VERBOSE_DEBUG_PRINTING = False # Set to True to see detailed printouts during setup and calculation
PLOT_DPI = 150 # Resolution for static plots

# --- End Configuration ---


# %% Load Packages
import numpy as np
import pandas as pd
from scipy.stats import lognorm, norm # norm needed for DSM if Type='Normal'
import xlsxwriter
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, FormatStrFormatter, AutoMinorLocator
import warnings
import re
from collections import defaultdict
from scipy.optimize import minimize
import copy

# Suppress the specific openpyxl warning about Data Validation
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

# Add ODYM module directory to system path
if str(ODYM_FRAMEWORK_PATH) not in sys.path:
    sys.path.insert(0, str(ODYM_FRAMEWORK_PATH))

# Check if path exists
if not ODYM_FRAMEWORK_PATH.exists():
    raise FileNotFoundError(f"ODYM framework path not found: {ODYM_FRAMEWORK_PATH}")

# Import ODYM modules
try:
    import ODYM_Classes as msc
    import ODYM_Functions as msf
    import dynamic_stock_model as dsm
except ImportError as e:
    print(f"Error importing ODYM modules from {ODYM_FRAMEWORK_PATH}. Check path and installation.")
    raise e

# Add bioDYM_addon module directory to system path
if str(BIODYM_ADDON_PATH) not in sys.path:
    sys.path.insert(0, str(BIODYM_ADDON_PATH))

# Check if path exists
if not BIODYM_ADDON_PATH.exists():
    raise FileNotFoundError(f"bioDYM addon path not found: {BIODYM_ADDON_PATH}")

# Import bioDYM_addon modules
try:
    import bioDYM_classes as bicl
    import bioDYM_plotting as bipl
    import bioDYM_export as bix
except ImportError as e:
    print(f"Error importing bioDYM modules from {BIODYM_ADDON_PATH}. Check path and installation.")
    raise e

# Enable plotting directly in the notebook environment (if applicable)
# %matplotlib inline # This magic command only works in Jupyter notebooks

print("Packages and Frameworks loaded.")

# %% [markdown]
# ## 1 Definition of system and relevant aspects
#
# The system definition is quite rigid, all aspects of the model are defined. In this setup here, the model includes a time dimension and an element dimension. Elements can be materials or included substances. Here, the top level is simply called material and sub level elements are water content (WC), dry matter (DM) and carbon content (CC). To adapt this section, the first three cells can simply be copied and only the years of the analysis and the elements included have to be modified. Then, all processes, stocks and flows are defined. In this study, this is done building up on the input data table. It is also possible to do it in a more simple way by just defining processes, flows and stocks manually in the Notebook (see case_study_bachelor_thesis or basic_examples).
#
# In general, processes are stored in the ProcessList, flows are stored in the FlowDict, stocks are stored in the StockDict and parameters (like TCs) are stored in the ParameterDict.

# %% Initiate model classifications (Time, Element)

# Create empty dictionary for model classifications
ModelClassification = {}

# Define period of analysis using configured start/end years
# +1 because np.arange excludes the endpoint
MyYears = list(np.arange(START_YEAR, END_YEAR + 1))

# Classification for time
ModelClassification['Time'] = msc.Classification(Name='Time', Dimension='Time', ID=1, Items=MyYears)

# Classification for elements using configured list
ModelClassification['Element'] = msc.Classification(Name='Elements', Dimension='Element', ID=2, Items=ELEMENTS)

# Get model time start, end, and duration:
Model_Time_Start = int(min(ModelClassification['Time'].Items))
Model_Time_End = int(max(ModelClassification['Time'].Items))
# Duration is number of intervals (years), which is N-1, but length is N
Model_Duration_Intervals = Model_Time_End - Model_Time_Start
Model_No_Of_Years = len(ModelClassification['Time'].Items)

print(f"Model time: {Model_Time_Start}-{Model_Time_End} ({Model_No_Of_Years} years)")
print(f"Model elements: {ModelClassification['Element'].Items}")


# %% Set up Index Table

IndexTable = pd.DataFrame({
    'Aspect': ['Time', 'Element'],
    'Description': ['Model aspect "time"', 'Model aspect "Element"'],
    'Dimension': ['Time', 'Element'],
    'Classification': [ModelClassification[Aspect] for Aspect in ['Time', 'Element']],
    'IndexLetter': ['t', 'e']
})
IndexTable.set_index('Aspect', inplace=True)

if VERBOSE_DEBUG_PRINTING:
    print("Index Table:")
    print(IndexTable)


# %% Initialize MFA system object

Dyn_MFA_System = msc.MFAsystem(Name='Rye_Straw_Cascading_System',
                      Geogr_Scope='Regional_Example', # Changed scope name
                      Unit='Mg', # Megagrams (tonnes)
                      ProcessList=[],
                      FlowDict={},
                      StockDict={},
                      ParameterDict={},
                      Time_Start=Model_Time_Start,
                      Time_End=Model_Time_End,
                      IndexTable=IndexTable,
                      Elements=IndexTable.loc['Element'].Classification.Items)

print(f"MFA System '{Dyn_MFA_System.Name}' initialized.")


# %% Import Excel Data Table

# Load all sheets from the Excel file
try:
    # Use Path object directly with pandas
    input_data = pd.read_excel(EXCEL_FILE_PATH, sheet_name=None, header=0)
    print(f"Successfully loaded Excel file: {EXCEL_FILE_PATH}")
    # Check if required sheets exist
    required_sheets = [PROCESS_DEF_SHEET, FLOW_DEF_SHEET, FLOW_DATA_SHEET, TC_DATA_SHEET]
    missing_sheets = [sheet for sheet in required_sheets if sheet not in input_data]
    if missing_sheets:
        raise ValueError(f"Missing required sheets in Excel file: {missing_sheets}")
    print(f"Found required sheets: {required_sheets}")
except FileNotFoundError:
    print(f"ERROR: Excel file not found at {EXCEL_FILE_PATH}")
    sys.exit(f"Stopping execution. Please ensure the file exists at the specified path.")
except ValueError as ve:
    print(f"ERROR: {ve}")
    sys.exit(f"Stopping execution. Please check the Excel file '{EXCEL_FILE_PATH}'.")
except Exception as e:
    print(f"ERROR: Could not read Excel file {EXCEL_FILE_PATH}. Error: {e}")
    sys.exit(f"Stopping execution due to Excel reading error.")


# %% Define processes and associated stocks from Excel sheet

# Get the process definition sheet
try:
    definition_processes = input_data[PROCESS_DEF_SHEET]
except KeyError:
     print(f"ERROR: Sheet '{PROCESS_DEF_SHEET}' not found in the Excel file.")
     sys.exit("Stopping execution.")

# Create the ODYM ProcessList
Dyn_MFA_System.ProcessList = []
process_ids_defined = set()

print("Defining processes and stocks...")
# Loop through rows in the process definition sheet
for index, row in definition_processes.iterrows():
    # Check if the row defines a process (requires Name and ID)
    if pd.notna(row['Name(EN)']) and pd.notna(row['ID']):
        try:
            # Extract process ID safely
            id_entry = int(row['ID'])
            process_name = str(row['Name(EN)']).strip()

            # Check for duplicate IDs
            if id_entry in process_ids_defined:
                 print(f"WARNING: Duplicate Process ID {id_entry} found for process '{process_name}'. Skipping this definition.")
                 continue
            process_ids_defined.add(id_entry)

            # Determine if process has Transfer Coefficients (TCs)
            # Use .get() for safe access in case column name differs slightly
            has_tc = str(row.get('TC?', 'No')).strip().lower() == 'yes'
            extension = 'TC' if has_tc else 'None'

            # Define the process and add it to the system list
            Dyn_MFA_System.ProcessList.append(msc.Process(Name=process_name, ID=id_entry, Extensions=extension))

            # Check if a stock is associated with this process
            # Use .get() for safe access
            has_stock = str(row.get('Stock?', 'No')).strip().lower() == 'yes'
            if has_stock:
                # Define stock change (dS) and stock (S) objects
                # Indices 't,e' match the Time and Element dimensions
                Dyn_MFA_System.StockDict[f"dS_{id_entry}"] = msc.Stock(Name=f"dS_{id_entry}", P_Res=id_entry, Type=1, Indices='t,e', Values=None)
                Dyn_MFA_System.StockDict[f"S_{id_entry}"] = msc.Stock(Name=f"S_{id_entry}", P_Res=id_entry, Type=0, Indices='t,e', Values=None)

        except ValueError:
            print(f"WARNING: Invalid ID '{row['ID']}' in process definition sheet, row {index+2}. Skipping.")
        except Exception as e:
            print(f"WARNING: Error processing row {index+2} in process definitions: {e}. Skipping.")
    # else: # Optional: print warning if row seems partially filled but invalid
    #     if pd.notna(row['Name(EN)']) or pd.notna(row['ID']):
    #          print(f"WARNING: Incomplete process definition in sheet '{PROCESS_DEF_SHEET}', row {index+2}. Requires Name and ID.")


# Initialize stock value arrays (filled with zeros) based on dimensions
Dyn_MFA_System.Initialize_StockValues()

# Save a copy of the initial (empty) StockDict structure if needed (e.g., for Monte Carlo resets)
Empty_StockDict = copy.deepcopy(Dyn_MFA_System.StockDict)

# Print summary or detailed definition if verbose flag is set
print(f"Defined {len(Dyn_MFA_System.ProcessList)} processes.")
print(f"Defined {len([s for s in Dyn_MFA_System.StockDict if s.startswith('S_')])} stocks.")

if VERBOSE_DEBUG_PRINTING:
    print('\nProcess definition details:')
    for process in Dyn_MFA_System.ProcessList:
        print(f"  Name: {process.Name}, ID: {process.ID}, Extensions: {process.Extensions}")

    print('\nStock definition details:')
    for stock in Dyn_MFA_System.StockDict.values():
        print(f"  Name: {stock.Name}, Process ID: {stock.P_Res}, Type: {stock.Type}, Shape: {stock.Values.shape}")


# %% Define flows from Excel sheet

# Get the flow definition sheet
try:
    definition_flows = input_data[FLOW_DEF_SHEET].copy() # Use copy to avoid modifying original df
except KeyError:
     print(f"ERROR: Sheet '{FLOW_DEF_SHEET}' not found in the Excel file.")
     sys.exit("Stopping execution.")

print("Defining flows...")
# Loop through rows in the flow definition sheet
for index, row in definition_flows.iterrows():
     # Check if the row defines a flow (requires Flow_ID, Process_ID_O, Process_ID_I)
    flow_id = row.get('Flow_ID')
    output_process_str = row.get('Process_ID_O')
    input_process_str = row.get('Process_ID_I')

    if pd.notna(flow_id) and pd.notna(output_process_str) and pd.notna(input_process_str):
        flow_id = str(flow_id).strip()
        output_process_str = str(output_process_str).strip()
        input_process_str = str(input_process_str).strip()

        # Expected format in Excel: Process_ID_O/I = "ID_Description", e.g., "13_RyeCultivation"
        # Extract only the numeric ID part using regex, matching digits at the start.
        output_match = re.match(r'(\d+)', output_process_str)
        input_match = re.match(r'(\d+)', input_process_str)

        if output_match and input_match:
            try:
                output_process_ID = int(output_match.group(1))
                input_process_ID = int(input_match.group(1))

                # Check if process IDs exist in the defined processes
                if output_process_ID not in process_ids_defined:
                    print(f"WARNING: Output Process ID {output_process_ID} for flow '{flow_id}' not found in defined processes. Skipping flow.")
                    continue
                if input_process_ID not in process_ids_defined:
                    print(f"WARNING: Input Process ID {input_process_ID} for flow '{flow_id}' not found in defined processes. Skipping flow.")
                    continue

                # Define the flow and add it to the system dictionary
                Dyn_MFA_System.FlowDict[flow_id] = msc.Flow(Name=flow_id, P_Start=output_process_ID, P_End=input_process_ID, Indices='t,e', Values=None)

            except ValueError:
                 print(f"WARNING: Could not convert parsed Process IDs to integers for flow '{flow_id}'. Output: '{output_match.group(1)}', Input: '{input_match.group(1)}'. Skipping flow definition.")
                 continue
            except Exception as e:
                 print(f"ERROR processing flow definition for '{flow_id}': {e}. Skipping.")
                 continue
        else:
            print(f"WARNING: Could not parse numeric Process IDs from '{output_process_str}' or '{input_process_str}' for flow '{flow_id}'. Check format (e.g., 'ID_Description'). Skipping flow definition.")
            continue
    # else: # Optional: Warn about incomplete rows
    #     if pd.notna(flow_id) or pd.notna(output_process_str) or pd.notna(input_process_str):
    #          print(f"WARNING: Incomplete flow definition in sheet '{FLOW_DEF_SHEET}', row {index+2}. Requires Flow_ID, Process_ID_O, Process_ID_I.")


# Initialize flow value arrays (filled with zeros)
Dyn_MFA_System.Initialize_FlowValues()

# Print summary or detailed definition if verbose flag is set
print(f"Defined {len(Dyn_MFA_System.FlowDict)} flows.")

if VERBOSE_DEBUG_PRINTING:
    print('\nFlow definition details:')
    for flow in Dyn_MFA_System.FlowDict.values():
        print(f"  Name: {flow.Name}, P_Start: {flow.P_Start}, P_End: {flow.P_End}, Shape: {flow.Values.shape}")


# %% [markdown]
# ## 2 Data input into model
# In this section, all input data is imported from the excel data table. Some flows values are known for the initial year, a configured growth rate (e.g., 2%) for each known flow is assumed. TCs are given and also element contents for all flows are given. Flow values are added to the flows of the FlowDict and all parameters (TCs and element contents) are imported to ODYM inherent ParameterDict. Also, the average lifetimes for the MBC products and their standard deviation are defined (using config). The section ends with a nice feature of ODYM: the consistency check.

# %% Add input data (flow values) from Excel sheet

# Get the flow data sheet
try:
    data_flows_input = input_data[FLOW_DATA_SHEET].copy()
except KeyError:
     print(f"ERROR: Sheet '{FLOW_DATA_SHEET}' not found in the Excel file.")
     sys.exit("Stopping execution.")

print(f"Reading initial flow values from sheet '{FLOW_DATA_SHEET}' for year {START_YEAR} and applying {ANNUAL_GROWTH_RATE*100:.1f}% annual growth...")

# Filter the input data for the specified START_YEAR only
# This assumes the Excel sheet *should* only contain data for the starting year
start_year_data = data_flows_input[data_flows_input['Year_Flow'] == START_YEAR]
if start_year_data.empty:
     print(f"WARNING: No flow data found for the start year {START_YEAR} in sheet '{FLOW_DATA_SHEET}'. Initial flows will be zero unless calculated by TCs.")

# Create a dictionary for quick lookup: Flow_ID -> Start Year Value
start_value_map = pd.Series(start_year_data.Flow_Py.values, index=start_year_data.Flow_ID).to_dict()
flows_with_input_data = set()

# Loop through all defined flows in the system
for flow_id, flow in Dyn_MFA_System.FlowDict.items():
    # Check if this flow has an input value defined in the map for the start year
    if flow_id in start_value_map:
        start_value = start_value_map[flow_id]
        if pd.isna(start_value):
             print(f"WARNING: NaN value found for flow '{flow_id}' in start year data. Treating as zero.")
             start_value = 0.0

        # Calculate the time series with the configured annual growth rate
        time_series = np.zeros(Model_No_Of_Years)
        for i, year in enumerate(MyYears):
            # Formula: value[year] = start_value * (1 + growth_rate)^(year - start_year)
            time_series[i] = start_value * ((1 + ANNUAL_GROWTH_RATE) ** (year - START_YEAR))

        # Assign the calculated time series to the 'material' aspect (index 0)
        flow.Values[:, 0] = time_series
        # Initialize other elements (WC, DM, CC) to zero; they will be calculated later using parameters
        flow.Values[:, 1:] = 0
        flows_with_input_data.add(flow_id)

    else:
        # If no input data is defined for this flow in the start year sheet,
        # initialize all elements (including material) to zero.
        # These flows must be calculated later using TCs or other means.
        flow.Values[:, :] = 0

print(f"Assigned initial data and growth to {len(flows_with_input_data)} flows.")
if VERBOSE_DEBUG_PRINTING:
    print("Flows with initial input data assigned:", sorted(list(flows_with_input_data)))
    # Example print of first flow with data
    first_flow_with_data = next((f for f in Dyn_MFA_System.FlowDict.values() if np.any(f.Values[:,0])), None)
    if first_flow_with_data:
        print(f"\nExample: {first_flow_with_data.Name} (material, first 5 years):")
        print(first_flow_with_data.Values[:5, 0])

# Save a copy of the FlowDict after assigning initial data (e.g., for Monte Carlo)
FlowDict_data_input_only = copy.deepcopy(Dyn_MFA_System.FlowDict)


# %% Add Transfer Coefficients (TCs) and Content data to ParameterDict

# Get the TC data sheet
try:
    tc_processes_data = input_data[TC_DATA_SHEET].copy()
except KeyError:
     print(f"ERROR: Sheet '{TC_DATA_SHEET}' not found in the Excel file.")
     sys.exit("Stopping execution.")

# Get the flow definitions again (needed for WC, DM, CC parameters)
try:
    definition_flows_for_params = input_data[FLOW_DEF_SHEET].copy()
except KeyError:
     print(f"ERROR: Sheet '{FLOW_DEF_SHEET}' not found (needed for content parameters).")
     sys.exit("Stopping execution.")


# Initialize ParameterDict if it wasn't already part of Dyn_MFA_System
if not hasattr(Dyn_MFA_System, 'ParameterDict') or Dyn_MFA_System.ParameterDict is None:
     Dyn_MFA_System.ParameterDict = {}

ParameterDict = Dyn_MFA_System.ParameterDict # Use reference for easier access
parameter_id_counter = 0 # Simple counter for unique parameter IDs

print(f"Reading TC parameters from sheet '{TC_DATA_SHEET}'...")
# --- Read Process TCs ---
for process in Dyn_MFA_System.ProcessList:
    # Check if the process was marked as having TCs during definition
    if process.Extensions == 'TC':
        # Find the row corresponding to this process ID in the TC sheet
        process_tc_row = tc_processes_data[tc_processes_data['Process_ID'] == process.ID]

        if not process_tc_row.empty:
            row_data = process_tc_row.iloc[0] # Get the data series for the process

            # Dynamically find output flow TC columns (e.g., Flow_ID_O_1, Flow_TC_O_1_[%])
            # Assumes a naming convention in the Excel sheet
            output_flow_id_cols = [col for col in tc_processes_data.columns if col.startswith('Flow_ID_O_') and not col.endswith('_[%]')]

            for id_col in output_flow_id_cols:
                # Extract the number suffix (e.g., '1' from 'Flow_ID_O_1')
                match_suffix = re.search(r'_O_(\d+)$', id_col)
                if not match_suffix: continue # Skip if column name format is unexpected
                suffix = match_suffix.group(1)

                # Construct corresponding TC column name
                tc_col = f'Flow_TC_O_{suffix}_[%]'
                # Optional: Check corresponding name column exists
                name_col = f'Output_Flow_O_{suffix}'

                # Check if the ID and TC columns exist for this suffix and have valid data
                if id_col in row_data and tc_col in row_data and pd.notna(row_data[id_col]) and pd.notna(row_data[tc_col]):
                     # Optional: Check if the Name column exists and is not 'N.A.'
                    if name_col in row_data and str(row_data[name_col]).strip() == 'N.A.':
                         continue # Skip if explicitly marked as not applicable

                    flow_id_str = str(row_data[id_col]).strip()
                    tc_value = row_data[tc_col]

                    # Parse the flow ID (e.g., "F_20_15") to get the process numbers (e.g., "20_15")
                    # Use regex for safer parsing
                    match_flow = re.match(r'F_(\d+)_(\d+)', flow_id_str, re.IGNORECASE)
                    if match_flow:
                        tc_suffix_name = f"{match_flow.group(1)}_{match_flow.group(2)}"
                        param_name = f"TC_{tc_suffix_name}"

                        # Ensure TC value is numeric
                        try:
                             tc_numeric_value = float(tc_value)
                             # ODYM parameters expect a value that can broadcast or a full array
                             # Here, we assume the TC is constant over time
                             ParameterDict[param_name] = msc.Parameter(Name=param_name, ID=parameter_id_counter, P_Res=process.ID,
                                                                   Indices='t,e', # Though value is constant, structure expects indices
                                                                   Values=tc_numeric_value, Unit='1') # Unit '1' for fraction/percentage
                             parameter_id_counter += 1
                        except (ValueError, TypeError):
                             print(f"WARNING: Invalid numeric value '{tc_value}' for TC '{param_name}' in Process {process.ID}. Skipping parameter.")
                    else:
                         print(f"WARNING: Could not parse Flow ID '{flow_id_str}' to create TC parameter name in Process {process.ID}. Check format 'F_X_Y'.")
        # else: # Optional warning if process marked 'TC' but no row found
        #     print(f"WARNING: Process {process.ID} ('{process.Name}') marked as having TCs, but no data found in sheet '{TC_DATA_SHEET}'.")


print(f"Reading content parameters (WC, DM, CC) from sheet '{FLOW_DEF_SHEET}'...")
# --- Read Flow Content Parameters (WC, DM, CC) ---
content_params_added = 0
for index, row in definition_flows_for_params.iterrows():
    flow_id = row.get('Flow_ID')
    if pd.notna(flow_id):
        flow_id_str = str(flow_id).strip()
        # Check if this flow was actually defined in the system
        if flow_id_str in Dyn_MFA_System.FlowDict:
            # Loop through the elements defining content (excluding 'material')
            for element_name in ELEMENTS[1:]: # WC, DM, CC
                param_name = f"{element_name}_{flow_id_str}"
                # Check if column exists in the DataFrame
                if element_name in row and pd.notna(row[element_name]):
                    try:
                        content_value = float(row[element_name])
                        # Assume content is constant over time
                        ParameterDict[param_name] = msc.Parameter(Name=param_name, ID=parameter_id_counter, P_Res=None, # Not linked to a single process TC calculation
                                                              Indices='t,e', Values=content_value, Unit='1') # Unit '1' for fraction
                        parameter_id_counter += 1
                        content_params_added +=1
                    except (ValueError, TypeError):
                         print(f"WARNING: Invalid numeric value '{row[element_name]}' for content parameter '{param_name}'. Skipping.")
                # else: # Optional warning for missing content columns
                #     print(f"INFO: Missing content parameter '{param_name}' (column '{element_name}') for flow '{flow_id_str}' in sheet '{FLOW_DEF_SHEET}'.")


print(f"Defined {len([p for p in ParameterDict if p.startswith('TC_')])} TC parameters.")
print(f"Defined {content_params_added} content parameters (WC, DM, CC).")


# %% Define dynamic stock model (DSM) parameters for MBC Use Phase

print("Defining DSM parameters for MBC Use Phase...")
# Check if required config variables exist
if not all([isinstance(MBC_LIFETIMES_TAU, list), isinstance(MBC_LIFETIMES_SIGMA, list), len(MBC_LIFETIMES_TAU) == len(MBC_LIFETIMES_SIGMA)]):
     raise ValueError("Configuration error: MBC_LIFETIMES_TAU and MBC_LIFETIMES_SIGMA must be lists of equal length.")

# Add mean lifetimes (tau) to ParameterDict
ParameterDict['tau'] = msc.Parameter(Name='mean product lifetime', ID=parameter_id_counter, P_Res=MBC_PROCESS_ID, # Associated with Use Phase process
                                   Indices=None, # No standard ODYM indices needed here
                                   Values=MBC_LIFETIMES_TAU, Unit='yr')
parameter_id_counter += 1

# Add standard deviations (sigma) to ParameterDict
ParameterDict['sigma'] = msc.Parameter(Name='stddev of mean product lifetime', ID=parameter_id_counter, P_Res=MBC_PROCESS_ID,
                                     Indices=None,
                                     Values=MBC_LIFETIMES_SIGMA, Unit='yr')
parameter_id_counter += 1

print(f"Defined DSM parameters: tau={ParameterDict['tau'].Values}, sigma={ParameterDict['sigma'].Values}")


# %% Define first-order model process (FOMP) parameters for Mineralization

print("Defining FOMP parameters for biochar mineralization...")
# Note: These are stored separately for now as they are used by the bioDYM addon,
# but could potentially be integrated into the main ParameterDict if needed elsewhere.
# Create empty dictionary for FOMP-specific parameters
BioParameterDict = {}

# Define Parameter f (labile fraction)
BioParameterDict['f'] = bicl.fompParameter(Name='f_labile_fraction', ID=1, P_Res=FOMP_INPUT_PROCESS_ID, # Link to process providing biochar
                                         Indices=None,
                                         Values=FOMP_PARAM_F, Uncert=None, Unit='1')
# Define Parameter k1 (labile decay rate)
BioParameterDict['k1'] = bicl.fompParameter(Name='k1_labile_decay', ID=2, P_Res=FOMP_INPUT_PROCESS_ID,
                                          Indices=None,
                                          Values=FOMP_PARAM_K1, Uncert=None, Unit='1/yr') # Corrected unit
# Define Parameter k2 (stable decay rate)
BioParameterDict['k2'] = bicl.fompParameter(Name='k2_stable_decay', ID=3, P_Res=FOMP_INPUT_PROCESS_ID,
                                          Indices=None,
                                          Values=FOMP_PARAM_K2, Uncert=None, Unit='1/yr') # Corrected unit

print(f"Defined FOMP parameters: f={BioParameterDict['f'].Values}, k1={BioParameterDict['k1'].Values}, k2={BioParameterDict['k2'].Values}")


# %% Assign final ParameterDict to MFA system (if not already done by reference)
Dyn_MFA_System.ParameterDict = ParameterDict
print(f"Total parameters defined in system: {len(Dyn_MFA_System.ParameterDict)}")

if VERBOSE_DEBUG_PRINTING:
    print('\nParameter definition summary:')
    for name, param in Dyn_MFA_System.ParameterDict.items():
        # Limit printing long arrays/values
        value_str = str(param.Values)
        if isinstance(param.Values, (np.ndarray, list)) and len(param.Values) > 5:
             value_str = f"[{value_str.split('[')[1].split(']')[0][:30]}...]" # Truncate long values
        print(f"  Name: {param.Name}, Value(s): {value_str}, Unit: {param.Unit}")


# %% Consistency check

print("\nPerforming ODYM system consistency check...")
try:
    # Check dimensions, process/flow links, etc.
    Dyn_MFA_System.Consistency_Check()
    print("Consistency check passed.")
except Exception as e:
    print(f"ERROR during consistency check: {e}")
    print("Please review system definitions (Processes, Flows, Stocks, Parameters).")
    # Depending on severity, you might want to exit
    # sys.exit("Stopping due to consistency check failure.")


# %% [markdown]
# ## 3 MFA Calculations
#
# Now, the solution of the MFA is calculated. Since most flows have either input data or TCs and substance contents are given, they can be easily calculated. However, this system includes a dynamic stock modeling (dsm) and a first order model process (FOMP) for the mineralization of carbon in soil. The idea is that first, all flows are calculated with TCs that are independent of dsm or FOMP. Then, dsm is performed and subsequently, all flows up to the FOMP are calculated. After that, the bioDYM_addon functions are used to calculate the mineralization. Finally, all following flows and stocks are calculated.

# %% Overview of process inputs/outputs/stocks (optional debug)

if VERBOSE_DEBUG_PRINTING:
    print('\n--- Process, Flows, and Stocks Overview ---')
    process_overview = {}
    for process in Dyn_MFA_System.ProcessList:
        process_id = process.ID
        input_flows = {flow.Name for flow in Dyn_MFA_System.FlowDict.values() if flow.P_End == process_id}
        output_flows = {flow.Name for flow in Dyn_MFA_System.FlowDict.values() if flow.P_Start == process_id}
        stock_changes = {stock.Name for stock in Dyn_MFA_System.StockDict.values() if stock.P_Res == process_id and stock.Type == 1} # Type 1 is dS
        process_overview[process_id] = {'Name': process.Name, 'Inputs': input_flows, 'Outputs': output_flows, 'StockChanges': stock_changes}
        print(f"\nProcess ID: {process_id} ({process.Name})")
        print(f"  Input Flows: {input_flows if input_flows else 'None'}")
        print(f"  Output Flows: {output_flows if output_flows else 'None'}")
        print(f"  Stock Changes: {stock_changes if stock_changes else 'None'}")
    print('--- End Overview ---')


# %% [markdown]
# ### 3.1 Solution MFA

# %% [markdown]
# #### 3.1.1 Solution MFA pt. I (until MBC dynamic stock modelling)

# %% Helper function to calculate flow value from TC (optional, keeping multi-stage loop for now)
# (See thought process - decided against function to keep explicit staging clear)

# %% Calculate flows up to the input of the MBC Use Phase (Process 3)

print("\n--- MFA Calculation: Part I (Up to MBC Use Phase Input) ---")

# Identify the flow entering the DSM process (MBC Use Phase)
# Assumes F_02_03 is the main inflow to process 3 based on diagram/setup
DSM_input_flow_name = f"F_{Dyn_MFA_System.ProcessList[Dyn_MFA_System.ProcessList.index(next(p for p in Dyn_MFA_System.ProcessList if p.ID == 2))].ID}_{MBC_PROCESS_ID}" # Should be F_02_03

# Flows calculated in this stage
calculated_flows_pt1 = set(flows_with_input_data) # Start with flows that had direct input

# We need to iterate potentially multiple times if calculations depend on each other
# A simpler approach for this structure is to calculate in order based on the diagram flow
# Assuming: Env->13->20->(15, 16, 1); Env->4->1; Env->11->2; Env->8->2; (1,4)->1; 1->(5, 2); 2->3(DSM input)
# We calculate flows based on available inputs and TCs until F_02_03 is calculated.

# Define the calculation order based on assumed dependencies (adjust if needed!)
# This order respects the flow from raw materials towards the DSM input
calculation_order_pt1 = [
    'F_00_13', 'F_13_20', # Rye cultivation path
    'F_20_15', 'F_20_16', 'F_20_01', # Rye harvest outputs
    'F_00_04', 'F_04_01', # Livestock path to biogas
    # Now biogas process 1 outputs (requires F_20_01 and F_04_01)
    'F_01_05', 'F_01_21', 'F_01_02', # Biogas outputs (incineration, delta, to MBC prod)
    # Now MBC Production inputs (process 2)
    'F_00_11', 'F_11_02', # Millet path to MBC prod
    'F_00_08', 'F_08_02', # Water import to MBC prod
    # Now MBC Production outputs (requires F_01_02, F_11_02, F_08_02)
    'F_02_06', 'F_02_14', 'F_02_12', 'F_02_03', # MBC prod outputs (EOL, water export, delta, to Use Phase)
]

# Add flows with input data that might not be in the explicit order
calculation_order_pt1 = list(dict.fromkeys(list(flows_with_input_data) + calculation_order_pt1))


calculation_made_progress = True
max_iterations = len(Dyn_MFA_System.FlowDict) + 5 # Safety limit
iteration = 0

while calculation_made_progress and iteration < max_iterations:
    calculation_made_progress = False
    iteration += 1
    if VERBOSE_DEBUG_PRINTING: print(f"\nCalculation Iteration {iteration} (Part I)")

    for flow_name in calculation_order_pt1:
        if flow_name not in Dyn_MFA_System.FlowDict:
            print(f"WARNING: Flow '{flow_name}' listed in calculation order but not defined in FlowDict. Skipping.")
            continue

        flow = Dyn_MFA_System.FlowDict[flow_name]

        # Skip if already calculated or has input data assigned
        if flow_name in calculated_flows_pt1:
            continue

        # Check if this flow can be calculated using a TC parameter
        flow_id_simple = '_'.join(flow.Name.split('_')[1:3])
        tc_param_name = f"TC_{flow_id_simple}"

        if tc_param_name in Dyn_MFA_System.ParameterDict:
            # Find required input flows to the source process (flow.P_Start)
            input_flow_names_to_process = {
                in_flow.Name for in_flow in Dyn_MFA_System.FlowDict.values()
                if in_flow.P_End == flow.P_Start
            }

            # Check if all required input flows have been calculated (or had initial data)
            inputs_ready = True
            sum_input_flows_material = np.zeros(Model_No_Of_Years)

            if not input_flow_names_to_process:
                # Handle case where TC exists but there are no feeding flows (e.g., flow from Env with TC?) - unusual
                # print(f"Note: Flow {flow.Name} has TC but no input flows to process {flow.P_Start}. Calculation based on TC only.")
                 inputs_ready = True # Allows calculation if TC applies to 'nothing' input (e.g., generation rate)
            else:
                for name in input_flow_names_to_process:
                    if name not in calculated_flows_pt1:
                        inputs_ready = False
                        if VERBOSE_DEBUG_PRINTING: print(f"  -> Delaying {flow.Name}, waiting for input {name}")
                        break # Stop checking inputs for this flow
                    # Sum the 'material' component of ready inputs
                    sum_input_flows_material += Dyn_MFA_System.FlowDict[name].Values[:, 0]

            # If all inputs are ready, calculate the flow
            if inputs_ready:
                 if VERBOSE_DEBUG_PRINTING: print(f"  Calculating {flow.Name} using TC {tc_param_name}...")
                 tc_value = Dyn_MFA_System.ParameterDict[tc_param_name].Values
                 # Calculate 'material' flow = Sum(Input Materials) * TC
                 flow.Values[:, 0] = sum_input_flows_material * tc_value

                 # Calculate substance flows (WC, DM, CC) using content parameters
                 for i, element_name in enumerate(ELEMENTS[1:], start=1):
                     content_param_key = f"{element_name}_{flow.Name}"
                     if content_param_key in Dyn_MFA_System.ParameterDict:
                         flow.Values[:, i] = flow.Values[:, 0] * Dyn_MFA_System.ParameterDict[content_param_key].Values
                     else:
                         # Content parameter missing, set to zero and warn
                         if np.any(flow.Values[:, 0]): # Only warn if material flow is non-zero
                             print(f"WARNING: Missing content parameter '{content_param_key}' for calculating {element_name} in flow '{flow.Name}'. Setting to 0.")
                         flow.Values[:, i] = 0

                 calculated_flows_pt1.add(flow_name)
                 calculation_made_progress = True # Mark progress

        # Else: Flow has no TC defined and no input data assigned - remains zero for now
        # It might be calculated in later stages or represent a boundary flow error

    # Check if the target DSM input flow is calculated
    if DSM_input_flow_name in calculated_flows_pt1:
        print(f"Input flow to DSM ({DSM_input_flow_name}) calculated. Ending Part I.")
        break # Exit the loop

if iteration == max_iterations:
    print("WARNING: Max calculation iterations reached in Part I. Check for circular dependencies or missing data/TCs.")
if DSM_input_flow_name not in calculated_flows_pt1:
     print(f"WARNING: Calculation Part I finished, but DSM input flow '{DSM_input_flow_name}' was not calculated. Check dependencies and TCs.")

print(f"Calculated {len(calculated_flows_pt1) - len(flows_with_input_data)} flows in Part I.")


# %% [markdown]
# #### 3.1.2 Solution MFA pt. II (Dynamic stock MBC use-phase calculation)

# %% Prepare for and apply Dynamic Stock Model (DSM)

print("\n--- MFA Calculation: Part II (MBC Use Phase DSM) ---")

# Check if the input flow to DSM was successfully calculated
if DSM_input_flow_name not in calculated_flows_pt1 or not np.any(Dyn_MFA_System.FlowDict[DSM_input_flow_name].Values):
     print(f"WARNING: Input flow '{DSM_input_flow_name}' for DSM has zero values or was not calculated. DSM results will be zero.")
     # Initialize DSM outputs to zero and skip calculation
     # Find the output flow from DSM (e.g., F_03_07)
     DSM_output_flow_name = f"F_{MBC_PROCESS_ID}_{Dyn_MFA_System.ProcessList[Dyn_MFA_System.ProcessList.index(next(p for p in Dyn_MFA_System.ProcessList if p.ID == 7))].ID}" # Should be F_03_07
     if DSM_output_flow_name in Dyn_MFA_System.FlowDict:
          Dyn_MFA_System.FlowDict[DSM_output_flow_name].Values[:, :] = 0
     if f"dS_{MBC_PROCESS_ID}" in Dyn_MFA_System.StockDict:
          Dyn_MFA_System.StockDict[f"dS_{MBC_PROCESS_ID}"].Values[:, :] = 0
          Dyn_MFA_System.StockDict[f"S_{MBC_PROCESS_ID}"].Values[:, :] = 0
     calculated_flows_dsm_output = set()

else:
    # --- Prepare DSM Inputs ---
    # Create a temporary dictionary to hold category-specific DSM flows/stocks
    MBC_DSM_Data = {}
    inflow_material = Dyn_MFA_System.FlowDict[DSM_input_flow_name].Values[:, 0] # Material inflow

    # Split the inflow according to defined fractions for lifetime categories
    if len(MBC_LIFETIME_SPLITS) != len(MBC_LIFETIMES_TAU):
         raise ValueError("Configuration mismatch: Number of MBC lifetime splits differs from number of tau/sigma values.")
    if not np.isclose(sum(MBC_LIFETIME_SPLITS), 1.0):
         print(f"WARNING: MBC lifetime splits {MBC_LIFETIME_SPLITS} do not sum to 1. Normalizing.")
         total_split = sum(MBC_LIFETIME_SPLITS)
         MBC_LIFETIME_SPLITS = [s / total_split for s in MBC_LIFETIME_SPLITS]

    num_mbc_categories = len(MBC_LIFETIMES_TAU)
    split_inflows = np.zeros((Model_No_Of_Years, num_mbc_categories))
    for i, split_fraction in enumerate(MBC_LIFETIME_SPLITS):
         split_inflows[:, i] = inflow_material * split_fraction

    # Store split inflow (useful for plotting later)
    MBC_DSM_Data['Inflow_Categories'] = split_inflows
    # Initialize arrays for categorized outflows and stocks
    MBC_DSM_Data['Outflow_Categories'] = np.zeros_like(split_inflows)
    MBC_DSM_Data['Stock_Categories'] = np.zeros_like(split_inflows)
    MBC_DSM_Data['StockChange_Categories'] = np.zeros_like(split_inflows)

    # --- Apply DSM for each category ---
    print(f"Applying DSM for {num_mbc_categories} MBC categories...")
    time_vector = np.array(MyYears)

    for category_idx in range(num_mbc_categories):
        tau_val = MBC_LIFETIMES_TAU[category_idx]
        sigma_val = MBC_LIFETIMES_SIGMA[category_idx]
        inflow_vals = split_inflows[:, category_idx]

        if VERBOSE_DEBUG_PRINTING:
            print(f"  Category {category_idx+1}: tau={tau_val}, sigma={sigma_val}")

        # Setup the dynamic stock model for this category
        # Using 'Normal' distribution based on presence of Mean and StdDev
        dsm_category = dsm.DynamicStockModel(
            t=time_vector,
            i=inflow_vals,
            lt={'Type': 'Normal', 'Mean': [tau_val], 'StdDev': [sigma_val]} # Pass lists
        )

        # Perform DSM calculations
        # Stock_by_cohort = dsm_category.compute_s_c_inflow_driven() # Stock per cohort over time
        O_C = dsm_category.compute_o_c_inflow_driven() # Outflow per cohort over time
        S_C = dsm_category.compute_s_c_inflow_driven() # Recompute stock per cohort

        # O = dsm_category.compute_outflow_total() # Total outflow over time
        # S = dsm_category.compute_stock_total()   # Total stock over time
        O = O_C.sum(axis=1)
        S = S_C.sum(axis=1)
        DS = dsm_category.compute_stock_change() # Total stock change over time (Inflow - Outflow)

        # Store results for this category
        MBC_DSM_Data['Outflow_Categories'][:, category_idx] = O
        MBC_DSM_Data['Stock_Categories'][:, category_idx] = S
        MBC_DSM_Data['StockChange_Categories'][:, category_idx] = DS


    # --- Aggregate DSM results and update system flows/stocks ---
    # Total outflow (sum across categories) is the material component of F_03_07
    total_outflow_material = MBC_DSM_Data['Outflow_Categories'].sum(axis=1)
    DSM_output_flow_name = f"F_{MBC_PROCESS_ID}_{Dyn_MFA_System.ProcessList[Dyn_MFA_System.ProcessList.index(next(p for p in Dyn_MFA_System.ProcessList if p.ID == 7))].ID}" # F_03_07

    if DSM_output_flow_name in Dyn_MFA_System.FlowDict:
        dsm_outflow_obj = Dyn_MFA_System.FlowDict[DSM_output_flow_name]
        dsm_outflow_obj.Values[:, 0] = total_outflow_material
        # Calculate substance flows for the outflow using its content parameters
        for i, element_name in enumerate(ELEMENTS[1:], start=1):
             content_param_key = f"{element_name}_{dsm_outflow_obj.Name}"
             if content_param_key in Dyn_MFA_System.ParameterDict:
                 dsm_outflow_obj.Values[:, i] = dsm_outflow_obj.Values[:, 0] * Dyn_MFA_System.ParameterDict[content_param_key].Values
             else:
                 if np.any(dsm_outflow_obj.Values[:, 0]):
                     print(f"WARNING: Missing content parameter '{content_param_key}' for DSM output flow '{dsm_outflow_obj.Name}'. Setting {element_name} to 0.")
                 dsm_outflow_obj.Values[:, i] = 0
        calculated_flows_dsm_output = {DSM_output_flow_name}
        print(f"DSM output flow '{DSM_output_flow_name}' calculated.")
    else:
         print(f"WARNING: DSM output flow '{DSM_output_flow_name}' not found in FlowDict. Cannot store results.")
         calculated_flows_dsm_output = set()


    # Calculate total stock change and stock for the DSM process (all categories)
    # Stock change = Inflow - Outflow (should match sum of DS from categories)
    total_stock_change = Dyn_MFA_System.FlowDict[DSM_input_flow_name].Values - Dyn_MFA_System.FlowDict[DSM_output_flow_name].Values

    # Total stock = Cumulative sum of stock change
    total_stock = total_stock_change.cumsum(axis=0)

    # Update the system StockDict
    stock_change_name = f"dS_{MBC_PROCESS_ID}"
    stock_name = f"S_{MBC_PROCESS_ID}"
    if stock_change_name in Dyn_MFA_System.StockDict:
        Dyn_MFA_System.StockDict[stock_change_name].Values = total_stock_change
        print(f"DSM stock change '{stock_change_name}' calculated.")
    else:
         print(f"WARNING: Stock change '{stock_change_name}' not found in StockDict.")

    if stock_name in Dyn_MFA_System.StockDict:
         Dyn_MFA_System.StockDict[stock_name].Values = total_stock
         print(f"DSM stock '{stock_name}' calculated.")
    else:
         print(f"WARNING: Stock '{stock_name}' not found in StockDict.")


# %% [markdown]
# #### 3.1.3 Solution MFA pt. III (until mineralization process)

# %% Calculate flows after DSM up to the input of the FOMP process

print("\n--- MFA Calculation: Part III (After DSM, up to FOMP Input) ---")

# Identify the input flow to the FOMP process (Lithosphere)
# Assumes F_09_17 is the main inflow from Pyrolysis (9) to Lithosphere (17)
FOMP_input_flow_name = f"F_{FOMP_INPUT_PROCESS_ID}_{FOMP_PROCESS_ID}" # Should be F_09_17

# Flows calculated so far (Part I + DSM output)
calculated_flows_pt3 = calculated_flows_pt1.union(calculated_flows_dsm_output)

# Define calculation order for this stage (flows between DSM output and FOMP input)
# Assumes: 7->(9, 10); 9->17(FOMP input); 10->(18, 19); 9->(19, 14); 10->14
calculation_order_pt3 = [
     # MBC EoL Treatment outputs (Process 7, requires F_03_07 from DSM)
    'F_07_09', 'F_07_10',
    # Pyrolysis outputs (Process 9, requires F_07_09)
    'F_09_19', 'F_09_14', 'F_09_17', # Includes FOMP input
    # Incineration outputs (Process 10, requires F_07_10)
    'F_10_18', 'F_10_19', 'F_10_14',
]

# Iterative calculation loop for this stage
calculation_made_progress = True
iteration = 0

while calculation_made_progress and iteration < max_iterations:
    calculation_made_progress = False
    iteration += 1
    if VERBOSE_DEBUG_PRINTING: print(f"\nCalculation Iteration {iteration} (Part III)")

    for flow_name in calculation_order_pt3:
        if flow_name not in Dyn_MFA_System.FlowDict:
            print(f"WARNING: Flow '{flow_name}' in calculation order Part III but not defined. Skipping.")
            continue

        flow = Dyn_MFA_System.FlowDict[flow_name]

        # Skip if already calculated
        if flow_name in calculated_flows_pt3:
            continue

        # Check if it can be calculated by TC
        flow_id_simple = '_'.join(flow.Name.split('_')[1:3])
        tc_param_name = f"TC_{flow_id_simple}"

        if tc_param_name in Dyn_MFA_System.ParameterDict:
            input_flow_names_to_process = {
                in_flow.Name for in_flow in Dyn_MFA_System.FlowDict.values()
                if in_flow.P_End == flow.P_Start
            }

            inputs_ready = True
            sum_input_flows_material = np.zeros(Model_No_Of_Years)

            if not input_flow_names_to_process:
                 inputs_ready = True # Allow TC on 'nothing' input if meaningful
            else:
                for name in input_flow_names_to_process:
                    if name not in calculated_flows_pt3:
                        inputs_ready = False
                        if VERBOSE_DEBUG_PRINTING: print(f"  -> Delaying {flow.Name}, waiting for input {name}")
                        break
                    sum_input_flows_material += Dyn_MFA_System.FlowDict[name].Values[:, 0]

            if inputs_ready:
                 if VERBOSE_DEBUG_PRINTING: print(f"  Calculating {flow.Name} using TC {tc_param_name}...")
                 tc_value = Dyn_MFA_System.ParameterDict[tc_param_name].Values
                 flow.Values[:, 0] = sum_input_flows_material * tc_value

                 # Calculate substance flows
                 for i, element_name in enumerate(ELEMENTS[1:], start=1):
                     content_param_key = f"{element_name}_{flow.Name}"
                     if content_param_key in Dyn_MFA_System.ParameterDict:
                         flow.Values[:, i] = flow.Values[:, 0] * Dyn_MFA_System.ParameterDict[content_param_key].Values
                     else:
                         if np.any(flow.Values[:, 0]):
                              print(f"WARNING: Missing content parameter '{content_param_key}' for flow '{flow.Name}'. Setting {element_name} to 0.")
                         flow.Values[:, i] = 0

                 calculated_flows_pt3.add(flow_name)
                 calculation_made_progress = True

    # Check if the target FOMP input flow is calculated
    if FOMP_input_flow_name in calculated_flows_pt3:
        print(f"Input flow to FOMP ({FOMP_input_flow_name}) calculated. Ending Part III.")
        break

if iteration == max_iterations:
    print("WARNING: Max calculation iterations reached in Part III. Check dependencies.")
if FOMP_input_flow_name not in calculated_flows_pt3:
     print(f"WARNING: Calculation Part III finished, but FOMP input flow '{FOMP_input_flow_name}' was not calculated. Check dependencies and TCs.")

print(f"Calculated {len(calculated_flows_pt3) - len(calculated_flows_pt1.union(calculated_flows_dsm_output))} new flows in Part III.")


# %% Calculate intermediate stocks (those not dependent on FOMP output)

print("\nCalculating intermediate stocks (excluding FOMP/Atmosphere)...")

# Stocks calculated so far (only the DSM stock)
calculated_stocks = {f"S_{MBC_PROCESS_ID}", f"dS_{MBC_PROCESS_ID}"}
# Define stocks to exclude (depend on FOMP output F_17_19 or were done by DSM)
excluded_stock_processes = {FOMP_PROCESS_ID, 19, MBC_PROCESS_ID} # Lithosphere, Atmosphere, MBC Use Phase

stocks_calculated_now = 0
for stock_obj in Dyn_MFA_System.StockDict.values():
    stock_name = stock_obj.Name
    process_id = stock_obj.P_Res

    # Skip if already calculated or excluded
    if stock_name in calculated_stocks or process_id in excluded_stock_processes:
        continue

    # Calculate stock change (dS) first
    if stock_obj.Type == 1: # Type 1 is dS
        # Find relevant input and output flows for this process
        input_flows_to_stock_process = {
            flow.Name for flow in Dyn_MFA_System.FlowDict.values()
            if flow.P_End == process_id
        }
        output_flows_from_stock_process = {
            flow.Name for flow in Dyn_MFA_System.FlowDict.values()
            if flow.P_Start == process_id
        }

        # Check if all relevant flows have been calculated
        all_flows_ready = True
        sum_input_values = np.zeros((Model_No_Of_Years, len(ELEMENTS)))
        sum_output_values = np.zeros((Model_No_Of_Years, len(ELEMENTS)))

        for flow_name in input_flows_to_stock_process:
            if flow_name not in calculated_flows_pt3: # Check against all calculated flows so far
                 all_flows_ready = False
                 if VERBOSE_DEBUG_PRINTING: print(f"  -> Delaying stock {stock_name}, waiting for input flow {flow_name}")
                 break
            sum_input_values += Dyn_MFA_System.FlowDict[flow_name].Values

        if all_flows_ready:
            for flow_name in output_flows_from_stock_process:
                # Special check: FOMP input flow F_09_17 might be an output here but needed for next stage
                if flow_name == FOMP_input_flow_name and flow_name not in calculated_flows_pt3:
                     all_flows_ready = False
                     if VERBOSE_DEBUG_PRINTING: print(f"  -> Delaying stock {stock_name}, waiting for output flow {flow_name}")
                     break
                elif flow_name not in calculated_flows_pt3:
                    all_flows_ready = False
                    if VERBOSE_DEBUG_PRINTING: print(f"  -> Delaying stock {stock_name}, waiting for output flow {flow_name}")
                    break
                sum_output_values += Dyn_MFA_System.FlowDict[flow_name].Values

        # Calculate dS = Sum(Inputs) - Sum(Outputs)
        if all_flows_ready:
            stock_obj.Values = sum_input_values - sum_output_values
            calculated_stocks.add(stock_name)
            stocks_calculated_now +=1
            if VERBOSE_DEBUG_PRINTING:
                print(f"  Calculated stock change: {stock_name}")

            # Calculate corresponding S (stock level) using cumsum
            stock_level_name = f"S_{process_id}"
            if stock_level_name in Dyn_MFA_System.StockDict:
                 Dyn_MFA_System.StockDict[stock_level_name].Values = stock_obj.Values.cumsum(axis=0)
                 calculated_stocks.add(stock_level_name)
                 if VERBOSE_DEBUG_PRINTING:
                     print(f"  Calculated stock level: {stock_level_name}")
            else:
                 print(f"WARNING: Stock level '{stock_level_name}' corresponding to '{stock_name}' not found.")

print(f"Calculated {stocks_calculated_now} intermediate stock changes (and levels).")


# %% [markdown]
# #### 3.1.4 Solution MFA pt. IV (FOMP mineralization process)
#
# The carbon mineralization process in the soil is calculated with a first order decay model according to (Cayuela et al., 2010) based on (Robertson & Paul, 2000):
#
# $$ C_{remaining} (t)=f \cdot exp⁡(-k_{1} \cdot t)+(1-f) \cdot exp⁡(-k_{2} \cdot t) $$
#
# Where:
# *   $C_{remaining}(t)$ is the fraction of carbon remaining after time $t$.
# *   $f$ is the fraction of the initial carbon in the rapidly decomposing (labile) pool.
# *   $k_1$ is the decay rate constant for the labile pool (per year).
# *   $k_2$ is the decay rate constant for the slowly decomposing (stable) pool (per year).
# *   $t$ is the time elapsed since application (in years).
#
# This calculation determines the carbon remaining in the soil stock (Process 17) originating from the biochar input (F_09_17). The difference between the carbon input and the net stock change represents the carbon mineralized and released (Flow F_17_19).

# %% Apply First Order Model Process (FOMP) for mineralization

print("\n--- MFA Calculation: Part IV (FOMP Mineralization) ---")

# Check if the input flow to FOMP was calculated
if FOMP_input_flow_name not in calculated_flows_pt3 or not np.any(Dyn_MFA_System.FlowDict[FOMP_input_flow_name].Values):
    print(f"WARNING: Input flow '{FOMP_input_flow_name}' for FOMP has zero values or was not calculated. FOMP results (stock 17, flow F_17_19) will be zero.")
    # Initialize FOMP outputs to zero
    FOMP_output_flow_name = f"F_{FOMP_PROCESS_ID}_19" # Assuming F_17_19 to Atmosphere
    if FOMP_output_flow_name in Dyn_MFA_System.FlowDict:
        Dyn_MFA_System.FlowDict[FOMP_output_flow_name].Values[:, :] = 0
    if f"dS_{FOMP_PROCESS_ID}" in Dyn_MFA_System.StockDict:
        Dyn_MFA_System.StockDict[f"dS_{FOMP_PROCESS_ID}"].Values[:, :] = 0
        Dyn_MFA_System.StockDict[f"S_{FOMP_PROCESS_ID}"].Values[:, :] = 0
    calculated_flows_fomp_output = set()

else:
    # Get the index for Carbon ('CC')
    try:
        carbon_index = ELEMENTS.index('CC')
        dm_index = ELEMENTS.index('DM')
        wc_index = ELEMENTS.index('WC')
    except ValueError as e:
         raise ValueError(f"Model element '{e}' needed for FOMP not found in configured ELEMENTS list: {ELEMENTS}")

    # Get the annual carbon input flow to the soil process (Lithosphere)
    fomp_inflow_carbon = Dyn_MFA_System.FlowDict[FOMP_input_flow_name].Values[:, carbon_index].copy()
    # Get the total material inflow for calculating non-carbon stock change
    fomp_inflow_material = Dyn_MFA_System.FlowDict[FOMP_input_flow_name].Values[:, 0].copy()
    fomp_inflow_dm = Dyn_MFA_System.FlowDict[FOMP_input_flow_name].Values[:, dm_index].copy()
    fomp_inflow_wc = Dyn_MFA_System.FlowDict[FOMP_input_flow_name].Values[:, wc_index].copy()


    # Time vector relative to start (0 to N-1 years) for decay calculation
    time_decay = np.arange(Model_No_Of_Years)

    # Calculate the fraction of carbon remaining from a single cohort after time t
    f = BioParameterDict['f'].Values
    k1 = BioParameterDict['k1'].Values
    k2 = BioParameterDict['k2'].Values
    # Ensure k1 and k2 are non-negative
    k1 = max(0, k1)
    k2 = max(0, k2)
    fraction_remaining = f * np.exp(-k1 * time_decay) + (1 - f) * np.exp(-k2 * time_decay)
    # Ensure fraction starts at 1 and does not exceed it or go below 0
    fraction_remaining = np.clip(fraction_remaining, 0, 1)
    fraction_remaining[0] = 1.0 # At time 0, 100% remains

    if VERBOSE_DEBUG_PRINTING:
        print(f"  FOMP Decay curve (fraction remaining): {fraction_remaining[:5]}...")

    # --- Cohort-based calculation ---
    # Create a matrix where column 'c' holds the inflow of cohort 'c'
    # We need inflow amount at year c, replicated down the column for years >= c
    inflow_matrix = np.zeros((Model_No_Of_Years, Model_No_Of_Years))
    for c in range(Model_No_Of_Years):
        inflow_matrix[c:, c] = fomp_inflow_carbon[c]

    # Create a matrix where element [t, c] is the decay factor for cohort c at time t (age t-c)
    decay_matrix = np.zeros((Model_No_Of_Years, Model_No_Of_Years))
    for c in range(Model_No_Of_Years):
        age = time_decay[c:] - c  # Age of cohort c at time steps t >= c
        decay_matrix[c:, c] = fraction_remaining[age]

    # Calculate remaining C from each cohort at each time step
    remaining_c_matrix = inflow_matrix * decay_matrix

    # Total remaining C stock at time t is the sum across cohorts (columns) for row t
    fomp_stock_carbon_total = np.sum(remaining_c_matrix, axis=1)

    # Calculate the net change in this specific carbon stock pool per year
    # dS_C[t] = S_C[t] - S_C[t-1] (with S_C[-1] = 0)
    fomp_stock_change_carbon = np.diff(fomp_stock_carbon_total, prepend=0)

    # Calculate carbon mineralized (outflow) = Carbon Input[t] - Net Carbon Stock Change[t]
    fomp_outflow_carbon = fomp_inflow_carbon - fomp_stock_change_carbon
    # Ensure outflow is not negative due to floating point issues
    fomp_outflow_carbon = np.maximum(0, fomp_outflow_carbon)

    # --- Update System Flows and Stocks ---
    # Update the outflow F_17_19 (assuming only carbon mineralizes to atmosphere)
    FOMP_output_flow_name = f"F_{FOMP_PROCESS_ID}_19" # F_17_19
    if FOMP_output_flow_name in Dyn_MFA_System.FlowDict:
        fomp_outflow_obj = Dyn_MFA_System.FlowDict[FOMP_output_flow_name]
        # Initialize all elements to zero
        fomp_outflow_obj.Values[:, :] = 0
        # Assign calculated carbon outflow
        fomp_outflow_obj.Values[:, carbon_index] = fomp_outflow_carbon
        # Assume mineralized C leaves as DM (e.g., CO2)
        fomp_outflow_obj.Values[:, dm_index] = fomp_outflow_carbon
        # Assume this outflow contributes to the 'material' total
        fomp_outflow_obj.Values[:, 0] = fomp_outflow_carbon # Or adjust if material definition differs

        calculated_flows_fomp_output = {FOMP_output_flow_name}
        print(f"FOMP output flow '{FOMP_output_flow_name}' calculated.")
    else:
         print(f"WARNING: FOMP output flow '{FOMP_output_flow_name}' not found in FlowDict.")
         calculated_flows_fomp_output = set()


    # Update the stock change (dS_17) and stock (S_17) for the Lithosphere process
    stock_change_name = f"dS_{FOMP_PROCESS_ID}" # dS_17
    stock_name = f"S_{FOMP_PROCESS_ID}"       # S_17

    if stock_change_name in Dyn_MFA_System.StockDict:
         # dS_17 = Total Inflow (F_09_17) - Total Outflow (F_17_19)
         total_inflow_values = Dyn_MFA_System.FlowDict[FOMP_input_flow_name].Values
         total_outflow_values = Dyn_MFA_System.FlowDict[FOMP_output_flow_name].Values if FOMP_output_flow_name in Dyn_MFA_System.FlowDict else np.zeros_like(total_inflow_values)
         Dyn_MFA_System.StockDict[stock_change_name].Values = total_inflow_values - total_outflow_values
         calculated_stocks.add(stock_change_name) # Mark as calculated
         print(f"FOMP stock change '{stock_change_name}' calculated.")

         # Update the total stock S_17
         if stock_name in Dyn_MFA_System.StockDict:
             Dyn_MFA_System.StockDict[stock_name].Values = Dyn_MFA_System.StockDict[stock_change_name].Values.cumsum(axis=0)
             calculated_stocks.add(stock_name) # Mark as calculated
             print(f"FOMP stock '{stock_name}' calculated.")
         else:
             print(f"WARNING: Stock '{stock_name}' not found for FOMP process.")
    else:
        print(f"WARNING: Stock change '{stock_change_name}' not found for FOMP process.")


# %% [markdown]
# #### 3.1.5 Solution MFA pt. V (last part after mineralization process)

# %% Calculate remaining flows and stocks (e.g., Atmosphere)

print("\n--- MFA Calculation: Part V (Final flows and stocks) ---")

# Flows calculated so far (Parts I, III + DSM/FOMP outputs)
calculated_flows_final = calculated_flows_pt3.union(calculated_flows_dsm_output).union(calculated_flows_fomp_output)

# Identify any remaining flows to calculate (should be none if system is fully defined)
remaining_flows = set(Dyn_MFA_System.FlowDict.keys()) - calculated_flows_final
if remaining_flows:
    print(f"WARNING: Some flows were not calculated: {remaining_flows}. Check system definition and TCs.")

# Calculate remaining stocks (e.g., Atmosphere - Process 19)
atmosphere_process_id = 19
stock_change_name_atm = f"dS_{atmosphere_process_id}"
stock_name_atm = f"S_{atmosphere_process_id}"

if stock_change_name_atm in Dyn_MFA_System.StockDict and stock_change_name_atm not in calculated_stocks:
    # Find all input flows to Atmosphere
    input_flows_to_atm = {
        flow.Name for flow in Dyn_MFA_System.FlowDict.values()
        if flow.P_End == atmosphere_process_id
    }
    # Find all output flows from Atmosphere (likely none within system boundary)
    output_flows_from_atm = {
        flow.Name for flow in Dyn_MFA_System.FlowDict.values()
        if flow.P_Start == atmosphere_process_id
    } # Should be empty unless Atmosphere flows out

    # Check if all input flows are calculated
    inputs_ready = True
    sum_input_values = np.zeros((Model_No_Of_Years, len(ELEMENTS)))
    for flow_name in input_flows_to_atm:
        if flow_name not in calculated_flows_final:
            inputs_ready = False
            print(f"WARNING: Cannot calculate Atmosphere stock, waiting for input flow {flow_name}")
            break
        sum_input_values += Dyn_MFA_System.FlowDict[flow_name].Values

    # Assume no outputs from Atmosphere within the system
    sum_output_values = np.zeros((Model_No_Of_Years, len(ELEMENTS)))
    if output_flows_from_atm:
         print(f"WARNING: Found unexpected outputs from Atmosphere: {output_flows_from_atm}. Ignoring for stock calculation.")


    if inputs_ready:
         # Calculate dS_19 = Sum(Inputs) - Sum(Outputs)
         Dyn_MFA_System.StockDict[stock_change_name_atm].Values = sum_input_values - sum_output_values
         calculated_stocks.add(stock_change_name_atm)
         print(f"Atmosphere stock change '{stock_change_name_atm}' calculated.")

         # Calculate S_19
         if stock_name_atm in Dyn_MFA_System.StockDict:
              Dyn_MFA_System.StockDict[stock_name_atm].Values = Dyn_MFA_System.StockDict[stock_change_name_atm].Values.cumsum(axis=0)
              calculated_stocks.add(stock_name_atm)
              print(f"Atmosphere stock '{stock_name_atm}' calculated.")
         else:
              print(f"WARNING: Atmosphere stock '{stock_name_atm}' not found.")
elif stock_change_name_atm in calculated_stocks:
     pass # Already calculated (e.g. if done in intermediate step)
else:
    print(f"INFO: Atmosphere stock change '{stock_change_name_atm}' not found in StockDict.")

# Verify all stocks seem to be calculated
remaining_stocks = set(Dyn_MFA_System.StockDict.keys()) - calculated_stocks
if remaining_stocks:
     print(f"WARNING: Some stocks may not have been calculated: {remaining_stocks}")

print("MFA calculations completed.")


# %% [markdown]
# #### 3.1.6 Final Mass balance check

# %% Check mass balances for all processes

print("\n--- Final Mass Balance Check ---")

try:
    # ODYM function calculates balance for each process, element, time step
    # Balance = Sum(Inputs) + dS_in - Sum(Outputs) - dS_out (should be zero)
    # Note: ODYM's dS might be defined differently; usually Balance = In - Out - dS_accumulation
    Bal = Dyn_MFA_System.MassBalance()

    # Dimensions: time x process x element
    print(f"Balance array shape: {Bal.shape}")

    # Calculate the sum of absolute balancing errors per process over all time steps and elements
    # This gives a single value per process indicating the magnitude of imbalance
    balance_summary = np.abs(Bal).sum(axis=(0, 2)) # Sum over time (axis 0) and elements (axis 2)

    # Report summary
    print("\nTotal absolute balancing error per process (sum over time & elements):")
    max_error = 0
    for pid, error in enumerate(balance_summary):
        process_name = Dyn_MFA_System.ProcessList[pid].Name
        print(f"  Process {pid} ({process_name}): {error:.6g} {Dyn_MFA_System.Unit}")
        if pid > 0: # Ignore environment process 0 for max error check if desired
             max_error = max(max_error, abs(error))

    # Check if the maximum error is acceptably small (e.g., close to floating point precision)
    tolerance = 1e-6 # Adjust tolerance as needed
    if max_error < tolerance:
        print(f"\nMass balance check passed (Max error across processes < {tolerance:.1g}).")
    else:
        print(f"\nWARNING: Mass balance check failed. Max error ({max_error:.6g}) exceeds tolerance ({tolerance:.1g}).")
        print("Review calculations, TCs, and system definitions.")

except Exception as e:
    print(f"ERROR calculating mass balance: {e}")


# %% Plot balancing error per process

# Create list of process labels (e.g., "P0", "P1", ...)
process_list_balance = [f"P{p.ID}" for p in Dyn_MFA_System.ProcessList]

# Set plot aesthetics
plt.rcParams['figure.dpi'] = PLOT_DPI
plt.figure(figsize=(12, 6)) # Adjusted size for potentially many processes

# Create bar chart
plt.bar(process_list_balance, balance_summary, color='salmon')

# Add labels, title
plt.xlabel('Processes')
plt.ylabel(f'Total Absolute Balancing Error ({Dyn_MFA_System.Unit})')
plt.title('Mass Balance Check: Total Absolute Error per Process (Sum over Time & Elements)')
plt.xticks(rotation=45, ha='right') # Rotate labels if many processes
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout() # Adjust layout to prevent labels overlapping
plt.show()


# %% [markdown]
# #### 3.1.7 Final results (Optional Print)

# %% Print final flow and stock values (if verbose)

if VERBOSE_DEBUG_PRINTING:
    print("\n--- Final Calculated Values ---")
    print("\nFlows:")
    for flow in Dyn_MFA_System.FlowDict.values():
        print(f"\n{flow.Name} (P{flow.P_Start} -> P{flow.P_End}):")
        # Print limited view (e.g., first 3 years, all elements)
        print(pd.DataFrame(flow.Values[:3, :], index=MyYears[:3], columns=ELEMENTS).round(3))

    print("\nStocks:")
    for stock in Dyn_MFA_System.StockDict.values():
        print(f"\n{stock.Name} (Process {stock.P_Res}, Type {stock.Type}):")
        print(pd.DataFrame(stock.Values[:3, :], index=MyYears[:3], columns=ELEMENTS).round(3))
    print("--- End Final Values ---")
else:
    print("\nFinal results calculated (Set VERBOSE_DEBUG_PRINTING=True to print values).")


# %% [markdown]
# ## 4 Presentation of results
#
# There are several presentation options shown here. Simple plotting is possible, but interactive sankey diagrams and stock plots are also provided. Finally, results can be exported to Excel, also.

# %% [markdown]
# ### 4.1 Simple plot example (Soil Stock)

# %% Plot Soil Stock Development (S_17)

soil_stock_name = f"S_{FOMP_PROCESS_ID}" # S_17
if soil_stock_name in Dyn_MFA_System.StockDict:
    print(f"\nPlotting development of soil stock '{soil_stock_name}'...")

    # Set plot aesthetics
    plt.rcParams['figure.dpi'] = PLOT_DPI
    fig, ax = plt.subplots(figsize=(10, 6))

    # Get time and stock values
    time_items = Dyn_MFA_System.IndexTable.loc['Time'].Classification.Items
    stock_values = Dyn_MFA_System.StockDict[soil_stock_name].Values

    # Plot total material and carbon content
    material_index = ELEMENTS.index('material')
    carbon_index = ELEMENTS.index('CC')
    ax.plot(time_items, stock_values[:, material_index], label='Total Material', marker='o', linestyle='-')
    ax.plot(time_items, stock_values[:, carbon_index], label='Carbon (CC)', marker='s', linestyle='--')

    # Add labels, title, legend
    ax.set_ylabel(f'Mass in Stock ({Dyn_MFA_System.Unit})')
    ax.set_xlabel('Year')
    ax.set_title(f'Soil Stock Development ({soil_stock_name})')
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.6)

    # Improve x-axis ticks for yearly data if not too many years
    if Model_No_Of_Years <= 20:
         ax.xaxis.set_major_locator(MultipleLocator(2)) # Tick every 2 years
         plt.xticks(rotation=45)
    elif Model_No_Of_Years <= 50:
         ax.xaxis.set_major_locator(MultipleLocator(5)) # Tick every 5 years
    # Else: Auto ticks for very long periods

    plt.tight_layout()
    plt.show()

else:
     print(f"Cannot plot soil stock: Stock '{soil_stock_name}' not found.")


# %% [markdown]
# ### 4.2 Interactive Sankey diagram

# %% Configure colors for Interactive Sankey

print("\nConfiguring colors for Sankey Diagram...")
# Define colors for flows and processes. This requires manual mapping based on the system structure.
# The order needs to match the order of flows/processes in Dyn_MFA_System.FlowDict/.ProcessList
# Example color mapping (adjust based on your actual flows and desired visual grouping):
num_flows = len(Dyn_MFA_System.FlowDict)
num_processes = len(Dyn_MFA_System.ProcessList)

# Default colors
colors_flows = ['rgba(150, 150, 150, 0.6)'] * num_flows # Default grey for flows
colors_processes = ['rgb(200, 200, 200)'] * num_processes # Default light grey for processes

# --- Assign specific colors manually (example based on original code's intent) ---
# This part is fragile and needs adjustment if the flow order changes.
# A more robust way would be to map colors based on flow names or start/end processes.
try:
    flow_names_ordered = list(Dyn_MFA_System.FlowDict.keys())

    def set_color(prefix, color, target_list=colors_flows):
        indices = [i for i, name in enumerate(flow_names_ordered) if name.startswith(prefix)]
        for i in indices:
            if i < len(target_list): target_list[i] = color

    def set_color_exact(name, color, target_list=colors_flows):
         try:
             idx = flow_names_ordered.index(name)
             if idx < len(target_list): target_list[idx] = color
         except ValueError: pass # Flow not found

    # Example assignments (adapt these based on your flow names and groups)
    set_color_exact('F_13_20', "khaki")
    set_color_exact('F_20_15', "khaki")
    set_color_exact('F_20_01', "khaki")
    set_color_exact('F_20_16', "khaki")
    set_color_exact('F_04_01', "mediumseagreen")
    set_color_exact('F_01_05', "mediumpurple") # Biogas to Incin.
    set_color_exact('F_01_02', "sandybrown")   # Biogas to MBC Prod.
    set_color_exact('F_02_03', "sandybrown")   # MBC Prod to Use
    set_color_exact('F_03_07', "sandybrown")   # MBC Use to EoL
    set_color_exact('F_02_06', "mediumseagreen")# MBC Prod waste
    set_color_exact('F_11_02', "khaki")        # Millet to MBC Prod
    set_color_exact('F_08_02', "skyblue")      # Water In to MBC Prod
    set_color_exact('F_02_14', "skyblue")      # Water Out from MBC Prod
    set_color_exact('F_02_12', "mediumseagreen")# MBC Prod delta loss
    set_color_exact('F_07_09', "mediumpurple") # EoL to Pyrolysis
    set_color_exact('F_07_10', "mediumpurple") # EoL to Incin
    set_color_exact('F_09_17', "mediumpurple") # Pyrolysis to Soil
    set_color_exact('F_10_18', "mediumpurple") # Incin to Ash
    set_color_exact('F_10_19', "mediumpurple") # Incin to Atmos
    # Boundary flows (often light gray or omitted)
    set_color_exact('F_00_13', "lightgray")
    set_color_exact('F_00_04', "lightgray")
    set_color_exact('F_00_11', "lightgray")
    set_color_exact('F_00_08', "lightgray")
    set_color_exact('F_09_19', "mediumpurple") # Pyrolysis Gas to Atmos
    set_color_exact('F_17_19', "mediumpurple") # Soil Mineralization to Atmos
    set_color_exact('F_09_14', "skyblue")      # Pyrolysis Water out
    set_color_exact('F_10_14', "skyblue")      # Incin Water out
    set_color_exact('F_01_21', "mediumseagreen")# Biogas delta loss

    # Set process colors (e.g., color main pathway processes)
    # process_ids_ordered = [p.ID for p in Dyn_MFA_System.ProcessList]
    # ... logic to set specific process colors ...

    print("Sankey colors configured (manual mapping).")

except Exception as e:
    print(f"WARNING: Error occurred during manual Sankey color mapping: {e}. Using default colors.")
    colors_flows = ['rgba(150, 150, 150, 0.6)'] * num_flows
    colors_processes = ['rgb(200, 200, 200)'] * num_processes


# %% Generate Interactive Sankey Diagram

# Requires ipywidgets and plotly to be installed and enabled in Jupyter environment
# If running as a plain script, this will likely not display interactively.

# Exclude certain flows if desired (e.g., boundary inputs)
# Use an empty set {} to show all flows.
excluded_flows_sankey = {'F_00_13', 'F_00_04', 'F_00_11', 'F_00_08'}
# Convert to list because the function might expect it
excluded_flows_sankey_list = list(excluded_flows_sankey)

print(f"\nGenerating interactive Sankey diagram (excluding flows: {excluded_flows_sankey})...")
print("Note: Interactive widgets require a Jupyter environment (Notebook/Lab).")

try:
    # Ensure the function gets the correct arguments: system, years list, classifications, colors, exclusions
    sankey_widget = bipl.sankey_results(Dyn_MFA_System,
                                       MyYears,
                                       ModelClassification,
                                       colors_flows,
                                       colors_processes,
                                       excluded_flows_sankey_list) # Pass the list

    # In a Jupyter environment, displaying the widget would render it:
    # display(sankey_widget)
    print("Sankey widget created. Display in Jupyter or save using widget controls.")

except NameError:
     print("WARNING: Function 'bipl.sankey_results' not found. Skipping Sankey diagram.")
except Exception as e:
     print(f"ERROR generating Sankey diagram: {e}")


# %% [markdown]
# ### 4.3 Interactive stock plots

# %% Generate Interactive Stock Plot

print("\nGenerating interactive stock plots...")
print("Note: Interactive widgets require a Jupyter environment (Notebook/Lab).")

try:
    stock_widget = bipl.bar_stocks_results(Dyn_MFA_System,
                                         MyYears,
                                         ModelClassification,
                                         colors_processes) # Using process colors for stocks here

    # In Jupyter: display(stock_widget)
    print("Stock plot widget created. Display in Jupyter or save using widget controls.")

except NameError:
    print("WARNING: Function 'bipl.bar_stocks_results' not found. Skipping interactive stock plot.")
except Exception as e:
    print(f"ERROR generating interactive stock plot: {e}")


# %% [markdown]
# ### 4.4 MBC dynamic stock model results plot

# %% Plot MBC DSM results (Inflow, Outflow, Stock by Category)

# Check if DSM was run and data exists
if 'MBC_DSM_Data' in locals() and isinstance(MBC_DSM_Data, dict):
    print("\nPlotting MBC DSM results by category...")
    plt.rcParams['figure.dpi'] = PLOT_DPI
    fig, axs = plt.subplots(3, 1, figsize=(10, 12), sharex=True)

    time_items = Dyn_MFA_System.IndexTable.loc['Time'].Classification.Items
    category_labels = [f'Cat {i+1} ($\\tau$={tau})' for i, tau in enumerate(MBC_LIFETIMES_TAU)]

    # Plot 1: Split Inflows to Use Phase
    axs[0].stackplot(time_items, MBC_DSM_Data['Inflow_Categories'].T, labels=category_labels, alpha=0.7)
    axs[0].set_title(f'Flow of MBC Products to Use Phase ({DSM_input_flow_name} split)')
    axs[0].set_ylabel(f'Flow ({Dyn_MFA_System.Unit}/yr)')
    axs[0].legend(loc='upper left')
    axs[0].grid(True, linestyle='--', alpha=0.6)

    # Plot 2: Categorized Outflows from Use Phase
    axs[1].stackplot(time_items, MBC_DSM_Data['Outflow_Categories'].T, labels=category_labels, alpha=0.7)
    axs[1].set_title(f'Flow of MBC Products from Use Phase to EoL ({DSM_output_flow_name} by origin category)')
    axs[1].set_ylabel(f'Flow ({Dyn_MFA_System.Unit}/yr)')
    axs[1].legend(loc='upper left')
    axs[1].grid(True, linestyle='--', alpha=0.6)

    # Plot 3: Categorized Stock in Use Phase
    axs[2].stackplot(time_items, MBC_DSM_Data['Stock_Categories'].T, labels=category_labels, alpha=0.7)
    axs[2].set_title(f'Stock of MBC Products in Use Phase (S_{MBC_PROCESS_ID} by origin category)')
    axs[2].set_ylabel(f'Stock ({Dyn_MFA_System.Unit})')
    axs[2].set_xlabel('Year')
    axs[2].legend(loc='upper left')
    axs[2].grid(True, linestyle='--', alpha=0.6)

    plt.tight_layout()
    plt.show()

else:
    print("Skipping MBC DSM plots: DSM data not found (likely due to zero input or skipped calculation).")


# %% [markdown]
# ### 4.5 Excel export

# %% Export results to Excel

output_excel_filename = f"{Dyn_MFA_System.Name}_Results_{START_YEAR}-{END_YEAR}.xlsx"
output_excel_path = BASE_DIR / output_excel_filename
print(f"\nExporting results to Excel file: {output_excel_path}...")

try:
    # Use the bioDYM export function
    bix.export_xlsx(Dyn_MFA_System, MyYears, ModelClassification, filename=output_excel_path)
    print(f"Results successfully exported.")

except NameError:
     print("WARNING: Function 'bix.export_xlsx' not found. Skipping Excel export.")
except Exception as e:
     print(f"ERROR exporting results to Excel: {e}")


# %% End of Script
print("\nScript execution finished.")