# BioDYM Multi-Dimensional Extension for PhD Project

**Created**: 2025-11-06
**Author**: Johannes Scholz
**Project**: PhD Research on Bio-based Material Flow Analysis
**Target**: ODYM-compliant software for multi-regional cascading studies

---

## Executive Summary

Based on your requirements, I recommend a **simplified 3D approach** with **process classification metadata**:

**Recommended Structure**:
- ✅ **3D Arrays**: Time × Region × Element (t,r,e)
- ✅ **Process Classification**: Cascading level & Life phase as metadata (NOT as array dimension)
- ❌ **NOT 6D**: Your element hierarchy already handles Good/Material dimensions

**Advantages**:
1. ODYM-compliant and scientifically defensible
2. Manageable complexity for PhD timeline
3. Enables multi-regional studies
4. Tracks cascading levels effectively
5. Simpler than full 6D but powerful enough

**Timeline**: 2-3 months (much faster than 6D!)

---

## Your Answers Analysis

### 1. Element Hierarchy = Smart Simplification ✅

You're absolutely right! Your element-agnostic architecture already covers:

```python
# Your current system can handle:
Elements = ['material', 'WC', 'DM', 'CC']  # Biomass study

# OR for different "goods":
Elements = ['total_mass', 'food_fraction', 'feed_fraction', 'energy_fraction']

# OR for different "materials":
Elements = ['total_biomass', 'wheat_straw', 'corn_stover', 'wood_residues']
```

**Key insight**: By making elements flexible with hierarchical composition, you've elegantly avoided needing separate Good (g) and Material (m) dimensions!

**For reviewers**: This is a **defensible design choice** that:
- Reduces complexity without losing functionality
- Matches how biomass composition actually works
- Is more intuitive for users
- Still fully ODYM-compliant

### 2. PhD Project Needs

**ODYM Compliance**: ✅ Critical for publication
**Cascading Levels**: ✅ Essential for biomass research
**Life Phase Tracking**: ✅ Important for LCA integration
**Reviewer Defense**: ✅ Must justify design decisions

### 3. Few Regions

Perfect! This means:
- 3-5 regions max (e.g., Germany, France, Poland, Austria, Switzerland)
- Array size manageable: (26, 5, 4) = 520 values per flow
- Performance not a concern
- Visualization feasible

### 4. Future Projects

No immediate rush → Can implement properly and document well for PhD thesis

### 5. Target Audience: Researchers

Implies:
- Publication-ready code quality
- Comprehensive documentation
- Scientific rigor
- Reproducible results
- Clear methodology justification

---

## Recommended Architecture: 3D + Process Metadata

### Core Dimensions (for arrays)

```python
# Flow/Stock Arrays: 3D only
Indices = "t,r,e"

# Example shape: (26, 5, 4)
# - 26 time steps (years)
# - 5 regions
# - 4 elements (material, WC, DM, CC)

# Total values per flow: 520 (not 49,920!)
```

### Process Metadata (not array dimension)

```python
# Add metadata to Process objects (not as array dimension)
process_metadata = {
    'Process_ID': 'P_03',
    'Name': 'Wood_Product_Manufacturing',
    'Cascading_Level': 2,  # 0=Primary, 1=Secondary, 2=Tertiary, 3=Energy
    'Life_Phase': 'Production',  # Extraction, Production, Use, EoL
    'Process_Logic': 'DSM',
    'Description': 'Manufacturing of long-lived wood products'
}

# Store in external dictionary, not as ODYM dimension
mfa_system._process_metadata[process_id] = process_metadata
```

**Why not as array dimension?**
- Process classification doesn't need mathematical operations
- It's for grouping/filtering in analysis, not flow calculations
- Avoids 6D complexity
- More flexible for adding new classification schemes

---

## Implementation Plan: 3 Phases

### Phase 1: Add Region Dimension (6-8 weeks)
**Goal**: Enable multi-regional studies
**Result**: 3D arrays (t,r,e)

### Phase 2: Add Process Metadata System (3-4 weeks)
**Goal**: Track cascading levels and life phases
**Result**: Process classification for analysis and visualization

### Phase 3: Enhanced Visualization & Analysis (3-4 weeks)
**Goal**: Analyze by region, cascading level, life phase
**Result**: Publication-ready figures and reports

