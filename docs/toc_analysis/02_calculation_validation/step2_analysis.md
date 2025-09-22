# Step 2: Calculation & Validation - Complete Analysis

## 📋 Overview

**Location in Notebook**: Lines 200-450  
**Purpose**: Execute MFA calculation and validate results through mass balance checks  
**Status**: ✅ COMPLETED

## 🚀 2.1 Model Initialization (Lines 200-250)

### **1. Setup Model Scope**
```python
model_classification, index_table = system_setup.define_model_scope(
    start_year, end_year, elements
)
```
**Function**: `system_setup.define_model_scope()`  
**Parameters**: `start_year`, `end_year`, `elements`  
**Returns**: Model classification and index table  
**Purpose**: Define temporal and elemental scope of the MFA model

### **2. Initialize MFA System**
```python
mfa_system_base = system_setup.initialize_mfa_system(
    model_classification, index_table
)
```
**Function**: `system_setup.initialize_mfa_system()`  
**Parameters**: `model_classification`, `index_table`  
**Returns**: Empty but structured MFAsystem object  
**Purpose**: Create the base MFA system with proper structure

### **3. Load and Define Processes**
```python
mfa_system_base, all_excel_data = system_setup.load_and_define_processes(
    mfa_system_base, input_file, data_loader
)
```
**Function**: `system_setup.load_and_define_processes()`  
**Parameters**: `mfa_system_base`, `input_file`, `data_loader`  
**Returns**: Updated MFA system and all Excel data  
**Purpose**: Load process definitions and initial stocks from Excel

### **4. Load Parameters**
```python
dsm_params = data_loader.load_dsm_parameters(all_excel_data)
fomp_params = data_loader.load_fomp_parameters(all_excel_data)
uncertainty_params = data_loader.load_uncertainty_definitions(all_excel_data)
```
**Functions Called**:
- `data_loader.load_dsm_parameters()` → Sheet: `3_1_Definition_DSM`
- `data_loader.load_fomp_parameters()` → Sheet: `3_2_Definition_FOMP`
- `data_loader.load_uncertainty_definitions()` → Sheet: `4_1_Uncertainty_Parameters`

## 🔗 2.2 MFA Calculation Execution (Lines 250-300)

### **5. Define Flows and Parameters**
```python
mfa_system_configured, _ = system_setup.define_flows_and_parameters(
    mfa_system_base, all_excel_data
)
```
**Function**: `system_setup.define_flows_and_parameters()`  
**Parameters**: `mfa_system_base`, `all_excel_data`  
**Returns**: Configured MFA system  
**Purpose**: Define all flows and transfer coefficients

### **5.1 Process Dynamic Transfer Coefficients**
```python
dynamic_tcs = system_setup.create_dynamic_tc_parameters(
    dynamic_tc_sheet, mfa_system_configured.IndexTable.Classification['Time'].Items
)
```
**Function**: `system_setup.create_dynamic_tc_parameters()`  
**Parameters**: `dynamic_tc_sheet`, time classification items  
**Returns**: Dynamic transfer coefficient parameters  
**Excel Data**: Sheet `2_5_dynamic_tcs`

### **6. Run Calculation**
```python
mfa_system_with_results, dsm_details = solver.run_mfa_calculation(
    mfa_system_configured, dsm_params, fomp_params, config
)
```
**Function**: `solver.run_mfa_calculation()`  
**Parameters**: Configured system, DSM params, FOMP params, config  
**Returns**: MFA system with results and DSM details  
**Purpose**: Execute the core MFA calculation

## ⚖️ 2.3 Mass Balance Validation (Lines 300-350)

### **Mass Balance Error Calculation**
```python
for process in mfa_system_with_results.ProcessList:
    if hasattr(process, 'MassBalance') and process.MassBalance is not None:
        for year_idx, year in enumerate(range(start_year, end_year + 1)):
            for element_idx, element in enumerate(elements):
                error = process.MassBalance[year_idx, element_idx]
                if abs(error) > 1e-6:  # Significant error threshold
                    mass_balance_errors.append({...})
```
**Purpose**: Check mass balance errors across all processes, years, and elements  
**Threshold**: 1e-6 (significant error threshold)

### **Mass Balance Visualization**
```python
plotting.plot_total_mass_balance_error(mfa_system_with_results)
plotting.plot_optimized_mass_balance_error(mfa_system_with_results)
```
**Functions Called**:
- `plotting.plot_total_mass_balance_error()` - General overview plot
- `plotting.plot_optimized_mass_balance_error()` - Time-specific interactive plot

### **Debug Flow Analysis**
```python
debug_flow = mfa_system_with_results.FlowDict.get('F_00_02')
```
**Purpose**: Debug specific flow for troubleshooting  
**Flow**: F_00_02 (example flow for debugging)

## 🟦 2.4 Sankey-Style Block Flow Diagram (Lines 350-400)

