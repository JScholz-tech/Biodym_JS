# -*- coding: utf-8 -*-
"""
Publication-Quality Figure Export for BioDYM

This module provides a unified, robust export system for creating publication-ready
figures from BioDYM visualizations. It handles:
- High-resolution export (300-400 DPI)
- Multiple formats (PNG, PDF, SVG, EPS)
- Proper figure sizing for print
- Automatic directory creation
- Timestamp management
- Export logging

Author: BioDYM Development Team
Date: 2025-11-04
"""

import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path
from typing import Optional, Union, List, Tuple
import warnings


# =============================================================================
# EXPORT SETTINGS
# =============================================================================

# Standard DPI settings
DPI_SETTINGS = {
    "screen": 96,  # Screen display
    "web": 150,  # Web/presentations
    "print": 300,  # Print quality
    "publication": 400,  # High-quality publication
}

# Figure size presets (width, height in inches for print)
PRINT_SIZES = {
    "single_column": (3.5, 2.625),  # Single column in 2-column layout
    "double_column": (7.0, 5.25),  # Full width in 2-column layout
    "large": None,  # Uses figure's current layout size (1200×900 px from FIGURE_SIZES["large"])
    "full_page": (7.5, 10),  # Full page
    "slide": (10, 7.5),  # Presentation slide
    "poster": (36, 48),  # Poster
    "custom": None,  # User-defined
}

# Default export directory
DEFAULT_EXPORT_DIR = "01_data/02_output/figures"


# =============================================================================
# MAIN EXPORT FUNCTION
# =============================================================================


