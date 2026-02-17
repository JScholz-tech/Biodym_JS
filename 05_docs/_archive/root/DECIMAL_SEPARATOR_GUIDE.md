# Decimal Separator Unification Guide

**Issue**: BioDYM has inconsistent decimal separator handling (comma vs point)
**Solution**: Standardize on DOT (.) as decimal separator everywhere
**Date**: 2025-11-08

---

## 📋 **Current Situation**

### Where Commas Are Currently Used/Expected

| File | Line | Code | Issue |
|------|------|------|-------|
| `00_BioDYM_Workflow.py` | 107 | `decimal=','` | Expects comma in Excel |
| `system_setup.py` | 191 | `decimal=','` | Expects comma in Excel |
| `enhanced_sankey.py` | 46, 221 | `.replace(',', '.')` | Manual conversion |
| `visualization_loader.py` | 40 | `.replace(',', '.')` | Manual conversion |

### Why This is Problematic

1. **User Confusion**: Should I use "0.5" or "0,5" in Excel?
2. **Regional Settings**: German Excel uses comma, English uses dot
3. **Inconsistency**: Some sheets might have mixed formats
4. **Errors**: `pd.read_excel(decimal=',')` fails if file has dots

---

## ✅ **Unified Solution**

### Rule: **Always Use DOT (.) Everywhere**

**In Excel Files**:
- Transfer Coefficients: `0.85` ✅ not `0,85` ❌
- Positions: `0.50` ✅ not `0,5` ❌
- All numeric values: `123.456` ✅ not `123,456` ❌

**In Python Code**:
- Remove `decimal=','` parameter
- Remove all `.replace(',', '.')` conversions
- Use native pandas float parsing

**Benefits**:
- ✅ Works in all regions (Germany, US, UK, etc.)
- ✅ No conversion overhead
- ✅ Consistent with Python/pandas defaults
- ✅ Excel compatibility (Excel understands both, exports as dot)

---

## 🔧 **Code Changes Required**

### Change #1: Update Main Workflow

**File**: `00_BioDYM_Workflow.py`

**Current** (Line 107):
```python
input_data = pd.read_excel(
    input_file, sheet_name=None, header=0, engine='openpyxl',
    na_values=['N.A.', 'NA', 'n/a'], decimal=','  # ❌ REMOVE THIS
)
```

**Fixed**:
```python
input_data = pd.read_excel(
    input_file, sheet_name=None, header=0, engine='openpyxl',
    na_values=['N.A.', 'NA', 'n/a']  # ✅ Use default (dot)
)
```

### Change #2: Update System Setup

**File**: `02_src/system_setup.py`

**Current** (Line 191):
```python
decimal=','  # ❌ REMOVE THIS
```

**Fixed**:
```python
# Use default decimal separator (dot) for international compatibility
```

### Change #3: Simplify Enhanced Sankey

**File**: `02_src/plotting/enhanced_sankey.py`

**Current** (Lines 46, 221):
```python
def _safe_float_convert(value, default=0.0):
    try:
        return float(str(value).replace(',', '.'))  # ❌ Unnecessary conversion
    except (ValueError, AttributeError):
        return default
```

**Fixed**:
```python
def _safe_float_convert(value, default=0.0):
    """Convert value to float, handling NaN and invalid values."""
    try:
        if pd.isna(value):
            return default
        return float(value)  # ✅ Direct conversion, expects dot
    except (ValueError, TypeError, AttributeError):
        return default
```

### Change #4: Simplify Visualization Loader

**File**: `02_src/plotting/visualization_loader.py`

**Current** (Lines 33-40):
```python
def _convert_df_decimal_columns(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    """Converts comma-based decimal strings to dot-based floats."""
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(',', '.', regex=False),
                errors='coerce'
            )
    return df
```

**Fixed**:
```python
def _ensure_numeric_columns(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    """Ensure specified columns are numeric (float), with NaN for invalid values."""
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')  # ✅ Simple, expects dot
    return df
```

---

## 📝 **Excel File Requirements**

### For Users Creating New Case Studies

**Rule**: Always use DOT (.) as decimal separator in Excel

#### Example Values

| Sheet | Column | ❌ Wrong (Comma) | ✅ Correct (Dot) |
|-------|--------|------------------|------------------|
| `2_2_static_TCs` | E1_value | 0,85 | **0.85** |
| `6_1_Visualization_Processes` | X_Position_Material | 0,5 | **0.5** |
| `6_3_Layout_Configuration` | Zoom_Factor | 1,2 | **1.2** |
| `1_2_Data_Flows` | E1_value | 123,45 | **123.45** |

#### How to Ensure Dots in Excel

**Method 1: Regional Settings** (Recommended)
1. In Excel: File → Options → Advanced → Editing options
2. **Uncheck** "Use system separators"
3. Set Decimal separator = `.` (dot)
4. Set Thousands separator = `,` (comma)

**Method 2: Direct Input**
- Type numbers with dot: `0.85`, `123.45`
- Excel will respect your input

