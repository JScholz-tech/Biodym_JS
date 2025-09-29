# -*- coding: utf-8 -*-
"""
Scenario Analysis Engine for BioDYM MFA Model.

This module provides functions for running scenario analysis, comparing different
parameter configurations, and generating comparative visualizations.
"""

import copy
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple

from . import solver
from src import data_loader
from src import system_setup


def run_scenario_analysis(
    config_obj,
    mfa_system_configured,
    all_excel_data,
    dsm_params,
    fomp_params,
    flow_tc_map,
    process_logic_map
) -> Tuple[Dict, Dict]:
    """
    Runs scenario analysis based on configuration settings.
    
    Args:
        config_obj: Configuration object with scenario settings
        mfa_system_configured: Configured MFA system (baseline)
        all_excel_data: Complete Excel data dictionary
        dsm_params: DSM parameters dictionary
        fomp_params: FOMP parameters dictionary
        flow_tc_map: Flow to TC mapping dictionary
        process_logic_map: Process logic mapping dictionary
        
    Returns:
        Tuple[Dict, Dict]: (all_scenario_results, scenario_definitions)
    """
    print("\n" + "="*60)
    print("🎭 SCENARIO ANALYSIS ENGINE")
    print("="*60)
    
    # Check if scenario analysis is enabled
    if not getattr(config_obj, 'Run_Scenario_Analysis', False):
        print("ℹ️ Scenario analysis is disabled in configuration.")
        return {}, {}
    
    # Find all scenarios defined in the config object
    scenario_names_to_run = _extract_scenario_names(config_obj)
    
    if not scenario_names_to_run:
        print("⚠️ Scenario Analysis is enabled, but no scenarios are selected in the configuration.")
        return {}, {}
    
    print(f"Found {len(scenario_names_to_run)} scenarios to run: {scenario_names_to_run}")
    
    # Load scenario definitions from Excel
    scenario_definitions = data_loader.load_scenario_definitions(all_excel_data)
    
    # Run each scenario
    all_scenario_results = {}
    for scenario_name in scenario_names_to_run:
        scenario_result = _run_single_scenario(
            scenario_name=scenario_name,
            scenario_definitions=scenario_definitions,
            mfa_system_configured=mfa_system_configured,
            config_obj=config_obj,
            dsm_params=dsm_params,
            fomp_params=fomp_params,
            flow_tc_map=flow_tc_map,
            process_logic_map=process_logic_map
        )
        
        if scenario_result is not None:
            all_scenario_results[scenario_name] = scenario_result
    
    print(f"\n✅ Scenario analysis completed: {len(all_scenario_results)} scenarios processed")
    return all_scenario_results, scenario_definitions


def _extract_scenario_names(config_obj) -> List[str]:
    """
    Extract scenario names from configuration object.
    
    Args:
        config_obj: Configuration object
        
    Returns:
        List[str]: List of scenario names to run
    """
    scenario_names_to_run = []
    for i in range(1, 10):  # Check for up to 9 scenarios
        # Try different possible attribute name formats
        possible_names = [
            f'Selected_Scenario_Name_{i}',      # With underscore
            f'Selected Scenario Name {i}',       # With spaces
            f'Selected_Scenario_Name_{i}',      # Alternative underscore format
        ]
        
        scenario_name = None
        for attr_name in possible_names:
            if hasattr(config_obj, attr_name):
                scenario_name = getattr(config_obj, attr_name)
                if scenario_name and not pd.isna(scenario_name):
                    break
        
        if scenario_name:
            scenario_names_to_run.append(scenario_name)
    
    return scenario_names_to_run


def _run_single_scenario(
    scenario_name: str,
    scenario_definitions: Dict,
    mfa_system_configured,
    config_obj,
    dsm_params: Dict,
    fomp_params: Dict,
    flow_tc_map: Dict,
    process_logic_map: Dict
) -> Optional[object]:
    """
    Run a single scenario calculation.
    
    Args:
        scenario_name: Name of the scenario to run
        scenario_definitions: Dictionary of all scenario definitions
        mfa_system_configured: Configured MFA system (baseline)
        config_obj: Configuration object
        dsm_params: DSM parameters dictionary
        fomp_params: FOMP parameters dictionary
        flow_tc_map: Flow to TC mapping dictionary
        process_logic_map: Process logic mapping dictionary
        
    Returns:
        MFA system results object or None if scenario not found
    """
    print("\n" + "="*60)
    print(f"🎭 RUNNING SCENARIO: '{scenario_name}'")
    print("="*60)
    
    if scenario_name not in scenario_definitions:
        print(f"⚠️ WARNING: Scenario '{scenario_name}' not found in '5_1_Scenario_Manager' sheet! Skipping.")
        return None
    
    # Create a deep copy of the configured system for this scenario
    mfa_system_scenario = copy.deepcopy(mfa_system_configured)
    
    # Apply scenario modifications
    mfa_system_scenario = system_setup.apply_scenario(
        mfa_system_scenario, 
        scenario_definitions, 
        scenario_name
    )
    
    # Create scenario-specific config (disable Monte Carlo for scenarios)
    scenario_config_obj = copy.deepcopy(config_obj)
    scenario_config_obj.RUN_MONTE_CARLO = False
    
    # Run the calculation for this scenario
    try:
        mfa_results_scenario, _ = solver.run_mfa_calculation(
            mfa_system_scenario, 
            dsm_params, 
            fomp_params, 
            scenario_config_obj, 
            flow_tc_map=flow_tc_map, 
            process_logic_map=process_logic_map
        )
        
        print(f"✅ Scenario '{scenario_name}' calculation completed successfully!")
        return mfa_results_scenario
        
    except Exception as e:
        print(f"❌ ERROR: Scenario '{scenario_name}' calculation failed: {e}")
        return None


