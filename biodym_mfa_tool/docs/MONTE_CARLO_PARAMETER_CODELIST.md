# Monte Carlo Parameter Codelist for BioDYM

## 📊 **Complete Parameter Reference for Uncertainty Analysis**

This document provides a comprehensive codelist of all parameter types that can be made uncertain in Monte Carlo simulations within the BioDYM framework.

---

## **1. TRANSFER COEFFICIENTS (TCs)**

### **1.1 Standard Transfer Coefficients**
**Naming Convention:** `TC_[StartProcess]_[EndProcess]`

| Parameter Name | Description | Example | Typical Range |
|---------------|-------------|---------|---------------|
| `TC_00_01` | Transfer coefficient from process 0 to process 1 | 0.5 | 0.0 - 1.0 |
| `TC_01_02` | Transfer coefficient from process 1 to process 2 | 0.8 | 0.0 - 1.0 |
| `TC_02_03` | Transfer coefficient from process 2 to process 3 | 0.6 | 0.0 - 1.0 |

**Distribution Types:**
- **Uniform**: `{'distribution': 'uniform', 'min': 0.4, 'max': 0.6}`
- **Normal**: `{'distribution': 'normal', 'mean': 0.5, 'std': 0.1}`
- **Triangular**: `{'distribution': 'triangular', 'min': 0.3, 'mode': 0.5, 'max': 0.7}`

### **1.2 Dynamic Transfer Coefficients**
**Naming Convention:** `TC_[StartProcess]_[EndProcess]_[Year]`

| Parameter Name | Description | Example |
|---------------|-------------|---------|
| `TC_04_00_2025` | Dynamic TC for 2025 | 0.3 |
| `TC_04_00_2035` | Dynamic TC for 2035 | 0.8 |

---

## **2. DYNAMIC STOCK MODEL (DSM) PARAMETERS**

### **2.1 DSM Lifetime Parameters**
**Naming Convention:** `dsm_[ProcessID]_lifetimes_[Type]_[CategoryIndex]`

| Parameter Name | Description | Example | Typical Range |
|---------------|-------------|---------|---------------|
| `dsm_6_lifetimes_Mean_0` | Mean lifetime for category 0 in process 6 | 30 | 1 - 100 years |
| `dsm_6_lifetimes_Mean_1` | Mean lifetime for category 1 in process 6 | 15 | 1 - 100 years |
| `dsm_6_lifetimes_StdDev_0` | Standard deviation for category 0 | 5 | 0.1 - 20 years |
| `dsm_6_lifetimes_StdDev_1` | Standard deviation for category 1 | 2 | 0.1 - 20 years |

### **2.2 DSM Inflow Split Parameters**
**Naming Convention:** `dsm_[ProcessID]_inflow_split_[CategoryIndex]`

| Parameter Name | Description | Example | Typical Range |
|---------------|-------------|---------|---------------|
| `dsm_6_inflow_split_0` | Inflow split for category 0 | 0.6 | 0.0 - 1.0 |
| `dsm_6_inflow_split_1` | Inflow split for category 1 | 0.2 | 0.0 - 1.0 |
| `dsm_6_inflow_split_2` | Inflow split for category 2 | 0.2 | 0.0 - 1.0 |

**Note:** Inflow splits must sum to 1.0 for each process.

---

## **3. FIRST-ORDER MINERALIZATION PROCESS (FOMP) PARAMETERS**

### **3.1 FOMP Decay Rate Parameters**
**Naming Convention:** `fomp_[ProcessID]_[ParameterName]`

| Parameter Name | Description | Example | Typical Range |
|---------------|-------------|---------|---------------|
| `fomp_8_k1` | Fast pool decay rate (1/year) | 0.025 | 0.001 - 0.1 |
| `fomp_8_k2` | Slow pool decay rate (1/year) | 0.005 | 0.0001 - 0.01 |
| `fomp_8_f` | Fraction to fast pool | 0.3 | 0.0 - 1.0 |

### **3.2 FOMP Initial Stock Parameters**
**Naming Convention:** `fomp_[ProcessID]_initial_stock_[Element]`