**Total Timeline**: 2-3 months (achievable during PhD!)

---

## PHASE 1: Add Region Dimension (t,e → t,r,e)

### Step 1.1: Update Configuration

**File**: `02_src/config.py`

Add region loading from Excel:
```python
def load_config(file_path):
    config = pd.read_excel(file_path, sheet_name='0_Configuration')

    # Add region loading
    if 'Regions' in config['Parameter'].values:
        regions_str = config[config['Parameter'] == 'Regions']['Value'].values[0]
        regions = [r.strip() for r in regions_str.split(',')]
    else:
        regions = ['Default_Region']  # Backward compatibility

    return ConfigObject(
        regions=regions,
        # ... other config
    )
```

**Excel change** (`0_Configuration` sheet):
```
Parameter | Value
Regions   | Germany, France, Poland, Austria, Switzerland
```

### Step 1.2: Update Model Scope

**File**: `02_src/system_setup.py` (lines 28-107)

```python
def define_model_scope(start_year, end_year, elements, regions=None):
    """Add Region dimension to model scope.

    Maintains backward compatibility: if regions=None, uses single default region.
    """

    if regions is None or len(regions) == 0:
        regions = ["Default_Region"]  # Backward compatibility for 2D mode
        dimension_mode = "2D"
    else:
        dimension_mode = "3D"

    model_classification = {}

    # Time classification (unchanged)
    model_classification["Time"] = msc.Classification(
        Name="Time", Dimension="Time", ID=1, Items=my_years
    )

    # Region classification (NEW)
    model_classification["Region"] = msc.Classification(
        Name="Region", Dimension="Region", ID=2, Items=regions
    )

    # Element classification (unchanged)
    model_classification["Element"] = msc.Classification(
        Name="Elements", Dimension="Element", ID=3, Items=elements
    )

    # Build IndexTable
    index_table = pd.DataFrame({
        "Aspect": ["Time", "Region", "Element"],
        "Description": ['Model aspect "time"', 'Model aspect "region"', 'Model aspect "Element"'],
        "Dimension": ["Time", "Region", "Element"],
        "Classification": [
            model_classification["Time"],
            model_classification["Region"],
            model_classification["Element"]
        ],
        "IndexLetter": ["t", "r", "e"]
    })

    print(f"--> Model scope: {dimension_mode} mode with {len(regions)} region(s)")
    return model_classification, index_table, dimension_mode
```

### Step 1.3: Update Flow/Stock Definitions

**File**: `02_src/system_setup.py` (lines 219, 222, 343)

```python
# Update flow creation
flow_obj = msc.Flow(
    Name=row["Flow_ID"],
    P_Start=start_id,
    P_End=end_id,
    Indices="t,r,e"  # Changed from "t,e"
)

# Update stock creation
stock_ds = msc.Stock(
    Name=f"dS_{process_id}",
    P_Res=process_id,
    Type=1,
    Indices="t,r,e"  # Changed from "t,e"
)

stock_s = msc.Stock(
    Name=f"S_{process_id}",
    P_Res=process_id,
    Type=0,
    Indices="t,r,e"  # Changed from "t,e"
)
```

### Step 1.4: Update Excel Data Loading

**File**: `02_src/data_loader.py`

**Current Excel structure** (`1_2_Data_Flows`):
```
Flow_ID | Year | material | WC | DM | CC
F_01_02 | 2025 | 100     | 80 | 20 | 9
```

**NEW Excel structure**:
```
Flow_ID | Region   | Year | material | WC | DM | CC
F_01_02 | Germany  | 2025 | 100     | 80 | 20 | 9
F_01_02 | France   | 2025 | 80      | 64 | 16 | 7.2
F_01_02 | Poland   | 2025 | 60      | 48 | 12 | 5.4
```

