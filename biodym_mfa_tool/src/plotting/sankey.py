
# -*- coding: utf-8 -*-
"""
Sankey Diagram Plotting Module.

This file contains the functions for generating interactive Sankey diagrams.
"""

import plotly.graph_objects as go
from ipywidgets import FloatSlider, Button, HBox, VBox, HTML, Layout, Dropdown, SelectMultiple
import os
from datetime import datetime

def plot_interactive_sankey(mfa_system_results, dsm_params=None, fomp_params=None):
    """
    Enhanced interactive Sankey diagram with advanced customization options.
    
    Features:
    - Color coding for process types (Regular, DSM, FOMP)
    - Export functionality (PNG) with organized folder
    - Professional legend
    - Flow threshold filtering
    - Process selection (multi-select, all selected by default)
    - Proper zoom and frame controls
    - Manual node positioning

    Args:
        mfa_system_results (odym.MFAsystem): The solved MFA system object.
        dsm_params (dict, optional): DSM parameters to identify DSM processes.
        fomp_params (dict, optional): FOMP parameters to identify FOMP processes.
    """
    from ipywidgets import interactive
    
    all_process_names = [p.Name for p in mfa_system_results.ProcessList]
    all_flows = list(mfa_system_results.FlowDict.values())
    time_items = mfa_system_results.IndexTable.Classification["Time"].Items
    element_items = mfa_system_results.Elements

    # Determine max flow value for slider
    max_flow_value = (
        max(f.Values.max() for f in all_flows if f.Values is not None)
        if all_flows
        else 1
    )

    # Define color schemes
    process_colors = {
        'Regular': '#1f77b4',  # Blue
        'DSM': '#ff7f0e',      # Orange
        'FOMP': '#2ca02c',     # Green
        'Input': '#d62728',     # Red
        'Output': '#9467bd'     # Purple
    }
    
    element_colors = {
        'material': '#1f77b4',
        'WC': '#ff7f0e', 
        'DM': '#2ca02c',
        'CC': '#d62728'
    }

    # Create the FigureWidget with proper zoom controls
    fig = go.FigureWidget(
        data=[go.Sankey(
            node=dict(
                label=[],
                color=[],
                pad=20,
                thickness=15,
                line=dict(color="black", width=0.5)
            ),
            link=dict(
                source=[],
                target=[],
                value=[],
                color=[]
            ),
            arrangement="snap"
        )]
    )

    def get_process_type(process_id):
        """Determine process type for color coding"""
        if dsm_params and process_id in dsm_params:
            return 'DSM'
        elif fomp_params and process_id in fomp_params:
            return 'FOMP'
        else:
            return 'Regular'

    def update_sankey(year, element, processes_to_show, min_flow_value):
        if not processes_to_show:
            with fig.batch_update():
                fig.data[0].node.label = []
            return

        # Create process mapping
        label_map = {
            p.ID: i
            for i, p in enumerate(mfa_system_results.ProcessList)
            if p.Name in processes_to_show
        }
        filtered_labels = list(processes_to_show)

        year_index = time_items.index(year)
        element_index = element_items.index(element)

        # Get candidate flows
        candidate_flows = [
            f for f in all_flows if f.P_Start in label_map and f.P_End in label_map
        ]

        # Filter flows based on threshold
        final_flows = [
            f
            for f in candidate_flows
            if f.Values[year_index, element_index] >= min_flow_value
        ]

        with fig.batch_update():
            if not final_flows:
                fig.data[0].node.label = filtered_labels
                fig.data[0].node.color = []
                fig.data[0].link.source = []
                fig.data[0].link.target = []
                fig.data[0].link.value = []
                fig.data[0].link.color = []
            else:
                # Calculate flow values
                flow_values = [f.Values[year_index, element_index] for f in final_flows]
                
                # Set node colors based on process type
                node_colors = []
                for process_name in filtered_labels:
                    process_id = next(p.ID for p in mfa_system_results.ProcessList if p.Name == process_name)
                    process_type = get_process_type(process_id)
                    node_colors.append(process_colors.get(process_type, process_colors['Regular']))
                
                # Set link colors based on element
                link_colors = [element_colors.get(element, '#1f77b4')] * len(final_flows)
                
                fig.data[0].node.label = filtered_labels
                fig.data[0].node.color = node_colors
                fig.data[0].link.source = [label_map[f.P_Start] for f in final_flows]
                fig.data[0].link.target = [label_map[f.P_End] for f in final_flows]
                fig.data[0].link.value = flow_values
                fig.data[0].link.color = link_colors

            # Update layout with proper zoom and frame controls
            title_text = f"Material Flow Sankey - {element.upper()} ({year})"
            
            fig.update_layout(
                title_text=title_text,
                font_size=12,
                height=900,  # Reduced height
                width=1400,  # Reduced width
                margin=dict(l=100, r=100, b=100, t=120),  # Reduced margins
                dragmode='pan',
                hovermode='closest',
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
            )

    def export_plot():
        """Export the current plot as PNG with organized folder structure"""
        try:
            # Create export folder with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_folder = f"exports/sankey_diagrams/{timestamp}"
            os.makedirs(export_folder, exist_ok=True)
            
            # Generate filename with current parameters
            current_year = year_slider.value
            current_element = element_dropdown.value
            
            filename = f"sankey_{current_element}_{current_year}.png"
            filepath = os.path.join(export_folder, filename)
            
            # Ensure the figure has data before exporting
            if len(fig.data[0].node.label) > 0:
                # Export the plot with current dimensions
                fig.write_image(filepath, width=1400, height=900, scale=2)
                print(f"✅ Sankey diagram exported to: {filepath}")
                print(f"📁 Export folder: {export_folder}")
            else:
                print("⚠️ No data to export. Please select processes and ensure flows are visible.")
                
        except Exception as e:
            print(f"❌ Export failed: {e}")
            print("💡 Make sure kaleido is installed: pip install kaleido")
            import traceback
            traceback.print_exc()

    # Create widgets with better organization and longer sliders
    year_slider = IntSlider(
        min=time_items[0],
        max=time_items[-1],
        step=1,
        value=time_items[0],
        description="Year:",
        style={'description_width': '80px'},
        layout=Layout(width='400px')
    )
    
    element_dropdown = Dropdown(
        options=element_items, 
        value=element_items[0], 
        description="Element:",
        style={'description_width': '80px'},
        layout=Layout(width='200px')
    )
    
    # Multi-select process selector, all selected by default
    process_selector = SelectMultiple(
        options=all_process_names,
        value=tuple(all_process_names),
        description="Processes:",
        style={'description_width': '100px'},
        layout=Layout(width='400px')
    )
    
    threshold_slider = FloatSlider(
        min=0,
        max=max_flow_value,
        step=max_flow_value / 100,
        value=0,
        description="Min Flow:",
        continuous_update=False,
        readout_format=".2f",
        style={'description_width': '80px'},
        layout=Layout(width='400px')
    )
    
    export_button = Button(
        description="Export PNG",
        button_style='success',
        icon='download',
        layout=Layout(width='120px')
    )
    export_button.on_click(lambda b: export_plot())

    # Create legend
    legend_html = f"""
    <div style="margin: 10px; padding: 10px; border: 1px solid #ccc; border-radius: 5px; background-color: #f9f9f9;">
        <h4 style="margin: 0 0 10px 0;">Legend</h4>
        <div style="display: flex; flex-wrap: wrap; gap: 15px;">
            <div style="display: flex; align-items: center;">
                <div style="width: 20px; height: 20px; background-color: {process_colors['Regular']}; margin-right: 5px;"></div>
                <span>Regular Process</span>
            </div>
            <div style="display: flex; align-items: center;">
                <div style="width: 20px; height: 20px; background-color: {process_colors['DSM']}; margin-right: 5px;"></div>
                <span>DSM Process</span>
            </div>
            <div style="display: flex; align-items: center;">
                <div style="width: 20px; height: 20px; background-color: {process_colors['FOMP']}; margin-right: 5px;"></div>
                <span>FOMP Process</span>
            </div>
        </div>
        <div style="margin-top: 10px;">
            <strong>Element Colors:</strong>
            <div style="display: flex; flex-wrap: wrap; gap: 15px; margin-top: 5px;">
                <div style="display: flex; align-items: center;">
                    <div style="width: 20px; height: 20px; background-color: {element_colors['material']}; margin-right: 5px;"></div>
                    <span>Material</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="width: 20px; height: 20px; background-color: {element_colors['WC']}; margin-right: 5px;"></div>
                    <span>WC</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="width: 20px; height: 20px; background-color: {element_colors['DM']}; margin-right: 5px;"></div>
                    <span>DM</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="width: 20px; height: 20px; background-color: {element_colors['CC']}; margin-right: 5px;"></div>
                    <span>CC</span>
                </div>
            </div>
        </div>
    </div>
    """
    
    legend_widget = HTML(value=legend_html)

    # Set up interaction with all parameters
    
    ui = VBox([
        HBox([year_slider, element_dropdown]),
        HBox([process_selector, threshold_slider]),
        HBox([export_button]),
        legend_widget
    ])
    out = interactive(
        update_sankey,
        year=year_slider,
        element=element_dropdown,
        processes_to_show=process_selector,
        min_flow_value=threshold_slider
    )
    display(ui)
    display(fig)
    out.update()
