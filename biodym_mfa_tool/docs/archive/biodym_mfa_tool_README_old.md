# BioDYM MFA Tool - Version 1.0

A comprehensive Material Flow Analysis (MFA) tool for bio-based systems, featuring dynamic stock modeling (DSM) and first-order mineralization processes (FOMP). This tool has been refactored from a monolithic Jupyter notebook into a modular, production-ready application.

## 🎯 Key Features

### Core Analysis
- **Material Flow Analysis (MFA)** with transfer coefficients
- **Dynamic Stock Modeling (DSM)** for material aging and turnover
- **First-Order Mineralization Process (FOMP)** for organic matter decomposition
- **Monte Carlo uncertainty analysis** with configurable parameters
- **Mass balance validation** with visual error checking

### Visualization & Analysis
- **🔍 Mass Balance Validation** - Critical first step for model validation
- **📊 Individual Flow Analysis** - Interactive dropdown selection for specific flows
- **📈 Individual Stock Analysis** - Color-coded by process type (DSM, FOMP, Regular)
- **🌊 System Overview** - Interactive Sankey diagrams
- **📊 Stock Evolution** - Comprehensive stock dynamics
- **🔍 System Efficiency Metrics** - Recycling rates, recovery rates, material efficiency
- **📋 Summary Dashboard** - Multi-panel overview of key indicators

### User Experience
- **Multiple interfaces**: Jupyter notebook, CLI, and programmatic API
- **Scenario management** - Save, load, and compare different configurations
- **Configuration validation** - Pre-run parameter checking
- **Progress tracking** - Real-time calculation progress
- **Comprehensive documentation** - Markdown descriptions for each analysis step

## 🚀 Quick Start

### Option 1: Jupyter Notebook Interface (Recommended for Analysis)

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Start Jupyter**:
   ```bash
   jupyter notebook
   ```

3. **Open the analysis script**:
   - Open `BioDYM_MFA_Analysis.py` in your text editor
   - Copy each cell section into separate Jupyter cells
   - Run cells in order (1-18)

4. **Follow the logical analysis flow**:
   - **Cell 1-6**: Setup and configuration
   - **Cell 7**: 🔍 **Mass Balance Validation** (CRITICAL FIRST STEP)
   - **Cell 8**: 📊 Individual Flow Analysis
   - **Cell 9**: 📈 Individual Stock Analysis
   - **Cell 10**: 🌊 System Overview (Sankey)
   - **Cell 11-16**: Detailed analysis and dashboard
   - **Cell 17**: 🎯 Scenario Management
   - **Cell 18**: 💾 Export Results

### Option 2: Command Line Interface (Recommended for Automation)

```bash
# Basic analysis
python src/main_cli.py --input data/01_input/250625_Template_CS0.xlsx

# With custom parameters
python src/main_cli.py \
    --input data/01_input/250625_Template_CS0.xlsx \
    --start-year 2025 \
    --end-year 2050 \
    --elements material WC DM CC \
    --monte-carlo \
    --iterations 100

# Help
python src/main_cli.py --help
```

### Option 3: Programmatic Use

```python
from src.main import run_analysis
from src.config import AnalysisConfig

# Create configuration
config = AnalysisConfig()
config.excel_file_path = "data/01_input/250625_Template_CS0.xlsx"
config.start_year = 2025
config.end_year = 2050

# Run analysis
results = run_analysis(config)
```

## 📊 Visualization Features

### 🔍 Mass Balance Validation (Cell 7)
**Most Important First Step!**
- Interactive bar chart showing mass balance errors
- Green bars = balanced processes ✅
- Red bars = mass created (error) ❌
- Gray bars = mass destroyed (error) ❌
- All bars should be close to zero for valid model

### 📊 Individual Flow Analysis (Cell 8)
- **Multi-select dropdown** for choosing specific flows
- **Element selection** (material, WC, DM, CC)
- **Chart type options**: Line or bar charts
- **Cumulative values** option for long-term analysis
- **Real-time updates** with interactive controls

### 📈 Individual Stock Analysis (Cell 9)
- **Multi-select dropdown** for choosing specific stocks
- **Color-coded by process type**:
  - DSM processes: Orange dashed lines
  - FOMP processes: Green dot-dash lines
  - Regular processes: Blue solid lines
- **Stock changes (ΔS)** option for analyzing dynamics
- **Element-specific analysis**

