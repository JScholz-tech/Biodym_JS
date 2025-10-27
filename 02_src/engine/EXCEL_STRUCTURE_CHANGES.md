# BioDYM Excel Structure Changes for ODYM Compliance

## Current Excel Structure Analysis

Based on your `data_loader.py`, here's your **current Excel structure**:

### **✅ Existing Sheets (No Changes Required)**
```
1_1_Definition_Flows     - Flow definitions
1_2_Data_Flows          - Flow data
2_1_Definition_Processes - Process definitions  
2_2_static_TCs          - Static transfer coefficients
2_3_dynamic_TCs         - Dynamic transfer coefficients
2_4_Initial_Stock       - Initial stock data
3_1_Definition_DSM      - DSM parameters
3_2_Definition_FOMP     - FOMP parameters
```

## Required Excel Changes for ODYM Compliance

### **❌ NEW SHEETS REQUIRED**

#### **1. Region Dimension Sheets**

**Sheet: `3_3_Definition_Regions`** (Required)
| Column | Description | Example Values |
|--------|-------------|----------------|
| `Region_ID` | Unique identifier | 1, 2, 3 |
| `Region_Name` | Region name | "Case_Study_Region", "Region_A", "Region_B" |
| `Description` | Region description | "Primary study area", "Secondary region" |
| `Geographic_Scope` | Geographic scope | "Local", "Regional", "National" |

**Sheet: `3_4_Data_Regions`** (Optional)
| Column | Description | Example Values |
|--------|-------------|----------------|
| `Region_ID` | Reference to Region_ID | 1, 2, 3 |
| `Region_Name` | Region name | "Case_Study_Region" |
| `Population` | Population count | 1000000 |
| `Area_km2` | Area in km² | 500 |
| `GDP` | GDP value | 50000000 |

#### **2. Good Dimension Sheets**

**Sheet: `4_1_Definition_Goods`** (Required)
| Column | Description | Example Values |
|--------|-------------|----------------|
| `Good_ID` | Unique identifier | 1, 2, 3, 4 |
| `Good_Name` | Good name | "Rye_Straw", "Biochar", "Compost", "Energy" |
| `Description` | Good description | "Primary biomass", "Carbonized material" |
| `Category` | Good category | "Biomass", "Energy", "Material" |
| `Unit` | Unit of measurement | "Mg", "MWh", "kg" |

**Sheet: `4_2_Data_Goods`** (Optional)
| Column | Description | Example Values |
|--------|-------------|----------------|
| `Good_ID` | Reference to Good_ID | 1, 2, 3, 4 |
| `Good_Name` | Good name | "Rye_Straw" |
| `Market_Price` | Market price | 50.0 |
| `Availability` | Availability factor | 0.8 |
| `Quality_Factor` | Quality factor | 0.9 |

#### **3. Material Dimension Sheets**

**Sheet: `5_1_Definition_Materials`** (Required)
| Column | Description | Example Values |
|--------|-------------|----------------|
| `Material_ID` | Unique identifier | 1, 2, 3 |
| `Material_Name` | Material name | "Dry_Matter", "Water_Content", "Carbon_Content" |
| `Description` | Material description | "Dry matter content", "Water content" |
| `Composition` | Material composition | "Organic", "Inorganic", "Carbon" |

**Sheet: `5_2_Data_Materials`** (Optional)
| Column | Description | Example Values |
|--------|-------------|----------------|
| `Material_ID` | Reference to Material_ID | 1, 2, 3 |
| `Material_Name` | Material name | "Dry_Matter" |
| `Density` | Material density | 1.2 |
| `Moisture_Content` | Moisture content | 0.2 |
| `Carbon_Content` | Carbon content | 0.45 |

#### **4. Process Dimension Sheets**

**Sheet: `6_1_Definition_Processes`** (Required)
| Column | Description | Example Values |
|--------|-------------|----------------|
| `Process_ID` | Unique identifier | 1, 2, 3, 4 |
| `Process_Name` | Process name | "Harvest", "Processing", "Storage", "Application" |
| `Description` | Process description | "Biomass harvesting", "Material processing" |
| `Type` | Process type | "Primary", "Secondary", "Tertiary" |
| `Efficiency` | Process efficiency | 0.85 |

**Sheet: `6_2_Data_Processes`** (Optional)
| Column | Description | Example Values |
|--------|-------------|----------------|
| `Process_ID` | Reference to Process_ID | 1, 2, 3, 4 |
| `Process_Name` | Process name | "Harvest" |
| `Energy_Consumption` | Energy consumption | 100.0 |
| `Water_Consumption` | Water consumption | 50.0 |
| `Emissions` | Emissions factor | 0.1 |

