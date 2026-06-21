# -*- coding: utf-8 -*-
"""
KPI Dashboard Module for BioDYM MFA.

This module contains functions to calculate, display, and export key
performance indicators (KPIs) for the MFA system.
"""

import pandas as pd
import numpy as np
import os

from utils import safe_sheet_name


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
    years = mfa_results.IndexTable.Classification["Time"].Items
    elements = mfa_results.Elements

    # Boundary processes are labeled "Input" and/or "Output".
    # In many ODYM systems, the environment (process 0) is labeled "Input"
    # and serves as both source and sink — flows FROM it are system inputs,
    # flows TO it are system outputs.
    boundary_processes = {
        pid for pid, logic in process_logic_map.items()
        if logic in ("Input", "Output")
    }

    all_kpi_data = []

    for element_idx, element_name in enumerate(elements):
        kpi_data_per_element = []
        for i, year in enumerate(years):
            # Total Input (flows FROM boundary processes into the system)
            total_input = sum(
                f.Values[i, element_idx]
                for f in mfa_results.FlowDict.values()
                if f.P_Start in boundary_processes
            )

            # Total Output (flows TO boundary processes from the system)
            total_output = sum(
                f.Values[i, element_idx]
                for f in mfa_results.FlowDict.values()
                if f.P_End in boundary_processes
            )

            # Net Stock Change (exclude boundary process stocks to avoid
            # double-counting — their dS reflects input/output already measured)
            net_stock_change = sum(
                s.Values[i, element_idx]
                for s in mfa_results.StockDict.values()
                if s.Name.startswith("dS_")
                and int(s.Name.split("_")[1]) not in boundary_processes
            )

            # Mass Balance Error
            balance_error = total_input - total_output - net_stock_change

            # Critical Deviation (%)
            critical_deviation = (
                (balance_error / total_input * 100) if total_input != 0 else 0
            )

            kpi_data_per_element.append(
                {
                    "Year": year,
                    "Element": element_name,
                    "Total Input": total_input,
                    "Total Output": total_output,
                    "Net Stock Change": net_stock_change,
                    "Mass Balance Error": balance_error,
                    "Critical Deviation (%)": critical_deviation,
                }
            )
        all_kpi_data.extend(kpi_data_per_element)

    return pd.DataFrame(all_kpi_data)


