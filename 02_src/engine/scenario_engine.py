# -*- coding: utf-8 -*-
"""
Scenario Analysis Engine for BioDYM MFA Model.

This module provides functions for running scenario analysis, comparing different
parameter configurations, and generating comparative visualizations.
"""

import copy
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple

from . import solver
import data_loader
import system_setup


def run_scenario_analysis(
    config_obj,
    mfa_system_configured,
    all_excel_data,
    dsm_params,
    fomp_params,
    flow_tc_map,
    process_logic_map,
    initial_stock_configs=None,
    lfg_params=None,
    bom_params=None,
    flow_cap_params=None,
    scenario_definitions=None,
) -> Tuple[Dict, Dict]:
    """Orchestrates the entire scenario analysis process.

    This function checks if scenario analysis is enabled in the configuration,
    loads the scenario definitions from the Excel file, and then calls a helper
    function to run each selected scenario in a loop.

    Parameters
    ----------
    config_obj : object
        The main configuration object with global settings.
    mfa_system_configured : odym.MFAsystem
        A fully configured but unsolved MFA system to use as a baseline.
    all_excel_data : dict
        A dictionary of DataFrames for each sheet in the Excel file.
    dsm_params : dict
        Configuration dictionary for DSM processes.
    fomp_params : dict
        Configuration dictionary for FOMP processes.
    flow_tc_map : dict
        A map from Flow_IDs to their TC_IDs.
    process_logic_map : dict
        A map from Process_IDs to their logic string.

    Returns
    -------
    tuple
        A tuple containing:
        - all_scenario_results (dict): A dictionary of solved MFA system objects for each scenario.
        - scenario_definitions (dict): The raw scenario definition rules from Excel.
    """
    print("\n" + "=" * 60)
    print("🎭 SCENARIO ANALYSIS ENGINE")
    print("=" * 60)

    # Check if scenario analysis is enabled
    if not getattr(config_obj, "Run_Scenario_Analysis", False):
        print("ℹ️ Scenario analysis is disabled in configuration.")
        return {}, {}

    # Find all scenarios defined in the config object
    scenario_names_to_run = _extract_scenario_names(config_obj)

    if not scenario_names_to_run:
        print(
            "⚠️ Scenario Analysis is enabled, but no scenarios are selected in the configuration."
        )
        return {}, {}

    print(
        f"Found {len(scenario_names_to_run)} scenarios to run: {scenario_names_to_run}"
    )

    # Load scenario definitions — from pre-loaded dict (YAML) or Excel
    if scenario_definitions is None:
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
            process_logic_map=process_logic_map,
            initial_stock_configs=initial_stock_configs,
            lfg_params=lfg_params,
            bom_params=bom_params,
            flow_cap_params=flow_cap_params,
        )

        if scenario_result is not None:
            all_scenario_results[scenario_name] = scenario_result

    print(
        f"\n✅ Scenario analysis completed: {len(all_scenario_results)} scenarios processed"
    )
    return all_scenario_results, scenario_definitions


