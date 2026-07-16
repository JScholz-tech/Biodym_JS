# -*- coding: utf-8 -*-
"""Regression tests for data_loader.yaml_to_excel_dataframes."""

import textwrap

import data_loader


def _write_yaml(tmp_path, body: str) -> str:
    p = tmp_path / "config.yaml"
    p.write_text(textwrap.dedent(body), encoding="utf-8")
    return str(p)


def test_dangling_tc_is_skipped_not_exported_as_junk(tmp_path, capsys):
    """A TC referencing a missing flow used to fall back to 0→0 endpoints, so
    every dangling TC exported the same junk TC_E*_00_00 name — two of them
    then crashed the dynamic-TC loader with duplicate year labels (observed
    live on heatpumps_2 after flow IDs were renamed by hand in the YAML)."""
    yaml_path = _write_yaml(
        tmp_path,
        """
        name: dangling_tc
        model:
          start_year: 2020
          end_year: 2025
          elements: [material, WC]
        processes:
        - {id: 0, name: Source, logic: Input, stock: No_Stock, tc_config: No TC}
        - {id: 1, name: Sorter, logic: Splitter, stock: No_Stock, tc_config: Dynamic}
        - {id: 2, name: Sink, logic: Output, stock: No_Stock, tc_config: No TC}
        flows:
        - {id: F_00_01, name: in, from_process: 0, to_process: 1}
        - {id: F_01_02, name: out, from_process: 1, to_process: 2}
        transfer_coefficients:
        - process_id: 1
          flow_id: F_01_02
          tc_type: dynamic
          time_series:
          - {year: 2020, values: {material: 1.0}}
        # two dangling TCs — both would have collided on TC_00_00 / year 2020
        - process_id: 1
          flow_id: F_99_98
          tc_type: dynamic
          time_series:
          - {year: 2020, values: {material: 0.5}}
        - process_id: 1
          flow_id: F_99_97
          tc_type: dynamic
          time_series:
          - {year: 2020, values: {material: 0.5}}
        - process_id: 1
          flow_id: F_99_96
          tc_type: static
          values: {material: 1.0}
        """,
    )
    sheets = data_loader.yaml_to_excel_dataframes(yaml_path)

    dyn = sheets["2_3_dynamic_TCs"]
    assert len(dyn) == 1  # only the valid TC survives
    assert dyn.iloc[0]["Flow_ID"] == "F_01_02"
    assert not any("00_00" in str(v) for v in dyn.get("E1_TC_ID", []))

    static = sheets["2_2_static_TCs"]
    assert len(static) == 0  # the dangling static TC is skipped too

    out = capsys.readouterr().out
    assert "missing flow 'F_99_98'" in out
    assert "missing flow 'F_99_96'" in out