def calculate_system_overview(mfa_results, process_logic_map, kpi_df):
    """
    Calculates system-wide overview KPIs including cumulative totals.

    Parameters
    ----------
    mfa_results : odym.MFAsystem
        The solved MFA system object.
    process_logic_map : dict
        A dictionary mapping Process_IDs to their logic.
    kpi_df : pd.DataFrame
        The detailed KPI dataframe from calculate_system_kpis.

    Returns
    -------
    pd.DataFrame
        System overview with cumulative and aggregate metrics.
    """
    years = mfa_results.IndexTable.Classification["Time"].Items
    elements = mfa_results.Elements
    unit = mfa_results.Unit or "Mg"

    overview_data = []

    for element_idx, element_name in enumerate(elements):
        element_kpis = kpi_df[kpi_df["Element"] == element_name]

        # Basic temporal metrics
        first_year = element_kpis.iloc[0]
        last_year = element_kpis.iloc[-1]

        # Cumulative totals over entire time period
        cumulative_input = element_kpis["Total Input"].sum()
        cumulative_output = element_kpis["Total Output"].sum()
        cumulative_stock_change = element_kpis["Net Stock Change"].sum()

        # Calculate throughput (sum of all flows over all years)
        all_flows = np.array(
            [f.Values[:, element_idx] for f in mfa_results.FlowDict.values()]
        )
        cumulative_throughput = all_flows.sum()  # Total material handled
        throughput_first = all_flows[:, 0].sum()
        throughput_last = all_flows[:, -1].sum()
        throughput_avg = all_flows.mean(axis=1).sum()
        throughput_peak = all_flows.sum(axis=0).max()
        throughput_peak_year = years[all_flows.sum(axis=0).argmax()]

        # Calculate stock metrics
        stock_keys = [k for k in mfa_results.StockDict.keys() if k.startswith("S_")]
        if stock_keys:
            all_stocks = np.array(
                [mfa_results.StockDict[k].Values[:, element_idx] for k in stock_keys]
            )
            total_stocks = all_stocks.sum(axis=0)

            current_stock = total_stocks[-1]
            peak_stock = total_stocks.max()
            peak_stock_year = years[total_stocks.argmax()]
            avg_stock = total_stocks.mean()

            # Residence time = Average Stock / Average Annual Throughput
            avg_annual_throughput = throughput_avg if throughput_avg > 0 else 1
            residence_time = avg_stock / avg_annual_throughput if avg_annual_throughput > 0 else 0
        else:
            current_stock = 0
            peak_stock = 0
            peak_stock_year = years[0]
            avg_stock = 0
            residence_time = 0

        # Growth rates
        input_growth = ((last_year["Total Input"] - first_year["Total Input"]) /
                       first_year["Total Input"] * 100) if first_year["Total Input"] > 0 else 0
        output_growth = ((last_year["Total Output"] - first_year["Total Output"]) /
                        first_year["Total Output"] * 100) if first_year["Total Output"] > 0 else 0
        throughput_growth = ((throughput_last - throughput_first) /
                            throughput_first * 100) if throughput_first > 0 else 0

        overview_data.append({
            "Element": element_name,
            "Metric_Category": "Cumulative_Totals",
            "Total_Material_Handled": cumulative_throughput,
            "Total_Input": cumulative_input,
            "Total_Output": cumulative_output,
            "Net_Stock_Accumulation": cumulative_stock_change,
            "Unit": unit,
        })

        overview_data.append({
            "Element": element_name,
            "Metric_Category": "Annual_Rates_First_Year",
            "Input_First": first_year["Total Input"],
            "Output_First": first_year["Total Output"],
            "Throughput_First": throughput_first,
            "Year": first_year["Year"],
            "Unit": f"{unit}/a",
        })

        overview_data.append({
            "Element": element_name,
            "Metric_Category": "Annual_Rates_Last_Year",
            "Input_Last": last_year["Total Input"],
            "Output_Last": last_year["Total Output"],
            "Throughput_Last": throughput_last,
            "Year": last_year["Year"],
            "Unit": f"{unit}/a",
        })

        overview_data.append({
            "Element": element_name,
            "Metric_Category": "Peak_Values",
            "Throughput_Peak": throughput_peak,
            "Throughput_Peak_Year": throughput_peak_year,
            "Stock_Peak": peak_stock,
            "Stock_Peak_Year": peak_stock_year,
            "Unit": f"{unit}/a",
        })

        overview_data.append({
            "Element": element_name,
            "Metric_Category": "Averages",
            "Throughput_Average": throughput_avg,
            "Stock_Average": avg_stock,
            "Residence_Time_Years": residence_time,
            "Unit": f"{unit}/a",
        })

        overview_data.append({
            "Element": element_name,
            "Metric_Category": "Growth_Rates",
            "Input_Growth_Percent": input_growth,
            "Output_Growth_Percent": output_growth,
            "Throughput_Growth_Percent": throughput_growth,
            "Unit": "%",
        })

        overview_data.append({
            "Element": element_name,
            "Metric_Category": "Current_Stock",
            "Stock_Level": current_stock,
            "Unit": unit,
        })

    return pd.DataFrame(overview_data)


def calculate_stock_analysis(mfa_results):
    """
    Calculates detailed stock analysis for each process and element.

    Returns
    -------
    pd.DataFrame
        Stock analysis with per-process metrics.
    """
    years = mfa_results.IndexTable.Classification["Time"].Items
    elements = mfa_results.Elements
    unit = mfa_results.Unit or "Mg"

    stock_data = []

    for stock_key in mfa_results.StockDict.keys():
        if not stock_key.startswith("S_"):
            continue

        process_id = int(stock_key.split("_")[1])
        process_name = next(
            (p.Name for p in mfa_results.ProcessList if p.ID == process_id),
            f"Process_{process_id}"
        )

        stock_obj = mfa_results.StockDict[stock_key]

        for element_idx, element_name in enumerate(elements):
            stock_ts = stock_obj.Values[:, element_idx]

            if stock_ts.max() < 1e-6:  # Skip if essentially zero
                continue

            initial_stock = stock_ts[0]
            final_stock = stock_ts[-1]
            peak_stock = stock_ts.max()
            peak_year = years[stock_ts.argmax()]
            avg_stock = stock_ts.mean()

            # Calculate average inflow for residence time
            inflows = [
                f.Values[:, element_idx]
                for f in mfa_results.FlowDict.values()
                if f.P_End == process_id
            ]
            avg_inflow = sum(inflows).mean() if inflows else 0
            residence_time = avg_stock / avg_inflow if avg_inflow > 1e-6 else 0

            stock_data.append({
                "Process_ID": process_id,
                "Process_Name": process_name,
                "Element": element_name,
                "Initial_Stock": initial_stock,
                "Final_Stock": final_stock,
                "Peak_Stock": peak_stock,
                "Peak_Year": peak_year,
                "Average_Stock": avg_stock,
                "Residence_Time_Years": residence_time,
                "Unit": unit,
            })

    return pd.DataFrame(stock_data)


