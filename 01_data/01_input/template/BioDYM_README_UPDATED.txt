================================================================================
WELCOME TO BioDYM
================================================================================
Version: 1.0
Last Updated: 2024-11-24
Built on: ODYM Framework (Pauliuk & Heeren, 2020)
License: MIT License

Authors:
- Johannes Scholz, Technische Universität Berlin
- Albrecht Fritze, Technische Universität Berlin
- Lukas Hoppe, Technische Universität Berlin
- Vera Susanne Rotter, Technische Universität Berlin

Contact: j.scholz@tu-berlin.de
GitHub: https://github.com/IndEcol/BioDYM (planned)

================================================================================
1. VISUAL WORKFLOW GUIDE
================================================================================

STAGE 1: SYSTEM CONFIGURATION
→ Configure the system basics (time range, elements, analysis options)
→ Sheet: 0_Configuration

STAGE 2: DEFINE SYSTEM STRUCTURE
→ Define processes (the "boxes" in your model)
→ Define flows (the "arrows" connecting processes)
→ Sheets: 2_1_Definition_Processes, 1_1_Definition_Flows

STAGE 3: ENTER DATA
→ Input flow quantities (measured or estimated values)
→ Define transfer coefficients (how processes split/transform flows)
→ Define initial stocks (starting amounts in processes)
→ Document data sources (references for transparency)
→ Sheets: 1_2_Data_Flows, 2_2_static_TCs, 2_3_dynamic_TCs,
          2_4_Initial_Stock, 6_1_Reference_Manager

STAGE 4: CONFIGURE ADVANCED MODELS (if needed)
→ Set up Dynamic Stock Models (DSM) for age-cohort tracking
→ Set up First-Order Mineralization Processes (FOMP) for organic decay
→ Sheets: 3_1_Definition_DSM, 3_2_Definition_FOMP

STAGE 5: UNCERTAINTY & SCENARIOS (optional)
→ Define parameter uncertainty for Monte Carlo analysis
→ Create scenario definitions for comparative analysis
→ Sheets: 4_1_Uncertainty_Parameters, 5_1_Scenario_Manager

STAGE 6: RUN ANALYSIS
→ Open Jupyter notebook: 00_BioDYM_Workflow.ipynb
→ Update input file path in notebook
→ Run all cells (Kernel → Restart & Run All)
→ View results in visualizations and exports

================================================================================
2. COLOR CODING SYSTEM
================================================================================

COLOR          PURPOSE                     EXAMPLE
------         -------                     -------
GREEN          Data Input                  Flow values, TC values, DSM parameters
               (Manual entry required)

BLUE           Dropdown Selection          Process_Logic, TC_Configuration,
               (Choose from list)          Stock_Configuration

RED            Auto-Calculation            Process_ID, Flow_ID (when auto-generated),
               (Do NOT modify)             ODYM fields, calculated values

YELLOW         Comments/References         Comment fields, Reference_ID fields,
               (Optional documentation)    Notes

WHITE/GRAY     System Fields              Complete?, ID, auto-populated names
               (System-managed)

================================================================================
3. QUICK START GUIDE
================================================================================
Follow these 6 steps to build your first model:

STEP 1: Define Your Processes
→ List all processes in your system (e.g., Forest, Sawmill, Landfill)
→ Assign Process_Logic to each (Input, Output, Splitter, Transformer, etc.)
→ Configure TC and Stock settings
→ Sheet: 2_1_Definition_Processes

STEP 2: Define Your Flows
→ List all flows connecting your processes
→ Define elemental composition (E1-E6: material, WC, DM, CC, etc.)
→ Sheet: 1_1_Definition_Flows

STEP 3: Enter Flow Data
→ Enter measured/estimated values for each flow and year
→ Specify units and conversion factors if needed
→ Document data sources using Reference_ID
→ Sheet: 1_2_Data_Flows

STEP 4: Set Transfer Coefficients (TCs)
→ For Splitter/Transformer processes, define how flows are distributed
→ Use static TCs for fixed distributions
→ Use dynamic TCs for time-varying distributions
→ Document TC sources using Reference_ID
→ Sheets: 2_2_static_TCs, 2_3_dynamic_TCs

STEP 5: Add References (IMPORTANT for transparency!)
→ Document all data sources in Reference Manager
→ Link data to references using Reference_ID in _Ref columns
→ Sheet: 6_1_Reference_Manager

