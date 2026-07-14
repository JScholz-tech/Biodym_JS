"""Config-wide cascade helpers: flow-ID renames, purges, process deletion and
renumbering. Every mutation that changes an ID or removes an entity must go
through these so no reference-bearing field is left stale.

Moved verbatim from ``main.py``.
"""
from __future__ import annotations

import re


def _process_name(cfg, pid: int) -> str:
    """Return a process's name (falls back to ``P{id}`` if unnamed/unknown)."""
    p = next((p for p in cfg.processes if p.id == pid), None)
    return p.name if p and p.name else f"P{pid}"


def _next_flow_id(cfg, from_p: int, to_p: int) -> str:
    """Auto-generate a flow ID as ``F_{from}_{to}`` (Excel convention, e.g. F_12_16).

    Process IDs are zero-padded to at least two digits. If a flow with that ID
    already exists (e.g. a second flow between the same two processes), a numeric
    suffix is appended: ``F_12_16``, ``F_12_16_2``, ``F_12_16_3``, …
    """
    base = f"F_{from_p:02d}_{to_p:02d}"
    existing = {str(f.id) for f in cfg.flows}
    if base not in existing:
        return base
    i = 2
    while f"{base}_{i}" in existing:
        i += 1
    return f"{base}_{i}"


def _rename_flow_id(cfg, old_id: str, new_id: str) -> None:
    """Propagate a flow-ID rename to every place that references a flow ID.

    Keeps transfer coefficients, flow data, compositions, BOM flows, and the
    process outflow pointers (FOMP / LFG / FlowCap) consistent, plus any
    scenario / MC parameters keyed exactly by the old flow ID.
    """
    for tc in cfg.transfer_coefficients:
        if tc.flow_id == old_id:
            tc.flow_id = new_id
    for fc in cfg.flow_compositions:
        if fc.flow_id == old_id:
            fc.flow_id = new_id
    for fd in cfg.flow_data:
        if fd.flow_id == old_id:
            fd.flow_id = new_id
    for entry in cfg.bom_assembly:
        for bf in entry.flows:
            if bf.flow_id == old_id:
                bf.flow_id = new_id
    for p in cfg.processes:
        if p.fomp:
            if p.fomp.outflow_id == old_id:
                p.fomp.outflow_id = new_id
            if p.fomp.outflow_id_2 == old_id:
                p.fomp.outflow_id_2 = new_id
        if p.lfg:
            if p.lfg.outflow_ch4_id == old_id:
                p.lfg.outflow_ch4_id = new_id
            if p.lfg.outflow_co2_id == old_id:
                p.lfg.outflow_co2_id = new_id
            if p.lfg.outflow_leachate_id == old_id:
                p.lfg.outflow_leachate_id = new_id
        if p.flowcap:
            if p.flowcap.capped_flow_id == old_id:
                p.flowcap.capped_flow_id = new_id
            if p.flowcap.overflow_flow_id == old_id:
                p.flowcap.overflow_flow_id = new_id
    for sc in cfg.scenarios:
        for mod in sc.modifications:
            if mod.parameter_name == old_id:
                mod.parameter_name = new_id
    for mc in cfg.mc_parameters:
        if mc.parameter_id == old_id:
            mc.parameter_id = new_id


def _purge_flow_references(cfg, flow_ids: set) -> None:
    """Remove every reference to the given flow IDs across the config.

    Used when flows disappear (e.g. their process is deleted) so nothing is
    left pointing at a flow that no longer exists.
    """
    if not flow_ids:
        return
    cfg.transfer_coefficients = [
        tc for tc in cfg.transfer_coefficients if tc.flow_id not in flow_ids
    ]
    cfg.flow_compositions = [
        fc for fc in cfg.flow_compositions if fc.flow_id not in flow_ids
    ]
    cfg.flow_data = [fd for fd in cfg.flow_data if fd.flow_id not in flow_ids]
    for entry in cfg.bom_assembly:
        entry.flows = [bf for bf in entry.flows if bf.flow_id not in flow_ids]
    for p in cfg.processes:
        if p.fomp:
            if p.fomp.outflow_id in flow_ids:
                p.fomp.outflow_id = ""
            if p.fomp.outflow_id_2 in flow_ids:
                p.fomp.outflow_id_2 = None
        if p.lfg:
            if p.lfg.outflow_ch4_id in flow_ids:
                p.lfg.outflow_ch4_id = ""
            if p.lfg.outflow_co2_id in flow_ids:
                p.lfg.outflow_co2_id = ""
            if p.lfg.outflow_leachate_id in flow_ids:
                p.lfg.outflow_leachate_id = ""
        if p.flowcap:
            if p.flowcap.capped_flow_id in flow_ids:
                p.flowcap.capped_flow_id = ""
            if p.flowcap.overflow_flow_id in flow_ids:
                p.flowcap.overflow_flow_id = ""
    for sc in cfg.scenarios:
        sc.modifications = [
            m for m in sc.modifications if m.parameter_name not in flow_ids
        ]
    cfg.mc_parameters = [
        mc for mc in cfg.mc_parameters if mc.parameter_id not in flow_ids
    ]


