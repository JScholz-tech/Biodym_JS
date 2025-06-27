"""
Created on 16.12.2024

@author: lhoppe
"""

"""
File bioDYM_export

Contains export options for bioDYM

standard abbreviation: bix


"""

import pandas as pd
import xlsxwriter
import os
import numpy as np 

# Export values of all flows and stocks to Excel for all elements
def export_xlsx(Dyn_MFA_System, MyYears, ModelClassification):
    flow_labels = []
    for flow in Dyn_MFA_System.FlowDict:
        flow_labels.append(Dyn_MFA_System.FlowDict[flow].Name)
    flow_labels
    
    stock_labels = []
    for stock in Dyn_MFA_System.StockDict:
        stock_labels.append(Dyn_MFA_System.StockDict[stock].Name)
    stock_labels

    folder = 'results'
    file_path = os.path.join(folder, 'Case_study_results.xlsx')
    # Create the folder if it doesn't exist
    os.makedirs(folder, exist_ok=True)
    writer = pd.ExcelWriter(file_path, engine='xlsxwriter')
    
    for element in ModelClassification['Element'].Items:
        flows_Values = []
        for flow in Dyn_MFA_System.FlowDict:
            flows_Values.append(Dyn_MFA_System.FlowDict[flow].Values[:, ModelClassification['Element'].Items.index(element)])
        df_flows = pd.DataFrame(flows_Values).T
        df_flows.columns = flow_labels
        df_flows['Years'] = MyYears
        df_flows.set_index('Years', inplace=True, drop=True)
    
    
        stock_Values = []
        for stock in Dyn_MFA_System.StockDict:
            stock_Values.append(Dyn_MFA_System.StockDict[stock].Values[:, ModelClassification['Element'].Items.index(element)])
        df_stock = pd.DataFrame(stock_Values).T
        df_stock.columns = stock_labels
        df_stock['Years'] = MyYears
        df_stock.set_index('Years', inplace=True, drop=True)
    
    
    
        df_flows.to_excel(writer, sheet_name= f'FlowDict_{element}')
        df_stock.to_excel(writer, sheet_name= f'StockDict_{element}')
    
    
    writer.close()


# Export mean and absolute standard deviation of Monte Carlo Simulation to Excel for all elements
def MC_export_xlsx(MC_FlowDict, MC_StockDict, MyYears, ModelClassification):
    flow_labels = []
    for flow in MC_FlowDict:
        flow_labels.append(MC_FlowDict[flow].Name)
    flow_labels
    
    stock_labels = []
    for stock in MC_StockDict:
        stock_labels.append(MC_StockDict[stock].Name)
    stock_labels
    
    folder = 'results'
    file_path = os.path.join(folder, 'MC_Case_study_results.xlsx')
    # Create the folder if it doesn't exist
    os.makedirs(folder, exist_ok=True)
    writer = pd.ExcelWriter(file_path, engine='xlsxwriter')
    
    for element in ModelClassification['Element'].Items:
        flow_values = np.array([
            MC_FlowDict[flow].Values[:, :, ModelClassification['Element'].Items.index(element)]
            for flow in MC_FlowDict
        ])  # Shape: (n_flows, 2, 15)
    
        mean_flows = np.mean(flow_values, axis=1)  # Mean over first dimension, shape (n_flows, 15)
        std_flows = np.std(flow_values, axis=1)
        df_mean_flows = pd.DataFrame(mean_flows.T, columns=flow_labels)  # Transpose to match years as rows
        df_std_flows = pd.DataFrame(std_flows.T, columns=flow_labels)
        
        df_mean_flows['Years'] = MyYears
        df_mean_flows.set_index('Years', inplace=True)
    
        df_std_flows['Years'] = MyYears
        df_std_flows.set_index('Years', inplace=True)
    
        
        df_mean_flows.to_excel(writer, sheet_name=f'FlowDict_{element}_Mean')
        df_std_flows.to_excel(writer, sheet_name=f'FlowDict_{element}_Std')
    
        stock_values = np.array([
            MC_StockDict[stock].Values[:, :, ModelClassification['Element'].Items.index(element)]
            for stock in MC_StockDict
        ])  # Shape: (n_stocks, 2, 15)
    
        mean_stocks = np.mean(stock_values, axis=1)
        std_stocks = np.std(stock_values, axis=1)
    
        df_mean_stocks = pd.DataFrame(mean_stocks.T, columns=stock_labels)
        df_std_stocks = pd.DataFrame(std_stocks.T, columns=stock_labels)
    
        df_mean_stocks['Years'] = MyYears
        df_mean_stocks.set_index('Years', inplace=True)
    
        df_std_stocks['Years'] = MyYears
        df_std_stocks.set_index('Years', inplace=True)
    
        df_mean_stocks.to_excel(writer, sheet_name=f'StockDict_{element}_Mean')
        df_std_stocks.to_excel(writer, sheet_name=f'StockDict_{element}_Std')
    
    writer.close()