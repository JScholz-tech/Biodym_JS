# BioDYM User Guide

## 1. Introduction

**BioDYM** is a Material Flow Analysis (MFA) tool built on the ODYM framework, specifically designed for bio-based systems. It provides a complete workflow from data input through calculation, visualization, and export.

### Key Features:
- **Dynamic Stock Modeling (DSM)** - Material aging and product lifetime modeling
- **First-Order Mineralization Process (FOMP)** - Organic matter decomposition simulation
- **Monte Carlo Simulation** - Uncertainty quantification and sensitivity analysis
- **Interactive Visualizations** - Sankey diagrams, process dynamics, stock charts
- **Excel-based Configuration** - Comprehensive data input and configuration management



# BioDYM Quick Start Tutorial

This tutorial will walk you through your first BioDYM analysis using a simple biomass flow example. No programming experience required!

## What You'll Learn

- How to prepare data in Excel
- How to run an MFA analysis
- How to interpret the results
- How to export findings

## The Example System

We'll analyze a simple biomass processing system with four components:

```
Environment → Processing → Food
                    ↓
                Biowaste → Environment
```

This represents biomass being harvested, processed into food, with some waste that returns to the environment.

## Step 1: Set Up with uv

Use uv to manage the environment and dependencies from `pyproject.toml` and `uv.lock`.

```bash
# Navigate to your project folder
cd path/to/Biodym_JS

# Install and lock dependencies into .venv (creates it if missing)
uv sync

# (Optional) ensure Python 3.13 is available
# uv python install cpython-3.13
```

## Step 2: Prepare Your Data

### Understanding the Excel Template

BioDYM uses Excel files to define your system. Let's look at the structure:

1. **Navigate to the example**:
   ```
   basic_examples/basic_example_1/input_data.xlsx
   ```

2. **Open the file** in Excel. You'll see two sheets:
   - `biomass` - Total mass data
   - `carbon` - Carbon content data

### Data Structure

Each sheet contains:
- **Year**: Time points for your analysis
- **F_0_1**: Input flow from environment (how much enters the system)
- **TC_1_2**: Transfer coefficient to food (what fraction goes to food)
- **TC_1_3**: Transfer coefficient to biowaste (what fraction becomes waste)
- **TC_3_0**: Transfer coefficient from biowaste to environment

Example data:
| Year | F_0_1 | TC_1_2 | TC_1_3 | TC_3_0 |
|------|-------|--------|--------|--------|
| 2025 | 100   | 0.7    | 0.3    | 0.5    |
| 2026 | 110   | 0.7    | 0.3    | 0.5    |

This means:
- 100 units enter in 2025
- 70% goes to food (100 × 0.7 = 70)
- 30% goes to biowaste (100 × 0.3 = 30)
- 50% of biowaste returns to environment (30 × 0.5 = 15)

## Step 3: Run the Analysis

### Using the Command Line (Easiest)

1. **Copy the example to create your own**:
   ```bash
   cp basic_examples/basic_example_1/input_data.xlsx my_first_analysis.xlsx
   ```

2. **Run BioDYM**:
   ```bash
   uv run python biodym_mfa_tool/src/main_cli.py --input my_first_analysis.xlsx
   ```

3. **Wait for completion**. You'll see:
   - Progress messages
   - Mass balance validation ✓
   - "Analysis complete!"

### Using Jupyter (More Interactive)

1. **Start Jupyter**:
    ```bash
   uv run jupyter lab
    ```

2. **Open**: `biodym_mfa_tool/BioDYM_Scientific_Notebook.ipynb`  
   (paired source: `biodym_mfa_tool/BioDYM_Scientific_Notebook.py`)

3. **Copy the code sections** into notebook cells

4. **Run cells in order** (Shift+Enter)

## Step 4: Understand the Results

### Mass Balance Check (Critical!)

The first result you'll see is the mass balance validation:

```
Mass Balance Check:
Process 0 (Environment): 0.00 ✓
Process 1 (Processing): 0.00 ✓
Process 2 (Food): 0.00 ✓
Process 3 (Biowaste): 0.00 ✓
```

✓ means the process is balanced (good!)
✗ would mean there's an error to fix

### Interactive Visualizations

1. **Sankey Diagram**: Shows material flows through the system
   - Width of arrows = amount of material
   - Use dropdown to switch between Biomass/Carbon
   - Use slider to see different years

2. **Stock Plots**: Shows accumulation in different processes
   - Bar height = total stock
   - Colors match process types

3. **Flow Analysis**: Detailed view of specific flows
   - Select flows from dropdown
   - Toggle between line/bar charts

## Step 5: Export Your Results

Results are automatically saved to:
```
data/02_output/results.xlsx
```

This file contains:
- **Flows sheet**: All calculated flows over time
- **Stocks sheet**: Stock levels in each process
- **Parameters sheet**: Your input data
- **Summary sheet**: Key metrics

## Common Modifications

### Change Time Period

Edit years in your Excel file:
```
2025 → 2030
2026 → 2031
...
```

### Add More Years

Simply add rows to your Excel sheets with new years and values.

### Adjust Transfer Coefficients

