"""Config-wide cascade helpers: flow-ID renames, purges, process deletion and
renumbering. Every mutation that changes an ID or removes an entity must go
through these so no reference-bearing field is left stale.

Scalar flow-ID pointers (FOMP/LFG/FlowCap outflows, DSM_Component spare-part
flows) are enumerated via ``consistency.iter_flow_pointers`` so a pointer
field added to the schema is registered exactly once.
"""
from __future__ import annotations

import re

from systemdefiner.consistency import FLOW_ID_CONVENTION, iter_flow_pointers


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

    Keeps transfer coefficients, flow data, compositions, BOM flows, and every
    scalar outflow pointer (FOMP / LFG / FlowCap / DSM spare-part) consistent,
    plus any scenario / MC parameters keyed exactly by the old flow ID.
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
    for _label, obj, attr, _blank in iter_flow_pointers(cfg):
        if getattr(obj, attr) == old_id:
            setattr(obj, attr, new_id)
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
    for _label, obj, attr, blank in iter_flow_pointers(cfg):
        if getattr(obj, attr) in flow_ids:
            setattr(obj, attr, blank)
    for sc in cfg.scenarios:
        sc.modifications = [
            m for m in sc.modifications if m.parameter_name not in flow_ids
        ]
    cfg.mc_parameters = [
        mc for mc in cfg.mc_parameters if mc.parameter_id not in flow_ids
    ]


# Parameter-name patterns that embed process IDs (scenario mods, MC params).
# P{pid:02d}_… : DSM / FOMP / LFG / IS names.  TC_E{n}_{from}_{to} and
# TC_{from}_{to} : per-flow TC names.  TC_Cap_{pid} : FlowCap cap series.
_P_PREFIX = re.compile(r"P(\d+)(_.*)")
_TC_E_PAIR = re.compile(r"TC_E(\d+)_(\d+)_(\d+)")
_TC_PAIR = re.compile(r"TC_(\d+)_(\d+)")
_TC_CAP = re.compile(r"TC_Cap_(\d+)")


def _param_name_references_process(name: str, pid: int) -> bool:
    """True when a scenario/MC parameter name embeds process ``pid``."""
    name = (name or "").strip()
    m = _P_PREFIX.fullmatch(name)
    if m:
        return int(m.group(1)) == pid
    m = _TC_CAP.fullmatch(name)
    if m:
        return int(m.group(1)) == pid
    m = _TC_E_PAIR.fullmatch(name) or _TC_PAIR.fullmatch(name)
    if m:
        pair = m.groups()[-2:]
        return int(pair[0]) == pid or int(pair[1]) == pid
    return False


