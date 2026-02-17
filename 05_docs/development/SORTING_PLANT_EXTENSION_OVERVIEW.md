# BioDYM Extension: General Waste Sorting Plant Modeling

## 1. Scope

This document outlines the design for extending BioDYM to model **any type of mechanical waste sorting plant**, including:

- **Packaging waste** (lightweight packaging / LVP): PET, PE, PP, PS, paper/cardboard, aluminium, tinplate, glass, composites (beverage cartons)
- **WEEE** (Waste Electrical and Electronic Equipment): PCBs, ferrous metals, copper, aluminium, precious metals (Au, Ag, Pd), plastics (ABS, HIPS, PP), glass, cables, batteries
- **Construction & Demolition waste** (C&D): Concrete, wood, metals, plastics, glass, aggregates, soil, gypsum
- **Mixed municipal solid waste** (MSW): Organics, paper, plastics, metals, glass, textiles, hazardous, residual
- **End-of-life vehicles** (ELV): Steel, aluminium, copper, plastics, rubber, glass, fluids

The model should be **waste-stream-agnostic**: the same engine handles any waste type by configuring different material types, physical properties, and separation technologies.

---

## 2. Material Types & Physical Properties

### 2.1 Material Types (Mass-Conserved, Tracked as ODYM Dimension)

Material types are the primary classification. They depend on the waste stream:

| Waste Stream | Example Material Types |
|---|---|
| Packaging | PET, PE-HD, PE-LD, PP, PS, EPS, PVC, Paper, Cardboard, Aluminium, Tinplate, Glass_clear, Glass_green, Glass_brown, Composites, Organics, Residual |
| WEEE | Steel, Stainless_Steel, Copper, Aluminium, Brass, PCB, ABS, HIPS, PP_WEEE, PVC_WEEE, Glass, Rubber, Ceramics, Battery_cells, Cables |
| C&D | Concrete, Brick, Wood, Steel_CD, Aluminium_CD, Plastic_CD, Glass_CD, Aggregates, Soil, Gypsum, Insulation |

These are configured per case study — the engine doesn't hardcode any.

### 2.2 Physical Properties (Drive Separation, Not Mass-Conserved)

Physical properties determine how materials behave in separation processes:

| Property | Unit | Relevance | Waste Streams |
|---|---|---|---|
| **Particle size** | mm (classes) | Screening, NIR detection, air classification | All |
| **Density** | kg/m3 | Sink-float, air classification, jigs | All |
| **Magnetic susceptibility** | Binary/ternary | Magnetic separator, eddy current | All with metals |
| **NIR signature** | Material class | NIR/optical sorting | Packaging, WEEE plastics |
| **Color** | Categories | VIS sorting | Glass, some plastics |
| **Conductivity** | Binary | Eddy current separator | All with metals |
| **Shape factor** | 2D/3D ratio | Ballistic separator, screening | Packaging, MSW |
| **Brittleness** | Index | Comminution behavior | WEEE, C&D |

### 2.3 Modeling Approach for Properties

**Particle size** — modeled as an ODYM dimension (size classes), since mass is distributed across classes and conserved:
```
size_classes = ['<20mm', '20-50mm', '50-80mm', '80-150mm', '150-300mm', '>300mm']
```

**Other properties** — stored as material-type attributes (not ODYM dimensions), used to calculate TCs:
```python
material_properties = {
    'PET': {'density': 1350, 'magnetic': False, 'conductive': False, 'nir_detectable': True},
    'Steel': {'density': 7800, 'magnetic': True, 'conductive': True, 'nir_detectable': False},
    ...
}
```

This avoids dimensionality explosion while keeping the physics.

---

## 3. Separation Technologies

### 3.1 Technology Catalog

Each technology is a process logic in BioDYM. The TC matrix for each depends on different physical properties:

| Technology | Separation Principle | TC Depends On | Typical Waste Streams |
|---|---|---|---|
| **Trommel screen** | Size | Particle size vs. mesh size | All |
| **Vibrating screen** | Size | Particle size, shape | C&D, WEEE |
| **Ballistic separator** | Size + Shape + Density | 2D/3D, density, size | Packaging, MSW |
| **Air classifier** (zigzag, cross-flow) | Aerodynamic | Density, size, shape | Packaging, MSW, WEEE |
| **Magnetic separator** (drum, overhead) | Magnetism | Magnetic susceptibility | All with metals |
| **Eddy current separator** | Conductivity | Conductivity, density, size | All with metals |
| **NIR sorter** | Optical (material ID) | NIR signature, size (min detection size) | Packaging, WEEE plastics |
| **VIS/color sorter** | Optical (color) | Color | Glass, some plastics |
| **X-ray sorter** (XRT/XRF) | Density / elemental | Atomic density, element | WEEE, C&D, metals |
| **Sink-float separator** | Density | Density vs. medium density | WEEE plastics, C&D |
| **Shredder / granulator** | Comminution | Brittleness, size | WEEE, ELV (pre-processing) |
| **Manual sorting** | Human recognition | Visual appearance | All (quality control) |
| **Robotic sorter** | AI + vision | Visual + NIR | Packaging, WEEE |

### 3.2 Process Logic Types

These technologies map to a small set of process logic patterns:

**A) Property-threshold separation** (Screen, Magnetic, Eddy Current)
- Binary split: material either has the property or doesn't
- Separation efficiency follows a Tromp/partition curve around the threshold
- Parameters: threshold value, curve sharpness (Ecart probable)

**B) Probabilistic identification** (NIR, VIS, X-ray, Robotic)
- Each material has a detection probability (depends on size, overlap, belt speed)
- Detected material gets ejected with an ejection efficiency
- Parameters: detection rate per (material, size), ejection efficiency, belt speed

**C) Density-gradient separation** (Air classifier, Sink-float, Jig)
- Separation based on density relative to a medium/air flow
- All materials separate simultaneously along a density gradient
- Parameters: cut-point density, Tromp curve sharpness

**D) Comminution** (Shredder, Granulator)
- Not a separation but a size reduction — transforms the size distribution
- Liberation of composite materials (e.g., PCB → separated metals + plastics)
- Parameters: target size distribution, liberation matrix per material

**E) Manual/Robotic sorting**
- Picking rate per material type (items/min or kg/min)
- Misidentification rate
- Limited by throughput capacity

---

## 4. ODYM Dimension Structure

### 4.1 Recommended Dimensions

```
Indices = "t,g,s"

t = Time         (e.g., hourly, daily, or yearly timesteps)
g = Good         (material type: PET, PE, Steel, ...)
s = Size class   (e.g., <20mm, 20-50mm, 50-80mm, ...)
```

Flow shape: `(num_timesteps, num_material_types, num_size_classes)`

### 4.2 Why Not More Dimensions?

Density, magnetism, color etc. are **deterministic properties of each material type** — they don't need their own dimension. PET always has density ~1350 kg/m3. Steel is always magnetic. These are lookup attributes, not tracked mass fractions.

Exception: if the same material type has varying properties (e.g., contaminated vs. clean PET with different densities), either:
- Split into sub-types: `PET_clean`, `PET_contaminated` (adds to `g` dimension)
- Add a quality/contamination dimension (only if many materials affected)

### 4.3 Time Resolution

Sorting plants operate continuously, not yearly. Consider:
- **Steady-state** (single timestep): simplest, sufficient for plant design/optimization
- **Hourly/daily**: captures input variability (morning vs. evening deliveries)
- **Seasonal**: captures composition changes (Christmas packaging peak, garden waste in spring)
- **Yearly**: for long-term planning / policy scenarios

The ODYM time dimension supports any resolution.

---

## 5. TC Matrix Generation

### 5.1 Tromp/Partition Curves for Size-Based Separation