def _extract_scenario_names(config_obj) -> List[str]:
    """Extracts the list of scenarios to run from the configuration object.

    This function checks for attributes like `Selected_Scenario_Name_1`,
    `Selected_Scenario_Name_2`, etc., in the configuration object to build
    the list of scenarios that the user has chosen to run.

    Parameters
    ----------
    config_obj : object
        The main configuration object loaded from Excel.

    Returns
    -------
    list of str
        A list of scenario names to be executed.
    """
    scenario_names_to_run = []
    for i in range(1, 10):  # Check for up to 9 scenarios
        # Try different possible attribute name formats
        possible_names = [
            f"Selected_Scenario_Name_{i}",  # With underscore
            f"Selected Scenario Name {i}",  # With spaces
            f"Selected_Scenario_Name_{i}",  # Alternative underscore format
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
    process_logic_map: Dict,
    initial_stock_configs: Optional[Dict] = None,
    lfg_params: Optional[Dict] = None,
    bom_params: Optional[Dict] = None,
    flow_cap_params: Optional[Dict] = None,
) -> Optional[object]:
    """Runs the MFA calculation for a single, specified scenario.

    This function creates a deep copy of the baseline MFA system, applies the
    specific parameter modifications for the given scenario, and then runs
    the iterative solver.

    Parameters
    ----------
    scenario_name : str
        The name of the scenario to run.
    scenario_definitions : dict
        A dictionary containing the rules for all available scenarios.
    mfa_system_configured : odym.MFAsystem
        The baseline, configured MFA system to use as a template.
    config_obj : object
        The main configuration object.
    dsm_params : dict
        Configuration dictionary for DSM processes.
    fomp_params : dict
        Configuration dictionary for FOMP processes.
    flow_tc_map : dict
        A map from Flow_IDs to their TC_IDs.
    process_logic_map : dict
        A map from Process_IDs to their logic string.

    Returns
    -------
    odym.MFAsystem or None
        The solved MFA system object for the scenario, or None if the
        scenario calculation fails.
    """
    print("\n" + "=" * 60)
    print(f"🎭 RUNNING SCENARIO: '{scenario_name}'")
    print("=" * 60)

    if scenario_name not in scenario_definitions:
        print(
            f"⚠️ WARNING: Scenario '{scenario_name}' not found in '5_1_Scenario_Manager' sheet! Skipping."
        )
        return None

    # Create a deep copy of the configured system for this scenario
    mfa_system_scenario = copy.deepcopy(mfa_system_configured)

    # Re-register FlowCap cap parameters on the copied system.
    # deepcopy may or may not preserve _CapParam objects depending on the Python
    # version and ODYM internals.  Calling register_cap_parameters is idempotent:
    # if the key already exists in ParameterDict it is a no-op; if it was lost
    # during copy it restores a fresh baseline array that apply_scenario then
    # modifies with the scenario values.
    if flow_cap_params:
        from engine import flow_cap as _fc
        _fc.register_cap_parameters(mfa_system_scenario, flow_cap_params)

    # Apply scenario modifications (now returns modified parameters too)
    (
        mfa_system_scenario,
        dsm_params_scenario,
        fomp_params_scenario,
        initial_stock_configs_scenario,
    ) = system_setup.apply_scenario(
        mfa_system_scenario,
        scenario_definitions,
        scenario_name,
        dsm_params=dsm_params,
        fomp_params=fomp_params,
        initial_stock_configs=initial_stock_configs,
    )

    # Create scenario-specific config
    # Note: We keep RUN_MONTE_CARLO setting to allow both scenario and MC analysis
    # to run in the same workflow (they operate independently on different systems)
    scenario_config_obj = copy.deepcopy(config_obj)
    # Disable MC for individual scenario runs to avoid nested MC-in-scenario calculations
    # MC will run separately on the baseline system if enabled
    scenario_config_obj.RUN_MONTE_CARLO = False

    # Run the calculation for this scenario (using scenario-modified parameters)
    try:
        mfa_results_scenario, _, _ = solver.run_mfa_calculation(
            mfa_system_scenario,
            dsm_params_scenario,
            fomp_params_scenario,
            scenario_config_obj,
            flow_tc_map=flow_tc_map,
            process_logic_map=process_logic_map,
            lfg_params=lfg_params or {},
            bom_params=bom_params or {},
            flow_cap_params=flow_cap_params or {},
        )

        print(f"✅ Scenario '{scenario_name}' calculation completed successfully!")
        check_mass_balance(mfa_results_scenario, label=scenario_name)
        return mfa_results_scenario

    except Exception as e:
        print(f"❌ ERROR: Scenario '{scenario_name}' calculation failed: {e}")
        return None


