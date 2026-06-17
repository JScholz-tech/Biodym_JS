# -*- coding: utf-8 -*-
"""
End-to-end workflow test: creates a complete bioDYM case study through the
web app's HTTP routes, then validates the exported YAML.

Simulates the user journey across all 6 dashboard sections:
  §1 Model Configuration
  §2 Processes & Stocks        (Splitter + FOMP + DSM)
  §3 Flows & Input Data        (flow compositions + flow data)
  §4 Advanced Models           (FOMP params + DSM params)
  §5 Scenario & Uncertainty    (scenario modifications + MC parameters)
  §6 Reference Manager         (skipped — no Zotero in tests)

Study topology:
  P1 Atmosphere (Input)
     ↓ F_01_02 Straw Supply
  P2 Field (Splitter)
     ↓ F_02_03 To Soil        TC material=0.40
     ↓ F_02_04 To Construction TC material=0.60
  P3 Soil_Inc (FOMP)
     ↓ F_03_01 CO2 to Atmosphere
  P4 Construction (DSM)
     ↓ F_04_01 EoL to Atmosphere
"""
from __future__ import annotations

import yaml
import pytest


STUDY = "Wheat_Straw_E2E"


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _post(client, url: str, **data) -> None:
    """POST form data and assert 2xx or 3xx."""
    r = client.post(url, data=data, follow_redirects=True)
    assert r.status_code == 200, f"POST {url} failed: {r.status_code}\n{r.text[:500]}"


# ─────────────────────────────────────────────────────────────────────────────
# §1  Model Configuration
# ─────────────────────────────────────────────────────────────────────────────

def _create_study(client) -> None:
    r = client.post(
        "/new",
        data={
            "name": STUDY,
            "start_year": 2025,
            "end_year": 2125,
            "elements": "material, WC, DM, TC",
        },
        follow_redirects=True,
    )
    assert r.status_code == 200
    assert STUDY.encode() in r.content


def _configure_model(client) -> None:
    _post(
        client,
        f"/{STUDY}/settings",
        start_year=2025,
        end_year=2125,
        elements="material, WC, DM, TC",
        unit_of_measurement="Mg",
        run_dsm_calculation="on",
        run_fomp_calculation="on",
        run_monte_carlo="on",
        mc_iterations=500,
        run_scenario_analysis="on",
        selected_scenarios_0="Baseline_DI",
    )


# ─────────────────────────────────────────────────────────────────────────────
# §2  Processes & Stocks
# ─────────────────────────────────────────────────────────────────────────────

def _create_processes(client) -> None:
    # P1: system boundary / atmosphere
    _post(client, f"/{STUDY}/processes/new",
          name="Atmosphere", logic="Input", stock="No_Stock")

    # P2: collection (Splitter, static TCs)
    _post(client, f"/{STUDY}/processes/new",
          name="Field", logic="Splitter", stock="No_Stock", tc_config="Static")

    # P3: soil incorporation (FOMP)
    _post(client, f"/{STUDY}/processes/new",
          name="Soil_Inc", logic="FOMP", stock="Stock",
          fomp_f_labile=0.3,
          fomp_k_labile=15.95,
          fomp_k_recalcitrant=0.05,
          fomp_outflow_id="F_03_01")

    # P4: long-lived construction use (DSM)
    _post(client, f"/{STUDY}/processes/new",
          name="Construction", logic="DSM", stock="Stock",
          dsm_lifetime_mean=50.0,
          dsm_lifetime_std=15.0,
          dsm_lifetime_distribution="Normal")


# ─────────────────────────────────────────────────────────────────────────────
# §3  Flows & Input Data
# ─────────────────────────────────────────────────────────────────────────────

def _create_flows(client) -> None:
    pairs = [
        ("F_01_02", "Straw Supply",         1, 2),
        ("F_02_03", "To Soil",              2, 3),
        ("F_02_04", "To Construction",      2, 4),
        ("F_03_01", "CO2 to Atmosphere",    3, 1),
        ("F_04_01", "EoL to Atmosphere",    4, 1),
    ]
    for fid, fname, frm, to in pairs:
        _post(client, f"/{STUDY}/flows/new",
              id=fid, name=fname, from_process=frm, to_process=to)


