# BioDYM Testing Guide

This guide will help you test BioDYM quickly and effectively.

## 🚀 Getting Started (5 minutes)

### Step 1: Install BioDYM

Choose **one** of these methods:

#### Option A: Anaconda (Recommended for most users)

```bash
# Create environment
conda env create -f environment.yml

# Activate environment
conda activate biodym_env
```

#### Option B: UV (Faster alternative)

```bash
# Install dependencies
uv sync
```

### Step 2: Open Jupyter Lab

```bash
# Anaconda users:
jupyter lab

# UV users:
uv run jupyter lab
```

### Step 3: Run the Main Workflow

1. Open `00_BioDYM_Workflow.ipynb` in Jupyter Lab
2. Go to the menu: **Kernel → Restart & Run All**
3. Wait for all cells to execute (takes 2-5 minutes)
4. Scroll through to see the results!

## ✅ What to Test

### 1. Core Functionality

- [ ] Workflow runs without errors from start to finish
- [ ] All visualizations display correctly (Sankey diagrams, time-series plots, etc.)
- [ ] Results are exported to `01_data/02_output/`
- [ ] Mass balance validation shows acceptable errors (< 1e-10)

### 2. Interactive Features

- [ ] **Sankey Diagram**: Try changing year, element, and min flow threshold
- [ ] **Process Dynamics**: Select different processes and elements
- [ ] **Flow Dynamics**: Select different flows and elements
- [ ] **Composition Plot**: Drag the year slider to see changes over time

### 3. Data Export

Check that these files are created in `01_data/02_output/`:
- [ ] `results_scientific_baseline.xlsx` - Main results
- [ ] `kpi_dashboard/system_kpis.xlsx` - KPI dashboard
- [ ] `composition_export/flow_composition.xlsx` - Composition data

### 4. Test Suite (Optional)

```bash
# Anaconda users:
pytest

# UV users:
uv run pytest
```

Expected: Most tests should pass (some tests may be skipped, that's OK)

## 🐛 Common Issues & Solutions

### Issue: "ModuleNotFoundError"

**Solution**: Make sure you activated the environment
```bash
conda activate biodym_env
```

### Issue: "Kernel not found"

**Solution**: Install ipykernel in the environment
```bash
conda activate biodym_env
conda install ipykernel
python -m ipykernel install --user --name biodym_env
```

Then restart Jupyter and select the "biodym_env" kernel.

### Issue: Plots not displaying

**Solution**: Make sure ipywidgets are enabled
```bash
conda activate biodym_env
jupyter labextension install @jupyter-widgets/jupyterlab-manager
```

### Issue: "Excel file not found"

**Solution**: Check the input file path in the notebook. The default path is:
```python
input_file = "01_data/01_input/251027_BioDYM_ODYM.xlsm"
```

Make sure this file exists, or change the path to an available Excel file.

## 📊 Example Files

The repository includes several example files you can test with:

1. **Current default**: `01_data/01_input/251027_BioDYM_ODYM.xlsm`
2. **Wheat straw case study**: `01_data/01_input/250922_CS1_Wheat_Straw.xlsx`
3. **Clean template**: `01_data/01_input/250625_Template_CS0.xlsx`

To test with a different file, change the `input_file` variable in cell 2 of the workflow notebook.

## 📝 What to Report

If you find issues, please report:

1. **What you were trying to do**: (e.g., "Running the main workflow")
2. **What happened**: (e.g., "Got an error in cell 5")
3. **Error message**: Copy the full error traceback
4. **Your setup**:
   - Operating system (Windows/Mac/Linux)
   - Installation method (Anaconda/UV)
   - Python version: `python --version`

## ⏱️ Expected Runtime

- **Full workflow**: 2-5 minutes
- **Test suite**: 30-60 seconds
- **Monte Carlo simulation** (if enabled): 5-15 minutes

## ✨ Everything Works?

If everything runs smoothly:
- The workflow completes without errors
- All visualizations display
- Results are exported
- Interactive controls work

**Congratulations!** BioDYM is working correctly. Feel free to explore:
- Try modifying the Excel input files
- Run scenario comparisons
- Enable Monte Carlo uncertainty analysis

## 🆘 Need More Help?

- Check the main **README.md** for detailed documentation
- Review **CLAUDE.md** for technical details and troubleshooting
- Open an issue on GitHub with your error details

---

**Last Updated**: 2025-11-06
**Version**: 1.0-beta
