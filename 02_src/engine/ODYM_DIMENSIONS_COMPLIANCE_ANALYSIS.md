# BioDYM ODYM Dimensions Compliance Analysis

## Overview

This document analyzes the compliance of BioDYM's dimension usage with ODYM's comprehensive dimension system. The analysis reveals significant gaps in dimension utilization that impact system scalability, interoperability, and compliance with ODYM standards.

## Executive Summary

- **Overall Dimension Compliance**: 3/10 (Poor) - Major gaps in dimension usage
- **Missing Dimensions**: Region, Good, Material, Process classifications
- **Impact**: Limited scalability, reduced interoperability, non-standard ODYM compliance
- **Priority**: High - Critical for ODYM compliance and future extensibility

## ODYM Dimension System Analysis

### Standard ODYM Dimensions

Based on the ODYM framework, the following dimensions are available:

#### **Core Dimensions** (from `ODYM_Classes.py`):
```python
self.Dimensions = {
    "Time": "Time",
    "Process": "Process", 
    "Region": "Region",
    "Good": "Process, good, or commodity",
    "Material": "Material: ore, alloy, scrap type, ...",
    "Element": "Chemical element",
}
```

#### **Core Aspects** (from `ODYM_Classes.py`):
```python
self.Aspects = {
    "Time": "Model time",
    "Cohort": "Age-cohort",
    "OriginProcess": "Process where flow originates",
    "DestinationProcess": "Destination process of flow",
    "OriginRegion": "Region where flow originates from",
    "DestinationRegion": "Region where flow is bound to",
    "Good": "Process, good, or commodity",
    "Material": "Material: ore, alloy, scrap type, ...",
    "Element": "Chemical element",
}
```

## BioDYM Current Dimension Usage

### **Currently Implemented Dimensions**

#### ✅ **Time Dimension** (Fully Implemented)
```python
# In system_setup.py
model_classification["Time"] = msc.Classification(
    Name="Time", Dimension="Time", ID=1, Items=my_years
)
```
- **Status**: ✅ Complete
- **Usage**: Properly integrated in IndexTable
- **Compliance**: 10/10

#### ✅ **Element Dimension** (Fully Implemented)
```python
# In system_setup.py
model_classification["Element"] = msc.Classification(
    Name="Elements", Dimension="Element", ID=2, Items=elements
)
```
- **Status**: ✅ Complete
- **Usage**: Properly integrated in IndexTable
- **Compliance**: 10/10

### **Missing Critical Dimensions**

#### ❌ **Region Dimension** (Not Implemented)
**Current State**: 
- Only `Geogr_Scope="Case_Study_Region"` as string
- No regional classification system
- No regional flow tracking

**ODYM Standard**:
```python
# Should be implemented as:
model_classification["Region"] = msc.Classification(
    Name="Regions", 
    Dimension="Region", 
    ID=3, 
    Items=["Region_A", "Region_B", "Case_Study_Region"]
)
```

**Impact**:
- ❌ Cannot track inter-regional flows
- ❌ Cannot perform regional analysis
- ❌ Limited scalability for multi-regional studies
- ❌ Non-compliant with ODYM standards

#### ❌ **Good Dimension** (Not Implemented)
**Current State**: 
- No good/commodity classification
- Materials treated as simple strings
- No good-specific flow tracking

**ODYM Standard**:
```python
# Should be implemented as:
model_classification["Good"] = msc.Classification(
    Name="Goods", 
    Dimension="Good", 
    ID=4, 
    Items=["Rye_Straw", "Biochar", "Compost", "Energy"]
)
```

**Impact**:
- ❌ Cannot track good-specific flows
- ❌ Limited material flow analysis
- ❌ No commodity-based reporting
- ❌ Non-compliant with ODYM standards

#### ❌ **Material Dimension** (Not Implemented)
**Current State**: 
- Materials handled as simple strings in Excel
- No material classification system
- No material-specific properties

**ODYM Standard**:
```python
# Should be implemented as:
model_classification["Material"] = msc.Classification(
    Name="Materials", 
    Dimension="Material", 
    ID=5, 
    Items=["Dry_Matter", "Water_Content", "Carbon_Content"]
)
```

**Impact**:
- ❌ Cannot track material-specific properties
- ❌ Limited material composition analysis
- ❌ No material-specific parameters
- ❌ Non-compliant with ODYM standards

