"""
Quick inline check for dynamic TC normalization.
Add this to your notebook after loading TCs but before solving.
"""

import numpy as np
import pandas as pd


def check_tc_normalization(tc_params, all_excel_data, elements, process_id=None):
    """
    Quick check if TCs are properly normalized.

    Parameters
    ----------
    tc_params : dict
        Dictionary of TC parameters (from load_tc_parameters)
    all_excel_data : dict
        Excel data dictionary
    elements : list
        List of element names
    process_id : int, optional
        Specific process to check. If None, checks all.

    Returns
    -------
    dict
        Results for each process-element combination
    """
    static_tc_defs = all_excel_data.get("2_2_static_TCs")
    if static_tc_defs is None:
        print("❌ No static TC definitions found")
        return {}

    results = {}

    # Get process IDs to check
    if process_id is not None:
        process_rows = static_tc_defs[static_tc_defs["Process_ID"] == process_id]
    else:
        process_rows = static_tc_defs

    process_ids = process_rows["Process_ID"].dropna().unique()

    print(f"Checking {len(process_ids)} processes...")

    for pid in process_ids:
        pid = int(pid)
        proc_rows = static_tc_defs[static_tc_defs["Process_ID"] == pid]

        for elem_idx, element in enumerate(elements):
            # Get TC column name
            tc_id_col = f"E{elem_idx + 1}_TC_ID"
            if tc_id_col not in proc_rows.columns:
                tc_id_col = f"TC_{element}_ID"

            if tc_id_col not in proc_rows.columns:
                continue

            # Get TC names for this process-element
            tc_names = proc_rows[tc_id_col].dropna().unique()

            if len(tc_names) <= 1:
                continue  # Only check multi-TC processes

            # Get TC values
            tc_values = {}
            is_dynamic = False
            for tc_name in tc_names:
                if tc_name in tc_params:
                    val = tc_params[tc_name].Values
                    tc_values[tc_name] = val
                    if isinstance(val, np.ndarray):
                        is_dynamic = True

            if not is_dynamic or not tc_values:
                continue

            # Calculate sum
            tc_sum = np.zeros_like(list(tc_values.values())[0])
            for tc_val in tc_values.values():
                if isinstance(tc_val, np.ndarray):
                    tc_sum += tc_val
                else:
                    tc_sum += tc_val

            # Check deviation
            max_dev = np.max(np.abs(tc_sum - 1.0))

            key = f"P{pid}_{element}"
            results[key] = {
                "process_id": pid,
                "element": element,
                "tc_names": list(tc_names),
                "max_deviation": max_dev,
                "sum_range": (tc_sum.min(), tc_sum.max()),
                "is_ok": max_dev < 1e-6,
            }

            # Print result
            status = "✅" if results[key]["is_ok"] else "❌"
            print(
                f"{status} Process {pid}, {element}: "
                f"Sum = {tc_sum.min():.6f}-{tc_sum.max():.6f}, "
                f"Max deviation = {max_dev:.6e}"
            )

            if not results[key]["is_ok"]:
                print(f"   TCs: {list(tc_names)}")
                print(f"   ⚠️  WARNING: TCs do NOT sum to 100%!")

    return results


def quick_process_check(mfa_system, process_id):
    """
    Quick check of a specific process after solving.

    Call this after running the solver to check if mass balance is OK.

    Parameters
    ----------
    mfa_system : ODYM MFAsystem
        Solved MFA system
    process_id : int
        Process ID to check
    """
    print(f"\n{'='*60}")
    print(f"Quick Check: Process {process_id}")
    print(f"{'='*60}")

    # Get process info
    process = mfa_system.ProcessDict.get(process_id)
    if process is None:
        print(f"❌ Process {process_id} not found")
        return

    print(f"Process: {process.Name}")

    # Get flows
    inflows = [f for f in mfa_system.FlowDict.values() if f.P_End == process_id]
    outflows = [f for f in mfa_system.FlowDict.values() if f.P_Start == process_id]

    print(f"\nInflows: {len(inflows)}")
    for f in inflows:
        print(f"  {f.Name} (from P{f.P_Start})")

    print(f"\nOutflows: {len(outflows)}")
    for f in outflows:
        print(f"  {f.Name} (to P{f.P_End})")

    # Calculate mass balance for material element
    if inflows and inflows[0].Values is not None:
        time_steps = len(inflows[0].Values)
        elements = mfa_system.Elements

        for elem_idx, element in enumerate(elements):
            total_in = sum(
                f.Values[:, elem_idx]
                for f in inflows
                if f.Values is not None and len(f.Values.shape) > 1
            )
            total_out = sum(
                f.Values[:, elem_idx]
                for f in outflows
                if f.Values is not None and len(f.Values.shape) > 1
            )

            # Check stock
            stock = mfa_system.StockDict.get(process_id)
            stock_change = np.zeros(time_steps)
            if stock and stock.Values is not None:
                if len(stock.Values.shape) > 1:
                    stock_vals = stock.Values[:, elem_idx]
                    stock_change = np.diff(stock_vals, prepend=0)

            balance = total_in - total_out - stock_change
            max_error = np.max(np.abs(balance))

            status = "✅" if max_error < 1e-6 else "❌"
            print(f"\n{status} {element}: Max error = {max_error:.6e}")

            if max_error > 1e-6:
                worst_idx = np.argmax(np.abs(balance))
                print(f"   Worst year: {worst_idx}")
                print(f"   In:  {total_in[worst_idx]:.6f}")
                print(f"   Out: {total_out[worst_idx]:.6f}")
                print(f"   ΔS:  {stock_change[worst_idx]:.6f}")
                print(f"   Err: {balance[worst_idx]:.6f}")

                # Check TC sum at this time step
                print(f"\n   Checking TCs at worst year...")
                for f in outflows:
                    if f.Values is not None:
                        flow_val = (
                            f.Values[worst_idx, elem_idx]
                            if len(f.Values.shape) > 1
                            else f.Values[worst_idx]
                        )
                        tc_val = flow_val / total_in[worst_idx] if total_in[worst_idx] > 0 else 0
                        print(f"   {f.Name}: {flow_val:.6f} (TC ≈ {tc_val:.4f})")

    print(f"{'='*60}\n")