### **Diagram Generation**
```python
dot_sankey = plot_graphviz_flow_chart_sankey_style(
    input_file,
    title="BioDYM System - Sankey-Style Block Flow Diagram",
    rankdir="LR",
    ranksep=1.0,
    nodesep=0.5
)
```
**Function**: `plot_graphviz_flow_chart_sankey_style()`  
**Parameters**: Input file, title, layout parameters  
**Returns**: Graphviz diagram object  
**Purpose**: Create visual representation of the system

### **File Handling**
```python
tmp_dir = tempfile.gettempdir()
tmp_filename = f"biodym_sankey_style_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
dot_sankey.render(tmp_path, format='png', cleanup=True)
```
**Purpose**: Create temporary PNG file for display  
**Cleanup**: Automatic cleanup after display

## 📈 2.5 Results Overview (Lines 400-450)

### **Final Stock Values**
```python
for stock_name, stock in mfa_system_with_results.StockDict.items():
    if stock_name.startswith('S_'):  # Absolute stocks only
        final_value = stock.Values[-1, 0]  # Material dimension, final year
        final_stocks.append({
            'Stock': stock_name,
            'Final Value (Mg)': stock_name
        })
```
**Purpose**: Display final stock values for the last year  
**Filter**: Only absolute stocks (starting with 'S_')  
**Dimension**: Material dimension (index 0)

### **Flow Summary**
```python
for flow_id, flow in mfa_system_with_results.FlowDict.items():
    avg_flow = np.mean(flow.Values[:, 0])  # Average material flow
    flow_summary.append({
        'Flow ID': flow_id,
        'From': flow.P_Start,
        'To': flow.P_End,
        'Avg Flow (Mg/year)': avg_flow
    })
```
**Purpose**: Display flow summary with average values  
**Calculation**: Mean flow across all years  
**Display**: First 10 flows

## 📊 Excel Data Mapping for Step 2

| **Data Type** | **Sheet Name** | **Function** | **Purpose** | **Required** |
|---------------|----------------|--------------|-------------|--------------|
| **DSM Parameters** | `3_1_Definition_DSM` | `data_loader.load_dsm_parameters()` | Load DSM configuration | ❌ Optional |
| **FOMP Parameters** | `3_2_Definition_FOMP` | `data_loader.load_fomp_parameters()` | Load FOMP configuration | ❌ Optional |
| **Uncertainty Parameters** | `4_1_Uncertainty_Parameters` | `data_loader.load_uncertainty_definitions()` | Load Monte Carlo parameters | ❌ Optional |
| **Process Definitions** | `2_1_Definition_Processes` | `system_setup.load_and_define_processes()` | Load process structure | ✅ Required |
| **Initial Stocks** | `2_4_Initial_Stock` | `system_setup.load_and_define_processes()` | Load initial stock values | ✅ Required |
| **Flow Definitions** | `1_1_Definition_Flows` | `system_setup.define_flows_and_parameters()` | Define flow structure | ✅ Required |
| **Transfer Coefficients** | `2_3_Process_TCs` | `system_setup.define_flows_and_parameters()` | Load transfer coefficients | ✅ Required |
| **Dynamic TCs** | `2_5_dynamic_tcs` | `system_setup.create_dynamic_tc_parameters()` | Load dynamic transfer coefficients | ✅ Required |

## 🔍 Function Usage Analysis for Step 2

### **Functions Actually Used**
1. **System Setup**: `system_setup.define_model_scope()`, `system_setup.initialize_mfa_system()`, `system_setup.load_and_define_processes()`, `system_setup.define_flows_and_parameters()`, `system_setup.create_dynamic_tc_parameters()`
2. **Data Loading**: `data_loader.load_dsm_parameters()`, `data_loader.load_fomp_parameters()`, `data_loader.load_uncertainty_definitions()`
3. **Solver**: `solver.run_mfa_calculation()`
4. **Plotting**: `plotting.plot_total_mass_balance_error()`, `plotting.plot_optimized_mass_balance_error()`, `plot_graphviz_flow_chart_sankey_style()`
5. **ODYM**: `msc.Parameter()` - Creating parameter objects

### **Excel Data Usage**
- **Heavy Excel usage** - Multiple sheets loaded and processed
- **Parameter extraction** - DSM, FOMP, uncertainty parameters
- **Process definition** - Complete system structure from Excel
- **Flow configuration** - Transfer coefficients and flow definitions

## 📝 Key Findings

1. **Step 2 is the core calculation phase** - heavy use of BioDYM functions
2. **Excel data is extensively used** - 8+ sheets actively processed
3. **Multiple calculation engines** - DSM, FOMP, Monte Carlo support
4. **Comprehensive validation** - Mass balance checks and error visualization
5. **Visual output generation** - Sankey diagrams and result summaries

## 🚀 Next Steps

- Continue with Step 3: Visualization
- Analyze plotting function usage
- Map Excel data usage in visualization functions
- Continue identifying unused functions

---

*Analysis Completed: 2025-08-31*  
*Step: 2/4*  
*Status: ✅ COMPLETED*
