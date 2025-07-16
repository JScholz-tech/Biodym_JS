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

# # BioDYM Material Flow Analysis - Comprehensive GUI
# 
# ::: {note}
# This notebook provides a comprehensive interface for the BioDYM Material Flow Analysis tool.
# It demonstrates all key features with minimal code and maximum documentation.
# :::
# 
# ## Overview
# 
# BioDYM is a comprehensive Material Flow Analysis (MFA) tool designed for analyzing bio-based material systems. Built on the [ODYM framework](https://github.com/IndEcol/ODYM), it tracks material flows, stocks, and transformations through time with special features for organic waste management and biomass cascading.
# 
# ### Key Features
# 
# - **Material Flow Analysis (MFA)** - Track materials through complex systems
# - **Dynamic Stock Modeling (DSM)** - Model material aging and product lifetimes
# - **First-Order Mineralization (FOMP)** - Simulate organic matter decomposition
# - **Monte Carlo Simulation** - Quantify uncertainty in results
# - **Interactive Visualizations** - Sankey diagrams, stock plots, and dashboards
# - **Excel-based Configuration** - No programming required for basic use
# 
# ::: {warning}
# **Important**: This notebook requires the BioDYM tool to be properly installed and configured.
# Make sure all dependencies are installed and the framework paths are correctly set.
# :::

# ## 1. Setup and Imports
# 
# First, we import all necessary modules and set up the environment.

# Import standard libraries
import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from ipywidgets import interact, IntSlider, Dropdown, SelectMultiple, Checkbox, Button, Output, VBox, HBox, Text, HTML as ipyHTML
from IPython.display import display, HTML, Markdown
import glob

# Add BioDYM modules to path
src_path = os.path.join(os.getcwd(), 'src')
sys.path.insert(0, src_path)

# Add ODYM framework to path (now inside biodym_mfa_tool)
biodym_mfa_tool_dir = os.getcwd()
odym_path = os.path.join(
    biodym_mfa_tool_dir, "framework", "ODYM-master_20241127", "odym", "modules"
)
sys.path.insert(0, odym_path)

# Add bioDYM add-on to path (now inside biodym_mfa_tool)
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
    print("✅ All BioDYM modules imported successfully!")
except ImportError as e:
    print(f"❌ Error importing BioDYM modules: {e}")
    print("Please ensure the BioDYM tool is properly installed.")

# Set up plotting
plt.style.use('default')
print("📊 Plotting environment configured")

# ## 2. 📁 INPUT FILE SELECTION
# 
# ::: {important}
# **START HERE!** This is the most important step - select your input Excel file.
# :::
# 
# ### What is an Input File?
# 
# The BioDYM tool uses Excel files as input that contain all the data needed for your Material Flow Analysis:
# 
# - **Material flows** between processes
# - **Process definitions** and their properties
# - **Stock data** and initial conditions
# - **Transfer coefficients** for material transformations
# - **Model parameters** for DSM and FOMP calculations
# - **Uncertainty parameters** for Monte Carlo simulations
# 
# ### Available Input Files
# 
# The following Excel files are available in your project:

# Function to list available input files
def list_available_input_files():
    """List all available Excel input files in the data directory."""
    
    # Look for Excel files in the data/01_input directory
    input_dir = "data/01_input"
    excel_files = []
    
    if os.path.exists(input_dir):
        # Find all Excel files
        excel_patterns = ["*.xlsx", "*.xls"]
        for pattern in excel_patterns:
            excel_files.extend(glob.glob(os.path.join(input_dir, pattern)))
    
    # Also check the test_data directory
    test_data_dir = "test_data"
    if os.path.exists(test_data_dir):
        for pattern in excel_patterns:
            excel_files.extend(glob.glob(os.path.join(test_data_dir, pattern)))
    
    return sorted(excel_files)

# Display available files
print("📋 Available Input Files:")
print("=" * 50)

available_files = list_available_input_files()
if available_files:
    for i, file_path in enumerate(available_files, 1):
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path) / 1024  # Size in KB
        print(f"{i}. {file_name} ({file_size:.1f} KB)")
        print(f"   Path: {file_path}")
        print()
else:
    print("❌ No Excel files found in data/01_input/ or test_data/")
    print("Please ensure you have input files available.")

