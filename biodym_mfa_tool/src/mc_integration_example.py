# -*- coding: utf-8 -*-
"""
Monte Carlo Integration Example

This example shows exactly how the new codelist system integrates
with the existing Monte Carlo workflow.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional

def demonstrate_mc_integration():
    """
    Demonstrate how the new codelist system integrates with existing MC workflow.
    """
    
    print("🎲 MONTE CARLO INTEGRATION EXAMPLE")
    print("=" * 60)
    
    # Simulate existing system data
    mfa_system = "mock_mfa_system"
    dsm_params = {'6': {'lifetimes': {'Mean': [10, 15], 'StdDev': [2, 3]}}}
    fomp_params = {'8': {'k1': 0.05, 'k2': 0.005}}
    flows_df = pd.DataFrame({
        'Flow_ID': ['F_00_01', 'F_01_02'],
        'Start_Process_Name': ['Harvest', 'Processing'],
        'End_Process_Name': ['Processing', 'Storage'],
        'TC_Value': [0.8, 0.9]
    })
    
    print("\n📊 STEP 1: User selects parameters via interface")
    print("Instead of typing in Excel, user sees:")
    
    # Simulate user selection
    user_selections = [
        "Transfer Coefficient: Harvest → Processing",
        "DSM Process 6 - Short-lived - Mean Lifetime"
    ]
    
    print("✅ User selected:")
    for selection in user_selections:
        print(f"   • {selection}")
    
    print("\n📊 STEP 2: System generates technical parameter names")
    
    # Simulate parameter name generation
    technical_names = {
        "Transfer Coefficient: Harvest → Processing": "TC_00_01",
        "DSM Process 6 - Short-lived - Mean Lifetime": "dsm_6_lifetimes_Mean_0"
    }
    
    print("🔧 System automatically generates:")
    for user_name, tech_name in technical_names.items():
        print(f"   • {user_name} → {tech_name}")
    
    print("\n📊 STEP 3: System creates uncertainty definitions")
    
    # Simulate uncertainty definition creation
    uncertainty_params = {
        'TC_00_01': {
            'distribution': 'normal',
            'mean': 0.8,
            'std': 0.08
        },
        'dsm_6_lifetimes_Mean_0': {
            'distribution': 'normal', 
            'mean': 10,
            'std': 1
        }
    }
    
    print("📋 Generated uncertainty parameters:")
    for param, config in uncertainty_params.items():
        print(f"   • {param}: {config['distribution']} distribution")
        print(f"     Mean: {config['mean']}, StdDev: {config['std']}")
    
    print("\n📊 STEP 4: System generates Excel for transparency")
    
    # Simulate Excel generation
    excel_data = [
        {
            'Parameter_Name': 'TC_00_01',
            'Distribution': 'normal',
            'Description': 'Transfer Coefficient: Harvest → Processing',
            'Mean': 0.8,
            'StdDev': 0.08
        },
        {
            'Parameter_Name': 'dsm_6_lifetimes_Mean_0',
            'Distribution': 'normal',
            'Description': 'DSM Process 6 - Short-lived - Mean Lifetime',
            'Mean': 10,
            'StdDev': 1
        }
    ]
    
    excel_df = pd.DataFrame(excel_data)
    print("💾 Generated Excel format:")
    print(excel_df.to_string(index=False))
    
    print("\n📊 STEP 5: Existing MC engine uses the parameters")
    
    # Simulate Monte Carlo execution
    print("🎲 Running Monte Carlo simulation...")
    print("   • Using generated uncertainty parameters")
    print("   • Existing MC engine unchanged")
    print("   • Results displayed in existing plots")
    
    return uncertainty_params, excel_df

def show_integration_options():
    """Show different integration options."""
    
    print("\n" + "=" * 60)
    print("🔧 INTEGRATION OPTIONS")
    print("=" * 60)
    
    print("\n📊 Option 1: Replace Excel Sheet")
    print("✅ Pros: No Excel needed, simpler workflow")
    print("❌ Cons: Less transparency, harder to debug")
    print("💡 Use when: Users prefer interface-only approach")
    
    print("\n📊 Option 2: Hybrid Approach") 
    print("✅ Pros: Both options available, backward compatible")
    print("❌ Cons: More complex, two workflows to maintain")
    print("💡 Use when: Gradual migration is preferred")
    
    print("\n📊 Option 3: Interface Generates Excel (RECOMMENDED)")
    print("✅ Pros: User-friendly + transparent + compatible")
    print("❌ Cons: Slightly more complex implementation")
    print("💡 Use when: Best of both worlds needed")
    
    print("\n🎯 RECOMMENDED APPROACH:")
    print("   Start with Option 3 (Interface Generates Excel)")
    print("   • Keep existing Excel workflow")
    print("   • Add interface as alternative")
    print("   • Interface generates Excel for transparency")
    print("   • Existing MC engine unchanged")

def show_workflow_comparison():
    """Show before/after workflow comparison."""
    
    print("\n" + "=" * 60)
    print("📊 WORKFLOW COMPARISON")
    print("=" * 60)
    
    print("\n❌ BEFORE (Excel-Only):")
    print("1. User opens Excel file")
    print("2. User types: dsm_6_lifetimes_Mean_0")
    print("3. User types: fomp_8_k1")
    print("4. User saves Excel file")
    print("5. System reads Excel and runs MC")
    print("6. Results displayed")
    
    print("\n✅ AFTER (Interface + Excel):")
    print("1. User opens parameter selector")
    print("2. User clicks: 'DSM Process 6 - Short-lived - Mean Lifetime'")
    print("3. User clicks: 'FOMP Process 8 - Fast pool decay rate'")
    print("4. System generates: dsm_6_lifetimes_Mean_0, fomp_8_k1")
    print("5. System creates Excel file automatically")
    print("6. System reads Excel and runs MC (same as before)")
    print("7. Results displayed")
    
    print("\n🎯 KEY DIFFERENCES:")
    print("   • User doesn't need to know parameter names")
    print("   • Visual selection instead of typing")
    print("   • Automatic Excel generation")
    print("   • Same MC engine and results")

def show_implementation_code():
    """Show example implementation code."""
    
    print("\n" + "=" * 60)
    print("💻 IMPLEMENTATION CODE")
    print("=" * 60)
    
    print("\n📊 Integration Function:")
    print("""
