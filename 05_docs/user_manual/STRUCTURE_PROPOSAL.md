# BioDYM User Manual - Structure Proposal

## Proposed Structure

---

## PART I: INTRODUCTION & GETTING STARTED

### 1. Introduction
- 1.1 What is BioDYM?
- 1.2 Key Features & Capabilities
- 1.3 System Architecture Overview
- 1.4 When to Use BioDYM
- 1.5 Comparison with Other MFA Tools
- 1.6 Citation & Acknowledgments

### 2. Installation & Setup
- 2.1 System Requirements
- 2.2 Python Environment Setup (uv sync)
- 2.3 Dependencies
- 2.4 Verifying Installation
- 2.5 Troubleshooting Installation Issues

### 3. Quick Start Tutorial
- 3.1 The BioDYM Workflow (Notebook Overview)
- 3.2 Your First Model (Simple Wood Example)
- 3.3 Running the Calculation
- 3.4 Interpreting Basic Results
- 3.5 Next Steps

---

## PART II: EXCEL TEMPLATE & DATA INPUT

### 4. Excel Template Overview
- 4.1 Template Structure (All Sheets)
- 4.2 Color Coding & Conventions
- 4.3 Required vs Optional Sheets
- 4.4 Data Validation & Dropdowns
- 4.5 Template Versioning

### 5. Configuration Sheet
- 5.1 Time Range Configuration
- 5.2 Element Definitions
- 5.3 Dimension Lists (Regions, Goods, Materials)
- 5.4 Calculation Flags (DSM, FOMP, Monte Carlo)
- 5.5 Scenario Settings

### 6. Flow Definitions (Sheet 1_1)
- 6.1 Flow ID Naming Conventions
- 6.2 Source and Target Processes
- 6.3 Element Composition (Fractions)
- 6.4 Flow Types & Categories
- 6.5 Documentation Fields

### 7. Flow Data Input (Sheet 1_2)
- 7.1 Time Series Data Entry
- 7.2 **Automatic Interpolation** (gaps in time series)
- 7.3 Unit Specifications
- 7.4 Conversion Factors
- 7.5 Data Sources & References
- 7.6 Element-Specific Values (E1, E2, E3...)

### 8. Process Definitions (Sheet 2_1)
- 8.1 Process ID System
- 8.2 Process Logic Types
  - Input, Output, Splitter, Transformer, Pass-through, DSM, FOMP
- 8.3 TC Configuration (Static/Dynamic/None)
- 8.4 Stock Configuration
- 8.5 Process Naming & Documentation

---

## PART III: CORE CONCEPTS & MODEL DESIGN

### 9. Material Flow Analysis Fundamentals
- 9.1 MFA Principles
- 9.2 Mass Balance Equations
- 9.3 System Boundaries
- 9.4 Temporal Resolution
- 9.5 Spatial Resolution

### 10. The ODYM Framework
- 10.1 ODYM Architecture
- 10.2 Classification & Index Tables
- 10.3 Parameters & Values
- 10.4 Flow and Stock Objects
- 10.5 BioDYM Extensions to ODYM

### 11. Elements & Hierarchies
- 11.1 Element Concept (material, WC, DM, CC)
- 11.2 Hierarchical Relationships
- 11.3 Element Recalculation Logic
- 11.4 Custom Element Definitions
- 11.5 Element Composition Validation

### 12. Process Types in Detail
- 12.1 Input Processes (System Entry Points)
- 12.2 Output Processes (System Exit Points)
- 12.3 Splitter Processes (Distribution Logic)
- 12.4 Transformer Processes (Material Conversion)
- 12.5 Pass-through Processes (No Transformation)
- 12.6 DSM Processes (Dynamic Stock with Lifetime)
- 12.7 FOMP Processes (Organic Matter Decay)

---

## PART IV: TRANSFER COEFFICIENTS & PARAMETERS

### 13. Transfer Coefficients (TCs)
- 13.1 TC Concept & Purpose
- 13.2 Static TCs (Sheet 2_2)
  - Single Value Configuration
  - Element-Specific TCs
  - Validation Rules
- 13.3 Dynamic TCs (Sheet 2_3)
  - Time-Varying Coefficients
  - **Automatic Interpolation**
  - **Normalization by Process**
  - Year-by-Year Definition
- 13.4 TC Naming Conventions
- 13.5 Mass Balance Requirements (Sum to 100%)

### 14. Initial Stock Parameters (Sheet 2_4)
- 14.1 When to Use Initial Stocks
- 14.2 Stock Value Input
- 14.3 Element Composition
- 14.4 Stock Outflow Configuration
- 14.5 Validation & Warnings

---

## PART V: DYNAMIC STOCK MODEL (DSM)

### 15. DSM Fundamentals
- 15.1 What is a Dynamic Stock?
- 15.2 Inflow-Driven vs Stock-Driven Models
- 15.3 Lifetime Distributions Concept
- 15.4 Cohort-Based Tracking
- 15.5 When to Use DSM

