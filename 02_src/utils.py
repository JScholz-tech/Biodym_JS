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
    Samples parameter values from their defined uncertainty distributions.

    This function iterates through a dictionary of parameter definitions,
    each specifying a distribution type (e.g., normal, uniform, triangular,
    lognormal) and its associated parameters (mean, std, min, max, mode).
    It generates a random sample for each parameter based on its distribution.
    Bounds (min/max) are applied if specified.

    Parameters
    ----------
    uncertainty_params : dict
        A dictionary where keys are parameter names (str) and values are
        dictionaries defining the uncertainty distribution for each parameter.
        Each parameter definition dictionary should contain:
        - 'distribution' (str): Type of distribution ('normal', 'uniform',
          'triangular', 'lognormal').
        - 'mean' (float, optional): Mean for normal/lognormal distributions.
        - 'std' (float, optional): Standard deviation for normal/lognormal distributions.
        - 'min' (float, optional): Minimum value for uniform/triangular distributions
          and lower bound for all distributions.
        - 'max' (float, optional): Maximum value for uniform/triangular distributions
          and upper bound for all distributions.
        - 'mode' (float, optional): Mode for triangular distribution.

    Returns
    -------
    dict
        A dictionary with parameter names as keys and their corresponding
        sampled float values.

    Raises
    ------
    ValueError
        If an unknown distribution type is encountered.

    Examples
    --------
    >>> params = {
    ...     "param_a": {"distribution": "normal", "mean": 10, "std": 2, "min": 0},
    ...     "param_b": {"distribution": "uniform", "min": 5, "max": 15}
    ... }
    >>> sampled = sample_parameters(params)
    >>> isinstance(sampled["param_a"], float)
    True
    >>> 0 <= sampled["param_a"]
    True
    >>> 5 <= sampled["param_b"] <= 15
    True
    """
    sampled_values = {}

    for param_name, param_def in uncertainty_params.items():
        distribution = param_def.get("distribution", "normal")
        mean = param_def.get("mean", 0)
        std = param_def.get("std", 1)
        min_val = param_def.get("min", None)
        max_val = param_def.get("max", None)

        if distribution == "normal":
            value = np.random.normal(mean, std)
        elif distribution == "uniform":
            value = np.random.uniform(min_val, max_val)
        elif distribution == "triangular":
            mode = param_def.get("mode", (min_val + max_val) / 2)
            value = np.random.triangular(min_val, mode, max_val)
        elif distribution == "lognormal":
            value = np.random.lognormal(mean, std)
        else:
            # Raise an error for unknown distributions
            raise ValueError(f"Unknown distribution type: {distribution}")

        # Apply bounds if specified
        if min_val is not None:
            value = max(value, min_val)
        if max_val is not None:
            value = min(value, max_val)

        sampled_values[param_name] = value

    return sampled_values



def export_results_to_excel(mfa_system_results, output_path, input_file_path="Not specified"):
    """
    Exports MFA system results to a professionally formatted Excel file.

    This function takes the solved MFA system results and exports them into
    an Excel file with multiple sheets for clarity and ease of analysis.
    It includes metadata, long-format data for programmatic use, and wide-format
    (crosstab) data for direct Excel analysis.

    Parameters
    ----------
    mfa_system_results : odym.MFAsystem
        The solved MFA system object containing flow and stock results.
    output_path : str
        The absolute or relative path where the Excel file should be saved.
    input_file_path : str, optional
        The path of the input file used for the analysis. Defaults to "Not specified".

    Returns
    -------
    None

    Notes
    -----
    The Excel file will contain the following sheets:
    - 'Export_Info': Metadata about the export, including input file, date,
      time range, elements, and counts of processes, flows, and stocks.
    - 'Flows_long': All flow data in a long (tidy) format, suitable for further
      data processing.
    - 'Stocks_long': All stock data in a long (tidy) format.
    - 'Flows_wide_<element>': For each element, a crosstab of flows (rows) by years (columns).
    - 'Stocks_wide_<element>': For each element, a crosstab of stocks (rows) by years (columns).

    Automatic column width adjustment and bold headers are applied for readability.
    If `mfa_system_results` is None, the export is skipped with a message.
    """
    if mfa_system_results is None:
        print("Export skipped: No results to export.")
        return
        
    print(f"--> Exporting results to '{output_path}'...")

    try:
        time_index = mfa_system_results.IndexTable.Classification["Time"].Items
        elements = mfa_system_results.Elements
    except AttributeError as e:
        print(f"Export skipped: Error: {e}")
        return

    with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
        workbook = writer.book
        header_format = workbook.add_format({'bold': True, 'bottom': 2, 'bg_color': '#F0F0F0'})

        # --- 1. Export Info Sheet ---
        meta_df = pd.DataFrame([
            ["Input File", input_file_path],
            ["Export Date", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            ["Time Range", f"{time_index[0]} - {time_index[-1]}"],
            ["Elements", ", ".join(elements)],
            ["Total Processes", len(mfa_system_results.ProcessList)],
            ["Total Flows", len(mfa_system_results.FlowDict)],
            ["Total Stocks", len([s for s in mfa_system_results.StockDict if s.startswith('S_')])]
        ], columns=["Attribute", "Value"])
        meta_df.to_excel(writer, sheet_name="Export_Info", index=False)
        worksheet = writer.sheets["Export_Info"]
        worksheet.set_column('A:A', 20) # Set width for Attribute column
        worksheet.set_column('B:B', 80) # Set width for Value column

        # --- 2. Long-Format Data (for programmatic use) ---
        flow_data_rows = []
        for name, flow_obj in mfa_system_results.FlowDict.items():
            for year_idx, year in enumerate(time_index):
                row = {"Flow": name, "Year": year}
                for elem_idx, element in enumerate(elements):
                    row[element] = flow_obj.Values[year_idx, elem_idx]
                flow_data_rows.append(row)
        flow_df_long = pd.DataFrame(flow_data_rows)
        flow_df_long.to_excel(writer, sheet_name="Flows_long", index=False)
        worksheet = writer.sheets["Flows_long"]
        for col_num, value in enumerate(flow_df_long.columns.values):
            worksheet.write(0, col_num, value, header_format)
            worksheet.set_column(col_num, col_num, len(value) + 2)

        stock_data_rows = []
        for name, stock_obj in mfa_system_results.StockDict.items():
            for year_idx, year in enumerate(time_index):
                row = {"Stock": name, "Year": year}
                for elem_idx, element in enumerate(elements):
                    row[element] = stock_obj.Values[year_idx, elem_idx]
                stock_data_rows.append(row)
        stock_df_long = pd.DataFrame(stock_data_rows)
        stock_df_long.to_excel(writer, sheet_name="Stocks_long", index=False)
        worksheet = writer.sheets["Stocks_long"]
        for col_num, value in enumerate(stock_df_long.columns.values):
            worksheet.write(0, col_num, value, header_format)
            worksheet.set_column(col_num, col_num, len(value) + 2)

        # --- 3. Wide-Format Data (for easy analysis in Excel) ---
        for element in elements:
            # Flows Wide
            if not flow_df_long.empty and element in flow_df_long.columns:
                flow_df_wide = flow_df_long.pivot_table(index="Flow", columns="Year", values=element)
                sheet_name = f"Flows_wide_{element}"
                flow_df_wide.to_excel(writer, sheet_name=sheet_name)
                worksheet = writer.sheets[sheet_name]
                worksheet.write(0, 0, 'Flow', header_format)
                for col_num, value in enumerate(flow_df_wide.columns.values):
                    worksheet.write(0, col_num + 1, value, header_format)
                worksheet.set_column(0, 0, 30) # Width for flow names

            # Stocks Wide
            if not stock_df_long.empty and element in stock_df_long.columns:
                stock_df_wide = stock_df_long.pivot_table(index="Stock", columns="Year", values=element)
                sheet_name = f"Stocks_wide_{element}"
                stock_df_wide.to_excel(writer, sheet_name=sheet_name)
                worksheet = writer.sheets[sheet_name]
                worksheet.write(0, 0, 'Stock', header_format)
                for col_num, value in enumerate(stock_df_wide.columns.values):
                    worksheet.write(0, col_num + 1, value, header_format)
                worksheet.set_column(0, 0, 30) # Width for stock names

    print(f"✅ Results successfully exported to {output_path}")



class ScenarioManager:
    """
    Manages the creation, storage, loading, and comparison of different MFA scenarios.

    This class provides functionalities to persist various model configurations
    (scenarios) to disk, load them back, list available scenarios, and perform
    comparisons or rankings based on defined criteria. Scenarios are stored as
    JSON files in a specified directory.

    Parameters
    ----------
    scenarios_dir : str, optional
        The name of the directory where scenario files will be stored.
        Defaults to "scenarios". This directory will be created if it does not exist.

    Attributes
    ----------
    scenarios_dir : str
        The directory path where scenarios are managed.
    scenarios : dict
        A dictionary holding loaded scenario data, keyed by scenario name.

    Examples
    --------
    >>> manager = ScenarioManager("my_scenarios")
    >>> # Assuming a config object exists
    >>> # manager.save_scenario("ScenarioA", my_config, "First test scenario")
    >>> # manager.list_scenarios()
    """

    def __init__(self, scenarios_dir="scenarios"):
        """
        Initializes the ScenarioManager.

        Sets up the directory for storing scenarios and loads any existing
        scenarios from that directory.

        Parameters
        ----------
        scenarios_dir : str, optional
            The name of the directory to store scenario files. Defaults to "scenarios".
        """
        self.scenarios_dir = scenarios_dir
        self.scenarios = {}
        self._ensure_scenarios_dir()
        self._load_existing_scenarios()

    def _ensure_scenarios_dir(self):
        """
        Ensures that the scenarios directory exists.

        If the directory specified by `self.scenarios_dir` does not exist,
        it is created. This prevents errors when trying to save scenario files.

        Returns
        -------
        None
        """
        if not os.path.exists(self.scenarios_dir):
            os.makedirs(self.scenarios_dir)

    def _load_existing_scenarios(self):
        """
        Loads existing scenario files from the scenarios directory into memory.

        This method scans the `self.scenarios_dir` for JSON files, which are
        assumed to be saved scenario configurations. Each valid JSON file is
        loaded and stored in the `self.scenarios` dictionary.
        Warnings are printed for any files that cannot be loaded.

        Returns
        -------
        None
        """
        if os.path.exists(self.scenarios_dir):
            for filename in os.listdir(self.scenarios_dir):
                if filename.endswith(".json"):
                    scenario_name = filename[:-5]  # Remove .json extension
                    try:
                        with open(os.path.join(self.scenarios_dir, filename), "r") as f:
                            self.scenarios[scenario_name] = json.load(f)
                    except Exception as e:
                        print(f"Warning: Could not load scenario {scenario_name}: {e}")

    def save_scenario(self, scenario_name, config, description=""):
        """
        Saves a given configuration object as a named scenario to disk.

        The configuration object's attributes are converted into a dictionary
        and stored along with a name, description, and creation timestamp in a
        JSON file within the `scenarios_dir`.

        Parameters
        ----------
        scenario_name : str
            A unique name for the scenario to be saved.
        config : object
            The configuration object (e.g., an instance of the `Config` class)
            whose attributes represent the scenario's settings.
        description : str, optional
            A brief description of the scenario. Defaults to an empty string.

        Returns
        -------
        None

        Notes
        -----
        The configuration object is converted to a dictionary by iterating
        over its attributes, excluding private attributes (starting with '_')
        and callable methods.
        """
        # Convert config object to dictionary
        config_dict = {}
        for attr in dir(config):
            if not attr.startswith("_") and not callable(getattr(config, attr)):
                config_dict[attr] = getattr(config, attr)

        scenario_data = {
            "name": scenario_name,
            "description": description,
            "created": datetime.now().isoformat(),
            "config": config_dict,
        }

        self.scenarios[scenario_name] = scenario_data

        # Save to file
        filename = os.path.join(self.scenarios_dir, f"{scenario_name}.json")
        with open(filename, "w") as f:
            json.dump(scenario_data, f, indent=2)

        print(f"✅ Scenario '{scenario_name}' saved successfully.")

    def load_scenario(self, scenario_name):
        """
        Loads a previously saved scenario configuration from memory.

        Parameters
        ----------
        scenario_name : str
            The name of the scenario to load.

        Returns
        -------
        dict
            A dictionary containing the configuration settings of the loaded scenario.

        Raises
        ------
        ValueError
            If the specified `scenario_name` does not exist in the loaded scenarios.

        Examples
        --------
        >>> manager = ScenarioManager()
        >>> # manager.save_scenario("TestScenario", some_config_object)
        >>> # loaded_config = manager.load_scenario("TestScenario")
        >>> # isinstance(loaded_config, dict)
        True
        """
        if scenario_name not in self.scenarios:
            raise ValueError(f"Scenario '{scenario_name}' not found.")

        return self.scenarios[scenario_name]["config"]

    def list_scenarios(self):
        """
        Lists all currently loaded scenarios with their names, descriptions, and creation dates.

        Returns
        -------
        list of dict
            A list of dictionaries, where each dictionary represents a scenario
            and contains its 'name', 'description', and 'created' timestamp.

        Examples
        --------
        >>> manager = ScenarioManager()
        >>> # manager.save_scenario("ScenarioA", some_config_object, "Description A")
        >>> # manager.list_scenarios()
        [{'name': 'ScenarioA', 'description': 'Description A', 'created': '...'}]
        """
        scenario_list = []
        for name, data in self.scenarios.items():
            scenario_list.append(
                {
                    "name": name,
                    "description": data.get("description", ""),
                    "created": data.get("created", ""),
                }
            )
        return scenario_list

    def delete_scenario(self, scenario_name):
        """
        Deletes a specified scenario from memory and its corresponding file from disk.

        Parameters
        ----------
        scenario_name : str
            The name of the scenario to be deleted.

        Returns
        -------
        None

        Raises
        ------
        ValueError
            If the specified `scenario_name` does not exist.

        Notes
        -----
        A confirmation message is printed upon successful deletion.
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
        Creates and saves a new scenario based on an existing configuration object.

        This method takes a configuration object, converts its relevant attributes
        into a dictionary, and then saves it as a new scenario using `save_scenario`.

        Parameters
        ----------
        scenario_name : str
            The name for the new scenario.
        config : object
            The configuration object (e.g., an instance of the `Config` class)
            to be used as the basis for the new scenario.
        description : str, optional
            A brief description of the scenario. Defaults to an empty string.

        Returns
        -------
        dict
            The dictionary representation of the configuration that was saved
            as the new scenario.

        See Also
        --------
        save_scenario : The method used internally to persist the scenario.
        """
        # Create a copy of the config
        config_dict = {}
        for attr in dir(config):
            if not attr.startswith("_") and not callable(getattr(config, attr)):
                config_dict[attr] = getattr(config, attr)

        # Save the scenario
        self.save_scenario(scenario_name, config, description)

        return config_dict

    def compare_scenarios(self, scenario_names):
        """
        Retrieves the configurations for a list of specified scenarios for comparison.

        Parameters
        ----------
        scenario_names : list of str
            A list containing the names of the scenarios to be compared.

        Returns
        -------
        dict
            A dictionary where keys are scenario names and values are dictionaries
            containing the scenario's description and its full configuration.

        Raises
        ------
        ValueError
            If fewer than two scenario names are provided, or if any specified
            scenario name is not found.

        Examples
        --------
        >>> manager = ScenarioManager()
        >>> # manager.save_scenario("ScenarioA", config_a)
        >>> # manager.save_scenario("ScenarioB", config_b)
        >>> # comparison = manager.compare_scenarios(["ScenarioA", "ScenarioB"])
        >>> # 'ScenarioA' in comparison
        True
        """
        if len(scenario_names) < 2:
            raise ValueError("Need at least 2 scenarios for comparison.")

        comparison = {}
        for name in scenario_names:
            if name not in self.scenarios:
                raise ValueError(f"Scenario '{name}' not found.")

            config = self.scenarios[name]["config"]
            comparison[name] = {
                "description": self.scenarios[name].get("description", ""),
                "config": config,
            }

        return comparison

    def create_scenario_comparison_plot(self, scenario_names, comparison_metrics=None):
        """
        Prepares data for a comparison plot of multiple scenarios based on specified metrics.

        This method gathers configuration data for the given scenarios and extracts
        values for a set of comparison metrics. While the name suggests plotting,
        this function primarily prepares the data structure suitable for a plotting
        function, rather than generating the plot itself.

        Parameters
        ----------
        scenario_names : list of str
            A list containing the names of the scenarios to compare.
        comparison_metrics : list of str, optional
            A list of configuration parameter names (strings) to use as metrics
            for comparison. If None, a default set of metrics is used.

        Returns
        -------
        dict
            A dictionary containing:
            - 'scenarios': Detailed configuration data for each scenario.
            - 'metrics': A nested dictionary where the outer keys are metric names
              and inner keys are scenario names, holding the metric values.
            - 'scenario_names': The list of scenario names that were compared.

        Raises
        ------
        ValueError
            If fewer than two scenario names are provided.

        See Also
        --------
        compare_scenarios : The method used internally to retrieve scenario configurations.
        """
        if len(scenario_names) < 2:
            raise ValueError("Need at least 2 scenarios for comparison.")

        comparison_data = self.compare_scenarios(scenario_names)

        # Default comparison metrics
        if comparison_metrics is None:
            comparison_metrics = [
                "Start Year",
                "End Year",
                "Monte Carlo Iterations",
                "Run DSM Calculation",
                "Run FOMP Calculation",
            ]

        # Extract metric values for each scenario
        metric_data = {}
        for metric in comparison_metrics:
            metric_data[metric] = {}
            for scenario_name in scenario_names:
                config = comparison_data[scenario_name]["config"]
                value = config.get(metric, "N/A")
                metric_data[metric][scenario_name] = value

        return {
            "scenarios": comparison_data,
            "metrics": metric_data,
            "scenario_names": scenario_names,
        }

    def export_scenario_comparison(self, scenario_names, output_path=None):
        """
        Exports a comparison of multiple scenarios to an Excel file.

        This method generates an Excel file containing a summary of the compared
        scenarios, a comparison of specified metrics, and individual sheets for
        each scenario's full configuration.

        Parameters
        ----------
        scenario_names : list of str
            A list containing the names of the scenarios to compare and export.
        output_path : str, optional
            The file path where the Excel comparison should be saved.
            If None, a default path based on the current timestamp is generated.

        Returns
        -------
        str
            The absolute path to the exported Excel file.

        See Also
        --------
        create_scenario_comparison_plot : Used internally to prepare comparison data.
        """
        if output_path is None:
            output_path = f"scenarios/scenario_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        comparison_data = self.create_scenario_comparison_plot(scenario_names)

        with pd.ExcelWriter(output_path) as writer:
            # Summary sheet
            summary_data = []
            for scenario_name in scenario_names:
                scenario_info = comparison_data["scenarios"][scenario_name]
                summary_data.append(
                    {
                        "Scenario": scenario_name,
                        "Description": scenario_info["description"],
                        "Created": scenario_info.get("created", "Unknown"),
                    }
                )

            pd.DataFrame(summary_data).to_excel(
                writer, sheet_name="Summary", index=False
            )

            # Metrics comparison sheet
            metrics_data = []
            for metric, values in comparison_data["metrics"].items():
                row = {"Metric": metric}
                for scenario_name in scenario_names:
                    row[scenario_name] = values.get(scenario_name, "N/A")
                metrics_data.append(row)

            pd.DataFrame(metrics_data).to_excel(
                writer, sheet_name="Metrics_Comparison", index=False
            )

            # Individual scenario sheets
            for scenario_name in scenario_names:
                scenario_config = comparison_data["scenarios"][scenario_name]["config"]
                config_df = pd.DataFrame(
                    list(scenario_config.items()), columns=["Parameter", "Value"]
                )
                config_df.to_excel(
                    writer, sheet_name=f"Scenario_{scenario_name}", index=False
                )

        print(f"✅ Scenario comparison exported to: {output_path}")
        return output_path

    def get_scenario_differences(self, scenario_names):
        """
        Compares exactly two scenarios and identifies differences in their configurations.

        Parameters
        ----------
        scenario_names : list of str
            A list containing the names of exactly two scenarios to compare.

        Returns
        -------
        dict
            A dictionary where keys are configuration parameter names. Each value
            is another dictionary containing the parameter's value in each scenario
            and a boolean indicating if the values are different.

        Raises
        ------
        ValueError
            If the `scenario_names` list does not contain exactly two scenario names.

        Examples
        --------
        >>> manager = ScenarioManager()
        >>> # manager.save_scenario("ScenarioA", config_a)
        >>> # manager.save_scenario("ScenarioB", config_b)
        >>> # differences = manager.get_scenario_differences(["ScenarioA", "ScenarioB"])
        >>> # 'Start Year' in differences
        True
        """
        if len(scenario_names) != 2:
            raise ValueError("This function compares exactly 2 scenarios.")

        scenario1, scenario2 = scenario_names
        config1 = self.scenarios[scenario1]["config"]
        config2 = self.scenarios[scenario2]["config"]

        differences = {}
        all_keys = set(config1.keys()) | set(config2.keys())

        for key in all_keys:
            val1 = config1.get(key, "N/A")
            val2 = config2.get(key, "N/A")

            if val1 != val2:
                differences[key] = {scenario1: val1, scenario2: val2, "different": True}
            else:
                differences[key] = {
                    scenario1: val1,
                    scenario2: val2,
                    "different": False,
                }

        return differences

    def create_scenario_ranking(self, scenario_names, ranking_criteria=None):
        """
        Ranks multiple scenarios based on a set of specified criteria and their weights.

        This method calculates a score for each scenario by evaluating its configuration
        against a set of ranking criteria. Each criterion can have a weight and a
        preference (e.g., 'higher' for better, 'boolean' for true/false).

        Parameters
        ----------
        scenario_names : list of str
            A list containing the names of the scenarios to be ranked.
        ranking_criteria : dict, optional
            A dictionary defining the criteria for ranking. Keys are parameter names,
            and values are dictionaries with 'weight' (float) and 'preference' (str,
            e.g., 'higher', 'boolean'). If None, a default set of criteria is used.

        Returns
        -------
        dict
            A dictionary containing:
            - 'ranking': A list of tuples, where each tuple contains (scenario_name, score),
              sorted in descending order of scores.
            - 'scores': A dictionary of scenario names mapped to their calculated scores.
            - 'criteria': The ranking criteria used.

        Examples
        --------
        >>> manager = ScenarioManager()
        >>> # manager.save_scenario("ScenarioA", config_a)
        >>> # manager.save_scenario("ScenarioB", config_b)
        >>> # ranking = manager.create_scenario_ranking(["ScenarioA", "ScenarioB"])
        >>> # ranking["ranking"]
        [('ScenarioA', 0.75), ('ScenarioB', 0.6)]
        """
        if ranking_criteria is None:
            # Default ranking criteria
            ranking_criteria = {
                "End Year": {"weight": 0.3, "preference": "higher"},
                "Monte Carlo Iterations": {"weight": 0.2, "preference": "higher"},
                "Run DSM Calculation": {"weight": 0.25, "preference": "boolean"},
                "Run FOMP Calculation": {"weight": 0.25, "preference": "boolean"},
            }

        comparison_data = self.create_scenario_comparison_plot(scenario_names)

        # Calculate scores for each scenario
        scenario_scores = {}
        for scenario_name in scenario_names:
            score = 0
            config = comparison_data["scenarios"][scenario_name]["config"]

            for criterion, criteria_info in ranking_criteria.items():
                if criterion in config:
                    value = config[criterion]
                    weight = criteria_info["weight"]
                    preference = criteria_info["preference"]

                    if preference == "higher":
                        # Normalize to 0-1 scale (assuming reasonable ranges)
                        if isinstance(value, (int, float)):
                            normalized_value = min(value / 100, 1.0)  # Assuming max 100
                            score += normalized_value * weight
                    elif preference == "boolean":
                        if isinstance(value, bool):
                            score += (1 if value else 0) * weight
                        elif isinstance(value, str):
                            score += (1 if value.lower() == "yes" else 0) * weight

            scenario_scores[scenario_name] = score

        # Sort scenarios by score
        ranked_scenarios = sorted(
            scenario_scores.items(), key=lambda x: x[1], reverse=True
        )

        return {
            "ranking": ranked_scenarios,
            "scores": scenario_scores,
            "criteria": ranking_criteria,
        }


def create_config_from_scenario(config_class, scenario_config):
    """
    Creates an instance of a configuration class and populates it with scenario settings.

    This function takes a configuration class (not an instance) and a dictionary
    representing a scenario's configuration. It instantiates the class and then
    sets attributes on the new object based on the key-value pairs in the
    `scenario_config` dictionary.

    Parameters
    ----------
    config_class : type
        The class type of the configuration object to be created (e.g., `Config`).
    scenario_config : dict
        A dictionary containing the configuration settings for the scenario.
        Keys should correspond to attribute names in `config_class`.

    Returns
    -------
    object
        An instance of `config_class` with its attributes populated from `scenario_config`.

    Examples
    --------
    >>> class MyConfig:
    ...     def __init__(self):
    ...         self.start_year = None
    ...         self.end_year = None
    >>> scenario_data = {"start_year": 2020, "end_year": 2030}
    >>> new_config = create_config_from_scenario(MyConfig, scenario_data)
    >>> new_config.start_year
    2020
    """
    config_instance = config_class()

    for key, value in scenario_config.items():
        if hasattr(config_instance, key):
            setattr(config_instance, key, value)

    return config_instance


def validate_scenario_config(config_dict, required_fields=None):
    """
    Validates a scenario configuration dictionary against a list of required fields.

    This function checks if all specified `required_fields` are present as keys
    in the `config_dict`. If any required fields are missing, it prints an error
    message and returns False.

    Parameters
    ----------
    config_dict : dict
        The configuration dictionary to validate.
    required_fields : list of str, optional
        A list of strings representing the names of fields that must be present
        in `config_dict`. If None, a default set of common required fields is used.

    Returns
    -------
    bool
        True if all required fields are present, False otherwise.

    Examples
    --------
    >>> valid_config = {"excel_file_path": "data.xlsx", "start_year": 2020}
    >>> validate_scenario_config(valid_config, ["excel_file_path"])
    True
    >>> invalid_config = {"start_year": 2020}
    >>> validate_scenario_config(invalid_config, ["excel_file_path"])
    ❌ Missing required fields: excel_file_path
    False
    """
    if required_fields is None:
        required_fields = ["excel_file_path", "start_year", "end_year", "elements"]

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
    Validates the provided analysis configuration object and collects validation messages.

    This function performs a series of checks on the configuration object,
    including file path existence, time range validity, element definitions,
    Monte Carlo settings, and output directory status. It returns a boolean
    indicating overall validity and a list of messages detailing each check's result.

    Parameters
    ----------
    config : object
        The configuration object (e.g., an instance of the `Config` class)
        to be validated.

    Returns
    -------
    tuple
        A tuple containing:
        - is_valid (bool): True if the configuration passes all critical validations,
          False otherwise.
        - messages (list of str): A list of strings, each representing a validation
          message (e.g., "✅ Input file found", "❌ Missing start_year").

    Notes
    -----
    Warnings (e.g., for large time ranges or low Monte Carlo iterations) are
    included in the messages but do not necessarily make the configuration invalid.
    """
    messages = []
    is_valid = True

    # Check file paths
    if not hasattr(config, "excel_file_path"):
        messages.append("❌ Missing excel_file_path in configuration")
        is_valid = False
    elif not os.path.exists(config.excel_file_path):
        messages.append(f"❌ Input file not found: {config.excel_file_path}")
        is_valid = False
    else:
        messages.append(f"✅ Input file found: {config.excel_file_path}")

    # Check time range
    if hasattr(config, "start_year") and hasattr(config, "end_year"):
        if config.start_year >= config.end_year:
            messages.append("❌ start_year must be less than end_year")
            is_valid = False
        elif config.end_year - config.start_year > 100:
            messages.append(
                "⚠️  Large time range detected (>100 years). This may take a long time to calculate."
            )
        else:
            messages.append(f"✅ Time range: {config.start_year} - {config.end_year}")
    else:
        messages.append("❌ Missing start_year or end_year in configuration")
        is_valid = False

    # Check elements
    if hasattr(config, "elements") and config.elements:
        messages.append(f"✅ Elements: {', '.join(config.elements)}")
    else:
        messages.append("❌ No elements defined in configuration")
        is_valid = False

    # Check Monte Carlo settings
    if hasattr(config, "run_monte_carlo") and config.run_monte_carlo:
        if hasattr(config, "mc_iterations"):
            if config.mc_iterations < 10:
                messages.append(
                    "⚠️  Low number of Monte Carlo iterations (<10). Results may be unreliable."
                )
            elif config.mc_iterations > 1000:
                messages.append(
                    "⚠️  High number of Monte Carlo iterations (>1000). This may take a very long time."
                )
            else:
                messages.append(f"✅ Monte Carlo iterations: {config.mc_iterations}")
        else:
            messages.append("❌ Monte Carlo enabled but mc_iterations not set")
            is_valid = False

    # Check model components
    if hasattr(config, "RUN_DSM_CALCULATION"):
        messages.append(
            f"✅ DSM calculation: {'Enabled' if config.RUN_DSM_CALCULATION else 'Disabled'}"
        )
    if hasattr(config, "RUN_FOMP_CALCULATION"):
        messages.append(
            f"✅ FOMP calculation: {'Enabled' if config.RUN_FOMP_CALCULATION else 'Disabled'}"
        )

    # Check output path
    if hasattr(config, "output_path"):
        output_dir = os.path.dirname(config.output_path)
        if not os.path.exists(output_dir):
            messages.append(f"⚠️  Output directory does not exist: {output_dir}")
            messages.append("   (Will be created automatically)")
        else:
            messages.append(f"✅ Output directory: {output_dir}")

    return is_valid, messages


