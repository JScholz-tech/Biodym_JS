# -*- coding: utf-8 -*-
"""
Enhanced Sankey Diagram Module for BioDYM MFA Tool.

This module provides advanced Sankey diagram functionality with support for:
- Excel-based visualization configuration
- Custom node positioning and styling
- Toggling between fixed, auto-layout, and interactive modes
"""

import collections
import os
from ipywidgets import (
    FloatSlider,
    IntSlider,
    HBox,
    VBox,
    Layout,
    Dropdown,
    SelectMultiple,
    Checkbox,
)
from IPython.display import display
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _safe_float_convert(value, default=1.0):
    """Safely convert a value to a float.

    This helper function attempts to convert a given value to a float, handling
    integers, floats, and strings (with comma as a decimal separator).
    If the conversion fails, it returns a default value.

    Parameters
    ----------
    value : any
        The value to be converted to a float.
    default : float, optional
        The default value to return if conversion fails. Defaults to 1.0.

    Returns
    -------
    float
        The converted float value or the default value.
    """
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).replace(",", "."))
    except (ValueError, TypeError):
        return default


def _calculate_node_positions(processes, flows):
    """Calculates node x-positions for a Sankey diagram using a topological sort.

    This function determines the horizontal (x-axis) position of each node
    (process) in a Sankey diagram. It constructs a directed graph from the
    flows between processes and uses a topological sort (Kahn's algorithm)
    to assign each node to a layer. The layer number then determines the
    x-position, creating a left-to-right flow layout.

    Parameters
    ----------
    processes : list of odym.Process
        A list of the process objects to be included as nodes in the diagram.
    flows : list of odym.Flow
        A list of the flow objects that connect the processes.

    Returns
    -------
    dict
        A dictionary mapping each process ID to its calculated x-position,
        a float value between 0.1 and 0.9.

    Notes
    -----
    Nodes with an in-degree of zero are placed in the first layer (leftmost).
    If the graph contains cycles, the remaining nodes are placed in a final
    layer to the right.
    """
    nodes = {p.ID for p in processes}
    if not nodes:
        return {}

    adj = {node: [] for node in nodes}
    in_degree = {node: 0 for node in nodes}

    for flow in flows:
        if flow.P_Start in nodes and flow.P_End in nodes:
            adj[flow.P_Start].append(flow.P_End)
            in_degree[flow.P_End] += 1

    queue = collections.deque([node for node in nodes if in_degree[node] == 0])
    layers = {node: 0 for node in nodes}
    max_layer = 0

    while queue:
        u = queue.popleft()
        for v in adj[u]:
            in_degree[v] -= 1
            layers[v] = max(layers.get(v, 0), layers[u] + 1)
            max_layer = max(max_layer, layers[v])
            if in_degree[v] == 0:
                queue.append(v)

    remaining_nodes = [node for node in nodes if in_degree[node] > 0]
    if remaining_nodes:
        max_layer += 1
        for node in remaining_nodes:
            layers[node] = max_layer

    if max_layer == 0:
        return {node: 0.5 for node in nodes}

    return {node: 0.1 + (layers[node] / max_layer) * 0.8 for node in nodes}


def load_visualization_config(excel_file_path):
    """Load visualization configuration from an Excel file.

    This function serves as a wrapper around the
    `visualization_loader.load_visualization_config_from_excel` function,
    providing a convenient way to load Sankey diagram styling and layout
    settings from a specified Excel file.

    Parameters
    ----------
    excel_file_path : str
        The absolute path to the Excel file containing the visualization
        configuration sheets.

    Returns
    -------
    dict
        A dictionary containing the loaded visualization configuration.
    """
    from .visualization_loader import load_visualization_config_from_excel

    return load_visualization_config_from_excel(excel_file_path)


