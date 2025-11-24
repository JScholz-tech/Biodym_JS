# How to Add Column Comments to BioDYM Template

## Overview

This guide explains how to add descriptive comments to all column headers in the BioDYM template using the validation data and VBA macro.

---

## Files Created

1. **`7_1_Comments_Validation_NEW.csv`** - Validation data with column descriptions (69 entries for input columns)
2. **`Add_Column_Comments_Macro.bas`** - VBA macro to apply comments
3. **`HOW_TO_ADD_COMMENTS.md`** - This file (instructions)

---

## Step-by-Step Instructions

### Step 1: Copy Your Template

**IMPORTANT**: Do NOT modify the original template!

1. Make a copy of your template file:
   ```
   251124_BioDYM_ODYM_Template_Empty.xlsm
   →
   251124_BioDYM_ODYM_Template_WithComments.xlsm
   ```

2. Work with the COPY from now on

---

### Step 2: Import the VBA Macro

1. Open your **COPY** of the template in Excel

2. Press `ALT + F11` to open the VBA Editor

3. In the VBA Editor:
   - Click **File** → **Import File**
   - Navigate to: `Add_Column_Comments_Macro.bas`
   - Select and import it

4. You should now see `Add_Column_Comments` module in the VBA Project Explorer

---

### Step 3: Run the Macro

1. Still in VBA Editor, click **Run** → **Run Sub/UserForm** (or press `F5`)

2. Select `AddCommentsFromCSV` from the list

3. Click **Run**

4. The macro will:
   - Read `7_1_Comments_Validation_NEW.csv`
   - Add comments to all matching columns
   - Show progress in Immediate Window (View → Immediate Window to see)
   - Display success message when complete

5. **Expected Result**:
   ```
   Successfully added: 69
   Skipped (already exist): 0
   Errors: 0
   ```

---

### Step 4: Verify Comments

1. Close VBA Editor

2. Go to any data sheet (e.g., `1_1_Definition_Flows`)

3. Hover over column headers to see comments:
   - **Flow_ID**: Shows purpose, action, example
   - **Flow_Name**: Shows descriptive guidance
   - **E1_TC_Value[%]**: Shows calculation details

4. Comments display as yellow tooltips when hovering

---

## Troubleshooting

### "File Not Found" Error

**Problem**: Macro can't find CSV file

**Solution**:
1. Ensure `7_1_Comments_Validation_NEW.csv` is in the **same folder** as your template
2. Check the file name exactly matches (case-sensitive)

---

### "Sheet Not Found" Errors

**Problem**: Macro reports sheets not found

**Solution**: This is normal if template doesn't have all sheets yet. Check error count in final message - should be low.

---

### Comments Not Appearing

**Problem**: Ran macro but comments don't show

**Solution**:
1. Make sure Excel comments are enabled (File → Options → Advanced → Display section → check "Indicators and comments")
2. Try hovering directly over cell (comments show on hover by default)

---

### Want to Update Comments?

**Problem**: Made changes to validation data and want to re-apply

**Solution**:
1. Run `ForceUpdateComments` macro (replaces all existing comments)
2. Or manually delete comments first: Run `RemoveAllComments`, then `AddCommentsFromCSV`

---

## What Gets Comments?

### Input Columns (Focus Areas)
- Flow definitions and data values
- Process configurations
- TC values (static and dynamic)
- DSM/FOMP parameters
- Initial stock values
- Uncertainty parameters
- Scenario definitions
- References

### System Columns (Brief Generic)
- `Complete?` - Completion flag
- `ID` - Auto-generated identifier
- `ODYM_*` - Framework fields (generic description for all)

### Pattern Columns
- `E#_*` columns (E1-E6) - Automatically applied to all element columns

---

## Validation Data Structure

The CSV file contains:

| Column | Description |
|--------|-------------|
| Sheet_Name | Which sheet this applies to (or "SYSTEM" for all sheets) |
| Column_Name | Exact column name (or pattern like "E#_TC_Value") |
| Category | Type: Input, Config, Reference, Identifier, System |
| Required | Is it mandatory? (Yes/No/Conditional) |
| Description | Full comment text (PURPOSE/ACTION/EXAMPLE/NOTE) |

---

## Tips

1. **Comments format**: Multi-line with clear structure:
   ```
   PURPOSE: Why this field exists
   ACTION: What to enter
   EXAMPLE: Sample value
   NOTE: Additional context (if needed)
   ```

2. **Comment width**: Set to 300 pixels for readability

3. **Auto-size**: Comments adjust height to fit content

4. **Backup**: Always keep the original template without comments as master

---

## Advanced: Updating Validation Data

If you need to modify descriptions:

1. Edit `generate_validation.py` script

2. Run: `uv run python generate_validation.py`

3. New CSV file generated

4. Import macro and run `ForceUpdateComments` on template copy

---

## Support

For questions about:
- **Comment content**: Check validation data or ask development team
- **Macro issues**: Check VBA error messages in Immediate Window
- **Missing columns**: Some columns may not need comments (calculated fields, deprecated columns)

---

**Last Updated**: 2024-11-24
**Version**: 1.0
**Generated for**: BioDYM v1.0 Template
