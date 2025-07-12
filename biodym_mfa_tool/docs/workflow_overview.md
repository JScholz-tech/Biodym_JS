# BioDYM Workflow Overview

This document describes the complete workflow for using BioDYM, from data preparation to results analysis.

## High-Level Workflow

```mermaid
graph TD
    A[Start] --> B[Prepare Excel Data]
    B --> C{Choose Interface}
    C -->|CLI| D[Command Line]
    C -->|Interactive| E[Jupyter Notebook]
    C -->|Programmatic| F[Python Script]
    
    D --> G[Run Analysis]
    E --> G
    F --> G
    
    G --> H[Validation]
    H --> I{Mass Balance OK?}
    I -->|No| J[Fix Data]
    J --> B
    I -->|Yes| K[View Results]
    
    K --> L[Interactive Plots]
    K --> M[Excel Export]
    K --> N[Save Scenario]
    
    style A fill:#e1f5e1
    style I fill:#ffe6e6
    style K fill:#e6f3ff
```

## Detailed Workflow Steps

### 1. Data Preparation Phase

```mermaid
flowchart LR
    subgraph "Data Sources"
        S1[Literature Data]
        S2[Measurements]
        S3[Expert Knowledge]
        S4[Previous Studies]
    end
    
    subgraph "Excel Template"
        E1[System Definition]
        E2[Flow Data]
        E3[Parameters]
        E4[Special Models]
    end
    
    S1 --> E1
    S2 --> E2
    S3 --> E3
    S4 --> E4
    
    E1 --> T[Template.xlsx]
    E2 --> T
    E3 --> T
    E4 --> T
```

### 2. System Definition Phase

```mermaid
graph TD
    subgraph "Define Structure"
        A1[Identify Processes] --> A2[Map Connections]
        A2 --> A3[Set Parameters]
        A3 --> A4[Configure Options]
    end
    
    subgraph "Excel Sheets"
        A1 --> B1[2_1_Definition_Processes]
        A2 --> B2[1_1_Definition_Flows]
        A3 --> B3[2_3_Process_TCs]
        A4 --> B4[3_1_DSM / 3_2_FOMP]
    end
```

### 3. Analysis Execution Phase

```mermaid
flowchart TD
    subgraph "Initialization"
        I1[Load Data] --> I2[Validate Structure]
        I2 --> I3[Build MFA System]
        I3 --> I4[Initialize Values]
    end
    
    subgraph "Calculation Loop"
        I4 --> C1[Year N]
        C1 --> C2[Calculate Flows]
        C2 --> C3[Update Stocks]
        C3 --> C4[Apply Models]
        C4 --> C5{Last Year?}
        C5 -->|No| C1
        C5 -->|Yes| C6[Finalize]
    end
    
    subgraph "Validation"
        C6 --> V1[Check Mass Balance]
        V1 --> V2[Verify Constraints]
        V2 --> V3[Generate Report]
    end
```

### 4. Results Analysis Phase

```mermaid
graph LR
    subgraph "Analysis Types"
        A[Results Data] --> B[Mass Balance]
        A --> C[Flow Analysis]
        A --> D[Stock Analysis]
        A --> E[System Metrics]
    end
    
    subgraph "Visualizations"
        B --> V1[Balance Bars]
        C --> V2[Time Series]
        D --> V3[Stock Evolution]
        E --> V4[Sankey Diagram]
    end
    
    subgraph "Outputs"
        V1 --> O1[Interactive HTML]
        V2 --> O1
        V3 --> O1
        V4 --> O1
        A --> O2[Excel Export]
        A --> O3[Scenario JSON]
    end
```

## Interface-Specific Workflows

### CLI Workflow

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant Engine
    participant Output
    
    User->>CLI: python main_cli.py --input data.xlsx
    CLI->>Engine: Load configuration
    Engine->>Engine: Validate data
    Engine->>Engine: Run calculations
    Engine->>CLI: Return results
    CLI->>Output: Generate plots
    CLI->>Output: Export Excel
    CLI->>User: Analysis complete!
```

### Jupyter Workflow

```mermaid
sequenceDiagram
    participant User
    participant Notebook
    participant Widgets
    participant Engine
    
    User->>Notebook: Run cells 1-6 (Setup)
    Notebook->>Engine: Initialize system
    User->>Notebook: Run cell 7 (Mass Balance)
    Engine->>Widgets: Display validation
    User->>Widgets: Select options
    Widgets->>Engine: Update parameters
    Engine->>Widgets: Refresh plots
    User->>Notebook: Export results
