import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# Set random seed for reproducibility
np.random.seed(42)

# --- 1. Data and Parameters ---
# Data has been updated with the new values for 1950-2000 from your image.
# Data from 2001-2022 is from the previous dataset to create a complete time series.
data = {
    'Year': np.arange(1950, 2023),
    'Harvest_Mm3_Germany': [
        # New data from 1950-2000
        25.61, 27.47, 24.54, 23.65, 22.80, 25.44, 21.67, 23.78, 24.03, 23.65,
        24.68, 26.23, 26.98, 24.09, 26.93, 25.72, 27.20, 26.18, 24.90, 26.58,
        28.04, 27.87, 23.70, 31.00, 31.59, 26.11, 28.89, 29.34, 28.64, 27.45,
        30.11, 29.20, 28.88, 27.52, 28.41, 31.45, 29.49, 29.40, 29.27, 31.90,
        68.98, 32.09, 27.66, 29.15, 37.10, 45.04, 50.69, 51.41, 50.86, 50.28,
        62.55,
        # Old data from 2001-2022 to complete the series
        56.43, 60.06, 60.96, 67.12, 57.53, 79.05, 98.07, 75.87, 64.25, 79.79, 
        74.70, 74.70, 63.63, 68.78, 70.80, 72.86, 68.31, 75.15, 76.16, 
        80.50, 80.46, 80.67
    ]
}
df = pd.DataFrame(data)

# Define area parameters and scaling factors
AREA_STUDY_KM2 = 1000
AREA_GERMANY_WEST_KM2 = 73000
AREA_GERMANY_UNIFIED_KM2 = 114000

FACTOR_WEST = AREA_STUDY_KM2 / AREA_GERMANY_WEST_KM2
FACTOR_UNIFIED = AREA_STUDY_KM2 / AREA_GERMANY_UNIFIED_KM2

print(f"Study Area: {AREA_STUDY_KM2} km²")
print(f"West Germany Scaling Factor: {FACTOR_WEST:.6f}")
print(f"Unified Germany Scaling Factor: {FACTOR_UNIFIED:.6f}")

# --- 2. Apply Dynamic Scaling ---
df['Scaled_Harvest_Mm3'] = np.where(
    df['Year'] < 1990,
    df['Harvest_Mm3_Germany'] * FACTOR_WEST,
    df['Harvest_Mm3_Germany'] * FACTOR_UNIFIED
)

# --- 3. Calculate Baseline and Fluctuation for Scenarios ---
baseline_period = df[df['Year'] >= 2000].copy()
bau_average = baseline_period['Scaled_Harvest_Mm3'].mean()
std_dev_percent = baseline_period['Scaled_Harvest_Mm3'].std() / baseline_period['Scaled_Harvest_Mm3'].mean()

print(f"BAU Baseline (Average of 2000-2022): {bau_average:.4f} Million m³")
print(f"Volatility (Std Dev as % of Mean, 2000-2022): {std_dev_percent:.2%}")

# --- 4. Generate Future "Business-as-Usual" (BAU) Scenario ---
future_years = np.arange(2023, 2101)
future_baseline = np.full(len(future_years), bau_average)
future_fluctuation = np.random.normal(0, bau_average * std_dev_percent, len(future_years))
bau_forecast = future_baseline + future_fluctuation

# --- 5. Create Additional Scenarios ---
# Define scenarios with different reduction/increase factors
scenarios = {
    'BAU': {
        'factor': 1.0,
        'forecast': bau_forecast,
        'baseline': bau_average,
        'description': 'Business as Usual - Based on 2000-2022 average'
    },
    'Reduced_Yield': {
        'factor': 0.85,
        'forecast': bau_forecast * 0.85,
        'baseline': bau_average * 0.85,
        'description': '15% reduction scenario'
    },
    'High_Yield': {
        'factor': 1.15,
        'forecast': bau_forecast * 1.15,
        'baseline': bau_average * 1.15,
        'description': '15% increase scenario'
    },
    'Low_Yield': {
        'factor': 0.70,
        'forecast': bau_forecast * 0.70,
        'baseline': bau_average * 0.70,
        'description': '30% reduction scenario'
    }
}

