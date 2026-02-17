# BioDYM N-Dimensional Integration Roadmap

**Created**: 2025-11-06
**Updated**: 2026-02-11
**Current Status**: BioDYM uses 2D (Time x Element)
**Strategy**: Dimension-agnostic engine, then activate dimensions per use case

---

## Strategy

**Old approach** (abandoned): Add dimensions one by one (Region, then Good, then Material...), refactoring the solver each time.

**New approach**: Refactor the solver ONCE to handle ANY number of dimensions, then activate only the dimensions each use case needs. This means:

1. The solver doesn't care whether a flow has shape `(26, 4)` or `(26, 8, 6, 4)` — it operates on the last N dimensions generically.
2. Existing 2D case studies (`t,e`) continue to work unchanged.
3. New use cases activate additional dimensions via configuration, not code changes.
4. ODYM already supports this natively (einsum-based mass balance, dynamic `Initialize_FlowValues`).

### Use Cases Driving Dimension Needs

| Use Case | Dimensions | Indices | Example Shape |
|---|---|---|---|
| **Biomass MFA** (current) | Time, Element | `t,e` | `(26, 4)` |
| **Multi-regional biomass** | Time, Region, Element | `t,r,e` | `(26, 3, 4)` |
| **Waste sorting plant** | Time, Good, Size | `t,g,s` | `(1, 15, 6)` |
| **Sorting + elements** | Time, Good, Size, Element | `t,g,s,e` | `(1, 15, 6, 4)` |
| **Multi-regional sorting** | Time, Region, Good, Size | `t,r,g,s` | `(4, 3, 15, 6)` |

Each use case picks its own dimensions — the engine handles all of them.

---

## Phase 1: Dimension-Agnostic Engine (~7-10 days)

**Goal**: Refactor the solver and supporting code to work with arbitrary dimensions. Verify by running existing 2D case studies and confirming identical results.

### 1.1 Solver Refactoring

**File**: `02_src/engine/solver.py`

The core change: replace hardcoded 2D indexing with dimension-aware operations.

**Current** (hardcoded 2D):
```python
# Material is always index 0 of last dimension
total_inflow = sum(f.Values for f in inflows)        # Shape (T, E)
outflow_material = total_inflow[:, 0] * tc_value      # Scalar indexing
outflow_element = total_inflow[:, e] * tc_value_e      # Loop over elements
```

**New** (dimension-agnostic):
```python
# Operate on the last dimension (always "element" or equivalent)
# Or use named dimension lookup from IndexTable
total_inflow = sum(f.Values for f in inflows)          # Shape (T, ..., E)
# TC applied via broadcasting — works for any number of leading dimensions
outflow = total_inflow * tc_array                       # Broadcasting handles shape
```

**Key patterns for N-dimensional operations**:
- `flow.Values[..., 0]` — material (last dim, first entry) regardless of shape
- `flow.Values[..., elem_idx]` — any element, any number of leading dims
- `np.sum(flow.Values, axis=tuple(range(1, ndim-1)))` — aggregate middle dims
- `np.einsum` — ODYM's mass balance already uses this

**Estimated changes**: ~50 locations in `solver.py`, mostly `[:, X]` → `[..., X]`

### 1.2 System Setup Generalization

**File**: `02_src/system_setup.py`

```python
def define_model_scope(start_year, end_year, elements,
                       regions=None, goods=None, sizes=None, materials=None):
    """Build IndexTable from whatever dimensions are provided."""
    aspects = ["Time"]
    index_letters = ["t"]

    # Add optional dimensions in standard order
    if regions is not None:
        aspects.append("Region"); index_letters.append("r")
    if goods is not None:
        aspects.append("Good"); index_letters.append("g")
    if sizes is not None:
        aspects.append("Size"); index_letters.append("s")
    if materials is not None:
        aspects.append("Material"); index_letters.append("m")

    # Element always last (convention)
    aspects.append("Element"); index_letters.append("e")

    # Build Indices string for flows
    indices = ",".join(index_letters)  # e.g., "t,g,s,e"
```

Flow and stock `Indices` strings are built dynamically. `Initialize_FlowValues()` creates the right shape automatically.

### 1.3 Data Loader Generalization

**File**: `02_src/data_loader.py`

**Approach**: Detect available columns in Excel and map to dimensions.

```python
def load_flow_data(df, index_table):
    """Load flow data, auto-detecting which dimensions are present."""
    dimension_columns = {
        'Region': 'r', 'Good': 'g', 'Size': 's', 'Material': 'm'
    }
    # Detect which dimension columns exist in the Excel data
    present_dims = [col for col in dimension_columns if col in df.columns]
    # Pivot into N-dimensional array based on what's present
```

**Backward compatibility**: If no Region/Good/Size columns exist in Excel, falls back to 2D loading.

### 1.4 TC Application Generalization

**Current**: TCs are scalars or 1D arrays (time-varying).
**New**: TCs can be N-dimensional arrays matching flow dimensions.

