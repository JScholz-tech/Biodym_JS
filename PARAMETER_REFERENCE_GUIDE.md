# Parameter Reference Guide
## All Expected Values and Dropdown Options

---

## **INITIAL STOCK PARAMETERS (Sheet 2_4_Initial_Stock)**

### **Cohort_Age_Distribution_Type**
**Dropdown Options (case-sensitive):**
```
uniform
exponential
```

**Required:** Only when `Stock_Configuration = "Stock_with_InitialStock_Cohort"`

**Description:**
- `uniform` → Equal amounts at each age (e.g., 10 Mg at age 0-1, 10 Mg at age 1-2, etc.)
- `exponential` → More recent items, exponentially fewer old items

---

## **DSM LIFETIME DISTRIBUTIONS (Sheet 3_1_Definition_DSM)**

### **DSM_Lifetime_Type** (or Lifetime_Type column)
**Dropdown Options (case-sensitive):**
```
Fixed
Normal
LogNormal
FoldedNormal
Weibull
```

### **Parameters for Each Distribution:**

#### **1. Fixed**
| Parameter | Required | Type | Example | Notes |
|-----------|----------|------|---------|-------|
| `DSM_Lifetime_Mean` | ✅ YES | Number (years) | 10 | Items leave at exactly this age |
| `DSM_Lifetime_StdDev` | ❌ NO | - | - | Not used for Fixed |

---

#### **2. Normal**
| Parameter | Required | Type | Example | Notes |
|-----------|----------|------|---------|-------|
| `DSM_Lifetime_Mean` | ✅ YES | Number (years) | 15 | Average lifetime |
| `DSM_Lifetime_StdDev` | ✅ YES | Number (years) | 3 | Standard deviation (variation) |

**Warning:** If `StdDev > 0.8 × Mean`, you'll get excessive variation

---

#### **3. LogNormal**
| Parameter | Required | Type | Example | Notes |
|-----------|----------|------|---------|-------|
| `DSM_Lifetime_Mean` | ✅ YES | Number (years) | 10 | Mean of the lognormal curve |
| `DSM_Lifetime_StdDev` | ✅ YES | Number (years) | 5 | StdDev of the lognormal curve |

**Note:** These are the mean/std of the lognormal distribution itself, NOT the underlying normal distribution

---

#### **4. FoldedNormal**
| Parameter | Required | Type | Example | Notes |
|-----------|----------|------|---------|-------|
| `DSM_Lifetime_Mean` | ✅ YES | Number (years) | 12 | Mean before folding |
| `DSM_Lifetime_StdDev` | ✅ YES | Number (years) | 2 | StdDev before folding |

**Note:** Similar to Normal but ensures no negative ages

---

#### **5. Weibull**
| Parameter | Required | Type | Example | Notes |
|-----------|----------|------|---------|-------|
| `DSM_Lifetime_Scale` | ✅ YES | Number (years) | 12 | Scale parameter (λ) |
| `DSM_Lifetime_Shape` | ✅ YES | Number (dimensionless) | 2.5 | Shape parameter (k) |

**Shape Parameter Interpretation:**
- `Shape < 1.0` → Infant mortality (early failures decrease over time)
- `Shape = 1.0` → Constant failure rate (exponential)
- `Shape > 1.0` → Wear-out (failures increase over time)
- `Shape = 2.0` → Moderate wear-out
- `Shape = 3.5` → Strong wear-out (Rayleigh-like)

**Relationship to Mean:**
```
Mean ≈ Scale × Γ(1 + 1/Shape)
```
For Shape=2.5 and Scale=12: Mean ≈ 10.6 years

---

## **MONTE CARLO UNCERTAINTY DISTRIBUTIONS (Sheet 4_X_Uncertainty_Parameters)**

### **Distribution Type Column**
**Dropdown Options (case-sensitive):**
```
uniform
triangular
normal
lognormal
```

### **Parameters for Each Distribution:**

#### **1. uniform**
| Parameter Column | Required | Type | Example | Notes |
|-----------------|----------|------|---------|-------|
| `min` | ✅ YES | Number | 10 | Lower bound |
| `max` | ✅ YES | Number | 30 | Upper bound |
| `mean` | ❌ NO | - | - | Not used |
| `std` | ❌ NO | - | - | Not used |
| `mode` | ❌ NO | - | - | Not used |

**Result:** All values between 10-30 equally likely

---

#### **2. triangular**
| Parameter Column | Required | Type | Example | Notes |
|-----------------|----------|------|---------|-------|
| `min` | ✅ YES | Number | 10 | Lower bound |
| `mode` | ✅ YES | Number | 15 | Most likely value (peak) |
| `max` | ✅ YES | Number | 25 | Upper bound |
| `mean` | ❌ NO | - | - | Not used |
| `std` | ❌ NO | - | - | Not used |

