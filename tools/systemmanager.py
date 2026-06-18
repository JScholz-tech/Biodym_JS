import marimo

__generated_with = "0.23.5"
app = marimo.App(width="full", app_title="BioDYM System Manager")


# ── Cell 1: imports ──────────────────────────────────────────────────────────
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


# ── Cell 2: all state definitions ────────────────────────────────────────────
@app.cell
def _(mo):
    excel_state, set_excel_state = mo.state(None)
    edits_state, set_edits_state = mo.state(
        {"processes": {}, "flows": {}, "tcs": {}, "bom": {}, "config": {}}
    )
    tc_sel_state, set_tc_sel_state = mo.state(None)
    bom_sel_state, set_bom_sel_state = mo.state(None)
    dirty_state, set_dirty_state = mo.state(False)
    return (
        bom_sel_state,
        dirty_state,
        edits_state,
        excel_state,
        set_bom_sel_state,
        set_dirty_state,
        set_edits_state,
        set_excel_state,
        set_tc_sel_state,
        tc_sel_state,
    )


# ── Cell 3: file upload widget ────────────────────────────────────────────────
@app.cell
def _(mo):
    file_upload = mo.ui.file(
        filetypes=[".xlsm", ".xlsx"],
        label="Upload input file (.xlsm / .xlsx)",
        multiple=False,
    )
    return (file_upload,)


# ── Cell 4: header + upload display ──────────────────────────────────────────
@app.cell
def _(file_upload, mo):
    mo.vstack([
        mo.md("# BioDYM System Manager"),
        mo.md(
            "Upload your `.xlsm` model file to inspect, edit configuration, "
            "and export a version-controllable YAML snapshot."
        ),
        file_upload,
    ])
    return


# ── Cell 5: file load handler ─────────────────────────────────────────────────
@app.cell
def _(
    file_upload,
    mo,
    os,
    pd,
    set_dirty_state,
    set_edits_state,
    set_excel_state,
):
    import tempfile as _tempfile

    mo.stop(
        not file_upload.value,
        mo.callout(mo.md("Upload an **.xlsm** file above to begin."), kind="info"),
    )

    _tmp = _tempfile.NamedTemporaryFile(suffix=".xlsm", prefix="BioDYM_sys_", delete=False)
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
        set_edits_state({"processes": {}, "flows": {}, "tcs": {}, "bom": {}, "config": {}})
        set_dirty_state(False)
        _status = mo.callout(
            mo.md(
                "✅ **" + file_upload.value[0].name + "** loaded — "
                + str(len(_sheets)) + " sheet(s): `"
                + "`, `".join(sorted(_sheets.keys())) + "`"
            ),
            kind="success",
        )
    except Exception as _e:
        _status = mo.callout(mo.md("❌ Failed to load file: `" + str(_e) + "`"), kind="danger")
    finally:
        try:
            os.unlink(_path)
        except OSError:
            pass

    _status
    return


# ── Cell 6: shared lookups (all edit sections depend on this) ─────────────────
@app.cell
def _(excel_state, mo, pd):
    import os as _os
    import sys as _sys

    _here = _os.path.dirname(_os.path.abspath(__file__))
    _src = _os.path.join(_here, "..", "02_src")
    for _p in (_here, _src):
        if _p not in _sys.path:
            _sys.path.insert(0, _p)
    from data_loader import normalize_column_names

    mo.stop(excel_state() is None, mo.callout(mo.md("No data loaded yet."), kind="info"))

    _data = excel_state()
    _sheets = _data["sheets"]

    def _get_elements(sheets):
        cfg = sheets.get("0_Configuration")
        if cfg is None:
            return []
        for _, row in cfg.iterrows():
            if str(row.get("Parameter", "")).strip() == "Elements":
                val = str(row.get("Value", "")).strip()
                if val and val != "nan":
                    return [e.strip() for e in val.split(",") if e.strip()]
        return []

    elements = _get_elements(_sheets)

    _proc_df = _sheets.get("2_1_Definition_Processes")
    process_id_to_name = {}
    process_rows = pd.DataFrame()
    if _proc_df is not None and "ID" in _proc_df.columns:
        for _, _r in _proc_df.dropna(subset=["ID"]).iterrows():
            _pid = int(float(_r["ID"]))
            process_id_to_name[_pid] = str(_r.get("Process_Name", "")).strip()
        process_rows = _proc_df.dropna(subset=["ID"]).copy()

    _flow_df = _sheets.get("1_1_Definition_Flows")
    flow_id_to_name = {}
    flow_rows = pd.DataFrame()
    if _flow_df is not None and "Flow_ID" in _flow_df.columns:
        for _, _r in _flow_df.dropna(subset=["Flow_ID"]).iterrows():
            _fid = str(_r["Flow_ID"]).strip()
            flow_id_to_name[_fid] = str(_r.get("Flow_Name", "")).strip()
        flow_rows = _flow_df.dropna(subset=["Flow_ID"]).copy()

    _tc_df = _sheets.get("2_2_static_TCs")
    tc_process_ids = set()
    if _tc_df is not None and "Process_ID" in _tc_df.columns:
        tc_process_ids = {int(float(x)) for x in _tc_df["Process_ID"].dropna()}

    bom_process_ids = set()
    if _proc_df is not None and "ID" in _proc_df.columns and "Process_Logic" in _proc_df.columns:
        for _, _r in _proc_df.dropna(subset=["ID"]).iterrows():
            if str(_r.get("Process_Logic", "")).strip() == "BOM_Assembler":
                bom_process_ids.add(int(float(_r["ID"])))

    return (
        bom_process_ids,
        elements,
        flow_id_to_name,
        flow_rows,
        normalize_column_names,
        process_id_to_name,
        process_rows,
        tc_process_ids,
    )


