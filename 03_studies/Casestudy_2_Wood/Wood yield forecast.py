import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- 1. SIMPLE PARAMETERS ---
AREA_HA = 100000        # Study Area
WC_FRESH = 0.40         # Fresh Water Content
DENSITY_AVG = 550       # Average Density (kg/m³) - Simplified from 470/680 mix

# --- 2. TOTAL YIELD CURVE (m³/ha) ---
# Source: History (Destatis), Current (BWI), Future (WEHAM)
# Simple linear interpolation between key dates
years = np.arange(1950, 2126)
yield_anchors = {
    1950: 4.8, 
    1990: 5.3, 
    2010: 7.0, 
    2022: 6.7, 
    2125: 7.5   # Future Target
}
df = pd.DataFrame(index=years)
df['Yield_m3_ha'] = pd.Series(yield_anchors).reindex(years).interpolate(method='linear')

# --- 3. SPECIES SPLIT (%) ---
# Source: Destatis (History) -> WEHAM (Future Waldumbau)
# Simple curve: Softwood share drops over time
share_anchors = {
    1950: 0.75, 
    2018: 0.78, # Calamity Peak
    2025: 0.55, # Post-Calamity
    2125: 0.45  # Mixed Forest Target
}
df['Softwood_Share'] = pd.Series(share_anchors).reindex(years).interpolate(method='linear')

# --- 4. MASS CALCULATION ---
# Calculate Total Volume (m³)
df['Total_Vol_m3'] = df['Yield_m3_ha'] * AREA_HA

# Calculate Fresh Mass (Mg)
# Mass = Volume * Density / 1000 (to Mg) / (1-WC)
df['Total_FM_Mg'] = (df['Total_Vol_m3'] * DENSITY_AVG / 1000) / (1 - WC_FRESH)

# --- 5. EXPORT FOR BIODYM ---
# This 'Total_FM_Mg' is the single flow that goes into P2 Forestry.
# The split (Softwood/Hardwood) will be handled inside bioDYM using Dynamic TCs.

# Visualization
plt.style.use('seaborn-v0_8-whitegrid')
fig, ax1 = plt.subplots(figsize=(10, 6))
ax1.plot(df.index, df['Total_FM_Mg']/1000, color='green', linewidth=2, label='Total Input Mass (1000 Mg)')
ax1.set_title('Simplified bioDYM Input: Total Wood Mass', fontsize=14)
ax1.set_ylabel('Fresh Mass (1000 Mg)')
plt.show()

# Print specific values for your text
print(f"Start (1950): {df.loc[1950, 'Total_FM_Mg']:.0f} Mg")
print(f"Future (2050): {df.loc[2050, 'Total_FM_Mg']:.0f} Mg")