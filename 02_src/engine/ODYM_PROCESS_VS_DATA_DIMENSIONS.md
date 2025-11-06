# Process vs Data Dimensions: Why Processes Don't Have Indices

**Date**: 2025-10-27  
**Question**: Why can we add Indices to Stocks/Flows but not to Processes?

---

## The Fundamental Difference

### **Processes = NETWORK NODES**
- Processes define **locations/activities** in the system
- They have **NO DATA** (no Values array)
- They are **identifiers** only (Name, ID)

### **Stocks & Flows = DATA STRUCTURES**
- Stocks and Flows contain **dimensional data**
- They have **Values arrays** with multiple dimensions
- They need **Indices** to define dimension structure

---

## ODYM Class Structure Comparison

### Process Class (NO Indices, NO Values)

```python
class Process(Obj):
    """A process is a LOCATION in the system"""
    
    def __init__(self, Name=None, ID=None, UUID=None, ...):
        self.Name = Name           # ✅ Identifier
        self.ID = ID               # ✅ Identifier
        self.Extensions = Extensions
        # ❌ NO Indices attribute
        # ❌ NO Values attribute
```

**Why?** A Process is just a **label**, not data.

### Flow Class (HAS Indices, HAS Values)

```python
class Flow(Obj):
    """A flow contains DATA moving between processes"""
    
    def __init__(self, Name=None, P_Start=None, P_End=None, ...):
        self.P_Start = P_Start     # ⬅️ Links to Process (node)
        self.P_End = P_End         # ⬅️ Links to Process (node)
        self.Indices = Indices      # ✅ Defines dimensions!
        self.Values = Values        # ✅ The actual data!
```

**Why?** Flows contain **dimensional data**.

### Stock Class (HAS Indices, HAS Values)

```python
class Stock(Obj):
    """A stock contains DATA at a process"""
    
    def __init__(self, Name=None, P_Res=None, ...):
        self.P_Res = P_Res          # ⬅️ Links to Process (node)
        self.Indices = Indices       # ✅ Defines dimensions!
        self.Values = Values         # ✅ The actual data!
```

**Why?** Stocks contain **dimensional data**.

---

## Understanding Network Structure

### The MFA Graph

```
Process (Node)          Flow (Edge with Data)         Process (Node)
  ↓                                                            ↓
  ↓         Values array shape: (26, 4, 3)                     ↓
[Harvest]  ─────────────────────────────────────────→  [Processing]
  Name="Harvest"  Indices="t,e,r"                     Name="Processing"
  ID=1             Values[t, e, r]                     ID=2
                                      ↓
                                      Biomass flow
                                   across 26 years,
                                   4 elements,
                                   3 regions
```

**Key Understanding**:
- **Processes** are just nodes (circles in the diagram)
- **Flows** are edges that **contain the dimensional data**
- The **Indices** define the **data dimensions** (Time, Element, Region)

---

## Adding "Region" to Your System

### Option 1: Multiple Processes (One Per Region)

Create a separate process for each region:

```python
# Region A
Process(Name="Harvest_RegionA", ID=1)

# Region B
Process(Name="Harvest_RegionB", ID=2)

# Region C
Process(Name="Harvest_RegionC", ID=3)
```

**Flows**: Each flow has `Indices="t,e"` (no regional dimension needed because each process is already regional)

**Pros**:
- ✅ Simple structure
- ✅ Clear separation by region
- ✅ Easy to understand

**Cons**:
- ❌ Must create duplicate processes for each region
- ❌ Can't aggregate across regions easily

---

### Option 2: Single Process with Regional Flows (RECOMMENDED)

Keep ONE process, but add regional dimensions to **flows and stocks**:

```python
# ONE process
Process(Name="Harvest", ID=1)

# Flow WITH regional dimension
Flow(Name="F_001", P_Start=1, P_End=2, Indices="t,e,r")
# Values shape: (26, 4, 3) = 26 years × 4 elements × 3 regions

# Stock WITH regional dimension
Stock(Name="S_1", P_Res=1, Type=0, Indices="t,e,r")
# Values shape: (26, 4, 3) = 26 years × 4 elements × 3 regions
```

**How It Works**:
- The **Process** is regional (single node)
- The **Flows** have regional data in their Values arrays
- Access regional data: `flow.Values[:, :, region_index]`

**Pros**:
- ✅ Cleaner structure (one process, not duplicates)
- ✅ Easy to aggregate across regions
- ✅ Single point of control

**Cons**:
- ⚠️ Requires IndexTable to include "Region" dimension

---

## BioDYM's Current Setup

### Current Structure (2D)

```python
# Process
Process(Name="Harvest", ID=1)  # NO regional dimension

# Flow
Flow(Name="F_001", Indices="t,e")  # 2D: (26, 4)
Flow.Values.shape = (26, 4)  # 26 years × 4 elements

# Stock
Stock(Name="S_1", Indices="t,e")  # 2D: (26, 4)
Stock.Values.shape = (26, 4)  # 26 years × 4 elements
```

