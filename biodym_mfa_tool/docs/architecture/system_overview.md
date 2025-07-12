# BioDYM System Architecture

This document illustrates the evolution of BioDYM from a notebook-based tool to a modular application.

## Legacy Architecture (Notebook-based)

The original BioDYM implementation used monolithic Jupyter notebooks with all functionality embedded in single files.

```mermaid
graph TB
    subgraph "Legacy Notebook Structure"
        A[Jupyter Notebook] --> B[Data Loading Code]
        A --> C[ODYM Setup Code]
        A --> D[Calculation Code]
        A --> E[Plotting Code]
        A --> F[Export Code]
        
        B --> G[Excel File]
        C --> H[MFA System]
        D --> H
        H --> I[Results]
        E --> I
        F --> J[Output Excel]
        
        style A fill:#ffcccc
        style B fill:#ffe6e6
        style C fill:#ffe6e6
        style D fill:#ffe6e6
        style E fill:#ffe6e6
        style F fill:#ffe6e6
    end
```

### Characteristics:
- All code in single `.ipynb` file
- Manual copy-paste for new analyses
- Direct ODYM framework calls
- Limited error handling
- No code reuse between notebooks

## Modern Architecture (Modular Tool)

The new BioDYM tool separates concerns into specialized modules with clear interfaces.

```mermaid
graph TB
    subgraph "User Interfaces"
        UI1[CLI Interface]
        UI2[Jupyter Interface]
        UI3[Python API]
    end
    
    subgraph "Core Modules"
        M1[config.py<br/>Configuration Management]
        M2[data_loader.py<br/>Excel Data Validation]
        M3[system_setup.py<br/>MFA System Builder]
        M4[mfa_engine.py<br/>Core Calculations]
        M5[plotting.py<br/>Visualizations]
        M6[utils.py<br/>Helper Functions]
    end
    
    subgraph "Calculation Engines"
        E1[solver.py<br/>MFA Solver]
        E2[dsm_model.py<br/>Dynamic Stocks]
        E3[fomp_model.py<br/>Mineralization]
    end
    
    subgraph "Data Layer"
        D1[Excel Templates]
        D2[Scenario Files]
        D3[Results Export]
    end
    
    UI1 --> M1
    UI2 --> M1
    UI3 --> M1
    
    M1 --> M2
    M2 --> D1
    M2 --> M3
    M3 --> M4
    M4 --> E1
    M4 --> E2
    M4 --> E3
    M4 --> M5
    M5 --> D3
    M1 --> D2
    
    style UI1 fill:#ccffcc
    style UI2 fill:#ccffcc
    style UI3 fill:#ccffcc
    style M1 fill:#e6f3ff
    style M2 fill:#e6f3ff
    style M3 fill:#e6f3ff
    style M4 fill:#e6f3ff
    style M5 fill:#e6f3ff
    style M6 fill:#e6f3ff
    style E1 fill:#fff0e6
    style E2 fill:#fff0e6
    style E3 fill:#fff0e6
```

### Key Improvements:
- **Separation of Concerns**: Each module has a single responsibility
- **Multiple Interfaces**: CLI, Jupyter, and programmatic access
- **Configuration Management**: Centralized settings and validation
- **Error Handling**: Comprehensive validation at each step
- **Testability**: Unit tests for each module
- **Reusability**: Shared code across all interfaces

## Data Flow Architecture

```mermaid
graph LR
    subgraph "Input Phase"
        I1[Excel Template] --> I2[Validation]
        I2 --> I3[Data Loading]
    end
    
    subgraph "Processing Phase"
        I3 --> P1[Build MFA System]
        P1 --> P2[Initialize Stocks]
        P2 --> P3[Calculate Flows]
        P3 --> P4[Update Stocks]
        P4 --> P5{More Years?}
        P5 -->|Yes| P3
        P5 -->|No| P6[Finalize Results]
    end
    
    subgraph "Analysis Phase"
        P6 --> A1[Mass Balance Check]
        P6 --> A2[Flow Analysis]
        P6 --> A3[Stock Analysis]
        P6 --> A4[Efficiency Metrics]
    end
    
    subgraph "Output Phase"
        A1 --> O1[Interactive Plots]
        A2 --> O1
        A3 --> O1
        A4 --> O1
        P6 --> O2[Excel Export]
        P6 --> O3[Scenario Save]
    end
    
    style I1 fill:#ffffcc
    style P3 fill:#ccffff
    style P4 fill:#ccffff
    style A1 fill:#ffccff
```

## Module Dependencies

```mermaid
graph BT
    U[utils.py] --> DL[data_loader.py]
    U --> S[system_setup.py]
    U --> E[mfa_engine.py]
    U --> P[plotting.py]
    
    DL --> S
    S --> E
    E --> P
    
    DSM[dsm_model.py] --> E
    FOMP[fomp_model.py] --> E
    SOL[solver.py] --> E
    
    C[config.py] --> M[main.py]
    DL --> M
    S --> M
    E --> M
    P --> M
    
    M --> CLI[main_cli.py]
    M --> JUP[BioDYM_MFA_Analysis.py]
    
    style U fill:#f0f0f0
    style C fill:#f0f0f0
```

## Technology Stack

### Core Technologies
- **Python 3.8+**: Main programming language
- **NumPy**: Numerical computations
- **Pandas**: Data manipulation
- **ODYM**: MFA framework foundation
- **Plotly**: Interactive visualizations

### Development Tools
- **pytest**: Testing framework
- **openpyxl**: Excel file handling
- **scipy**: Statistical distributions
- **matplotlib**: Additional plotting

### User Interfaces
- **Jupyter**: Interactive analysis
- **argparse**: Command-line interface
- **ipywidgets**: Interactive controls