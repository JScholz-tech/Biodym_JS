# -*- coding: utf-8 -*-
"""Unit tests for app/storage.py."""
from __future__ import annotations

import pytest

from systemdefiner.models.config_schema import (
    CaseStudyConfig,
    Flow,
    ModelSettings,
    Process,
    ProcessLogic,
    StockConfig,
    TransferCoefficient,
)
from systemdefiner import storage


def _make_cfg(name: str = "test", **model_kwargs) -> CaseStudyConfig:
    return CaseStudyConfig(name=name, model=ModelSettings(**model_kwargs))


# ── save / load round-trip ────────────────────────────────────────────────────

class TestSaveLoad:
    def test_save_creates_file(self, isolated_case_studies):
        cfg = _make_cfg("mystudy")
        storage.save_case_study(cfg)
        assert (isolated_case_studies / "mystudy" / "config.yaml").exists()

    def test_load_returns_correct_model(self):
        cfg = _make_cfg("s1", start_year=2000, end_year=2080,
                        elements=["material", "WC", "DM"])
        storage.save_case_study(cfg)
        loaded = storage.load_case_study("s1")
        assert loaded.model.start_year == 2000
        assert loaded.model.end_year == 2080
        assert loaded.model.elements == ["material", "WC", "DM"]

    def test_load_preserves_processes_and_flows(self):
        cfg = _make_cfg("s2")
        cfg.processes = [
            Process(id=1, name="Input", logic=ProcessLogic.input),
            Process(id=2, name="FlowCap step", logic=ProcessLogic.flowcap),
            Process(id=3, name="Sink", logic=ProcessLogic.output),
        ]
        cfg.flows = [Flow(id="F_01_02", name="A→B", from_process=1, to_process=2)]
        storage.save_case_study(cfg)

        loaded = storage.load_case_study("s2")
        assert len(loaded.processes) == 3
        assert loaded.processes[1].logic == ProcessLogic.flowcap
        assert loaded.processes[2].logic == ProcessLogic.output
        assert loaded.flows[0].id == "F_01_02"

    def test_load_preserves_transfer_coefficients(self):
        cfg = _make_cfg("s3")
        cfg.transfer_coefficients = [
            TransferCoefficient(process_id=1, flow_id="F_01_02", values={"WC": 0.3, "DM": 0.7})
        ]
        storage.save_case_study(cfg)
        loaded = storage.load_case_study("s3")
        assert loaded.transfer_coefficients[0].values["WC"] == pytest.approx(0.3)

    def test_overwrite_updates_file(self):
        cfg = _make_cfg("s4", start_year=2020)
        storage.save_case_study(cfg)
        cfg.model.start_year = 2030
        storage.save_case_study(cfg)
        loaded = storage.load_case_study("s4")
        assert loaded.model.start_year == 2030

    def test_load_nonexistent_raises(self):
        with pytest.raises(Exception):
            storage.load_case_study("does_not_exist")


# ── list_case_studies ─────────────────────────────────────────────────────────

class TestList:
    def test_empty_dir_returns_empty_list(self):
        assert storage.list_case_studies() == []

    def test_lists_saved_studies(self):
        storage.save_case_study(_make_cfg("alpha"))
        storage.save_case_study(_make_cfg("beta"))
        studies = storage.list_case_studies()
        names = [s["name"] for s in studies]
        assert "alpha" in names
        assert "beta" in names

    def test_summary_fields(self):
        cfg = _make_cfg("summary_test", elements=["material", "WC"])
        cfg.processes = [Process(id=1, name="P", logic=ProcessLogic.splitter)]
        cfg.flows = [Flow(id="F_00_01", name="f", from_process=0, to_process=1)]
        storage.save_case_study(cfg)
        studies = storage.list_case_studies()
        s = next(x for x in studies if x["name"] == "summary_test")
        assert s["processes"] == 1
        assert s["flows"] == 1
        assert "material" in s["elements"]

    def test_corrupt_yaml_shows_question_marks(self, isolated_case_studies):
        bad_dir = isolated_case_studies / "broken"
        bad_dir.mkdir(parents=True)
        (bad_dir / "config.yaml").write_text("start_year: 'not_an_int'\nname: broken\n")
        studies = storage.list_case_studies()
        s = next((x for x in studies if x["name"] == "broken"), None)
        # Should not raise; returns fallback summary
        assert s is not None


# ── delete ────────────────────────────────────────────────────────────────────

class TestDelete:
    def test_delete_removes_directory(self, isolated_case_studies):
        storage.save_case_study(_make_cfg("todelete"))
        assert (isolated_case_studies / "todelete").exists()
        storage.delete_case_study("todelete")
        assert not (isolated_case_studies / "todelete").exists()

    def test_delete_nonexistent_is_noop(self):
        storage.delete_case_study("never_existed")  # should not raise


# ── case_study_exists ─────────────────────────────────────────────────────────

class TestExists:
    def test_false_before_save(self):
        assert not storage.case_study_exists("ghost")

    def test_true_after_save(self):
        storage.save_case_study(_make_cfg("present"))
        assert storage.case_study_exists("present")

    def test_false_after_delete(self):
        storage.save_case_study(_make_cfg("gone"))
        storage.delete_case_study("gone")
        assert not storage.case_study_exists("gone")
