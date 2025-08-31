# Configuration Sheet Analysis - 0_Configuration

## 📋 Overview

**Sheet Name**: `0_Configuration`  
**Location**: `data/01_input/250813_CS1_simple_V1.xlsx`  
**Structure**: 30 rows × 3 columns  
**Purpose**: Central configuration for BioDYM MFA Tool  
**Analysis Date**: 2025-08-31

## 🗂️ Sheet Structure

### **Column Layout**
| **Column** | **Name** | **Purpose** | **Content Type** |
|------------|----------|-------------|------------------|
| **Column 0** | `BioDYM MFA Tool - Configuration Settings` | Configuration categories and keys | Text/Headers |
| **Column 1** | `Selected Options` | Configuration values | Mixed (Text/Numbers) |
| **Column 2** | `Comment` | Additional notes | Text (mostly empty) |

### **Row Organization**
- **Rows 0-1**: Header information
- **Rows 2-6**: File paths and model scope
- **Rows 7-11**: Calculation options
- **Rows 12-15**: Analysis settings
- **Rows 16-20**: Scenario management
- **Rows 21-25**: Visualization settings
- **Rows 26-29**: Validation settings

## 📊 Configuration Categories

### **1. FILE PATHS (Rows 1-2)**
| **Setting** | **Value** | **Purpose** | **Status** |
|-------------|-----------|-------------|------------|
| Input File Path | `data/01_input/your_data_file.xlsx` | Input data location | ⚠️ **Placeholder** |
| Output File Path | `data/02_output/results.xlsx` | Results output location | ✅ **Configured** |

### **2. MODEL SCOPE (Rows 4-6)**
| **Setting** | **Value** | **Purpose** | **Status** |
|-------------|-----------|-------------|------------|
| Start Year | `2025` | Analysis start year | ✅ **Configured** |
| End Year | `2050` | Analysis end year | ✅ **Configured** |
| Elements | `material,WC,DM,CC` | Elements to track | ✅ **Configured** |

### **3. CALCULATION OPTIONS (Rows 8-11)**
| **Setting** | **Value** | **Purpose** | **Status** |
|-------------|-----------|-------------|------------|
| Monte Carlo Simulation | `No` | Enable MC analysis | ✅ **Configured** |
| Monte Carlo Iterations | `10` | Number of MC runs | ✅ **Configured** |
| DSM Calculation | `No` | Enable DSM analysis | ✅ **Configured** |
| FOMP Calculation | `Yes` | Enable FOMP analysis | ✅ **Configured** |

### **4. ANALYSIS SETTINGS (Rows 13-15)**
| **Setting** | **Value** | **Purpose** | **Status** |
|-------------|-----------|-------------|------------|
| Minimum Flow Threshold | `0.1` | Filter small flows | ✅ **Configured** |
| Show Zero Flows | `No` | Display zero flows | ✅ **Configured** |
| Export Format | `Excel` | Results format | ✅ **Configured** |

### **5. SCENARIO MANAGER (Rows 17-20)**
| **Setting** | **Value** | **Purpose** | **Status** |
|-------------|-----------|-------------|------------|
| Scenario Available | `Yes` | Enable scenarios | ✅ **Configured** |
| Scenario 1 | `High recycling rate` | First scenario | ✅ **Configured** |
| Scenario 2 | `No incineration` | Second scenario | ✅ **Configured** |
| Scenario 3 | Empty | Third scenario | ⚠️ **Not configured** |

### **6. VISUALIZATION SETTINGS (Rows 22-25)**
| **Setting** | **Value** | **Purpose** | **Status** |
|-------------|-----------|-------------|------------|
| Default Plot Style | `Line` | Chart type | ✅ **Configured** |
| Color Scheme | `Default` | Plot colors | ✅ **Configured** |
| Export Plots as Images | `Yes` | Save plots | ✅ **Configured** |
| Dashboard Layout | `Grid` | Layout style | ✅ **Configured** |