STEP 6: Run the Analysis
→ Save your Excel file
→ Open: 00_BioDYM_Workflow.ipynb
→ Update input_file path to your Excel file
→ Run: Kernel → Restart & Run All
→ Results appear in visualizations and exported files

================================================================================
4. COMPLETE SHEET OVERVIEW
================================================================================

SHEET NAME                      PURPOSE
----------                      -------
0_Configuration                 System configuration (time, elements, options)

1_1_Definition_Flows            Define all flows (what moves between processes)
1_2_Data_Flows                  Enter flow quantities and composition data

2_1_Definition_Processes        Define all processes and their behavior
2_2_static_TCs                  Define fixed transfer coefficients
2_3_dynamic_TCs                 Define time-varying transfer coefficients
2_4_Initial_Stock               Define initial stock amounts

3_1_Definition_DSM              Configure Dynamic Stock Models (age-cohort)
3_2_Definition_FOMP             Configure First-Order Mineralization Processes

4_1_Uncertainty_Parameters      Define parameter uncertainty for Monte Carlo

5_1_Scenario_Manager            Define scenarios for comparative analysis

6_1_Reference_Manager           Document all data sources (NEW in v1.0!)

7_1_Comments_Validation         Column descriptions and validation rules
7_2_Codelists                   Reference lists for dropdown options

================================================================================
5. CORE CONCEPTS EXPLAINED
================================================================================

CONCEPT: Process
EXPLANATION: A "box" in your model representing a physical location,
transformation, or system boundary. Can store material (stock) or just
transform/split flows.
EXAMPLE: P01_Forest, P02_Sawmill, P03_Use_Phase, P04_Landfill

---

CONCEPT: Flow
EXPLANATION: Movement of material between processes. Defined by source process,
destination process, and elemental composition.
EXAMPLE: F_01_Timber_Harvest (Forest → Sawmill),
         F_05_Recycled_Material (Sorting → Processing)

---

CONCEPT: Process_Logic (CRITICAL!)
EXPLANATION: Defines HOW a process behaves. This is the most important setting!

OPTIONS:
- Input: Boundary process receiving from outside (data-driven, no TCs)
- Output: Boundary process sending outside (requires stock, no TCs)
- Splitter: Splits flow to outputs (uses E1 TCs only, composition unchanged)
- Transformer: Changes composition (uses E1-E6 TCs, composition changes)
- DSM: Dynamic Stock Model with age-cohort tracking
- FOMP: First-Order Mineralization (organic matter decay)
- Pass-through: Flows pass unchanged (no TCs needed)

EXAMPLE:
- Forest = Input (receives growth from environment)
- Sorting facility = Splitter (separates materials)
- Composting = Transformer (water evaporates, changes composition)
- Buildings = DSM (stock accumulates, demolished after lifetime)

---

CONCEPT: Transfer Coefficient (TC)
EXPLANATION: Fraction (0-1 or 0-100%) defining how much of an inflow goes to
each outflow. For each process, sum of all TCs must equal 1.0 (100%).
EXAMPLE: Sawmill with 75% lumber output, 25% sawdust:
         TC_Lumber = 0.75, TC_Sawdust = 0.25

---

CONCEPT: Static vs Dynamic TCs
EXPLANATION:
- Static TCs: Fixed values, don't change over time
- Dynamic TCs: Time-varying values, interpolated between data points

USE WHEN:
- Static: Fixed recycling rate (always 70%)
- Dynamic: Increasing recycling rate (2020: 60% → 2030: 80%)

NOTE: System automatically normalizes dynamic TCs to ensure they sum to 100%

---

CONCEPT: Elements (E1-E6)
EXPLANATION: Different material properties tracked simultaneously:
- E1: Material (total mass) - always required
- E2: Water Content (WC)
- E3: Dry Matter (DM)
- E4: Carbon Content (CC)
- E5-E6: User-defined elements

Elements can be hierarchical (e.g., CC as fraction of DM, not total material)

---

CONCEPT: DSM (Dynamic Stock Model)
EXPLANATION: Models processes where material accumulates and exits after a
lifetime. Uses age-cohort tracking and lifetime distributions (Normal, Fixed,
Weibull).
EXAMPLE: Buildings (constructed, used for 30±5 years, then demolished)

