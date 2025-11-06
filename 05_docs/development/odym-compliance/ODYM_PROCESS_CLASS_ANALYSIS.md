# ODYM Process Class: Analysis & BioDYM Usage

**Date**: 2025-10-27  
**Reference**: [ODYM Process Class](https://github.com/IndEcol/ODYM/blob/master/src/odym/classes/ODYM_Classes.py#L454)

---

## ODYM Process Class Definition

### Official ODYM Process Structure

**Location**: `06_framework/ODYM-master_20241127/odym/modules/ODYM_Classes.py:454-498`

```python
class Process(Obj):
    """Class with the definition and methods for a process in ODYM"""
    
    def __init__(
        self,
        Name=None,          # Process name
        ID=None,            # Process ID
        UUID=None,          # Process UUID
        Bipartite=None,     # 't' or 'd' for bipartite graphs
        Graphical=None,     # Dictionary of graphical properties
        Extensions=None,     # Dictionary for additional data
        Parameters=None,    # List of process parameters
    ):
        """Basic initialisation of a process."""
        Obj.__init__(self, Name=Name, ID=ID, UUID=UUID)
        self.Bipartite = Bipartite
        self.Extensions = Extensions      # ⬅️ Can store custom data!
        self.Graphical = Graphical
```

### Key Attributes Explained

| Attribute | Type | Description | BioDYM Usage |
|-----------|------|-------------|--------------|
| `Name` | str | Process name | `"Harvest"`, `"Processing"` |
| `ID` | int | Process identifier | Process ID from Excel |
| `Extensions` | dict | **Additional custom data** | Used for TC/Stock configuration |
| `Graphical` | dict | **Visualization properties** | Not used by BioDYM |
| `Bipartite` | str | 't' or 'd' for graph type | Not used by BioDYM |

---

## BioDYM's Process Usage

### How BioDYM Creates Processes

**Location**: `02_src/system_setup.py:207-209`

```python
def load_and_define_processes(mfa_system, input_data, data_loader):
    """Load processes from Excel and create ODYM Process objects"""
    
    for _, row in process_definitions.iterrows():
        process_id = int(row["ID"])
        process_name = row["Process_Name"]
        
        # Check TC configuration (could be "TC", "Static", "Dynamic", etc.)
        has_tcs = None
        if "TC_Configuration" in row and pd.notna(row["TC_Configuration"]):
            tc_config = str(row["TC_Configuration"]).strip()
            if tc_config in ["Static", "Dynamic"]:
                has_tcs = "TC"  # Store in Extensions
        
        # Create ODYM Process object
        mfa_system.ProcessList.append(
            msc.Process(
                Name=row["Process_Name"], 
                ID=process_id, 
                Extensions=has_tcs  # ⬅️ Store TC config
            )
        )
```

**Excel Sheet**: `2_1_Definition_Processes`
```
ID | Process_Name | Process_Logic | TC_Configuration | Stock_Configuration
1  | Harvest      | DSM           | Static           | Stock
2  | Processing   | TC            | Dynamic          | Stock
3  | Storage      | Standard      | None             | None
```

---

## Understanding Process Extensions

### What are Extensions?

Extensions allow storing **custom data** on Process objects:

```python
Process.Extensions = "TC"  # Simple value
# OR
Process.Extensions = {"type": "TC", "config": "Static"}  # Dictionary
```

**Why Use Extensions?**
- ✅ ODYM-compliant way to store custom data
- ✅ Better than adding custom attributes
- ✅ Processed can carry metadata without breaking ODYM structure

### BioDYM's Extension Usage

**Current Pattern** (```207:209:02_src/system_setup.py```):
```python
# Store TC configuration in Extensions
mfa_system.ProcessList.append(
    msc.Process(Name=row["Process_Name"], ID=process_id, Extensions=has_tcs)
)
```

**Example**:
```python
Process(1).Extensions = "TC"          # Has TC configuration
Process(2).Extensions = "TC"          # Has TC configuration
Process(3).Extensions = None          # No TC configuration
```

---

## The Process Hierarchy

### ODYM System Structure

```
MFAsystem
├─ ProcessList (list of Process objects)
│   ├─ Process(Name="Harvest", ID=1, Extensions="TC")
│   ├─ Process(Name="Processing", ID=2, Extensions="TC")
│   └─ Process(Name="Storage", ID=3, Extensions=None)
├─ FlowDict (flows CONNECTED to processes)
├─ StockDict (stocks AT processes)
└─ ParameterDict (parameters for processes)
```

### Process Relationships

**Processes** are the **nodes** in the MFA graph:

```
[Process 1: Harvest]
    └─ Flow OUT: F_001 → [Process 2]

[Process 2: Processing]
    ├─ Flow IN: F_001 ← [Process 1]
    ├─ Stock: S_2 (material stored)
    └─ Flow OUT: F_002 → [Process 3]

[Process 3: Storage]
    ├─ Flow IN: F_002 ← [Process 2]
    └─ Flow OUT: F_003 → [End]
```

---

## BioDYM's Process Types

### 1. Standard Process

```python
Process(Name="Storage", ID=3, Extensions=None)
# No special configuration
# Standard inflows/outflows
```

**Excel**: `Process_Logic = "Standard"`  
**Extensions**: `None`

---

### 2. TC-Driven Process

```python
Process(Name="Processing", ID=2, Extensions="TC")
# Has TC (Transfer Coefficient) configuration
# Uses TCs to calculate outflows from inflows
```

**Excel**: `TC_Configuration = "Static"` or `"Dynamic"`  
**Extensions**: `"TC"`  
**Logic**: Calculates outflows using transfer coefficients

---

### 3. DSM Process

```python
Process(Name="Harvest", ID=1, Extensions="TC")
# DSM (Dynamic Stock Model)
# Has stock-based outflow calculations
```

**Excel**: `Process_Logic = "DSM"`, `Stock_Configuration = "Stock"`  
**Extensions**: `"TC"` (if TCs used)  
**Logic**: Calculates outflows from stock change

---

### 4. FOMP Process

```python
Process(Name="Decomposition", ID=4, Extensions=None)
# FOMP (First-Order Mass Pool)
# Has exponential decay pools
```

**Excel**: `Process_Logic = "FOMP"`, FOMP definition sheet exists  
**Extensions**: `None` (FOMP handled separately)  
**Logic**: Calculates decay pools with exponential kinetics

---

## How BioDYM Uses Processes

### 1. Process Identification

**Location**: `02_src/engine/solver.py`

```python
def _identify_process_types(mfa_system, process_logic_map):
    """Identify different process types for different calculation methods"""
    
    dsm_processes = []
    fomp_processes = []
    
    for process in mfa_system.ProcessList:
        if process_logic_map[process.ID] == "DSM":
            dsm_processes.append(process.ID)
        elif process_logic_map[process.ID] == "FOMP":
            fomp_processes.append(process.ID)
    
    return dsm_processes, fomp_processes
```

---

### 2. TC-Configuration Check

**Location**: `02_src/engine/solver.py`

```python
# Check if process has TC configuration
has_tcs = (hasattr(process, 'Extensions') and process.Extensions == "TC")

if has_tcs:
    # Use TC-driven flow calculation
    _calculate_tc_driven_flows(mfa_system, ...)
```

---

### 3. Stock Association

**Location**: `02_src/system_setup.py`

```python
# Stocks are linked to processes via P_Res
for process in mfa_system.ProcessList:
    stocks_at_process = [
        stock for stock in mfa_system.StockDict.values() 
        if stock.P_Res == process.ID
    ]
    # stocks_at_process contains all stocks AT this process
```

---

### 4. Flow Association

**Location**: `02_src/engine/solver.py`

```python
# Find flows connected to a process
for process in mfa_system.ProcessList:
    inflows = [f for f in mfa_system.FlowDict.values() if f.P_End == process.ID]
    outflows = [f for f in mfa_system.FlowDict.values() if f.P_Start == process.ID]
    
    # Calculate mass balance
    net_flow = total_inflows - total_outflows
```

---

## Process Extensions: Proper Usage

### Current: Simple String

**BioDYM Pattern**:
```python
mfa_system.ProcessList.append(
    msc.Process(Name="Processing", ID=2, Extensions="TC")
)
```

**Pros**:
- ✅ Simple
- ✅ ODYM compliant
- ✅ Easy to check

**Cons**:
- ⚠️ Limited flexibility
- ⚠️ Only stores one value

---

### Future: Dictionary for Complex Data

**Potential Pattern**:
```python
mfa_system.ProcessList.append(
    msc.Process(
        Name="Processing", 
        ID=2, 
        Extensions={
            "TC_Config": "Static",
            "Stock_Config": "Stock",
            "Process_Logic": "DSM",
            "Outflow_Count": 2
        }
    )
)
```

**Benefits**:
- ✅ Stores multiple attributes
- ✅ More flexible
- ✅ Still ODYM compliant

---

## Process vs. Flow vs. Stock

### Process (Node)
- **Role**: Location/activity in the system
- **Has**: Name, ID, Extensions
- **Contains**: Stocks
- **Connects**: Flows (inflows and outflows)

### Flow (Edge)
- **Role**: Material movement between processes
- **Has**: P_Start, P_End, Values
- **Connects**: Two processes

### Stock (State)
- **Role**: Material accumulation at a process
- **Has**: P_Res, Values, Type
- **Belongs**: To one process

**Relationship**:
```
Process 1 (node) ──→ Flow (edge) ──→ Process 2 (node)
     ↑                                ↓
   Stock                          Stock
   (state)                         (state)
```

---

## ODYM Compliance: BioDYM's Process Usage

### ✅ Correct Usage

1. **Processes Created**: Using `msc.Process()`
2. **Name and ID Set**: From Excel data
3. **Extensions Used**: For TC configuration
4. **No Custom Attributes**: Uses Extensions instead ✅
5. **Proper Hierarchy**: Processes contain stocks, connect via flows

### Current Process Creation Pattern

```python
# From system_setup.py:207-209
mfa_system.ProcessList.append(
    msc.Process(
        Name=row["Process_Name"],     # ✅ From Excel
        ID=process_id,                # ✅ From Excel
        Extensions=has_tcs             # ✅ TC config
    )
)
```

---

## BioDYM's Process Extensions Usage

### Where Extensions Are Set

**Location**: `02_src/system_setup.py:207-209`

```python
# Check TC configuration from Excel
has_tcs = None
if "TC_Configuration" in row and pd.notna(row["TC_Configuration"]):
    tc_config = str(row["TC_Configuration"]).strip()
    if tc_config in ["Static", "Dynamic"]:
        has_tcs = "TC"  # Store in Extensions

# Create process with Extensions
mfa_system.ProcessList.append(
    msc.Process(Name=row["Process_Name"], ID=process_id, Extensions=has_tcs)
)
```

### Where Extensions Are Used

Currently, BioDYM does NOT actively use Extensions in calculations. The TC configuration is tracked via the `process_logic_map` dictionary instead.

**Potential Use**:
```python
# Could check Extensions instead of process_logic_map
for process in mfa_system.ProcessList:
    if hasattr(process, 'Extensions') and process.Extensions == "TC":
        # Process uses TC-driven flows
        calculate_tc_flows(mfa_system, process)
```

---

## Process ID = Index in ProcessList?

### ODYM Structure

```python
mfa_system.ProcessList = [
    Process(Name="Harvest", ID=1),    # Index 0, ID 1
    Process(Name="Processing", ID=2),  # Index 1, ID 2
    Process(Name="Storage", ID=3),     # Index 2, ID 3
]
```

**Important**: Process.ID ≠ Index in ProcessList!

```python
Process.ID = 1, 2, 3, ... (from Excel)
ProcessList index = 0, 1, 2, ... (Python array index)
```

**To Find Process by ID**:
```python
# DON'T assume index = ID
process = mfa_system.ProcessList[process_id - 1]  # ❌ BAD - assumes ID = index+1

# DO search by ID
process = next(p for p in mfa_system.ProcessList if p.ID == process_id)  # ✅ GOOD
```

BioDYM uses the **process_logic_map** dictionary to map IDs to logic types.

---

## Summary

### ODYM Process Class Usage in BioDYM

✅ **Perfectly Compliant**:
- Processes created using `msc.Process()`
- Name and ID correctly set from Excel
- Extensions used for TC configuration
- Proper hierarchy (Process → Stocks → Flows)
- No custom attributes on Process objects
- ODYM compliant ✅

### Current Pattern

```python
# Create process
mfa_system.ProcessList.append(
    msc.Process(Name="Processing", ID=2, Extensions="TC")
)

# Use in calculations
for process in mfa_system.ProcessList:
    flows_in = [f for f in mfa_system.FlowDict.values() if f.P_End == process.ID]
    flows_out = [f for f in mfa_system.FlowDict.values() if f.P_Start == process.ID]
```

---

## Next: Parameter Class Analysis?

Should we analyze:
1. **Parameter** class usage?
2. **Complete summary** of all ODYM classes?

**Process analysis is complete and fully ODYM compliant!** ✅






