# -*- coding: utf-8 -*-
"""Mutation-route consistency tests.

Each test replays a mutation sequence from the 2026-07 SystemDefiner audit and
asserts (a) the specific references were cascaded/purged and (b)
``check_config_consistency`` reports no errors afterwards.
"""
from __future__ import annotations

import pytest

from systemdefiner import storage
from systemdefiner.cascades import (
    _compact_process_ids,
    _purge_flow_references,
    _remap_embedded_ids,
    _rename_flow_id,
)
from systemdefiner.consistency import check_config_consistency
from systemdefiner.models.config_schema import (
    CaseStudyConfig,
    DsmComponentItem,
    DsmParams,
    Flow,
    FlowCapParams,
    FlowComposition,
    FlowDataEntry,
    FompParams,
    McParameter,
    Process,
    ProcessLogic,
    ScenarioDefinition,
    ScenarioModification,
    StockConfig,
    TCConfig,
    TransferCoefficient,
)


def _errors(cfg) -> list[str]:
    return [i["message"] for i in check_config_consistency(cfg) if i["level"] == "error"]


def _scenario_names(cfg) -> list[str]:
    return [m.parameter_name for s in cfg.scenarios for m in s.modifications]


def _mc_names(cfg) -> list[str]:
    return [m.parameter_id for m in cfg.mc_parameters]


# ══════════════════════════════════════════════════════════════════════════════
# Renumber (Findings 1, 7, 11b)
# ══════════════════════════════════════════════════════════════════════════════


def _gapped_study(name="renumber_test") -> CaseStudyConfig:
    """P0 Input, P1 Splitter, P3 FOMP, P4 Output — gap at ID 2."""
    cfg = CaseStudyConfig(
        name=name,
        processes=[
            Process(id=0, name="Source", logic=ProcessLogic.input),
            Process(
                id=1, name="Sorter", logic=ProcessLogic.splitter, tc_config=TCConfig.static
            ),
            Process(
                id=3,
                name="Soil",
                logic=ProcessLogic.fomp,
                stock=StockConfig.stock,
                fomp=FompParams(outflow_id="F_03_04"),
            ),
            Process(id=4, name="Sink", logic=ProcessLogic.output),
        ],
        flows=[
            Flow(id="F_00_01", name="in", from_process=0, to_process=1),
            Flow(id="F_01_03", name="a", from_process=1, to_process=3),
            Flow(id="F_01_03_2", name="b", from_process=1, to_process=3),
            Flow(id="F_03_04", name="out", from_process=3, to_process=4),
        ],
        transfer_coefficients=[
            TransferCoefficient(
                process_id=1, flow_id="F_01_03", tc_type="static", values={"material": 1.0}
            ),
        ],
        flow_data=[FlowDataEntry(flow_id="F_00_01", values={2025: 100.0})],
        flow_compositions=[
            FlowComposition(flow_id="F_00_01", values={"material": 1.0})
        ],
        scenarios=[
            ScenarioDefinition(
                name="S1",
                modifications=[
                    ScenarioModification(parameter_name="F_01_03", operation="multiply", new_value=1.1),
                    ScenarioModification(parameter_name="TC_E1_01_03", operation="replace", new_value=0.5),
                    ScenarioModification(
                        parameter_name="P03_decay_k1 (Labile pool)", operation="replace", new_value=2.0
                    ),
                ],
            )
        ],
        mc_parameters=[
            McParameter(parameter_id="TC_E1_01_03", distribution="normal", mean=1.0, std=0.1),
            McParameter(
                parameter_id="P03_decay_k1 (Labile pool)", distribution="normal", mean=1.0, std=0.1
            ),
        ],
    )
    return cfg


