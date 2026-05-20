import marimo

__generated_with = "0.23.5"
app = marimo.App(width="full", app_title="BioDYM System Manager")


@app.cell
def _():
    import os
    import sys
    import warnings

    import marimo as mo
    import pandas as pd

    warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

    here = os.path.dirname(os.path.abspath(__file__))
    _src = os.path.join(here, "..", "02_src")
    for _p in (here, _src):
        if _p not in sys.path:
            sys.path.insert(0, _p)

    from yaml_schema import validate_composition, model_to_yaml, save_yaml

    return here, mo, model_to_yaml, os, pd, save_yaml, validate_composition


@app.cell
def _(mo):
    file_upload = mo.ui.file(
        filetypes=[".xlsm", ".xlsx"],
        label="📂 Upload input file (.xlsm / .xlsx)",
        multiple=False,
    )
    excel_state, set_excel_state = mo.state(None)
    return excel_state, file_upload, set_excel_state


@app.cell
def _(file_upload, mo):
    mo.vstack([
        mo.md("# BioDYM System Manager"),
        mo.md(
            "Upload your `.xlsm` model file to inspect configuration, validate "
            "compositions, and export a version-controllable YAML snapshot."
        ),
        file_upload,
    ])
    return


@app.cell
def _(file_upload, mo, os, pd, set_excel_state):
    import tempfile

    mo.stop(
        not file_upload.value,
        mo.callout(mo.md("Upload an **.xlsm** file above to begin."), kind="info"),
    )

    _tmp = tempfile.NamedTemporaryFile(suffix=".xlsm", prefix="BioDYM_sys_", delete=False)
    _tmp.write(file_upload.value[0].contents)
    _tmp.close()
    _path = _tmp.name

    try:
        _sheets = pd.read_excel(
            _path,
            sheet_name=None,
            header=0,
            engine="openpyxl",
            na_values=["N.A.", "NA", "n/a"],
            decimal=",",
        )
        set_excel_state({"sheets": _sheets, "filename": file_upload.value[0].name})
        _status = mo.callout(
            mo.md(
                f"✅ **{file_upload.value[0].name}** loaded — "
                f"{len(_sheets)} sheet(s): `{'`, `'.join(sorted(_sheets.keys()))}`"
            ),
            kind="success",
        )
    except Exception as _e:
        _status = mo.callout(mo.md(f"❌ Failed to load file: `{_e}`"), kind="danger")
    finally:
        try:
            os.unlink(_path)
        except OSError:
            pass

    _status
    return


