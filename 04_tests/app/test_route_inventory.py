# -*- coding: utf-8 -*-
"""Safety net for restructuring systemdefiner.main: route inventory + full-page
round trip.

The inventory test pins the exact ordered route table so a module split cannot
silently drop, rename, or reorder a route (Starlette matches in declaration
order). The round-trip test builds a study that touches every editor and then
GETs every page, so broken imports/template wiring surface as non-200s.
"""
from __future__ import annotations


# Ordered (method, path) pairs as declared in systemdefiner.main. Keep this in
# sync deliberately when routes are added/removed — that is the point.
EXPECTED_ROUTES = [
    ("GET", "/"),
    ("GET", "/glossary"),
    ("POST", "/create-from-excel"),
    ("POST", "/new"),
    ("POST", "/{name}/delete"),
    ("POST", "/{name}/clone"),
    ("GET", "/{name}"),
    ("POST", "/{name}/settings"),
    ("POST", "/{name}/group"),
    ("GET", "/{name}/processes"),
    ("POST", "/{name}/processes/new"),
    ("GET", "/{name}/processes/{pid}/edit"),
    ("POST", "/{name}/processes/{pid}/edit"),
    ("POST", "/{name}/processes/{pid}/delete"),
    ("POST", "/{name}/processes/renumber"),
    ("GET", "/{name}/flows"),
    ("POST", "/{name}/flows/new"),
    ("GET", "/{name}/flows/{fid}/edit"),
    ("POST", "/{name}/flows/{fid}/edit"),
    ("POST", "/{name}/flows/{fid}/delete"),
    ("GET", "/{name}/tcs"),
    ("GET", "/{name}/tcs/{pid}"),
    ("POST", "/{name}/tcs/{pid}"),
    ("GET", "/{name}/scenarios"),
    ("POST", "/{name}/scenarios/new"),
    ("GET", "/{name}/scenarios/{sname}"),
    ("POST", "/{name}/scenarios/{sname}"),
    ("POST", "/{name}/scenarios/{sname}/delete"),
    ("GET", "/api/zotero/search"),
    ("GET", "/api/zotero/status"),
    ("GET", "/{name}/references"),
    ("POST", "/{name}/references/add"),
    ("POST", "/{name}/references/note"),
    ("POST", "/{name}/references/delete"),
    ("GET", "/{name}/export"),
    ("GET", "/{name}/diagram"),
    ("POST", "/{name}/diagram"),
    ("POST", "/{name}/diagram/delete"),
    ("GET", "/{name}/import"),
    ("POST", "/{name}/import"),
    ("GET", "/{name}/elements"),
    ("POST", "/{name}/elements"),
    ("GET", "/{name}/hierarchy"),
    ("GET", "/{name}/mc_parameters"),
    ("POST", "/{name}/mc_parameters"),
    ("GET", "/{name}/compositions"),
    ("POST", "/{name}/compositions"),
    ("GET", "/{name}/bom/{pid}"),
    ("POST", "/{name}/bom/{pid}"),
    ("GET", "/{name}/initial_stock/{pid}"),
    ("POST", "/{name}/initial_stock/{pid}"),
    ("GET", "/{name}/flow_data"),
    ("POST", "/{name}/flow_data"),
]


def test_route_inventory_is_stable():
    from fastapi.routing import APIRoute

    from systemdefiner.main import app

    actual = [
        (m, r.path)
        for r in app.routes
        if isinstance(r, APIRoute)
        for m in sorted(r.methods - {"HEAD"})
    ]
    assert actual == EXPECTED_ROUTES


def test_main_reexports_survive_restructuring():
    """Symbols other modules/tests import from systemdefiner.main."""
    from systemdefiner import main

    for symbol in (
        "app",
        "_build_scenario_params",
        "_model_health",
        "_rename_flow_id",
        "_purge_flow_references",
        "_delete_process_cascade",
        "_compact_process_ids",
        "_next_flow_id",
        "_rules_to_paths",
    ):
        assert hasattr(main, symbol), f"systemdefiner.main.{symbol} missing"


