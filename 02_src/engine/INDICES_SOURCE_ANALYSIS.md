# Indices Source Analysis: Excel vs. Hardcoded

**Date**: 2025-10-27  
**Question**: Are the Indices (like "t,e") loaded from the Excel file?

---

## Answer: **NO, Currently Hardcoded**

BioDYM currently **hardcodes** all `Indices` to `"t,e"` in the Python code. The Excel file does NOT currently define indices columns.

---

## Current Implementation

### 1. Flow Indices (Hardcoded)

**Location**: `02_src/system_setup.py:339`

```python
def _initialize_flows(mfa_system, flow_definitions):
    for _, row in flow_definitions.iterrows():
        if pd.notna(row["Flow_Name"]):
            start_id, end_id = int(row["Flow_Output_Process_ID"]), int(row["Input_Process_ID"])
            
            # ⬅️ HARDCODED: Indices="t,e"
            flow_obj = msc.Flow(
                Name=row["Flow_ID"], 
                P_Start=start_id, 
                P_End=end_id, 
                Indices="t,e"  # ⬅️ Always "t,e"
            )
```

**Excel Sheet**: `1_1_Definition_Flows`  
**Does NOT have**: `Indices` column

---

### 2. Stock Indices (Hardcoded)

**Location**: `02_src/system_setup.py:219,222`

```python
def load_and_define_processes(mfa_system, input_data, data_loader):
    for _, row in process_definitions.iterrows():
        if should_create_stock:
            # ⬅️ HARDCODED: Indices="t,e"
            mfa_system.StockDict[f"dS_{process_id}"] = msc.Stock(
                Name=f"dS_{process_id}", 
                P_Res=process_id, 
                Type=1, 
                Indices="t,e"  # ⬅️ Always "t,e"
            )
            
            mfa_system.StockDict[f"S_{process_id}"] = msc.Stock(
                Name=f"S_{process_id}", 
                P_Res=process_id, 
                Type=0, 
                Indices="t,e"  # ⬅️ Always "t,e"
            )
```

**Excel Sheet**: `2_1_Definition_Processes`  
**Does NOT have**: `Stock_Indices` column

---

### 3. Parameter Indices (Scalar = Empty)

**Location**: `02_src/system_setup.py:420`

```python
def define_flows_and_parameters(mfa_system, content_definitions):
    for _, row in content_definitions.iterrows():
        param_name = f"{element}_{flow_id}"
        
        # ⬅️ HARDCODED: Indices="" for scalar parameters
        mfa_system.ParameterDict[param_name] = msc.Parameter(
            Name=param_name, 
            ID=parameter_id_counter, 
            Values=row[column_name], 
            Indices="",  # ⬅️ Empty string for scalar
            Unit="1"
        )
```

**Excel Sheet**: `1_1_Definition_Flows` (for content parameters)  
**Does NOT have**: `Indices` column for parameters

---

## What's in the Excel File?

### Current Excel Columns

**Sheet: `1_1_Definition_Flows`**
```
Flow_ID | Flow_Name | Flow_Output_Process_ID | Input_Process_ID | Flow_WC[%] | Flow_DM[%] | Flow_CC_DM[%]
```
❌ **Missing**: `Indices` column

**Sheet: `2_1_Definition_Processes`**
```
ID | Process_Name | Process_Logic | TC_Configuration | Stock_Configuration
```
❌ **Missing**: `Stock_Indices` column

---

## How Should It Work (Future Enhancement)?

### Proposed: Excel-Driven Indices

**Sheet: `1_1_Definition_Flows`** - ADD Indices column:
```
Flow_ID | Flow_Name | Flow_Output_Process_ID | Input_Process_ID | Indices | Flow_WC[%] | Flow_DM[%] | Flow_CC_DM[%]
1       | Flow_001  | 1                      | 2                | t,e     | 20        | 80         | 45
2       | Flow_002  | 2                      | 3                | t,e,r   | 10        | 90         | 50
```

**Sheet: `2_1_Definition_Processes`** - ADD Stock_Indices column:
```
ID | Process_Name | Process_Logic | Stock_Configuration | Stock_Indices
1  | Harvest      | DSM           | Stock               | t,e
2  | Processing   | DSM           | Stock               | t,e,r
```

---

## Required Code Changes

### Step 1: Update Data Loader

**File**: `02_src/data_loader.py:169`

