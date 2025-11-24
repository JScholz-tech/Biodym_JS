"""
Generate validation data for BioDYM template columns.
Focuses on INPUT columns only - user-editable fields.
"""

import pandas as pd

# Store all validation entries
validation_data = []

def add_entry(sheet, column, category, required, description):
    """Add a validation entry."""
    validation_data.append({
        'Sheet_Name': sheet,
        'Column_Name': column,
        'Category': category,
        'Required': required,
        'Description': description
    })

# ============================================================================
# 0_CONFIGURATION
# ============================================================================

add_entry('0_Configuration', 'Value', 'Input', 'Yes',
'''Configuration parameter value

PURPOSE: Sets the actual value for each configuration setting

ACTION: Enter appropriate value based on Setting_Name:
- Years: Numeric (e.g., 2020)
- Elements: Comma-separated list (e.g., material, WC, DM, CC)
- Flags: Yes/No

EXAMPLE: For Start_Year → 2000''')

# ============================================================================
# 1_1_DEFINITION_FLOWS
# ============================================================================

add_entry('1_1_Definition_Flows', 'Flow_ID', 'Identifier', 'Yes',
'''Unique flow identifier

PURPOSE: System identifier for this flow

ACTION: Enter unique ID using convention F_##_Description
Use sequential numbering (F_01, F_02, etc.)

EXAMPLE: F_01_Timber_Harvest''')

add_entry('1_1_Definition_Flows', 'Flow_Name', 'Input', 'Yes',
'''Descriptive flow name

PURPOSE: Human-readable name displayed in visualizations

ACTION: Enter clear, concise name describing the material flow

EXAMPLE: Timber from Forest to Sawmill''')

add_entry('1_1_Definition_Flows', 'Comment', 'Input', 'No',
'''Additional notes or clarifications

PURPOSE: Free-text field for documentation

ACTION: Optional notes about data quality, assumptions, or special conditions''')

add_entry('1_1_Definition_Flows', 'Flow_Output_Process', 'Input', 'Yes',
'''Source process name

PURPOSE: Defines where this flow originates

ACTION: Select from process names defined in 2_1_Definition_Processes
Must match exactly.

EXAMPLE: Forest (for timber harvest flow)''')

add_entry('1_1_Definition_Flows', 'Flow_Input_Process', 'Input', 'Yes',
'''Destination process name

PURPOSE: Defines where this flow goes

ACTION: Select from process names defined in 2_1_Definition_Processes
Must match exactly.

EXAMPLE: Sawmill (for timber processing)''')

add_entry('1_1_Definition_Flows', 'Flow_E#_Fraction[%]', 'Input', 'Conditional',
'''Element composition fraction (E1-E6)

PURPOSE: Defines elemental composition of flow

ACTION: Enter percentage (0-100) representing fraction of this element

EXAMPLE: For E2 (Water Content) → 20 means 20% water content

NOTE: Fractions used to calculate absolute values based on hierarchy
defined in Configuration sheet.

REQUIRED: When element is active in system configuration''')

add_entry('1_1_Definition_Flows', 'E#_Ref', 'Reference', 'No',
'''Reference for element data (E1-E6)

PURPOSE: Document data source for element composition

ACTION: Enter Reference_ID from 6_1_Reference_Manager sheet

EXAMPLE: R003 (links to journal article or dataset)''')

# ============================================================================
# 1_2_DATA_FLOWS
# ============================================================================

add_entry('1_2_Data_Flows', 'Flow_ID', 'Identifier', 'Yes',
'''Flow identifier

PURPOSE: Links data to flow definition

ACTION: Select from Flow_IDs defined in 1_1_Definition_Flows
Must match exactly.

EXAMPLE: F_01_Timber_Harvest''')

add_entry('1_2_Data_Flows', 'Flow_Data_Year', 'Input', 'Yes',
'''Data year

PURPOSE: Temporal dimension for flow data

ACTION: Enter year as 4-digit number (e.g., 2020)
Must be within Start_Year to End_Year range defined in configuration.

EXAMPLE: 2020''')

add_entry('1_2_Data_Flows', 'Flow', 'Input', 'Yes',
'''Flow quantity (total material)

PURPOSE: Primary flow value representing total material quantity

ACTION: Enter numeric value for total flow in this year

EXAMPLE: 15000 (representing 15,000 tons)

NOTE: This is typically E1 (material) value. Element-specific values
calculated based on fractions defined in flow definition.''')