| Parameter Name | Description | Example | Typical Range |
|---------------|-------------|---------|---------------|
| `fomp_8_initial_stock_material` | Initial material stock | 1000 | 0 - 10000 Mg |
| `fomp_8_initial_stock_WC` | Initial water content | 0.1 | 0.0 - 1.0 |
| `fomp_8_initial_stock_DM` | Initial dry matter | 0.9 | 0.0 - 1.0 |
| `fomp_8_initial_stock_CC` | Initial carbon content | 0.45 | 0.0 - 1.0 |

---

## **4. STOCK-OUTFLOW TRANSFER COEFFICIENTS (BioDYM Extension)**

### **4.1 Stock Consumption Rate Parameters**
**Naming Convention:** `STC_[StockProcess]_[DestinationProcess]`

| Parameter Name | Description | Example | Typical Range |
|---------------|-------------|---------|---------------|
| `STC_09_00` | Stock consumption rate from process 9 to 0 | 0.1 | 0.0 - 1.0 |
| `STC_10_01` | Stock consumption rate from process 10 to 1 | 0.05 | 0.0 - 1.0 |

**Note:** These are BioDYM-specific extensions to the standard ODYM framework.

---

## **5. INITIAL STOCK PARAMETERS**

### **5.1 Initial Stock Values**
**Naming Convention:** `Initial_Stock_[Element]` or `initial_stock_[ProcessID]_[Element]`

| Parameter Name | Description | Example | Typical Range |
|---------------|-------------|---------|---------------|
| `Initial_Stock_material` | Initial material stock | 1000 | 0 - 10000 Mg |
| `Initial_Stock_WC` | Initial water content | 0.1 | 0.0 - 1.0 |
| `Initial_Stock_DM` | Initial dry matter | 0.9 | 0.0 - 1.0 |
| `Initial_Stock_CC` | Initial carbon content | 0.45 | 0.0 - 1.0 |

---

## **6. FLOW COMPOSITION PARAMETERS**

### **6.1 Element Composition Parameters**
**Naming Convention:** `[Element]_[FlowName]`

| Parameter Name | Description | Example | Typical Range |
|---------------|-------------|---------|---------------|
| `WC_F_00_01` | Water content in flow F_00_01 | 0.1 | 0.0 - 1.0 |
| `DM_F_00_01` | Dry matter in flow F_00_01 | 0.9 | 0.0 - 1.0 |
| `CC_F_00_01` | Carbon content in flow F_00_01 | 0.45 | 0.0 - 1.0 |

---

## **7. CONFIGURATION PARAMETERS**

### **7.1 Monte Carlo Configuration**
| Parameter Name | Description | Example | Typical Range |
|---------------|-------------|---------|---------------|
| `MC_ITERATIONS` | Number of Monte Carlo iterations | 100 | 10 - 10000 |
| `RUN_MONTE_CARLO` | Enable/disable MC simulation | True | Boolean |

---

## **8. DISTRIBUTION TYPES AND PARAMETERS**

### **8.1 Supported Distribution Types**

#### **Normal Distribution**
```python
{
    'distribution': 'normal',
    'mean': 0.5,
    'std': 0.1
}
```

#### **Uniform Distribution**
```python
{
    'distribution': 'uniform',
    'min': 0.4,
    'max': 0.6
}
```

#### **Triangular Distribution**
```python
{
    'distribution': 'triangular',
    'min': 0.3,
    'mode': 0.5,
    'max': 0.7
}
```

#### **Lognormal Distribution**
```python
{
    'distribution': 'lognormal',
    'mean': 0.5,
    'std': 0.1
}
```

---

## **9. EXCEL INPUT FORMAT**

### **9.1 Uncertainty Parameters Sheet (`4_1_Uncertainty_Parameters`)**

| Column | Description | Example | Required |
|--------|-------------|---------|----------|
| `Parameter_Name` | Exact parameter name | `TC_03_04` | Yes |
| `Distribution` | Distribution type | `uniform` | Yes |
| `Min` | Minimum value | 0.4 | For uniform/triangular |
| `Max` | Maximum value | 0.6 | For uniform/triangular |
| `Mode` | Mode value | 0.5 | For triangular |
| `Mean` | Mean value | 0.5 | For normal/lognormal |
| `StdDev` | Standard deviation | 0.1 | For normal/lognormal |

