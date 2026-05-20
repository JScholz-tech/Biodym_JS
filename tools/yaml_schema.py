# -*- coding: utf-8 -*-
"""YAML schema utilities for BioDYM model configuration.

Provides helpers for validating, saving, and loading BioDYM model configs
as human-readable YAML files suitable for version control.
"""

from __future__ import annotations

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
    text = yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)
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

    out: dict[str, Any] = {
        "meta": {
            "source_file": str(source_file),
            "exported_at": datetime.now().isoformat(timespec="seconds"),
        },
        "model": {},
        "processes": [],
        "flows": [],
    }

    # ---- Model dimensions from 0_Configuration ----
    cfg_df = excel_data.get("0_Configuration")
    if cfg_df is not None:
        cfg: dict[str, str] = {}
        for _, row in cfg_df.iterrows():
            key = str(row.get("Parameter", "")).strip()
            val = str(row.get("Value", "")).strip()
            if key and key != "nan":
                cfg[key] = val

        elements_raw = cfg.get("Elements", "")
        elements = [e.strip() for e in elements_raw.split(",") if e.strip()]
        start_raw = cfg.get("Start_Year", "")
        end_raw = cfg.get("End_Year", "")
        out["model"] = {
            "start_year": int(start_raw) if start_raw.isdigit() else start_raw,
            "end_year": int(end_raw) if end_raw.isdigit() else end_raw,
            "elements": elements,
        }

    # ---- Processes ----
    proc_df = excel_data.get("2_1_Definition_Processes")
    if proc_df is not None and "Process_ID" in proc_df.columns:
        for _, row in proc_df.dropna(subset=["Process_ID"]).iterrows():
            proc: dict[str, Any] = {
                "id": int(float(row["Process_ID"])),
                "name": str(row.get("Process_Name", "")).strip(),
                "logic": str(row.get("Process_Logic", "")).strip(),
            }
            if "Stock_Configuration" in row and pd.notna(row["Stock_Configuration"]):
                proc["stock"] = str(row["Stock_Configuration"]).strip()
            out["processes"].append(proc)

    # ---- Flows ----
    flow_df = excel_data.get("1_1_Definition_Flows")
    if flow_df is not None and "Flow_ID" in flow_df.columns:
        for _, row in flow_df.dropna(subset=["Flow_ID"]).iterrows():
            flow: dict[str, Any] = {
                "id": str(row["Flow_ID"]).strip(),
            }
            if "Flow_Name" in row and pd.notna(row.get("Flow_Name")):
                flow["name"] = str(row["Flow_Name"]).strip()
            if "From_Process" in row and pd.notna(row.get("From_Process")):
                flow["from_process"] = int(float(row["From_Process"]))
            if "To_Process" in row and pd.notna(row.get("To_Process")):
                flow["to_process"] = int(float(row["To_Process"]))
            out["flows"].append(flow)

    return out