### **7. VALIDATION SETTINGS (Rows 27-29)**
| **Setting** | **Value** | **Purpose** | **Status** |
|-------------|-----------|-------------|------------|
| Mass Balance Tolerance | `0.001` | Error threshold | ✅ **Configured** |
| Data Validation Level | `Strict` | Validation rigor | ✅ **Configured** |
| Auto-save Results | `Yes` | Auto-save | ✅ **Configured** |

## 🔍 Function Usage Analysis

### **Current Usage**
- **Function**: `config.load_config_from_excel()` (imported but not used in Steps 1-2)
- **Status**: ❌ **NOT USED YET**
- **Expected Usage**: Step 3 (Visualization) or Step 4 (Export)

### **Configuration Loading Pattern**
```python
# Expected usage pattern
config_dict = config.load_config_from_excel(input_file)
monte_carlo_enabled = config_dict.get('Run Monte Carlo Simulation', False)
mc_iterations = config_dict.get('Monte Carlo Iterations', 10)
```

## 📝 Key Findings

### **1. Configuration Completeness**
- **✅ Well-structured**: Clear categories and logical organization
- **✅ Comprehensive**: Covers all major tool aspects
- **⚠️ Some placeholders**: Input file path needs updating

### **2. Feature Configuration**
- **Monte Carlo**: Disabled (10 iterations if enabled)
- **DSM**: Disabled
- **FOMP**: Enabled
- **Scenarios**: Available with 2 defined scenarios

### **3. Analysis Settings**
- **Time Range**: 2025-2050 (26 years)
- **Elements**: 4 elements (material, WC, DM, CC)
- **Threshold**: 0.1 Mg minimum flow

### **4. Visualization Preferences**
- **Style**: Line charts
- **Export**: Images enabled
- **Layout**: Grid dashboard

## 🚨 Issues and Recommendations

### **Immediate Issues**
1. **Input File Path**: Placeholder value needs updating
2. **Scenario 3**: Empty scenario definition
3. **Comment Column**: Mostly unused (could be removed)

### **Configuration Improvements**
1. **Add validation**: Ensure values are within valid ranges
2. **Add descriptions**: Use comment column for explanations
3. **Add units**: Specify units for numerical values
4. **Add dependencies**: Link related settings

### **Function Integration**
1. **Implement config loading**: Use this sheet in the notebook
2. **Add validation**: Check configuration before running analysis
3. **Add overrides**: Allow command-line overrides

## 🎯 Expected Usage in Workflow

### **Step 1: Setup and Data Loading**
- **Not used** - Hardcoded values used instead

### **Step 2: Calculation & Validation**
- **Not used** - Hardcoded values used instead

### **Step 3: Visualization (Predicted)**
- **Plot style**: Line charts
- **Color scheme**: Default
- **Export settings**: Images enabled

### **Step 4: Export (Predicted)**
- **Output format**: Excel
- **Auto-save**: Enabled
- **File paths**: Output location

## 📊 Configuration Status Summary

| **Category** | **Configured** | **Placeholder** | **Empty** | **Total** |
|--------------|----------------|-----------------|-----------|-----------|
| File Paths | 1 | 1 | 0 | 2 |
| Model Scope | 3 | 0 | 0 | 3 |
| Calculation | 4 | 0 | 0 | 4 |
| Analysis | 3 | 0 | 0 | 3 |
| Scenarios | 3 | 0 | 1 | 4 |
| Visualization | 4 | 0 | 0 | 4 |
| Validation | 3 | 0 | 0 | 3 |
| **Total** | **21** | **1** | **1** | **23** |

**Configuration Rate**: 91% (21/23 settings configured)

## 🚀 Next Steps

1. **Update input file path** to actual file location
2. **Define Scenario 3** or remove empty row
3. **Implement config loading** in the notebook
4. **Add configuration validation**
5. **Use configuration values** instead of hardcoded values

---

*Analysis Completed: 2025-08-31*  
*Sheet: 0_Configuration*  
*Status: ✅ ANALYZED - READY FOR INTEGRATION*
