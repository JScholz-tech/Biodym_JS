import os
import sys
import pandas as pd

# Add ODYM framework path
current_dir = os.getcwd()
project_root_parent = os.path.dirname(current_dir)
odym_path = os.path.join(
    project_root_parent, "framework", "ODYM-master_20241127", "odym", "modules"
)
sys.path.insert(0, odym_path)

# Now import the modules
from src import config, data_loader, system_setup
from src.engine import solver

# 1. Load configuration
config_obj = config.load_configuration("data/01_input/250707_Template_CS1.xlsx")
print("✅ Config loaded:", vars(config_obj))

# 2. Load and validate data
input_data = pd.read_excel(
    "data/01_input/250707_Template_CS1.xlsx",
    sheet_name=None,
    header=0,
    engine="openpyxl",
    na_values=["N.A.", "NA", "n/a"],
)
data_loader.validate_input_data(input_data)
print("✅ Data validation passed!")

# 3. Model setup
model_classification, index_table = system_setup.define_model_scope(
    config_obj.Start_Year,
    config_obj.End_Year,
    getattr(config_obj, "Elements_comma-separated").split(","),
)
mfa_system_base = system_setup.initialize_mfa_system(model_classification, index_table)
mfa_system_base, all_excel_data = system_setup.load_and_define_processes(
    mfa_system_base, "data/01_input/250707_Template_CS1.xlsx", data_loader
)

# 4. Configure flows and parameters (MISSING STEP!)
mfa_system_configured, all_excel_data = system_setup.define_flows_and_parameters(
    mfa_system_base, all_excel_data
)

# 5. Parameter loading
dsm_params = data_loader.load_dsm_parameters(all_excel_data)
fomp_params = data_loader.load_fomp_parameters(all_excel_data)
uncertainty_params = data_loader.load_uncertainty_definitions(all_excel_data)

# 6. Run calculation (deterministic)
mfa_system_with_results, dsm_details = solver.run_mfa_calculation(
    mfa_system_configured, dsm_params, fomp_params, config_obj
)
print("✅ Calculation complete!")

# 7. (Optional) Save results
from src import utils

utils.export_results_to_excel(mfa_system_with_results, config_obj.Output_File_Path)
print("✅ Results exported!")

# Debug information
print("Loaded sheets:", list(all_excel_data.keys()))
print("Sample of 1_1_Definition_Flows:", all_excel_data["1_1_Definition_Flows"].head())
print("Sample of 1_2_Data_Flows:", all_excel_data["1_2_Data_Flows"].head())

print("Flows defined:", len(mfa_system_with_results.FlowDict))
print("Stocks defined:", len(mfa_system_with_results.StockDict))

try:
    # Check flow values
    for flow_id, flow in mfa_system_with_results.FlowDict.items():
        print(f"{flow_id}: {flow.Values[:3, :]}")  # Show first 3 years
        break  # Just one for brevity

    # Check stock values
    for stock_id, stock in mfa_system_with_results.StockDict.items():
        print(f"{stock_id}: {stock.Values[:3, :]}")  # Show first 3 years
        break
except Exception as e:
    print("Error checking flows/stocks:", e)
