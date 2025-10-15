# BioDYM Excel Data Protocol - README

## 📋 Project Information
- **Project**: BioDYM (Biomass Dynamic Material Flow Analysis)
- **Version**: 2.0
- **Last Updated**: 2024-12-19
- **Purpose**: Comprehensive MFA model for biomass systems with dynamic stock management
- **Contact**: [Your Name/Institution]

## 📊 File Structure Overview

### Core Definition Sheets
- **1_1_Definition_Flows**: Define all material and element flows in the system
- **1_2_Data_Flows**: Enter actual flow data values
- **2_1_Definition_Processes**: Define all processes and their configurations
- **2_2_static_TCs**: Static transfer coefficients for material flows
- **2_3_dynamic_TCs**: Dynamic transfer coefficients for element flows

### Specialized Configuration Sheets
- **2_4_Initial_Stock**: Initial stock configurations for processes
- **3_1_Definition_DSM**: Dynamic Stock Management parameters
- **3_2_Definition_FOMP**: First-Order Mass Pool parameters
- **4_1_Uncertainty_Parameters**: Uncertainty definitions for Monte Carlo
- **5_1_Scenarios**: Scenario definitions for analysis

### Validation and Documentation
- **7_1_Comments_Validation**: Data validation instructions and guidelines

## 🔧 Data Entry Guidelines

### Required Fields (Must be filled)
- **Process_ID**: Unique identifier for each process
- **Flow_ID**: Unique identifier for each flow
- **Process_Name**: Descriptive name for processes
- **Flow_Name**: Descriptive name for flows
- **Process_Logic**: How process handles flows (Input, Output, Pass-through, Transformation, DSM, FOMP)

### Data Types and Formats
- **IDs**: Auto-generated, format P## for processes, F_##_## for flows
- **Percentages**: Use decimal format (0.3 for 30%)
- **Names**: Use descriptive text with underscores
- **Values**: Use appropriate units (tonnes, years, etc.)

### Validation Rules
- **Dropdown Lists**: Use provided dropdown options
- **Range Checks**: Values must be within specified ranges
- **Consistency Checks**: Related fields must be consistent

## 📝 Sheet-Specific Instructions

### 1_1_Definition_Flows
- Define all material flows (wood, waste, etc.)
- Define element flows (WC, DM, CC)
- Set flow composition percentages
- **Important**: Flow_WC[%], Flow_DM[%], Flow_CC_DM[%] columns are required

### 2_1_Definition_Processes
- Define all processes in the system
- Set Process_Logic for each process
- Configure TC_Configuration and Stock_Configuration
- **Process Logic Types**:
  - **Input**: Process receives material
  - **Output**: Process produces material
  - **Pass-through**: Material passes through unchanged
  - **Transformation**: Material is transformed
  - **DSM**: Dynamic Stock Management process
  - **FOMP**: First-Order Mass Pool process

### 2_2_static_TCs & 2_3_dynamic_TCs
- **Static TCs**: Material flow transfer coefficients
- **Dynamic TCs**: Element flow transfer coefficients
- Use Process_ID to link to processes
- **Splitter vs Transformer**:
  - **Splitter**: Only material TCs needed (keeps composition)
  - **Transformer**: Only element TCs needed (changes composition)

### 3_1_Definition_DSM
- Define Dynamic Stock Management parameters
- Use DSM_Parameter_type and DSM_Value columns
- **Parameter Types**:
  - DSM_Category_Name: Name of stock category
  - DSM_Inflow_Split_[%]: Inflow distribution
  - DSM_Lifetime_Type: Lifetime distribution type
  - DSM_Lifetime_Mean: Average lifetime
  - DSM_Lifetime_StdDev: Lifetime standard deviation
  - DSM_Output_*_Flow_ID: Output flow identifiers
  - DSM_Output_*_Split_[%]: Output distribution

### 3_2_Definition_FOMP
- Define First-Order Mass Pool parameters
- Use FOMP_Parameter_ID and FOMP_Parameter_Value columns
- **Parameter Types**:
  - Inflow_fraction_f: Inflow fraction for pools
  - decay_k1, decay_k2: Decay rate constants
  - output_carbon_id: Carbon output flow ID
  - output_environmental_id: Environmental output flow ID

## ⚠️ Troubleshooting

### Common Issues
- **#VALUE! Errors**: Check data types and formats
- **Missing Data**: Ensure all required fields are filled
- **Validation Errors**: Check dropdown selections and ranges
- **MFA Calculation Fails**: Verify TC values are not all NaN

### Data Quality Checks
- **Process Logic Consistency**: Ensure Process_Logic matches TC configuration
- **Flow ID Consistency**: Check Flow_IDs exist in definition sheets
- **TC Completeness**: Verify TCs are defined for all process-flow combinations
- **Stock Configuration**: Ensure stock processes have proper configuration

### Validation Messages
- **"Invalid Selection"**: Choose from dropdown list
- **"Value Out of Range"**: Check value is within specified limits
- **"Required Field"**: Fill in mandatory information
- **"Inconsistent Data"**: Check related fields for consistency

## 🔧 Technical Information

### Column Naming Conventions
- **Process_ID**: P## (e.g., P01, P02)
- **Flow_ID**: F_##_## (e.g., F_01_02)
- **Parameter Names**: Descriptive with underscores
- **Percentage Columns**: End with [%]
- **ID Columns**: End with _ID

### ID Generation
- **Process IDs**: Auto-generated based on row order
- **Flow IDs**: Auto-generated based on source and target processes
- **Parameter IDs**: Include process prefix (e.g., P04_output_carbon_id)

### Macro Information
- **Validation Macro**: Apply data validation rules
- **Codelist Management**: Manage dropdown lists
- **Data Quality Checks**: Verify data integrity

## 📚 Additional Resources
- **User Manual**: [Link to detailed manual]
- **Training Materials**: [Link to training resources]
- **Support**: [Contact information for support]

---
*This README is updated regularly. Check the version number and last updated date.*
