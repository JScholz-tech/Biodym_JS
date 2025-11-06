# Plotting Updates Needed for 3D Arrays

## The Problem

**Current plotting code assumes 2D arrays**:
```python
flow.Values[:, element_index]  # Works for 2D (time, elements)
```

**But with Materials dimension, arrays are 3D**:
```python
flow.Values.shape = (26, 2, 1)  # (time, materials, elements)
flow.Values[:, element_index]  # ERROR: Dimension mismatch!
```

---

## What Needs to Change

### **Files Affected**:
1. `plotting/scenario.py` - 4 locations
2. `plotting/dynamics.py` - Multiple locations  
3. `plotting/validation.py` - Multiple locations
4. `plotting/composition.py` - Multiple locations
5. `plotting/enhanced_sankey.py` - Multiple locations

---

## Solution Strategy

### **Option A: Use Helper Function** ✅ **RECOMMENDED**

Import and use `get_element_values()` from `utils_3d.py`:

```python
# OLD CODE:
flow.Values[:, element_index]

# NEW CODE:
from plotting.utils_3d import get_element_values
values = get_element_values(flow, element_index)  # Automatically handles 2D/3D
```

### **Advantages**:
- ✅ Backward compatible (works with 2D and 3D)
- ✅ Centralized logic (update in one place)
- ✅ Automatic aggregation over materials
- ✅ Less code changes needed

---

## Files That Need Updates

### **1. plotting/scenario.py** (4 locations)

**Line 115**: `flow.Values[:, element_index]`
```python
# Change to:
from plotting.utils_3d import get_element_values
values.append(np.sum(get_element_values(baseline_results.FlowDict[item], element_index)))
```

**Line 123**: Same change

**Line 281**: `flow.Values[:, element_index]`  
```python
# Change to:
y=get_element_values(flow_obj, element_index)
```

**Line 297**: Same change

### **2. plotting/dynamics.py**

Need to find all locations with `[:, element_index]` and replace with helper function.

### **3. plotting/validation.py**

**Line 58**: `flow.Values[year_index, element_index]`
```python
# Change to:
from plotting.utils_3d import get_element_values
flow_value = get_element_values(flow, element_index)[year_index]
```

**Line 76**: `stock.Values[year_index, element_index]`
```python
ds_sum = get_element_values(ds_val, element_index)[year_index] if ds_val else 0
```

### **4. plotting/composition.py**

Already updated in previous fixes! ✅

### **5. plotting/enhanced_sankey.py**

Need to check and update if needed.

---

## Implementation Approach

### **Phase 1: Update Imports**

Add to top of each file:
```python
from plotting.utils_3d import get_element_values
```

### **Phase 2: Replace Direct Access**

Search and replace patterns:
```python
# Pattern 1: flow.Values[:, element_index]
# Replace with: get_element_values(flow, element_index)

# Pattern 2: flow.Values[year_index, element_index]  
# Replace with: get_element_values(flow, element_index)[year_index]

# Pattern 3: np.sum(flow.Values[:, element_index])
# Replace with: np.sum(get_element_values(flow, element_index))
```

---

## Testing

After updates, test with:
1. ✅ 2D structure (no materials) - should work as before
2. ✅ 3D structure (with materials) - should aggregate over materials
3. ✅ All plots generate successfully
4. ✅ Values are consistent between 2D and 3D

---

## Risk Assessment

**Risk Level**: **Medium**

**Why**:
- Many locations need updates
- But changes are straightforward (search-replace)
- Helper function is tested and safe
- Backward compatible

**Mitigation**:
- Update one file at a time
- Test each file after update
- Keep git commits for rollback

---

**Would you like me to start updating the plotting files?** 🎨