def generate_kpi_dashboard(mfa_results, process_logic_map, output_path):
    """
    Calculates KPIs for all elements, displays a summary, and exports to Excel.

    Enhanced version with:
    - System overview with cumulative totals
    - Stock analysis by process
    - Multi-sheet Excel export
    - Improved console output

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

    unit = mfa_results.Unit or "Mg"

    print("\n" + "=" * 70)
    print("📊 BIODYM KPI DASHBOARD - COMPREHENSIVE SYSTEM OVERVIEW")
    print("=" * 70)

    # Calculate enhanced KPIs
    overview_df = calculate_system_overview(mfa_results, process_logic_map, kpi_df)
    stock_analysis_df = calculate_stock_analysis(mfa_results)

    # Display enhanced console output
    for element_name in mfa_results.Elements:
        element_kpis = kpi_df[kpi_df["Element"] == element_name]
        element_overview = overview_df[overview_df["Element"] == element_name]

        if element_kpis.empty:
            continue

        print(f"\n{'=' * 70}")
        print(f"🌍 ELEMENT: {element_name.upper()}")
        print(f"{'=' * 70}")

        # Cumulative Totals (THE KEY METRIC YOU REQUESTED!)
        cumulative_row = element_overview[element_overview["Metric_Category"] == "Cumulative_Totals"].iloc[0]
        print(f"\n📦 CUMULATIVE TOTALS (Entire Period: {element_kpis['Year'].iloc[0]}-{element_kpis['Year'].iloc[-1]})")
        print(f"  ┌─ Total Material Handled:    {cumulative_row['Total_Material_Handled']:>15,.0f} {unit}")
        print(f"  ├─ Total Input (from system): {cumulative_row['Total_Input']:>15,.0f} {unit}")
        print(f"  ├─ Total Output (to system):  {cumulative_row['Total_Output']:>15,.0f} {unit}")
        print(f"  └─ Net Stock Accumulation:    {cumulative_row['Net_Stock_Accumulation']:>15,.0f} {unit}")

        # Annual rates
        first_row = element_overview[element_overview["Metric_Category"] == "Annual_Rates_First_Year"].iloc[0]
        last_row = element_overview[element_overview["Metric_Category"] == "Annual_Rates_Last_Year"].iloc[0]
        print("\n📊 ANNUAL RATES")
        print(f"  First Year ({int(first_row['Year'])}):  Input={first_row['Input_First']:>10,.0f}  Output={first_row['Output_First']:>10,.0f}  Throughput={first_row['Throughput_First']:>10,.0f} {unit}/a")
        print(f"  Last Year  ({int(last_row['Year'])}):  Input={last_row['Input_Last']:>10,.0f}  Output={last_row['Output_Last']:>10,.0f}  Throughput={last_row['Throughput_Last']:>10,.0f} {unit}/a")

        # Peak values
        peak_row = element_overview[element_overview["Metric_Category"] == "Peak_Values"].iloc[0]
        print("\n📈 PEAK VALUES")
        print(f"  ┌─ Peak Throughput: {peak_row['Throughput_Peak']:>15,.0f} {unit}/a (Year {int(peak_row['Throughput_Peak_Year'])})")
        print(f"  └─ Peak Stock:      {peak_row['Stock_Peak']:>15,.0f} {unit}   (Year {int(peak_row['Stock_Peak_Year'])})")

        # Averages
        avg_row = element_overview[element_overview["Metric_Category"] == "Averages"].iloc[0]
        print("\n📉 AVERAGES")
        print(f"  ┌─ Average Annual Throughput: {avg_row['Throughput_Average']:>15,.0f} {unit}/a")
        print(f"  ├─ Average Stock Level:       {avg_row['Stock_Average']:>15,.0f} {unit}")
        print(f"  └─ Average Residence Time:    {avg_row['Residence_Time_Years']:>15,.1f} years")

        # Growth rates
        growth_row = element_overview[element_overview["Metric_Category"] == "Growth_Rates"].iloc[0]
        print("\n📈 GROWTH RATES (First → Last Year)")
        print(f"  ┌─ Input Growth:      {growth_row['Input_Growth_Percent']:>8,.1f}%")
        print(f"  ├─ Output Growth:     {growth_row['Output_Growth_Percent']:>8,.1f}%")
        print(f"  └─ Throughput Growth: {growth_row['Throughput_Growth_Percent']:>8,.1f}%")

        # Current stock
        current_row = element_overview[element_overview["Metric_Category"] == "Current_Stock"].iloc[0]
        print("\n📦 CURRENT STOCK (End of Period)")
        print(f"  └─ Total Stock: {current_row['Stock_Level']:>15,.0f} {unit}")

    # Display stock analysis summary
    if not stock_analysis_df.empty:
        print(f"\n{'=' * 70}")
        print("📦 STOCK ANALYSIS BY PROCESS")
        print(f"{'=' * 70}")
        for element_name in mfa_results.Elements:
            element_stocks = stock_analysis_df[stock_analysis_df["Element"] == element_name]
            if element_stocks.empty:
                continue
            print(f"\n🧪 Element: {element_name.upper()}")
            for _, row in element_stocks.iterrows():
                print(f"  Process: {row['Process_Name']}")
                print(f"    ├─ Initial:  {row['Initial_Stock']:>12,.0f} {unit}")
                print(f"    ├─ Final:    {row['Final_Stock']:>12,.0f} {unit}")
                print(f"    ├─ Peak:     {row['Peak_Stock']:>12,.0f} {unit} (Year {int(row['Peak_Year'])})")
                print(f"    ├─ Average:  {row['Average_Stock']:>12,.0f} {unit}")
                print(f"    └─ Res.Time: {row['Residence_Time_Years']:>12,.1f} years")

    # --- Export to Excel (Multi-sheet) ---
    try:
        output_dir = os.path.dirname(output_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Sheet 1: System Overview (NEW!)
            overview_df.to_excel(writer, sheet_name="System_Overview", index=False)

            # Sheet 2: Stock Analysis (NEW!)
            if not stock_analysis_df.empty:
                stock_analysis_df.to_excel(writer, sheet_name="Stock_Analysis", index=False)

            # Sheet 3: Timeseries - All Elements (original detailed data)
            kpi_df.to_excel(writer, sheet_name="Timeseries_All_Elements", index=False)

            # Sheet 4-7: Element-specific timeseries (NEW!)
            _used_kpi_sheets: set = set(writer.sheets)
            for element_name in mfa_results.Elements:
                element_data = kpi_df[kpi_df["Element"] == element_name].copy()
                if not element_data.empty:
                    sheet_name = safe_sheet_name(
                        f"Timeseries_{element_name}", _used_kpi_sheets
                    )
                    element_data.to_excel(writer, sheet_name=sheet_name, index=False)

        print(f"\n{'=' * 70}")
        print("✅ KPI DASHBOARD EXPORTED SUCCESSFULLY")
        print(f"{'=' * 70}")
        print(f"📁 Location: {output_path}")
        print("📊 Sheets created:")
        print("   1. System_Overview      - Cumulative totals & key metrics")
        print("   2. Stock_Analysis       - Per-process stock details")
        print("   3. Timeseries_All_Elements - Year-by-year all elements")
        for i, element_name in enumerate(mfa_results.Elements, start=4):
            print(f"   {i}. Timeseries_{element_name:<10} - Year-by-year {element_name}")
        print(f"{'=' * 70}")

    except Exception as e:
        print(f"\n⚠️ Could not export KPI data: {e}")
        import traceback
        traceback.print_exc()
