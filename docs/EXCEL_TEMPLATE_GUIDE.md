# BioDYM Excel Template Guide

This guide explains how to structure your data in the BioDYM Excel template. Each sheet has a specific purpose and required format.

## Template Overview

The Excel template organizes your MFA system definition into logical sheets:

| Sheet | Purpose | Required |
|-------|---------|----------|
| 0_Metadata | Dataset documentation | Recommended |
| 1_1_Definition_Flows | Define system connections | ✓ |
| 1_2_Data_Flows | Input flow time series | ✓ |
| 2_1_Definition_Processes | Define system nodes | ✓ |
| 2_3_Process_TCs | Static transfer coefficients | ✓ |
| 2_4_Process_Stock | Initial stock values | If stocks exist |
| 2_5_dynamic_tcs | Time-varying coefficients | Optional |
| 3_1_Definition_DSM | Dynamic stock parameters | If using DSM |
| 3_2_Definition_FOMP | Mineralization parameters | If using FOMP |
| 4_1_Uncertainty_Parameters | Monte Carlo settings | If using MC |

## Sheet-by-Sheet Guide

### 0_Metadata (Recommended)

Document your dataset for future reference.

| Column | Description | Example |
|--------|-------------|---------|
| Dataset_Name | Descriptive name | "Wheat Straw Analysis 2025" |
| Version | Version number | "1.0.0" |
| Date_Modified | Last update date | "2025-01-15" |
| Author | Creator name | "J. Smith" |
| Description | Brief summary | "Analysis of wheat straw cascading through biorefinery" |
| Source_Reference | Data source | "Smith et al. (2025)" |

### 1_1_Definition_Flows

Define all connections between processes in your system.

| Column | Description | Example | Rules |
|--------|-------------|---------|-------|
| Flow_ID | Unique identifier | "F_01_02" | Format: F_origin_destination |
| Name(EN) | Descriptive name | "Harvest to Processing" | Human-readable |
| Process_ID_O | Origin process ID | 1 | Must exist in processes |
| Process_ID_I | Destination process ID | 2 | Must exist in processes |
| WC | Water content (%) | 0.15 | Optional, 0-1 range |
| DM | Dry matter (%) | 0.85 | Optional, 0-1 range |
| CC | Carbon content (%) | 0.45 | Optional, 0-1 range |

**Important**: 
- Process ID 0 is reserved for system boundary (environment)
- WC + DM should equal 1.0
- CC is typically relative to dry matter

### 1_2_Data_Flows

Time series data for PRIMARY input flows (from system boundary).

| Column | Description | Example | Rules |
|--------|-------------|---------|-------|
| Flow_ID | Flow identifier | "F_00_01" | Must match Definition_Flows |
| Year_Flow | Year | 2025 | Integer |
| Flow_Py | Flow value | 1500.75 | In system units (e.g., Mg) |

**Note**: Only includes flows FROM process 0 (system boundary)

### 2_1_Definition_Processes

Define all nodes (processes) in your system.

| Column | Description | Example | Rules |
|--------|-------------|---------|-------|
| ID | Unique integer ID | 3 | 0 = system boundary |
| Name(EN) | Process name | "Biogas Digester" | Descriptive |
| Stock? | Has stock? | "Yes" | Yes/No |
| Initial_Stock? | Non-zero start? | "No" | Yes/No |
| Process_Type | Category | "Treatment" | Optional grouping |

**Process Types** (optional):
- Input: Entry points
- Treatment: Processing steps
- Use: Product use phases
- EoL: End-of-life handling
- Output: Exit points

### 2_3_Process_TCs

Static (constant) transfer coefficients.

| Column | Description | Example | Rules |
|--------|-------------|---------|-------|
| TC_ID | Unique identifier | "TC_02_03" | Format: TC_origin_destination |
| TC_Value | Coefficient value | 0.85 | Range: 0-1 |

**Important**: 
- Sum of TCs leaving a process should ≤ 1.0
- Remainder stays as stock change

### 2_4_Process_Stock

Initial stock values for processes marked with Initial_Stock = Yes.

| Column | Description | Example | Rules |
|--------|-------------|---------|-------|
| Process_ID | Process with stock | 6 | Must have Stock? = Yes |
| Initial_Stock_material | Total mass | 1000 | System units |
| Initial_Stock_WC[%] | Water content | 0.1 | As percentage (10%) |
| Initial_Stock_DM[%] | Dry matter | 0.9 | As percentage (90%) |
| Initial_Stock_CC[%] | Carbon content | 0.45 | As percentage (45%) |

### 2_5_dynamic_tcs

Time-varying transfer coefficients (linear interpolation between points).

| Column | Description | Example | Rules |
|--------|-------------|---------|-------|
| TC_ID | Coefficient ID | "TC_04_00" | Must exist in Process_TCs |
| Year | Year | 2030 | Within analysis period |
| Value | TC value at year | 0.6 | Range: 0-1 |

