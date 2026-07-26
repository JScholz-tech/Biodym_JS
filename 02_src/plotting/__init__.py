# -*- coding: utf-8 -*-
"""
Plotting Subpackage for BioDYM.
"""

# Import key plotting functions for easy access
from .themes import (
    set_theme,
    get_active_theme,
    get_theme,
    apply_theme,
    get_mass_display,
    y_label,
    set_mass_unit_from_config,
)
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
    plot_component_replacement_rate,
    plot_fomp_dynamics,
    plot_flow_dynamics,
    plot_stock_bar_chart,
    plot_system_stock_composition,
    plot_lfg_gas_production,
    plot_lfg_stock_details,
    plot_lfg_fraction_breakdown,
    plot_lfg_ipcc_vs_mfa_comparison,
    plot_bom_assembly_flows,
)
from .validation import (
    plot_optimized_mass_balance_error,
    plot_total_mass_balance_error,
    plot_dynamic_process_balance,
)
from .monte_carlo import (
    plot_interactive_mc_histogram,
    plot_interactive_tornado,
    plot_interactive_mc_paths,
    plot_interactive_mc_stock_comparison,
    plot_interactive_mc_multiple_histograms,
    plot_interactive_mc_boxplot,
)
from .scenario import (
    plot_multi_scenario_comparison,
    plot_scenario_flow_dynamics,
    plot_scenario_stock_dynamics,
    plot_scenario_stock_publication,
)
from .graphviz_flow_charts import plot_graphviz_flow_chart_sankey_style
from .sankey import (
    export_sankey_json,
    export_sankey_html,
    export_sankey_csv,
    export_sankey_sankeymatic,
    export_mfa_diagram_xlsx,
)
from . import sankey_config as _sankey_config


def set_sankey_title_from_config(config_obj) -> None:
    """Set the Sankey diagram title from the configuration object.

    Call once after load_configuration()/load_config_from_yaml(), like
    set_mass_unit_from_config(). Reads the resolved ``Sankey_Title`` (which the
    YAML loader fills from the study's sankey_title, falling back to its name);
    a blank value keeps the generic default.
    """
    title = None
    for attr in ("Sankey_Title", "SANKEY_TITLE", "Name", "name"):
        val = getattr(config_obj, attr, None)
        if val and isinstance(val, str) and val.strip():
            title = val.strip()
            break
    _sankey_config.set_title(title)

__all__ = [
    "set_theme",
    "get_active_theme",
    "get_theme",
    "apply_theme",
    "get_mass_display",
    "y_label",
    "set_mass_unit_from_config",
    "set_sankey_title_from_config",
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
    "plot_component_replacement_rate",
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
    "plot_interactive_mc_boxplot",
    "plot_multi_scenario_comparison",
    "plot_scenario_flow_dynamics",
    "plot_scenario_stock_dynamics",
    "plot_scenario_stock_publication",
    "plot_graphviz_flow_chart_sankey_style",
    "plot_lfg_gas_production",
    "plot_lfg_stock_details",
    "plot_lfg_fraction_breakdown",
    "plot_lfg_ipcc_vs_mfa_comparison",
    "plot_bom_assembly_flows",
    "export_sankey_json",
    "export_sankey_html",
    "export_sankey_csv",
    "export_sankey_sankeymatic",
    "export_mfa_diagram_xlsx",
]