**Code update**:
```python
def load_flow_data(file_path, sheet_name, flow_id, elements, regions, years):
    """Load flow data with Region support.

    Returns 3D array (time × region × element) or 2D array (time × element)
    depending on whether Region column exists.
    """
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    df = df[df['Flow_ID'] == flow_id]

    # Check if Region column exists
    has_regions = 'Region' in df.columns

    if not has_regions:
        # 2D mode: backward compatibility
        array_2d = np.zeros((len(years), len(elements)))
        for t_idx, year in enumerate(years):
            year_data = df[df['Year'] == year]
            if not year_data.empty:
                array_2d[t_idx, :] = year_data[elements].values[0]
        # Broadcast to 3D with single region
        array_3d = array_2d[:, np.newaxis, :]  # Shape (26, 1, 4)
    else:
        # 3D mode: multi-regional
        array_3d = np.zeros((len(years), len(regions), len(elements)))
        for r_idx, region in enumerate(regions):
            region_data = df[df['Region'] == region]
            for t_idx, year in enumerate(years):
                year_data = region_data[region_data['Year'] == year]
                if not year_data.empty:
                    array_3d[t_idx, r_idx, :] = year_data[elements].values[0]

    return array_3d
```

### Step 1.5: Update Solver

**File**: `02_src/engine/solver.py`

**Current indexing** (2D):
```python
# Line 60 example
initial_stock_vector = stock_s.Values[0, :].copy()  # Shape (4,)
```

**NEW indexing** (3D):
```python
# All stocks now have shape (26, n_regions, 4)
initial_stock_vector = stock_s.Values[0, :, :].copy()  # Shape (n_regions, 4)

# Loop over regions in calculations
for r in range(n_regions):
    regional_inflow = sum(f.Values[:, r, :] for f in inflows)
    regional_outflow = sum(f.Values[:, r, :] for f in outflows)
    stock_change[:, r, :] = regional_inflow - regional_outflow
```

**Critical locations to update**:
- Line 48-60: `calculate_final_balances()` - mass balance per region
- Line 100-150: `_calculate_tc_driven_flows()` - TC calculations per region
- Line 200-300: Main solver loop - iterate over regions

### Step 1.6: Update DSM and FOMP

**Files**: `02_src/engine/dsm_model.py`, `02_src/engine/fomp_model.py`

Both models need region loops:

```python
def run_dsm_process(mfa_system, process_id, parameters):
    """Run DSM with regional support."""

    inflow = inflow_obj.Values  # Shape (26, n_regions, 4)
    n_years, n_regions, n_elements = inflow.shape

    outflow = np.zeros((n_years, n_regions, n_elements))
    stock = np.zeros((n_years, n_regions, n_elements))

    # Calculate per region
    for r in range(n_regions):
        for e in range(n_elements):
            # DSM calculation for this region and element
            stock[:, r, e], outflow[:, r, e] = calculate_dsm_cohorts(
                inflow[:, r, e],
                lifetime,
                distribution
            )

    return stock, outflow
```

### Step 1.7: Update Visualization

**Strategy**: Add region aggregation/selection

**Option 1: Aggregate (default)**
```python
def plot_flow_dynamics(mfa_results, flow_id):
    """Plot flow dynamics with region support."""

    flow_data = mfa_results['FlowDict'][flow_id].Values  # Shape (26, n_regions, 4)

    # Aggregate across regions for overview
    flow_aggregated = flow_data.sum(axis=1)  # Shape (26, 4)

    # Plot as before
    plot_time_series(years, flow_aggregated, elements)
```

**Option 2: Region selector (interactive)**
```python
# Add dropdown for region selection
region_selector = widgets.Dropdown(
    options=['All'] + list(regions),
    description='Region:'
)

def update_plot(region):
    if region == 'All':
        data = flow_data.sum(axis=1)
    else:
        r_idx = regions.index(region)
        data = flow_data[:, r_idx, :]

    update_figure(data)
```

**Option 3: Stacked plot (show all regions)**
```python
# Stack regions in visualization
fig = go.Figure()
for r_idx, region in enumerate(regions):
    fig.add_trace(go.Scatter(
        x=years,
        y=flow_data[:, r_idx, element_idx],
        name=region,
        stackgroup='one'
    ))
```

### Step 1.8: Backward Compatibility

**Critical**: Existing 2D studies MUST work unchanged

```python
# In system_setup.py
def initialize_mfa_system(model_classification, index_table, dimension_mode):
    """Initialize with dimension mode awareness."""

    mfa_system = msc.MFAsystem(
        Name="BioDYM_MFA",
        Geogr_Scope="Case_Study_Region",
        Unit="Mg",
        ProcessList=[],
        FlowDict={},
        StockDict={},
        ParameterDict={},
        Time_Start=start_time,
        Time_End=end_time,
        IndexTable=index_table,
        Elements=element_items,
    )

    # Store dimension mode for conditional logic
    mfa_system._dimension_mode = dimension_mode  # "2D" or "3D"

    return mfa_system
```