# --- 5. Excel Export ---
print("\n" + "=" * 70)
print("Exporting data to Excel...")
print("=" * 70)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_path = f"wood_yield_scenarios_{AREA_STUDY_KM2}km2_{timestamp}.xlsx"

with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
    # 1. Historical Data Sheet
    df.to_excel(writer, sheet_name='Historical_Data', index=False)
    
    # 2. Individual Scenario Sheets
    for scenario_name, scenario_info in scenarios.items():
        scenario_df = pd.DataFrame({
            'Year': future_years,
            'Baseline_Mm3': scenario_info['baseline'],
            'Fluctuation_Mm3': future_fluctuation * scenario_info['factor'],
            'Total_Forecast_Mm3': scenario_info['forecast'],
            'Scenario': scenario_name,
            'Factor': scenario_info['factor']
        })
        sheet_name = f'Scenario_{scenario_name}'[:31]
        scenario_df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    # 3. Scenario Comparison Sheet
    comparison_data = {'Year': future_years}
    for scenario_name, scenario_info in scenarios.items():
        comparison_data[f'{scenario_name}_Mm3'] = scenario_info['forecast']
    comparison_df = pd.DataFrame(comparison_data)
    comparison_df.to_excel(writer, sheet_name='Scenario_Comparison', index=False)
    
    # 4. Metadata Sheet
    metadata = {
        'Parameter': [
            'Study Area (km²)',
            'West Germany Area (km²)',
            'Unified Germany Area (km²)',
            'West Scaling Factor',
            'Unified Scaling Factor',
            'BAU Baseline (Mm³/year)',
            'Standard Deviation (Mm³/year)',
            'Std Dev as % of Mean',
            'Baseline Period',
            'Forecast Period',
            'Number of Years Forecasted',
            'Number of Scenarios',
            'Random Seed',
            'Calculation Date',
            'Data Source'
        ],
        'Value': [
            AREA_STUDY_KM2,
            AREA_GERMANY_WEST_KM2,
            AREA_GERMANY_UNIFIED_KM2,
            FACTOR_WEST,
            FACTOR_UNIFIED,
            bau_average,
            bau_average * std_dev_percent,
            f'{std_dev_percent:.2%}',
            '2000-2022',
            '2023-2100',
            len(future_years),
            len(scenarios),
            42,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'Historical German harvest data (1950-2022)'
        ]
    }
    metadata_df = pd.DataFrame(metadata)
    metadata_df.to_excel(writer, sheet_name='Metadata', index=False)
    
    # 5. Scenario Descriptions
    scenario_desc = {
        'Scenario': list(scenarios.keys()),
        'Factor': [info['factor'] for info in scenarios.values()],
        'Baseline (Mm³/year)': [info['baseline'] for info in scenarios.values()],
        'Description': [info['description'] for info in scenarios.values()]
    }
    scenario_desc_df = pd.DataFrame(scenario_desc)
    scenario_desc_df.to_excel(writer, sheet_name='Scenario_Descriptions', index=False)
    
    # 6. Summary Statistics
    summary_stats = []
    for scenario_name, scenario_info in scenarios.items():
        forecast = scenario_info['forecast']
        stats = {
            'Scenario': scenario_name,
            'Mean (Mm³)': forecast.mean(),
            'Median (Mm³)': np.median(forecast),
            'Std Dev (Mm³)': forecast.std(),
            'Min (Mm³)': forecast.min(),
            'Max (Mm³)': forecast.max(),
            'Range (Mm³)': forecast.max() - forecast.min()
        }
        summary_stats.append(stats)
    summary_df = pd.DataFrame(summary_stats)
    summary_df.to_excel(writer, sheet_name='Summary_Statistics', index=False)

print(f"[SUCCESS] Data exported to Excel: {output_path}")
print(f"  - 7 sheets created:")
print(f"    - Historical_Data")
print(f"    - Scenario_BAU, Scenario_Reduced_Yield, Scenario_High_Yield, Scenario_Low_Yield")
print(f"    - Scenario_Comparison")
print(f"    - Metadata")
print(f"    - Scenario_Descriptions")
print(f"    - Summary_Statistics")

