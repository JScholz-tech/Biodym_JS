# BioDYM Scientific Notebook - Table of Contents

## 📋 Overview
A streamlined notebook for Material Flow Analysis using the BioDYM framework with enhanced plotting capabilities.

## 🔄 Workflow Summary
1. **Load Excel File** - Define input data
2. **Confirm Configuration** - Review loaded data and settings  
3. **Run Calculation** - Execute MFA analysis
4. **Mass Balance Check** - Verify calculation accuracy
5. **Visualizations** - Display all available plots

---

## 📚 Detailed Table of Contents

### 1. Setup and Imports
- **1.1** Import statements and path configuration
- **1.2** BioDYM modules import
- **1.3** Plotting environment setup

### 2. Define Input File
- **2.1** Input file specification
- **2.2** File path configuration

### 3. Load and Validate Data
- **3.1** Excel file loading
- **3.2** Sheet overview display
- **3.3** Required sheets validation
- **3.4** Data quality checks

### 4. Extract Configuration from Data
- **4.1** Time range extraction
- **4.2** Element identification
- **4.3** Monte Carlo availability check
- **4.4** DSM parameters detection
- **4.5** FOMP parameters detection

### 5. Confirm Configuration
- **5.1** Configuration summary display
- **5.2** Analysis parameters review

### 6. Run MFA Calculation
- **6.1** Model scope setup
- **6.2** MFA system initialization
- **6.3** Process and data loading
- **6.4** Parameter loading
- **6.5** Flow and parameter definition
- **6.6** Calculation execution

### 7. Mass Balance Check
- **7.1** Mass balance error calculation
- **7.2** Error threshold verification
- **7.3** Error reporting

### 8. Results Overview
- **8.1** Final stock values display
- **8.2** Flow summary analysis
- **8.3** Key metrics presentation

### 9. Visualizations

#### 9.1 System Overview - Sankey Diagram
- **9.1.1** Interactive Sankey creation
- **9.1.2** Enhanced features demonstration
- **9.1.3** Export functionality

#### 9.2 System Overview - Stock Overview
- **9.2.1** Stock evolution plots
- **9.2.2** Process type highlighting

#### 9.3 System Overview - Flow Overview
- **9.3.1** Flow dynamics plots
- **9.3.2** System flow analysis

#### 9.4 System Overview - Mass Balance Check
- **9.4.1** Optimized mass balance error plots
- **9.4.2** Performance features
- **9.4.3** Enhanced export options

#### 9.5 Individual Process Analysis
- **9.5.1** Regular Process Dynamics
- **9.5.2** DSM Process Analysis
- **9.5.3** FOMP Process Analysis

#### 9.6 Individual Stock Analysis
- **9.6.1** Multi-stock selection
- **9.6.2** Process type color coding
- **9.6.3** Delta stock visualization

#### 9.7 Individual Flow Analysis
- **9.7.1** Multi-flow selection
- **9.7.2** Cumulative vs. individual values
- **9.7.3** Element-specific analysis

#### 9.8 System Efficiency Analysis
- **9.8.1** Efficiency metrics calculation
- **9.8.2** Performance indicators

#### 9.9 Summary Dashboard
- **9.9.1** Comprehensive system overview
- **9.9.2** Key performance indicators

#### 9.10 Monte Carlo Analysis
- **9.10.1** Integrated Monte Carlo dashboard
- **9.10.2** 4-Panel layout demonstration
- **9.10.3** Individual MC plots
- **9.10.4** Distribution analysis
- **9.10.5** Correlation matrices
- **9.10.6** Confidence intervals

### 10. Export Results
- **10.1** Excel export functionality
- **10.2** Configuration summary export
- **10.3** File organization

### 11. Summary
- **11.1** Analysis completion summary
- **11.2** Key results overview
- **11.3** Generated files list

---

## 🎯 Key Features by Section

### Enhanced Plotting Features
- ✅ **Interactive Sankey Diagram** with multi-process selection
- ✅ **Monte Carlo Dashboard** with 4-panel layout
- ✅ **Optimized Mass Balance Plots** with performance improvements
- ✅ **Professional Legends** with color coding
- ✅ **Export Functionality** with multiple formats
- ✅ **Real-time Updates** and interactive controls

### Analysis Capabilities
- ✅ **DSM Process Analysis** with detailed stock evolution
- ✅ **FOMP Process Analysis** with mineralization tracking
- ✅ **System Efficiency Metrics** with recycling rates
- ✅ **Individual Flow/Stock Analysis** with multi-selection
- ✅ **Scenario Comparison** capabilities

### Export and Documentation
- ✅ **Excel Export** with organized results
- ✅ **Configuration Export** with analysis parameters
- ✅ **Comprehensive Documentation** with guides and examples

---

## 📊 Visualization Types Available

### Interactive Plots
1. **Sankey Diagrams** - Material flow visualization
2. **Stock Evolution** - Time series analysis
3. **Flow Dynamics** - Process interaction analysis
4. **Mass Balance Errors** - Validation plots
5. **Monte Carlo Dashboard** - Uncertainty analysis

### Individual Analysis Plots
1. **Process Dynamics** - Inflow/Stock/Outflow analysis
2. **Stock Composition** - Detailed stock breakdown
3. **Flow Analysis** - Individual flow tracking
4. **Efficiency Metrics** - System performance indicators

### Summary Dashboards
1. **System Overview** - Key performance indicators
2. **Scenario Comparison** - Multi-scenario analysis
3. **Monte Carlo Summary** - Uncertainty quantification

---

## 🔧 Technical Requirements

### Dependencies
- Python 3.x
- Plotly for interactive visualizations
- Pandas for data manipulation
- NumPy for numerical computations
- IPyWidgets for interactive controls

### Input Requirements
- Excel file with required sheets
- Proper data formatting
- Valid process and flow definitions

### Output Capabilities
- Interactive HTML plots
- PNG export functionality
- Excel result files
- Configuration summaries

---

*This notebook provides a comprehensive Material Flow Analysis workflow with enhanced visualization capabilities, ready for scientific presentations and detailed system analysis.* 