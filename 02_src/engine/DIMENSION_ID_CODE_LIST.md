# BioDYM Dimension ID Code List

## Dimension ID Coding System

### **Purpose**
A standardized coding system for specifying how dimensions apply to different flows, stocks, and parameters.

### **Core Coding Convention**

#### **For All Dimension Types (Good, Material, Element, Process, Region)**

| Code | Meaning | Usage | Implementation |
|------|---------|-------|----------------|
| **Empty/Blank** | All | Applies to all items in this dimension | Use full dimension range in calculations |
| **Number (1, 2, 3...)** | Specific | Applies to specific item in this dimension | Use index [item_id - 1] in calculations |
| **0** | None | Not applicable for this dimension | Exclude from calculations |

### **Detailed Breakdown**

#### **1. Good_ID Codes**

**Your Good Classification**:
```
Good_ID=1: Raw_Material
Good_ID=2: Product  
Good_ID=3: Waste
```

**Coding in Excel**:

| Code | Meaning | Example Usage |
|------|---------|---------------|
| **Empty/Blank** | All good types (Raw_Material + Product + Waste) | Flow represents total flow across all goods |
| **1** | Raw_Material only | Flow represents raw material input |
| **2** | Product only | Flow represents product output |
| **3** | Waste only | Flow represents waste output |
| **0** | None (not applicable) | Flow is not commodity-based |

**Example**:
```excel
# Sheet: 1_1_Definition_Flows
Flow_ID | Good_ID | Meaning
--------|---------|----------
1 | [empty] | Total flow (all good types)
2 | 1 | Raw_Material flow only
3 | 2 | Product flow only
4 | 3 | Waste flow only
```

#### **2. Material_ID Codes**

**Your Material Classification**:
```
Material_ID=1: WC (Water Content)
Material_ID=2: DM (Dry Matter)
```

**Coding in Excel**:

| Code | Meaning | Example Usage |
|------|---------|---------------|
| **Empty/Blank** | All materials (WC + DM) | Flow represents total material |
| **1** | WC only | Flow represents water content |
| **2** | DM only | Flow represents dry matter |
| **0** | None (not applicable) | Flow is not material-specific |

**Example**:
```excel
# Sheet: 1_1_Definition_Flows
Flow_ID | Material_ID | Meaning
--------|-------------|----------
1 | [empty] | Total material (WC + DM)
2 | 1 | Water content only
3 | 2 | Dry matter only
```

#### **3. Element_ID Codes**

**Your Element Classification**:
```
Element_ID=1: C (Carbon)
Element_ID=2: Non-Carbon
```

**Coding in Excel**:

| Code | Meaning | Example Usage |
|------|---------|---------------|
| **Empty/Blank** | All elements (C + Non-Carbon) | Flow represents total element content |
| **1** | C only | Flow represents carbon content |
| **2** | Non-Carbon only | Flow represents non-carbon content |
| **0** | None (not applicable) | Flow is not element-specific |

**Example**:
```excel
# Sheet: 1_1_Definition_Flows
Flow_ID | Element_ID | Meaning
--------|------------|----------
1 | [empty] | All elements
2 | 1 | Carbon only
3 | 2 | Non-Carbon only
```

#### **4. Process_Type_ID Codes**

**Your Process Type Classification** (from ODYM Configuration):
```
Process_Type_ID=1: Harvest
Process_Type_ID=2: Processing
Process_Type_ID=3: Storage
Process_Type_ID=4: Application
```

**Coding in Excel**:

| Code | Meaning | Example Usage |
|------|---------|---------------|
| **Empty/Blank** | All process types | Flow/stock applies to all process types |
| **1** | Harvest only | Specific to harvest operations |
| **2** | Processing only | Specific to processing operations |
| **3** | Storage only | Specific to storage operations |
| **4** | Application only | Specific to application operations |
| **0** | None (not applicable) | Not process-specific |

**Example**:
```excel
# Sheet: 1_1_Definition_Flows
Flow_ID | Process_Type_ID | Meaning
--------|-----------------|----------
1 | [empty] | All process types
2 | 1 | Harvest operations
3 | 2 | Processing operations
```

#### **5. Region_ID Codes**

**Your Region Classification**:
```
Region_ID=1: Case_Study_Region
```

**Coding in Excel**:

| Code | Meaning | Example Usage |
|------|---------|---------------|
| **Empty/Blank** | All regions (single region default) | Flow applies to entire study region |
| **1** | Case_Study_Region | Specific to study region |
| **0** | None (not applicable) | Not region-specific |

**Example**:
```excel
# Sheet: 1_1_Definition_Flows
Flow_ID | Region_ID | Meaning
--------|-----------|----------
1 | [empty] | All regions (default)
2 | 1 | Case_Study_Region
```

## Implementation in Data Loader

### **Reading Dimension IDs from Excel**