# --- 6. Visualization ---
print("Creating visualization...")
plt.style.use('seaborn-v0_8-whitegrid')
fig, ax = plt.subplots(figsize=(15, 8))

# Plot historical data
ax.plot(df['Year'], df['Scaled_Harvest_Mm3'], 
        label=f'Scaled Historical Harvest ({AREA_STUDY_KM2} km²)', 
        color='black', marker='.', linestyle='None', markersize=4)

# Plot the calculated average baseline
ax.axhline(y=bau_average, label=f'BAU Baseline (2000-2022 Average)', 
           color='red', linestyle='--', linewidth=2)

# Plot all scenarios
colors = ['blue', 'green', 'orange', 'purple']
for i, (scenario_name, scenario_info) in enumerate(scenarios.items()):
    color = colors[i % len(colors)]
    alpha = 0.8 if scenario_name == 'BAU' else 0.6
    ax.plot(future_years, scenario_info['forecast'], 
            label=f'{scenario_name} Forecast (2023-2100)', 
            color=color, alpha=alpha, linewidth=1.5)

ax.set_title(f'Scenario-Based Wood Harvest Forecast for {AREA_STUDY_KM2} km² Area', fontsize=16)
ax.set_xlabel('Year', fontsize=12)
ax.set_ylabel('Scaled Annual Harvest (Million m³)', fontsize=12)
ax.ticklabel_format(style='plain', axis='y')  # Prevent scientific notation
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)

# Add text box with baseline information
baseline_text = f'BAU Baseline: {bau_average:.4f} Mm³\n'
baseline_text += f'Std Deviation: {bau_average * std_dev_percent:.4f} Mm³\n'
baseline_text += f'Volatility: {std_dev_percent:.2%}\n'
baseline_text += f'Source: Historical German data\n'
baseline_text += f'Area: {AREA_STUDY_KM2} km²'

ax.text(0.02, 0.98, baseline_text, transform=ax.transAxes, fontsize=10,
        verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

plt.tight_layout()

# Save plot
plot_path = f"wood_yield_scenarios_{AREA_STUDY_KM2}km2_{timestamp}.png"
plt.savefig(plot_path, dpi=300, bbox_inches='tight')
print(f"[SUCCESS] Plot saved to: {plot_path}")

plt.show()

# --- 7. Print Summary ---
print("\n" + "=" * 70)
print("SUMMARY STATISTICS")
print("=" * 70)
print(f"Study Area: {AREA_STUDY_KM2} km²")
print(f"Historical Period: 1950-2022 ({len(df)} years)")
print(f"Baseline Period: 2000-2022 ({len(baseline_period)} years)")
print(f"Forecast Period: 2023-2100 ({len(future_years)} years)")
print()
print("Scaling Factors:")
print(f"  West Germany (pre-1990): {FACTOR_WEST:.6f}")
print(f"  Unified Germany (post-1990): {FACTOR_UNIFIED:.6f}")
print()
print("Baseline Parameters:")
print(f"  BAU Baseline: {bau_average:.4f} Mm³/year")
print(f"  Standard Deviation: {bau_average * std_dev_percent:.4f} Mm³/year ({std_dev_percent:.2%})")
print()
print("Scenario Summary (2023-2100):")
print("-" * 70)
for scenario_name, scenario_info in scenarios.items():
    forecast = scenario_info['forecast']
    print(f"{scenario_name}:")
    print(f"  Factor: {scenario_info['factor']:.2f}")
    print(f"  Mean: {forecast.mean():.4f} Mm³")
    print(f"  Min:  {forecast.min():.4f} Mm³")
    print(f"  Max:  {forecast.max():.4f} Mm³")
    print(f"  Range: {forecast.max() - forecast.min():.4f} Mm³")
    print()

print("=" * 70)
print("Analysis completed successfully!")
print("=" * 70)







