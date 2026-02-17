# Distribution Parameters - Detailed Guide

## Weibull Shape Parameter (DSM)

### What is the Shape parameter?

The **Shape parameter** (also called k or β) controls the behavior of the failure rate over time:

```
Shape < 1  →  Decreasing failure rate (infant mortality/early failures)
Shape = 1  →  Constant failure rate (exponential distribution)
Shape > 1  →  Increasing failure rate (wear-out failures)
```

### Expected Values

| Shape Value | Interpretation | Example Products |
|-------------|----------------|------------------|
| **0.5 - 0.8** | High infant mortality<br>Many early failures | Early prototype electronics, infant mortality phase |
| **1.0** | Constant failure rate<br>Random failures | Light bulbs, random component failures |
| **1.5 - 2.0** | Moderate wear-out<br>Useful life phase | Consumer electronics, mechanical parts |
| **2.5 - 3.5** | Strong wear-out<br>Age-dependent failure | Tires, bearings, structural components |
| **> 4.0** | Very rapid wear-out<br>Sudden end-of-life | Safety-critical components with strict replacement |

### Practical Guidelines

✅ **Common ranges:**
- Most products: Shape = 1.5 to 2.5
- Consumer electronics: Shape = 1.8 to 2.2
- Mechanical wear-out: Shape = 2.5 to 3.5
- Random failures: Shape = 1.0

⚠️ **Avoid:**
- Shape = 0 (undefined, will cause errors)
- Shape < 0.5 (extreme infant mortality, rarely realistic)
- Shape > 5.0 (unrealistically sharp end-of-life)

### Relationship with Mean and Scale

In ODYM/BioDYM, you specify:
- **Mean**: Average lifetime (years)
- **Shape**: Failure rate pattern

The system calculates the **Scale parameter** internally using:
```
Scale = Mean / Γ(1 + 1/Shape)
```
where Γ is the gamma function.

### Visual Interpretation

```
Shape = 0.5 (Infant Mortality)
Failure Rate: ████▌
Time:         ▁▁▁▁▁▁▁▁▁▁▁
              Early  →  Late

Shape = 1.0 (Random Failures)
Failure Rate: ████████████
Time:         ▁▁▁▁▁▁▁▁▁▁▁
              Constant

Shape = 2.0 (Wear-Out)
Failure Rate: ▁▁▂▃▅▇████
Time:         ▁▁▁▁▁▁▁▁▁▁▁
              Early  →  Late

Shape = 3.5 (Rapid Wear-Out)
Failure Rate: ▁▁▁▁▂▅██████
Time:         ▁▁▁▁▁▁▁▁▁▁▁
              Early  →  Late
```

---

## Triangular Mode Parameter (Monte Carlo)

### What is the Mode parameter?

The **Mode** is the **most likely value** - the peak of the triangular distribution.

```
Triangular Distribution:
      ^
      |      Mode
      |       /\
Prob. |      /  \
      |     /    \
      |    /      \
      |___/________\___
          Min      Max
```

### Expected Values

The Mode must satisfy:
```
Min ≤ Mode ≤ Max
```

**Position of Mode determines skewness:**

| Mode Position | Distribution Shape | Use Case |
|---------------|-------------------|----------|
| **Mode = Min** | Right-skewed (maximum) | Optimistic: most likely the minimum, but could be higher |
| **Mode = (Min+Max)/2** | Symmetric | Balanced: centered estimate |
| **Mode = Max** | Left-skewed (maximum) | Pessimistic: most likely the maximum, but could be lower |
| **Mode closer to Min** | Right-skewed | Expect low value, but some chance of high |
| **Mode closer to Max** | Left-skewed | Expect high value, but some chance of low |

### Practical Examples

#### Example 1: Expert Estimate for Recycling Rate
```
Min = 0.30   (Pessimistic scenario)
Mode = 0.45  (Most likely value based on current trends)
Max = 0.65   (Optimistic scenario)
→ Slightly right-skewed distribution
```

#### Example 2: Future Wood Harvest Uncertainty
```
Min = 1000 Mg   (Drought scenario)
Mode = 1500 Mg  (Normal weather, current practices)
Max = 2500 Mg   (Optimal conditions + intensification)
→ Asymmetric with longer tail to the right
```

#### Example 3: Transfer Coefficient Uncertainty
```
Min = 0.15   (Conservative estimate)
Mode = 0.20  (Best engineering estimate)
Max = 0.30   (Upper bound from experiments)
→ Right-skewed: most likely near 0.20
```

