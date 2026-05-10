import marimo

__generated_with = "0.23.3"
app = marimo.App(width="full", app_title="CUF Explorer")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    from scipy import stats
    return go, make_subplots, mo, np, stats


@app.cell
def _(mo):
    mo.md(r"""
    # CUF Explorer — Carbon Utilization Factor

    Dual sub-indicator for carbon cycle assessment in bio-based systems.

    | Sub-indicator | Formula | BUF analog |
    |---|---|---|
    | **CUF_cascade** | (C_material + C_soil + C_energy) / CI₀ | Production efficiency, TC basis |
    | **CUF_temporal** | (1/T_ref) × (1/CI₀) × Σ [S_DSM(t) + S_FOMP(t)] | No analog — temporal retention |

    *All models assume a single TC pulse at t = 0. Adjust parameters to explore how
    carbon fate and retention time shape the two sub-indicators.*
    """)
    return


@app.cell
def _():
    PRESETS = {
        "DI — Direct Incorporation": dict(
            frac_dsm=0.00, frac_fomp=1.00, frac_lfg=0.00,
            f_labile=0.82, k_labile=15.95, k_rec=0.050,
            dsm_mu=50, dsm_sigma=15,
            note="All carbon to soil. Fast labile pool dominates — low CUF_temporal.",
        ),
        "P&I — Pyrolysis & Incorporation": dict(
            frac_dsm=0.00, frac_fomp=1.00, frac_lfg=0.00,
            f_labile=0.006, k_labile=15.95, k_rec=0.00252,
            dsm_mu=50, dsm_sigma=15,
            note="Biochar: 99.4% recalcitrant pool, very slow decay — high CUF_temporal.",
        ),
        "AD&I — Anaerobic Digestion": dict(
            frac_dsm=0.00, frac_fomp=0.45, frac_lfg=0.55,
            f_labile=0.55, k_labile=15.95, k_rec=0.050,
            dsm_mu=50, dsm_sigma=15,
            note="55% to biogas (no long-term stock), 45% as digestate to soil.",
        ),
        "CM — Construction Material": dict(
            frac_dsm=0.90, frac_fomp=0.10, frac_lfg=0.00,
            f_labile=0.82, k_labile=15.95, k_rec=0.050,
            dsm_mu=50, dsm_sigma=15,
            note="90% to physical stock (straw bale). Long lifetime → high CUF_temporal.",
        ),
    }
    return (PRESETS,)


@app.cell
def _(PRESETS, mo):
    scenario_dd = mo.ui.dropdown(
        options=list(PRESETS.keys()),
        value="DI — Direct Incorporation",
        label="Scenario preset",
    )
    return (scenario_dd,)


@app.cell
def _(PRESETS, mo, scenario_dd):
    _p = PRESETS[scenario_dd.value]

    # Global
    t_sim_sl  = mo.ui.slider(50, 200, value=100, step=10,  label="Simulation horizon T (yr)")
    t_ref_sl  = mo.ui.slider(25, 200, value=100, step=25,  label="T_ref for CUF_temporal (yr)")
    ci0_num   = mo.ui.number(start=100, stop=1_000_000, value=10_000, step=100, label="CI₀ (Mg C)")

    # Carbon routing
    frac_dsm_sl  = mo.ui.slider(0.0, 1.0, value=_p["frac_dsm"],  step=0.01, label="→ DSM  (material stock)")
    frac_fomp_sl = mo.ui.slider(0.0, 1.0, value=_p["frac_fomp"], step=0.01, label="→ FOMP (soil C)")
    frac_lfg_sl  = mo.ui.slider(0.0, 1.0, value=_p["frac_lfg"],  step=0.01, label="→ LFG  (biogas, no stock)")

    # FOMP
    f_labile_sl = mo.ui.slider(0.001, 1.0,  value=_p["f_labile"],  step=0.001, label="f_labile")
    k_lab_sl    = mo.ui.slider(0.01,  30.0, value=_p["k_labile"],  step=0.01,  label="k_labile (yr⁻¹)")
    k_rec_sl    = mo.ui.slider(0.0001, 0.5, value=_p["k_rec"],     step=0.0001,label="k_recalcitrant (yr⁻¹)")

    # DSM
    dsm_mu_sl    = mo.ui.slider(1, 150, value=_p["dsm_mu"],    step=1, label="Lifetime μ (yr)")
    dsm_sigma_sl = mo.ui.slider(0, 75,  value=_p["dsm_sigma"], step=1, label="Lifetime σ (yr)")

    return (
        ci0_num, dsm_mu_sl, dsm_sigma_sl, f_labile_sl,
        frac_dsm_sl, frac_fomp_sl, frac_lfg_sl,
        k_lab_sl, k_rec_sl, t_ref_sl, t_sim_sl,
    )