def export_figure(
    fig: go.Figure,
    filename: str,
    formats: Optional[Union[str, List[str]]] = "png",
    quality: str = "publication",
    size: Optional[Union[str, Tuple[float, float]]] = None,
    dpi: Optional[int] = None,
    output_dir: Optional[str] = None,
    timestamp: bool = False,
    overwrite: bool = True,
    verbose: bool = True,
) -> List[str]:
    """
    Export a Plotly figure to publication-quality file(s).

    This is THE function to use for exporting BioDYM visualizations. It handles
    all the complexity of creating publication-ready figures with proper
    resolution, sizing, and format conversion.

    Parameters
    ----------
    fig : go.Figure
        Plotly figure object to export
    filename : str
        Base filename (without extension). Example: 'sankey_baseline'
    formats : str or List[str], optional
        Export format(s): 'png', 'pdf', 'svg', 'eps', 'html', or 'all'
        Can be a single string or list of strings
        Defaults to 'png'
    quality : str, optional
        Quality preset: 'screen' (96 DPI), 'web' (150 DPI),
        'print' (300 DPI), 'publication' (400 DPI)
        Defaults to 'publication'
    size : str or Tuple[float, float], optional
        Figure size. Can be:
        - Preset name: 'single_column', 'double_column', 'full_page', 'slide'
        - Tuple of (width, height) in inches: (7.0, 5.0)
        - None: Use figure's current size
        Defaults to None
    dpi : int, optional
        Custom DPI override. If provided, overrides quality setting
        Defaults to None
    output_dir : str, optional
        Output directory path. If None, uses DEFAULT_EXPORT_DIR
        Defaults to None
    timestamp : bool, optional
        If True, adds timestamp to filename (YYYYMMDD_HHMMSS)
        Defaults to False
    overwrite : bool, optional
        If True, overwrites existing files. If False, adds number suffix
        Defaults to False
    verbose : bool, optional
        If True, prints export status messages
        Defaults to True

    Returns
    -------
    List[str]
        List of full paths to exported files

    Examples
    --------
    >>> # Simple PNG export at publication quality (400 DPI)
    >>> export_figure(fig, 'my_sankey')

    >>> # Multiple formats at print quality
    >>> export_figure(fig, 'results', formats=['png', 'pdf', 'svg'],
    ...               quality='print')

    >>> # Custom size and DPI
    >>> export_figure(fig, 'figure1', size=(8, 6), dpi=300,
    ...               timestamp=False)

    >>> # Single column publication figure
    >>> export_figure(fig, 'fig_methods', size='single_column',
    ...               formats=['pdf', 'png'], quality='publication')

    Notes
    -----
    - PNG, PDF, SVG exports require kaleido package (installed with BioDYM)
    - EPS export converts from PDF (requires kaleido)
    - HTML exports preserve interactivity
    - Timestamp format: YYYYMMDD_HHMMSS
    - Directory is created automatically if it doesn't exist
    """

    # Validate and normalize formats
    if formats == "all":
        formats_list = ["png", "pdf", "svg", "html"]
    elif isinstance(formats, str):
        formats_list = [formats]
    else:
        formats_list = formats

    # Validate formats
    valid_formats = ["png", "pdf", "svg", "eps", "html", "json"]
    for fmt in formats_list:
        if fmt not in valid_formats:
            raise ValueError(f"Invalid format '{fmt}'. Valid: {valid_formats}")

    # Determine DPI
    if dpi is None:
        dpi = DPI_SETTINGS.get(quality, DPI_SETTINGS["publication"])

    # Calculate scale factor for Plotly (Plotly uses 96 DPI as base)
    scale_factor = dpi / 96.0

    # Determine output directory
    if output_dir is None:
        output_dir = DEFAULT_EXPORT_DIR

    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Build filename with optional timestamp
    base_filename = filename
    if timestamp:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"{filename}_{ts}"

    # Handle figure sizing
    if size is not None:
        if isinstance(size, str):
            # Preset size
            if size in PRINT_SIZES:
                size_inches = PRINT_SIZES[size]
                if size_inches:
                    width_px = int(size_inches[0] * dpi)
                    height_px = int(size_inches[1] * dpi)
                    fig.update_layout(width=width_px, height=height_px)
            else:
                warnings.warn(f"Unknown size preset '{size}'. Using current size.")
        elif isinstance(size, (tuple, list)) and len(size) == 2:
            # Custom size in inches
            width_px = int(size[0] * dpi)
            height_px = int(size[1] * dpi)
            fig.update_layout(width=width_px, height=height_px)

    # Export to each format
    exported_files = []

    for fmt in formats_list:
        # Build full filename
        full_filename = f"{base_filename}.{fmt}"
        full_path = output_path / full_filename

        # Handle file exists
        if not overwrite and full_path.exists():
            counter = 1
            while full_path.exists():
                full_filename = f"{base_filename}_{counter}.{fmt}"
                full_path = output_path / full_filename
                counter += 1

        # Export based on format
        try:
            if fmt == "html":
                # HTML preserves interactivity
                fig.write_html(str(full_path), include_plotlyjs="cdn")

            elif fmt == "json":
                # JSON for programmatic access
                fig.write_json(str(full_path))

            elif fmt == "eps":
                # EPS: First export to PDF, then convert (kaleido limitation)
                temp_pdf = output_path / f"{base_filename}_temp.pdf"
                fig.write_image(str(temp_pdf), scale=scale_factor)

                # Convert PDF to EPS (requires ghostscript or similar)
                try:
                    import subprocess

                    subprocess.run(
                        ["pdftops", "-eps", str(temp_pdf), str(full_path)],
                        check=True,
                        capture_output=True,
                    )
                    temp_pdf.unlink()  # Remove temporary PDF
                except (subprocess.CalledProcessError, FileNotFoundError):
                    warnings.warn(
                        "EPS conversion failed. Install ghostscript/poppler-utils. "
                        "Keeping PDF instead."
                    )
                    temp_pdf.rename(full_path.with_suffix(".pdf"))
                    fmt = "pdf"  # Update format for message

            else:
                # PNG, PDF, SVG (via kaleido)
                fig.write_image(str(full_path), format=fmt, scale=scale_factor)

            exported_files.append(str(full_path))

            if verbose:
                file_size = full_path.stat().st_size / 1024  # KB
                print(
                    f"✅ Exported {fmt.upper()}: {full_path} ({file_size:.1f} KB, {dpi} DPI)"
                )

        except Exception as e:
            if verbose:
                print(f"❌ Failed to export {fmt.upper()}: {e}")
            warnings.warn(f"Export to {fmt} failed: {e}")

    return exported_files


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def quick_export_png(fig: go.Figure, filename: str, **kwargs) -> str:
    """
    Quick PNG export with publication quality.

    Convenience wrapper for the most common use case.

    Parameters
    ----------
    fig : go.Figure
        Plotly figure
    filename : str
        Base filename
    **kwargs
        Additional arguments passed to export_figure()

    Returns
    -------
    str
        Path to exported file
    """
    files = export_figure(fig, filename, formats="png", quality="publication", **kwargs)
    return files[0] if files else None


