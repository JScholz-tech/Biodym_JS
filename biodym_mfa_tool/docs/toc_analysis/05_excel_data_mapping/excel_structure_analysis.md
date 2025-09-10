# Excel File Structure Analysis (example)

Note: This analysis uses an example Excel file name; your active file may differ. The sheet structure and mappings remain applicable.

## 📊 File Overview

**File**: `data/01_input/250813_CS1_simple_V1.xlsx`  
**Total Sheets**: 22  
**Analysis Date**: 2025-08-31  
**Status**: ✅ ANALYZED

## 🗂️ Complete Sheet Inventory

| **Sheet Name** | **Rows** | **Columns** | **Purpose** | **Used by Functions** |
|----------------|----------|-------------|-------------|----------------------|
| `Version_CS2_08.05.` | 0 | 0 | Version info | None (empty) |
| `0_ReadMe` | 73 | 20 | Documentation | Manual reading only |
| `Table of Content` | 26 | 2 | Navigation | Manual reading only |
| `0_Configuration` | 30 | 3 | System configuration | `config.load_config_from_excel()` |
| `1_1_Definition_Flows` | 78 | 22 | Flow definitions | `data_loader.load_flow_definitions()` |
| `1_2_Data_Flows` | 349 | 37 | Flow data values | `pd.read_excel()`, time extraction |
| `2_1_Definition_Processes` | 53 | 38 | Process definitions | `data_loader.load_process_definitions()` |
| `2_3_Process_TCs` | 57 | 29 | Process transfer coefficients | `data_loader.load_transfer_coefficients()` |
| `2_4_Initial_Stock` | 62 | 21 | Initial stock values | `data_loader.load_initial_stocks()` |
| `2_5_dynamic_tcs` | 148 | 64 | Dynamic transfer coefficients | `system_setup.create_dynamic_tc_parameters()` |
| `3_1_Definition_DSM` | 50 | 18 | DSM parameters | `data_loader.load_dsm_parameters()` |
| `3_2_Definition_FOMP` | 42 | 17 | FOMP parameters | `data_loader.load_fomp_parameters()` |
| `4_1_Uncertainty_Parameters` | 20 | 10 | Monte Carlo parameters | `data_loader.load_uncertainty_definitions()` |
| `5_1_Scenario_Manager` | 12 | 7 | Scenario configuration | Future scenario manager |
| `3. TC_Data` | 0 | 0 | Transfer coefficient data | None (empty) |
| `PX - Template` | 71 | 23 | PowerBI template | Manual export |
| `4. Calculation_factors>>>>` | 0 | 0 | Calculation factors | None (empty) |
| `Sheet2` | 15 | 5 | Temporary data | None (temporary) |
| `4. Codelists>>>>` | 0 | 1 | Code lists | None (empty) |
| `4_1 Codelists` | 93 | 23 | Code lists | `data_loader.load_codelists()` |
| `5. Wastefiles >>>>` | 0 | 1 | Waste files | None (empty) |

## 🔍 Function-to-Excel Mapping

### **Step 1: Setup and Data Loading**

#### **Required Sheets (Validation)**
```python
required_sheets = [
    '1_1_Definition_Flows',      # ✅ Used by: Sheet validation
    '1_2_Data_Flows',            # ✅ Used by: Time extraction, flow data
    '2_1_Definition_Processes',  # ✅ Used by: Process validation
    '2_4_Initial_Stock',         # ✅ Used by: Stock validation
    '2_5_dynamic_tcs'            # ✅ Used by: Dynamic TC validation
]
```

#### **Feature Detection Sheets**
```python
# Monte Carlo
has_mc = '4_1_Uncertainty_Parameters' in input_data.keys()

# DSM
has_dsm = '3_1_Definition_DSM' in input_data.keys()

# FOMP
has_fomp = '3_2_Definition_FOMP' in input_data.keys()
```

### **Step 2: Calculation & Validation (To be analyzed)**

#### **Data Loading Functions**
- `data_loader.load_dsm_parameters(all_excel_data)` → Sheet: `3_1_Definition_DSM`
- `data_loader.load_fomp_parameters(all_excel_data)` → Sheet: `3_2_Definition_FOMP`
- `data_loader.load_uncertainty_definitions(all_excel_data)` → Sheet: `4_1_Uncertainty_Parameters`

#### **System Setup Functions**
- `system_setup.load_and_define_processes()` → Sheets: `2_1_Definition_Processes`, `2_4_Initial_Stock`
- `system_setup.define_flows_and_parameters()` → Sheets: `1_1_Definition_Flows`, `2_3_Process_TCs`
- `system_setup.create_dynamic_tc_parameters()` → Sheet: `2_5_dynamic_tcs`

## 📋 Key Column Analysis

### **Time Range Extraction**
- **Sheet**: `1_2_Data_Flows`
- **Column**: `Year_Flow`
- **Usage**: Extract unique years for time range
- **Function**: `flow_data['Year_Flow'].unique()`

### **Configuration Loading**
- **Sheet**: `0_Configuration`
- **Format**: Key-Value pairs
- **Usage**: System configuration parameters
- **Function**: `config.load_config_from_excel()`

## 🚨 Unused/Empty Sheets

### **Completely Empty Sheets**
- `Version_CS2_08.05.` (0 rows, 0 columns)
- `3. TC_Data` (0 rows, 0 columns)
- `4. Calculation_factors>>>>` (0 rows, 0 columns)
- `4. Codelists>>>>` (0 rows, 1 column)
- `5. Wastefiles >>>>` (0 rows, 1 column)

### **Potentially Unused Sheets**
- `PX - Template` - PowerBI export template
- `Sheet2` - Temporary data sheet
- `4_1 Codelists` - Code lists (may be used by data_loader)

## 🎯 Recommendations

### **Immediate Actions**
1. **Remove empty sheets** to clean up the Excel file
2. **Validate sheet naming** consistency
3. **Document required vs. optional sheets**

### **Future Enhancements**
1. **Scenario Manager** - Sheet `5_1_Scenario_Manager` is ready for implementation
2. **Code Lists** - Sheet `4_1 Codelists` may need integration
3. **PowerBI Template** - Consider if `PX - Template` is needed

## 📊 Data Flow Summary

```
Excel File → pd.read_excel() → input_data dictionary
    ↓
Sheet validation → Required sheets check
    ↓
Feature detection → Monte Carlo, DSM, FOMP availability
    ↓
Data extraction → Time range, elements, parameters
    ↓
Function calls → Specific data_loader functions for each sheet type
```

---

*Analysis Completed: 2025-08-31*  
*Excel File: 250813_CS1_simple_V1.xlsx*  
*Total Sheets: 22*  
*Used Sheets: 12*  
*Empty Sheets: 5*
