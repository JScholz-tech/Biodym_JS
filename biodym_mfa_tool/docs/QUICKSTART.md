# BioDYM Quick Start Tutorial

This tutorial will walk you through your first BioDYM analysis using a simple biomass flow example. No programming experience required!

## What You'll Learn

- How to prepare data in Excel
- How to run an MFA analysis
- How to interpret the results
- How to export findings

## The Example System

We'll analyze a simple biomass processing system with four components:

```
Environment → Processing → Food
                    ↓
                Biowaste → Environment
```

This represents biomass being harvested, processed into food, with some waste that returns to the environment.

## Step 1: Install BioDYM

### Option A: Using Anaconda (Recommended)

1. Download and install [Anaconda](https://www.anaconda.com/download)
2. Open Anaconda Prompt (Windows) or Terminal (Mac/Linux)
3. Navigate to the BioDYM folder:
   ```bash
   cd path/to/Biodym_JS
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Option B: Using Python

If you already have Python 3.8+ installed:
```bash
pip install -r requirements.txt
```

## Step 2: Prepare Your Data

### Understanding the Excel Template

BioDYM uses Excel files to define your system. Let's look at the structure:

1. **Navigate to the example**:
   ```
   basic_examples/basic_example_1/input_data.xlsx
   ```

2. **Open the file** in Excel. You'll see two sheets:
   - `biomass` - Total mass data
   - `carbon` - Carbon content data

### Data Structure

Each sheet contains:
- **Year**: Time points for your analysis
- **F_0_1**: Input flow from environment (how much enters the system)
- **TC_1_2**: Transfer coefficient to food (what fraction goes to food)
- **TC_1_3**: Transfer coefficient to biowaste (what fraction becomes waste)
- **TC_3_0**: Transfer coefficient from biowaste to environment

Example data:
| Year | F_0_1 | TC_1_2 | TC_1_3 | TC_3_0 |
|------|-------|--------|--------|--------|
| 2025 | 100   | 0.7    | 0.3    | 0.5    |
| 2026 | 110   | 0.7    | 0.3    | 0.5    |

This means:
- 100 units enter in 2025
- 70% goes to food (100 × 0.7 = 70)
- 30% goes to biowaste (100 × 0.3 = 30)
- 50% of biowaste returns to environment (30 × 0.5 = 15)

## Step 3: Run the Analysis

### Using the Command Line (Easiest)

1. **Copy the example to create your own**:
   ```bash
   cp basic_examples/basic_example_1/input_data.xlsx my_first_analysis.xlsx
   ```

2. **Run BioDYM**:
   ```bash
   python biodym_mfa_tool/src/main_cli.py --input my_first_analysis.xlsx
   ```

3. **Wait for completion**. You'll see:
   - Progress messages
   - Mass balance validation ✓
   - "Analysis complete!"

### Using Jupyter (More Interactive)

1. **Start Jupyter**:
   ```bash
   jupyter notebook
   ```

2. **Navigate to**: `biodym_mfa_tool/BioDYM_MFA_Analysis.py`

3. **Copy the code sections** into notebook cells

4. **Run cells in order** (Shift+Enter)

## Step 4: Understand the Results

### Mass Balance Check (Critical!)

The first result you'll see is the mass balance validation:

```
Mass Balance Check:
Process 0 (Environment): 0.00 ✓
Process 1 (Processing): 0.00 ✓
Process 2 (Food): 0.00 ✓
Process 3 (Biowaste): 0.00 ✓
```

✓ means the process is balanced (good!)
✗ would mean there's an error to fix

### Interactive Visualizations

1. **Sankey Diagram**: Shows material flows through the system
   - Width of arrows = amount of material
   - Use dropdown to switch between Biomass/Carbon
   - Use slider to see different years

2. **Stock Plots**: Shows accumulation in different processes
   - Bar height = total stock
   - Colors match process types

3. **Flow Analysis**: Detailed view of specific flows
   - Select flows from dropdown
   - Toggle between line/bar charts

## Step 5: Export Your Results

Results are automatically saved to:
```
data/02_output/results.xlsx
```

This file contains:
- **Flows sheet**: All calculated flows over time
- **Stocks sheet**: Stock levels in each process
- **Parameters sheet**: Your input data
- **Summary sheet**: Key metrics

## Common Modifications

### Change Time Period

Edit years in your Excel file:
```
2025 → 2030
2026 → 2031
...
```

### Add More Years

Simply add rows to your Excel sheets with new years and values.

### Adjust Transfer Coefficients

Change the TC values to model different scenarios:
- Higher TC_1_2 = more efficient food production
- Lower TC_3_0 = better waste retention

### Run Monte Carlo Uncertainty

Add the `--monte-carlo` flag:
```bash
python biodym_mfa_tool/src/main_cli.py --input my_first_analysis.xlsx --monte-carlo --iterations 100
```

## Next Steps

1. **Try modifying** the example data to see how results change
2. **Read** the [Excel Template Guide](EXCEL_TEMPLATE_GUIDE.md) for advanced features
3. **Explore** other examples in the `basic_examples` folder
4. **Create** your own system using the template generator

## Getting Help

- **Mass balance errors?** See [Troubleshooting](TROUBLESHOOTING.md)
- **Excel structure questions?** See [Excel Template Guide](EXCEL_TEMPLATE_GUIDE.md)
- **Moving from old notebooks?** See [Migration Guide](MIGRATION_GUIDE.md)

## Tips for Success

1. **Always check mass balance first** - it validates your model
2. **Start simple** - modify examples before creating from scratch
3. **Use meaningful names** - helps track your analyses
4. **Save scenarios** - compare different parameter sets
5. **Document assumptions** - use the metadata sheet

---

Congratulations! You've completed your first BioDYM analysis. The same principles apply to more complex systems - just with more processes and flows.