"""Config-consistency invariants for the SystemDefiner.

Two things live here:

1. ``iter_flow_pointers(cfg)`` — the single authoritative enumeration of every
   *scalar* flow-ID pointer field in the config schema (FOMP/LFG/FlowCap
   outflows, Input_Substitution's consumed/surplus flows, and the
   DSM_Component sparepart flows). The cascade helpers in ``cascades.py``
   iterate this registry, so a new pointer field added to
   ``config_schema.py`` only needs to be registered once and every rename /
   purge / renumber picks it up. Row-level references (TCs, compositions,
   flow data, BOM flows, scenario/MC names) are handled by the cascades
   directly because their purge semantics is *remove the row*, not *blank the
   field*. ``Input_Substitution.supply_flow_ids`` is a *list*-valued pointer
   (like ``bom_assembly.flows``), so it is handled by explicit loops in
   ``cascades.py`` instead of this scalar-only registry.

2. ``check_config_consistency(cfg)`` — a pure function returning
   ``[{level, message}]`` issues for every invariant a mutation could break
   without producing invalid YAML: dangling or retargeted scenario/MC
   parameter names, stale element keys, TC ownership mismatches, duplicate
   IDs, flow-ID/endpoint drift, orphaned flow data, and hierarchy defects.
   ``health._model_health`` merges these into the overview page, and the test
   suite asserts a clean report after every mutation route.
"""
from __future__ import annotations

import re
from typing import Iterator

from systemdefiner.models.config_schema import ProcessLogic, TCConfig

# Flow-ID convention: F_<from>_<to> with an optional _N duplicate-edge suffix.
FLOW_ID_CONVENTION = re.compile(r"F_(\d+)_(\d+)(?:_(\d+))?")


def iter_flow_pointers(cfg) -> Iterator[tuple[str, object, str, object]]:
    """Yield ``(label, owner_object, attribute_name, blank_value)`` for every
    scalar flow-ID pointer in the config.

    ``blank_value`` is what a purge writes when the referenced flow vanishes
    (matches the schema defaults: ``""`` except FOMP's optional second outflow,
    which is ``None``).
    """
    for p in cfg.processes:
        if p.fomp:
            yield (f"P{p.id} {p.name}: FOMP outflow", p.fomp, "outflow_id", "")
            yield (
                f"P{p.id} {p.name}: FOMP secondary outflow",
                p.fomp,
                "outflow_id_2",
                None,
            )
        if p.lfg:
            yield (f"P{p.id} {p.name}: LFG CH4 outflow", p.lfg, "outflow_ch4_id", "")
            yield (f"P{p.id} {p.name}: LFG CO2 outflow", p.lfg, "outflow_co2_id", "")
            yield (
                f"P{p.id} {p.name}: LFG leachate outflow",
                p.lfg,
                "outflow_leachate_id",
                "",
            )
        if p.flowcap:
            yield (
                f"P{p.id} {p.name}: FlowCap capped flow",
                p.flowcap,
                "capped_flow_id",
                "",
            )
            yield (
                f"P{p.id} {p.name}: FlowCap overflow flow",
                p.flowcap,
                "overflow_flow_id",
                "",
            )
        if p.input_substitution:
            yield (
                f"P{p.id} {p.name}: Input_Substitution Substitution flow",
                p.input_substitution,
                "consumed_flow_id",
                "",
            )
            yield (
                f"P{p.id} {p.name}: Input_Substitution Overflow",
                p.input_substitution,
                "surplus_flow_id",
                "",
            )
            yield (
                f"P{p.id} {p.name}: Input_Substitution System input",
                p.input_substitution,
                "residual_flow_id",
                "",
            )
        if p.dsm:
            for comp in p.dsm.components:
                yield (
                    f"P{p.id} {p.name}: DSM component '{comp.element}' spare-part outflow",
                    comp,
                    "sparepart_outflow",
                    "",
                )
                yield (
                    f"P{p.id} {p.name}: DSM component '{comp.element}' spare-part inflow",
                    comp,
                    "sparepart_inflow",
                    "",
                )


