# -*- coding: utf-8 -*-
"""
BOM Assembler Process Logic for the BioDYM Engine.

A BOM_Assembler process models remanufacturing, repair, or assembly operations
where the output product must have a strictly defined mass composition (Bill of
Materials). Rather than splitting the inflow by fixed fractions, the process:

  1. Totals the available mass for each element from all inflows.
  2. Reads the target BOM composition from ParameterDict (time-varying TCs).
  3. Converts parent-relative fractions to absolute (material-relative) fractions
     by cascading through the element hierarchy.
  4. Finds the limiting element — the one that constrains maximum assembly volume.
  5. Scales the target-product output to match the exact BOM.
  6. Routes all excess (non-assemblable) mass to designated residue flows.

Mass balance: total_inflow == target_product + residue  (always maintained).

Excel configuration: sheet '3_3_Definition_BOM_Assembly'
Multi-row layout — one row per output flow per process:

    Process_ID        int   — ID in 2_1_Definition_Processes
    Process_Name      str   — informational
    Process_Logic     str   — must be 'BOM_Assembler'
    TC_Configuration  str   — 'Dynamic' or 'No TC'
    Stock_Configuration str — typically 'No_Stock'
    Outflow_count     int   — total number of output flows for this process
    Output_Flow       str   — human-readable output flow name
    Output_flow_type  str   — 'target_Product' or 'Unused_Material'
    Flow_ID           str   — matches FlowDict key (e.g. 'F_04_05')
    Year              int   — start year (informational)
    E2_TC_ID … E{n}_TC_ID  — ParameterDict keys for BOM fractions (one per element)
                              Fractions are relative to the parent element
                              (same convention as the element hierarchy).
                              Only required on 'target_Product' rows.

BOM fraction semantics (relative-to-parent):
    E2_TC_ID value → fraction of MATERIAL that is element-2  (e.g. WC = 60%)
    E3_TC_ID value → fraction of MATERIAL that is element-3  (e.g. DM = 40%)
    E4_TC_ID value → fraction of element-3 (DM) that is element-4 (TC = 18%)

For 'No TC' processes (TC_Configuration == 'No TC'): no BOM fractions are
defined; all inflow passes directly to the target_Product flow with no
composition constraint (behaves as a pass-through / merger).
"""

import numpy as np


# ---------------------------------------------------------------------------
# Excel loader
# ---------------------------------------------------------------------------

SHEET_NAME = "3_3_Definition_BOM_Assembly"


