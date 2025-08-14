
import pandas as pd
import sys

# Check if the correct number of arguments are provided
if len(sys.argv) != 3:
    print("Usage: python read_excel_data.py <file_path> <sheet_name>")
    sys.exit(1)

file_path = sys.argv[1]
sheet_name = sys.argv[2]

try:
    xls = pd.ExcelFile(file_path)
    if sheet_name in xls.sheet_names:
        print(f"--- Content of sheet: {sheet_name} ---")
        df = pd.read_excel(xls, sheet_name=sheet_name)
        print(df.to_string())
    else:
        print(f"--- Sheet '{sheet_name}' not found in the Excel file. ---")
except FileNotFoundError:
    print(f"Error: The file was not found at {file_path}")
except Exception as e:
    print(f"An error occurred: {e}")
