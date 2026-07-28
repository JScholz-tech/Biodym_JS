"""Form-parsing helpers shared by the SystemDefiner routers.

Everything here converts raw HTML form fields (or raw YAML dicts from the
Excel importer) into config-schema objects. Moved verbatim from ``main.py``.
"""
from __future__ import annotations

import re
from typing import Optional

from systemdefiner.models.config_schema import (
    BomAssemblyEntry,
    BomAssemblyFlow,
    DsmCategory,
    DsmComponentItem,
    DsmParams,
    DynamicTCPoint,
    ElementHierarchyRule,
    FlowCapParams,
    FlowComposition,
    FlowDataEntry,
    FompParams,
    InitialStockEntry,
    LfgFraction,
    LfgParams,
    McParameter,
    ScenarioDefinition,
    ScenarioModification,
    TransferCoefficient,
)


def _slug(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_\-]", "_", name.strip())


def _g(form, key: str) -> Optional[str]:
    v = form.get(key)
    return v.strip() if v and v.strip() else None


def _gf(form, key: str) -> Optional[float]:
    v = _g(form, key)
    return float(v) if v is not None else None


def _gi(form, key: str) -> Optional[int]:
    v = _g(form, key)
    return int(v) if v is not None else None


def _parse_tcs_from_yaml(raw_tcs: list) -> list[TransferCoefficient]:
    """Convert flat TC list from yaml_schema into TransferCoefficient objects."""
    result = []
    for tc in raw_tcs:
        tc_type = tc.get("tc_type", "static")
        if tc_type == "dynamic":
            points = [
                DynamicTCPoint(year=p["year"], values=p.get("values", {}))
                for p in tc.get("time_series", [])
            ]
            result.append(
                TransferCoefficient(
                    process_id=tc["process_id"],
                    flow_id=tc["flow_id"],
                    tc_type="dynamic",
                    time_series=points,
                )
            )
        else:
            result.append(
                TransferCoefficient(
                    process_id=tc["process_id"],
                    flow_id=tc["flow_id"],
                    tc_type="static",
                    values=tc.get("values", {}),
                )
            )
    return result


def _parse_bom_from_yaml(raw_bom: list) -> list[BomAssemblyEntry]:
    result = []
    for entry in raw_bom:
        pid = entry.get("process_id")
        if pid is None:
            continue
        flows = [
            BomAssemblyFlow(
                flow_id=f["flow_id"],
                output_flow_type=f.get("output_flow_type", ""),
                fractions=f.get("fractions", {}),
            )
            for f in entry.get("flows", [])
            if f.get("flow_id")
        ]
        result.append(BomAssemblyEntry(process_id=int(pid), flows=flows))
    return result


def _apply_extra_yaml(yaml_data: dict, cfg) -> None:
    """Populate extra fields (compositions, hierarchy, flow_data, scenarios, MC) from yaml_data."""
    if yaml_data.get("element_hierarchy"):
        cfg.element_hierarchy = [
            ElementHierarchyRule(
                parent=str(r["parent"]),
                children=[str(c) for c in r.get("children", [])],
            )
            for r in yaml_data["element_hierarchy"]
        ]

    if yaml_data.get("flow_data"):
        cfg.flow_data = [
            FlowDataEntry(
                flow_id=str(fd["flow_id"]),
                element=str(fd.get("element", "material")),
                values={int(k): float(v) for k, v in fd.get("values", {}).items()},
            )
            for fd in yaml_data["flow_data"]
        ]

    if yaml_data.get("flow_compositions"):
        cfg.flow_compositions = [
            FlowComposition(
                flow_id=str(fc["flow_id"]),
                values={k: float(v) for k, v in fc.get("values", {}).items()},
            )
            for fc in yaml_data["flow_compositions"]
        ]

    if yaml_data.get("scenarios"):
        cfg.scenarios = []
        for s in yaml_data["scenarios"]:
            mods = [
                ScenarioModification(
                    parameter_name=m.get("parameter_name", ""),
                    parameter_type=m.get("parameter_type", ""),
                    operation=m.get("operation", "replace"),
                    new_value=float(m.get("new_value") or 0.0),
                    start_year=m.get("start_year"),
                    end_year=m.get("end_year"),
                )
                for m in s.get("modifications", [])
            ]
            cfg.scenarios.append(
                ScenarioDefinition(name=str(s["name"]), modifications=mods)
            )

    if yaml_data.get("mc_parameters"):
        cfg.mc_parameters = [
            McParameter(
                parameter_id=p.get("parameter_id", ""),
                enabled=bool(p.get("enabled", True)),
                distribution=p.get("distribution", "normal"),
                mean=p.get("mean"),
                std=p.get("std"),
                min=p.get("min"),
                max=p.get("max"),
                mode=p.get("mode"),
                operation=p.get("operation", "set"),
                start_year=p.get("start_year"),
                end_year=p.get("end_year"),
                flow_group=p.get("flow_group"),
            )
            for p in yaml_data["mc_parameters"]
        ]

    if yaml_data.get("initial_stocks"):
        cfg.initial_stocks = [
            InitialStockEntry(
                process_id=int(s["process_id"]),
                material_quantity=float(s.get("material_quantity", 0.0) or 0.0),
                composition={k: float(v) for k, v in s.get("composition", {}).items()},
                cohort_age_distribution_type=s.get(
                    "cohort_age_distribution_type", "Normal"
                ),
                cohort_mean_age=s.get("cohort_mean_age"),
                cohort_std_age=s.get("cohort_std_age"),
                cohort_max_age=s.get("cohort_max_age"),
                cohort_decay_constant=s.get("cohort_decay_constant"),
            )
            for s in yaml_data["initial_stocks"]
        ]


