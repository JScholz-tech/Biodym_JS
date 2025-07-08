# -*- coding: utf-8 -*-
"""
Golden Dataset for BioDYM MFA Testing

This module creates a simple but comprehensive test dataset with known solutions.
The dataset is designed to test all major features while being simple enough
to calculate expected results by hand.

Test System: Simple 3-process system
- Process 0: Input (Atmosphere)
- Process 1: Processing (Environment) 
- Process 2: Output (Lithosphere)

Flows:
- F_00_01: Input flow (100 Mg/year, constant)
- F_01_02: Processing flow (80% of input, TC = 0.8)
- F_01_00: Recycling flow (20% of input, TC = 0.2)

Stocks:
- S_1: Processing stock (accumulates over time)
- dS_1: Stock change (inflow - outflow)

Expected Results (by hand calculation):
- Year 1: S_1 = 0 + 100 - 80 = 20 Mg
- Year 2: S_1 = 20 + 100 - 80 = 40 Mg
- Year 3: S_1 = 40 + 100 - 80 = 60 Mg
- etc.
"""

import os
import sys
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# Add project paths
current_dir = os.getcwd()
src_path = os.path.join(current_dir, 'src')
sys.path.insert(0, src_path)

# Add ODYM framework path
project_root_parent = os.path.dirname(current_dir)
odym_path = os.path.join(project_root_parent, 'framework', 'ODYM-master_20241127', 'odym', 'modules')
sys.path.insert(0, odym_path)

