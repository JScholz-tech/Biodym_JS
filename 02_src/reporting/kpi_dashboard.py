# -*- coding: utf-8 -*-
"""
KPI Dashboard Module for BioDYM MFA.

This module contains functions to calculate, display, and export key
performance indicators (KPIs) for the MFA system.
"""

import pandas as pd
import numpy as np
import os

def calculate_system_kpis(mfa_results, process_logic_map):
    """
    Calculates a set of system-level KPIs for all elements in the MFA results.

    Parameters
    ----------
    mfa_results : odym.MFAsystem
        The solved MFA system object.
    process_logic_map : dict
        A dictionary mapping Process_IDs to their logic.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the calculated KPIs for each year and element.
    """
    years = mfa_results.IndexTable.Classification['Time'].Items
    elements = mfa_results.Elements
    
    input_processes = {pid for pid, logic in process_logic_map.items() if logic == 'Input'}
    output_processes = {pid for pid, logic in process_logic_map.items() if logic == 'Output'}

    all_kpi_data = []

    for element_idx, element_name in enumerate(elements):
        kpi_data_per_element = []
        for i, year in enumerate(years):
            # Total Input
            total_input = sum(
                f.Values[i, element_idx] for f in mfa_results.FlowDict.values() if f.P_Start in input_processes
            )

            # Total Output
            total_output = sum(
                f.Values[i, element_idx] for f in mfa_results.FlowDict.values() if f.P_End in output_processes
            )

            # Net Stock Change
            net_stock_change = sum(
                s.Values[i, element_idx] for s in mfa_results.StockDict.values() if s.Name.startswith('dS_')
            )

            # Mass Balance Error
            balance_error = total_input - total_output - net_stock_change

            # Critical Deviation (%)
            critical_deviation = (balance_error / total_input * 100) if total_input != 0 else 0

            kpi_data_per_element.append({
                'Year': year,
                'Element': element_name,
                'Total Input': total_input,
                'Total Output': total_output,
                'Net Stock Change': net_stock_change,
                'Mass Balance Error': balance_error,
                'Critical Deviation (%)': critical_deviation
            })
        all_kpi_data.extend(kpi_data_per_element)

    return pd.DataFrame(all_kpi_data)

def generate_kpi_dashboard(mfa_results, process_logic_map, output_path):
    """
    Calculates KPIs for all elements, displays a summary, and exports to Excel.

    Parameters
    ----------
    mfa_results : odym.MFAsystem
        The solved MFA system object.
    process_logic_map : dict
        A dictionary mapping Process_IDs to their logic.
    output_path : str
        Path to save the output Excel file.
    """
    kpi_df = calculate_system_kpis(mfa_results, process_logic_map)
    if kpi_df.empty:
        return

    unit = mfa_results.Unit or "Mass"
    time_unit = "/a" # Assuming per annum

    print("\n" + "="*60)
    print("📊 KEY PERFORMANCE INDICATOR (KPI) DASHBOARD")
    print("="*60)

    for element_name in mfa_results.Elements:
        element_kpis = kpi_df[kpi_df['Element'] == element_name]
        if element_kpis.empty:
            continue

        # --- Display Summary Dashboard for each element ---
        print(f"\n--- KPIs for Element: {element_name} ---")
        first_year_kpis = element_kpis.iloc[0]
        last_year_kpis = element_kpis.iloc[-1]

        summary = {
            "Metric": ["Total Input", "Total Output", "Net Stock Change", "Mass Balance Error", "Critical Deviation"],
            "Unit": [f"{unit}{time_unit}", f"{unit}{time_unit}", f"{unit}{time_unit}", f"{unit}{time_unit}", "%"],
            f"First Year ({element_kpis['Year'].iloc[0]}) ": [
                f"{first_year_kpis['Total Input']:.2f}",
                f"{first_year_kpis['Total Output']:.2f}",
                f"{first_year_kpis['Net Stock Change']:.2f}",
                f"{first_year_kpis['Mass Balance Error']:.4f}",
                f"{first_year_kpis['Critical Deviation (%)']:.4f}"
            ],
            f"Last Year ({element_kpis['Year'].iloc[-1]}) ": [
                f"{last_year_kpis['Total Input']:.2f}",
                f"{last_year_kpis['Total Output']:.2f}",
                f"{last_year_kpis['Net Stock Change']:.2f}",
                f"{last_year_kpis['Mass Balance Error']:.4f}",
                f"{last_year_kpis['Critical Deviation (%)']:.4f}"
            ]
        }
        summary_df = pd.DataFrame(summary)
        print(summary_df.to_string(index=False))

        # --- Calculate and Display Throughput for each element ---
        try:
            element_idx = mfa_results.Elements.index(element_name)
            all_flows = np.array([f.Values[:, element_idx] for f in mfa_results.FlowDict.values()])
            
            throughput_first_year = all_flows[:, 0].sum()
            throughput_last_year = all_flows[:, -1].sum()
            throughput_average = all_flows.mean(axis=1).sum()

            print("\n" + "-"*40)
            print(f"System Throughput ({element_name}):")
            print(f"  - First Year: {throughput_first_year:.2f} {unit}{time_unit}")
            print(f"  - Last Year:  {throughput_last_year:.2f} {unit}{time_unit}")
            print(f"  - Average:    {throughput_average:.2f} {unit}{time_unit}")
            print("-"*40)

        except (ValueError, IndexError):
            continue

    # --- Export to Excel ---
    try:
        output_dir = os.path.dirname(output_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Re-organize columns for export
        export_df = kpi_df[[
            'Year', 'Element', 'Total Input', 'Total Output', 'Net Stock Change', 
            'Mass Balance Error', 'Critical Deviation (%)'
        ]]

        export_df.to_excel(output_path, index=False, sheet_name='System_KPIs_by_Year')
        print(f"\n✅ KPI data for all elements successfully exported to: {output_path}")
    except Exception as e:
        print(f"\n⚠️ Could not export KPI data: {e}")