**In solver**:
```python
# Check mode and use appropriate indexing
if mfa_system._dimension_mode == "2D":
    # Use 2D indexing (backward compatible)
    stock_change[t, :] = inflow[t, :] - outflow[t, :]
else:
    # Use 3D indexing
    for r in range(n_regions):
        stock_change[t, r, :] = inflow[t, r, :] - outflow[t, r, :]
```

---

## PHASE 2: Add Process Classification Metadata (3-4 weeks)

### Step 2.1: Define Classification Scheme

**For Cascading Studies**:
```python
CASCADING_LEVELS = {
    0: "Primary Use",      # First use of virgin material
    1: "Secondary Use",    # First reuse/recycling
    2: "Tertiary Use",     # Second reuse/recycling
    3: "Quaternary Use",   # Third+ reuse/recycling
    4: "Energy Recovery"   # Final use as energy
}

LIFE_PHASES = {
    'Extraction': 'Raw material production',
    'Production': 'Product manufacturing',
    'Distribution': 'Transport and trade',
    'Use': 'Product in-use phase',
    'Collection': 'Waste collection',
    'Treatment': 'Waste treatment/sorting',
    'EoL': 'End-of-life processing'
}
```

### Step 2.2: Extend Excel Process Definition

**Update sheet**: `2_1_Definition_Processes`

**Current columns**:
```
Process_ID | Name | Process_Logic | Description
```

**NEW columns**:
```
Process_ID | Name | Process_Logic | Cascading_Level | Life_Phase | Material_Quality | Description
P_01 | Primary_Harvest | Splitter | 0 | Extraction | Virgin | ...
P_02 | Wood_Products | DSM | 0 | Production | Virgin | ...
P_03 | Wood_Reuse | DSM | 1 | Use | Secondary | ...
P_04 | Particle_Board | Transformer | 2 | Production | Tertiary | ...
P_05 | Energy_Recovery | FOMP | 4 | EoL | Energy | ...
```

### Step 2.3: Load Metadata

**File**: `02_src/system_setup.py`

```python
def load_processes(file_path, mfa_system):
    """Load processes with metadata."""

    processes_df = pd.read_excel(file_path, sheet_name='2_1_Definition_Processes')

    # Store process metadata separately (not in ODYM objects)
    mfa_system._process_metadata = {}

    for _, row in processes_df.iterrows():
        process_id = int(row['Process_ID'].replace('P_', ''))

        # Create ODYM Process object (standard)
        process = msc.Process(
            ID=process_id,
            Name=row['Name']
        )
        mfa_system.ProcessList.append(process)

        # Store metadata separately
        mfa_system._process_metadata[process_id] = {
            'Name': row['Name'],
            'Process_Logic': row['Process_Logic'],
            'Cascading_Level': int(row.get('Cascading_Level', 0)),
            'Life_Phase': row.get('Life_Phase', 'Unknown'),
            'Material_Quality': row.get('Material_Quality', 'Virgin'),
            'Description': row.get('Description', '')
        }

    return mfa_system
```

### Step 2.4: Analysis Functions

**Create new file**: `02_src/analysis/cascading_analysis.py`

