# -*- coding: utf-8 -*-
"""
Utility functions for the BioDYM MFA Model.

This file contains helper functions for data processing, parameter sampling,
and result export functionality.
"""
import numpy as np
import pandas as pd
import json
import os
from datetime import datetime


def sample_parameters(uncertainty_params):
    """
    Samples parameter values from their uncertainty distributions.

    Args:
        uncertainty_params (dict): Dictionary containing uncertainty parameter definitions.

    Returns:
        dict: Dictionary with parameter names as keys and sampled values as values.
    """
    sampled_values = {}
    
    for param_name, param_def in uncertainty_params.items():
        distribution = param_def.get('distribution', 'normal')
        mean = param_def.get('mean', 0)
        std = param_def.get('std', 1)
        min_val = param_def.get('min', None)
        max_val = param_def.get('max', None)
        
        if distribution == 'normal':
            value = np.random.normal(mean, std)
        elif distribution == 'uniform':
            value = np.random.uniform(min_val, max_val)
        elif distribution == 'lognormal':
            value = np.random.lognormal(mean, std)
        else:
            value = mean  # Default to mean if distribution not recognized
        
        # Apply bounds if specified
        if min_val is not None:
            value = max(value, min_val)
        if max_val is not None:
            value = min(value, max_val)
        
        sampled_values[param_name] = value
    
    return sampled_values


