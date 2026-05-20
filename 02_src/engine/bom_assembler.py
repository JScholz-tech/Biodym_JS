# -*- coding: utf-8 -*-
"""
BOM Assembler Process Logic for the BioDYM Engine.

A BOM_Assembler process models remanufacturing, repair, or assembly operations
where the output product must have a strictly defined mass composition (Bill of
Materials, BOM). Rather than splitting the inflow by fixed fractions, the process:

  1. Totals the available mass for each top-level element from all inflows.
  2. Finds the limiting element — the one that constrains maximum assembly volume
     given the BOM target fractions.
  3. Scales the primary product output to match the exact BOM.
  4. Routes all excess (non-assemblable) mass to a designated residue flow.

Mass balance is always maintained: total_inflow = primary_product + residue.

Excel configuration lives in sheet '3_4_Definition_BOM'. Each row defines one
BOM_Assembler process. The BOM fractions must be given for every top-level element
(elements whose parent is 'material' or who have no parent); sub-elements like DM/TC
within the hierarchy are recomputed automatically.

Configuration columns expected in '3_4_Definition_BOM':
    Process_ID          int  — matches the process ID in 2_1_Definition_Processes
    Primary_Flow_ID     str  — Flow_ID of the primary product output
    Residue_Flow_ID     str  — Flow_ID of the residue/waste output
    BOM_E{n}_Fraction   float — target mass fraction for element n (0–1 scale)
                                e.g. BOM_E1_Fraction for 'material' (always 1.0),
                                     BOM_E2_Fraction for 'WC', etc.

The BOM fractions for top-level elements must sum to 1.0.
"""

import numpy as np


def load_bom_parameters(excel_data, elements, debug_mode=False):
    """Reads BOM Assembler configurations from the '3_4_Definition_BOM' sheet.

    Parameters
    ----------
    excel_data : dict
        Dictionary of DataFrames keyed by sheet name.
    elements : list of str
        Ordered list of element names matching mfa_system.Elements.
    debug_mode : bool, optional
        If True, print detailed parsing information.

    Returns
    -------
    dict
        Keys are process IDs (int). Values are dicts with:
        - 'primary_flow_id'  : str
        - 'residue_flow_id'  : str
        - 'bom_fractions'    : np.ndarray, shape (n_elements,),
                               target mass fraction per element (0–1).
                               Index 0 (material) is implicitly 1.0.
        Returns {} if the sheet is missing or empty.
    """
    sheet_name = "3_4_Definition_BOM"
    if debug_mode:
        print(f"--> Loading BOM Assembler parameters from sheet '{sheet_name}'...")

    if sheet_name not in excel_data:
        if debug_mode:
            print(f"  -> Sheet '{sheet_name}' not found. No BOM Assembler processes.")
        return {}

    df = excel_data[sheet_name].dropna(subset=["Process_ID"])
    if df.empty:
        if debug_mode:
            print(f"  -> Sheet '{sheet_name}' is empty.")
        return {}

    bom_params = {}

    for _, row in df.iterrows():
        process_id = int(row["Process_ID"])
        primary_flow_id = str(row.get("Primary_Flow_ID", "")).strip()
        residue_flow_id = str(row.get("Residue_Flow_ID", "")).strip()

        if not primary_flow_id or not residue_flow_id:
            print(
                f"  -> WARNING: BOM process {process_id} missing Primary_Flow_ID or "
                f"Residue_Flow_ID — skipped."
            )
            continue

        # Read per-element BOM fractions using E{n}_Fraction column naming
        bom_fractions = np.zeros(len(elements))
        bom_fractions[0] = 1.0  # material fraction is always 1.0

        for elem_idx, element in enumerate(elements[1:], start=1):
            col = f"BOM_E{elem_idx + 1}_Fraction"
            if col in row and not _is_missing(row[col]):
                bom_fractions[elem_idx] = float(row[col])
            else:
                # Try legacy element-name column: BOM_WC_Fraction
                col_legacy = f"BOM_{element}_Fraction"
                if col_legacy in row and not _is_missing(row[col_legacy]):
                    bom_fractions[elem_idx] = float(row[col_legacy])

        bom_params[process_id] = {
            "primary_flow_id": primary_flow_id,
            "residue_flow_id": residue_flow_id,
            "bom_fractions": bom_fractions,
        }
        if debug_mode:
            print(
                f"  -> Process {process_id}: primary={primary_flow_id}, "
                f"residue={residue_flow_id}, BOM={bom_fractions}"
            )

    print(
        f"--> Loaded BOM Assembler parameters for {len(bom_params)} process(es)."
    )
    return bom_params


def _is_missing(val):
    """Return True if val is NaN, None, or empty string."""
    if val is None:
        return True
    try:
        import math
        return math.isnan(val)
    except (TypeError, ValueError):
        return str(val).strip() == ""


