# Sankey Visualization Problems - Comprehensive Analysis

## 🚨 **Current Status: CRITICAL ISSUES**

The Enhanced Sankey diagram in the BioDYM MFA Tool has several critical issues that make it practically unusable. This document provides a comprehensive analysis of all known problems and their root causes.

---

## 📊 **Problem Overview**

### **Primary Issues**
1. **Flows Going Outside Window Boundaries** - Most critical issue
2. **Element-Specific Positioning Not Working** - Major functionality issue  
3. **Zoom Factor Ineffective** - User control not working
4. **Node Position Inconsistency** - Visual disruption when switching elements
5. **Excel Data Quality Issues** - Configuration problems

### **Impact Assessment**
- **Usability**: ❌ **CRITICAL** - Diagram is unreadable due to flows outside window
- **Functionality**: ❌ **MAJOR** - Element switching doesn't work as intended
- **User Experience**: ❌ **POOR** - Controls don't work, positioning is inconsistent
- **Data Quality**: ⚠️ **MODERATE** - Excel configuration has issues

---

## 🔍 **Detailed Problem Analysis**

### **1. Flows Going Outside Window Boundaries** 🚨 **CRITICAL**

#### **Problem Description**
- Flow connections extend beyond the visible plot area
- Users cannot see complete flow connections
- Diagram becomes unreadable and unusable

#### **Root Causes**
1. **Plotly Sankey Auto-Routing**: Plotly automatically routes flows between nodes, ignoring window boundaries
2. **No Flow Constraint Logic**: No validation that flows stay within plot margins
3. **Inadequate Boundary Management**: Node positions don't account for flow routing space
4. **Missing Margin Enforcement**: No padding around plot area for flow routing

#### **Technical Details**
```python
# Current problematic code
fig = go.FigureWidget(go.Sankey(
    node=dict(x=[], y=[]),  # Positions set but flows ignore boundaries
    link=dict(source=[], target=[], value=[])  # No boundary constraints
))
```

#### **Expected Behavior**
- All flows should be visible within the plot window
- Flows should respect plot margins and padding
- Auto-fit should constrain both nodes and flows

#### **Current Behavior**
- Flows extend beyond plot boundaries
- No constraint on flow routing
- Auto-fit only affects node positions, not flows

---

### **2. Element-Specific Positioning Not Working** 🚨 **MAJOR**

#### **Problem Description**
- When switching between elements (Material, WC, DM, CC), nodes don't use their specific Excel-defined positions
- All elements appear to use the same positions (likely Material positions)
- Element-specific positioning system is not functioning

#### **Root Causes**
1. **Case Sensitivity Issues**: Excel columns `X_Position_WC` vs code looking for `X_Position_wc`
2. **Position Lookup Logic Errors**: Element-specific position lookup not working correctly
3. **Excel Data Quality**: Some rows have NaN values affecting position loading
4. **Fallback Logic Problems**: System falls back to general positions instead of element-specific ones

#### **Technical Details**
```python
# Current problematic logic
if element:
    element_name = element.upper()  # WC, DM, CC
    element_x_key = f'X_Position_{element_name}'  # X_Position_WC
    # But Excel has X_Position_WC, X_Position_DM, X_Position_CC
```

#### **Expected Behavior**
- Material: Use `X_Position_Material` / `Y_Position_Material`
- WC: Use `X_Position_WC` / `Y_Position_WC`  
- DM: Use `X_Position_DM` / `Y_Position_DM`
- CC: Use `X_Position_CC` / `Y_Position_CC`

#### **Current Behavior**
- All elements use Material positions
- Element-specific positions are ignored
- No visual difference when switching elements

---

### **3. Zoom Factor Ineffective** ⚠️ **MAJOR**

#### **Problem Description**
- Zoom settings don't work as expected
- Zoom scales window size instead of content
- Flows still escape boundaries even with zoom

#### **Root Causes**
1. **Wrong Zoom Implementation**: `effective_width = window_width * zoom_factor` scales window, not content
2. **No Content Scaling**: Zoom doesn't scale the actual diagram content
3. **Missing Flow Constraints**: Zoom doesn't affect flow routing boundaries

#### **Technical Details**
```python
# Current problematic zoom logic
effective_width = int(window_width * zoom_factor)  # Scales window size
effective_height = int(window_height * zoom_factor)  # Not content size
```

#### **Expected Behavior**
- Zoom should scale diagram content to fit within window
- Flows should be constrained by zoom level
- Content should scale proportionally

#### **Current Behavior**
- Zoom increases window size
- Content doesn't scale properly
- Flows still escape boundaries