**Method 3: Find & Replace** (For existing files with commas)
1. Select all numeric cells
2. Ctrl+H (Find & Replace)
3. Find: `,` (comma)
4. Replace: `.` (dot)
5. Replace All

---

## 🧪 **Testing the Changes**

### Test Case 1: Load Excel with Dots

```python
# Should work without errors
df = pd.read_excel('test.xlsx', sheet_name='2_2_static_TCs')
print(df['E1_value'].dtype)  # Should be float64
print(df['E1_value'].head())  # Should show: 0.85, 0.92, etc.
```

### Test Case 2: Enhanced Sankey Positions

```python
# Should parse correctly
from plotting.enhanced_sankey import _safe_float_convert

value = "0.85"  # From Excel with dot
result = _safe_float_convert(value)
assert result == 0.85  # ✅ Pass
```

### Test Case 3: Visualization Loader

```python
df = pd.DataFrame({'X_Position': ['0.5', '0.75', '0.9']})
df = _ensure_numeric_columns(df, ['X_Position'])
assert df['X_Position'].dtype == 'float64'  # ✅ Pass
```

---

## 📦 **Migration Guide for Existing Files**

### If You Have Old Files with Commas

**Option A: Manual Fix in Excel** (Recommended)
1. Open file in Excel
2. Select all numeric columns
3. Find & Replace: `,` → `.`
4. Save

**Option B: Python Script** (Automated)

```python
import pandas as pd

# Load with comma decimal
df_old = pd.read_excel('old_file.xlsx', sheet_name='2_2_static_TCs', decimal=',')

# Convert all numeric columns
numeric_cols = df_old.select_dtypes(include=['float64', 'int64']).columns
for col in numeric_cols:
    df_old[col] = df_old[col]  # Already numeric, just ensure format

# Save with dot decimal (pandas default)
with pd.ExcelWriter('new_file.xlsx', engine='openpyxl') as writer:
    df_old.to_excel(writer, sheet_name='2_2_static_TCs', index=False)

print("✅ Converted: commas → dots")
```

**Option C: Keep Old Code Temporarily**

If you have many old files, keep `decimal=','` as a **temporary option**:

```python
# In config or as command-line argument
DECIMAL_SEPARATOR = ','  # or '.' after migration

input_data = pd.read_excel(
    input_file,
    decimal=DECIMAL_SEPARATOR if DECIMAL_SEPARATOR == ',' else None
)
```

---

## 🎯 **Recommended Implementation Order**

### Phase 1: Update Code (No Breaking Changes)

1. ✅ Make `_safe_float_convert()` robust (handles both comma and dot)
2. ✅ Add deprecation warning when commas detected
3. ✅ Update documentation

### Phase 2: Update Excel Template

4. ✅ Create new template with all dots: `BioDYM_ODYM_Template_v2.xlsm`
5. ✅ Add note in `0_Configuration`: "Use dot (.) as decimal separator"

### Phase 3: Migrate Existing Files

6. ✅ Run migration script on all files in `01_data/01_input/`
7. ✅ Verify calculations unchanged

### Phase 4: Remove Comma Support

8. ✅ Remove `decimal=','` from all code
9. ✅ Remove `.replace(',', '.')` conversions
10. ✅ Update all documentation

---

## ✅ **Benefits After Unification**

1. **Clarity**: Users know exactly what to use (always dot)
2. **Compatibility**: Works in all regions (Germany, US, UK, etc.)
3. **Performance**: No conversion overhead
4. **Reliability**: No format-related crashes
5. **Standards**: Aligned with Python/pandas/ODYM conventions
6. **Future-proof**: Compatible with internationalization

---

## 📚 **Documentation Updates Needed**

### Update These Files:

1. **README.md**: Add section "Data Format Requirements"
   ```markdown
   ## Data Format Requirements

   BioDYM uses **DOT (.)** as decimal separator in all Excel files.

   ✅ Correct: `0.85`, `123.45`
   ❌ Wrong: `0,85`, `123,45`
   ```

2. **Excel Template**: Add note in `0_Configuration` sheet
   ```
   IMPORTANT: Use dot (.) as decimal separator everywhere
   Examples: 0.85, 123.45, 0.5
   ```

3. **User Guide**: Add "Common Mistakes" section
   ```markdown
   ### Common Mistake: Using Commas

   If you see errors like "could not convert string to float: '0,85'":
   - Your Excel has commas instead of dots
   - Fix: Find & Replace all `,` with `.` in numeric columns
   ```

---

## 🔧 **Quick Fix for Your Current File**

For `251108_BioDYM_ODYM_CS1_Whaeat_Straw.xlsm`:

**Check if you have commas or dots**:
1. Open Excel
2. Go to any sheet with numbers (e.g., `2_2_static_TCs`)
3. Look at E1_value column

**If you see commas** (0,85):
1. Select all numeric columns
2. Ctrl+H
3. Find: `,` → Replace: `.`
4. Replace All
5. Save

**If you see dots** (0.85):
- ✅ You're already compliant!
- Code will work after we remove `decimal=','`

---

**Last Updated**: 2025-11-08
**Status**: Ready for implementation
**Priority**: HIGH - Affects data loading reliability
