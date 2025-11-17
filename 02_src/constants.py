# -*- coding: utf-8 -*-
"""
BioDYM Constants and Standard Icons

This module defines standard icons and constants used throughout BioDYM
for consistent user feedback and visual communication.
"""


class Icons:
    """Standard emoji icons for consistent user feedback across BioDYM"""

    # Status Indicators
    SUCCESS = "✅"  # Success / Complete
    ERROR = "❌"  # Error / Failed
    WARNING = "⚠️"  # Warning
    INFO = "ℹ️"  # Information
    PROCESSING = "⚙️"  # Processing / Working

    # File Operations
    FILE = "📁"  # File operations
    FOLDER = "📂"  # Folder / Directory

    # Workflow Stages
    CALCULATION = "🧮"  # Calculation / Computation
    VISUALIZATION = "📊"  # Visualization / Chart
    EXPORT = "💾"  # Export / Save
    IMPORT = "📥"  # Import / Load

    # Analysis Types
    MFA = "🔄"  # Material Flow Analysis
    DSM = "🏗️"  # Dynamic Stock Model
    FOMP = "🌱"  # First-Order Mineralization Process
    MONTE_CARLO = "🎲"  # Monte Carlo Simulation
    SCENARIO = "🎭"  # Scenario Analysis

    # System Components
    CONFIGURATION = "⚙️"  # Configuration / Settings
    DATA_LOADING = "📥"  # Data Loading
    VALIDATION = "⚖️"  # Validation / Mass Balance
    SYSTEM = "🔧"  # System / Setup

    # Time & Elements
    TIME = "📅"  # Time / Date
    ELEMENT = "🧪"  # Element / Chemical

    # Visualizations
    SANKEY = "🌊"  # Flow / Sankey Diagram
    BAR_CHART = "📈"  # Bar Chart / Stock
    PROCESS = "🏭"  # Process / Factory

    # Actions
    CREATING = "🎯"  # Creating / Generating
    RUNNING = "🚀"  # Running / Execution
    LOADING = "📥"  # Loading
    SAVING = "💾"  # Saving
    ANALYZING = "🔍"  # Analyzing / Searching

    # Categories
    SECTION = "█"  # Section marker
    SUBSECTION = "─"  # Subsection marker
    ARROW = "→"  # Direction / Flow

    # Progress
    START = "▶️"  # Start / Play
    STOP = "⏹️"  # Stop
    TIMER = "⏱️"  # Timer / Duration


class StatusLevel:
    """Message status levels for logging"""

    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    DEBUG = "DEBUG"


class Colors:
    """ANSI color codes for terminal output (optional)"""

    RESET = "\033[0m"
    BOLD = "\033[1m"

    # Status colors
    SUCCESS = "\033[92m"  # Green
    WARNING = "\033[93m"  # Yellow
    ERROR = "\033[91m"  # Red
    INFO = "\033[94m"  # Blue

    # Text colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"


# Standard messages formats
def format_header(title: str, level: int = 1, char: str = "=") -> str:
    """Format a section header

    Args:
        title: Header text
        level: Header level (1-3)
        char: Character to use for separator

    Returns:
        Formatted header string
    """
    widths = {1: 70, 2: 60, 3: 50}
    width = widths.get(level, 70)
    return f"\n{char * width}\n{title}\n{char * width}\n"


def format_step(icon: str, step: str, message: str) -> str:
    """Format a workflow step message

    Args:
        icon: Icon to display
        step: Step identifier (e.g., "1.1", "2.3")
        message: Step description

    Returns:
        Formatted step string
    """
    return f"  {icon} [{step}] {message}"


def format_success(message: str) -> str:
    """Format a success message"""
    return f"{Icons.SUCCESS} {message}"


def format_error(message: str) -> str:
    """Format an error message"""
    return f"{Icons.ERROR} {message}"


def format_warning(message: str) -> str:
    """Format a warning message"""
    return f"{Icons.WARNING} {message}"


def format_info(message: str) -> str:
    """Format an info message"""
    return f"{Icons.INFO} {message}"


def format_file_path(path: str, action: str = "Loading") -> str:
    """Format a file path with highlighting

    Args:
        path: File path
        action: Action being performed on file

    Returns:
        Formatted file path string
    """
    return f"  {Icons.FILE} {action}: [{path}]"


# Icon usage reference
ICON_USAGE_REFERENCE = """
BioDYM Standard Icon Usage

Status Indicators:
  {SUCCESS}   - Success / Complete
  {ERROR}     - Error / Failed  
  {WARNING}   - Warning
  {INFO}      - Information
  {PROCESSING} - Processing / Working

Workflow Stages:
  {CALCULATION}    - Calculation / Computation
  {VISUALIZATION} - Visualization / Chart
  {EXPORT}        - Export / Save
  {IMPORT}        - Import / Load
  
Analysis Types:
  {DSM}         - Dynamic Stock Model
  {FOMP}        - First-Order Mineralization Process
  {MONTE_CARLO} - Monte Carlo Simulation
  {SCENARIO}    - Scenario Analysis

System Components:
  {CONFIGURATION} - Configuration / Settings
  {DATA_LOADING}  - Data Loading
  {VALIDATION}    - Validation / Mass Balance
  {SYSTEM}        - System / Setup
  
Time & Elements:
  {TIME}      - Time / Date
  {ELEMENT}   - Element / Chemical

Visualizations:
  {SANKEY}    - Flow / Sankey Diagram
  {BAR_CHART} - Bar Chart / Stock
  {PROCESS}   - Process / Factory

Actions:
  {CREATING} - Creating / Generating
  {RUNNING}  - Running / Execution
  {ANALYZING} - Analyzing / Searching

Categories:
  {ARROW} - Direction / Flow
""".format(**{k: v for k, v in Icons.__dict__.items() if not k.startswith("_")})