def calculate_element_specific_positions(processes, config, element):
    """Calculate node positions based on element-specific settings in the config.

    This function determines the (x, y) coordinates for each process node based
    on the visualization configuration. It prioritizes element-specific
    positions (e.g., 'X_Position_C') before falling back to generic positions.
    The final coordinates are clamped to the valid range [0.0, 1.0].

    Parameters
    ----------
    processes : list of odym.Process
        The list of process objects to be positioned.
    config : dict
        The visualization configuration dictionary, loaded from Excel.
    element : str
        The specific element for which to calculate positions.

    Returns
    -------
    dict
        A dictionary mapping each process ID to a tuple (x, y) of its
        calculated coordinates.
    """
    positions = {}
    for process in processes:
        viz_settings = get_process_visualization(
            process.ID, process.Name, config, element
        )
        x = _safe_float_convert(viz_settings.get("X_Position"), 0.5)
        y = _safe_float_convert(viz_settings.get("Y_Position"), 0.5)

        # No clamping - allow free positioning anywhere
        # Users can place nodes outside [0,1] range if needed

        positions[process.ID] = (x, y)
    return positions


def get_process_visualization(
    process_id: int, process_name: str, config: dict, element: str = None
) -> dict:
    """Get visualization settings for a process, with robust element-specific positioning.

    This function retrieves the visualization settings (e.g., color, position)
    for a specific process from the configuration dictionary. It can look up
    the process by its ID or name. For positions, it implements a fallback
    logic, prioritizing element-specific keys (e.g., 'X_Position_C') before
    using generic keys ('X_Position').

    Parameters
    ----------
    process_id : int
        The ID of the process.
    process_name : str
        The name of the process, used as a fallback for lookup.
    config : dict
        The visualization configuration dictionary.
    element : str, optional
        The specific element being plotted. If provided, the function will
        search for element-specific position keys. Defaults to None.

    Returns
    -------
    dict
        A dictionary of visualization settings for the process. Returns a
        default dictionary with a grey color if the process is not found.
    """
    processes_config = config.get("process_colors", config.get("processes", {}))
    proc_key = str(process_id).strip().upper()
    proc_config = processes_config.get(proc_key)

    if not proc_config:
        for key, value in processes_config.items():
            config_name = value.get("Process_Name") or value.get("Name(EN)")
            if (
                config_name
                and str(config_name).strip().upper()
                == str(process_name).strip().upper()
            ):
                proc_config = value
                break

    if not proc_config:
        return {"Node_Color_#": "#808080", "X_Position": 0.5, "Y_Position": 0.5}

    viz_settings = proc_config.copy()

    def get_valid_position(key_options):
        for key in key_options:
            for config_key in viz_settings:
                if config_key.upper() == key.upper():
                    val = viz_settings[config_key]
                    if val is not None and str(val).strip() not in ["", "nan"]:
                        try:
                            return float(str(val).replace(",", "."))
                        except (ValueError, TypeError):
                            continue
        return None

    if element:
        x_keys = [f"X_Position_{element.upper()}", "X_Position_Material", "X_Position"]
        y_keys = [f"Y_Position_{element.upper()}", "Y_Position_Material", "Y_Position"]
        x_pos = get_valid_position(x_keys)
        y_pos = get_valid_position(y_keys)
        viz_settings["X_Position"] = x_pos if x_pos is not None else 0.5
        viz_settings["Y_Position"] = y_pos if y_pos is not None else 0.5
    else:
        viz_settings["X_Position"] = get_valid_position(["X_Position"]) or 0.5
        viz_settings["Y_Position"] = get_valid_position(["Y_Position"]) or 0.5

    return viz_settings


def get_flow_visualization(flow_id, flow_name, config):
    """Get visualization settings for a flow.

    This function retrieves the visualization settings (e.g., color) for a
    specific flow from the configuration dictionary. It can look up the flow
    by its ID or name.

    Parameters
    ----------
    flow_id : str
        The ID of the flow.
    flow_name : str
        The name of the flow, used as a fallback for lookup.
    config : dict
        The visualization configuration dictionary.

    Returns
    -------
    dict
        A dictionary of visualization settings for the flow. Returns a default
        dictionary with a blue color if the flow is not found.
    """
    flows_config = config.get("flow_colors", config.get("flows", {}))
    if flow_id in flows_config:
        return flows_config[flow_id]
    for fid, flow_config in flows_config.items():
        if flow_config.get("Flow_Name") == flow_name:
            return flow_config
    return {"Flow_Color_#": "#1f77b4"}


