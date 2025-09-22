
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
from .validation import plot_optimized_mass_balance_error, plot_total_mass_balance_error
from .monte_carlo import plot_monte_carlo_integrated_dashboard, plot_mc_distribution
from .mc_visuals import plot_interactive_mc_histogram, plot_interactive_tornado
from .scenario import plot_multi_scenario_comparison

from .utils import plot_enhanced_export_options

# Publication-quality plotting modules
from .publication_style import (
    get_publication_layout,
    get_element_color,
    get_process_color,
    detect_biodym_process_type,
    create_color_sequence,
    get_export_filename,
    BIOYM_COLORS,
    ELEMENT_COLORS,
    PROCESS_COLORS,
    STATUS_COLORS
)
from .publication_export import (
    PublicationExporter,
    create_publication_export_widget,
    apply_publication_style,
    create_figure_summary,
    quick_export
)

# Re-export UI primitives for tests to patch/mocks
from ipywidgets import Button, HBox, interact  # noqa: F401
from IPython.display import display  # noqa: F401

# Flow chart plotting is handled by graphviz_flow_charts module