def _save_static_tcs(client) -> None:
    # P2 = Splitter; only material is validated (must sum to 1.0).
    # All elements sent in ONE request — the route clears all TCs for the
    # process before saving, so sending one element at a time would overwrite.
    data = {}
    for elem in ("material", "WC", "DM", "TC"):
        data[f"tc_F_02_03_{elem}"] = "0.4"
        data[f"tc_F_02_04_{elem}"] = "0.6"
    _post(client, f"/{STUDY}/tcs/2", **data)


def _save_flow_compositions(client) -> None:
    # Only F_01_02 comes from an Input process (P1) — that's what the route shows
    _post(
        client,
        f"/{STUDY}/compositions",
        **{
            "comp_F_01_02_material": "1.0",
            "comp_F_01_02_WC":       "0.20",
            "comp_F_01_02_DM":       "0.80",
            "comp_F_01_02_TC":       "0.45",
        },
    )


def _save_flow_data(client) -> None:
    # F_01_02: annual straw supply (two anchor points — engine interpolates)
    _post(
        client,
        f"/{STUDY}/flow_data",
        fd_0_id="F_01_02",
        fd_0_y_0=2025,
        fd_0_v_0=1000.0,
        fd_0_y_1=2125,
        fd_0_v_1=1500.0,
    )


# ─────────────────────────────────────────────────────────────────────────────
# §5  Scenario & Uncertainty Management
# ─────────────────────────────────────────────────────────────────────────────

def _create_scenario(client) -> None:
    # Create the scenario entry
    _post(client, f"/{STUDY}/scenarios/new", scenario_name="Baseline_DI")

    # Save one modification: TC for F_02_03 material fraction
    _post(
        client,
        f"/{STUDY}/scenarios/Baseline_DI",
        mod_0_parameter_name="TC_02_03",
        mod_0_parameter_type="TC",
        mod_0_operation="replace",
        mod_0_new_value=0.35,
    )