def load_bom_parameters(excel_data, elements, debug_mode=False):
    """Reads BOM Assembler configurations from '3_3_Definition_BOM_Assembly'.

    Parameters
    ----------
    excel_data : dict
        Dictionary of DataFrames keyed by sheet name.
    elements : list of str
        Ordered element names matching mfa_system.Elements.
    debug_mode : bool, optional

    Returns
    -------
    dict
        Keys are process IDs (int). Values:
        {
          'target_flows': [{'flow_id': str, 'tc_ids': {element: tc_id_str}}, ...],
          'residue_flows': [str, ...],
          'tc_configuration': str,   # 'Dynamic' or 'No TC'
        }
        Returns {} if the sheet is missing or empty.
    """
    if debug_mode:
        print(f"--> Loading BOM Assembler parameters from '{SHEET_NAME}'...")

    if SHEET_NAME not in excel_data:
        if debug_mode:
            print(f"  -> Sheet '{SHEET_NAME}' not found. No BOM Assembler processes.")
        return {}

    df = excel_data[SHEET_NAME].dropna(subset=["Process_ID"])
    if df.empty:
        if debug_mode:
            print(f"  -> Sheet '{SHEET_NAME}' is empty.")
        return {}

    # Detect TC column formats: E{n}_TC_ID and E{n}_TC_Value[%]
    tc_col_map = _build_tc_column_map(df, elements, debug_mode)
    tc_val_col_map = _build_tc_value_column_map(df, elements)

    bom_params = {}

    for process_id, group in df.groupby(df["Process_ID"].astype(int)):
        process_id = int(process_id)
        tc_cfg = (
            str(group["TC_Configuration"].iloc[0]).strip()
            if "TC_Configuration" in group.columns
            else "No TC"
        )

        target_flows = []
        residue_flows = []

        for _, row in group.iterrows():
            flow_id = str(row.get("Flow_ID", "")).strip()
            if not flow_id:
                continue
            flow_type = str(row.get("Output_flow_type", "")).strip()

            if flow_type == "target_Product":
                tc_ids = {}
                tc_values = {}
                for elem, col in tc_col_map.items():
                    if col and col in row and not _is_nan(row[col]):
                        tc_ids[elem] = str(row[col]).strip()
                # Read inline values from E{n}_TC_Value[%] columns as fallback
                for elem, val_col in tc_val_col_map.items():
                    if val_col and val_col in row and not _is_nan(row[val_col]):
                        try:
                            tc_values[elem] = float(row[val_col])
                        except (TypeError, ValueError):
                            pass
                target_flows.append(
                    {"flow_id": flow_id, "tc_ids": tc_ids, "tc_values": tc_values}
                )
                if debug_mode:
                    print(
                        f"  -> Process {process_id}: target_Product flow '{flow_id}', tc_ids={tc_ids}, tc_values={tc_values}"
                    )

            elif flow_type == "Unused_Material":
                residue_flows.append(flow_id)
                if debug_mode:
                    print(
                        f"  -> Process {process_id}: Unused_Material flow '{flow_id}'"
                    )
            else:
                if debug_mode:
                    print(
                        f"  -> Process {process_id}: unknown Output_flow_type '{flow_type}' for '{flow_id}' — skipped"
                    )

        if not target_flows:
            print(
                f"  -> WARNING: BOM process {process_id} has no 'target_Product' flow — skipped."
            )
            continue

        bom_params[process_id] = {
            "target_flows": target_flows,
            "residue_flows": residue_flows,
            "tc_configuration": tc_cfg,
        }

    print(f"--> Loaded BOM Assembler configurations for {len(bom_params)} process(es).")
    return bom_params


def _build_tc_column_map(df, elements, debug_mode=False):
    """Returns {element_name: column_name} for TC_ID columns.

    Priority: <element>_TC_ID (named) over E{n}_TC_ID (legacy index).
    """
    cols = df.columns.tolist()
    col_map = {}
    for elem_idx, element in enumerate(elements):
        if element == "material":
            continue
        n = elem_idx + 1
        named = f"{element}_TC_ID"
        legacy = f"E{n}_TC_ID"
        if named in cols:
            col_map[element] = named
        elif legacy in cols:
            col_map[element] = legacy
        else:
            col_map[element] = None
    if debug_mode:
        print(f"  -> BOM TC column map: {col_map}")
    return col_map


def _build_tc_value_column_map(df, elements):
    """Returns {element_name: column_name} for TC_Value columns.

    Priority: <element>_Value[%] (named) over E{n}_TC_Value[%] (legacy index).
    """
    cols = df.columns.tolist()
    col_map = {}
    for elem_idx, element in enumerate(elements):
        if element == "material":
            continue
        n = elem_idx + 1
        named = f"{element}_Value[%]"
        legacy = f"E{n}_TC_Value[%]"
        col_map[element] = (
            named if named in cols else (legacy if legacy in cols else None)
        )
    return col_map


def _is_nan(val):
    if val is None:
        return True
    try:
        import math

        return math.isnan(float(val))
    except (TypeError, ValueError):
        return str(val).strip() in ("", "nan", "NaN", "None")


# ---------------------------------------------------------------------------
# Assembly calculation (called from solver every iteration)
# ---------------------------------------------------------------------------