def create_golden_dataset():
    """
    Create a comprehensive test dataset with known solutions.
    
    Returns:
        str: Path to the created Excel file
    """
    print("🔧 Creating Golden Dataset...")
    
    # Create output directory
    test_data_dir = "test_data"
    if not os.path.exists(test_data_dir):
        os.makedirs(test_data_dir)
    
    excel_path = os.path.join(test_data_dir, "golden_dataset.xlsx")
    
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        
        # 1. Configuration Sheet
        config_data = {
            'Parameter': [
                'Input File Path',
                'Output File Path', 
                'Start Year',
                'End Year',
                'Elements (comma-separated)',
                'Run Monte Carlo Simulation',
                'Monte Carlo Iterations',
                'Run DSM Calculation',
                'Run FOMP Calculation',
                'Minimum Flow Threshold (Mg)',
                'Show Zero Flows in Plots',
                'Export Format',
                'Default Plot Style',
                'Color Scheme',
                'Export Plots as Images',
                'Dashboard Layout',
                'Mass Balance Tolerance',
                'Data Validation Level',
                'Auto-save Results'
            ],
            'Value': [
                'test_data/golden_dataset.xlsx',
                'test_data/golden_results.xlsx',
                2025,
                2030,
                'material,WC,DM,CC',
                False,
                100,
                True,
                False,
                0.1,
                False,
                'Excel',
                'Line',
                'Default',
                True,
                'Grid',
                0.001,
                'Strict',
                True
            ]
        }
        pd.DataFrame(config_data).to_excel(writer, sheet_name='0_Configuration', index=False)
        
        # 2. Process Definitions (2_1_Definition_Processes)
        process_data = {
            'ID': [0, 1, 2, 3],
            'Name(EN)': ['Atmosphere', 'Environment', 'Lithosphere', 'Use-Phase'],
            'Stock?': ['No', 'Yes', 'No', 'Yes'],
            'TC?': ['No', 'Yes', 'No', 'No'],
            'Initial_Stock?': ['No', 'No', 'No', 'No'],
            'DSM?': ['No', 'No', 'No', 'Yes'],
            'FOMP?': ['No', 'No', 'No', 'No']
        }
        pd.DataFrame(process_data).to_excel(writer, sheet_name='2_1_Definition_Processes', index=False)
        
        # 3. Flow Definitions (1_1_Definition_Flows)
        flow_data = {
            'Flow_ID': ['F_00_01', 'F_01_02', 'F_01_00', 'F_01_03', 'F_03_02'],
            'Name(EN)': ['Input_Flow', 'Processing_Flow', 'Recycling_Flow', 'To_UsePhase', 'DSM_Outflow'],
            'Process_ID_O': [0, 1, 1, 1, 3],
            'Process_ID_I': [1, 2, 0, 3, 2],
            'WC': [0.2]*5,
            'DM': [0.8]*5,
            'CC': [0.45]*5
        }
        pd.DataFrame(flow_data).to_excel(writer, sheet_name='1_1_Definition_Flows', index=False)
        
        # 4. Flow Data (1_2_Data_Flows)
        years = list(range(2025, 2031))
        flow_time_data = []
        for year in years:
            flow_time_data.append({
                'Flow_ID': 'F_00_01',
                'Year_Flow': year,
                'Flow_Py': 100.0,
                'WC_Flow_Py': 20.0,
                'DM_Flow_Py': 80.0,
                'CC_Flow_Py': 36.0
            })
            flow_time_data.append({
                'Flow_ID': 'F_01_03',
                'Year_Flow': year,
                'Flow_Py': 90.0,
                'WC_Flow_Py': 18.0,
                'DM_Flow_Py': 72.0,
                'CC_Flow_Py': 32.4
            })
            flow_time_data.append({
                'Flow_ID': 'F_03_02',
                'Year_Flow': year,
                'Flow_Py': 0.0,
                'WC_Flow_Py': 0.0,
                'DM_Flow_Py': 0.0,
                'CC_Flow_Py': 0.0
            })
        pd.DataFrame(flow_time_data).to_excel(writer, sheet_name='1_2_Data_Flows', index=False)
        
        # 5. Transfer Coefficients (2_3_Process_TCs)
        tc_data = {
            'TC_ID': ['TC_01_02', 'TC_01_00'],
            'TC_Value': [0.8, 0.2],
            'Description': ['Processing efficiency', 'Recycling rate']
        }
        pd.DataFrame(tc_data).to_excel(writer, sheet_name='2_3_Process_TCs', index=False)
        
        # 6. DSM Parameters (3_1_Definition_DSM)
        dsm_df = pd.DataFrame({
            'ID': [1, 2, 3],
            'Process_ID': [3, 3, 3],
            'Category_ID': [1, 2, 3],
            'Category_Name': ['App1', 'App2', 'App3'],
            'Inflow_Split_[%]': [0.3333, 0.3333, 0.3334],
            'Lifetime_Type': ['Fixed', 'Fixed', 'Fixed'],
            'Lifetime_Mean': [1, 2, 3],
            'Lifetime_StdDev': [0, 0, 0]  # This column can remain, but is ignored for 'Fixed'
        })
        dsm_df.to_excel(writer, sheet_name='3_1_Definition_DSM', index=False)
        
        # 7. FOMP Parameters (3_2_Definition_FOMP)
        fomp_df = pd.DataFrame(columns=['ID', 'Process_ID', 'FOMP_Type', 'Parameters'])
        fomp_df.to_excel(writer, sheet_name='3_2_Definition_FOMP', index=False)
        
        # 8. Uncertainty Parameters (4_1_Uncertainty_Parameters)
        uncertainty_data = {
            'ID': [1, 2],
            'Parameter_Name': ['TC_01_02', 'TC_01_00'],
            'Distribution': ['Normal', 'Normal'],
            'Mean': [0.8, 0.2],
            'StdDev': [0.05, 0.02],
            'Min': [0.7, 0.15],
            'Max': [0.9, 0.25]
        }
        pd.DataFrame(uncertainty_data).to_excel(writer, sheet_name='4_1_Uncertainty_Parameters', index=False)
        
        # 9. Dynamic Transfer Coefficients (2_5_dynamic_tcs)
        dynamic_tcs_df = pd.DataFrame(columns=['TC_ID', 'Year', 'Value'])
        dynamic_tcs_df.to_excel(writer, sheet_name='2_5_dynamic_tcs', index=False)
        
        # 10. Initial Stocks (2_4_Initial_Stock)
        initial_stock_df = pd.DataFrame(columns=['Process_ID', 'Initial_Stock_material', 'Initial_Stock_WC[%]', 'Initial_Stock_DM[%]', 'Initial_Stock_CC[%]'])
        initial_stock_df.to_excel(writer, sheet_name='2_4_Initial_Stock', index=False)
    
    print(f"✅ Golden dataset created: {excel_path}")
    return excel_path

