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
    Calculates a set of system-level KPIs for the MFA results.

    Parameters
    ----------
    mfa_results : odym.MFAsystem
        The solved MFA system object.
    process_logic_map : dict
        A dictionary mapping Process_IDs to their logic.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the calculated KPIs for each year.
    """
    years = mfa_results.IndexTable.Classification['Time'].Items
    try:
        cc_idx = mfa_results.Elements.index('CC')
    except ValueError:
        print("⚠️ Carbon Content (CC) not in elements. Cannot calculate Carbon KPIs.")
        return pd.DataFrame()

    input_processes = {pid for pid, logic in process_logic_map.items() if logic == 'Input'}
    output_processes = {pid for pid, logic in process_logic_map.items() if logic == 'Output'}

    kpi_data = []

    for i, year in enumerate(years):
        # KPI B: Sum of Carbon Input
        total_carbon_input = sum(
            f.Values[i, cc_idx] for f in mfa_results.FlowDict.values() if f.P_Start in input_processes
        )

        # KPI D: Sum of Carbon Output
        total_carbon_output = sum(
            f.Values[i, cc_idx] for f in mfa_results.FlowDict.values() if f.P_End in output_processes
        )

        # KPI F: Net Carbon Stock Change
        net_stock_change = sum(
            s.Values[i, cc_idx] for s in mfa_results.StockDict.values() if s.Name.startswith('dS_')
        )

        # KPI G: Mass Balance Saldo (Carbon)
        balance_error = total_carbon_input - total_carbon_output - net_stock_change

        # KPI J: Critical Deviation (%)
        critical_deviation = (balance_error / total_carbon_input * 100) if total_carbon_input != 0 else 0

        kpi_data.append({
            'Year': year,
            'Total Carbon Input (kt C/a)': total_carbon_input,
            'Total Carbon Output (kt C/a)': total_carbon_output,
            'Net Carbon Stock Change (kt C/a)': net_stock_change,
            'Mass Balance Error (kt C/a)': balance_error,
            'Critical Deviation (%)': critical_deviation
        })

    return pd.DataFrame(kpi_data)

def generate_kpi_dashboard(mfa_results, process_logic_map, output_path):
    """
    Calculates KPIs, displays a summary, and exports the full table to Excel.

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

    # Calculate Throughput KPIs
    try:
        cc_idx = mfa_results.Elements.index('CC')
        all_flows = np.array([f.Values[:, cc_idx] for f in mfa_results.FlowDict.values()])
        
        throughput_first_year = all_flows[:, 0].sum()
        throughput_last_year = all_flows[:, -1].sum()
        throughput_average = all_flows.mean(axis=1).sum()

    except ValueError:
        throughput_first_year, throughput_last_year, throughput_average = 0, 0, 0

    # --- Display Summary Dashboard ---
    print("\n" + "="*60)
    print("📊 KEY PERFORMANCE INDICATOR (KPI) DASHBOARD")
    print("="*60)
    
    first_year_kpis = kpi_df.iloc[0]
    last_year_kpis = kpi_df.iloc[-1]

    summary = {
        "Metric": ["Total Carbon Input", "Total Carbon Output", "Net Carbon Stock Change", "Mass Balance Error", "Critical Deviation"],
        "Unit": ["kt C/a", "kt C/a", "kt C/a", "kt C/a", "%"],
        f"First Year ({kpi_df['Year'].iloc[0]}) ": [
            f"{first_year_kpis['Total Carbon Input (kt C/a)']:.2f}",
            f"{first_year_kpis['Total Carbon Output (kt C/a)']:.2f}",
            f"{first_year_kpis['Net Carbon Stock Change (kt C/a)']:.2f}",
            f"{first_year_kpis['Mass Balance Error (kt C/a)']:.4f}",
            f"{first_year_kpis['Critical Deviation (%)']:.4f}"
        ],
        f"Last Year ({kpi_df['Year'].iloc[-1]}) ": [
            f"{last_year_kpis['Total Carbon Input (kt C/a)']:.2f}",
            f"{last_year_kpis['Total Carbon Output (kt C/a)']:.2f}",
            f"{last_year_kpis['Net Carbon Stock Change (kt C/a)']:.2f}",
            f"{last_year_kpis['Mass Balance Error (kt C/a)']:.4f}",
            f"{last_year_kpis['Critical Deviation (%)']:.4f}"
        ]
    }
    summary_df = pd.DataFrame(summary)
    print(summary_df.to_string(index=False))

    print("\n" + "-"*60)
    print("System Throughput (Carbon):")
    print(f"  - First Year: {throughput_first_year:.2f} kt C/a")
    print(f"  - Last Year:  {throughput_last_year:.2f} kt C/a")
    print(f"  - Average:    {throughput_average:.2f} kt C/a")
    print("-"*60)

    # --- Export to Excel ---
    try:
        output_dir = os.path.dirname(output_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        kpi_df.to_excel(output_path, index=False, sheet_name='System_KPIs_by_Year')
        print(f"\n✅ KPI data successfully exported to: {output_path}")
    except Exception as e:
        print(f"\n⚠️ Could not export KPI data: {e}")
