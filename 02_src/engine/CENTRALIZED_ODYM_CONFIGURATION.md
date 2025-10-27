# BioDYM Centralized ODYM Dimension Configuration

## Your Proposed Approach Analysis

Your approach is **excellent** and much more elegant than my previous suggestions! Let me analyze this centralized configuration approach.

## Core ODYM Dimensions (Always Required)

Based on the ODYM framework, here are the **core dimensions**:

### **✅ Always Required Dimensions**
```python
# From ODYM_Classes.py
self.Dimensions = {
    "Time": "Time",           # ✅ You have this
    "Process": "Process",     # ✅ You have this (as individual processes)
    "Region": "Region",       # ❌ You need this
    "Good": "Process, good, or commodity",     # ✅ You have this (as materials)
    "Material": "Material: ore, alloy, scrap type, ...",  # ✅ You have this
    "Element": "Chemical element",             # ✅ You have this
}
```

### **📊 Your Current BioDYM Dimensions**
- **Time**: ✅ Years (2020-2025)
- **Element**: ✅ ["material", "WC", "DM", "CC"]
- **Process**: ✅ Individual processes (Harvest, Processing, etc.)
- **Material**: ✅ Material flows (Dry Matter, Water Content, Carbon Content)
- **Good**: ✅ Implicit in your material flows (Rye Straw, Biochar, etc.)
- **Region**: ❌ Missing (only Geogr_Scope="Case_Study_Region")

## Proposed Excel Structure

### **🎯 Centralized Configuration Sheet**

**Sheet: `0_ODYM_Configuration`** (New - At the beginning)

| Section | Column A | Column B | Column C | Column D | Column E |
|---------|----------|----------|----------|----------|----------|
| **Model Info** | | | | | |
| | Model_Name | RyeStrawMFA | | | |
| | Time_Start | 2020 | | | |
| | Time_End | 2025 | | | |
| | Unit | Mg | | | |
| | Geogr_Scope | Case_Study_Region | | | |
| **Dimension Selection** | | | | | |
| | Dimension_Name | Use_Dimension | Items | Description | Index_Letter |
| | Time | TRUE | 2020,2021,2022,2023,2024,2025 | Model time | t |
| | Element | TRUE | material,WC,DM,CC | Chemical elements | e |
| | Process | TRUE | Harvest,Processing,Storage,Application | Process types | p |
| | Material | TRUE | Dry_Matter,Water_Content,Carbon_Content | Material types | m |
| | Good | TRUE | Rye_Straw,Biochar,Compost,Energy | Good types | g |
| | Region | FALSE | Case_Study_Region | Regional scope | r |
| | Cohort | FALSE | | Age-cohort | c |
| **Dimension Definitions** | | | | | |
| **Process Types** | Process_ID | Process_Name | Description | Type | Efficiency |
| | 1 | Harvest | Biomass harvesting | Primary | 0.9 |
| | 2 | Processing | Material processing | Secondary | 0.8 |
| | 3 | Storage | Material storage | Secondary | 0.95 |
| | 4 | Application | Material application | Tertiary | 0.85 |
| **Good Types** | Good_ID | Good_Name | Description | Category | Unit |
| | 1 | Rye_Straw | Primary biomass | Biomass | Mg |
| | 2 | Biochar | Carbonized material | Material | Mg |
| | 3 | Compost | Organic material | Material | Mg |
| | 4 | Energy | Energy output | Energy | MWh |
| **Material Types** | Material_ID | Material_Name | Description | Composition |
| | 1 | Dry_Matter | Dry matter content | Organic |
| | 2 | Water_Content | Water content | Inorganic |
| | 3 | Carbon_Content | Carbon content | Carbon |
| **Region Types** | Region_ID | Region_Name | Description | Geographic_Scope |
| | 1 | Case_Study_Region | Primary study area | Local |

### **🔄 Updated Flow Definition Sheets**

**Sheet: `1_1_Definition_Flows`** (Updated)
| Column | Description | Example Values |
|--------|-------------|----------------|
| Flow_ID | Unique identifier | 1, 2, 3 |
| Flow_Name | Flow name | "Rye_Harvest_Flow" |
| Flow_Output_Process_ID | Output process ID | 1 |
| Input_Process_ID | Input process ID | 2 |
| Flow_WC[%] | Water content % | 20 |
| Flow_DM[%] | Dry matter % | 80 |
| Flow_CC_DM[%] | Carbon content % | 45 |
| **Process_Type_ID** | **Reference to Process_ID** | **1** |
| **Good_ID** | **Reference to Good_ID** | **1** |
| **Material_ID** | **Reference to Material_ID** | **1** |
| **Region_ID** | **Reference to Region_ID** | **1** |

**Sheet: `1_2_Data_Flows`** (Updated)
| Column | Description | Example Values |
|--------|-------------|----------------|
| Flow_ID | Reference to Flow_ID | 1 |
| Flow_Data_Year | Year | 2020 |
| Flow_Material | Material amount | 1000 |
| **Process_Type_ID** | **Reference to Process_ID** | **1** |
| **Good_ID** | **Reference to Good_ID** | **1** |
| **Material_ID** | **Reference to Material_ID** | **1** |
| **Region_ID** | **Reference to Region_ID** | **1** |