def plot_enhanced_sankey(
    mfa_system_results,
    dsm_params=None,
    fomp_params=None,
    visualization_config_path=None,
):
    """Enhanced interactive Sankey diagram with selectable layout modes.

    This function creates a highly interactive Sankey diagram for visualizing
    Material Flow Analysis (MFA) results. It allows for dynamic filtering by
    year, element, and processes, and supports two layout modes:
    - **Custom**: Node positions are loaded from an Excel configuration file,
      allowing for precise, publication-ready layouts.
    - **Auto-Layout**: Node positions are calculated automatically using a
      topological sort for a clean, hierarchical arrangement.

    Parameters
    ----------
    mfa_system_results : odym.MFAsystem
        The solved MFA system object containing all calculated data.
    dsm_params : dict, optional
        Unused in this function, but kept for API consistency. Defaults to None.
    fomp_params : dict, optional
        Unused in this function, but kept for API consistency. Defaults to None.
    visualization_config_path : str, optional
        The absolute path to the Excel file containing visualization settings.
        If not provided or not found, default settings are used.

    Notes
    -----
    The function uses `ipywidgets` for interactivity and `plotly` for plotting.
    It is designed to be used within a Jupyter Notebook or JupyterLab environment.
    The `dsm_params` and `fomp_params` are included for API consistency but do
    not influence the plot generated by this function.
    """
    if visualization_config_path and os.path.exists(visualization_config_path):
        config = load_visualization_config(visualization_config_path)
    else:
        config = {}
        print("Warning: Visualization config file not found. Using default settings.")

    all_processes = mfa_system_results.ProcessList
    all_flows = list(mfa_system_results.FlowDict.values())
    time_items = mfa_system_results.IndexTable.Classification["Time"].Items
    element_items = mfa_system_results.Elements
    max_flow_value = (
        max(f.Values.max() for f in all_flows if f.Values is not None)
        if all_flows
        else 1
    )

    fig = go.FigureWidget(go.Sankey(node={}, link={}))
    layout_settings = config.get("layout_settings", {})

    def _safe_int_convert(value, default=1200):
        return int(_safe_float_convert(value, default))

    # --- WIDGETS ---
    year_slider = IntSlider(
        min=time_items[0],
        max=time_items[-1],
        value=time_items[0],
        description="Year:",
        layout=Layout(width="300px"),
    )
    element_dropdown = Dropdown(
        options=element_items,
        value=element_items[0],
        description="Element:",
        layout=Layout(width="200px"),
    )
    process_selector = SelectMultiple(
        options=[p.Name for p in all_processes],
        value=[p.Name for p in all_processes],
        description="Processes:",
        layout=Layout(width="400px", height="100px"),
    )
    min_flow_slider = FloatSlider(
        value=0,
        min=0,
        max=max_flow_value,
        step=max_flow_value / 100,
        description="Min Flow:",
        layout=Layout(width="300px"),
    )
    layout_dropdown = Dropdown(
        options=["Custom", "Auto-Layout"],
        value="Custom",
        description="Layout:",
        layout=Layout(width="150px"),
    )
    show_coordinates_checkbox = Checkbox(
        value=False, description="Show Coordinates", layout=Layout(width="150px")
    )

    # --- UI LAYOUT ---
    controls = VBox(
        [
            HBox([year_slider, element_dropdown]),
            HBox([process_selector, min_flow_slider]),
            HBox([layout_dropdown, show_coordinates_checkbox]),
        ]
    )

    # --- UPDATE FUNCTION ---
    def update_sankey(
        year, element, processes_to_show, min_flow_value, layout_type, show_coords
    ):
        with fig.batch_update():
            if not processes_to_show:
                fig.data[0].node.label = []
                fig.data[0].link.source = []
                return

            year_index = time_items.index(year)
            element_index = element_items.index(element)
            filtered_processes = [
                p for p in all_processes if p.Name in processes_to_show
            ]
            process_id_to_index = {p.ID: i for i, p in enumerate(filtered_processes)}
            final_flows = [
                f
                for f in all_flows
                if f.P_Start in process_id_to_index
                and f.P_End in process_id_to_index
                and f.Values[year_index, element_index] >= min_flow_value
            ]

            if layout_type == "Auto-Layout":
                arrangement = "snap"
                layout_flows = [
                    f
                    for f in all_flows
                    if f.P_Start in process_id_to_index
                    and f.P_End in process_id_to_index
                ]
                node_positions = _calculate_node_positions(
                    filtered_processes, layout_flows
                )
                node_x = [node_positions.get(p.ID, 0.5) for p in filtered_processes]
                node_y = None
                current_pad, current_thickness = 20, 15
                current_margin = dict(l=250, r=250, b=200, t=200)
                current_font_size, current_hovermode, current_dragmode = (
                    12,
                    "closest",
                    "pan",
                )
                show_axes = False
            else:  # 'Custom' mode
                arrangement = "fixed"
                all_positions = calculate_element_specific_positions(
                    all_processes, config, element
                )
                padding_factor = _safe_float_convert(
                    layout_settings.get("Padding_Factor", 0.1), 0.1
                )
                zoom_factor = _safe_float_convert(
                    layout_settings.get("Zoom_Factor", 1.0), 1.0
                )
                padding = max(0.05, padding_factor / zoom_factor)
                x_values = [pos[0] for pos in all_positions.values()]
                y_values = [pos[1] for pos in all_positions.values()]
                if x_values and y_values:
                    min_x, max_x = min(x_values), max(x_values)
                    min_y, max_y = min(y_values), max(y_values)
                    span_x, span_y = max_x - min_x, max_y - min_y
                    target_span = 1.0 - 2 * padding
                    scale = min(
                        target_span / max(span_x, 0.1), target_span / max(span_y, 0.1)
                    )
                    center_x, center_y = (min_x + max_x) / 2, (min_y + max_y) / 2
                    for pid, pos in all_positions.items():
                        all_positions[pid] = (
                            0.5 + (pos[0] - center_x) * scale,
                            0.5 + (pos[1] - center_y) * scale,
                        )
                node_x = [
                    all_positions.get(p.ID, (0.5, 0.5))[0] for p in filtered_processes
                ]
                node_y = [
                    all_positions.get(p.ID, (0.5, 0.5))[1] for p in filtered_processes
                ]
                node_scale_factor = _safe_float_convert(
                    layout_settings.get("Node_Scale_Factor", 1.0)
                )
                current_pad = int(15 * zoom_factor * node_scale_factor)
                current_thickness = int(20 * zoom_factor * node_scale_factor)
                current_margin = dict(l=50, r=50, t=80, b=50)
                current_font_size, current_hovermode, current_dragmode = 16, "x", "pan"
                show_axes = True

            node_colors = [
                get_process_visualization(p.ID, p.Name, config).get(
                    "Node_Color_#", "#808080"
                )
                for p in filtered_processes
            ]
            fig.data[0].arrangement = arrangement
            fig.data[0].node = dict(
                label=[p.Name for p in filtered_processes],
                x=node_x,
                y=node_y,
                color=node_colors,
                pad=current_pad,
                thickness=current_thickness,
                line=dict(color="black", width=0.5),
            )

            if final_flows:
                flow_values = [f.Values[year_index, element_index] for f in final_flows]
                flow_sources = [process_id_to_index[f.P_Start] for f in final_flows]
                flow_targets = [process_id_to_index[f.P_End] for f in final_flows]
                default_flow_color = (
                    config.get("elements", {}).get(element, {}).get("Color", "#888")
                )
                flow_colors = [
                    get_flow_visualization(f.Name, f.Name, config).get(
                        "Flow_Color_#", default_flow_color
                    )
                    for f in final_flows
                ]
                # Use descriptive names if available, fallback to flow ID
                custom_data = [
                    getattr(f, "DescriptiveName", f.Name) for f in final_flows
                ]
                fig.data[0].link = dict(
                    source=flow_sources,
                    target=flow_targets,
                    value=flow_values,
                    color=flow_colors,
                    customdata=custom_data,
                    hovertemplate="Flow: %{customdata}<br>Source: %{source.label}<br>Target: %{target.label}<br>Value: %{value}<extra></extra>",
                )
            else:
                fig.data[0].link = dict(source=[], target=[], value=[])

            total_flow = sum(flow_values) if final_flows else 0
            title_text = (
                f"Sankey Diagram - {element} ({year}) - Total Flow: {total_flow:.1f} t"
            )
            window_width = _safe_int_convert(layout_settings.get("Window_Width", 1400))
            window_height = _safe_int_convert(layout_settings.get("Window_Height", 900))

            fig.update_layout(
                title_text=title_text,
                font_size=current_font_size,
                height=window_height,
                width=window_width,
                margin=current_margin,
                hovermode=current_hovermode,
                dragmode=current_dragmode,
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=show_axes),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=show_axes),
            )

            # Add coordinate annotations if requested
            if show_coords and layout_type == "Custom":
                annotations = []
                for i, p in enumerate(filtered_processes):
                    x_pos = node_x[i]
                    y_pos = node_y[i] if node_y else 0.5
                    # Get original (unscaled) positions from config
                    original_pos = calculate_element_specific_positions(
                        [p], config, element
                    ).get(p.ID, (0.5, 0.5))

                    annotations.append(
                        dict(
                            x=x_pos,
                            y=y_pos,
                            text=f"({original_pos[0]:.2f}, {original_pos[1]:.2f})",
                            showarrow=False,
                            font=dict(size=9, color="#666"),
                            xanchor="center",
                            yanchor="bottom",
                            yshift=25,  # Position above node
                        )
                    )
                fig.update_layout(annotations=annotations)
            else:
                fig.update_layout(annotations=[])

    # --- WIDGET INTERACTION ---
    def handle_change(change):
        update_sankey(
            year_slider.value,
            element_dropdown.value,
            process_selector.value,
            min_flow_slider.value,
            layout_dropdown.value,
            show_coordinates_checkbox.value,
        )

    year_slider.observe(handle_change, names="value")
    element_dropdown.observe(handle_change, names="value")
    process_selector.observe(handle_change, names="value")
    min_flow_slider.observe(handle_change, names="value")
    layout_dropdown.observe(handle_change, names="value")
    show_coordinates_checkbox.observe(handle_change, names="value")

    display(VBox([controls, fig]))
    handle_change(None)  # Initial plot draw


