# BioDYM MFA Tool: Comprehensive Documentation

## Chapter 1: System Setup - Building the Model's Blueprint

### 1.1. Introduction: The Qualitative Model

The initial phase of any Material Flow Analysis (MFA) involves translating a conceptual model into a structured, qualitative format. In the BioDYM MFA tool, this process is about building the "scaffolding" of the model before any quantitative data is introduced. This involves defining the system's boundaries, its components (processes, flows, and stocks), and the dimensions (time and elements) over which the analysis will be conducted.

Crucially, all definitions for this model construction are sourced directly from the Excel input file. While this chapter focuses on *how* the internal ODYM model objects are constructed, the *details* of the Excel file's structure and data loading process will be elaborated in Chapter 2: Data Loading.

### 1.2. Defining the Model Scope (`define_model_scope`)

The first step in setting up the BioDYM MFA model is to define its fundamental scope in terms of time and the elements to be tracked. The `define_model_scope` function (located in `src/system_setup.py`) takes the analysis's `start_year`, `end_year`, and a list of `elements` (e.g., 'material', 'WC', 'DM', 'CC') as input.

This function creates two core ODYM data structures:
*   **`ModelClassification`**: A dictionary containing `msc.Classification` objects for 'Time' and 'Element'. These objects define the discrete items within each dimension (e.g., a list of years for 'Time', or a list of specific elements for 'Element').
*   **`IndexTable`**: A pandas DataFrame that serves as a lookup table for the model's dimensions, providing metadata like the 'IndexLetter' (e.g., 't' for time, 'e' for element) used in ODYM's internal indexing.

This step establishes the fundamental axes along which all subsequent model data will be organized.

*   **Verification Reference:** The correct creation and content of these scope objects are verified by `test_setup.py::test_define_model_scope_structure_and_content`.

### 1.3. Initializing the System Container (`initialize_mfa_system`)

Once the model's scope is defined, the `initialize_mfa_system` function (also in `src/system_setup.py`) creates the central container for the entire MFA model: the `msc.MFAsystem` object. This object is the backbone of the BioDYM tool, holding all processes, flows, stocks, and parameters.

The `MFAsystem` object is initialized with global properties such as the model's `Name`, `Unit` (e.g., 'Mg' for Megagrams), and the defined `Time_Start`, `Time_End`, and `Elements`. Importantly, it sets up empty lists and dictionaries (`ProcessList`, `FlowDict`, `StockDict`, `ParameterDict`) that will be populated in subsequent setup steps.

*   **Verification Reference:** The correct initialization and structure of the `MFAsystem` object are verified by `test_setup.py::test_initialize_mfa_system_creation`.

### 1.4. Defining Processes and Stocks (`load_and_define_processes`)

This function (in `src/system_setup.py`) bridges the gap between the raw Excel input and the structured ODYM model. It reads the `2_1_Definition_Processes` sheet from the Excel input file to define the "boxes" of the MFA system.

For each process defined in the Excel sheet, an `msc.Process` object is created and added to the `MFAsystem`'s `ProcessList`. A critical aspect of this step is the conditional creation of stock objects: if a process is marked with `Stock? == 'Yes'` in the Excel sheet, two corresponding `msc.Stock` objects are created:
*   `S_ProcessID`: Represents the absolute stock within that process.
*   `dS_ProcessID`: Represents the change in stock for that process.

These stock objects are added to the `MFAsystem`'s `StockDict` and are initialized with zero values, ready to accumulate material.

*   **Verification Reference:** The correct definition of processes and the conditional creation of stock objects are verified by `test_setup.py::test_load_and_define_processes`.

### 1.5. Defining Flows and Parameters (`define_flows_and_parameters`)

This comprehensive function (in `src/system_setup.py`) is responsible for establishing the connections between processes (flows) and defining the parameters that govern material transformations and compositions. It uses information primarily from the `1_1_Definition_Flows` sheet of the Excel input.

Key actions performed:
*   **Flow Creation:** `msc.Flow` objects are created for each flow defined in the Excel sheet, establishing the pathways between processes. These flows are initially populated with zero values.
*   **Parameter Definition:** Static parameters, such as elemental content fractions (e.g., 'WC' for Water Content, 'CC' for Carbon Content) and Transfer Coefficients (TCs), are read from the Excel sheets (e.g., `1_1_Definition_Flows`, `2_3_Process_TCs`) and stored as `msc.Parameter` objects in the `MFAsystem`'s `ParameterDict`.
*   **Elemental Composition Calculation:** For primary input flows, this function calculates the elemental composition (e.g., how much water or carbon is in the 'material' flow) based on the defined parameters.

This step completes the qualitative definition of the model, preparing it for the injection of quantitative time-series data.

*   **Verification Reference:** The correct definition of flows, parameters, and the calculation of elemental compositions are verified by `test_setup.py::test_define_flows_and_parameters_logic`.

### 1.6. Handling Dynamic Parameters (`create_dynamic_tc_parameters`)

The BioDYM tool supports dynamic parameters, meaning certain parameters can change over time. The `create_dynamic_tc_parameters` function (in `src/system_setup.py`) handles this by taking sparse time-series data for a Transfer Coefficient (TC) from the `2_5_dynamic_tcs` sheet in the Excel input.

This function interpolates the provided data points across the entire model's time range, creating a complete time series for the dynamic TC. This allows for more realistic modeling of systems where parameters are not constant over the analysis period.

*   **Verification Reference:** The successful interpolation and error handling for dynamic TC parameters are verified by `test_setup.py::test_create_dynamic_tc_parameters_success`, `test_create_dynamic_tc_parameters_duplicate_error`, and `test_create_dynamic_tc_parameters_missing_columns`.
