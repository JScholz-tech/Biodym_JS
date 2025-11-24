"""
Dynamic TC Interpolation Preview Tool

Utility to visualize how dynamic TCs are interpolated before running the full analysis.
Useful for verifying that interpolation produces expected values.

Usage:
    python 02_src/utils_dynamic_tc_preview.py --input my_input_file.xlsx --tc TC_rec

Or import in Jupyter notebook:
    from utils_dynamic_tc_preview import preview_dynamic_tc
    preview_dynamic_tc("01_data/01_input/my_file.xlsx", "TC_rec")
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import argparse


def preview_dynamic_tc(
    excel_path, tc_name, element="E1", show_data_points=True, save_fig=None
):
    """
    Preview interpolated dynamic TC profile.

    Parameters
    ----------
    excel_path : str or Path
        Path to Excel input file
    tc_name : str
        TC parameter name (e.g., "TC_rec", "TC_1")
    element : str, optional
        Element to preview (E1, E2, E3, E4). Default is "E1".
    show_data_points : bool, optional
        If True, overlay original data points. Default is True.
    save_fig : str or Path, optional
        If provided, save figure to this path. Default is None (show only).

    Returns
    -------
    dict
        Dictionary with keys:
        - 'years': array of years
        - 'values': interpolated TC values
        - 'data_points': original data points (year, value pairs)
    """
    # Load Excel data
    config_df = pd.read_excel(excel_path, sheet_name="0_Configuration")
    dynamic_tc_df = pd.read_excel(excel_path, sheet_name="2_3_dynamic_TCs")

    # Extract time range from configuration
    t_start = int(config_df[config_df["Parameter"] == "t_start"]["Value"].values[0])
    t_end = int(config_df[config_df["Parameter"] == "t_end"]["Value"].values[0])
    time_vector = np.arange(t_start, t_end + 1)

    # Detect format (E# vs old format)
    if "E1_TC_ID" in dynamic_tc_df.columns:
        # New format
        element_num = int(element[1])  # Extract number from "E1" -> 1
        tc_id_col = f"E{element_num}_TC_ID"
        tc_value_col = f"E{element_num}_TC_Value[%]"
    else:
        # Old format
        element_name = {
            "E1": "material",
            "E2": "WC",
            "E3": "DM",
            "E4": "CC",
        }.get(element, "material")
        tc_id_col = f"TC_{element_name}_ID"
        tc_value_col = f"TC_Value_{element_name}"

    # Filter for specific TC
    tc_data = dynamic_tc_df[
        [tc_id_col, tc_value_col, "Year"]
    ].dropna()
    tc_data = tc_data[tc_data[tc_id_col] == tc_name]

    if tc_data.empty:
        raise ValueError(
            f"No data found for TC '{tc_name}' in element '{element}'. "
            f"Available TCs: {dynamic_tc_df[tc_id_col].dropna().unique()}"
        )

    # Extract data points
    data_years = tc_data["Year"].values
    data_values = tc_data[tc_value_col].values

    # Perform interpolation (same logic as data_loader.py)
    ts = pd.Series(data_values, index=data_years)
    ts_full = ts.reindex(time_vector)
    ts_interpolated = ts_full.interpolate(method="linear", limit_direction="both")

    # Handle edge cases
    if ts_interpolated.isna().any():
        ts_interpolated = ts_interpolated.ffill().bfill()

    # Create plot
    fig, ax = plt.subplots(figsize=(12, 6))

    # Plot interpolated line
    ax.plot(
        time_vector,
        ts_interpolated.values,
        "b-",
        linewidth=2,
        label="Interpolated",
    )

    # Plot original data points
    if show_data_points:
        ax.scatter(
            data_years,
            data_values,
            color="red",
            s=100,
            zorder=5,
            label="Data Points",
            edgecolors="black",
        )

    # Formatting
    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel("TC Value [%]", fontsize=12)
    ax.set_title(
        f"Dynamic TC Preview: {tc_name} ({element})",
        fontsize=14,
        fontweight="bold",
    )
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=11)

    # Add statistics as text
    stats_text = (
        f"Data points: {len(data_years)}\n"
        f"Range: {data_years.min():.0f} - {data_years.max():.0f}\n"
        f"Min TC: {ts_interpolated.min():.2f}%\n"
        f"Max TC: {ts_interpolated.max():.2f}%\n"
        f"Mean TC: {ts_interpolated.mean():.2f}%"
    )
    ax.text(
        0.02,
        0.98,
        stats_text,
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment="top",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
    )

    plt.tight_layout()

    if save_fig:
        plt.savefig(save_fig, dpi=300, bbox_inches="tight")
        print(f"Figure saved to: {save_fig}")

    plt.show()

    # Return data for further analysis
    return {
        "years": time_vector,
        "values": ts_interpolated.values,
        "data_points": list(zip(data_years, data_values)),
    }


def preview_all_dynamic_tcs(excel_path, element="E1", save_dir=None):
    """
    Preview all dynamic TCs in the Excel file for a specific element.

    Parameters
    ----------
    excel_path : str or Path
        Path to Excel input file
    element : str, optional
        Element to preview (E1, E2, E3, E4). Default is "E1".
    save_dir : str or Path, optional
        If provided, save figures to this directory. Default is None.

    Returns
    -------
    dict
        Dictionary mapping TC names to their interpolated data
    """
    # Load dynamic TC sheet
    dynamic_tc_df = pd.read_excel(excel_path, sheet_name="2_3_dynamic_TCs")

    # Detect format and get TC names
    if "E1_TC_ID" in dynamic_tc_df.columns:
        element_num = int(element[1])
        tc_id_col = f"E{element_num}_TC_ID"
    else:
        element_name = {
            "E1": "material",
            "E2": "WC",
            "E3": "DM",
            "E4": "CC",
        }.get(element, "material")
        tc_id_col = f"TC_{element_name}_ID"

    tc_names = dynamic_tc_df[tc_id_col].dropna().unique()

    if len(tc_names) == 0:
        print(f"No dynamic TCs found for element {element}")
        return {}

    print(f"Found {len(tc_names)} dynamic TCs for {element}: {list(tc_names)}")

    results = {}
    for tc_name in tc_names:
        print(f"\nProcessing {tc_name}...")

        save_path = None
        if save_dir:
            save_dir = Path(save_dir)
            save_dir.mkdir(parents=True, exist_ok=True)
            save_path = save_dir / f"dynamic_tc_{tc_name}_{element}.png"

        try:
            result = preview_dynamic_tc(
                excel_path, tc_name, element=element, save_fig=save_path
            )
            results[tc_name] = result
        except Exception as e:
            print(f"Error processing {tc_name}: {e}")

    return results


def main():
    """Command-line interface for the preview tool."""
    parser = argparse.ArgumentParser(
        description="Preview dynamic TC interpolation profiles"
    )
    parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Path to Excel input file",
    )
    parser.add_argument(
        "--tc",
        "-t",
        help="Specific TC name to preview (e.g., TC_rec). If not provided, previews all TCs.",
    )
    parser.add_argument(
        "--element",
        "-e",
        default="E1",
        choices=["E1", "E2", "E3", "E4"],
        help="Element to preview (default: E1)",
    )
    parser.add_argument(
        "--save",
        "-s",
        help="Save figure to this path (for single TC) or directory (for all TCs)",
    )

    args = parser.parse_args()

    if args.tc:
        # Preview single TC
        preview_dynamic_tc(
            args.input,
            args.tc,
            element=args.element,
            save_fig=args.save,
        )
    else:
        # Preview all TCs
        preview_all_dynamic_tcs(
            args.input,
            element=args.element,
            save_dir=args.save,
        )


if __name__ == "__main__":
    main()