#### Example 4: Symmetric Uncertainty
```
Min = 100
Mode = 150  (exactly at midpoint)
Max = 200
→ Perfectly symmetric triangle
```

### Guidelines for Choosing Mode

✅ **Good practices:**
- **Use expert judgment**: Mode = your best estimate
- **Check skewness**: Mode position reflects your confidence
- **Closer to Min**: You're more confident in lower values
- **Closer to Max**: You're more confident in higher values
- **At midpoint**: Equal uncertainty in both directions

⚠️ **Avoid:**
- Mode < Min (will cause error)
- Mode > Max (will cause error)
- Mode exactly = Min or Max (becomes degenerate, use uniform instead)

### Default Behavior

If Mode is **not specified** in BioDYM, the system automatically calculates:
```python
Mode = (Min + Max) / 2  # Symmetric triangle
```

This is a safe default when you only know the range but have no preference for the most likely value.

### When to Use Triangular vs Other Distributions?

**Use Triangular when:**
- ✅ You have expert judgment about most likely value
- ✅ You know min/max bounds
- ✅ You want to incorporate qualitative knowledge
- ✅ You have limited data but reasonable estimates

**Use Uniform when:**
- → You only know min/max, no preferred value
- → All values in range equally plausible

**Use Normal when:**
- → You have measurement data with known mean and std
- → Distribution should be symmetric
- → You want tails beyond your bounds (use Min/Max to truncate)

---

## Complete Excel Input Examples

### DSM Weibull Configuration

```
Process_ID: 5
Category_ID: 1
DSM_Lifetime_Type_Cat_1: Weibull
DSM_Lifetime_Mean_Cat_1: 25          # Average 25 years lifetime
DSM_Lifetime_Shape_Cat_1: 2.5        # Moderate wear-out (increasing failures over time)
DSM_Category_Name_Cat_1: "Mechanical Equipment"
```

**Interpretation**: Mechanical equipment with 25-year average lifetime, showing increasing failure rate over time (wear-out pattern).

---

### Monte Carlo Triangular Configuration

```
Parameter_Name: TC_Future_Recycling_Rate
Distribution_Type: triangular
Min: 0.25            # Pessimistic: 25% recycling rate
Mode: 0.40           # Most likely: 40% based on trends
Max: 0.60            # Optimistic: 60% with policy support
```

**Interpretation**: Recycling rate most likely around 40%, with range 25%-60%, slightly right-skewed (more upside potential than downside risk).

---

## Validation in BioDYM

BioDYM automatically validates these parameters:

### Weibull Validation
```python
if Shape == 0:
    ERROR: "Weibull Shape parameter cannot be 0"

if Shape < 0:
    ERROR: "Weibull Shape parameter must be positive"
```

### Triangular Validation
```python
if not (Min <= Mode <= Max):
    ERROR: "Mode must be between Min and Max"

if Min == Max:
    WARNING: "Min equals Max, using constant value instead"
```

---

## Quick Reference Table

| Parameter | Type | Valid Range | Typical Values | Units |
|-----------|------|-------------|----------------|-------|
| Weibull **Shape** | Numeric | > 0, typically 0.5-4.0 | 1.5-2.5 (most products) | Dimensionless |
| Weibull **Mean** | Numeric | > 0 | Product-dependent | Years |
| Triangular **Mode** | Numeric | Min ≤ Mode ≤ Max | Between your bounds | Same as parameter |
| Triangular **Min** | Numeric | < Max | Product-dependent | Same as parameter |
| Triangular **Max** | Numeric | > Min | Product-dependent | Same as parameter |

---

## Summary

### Weibull Shape
- **Physical meaning**: Controls failure rate pattern over time
- **Typical values**: 1.5 to 2.5 for most products
- **Below 1**: Early failures dominate
- **Equal to 1**: Constant failure rate
- **Above 1**: Wear-out failures dominate

### Triangular Mode
- **Physical meaning**: Your best estimate / most likely value
- **Must satisfy**: Min ≤ Mode ≤ Max
- **Position matters**:
  - Near Min → Right-skewed (optimistic tail)
  - Centered → Symmetric
  - Near Max → Left-skewed (pessimistic tail)
- **Default**: (Min + Max) / 2 if not specified

---

**Last Updated:** 2025-12-05
