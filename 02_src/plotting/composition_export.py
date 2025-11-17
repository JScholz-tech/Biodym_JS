# -*- coding: utf-8 -*-
"""
Functions for exporting flow composition data.
"""

import pandas as pd
import os


def export_flow_composition(mfa_system_results, output_path):
    """
    Exports the composition of each flow to an Excel file.

    Parameters
    ----------
    mfa_system_results : odym.MFAsystem
        The solved MFA system object containing flow and stock results.
    output_path : str
        The path to the output Excel file.
    """
    flows = mfa_system_results.FlowDict
    years = mfa_system_results.IndexTable.Classification["Time"].Items
    elements = mfa_system_results.Elements

    data = []

    for i, year in enumerate(years):
        for flow_name, flow in flows.items():
            values = flow.Values[i, :]

            # Phase 1b: Handle new element structure safely
            wc_mass = values[elements.index("WC")] if "WC" in elements else 0
            dm_mass = values[elements.index("DM")] if "DM" in elements else 0
            cc_mass = values[elements.index("CC")] if "CC" in elements else 0
            non_carbon_dm_mass = dm_mass - cc_mass
            total_mass = wc_mass + dm_mass

            if total_mass > 0:
                wc_perc = wc_mass / total_mass * 100
                cc_perc = cc_mass / total_mass * 100
                non_carbon_dm_perc = non_carbon_dm_mass / total_mass * 100
            else:
                wc_perc = 0
                cc_perc = 0
                non_carbon_dm_perc = 0

            data.append(
                {
                    "Year": year,
                    "Flow Name": flow_name,
                    "Water Content (Mass)": wc_mass,
                    "Dry Matter (Mass)": dm_mass,
                    "Carbon Content (Mass)": cc_mass,
                    "Non-Carbon Dry Matter (Mass)": non_carbon_dm_mass,
                    "Total Mass": total_mass,
                    "Water Content (%)": wc_perc,
                    "Carbon Content (%)": cc_perc,
                    "Non-Carbon Dry Matter (%)": non_carbon_dm_perc,
                }
            )

    df = pd.DataFrame(data)

    # Create the output directory if it doesn't exist
    output_dir = os.path.dirname(output_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    df.to_excel(output_path, index=False, sheet_name="Flow Composition")
    print(f"\n--> Flow composition data successfully exported to {output_path}")