class TestFullPageRoundTrip:
    """Build one study through the forms, then GET every page."""

    def _build_study(self, client, name="roundtrip"):
        client.post(
            "/new",
            data={
                "name": name,
                "start_year": 2025,
                "end_year": 2035,
                "elements": "material, WC, DM, TC",
            },
        )
        # P0 Input, P1 Splitter, P2 FOMP, P3 DSM, P4 Output
        for pname, logic, stock in [
            ("Source", "Input", "No_Stock"),
            ("Sorter", "Splitter", "No_Stock"),
            ("Soil", "FOMP", "Stock"),
            ("Stockpile", "DSM", "Stock_with_InitialStock_Decay"),
            ("Sink", "Output", "No_Stock"),
        ]:
            client.post(
                f"/{name}/processes/new",
                data={"name": pname, "logic": logic, "stock": stock},
            )
        for from_p, to_p in [(0, 1), (1, 2), (1, 3), (2, 4), (3, 4)]:
            client.post(
                f"/{name}/flows/new",
                data={"name": "", "from_process": from_p, "to_process": to_p},
            )
        # Static TCs on the splitter (P1) — two outgoing flows, 50/50
        client.post(
            f"/{name}/tcs/1",
            data={"tc_F_01_02_material": "0.5", "tc_F_01_03_material": "0.5"},
        )
        # Composition + flow data on the input flow
        client.post(
            f"/{name}/compositions",
            data={
                "comp_F_00_01_material": "1.0",
                "comp_F_00_01_WC": "0.2",
                "comp_F_00_01_DM": "0.8",
                "comp_F_00_01_TC": "0.4",
            },
        )
        client.post(
            f"/{name}/flow_data",
            data={"fd_0_id": "F_00_01", "fd_0_y_0": "2025", "fd_0_v_0": "100"},
        )
        # Initial stock on the DSM process (P3)
        client.post(
            f"/{name}/initial_stock/3",
            data={"is_material_quantity": "500", "is_DM": "0.9"},
        )
        # Scenario + modification, MC parameter, reference
        client.post(f"/{name}/scenarios/new", data={"scenario_name": "S1"})
        client.post(
            f"/{name}/scenarios/S1",
            data={
                "mod_0_parameter_name": "F_00_01",
                "mod_0_parameter_type": "Flow",
                "mod_0_operation": "multiply",
                "mod_0_new_value": "1.1",
            },
        )
        client.post(
            f"/{name}/mc_parameters",
            data={
                "mc_0_parameter_id": "TC_E1_01_02",
                "mc_0_enabled": "on",
                "mc_0_distribution": "normal",
                "mc_0_mean": "0.5",
                "mc_0_std": "0.05",
                "mc_0_operation": "set",
            },
        )
        client.post(
            f"/{name}/references/add",
            data={"cite_key": "test2026", "title": "A test source"},
        )
        return name

    def test_every_page_renders(self, client):
        n = self._build_study(client)
        pages = [
            "/",
            "/glossary",
            f"/{n}",
            f"/{n}/processes",
            f"/{n}/processes/1/edit",
            f"/{n}/flows",
            f"/{n}/flows/F_01_02/edit",
            f"/{n}/tcs",
            f"/{n}/tcs/1",
            f"/{n}/scenarios",
            f"/{n}/scenarios/S1",
            f"/{n}/references",
            f"/{n}/import",
            f"/{n}/elements",
            f"/{n}/mc_parameters",
            f"/{n}/compositions",
            f"/{n}/bom/1",
            f"/{n}/initial_stock/3",
            f"/{n}/flow_data",
            f"/{n}/export",
        ]
        for page in pages:
            r = client.get(page)
            assert r.status_code == 200, f"GET {page} -> {r.status_code}"

    def test_saved_config_round_trips(self, client):
        from systemdefiner import storage

        n = self._build_study(client)
        cfg = storage.load_case_study(n)
        assert len(cfg.processes) == 5
        assert len(cfg.flows) == 5
        assert {tc.flow_id for tc in cfg.transfer_coefficients} == {
            "F_01_02",
            "F_01_03",
        }
        assert cfg.flow_compositions[0].flow_id == "F_00_01"
        assert cfg.flow_data[0].values == {2025: 100.0}
        assert cfg.initial_stocks[0].process_id == 3
        assert cfg.scenarios[0].modifications[0].parameter_name == "F_00_01"
        assert cfg.mc_parameters[0].parameter_id == "TC_E1_01_02"
        assert cfg.references[0].cite_key == "test2026"
        # Re-save and re-load: stable
        storage.save_case_study(cfg)
        cfg2 = storage.load_case_study(n)
        assert cfg2 == cfg
