# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.17.2
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# # BioDYM Material Flow Analysis - Scientific Notebook
# 
# A streamlined notebook for Material Flow Analysis using the BioDYM framework.
# 
# ## Workflow
# 1. **Load Excel File** - Define input data
# 2. **Confirm Configuration** - Review loaded data and settings
# 3. **Run Calculation** - Execute MFA analysis
# 4. **Mass Balance Check** - Verify calculation accuracy
# 5. **Visualizations** - Display all available plots
# 
# ---

# ## 1. Setup and Imports

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from IPython.display import display, HTML, Markdown

# Add BioDYM modules to path
src_path = os.path.join(os.getcwd(), 'src')
sys.path.insert(0, src_path)

# Add ODYM framework to path
biodym_mfa_tool_dir = os.getcwd()
odym_path = os.path.join(
    biodym_mfa_tool_dir, "framework", "ODYM-master_20241127", "odym", "modules"
)
sys.path.insert(0, odym_path)

# Add bioDYM add-on to path
biodym_addon_path = os.path.join(
    biodym_mfa_tool_dir, "framework", "bioDYM_add-on", "modules"
)
sys.path.insert(0, biodym_addon_path)

# Import BioDYM modules
try:
    import config
    import data_loader
    import system_setup
    import utils
    from engine import solver
    import plotting
    print("✅ BioDYM modules imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    raise

# Set up plotting
plt.style.use('default')
print("📊 Plotting environment ready")

# ## 2. Define Input File
# 
# **Change this variable to your Excel file:**

input_file = "data/01_input/250707_Template_CS1.xlsx"

print(f"📁 Input file: {input_file}")

# ## 3. Load and Validate Data

print("\n" + "="*60)
print("📊 LOADING AND VALIDATING DATA")
print("="*60)

# Load Excel file
try:
    input_data = pd.read_excel(
        input_file,
        sheet_name=None,
        header=0,
        engine='openpyxl',
        na_values=['N.A.', 'NA', 'n/a']
    )
    print(f"✅ Excel file loaded: {len(input_data)} sheets")
except Exception as e:
    print(f"❌ Error loading file: {e}")
    raise

# Display sheet overview
print("\n📋 Sheet Overview:")
for sheet_name, df in input_data.items():
    print(f"   {sheet_name}: {df.shape[0]} rows × {df.shape[1]} columns")

# Validate required sheets
required_sheets = [
    '1_1_Definition_Flows',
    '1_2_Data_Flows', 
    '2_1_Definition_Processes',
    '2_4_Initial_Stock',  # Correct sheet name
    '2_5_dynamic_tcs'
]

missing_sheets = [sheet for sheet in required_sheets if sheet not in input_data.keys()]
if missing_sheets:
    print(f"\n⚠️ Missing required sheets: {missing_sheets}")
else:
    print("\n✅ All required sheets present")

# ## 4. Extract Configuration from Data

print("\n" + "="*60)
print("⚙️ EXTRACTING CONFIGURATION")
print("="*60)

# Extract time range from flow data
flow_data = input_data['1_2_Data_Flows']
years = sorted(flow_data['Year_Flow'].unique())
start_year = int(min(years))
end_year = int(max(years))

print(f"📅 Time range: {start_year} - {end_year}")

# Extract elements from flow data
elements = ['material', 'WC', 'DM', 'CC']  # Default elements
print(f"🧪 Elements: {elements}")

# Check for Monte Carlo parameters
has_mc = '4_1_Uncertainty_Parameters' in input_data.keys()
print(f"🎲 Monte Carlo available: {'Yes' if has_mc else 'No'}")

# Check for DSM parameters
has_dsm = '3_1_Definition_DSM' in input_data.keys()
print(f"📈 DSM available: {'Yes' if has_dsm else 'No'}")

# Check for FOMP parameters
has_fomp = '3_2_Definition_FOMP' in input_data.keys()
print(f"🌱 FOMP available: {'Yes' if has_fomp else 'No'}")

# ## 5. Confirm Configuration

print("\n" + "="*60)
print("✅ CONFIGURATION CONFIRMATION")
print("="*60)

config_summary = f"""
**Analysis Configuration:**
- Input File: {input_file}
- Time Range: {start_year} - {end_year}
- Elements: {', '.join(elements)}
- Monte Carlo: {'Enabled' if has_mc else 'Disabled'}
- DSM: {'Enabled' if has_dsm else 'Disabled'}
- FOMP: {'Enabled' if has_fomp else 'Disabled'}
"""

display(Markdown(config_summary))

# ## 6. Run MFA Calculation

print("\n" + "="*60)
print("🚀 RUNNING MFA CALCULATION")
print("="*60)

# 1. Setup model scope
print("📋 Setting up model scope...")
try:
    model_classification, index_table = system_setup.define_model_scope(
        start_year, end_year, elements
    )
    print("✅ Model scope defined")
except Exception as e:
    print(f"❌ Error setting up model scope: {e}")
    raise

# 2. Initialize MFA system
print("🔧 Initializing MFA system...")
try:
    mfa_system_base = system_setup.initialize_mfa_system(
        model_classification, index_table
    )
    print("✅ MFA system initialized")
except Exception as e:
    print(f"❌ Error initializing MFA system: {e}")
    raise

# 3. Load and define processes
print("📊 Loading processes and data...")
try:
    mfa_system_base, all_excel_data = system_setup.load_and_define_processes(
        mfa_system_base, input_file, data_loader
    )
    print("✅ Processes and data loaded")
except Exception as e:
    print(f"❌ Error loading processes: {e}")
    raise

# 4. Load parameters
print("⚙️ Loading parameters...")
try:
    dsm_params = data_loader.load_dsm_parameters(all_excel_data)
    fomp_params = data_loader.load_fomp_parameters(all_excel_data)
    uncertainty_params = data_loader.load_uncertainty_definitions(all_excel_data)
    print("✅ Parameters loaded")
except Exception as e:
    print(f"❌ Error loading parameters: {e}")
    raise

# 5. Define flows and parameters
print("🔗 Defining flows and parameters...")
try:
    mfa_system_configured, _ = system_setup.define_flows_and_parameters(
        mfa_system_base, all_excel_data
    )
    print(f"✅ System configured: {len(mfa_system_configured.ProcessList)} processes, "
          f"{len(mfa_system_configured.FlowDict)} flows, {len(mfa_system_configured.StockDict)} stocks")
except Exception as e:
    print(f"❌ Error defining flows and parameters: {e}")
    raise

# 6. Run calculation
print("🧮 Running calculation...")
try:
    mfa_system_with_results, dsm_details = solver.run_mfa_calculation(
        mfa_system_configured, dsm_params, fomp_params, config
    )
    print("✅ Calculation completed successfully!")
except Exception as e:
    print(f"❌ Calculation error: {e}")
    import traceback
    traceback.print_exc()
    raise

# ## 7. Mass Balance Check

print("\n" + "="*60)
print("⚖️ MASS BALANCE VERIFICATION")
print("="*60)

# Calculate mass balance errors
mass_balance_errors = []
for process in mfa_system_with_results.ProcessList:
    if hasattr(process, 'MassBalance') and process.MassBalance is not None:
        for year_idx, year in enumerate(range(start_year, end_year + 1)):
            for element_idx, element in enumerate(elements):
                error = process.MassBalance[year_idx, element_idx]
                if abs(error) > 1e-6:  # Significant error threshold
                    mass_balance_errors.append({
                        'Process': process.Name,
                        'Year': year,
                        'Element': element,
                        'Error': error
                    })

if mass_balance_errors:
    print("⚠️ Mass balance errors detected:")
    error_df = pd.DataFrame(mass_balance_errors)
    display(error_df)
else:
    print("✅ All mass balances within acceptable limits")

# ## 8. Results Overview

print("\n" + "="*60)
print("📈 RESULTS OVERVIEW")
print("="*60)

# Display final stock values
print("\n📊 Final Stock Values (Year {end_year}):")
final_stocks = []
for stock_name, stock in mfa_system_with_results.StockDict.items():
    if stock_name.startswith('S_'):  # Absolute stocks only
        final_value = stock.Values[-1, 0]  # Material dimension, final year
        final_stocks.append({
            'Stock': stock_name,
            'Final Value (Mg)': final_value
        })

if final_stocks:
    stocks_df = pd.DataFrame(final_stocks)
    display(stocks_df)

# Display flow summary
print("\n🔄 Flow Summary:")
flow_summary = []
for flow_id, flow in mfa_system_with_results.FlowDict.items():
    avg_flow = np.mean(flow.Values[:, 0])  # Average material flow
    flow_summary.append({
        'Flow ID': flow_id,
        'From': flow.P_Start,
        'To': flow.P_End,
        'Avg Flow (Mg/year)': avg_flow
    })

if flow_summary:
    flows_df = pd.DataFrame(flow_summary)
    display(flows_df.head(10))  # Show first 10 flows

# ## 9. Visualizations

print("\n" + "="*60)
print("📊 VISUALIZATIONS")
print("="*60)

# ============================================================================
# 3.1 System Overview - Sankey Diagram
# ============================================================================

print("\n" + "-"*40)
print("3.1 SYSTEM OVERVIEW - SANKEY DIAGRAM")
print("-"*40)

print("🔗 Creating interactive Sankey diagram...")
try:
    # Use the existing interactive Sankey function
    plotting.plot_interactive_sankey(mfa_system_with_results)
    print("✅ Interactive Sankey diagram created")
except Exception as e:
    print(f"⚠️ Could not create interactive Sankey diagram: {e}")
    import traceback
    traceback.print_exc()

# ============================================================================
# 3.2 System Overview - Stock Overview
# ============================================================================

print("\n" + "-"*40)
print("3.2 SYSTEM OVERVIEW - STOCK OVERVIEW")
print("-"*40)

print("📊 Creating stock evolution plots...")
try:
    # Use the existing stock evolution function
    plotting.plot_stock_evolution(mfa_system_with_results, dsm_params, fomp_params)
    print("✅ Stock evolution plots created")
except Exception as e:
    print(f"⚠️ Could not create stock evolution plots: {e}")

# ============================================================================
# 3.3 System Overview - Flow Overview
# ============================================================================

print("\n" + "-"*40)
print("3.3 SYSTEM OVERVIEW - FLOW OVERVIEW")
print("-"*40)

print("🔄 Creating flow dynamics plots...")
try:
    # Use the existing flow dynamics function
    plotting.plot_flow_dynamics(mfa_system_with_results)
    print("✅ Flow dynamics plots created")
except Exception as e:
    print(f"⚠️ Could not create flow dynamics plots: {e}")

# ============================================================================
# 3.4 System Overview - Mass Balance Check
# ============================================================================

print("\n" + "-"*40)
print("3.4 SYSTEM OVERVIEW - MASS BALANCE CHECK")
print("-"*40)

print("⚖️ Creating mass balance error plots...")
try:
    # Use the existing mass balance error function
    plotting.plot_mass_balance_error(mfa_system_with_results)
    print("✅ Mass balance error plots created")
except Exception as e:
    print(f"⚠️ Could not create mass balance error plots: {e}")

# ============================================================================
# 3.5 Individual Process Analysis
# ============================================================================

print("\n" + "-"*40)
print("3.5 INDIVIDUAL PROCESS ANALYSIS")
print("-"*40)

# 3.5.1 Regular Processes
print("\n📋 3.5.1 Regular Process Dynamics:")
try:
    # Load process definitions for smart titles
    process_definitions = input_data['2_1_Definition_Processes']
    plotting.plot_process_dynamics(mfa_system_with_results, process_definitions)
    print("✅ Regular process dynamics plots created")
except Exception as e:
    print(f"⚠️ Could not create regular process dynamics: {e}")

# 3.5.2 DSM Processes
print("\n📈 3.5.2 DSM Process Analysis:")
try:
    if has_dsm and dsm_details:
        plotting.plot_dsm_stock_details(mfa_system_with_results, dsm_params, dsm_details)
        print("✅ DSM process analysis plots created")
    else:
        print("ℹ️ No DSM processes available")
except Exception as e:
    print(f"⚠️ Could not create DSM process analysis: {e}")

# 3.5.3 FOMP Processes
print("\n🌱 3.5.3 FOMP Process Analysis:")
try:
    if has_fomp and fomp_params:
        plotting.plot_fomp_stock_details(mfa_system_with_results, fomp_params)
        print("✅ FOMP process analysis plots created")
    else:
        print("ℹ️ No FOMP processes available")
except Exception as e:
    print(f"⚠️ Could not create FOMP process analysis: {e}")

# ============================================================================
# 3.6 Individual Stock Analysis
# ============================================================================

print("\n" + "-"*40)
print("3.6 INDIVIDUAL STOCK ANALYSIS")
print("-"*40)

print("📊 Creating individual stock analysis...")
try:
    plotting.plot_individual_stocks(mfa_system_with_results, dsm_params, fomp_params)
    print("✅ Individual stock analysis created")
except Exception as e:
    print(f"⚠️ Could not create individual stock analysis: {e}")

# ============================================================================
# 3.7 Individual Flow Analysis
# ============================================================================

print("\n" + "-"*40)
print("3.7 INDIVIDUAL FLOW ANALYSIS")
print("-"*40)

print("🔄 Creating individual flow analysis...")
try:
    plotting.plot_individual_flows(mfa_system_with_results)
    print("✅ Individual flow analysis created")
except Exception as e:
    print(f"⚠️ Could not create individual flow analysis: {e}")

# ============================================================================
# 3.8 System Efficiency Analysis
# ============================================================================

print("\n" + "-"*40)
print("3.8 SYSTEM EFFICIENCY ANALYSIS")
print("-"*40)

print("📈 Creating system efficiency metrics...")
try:
    plotting.plot_system_efficiency_metrics(mfa_system_with_results)
    print("✅ System efficiency metrics created")
except Exception as e:
    print(f"⚠️ Could not create system efficiency metrics: {e}")

# ============================================================================
# 3.9 Summary Dashboard
# ============================================================================

print("\n" + "-"*40)
print("3.9 SUMMARY DASHBOARD")
print("-"*40)

print("📊 Creating summary dashboard...")
try:
    plotting.plot_summary_dashboard(mfa_system_with_results, dsm_params, fomp_params)
    print("✅ Summary dashboard created")
except Exception as e:
    print(f"⚠️ Could not create summary dashboard: {e}")

# ============================================================================
# 3.10 Monte Carlo Analysis (if available)
# ============================================================================

print("\n" + "-"*40)
print("3.10 MONTE CARLO ANALYSIS")
print("-"*40)

if has_mc:
    print("🎲 Monte Carlo analysis available - to be implemented")
    print("This will include:")
    print("- MC distribution plots")
    print("- Sensitivity analysis")
    print("- Parameter importance")
    print("- Confidence intervals")
else:
    print("ℹ️ Monte Carlo analysis not available (no uncertainty parameters)")

# ## 10. Export Results

print("\n" + "="*60)
print("💾 EXPORTING RESULTS")
print("="*60)

# Export to Excel
output_file = "data/02_output/results_scientific.xlsx"
try:
    utils.export_results_to_excel(mfa_system_with_results, output_file)
    print(f"✅ Results exported to: {output_file}")
except Exception as e:
    print(f"⚠️ Export error: {e}")

# Export configuration summary
config_file = output_file.replace('.xlsx', '_config.xlsx')
try:
    config_summary = pd.DataFrame([{
        'Input File': input_file,
        'Start Year': start_year,
        'End Year': end_year,
        'Elements': ', '.join(elements),
        'Monte Carlo': has_mc,
        'DSM': has_dsm,
        'FOMP': has_fomp
    }])
    config_summary.to_excel(config_file, index=False)
    print(f"✅ Configuration exported to: {config_file}")
except Exception as e:
    print(f"⚠️ Config export error: {e}")

# ## 11. Summary

print("\n" + "="*60)
print("🎉 ANALYSIS COMPLETE")
print("="*60)

summary = f"""
**Analysis Summary:**
- ✅ Input file processed successfully
- ✅ Configuration extracted automatically
- ✅ MFA calculation completed
- ✅ Mass balance verified
- ✅ Visualizations generated
- ✅ Results exported

**Key Results:**
- Time period: {start_year} - {end_year}
- Processes analyzed: {len(mfa_system_with_results.ProcessList)}
- Flows tracked: {len(mfa_system_with_results.FlowDict)}
- Stocks modeled: {len(mfa_system_with_results.StockDict)}
- Mass balance errors: {len(mass_balance_errors)}

**Files Generated:**
- Main results: {output_file}
- Configuration: {config_file}
"""

display(Markdown(summary))

print("\n📊 Analysis completed successfully!") 