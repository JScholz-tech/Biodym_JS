# Initial Stock Integration with Splitter & Transformer Logic

## Overview

The initial stock system has been designed to seamlessly integrate with BioDYM's existing splitter and transformation logic. This document explains how the integration works and what considerations are important.

## Process Type Compatibility

### ✅ Compatible Process Types
- **Splitter**: Can have initial stocks and outflow splits
- **Transformer**: Can have initial stocks and outflow splits  
- **DSM**: Already has stock management (initial stocks complement existing functionality)
- **FOMP**: Already has stock management (initial stocks complement existing functionality)

### ❌ Incompatible Process Types
- **Input**: No stocks (by definition - these are entry points)
- **Output**: No stocks (by definition - these are exit points)
- **Pass-through**: No stocks (by definition - these are simple connectors)

## Integration Architecture

### 1. Setup Phase (system_setup.py)
```
1. Load initial stock configurations from Excel
2. Create stock objects for processes with Stock_Configuration = "Stock"
3. Set initial stock values (first year only)
4. Create outflow flow structures (but don't set values yet)
5. Store configuration for solver use
```

### 2. Solver Phase (solver.py)
```
For each iteration:
1. Process TC-driven flows (Splitter & Transformer)
2. Update initial stock flows (NEW - ensures proper integration)
3. Process DSM flows
4. Process FOMP flows
5. Calculate stock balances
```

## Key Integration Points

### Flow Processing Order
The solver processes flows in this specific order to ensure proper integration:

1. **TC-driven flows** (Splitter & Transformer processes)
2. **Initial stock flows** (Updated each iteration)
3. **Special Models** (DSM processes)
4. **FOMP processes**
5. **Stock balance calculations**

### Initial Stock Flow Updates
Initial stock flows are updated during each solver iteration using:
```python
# In solver.py, after TC-driven flows
from . import initial_stock_engine
mfa_system = initial_stock_engine.update_initial_stock_flows_during_solver(mfa_system)
```

This ensures that:
- Initial stock outflows are properly integrated with splitter/transformer logic
- Flow values are consistent across all process types
- Mass balance is maintained throughout the system

## Example Scenarios

### Scenario 1: Splitter with Initial Stock
```
Process 1 (Splitter):
- Initial Stock: 1000 Mg material
- Annual Consumption Rate: 0.1 (10% per year)
- Outflow Split: 60% to Process 2, 40% to Process 3

Result:
- Flow F_01_02_stock: 60 Mg/year (constant)
- Flow F_01_03_stock: 40 Mg/year (constant)
- Regular splitter flows: Calculated from inflows + initial stock outflows
```

### Scenario 2: Transformer with Initial Stock
```
Process 2 (Transformer):
- Initial Stock: 500 Mg material
- Annual Consumption Rate: 0.05 (5% per year)
- Single outflow to Process 4

Result:
- Flow F_02_04_stock: 25 Mg/year (constant)
- Regular transformer flows: Calculated from inflows + initial stock outflows
```

### Scenario 3: Mixed Process Types
```
Process 1 (Splitter) → Process 2 (Transformer) → Process 3 (DSM)
- Process 1: Has initial stock, splits to Process 2 and Process 3
- Process 2: Has initial stock, transforms to Process 3
- Process 3: DSM process with stock management

Result:
- All initial stock outflows are processed first
- Regular flows are calculated including initial stock contributions
- DSM process receives both regular inflows and initial stock outflows
```

## Technical Implementation

### Flow Creation
Initial stock flows are created during setup but values are set during solver iterations:

```python
# During setup - create flow structure
flow = msc.Flow(Name=flow_name, P_Start=process_id, P_End=destination_process, Indices="t,e")
flow._initial_stock_config = {
    'initial_stock': initial_stock,
    'consumption_rate': consumption_rate,
    'split_fraction': split_fraction
}

# During solver - update values
annual_consumption = (config['initial_stock'] * 
                    config['consumption_rate'] * 
                    config['split_fraction'])
flow.Values[t, :] = annual_consumption
```

### Mass Balance Integration
Initial stock outflows are treated as additional inflows to destination processes:

```python
# In solver.py - total inflow calculation
input_flows = [f for f in mfa_system.FlowDict.values() if f.P_End == flow.P_Start]
total_inflow_vector = sum(f.Values for f in input_flows)
# This includes both regular flows AND initial stock outflows
```

## Configuration Requirements

### Process Configuration
Processes must have:
- `Stock_Configuration = "Stock"` in 2_1_Definition_Processes sheet
- `Process_Logic` in ['Splitter', 'Transformer', 'DSM', 'FOMP']

### Initial Stock Configuration
In 2_4_Initial_Stock sheet:
- `Process_ID`: Links to process definitions
- `Parameter_Name`: Type of parameter
- `Parameter_Value`: Value of parameter
- `Destination_Process`: Target process for outflow (optional)
- `Outflow_Split[%]`: Percentage split (optional)

## Validation and Error Handling

### Process Validation
- Processes with initial stocks must have `Stock_Configuration = "Stock"`
- Processes must be compatible type (not Input/Output/Pass-through)
- Initial stock parameters must be valid (material > 0, consumption rate > 0)

### Flow Validation
- Outflow splits must sum to 100% (or be normalized)
- Destination processes must exist
- Flow names must be unique

### Mass Balance Validation
- Total initial stock consumption must not exceed initial stock amount
- Stock balances must remain non-negative
- Flow conservation must be maintained

## Benefits of This Integration

1. **Seamless Integration**: Initial stocks work with existing splitter/transformer logic
2. **Flexible Configuration**: Multiple destinations and splits supported
3. **Mass Balance**: Proper conservation of mass throughout the system
4. **Iterative Solving**: Initial stock flows are updated each iteration
5. **Extensible**: Easy to add new features (time-varying rates, uncertainty, etc.)

## Future Enhancements

Potential future improvements:
- Time-varying consumption rates
- Uncertainty quantification for initial stocks
- Dynamic stock replenishment
- Integration with scenario analysis
- Advanced stock decay models

This integration ensures that initial stocks are a first-class citizen in the BioDYM system, working seamlessly with all existing process types while maintaining proper mass balance and flow conservation.
