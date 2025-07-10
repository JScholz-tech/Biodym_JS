# BioDYM MFA Model - Excel Data Template Documentation

This document explains the structure and purpose of the `250625_Template_CS0.xlsx` file, which serves as the central data and configuration hub for the BioDYM Material Flow Analysis (MFA) model.

## General Principles

- **One File, One Scenario:** Each Excel file represents a complete, self-contained scenario. To compare scenarios, create copies of this template and modify their parameters.
- **Sheet-Based Organization:** Data is organized into sheets based on its function (e.g., defining processes, defining flows, providing parameters).
- **Column Naming:** Column names are critical and must match the names specified below, as the Python code uses them directly to load data.

---

## Sheet-by-Sheet Guide

### `0_Metadata` (Recommended)

This sheet serves as the "cover page" for the dataset, making it self-documenting.

| Column          | Description                                                                 | Example                               |
|-----------------|-----------------------------------------------------------------------------|---------------------------------------|
| `Dataset_Name`  | A human-readable name for the scenario.                                     | `Rye Straw Cascading - Baseline`      |
| `Version`       | The version number of this data file (e.g., following SemVer).              | `1.0.0`                               |
| `Date_Modified` | The date this file was last modified.                                       | `2025-06-26`                          |
| `Author`        | The name of the person who created or last modified the data.               | `J. Scholz`                           |
| `Description`   | A brief summary of what this scenario represents.                           | `Baseline scenario with current...`   |
| `Source_Reference`| A citation or link to the primary data source.                              | `Scholz et al. (2025)`                |

### `1_1_Definition_Flows`

This sheet defines the connections (flows) between processes.

| Column         | Description                                                                 | Example                               |
|----------------|-----------------------------------------------------------------------------|---------------------------------------|
| `Flow_ID`      | A unique identifier for the flow, typically `F_<origin>_<destination>`.       | `F_02_03`                             |
| `Name(EN)`     | A human-readable name for the flow.                                         | `Straw to Treatment`                  |
| `Process_ID_O` | The integer ID of the **origin** process (must match an ID in `2_1_Definition_Processes`). | `2`                                   |
| `Process_ID_I` | The integer ID of the **destination** process (must match an ID in `2_1_Definition_Processes`). | `3`                                   |
| `WC`, `DM`, `CC` | **(Optional)** The percentage content of Water, Dry Matter, and Carbon for this flow. Used for primary input flows where composition is known. | `0.15` (for 15%)                      |

### `1_2_Data_Flows`

This sheet provides the time-series data for the primary input flows into the system (i.e., flows originating from the system boundary, process `0`).

| Column      | Description                                                                 | Example                               |
|-------------|-----------------------------------------------------------------------------|---------------------------------------|
| `Flow_ID`   | The ID of the flow this data belongs to. Must match an ID in `1_1_Definition_Flows`. | `F_00_02`                             |
| `Year_Flow` | The year for the data point.                                                | `2025`                                |
| `Flow_Py`   | The numerical value (mass) of the flow for that year, in the model's base unit (e.g., Mg). | `1500.75`                             |

### `2_1_Definition_Processes`

This sheet defines all the nodes (processes) in the MFA system.

| Column           | Description                                                                 | Example                               |
|------------------|-----------------------------------------------------------------------------|---------------------------------------|
| `ID`             | The unique **integer** ID for the process. `0` is reserved for the system boundary. | `3`                                   |
| `Name(EN)`       | A human-readable name for the process.                                      | `MBC Use Phase`                       |
| `Stock?`         | A flag (`Yes`/`No`) indicating if this process has an associated stock.     | `Yes`                                 |
| `Initial_Stock?` | A flag (`Yes`/`No`) indicating if the stock has a non-zero initial value at the start of the simulation. | `Yes`                                 |
| `Process_Type`   | **(Optional)** A category used for smarter plot titles (e.g., `Input`, `Output`). | `Input`                               |

### `2_3_Process_TCs`

