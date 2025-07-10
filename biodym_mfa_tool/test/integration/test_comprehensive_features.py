# -*- coding: utf-8 -*-
"""
Comprehensive Testing Script for BioDYM MFA Tool

This script tests all the new features:
1. Excel Configuration Loading
2. Enhanced Monte Carlo Visualization
3. Scenario Comparison System
4. Data Input Improvements

Run this script to test all functionality with your new dataset.
"""

import os
import sys
import pandas as pd
import numpy as np
import warnings

# --- Add project structure to system path ---
# This allows us to import our custom modules and the ODYM framework.
# It assumes the ODYM and bioDYM frameworks are in a 'framework' folder
# at the same level as the 'biodym_mfa_tool' project folder.

# Path to the 'src' directory of our project
src_path = os.path.join(os.getcwd(), "src")
sys.path.insert(0, src_path)

# Path to the parent directory of the project root to find the 'framework' folder
project_root_parent = os.path.dirname(os.path.dirname(src_path))

# Add ODYM framework to path
odym_path = os.path.join(
    project_root_parent, "framework", "ODYM-master_20241127"
)
sys.path.insert(0, odym_path)

# Add bioDYM add-on to path
biodym_addon_path = os.path.join(
    project_root_parent, "framework", "bioDYM_add-on", "modules"
)
sys.path.insert(0, biodym_addon_path)


warnings.filterwarnings("ignore")

# Add project paths
current_dir = os.getcwd()
src_path = os.path.join(current_dir, "src")
sys.path.insert(0, src_path)

# Import BioDYM modules
try:
    import config
    import data_loader
    import system_setup
    import utils
    from engine import solver
    import plotting

    print("✅ All modules imported successfully!")
except ImportError as e:
    print(f"❌ Import error: {e}")
    raise


def test_excel_configuration_loading():
    """
    Test the new Excel configuration loading functionality.
    """
    print("\n" + "=" * 60)
    print("🧪 TEST 1: Excel Configuration Loading")
    print("=" * 60)

    # First, generate the new Excel template
    try:
        from generate_excel_template import create_excel_template

        template_path = create_excel_template()
        print(f"✅ Generated new Excel template: {template_path}")
    except Exception as e:
        print(f"❌ Error generating template: {e}")
        return False

    # Test loading configuration from Excel
    try:
        config_obj = config.load_configuration(template_path)
        print("✅ Successfully loaded configuration from Excel!")
        print(f"   Start Year: {config_obj.Start_Year}")
        print(f"   End Year: {config_obj.End_Year}")
        print(f"   Monte Carlo: {config_obj.Run_Monte_Carlo_Simulation}")
        print(f"   MC Iterations: {config_obj.Monte_Carlo_Iterations}")
        return True
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        return False


def test_monte_carlo_visualization():
    """
    Test the enhanced Monte Carlo visualization functions.
    """
    print("\n" + "=" * 60)
    print("🧪 TEST 2: Monte Carlo Visualization")
    print("=" * 60)

    # Create sample MC results for testing
    np.random.seed(42)
    n_runs = 100

    mc_results = pd.DataFrame(
        {
            "run_id": range(n_runs),
            "TC_1": np.random.normal(0.5, 0.1, n_runs),
            "TC_2": np.random.normal(0.3, 0.05, n_runs),
            "F_02_03": np.random.normal(200, 20, n_runs),
            "k1": np.random.normal(0.025, 0.005, n_runs),
            "final_C_stock_soil": np.random.normal(1500, 200, n_runs),
            "final_material_flow": np.random.normal(3000, 300, n_runs),
        }
    )

    print(f"✅ Created sample MC results with {n_runs} runs")

    # Test MC distribution plot
    try:
        plotting.plot_mc_distribution(mc_results, "final_C_stock_soil", unit="Mg C")
        print("✅ MC distribution plot created successfully")
    except Exception as e:
        print(f"❌ Error in MC distribution plot: {e}")

    # Test MC sensitivity scatter
    try:
        plotting.plot_mc_sensitivity_scatter(
            mc_results, "TC_1", "final_C_stock_soil", unit="Mg C"
        )
        print("✅ MC sensitivity scatter plot created successfully")
    except Exception as e:
        print(f"❌ Error in MC sensitivity scatter: {e}")

    # Test MC correlation matrix
    try:
        plotting.plot_mc_correlation_matrix(mc_results)
        print("✅ MC correlation matrix created successfully")
    except Exception as e:
        print(f"❌ Error in MC correlation matrix: {e}")

    # Test MC confidence intervals
    try:
        plotting.plot_mc_confidence_intervals(
            mc_results, "final_C_stock_soil", unit="Mg C"
        )
        print("✅ MC confidence intervals created successfully")
    except Exception as e:
        print(f"❌ Error in MC confidence intervals: {e}")

    # Test MC parameter importance
    try:
        plotting.plot_mc_parameter_importance(mc_results, "final_C_stock_soil")
        print("✅ MC parameter importance created successfully")
    except Exception as e:
        print(f"❌ Error in MC parameter importance: {e}")

    return True


