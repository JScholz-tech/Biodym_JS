# BioDYM Development Roadmap

Future features and planned enhancements for BioDYM.

## Version 1.0 (Current) - Foundation Release

**Status**: Pre-publication preparation

**Key Features**:
- ✅ Element-agnostic architecture (any element set supported)
- ✅ Dynamic Stock Model (DSM) with age-cohort tracking
- ✅ First-Order Mineralization Process (FOMP)
- ✅ Monte Carlo uncertainty analysis
- ✅ Scenario comparison
- ✅ Excel-based configuration
- ✅ Interactive visualizations (Sankey, time-series, dashboards)
- ✅ ODYM framework compliance
- ✅ Stock-outflow transfer coefficients (BioDYM extension)

**Pending**:
- See `PRE_PUBLICATION_CHECKLIST.md` for remaining tasks before v1.0 release

## Version 1.1 (Q1 2026) - Bug Fixes & Polish

**Focus**: Address user feedback from v1.0 release

**Planned Improvements**:
- Bug fixes from initial user reports
- Documentation improvements based on user questions
- Performance optimizations for large systems
- Enhanced error messages and validation
- Additional example datasets

## Version 2.0 (Q3 2026) - Multi-Dimensional Expansion

**Major Features**:

### Composition Dimension Refactor

**Current State**: Composition fractions (WC, DM, CC) stored in element dimension `e`

**Issue**: Conceptual mismatch - treating composition fractions as "elements"
- Material = total biomass (level 0)
- WC, DM = fractions of material (level 1)
- CC = fraction of DM (level 2)
- This is a hierarchical mass accounting system squeezed into one dimension

**Goal**: Separate composition dimension for ODYM compliance

**Proposed Solution**:
```python
# Current structure (v1.0):
Indices = "t,e"  # (time, element)
Shape = (26, 4)  # material, WC, DM, CC in same dimension
# Hierarchy tracked via _element_hierarchy metadata

# New structure (v2.0+):
Indices = "t,m,c"  # (time, material, composition)
Shape = (26, 1, 4)  # 1 material type (biomass), 4 composition levels
# OR
Indices = "t,g,c"  # (time, good, composition)
# Where:
#   m/g = material/good dimension: [biomass]
#   c = composition dimension: [total, water, dry_matter, carbon]
```

**Benefits**:
- ✅ Conceptually clean separation of concerns
- ✅ Hierarchy built into dimensional structure (not metadata)
- ✅ More ODYM-compliant
- ✅ Easier to extend (add more composition levels)
- ✅ Better scientific rigor

**Required Changes**:
```python
# All arrays become 3D instead of 2D
# Affected: solver.py, dsm_model.py, fomp_model.py, all plotting
# Excel template needs restructuring
# Estimate: 6-8 weeks of refactoring + testing
```

**Rationale**:
- v1.0 uses pragmatic approach (metadata) to ship on time
- v2.0+ can do proper refactor with breaking changes allowed
- This enables other multi-dimensional features (regions, goods, etc.)

**Technical Debt**:
- Tracked as `_element_hierarchy` attribute on mfa_system (v1.0)
- To be resolved with proper dimension in v2.0

**Status**: Documented 2025-11-06, planned for v2.0

---

### Multi-Regional MFA

**Current State**: 2D system (Time × Element)

**Goal**: 3D+ system (Time × Element × Region)

**Required Changes**:
```python
# 1. Update system_setup.py → define_model_scope()
model_classification["Region"] = msc.Classification(
    Name="Regions", Dimension="Region", ID=3, Items=regions
)

# 2. Update IndexTable
aspects.append("Region")
index_letters.append("r")

# 3. Update all Indices strings
# Before: Indices="t,e"  → shape (T, E)
# After:  Indices="t,e,r" → shape (T, E, R)

# 4. CRITICAL: All array operations must handle 3D+
# Affected: solver.py, dsm_model.py, fomp_model.py, all plotting
# Estimate: 2-4 weeks of refactoring
```

**Benefits**:
- Regional trade flows
- Multi-region comparison
- Spatial visualization
- Regional policy scenarios

**Recommendation**:
- ✅ Architecture is ODYM-compliant and ready
- ✅ Document in roadmap for v2.0
- ❌ Don't implement before v1.0 (scope creep risk)

### Data Reconciliation Module

**Status**: Excellent implementation plan exists in `IMPLEMENTATION_PLAN_DATA_RECONCILIATION.md`

**Key Features Planned**:
- Constrained weighted least-squares optimization
- Gross error detection with statistical diagnostics
- Integration with Monte Carlo uncertainty
- Phase 1-4 implementation strategy already defined

**Benefits**:
- Improved data quality
- Statistical consistency
- Automatic error detection
- Reduced uncertainty

**Development Time**: 4-6 weeks

**Recommendation**:
- **Keep implementation plan** - Well-designed for future
- **Mention in roadmap** - Show planned development
- **Reference in paper** - "Future work will include statistical data reconciliation..."

## Version 2.1 (Q4 2026) - Advanced Visualizations

**Planned Features**:

### Element Multiplot Sankey
- Stack multiple Sankey diagrams vertically (one per element)
- Single time slider controlling all subplots
- Show multi-level element hierarchy
- Dynamic evolution visualization

**Status**: Attempted in 2025-11-03, needs rework
- Issue: Plotly's `make_subplots` with Sankey traces
- Alternative: Create separate FigureWidgets and stack them

### 3D Flow Visualization
- 3D representation of system structure
- Interactive rotation and zoom
- Color-coded by element or process type
- Animation over time

### Network Analysis Tools
- Process dependency graphs
- Critical path identification
- Bottleneck detection
- Flow optimization suggestions

## Version 3.0 (2027) - Sustainability Metrics

**Focus**: Advanced sustainability and circularity indicators

**Planned Features**:

### Life Cycle Assessment (LCA) Integration
- Carbon footprint tracking
- Energy balance analysis
- Water footprint
- Integration with ecoinvent/other LCA databases

### Circular Economy Metrics
- Material circularity indicators (MCI)
- Cascading utilization efficiency
- Recycling rates
- Value retention metrics

### Economic Analysis
- Cost-benefit analysis
- Material value tracking
- Economic circularity indicators

## Long-Term Vision (2028+)

### Machine Learning Integration
- Automated system structure discovery
- Transfer coefficient prediction
- Anomaly detection in flows
- Forecasting and scenario generation

### Web-Based Interface
- Browser-based GUI (no installation required)
- Cloud computation for large systems
- Collaborative editing
- Real-time visualization updates

### Database Integration
- Direct connection to production databases
- Automated data import
- Real-time MFA updates
- API for external systems

## Contributing to the Roadmap

We welcome suggestions for future features! Please:

1. Open an issue on GitHub with label `enhancement`
2. Describe the use case and benefits
3. Provide example data if possible
4. Discuss technical approach if you have ideas

## Versioning Strategy

BioDYM follows [Semantic Versioning](https://semver.org/):

- **Major (X.0.0)**: Breaking changes, major new features
- **Minor (1.X.0)**: New features, backwards compatible
- **Patch (1.0.X)**: Bug fixes, documentation updates

---

**Last Updated**: 2025-11-04
**Current Version**: 1.0.0-pre (unreleased)
