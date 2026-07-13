# -*- coding: utf-8 -*-
"""
Flow Composition Plotting and Validation Module for BioDYM.

This module provides publication-quality flow composition visualizations with:
- Element-agnostic composition analysis (works with any element set)
- 100% composition validation (detects over/under-allocation)
- Element hierarchy support (e.g., CC as % of DM)
- Standardized styling and export functionality

Author: BioDYM Development Team
Date: 2025-11-04
"""

import numpy as np
import plotly.graph_objects as go
from ipywidgets import IntSlider, Button, HBox, Layout, HTML
from IPython.display import display
from typing import Optional, Dict, List, Tuple

from .themes import (
    get_publication_layout,
    BIOYM_COLORS,
)
from .dynamic_colors import ElementColorManager
from .export_publication import export_figure
from engine.element_utils import (
    validate_element_hierarchy,
    build_element_children_map,
)

# Border color used to flag a "Remaining X" bar segment where children
# exceed their parent (ρ_f^e(t) < -tolerance, §2.6) — distinct from the
# BIOYM_COLORS palette since that has no dedicated warning/danger color.
_HIERARCHY_VIOLATION_COLOR = "#D62728"


def _summarize_pct_entries(entries):
    """Reduces a list of (flow_label, year, pct) to (count, min_pct, max_pct).

    Used to present "children vs. parent" percentages as one grouped range
    instead of one line per flow/year — see bioDYM_mathematical_formulas.md
    §2.6. Returns (0, None, None) for an empty list.
    """
    if not entries:
        return 0, None, None
    pcts = [p for _f, _y, p in entries]
    return len(entries), min(pcts), max(pcts)