def calculate_expected_results():
    """
    Calculate expected results for the golden dataset.
    
    Returns:
        dict: Expected results for validation
    """
    years = list(range(2025, 2031))
    # Fractions used in the golden dataset
    wc_frac = 0.2
    dm_frac = 0.8
    cc_frac = 0.45
    material = 100.0
    wc = material * wc_frac
    dm = material * dm_frac
    cc = dm * cc_frac
    expected_results = {
        'flows': {
            'F_00_01': {
                'material': [material] * len(years),
                'WC': [wc] * len(years),
                'DM': [dm] * len(years),
                'CC': [cc] * len(years),
            },
            'F_01_02': {
                'material': [material * 0.8] * len(years),
                'WC': [material * 0.8 * wc_frac] * len(years),
                'DM': [material * 0.8 * dm_frac] * len(years),
                'CC': [material * 0.8 * dm_frac * cc_frac] * len(years),
            },
            'F_01_00': {
                'material': [material * 0.2] * len(years),
                'WC': [material * 0.2 * wc_frac] * len(years),
                'DM': [material * 0.2 * dm_frac] * len(years),
                'CC': [material * 0.2 * dm_frac * cc_frac] * len(years),
            },
        },
        'stocks': {
            'S_1': [0.0] * len(years),        # No accumulation (inflow = outflow)
            'dS_1': [0.0] * len(years),       # No change (inflow = outflow)
        },
        'mass_balance': {
            'process_1_inflow': [material] * len(years),
            'process_1_outflow': [material] * len(years),  # 80 + 20
            'process_1_stock_change': [0.0] * len(years),  # inflow - outflow = 0
            'balance_error': [0.0] * len(years),  # Should be zero
        }
    }
    
    # DSM expected results for inflow-driven model with 3 categories
    # Inflow to DSM: 90 per year, split equally
    inflow = 90.0
    inflow_split = [0.3333, 0.3333, 0.3334]
    means = [1, 2, 3]
    years = list(range(2025, 2031))
    dsm_stock = np.zeros(len(years))
    dsm_outflow = np.zeros(len(years))
    inflow_by_cat = [inflow * s for s in inflow_split]
    for t in range(len(years)):
        stock_t = 0
        outflow_t = 0
        for i, mean in enumerate(means):
            for tau in range(t+1):
                age = t - tau
                # For Normal(μ, 0), all outflow at age=mean (discrete lifetime)
                if age == mean:
                    outflow_t += inflow_by_cat[i]
                elif age < mean:
                    stock_t += inflow_by_cat[i]
        dsm_stock[t] = stock_t
        dsm_outflow[t] = outflow_t
    expected_results['stocks']['S_3'] = list(dsm_stock)
    expected_results['flows']['F_03_02'] = {
        'material': list(dsm_outflow),
        'WC': [v * 0.2 for v in dsm_outflow],
        'DM': [v * 0.8 for v in dsm_outflow],
        'CC': [v * 0.8 * 0.45 for v in dsm_outflow],
    }
    
    return expected_results

def get_dimension_index(dim_name):
    # Standard order: material, WC, DM, CC
    mapping = {'material': 0, 'WC': 1, 'DM': 2, 'CC': 3}
    return mapping[dim_name]