def input_substitution_residual_flow(cfg, process):
    """The Input_Substitution process's "virgin material still needed" outflow.

    Named via ``residual_flow_id`` when set. Falls back to discovery — the
    sole flow with ``from_process == process.id`` that isn't
    ``consumed_flow_id``/``surplus_flow_id`` — for configs saved before that
    field existed. This is the flow whose ``flow_data`` entry supplies the
    demand target — same mechanism as a plain Input process. Returns
    ``None`` when there isn't exactly one candidate (dangling config;
    ``health.py`` reports it) or when the process has no
    ``consumed_flow_id`` configured yet.
    """
    is_ = getattr(process, "input_substitution", None)
    if not is_ or not is_.consumed_flow_id:
        return None
    if is_.residual_flow_id:
        return next((f for f in cfg.flows if f.id == is_.residual_flow_id), None)
    claimed = {is_.consumed_flow_id, is_.surplus_flow_id}
    candidates = [
        f for f in cfg.flows if f.from_process == process.id and f.id not in claimed
    ]
    return candidates[0] if len(candidates) == 1 else None


def _element_key_sites(cfg) -> Iterator[tuple[str, dict]]:
    """Yield ``(label, element_keyed_dict)`` for every dict whose keys must be
    element names from ``cfg.model.elements``."""
    for tc in cfg.transfer_coefficients:
        if tc.values:
            yield (f"TC (P{tc.process_id}, {tc.flow_id})", tc.values)
        for pt in tc.time_series:
            if pt.values:
                yield (f"Dynamic TC (P{tc.process_id}, {tc.flow_id}, {pt.year})", pt.values)
    for fc in cfg.flow_compositions:
        if fc.values:
            yield (f"Flow composition {fc.flow_id}", fc.values)
    for entry in cfg.bom_assembly:
        for bf in entry.flows:
            if bf.fractions:
                yield (f"BOM P{entry.process_id} flow {bf.flow_id}", bf.fractions)
    for s in cfg.initial_stocks:
        if s.composition:
            yield (f"Initial stock P{s.process_id}", s.composition)
    for p in cfg.processes:
        if p.expected_inflow_composition:
            yield (
                f"P{p.id} {p.name}: expected inflow composition",
                p.expected_inflow_composition,
            )
        if p.dsm:
            for cat in p.dsm.categories:
                if cat.component_lifetimes:
                    yield (
                        f"P{p.id} {p.name}: DSM category '{cat.name}' component lifetimes",
                        cat.component_lifetimes,
                    )