```python
# TC broadcasting rules:
# - Scalar TC: applies uniformly to all dimensions
# - 1D TC (time): broadcast across other dimensions
# - 2D TC (good x size): broadcast across time
# - Full TC: matches flow dimensions exactly

def apply_tc(inflow_values, tc_values):
    """Apply TC with automatic broadcasting."""
    return inflow_values * tc_values  # NumPy broadcasting handles shape mismatch
```

### 1.5 DSM / FOMP Adaptation

**DSM** (`dsm_model.py`): Operates on the "material" slice (first entry of last dimension). For extra dimensions, loop over them or vectorize:

```python
# DSM works on material mass — extra dimensions are independent
# If flow shape is (T, G, S, E), DSM operates on (T,) per (g, s) combination
for idx in np.ndindex(flow.Values.shape[1:-1]):  # Loop over middle dims
    material_inflow = flow.Values[(slice(None),) + idx + (0,)]  # (T,)
    # Run DSM on this 1D time series
    stock_result = run_dsm_1d(material_inflow, params)
```

**FOMP** (`fomp_model.py`): Same pattern — FOMP operates per-element, loop over extra dimensions.

**Note**: DSM and FOMP are unlikely to be used in sorting plant models (no long-term stock accumulation, no biological decay). They stay functional for biomass/construction use cases.

### 1.6 Plotting Adaptation

**Strategy**: Add dimension selectors (dropdowns) to interactive plots. Aggregate or slice along extra dimensions.

```python
def get_plot_data(flow_values, index_table, selections):
    """Reduce N-dimensional flow to 2D (time x selected_dim) for plotting."""
    # Sum/slice along all dimensions except time and the selected one
    # Returns a 2D array suitable for existing plot functions
```

Most existing plot functions receive 2D data — the adapter layer handles dimensionality.

### 1.7 Verification

- Run ALL existing 2D test cases — must produce identical results
- Run existing biomass and wood case studies — results must match bit-for-bit
- Create a simple 3D test case: single region (should equal 2D)
- Mass balance check via ODYM's `MassBalance()` (einsum, works with any dims)

---

## Phase 2: Biomass Multi-Regional (~1-2 weeks, optional)

**Goal**: Add Region dimension to existing biomass case studies.

**Activate**: `regions = ["Germany", "Austria"]` in workflow configuration.

| Task | Effort |
|---|---|
| Add Region column to Excel input sheets | 1 day |
| Configure multi-regional case study | 1 day |
| Add region selector to plots | 1-2 days |
| Test mass balance per region | 0.5 day |
| Cross-regional flows (trade) | 2-3 days (if needed) |

**Note**: This phase is optional and independent of the sorting extension. It can be done before, after, or in parallel with Phase 3.

---

## Phase 3: Waste Sorting Plant Extension (~2-3 weeks)

**Goal**: Model mechanical waste sorting plants using the N-dimensional engine.

**Activate**: `goods = ["PET", "PE", "PP", ...]` and `sizes = ["<20mm", "20-50mm", ...]`

### 3.1 Configuration & Data Loading (3-4 days)

| Task | Effort |
|---|---|
| New Excel sheets: material types, size classes, material properties | 1 day |
| Input flow composition as `(good x size)` matrix | 1 day |
| Separation parameters per process (mesh sizes, detection rates, cut densities) | 1 day |
| Material property database (density, magnetism, NIR signature per material type) | 0.5 day |

### 3.2 Separation Process Engines (5-8 days)

Each engine generates TC matrices `(good x size)` from physical parameters:

| Engine | File | Effort | Generates TCs From |
|---|---|---|---|
| **Tromp/partition curve** (screens, density) | `tromp_model.py` | 2 days | Mesh size / cut density + curve sharpness |
| **NIR/optical sorting** | `nir_model.py` | 2 days | Detection rate per (material, size) + ejection efficiency |
| **Magnetic/eddy current** | Reuse Transformer | 0.5 day | Binary material property (magnetic/conductive) |
| **Comminution** (WEEE/C&D only) | `comminution_model.py` | 2-3 days | Liberation matrix, target size distribution |

These engines are called BEFORE the solver runs — they populate TC matrices that the generic solver then applies.

### 3.3 KPI Module (1-2 days)

| KPI | Formula |
|---|---|
| **Grade** (purity) | `target_material_in_stream / total_mass_in_stream` |
| **Recovery** | `target_material_in_stream / target_material_in_input` |
| **Yield** | `total_mass_in_stream / total_mass_in_input` |
| **Contamination rate** | `non_target_material / total_mass_in_stream` |

### 3.4 Sorting-Specific Plots (2-3 days)

- Stacked bar: output stream composition by material type
- Sankey: material flows through sorting cascade, colored by material type
- Grade vs. Recovery scatter for each output stream
- Tromp/partition curves for each separation step

### 3.5 Validation

- Mass balance across all material types and size classes
- Compare against literature data or real plant mass balances
- Sensitivity analysis: how do TC uncertainties propagate?

---

## Phase 4: Advanced Features (optional, 1-2 weeks each)

### 4.1 MC Simulation for Sorting
- Sample input composition from distributions
- Sample separation parameters (detection rates, curve sharpness)
- Propagate uncertainty through sorting cascade
- **Effort**: ~3 days (MC framework already exists, just needs N-dim compatibility)