#### ❌ **Process Dimension** (Partially Implemented)
**Current State**: 
- Processes exist but not as formal classification
- No process classification system
- Process IDs used directly without classification

**ODYM Standard**:
```python
# Should be implemented as:
model_classification["Process"] = msc.Classification(
    Name="Processes", 
    Dimension="Process", 
    ID=6, 
    Items=["Harvest", "Processing", "Storage", "Application"]
)
```

**Impact**:
- ❌ Cannot perform process-type analysis
- ❌ Limited process categorization
- ❌ No process-specific reporting
- ❌ Non-compliant with ODYM standards

## Detailed Compliance Analysis

### **IndexTable Structure Analysis**

#### **Current BioDYM IndexTable**:
```python
# Current implementation (system_setup.py)
index_table = pd.DataFrame({
    "Aspect": ["Time", "Element"],
    "Description": ['Model aspect "time"', 'Model aspect "Element"'],
    "Dimension": ["Time", "Element"],
    "Classification": [model_classification[Aspect] for Aspect in ["Time", "Element"]],
    "IndexLetter": ["t", "e"],
})
```

#### **ODYM-Compliant IndexTable**:
```python
# Should be implemented as:
index_table = pd.DataFrame({
    "Aspect": ["Time", "Element", "Region", "Good", "Material", "Process"],
    "Description": [
        'Model aspect "time"',
        'Model aspect "Element"', 
        'Model aspect "Region"',
        'Model aspect "Good"',
        'Model aspect "Material"',
        'Model aspect "Process"'
    ],
    "Dimension": ["Time", "Element", "Region", "Good", "Material", "Process"],
    "Classification": [
        model_classification["Time"],
        model_classification["Element"],
        model_classification["Region"],
        model_classification["Good"],
        model_classification["Material"],
        model_classification["Process"]
    ],
    "IndexLetter": ["t", "e", "r", "g", "m", "p"],
})
```

### **Flow Indices Analysis**

#### **Current BioDYM Flow Indices**:
```python
# Current implementation
Indices="t,e"  # Only Time and Element
```

#### **ODYM-Compliant Flow Indices**:
```python
# Should be implemented as:
Indices="t,e,r,g,m,p"  # Time, Element, Region, Good, Material, Process
```

**Impact on Flow Arrays**:
- **Current**: 2D arrays (Time × Element)
- **ODYM Standard**: 6D arrays (Time × Element × Region × Good × Material × Process)

### **Data Structure Impact Analysis**

#### **Current BioDYM Data Structures**:
```python
# Flow values: 2D array
flow.Values.shape = (n_years, n_elements)

# Stock values: 2D array  
stock.Values.shape = (n_years, n_elements)

# Parameter values: 2D array
parameter.Values.shape = (n_years, n_elements)
```

#### **ODYM-Compliant Data Structures**:
```python
# Flow values: 6D array
flow.Values.shape = (n_years, n_elements, n_regions, n_goods, n_materials, n_processes)

# Stock values: 6D array
stock.Values.shape = (n_years, n_elements, n_regions, n_goods, n_materials, n_processes)

# Parameter values: 6D array
parameter.Values.shape = (n_years, n_elements, n_regions, n_goods, n_materials, n_processes)
```

## Compliance Issues Identified

### **1. Missing Regional Dimension**
**Severity**: High | **Impact**: Major

**Issues**:
- Cannot track inter-regional flows
- Cannot perform regional analysis
- Limited scalability for multi-regional studies
- Non-compliant with ODYM standards

**Example Impact**:
```python
# Current: Cannot track regional flows
flow_from_region_a_to_b = None  # Not possible

# ODYM Standard: Can track regional flows
flow_from_region_a_to_b = mfa_system.FlowDict["Flow_A_to_B"].Values[:, :, region_a_idx, :, :, :]
```

### **2. Missing Good Dimension**
**Severity**: High | **Impact**: Major

**Issues**:
- Cannot track good-specific flows
- Limited material flow analysis
- No commodity-based reporting
- Non-compliant with ODYM standards

**Example Impact**:
```python
# Current: Cannot track good-specific flows
rye_straw_flows = None  # Not possible

# ODYM Standard: Can track good-specific flows
rye_straw_flows = mfa_system.FlowDict["Rye_Straw_Flow"].Values[:, :, :, rye_straw_idx, :, :]
```

