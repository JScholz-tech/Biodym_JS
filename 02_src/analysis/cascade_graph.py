# -*- coding: utf-8 -*-
"""Shared cascade graph-walk core for the utilization-framework analysis layer.

Both the Biomass Utilisation Factor (BUF, dry-matter basis; ``analysis/buf.py``)
and the carbon-cascade side of the CUF (total-carbon basis; ``analysis/cuf.py``)
are the *same* operation on a solved bioDYM ``MFAsystem`` — sum the biomass/carbon
put to a credited use across all cascade stages, normalised by the boundary input.
They differ only in the element they project onto (DM vs TC) and in the fate
vocabulary they attach to each flow.

Why the solved system already is the cascade
--------------------------------------------
A single unit of biomass entering at the atmosphere boundary propagates through
the flow graph; with static transfer coefficients the fraction reaching any
process is deterministic. The solver has *already* computed exactly that
propagation — the absolute flow values ARE the pulse, scaled by the total
boundary input BI₀. So the per-cohort single-pulse utilisation factor reduces to

    UF = Σ_stages (credited element mass entering the stage) / BI₀

which can exceed 1 whenever material cascades (biomass credited at stage n
re-enters a further credited use downstream). This is the defining BUF property.

Fate categories (vom Berg et al. 2023, Ind. Biotechnol. 19(2):49–61)
-------------------------------------------------------------------
    BBP  bio-based product (cascades)   BE  bioenergy
    FF   food & feed                    UF  useful in biosphere
    NF   not useful in biosphere (losses, uncredited)
PE (production efficiency) credits BBP+BE+FF+UF; NF is excluded.
"""

from collections import defaultdict

import numpy as np

# Credited fate categories (contribute to the production efficiency PE).
CREDITED = ("BBP", "BE", "FF", "UF")


def _pid_logic(process_logic_map, *labels):
    labels = set(labels)
    return {pid for pid, lg in process_logic_map.items() if lg in labels}


def _flow_mass(flow, e_idx):
    """Cumulative element mass carried by a flow over the whole horizon."""
    return float(np.sum(flow.Values[:, e_idx]))


def auto_classify_processes(process_logic_map, overrides=None):
    """Assign a utilisation role to every process from its own logic.

    The role is what the process does with the carbon entering it — so a process
    with a credited role credits its *inflow*. Any entry in ``overrides``
    (process_id → role string) wins; this is the per-process ``utilisation_role``
    the user sets in the SystemDefiner (e.g. an incineration Transformer → BE).

    Rules (process logic → role):
        DSM / DSM_Component → BBP  (carbon becomes a physical product)
        FOMP               → UF   (useful biosphere return: soil / compost / char)
        LFG                → BE   (bioenergy)
        anything else      → ""   (transit / boundary — no credited role)

    Returns
    -------
    dict
        process_id → role string ("BBP"/"BE"/"FF"/"UF"/"NF"/"").
    """
    overrides = overrides or {}
    roles = {}
    for pid, logic in process_logic_map.items():
        ov = overrides.get(pid)
        if ov:  # non-empty override
            roles[pid] = ov
        elif logic in ("DSM", "DSM_Component"):
            roles[pid] = "BBP"
        elif logic == "FOMP":
            roles[pid] = "UF"
        elif logic == "LFG":
            roles[pid] = "BE"
        else:
            roles[pid] = ""
    return roles


def boundary_input(mfa_system, process_logic_map, e_idx):
    """BI₀ — total element mass entering the system from boundary processes."""
    boundary = _pid_logic(process_logic_map, "Input")
    return float(
        sum(
            _flow_mass(f, e_idx)
            for f in mfa_system.FlowDict.values()
            if f.P_Start in boundary and f.P_End not in boundary
        )
    )


