# -*- coding: utf-8 -*-
"""Integration tests for all FastAPI routes (app/main.py)."""
from __future__ import annotations

import io

import pytest

from conftest import make_excel_bytes


# ══════════════════════════════════════════════════════════════════════════════
# HOME / CASE STUDY CRUD
# ══════════════════════════════════════════════════════════════════════════════

class TestHome:
    def test_get_index(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert b"BioDYM" in r.content

    def test_new_case_study_redirects(self, client):
        r = client.post("/new", data={"name": "MyStudy", "start_year": 2020, "end_year": 2080, "elements": "material, WC"}, follow_redirects=False)
        assert r.status_code == 303
        assert r.headers["location"].startswith("/MyStudy")

    def test_new_case_study_appears_in_list(self, client):
        client.post("/new", data={"name": "Listed", "start_year": 2020, "end_year": 2080, "elements": "material"})
        r = client.get("/")
        assert b"Listed" in r.content

    def test_duplicate_name_returns_400(self, client):
        client.post("/new", data={"name": "Dup", "start_year": 2020, "end_year": 2080, "elements": "material"})
        r = client.post("/new", data={"name": "Dup", "start_year": 2020, "end_year": 2080, "elements": "material"})
        assert r.status_code == 400

    def test_empty_name_returns_400(self, client):
        r = client.post("/new", data={"name": "   ", "start_year": 2020, "end_year": 2080, "elements": "material"})
        assert r.status_code == 400

    def test_delete_case_study(self, client):
        client.post("/new", data={"name": "ToDelete", "start_year": 2020, "end_year": 2080, "elements": "material"})
        r = client.post("/ToDelete/delete", follow_redirects=False)
        assert r.status_code == 303
        r2 = client.get("/ToDelete")
        assert r2.status_code == 404

    def test_get_nonexistent_returns_404(self, client):
        r = client.get("/ghost")
        assert r.status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# CASE STUDY OVERVIEW / SETTINGS
# ══════════════════════════════════════════════════════════════════════════════

class TestCaseStudyOverview:
    def _create(self, client, name="cs1"):
        client.post("/new", data={"name": name, "start_year": 2025, "end_year": 2125, "elements": "material, WC"})
        return name

    def test_overview_page_loads(self, client):
        name = self._create(client)
        r = client.get(f"/{name}")
        assert r.status_code == 200
        assert b"material" in r.content

    def test_update_settings(self, client):
        name = self._create(client)
        r = client.post(f"/{name}/settings",
                        data={"start_year": 2000, "end_year": 2100, "elements": "material, TC"},
                        follow_redirects=True)
        assert r.status_code == 200
        assert b"2000" in r.content
        assert b"2100" in r.content

    def test_update_settings_persists_mc_seed_and_solver(self, client):
        from systemdefiner import storage

        name = self._create(client)
        client.post(
            f"/{name}/settings",
            data={
                "start_year": 2025,
                "end_year": 2125,
                "mc_iterations": 500,
                "mc_seed": "1234",
                "solver_strict": "on",
                "solver_max_iterations": 60,
            },
            follow_redirects=True,
        )
        cfg = storage.load_case_study(name)
        assert cfg.model.mc_seed == "1234"
        assert cfg.model.solver_strict is True
        assert cfg.model.solver_max_iterations == 60

    def test_settings_form_exposes_new_fields(self, client):
        name = self._create(client)
        html = client.get(f"/{name}").content
        assert b'name="mc_seed"' in html
        assert b'name="solver_strict"' in html
        assert b'name="solver_max_iterations"' in html


# ══════════════════════════════════════════════════════════════════════════════
# PROCESSES
# ══════════════════════════════════════════════════════════════════════════════

class TestProcesses:
    def _study(self, client, name="proc_test"):
        client.post("/new", data={"name": name, "start_year": 2025, "end_year": 2125, "elements": "material"})
        return name

    def test_processes_list_loads(self, client):
        n = self._study(client)
        assert client.get(f"/{n}/processes").status_code == 200

    def test_create_process(self, client):
        n = self._study(client)
        r = client.post(f"/{n}/processes/new", data={"name": "Soil", "logic": "FOMP", "stock": "Stock"}, follow_redirects=True)
        assert r.status_code == 200
        assert b"Soil" in r.content

    def test_create_flowcap_process(self, client):
        n = self._study(client)
        r = client.post(f"/{n}/processes/new", data={"name": "Cap", "logic": "FlowCap", "stock": "No_Stock"}, follow_redirects=True)
        assert r.status_code == 200
        assert b"Cap" in r.content

    def test_create_output_process(self, client):
        n = self._study(client)
        r = client.post(f"/{n}/processes/new", data={"name": "Sink", "logic": "Output", "stock": "No_Stock"}, follow_redirects=True)
        assert r.status_code == 200
        assert b"Sink" in r.content

    def test_edit_process_form_loads(self, client):
        n = self._study(client)
        client.post(f"/{n}/processes/new", data={"name": "P", "logic": "Splitter", "stock": "No_Stock"})
        r = client.get(f"/{n}/processes/0/edit")
        assert r.status_code == 200

    def test_edit_process_saves(self, client):
        n = self._study(client)
        client.post(f"/{n}/processes/new", data={"name": "Old", "logic": "Splitter", "stock": "No_Stock"})
        client.post(f"/{n}/processes/0/edit", data={"name": "New", "logic": "Transformer", "stock": "No_Stock"})
        r = client.get(f"/{n}/processes")
        assert b"New" in r.content

    def test_delete_process(self, client):
        n = self._study(client)
        client.post(f"/{n}/processes/new", data={"name": "Remove", "logic": "Splitter", "stock": "No_Stock"})
        client.post(f"/{n}/processes/0/delete")
        r = client.get(f"/{n}/processes")
        assert b"Remove" not in r.content

    def test_edit_nonexistent_process_returns_404(self, client):
        n = self._study(client)
        r = client.get(f"/{n}/processes/999/edit")
        assert r.status_code == 404

    def _flowcap_form(self, name="Cap", **extra):
        data = {
            "name": name,
            "logic": "FlowCap",
            "stock": "No_Stock",
            "flowcap_capped_flow_id": "F_01_02",
            "flowcap_overflow_flow_id": "F_01_03",
            "flowcap_year_0": "2025",
            "flowcap_cap_0": "100",
        }
        data.update(extra)
        return data

    def test_flowcap_save_auto_derives_cap_tc_id(self, client):
        from systemdefiner import storage
        n = self._study(client)
        client.post(f"/{n}/processes/new", data=self._flowcap_form())
        cfg = storage.load_case_study(n)
        proc = next(p for p in cfg.processes if p.name == "Cap")
        assert proc.flowcap.cap_tc_id == f"TC_Cap_{proc.id:02d}"

    def test_flowcap_save_preserves_custom_cap_tc_id(self, client):
        from systemdefiner import storage
        n = self._study(client)
        client.post(f"/{n}/processes/new", data=self._flowcap_form())
        cfg = storage.load_case_study(n)
        pid = next(p.id for p in cfg.processes if p.name == "Cap")
        client.post(
            f"/{n}/processes/{pid}/edit",
            data=self._flowcap_form(flowcap_cap_tc_id="TC_Cap_Custom"),
        )
        cfg = storage.load_case_study(n)
        proc = next(p for p in cfg.processes if p.id == pid)
        assert proc.flowcap.cap_tc_id == "TC_Cap_Custom"

    def test_flowcap_resave_keeps_cap_tc_id(self, client):
        # Re-saving via the form (which pre-fills the field) must not wipe the ID
        from systemdefiner import storage
        n = self._study(client)
        client.post(f"/{n}/processes/new", data=self._flowcap_form())
        cfg = storage.load_case_study(n)
        pid = next(p.id for p in cfg.processes if p.name == "Cap")
        expected = f"TC_Cap_{pid:02d}"
        r = client.get(f"/{n}/processes/{pid}/edit")
        assert expected.encode() in r.content  # field is pre-filled
        client.post(f"/{n}/processes/{pid}/edit", data=self._flowcap_form())
        cfg = storage.load_case_study(n)
        proc = next(p for p in cfg.processes if p.id == pid)
        assert proc.flowcap.cap_tc_id == expected


# ══════════════════════════════════════════════════════════════════════════════
# SCENARIO / MC PARAMETER CATALOG
# ══════════════════════════════════════════════════════════════════════════════

class TestParameterCatalog:
    def _cfg_with_flowcap_and_is(self):
        from systemdefiner.models.config_schema import (
            CaseStudyConfig,
            Flow,
            FlowCapParams,
            InitialStockEntry,
            Process,
            ProcessLogic,
            StockConfig,
        )

        return CaseStudyConfig(
            name="catalog_test",
            processes=[
                Process(id=0, name="Boundary", logic=ProcessLogic.input),
                Process(
                    id=1,
                    name="Sorting",
                    logic=ProcessLogic.flowcap,
                    flowcap=FlowCapParams(
                        capped_flow_id="F_01_02",
                        overflow_flow_id="F_01_03",
                        cap_series={2025: 100.0},
                        cap_tc_id="TC_Cap_01",
                    ),
                ),
                Process(
                    id=2,
                    name="Store",
                    logic=ProcessLogic.splitter,
                    stock=StockConfig.initial_stock_decay,
                ),
            ],
            flows=[
                Flow(id="F_00_01", name="In", from_process=0, to_process=1),
                Flow(id="F_01_02", name="Capped", from_process=1, to_process=2),
                Flow(id="F_01_03", name="Overflow", from_process=1, to_process=2),
            ],
            initial_stocks=[
                InitialStockEntry(
                    process_id=2,
                    material_quantity=500.0,
                    composition={"WC": 0.1, "DM": 0.9, "TC": 0.4},
                )
            ],
        )

    def test_catalog_offers_flowcap_cap(self):
        from systemdefiner.main import _build_scenario_params

        params = _build_scenario_params(self._cfg_with_flowcap_and_is())
        cap = next((p for p in params if p["group"] == "FlowCap"), None)
        assert cap is not None
        assert cap["name"] == "TC_Cap_01"
        assert cap["type"] == ""  # must bypass TC normalization
        assert not cap.get("scenario_only")  # cap works in MC too

    def test_catalog_flowcap_falls_back_to_derived_id(self):
        from systemdefiner.main import _build_scenario_params

        cfg = self._cfg_with_flowcap_and_is()
        cfg.processes[1].flowcap.cap_tc_id = ""
        params = _build_scenario_params(cfg)
        cap = next(p for p in params if p["group"] == "FlowCap")
        assert cap["name"] == "TC_Cap_01"

    def test_catalog_hides_lfg_parameters(self):
        # The engine cannot apply LFG parameter modifications (no LFG branch
        # in apply_scenario, no MC update function) — offering them would be
        # a silent no-op. Guard until engine support exists (Finding B).
        from systemdefiner.main import _build_scenario_params
        from systemdefiner.models.config_schema import (
            LfgParams,
            Process,
            ProcessLogic,
        )

        cfg = self._cfg_with_flowcap_and_is()
        cfg.processes.append(
            Process(
                id=3,
                name="Landfill",
                logic=ProcessLogic.lfg,
                lfg=LfgParams(outflow_ch4_id="F_03_00"),
            )
        )
        params = _build_scenario_params(cfg)
        assert not [p for p in params if p["group"] == "LFG"]

    def test_catalog_offers_initial_stock_entries(self):
        from systemdefiner.main import _build_scenario_params

        params = _build_scenario_params(self._cfg_with_flowcap_and_is())
        is_params = [p for p in params if p["group"] == "Initial Stock"]
        names = {p["name"] for p in is_params}
        assert "P02_IS_material_quantity[UoM]" in names
        # E-index follows cfg.model.elements order: material=E1, WC=E2, DM=E3, TC=E4
        assert "P02_IS_E2_[%](WC)" in names
        assert "P02_IS_E4_[%](TC)" in names
        # IS is scenario-engine-only — must be hidden on the MC page
        assert all(p.get("scenario_only") for p in is_params)


# ══════════════════════════════════════════════════════════════════════════════
# FLOWS
# ══════════════════════════════════════════════════════════════════════════════

class TestFlows:
    def _study(self, client, name="flow_test"):
        client.post("/new", data={"name": name, "start_year": 2025, "end_year": 2125, "elements": "material"})
        client.post(f"/{name}/processes/new", data={"name": "P1", "logic": "Input", "stock": "No_Stock"})
        client.post(f"/{name}/processes/new", data={"name": "P2", "logic": "Output", "stock": "No_Stock"})
        return name

    def test_flows_list_loads(self, client):
        n = self._study(client)
        assert client.get(f"/{n}/flows").status_code == 200

    def test_create_flow(self, client):
        n = self._study(client)
        r = client.post(f"/{n}/flows/new",
                        data={"id": "F_01_02", "name": "My flow", "from_process": 0, "to_process": 1},
                        follow_redirects=True)
        assert r.status_code == 200
        assert b"My flow" in r.content

    def test_edit_flow(self, client):
        n = self._study(client)
        client.post(f"/{n}/flows/new", data={"id": "F_01_02", "name": "Old", "from_process": 0, "to_process": 1})
        r = client.get(f"/{n}/flows/F_01_02/edit")
        assert r.status_code == 200

    def test_delete_flow(self, client):
        n = self._study(client)
        client.post(f"/{n}/flows/new", data={"id": "F_01_02", "name": "Gone", "from_process": 0, "to_process": 1})
        client.post(f"/{n}/flows/F_01_02/delete")
        r = client.get(f"/{n}/flows")
        assert b"Gone" not in r.content

    def test_edit_nonexistent_flow_returns_404(self, client):
        n = self._study(client)
        r = client.get(f"/{n}/flows/F_99_99/edit")
        assert r.status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# TRANSFER COEFFICIENTS
# ══════════════════════════════════════════════════════════════════════════════

class TestTransferCoefficients:
    def _study_with_flow(self, client, name="tc_test"):
        client.post("/new", data={"name": name, "start_year": 2025, "end_year": 2125, "elements": "material, WC"})
        client.post(f"/{name}/processes/new", data={"name": "P1", "logic": "Splitter", "stock": "No_Stock"})
        client.post(f"/{name}/processes/new", data={"name": "P2", "logic": "Output", "stock": "No_Stock"})
        client.post(f"/{name}/flows/new", data={"id": "F_01_02", "name": "f", "from_process": 0, "to_process": 1})
        return name

    def test_tc_overview_loads(self, client):
        n = self._study_with_flow(client)
        assert client.get(f"/{n}/tcs").status_code == 200

    def test_tc_edit_form_loads(self, client):
        n = self._study_with_flow(client)
        assert client.get(f"/{n}/tcs/0").status_code == 200

    def test_tc_save_valid(self, client):
        n = self._study_with_flow(client)
        r = client.post(f"/{n}/tcs/0",
                        data={"tc_F_01_02_material": "1.0", "tc_F_01_02_WC": "1.0"},
                        follow_redirects=True)
        assert r.status_code == 200

    def test_tc_nonexistent_process_404(self, client):
        n = self._study_with_flow(client)
        assert client.get(f"/{n}/tcs/999").status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# EXPORT
# ══════════════════════════════════════════════════════════════════════════════

class TestExport:
    def test_export_returns_yaml_file(self, client):
        client.post("/new", data={"name": "export_test", "start_year": 2020, "end_year": 2100, "elements": "material"})
        r = client.get("/export_test/export")
        assert r.status_code == 200
        assert "yaml" in r.headers.get("content-type", "")
        assert b"export_test" in r.content

    def test_export_nonexistent_raises(self, client):
        r = client.get("/nonexistent/export")
        assert r.status_code in (404, 500)


# ══════════════════════════════════════════════════════════════════════════════
# IMPORT
# ══════════════════════════════════════════════════════════════════════════════

class TestCreateFromExcel:
    def test_create_from_excel_redirects(self, client, minimal_excel):
        r = client.post("/create-from-excel",
                        data={"name": "FromExcel"},
                        files={"file": ("test.xlsx", minimal_excel, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                        follow_redirects=False)
        assert r.status_code == 303
        assert "FromExcel" in r.headers["location"]

    def test_create_from_excel_populates_settings(self, client):
        xlsx = make_excel_bytes(start_year=2010, end_year=2050, elements=["material", "WC", "DM"])
        client.post("/create-from-excel",
                    data={"name": "CS1"},
                    files={"file": ("test.xlsx", xlsx, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                    follow_redirects=True)
        r = client.get("/CS1")
        assert r.status_code == 200
        assert b"2010" in r.content
        assert b"2050" in r.content
        assert b"WC" in r.content

    def test_create_from_excel_populates_processes(self, client, minimal_excel):
        client.post("/create-from-excel",
                    data={"name": "CS2"},
                    files={"file": ("test.xlsx", minimal_excel, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                    follow_redirects=True)
        from systemdefiner import storage
        cfg = storage.load_case_study("CS2")
        assert len(cfg.processes) > 0

    def test_create_from_excel_duplicate_name_returns_error(self, client, minimal_excel):
        for _ in range(2):
            r = client.post("/create-from-excel",
                            data={"name": "Dup"},
                            files={"file": ("test.xlsx", minimal_excel, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                            follow_redirects=False)
        assert r.status_code == 400

    def test_create_from_excel_bad_file_returns_error_page(self, client):
        r = client.post("/create-from-excel",
                        data={"name": "BadFile"},
                        files={"file": ("bad.xlsx", b"not excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                        follow_redirects=True)
        assert r.status_code == 422
        assert b"Import failed" in r.content

    def test_create_from_excel_with_all_logic_types(self, client):
        xlsx = make_excel_bytes(processes=[
            {"id": 0, "name": "Input", "logic": "Input"},
            {"id": 1, "name": "Cap", "logic": "FlowCap"},
            {"id": 2, "name": "Sink", "logic": "Output"},
            {"id": 3, "name": "DSM node", "logic": "DSM"},
        ])
        r = client.post("/create-from-excel",
                        data={"name": "AllTypes"},
                        files={"file": ("types.xlsx", xlsx, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                        follow_redirects=False)
        assert r.status_code == 303
        # Case study page must load without error
        r2 = client.get("/AllTypes")
        assert r2.status_code == 200


class TestImport:
    def _create_study(self, client, name="import_test"):
        client.post("/new", data={"name": name, "start_year": 2025, "end_year": 2125, "elements": "material"})
        return name

    def test_import_form_loads(self, client):
        n = self._create_study(client)
        assert client.get(f"/{n}/import").status_code == 200

    def test_import_minimal_excel_redirects(self, client, minimal_excel):
        n = self._create_study(client)
        r = client.post(
            f"/{n}/import",
            files={"file": ("test.xlsx", minimal_excel, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            follow_redirects=False,
        )
        assert r.status_code == 303

    def test_import_sets_correct_years(self, client):
        n = self._create_study(client)
        xlsx = make_excel_bytes(start_year=2010, end_year=2050)
        client.post(f"/{n}/import",
                    files={"file": ("test.xlsx", xlsx, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                    follow_redirects=True)
        r = client.get(f"/{n}")
        assert b"2010" in r.content
        assert b"2050" in r.content

    def test_import_sets_correct_elements(self, client):
        n = self._create_study(client)
        xlsx = make_excel_bytes(elements=["material", "WC", "DM", "TC"])
        client.post(f"/{n}/import",
                    files={"file": ("test.xlsx", xlsx, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                    follow_redirects=True)
        r = client.get(f"/{n}")
        assert b"WC" in r.content
        assert b"DM" in r.content

    def test_import_filters_nan_processes(self, client, excel_with_nan_rows):
        n = self._create_study(client)
        client.post(f"/{n}/import",
                    files={"file": ("test.xlsx", excel_with_nan_rows, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                    follow_redirects=True)
        from systemdefiner import storage
        cfg = storage.load_case_study(n)
        for p in cfg.processes:
            assert p.name and p.name.lower() != "nan"

    def test_import_filters_placeholder_flows(self, client, excel_with_nan_rows):
        n = self._create_study(client)
        client.post(f"/{n}/import",
                    files={"file": ("test.xlsx", excel_with_nan_rows, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                    follow_redirects=True)
        from systemdefiner import storage
        cfg = storage.load_case_study(n)
        # No duplicate F_13_13 placeholder flows
        flow_ids = [f.id for f in cfg.flows]
        assert flow_ids.count("F_13_13") <= 1

    def test_import_new_format_excel(self, client, excel_new_format):
        n = self._create_study(client)
        r = client.post(f"/{n}/import",
                        files={"file": ("new.xlsx", excel_new_format, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                        follow_redirects=False)
        assert r.status_code == 303

    def test_import_old_format_excel(self, client, excel_old_format):
        n = self._create_study(client)
        r = client.post(f"/{n}/import",
                        files={"file": ("old.xlsx", excel_old_format, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                        follow_redirects=False)
        assert r.status_code == 303

    def test_import_invalid_file_returns_error_page(self, client):
        n = self._create_study(client)
        r = client.post(f"/{n}/import",
                        files={"file": ("bad.xlsx", b"not an excel file", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                        follow_redirects=True)
        # Must return error page (422), not crash (500)
        assert r.status_code == 422
        assert b"Import failed" in r.content

    def test_import_with_all_logic_types(self, client):
        """Regression: FlowCap and Output must be accepted without crashing."""
        n = self._create_study(client)
        xlsx = make_excel_bytes(processes=[
            {"id": 0, "name": "Input", "logic": "Input"},
            {"id": 1, "name": "Splitter", "logic": "Splitter"},
            {"id": 2, "name": "Cap", "logic": "FlowCap"},
            {"id": 3, "name": "Sink", "logic": "Output"},
            {"id": 4, "name": "DSM node", "logic": "DSM"},
        ])
        r = client.post(f"/{n}/import",
                        files={"file": ("all_types.xlsx", xlsx, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                        follow_redirects=False)
        assert r.status_code == 303

    def test_imported_config_loadable_after_import(self, client, minimal_excel):
        """Regression: imported YAML must be loadable without ValidationError."""
        n = self._create_study(client)
        client.post(f"/{n}/import",
                    files={"file": ("test.xlsx", minimal_excel, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                    follow_redirects=True)
        # GET on the overview page must not 500
        r = client.get(f"/{n}")
        assert r.status_code == 200