### **3. Missing Material Dimension**
**Severity**: Medium | **Impact**: Moderate

**Issues**:
- Cannot track material-specific properties
- Limited material composition analysis
- No material-specific parameters
- Non-compliant with ODYM standards

**Example Impact**:
```python
# Current: Cannot track material-specific flows
dry_matter_flows = None  # Not possible

# ODYM Standard: Can track material-specific flows
dry_matter_flows = mfa_system.FlowDict["DM_Flow"].Values[:, :, :, :, dry_matter_idx, :]
```

### **4. Missing Process Dimension**
**Severity**: Medium | **Impact**: Moderate

**Issues**:
- Cannot perform process-type analysis
- Limited process categorization
- No process-specific reporting
- Non-compliant with ODYM standards

**Example Impact**:
```python
# Current: Cannot track process-specific flows
harvest_flows = None  # Not possible

# ODYM Standard: Can track process-specific flows
harvest_flows = mfa_system.FlowDict["Harvest_Flow"].Values[:, :, :, :, :, harvest_idx]
```

## Implementation Strategy

### **Phase 1: Foundation Dimensions (2-3 weeks)**
**Priority**: High | **Effort**: 8-12 hours

#### **1.1 Add Region Dimension**
```python
# In system_setup.py
def define_model_scope(start_year, end_year, elements, regions=None):
    """Defines the temporal, elemental, and regional scope of the MFA model."""
    
    if regions is None:
        regions = ["Case_Study_Region"]  # Default single region
    
    model_classification = {}
    my_years = list(np.arange(start_year, end_year + 1))
    
    # Existing dimensions
    model_classification["Time"] = msc.Classification(
        Name="Time", Dimension="Time", ID=1, Items=my_years
    )
    model_classification["Element"] = msc.Classification(
        Name="Elements", Dimension="Element", ID=2, Items=elements
    )
    
    # NEW: Add Region dimension
    model_classification["Region"] = msc.Classification(
        Name="Regions", Dimension="Region", ID=3, Items=regions
    )
    
    # Update IndexTable
    index_table = pd.DataFrame({
        "Aspect": ["Time", "Element", "Region"],
        "Description": [
            'Model aspect "time"',
            'Model aspect "Element"',
            'Model aspect "Region"'
        ],
        "Dimension": ["Time", "Element", "Region"],
        "Classification": [
            model_classification["Time"],
            model_classification["Element"],
            model_classification["Region"]
        ],
        "IndexLetter": ["t", "e", "r"],
    })
    
    return model_classification, index_table
```

#### **1.2 Add Good Dimension**
```python
# In system_setup.py
def define_model_scope(start_year, end_year, elements, regions=None, goods=None):
    """Defines the comprehensive scope of the MFA model."""
    
    if goods is None:
        goods = ["Rye_Straw", "Biochar", "Compost", "Energy"]  # Default goods
    
    # ... existing code ...
    
    # NEW: Add Good dimension
    model_classification["Good"] = msc.Classification(
        Name="Goods", Dimension="Good", ID=4, Items=goods
    )
    
    # Update IndexTable
    index_table = pd.DataFrame({
        "Aspect": ["Time", "Element", "Region", "Good"],
        "Description": [
            'Model aspect "time"',
            'Model aspect "Element"',
            'Model aspect "Region"',
            'Model aspect "Good"'
        ],
        "Dimension": ["Time", "Element", "Region", "Good"],
        "Classification": [
            model_classification["Time"],
            model_classification["Element"],
            model_classification["Region"],
            model_classification["Good"]
        ],
        "IndexLetter": ["t", "e", "r", "g"],
    })
    
    return model_classification, index_table
```

### **Phase 2: Advanced Dimensions (3-4 weeks)**
**Priority**: Medium | **Effort**: 12-16 hours