class TestRenumber:
    def test_renumber_remaps_scenario_and_mc_names(self, client):
        storage.save_case_study(_gapped_study())
        client.post("/renumber_test/processes/renumber")
        cfg = storage.load_case_study("renumber_test")
        assert _scenario_names(cfg) == [
            "F_01_02",
            "TC_E1_01_02",
            "P02_decay_k1 (Labile pool)",
        ]
        assert _mc_names(cfg) == ["TC_E1_01_02", "P02_decay_k1 (Labile pool)"]
        assert _errors(cfg) == []

    def test_renumber_renames_suffixed_duplicate_edges(self, client):
        storage.save_case_study(_gapped_study())
        client.post("/renumber_test/processes/renumber")
        cfg = storage.load_case_study("renumber_test")
        flow_ids = {f.id for f in cfg.flows}
        assert flow_ids == {"F_00_01", "F_01_02", "F_01_02_2", "F_02_03"}
        # the duplicate edge kept its suffix and follows the new endpoints
        f2 = next(f for f in cfg.flows if f.id == "F_01_02_2")
        assert (f2.from_process, f2.to_process) == (1, 2)

    def test_renumber_updates_fomp_outflow_pointer(self, client):
        storage.save_case_study(_gapped_study())
        client.post("/renumber_test/processes/renumber")
        cfg = storage.load_case_study("renumber_test")
        soil = next(p for p in cfg.processes if p.name == "Soil")
        assert soil.id == 2
        assert soil.fomp.outflow_id == "F_02_03"

    def test_renumber_remaps_flowcap_cap_tc_id(self, client):
        cfg = CaseStudyConfig(
            name="cap_renumber",
            processes=[
                Process(id=0, name="Source", logic=ProcessLogic.input),
                Process(
                    id=3,
                    name="Cap",
                    logic=ProcessLogic.flowcap,
                    flowcap=FlowCapParams(
                        capped_flow_id="F_03_04",
                        cap_series={2025: 10.0},
                        cap_tc_id="TC_Cap_03",
                    ),
                ),
                Process(id=4, name="Sink", logic=ProcessLogic.output),
            ],
            flows=[
                Flow(id="F_00_03", name="in", from_process=0, to_process=3),
                Flow(id="F_03_04", name="capped", from_process=3, to_process=4),
            ],
            scenarios=[
                ScenarioDefinition(
                    name="S1",
                    modifications=[
                        ScenarioModification(parameter_name="TC_Cap_03", new_value=20.0)
                    ],
                )
            ],
        )
        storage.save_case_study(cfg)
        client.post("/cap_renumber/processes/renumber")
        cfg = storage.load_case_study("cap_renumber")
        cap = next(p for p in cfg.processes if p.name == "Cap")
        assert cap.id == 1
        assert cap.flowcap.cap_tc_id == "TC_Cap_01"
        assert _scenario_names(cfg) == ["TC_Cap_01"]
        assert _errors(cfg) == []

    def test_remap_leaves_dangling_and_custom_names_alone(self):
        id_map = {0: 0, 1: 1, 3: 2}
        assert _remap_embedded_ids("P09_decay_k1 (Labile pool)", id_map) == (
            "P09_decay_k1 (Labile pool)"
        )
        assert _remap_embedded_ids("My_Custom_Param", id_map) == "My_Custom_Param"
        assert _remap_embedded_ids("TC_E1_03_09", id_map) == "TC_E1_03_09"


# ══════════════════════════════════════════════════════════════════════════════
# Process delete + ID reuse (Finding 2)
# ══════════════════════════════════════════════════════════════════════════════


class TestDeleteProcess:
    def _study(self, name="delete_test") -> CaseStudyConfig:
        return CaseStudyConfig(
            name=name,
            processes=[
                Process(id=0, name="Source", logic=ProcessLogic.input),
                Process(id=1, name="Sorter", logic=ProcessLogic.splitter),
                Process(
                    id=2,
                    name="Soil",
                    logic=ProcessLogic.fomp,
                    stock=StockConfig.stock,
                    fomp=FompParams(outflow_id="F_02_03"),
                ),
                Process(id=3, name="Sink", logic=ProcessLogic.output),
            ],
            flows=[
                Flow(id="F_00_01", name="in", from_process=0, to_process=1),
                Flow(id="F_01_02", name="mid", from_process=1, to_process=2),
                Flow(id="F_02_03", name="out", from_process=2, to_process=3),
            ],
            scenarios=[
                ScenarioDefinition(
                    name="S1",
                    modifications=[
                        ScenarioModification(
                            parameter_name="P02_decay_k1 (Labile pool)", new_value=2.0
                        ),
                        ScenarioModification(parameter_name="TC_E1_01_02", new_value=0.5),
                        ScenarioModification(parameter_name="F_00_01", new_value=1.1),
                    ],
                )
            ],
            mc_parameters=[
                McParameter(
                    parameter_id="P02_decay_k1 (Labile pool)",
                    distribution="normal",
                    mean=1.0,
                    std=0.1,
                ),
            ],
        )

    def test_delete_purges_embedded_param_names(self, client):
        storage.save_case_study(self._study())
        client.post("/delete_test/processes/2/delete")
        cfg = storage.load_case_study("delete_test")
        # P02_… (embedded pid) and TC_E1_01_02 (pair touches P2) are gone;
        # the unrelated flow modification survives.
        assert _scenario_names(cfg) == ["F_00_01"]
        assert _mc_names(cfg) == []
        assert _errors(cfg) == []

    def test_reused_id_does_not_inherit_stale_params(self, client):
        storage.save_case_study(self._study())
        client.post("/delete_test/processes/2/delete")
        # process_new fills the gap → new process gets ID 2
        client.post(
            "/delete_test/processes/new",
            data={"name": "NewProc", "logic": "Splitter", "stock": "No_Stock"},
        )
        cfg = storage.load_case_study("delete_test")
        new = next(p for p in cfg.processes if p.name == "NewProc")
        assert new.id == 2
        # nothing referencing P2 remains from the deleted FOMP process
        assert all("P02" not in n for n in _scenario_names(cfg) + _mc_names(cfg))
        assert _errors(cfg) == []


