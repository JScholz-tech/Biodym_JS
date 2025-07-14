# -*- coding: utf-8 -*-
"""
User-Friendly Monte Carlo Parameter Selection Interface

This module provides an interactive interface for selecting Monte Carlo parameters
using the codelist system. Users can select parameters by their meaning and the
system automatically generates the correct parameter names and Excel format.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from ipywidgets import (
    SelectMultiple, Dropdown, Checkbox, Button, 
    VBox, HBox, HTML, Layout, Output
)
from IPython.display import display, clear_output
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .mc_parameter_codelist import MCParameterCodelist


class MCParameterSelector:
    """
    Interactive parameter selector for Monte Carlo uncertainty analysis.
    
    This class provides a user-friendly interface where users can:
    1. Browse available parameters by category
    2. Select parameters by their meaning (not technical names)
    3. Configure uncertainty distributions
    4. Export to Excel format
    """
    
    def __init__(self, mfa_system=None, dsm_params=None, fomp_params=None,
                 flows_df=None, stocks_df=None):
        """
        Initialize the parameter selector.
        
        Args:
            mfa_system: MFA system object
            dsm_params: DSM parameters dictionary
            fomp_params: FOMP parameters dictionary
            flows_df: Flows DataFrame
            stocks_df: Stocks DataFrame
        """
        self.codelist = MCParameterCodelist(mfa_system, dsm_params, fomp_params)
        self.flows_df = flows_df
        self.stocks_df = stocks_df
        
        # Get all available parameters
        self.all_params = self.codelist.get_all_parameters(flows_df, stocks_df)
        self.categories = self.codelist.get_parameter_categories()
        
        # Selected parameters and their configurations
        self.selected_params = {}
        self.param_configs = {}
        
        # Create widgets
        self._create_widgets()
    
    def _create_widgets(self):
        """Create the interactive widgets."""
        
        # Category selector
        self.category_dropdown = Dropdown(
            options=list(self.categories.keys()),
            value=list(self.categories.keys())[0] if self.categories else None,
            description='Parameter Category:',
            layout=Layout(width='400px')
        )
        
        # Parameter selector (multi-select)
        self.param_selector = SelectMultiple(
            options=[],
            description='Available Parameters:',
            layout=Layout(width='600px', height='200px')
        )
        
        # Distribution selector
        self.distribution_dropdown = Dropdown(
            options=['normal', 'uniform', 'triangular', 'lognormal'],
            value='normal',
            description='Distribution Type:',
            layout=Layout(width='200px')
        )
        
        # Parameter configuration widgets
        self.config_widgets = VBox([])
        
        # Action buttons
        self.add_button = Button(
            description='Add Selected Parameters',
            button_style='success',
            layout=Layout(width='200px')
        )
        
        self.remove_button = Button(
            description='Remove Selected',
            button_style='danger',
            layout=Layout(width='200px')
        )
        
        self.export_button = Button(
            description='Export to Excel',
            button_style='info',
            layout=Layout(width='200px')
        )
        
        # Selected parameters display
        self.selected_display = HTML(value="<h4>Selected Parameters:</h4><p>None</p>")
        
        # Output area
        self.output = Output()
        
        # Connect events
        self.category_dropdown.observe(self._on_category_change, names='value')
        self.add_button.on_click(self._on_add_parameters)
        self.remove_button.on_click(self._on_remove_parameters)
        self.export_button.on_click(self._on_export)
        
        # Initialize parameter list
        self._update_parameter_list()
    
    def _on_category_change(self, change):
        """Handle category selection change."""
        self._update_parameter_list()
    
    def _update_parameter_list(self):
        """Update the parameter list based on selected category."""
        category = self.category_dropdown.value
        if category and category in self.categories:
            params = self.categories[category]
            
            # Create user-friendly options
            options = []
            for param in params:
                if param in self.all_params:
                    param_info = self.all_params[param]
                    display_name = f"{param_info['user_name']} ({param})"
                    options.append((display_name, param))
            
            self.param_selector.options = options
        else:
            self.param_selector.options = []
    
    def _on_add_parameters(self, button):
        """Add selected parameters to the configuration."""
        selected_indices = self.param_selector.index
        category = self.category_dropdown.value
        
        if category and category in self.categories:
            params = self.categories[category]
            
            for idx in selected_indices:
                if idx < len(params):
                    param_name = params[idx]
                    if param_name in self.all_params:
                        param_info = self.all_params[param_name]
                        
                        # Add to selected parameters
                        self.selected_params[param_name] = {
                            'user_name': param_info['user_name'],
                            'category': param_info['category'],
                            'description': param_info['description'],
                            'unit': param_info['unit'],
                            'default_value': param_info['default_value'],
                            'distribution': self.distribution_dropdown.value
                        }
            
            self._update_selected_display()
            self._create_config_widgets()
    
    def _on_remove_parameters(self, button):
        """Remove selected parameters from configuration."""
        # For simplicity, remove all selected parameters
        # In a more sophisticated version, you could add individual removal
        self.selected_params.clear()
        self._update_selected_display()
        self._create_config_widgets()
    
    def _update_selected_display(self):
        """Update the display of selected parameters."""
        if not self.selected_params:
            html_content = "<h4>Selected Parameters:</h4><p>None</p>"
        else:
            html_content = "<h4>Selected Parameters:</h4><ul>"
            for param_name, config in self.selected_params.items():
                html_content += f"<li><strong>{config['user_name']}</strong> ({param_name})</li>"
            html_content += "</ul>"
        
        self.selected_display.value = html_content
    
    def _create_config_widgets(self):
        """Create configuration widgets for selected parameters."""
        # This would create individual configuration widgets for each parameter
        # For now, we'll use a simple approach
        pass
    
    def _on_export(self, button):
        """Export selected parameters to Excel format."""
        if not self.selected_params:
            with self.output:
                clear_output()
                print("❌ No parameters selected for export")
            return
        
        try:
            # Create uncertainty definitions
            uncertainty_params = {}
            for param_name, config in self.selected_params.items():
                param_info = self.all_params[param_name]
                
                # Create basic uncertainty definition
                uncertainty_params[param_name] = {
                    'distribution': config['distribution'],
                    'mean': param_info['default_value'],
                    'std': param_info['default_value'] * 0.1  # 10% uncertainty
                }
            
            # Export to Excel format
            excel_df = self.codelist.export_to_excel_format(
                list(self.selected_params.keys()),
                {param: config['distribution'] for param, config in self.selected_params.items()}
            )
            
            with self.output:
                clear_output()
                print("✅ Successfully exported parameters to Excel format")
                print(f"📊 Generated {len(excel_df)} parameter definitions")
                print("\n📋 Excel Format Preview:")
                print(excel_df.to_string(index=False))
                
                # Save to file
                excel_file = "mc_uncertainty_parameters.xlsx"
                excel_df.to_excel(excel_file, index=False)
                print(f"\n💾 Saved to: {excel_file}")
                
                # Show parameter summary
                print("\n📈 Parameter Summary:")
                for param_name, config in self.selected_params.items():
                    print(f"   • {config['user_name']}")
                    print(f"     Distribution: {config['distribution']}")
                    print(f"     Unit: {config['unit']}")
                    print(f"     Default: {config['default_value']}")
                
        except Exception as e:
            with self.output:
                clear_output()
                print(f"❌ Export error: {e}")
    
    def display(self):
        """Display the parameter selector interface."""
        # Main layout
        main_layout = VBox([
            HTML("<h3>🎲 Monte Carlo Parameter Selector</h3>"),
            HTML("<p>Select parameters by category and add them to your uncertainty analysis.</p>"),
            
            # Category and parameter selection
            HBox([
                VBox([
                    self.category_dropdown,
                    self.param_selector
                ]),
                VBox([
                    self.distribution_dropdown,
                    self.add_button,
                    self.remove_button
                ])
            ]),
            
            # Selected parameters
            self.selected_display,
            
            # Configuration area
            self.config_widgets,
            
            # Export button
            self.export_button,
            
            # Output area
            self.output
        ])
        
        display(main_layout)
    
    def get_uncertainty_params(self) -> Dict:
        """Get the uncertainty parameters dictionary."""
        uncertainty_params = {}
        
        for param_name, config in self.selected_params.items():
            param_info = self.all_params[param_name]
            
            # Create uncertainty definition
            definition = {
                'distribution': config['distribution']
            }
            
            if config['distribution'] == 'normal':
                definition.update({
                    'mean': param_info['default_value'],
                    'std': param_info['default_value'] * 0.1
                })
            elif config['distribution'] == 'uniform':
                min_val, max_val = param_info['typical_range']
                definition.update({
                    'min': min_val,
                    'max': max_val
                })
            elif config['distribution'] == 'triangular':
                min_val, max_val = param_info['typical_range']
                definition.update({
                    'min': min_val,
                    'mode': param_info['default_value'],
                    'max': max_val
                })
            
            uncertainty_params[param_name] = definition
        
        return uncertainty_params
    
    def get_excel_dataframe(self) -> pd.DataFrame:
        """Get the Excel format DataFrame."""
        return self.codelist.export_to_excel_format(
            list(self.selected_params.keys()),
            {param: config['distribution'] for param, config in self.selected_params.items()}
        )


def create_mc_parameter_interface(mfa_system=None, dsm_params=None, fomp_params=None,
                                flows_df=None, stocks_df=None):
    """
    Create and display the Monte Carlo parameter selection interface.
    
    Args:
        mfa_system: MFA system object
        dsm_params: DSM parameters dictionary
        fomp_params: FOMP parameters dictionary
        flows_df: Flows DataFrame
        stocks_df: Stocks DataFrame
        
    Returns:
        MCParameterSelector object
    """
    selector = MCParameterSelector(mfa_system, dsm_params, fomp_params, flows_df, stocks_df)
    selector.display()
    return selector


def quick_mc_setup(mfa_system=None, dsm_params=None, fomp_params=None,
                   flows_df=None, stocks_df=None, 
                   common_params: List[str] = None) -> Dict:
    """
    Quick setup for common Monte Carlo parameters.
    
    Args:
        mfa_system: MFA system object
        dsm_params: DSM parameters dictionary
        fomp_params: FOMP parameters dictionary
        flows_df: Flows DataFrame
        stocks_df: Stocks DataFrame
        common_params: List of common parameter types to include
        
    Returns:
        Dictionary of uncertainty parameters
    """
    codelist = MCParameterCodelist(mfa_system, dsm_params, fomp_params)
    all_params = codelist.get_all_parameters(flows_df, stocks_df)
    
    # Default common parameters if none specified
    if common_params is None:
        common_params = ['Transfer Coefficients', 'Dynamic Stock Model']
    
    # Select parameters from common categories
    selected_params = []
    for category in common_params:
        if category in codelist.get_parameter_categories():
            params = codelist.get_parameter_categories()[category]
            # Take first few parameters from each category
            selected_params.extend(params[:3])  # Limit to 3 per category
    
    # Create uncertainty definitions
    uncertainty_params = {}
    for param_name in selected_params:
        if param_name in all_params:
            param_info = all_params[param_name]
            
            # Create basic uncertainty definition
            uncertainty_params[param_name] = {
                'distribution': 'normal',
                'mean': param_info['default_value'],
                'std': param_info['default_value'] * 0.1  # 10% uncertainty
            }
    
    return uncertainty_params


# Example usage
def example_usage():
    """Example of how to use the MC parameter interface."""
    
    print("🎲 Monte Carlo Parameter Selection Example")
    print("=" * 50)
    
    # Create a simple example
    codelist = MCParameterCodelist()
    
    # Get all parameters
    all_params = codelist.get_all_parameters()
    
    print(f"📊 Available parameters: {len(all_params)}")
    
    # Show categories
    categories = codelist.get_parameter_categories()
    for category, params in categories.items():
        print(f"   • {category}: {len(params)} parameters")
    
    # Quick setup example
    quick_params = quick_mc_setup()
    print(f"\n⚡ Quick setup generated {len(quick_params)} parameters")
    
    return quick_params


if __name__ == "__main__":
    # Run example
    example_params = example_usage()
    
    if example_params:
        print("\n📋 Generated Parameters:")
        for param, definition in example_params.items():
            print(f"   {param}: {definition}") 