def path_flows(mfa_system, processes):
    """Resolve a process-set path to its entry and excluded flow IDs.

    A path is the induced sub-graph over ``processes``:
      * entry flows  — cross INTO the set (feedstock): P_End ∈ set, P_Start ∉ set
      * excluded flows — leave the set: P_Start ∈ set, P_End ∉ set (not part of
        the route; pruned from the cascade)

    Returns
    -------
    (entry_flows, excluded_flows) : tuple[list[str], list[str]]
    """
    s = set(processes)
    entry, excluded = [], []
    for fid, f in mfa_system.FlowDict.items():
        if f.P_End in s and f.P_Start not in s:
            entry.append(fid)
        elif f.P_Start in s and f.P_End not in s:
            excluded.append(fid)
    return entry, excluded


def forward_reachable(mfa_system, start_pids):
    """Set of processes reachable downstream from ``start_pids`` in the flow graph.

    Used for per-feedstock-chain evaluation: restricts the cascade to the
    sub-graph fed by a chosen entry point. Cycle-safe (visited set).
    """
    adj = defaultdict(set)
    for f in mfa_system.FlowDict.values():
        adj[f.P_Start].add(f.P_End)
    seen = set(start_pids)
    stack = list(start_pids)
    while stack:
        p = stack.pop()
        for q in adj[p]:
            if q not in seen:
                seen.add(q)
                stack.append(q)
    return seen


def _topo_order(mfa_system, process_logic_map):
    """Topological order of non-boundary processes (Kahn). Cycle remnants are
    appended in arbitrary order so propagation still terminates."""
    boundary = _pid_logic(process_logic_map, "Input")
    nodes = {
        p
        for f in mfa_system.FlowDict.values()
        for p in (f.P_Start, f.P_End)
        if p not in boundary
    }
    succ = defaultdict(set)
    indeg = {p: 0 for p in nodes}
    for f in mfa_system.FlowDict.values():
        a, b = f.P_Start, f.P_End
        if a in nodes and b in nodes and b not in succ[a]:
            succ[a].add(b)
            indeg[b] += 1
    queue = [p for p in nodes if indeg[p] == 0]
    order = []
    while queue:
        p = queue.pop()
        order.append(p)
        for q in succ[p]:
            indeg[q] -= 1
            if indeg[q] == 0:
                queue.append(q)
    order.extend(p for p in nodes if p not in order)  # cycle remnants
    return order


def propagate_from(mfa_system, process_logic_map, e_idx, entry_flows, excluded=None):
    """Entry-derived element mass on every flow, propagated from ``entry_flows``.

    Injects the entry flows' mass and pushes it downstream, at each process
    allocating throughput to outflows in proportion to their share of that
    process's total outflow (proportional-mixing assumption). This isolates the
    fraction of each downstream flow attributable to the chosen feedstock, so a
    per-chain factor is not inflated by biomass that joins the chain from other
    feedstocks.

    ``excluded`` flow IDs are pruned: the pulse does not travel along them (a
    branch the path should not follow), though they still count toward each
    process's outflow denominator so the remaining branches keep their real
    physical shares.

    Returns
    -------
    dict
        flow_id → entry-derived element mass on that flow.
    """
    flows = mfa_system.FlowDict
    excluded = set(excluded or ())
    boundary = _pid_logic(process_logic_map, "Input")
    out_total = defaultdict(float)
    outflows = defaultdict(list)
    for fid, f in flows.items():
        out_total[f.P_Start] += _flow_mass(f, e_idx)
        outflows[f.P_Start].append(fid)

    node_in = defaultdict(float)
    for fid in entry_flows:
        if fid in flows:
            node_in[flows[fid].P_End] += _flow_mass(flows[fid], e_idx)

    result = defaultdict(float)
    for p in _topo_order(mfa_system, process_logic_map):
        if p in boundary or out_total[p] <= 0 or node_in[p] <= 0:
            continue
        for fid in outflows[p]:
            if fid in excluded:
                continue
            m = node_in[p] * (_flow_mass(flows[fid], e_idx) / out_total[p])
            result[fid] += m
            q = flows[fid].P_End
            if q not in boundary:
                node_in[q] += m
    return result


