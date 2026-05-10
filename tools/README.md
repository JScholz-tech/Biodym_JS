# BioDYM Interactive Tools

Standalone Marimo apps for interactive exploration and analysis.

> **Primary dashboard:** `01_BioDYM_Dashboard.ipynb` (Voilà) — run with `uv run voila 01_BioDYM_Dashboard.ipynb`

---

## Dashboard — Full Analysis (Marimo, WIP)

Upload an `.xlsm` input file and run the full MFA pipeline interactively.
Results are shown in tabs: Sankey, Flows, Composition, Stocks, KPIs, Validation.

```bash
uv run marimo run tools/marimo_dashboard.py
# or in developer/edit mode:
uv run marimo edit tools/marimo_dashboard.py
```

> This is a work-in-progress Marimo port of the Voilà dashboard. Use the `.ipynb` for production.

---

## BUF Explorer — Biomass Utilisation Factor

Interactive calculator based on *vom Berg et al. (2022), nova-Paper #16*.
Supports multi-stage cascade scenarios with presets for common pathways.

```bash
uv run marimo run tools/buf_explorer.py
```

## CUF Explorer — Carbon Utilisation Factor

Dual sub-indicator for carbon cycle assessment in bio-based systems.
Presets for different pathways (direct incorporation, pyrolysis, anaerobic digestion, etc.).

```bash
uv run marimo run tools/cuf_explorer.py
```
