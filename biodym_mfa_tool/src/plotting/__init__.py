
# -*- coding: utf-8 -*-
"""
Plotting Module

This __init__.py file makes the plotting functions available
from the `plotting` package.
"""

from .sankey import plot_interactive_sankey
from .circular_sankey import plot_circular_sankey, plot_sankey_circular
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
from .validation import plot_mass_balance_error, plot_optimized_mass_balance_error, plot_total_mass_balance_error
from .monte_carlo import plot_monte_carlo_integrated_dashboard, plot_mc_distribution
from .mc_visuals import plot_interactive_mc_histogram, plot_interactive_tornado
from .scenario import plot_multi_scenario_comparison

from .utils import plot_enhanced_export_options

# Re-export UI primitives for tests to patch/mocks
from ipywidgets import Button, HBox, interact  # noqa: F401
from IPython.display import display  # noqa: F401

# Flow chart plotting - using Graphviz functions instead
# from .flow_charts import (
#     plot_simple_flow_chart_from_excel,
#     plot_interactive_flow_chart_from_excel,
#     plot_system_architecture_from_excel,
#     create_flow_chart_export_controls
# )

# Legacy functions removed for cleanup - use plot_graphviz_flow_chart_sankey_style instead
