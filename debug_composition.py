import sys
import warnings
warnings.filterwarnings('ignore')

# Add paths
sys.path.insert(0, "02_src")
sys.path.insert(0, "06_framework/ODYM-master_20241127/odym/modules")

import config
import system_setup

# Load configuration
print("Loading configuration...")
cfg = config.load_configuration("01_data/01_input/251120_BioDYM_ODYM_Wood.xlsm")

# Setup system
print("\nSetting up MFA system...")
mfa_system, all_excel_data, flow_tc_map, process_logic_map = system_setup.create_mfa_system(
    cfg, debug_mode=True
)

# Check specific flows
print("\n" + "="*80)
print("CHECKING FLOW COMPOSITIONS")
print("="*80)

for flow_id in ['F_00_02', 'F_01_02']:
    if flow_id in mfa_system.FlowDict:
        flow = mfa_system.FlowDict[flow_id]
        print(f"\n{flow_id}: {mfa_system._flow_descriptions.get(flow_id, flow_id)}")
        print(f"  Elements: {mfa_system.Elements}")
        print(f"  First year values: {flow.Values[0, :]}")

        # Calculate percentages
        material = flow.Values[0, 0]
        if material > 0:
            for idx, elem in enumerate(mfa_system.Elements):
                value = flow.Values[0, idx]
                pct = (value / material * 100) if idx > 0 else 100
                print(f"    {elem}: {value:.2f} Mg ({pct:.2f}% of material)")

        # Check parameters
        print(f"  Parameters:")
        for elem in mfa_system.Elements[1:]:
            param_name = f"{elem}_{flow_id}"
            if param_name in mfa_system.ParameterDict:
                param = mfa_system.ParameterDict[param_name]
                print(f"    {elem}: fraction = {param.Values}")
            else:
                print(f"    {elem}: NO PARAMETER FOUND")

print("\n" + "="*80)