@app.cell
def _(excel_state, mo, validate_composition):
    import sys as _sys
    import os as _os
    _here = _os.path.dirname(_os.path.abspath(__file__))
    _src = _os.path.join(_here, "..", "02_src")
    for _p in (_here, _src):
        if _p not in _sys.path:
            _sys.path.insert(0, _p)
    from data_loader import normalize_column_names

    mo.stop(
        excel_state() is None,
        mo.callout(mo.md("No data loaded yet — upload a file above."), kind="info"),
    )

    _data = excel_state()
    _sheets = _data["sheets"]

    # ---- Extract elements from 0_Configuration ----
    def _get_elements(sheets):
        cfg_df = sheets.get("0_Configuration")
        if cfg_df is None:
            return []
        for _, row in cfg_df.iterrows():
            key = str(row.get("Parameter", "")).strip()
            val = str(row.get("Value", "")).strip()
            if key == "Elements" and val and val != "nan":
                return [e.strip() for e in val.split(",") if e.strip()]
        return []

    _elements = _get_elements(_sheets)

    # ---- Helper: render a DataFrame as an HTML table ----
    def _show_df(df, max_rows=200):
        if df is None or df.empty:
            return mo.callout(mo.md("*(sheet is empty)*"), kind="info")
        _html = df.head(max_rows).fillna("").to_html(index=False, border=0, classes="dataframe")
        return mo.Html(f'<div style="overflow-x:auto;max-height:400px;overflow-y:auto">{_html}</div>')

    # ---- Tab: Overview ----
    def _build_overview(sheets, elements):
        cfg_df = sheets.get("0_Configuration")
        cfg_rows = []
        if cfg_df is not None:
            for _, row in cfg_df.iterrows():
                k = str(row.get("Parameter", "")).strip()
                v = str(row.get("Value", "")).strip()
                if k and k != "nan":
                    cfg_rows.append(f"| `{k}` | `{v}` |")
        cfg_table = (
            "| Parameter | Value |\n|---|---|\n" + "\n".join(cfg_rows)
            if cfg_rows else "*(0_Configuration sheet not found)*"
        )
        sheet_list = "\n".join(f"- `{s}`" for s in sorted(sheets.keys()))
        return mo.vstack([
            mo.md("## Model Configuration"),
            mo.md(cfg_table),
            mo.md(f"**Detected elements:** `{', '.join(elements) if elements else 'not found'}`"),
            mo.md("## Available Sheets"),
            mo.md(sheet_list),
        ])

    # ---- Tab: Processes ----
    def _build_processes(sheets):
        df = sheets.get("2_1_Definition_Processes")
        if df is None:
            return mo.callout(mo.md("Sheet `2_1_Definition_Processes` not found."), kind="warn")
        display_cols = [c for c in [
            "Process_ID", "Process_Name", "Process_Logic",
            "TC_Configuration", "Stock_Configuration",
        ] if c in df.columns]
        return mo.vstack([
            mo.md(f"## Processes ({len(df.dropna(subset=['Process_ID'] if 'Process_ID' in df.columns else []))} rows)"),
            _show_df(df[display_cols] if display_cols else df),
        ])

    # ---- Tab: Flows ----
    def _build_flows(sheets):
        df = sheets.get("1_1_Definition_Flows")
        if df is None:
            return mo.callout(mo.md("Sheet `1_1_Definition_Flows` not found."), kind="warn")
        display_cols = [c for c in [
            "Flow_ID", "Flow_Name", "From_Process", "To_Process", "Flow_Type",
        ] if c in df.columns]
        return mo.vstack([
            mo.md(f"## Flows ({len(df.dropna(subset=['Flow_ID'] if 'Flow_ID' in df.columns else []))} rows)"),
            _show_df(df[display_cols] if display_cols else df),
        ])

    # ---- Tab: TCs (with element-named columns) ----
    def _build_tcs(sheets, elements, normalizer):
        # Try common TC sheet names
        tc_candidates = [
            "2_2_static_TCs", "2_3_Process_TCs", "2_2_Process_TCs",
            "Static_TCs", "2_2_TCs",
        ]
        results = []
        for name in tc_candidates:
            df = sheets.get(name)
            if df is not None:
                if elements:
                    df = normalizer(df, sheet_name=name, elements=elements)
                results.append((name, df))

        if not results:
            # Show any sheet whose name contains "TC"
            for sname, df in sheets.items():
                if "TC" in sname.upper() and "BOM" not in sname.upper() and "DYNAMIC" not in sname.upper():
                    if elements:
                        df = normalizer(df, sheet_name=sname, elements=elements)
                    results.append((sname, df))

        if not results:
            return mo.callout(mo.md("No TC sheets found."), kind="info")

        parts = []
        for sname, df in results:
            named_cols = [c for c in df.columns if any(
                f"{e}_TC_ID" == c or f"{e}_Value" in c for e in elements
            )] if elements else []
            note = (
                f" *(named columns: `{'`, `'.join(named_cols)}`)*"
                if named_cols else " *(legacy E{{n}} format)*"
            )
            parts.append(mo.md(f"### Sheet: `{sname}`{note}"))
            parts.append(_show_df(df))
        return mo.vstack(parts)

    # ---- Tab: BOM Assembly ----
    def _build_bom(sheets, elements, normalizer):
        df = sheets.get("3_3_Definition_BOM_Assembly")
        if df is None:
            return mo.callout(mo.md("Sheet `3_3_Definition_BOM_Assembly` not found."), kind="info")
        if elements:
            df = normalizer(df, sheet_name="3_3_Definition_BOM_Assembly", elements=elements)
        named_cols = [c for c in df.columns if any(
            f"{e}_TC_ID" == c or f"{e}_Value" in c for e in elements
        )] if elements else []
        note = (
            f"Named element columns: `{'`, `'.join(named_cols)}`"
            if named_cols else "No named element columns found (legacy E{n} format)."
        )
        return mo.vstack([
            mo.md("## BOM Assembly"),
            mo.callout(mo.md(note), kind="success" if named_cols else "warn"),
            _show_df(df),
        ])

    # ---- Tab: Validation ----
    def _build_validation(sheets, elements):
        issues = []
        ok = []

        # Check elements declared
        if elements:
            ok.append(f"✅ Elements declared: `{', '.join(elements)}`")
        else:
            issues.append("⚠️ No elements found in `0_Configuration`.")

        # Check for pandas dedup suffixes in key sheets
        for sname in ["3_3_Definition_BOM_Assembly", "2_1_Definition_Processes", "1_1_Definition_Flows"]:
            df = sheets.get(sname)
            if df is not None:
                dups = [c for c in df.columns if "." in str(c) and str(c).split(".")[-1].isdigit()]
                if dups:
                    issues.append(f"⚠️ `{sname}`: possible duplicate columns: `{'`, `'.join(dups)}`")
                else:
                    ok.append(f"✅ `{sname}`: no duplicate columns detected")

        # Check BOM fractions if present
        bom_df = sheets.get("3_3_Definition_BOM_Assembly")
        if bom_df is not None and elements:
            val_cols = [c for c in bom_df.columns if c.endswith("_Value[%]") or (
                any(c.startswith(f"E{i}") for i in range(2, 10)) and "Value" in c
            )]
            if val_cols:
                target_rows = bom_df[
                    bom_df.get("Output_flow_type", bom_df.iloc[:, 0]).astype(str) == "target_Product"
                ] if "Output_flow_type" in bom_df.columns else bom_df
                for _, row in target_rows.iterrows():
                    fracs = {}
                    for vc in val_cols:
                        try:
                            v = float(row[vc])
                            if v == v:  # not nan
                                fracs[vc] = v
                        except (ValueError, TypeError):
                            pass
                    if fracs:
                        res = validate_composition(fracs)
                        fid = str(row.get("Flow_ID", "?")).strip()
                        if not res["valid"]:
                            issues.append(f"⚠️ BOM flow `{fid}`: {res['error']}")
                        else:
                            ok.append(f"✅ BOM flow `{fid}`: fractions OK ({sum(fracs.values()):.3f})")

        summary = (issues + ok) if issues else ok
        kind = "warn" if issues else "success"
        return mo.vstack([
            mo.md("## Validation"),
            mo.callout(mo.md("\n\n".join(summary) if summary else "Nothing to validate yet."), kind=kind),
        ])

    # ---- Assemble tabs ----
    mo.ui.tabs({
        "Overview": _build_overview(_sheets, _elements),
        "Processes": _build_processes(_sheets),
        "Flows": _build_flows(_sheets),
        "TCs": _build_tcs(_sheets, _elements, normalize_column_names),
        "BOM Assembly": _build_bom(_sheets, _elements, normalize_column_names),
        "Validation": _build_validation(_sheets, _elements),
    })
    return


