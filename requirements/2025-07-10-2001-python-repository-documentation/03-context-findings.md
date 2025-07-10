# Context Findings

## Codebase Structure Analysis

### Two Parallel Implementations
1. **Legacy (Notebook-based)**: Monolithic Jupyter notebooks in studies/ and basic_examples/
2. **Modern (Modular)**: Well-structured Python modules in biodym_mfa_tool/src/

### Key Files Identified

#### Documentation Files
- `README.md` - Original documentation (notebook-focused)
- `README2.0.md` - Excel template documentation
- `biodym_mfa_tool/README.md` - New modular tool documentation
- `docs/workflow_diagram.pdf` - Visual workflow (potentially outdated)

#### Core Implementation
- `biodym_mfa_tool/src/main.py` - Main analysis engine
- `biodym_mfa_tool/src/main_cli.py` - CLI interface
- `biodym_mfa_tool/src/data_loader.py` - Excel data handling
- `biodym_mfa_tool/src/plotting.py` - Visualization functions

#### User Entry Points
- `biodym_mfa_tool/BioDYM_MFA_Analysis.py` - Jupyter notebook interface
- `biodym_mfa_tool/generate_excel_template.py` - Template generator
- Excel templates in `data/01_input/`

### Documentation Issues Found

1. **Fragmentation**: Three separate README files with overlapping content
2. **Inconsistency**: Old workflow still documented alongside new approach
3. **Missing Elements**:
   - No unified user guide
   - Limited troubleshooting section
   - No visual architecture diagram for new structure
   - Incomplete API documentation

4. **Stale Content**:
   - Workflow diagrams don't reflect modular architecture
   - Some examples reference old notebook approach
   - Installation instructions incomplete

### User Interaction Patterns

#### Primary Workflow (Domain Experts)
1. Generate/modify Excel template
2. Run analysis via CLI or Jupyter
3. Review mass balance validation
4. Explore visualizations
5. Export results to Excel

#### Key Excel Sheets Used
- `0_Metadata` - Dataset information
- `1_1_Definition_Flows` - System connections
- `1_2_Data_Flows` - Time series data
- `2_1_Definition_Processes` - System nodes
- `2_3_Process_TCs` - Transfer coefficients
- `3_1_Definition_DSM` - Dynamic stock parameters
- `3_2_Definition_FOMP` - Mineralization parameters

### Technical Constraints
- Python-based with heavy NumPy/Pandas usage
- ODYM framework dependency
- Excel as primary data interface
- Plotly for interactive visualizations
- Monte Carlo for uncertainty analysis

### Similar Features Analyzed
- ODYM examples for MFA structure
- Standard Jupyter notebook patterns
- Excel-based configuration systems
- Scientific visualization approaches

### Integration Points
- ODYM framework (external dependency)
- Excel I/O via openpyxl
- Plotly for web-based charts
- Jupyter for interactive analysis
- CLI for automation