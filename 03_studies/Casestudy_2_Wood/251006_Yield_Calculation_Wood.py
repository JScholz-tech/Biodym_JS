import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from datetime import datetime

class WoodYieldCalculator:
    """
    Wood Yield Calculation and Scenario Forecasting Tool
    
    This class handles the calculation of wood harvest yields for a study area
    based on German national data, including scaling, scenario analysis, and forecasting.
    """
    
    def __init__(self, study_area_km2=1000):
        """
        Initialize the calculator with study area parameters.
        
        Parameters:
        -----------
        study_area_km2 : float
            Area of the study region in km² (default: 1000 km²)
        """
        self.study_area_km2 = study_area_km2
        self.area_germany_west_km2 = 73000  # West Germany area
        self.area_germany_unified_km2 = 114000  # Unified Germany area
        
        # Calculate scaling factors
        self.factor_west = self.study_area_km2 / self.area_germany_west_km2
        self.factor_unified = self.study_area_km2 / self.area_germany_unified_km2
        
        # Initialize data containers
        self.historical_data = None
        self.scaled_data = None
        self.baseline_params = None
        self.scenarios = {}
        
    def load_historical_data(self):
        """
        Load historical wood harvest data for Germany (1950-2022).
        
        Returns:
        --------
        pd.DataFrame
            Historical harvest data with columns: Year, Harvest_Mm3_Germany
        """
        data = {
            'Year': np.arange(1950, 2023),
            'Harvest_Mm3_Germany': [
                29.21, 27.57, 24.54, 24.34, 22.80, 25.44, 21.61, 23.78, 24.03, 23.65, 
                24.68, 24.97, 25.08, 24.09, 26.66, 25.72, 27.40, 26.18, 24.90, 26.96, 
                28.01, 27.87, 29.74, 31.00, 31.59, 30.13, 28.89, 29.34, 28.61, 27.45, 
                30.11, 29.20, 28.88, 29.46, 28.41, 31.45, 29.49, 29.40, 29.27, 31.09, 
                68.98, 52.09, 27.56, 29.15, 31.95, 45.04, 50.69, 51.41, 50.86, 50.28, 
                53.55, 56.43, 60.06, 60.96, 67.12, 57.53, 79.05, 98.07, 75.87, 64.25, 
                79.79, 74.70, 74.70, 63.63, 68.78, 70.80, 72.86, 68.31, 75.15, 76.16, 
                80.50, 80.46, 80.67
            ]
        }
        
        self.historical_data = pd.DataFrame(data)
        return self.historical_data
    
    def apply_scaling(self):
        """
        Apply dynamic scaling based on historical periods (pre/post 1990).
        
        Returns:
        --------
        pd.DataFrame
            Scaled data with additional column: Scaled_Harvest_Mm3
        """
        if self.historical_data is None:
            raise ValueError("Historical data must be loaded first. Call load_historical_data().")
        
        df = self.historical_data.copy()
        
        # Apply scaling based on year (pre- or post-1990)
        df['Scaled_Harvest_Mm3'] = np.where(
            df['Year'] < 1990,
            df['Harvest_Mm3_Germany'] * self.factor_west,
            df['Harvest_Mm3_Germany'] * self.factor_unified
        )
        
        self.scaled_data = df
        return self.scaled_data
    
    def calculate_baseline(self, baseline_start_year=2000):
        """
        Calculate BAU baseline from scaled historical data.
        
        Parameters:
        -----------
        baseline_start_year : int
            Starting year for baseline calculation (default: 2000)
            
        Returns:
        --------
        dict
            Dictionary containing baseline parameters and statistics
        """
        if self.scaled_data is None:
            raise ValueError("Scaled data must be calculated first. Call apply_scaling().")
        
        # Use specified period for baseline calculation
        baseline_period = self.scaled_data[self.scaled_data['Year'] >= baseline_start_year].copy()
        
        if len(baseline_period) < 2:
            raise ValueError(f"Insufficient data for baseline calculation starting from {baseline_start_year}")
        
        # Calculate baseline statistics
        bau_average = baseline_period['Scaled_Harvest_Mm3'].mean()
        std_dev = baseline_period['Scaled_Harvest_Mm3'].std()
        
        # Calculate additional statistics
        min_value = baseline_period['Scaled_Harvest_Mm3'].min()
        max_value = baseline_period['Scaled_Harvest_Mm3'].max()
        median_value = baseline_period['Scaled_Harvest_Mm3'].median()
        
        self.baseline_params = {
            'average': bau_average,
            'std_deviation': std_dev,
            'min_value': min_value,
            'max_value': max_value,
            'median_value': median_value,
            'baseline_start_year': baseline_start_year,
            'baseline_period_years': len(baseline_period)
        }
        
        return self.baseline_params
    
    def generate_scenarios(self, forecast_start_year=2023, forecast_end_year=2100, 
                          random_seed=None, additional_scenarios=None):
        """
        Generate multiple scenarios based on baseline and historical variability.
        
        Parameters:
        -----------
        forecast_start_year : int
            Starting year for forecast (default: 2023)
        forecast_end_year : int
            Ending year for forecast (default: 2100)
        random_seed : int, optional
            Random seed for reproducible results
        additional_scenarios : dict, optional
            Dictionary of additional scenarios with names and factors
            e.g., {'Reduced_Yield': 0.85, 'High_Yield': 1.15}
            
        Returns:
        --------
        dict
            Dictionary containing all scenario dataframes
        """
        if self.baseline_params is None:
            raise ValueError("Baseline must be calculated first. Call calculate_baseline().")
        
        if random_seed is not None:
            np.random.seed(random_seed)
        
        future_years = np.arange(forecast_start_year, forecast_end_year + 1)
        
        # Generate BAU scenario (baseline + fluctuation)
        future_baseline = np.full(len(future_years), self.baseline_params['average'])
        future_fluctuation = np.random.normal(0, self.baseline_params['std_deviation'], len(future_years))
        bau_forecast = future_baseline + future_fluctuation
        
        # Create BAU scenario dataframe
        bau_df = pd.DataFrame({
            'Year': future_years,
            'Baseline': future_baseline,
            'Fluctuation': future_fluctuation,
            'Total_Forecast': bau_forecast,
            'Scenario': 'BAU'
        })
        
        self.scenarios['BAU'] = bau_df
        
        # Generate additional scenarios if provided
        if additional_scenarios:
            for scenario_name, factor in additional_scenarios.items():
                scenario_forecast = bau_forecast * factor
                
                scenario_df = pd.DataFrame({
                    'Year': future_years,
                    'Baseline': future_baseline * factor,
                    'Fluctuation': future_fluctuation * factor,
                    'Total_Forecast': scenario_forecast,
                    'Scenario': scenario_name,
                    'Factor': factor
                })
                
                self.scenarios[scenario_name] = scenario_df
        
        return self.scenarios
    
    def create_visualization(self, save_path=None, show_scenarios=None):
        """
        Create visualization of historical data, baseline, and scenarios.
        
        Parameters:
        -----------
        save_path : str, optional
            Path to save the plot (if None, only display)
        show_scenarios : list, optional
            List of scenario names to show (if None, show all)
            
        Returns:
        --------
        matplotlib.figure.Figure
            The created figure
        """
        if self.scaled_data is None or not self.scenarios:
            raise ValueError("Both scaled data and scenarios must be calculated first.")
        
        plt.style.use('seaborn-v0_8-whitegrid')
        fig, ax = plt.subplots(figsize=(15, 8))
        
        # Plot historical data
        ax.plot(self.scaled_data['Year'], self.scaled_data['Scaled_Harvest_Mm3'], 
                label=f'Scaled Historical Harvest ({self.study_area_km2} km²)', 
                color='black', marker='.', linestyle='None', markersize=4)
        
        # Plot baseline
        ax.axhline(y=self.baseline_params['average'], 
                  label=f'BAU Baseline ({self.baseline_params["baseline_start_year"]}-2022 Average)', 
                  color='red', linestyle='--', linewidth=2)
        
        # Plot scenarios
        colors = ['blue', 'green', 'orange', 'purple', 'brown']
        scenario_names = show_scenarios if show_scenarios else list(self.scenarios.keys())
        
        for i, scenario_name in enumerate(scenario_names):
            if scenario_name in self.scenarios:
                scenario_data = self.scenarios[scenario_name]
                color = colors[i % len(colors)]
                alpha = 0.8 if scenario_name == 'BAU' else 0.6
                
                ax.plot(scenario_data['Year'], scenario_data['Total_Forecast'], 
                       label=f'{scenario_name} Forecast (2023-2100)', 
                       color=color, alpha=alpha, linewidth=1.5)
        
        ax.set_title(f'Scenario-Based Wood Harvest Forecast for {self.study_area_km2} km² Area', fontsize=16)
        ax.set_xlabel('Year', fontsize=12)
        ax.set_ylabel('Annual Harvest (Million m³)', fontsize=12)
        ax.legend(fontsize=11)
        ax.grid(True, alpha=0.3)
        
        # Add text box with baseline information
        baseline_text = f'Baseline Average: {self.baseline_params["average"]:.3f} Mm³\n'
        baseline_text += f'Std Deviation: {self.baseline_params["std_deviation"]:.3f} Mm³\n'
        baseline_text += f'Period: {self.baseline_params["baseline_start_year"]}-2022\n'
        baseline_text += f'Years: {self.baseline_params["baseline_period_years"]}'
        
        ax.text(0.02, 0.98, baseline_text, transform=ax.transAxes, fontsize=10,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Plot saved to: {save_path}")
        
        plt.show()
        return fig
    
    def export_to_excel(self, output_path=None, include_metadata=True):
        """
        Export all data and results to Excel file.
        
        Parameters:
        -----------
        output_path : str, optional
            Path for Excel file (if None, auto-generate filename)
        include_metadata : bool
            Whether to include metadata sheet (default: True)
            
        Returns:
        --------
        str
            Path to the created Excel file
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"wood_yield_scenarios_{self.study_area_km2}km2_{timestamp}.xlsx"
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Historical data
            if self.historical_data is not None:
                self.historical_data.to_excel(writer, sheet_name='Historical_Data', index=False)
            
            # Scaled data
            if self.scaled_data is not None:
                self.scaled_data.to_excel(writer, sheet_name='Scaled_Data', index=False)
            
            # Individual scenario sheets
            for scenario_name, scenario_data in self.scenarios.items():
                sheet_name = f'Scenario_{scenario_name}'[:31]  # Excel sheet name limit
                scenario_data.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Combined scenarios sheet
            if self.scenarios:
                combined_data = []
                for scenario_name, scenario_data in self.scenarios.items():
                    combined_data.append(scenario_data)
                combined_df = pd.concat(combined_data, ignore_index=True)
                combined_df.to_excel(writer, sheet_name='All_Scenarios', index=False)
            
            # Scenario comparison sheet
            if len(self.scenarios) > 1:
                comparison_data = {'Year': self.scenarios['BAU']['Year']}
                for scenario_name, scenario_data in self.scenarios.items():
                    comparison_data[f'{scenario_name}_Forecast'] = scenario_data['Total_Forecast']
                comparison_df = pd.DataFrame(comparison_data)
                comparison_df.to_excel(writer, sheet_name='Scenario_Comparison', index=False)
            
            # Metadata and parameters
            if include_metadata:
                metadata = {
                    'Parameter': [
                        'Study Area (km²)',
                        'Germany West Area (km²)',
                        'Germany Unified Area (km²)',
                        'West Scaling Factor',
                        'Unified Scaling Factor',
                        'Baseline Start Year',
                        'Baseline Average (Mm³)',
                        'Baseline Std Deviation (Mm³)',
                        'Baseline Min Value (Mm³)',
                        'Baseline Max Value (Mm³)',
                        'Baseline Median Value (Mm³)',
                        'Baseline Period Years',
                        'Forecast Start Year',
                        'Forecast End Year',
                        'Number of Scenarios',
                        'Calculation Date'
                    ],
                    'Value': [
                        self.study_area_km2,
                        self.area_germany_west_km2,
                        self.area_germany_unified_km2,
                        self.factor_west,
                        self.factor_unified,
                        self.baseline_params['baseline_start_year'] if self.baseline_params else 'N/A',
                        self.baseline_params['average'] if self.baseline_params else 'N/A',
                        self.baseline_params['std_deviation'] if self.baseline_params else 'N/A',
                        self.baseline_params['min_value'] if self.baseline_params else 'N/A',
                        self.baseline_params['max_value'] if self.baseline_params else 'N/A',
                        self.baseline_params['median_value'] if self.baseline_params else 'N/A',
                        self.baseline_params['baseline_period_years'] if self.baseline_params else 'N/A',
                        self.scenarios['BAU']['Year'].min() if self.scenarios else 'N/A',
                        self.scenarios['BAU']['Year'].max() if self.scenarios else 'N/A',
                        len(self.scenarios),
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ]
                }
                metadata_df = pd.DataFrame(metadata)
                metadata_df.to_excel(writer, sheet_name='Metadata', index=False)
        
        print(f"Data exported to Excel: {output_path}")
        return output_path
    
    def run_complete_analysis(self, baseline_start_year=2000, forecast_end_year=2100, 
                            random_seed=42, additional_scenarios=None, save_plot=True, export_excel=True):
        """
        Run the complete analysis pipeline.
        
        Parameters:
        -----------
        baseline_start_year : int
            Starting year for baseline calculation
        forecast_end_year : int
            Ending year for forecast
        random_seed : int
            Random seed for reproducible results
        additional_scenarios : dict, optional
            Additional scenarios to generate
        save_plot : bool
            Whether to save the plot
        export_excel : bool
            Whether to export to Excel
            
        Returns:
        --------
        dict
            Dictionary containing all results
        """
        print(f"Starting Wood Yield Scenario Analysis for {self.study_area_km2} km² study area...")
        print("=" * 70)
        
        # Step 1: Load historical data
        print("1. Loading historical data...")
        self.load_historical_data()
        print(f"   Loaded {len(self.historical_data)} years of data (1950-2022)")
        
        # Step 2: Apply scaling
        print("2. Applying scaling factors...")
        self.apply_scaling()
        print(f"   West Germany factor: {self.factor_west:.6f}")
        print(f"   Unified Germany factor: {self.factor_unified:.6f}")
        
        # Step 3: Calculate baseline
        print(f"3. Calculating baseline from {baseline_start_year}...")
        self.calculate_baseline(baseline_start_year)
        print(f"   BAU Baseline: {self.baseline_params['average']:.4f} Mm³")
        print(f"   Standard deviation: {self.baseline_params['std_deviation']:.4f} Mm³")
        print(f"   Range: {self.baseline_params['min_value']:.3f} - {self.baseline_params['max_value']:.3f} Mm³")
        
        # Step 4: Generate scenarios
        print(f"4. Generating scenarios (2023-{forecast_end_year})...")
        self.generate_scenarios(forecast_end_year=forecast_end_year, random_seed=random_seed, 
                               additional_scenarios=additional_scenarios)
        print(f"   Generated {len(self.scenarios)} scenarios: {list(self.scenarios.keys())}")
        
        # Step 5: Create visualization
        print("5. Creating visualization...")
        if save_plot:
            plot_path = f"wood_yield_scenarios_{self.study_area_km2}km2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            self.create_visualization(save_path=plot_path)
        else:
            self.create_visualization()
        
        # Step 6: Export to Excel
        if export_excel:
            print("6. Exporting to Excel...")
            excel_path = self.export_to_excel()
        
        print("=" * 70)
        print("Scenario analysis completed successfully!")
        
        return {
            'historical_data': self.historical_data,
            'scaled_data': self.scaled_data,
            'baseline_params': self.baseline_params,
            'scenarios': self.scenarios,
            'excel_path': excel_path if export_excel else None
        }


# Example usage and demonstration
if __name__ == "__main__":
    # Create calculator instance
    calculator = WoodYieldCalculator(study_area_km2=1000)
    
    # Define additional scenarios
    additional_scenarios = {
        'Reduced_Yield': 0.85,  # 15% reduction
        'High_Yield': 1.15,     # 15% increase
        'Low_Yield': 0.70       # 30% reduction
    }
    
    # Run complete analysis
    results = calculator.run_complete_analysis(
        baseline_start_year=2000,
        forecast_end_year=2100,
        random_seed=42,
        additional_scenarios=additional_scenarios,
        save_plot=True,
        export_excel=True
    )
    
    # Display summary statistics
    print("\nSummary Statistics:")
    print("-" * 40)
    print(f"Historical period: 1950-2022 ({len(results['historical_data'])} years)")
    print(f"Baseline period: {results['baseline_params']['baseline_start_year']}-2022 ({results['baseline_params']['baseline_period_years']} years)")
    print(f"Forecast period: 2023-2100 ({len(results['scenarios']['BAU'])} years)")
    print(f"Study area: {calculator.study_area_km2} km²")
    
    # Show scenario summaries
    print(f"\nScenario Summary (2023-2100):")
    print("-" * 40)
    for scenario_name, scenario_data in results['scenarios'].items():
        forecast_summary = scenario_data['Total_Forecast'].describe()
        print(f"{scenario_name}:")
        print(f"  Mean: {forecast_summary['mean']:.2f} Mm³")
        print(f"  Min:  {forecast_summary['min']:.2f} Mm³")
        print(f"  Max:  {forecast_summary['max']:.2f} Mm³")
        if 'Factor' in scenario_data.columns:
            factor = scenario_data['Factor'].iloc[0]
            print(f"  Factor: {factor:.2f}")
        print()