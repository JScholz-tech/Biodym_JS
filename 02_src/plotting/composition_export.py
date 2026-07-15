# -*- coding: utf-8 -*-
"""
Functions for exporting flow composition data.
"""

import os

import pandas as pd

from engine.element_utils import build_element_children_map


def export_flow_composition(mfa_system_results, output_path):
    """
    Exports the composition of each flow to an Excel file.

    Element-agnostic: works with whatever elements the system tracks, not
    a fixed WC/DM/CC set. Elements with tracked children are exported as
    "Remaining X" (X minus the sum of its children), mirroring the
    hierarchy handling in ``plotting.composition.plot_flow_composition`` —
    this telescopes to exactly 100% of material regardless of how many
    hierarchy levels are tracked (bioDYM_mathematical_formulas.md §6.2),
    unlike summing every element flat (which double-counts parent/child
    pairs such as DM and TC).

    Parameters
    ----------
    mfa_system_results : odym.MFAsystem
        The solved MFA system object containing flow and stock results.
    output_path : str
        The path to the output Excel file.
    """
    flows = mfa_system_results.FlowDict
    years = mfa_system_results.IndexTable.Classification["Time"].Items
    elements = list(mfa_system_results.Elements)

    if "material" not in elements:
        raise ValueError(f"'material' element not found in system elements: {elements}")
    material_idx = elements.index("material")

    element_hierarchy = getattr(mfa_system_results, "_element_hierarchy", {})
    children_map = build_element_children_map(element_hierarchy, elements)

    # (column label, element name, child element names to subtract)
    columns = []
    for e in elements:
        if e == "material":
            continue
        children = children_map.get(e, [])
        label = f"Remaining {e}" if children else e
        columns.append((label, e, children))

    data = []
    for i, year in enumerate(years):
        for flow_name, flow in flows.items():
            values = flow.Values[i, :]
            total_mass = values[material_idx]

            row = {"Year": year, "Flow Name": flow_name, "Total Mass": total_mass}
            for label, elem, children in columns:
                mass = values[elements.index(elem)]
                for child in children:
                    mass -= values[elements.index(child)]
                row[f"{label} (Mass)"] = mass
                row[f"{label} (%)"] = mass / total_mass * 100 if total_mass > 0 else 0
            data.append(row)

    df = pd.DataFrame(data)

    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    df.to_excel(output_path, index=False, sheet_name="Flow Composition")
    print(f"\n--> Flow composition data successfully exported to {output_path}")