### **⚠️ EXISTING SHEETS - MINOR UPDATES REQUIRED**

#### **1. Update `1_1_Definition_Flows`**
**Add new columns** (keep existing columns):
| New Column | Description | Example Values |
|------------|-------------|----------------|
| `Region_ID` | Reference to Region_ID | 1, 2, 3 |
| `Good_ID` | Reference to Good_ID | 1, 2, 3, 4 |
| `Material_ID` | Reference to Material_ID | 1, 2, 3 |
| `Process_Type_ID` | Reference to Process_ID | 1, 2, 3, 4 |

#### **2. Update `1_2_Data_Flows`**
**Add new columns** (keep existing columns):
| New Column | Description | Example Values |
|------------|-------------|----------------|
| `Region_ID` | Reference to Region_ID | 1, 2, 3 |
| `Good_ID` | Reference to Good_ID | 1, 2, 3, 4 |
| `Material_ID` | Reference to Material_ID | 1, 2, 3 |
| `Process_Type_ID` | Reference to Process_ID | 1, 2, 3, 4 |

#### **3. Update `2_1_Definition_Processes`**
**Add new columns** (keep existing columns):
| New Column | Description | Example Values |
|------------|-------------|----------------|
| `Process_Type_ID` | Reference to Process_ID | 1, 2, 3, 4 |
| `Region_ID` | Reference to Region_ID | 1, 2, 3 |

## Implementation Strategy

### **Phase 1: Minimal Implementation (Backward Compatible)**

#### **Step 1.1: Add Default Dimension Sheets**
Create the new sheets with **default single values** to maintain compatibility:

**`3_3_Definition_Regions`**:
| Region_ID | Region_Name | Description | Geographic_Scope |
|-----------|-------------|-------------|------------------|
| 1 | Case_Study_Region | Primary study area | Local |

**`4_1_Definition_Goods`**:
| Good_ID | Good_Name | Description | Category | Unit |
|---------|-----------|-------------|----------|------|
| 1 | Rye_Straw | Primary biomass | Biomass | Mg |
| 2 | Biochar | Carbonized material | Material | Mg |
| 3 | Compost | Organic material | Material | Mg |
| 4 | Energy | Energy output | Energy | MWh |

**`5_1_Definition_Materials`**:
| Material_ID | Material_Name | Description | Composition |
|-------------|---------------|-------------|------------|
| 1 | Dry_Matter | Dry matter content | Organic |
| 2 | Water_Content | Water content | Inorganic |
| 3 | Carbon_Content | Carbon content | Carbon |

**`6_1_Definition_Processes`**:
| Process_ID | Process_Name | Description | Type | Efficiency |
|------------|--------------|-------------|------|------------|
| 1 | Harvest | Biomass harvesting | Primary | 0.9 |
| 2 | Processing | Material processing | Secondary | 0.8 |
| 3 | Storage | Material storage | Secondary | 0.95 |
| 4 | Application | Material application | Tertiary | 0.85 |

#### **Step 1.2: Update Existing Sheets (Optional Columns)**
Add the new dimension reference columns to existing sheets, but make them **optional** for backward compatibility:

**`1_1_Definition_Flows`** - Add columns:
- `Region_ID` (default: 1)
- `Good_ID` (default: 1) 
- `Material_ID` (default: 1)
- `Process_Type_ID` (default: 1)

**`1_2_Data_Flows`** - Add columns:
- `Region_ID` (default: 1)
- `Good_ID` (default: 1)
- `Material_ID` (default: 1) 
- `Process_Type_ID` (default: 1)

**`2_1_Definition_Processes`** - Add columns:
- `Process_Type_ID` (default: 1)
- `Region_ID` (default: 1)

### **Phase 2: Full Implementation (Multi-Dimensional)**

#### **Step 2.1: Populate Dimension References**
Once the basic structure is in place, populate the dimension reference columns with actual values:

**Example for `1_1_Definition_Flows`**:
| Flow_ID | Flow_Name | Region_ID | Good_ID | Material_ID | Process_Type_ID |
|---------|-----------|-----------|---------|-------------|-----------------|
| 1 | Rye_Harvest_Flow | 1 | 1 | 1 | 1 |
| 2 | Biochar_Production_Flow | 1 | 2 | 1 | 2 |
| 3 | Compost_Application_Flow | 1 | 3 | 1 | 4 |

#### **Step 2.2: Add Optional Data Sheets**
Add the optional data sheets for richer analysis:

- `3_4_Data_Regions`
- `4_2_Data_Goods` 
- `5_2_Data_Materials`
- `6_2_Data_Processes`

## Data Loader Updates Required

### **Update `REQUIRED_STRUCTURE` in `data_loader.py`**

```python
# Add to REQUIRED_STRUCTURE
REQUIRED_STRUCTURE = {
    # Existing sheets (unchanged)
    "1_1_Definition_Flows": ["Flow_ID", "Flow_Name", "Flow_Output_Process_ID", "Input_Process_ID", "Flow_WC[%]", "Flow_DM[%]", "Flow_CC_DM[%]"],
    "1_2_Data_Flows": ["Flow_ID", "Flow_Data_Year", "Flow_Material"],
    "2_1_Definition_Processes": ["ID", "Process_Name", "Process_Logic"],
    "2_2_static_TCs": ["Flow_ID", "Process_ID", "TC_material_ID", "TC_Value_material"],
    "2_3_dynamic_TCs": ["TC_material_ID", "TC_Value_material", "Year"],
    "2_4_Initial_Stock": ["Process_ID", "IS_Parameter_type", "IS_Parameter_Value"],
    
    # NEW: Dimension sheets
    "3_3_Definition_Regions": ["Region_ID", "Region_Name", "Description", "Geographic_Scope"],
    "4_1_Definition_Goods": ["Good_ID", "Good_Name", "Description", "Category", "Unit"],
    "5_1_Definition_Materials": ["Material_ID", "Material_Name", "Description", "Composition"],
    "6_1_Definition_Processes": ["Process_ID", "Process_Name", "Description", "Type", "Efficiency"],
}
```

### **Update Column Name Mapping**

```python
# Add to COLUMN_NAME_MAPPING
COLUMN_NAME_MAPPING = {
    # Existing mappings (unchanged)
    # ...
    
    # NEW: Dimension sheet mappings
    "3_3_Definition_Regions": {
        "Region_ID": "Region_ID",
        "Region_Name": "Region_Name", 
        "Description": "Description",
        "Geographic_Scope": "Geographic_Scope"
    },
    "4_1_Definition_Goods": {
        "Good_ID": "Good_ID",
        "Good_Name": "Good_Name",
        "Description": "Description", 
        "Category": "Category",
        "Unit": "Unit"
    },
    "5_1_Definition_Materials": {
        "Material_ID": "Material_ID",
        "Material_Name": "Material_Name",
        "Description": "Description",
        "Composition": "Composition"
    },
    "6_1_Definition_Processes": {
        "Process_ID": "Process_ID", 
        "Process_Name": "Process_Name",
        "Description": "Description",
        "Type": "Type",
        "Efficiency": "Efficiency"
    }
}
```

## Migration Strategy

### **Option 1: Gradual Migration (Recommended)**
1. **Week 1**: Add new dimension sheets with default values
2. **Week 2**: Update data loader to handle new sheets
3. **Week 3**: Add optional dimension columns to existing sheets
4. **Week 4**: Test with existing Excel templates
5. **Week 5**: Gradually populate dimension references

### **Option 2: Complete Migration**
1. **Week 1**: Create all new sheets and update all existing sheets
2. **Week 2**: Update data loader completely
3. **Week 3**: Test with updated Excel templates
4. **Week 4**: Migrate all existing data

## Impact Assessment

### **✅ Benefits**
- **Full ODYM Compliance**: Complete dimension system
- **Enhanced Analysis**: Multi-dimensional flow analysis
- **Scalability**: Easy to add new regions, goods, materials, processes
- **Interoperability**: Compatible with other ODYM systems

### **⚠️ Considerations**
- **Excel File Size**: Additional sheets will increase file size
- **Data Entry**: More columns to fill (though many can have defaults)
- **Learning Curve**: Users need to understand new dimension system

### **❌ Risks**
- **Breaking Changes**: Existing Excel templates won't work without updates
- **Data Migration**: Need to migrate existing data to new structure
- **User Confusion**: More complex Excel structure

## Recommendation

**Start with Phase 1 (Minimal Implementation)**:

1. **Add the 4 new dimension sheets** with default single values
2. **Update data loader** to handle new sheets
3. **Test with existing Excel templates** (should still work)
4. **Gradually add dimension columns** to existing sheets
5. **Populate dimension references** as needed

This approach ensures **backward compatibility** while enabling **full ODYM compliance** when needed.

---

*Document Version: 1.0*  
*Last Updated: [Current Date]*  
*Author: BioDYM Development Team*
