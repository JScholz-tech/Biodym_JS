# -*- coding: utf-8 -*-
"""
Pre-refactor safety tests for the E{n} → named-column migration.

These tests must ALL PASS before any Phase 1 code changes are merged.
They guard against the 5 ranked failure modes identified during planning.
"""

import pytest
import pandas as pd

from data_loader import normalize_column_names, _sanitize_col_name
from engine.bom_assembler import _build_tc_column_map, _build_tc_value_column_map


# ---------------------------------------------------------------------------
# PRECHECK-1: Mixed format — both E{n} and named columns coexist
# Expected: named column wins; E{n} fallback works for unmigrated elements
# ---------------------------------------------------------------------------

def test_mixed_format_named_wins():
    """Named column takes priority when both E{n} and named exist."""
    elements = ['material', 'WC', 'DM']
    df = pd.DataFrame(columns=['E2_TC_ID', 'WC_TC_ID', 'E3_TC_ID'])
    m = _build_tc_column_map(df, elements)
    assert m['WC'] == 'WC_TC_ID', f"Named column should win, got: {m['WC']}"
    assert m['DM'] == 'E3_TC_ID', f"E{{n}} fallback should work for unmigrated, got: {m['DM']}"


def test_mixed_format_value_named_wins():
    """Named value column takes priority over E{n}_TC_Value[%]."""
    elements = ['material', 'WC', 'DM']
    df = pd.DataFrame(columns=['E2_TC_Value[%]', 'WC_Value[%]', 'E3_TC_Value[%]'])
    m = _build_tc_value_column_map(df, elements)
    assert m['WC'] == 'WC_Value[%]', f"Named value column should win, got: {m['WC']}"
    assert m['DM'] == 'E3_TC_Value[%]', f"E{{n}} fallback for unmigrated, got: {m['DM']}"


def test_named_columns_only():
    """Named columns work with no E{n} columns present (new Excel format)."""
    elements = ['material', 'WC', 'DM', 'TC']
    df = pd.DataFrame(columns=['WC_TC_ID', 'WC_Value[%]', 'DM_TC_ID', 'TC_TC_ID'])
    m = _build_tc_column_map(df, elements)
    assert m['WC'] == 'WC_TC_ID'
    assert m['DM'] == 'DM_TC_ID'
    assert m['TC'] == 'TC_TC_ID'


def test_en_columns_only_backward_compat():
    """Legacy E{n} columns still work (old Excel format, no regression)."""
    elements = ['material', 'WC', 'DM', 'TC']
    df = pd.DataFrame(columns=['E2_TC_ID', 'E3_TC_ID', 'E4_TC_ID'])
    m = _build_tc_column_map(df, elements)
    assert m['WC'] == 'E2_TC_ID'
    assert m['DM'] == 'E3_TC_ID'
    assert m['TC'] == 'E4_TC_ID'


# ---------------------------------------------------------------------------
# PRECHECK-2: Excel column deduplication — pandas appends '.N' suffix
# Expected: normalize_column_names raises ValueError before data is read
# ---------------------------------------------------------------------------

def test_duplicate_columns_detected():
    """Loader issues a UserWarning for pandas-style duplicate suffix (.1, .2)."""
    import warnings
    df = pd.DataFrame(columns=['E2_TC_ID', 'E2_TC_ID.1', 'Flow_ID'])
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        normalize_column_names(df)
    assert any("duplicate" in str(w.message).lower() for w in caught), (
        "Expected a duplicate-column warning but none was issued"
    )


def test_no_false_positive_on_clean_columns():
    """Clean columns with no .N suffix must not raise."""
    df = pd.DataFrame(columns=['E2_TC_ID', 'E3_TC_ID', 'Flow_ID'])
    # Should not raise
    result = normalize_column_names(df)
    assert 'E2_TC_ID' in result.columns


# ---------------------------------------------------------------------------
# PRECHECK-3: Element names with special characters
# Expected: sanitized to safe identifier
# ---------------------------------------------------------------------------