---

### Adding Regional Dimension (Future)

```python
# Process (STILL no regional dimension - it's just a node)
Process(Name="Harvest", ID=1)

# Flow (ADD regional dimension to Indices)
Flow(Name="F_001", Indices="t,e,r")  # 3D: (26, 4, 3)
Flow.Values.shape = (26, 4, 3)  # 26 years × 4 elements × 3 regions

# Stock (ADD regional dimension to Indices)
Stock(Name="S_1", Indices="t,e,r")  # 3D: (26, 4, 3)
Stock.Values.shape = (26, 4, 3)  # 26 years × 4 elements × 3 regions
```

**Key**: The Process stays the same! Only the **data structures** (Flows/Stocks) get regional dimensions.

---

## Why This Architecture?

### Processes are "Pure"
- Processes are **locations** in the network
- They don't contain dimensional data
- They're just identifiers

### Data Lives in Flows/Stocks
- Flows carry material between processes
- Stocks hold material at processes
- **Both** can have multi-dimensional data

### Separation of Concerns
```
Process = WHERE (location in network)
Flow/Stock = WHAT (dimensional data)
Indices = HOW MANY DIMENSIONS (t, e, r, g, m, p)
```

---

## Example: Regional Harvest Data

### Current (2D System)

```python
# Process 1
Process(Name="Harvest", ID=1)

# Flow from Process 1 to Process 2
Flow(Name="F_001", P_Start=1, P_End=2, Indices="t,e")
Flow.Values.shape = (26, 4)  # 26 years × 4 elements
Flow.Values[0, 0] = 100  # Year 2020, element 'material' = 100 Mg

# Access: Flow.Values[year_idx, element_idx]
```

**Limitation**: Can't store different harvest amounts for different regions.

---

### With Regional Dimension (3D System)

```python
# Process 1 (still the same!)
Process(Name="Harvest", ID=1)

# Flow from Process 1 to Process 2
Flow(Name="F_001", P_Start=1, P_End=2, Indices="t,e,r")
Flow.Values.shape = (26, 4, 3)  # 26 years × 4 elements × 3 regions
Flow.Values[0, 0, 0] = 100  # Year 2020, element 'material', Region A = 100 Mg
Flow.Values[0, 0, 1] = 150  # Year 2020, element 'material', Region B = 150 Mg
Flow.Values[0, 0, 2] = 80   # Year 2020, element 'material', Region C = 80 Mg

# Access: Flow.Values[year_idx, element_idx, region_idx]
```

**Benefit**: Can store harvest amounts for multiple regions in one flow.

---

## How to Add Regional Data

### Step 1: Update IndexTable

```python
# Add Region to IndexTable
mfa_system.IndexTable.loc["Region"] = {
    "IndexLetter": "r",
    "ClassificationName": "Region",
    "FullName": "Region"
}

# Add Region classification
mfa_system.IndexTable.Classification['Region'] = msc.Classification(
    Name="Region",
    Items=['Region_A', 'Region_B', 'Region_C']
)
```

### Step 2: Update Flow Indices

```python
# BEFORE: 2D
Flow(Name="F_001", Indices="t,e")  # (26, 4)

# AFTER: 3D with region
Flow(Name="F_001", Indices="t,e,r")  # (26, 4, 3)
```

### Step 3: Update Stock Indices

```python
# BEFORE: 2D
Stock(Name="S_1", Indices="t,e")  # (26, 4)

# AFTER: 3D with region
Stock(Name="S_1", Indices="t,e,r")  # (26, 4, 3)
```

**Important**: The Process doesn't change! Still:
```python
Process(Name="Harvest", ID=1)  # No Indices!
```

---

## Answer to Your Question

### **"Why can't we add Indices to Processes?"**

**Short Answer**: Processes don't have data, so they don't need Indices.

**Detailed Answer**:
- Processes are **network nodes** (identifiers)
- Flows/Stocks are **data structures** (with Values arrays)
- Only data structures need Indices to define their dimensions

---

### **"Can I add a region to a process?"**

**Short Answer**: Yes, by adding regional dimensions to **Flows and Stocks**, not to the Process itself.

**How**:
1. Add "Region" to IndexTable
2. Update Flow.Indices: `"t,e"` → `"t,e,r"`
3. Update Stock.Indices: `"t,e"` → `"t,e,r"`
4. Process stays the same (no Indices needed)

**Result**: The process can now handle regional data through its flows and stocks!

---

## Summary

| Object | Has Indices? | Has Values? | Contains Data? | Regional Data? |
|--------|-------------|-------------|---------------|---------------|
| **Process** | ❌ NO | ❌ NO | ❌ NO | Store in flows/stocks |
| **Flow** | ✅ YES | ✅ YES | ✅ YES | Add `Indices="t,e,r"` |
| **Stock** | ✅ YES | ✅ YES | ✅ YES | Add `Indices="t,e,r"` |

**Key Insight**: The Process is just a location. Regional data lives in the Flows and Stocks connected to that Process.





