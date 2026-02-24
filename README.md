# bioDYM - Biogenic Dynamic Material Systems Model

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-43%2F43%20passing-brightgreen)](04_tests/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

BioDYM is a comprehensive Material Flow Analysis (MFA) tool designed for analyzing bio-based material systems. Built on the [ODYM framework](https://github.com/IndEcol/ODYM), it tracks material flows, stocks, and transformations through time with special features for organic waste management and biomass cascading.

## ⚡ Quick Reference for Testers

**To get started in 5 minutes:**

1. **Install** (choose one):
   - UV: `uv sync` (fast, recommended)
   - Anaconda: `conda env create -f environment.yml && conda activate biodym_env`

2. **Open Jupyter**: `jupyter lab` (or `uv run jupyter lab` for UV users)

3. **Run the workflow**: Open `00_BioDYM_Workflow.ipynb`, add the filepath of the biodym Systemmanager Template and select "Kernel → Restart & Run All"

4. **Explore**: Interactive visualizations appear automatically - no coding required!

**Need help?** See [Getting Help](#-getting-help) section below.

## 🎯 Key Features

### Core Analysis Capabilities
- **Material Flow Analysis (MFA)** - Track materials through complex systems
- **Multi-Element Analysis** - Simultaneously track material, carbon, nitrogen, and other elements
- **Time-Series Analysis** - Dynamic modeling over multiple years with temporal resolution
- **Dynamic Stock Modeling (DSM)** - Model material aging and product lifetimes
- **First-Order Mineralization (FOMP)** - Simulate organic matter decomposition (e.g., carbon in soil)

### Process Logic & Configuration
- **Excel-based Configuration** - Pure data input via Excel files, no programming required
- **Interactive Jupyter Notebook** - Step-by-step analysis workflow with guided execution
- **Process Logic Types** - Splitter and Transformer processes for different material transformations
- **Stock-Outflow Transfer Coefficients** - Custom ODYM extension for stock-driven flows

### Analysis & Visualization
- **Interactive Visualizations** - Sankey diagrams, stock plots, and dashboards
- **Scenario Manager** - Compare multiple scenarios and analyze sensitivity
- **Monte Carlo Simulation** - Quantify uncertainty in results
- **Mass Balance Validation** - Automatic system consistency checks

### Quality Assurance
- **Comprehensive Test Suite** - Validated calculations with extensive testing
- **Structured Workflow** - Organized analysis pipeline from data loading to export

## 🚀 Quick Start

### 1. Install BioDYM

Choose either **UV** (recommended, faster) or **Anaconda** (more traditional):

#### Option A: UV Installation (Recommended)

```bash
# Clone the repository
git clone https://github.com/JScholz-tech/Biodym_JS.git
cd Biodym_JS

# Install uv if you don't have it
# On macOS/Linux: curl -LsSf https://astral.sh/uv/install.sh | sh
# On Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Create virtual environment and install dependencies
uv sync
```

#### Option B: Anaconda Installation

```bash
# Clone the repository
git clone https://github.com/JScholz-tech/Biodym_JS.git
cd Biodym_JS

# Create conda environment from environment.yml
conda env create -f environment.yml

# Activate the environment
conda activate biodym_env
```

### 2. Prepare Your Data

Copy the BioDYM Systemmanager template to use as your input data. The Excel file contains all system configuration, processes, flows, and parameters:

```bash
# Copy the template to your working location
cp 01_data/01_input/template/260217_bioDYM_Systemmanager_template_final.xlsm my_analysis.xlsm
```

> **Note**: `my_analysis.xlsm` is just a placeholder name — use any filename you prefer. A protected version of the template (`_protected.xlsm`) is also available if you want to prevent accidental formula edits.

### 3. Run Your Analysis

**🎯 Recommended: Use the Interactive Jupyter Notebook**

```bash
# UV users:
uv run jupyter lab

# Anaconda users:
jupyter lab

# Then open 00_BioDYM_Workflow.ipynb
# Update the input_file path in the notebook to point to your Excel file
```

**Alternative: Command Line Interface**

```bash
# UV users:
uv run python 02_src/main_cli.py --input my_analysis.xlsx

# Anaconda users:
python 02_src/main_cli.py --input my_analysis.xlsx
```

## 📖 Getting Started

### Understanding the Excel Input File

Your Excel file contains several sheets that define your material flow system:

- **`0_Configuration`** - Main settings (time range, elements, analysis options)
- **`1_1_Definition_Flows`** - Define all material flows in your system
- **`1_2_Data_Flows`** - Flow data over time
- **`2_1_Definition_Processes`** - Define processes and their logic types
- **`2_3_Process_TCs`** - Process transfer coefficients
- **`2_4_dynamic_tcs`** - Dynamic transfer coefficients over time
- **`2_5_Initial_Stock`** - Initial stock levels and stock-outflow TCs
- **`3_1_Definition_DSM`** - Dynamic Stock Model parameters
- **`3_2_Definition_FOMP`** - First-Order Mineralization Process parameters
- **`4_1_Uncertainty_Parameters`** - Monte Carlo uncertainty definitions
- **`5_1_Scenario_Manager`** - Scenario definitions for comparison
- **`6_1_Reference_Manager`** - Reference Manager and assumptions


### Running Your First Analysis

1. **Open the Notebook**: Start Jupyter Lab and open `00_BioDYM_Workflow.ipynb`
2. **Set Your Input File**: Update the `input_file` variable to point to your Excel file
3. **Run All Cells**: Execute the notebook cells in order (Kernel → Restart & Run All)
4. **Explore Results**: Interactive visualizations will appear automatically
5. **Export Data**: Results are saved to Excel files in `01_data/02_output/`

## 🔧 Project Structure

The BioDYM project follows a clean, organized structure:

### Core Application
- **`02_src/`** - Core application source code
  - `engine/` - MFA calculation engine, DSM, FOMP, Monte Carlo
  - `plotting/` - Visualization modules and interactive charts
  - `reporting/` - KPI dashboards and reports
- **`06_framework/`** - ODYM framework and BioDYM extensions
- **`04_tests/`** - Comprehensive test suite with unit and integration tests

### Data & Configuration
- **`01_data/`** - Input/output data and examples
  - `01_input/` - Example Excel files and templates
  - `02_output/` - Analysis results and exports
- **`01_data/02_output/scenarios/`** - Scenario comparison results (Excel, generated)
- **`03_studies/`** - Case studies and research examples

### Documentation & Notebooks
- **`05_docs/`** - Complete documentation and guides
- **`00_BioDYM_Workflow.ipynb`** - Main interactive analysis notebook
- **`environment.yml`** - Anaconda environment specification
- **`pyproject.toml`** - UV/pip dependencies and project metadata

## 📊 Example Studies

### Included Template

The repository includes the BioDYM Systemmanager template:

- **`01_data/01_input/template/260217_bioDYM_Systemmanager_template_final.xlsm`** — Blank template for setting up a new analysis
- **`01_data/01_input/template/260217_bioDYM_Systemmanager_template_final_protected.xlsm`** — Protected version (prevents accidental formula edits)

### Published Case Study

- **Wheat Straw Cascading (DGAW 2026)** — `03_studies/26_Weizenstroh_DGAW/` — Complete wheat straw system with Monte Carlo analysis. See the study [README](03_studies/26_Weizenstroh_DGAW/README.md) and [CITATION.bib](03_studies/26_Weizenstroh_DGAW/CITATION.bib).

### Generated Outputs

After running the workflow, results are written to `01_data/02_output/`:

| Folder | Content |
|--------|---------|
| `results/` | Baseline MFA results (Excel) |
| `composition/` | Flow composition data (Excel) |
| `kpi/` | System KPI dashboard (Excel) |
| `mc/` | Monte Carlo uncertainty results (Excel) |
| `figures/` | All exported publication figures (PNG/SVG) |
| `scenarios/` | Scenario comparison results (Excel) |

## 💡 Common Use Cases

- **Waste Management** - Track organic waste through treatment systems
- **Circular Economy** - Analyze material recycling and cascading use
- **Carbon Accounting** - Follow carbon through biogenic systems
- **Resource Planning** - Optimize biomass utilization pathways

## 🛠️ System Requirements

- Python 3.12 or higher
- 4GB RAM minimum (8GB recommended for Monte Carlo)
- Windows, macOS, or Linux

## 📦 Dependency Management

### UV Users

- Install and sync dependencies (creates `.venv` if missing):
  ```bash
  uv sync
  ```

- Add a runtime dependency:
  ```bash
  uv add <package>
  ```

- Add a dev-only dependency (testing, linting, etc.):
  ```bash
  uv add --dev <package>
  ```

- Run commands in the project environment:
  ```bash
  uv run pytest
  uv run jupyter lab
  uv run python 02_src/main_cli.py --help
  ```

### Anaconda Users

- Update environment from environment.yml:
  ```bash
  conda env update -f environment.yml --prune
  ```

- Install additional packages:
  ```bash
  conda activate biodym_env
  conda install <package>
  ```

- Run commands (after activating environment):
  ```bash
  pytest
  jupyter lab
  python 02_src/main_cli.py --help
  ```

## 📈 Workflow Overview

```mermaid
graph LR
    A[Excel Data] --> B[BioDYM Tool]
    B --> C{Analysis Type}
    C --> D[Mass Balance Check]
    C --> E[Flow Analysis] 
    C --> F[Stock Dynamics]
    C --> G[System Efficiency]
    D --> H[Results & Visualizations]
    E --> H
    F --> H
    G --> H
    H --> I[Excel Export]
```

## 🧪 Testing

BioDYM includes a comprehensive test suite to ensure code quality and reliability:

```bash
# UV users:
uv run pytest

# Anaconda users:
pytest

# Run with verbose output:
pytest -v

# Run specific test file:
pytest 04_tests/test_solver.py
```

**Master Integration Test**: The main workflow notebook `00_BioDYM_Workflow.ipynb` serves as the comprehensive integration test. It should run successfully from start to finish after any code changes (Kernel → Restart & Run All).

## 📑 Cite This Software

If you use BioDYM in your research, please cite:

> Scholz, J. (2026). *BioDYM: Material Flow Analysis for Bio-based Systems* (v1.0.0).
> Zenodo. https://doi.org/10.5281/zenodo.18759081

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18759081.svg)](https://doi.org/10.5281/zenodo.18759081)

A machine-readable citation is available in [CITATION.cff](CITATION.cff).

## 🤝 Contributing

We welcome contributions! Please see our [GitHub Issues](https://github.com/JScholz-tech/Biodym_JS/issues) for bug reports and feature requests.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [ODYM Framework](https://github.com/IndEcol/ODYM) - The foundation for MFA calculations
- TU Berlin - Chair of Circular Economy and Recycling Technology
- All contributors and users who have helped improve BioDYM

## 📬 Getting Help

- **Issues**: Report bugs or request features on [GitHub Issues](https://github.com/JScholz-tech/Biodym_JS/issues)
- **Discussions**: Join our [GitHub Discussions](https://github.com/JScholz-tech/Biodym_JS/discussions)
- **Examples**: Start with the template in `01_data/01_input/template/`

---

*Last updated: February 2026 | Version: 1.0.0*

## BioDYM Extension: Stock-Outflow Transfer Coefficients (TCs)

**Note:** This feature is a custom extension to the ODYM framework, developed specifically for BioDYM. It is **not** part of the standard ODYM release.

### What is it?

This extension allows you to define transfer coefficients (TCs) that control outflows directly from initial stocks of any process. It enables modeling of processes where material is gradually consumed from an initial stock, independent of regular inflows/outflows.

### Why was it added?

Standard ODYM does not provide a built-in mechanism for stock-driven outflows using user-defined TCs. Many real-world systems (e.g., landfills, storage, legacy stocks) require this feature for accurate modeling.

### How does it work?

- You can specify stock-outflow TCs directly in the `2_4_Initial_Stock` sheet of your input Excel file.
- For each process, you can define:
  - `Stock_Outflow_TC`: A unique ID for the stock-outflow TC
  - `Destination_Process`: The process that receives the outflow
  - `Annual_Consumption_Rate`: The fraction of the initial stock consumed per year (e.g., 0.1 for 10%/year)
- The BioDYM engine will automatically create flows that consume the initial stock at the specified rate and send it to the destination process.

### Example

| Process_ID | Initial_Stock_material | ... | Stock_Outflow_TC | Destination_Process | Annual_Consumption_Rate |
|------------|-----------------------|-----|------------------|--------------------|------------------------|
| 9          | 10000.0               | ... | STC_09_07        | 7                  | 0.1                    |

This will consume 10% of the initial stock of process 9 (Animal bedding) per year and send it to process 7 (Incineration).

### Code Location

- The main logic is implemented in `02_src/engine/solver.py` and `02_src/engine/initial_stock_engine.py`.
- This function and related logic are clearly marked as BioDYM extensions in the code and documentation.

### Disclaimer

This feature is not part of the official ODYM framework and may not be compatible with future ODYM updates. It is maintained as part of the BioDYM project.
