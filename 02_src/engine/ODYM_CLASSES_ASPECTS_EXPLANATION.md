# Understanding ODYM Classes, Aspects, and Class Parameters

## Conceptual Clarification

### **ODYM Classes** (Python Objects)
ODYM classes are **Python objects** that represent different components of a Material Flow Analysis (MFA) system. The main ODYM classes are:

1. **`Process`** - Represents a transformation process (e.g., Harvest, Processing, Storage)
2. **`Flow`** - Represents a material flow between processes (e.g., Rye_Straw_Flow)
3. **`Stock`** - Represents material stocks at processes (e.g., dS_1, S_1)
4. **`Parameter`** - Represents system parameters (e.g., Transfer Coefficients, Lifetimes)
5. **`Classification`** - Represents dimension classifications (e.g., Time, Element)
6. **`MFAsystem`** - Represents the entire MFA system

### **Aspects (Dimensions)** 
Aspects are **data structure dimensions** used to describe the multi-dimensional nature of flows, stocks, and parameters. From the ODYM framework:

```python
self.Aspects = {
    "Time": "Model time",
    "Cohort": "Age-cohort",
    "OriginProcess": "Process where flow originates",
    "DestinationProcess": "Destination process of flow",
    "OriginRegion": "Region where flow originates from",
    "DestinationRegion": "Region where flow is bound to",
    "Good": "Process, good, or commodity",
    "Material": "Material: ore, alloy, scrap type, ...",
    "Element": "Chemical element",
}
```

**Key Point**: Aspects define the **dimensional structure** of data arrays (e.g., Flow.Values, Stock.Values, Parameter.Values)

### **Class Parameters (Attributes)**
Class parameters are **properties/attributes** of ODYM class instances. Each class has specific parameters:

## Detailed Class Structure Analysis

### **1. Flow Class Parameters**

```python
class Flow(Obj):
    def __init__(
        self,
        Name=None,        # Flow name
        ID=None,          # Flow ID
        P_Start=None,     # Origin process ID
        P_End=None,       # Destination process ID
        Indices=None,     # AS
        
PECT: Defines which dimensions this flow uses (e.g., "t,e")
        Values=None,      # Values: numpy array with shape matching Indices
    )
```

**Aspects for Flow**:
- **Indices**: Defines which dimensions/aspects the flow uses (e.g., "t,e" for time and element)
- **Values**: Numpy array with shape matching the indices

**Example**:
```python
# Flow with Indices="t,e" (time and element)
flow = Flow(
    Name="Rye_Straw_Flow",
    P_Start=1,  # From Harvest process
    P_End=2,    # To Processing process
    Indices="t,e",  # Time and Element dimensions
    Values=np.zeros((26, 4))  # Shape: (years, elements)
)
```

### **2. Process Class Parameters**

```python
class Process(Obj):
    def __init__(
        self,
        Name=None,        # Process name
        ID=None,          # Process ID
        Extensions=None,  # Process extensions (custom data)
    )
```

**Aspects for Process**:
- Processes themselves don't use aspects/dimensions
- Processes are simple objects with ID, Name, and Extensions
- The **position** of processes in ProcessList determines their ID

### **3. Stock Class Parameters**

```python
class Stock(Obj):
    def __init__(
        self,
        Name=None,        # Stock name
        ID=None,          # Stock ID
        P_Res=None,       # Residence process ID
        Indices=None,     # ASPECT: Defines which dimensions this stock uses
        Values=None,      # Values: numpy array with shape matching Indices
        Type=None,        # Stock type (0=absolute, 1=change)
    )
```

**Aspects for Stock**:
- **Indices**: Defines which dimensions/aspects the stock uses (e.g., "t,e")
- **Values**: Numpy array with shape matching the indices

**Example**:
```python
# Stock with Indices="t,e" (time and element)
stock = Stock(
    Name="dS_1",
    P_Res=1,  # At process 1
    Type=1,   # Change stock
    Indices="t,e",  # Time and Element dimensions
    Values=np.zeros((26, 4))  # Shape: (years, elements)
)
```

### **4. Parameter Class Parameters**

```python
class Parameter(Obj):
    def __init__(
        self,
        Name=None,        # Parameter name
        ID=None,          # Parameter ID
        Indices=None,     # ASPECT: Defines which dimensions this parameter uses
        Values=None,      # Values: numpy array with shape matching Indices
        Unit=None,        # Unit of measurement
    )
```

**Aspects for Parameter**:
- **Indices**: Defines which dimensions/aspects the parameter uses (e.g., "t,e")
- **Values**: Numpy array with shape matching the indices

### **5. Classification Class Parameters**

```python
class Classification(Obj):
    def __init__(
        self,
        Name=None,              # Classification name
        ID=None,                # Classification ID
        Dimension=None,         # Dimension type (Time, Element, etc.)
        Items=None,             # List of items in this classification
        IDs=None,               # List of IDs for items
        AdditionalProps={},     # Additional properties
    )
```