#### **2.1 Add Material Dimension**
```python
# In system_setup.py
def define_model_scope(start_year, end_year, elements, regions=None, goods=None, materials=None):
    """Defines the comprehensive scope of the MFA model."""
    
    if materials is None:
        materials = ["Dry_Matter", "Water_Content", "Carbon_Content"]  # Default materials
    
    # ... existing code ...
    
    # NEW: Add Material dimension
    model_classification["Material"] = msc.Classification(
        Name="Materials", Dimension="Material", ID=5, Items=materials
    )
    
    # Update IndexTable
    index_table = pd.DataFrame({
        "Aspect": ["Time", "Element", "Region", "Good", "Material"],
        "Description": [
            'Model aspect "time"',
            'Model aspect "Element"',
            'Model aspect "Region"',
            'Model aspect "Good"',
            'Model aspect "Material"'
        ],
        "Dimension": ["Time", "Element", "Region", "Good", "Material"],
        "Classification": [
            model_classification["Time"],
            model_classification["Element"],
            model_classification["Region"],
            model_classification["Good"],
            model_classification["Material"]
        ],
        "IndexLetter": ["t", "e", "r", "g", "m"],
    })
    
    return model_classification, index_table
```

#### **2.2 Add Process Dimension**
```python
# In system_setup.py
def define_model_scope(start_year, end_year, elements, regions=None, goods=None, materials=None, processes=None):
    """Defines the comprehensive scope of the MFA model."""
    
    if processes is None:
        processes = ["Harvest", "Processing", "Storage", "Application"]  # Default processes
    
    # ... existing code ...
    
    # NEW: Add Process dimension
    model_classification["Process"] = msc.Classification(
        Name="Processes", Dimension="Process", ID=6, Items=processes
    )
    
    # Update IndexTable
    index_table = pd.DataFrame({
        "Aspect": ["Time", "Element", "Region", "Good", "Material", "Process"],
        "Description": [
            'Model aspect "time"',
            'Model aspect "Element"',
            'Model aspect "Region"',
            'Model aspect "Good"',
            'Model aspect "Material"',
            'Model aspect "Process"'
        ],
        "Dimension": ["Time", "Element", "Region", "Good", "Material", "Process"],
        "Classification": [
            model_classification["Time"],
            model_classification["Element"],
            model_classification["Region"],
            model_classification["Good"],
            model_classification["Material"],
            model_classification["Process"]
        ],
        "IndexLetter": ["t", "e", "r", "g", "m", "p"],
    })
    
    return model_classification, index_table
```

### **Phase 3: Data Structure Migration (4-5 weeks)**
**Priority**: High | **Effort**: 16-20 hours

#### **3.1 Update Flow Indices**
```python
# In system_setup.py
def create_flow_with_full_indices(mfa_system, flow_name, process_start, process_end):
    """Create flow with full ODYM-compliant indices."""
    
    # Determine flow indices based on available dimensions
    indices = "t,e"  # Start with Time and Element
    
    if "Region" in mfa_system.IndexTable.index:
        indices += ",r"
    if "Good" in mfa_system.IndexTable.index:
        indices += ",g"
    if "Material" in mfa_system.IndexTable.index:
        indices += ",m"
    if "Process" in mfa_system.IndexTable.index:
        indices += ",p"
    
    # Create flow with proper indices
    flow = msc.Flow(
        Name=flow_name,
        P_Start=process_start,
        P_End=process_end,
        Indices=indices
    )
    
    return flow
```

#### **3.2 Update Data Array Shapes**
```python
# In system_setup.py
def initialize_flow_values(mfa_system, flow):
    """Initialize flow values with proper dimensions."""
    
    # Get dimension sizes
    n_years = len(mfa_system.IndexTable.Classification["Time"].Items)
    n_elements = len(mfa_system.IndexTable.Classification["Element"].Items)
    
    # Initialize with Time and Element dimensions
    shape = [n_years, n_elements]
    
    # Add additional dimensions if available
    if "Region" in mfa_system.IndexTable.index:
        n_regions = len(mfa_system.IndexTable.Classification["Region"].Items)
        shape.append(n_regions)
    
    if "Good" in mfa_system.IndexTable.index:
        n_goods = len(mfa_system.IndexTable.Classification["Good"].Items)
        shape.append(n_goods)
    
    if "Material" in mfa_system.IndexTable.index:
        n_materials = len(mfa_system.IndexTable.Classification["Material"].Items)
        shape.append(n_materials)
    
    if "Process" in mfa_system.IndexTable.index:
        n_processes = len(mfa_system.IndexTable.Classification["Process"].Items)
        shape.append(n_processes)
    
    # Initialize flow values
    flow.Values = np.zeros(shape)
    
    return flow
```