def _delete_process_cascade(cfg, pid: int) -> None:
    """Delete a process and everything that depends on it.

    Removes the process, every flow touching it (in or out), its transfer
    coefficients, BOM entry and initial stock, purges all remaining references
    to the now-removed flows (TCs, flow data, compositions, BOM flows, scalar
    outflow pointers, scenario/MC parameters), and drops scenario/MC entries
    whose parameter *name* embeds the deleted process (``P{pid:02d}_…``,
    ``TC_E*_{pid}_*``, ``TC_Cap_{pid}``) — otherwise they silently retarget
    the next process that reuses the freed ID.
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
    for sc in cfg.scenarios:
        sc.modifications = [
            m
            for m in sc.modifications
            if not _param_name_references_process(m.parameter_name, pid)
        ]
    cfg.mc_parameters = [
        mc
        for mc in cfg.mc_parameters
        if not _param_name_references_process(mc.parameter_id, pid)
    ]


# Convention flow IDs including the _N duplicate-edge suffix (F_02_06_2).
_CONV_FLOW_ID = FLOW_ID_CONVENTION


def _remap_embedded_ids(name: str, id_map: dict) -> str:
    """Rewrite the process IDs embedded in a scenario/MC parameter name.

    Handles ``P{pid:02d}_…`` (DSM/FOMP/LFG/IS), ``TC_E{n}_{from}_{to}``,
    ``TC_{from}_{to}`` and ``TC_Cap_{pid}``. Names embedding an ID that is not
    in ``id_map`` (already dangling) are returned unchanged — the consistency
    checker reports those.
    """
    name = (name or "").strip()
    m = _P_PREFIX.fullmatch(name)
    if m and int(m.group(1)) in id_map:
        return f"P{id_map[int(m.group(1))]:02d}{m.group(2)}"
    m = _TC_CAP.fullmatch(name)
    if m and int(m.group(1)) in id_map:
        return f"TC_Cap_{id_map[int(m.group(1))]:02d}"
    m = _TC_E_PAIR.fullmatch(name)
    if m and int(m.group(2)) in id_map and int(m.group(3)) in id_map:
        return (
            f"TC_E{m.group(1)}_{id_map[int(m.group(2))]:02d}"
            f"_{id_map[int(m.group(3))]:02d}"
        )
    m = _TC_PAIR.fullmatch(name)
    if m and int(m.group(1)) in id_map and int(m.group(2)) in id_map:
        return f"TC_{id_map[int(m.group(1))]:02d}_{id_map[int(m.group(2))]:02d}"
    return name


def _compact_process_ids(cfg) -> dict:
    """Renumber process IDs to a contiguous 0..N-1 range (gaps left by deletions
    break the engine, which expects 0-based contiguous IDs).

    Cascades the renumber through every reference: flow endpoints, the
    ``F_<from>_<to>`` flow IDs (including ``_N`` duplicate-edge suffixes) and
    all string references to them (TCs, flow compositions, flow data, BOM
    flows, scalar outflow pointers, scenario/MC parameters), the ``process_id``
    on TCs, BOM entries and initial stocks, and the process IDs *embedded* in
    scenario/MC parameter names (``P{pid:02d}_…``, ``TC_E*_{from}_{to}``,
    ``TC_Cap_{pid}``) plus auto-derived FlowCap ``cap_tc_id`` keys. Returns the
    old→new id map (empty when already contiguous).
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

    # Rename convention flow IDs to match the new endpoints. Two passes so the
    # outcome cannot depend on list order: first park every convention ID on a
    # unique placeholder (freeing all old names), then assign final names via
    # _next_flow_id, which suffixes on genuine collisions (custom IDs that
    # happen to look conventional) instead of silently skipping.
    conv_flows = [f for f in cfg.flows if _CONV_FLOW_ID.fullmatch(str(f.id))]
    # Base IDs before their _N siblings so duplicate edges keep suffix order.
    conv_flows.sort(
        key=lambda f: (
            f.from_process,
            f.to_process,
            int(_CONV_FLOW_ID.fullmatch(str(f.id)).group(3) or 1),
        )
    )
    flow_rename: dict[str, str] = {}
    old_by_placeholder: dict[str, str] = {}
    for i, f in enumerate(conv_flows):
        placeholder = f"__renumber_tmp_{i}__"
        old_by_placeholder[placeholder] = str(f.id)
        f.id = placeholder
    for f in conv_flows:
        old = old_by_placeholder[str(f.id)]
        final = _next_flow_id(cfg, f.from_process, f.to_process)
        f.id = final
        if final != old:
            flow_rename[old] = final

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
    for _label, obj, attr, _blank in iter_flow_pointers(cfg):
        setattr(obj, attr, _rn(getattr(obj, attr)))

    # Scenario/MC parameter names: exact flow IDs first, then embedded IDs.
    for sc in cfg.scenarios:
        for mod in sc.modifications:
            renamed = _rn(mod.parameter_name)
            if renamed != mod.parameter_name:
                mod.parameter_name = renamed
            else:
                mod.parameter_name = _remap_embedded_ids(mod.parameter_name, id_map)
    for mc in cfg.mc_parameters:
        renamed = _rn(mc.parameter_id)
        if renamed != mc.parameter_id:
            mc.parameter_id = renamed
        else:
            mc.parameter_id = _remap_embedded_ids(mc.parameter_id, id_map)

    # Auto-derived FlowCap cap IDs follow their process; hand-authored keys
    # (anything not matching TC_Cap_<old pid>) are left untouched.
    for p in cfg.processes:
        if p.flowcap and p.flowcap.cap_tc_id:
            p.flowcap.cap_tc_id = _remap_embedded_ids(p.flowcap.cap_tc_id, id_map)
    return id_map