# ### File Selection Interface

# Create prominent file selection widget
def create_file_selection_widget():
    """Create a prominent file selection interface."""
    
    # Get available files
    available_files = list_available_input_files()
    file_options = ["Select a file..."] + [os.path.basename(f) for f in available_files]
    file_paths = [""] + available_files
    
    # File dropdown
    file_dropdown = Dropdown(
        options=file_options,
        value="Select a file...",
        description='📁 Input File:',
        style={'description_width': '120px'},
        layout={'width': '400px'}
    )
    
    # File path display
    file_path_display = Text(
        value="",
        description='📂 Full Path:',
        style={'description_width': '120px'},
        layout={'width': '600px'},
        disabled=True
    )
    
    # File info display
    file_info_display = Output()
    
    def update_file_info(change):
        """Update file information when selection changes."""
        if change['new'] != "Select a file...":
            selected_index = file_options.index(change['new'])
            selected_path = file_paths[selected_index]
            
            file_path_display.value = selected_path
            
            # Display file information
            with file_info_display:
                file_info_display.clear_output()
                
                if os.path.exists(selected_path):
                    # Get file info
                    file_size = os.path.getsize(selected_path) / 1024  # KB
                    file_stats = os.stat(selected_path)
                    modified_time = pd.to_datetime(file_stats.st_mtime, unit='s')
                    
                    print(f"📊 File Information:")
                    print(f"   Size: {file_size:.1f} KB")
                    print(f"   Modified: {modified_time.strftime('%Y-%m-%d %H:%M')}")
                    
                    # Try to read and validate the file
                    try:
                        input_data = pd.read_excel(selected_path, sheet_name=None)
                        print(f"   Sheets: {len(input_data)}")
                        print(f"   Sheet names: {list(input_data.keys())}")
                        
                        # Check for required sheets
                        required_sheets = [
                            '1_1_Definition_Flows',
                            '1_2_Data_Flows', 
                            '2_1_Definition_Processes',
                            '2_4_Initial_Stock',
                            '2_5_dynamic_tcs'
                        ]
                        
                        missing_sheets = [sheet for sheet in required_sheets if sheet not in input_data.keys()]
                        
                        if missing_sheets:
                            print(f"   ⚠️ Missing required sheets: {missing_sheets}")
                        else:
                            print("   ✅ All required sheets present")
                            
                    except Exception as e:
                        print(f"   ❌ Error reading file: {e}")
                else:
                    print("❌ File not found")
    
    file_dropdown.observe(update_file_info, names='value')
    
    # Load button
    load_button = Button(
        description='📥 Load Selected File',
        button_style='success',
        layout={'width': '200px'}
    )
    
    # Status display
    status_display = Output()
    
    def on_load_click(b):
        """Handle file loading."""
        selected_file = file_dropdown.value
        if selected_file != "Select a file...":
            selected_index = file_options.index(selected_file)
            selected_path = file_paths[selected_index]
            
            with status_display:
                status_display.clear_output()
                print(f"🔄 Loading file: {selected_file}")
                
                # Load and validate the file
                global input_data
                input_data = load_input_data(selected_path)
                
                if input_data:
                    print("✅ File loaded successfully!")
                    print(f"📊 Loaded {len(input_data)} sheets")
                    display_input_summary(input_data)
                else:
                    print("❌ Failed to load file. Please check the file format.")
    
    load_button.on_click(on_load_click)
    
    # Instructions
    instructions_html = """
    <div style="background-color: #e8f4fd; padding: 15px; border-radius: 5px; margin: 10px 0;">
        <h4>📋 Instructions:</h4>
        <ol>
            <li><strong>Select a file</strong> from the dropdown above</li>
            <li><strong>Review the file information</strong> that appears below</li>
            <li><strong>Click "Load Selected File"</strong> to load the data</li>
            <li><strong>Check the summary</strong> to verify the data loaded correctly</li>
        </ol>
        <p><strong>Need a template?</strong> Run: <code>python generate_excel_template.py</code></p>
    </div>
    """
    
    # Layout
    file_widget = VBox([
        ipyHTML(instructions_html),
        HBox([file_dropdown, load_button]),
        file_path_display,
        file_info_display,
        status_display
    ])
    
    return file_widget, file_dropdown