add_entry('1_2_Data_Flows', 'UoM_Source', 'Input', 'Yes',
'''Unit of measurement

PURPOSE: Specifies unit for flow value

ACTION: Select from unit codelist (mg, g, Kg, Mg, Gg)
Typically: Mg (megagram = metric ton)

EXAMPLE: Mg''')

add_entry('1_2_Data_Flows', 'Flow_Ref', 'Reference', 'No',
'''Flow data reference

PURPOSE: Document data source

ACTION: Enter Reference_ID from 6_1_Reference_Manager

EXAMPLE: R005 (links to statistical database)

NOTE: Use this to cite where flow data originated''')

add_entry('1_2_Data_Flows', 'CF_required?', 'Config', 'No',
'''Conversion factor required flag

PURPOSE: Indicates if calculation adjustment needed

ACTION: Select Yes if Flow value needs adjustment
Select No if value used directly

EXAMPLE: Yes (if only partial flow relevant or unit conversion needed)''')

add_entry('1_2_Data_Flows', 'CF', 'Input', 'Conditional',
'''Conversion/calculation factor value

PURPOSE: Factor to adjust flow value

ACTION: Enter factor as decimal number

EXAMPLE:
- Partial flow: 0.8 (only 80% of flow is relevant)
- Unit conversion: 0.5 (converts between units)

REQUIRED: When CF_required? = Yes''')

add_entry('1_2_Data_Flows', 'Name_CF', 'Input', 'Conditional',
'''Conversion factor description

PURPOSE: Explains what conversion factor represents

ACTION: Enter brief description

EXAMPLE: Partial flow factor or Density conversion

REQUIRED: When CF_required? = Yes''')

add_entry('1_2_Data_Flows', 'CF_Ref', 'Reference', 'No',
'''Conversion factor reference

PURPOSE: Document source for conversion factor

ACTION: Enter Reference_ID for conversion factor source

EXAMPLE: R012 (links to conversion standard)''')

add_entry('1_2_Data_Flows', 'E#_Fraction[%]', 'Input', 'Conditional',
'''Element fraction (E1-E6)

PURPOSE: Percentage composition of each element in flow

ACTION: Enter percentage (0-100)
Sum of E1 should equal 100%
Other elements relative to their parent in hierarchy

EXAMPLE: E2 (WC) = 20 means 20% water content

NOTE: Overrides fractions from flow definition if entered here.

REQUIRED: When element active and flow-specific composition needed''')

# ============================================================================
# 2_1_DEFINITION_PROCESSES
# ============================================================================

add_entry('2_1_Definition_Processes', 'Process_ID', 'Identifier', 'Yes',
'''Unique process identifier

PURPOSE: System identifier for this process

ACTION: Enter unique ID using sequential numbering (1, 2, 3, ...)

EXAMPLE: 1 (for first process)

NOTE: Referenced by flows, TCs, stocks, DSM, FOMP''')

add_entry('2_1_Definition_Processes', 'Process_Name', 'Input', 'Yes',
'''Descriptive process name

PURPOSE: Human-readable name for process

ACTION: Enter clear, concise name

EXAMPLE: Sawmill or Recycling_Facility

NOTE: Used in visualizations and reports''')

add_entry('2_1_Definition_Processes', 'Description', 'Input', 'No',
'''Process description

PURPOSE: Detailed explanation of process function

ACTION: Enter free-text description of what this process does

EXAMPLE: Sorts end-of-life wood products for recycling or disposal''')

add_entry('2_1_Definition_Processes', 'Process_Logic', 'Config', 'Yes',
'''Process behavior type

PURPOSE: Defines how process handles material flows

ACTION: Select from dropdown (see codelist for option descriptions):
Input, Output, Splitter, Transformer, DSM, FOMP, Pass-through

EXAMPLE: Splitter (for sorting facility)

NOTE: Process_Logic determines which parameters required in other sheets''')

add_entry('2_1_Definition_Processes', 'TC_Configuration', 'Config', 'Conditional',
'''Transfer coefficient configuration

PURPOSE: Defines how outflow distribution is determined

ACTION: Select from dropdown (see codelist):
Static, Dynamic, No TC

EXAMPLE: Static (for fixed distribution rates)

REQUIRED: For Splitter and Transformer processes''')

