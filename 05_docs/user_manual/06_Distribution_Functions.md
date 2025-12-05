# Distribution Functions in BioDYM - Complete Reference Guide

This document provides a comprehensive overview of all distribution functions used in BioDYM, their purposes, required parameters, and usage contexts.

---

## Overview

BioDYM uses distribution functions in two distinct contexts:

1. **DSM (Dynamic Stock Model)** - For modeling product lifetime distributions
2. **Monte Carlo Simulation** - For uncertainty analysis of model parameters

---

## 1. DSM Lifetime Distributions

**Purpose:** Define how long products/materials stay in stock before outflow

**Location:** Sheet `3_1_Definition_DSM`, Column `Lifetime_Type` (or `DSM_Lifetime_Type_Cat_#`)

### Available Distributions

| Distribution | Required Parameters | Use Case | Notes |
|--------------|-------------------|----------|--------|
| **Fixed** | • Mean (years) | Products with exact known lifetime | No variability; all items leave stock at exactly Mean years |
| **Normal** | • Mean (years)<br>• StdDev (years) | Products with symmetric lifetime variation | ⚠️ Can generate negative lifetimes if StdDev is too large (>80% of Mean) |
| **FoldedNormal** | • Mean (years, before folding)<br>• StdDev (years, before folding) | Products with symmetric variation but no negative lifetimes | Safer alternative to Normal; eliminates negative lifetime issue |
| **LogNormal** | • Mean (years, of lognormal curve)<br>• StdDev (years, of lognormal curve) | Products with right-skewed lifetime (some last much longer) | Common for electronics, machinery; always positive values |
| **Weibull** | • Mean (years)<br>• Shape (dimensionless) | Products with increasing/decreasing failure rates | Shape < 1: early failures<br>Shape = 1: constant rate<br>Shape > 1: wear-out failures |

### Parameter Naming (New Format)
```
DSM_Lifetime_Type_Cat_1       = "Normal"
DSM_Lifetime_Mean_Cat_1       = 30        # years
DSM_Lifetime_StdDev_Cat_1     = 5         # years
```

### Parameter Naming (Legacy Format)
```
Lifetime_Type    = "Normal"
Lifetime_Mean    = 30        # years
Lifetime_StdDev  = 5         # years
```

---

## 2. Monte Carlo Uncertainty Distributions

**Purpose:** Define uncertainty ranges for model parameters (TCs, flow data, DSM parameters, etc.)

**Location:** Sheet `4_1_Uncertainty_Parameters`, Column `Distribution_Type`

### Available Distributions

| Distribution | Required Parameters | Use Case | Notes |
|--------------|-------------------|----------|--------|
| **normal** | • Mean<br>• StdDev<br>• Optional: Min, Max (bounds) | Parameters with symmetric uncertainty around a mean value | Can be bounded with Min/Max to prevent unrealistic values |
| **uniform** | • Min<br>• Max | Parameters where any value in range is equally likely | Use when you only know the range, not the most likely value |
| **triangular** | • Min<br>• Mode<br>• Max | Parameters where you know range and most likely value | Good for expert estimates; Mode is the peak of the triangle |
| **lognormal** | • Mean (of lognormal)<br>• StdDev (of lognormal)<br>• Optional: Min, Max | Parameters that are always positive with right skew | Common for rates, fractions; use when lower bound is important |

### Parameter Format
```
Parameter_Name       Distribution_Type    Mean    StdDev    Min     Max     Mode
TC_Recycling_Rate    normal              0.65    0.10      0.0     1.0     -
Flow_Input_2020      uniform             -       -         1000    1500    -
TC_Split_Product_A   triangular          -       -         0.3     0.5     0.4
Decay_Rate_k1        lognormal           0.05    0.01      0.001   0.2     -
```

---

## 3. Key Differences & Important Notes

### Naming Inconsistencies (TO BE AWARE OF)

| Context | Normal | Lognormal | Fixed |
|---------|--------|-----------|-------|
| **DSM** | "Normal" | "LogNormal" | "Fixed" |
| **Monte Carlo** | "normal" | "lognormal" | N/A |

⚠️ **Case Sensitivity:** DSM uses capitalized names, Monte Carlo uses lowercase. The system handles both internally.

### Parameter Requirements

**DSM Distributions:**
- All require `Mean`
- Normal, FoldedNormal, LogNormal require `StdDev`
- Weibull requires `Shape` instead of `StdDev`
- Fixed only needs `Mean` (StdDev can be 0 or omitted)

**Monte Carlo Distributions:**
- Normal and lognormal: require `Mean` and `StdDev`
- Uniform: requires `Min` and `Max`
- Triangular: requires `Min`, `Mode`, and `Max`
- All distributions can optionally use `Min`/`Max` as hard bounds

### Distribution Selection Guidelines

#### For DSM (Product Lifetimes):
```
Choose Fixed       → When: Exact lifetime known (e.g., leasing contracts)
Choose Normal      → When: Symmetric variation, large sample size
Choose FoldedNormal→ When: Symmetric variation, avoid negative lifetimes
Choose LogNormal   → When: Right-skewed (some products last much longer)
Choose Weibull     → When: Modeling wear-out or infant mortality
```

#### For Monte Carlo (Parameter Uncertainty):
```
Choose normal      → When: Measurement error, well-studied parameters
Choose uniform     → When: Only know range, no preferred value
Choose triangular  → When: Expert estimate with most likely value
Choose lognormal   → When: Ratio/rate that cannot be negative
```