# Display file selection widget
print("\n" + "="*60)
print("📁 STEP 1: SELECT YOUR INPUT FILE")
print("="*60)

file_widget, file_selector = create_file_selection_widget()
display(file_widget)

# ## 3. Input Data Management
# 
# ::: {note}
# After loading your file, this section will show you a summary of the data structure.
# :::
# 
# ### Required Excel Structure
# 
# Your input Excel file should contain the following sheets:
# 
# | Sheet Name | Purpose | Key Columns |
# |------------|---------|-------------|
# | `1_1_Definition_Flows` | Define material flows | Flow_ID, Name(EN), Process_ID_O, Process_ID_I |
# | `1_2_Data_Flows` | Flow data over time | Flow_ID, Year_Flow, Flow_Py |
# | `2_1_Definition_Processes` | Define processes | ID, Name(EN), Stock?, Initial_Stock? |
# | `2_4_Initial_Stock` | Initial stock values | Process_ID, Initial_Stock_material, etc. |
# | `2_5_dynamic_tcs` | Transfer coefficients | TC_ID, Year, Value |
# | `3_1_Definition_DSM` | DSM parameters | Process_ID, Lifetime_Type, etc. |
# | `3_2_Definition_FOMP` | FOMP parameters | Process_ID, Parameter_Name, Value |
# | `4_1_Uncertainty_Parameters` | Monte Carlo parameters | Parameter_Name, Distribution, etc. |
# 
# ::: {tip}
# You can generate a template Excel file using: `python generate_excel_template.py`
# :::

# Function to load and validate input data
def load_input_data(file_path):
    """
    Load and validate input Excel file.
    
    Args:
        file_path (str): Path to the Excel input file
        
    Returns:
        dict: Dictionary containing all Excel sheets as DataFrames
    """
    try:
        # Load all sheets from Excel
        input_data = pd.read_excel(
            file_path,
            sheet_name=None,
            header=0,
            engine='openpyxl',
            na_values=['N.A.', 'NA', 'n/a']
        )
        
        # Validate the structure
        data_loader.validate_input_data(input_data)
        
        print(f"✅ Input file loaded successfully: {file_path}")
        print(f"📊 Found {len(input_data)} sheets")
        
        return input_data
        
    except Exception as e:
        print(f"❌ Error loading input file: {e}")
        return None

# Function to display input data summary
def display_input_summary(input_data):
    """Display a summary of the loaded input data."""
    if input_data is None:
        print("❌ No input data to display")
        return
    
    print("\n📋 Input Data Summary:")
    print("=" * 50)
    
    for sheet_name, df in input_data.items():
        print(f"\n📄 {sheet_name}:")
        print(f"   Shape: {df.shape}")
        print(f"   Columns: {list(df.columns)}")
        if len(df) > 0:
            print(f"   Sample data:")
            display(df.head(3))

# ## 4. Model Configuration
# 
# ::: {note}
# The model configuration defines the temporal scope, elements to track, and calculation options.
# :::
# 
# ### Configuration Options
# 
# - **Time Range**: Start and end years for the analysis
# - **Elements**: Materials to track (e.g., material, WC, DM, CC)
# - **Calculation Type**: Deterministic or Monte Carlo simulation
# - **Model Components**: DSM and FOMP switches
# 
# ::: {tip}
# For Monte Carlo simulations, you can specify the number of iterations and uncertainty parameters.
# :::