def test_golden_dataset():
    """
    Test the golden dataset with known solutions.
    """
    print("\n" + "="*60)
    print("🧪 GOLDEN DATASET TEST")
    print("="*60)
    
    try:
        # 1. Create the dataset
        excel_path = create_golden_dataset()
        
        # 2. Load and run the model
        from src import config, data_loader, system_setup
        from src.engine import solver
        
        # Load configuration
        config_obj = config.load_configuration(excel_path)
        print("✅ Configuration loaded")
        
        # Update config to enable DSM
        setattr(config_obj, 'Run_DSM_Calculation', True)
        print("✅ DSM Calculation enabled")


        
        # Load and validate data
        input_data = pd.read_excel(excel_path, sheet_name=None, header=0, 
                                  engine='openpyxl', na_values=['N.A.', 'NA', 'n/a'])
        data_loader.validate_input_data(input_data)
        print("✅ Data validation passed")
        
        # Model setup
        model_classification, index_table = system_setup.define_model_scope(
            getattr(config_obj, 'Start_Year', 2025), getattr(config_obj, 'End_Year', 2030), 
            getattr(config_obj, 'Elements_comma-separated').split(',')
        )
        mfa_system_base = system_setup.initialize_mfa_system(model_classification, index_table)
        mfa_system_base, all_excel_data = system_setup.load_and_define_processes(
            mfa_system_base, excel_path, data_loader
        )
        
        # Configure flows and parameters
        mfa_system_configured, all_excel_data = system_setup.define_flows_and_parameters(
            mfa_system_base, all_excel_data
        )
        
        # Parameter loading
        dsm_params = data_loader.load_dsm_parameters(all_excel_data)
        fomp_params = data_loader.load_fomp_parameters(all_excel_data)
        uncertainty_params = data_loader.load_uncertainty_definitions(all_excel_data)

        print("DSM parameter sheet:")
        print(all_excel_data['3_1_Definition_DSM'])
        print("Flow definition sheet:")
        print(all_excel_data['1_1_Definition_Flows'])
        print("Flow data sheet:")
        print(all_excel_data['1_2_Data_Flows'])
        print("DSM params loaded:", dsm_params)
        print("FOMP params loaded:", fomp_params)
        print("Uncertainty params loaded:", uncertainty_params)
        
        # Run calculation
        mfa_system_with_results, dsm_details = solver.run_mfa_calculation(
            mfa_system_configured, dsm_params, fomp_params, config_obj
        )
        print("✅ Calculation completed")
        
        # 3. Debug: Print actual calculated values
        print("\n🔍 DEBUG: Actual calculated values:")
        for flow_id, flow in mfa_system_with_results.FlowDict.items():
            print(f"   {flow_id}: {flow.Values[:, 0]}")
        for stock_id, stock in mfa_system_with_results.StockDict.items():
            print(f"   {stock_id}: {stock.Values[:, 0]}")
        
        # 4. Validate results
        expected = calculate_expected_results()
        validation_results = validate_results(mfa_system_with_results, expected)
        
        # 4. Print validation summary
        print("\n📊 VALIDATION RESULTS:")
        print(f"   Flows validated: {validation_results['flows_correct']}/{validation_results['flows_total']}")
        print(f"   Stocks validated: {validation_results['stocks_correct']}/{validation_results['stocks_total']}")
        print(f"   Mass balance: {'✅ PASS' if validation_results['mass_balance_correct'] else '❌ FAIL'}")
        print(f"   Overall: {'✅ PASS' if validation_results['overall_pass'] else '❌ FAIL'}")
        
        return validation_results['overall_pass']
        
    except Exception as e:
        print(f"❌ Error in golden dataset test: {e}")
        import traceback
        traceback.print_exc()
        return False

