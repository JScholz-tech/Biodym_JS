import numpy as np
import pandas as pd
from datetime import datetime

# --- 1. Define Your Assumptions ---

# Time Period
start_year = 2025
end_year = 2050
years = np.arange(start_year, end_year + 1)

# Yield Parameters (with uncertainty)
base_yield_tonnes = 770000      # Mean annual yield for a 1000 km² area
std_dev_tonnes = 100000         # Standard deviation for annual fluctuation
annual_trend_factor = 0.005     # 0.5% increase per year

# Material Composition Fractions (fixed for this calculation)
wc_frac = 0.14  # 14% Water Content
dm_frac = 0.86  # 86% Dry Matter
cc_dm_frac = 0.48 # 48% Carbon Content of the Dry Matter

# --- 2. Generate the Total Yield Time Series (with uncertainty) ---

# Calculate the deterministic linear trend
trend_increase = (years - start_year) * (base_yield_tonnes * annual_trend_factor)
trend_yield = base_yield_tonnes + trend_increase

# *** START OF CHANGE ***
# Generate the random annual fluctuation
fluctuations = np.random.normal(loc=0, scale=std_dev_tonnes, size=len(years))

# Combine trend and fluctuation to get the final stochastic time series
total_yield_series = trend_yield + fluctuations

# Ensure yield cannot be negative (a robust check)
total_yield_series[total_yield_series < 0] = 0
# *** END OF CHANGE ***


# Create a DataFrame to hold the data
df_flows = pd.DataFrame({
    'Year': years,
    'Total_Yield': total_yield_series
})

# --- 3. Calculate the Component Flows (logic is unchanged) ---

# Calculate the mass of water and dry matter
df_flows['Water_Mass'] = df_flows['Total_Yield'] * wc_frac
df_flows['Dry_Matter_Mass'] = df_flows['Total_Yield'] * dm_frac

# Calculate the Carbon Flow (from Atmosphere)
df_flows['Carbon_Flow_from_Atmosphere'] = df_flows['Dry_Matter_Mass'] * cc_dm_frac

# Calculate the Environmental Flow (from Environment)
non_carbon_dry_matter = df_flows['Dry_Matter_Mass'] - df_flows['Carbon_Flow_from_Atmosphere']
df_flows['Environmental_Flow'] = df_flows['Water_Mass'] + non_carbon_dry_matter

# --- 4. Display the Final Input Flows ---

# Select and rename the final columns for clarity
final_input_flows = df_flows[['Year', 'Carbon_Flow_from_Atmosphere', 'Environmental_Flow', 'Total_Yield']].copy()
final_input_flows.set_index('Year', inplace=True)

print("Calculated Stochastic Annual Input Flows (in Tonnes):\n")
print(final_input_flows.round(2))

# Round all values to 2 decimal places for cleaner output
final_input_flows = final_input_flows.round(2)

# Display additional information
print(f"\nDataFrame shape: {final_input_flows.shape}")
print(f"Number of years: {len(final_input_flows)}")

# Export to Excel
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
excel_filename = f"stochastic_input_flows_{timestamp}.xlsx"

# Create Excel writer with formatting
with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
    # Write the main data
    final_input_flows.to_excel(writer, sheet_name='Stochastic_Input_Flows', index=True)
    
    # Get the workbook and worksheet for formatting
    workbook = writer.book
    worksheet = writer.sheets['Stochastic_Input_Flows']
    
    # Auto-adjust column widths
    for column in worksheet.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 25)  # Cap at 25 characters for longer column names
        worksheet.column_dimensions[column_letter].width = adjusted_width

print(f"\nResults exported to: {excel_filename}")
print(f"File contains {len(final_input_flows)} years of stochastic input flow calculations")