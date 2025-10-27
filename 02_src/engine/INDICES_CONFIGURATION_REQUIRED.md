# BioDYM Indices Configuration in Excel - Critical Requirement

## Critical Issue: Indices are Currently Hardcoded!

### **Current Implementation Problem**

Your code currently **hardcodes** `Indices="t,e"` everywhere:

```python
# In system_setup.py line 179, 182
mfa_system.StockDict[f"dS_{process_id}"] = msc.Stock(
    Name=f"dS_{process_id}", P_Res=process_id, Type=1, Indices="t,e"  # ❌ HARDCODED!
)

# In system_setup.py line 289
flow_obj = msc.Flow(Name=row["Flow_ID"], P_Start=start_id, P_End=end_id, Indices="t,e")  # ❌ HARDCODED!
```

**This is the MAJOR issue!** You need to make Indices configurable via Excel!

## Required Excel Changes for Indices

### **1. Add Indices Column to Flow Definitions**

**Sheet: `1_1_Definition_Flows`** - Add Indices column:

| Flow_ID | Flow_Name | Flow_Output_Process_ID | Input_Process_ID | Indices | Flow_WC[%] | Flow_DM[%] | Flow_CC_DM[%] |
|---------|-----------|------------------------|------------------|---------|------------|------------|---------------|
| 1 | Rye_Harvest_Flow | 1 | 2 | t,e | 20 | 80 | 45 |
| 2 | Biochar_Production_Flow | 2 | 3 | t,e | 5 | 95 | 80 |

**Indices Options**:
- `"t,e"` - Basic (Time, Element) - Current default
- `"t,e,p"` - With Process dimension
- `"t,e,g"` - With Good dimension  
- `"t,e,m"` - With Material dimension
- `"t,e,r"` - With Region dimension
- `"t,e,p,g,m"` - Multi-dimensional

### **2. Add Indices Column to Stock Definitions**

**Sheet: `2_1_Definition_Processes`** - Add Indices column for stocks:

| ID | Process_Name | Process_Logic | Stock_Configuration | Stock_Indices |
|----|--------------|---------------|-------------------|---------------|
| 1 | Harvest | DSM | Stock | t,e |
| 2 | Processing | DSM | Stock | t,e |
| 3 | Storage | Standard | Stock | t,e |

**Stock_Indices Options**:
- `"t,e"` - Basic (Time, Element)
- `"t,e,p"` - With Process dimension
- `"t,e,g"` - With Good dimension
- `"t,e,m"` - With Material dimension

### **3. Add Indices to Parameter Definitions**

**Sheet: `2_2_static_TCs` and `2_3_dynamic_TCs`** - Add Indices column:

| Flow_ID | Process_ID | TC_material_ID | TC_Value_material | Year | Indices |
|---------|------------|----------------|-------------------|------|---------|
| 1 | 2 | TC_1 | 0.5 | 2025 | t,e |

**Parameter Indices**:
- `"t,e"` - Time-dependent parameter
- `"e"` - Element-dependent parameter
- `"t"` - Time-only parameter

## Implementation Strategy

### **Phase 1: Excel Template Update**

#### **Step 1.1: Add Indices Columns**
1. Add `Indices` column to `1_1_Definition_Flows`
2. Add `Stock_Indices` column to `2_1_Definition_Processes`
3. Add `Indices` column to `2_2_static_TCs` and `2_3_dynamic_TCs`
4. Set default value as `"t,e"` for all rows (backward compatibility)

#### **Step 1.2: Data Loader Update**
Update `data_loader.py` to read Indices from Excel:

```python
# In validate_input_data()
REQUIRED_STRUCTURE = {
    "1_1_Definition_Flows": ["Flow_ID", "Flow_Name", "Flow_Output_Process_ID", "Input_Process_ID", "Indices"],  # Added Indices
    "2_1_Definition_Processes": ["ID", "Process_Name", "Process_Logic", "Stock_Configuration", "Stock_Indices"],  # Added Stock_Indices
    # ... other sheets
}
```

#### **Step 1.3: System Setup Update**
Update `system_setup.py` to use Indices from Excel:

```python
# In load_and_define_processes() - Update Stock creation
if should_create_stock:
    # Get Stock_Indices from Excel (default to "t,e" if not specified)
    stock_indices = str(row.get("Stock_Indices", "t,e")).strip()
    
    mfa_system.StockDict[f"dS_{process_id}"] = msc.Stock(
        Name=f"dS_{process_id}", P_Res=process_id, Type=1, Indices=stock_indices
    )
    mfa_system.StockDict[f"S_{process_id}"] = msc.Stock(
        Name=f"S_{process_id}", P_Res=process_id, Type=0, Indices=stock_indices
    )

# In define_flows_and_parameters() - Update Flow creation
for _, row in flow_definitions.iterrows():
    if pd.notna(row["Flow_Name"]):
        start_id, end_id = int(row["Flow_Output_Process_ID"]), int(row["Input_Process_ID"])
        
        # Get Indices from Excel (default to "t,e" if not specified)
        flow_indices = str(row.get("Indices", "t,e")).strip()
        
        flow_obj = msc.Flow(
            Name=row["Flow_ID"], 
            P_Start=start_id, 
            P_End=end_id, 
            Indices=flow_indices  # ✅ Now using Excel value!
        )
        flow_obj.DescriptiveName = row["Flow_Name"]
        mfa_system.FlowDict[row["Flow_ID"]] = flow_obj
```

