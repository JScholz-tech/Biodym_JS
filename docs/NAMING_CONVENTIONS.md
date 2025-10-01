
# BioDYM Naming Conventions

This document defines the standardized, hierarchical naming conventions for all components within the BioDYM MFA modeling framework. Adhering to these conventions is critical for ensuring model consistency, maintainability, and compatibility with the data loader and simulation engines.

## 1. Core Principles

- **Hierarchical:** Names are structured from general to specific (e.g., `Type_Process_Attribute_Index`).
- **Human-Readable:** Names should be understandable on their own (e.g., `P01_Forestry`).
- **Machine-Parsable:** The structure allows for easy parsing by the Python codebase (e.g., using `name.split('_')`).
- **Consistent:** All names for a given component type must follow the same structure.

---

## 2. Process IDs

**Format:** `P<XX>_<ProcessName>`

- `P`: A static prefix for "Process".
- `<XX>`: A two-digit, zero-padded number (e.g., `01`, `02`, `15`). This provides a unique, sortable identifier.
- `<ProcessName>`: A short, descriptive name in PascalCase (e.g., `PrimaryProcessing`, `UsePhase`).

**Examples:**
- `P01_Forestry`
- `P02_PrimaryProcessing`
- `P10_EoL_Sorting`

---

## 3. Flow IDs

**Format:** `F<P_Start_XX>_<P_End_XX>_<FlowName>`

- `F`: A static prefix for "Flow".
- `<P_Start_XX>`: The two-digit number of the starting process.
- `<P_End_XX>`: The two-digit number of the ending process.
- `<FlowName>`: A short, descriptive name in PascalCase (e.g., `WoodHarvest`, `ProcessedWood`).

**Examples:**
- `F01_02_WoodHarvest`
- `F02_03_ProcessedWood`

---

## 4. Parameter IDs

This is a general structure that applies to Transfer Coefficients (TCs), DSM, and FOMP parameters.

**Format:** `<Type>_P<XX>_<ParameterName>_<Index>`

- `<Type>`: The parameter type (`TC`, `DSM`, `FOMP`).
- `P<XX>`: The two-digit number of the process the parameter belongs to.
- `<ParameterName>`: A descriptive name for the parameter (e.g., `Splitter`, `LifetimeMean`, `DecayRateLabile`).
- `<Index>`: A two-digit number to ensure uniqueness if a process has multiple parameters of the same type (e.g., a process with two splitters).

**Examples:**
- **Transfer Coefficient:** `TC_P02_Splitter_01`
- **DSM Parameter:** `DSM_P03_LifetimeMean_01`
- **FOMP Parameter:** `FOMP_P04_DecayRateLabile_01`

---

## 5. Uncertainty Parameter IDs

Uncertainty parameters are directly linked to the model parameters they describe.

**Format:** `UNC_<Parameter_ID>_<Distribution>`

- `UNC`: A static prefix for "Uncertainty".
- `<Parameter_ID>`: The full ID of the parameter to be made uncertain (e.g., `TC_P02_Splitter_01`).
- `<Distribution>`: The statistical distribution to be used (e.g., `Normal`, `Uniform`, `Triangular`).

**Examples:**
- `UNC_TC_P02_Splitter_01_Normal`
- `UNC_DSM_P03_LifetimeMean_01_Triangular`

This structure allows the Monte Carlo engine to automatically identify the target parameter and the distribution to apply without needing a separate mapping table.
