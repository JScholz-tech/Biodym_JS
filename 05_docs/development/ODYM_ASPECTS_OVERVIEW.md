# ODYM Aspects in BioDYM - Complete Overview

**Last Updated**: 2025-11-06
**Your Branch**: feature/odym-compliance
**ODYM Reference**: https://github.com/IndEcol/ODYM/tree/master

## Currently Active Aspects (Dimensions)

### 1. Time Aspect (t)
- **Letter Code**: `t`
- **Purpose**: Temporal dimension for the analysis period
- **Classification**: Years from start_year to end_year
- **Example Usage**: `Indices="t,e"` for time-varying, element-specific flows
- **Your Setup**: Typically 2025-2050 (26 years)

### 2. Element Aspect (e)
- **Letter Code**: `e`
- **Purpose**: Track multiple material composition elements simultaneously
- **Classification**: `['material', 'WC', 'DM', 'CC']`
  - **material**: Total material mass
  - **WC**: Water Content
  - **DM**: Dry Matter
  - **CC**: Carbon Content
- **Example Usage**: `Indices="t,e"` creates shape (26, 4) array
- **Your Innovation**: Element-agnostic - can be reconfigured for metals, food, etc.

## Planned/Optional Aspects (Phase 1b - Not Yet Active)

### 3. Material Aspect (m)
- **Letter Code**: `m`
- **Status**: Code present but NOT actively used
- **Purpose**: Material categories (e.g., wood, straw, plastic)
- **Note**: Currently handled differently - not needed for your current studies
- **Code Location**: system_setup.py:86-94

### 4. Region Aspect (r)
- **Letter Code**: `r`
- **Status**: Available but defaults to single region
- **Classification**: `["Case_Study_Region"]` (default)
- **Purpose**: Spatial differentiation for multi-region studies
- **Usage**: Could be activated via Excel config for multi-regional MFA

### 5. Good Aspect (g)
- **Letter Code**: `g`
- **Status**: Available but not yet used
- **Purpose**: Product/good categories
- **Future Use**: For product-level tracking

### 6. Process Aspect (p)
- **Letter Code**: `p`
- **Status**: Available but not yet used
- **Purpose**: Process type classification
- **Note**: Your processes are tracked via Process IDs, not as a dimension

## Standard ODYM Aspects (from IndEcol/ODYM)

According to the ODYM framework, standard aspects include:
- **t**: Time
- **e**: Element/chemical element
- **m**: Material
- **g**: Good
- **r**: Region
- **p**: Process
- **c**: Cohort (for age-cohort tracking in DSM)
- **w**: Waste/Scrap type
- **o**: Origin
- **d**: Destination

## Your Current IndexTable Structure

```python
# From system_setup.py:96-107
index_table = pd.DataFrame({
    "Aspect": ["Time", "Element"],
    "Description": ['Model aspect "time"', 'Model aspect "Element"'],
    "Dimension": ["Time", "Element"],
    "Classification": [
        msc.Classification(Name="Time", Dimension="Time", ID=1, Items=[2025...2050]),
        msc.Classification(Name="Elements", Dimension="Element", ID=2, Items=['material', 'WC', 'DM', 'CC'])
    ],
    "IndexLetter": ["t", "e"]
})
```

## How Indices are Used in Your Code

### Flows and Stocks

```python
# From system_setup.py:343
# All flows use "t,e" (time × element)
flow_obj = msc.Flow(
    Name="F_01_02",
    P_Start=1,
    P_End=2,
    Indices="t,e"  # Creates array of shape (26, 4)
)

# From system_setup.py:219, 222
# All stocks use "t,e"
stock_change = msc.Stock(Name="dS_1", P_Res=1, Type=1, Indices="t,e")
stock_level = msc.Stock(Name="S_1", P_Res=1, Type=0, Indices="t,e")
```

### Parameters

**Time-varying, element-specific**:
```python
# Transfer coefficients that vary over time and by element
tc_param = msc.Parameter(
    Name="TC_1_2_3",
    Indices="t,e",  # Shape (26, 4)
    Values=np.array([...])
)
```

**Scalar parameters**:
```python
# From system_setup.py:442
# Single value parameters (e.g., lifetimes, decay rates)
lifetime_param = msc.Parameter(
    Name="lifetime",
    Indices="",  # CRITICAL: Empty string, not None!
    Values=10.0
)
```

## Data Structure Shapes

When you define `Indices="t,e"` with:
- Time: 2025-2050 (26 years)
- Elements: ['material', 'WC', 'DM', 'CC'] (4 elements)

**Result**: NumPy array of shape `(26, 4)`

```
Year    material    WC      DM      CC
2025    100.0      80.0    20.0    9.0
2026    105.0      82.0    23.0    10.35
2027    110.0      84.0    26.0    11.7
...
2050    250.0      180.0   70.0    31.5
```

## BioDYM's Aspect Strategy

Your study uses a **minimalist approach**:

1. **Active Dimensions**: Only `t` and `e` (Time × Element)
2. **Rationale**: Sufficient for single-region, single-material-category studies
3. **Flexibility**: Element aspect is generic - works for biomass, metals, food, nutrients
4. **Scalability**: Additional aspects available when needed for complex studies
5. **Performance**: Simpler structure = faster computation and easier debugging

## Comparison to Standard ODYM Usage

| Model Type | Typical Aspects | Dimensionality |
|------------|----------------|----------------|
| **Standard ODYM** (complex) | t, r, g, m, e | 5D |
| **Your BioDYM** (current) | t, e | 2D |
| **BioDYM Extended** (future) | t, r, g, e | 4D |

**Advantages of your approach**:
- ✅ Simpler code and data structures
- ✅ Faster computation
- ✅ Sufficient for case study research
- ✅ Easier to debug and validate

**Trade-off**:
- ⚠️ Less granular than full multi-regional, multi-product MFA
- ✅ But can be extended when needed!

## When You'd Need More Aspects

### Region (r)
**Use case**: Multi-country biomass flow study
```python
regions = ["Germany", "France", "Poland"]
# Indices="t,r,e" → shape (26, 3, 4) = 312 values per flow
```

### Good (g)
**Use case**: Different product categories
```python
goods = ["Food", "Feed", "Energy", "Material"]
# Indices="t,g,e" → shape (26, 4, 4) = 416 values per flow
```

### Material (m)
**Use case**: Multiple feedstocks tracked separately
```python
materials = ["Wheat_Straw", "Corn_Stover", "Wood_Residues"]
# Indices="t,m,e" → shape (26, 3, 4) = 312 values per flow
```

### Cohort (c)
**Use case**: Age-cohort tracking
- **Note**: ODYM's DSM already handles this internally
- You don't need to explicitly define it in your IndexTable
- DSM creates cohort dimension automatically when needed

## Real Example: Why Element-Specific Matters

```python
# Transfer coefficient for a drying process
TC_drying = {
    'material': 0.95,  # 5% material loss
    'WC': 0.30,        # 70% water removed!
    'DM': 1.00,        # Dry matter conserved
    'CC': 1.00         # Carbon follows dry matter
}

# Result after drying 100 Mg material with 80% WC:
# Input:  material=100, WC=80, DM=20, CC=9
# Output: material=95,  WC=24, DM=20, CC=9
```

This shows why tracking elements separately is crucial for biomass MFA!

## Code References

Key locations in your codebase:

- **Aspect definition**: `02_src/system_setup.py:66-107` (define_model_scope)
- **Flow creation**: `02_src/system_setup.py:343` (load_flows_and_stocks)
- **Stock creation**: `02_src/system_setup.py:219, 222` (load_processes)
- **Parameter creation**: `02_src/system_setup.py:437-442` (load_transfer_coefficients)
- **Usage in solver**: `02_src/engine/solver.py` (entire file)

## Summary

### ✅ What You're Using (Actively)

| Aspect | Letter | Usage | Array Dimension | Purpose |
|--------|--------|-------|----------------|---------|
| Time | `t` | Years 2025-2050 | 26 | Temporal evolution |
| Element | `e` | material/WC/DM/CC | 4 | Composition tracking |

**Total dimensionality**: 2D (26 × 4 = 104 values per flow/stock)

### 📋 What's Available (But Not Used Yet)

| Aspect | Letter | Status | When You'd Need It |
|--------|--------|--------|-------------------|
| Region | `r` | Optional, defaults to 1 | Multi-country studies |
| Good | `g` | Planned | Product categories |
| Material | `m` | Planned | Multiple feedstocks |
| Process | `p` | Planned | Process type classification |
| Cohort | `c` | ODYM DSM internal | Age tracking (automatic) |

## Key Takeaways

1. **You use a 2-aspect system** (Time, Element) - simpler than standard ODYM
2. **Your innovation**: Element aspect is flexible and works for any element set
3. **All flows/stocks have shape (26, 4)** when `Indices="t,e"`
4. **Scalar parameters use `Indices=""`** (critical for ODYM compliance!)
5. **Your approach is optimal** for single-region biomass case studies
6. **It's easily extendable** - add aspects when your research scope expands

## For Further Reference

**ODYM GitHub**: https://github.com/IndEcol/ODYM/tree/master

Key ODYM files to understand aspects:
- `/odym/modules/ODYM_Classes.py` - Class definitions
- `/docs/` - Official documentation on dimensions
- `/examples/` - Examples showing multi-aspect usage

**Your documentation**:
- `CLAUDE.md` - Complete BioDYM development guide
- `TECHNICAL_DEEP_DIVE.md` - Detailed calculation engine documentation
- `ODYM_COMPLIANCE_CONSOLIDATED.md` - ODYM compliance checklist

---

**Status**: Your BioDYM is fully ODYM-compliant and uses an optimal subset of aspects for your research scope.