def _parse_fomp(form) -> FompParams:
    def _flt(key, default):
        v = (form.get(key) or "").strip()
        try:
            return float(v) if v else default
        except ValueError:
            return default

    return FompParams(
        f_labile=_flt("fomp_f_labile", 0.5),
        k_labile=_flt("fomp_k_labile", 1.0),
        k_recalcitrant=_flt("fomp_k_recalcitrant", 0.01),
        outflow_id=form.get("fomp_outflow_id", "") or "",
        outflow_id_2=form.get("fomp_outflow_id_2", "") or "",
        refs=[c.strip() for c in form.getlist("fomp_refs") if c.strip()],
    )


def _parse_dsm(form) -> DsmParams:
    categories: list[DsmCategory] = []
    # Collect row indices tolerantly (a removal can leave gaps in the
    # numbering); scanning until the first missing index would drop every
    # category past the gap.
    cat_indices = sorted(
        {
            int(m.group(1))
            for key in form.keys()
            if (m := re.fullmatch(r"dsm_cat_(\d+)_lifetime_type", key))
        }
    )
    for i in cat_indices:

        def _flt(key, default=None):
            v = form.get(key, "").strip()
            try:
                return float(v) if v else default
            except ValueError:
                return default

        categories.append(
            DsmCategory(
                name=(form.get(f"dsm_cat_{i}_name") or f"Cat_{i + 1}").strip(),
                # UI shows split as a percent (0–100); stored as a 0–1 fraction.
                inflow_split=(_flt(f"dsm_cat_{i}_inflow_split", 100.0) or 0.0) / 100.0,
                lifetime_type=form.get(f"dsm_cat_{i}_lifetime_type", "Normal"),
                lifetime_mean=_flt(f"dsm_cat_{i}_lifetime_mean"),
                lifetime_std=_flt(f"dsm_cat_{i}_lifetime_std"),
                lifetime_shape=_flt(f"dsm_cat_{i}_lifetime_shape"),
                lifetime_scale=_flt(f"dsm_cat_{i}_lifetime_scale"),
            )
        )
    if not categories:
        categories = [DsmCategory()]
    return DsmParams(
        categories=categories,
        refs=[c.strip() for c in form.getlist("dsm_refs") if c.strip()],
    )


def _parse_dsm_component(form) -> DsmParams:
    """Parse DSM_Component form: device categories (dsmc_cat_*) + component rows (dsm_comp_*).

    Uses a separate dsmc_cat_* prefix to avoid colliding with the standard DSM block's
    dsm_cat_* fields — both blocks coexist in the DOM, only one is visible at a time.
    """
    def _s(key): return (form.get(key) or "").strip()
    def _f(key, default=None):
        v = _s(key)
        try:
            return float(v) if v else default
        except ValueError:
            return default

    # Row indices are collected tolerantly (client-side removals can leave
    # gaps); the per-category lifetime override keys reuse the component's
    # actual DOM index, so keep (index, element) pairs.
    comp_indices = sorted(
        {
            int(m.group(1))
            for key in form.keys()
            if (m := re.fullmatch(r"dsm_comp_(\d+)_element", key))
        }
    )
    _comp_elems: list[tuple[int, str]] = [
        (j, _s(f"dsm_comp_{j}_element")) for j in comp_indices
    ]

    # Device lifetime categories (with optional per-component lifetime overrides)
    cats: list[DsmCategory] = []
    cat_indices = sorted(
        {
            int(m.group(1))
            for key in form.keys()
            if (m := re.fullmatch(r"dsmc_cat_(\d+)_name", key))
        }
    )
    for i in cat_indices:
        comp_lts: dict[str, float] = {}
        for j, elem in _comp_elems:
            val = _f(f"dsmc_cat_{i}_comp_lt_{j}")
            if val is not None and val > 0 and elem:
                comp_lts[elem] = val
        cats.append(DsmCategory(
            name=_s(f"dsmc_cat_{i}_name") or "Default",
            inflow_split=(_f(f"dsmc_cat_{i}_inflow_split") or 0.0) / 100.0,
            lifetime_type=_s(f"dsmc_cat_{i}_lifetime_type") or "Normal",
            lifetime_mean=_f(f"dsmc_cat_{i}_lifetime_mean"),
            lifetime_std=_f(f"dsmc_cat_{i}_lifetime_std"),
            lifetime_shape=_f(f"dsmc_cat_{i}_lifetime_shape"),
            lifetime_scale=_f(f"dsmc_cat_{i}_lifetime_scale"),
            component_lifetimes=comp_lts,
        ))
    if not cats:
        cats = [DsmCategory(name="Default", inflow_split=1.0, lifetime_type="Normal")]

    # Component renewal rows
    components: list[DsmComponentItem] = []
    for i, elem in _comp_elems:
        mean_lt = _f(f"dsm_comp_{i}_mean_lifetime")
        outflow = _s(f"dsm_comp_{i}_sparepart_outflow")
        inflow  = _s(f"dsm_comp_{i}_sparepart_inflow")
        if elem and mean_lt:
            components.append(DsmComponentItem(
                element=elem,
                mean_lifetime=mean_lt,
                sparepart_outflow=outflow,
                sparepart_inflow=inflow,
            ))

    refs = [v for v in form.getlist("dsm_refs") if v]
    return DsmParams(categories=cats, components=components, refs=refs)