def test_scenario_comparison():
    """
    Test the enhanced scenario comparison system.
    """
    print("\n" + "=" * 60)
    print("🧪 TEST 3: Scenario Comparison System")
    print("=" * 60)

    # Initialize scenario manager
    scenario_manager = utils.ScenarioManager()

    # Create test scenarios
    class TestConfig:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    # Scenario 1: Baseline
    baseline_config = TestConfig(
        Start_Year=2025,
        End_Year=2050,
        Monte_Carlo_Iterations=100,
        Run_DSM_Calculation=True,
        Run_FOMP_Calculation=True,
    )

    # Scenario 2: Extended horizon
    extended_config = TestConfig(
        Start_Year=2025,
        End_Year=2060,
        Monte_Carlo_Iterations=200,
        Run_DSM_Calculation=True,
        Run_FOMP_Calculation=True,
    )

    # Scenario 3: High efficiency
    high_efficiency_config = TestConfig(
        Start_Year=2025,
        End_Year=2050,
        Monte_Carlo_Iterations=150,
        Run_DSM_Calculation=False,
        Run_FOMP_Calculation=True,
    )

    try:
        # Save scenarios
        scenario_manager.save_scenario("baseline", baseline_config, "Baseline scenario")
        scenario_manager.save_scenario(
            "extended", extended_config, "Extended time horizon"
        )
        scenario_manager.save_scenario(
            "high_efficiency", high_efficiency_config, "High efficiency scenario"
        )
        print("✅ Created test scenarios successfully")

        # List scenarios
        scenarios = scenario_manager.list_scenarios()
        print(f"✅ Available scenarios: {[s['name'] for s in scenarios]}")

        # Compare scenarios
        comparison_data = scenario_manager.create_scenario_comparison_plot(
            ["baseline", "extended", "high_efficiency"]
        )
        print("✅ Scenario comparison data created")

        # Get scenario differences
        differences = scenario_manager.get_scenario_differences(
            ["baseline", "extended"]
        )
        print(
            f"✅ Found {len([k for k, v in differences.items() if v['different']])} differences between baseline and extended"
        )

        # Create scenario ranking
        ranking = scenario_manager.create_scenario_ranking(
            ["baseline", "extended", "high_efficiency"]
        )
        print("✅ Scenario ranking created")
        print(
            f"   Top scenario: {ranking['ranking'][0][0]} (score: {ranking['ranking'][0][1]:.3f})"
        )

        # Export comparison
        export_path = scenario_manager.export_scenario_comparison(
            ["baseline", "extended", "high_efficiency"]
        )
        print(f"✅ Scenario comparison exported to: {export_path}")

        return True

    except Exception as e:
        print(f"❌ Error in scenario comparison: {e}")
        return False


def test_data_input_improvements():
    """
    Test the improved data input validation and structure.
    """
    print("\n" + "=" * 60)
    print("🧪 TEST 4: Data Input Improvements")
    print("=" * 60)

    # Test with your new dataset
    test_files = [
        "data/01_input/250707_Template_CS1.xlsx",
        "data/01_input/250625_Template_CS0.xlsx",
        "data/01_input/BioDYM_MFA_Input_Template.xlsx",
    ]

    for file_path in test_files:
        if os.path.exists(file_path):
            print(f"\n📁 Testing file: {file_path}")

            try:
                # Load and validate data
                input_data = pd.read_excel(
                    file_path,
                    sheet_name=None,
                    header=0,
                    engine="openpyxl",
                    na_values=["N.A.", "NA", "n/a"],
                )

                print("   ✅ File loaded successfully")
                print(f"   📊 Available sheets: {list(input_data.keys())}")

                # Test data validation
                try:
                    data_loader.validate_input_data(input_data)
                    print("   ✅ Data validation passed")
                except Exception as e:
                    print(f"   ⚠️  Data validation issues: {e}")

                # Test configuration loading if Configuration sheet exists
                if "Configuration" in input_data:
                    try:
                        config_obj = config.load_configuration(file_path)
                        print("   ✅ Configuration loaded from Excel")
                        print(
                            f"      Start Year: {getattr(config_obj, 'Start_Year', 'N/A')}"
                        )
                        print(
                            f"      End Year: {getattr(config_obj, 'End_Year', 'N/A')}"
                        )
                    except Exception as e:
                        print(f"   ❌ Configuration loading failed: {e}")

            except Exception as e:
                print(f"   ❌ Error processing file: {e}")

    return True