**Example Excel Entry:**
```
Parameter_Name | Distribution | Min | Max | Mode | Mean | StdDev
TC_03_04      | uniform      | 0.4 | 0.6 |      |      |
dsm_6_lifetimes_Mean_0 | triangular | 25 | 40 | 30 |      |
fomp_8_k1     | normal       |     |     |     | 0.025 | 0.005
```

---

## **10. PARAMETER VALIDATION RULES**

### **10.1 Transfer Coefficients**
- **Range**: 0.0 ≤ TC ≤ 1.0
- **Sum Rule**: For each process, sum of outgoing TCs ≤ 1.0

### **10.2 DSM Parameters**
- **Lifetimes**: Mean > 0, StdDev ≥ 0
- **Inflow Splits**: 0.0 ≤ split ≤ 1.0, sum = 1.0 per process

### **10.3 FOMP Parameters**
- **Decay Rates**: k1, k2 > 0
- **Fraction**: 0.0 ≤ f ≤ 1.0
- **Composition**: 0.0 ≤ composition ≤ 1.0

### **10.4 Stock Parameters**
- **Initial Values**: ≥ 0
- **Composition**: 0.0 ≤ composition ≤ 1.0

---

## **11. BEST PRACTICES**

### **11.1 Parameter Selection**
1. **Start with TCs**: Most impactful on results
2. **Add DSM lifetimes**: For long-lived products
3. **Include FOMP rates**: For organic decomposition
4. **Consider composition**: For multi-element systems

### **11.2 Distribution Selection**
- **Normal**: When you have mean and standard deviation
- **Uniform**: When you only know min/max bounds
- **Triangular**: Expert opinion with most likely value
- **Lognormal**: For skewed distributions (lifetimes)

### **11.3 Uncertainty Ranges**
- **Conservative**: ±10-20% for well-known parameters
- **Moderate**: ±20-50% for estimated parameters
- **High**: ±50-100% for poorly known parameters

---

## **12. EXAMPLE COMPLETE CONFIGURATION**

```python
UNCERTAINTY_PARAMS = {
    # Transfer Coefficients
    'TC_03_04': {'distribution': 'uniform', 'min': 0.4, 'max': 0.6},
    'TC_04_00': {'distribution': 'normal', 'mean': 0.5, 'std': 0.1},
    
    # DSM Parameters
    'dsm_6_lifetimes_Mean_0': {'distribution': 'triangular', 'min': 25, 'mode': 30, 'max': 40},
    'dsm_6_lifetimes_StdDev_0': {'distribution': 'uniform', 'min': 3, 'max': 7},
    'dsm_6_inflow_split_0': {'distribution': 'normal', 'mean': 0.6, 'std': 0.1},
    
    # FOMP Parameters
    'fomp_8_k1': {'distribution': 'normal', 'mean': 0.025, 'std': 0.005},
    'fomp_8_k2': {'distribution': 'normal', 'mean': 0.005, 'std': 0.001},
    
    # Stock-Outflow TCs (BioDYM Extension)
    'STC_09_00': {'distribution': 'uniform', 'min': 0.05, 'max': 0.15},
    
    # Initial Stock
    'Initial_Stock_material': {'distribution': 'normal', 'mean': 1000, 'std': 100},
    
    # Composition Parameters
    'WC_F_00_01': {'distribution': 'normal', 'mean': 0.1, 'std': 0.02},
    'CC_F_00_01': {'distribution': 'normal', 'mean': 0.45, 'std': 0.05}
}
```

---

## **13. TROUBLESHOOTING**

### **13.1 Common Issues**
1. **Parameter not found**: Check exact naming convention
2. **Invalid distribution**: Use supported distribution types
3. **Range violations**: Ensure parameters stay within valid bounds
4. **Sum violations**: Check that TC sums ≤ 1.0 per process

### **13.2 Validation Functions**
- Use `utils.validate_uncertainty_params()` to check configuration
- Use `utils.sample_parameters()` to test sampling
- Check Excel sheet format with `data_loader.load_uncertainty_definitions()`

---

*This codelist covers all parameter types currently supported in the BioDYM framework for Monte Carlo uncertainty analysis.* 