---

## 4. Common Pitfalls & Best Practices

### DSM Lifetime Distributions

❌ **AVOID:**
- Normal distribution with StdDev > 80% of Mean (generates negative lifetimes)
- Weibull with Shape = 0 (undefined)
- Fixed lifetime with StdDev > 0 (will be ignored)

✅ **RECOMMENDED:**
- Use FoldedNormal instead of Normal when StdDev is large
- For safety-critical products: Use Fixed or tight distributions
- Validate that most of your products fall within Mean ± 2*StdDev

### Monte Carlo Uncertainty Distributions

❌ **AVOID:**
- unbounded normal distributions for fractions/percentages (use Min=0, Max=1)
- lognormal for parameters that can be negative
- triangular with Mode outside [Min, Max]

✅ **RECOMMENDED:**
- Always set Min/Max bounds for normal distributions on physical quantities
- Use lognormal for decay rates, growth rates, and transfer coefficients
- Triangular is excellent for incorporating expert judgment

---

## 5. Validation Warnings

BioDYM automatically validates your distribution parameters:

### DSM Warnings:
```
⚠️  WARNING: DSM Process 4, Category 'Short-lived products':
    StdDev (25.00) > 80% of Mean (30.00)
    → Large standard deviation may cause negative lifetimes in normal distribution
    → Consider reducing StdDev to max 24.00 years
```

### Monte Carlo Warnings:
```
⚠️  WARNING: Parameter 'TC_Split_A' has normal distribution without bounds
    → Consider adding Min and Max to prevent unrealistic values
```

---

## 6. Quick Reference Table

### Which Distribution Should I Use?

| Your Situation | DSM Lifetime | Monte Carlo Uncertainty |
|---------------|--------------|------------------------|
| "All items last exactly X years" | Fixed | N/A |
| "Most items last X±Y years, evenly distributed" | Normal or FoldedNormal | normal (with bounds) |
| "Some items last much longer than average" | LogNormal | lognormal |
| "I only know the min and max" | N/A | uniform |
| "I know min, max, and most likely value" | N/A | triangular |
| "Infant mortality or wear-out pattern" | Weibull | N/A |

---

## 7. Example Configurations

### Example 1: Building Stock with Long Lifetime
```
DSM_Lifetime_Type_Cat_1    = "Normal"
DSM_Lifetime_Mean_Cat_1    = 80        # years
DSM_Lifetime_StdDev_Cat_1  = 15        # years (~19% of mean, safe)
```

### Example 2: Electronics with Right-Skewed Lifetime
```
DSM_Lifetime_Type_Cat_1    = "LogNormal"
DSM_Lifetime_Mean_Cat_1    = 12        # years
DSM_Lifetime_StdDev_Cat_1  = 4         # years
```

### Example 3: Uncertain Transfer Coefficient
```
Parameter_Name       Distribution_Type    Mean    StdDev    Min     Max
TC_Recycling_Wood    normal              0.30    0.10      0.0     1.0
```

### Example 4: Expert Estimate for Future Flow
```
Parameter_Name       Distribution_Type    Min     Mode    Max
Flow_Future_2030     triangular          1000    1200    1800
```

---

## 8. Technical Implementation Details

### DSM Implementation
- **Engine:** Uses ODYM's `DynamicStockModel` class
- **Location:** `06_framework/ODYM-master_20241127/odym/modules/dynamic_stock_model.py`
- **Method:** Survival functions computed based on distribution type

### Monte Carlo Implementation
- **Engine:** Custom `sample_parameters()` function
- **Location:** `02_src/utils.py`
- **Method:** Uses NumPy's random sampling functions

---

## 9. Summary for Excel Template Info Box

**Recommended Info Box Text:**

```
╔════════════════════════════════════════════════════════════╗
║  DISTRIBUTION FUNCTIONS IN BioDYM                          ║
╠════════════════════════════════════════════════════════════╣
║  DSM LIFETIMES (Sheet 3_1_Definition_DSM):                ║
║  • Fixed: Exact lifetime (only Mean required)              ║
║  • Normal: Symmetric (Mean, StdDev < 80% of Mean)          ║
║  • FoldedNormal: Safer Normal (no negative lifetimes)      ║
║  • LogNormal: Right-skewed (Mean, StdDev)                  ║
║  • Weibull: Failure patterns (Mean, Shape)                 ║
║                                                            ║
║  MONTE CARLO UNCERTAINTY (Sheet 4_1_Uncertainty_Parameters):║
║  • normal: Symmetric uncertainty (Mean, StdDev, bounds)    ║
║  • uniform: Equal probability in range (Min, Max)          ║
║  • triangular: Expert estimate (Min, Mode, Max)            ║
║  • lognormal: Right-skewed, positive values (Mean, StdDev) ║
║                                                            ║
║  ⚠️  IMPORTANT:                                            ║
║  • DSM: StdDev should be < 80% of Mean for Normal          ║
║  • Monte Carlo: Always set Min/Max bounds for fractions    ║
║  • Case matters: DSM uses "Normal", MC uses "normal"       ║
╚════════════════════════════════════════════════════════════╝
```

---

**Document Version:** 1.0
**Last Updated:** 2025-12-05
**Maintained by:** BioDYM Development Team
