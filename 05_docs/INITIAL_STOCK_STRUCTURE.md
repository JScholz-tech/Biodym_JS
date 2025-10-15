# Initial Stock Excel Structure - Long Table Format

## Sheet: 2_4_Initial_Stock

This sheet uses a long table format for consistency with other BioDYM sheets (like 2_3_dynamic_TCs and 3_1_Definition_DSM).

### Required Columns:
- **Process_ID**: Integer ID linking to process definitions
- **Parameter_Name**: Name of the parameter
- **Parameter_Value**: Value of the parameter

### Optional Columns:
- **Unit**: Unit of measurement
- **Destination_Process**: Target process for outflow (integer)
- **Destination_Flow**: Name of the destination flow
- **Notes**: Additional information

### Example Data Structure:

| Process_ID | Parameter_Name | Parameter_Value | Unit | Destination_Process | Destination_Flow | Notes |
|------------|---------------|-----------------|------|-------------------|------------------|-------|
| 1 | Initial_Stock_material | 1000 | Mg | - | - | Base material amount |
| 1 | Initial_Stock_WC[%] | 15 | % | - | - | Water content percentage |
| 1 | Initial_Stock_DM[%] | 85 | % | - | - | Dry matter percentage |
| 1 | Initial_Stock_CC[%] | 45 | % | - | - | Carbon content percentage |
| 1 | Annual_Consumption_Rate | 0.1 | 1/year | 2 | F_01_02_stock | 10% consumption per year |
| 1 | Outflow_Split[%] | 60 | % | 2 | F_01_02_stock | 60% to process 2 |
| 1 | Outflow_Split[%] | 40 | % | 3 | F_01_03_stock | 40% to process 3 |
| 2 | Initial_Stock_material | 500 | Mg | - | - | Base material amount |
| 2 | Initial_Stock_WC[%] | 20 | % | - | - | Water content percentage |
| 2 | Initial_Stock_DM[%] | 80 | % | - | - | Dry matter percentage |
| 2 | Initial_Stock_CC[%] | 50 | % | - | - | Carbon content percentage |
| 2 | Annual_Consumption_Rate | 0.05 | 1/year | 4 | F_02_04_stock | 5% consumption per year |

### Parameter Types:

#### Initial Stock Composition:
- **Initial_Stock_material**: Base material amount (required)
- **Initial_Stock_WC[%]**: Water content percentage (optional, default 0%)
- **Initial_Stock_DM[%]**: Dry matter percentage (optional, default 100%)
- **Initial_Stock_CC[%]**: Carbon content percentage of DM (optional, default 0%)

#### Outflow Configuration:
- **Annual_Consumption_Rate**: Annual consumption rate as fraction (required for outflows)
- **Outflow_Split[%]**: Percentage split to specific destination (optional, for multiple destinations)

### Key Features:

1. **Multiple Destinations**: Each process can have multiple outflow destinations with different split percentages
2. **Flexible Structure**: Easy to add new parameters without changing column structure
3. **Consistent Format**: Matches other BioDYM sheets for maintainability
4. **Validation**: System validates required parameters and warns about missing data

### Migration from Old Format:

If you have the old wide-table format, you can convert it by:
1. Creating one row per parameter per process
2. Using the Parameter_Name column to specify the parameter type
3. Adding Destination_Process and Outflow_Split[%] rows for outflow configurations

### Process Configuration:

Remember that processes must have **Stock_Configuration = "Stock"** in the 2_1_Definition_Processes sheet to enable initial stock functionality.
