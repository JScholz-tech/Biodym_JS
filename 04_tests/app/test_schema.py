# -*- coding: utf-8 -*-
"""Unit tests for app/models/config_schema.py."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from systemdefiner.models.config_schema import (
    CaseStudyConfig,
    DsmCategory,
    DsmParams,
    Flow,
    FompParams,
    LfgParams,
    ModelSettings,
    Process,
    ProcessLogic,
    StockConfig,
    TransferCoefficient,
)


# ── ProcessLogic enum ─────────────────────────────────────────────────────────

class TestProcessLogicEnum:
    ALL_EXPECTED = [
        "Input", "Output", "Splitter", "Transformer",
        "DSM", "FOMP", "LFG", "BOM_Assembler", "Pass-through", "FlowCap",
    ]

    def test_all_expected_values_present(self):
        values = {e.value for e in ProcessLogic}
        for expected in self.ALL_EXPECTED:
            assert expected in values, f"ProcessLogic missing value: {expected!r}"

    def test_count(self):
        assert len(ProcessLogic) == len(self.ALL_EXPECTED)

    @pytest.mark.parametrize("value", ALL_EXPECTED)
    def test_each_value_roundtrips(self, value):
        logic = ProcessLogic(value)
        assert logic.value == value

    def test_unknown_value_raises(self):
        with pytest.raises(ValueError):
            ProcessLogic("NotALogic")


# ── StockConfig enum ──────────────────────────────────────────────────────────

class TestStockConfigEnum:
    def test_all_values(self):
        expected = {"Stock", "No_Stock", "Stock_with_InitialStock_Cohort", "Stock_with_InitialStock_Decay"}
        assert {e.value for e in StockConfig} == expected


# ── ModelSettings ─────────────────────────────────────────────────────────────

class TestModelSettings:
    def test_defaults(self):
        m = ModelSettings()
        assert m.start_year == 2025
        assert m.end_year == 2125
        assert "material" in m.elements

    def test_elements_from_list(self):
        m = ModelSettings(elements=["material", "WC", "DM"])
        assert m.elements == ["material", "WC", "DM"]

    def test_elements_from_comma_string(self):
        m = ModelSettings(elements="material, WC, DM, TC")
        assert m.elements == ["material", "WC", "DM", "TC"]

    def test_elements_strips_whitespace(self):
        m = ModelSettings(elements="material ,  WC , DM")
        assert m.elements == ["material", "WC", "DM"]

    def test_year_validation(self):
        m = ModelSettings(start_year=2000, end_year=2100)
        assert m.start_year == 2000
        assert m.end_year == 2100


# ── Process ───────────────────────────────────────────────────────────────────

class TestProcess:
    def test_minimal(self):
        p = Process(id=1, name="Soil")
        assert p.id == 1
        assert p.logic == ProcessLogic.splitter
        assert p.stock == StockConfig.no_stock
        assert p.fomp is None
        assert p.dsm is None
        assert p.lfg is None

    def test_fomp_process(self):
        p = Process(id=2, name="FOMP", logic=ProcessLogic.fomp,
                    fomp=FompParams(f_labile=0.6, k_labile=1.5, k_recalcitrant=0.02))
        assert p.logic == ProcessLogic.fomp
        assert p.fomp.f_labile == 0.6

    def test_dsm_process(self):
        p = Process(id=3, name="Building", logic=ProcessLogic.dsm,
                    dsm=DsmParams(categories=[
                        DsmCategory(name="Default", inflow_split=1.0,
                                    lifetime_type="Normal", lifetime_mean=50.0, lifetime_std=10.0)]))
        assert p.dsm.categories[0].lifetime_mean == 50.0
        assert p.dsm.categories[0].lifetime_std == 10.0

    def test_flowcap_logic(self):
        p = Process(id=4, name="Cap", logic=ProcessLogic.flowcap)
        assert p.logic.value == "FlowCap"

    def test_output_logic(self):
        p = Process(id=5, name="Boundary", logic=ProcessLogic.output)
        assert p.logic.value == "Output"

    def test_invalid_logic_raises(self):
        with pytest.raises(ValidationError):
            Process(id=6, name="Bad", logic="UnknownLogic")


# ── Flow ──────────────────────────────────────────────────────────────────────

class TestFlow:
    def test_basic(self):
        f = Flow(id="F_01_02", name="My flow", from_process=1, to_process=2)
        assert f.id == "F_01_02"
        assert f.from_process == 1


# ── TransferCoefficient ───────────────────────────────────────────────────────

class TestTransferCoefficient:
    def test_basic(self):
        tc = TransferCoefficient(process_id=1, flow_id="F_01_02", values={"WC": 0.5, "DM": 0.5})
        assert tc.values["WC"] == 0.5


# ── CaseStudyConfig ───────────────────────────────────────────────────────────

class TestCaseStudyConfig:
    def test_minimal(self):
        cfg = CaseStudyConfig(name="test")
        assert cfg.name == "test"
        assert cfg.processes == []
        assert cfg.flows == []

    def test_model_validate_round_trip(self):
        cfg = CaseStudyConfig(
            name="roundtrip",
            model=ModelSettings(start_year=2000, end_year=2050, elements=["material", "TC"]),
            processes=[Process(id=1, name="Input", logic=ProcessLogic.input)],
            flows=[Flow(id="F_00_01", name="flow", from_process=0, to_process=1)],
        )
        dumped = cfg.model_dump(mode="json")
        restored = CaseStudyConfig.model_validate(dumped)
        assert restored.name == "roundtrip"
        assert restored.model.start_year == 2000
        assert restored.processes[0].logic == ProcessLogic.input
        assert restored.flows[0].id == "F_00_01"

    def test_model_validate_with_flowcap_and_output(self):
        """Regression: FlowCap and Output must survive a YAML round-trip."""
        raw = {
            "name": "test",
            "model": {"start_year": 2015, "end_year": 2040, "elements": ["material"]},
            "processes": [
                {"id": 1, "name": "Cap", "logic": "FlowCap", "stock": "No_Stock"},
                {"id": 2, "name": "Boundary", "logic": "Output", "stock": "No_Stock"},
            ],
            "flows": [],
            "transfer_coefficients": [],
        }
        cfg = CaseStudyConfig.model_validate(raw)
        assert cfg.processes[0].logic == ProcessLogic.flowcap
        assert cfg.processes[1].logic == ProcessLogic.output
