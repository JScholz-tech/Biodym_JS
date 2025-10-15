"""
Created on 16.12.2024

@author: lhoppe
"""

"""
File bioDYM_export

Contains interactive sankey and stock bar plot options

standard abbreviation: bipl


"""

import re
import plotly.graph_objects as go
from ipywidgets import interact, interactive, fixed, interact_manual
import ipywidgets as widgets

# Create interactive sankey diagrams
def sankey_results(Dyn_MFA_System, MyYears, ModelClassification, colors_flows, colors_processes, excluded_flows):
    # Loop through all flows and extract their starting process, end process and values
    flows_P_Start = []
    flows_P_End = []
    flows_Values = []
    for flow in Dyn_MFA_System.FlowDict.values():
        if flow.Name not in excluded_flows:
            flows_P_Start.append(flow.P_Start)
            flows_P_End.append(flow.P_End)
            flows_Values.append(flow.Values)

    
    # Bring flows_values into applicable form
    flows_Values_loop = []
    for i in range(len(MyYears)):
        loop_list = []
        for b in range(len(flows_P_Start)):
            loop_list.append([flows_Values[b][:][i][e] for e in range(len(ModelClassification['Element'].Items))])
        flows_Values_loop.append(loop_list)

    # Get names of processes
    labels = []
    for process in Dyn_MFA_System.ProcessList:
        labels.append(process.Name)
    
    elements = ModelClassification['Element'].Items
    
    # Initiate figure
    fig = go.FigureWidget()
    fig.add_sankey(node = dict(
          pad = 80,
          thickness = 10,
          line = dict(color = "black", width = 0.5),
          label = labels,
          color = colors_processes
        ),
        link = dict(
          source = flows_P_Start, 
          target = flows_P_End,
          value = flows_Values_loop[0][0],
            color = colors_flows,
      ))
    fig.update_layout(
        width=1000,  # Wider plot
        height=800   # Taller plot
    )
    fig.layout.title = f"""System Sankey diagram {elements[0]} (years {MyYears[0]}-{MyYears[-1]}) [t]"""
    display(fig)
  
    # This functions updates the Sankey diagram to make it interactive and introduces the slider feature
    def update(element, i = MyYears[0]):
        element_index = elements.index(element)
        fig.data[0].link.value = [flows_Values_loop[i-(MyYears[0])][b][element_index] for b in range(len(flows_Values))]
        fig.layout.title = f"""System Sankey diagram {element} (year {i}) in t"""
    element_dropdown = widgets.Dropdown(
        options = elements,
        value = elements[0],
        description = 'element:'
    )
    interact(update, element = element_dropdown, i = (MyYears[0], MyYears[-1], 1));




# Create interactive stock plots
def bar_stocks_results(Dyn_MFA_System, MyYears, ModelClassification, colors_processes):

    # Empty lists for names and values
    stocks_Names = []
    stocks_Values = []
    
    # StockDict includes stock changes and stocks, only stock names and values are needed 
    # Loop through StockDict and extract values and names of stocks and put them in lists above
    for stock in Dyn_MFA_System.StockDict:
        if 'd' not in stock:
            stocks_Values.append(Dyn_MFA_System.StockDict[stock].Values)
            stocks_Names.append(Dyn_MFA_System.StockDict[stock].Name)
    
    # Bring values into applicable form
    stocks_Values_loop = []
    for i in range(len(MyYears)):
        loop_list = []
        for b in range(int(len(Dyn_MFA_System.StockDict)/2)):
            loop_list.append([stocks_Values[b][:][i][e] for e in range(len(ModelClassification['Element'].Items))])
        stocks_Values_loop.append(loop_list)
    
    
    # Stocks bars should have same color of the associated process and also be linked to the process name
    # Create empty lists
    colors_stocks = []
    stocks_process_Names = []
    
    # Loop through stock names and compare stock number to process ID and save process name and color
    for stock in stocks_Names:
        # Using regular expression to get number of the stock
        match = re.search(r'(\d+)$', stock)
        if match:
            index = int(match.group(1))
            colors_stocks.append(colors_processes[index])
            for process in Dyn_MFA_System.ProcessList:
                if process.ID == index:
                    stocks_process_Names.append(process.Name)
        else:
            print(f'Stock {stock} does not have a numeric suffix.')

    elements = ModelClassification['Element'].Items
    
    # Initiate figure
    fig = go.FigureWidget()
    # max value so the plot is scaled to max value from the beginnning
    max_value = max(max(year_values) for year_values in stocks_Values_loop)
    fig.add_bar(
        x = stocks_process_Names,
        y = stocks_Values_loop[0][0],
        marker_color = colors_stocks
    )

    fig.layout.title = f"""System stocks diagram {elements[0]} (years {MyYears[0]}-{MyYears[-1]}) [t]"""
    display(fig)
  
    # this functions updates the stocks diagram to make it interactive and introduces the slider feature
    def update(element, i=MyYears[0]):
        element_index = elements.index(element)
        fig.data[0].y = [stocks_Values_loop[i-MyYears[0]][b][element_index] for b in range(len(stocks_Values))]
        fig.layout.title = f"""System stocks diagram {element} (year {i}) in Mg"""

    element_dropdown = widgets.Dropdown(
        options = elements,
        value = elements[0],
        description = "element:"
    )
    interact(update, element = element_dropdown, i = (MyYears[0], MyYears[-1], 1));