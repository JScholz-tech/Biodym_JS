# Monte Carlo Parameter Selection - User Guide

## 🎯 **Problem Solved: Parameter Name Complexity**

### **The Challenge**
Users previously had to know exact parameter names like:
- `dsm_6_lifetimes_Mean_0`
- `fomp_8_k1`
- `TC_03_04`
- `Initial_Stock_material`

This created a major usability barrier because:
1. **Complex naming conventions** - hard to remember
2. **Error-prone** - typos break the analysis
3. **Not intuitive** - names don't describe meaning
4. **Different parameter types** have different naming patterns

### **The Solution: Codelist-Based Selection**

We've created a **user-friendly parameter selection system** that:
- ✅ **Select parameters by meaning** - not technical names
- ✅ **Automatic name generation** - system creates correct names
- ✅ **Category-based browsing** - organized by parameter type
- ✅ **Validation** - ensures selected parameters exist
- ✅ **Excel export** - generates correct format automatically

---

## 📊 **How It Works**

### **1. Parameter Categories**

The system organizes all parameters into user-friendly categories:

| Category | Description | Examples |
|----------|-------------|----------|
| **Transfer Coefficients** | Flow distribution between processes | "Transfer Coefficient: Process 0 → Process 1" |
| **Dynamic Stock Model** | Product lifetime and stock dynamics | "DSM Process 6 - Category 0 - Mean Lifetime" |
| **First-Order Mineralization Process** | Organic matter decomposition | "FOMP Process 8 - Fast pool decay rate" |
| **Initial Stocks** | Starting stock values and composition | "Initial Stock - Process 3 - Material" |
| **Stock-Outflow Transfer Coefficients** | Stock consumption rates (BioDYM extension) | "Stock Consumption Rate: Process 2 → Process 4" |

### **2. User Selection Process**

Instead of typing technical names, users:

1. **Browse by category** - Select "Transfer Coefficients"
2. **See user-friendly descriptions** - "Transfer Coefficient: Harvest → Processing"
3. **Select by meaning** - Click on the parameter they want
4. **Configure uncertainty** - Choose distribution type and parameters
5. **Export automatically** - System generates correct Excel format

### **3. Automatic Name Generation**

The system automatically converts user selections to correct technical names:

```
User Selection: "Transfer Coefficient: Harvest → Processing"
↓
System Generates: "TC_00_01"
↓
Excel Format: Parameter_Name=TC_00_01, Distribution=normal, Mean=0.5, StdDev=0.05
```

---

## 🚀 **Usage Examples**

### **Example 1: Quick Setup**

```python
# Quick setup for common parameters
quick_params = quick_mc_setup(
    mfa_system=mfa_system,
    dsm_params=dsm_params,
    fomp_params=fomp_params,
    flows_df=flows_df,
    stocks_df=stocks_df,
    common_params=['Transfer Coefficients', 'Dynamic Stock Model']
)

print(f"Generated {len(quick_params)} parameters")
# Output: Generated 6 parameters
```

### **Example 2: Interactive Selection**

```python
# Create interactive interface
selector = create_mc_parameter_interface(
    mfa_system=mfa_system,
    dsm_params=dsm_params,
    fomp_params=fomp_params,
    flows_df=flows_df,
    stocks_df=stocks_df
)

# Users interact with dropdowns and checkboxes
# System automatically generates parameter names
```

### **Example 3: Manual Codelist Usage**

```python
# Create codelist
codelist = MCParameterCodelist(mfa_system, dsm_params, fomp_params)

# Get all available parameters
all_params = codelist.get_all_parameters(flows_df, stocks_df)

# Select parameters by user-friendly names
selected_params = [
    "Transfer Coefficient: Harvest → Processing",  # User-friendly
    "DSM Process 6 - Category 0 - Mean Lifetime",  # User-friendly
    "FOMP Process 8 - Fast pool decay rate"  # User-friendly
]

# Validate selection
is_valid, errors = codelist.validate_parameter_selection(selected_params)

# Export to Excel
excel_df = codelist.export_to_excel_format(selected_params)
```

---

## 📋 **Parameter Codelist Reference**

### **Transfer Coefficients (TCs)**

**Naming Pattern:** `TC_[StartProcess]_[EndProcess]`

| User-Friendly Name | Technical Name | Description | Typical Range |
|-------------------|----------------|-------------|---------------|
| Transfer Coefficient: Process 0 → Process 1 | `TC_00_01` | Flow from Process 0 to Process 1 | 0.0 - 1.0 |
| Transfer Coefficient: Process 1 → Process 2 | `TC_01_02` | Flow from Process 1 to Process 2 | 0.0 - 1.0 |

### **Dynamic Stock Model (DSM)**

**Naming Pattern:** `dsm_[ProcessID]_[Parameter]_[CategoryIndex]`

