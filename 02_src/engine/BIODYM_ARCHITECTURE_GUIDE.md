# BioDYM Architecture Guide: Framework Integration

**Question**: Should we modify files in `06_framework/` or keep everything in `02_src/`?

**Answer**: ✅ **Keep ODYM framework untouched, modify BioDYM code in `02_src/`**

---

## Current Architecture

```
bioDYM-CERT-edit-main/
├── 02_src/                          ✅ BioDYM Application Code
│   ├── engine/                      ✅ Engine modules (solver, DSM, FOMP, etc.)
│   ├── plotting/                    ✅ BioDYM plotting functions
│   ├── config.py                    ✅ Configuration loader
│   ├── data_loader.py              ✅ Excel data loader
│   ├── system_setup.py             ✅ System initialization
│   └── utils.py                     ✅ Utilities
│
└── 06_framework/                    ⚠️ External Frameworks (READ-ONLY)
    ├── ODYM-master_20241127/       ⚠️ ODYM Framework (don't modify)
    │   └── odym/modules/
    │       ├── ODYM_Classes.py     ⚠️ Core ODYM classes
    │       ├── ODYM_Functions.py   ⚠️ Core ODYM functions
    │       └── dynamic_stock_model.py ⚠️ DSM functions
    │
    └── bioDYM_add-on/               ✅ BioDYM Extensions (custom classes)
        └── modules/
            ├── bioDYM_classes.py    (FOMP Parameter class)
            ├── bioDYM_plotting.py   (not currently used)
            └── bioDYM_export.py     (not currently used)
```

---

## Import Strategy

### How BioDYM Imports ODYM

**In `02_src/system_setup.py` (line 16-26)**:
```python
# Add ODYM framework to path
odym_path = os.path.join(
    project_root, "06_framework", "ODYM-master_20241127", "odym", "modules"
)
sys.path.insert(0, odym_path)

# Import ODYM classes
import ODYM_Classes as msc
```

**In BioDYM code**:
```python
# Use ODYM classes
flow = msc.Flow(Name="F1", P_Start=1, P_End=2, Indices="t,e")
stock = msc.Stock(Name="S1", P_Res=1, Type=0, Indices="t,e")
mfa_system = msc.MFAsystem(...)
```

---

## ODYM Framework Status

### ✅ ODYM (In `06_framework/ODYM-master_20241127/`)

**Status**: **READ-ONLY** - Framework code, do not modify

**What ODYM Provides**:
- `MFAsystem` class with methods:
  - `Initialize_FlowValues()`
  - `Initialize_StockValues()`
  - `Initialize_ParameterValues()`
  - `Consistency_Check()`
  - `IndexTableCheck()`
- `Flow`, `Stock`, `Parameter`, `Process`, `Classification` classes
- Dynamic Stock Model (DSM) functions

**Why Don't We Modify It?**
1. It's a separate framework - keeps BioDYM updates independent from ODYM updates
2. ODYM can be updated from its GitHub repository
3. Maintains clear separation between framework and application

---

## BioDYM Application Code Status

### ✅ BioDYM Engine (In `02_src/engine/`)

**Status**: **READ/WRITE** - Our application code, modify freely

**What We Modify**:
- `solver.py` - Main MFA solver
- `dsm_model.py` - Dynamic Stock Model calculations
- `fomp_model.py` - First-Order Mass Pool calculations
- `initial_stock_engine.py` - Initial stock processing
- `scenario_engine.py` - Scenario analysis
- `mc_simulation.py` - Monte Carlo simulation

**How We Use ODYM**:
- Create `MFAsystem` objects using ODYM classes
- Call ODYM methods (Initialize, Consistency_Check, etc.)
- **Never** modify ODYM's internal code

---

## BioDYM Add-On Status

### ⚠️ BioDYM Add-On (In `06_framework/bioDYM_add-on/`)

**Status**: **Minimal usage** - Contains `fompParameter` class for FOMP

**Current Usage**:
- `bioDYM_classes.py` - Defines `fompParameter` class (FOMP-specific)
- `bioDYM_plotting.py` - Not currently used in main workflow
- `bioDYM_export.py` - Not currently used in main workflow

**Note**: Most BioDYM-specific extensions are in `02_src/engine/` rather than in the add-on folder.

---

## Best Practices

### ✅ DO

1. **Modify BioDYM code in `02_src/`**
   - Engine modules (`02_src/engine/`)
   - Plotting (`02_src/plotting/`)
   - Configuration (`02_src/config.py`, `02_src/data_loader.py`)

2. **Use ODYM classes and methods**
   - Import: `import ODYM_Classes as msc`
   - Call methods: `mfa_system.Initialize_FlowValues()`
   - Create objects: `msc.Flow(...)`, `msc.Stock(...)`

3. **Keep ODYM framework untouched**
   - Read ODYM code for reference
   - Don't modify ODYM files
   - Update ODYM by pulling from GitHub

### ❌ DON'T

1. **Modify files in `06_framework/ODYM-master_20241127/`**
   - These are framework files
   - Should be kept in sync with ODYM GitHub repository

2. **Add custom attributes to ODYM objects**
   - Use external dictionaries instead
   - Example: Don't do `flow.DescriptiveName` (custom attribute)
   - Instead: `flow_descriptions[flow_id] = name` (external dict)

3. **Call ODYM classes "our engine"**
   - ODYM = Framework (external)
   - BioDYM Engine = Our code in `02_src/engine/`

---

## Current Phase 1a Implementation

### What We Modified for ODYM Compliance

**Files Changed**:
- ✅ `02_src/engine/initial_stock_engine.py`
- ✅ `02_src/system_setup.py`

**What We Did**:
- Replaced manual `np.zeros()` with ODYM's `Initialize_FlowValues()`
- Replaced manual stock initialization with `Initialize_StockValues()`
- Added `Initialize_ParameterValues()` call
- Added `IndexTableCheck()` validation

**Where We DIDN'T Modify**:
- ❌ `06_framework/ODYM-master_20241127/` (kept untouched)
- ✅ All changes in `02_src/` (our application code)

---

## Relationship Diagram

```
┌─────────────────────────────────────────────────────────┐
│                       BioDYM Application                  │
│                    (02_src/ - MODIFY HERE)                │
├───────────────────────────────────────────────────────────┤
│  system_setup.py  →  Creates MFAsystem                    │
│       ↓                                                   │
│  Uses ODYM classes: msc.Flow, msc.Stock, msc.MFAsystem   │
│       ↓                                                   │
│  Calls ODYM methods: Initialize_FlowValues()            │
└──────────────┬───────────────────────────────────────────┘
               │ Imports
               │
┌──────────────▼───────────────────────────────────────────┐
│                    ODYM Framework                        │
│         (06_framework/ - READ-ONLY)                       │
├───────────────────────────────────────────────────────────┤
│  ODYM_Classes.py  →  Core classes                       │
│  ODYM_Functions.py →  Helper functions                   │
│  dynamic_stock_model.py → DSM functions                 │
└───────────────────────────────────────────────────────────┘
```

---

## Summary

**Your Question**: "Should we interact here with the Framework folder?"

**Answer**: 
- ✅ **We USE the framework**, not modify it
- ✅ **We modify BioDYM application code** in `02_src/`
- ✅ **We call ODYM methods** like `Initialize_FlowValues()`
- ❌ **We don't modify ODYM's core code**

**Current Status**: Phase 1a changes are correctly placed in `02_src/` and use ODYM's methods without modifying the framework itself.

