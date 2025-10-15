# -*- coding: utf-8 -*-
"""
Publication Plotting Example for BioDYM

This example demonstrates how to use the new publication-quality plotting
standards in BioDYM. It shows the before/after comparison and various
export options.
"""

import sys
import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Add BioDYM modules to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, 'src'))

# Import BioDYM plotting modules
import plotting
from plotting.publication_style import (
    get_publication_layout,
    get_element_color,
    get_process_color,
    create_color_sequence,
    BIOYM_COLORS,
    ELEMENT_COLORS
)
from plotting.publication_export import (
    apply_publication_style,
    create_publication_export_widget,
    quick_export
)

def create_sample_data():
    """Create sample data for demonstration."""
    np.random.seed(42)
    
    # Sample time series data
    years = list(range(2020, 2031))
    elements = ['material', 'carbon', 'nitrogen']
    
    data = []
    for element in elements:
        for year in years:
            data.append({
                'Year': year,
                'Element': element,
                'Stock': np.random.uniform(100, 500),
                'Flow': np.random.uniform(50, 200)
            })
    
    return pd.DataFrame(data)

def create_old_style_plot(df):
    """Create a plot using old, inconsistent styling."""
    fig = go.Figure()
    
    colors = ['red', 'blue', 'green']  # Inconsistent colors
    elements = df['Element'].unique()
    
    for i, element in enumerate(elements):
        element_data = df[df['Element'] == element]
        fig.add_trace(go.Scatter(
            x=element_data['Year'],
            y=element_data['Stock'],
            mode='lines+markers',
            name=element,
            line=dict(color=colors[i], width=2),
            marker=dict(size=8)
        ))
    
    # Old styling
    fig.update_layout(
        title="Stock Levels Over Time",
        xaxis_title="Year",
        yaxis_title="Stock (t)",
        font=dict(size=10),  # Small font
        plot_bgcolor='white',
        width=800,
        height=500
    )
    
    return fig

def create_new_style_plot(df):
    """Create a plot using new publication standards."""
    fig = go.Figure()
    
    elements = df['Element'].unique()
    
    for element in elements:
        element_data = df[df['Element'] == element]
        fig.add_trace(go.Scatter(
            x=element_data['Year'],
            y=element_data['Stock'],
            mode='lines+markers',
            name=element.title(),
            line=dict(
                color=get_element_color(element),
                width=2
            ),
            marker=dict(
                size=8,
                color=get_element_color(element)
            )
        ))
    
    # Apply publication styling
    fig = apply_publication_style(
        fig, 
        title="Stock Levels Over Time",
        size='publication',
        show_grid=True
    )
    
    # Update axis labels
    fig.update_xaxes(title_text="Year")
    fig.update_yaxes(title_text="Stock (t)")
    
    return fig

def create_multi_element_comparison(df):
    """Create a multi-element comparison plot."""
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=['Material', 'Carbon', 'Nitrogen', 'Total'],
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    elements = df['Element'].unique()
    colors = create_color_sequence(len(elements), 'element')
    
    for i, element in enumerate(elements):
        element_data = df[df['Element'] == element]
        row = (i // 2) + 1
        col = (i % 2) + 1
        
        fig.add_trace(
            go.Scatter(
                x=element_data['Year'],
                y=element_data['Stock'],
                mode='lines+markers',
                name=element.title(),
                line=dict(color=colors[i], width=2),
                marker=dict(size=6)
            ),
            row=row, col=col
        )
    
    # Add total line to the last subplot
    total_data = df.groupby('Year')['Stock'].sum().reset_index()
    fig.add_trace(
        go.Scatter(
            x=total_data['Year'],
            y=total_data['Stock'],
            mode='lines+markers',
            name='Total',
            line=dict(color=BIOYM_COLORS['primary'], width=3),
            marker=dict(size=8)
        ),
        row=2, col=2
    )
    
    # Apply publication styling
    fig = apply_publication_style(
        fig,
        title="Multi-Element Stock Analysis",
        size='large',
        show_grid=True
    )
    
    # Update subplot titles
    fig.update_annotations(font_size=12)
    
    return fig

def demonstrate_export_options(fig, plot_name):
    """Demonstrate various export options."""
    print(f"\n{'='*60}")
    print(f"📊 EXPORT OPTIONS FOR {plot_name.upper()}")
    print(f"{'='*60}")
    
    # Quick export examples
    print("\n🚀 Quick Export Examples:")
    
    # PNG export
    png_path = quick_export(fig, plot_name, format='png')
    print(f"✅ PNG exported: {png_path}")
    
    # PDF export
    pdf_path = quick_export(fig, plot_name, format='pdf')
    print(f"✅ PDF exported: {pdf_path}")
    
    # SVG export
    svg_path = quick_export(fig, plot_name, format='svg')
    print(f"✅ SVG exported: {svg_path}")
    
    print(f"\n📋 Interactive Export Widget:")
    export_widget = create_publication_export_widget(fig, plot_name)
    return export_widget

def main():
    """Main demonstration function."""
    print("🎨 BioDYM Publication Plotting Standards Demo")
    print("="*60)
    
    # Create sample data
    df = create_sample_data()
    print(f"📊 Created sample data: {len(df)} records")
    
    # Demonstrate color palettes
    print(f"\n🎨 Color Palette Examples:")
    print(f"Primary Blue: {BIOYM_COLORS['primary']}")
    print(f"Element Colors: {ELEMENT_COLORS}")
    
    # Create old vs new style comparison
    print(f"\n📈 Creating Old vs New Style Comparison...")
    
    old_fig = create_old_style_plot(df)
    new_fig = create_new_style_plot(df)
    
    print("✅ Old style plot created")
    print("✅ New style plot created")
    
    # Create multi-element comparison
    print(f"\n📊 Creating Multi-Element Comparison...")
    multi_fig = create_multi_element_comparison(df)
    print("✅ Multi-element plot created")
    
    # Demonstrate export options
    print(f"\n📤 Demonstrating Export Options...")
    
    # Export old style plot
    old_export_widget = demonstrate_export_options(old_fig, "old_style")
    
    # Export new style plot
    new_export_widget = demonstrate_export_options(new_fig, "new_style")
    
    # Export multi-element plot
    multi_export_widget = demonstrate_export_options(multi_fig, "multi_element")
    
    print(f"\n🎉 Demonstration Complete!")
    print(f"📁 All exports saved to: exports/")
    print(f"📚 See docs/PLOTTING_STANDARDS.md for full guidelines")
    
    return {
        'old_fig': old_fig,
        'new_fig': new_fig,
        'multi_fig': multi_fig,
        'old_widget': old_export_widget,
        'new_widget': new_export_widget,
        'multi_widget': multi_export_widget
    }

if __name__ == "__main__":
    # Run the demonstration
    results = main()
    
    # Display the figures (if running in Jupyter)
    try:
        from IPython.display import display
        
        print("\n📊 Displaying Figures:")
        display(results['old_fig'])
        display(results['new_fig'])
        display(results['multi_fig'])
        
        print("\n📤 Export Widgets:")
        display(results['old_widget'])
        display(results['new_widget'])
        display(results['multi_widget'])
        
    except ImportError:
        print("\n💡 Run this script in Jupyter Notebook to see interactive figures")
        print("   Or check the exported files in the exports/ directory")
