# BioDYM Data Flow Documentation

This document explains how data flows through the BioDYM system, from Excel input to final results.

## Excel Input Structure

```mermaid
graph TD
    subgraph "Excel Template Sheets"
        E1[0_Metadata<br/>Dataset Info]
        E2[1_1_Definition_Flows<br/>System Connections]
        E3[1_2_Data_Flows<br/>Time Series Data]
        E4[2_1_Definition_Processes<br/>System Nodes]
        E5[2_3_Process_TCs<br/>Transfer Coefficients]
        E6[2_4_Process_Stock<br/>Initial Stocks]
        E7[2_5_dynamic_tcs<br/>Time-variant TCs]
        E8[3_1_Definition_DSM<br/>Dynamic Stock Parameters]
        E9[3_2_Definition_FOMP<br/>Mineralization Parameters]
        E10[4_1_Uncertainty_Parameters<br/>Monte Carlo Settings]
    end
    
    style E1 fill:#ffe6cc
    style E2 fill:#e6f3ff
    style E3 fill:#e6f3ff
    style E4 fill:#e6f3ff
    style E5 fill:#ccffcc
    style E6 fill:#ccffcc
    style E7 fill:#ccffcc
    style E8 fill:#ffccff
    style E9 fill:#ffccff
    style E10 fill:#ffffcc
```

## Data Processing Pipeline

```mermaid
flowchart LR
    subgraph "1. Data Loading"
        L1[Read Excel] --> L2{Validate Structure}
        L2 -->|Valid| L3[Parse Sheets]
        L2 -->|Invalid| L4[Error Report]
        L3 --> L5[Create Data Objects]
    end
    
    subgraph "2. System Setup"
        L5 --> S1[Define Processes]
        S1 --> S2[Define Flows]
        S2 --> S3[Set Parameters]
        S3 --> S4[Initialize Stocks]
    end
    
    subgraph "3. Time Loop"
        S4 --> T1[Year N]
        T1 --> T2[Calculate Flows]
        T2 --> T3[Apply TCs]
        T3 --> T4[Update Stocks]
        T4 --> T5[Apply DSM/FOMP]
        T5 --> T6{Last Year?}
        T6 -->|No| T1
        T6 -->|Yes| T7[Complete]
    end
    
    subgraph "4. Results"
        T7 --> R1[Flow Time Series]
        T7 --> R2[Stock Time Series]
        T7 --> R3[Mass Balance]
        T7 --> R4[Efficiency Metrics]
    end
```

## Material Elements Tracking

BioDYM tracks four material elements through the system:

```mermaid
graph TD
    M[Material Input] --> E1[material<br/>Total Mass]
    M --> E2[WC<br/>Water Content]
    M --> E3[DM<br/>Dry Matter]
    M --> E4[CC<br/>Carbon Content]
    
    E1 --> C[Calculations]
    E2 --> C
    E3 --> C
    E4 --> C
    
    C --> R1[Element-specific Results]
    C --> R2[Mass Balance per Element]
    C --> R3[Conversion Tracking]
    
    style E1 fill:#ccccff
    style E2 fill:#ccffff
    style E3 fill:#ffffcc
    style E4 fill:#ffcccc
```

## Process Types and Calculations

```mermaid
graph TB
    subgraph "Regular Process"
        RP1[Input Flow] --> RP2[Apply TC]
        RP2 --> RP3[Output Flows]
        RP2 --> RP4[Stock Change]
    end
    
    subgraph "DSM Process"
        DP1[Inflow] --> DP2[Add to Stock]
        DP2 --> DP3[Apply Lifetime]
        DP3 --> DP4[Calculate Outflow]
        DP4 --> DP5[Update Stock]
    end
    
    subgraph "FOMP Process"
        FP1[Inflow] --> FP2[Add to Pool]
        FP2 --> FP3[Apply k-rates]
        FP3 --> FP4[Mineralization]
        FP4 --> FP5[Remaining Stock]
    end
```

## Transfer Coefficient Application

```mermaid
flowchart LR
    subgraph "TC Types"
        TC1[Static TC<br/>Fixed Value]
        TC2[Dynamic TC<br/>Time-varying]
    end
    
    subgraph "Application"
        F1[Input Flow] --> A1{TC Type?}
        A1 -->|Static| A2[Apply Fixed TC]
        A1 -->|Dynamic| A3[Interpolate for Year]
        A3 --> A4[Apply Interpolated TC]
        A2 --> F2[Output Flow]
        A4 --> F2
    end
    
    TC1 -.-> A2
    TC2 -.-> A3
```

## Mass Balance Validation

```mermaid
graph TD
    subgraph "For Each Process"
        MB1[Sum Inputs] --> MB3[Calculate Balance]
        MB2[Sum Outputs] --> MB3
        MB4[Stock Change] --> MB3
        MB3 --> MB5{Balance = 0?}
        MB5 -->|Yes| MB6[✓ Valid]
        MB5 -->|No| MB7[⚠ Error]
    end
    
    MB7 --> E1[Identify Issue]
    E1 --> E2[Report Location]
    E2 --> E3[Suggest Fix]
    
    style MB6 fill:#ccffcc
    style MB7 fill:#ffcccc
```

## Data Export Structure

```mermaid
graph TD
    subgraph "Results Organization"
        R[Analysis Results] --> R1[Flows Sheet]
        R --> R2[Stocks Sheet]
        R --> R3[Summary Sheet]
        R --> R4[Validation Sheet]
        
        R1 --> D1[Year x Flow x Element]
        R2 --> D2[Year x Stock x Element]
        R3 --> D3[Key Metrics]
        R4 --> D4[Mass Balance Checks]
    end
    
    subgraph "Export Formats"
        D1 --> F1[Excel File]
        D2 --> F1
        D3 --> F1
        D4 --> F1
        
        R --> F2[Interactive HTML]
        R --> F3[Static Images]
        R --> F4[Scenario JSON]
    end
```

## Monte Carlo Data Flow

```mermaid
flowchart LR
    subgraph "Uncertainty Setup"
        U1[Parameter Distributions] --> U2[Sample Generation]
        U2 --> U3[N Iterations]
    end
    
    subgraph "Parallel Processing"
        U3 --> P1[Run 1]
        U3 --> P2[Run 2]
        U3 --> P3[Run N]
        
        P1 --> R1[Results 1]
        P2 --> R2[Results 2]
        P3 --> R3[Results N]
    end
    
    subgraph "Statistical Analysis"
        R1 --> S1[Aggregate Results]
        R2 --> S1
        R3 --> S1
        S1 --> S2[Calculate Statistics]
        S2 --> S3[Mean, Std, Percentiles]
    end
```