---

### **4. Node Position Inconsistency** ⚠️ **MODERATE**

#### **Problem Description**
- Node positions change when switching between elements
- Visual disruption when changing material levels
- Inconsistent layout across different views

#### **Root Causes**
1. **Process Filtering Before Positioning**: System filters processes based on flows before calculating positions
2. **Position Recalculation**: When fewer processes have flows, positions are recalculated
3. **Lost Custom Layout**: Excel-defined layouts get overridden

#### **Technical Details**
```python
# Current problematic logic
filtered_processes = [p for p in all_processes if p.Name in processes_to_show]
# Then uses filtered_processes for positioning - WRONG!
```

#### **Expected Behavior**
- Node positions should remain consistent across all elements
- Only flows should change when switching elements
- Excel-defined layouts should be preserved

#### **Current Behavior**
- Positions change when switching elements
- Layout becomes inconsistent
- Excel positions are overridden

---

### **5. Excel Data Quality Issues** ⚠️ **MODERATE**

#### **Problem Description**
- Excel file contains NaN values in Process_ID and Name(EN) columns
- Some position data may be missing or invalid
- Data structure inconsistencies

#### **Root Causes**
1. **Data Entry Issues**: Some rows have incomplete data
2. **Format Inconsistencies**: Mixed data types in position columns
3. **Missing Validation**: No data quality checks

#### **Technical Details**
```python
# Excel data issues
Process_ID: [0, 1, 2, ..., NaN, NaN, NaN]  # Rows 11+ have NaN
Name(EN): ['Atmosphere', 'Environment', ..., NaN, NaN, NaN]
```

#### **Expected Behavior**
- All processes should have valid IDs and names
- All position data should be complete
- Data should be in correct format (0-1 range for positions)

#### **Current Behavior**
- Some processes have NaN values
- Position loading may fail for some processes
- Data quality issues cause errors

---

## 🎯 **Plotly Sankey Requirements vs Current Implementation**

