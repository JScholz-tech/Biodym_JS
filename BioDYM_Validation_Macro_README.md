# BioDYM Excel Validation Macro

## Overview
This VBA macro automatically applies validation instructions from the `7_1_Comments_Validation` sheet to all data sheets in the BioDYM Excel workbook. It reads validation instructions and applies appropriate data validation rules, comments, and input messages.

## Features

### 🎯 **Automatic Field Detection**
- **Auto-Generated Fields**: IDs, Process_IDs, Flow_IDs (comments only, no validation)
- **Configuration Fields**: Dropdown lists for Complete?, Process_Logic, TC_Configuration, etc.
- **Percentage Fields**: WC[%], DM[%], CC[%] with 0-100% validation
- **Name Fields**: Text validation for Flow_Name, Process_Name, etc.
- **Value Fields**: Number validation for amounts, years, transfer coefficients
- **Source Fields**: Text validation for Author_Source, Type_Source

### 🔧 **Smart Validation Rules**
- **Dropdown Lists**: Predefined options for configuration fields
- **Range Validation**: Percentage (0-100%), Years (2000-2100), Positive numbers
- **Input Messages**: Helpful instructions when users click on cells
- **Error Messages**: Clear feedback for invalid entries
- **Comments**: Detailed guidance accessible via cell comments

### 📋 **Field-Specific Handling**

#### **Process Logic Fields**
- **Input**: Receives only
- **Output**: Produces only  
- **Pass-through**: No transformation
- **Transformation**: Converts materials
- **Troubleshooting**: Splitter vs Transformer guidance

#### **Transfer Coefficient Configuration**
- **Static**: Constant TCs over time
- **Dynamic**: Time-varying TCs
- **None**: Skip TC calculations

#### **Stock Configuration**
- **Stock**: Maintains material stocks
- **None**: No stock calculations

## Installation Instructions

### 1. **Enable VBA in Excel**
1. Open Excel
2. Go to `File` → `Options` → `Trust Center` → `Trust Center Settings`
3. Select `Macro Settings`
4. Choose `Enable all macros` or `Disable all macros with notification`

### 2. **Add Macro to Workbook**
1. Open your BioDYM Excel file
2. Press `Alt + F11` to open VBA Editor
3. Right-click on your workbook name in Project Explorer
4. Select `Insert` → `Module`
5. Copy and paste the entire macro code from `BioDYM_Validation_Macro.vba`
6. Save the workbook as `.xlsm` (Excel Macro-Enabled Workbook)

### 3. **Create Macro Buttons (Optional)**
1. Go to `Developer` tab → `Insert` → `Form Controls` → `Button`
2. Draw button on worksheet
3. Assign macro: `ApplyValidationInstructions`
4. Repeat for other utility macros

## Usage Instructions

### **Main Functions**

#### **ApplyValidationInstructions**
- **Purpose**: Main function to apply all validation instructions
- **Usage**: Run this after updating the validation sheet
- **Process**: Reads validation sheet → Applies to all data sheets

#### **UpdateValidationInstructions**
- **Purpose**: Clear existing validation and reapply
- **Usage**: Use when validation sheet has been updated
- **Process**: Clear all → Reapply all

#### **ClearAllValidation**
- **Purpose**: Remove all validation and comments
- **Usage**: Clean slate before reapplying
- **Process**: Deletes all validation rules and comments

#### **ShowValidationStatus**
- **Purpose**: Display current validation status
- **Usage**: Check how many validations are applied
- **Output**: Count of validations and comments applied

### **Running the Macro**

#### **Method 1: VBA Editor**
1. Press `Alt + F11`
2. Select `ApplyValidationInstructions` in Project Explorer
3. Press `F5` or click `Run`

#### **Method 2: Macro Dialog**
1. Press `Alt + F8`
2. Select `ApplyValidationInstructions`
3. Click `Run`

#### **Method 3: Button (if created)**
1. Click the macro button on worksheet

## Updating the Macro

### **When to Update**
- Validation instructions change
- New field types added
- New sheets added to workbook
- Validation rules need modification

### **How to Update**

#### **1. Update Validation Sheet**
- Modify instructions in `7_1_Comments_Validation` sheet
- Ensure all required columns are filled:
  - `Name_sheet`: Target sheet name
  - `Name_Column`: Target column name
  - `Titel:`: Validation title
  - `Body:`: Input message
  - `Purpose:`: Field purpose
  - `Action:`: Action instruction
  - `Note:`: Additional notes

#### **2. Run Update Macro**
```vba
Sub UpdateValidationInstructions()
    Call ClearAllValidation
    Call ApplyValidationInstructions
End Sub
```