**Sheet: `2_1_Definition_Processes`** (Updated)
| Column | Description | Example Values |
|--------|-------------|----------------|
| ID | Process ID | 1 |
| Process_Name | Process name | "Harvest_Process_A" |
| Process_Logic | Process logic | "DSM" |
| **Process_Type_ID** | **Reference to Process_ID** | **1** |
| **Region_ID** | **Reference to Region_ID** | **1** |

## Implementation Benefits

### **✅ Advantages of Your Approach**

1. **Centralized Configuration**: All ODYM dimensions in one place
2. **Flexible Selection**: Users can choose which dimensions to use
3. **Backward Compatibility**: Existing sheets work with added columns
4. **Clear Structure**: Easy to understand and maintain
5. **Scalable**: Easy to add new dimensions or modify existing ones

### **🎯 Key Insights**

1. **You already have most dimensions**: You just need to formalize them as ODYM classifications
2. **Region is the main missing piece**: But you can start with a single region
3. **Process types vs. individual processes**: You have individual processes, need to add process type classification
4. **Good vs. Material**: You have materials, need to distinguish goods from materials

## Recommended Implementation Steps

### **Phase 1: Create Configuration Sheet**
1. **Create `0_ODYM_Configuration` sheet** with dimension definitions
2. **Set up dimension selection** (TRUE/FALSE for each dimension)
3. **Define default values** for all dimensions

### **Phase 2: Update Existing Sheets**
1. **Add dimension reference columns** to existing sheets
2. **Set default values** (all flows/processes use default dimension values)
3. **Test backward compatibility**

### **Phase 3: Enable Multi-Dimensional Analysis**
1. **Populate dimension references** with actual values
2. **Test multi-dimensional calculations**
3. **Add optional data sheets** for richer analysis

## Data Loader Updates

### **Update `data_loader.py`**

```python
# Add to REQUIRED_STRUCTURE
REQUIRED_STRUCTURE = {
    "0_ODYM_Configuration": ["Dimension_Name", "Use_Dimension", "Items"],
    # Existing sheets (unchanged)
    "1_1_Definition_Flows": ["Flow_ID", "Flow_Name", "Flow_Output_Process_ID", "Input_Process_ID"],
    "1_2_Data_Flows": ["Flow_ID", "Flow_Data_Year", "Flow_Material"],
    "2_1_Definition_Processes": ["ID", "Process_Name", "Process_Logic"],
    # ... other existing sheets
}

# Add configuration loading function
def load_odym_configuration(excel_data_dict):
    """Load ODYM configuration from the configuration sheet."""
    config_sheet = excel_data_dict["0_ODYM_Configuration"]
    
    # Extract dimension selection
    dimensions = {}
    for _, row in config_sheet.iterrows():
        if pd.notna(row["Dimension_Name"]):
            dimensions[row["Dimension_Name"]] = {
                "use": row["Use_Dimension"] == "TRUE",
                "items": row["Items"].split(",") if pd.notna(row["Items"]) else [],
                "description": row["Description"],
                "index_letter": row["Index_Letter"]
            }
    
    return dimensions
```

### **Update `system_setup.py`**

```python
def define_model_scope_from_config(config_dimensions):
    """Define model scope from ODYM configuration."""
    model_classification = {}
    
    # Always include Time and Element
    model_classification["Time"] = msc.Classification(
        Name="Time", Dimension="Time", ID=1, Items=config_dimensions["Time"]["items"]
    )
    model_classification["Element"] = msc.Classification(
        Name="Elements", Dimension="Element", ID=2, Items=config_dimensions["Element"]["items"]
    )
    
    # Add other dimensions based on configuration
    dimension_id = 3
    for dim_name, dim_config in config_dimensions.items():
        if dim_config["use"] and dim_name not in ["Time", "Element"]:
            model_classification[dim_name] = msc.Classification(
                Name=dim_name, 
                Dimension=dim_name, 
                ID=dimension_id, 
                Items=dim_config["items"]
            )
            dimension_id += 1
    
    return model_classification
```

## Conclusion

Your centralized configuration approach is **much better** than my previous suggestions because:

1. **It's user-friendly**: All ODYM configuration in one place
2. **It's flexible**: Users can choose which dimensions to use
3. **It's maintainable**: Easy to modify and extend
4. **It's backward compatible**: Existing sheets work with minimal changes

**Would you like me to help you implement this centralized configuration approach?** We could start with:

1. Creating the `0_ODYM_Configuration` sheet structure
2. Updating the data loader to read the configuration
3. Modifying `system_setup.py` to use the configuration
4. Testing with your existing Excel templates

This approach will give you full ODYM compliance while maintaining the elegance and usability of your current system!

---

*Document Version: 1.0*  
*Last Updated: [Current Date]*  
*Author: BioDYM Development Team*