def export_results_to_excel(mfa_system_results, output_path):
    """
    Exports MFA system results to an Excel file with multiple sheets.

    Args:
        mfa_system_results (odym.MFAsystem): The solved MFA system object.
        output_path (str): Path where the Excel file should be saved.
    """
    print(f"--> Exporting results to '{output_path}'...")
    
    time_index = mfa_system_results.IndexTable.Classification['Time'].Items
    elements = mfa_system_results.Elements
    
    with pd.ExcelWriter(output_path) as writer:
        # --- Export Flows ---
        flow_data_rows = []
        for name, flow_obj in mfa_system_results.FlowDict.items():
            for year_idx, year in enumerate(time_index):
                row = {'Flow': name, 'Year': year}
                for elem_idx, element in enumerate(elements):
                    row[f'{element}'] = flow_obj.Values[year_idx, elem_idx]
                flow_data_rows.append(row)
        
        flow_df = pd.DataFrame(flow_data_rows)
        flow_df.to_excel(writer, sheet_name='Flows', index=False)
        
        # --- Export Stocks ---
        stock_data_rows = []
        for name, stock_obj in mfa_system_results.StockDict.items():
            for year_idx, year in enumerate(time_index):
                row = {'Stock': name, 'Year': year}
                for elem_idx, element in enumerate(elements):
                    row[f'{element}'] = stock_obj.Values[year_idx, elem_idx]
                stock_data_rows.append(row)
        
        stock_df = pd.DataFrame(stock_data_rows)
        stock_df.to_excel(writer, sheet_name='Stocks', index=False)
        
        # --- Export Parameters ---
        param_data_rows = []
        for name, param_obj in mfa_system_results.ParameterDict.items():
            row = {'Parameter': name, 'Value': param_obj.Values}
            param_data_rows.append(row)
        
        param_df = pd.DataFrame(param_data_rows)
        param_df.to_excel(writer, sheet_name='Parameters', index=False)
        
        # --- Export Summary ---
        summary_data = {
            'Metric': ['Total Processes', 'Total Flows', 'Total Stocks', 'Time Range', 'Elements'],
            'Value': [
                len(mfa_system_results.ProcessList),
                len(mfa_system_results.FlowDict),
                len([s for s in mfa_system_results.StockDict.keys() if s.startswith('S_')]),
                f"{time_index[0]} - {time_index[-1]}",
                ', '.join(elements)
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)


class ScenarioManager:
    """
    Manages different scenarios for MFA analysis.
    Allows saving, loading, and comparing different parameter configurations.
    """
    
    def __init__(self, scenarios_dir='scenarios'):
        """
        Initialize the scenario manager.
        
        Args:
            scenarios_dir (str): Directory to store scenario files.
        """
        self.scenarios_dir = scenarios_dir
        self.scenarios = {}
        self._ensure_scenarios_dir()
        self._load_existing_scenarios()
    
    def _ensure_scenarios_dir(self):
        """Create scenarios directory if it doesn't exist."""
        if not os.path.exists(self.scenarios_dir):
            os.makedirs(self.scenarios_dir)
    
    def _load_existing_scenarios(self):
        """Load existing scenario files from disk."""
        if os.path.exists(self.scenarios_dir):
            for filename in os.listdir(self.scenarios_dir):
                if filename.endswith('.json'):
                    scenario_name = filename[:-5]  # Remove .json extension
                    try:
                        with open(os.path.join(self.scenarios_dir, filename), 'r') as f:
                            self.scenarios[scenario_name] = json.load(f)
                    except Exception as e:
                        print(f"Warning: Could not load scenario {scenario_name}: {e}")
    
    def save_scenario(self, scenario_name, config, description=""):
        """
        Save a scenario configuration to disk.
        
        Args:
            scenario_name (str): Name of the scenario.
            config (object): Configuration object (e.g., AnalysisConfig).
            description (str): Optional description of the scenario.
        """
        # Convert config object to dictionary
        config_dict = {}
        for attr in dir(config):
            if not attr.startswith('_') and not callable(getattr(config, attr)):
                config_dict[attr] = getattr(config, attr)
        
        scenario_data = {
            'name': scenario_name,
            'description': description,
            'created': datetime.now().isoformat(),
            'config': config_dict
        }
        
        self.scenarios[scenario_name] = scenario_data
        
        # Save to file
        filename = os.path.join(self.scenarios_dir, f"{scenario_name}.json")
        with open(filename, 'w') as f:
            json.dump(scenario_data, f, indent=2)
        
        print(f"✅ Scenario '{scenario_name}' saved successfully.")
    
    def load_scenario(self, scenario_name):
        """
        Load a scenario configuration.
        
        Args:
            scenario_name (str): Name of the scenario to load.
            
        Returns:
            dict: Scenario configuration dictionary.
        """
        if scenario_name not in self.scenarios:
            raise ValueError(f"Scenario '{scenario_name}' not found.")
        
        return self.scenarios[scenario_name]['config']
    
    def list_scenarios(self):
        """
        List all available scenarios.
        
        Returns:
            list: List of scenario names and descriptions.
        """
        scenario_list = []
        for name, data in self.scenarios.items():
            scenario_list.append({
                'name': name,
                'description': data.get('description', ''),
                'created': data.get('created', '')
            })
        return scenario_list
    
    def delete_scenario(self, scenario_name):
        """
        Delete a scenario.
        
        Args:
            scenario_name (str): Name of the scenario to delete.
        """
        if scenario_name not in self.scenarios:
            raise ValueError(f"Scenario '{scenario_name}' not found.")
        
        # Remove from memory
        del self.scenarios[scenario_name]
        
        # Remove file
        filename = os.path.join(self.scenarios_dir, f"{scenario_name}.json")
        if os.path.exists(filename):
            os.remove(filename)
        
        print(f"✅ Scenario '{scenario_name}' deleted successfully.")
    
    def create_scenario_from_config(self, scenario_name, config, description=""):
        """
        Create a new scenario from an existing configuration.
        
        Args:
            scenario_name (str): Name for the new scenario.
            config (object): Configuration object to base the scenario on.
            description (str): Description of the scenario.
            
        Returns:
            dict: The created scenario configuration.
        """
        # Create a copy of the config
        config_dict = {}
        for attr in dir(config):
            if not attr.startswith('_') and not callable(getattr(config, attr)):
                config_dict[attr] = getattr(config, attr)
        
        # Save the scenario
        self.save_scenario(scenario_name, config, description)
        
        return config_dict
    
    def compare_scenarios(self, scenario_names):
        """
        Compare multiple scenarios.
        
        Args:
            scenario_names (list): List of scenario names to compare.
            
        Returns:
            dict: Comparison data.
        """
        if len(scenario_names) < 2:
            raise ValueError("Need at least 2 scenarios for comparison.")
        
        comparison = {}
        for name in scenario_names:
            if name not in self.scenarios:
                raise ValueError(f"Scenario '{name}' not found.")
            
            config = self.scenarios[name]['config']
            comparison[name] = {
                'description': self.scenarios[name].get('description', ''),
                'config': config
            }
        
        return comparison

    def create_scenario_comparison_plot(self, scenario_names, comparison_metrics=None):
        """
        Create a comparison plot for multiple scenarios.
        
        Args:
            scenario_names (list): List of scenario names to compare.
            comparison_metrics (list, optional): List of metrics to compare.
            
        Returns:
            dict: Comparison data with plots.
        """
        if len(scenario_names) < 2:
            raise ValueError("Need at least 2 scenarios for comparison.")
        
        comparison_data = self.compare_scenarios(scenario_names)
        
        # Default comparison metrics
        if comparison_metrics is None:
            comparison_metrics = [
                'Start Year', 'End Year', 'Monte Carlo Iterations',
                'Run DSM Calculation', 'Run FOMP Calculation'
            ]
        
        # Extract metric values for each scenario
        metric_data = {}
        for metric in comparison_metrics:
            metric_data[metric] = {}
            for scenario_name in scenario_names:
                config = comparison_data[scenario_name]['config']
                value = config.get(metric, 'N/A')
                metric_data[metric][scenario_name] = value
        
        return {
            'scenarios': comparison_data,
            'metrics': metric_data,
            'scenario_names': scenario_names
        }

    def export_scenario_comparison(self, scenario_names, output_path=None):
        """
        Export scenario comparison to Excel.
        
        Args:
            scenario_names (list): List of scenario names to compare.
            output_path (str, optional): Output file path.
            
        Returns:
            str: Path to exported file.
        """
        if output_path is None:
            output_path = f"scenarios/scenario_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        comparison_data = self.create_scenario_comparison_plot(scenario_names)
        
        with pd.ExcelWriter(output_path) as writer:
            # Summary sheet
            summary_data = []
            for scenario_name in scenario_names:
                scenario_info = comparison_data['scenarios'][scenario_name]
                summary_data.append({
                    'Scenario': scenario_name,
                    'Description': scenario_info['description'],
                    'Created': scenario_info.get('created', 'Unknown')
                })
            
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
            
            # Metrics comparison sheet
            metrics_data = []
            for metric, values in comparison_data['metrics'].items():
                row = {'Metric': metric}
                for scenario_name in scenario_names:
                    row[scenario_name] = values.get(scenario_name, 'N/A')
                metrics_data.append(row)
            
            pd.DataFrame(metrics_data).to_excel(writer, sheet_name='Metrics_Comparison', index=False)
            
            # Individual scenario sheets
            for scenario_name in scenario_names:
                scenario_config = comparison_data['scenarios'][scenario_name]['config']
                config_df = pd.DataFrame(list(scenario_config.items()), columns=['Parameter', 'Value'])
                config_df.to_excel(writer, sheet_name=f'Scenario_{scenario_name}', index=False)
        
        print(f"✅ Scenario comparison exported to: {output_path}")
        return output_path

    def get_scenario_differences(self, scenario_names):
        """
        Get differences between scenarios.
        
        Args:
            scenario_names (list): List of scenario names to compare.
            
        Returns:
            dict: Differences between scenarios.
        """
        if len(scenario_names) != 2:
            raise ValueError("This function compares exactly 2 scenarios.")
        
        scenario1, scenario2 = scenario_names
        config1 = self.scenarios[scenario1]['config']
        config2 = self.scenarios[scenario2]['config']
        
        differences = {}
        all_keys = set(config1.keys()) | set(config2.keys())
        
        for key in all_keys:
            val1 = config1.get(key, 'N/A')
            val2 = config2.get(key, 'N/A')
            
            if val1 != val2:
                differences[key] = {
                    scenario1: val1,
                    scenario2: val2,
                    'different': True
                }
            else:
                differences[key] = {
                    scenario1: val1,
                    scenario2: val2,
                    'different': False
                }
        
        return differences

    def create_scenario_ranking(self, scenario_names, ranking_criteria=None):
        """
        Create a ranking of scenarios based on specified criteria.
        
        Args:
            scenario_names (list): List of scenario names to rank.
            ranking_criteria (dict, optional): Criteria for ranking with weights.
            
        Returns:
            dict: Ranking results.
        """
        if ranking_criteria is None:
            # Default ranking criteria
            ranking_criteria = {
                'End Year': {'weight': 0.3, 'preference': 'higher'},
                'Monte Carlo Iterations': {'weight': 0.2, 'preference': 'higher'},
                'Run DSM Calculation': {'weight': 0.25, 'preference': 'boolean'},
                'Run FOMP Calculation': {'weight': 0.25, 'preference': 'boolean'}
            }
        
        comparison_data = self.create_scenario_comparison_plot(scenario_names)
        
        # Calculate scores for each scenario
        scenario_scores = {}
        for scenario_name in scenario_names:
            score = 0
            config = comparison_data['scenarios'][scenario_name]['config']
            
            for criterion, criteria_info in ranking_criteria.items():
                if criterion in config:
                    value = config[criterion]
                    weight = criteria_info['weight']
                    preference = criteria_info['preference']
                    
                    if preference == 'higher':
                        # Normalize to 0-1 scale (assuming reasonable ranges)
                        if isinstance(value, (int, float)):
                            normalized_value = min(value / 100, 1.0)  # Assuming max 100
                            score += normalized_value * weight
                    elif preference == 'boolean':
                        if isinstance(value, bool):
                            score += (1 if value else 0) * weight
                        elif isinstance(value, str):
                            score += (1 if value.lower() == 'yes' else 0) * weight
            
            scenario_scores[scenario_name] = score
        
        # Sort scenarios by score
        ranked_scenarios = sorted(scenario_scores.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'ranking': ranked_scenarios,
            'scores': scenario_scores,
            'criteria': ranking_criteria
        }


def create_config_from_scenario(config_class, scenario_config):
    """
    Create a configuration object from a scenario dictionary.
    
    Args:
        config_class (class): The configuration class to instantiate.
        scenario_config (dict): Scenario configuration dictionary.
        
    Returns:
        object: Configuration object instance.
    """
    config_instance = config_class()
    
    for key, value in scenario_config.items():
        if hasattr(config_instance, key):
            setattr(config_instance, key, value)
    
    return config_instance


def validate_scenario_config(config_dict, required_fields=None):
    """
    Validate a scenario configuration.
    
    Args:
        config_dict (dict): Configuration dictionary to validate.
        required_fields (list): List of required field names.
        
    Returns:
        bool: True if valid, False otherwise.
    """
    if required_fields is None:
        required_fields = ['excel_file_path', 'start_year', 'end_year', 'elements']
    
    missing_fields = []
    for field in required_fields:
        if field not in config_dict:
            missing_fields.append(field)
    
    if missing_fields:
        print(f"❌ Missing required fields: {', '.join(missing_fields)}")
        return False
    
    return True


def validate_configuration(config):
    """
    Validates the analysis configuration and provides helpful feedback.
    
    Args:
        config (object): Configuration object to validate.
        
    Returns:
        tuple: (is_valid, messages) where messages is a list of validation messages.
    """
    messages = []
    is_valid = True
    
    # Check file paths
    if not hasattr(config, 'excel_file_path'):
        messages.append("❌ Missing excel_file_path in configuration")
        is_valid = False
    elif not os.path.exists(config.excel_file_path):
        messages.append(f"❌ Input file not found: {config.excel_file_path}")
        is_valid = False
    else:
        messages.append(f"✅ Input file found: {config.excel_file_path}")
    
    # Check time range
    if hasattr(config, 'start_year') and hasattr(config, 'end_year'):
        if config.start_year >= config.end_year:
            messages.append("❌ start_year must be less than end_year")
            is_valid = False
        elif config.end_year - config.start_year > 100:
            messages.append("⚠️  Large time range detected (>100 years). This may take a long time to calculate.")
        else:
            messages.append(f"✅ Time range: {config.start_year} - {config.end_year}")
    else:
        messages.append("❌ Missing start_year or end_year in configuration")
        is_valid = False
    
    # Check elements
    if hasattr(config, 'elements') and config.elements:
        messages.append(f"✅ Elements: {', '.join(config.elements)}")
    else:
        messages.append("❌ No elements defined in configuration")
        is_valid = False
    
    # Check Monte Carlo settings
    if hasattr(config, 'run_monte_carlo') and config.run_monte_carlo:
        if hasattr(config, 'mc_iterations'):
            if config.mc_iterations < 10:
                messages.append("⚠️  Low number of Monte Carlo iterations (<10). Results may be unreliable.")
            elif config.mc_iterations > 1000:
                messages.append("⚠️  High number of Monte Carlo iterations (>1000). This may take a very long time.")
            else:
                messages.append(f"✅ Monte Carlo iterations: {config.mc_iterations}")
        else:
            messages.append("❌ Monte Carlo enabled but mc_iterations not set")
            is_valid = False
    
    # Check model components
    if hasattr(config, 'RUN_DSM_CALCULATION'):
        messages.append(f"✅ DSM calculation: {'Enabled' if config.RUN_DSM_CALCULATION else 'Disabled'}")
    if hasattr(config, 'RUN_FOMP_CALCULATION'):
        messages.append(f"✅ FOMP calculation: {'Enabled' if config.RUN_FOMP_CALCULATION else 'Disabled'}")
    
    # Check output path
    if hasattr(config, 'output_path'):
        output_dir = os.path.dirname(config.output_path)
        if not os.path.exists(output_dir):
            messages.append(f"⚠️  Output directory does not exist: {output_dir}")
            messages.append("   (Will be created automatically)")
        else:
            messages.append(f"✅ Output directory: {output_dir}")
    
    return is_valid, messages


def print_configuration_summary(config):
    """
    Prints a user-friendly summary of the configuration.
    
    Args:
        config (object): Configuration object to summarize.
    """
    print("📋 Configuration Summary")
    print("=" * 50)
    
    is_valid, messages = validate_configuration(config)
    
    for message in messages:
        print(f"   {message}")
    
    print("\n" + "=" * 50)
    
    if is_valid:
        print("✅ Configuration is valid and ready for analysis!")
    else:
        print("❌ Configuration has issues. Please fix them before proceeding.")
    
    return is_valid


def create_progress_tracker(total_steps, description="Progress"):
    """
    Creates a simple progress tracker for long-running operations.
    
    Args:
        total_steps (int): Total number of steps to track.
        description (str): Description of the operation.
        
    Returns:
        function: Progress update function.
    """
    current_step = 0
    
    def update_progress(step_increment=1, custom_message=None):
        nonlocal current_step
        current_step += step_increment
        
        percentage = (current_step / total_steps) * 100
        progress_bar = "█" * int(percentage / 5) + "░" * (20 - int(percentage / 5))
        
        message = custom_message or f"{description}"
        print(f"\r{message}: [{progress_bar}] {percentage:.1f}% ({current_step}/{total_steps})", end="")
        
        if current_step >= total_steps:
            print()  # New line when complete
    
    return update_progress