import pandas as pd
import sys

try:
    xls = pd.ExcelFile('01_data/01_input/251027_BioDYM_ODYM.xlsm')
    df = pd.read_excel(xls, sheet_name='1_1_Definition_Flows')
    print('Columns:', df.columns.tolist())
    print('Head:\n', df.head().to_string())
except Exception as e:
    print(f"Error reading Excel sheet: {e}", file=sys.stderr)
    sys.exit(1)