# ── Cell 7: shared helper functions ──────────────────────────────────────────
@app.cell
def _(mo):
    def show_df(df, max_rows=200):
        if df is None or df.empty:
            return mo.callout(mo.md("*(sheet is empty)*"), kind="info")
        _html = df.head(max_rows).fillna("").to_html(
            index=False, border=0, classes="dataframe"
        )
        return mo.Html(
            '<div style="overflow-x:auto;max-height:400px;overflow-y:auto">'
            + _html
            + "</div>"
        )

    def apply_edits(base_sheets, edits):
        """Merge edits overlay onto base DataFrames."""
        import pandas as _pd

        sheets = {k: v.copy() for k, v in base_sheets.items()}

        proc_df = sheets.get("2_1_Definition_Processes")
        if proc_df is not None and "ID" in proc_df.columns and edits.get("processes"):
            for pid, changes in edits["processes"].items():
                mask = proc_df["ID"].apply(
                    lambda x: int(float(x)) if _pd.notna(x) else -1
                ) == pid
                for col, val in changes.items():
                    if col in proc_df.columns:
                        proc_df.loc[mask, col] = val
            sheets["2_1_Definition_Processes"] = proc_df

        flow_df = sheets.get("1_1_Definition_Flows")
        if flow_df is not None and "Flow_ID" in flow_df.columns and edits.get("flows"):
            for fid, changes in edits["flows"].items():
                mask = flow_df["Flow_ID"].astype(str).str.strip() == fid
                for col, val in changes.items():
                    if col in flow_df.columns:
                        flow_df.loc[mask, col] = val
            sheets["1_1_Definition_Flows"] = flow_df

        tc_df = sheets.get("2_2_static_TCs")
        if tc_df is not None and edits.get("tcs"):
            for (pid, fid, en), val in edits["tcs"].items():
                col = en + "_TC_Value[%]"
                if col in tc_df.columns:
                    mask = (
                        tc_df["Process_ID"].apply(
                            lambda x: int(float(x)) if _pd.notna(x) else -1
                        ) == pid
                    ) & (tc_df["Flow_ID"].astype(str).str.strip() == fid)
                    tc_df.loc[mask, col] = val
            sheets["2_2_static_TCs"] = tc_df

        bom_df = sheets.get("3_3_Definition_BOM_Assembly")
        if bom_df is not None and edits.get("bom"):
            for (pid, fid, en), val in edits["bom"].items():
                col = en + "_TC_Value[%]"
                if col in bom_df.columns:
                    mask = (
                        bom_df["Process_ID"].apply(
                            lambda x: int(float(x)) if _pd.notna(x) else -1
                        ) == pid
                    ) & (bom_df["Flow_ID"].astype(str).str.strip() == fid)
                    bom_df.loc[mask, col] = val
            sheets["3_3_Definition_BOM_Assembly"] = bom_df

        return sheets

    return apply_edits, show_df


# ═══════════════════════════════════════════════════════════════════════════════
# GROUP D — Overview Tab
# ═══════════════════════════════════════════════════════════════════════════════

@app.cell
def _(edits_state, elements, excel_state, mo, show_df):
    mo.stop(excel_state() is None, mo.md(""))

    _sheets = excel_state()["sheets"]

    _cfg_df = _sheets.get("0_Configuration")
    _cfg_rows = []
    if _cfg_df is not None:
        for _, _r in _cfg_df.iterrows():
            k = str(_r.get("Parameter", "")).strip()
            v = str(_r.get("Value", "")).strip()
            if k and k != "nan":
                _cfg_rows.append("| `" + k + "` | `" + v + "` |")
    _cfg_table = (
        "| Parameter | Value |\n|---|---|\n" + "\n".join(_cfg_rows)
        if _cfg_rows
        else "*(0_Configuration sheet not found)*"
    )

    _edits = edits_state()
    _has_edits = any(bool(_edits.get(k)) for k in ("processes", "flows", "tcs", "bom"))
    _badge = (
        mo.callout(mo.md("⚠️ **Unsaved edits** in overlay — export to persist."), kind="warn")
        if _has_edits
        else mo.md("")
    )

    overview_tab = mo.vstack([
        mo.md("## Model Configuration"),
        mo.md(_cfg_table),
        mo.md("**Detected elements:** `" + (", ".join(elements) if elements else "not found") + "`"),
        _badge,
        mo.md("## Available Sheets"),
        mo.md("\n".join("- `" + s + "`" for s in sorted(_sheets.keys()))),
    ])
    overview_tab
    return (overview_tab,)


