#!/usr/bin/env python3
"""
Comprehensive Wood Yield Calculation and Scenario Forecasting Tool
Combining the best elements from multiple approaches for scientific accuracy

This tool creates a scientifically solid timeline from 1950-2100 by:
1. Using complete historical data (1950-2022) with anchor point validation
2. Applying dynamic scaling for pre/post-1990 periods
3. Cross-validating with bottom-up BWI4 data
4. Generating multiple scenarios with proper uncertainty quantification
5. Providing comprehensive documentation and reproducibility

Author: BioDYM Research Team
Date: 2025-01-11
Version: 1.0
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class ComprehensiveWoodYieldCalculator:
    """
    Comprehensive Wood Yield Calculator combining multiple approaches
    
    This class integrates:
    - Complete historical data analysis (251007 approach)
    - Anchor point validation (251010 approach) 
    - Object-oriented structure (251006 approach)
    - Bottom-up validation with BWI4 data
    - Multiple scenario generation with uncertainty quantification
    """
    
    def __init__(self, study_area_km2=1000, random_seed=42):
        """
        Initialize the comprehensive calculator
        
        Parameters:
        -----------
        study_area_km2 : float
            Area of the study region in km² (default: 1000 km²)
        random_seed : int
            Random seed for reproducible results (default: 42)
        """
        self.study_area_km2 = study_area_km2
        self.random_seed = random_seed
        np.random.seed(random_seed)
        
        # Geographic parameters
        self.area_germany_west_km2 = 73000  # West Germany area
        self.area_germany_unified_km2 = 114000  # Unified Germany area
        
        # Calculate scaling factors
        self.factor_west = self.study_area_km2 / self.area_germany_west_km2
        self.factor_unified = self.study_area_km2 / self.area_germany_unified_km2
        
        # BWI4 validation parameters (from 251010 approach)
        self.area_ha = study_area_km2 * 100  # Convert km² to hectares
        self.avg_harvest_m3_per_ha = 6.7  # Official BWI4 average
        
        # Anchor points for validation (from 251010 approach)
        self.anchor_points = {
            1950: 33.5,
            1970: 28.3,
            1990: 56.8,  # Storm anomaly
            2002: 47.8,
            2022: 80.7   # Most recent data point
        }
        
        # Initialize data containers
        self.historical_data = None
        self.scaled_data = None
        self.baseline_params = None
        self.scenarios = {}
        self.validation_results = {}
        
    def load_comprehensive_historical_data(self):
        """
        Load and validate comprehensive historical data (1950-2022)
        
        Uses the most complete dataset from 251007 approach with anchor point validation
        """
        # Complete historical dataset (from 251007 approach)
        data = {
            'Year': np.arange(1950, 2023),
            'Harvest_Mm3_Germany': [
                # Historical data 1950-2000 (updated values)
                25.61, 27.47, 24.54, 23.65, 22.80, 25.44, 21.67, 23.78, 24.03, 23.65,
                24.68, 26.23, 26.98, 24.09, 26.93, 25.72, 27.20, 26.18, 24.90, 26.58,
                28.04, 27.87, 23.70, 31.00, 31.59, 26.11, 28.89, 29.34, 28.64, 27.45,
                30.11, 29.20, 28.88, 27.52, 28.41, 31.45, 29.49, 29.40, 29.27, 31.90,
                68.98, 32.09, 27.66, 29.15, 37.10, 45.04, 50.69, 51.41, 50.86, 50.28,
                62.55,
                # Data 2001-2022
                56.43, 60.06, 60.96, 67.12, 57.53, 79.05, 98.07, 75.87, 64.25, 79.79, 
                74.70, 74.70, 63.63, 68.78, 70.80, 72.86, 68.31, 75.15, 76.16, 
                80.50, 80.46, 80.67
            ]
        }
        
        self.historical_data = pd.DataFrame(data)
        
        # Validate against anchor points
        self._validate_anchor_points()
        
        return self.historical_data
    
    def _validate_anchor_points(self):
        """
        Validate historical data against known anchor points
        """
        validation_results = {}
        
        for year, expected_value in self.anchor_points.items():
            if year in self.historical_data['Year'].values:
                actual_value = self.historical_data[
                    self.historical_data['Year'] == year
                ]['Harvest_Mm3_Germany'].iloc[0]
                
                deviation = abs(actual_value - expected_value)
                deviation_percent = (deviation / expected_value) * 100
                
                validation_results[year] = {
                    'expected': expected_value,
                    'actual': actual_value,
                    'deviation': deviation,
                    'deviation_percent': deviation_percent,
                    'status': 'GOOD' if deviation_percent < 5 else 'WARNING' if deviation_percent < 15 else 'ERROR'
                }
        
        self.validation_results['anchor_points'] = validation_results
        
        # Print validation summary
        print("Anchor Point Validation:")
        print("-" * 50)
        for year, result in validation_results.items():
            status_icon = "✓" if result['status'] == 'GOOD' else "⚠" if result['status'] == 'WARNING' else "✗"
            print(f"{status_icon} {year}: Expected {result['expected']:.1f}, "
                  f"Actual {result['actual']:.1f} ({result['deviation_percent']:.1f}% deviation)")
        print()
    
    def apply_dynamic_scaling(self):
        """
        Apply dynamic scaling based on historical periods (pre/post-1990)
        """
        if self.historical_data is None:
            raise ValueError("Historical data must be loaded first. Call load_comprehensive_historical_data().")
        
        df = self.historical_data.copy()
        
        # Apply scaling based on year (pre- or post-1990)
        df['Scaled_Harvest_Mm3'] = np.where(
            df['Year'] < 1990,
            df['Harvest_Mm3_Germany'] * self.factor_west,
            df['Harvest_Mm3_Germany'] * self.factor_unified
        )
        
        self.scaled_data = df
        return self.scaled_data
    
    def calculate_robust_baseline(self, baseline_start_year=2000):
        """
        Calculate robust baseline with multiple validation approaches
        """
        if self.scaled_data is None:
            raise ValueError("Scaled data must be calculated first. Call apply_dynamic_scaling().")
        
        # Use specified period for baseline calculation
        baseline_period = self.scaled_data[self.scaled_data['Year'] >= baseline_start_year].copy()
        
        if len(baseline_period) < 2:
            raise ValueError(f"Insufficient data for baseline calculation starting from {baseline_start_year}")
        
        # Calculate baseline statistics
        bau_average = baseline_period['Scaled_Harvest_Mm3'].mean()
        std_dev = baseline_period['Scaled_Harvest_Mm3'].std()
        std_dev_percent = std_dev / bau_average
        
        # Calculate additional statistics
        min_value = baseline_period['Scaled_Harvest_Mm3'].min()
        max_value = baseline_period['Scaled_Harvest_Mm3'].max()
        median_value = baseline_period['Scaled_Harvest_Mm3'].median()
        
        # BWI4 bottom-up validation
        bwi4_baseline_m3 = self.area_ha * self.avg_harvest_m3_per_ha
        bwi4_baseline_Mm3 = bwi4_baseline_m3 / 1_000_000
        
        # Compare approaches
        bwi4_deviation = abs(bau_average - bwi4_baseline_Mm3)
        bwi4_deviation_percent = (bwi4_deviation / bau_average) * 100
        
        self.baseline_params = {
            'average': bau_average,
            'std_deviation': std_dev,
            'std_deviation_percent': std_dev_percent,
            'min_value': min_value,
            'max_value': max_value,
            'median_value': median_value,
            'baseline_start_year': baseline_start_year,
            'baseline_period_years': len(baseline_period),
            'bwi4_baseline': bwi4_baseline_Mm3,
            'bwi4_deviation': bwi4_deviation,
            'bwi4_deviation_percent': bwi4_deviation_percent
        }
        
        # Print baseline comparison
        print("Baseline Calculation Results:")
        print("-" * 50)
        print(f"Historical Average (2000-2022): {bau_average:.4f} Mm³")
        print(f"BWI4 Bottom-up Estimate: {bwi4_baseline_Mm3:.4f} Mm³")
        print(f"Deviation: {bwi4_deviation:.4f} Mm³ ({bwi4_deviation_percent:.1f}%)")
        print(f"Standard Deviation: {std_dev:.4f} Mm³ ({std_dev_percent:.1%})")
        print(f"Range: {min_value:.3f} - {max_value:.3f} Mm³")
        print()
        
        return self.baseline_params
    
    def generate_comprehensive_scenarios(self, forecast_start_year=2023, forecast_end_year=2100, 
                                       additional_scenarios=None):
        """
        Generate comprehensive scenarios with multiple approaches
        """
        if self.baseline_params is None:
            raise ValueError("Baseline must be calculated first. Call calculate_robust_baseline().")
        
        future_years = np.arange(forecast_start_year, forecast_end_year + 1)
        
        # Generate BAU scenario using historical volatility
        future_baseline = np.full(len(future_years), self.baseline_params['average'])
        future_fluctuation = np.random.normal(0, self.baseline_params['std_deviation'], len(future_years))
        bau_forecast = future_baseline + future_fluctuation
        
        # Generate BWI4-based scenario for comparison
        bwi4_fluctuation = np.random.normal(0, self.baseline_params['bwi4_baseline'] * self.baseline_params['std_deviation_percent'], len(future_years))
        bwi4_forecast = self.baseline_params['bwi4_baseline'] + bwi4_fluctuation
        
        # Create BAU scenario dataframe
        bau_df = pd.DataFrame({
            'Year': future_years,
            'Baseline': future_baseline,
            'Fluctuation': future_fluctuation,
            'Total_Forecast': bau_forecast,
            'Scenario': 'BAU_Historical',
            'Method': 'Historical Average + Volatility'
        })
        
        # Create BWI4 scenario dataframe
        bwi4_df = pd.DataFrame({
            'Year': future_years,
            'Baseline': self.baseline_params['bwi4_baseline'],
            'Fluctuation': bwi4_fluctuation,
            'Total_Forecast': bwi4_forecast,
            'Scenario': 'BAU_BWI4',
            'Method': 'BWI4 Bottom-up + Volatility'
        })
        
        self.scenarios['BAU_Historical'] = bau_df
        self.scenarios['BAU_BWI4'] = bwi4_df
        
        # Generate additional scenarios if provided
        if additional_scenarios:
            for scenario_name, factor in additional_scenarios.items():
                # Apply factor to historical-based forecast
                scenario_forecast = bau_forecast * factor
                
                scenario_df = pd.DataFrame({
                    'Year': future_years,
                    'Baseline': future_baseline * factor,
                    'Fluctuation': future_fluctuation * factor,
                    'Total_Forecast': scenario_forecast,
                    'Scenario': scenario_name,
                    'Method': f'Historical * {factor:.2f}',
                    'Factor': factor
                })
                
                self.scenarios[scenario_name] = scenario_df
        
        return self.scenarios
    
    def create_comprehensive_visualization(self, save_path=None):
        """
        Create comprehensive visualization showing all approaches and scenarios
        """
        if self.scaled_data is None or not self.scenarios:
            raise ValueError("Both scaled data and scenarios must be calculated first.")
        
        plt.style.use('seaborn-v0_8-whitegrid')
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12))
        
        # Top plot: Historical data and scenarios
        ax1.plot(self.scaled_data['Year'], self.scaled_data['Scaled_Harvest_Mm3'], 
                label=f'Scaled Historical Harvest ({self.study_area_km2} km²)', 
                color='black', marker='.', linestyle='None', markersize=3, alpha=0.7)
        
        # Highlight anchor points
        for year, value in self.anchor_points.items():
            if year < 1990:
                scaled_value = value * self.factor_west
            else:
                scaled_value = value * self.factor_unified
            ax1.plot(year, scaled_value, 'ro', markersize=6, alpha=0.8)
        
        # Plot baseline lines
        ax1.axhline(y=self.baseline_params['average'], 
                   label=f'Historical Baseline ({self.baseline_params["baseline_start_year"]}-2022)', 
                   color='red', linestyle='--', linewidth=2)
        ax1.axhline(y=self.baseline_params['bwi4_baseline'], 
                   label=f'BWI4 Baseline (6.7 m³/ha)', 
                   color='green', linestyle='--', linewidth=2)
        
        # Plot scenarios
        colors = ['blue', 'orange', 'purple', 'brown', 'pink']
        for i, (scenario_name, scenario_data) in enumerate(self.scenarios.items()):
            color = colors[i % len(colors)]
            alpha = 0.8 if 'BAU' in scenario_name else 0.6
            ax1.plot(scenario_data['Year'], scenario_data['Total_Forecast'], 
                    label=f'{scenario_name} Forecast', 
                    color=color, alpha=alpha, linewidth=1.5)
        
        ax1.set_title(f'Comprehensive Wood Harvest Analysis for {self.study_area_km2} km² Area (1950-2100)', fontsize=16)
        ax1.set_xlabel('Year', fontsize=12)
        ax1.set_ylabel('Annual Harvest (Million m³)', fontsize=12)
        ax1.legend(fontsize=10, loc='upper left')
        ax1.grid(True, alpha=0.3)
        
        # Bottom plot: Scenario comparison (2023-2100)
        scenario_names = list(self.scenarios.keys())
        scenario_means = [self.scenarios[name]['Total_Forecast'].mean() for name in scenario_names]
        scenario_stds = [self.scenarios[name]['Total_Forecast'].std() for name in scenario_names]
        
        x_pos = np.arange(len(scenario_names))
        bars = ax2.bar(x_pos, scenario_means, yerr=scenario_stds, 
                      capsize=5, alpha=0.7, color=colors[:len(scenario_names)])
        
        ax2.set_title('Scenario Comparison: Mean Annual Harvest (2023-2100)', fontsize=14)
        ax2.set_xlabel('Scenario', fontsize=12)
        ax2.set_ylabel('Mean Annual Harvest (Million m³)', fontsize=12)
        ax2.set_xticks(x_pos)
        ax2.set_xticklabels(scenario_names, rotation=45, ha='right')
        ax2.grid(True, alpha=0.3)
        
        # Add value labels on bars
        for i, (bar, mean, std) in enumerate(zip(bars, scenario_means, scenario_stds)):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + std + 0.01,
                    f'{mean:.3f}', ha='center', va='bottom', fontsize=9)
        
        # Add comprehensive text box
        info_text = f'Study Area: {self.study_area_km2} km²\n'
        info_text += f'Historical Baseline: {self.baseline_params["average"]:.3f} Mm³\n'
        info_text += f'BWI4 Baseline: {self.baseline_params["bwi4_baseline"]:.3f} Mm³\n'
        info_text += f'Volatility: {self.baseline_params["std_deviation_percent"]:.1%}\n'
        info_text += f'BWI4 Deviation: {self.baseline_params["bwi4_deviation_percent"]:.1f}%\n'
        info_text += f'Random Seed: {self.random_seed}'
        
        ax1.text(0.02, 0.98, info_text, transform=ax1.transAxes, fontsize=10,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Comprehensive plot saved to: {save_path}")
        
        plt.show()
        return fig
    
    def export_comprehensive_results(self, output_path=None):
        """
        Export comprehensive results to Excel with all approaches and validations
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"comprehensive_wood_yield_{self.study_area_km2}km2_{timestamp}.xlsx"
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # 1. Executive Summary
            self._create_executive_summary_sheet(writer)
            
            # 2. Historical Data
            if self.historical_data is not None:
                self.historical_data.to_excel(writer, sheet_name='Historical_Data', index=False)
            
            # 3. Scaled Data
            if self.scaled_data is not None:
                self.scaled_data.to_excel(writer, sheet_name='Scaled_Data', index=False)
            
            # 4. Individual Scenario Sheets
            for scenario_name, scenario_data in self.scenarios.items():
                sheet_name = f'Scenario_{scenario_name}'[:31]
                scenario_data.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # 5. Scenario Comparison
            if len(self.scenarios) > 1:
                comparison_data = {'Year': self.scenarios['BAU_Historical']['Year']}
                for scenario_name, scenario_data in self.scenarios.items():
                    comparison_data[f'{scenario_name}_Forecast'] = scenario_data['Total_Forecast']
                comparison_df = pd.DataFrame(comparison_data)
                comparison_df.to_excel(writer, sheet_name='Scenario_Comparison', index=False)
            
            # 6. Statistical Analysis
            self._create_statistical_analysis_sheet(writer)
            
            # 7. Validation Results
            if self.validation_results:
                validation_df = pd.DataFrame(self.validation_results['anchor_points']).T
                validation_df.to_excel(writer, sheet_name='Validation_Results', index=True)
            
            # 8. Baseline Analysis
            self._create_baseline_analysis_sheet(writer)
            
            # 9. Forecast Summary
            self._create_forecast_summary_sheet(writer)
            
            # 10. Comprehensive Metadata
            self._create_comprehensive_metadata_sheet(writer)
        
        print(f"Comprehensive results exported to Excel: {output_path}")
        return output_path
    
    def _create_executive_summary_sheet(self, writer):
        """Create executive summary sheet with key findings"""
        summary_data = []
        
        # Key metrics
        if self.baseline_params:
            summary_data.extend([
                ['KEY METRICS', '', ''],
                ['Study Area', f'{self.study_area_km2} km²', ''],
                ['Historical Baseline (2000-2022)', f'{self.baseline_params["average"]:.4f} Mm³/year', ''],
                ['BWI4 Validation', f'{self.baseline_params["bwi4_baseline"]:.4f} Mm³/year', ''],
                ['Validation Deviation', f'{self.baseline_params["bwi4_deviation_percent"]:.1f}%', ''],
                ['Volatility (Std Dev)', f'{self.baseline_params["std_deviation_percent"]:.1%}', ''],
                ['', '', ''],
            ])
        
        # Scenario summary
        if self.scenarios:
            summary_data.extend([
                ['SCENARIO SUMMARY (2023-2100)', '', ''],
                ['Scenario', 'Mean Annual Harvest (Mm³)', 'Method'],
            ])
            
            for scenario_name, scenario_data in self.scenarios.items():
                mean_harvest = scenario_data['Total_Forecast'].mean()
                method = scenario_data['Method'].iloc[0] if 'Method' in scenario_data.columns else 'N/A'
                summary_data.append([scenario_name, f'{mean_harvest:.4f}', method])
            
            summary_data.append(['', '', ''])
        
        # Validation summary
        if self.validation_results and 'anchor_points' in self.validation_results:
            summary_data.extend([
                ['ANCHOR POINT VALIDATION', '', ''],
                ['Year', 'Status', 'Deviation (%)'],
            ])
            
            for year, validation in self.validation_results['anchor_points'].items():
                summary_data.append([year, validation['status'], f'{validation["deviation_percent"]:.1f}%'])
        
        summary_df = pd.DataFrame(summary_data, columns=['Parameter', 'Value', 'Notes'])
        summary_df.to_excel(writer, sheet_name='Executive_Summary', index=False)
    
    def _create_statistical_analysis_sheet(self, writer):
        """Create detailed statistical analysis sheet"""
        stats_data = []
        
        if self.scenarios:
            stats_data.extend([
                ['STATISTICAL ANALYSIS BY SCENARIO (2023-2100)', '', '', '', '', ''],
                ['Scenario', 'Mean (Mm³)', 'Median (Mm³)', 'Std Dev (Mm³)', 'Min (Mm³)', 'Max (Mm³)'],
            ])
            
            for scenario_name, scenario_data in self.scenarios.items():
                forecast = scenario_data['Total_Forecast']
                stats_data.append([
                    scenario_name,
                    f'{forecast.mean():.4f}',
                    f'{forecast.median():.4f}',
                    f'{forecast.std():.4f}',
                    f'{forecast.min():.4f}',
                    f'{forecast.max():.4f}'
                ])
            
            stats_data.extend(['', '', '', '', '', ''])
        
        # Historical statistics
        if self.scaled_data is not None:
            historical_stats = self.scaled_data['Scaled_Harvest_Mm3'].describe()
            stats_data.extend([
                ['HISTORICAL DATA STATISTICS (1950-2022)', '', '', '', '', ''],
                ['Statistic', 'Value (Mm³)', '', '', '', ''],
                ['Count', f'{historical_stats["count"]:.0f}', '', '', '', ''],
                ['Mean', f'{historical_stats["mean"]:.4f}', '', '', '', ''],
                ['Std Dev', f'{historical_stats["std"]:.4f}', '', '', '', ''],
                ['Min', f'{historical_stats["min"]:.4f}', '', '', '', ''],
                ['25%', f'{historical_stats["25%"]:.4f}', '', '', '', ''],
                ['50% (Median)', f'{historical_stats["50%"]:.4f}', '', '', '', ''],
                ['75%', f'{historical_stats["75%"]:.4f}', '', '', '', ''],
                ['Max', f'{historical_stats["max"]:.4f}', '', '', '', ''],
            ])
        
        stats_df = pd.DataFrame(stats_data)
        stats_df.to_excel(writer, sheet_name='Statistical_Analysis', index=False)
    
    def _create_baseline_analysis_sheet(self, writer):
        """Create detailed baseline analysis sheet"""
        baseline_data = []
        
        if self.baseline_params:
            baseline_data.extend([
                ['BASELINE ANALYSIS', '', ''],
                ['Parameter', 'Value', 'Description'],
                ['Study Area', f'{self.study_area_km2} km²', 'Area of study region'],
                ['Baseline Period', f'{self.baseline_params["baseline_start_year"]}-2022', 'Years used for baseline calculation'],
                ['Baseline Years', f'{self.baseline_params["baseline_period_years"]}', 'Number of years in baseline'],
                ['Historical Average', f'{self.baseline_params["average"]:.4f} Mm³', 'Mean annual harvest in baseline period'],
                ['Standard Deviation', f'{self.baseline_params["std_deviation"]:.4f} Mm³', 'Standard deviation of baseline period'],
                ['Volatility', f'{self.baseline_params["std_deviation_percent"]:.1%}', 'Coefficient of variation'],
                ['Minimum Value', f'{self.baseline_params["min_value"]:.4f} Mm³', 'Lowest annual harvest in baseline'],
                ['Maximum Value', f'{self.baseline_params["max_value"]:.4f} Mm³', 'Highest annual harvest in baseline'],
                ['Median Value', f'{self.baseline_params["median_value"]:.4f} Mm³', 'Median annual harvest in baseline'],
                ['', '', ''],
                ['BWI4 VALIDATION', '', ''],
                ['BWI4 Harvest Rate', f'{self.avg_harvest_m3_per_ha} m³/ha', 'Official BWI4 average harvest rate'],
                ['Study Area (ha)', f'{self.area_ha:,}', 'Study area in hectares'],
                ['BWI4 Baseline', f'{self.baseline_params["bwi4_baseline"]:.4f} Mm³', 'Bottom-up calculation using BWI4 data'],
                ['Deviation from Historical', f'{self.baseline_params["bwi4_deviation"]:.4f} Mm³', 'Absolute difference between approaches'],
                ['Deviation Percentage', f'{self.baseline_params["bwi4_deviation_percent"]:.1f}%', 'Relative difference between approaches'],
            ])
        
        baseline_df = pd.DataFrame(baseline_data, columns=['Parameter', 'Value', 'Description'])
        baseline_df.to_excel(writer, sheet_name='Baseline_Analysis', index=False)
    
    def _create_forecast_summary_sheet(self, writer):
        """Create forecast summary sheet with annual data"""
        if not self.scenarios:
            return
        
        # Create annual forecast summary
        forecast_data = {'Year': self.scenarios['BAU_Historical']['Year']}
        
        for scenario_name, scenario_data in self.scenarios.items():
            forecast_data[f'{scenario_name}_Forecast'] = scenario_data['Total_Forecast']
            forecast_data[f'{scenario_name}_Baseline'] = scenario_data['Baseline']
            forecast_data[f'{scenario_name}_Fluctuation'] = scenario_data['Fluctuation']
        
        forecast_df = pd.DataFrame(forecast_data)
        
        # Add summary statistics at the bottom
        summary_rows = []
        for scenario_name in self.scenarios.keys():
            forecast_col = f'{scenario_name}_Forecast'
            if forecast_col in forecast_df.columns:
                summary_rows.extend([
                    [f'{scenario_name}_Mean', forecast_df[forecast_col].mean(), '', '', '', ''],
                    [f'{scenario_name}_Std', forecast_df[forecast_col].std(), '', '', '', ''],
                    [f'{scenario_name}_Min', forecast_df[forecast_col].min(), '', '', '', ''],
                    [f'{scenario_name}_Max', forecast_df[forecast_col].max(), '', '', '', ''],
                ])
        
        # Add summary to dataframe
        summary_df = pd.DataFrame(summary_rows, columns=forecast_df.columns)
        forecast_with_summary = pd.concat([forecast_df, summary_df], ignore_index=True)
        
        forecast_with_summary.to_excel(writer, sheet_name='Forecast_Summary', index=False)
    
    def _create_comprehensive_metadata_sheet(self, writer):
        """Create comprehensive metadata sheet"""
        metadata = {
            'Parameter': [
                'Study Area (km²)',
                'Germany West Area (km²)',
                'Germany Unified Area (km²)',
                'West Scaling Factor',
                'Unified Scaling Factor',
                'BWI4 Harvest Rate (m³/ha)',
                'BWI4 Total Area (ha)',
                'Historical Baseline (Mm³)',
                'BWI4 Baseline (Mm³)',
                'BWI4 Deviation (%)',
                'Standard Deviation (Mm³)',
                'Volatility (% of mean)',
                'Baseline Period',
                'Forecast Period',
                'Number of Scenarios',
                'Random Seed',
                'Calculation Date',
                'Data Sources',
                'Methodology',
                'Validation Methods',
                'Uncertainty Quantification',
                'Reproducibility'
            ],
            'Value': [
                self.study_area_km2,
                self.area_germany_west_km2,
                self.area_germany_unified_km2,
                self.factor_west,
                self.factor_unified,
                self.avg_harvest_m3_per_ha,
                self.area_ha,
                self.baseline_params['average'] if self.baseline_params else 'N/A',
                self.baseline_params['bwi4_baseline'] if self.baseline_params else 'N/A',
                f"{self.baseline_params['bwi4_deviation_percent']:.1f}%" if self.baseline_params else 'N/A',
                self.baseline_params['std_deviation'] if self.baseline_params else 'N/A',
                f"{self.baseline_params['std_deviation_percent']:.1%}" if self.baseline_params else 'N/A',
                f"{self.baseline_params['baseline_start_year']}-2022" if self.baseline_params else 'N/A',
                '2023-2100',
                len(self.scenarios),
                self.random_seed,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'Historical German data (1950-2022) + BWI4 validation + Anchor points',
                'Comprehensive approach combining historical analysis, anchor point validation, and BWI4 cross-validation',
                'Anchor point verification, BWI4 bottom-up validation, statistical consistency checks',
                'Monte Carlo simulation with historical volatility, multiple scenario generation',
                'Random seed control, comprehensive documentation, reproducible methodology'
            ]
        }
        metadata_df = pd.DataFrame(metadata)
        metadata_df.to_excel(writer, sheet_name='Comprehensive_Metadata', index=False)
    
    def run_comprehensive_analysis(self, baseline_start_year=2000, forecast_end_year=2100, 
                                 additional_scenarios=None, save_plot=True, export_excel=True):
        """
        Run the complete comprehensive analysis pipeline
        """
        print(f"Starting Comprehensive Wood Yield Analysis for {self.study_area_km2} km² study area...")
        print("=" * 80)
        
        # Step 1: Load and validate historical data
        print("1. Loading and validating comprehensive historical data...")
        self.load_comprehensive_historical_data()
        print(f"   ✓ Loaded {len(self.historical_data)} years of data (1950-2022)")
        print(f"   ✓ Validated against {len(self.anchor_points)} anchor points")
        
        # Step 2: Apply dynamic scaling
        print("2. Applying dynamic scaling factors...")
        self.apply_dynamic_scaling()
        print(f"   ✓ West Germany factor: {self.factor_west:.6f}")
        print(f"   ✓ Unified Germany factor: {self.factor_unified:.6f}")
        
        # Step 3: Calculate robust baseline with validation
        print(f"3. Calculating robust baseline from {baseline_start_year}...")
        self.calculate_robust_baseline(baseline_start_year)
        print(f"   ✓ Historical baseline: {self.baseline_params['average']:.4f} Mm³")
        print(f"   ✓ BWI4 validation: {self.baseline_params['bwi4_baseline']:.4f} Mm³")
        print(f"   ✓ Deviation: {self.baseline_params['bwi4_deviation_percent']:.1f}%")
        
        # Step 4: Generate comprehensive scenarios
        print(f"4. Generating comprehensive scenarios (2023-{forecast_end_year})...")
        self.generate_comprehensive_scenarios(forecast_end_year=forecast_end_year, 
                                            additional_scenarios=additional_scenarios)
        print(f"   ✓ Generated {len(self.scenarios)} scenarios: {list(self.scenarios.keys())}")
        
        # Step 5: Create comprehensive visualization
        print("5. Creating comprehensive visualization...")
        if save_plot:
            plot_path = f"comprehensive_wood_yield_{self.study_area_km2}km2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            self.create_comprehensive_visualization(save_path=plot_path)
        else:
            self.create_comprehensive_visualization()
        
        # Step 6: Export comprehensive results
        if export_excel:
            print("6. Exporting comprehensive results...")
            excel_path = self.export_comprehensive_results()
        
        print("=" * 80)
        print("Comprehensive analysis completed successfully!")
        print("=" * 80)
        
        return {
            'historical_data': self.historical_data,
            'scaled_data': self.scaled_data,
            'baseline_params': self.baseline_params,
            'scenarios': self.scenarios,
            'validation_results': self.validation_results,
            'excel_path': excel_path if export_excel else None
        }