A screen with mesh size `d_cut` doesn't create a sharp cut. The probability of a particle passing through follows a sigmoid:

```
P(pass | size) = 1 / (1 + exp(k * (size - d_cut)))
```

where `k` controls sharpness. For each material type `m` and size class `s`:
```
TC_fines[m, s] = P(pass | midpoint(s))
TC_overs[m, s] = 1 - TC_fines[m, s]
```

Shape-dependent materials (e.g., flat films) have different `k` values than 3D objects.

### 5.2 NIR Sorting Efficiency Matrix

For each (material, size) combination:
```
TC_target[m, s] = detection_rate[m, s] * ejection_efficiency
TC_reject[m, s] = 1 - TC_target[m, s]
```

Detection rate depends on:
- Material NIR signature (some plastics are NIR-invisible: black, multi-layer)
- Particle size (too small → below sensor resolution)
- Belt loading (overlapping particles reduce detection)

### 5.3 Density Separation

For each material type with known density `rho_m`:
```
TC_light[m, s] = 1 / (1 + exp(k * (rho_m - rho_cut)))
TC_heavy[m, s] = 1 - TC_light[m, s]
```

Size influences separation in air classifiers (aerodynamic diameter = f(size, density, shape)).

### 5.4 Magnetic / Eddy Current

Essentially binary based on material property:
```
TC_magnetic[m, s] = recovery_rate    if material_properties[m]['magnetic'] else misplacement_rate
TC_non_mag[m, s] = 1 - TC_magnetic[m, s]
```

Recovery rate may depend on size (small particles harder to capture).

---

## 6. Architecture Changes to BioDYM

### 6.1 What Stays the Same
- Iterative solver loop (convergence-based)
- ODYM MFAsystem, Flow, Stock, Parameter classes
- Mass balance checking (einsum aggregation)
- Scenario engine (deep-copy + re-solve)
- MC simulation framework
- Excel-based configuration

### 6.2 What Changes

| Component | Change | Effort |
|---|---|---|
| **IndexTable** | Add `Good` (material type) and `Size` (size class) classifications | Small |
| **Flow initialization** | `Indices = "t,g,s"` instead of `"t,e"` | Small |
| **Solver: TC application** | Apply TC matrices `(g,s)` to 3D flow arrays | Medium |
| **Data loader** | New Excel sheets for material types, size classes, process parameters | Medium |
| **Separation engines** | New modules for Tromp curves, NIR efficiency, density separation | Medium |
| **Plotting** | Dimension selectors, stacked bar by material type, Sankey by material | Medium |
| **KPI module** | Grade (purity) and Recovery metrics per output stream | Small |

### 6.3 What Can Be Reused As-Is

| Component | Why It Works |
|---|---|
| `Splitter` logic | Splits flow without changing composition — same in 3D |
| `Transformer` logic | Changes composition via element-specific TCs — maps to material-specific TCs |
| Scenario engine | Deep-copy + re-solve works regardless of dimensionality |
| MC simulation | Parameter sampling applies to TC matrices the same way |
| Mass balance (`MassBalance()`) | ODYM's einsum handles any dimensions |

### 6.4 What Probably Doesn't Apply to Sorting

| Component | Reason |
|---|---|
| DSM (Dynamic Stock Model) | Sorting plants don't accumulate stock over decades |
| FOMP (First-Order Multi-Pool) | No biological decay in mechanical sorting |
| Element hierarchy (CC/DM/WC) | Replaced by material type dimension |

These stay in the codebase for biomass/construction case studies but aren't used for sorting.

---

## 7. Differences by Waste Stream

### 7.1 Packaging Waste
- **Key technologies**: Trommel, ballistic separator, NIR (multiple stages), magnetic, eddy current, manual QC
- **Key materials**: ~15-20 material types (polymers, paper, metals, glass)
- **Key properties**: Size (6 classes), NIR signature, density, magnetism
- **Typical plant**: 8-15 unit operations in cascade
- **Time resolution**: Steady-state or seasonal (composition varies)