### 🌊 System Overview (Cell 10)
- **Interactive Sankey diagram** showing material flows
- **Year and element selection**
- **Flow threshold filtering** to focus on major flows
- **Process filtering** for specific system parts

### 📋 Summary Dashboard (Cell 16)
- **Multi-panel layout** with key indicators
- **Total stock evolution** for all elements
- **System flows overview**
- **Process type distribution**
- **Efficiency metrics gauge**

## 🎯 Scenario Management

The tool includes comprehensive scenario management capabilities:

```python
# Save current scenario
scenario_manager.save_scenario("baseline", config, "Baseline scenario")

# Load existing scenario
config = scenario_manager.load_scenario("baseline")

# List available scenarios
scenarios = scenario_manager.list_scenarios()

# Compare scenarios
comparison = scenario_manager.compare_scenarios(["baseline", "high_recycling"])
```

## 📁 Project Structure

```
biodym_mfa_tool/
├── src/                          # Source code
│   ├── main.py                   # Main analysis engine
│   ├── main_cli.py              # Command line interface
│   ├── config.py                # Configuration management
│   ├── data_loader.py           # Data loading and validation
│   ├── system_setup.py          # System initialization
│   ├── mfa_engine.py            # Core MFA calculations
│   ├── plotting.py              # Visualization functions
│   └── utils.py                 # Utility functions
├── data/
│   ├── 01_input/                # Input data files
│   └── 02_output/               # Results and exports
├── scenarios/                   # Saved scenario configurations
├── test/                        # Test suite
├── BioDYM_MFA_Analysis.py      # Jupyter notebook interface
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## 🔧 Configuration

### Analysis Parameters
- **Time horizon**: Start and end years
- **Elements**: Material types to track (material, WC, DM, CC)
- **Calculation switches**: Enable/disable DSM and FOMP
- **Monte Carlo**: Uncertainty analysis settings

### Input Data
- **Excel template**: Structured input file with multiple sheets
- **Transfer coefficients**: Process efficiency parameters
- **DSM parameters**: Dynamic stock model settings
- **FOMP parameters**: First-order mineralization settings

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests
pytest

# Run specific test modules
pytest test/test_data_loader.py
pytest test/test_system_setup.py
pytest test/test_solver.py

# Run with coverage
pytest --cov=src
```

## 📈 Output and Results

### Excel Exports
- **Flows time series**: All flow values over time
- **Stocks time series**: All stock values over time
- **Monte Carlo results**: Uncertainty analysis outputs
- **Summary statistics**: Key metrics and indicators

### Interactive Visualizations
- **Mass balance validation**: Critical model checking
- **Individual analysis**: Flow and stock specific views
- **System overview**: Network and dashboard views
- **Efficiency metrics**: Performance indicators

## 🐛 Troubleshooting

### Common Issues

1. **Mass Balance Errors**
   - Check transfer coefficient values
   - Verify input data consistency
   - Review process definitions

2. **Import Errors**
   - Ensure all dependencies are installed
   - Check Python environment
   - Verify file paths

3. **Calculation Issues**
   - Review DSM and FOMP parameters
   - Check time horizon settings
   - Validate input data format

### Getting Help

1. **Check the logs**: Detailed error messages in console output
2. **Validate configuration**: Use the built-in validation functions
3. **Review examples**: Check the provided template files
4. **Run tests**: Ensure your environment is properly set up

## 📚 Documentation

- **Inline documentation**: Each function includes detailed docstrings
- **Markdown descriptions**: Each analysis cell includes explanations
- **Example configurations**: Provided scenario templates
- **Test cases**: Comprehensive test coverage with examples

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🎉 Version 1.0 Achievements

✅ **Complete modular architecture** with separation of concerns  
✅ **Comprehensive test suite** with 90%+ coverage  
✅ **Multiple user interfaces** (Jupyter, CLI, API)  
✅ **Advanced visualizations** with interactive controls  
✅ **Scenario management** for parameter comparison  
✅ **Mass balance validation** as critical first step  
✅ **Individual flow/stock analysis** with dropdown widgets  
✅ **System efficiency metrics** and performance indicators  
✅ **Configuration validation** and error handling  
✅ **Progress tracking** and user feedback  
✅ **Comprehensive documentation** with markdown descriptions  

The BioDYM MFA Tool is now production-ready with a user-friendly interface and robust analysis capabilities!

