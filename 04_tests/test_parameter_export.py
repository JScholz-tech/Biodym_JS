# -*- coding: utf-8 -*-
"""
Tests for the parameter overview export (reporting/parameter_export.py).

Builds unsolved MFA systems from tutorial case studies via the shared golden
pipeline (T04: DSM lifetime categories, T12: Monte Carlo uncertainties) and
asserts that the exported workbook contains the expected sheets and that key
parameter values round-trip.
"""

import os

import pandas as pd
import pytest

import data_loader
from golden_utils import build_case_study_yaml
from reporting.parameter_export import export_parameter_overview

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CASE_STUDY_DIR = os.path.join(
    _PROJECT_ROOT, "01_data", "01_input", "case_studies"
)

T04_YAML = os.path.join(
    _CASE_STUDY_DIR, "T04_Dynamic_Stock_Modelling", "config.yaml"
)
T12_YAML = os.path.join(
    _CASE_STUDY_DIR, "T12_Monte_Carlo_Process", "config.yaml"
)


def _export_case_study(yaml_path, tmp_path):
    parts = build_case_study_yaml(yaml_path)
    uncertainty_params = data_loader.load_uncertainty_definitions_from_yaml(
        yaml_path
    )
    output_path = str(tmp_path / "parameter_overview.xlsx")
    export_parameter_overview(
        parts["mfa_system"],
        parts["config_obj"],
        output_path,
        dsm_params=parts["dsm_params"],
        fomp_params=parts["fomp_params"],
        lfg_params=parts["lfg_params"],
        flow_cap_params=parts["flow_cap_params"],
        bom_params=parts["bom_params"],
        uncertainty_params=uncertainty_params,
        process_logic_map=parts["process_logic_map"],
        flow_tc_map=parts["flow_tc_map"],
        all_excel_data=parts["all_excel_data"],
        source_file=yaml_path,
    )
    return parts, pd.read_excel(output_path, sheet_name=None)


@pytest.fixture(scope="module")
def t04_export(tmp_path_factory):
    return _export_case_study(T04_YAML, tmp_path_factory.mktemp("t04"))


@pytest.fixture(scope="module")
def t12_export(tmp_path_factory):
    return _export_case_study(T12_YAML, tmp_path_factory.mktemp("t12"))


def test_core_sheets_always_present(t04_export):
    _, sheets = t04_export
    for name in ("0_Export_Info", "1_Configuration", "2_Processes",
                 "5_Transfer_Coefficients", "12_Symbol_Legend"):
        assert name in sheets, f"missing sheet: {name}"


def test_export_info_lists_skipped_sheets(t04_export):
    _, sheets = t04_export
    info = sheets["0_Export_Info"]
    attrs = set(info["Attribute"])
    assert "Included sheets" in attrs
    assert "Notation reference" in attrs


def test_processes_sheet_carries_logic(t04_export):
    parts, sheets = t04_export
    procs = sheets["2_Processes"]
    logic_by_pid = dict(zip(procs["Process_ID"], procs["Process_Logic"]))
    for pid, logic in parts["process_logic_map"].items():
        assert logic_by_pid.get(pid) == logic


def test_dsm_sheet_round_trips_lifetimes(t04_export):
    parts, sheets = t04_export
    assert parts["dsm_params"], "T04 should define DSM parameters"
    assert "6_DSM" in sheets
    dsm_sheet = sheets["6_DSM"]

    pid, params = next(iter(parts["dsm_params"].items()))
    proc_rows = dsm_sheet[dsm_sheet["Process"] == pid]
    assert not proc_rows.empty

    # α_i (inflow split) and μ_i (mean lifetime) must round-trip exactly
    exported_splits = proc_rows[
        proc_rows["Code variable"] == "inflow_split"]["Value"].tolist()
    assert exported_splits == pytest.approx(params["inflow_split"])

    exported_means = proc_rows[
        proc_rows["Code variable"] == "Lifetime_Mean"]["Value"].tolist()
    expected_means = [m for m in params["lifetimes"]["Mean"] if m not in (0.0,)]
    assert exported_means == pytest.approx(expected_means)


def test_tc_values_round_trip(t04_export):
    parts, sheets = t04_export
    tc_sheet = sheets["5_Transfer_Coefficients"]
    param_dict = parts["mfa_system"].ParameterDict
    tc_names = [n for n in param_dict if str(n).startswith("TC")]
    assert tc_names, "case study should define TCs"

    exported = dict(zip(tc_sheet["Code variable"], tc_sheet["Value"]))
    for name in tc_names:
        assert name in exported, f"TC {name} missing from export"
        values = param_dict[name].Values
        if not hasattr(values, "ndim"):  # static TC → exact value
            assert exported[name] == pytest.approx(values)


def test_uncertainty_sheet_round_trips(t12_export):
    parts, sheets = t12_export
    uncertainty = data_loader.load_uncertainty_definitions_from_yaml(T12_YAML)
    assert uncertainty, "T12 should define MC uncertainty parameters"
    assert "11_Uncertainty" in sheets
    unc_sheet = sheets["11_Uncertainty"]

    assert set(unc_sheet["Parameter"]) == set(uncertainty.keys())
    for _, row in unc_sheet.iterrows():
        defn = uncertainty[row["Parameter"]]
        assert row["Distribution"] == defn["distribution"]


def test_symbol_legend_uses_report_notation(t04_export):
    _, sheets = t04_export
    legend = sheets["12_Symbol_Legend"]
    symbols = set(legend["Symbol"])
    for expected in ("φ_f^e", "TC_i(t)", "α_L", "ψ", "α_i"):
        assert expected in symbols, f"legend missing symbol {expected}"