def _delete_process_cascade(cfg, pid: int) -> None:
    """Delete a process and everything that depends on it.

    Removes the process, every flow touching it (in or out), its transfer
    coefficients and BOM entry, and then purges all remaining references to the
    now-removed flows (TCs, flow data, compositions, BOM flows, FOMP/LFG/FlowCap
    outflow pointers, scenario/MC parameters).
    """
    orphan_flow_ids = {
        f.id for f in cfg.flows if f.from_process == pid or f.to_process == pid
    }
    cfg.processes = [p for p in cfg.processes if p.id != pid]
    cfg.flows = [f for f in cfg.flows if f.from_process != pid and f.to_process != pid]
    cfg.transfer_coefficients = [
        tc for tc in cfg.transfer_coefficients if tc.process_id != pid
    ]
    cfg.bom_assembly = [e for e in cfg.bom_assembly if e.process_id != pid]
    cfg.initial_stocks = [s for s in cfg.initial_stocks if s.process_id != pid]
    _purge_flow_references(cfg, orphan_flow_ids)


def _compact_process_ids(cfg) -> dict:
    """Renumber process IDs to a contiguous 0..N-1 range (gaps left by deletions
    break the engine, which expects 0-based contiguous IDs).

    Cascades the renumber through every reference: flow endpoints, the
    ``F_<from>_<to>`` flow IDs and all string references to them (TCs, flow
    compositions, flow data, BOM flows, FOMP/LFG/FlowCap outflow IDs), plus the
    ``process_id`` on TCs, BOM entries and initial stocks. Returns the old→new
    id map (empty when already contiguous).
    """
    old_ids = sorted(p.id for p in cfg.processes)
    id_map = {old: new for new, old in enumerate(old_ids)}
    if all(o == n for o, n in id_map.items()):
        return {}

    for p in cfg.processes:
        p.id = id_map[p.id]
    for f in cfg.flows:
        f.from_process = id_map.get(f.from_process, f.from_process)
        f.to_process = id_map.get(f.to_process, f.to_process)

    # Rename F_<from>_<to> flow IDs to match new endpoints (collision-safe).
    existing = {f.id for f in cfg.flows}
    flow_rename: dict[str, str] = {}
    for f in cfg.flows:
        if not re.fullmatch(r"F_\d+_\d+", f.id):
            continue
        cand = f"F_{f.from_process:02d}_{f.to_process:02d}"
        if cand == f.id or cand in existing:
            continue
        existing.discard(f.id)
        existing.add(cand)
        flow_rename[f.id] = cand
        f.id = cand

    def _rn(fid):
        return flow_rename.get(fid, fid) if fid else fid

    for tc in cfg.transfer_coefficients:
        tc.process_id = id_map.get(tc.process_id, tc.process_id)
        tc.flow_id = _rn(tc.flow_id)
    for fc in cfg.flow_compositions:
        fc.flow_id = _rn(fc.flow_id)
    for fd in cfg.flow_data:
        fd.flow_id = _rn(fd.flow_id)
    for e in cfg.bom_assembly:
        e.process_id = id_map.get(e.process_id, e.process_id)
        for bf in e.flows:
            bf.flow_id = _rn(bf.flow_id)
    for s in cfg.initial_stocks:
        s.process_id = id_map.get(s.process_id, s.process_id)
    for p in cfg.processes:
        if p.fomp:
            p.fomp.outflow_id = _rn(p.fomp.outflow_id)
            p.fomp.outflow_id_2 = _rn(p.fomp.outflow_id_2)
        if p.lfg:
            p.lfg.outflow_ch4_id = _rn(p.lfg.outflow_ch4_id)
            p.lfg.outflow_co2_id = _rn(p.lfg.outflow_co2_id)
            p.lfg.outflow_leachate_id = _rn(p.lfg.outflow_leachate_id)
        if p.flowcap:
            p.flowcap.capped_flow_id = _rn(p.flowcap.capped_flow_id)
            p.flowcap.overflow_flow_id = _rn(p.flowcap.overflow_flow_id)
    return id_map
