# -*- coding: utf-8 -*-
"""
Monte Carlo Parameter Codelist System for BioDYM

This module provides user-friendly parameter selection for Monte Carlo uncertainty analysis.
Instead of requiring users to know exact parameter names, they can select parameters
by their meaning and the system automatically generates the correct parameter names.
"""

import pandas as pd
from typing import Dict, List, Tuple, Optional
import numpy as np


class MCParameterCodelist:
    """
    User-friendly parameter selection system for Monte Carlo uncertainty analysis.
    
    This class provides methods to:
    1. Generate parameter names automatically from user selections
    2. Validate parameter selections against the actual model
    3. Create uncertainty parameter definitions
    4. Provide user-friendly parameter descriptions
    """
    
    def __init__(self, mfa_system=None, dsm_params=None, fomp_params=None):
        """
        Initialize the parameter codelist system.
        
        Args:
            mfa_system: The MFA system object (optional, for validation)
            dsm_params: DSM parameters dictionary (optional)
            fomp_params: FOMP parameters dictionary (optional)
        """
        self.mfa_system = mfa_system
        self.dsm_params = dsm_params or {}
        self.fomp_params = fomp_params or {}
        
        # Initialize parameter codelists
        self._init_parameter_codelists()
    
    def _init_parameter_codelists(self):
        """Initialize all parameter codelists with user-friendly descriptions."""
        
        # 1. TRANSFER COEFFICIENTS
        self.tc_codelist = {
            'category': 'Transfer Coefficients',
            'description': 'Flow distribution coefficients between processes',
            'parameters': {}
        }
        
        # 2. DSM PARAMETERS
        self.dsm_codelist = {
            'category': 'Dynamic Stock Model',
            'description': 'Product lifetime and stock dynamics parameters',
            'parameters': {}
        }
        
        # 3. FOMP PARAMETERS
        self.fomp_codelist = {
            'category': 'First-Order Mineralization Process',
            'description': 'Organic matter decomposition parameters',
            'parameters': {}
        }
        
        # 4. STOCK PARAMETERS
        self.stock_codelist = {
            'category': 'Initial Stocks',
            'description': 'Initial stock values and composition',
            'parameters': {}
        }
        
        # 5. FLOW COMPOSITION PARAMETERS
        self.flow_codelist = {
            'category': 'Flow Composition',
            'description': 'Element composition in flows',
            'parameters': {}
        }
        
        # 6. STOCK-OUTFLOW PARAMETERS (BioDYM Extension)
        self.stock_outflow_codelist = {
            'category': 'Stock-Outflow Transfer Coefficients',
            'description': 'BioDYM extension: Stock consumption rates',
            'parameters': {}
        }
    
    def generate_tc_parameters(self, flows_df: pd.DataFrame) -> Dict:
        """
        Generate transfer coefficient parameters from flows data.
        
        Args:
            flows_df: DataFrame with flow definitions
            
        Returns:
            Dictionary of TC parameters with user-friendly names
        """
        tc_params = {}
        
        if flows_df is None or flows_df.empty:
            return tc_params
        
        for _, flow in flows_df.iterrows():
            if pd.notna(flow.get('Flow_ID')):
                flow_id = flow['Flow_ID']
                if flow_id.startswith('F_'):
                    # Extract process IDs from flow name (e.g., F_00_01 -> 00, 01)
                    parts = flow_id.split('_')
                    if len(parts) >= 3:
                        start_process = parts[1]
                        end_process = parts[2]
                        
                        # Generate TC parameter name
                        tc_name = f"TC_{start_process}_{end_process}"
                        
                        # Create user-friendly description
                        start_process_name = flow.get('Start_Process_Name', f'Process {start_process}')
                        end_process_name = flow.get('End_Process_Name', f'Process {end_process}')
                        
                        user_name = f"Transfer Coefficient: {start_process_name} → {end_process_name}"
                        
                        tc_params[tc_name] = {
                            'user_name': user_name,
                            'category': 'Transfer Coefficients',
                            'description': f'Flow distribution from {start_process_name} to {end_process_name}',
                            'default_value': flow.get('TC_Value', 0.5),
                            'typical_range': (0.0, 1.0),
                            'unit': 'fraction',
                            'validation_rules': ['0 ≤ value ≤ 1']
                        }
        
        return tc_params
    
    def generate_dsm_parameters(self) -> Dict:
        """
        Generate DSM parameters from DSM configuration.
        
        Returns:
            Dictionary of DSM parameters with user-friendly names
        """
        dsm_params = {}
        
        for process_id, params in self.dsm_params.items():
            process_name = f"Process {process_id}"
            
            # Lifetime parameters
            lifetimes = params.get('lifetimes', {})
            category_names = params.get('category_names', [])
            
            for i, (mean_lifetime, std_dev) in enumerate(zip(
                lifetimes.get('Mean', []), 
                lifetimes.get('StdDev', [])
            )):
                category_name = category_names[i] if i < len(category_names) else f"Category {i}"
                
                # Mean lifetime parameter
                mean_param = f"dsm_{process_id}_lifetimes_Mean_{i}"
                dsm_params[mean_param] = {
                    'user_name': f"DSM {process_name} - {category_name} - Mean Lifetime",
                    'category': 'Dynamic Stock Model',
                    'description': f'Average lifetime for {category_name} in {process_name}',
                    'default_value': mean_lifetime,
                    'typical_range': (1, 100),
                    'unit': 'years',
                    'validation_rules': ['value > 0']
                }
                
                # Standard deviation parameter
                std_param = f"dsm_{process_id}_lifetimes_StdDev_{i}"
                dsm_params[std_param] = {
                    'user_name': f"DSM {process_name} - {category_name} - Lifetime StdDev",
                    'category': 'Dynamic Stock Model',
                    'description': f'Lifetime standard deviation for {category_name} in {process_name}',
                    'default_value': std_dev,
                    'typical_range': (0.1, 20),
                    'unit': 'years',
                    'validation_rules': ['value ≥ 0']
                }
            
            # Inflow split parameters
            inflow_splits = params.get('inflow_split', [])
            for i, split in enumerate(inflow_splits):
                category_name = category_names[i] if i < len(category_names) else f"Category {i}"
                
                split_param = f"dsm_{process_id}_inflow_split_{i}"
                dsm_params[split_param] = {
                    'user_name': f"DSM {process_name} - {category_name} - Inflow Split",
                    'category': 'Dynamic Stock Model',
                    'description': f'Inflow fraction for {category_name} in {process_name}',
                    'default_value': split,
                    'typical_range': (0.0, 1.0),
                    'unit': 'fraction',
                    'validation_rules': ['0 ≤ value ≤ 1', 'sum of splits = 1.0']
                }
        
        return dsm_params
    
    def generate_fomp_parameters(self) -> Dict:
        """
        Generate FOMP parameters from FOMP configuration.
        
        Returns:
            Dictionary of FOMP parameters with user-friendly names
        """
        fomp_params = {}
        
        for process_id, params in self.fomp_params.items():
            process_name = f"Process {process_id}"
            
            # Decay rate parameters
            for param_name, value in params.items():
                if param_name in ['k1', 'k2', 'f']:
                    fomp_param = f"fomp_{process_id}_{param_name}"
                    
                    # User-friendly descriptions
                    descriptions = {
                        'k1': 'Fast pool decay rate',
                        'k2': 'Slow pool decay rate', 
                        'f': 'Fraction to fast pool'
                    }
                    
                    units = {
                        'k1': '1/year',
                        'k2': '1/year',
                        'f': 'fraction'
                    }
                    
                    ranges = {
                        'k1': (0.001, 0.1),
                        'k2': (0.0001, 0.01),
                        'f': (0.0, 1.0)
                    }
                    
                    fomp_params[fomp_param] = {
                        'user_name': f"FOMP {process_name} - {descriptions[param_name]}",
                        'category': 'First-Order Mineralization Process',
                        'description': f'{descriptions[param_name]} for {process_name}',
                        'default_value': value,
                        'typical_range': ranges[param_name],
                        'unit': units[param_name],
                        'validation_rules': ['value > 0' if param_name in ['k1', 'k2'] else '0 ≤ value ≤ 1']
                    }
        
        return fomp_params
    
    def generate_stock_parameters(self, stocks_df: pd.DataFrame) -> Dict:
        """
        Generate initial stock parameters from stocks data.
        
        Args:
            stocks_df: DataFrame with stock definitions
            
        Returns:
            Dictionary of stock parameters with user-friendly names
        """
        stock_params = {}
        
        if stocks_df is None or stocks_df.empty:
            return stock_params
        
        for _, stock in stocks_df.iterrows():
            process_id = stock.get('Process_ID')
            if pd.notna(process_id):
                process_name = stock.get('Process_Name', f'Process {process_id}')
                
                # Material stock
                material_param = f"Initial_Stock_material"
                stock_params[material_param] = {
                    'user_name': f"Initial Stock - {process_name} - Material",
                    'category': 'Initial Stocks',
                    'description': f'Initial material stock in {process_name}',
                    'default_value': stock.get('Initial_Stock_material', 0),
                    'typical_range': (0, 10000),
                    'unit': 'Mg',
                    'validation_rules': ['value ≥ 0']
                }
                
                # Element composition parameters
                for element in ['WC', 'DM', 'CC']:
                    comp_param = f"Initial_Stock_{element}"
                    stock_params[comp_param] = {
                        'user_name': f"Initial Stock - {process_name} - {element} Content",
                        'category': 'Initial Stocks',
                        'description': f'Initial {element} content in {process_name}',
                        'default_value': stock.get(f'Initial_Stock_{element}[%]', 0) / 100,
                        'typical_range': (0.0, 1.0),
                        'unit': 'fraction',
                        'validation_rules': ['0 ≤ value ≤ 1']
                    }
        
        return stock_params
    
    def generate_stock_outflow_parameters(self, stocks_df: pd.DataFrame) -> Dict:
        """
        Generate stock-outflow parameters from stocks data.
        
        Args:
            stocks_df: DataFrame with stock definitions
            
        Returns:
            Dictionary of stock-outflow parameters with user-friendly names
        """
        stock_outflow_params = {}
        
        if stocks_df is None or stocks_df.empty:
            return stock_outflow_params
        
        for _, stock in stocks_df.iterrows():
            if pd.notna(stock.get('Stock_Outflow_TC')):
                process_id = stock.get('Process_ID')
                destination_process = stock.get('Destination_Process')
                
                if pd.notna(process_id) and pd.notna(destination_process):
                    process_name = stock.get('Process_Name', f'Process {process_id}')
                    dest_name = f'Process {destination_process}'
                    
                    stc_param = f"STC_{process_id}_{destination_process}"
                    stock_outflow_params[stc_param] = {
                        'user_name': f"Stock Consumption Rate: {process_name} → {dest_name}",
                        'category': 'Stock-Outflow Transfer Coefficients',
                        'description': f'Annual consumption rate from {process_name} to {dest_name}',
                        'default_value': stock.get('Annual_Consumption_Rate', 0.1),
                        'typical_range': (0.0, 1.0),
                        'unit': '1/year',
                        'validation_rules': ['0 ≤ value ≤ 1']
                    }
        
        return stock_outflow_params
    
    def get_all_parameters(self, flows_df: pd.DataFrame = None, stocks_df: pd.DataFrame = None) -> Dict:
        """
        Get all available parameters with user-friendly names.
        
        Args:
            flows_df: DataFrame with flow definitions
            stocks_df: DataFrame with stock definitions
            
        Returns:
            Dictionary of all parameters organized by category
        """
        all_params = {}
        
        # Generate parameters from different sources
        all_params.update(self.generate_tc_parameters(flows_df))
        all_params.update(self.generate_dsm_parameters())
        all_params.update(self.generate_fomp_parameters())
        all_params.update(self.generate_stock_parameters(stocks_df))
        all_params.update(self.generate_stock_outflow_parameters(stocks_df))
        
        return all_params
    
    def create_uncertainty_definition(self, param_name: str, distribution: str, **kwargs) -> Dict:
        """
        Create an uncertainty parameter definition.
        
        Args:
            param_name: The parameter name
            distribution: Distribution type ('normal', 'uniform', 'triangular', 'lognormal')
            **kwargs: Distribution parameters
            
        Returns:
            Dictionary with uncertainty definition
        """
        definition = {'distribution': distribution}
        
        if distribution == 'normal':
            definition.update({
                'mean': kwargs.get('mean', 0),
                'std': kwargs.get('std', 1)
            })
        elif distribution == 'uniform':
            definition.update({
                'min': kwargs.get('min', 0),
                'max': kwargs.get('max', 1)
            })
        elif distribution == 'triangular':
            definition.update({
                'min': kwargs.get('min', 0),
                'mode': kwargs.get('mode', 0.5),
                'max': kwargs.get('max', 1)
            })
        elif distribution == 'lognormal':
            definition.update({
                'mean': kwargs.get('mean', 0),
                'std': kwargs.get('std', 1)
            })
        
        return definition
    
    def validate_parameter_selection(self, selected_params: List[str]) -> Tuple[bool, List[str]]:
        """
        Validate selected parameters against the actual model.
        
        Args:
            selected_params: List of parameter names to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        all_params = self.get_all_parameters()
        available_params = set(all_params.keys())
        
        errors = []
        for param in selected_params:
            if param not in available_params:
                errors.append(f"Parameter '{param}' not found in model")
        
        return len(errors) == 0, errors
    
    def get_parameter_categories(self) -> Dict[str, List[str]]:
        """
        Get parameters organized by category.
        
        Returns:
            Dictionary with categories as keys and parameter lists as values
        """
        all_params = self.get_all_parameters()
        categories = {}
        
        for param_name, param_info in all_params.items():
            category = param_info['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(param_name)
        
        return categories
    
    def export_to_excel_format(self, selected_params: List[str], 
                             distributions: Dict[str, str] = None,
                             **kwargs) -> pd.DataFrame:
        """
        Export selected parameters to Excel format for uncertainty analysis.
        
        Args:
            selected_params: List of parameter names
            distributions: Dictionary mapping parameter names to distribution types
            **kwargs: Additional distribution parameters
            
        Returns:
            DataFrame in Excel format for 4_1_Uncertainty_Parameters sheet
        """
        excel_data = []
        
        for param_name in selected_params:
            all_params = self.get_all_parameters()
            if param_name in all_params:
                param_info = all_params[param_name]
                
                # Get distribution type (default to normal)
                dist_type = distributions.get(param_name, 'normal') if distributions else 'normal'
                
                row = {
                    'Parameter_Name': param_name,
                    'Distribution': dist_type,
                    'Description': param_info['user_name'],
                    'Unit': param_info['unit'],
                    'Default_Value': param_info['default_value']
                }
                
                # Add distribution-specific parameters
                if dist_type == 'normal':
                    row.update({
                        'Mean': kwargs.get(f'{param_name}_mean', param_info['default_value']),
                        'StdDev': kwargs.get(f'{param_name}_std', param_info['default_value'] * 0.1)
                    })
                elif dist_type == 'uniform':
                    range_min, range_max = param_info['typical_range']
                    row.update({
                        'Min': kwargs.get(f'{param_name}_min', range_min),
                        'Max': kwargs.get(f'{param_name}_max', range_max)
                    })
                elif dist_type == 'triangular':
                    range_min, range_max = param_info['typical_range']
                    default_val = param_info['default_value']
                    row.update({
                        'Min': kwargs.get(f'{param_name}_min', range_min),
                        'Mode': kwargs.get(f'{param_name}_mode', default_val),
                        'Max': kwargs.get(f'{param_name}_max', range_max)
                    })
                
                excel_data.append(row)
        
        return pd.DataFrame(excel_data)


def create_user_friendly_mc_interface(mfa_system=None, dsm_params=None, fomp_params=None,
                                    flows_df=None, stocks_df=None):
    """
    Create a user-friendly interface for Monte Carlo parameter selection.
    
    Args:
        mfa_system: MFA system object
        dsm_params: DSM parameters dictionary
        fomp_params: FOMP parameters dictionary
        flows_df: Flows DataFrame
        stocks_df: Stocks DataFrame
        
    Returns:
        MCParameterCodelist object with all available parameters
    """
    codelist = MCParameterCodelist(mfa_system, dsm_params, fomp_params)
    
    # Generate all parameters
    all_params = codelist.get_all_parameters(flows_df, stocks_df)
    
    print(f"📊 Generated {len(all_params)} parameters for Monte Carlo analysis")
    print("\n📋 Available Parameter Categories:")
    
    categories = codelist.get_parameter_categories()
    for category, params in categories.items():
        print(f"   • {category}: {len(params)} parameters")
    
    return codelist


# Example usage functions
def example_parameter_selection():
    """Example of how to use the parameter codelist system."""
    
    # Create codelist (you would pass actual data here)
    codelist = MCParameterCodelist()
    
    # Get all available parameters
    all_params = codelist.get_all_parameters()
    
    # Example: Select some parameters
    selected_params = [
        'TC_03_04',  # Transfer coefficient
        'dsm_6_lifetimes_Mean_0',  # DSM lifetime
        'fomp_8_k1',  # FOMP decay rate
        'Initial_Stock_material'  # Initial stock
    ]
    
    # Validate selection
    is_valid, errors = codelist.validate_parameter_selection(selected_params)
    
    if is_valid:
        # Create uncertainty definitions
        uncertainty_params = {}
        for param in selected_params:
            uncertainty_params[param] = codelist.create_uncertainty_definition(
                param, 'normal', mean=0.5, std=0.1
            )
        
        # Export to Excel format
        excel_df = codelist.export_to_excel_format(selected_params)
        
        print("✅ Parameter selection valid")
        print("📊 Excel format ready for export")
        
        return uncertainty_params, excel_df
    else:
        print("❌ Parameter selection errors:")
        for error in errors:
            print(f"   {error}")
        
        return None, None


if __name__ == "__main__":
    # Run example
    uncertainty_params, excel_df = example_parameter_selection()
    
    if uncertainty_params:
        print("\n📋 Generated Uncertainty Parameters:")
        for param, definition in uncertainty_params.items():
            print(f"   {param}: {definition}")
        
        print("\n📊 Excel Format:")
        print(excel_df.to_string(index=False)) 