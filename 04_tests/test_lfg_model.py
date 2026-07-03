# -*- coding: utf-8 -*-
"""
Tests for the engine/lfg_model.py module.

Unit tests for the Landfill Gas (LFG) first-order decay calculation,
covering mass balance, fraction independence, ash accumulation, and
leachate output. Mirrors the structure of test_fomp_model.py.
"""

import sys
import os
import pytest
import numpy as np
import copy

# Pure calculation: import lfg_model directly to avoid triggering engine/__init__.py
# which would try to import dsm_model (requires dynamic_stock_model / ODYM framework).
import importlib.util as _ilu
import os as _os

_lfg_spec = _ilu.spec_from_file_location(
    "lfg_model",
    _os.path.join(_os.path.dirname(__file__), "..", "02_src", "engine", "lfg_model.py"),
)
_lfg_mod = _ilu.module_from_spec(_lfg_spec)
_lfg_spec.loader.exec_module(_lfg_mod)
_calculate_lfg_series = _lfg_mod._calculate_lfg_series
calculate_lfg = _lfg_mod.calculate_lfg

# ODYM-dependent imports — integration tests are skipped if ODYM is not installed
try:
    import ODYM_Classes as msc
    from system_setup import define_model_scope, initialize_mfa_system
    ODYM_AVAILABLE = True
except ImportError:
    ODYM_AVAILABLE = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _single_fraction_params(k_j=0.1, DOC_j=0.4, f_input_j=1.0, f_ash_j=0.05,
                              MCF=1.0, DOCf=1.0, F_CH4=0.5, OX=0.0, phi=1.0):
    """Minimal LFG parameter dict with a single waste fraction."""
    return {
        "fractions": [
            {"name": "Test_fraction", "k_j": k_j, "DOC_j": DOC_j,
             "f_input_j": f_input_j, "f_ash_j": f_ash_j},
        ],
        "MCF": MCF,
        "DOCf": DOCf,
        "F_CH4": F_CH4,
        "OX": OX,
        "phi": phi,
    }


# ---------------------------------------------------------------------------
# Test: exponential decay of a single fraction
# ---------------------------------------------------------------------------

def test_lfg_single_fraction_decay():
    """One fraction, no inflow after year 1: stock decays exponentially."""
    k = 0.2
    initial_C = 100.0
    T = 5
    waste_in = np.zeros(T)
    wc_in = np.zeros(T)
    params = _single_fraction_params(k_j=k, DOC_j=1.0, f_input_j=1.0,
                                      f_ash_j=0.0, DOCf=1.0, MCF=1.0, OX=0.0)

    results = _calculate_lfg_series(
        waste_in, wc_in, params, initial_stocks={"Test_fraction": initial_C}
    )

    stock = results["stocks"]["Test_fraction"]
    expected_factor = 1.0 - np.exp(-k)
    # Year 0: stock = initial_C - initial_C*(1-exp(-k)) = initial_C*exp(-k)
    assert np.isclose(stock[0], initial_C * np.exp(-k), rtol=1e-6)
    # Each year: stock * exp(-k)
    for t in range(1, T):
        assert np.isclose(stock[t], stock[t - 1] * np.exp(-k), rtol=1e-6), (
            f"Year {t}: stock {stock[t]:.6f} != expected {stock[t-1]*np.exp(-k):.6f}"
        )


# ---------------------------------------------------------------------------
# Test: multi-fraction independence
# ---------------------------------------------------------------------------

def test_lfg_multi_fraction_independence():
    """Three fractions must evolve independently of each other."""
    T = 5
    waste_in = np.ones(T) * 100.0  # 100 Mg/year
    wc_in = np.zeros(T)

    params = {
        "fractions": [
            {"name": "Fast",   "k_j": 0.5, "DOC_j": 0.3, "f_input_j": 0.4, "f_ash_j": 0.0},
            {"name": "Medium", "k_j": 0.1, "DOC_j": 0.2, "f_input_j": 0.4, "f_ash_j": 0.0},
            {"name": "Slow",   "k_j": 0.02,"DOC_j": 0.4, "f_input_j": 0.2, "f_ash_j": 0.0},
        ],
        "MCF": 1.0, "DOCf": 1.0, "F_CH4": 0.5, "OX": 0.0,
    }

    results = _calculate_lfg_series(waste_in, wc_in, params)

    # Fast fraction should have lower stock than slow fraction at steady approach
    fast_final = results["stocks"]["Fast"][-1]
    slow_final = results["stocks"]["Slow"][-1]
    # Fast decays quicker → lower stock relative to inflow
    assert fast_final < slow_final, (
        f"Fast fraction stock ({fast_final:.2f}) should be < slow ({slow_final:.2f})"
    )

    # Verify all stocks are non-negative
    for frac_name, stock in results["stocks"].items():
        assert np.all(stock >= 0), f"Negative stock in fraction '{frac_name}'"


