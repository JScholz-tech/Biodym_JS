# BioDYM Methodology Chapter - PhD Thesis Draft

**Title**: Multi-Dimensional Material Flow Analysis Framework for Bio-based Systems
**Author**: Johannes Scholz
**Institution**: [Your University]
**Date**: November 2025
**Status**: Draft for review

---

## Chapter X: Methodology - BioDYM Framework Architecture

### X.1 Introduction to Material Flow Analysis and ODYM

Material Flow Analysis (MFA) is a systematic assessment of the flows and stocks of materials within a system defined in space and time (Brunner & Rechberger, 2004). The method is based on the principle of mass conservation, which states that matter can neither be created nor destroyed within the system boundaries, enabling the quantification and tracking of material pathways through production, consumption, and waste management processes.

The Open Dynamic Material Systems Model (ODYM) framework, developed by Pauliuk and Heeren (2020), provides a standardized, open-source implementation of dynamic MFA suitable for industrial ecology research. ODYM defines a multi-dimensional array structure for representing material flows and stocks across multiple classification dimensions (aspects), including time, region, material, product, element, and process type. This dimensional structure enables comprehensive tracking of material transformations and movements through complex socio-economic systems.

While ODYM's full multi-dimensional structure (typically 5-6 dimensions) provides maximum granularity for complex multi-regional, multi-product studies, the framework's flexibility allows researchers to adapt the dimensional structure to match specific research requirements and data availability (Heeren & Hellweg, 2019). This methodological chapter presents BioDYM (Bio-based Dynamic Material Flow Model), an ODYM-compliant framework optimized for bio-based material flow analysis with specific focus on biomass cascading and multi-regional studies.

### X.2 BioDYM Framework Design Philosophy

#### X.2.1 Design Requirements

The development of BioDYM was guided by five primary requirements:

1. **ODYM Compliance**: Full adherence to ODYM framework standards to ensure scientific rigor, reproducibility, and compatibility with established MFA methodology
2. **Biomass-Specific Features**: Support for biomass composition tracking (water content, dry matter, carbon content) and organic matter decomposition processes
3. **Cascading Analysis**: Capability to track material flows through multiple cascading stages and life cycle phases
4. **Multi-Regional Support**: Enable comparative analysis across multiple geographic regions
5. **Practical Usability**: Balance between model granularity and data input requirements, computational efficiency, and result interpretability

#### X.2.2 Dimensional Structure Selection

BioDYM implements a three-dimensional array structure comprising Time (t), Region (r), and Element (e) dimensions, representing a pragmatic simplification of the standard ODYM structure while maintaining full framework compliance. This design decision is justified by the following considerations:

**Element Hierarchy Approach**: Unlike conventional ODYM implementations that typically employ separate Good (g) and Material (m) dimensions for product categories and material types, BioDYM utilizes a hierarchical element composition system. Biomass composition is inherently hierarchical (e.g., carbon content is a fixed proportion of dry matter, which in turn constitutes the non-water fraction of total material mass). This physical reality is more naturally represented through element hierarchy relationships than through additional array dimensions.

**Research Scope Appropriateness**: For biomass MFA studies, the research questions typically focus on (1) temporal evolution of biomass stocks and flows, (2) spatial distribution and regional differences, and (3) material composition and quality. The 3D structure (t,r,e) directly addresses these three analytical foci without introducing unnecessary complexity.

**Data Availability Constraints**: Biomass flow data are typically available disaggregated by time, location, and composition, but detailed product-level or material-type disaggregation (as would be required for full Good/Material dimensions) is often unavailable or inconsistent across sources.

**Computational Efficiency**: The 3D structure enables efficient computation for Monte Carlo uncertainty analysis and scenario comparison, which are essential components of robust MFA studies but can become computationally prohibitive with higher-dimensional structures.

This dimensional choice aligns with the ODYM framework's principle of adapting the model structure to the research context while maintaining methodological consistency (Pauliuk & Heeren, 2020).

### X.3 Mathematical Formulation

#### X.3.1 System Definition and Scope

A BioDYM system is defined as an ODYM-compliant MFA system $\mathcal{S}$ characterized by:

$$
\mathcal{S} = \{P, F, S, T, R, E, \Theta\}
$$