## Excel Template Impact Analysis

### **Current Excel Structure**
**Impact Level**: ❌ **MAJOR CHANGES REQUIRED**

#### **Required Excel Changes**:

1. **Add Regional Data Sheets**:
   - `3_1_Definition_Regions`
   - `3_2_Data_Regions`

2. **Add Good Data Sheets**:
   - `4_1_Definition_Goods`
   - `4_2_Data_Goods`

3. **Add Material Data Sheets**:
   - `5_1_Definition_Materials`
   - `5_2_Data_Materials`

4. **Add Process Data Sheets**:
   - `6_1_Definition_Processes`
   - `6_2_Data_Processes`

5. **Update Existing Sheets**:
   - Add regional, good, material, process columns to flow definitions
   - Update data structures to support multi-dimensional arrays

#### **Example Excel Structure**:
```
Excel Template Structure:
├── 1_1_Definition_Flows (Updated with new dimensions)
├── 1_2_Data_Flows (Updated with new dimensions)
├── 2_1_Definition_Processes (Updated)
├── 2_2_static_TCs (Updated)
├── 2_3_dynamic_TCs (Updated)
├── 2_4_Initial_Stock (Updated)
├── 3_1_Definition_Regions (NEW)
├── 3_2_Data_Regions (NEW)
├── 4_1_Definition_Goods (NEW)
├── 4_2_Data_Goods (NEW)
├── 5_1_Definition_Materials (NEW)
├── 5_2_Data_Materials (NEW)
├── 6_1_Definition_Processes (NEW)
└── 6_2_Data_Processes (NEW)
```

## Compliance Score Summary

| Dimension | Current Status | Compliance Score | Priority | Effort |
|-----------|----------------|------------------|----------|--------|
| **Time** | ✅ Complete | 10/10 | Low | 0 hours |
| **Element** | ✅ Complete | 10/10 | Low | 0 hours |
| **Region** | ❌ Missing | 0/10 | High | 4-6 hours |
| **Good** | ❌ Missing | 0/10 | High | 4-6 hours |
| **Material** | ❌ Missing | 0/10 | Medium | 3-4 hours |
| **Process** | ❌ Missing | 0/10 | Medium | 3-4 hours |

**Overall Dimension Compliance**: 3/10 (Poor)

## Recommendations

### **Immediate Actions (High Priority)**

1. **Add Region Dimension**: Critical for multi-regional studies
2. **Add Good Dimension**: Essential for commodity tracking
3. **Update IndexTable**: Include all dimensions
4. **Update Flow Indices**: Support multi-dimensional flows

### **Medium-Term Actions (Medium Priority)**

1. **Add Material Dimension**: For material-specific analysis
2. **Add Process Dimension**: For process-type analysis
3. **Update Data Structures**: Support multi-dimensional arrays
4. **Update Excel Templates**: Add new dimension sheets

### **Long-Term Actions (Low Priority)**

1. **Comprehensive Testing**: Test all dimension combinations
2. **Performance Optimization**: Optimize multi-dimensional operations
3. **Documentation Updates**: Update documentation for new dimensions
4. **User Training**: Train users on new dimension system

## Conclusion

Your observation about missing dimensions is **absolutely correct** and represents a **critical compliance issue**. BioDYM currently uses only 2 out of 6 standard ODYM dimensions (Time and Element), missing the crucial Region, Good, Material, and Process dimensions.

**Key Findings**:
- **Dimension Compliance**: 3/10 (Poor)
- **Missing Dimensions**: 4 out of 6 standard dimensions
- **Impact**: Major limitations in scalability and interoperability
- **Excel Impact**: Major changes required to Excel templates

**Recommended Approach**:
1. **Phase 1**: Add Region and Good dimensions (high priority)
2. **Phase 2**: Add Material and Process dimensions (medium priority)
3. **Phase 3**: Update data structures and Excel templates (high priority)

This dimension compliance issue is **more critical** than the function compliance issues we discussed earlier, as it fundamentally limits BioDYM's ability to scale and integrate with other ODYM-based systems.

---

*Document Version: 1.0*  
*Last Updated: [Current Date]*  
*Author: BioDYM Development Team*