### 16. DSM Configuration (Sheet 3_1)
- 16.1 Category-Based Structure
- 16.2 Inflow Splits
- 16.3 Lifetime Parameters
- 16.4 Output Flow Configuration
- 16.5 Parameter Format (New vs Legacy)

### 17. DSM Lifetime Distributions
- 17.1 **Fixed Distribution**
  - Parameters: Mean
  - Use Cases
  - Examples
- 17.2 **Normal Distribution**
  - Parameters: Mean, StdDev
  - ⚠️ Warning: StdDev < 80% of Mean
  - Use Cases
- 17.3 **FoldedNormal Distribution**
  - Parameters: Mean, StdDev
  - Advantages over Normal
  - Use Cases
- 17.4 **LogNormal Distribution**
  - Parameters: Mean, StdDev
  - Right-Skewed Behavior
  - Use Cases (electronics, machinery)
- 17.5 **Weibull Distribution**
  - Parameters: Mean, **Shape**
  - Shape < 1: Infant mortality
  - Shape = 1: Constant failure
  - Shape > 1: Wear-out
  - Use Cases & Examples

### 18. DSM Results & Visualization
- 18.1 Stock Evolution Over Time
- 18.2 Inflow vs Outflow Dynamics
- 18.3 Category Breakdown
- 18.4 Lifetime Analysis
- 18.5 Troubleshooting DSM Issues

---

## PART VI: FOMP (FIRST-ORDER MULTI-POOL)

### 19. FOMP Fundamentals
- 19.1 What is FOMP?
- 19.2 Organic Matter Decay
- 19.3 Multi-Pool Structure (Labile/Recalcitrant)
- 19.4 Mineralization Process
- 19.5 When to Use FOMP

### 20. FOMP Configuration (Sheet 3_2)
- 20.1 Decay Pool Definition
- 20.2 Inflow Fractions
- 20.3 Decay Rate Constants (k1, k2, k3...)
- 20.4 Output Flow Configuration
- 20.5 Parameter Naming (FOMP_Parameter_ID)

### 21. FOMP Results & Visualization
- 21.1 Stock Accumulation
- 21.2 Mineralization Rates
- 21.3 Pool-Specific Dynamics
- 21.4 Annual vs Cumulative Flows
- 21.5 Troubleshooting FOMP Issues

---

## PART VII: UNCERTAINTY & SCENARIO ANALYSIS

### 22. Distribution Functions
- 22.1 Distribution Concept Overview
- 22.2 DSM vs Monte Carlo Distributions
- 22.3 **Complete Distribution Reference**
  - All DSM distributions (Fixed, Normal, FoldedNormal, LogNormal, Weibull)
  - All Monte Carlo distributions (normal, uniform, triangular, lognormal)
  - Parameter requirements
  - Use case guidelines
- 22.4 **Weibull Shape Parameter Guide**
- 22.5 **Triangular Mode Parameter Guide**

### 23. Monte Carlo Simulation (Sheet 4_1)
- 23.1 Uncertainty Analysis Concept
- 23.2 Parameter Selection for MC
- 23.3 Distribution Type Selection
- 23.4 Number of Iterations
- 23.5 Running Monte Carlo
- 23.6 Results Interpretation
  - Histograms
  - Sensitivity (Tornado Charts)
  - Simulation Paths
  - Confidence Intervals

### 24. Scenario Analysis (Sheet 5_1)
- 24.1 Scenario Manager Overview
- 24.2 Defining Scenarios
- 24.3 Parameter Modifications
  - Flow modifications
  - TC modifications
  - DSM parameter modifications
- 24.4 Time Range Specifications
- 24.5 Running Multiple Scenarios
- 24.6 Scenario Comparison Visualizations

---

## PART VIII: VALIDATION & RESULTS

### 25. Mass Balance Verification
- 25.1 Mass Balance Principles
- 25.2 Total Mass Balance Error
- 25.3 Process-Level Balance
- 25.4 Element-Specific Balance
- 25.5 Acceptable Error Ranges
- 25.6 Troubleshooting Balance Issues

### 26. Flow Composition Validation
- 26.1 Composition Completeness
- 26.2 Hierarchical Element Checks
- 26.3 Interactive Composition Explorer
- 26.4 Composition Export

### 27. Data Validation Summary
- 27.1 Automated Validation Checks
- 27.2 Warning Messages
- 27.3 Error Messages
- 27.4 Validation Best Practices

---

## PART IX: VISUALIZATION & EXPORT

### 28. System Visualization
- 28.1 Graphviz Flow Charts
- 28.2 Process Flow Diagrams
- 28.3 Interactive Sankey Diagrams
  - Element Selection
  - Year Filtering
  - Threshold Settings
- 28.4 Customization Options

### 29. Dynamic Analysis Plots
- 29.1 Process Dynamics (3-Panel View)
- 29.2 Flow Dynamics (Time Series)
- 29.3 Stock Bar Charts
- 29.4 System Stock Composition
- 29.5 DSM Stock Details
- 29.6 FOMP Mineralization Plots