# ---------------------------------------------------------------------------
# Test: carbon mass balance (CH4-C + CO2-C + stock = cumulative DOC inflow)
# ---------------------------------------------------------------------------

def test_lfg_gas_output_mass_balance():
    """CH4-C + CO2-C + organic_stock == cumulative active C inflow."""
    T = 10
    waste_in = np.ones(T) * 200.0
    wc_in = np.zeros(T)
    k = 0.15
    DOC_j = 0.3
    DOCf = 0.8
    MCF = 1.0
    OX = 0.0

    params = _single_fraction_params(
        k_j=k, DOC_j=DOC_j, f_input_j=1.0, f_ash_j=0.0,
        MCF=MCF, DOCf=DOCf, OX=OX
    )

    results = _calculate_lfg_series(waste_in, wc_in, params)

    cumulative_C_in = np.sum(waste_in * DOC_j * DOCf)
    cumulative_CH4_C = np.sum(results["ch4_carbon_total"])
    cumulative_CO2_C = np.sum(results["co2_carbon_total"])
    final_organic_stock = results["stocks"]["Test_fraction"][-1]

    total_accounted = cumulative_CH4_C + cumulative_CO2_C + final_organic_stock
    assert np.isclose(total_accounted, cumulative_C_in, rtol=1e-6), (
        f"Carbon balance mismatch: {total_accounted:.4f} != {cumulative_C_in:.4f}"
    )


# ---------------------------------------------------------------------------
# Test: ash accumulates permanently and never decays
# ---------------------------------------------------------------------------

def test_lfg_ash_permanent_stock():
    """Ash inflow accumulates linearly and is not reduced by decay."""
    T = 5
    W = 100.0
    f_ash = 0.08
    waste_in = np.ones(T) * W
    wc_in = np.zeros(T)

    params = _single_fraction_params(k_j=0.5, f_ash_j=f_ash)

    results = _calculate_lfg_series(waste_in, wc_in, params)

    ash = results["ash_stock_total"]
    # Ash must be strictly increasing
    assert np.all(np.diff(ash) > 0), "Ash stock is not monotonically increasing"
    # Cumulative ash = W * f_input_j * f_ash * t (after year t, 1-indexed)
    expected_ash_final = W * 1.0 * f_ash * T
    assert np.isclose(ash[-1], expected_ash_final, rtol=1e-6), (
        f"Final ash {ash[-1]:.4f} != expected {expected_ash_final:.4f}"
    )


# ---------------------------------------------------------------------------
# Test: leachate equals WC inflow
# ---------------------------------------------------------------------------

def test_lfg_leachate_equals_wc_in():
    """Leachate (water) output must exactly equal WC inflow."""
    T = 8
    wc_in = np.array([10, 12, 15, 14, 13, 11, 10, 9], dtype=float)
    waste_in = np.ones(T) * 100.0

    params = _single_fraction_params()
    results = _calculate_lfg_series(waste_in, wc_in, params)

    assert np.allclose(results["leachate_total"], wc_in), (
        "Leachate does not equal WC inflow"
    )


# ---------------------------------------------------------------------------
# Test: MCF = 0 → no gas output
# ---------------------------------------------------------------------------

def test_lfg_site_params_mcf_effect():
    """MCF applies to the methane pathway only: MCF=0 zeroes CH4, not CO2."""
    T = 5
    waste_in = np.ones(T) * 100.0
    wc_in = np.zeros(T)

    params = _single_fraction_params(MCF=0.0)
    results = _calculate_lfg_series(waste_in, wc_in, params)

    assert np.all(results["ch4_carbon_total"] == 0), "CH4 should be 0 when MCF=0"
    assert np.all(results["co2_carbon_total"] > 0), (
        "CO2 must be unaffected by MCF (direct emission of the non-CH4 share)"
    )


# ---------------------------------------------------------------------------
# Test: zero inflow → pure decay from initial stock
# ---------------------------------------------------------------------------