def plot_flow_composition(
    mfa_system_results,
    color_manager: Optional[ElementColorManager] = None,
    enable_export: bool = True,
    show_validation_warnings: bool = True,
    composition_tolerance: float = 1.0,
):
    """
    Creates an interactive stacked bar chart to visualize flow composition with validation.

    This function displays the elemental composition of each flow as percentages,
    showing how the total mass is distributed among different elements. It includes
    automatic validation to detect composition errors (sum ≠ 100%) and supports
    any element configuration.

    Parameters
    ----------
    mfa_system_results : odym.MFAsystem
        The solved MFA system object containing flow and stock results.
    color_manager : ElementColorManager, optional
        Dynamic color manager for element colors. If None, creates one from
        mfa_system_results.Elements. Defaults to None.
    enable_export : bool, optional
        If True, adds an export button for saving publication-quality figures.
        Defaults to True.
    show_validation_warnings : bool, optional
        If True, displays warnings when composition sum deviates from 100%.
        Defaults to True.
    composition_tolerance : float, optional
        Tolerance for composition validation (%). Compositions outside
        100% ± tolerance will trigger warnings. Defaults to 1.0 (i.e., 99%-101%).

    Returns
    -------
    go.Figure
        Plotly figure object for the composition plot.

    Notes
    -----
    The plot shows composition as stacked horizontal bars where each element
    is represented by a distinct color. A time slider allows exploration across
    years.

    **Hierarchical Elements:** Elements with children display their "Remaining" portion
    to show hierarchy while avoiding double-counting. For example, if CC is defined
    as 45% of DM, the plot shows:
    - WC (water content, % of material)
    - Remaining DM (DM minus CC, % of material) - shown in lighter shade
    - CC (carbon content, % of material)

    This ensures WC + Remaining_DM + CC = 100% of material, providing complete visibility
    of both hierarchy levels while maintaining accurate composition validation.

    **Validation (see bioDYM_mathematical_formulas.md §2.6):** every branching
    node of the element hierarchy is validated independently via
    ``engine.element_utils.validate_element_hierarchy()`` — not only the
    top-level "sum to 100% of material" check. A "Remaining X" segment gets a
    red border for any flow/year where X's children exceed X
    (ρ_f^X(t) < -tolerance); the warnings panel lists every such node
    violation for the selected year. Children under-accounting for their
    parent are reported informationally, not as errors (a genuine untracked
    remainder is expected — see §2.2's "undefined elements default to 0"
    note), matching how "material" itself was always treated.

    Examples
    --------
    >>> # Basic usage
    >>> fig = plot_flow_composition(mfa_results)

    >>> # With color-blind friendly colors
    >>> color_mgr = ElementColorManager(elements, color_scheme='colorblind')
    >>> fig = plot_flow_composition(mfa_results, color_manager=color_mgr)

    >>> # Disable validation warnings
    >>> fig = plot_flow_composition(mfa_results, show_validation_warnings=False)

    >>> # Stricter validation tolerance
    >>> fig = plot_flow_composition(mfa_results, composition_tolerance=0.5)

    >>> # Example composition with hierarchy:
    >>> # Material: 1000 Mg, WC: 15%, DM: 85%, CC: 45% of DM
    >>> # Display shows:
    >>> #   WC: 15% (150 Mg)
    >>> #   Remaining DM: 46.75% (467.5 Mg = 850 - 382.5)
    >>> #   CC: 38.25% (382.5 Mg)
    >>> #   Total: 100% ✓
    """
    flows = mfa_system_results.FlowDict
    years = mfa_system_results.IndexTable.Classification["Time"].Items
    element_items = [e.lower() for e in mfa_system_results.Elements]

    # Get flow descriptions for display (use descriptive names instead of IDs)
    flow_descriptions = getattr(mfa_system_results, "_flow_descriptions", {})

    # Create color manager if not provided
    if color_manager is None:
        color_manager = ElementColorManager(element_items)

    # Get element hierarchy info if available
    # NOTE: _element_hierarchy is a BioDYM extension (stored by system_setup.py)
    element_hierarchy = getattr(mfa_system_results, "_element_hierarchy", {})

    # Build composition structure respecting hierarchy
    # Strategy: Show "Remaining X" for elements with children, plus all leaf elements
    # Example: material -> WC, DM -> Remaining_DM, CC
    # This ensures: WC + Remaining_DM + CC = 100% of material

    # Identify which elements have children
    # element_hierarchy structure: {element_id: {'name': str, 'parent': str or None}}
    elements_with_children = set()
    leaf_elements = []

    for e in element_items:
        if e == "material":
            continue

        # Check if this element has children (any element whose parent is this element)
        has_children = False
        if element_hierarchy:
            for elem_id, elem_info in element_hierarchy.items():
                # Compare parent name (case-insensitive)
                parent_name = (
                    elem_info.get("parent", "").lower()
                    if elem_info.get("parent")
                    else None
                )
                if parent_name == e.lower():
                    has_children = True
                    break

        if has_children:
            elements_with_children.add(e)
        else:
            leaf_elements.append(e)

    # Build display elements list (order matters for stacking)
    # Include "Remaining X" for parents and all leaf elements
    composable_elements = []
    element_display_names = {}  # Map internal name -> display name

    for e in element_items:
        if e == "material":
            continue

        if e in elements_with_children:
            # Add "Remaining X" entry
            remaining_key = f"remaining_{e}"
            composable_elements.append(remaining_key)
            element_display_names[remaining_key] = f"Remaining {e.upper()}"

        if e in leaf_elements:
            # Add leaf element as-is
            composable_elements.append(e)
            element_display_names[e] = e.upper()

    # Create figure widget
    fig = go.FigureWidget()
    validation_output = HTML()

    # Apply initial layout once (to prevent shrinking on updates)
    initial_layout = get_publication_layout(
        size="large",
        show_grid=True,
        custom_title="bioDYM - Flow Composition",
        x_title="Composition (%)",
        y_title="Flows",
    )

    # Customize for composition plot
    initial_layout["barmode"] = "stack"
    initial_layout["xaxis"]["range"] = [0, 105]  # Slightly over 100% to show errors
    initial_layout["legend"] = {
        "title": {"text": "Element", "font": {"size": 12}},
        "font": {"size": 10},
        "bgcolor": "rgba(255,255,255,0.9)",
        "bordercolor": BIOYM_COLORS["neutral"],
        "borderwidth": 1,
        "orientation": "h",
        "yanchor": "bottom",
        "y": 1.1,
        "xanchor": "right",
        "x": 1,
    }

    # Increase top margin to prevent legend from overlapping with 100% line
    if "margin" not in initial_layout:
        initial_layout["margin"] = {}
    initial_layout["margin"]["t"] = initial_layout["margin"].get("t", 100) + 40

    # Apply initial layout to figure
    fig.update_layout(initial_layout)

    # Per-node composition validation (§2.6), computed once for all
    # flows/years — not recomputed on every slider tick. Every branching
    # node of the element hierarchy is checked independently (not only
    # "material"), which is what the old aggregate "sum to 100%" check
    # could never do (see the docstring Notes above and §2.6 for the proof).
    all_violations = (
        validate_element_hierarchy(mfa_system_results, tolerance=composition_tolerance)
        if show_validation_warnings
        else {}
    )

    def update_plot(year):
        year_index = list(years).index(year)

        flow_names = []
        element_percentages = {elem: [] for elem in composable_elements}

        for flow_id, flow in flows.items():
            values = flow.Values[year_index, :]

            # Get material (total mass) - always at index 0
            material_idx = element_items.index("material")
            total_mass = values[material_idx]

            if total_mass > 1e-10:  # Only include flows with mass
                # Use descriptive name if available, otherwise use Flow ID
                display_name = flow_descriptions.get(flow_id, flow_id)
                flow_names.append(display_name)

                # Calculate percentages for each composable element
                for display_elem in composable_elements:
                    if display_elem.startswith("remaining_"):
                        # This is a "Remaining X" element
                        parent_elem = display_elem.replace("remaining_", "")
                        parent_idx = element_items.index(parent_elem)
                        parent_val = values[parent_idx]

                        # Subtract all children values from parent
                        children_sum = 0
                        if element_hierarchy:
                            for elem_id, elem_info in element_hierarchy.items():
                                # Check if this element's parent is the current parent_elem
                                elem_parent = (
                                    elem_info.get("parent", "").lower()
                                    if elem_info.get("parent")
                                    else None
                                )
                                if elem_parent == parent_elem.lower():
                                    # This is a child element - subtract its value
                                    child_name = elem_info["name"].lower()
                                    if child_name in element_items:
                                        child_idx = element_items.index(child_name)
                                        children_sum += values[child_idx]

                        # Remaining = parent - sum(children)
                        remaining_val = parent_val - children_sum
                        percentage = (
                            (remaining_val / total_mass * 100) if total_mass > 0 else 0
                        )

                    else:
                        # Regular element (leaf or no hierarchy)
                        elem_idx = element_items.index(display_elem)
                        elem_val = values[elem_idx]
                        percentage = (
                            (elem_val / total_mass * 100) if total_mass > 0 else 0
                        )

                    element_percentages[display_elem].append(percentage)

        # Composition validation for the selected year: query the
        # precomputed per-node violations (§2.6) rather than recomputing
        # an aggregate that could never detect anything below "material".
        # Two different things are being checked here, kept visually and
        # textually separate so they can't be mistaken for one another:
        #   - "over" (children exceed parent) is a real hierarchy-consistency
        #     bug — listed individually so the offending flow is easy to find.
        #   - "under" (children fall short of parent) is expected whenever
        #     only some of an element's children are tracked (§2.2) — grouped
        #     into one count + range per node instead of one line per flow,
        #     so it reads as "for your information", not as a wall of errors.
        flagged_flows_by_node: Dict[str, set] = {}
        error_lines = []
        info_lines = []
        for node, kinds in all_violations.items():
            node_lower = node.lower()
            for flow_label, viol_year, pct in kinds.get("over", []):
                if viol_year == year:
                    flagged_flows_by_node.setdefault(node_lower, set()).add(flow_label)
                    error_lines.append(
                        f"{flow_label}: node '{node}' — children sum to "
                        f"{pct:.1f}% of parent (EXCEEDS 100%, likely a data error)"
                    )
            under_this_year = [
                (f, y, p) for f, y, p in kinds.get("under", []) if y == year
            ]
            n_under, min_pct, max_pct = _summarize_pct_entries(under_this_year)
            if n_under:
                pct_range = (
                    f"{min_pct:.0f}%" if min_pct == max_pct
                    else f"{min_pct:.0f}%–{max_pct:.0f}%"
                )
                info_lines.append(
                    f"node '{node}': {n_under} flow(s) have an untracked "
                    f"remainder (children = {pct_range} of parent)"
                )

        # Update figure
        with fig.batch_update():
            fig.data = []  # Clear previous data

            # Add trace for each element
            for display_elem in composable_elements:
                # Get appropriate color
                if display_elem.startswith("remaining_"):
                    # Use parent element color but lighter/muted
                    parent_elem = display_elem.replace("remaining_", "")
                    base_color = color_manager.get_element_color(parent_elem)
                    # Make it lighter by converting to RGB and adjusting

                    hex_color = base_color.lstrip("#")
                    r, g, b = tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
                    # Lighten by blending with white (increase RGB values)
                    r = int(r + (255 - r) * 0.4)
                    g = int(g + (255 - g) * 0.4)
                    b = int(b + (255 - b) * 0.4)
                    element_color = f"#{r:02x}{g:02x}{b:02x}"
                else:
                    element_color = color_manager.get_element_color(display_elem)

                display_name = element_display_names.get(
                    display_elem, display_elem.upper()
                )

                # Flag individual bar segments where this node's children
                # exceed it (ρ_f^e(t) < -tolerance, §2.6) with a red border,
                # instead of only reporting it in the text warnings panel.
                if display_elem.startswith("remaining_"):
                    flagged_flows = flagged_flows_by_node.get(parent_elem, set())
                    border_color = [
                        _HIERARCHY_VIOLATION_COLOR
                        if fn in flagged_flows
                        else BIOYM_COLORS["dark"]
                        for fn in flow_names
                    ]
                    border_width = [
                        2.5 if fn in flagged_flows else 0.5 for fn in flow_names
                    ]
                else:
                    border_color = BIOYM_COLORS["dark"]
                    border_width = 0.5

                fig.add_trace(
                    go.Bar(
                        y=flow_names,
                        x=element_percentages[display_elem],
                        name=display_name,
                        orientation="h",
                        marker=dict(
                            color=element_color,
                            line=dict(color=border_color, width=border_width),
                        ),
                        hovertemplate=f"<b>%{{y}}</b><br>{display_name}: %{{x:.1f}}%<extra></extra>",
                    )
                )

            # Only update dynamic elements (NOT height/width to prevent shrinking)
            # Update title, shapes, and annotations only
            fig.update_layout(
                title={
                    "text": f"bioDYM - Flow Composition ({year})",
                    "x": 0.5,
                    "xanchor": "center",
                },
                shapes=[
                    dict(
                        type="line",
                        x0=100,
                        x1=100,
                        y0=-0.5,
                        y1=len(flow_names) - 0.5,
                        line=dict(color=BIOYM_COLORS["dark"], width=2, dash="dash"),
                    )
                ],
                annotations=[
                    dict(
                        x=100,
                        y=1.05,
                        xref="x",
                        yref="paper",
                        text="100%",
                        showarrow=False,
                        font=dict(size=14, color=BIOYM_COLORS["dark"]),
                    )
                ],
            )

        # Update validation display — two visually distinct panels so a
        # real problem (error_lines) can never be mistaken for the merely
        # informational, and expected, partial sub-elements (info_lines).
        panels = ""
        if show_validation_warnings and error_lines:
            panels += (
                "<div style='background-color:#fdecea; border:1px solid #D62728; "
                "border-radius:4px; padding:10px; margin:10px 0'>"
                f"<strong>⚠️ Composition errors — Year {year} "
                "(a sub-element exceeds its parent's mass; likely a data error):</strong><br>"
                + "".join(f"• {line}<br>" for line in error_lines)
                + f"<em>Tolerance: ±{composition_tolerance}%</em></div>"
            )
        if show_validation_warnings and info_lines:
            panels += (
                "<div style='background-color:#f1f3f5; border:1px solid #ced4da; "
                "border-radius:4px; padding:10px; margin:10px 0; color:#495057'>"
                f"<strong>ℹ️ Untracked remainder — Year {year} "
                "(only some children are tracked for these elements; not an error):</strong><br>"
                + "".join(f"• {line}<br>" for line in info_lines)
                + "</div>"
            )
        validation_output.value = panels

    def export_current_plot(btn):
        """Export current plot configuration."""
        year = year_slider.value
        update_plot(year)  # Ensure plot is current

        filename = f"flow_composition_{year}"
        try:
            paths = export_figure(
                fig,
                filename,
                formats=["png", "pdf"],
                quality="publication",
                size="large",
            )
            print(f"✅ Exported: {', '.join(paths)}")
        except Exception as e:
            print(f"❌ Export failed: {e}")

    # Create widgets
    year_slider = IntSlider(
        min=years[0],
        max=years[-1],
        step=1,
        value=years[0],
        description="Year:",
        style={"description_width": "60px"},
        layout=Layout(width="400px"),
    )

    # Create control panel
    controls = [year_slider]

    if enable_export:
        export_btn = Button(
            description="📥 Export Figure",
            button_style="success",
            tooltip="Export current view to PNG and PDF",
            layout=Layout(width="150px"),
        )
        export_btn.on_click(export_current_plot)
        controls.append(export_btn)

    control_box = HBox(controls, layout=Layout(margin="10px 0"))

    # Set up interaction manually to avoid double widget display
    from ipywidgets import interactive_output

    interactive_output(update_plot, {"year": year_slider})

    # Display
    display(control_box)
    if show_validation_warnings:
        display(validation_output)
    display(fig)

    # Initial plot
    update_plot(year_slider.value)


