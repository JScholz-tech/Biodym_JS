# -*- coding: utf-8 -*-
"""
Functions for plotting flow composition data.
"""

import plotly.graph_objects as go

def plot_flow_composition(mfa_system_results):
    """
    Creates an interactive stacked bar chart to visualize the composition of each flow.

    Parameters
    ----------
    mfa_system_results : odym.MFAsystem
        The solved MFA system object containing flow and stock results.

    Returns
    -------
    plotly.graph_objects.Figure
        The Plotly figure object for the composition plot.
    """
    flows = mfa_system_results.FlowDict
    years = mfa_system_results.IndexTable.Classification['Time'].Items
    elements = mfa_system_results.Elements

    fig = go.Figure()

    for i, year in enumerate(years):
        flow_names = []
        wc_percentages = []
        cc_percentages = []
        non_carbon_dm_percentages = []

        for flow_name, flow in flows.items():
            values = flow.Values[i, :]
            
            # Phase 1b: Handle new element structure safely
            wc_val = values[elements.index('WC')] if 'WC' in elements else 0
            dm_val = values[elements.index('DM')] if 'DM' in elements else 0
            cc_val = values[elements.index('CC')] if 'CC' in elements else 0

            total_mass = wc_val + dm_val

            if total_mass > 0:
                flow_names.append(flow_name)
                wc_percentages.append(wc_val / total_mass * 100)
                cc_percentages.append(cc_val / total_mass * 100)
                non_carbon_dm_percentages.append((dm_val - cc_val) / total_mass * 100)

        fig.add_trace(
            go.Bar(
                y=flow_names,
                x=wc_percentages,
                name='Water Content (WC)',
                orientation='h',
                marker=dict(color='#007BFF'),
                visible=(i == 0)  # Only the first year is visible initially
            )
        )
        fig.add_trace(
            go.Bar(
                y=flow_names,
                x=cc_percentages,
                name='Carbon Content (CC)',
                orientation='h',
                marker=dict(color='#FF4444'),
                visible=(i == 0)
            )
        )
        fig.add_trace(
            go.Bar(
                y=flow_names,
                x=non_carbon_dm_percentages,
                name='Non-Carbon Dry Matter',
                orientation='h',
                marker=dict(color='#FF8C00'),
                visible=(i == 0)
            )
        )

    steps = []
    for i, year in enumerate(years):
        step = dict(
            method="update",
            args=[{"visible": [(i * 3 <= j < (i + 1) * 3) for j in range(len(fig.data))]}],
            label=str(year)
        )
        steps.append(step)

    sliders = [dict(
        active=0,
        currentvalue={"prefix": "Year: "},
        pad={"t": 50},
        steps=steps
    )]

    fig.update_layout(
        barmode='stack',
        title_text='Flow Composition by Year',
        xaxis_title='Composition (%)',
        yaxis_title='Flows',
        sliders=sliders
    )

    return fig