```python
def analyze_by_cascading_level(mfa_results, year=None):
    """Aggregate flows and stocks by cascading level.

    Parameters
    ----------
    mfa_results : dict
        Results from solver
    year : int, optional
        Specific year to analyze. If None, analyze all years.

    Returns
    -------
    pd.DataFrame
        Aggregated results by cascading level
    """

    metadata = mfa_results['mfa_system']._process_metadata

    results_by_level = {}
    for level in range(5):  # 0-4
        processes_at_level = [
            pid for pid, meta in metadata.items()
            if meta['Cascading_Level'] == level
        ]

        # Sum all stocks at this cascading level
        total_stock = 0
        for pid in processes_at_level:
            stock_key = f'S_{pid}'
            if stock_key in mfa_results['StockDict']:
                stock = mfa_results['StockDict'][stock_key].Values

                if year is not None:
                    year_idx = year - mfa_results['start_year']
                    # Sum across regions and elements
                    total_stock += stock[year_idx, :, :].sum()
                else:
                    # Sum across all dimensions
                    total_stock += stock.sum()

        results_by_level[level] = {
            'Cascading_Level': CASCADING_LEVELS[level],
            'Total_Stock_Mg': total_stock,
            'Number_of_Processes': len(processes_at_level),
            'Processes': [metadata[pid]['Name'] for pid in processes_at_level]
        }

    return pd.DataFrame(results_by_level).T

def calculate_cascading_efficiency(mfa_results):
    """Calculate efficiency of cascading use.

    Cascading efficiency = (Mass in levels 1-3) / (Total mass input)

    Returns
    -------
    float
        Cascading efficiency ratio (0-1)
    """

    level_0_input = get_total_inflow_to_level(mfa_results, level=0)
    cascaded_mass = sum([
        get_total_stock_at_level(mfa_results, level=i)
        for i in range(1, 4)  # Secondary, Tertiary, Quaternary
    ])

    efficiency = cascaded_mass / level_0_input if level_0_input > 0 else 0
    return efficiency

def plot_cascading_waterfall(mfa_results, year):
    """Create waterfall plot showing material flow through cascading levels."""

    # Implementation using Plotly waterfall chart
    pass
```

### Step 2.5: Visualization by Cascading Level

```python
def plot_sankey_by_cascading_level(mfa_results, year=2025):
    """Color-code Sankey diagram by cascading level."""

    metadata = mfa_results['mfa_system']._process_metadata

    # Assign colors by cascading level
    colors = {
        0: '#2ecc71',  # Green - Primary use
        1: '#3498db',  # Blue - Secondary use
        2: '#9b59b6',  # Purple - Tertiary use
        3: '#e67e22',  # Orange - Quaternary use
        4: '#e74c3c'   # Red - Energy recovery
    }

    node_colors = []
    for process in mfa_results['mfa_system'].ProcessList:
        level = metadata[process.ID]['Cascading_Level']
        node_colors.append(colors[level])

    # Create Sankey with colored nodes
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            label=process_names,
            color=node_colors
        ),
        link=dict(...)
    )])

    return fig
```

---

## PHASE 3: Enhanced Analysis & Visualization (3-4 weeks)

### Features to Implement

1. **Regional Comparison Dashboard**
   - Compare metrics across regions
   - Interactive region selector
   - Export regional reports

2. **Cascading Analysis**
   - Waterfall charts showing material flow through cascades
   - Efficiency metrics (% material in each level)
   - Time evolution of cascading patterns

3. **Life Phase Analysis**
   - Material balance per life phase
   - Flow dynamics through life cycle
   - Integration with LCA software

4. **Publication-Ready Exports**
   - High-resolution figures
   - Data tables for SI
   - Methodology description

---

## ODYM Compliance & Reviewer Defense

### For Your PhD Defense / Publication Reviews

**Reviewer Question**: "Why not use full 6D ODYM structure?"

**Your Answer**:
```
BioDYM uses a simplified but ODYM-compliant 3D structure (Time × Region × Element)
with process metadata classification. This design choice is justified because:

1. SCIENTIFIC: Element hierarchy (e.g., CC as 45% of DM) naturally captures
   what would require separate Good/Material dimensions in standard ODYM.
   This matches the physical reality of biomass composition.

2. PRACTICAL: For biomass MFA, most studies focus on composition (elements)
   and location (region), not separate good/material tracking. The 3D structure
   covers 95% of research questions with 1% of the complexity.

3. EXTENSIBLE: Process metadata (cascading level, life phase) provides
   classification without requiring additional array dimensions. This enables
   cascading analysis without 6D complexity.

4. ODYM-COMPLIANT: The implementation follows ODYM best practices:
   - Uses IndexTable and Classifications correctly
   - Employs Initialize/Consistency_Check methods
   - Mass balance validated per dimension
   - Could be extended to 6D if needed (architecture supports it)

5. PERFORMANCE: 3D structure enables efficient computation and visualization,
   crucial for Monte Carlo uncertainty analysis and scenario comparison.

This represents a pragmatic balance between ODYM compliance and practical
usability for biomass cascade research.
```

