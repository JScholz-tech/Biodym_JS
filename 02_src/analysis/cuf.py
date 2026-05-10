# -*- coding: utf-8 -*-
"""
Carbon Utilization Factor (CUF) — post-processing indicator module.

CUF is a dual sub-indicator for carbon cycle assessment in bioDYM.
It is conceptually analogous to the Biomass Utilisation Factor (BUF,
vom Berg et al. 2022, nova-Paper #16), extended from dry-matter to
carbon (TC) basis and augmented with a temporal dimension.

Sub-indicators
--------------
CUF_cascade
    Cumulative fraction of input carbon routed to productive use.
    Direct TC analog of BUF's production efficiency. Dimensionless, [0, 1].
    Distinguishes productive from unproductive carbon fate but cannot
    differentiate scenarios with equal efficiency and different retention times.

CUF_temporal
    Time-integrated productive TC stock, normalised by CI₀ × T_ref.
    Dimensionless; captures *how long* carbon remains in productive use.
    This is the metric that discriminates short-lived uses (direct incorporation,
    biogas) from long-lived uses (biochar, construction materials).

Usage (after running the solver)
---------------------------------
    from analysis.cuf import compute_cuf

    results = compute_cuf(
        mfa_system, process_logic_map,
        fomp_details=solver_info["fomp_details"],
        t_ref=100,
    )
    print(f"CUF_cascade  = {results['cuf_cascade']:.3f}")
    print(f"CUF_temporal = {results['cuf_temporal']:.3f}")
    print(f"BUF          = {results['buf']:.3f}")

Carbon fate categories (mapped from BUF categories)
-----------------------------------------------------
    C_material  ↔  BBP  — TC entering DSM processes (physical stocks that can cascade)
    C_soil      ↔  UF   — TC entering FOMP processes (useful biosphere return)
    C_energy    ↔  BE   — TC entering LFG processes (bioenergy)
    C_released  ↔  —    — TC flowing to boundary without productive use (no credit)
"""

import numpy as np


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_cc_idx(mfa_system):
    """Return TC/CC element index using the standard TC→CC fallback."""
    tc_name = next((e for e in ("TC", "CC") if e in mfa_system.Elements), None)
    if tc_name is None:
        raise ValueError("MFA system is missing a carbon element (TC or CC).")
    return mfa_system.Elements.index(tc_name)


def _pid_set(process_logic_map, *logic_labels):
    """Return set of process IDs whose logic matches any of the given labels."""
    labels = set(logic_labels)
    return {pid for pid, logic in process_logic_map.items() if logic in labels}