# ═══════════════════════════════════════════════════════════════════════════════
# GROUP E — Processes Tab
# ═══════════════════════════════════════════════════════════════════════════════

@app.cell
def _(mo, process_id_to_name):
    _proc_options = {
        pid: "P" + str(pid) + " — " + name
        for pid, name in sorted(process_id_to_name.items())
    }
    proc_sel = mo.ui.dropdown(
        options=_proc_options,
        label="Select process to edit",
    )
    proc_sel
    return (proc_sel,)


@app.cell
def _(edits_state, excel_state, mo, proc_sel):
    mo.stop(proc_sel.value is None, mo.md("*Select a process above.*"))

    _pid = proc_sel.value
    _sheets = excel_state()["sheets"]
    _proc_df = _sheets.get("2_1_Definition_Processes")
    _base = {}
    if _proc_df is not None and "ID" in _proc_df.columns:
        for _, _r in _proc_df.iterrows():
            if int(float(_r["ID"])) == _pid:
                _base = _r.to_dict()
                break

    _ov = edits_state().get("processes", {}).get(_pid, {})

    _cur_name  = _ov.get("Process_Name",       str(_base.get("Process_Name",       "")).strip())
    _cur_logic = _ov.get("Process_Logic",      str(_base.get("Process_Logic",      "")).strip())
    _cur_tc    = _ov.get("TC_Configuration",   str(_base.get("TC_Configuration",   "")).strip())
    _cur_stock = _ov.get("Stock_Configuration",str(_base.get("Stock_Configuration","")).strip())

    _LOGIC_OPTS  = ["Input", "Output", "Splitter", "Transformer", "DSM",
                    "BOM_Assembler", "Pass-through", "LFG"]
    _TC_OPTS     = ["Static", "Dynamic", "No TC"]
    _STOCK_OPTS  = ["Stock", "No_Stock",
                    "Stock_with_InitialStock_Cohort",
                    "Stock_with_InitialStock_Decay"]

    proc_name_txt  = mo.ui.text(value=_cur_name,  label="Process Name")
    proc_logic_dd  = mo.ui.dropdown(options=_LOGIC_OPTS,  value=_cur_logic if _cur_logic in _LOGIC_OPTS  else _LOGIC_OPTS[0],  label="Process Logic")
    proc_tc_dd     = mo.ui.dropdown(options=_TC_OPTS,     value=_cur_tc    if _cur_tc    in _TC_OPTS     else _TC_OPTS[0],     label="TC Configuration")
    proc_stock_dd  = mo.ui.dropdown(options=_STOCK_OPTS,  value=_cur_stock if _cur_stock in _STOCK_OPTS  else _STOCK_OPTS[0],  label="Stock Configuration")
    proc_save_btn  = mo.ui.run_button(label="Apply process edits")

    mo.vstack([
        mo.md("### Edit Process P" + str(_pid)),
        mo.hstack([proc_name_txt, proc_logic_dd], justify="start"),
        mo.hstack([proc_tc_dd, proc_stock_dd], justify="start"),
        proc_save_btn,
    ])
    return proc_logic_dd, proc_name_txt, proc_save_btn, proc_stock_dd, proc_tc_dd


@app.cell
def _(
    edits_state,
    proc_logic_dd,
    proc_name_txt,
    proc_save_btn,
    proc_sel,
    proc_stock_dd,
    proc_tc_dd,
    set_dirty_state,
    set_edits_state,
):
    import marimo as _mo
    _mo.stop(not proc_save_btn.value)
    _mo.stop(proc_sel.value is None)

    _pid = proc_sel.value
    _cur = edits_state()
    _new = {k: dict(v) if isinstance(v, dict) else v for k, v in _cur.items()}
    _new["processes"] = dict(_cur.get("processes", {}))
    _new["processes"][_pid] = {
        "Process_Name":       proc_name_txt.value,
        "Process_Logic":      proc_logic_dd.value,
        "TC_Configuration":   proc_tc_dd.value,
        "Stock_Configuration":proc_stock_dd.value,
    }
    set_edits_state(_new)
    set_dirty_state(True)
    return


@app.cell
def _(edits_state, elements, excel_state, mo, process_rows, show_df):
    mo.stop(excel_state() is None, mo.md(""))

    _edits = edits_state().get("processes", {})
    _df = process_rows.copy() if not process_rows.empty else None

    if _df is not None and not _df.empty and _edits:
        for _pid, _changes in _edits.items():
            _mask = _df["ID"].apply(lambda x: int(float(x))) == _pid
            for _col, _val in _changes.items():
                if _col in _df.columns:
                    _df.loc[_mask, _col] = _val

    _display_cols = [c for c in ["ID", "Process_Name", "Process_Logic",
                                  "TC_Configuration", "Stock_Configuration"]
                     if _df is not None and c in _df.columns]

    processes_tab = mo.vstack([
        mo.md("## Processes"),
        show_df(_df[_display_cols] if _display_cols and _df is not None else _df),
        mo.md("---\n### Edit a Process"),
    ])
    processes_tab
    return (processes_tab,)