def validate_flow_compositions(
    mfa_system_results, tolerance: float = 1.0, verbose: bool = True
) -> Dict[str, List[Tuple[str, int, float]]]:
    """
    Validate all flow compositions across all years.

    Thin wrapper around ``engine.element_utils.validate_element_hierarchy()``
    (see bioDYM_mathematical_formulas.md §2.6). The returned ``over_100`` /
    ``under_100`` lists are the "material" node's slice — numerically
    identical to what this function always computed, since summing every
    "Remaining X" segment telescopes exactly to the top-level
    Σ_{e∈E_top} F_f^e(t) regardless of deeper-node correctness (§2.6). That
    telescoping is also why this function's aggregate check could never
    detect a violation below the top level (e.g. TOC+TIC exceeding TC): the
    verbose report below now surfaces those separately, since they are
    invisible to the over_100/under_100 return value by construction.

    Parameters
    ----------
    mfa_system_results : odym.MFAsystem
        The solved MFA system object.
    tolerance : float, optional
        Tolerance for validation (%). Defaults to 1.0.
    verbose : bool, optional
        If True, prints detailed validation report. Defaults to True.

    Returns
    -------
    Dict[str, List[Tuple[str, int, float]]]
        Dictionary with 'over_100' and 'under_100' keys (top-level /
        "material" node only, for backward compatibility), plus
        'valid_count'. Use ``validate_element_hierarchy()`` directly for
        violations at every node.

    Examples
    --------
    >>> # Validate compositions
    >>> issues = validate_flow_compositions(mfa_results, tolerance=1.0)
    >>> if issues['over_100']:
    ...     print("Flows exceeding 100%:", issues['over_100'])
    """
    all_violations = validate_element_hierarchy(mfa_system_results, tolerance=tolerance)
    material_violations = all_violations.get("material", {"over": [], "under": []})
    over_100 = [(f, y, p) for f, y, p in material_violations.get("over", [])]
    under_100 = [(f, y, p) for f, y, p in material_violations.get("under", [])]

    # valid_count = flow-year combinations with material mass, minus those
    # already counted as a top-level over/under violation.
    material_idx = list(mfa_system_results.Elements).index("material")
    total_checked = sum(
        int(np.sum(np.abs(flow.Values[:, material_idx]) > 1e-10))
        for flow in mfa_system_results.FlowDict.values()
    )
    valid_count = total_checked - len(over_100) - len(under_100)

    deeper_violations = {
        node: kinds for node, kinds in all_violations.items() if node != "material"
    }

    # Print report. Two things are checked, printed as two clearly labelled
    # steps, and within each step the two possible outcomes are never mixed:
    #   - "exceeds" (a sub-element's children add up to MORE than the
    #     sub-element itself) is always a real data error — listed
    #     individually (capped) so the offending flow can be found.
    #   - "below" (children add up to LESS) is expected whenever only some
    #     of an element's children are tracked (§2.2) — grouped into one
    #     count + percentage range per relationship, not one line per flow,
    #     so it reads as an FYI rather than a wall of warnings.
    if verbose:
        print("=" * 80)
        print("FLOW COMPOSITION VALIDATION REPORT")
        print("=" * 80)
        print(f"Tolerance: ±{tolerance}%\n")

        print(f"STEP 1 — Top level: does every top-level element (e.g. WC, DM)")
        print(f"add up to material? [{total_checked} flow-year combinations checked]")
        if not over_100 and not under_100:
            print(f"  ✅ {valid_count}/{total_checked} match. No errors.")
        else:
            print(f"  ✅ {valid_count}/{total_checked} match.")
            if over_100:
                print(f"  ⚠️  {len(over_100)} EXCEED 100% (real error — top-level "
                      f"elements over-account for material):")
                for flow_name, year, pct in sorted(
                    over_100, key=lambda x: x[2], reverse=True
                )[:10]:
                    print(f"       {flow_name:40s} | Year {year} | {pct:6.2f}%")
                if len(over_100) > 10:
                    print(f"       ... and {len(over_100) - 10} more")
            if under_100:
                n, lo, hi = _summarize_pct_entries(under_100)
                rng = f"{lo:.0f}%" if lo == hi else f"{lo:.0f}%–{hi:.0f}%"
                print(f"  ℹ️  {n} below 100% (top-level elements = {rng} of "
                      f"material — untracked remainder, not an error)")

        print(f"\nSTEP 2 — Sub-elements: for every element with tracked children, "
              f"does the sum\nof its children match its own mass? "
              f"(e.g. does TOC + TIC add up to TC?)")
        if not deeper_violations:
            print("  ✅ No sub-element relationships found any issues.")
        else:
            for node, kinds in deeper_violations.items():
                over = kinds.get("over", [])
                under = kinds.get("under", [])
                print(f"\n  {node}:")
                if over:
                    print(f"    ⚠️  {len(over)} EXCEED 100% of {node} "
                          f"(real error — likely a data entry mistake):")
                    for flow_name, year, pct in sorted(
                        over, key=lambda x: x[2], reverse=True
                    )[:10]:
                        print(f"         {flow_name:30s} | Year {year} | "
                              f"{pct:6.2f}% of {node}")
                    if len(over) > 10:
                        print(f"         ... and {len(over) - 10} more")
                if under:
                    n, lo, hi = _summarize_pct_entries(under)
                    rng = f"{lo:.0f}%" if lo == hi else f"{lo:.0f}%–{hi:.0f}%"
                    print(f"    ℹ️  {n} flow(s): children = {rng} of {node} "
                          f"(untracked remainder — informational, not an error)")

        # Overall headline: only "exceeds" cases are real errors.
        error_nodes = ({"material"} if over_100 else set()) | {
            node for node, kinds in deeper_violations.items() if kinds.get("over")
        }
        info_nodes = ({"material"} if under_100 else set()) | {
            node for node, kinds in deeper_violations.items() if kinds.get("under")
        }
        print("\n" + "-" * 80)
        if error_nodes:
            print(f"⚠️  {len(error_nodes)} relationship(s) have real errors "
                  f"(children exceed their parent) — see above.")
        else:
            print("✅ No real errors: no sub-element ever exceeds its parent's mass.")
        if info_nodes:
            print(f"ℹ️  {len(info_nodes)} relationship(s) have an untracked "
                  f"remainder — informational only, see above.")
        print("=" * 80)

    return {"over_100": over_100, "under_100": under_100, "valid_count": valid_count}