def generate_scenario_comparison_visualizations(
    baseline_results,
    all_scenario_results: Dict,
    scenario_definitions: Dict
) -> None:
    """
    Generate comparative visualizations for scenario analysis.
    
    Args:
        baseline_results: Baseline MFA system results
        all_scenario_results: Dictionary of scenario results
        scenario_definitions: Dictionary of scenario definitions
    """
    if not all_scenario_results:
        print("ℹ️ No scenario results available for visualization.")
        return
    
    print("\n" + "="*60)
    print("📊 SCENARIO COMPARISON VISUALIZATIONS")
    print("="*60)
    
    # Import plotting module dynamically to avoid circular imports
    try:
        import plotting
        import importlib
        importlib.reload(plotting)
        
        # Generate multi-scenario comparison plot
        print("📈 Generating multi-scenario comparison plot...")
        plotting.plot_multi_scenario_comparison(
            baseline_results=baseline_results, 
            all_scenario_results=all_scenario_results,
            scenario_definitions=scenario_definitions
        )
        
        # Generate scenario flow dynamics plot
        print("📈 Generating scenario flow dynamics plot...")
        plotting.plot_scenario_flow_dynamics(
            baseline_results=baseline_results,
            all_scenario_results=all_scenario_results,
            scenario_definitions=scenario_definitions
        )
        
        print("✅ Scenario comparison visualizations completed!")
        
    except ImportError as e:
        print(f"❌ ERROR: Could not import plotting module: {e}")
    except Exception as e:
        print(f"❌ ERROR: Visualization generation failed: {e}")


def export_scenario_results(
    all_scenario_results: Dict,
    scenario_definitions: Dict,
    output_dir: str = "data/02_output"
) -> None:
    """
    Export scenario results to Excel files.
    
    Args:
        all_scenario_results: Dictionary of scenario results
        scenario_definitions: Dictionary of scenario definitions
        output_dir: Output directory for results
    """
    if not all_scenario_results:
        print("ℹ️ No scenario results to export.")
        return
    
    print(f"\n📁 Exporting scenario results to {output_dir}...")
    
    try:
        import os
        from datetime import datetime
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate timestamp for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Export each scenario result
        for scenario_name, scenario_result in all_scenario_results.items():
            filename = f"{output_dir}/scenario_{scenario_name}_{timestamp}.xlsx"
            
            # Use the existing export function
            from src.utils import export_results_to_excel
            export_results_to_excel(
                mfa_system_results=scenario_result,
                output_path=filename,
                input_file_path=f"Scenario: {scenario_name}"
            )
        
        print(f"✅ Scenario results exported successfully!")
        
    except Exception as e:
        print(f"❌ ERROR: Scenario export failed: {e}")


def get_scenario_summary(
    all_scenario_results: Dict,
    scenario_definitions: Dict
) -> pd.DataFrame:
    """
    Generate a summary DataFrame comparing key metrics across scenarios.
    
    Args:
        all_scenario_results: Dictionary of scenario results
        scenario_definitions: Dictionary of scenario definitions
        
    Returns:
        pd.DataFrame: Summary comparison of scenarios
    """
    if not all_scenario_results:
        return pd.DataFrame()
    
    summary_data = []
    
    for scenario_name, scenario_result in all_scenario_results.items():
        # Extract key metrics (customize based on your needs)
        scenario_summary = {
            'Scenario': scenario_name,
            'Total_Stocks': len(scenario_result.StockDict),
            'Total_Flows': len(scenario_result.FlowDict),
            'Elements': ', '.join(scenario_result.Elements),
            'Time_Period': f"{scenario_result.IndexTable.Classification['Time'].Items[0]}-{scenario_result.IndexTable.Classification['Time'].Items[-1]}"
        }
        
        # Add scenario-specific metrics
        scenario_def = scenario_definitions.get(scenario_name, [])
        scenario_summary['Parameter_Changes'] = len(scenario_def)
        
        summary_data.append(scenario_summary)
    
    return pd.DataFrame(summary_data)
