# Modified FOMP Parameter Loading for Pool_ID System

def load_fomp_parameters_with_pool_id(excel_data):
    """
    Reads the '3_2_Definition_FOMP' sheet with Pool_ID system and constructs 
    the FOMP_PARAMS dictionary compatible with the existing system.
    """
    sheet_name = "3_2_Definition_FOMP"
    print(f"--> Loading FOMP parameters from sheet '{sheet_name}' with Pool_ID system...")

    if sheet_name not in excel_data:
        print(f"--> INFO: Sheet '{sheet_name}' not found. Using empty FOMP configuration.")
        return {}

    df_fomp = excel_data[sheet_name]
    fomp_params = {}

    for _, row in df_fomp.iterrows():
        if pd.isna(row["Pool_ID"]) or pd.isna(row["Parameter_Name"]):
            continue

        pool_id = str(row["Pool_ID"])
        param_name = row["Parameter_Name"]
        value = row["Value"]

        # Extract process ID from Pool_ID format (e.g., "1:08_pool_1_k1" -> "08")
        try:
            # Handle format: "X:YY_pool_Z_k1" -> extract YY
            if ":" in pool_id:
                process_id = int(pool_id.split(":")[1].split("_")[0])
            else:
                # Handle format: "YY_Outflow_Z" -> extract YY
                process_id = int(pool_id.split("_")[0])
        except (ValueError, IndexError):
            print(f"⚠️ WARNING: Could not extract process ID from Pool_ID: {pool_id}")
            continue

        # Initialize process dictionary if not exists
        if process_id not in fomp_params:
            fomp_params[process_id] = {}

        # Map parameter names to expected format
        if param_name == "output_carbon_id":
            fomp_params[process_id]["outflow_id"] = value
        elif param_name == "output_environmental_id":
            fomp_params[process_id]["outflow_id_2"] = value
        else:
            # Keep original parameter names for calculation
            try:
                fomp_params[process_id][param_name] = float(value)
            except (ValueError, TypeError):
                fomp_params[process_id][param_name] = value
    
    print(f"--> Successfully loaded configurations for {len(fomp_params)} FOMP process(es).")
    for process_id, params in fomp_params.items():
        print(f"   Process {process_id}: {len(params)} parameters")
    
    return fomp_params

# For Monte Carlo uncertainty, you would use parameter names like:
# "P08_decay_k1 (Labile pool)" for Process 08
# "P10_decay_k1 (Labile pool)" for Process 10  
# "P07_decay_k1 (Labile pool)" for Process 07