Change the TC values to model different scenarios:
- Higher TC_1_2 = more efficient food production
- Lower TC_3_0 = better waste retention

### Run Monte Carlo Uncertainty

Add the `--monte-carlo` flag:
```bash
uv run python biodym_mfa_tool/src/main_cli.py --input my_first_analysis.xlsx --monte-carlo --iterations 100
```

## Next Steps

1. **Try modifying** the example data to see how results change
2. **Read** the [Essential Knowledge Summary](ESSENTIAL_KNOWLEDGE_SUMMARY.md) for architecture & workflow
3. **Explore** other examples in the `basic_examples` folder
4. **Create** your own system using the template generator

## Getting Help

- **Mass balance checks & plots?** See [Essential Knowledge Summary](ESSENTIAL_KNOWLEDGE_SUMMARY.md)
- **In-depth analysis docs?** See [Analysis Docs Index](toc_analysis/README.md)

## Tips for Success

1. **Always check mass balance first** - it validates your model
2. **Start simple** - modify examples before creating from scratch
3. **Use meaningful names** - helps track your analyses
4. **Save scenarios** - compare different parameter sets
5. **Document assumptions** - use the metadata sheet

---

Congratulations! You've completed your first BioDYM analysis. The same principles apply to more complex systems - just with more processes and flows.## 3. Core Concepts

### Architecture Overview

**Main Components:**
1. **Scientific Notebook** (`BioDYM_Scientific_Notebook.py`) - Main user interface and workflow orchestrator
2. **Core Engine** (`src/engine/`) - MFA calculation engine with solver, DSM, FOMP, and Monte Carlo
3. **Data Management** (`src/data_loader.py`, `src/system_setup.py`) - Excel data loading and system initialization
4. **Visualization** (`src/plotting/`) - Comprehensive plotting and analysis tools
5. **Utilities** (`src/utils.py`) - Export, parameter sampling, and helper functions

### Workflow Structure (4 Steps)

**Step 1: Setup & Data Loading**
- **Purpose**: Environment preparation and data validation
- **Key Activities**: Import modules, set paths, load Excel file, validate sheets

**Step 2: Calculation & Validation**
- **Purpose**: MFA calculation execution and mass balance verification
- **Key Activities**: Model initialization, MFA calculation, mass balance validation

**Step 3: Visualization**
- **Purpose**: Comprehensive analysis and exploration
- **Key Activities**: System overview, process analysis, component analysis

**Step 4: Export**
- **Purpose**: Results export and Monte Carlo analysis
- **Key Activities**: Results export, configuration export, MC simulation

### Excel Data Structure

**Core Data Sheets (Required):**
- `1_1_Definition_Flows` - Flow definitions and connections
- `1_2_Data_Flows` - Flow data over time
- `2_1_Definition_Processes` - Process definitions
- `2_3_Process_TCs` - Transfer coefficients
- `2_4_Initial_Stock` - Initial stock values
- `2_5_dynamic_tcs` - Dynamic transfer coefficients

**Parameter Sheets (Optional):**
- `3_1_Definition_DSM` - Dynamic Stock Model parameters
- `3_2_Definition_FOMP` - First-Order Mineralization Process parameters
- `4_1_Uncertainty_Parameters` - Monte Carlo uncertainty definitions

**Configuration Sheet:**
- `0_Configuration` - Settings for model configuration


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

## 4. Initial Stock Feature

The initial stock system has been designed to seamlessly integrate with BioDYM's existing splitter and transformation logic.

### Process Type Compatibility

- **Compatible**: `Splitter`, `Transformer`, `DSM`, `FOMP`
- **Incompatible**: `Input`, `Output`, `Pass-through`

### Excel Structure: `2_4_Initial_Stock`

This sheet uses a long table format.

**Required Columns:**
- `Process_ID`: Integer ID linking to process definitions
- `Parameter_Name`: Name of the parameter
- `Parameter_Value`: Value of the parameter

**Optional Columns:**
- `Unit`: Unit of measurement
- `Destination_Process`: Target process for outflow (integer)
- `Destination_Flow`: Name of the destination flow
- `Notes`: Additional information

**Example Data Structure:**

| Process_ID | Parameter_Name | Parameter_Value | Unit | Destination_Process | Destination_Flow | Notes |
|------------|---------------|-----------------|------|-------------------|------------------|-------|
| 1 | Initial_Stock_material | 1000 | Mg | - | - | Base material amount |
| 1 | Initial_Stock_WC[%] | 15 | % | - | - | Water content percentage |
| 1 | Annual_Consumption_Rate | 0.1 | 1/year | 2 | F_01_02_stock | 10% consumption per year |
| 1 | Outflow_Split[%] | 60 | % | 2 | F_01_02_stock | 60% to process 2 |
| 1 | Outflow_Split[%] | 40 | % | 3 | F_01_03_stock | 40% to process 3 |

**Parameter Types:**

- **Initial Stock Composition**:
  - `Initial_Stock_material`: Base material amount (required)
  - `Initial_Stock_WC[%]`: Water content percentage (optional, default 0%)
  - `Initial_Stock_DM[%]`: Dry matter percentage (optional, default 100%)
  - `Initial_Stock_CC[%]`: Carbon content percentage of DM (optional, default 0%)

