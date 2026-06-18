# -*- coding: utf-8 -*-
"""Shared fixtures for config web app tests."""
from __future__ import annotations

import io
import sys
from pathlib import Path

import pandas as pd
import pytest
from starlette.testclient import TestClient

# Ensure tools/ is importable (yaml_schema)
_ROOT = Path(__file__).parent.parent.parent
# Project root must be on path for `app` and `tools` packages
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(_ROOT / "tools"))


# ── Isolation: redirect storage to a tmp directory ───────────────────────────

@pytest.fixture(autouse=True)
def isolated_case_studies(tmp_path, monkeypatch):
    """Patch storage.CASE_STUDIES_DIR so every test uses a fresh temp dir."""
    import app.storage as storage_mod
    monkeypatch.setattr(storage_mod, "CASE_STUDIES_DIR", tmp_path / "case_studies")
    return tmp_path / "case_studies"


@pytest.fixture
def client():
    """Synchronous TestClient for the FastAPI app."""
    from systemdefiner.main import app
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture
def client_raises():
    """TestClient that re-raises server exceptions (for checking 500s explicitly)."""
    from systemdefiner.main import app
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


# ── Synthetic Excel builder ───────────────────────────────────────────────────

def make_excel_bytes(
    *,
    start_year: int = 2025,
    end_year: int = 2125,
    elements: list[str] | None = None,
    use_setting_name_col: bool = True,
    processes: list[dict] | None = None,
    flows: list[dict] | None = None,
    include_nan_processes: bool = False,
    include_placeholder_flows: bool = False,
) -> bytes:
    """Build a minimal BioDYM Excel workbook in memory and return raw bytes."""
    if elements is None:
        elements = ["material", "WC", "DM", "TC"]
    if processes is None:
        processes = [
            {"id": 0, "name": "Input", "logic": "Input"},
            {"id": 1, "name": "Soil", "logic": "FOMP", "stock": "Stock"},
            {"id": 2, "name": "Output", "logic": "Output"},
        ]
    if flows is None:
        flows = [
            {"id": "F_00_01", "name": "Input flow", "from": 0, "to": 1},
            {"id": "F_01_02", "name": "Soil output", "from": 1, "to": 2},
        ]

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        # --- 0_Configuration ---
        if use_setting_name_col:
            cfg_rows = [
                {"Setting_Name": "Start_Year", "Value": start_year},
                {"Setting_Name": "End_Year", "Value": end_year},
            ]
            for i, elem in enumerate(elements, 1):
                cfg_rows.append({"Setting_Name": f"Element_ID_{i}", "Value": elem})
            pd.DataFrame(cfg_rows).to_excel(writer, sheet_name="0_Configuration", index=False)
        else:
            cfg_rows = [
                {"Parameter": "Start_Year", "Value": start_year},
                {"Parameter": "End_Year", "Value": end_year},
                {"Parameter": "Elements", "Value": ", ".join(elements)},
            ]
            pd.DataFrame(cfg_rows).to_excel(writer, sheet_name="0_Configuration", index=False)

        # --- 2_1_Definition_Processes ---
        proc_rows = [
            {
                "ID": p["id"],
                "Process_Name": p["name"],
                "Process_Logic": p["logic"],
                "Stock_Configuration": p.get("stock", "No_Stock"),
            }
            for p in processes
        ]
        if include_nan_processes:
            # Template placeholder rows with NaN name — should be filtered
            for i in range(13, 16):
                proc_rows.append({"ID": i, "Process_Name": float("nan"), "Process_Logic": "Splitter", "Stock_Configuration": "No_Stock"})
        pd.DataFrame(proc_rows).to_excel(writer, sheet_name="2_1_Definition_Processes", index=False)

        # --- 1_1_Definition_Flows ---
        flow_rows = [
            {
                "Flow_ID": f["id"],
                "Flow_Name": f["name"],
                "Flow_Output_Process_ID": f["from"],
                "Input_Process_ID": f["to"],
            }
            for f in flows
        ]
        if include_placeholder_flows:
            # Duplicate placeholder flows — should be filtered/deduplicated
            for _ in range(3):
                flow_rows.append({
                    "Flow_ID": "F_13_13",
                    "Flow_Name": float("nan"),
                    "Flow_Output_Process_ID": float("nan"),
                    "Input_Process_ID": float("nan"),
                })
        pd.DataFrame(flow_rows).to_excel(writer, sheet_name="1_1_Definition_Flows", index=False)

    buf.seek(0)
    return buf.read()


@pytest.fixture
def minimal_excel() -> bytes:
    return make_excel_bytes()


@pytest.fixture
def excel_with_nan_rows() -> bytes:
    return make_excel_bytes(include_nan_processes=True, include_placeholder_flows=True)


@pytest.fixture
def excel_new_format() -> bytes:
    """New Excel format: Setting_Name column, Element_ID_N rows."""
    return make_excel_bytes(use_setting_name_col=True)


@pytest.fixture
def excel_old_format() -> bytes:
    """Old Excel format: Parameter column, Elements comma-string."""
    return make_excel_bytes(use_setting_name_col=False)