def calculate_bom_assembly(
    mfa_system, bom_processes, bom_params, element_hierarchy=None
):
    """Calculates target-product and residue flows for all BOM_Assembler processes.

    For each BOM_Assembler process:
      1. Sum all inflows to get available mass per element.
      2. Read time-varying BOM fractions from ParameterDict (parent-relative).
      3. Convert to absolute fractions via hierarchy cascade.
      4. Find limiting element → scale primary output to exact BOM.
      5. Assign excess to residue flows.

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        Modified in place.
    bom_processes : set of int
        Process IDs registered as BOM_Assembler.
    bom_params : dict
        Per-process config as returned by load_bom_parameters().
    element_hierarchy : dict or None
        mfa_system._element_hierarchy.

    Returns
    -------
    bool
        True if any flow value changed.
    """
    if not bom_processes:
        return False

    something_changed = False
    elements = mfa_system.Elements
    n_elem = len(elements)
    n_time = len(mfa_system.IndexTable.Classification["Time"].Items)

    for process_id in bom_processes:
        if process_id not in bom_params:
            continue

        cfg = bom_params[process_id]
        target_flow_cfgs = cfg["target_flows"]
        residue_flow_ids = cfg["residue_flows"]
        tc_cfg = cfg.get("tc_configuration", "No TC")

        # --- Sum all inflows ---
        inflows = [f for f in mfa_system.FlowDict.values() if f.P_End == process_id]
        if not inflows:
            continue
        available = sum(f.Values for f in inflows)  # (n_time, n_elem)

        total_primary = np.zeros((n_time, n_elem))

        for target_cfg in target_flow_cfgs:
            fid = target_cfg["flow_id"]
            if fid not in mfa_system.FlowDict:
                print(
                    f"  -> WARNING: BOM target flow '{fid}' not in FlowDict for process {process_id}"
                )
                continue

            old_values = mfa_system.FlowDict[fid].Values.copy()

            if tc_cfg == "No TC" or (
                not target_cfg["tc_ids"] and not target_cfg.get("tc_values")
            ):
                # No composition constraint: target gets everything available
                primary = available.copy()
            else:
                bom_ts = _read_bom_fractions_ts(
                    target_cfg["tc_ids"],
                    elements,
                    mfa_system,
                    n_time,
                    n_elem,
                    tc_values=target_cfg.get("tc_values"),
                )
                abs_bom_ts = _compute_absolute_bom_fractions_ts(
                    bom_ts, elements, element_hierarchy
                )
                max_assemblable = _find_limiting_factor(
                    available, abs_bom_ts, n_time, n_elem
                )
                primary = _build_primary_vector(
                    max_assemblable, abs_bom_ts, n_time, n_elem
                )

            mfa_system.FlowDict[fid].Values = primary
            total_primary += primary

            if not np.allclose(old_values, primary):
                something_changed = True

        # --- Residue = inflow − all primary products ---
        residue = np.maximum(available - total_primary, 0.0)

        if residue_flow_ids:
            split = 1.0 / len(residue_flow_ids)
            for rfid in residue_flow_ids:
                if rfid not in mfa_system.FlowDict:
                    print(
                        f"  -> WARNING: BOM residue flow '{rfid}' not in FlowDict for process {process_id}"
                    )
                    continue
                old_r = mfa_system.FlowDict[rfid].Values.copy()
                mfa_system.FlowDict[rfid].Values = residue * split
                if not np.allclose(old_r, mfa_system.FlowDict[rfid].Values):
                    something_changed = True

    return something_changed


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _read_bom_fractions_ts(
    tc_ids, elements, mfa_system, n_time, n_elem, tc_values=None
):
    """Read per-element BOM fractions from ParameterDict, with inline-value fallback.

    Priority:
      1. ParameterDict[tc_id]  (time-varying, from static/dynamic TCs sheets)
      2. tc_values[elem]       (constant, read directly from BOM sheet value column)

    Returns (n_time, n_elem) array of parent-relative fractions.
    material (index 0) is always 1.0.
    """
    bom_ts = np.zeros((n_time, n_elem))
    bom_ts[:, 0] = 1.0
    tc_values = tc_values or {}

    for elem_idx, elem in enumerate(elements):
        if elem == "material":
            continue
        idx = elem_idx  # elements list is 0-indexed; material is index 0

        tc_id = tc_ids.get(elem)
        if tc_id and tc_id in mfa_system.ParameterDict:
            # Priority 1: ParameterDict lookup (time-varying)
            vals = mfa_system.ParameterDict[tc_id].Values
            if isinstance(vals, (int, float)):
                bom_ts[:, idx] = float(vals)
            else:
                arr = np.asarray(vals).reshape(-1)
                bom_ts[:, idx] = (
                    arr[:n_time]
                    if len(arr) >= n_time
                    else np.pad(arr, (0, n_time - len(arr)), constant_values=arr[-1])
                )
        elif elem in tc_values:
            # Priority 2: inline constant value from BOM sheet E{n}_TC_Value[%]
            bom_ts[:, idx] = float(tc_values[elem])

    return bom_ts