add_entry('2_1_Definition_Processes', 'Stock_Configuration', 'Config', 'Yes',
'''Stock configuration

PURPOSE: Defines if and how process stores material

ACTION: Select from dropdown (see codelist):
Stock, No Stock, Initial Stock

EXAMPLE: Stock (for use-phase accumulation)''')

# ============================================================================
# 2_2_STATIC_TCs
# ============================================================================

add_entry('2_2_static_TCs', 'Output_Flow', 'Input', 'Yes',
'''Output flow name

PURPOSE: Identifies which output flow this TC applies to

ACTION: Select from Flow_Names where this process is the output process

EXAMPLE: F_05_Recycled_Material

NOTE: Each output flow needs its own TC row''')

add_entry('2_2_static_TCs', 'E#_TC_ID', 'Identifier', 'Conditional',
'''Transfer coefficient identifier (E1-E6)

PURPOSE: Unique name for this TC parameter

ACTION: Enter descriptive ID using convention TC_Description

EXAMPLE: TC_Recycling_Rate

REQUIRED: E1 always for Splitter/Transformer; E2-E6 only for Transformer''')

add_entry('2_2_static_TCs', 'E#_TC_Value[%]', 'Input', 'Conditional',
'''Transfer coefficient value (E1-E6)

PURPOSE: Fraction of inflow directed to this output (0-100%)

ACTION: Enter percentage value
Sum of all E1_TC_Values for one process must equal 100%

EXAMPLE: 75 (means 75% of inflow goes to this output)

REQUIRED: E1 always for processes with TCs; E2-E6 only if Transformer''')

add_entry('2_2_static_TCs', 'Static_TC_Ref', 'Reference', 'No',
'''Transfer coefficient reference

PURPOSE: Document source for TC value

ACTION: Enter Reference_ID from 6_1_Reference_Manager

EXAMPLE: R008''')

add_entry('2_2_static_TCs', 'Comment', 'Input', 'No',
'''Additional notes

PURPOSE: Free-text documentation

ACTION: Optional notes about assumptions or special conditions''')

# ============================================================================
# 2_3_DYNAMIC_TCs
# ============================================================================

add_entry('2_3_dynamic_TCs', 'Output_Flow', 'Input', 'Yes',
'''Output flow name

PURPOSE: Identifies which output flow this TC applies to

ACTION: Select from Flow_Names

EXAMPLE: F_05_Recycled_Material''')

add_entry('2_3_dynamic_TCs', 'TC_Data_Year', 'Input', 'Yes',
'''Data year for TC value

PURPOSE: Temporal dimension for time-varying TC

ACTION: Enter year as 4-digit number
Provide TC values at key years - system interpolates between points.

EXAMPLE: 2020, 2025, 2030 (three points for interpolation)''')

add_entry('2_3_dynamic_TCs', 'E#_TC_ID', 'Identifier', 'Conditional',
'''Transfer coefficient identifier (E1-E6)

PURPOSE: Unique name for this dynamic TC parameter

ACTION: Enter descriptive ID - must be consistent across all years

EXAMPLE: TC_Recycling_Rate_Dynamic

REQUIRED: E1 always; E2-E6 for Transformer''')

add_entry('2_3_dynamic_TCs', 'E#_TC_Value[%]', 'Input', 'Conditional',
'''Transfer coefficient value at this year (E1-E6)

PURPOSE: Time-specific TC value for interpolation

ACTION: Enter percentage value for this year
System interpolates linearly between data points.

EXAMPLE: Year 2020: 60%, Year 2030: 80% → 2025 interpolates to 70%

NOTE: For each year, sum of all E1_TC_Values must equal 100%

REQUIRED: E1 always; E2-E6 for Transformer''')

add_entry('2_3_dynamic_TCs', 'Dyn_TC_Ref', 'Reference', 'No',
'''Dynamic TC reference

PURPOSE: Document source for time-varying TC data

ACTION: Enter Reference_ID from 6_1_Reference_Manager

EXAMPLE: R015''')

# ============================================================================
# 2_4_INITIAL_STOCK
# ============================================================================