### 4.2 Scenario Engine for Plant Optimization
- Add/remove/reorder sorting stages
- Change operating parameters (mesh size, belt speed)
- Compare plant configurations
- **Effort**: ~2 days (scenario engine already exists)

### 4.3 ABM Input Generator (Option C)
- Particle simulation to derive TC matrices from physical models
- Calibrate once, run MFA many times
- **Effort**: ~5-8 days

### 4.4 Economic Layer
- Cost per process (energy, labor, maintenance)
- Revenue per output stream (market prices)
- Optimize for profit, not just recovery
- **Effort**: ~3-5 days

### 4.5 Time-Dynamic Sorting (Seasonal Variability)
- Input composition changes over time (seasons, holidays)
- Run sorting plant model per timestep
- **Effort**: ~2 days (engine already supports time dimension)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Excel Configuration                   │
│  Material types, Size classes, Process parameters, TCs   │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│               System Setup (N-dimensional)               │
│  IndexTable: t, [r], [g], [s], [m], e                   │
│  Flows: shape determined by active dimensions            │
│  Stocks: same                                            │
└────────────────────────┬────────────────────────────────┘
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
   ┌─────────────┐ ┌──────────┐ ┌────────────┐
   │ Separation  │ │   DSM    │ │    FOMP    │
   │  Engines    │ │  Engine  │ │   Engine   │
   │ (Tromp,NIR) │ │ (cohort) │ │ (2-pool)   │
   │ → TC matrix │ │          │ │            │
   └──────┬──────┘ └────┬─────┘ └─────┬──────┘
          │              │              │
          ▼              ▼              ▼
┌─────────────────────────────────────────────────────────┐
│            Solver (dimension-agnostic)                    │
│  Iterative convergence, TC application via broadcasting   │
│  Works with (t,e), (t,g,s), (t,r,g,s,e), ...           │
└────────────────────────┬────────────────────────────────┘
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
   ┌─────────────┐ ┌──────────┐ ┌────────────┐
   │   Plotting  │ │    MC    │ │  Scenario  │
   │ (dim-aware) │ │Simulation│ │   Engine   │
   └─────────────┘ └──────────┘ └────────────┘
```

---

## Effort Summary

| Phase | Description | Effort | Prerequisite |
|---|---|---|---|
| **1** | Dimension-agnostic engine | 7-10 days | None |
| **2** | Biomass multi-regional | 5-8 days | Phase 1 |
| **3** | Waste sorting plant | 12-18 days | Phase 1 |
| **4** | Advanced features | 2-8 days each | Phase 1 + relevant use case |

Phase 1 is the foundation. Phases 2 and 3 are independent of each other and can be done in any order. Phase 4 items are optional enhancements.

**Critical path to sorting plant**: Phase 1 (10 days) + Phase 3 (15 days) = ~5 weeks

---

## Key Design Decisions

### 1. Element Always Last
Convention: the element/composition dimension is always the last axis. This simplifies slicing (`[..., elem_idx]`) and is consistent with ODYM practice.

### 2. Dimensions Are Optional
Each use case activates only the dimensions it needs. No dummy dimensions with size 1 — if Region isn't needed, it simply isn't in the Indices string.

### 3. Backward Compatibility via Detection
If the Excel file has no Region/Good/Size columns, the system falls back to 2D mode. Existing case studies work without any changes.

### 4. TC Broadcasting
TCs can have fewer dimensions than flows. NumPy broadcasting handles the expansion automatically. A scalar TC applies to all dimensions; a time-varying TC broadcasts across spatial dimensions.

### 5. Separation Engines Generate TCs
Sorting-specific models (Tromp curves, NIR efficiency) don't replace the solver — they generate TC matrices that the generic solver applies. This keeps the solver simple and universal.

---

## Open Questions

1. **Element dimension in sorting**: Do sorting plants need "elements" (WC, DM, CC), or are material types (PET, PE, PP) sufficient? If both: `Indices = "t,g,s,e"` with Good = material type, Element = chemical composition.
2. **Cross-regional flows**: If Phase 2 is activated, can material flow between regions? This requires origin-destination flow tracking (`O,D` indices) which adds complexity.
3. **Sparse combinations**: Not all (Good x Size) combinations exist (e.g., glass is rarely <5mm in packaging). Should we use masked arrays or just accept zeros?
4. **Performance threshold**: At what array size does the solver become too slow? Need to profile with realistic sorting plant dimensions (~15 goods x 6 sizes = 90 cells per flow per timestep).

---

## References

- [SORTING_PLANT_EXTENSION_OVERVIEW.md](../SORTING_PLANT_EXTENSION_OVERVIEW.md) — Detailed sorting plant modeling design
- Pauliuk (2020): ODYM framework — supports arbitrary dimensions via einsum
- Tanguay-Rioux et al. (2022): Hybrid TC + mechanistic sorting models
- Kroell et al. (2024): Digital twins for waste sorting plants

---

**Document Status**: Updated strategy — dimension-agnostic engine first
**Last Updated**: 2026-02-11
