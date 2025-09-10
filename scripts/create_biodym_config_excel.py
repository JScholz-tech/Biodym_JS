# -*- coding: utf-8 -*-
"""
BioDYM Configuration Generator

This script creates a well-structured Excel configuration file for the BioDYM MFA Tool.
The configuration is organized into logical categories for better usability.
"""

import pandas as pd
import os
from datetime import datetime

def create_biodym_config_excel(output_path="data/01_input/BioDYM_Configuration_Template.xlsx"):
    """
    Creates a comprehensive Excel configuration file for BioDYM MFA Tool.
    
    Args:
        output_path (str): Path where to save the Excel file
    """
    
    # Define configuration settings organized by category
    config_data = [
        # Header information
        ["BioDYM MFA Tool - Configuration Settings", "", "", "", ""],
        ["Generated:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "", "", ""],
        ["Version:", "2.0", "", "", ""],
        ["", "", "", "", ""],
        
        # CORE SETTINGS
        ["CORE SETTINGS", "", "", "", ""],
        ["Setting Name", "Value", "Description", "Category", "Status"],
        ["Start_Year", 2025, "Analysis start year", "Core", "Required"],
        ["End_Year", 2050, "Analysis end year", "Core", "Required"],
        ["Elements", "material,WC,DM,CC", "Elements to track (comma-separated)", "Core", "Required"],
        ["Input_File", "data/01_input/250902_CS1_Wheat_Straw.xlsx", "Path to Excel input file", "Core", "Required"],
        ["Output_File", "data/02_output/results.xlsx", "Path for results output", "Core", "Required"],
        ["", "", "", "", ""],
        
        # CALCULATION SETTINGS
        ["CALCULATION SETTINGS", "", "", "", ""],
        ["Setting Name", "Value", "Description", "Category", "Status"],
        ["Run_DSM_Calculation", True, "Enable Dynamic Stock Model calculation", "Calculation", "Required"],
        ["Run_FOMP_Calculation", True, "Enable First-Order Material Process calculation", "Calculation", "Required"],
        ["Run_Monte_Carlo", False, "Enable Monte Carlo uncertainty analysis", "Calculation", "Optional"],
        ["MC_Iterations", 100, "Number of Monte Carlo iterations", "Calculation", "Optional"],
        ["", "", "", "", ""],
        
        # SCENARIO SETTINGS
        ["SCENARIO ANALYSIS SETTINGS", "", "", "", ""],
        ["Setting Name", "Value", "Description", "Category", "Status"],
        ["Run_Scenario_Analysis", False, "Enable scenario comparison analysis", "Scenario", "Optional"],
        ["Selected_Scenario_1", "N/A", "First scenario name to analyze", "Scenario", "Optional"],
        ["Selected_Scenario_2", "N/A", "Second scenario name to analyze", "Scenario", "Optional"],
        ["Selected_Scenario_3", "N/A", "Third scenario name to analyze", "Scenario", "Optional"],
        ["Scenario_Comparison_Metrics", "All", "Metrics to compare (All, Stocks, Flows, Efficiency)", "Scenario", "Optional"],
        ["", "", "", "", ""],
        
        # VISUALIZATION SETTINGS
        ["VISUALIZATION SETTINGS", "", "", "", ""],
        ["Setting Name", "Value", "Description", "Category", "Status"],
        ["Min_Flow_Threshold", 0.1, "Minimum flow value to display (Mg)", "Visualization", "Required"],
        ["Show_Zero_Flows", False, "Show flows with zero values in plots", "Visualization", "Optional"],
        ["Plot_Interactivity", "High", "Plot interactivity level (Low, Medium, High)", "Visualization", "Optional"],
        ["Color_Scheme", "BioDYM", "Color scheme (BioDYM, Scientific, Custom)", "Visualization", "Optional"],
        ["Export_Plots", True, "Automatically export plots as images", "Visualization", "Optional"],
        ["Plot_Resolution", "High", "Plot resolution (Low, Medium, High)", "Visualization", "Optional"],
        ["", "", "", "", ""],
        
        # EXPORT SETTINGS
        ["EXPORT SETTINGS", "", "", "", ""],
        ["Setting Name", "Value", "Description", "Category", "Status"],
        ["Export_Format", "Excel", "Export file format (Excel, CSV, JSON)", "Export", "Required"],
        ["Auto_Save_Results", True, "Automatically save results after calculation", "Export", "Optional"],
        ["Export_Detail_Level", "Full", "Export detail level (Summary, Full, Debug)", "Export", "Optional"],
        ["Export_Plots_As_Images", True, "Export plots as PNG images", "Export", "Optional"],
        ["Export_Directory", "exports", "Directory for exported files", "Export", "Optional"],
        ["", "", "", "", ""],
        
        # NICE TO HAVE SETTINGS (Advanced)
        ["NICE TO HAVE SETTINGS (Advanced)", "", "", "", ""],
        ["Setting Name", "Value", "Description", "Category", "Status"],
        ["Mass_Balance_Tolerance", 0.001, "Tolerance for mass balance validation", "Advanced", "Nice to Have"],
        ["Data_Validation_Level", "Strict", "Data validation strictness (Loose, Normal, Strict)", "Advanced", "Nice to Have"],
        ["Error_Handling_Mode", "Verbose", "Error message level (Quiet, Normal, Verbose)", "Advanced", "Nice to Have"],
        ["Debug_Mode", False, "Enable debug output and logging", "Advanced", "Nice to Have"],
        ["Performance_Monitoring", False, "Enable performance monitoring", "Advanced", "Nice to Have"],
    ]

    # Convert to DataFrame and write to Excel
    df = pd.DataFrame(config_data)
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Settings', index=False, header=False)
        
        # Derived sheet with only key-value for programmatic access
        settings_only = []
        started = False
        for row in config_data:
            if row and row[0] == 'Setting Name':
                started = True
                continue
            if started and row and row[0] not in ("", "CORE SETTINGS", "CALCULATION SETTINGS", "SCENARIO ANALYSIS SETTINGS", "VISUALIZATION SETTINGS", "EXPORT SETTINGS", "NICE TO HAVE SETTINGS (Advanced)"):
                if len(row) >= 2:
                    settings_only.append([row[0], row[1]])
        pd.DataFrame(settings_only, columns=["Setting_Name", "Value"]).to_excel(writer, sheet_name='Settings_Only', index=False)

    print(f"✅ Configuration file created: {output_path}")
    return output_path

def create_config_validation_script():
    """
    Creates a Python script to validate the configuration file.
    """
    validation_script = '''# -*- coding: utf-8 -*-
"""
BioDYM Configuration Validator

This script validates the configuration file to ensure all required settings are present
and have valid values.
"""

import pandas as pd
import os

def validate_config_file(config_path):
    """
    Validate the BioDYM configuration file.
    
    Args:
        config_path (str): Path to the configuration Excel file
        
    Returns:
        tuple: (is_valid, errors, warnings)
    """
    try:
        # Load configuration
        config_df = pd.read_excel(config_path, sheet_name='Settings_Only')
        
        errors = []
        warnings = []
        
        # Required settings
        required_settings = [
            'Start_Year', 'End_Year', 'Elements', 'Input_File', 'Output_File',
            'Run_DSM_Calculation', 'Run_FOMP_Calculation', 'Min_Flow_Threshold',
            'Export_Format'
        ]
        
        # Check required settings
        for setting in required_settings:
            if setting not in config_df['Setting_Name'].values:
                errors.append(f"Missing required setting: {setting}")
        
        # Validate specific settings
        for _, row in config_df.iterrows():
            setting_name = row['Setting_Name']
            value = row['Value']
            
            if setting_name == 'Start_Year' and not isinstance(value, (int, float)):
                errors.append("Start_Year must be a number")
            elif setting_name == 'End_Year' and not isinstance(value, (int, float)):
                errors.append("End_Year must be a number")
            elif setting_name == 'Elements' and not isinstance(value, str):
                errors.append("Elements must be a string")
            elif setting_name in ['Run_DSM_Calculation', 'Run_FOMP_Calculation'] and not isinstance(value, bool):
                warnings.append(f"{setting_name} should be True or False")
        
        is_valid = len(errors) == 0
        
        return is_valid, errors, warnings
        
    except Exception as e:
        return False, [f"Error loading configuration: {e}"], []

if __name__ == "__main__":
    config_path = "data/01_input/BioDYM_Configuration_Template.xlsx"
    
    if os.path.exists(config_path):
        is_valid, errors, warnings = validate_config_file(config_path)
        
        if is_valid:
            print("✅ Configuration file is valid!")
            if warnings:
                print("⚠️ Warnings:")
                for warning in warnings:
                    print(f"   - {warning}")
        else:
            print("❌ Configuration file has errors:")
            for error in errors:
                print(f"   - {error}")
    else:
        print(f"❌ Configuration file not found: {config_path}")
'''
    
    with open("validate_config.py", "w") as f:
        f.write(validation_script)
    
    print("✅ Configuration validator script created: validate_config.py")

if __name__ == "__main__":
    # Create the configuration file
    config_path = create_biodym_config_excel()
    
    # Create validation script
    create_config_validation_script()
    
    print("\n🎉 BioDYM Configuration Generator Complete!")
    print("📁 Files created:")
    print(f"   - {config_path}")
    print("   - validate_config.py")
    print("\n📖 Next steps:")
    print("   1. Review the configuration file")
    print("   2. Modify values as needed")
    print("   3. Run validate_config.py to check for errors")
    print("   4. Use the configuration in your BioDYM analysis")