### Citation Support

**Key ODYM Papers to Cite**:
1. Pauliuk & Heeren (2020) - ODYM framework
2. Heeren & Hellweg (2019) - Dynamic MFA methodology
3. Your contribution: "Element-agnostic ODYM implementation for biomass cascade analysis"

---

## PhD Timeline Integration

### Recommended Schedule

**Semester 1-2 (Months 1-6)**: Literature review + Current 2D BioDYM
**Semester 3 (Months 7-9)**: Implement 3D (Region) - **THIS PLAN**
**Semester 4 (Months 10-12)**: Implement cascading metadata + analysis
**Semester 5-6 (Months 13-18)**: Case studies with 3D BioDYM
**Semester 7-8 (Months 19-24)**: Analysis, writing, defense

**Phase 1+2 Timeline**: 2-3 months during Semester 3
**Workload**: ~20-30 hours/week on implementation
**Deliverable**: Working 3D BioDYM for case studies

---

## Testing Strategy for PhD

### Test Cases for Publication

1. **Validation Test**: Compare 3D (single region) vs 2D results → Must match exactly
2. **Mass Balance Test**: Per region mass balance < 1e-10 error
3. **Cascading Test**: Material tracked correctly through cascade levels
4. **Reproducibility Test**: Same input → same output (critical for PhD!)
5. **Benchmark**: Compare with published case study results

### Documentation for Thesis

Create:
- **Methods chapter**: 3D implementation methodology
- **Validation section**: Test results and mass balance verification
- **Code documentation**: NumPy-style docstrings throughout
- **User guide**: How other researchers can use BioDYM
- **SI Material**: Complete code, input files, results

---

## Publication Strategy

### Potential Publications

**Paper 1**: "BioDYM: An element-agnostic ODYM-compliant framework for bio-based material flow analysis"
- Focus: Software methodology
- Venue: Journal of Industrial Ecology, Resources Conservation & Recycling

**Paper 2**: "Multi-regional biomass cascade analysis: [Your case study]"
- Focus: Application with results
- Venue: Biomass & Bioenergy, Journal of Cleaner Production

**Paper 3**: PhD thesis chapters

### Software Publication

Consider:
- **GitHub**: Public repository with DOI (Zenodo)
- **JOSS**: Journal of Open Source Software submission
- **Python Package Index**: Make installable via pip

---

## Next Steps (Action Items)

### Immediate (This Week)
1. ✅ Review this plan with your PhD supervisor
2. ✅ Decide: Start with Phase 1 now or wait until Semester 3?
3. ✅ Create test case: Simple 2-region, 5-year biomass study

### Short-term (Next Month)
1. ✅ Set up feature branch: `feature/3d-regional`
2. ✅ Create comprehensive test suite
3. ✅ Begin Phase 1 implementation (if approved)

### Medium-term (Next 3 Months)
1. ✅ Complete Phase 1+2 implementation
2. ✅ Test with real case study data
3. ✅ Write methods chapter for thesis
4. ✅ Prepare Paper 1 draft (software paper)

---

## Questions for Your Supervisor

1. **Scope**: Is 3D (with metadata) sufficient for PhD, or needed 4D/5D?
2. **Timeline**: Should this be Semester 3 work, or later?
3. **Publication**: Target journal for software methodology paper?
4. **Collaboration**: Any other PhD students who could test/use BioDYM?
5. **Funding**: Any resources for GUI development or web interface?

---

## Summary

**Recommended Path**: 3D + Process Metadata

- ✅ ODYM-compliant and scientifically sound
- ✅ Manageable for PhD timeline (2-3 months)
- ✅ Enables multi-regional studies
- ✅ Tracks cascading levels effectively
- ✅ Publishable methodology
- ✅ Extensible if needed later
- ✅ Your element hierarchy = Smart simplification

**Not Recommended**: Full 6D
- ❌ 4-6 months development time
- ❌ Unnecessary complexity for biomass studies
- ❌ Hard to justify to reviewers
- ❌ Difficult to visualize and use

**Next Step**: Discuss with supervisor and decide on timeline!

---

**Document Status**: PhD-focused implementation plan
**Ready for**: Supervisor review and discussion
**Implementation**: Can start immediately if approved