```python
# BEFORE
REQUIRED_STRUCTURE = {
    "1_1_Definition_Flows": ["Flow_ID", "Flow_Name", "Flow_Output_Process_ID", "Input_Process_ID", "Flow_WC[%]", "Flow_DM[%]", "Flow_CC_DM[%]"],
    # ...
}

# AFTER (make Indices optional with default)
REQUIRED_STRUCTURE = {
    "1_1_Definition_Flows": ["Flow_ID", "Flow_Name", "Flow_Output_Process_ID", "Input_Process_ID", "Flow_WC[%]", "Flow_DM[%]", "Flow_CC_DM[%]"],  # Note: Indices is optional
    # ...
}
```

---

### Step 2: Update Flow Creation

**File**: `02_src/system_setup.py:339`

```python
# BEFORE
flow_obj = msc.Flow(
    Name=row["Flow_ID"], 
    P_Start=start_id, 
    P_End=end_id, 
    Indices="t,e"  # ⬅️ Hardcoded
)

# AFTER
flow_indices = str(row.get("Indices", "t,e")).strip()  # Get from Excel, default to "t,e"

flow_obj = msc.Flow(
    Name=row["Flow_ID"], 
    P_Start=start_id, 
    P_End=end_id, 
    Indices=flow_indices  # ⬅️ From Excel!
)
```

---

### Step 3: Update Stock Creation

**File**: `02_src/system_setup.py:219,222`

```python
# BEFORE
mfa_system.StockDict[f"dS_{process_id}"] = msc.Stock(
    Name=f"dS_{process_id}", 
    P_Res=process_id, 
    Type=1, 
    Indices="t,e"  # ⬅️ Hardcoded
)

# AFTER
stock_indices = str(row.get("Stock_Indices", "t,e")).strip()  # Get from Excel

mfa_system.StockDict[f"dS_{process_id}"] = msc.Stock(
    Name=f"dS_{process_id}", 
    P_Res=process_id, 
    Type=1, 
    Indices=stock_indices  # ⬅️ From Excel!
)
```

---

## Why Hardcode Indices Currently?

### Current Approach (2D System)

BioDYM currently assumes **all** flows and stocks have dimensions `(Time, Element)`, which maps to `Indices="t,e"`.

**Benefits**:
- ✅ Simple and consistent
- ✅ Works for all current use cases
- ✅ No user configuration needed
- ✅ Fast implementation

**Limitations**:
- ❌ Cannot support multi-dimensional models (e.g., `Indices="t,e,r"` for Region dimension)
- ❌ All flows/stocks must use same dimensions
- ❌ Not flexible for future enhancements

---

## When Would You Need Excel-Driven Indices?

### Use Cases:

1. **Multi-dimensional Models**:
   - Add Region dimension: `Indices="t,e,r"`
   - Add Material dimension: `Indices="t,e,m"`
   - Full separation: `Indices="t,e,r,g,m,p"`

2. **Heterogeneous Flows**:
   - Some flows: `Indices="t,e"` (simple)
   - Other flows: `Indices="t,e,r"` (with region)
   - Mixed dimensionality

3. **User Configuration**:
   - Let users define dimensions in Excel
   - Different models need different dimensions
   - Flexibility for various applications

---

## Current Status vs. Future

### Current (Phase 1a - 2D System)

```
✅ Indices hardcoded to "t,e"
✅ All flows: (26, 4) = Time × Element
✅ All stocks: (26, 4) = Time × Element
✅ Works perfectly for 2D models
```

### Future (Multi-dimensional System)

```
⏳ Indices loaded from Excel
⏳ Each flow/stock can have different Indices
⏳ Support for "t,e,r", "t,e,m", etc.
⏳ User-configurable dimensions
```

---

## Implementation Priority

### Not Required for Current Phase 1a

✅ **Phase 1a is COMPLETE without Excel-driven Indices**

The current hardcoded approach is:
- ✅ **ODYM compliant** (indices are correctly set)
- ✅ **Functional** for 2D models
- ✅ **Simple** and maintainable

### Future Enhancement (Phase 2?)

⏳ **Excel-driven Indices** would be useful for:
- Multi-dimensional models (3D, 4D, etc.)
- User flexibility
- Advanced use cases

---

## Summary

| Aspect | Current | Future (Potential) |
|--------|---------|-------------------|
| **Source** | Hardcoded in Python | Excel file |
| **Columns** | None in Excel | `Indices`, `Stock_Indices` |
| **Default** | Always `"t,e"` | Configurable per flow/stock |
| **Flexibility** | Fixed 2D | Multi-dimensional |
| **Status** | ✅ Working now | ⏳ Future enhancement |

---

## Conclusion

**Answer**: Indices are **NOT** currently loaded from Excel. They are **hardcoded to "t,e"** in `system_setup.py`.

This is **acceptable for Phase 1a** (2D compliance), but **Excel-driven indices** would be a useful future enhancement for multi-dimensional models.