# ═══════════════════════════════════════════════════════════════════════════════
# GROUP F — Flows Tab
# ═══════════════════════════════════════════════════════════════════════════════

@app.cell
def _(flow_id_to_name, mo):
    _flow_options = {
        fid: fid + " — " + name
        for fid, name in sorted(flow_id_to_name.items())
    }
    flow_sel = mo.ui.dropdown(
        options=_flow_options,
        label="Select flow to edit",
    )
    flow_sel
    return (flow_sel,)


@app.cell
def _(edits_state, excel_state, flow_sel, mo, process_id_to_name):
    mo.stop(flow_sel.value is None, mo.md("*Select a flow above.*"))

    _fid = flow_sel.value
    _sheets = excel_state()["sheets"]
    _flow_df = _sheets.get("1_1_Definition_Flows")
    _base = {}
    if _flow_df is not None and "Flow_ID" in _flow_df.columns:
        for _, _r in _flow_df.iterrows():
            if str(_r["Flow_ID"]).strip() == _fid:
                _base = _r.to_dict()
                break

    _ov = edits_state().get("flows", {}).get(_fid, {})

    _cur_name = _ov.get("Flow_Name",              str(_base.get("Flow_Name", "")).strip())
    _cur_from = _ov.get("Flow_Output_Process_ID", _base.get("Flow_Output_Process_ID"))
    _cur_to   = _ov.get("Input_Process_ID",       _base.get("Input_Process_ID"))

    _proc_opts = {pid: "P" + str(pid) + " — " + name
                  for pid, name in sorted(process_id_to_name.items())}

    flow_name_txt = mo.ui.text(value=_cur_name, label="Flow Name")
    flow_from_dd  = mo.ui.dropdown(
        options=_proc_opts,
        value=int(_cur_from) if _cur_from is not None else None,
        label="From Process (Flow_Output_Process_ID)",
    )
    flow_to_dd = mo.ui.dropdown(
        options=_proc_opts,
        value=int(_cur_to) if _cur_to is not None else None,
        label="To Process (Input_Process_ID)",
    )
    flow_save_btn = mo.ui.run_button(label="Apply flow edits")

    mo.vstack([
        mo.md("### Edit Flow " + _fid),
        flow_name_txt,
        mo.hstack([flow_from_dd, flow_to_dd], justify="start"),
        flow_save_btn,
    ])
    return flow_from_dd, flow_name_txt, flow_save_btn, flow_sel, flow_to_dd


@app.cell
def _(
    edits_state,
    flow_from_dd,
    flow_name_txt,
    flow_save_btn,
    flow_sel,
    flow_to_dd,
    set_dirty_state,
    set_edits_state,
):
    import marimo as _mo2
    _mo2.stop(not flow_save_btn.value)
    _mo2.stop(flow_sel.value is None)

    _fid = flow_sel.value
    _cur = edits_state()
    _new = {k: dict(v) if isinstance(v, dict) else v for k, v in _cur.items()}
    _new["flows"] = dict(_cur.get("flows", {}))
    _new["flows"][_fid] = {
        "Flow_Name":             flow_name_txt.value,
        "Flow_Output_Process_ID":flow_from_dd.value,
        "Input_Process_ID":      flow_to_dd.value,
    }
    set_edits_state(_new)
    set_dirty_state(True)
    return


@app.cell
def _(edits_state, excel_state, flow_rows, mo, show_df):
    mo.stop(excel_state() is None, mo.md(""))

    _edits = edits_state().get("flows", {})
    _df2 = flow_rows.copy() if not flow_rows.empty else None

    if _df2 is not None and not _df2.empty and _edits:
        for _fid, _changes in _edits.items():
            _mask = _df2["Flow_ID"].astype(str).str.strip() == _fid
            for _col, _val in _changes.items():
                if _col in _df2.columns:
                    _df2.loc[_mask, _col] = _val

    _dcols = [c for c in ["Flow_ID", "Flow_Name", "Flow_Output_Process_ID",
                           "Input_Process_ID", "Flow_Type"]
              if _df2 is not None and c in _df2.columns]

    flows_tab = mo.vstack([
        mo.md("## Flows"),
        show_df(_df2[_dcols] if _dcols and _df2 is not None else _df2),
        mo.md("---\n### Edit a Flow"),
    ])
    flows_tab
    return (flows_tab,)


# ═══════════════════════════════════════════════════════════════════════════════
# GROUP G — TCs Tab
# ═══════════════════════════════════════════════════════════════════════════════

@app.cell
def _(mo, process_id_to_name, tc_process_ids):
    _tc_opts = {
        pid: "P" + str(pid) + " — " + process_id_to_name.get(pid, "?")
        for pid in sorted(tc_process_ids)
    }
    tc_proc_sel = mo.ui.dropdown(options=_tc_opts, label="Select process (TCs)")
    tc_proc_sel
    return (tc_proc_sel,)


@app.cell
def _(set_tc_sel_state, tc_proc_sel):
    set_tc_sel_state(tc_proc_sel.value)
    return