This sheet defines static (time-invariant) Transfer Coefficients (TCs).

| Column     | Description                                                                 | Example                               |
|------------|-----------------------------------------------------------------------------|---------------------------------------|
| `TC_ID`    | The unique identifier for the TC, typically `TC_<origin>_<destination>`.      | `TC_03_04`                            |
| `TC_Value` | The numerical value of the TC (from 0 to 1).                                | `0.85`                                |

### `2_4_Process_Stock_`

This sheet provides the initial values for stocks that are flagged with `Initial_Stock? = Yes` in the processes sheet.

| Column                   | Description                                                                 | Example                               |
|--------------------------|-----------------------------------------------------------------------------|---------------------------------------|
| `Process_ID`             | The ID of the process whose stock is being defined.                         | `6`                                   |
| `Initial_Stock_material` | The total material mass of the initial stock.                               | `1000`                                |
| `Initial_Stock_WC[%]`, etc. | The percentage composition of the initial stock for each element.         | `0.1` (for 10%)                       |

### `2_5_dynamic_tcs`

This sheet defines dynamic (time-variant) Transfer Coefficients. The model will linearly interpolate values for years between the given data points.

| Column  | Description                                                                 | Example                               |
|---------|-----------------------------------------------------------------------------|---------------------------------------|
| `TC_ID` | The identifier of the TC.                                                   | `TC_04_00`                            |
| `Year`  | The year for the given data point.                                          | `2030`                                |
| `Value` | The numerical value of the TC at that year.                                 | `0.6`                                 |

### `3_1_Definition_DSM`

This sheet defines the parameters for all **Dynamic Stock Model (DSM)** processes. Each row represents a product category within a stock.

| Column             | Description                                                                 | Example                               |
|--------------------|-----------------------------------------------------------------------------|---------------------------------------|
| `Process_ID`       | The ID of the process where the dynamic stock resides.                      | `6`                                   |
| `Category_ID`      | An integer ID for the sub-category of products within the stock.            | `1`                                   |
| `Inflow_Split_[%]` | The percentage of total inflow allocated to this category. The sum for a given `Process_ID` should be 1.0. | `0.6` (for 60%)                       |
| `Lifetime_Type`    | The type of lifetime distribution (e.g., `Normal`, `Lognormal`).            | `Normal`                              |
| `Lifetime_Mean`    | The mean lifetime (in years) for this category.                             | `30`                                  |
| `Lifetime_StdDev`  | The standard deviation of the lifetime (in years).                          | `1.0`                                 |
| `Category_Name`    | A human-readable name for the category, used in plot legends.               | `Tires`                               |

### `3_2_Definition_FOMP`

This sheet defines the parameters for all **First-Order Model Process (FOMP)** calculations (e.g., decay, mineralization).

| Column           | Description                                                                 | Example                               |
|------------------|-----------------------------------------------------------------------------|---------------------------------------|
| `Process_ID`     | The ID of the process where the decay occurs.                               | `8`                                   |
| `Parameter_Name` | The name of the parameter (e.g., `k1`, `k2`, `f`, `outflow_id`).            | `k1`                                  |
| `Value`          | The value of the parameter. For `outflow_id`, this is the `Flow_ID` of the calculated outflow. | `0.025` or `F_08_00`                  |

### `4_1_Uncertainty_Parameters`

This sheet defines the probability distributions for parameters to be used in the **Monte Carlo simulation**.

| Column           | Description                                                                 | Example                               |
|------------------|-----------------------------------------------------------------------------|---------------------------------------|
| `Parameter_Name` | The exact name of the parameter to make uncertain. This must match the name used internally by the model (e.g., `TC_...`, `fomp_...`, `dsm_...`). | `fomp_8_k1`                           |
| `Distribution`   | The type of probability distribution to use.                                | `normal`                              |
| `Min`, `Max`, `Mean`, `StdDev`, `Mode` | The parameters for the chosen distribution. Only fill in the columns relevant to the selected distribution type. | `0.025` (for Mean)                    |

