# BioDYM Input Files

A BioDYM model can be defined in **two interchangeable formats**. Both feed the
same engine — pick whichever suits you.

| Format | File | Authored with | Best for |
|---|---|---|---|
| **Excel Systemmanager** | `*.xlsm` | Excel (the `template/` workbook) | spreadsheet users, bulk data entry |
| **YAML config** | `config.yaml` | the **bioDYM SystemDefiner** web app (`uv run python -m systemdefiner`) | visual editing, version control, web workflow |

Both are loaded the same way — set `input_file` in `00_BioDYM_Workflow.ipynb`, or
enter the path in the Voilà dashboard. The notebook/dashboard auto-detect the
extension (`.xlsm`/`.xlsx` → Excel, `.yaml`/`.yml` → YAML).

## Folder layout

```
01_data/01_input/
  README.md      ← this file
  template/      ← blank Excel Systemmanager template (the Excel-format reference)
  case_studies/  ← SystemDefiner working directory
    T01_…/       ← tutorial studies (names starting "T0")            [tracked]
    <your study>/← your own studies                                  [not tracked]
  <other files>  ← your own working inputs                           [not tracked]
```

Only `template/`, this `README.md`, and **tutorial studies** are committed to git.
Tutorials are ordinary SystemDefiner studies named `T0…` (e.g. `T01_First_MFA`)
that live in `case_studies/` so they appear in the app directly — a fresh clone
opens the SystemDefiner with the tutorials already in the list. Everything else
under `01_data/01_input/` (your other studies, working `.xlsm` files) is local and
gitignored.

---

## Excel Systemmanager structure (`.xlsm`)

One workbook; each sheet defines part of the system:

| Sheet | Defines |
|---|---|
| `0_Configuration` | time range, element list + hierarchy, run flags (DSM/FOMP/MC/scenarios), unit |
| `1_1_Definition_Flows` | every flow (ID, name, from/to process) + element composition columns |
| `1_2_Data_Flows` | flow amounts per year (time series) |
| `2_1_Definition_Processes` | processes: `ID`, `Process_Name`, `Process_Logic`, `Stock_Configuration`, `TC_Configuration` |
| `2_2_static_TCs` | static transfer coefficients (`E{n}_TC_ID`, `E{n}_TC_Value[%]`) |
| `2_3_dynamic_TCs` | time-varying TCs (adds a `Year` column) |
| `2_4_Initial_Stock` | t=0 stock (`Basic_Material_Quantity`, `Basic_E{n}_Fraction[%]`, cohort params) |
| `3_1_Definition_DSM` | dynamic stock model — one row per lifetime category |
| `3_2_Definition_FOMP` | first-order decay parameters (`f_labile`, `k_labile`, …) |
| `3_3_Definition_LFG` | landfill-gas fractions + site parameters |
| `3_3_Definition_BOM_Assembly` | bill-of-materials target compositions |
| `3_4_Definition_FlowCap` | capacity-limited routing (capped/overflow + cap series) |
| `4_1_Uncertainty_Parameters` | Monte Carlo parameter distributions |
| `5_1_Scenario_Manager` | scenario modifications |

**Process logics:** `Input`, `Output`, `Pass-through`, `Splitter`, `Transformer`,
`DSM`, `FOMP`, `LFG`, `BOM_Assembler`, `FlowCap`.
**TC ID convention:** every element uses `TC_E{n}_{from:02d}_{to:02d}` — `E1` = material,
`E2` = WC, `E3` = DM, … (process IDs are 0-based; `P0` is the system boundary).

## YAML config structure (`config.yaml`)

Produced by the SystemDefiner; the same information as the workbook, as nested keys:

```yaml
schema_version: "1.0"
name: My_Study
description: ""              # free-text notes (shown under the diagram in the app)
model:
  start_year: 2025
  end_year: 2125
  elements: [material, WC, DM, TC]
  unit_of_measurement: Mg
  run_dsm_calculation: true
  run_fomp_calculation: true
  run_monte_carlo: false
  run_scenario_analysis: false
  selected_scenarios: ["", "", "", ""]
processes:            # id (0-based), name, logic, stock, tc_config, + fomp/dsm/lfg/flowcap blocks
flows:                # id, name, from_process, to_process
transfer_coefficients:# process_id, flow_id, tc_type (static|dynamic), values / time_series
element_hierarchy:    # parent → children (material = WC + DM; DM = TC + …)
flow_compositions:    # flow_id → element fractions (of total material)
flow_data:            # flow_id, element, {year: value}
bom_assembly:         # per-process BOM target compositions
scenarios:            # name → modifications (parameter_name, operation, new_value, year range)
mc_parameters:        # Monte Carlo distributions (parameter_id, distribution, …, flow_group)
initial_stocks:       # per-process t=0 stock (quantity, composition, cohort/decay params)
references:           # Zotero-linked citations
```

The SystemDefiner's YAML→engine bridge (`data_loader.yaml_to_excel_dataframes`)
maps every section above onto the corresponding Excel sheet, so a YAML config and
the equivalent workbook produce identical results.

---

## Tutorials

Tutorial studies are small, self-contained examples that each demonstrate one
feature, with an in-app **Description** explaining the lesson. They are ordinary
SystemDefiner studies named with a `T0…` prefix (`T01_First_MFA`,
`T02_Splitting_a_flow`, …) kept directly in `case_studies/`, so they show up in the
SystemDefiner list and open like any other study.

To add a tutorial: create a study in the app and name it `T0x_…` — the `T0…` prefix
is what git tracks (see `.gitignore`); every other study in `case_studies/` stays
local. No copying or export step is needed.