where:
- $P = \{p_1, p_2, ..., p_n\}$ is the set of $n$ processes
- $F = \{f_{ij}\}$ is the set of flows between processes $p_i$ and $p_j$
- $S = \{s_i\}$ is the set of stocks within processes
- $T = \{t_1, t_2, ..., t_T\}$ is the set of time periods
- $R = \{r_1, r_2, ..., r_R\}$ is the set of regions
- $E = \{e_1, e_2, ..., e_E\}$ is the set of elements (composition components)
- $\Theta$ is the set of system parameters (transfer coefficients, lifetimes, decay rates)

#### X.3.2 Dimensional Index Structure

Following ODYM conventions, the model employs an IndexTable defining aspect classifications:

| Aspect | Dimension | IndexLetter | Classification |
|--------|-----------|-------------|----------------|
| Time | Time | t | $T$ time periods |
| Region | Region | r | $R$ geographic regions |
| Element | Element | e | $E$ composition elements |

All flow and stock arrays are indexed according to this structure:

$$
f_{ij}[t, r, e] \in \mathbb{R}^{T \times R \times E}_{\geq 0}
$$

$$
s_i[t, r, e] \in \mathbb{R}^{T \times R \times E}_{\geq 0}
$$

where $f_{ij}[t, r, e]$ represents the flow from process $p_i$ to process $p_j$ at time $t$, in region $r$, for element $e$ (in mass units, typically Mg).

#### X.3.3 Mass Balance Equation

The fundamental mass balance equation is applied per process, per time step, per region, and per element:

$$
s_i[t+1, r, e] = s_i[t, r, e] + \sum_{j} f_{ji}[t, r, e] - \sum_{k} f_{ik}[t, r, e]
$$

where:
- $\sum_{j} f_{ji}[t, r, e]$ represents total inflows to process $p_i$
- $\sum_{k} f_{ik}[t, r, e]$ represents total outflows from process $p_i$
- The equation must hold independently for each region $r$ and element $e$

This formulation ensures that mass balance is maintained at the most granular level (per region, per element) and that regional systems are treated as separate but coupled subsystems.

#### X.3.4 Element Hierarchy and Composition

BioDYM implements a hierarchical element composition system where certain elements are defined as proportions of others:

$$
e_{\text{child}}[t, r] = \alpha_{t,r} \cdot e_{\text{parent}}[t, r]
$$

where $\alpha_{t,r} \in [0,1]$ is the composition coefficient, which may vary by time and region.

**Example: Biomass Composition Hierarchy**
```
material (total mass)
├── WC (water content) = α_WC × material
└── DM (dry matter) = (1 - α_WC) × material
    └── CC (carbon content) = α_CC × DM
```

This formulation ensures:
1. Physical consistency: $e_{\text{child}} \leq e_{\text{parent}}$ always
2. Conservation: Sum of child elements equals parent element where applicable
3. Flexibility: Composition coefficients can vary across time, regions, and processes

Mathematically, for biomass composition:

$$
\text{DM}[t, r] = (1 - \alpha_{\text{WC}}[t,r]) \cdot \text{material}[t, r]
$$

$$
\text{CC}[t, r] = \alpha_{\text{CC|DM}}[t,r] \cdot \text{DM}[t, r]
$$

where $\alpha_{\text{WC}}$ is the water content fraction and $\alpha_{\text{CC|DM}}$ is the carbon content as a fraction of dry matter.

### X.4 Process Types and Calculation Logic

BioDYM implements four primary process types, each with distinct calculation logic:

#### X.4.1 Transfer Coefficient (TC) Processes

TC processes (Splitters and Transformers) distribute incoming flows according to fixed or time-varying transfer coefficients:

$$
f_{ik}[t, r, e] = \text{TC}_{ij \to k}[t, r, e] \cdot f_{ji}[t, r, e]
$$

where $\text{TC}_{ij \to k}[t, r, e]$ is the transfer coefficient from inflow $j$ to outflow $k$ at process $i$.

**Conservation constraint**:
$$
\sum_k \text{TC}_{ij \to k}[t, r, e] = 1 \quad \forall j, t, r, e
$$

**Splitters**: Distribute material without composition change ($\text{TC}$ same for all elements)
**Transformers**: May modify composition ($\text{TC}$ can vary by element)