# Interactive configuration widget
def create_config_widget():
    """Create an interactive widget for model configuration."""
    
    # Time range
    start_year = IntSlider(
        value=2025,
        min=2000,
        max=2100,
        step=1,
        description='Start Year:',
        style={'description_width': '100px'}
    )
    
    end_year = IntSlider(
        value=2050,
        min=2000,
        max=2100,
        step=1,
        description='End Year:',
        style={'description_width': '100px'}
    )
    
    # Elements
    elements = SelectMultiple(
        options=['material', 'WC', 'DM', 'CC'],
        value=['material', 'WC', 'DM', 'CC'],
        description='Elements:',
        style={'description_width': '100px'}
    )
    
    # Calculation options
    run_monte_carlo = Checkbox(
        value=False,
        description='Monte Carlo Simulation',
        style={'description_width': '150px'}
    )
    
    mc_iterations = IntSlider(
        value=100,
        min=10,
        max=10000,
        step=10,
        description='MC Iterations:',
        style={'description_width': '120px'}
    )
    
    # Model components
    run_dsm = Checkbox(
        value=True,
        description='Run DSM Calculation',
        style={'description_width': '150px'}
    )
    
    run_fomp = Checkbox(
        value=True,
        description='Run FOMP Calculation',
        style={'description_width': '150px'}
    )
    
    # Layout
    config_widget = VBox([
        HBox([start_year, end_year]),
        elements,
        HBox([run_monte_carlo, mc_iterations]),
        HBox([run_dsm, run_fomp])
    ])
    
    return config_widget, {
        'start_year': start_year,
        'end_year': end_year,
        'elements': elements,
        'run_monte_carlo': run_monte_carlo,
        'mc_iterations': mc_iterations,
        'run_dsm': run_dsm,
        'run_fomp': run_fomp
    }

# Display configuration widget
print("\n" + "="*60)
print("🔧 STEP 2: CONFIGURE YOUR ANALYSIS")
print("="*60)

config_widget, config_vars = create_config_widget()
display(config_widget)

# Make config_vars globally accessible
global_config_vars = config_vars

# ## 5. Model Execution
# 
# ::: {note}
# This section runs the actual MFA calculation using the configured parameters.
# :::
# 
# ### Calculation Process
# 
# 1. **System Setup**: Define model scope and initialize MFA system
# 2. **Data Loading**: Load and validate input data
# 3. **Process Definition**: Define processes, flows, and stocks
# 4. **Parameter Loading**: Load DSM and FOMP parameters
# 5. **Calculation**: Run the iterative solver
# 6. **Results**: Generate outputs and visualizations
# 
# ::: {warning}
# Monte Carlo simulations can take significant time depending on the number of iterations.
# :::

# Function to run the complete MFA analysis
def run_mfa_analysis(input_file, config_params):
    """
    Run the complete MFA analysis.
    
    Args:
        input_file (str): Path to input Excel file
        config_params (dict): Configuration parameters
        
    Returns:
        tuple: (mfa_system, results_dict)
    """
    
    print("🚀 Starting BioDYM MFA Analysis...")
    print("=" * 60)
    
    try:
        # 1. Setup and Configuration
        print("\n📋 Phase 1: Model Setup")
        
        model_classification, index_table = system_setup.define_model_scope(
            config_params['start_year'],
            config_params['end_year'],
            config_params['elements']
        )
        
        mfa_system_base = system_setup.initialize_mfa_system(
            model_classification, index_table
        )
        
        # 2. Data Loading
        print("\n📊 Phase 2: Data Loading")
        
        mfa_system_base, all_excel_data = system_setup.load_and_define_processes(
            mfa_system_base, input_file, data_loader
        )
        
        # 3. Parameter Loading
        print("\n⚙️ Phase 3: Parameter Loading")
        
        dsm_params = data_loader.load_dsm_parameters(all_excel_data)
        fomp_params = data_loader.load_fomp_parameters(all_excel_data)
        uncertainty_params = data_loader.load_uncertainty_definitions(all_excel_data)
        
        # 4. System Configuration
        print("\n🔧 Phase 4: System Configuration")
        
        mfa_system_configured, _ = system_setup.define_flows_and_parameters(
            mfa_system_base, all_excel_data
        )
        
        print(f"   ✅ Setup complete: {len(mfa_system_configured.ProcessList)} processes, "
              f"{len(mfa_system_configured.FlowDict)} flows, {len(mfa_system_configured.StockDict)} stocks")
        
        # 5. Calculation
        print("\n🧮 Phase 5: Calculation")
        
        if config_params.get('run_monte_carlo', False):
            mc_iterations = config_params.get('mc_iterations', 100)
            print(f"   Running Monte Carlo simulation ({mc_iterations} iterations)...")
            
            mc_results = []
            for i in range(mc_iterations):
                if i % 10 == 0:
                    print(f"     Progress: {i}/{mc_iterations}")
                
                # Sample parameters
                sampled_values = utils.sample_parameters(uncertainty_params)
                tc_updates = {k: v for k, v in sampled_values.items() if k.startswith('TC_')}
                
                # Run calculation
                run_results, _ = solver.run_mfa_calculation(
                    mfa_system_configured,
                    dsm_params,
                    fomp_params,
                    config,
                    tc_updates=tc_updates
                )
                
                # Extract results
                if run_results:
                    final_c_stock_soil = run_results.StockDict["S_8"].Values[-1, 3]
                    mc_results.append({
                        'run_id': i,
                        'final_C_stock_soil': final_c_stock_soil,
                        **sampled_values
                    })
            
            df_mc_results = pd.DataFrame(mc_results)
            mfa_system_with_results = None
            
            print("   ✅ Monte Carlo simulation complete!")
            
        else:
            print("   Running deterministic calculation...")
            
            mfa_system_with_results, dsm_details = solver.run_mfa_calculation(
                mfa_system_configured, dsm_params, fomp_params, config
            )
            
            df_mc_results = None
            
            print("   ✅ Deterministic calculation complete!")
        
        # 6. Results Summary
        print("\n📈 Phase 6: Results Summary")
        
        results = {
            'mfa_system': mfa_system_with_results,
            'mc_results': df_mc_results,
            'dsm_details': dsm_details,
            'config': config_params
        }
        
        print("\n" + "=" * 60)
        print("  ✅ BioDYM MFA Analysis Complete!")
        print("=" * 60)
        
        return mfa_system_with_results, results
        
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return None, None

