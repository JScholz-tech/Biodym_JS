# -*- coding: utf-8 -*-
"""Unit tests for 02_src/systemdefiner/yaml_schema.py :: model_to_yaml()."""
from __future__ import annotations

import math

import pandas as pd
import pytest

from systemdefiner.yaml_schema import model_to_yaml


# ── Helpers ───────────────────────────────────────────────────────────────────

def _cfg_df_new(start=2015, end=2040, elements=("material", "WC", "DM", "TC")):
    """Build 0_Configuration sheet in new format (Setting_Name column)."""
    rows = [
        {"Setting_Name": "Start_Year", "Value": start},
        {"Setting_Name": "End_Year", "Value": end},
    ]
    for i, elem in enumerate(elements, 1):
        rows.append({"Setting_Name": f"Element_ID_{i}", "Value": elem})
    return pd.DataFrame(rows)


def _cfg_df_old(start=2015, end=2040, elements=("material", "WC", "DM", "TC")):
    """Build 0_Configuration sheet in old format (Parameter column)."""
    return pd.DataFrame([
        {"Parameter": "Start_Year", "Value": start},
        {"Parameter": "End_Year", "Value": end},
        {"Parameter": "Elements", "Value": ", ".join(elements)},
    ])


def _proc_df(rows):
    return pd.DataFrame([
        {"ID": r["id"], "Process_Name": r["name"], "Process_Logic": r["logic"],
         "Stock_Configuration": r.get("stock", "No_Stock")}
        for r in rows
    ])


def _flow_df(rows):
    return pd.DataFrame([
        {"Flow_ID": r["id"], "Flow_Name": r["name"],
         "Flow_Output_Process_ID": r["from"], "Input_Process_ID": r["to"]}
        for r in rows
    ])


# ── 0_Configuration parsing ───────────────────────────────────────────────────

class TestConfigParsing:
    def test_new_format_years(self):
        result = model_to_yaml({"0_Configuration": _cfg_df_new(2015, 2040)})
        assert result["model"]["start_year"] == 2015
        assert result["model"]["end_year"] == 2040

    def test_new_format_elements_in_order(self):
        result = model_to_yaml({"0_Configuration": _cfg_df_new(elements=["material", "WC", "DM", "TC"])})
        assert result["model"]["elements"] == ["material", "WC", "DM", "TC"]

    def test_old_format_years(self):
        result = model_to_yaml({"0_Configuration": _cfg_df_old(2020, 2120)})
        assert result["model"]["start_year"] == 2020
        assert result["model"]["end_year"] == 2120

    def test_old_format_elements_comma_string(self):
        result = model_to_yaml({"0_Configuration": _cfg_df_old(elements=["material", "WC"])})
        assert result["model"]["elements"] == ["material", "WC"]

    def test_years_are_integers(self):
        result = model_to_yaml({"0_Configuration": _cfg_df_new(2025, 2125)})
        assert isinstance(result["model"]["start_year"], int)
        assert isinstance(result["model"]["end_year"], int)

    def test_missing_sheet_returns_empty_model(self):
        result = model_to_yaml({})
        assert result["model"] == {}

    def test_nan_value_rows_skipped(self):
        df = _cfg_df_new()
        # Inject a row with NaN value — should not crash or add to elements
        nan_row = pd.DataFrame([{"Setting_Name": "Element_ID_99", "Value": float("nan")}])
        df = pd.concat([df, nan_row], ignore_index=True)
        result = model_to_yaml({"0_Configuration": df})
        assert "nan" not in result["model"]["elements"]
        assert len(result["model"]["elements"]) == 4  # only the real 4


# ── Process filtering ─────────────────────────────────────────────────────────

class TestProcessFiltering:
    def test_real_processes_imported(self):
        procs = [
            {"id": 0, "name": "Input", "logic": "Input"},
            {"id": 1, "name": "Soil", "logic": "FOMP"},
        ]
        result = model_to_yaml({"2_1_Definition_Processes": _proc_df(procs)})
        assert len(result["processes"]) == 2

    def test_nan_name_rows_filtered(self):
        rows = [
            {"ID": 1, "Process_Name": "Real", "Process_Logic": "Splitter", "Stock_Configuration": "No_Stock"},
            {"ID": 13, "Process_Name": float("nan"), "Process_Logic": "Splitter", "Stock_Configuration": "No_Stock"},
            {"ID": 14, "Process_Name": float("nan"), "Process_Logic": "Splitter", "Stock_Configuration": "No_Stock"},
        ]
        result = model_to_yaml({"2_1_Definition_Processes": pd.DataFrame(rows)})
        assert len(result["processes"]) == 1
        assert result["processes"][0]["name"] == "Real"

    def test_all_logic_types_preserved(self):
        procs = [
            {"id": i, "name": f"P{i}", "logic": logic}
            for i, logic in enumerate([
                "Input", "Output", "Splitter", "Transformer",
                "DSM", "FOMP", "LFG", "BOM_Assembler", "Pass-through", "FlowCap"
            ])
        ]
        result = model_to_yaml({"2_1_Definition_Processes": _proc_df(procs)})
        logics = {p["logic"] for p in result["processes"]}
        assert "FlowCap" in logics
        assert "Output" in logics

    def test_stock_configuration_preserved(self):
        rows = pd.DataFrame([
            {"ID": 1, "Process_Name": "DSM node", "Process_Logic": "DSM",
             "Stock_Configuration": "Stock_with_InitialStock_Cohort"}
        ])
        result = model_to_yaml({"2_1_Definition_Processes": rows})
        assert result["processes"][0]["stock"] == "Stock_with_InitialStock_Cohort"