@app.cell
def _(edits_state, elements, excel_state, flow_id_to_name, mo, tc_sel_state):
    import pandas as _pd_tc

    mo.stop(tc_sel_state() is None, mo.md("*Select a process above.*"))

    _pid_tc = tc_sel_state()
    _sheets_tc = excel_state()["sheets"]
    _tc_df = _sheets_tc.get("2_2_static_TCs")
    _active_ns = list(range(2, len(elements) + 1))

    mo.stop(
        _tc_df is None or "Process_ID" not in _tc_df.columns,
        mo.callout(mo.md("Sheet `2_2_static_TCs` not found."), kind="warn"),
    )

    _rows_for_pid = _tc_df[
        _tc_df["Process_ID"].apply(
            lambda x: int(float(x)) if _pd_tc.notna(x) else -1
        ) == _pid_tc
    ].copy()

    _tc_edits = edits_state().get("tcs", {})

    tc_rows = []
    for _, _r in _rows_for_pid.iterrows():
        _fid = str(_r.get("Flow_ID", "")).strip()
        if not _fid or _fid == "nan":
            continue
        _fname = flow_id_to_name.get(_fid, _fid)
        _widgets = {}
        for _n in _active_ns:
            _col = "E" + str(_n) + "_TC_Value[%]"
            _base_val = 0.0
            if _col in _r.index and _pd_tc.notna(_r[_col]):
                _base_val = float(_r[_col])
            _edit_key = (_pid_tc, _fid, "E" + str(_n))
            _val = _tc_edits.get(_edit_key, _base_val)
            _elem_name = elements[_n - 1] if _n - 1 < len(elements) else "E" + str(_n)
            _widgets[_n] = mo.ui.number(
                start=0.0, stop=1.0, step=0.001,
                value=round(float(_val), 6),
                label=_elem_name,
            )
        tc_rows.append({"flow_id": _fid, "flow_name": _fname, "widgets": _widgets})

    tc_save_btn = mo.ui.run_button(label="Apply TC edits")

    _header_cells = ["Flow"]
    for _n in _active_ns:
        _elem_name = elements[_n - 1] if _n - 1 < len(elements) else "E" + str(_n)
        _header_cells.append(_elem_name)

    _form_rows = []
    for _tc_row in tc_rows:
        _row_widgets = [mo.md("**" + _tc_row["flow_id"] + "**  \n*" + _tc_row["flow_name"] + "*")]
        for _n in _active_ns:
            _row_widgets.append(_tc_row["widgets"][_n])
        _form_rows.append(mo.hstack(_row_widgets, justify="start", gap="1rem"))

    mo.vstack(
        [mo.md("### Edit TCs — P" + str(_pid_tc))]
        + (_form_rows if _form_rows else [mo.md("*No TC rows found for this process.*")])
        + [tc_save_btn]
    )
    return tc_rows, tc_save_btn


@app.cell
def _(elements, mo, tc_rows, tc_sel_state):
    mo.stop(tc_sel_state() is None, mo.md(""))

    _active_ns2 = list(range(2, len(elements) + 1))
    _sums = {}
    for _n in _active_ns2:
        _s = sum(row["widgets"][_n].value for row in tc_rows if _n in row["widgets"])
        _elem = elements[_n - 1] if _n - 1 < len(elements) else "E" + str(_n)
        _sums[_elem] = _s

    _lines = []
    tc_sum_ok = True
    for _elem, _s in _sums.items():
        _ok = abs(_s - 1.0) < 1e-6
        if not _ok:
            tc_sum_ok = False
        _icon = "✅" if _ok else "⚠️"
        _lines.append(_icon + " **" + _elem + "**: sum = " + str(round(_s, 6)))

    _kind = "success" if tc_sum_ok else "warn"
    mo.callout(mo.md("\n\n".join(_lines) if _lines else "No rows."), kind=_kind)
    return (tc_sum_ok,)


@app.cell
def _(
    edits_state,
    elements,
    mo,
    set_dirty_state,
    set_edits_state,
    tc_rows,
    tc_save_btn,
    tc_sel_state,
    tc_sum_ok,
):
    import marimo as _mo3
    _mo3.stop(not tc_save_btn.value)
    _mo3.stop(tc_sel_state() is None)

    if not tc_sum_ok:
        mo.callout(
            mo.md("❌ **Cannot save:** TC fractions must sum to exactly 1.0 per element."),
            kind="danger",
        )
    else:
        _pid_save = tc_sel_state()
        _active_ns3 = list(range(2, len(elements) + 1))
        _cur = edits_state()
        _new = {k: dict(v) if isinstance(v, dict) else v for k, v in _cur.items()}
        _new["tcs"] = dict(_cur.get("tcs", {}))
        for _row in tc_rows:
            _fid = _row["flow_id"]
            for _n in _active_ns3:
                if _n in _row["widgets"]:
                    _new["tcs"][(_pid_save, _fid, "E" + str(_n))] = _row["widgets"][_n].value
        set_edits_state(_new)
        set_dirty_state(True)
    return


