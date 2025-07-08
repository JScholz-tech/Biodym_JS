# -*- coding: utf-8 -*-
"""
Command Line Interface for the BioDYM MFA Model.

This script provides a user-friendly command-line interface for running
the BioDYM MFA model with various options and configurations.

Usage examples:
    python src/main_cli.py --input data/01_input/250625_Template_CS0.xlsx
    python src/main_cli.py --input data/01_input/250625_Template_CS0.xlsx --output results.xlsx --monte-carlo --iterations 1000
    python src/main_cli.py --help
"""

import os
import sys
import argparse
import pandas as pd
from pathlib import Path

# Add project structure to system path
src_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, src_path)

# Add ODYM framework to path
project_root_parent = os.path.dirname(os.path.dirname(src_path))
odym_path = os.path.join(project_root_parent, 'framework', 'ODYM-master_20241127', 'odym', 'modules')
sys.path.insert(0, odym_path)

# Import BioDYM modules
try:
    import config
    import data_loader
    import system_setup
    import utils
    from engine import solver
    import plotting
    import ODYM_Classes as msc
    from tqdm import tqdm
except ImportError as e:
    print(f"❌ FATAL ERROR: Could not import required modules: {e}")
    print("Please ensure all dependencies are installed and paths are correct.")
    sys.exit(1)