@app.cell
def _(mo):
    export_btn = mo.ui.run_button(label="💾  Export YAML")
    return (export_btn,)


@app.cell
def _(export_btn, mo):
    mo.vstack([
        mo.md("---\n## Export Configuration"),
        mo.md("Export model metadata, processes, and flows as a version-controllable YAML file."),
        export_btn,
    ])
    return


@app.cell
def _(excel_state, export_btn, here, mo, model_to_yaml, os, save_yaml):
    mo.stop(excel_state() is None, mo.md(""))
    mo.stop(not export_btn.value)

    import yaml as _yaml

    _data = excel_state()
    _yaml_data = model_to_yaml(_data["sheets"], source_file=_data["filename"])
    _stem = os.path.splitext(_data["filename"])[0]
    _out_dir = os.path.join(here, "..", "01_data", "02_output")
    os.makedirs(_out_dir, exist_ok=True)
    _out_path = os.path.join(_out_dir, f"{_stem}_config.yaml")
    save_yaml(_yaml_data, _out_path)

    _preview = _yaml.dump(_yaml_data, default_flow_style=False, allow_unicode=True, sort_keys=False)
    mo.vstack([
        mo.callout(mo.md(f"✅ Saved to `{_out_path}`"), kind="success"),
        mo.md("### YAML Preview"),
        mo.md(f"```yaml\n{_preview}\n```"),
    ])
    return


if __name__ == "__main__":
    app.run()