#### **3. Add New Field Types**
To add new field types, modify the `DetermineFieldType` function:

```vba
Function DetermineFieldType(columnName As String) As String
    ' Add new conditions here
    If InStr(columnName, "NewFieldType") > 0 Then
        fieldType = "NewFieldType"
    ' ... existing conditions
End Function
```

#### **4. Add New Validation Rules**
Create new validation subroutines:

```vba
Sub AddNewFieldTypeValidation(rng As Range, title As String, body As String, note As String)
    ' Add your validation logic here
End Sub
```

## Validation Sheet Structure

### **Required Columns**
| Column | Description | Example |
|--------|-------------|---------|
| `Name_sheet` | Target sheet name | `1_1_Definition_Flows` |
| `Name_Column` | Target column name | `Flow_Name` |
| `Titel:` | Validation title | `Definition of Flow Name` |
| `Body:` | Input message | `Enter the name of the flow` |
| `Purpose:` | Field purpose | `Defines the Flow Name for identification` |
| `Action:` | Action instruction | `Enter a comprehensive flow name` |
| `Note:` | Additional notes | `Use descriptive names for clarity` |

### **Field Type Examples**

#### **Auto-Generated Fields**
- `ID`, `Process_ID`, `Flow_ID`, `TC_ID`
- Only comments applied, no data validation

#### **Configuration Fields**
- `Complete?`, `Process_Logic`, `TC_Configuration`
- Dropdown validation with predefined options

#### **Percentage Fields**
- `WC[%]`, `DM[%]`, `CC[%]`
- Range validation (0-100%)

#### **Name Fields**
- `Flow_Name`, `Process_Name`, `Description`
- Text validation with length requirements

#### **Value Fields**
- `Flow_Material`, `TC_Value_material`, `Year`
- Number validation with appropriate ranges

## Troubleshooting

### **Common Issues**

#### **Macro Not Running**
- Check macro security settings
- Ensure workbook is saved as `.xlsm`
- Verify VBA code is properly pasted

#### **Validation Not Applied**
- Check validation sheet structure
- Verify sheet and column names match exactly
- Check for typos in field names

#### **Error Messages**
- Check VBA Editor for error details
- Ensure all required columns are filled
- Verify target sheets exist

#### **Performance Issues**
- Use `Application.ScreenUpdating = False` (already included)
- Process large workbooks in smaller batches
- Clear validation before reapplying

### **Debug Mode**
Enable debug mode by adding this line at the beginning of `ApplyValidationInstructions`:

```vba
Debug.Print "Processing: " & targetSheet & "." & targetColumn
```

## Customization Options

### **Modify Validation Rules**
Edit the validation subroutines to change:
- Input message format
- Error message text
- Validation criteria
- Comment content

### **Add New Field Types**
1. Add condition to `DetermineFieldType`
2. Create new validation subroutine
3. Add case to `ApplyValidationToSheet`

### **Customize Messages**
Modify the message templates in each validation subroutine:
- Input messages
- Error messages
- Comment text

## Best Practices

### **Before Running**
1. **Backup** your workbook
2. **Test** on a copy first
3. **Verify** validation sheet is complete
4. **Check** sheet and column names

### **After Running**
1. **Test** validation on sample data
2. **Verify** all fields have appropriate validation
3. **Check** error messages are helpful
4. **Document** any custom modifications

### **Maintenance**
1. **Update** validation sheet when adding new fields
2. **Re-run** macro after structural changes
3. **Monitor** user feedback on validation messages
4. **Keep** macro code versioned and documented

## Support

### **Macro Functions Reference**
- `ApplyValidationInstructions()`: Main execution function
- `DetermineFieldType()`: Field type detection
- `CreateCombinedNote()`: Note formatting
- `ApplyValidationToSheet()`: Sheet-specific application
- `AddDropdownValidation()`: Dropdown validation
- `AddPercentageValidation()`: Percentage validation
- `AddTextValidation()`: Text validation
- `AddNumberValidation()`: Number validation
- `ClearAllValidation()`: Cleanup function
- `UpdateValidationInstructions()`: Update function
- `ShowValidationStatus()`: Status reporting

### **Error Handling**
The macro includes comprehensive error handling:
- Sheet existence checking
- Column existence verification
- Data range validation
- Graceful error recovery

### **Logging**
Debug information is printed to the Immediate Window:
- Processing status
- Field type detection
- Validation application results
- Error details

---

**Version**: 1.0  
**Last Updated**: 2024  
**Compatibility**: Excel 2016+ with VBA support
