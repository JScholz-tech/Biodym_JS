# -*- coding: utf-8 -*-
"""Unit tests for 02_src/engine/scenario_engine.py."""

import os
from types import SimpleNamespace

import numpy as np
import pandas as pd

from engine.scenario_engine import _extract_scenario_names, check_mass_balance
from golden_utils import run_case_study_yaml

_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_TESTS_DIR)
CASE_STUDIES_DIR = os.path.join(
    _PROJECT_ROOT, "01_data", "01_input", "case_studies"
)


# --------------------------------------------------------------------------
# _extract_scenario_names
# --------------------------------------------------------------------------

def test_extract_scenario_names_reads_numbered_attributes():
    config_obj = SimpleNamespace(
        Selected_Scenario_Name_1="S1_AD",
        Selected_Scenario_Name_2="S2_Pyrolysis",
    )
    assert _extract_scenario_names(config_obj) == ["S1_AD", "S2_Pyrolysis"]


def test_extract_scenario_names_skips_empty_and_nan():
    config_obj = SimpleNamespace(
        Selected_Scenario_Name_1="S1_AD",
        Selected_Scenario_Name_2="",
        Selected_Scenario_Name_3=float("nan"),
        Selected_Scenario_Name_4="S4_Construction",
    )
    assert _extract_scenario_names(config_obj) == ["S1_AD", "S4_Construction"]


def test_extract_scenario_names_empty_config():
    assert _extract_scenario_names(SimpleNamespace()) == []


# --------------------------------------------------------------------------
# check_mass_balance — on a real solved system (T02 splitter tutorial)
# --------------------------------------------------------------------------

def test_check_mass_balance_passes_on_solved_tutorial():
    yaml_path = os.path.join(
        CASE_STUDIES_DIR, "T02_Splitting_a_flow", "config.yaml"
    )
    mfa_system, _, solver_info = run_case_study_yaml(yaml_path)
    assert solver_info.get("converged") is True

    df = check_mass_balance(mfa_system, label="T02")

    assert isinstance(df, pd.DataFrame)
    assert set(df.columns) == {
        "Element",
        "Max_Abs_Error_Mg",
        "Sum_Abs_Error_Mg",
        "Status",
    }
    assert len(df) == len(mfa_system.Elements)
    # A converged splitter tutorial must balance to numerical noise
    assert (df["Status"] == "PASS").all(), df.to_string()


# --------------------------------------------------------------------------
# check_mass_balance — process ID vs. list position (SystemDefiner audit
# Finding 6: dS was indexed by ProcessList position while flows were indexed
# by process ID, and flows touching IDs >= len(ProcessList) were skipped)
# --------------------------------------------------------------------------

def _fake_system(process_ids, flows, stocks, n_years=2):
    """Minimal duck-typed MFA system: one element, constant flows/stocks.

    flows:  list of (P_Start, P_End, value_per_year)
    stocks: dict process_id -> dS_value_per_year
    """
    return SimpleNamespace(
        Unit="Mg",
        Elements=["material"],
        IndexTable=SimpleNamespace(
            Classification={"Time": SimpleNamespace(Items=list(range(2025, 2025 + n_years)))}
        ),
        ProcessList=[
            SimpleNamespace(ID=pid, Name=f"P{pid}") for pid in process_ids
        ],
        FlowDict={
            f"f{i}": SimpleNamespace(
                P_Start=start, P_End=end, Values=np.full((n_years, 1), value)
            )
            for i, (start, end, value) in enumerate(flows)
        },
        StockDict={
            f"dS_{pid}": SimpleNamespace(Values=np.full((n_years, 1), value))
            for pid, value in stocks.items()
        },
    )


def test_check_mass_balance_with_non_ascending_process_list():
    # P1 balances exactly (in 10 = out 4 + dS 6), but P1 sits at list
    # position 2 — position-indexed dS would land on the wrong process and
    # report a phantom imbalance.
    system = _fake_system(
        process_ids=[0, 2, 1],
        flows=[(0, 1, 10.0), (1, 2, 4.0)],
        stocks={1: 6.0},
    )
    df = check_mass_balance(system, label="shuffled")
    assert (df["Status"] == "PASS").all(), df.to_string()


def test_check_mass_balance_with_id_gap_counts_all_flows():
    # Max process ID (3) exceeds len(ProcessList) (3 → indices 0..2). The old
    # code silently skipped the flow into P3, hiding P1's imbalance and
    # missing P3 entirely.
    balanced = _fake_system(
        process_ids=[0, 1, 3],
        flows=[(0, 1, 10.0), (1, 3, 10.0)],
        stocks={},
    )
    df = check_mass_balance(balanced, label="gap-balanced")
    assert (df["Status"] == "PASS").all(), df.to_string()

    leaky = _fake_system(
        process_ids=[0, 1, 3],
        flows=[(0, 1, 10.0), (1, 3, 4.0)],  # P1 loses 6/yr with no stock
        stocks={},
    )
    df = check_mass_balance(leaky, label="gap-leaky")
    assert (df["Status"] == "WARN").any(), df.to_string()
