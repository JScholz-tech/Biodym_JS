"""
Debug script to investigate mass balance errors in dynamic TC processes.

This script helps diagnose whether mass balance errors are caused by:
1. TCs not summing to 100% (normalization issue)
2. Other solver/process configuration issues
3. Data quality problems

Usage:
    python debug_tc_balance.py --input your_file.xlsx --process_id 5
"""

import sys
import os
import numpy as np
import pandas as pd

# Add project paths
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(project_root, "02_src"))

# Add ODYM to path
odym_path = os.path.join(
    project_root, "06_framework", "ODYM-master_20241127", "odym", "modules"
)
if odym_path not in sys.path:
    sys.path.insert(0, odym_path)

import ODYM_Classes as msc
from data_loader import load_tc_parameters
from utils import safe_read_excel
import config as cfg


def debug_process_tcs(excel_path, process_id=None):
    """
    Debug transfer coefficients for a specific process.

    Parameters
    ----------
    excel_path : str
        Path to Excel input file
    process_id : int, optional
        Process ID to debug. If None, shows all processes with dynamic TCs.
    """
    print("=" * 80)
    print("DEBUG: Dynamic TC Mass Balance Analysis")
    print("=" * 80)

    # Load Excel data
    print(f"\n1. Loading Excel file: {excel_path}")
    all_excel_data = safe_read_excel(excel_path)

    # Load configuration
    print("\n2. Loading configuration...")
    configuration = cfg.load_configuration(all_excel_data)
    elements = configuration.Elements
    time_vector = configuration.IndexTable["Time"].Classification.Items

    print(f"   Elements: {elements}")
    print(f"   Time range: {time_vector[0]} - {time_vector[-1]} ({len(time_vector)} years)")

    # Load process definitions
    process_defs = all_excel_data.get("2_1_Definition_Processes")
    static_tc_defs = all_excel_data.get("2_2_static_TCs")
    dynamic_tc_defs = all_excel_data.get("2_3_dynamic_TCs")

    # Find processes with dynamic TCs
    print("\n3. Identifying processes with dynamic TCs...")
    dynamic_processes = []

    for _, row in process_defs.iterrows():
        pid = row.get("Process_ID")
        pname = row.get("Process_Name")
        tc_config = row.get("TC_Configuration")

        if pd.notna(pid) and tc_config == "Dynamic":
            dynamic_processes.append((int(pid), pname))
            print(f"   → Process {pid}: {pname} (Dynamic TCs)")

    if not dynamic_processes:
        print("   ⚠️  No processes with dynamic TCs found!")
        return

    # Filter to specific process if requested
    if process_id is not None:
        dynamic_processes = [(pid, pname) for pid, pname in dynamic_processes if pid == process_id]
        if not dynamic_processes:
            print(f"\n   ❌ ERROR: Process {process_id} not found or doesn't have dynamic TCs")
            return

    # Load TCs (with normalization)
    print("\n4. Loading TCs (normalization will run automatically)...")
    print("-" * 80)
    tc_params = load_tc_parameters(all_excel_data, elements, time_vector, debug_mode=True)
    print("-" * 80)

    # Analyze each process
    for pid, pname in dynamic_processes:
        print(f"\n{'='*80}")
        print(f"ANALYZING PROCESS {pid}: {pname}")
        print(f"{'='*80}")

        # Find TCs for this process
        process_tc_rows = static_tc_defs[static_tc_defs["Process_ID"] == pid]

        if process_tc_rows.empty:
            print(f"   ⚠️  No TC mappings found in 2_2_static_TCs for process {pid}")
            continue

        # Check each element
        for elem_idx, element in enumerate(elements):
            print(f"\n--- Element: {element} ---")

            # Get TC IDs for this element
            element_id = elem_idx + 1
            tc_id_col = f"E{element_id}_TC_ID"

            if tc_id_col not in process_tc_rows.columns:
                tc_id_col = f"TC_{element}_ID"  # Try old format

            if tc_id_col not in process_tc_rows.columns:
                print(f"   ⚠️  No TC column found for element {element}")
                continue

            tc_names = process_tc_rows[tc_id_col].dropna().unique()

            if len(tc_names) == 0:
                print(f"   ℹ️  No TCs defined for element {element}")
                continue

            print(f"   TCs: {list(tc_names)}")

            # Get TC values
            tc_values = {}
            for tc_name in tc_names:
                if tc_name in tc_params:
                    tc_values[tc_name] = tc_params[tc_name].Values

            if not tc_values:
                print(f"   ⚠️  TCs not found in loaded parameters!")
                continue

            # Check if TCs sum to 100% at each time step
            print(f"\n   Checking TC sums over time...")

            # Calculate sum at each time step
            tc_sum_over_time = np.zeros(len(time_vector))
            for tc_name, tc_vals in tc_values.items():
                if isinstance(tc_vals, np.ndarray):
                    tc_sum_over_time += tc_vals
                else:
                    tc_sum_over_time += tc_vals

            # Check for deviations
            deviations = tc_sum_over_time - 1.0
            max_deviation = np.max(np.abs(deviations))

            print(f"   Sum range: {tc_sum_over_time.min():.6f} - {tc_sum_over_time.max():.6f}")
            print(f"   Max deviation from 1.0: {max_deviation:.6e}")

            if max_deviation > 1e-6:
                print(f"   ❌ ERROR: TCs do NOT sum to 100%!")
                print(f"   Years with largest deviations:")
                worst_indices = np.argsort(np.abs(deviations))[-5:]
                for idx in worst_indices[::-1]:
                    year = time_vector[idx]
                    sum_val = tc_sum_over_time[idx]
                    print(f"      Year {year}: Sum = {sum_val:.6f} (deviation: {deviations[idx]:+.6f})")
                    for tc_name, tc_vals in tc_values.items():
                        val = tc_vals[idx] if isinstance(tc_vals, np.ndarray) else tc_vals
                        print(f"         {tc_name} = {val:.6f}")
            else:
                print(f"   ✅ TCs sum to 100% (within tolerance)")

            # Show TC evolution over time (sample years)
            print(f"\n   TC values over time (sample years):")
            sample_years = [0, len(time_vector)//4, len(time_vector)//2,
                           3*len(time_vector)//4, len(time_vector)-1]

            for year_idx in sample_years:
                year = time_vector[year_idx]
                print(f"      Year {year}:")
                for tc_name, tc_vals in tc_values.items():
                    val = tc_vals[year_idx] if isinstance(tc_vals, np.ndarray) else tc_vals
                    print(f"         {tc_name} = {val:.4f} ({val*100:.2f}%)")
                print(f"         → Sum = {tc_sum_over_time[year_idx]:.6f}")

    print(f"\n{'='*80}")
    print("DEBUG COMPLETE")
    print(f"{'='*80}")


def check_mass_balance_from_results(mfa_system, process_id):
    """
    Check mass balance for a specific process from MFA results.

    Parameters
    ----------
    mfa_system : ODYM MFAsystem
        Solved MFA system
    process_id : int
        Process ID to check
    """
    print(f"\n{'='*80}")
    print(f"MASS BALANCE CHECK: Process {process_id}")
    print(f"{'='*80}")

    # Get inflows
    inflows = [f for f in mfa_system.FlowDict.values() if f.P_End == process_id]
    outflows = [f for f in mfa_system.FlowDict.values() if f.P_Start == process_id]

    # Get stock change if exists
    stock = mfa_system.StockDict.get(process_id)

    print(f"\nInflows ({len(inflows)}):")
    for f in inflows:
        print(f"   {f.Name}: {f.P_Start} → {f.P_End}")

    print(f"\nOutflows ({len(outflows)}):")
    for f in outflows:
        print(f"   {f.Name}: {f.P_Start} → {f.P_End}")

    if stock:
        print(f"\nStock: {stock.Name}")

    # Calculate mass balance
    elements = mfa_system.Elements
    time_steps = len(mfa_system.IndexTable["Time"].Classification.Items)

    for elem_idx, element in enumerate(elements):
        print(f"\n--- Element: {element} ---")

        total_inflow = np.zeros(time_steps)
        total_outflow = np.zeros(time_steps)
        stock_change = np.zeros(time_steps)

        # Sum inflows
        for f in inflows:
            if f.Values is not None and len(f.Values.shape) > 1:
                total_inflow += f.Values[:, elem_idx]

        # Sum outflows
        for f in outflows:
            if f.Values is not None and len(f.Values.shape) > 1:
                total_outflow += f.Values[:, elem_idx]

        # Get stock change
        if stock and stock.Values is not None:
            if len(stock.Values.shape) > 1:
                stock_vals = stock.Values[:, elem_idx]
                stock_change = np.diff(stock_vals, prepend=0)

        # Calculate balance error
        balance = total_inflow - total_outflow - stock_change
        max_error = np.max(np.abs(balance))

        print(f"   Max balance error: {max_error:.6e}")

        if max_error > 1e-6:
            print(f"   ❌ MASS BALANCE ERROR DETECTED!")
            worst_idx = np.argmax(np.abs(balance))
            print(f"   Worst year: {worst_idx}")
            print(f"      Inflow:  {total_inflow[worst_idx]:.6f}")
            print(f"      Outflow: {total_outflow[worst_idx]:.6f}")
            print(f"      Stock Δ: {stock_change[worst_idx]:.6f}")
            print(f"      Error:   {balance[worst_idx]:.6f}")
        else:
            print(f"   ✅ Mass balance OK")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Debug dynamic TC mass balance")
    parser.add_argument("--input", "-i", help="Path to Excel input file")
    parser.add_argument("--process_id", "-p", type=int, help="Process ID to debug")

    args = parser.parse_args()

    if args.input:
        debug_process_tcs(args.input, args.process_id)
    else:
        print("Please provide input file with --input")
        print("Example: python debug_tc_balance.py --input my_file.xlsx --process_id 5")