def export_for_paper(
    fig: go.Figure, filename: str, size: str = "double_column"
) -> List[str]:
    """
    Export figure optimized for scientific paper.

    Exports to both PNG (for Word/Google Docs) and PDF (for LaTeX).
    Uses 400 DPI publication quality and standard column widths.

    Parameters
    ----------
    fig : go.Figure
        Plotly figure
    filename : str
        Base filename
    size : str, optional
        Size preset ('single_column' or 'double_column')
        Defaults to 'double_column'

    Returns
    -------
    List[str]
        Paths to exported files (PNG and PDF)
    """
    return export_figure(
        fig,
        filename,
        formats=["png", "pdf"],
        quality="publication",
        size=size,
        timestamp=False,
        verbose=True,
    )


def export_for_presentation(fig: go.Figure, filename: str) -> List[str]:
    """
    Export figure optimized for presentations.

    Exports to PNG at screen quality (smaller file size) and HTML
    (for interactive presentations).

    Parameters
    ----------
    fig : go.Figure
        Plotly figure
    filename : str
        Base filename

    Returns
    -------
    List[str]
        Paths to exported files (PNG and HTML)
    """
    return export_figure(
        fig,
        filename,
        formats=["png", "html"],
        quality="web",
        size="slide",
        timestamp=False,
        verbose=True,
    )


def batch_export_figures(figures: dict, quality: str = "publication", **kwargs) -> dict:
    """
    Export multiple figures with consistent settings.

    Parameters
    ----------
    figures : dict
        Dictionary mapping filenames to figure objects
        Example: {'sankey_baseline': fig1, 'dynamics_material': fig2}
    quality : str, optional
        Quality preset for all figures
        Defaults to 'publication'
    **kwargs
        Additional arguments passed to export_figure()

    Returns
    -------
    dict
        Dictionary mapping filenames to lists of exported file paths

    Examples
    --------
    >>> figures = {
    ...     'fig1_sankey': sankey_fig,
    ...     'fig2_dynamics': dynamics_fig,
    ...     'fig3_validation': validation_fig
    ... }
    >>> paths = batch_export_figures(figures, formats=['png', 'pdf'])
    """
    exported = {}

    for name, fig in figures.items():
        try:
            paths = export_figure(fig, name, quality=quality, **kwargs)
            exported[name] = paths
        except Exception as e:
            print(f"❌ Failed to export {name}: {e}")
            exported[name] = []

    return exported


# =============================================================================
# EXPORT REPORT
# =============================================================================


def generate_export_report(output_dir: Optional[str] = None) -> str:
    """
    Generate a report of all exported figures in the output directory.

    Parameters
    ----------
    output_dir : str, optional
        Directory to scan. If None, uses DEFAULT_EXPORT_DIR
        Defaults to None

    Returns
    -------
    str
        Formatted report string

    Examples
    --------
    >>> report = generate_export_report()
    >>> print(report)
    """
    if output_dir is None:
        output_dir = DEFAULT_EXPORT_DIR

    output_path = Path(output_dir)

    if not output_path.exists():
        return f"Export directory does not exist: {output_dir}"

    # Group files by format
    files_by_format = {}

    for file_path in output_path.glob("*"):
        if file_path.is_file():
            ext = file_path.suffix[1:]  # Remove leading dot
            if ext not in files_by_format:
                files_by_format[ext] = []
            files_by_format[ext].append(file_path)

    # Generate report
    report_lines = [
        "=" * 80,
        "BIODYM EXPORTED FIGURES REPORT",
        "=" * 80,
        f"Directory: {output_path.absolute()}",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
    ]

    total_files = 0
    total_size = 0

    for fmt in sorted(files_by_format.keys()):
        files = files_by_format[fmt]
        format_size = sum(f.stat().st_size for f in files)

        report_lines.append(f"\n{fmt.upper()} files: {len(files)}")
        report_lines.append("-" * 40)

        for file_path in sorted(files):
            size_kb = file_path.stat().st_size / 1024
            mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            report_lines.append(
                f"  {file_path.name:50s} {size_kb:8.1f} KB  {mod_time:%Y-%m-%d %H:%M}"
            )

        total_files += len(files)
        total_size += format_size

    report_lines.extend(
        [
            "",
            "=" * 80,
            f"TOTAL: {total_files} files, {total_size / (1024 * 1024):.2f} MB",
            "=" * 80,
        ]
    )

    return "\n".join(report_lines)


# =============================================================================
# INITIALIZATION
# =============================================================================


def set_default_export_directory(path: str):
    """
    Set the default export directory for all future exports.

    Parameters
    ----------
    path : str
        Path to export directory
    """
    global DEFAULT_EXPORT_DIR
    DEFAULT_EXPORT_DIR = path


def get_default_export_directory() -> str:
    """
    Get the current default export directory.

    Returns
    -------
    str
        Path to default export directory
    """
    return DEFAULT_EXPORT_DIR