# ══════════════════════════════════════════════════════════════════════════════
# DSM_Component spare-part flow pointers (Finding 3)
# ══════════════════════════════════════════════════════════════════════════════


def _dsm_component_study(name="sparepart_test") -> CaseStudyConfig:
    return CaseStudyConfig(
        name=name,
        model={"elements": ["material", "electronics", "housing"]},
        processes=[
            Process(id=0, name="Source", logic=ProcessLogic.input),
            Process(
                id=1,
                name="Printers",
                logic=ProcessLogic.dsm_component,
                stock=StockConfig.stock,
                dsm=DsmParams(
                    components=[
                        DsmComponentItem(
                            element="electronics",
                            mean_lifetime=5.0,
                            sparepart_outflow="F_01_02",
                            sparepart_inflow="F_00_01",
                        )
                    ]
                ),
            ),
            Process(id=2, name="WEEE", logic=ProcessLogic.output),
        ],
        flows=[
            Flow(id="F_00_01", name="parts in", from_process=0, to_process=1),
            Flow(id="F_01_02", name="worn parts", from_process=1, to_process=2),
        ],
    )


class TestSparepartPointers:
    def test_rename_cascades_to_sparepart_fields(self):
        cfg = _dsm_component_study()
        _rename_flow_id(cfg, "F_01_02", "F_01_09")
        comp = cfg.processes[1].dsm.components[0]
        assert comp.sparepart_outflow == "F_01_09"

    def test_purge_blanks_sparepart_fields(self):
        cfg = _dsm_component_study()
        _purge_flow_references(cfg, {"F_00_01"})
        comp = cfg.processes[1].dsm.components[0]
        assert comp.sparepart_inflow == ""
        assert comp.sparepart_outflow == "F_01_02"  # untouched

    def test_renumber_cascades_to_sparepart_fields(self):
        cfg = _dsm_component_study()
        # introduce a gap: shift everything up by deleting nothing but renaming ids
        for p in cfg.processes:
            if p.id >= 1:
                p.id += 1  # ids: 0, 2, 3
        for f in cfg.flows:
            if f.from_process >= 1:
                f.from_process += 1
            if f.to_process >= 1:
                f.to_process += 1
        cfg.flows[0].id = "F_00_02"
        cfg.flows[1].id = "F_02_03"
        comp = cfg.processes[1].dsm.components[0]
        comp.sparepart_inflow = "F_00_02"
        comp.sparepart_outflow = "F_02_03"
        _compact_process_ids(cfg)
        assert comp.sparepart_inflow == "F_00_01"
        assert comp.sparepart_outflow == "F_01_02"

    def test_flow_delete_route_blanks_sparepart(self, client):
        storage.save_case_study(_dsm_component_study())
        client.post("/sparepart_test/flows/F_01_02/delete")
        cfg = storage.load_case_study("sparepart_test")
        comp = cfg.processes[1].dsm.components[0]
        assert comp.sparepart_outflow == ""

    def test_flow_rewire_route_follows_sparepart(self, client):
        cfg = _dsm_component_study()
        cfg.processes.append(Process(id=3, name="Recycler", logic=ProcessLogic.output))
        storage.save_case_study(cfg)
        # rewire worn-parts flow to the recycler → ID auto-syncs to F_01_03
        client.post(
            "/sparepart_test/flows/F_01_02/edit",
            data={"name": "worn parts", "from_process": 1, "to_process": 3},
        )
        cfg = storage.load_case_study("sparepart_test")
        comp = cfg.processes[1].dsm.components[0]
        assert comp.sparepart_outflow == "F_01_03"