**Purpose**: Classifications define **what items** are in each dimension

## How Aspects (Dimensions) Work with Classes

### **The Relationship**:

1. **Classifications define WHAT items** are in each dimension:
```python
classification_Time = Classification(
    Name="Time",
    Dimension="Time",
    Items=[2020, 2021, 2022, 2023, 2024, 2025]
)

classification_Element = Classification(
    Name="Elements",
    Dimension="Element",
    Items=["C", "N", "P"]
)
```

2. **Indices define WHICH dimensions** a class instance uses:
```python
flow = Flow(
    Name="Rye_Straw_Flow",
    Indices="t,e"  # This flow uses Time (t) and Element (e) dimensions
)
```

3. **Values match the Indices**:
```python
# Indices="t,e" means Values shape must be (n_time, n_element)
flow.Values = np.zeros((26, 3))  # 26 years, 3 elements
```

### **IndexTable Maps Everything Together**:

```python
index_table = pd.DataFrame({
    "Aspect": ["Time", "Element"],
    "Dimension": ["Time", "Element"],
    "Classification": [classification_Time, classification_Element],
    "IndexLetter": ["t", "e"],
})
```

This IndexTable tells the system:
- **"t"** refers to **Time** dimension with items [2020, 2021, ...]
- **"e"** refers to **Element** dimension with items ["C", "N", "P"]
- Flow with Indices="t,e" has shape (26, 3)

## Your Excel Configuration - Mapping to ODYM Classes

### **What You're Defining in Excel**:

#### **1. Dimensions/Aspects Selection** (Your ODYM Configuration Sheet)
```excel
| Dimension Name | Use Dimension | Items |
|----------------|---------------|-------|
| Time | TRUE | 2020-2050 |
| Element | TRUE | C, Remaining DM |
| Process | TRUE | (defined in 2_1_Definition_Processes) |
| Material | TRUE | WC, DM |
| Good | TRUE | (defined in 1_1_Definition_Flows) |
| Region | TRUE | Case_Study_Region |
```

**This creates Classifications** for each dimension

#### **2. Process Definitions** (Sheet: 2_1_Definition_Processes)
```excel
| ID | Process_Name | Process_Logic |
|----|--------------|---------------|
| 1 | Harvest | DSM |
| 2 | Processing | DSM |
```

**This creates Process objects** with Name, ID, and Extensions

#### **3. Flow Definitions** (Sheet: 1_1_Definition_Flows)
```excel
| Flow_ID | Flow_Name | P_Start | P_End | Indices |
|---------|-----------|---------|-------|---------|
| 1 | Rye_Straw_Flow | 1 | 2 | t,e |
```

**This creates Flow objects** with Name, ID, P_Start, P_End, and Indices

**The Indices here specify which aspects/dimensions this flow uses!**

## Key Understanding

### **What You DON'T Need to Do**:
❌ You don't need to define class parameters for every possible aspect
❌ You don't need to describe every class instance with all aspects

### **What You DO Need to Do**:
✅ Define which dimensions/aspects your system will use (your configuration sheet)
✅ Define the Indices for each Flow, Stock, and Parameter (which dimensions it uses)
✅ The Values arrays will automatically match the Indices

## Example: Complete Flow Definition

```python
# From your Excel:
# Sheet: 1_1_Definition_Flows
Flow_ID: 1
Flow_Name: "Rye_Straw_Flow"
P_Start: 1 (Harvest process)
P_End: 2 (Processing process)
Indices: "t,e"  # Uses Time and Element dimensions

# This creates in Python:
flow = Flow(
    Name="Rye_Straw_Flow",
    ID=1,
    P_Start=1,
    P_End=2,
    Indices="t,e"  # This defines which aspects (dimensions) the flow uses
)

# The Values array will be automatically created with shape (n_time, n_element)
# based on your IndexTable

# If you want multi-dimensional flows:
Flow with Indices="t,e,p,m,g"  # Time, Element, Process, Material, Good
# Values shape will be (n_time, n_element, n_process, n_material, n_good)
```

## Summary

**ODYM Classes** = Python objects (Process, Flow, Stock, Parameter)
**Aspects (Dimensions)** = Data structure dimensions (Time, Element, Process, Material, Good, Region)
**Class Parameters** = Properties of class instances (Name, ID, Indices, Values, etc.)

**Your Excel configuration**:
1. Defines **which dimensions** to use (configuration sheet)
2. Defines **which Indices** each Flow/Stock/Parameter uses (definitions sheets)
3. ODYM automatically creates **Values arrays** with correct shapes

**You don't need to manually describe every class with every aspect** - you just need to specify the Indices for each class instance, and ODYM handles the rest!

---

*Document Version: 1.0*  
*Last Updated: [Current Date]*  
*Author: BioDYM Development Team*