def test_lfg_zero_inflow():
    """With no new waste input, existing stock should decay according to k_j."""
    k = 0.1
    initial_C = 500.0
    T = 6
    waste_in = np.zeros(T)
    wc_in = np.zeros(T)

    params = _single_fraction_params(k_j=k)
    results = _calculate_lfg_series(
        waste_in, wc_in, params, initial_stocks={"Test_fraction": initial_C}
    )

    stock = results["stocks"]["Test_fraction"]
    # Pure exponential decay
    for t in range(T):
        expected = initial_C * np.exp(-k * (t + 1))
        assert np.isclose(stock[t], expected, rtol=1e-6), (
            f"Year {t}: stock {stock[t]:.4f} != expected {expected:.4f}"
        )

    # Gas output should be non-zero
    assert np.all(results["ch4_carbon_total"] > 0), "CH4 should be > 0 during decay"


# ---------------------------------------------------------------------------
# Test: organic C stock (Mg C) and ash stock (Mg DM) are reported separately
# ---------------------------------------------------------------------------

def test_lfg_organic_and_ash_stocks_separate():
    """organic_c_stock sums the fraction C stocks; ash stays its own key."""
    T = 5
    waste_in = np.ones(T) * 100.0
    wc_in = np.zeros(T)
    params = {
        "fractions": [
            {"name": "A", "k_j": 0.1, "DOC_j": 0.3, "f_input_j": 0.6, "f_ash_j": 0.05},
            {"name": "B", "k_j": 0.3, "DOC_j": 0.2, "f_input_j": 0.4, "f_ash_j": 0.10},
        ],
        "MCF": 0.8, "DOCf": 0.5, "F_CH4": 0.5, "OX": 0.1,
    }

    results = _calculate_lfg_series(waste_in, wc_in, params)

    expected_organic = results["stocks"]["A"] + results["stocks"]["B"]
    assert np.allclose(results["organic_c_stock"], expected_organic)
    # The unit-mixing "stable_stock" (Mg C + Mg DM) key was removed
    assert "stable_stock" not in results
    assert np.all(results["ash_stock_total"] >= 0)


# ---------------------------------------------------------------------------
# Test: phi (model correction factor) scales gas output
# ---------------------------------------------------------------------------

def test_lfg_phi_scales_ch4_only():
    """phi=0.75 must reduce CH4 to 75% of phi=1.0; CO2 is not corrected."""
    T = 5
    waste_in = np.ones(T) * 100.0
    wc_in = np.zeros(T)
    base_params = _single_fraction_params()

    params_phi1 = {**base_params, "phi": 1.0}
    params_phi075 = {**base_params, "phi": 0.75}

    r1 = _calculate_lfg_series(waste_in, wc_in, params_phi1)
    r075 = _calculate_lfg_series(waste_in, wc_in, params_phi075)

    assert np.allclose(r075["ch4_carbon_total"], r1["ch4_carbon_total"] * 0.75), (
        "CH4 with phi=0.75 should be 75% of phi=1.0"
    )
    assert np.allclose(r075["co2_carbon_total"], r1["co2_carbon_total"]), (
        "CO2 must be unaffected by phi (correction applies to CH4 only)"
    )


def test_lfg_phi_zero_suppresses_ch4_only():
    """phi=0 must zero the CH4 output; CO2 continues to be emitted."""
    T = 5
    waste_in = np.ones(T) * 100.0
    wc_in = np.zeros(T)
    params = _single_fraction_params(phi=0.0)
    results = _calculate_lfg_series(waste_in, wc_in, params)

    assert np.all(results["ch4_carbon_total"] == 0), "CH4 should be 0 when phi=0"
    assert np.all(results["co2_carbon_total"] > 0), (
        "CO2 must be unaffected by phi"
    )


def test_lfg_gas_carbon_never_exceeds_decay():
    """CH4_C + CO2_C must never exceed the decayed carbon (validation note)."""
    T = 10
    waste_in = np.ones(T) * 100.0
    wc_in = np.zeros(T)
    params = _single_fraction_params(MCF=0.7, OX=0.1, phi=0.9)
    results = _calculate_lfg_series(waste_in, wc_in, params)

    # Total decayed C = cumulative active inflow - final stock
    frac = params["fractions"][0]
    total_c_in = np.sum(waste_in * frac["f_input_j"] * frac["DOC_j"] * params["DOCf"])
    total_decay = total_c_in - results["stocks"][frac["name"]][-1]
    total_gas = np.sum(results["ch4_carbon_total"]) + np.sum(
        results["co2_carbon_total"]
    )
    assert total_gas <= total_decay + 1e-9