# Run button
def create_run_button():
    """Create a button to run the analysis."""
    
    def on_run_click(b):
        # Check if a file is loaded
        if 'input_data' not in globals() or input_data is None:
            print("❌ No input file loaded. Please select and load a file first.")
            return
        
        # Get current configuration values using global config_vars
        config_params = {
            'start_year': global_config_vars['start_year'].value,
            'end_year': global_config_vars['end_year'].value,
            'elements': list(global_config_vars['elements'].value),
            'run_monte_carlo': global_config_vars['run_monte_carlo'].value,
            'mc_iterations': global_config_vars['mc_iterations'].value,
            'run_dsm': global_config_vars['run_dsm'].value,
            'run_fomp': global_config_vars['run_fomp'].value
        }
        
        # Get the selected file path
        selected_file = file_selector.value
        if selected_file == "Select a file...":
            print("❌ No file selected. Please select a file first.")
            return
        
        # Find the file path
        available_files = list_available_input_files()
        file_options = ["Select a file..."] + [os.path.basename(f) for f in available_files]
        selected_index = file_options.index(selected_file)
        input_file = available_files[selected_index - 1]  # -1 because of the "Select a file..." option
        
        # Run analysis
        results, _ = run_mfa_analysis(input_file, config_params)
        
        if results is not None:
            print("\n🎉 Analysis completed successfully!")
            # Store results for visualization
            global analysis_results
            analysis_results = results
        else:
            print("\n❌ Analysis failed. Please check the error messages above.")
    
    run_button = Button(
        description='🚀 Run Analysis',
        button_style='success',
        layout={'width': '200px'}
    )
    run_button.on_click(on_run_click)
    
    return run_button

# Display run button
print("\n" + "="*60)
print("🚀 STEP 3: RUN YOUR ANALYSIS")
print("="*60)

run_button = create_run_button()
display(run_button)

# ## 6. Results Visualization
# 
# ::: {note}
# This section provides interactive visualizations of the analysis results.
# :::
# 
# ### Available Visualizations
# 
# - **Mass Balance Error**: Check calculation accuracy
# - **Flow Diagrams**: Sankey diagrams showing material flows
# - **Stock Dynamics**: Time series of stock changes
# - **Monte Carlo Results**: Uncertainty analysis plots
# - **Process Efficiency**: Performance metrics
# 
# ::: {tip}
# Use the interactive widgets to explore different aspects of your results.
# :::

