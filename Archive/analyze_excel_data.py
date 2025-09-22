#!/usr/bin/env python3
"""
Analyze Excel data structure against Plotly Sankey requirements.
"""

import pandas as pd
import numpy as np

def analyze_excel_data():
    """Analyze Excel data structure and compare with Plotly requirements."""
    
    print("🔍 EXCEL DATA ANALYSIS - Plotly Sankey Requirements")
    print("=" * 60)
    
    # Load Excel data
    try:
        df = pd.read_excel('data/01_input/250910_CS1_Wheat_Straw_v3.xlsx', 
                          sheet_name='6_1_Visualization_Processes')
        print(f"✅ Successfully loaded Excel data")
        print(f"📊 Total rows: {len(df)}")
        print(f"📋 Columns: {list(df.columns)}")
        
    except Exception as e:
        print(f"❌ Error loading Excel: {e}")
        return
    
    print("\n" + "="*60)
    print("📋 PLOTLY SANKEY REQUIREMENTS vs EXCEL DATA")
    print("="*60)
    
    # Plotly Sankey Requirements
    plotly_requirements = {
        'node': {
            'label': 'List of node names (required)',
            'x': 'X coordinates 0-1 (optional)',
            'y': 'Y coordinates 0-1 (optional)', 
            'color': 'Node colors (optional)',
            'pad': 'Vertical spacing (optional)',
            'thickness': 'Node width (optional)',
            'line': 'Border styling (optional)',
            'align': 'Node alignment (optional)'
        },
        'link': {
            'source': 'Source node indices (required)',
            'target': 'Target node indices (required)',
            'value': 'Flow values (required)',
            'color': 'Link colors (optional)',
            'label': 'Link labels (optional)',
            'arrowlen': 'Arrow length (optional)'
        },
        'layout': {
            'arrangement': 'snap, perpendicular, freeform, fixed',
            'width': 'Figure width in pixels',
            'height': 'Figure height in pixels'
        }
    }
    
    # Analyze what we have in Excel
    excel_columns = df.columns.tolist()
    
    print("\n🎯 NODE REQUIREMENTS ANALYSIS:")
    print("-" * 40)
    
    # Node labels
    if 'Name(EN)' in excel_columns:
        valid_names = df['Name(EN)'].dropna()
        print(f"✅ Node Labels: {len(valid_names)} valid names found")
        print(f"   Sample: {valid_names.head(3).tolist()}")
    else:
        print("❌ Node Labels: Missing 'Name(EN)' column")
    
    # Node positions
    position_columns = [col for col in excel_columns if 'Position' in col]
    print(f"\n📍 Node Positions: {len(position_columns)} position columns found")
    for col in position_columns:
        print(f"   - {col}")
    
    # Check position data quality
    if 'X_Position_Material' in excel_columns and 'Y_Position_Material' in excel_columns:
        x_pos = df['X_Position_Material'].dropna()
        y_pos = df['Y_Position_Material'].dropna()
        print(f"   📊 Material positions: {len(x_pos)} valid X, {len(y_pos)} valid Y")
        print(f"   📈 X range: {x_pos.min():.3f} - {x_pos.max():.3f}")
        print(f"   📈 Y range: {y_pos.min():.3f} - {y_pos.max():.3f}")
        
        # Check if positions are in 0-1 range (Plotly requirement)
        x_in_range = ((x_pos >= 0) & (x_pos <= 1)).all()
        y_in_range = ((y_pos >= 0) & (y_pos <= 1)).all()
        print(f"   ✅ X positions in 0-1 range: {x_in_range}")
        print(f"   ✅ Y positions in 0-1 range: {y_in_range}")
    
    # Node colors
    color_columns = [col for col in excel_columns if 'Color' in col]
    print(f"\n🎨 Node Colors: {len(color_columns)} color columns found")
    for col in color_columns:
        print(f"   - {col}")
    
    # Check color data quality
    if 'Node_Color_#' in excel_columns:
        colors = df['Node_Color_#'].dropna()
        print(f"   📊 Color data: {len(colors)} valid colors")
        print(f"   📈 Sample colors: {colors.head(3).tolist()}")
    
    print("\n🔗 LINK REQUIREMENTS ANALYSIS:")
    print("-" * 40)
    print("❌ Link data: Not found in this sheet (should be in flows sheet)")
    print("   Note: Links are typically defined by flow data, not process data")
    
    print("\n⚙️ LAYOUT REQUIREMENTS ANALYSIS:")
    print("-" * 40)
    
    # Check for layout configuration
    layout_columns = [col for col in excel_columns if any(x in col.lower() for x in ['layout', 'arrangement', 'align', 'pad', 'thickness'])]
    if layout_columns:
        print(f"✅ Layout settings: {len(layout_columns)} found")
        for col in layout_columns:
            print(f"   - {col}")
    else:
        print("❌ Layout settings: No layout columns found in process sheet")
    
    print("\n" + "="*60)
    print("📊 DATA QUALITY ANALYSIS")
    print("="*60)
    
    # Check for missing data
    print("\n🔍 Missing Data Analysis:")
    for col in excel_columns:
        null_count = df[col].isnull().sum()
        if null_count > 0:
            print(f"   ⚠️ {col}: {null_count}/{len(df)} missing values")
    
    # Check for duplicate process IDs
    if 'Process_ID' in excel_columns:
        process_ids = df['Process_ID'].dropna()
        duplicates = process_ids.duplicated().sum()
        if duplicates > 0:
            print(f"   ⚠️ Process_ID: {duplicates} duplicate IDs found")
        else:
            print(f"   ✅ Process_ID: No duplicates found")
    
    print("\n" + "="*60)
    print("🎯 USEFUL vs USELESS SETTINGS")
    print("="*60)
    
    # Categorize settings
    useful_settings = []
    useless_settings = []
    missing_settings = []
    
    # Node settings
    if 'Name(EN)' in excel_columns:
        useful_settings.append("Node Labels (Name(EN))")
    else:
        missing_settings.append("Node Labels")
    
    if any('Position' in col for col in excel_columns):
        useful_settings.append("Node Positions (X_Position_*, Y_Position_*)")
    else:
        missing_settings.append("Node Positions")
    
    if any('Color' in col for col in excel_columns):
        useful_settings.append("Node Colors (Node_Color_*)")
    else:
        missing_settings.append("Node Colors")
    
    # Check for useless settings
    useless_columns = []
    for col in excel_columns:
        if col in ['Process_ID']:  # Process_ID is useful for identification
            continue
        elif 'Position' in col or 'Color' in col or 'Name' in col:
            continue
        else:
            useless_columns.append(col)
    
    if useless_columns:
        useless_settings.extend(useless_columns)
    
    print("\n✅ USEFUL SETTINGS:")
    for setting in useful_settings:
        print(f"   - {setting}")
    
    print("\n❌ USELESS SETTINGS:")
    for setting in useless_settings:
        print(f"   - {setting}")
    
    print("\n⚠️ MISSING SETTINGS:")
    for setting in missing_settings:
        print(f"   - {setting}")
    
    print("\n" + "="*60)
    print("🔧 RECOMMENDATIONS")
    print("="*60)
    
    print("\n1. POSITION DATA:")
    print("   - Ensure all positions are in 0-1 range")
    print("   - Clean up NaN values in position columns")
    print("   - Validate element-specific positions are different")
    
    print("\n2. COLOR DATA:")
    print("   - Use hex codes (#RRGGBB) for colors")
    print("   - Ensure all processes have color definitions")
    
    print("\n3. LAYOUT SETTINGS:")
    print("   - Move layout settings to separate sheet")
    print("   - Add arrangement, alignment, padding settings")
    print("   - Add window sizing settings")
    
    print("\n4. DATA CLEANUP:")
    print("   - Remove rows with NaN Process_ID")
    print("   - Standardize column names")
    print("   - Add validation for required fields")

if __name__ == "__main__":
    analyze_excel_data()