@app.cell
def _(edits_state, elements, excel_state, mo, normalize_column_names, show_df, tc_process_ids):
    mo.stop(excel_state() is None, mo.md(""))

    _sheets_tcs = excel_state()["sheets"]
    _tc_candidates = [
        "2_2_static_TCs", "2_3_dynamic_TCs", "2_3_Process_TCs", "Static_TCs",
    ]
    _tc_parts = []
    for _sname in _tc_candidates:
        _df_tc = _sheets_tcs.get(_sname)
        if _df_tc is not None:
            if elements:
                _df_tc = normalize_column_names(_df_tc, sheet_name=_sname, elements=elements)
            _tc_parts.append(mo.md("### Sheet: `" + _sname + "`"))
            _tc_parts.append(show_df(_df_tc))

    if not _tc_parts:
        for _sn, _df_tc in _sheets_tcs.items():
            if "TC" in _sn.upper() and "BOM" not in _sn.upper() and "DYNAMIC" not in _sn.upper():
                _tc_parts.append(mo.md("### Sheet: `" + _sn + "`"))
                _tc_parts.append(show_df(_df_tc))

    tcs_tab = mo.vstack(
        [mo.md("## Transfer Coefficients"), mo.md("---\n### Edit TCs for a Process")]
        + (_tc_parts if _tc_parts else [mo.callout(mo.md("No TC sheets found."), kind="info")])
    )
    tcs_tab
    return (tcs_tab,)


# ═══════════════════════════════════════════════════════════════════════════════
# GROUP H — BOM Assembly Tab
# ═══════════════════════════════════════════════════════════════════════════════

@app.cell
def _(bom_process_ids, mo, process_id_to_name):
    _bom_opts = {
        pid: "P" + str(pid) + " — " + process_id_to_name.get(pid, "?")
        for pid in sorted(bom_process_ids)
    }
    if not _bom_opts:
        _bom_opts = {"(none)": "(No BOM_Assembler processes found)"}
    bom_proc_sel = mo.ui.dropdown(options=_bom_opts, label="Select BOM_Assembler process")
    bom_proc_sel
    return (bom_proc_sel,)


@app.cell
def _(bom_proc_sel, set_bom_sel_state):
    set_bom_sel_state(bom_proc_sel.value)
    return


@app.cell
def _(bom_sel_state, edits_state, elements, excel_state, flow_id_to_name, mo):
    import pandas as _pd_bom

    mo.stop(bom_sel_state() is None, mo.md("*Select a process above.*"))

    _pid_bom = bom_sel_state()
    _sheets_bom = excel_state()["sheets"]
    _bom_df = _sheets_bom.get("3_3_Definition_BOM_Assembly")
    _active_ns_bom = list(range(2, len(elements) + 1))

    mo.stop(
        _bom_df is None or "Process_ID" not in _bom_df.columns,
        mo.callout(mo.md("Sheet `3_3_Definition_BOM_Assembly` not found."), kind="warn"),
    )

    _bom_rows_df = _bom_df[
        _bom_df["Process_ID"].apply(
            lambda x: int(float(x)) if _pd_bom.notna(x) else -1
        ) == _pid_bom
    ].copy()

    _bom_edits = edits_state().get("bom", {})

    bom_rows = []
    for _, _r in _bom_rows_df.iterrows():
        _fid = str(_r.get("Flow_ID", "")).strip()
        _ftype = str(_r.get("Output_flow_type", "")).strip()
        if not _fid or _fid == "nan":
            continue
        _fname = flow_id_to_name.get(_fid, _fid)
        _widgets_bom = {}
        if _ftype == "target_Product":
            for _n in _active_ns_bom:
                _col = "E" + str(_n) + "_TC_Value[%]"
                _base_val = 0.0
                if _col in _r.index and _pd_bom.notna(_r[_col]):
                    _base_val = float(_r[_col])
                _edit_key = (_pid_bom, _fid, "E" + str(_n))
                _val = _bom_edits.get(_edit_key, _base_val)
                _elem_name = elements[_n - 1] if _n - 1 < len(elements) else "E" + str(_n)
                _widgets_bom[_n] = mo.ui.number(
                    start=0.0, stop=1.0, step=0.001,
                    value=round(float(_val), 6),
                    label=_elem_name,
                )
        bom_rows.append({
            "flow_id":   _fid,
            "flow_name": _fname,
            "flow_type": _ftype,
            "widgets":   _widgets_bom,
        })

    bom_save_btn = mo.ui.run_button(label="Apply BOM edits")

    _form_bom_rows = []
    for _brow in bom_rows:
        if _brow["flow_type"] == "target_Product":
            _row_w = [mo.md("**" + _brow["flow_id"] + "** *(target_Product)*")]
            for _n in _active_ns_bom:
                _row_w.append(_brow["widgets"][_n])
            _form_bom_rows.append(mo.hstack(_row_w, justify="start", gap="1rem"))
        else:
            _form_bom_rows.append(
                mo.md("**" + _brow["flow_id"] + "** — *" + _brow["flow_type"] + "* (remainder; auto)")
            )

    mo.vstack(
        [mo.md("### Edit BOM Assembly — P" + str(_pid_bom))]
        + (_form_bom_rows if _form_bom_rows else [mo.md("*No BOM rows found.*")])
        + [bom_save_btn]
    )
    return bom_rows, bom_save_btn


