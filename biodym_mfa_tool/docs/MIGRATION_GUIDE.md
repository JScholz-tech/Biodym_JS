# Migration Guide: From Notebooks to BioDYM Tool

This guide helps you transition from the legacy Jupyter notebook workflow to the modern BioDYM modular tool.

## Why Migrate?

### Benefits of the New Tool

| Old Notebooks | New BioDYM Tool |
|---------------|-----------------|
| Copy-paste code blocks | Reusable modules |
| Manual error checking | Automatic validation |
| Code mixed with data | Clean separation |
| Limited error messages | Detailed diagnostics |
| Single workflow | Multiple interfaces |
| No version control | Scenario management |

### Key Improvements

1. **Error Prevention**: Validation before calculations
2. **Reproducibility**: Save and reload scenarios
3. **Flexibility**: CLI, Jupyter, or Python API
4. **Performance**: Optimized calculations
5. **Maintenance**: Easier to update and debug

## Migration Strategies

### Option 1: Quick Migration (Recommended)

Best for: Simple systems, standard workflows

1. **Export your data** from notebook to Excel
2. **Use template generator** to create structure
3. **Copy values** into new template
4. **Run with new tool**

### Option 2: Gradual Migration

Best for: Complex systems, custom calculations

1. **Keep notebook** for reference
2. **Build Excel template** incrementally
3. **Test each component**
4. **Validate against notebook results**

### Option 3: Parallel Running

Best for: Critical analyses, validation needed

1. **Run both systems** temporarily
2. **Compare results**
3. **Document differences**
4. **Switch when confident**

## Step-by-Step Migration

### Step 1: Understand Your Current System

Review your notebook and identify:
- [ ] Number of processes
- [ ] Flow connections
- [ ] Transfer coefficients
- [ ] Time period
- [ ] Special calculations (DSM, FOMP)

### Step 2: Create Excel Template

```bash
# Generate blank template
python biodym_mfa_tool/generate_excel_template.py

# Or copy example
cp biodym_mfa_tool/data/01_input/BioDYM_MFA_Input_Template.xlsx my_system.xlsx
```

### Step 3: Map Notebook → Excel

#### Process Definitions

**Notebook code**:
```python
Dyn_MFA_System.ProcessList.append(msc.Process(Name = 'Processing', ID = 1))
Dyn_MFA_System.ProcessList.append(msc.Process(Name = 'Use', ID = 2))
```

**Excel (2_1_Definition_Processes)**:
| ID | Name(EN) | Stock? | Initial_Stock? |
|----|----------|--------|----------------|
| 1 | Processing | No | No |
| 2 | Use | Yes | No |

#### Flow Definitions

**Notebook code**:
```python
Dyn_MFA_System.FlowDict['F_0_1'] = msc.Flow(Name = 'Input', P_Start = 0, P_End = 1)
```

**Excel (1_1_Definition_Flows)**:
| Flow_ID | Name(EN) | Process_ID_O | Process_ID_I |
|---------|----------|--------------|--------------|
| F_00_01 | Input | 0 | 1 |

#### Transfer Coefficients

**Notebook code**:
```python
TC_1_2 = 0.7
Flow_1_2 = Flow_0_1 * TC_1_2
```

**Excel (2_3_Process_TCs)**:
| TC_ID | TC_Value |
|-------|----------|
| TC_01_02 | 0.7 |

### Step 4: Handle Special Features

#### Dynamic Stock Model

**Notebook code**:
```python
DSM_Lifetime_mean = 30
DSM_Lifetime_std = 5
```

**Excel (3_1_Definition_DSM)**:
| Process_ID | Category_ID | Lifetime_Type | Lifetime_Mean | Lifetime_StdDev |
|------------|-------------|---------------|---------------|-----------------|
| 2 | 1 | Normal | 30 | 5 |

#### First-Order Process

**Notebook code**:
```python
k_rate = 0.025
mineralization = stock * k_rate
```

**Excel (3_2_Definition_FOMP)**:
| Process_ID | Parameter_Name | Value |
|------------|----------------|-------|
| 3 | k1 | 0.025 |

### Step 5: Validate Migration

1. **Run both systems** with same input
2. **Compare key outputs**:
   - Total flows per year
   - Final stock levels
   - Mass balance checks
3. **Check visualization** matches
4. **Document any differences**

## Common Migration Issues

### Issue: Different Results

**Causes**:
- Rounding differences
- Calculation order
- Default assumptions

**Solution**: Check tolerance levels, usually < 0.1% difference is acceptable

### Issue: Missing Features

Some notebook customizations may need adaptation:

| Notebook Feature | BioDYM Tool Equivalent |
|-----------------|------------------------|
| Custom plots | Use plotting.py module |
| Special calculations | Extend engine modules |
| Data preprocessing | Add to data_loader.py |

### Issue: Complex Formulas

**Notebook**:
```python
complex_flow = (input * factor1 * (1 - loss_rate)) / efficiency
```

**Solution**: Break into multiple TCs:
1. TC for factor1
2. TC for (1 - loss_rate)
3. TC for 1/efficiency

## Verification Checklist

After migration, verify:

- [ ] Mass balance passes (error < 1e-10)
- [ ] Total system throughput matches
- [ ] Stock accumulation correct
- [ ] Time series trends similar
- [ ] Element balances maintained
- [ ] Uncertainty ranges overlap

## Migration Examples

### Example 1: Simple Linear System

**Old Notebook Structure**:
```
notebooks/
└── my_analysis.ipynb (500+ lines)
```

**New Tool Structure**:
```
my_project/
├── data/
│   └── my_analysis.xlsx
├── scenarios/
│   ├── baseline.json
│   └── improved.json
└── results/
    └── comparison.xlsx
```

### Example 2: Research Project

**Before**: Multiple notebook versions
```
analysis_v1.ipynb
analysis_v2_fixed.ipynb
analysis_final.ipynb
analysis_final_REAL.ipynb
```

**After**: Single tool, multiple scenarios
```
python src/main_cli.py --input base_case.xlsx --scenario baseline
python src/main_cli.py --input sensitivity_1.xlsx --scenario test1
python src/main_cli.py --compare baseline test1
```

## Best Practices

1. **Start Fresh**: Don't try to convert code directly
2. **Think in Flows**: Map your system conceptually first
3. **Use Examples**: Study basic_examples for patterns
4. **Test Incrementally**: Validate each component
5. **Document Changes**: Note any assumptions
6. **Keep Backups**: Archive working notebooks

## Getting Help

### Migration Support

1. **Use debug mode** to see calculations:
   ```bash
   python src/main_cli.py --input data.xlsx --debug
   ```

2. **Export intermediate results** for comparison

3. **Check calculation logs** in biodym_mfa_tool/logs/

### Common Questions

**Q: Can I still use my custom visualizations?**
A: Yes, export results and use your existing plotting code

**Q: What about my Monte Carlo setup?**
A: Add uncertainty parameters to sheet 4_1

**Q: Can I extend the tool?**
A: Yes, the modular structure makes it easy to add features

## Next Steps

After successful migration:

1. Delete duplicate notebooks
2. Document your system in metadata
3. Create scenarios for different cases
4. Set up automated runs with CLI
5. Share templates with colleagues

---

Remember: The goal is not to replicate your notebook exactly, but to achieve the same analytical results with a more robust tool!