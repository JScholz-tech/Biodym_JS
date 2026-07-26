# BioDYM Flow & Process Naming Convention

Readable `name:` fields for flows and processes in a study `config.yaml`.
Governs the **human-readable name only** — never the `F_<from>_<to>` IDs (those
are systematic and cascade-safe already) and never any referenced field.

Motivation: names are what every graph prints (Sankey hover, graphviz /
esankey / sankeymatic static edges all read `flow.Name`). Inconsistent or
ID-echoing names make flows impossible to identify in a diagram, and hand-typed
endpoint/ID fragments in a name **drift** the moment a flow is rewired.

---

## Flow names

Form: **`Material_Status (to Destination)`**

Two parts, split at the parenthesis:

- **`Material_Status`** (the semantic core, before the `(`) — the substance plus
  its state/lineage at this point in the system. This is the part that carries
  information found *nowhere else* in the config, so it is what the name exists
  for.
  - **Material** — the substance. Title Case. e.g. `Printer`, `Cartridge`,
    `Straw`, `Construction_Material`.
  - **`_Status`** — optional, underscore-joined: the material's condition or
    processing lineage. e.g. `Printer_Reman`, `Straw_Incorporated`,
    `Construction_Material_EoL`, `Cartridge_Extracted`. Omit when the material
    alone is unambiguous (`Grain`, `Pyrochar`).
- **`(to Destination)`** (in parentheses) — the readable graph disambiguator:
  where the flow goes. Manually maintained (BioDYM does not yet auto-derive it),
  so it can go stale if you rename the target process — keep it in sync, or drop
  it and rely on the ID's `to` endpoint.
  - Always `(to X)` form: `(to WEEE)`, `(to Remanufacturing)`, `(to Atmosphere)`.
  - This is where an element-coded sink split belongs: prefer
    `Emissions (to Atmosphere)` / `Emissions (to Water & Nutrient)` over an
    `_C` / `_E` element suffix baked into the core.

### Hard rules (ERROR — must fix)

1. Not empty.
2. Not a placeholder default: `Flow <n>`, or `<from_name>_<to_name>`
   (SystemDefiner's blank-name default).
3. Never echoes topology already in the ID: no `F_<a>_<b>` fragment anywhere in
   the name, no leading `F_<a>_<b>_` prefix, name ≠ its own ID.
4. **Destination required on a split**: when >1 flow with the *same
   `Material_Status` core* leaves the *same* process, each must carry a distinct
   `(to Destination)`. Two identical cores out of one node are indistinguishable
   in every graph.
5. Balanced brackets (`(Extraction)`, not `[Extraction)`).

### Soft rules (WARN — suggest, don't force)

- Title Case first letter.
- Exactly one space before `(`, none inside: `Printer_Reman (to WEEE)`, not
  `Printer_Reman(to WEEE)` or `Printer_Reman ( to WEEE )`.
- A parenthesis that is **not** a `(to …)` destination is probably a status that
  belongs in the underscore core: `Printer (Reman)` → `Printer_Reman`.
- No leading/trailing whitespace.
- No two flows share an identical name (indistinguishable in a legend).

---

## Process names

Structured freeform — a real, descriptive label. Role shapes the grammar:

- **Operations / transformers** — what it does: `Dismantling (extraction)`,
  `Shredder & Mechanical Sorting`.
- **Stock / boundary sinks & sources** — a place noun: `WEEE Recycling`,
  `Spare-Part Storage`, `Recovered Materials`.

### Hard rules (ERROR)

1. Not empty.
2. Not the `Process <n>` default; name ≠ `P<id>`.
3. Balanced brackets.

### Soft rules (WARN)

- Title Case.
- Consistent ` (qualifier)` spacing (one space before `(`).
- No leading/trailing whitespace.
- Consistent domain spelling across the study (e.g. don't mix `WEE` / `WEEE`).

---

## Stocks

Stocks have **no name field** of their own — a stock lives on a process whose
`stock: Stock` flag is set, and it is labelled by that process's name in every
plot. So the stock convention *is* the process-name convention: a stock-bearing
process should read as a place noun (see above). The scanner reports
stock-bearing processes so you can eyeball them, but applies no separate rule.

---

## What this convention does NOT touch

- `F_<from>_<to>` flow IDs and the `_N` duplicate-edge suffix — systematic,
  repaired by SystemDefiner cascades, never rewritten here.
- Scenario / MC parameter names (`TC_E<e>_<from>_<to>`, `P<id>_…`) — keyed to
  IDs, out of scope.
- Element names, references, compositions.