def check_config_consistency(cfg) -> list[dict]:
    """Return ``[{level, message}]`` issues for cross-reference invariants.

    Complements (does not repeat) the checks in ``health._model_health`` —
    the two are merged on the overview page.
    """
    issues: list[dict] = []

    def err(msg):
        issues.append({"level": "error", "message": msg})

    def warn(msg):
        issues.append({"level": "warn", "message": msg})

    flow_by_id = {f.id: f for f in cfg.flows}
    flow_ids = set(flow_by_id)
    elements = list(cfg.model.elements)
    element_set = set(elements)

    # ── Duplicate IDs (reachable via Excel/YAML import) ──────────────────────
    seen: set = set()
    for p in cfg.processes:
        if p.id in seen:
            err(f"Duplicate process ID P{p.id} — downstream data will collide.")
        seen.add(p.id)
    seen = set()
    for f in cfg.flows:
        if f.id in seen:
            err(f"Duplicate flow ID '{f.id}' — downstream data will collide.")
        seen.add(f.id)
    seen = set()
    for e in elements:
        if e in seen:
            err(f"Duplicate element name '{e}'.")
        seen.add(e)

    # ── Flow-ID / endpoint drift + duplicate edges ───────────────────────────
    for f in cfg.flows:
        m = FLOW_ID_CONVENTION.fullmatch(str(f.id))
        if m and (int(m.group(1)) != f.from_process or int(m.group(2)) != f.to_process):
            warn(
                f"Flow '{f.id}' is wired P{f.from_process}→P{f.to_process} but its "
                f"ID names P{int(m.group(1))}→P{int(m.group(2))} — the label disguises "
                f"the real topology (rename the flow or fix the endpoints)."
            )
    pair_counts: dict[tuple, list] = {}
    for f in cfg.flows:
        pair_counts.setdefault((f.from_process, f.to_process), []).append(f.id)
    for (fp, tp), fids in pair_counts.items():
        if len(fids) > 1:
            warn(
                f"Multiple flows between P{fp}→P{tp}: {', '.join(fids)} — "
                f"they share the same derived TC parameter names, so only the "
                f"first TC definition takes effect."
            )

    # ── TC ownership + duplicate derived TC names ────────────────────────────
    tc_keys: set = set()
    tc_pairs: dict[tuple, list] = {}
    for tc in cfg.transfer_coefficients:
        fl = flow_by_id.get(tc.flow_id)
        if fl is None:
            err(
                f"TC for P{tc.process_id} references flow '{tc.flow_id}', which "
                f"does not exist."
            )
            continue
        if fl.from_process != tc.process_id:
            err(
                f"TC owned by P{tc.process_id} points at flow '{tc.flow_id}', "
                f"which leaves P{fl.from_process} — a stale entry from a rewired "
                f"flow; it exports under P{fl.from_process}→P{fl.to_process} TC "
                f"names and silently overrides that process's own TCs."
            )
        key = (tc.process_id, tc.flow_id)
        if key in tc_keys:
            err(f"Duplicate TC entry for (P{tc.process_id}, {tc.flow_id}).")
        tc_keys.add(key)
        if tc.values or tc.time_series:
            tc_pairs.setdefault((fl.from_process, fl.to_process), []).append(tc.flow_id)
    for (fp, tp), fids in tc_pairs.items():
        if len(fids) > 1:
            err(
                f"TCs on {len(fids)} flows sharing the pair P{fp}→P{tp} "
                f"({', '.join(fids)}) export identical TC_E*_{fp:02d}_{tp:02d} "
                f"parameter names — the engine keeps only the first value."
            )

    # ── Static TC sums (config-wide; the editor only validates its own save) ─
    _splitterish = {ProcessLogic.splitter, ProcessLogic.dsm, ProcessLogic.dsm_component}
    for p in cfg.processes:
        if p.tc_config != TCConfig.static:
            continue
        if p.logic not in _splitterish and p.logic != ProcessLogic.transformer:
            continue
        proc_tcs = [
            tc
            for tc in cfg.transfer_coefficients
            if tc.process_id == p.id and tc.values
        ]
        if not proc_tcs:
            continue  # "no TCs defined" is _model_health's warning
        validate_elements = elements[:1] if p.logic in _splitterish else elements[1:]
        for elem in validate_elements:
            total = sum(tc.values.get(elem, 0.0) for tc in proc_tcs)
            if abs(total - 1.0) > 1e-6:
                warn(
                    f"P{p.id} {p.name}: static TCs for '{elem}' sum to {total:.4f} "
                    f"(must be 1.0) — the model will not conserve mass."
                )

    # ── Element keys must exist in the element list ──────────────────────────
    for label, d in _element_key_sites(cfg):
        stale = [k for k in d if k not in element_set]
        if stale:
            err(
                f"{label}: values stored for unknown element(s) "
                f"{', '.join(sorted(stale))} — they are silently ignored by the "
                f"engine (element renamed/removed without updating the data?)."
            )
    for fd in cfg.flow_data:
        if fd.element and fd.element not in element_set:
            err(
                f"Flow data {fd.flow_id}: element '{fd.element}' is not in the "
                f"element list."
            )
    for p in cfg.processes:
        if p.dsm:
            for comp in p.dsm.components:
                if comp.element and comp.element not in element_set:
                    err(
                        f"P{p.id} {p.name}: DSM component element '{comp.element}' "
                        f"is not in the element list."
                    )

    # ── DSM component spare-part flow pointers ───────────────────────────────
    for label, obj, attr, _blank in iter_flow_pointers(cfg):
        if "spare-part" not in label:
            continue  # FOMP/LFG/FlowCap/Input_Substitution pointers are checked in _model_health
        fid = getattr(obj, attr)
        if fid and fid not in flow_ids:
            warn(f"{label} '{fid}' is not a defined flow.")

    # ── flow data / compositions stranded on non-input flows ────────────────
    input_pids = {p.id for p in cfg.processes if p.logic == ProcessLogic.input} | {0}
    for fd in cfg.flow_data:
        fl = flow_by_id.get(fd.flow_id)
        if fl is None:
            err(f"Flow data references flow '{fd.flow_id}', which does not exist.")
        elif fl.from_process not in input_pids:
            warn(
                f"Flow data on '{fd.flow_id}' whose source P{fl.from_process} is "
                f"not an Input process — the values are invisible in the editor "
                f"but still prescribe the flow in the engine."
            )
    for fc in cfg.flow_compositions:
        fl = flow_by_id.get(fc.flow_id)
        if fl is None:
            err(
                f"Flow composition references flow '{fc.flow_id}', which does "
                f"not exist."
            )
        elif fl.from_process not in input_pids:
            warn(
                f"Composition on '{fc.flow_id}' whose source P{fl.from_process} is "
                f"not an Input process — it is invisible in the editor but still "
                f"exported to the engine."
            )

    # ── Scenario / MC parameter names must resolve ───────────────────────────
    from systemdefiner.scenario_params import _build_scenario_params

    known_params = {p["name"] for p in _build_scenario_params(cfg)}
    for sc in cfg.scenarios:
        for i, mod in enumerate(sc.modifications, 1):
            nm = (mod.parameter_name or "").strip()
            if nm and nm not in known_params:
                err(
                    f"Scenario '{sc.name}' modification {i}: parameter '{nm}' does "
                    f"not match any flow/TC/DSM/FOMP/FlowCap/IS parameter of the "
                    f"current model — it is silently ignored (renumbered or "
                    f"deleted process/flow?)."
                )
    for mp in cfg.mc_parameters:
        nm = (mp.parameter_id or "").strip()
        if nm and nm not in known_params:
            err(
                f"MC parameter '{nm}' does not match any flow/TC/DSM/FOMP/FlowCap "
                f"parameter of the current model — it is silently ignored "
                f"(renumbered or deleted process/flow?)."
            )

    # ── Element hierarchy sanity ─────────────────────────────────────────────
    child_parents: dict[str, list] = {}
    hier_members: set = set()
    for rule in cfg.element_hierarchy:
        hier_members.add(rule.parent)
        for child in rule.children:
            hier_members.add(child)
            child_parents.setdefault(child, []).append(rule.parent)
    for member in sorted(hier_members - element_set):
        err(
            f"Element hierarchy references '{member}', which is not in the "
            f"element list."
        )
    for child, parents in sorted(child_parents.items()):
        if len(parents) > 1:
            err(
                f"Element '{child}' has multiple parents in the hierarchy "
                f"({', '.join(sorted(parents))}) — the hierarchy must be a tree."
            )
    # Cycle detection over the child→parent chain
    parent_of = {c: ps[0] for c, ps in child_parents.items()}
    for start in parent_of:
        cur, hops = start, 0
        while cur in parent_of:
            cur = parent_of[cur]
            hops += 1
            if cur == start or hops > len(parent_of):
                err(
                    f"Element hierarchy contains a cycle involving '{start}' — "
                    f"fix the parent/child rows on the Elements page."
                )
                break

    return issues