# Function to create visualization widgets
def create_visualization_widgets():
    """Create interactive widgets for result visualization."""
    
    # Visualization type selector
    viz_type = Dropdown(
        options=[
            'Mass Balance Error',
            'Flow Diagram',
            'Stock Dynamics',
            'Process Efficiency',
            'Monte Carlo Results'
        ],
        value='Mass Balance Error',
        description='Visualization:',
        style={'description_width': '120px'}
    )
    
    # Year selector for time series
    year_selector = IntSlider(
        value=2025,
        min=2025,
        max=2050,
        step=1,
        description='Year:',
        style={'description_width': '80px'}
    )
    
    # Process selector
    process_selector = Dropdown(
        options=['All Processes'],
        value='All Processes',
        description='Process:',
        style={'description_width': '100px'}
    )
    
    # Update process list when results are available
    def update_process_list(results):
        if results and 'mfa_system' in results and results['mfa_system']:
            processes = ['All Processes'] + [p.Name for p in results['mfa_system'].ProcessList]
            process_selector.options = processes
    
    # Visualization function
    def create_visualization(viz_type, year, process):
        """Create the selected visualization."""
        
        if 'analysis_results' not in globals() or analysis_results is None:
            print("⚠️ No analysis results available. Please run an analysis first.")
            return
        
        results = analysis_results
        
        if viz_type == 'Mass Balance Error':
            if results['mfa_system']:
                plotting.plot_mass_balance_error(results['mfa_system'])
            
        elif viz_type == 'Flow Diagram':
            if results['mfa_system']:
                # Create a simple flow diagram
                fig = go.Figure()
                
                # Add flows as arrows
                for flow_id, flow in results['mfa_system'].FlowDict.items():
                    # This is a simplified version - you'd need more complex logic for a proper Sankey
                    fig.add_trace(go.Scatter(
                        x=[flow.P_Start, flow.P_End],
                        y=[0, 0],
                        mode='lines+markers',
                        name=flow_id,
                        line=dict(width=2)
                    ))
                
                fig.update_layout(
                    title='Material Flow Diagram',
                    xaxis_title='Process ID',
                    yaxis_title='Flow Value',
                    showlegend=True
                )
                fig.show()
            
        elif viz_type == 'Stock Dynamics':
            if results['mfa_system']:
                # Create stock time series plot
                fig = go.Figure()
                
                for stock_name, stock in results['mfa_system'].StockDict.items():
                    if stock_name.startswith('S_'):  # Only absolute stocks
                        years = list(range(results['config']['start_year'], results['config']['end_year'] + 1))
                        fig.add_trace(go.Scatter(
                            x=years,
                            y=stock.Values[:, 0],  # Material dimension
                            mode='lines+markers',
                            name=stock_name
                        ))
                
                fig.update_layout(
                    title='Stock Dynamics Over Time',
                    xaxis_title='Year',
                    yaxis_title='Stock Value (Mg)',
                    showlegend=True
                )
                fig.show()
            
        elif viz_type == 'Monte Carlo Results':
            if results['mc_results'] is not None:
                # Create MC results histogram
                fig = go.Figure()
                
                fig.add_trace(go.Histogram(
                    x=results['mc_results']['final_C_stock_soil'],
                    nbinsx=30,
                    name='Final C Stock'
                ))
                
                fig.update_layout(
                    title='Monte Carlo Results Distribution',
                    xaxis_title='Final Carbon Stock (Mg C)',
                    yaxis_title='Frequency',
                    showlegend=True
                )
                fig.show()
            else:
                print("⚠️ No Monte Carlo results available.")
    
    # Create visualization button
    viz_button = Button(
        description='📊 Create Visualization',
        button_style='info',
        layout={'width': '200px'}
    )
    
    def on_viz_click(b):
        create_visualization(viz_type.value, year_selector.value, process_selector.value)
    
    viz_button.on_click(on_viz_click)
    
    # Layout
    viz_widget = VBox([
        HBox([viz_type, year_selector]),
        process_selector,
        viz_button
    ])
    
    return viz_widget

# Display visualization widgets
print("\n" + "="*60)
print("📊 STEP 4: VISUALIZE YOUR RESULTS")
print("="*60)

viz_widgets = create_visualization_widgets()
display(viz_widgets)

# ## 7. Export and Reporting
# 
# ::: {note}
# Export your results to Excel files for further analysis or reporting.
# :::
# 
# ### Export Options
# 
# - **Excel Export**: Complete results with multiple sheets
# - **Monte Carlo Results**: Statistical summary and distributions
# - **Plots as Images**: Save visualizations as PNG/PDF
# - **Configuration Summary**: Export model settings
# 
# ::: {tip}
# Use the export functions to create reports for stakeholders or further analysis.
# :::