def _compute_absolute_bom_fractions_ts(bom_ts, elements, element_hierarchy):
    """Convert parent-relative BOM fractions to material-absolute fractions.

    Parameters
    ----------
    bom_ts : (n_time, n_elem) — fractions relative to parent element.
    elements : list of str
    element_hierarchy : dict or None

    Returns
    -------
    abs_bom_ts : (n_time, n_elem) — fraction of total MATERIAL mass.
    """
    n_time, n_elem = bom_ts.shape
    abs_bom = np.zeros_like(bom_ts)
    abs_bom[:, 0] = 1.0  # material

    if not element_hierarchy:
        # No hierarchy: all elements treated as top-level (direct % of material)
        abs_bom[:, 1:] = bom_ts[:, 1:]
        return abs_bom

    elem_idx = {e: i for i, e in enumerate(elements)}

    # Multiple passes to handle arbitrary hierarchy depth
    for _ in range(n_elem):
        for _eid, info in element_hierarchy.items():
            elem = info.get("name")
            parent = info.get("parent")
            if elem not in elem_idx or parent not in elem_idx:
                continue
            e_i = elem_idx[elem]
            p_i = elem_idx[parent]
            abs_bom[:, e_i] = abs_bom[:, p_i] * bom_ts[:, e_i]

    # Fallback: elements not covered by hierarchy use their bom_ts value directly
    for i in range(1, n_elem):
        mask = (abs_bom[:, i] == 0) & (bom_ts[:, i] > 0)
        abs_bom[mask, i] = bom_ts[mask, i]

    return abs_bom


def _find_limiting_factor(available, abs_bom_ts, n_time, n_elem):
    """Return max assemblable material per time step given available mass and BOM.

    Parameters
    ----------
    available : (n_time, n_elem)
    abs_bom_ts : (n_time, n_elem) — absolute fractions relative to material

    Returns
    -------
    max_assemblable : (n_time,)
    """
    max_assemblable = np.full(n_time, np.inf)

    for e in range(1, n_elem):  # skip material (index 0)
        bom_e = abs_bom_ts[:, e]
        avail_e = available[:, e]
        # Where BOM fraction > 0, compute how much material we could assemble
        mask = bom_e > 0
        ratio = np.where(mask, avail_e / np.where(mask, bom_e, 1.0), np.inf)
        max_assemblable = np.minimum(max_assemblable, ratio)

    # If no element had a positive BOM fraction, use available material directly
    all_inf = np.isinf(max_assemblable)
    max_assemblable = np.where(all_inf, available[:, 0], max_assemblable)

    # Clamp: cannot assemble more material than what arrived
    return np.clip(max_assemblable, 0.0, available[:, 0])


def _build_primary_vector(max_assemblable, abs_bom_ts, n_time, n_elem):
    """Compute primary product flow values.

    primary[t, 0]  = max_assemblable[t]               (material)
    primary[t, e]  = max_assemblable[t] × abs_bom[t, e]  (elements)
    """
    primary = max_assemblable[:, np.newaxis] * abs_bom_ts  # (n_time, n_elem)
    primary[:, 0] = max_assemblable  # material = total, not product of fraction
    return primary