KEY PARAMETERS:
- Lifetime_Mean: Average product lifetime (years)
- Lifetime_StdDev: Variability (WARNING: >80% of mean may cause issues)
- Inflow_Split: Fraction to each product category
- Output_Split: Fraction to each outflow when product reaches end-of-life

---

CONCEPT: FOMP (First-Order Mineralization Process)
EXPLANATION: Models organic matter decomposition with multiple pools
(labile/recalcitrant) and different decay rates.
EXAMPLE: Compost (fast labile pool, slow recalcitrant pool)

KEY PARAMETERS:
- Inflow_fraction: Fraction to each pool (sum = 1.0)
- Half_life: Decay half-life for each pool (years)
- Shorter half-life = faster decay

---

CONCEPT: Reference Manager (NEW!)
EXPLANATION: Central database for documenting ALL data sources. Improves
transparency, reproducibility, and scientific rigor.

USE FOR:
- Flow data sources (statistics, measurements)
- TC value sources (literature, expert estimates)
- DSM lifetime assumptions (building surveys, studies)
- Uncertainty ranges (sensitivity analyses)

HOW TO USE:
1. Add reference in 6_1_Reference_Manager (assign Reference_ID)
2. Link data to reference using _Ref columns throughout template
   (Flow_Ref, Static_TC_Ref, DSM_Ref, etc.)

================================================================================
6. TROUBLESHOOTING & FAQ
================================================================================

PROBLEM: MFA calculation fails or mass balance errors
FIX:
→ Check TCs sum to 100% for each process
→ Verify no process has ONLY inputs or ONLY outputs (except Input/Output types)
→ Check Process_Logic is set correctly
→ Ensure dynamic TCs have data points at multiple years

---

PROBLEM: Process or flow missing from results
FIX:
→ Verify Process_Logic matches process function
→ Check Flow_ID consistency across all sheets
→ Ensure Flow_Output_Process and Flow_Input_Process are defined
→ Verify flows are connected in correct direction

---

PROBLEM: '#VALUE!' or Excel errors
FIX:
→ Check number formatting (numbers as numbers, not text)
→ Verify percentages entered correctly (0.75 or 75% depending on column)
→ Check for empty cells that should contain 0

---

PROBLEM: Dropdown lists empty or incorrect
FIX:
→ Check 7_2_Codelists sheet for dropdown options
→ Verify data validation rules are applied (may need macro re-application)
→ Check sheet names match exactly (case-sensitive)

---

PROBLEM: DSM warnings about negative stocks or large StdDev
FIX:
→ Large StdDev warning: Keep StdDev ≤ 80% of Mean to avoid negative lifetimes
→ Negative stocks: Check lifetime parameters, may be too short or data quality
→ Review DSM parameter values in 3_1_Definition_DSM

---

PROBLEM: Scenario results keep creating new files
FIX:
→ This was fixed in v1.0! Scenarios now overwrite existing files
→ Each scenario creates ONE file (e.g., scenario_Increased_Recycling.xlsx)
→ Copy file before running again if you want to keep old results

================================================================================
7. BEST PRACTICES
================================================================================

TIP 1: Start Small
→ Build a simple model (3-5 processes) first
→ Verify mass balance works
→ Gradually add complexity
→ WHY: Much easier to debug small models

---

TIP 2: Use Descriptive Names
→ Processes: Use_Phase_Buildings (not P03)
→ Flows: Timber_Harvest (not F_01)
→ TCs: TC_Recycling_Rate (not TC_1)
→ WHY: Model easier to understand and maintain

---

TIP 3: Document Everything
→ Use Comment columns throughout
→ Add ALL sources to Reference_Manager
→ Link data to sources via _Ref columns
→ WHY: Reproducibility and scientific credibility

---

TIP 4: Check Your Units
→ Use consistent units (Mg recommended)
→ Document units in UoM columns
→ Use conversion factors (CF) if source data in different units
→ WHY: Unit mixing is #1 source of MFA errors

---

TIP 5: Validate Incrementally
→ Check mass balance after each addition
→ Use validation plots in notebook
→ Run mass balance checks frequently
→ WHY: Catch errors early, easier to fix

---