#### X.4.2 Dynamic Stock Model (DSM) Processes

DSM processes model product stocks with finite lifetimes using age-cohort tracking (Müller, 2006):

$$
s_i[t, r, e] = \sum_{\tau=0}^{t} I[t-\tau, r, e] \cdot \text{SF}(\tau)
$$

where:
- $I[t-\tau, r, e]$ is the inflow cohort from year $t-\tau$
- $\text{SF}(\tau)$ is the survival function describing the probability that material persists for $\tau$ years
- Commonly modeled with Weibull distribution: $\text{SF}(\tau) = \exp\left[-\left(\frac{\tau}{\lambda}\right)^\kappa\right]$

The outflow at time $t$ is:

$$
O[t, r, e] = \sum_{\tau=1}^{t} I[t-\tau, r, e] \cdot \left[\text{SF}(\tau-1) - \text{SF}(\tau)\right]
$$

This formulation is applied independently per region and element, enabling region-specific lifetime distributions and composition-dependent degradation patterns.

#### X.4.3 First-Order Mineralization Process (FOMP)

FOMP processes model organic matter decomposition in landfills, composting, or soil applications:

$$
\frac{d s_{\text{organic}}[t, r]}{dt} = I_{\text{organic}}[t, r] - k \cdot s_{\text{organic}}[t, r]
$$

where $k$ is the first-order decay rate constant (yr$^{-1}$).

For discrete time steps:

$$
s_{\text{organic}}[t+1, r] = s_{\text{organic}}[t, r] \cdot (1 - k) + I_{\text{organic}}[t, r]
$$

**Two-pool extension** for labile and recalcitrant fractions:

$$
s_{\text{total}}[t, r] = s_{\text{labile}}[t, r] + s_{\text{recalcitrant}}[t, r]
$$

$$
s_{\text{labile}}[t+1, r] = s_{\text{labile}}[t, r] \cdot (1 - k_L) + f_L \cdot I[t, r]
$$

$$
s_{\text{recalcitrant}}[t+1, r] = s_{\text{recalcitrant}}[t, r] \cdot (1 - k_R) + (1-f_L) \cdot I[t, r]
$$

where $k_L$ and $k_R$ are decay rates for labile and recalcitrant pools, and $f_L$ is the labile fraction.

This formulation is applied per region and per relevant element (typically carbon content).

#### X.4.4 Pass-Through Processes

Pass-through processes serve as system boundary nodes or aggregation points:

$$
\sum_k f_{ik}[t, r, e] = \sum_j f_{ji}[t, r, e] \quad \forall t, r, e
$$

No stock accumulation occurs, and composition is preserved.

### X.5 Process Metadata Classification System

To enable cascading analysis and life cycle assessment integration without increasing array dimensionality, BioDYM employs a process metadata classification system. Each process $p_i$ is assigned metadata attributes:

$$
\mathcal{M}(p_i) = \{\text{CL}_i, \text{LP}_i, \text{MQ}_i\}
$$

where:
- $\text{CL}_i \in \{0, 1, 2, 3, 4\}$ is the cascading level
- $\text{LP}_i \in \{\text{Extraction, Production, Use, Collection, Treatment, EoL}\}$ is the life phase
- $\text{MQ}_i \in \{\text{Virgin, Secondary, Tertiary, Quaternary, Energy}\}$ is the material quality descriptor

**Cascading Level Classification**:
- **Level 0 (Primary)**: First use of virgin biomass (e.g., food production, timber construction)
- **Level 1 (Secondary)**: First reuse or recycling (e.g., wood reuse, animal feed from food residues)
- **Level 2 (Tertiary)**: Second recycling cascade (e.g., particle board from recycled wood)
- **Level 3 (Quaternary)**: Third+ recycling cascade (e.g., soil amendment from composted particle board)
- **Level 4 (Energy)**: Final use as energy carrier (combustion, biogas)

This classification enables post-processing analysis such as:

$$
\text{Stock}_{\text{CL}=k}[t, r] = \sum_{i: \text{CL}_i = k} \sum_e s_i[t, r, e]
$$

**Cascading efficiency metric**:

$$
\eta_{\text{cascade}}[t, r] = \frac{\sum_{k=1}^{3} \text{Stock}_{\text{CL}=k}[t, r]}{\text{Stock}_{\text{CL}=0}[t, r]}
$$

This approach maintains the computational efficiency of the 3D structure while enabling comprehensive cascading and life cycle analysis.

### X.6 Regional Coupling and Trade

Regional systems in BioDYM are coupled through inter-regional trade flows. A flow $f_{ij}$ with origin region $r_o$ and destination region $r_d$ is represented as:

$$
f_{ij}[t, r, e] =
\begin{cases}
Q[t, e] & \text{if } r = r_o \text{ (outflow from origin)} \\
Q[t, e] & \text{if } r = r_d \text{ (inflow to destination)} \\
0 & \text{otherwise}
\end{cases}
$$

**Conservation constraint** for inter-regional flows:

$$
\sum_r f_{\text{export}}[t, r, e] = \sum_r f_{\text{import}}[t, r, e]
$$

This ensures that material leaving one region arrives in another, maintaining global mass balance.

### X.7 Solver Algorithm and Convergence

BioDYM employs an iterative solver algorithm to handle process interdependencies and circular flows:

**Algorithm 1: BioDYM Iterative Solver**
```
Input: Initial flows F⁰, stocks S⁰, parameters Θ, convergence threshold ε
Output: Converged flows F*, stocks S*

1. Initialize iteration counter: iter = 0
2. Initialize residual: Δ = ∞
3. While Δ > ε and iter < max_iterations:
   a. For each process pᵢ in calculation order:
      i.   Calculate inflows: Σⱼ fⱼᵢ[t,r,e]
      ii.  Apply process-specific logic (TC/DSM/FOMP)
      iii. Calculate outflows: fᵢₖ[t,r,e]
      iv.  Update stocks: sᵢ[t,r,e]
   b. Check mass balance per process, per region, per element
   c. Calculate residual: Δ = max|Inflow - Outflow - ΔStock|
   d. iter = iter + 1
4. Return F*, S*
```

**Convergence criterion**:

$$
\max_{i,t,r,e} \left| \sum_j f_{ji}[t,r,e] - \sum_k f_{ik}[t,r,e] - (s_i[t+1,r,e] - s_i[t,r,e]) \right| < \varepsilon
$$

with $\varepsilon = 10^{-10}$ (mass units).

This ensures that mass balance is satisfied to numerical precision across all processes, regions, and elements.

### X.8 ODYM Compliance and Framework Integration

BioDYM fully implements ODYM framework standards through the following mechanisms:

#### X.8.1 Core ODYM Components

**IndexTable Structure**: BioDYM constructs an ODYM-compliant IndexTable defining all model dimensions:

```python
index_table = pd.DataFrame({
    'Aspect': ['Time', 'Region', 'Element'],
    'Description': ['Model aspect "time"', 'Model aspect "region"',
                    'Model aspect "Element"'],
    'Dimension': ['Time', 'Region', 'Element'],
    'Classification': [time_classification, region_classification,
                       element_classification],
    'IndexLetter': ['t', 'r', 'e']
})
```

**Classification Objects**: Each dimension is defined using ODYM Classification objects:

```python
time_classification = msc.Classification(
    Name='Time',
    Dimension='Time',
    ID=1,
    Items=[2025, 2026, ..., 2050]
)

region_classification = msc.Classification(
    Name='Region',
    Dimension='Region',
    ID=2,
    Items=['Germany', 'France', 'Poland', ...]
)

element_classification = msc.Classification(
    Name='Elements',
    Dimension='Element',
    ID=3,
    Items=['material', 'WC', 'DM', 'CC']
)
```

**MFAsystem Object**: The entire system is initialized as an ODYM MFAsystem:

```python
mfa_system = msc.MFAsystem(
    Name='BioDYM_System',
    Geogr_Scope='Multi_Regional',
    Unit='Mg',
    ProcessList=processes,
    FlowDict=flows,
    StockDict=stocks,
    ParameterDict=parameters,
    Time_Start=start_year,
    Time_End=end_year,
    IndexTable=index_table,
    Elements=element_items
)
```

#### X.8.2 ODYM Initialization Methods