def run_monte_carlo_with_interface(mfa_system, dsm_params, fomp_params):
    \"\"\"Run Monte Carlo with interface-selected parameters.\"\"\"
    
    # Step 1: Get user selections via interface
    selector = MCParameterSelector(mfa_system, dsm_params, fomp_params)
    selected_params = selector.get_selected_parameters()
    
    # Step 2: Generate technical parameter names
    codelist = MCParameterCodelist(mfa_system, dsm_params, fomp_params)
    uncertainty_params = codelist.create_uncertainty_definitions(selected_params)
    
    # Step 3: Generate Excel for transparency
    excel_df = codelist.export_to_excel_format(selected_params)
    excel_df.to_excel('interface_generated_uncertainty.xlsx', index=False)
    
    # Step 4: Run Monte Carlo (existing code unchanged)
    mc_results = run_monte_carlo_simulation(mfa_system, uncertainty_params)
    
    return mc_results
    """)
    
    print("\n📊 Usage in Scientific Notebook:")
    print("""
# In the Monte Carlo section of the notebook
if has_mc:
    # Try interface first, fall back to Excel
    try:
        mc_results = run_monte_carlo_with_interface(
            mfa_system, dsm_params, fomp_params
        )
        print("✅ Used interface-selected parameters")
    except Exception as e:
        print(f"⚠️ Interface not available: {e}")
        # Fall back to existing Excel-based workflow
        mc_results = run_monte_carlo_from_excel(input_data)
        print("✅ Used Excel-based parameters")
    """)

if __name__ == "__main__":
    # Run the demonstration
    uncertainty_params, excel_df = demonstrate_mc_integration()
    show_integration_options()
    show_workflow_comparison()
    show_implementation_code()
    
    print("\n" + "=" * 60)
    print("🎯 SUMMARY")
    print("=" * 60)
    print("The new codelist system integrates seamlessly with existing MC workflow:")
    print("✅ User-friendly parameter selection")
    print("✅ Automatic technical name generation") 
    print("✅ Excel generation for transparency")
    print("✅ Existing MC engine unchanged")
    print("✅ Same results and visualizations") 