```python
def read_dimension_id(value):
    """
    Read and interpret dimension ID from Excel.
    
    Parameters:
    -----------
    value : str, int, float, None
        Value from Excel cell
    
    Returns:
    --------
    str : "all", "specific", or "none"
        Interpretation of the ID
    int or None : The specific ID if applicable
    """
    # Handle NaN/empty values
    if pd.isna(value) or value == "" or str(value).strip() == "":
        return "all", None
    
    # Handle string representations
    str_value = str(value).strip()
    
    # Handle "0" as "none"
    if str_value == "0" or str_value == "None":
        return "none", None
    
    # Handle specific numbers
    try:
        int_value = int(float(str_value))
        return "specific", int_value
    except (ValueError, OverflowError):
        # If can't convert to int, treat as "all"
        return "all", None
```

### **Processing Flows with Dimension IDs**

```python
def create_flow_with_dimension_ids(row, mfa_system):
    """
    Create flow object with dimension IDs from Excel row.
    
    Parameters:
    -----------
    row : pandas.Series
        Excel row with Flow definition
    mfa_system : msc.MFAsystem
        The MFA system object
    
    Returns:
    --------
    msc.Flow : Flow object with proper Indices
    """
    # Read dimension IDs from Excel
    good_id = read_dimension_id(row.get("Good_ID", ""))
    material_id = read_dimension_id(row.get("Material_ID", ""))
    element_id = read_dimension_id(row.get("Element_ID", ""))
    process_type_id = read_dimension_id(row.get("Process_Type_ID", ""))
    region_id = read_dimension_id(row.get("Region_ID", ""))
    
    # Build Indices string based on dimension IDs
    indices = "t"  # Time is always first
    dimension_map = {}
    
    # Add Element dimension
    indices += ",e"
    
    # Add other dimensions if specific IDs provided
    if region_id[0] == "specific":
        indices += ",r"
        dimension_map["region"] = region_id[1]
    
    if good_id[0] == "specific":
        indices += ",g"
        dimension_map["good"] = good_id[1]
    
    if material_id[0] == "specific":
        indices += ",m"
        dimension_map["material"] = material_id[1]
    
    if process_type_id[0] == "specific":
        indices += ",p"
        dimension_map["process_type"] = process_type_id[1]
    
    # If all dimensions use "all", default to "t,e"
    if indices == "t,e" and all(d[0] == "all" for d in [good_id, material_id, process_type_id, region_id]):
        indices = "t,e"  # Keep simple
    
    # Create flow object
    flow = msc.Flow(
        Name=row["Flow_ID"],
        P_Start=int(row["Flow_Output_Process_ID"]),
        P_End=int(row["Input_Process_ID"]),
        Indices=indices
    )
    
    # Store dimension IDs as custom attribute (temporary, will use ODYM Extensions later)
    flow._dimension_ids = dimension_map
    
    return flow
```

## Complete Excel Example

### **1_1_Definition_Flows (With Dimension IDs)**

| Flow_ID | Flow_Name | Good_ID | Material_ID | Element_ID | Process_Type_ID | Region_ID | Indices |
|---------|-----------|---------|-------------|------------|-----------------|-----------|---------|
| 1 | Total_Flow | [empty] | [empty] | [empty] | [empty] | [empty] | t,e |
| 2 | Raw_Material_Flow | 1 | [empty] | [empty] | [empty] | [empty] | t,e,g |
| 3 | Product_Flow | 2 | [empty] | [empty] | [empty] | [empty] | t,e,g |
| 4 | Waste_Flow | 3 | [empty] | [empty] | [empty] | [empty] | t,e,g |
| 5 | WC_Flow | [empty] | 1 | [empty] | [empty] | [empty] | t,e,m |
| 6 | DM_Flow | [empty] | 2 | [empty] | [empty] | [empty] | t,e,m |
| 7 | Carbon_Flow | [empty] | [empty] | 1 | [empty] | [empty] | t,e |
| 8 | Carbon_Product_Flow | 2 | [empty] | 1 | [empty] | [empty] | t,e,g |
| 9 | Biochar_Production | 2 | 2 | 1 | 2 | [empty] | t,e,g,m,p |

**Interpretation**:
- Flow_ID=1: All materials, all elements, all goods → Simple 2D array
- Flow_ID=2: Raw_Material only (Good_ID=1) → 3D array with Good dimension
- Flow_ID=5: Water Content only (Material_ID=1) → 3D array with Material dimension
- Flow_ID=8: Product (Good_ID=2) + Carbon (Element_ID=1) → 3D array
- Flow_ID=9: Product (Good_ID=2) + Dry Matter (Material_ID=2) + Carbon (Element_ID=1) + Processing (Process_Type_ID=2) → Multi-dimensional

## Summary

**Coding Convention**:
- **Empty/Blank** = "All" (include entire dimension)
- **Number (1,2,3...)** = "Specific" (include that item only)
- **0** = "None" (exclude from this dimension)

**For Your Question**:
```
All = [empty/blank] → Flow applies to all items in dimension
Specific = number (1, 2, 3...) → Flow applies to that specific item
None = 0 → Flow not applicable to this dimension
```

This gives you maximum flexibility for defining flows while maintaining backward compatibility!

---

*Document Version: 1.0*  
*Last Updated: [Current Date]*  
*Author: BioDYM Development Team*
