# -*- coding: utf-8 -*-
"""YAML schema utilities for BioDYM model configuration.

Provides helpers for validating, saving, and loading BioDYM model configs
as human-readable YAML files suitable for version control.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


def validate_composition(fractions: dict[str, float]) -> dict[str, Any]:
    """Validate that element fractions in a composition dict sum to <= 1.0.

    Parameters
    ----------
    fractions : dict
        {element_name: fraction_value (0.0 – 1.0)}

    Returns
    -------
    dict
        ``{'valid': bool, 'error': str | None}``
    """
    if not fractions:
        return {"valid": True, "error": None}
    total = sum(float(v) for v in fractions.values())
    if total > 1.0 + 1e-9:
        return {
            "valid": False,
            "error": f"fraction sum {total:.4f} exceeds 1.0",
        }
    return {"valid": True, "error": None}


def save_yaml(data: dict, path: str) -> None:
    """Write a Python dict to a YAML file (UTF-8, block style)."""
    text = yaml.dump(
        data, default_flow_style=False, allow_unicode=True, sort_keys=False
    )
    Path(path).write_text(text, encoding="utf-8")


def load_yaml(path: str) -> dict:
    """Load a YAML file and return its contents as a dict."""
    return yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}


def model_to_yaml(excel_data: dict, source_file: str = "") -> dict:
    """Convert a BioDYM Excel data dict to a YAML-serializable dict.

    Extracts the key configuration sheets (model dimensions, processes,
    flows) and returns a structured dict ready for ``save_yaml()``.

    Parameters
    ----------
    excel_data : dict[str, pd.DataFrame]
        Sheet-name → DataFrame as returned by ``pd.read_excel(sheet_name=None)``.
    source_file : str
        Original filename for the ``meta`` block.

    Returns
    -------
    dict
        Structured model config.
    """
    import pandas as pd  # local import keeps this module lightweight
    import re as _re

    out: dict[str, Any] = {
        "meta": {
            "source_file": str(source_file),
            "exported_at": datetime.now().isoformat(timespec="seconds"),
        },
        "model": {},
        "processes": [],
        "flows": [],
        "transfer_coefficients": [],
        "bom_assembly": [],
        "element_hierarchy": [],
        "flow_compositions": [],
        "flow_data": [],
        "scenarios": [],
        "mc_parameters": [],
        "initial_stocks": [],
    }

    # ---- Model dimensions from 0_Configuration ----
    # Supports both old format (Parameter/Value columns) and
    # new format (Setting_Name/Value columns).
    cfg_df = excel_data.get("0_Configuration")
    if cfg_df is not None:
        # Detect which column holds the parameter key
        key_col = "Setting_Name" if "Setting_Name" in cfg_df.columns else "Parameter"
        cfg: dict[str, str] = {}
        for _, row in cfg_df.iterrows():
            key = str(row.get(key_col, "")).strip()
            val = row.get("Value", "")
            val_str = "" if pd.isna(val) else str(val).strip()
            if key and key != "nan":
                cfg[key] = val_str

        # Start / End year
        start_raw = cfg.get("Start_Year", "")
        end_raw = cfg.get("End_Year", "")

        def _to_int(v: str) -> Any:
            try:
                return int(float(v))
            except (ValueError, TypeError):
                return None

        start_year = _to_int(start_raw)
        end_year = _to_int(end_raw)

        # Elements: old format has "Elements" key with comma-separated string;
        # new format has Element_ID_1, Element_ID_2, … rows.
        elements: list[str] = []
        elem_pairs: list[tuple[int, str]] = []
        elem_pattern = _re.compile(r"^Element_ID_(\d+)$", _re.IGNORECASE)
        for k, v in cfg.items():
            m = elem_pattern.match(k)
            if m and v and v != "nan":
                elem_pairs.append((int(m.group(1)), v))

        if "Elements" in cfg:
            elements = [e.strip() for e in cfg["Elements"].split(",") if e.strip()]
        else:
            elements = [v for _, v in sorted(elem_pairs)]

        # Build element num→name lookup for hierarchy extraction
        _elem_num_to_name: dict[int, str] = {
            num: name_val for num, name_val in elem_pairs
        }

        # Parse Parent_Element_ID_N → build {parent: [child, ...]} groups
        _parent_pattern = _re.compile(r"^Parent_Element_ID_(\d+)$", _re.IGNORECASE)
        _parent_to_children: dict[str, list[str]] = {}
        for k, v in cfg.items():
            m = _parent_pattern.match(k)
            if m and v and v not in ("nan", "None", ""):
                elem_num = int(m.group(1))
                child_name = _elem_num_to_name.get(elem_num)
                parent_name = str(v).strip()
                if child_name and parent_name:
                    _parent_to_children.setdefault(parent_name, []).append(child_name)

        out["element_hierarchy"] = [
            {"parent": parent, "children": children}
            for parent, children in _parent_to_children.items()
        ]

        out["model"] = {
            "start_year": start_year if start_year is not None else 2025,
            "end_year": end_year if end_year is not None else 2125,
            "elements": elements,
        }

    # ---- Processes ----
    proc_df = excel_data.get("2_1_Definition_Processes")
    if proc_df is not None and "ID" in proc_df.columns:
        # Filter: require both ID and Process_Name to be non-null
        valid = proc_df.dropna(subset=["ID"])
        if "Process_Name" in valid.columns:
            valid = valid[valid["Process_Name"].notna()]
            valid = valid[
                valid["Process_Name"].astype(str).str.strip().str.lower() != "nan"
            ]
        for _, row in valid.iterrows():
            proc: dict[str, Any] = {
                "id": int(float(row["ID"])),
                "name": str(row.get("Process_Name", "")).strip(),
                "logic": str(row.get("Process_Logic", "Splitter")).strip(),
            }
            if "Stock_Configuration" in row and pd.notna(
                row.get("Stock_Configuration")
            ):
                proc["stock"] = str(row["Stock_Configuration"]).strip()
            if "TC_Configuration" in row and pd.notna(row.get("TC_Configuration")):
                proc["tc_config"] = str(row["TC_Configuration"]).strip()
            out["processes"].append(proc)

    # ---- Flows ----
    flow_df = excel_data.get("1_1_Definition_Flows")
    if flow_df is not None and "Flow_ID" in flow_df.columns:
        # Filter: require Flow_ID, Flow_Name, and both process ID columns to be non-null
        valid_flows = flow_df.dropna(subset=["Flow_ID"])
        if "Flow_Name" in valid_flows.columns:
            valid_flows = valid_flows[valid_flows["Flow_Name"].notna()]
            valid_flows = valid_flows[
                valid_flows["Flow_Name"].astype(str).str.strip().str.lower() != "nan"
            ]
        if "Flow_Output_Process_ID" in valid_flows.columns:
            valid_flows = valid_flows[valid_flows["Flow_Output_Process_ID"].notna()]
        if "Input_Process_ID" in valid_flows.columns:
            valid_flows = valid_flows[valid_flows["Input_Process_ID"].notna()]
        # Deduplicate by Flow_ID (keep first occurrence)
        seen_fids: set[str] = set()
        for _, row in valid_flows.iterrows():
            fid = str(row["Flow_ID"]).strip()
            if not fid or fid == "nan" or fid in seen_fids:
                continue
            seen_fids.add(fid)
            flow: dict[str, Any] = {"id": fid}
            if "Flow_Name" in row and pd.notna(row.get("Flow_Name")):
                flow["name"] = str(row["Flow_Name"]).strip()
            if "Flow_Output_Process_ID" in row and pd.notna(
                row.get("Flow_Output_Process_ID")
            ):
                flow["from_process"] = int(float(row["Flow_Output_Process_ID"]))
            if "Input_Process_ID" in row and pd.notna(row.get("Input_Process_ID")):
                flow["to_process"] = int(float(row["Input_Process_ID"]))
            out["flows"].append(flow)

    # ---- FOMP params (3_2_Definition_FOMP) ----
    # Normalise multiple legacy formats into {pid: {f_labile, k_labile, …}}
    # then attach as proc["fomp"] on the matching process dict.
    _fomp_raw: dict[int, dict] = {}
    fomp_df = excel_data.get("3_2_Definition_FOMP")
    if fomp_df is not None and not fomp_df.empty:
        _FOMP_PARAM_MAP = {
            "Inflow_fraction_f (Labile pool)": "f_labile",
            "decay_k1 (Labile pool)": "k_labile",
            "decay_k2 (Recalcitrant pool)": "k_recalcitrant",
            "outflow_id": "outflow_id",
            "outflow_id_2": "outflow_id_2",
            "output_carbon_id": "outflow_id",
            "output_environmental_id": "outflow_id_2",
        }
        for _, row in fomp_df.iterrows():
            # Detect format: FOMP_Parameter_ID → "P04_Inflow_fraction_f (Labile pool)"
            pid = None
            pname = None
            val = None
            if "FOMP_Parameter_ID" in fomp_df.columns and pd.notna(
                row.get("FOMP_Parameter_ID")
            ):
                raw_id = str(row["FOMP_Parameter_ID"])
                val = row.get("FOMP_Parameter_Value")
                if raw_id.startswith("P") and "_" in raw_id:
                    try:
                        pid = int(raw_id[1:].split("_")[0])
                        pname = raw_id.split("_", 1)[1]
                    except (ValueError, IndexError):
                        pass
            elif "FOMP_Parameter_type" in fomp_df.columns and pd.notna(
                row.get("FOMP_Parameter_type")
            ):
                pid_raw = row.get("Process_ID")
                pid = (
                    int(float(pid_raw))
                    if pid_raw is not None
                    and not (isinstance(pid_raw, float) and pd.isna(pid_raw))
                    else None
                )
                pname = str(row["FOMP_Parameter_type"])
                val = row.get("FOMP_Parameter_Value")
            elif "Pool_ID" in fomp_df.columns and pd.notna(row.get("Pool_ID")):
                pool_id = str(row["Pool_ID"])
                pname = str(row.get("Parameter_Name", ""))
                val = row.get("Value")
                if pool_id.startswith("P") and "_" in pool_id:
                    try:
                        pid = int(pool_id[1:].split("_")[0])
                    except (ValueError, IndexError):
                        pass
            elif "Process_ID" in fomp_df.columns and pd.notna(row.get("Process_ID")):
                pid = int(float(row["Process_ID"]))
                pname = str(row.get("Parameter_Name", ""))
                val = row.get("Value")
            if pid is None or not pname:
                continue
            yaml_key = _FOMP_PARAM_MAP.get(pname)
            if yaml_key is None:
                continue
            entry = _fomp_raw.setdefault(pid, {})
            if yaml_key in ("outflow_id", "outflow_id_2"):
                entry[yaml_key] = str(val) if pd.notna(val) else ""
            else:
                try:
                    entry[yaml_key] = float(val)
                except (ValueError, TypeError):
                    pass

    # Build pid → index in out["processes"] for fast attachment
    _pid_to_idx: dict[int, int] = {p["id"]: i for i, p in enumerate(out["processes"])}
    for pid, fomp_params in _fomp_raw.items():
        if not fomp_params:
            continue
        idx = _pid_to_idx.get(pid)
        if idx is None:
            continue
        out["processes"][idx]["fomp"] = {
            "f_labile": fomp_params.get("f_labile", 0.5),
            "k_labile": fomp_params.get("k_labile", 1.0),
            "k_recalcitrant": fomp_params.get("k_recalcitrant", 0.01),
            "outflow_id": fomp_params.get("outflow_id", ""),
            "outflow_id_2": fomp_params.get("outflow_id_2", None),
        }

    # ---- DSM params (3_1_Definition_DSM) ----
    # Only single-category is supported in the web app / YAML schema.
    # For multi-category processes we take the first (lowest DSM_material_count).
    dsm_df = excel_data.get("3_1_Definition_DSM")
    if dsm_df is not None and not dsm_df.empty:
        dsm_df = dsm_df.copy()
        # Determine pid per row: prefer Process_ID column, fall back to
        # extracting from DSM_Parameter_ID (format: "P10_DSM_Lifetime_Mean_Cat_1")
        if "Process_ID" in dsm_df.columns:
            dsm_df["_pid"] = dsm_df["Process_ID"].apply(
                lambda x: int(float(x)) if pd.notna(x) else -1
            )
        elif "DSM_Parameter_ID" in dsm_df.columns:

            def _dsm_pid(raw):
                s = str(raw).strip()
                if s.startswith("P") and "_" in s:
                    try:
                        return int(s[1:].split("_")[0])
                    except (ValueError, IndexError):
                        pass
                return -1

            dsm_df["_pid"] = dsm_df["DSM_Parameter_ID"].apply(_dsm_pid)
        else:
            dsm_df["_pid"] = -1
        dsm_df = dsm_df[dsm_df["_pid"] >= 0]

        for pid, grp in dsm_df.groupby("_pid"):
            idx = _pid_to_idx.get(pid)
            if idx is None:
                continue
            categories_out: list[dict] = []
            # New parameter-based format (DSM_Parameter_type + DSM_Value columns)
            if "DSM_Parameter_type" in grp.columns and "DSM_Value" in grp.columns:
                # Group by category number (DSM_material_count)
                if (
                    "DSM_material_count" in grp.columns
                    and grp["DSM_material_count"].notna().any()
                ):
                    cat_nums = sorted(grp["DSM_material_count"].dropna().unique())
                    cat_groups = [
                        (n, grp[grp["DSM_material_count"] == n]) for n in cat_nums
                    ]
                else:
                    cat_groups = [(1, grp)]
                for _cat_n, cat_grp in cat_groups:
                    pm: dict[str, Any] = {}
                    for _, r in cat_grp.iterrows():
                        pt = str(r.get("DSM_Parameter_type", "")).strip()
                        pv = r.get("DSM_Value")
                        if pt and pd.notna(pv):
                            pm[pt] = pv

                    def _fval(key, default=None):
                        v = pm.get(key)
                        if v is None or (isinstance(v, float) and pd.isna(v)):
                            return default
                        try:
                            return float(v)
                        except (ValueError, TypeError):
                            return default

                    categories_out.append(
                        {
                            "name": str(pm.get("DSM_Category_Name", f"Cat_{_cat_n}")),
                            "inflow_split": _fval("DSM_Inflow_Split_[%]", 1.0),
                            "lifetime_type": str(
                                pm.get("DSM_Lifetime_Type", "Normal")
                            ).strip(),
                            "lifetime_mean": _fval("DSM_Lifetime_Mean"),
                            "lifetime_std": _fval("DSM_Lifetime_StdDev"),
                            "lifetime_shape": _fval("DSM_Lifetime_Shape"),
                            "lifetime_scale": _fval("DSM_Lifetime_Scale"),
                        }
                    )
            else:
                # Old category-based format: one row per category, columns Lifetime_Mean etc.
                for _, r in grp.iterrows():

                    def _rv(col, default=None):
                        v = r.get(col)
                        if v is None or (isinstance(v, float) and pd.isna(v)):
                            return default
                        try:
                            return float(v)
                        except (ValueError, TypeError):
                            return default

                    categories_out.append(
                        {
                            "name": str(r.get("Category_Name", "Default")),
                            "inflow_split": _rv("Inflow_Split_[%]", 1.0),
                            "lifetime_type": str(
                                r.get("Lifetime_Type", "Normal")
                            ).strip()
                            if pd.notna(r.get("Lifetime_Type"))
                            else "Normal",
                            "lifetime_mean": _rv("Lifetime_Mean"),
                            "lifetime_std": _rv("Lifetime_StdDev"),
                            "lifetime_shape": _rv("Lifetime_Shape"),
                            "lifetime_scale": _rv("Lifetime_Scale"),
                        }
                    )
            if categories_out:
                out["processes"][idx]["dsm"] = {"categories": categories_out}

    # ---- Shared helpers for TC + BOM export ----
    elements = out["model"].get("elements", [])
    _active_elem_indices = list(
        range(2, len(elements) + 1)
    )  # E1=material skipped (used for BOM)
    _tc_elem_indices = list(
        range(1, len(elements) + 1)
    )  # includes E1=material (used for TCs)

    proc_id_to_name: dict[int, str] = {}
    proc_tc_config: dict[int, str] = {}  # pid → "Static" | "Dynamic" | "No TC"
    if proc_df is not None and "ID" in proc_df.columns:
        for _, row in proc_df.dropna(subset=["ID"]).iterrows():
            pid_int = int(float(row["ID"]))
            proc_id_to_name[pid_int] = str(row.get("Process_Name", "")).strip()
            if "TC_Configuration" in row.index and pd.notna(
                row.get("TC_Configuration")
            ):
                proc_tc_config[pid_int] = str(row["TC_Configuration"]).strip()

    def _safe_pid(x):
        try:
            return int(float(x))
        except (ValueError, TypeError):
            return -1

    def _extract_element_values(row, active_indices, elem_list):
        """Return {elem_name: float} for non-NaN E{n}_TC_Value[%] columns."""
        values: dict[str, Any] = {}
        for n in active_indices:
            col = f"E{n}_TC_Value[%]"
            if col in row.index and pd.notna(row[col]):
                elem_name = elem_list[n - 1] if n - 1 < len(elem_list) else f"E{n}"
                values[elem_name] = float(row[col])
        return values

    # ---- Static Transfer Coefficients ----
    static_tc_df = excel_data.get("2_2_static_TCs")
    if static_tc_df is not None and "Process_ID" in static_tc_df.columns and elements:
        tc_clean = static_tc_df[static_tc_df["Process_ID"].notna()].copy()
        tc_clean["_pid"] = tc_clean["Process_ID"].apply(_safe_pid)
        tc_clean = tc_clean[tc_clean["_pid"] >= 0]
        for pid, grp in tc_clean.groupby("_pid"):
            # Only export if process TC config agrees (or is unknown)
            if proc_tc_config.get(pid, "Static") not in ("Static", "No TC"):
                continue
            for _, row in grp.iterrows():
                fid = str(row.get("Flow_ID", "")).strip()
                if not fid or fid == "nan":
                    continue
                values = _extract_element_values(row, _tc_elem_indices, elements)
                if values:
                    out["transfer_coefficients"].append(
                        {
                            "process_id": int(pid),
                            "flow_id": fid,
                            "tc_type": "static",
                            "values": values,
                        }
                    )

    # ---- Dynamic Transfer Coefficients ----
    dyn_tc_df = excel_data.get("2_3_dynamic_TCs")
    if dyn_tc_df is not None and "Process_ID" in dyn_tc_df.columns and elements:
        dyn_clean = dyn_tc_df[dyn_tc_df["Process_ID"].notna()].copy()
        dyn_clean["_pid"] = dyn_clean["Process_ID"].apply(_safe_pid)
        dyn_clean = dyn_clean[dyn_clean["_pid"] >= 0]

        # Require a Year column
        if "Year" in dyn_clean.columns:
            dyn_clean = dyn_clean[dyn_clean["Year"].notna()].copy()
            dyn_clean["_year"] = dyn_clean["Year"].apply(
                lambda y: int(float(y)) if pd.notna(y) else -1
            )
            dyn_clean = dyn_clean[dyn_clean["_year"] > 0]

            # Group by (process_id, flow_id) then collect year points
            if "Flow_ID" not in dyn_clean.columns:
                dyn_clean["Flow_ID"] = ""
            dyn_clean["_fid"] = dyn_clean["Flow_ID"].fillna("").astype(str).str.strip()

            for (pid, fid), grp in dyn_clean.groupby(["_pid", "_fid"]):
                if not fid or fid == "nan":
                    continue
                time_series: list[dict] = []
                for year, year_grp in grp.groupby("_year"):
                    row = year_grp.iloc[0]
                    values = _extract_element_values(row, _tc_elem_indices, elements)
                    if values:
                        time_series.append({"year": int(year), "values": values})
                if time_series:
                    time_series.sort(key=lambda p: p["year"])
                    out["transfer_coefficients"].append(
                        {
                            "process_id": int(pid),
                            "flow_id": fid,
                            "tc_type": "dynamic",
                            "time_series": time_series,
                        }
                    )

    # ---- BOM Assembly ----
    bom_df = excel_data.get("3_3_Definition_BOM_Assembly")
    if bom_df is not None and "Process_ID" in bom_df.columns and elements:
        bom_clean = bom_df.dropna(subset=["Process_ID"])
        for pid_raw, grp in bom_clean.groupby(
            bom_clean["Process_ID"].apply(lambda x: int(float(x)))
        ):
            pid = int(pid_raw)
            bom_flows = []
            for _, row in grp.iterrows():
                fid = str(row.get("Flow_ID", "")).strip()
                flow_type = str(row.get("Output_flow_type", "")).strip()
                if not fid or fid == "nan":
                    continue
                fractions: dict[str, float] = {}
                if flow_type == "target_Product":
                    for n in _active_elem_indices:
                        col = f"E{n}_TC_Value[%]"
                        if col in row.index and pd.notna(row[col]):
                            elem_name = (
                                elements[n - 1] if n - 1 < len(elements) else f"E{n}"
                            )
                            fractions[elem_name] = float(row[col])
                bom_flows.append(
                    {
                        "flow_id": fid,
                        "output_flow_type": flow_type,
                        "fractions": fractions,
                    }
                )
            if bom_flows:
                out["bom_assembly"].append(
                    {
                        "process_id": pid,
                        "process_name": proc_id_to_name.get(pid, ""),
                        "flows": bom_flows,
                    }
                )

    # ---- FlowCap params (3_4_Definition_FlowCap) ----
    # Attach a per-process flowcap block to the matching process dict.
    # Excel layout: Capped_Output rows carry Process_ID, Flow_ID, Year and the
    # cap value (column "Flow"); a single Overflow row names the overflow flow.
    # Output_flow_type can carry stray whitespace/tabs from the template, so we
    # strip before matching. Without this block, importing an Excel silently
    # dropped the cap (the inverse of the YAML->engine bridge).
    fc_df = excel_data.get("3_4_Definition_FlowCap")
    if fc_df is not None and not fc_df.empty and "Flow_ID" in fc_df.columns:
        fc_df = fc_df.copy()
        fc_df.columns = [str(c).strip() for c in fc_df.columns]
        cap_col = next(
            (c for c in ("Flow", "Cap_Value[UoM]", "Cap") if c in fc_df.columns), None
        )
        has_pid = "Process_ID" in fc_df.columns
        for _, row in fc_df.iterrows():
            fid = str(row.get("Flow_ID", "")).strip()
            if not fid or fid.lower() == "nan" or set(fid) <= {"F", "_"}:
                continue  # blank / filler row (e.g. "F__")
            pid = None
            if has_pid and pd.notna(row.get("Process_ID")):
                try:
                    pid = int(float(row["Process_ID"]))
                except (ValueError, TypeError):
                    pid = None
            if pid is None:  # infer from flow id F_<from>_<to>
                parts = fid.split("_")
                if len(parts) >= 2 and parts[1].isdigit():
                    pid = int(parts[1])
            idx = _pid_to_idx.get(pid)
            if idx is None:
                continue
            block = out["processes"][idx].setdefault(
                "flowcap",
                {
                    "capped_flow_id": "",
                    "overflow_flow_id": "",
                    "cap_series": {},
                    "cap_tc_id": "",
                },
            )
            ftype = str(row.get("Output_flow_type", "")).strip().lower()
            if ftype.startswith("overflow"):
                block["overflow_flow_id"] = fid
            else:  # Capped_Output (default)
                block["capped_flow_id"] = fid
                # Cap_TC_ID (ParameterDict key for scenario/MC cap switching)
                # sits on the Capped_Output rows — mirror the engine loader,
                # which otherwise loses it on Excel→YAML round-trips.
                raw_tc = row.get("Cap_TC_ID")
                if pd.notna(raw_tc):
                    raw_tc = str(raw_tc).strip()
                    if raw_tc and raw_tc.lower() not in ("nan", "n.a.", "n/a"):
                        block["cap_tc_id"] = raw_tc
                if cap_col is not None and pd.notna(row.get(cap_col)):
                    try:
                        cap = float(str(row[cap_col]).replace(",", "."))
                    except (ValueError, TypeError):
                        cap = None
                    if cap is not None:
                        yr = row.get("Year")
                        try:
                            yr = int(float(yr)) if pd.notna(yr) else 0
                        except (ValueError, TypeError):
                            yr = 0
                        block["cap_series"][yr] = cap
        # discard incomplete blocks (no capped flow -> nothing to cap)
        for _p in out["processes"]:
            if "flowcap" in _p and not _p["flowcap"].get("capped_flow_id"):
                del _p["flowcap"]

    # ---- LFG params (3_3_Definition_LFG) ----
    # Mirror load_lfg_parameters: site scalars (MCF/DOCf/F_CH4/OX/phi/f_capture
    # + outflow IDs) and per-fraction rows whose LFG_Parameter_ID carries a
    # _j{n} suffix. Map the Excel parameter names onto the LfgParams field names.
    lfg_df = excel_data.get("3_3_Definition_LFG")
    if (
        lfg_df is not None
        and not lfg_df.empty
        and "LFG_Parameter_type" in lfg_df.columns
        and "LFG_Parameter_Value" in lfg_df.columns
    ):
        _LFG_MAP = {  # excel type -> LfgParams field
            "MCF": "mcf",
            "DOCf": "doc_f",
            "F": "f_ch4",
            "F_CH4": "f_ch4",
            "OX": "ox",
            "Φ": "phi",
            "φ": "phi",
            "phi": "phi",
            "f": "f_capture",
            "f_capture": "f_capture",
            "output_CH4_id": "outflow_ch4_id",
            "outflow_ch4_id": "outflow_ch4_id",
            "output_CO2_id": "outflow_co2_id",
            "outflow_co2_id": "outflow_co2_id",
            "output_leaching": "outflow_leachate_id",
            "outflow_leachate_id": "outflow_leachate_id",
        }
        _SITE = {"mcf", "doc_f", "f_ch4", "ox", "phi", "f_capture"}
        _ID_FIELDS = {"outflow_ch4_id", "outflow_co2_id", "outflow_leachate_id"}
        _FRAC = {
            "Waste_Fraction_j": "name",
            "k_j": "k_j",
            "DOC_j": "doc_j",
            "f_input_j": "f_input_j",
            "f_ash_j": "f_ash_j",
        }
        _jpat = re.compile(r"_j(\d+)\b", re.IGNORECASE)
        has_pid = "Process_ID" in lfg_df.columns
        has_id = "LFG_Parameter_ID" in lfg_df.columns
        _site: dict[int, dict] = {}
        _fracs: dict[int, dict] = {}
        for _, row in lfg_df.iterrows():
            ptype = row.get("LFG_Parameter_type")
            if pd.isna(ptype):
                continue
            ptype = str(ptype).strip()
            pval = row.get("LFG_Parameter_Value")
            pidv = row.get("LFG_Parameter_ID") if has_id else None
            pid = None
            if has_pid and pd.notna(row.get("Process_ID")):
                try:
                    pid = int(float(row["Process_ID"]))
                except (ValueError, TypeError):
                    pid = None
            if pid is None and pd.notna(pidv):
                s = str(pidv).strip()
                if s.startswith("P") and "_" in s:
                    try:
                        pid = int(s[1:].split("_")[0])
                    except (ValueError, IndexError):
                        pid = None
            if pid is None or pid not in _pid_to_idx:
                continue
            fidx = None
            if pd.notna(pidv):
                m = _jpat.search(str(pidv))
                if m:
                    fidx = int(m.group(1))
            if ptype in _FRAC and fidx is not None:
                _fracs.setdefault(pid, {}).setdefault(fidx, {})[_FRAC[ptype]] = pval
                continue
            field = _LFG_MAP.get(ptype)
            if field in _ID_FIELDS:
                if pd.notna(pval):
                    _site.setdefault(pid, {})[field] = str(pval).strip()
            elif field in _SITE and pd.notna(pval):
                try:
                    _site.setdefault(pid, {})[field] = float(pval)
                except (ValueError, TypeError):
                    pass
        for pid in set(_site) | set(_fracs):
            idx = _pid_to_idx.get(pid)
            if idx is None:
                continue
            block = dict(_site.get(pid, {}))
            frac_list = []
            for fi in sorted(_fracs.get(pid, {})):
                fd = _fracs[pid][fi]

                def _f(k, d=0.0):
                    v = fd.get(k)
                    if v is None or (isinstance(v, float) and pd.isna(v)):
                        return d
                    try:
                        return float(v)
                    except (ValueError, TypeError):
                        return d

                frac_list.append(
                    {
                        "name": str(fd.get("name", f"Fraction_{fi}")).strip(),
                        "k_j": _f("k_j"),
                        "doc_j": _f("doc_j"),
                        "f_input_j": _f("f_input_j"),
                        "f_ash_j": _f("f_ash_j"),
                    }
                )
            if frac_list:
                block["fractions"] = frac_list
            if block:
                out["processes"][idx]["lfg"] = block

    # ---- Initial Stock (2_4_Initial_Stock) ----
    # Tall format Process_ID / IS_Parameter_type / IS_Parameter_Value. Mirrors
    # load_initial_stock_parameters: material quantity, Basic_E{n}_Fraction[%]
    # element composition (absolute), and Cohort_* params. Top-level list.
    is_df = excel_data.get("2_4_Initial_Stock")
    if (
        is_df is not None
        and not is_df.empty
        and {"Process_ID", "IS_Parameter_type", "IS_Parameter_Value"}
        <= set(is_df.columns)
    ):

        def _isf(v):
            if pd.isna(v):
                return None
            try:
                return (
                    float(str(v).replace(",", ".")) if isinstance(v, str) else float(v)
                )
            except (ValueError, TypeError):
                return None

        # element -> candidate IS_Parameter_type names (1-based id, skip material)
        elem_candidates: dict[str, list[str]] = {}
        for ei, elem in enumerate(elements):
            if elem == "material":
                continue
            eid = ei + 1
            elem_candidates[elem] = [
                f"Basic_E{eid}_Fraction[%]",
                f"IS_E{eid}_Fraction[%]",
                f"IS_E{eid}_[%]({elem})",
                f"IS_E{eid}[%]",
                f"IS_E{eid}_[%]",
                f"IS_{elem}[%]",
            ]
        _by_pid: dict[int, dict] = {}
        for _, row in is_df.dropna(
            subset=["Process_ID", "IS_Parameter_type"]
        ).iterrows():
            try:
                pid = int(float(row["Process_ID"]))
            except (ValueError, TypeError):
                continue
            pname = str(row["IS_Parameter_type"]).strip()
            praw = row["IS_Parameter_Value"]
            pnum = _isf(praw)
            entry = _by_pid.setdefault(pid, {"process_id": pid, "composition": {}})
            if pname in ("IS_material_quantity[UoM]", "Basic_Material_Quantity[UoM]"):
                if pnum is not None:
                    entry["material_quantity"] = pnum
            elif pname == "Cohort_Age_Distribution_Type":
                entry["cohort_age_distribution_type"] = str(praw).strip()
            elif pname == "Cohort_Mean_Age[years]":
                if pnum is not None:
                    entry["cohort_mean_age"] = pnum
            elif pname == "Cohort_StdDev_Age[years]":
                if pnum is not None:
                    entry["cohort_std_age"] = pnum
            elif pname == "Cohort_Max_Age[years]":
                if pnum is not None:
                    entry["cohort_max_age"] = int(pnum)
            elif pname == "Cohort_Decay_Constant[years]":
                if pnum is not None:
                    entry["cohort_decay_constant"] = pnum
            else:
                for elem, cands in elem_candidates.items():
                    if pname in cands and pnum is not None:
                        entry["composition"][elem] = pnum
                        break
        for pid in sorted(_by_pid):
            e = _by_pid[pid]
            if e.get("material_quantity", 0) > 0 or e["composition"]:
                out["initial_stocks"].append(e)

    # ---- Flow Compositions ----
    # Reads elemental fractions from 1_1_Definition_Flows for every flow that
    # has non-zero fraction data.  New format: Flow_E{n}_Fraction[%] (n=1 for
    # material, n=2 for WC, …).  Old format: Flow_WC[%], Flow_DM[%], Flow_CC_DM[%].
    # Values are expected to be 0–1 fractions (consistent with TC conventions).
    if flow_df is not None and "Flow_ID" in flow_df.columns and elements:
        _new_frac_cols = [f"Flow_E{n + 1}_Fraction[%]" for n in range(len(elements))]
        _has_new_frac = any(c in flow_df.columns for c in _new_frac_cols)
        _old_frac_map = {
            "WC": "Flow_WC[%]",
            "DM": "Flow_DM[%]",
            "CC": "Flow_CC_DM[%]",
            "TC": "Flow_CC_DM[%]",
        }

        for _, row in flow_df.iterrows():
            fid = str(row.get("Flow_ID", "")).strip()
            if not fid or fid == "nan":
                continue

            comp: dict[str, float] = {}
            if _has_new_frac:
                for n, elem in enumerate(elements):
                    col = f"Flow_E{n + 1}_Fraction[%]"
                    if col in row.index and pd.notna(row[col]):
                        val = float(row[col])
                        if val != 0.0:
                            comp[elem] = val
            else:
                for elem in elements:
                    col = _old_frac_map.get(elem, f"Flow_{elem}[%]")
                    if col in row.index and pd.notna(row[col]):
                        val = float(row[col])
                        if val != 0.0:
                            comp[elem] = val

            if comp:
                out["flow_compositions"].append({"flow_id": fid, "values": comp})

    # ---- Flow Time-Series Data (1_2_Data_Flows) ----
    flow_data_df = excel_data.get("1_2_Data_Flows")
    if (
        flow_data_df is not None
        and "Flow_ID" in flow_data_df.columns
        and "Flow_Data_Year" in flow_data_df.columns
    ):
        material_col = (
            "E1_value"
            if "E1_value" in flow_data_df.columns
            else "Flow_Material"
            if "Flow_Material" in flow_data_df.columns
            else None
        )
        if material_col:
            flow_data_acc: dict[str, dict[int, float]] = {}
            for _, row in flow_data_df.iterrows():
                fid = str(row.get("Flow_ID", "")).strip()
                year_raw = row.get("Flow_Data_Year")
                val_raw = row.get(material_col)
                if not fid or fid == "nan" or pd.isna(year_raw):
                    continue
                try:
                    year = int(float(year_raw))
                    val = float(val_raw) if pd.notna(val_raw) else 0.0
                except (ValueError, TypeError):
                    continue
                flow_data_acc.setdefault(fid, {})[year] = val
            for fid, yv in sorted(flow_data_acc.items()):
                out["flow_data"].append(
                    {"flow_id": fid, "element": "material", "values": yv}
                )

    # ---- Scenarios ----
    _scen_sheet = next(
        (s for s in ("5_1_Scenario_Manager", "Scenario Manager") if s in excel_data),
        None,
    )
    if _scen_sheet:
        df_s = excel_data[_scen_sheet].copy()

        # Find the real header row (some sheets have description rows above)
        _hdr = 0
        for _i in range(min(10, len(df_s))):
            if "Scenario_Name" in df_s.iloc[_i].values:
                _hdr = _i
                break
        if _hdr:
            df_s.columns = df_s.iloc[_hdr]
            df_s = df_s.iloc[_hdr + 1 :].reset_index(drop=True)

        # Normalise column aliases
        df_s = df_s.rename(
            columns={
                "Parameter_ID": "Parameter_Name",
                "Scenario_Operation": "Operation",
            }
        )

        try:
            df_s = df_s.dropna(subset=["Scenario_Name", "Parameter_Name"])
        except KeyError:
            df_s = pd.DataFrame()

        _scen_acc: dict[str, list] = {}
        for _, row in df_s.iterrows():
            sname = str(row.get("Scenario_Name", "")).strip()
            pname = str(row.get("Parameter_Name", "")).strip()
            if not sname or not pname or sname == "nan" or pname == "nan":
                continue

            op_raw = row.get("Operation", "replace")
            op = str(op_raw).strip().lower() if pd.notna(op_raw) else "replace"
            if op not in ("replace", "multiply", "add"):
                op = "replace"

            nv_raw = row.get("New_Value") if "New_Value" in row else row.get("Value")
            try:
                new_value = float(nv_raw) if pd.notna(nv_raw) else 0.0
            except (ValueError, TypeError):
                new_value = 0.0

            def _sy(k):
                v = row.get(k)
                if v is None or (isinstance(v, float) and pd.isna(v)):
                    return None
                try:
                    return int(v)
                except (ValueError, TypeError):
                    return None

            mod = {
                "parameter_name": pname,
                "parameter_type": str(row.get("Parameter_Type", "") or "").strip(),
                "operation": op,
                "new_value": new_value,
                "start_year": _sy("start_year") or _sy("MC_Start_Year"),
                "end_year": _sy("end_year") or _sy("MC_End_Year"),
            }
            _scen_acc.setdefault(sname, []).append(mod)

        for sname, mods in _scen_acc.items():
            out["scenarios"].append({"name": sname, "modifications": mods})

    # ---- MC Parameters ----
    _mc_sheet = "4_1_Uncertainty_Parameters"
    if _mc_sheet in excel_data:
        df_mc = excel_data[_mc_sheet].copy()
        _id_col = (
            "MC_Parameter_ID"
            if "MC_Parameter_ID" in df_mc.columns
            else "Parameter_Name"
        )
        df_mc = df_mc.dropna(subset=[_id_col])

        def _flt(v) -> Any:
            if v is None or (isinstance(v, float) and pd.isna(v)):
                return None
            try:
                return float(v)
            except (ValueError, TypeError):
                return None

        def _int(v) -> Any:
            if v is None or (isinstance(v, float) and pd.isna(v)):
                return None
            try:
                return int(v)
            except (ValueError, TypeError):
                return None

        _op_col = "MC_Operation" if "MC_Operation" in df_mc.columns else "Operation"
        _sel_col = "MC_Parameter_Selection"

        for _, row in df_mc.iterrows():
            param_id = str(row[_id_col]).strip()
            if not param_id or param_id == "nan":
                continue

            # enabled: MC_Parameter_Selection column present and non-empty
            if _sel_col in df_mc.columns:
                sel = row.get(_sel_col)
                enabled = pd.notna(sel) and str(sel).strip() != ""
            else:
                enabled = True

            dist_raw = row.get("Distribution_Type", "normal")
            distribution = (
                str(dist_raw).lower().strip() if pd.notna(dist_raw) else "normal"
            )

            op_raw = row.get(_op_col, "set")
            operation = str(op_raw).strip().lower() if pd.notna(op_raw) else "set"
            if operation == "replace":
                operation = "set"
            if operation not in ("set", "multiply", "add"):
                operation = "set"

            start_year = _int(row.get("MC_Start_Year")) or _int(row.get("start_year"))
            end_year = _int(row.get("MC_End_Year")) or _int(row.get("end_year"))

            flow_group_raw = row.get("MC_Flow_Group")
            flow_group = (
                str(flow_group_raw).strip()
                if pd.notna(flow_group_raw) and str(flow_group_raw).strip()
                else None
            )

            out["mc_parameters"].append(
                {
                    "parameter_id": param_id,
                    "enabled": enabled,
                    "distribution": distribution,
                    "mean": _flt(row.get("Mean")),
                    "std": _flt(row.get("StdDev")),
                    "min": _flt(row.get("Min")),
                    "max": _flt(row.get("Max")),
                    "mode": _flt(row.get("Mode")),
                    "operation": operation,
                    "start_year": start_year,
                    "end_year": end_year,
                    "flow_group": flow_group,
                }
            )

    return out
