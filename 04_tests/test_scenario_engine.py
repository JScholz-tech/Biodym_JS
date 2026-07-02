# -*- coding: utf-8 -*-
"""Unit tests for 02_src/engine/scenario_engine.py."""

import os
from types import SimpleNamespace

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