add_entry('2_4_Initial_Stock', 'Destination_Process', 'Input', 'Conditional',
'''Destination process for stock outflow

PURPOSE: Where initial stock flows when it depletes

ACTION: Select process name if stock depletes over time
Leave blank if stock permanent.

EXAMPLE: Landfill

REQUIRED: Only if stock has outflow''')

add_entry('2_4_Initial_Stock', 'Destination_Flow', 'Input', 'Conditional',
'''Destination flow for stock outflow

PURPOSE: Specific flow for stock depletion

ACTION: Select flow name connecting this process to destination

EXAMPLE: F_15_Landfill_Emissions

REQUIRED: Only if Destination_Process specified''')

add_entry('2_4_Initial_Stock', 'Annual_Consumption_Rate', 'Input', 'Conditional',
'''Annual depletion rate

PURPOSE: Fraction of stock that flows out annually (0-1)

ACTION: Enter decimal value for yearly depletion
0.1 = 10% leaves each year (first-order decay)

EXAMPLE: 0.05 (5% annual depletion)

REQUIRED: Only if stock depletes
Set to 0 for permanent storage''')

add_entry('2_4_Initial_Stock', 'E#_Stock', 'Input', 'Yes',
'''Initial stock quantity for element (E1-E6)

PURPOSE: Starting stock level at year 0

ACTION: Enter numeric value in system units (typically Mg)

EXAMPLE: 50000 (50,000 tons)

REQUIRED: For all active elements''')

add_entry('2_4_Initial_Stock', 'IS_Ref', 'Reference', 'No',
'''Initial stock reference

PURPOSE: Document source for initial stock estimate

ACTION: Enter Reference_ID from 6_1_Reference_Manager

EXAMPLE: R020''')

# ============================================================================
# 3_1_DEFINITION_DSM
# ============================================================================

add_entry('3_1_Definition_DSM', 'DSM_Parameter_type', 'Input', 'Yes',
'''DSM parameter name

PURPOSE: Identifies which DSM parameter this row defines

ACTION: Use standardized naming (see codelist for full list):
- DSM_Inflow_Split_Cat_#
- DSM_Lifetime_Type_Cat_#
- DSM_Lifetime_Mean_Cat_#
- DSM_Lifetime_StdDev_Cat_#
- DSM_Category_Name_Cat_#
- DSM_Output_#_Split_Cat_#
- DSM_Output_#_Flow_ID_Cat_#

EXAMPLE: DSM_Lifetime_Mean_Cat_1

NOTE: Categories numbered sequentially (Cat_1, Cat_2, ...)''')

add_entry('3_1_Definition_DSM', 'DSM_Value', 'Input', 'Yes',
'''DSM parameter value

PURPOSE: Value for the specified DSM parameter

ACTION: Enter value based on parameter type (see codelist for details):
- Inflow_Split: Fraction 0-1
- Lifetime_Type: Normal, Fixed, or Weibull
- Lifetime_Mean: Years (e.g., 30)
- Lifetime_StdDev: Years (e.g., 5)
- Category_Name: Text
- Output_Split: Fraction 0-1
- Flow_ID: Flow identifier

EXAMPLE: 30 (for 30-year average lifetime)

NOTE: StdDev >80% of Mean triggers warning''')

add_entry('3_1_Definition_DSM', 'DSM_Ref', 'Reference', 'No',
'''DSM parameter reference

PURPOSE: Document source for DSM parameters

ACTION: Enter Reference_ID from 6_1_Reference_Manager

EXAMPLE: R025''')

# ============================================================================
# 3_2_DEFINITION_FOMP
# ============================================================================

add_entry('3_2_Definition_FOMP', 'FOMP_Parameter_ID', 'Input', 'Yes',
'''FOMP parameter identifier

PURPOSE: Identifies which FOMP parameter this row defines

ACTION: Use naming convention P{ProcessID}_{ParameterName}_{Pool}
See codelist for standard parameters.

EXAMPLE: P04_Inflow_fraction_f_Labile

NOTE: Each FOMP typically has 2 pools (Labile and Recalcitrant)''')