def print_configuration_summary(config):
    """
    Prints a user-friendly summary of the current configuration and its validation status.

    This function calls `validate_configuration` to get a list of validation
    messages and then prints them to the console, along with an overall status
    indicating whether the configuration is valid or has issues.

    Parameters
    ----------
    config : object
        The configuration object (e.g., an instance of the `Config` class)
        whose summary is to be printed.

    Returns
    -------
    bool
        True if the configuration is valid, False otherwise.

    See Also
    --------
    validate_configuration : Used internally to perform the actual validation checks.
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
    Creates a closure that provides a simple, console-based progress tracker.

    This function returns an `update_progress` function that, when called,
    updates and prints a progress bar to the console. It's useful for visualizing
    the progress of long-running operations.

    Parameters
    ----------
    total_steps : int
        The total number of steps required to complete the operation.
    description : str, optional
        A brief description of the task being tracked. Defaults to "Progress".

    Returns
    -------
    function
        A nested function `update_progress(step_increment=1, custom_message=None)`
        that can be called to advance and display the progress.

    Notes
    -----
    The progress bar uses block characters and percentage to indicate completion.
    It overwrites the current line in the console, providing a dynamic update.

    Examples
    --------
    >>> tracker = create_progress_tracker(10, "Processing Data")
    >>> for i in range(10):
    ...     # Simulate work
    ...     import time; time.sleep(0.1)
    ...     tracker()
    Processing Data: [████████████████████] 100.0% (10/10)
    """
    current_step = 0

    def update_progress(step_increment=1, custom_message=None):
        nonlocal current_step
        current_step += step_increment

        percentage = (current_step / total_steps) * 100
        progress_bar = "█" * int(percentage / 5) + "░" * (20 - int(percentage / 5))

        message = custom_message or f"{description}"
        print(
            f"\r{message}: [{progress_bar}] {percentage:.1f}% ({current_step}/{total_steps})",
            end="",
        )

        if current_step >= total_steps:
            print()  # New line when complete

    return update_progress