### **Plotly Requirements**
Based on [Plotly Sankey documentation](https://plotly.com/python/sankey-diagram/#hovertemplate-and-customdata-of-sankey-diagrams):

#### **Node Requirements**
- `label`: List of node names (required)
- `x`, `y`: Coordinates 0-1 (optional, for manual positioning)
- `color`: Node colors (optional)
- `pad`: Vertical spacing (optional)
- `thickness`: Node width (optional)
- `line`: Border styling (optional)
- `align`: Node alignment (optional)

#### **Link Requirements**
- `source`: Source node indices (required)
- `target`: Target node indices (required)
- `value`: Flow values (required)
- `color`: Link colors (optional)
- `label`: Link labels (optional)
- `arrowlen`: Arrow length (optional)

#### **Layout Requirements**
- `arrangement`: "snap", "perpendicular", "freeform", "fixed"
- `width`, `height`: Figure dimensions in pixels

### **Current Implementation Issues**
1. **Missing `arrangement="fixed"`**: Not using manual positioning mode
2. **Incorrect Position Usage**: Not properly using `node.x` and `node.y`
3. **No Flow Constraints**: No boundary management for flows
4. **Wrong Zoom Logic**: Scaling window instead of content
5. **Missing Layout Options**: No arrangement or alignment controls

---

## 🔧 **Technical Root Causes**

### **1. Plotly Limitations Not Addressed**
- **Auto-Routing**: Plotly automatically routes flows, ignoring boundaries
- **No Flow Control**: Limited control over flow path geometry
- **Manual Positioning**: Requires `arrangement="fixed"` for manual control

### **2. Implementation Errors**
- **Wrong Positioning Logic**: Using filtered processes for positioning
- **Incorrect Zoom**: Scaling window size instead of content
- **Missing Constraints**: No boundary validation for flows
- **Poor Data Handling**: Not handling Excel data quality issues

### **3. Configuration Problems**
- **Excel Data Quality**: NaN values and format issues
- **Missing Settings**: No arrangement, alignment, or constraint settings
- **Inconsistent Naming**: Case sensitivity issues in column names

---

## 📋 **Priority Fix List**

### **Priority 1: Critical Fixes** 🚨
1. **Fix Flow Boundary Management**
   - Implement flow constraint logic
   - Add margin enforcement
   - Ensure flows stay within plot area

2. **Fix Zoom Implementation**
   - Scale content, not window size
   - Implement proper content scaling
   - Add flow boundary constraints

3. **Fix Element-Specific Positioning**
   - Debug position lookup logic
   - Fix case sensitivity issues
   - Clean up Excel data quality

### **Priority 2: Important Fixes** ⚠️
4. **Implement Proper Plotly Arrangement**
   - Use `arrangement="fixed"` for manual positioning
   - Add arrangement options to Excel config
   - Implement proper node positioning

5. **Add Layout Controls**
   - Node alignment options
   - Arrow links support
   - Better spacing controls

### **Priority 3: Enhancement Fixes** 🔧
6. **Improve Data Quality**
   - Clean up Excel data
   - Add validation
   - Standardize formats

7. **Add Advanced Features**
   - Hover templates
   - Custom data
   - Better styling options

---

## 🧪 **Test Cases Needed**

### **Window Boundary Tests**
1. **Large Dataset Test**: Many processes with complex flows
2. **Zoom Test**: Verify zoom constrains content, not window
3. **Margin Test**: Ensure flows respect padding settings
4. **Responsive Test**: Test different window sizes

### **Element Switching Tests**
1. **Position Consistency Test**: Verify positions don't change
2. **Element-Specific Test**: Verify each element uses its own positions
3. **Fallback Test**: Test behavior when positions are missing
4. **Data Quality Test**: Test with various Excel data conditions

### **Layout Tests**
1. **Arrangement Test**: Test different arrangement options
2. **Alignment Test**: Test node alignment options
3. **Arrow Test**: Test arrow links functionality
4. **Spacing Test**: Test padding and spacing controls

---

## 🎯 **Success Criteria**

### **Functional Requirements**
- ✅ All flows visible within window boundaries
- ✅ Element-specific positioning working correctly
- ✅ Zoom controls content, not window size
- ✅ Node positions consistent across elements
- ✅ Clean Excel data with no NaN values

### **Performance Requirements**
- ✅ Responsive to different window sizes
- ✅ Fast rendering with large datasets
- ✅ Smooth element switching
- ✅ Reliable positioning calculations

### **User Experience Requirements**
- ✅ Intuitive controls and settings
- ✅ Clear visual feedback
- ✅ Consistent behavior
- ✅ Professional appearance

---

## 📁 **Files Requiring Changes**

### **Core Implementation**
- `src/plotting/enhanced_sankey.py` - Main Sankey implementation
- `src/plotting/visualization_loader.py` - Excel configuration loading
- `BioDYM_Scientific_Notebook.ipynb` - Test environment

### **Configuration**
- `data/01_input/250910_CS1_Wheat_Straw_v3.xlsx` - Excel configuration
- `scripts/create_visualization_config.py` - Configuration creation

### **Testing**
- `test/test_enhanced_sankey_positions.py` - Position testing
- New test files for boundary and zoom testing

---

## 🚀 **Implementation Strategy**

### **Phase 1: Critical Fixes (Week 1)**
1. Fix flow boundary management
2. Fix zoom implementation
3. Fix element-specific positioning
4. Clean up Excel data quality

### **Phase 2: Layout Improvements (Week 2)**
1. Implement proper Plotly arrangement
2. Add layout controls and options
3. Improve positioning logic
4. Add validation and error handling

### **Phase 3: Enhancement (Week 3)**
1. Add advanced features
2. Improve user experience
3. Add comprehensive testing
4. Documentation and examples

---

## 📊 **Current Status Summary**

| Issue | Severity | Status | Priority |
|-------|----------|--------|----------|
| Flows Outside Window | 🚨 Critical | Not Fixed | 1 |
| Element Positioning | 🚨 Major | Not Fixed | 1 |
| Zoom Ineffective | ⚠️ Major | Not Fixed | 1 |
| Position Inconsistency | ⚠️ Moderate | Partially Fixed | 2 |
| Excel Data Quality | ⚠️ Moderate | Not Fixed | 2 |
| Missing Layout Options | 🔧 Minor | Not Fixed | 3 |

---

## 📝 **Conclusion**

The Enhanced Sankey diagram has critical usability issues that must be addressed before it can be considered functional. The primary problems are:

1. **Flows going outside window boundaries** - Makes diagram unreadable
2. **Element-specific positioning not working** - Core functionality missing
3. **Zoom controls ineffective** - User control not working

These issues stem from fundamental misunderstandings of how Plotly Sankey works and inadequate implementation of boundary management and positioning logic.

**Immediate Action Required**: Fix flow boundary management and zoom implementation to make the diagram usable, then address element-specific positioning and data quality issues.

---

*Document created: 2025-01-10*  
*Status: Active Analysis*  
*Next Action: Implement Priority 1 fixes*