def _save_mc_parameters(client) -> None:
    # One uncertain parameter: Splitter TC material fraction for F_02_03
    _post(
        client,
        f"/{STUDY}/mc_parameters",
        mc_0_parameter_id="TC_02_03",
        mc_0_enabled="on",
        mc_0_distribution="normal",
        mc_0_mean=0.40,
        mc_0_std=0.05,
        mc_0_operation="replace",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Export helper
# ─────────────────────────────────────────────────────────────────────────────

def _export_yaml(client) -> dict:
    r = client.get(f"/{STUDY}/export")
    assert r.status_code == 200, f"Export failed: {r.status_code}"
    assert "yaml" in r.headers.get("content-type", "")
    return yaml.safe_load(r.content)


# ─────────────────────────────────────────────────────────────────────────────
# Full end-to-end test
# ─────────────────────────────────────────────────────────────────────────────

class TestFullWorkflow:
    """
    Walk through the entire user journey and validate the resulting YAML.

    Each _create_* / _save_* helper corresponds to one dashboard section.
    Failures report which step broke and the first 500 chars of the response.
    """

    def test_complete_study_workflow(self, client):
        # ── §1 Create + configure ─────────────────────────────────────────────
        _create_study(client)
        _configure_model(client)

        # ── §2 Processes ──────────────────────────────────────────────────────
        _create_processes(client)

        # ── §3 Flows + data ───────────────────────────────────────────────────
        _create_flows(client)
        _save_static_tcs(client)
        _save_flow_compositions(client)
        _save_flow_data(client)

        # ── §5 Scenarios + MC ─────────────────────────────────────────────────
        _create_scenario(client)
        _save_mc_parameters(client)

        # ── Export ────────────────────────────────────────────────────────────
        data = _export_yaml(client)

        # ── Validate YAML schema round-trip ───────────────────────────────────
        from app.models.config_schema import CaseStudyConfig
        cfg = CaseStudyConfig.model_validate(data)

        # ── §1 Model settings ─────────────────────────────────────────────────
        assert cfg.model.start_year == 2025
        assert cfg.model.end_year == 2125
        assert cfg.model.elements == ["material", "WC", "DM", "TC"]
        assert cfg.model.run_fomp_calculation is True
        assert cfg.model.run_dsm_calculation is True
        assert cfg.model.run_monte_carlo is True
        assert cfg.model.run_scenario_analysis is True

        # ── §2 Processes ──────────────────────────────────────────────────────
        assert len(cfg.processes) == 4

        by_name = {p.name: p for p in cfg.processes}
        assert "Atmosphere" in by_name
        assert "Field" in by_name
        assert "Soil_Inc" in by_name
        assert "Construction" in by_name

        # FOMP params persisted through process creation
        soil = by_name["Soil_Inc"]
        assert soil.fomp is not None
        assert soil.fomp.f_labile == pytest.approx(0.3)
        assert soil.fomp.k_labile == pytest.approx(15.95)
        assert soil.fomp.k_recalcitrant == pytest.approx(0.05)

        # DSM params persisted through process creation
        construction = by_name["Construction"]
        assert construction.dsm is not None
        assert construction.dsm.lifetime_mean == pytest.approx(50.0)
        assert construction.dsm.lifetime_std == pytest.approx(15.0)

        # ── §3 Flows ──────────────────────────────────────────────────────────
        assert len(cfg.flows) == 5
        flow_ids = {f.id for f in cfg.flows}
        assert {"F_01_02", "F_02_03", "F_02_04", "F_03_01", "F_04_01"} == flow_ids

        # ── §3 Splitter TCs ───────────────────────────────────────────────────
        # P2 (Field, Splitter): material must be the splitting element
        splitter_pid = by_name["Field"].id
        splitter_tcs = [tc for tc in cfg.transfer_coefficients if tc.process_id == splitter_pid]
        assert len(splitter_tcs) == 2, "Splitter must have exactly 2 outgoing TCs"

        tc_map = {tc.flow_id: tc for tc in splitter_tcs}
        assert "F_02_03" in tc_map
        assert "F_02_04" in tc_map

        # Material fractions must be present and sum to 1.0
        mat_03 = tc_map["F_02_03"].values.get("material", None)
        mat_04 = tc_map["F_02_04"].values.get("material", None)
        assert mat_03 is not None, "Splitter TC F_02_03 missing 'material' key"
        assert mat_04 is not None, "Splitter TC F_02_04 missing 'material' key"
        assert mat_03 + mat_04 == pytest.approx(1.0, abs=1e-6)

        # ── §3 Flow compositions ──────────────────────────────────────────────
        comp_map = {fc.flow_id: fc for fc in cfg.flow_compositions}
        assert "F_01_02" in comp_map, "Flow composition for input flow F_01_02 missing"
        comp = comp_map["F_01_02"]
        assert comp.values.get("WC", 0) == pytest.approx(0.20)
        assert comp.values.get("DM", 0) == pytest.approx(0.80)
        assert comp.values.get("TC", 0) == pytest.approx(0.45)

        # ── §3 Flow data ──────────────────────────────────────────────────────
        fd_map = {fd.flow_id: fd for fd in cfg.flow_data}
        assert "F_01_02" in fd_map, "Flow data for F_01_02 missing"
        fd = fd_map["F_01_02"]
        assert 2025 in fd.values
        assert fd.values[2025] == pytest.approx(1000.0)

        # ── §5 Scenario ───────────────────────────────────────────────────────
        assert len(cfg.scenarios) == 1
        scenario = cfg.scenarios[0]
        assert scenario.name == "Baseline_DI"
        assert len(scenario.modifications) == 1
        mod = scenario.modifications[0]
        assert mod.parameter_name == "TC_02_03"
        assert mod.new_value == pytest.approx(0.35)

        # ── §5 MC parameters ─────────────────────────────────────────────────
        assert len(cfg.mc_parameters) == 1
        mc = cfg.mc_parameters[0]
        assert mc.parameter_id == "TC_02_03"
        assert mc.distribution == "normal"
        assert mc.mean == pytest.approx(0.40)
        assert mc.std == pytest.approx(0.05)
