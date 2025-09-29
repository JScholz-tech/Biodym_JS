# -*- coding: utf-8 -*-
"""
Plotting Subpackage for BioDYM.
"""

# Import key plotting functions for easy access
from .sankey import plot_interactive_sankey
from .dynamics import (
    plot_dsm_stock_details,
    plot_fomp_stock_details,
    plot_system_efficiency_metrics,
    plot_stock_overview,
    plot_summary_dashboard,
    plot_process_dynamics,
    plot_dynamic_stock_composition,
    plot_fomp_dynamics,
    plot_flow_dynamics,
    plot_stock_bar_chart,
    plot_system_stock_composition,
)
from .validation import plot_optimized_mass_balance_error, plot_total_mass_balance_error
from .monte_carlo import (
    plot_interactive_mc_histogram,
    plot_interactive_tornado,
    plot_interactive_mc_paths,
)
from .scenario import plot_multi_scenario_comparison, plot_scenario_flow_dynamics
from .graphviz_flow_charts import plot_graphviz_flow_chart_sankey_style

__all__ = [
    'plot_interactive_sankey',
    'plot_dsm_stock_details',
    'plot_fomp_stock_details',
    'plot_system_efficiency_metrics',
    'plot_stock_overview',
    'plot_summary_dashboard',
    'plot_process_dynamics',
    'plot_dynamic_stock_composition',
    'plot_fomp_dynamics',
    'plot_flow_dynamics',
    'plot_stock_bar_chart',
    'plot_system_stock_composition',
    'plot_optimized_mass_balance_error',
    'plot_total_mass_balance_error',
    'plot_interactive_mc_histogram',
    'plot_interactive_tornado',
    'plot_interactive_mc_paths',
    'plot_multi_scenario_comparison',
    'plot_scenario_flow_dynamics',
    'plot_graphviz_flow_chart_sankey_style',
]