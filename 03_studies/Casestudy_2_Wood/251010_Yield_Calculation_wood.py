import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- 1. Define Anchor Points and Parameters ---
# Sourced data points for total German harvest in Million m³
anchor_points = {
    1950: 33.5,
    1970: 28.3,
    1990: 56.8, # Storm anomaly
    2002: 47.8,
    2022: 80.7  # Most recent data point
}

# Define area parameters and scaling factors
AREA_STUDY_KM2 = 1000
AREA_GERMANY_WEST_KM2 = 73000
AREA_GERMANY_UNIFIED_KM2 = 114000

FACTOR_WEST = AREA_STUDY_KM2 / AREA_GERMANY_WEST_KM2
FACTOR_UNIFIED = AREA_STUDY_KM2 / AREA_GERMANY_UNIFIED_KM2

# --- 2. Create Historical Series with Interpolation ---
# Create a full time index from 1950 to 2022
historical_years = np.arange(1950, 2023)
df_hist = pd.DataFrame(index=historical_years)
df_hist.index.name = 'Year'

# Place anchor points in the dataframe
df_hist['Harvest_Mm3_Germany'] = pd.Series(anchor_points)

# Use linear interpolation to fill the gaps between anchor points
df_hist['Harvest_Mm3_Germany'].interpolate(method='linear', inplace=True)

# --- 3. Apply Dynamic Scaling ---
df_hist['Scaled_Harvest_Mm3'] = np.where(
    df_hist.index < 1990,
    df_hist['Harvest_Mm3_Germany'] * FACTOR_WEST,
    df_hist['Harvest_Mm3_Germany'] * FACTOR_UNIFIED
)

# --- 4. Generate Future Forecast (Bottom-Up Approach) ---
AREA_HA = 100000  # 1,000 km² in hectares
AVG_HARVEST_M3_PER_HA = 6.7  # Official average harvest from BWI4
bau_baseline_m3 = AREA_HA * AVG_HARVEST_M3_PER_HA
bau_baseline_Mm3 = bau_baseline_m3 / 1_000_000 # Convert to Million m³

# Calculate a "normal" volatility from the scaled historical data (pre-calamity)
normal_period = df_hist.loc[2000:2017]
std_dev_percent = normal_period['Scaled_Harvest_Mm3'].std() / normal_period['Scaled_Harvest_Mm3'].mean()

future_years = np.arange(2023, 2101)
future_fluctuation = np.random.normal(0, bau_baseline_Mm3 * std_dev_percent, len(future_years))
bau_forecast = bau_baseline_Mm3 + future_fluctuation

# --- 5. Visualization ---
plt.style.use('seaborn-v0_8-whitegrid')
fig, ax = plt.subplots(figsize=(15, 8))

# Plot the final scaled historical time series
ax.plot(df_hist.index, df_hist['Scaled_Harvest_Mm3'], label='Scaled Historical Harvest (Interpolated)', color='black')

# Highlight the anchor points
ax.plot(list(anchor_points.keys()), df_hist.loc[list(anchor_points.keys())]['Harvest_Mm3_Germany'] * np.where(np.array(list(anchor_points.keys())) < 1990, FACTOR_WEST, FACTOR_UNIFIED), 'ro', label='Sourced Anchor Points')

# Plot the future forecast
ax.axhline(y=bau_baseline_Mm3, label=f'BAU Baseline ({bau_baseline_Mm3:.2f} M m³/year)', color='green', linestyle='--')
ax.plot(future_years, bau_forecast, label='BAU Forecast (2023-2100)', color='blue', alpha=0.8)

ax.set_title('Hybrid "Anchor Point" Wood Harvest Forecast for 1000 km² Area', fontsize=16)
ax.set_xlabel('Year', fontsize=12)
ax.set_ylabel('Scaled Annual Harvest (Million m³)', fontsize=12)
ax.legend()
ax.grid(True)
plt.show()

# --- 6. Final Time Series ---
final_historical_series = df_hist['Scaled_Harvest_Mm3']
final_future_series = pd.Series(bau_forecast, index=future_years)
full_timeseries = pd.concat([final_historical_series, final_future_series]) * 1_000_000 # convert to m³

# print(full_timeseries.head())
# print(full_timeseries.tail())