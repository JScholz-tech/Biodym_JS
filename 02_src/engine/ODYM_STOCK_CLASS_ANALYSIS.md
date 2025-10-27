# ODYM Stock Class: Analysis & BioDYM Usage

**Date**: 2025-10-27  
**Reference**: [ODYM Stock Class](https://github.com/IndEcol/ODYM/blob/master/src/odym/classes/ODYM_Classes.py#L535)

---

## ODYM Stock Class Definition

### Official ODYM Stock Structure

**Location**: `06_framework/ODYM-master_20241127/odym/modules/ODYM_Classes.py:535-568`

```python
class Stock(Obj):
    """Class with the definition and methods for a stock in ODYM"""
    
    def __init__(
        self,
        Name=None,          # Stock name
        ID=None,            # Stock ID
        UUID=None,          # Stock UUID
        P_Res=None,         # ⬅️ Process where stock resides (CRITICAL!)
        Indices=None,       # ⬅️ Dimension indices (e.g., "t,e")
        Type=None,          # ⬅️ Stock type (0=stock, 1=net change, 2=removal)
        Values=None,        # Stock values array
        Uncert=None,        # Uncertainty (%)
        Unit=None,          # Unit string
        Color=None,         # Color as 'R,G,B'
    ):
```

### Key Attributes Explained

| Attribute | Type | Description | BioDYM Usage |
|-----------|------|-------------|--------------|
| `Name` | str | Stock identifier | `"S_1"`, `"dS_1"` |
| `P_Res` | int | **Process ID where stock resides** | Process ID (e.g., `1`) |
| `Indices` | str | **Dimension indices** | `"t,e"` (Time, Element) |
| `Type` | int | **0=absolute stock, 1=net change, 2=removal** | `0` or `1` |
| `Values` | np.array | Stock values | Created by `Initialize_StockValues()` |

---

## BioDYM's Stock Usage

### How BioDYM Creates Stocks

**Location**: `02_src/system_setup.py:218-223`

```python
if should_create_stock:
    # dS = net stock change (Type=1)
    mfa_system.StockDict[f"dS_{process_id}"] = msc.Stock(
        Name=f"dS_{process_id}", 
        P_Res=process_id,    # ⬅️ Links stock to process
        Type=1,              # ⬅️ Net stock change
        Indices="t,e"        # ⬅️ Time × Element dimensions
    )
    
    # S = absolute stock (Type=0)
    mfa_system.StockDict[f"S_{process_id}"] = msc.Stock(
        Name=f"S_{process_id}", 
        P_Res=process_id,    # ⬅️ Links stock to process
        Type=0,              # ⬅️ Absolute stock value
        Indices="t,e"        # ⬅️ Time × Element dimensions
    )
```

---

## Stock Type Explanation

### Type=0: Absolute Stock (`S`)
- **Meaning**: Total stock at this process
- **Example**: `S_1` = total biomass stock at Process 1
- **Shape**: `(time_steps, elements)`
- **Usage**: Cumulative stock over time

### Type=1: Net Stock Change (`dS`)
- **Meaning**: Change in stock (inflows - outflows)
- **Example**: `dS_1` = change in stock at Process 1 per year
- **Shape**: `(time_steps, elements)`
- **Usage**: Calculate net flows

---

## The Relationship: Stocks ← Processes

### ODYM Structure

```
Process (ID=1, Name="Harvest")
    ├─ Flow IN: Biomass from field (P_End=1)
    ├─ Flow OUT: Biomass to processing (P_Start=1)
    └─ Stock AT: 
        ├─ dS_1 (net change, Type=1)
        └─ S_1 (absolute value, Type=0)
```

### P_Res Attribute (Critical!)

```python
Stock.P_Res = process_id  # ⬅️ Links stock to specific process
```

**Why `P_Res` is critical**:
- ODYM uses `P_Res` to link stocks to their parent process
- Mass balance calculations use `P_Res` to find stocks at each process
- Stock outflows depend on `P_Res` to know where stock is located

---

## BioDYM's Stock Pair Pattern

### Why Two Stocks Per Process?

BioDYM creates **TWO** stocks per process:

```python
# Pattern:
dS_processid  # Type=1 (net change)
S_processid    # Type=0 (absolute)
```

**Reason**: DSM (Dynamic Stock Model) requires:
1. **Net change** (`dS`) - to calculate inflows/outflows
2. **Absolute stock** (`S`) - to track cumulative stock

**Example**:
```python
Process 1: Harvest
├─ dS_1 = inflow - outflow (net change per year)
└─ S_1 = cumulative stock at process (total biomass)
```

---

## ODYM Compliance: BioDYM's Stock Usage

### ✅ Correct Usage

1. **P_Res Attached**: Stocks linked to processes via `P_Res`
2. **Indices Provided**: `Indices="t,e"` correctly set
3. **Type Distinguished**: Type=0 for absolute, Type=1 for net change
4. **Initialization**: Uses `Initialize_StockValues()` (ODYM method)
5. **No Custom Attributes**: No custom attrs on Stock objects

### Current Stock Creation Pattern

```python
# From system_setup.py:218-223
mfa_system.StockDict[f"dS_{process_id}"] = msc.Stock(
    Name=f"dS_{process_id}", 
    P_Res=process_id,     # ✅ Links to process
    Type=1,               # ✅ Net change type
    Indices="t,e"         # ✅ 2D dimensions
)

mfa_system.StockDict[f"S_{process_id}"] = msc.Stock(
    Name=f"S_{process_id}", 
    P_Res=process_id,     # ✅ Links to process
    Type=0,               # ✅ Absolute stock type
    Indices="t,e"         # ✅ 2D dimensions
)

# Then initialize with ODYM method
mfa_system.Initialize_StockValues()  # ✅ ODYM compliant
```

---

## How ODYM Processes Stocks

### 1. Initialization

```python
def Initialize_StockValues(self):
    """Creates numpy arrays for stocks with Indices"""
    for stock in self.StockDict.values():
        if stock.Values is None:
            stock.Values = np.zeros(shape_from_indices)  # Based on Indices!
```

**BioDYM**: Uses this method ✅

### 2. Consistency Check

```python
def Consistency_Check(self):
    # Validates that stock shapes match their Indices
    for stock in self.StockDict.values():
        expected_shape = shape_from(stock.Indices)
        actual_shape = stock.Values.shape
        assert expected_shape == actual_shape  # Validates!
```

**BioDYM**: Calls this method ✅

### 3. Mass Balance Calculation

**ODYM uses `P_Res` to group stocks by process**:

```python
for process_id in ProcessList:
    stocks_at_process = [s for s in StockDict.values() if s.P_Res == process_id]
    # Calculate mass balance using stocks_at_process
```

**BioDYM**: Uses `P_Res` correctly ✅

---

## Stock Indices Explained

### What Does `Indices="t,e"` Mean?

**`t`** = Time dimension (from IndexTable)
- Access: `IndexTable.loc["Time"]`
- Items: `[2020, 2021, ..., 2045]` (26 years)

**`e`** = Element dimension (from IndexTable)
- Access: `IndexTable.loc["Element"]`
- Items: `['material', 'WC', 'DM', 'CC']` (4 elements)

**Result**: `Values` array shape = `(26, 4)`

### Example Stock.Values Array

```python
# Stock S_1 with Indices="t,e"
S_1.Values.shape  # (26, 4) - 26 years × 4 elements

# Accessing values:
S_1.Values[0, 0]   # Year 2020, element 'material'
S_1.Values[0, 1]   # Year 2020, element 'WC'
S_1.Values[25, 3]  # Year 2045, element 'CC'
```

---

## Stock Indices vs. Aspects

### ODYM's Aspect System

Aspects define dimensions in IndexTable:

```
Aspect  | IndexLetter | Dimension    | Items
--------|-------------|--------------|------------------
Time    | 't'         | Time         | [2020, ..., 2045]
Element | 'e'         | Element      | ['material', 'WC', 'DM', 'CC']
Region  | 'r'         | Region       | ['Case_Study_Region']
Good    | 'g'         | Good         | ['Biomass']
Material| 'm'         | Material     | ['WC', 'DM']
Process | 'p'         | Process      | [1, 2, 3, ...]
```

### Indices String Links to Aspects

```python
Indices="t,e"    → Uses Time + Element aspects
Indices="t,e,r"  → Uses Time + Element + Region aspects
Indices="t,r"    → Uses Time + Region aspects
```

**BioDYM**: Currently uses `Indices="t,e"` (2D) ✅

---

## Summary

### ODYM Stock Class Usage in BioDYM

✅ **Correctly Implemented**:
- Stocks linked to processes via `P_Res`
- Proper `Indices="t,e"` for 2D structure
- Type 0 (absolute) and Type 1 (net change) correctly used
- ODYM's `Initialize_StockValues()` called
- No custom attributes added
- ODYM compliant ✅

### Current Pattern

```python
# Create two stocks per process
dS = msc.Stock(Name="dS_X", P_Res=X, Type=1, Indices="t,e")  # Net change
S = msc.Stock(Name="S_X", P_Res=X, Type=0, Indices="t,e")    # Absolute

# Initialize with ODYM
mfa_system.Initialize_StockValues()
```

---

## Next: Flow Class Analysis?

Should we analyze:
1. **Flow** class usage?
2. **Process** class usage?
3. **Parameter** class usage?

**All are compliant** based on Phase 1a work! ✅