TIP 6: Save Versions
→ Save as: my_model_v1.xlsm, my_model_v2.xlsm
→ Keep working copies separate from final
→ Use git for version control (recommended)
→ WHY: Easy to revert if something breaks

---

TIP 7: Use Element Hierarchy Wisely
→ Define hierarchy in Configuration sheet
→ E1 (material) always parent
→ E2-E4 can be children of each other (e.g., CC as fraction of DM)
→ WHY: Enables realistic composition modeling

---

TIP 8: Test with Simple Data First
→ Use round numbers initially (100, 1000, etc.)
→ Verify calculations by hand
→ Then replace with real data
→ WHY: Easy to spot calculation errors with simple numbers

================================================================================
8. COMMON MISTAKES TO AVOID
================================================================================

MISTAKE 1: Using wrong Process_Logic
❌ BAD: Forest as "Splitter" (should be "Input")
❌ BAD: Sorting as "Transformer" (should be "Splitter")
✓ GOOD: Match logic to actual process behavior

---

MISTAKE 2: TCs don't sum to 100%
❌ BAD: TC_1 = 0.6, TC_2 = 0.3 (sum = 0.9, material disappears!)
✓ GOOD: TC_1 = 0.6, TC_2 = 0.4 (sum = 1.0)
NOTE: System auto-normalizes dynamic TCs, but verify static TCs manually!

---

MISTAKE 3: Mixing data entry methods
❌ BAD: Some flows in 1_2_Data_Flows, others hardcoded in notebook
✓ GOOD: ALL flow data in 1_2_Data_Flows

---

MISTAKE 4: Ignoring validation warnings
❌ BAD: "Large StdDev" warning → ignore and continue
✓ GOOD: Adjust DSM parameters based on warnings

---

MISTAKE 5: Not documenting data sources
❌ BAD: Enter values without references
✓ GOOD: Add ALL sources to Reference_Manager, link via _Ref columns

---

MISTAKE 6: Forgetting Initial Stock
❌ BAD: Process with Stock_Configuration = "Initial Stock" but no entry in 2_4
✓ GOOD: Define initial stock for all processes that start with material

================================================================================
9. RECENT UPDATES (v1.0 - November 2024)
================================================================================

NEW FEATURES:
✓ Reference Manager (6_1_Reference_Manager) for data source documentation
✓ Pass-through Process_Logic (flows pass unchanged without TCs)
✓ Dynamic TC normalization (ensures TCs always sum to 100%)
✓ DSM validation warnings (large StdDev, negative stocks)
✓ Scenario export improvement (overwrites instead of timestamps)
✓ E1-E6 element support (up to 6 elements)
✓ Enhanced validation with column comments
✓ Comprehensive codelists (7_2_Codelists)

BUG FIXES:
✓ Dynamic TC mass balance errors fixed
✓ Element composition calculations corrected
✓ Stock accumulation in DSM processes verified

DOCUMENTATION:
✓ Complete validation rebuild (69 INPUT columns documented)
✓ This README updated with recent changes
✓ VBA macros for comment management
✓ Comprehensive troubleshooting guide

================================================================================
10. GETTING HELP
================================================================================

DOCUMENTATION:
→ README (this sheet): Overview and quick start
→ Column comments: Hover over column headers for descriptions
→ 7_1_Comments_Validation: Detailed field descriptions
→ 7_2_Codelists: Dropdown option explanations
→ CLAUDE.md (in repository): Technical developer guide

VALIDATION TOOLS:
→ Mass balance plots in notebook
→ Composition validation
→ DSM/FOMP diagnostics

CONTACT:
→ Email: j.scholz@tu-berlin.de
→ GitHub Issues: (link when published)

CITATION:
→ When using BioDYM, please cite:
  Scholz, J., Fritze, A., Hoppe, L., & Rotter, V.S. (2024).
  BioDYM: Dynamic Material Flow Analysis for Bio-based Systems.
  DOI: (pending publication)

→ Built on ODYM framework:
  Pauliuk, S., & Heeren, N. (2020).
  ODYM—An open software framework for studying dynamic material systems.
  Journal of Industrial Ecology, 24(3), 446-458.

================================================================================
END OF README
================================================================================

Version: 1.0
Last Updated: 2024-11-24
Template: 251124_BioDYM_ODYM_Template_Empty.xlsm

For more information, visit the BioDYM documentation or contact the authors.