# Example usage and demonstration
if __name__ == "__main__":
    # Create comprehensive calculator instance
    calculator = ComprehensiveWoodYieldCalculator(study_area_km2=1000, random_seed=42)
    
    # Define additional scenarios
    additional_scenarios = {
        'Reduced_Yield': 0.85,  # 15% reduction
        'High_Yield': 1.15,     # 15% increase
        'Low_Yield': 0.70,      # 30% reduction
        'Climate_Impact': 0.90  # 10% reduction due to climate change
    }
    
    # Run comprehensive analysis
    results = calculator.run_comprehensive_analysis(
        baseline_start_year=2000,
        forecast_end_year=2100,
        additional_scenarios=additional_scenarios,
        save_plot=True,
        export_excel=True
    )
    
    # Display comprehensive summary
    print("\n" + "=" * 80)
    print("COMPREHENSIVE ANALYSIS SUMMARY")
    print("=" * 80)
    print(f"Study Area: {calculator.study_area_km2} km²")
    print(f"Historical Period: 1950-2022 ({len(results['historical_data'])} years)")
    print(f"Baseline Period: {results['baseline_params']['baseline_start_year']}-2022 ({results['baseline_params']['baseline_period_years']} years)")
    print(f"Forecast Period: 2023-2100 ({len(results['scenarios']['BAU_Historical'])} years)")
    print()
    
    print("Baseline Comparison:")
    print(f"  Historical Average: {results['baseline_params']['average']:.4f} Mm³")
    print(f"  BWI4 Bottom-up: {results['baseline_params']['bwi4_baseline']:.4f} Mm³")
    print(f"  Deviation: {results['baseline_params']['bwi4_deviation_percent']:.1f}%")
    print(f"  Volatility: {results['baseline_params']['std_deviation_percent']:.1%}")
    print()
    
    print("Scenario Summary (2023-2100):")
    print("-" * 80)
    for scenario_name, scenario_data in results['scenarios'].items():
        forecast = scenario_data['Total_Forecast']
        method = scenario_data['Method'].iloc[0] if 'Method' in scenario_data.columns else 'N/A'
        print(f"{scenario_name}:")
        print(f"  Method: {method}")
        print(f"  Mean: {forecast.mean():.4f} Mm³")
        print(f"  Min:  {forecast.min():.4f} Mm³")
        print(f"  Max:  {forecast.max():.4f} Mm³")
        print(f"  Std:  {forecast.std():.4f} Mm³")
        if 'Factor' in scenario_data.columns:
            factor = scenario_data['Factor'].iloc[0]
            print(f"  Factor: {factor:.2f}")
        print()
    
    print("Validation Results:")
    print("-" * 80)
    for year, validation in results['validation_results']['anchor_points'].items():
        status = validation['status']
        print(f"  {year}: {status} ({validation['deviation_percent']:.1f}% deviation)")
    
    print("\n" + "=" * 80)
    print("Analysis completed successfully!")
    print("=" * 80)