def _flow_tc_sum(flows, pid_filter, cc_idx):
    """Sum cumulative TC (Mg C) for flows whose target process is in pid_filter."""
    return float(
        sum(
            np.sum(f.Values[:, cc_idx])
            for f in flows
            if pid_filter(f)
        )
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def classify_carbon_fate(mfa_system, process_logic_map, fomp_details):
    """Classify cumulative TC flows and annual TC stocks by carbon fate category.

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        Solved MFA system (output of solver.run_mfa_calculation).
    process_logic_map : dict
        Maps process ID → logic string ("DSM", "FOMP", "LFG", "Input", ...).
        This is the same map passed to the solver.
    fomp_details : dict
        solver_info["fomp_details"] — keyed by process_id, each entry contains
        arrays "stock_tc_labile" and "stock_tc_recalcitrant" of shape (T,).

    Returns
    -------
    dict
        ci0           : float — total cumulative TC input from boundary (Mg C)
        c_material    : float — cumulative TC entering DSM processes (Mg C)
        c_soil        : float — cumulative TC entering FOMP processes (Mg C)
        c_energy      : float — cumulative TC entering LFG processes (Mg C)
        c_released    : float — ci0 − c_material − c_soil − c_energy (Mg C)
        stock_dsm_tc  : ndarray (T,) — annual total DSM TC stock (Mg C)
        stock_fomp_tc : ndarray (T,) — annual total FOMP organic TC stock (Mg C)
    """
    cc_idx = _get_cc_idx(mfa_system)
    flows = list(mfa_system.FlowDict.values())

    boundary_pids = _pid_set(process_logic_map, "Input")
    dsm_pids = _pid_set(process_logic_map, "DSM")
    fomp_pids = _pid_set(process_logic_map, "FOMP")
    lfg_pids = _pid_set(process_logic_map, "LFG")

    # CI₀: TC flowing FROM any boundary process INTO the system
    ci0 = _flow_tc_sum(
        flows,
        lambda f: f.P_Start in boundary_pids and f.P_End not in boundary_pids,
        cc_idx,
    )

    # Productive fate categories — inflows TO each process type
    c_material = _flow_tc_sum(flows, lambda f: f.P_End in dsm_pids, cc_idx)
    c_soil = _flow_tc_sum(flows, lambda f: f.P_End in fomp_pids, cc_idx)
    c_energy = _flow_tc_sum(flows, lambda f: f.P_End in lfg_pids, cc_idx)
    c_released = ci0 - c_material - c_soil - c_energy

    # Annual TC stock time-series
    T = len(mfa_system.IndexTable.Classification["Time"].Items)

    stock_dsm_tc = np.zeros(T)
    for pid in dsm_pids:
        key = f"S_{pid}"
        if key in mfa_system.StockDict:
            stock_dsm_tc += mfa_system.StockDict[key].Values[:, cc_idx]

    # Use fomp_details TC pools (organic C only) rather than StockDict, which
    # also accumulates Ash and TIC that are not part of the active carbon cycle.
    stock_fomp_tc = np.zeros(T)
    for pid in fomp_pids:
        if pid in fomp_details:
            stock_fomp_tc += (
                fomp_details[pid]["stock_tc_labile"]
                + fomp_details[pid]["stock_tc_recalcitrant"]
            )

    return {
        "ci0": ci0,
        "c_material": c_material,
        "c_soil": c_soil,
        "c_energy": c_energy,
        "c_released": c_released,
        "stock_dsm_tc": stock_dsm_tc,
        "stock_fomp_tc": stock_fomp_tc,
    }


def calculate_cuf_cascade(carbon_fate):
    """CUF_cascade: cumulative fraction of input carbon routed to productive use.

    Formula
    -------
    CUF_cascade = (C_material + C_soil + C_energy) / CI₀

    Analogous to BUF production efficiency but on TC basis. For single-stage
    cascade systems (typical bioDYM case studies), CUF_cascade ≤ 1. Values
    close to 1 indicate almost all input carbon is put to some productive use;
    the sub-indicator cannot discriminate scenarios that differ only in *how long*
    the carbon remains productive — use CUF_temporal for that.

    Parameters
    ----------
    carbon_fate : dict
        Output of classify_carbon_fate().

    Returns
    -------
    float
        CUF_cascade ∈ [0, 1].
    """
    ci0 = carbon_fate["ci0"]
    if ci0 <= 0:
        return 0.0
    productive = carbon_fate["c_material"] + carbon_fate["c_soil"] + carbon_fate["c_energy"]
    return productive / ci0


def calculate_cuf_temporal(carbon_fate, t_ref=100):
    """CUF_temporal: time-integrated productive TC stock fraction.

    Numerically integrates the combined DSM + FOMP TC stock over the simulation
    horizon (Δt = 1 year) and normalises by CI₀ × T_ref.

    Formula
    -------
    CUF_temporal = (1 / T_ref) × (1 / CI₀) × Σ_t [S_DSM(t) + S_FOMP(t)]

    Interpretation: the average fraction of the reference horizon during which
    one unit of input carbon resides in a productive stock. A scenario where all
    carbon stays in stock for the full T_ref years scores CUF_temporal = 1.

    Parameters
    ----------
    carbon_fate : dict
        Output of classify_carbon_fate().
    t_ref : float
        Reference horizon in years (default 100). Should match the simulation
        length for full-horizon assessment, or a policy-relevant period.

    Returns
    -------
    float
        CUF_temporal ≥ 0. Values > 1 indicate average residence time exceeds
        T_ref (possible when stock continues to grow within the horizon).
    """
    ci0 = carbon_fate["ci0"]
    if ci0 <= 0 or t_ref <= 0:
        return 0.0
    stock_integral = np.sum(carbon_fate["stock_dsm_tc"] + carbon_fate["stock_fomp_tc"])
    return float(stock_integral / (ci0 * t_ref))


def calculate_buf(mfa_system, process_logic_map):
    """BUF on dry-matter basis — direct comparison reference for CUF_cascade.

    Computes the single-stage production efficiency on DM basis, mapping
    bioDYM process types to BUF categories:
        DSM  → BBP (bio-based physical products)
        FOMP → UF  (useful biosphere return)
        LFG  → BE  (bioenergy)

    Formula
    -------
    BUF = (DM_BBP + DM_UF + DM_BE) / DM_CI₀

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        Solved MFA system.
    process_logic_map : dict
        Maps process ID → logic string.

    Returns
    -------
    float
        BUF ∈ [0, 1] for single-cascade systems.

    Raises
    ------
    ValueError
        If the MFA system does not include a "DM" element.
    """
    if "DM" not in mfa_system.Elements:
        raise ValueError("BUF requires a 'DM' (dry matter) element in the MFA system.")

    dm_idx = mfa_system.Elements.index("DM")
    flows = list(mfa_system.FlowDict.values())

    boundary_pids = _pid_set(process_logic_map, "Input")
    dsm_pids = _pid_set(process_logic_map, "DSM")
    fomp_pids = _pid_set(process_logic_map, "FOMP")
    lfg_pids = _pid_set(process_logic_map, "LFG")

    def _dm_sum(pid_filter):
        return float(sum(np.sum(f.Values[:, dm_idx]) for f in flows if pid_filter(f)))

    dm_ci0 = _dm_sum(
        lambda f: f.P_Start in boundary_pids and f.P_End not in boundary_pids
    )
    if dm_ci0 <= 0:
        return 0.0

    dm_bbp = _dm_sum(lambda f: f.P_End in dsm_pids)
    dm_uf = _dm_sum(lambda f: f.P_End in fomp_pids)
    dm_be = _dm_sum(lambda f: f.P_End in lfg_pids)

    return (dm_bbp + dm_uf + dm_be) / dm_ci0


def compute_cuf(mfa_system, process_logic_map, fomp_details, t_ref=100):
    """Compute all CUF metrics in a single call.

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        Solved MFA system (first element of the solver 3-tuple).
    process_logic_map : dict
        Maps process ID → logic string. Same dict passed to the solver.
    fomp_details : dict
        solver_info["fomp_details"] (third element of the solver 3-tuple).
    t_ref : float
        Reference horizon in years (default 100).

    Returns
    -------
    dict
        carbon_fate  : dict from classify_carbon_fate()
        cuf_cascade  : float
        cuf_temporal : float
        buf          : float, or None if DM element is absent

    Examples
    --------
    >>> mfa_system, dsm_details, solver_info = solver.run_mfa_calculation(...)
    >>> results = compute_cuf(mfa_system, process_logic_map, solver_info["fomp_details"])
    >>> print(results["cuf_cascade"], results["cuf_temporal"])
    """
    carbon_fate = classify_carbon_fate(mfa_system, process_logic_map, fomp_details)
    cuf_cascade = calculate_cuf_cascade(carbon_fate)
    cuf_temporal = calculate_cuf_temporal(carbon_fate, t_ref)
    try:
        buf = calculate_buf(mfa_system, process_logic_map)
    except ValueError:
        buf = None

    return {
        "carbon_fate": carbon_fate,
        "cuf_cascade": cuf_cascade,
        "cuf_temporal": cuf_temporal,
        "buf": buf,
    }


def print_cuf_summary(results, label="Scenario"):
    """Print a formatted CUF results summary to stdout.

    Parameters
    ----------
    results : dict
        Output of compute_cuf().
    label : str
        Scenario name or label shown in the header.
    """
    fate = results["carbon_fate"]
    ci0 = fate["ci0"]

    print(f"\n{'─' * 48}")
    print(f"  CUF Summary — {label}")
    print(f"{'─' * 48}")
    print(f"  CI₀ (total TC input)  : {ci0:>10.1f}  Mg C")
    print(f"  C_material (DSM)      : {fate['c_material']:>10.1f}  Mg C  ({100 * fate['c_material'] / max(ci0, 1):.1f}%)")
    print(f"  C_soil     (FOMP)     : {fate['c_soil']:>10.1f}  Mg C  ({100 * fate['c_soil'] / max(ci0, 1):.1f}%)")
    print(f"  C_energy   (LFG)      : {fate['c_energy']:>10.1f}  Mg C  ({100 * fate['c_energy'] / max(ci0, 1):.1f}%)")
    print(f"  C_released            : {fate['c_released']:>10.1f}  Mg C  ({100 * fate['c_released'] / max(ci0, 1):.1f}%)")
    print(f"{'─' * 48}")
    print(f"  CUF_cascade           : {results['cuf_cascade']:>10.4f}")
    print(f"  CUF_temporal          : {results['cuf_temporal']:>10.4f}")
    if results["buf"] is not None:
        print(f"  BUF (DM basis)        : {results['buf']:>10.4f}")
    print(f"{'─' * 48}\n")