add_entry('3_2_Definition_FOMP', 'FOMP_Parameter_Value', 'Input', 'Yes',
'''FOMP parameter value

PURPOSE: Value for the specified FOMP parameter

ACTION: Enter value based on parameter type (see codelist):
- Inflow_fraction: 0-1
- Half_life: Years
- Pool_name: Text

EXAMPLE: 0.7 (70% to labile pool)

NOTE: Half-life determines decay rate: k = ln(2)/t_half''')

add_entry('3_2_Definition_FOMP', 'FOMP_Ref', 'Reference', 'No',
'''FOMP parameter reference

PURPOSE: Document source for decay parameters

ACTION: Enter Reference_ID from 6_1_Reference_Manager

EXAMPLE: R030''')

# ============================================================================
# 4_1_UNCERTAINTY_PARAMETERS
# ============================================================================

add_entry('4_1_Uncertainty_Parameters', 'Parameter_Name', 'Input', 'Yes',
'''Parameter name for uncertainty analysis

PURPOSE: Identifies which parameter to vary in Monte Carlo

ACTION: Enter parameter name exactly as defined elsewhere:
TC_ID, Flow_ID, or DSM/FOMP parameter name

EXAMPLE: TC_Recycling_Rate''')

add_entry('4_1_Uncertainty_Parameters', 'Distribution_Type', 'Config', 'Yes',
'''Probability distribution type

PURPOSE: Defines how parameter varies

ACTION: Select from dropdown (see codelist for descriptions):
Uniform, Normal, Triangular

EXAMPLE: Normal

NOTE: Determines which distribution parameters required''')

add_entry('4_1_Uncertainty_Parameters', 'Min', 'Input', 'Conditional',
'''Minimum value

PURPOSE: Lower bound for parameter

ACTION: Enter minimum plausible value

EXAMPLE: 0.5

REQUIRED: For Uniform and Triangular''')

add_entry('4_1_Uncertainty_Parameters', 'Mode', 'Input', 'Conditional',
'''Most likely value

PURPOSE: Peak of triangular distribution

ACTION: Enter most probable value (between Min and Max)

EXAMPLE: 0.75

REQUIRED: For Triangular only''')

add_entry('4_1_Uncertainty_Parameters', 'Max', 'Input', 'Conditional',
'''Maximum value

PURPOSE: Upper bound for parameter

ACTION: Enter maximum plausible value

EXAMPLE: 0.9

REQUIRED: For Uniform and Triangular''')

add_entry('4_1_Uncertainty_Parameters', 'Mean', 'Input', 'Conditional',
'''Mean value

PURPOSE: Center of normal distribution

ACTION: Enter average/expected value

EXAMPLE: 0.75

REQUIRED: For Normal''')

add_entry('4_1_Uncertainty_Parameters', 'StdDev', 'Input', 'Conditional',
'''Standard deviation

PURPOSE: Spread of normal distribution

ACTION: Enter standard deviation

EXAMPLE: 0.05

REQUIRED: For Normal

NOTE: ~68% within ±1 StdDev, ~95% within ±2 StdDev''')

add_entry('4_1_Uncertainty_Parameters', 'MC_Ref', 'Reference', 'No',
'''Uncertainty parameter reference

PURPOSE: Document source for uncertainty range

ACTION: Enter Reference_ID from 6_1_Reference_Manager

EXAMPLE: R035''')

# ============================================================================
# 5_1_SCENARIO_MANAGER
# ============================================================================

add_entry('5_1_Scenario_Manager', 'Scenario_Name', 'Input', 'Yes',
'''Scenario identifier

PURPOSE: Unique name for this scenario

ACTION: Enter descriptive name
Multiple rows with same name define one scenario.

EXAMPLE: Increased_Recycling_Policy''')

add_entry('5_1_Scenario_Manager', 'Parameter_Type', 'Config', 'Yes',
'''Type of parameter to modify

PURPOSE: Categorizes parameter

ACTION: Select from dropdown (see codelist):
TC, Flow, DSM, FOMP

EXAMPLE: TC''')

add_entry('5_1_Scenario_Manager', 'Parameter_Name', 'Input', 'Yes',
'''Parameter to modify

PURPOSE: Identifies specific parameter

ACTION: Enter exact parameter name from other sheets

EXAMPLE: TC_Recycling_Rate''')

add_entry('5_1_Scenario_Manager', 'Modification_Type', 'Config', 'Yes',
'''How to modify parameter

PURPOSE: Defines modification method

ACTION: Select from dropdown (see codelist):
set_value, multiply, add

EXAMPLE: multiply''')

