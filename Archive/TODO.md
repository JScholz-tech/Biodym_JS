BioDYM MFA Tool – Enhanced Sankey Fixes (TODO)

1) Plotting: Robust config lookup
- get_process_visualization: accept Process_ID variants
  - Numeric: "1", "01", "001"
  - Prefixed: "P_1", "P_01", "P_001" (case-insensitive)
- Fallback by name: check both "Process_Name" and "Name(EN)" keys
- Prefer element-specific X/Y (Material, WC, DM, CC); then general X/Y; else default

2) Plotting: Position safety
- Coerce X/Y to float; clamp to [0,1]
- Apply clamp in:
  - calculate_element_specific_positions
  - calculate_dynamic_positions (Custom/Linear paths)

3) Loader: Normalize keys
- In load_part6_visualization_sheets:
  - Normalize Process_ID/ID keys: strip, upper
  - Store dict under config['process_colors'] with normalized keys
  - Preserve original columns including Process_ID and Name(EN)

4) Tests
- Test robust ID/name matching:
  - Processes with Process_ID like 'P_02' and Name(EN)
  - Verify element-specific positions returned for Material/DM/CC/WC
- Test decimal coercion & clamping behavior

5) Smoke script (optional)
- Small helper to print mapping (Process_ID → element X/Y) for a few rows

6) Validate
- uv run pytest -q
- Document summary in session.md

