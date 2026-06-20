# -*- coding: utf-8 -*-
"""Tests for the SystemDefiner hardening audit (cascade deletes, safe names,
404 consistency, input guards)."""
from __future__ import annotations

import pytest

from systemdefiner import storage
from systemdefiner.models.config_schema import (
    BomAssemblyEntry,
    BomAssemblyFlow,
    CaseStudyConfig,
    Flow,
    FlowDataEntry,
    FompParams,
    McParameter,
    ModelSettings,
    Process,
    ProcessLogic,
    ScenarioDefinition,
    ScenarioModification,
    StockConfig,
    TCConfig,
    TransferCoefficient,
)


def _seed_linked_study(name: str = "t") -> CaseStudyConfig:
    """A study where P2 is wired to flows, TCs, BOM, FOMP outflow, scenario & MC."""
    cfg = CaseStudyConfig(name=name, model=ModelSettings())
    cfg.processes = [
        Process(id=1, name="P1", logic=ProcessLogic.input, stock=StockConfig.no_stock, tc_config=TCConfig.no_tc),
        Process(id=2, name="P2", logic=ProcessLogic.splitter, stock=StockConfig.no_stock, tc_config=TCConfig.static),
        Process(id=3, name="P3", logic=ProcessLogic.fomp, stock=StockConfig.no_stock, tc_config=TCConfig.no_tc),
    ]
    cfg.flows = [
        Flow(id="F_01_02", name="in", from_process=1, to_process=2),
        Flow(id="F_02_03", name="mid", from_process=2, to_process=3),
        Flow(id="F_03_01", name="out", from_process=3, to_process=1),
    ]
    cfg.transfer_coefficients = [
        TransferCoefficient(process_id=2, flow_id="F_02_03", values={"material": 1.0}),
    ]
    cfg.flow_data = [FlowDataEntry(flow_id="F_01_02", values={2025: 10.0})]
    cfg.processes[2].fomp = FompParams(outflow_id="F_02_03")
    cfg.scenarios = [ScenarioDefinition(
        name="s", modifications=[ScenarioModification(parameter_name="F_02_03", parameter_type="Flow")])]
    cfg.mc_parameters = [McParameter(parameter_id="F_02_03")]
    storage.save_case_study(cfg)
    return cfg


# ── Cascade deletes ─────────────────────────────────────────────────────────

class TestProcessDeleteCascade:
    def test_delete_removes_dependents(self, client):
        _seed_linked_study()
        r = client.post("/t/processes/2/delete", follow_redirects=False)
        assert r.status_code == 303
        g = storage.load_case_study("t")
        assert [p.id for p in g.processes] == [1, 3]
        # both flows touching P2 are gone
        assert {f.id for f in g.flows} == {"F_03_01"}
        # all references to the removed flows are gone
        assert g.transfer_coefficients == []
        assert g.flow_data == []
        assert g.processes[1].fomp.outflow_id == ""   # P3 FOMP outflow cleared
        assert all(not s.modifications for s in g.scenarios)
        assert g.mc_parameters == []

    def test_flow_delete_purges_references(self, client):
        _seed_linked_study()
        r = client.post("/t/flows/F_02_03/delete", follow_redirects=False)
        assert r.status_code == 303
        g = storage.load_case_study("t")
        assert "F_02_03" not in {f.id for f in g.flows}
        assert g.transfer_coefficients == []
        assert g.processes[2].fomp.outflow_id == ""


# ── Safe names / path traversal ─────────────────────────────────────────────

class TestSafeNames:
    @pytest.mark.parametrize("bad", ["..", "../etc", "a/b", "a\\b", "", "."])
    def test_unsafe_names_rejected(self, bad):
        assert storage.case_study_exists(bad) is False
        with pytest.raises(storage.CaseStudyNotFound):
            storage.load_case_study(bad)

    def test_traversal_url_returns_404(self, client):
        r = client.get("/..%2F..%2Fconfig")
        assert r.status_code == 404


# ── 404 consistency ─────────────────────────────────────────────────────────

class TestNotFoundConsistency:
    @pytest.mark.parametrize("path", [
        "/nope/processes", "/nope/flows", "/nope/tcs",
        "/nope/scenarios", "/nope/flow_data", "/nope/mc_parameters",
        "/nope/compositions", "/nope/elements",
    ])
    def test_missing_study_is_404_not_500(self, client, path):
        r = client.get(path)
        assert r.status_code == 404
        assert b"Back to Case Studies" in r.content   # friendly error page


# ── Input guards ────────────────────────────────────────────────────────────

class TestInputGuards:
    def _study(self, client):
        client.post("/new", data={"name": "g", "start_year": "2025", "end_year": "2030",
                                  "elements": "material, WC, DM, TC"})
        return "g"

    def test_invalid_logic_and_stock_fall_back(self, client):
        n = self._study(client)
        r = client.post(f"/{n}/processes/new",
                        data={"name": "X", "logic": "BOGUS", "stock": "NONSENSE", "tc_config": "No TC"},
                        follow_redirects=False)
        assert r.status_code == 303
        g = storage.load_case_study(n)
        assert g.processes[-1].logic == ProcessLogic.splitter
        assert g.processes[-1].stock == StockConfig.no_stock

    def test_fomp_empty_fields_use_defaults(self, client):
        n = self._study(client)
        r = client.post(f"/{n}/processes/new",
                        data={"name": "F", "logic": "FOMP", "stock": "No_Stock", "tc_config": "No TC",
                              "fomp_f_labile": "", "fomp_k_labile": ""},
                        follow_redirects=False)
        assert r.status_code == 303
        g = storage.load_case_study(n)
        fomp = [p for p in g.processes if p.logic == ProcessLogic.fomp][0].fomp
        assert fomp.f_labile == 0.5
        assert fomp.k_labile == 1.0
