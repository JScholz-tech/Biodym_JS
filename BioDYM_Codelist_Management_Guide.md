# BioDYM Codelist Management Guide

## Overview
This guide explains how to structure and manage codelists in Excel for the BioDYM validation macro, ensuring clean, maintainable data validation rules.

## Recommended Codelist Structure

### 1. **Dedicated Codelist Sheet**
Create a separate sheet called `Codelists` to store all your validation lists:

```
Sheet: "Codelists"
├── Table: "Complete?"
│   ├── Yes
│   └── No
├── Table: "Process_Logic"
│   ├── Input
│   ├── Output
│   ├── Pass-through
│   └── Transformation
├── Table: "TC_Configuration"
│   ├── Static
│   ├── Dynamic
│   └── None
└── Table: "Stock_Configuration"
    ├── Stock
    └── None
```

### 2. **Excel Table Format**
Use Excel Tables (Insert → Table) for each codelist:

| Column Name | Values |
|-------------|--------|
| Complete? | Yes |
| Complete? | No |
| Process_Logic | Input |
| Process_Logic | Output |
| Process_Logic | Pass-through |
| Process_Logic | Transformation |

### 3. **Named Ranges (Alternative)**
You can also use named ranges:

```
Name: "Complete?"
Refers to: =Codelists!$A$2:$A$3

Name: "Process_Logic"  
Refers to: =Codelists!$B$2:$B$5
```

## Enhanced Macro Features

### **Smart Codelist Detection**
The enhanced macro automatically detects codelists for each column:

1. **Table-based**: Looks for Excel tables with matching column names
2. **Named Range**: Checks for named ranges matching column names
3. **Fallback**: Uses input-only validation if no codelist found

### **Codelist Management Functions**

#### **CreateCodelistTable(sheetName, columnName, tableName)**
- Extracts unique values from existing data
- Creates a new table in the Codelists sheet
- Automatically updates validation rules

#### **AddManualCodelistValidation(sheetName, columnName, values)**
- Manually adds codelist validation
- Values provided as comma-separated string
- Useful for predefined lists

#### **ShowCodelistOptions()**
- Interactive menu for codelist management
- Easy access to all codelist functions

## Step-by-Step Setup

### **Step 1: Create Codelist Sheet**
1. Insert new worksheet named `Codelists`
2. Add headers for each codelist type
3. Create Excel tables for each codelist

### **Step 2: Define Your Codelists**

#### **Process Logic Codelist**
| Process_Logic |
|---------------|
| Input |
| Output |
| Pass-through |
| Transformation |

#### **Configuration Codelists**
| Complete? | TC_Configuration | Stock_Configuration |
|-----------|------------------|-------------------|
| Yes | Static | Stock |
| No | Dynamic | None |
| | None | |

#### **Source Type Codelist**
| Type_Source |
|-------------|
| Literature |
| Measurement |
| Estimate |
| Database |
| Expert Knowledge |

### **Step 3: Run Enhanced Macro**
The macro will automatically:
- Detect existing codelists
- Apply dropdown validation where codelists exist
- Use input-only validation for other fields
- Add comments to header cells
- Add validation messages to data cells

## Best Practices

### **1. Consistent Naming**
- Use exact column names for table names
- Keep naming consistent across sheets
- Use clear, descriptive names

### **2. Data Organization**
- One table per codelist type
- Keep values in single column
- Remove duplicates and empty cells

### **3. Maintenance**
- Update codelists when requirements change
- Use `UpdateValidation()` to refresh all rules
- Test validation on sample data

### **4. Documentation**
- Document codelist meanings
- Keep validation sheet updated
- Maintain change log

## Example Usage

### **Creating Codelist from Existing Data**
```vba
' Extract unique values from Process_Logic column
Call CreateCodelistTable("2_1_Definition_Processes", "Process_Logic", "Process_Logic")
```

### **Adding Manual Codelist**
```vba
' Add manual validation for Complete? field
Call AddManualCodelistValidation("1_1_Definition_Flows", "Complete?", "Yes,No")
```

### **Running Enhanced Validation**
```vba
' Apply all validation rules (including codelists)
Call ApplyValidationInstructions()
```

## Troubleshooting

### **Codelist Not Detected**
- Check table name matches column name exactly
- Verify table is in Codelists sheet
- Ensure table has data

### **Validation Not Applied**
- Run `UpdateValidation()` to refresh
- Check for typos in sheet/column names
- Verify codelist structure

### **Performance Issues**
- Limit codelist size (< 100 items)
- Use tables instead of large ranges
- Clear validation before reapplying

## Migration from Existing Validation

### **Step 1: Backup Current Rules**
- Document existing validation rules
- Save current workbook as backup

### **Step 2: Extract Codelists**
- Identify columns with dropdown validation
- Extract unique values to Codelists sheet
- Create tables for each codelist

### **Step 3: Update Validation Sheet**
- Ensure validation sheet has all required columns
- Add instructions for codelist fields

### **Step 4: Run Enhanced Macro**
- Clear existing validation
- Apply new validation with codelist support
- Test on sample data

## Benefits of This Approach

### **1. Maintainability**
- Centralized codelist management
- Easy to update validation rules
- Consistent across all sheets

### **2. Flexibility**
- Mix of codelist and input-only validation
- Easy to add new codelists
- Supports both table and named range approaches

### **3. User Experience**
- Clear dropdown options for users
- Helpful validation messages
- Consistent interface across sheets

### **4. Data Quality**
- Prevents invalid entries
- Enforces data consistency
- Reduces data entry errors

---

**Next Steps:**
1. Create your Codelists sheet with tables
2. Run the enhanced macro
3. Test validation on sample data
4. Adjust codelists as needed
5. Document your codelist structure