### 30. Results Export
- 30.1 KPI Dashboard
- 30.2 Excel Export Format
- 30.3 Scenario Results Export
- 30.4 Monte Carlo Results Export
- 30.5 Composition Export
- 30.6 Custom Export Options

---

## PART X: ADVANCED TOPICS

### 31. Model Design Best Practices
- 31.1 System Boundary Definition
- 31.2 Process Granularity
- 31.3 Data Quality Requirements
- 31.4 Documentation Standards
- 31.5 Model Validation Workflow

### 32. Performance Optimization
- 32.1 Large System Considerations
- 32.2 Monte Carlo Efficiency
- 32.3 Memory Management
- 32.4 Computation Time Reduction

### 33. Extending BioDYM
- 33.1 Custom Element Definitions
- 33.2 Custom Process Logic
- 33.3 Integration with External Tools
- 33.4 Python API Usage

### 34. Version Control & Collaboration
- 34.1 Git Workflow
- 34.2 Template Versioning
- 34.3 Model Documentation
- 34.4 Collaborative Development

---

## PART XI: TROUBLESHOOTING & REFERENCE

### 35. Common Errors & Solutions
- 35.1 Data Loading Errors
- 35.2 Calculation Errors
- 35.3 Validation Warnings
- 35.4 Visualization Issues
- 35.5 Export Problems

### 36. FAQ (Frequently Asked Questions)
- 36.1 General Questions
- 36.2 Data Input Questions
- 36.3 Calculation Questions
- 36.4 Results Interpretation Questions

### 37. Complete Parameter Reference
- 37.1 Configuration Parameters
- 37.2 Flow Parameters
- 37.3 Process Parameters
- 37.4 TC Parameters
- 37.5 DSM Parameters
- 37.6 FOMP Parameters
- 37.7 Monte Carlo Parameters

### 38. Formula Reference
- 38.1 Mass Balance Equations
- 38.2 Element Recalculation
- 38.3 DSM Calculations
- 38.4 FOMP Decay Equations
- 38.5 Statistical Formulas

### 39. Glossary
- 39.1 MFA Terms
- 39.2 BioDYM-Specific Terms
- 39.3 ODYM Terms
- 39.4 Abbreviations

### 40. Appendices
- A. Excel Template Column Reference
- B. Validation Rules Complete List
- C. Distribution Function Mathematical Details
- D. Example Models
- E. Bibliography & References

---

## PROPOSED PRIORITIES FOR WRITING

### Phase 1: Essential Core (Users can start working)
1. Introduction (Ch 1)
2. Installation & Quick Start (Ch 2-3)
3. Excel Template Overview (Ch 4)
4. Flow & Process Definitions (Ch 6, 7, 8)
5. Transfer Coefficients (Ch 13)
6. Basic Visualization & Export (Ch 28, 30)

### Phase 2: Advanced Features (Power users)
7. DSM Complete (Ch 15-18)
8. Distribution Functions (Ch 22)
9. Monte Carlo & Scenarios (Ch 23-24)
10. Validation (Ch 25-27)

### Phase 3: Specialized & Reference
11. FOMP (Ch 19-21)
12. Advanced Topics (Ch 31-34)
13. Troubleshooting & Reference (Ch 35-40)

---

## QUESTIONS FOR DISCUSSION

1. **Target Audience:** Should we write for:
   - Beginners (step-by-step, lots of examples)?
   - Experienced MFA practitioners (concise, technical)?
   - Both (separate tracks)?

2. **Format:**
   - Single large PDF?
   - Multiple documents (Getting Started, Reference, Advanced)?
   - Online documentation (ReadTheDocs style)?
   - All of the above?

3. **Depth vs Breadth:**
   - Comprehensive mathematical details?
   - Practical examples with less theory?
   - Balanced approach?

4. **Examples:**
   - Should each chapter have worked examples?
   - One complete running example throughout?
   - Multiple domain-specific examples (wood, plastics, bio-based)?

5. **Emphasis Areas:**
   - What features are most important to document first?
   - Any features rarely used that can be lower priority?
   - Any pain points users currently experience?

6. **Interactive Elements:**
   - Video tutorials?
   - Jupyter notebook tutorials?
   - Interactive web-based examples?

7. **Maintenance:**
   - Who will maintain the manual as BioDYM evolves?
   - Versioning strategy for documentation?

---

## SUGGESTED NAMING & ORGANIZATION

```
05_docs/
├── user_manual/
│   ├── 00_Introduction.md
│   ├── 01_Installation_Setup.md
│   ├── 02_Quick_Start.md
│   ├── 03_Excel_Template_Overview.md
│   ├── 04_Flow_Definitions.md
│   ├── 05_Flow_Data_Input.md
│   ├── ...
│   └── 40_Appendices.md
├── figures/
│   ├── system_architecture.png
│   ├── excel_template_overview.png
│   └── ...
├── examples/
│   ├── simple_wood_example/
│   ├── complete_biobased_system/
│   └── ...
└── BioDYM_User_Manual.pdf  (compiled version)
```

---

**What do you think of this structure? What should we prioritize?**
