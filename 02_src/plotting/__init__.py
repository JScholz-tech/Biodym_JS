# -*- coding: utf-8 -*-
"""
Plotting Subpackage for BioDYM.
"""

# Import key plotting functions for easy access
from .themes import set_theme, get_active_theme, get_theme, apply_theme, get_mass_display, y_label
from .sankey import plot_interactive_sankey
from .enhanced_sankey import plot_enhanced_sankey, plot_element_multiplot_sankey
from .dynamics import (
    plot_dsm_stock_details,
    plot_dsm_stock_publication,
    plot_dsm_process_dynamics,
    plot_fomp_stock_details,
    plot_fomp_stock_comparison,
    plot_fomp_pool_breakdown,
    plot_system_efficiency_metrics,
    plot_stock_overview,
    plot_process_dynamics,
    plot_dynamic_stock_composition,
    plot_fomp_dynamics,
    plot_flow_dynamics,
    plot_stock_bar_chart,
    plot_system_stock_composition,
    plot_lfg_gas_production,
    plot_lfg_stock_details,
    plot_lfg_fraction_breakdown,
    plot_lfg_ipcc_vs_mfa_comparison,
)
from .validation import plot_optimized_mass_balance_error, plot_total_mass_balance_error, plot_dynamic_process_balance
from .monte_carlo import (
    plot_interactive_mc_histogram,
    plot_interactive_tornado,
    plot_interactive_mc_paths,
    plot_interactive_mc_stock_comparison,
    plot_interactive_mc_multiple_histograms,
)
from .scenario import (
    plot_multi_scenario_comparison,
    plot_scenario_flow_dynamics,
    plot_scenario_stock_dynamics,
)
from .graphviz_flow_charts import plot_graphviz_flow_chart_sankey_style

__all__ = [
    "set_theme",
    "get_active_theme",
    "get_theme",
    "apply_theme",
    "get_mass_display",
    "y_label",
    "plot_interactive_sankey",
    "plot_enhanced_sankey",
    "plot_element_multiplot_sankey",
    "plot_dsm_stock_details",
    "plot_dsm_stock_publication",
    "plot_dsm_process_dynamics",
    "plot_fomp_stock_details",
    "plot_fomp_stock_comparison",
    "plot_fomp_pool_breakdown",
    "plot_system_efficiency_metrics",
    "plot_stock_overview",
    "plot_process_dynamics",
    "plot_dynamic_stock_composition",
    "plot_fomp_dynamics",
    "plot_flow_dynamics",
    "plot_stock_bar_chart",
    "plot_system_stock_composition",
    "plot_optimized_mass_balance_error",
    "plot_total_mass_balance_error",
    "plot_dynamic_process_balance",
    "plot_interactive_mc_histogram",
    "plot_interactive_tornado",
    "plot_interactive_mc_paths",
    "plot_interactive_mc_stock_comparison",
    "plot_interactive_mc_multiple_histograms",
    "plot_multi_scenario_comparison",
    "plot_scenario_flow_dynamics",
    "plot_scenario_stock_dynamics",
    "plot_graphviz_flow_chart_sankey_style",
    "plot_lfg_gas_production",
    "plot_lfg_stock_details",
    "plot_lfg_fraction_breakdown",
    "plot_lfg_ipcc_vs_mfa_comparison",
]