```

## Decision Points

### Choosing Analysis Type

```mermaid
graph TD
    Q1{Need Uncertainty?} -->|Yes| MC[Monte Carlo]
    Q1 -->|No| Q2{Have Product Lifetimes?}
    
    Q2 -->|Yes| DSM[Use DSM]
    Q2 -->|No| Q3{Organic Decomposition?}
    
    Q3 -->|Yes| FOMP[Use FOMP]
    Q3 -->|No| BASIC[Basic MFA]
    
    MC --> CONFIG[Configure in Excel]
    DSM --> CONFIG
    FOMP --> CONFIG
    BASIC --> CONFIG
```

### Troubleshooting Workflow

```mermaid
graph TD
    ERROR[Error Occurs] --> TYPE{Error Type?}
    
    TYPE -->|Mass Balance| MB[Check TCs]
    TYPE -->|Import Error| IE[Check Excel Format]
    TYPE -->|Calculation| CE[Check Parameters]
    
    MB --> FIX1[Adjust Coefficients]
    IE --> FIX2[Fix Column Names]
    CE --> FIX3[Validate Ranges]
    
    FIX1 --> RETRY[Run Again]
    FIX2 --> RETRY
    FIX3 --> RETRY
```

## Best Practices Workflow

```mermaid
graph LR
    subgraph "Development"
        D1[Start Simple] --> D2[Test Core]
        D2 --> D3[Add Features]
        D3 --> D4[Validate Each Step]
    end
    
    subgraph "Production"
        P1[Load Scenario] --> P2[Update Data]
        P2 --> P3[Run Analysis]
        P3 --> P4[Compare Results]
    end
    
    subgraph "Maintenance"
        M1[Version Control] --> M2[Document Changes]
        M2 --> M3[Archive Results]
        M3 --> M4[Share Templates]
    end
```

## Scenario Management Workflow

```mermaid
stateDiagram-v2
    [*] --> BaseCase: Create Initial
    BaseCase --> Variations: Modify Parameters
    Variations --> Comparison: Run Multiple
    Comparison --> Selection: Choose Best
    Selection --> Documentation: Document Results
    Documentation --> [*]
    
    Variations --> BaseCase: Revert Changes
    Comparison --> Variations: Adjust Parameters
```

## Integration Workflow

```mermaid
graph TD
    subgraph "Input Sources"
        IS1[Lab Data]
        IS2[Field Measurements]
        IS3[Literature]
    end
    
    subgraph "BioDYM"
        B1[Data Import]
        B2[Analysis Engine]
        B3[Results Export]
    end
    
    subgraph "Downstream"
        DS1[Reports]
        DS2[Publications]
        DS3[Decision Support]
    end
    
    IS1 --> B1
    IS2 --> B1
    IS3 --> B1
    
    B1 --> B2
    B2 --> B3
    
    B3 --> DS1
    B3 --> DS2
    B3 --> DS3
```

## Recommended Workflow Sequence

1. **Planning Phase**
   - Define system boundaries
   - Identify data sources
   - Sketch process flow

2. **Setup Phase**
   - Create Excel template
   - Input base data
   - Define parameters

3. **Testing Phase**
   - Run with few years
   - Check mass balance
   - Validate results

4. **Analysis Phase**
   - Full time horizon
   - Sensitivity analysis
   - Scenario comparison

5. **Reporting Phase**
   - Export results
   - Create visualizations
   - Document findings

## Quick Reference

### Daily Workflow
```bash
# Morning: Load yesterday's work
python src/main_cli.py --input current_work.xlsx --scenario yesterday

# Work: Test new parameters
python src/main_cli.py --input test_params.xlsx --validate-only

# Afternoon: Run full analysis
python src/main_cli.py --input final_params.xlsx --monte-carlo

# Evening: Save progress
python src/main_cli.py --save-scenario today
```

### Weekly Workflow
- Monday: Data collection and cleaning
- Tuesday: System setup and validation
- Wednesday: Run base scenarios
- Thursday: Sensitivity analysis
- Friday: Results compilation and reporting

---

For detailed instructions on any workflow step, see:
- [Quick Start Tutorial](QUICKSTART.md)
- [Excel Template Guide](EXCEL_TEMPLATE_GUIDE.md)
- [Troubleshooting](TROUBLESHOOTING.md)