@app.cell
def _(
    PRESETS, ci0_num, dsm_mu_sl, dsm_sigma_sl, f_labile_sl,
    frac_dsm_sl, frac_fomp_sl, frac_lfg_sl,
    k_lab_sl, k_rec_sl, mo, scenario_dd, t_ref_sl, t_sim_sl,
):
    _note = PRESETS[scenario_dd.value]["note"]
    return mo.vstack([
        mo.hstack([scenario_dd, mo.callout(mo.md(_note), kind="info")]),
        mo.md("**Simulation**"),
        mo.hstack([t_sim_sl, t_ref_sl, ci0_num]),
        mo.md("**Carbon Routing** *(fractions need not sum to 1 — remainder is unproductive loss)*"),
        mo.hstack([frac_dsm_sl, frac_fomp_sl, frac_lfg_sl]),
        mo.md("**FOMP parameters**"),
        mo.hstack([f_labile_sl, k_lab_sl, k_rec_sl]),
        mo.md("**DSM parameters**"),
        mo.hstack([dsm_mu_sl, dsm_sigma_sl]),
    ])


@app.cell
def _(
    ci0_num, dsm_mu_sl, dsm_sigma_sl, f_labile_sl,
    frac_dsm_sl, frac_fomp_sl, frac_lfg_sl,
    k_lab_sl, k_rec_sl, np, stats, t_ref_sl, t_sim_sl,
):
    T      = t_sim_sl.value
    T_ref  = t_ref_sl.value
    CI0    = ci0_num.value
    t_arr  = np.arange(T)

    # Normalise routing fractions (cap productive at 1, remainder = released)
    _total_prod = frac_dsm_sl.value + frac_fomp_sl.value + frac_lfg_sl.value
    _scale = min(1.0, 1.0 / _total_prod) if _total_prod > 0 else 1.0
    f_dsm  = frac_dsm_sl.value  * _scale
    f_fomp = frac_fomp_sl.value * _scale
    f_lfg  = frac_lfg_sl.value  * _scale
    f_lost = max(0.0, 1.0 - f_dsm - f_fomp - f_lfg)

    # Carbon fate (cumulative)
    c_material = CI0 * f_dsm
    c_soil     = CI0 * f_fomp
    c_energy   = CI0 * f_lfg
    c_released = CI0 * f_lost

    # --- DSM stock (Normal lifetime, single cohort at t=0) ---
    _mu, _sig = dsm_mu_sl.value, dsm_sigma_sl.value
    if _sig > 0:
        stock_dsm = c_material * (1 - stats.norm.cdf(t_arr, loc=_mu, scale=_sig))
    else:
        stock_dsm = c_material * (t_arr < _mu).astype(float)

    # --- FOMP stock (two-pool, single pulse at t=0) ---
    _fl  = f_labile_sl.value
    _kl  = k_lab_sl.value
    _kr  = k_rec_sl.value
    stock_fomp_lab = c_soil * _fl       * np.exp(-_kl * t_arr)
    stock_fomp_rec = c_soil * (1 - _fl) * np.exp(-_kr * t_arr)
    stock_fomp     = stock_fomp_lab + stock_fomp_rec

    # LFG: no long-term stock (gas released immediately)
    stock_lfg = np.zeros(T)

    # --- CUF metrics ---
    productive = c_material + c_soil + c_energy
    cuf_cascade  = productive / CI0 if CI0 > 0 else 0.0
    stock_integ  = float(np.sum(stock_dsm + stock_fomp))   # Δt = 1 yr
    cuf_temporal = stock_integ / (CI0 * T_ref) if (CI0 > 0 and T_ref > 0) else 0.0

    # BUF (DM proxy — same routing, DM assumed proportional to TC here)
    buf = cuf_cascade  # identical for single-element model

    return (
        T, T_ref, CI0, t_arr,
        c_material, c_soil, c_energy, c_released,
        stock_dsm, stock_fomp, stock_fomp_lab, stock_fomp_rec, stock_lfg,
        cuf_cascade, cuf_temporal, buf,
    )


