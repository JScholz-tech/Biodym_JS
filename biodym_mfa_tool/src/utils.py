# -*- coding: utf-8 -*-
"""
Utilities Module for the BioDYM MFA Model.

This file contains miscellaneous helper functions that support the main
workflow, such as parameter sampling for Monte Carlo simulations and
exporting results to files.
"""
import numpy as np
import pandas as pd


def sample_parameters(uncertainty_defs):
    """
    Draws a new random value for each defined uncertain parameter based on its
    specified probability distribution.

    Args:
        uncertainty_defs (dict): A dictionary defining the uncertain parameters
                                 and their distributions.

    Returns:
        dict: A dictionary where keys are parameter names and values are the
              newly sampled values for this iteration.
    """
    sampled_values = {}
    for param_name, definition in uncertainty_defs.items():
        dist_type = definition.get('distribution')

        if dist_type == 'uniform':
            sampled_values[param_name] = np.random.uniform(definition['min'], definition['max'])
        elif dist_type == 'normal':
            sampled_values[param_name] = np.random.normal(definition['mean'], definition['std'])
        elif dist_type == 'triangular':
            sampled_values[param_name] = np.random.triangular(definition['min'], definition['mode'], definition['max'])
        elif dist_type == 'lognormal':
             sampled_values[param_name] = np.random.lognormal(definition['mean'], definition['std'])
        else:
            print(f"WARNING: Unknown distribution type '{dist_type}' for parameter '{param_name}'. Parameter will not be sampled.")

    return sampled_values


def export_results_to_excel(mfa_system_results, output_path):
    """
    Exports all calculated flows and stocks into a single Excel file with multiple sheets.

    Args:
        mfa_system_results (odym.MFAsystem): The solved MFA system object.
        output_path (str): The full path for the output Excel file.
    """
    if mfa_system_results is None:
        print("--> Export skipped: No results to export.")
        return

    print(f"\n--> Exporting results to '{output_path}'...")

    time_index = mfa_system_results.IndexTable.Classification['Time'].Items
    elements = mfa_system_results.Elements

    with pd.ExcelWriter(output_path) as writer:
        # --- Export Flows ---
        flow_data_rows = []
        for name, flow_obj in mfa_system_results.FlowDict.items():
            for i, year in enumerate(time_index):
                row = {'Flow_ID': name, 'Year': year}
                for j, element in enumerate(elements):
                    row[element] = flow_obj.Values[i, j]
                flow_data_rows.append(row)
        df_flows = pd.DataFrame(flow_data_rows)
        df_flows.to_excel(writer, sheet_name='Flows_ts', index=False)

        # --- Export Stocks ---
        stock_data_rows = []
        for name, stock_obj in mfa_system_results.StockDict.items():
            for i, year in enumerate(time_index):
                row = {'Stock_ID': name, 'Year': year}
                for j, element in enumerate(elements):
                    row[element] = stock_obj.Values[i, j]
                stock_data_rows.append(row)
        df_stocks = pd.DataFrame(stock_data_rows)
        df_stocks.to_excel(writer, sheet_name='Stocks_ts', index=False)

    print("--> Export complete.")