def utilisation_factor(
    mfa_system, process_logic_map, process_roles, e_idx, cutoff=0.05,
    entry_flows=None, excluded_flows=None,
):
    """Cascade utilisation factor on a chosen element basis.

    Credits the element mass *entering* each process that carries a credited
    utilisation role (its inflow), normalised by BI₀. A process with a credited
    role (BBP/BE/FF/UF) is a use stage; carbon is credited again at each such
    stage it passes through, so the factor can exceed 1. Stages whose total
    inflow has dropped below ``cutoff × BI₀`` are excluded (nova cascade cut-off).
    Flows into the atmosphere boundary are emissions, summed as released carbon.

    Parameters
    ----------
    e_idx : int
        Element column index — DM for BUF, TC for the carbon cascade.
    process_roles : dict
        process_id → role override (the user's ``utilisation_role``); missing
        entries are auto-classified from logic by
        :func:`auto_classify_processes`.
    entry_flows : list[str], optional
        Per-feedstock-chain mode. When given, BI₀ = the summed mass of these
        entry flows and only the sub-cascade **downstream** of them is counted.
        When ``None`` (default), BI₀ = total boundary input and the whole system
        is evaluated (atmosphere→atmosphere).

    Returns
    -------
    dict
        value        : float — the utilisation factor (>1 possible)
        bi0          : float
        by_category  : dict role → credited mass / BI₀
        stages       : list of per-stage dicts (process, bi_at, credited, categories)
        released     : float — carbon emitted to the atmosphere boundary / BI₀
        scope        : "system" | "chain"
    """
    flows = mfa_system.FlowDict
    excluded = set(excluded_flows or ())

    if entry_flows:
        # Per-chain: BI₀ = entry-flow mass; each flow's counted mass is the
        # entry-derived fraction (proportional-mixing propagation), so biomass
        # joining the chain from other feedstocks is not credited.
        bi0 = float(
            sum(_flow_mass(flows[fid], e_idx) for fid in entry_flows if fid in flows)
        )
        flow_mass = propagate_from(
            mfa_system, process_logic_map, e_idx, entry_flows, excluded
        )
        scope = "chain"
    else:
        # System: solved flows already are the boundary pulse scaled by BI₀.
        bi0 = boundary_input(mfa_system, process_logic_map, e_idx)
        flow_mass = {
            fid: _flow_mass(f, e_idx)
            for fid, f in flows.items()
            if fid not in excluded
        }
        scope = "system"

    if bi0 <= 0:
        return {
            "value": 0.0, "bi0": 0.0, "by_category": {}, "stages": [],
            "released": 0.0, "scope": scope,
        }

    roles = auto_classify_processes(process_logic_map, process_roles or {})
    boundary = _pid_logic(process_logic_map, "Input")

    inflow_by_dest = defaultdict(float)
    for fid, f in flows.items():
        inflow_by_dest[f.P_End] += flow_mass.get(fid, 0.0)

    # Credit each flow by the role of the process it ENTERS; flows into the
    # atmosphere boundary are emissions (released), not credited.
    credited_by_dest = defaultdict(lambda: defaultdict(float))
    released_mass = 0.0
    for fid, f in flows.items():
        mass = flow_mass.get(fid, 0.0)
        dest = f.P_End
        if dest in boundary:
            released_mass += mass
        role = roles.get(dest, "")
        if role in CREDITED:
            credited_by_dest[dest][role] += mass

    total = 0.0
    by_category = defaultdict(float)
    stages = []
    for dest, catmass in credited_by_dest.items():
        if inflow_by_dest[dest] < cutoff * bi0:
            continue
        stage_credited = sum(catmass.values())
        total += stage_credited
        for cat, m in catmass.items():
            by_category[cat] += m
        stages.append({
            "process": dest,
            "bi_at": inflow_by_dest[dest],
            "credited": stage_credited,
            "categories": dict(catmass),
        })

    # Largest-first for readable reporting.
    stages.sort(key=lambda s: s["credited"], reverse=True)
    return {
        "value": total / bi0,
        "bi0": bi0,
        "by_category": {k: v / bi0 for k, v in by_category.items()},
        "stages": stages,
        "released": released_mass / bi0,
        "scope": scope,
    }