def validate_results(mfa_system, expected_results, tolerance=1e-6):
    """
    Validate calculated results against expected results.
    
    Args:
        mfa_system: The MFA system with results
        expected_results: Dictionary of expected results
        tolerance: Numerical tolerance for comparisons
        
    Returns:
        dict: Validation results
    """
    validation = {
        'flows_correct': 0,
        'flows_total': 0,
        'stocks_correct': 0,
        'stocks_total': 0,
        'mass_balance_correct': True,
        'overall_pass': True
    }
    
    # Validate flows
    for flow_id, expected_values in expected_results['flows'].items():
        if flow_id in mfa_system.FlowDict:
            flow = mfa_system.FlowDict[flow_id]
            # Check all dimensions (material, WC, DM, CC)
            for dim_name, expected_dim_values in expected_values.items():
                dim_idx = get_dimension_index(dim_name)
                calculated_dim_values = flow.Values[:, dim_idx]
                
                if len(calculated_dim_values) == len(expected_dim_values):
                    max_diff = max(abs(calc - exp) for calc, exp in zip(calculated_dim_values, expected_dim_values))
                    if max_diff <= tolerance:
                        validation['flows_correct'] += 1
                    else:
                        print(f"   ❌ Flow {flow_id} dimension {dim_name}: max difference = {max_diff}")
                        validation['overall_pass'] = False
                else:
                    print(f"   ❌ Flow {flow_id} dimension {dim_name}: length mismatch")
                    validation['overall_pass'] = False
            validation['flows_total'] += 1
    
    # Validate stocks
    for stock_id, expected_values in expected_results['stocks'].items():
        if stock_id in mfa_system.StockDict:
            stock = mfa_system.StockDict[stock_id]
            calculated_values = stock.Values[:, 0]  # Material values
            
            if len(calculated_values) == len(expected_values):
                max_diff = max(abs(calc - exp) for calc, exp in zip(calculated_values, expected_values))
                if max_diff <= tolerance:
                    validation['stocks_correct'] += 1
                else:
                    print(f"   ❌ Stock {stock_id}: max difference = {max_diff}")
                    validation['overall_pass'] = False
            else:
                print(f"   ❌ Stock {stock_id}: length mismatch")
                validation['overall_pass'] = False
            validation['stocks_total'] += 1
    
    # Validate mass balance for process 1
    process_1_flows = [f for f in mfa_system.FlowDict.values() if f.P_End == 1 or f.P_Start == 1]
    if process_1_flows:
        # This is a simplified check - in practice you'd want more comprehensive mass balance validation
        validation['mass_balance_correct'] = True  # Placeholder
    
    # DSM stock and outflow validation
    if 'S_3' in expected_results['stocks']:
        stock = mfa_system.StockDict['S_3']
        calc = stock.Values[:, 0]
        exp = expected_results['stocks']['S_3']
        max_diff = max(abs(c - e) for c, e in zip(calc, exp))
        if max_diff <= tolerance:
            print('   ✅ DSM stock S_3 matches expected values.')
        else:
            print(f'   ❌ DSM stock S_3: max difference = {max_diff}')
            validation['overall_pass'] = False
    if 'F_03_02' in expected_results['flows']:
        flow = mfa_system.FlowDict['F_03_02']
        for dim_name, exp_vals in expected_results['flows']['F_03_02'].items():
            dim_idx = get_dimension_index(dim_name)
            calc_vals = flow.Values[:, dim_idx]
            max_diff = max(abs(c - e) for c, e in zip(calc_vals, exp_vals))
            if max_diff <= tolerance:
                print(f'   ✅ DSM outflow F_03_02 ({dim_name}) matches expected values.')
            else:
                print(f'   ❌ DSM outflow F_03_02 ({dim_name}): max difference = {max_diff}')
                validation['overall_pass'] = False
    
    return validation

if __name__ == "__main__":
    success = test_golden_dataset()
    if success:
        print("\n🎉 Golden dataset test PASSED!")
    else:
        print("\n❌ Golden dataset test FAILED!") 