@app.cell
def _(bom_rows, bom_sel_state, elements, mo):
    mo.stop(bom_sel_state() is None, mo.md(""))

    _active_ns_bom2 = list(range(2, len(elements) + 1))
    _bom_sums = {}
    for _n in _active_ns_bom2:
        _s = sum(
            row["widgets"][_n].value
            for row in bom_rows
            if row["flow_type"] == "target_Product" and _n in row["widgets"]
        )
        _elem = elements[_n - 1] if _n - 1 < len(elements) else "E" + str(_n)
        _bom_sums[_elem] = _s

    _bom_lines = []
    _bom_any_over = False
    for _elem, _s in _bom_sums.items():
        _over = _s > 1.0 + 1e-9
        if _over:
            _bom_any_over = True
        _icon = "⚠️" if _over else "✅"
        _bom_lines.append(
            _icon + " **" + _elem + "**: " + str(round(_s, 4))
        )

    _bom_kind = "warn" if _bom_any_over else "success"
    mo.callout(mo.md("\n\n".join(_bom_lines) if _bom_lines else "No rows."), kind=_bom_kind)
    return (bom_any_over,)


@app.cell
def _(
    bom_any_over,
    bom_rows,
    bom_save_btn,
    bom_sel_state,
    edits_state,
    elements,
    mo,
    set_dirty_state,
    set_edits_state,
):
    import marimo as _mo4
    _mo4.stop(not bom_save_btn.value)
    _mo4.stop(bom_sel_state() is None)

    _pid_bom_save = bom_sel_state()
    _active_ns_bom3 = list(range(2, len(elements) + 1))
    _cur_bom = edits_state()
    _new_bom = {k: dict(v) if isinstance(v, dict) else v for k, v in _cur_bom.items()}
    _new_bom["bom"] = dict(_cur_bom.get("bom", {}))
    for _brow in bom_rows:
        if _brow["flow_type"] != "target_Product":
            continue
        _fid = _brow["flow_id"]
        for _n in _active_ns_bom3:
            if _n in _brow["widgets"]:
                _new_bom["bom"][(_pid_bom_save, _fid, "E" + str(_n))] = _brow["widgets"][_n].value
    set_edits_state(_new_bom)
    set_dirty_state(True)

    if bom_any_over:
        mo.callout(
            mo.md("⚠️ **Saved with warning:** some element fractions exceed 1.0. "
                  "Remainder will go to Unused_Material."),
            kind="warn",
        )
    return


@app.cell
def _(edits_state, elements, excel_state, mo, normalize_column_names, show_df):
    mo.stop(excel_state() is None, mo.md(""))

    _sheets_bom_tab = excel_state()["sheets"]
    _bom_df_tab = _sheets_bom_tab.get("3_3_Definition_BOM_Assembly")
    if _bom_df_tab is not None and elements:
        _bom_df_tab = normalize_column_names(
            _bom_df_tab, sheet_name="3_3_Definition_BOM_Assembly", elements=elements
        )

    bom_tab = mo.vstack([
        mo.md("## BOM Assembly"),
        show_df(_bom_df_tab),
        mo.md("---\n### Edit BOM Fractions for a Process"),
    ])
    bom_tab
    return (bom_tab,)


# ═══════════════════════════════════════════════════════════════════════════════
# GROUP I — Validation Tab
# ═══════════════════════════════════════════════════════════════════════════════