def _parse_lfg(form) -> LfgParams:
    fractions: list[LfgFraction] = []
    # Collect row indices tolerantly (a removal can leave gaps in the numbering);
    # scanning until the first missing index would drop fractions past the gap.
    frac_indices = sorted(
        {
            int(m.group(1))
            for key in form.keys()
            if (m := re.fullmatch(r"lfg_frac_(\d+)_name", key))
        }
    )
    for idx in frac_indices:
        fractions.append(
            LfgFraction(
                name=form.get(f"lfg_frac_{idx}_name", "") or "",
                k_j=float(form.get(f"lfg_frac_{idx}_k_j", 0.1) or 0.1),
                doc_j=float(form.get(f"lfg_frac_{idx}_doc_j", 0.5) or 0.5),
                f_input_j=float(form.get(f"lfg_frac_{idx}_f_input_j", 1.0) or 1.0),
                f_ash_j=float(form.get(f"lfg_frac_{idx}_f_ash_j", 0.05) or 0.05),
            )
        )

    def _flt(key, default):
        v = (form.get(key) or "").strip()
        try:
            return float(v) if v else default
        except ValueError:
            return default

    return LfgParams(
        mcf=_flt("lfg_mcf", 1.0),
        doc_f=_flt("lfg_doc_f", 0.5),
        f_ch4=_flt("lfg_f_ch4", 0.5),
        ox=_flt("lfg_ox", 0.1),
        phi=_flt("lfg_phi", 1.0),
        f_capture=_flt("lfg_f_capture", 0.0),
        outflow_ch4_id=form.get("lfg_outflow_ch4_id", "") or "",
        outflow_co2_id=form.get("lfg_outflow_co2_id", "") or "",
        outflow_leachate_id=form.get("lfg_outflow_leachate_id", "") or "",
        fractions=fractions,
        refs=[c.strip() for c in form.getlist("lfg_refs") if c.strip()],
    )


def _parse_flowcap(form, process_id: int) -> Optional[FlowCapParams]:
    capped = form.get("flowcap_capped_flow_id", "") or ""
    if not capped:
        return None
    cap_series: dict[int, float] = {}
    # Collect row indices tolerantly: a client-side row removal can leave gaps
    # in the flowcap_year_{i} numbering, so never stop at the first missing
    # index — that would silently drop every capacity point past the gap.
    cap_indices = sorted(
        {
            int(m.group(1))
            for key in form.keys()
            if (m := re.fullmatch(r"flowcap_year_(\d+)", key))
        }
    )
    for idx in cap_indices:
        try:
            year = int(float(form[f"flowcap_year_{idx}"]))
            cap = float(form.get(f"flowcap_cap_{idx}", 0) or 0)
            if year:
                cap_series[year] = cap
        except (ValueError, TypeError):
            pass
    # ParameterDict key under which the engine registers the cap series, so
    # the Scenario Manager and MC can switch the cap. Auto-derive the
    # canonical name when the form leaves it blank; keep hand-authored IDs.
    cap_tc_id = (form.get("flowcap_cap_tc_id", "") or "").strip()
    if not cap_tc_id:
        cap_tc_id = f"TC_Cap_{process_id:02d}"
    return FlowCapParams(
        capped_flow_id=capped,
        overflow_flow_id=form.get("flowcap_overflow_flow_id", "") or "",
        cap_series=cap_series,
        cap_tc_id=cap_tc_id,
        refs=[c.strip() for c in form.getlist("flowcap_refs") if c.strip()],
    )