BioDYM employs ODYM's standard initialization methods:

**Flow Initialization**:
```python
mfa_system.Initialize_FlowValues()
```
Creates zero-filled arrays for all flows with shape $(T, R, E)$ based on IndexTable.

**Stock Initialization**:
```python
mfa_system.Initialize_StockValues()
```
Creates zero-filled arrays for all stocks with shape $(T, R, E)$.

**Parameter Initialization**:
```python
mfa_system.Initialize_ParameterValues()
```
Initializes parameter arrays with specified Indices string (e.g., "t,r,e" or "" for scalars).

#### X.8.3 Validation and Consistency Checks

BioDYM utilizes ODYM's built-in validation methods:

**IndexTable Validation**:
```python
mfa_system.IndexTableCheck()
```
Verifies consistency of IndexTable structure, classification objects, and dimension definitions.

**Mass Balance Consistency**:
```python
mfa_system.Consistency_Check()
```
Validates mass balance across all processes, ensuring:

$$
\left| \sum_j f_{ji}[t,r,e] - \sum_k f_{ik}[t,r,e] - \Delta s_i[t,r,e] \right| < \varepsilon \quad \forall i,t,r,e
$$

#### X.8.4 Dimensional Index Convention

BioDYM strictly follows ODYM's Indices string convention:

- **Flows/Stocks**: `Indices = "t,r,e"` creates arrays of shape $(T, R, E)$
- **Time-varying parameters**: `Indices = "t"` creates arrays of shape $(T,)$
- **Scalar parameters**: `Indices = ""` creates scalar values (not `None`)

**Critical compliance note**: ODYM requires `Indices=""` (empty string) for scalar parameters, not `Indices=None`, to prevent AttributeError in `Initialize_ParameterValues()` method.

Example:
```python
# CORRECT - ODYM compliant
lifetime_param = msc.Parameter(
    Name='product_lifetime',
    Indices='',  # Empty string for scalar
    Values=15.0
)

# INCORRECT - Causes crash
lifetime_param = msc.Parameter(
    Name='product_lifetime',
    Indices=None,  # Will raise AttributeError
    Values=15.0
)
```

### X.9 Comparison with Standard ODYM Implementations

Table X.1 compares BioDYM's dimensional structure with standard ODYM implementations:

| **Aspect** | **Standard ODYM** | **BioDYM** | **Justification** |
|------------|-------------------|------------|-------------------|
| Time (t) | ✓ Required | ✓ Required | Temporal dynamics essential for MFA |
| Region (r) | ✓ Common | ✓ Required | Multi-regional analysis capability |
| Good (g) | ✓ Common | ✗ Not used | Covered by element hierarchy |
| Material (m) | ✓ Common | ✗ Not used | Covered by element hierarchy |
| Element (e) | ✓ Required | ✓ Required | Composition tracking |
| Process (p) | ○ Optional | ○ Metadata only | Classification without dimension |
| Cohort (c) | ○ DSM internal | ○ DSM internal | Age-cohort in DSM processes |

**Legend**: ✓ = Used as array dimension, ✗ = Not used, ○ = Special handling

**Key innovation**: BioDYM's element hierarchy system (Section X.3.4) eliminates the need for separate Good and Material dimensions while maintaining the ability to track product categories and material types through hierarchical composition relationships. This represents a methodologically valid simplification that:

1. Reduces computational complexity from $O(T \times R \times G \times M \times E \times P)$ to $O(T \times R \times E)$
2. Maintains mass balance consistency at the most granular level (per element)
3. Aligns with physical reality of biomass composition
4. Simplifies data input requirements while preserving analytical capability

### X.10 Uncertainty Quantification

BioDYM implements Monte Carlo uncertainty analysis following ODYM conventions. For parameters with uncertainty, probability distributions are defined:

$$
\theta_k \sim \mathcal{D}(\mu_k, \sigma_k)
$$

where $\mathcal{D}$ is the distribution type (normal, lognormal, triangular, uniform), $\mu_k$ is the mean, and $\sigma_k$ is the standard deviation or uncertainty range.