| User-Friendly Name | Technical Name | Description | Typical Range |
|-------------------|----------------|-------------|---------------|
| DSM Process 6 - Category 0 - Mean Lifetime | `dsm_6_lifetimes_Mean_0` | Average lifetime for category 0 | 1 - 100 years |
| DSM Process 6 - Category 0 - Lifetime StdDev | `dsm_6_lifetimes_StdDev_0` | Lifetime standard deviation | 0.1 - 20 years |
| DSM Process 6 - Category 0 - Inflow Split | `dsm_6_inflow_split_0` | Inflow fraction for category 0 | 0.0 - 1.0 |

### **First-Order Mineralization Process (FOMP)**

**Naming Pattern:** `fomp_[ProcessID]_[Parameter]`

| User-Friendly Name | Technical Name | Description | Typical Range |
|-------------------|----------------|-------------|---------------|
| FOMP Process 8 - Fast pool decay rate | `fomp_8_k1` | Fast pool decomposition rate | 0.001 - 0.1 1/year |
| FOMP Process 8 - Slow pool decay rate | `fomp_8_k2` | Slow pool decomposition rate | 0.0001 - 0.01 1/year |
| FOMP Process 8 - Fraction to fast pool | `fomp_8_f` | Fraction going to fast pool | 0.0 - 1.0 |

### **Initial Stocks**

**Naming Pattern:** `Initial_Stock_[Component]`

| User-Friendly Name | Technical Name | Description | Typical Range |
|-------------------|----------------|-------------|---------------|
| Initial Stock - Process 3 - Material | `Initial_Stock_material` | Initial material stock | 0 - 10000 Mg |
| Initial Stock - Process 3 - WC Content | `Initial_Stock_WC` | Water content fraction | 0.0 - 1.0 |
| Initial Stock - Process 3 - DM Content | `Initial_Stock_DM` | Dry matter content fraction | 0.0 - 1.0 |

### **Stock-Outflow Transfer Coefficients (BioDYM Extension)**

**Naming Pattern:** `STC_[ProcessID]_[DestinationProcess]`

| User-Friendly Name | Technical Name | Description | Typical Range |
|-------------------|----------------|-------------|---------------|
| Stock Consumption Rate: Process 2 → Process 4 | `STC_2_4` | Annual consumption rate | 0.0 - 1.0 1/year |

---

## 🔧 **Technical Implementation**

### **Core Components**

1. **`MCParameterCodelist`** - Generates parameter names and metadata
2. **`MCParameterSelector`** - Interactive user interface
3. **`quick_mc_setup`** - Automated parameter selection
4. **Excel export functions** - Generate correct format

### **Parameter Generation Process**

```python
# 1. Extract from flows data
tc_params = generate_tc_parameters(flows_df)
# Creates: TC_00_01, TC_01_02, etc.

# 2. Extract from DSM configuration
dsm_params = generate_dsm_parameters(dsm_params)
# Creates: dsm_6_lifetimes_Mean_0, etc.

# 3. Extract from FOMP configuration
fomp_params = generate_fomp_parameters(fomp_params)
# Creates: fomp_8_k1, fomp_8_k2, etc.

# 4. Extract from stocks data
stock_params = generate_stock_parameters(stocks_df)
# Creates: Initial_Stock_material, etc.
```

### **Validation Rules**

Each parameter type has validation rules:

- **Transfer Coefficients:** 0 ≤ value ≤ 1
- **DSM Lifetimes:** value > 0
- **DSM Inflow Splits:** 0 ≤ value ≤ 1, sum = 1.0
- **FOMP Rates:** value > 0
- **Stock-Outflow TCs:** 0 ≤ value ≤ 1

---

## 📈 **Benefits**

### **For Users:**
- ✅ **No need to memorize parameter names**
- ✅ **Intuitive selection by meaning**
- ✅ **Reduced errors and typos**
- ✅ **Faster parameter setup**
- ✅ **Automatic validation**

### **For Developers:**
- ✅ **Centralized parameter management**
- ✅ **Consistent naming conventions**
- ✅ **Easy to extend with new parameter types**
- ✅ **Automatic Excel format generation**
- ✅ **Built-in validation**

### **For System:**
- ✅ **Reduced user support requests**
- ✅ **More reliable Monte Carlo analyses**
- ✅ **Better user experience**
- ✅ **Standardized parameter handling**

---

## 🎯 **Next Steps**

1. **Integrate into main workflow** - Add to scientific notebook
2. **Create GUI interface** - Interactive parameter selection
3. **Add parameter templates** - Pre-configured common scenarios
4. **Extend validation** - More sophisticated parameter validation
5. **Add parameter sensitivity analysis** - Identify most important parameters

---

## 📚 **Related Documentation**

- [Monte Carlo Parameter Codelist](../MONTE_CARLO_PARAMETER_CODELIST.md) - Complete parameter reference
- [Excel Template Guide](../EXCEL_TEMPLATE_GUIDE.md) - Excel format specifications
- [Troubleshooting Guide](../TROUBLESHOOTING.md) - Common issues and solutions 