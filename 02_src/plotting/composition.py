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
    years. Composition validation checks that element percentages sum to 100%
    for each flow.

    **Hierarchical Elements:** Elements with children display their "Remaining" portion
    to show hierarchy while avoiding double-counting. For example, if CC is defined
    as 45% of DM, the plot shows:
    - WC (water content, % of material)
    - Remaining DM (DM minus CC, % of material) - shown in lighter shade
    - CC (carbon content, % of material)

    This ensures WC + Remaining_DM + CC = 100% of material, providing complete visibility
    of both hierarchy levels while maintaining accurate composition validation.

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

    def validate_composition(
        flow_name: str, percentages: Dict[str, float]
    ) -> Tuple[bool, str]:
        """
        Validate that composition percentages sum to 100%.

        Returns
        -------
        Tuple[bool, str]
            (is_valid, warning_message)
        """
        total_pct = sum(percentages.values())

        if abs(total_pct - 100.0) > composition_tolerance:
            if total_pct > 100.0:
                return False, f"⚠️ {flow_name}: Sum = {total_pct:.1f}% (EXCEEDS 100%)"
            else:
                return False, f"⚠️ {flow_name}: Sum = {total_pct:.1f}% (BELOW 100%)"

        return True, ""

    def update_plot(year):
        year_index = list(years).index(year)

        flow_names = []
        element_percentages = {elem: [] for elem in composable_elements}
        validation_warnings = []

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
                flow_percentages = {}

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
                    flow_percentages[display_elem] = percentage

                # Validate composition
                if show_validation_warnings:
                    is_valid, warning = validate_composition(
                        display_name, flow_percentages
                    )
                    if not is_valid:
                        validation_warnings.append(warning)

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

                fig.add_trace(
                    go.Bar(
                        y=flow_names,
                        x=element_percentages[display_elem],
                        name=display_name,
                        orientation="h",
                        marker=dict(
                            color=element_color,
                            line=dict(color=BIOYM_COLORS["dark"], width=0.5),
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

        # Update validation warnings display
        if show_validation_warnings and validation_warnings:
            warning_html = "<div style='background-color: #fff3cd; border: 1px solid #ffc107; border-radius: 4px; padding: 10px; margin: 10px 0;'>"
            warning_html += "<strong>⚠️ Composition Validation Warnings:</strong><br>"
            for warning in validation_warnings:
                warning_html += f"• {warning}<br>"
            warning_html += f"<em>Tolerance: ±{composition_tolerance}%</em>"
            warning_html += "</div>"
            validation_output.value = warning_html
        else:
            validation_output.value = ""

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

    This function checks that the sum of element percentages equals 100%
    for each flow in each year, helping detect data quality issues.

    Hierarchical elements are handled by calculating "Remaining" portions
    (e.g., "Remaining DM" = DM - CC) to show hierarchy without double-counting.
    This ensures validation sums: WC + Remaining_DM + CC = 100%.

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
        Dictionary with 'over_100' and 'under_100' keys, each containing
        list of (flow_name, year, total_percentage) tuples for violations.

    Examples
    --------
    >>> # Validate compositions
    >>> issues = validate_flow_compositions(mfa_results, tolerance=1.0)
    >>> if issues['over_100']:
    ...     print("Flows exceeding 100%:", issues['over_100'])
    """
    flows = mfa_system_results.FlowDict
    years = mfa_system_results.IndexTable.Classification["Time"].Items
    element_items = [e.lower() for e in mfa_system_results.Elements]

    # Get flow descriptions for display (use descriptive names instead of IDs)
    flow_descriptions = getattr(mfa_system_results, "_flow_descriptions", {})

    # Get element hierarchy info
    # NOTE: _element_hierarchy is a BioDYM extension (stored by system_setup.py)
    element_hierarchy = getattr(mfa_system_results, "_element_hierarchy", {})

    # Build composition structure respecting hierarchy (same as plot function)
    elements_with_children = set()
    leaf_elements = []

    for e in element_items:
        if e == "material":
            continue

        has_children = False
        if element_hierarchy:
            for elem_id, elem_info in element_hierarchy.items():
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

    # Build display elements list
    composable_elements = []
    for e in element_items:
        if e == "material":
            continue
        if e in elements_with_children:
            composable_elements.append(f"remaining_{e}")
        if e in leaf_elements:
            composable_elements.append(e)

    over_100 = []
    under_100 = []
    valid_count = 0

    for flow_id, flow in flows.items():
        # Use descriptive name if available, otherwise use Flow ID
        display_name = flow_descriptions.get(flow_id, flow_id)

        for year_idx, year in enumerate(years):
            values = flow.Values[year_idx, :]

            material_idx = element_items.index("material")
            total_mass = values[material_idx]

            if total_mass > 1e-10:
                # Calculate total percentage using hierarchy-aware logic
                total_pct = 0
                for display_elem in composable_elements:
                    if display_elem.startswith("remaining_"):
                        # Calculate remaining portion
                        parent_elem = display_elem.replace("remaining_", "")
                        parent_idx = element_items.index(parent_elem)
                        parent_val = values[parent_idx]

                        # Subtract children
                        children_sum = 0
                        if element_hierarchy:
                            for elem_id, elem_info in element_hierarchy.items():
                                elem_parent = (
                                    elem_info.get("parent", "").lower()
                                    if elem_info.get("parent")
                                    else None
                                )
                                if elem_parent == parent_elem.lower():
                                    child_name = elem_info["name"].lower()
                                    if child_name in element_items:
                                        child_idx = element_items.index(child_name)
                                        children_sum += values[child_idx]

                        remaining_val = parent_val - children_sum
                        total_pct += remaining_val / total_mass * 100
                    else:
                        # Regular element
                        elem_idx = element_items.index(display_elem)
                        elem_val = values[elem_idx]
                        total_pct += elem_val / total_mass * 100

                # Check validation
                if total_pct > 100.0 + tolerance:
                    over_100.append((display_name, year, total_pct))
                elif total_pct < 100.0 - tolerance:
                    under_100.append((display_name, year, total_pct))
                else:
                    valid_count += 1

    # Print report
    if verbose:
        print("=" * 80)
        print("FLOW COMPOSITION VALIDATION REPORT")
        print("=" * 80)
        print(f"Tolerance: ±{tolerance}%")
        print(
            f"Total flow-year combinations checked: {valid_count + len(over_100) + len(under_100)}"
        )
        print(f"✅ Valid (within tolerance): {valid_count}")
        print(f"⚠️ Exceeding 100%: {len(over_100)}")
        print(f"⚠️ Below 100%: {len(under_100)}")

        if over_100:
            print("\n" + "=" * 80)
            print("FLOWS EXCEEDING 100% (Data Quality Issue)")
            print("=" * 80)
            for flow_name, year, total_pct in sorted(
                over_100, key=lambda x: x[2], reverse=True
            )[:10]:
                print(f"  {flow_name:40s} | Year {year} | {total_pct:6.2f}%")
            if len(over_100) > 10:
                print(f"  ... and {len(over_100) - 10} more")

        if under_100:
            print("\n" + "=" * 80)
            print("FLOWS BELOW 100% (Missing Material)")
            print("=" * 80)
            for flow_name, year, total_pct in sorted(under_100, key=lambda x: x[2])[
                :10
            ]:
                print(f"  {flow_name:40s} | Year {year} | {total_pct:6.2f}%")
            if len(under_100) > 10:
                print(f"  ... and {len(under_100) - 10} more")

        print("\n" + "=" * 80)

    return {"over_100": over_100, "under_100": under_100, "valid_count": valid_count}