**Monte Carlo Algorithm**:
```
For each simulation run n = 1 to N:
    1. Sample parameter values: θ⁽ⁿ⁾ ~ D(μ, σ)
    2. Run solver with θ⁽ⁿ⁾ to obtain F⁽ⁿ⁾, S⁽ⁿ⁾
    3. Store results

Calculate statistics:
    - Mean: μ_result = (1/N) Σⁿ result⁽ⁿ⁾
    - Standard deviation: σ_result
    - Percentiles: P₅, P₅₀, P₉₅
    - Sensitivity: Sobol indices
```

Results are reported as:

$$
\text{Result}[t, r, e] = \mu_{\text{result}}[t,r,e] \pm \sigma_{\text{result}}[t,r,e]
$$

with confidence intervals: $[\text{P}_5[t,r,e], \text{P}_{95}[t,r,e]]$

### X.11 Model Validation Strategy

BioDYM validation follows a multi-level approach:

#### X.11.1 Internal Consistency Validation

**Mass Balance Verification**:
$$
\sum_{t,r,e} \left| \text{Inflow}[t,r,e] - \text{Outflow}[t,r,e] - \Delta \text{Stock}[t,r,e] \right| < N \cdot \varepsilon
$$

where $N$ is the total number of processes and $\varepsilon = 10^{-10}$ Mg.

**Element Hierarchy Consistency**:
$$
\text{CC}[t,r] \leq \text{DM}[t,r] \leq \text{material}[t,r] \quad \forall t, r
$$

**Regional Conservation**:
$$
\sum_r \text{Stock}[t,r,e] + \sum_r \text{Export}[t,r,e] = \sum_r \text{Production}[t,r,e] + \sum_r \text{Import}[t,r,e]
$$

#### X.11.2 Comparison with Reference Data

Where available, model outputs are compared against:
1. Statistical data (production, consumption, trade)
2. Life cycle inventory databases (ecoinvent, GaBi)
3. Published MFA studies for similar systems
4. Expert estimates and stakeholder validation

#### X.11.3 Sensitivity Analysis

Sensitivity analysis identifies influential parameters:

$$
S_{i,j} = \frac{\partial Y_j}{\partial \theta_i} \cdot \frac{\theta_i}{Y_j}
$$

where $S_{i,j}$ is the sensitivity of output $Y_j$ to parameter $\theta_i$.

Sobol indices quantify variance contributions:

$$
S_i^{\text{total}} = \frac{\text{Var}[E[Y|\theta_{\sim i}]]}{\text{Var}[Y]}
$$

### X.12 Software Implementation

BioDYM is implemented in Python 3.10+ using the following core dependencies:

- **ODYM Framework**: Provides MFAsystem, Flow, Stock, Process, Parameter classes
- **NumPy** (≥1.24): Multi-dimensional array operations
- **Pandas** (≥2.0): Data loading and manipulation
- **Plotly** (≥5.14): Interactive visualization
- **Scipy** (≥1.10): Statistical distributions and optimization

**Code structure**:
```
bioDYM/
├── config.py              # Configuration loading
├── system_setup.py        # Model initialization (ODYM)
├── data_loader.py         # Excel data loading
├── engine/
│   ├── solver.py          # Iterative solver
│   ├── dsm_model.py       # Dynamic Stock Model
│   ├── fomp_model.py      # First-Order Mineralization
│   └── initial_stock_engine.py
├── plotting/              # Visualization modules
└── utils.py               # Export and utility functions
```

**ODYM integration**:
```python
import sys
sys.path.insert(0, 'path/to/ODYM/modules')
import ODYM_Classes as msc
```

All BioDYM components interact with ODYM objects (MFAsystem, Flow, Stock, Process, Parameter) following framework conventions.

### X.13 Limitations and Future Extensions

#### X.13.1 Current Limitations

1. **Spatial Resolution**: Regions are treated as homogeneous units; sub-regional spatial variation is not captured
2. **Process Detail**: Technology-specific processes within regions are aggregated; detailed technology comparison requires process disaggregation
3. **Trade Modeling**: Inter-regional trade is represented as direct flows; trade networks and logistics are simplified
4. **Element Set**: Currently optimized for biomass composition; adaptation to other material systems requires element redefinition

#### X.13.2 Potential Extensions

The 3D array structure with ODYM compliance enables future extensions:

**Addition of Good Dimension** (3D → 4D):
$$
f_{ij}[t, r, g, e] \in \mathbb{R}^{T \times R \times G \times E}
$$

Enables explicit product-level tracking if data availability improves and research questions require this granularity.

**Material Dimension** (4D → 5D):
$$
f_{ij}[t, r, g, m, e] \in \mathbb{R}^{T \times R \times G \times M \times E}
$$

Allows simultaneous tracking of multiple biomass feedstock types (wheat, corn, wood, etc.) through the same system structure.

**Process Dimension** (5D → 6D):
$$
f_{ij}[t, r, g, m, e, p] \in \mathbb{R}^{T \times R \times G \times M \times E \times P}
$$

Converts process metadata into array dimension if needed for specific analysis requirements.

The modular architecture and ODYM compliance ensure that dimensional extensions can be implemented without fundamental restructuring of the solver, validation, or visualization components.

### X.14 Conclusion

BioDYM represents an ODYM-compliant implementation optimized for bio-based material flow analysis. The framework's key contributions are:

1. **Element Hierarchy Innovation**: Hierarchical composition tracking eliminates need for separate Good/Material dimensions while maintaining analytical capability
2. **Multi-Regional Structure**: 3D array structure enables comparative regional analysis with manageable computational requirements
3. **Process Metadata System**: Cascading level and life phase classification without dimensional complexity
4. **Full ODYM Compliance**: Adherence to framework standards ensures scientific rigor and reproducibility
5. **Practical Usability**: Balance between model granularity and data requirements appropriate for biomass MFA research

This methodological approach provides a scientifically defensible foundation for the case study analyses presented in subsequent chapters, enabling robust quantification of biomass flows, stocks, and cascading patterns across multiple regions and time periods.

---

## References

Brunner, P. H., & Rechberger, H. (2004). *Practical Handbook of Material Flow Analysis*. CRC Press.

Heeren, N., & Hellweg, S. (2019). Tracking Construction Material over Space and Time: Prospective and Geo-referenced Modeling of Building Stocks and Construction Material Flows. *Journal of Industrial Ecology*, 23(1), 253-267.

Müller, D. B. (2006). Stock dynamics for forecasting material flows—Case study for housing in The Netherlands. *Ecological Economics*, 59(1), 142-156.

Pauliuk, S., & Heeren, N. (2020). ODYM—An open software framework for studying dynamic material systems: Principles, implementation, and data structures. *Journal of Industrial Ecology*, 24(3), 446-458.

---

**End of Methodology Chapter Draft**

---

## Appendix A: Notation and Symbols

| Symbol | Description | Unit |
|--------|-------------|------|
| $\mathcal{S}$ | MFA system | - |
| $P$ | Set of processes | - |
| $p_i$ | Process $i$ | - |
| $F$ | Set of flows | - |
| $f_{ij}[t,r,e]$ | Flow from process $i$ to $j$ at time $t$, region $r$, element $e$ | Mg |
| $S$ | Set of stocks | - |
| $s_i[t,r,e]$ | Stock in process $i$ at time $t$, region $r$, element $e$ | Mg |
| $T$ | Set of time periods | yr |
| $t$ | Time index | yr |
| $R$ | Set of regions | - |
| $r$ | Region index | - |
| $E$ | Set of elements | - |
| $e$ | Element index | - |
| $\Theta$ | Set of parameters | - |
| $\text{TC}$ | Transfer coefficient | - |
| $\text{SF}(\tau)$ | Survival function (DSM) | - |
| $\tau$ | Age/cohort | yr |
| $\lambda$ | Lifetime parameter | yr |
| $\kappa$ | Shape parameter (Weibull) | - |
| $k$ | Decay rate constant (FOMP) | yr$^{-1}$ |
| $\alpha$ | Composition coefficient | - |
| $\text{CL}$ | Cascading level | - |
| $\text{LP}$ | Life phase | - |
| $\varepsilon$ | Convergence threshold | Mg |
| $\eta$ | Efficiency | - |

---

**Document Status**: Draft for PhD thesis methodology chapter
**Review Status**: Requires supervisor and committee review
**ODYM Compliance**: Verified against ODYM framework standards (v1.0)
**Next Steps**: Integrate feedback, add case study-specific details in implementation section
