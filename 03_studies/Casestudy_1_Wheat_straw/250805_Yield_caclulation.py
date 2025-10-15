import numpy as np
import pandas as pd
from datetime import datetime

# --- Parameters ---
start_year = 2025
end_year = 2050
years = np.arange(start_year, end_year + 1)

base_yield_tonnes = 770000  # Mean annual yield
std_dev_tonnes = 100000     # Standard deviation for fluctuation
annual_trend_factor = 0.005 # 0.5% increase per year

# --- Calculation ---
# 1. Create the linear trend
# We calculate the increase relative to the starting year 2025
trend_increase = (years - start_year) * (base_yield_tonnes * annual_trend_factor)
trend_yield = base_yield_tonnes + trend_increase

# 2. Add random annual fluctuation
fluctuations = np.random.normal(0, std_dev_tonnes, len(years))

# 3. Final time series
final_yield_time_series = trend_yield + fluctuations

# Create a DataFrame for easy use
df_yield = pd.DataFrame({
    'Year': years,
    'Projected_Yield_Tonnes': final_yield_time_series
})

# Round the yield values to 2 decimal places for cleaner output
df_yield['Projected_Yield_Tonnes'] = df_yield['Projected_Yield_Tonnes'].round(2)

# Display results
print("Yield Projection Results:")
print(df_yield)
print(f"\nDataFrame shape: {df_yield.shape}")
print(f"Number of years: {len(df_yield)}")

# Export to Excel
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
excel_filename = f"yield_projection_{timestamp}.xlsx"

# Create Excel writer with formatting
with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
    # Write the main data
    df_yield.to_excel(writer, sheet_name='Yield_Projection', index=False)
    
    # Get the workbook and worksheet for formatting
    workbook = writer.book
    worksheet = writer.sheets['Yield_Projection']
    
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
        adjusted_width = min(max_length + 2, 20)  # Cap at 20 characters
        worksheet.column_dimensions[column_letter].width = adjusted_width

print(f"\nResults exported to: {excel_filename}")
print(f"File contains {len(df_yield)} years of yield projections")