def create_parser():
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="BioDYM MFA Model - Material Flow Analysis Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic run with default settings
  python src/main_cli.py --input data/01_input/250625_Template_CS0.xlsx

  # Run with custom output and Monte Carlo
  python src/main_cli.py --input data/01_input/250625_Template_CS0.xlsx --output results.xlsx --monte-carlo --iterations 1000

  # Run with custom time range
  python src/main_cli.py --input data/01_input/250625_Template_CS0.xlsx --start-year 2020 --end-year 2030

  # Run with verbose output
  python src/main_cli.py --input data/01_input/250625_Template_CS0.xlsx --verbose
        """
    )
    
    # Required arguments
    parser.add_argument(
        '--input', '-i',
        type=str,
        required=True,
        help='Path to the input Excel file (e.g., data/01_input/250625_Template_CS0.xlsx)'
    )
    
    # Optional arguments
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='data/02_output/results.xlsx',
        help='Path for the output Excel file (default: data/02_output/results.xlsx)'
    )
    
    parser.add_argument(
        '--start-year',
        type=int,
        default=config.START_YEAR,
        help=f'Start year for the analysis (default: {config.START_YEAR})'
    )
    
    parser.add_argument(
        '--end-year',
        type=int,
        default=config.END_YEAR,
        help=f'End year for the analysis (default: {config.END_YEAR})'
    )
    
    parser.add_argument(
        '--elements',
        nargs='+',
        default=config.ELEMENTS,
        help=f'Elements to track (default: {config.ELEMENTS})'
    )
    
    parser.add_argument(
        '--monte-carlo', '-mc',
        action='store_true',
        help='Run Monte Carlo simulation instead of deterministic calculation'
    )
    
    parser.add_argument(
        '--iterations',
        type=int,
        default=config.MC_ITERATIONS,
        help=f'Number of Monte Carlo iterations (default: {config.MC_ITERATIONS})'
    )
    
    parser.add_argument(
        '--no-export',
        action='store_true',
        help='Skip exporting results to Excel file'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output with detailed progress information'
    )
    
    parser.add_argument(
        '--summary',
        action='store_true',
        help='Show a detailed summary of results after calculation'
    )
    
    return parser


def validate_input_file(file_path):
    """Validate that the input file exists and is readable."""
    if not os.path.exists(file_path):
        print(f"❌ ERROR: Input file not found: {file_path}")
        print("Please check the file path and try again.")
        return False
    
    if not file_path.endswith(('.xlsx', '.xls')):
        print(f"❌ ERROR: Input file must be an Excel file (.xlsx or .xls): {file_path}")
        return False
    
    return True


def run_mfa_analysis(args):
    """Run the MFA analysis with the given arguments."""
    print("=" * 60)
    print("  🚀 BioDYM MFA Model - Starting Analysis")
    print("=" * 60)
    
    # Validate input file
    if not validate_input_file(args.input):
        return False
    
    # Create output directory if needed
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        if args.verbose:
            print(f"📁 Created output directory: {output_dir}")
    
    # Configuration summary
    print(f"\n📋 Configuration:")
    print(f"   Input file: {args.input}")
    print(f"   Output file: {args.output}")
    print(f"   Time range: {args.start_year} - {args.end_year}")
    print(f"   Elements: {', '.join(args.elements)}")
    print(f"   Monte Carlo: {'Yes' if args.monte_carlo else 'No'}")
    if args.monte_carlo:
        print(f"   Iterations: {args.iterations}")
    
    try:
        # 1. SETUP AND CONFIGURATION
        print(f"\n🔧 Phase 1: Model Setup")
        if args.verbose:
            print("   Defining model scope...")
        
        model_classification, index_table = system_setup.define_model_scope(
            args.start_year, args.end_year, args.elements
        )
        
        if args.verbose:
            print("   Initializing MFA system...")
        
        mfa_system_base = system_setup.initialize_mfa_system(model_classification, index_table)
        
        if args.verbose:
            print("   Loading data and defining processes...")
        
        mfa_system_base, all_excel_data = system_setup.load_and_define_processes(
            mfa_system_base, args.input, data_loader
        )
        
        if args.verbose:
            print("   Loading model parameters...")
        
        dsm_params = data_loader.load_dsm_parameters(all_excel_data)
        fomp_params = data_loader.load_fomp_parameters(all_excel_data)
        uncertainty_params = data_loader.load_uncertainty_definitions(all_excel_data)
        
        if args.verbose:
            print("   Configuring flows and parameters...")
        
        mfa_system_configured, _ = system_setup.define_flows_and_parameters(mfa_system_base, all_excel_data)
        
        print(f"   ✅ Setup complete: {len(mfa_system_configured.ProcessList)} processes, "
              f"{len(mfa_system_configured.FlowDict)} flows, {len(mfa_system_configured.StockDict)} stocks")
        
        # 2. CALCULATION
        print(f"\n🧮 Phase 2: Calculation")
        
        if args.monte_carlo:
            print(f"   Running Monte Carlo simulation ({args.iterations} iterations)...")
            
            mc_run_results = []
            iterator = tqdm(range(args.iterations), desc='MC Progress') if not args.verbose else range(args.iterations)
            
            for i in iterator:
                if args.verbose and i % 10 == 0:
                    print(f"     Progress: {i}/{args.iterations}")
                
                # Sample parameters
                sampled_values = utils.sample_parameters(uncertainty_params)
                tc_updates = {k: v for k, v in sampled_values.items() if k.startswith('TC_')}
                
                # Run calculation
                run_results, _ = solver.run_mfa_calculation(
                    mfa_system_configured, dsm_params, fomp_params, config, tc_updates=tc_updates
                )
                
                # Extract KPIs
                if run_results:
                    final_c_stock_soil = run_results.StockDict['S_8'].Values[-1, 3]
                    current_run_data = sampled_values.copy()
                    current_run_data['run_id'] = i
                    current_run_data['final_C_stock_soil'] = final_c_stock_soil
                    mc_run_results.append(current_run_data)
            
            df_mc_results = pd.DataFrame(mc_run_results)
            mfa_system_with_results = None
            dsm_details = None
            
            print(f"   ✅ Monte Carlo simulation complete!")
            
        else:
            print(f"   Running deterministic calculation...")
            
            mfa_system_with_results, dsm_details = solver.run_mfa_calculation(
                mfa_system_configured, dsm_params, fomp_params, config
            )
            
            df_mc_results = None
            
            print(f"   ✅ Deterministic calculation complete!")
        
        # 3. RESULTS SUMMARY
        if args.summary:
            print(f"\n📊 Results Summary")
            print("-" * 40)
            
            if args.monte_carlo and df_mc_results is not None:
                if 'final_C_stock_soil' in df_mc_results.columns:
                    final_c_stock = df_mc_results['final_C_stock_soil']
                    print(f"🎲 Monte Carlo Results:")
                    print(f"   Final Soil Carbon Stock:")
                    print(f"     Mean: {final_c_stock.mean():.2f} Mg C")
                    print(f"     5th percentile: {final_c_stock.quantile(0.05):.2f} Mg C")
                    print(f"     95th percentile: {final_c_stock.quantile(0.95):.2f} Mg C")
                    print(f"     Standard deviation: {final_c_stock.std():.2f} Mg C")
            else:
                if mfa_system_with_results is not None:
                    print(f"📈 Deterministic Results:")
                    print(f"   Final Stock Values (last year):")
                    for stock_name, stock_obj in mfa_system_with_results.StockDict.items():
                        if stock_name.startswith('S_'):
                            final_values = stock_obj.Values[-1, :]
                            print(f"     {stock_name}: {final_values[0]:.2f} Mg material")
                            if len(final_values) > 3:
                                print(f"            {final_values[3]:.2f} Mg C")
        
        # 4. EXPORT RESULTS
        if not args.no_export:
            print(f"\n💾 Phase 3: Export Results")
            
            if mfa_system_with_results is not None:
                utils.export_results_to_excel(mfa_system_with_results, args.output)
                print(f"   ✅ Results exported to: {args.output}")
            
            if args.monte_carlo and df_mc_results is not None:
                mc_output_path = args.output.replace('.xlsx', '_MonteCarlo.xlsx')
                with pd.ExcelWriter(mc_output_path) as writer:
                    df_mc_results.to_excel(writer, sheet_name='MC_Results', index=False)
                    if 'final_C_stock_soil' in df_mc_results.columns:
                        summary_stats = df_mc_results['final_C_stock_soil'].describe()
                        summary_stats.to_frame('final_C_stock_soil').to_excel(writer, sheet_name='Summary_Stats')
                print(f"   ✅ Monte Carlo results exported to: {mc_output_path}")
        
        print(f"\n" + "=" * 60)
        print(f"  ✅ BioDYM MFA Analysis Complete!")
        print(f"=" * 60)
        
        if not args.no_export:
            print(f"\n📁 Output files:")
            if mfa_system_with_results is not None:
                print(f"   - {args.output}")
            if args.monte_carlo and df_mc_results is not None:
                mc_output_path = args.output.replace('.xlsx', '_MonteCarlo.xlsx')
                print(f"   - {mc_output_path}")
        
        print(f"\n💡 Next steps:")
        print(f"   - Open the exported Excel files for detailed data")
        print(f"   - Use the Jupyter notebook for interactive visualizations")
        print(f"   - Modify parameters and re-run for different scenarios")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: Analysis failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return False


def main():
    """Main function to handle CLI execution."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Run the analysis
    success = run_mfa_analysis(args)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 