### **Phase 2: Dynamic Indices Generation**

Create a function to automatically generate Indices based on configuration:

```python
def determine_flow_indices(mfa_system, custom_indices=None):
    """
    Determine flow indices based on ODYM configuration.
    
    Parameters:
    -----------
    mfa_system : msc.MFAsystem
        The MFA system object with IndexTable
    custom_indices : str, optional
        Custom indices string from Excel (e.g., "t,e,p")
    
    Returns:
    --------
    str : Indices string (e.g., "t,e,r,g,m,p")
    """
    # If custom indices specified, use them (with validation)
    if custom_indices:
        # Validate custom indices
        valid_indices = []
        for idx in custom_indices.split(","):
            if idx.strip() in mfa_system.IndexTable.index:
                valid_indices.append(idx.strip())
        return ",".join(valid_indices) if valid_indices else "t,e"
    
    # Otherwise, generate based on IndexTable
    indices = "t,e"  # Always include Time and Element
    
    # Add other dimensions based on IndexTable
    for dim in ["Region", "Good", "Material", "Process"]:
        if dim in mfa_system.IndexTable.index:
            idx_letter = mfa_system.IndexTable.loc[dim]["IndexLetter"]
            indices += f",{idx_letter}"
    
    return indices

# Usage in system_setup.py
flow_indices = row.get("Indices")  # Get from Excel
flow_indices = determine_flow_indices(mfa_system, flow_indices)  # Auto-generate if needed

flow_obj = msc.Flow(
    Name=row["Flow_ID"],
    P_Start=start_id,
    P_End=end_id,
    Indices=flow_indices
)
```

## Complete Excel Structure with Indices

### **1.1_Definition_Flows (Updated)**

| Flow_ID | Flow_Name | Flow_Output_Process_ID | Input_Process_ID | **Indices** | Flow_WC[%] | Flow_DM[%] | Flow_CC_DM[%] | **Good_ID** | **Material_ID** | **Process_Type_ID** | **Region_ID** |
|---------|-----------|------------------------|------------------|-------------|------------|------------|---------------|-------------|-----------------|-------------------|---------------|
| 1 | Rye_Harvest_Flow | 1 | 2 | t,e | 20 | 80 | 45 | 1 | 1 | 1 | 1 |
| 2 | Biochar_Flow | 2 | 3 | t,e,p | 5 | 95 | 80 | 2 | 1 | 2 | 1 |

### **2.1_Definition_Processes (Updated)**

| ID | Process_Name | Process_Logic | Stock_Configuration | **Stock_Indices** | **Process_Type_ID** | **Region_ID** |
|----|--------------|---------------|-------------------|------------------|-------------------|---------------|
| 1 | Harvest | DSM | Stock | t,e | 1 | 1 |
| 2 | Processing | DSM | Stock | t,e,p | 2 | 1 |
| 3 | Storage | Standard | Stock | t,e,g,m | 3 | 1 |

## Key Points

### **✅ What You Need to Add**

1. **Indices Column** to Flow definitions (required)
2. **Stock_Indices Column** to Process definitions (required)
3. **Indices Column** to Parameter definitions (optional)
4. **Dimension Reference Columns** (Good_ID, Material_ID, Process_Type_ID, Region_ID) - for multi-dimensional tracking

### **⚠️ Backward Compatibility**

Set default Indices as `"t,e"` in Excel so existing templates continue to work:

```excel
# In 1_1_Definition_Flows
Indices: "t,e" (default for all flows)

# In 2_1_Definition_Processes  
Stock_Indices: "t,e" (default for all stocks)
```

This ensures existing Excel files will work without modification!

## Summary

**Yes, you're absolutely right!** You need to add Indices columns to your flow and process definitions in Excel. This is **critical** for ODYM compliance because:

1. **Indices define which dimensions** each Flow/Stock/Parameter uses
2. **Currently hardcoded** as `"t,e"` everywhere in your code
3. **Need to be configurable** via Excel for full ODYM compliance
4. **Need dimension reference columns** to support multi-dimensional analysis

**The Excel file is NOT ready yet** - you need to add these Indices columns first!

---

*Document Version: 1.0*  
*Last Updated: [Current Date]*  
*Author: BioDYM Development Team*