**Note:** Mode can be anywhere between min and max (doesn't have to be centered)

---

#### **3. normal**
| Parameter Column | Required | Type | Example | Notes |
|-----------------|----------|------|---------|-------|
| `mean` | ✅ YES | Number | 100 | Mean value |
| `std` | ✅ YES | Number | 10 | Standard deviation |
| `min` | ⚠️ Optional | Number | - | Used as lower bound if specified |
| `max` | ⚠️ Optional | Number | - | Used as upper bound if specified |
| `mode` | ❌ NO | - | - | Not used |

**Warning:** Can sample negative values if `mean < 3 × std`

**Bounds behavior (from code):**
```python
value = np.random.normal(mean, std)
if min_val is not None and value < min_val:
    value = min_val  # Clipped to minimum
if max_val is not None and value > max_val:
    value = max_val  # Clipped to maximum
```

---

#### **4. lognormal**
| Parameter Column | Required | Type | Example | Notes |
|-----------------|----------|------|---------|-------|
| `mean` | ✅ YES | Number | 100 | Mean of underlying normal |
| `std` | ✅ YES | Number | 20 | StdDev of underlying normal |
| `min` | ⚠️ Optional | Number | - | Used as lower bound if specified |
| `max` | ⚠️ Optional | Number | - | Used as upper bound if specified |
| `mode` | ❌ NO | - | - | Not used |

**Note:** Always produces positive values (cannot be negative)

---

## **VALIDATION RULES**

### **Initial Stock Sheet:**

```
IF Stock_Configuration = "Stock_with_InitialStock_Cohort" THEN
    Required:
    - Cohort_Age_Distribution_Type (must be "uniform" or "exponential")
    - Cohort_Max_Age[years] (positive number)

    Optional:
    - Cohort_Decay_Constant[years] (only used if distribution = "exponential")
      Default value if not specified: Max_Age / 3

IF Stock_Configuration = "Stock_with_InitialStock_Decay" AND Process_Logic = "Splitter" THEN
    Required:
    - Splitter_Annual_Consumption_Rate[1/year]
    - At least one Splitter_Outflow_X_FlowID and corresponding Split[%]
    - All splits must sum to 100% (1.0)

IF Stock_Configuration = "Stock_with_InitialStock_Decay" AND Process_Logic = "DSM" THEN
    Not Required:
    - Splitter_* parameters (uses DSM output_splits instead)
```

### **DSM Sheet:**

```
IF DSM_Lifetime_Type = "Weibull" THEN
    Use: DSM_Lifetime_Scale and DSM_Lifetime_Shape
    Ignore: DSM_Lifetime_Mean and DSM_Lifetime_StdDev

ELSE (Fixed, Normal, LogNormal, FoldedNormal) THEN
    Use: DSM_Lifetime_Mean
    Use: DSM_Lifetime_StdDev (except for Fixed)
    Ignore: DSM_Lifetime_Scale and DSM_Lifetime_Shape
```

### **MC Uncertainty Sheet:**

```
IF distribution = "uniform" THEN
    Required: min, max
    Ignored: mean, std, mode

IF distribution = "triangular" THEN
    Required: min, mode, max
    Ignored: mean, std

IF distribution = "normal" OR distribution = "lognormal" THEN
    Required: mean, std
    Optional: min, max (for bounds)
    Ignored: mode
```

---

## **COMMON MISTAKES TO AVOID**

❌ **Don't write:** "Weibul" → ✅ **Write:** "Weibull"
❌ **Don't write:** "Uniform" → ✅ **Write:** "uniform"
❌ **Don't write:** "lognormal" for DSM → ✅ **Write:** "LogNormal"
❌ **Don't write:** "LogNormal" for MC → ✅ **Write:** "lognormal"

**Case sensitivity matters!**
- DSM distributions: **PascalCase** (Fixed, Normal, LogNormal, FoldedNormal, Weibull)
- MC distributions: **lowercase** (uniform, triangular, normal, lognormal)
- Initial stock age: **lowercase** (uniform, exponential)

---

## **QUICK REFERENCE TABLE**

| Sheet | Parameter | Allowed Values | Required When |
|-------|-----------|----------------|---------------|
| 2_4_Initial_Stock | Cohort_Age_Distribution_Type | `uniform` or `exponential` | Stock_Config = Cohort |
| 3_1_Definition_DSM | DSM_Lifetime_Type | `Fixed`, `Normal`, `LogNormal`, `FoldedNormal`, `Weibull` | Always (for DSM) |
| 4_X_Uncertainty | distribution | `uniform`, `triangular`, `normal`, `lognormal` | Always (for MC) |

