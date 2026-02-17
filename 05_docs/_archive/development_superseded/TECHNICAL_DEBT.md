# BioDYM Technical Debt

This document tracks known technical debt and architectural limitations that are acceptable for v1.0 but should be addressed in future versions.

---

## 1. Composition Hierarchy as Metadata (Not Dimensional)

**Documented**: 2025-11-06
**Target Resolution**: v2.0 (Q3 2026)
**Severity**: Medium (affects scientific rigor, not functionality)

### Problem

BioDYM currently treats composition fractions (WC, DM, CC) as "elements" in a single dimension, with hierarchy tracked via `_element_hierarchy` metadata:

```python
# Current v1.0 structure:
Indices = "t,e"  # (time, element)
Shape = (26, 4)  # [material, WC, DM, CC] all in element dimension

# Hierarchy stored as metadata:
mfa_system._element_hierarchy = {
    1: {'name': 'material', 'parent': None},
    2: {'name': 'WC', 'parent': 'material'},
    3: {'name': 'DM', 'parent': 'material'},
    4: {'name': 'CC', 'parent': 'DM'}  # ← CC is child of DM
}
```

### Why It's Wrong

1. **Conceptual mismatch**: These aren't ODYM "elements" (like C, H, O in chemistry)
2. **Hierarchy is metadata**: Parent-child relationships tracked outside dimensional structure
3. **Double-counting risk**: CC is both part of DM and shown separately
4. **Not extensible**: Adding more hierarchy levels becomes messy

### Why We Accept It for v1.0

1. **Time constraint**: Proper fix requires 6-8 weeks of refactoring
2. **Backwards compatibility**: Changing to 3D arrays breaks existing Excel templates
3. **User expectation**: Biomass field uses WC/DM/CC convention
4. **Functionality works**: Math is correct, just structure is suboptimal

### Correct Solution for v2.0+

```python
# Proper ODYM structure:
Indices = "t,m,c"  # (time, material, composition)
Shape = (26, 1, 4)
# Where:
#   material dimension (m): [biomass] (just 1 entry)
#   composition dimension (c): [total, water, dry_matter, carbon] (4 levels)

# Hierarchy is now structural, not metadata:
# - c[0] = total (100%)
# - c[1] = water content (% of total)
# - c[2] = dry matter (% of total)
# - c[3] = carbon (% of dry matter, automatically handled by dimension)
```

### Impact

**Files Affected by Metadata Approach**:
- `02_src/system_setup.py`: Stores `_element_hierarchy` on mfa_system
- `02_src/plotting/composition.py`: Reads metadata to build hierarchy display
- `02_src/engine/solver.py`: Uses metadata for hierarchical calculations

**Files That Will Need Refactoring for v2.0**:
- All calculation modules (solver, dsm_model, fomp_model)
- All plotting modules (need 3D array handling)
- Excel templates (need composition dimension columns)
- Data loaders (config.py, data_loader.py, system_setup.py)

### References

- **Full discussion**: See ROADMAP.md → Version 2.0 → Composition Dimension Refactor
- **Decision rationale**: Option C (metadata) chosen for v1.0 pragmatism
- **Alternative considered**: Option A (dimensional) planned for v2.0

---

## Future Technical Debt Items

Add additional technical debt items here as they are identified.

### Template for New Items

```markdown
## X. [Title]

**Documented**: YYYY-MM-DD
**Target Resolution**: vX.X
**Severity**: Low/Medium/High

### Problem
[Description]

### Why It's Wrong
[Conceptual issues]

### Why We Accept It
[Practical reasons]

### Correct Solution
[How to fix it]

### Impact
[Affected files/systems]

### References
[Links to related docs]
```

---

**Last Updated**: 2025-11-06
**Status**: 1 known technical debt item tracked