def generate_scenario_comparison_visualizations(
    baseline_results, all_scenario_results: Dict, scenario_definitions: Dict
) -> None:
    """Generates and displays a suite of comparative scenario visualizations.

    This function calls various plotting functions from the `plotting` module
    to create charts that compare the baseline results against all calculated
    scenarios.

    Parameters
    ----------
    baseline_results : odym.MFAsystem
        The solved MFA system object for the baseline run.
    all_scenario_results : dict
        A dictionary of solved MFA system objects for each scenario.
    scenario_definitions : dict
        A dictionary containing the rules for all available scenarios.
    """
    if not all_scenario_results:
        print("ℹ️ No scenario results available for visualization.")
        return

    print("\n" + "=" * 60)
    print("📊 SCENARIO COMPARISON VISUALIZATIONS")
    print("=" * 60)

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
            scenario_definitions=scenario_definitions,
        )

        # Generate scenario flow dynamics plot
        print("📈 Generating scenario flow dynamics plot...")
        plotting.plot_scenario_flow_dynamics(
            baseline_results=baseline_results,
            all_scenario_results=all_scenario_results,
            scenario_definitions=scenario_definitions,
        )

        # Generate scenario stock dynamics plot
        print("📈 Generating scenario stock dynamics plot...")
        plotting.plot_scenario_stock_dynamics(
            baseline_results=baseline_results,
            all_scenario_results=all_scenario_results,
            scenario_definitions=scenario_definitions,
        )

        print("✅ Scenario comparison visualizations completed!")

    except ImportError as e:
        print(f"❌ ERROR: Could not import plotting module: {e}")
    except Exception as e:
        print(f"❌ ERROR: Visualization generation failed: {e}")


def export_scenario_results(
    all_scenario_results: Dict,
    scenario_definitions: Dict,
    output_dir: str = "01_data/02_output/scenarios",
) -> None:
    """Exports the results of each scenario to a separate Excel file.

    Parameters
    ----------
    all_scenario_results : dict
        A dictionary of solved MFA system objects for each scenario.
    scenario_definitions : dict
        A dictionary containing the rules for all available scenarios.
    output_dir : str, optional
        The directory where the result files will be saved.
        Default is "01_data/02_output/scenario_output".
    """
    if not all_scenario_results:
        print("ℹ️ No scenario results to export.")
        return

    print(f"\n📁 Exporting scenario results to {output_dir}...")

    try:
        import os

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Export each scenario result (overwrites existing files)
        for scenario_name, scenario_result in all_scenario_results.items():
            filename = f"{output_dir}/scenario_{scenario_name}.xlsx"

            # Use the existing export function
            from utils import export_results_to_excel

            export_results_to_excel(
                mfa_system_results=scenario_result,
                output_path=filename,
                input_file_path=f"Scenario: {scenario_name}",
            )

        print("✅ Scenario results exported successfully!")

    except Exception as e:
        print(f"❌ ERROR: Scenario export failed: {e}")