@app.cell
def _(apply_edits, edits_state, elements, excel_state, mo, validate_composition):
    mo.stop(excel_state() is None, mo.md(""))

    _data_val = excel_state()
    _merged = apply_edits(_data_val["sheets"], edits_state())

    _issues = []
    _ok_msgs = []

    if elements:
        _ok_msgs.append("✅ Elements: `" + ", ".join(elements) + "`")
    else:
        _issues.append("⚠️ No elements found in `0_Configuration`.")

    for _sname in ["3_3_Definition_BOM_Assembly", "2_1_Definition_Processes", "1_1_Definition_Flows"]:
        _df_v = _merged.get(_sname)
        if _df_v is not None:
            _dups = [c for c in _df_v.columns if "." in str(c) and str(c).split(".")[-1].isdigit()]
            if _dups:
                _issues.append("⚠️ `" + _sname + "`: duplicate columns: `" + "`, `".join(_dups) + "`")
            else:
                _ok_msgs.append("✅ `" + _sname + "`: no duplicate columns")

    _tc_df_v = _merged.get("2_2_static_TCs")
    if _tc_df_v is not None and elements and "Process_ID" in _tc_df_v.columns:
        _active_ns_v = list(range(2, len(elements) + 1))
        for _pid_v, _grp in _tc_df_v.groupby(
            _tc_df_v["Process_ID"].apply(lambda x: int(float(x)))
        ):
            for _n in _active_ns_v:
                _col = "E" + str(_n) + "_TC_Value[%]"
                if _col in _grp.columns:
                    _s = _grp[_col].dropna().sum()
                    _elem = elements[_n - 1] if _n - 1 < len(elements) else "E" + str(_n)
                    if abs(_s - 1.0) > 1e-6:
                        _issues.append(
                            "⚠️ TC P" + str(_pid_v) + " / " + _elem
                            + ": sum = " + str(round(_s, 6)) + " ≠ 1.0"
                        )
                    else:
                        _ok_msgs.append("✅ TC P" + str(_pid_v) + " / " + _elem + ": sum = 1.0")

    _bom_df_v = _merged.get("3_3_Definition_BOM_Assembly")
    if _bom_df_v is not None and elements and "Output_flow_type" in _bom_df_v.columns:
        _active_ns_v2 = list(range(2, len(elements) + 1))
        _target = _bom_df_v[_bom_df_v["Output_flow_type"].astype(str) == "target_Product"]
        if "Process_ID" in _target.columns:
            for _pid_v, _grp in _target.groupby(
                _target["Process_ID"].apply(lambda x: int(float(x)))
            ):
                for _n in _active_ns_v2:
                    _col = "E" + str(_n) + "_TC_Value[%]"
                    if _col in _grp.columns:
                        _fracs = {_col: float(v) for v in _grp[_col].dropna()}
                        if _fracs:
                            _res = validate_composition(_fracs)
                            _elem = elements[_n - 1] if _n - 1 < len(elements) else "E" + str(_n)
                            if not _res["valid"]:
                                _issues.append(
                                    "⚠️ BOM P" + str(_pid_v) + " / " + _elem
                                    + ": " + str(_res["error"])
                                )

    _proc_df_v = _merged.get("2_1_Definition_Processes")
    _flow_df_v = _merged.get("1_1_Definition_Flows")
    if _proc_df_v is not None and _flow_df_v is not None:
        _valid_pids = set(
            int(float(x))
            for x in _proc_df_v["ID"].dropna()
        ) if "ID" in _proc_df_v.columns else set()
        for _col_fk in ("Flow_Output_Process_ID", "Input_Process_ID"):
            if _col_fk in _flow_df_v.columns:
                for _fid_v, _pid_v in _flow_df_v[["Flow_ID", _col_fk]].dropna().itertuples(index=False):
                    if int(_pid_v) not in _valid_pids:
                        _issues.append(
                            "⚠️ Flow `" + str(_fid_v) + "` references unknown process " + str(int(_pid_v))
                        )

    _summary = _issues + _ok_msgs
    validation_tab = mo.vstack([
        mo.md("## Validation"),
        mo.callout(
            mo.md("\n\n".join(_summary) if _summary else "Nothing to validate."),
            kind="warn" if _issues else "success",
        ),
    ])
    validation_tab
    return (validation_tab,)


# ═══════════════════════════════════════════════════════════════════════════════
# GROUP J — Main Tabs Container
# ═══════════════════════════════════════════════════════════════════════════════

@app.cell
def _(
    bom_tab,
    flows_tab,
    mo,
    overview_tab,
    processes_tab,
    tcs_tab,
    validation_tab,
):
    mo.ui.tabs({
        "Overview":     overview_tab,
        "Processes":    processes_tab,
        "Flows":        flows_tab,
        "TCs":          tcs_tab,
        "BOM Assembly": bom_tab,
        "Validation":   validation_tab,
    })
    return


# ═══════════════════════════════════════════════════════════════════════════════
# GROUP K — Export
# ═══════════════════════════════════════════════════════════════════════════════

@app.cell
def _(dirty_state, mo):
    _label = (
        "💾  Export YAML  (● unsaved edits)"
        if dirty_state()
        else "💾  Export YAML"
    )
    export_btn = mo.ui.run_button(label=_label)
    mo.vstack([
        mo.md("---\n## Export Configuration"),
        mo.md(
            "Export model metadata, processes, flows, TCs, and BOM fractions "
            "as a version-controllable YAML file."
        ),
        export_btn,
    ])
    return (export_btn,)


@app.cell
def _(
    apply_edits,
    edits_state,
    excel_state,
    export_btn,
    here,
    mo,
    model_to_yaml,
    os,
    save_yaml,
):
    import yaml as _yaml

    mo.stop(excel_state() is None, mo.md(""))
    mo.stop(not export_btn.value)

    _data_exp = excel_state()
    _merged_exp = apply_edits(_data_exp["sheets"], edits_state())
    _yaml_data = model_to_yaml(_merged_exp, source_file=_data_exp["filename"])
    _stem = os.path.splitext(_data_exp["filename"])[0]
    _out_dir = os.path.join(here, "..", "01_data", "02_output")
    os.makedirs(_out_dir, exist_ok=True)
    _out_path = os.path.join(_out_dir, _stem + "_config.yaml")
    save_yaml(_yaml_data, _out_path)

    _preview = _yaml.dump(_yaml_data, default_flow_style=False, allow_unicode=True, sort_keys=False)
    mo.vstack([
        mo.callout(mo.md("✅ Saved to `" + _out_path + "`"), kind="success"),
        mo.md("### YAML Preview"),
        mo.md("```yaml\n" + _preview + "\n```"),
    ])
    return


if __name__ == "__main__":
    app.run()