def _lighten_hex(hex_color: str, factor: float = 0.4) -> str:
    """Blend a #rrggbb color toward white (same 0.4 rule as the bar chart's
    "Remaining X" segments). Falls back to a neutral grey on bad input."""
    s = str(hex_color).lstrip("#")
    if len(s) != 6:
        return "#cccccc"
    try:
        r, g, b = (int(s[i : i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return "#cccccc"
    r = int(r + (255 - r) * factor)
    g = int(g + (255 - g) * factor)
    b = int(b + (255 - b) * factor)
    return f"#{r:02x}{g:02x}{b:02x}"


def _build_composition_sunburst_figure(
    mfa_system_results,
    flow_id: Optional[str] = None,
    year: Optional[int] = None,
    color_manager: Optional[ElementColorManager] = None,
) -> go.Figure:
    """Build (but do not display) the composition sunburst figure.

    Nesting follows the element hierarchy ch(e) (root = the total-mass element,
    element 0 — conventionally "material"). Each branching node adds a lighter
    "Remaining X" wedge for the untracked residual so its children sum exactly
    to it, keeping ``branchvalues="total"`` consistent (mirrors the stacked-bar
    ``plot_flow_composition``). If a node's children exceed it (a hierarchy
    violation), the node is expanded to fit rather than raising.
    """
    elements = list(mfa_system_results.Elements)
    if not elements:
        raise ValueError("MFA system has no elements to plot.")
    root = elements[0]  # total-mass element (conserved), typically "material"

    years = list(mfa_system_results.IndexTable.Classification["Time"].Items)
    if year is None:
        year = years[-1]
    if year in years:
        year_idx = years.index(year)
    else:  # snap to the nearest available year
        year_idx = int(np.argmin([abs(y - year) for y in years]))
        year = years[year_idx]

    flows = mfa_system_results.FlowDict
    flow_descriptions = getattr(mfa_system_results, "_flow_descriptions", {})

    if flow_id is not None:
        if flow_id not in flows:
            raise KeyError(f"Flow '{flow_id}' not found in the MFA system.")
        selected = {flow_id: flows[flow_id]}
        scope_label = flow_descriptions.get(flow_id, flow_id)
    else:
        selected = flows
        scope_label = "All flows"

    # Mass per element at the chosen year, summed across the selected flows.
    mass_of = {e: 0.0 for e in elements}
    for f in selected.values():
        vals = f.Values[year_idx, :]
        for i, e in enumerate(elements):
            mass_of[e] += float(vals[i])

    # ch(e); fall back to a flat "material → everything else" if no hierarchy.
    element_hierarchy = getattr(mfa_system_results, "_element_hierarchy", {})
    children_map = build_element_children_map(element_hierarchy, elements)
    if not children_map:
        children_map = {root: [e for e in elements if e != root]}

    if color_manager is None:
        color_manager = ElementColorManager([e.lower() for e in elements])

    ids: List[str] = []
    labels: List[str] = []
    parents: List[str] = []
    values: List[float] = []
    colors: List[str] = []
    eps = max(max(mass_of.get(root, 0.0), 0.0) * 1e-6, 1e-9)

    def add_node(elem: str, parent_id: str) -> float:
        """Append this element's wedge (and its subtree); return its effective
        total (= own mass, or the children's sum if they exceed it)."""
        node_id = f"{parent_id}/{elem}" if parent_id else elem
        idx = len(ids)
        mass = max(mass_of.get(elem, 0.0), 0.0)
        ids.append(node_id)
        labels.append(elem)
        parents.append(parent_id)
        values.append(mass)
        colors.append(color_manager.get_element_color(elem))

        kids = children_map.get(elem, [])
        if kids:
            child_sum = 0.0
            for c in kids:
                child_sum += add_node(c, node_id)
            if child_sum > values[idx]:
                # Hierarchy violation: grow the parent so children fit (a red
                # "Remaining" would be misleading; the bar chart flags these).
                values[idx] = child_sum
            else:
                remainder = values[idx] - child_sum
                if remainder > eps:
                    ids.append(f"{node_id}/__remaining__")
                    labels.append(f"Remaining {elem}")
                    parents.append(node_id)
                    values.append(remainder)
                    colors.append(
                        _lighten_hex(color_manager.get_element_color(elem))
                    )
        return values[idx]

    add_node(root, "")

    unit = getattr(mfa_system_results, "Unit", "Mg")
    fig = go.Figure(
        go.Sunburst(
            ids=ids,
            labels=labels,
            parents=parents,
            values=values,
            branchvalues="total",
            marker=dict(colors=colors),
            hovertemplate=(
                "<b>%{label}</b><br>"
                f"%{{value:.4g}} {unit}<br>"
                f"%{{percentRoot:.1%}} of {root}<extra></extra>"
            ),
            insidetextorientation="radial",
        )
    )
    fig.update_layout(
        title=f"Flow composition — {scope_label} ({year})",
        margin=dict(t=60, l=10, r=10, b=10),
    )
    return fig


def plot_flow_composition_sunburst(
    mfa_system_results,
    flow_id: Optional[str] = None,
    year: Optional[int] = None,
    color_manager: Optional[ElementColorManager] = None,
    enable_export: bool = True,
):
    """Display the flow composition as a hierarchical sunburst.

    A supplementary view to :func:`plot_flow_composition` (stacked bars): the
    element hierarchy is shown as concentric rings — the total-mass element at
    the centre, its top-level elements in the first ring, their sub-elements
    further out — with a lighter "Remaining X" wedge for any untracked residual.

    Parameters
    ----------
    mfa_system_results : odym.MFAsystem
        The solved MFA system.
    flow_id : str, optional
        Restrict to a single flow. If None (default), aggregates the mass of
        all flows.
    year : int, optional
        The year to display. Defaults to the last year in the model horizon;
        an out-of-range year snaps to the nearest available one.
    color_manager : ElementColorManager, optional
        Reuse an existing color manager so element colors match other plots.
    enable_export : bool, optional
        If True (default), also show a button to export the figure to
        publication-quality PNG/PDF.

    Notes
    -----
    Follows the module convention: renders via ``fig.show()`` and returns the
    figure (handy for tests / further tweaking).

    Examples
    --------
    >>> plot_flow_composition_sunburst(mfa_results)                 # all flows, last year
    >>> plot_flow_composition_sunburst(mfa_results, year=2050)
    >>> plot_flow_composition_sunburst(mfa_results, flow_id="F_01_02")
    """
    fig = _build_composition_sunburst_figure(
        mfa_system_results,
        flow_id=flow_id,
        year=year,
        color_manager=color_manager,
    )

    if enable_export:
        # Guarded so a missing kaleido/ipywidgets never blocks the plot itself.
        try:
            resolved_year = (
                year
                if year is not None
                else mfa_system_results.IndexTable.Classification["Time"].Items[-1]
            )

            def _export(_btn):
                try:
                    paths = export_figure(
                        fig,
                        f"composition_sunburst_{resolved_year}",
                        formats=["png", "pdf"],
                        quality="publication",
                        size="large",
                    )
                    print(f"✅ Exported: {', '.join(paths)}")
                except Exception as e:  # pragma: no cover - export env dependent
                    print(f"❌ Export failed: {e}")

            export_btn = Button(
                description="📥 Export Figure",
                button_style="success",
                tooltip="Export sunburst to PNG and PDF",
                layout=Layout(width="150px"),
            )
            export_btn.on_click(_export)
            display(export_btn)
        except Exception:  # pragma: no cover - never block rendering
            pass

    fig.show()
    return fig