add_entry('5_1_Scenario_Manager', 'Modification_Value', 'Input', 'Yes',
'''Modification amount

PURPOSE: New value or adjustment factor

ACTION: Enter value based on Modification_Type (see codelist for details):
- set_value: New absolute value
- multiply: Multiplier factor
- add: Amount to add

EXAMPLE: 1.2 (multiply by 1.2)''')

add_entry('5_1_Scenario_Manager', 'Comment', 'Input', 'No',
'''Scenario description

PURPOSE: Explain scenario rationale

ACTION: Optional explanation of assumptions or policy drivers''')

# ============================================================================
# 6_1_REFERENCE_MANAGER
# ============================================================================

add_entry('6_1_Reference_Manager', 'Reference_ID', 'Identifier', 'Yes',
'''Unique reference identifier

PURPOSE: ID for citing this source throughout template

ACTION: Enter unique code:
R### for external sources (R001, R002...)
ASM### for assumptions (ASM001, ASM002...)

EXAMPLE: R003

NOTE: Used in all _Ref columns to link data to sources''')

add_entry('6_1_Reference_Manager', 'Type', 'Config', 'Yes',
'''Literature type

PURPOSE: Categorizes source type

ACTION: Select from codelist (see 7_2_Codelists for full descriptions):
JA, RP, DS, BK, TH, ST, WB, PC, AS, GL

EXAMPLE: JA (Journal Article)''')

add_entry('6_1_Reference_Manager', 'Author(s)', 'Input', 'Yes',
'''Author names

PURPOSE: Primary author(s) or institution

ACTION: Enter last name(s) or institution
Multiple authors: Use semicolon separator

EXAMPLE: Smith, J.; Mueller, A.''')

add_entry('6_1_Reference_Manager', 'Year', 'Input', 'Yes',
'''Publication year

PURPOSE: Year source was published

ACTION: Enter 4-digit year

EXAMPLE: 2022''')

add_entry('6_1_Reference_Manager', 'Title', 'Input', 'Yes',
'''Source title

PURPOSE: Full title or brief description

ACTION: Enter complete title or descriptive summary

EXAMPLE: Material Flow Analysis of Timber Products''')

add_entry('6_1_Reference_Manager', 'DOI/URL', 'Input', 'No',
'''Digital identifier or web address

PURPOSE: Direct link to source

ACTION: Enter DOI (preferred) or URL

EXAMPLE: 10.1016/j.resconrec.2022.01234

NOTE: DOIs more permanent than URLs''')

add_entry('6_1_Reference_Manager', 'Notes (How was the source used)?', 'Input', 'No',
'''Usage notes

PURPOSE: Explain how source was used

ACTION: Note specific tables, figures, or data used

EXAMPLE: Table 3 for transfer coefficients; Figure 2 for validation''')

# ============================================================================
# SYSTEM COLUMNS (Brief generic descriptions)
# ============================================================================

add_entry('SYSTEM', 'Complete?', 'System', 'No',
'''Completion flag

PURPOSE: Mark row as verified and complete

ACTION: Check box after all data verified
Used for progress tracking.''')

add_entry('SYSTEM', 'ID', 'System', 'Yes',
'''Auto-generated row identifier

PURPOSE: Unique sequential number for data integrity

ACTION: System-generated. Do not modify.''')

add_entry('SYSTEM', 'ODYM_*', 'System', 'No',
'''ODYM framework field

PURPOSE: Technical field for framework integration

ACTION: Auto-generated. Do not modify.

NOTE: Used for dimensional indexing.''')

# Convert to DataFrame and save
df_validation = pd.DataFrame(validation_data)

# Save to CSV
output_path = '01_data/01_input/template/7_1_Comments_Validation_NEW.csv'
df_validation.to_csv(output_path, index=False, encoding='utf-8-sig')

print(f'[OK] Validation data generated: {len(df_validation)} entries')
print(f'[OK] Saved to: {output_path}')
print(f'\nBreakdown by category:')
print(df_validation['Category'].value_counts())
print(f'\nBreakdown by sheet (top 10):')
print(df_validation['Sheet_Name'].value_counts().head(10))
print('\n[OK] Generation complete!')
