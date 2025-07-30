
# -*- coding: utf-8 -*-
"""
Plotting Module

This __init__.py file makes the plotting functions available
from the `plotting` package.
"""

from .sankey import plot_interactive_sankey
from .dynamics import (
    plot_process_dynamics,
    
    plot_dynamic_stock_composition,
    plot_fomp_dynamics,
    plot_flow_dynamics,
    plot_dsm_stock_details,
    plot_fomp_stock_details,
    plot_system_efficiency_metrics,
    plot_stock_overview,
    plot_summary_dashboard,
    plot_stock_bar_chart,
)
from .validation import plot_mass_balance_error, plot_optimized_mass_balance_error
from .monte_carlo import plot_monte_carlo_integrated_dashboard, plot_mc_distribution
from .mc_visuals import plot_interactive_mc_histogram, plot_interactive_tornado
from .scenario import plot_scenario_comparison
from .utils import plot_enhanced_export_options

# Flow chart plotting - using Graphviz functions instead
# from .flow_charts import (
#     plot_simple_flow_chart_from_excel,
#     plot_interactive_flow_chart_from_excel,
#     plot_system_architecture_from_excel,
#     create_flow_chart_export_controls
# )

# Legacy function names for backward compatibility
def plot_flow_chart(mfa_system_results, title="System Flow Chart", layout_type="hierarchical"):
    """
    Legacy function for backward compatibility.
    Creates a flow chart from MFA system results.
    
    Args:
        mfa_system_results (odym.MFAsystem): The solved MFA system object.
        title (str): Title for the flow chart.
        layout_type (str): Layout type.
    
    Returns:
        tuple: (matplotlib figure, networkx graph)
    """
    print("⚠️ Legacy plot_flow_chart called. Consider using plot_graphviz_flow_chart_sankey_style instead.")
    return None, None

def plot_interactive_flow_chart(mfa_system_results, title="Interactive System Flow Chart"):
    """
    Legacy function for backward compatibility.
    Creates an interactive flow chart from MFA system results.
    
    Args:
        mfa_system_results (odym.MFAsystem): The solved MFA system object.
        title (str): Title for the flow chart.
    
    Returns:
        plotly.graph_objects.Figure: Interactive flow chart.
    """
    print("⚠️ Legacy plot_interactive_flow_chart called. Consider using plot_graphviz_flow_chart_sankey_style instead.")
    return None

def plot_system_architecture_diagram(mfa_system_results, title="System Architecture"):
    """
    Legacy function for backward compatibility.
    Creates a system architecture diagram from MFA system results.
    
    Args:
        mfa_system_results (odym.MFAsystem): The solved MFA system object.
        title (str): Title for the diagram.
    
    Returns:
        plotly.graph_objects.Figure: System architecture diagram.
    """
    print("⚠️ Legacy plot_system_architecture_diagram called. Consider using plot_graphviz_flow_chart_sankey_style instead.")
    return None