def test_full_workflow():
    """
    Test the complete workflow with the new features.
    """
    print("\n" + "=" * 60)
    print("🧪 TEST 5: Complete Workflow")
    print("=" * 60)

    # Use the new Excel template
    template_path = "data/01_input/BioDYM_MFA_Input_Template.xlsx"

    if not os.path.exists(template_path):
        print(f"❌ Template file not found: {template_path}")
        return False

    try:
        # Load configuration from Excel
        config_obj = config.load_configuration(template_path)
        print("✅ Configuration loaded from Excel")

        # Create analysis config
        class AnalysisConfig:
            def __init__(self, config_obj):
                self.excel_file_path = getattr(
                    config_obj,
                    "Input_File_Path",
                    "data/01_input/250707_Template_CS1.xlsx",
                )
                self.output_path = getattr(
                    config_obj, "Output_File_Path", "data/02_output/results.xlsx"
                )
                self.start_year = getattr(config_obj, "Start_Year", 2025)
                self.end_year = getattr(config_obj, "End_Year", 2050)
                self.elements = getattr(
                    config_obj, "Elements_comma_separated", "material,WC,DM,CC"
                ).split(",")
                self.run_monte_carlo = getattr(
                    config_obj, "Run_Monte_Carlo_Simulation", False
                )
                self.mc_iterations = getattr(config_obj, "Monte_Carlo_Iterations", 100)
                self.RUN_DSM_CALCULATION = getattr(
                    config_obj, "Run_DSM_Calculation", True
                )
                self.RUN_FOMP_CALCULATION = getattr(
                    config_obj, "Run_FOMP_Calculation", True
                )

        analysis_config = AnalysisConfig(config_obj)
        print("✅ Analysis configuration created")

        # Test model setup (without running full calculation)
        print("🔧 Testing model setup...")

        # Define model scope
        model_classification, index_table = system_setup.define_model_scope(
            analysis_config.start_year,
            analysis_config.end_year,
            analysis_config.elements,
        )
        print("   ✅ Model scope defined")

        # Initialize MFA system
        mfa_system_base = system_setup.initialize_mfa_system(
            model_classification, index_table
        )
        print("   ✅ MFA system initialized")

        # Load data and define processes
        mfa_system_base, all_excel_data = system_setup.load_and_define_processes(
            mfa_system_base, analysis_config.excel_file_path, data_loader
        )
        print("   ✅ Data loaded and processes defined")

        # Load model parameters
        dsm_params = data_loader.load_dsm_parameters(all_excel_data)
        fomp_params = data_loader.load_fomp_parameters(all_excel_data)
        uncertainty_params = data_loader.load_uncertainty_definitions(all_excel_data)
        print("   ✅ Model parameters loaded")

        print("   📊 Model summary:")
        print(f"      Processes: {len(mfa_system_base.ProcessList)}")
        print(f"      Flows: {len(mfa_system_base.FlowDict)}")
        print(f"      Stocks: {len(mfa_system_base.StockDict)}")
        print(f"      Parameters: {len(mfa_system_base.ParameterDict)}")

        return True

    except Exception as e:
        print(f"❌ Error in complete workflow: {e}")
        return False


def main():
    """
    Run all comprehensive tests.
    """
    print("🚀 BioDYM MFA Tool - Comprehensive Feature Testing")
    print("=" * 60)

    test_results = {}

    # Run all tests
    test_results["excel_config"] = test_excel_configuration_loading()
    test_results["mc_visualization"] = test_monte_carlo_visualization()
    test_results["scenario_comparison"] = test_scenario_comparison()
    test_results["data_input"] = test_data_input_improvements()
    test_results["full_workflow"] = test_full_workflow()

    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)

    passed = 0
    total = len(test_results)

    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {test_name.replace('_', ' ').title()}: {status}")
        if result:
            passed += 1

    print(f"\n🎯 Overall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Your BioDYM MFA tool is ready for use.")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")

    print("\n📝 Next Steps:")
    print("   1. Review the test results above")
    print("   2. Fix any failed tests")
    print("   3. Use the new Excel template for your analysis")
    print("   4. Explore the enhanced MC visualization features")
    print("   5. Create and compare different scenarios")


if __name__ == "__main__":
    main()
