# -*- coding: utf-8 -*-
"""Unit tests for 02_src/engine/initial_stock_engine.py (t=0 stock composition)."""

from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from engine.initial_stock_engine import (
    _build_initial_stock_element_column_map,
    _calculate_initial_stock_values,
    apply_initial_stock_values,
    calculate_initial_stock_balances,
    load_initial_stock_parameters,
)

ELEMENTS = ["material", "WC", "DM", "TC"]


# --------------------------------------------------------------------------
# _calculate_initial_stock_values
# --------------------------------------------------------------------------

def test_initial_stock_values_from_material_and_fractions():
    stock_values = {
        "Initial_Stock_material": 1000.0,
        "Initial_Stock_WC[%]": 0.6,   # decimals, not percentages
        "Initial_Stock_DM[%]": 0.4,
        "Initial_Stock_TC[%]": 0.18,
    }
    result = _calculate_initial_stock_values(stock_values, ELEMENTS)
    np.testing.assert_allclose(result, [1000.0, 600.0, 400.0, 180.0])


def test_initial_stock_values_missing_fractions_default_zero():
    result = _calculate_initial_stock_values(
        {"Initial_Stock_material": 500.0}, ELEMENTS
    )
    np.testing.assert_allclose(result, [500.0, 0.0, 0.0, 0.0])


# --------------------------------------------------------------------------
# _build_initial_stock_element_column_map — naming priority
# --------------------------------------------------------------------------

def test_column_map_prefers_basic_over_is_naming():
    df = pd.DataFrame(
        {
            "IS_Parameter_type": [
                "Basic_E2_Fraction[%]",  # preferred new name for WC (E2)
                "IS_E2_Fraction[%]",     # old name for the same thing
                "IS_E3_Fraction[%]",     # DM only has the old name
            ]
        }
    )
    mapping = _build_initial_stock_element_column_map(ELEMENTS, df)
    assert mapping["WC"] == "Basic_E2_Fraction[%]"
    assert mapping["DM"] == "IS_E3_Fraction[%]"
    assert mapping["TC"] is None  # no candidate present


# --------------------------------------------------------------------------
# load_initial_stock_parameters
# --------------------------------------------------------------------------

def _sheet(rows):
    return {
        "2_4_Initial_Stock": pd.DataFrame(
            rows, columns=["Process_ID", "IS_Parameter_type", "IS_Parameter_Value"]
        )
    }


def test_load_initial_stock_parses_basic_naming():
    excel_data = _sheet(
        [
            (3, "Basic_Material_Quantity[UoM]", 1000.0),
            (3, "Basic_E2_Fraction[%]", 0.6),
            (3, "Basic_E3_Fraction[%]", 0.4),
        ]
    )
    configs = load_initial_stock_parameters(excel_data, elements=ELEMENTS)
    assert set(configs) == {3}
    values = configs[3]["initial_stock_values"]
    assert values["Initial_Stock_material"] == 1000.0
    assert values["Initial_Stock_WC[%]"] == 0.6
    assert values["Initial_Stock_DM[%]"] == 0.4


def test_load_initial_stock_missing_sheet_returns_empty():
    assert load_initial_stock_parameters({}, elements=ELEMENTS) == {}


def test_load_initial_stock_empty_sheet_returns_empty():
    excel_data = {"2_4_Initial_Stock": pd.DataFrame()}
    assert load_initial_stock_parameters(excel_data, elements=ELEMENTS) == {}


# --------------------------------------------------------------------------
# apply_initial_stock_values
# --------------------------------------------------------------------------

def _fake_system(process_ids, num_years=5, num_elements=4):
    stocks = {
        f"S_{pid}": SimpleNamespace(Values=np.zeros((num_years, num_elements)))
        for pid in process_ids
    }
    return SimpleNamespace(StockDict=stocks)


def test_apply_initial_stock_writes_t0_only():
    system = _fake_system([3])
    configs = {
        3: {
            "process_id": 3,
            "elements": ELEMENTS,
            "initial_stock_values": {
                "Initial_Stock_material": 1000.0,
                "Initial_Stock_WC[%]": 0.6,
            },
        }
    }
    apply_initial_stock_values(system, configs)
    values = system.StockDict["S_3"].Values
    np.testing.assert_allclose(values[0], [1000.0, 600.0, 0.0, 0.0])
    # Only t=0 is written; later years untouched
    np.testing.assert_array_equal(values[1:], 0.0)


def test_apply_initial_stock_missing_stock_is_noop():
    system = _fake_system([1])  # process 99 has no S_99 entry
    configs = {
        99: {
            "process_id": 99,
            "elements": ELEMENTS,
            "initial_stock_values": {"Initial_Stock_material": 10.0},
        }
    }
    apply_initial_stock_values(system, configs)  # must not raise
    np.testing.assert_array_equal(system.StockDict["S_1"].Values, 0.0)


# --------------------------------------------------------------------------
# deprecated stub
# --------------------------------------------------------------------------

def test_calculate_initial_stock_balances_is_deprecated():
    with pytest.warns(DeprecationWarning):
        calculate_initial_stock_balances(None, {})