# ── Flow filtering ────────────────────────────────────────────────────────────

class TestFlowFiltering:
    def test_real_flows_imported(self):
        flows = [
            {"id": "F_00_01", "name": "Input flow", "from": 0, "to": 1},
            {"id": "F_01_02", "name": "Soil out", "from": 1, "to": 2},
        ]
        result = model_to_yaml({"1_1_Definition_Flows": _flow_df(flows)})
        assert len(result["flows"]) == 2

    def test_nan_name_flows_filtered(self):
        rows = pd.DataFrame([
            {"Flow_ID": "F_00_01", "Flow_Name": "Real", "Flow_Output_Process_ID": 0.0, "Input_Process_ID": 1.0},
            {"Flow_ID": "F_13_13", "Flow_Name": float("nan"), "Flow_Output_Process_ID": float("nan"), "Input_Process_ID": float("nan")},
            {"Flow_ID": "F_13_13", "Flow_Name": float("nan"), "Flow_Output_Process_ID": float("nan"), "Input_Process_ID": float("nan")},
        ])
        result = model_to_yaml({"1_1_Definition_Flows": rows})
        assert len(result["flows"]) == 1
        assert result["flows"][0]["id"] == "F_00_01"

    def test_duplicate_flow_ids_deduplicated(self):
        rows = pd.DataFrame([
            {"Flow_ID": "F_01_02", "Flow_Name": "First", "Flow_Output_Process_ID": 1.0, "Input_Process_ID": 2.0},
            {"Flow_ID": "F_01_02", "Flow_Name": "Duplicate", "Flow_Output_Process_ID": 1.0, "Input_Process_ID": 2.0},
        ])
        result = model_to_yaml({"1_1_Definition_Flows": rows})
        assert len(result["flows"]) == 1
        assert result["flows"][0]["name"] == "First"

    def test_from_to_process_ids_are_ints(self):
        flows = [{"id": "F_00_01", "name": "f", "from": 0, "to": 1}]
        result = model_to_yaml({"1_1_Definition_Flows": _flow_df(flows)})
        assert isinstance(result["flows"][0]["from_process"], int)
        assert isinstance(result["flows"][0]["to_process"], int)


# ── Transfer Coefficients ─────────────────────────────────────────────────────

class TestTransferCoefficients:
    def _tc_df(self, rows):
        return pd.DataFrame(rows)

    def test_tc_values_mapped_to_element_names(self):
        cfg = {"0_Configuration": _cfg_df_new(elements=["material", "WC", "DM"])}
        tc = self._tc_df([
            {"Process_ID": 1, "Flow_ID": "F_01_02",
             "E2_TC_Value[%]": 0.3, "E3_TC_Value[%]": 0.7}
        ])
        result = model_to_yaml({**cfg, "2_2_static_TCs": tc})
        assert len(result["transfer_coefficients"]) == 1
        tc_entry = result["transfer_coefficients"][0]
        assert tc_entry["process_id"] == 1
        assert tc_entry["flow_id"] == "F_01_02"
        values = tc_entry["values"]
        assert values["WC"] == pytest.approx(0.3)
        assert values["DM"] == pytest.approx(0.7)
        # E1_TC_Value[%] not in data → material must not appear in values
        assert "material" not in values

    def test_splitter_tc_read_from_e1_material_column(self):
        # Regression: E1_TC_Value[%] (material) was skipped when _active_elem_indices
        # started at 2.  Splitter processes only fill E1, so their TCs were silently
        # dropped.  After the fix (_tc_elem_indices starts at 1), material is read.
        cfg = {"0_Configuration": _cfg_df_new(elements=["material", "WC", "DM", "TC"])}
        tc = self._tc_df([
            {"Process_ID": 2, "Flow_ID": "F_02_03", "E1_TC_Value[%]": 0.4},
            {"Process_ID": 2, "Flow_ID": "F_02_04", "E1_TC_Value[%]": 0.6},
        ])
        result = model_to_yaml({**cfg, "2_2_static_TCs": tc})
        assert len(result["transfer_coefficients"]) == 2
        by_flow = {t["flow_id"]: t for t in result["transfer_coefficients"]}
        assert by_flow["F_02_03"]["values"]["material"] == pytest.approx(0.4)
        assert by_flow["F_02_04"]["values"]["material"] == pytest.approx(0.6)

    def test_all_nan_tc_row_skipped(self):
        cfg = {"0_Configuration": _cfg_df_new(elements=["material", "WC"])}
        tc = self._tc_df([
            {"Process_ID": 1, "Flow_ID": "F_01_02",
             "E2_TC_Value[%]": float("nan")}
        ])
        result = model_to_yaml({**cfg, "2_2_static_TCs": tc})
        assert result["transfer_coefficients"] == []

    def test_nan_flow_id_in_tc_skipped(self):
        cfg = {"0_Configuration": _cfg_df_new(elements=["material", "WC"])}
        tc = self._tc_df([
            {"Process_ID": 1, "Flow_ID": float("nan"), "E2_TC_Value[%]": 0.5}
        ])
        result = model_to_yaml({**cfg, "2_2_static_TCs": tc})
        assert result["transfer_coefficients"] == []

    def test_no_elements_means_no_tcs(self):
        tc = self._tc_df([{"Process_ID": 1, "Flow_ID": "F_01_02", "E2_TC_Value[%]": 0.5}])
        result = model_to_yaml({"2_2_static_TCs": tc})
        assert result["transfer_coefficients"] == []