- **Outflow Configuration**:
  - `Annual_Consumption_Rate`: Annual consumption rate as fraction (required for outflows)
  - `Outflow_Split[%]`: Percentage split to specific destination (optional, for multiple destinations)

### Process Configuration

Processes must have **Stock_Configuration = "Stock"** in the `2_1_Definition_Processes` sheet to enable initial stock functionality.

## 5. Visualization Guide

### Plotting Standards

This document defines the comprehensive styling standards for all BioDYM plots, ensuring consistency, professional appearance, and print-readiness across the entire framework.

#### Color Palettes

**Primary BioDYM Colors**
- **Primary Blue**: `#2E86AB` - Main elements, primary flows
- **Secondary Pink**: `#A23B72` - Secondary elements, transformers
- **Accent Orange**: `#F18F01` - Highlights, important annotations
- **Success Red**: `#C73E1D` - Important flows, critical processes
- **Neutral Gray**: `#6C757D` - Neutral elements, backgrounds
- **Light Gray**: `#F8F9FA` - Plot backgrounds
- **Dark Gray**: `#212529` - Text, borders

**Element-Specific Colors**
- **Material**: `#2E86AB` (Primary blue)
- **Carbon**: `#28A745` (Green)
- **Nitrogen**: `#FFC107` (Yellow)
- **Phosphorus**: `#DC3545` (Red)
- **Water**: `#17A2B8` (Cyan)
- **Energy**: `#FD7E14` (Orange)
- **WC (Water Content)**: `#28A745` (Green)
- **DM (Dry Matter)**: `#6C757D` (Gray)
- **CC (Carbon Content)**: `#FFC107` (Yellow)

**Process Type Colors**
- **Splitter**: `#2E86AB` (Blue)
- **Transformer**: `#A23B72` (Pink)
- **Storage**: `#6C757D` (Gray)
- **Sink**: `#DC3545` (Red)
- **Source**: `#28A745` (Green)

**Status Colors**
- **Success**: `#28A745` (Green)
- **Warning**: `#FFC107` (Yellow)
- **Error**: `#DC3545` (Red)
- **Info**: `#17A2B8` (Cyan)

#### Typography

**Font Family**
- **Primary**: Arial, sans-serif
- **Fallback**: System default sans-serif fonts

**Font Sizes**
- **Title**: 16pt
- **Subtitle**: 14pt
- **Axis Title**: 12pt
- **Axis Labels**: 10pt
- **Legend**: 10pt
- **Annotation**: 9pt
- **Tick Labels**: 9pt

#### Layout Standards

**Figure Sizes (pixels)**
- **Small**: 800×600
- **Medium**: 1000×750
- **Large**: 1200×900
- **Publication**: 1000×800

**Margins**
- **Standard**: 80px top/bottom, 50px left/right
- **Publication**: 100px top/bottom, 50px left/right

#### Grid and Background

**Grid Style**
- **Color**: `#E5E5E5` (Light gray)
- **Width**: 1px
- **Style**: Dotted

**Background Colors**
- **White**: `#FFFFFF` (Default)
- **Light Gray**: `#FAFAFA`

#### Export Settings

- **PNG Standard**: 1200×900px, 2x scale (150 DPI)
- **PNG Publication**: 1200×900px, 3x scale (300 DPI)
- **PDF**: 1200×900px (Vector format)
- **SVG**: 1200×900px (Scalable vector)

### Enhanced Sankey Diagrams for Circular Systems

This guide explains how to use the enhanced Sankey diagram functionality for visualizing circular/recycling material flow systems in BioDYM.

#### Excel Configuration

**Process_Visualization Sheet**

| Column | Description | Example |
|---|---|---|
| Process_ID | Must match your MFA system process IDs | P_01, P_02, etc. |
| Process_Name | Human-readable process name | "Input Process" |
| Node_Color | Hex color code | #FF6B6B |
| X_Position | X coordinate (0.0 to 1.0) | 0.5 |
| Y_Position | Y coordinate (0.0 to 1.0) | 0.5 |
| Layout_Type | Layout algorithm | Auto, Fixed, Circular, Radial |

**Flow_Visualization Sheet**

| Column | Description | Example |
|---|---|---|
| Flow_ID | Must match your MFA system flow IDs | F_01_02, F_02_03, etc. |
| Flow_Color | Hex color code | #FF6B6B |
| Flow_Style | Line style | Solid, Dashed, Dotted |

**Layout_Configuration Sheet**

| Setting | Description | Options |
|---|---|---|
| Default_Layout_Type | Main layout algorithm | Linear, Circular, Radial, Custom |
| Circular_Radius | Radius for circular layout | 0.1 to 0.5 |
| Flow_Curvature | How curved the flows are | 0.0 to 1.0 |

#### Layout Types

- **Circular**: Best for recycling systems - processes with circular flows are arranged in a circle
- **Radial**: All processes arranged in a circle
- **Linear**: Traditional left-to-right layout
- **Custom**: Manual positioning using X_Position and Y_Position