# ---------------------------------------------------------------------------
# Test: MFA system integration (calculate_lfg)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not ODYM_AVAILABLE, reason="ODYM framework not installed")
def test_calculate_lfg_writes_flows():
    """calculate_lfg must write CH4, CO2, and leachate flows to FlowDict."""
    elements = ["material", "WC", "DM", "CC"]
    start_year, end_year = 2025, 2027
    model_class, index_table = define_model_scope(start_year, end_year, elements)
    mfa_system = initialize_mfa_system(model_class, index_table)

    mfa_system.ProcessList.append(msc.Process(Name="Environment", ID=0))
    mfa_system.ProcessList.append(msc.Process(Name="Landfill", ID=7))
    mfa_system.ProcessList.append(msc.Process(Name="Gas_CH4", ID=8))
    mfa_system.ProcessList.append(msc.Process(Name="Gas_CO2", ID=9))
    mfa_system.ProcessList.append(msc.Process(Name="Leachate", ID=10))

    mfa_system.StockDict["S_7"] = msc.Stock(Name="S_7", P_Res=7, Type=0, Indices="t,e")
    mfa_system.Initialize_StockValues()

    T = end_year - start_year + 1
    num_el = len(elements)
    inflow_vals = np.zeros((T, num_el))
    # material = 100, WC = 20 (20% moisture), DM = 80, CC = 30 (30% C of DM)
    inflow_vals[:, 0] = 100.0  # material
    inflow_vals[:, 1] = 20.0   # WC
    inflow_vals[:, 2] = 80.0   # DM
    inflow_vals[:, 3] = 30.0   # CC

    mfa_system.FlowDict["F_0_7"] = msc.Flow(
        Name="F_0_7", P_Start=0, P_End=7, Indices="t,e", Values=inflow_vals
    )
    mfa_system.FlowDict["F_7_8"] = msc.Flow(
        Name="F_7_8", P_Start=7, P_End=8, Indices="t,e"
    )
    mfa_system.FlowDict["F_7_9"] = msc.Flow(
        Name="F_7_9", P_Start=7, P_End=9, Indices="t,e"
    )
    mfa_system.FlowDict["F_7_10"] = msc.Flow(
        Name="F_7_10", P_Start=7, P_End=10, Indices="t,e"
    )
    mfa_system.Initialize_FlowValues()

    lfg_params_config = {
        7: {
            "fractions": [
                {"name": "MSW", "k_j": 0.1, "DOC_j": 0.3, "f_input_j": 1.0, "f_ash_j": 0.05},
            ],
            "MCF": 0.8, "DOCf": 0.5, "F_CH4": 0.5, "OX": 0.1,
            "outflow_ch4_id": "F_7_8",
            "outflow_co2_id": "F_7_9",
            "outflow_leachate_id": "F_7_10",
        }
    }

    result = calculate_lfg(copy.deepcopy(mfa_system), lfg_params_config)

    ch4_vals = result.FlowDict["F_7_8"].Values
    co2_vals = result.FlowDict["F_7_9"].Values
    leachate_vals = result.FlowDict["F_7_10"].Values

    mat_idx = elements.index("material")
    wc_idx = elements.index("WC")

    # Year 0: no initial stock, so CH4/CO2 = 0 (no decay yet, stock builds)
    # But year 1 onward should have gas output
    assert np.all(ch4_vals >= 0), "CH4 flow must be non-negative"
    assert np.all(co2_vals >= 0), "CO2 flow must be non-negative"
    assert np.all(leachate_vals[:, mat_idx] >= 0), "Leachate material flow must be non-negative"

    # Leachate material = WC inflow
    assert np.allclose(leachate_vals[:, wc_idx], inflow_vals[:, wc_idx]), (
        "Leachate WC should equal WC inflow"
    )
    # Leachate CC = 0
    cc_idx = elements.index("CC")
    assert np.all(leachate_vals[:, cc_idx] == 0), "Leachate CC should be 0"


# ---------------------------------------------------------------------------
# Test: load_lfg_parameters — parses LFG_Parameter_type/Value layout
# ---------------------------------------------------------------------------