@app.cell
def _(cuf_cascade, cuf_temporal, mo):
    mo.hstack([
        mo.stat(f"{cuf_cascade:.4f}", label="CUF_cascade", bordered=True),
        mo.stat(f"{cuf_temporal:.4f}", label="CUF_temporal", bordered=True),
        mo.stat(f"{cuf_cascade:.4f}", label="BUF (DM proxy)", bordered=True),
    ])


@app.cell
def _(
    CI0, T, T_ref, c_energy, c_material, c_released, c_soil,
    cuf_temporal, go, make_subplots, stock_dsm, stock_fomp,
    stock_fomp_lab, stock_fomp_rec, t_arr,
):
    fig1 = make_subplots(
        rows=1, cols=2,
        subplot_titles=("TC Stock Time-Series", "Carbon Fate Breakdown"),
        column_widths=[0.65, 0.35],
    )

    # --- Left: stock time-series ---
    fig1.add_trace(go.Scatter(
        x=t_arr, y=stock_dsm,
        name="DSM (physical stock)", line=dict(color="#2196F3", width=2),
        fill="tozeroy", fillcolor="rgba(33,150,243,0.15)",
    ), row=1, col=1)
    fig1.add_trace(go.Scatter(
        x=t_arr, y=stock_fomp_rec,
        name="FOMP recalcitrant", line=dict(color="#4CAF50", width=2),
        fill="tozeroy", fillcolor="rgba(76,175,80,0.15)",
    ), row=1, col=1)
    fig1.add_trace(go.Scatter(
        x=t_arr, y=stock_fomp_lab,
        name="FOMP labile", line=dict(color="#8BC34A", width=2, dash="dot"),
        fill="tozeroy", fillcolor="rgba(139,195,74,0.10)",
    ), row=1, col=1)

    # T_ref vline
    fig1.add_vline(x=T_ref, line_dash="dash", line_color="gray",
                   annotation_text=f"T_ref={T_ref}yr", row=1, col=1)

    # CUF_temporal annotation
    _area = float((stock_dsm + stock_fomp).sum())
    fig1.add_annotation(
        x=T * 0.65, y=(stock_dsm + stock_fomp).max() * 0.85,
        text=f"∫Stock dt = {_area:,.0f} Mg·C·yr<br>CUF_temporal = {cuf_temporal:.4f}",
        showarrow=False, bgcolor="white", bordercolor="gray",
        row=1, col=1,
    )

    # --- Right: fate pie ---
    _labels = ["C_material (DSM)", "C_soil (FOMP)", "C_energy (LFG)", "C_released"]
    _values = [c_material, c_soil, c_energy, c_released]
    _colors = ["#2196F3", "#4CAF50", "#FF9800", "#F44336"]
    fig1.add_trace(go.Pie(
        labels=_labels, values=_values,
        marker=dict(colors=_colors),
        textinfo="label+percent",
        hole=0.35,
    ), row=1, col=2)

    fig1.update_xaxes(title_text="Year", row=1, col=1)
    fig1.update_yaxes(title_text="TC Stock (Mg C)", row=1, col=1)
    fig1.update_layout(
        height=420, showlegend=True,
        legend=dict(x=0.01, y=0.99),
        margin=dict(t=50, b=40, l=60, r=20),
        title_text=f"CI₀ = {CI0:,.0f} Mg C",
    )
    fig1


@app.cell
def _(mo):
    mo.md("---\n## Scenario Comparison\nComputes all four presets at fixed parameters for direct comparison.")