def plot_element_multiplot_sankey(
    mfa_system_results,
    visualization_config_path=None,
    elements_to_plot=None,
    subplot_height=350,
):
    """Create stacked Sankey diagrams showing multiple elements with time slider.

    This function creates a vertically-stacked multiplot where each subplot shows
    a different element (material, WC, DM, CC). All subplots share a single time
    slider, allowing you to see how the multi-level elemental composition evolves
    over time. This visualization emphasizes both the multi-level character
    (hierarchical elements) and dynamic evolution (time slider).

    Parameters
    ----------
    mfa_system_results : odym.MFAsystem
        The solved MFA system object containing all calculated data.
    visualization_config_path : str, optional
        The absolute path to the Excel file containing visualization settings.
        If not provided, default settings are used.
    elements_to_plot : list of str, optional
        List of element names to plot. If None, uses all elements from the system.
    subplot_height : int, optional
        Height in pixels for each subplot. Total figure height will be
        (num_elements × subplot_height). Defaults to 350.

    Returns
    -------
    None
        Displays the interactive multiplot in the notebook.

    Notes
    -----
    This function creates an interactive visualization with:
    - Time slider: Navigate through years (updates all subplots)
    - Process selector: Filter which processes to show
    - Min flow slider: Filter out small flows
    - Layout dropdown: Switch between Custom (Excel) and Auto-Layout

    The multiplot design shows the multi-level character of BioDYM's element
    tracking system, with material at the top, followed by WC, DM, and CC.
    """
    if visualization_config_path and os.path.exists(visualization_config_path):
        config = load_visualization_config(visualization_config_path)
    else:
        config = {}
        print("Warning: Visualization config file not found. Using default settings.")

    all_processes = mfa_system_results.ProcessList
    all_flows = list(mfa_system_results.FlowDict.values())
    time_items = mfa_system_results.IndexTable.Classification["Time"].Items
    element_items = mfa_system_results.Elements

    # Determine which elements to plot
    if elements_to_plot is None:
        elements_to_plot = element_items
    else:
        # Validate requested elements exist
        elements_to_plot = [e for e in elements_to_plot if e in element_items]

    num_elements = len(elements_to_plot)
    total_height = num_elements * subplot_height

    # Create subplot structure
    subplot_titles = [f"{elem.upper()}" for elem in elements_to_plot]
    fig = make_subplots(
        rows=num_elements,
        cols=1,
        subplot_titles=subplot_titles,
        specs=[[{"type": "sankey"}] for _ in range(num_elements)],
        vertical_spacing=0.08,
    )

    # Convert to FigureWidget for interactivity
    fig = go.FigureWidget(fig)

    layout_settings = config.get("layout_settings", {})
    max_flow_value = (
        max(f.Values.max() for f in all_flows if f.Values is not None)
        if all_flows
        else 1
    )

    def _safe_int_convert(value, default=1200):
        return int(_safe_float_convert(value, default))

    # --- WIDGETS ---
    year_slider = IntSlider(
        min=time_items[0],
        max=time_items[-1],
        value=time_items[0],
        description="Year:",
        layout=Layout(width="400px"),
    )
    process_selector = SelectMultiple(
        options=[p.Name for p in all_processes],
        value=[p.Name for p in all_processes],
        description="Processes:",
        layout=Layout(width="500px", height="120px"),
    )
    min_flow_slider = FloatSlider(
        value=0,
        min=0,
        max=max_flow_value,
        step=max_flow_value / 100 if max_flow_value > 0 else 1,
        description="Min Flow:",
        layout=Layout(width="400px"),
    )
    layout_dropdown = Dropdown(
        options=["Custom", "Auto-Layout"],
        value="Custom",
        description="Layout:",
        layout=Layout(width="200px"),
    )

    # --- UI LAYOUT ---
    controls = VBox(
        [
            HBox([year_slider, layout_dropdown]),
            HBox([process_selector, min_flow_slider]),
        ]
    )

    # --- UPDATE FUNCTION ---
    def update_multiplot(year, processes_to_show, min_flow_value, layout_type):
        """Update all subplots for the selected year and filters."""
        with fig.batch_update():
            if not processes_to_show:
                # Clear all subplots
                for i in range(num_elements):
                    fig.data[i].node.label = []
                    fig.data[i].link.source = []
                return

            year_index = time_items.index(year)
            filtered_processes = [
                p for p in all_processes if p.Name in processes_to_show
            ]
            process_id_to_index = {p.ID: i for i, p in enumerate(filtered_processes)}

            # Calculate node positions once (shared across elements)
            if layout_type == "Auto-Layout":
                arrangement = "snap"
                layout_flows = [
                    f
                    for f in all_flows
                    if f.P_Start in process_id_to_index
                    and f.P_End in process_id_to_index
                ]
                node_positions = _calculate_node_positions(
                    filtered_processes, layout_flows
                )
                node_x = [node_positions.get(p.ID, 0.5) for p in filtered_processes]
                node_y = None
                current_pad, current_thickness = 15, 12
            else:  # 'Custom' mode
                arrangement = "fixed"
                all_positions = calculate_element_specific_positions(
                    all_processes, config, elements_to_plot[0]
                )
                padding_factor = _safe_float_convert(
                    layout_settings.get("Padding_Factor", 0.1), 0.1
                )
                zoom_factor = _safe_float_convert(
                    layout_settings.get("Zoom_Factor", 1.0), 1.0
                )
                padding = max(0.05, padding_factor / zoom_factor)

                x_values = [pos[0] for pos in all_positions.values()]
                y_values = [pos[1] for pos in all_positions.values()]

                if x_values and y_values:
                    min_x, max_x = min(x_values), max(x_values)
                    min_y, max_y = min(y_values), max(y_values)
                    span_x, span_y = max_x - min_x, max_y - min_y
                    target_span = 1.0 - 2 * padding
                    scale = min(
                        target_span / max(span_x, 0.1), target_span / max(span_y, 0.1)
                    )
                    center_x, center_y = (min_x + max_x) / 2, (min_y + max_y) / 2

                    for pid, pos in all_positions.items():
                        all_positions[pid] = (
                            0.5 + (pos[0] - center_x) * scale,
                            0.5 + (pos[1] - center_y) * scale,
                        )

                node_x = [
                    all_positions.get(p.ID, (0.5, 0.5))[0] for p in filtered_processes
                ]
                node_y = [
                    all_positions.get(p.ID, (0.5, 0.5))[1] for p in filtered_processes
                ]
                node_scale_factor = _safe_float_convert(
                    layout_settings.get("Node_Scale_Factor", 1.0)
                )
                current_pad = int(12 * zoom_factor * node_scale_factor)
                current_thickness = int(18 * zoom_factor * node_scale_factor)

            node_colors = [
                get_process_visualization(p.ID, p.Name, config).get(
                    "Node_Color_#", "#808080"
                )
                for p in filtered_processes
            ]

            # Update each subplot (one per element)
            for elem_idx, element in enumerate(elements_to_plot):
                element_index = element_items.index(element)

                # Filter flows for this element
                final_flows = [
                    f
                    for f in all_flows
                    if f.P_Start in process_id_to_index
                    and f.P_End in process_id_to_index
                    and f.Values[year_index, element_index] >= min_flow_value
                ]

                # Update node for this subplot
                fig.data[elem_idx].arrangement = arrangement
                fig.data[elem_idx].node = dict(
                    label=[p.Name for p in filtered_processes],
                    x=node_x,
                    y=node_y,
                    color=node_colors,
                    pad=current_pad,
                    thickness=current_thickness,
                    line=dict(color="black", width=0.5),
                )

                # Update links for this subplot
                if final_flows:
                    flow_values = [
                        f.Values[year_index, element_index] for f in final_flows
                    ]
                    flow_sources = [process_id_to_index[f.P_Start] for f in final_flows]
                    flow_targets = [process_id_to_index[f.P_End] for f in final_flows]
                    default_flow_color = (
                        config.get("elements", {}).get(element, {}).get("Color", "#888")
                    )
                    flow_colors = [
                        get_flow_visualization(f.Name, f.Name, config).get(
                            "Flow_Color_#", default_flow_color
                        )
                        for f in final_flows
                    ]
                    custom_data = [
                        getattr(f, "DescriptiveName", f.Name) for f in final_flows
                    ]

                    fig.data[elem_idx].link = dict(
                        source=flow_sources,
                        target=flow_targets,
                        value=flow_values,
                        color=flow_colors,
                        customdata=custom_data,
                        hovertemplate="Flow: %{customdata}<br>Source: %{source.label}<br>Target: %{target.label}<br>Value: %{value:.2f}<extra></extra>",
                    )
                else:
                    fig.data[elem_idx].link = dict(source=[], target=[], value=[])

            # Update overall layout
            window_width = _safe_int_convert(layout_settings.get("Window_Width", 1400))
            fig.update_layout(
                height=total_height,
                width=window_width,
                title_text=f"Multi-Element Sankey Diagram - Year {year}",
                font_size=12,
                showlegend=False,
                hovermode="closest",
            )

    # --- WIDGET INTERACTION ---
    def handle_change(change):
        update_multiplot(
            year_slider.value,
            process_selector.value,
            min_flow_slider.value,
            layout_dropdown.value,
        )

    year_slider.observe(handle_change, names="value")
    process_selector.observe(handle_change, names="value")
    min_flow_slider.observe(handle_change, names="value")
    layout_dropdown.observe(handle_change, names="value")

    display(VBox([controls, fig]))
    handle_change(None)  # Initial plot draw
