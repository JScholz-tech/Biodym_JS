# -*- coding: utf-8 -*-
"""
Main Executable for the BioDYM MFA Model.

This script serves as the central entry point for running the model. It
imports the necessary modules for configuration, data loading, calculation,
and plotting, and then orchestrates the entire workflow from setup to
result visualization.

To run the model, execute this script from your terminal:
`python main.py`
"""

import os
import sys
import pandas as pd

# --- Add project structure to system path ---
# This allows us to import our custom modules and the ODYM framework.
# It assumes the ODYM and bioDYM frameworks are in a 'framework' folder
# at the project root level.

# Path to the 'src' directory of our project
src_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, src_path)

# Path to the project root to find the 'framework' folder
project_root = os.path.dirname(src_path)

# Add ODYM framework to path
odym_path = os.path.join(
    project_root, "framework", "ODYM-master_20241127", "odym", "modules"
)
sys.path.insert(0, odym_path)

# Add bioDYM add-on to path
biodym_addon_path = os.path.join(
    project_root, "framework", "bioDYM_add-on", "modules"
)
sys.path.insert(0, biodym_addon_path)

# --- Import Custom and External Modules ---
try:
    import config
    import data_loader
    import system_setup
    import utils
    from engine import solver
    import plotting
    import ODYM_Classes as msc
    from tqdm import tqdm
except ImportError as e:
    print(f"FATAL ERROR: A required module could not be imported: {e}")
    print("Please ensure all project files and dependencies are correctly installed.")
    sys.exit(1)


def main():
    """
    Main function to orchestrate the MFA model execution.
    """
    print("========================================")
    print("  STARTING BioDYM MFA MODEL EXECUTION   ")
    print("========================================")

    # --- 1. SETUP AND CONFIGURATION ---
    print("\n--- PHASE 1: MODEL SETUP ---")
    model_classification, index_table = system_setup.define_model_scope(
        config.START_YEAR, config.END_YEAR, config.ELEMENTS
    )
    mfa_system_base = system_setup.initialize_mfa_system(
        model_classification, index_table
    )

    # Load all data from Excel and define process/stock structures
    excel_file_full_path = os.path.join(
        os.path.dirname(src_path), "data", "01_input", config.EXCEL_FILE_PATH
    )
    mfa_system_base, all_excel_data = system_setup.load_and_define_processes(
        mfa_system_base, excel_file_full_path, data_loader
    )

    # Load model-specific parameters
    dsm_params = data_loader.load_dsm_parameters(all_excel_data)
    fomp_params = data_loader.load_fomp_parameters(all_excel_data)
    uncertainty_params = data_loader.load_uncertainty_definitions(all_excel_data)

    # Configure the base system with flows and parameters
    mfa_system_configured, _ = system_setup.define_flows_and_parameters(
        mfa_system_base, all_excel_data
    )

    # Process dynamic TCs if available
    dynamic_tc_sheet = all_excel_data.get('2_5_dynamic_tcs')
    if dynamic_tc_sheet is not None and not dynamic_tc_sheet.empty:
        print("--> Processing dynamic transfer coefficients...")
        dynamic_tcs = system_setup.create_dynamic_tc_parameters(
            dynamic_tc_sheet, mfa_system_configured.IndexTable.Classification['Time'].Items
        )
        # Add dynamic TCs to the system parameters
        for name, values in dynamic_tcs.items():
            mfa_system_configured.ParameterDict[name] = msc.Parameter(
                Name=name,
                ID=len(mfa_system_configured.ParameterDict) + 1,
                Values=values,
                Unit="1"
            )
        print(f"--> Dynamic TCs processed: {len(dynamic_tcs)} parameters added")
    else:
        print("--> No dynamic TCs found in input data")

    # --- 2. CALCULATION ---
    print("\n--- PHASE 2: CALCULATION ---")
    df_mc_results = None
    mfa_system_with_results = None
    dsm_details = None

    if config.RUN_MONTE_CARLO:
        print(
            f"\n--- Starting Monte Carlo Simulation ({config.MC_ITERATIONS} iterations) ---"
        )
        mc_run_results = []
        iterator = tqdm(range(config.MC_ITERATIONS), desc="MC Runs")

        for i in iterator:
            # 1. Sample new parameter values for this iteration - This should be in a utils file
            sampled_values = utils.sample_parameters(uncertainty_params)
            tc_updates = {
                k: v for k, v in sampled_values.items() if k.startswith("TC_")
            }

            # 2. Run the calculation with the sampled parameters
            run_results, _ = solver.run_mfa_calculation(
                mfa_system_configured,
                dsm_params,
                fomp_params,
                config,
                tc_updates=tc_updates,
            )

            # 3. Extract and store Key Performance Indicators (KPIs)
            if run_results:
                final_c_stock_soil = run_results.StockDict["S_8"].Values[-1, 3]
                current_run_data = sampled_values.copy()
                current_run_data["run_id"] = i
                current_run_data["final_C_stock_soil"] = final_c_stock_soil
                mc_run_results.append(current_run_data)

        df_mc_results = pd.DataFrame(mc_run_results)
        print("\n--- Monte Carlo Simulation Complete ---")

    else:
        print("\n--- Starting Single Deterministic Run ---")
        mfa_system_with_results, dsm_details = solver.run_mfa_calculation(
            mfa_system_configured, dsm_params, fomp_params, config
        )
        print("\n--- Calculation Complete ---")

    # --- 3. VISUALIZATION ---
    print("\n--- PHASE 3: VISUALIZATION ---")
    if config.RUN_MONTE_CARLO:
        if df_mc_results is not None and not df_mc_results.empty:
            print("\nDisplaying Monte Carlo results...")
            plotting.plot_mc_distribution(
                df_mc_results, "final_C_stock_soil", unit="Mg C"
            )

            uncertain_input_to_test = "fomp_8_k1"
            if uncertain_input_to_test in df_mc_results.columns:
                plotting.plot_mc_sensitivity_scatter(
                    df_mc_results,
                    uncertain_input_to_test,
                    "final_C_stock_soil",
                    unit="Mg C",
                )
        else:
            print(
                "\nINFO: Monte Carlo run was selected, but no results were generated."
            )
    else:
        if mfa_system_with_results is not None:
            print("\nDisplaying results for single run...")
            print("\nDisplaying Mass Balance Check:")
            plotting.plot_optimized_mass_balance_error(mfa_system_with_results)

            print("\nDisplaying interactive Sankey diagram:")
            plotting.plot_interactive_sankey(mfa_system_with_results)

            print("\nDisplaying Inflow-Stock-Outflow Dynamics:")
            plotting.plot_process_dynamics(
                mfa_system_with_results, all_excel_data["2_1_Definition_Processes"]
            )

            if dsm_details:
                print("\nDisplaying Dynamic Stock Composition:")
                plotting.plot_dynamic_stock_composition(
                    dsm_details, mfa_system_with_results
                )
        else:
            print("\nINFO: Single run was selected, but no results were generated.")

    print("\n========================================")
    print("   BioDYM MFA MODEL EXECUTION FINISHED  ")
    print("========================================")


if __name__ == "__main__":
    main()
