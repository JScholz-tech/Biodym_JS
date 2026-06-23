# -*- coding: utf-8 -*-
"""Validation summary display for loaded BioDYM MFA systems."""

import numpy as np


def display_system_summary(
    mfa_system,
    config_obj,
    elements: list,
    regions: list,
    start_year: int,
    end_year: int,
    dsm_params: dict,
    fomp_params: dict,
    lfg_params: dict,
) -> None:
    """Print a structured summary of loaded data counts and configuration flags."""
    num_processes = len(mfa_system.ProcessList)
    num_flows = len(mfa_system.FlowDict)
    num_stocks = len(mfa_system.StockDict)
    num_elements = len(elements)
    time_span = end_year - start_year + 1

    num_static_tcs = sum(
        1
        for p in mfa_system.ParameterDict.values()
        if "TC" in p.Name and np.isscalar(p.Values)
    )
    num_dynamic_tcs = sum(
        1
        for p in mfa_system.ParameterDict.values()
        if "TC" in p.Name and isinstance(p.Values, np.ndarray)
    )
    num_dsm_processes = len(dsm_params) if dsm_params else 0
    num_fomp_processes = len(fomp_params) if fomp_params else 0
    num_lfg_processes = len(lfg_params) if lfg_params else 0

    print("\n📊 Configuration & Scope")
    print(f"  ✅ Time range: {start_year}-{end_year} ({time_span} years)")
    print(f"  ✅ Elements: {num_elements} defined ({', '.join(elements)})")
    print(f"  ✅ Regions: {len(regions)} ({', '.join(regions)})")

    print("\n🏗️  System Structure")
    print(f"  ✅ Processes: {num_processes} loaded")
    print(f"  ✅ Flows: {num_flows} defined")
    print(f"  ✅ Stocks: {num_stocks} configured")

    print("\n⚙️  Parameters")
    print("  ✅ Transfer Coefficients:")
    print(f"     • Static TCs: {num_static_tcs}")
    print(f"     • Dynamic TCs: {num_dynamic_tcs}")
    if num_dsm_processes > 0:
        print(f"  ✅ DSM Processes: {num_dsm_processes} configured")
    else:
        print("  ⚠️  DSM Processes: None configured")
    if num_fomp_processes > 0:
        print(f"  ✅ FOMP Processes: {num_fomp_processes} configured")
    else:
        print("  ⚠️  FOMP Processes: None configured")
    if num_lfg_processes > 0:
        print(f"  ✅ LFG Processes: {num_lfg_processes} configured")
    else:
        print("     LFG Processes: None configured (optional)")

    warnings_found = []
    if num_dsm_processes == 0 and config_obj.RUN_DSM_CALCULATION:
        warnings_found.append("DSM calculation enabled but no processes configured")
    if num_fomp_processes == 0 and config_obj.RUN_FOMP_CALCULATION:
        warnings_found.append("FOMP calculation enabled but no processes configured")

    print("\n📍 Overall Status")
    if not warnings_found:
        print("  🟢 ALL SYSTEMS GO - No warnings detected")
        print("  ✅ All required data loaded successfully")
    else:
        print(f"  🟡 READY WITH {len(warnings_found)} WARNING(S)")
        for warning in warnings_found:
            print(f"     ⚠️  {warning}")
        print("  ✅ Analysis can proceed (warnings are non-critical)")

    print()
