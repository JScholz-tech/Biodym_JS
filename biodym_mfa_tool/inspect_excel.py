import pandas as pd

def inspect_excel_structure(file_path):
    """
    Reads an Excel file and prints its structure (sheet names and columns).
    """
    try:
        xls = pd.ExcelFile(file_path)
        print(f"Successfully opened Excel file: {file_path}")
        print("\n" + "="*30)
        print("SHEET STRUCTURE")
        print("="*30)

        for sheet_name in xls.sheet_names:
            try:
                df = xls.parse(sheet_name)
                print(f"\n--- Sheet: '{sheet_name}' ---")
                if df.empty:
                    print("    (Sheet is empty)")
                else:
                    print("    Columns:")
                    for col in df.columns:
                        print(f"      - {col}")
            except Exception as e:
                print(f"\n--- Sheet: '{sheet_name}' ---")
                print(f"    Could not parse sheet. Error: {e}")

    except FileNotFoundError:
        print(f"ERROR: File not found at '{file_path}'")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    input_file = "data/01_input/250902_CS1_Wheat_Straw.xlsx"
    inspect_excel_structure(input_file)
