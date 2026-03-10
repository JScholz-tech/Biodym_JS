# -*- coding: utf-8 -*-
"""
Integration test: load_lfg_parameters() against the real LFG Excel template.

Reads 260309_bioDYM_Systemmanager_template_LFG.xlsm and verifies that the
parser produces exactly the expected output for Process 1.

Run with:
    uv run pytest 04_tests/test_load_lfg_parameters.py -v
"""

import os
import importlib.util as _ilu
import numpy as np
import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Locate files
# ---------------------------------------------------------------------------

_test_dir = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_test_dir)
_xlsm_path = os.path.join(
    _root,
    "01_data", "01_input", "26_template_LFG",
    "260309_bioDYM_Systemmanager_template_LFG.xlsm",
)

# Load data_loader without triggering the full engine/__init__.py
_dl_spec = _ilu.spec_from_file_location(
    "data_loader",
    os.path.join(_root, "02_src", "data_loader.py"),
)
_dl_mod = _ilu.module_from_spec(_dl_spec)
_dl_spec.loader.exec_module(_dl_mod)

load_lfg_parameters = _dl_mod.load_lfg_parameters
normalize_sheet_names = _dl_mod.normalize_sheet_names


def _read_excel(path):
    """Read all sheets from an xlsm file and apply BioDYM column normalisation."""
    raw = pd.read_excel(
        path, sheet_name=None, header=0, engine="openpyxl",
        na_values=["N.A.", "NA", "n/a"], decimal=",",
    )
    return normalize_sheet_names(raw)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def lfg_params():
    """Load LFG parameters from the real Excel template once per module."""
    if not os.path.exists(_xlsm_path):
        pytest.skip(f"LFG template not found: {_xlsm_path}")
    excel_data = _read_excel(_xlsm_path)
    return load_lfg_parameters(excel_data, debug_mode=True)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_process_1_present(lfg_params):
    """Process 1 must be parsed from the sheet."""
    assert 1 in lfg_params, (
        f"Process 1 not found in result. Keys: {list(lfg_params.keys())}"
    )


def test_six_fractions_parsed(lfg_params):
    """Process 1 must have exactly 6 waste fractions."""
    fracs = lfg_params[1]["fractions"]
    assert len(fracs) == 6, (
        f"Expected 6 fractions, got {len(fracs)}: {[f['name'] for f in fracs]}"
    )


def test_fraction_names(lfg_params):
    """Fraction names must match the Excel values in order."""
    names = [f["name"] for f in lfg_params[1]["fractions"]]
    expected = ["Food Waste", "Garden and Park Waste", "Wood Waste",
                "Paper", "Textiles", "Other"]
    assert names == expected, f"Names mismatch:\n  got:      {names}\n  expected: {expected}"


def test_fraction_k_j_values(lfg_params):
    """k_j decay constants must match the Excel values."""
    k_vals = [f["k_j"] for f in lfg_params[1]["fractions"]]
    expected = [0.4, 0.17, 0.035, 0.07, 0.07, 0.0]
    for i, (got, exp) in enumerate(zip(k_vals, expected)):
        assert np.isclose(got, exp, rtol=1e-6), (
            f"Fraction {i+1} k_j: got {got}, expected {exp}"
        )


def test_fraction_doc_j_values(lfg_params):
    """DOC_j values must match the Excel values."""
    doc_vals = [f["DOC_j"] for f in lfg_params[1]["fractions"]]
    expected = [0.15, 0.20, 0.43, 0.40, 0.24, 0.0]
    for i, (got, exp) in enumerate(zip(doc_vals, expected)):
        assert np.isclose(got, exp, rtol=1e-6), (
            f"Fraction {i+1} DOC_j: got {got}, expected {exp}"
        )


def test_fraction_f_input_j_values(lfg_params):
    """f_input_j values must match the Excel values."""
    fi_vals = [f["f_input_j"] for f in lfg_params[1]["fractions"]]
    expected = [0.60, 0.10, 0.03, 0.10, 0.03, 0.14]
    for i, (got, exp) in enumerate(zip(fi_vals, expected)):
        assert np.isclose(got, exp, rtol=1e-6), (
            f"Fraction {i+1} f_input_j: got {got}, expected {exp}"
        )


