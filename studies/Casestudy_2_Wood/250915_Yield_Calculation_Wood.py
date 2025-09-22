import numpy as np
import pandas as pd
import plotly.express as px

# --- 1. Define Parameters for Wood Yield ---

# Time Period
start_year = 1900
end_year = 2050
years = np.arange(start_year, end_year + 1)

# Area
area_ha = 1000 * 100  # 1000 km² = 100,000 ha

# Yield Parameters (per hectare)
base_yield_m3_per_ha = 11.0      # m³/ha/yr
std_dev_m3_per_ha = 1.5          # m³/ha/yr
annual_trend_factor = 0.0005     # 0.05% increase per year

# Conversion Parameter
density_tonnes_per_m3 = 0.8      # tonnes/m³

# --- 2. Generate Yield Time Series (in Volume) ---

# Calculate the deterministic linear trend over the long period
trend_increase = (years - start_year) * (base_yield_m3_per_ha * annual_trend_factor)
trend_yield_m3 = base_yield_m3_per_ha + trend_increase

# Generate the random annual fluctuation
fluctuations_m3 = np.random.normal(0, std_dev_m3_per_ha, len(years))

# Combine trend and fluctuation
yield_per_ha_m3_series = trend_yield_m3 + fluctuations_m3

# Ensure yield cannot be negative
yield_per_ha_m3_series[yield_per_ha_m3_series < 0] = 0

# --- 3. Calculate Total Yield and Convert to Mass (Tonnes) ---

# Calculate total yield for the area in cubic meters
total_yield_m3_series = yield_per_ha_m3_series * area_ha

# Convert total volume to total mass
total_yield_tonnes_series = total_yield_m3_series * density_tonnes_per_m3

# --- 4. Create DataFrame and Display ---

df_wood_yield = pd.DataFrame({
    'Year': years,
    'Projected_Yield_Tonnes': total_yield_tonnes_series
})

# Display the beginning and end of the time series
print("Wood Yield Time Series (1900-2050):\n")
print(df_wood_yield.head())
print("\n...\n")
print(df_wood_yield.tail())


# --- 5. Export to Excel ---
output_filename = 'wood_yield_calculation_results.xlsx'
df_wood_yield.to_excel(output_filename, index=False, sheet_name='Wood_Yield_Data')
print(f"\nData exported to: {output_filename}")

# --- 6. Optional: Visualize the Results ---
fig = px.line(df_wood_yield, 
              x='Year', 
              y='Projected_Yield_Tonnes', 
              title='Projected Annual Wood Yield (1000 km² Area)')
fig.show()