def calculate_bom_assembly(mfa_system, bom_processes, bom_params, element_hierarchy=None):
    """Calculates primary-product and residue flows for all BOM_Assembler processes.

    For each BOM_Assembler process this function:
      1. Sums all inflows to get total available mass per element per year.
      2. Identifies the limiting element and scales primary output to exact BOM.
      3. Routes excess mass to the residue flow.

    The calculation is element-hierarchy-aware: the material total (element 0) is
    derived as the sum of top-level elements, not set independently.

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        The MFA system object, modified in place.
    bom_processes : set
        Set of process IDs identified as BOM_Assembler.
    bom_params : dict
        Per-process configuration dicts as returned by load_bom_parameters().
    element_hierarchy : dict, optional
        Element hierarchy from mfa_system._element_hierarchy. Used to identify
        top-level elements for the limiting-factor comparison.

    Returns
    -------
    bool
        True if any flow values changed during this call, False otherwise.
    """
    if not bom_processes:
        return False

    something_changed = False
    elements = mfa_system.Elements
    n_elem = len(elements)
    elem_idx = {e: i for i, e in enumerate(elements)}

    # Identify top-level elements (direct children of 'material', excluding material itself)
    top_level_indices = _get_top_level_element_indices(elements, element_hierarchy)

    for process_id in bom_processes:
        if process_id not in bom_params:
            continue

        cfg = bom_params[process_id]
        primary_fid = cfg["primary_flow_id"]
        residue_fid = cfg["residue_flow_id"]
        bom_fractions = cfg["bom_fractions"]  # shape (n_elem,)

        # Validate that both flows exist
        if primary_fid not in mfa_system.FlowDict:
            print(f"  -> WARNING: Primary flow '{primary_fid}' not found for BOM process {process_id}")
            continue
        if residue_fid not in mfa_system.FlowDict:
            print(f"  -> WARNING: Residue flow '{residue_fid}' not found for BOM process {process_id}")
            continue

        # Sum all inflows to this process
        inflows = [f for f in mfa_system.FlowDict.values() if f.P_End == process_id]
        if not inflows:
            continue

        total_inflow = sum(f.Values for f in inflows)  # shape (n_time, n_elem)
        n_time = total_inflow.shape[0]

        old_primary = mfa_system.FlowDict[primary_fid].Values.copy()

        # --- Limiting-factor calculation ---
        # For each top-level element e with BOM fraction b_e > 0:
        #   max_assemblable[t] = available[t, e] / b_e
        # The actual product volume is min over all top-level elements.
        # Material total is sum of top-level assembled amounts.

        max_assemblable = np.full(n_time, np.inf)  # start with no constraint

        for tl_idx in top_level_indices:
            b = bom_fractions[tl_idx]
            if b <= 0:
                # This element contributes nothing to the BOM — its surplus is residue
                continue
            available = total_inflow[:, tl_idx]
            # Avoid division by zero: if b == 0 skip; already handled above
            max_assemblable = np.minimum(max_assemblable, available / b)

        # If no top-level element had a positive BOM fraction, nothing can be assembled
        if np.all(np.isinf(max_assemblable)):
            max_assemblable = np.zeros(n_time)

        # Clamp to [0, total_inflow_material] — can't assemble more than we have
        max_assemblable = np.clip(max_assemblable, 0.0, total_inflow[:, 0])

        # Build primary product vector
        primary_out = np.zeros_like(total_inflow)
        primary_out[:, 0] = max_assemblable  # material total set from top-level sum below
        for tl_idx in top_level_indices:
            primary_out[:, tl_idx] = max_assemblable * bom_fractions[tl_idx]

        # Recalculate material column as sum of top-level elements
        primary_out[:, 0] = sum(primary_out[:, i] for i in top_level_indices)

        # Sub-elements (DM, TC, etc.) are proportional to their parent in the BOM
        _propagate_sub_elements(primary_out, bom_fractions, elements, element_hierarchy)

        # Residue = everything that wasn't assembled
        residue_out = total_inflow - primary_out
        residue_out = np.maximum(residue_out, 0.0)  # numerical guard

        # Write to flows
        mfa_system.FlowDict[primary_fid].Values = primary_out
        mfa_system.FlowDict[residue_fid].Values = residue_out

        if not np.allclose(old_primary, primary_out):
            something_changed = True

    return something_changed


def _get_top_level_element_indices(elements, element_hierarchy):
    """Returns indices of top-level elements (direct children of 'material').

    If no hierarchy is provided, all non-material elements are top-level.

    Parameters
    ----------
    elements : list of str
    element_hierarchy : dict or None

    Returns
    -------
    list of int
    """
    if not element_hierarchy:
        # No hierarchy: all elements except material[0] are top-level
        return list(range(1, len(elements)))

    top_level = []
    for idx, elem in enumerate(elements[1:], start=1):
        # Find this element in the hierarchy by name
        parent = None
        for _eid, info in element_hierarchy.items():
            if info["name"] == elem:
                parent = info.get("parent")
                break
        # Top-level: parent is 'material' or absent
        if parent is None or parent == "material":
            top_level.append(idx)
    return top_level


def _propagate_sub_elements(out_vector, bom_fractions, elements, element_hierarchy):
    """Sets sub-element values in out_vector based on their parent's assembled mass.

    Sub-elements (e.g. DM within material, TC within DM) are assigned values
    proportional to their BOM fraction times their parent's assembled value.

    Parameters
    ----------
    out_vector : np.ndarray, shape (n_time, n_elem)
        Modified in place.
    bom_fractions : np.ndarray, shape (n_elem,)
    elements : list of str
    element_hierarchy : dict or None
    """
    if not element_hierarchy:
        return

    elem_idx = {e: i for i, e in enumerate(elements)}

    for _eid, info in element_hierarchy.items():
        elem = info["name"]
        parent = info.get("parent")
        if elem not in elem_idx or parent not in elem_idx:
            continue
        if parent == "material":
            continue  # already handled as top-level

        child_i = elem_idx[elem]
        parent_i = elem_idx[parent]
        b = bom_fractions[child_i]
        out_vector[:, child_i] = out_vector[:, parent_i] * b