def test_sanitize_spaces_and_parens():
    assert _sanitize_col_name("core electronics (assembled)") == "core_electronics_assembled_"


def test_sanitize_slash():
    assert _sanitize_col_name("TC/DM ratio") == "TC_DM_ratio"


def test_sanitize_brackets():
    # TC[%] → T,C kept; [,%, ] each → _; three consecutive _ collapse to one
    assert _sanitize_col_name("TC[%]") == "TC_"


def test_sanitize_plain_name_unchanged():
    assert _sanitize_col_name("WC") == "WC"
    assert _sanitize_col_name("structural_elements") == "structural_elements"


# ---------------------------------------------------------------------------
# PRECHECK-4: Dynamic TC — mixed per-process E{n} and named in same sheet
# The adapter must normalize the whole sheet before groupby so both formats
# coexist without cross-contamination.
# ---------------------------------------------------------------------------

def test_normalize_translates_en_to_named_for_known_elements():
    """normalize_column_names with elements= renames E{n} → named."""
    elements = ['material', 'WC', 'DM', 'TC']
    df = pd.DataFrame(columns=['Flow_ID', 'E2_TC_ID', 'E2_TC_Value[%]', 'E3_TC_ID'])
    df_norm = normalize_column_names(df, elements=elements)
    assert 'WC_TC_ID' in df_norm.columns, f"E2_TC_ID should become WC_TC_ID, got: {df_norm.columns.tolist()}"
    assert 'WC_Value[%]' in df_norm.columns, "E2_TC_Value[%] should become WC_Value[%]"
    assert 'DM_TC_ID' in df_norm.columns, "E3_TC_ID should become DM_TC_ID"
    # E{n} originals should be gone (renamed, not duplicated)
    assert 'E2_TC_ID' not in df_norm.columns
    assert 'E3_TC_ID' not in df_norm.columns


def test_normalize_named_columns_pass_through():
    """Already-named columns are not double-translated."""
    elements = ['material', 'WC', 'DM']
    df = pd.DataFrame(columns=['WC_TC_ID', 'WC_Value[%]', 'DM_TC_ID'])
    df_norm = normalize_column_names(df, elements=elements)
    assert 'WC_TC_ID' in df_norm.columns
    assert 'DM_TC_ID' in df_norm.columns
    assert 'WC_TC_ID.1' not in df_norm.columns  # no duplication


# ---------------------------------------------------------------------------
# PRECHECK-5: Initial stock element order independence
# IS_E2_Fraction maps to correct element regardless of element list order
# ---------------------------------------------------------------------------

def test_initial_stock_element_map_standard_order():
    """IS_E2_Fraction[%] maps to the second element (WC) in standard order."""
    from engine.initial_stock_engine import _build_initial_stock_element_column_map
    elements = ['material', 'WC', 'DM', 'TC']
    df = pd.DataFrame({'IS_Parameter_type': ['IS_E2_Fraction[%]', 'IS_E3_Fraction[%]']})
    m = _build_initial_stock_element_column_map(elements, df)
    assert m['WC'] == 'IS_E2_Fraction[%]', f"WC should map to IS_E2_Fraction[%], got {m}"
    assert m['DM'] == 'IS_E3_Fraction[%]'


def test_initial_stock_element_map_more_elements():
    """Mapping scales correctly when more elements are added."""
    from engine.initial_stock_engine import _build_initial_stock_element_column_map
    elements = ['material', 'WC', 'DM', 'TC', 'TOC', 'TIC']
    df = pd.DataFrame({'IS_Parameter_type': [
        'IS_E2_Fraction[%]', 'IS_E3_Fraction[%]',
        'IS_E4_Fraction[%]', 'IS_E5_Fraction[%]', 'IS_E6_Fraction[%]',
    ]})
    m = _build_initial_stock_element_column_map(elements, df)
    assert m['WC'] == 'IS_E2_Fraction[%]'
    assert m['TOC'] == 'IS_E5_Fraction[%]'
    assert m['TIC'] == 'IS_E6_Fraction[%]'