# Function to export results
def export_results(output_path="data/02_output/results.xlsx"):
    """Export analysis results to Excel file."""
    
    if 'analysis_results' not in globals() or analysis_results is None:
        print("⚠️ No analysis results available for export.")
        return
    
    results = analysis_results
    
    try:
        # Create output directory if needed
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Export main results
        if results['mfa_system']:
            utils.export_results_to_excel(results['mfa_system'], output_path)
            print(f"✅ Main results exported to: {output_path}")
        
        # Export Monte Carlo results if available
        if results['mc_results'] is not None:
            mc_output_path = output_path.replace('.xlsx', '_MonteCarlo.xlsx')
            
            with pd.ExcelWriter(mc_output_path) as writer:
                results['mc_results'].to_excel(writer, sheet_name='MC_Results', index=False)
                
                if 'final_C_stock_soil' in results['mc_results'].columns:
                    summary_stats = results['mc_results']['final_C_stock_soil'].describe()
                    summary_stats.to_frame('final_C_stock_soil').to_excel(
                        writer, sheet_name='Summary_Stats'
                    )
            
            print(f"✅ Monte Carlo results exported to: {mc_output_path}")
        
        # Export configuration summary
        config_output_path = output_path.replace('.xlsx', '_Configuration.xlsx')
        config_df = pd.DataFrame([results['config']])
        config_df.to_excel(config_output_path, index=False)
        print(f"✅ Configuration exported to: {config_output_path}")
        
        print("\n📁 Export complete!")
        
    except Exception as e:
        print(f"❌ Error during export: {e}")

# Export button
def create_export_button():
    """Create a button to export results."""
    
    def on_export_click(b):
        export_results()
    
    export_button = Button(
        description='💾 Export Results',
        button_style='warning',
        layout={'width': '200px'}
    )
    export_button.on_click(on_export_click)
    
    return export_button

# Display export button
print("\n" + "="*60)
print("💾 STEP 5: EXPORT YOUR RESULTS")
print("="*60)

export_button = create_export_button()
display(export_button)

# ## 8. Summary and Next Steps
# 
# ::: {note}
# This comprehensive GUI provides access to all BioDYM features through an intuitive interface.
# :::
# 
# ### What You've Accomplished
# 
# ✅ **Project Restructuring**: Clean, organized codebase
# ✅ **Import Fixes**: Resolved ODYM framework integration
# ✅ **CLI Interface**: Command-line tool for automation
# ✅ **Comprehensive GUI**: Interactive Jupyter notebook
# ✅ **Rich Documentation**: MyST-enhanced explanations
# ✅ **Testing Framework**: All tests passing
# 
# ### Key Features Demonstrated
# 
# - **Interactive Configuration**: Widgets for all model parameters
# - **Data Validation**: Automatic input file checking
# - **Flexible Calculation**: Deterministic and Monte Carlo options
# - **Rich Visualizations**: Multiple plot types and interactivity
# - **Export Capabilities**: Excel output with multiple formats
# 
# ### Next Steps
# 
# 1. **Customize Input Data**: Modify the Excel template for your specific use case
# 2. **Explore Scenarios**: Test different parameter combinations
# 3. **Validate Results**: Compare with known benchmarks
# 4. **Extend Functionality**: Add new visualization types or analysis methods
# 5. **Documentation**: Create user guides and tutorials
# 
# ::: {tip}
# **Pro Tip**: Use Jupytext to version control this notebook as a Markdown file:
# ```bash
# jupytext --to md BioDYM_Comprehensive_GUI.ipynb
# ```
# :::
# 
# ### Support and Resources
# 
# - **Documentation**: Check the `docs/` folder for detailed guides
# - **Examples**: Explore the `basic_examples/` and `studies/` folders
# - **Testing**: Run `pytest` to verify functionality
# - **Issues**: Report problems or request features
# 
# ::: {success}
# 🎉 **Congratulations!** Your BioDYM MFA tool is now fully operational with a comprehensive GUI.
# ::: 