def test_load_lfg_parameters_parses_correctly():
    """load_lfg_parameters must parse the FOMP-style row-per-parameter layout."""
    import importlib.util as _ilu2
    import os as _os2

    _dl_spec = _ilu2.spec_from_file_location(
        "data_loader",
        _os2.path.join(_os2.path.dirname(__file__), "..", "02_src", "data_loader.py"),
    )
    _dl_mod = _ilu2.module_from_spec(_dl_spec)
    _dl_spec.loader.exec_module(_dl_mod)
    load_lfg_parameters = _dl_mod.load_lfg_parameters

    import pandas as pd

    # Simulate the actual Excel sheet structure:
    # LFG_Parameter_ID | LFG_Parameter_type | LFG_Parameter_Value | Process_ID
    rows = [
        # Fraction 1 rows (Food waste)
        {"Process_ID": 1, "LFG_Parameter_ID": "P01_Waste_Fraction_j1", "LFG_Parameter_type": "Waste_Fraction_j", "LFG_Parameter_Value": "Food_waste"},
        {"Process_ID": 1, "LFG_Parameter_ID": "P01_f_input_j1",        "LFG_Parameter_type": "f_input_j",       "LFG_Parameter_Value": 0.6},
        {"Process_ID": 1, "LFG_Parameter_ID": "P01_DOC_j1",            "LFG_Parameter_type": "DOC_j",           "LFG_Parameter_Value": 0.15},
        {"Process_ID": 1, "LFG_Parameter_ID": "P01_k_j1",              "LFG_Parameter_type": "k_j",             "LFG_Parameter_Value": 0.185},
        # Fraction 2 rows (Paper)
        {"Process_ID": 1, "LFG_Parameter_ID": "P01_Waste_Fraction_j2", "LFG_Parameter_type": "Waste_Fraction_j", "LFG_Parameter_Value": "Paper"},
        {"Process_ID": 1, "LFG_Parameter_ID": "P01_f_input_j2",        "LFG_Parameter_type": "f_input_j",       "LFG_Parameter_Value": 0.4},
        {"Process_ID": 1, "LFG_Parameter_ID": "P01_DOC_j2",            "LFG_Parameter_type": "DOC_j",           "LFG_Parameter_Value": 0.40},
        {"Process_ID": 1, "LFG_Parameter_ID": "P01_k_j2",              "LFG_Parameter_type": "k_j",             "LFG_Parameter_Value": 0.04},
        # Site parameters (uses Excel column names before mapping)
        {"Process_ID": 1, "LFG_Parameter_ID": "P01_MCF_Site_Parameter", "LFG_Parameter_type": "MCF",  "LFG_Parameter_Value": 0.8},
        {"Process_ID": 1, "LFG_Parameter_ID": "P01_DOCf_Site_Parameter","LFG_Parameter_type": "DOCf", "LFG_Parameter_Value": 0.5},
        {"Process_ID": 1, "LFG_Parameter_ID": "P01_F_Site_Parameter",   "LFG_Parameter_type": "F",    "LFG_Parameter_Value": 0.5},
        {"Process_ID": 1, "LFG_Parameter_ID": "P01_OX_Site_Parameter",  "LFG_Parameter_type": "OX",   "LFG_Parameter_Value": 0.1},
        # Output flow IDs (P05 bug in template — Process_ID column must override)
        {"Process_ID": 1, "LFG_Parameter_ID": "P05_output_CH4_id",      "LFG_Parameter_type": "output_CH4_id",  "LFG_Parameter_Value": "F_01_02"},
        {"Process_ID": 1, "LFG_Parameter_ID": "P05_output_CO2_id",      "LFG_Parameter_type": "output_CO2_id",  "LFG_Parameter_Value": "F_01_04"},
        {"Process_ID": 1, "LFG_Parameter_ID": "P05_output_leaching",    "LFG_Parameter_type": "output_leaching","LFG_Parameter_Value": "F_01_03"},
    ]
    df = pd.DataFrame(rows)
    excel_data = {"3_3_Definition_LFG": df}

    result = load_lfg_parameters(excel_data, debug_mode=False)

    assert 1 in result, "Process 1 must be parsed"
    p = result[1]

    # Fractions
    assert len(p["fractions"]) == 2, f"Expected 2 fractions, got {len(p['fractions'])}"
    frac1 = p["fractions"][0]
    assert frac1["name"] == "Food_waste"
    assert np.isclose(frac1["k_j"], 0.185)
    assert np.isclose(frac1["DOC_j"], 0.15)
    assert np.isclose(frac1["f_input_j"], 0.6)

    frac2 = p["fractions"][1]
    assert frac2["name"] == "Paper"
    assert np.isclose(frac2["k_j"], 0.04)

    # Site params — F must be mapped to F_CH4
    assert np.isclose(p["MCF"], 0.8)
    assert np.isclose(p["DOCf"], 0.5)
    assert np.isclose(p["F_CH4"], 0.5), "F in Excel must be mapped to F_CH4"
    assert np.isclose(p["OX"], 0.1)

    # Output flow IDs — must use Process_ID column, not P05 prefix
    assert p["outflow_ch4_id"] == "F_01_02", "output_CH4_id must map to outflow_ch4_id"
    assert p["outflow_co2_id"] == "F_01_04"
    assert p["outflow_leachate_id"] == "F_01_03", "output_leaching must map to outflow_leachate_id"
