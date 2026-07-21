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


def test_fomp_parameter_keys_match_what_calculate_fomp_reads(tmp_path):
    """calculate_fomp() (engine/fomp_model.py) reads verbose parameter names
    ("Inflow_fraction_f (Labile pool)", "decay_k1 (Labile pool)",
    "decay_k2 (Recalcitrant pool)") via .get(key, default) with a silent
    fallback. yaml_to_excel_dataframes() previously emitted short keys
    ("f_labile"/"k_labile"/"k_recalcitrant") that calculate_fomp never
    recognized, so every YAML-only FOMP study silently got default decay
    parameters instead of its configured values. Assert the configured
    values round-trip under the exact keys calculate_fomp looks up."""
    yaml_path = _write_yaml(
        tmp_path,
        """
        name: fomp_key_roundtrip
        model:
          start_year: 2020
          end_year: 2025
          elements: [material, TC]
        processes:
        - {id: 0, name: Source, logic: Input, stock: No_Stock, tc_config: No TC}
        - id: 1
          name: Decay
          logic: FOMP
          stock: Stock
          tc_config: No TC
          fomp:
            f_labile: 0.3
            k_labile: 0.2
            k_recalcitrant: 0.05
            outflow_id: F_01_02
            outflow_id_2: F_01_03
        - {id: 2, name: Atmosphere, logic: Output, stock: No_Stock, tc_config: No TC}
        - {id: 3, name: Nutrient_Cycle, logic: Output, stock: No_Stock, tc_config: No TC}
        flows:
        - {id: F_00_01, name: in, from_process: 0, to_process: 1}
        - {id: F_01_02, name: carbon_out, from_process: 1, to_process: 2}
        - {id: F_01_03, name: env_out, from_process: 1, to_process: 3}
        """,
    )
    sheets = data_loader.yaml_to_excel_dataframes(yaml_path)

    fomp_df = sheets["3_2_Definition_FOMP"]
    values = dict(zip(fomp_df["Parameter_Name"], fomp_df["Value"]))

    assert values["Inflow_fraction_f (Labile pool)"] == 0.3
    assert values["decay_k1 (Labile pool)"] == 0.2
    assert values["decay_k2 (Recalcitrant pool)"] == 0.05
    assert values["output_carbon_id"] == "F_01_02"
    assert values["output_environmental_id"] == "F_01_03"
    # The short keys the bug used to emit must not reappear.
    assert "f_labile" not in fomp_df["Parameter_Name"].values
    assert "k_labile" not in fomp_df["Parameter_Name"].values
    assert "k_recalcitrant" not in fomp_df["Parameter_Name"].values