def check_mass_balance(mfa_system_results, label: str = "System") -> pd.DataFrame:
    """Checks mass balance for a solved MFA system and returns error summary.

    Computes (inflows - outflows - dS) for each process and element over all
    years, excluding system boundary processes. Returns a DataFrame with the
    maximum absolute error per element.

    Parameters
    ----------
    mfa_system_results : odym.MFAsystem
        The solved MFA system object.
    label : str, optional
        Label for this check (e.g. scenario name). Defaults to "System".

    Returns
    -------
    pd.DataFrame
        Summary with columns: Element, Max_Abs_Error, Sum_Abs_Error, Status.
    """
    unit = getattr(mfa_system_results, "Unit", "Mg")
    element_items = [e.lower() for e in mfa_system_results.Elements]
    num_processes = len(mfa_system_results.ProcessList)
    num_elements = len(element_items)
    num_years = len(mfa_system_results.IndexTable.Classification["Time"].Items)

    # Build inflow/outflow/dS matrices
    total_inflows = np.zeros((num_years, num_processes, num_elements))
    total_outflows = np.zeros((num_years, num_processes, num_elements))

    for flow in mfa_system_results.FlowDict.values():
        if flow.P_Start < num_processes and flow.P_End < num_processes:
            total_inflows[:, flow.P_End, :] += flow.Values
            total_outflows[:, flow.P_Start, :] += flow.Values

    total_ds = np.zeros((num_years, num_processes, num_elements))
    for p_idx, p in enumerate(mfa_system_results.ProcessList):
        ds_stock = mfa_system_results.StockDict.get(f"dS_{p.ID}")
        if ds_stock is not None:
            total_ds[:, p_idx, :] = ds_stock.Values

    balance_matrix = total_inflows - total_outflows - total_ds

    # Identify boundary processes to exclude
    boundary_mask = np.zeros(num_processes, dtype=bool)
    for p_idx in range(num_processes):
        avg_in = np.mean(total_inflows[:, p_idx, :])
        avg_out = np.mean(total_outflows[:, p_idx, :])
        avg_ds = np.mean(total_ds[:, p_idx, :])
        is_boundary = (
            ((avg_in == 0) and (avg_out > 0) and (abs(avg_ds) < 1e-10))
            or ((avg_in > 0) and (avg_out == 0) and (abs(avg_ds) < 1e-10))
        )
        boundary_mask[p_idx] = is_boundary

    # Compute errors excluding boundary processes
    internal_balance = balance_matrix[:, ~boundary_mask, :]

    summary_rows = []
    all_pass = True
    for e_idx, element in enumerate(element_items):
        errors = internal_balance[:, :, e_idx]
        max_abs = np.max(np.abs(errors))
        sum_abs = np.sum(np.abs(errors))
        # Tolerance: error < 1e-6 Mg is considered negligible
        status = "PASS" if max_abs < 1e-6 else "WARN"
        if status == "WARN":
            all_pass = False
        summary_rows.append({
            "Element": element.upper(),
            "Max_Abs_Error_Mg": max_abs,
            "Sum_Abs_Error_Mg": sum_abs,
            "Status": status,
        })

    df = pd.DataFrame(summary_rows)

    # Print summary
    if all_pass:
        print(f"   ✅ Mass balance check [{label}]: PASSED (all elements < 1e-6 {unit})")
    else:
        print(f"   ⚠️ Mass balance check [{label}]:")
        for _, row in df.iterrows():
            marker = "✅" if row["Status"] == "PASS" else "⚠️"
            print(f"      {marker} {row['Element']}: max error = {row['Max_Abs_Error_Mg']:.2e} {unit}")

    return df


def get_scenario_summary(
    all_scenario_results: Dict, scenario_definitions: Dict
) -> pd.DataFrame:
    """Generates a summary DataFrame comparing key metrics across scenarios.

    Parameters
    ----------
    all_scenario_results : dict
        A dictionary of solved MFA system objects for each scenario.
    scenario_definitions : dict
        A dictionary containing the rules for all available scenarios.

    Returns
    -------
    pd.DataFrame
        A DataFrame where each row summarizes a scenario with key metrics.
    """
    if not all_scenario_results:
        return pd.DataFrame()

    summary_data = []

    for scenario_name, scenario_result in all_scenario_results.items():
        # Extract key metrics (customize based on your needs)
        scenario_summary = {
            "Scenario": scenario_name,
            "Total_Stocks": len(scenario_result.StockDict),
            "Total_Flows": len(scenario_result.FlowDict),
            "Elements": ", ".join(scenario_result.Elements),
            "Time_Period": f"{scenario_result.IndexTable.Classification['Time'].Items[0]}-{scenario_result.IndexTable.Classification['Time'].Items[-1]}",
        }

        # Add scenario-specific metrics
        scenario_def = scenario_definitions.get(scenario_name, [])
        scenario_summary["Parameter_Changes"] = len(scenario_def)

        summary_data.append(scenario_summary)

    return pd.DataFrame(summary_data)