def test_f_input_j_sums_to_one(lfg_params):
    """f_input_j values across all fractions must sum to 1.0."""
    total = sum(f["f_input_j"] for f in lfg_params[1]["fractions"])
    assert np.isclose(total, 1.0, atol=1e-6), (
        f"f_input_j sum = {total:.6f} (expected 1.0)"
    )


def test_site_param_mcf(lfg_params):
    """MCF must be 1.0 as set in the template."""
    assert np.isclose(lfg_params[1]["MCF"], 1.0), (
        f"MCF: got {lfg_params[1].get('MCF')}, expected 1.0"
    )


def test_site_param_f_ch4(lfg_params):
    """Excel 'F' must be mapped to 'F_CH4' with value 0.5."""
    assert "F_CH4" in lfg_params[1], (
        "F_CH4 missing — check that Excel 'F' is mapped to 'F_CH4'"
    )
    assert np.isclose(lfg_params[1]["F_CH4"], 0.5)


def test_site_param_ox(lfg_params):
    """OX must be 0.1."""
    assert np.isclose(lfg_params[1]["OX"], 0.1), (
        f"OX: got {lfg_params[1].get('OX')}, expected 0.1"
    )


def test_site_param_docf(lfg_params):
    """DOCf must be 0.5."""
    assert np.isclose(lfg_params[1]["DOCf"], 0.5), (
        f"DOCf: got {lfg_params[1].get('DOCf')}, expected 0.5"
    )


def test_output_ch4_id(lfg_params):
    """Excel 'output_CH4_id' must be mapped to 'outflow_ch4_id' = 'F_01_02'."""
    assert lfg_params[1].get("outflow_ch4_id") == "F_01_02", (
        f"outflow_ch4_id: got '{lfg_params[1].get('outflow_ch4_id')}', expected 'F_01_02'"
    )


def test_output_co2_id(lfg_params):
    """Excel 'output_CO2_id' must be mapped to 'outflow_co2_id' = 'F_01_04'."""
    assert lfg_params[1].get("outflow_co2_id") == "F_01_04", (
        f"outflow_co2_id: got '{lfg_params[1].get('outflow_co2_id')}', expected 'F_01_04'"
    )


def test_output_leachate_id(lfg_params):
    """Excel 'output_leaching' must be mapped to 'outflow_leachate_id' = 'F_01_03'."""
    assert lfg_params[1].get("outflow_leachate_id") == "F_01_03", (
        f"outflow_leachate_id: got '{lfg_params[1].get('outflow_leachate_id')}', "
        f"expected 'F_01_03'"
    )


def test_p05_bug_no_spurious_process_5(lfg_params):
    """Output-ID rows have 'P05' prefix in LFG_Parameter_ID but belong to process 1.
    Process 5 must NOT appear as a spurious key in the result."""
    assert 5 not in lfg_params, (
        "Process 5 found in result — P05 prefix bug not handled correctly. "
        "Parser must use Process_ID column, not LFG_Parameter_ID prefix."
    )


def test_unknown_params_not_in_result(lfg_params):
    """Raw Excel keys 'Φ' and 'f' must be normalised — raw form must not appear."""
    p = lfg_params[1]
    # 'Φ' → 'phi' and 'f' → 'f_capture' via PARAM_MAP; raw Unicode must not survive
    for key in ("Φ", "φ"):
        assert key not in p, (
            f"Raw parameter '{key}' should be normalised to 'phi', not stored as-is."
        )


def test_phi_and_f_capture_in_result(lfg_params):
    """φ must be stored as 'phi' and f must be stored as 'f_capture'."""
    p = lfg_params[1]
    assert "phi" in p, "φ should be mapped to 'phi'"
    assert np.isclose(p["phi"], 0.75), f"phi: got {p.get('phi')}, expected 0.75"
    assert "f_capture" in p, "f should be mapped to 'f_capture'"
    assert np.isclose(p["f_capture"], 0.0), f"f_capture: got {p.get('f_capture')}, expected 0.0"