**Example**: Increasing recycling rate
```
TC_ID    Year    Value
TC_04_00 2025    0.3
TC_04_00 2035    0.8
```

### 3_1_Definition_DSM

Dynamic Stock Model parameters for products with lifetimes.

| Column | Description | Example | Rules |
|--------|-------------|---------|-------|
| Process_ID | Stock process | 6 | Must have Stock? = Yes |
| Category_ID | Product category | 1 | Unique within process |
| Inflow_Split_[%] | Share of inflow | 0.6 | Sum = 1.0 per process |
| Lifetime_Type | Distribution | "Normal" | Normal/Lognormal/Fixed |
| Lifetime_Mean | Average lifetime | 30 | Years |
| Lifetime_StdDev | Standard deviation | 5 | Years (0 for Fixed) |
| Category_Name | Display name | "Building Materials" | For plots |

**Lifetime Types**:
- Normal: Bell curve distribution
- Lognormal: Skewed (products rarely fail early)
- Fixed: All products last exactly X years

### 3_2_Definition_FOMP

First-Order Mineralization Process for organic decomposition.

| Column | Description | Example | Rules |
|--------|-------------|---------|-------|
| Process_ID | FOMP process | 8 | Must be defined |
| Parameter_Name | Parameter type | "k1" | See below |
| Value | Parameter value | 0.025 | Depends on type |

**Parameters**:
- `k1`: Fast pool decay rate (1/year)
- `k2`: Slow pool decay rate (1/year)
- `f`: Fraction to fast pool (0-1)
- `outflow_id`: Flow ID for mineralized material

**Example**: Soil carbon
```
Process_ID  Parameter_Name  Value
8           k1             0.1      # 10% fast pool decays/year
8           k2             0.01     # 1% slow pool decays/year
8           f              0.3      # 30% goes to fast pool
8           outflow_id     F_08_00  # Returns to environment
```

### 4_1_Uncertainty_Parameters

Monte Carlo simulation settings.

| Column | Description | Example | Rules |
|--------|-------------|---------|-------|
| Parameter_Name | Parameter to vary | "TC_02_03" | Exact system name |
| Distribution | Type | "normal" | See below |
| Min | Minimum value | 0.7 | For uniform/triangle |
| Max | Maximum value | 0.9 | For uniform/triangle |
| Mean | Average | 0.8 | For normal |
| StdDev | Standard deviation | 0.05 | For normal |
| Mode | Most likely | 0.85 | For triangle |

**Distribution Types**:
- `uniform`: Equal probability across range
- `normal`: Bell curve around mean
- `triangle`: Peak at mode
- `lognormal`: Skewed positive

## Common Patterns

### Simple Linear System
```
Environment → Process A → Process B → Environment
```
- Define 3 processes (0, 1, 2)
- Create flows: F_00_01, F_01_02, F_02_00
- Set TCs for each flow

### Branching System
```
           → Product (Stock)
Input →  ↗
         ↘ → Waste → Environment
```
- Use multiple TCs from same origin
- Ensure TC sum ≤ 1.0

### Cascading Use
```
Input → Use 1 → Use 2 → Use 3 → EoL
```
- Chain processes with TC = 1.0 between uses
- Apply lifetime distributions at each use

## Validation Checklist

Before running your analysis, verify:

- [ ] All process IDs in flows exist in Definition_Processes
- [ ] Transfer coefficients sum ≤ 1.0 for each process
- [ ] Years in Data_Flows match analysis period
- [ ] Element percentages sum correctly (WC + DM = 1.0)
- [ ] DSM inflow splits sum to 1.0
- [ ] Initial stocks have all required element data
- [ ] Flow IDs follow naming convention
- [ ] No duplicate IDs within sheets

## Tips for Success

1. **Start Simple**: Begin with few processes, add complexity gradually
2. **Use Meaningful Names**: "F_harvest_processing" better than "F_01_02"
3. **Document Assumptions**: Use metadata sheet and comments
4. **Check Units**: Ensure consistency (all Mg or all tonnes)
5. **Version Control**: Save versions when making major changes
6. **Test Small**: Run with few years first to verify setup

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "Process ID not found" | Flow references undefined process | Check Definition_Processes |
| "TC sum > 1" | Transfer coefficients too high | Reduce TCs or add stock |
| "Mass balance error" | Inputs ≠ Outputs + Stock | Check all TCs and flows |
| "Missing required column" | Excel structure incorrect | Use template generator |

## Advanced Features

### Multi-Element Tracking
Track multiple elements (C, N, P) by adding more sheets with same structure but different element data.

### Scenario Comparison
Create multiple Excel files with different parameters, run separately, compare results.

### Coupled Processes
Link outputs of one system as inputs to another using consistent Flow_IDs.

---

For more help, see:
- [Quick Start Tutorial](QUICKSTART.md) - Step-by-step first analysis
- [Troubleshooting](TROUBLESHOOTING.md) - Common problems and solutions
- [Migration Guide](MIGRATION_GUIDE.md) - Moving from old notebooks