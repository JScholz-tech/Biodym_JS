# -*- coding: utf-8 -*-
"""Biomass Utilisation Factor (BUF) — bioDYM-driven, cascade-recursive.

Faithful implementation of the published BUF (vom Berg et al. 2023,
Industrial Biotechnology 19(2):49–61) driven by a solved bioDYM ``MFAsystem``,
on a **dry-matter** basis.

    BUF_RP = Σ_stages (credited DM entering the stage) / BI₀

where a stage's credited DM covers the fate categories BBP + BE + FF + UF and
BI₀ is the total dry matter entering from the atmosphere/environment boundary.
Because a bio-based product (BBP) cascades to a further use, credited biomass is
counted again at each downstream stage, so **BUF_RP can exceed 1** — the whole
point of the metric. A single-stage system gives BUF_RP = PE₁ ≤ 1.

This is the real cascade BUF; ``cuf.calculate_stage1_efficiency`` is only the
first-stage production efficiency PE₁ and must not be confused with it.

Usage
-----
    from analysis.buf import compute_buf
    mfa_system, _, solver_info = solver.run_mfa_calculation(...)
    res = compute_buf(mfa_system, process_logic_map, cutoff=0.05)
    print(res["buf_rp"])                 # e.g. 1.37 for a multi-stage cascade
"""

from analysis import cascade_graph


def _dm_index(mfa_system):
    if "DM" not in mfa_system.Elements:
        raise ValueError("BUF requires a 'DM' (dry matter) element in the MFA system.")
    return mfa_system.Elements.index("DM")


def compute_buf(
    mfa_system, process_logic_map, process_roles=None, cutoff=0.05,
    entry_flows=None, excluded_flows=None,
):
    """Compute the cascade-recursive BUF on a solved MFA system (DM basis).

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        Solved system (first element of the solver 3-tuple).
    process_logic_map : dict
        Process ID → logic string (same dict passed to the solver).
    process_roles : dict, optional
        process_id → utilisation-role override. Missing/blank entries are
        auto-classified from the process logic (see
        ``cascade_graph.auto_classify_processes``). Pass the study's per-process
        ``utilisation_role`` values here (e.g. an incineration process → BE).
    cutoff : float
        Cascade cut-off as a fraction of BI₀ (default 0.05).
    entry_flows : list[str], optional
        Per-feedstock-chain mode — restrict to the sub-cascade downstream of
        these entry flows, with BI₀ = their summed DM. Default (None) evaluates
        the whole system (BI₀ = total boundary DM input).

    Returns
    -------
    dict
        buf_rp       : float — the Biomass Utilisation Factor (>1 possible)
        bi0          : float — total boundary DM input
        by_category  : dict — credited DM per role, as a fraction of BI₀
        released     : float — DM emitted to the atmosphere boundary / BI₀
        stages       : list — per-stage credited DM breakdown
        n_stages     : int  — number of credited use stages above the cut-off
    """
    dm_idx = _dm_index(mfa_system)
    r = cascade_graph.utilisation_factor(
        mfa_system, process_logic_map, process_roles or {}, dm_idx, cutoff,
        entry_flows=entry_flows, excluded_flows=excluded_flows,
    )
    return {
        "buf_rp": r["value"],
        "bi0": r["bi0"],
        "by_category": r["by_category"],
        "released": r["released"],
        "stages": r["stages"],
        "n_stages": len(r["stages"]),
        "scope": r["scope"],
    }


def compute_buf_for_path(
    mfa_system, process_logic_map, processes, process_roles=None, cutoff=0.05
):
    """BUF for a named process-set path (induced-subgraph route).

    Resolves the process set to its entry/excluded flows
    (:func:`cascade_graph.path_flows`) and evaluates the per-chain BUF over that
    route only.
    """
    entry, excluded = cascade_graph.path_flows(mfa_system, processes)
    return compute_buf(
        mfa_system, process_logic_map, process_roles=process_roles,
        cutoff=cutoff, entry_flows=entry, excluded_flows=excluded,
    )


def print_buf_summary(results, label="Scenario"):
    """Print a formatted BUF results summary to stdout."""
    print(f"\n{'─' * 52}")
    print(f"  BUF Summary — {label}")
    print(f"{'─' * 52}")
    print(f"  BI₀ (boundary DM input)   : {results['bi0']:>12.1f}")
    print(f"  Credited use stages       : {results['n_stages']:>12d}")
    for cat in cascade_graph.CREDITED:
        frac = results["by_category"].get(cat, 0.0)
        if frac:
            print(f"    {cat:<4} contribution        : {frac:>12.4f}")
    print(f"  Released to atmosphere    : {results['released']:>12.4f}")
    print(f"{'─' * 52}")
    tag = "  (cascade → >1)" if results["buf_rp"] > 1 else ""
    print(f"  BUF_RP                    : {results['buf_rp']:>12.4f}{tag}")
    print(f"{'─' * 52}\n")
