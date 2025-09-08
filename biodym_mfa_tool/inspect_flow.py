import pandas as pd

def find_flow_source(file_path, flow_id_to_find):
    """
    Finds the source and destination processes for a given flow ID.
    """
    try:
        # Read both the flow and process definition sheets
        xls = pd.ExcelFile(file_path)
        if '1_1_Definition_Flows' not in xls.sheet_names:
            print("ERROR: Sheet '1_1_Definition_Flows' not found.")
            return
        if '2_1_Definition_Processes' not in xls.sheet_names:
            print("ERROR: Sheet '2_1_Definition_Processes' not found.")
            return

        df_flows = xls.parse('1_1_Definition_Flows')
        df_processes = xls.parse('2_1_Definition_Processes')

        # Find the row for the specified flow
        flow_info = df_flows[df_flows['Flow_ID'] == flow_id_to_find]

        if flow_info.empty:
            print(f"Flow ID '{flow_id_to_find}' not found in '1_1_Definition_Flows'.")
            return

        # Get the source and destination process IDs
        source_id = flow_info['Process_ID_O'].iloc[0]
        dest_id = flow_info['Process_ID_I'].iloc[0]

        # Get the names of the processes
        source_process_name = df_processes[df_processes['ID'] == source_id]['Name(EN)'].iloc[0]
        dest_process_name = df_processes[df_processes['ID'] == dest_id]['Name(EN)'].iloc[0]

        print(f"Analysis for Flow: {flow_id_to_find}")
        print("-" * 30)
        print(f"Source (Origin): Process {source_id} ({source_process_name})")
        print(f"Destination (Input): Process {dest_id} ({dest_process_name})")

    except FileNotFoundError:
        print(f"ERROR: File not found at '{file_path}'")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    input_file = "data/01_input/250902_CS1_Wheat_Straw.xlsx"
    flow_to_find = "F_08_05"
    find_flow_source(input_file, flow_to_find)
