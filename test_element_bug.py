import sys
import warnings
import pandas as pd
import numpy as np
warnings.filterwarnings('ignore')

sys.path.insert(0, "02_src")
sys.path.insert(0, "06_framework/ODYM-master_20241127/odym/modules")

# Read config directly
config_df = pd.read_excel('01_data/01_input/251120_BioDYM_ODYM_Wood.xlsm', sheet_name='0_Configuration')
print("=== Element Configuration ===")
elem_rows = config_df[(config_df.iloc[:, 1].astype(str).str.contains('Element_ID', na=False))]
for _, row in elem_rows.iterrows():
    print(f"{row.iloc[1]}: {row.iloc[2]}")

# Read flow definitions
flows_def = pd.read_excel('01_data/01_input/251120_BioDYM_ODYM_Wood.xlsm', sheet_name='1_1_Definition_Flows')
print("\n=== Flow F_01_02 Fractions (from 1_1_Definition_Flows) ===")
f01_def = flows_def[flows_def['Flow_ID'] == 'F_01_02'].iloc[0]
print(f"Flow_E2_Fraction[%]: {f01_def['Flow_E2_Fraction[%]']}")
print(f"Flow_E3_Fraction[%]: {f01_def['Flow_E3_Fraction[%]']}")
print(f"Flow_E4_Fraction[%]: {f01_def['Flow_E4_Fraction[%]']}")

# Read flow data
flows_data = pd.read_excel('01_data/01_input/251120_BioDYM_ODYM_Wood.xlsm', sheet_name='1_2_Data_Flows')
print("\n=== Flow F_01_02 Data (Year 1950) ===")
f01_data = flows_data[flows_data['Flow_ID'] == 'F_01_02'].iloc[0]
print(f"Material (E1_value): {f01_data['E1_value']}")
print(f"E2_Fraction[%]: {f01_data['E2_Fraction[%]']}")
print(f"E3_Fraction[%]: {f01_data['E3_Fraction[%]']}")
print(f"E4_Fraction[%]: {f01_data['E4_Fraction[%]']}")

# Now manually calculate what the values SHOULD be
material = f01_data['E1_value']
wc_fraction = f01_data['E2_Fraction[%]']
dm_fraction = f01_data['E3_Fraction[%]']
cc_fraction = f01_data['E4_Fraction[%]']

wc_value = material * wc_fraction
dm_value = material * dm_fraction
cc_value = dm_value * cc_fraction

print("\n=== EXPECTED Calculated Values ===")
print(f"WC (60% of material): {wc_value:.2f} Mg")
print(f"DM (40% of material): {dm_value:.2f} Mg")
print(f"CC (0% of DM): {cc_value:.2f} Mg")
print(f"Total (WC + DM): {wc_value + dm_value:.2f} Mg")

# Check composition export
comp_export = pd.read_excel('01_data/02_output/composition_export/flow_composition.xlsx')
f01_comp = comp_export[(comp_export['Flow Name'] == 'F_01_02') & (comp_export['Year'] == 1950)].iloc[0]

print("\n=== ACTUAL Values (from composition export) ===")
print(f"WC: {f01_comp['Water Content (Mass)']:.2f} Mg")
print(f"DM: {f01_comp['Dry Matter (Mass)']:.2f} Mg")
print(f"CC: {f01_comp['Carbon Content (Mass)']:.2f} Mg")
print(f"Total: {f01_comp['Total Mass']:.2f} Mg")

print("\n=== COMPARISON ===")
print(f"Material mismatch: {material:.2f} vs {f01_comp['Total Mass']:.2f} (ratio: {f01_comp['Total Mass']/material:.4f})")
print(f"WC mismatch: {wc_value:.2f} vs {f01_comp['Water Content (Mass)']:.2f}")
print(f"DM mismatch: {dm_value:.2f} vs {f01_comp['Dry Matter (Mass)']:.2f}")