### 7.2 WEEE
- **Key technologies**: Shredder, magnetic, eddy current, density separation, NIR for plastics
- **Key materials**: ~15 types (metals, plastics, PCB, cables, batteries)
- **Key properties**: Size (post-shredding), density, magnetism, conductivity
- **Special**: Comminution step transforms size distribution and liberates composites
- **Liberation matrix**: Shredding a PCB produces X% copper particles, Y% plastic particles, Z% mixed
- **Typical plant**: Pre-processing (shredder) → metal recovery → plastic separation

### 7.3 Construction & Demolition
- **Key technologies**: Jaw crusher, trommel, air classifier, magnetic, manual
- **Key materials**: ~10 types (concrete, brick, wood, metals, aggregates)
- **Key properties**: Size (coarse classes), density, magnetism
- **Special**: Crushing changes size distribution (similar to WEEE shredding)
- **Typical plant**: Simpler cascade, fewer stages

### 7.4 What Makes It General

The same engine handles all waste streams by changing the **configuration**, not the code:

| Configurable Aspect | How |
|---|---|
| Material types | Excel: list of material names + properties |
| Size classes | Excel: bin edges |
| Plant layout | Excel: process definitions + flow connections |
| Separation parameters | Excel: per-process parameters (mesh size, cut density, detection rates) |
| Input composition | Excel: mass fractions per (material, size) |

Only the **comminution/liberation model** (WEEE, C&D) would need an additional process engine beyond what packaging sorting requires, since it transforms the size distribution rather than separating it.

---

## 8. Implementation Roadmap

### Phase 1: Core Multi-Dimensional Engine (~2 weeks)
- Add `Good` and `Size` classifications to IndexTable
- Update solver for 3D flow arrays `(t, g, s)`
- Extend data loader for new Excel sheets
- Basic Tromp curve utility for TC generation

### Phase 2: Packaging Sorting Case Study (~1-2 weeks)
- Configure a reference LVP sorting plant
- Implement NIR efficiency model
- Add Grade + Recovery KPIs
- Validate against literature/plant data

### Phase 3: Generalization (~1-2 weeks)
- Comminution/liberation model for WEEE/C&D
- Density separation model (sink-float, air classifier)
- Material property database (configurable per waste stream)

### Phase 4: Advanced Features (optional, ~1-2 weeks each)
- MC simulation for input variability + separation uncertainty
- Scenario engine for plant optimization (add/remove/reorder stages)
- ABM input generator (Option C: particle simulation → TC calibration)
- Economic model (throughput, energy, labor costs per process)

---

## 9. Open Questions for Discussion

1. **Time resolution**: Steady-state (simplest) vs. dynamic (captures variability)?
2. **Size classes**: How many? Fixed bins or configurable per case study?
3. **Comminution priority**: Is WEEE/C&D in scope for Phase 1, or packaging first?
4. **Input data format**: Do you have composition data as (material × size) matrices, or as separate distributions that need combining?
5. **Validation data**: Do you have real plant mass balance data to calibrate against?
6. **Economic layer**: Is cost optimization part of the goal, or purely mass balance?
7. **Existing process formulas**: Which separation technologies do your existing formulas cover? This determines which process engines to build first.

---

## 10. References

- Tanguay-Rioux et al. (2022): Mixed modeling approach for mechanical sorting — hybrid TC + mechanistic models for MRFs
- Kroell et al. (2024): Digital twins of waste sorting plants — data-driven NIR process models
- Peukert & Pretz (2015): MC simulation of feed characteristics — particle-level sorter prediction
- Cimpan et al. (2021): Predictive modelling for household packaging waste in sorting facilities
- Pauliuk (2020): ODYM — Open Dynamic Material Systems Model framework
- Brunner & Rechberger (2016): Handbook of Material Flow Analysis — foundational MFA methodology