@app.cell
def _(PRESETS, mo, np, stats, t_ref_sl, t_sim_sl):
    _T    = t_sim_sl.value
    _Tref = t_ref_sl.value
    _CI0  = 10_000.0
    _t    = np.arange(_T)

    _rows = []
    for _name, _p in PRESETS.items():
        _f_dsm  = _p["frac_dsm"]
        _f_fomp = _p["frac_fomp"]
        _f_lfg  = _p["frac_lfg"]

        # DSM
        _mu, _sig = _p["dsm_mu"], _p["dsm_sigma"]
        if _sig > 0:
            _s_dsm = _CI0 * _f_dsm * (1 - stats.norm.cdf(_t, loc=_mu, scale=_sig))
        else:
            _s_dsm = _CI0 * _f_dsm * (_t < _mu).astype(float)

        # FOMP
        _fl = _p["f_labile"]
        _kl, _kr = _p["k_labile"], _p["k_rec"]
        _s_fomp = _CI0 * _f_fomp * (
            _fl * np.exp(-_kl * _t) + (1 - _fl) * np.exp(-_kr * _t)
        )

        _productive = (_f_dsm + _f_fomp + _f_lfg) * _CI0
        _cascade  = _productive / _CI0
        _temporal = float(np.sum(_s_dsm + _s_fomp)) / (_CI0 * _Tref)
        _rows.append((_name.split("—")[0].strip(), _cascade, _temporal))

    _labels    = [r[0] for r in _rows]
    _cascades  = [r[1] for r in _rows]
    _temporals = [r[2] for r in _rows]

    import plotly.graph_objects as _go
    from plotly.subplots import make_subplots as _msp

    _fig2 = _msp(rows=1, cols=2, subplot_titles=("CUF_cascade", "CUF_temporal"))

    _colors = ["#F44336", "#4CAF50", "#FF9800", "#2196F3"]
    _fig2.add_trace(_go.Bar(
        x=_labels, y=_cascades, marker_color=_colors, showlegend=False,
        text=[f"{v:.3f}" for v in _cascades], textposition="outside",
    ), row=1, col=1)
    _fig2.add_trace(_go.Bar(
        x=_labels, y=_temporals, marker_color=_colors, showlegend=False,
        text=[f"{v:.3f}" for v in _temporals], textposition="outside",
    ), row=1, col=2)

    _fig2.update_yaxes(title_text="CUF_cascade", range=[0, 1.15], row=1, col=1)
    _fig2.update_yaxes(title_text="CUF_temporal", row=1, col=2)
    _fig2.update_layout(
        height=380, margin=dict(t=60, b=40),
        title_text=f"Preset comparison  (T={_T} yr, T_ref={_Tref} yr, CI₀={_CI0:,.0f} Mg C)",
    )

    mo.vstack([
        _fig2,
        mo.md(f"""
        **Key insight:** CUF_cascade is near 1 for all scenarios (all carbon goes to *some* productive use).
        CUF_temporal clearly discriminates P&I (biochar persists) and CM (long building lifetime)
        from DI (fast soil decay) and AD&I (biogas has no long-term stock).
        """),
    ])


@app.cell
def _(mo):
    mo.md("""
    ---
    ## FOMP Pool Decomposition
    *Explore how labile/recalcitrant split and decay rates shape the soil carbon stock.*
    """)


@app.cell
def _(
    CI0, f_labile_sl, go, k_lab_sl, k_rec_sl, np, t_arr,
):
    _fl  = f_labile_sl.value
    _kl  = k_lab_sl.value
    _kr  = k_rec_sl.value
    _c   = CI0  # assume all carbon goes to FOMP for this diagnostic

    _s_lab = _c * _fl       * np.exp(-_kl * t_arr)
    _s_rec = _c * (1 - _fl) * np.exp(-_kr * t_arr)

    # Half-lives
    _hl_lab = float(np.log(2) / _kl) if _kl > 0 else float("inf")
    _hl_rec = float(np.log(2) / _kr) if _kr > 0 else float("inf")

    _fig3 = go.Figure()
    _fig3.add_trace(go.Scatter(
        x=t_arr, y=_s_lab,
        name=f"Labile (t½ = {_hl_lab:.2f} yr)",
        line=dict(color="#8BC34A", width=2, dash="dot"),
    ))
    _fig3.add_trace(go.Scatter(
        x=t_arr, y=_s_rec,
        name=f"Recalcitrant (t½ = {_hl_rec:.1f} yr)",
        line=dict(color="#388E3C", width=2),
    ))
    _fig3.add_trace(go.Scatter(
        x=t_arr, y=_s_lab + _s_rec,
        name="Total FOMP stock",
        line=dict(color="#1B5E20", width=3),
        fill="tozeroy", fillcolor="rgba(27,94,32,0.1)",
    ))
    _fig3.update_layout(
        xaxis_title="Year", yaxis_title="TC Stock (Mg C)",
        title=f"FOMP pools  |  f_labile={_fl:.3f}  k_lab={_kl:.3f}  k_rec={_kr:.4f}",
        height=350, margin=dict(t=50, b=40, l=60, r=20),
    )
    _fig3


if __name__ == "__main__":
    app.run()
