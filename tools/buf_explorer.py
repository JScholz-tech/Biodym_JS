import marimo

__generated_with = "0.23.3"
app = marimo.App(width="full", app_title="BUF Explorer")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    return go, make_subplots, mo, np


@app.cell
def _(mo):
    mo.md(r"""
    # BUF Explorer — Biomass Utilisation Factor

    Interactive implementation based on *vom Berg et al. (2022), nova-Paper #16*.

    $$\text{BUF}_{RP} = \sum_{n=1}^{N} BI_n \cdot PE_n
    \qquad
    PE_n = \frac{BBP_n + BE_n + FF_n + UF_n}{100}
    \qquad
    BI_{n+1} = BI_n \cdot \frac{BBP_n}{100}$$

    | Code | Name | Role |
    |:---:|:---|:---|
    | **BBP** | Bio-Based Products | Credited **and cascades** — physical material stock carries on to next stage |
    | **BE**  | Bioenergy | Credited, **terminal** — energy cannot be re-used as material |
    | **FF**  | Functional Filling | Credited, **terminal** — e.g. soil, road subbase |
    | **UF**  | Useful Biosphere Return | Credited, **terminal** — e.g. compost, mulch |
    | **Lost**| 100 − (BBP+BE+FF+UF) | Not credited, not cascading — waste or process losses |

    Cascade stops when $BI_n < \text{cutoff} \times BI_0$.
    BUF **can exceed 1** because each cascade stage contributes independently to the sum.
    """)
    return


@app.cell
def _():
    def _s(*rows):
        return [dict(zip(("bbp", "be", "ff", "uf"), r)) for r in rows]

    PRESETS = {
        "Direct Incorporation (1 stage)": {
            "stages": _s((0, 5, 0, 90)),
            "note": "All biomass to soil as organic amendment. No physical product — cascade impossible. BUF = PE₁ = 0.95.",
        },
        "Biogas + Digestate (1 stage)": {
            "stages": _s((0, 55, 0, 40)),
            "note": "55 % as biogas energy (BE) + 40 % digestate back to soil (UF). BUF = 0.95.",
        },
        "Wood — 3-stage cascade": {
            "stages": _s((70, 5, 0, 5), (60, 10, 5, 5), (0, 80, 5, 5)),
            "note": "Classic cascade: sawn lumber → chipboard/MDF → energy recovery. BBP cascades at each stage → BUF > 1.",
        },
        "Bioplastics — 2-stage": {
            "stages": _s((85, 5, 0, 5), (0, 75, 5, 10)),
            "note": "High-value bio-based plastic product, then end-of-life thermal recovery.",
        },
        "Ideal — 4-stage": {
            "stages": _s((90, 0, 0, 5), (85, 5, 0, 5), (70, 10, 5, 10), (0, 80, 5, 10)),
            "note": "Near-ideal cascade with high BBP fractions. Demonstrates BUF >> 1 when cascading is efficient.",
        },
        "Straw bale building": {
            "stages": _s((88, 2, 0, 5), (0, 70, 5, 10)),
            "note": "88 % to construction (long-lived BBP), 5 % to soil during installation (UF), then end-of-life energy.",
        },
        "Custom": {
            "stages": _s((50, 20, 10, 15), (40, 30, 10, 15)),
            "note": "Blank scenario for free experimentation.",
        },
    }
    MAX_STAGES = 6
    return MAX_STAGES, PRESETS


@app.cell
def _(PRESETS, mo):
    preset_dd = mo.ui.dropdown(
        options=list(PRESETS.keys()),
        value="Wood — 3-stage cascade",
        label="Scenario preset",
    )
    cutoff_sl = mo.ui.slider(0.0, 20.0, value=5.0, step=0.5, label="Cascade cutoff (% of BI₀)")
    bi0_num   = mo.ui.number(start=1, stop=1_000_000, value=1000, step=10,
                             label="BI₀ (dry matter, any consistent unit)")
    return bi0_num, cutoff_sl, preset_dd


@app.cell
def _(MAX_STAGES, PRESETS, mo, preset_dd):
    _p  = PRESETS[preset_dd.value]
    _np = len(_p["stages"])

    stage_sliders = []
    for _i in range(MAX_STAGES):
        _sp = _p["stages"][_i] if _i < _np else {"bbp": 0, "be": 0, "ff": 0, "uf": 0}
        stage_sliders.append({
            "bbp": mo.ui.slider(0, 100, value=_sp["bbp"], step=1, label="BBP %"),
            "be":  mo.ui.slider(0, 100, value=_sp["be"],  step=1, label="BE %"),
            "ff":  mo.ui.slider(0, 100, value=_sp["ff"],  step=1, label="FF %"),
            "uf":  mo.ui.slider(0, 100, value=_sp["uf"],  step=1, label="UF %"),
        })

    n_stages_sl = mo.ui.slider(1, MAX_STAGES, value=min(_np, MAX_STAGES), step=1,
                                label="Active stages")
    return n_stages_sl, stage_sliders


@app.cell
def _(PRESETS, bi0_num, cutoff_sl, mo, n_stages_sl, preset_dd, stage_sliders):
    _note = PRESETS[preset_dd.value]["note"]
    _n    = n_stages_sl.value

    _cols = []
    for _i in range(_n):
        _s   = stage_sliders[_i]
        _tot = _s["bbp"].value + _s["be"].value + _s["ff"].value + _s["uf"].value
        _ok  = "✅" if _tot <= 100 else "⚠️ >100 %"
        _cols.append(mo.vstack([
            mo.md(f"#### Stage {_i + 1}"),
            _s["bbp"], _s["be"], _s["ff"], _s["uf"],
            mo.md(
                f"Lost: **{max(0, 100 - _tot):.0f} %** &nbsp;|&nbsp; "
                f"PE = **{min(_tot, 100):.0f} %** {_ok}"
            ),
        ]))

    return mo.vstack([
        mo.hstack([preset_dd, mo.callout(mo.md(_note), kind="info")]),
        mo.hstack([n_stages_sl, cutoff_sl, bi0_num]),
        mo.md("---"),
        mo.hstack(_cols, gap=3, wrap=True),
    ])


@app.cell
def _(bi0_num, cutoff_sl, n_stages_sl, stage_sliders):
    BI0    = float(bi0_num.value)
    cutoff = cutoff_sl.value / 100.0
    N      = n_stages_sl.value

    stages_data = []
    _bi = BI0
    _buf_acc = 0.0

    for _i in range(N):
        if _i > 0 and _bi < cutoff * BI0:
            break
        _s    = stage_sliders[_i]
        _bbp  = _s["bbp"].value
        _be   = _s["be"].value
        _ff   = _s["ff"].value
        _uf   = _s["uf"].value
        _tot  = _bbp + _be + _ff + _uf
        _pe   = min(_tot, 100) / 100.0
        _lost = max(0, 100 - _tot)

        _contrib  = _bi * _pe
        _buf_acc += _contrib

        stages_data.append({
            "stage":    _i + 1,
            "bi":       _bi,
            "bbp_pct":  _bbp,  "be_pct":  _be,  "ff_pct":  _ff,  "uf_pct":  _uf,
            "lost_pct": _lost,
            "bbp_abs":  _bi * _bbp  / 100,
            "be_abs":   _bi * _be   / 100,
            "ff_abs":   _bi * _ff   / 100,
            "uf_abs":   _bi * _uf   / 100,
            "lost_abs": _bi * _lost / 100,
            "pe":       _pe,
            "contrib":  _contrib,
            "buf_cum":  _buf_acc,
        })
        _bi = _bi * _bbp / 100.0

    buf_rp   = _buf_acc / BI0 if BI0 > 0 else 0.0
    bi_waste = _bi   # biomass that cascaded below cutoff (unrealised)
    return BI0, bi_waste, buf_rp, stages_data


@app.cell
def _(BI0, bi_waste, buf_rp, mo, stages_data):
    _n = len(stages_data)
    _credited = sum(d["contrib"] for d in stages_data) / BI0 if BI0 > 0 else 0
    mo.hstack([
        mo.stat(f"{buf_rp:.4f}",  label="BUF_RP",                bordered=True),
        mo.stat(f"{_n}",           label="Active cascade stages", bordered=True),
        mo.stat(f"{_credited:.4f}", label="Total PE (credited fraction)", bordered=True),
        mo.stat(f"{bi_waste:.2f}", label="BI below cutoff (not counted)", bordered=True),
    ])


@app.cell
def _(BI0, buf_rp, go, make_subplots, stages_data):
    CAT_COLORS = {
        "BBP":  "#1565C0",
        "BE":   "#E65100",
        "FF":   "#2E7D32",
        "UF":   "#6A1B9A",
        "Lost": "#90A4AE",
    }

    _xl = [f"Stage {d['stage']}" for d in stages_data]
    _contribs = [d["contrib"] / BI0 for d in stages_data]
    _cumuls   = [d["buf_cum"]  / BI0 for d in stages_data]

    fig_main = make_subplots(
        rows=1, cols=3,
        subplot_titles=("Biomass fate per stage", "BUF accumulation per stage", "BI input per stage"),
        column_widths=[0.44, 0.32, 0.24],
    )

    # Stacked fate bars
    for _cat, _key in [
        ("BBP","bbp_abs"), ("BE","be_abs"), ("FF","ff_abs"), ("UF","uf_abs"), ("Lost","lost_abs")
    ]:
        fig_main.add_trace(go.Bar(
            name=_cat, x=_xl, y=[d[_key] for d in stages_data],
            marker_color=CAT_COLORS[_cat],
        ), row=1, col=1)

    # BUF contribution bars + cumulative line
    fig_main.add_trace(go.Bar(
        name="BUF stage contribution", x=_xl, y=_contribs,
        marker_color=[CAT_COLORS["BBP"], CAT_COLORS["BE"], CAT_COLORS["FF"],
                      CAT_COLORS["UF"], "#78909C"][:len(stages_data)],
        text=[f"{v:.3f}" for v in _contribs], textposition="outside",
        showlegend=False,
    ), row=1, col=2)
    fig_main.add_trace(go.Scatter(
        name="Cumulative BUF_RP", x=_xl, y=_cumuls,
        mode="lines+markers+text",
        text=[f"{v:.3f}" for v in _cumuls], textposition="top center",
        line=dict(color="#C62828", width=2.5), marker=dict(size=9, color="#C62828"),
    ), row=1, col=2)
    fig_main.add_hline(
        y=1.0, line_dash="dash", line_color="gray", line_width=1.5,
        annotation_text="BUF = 1", annotation_position="right",
        row=1, col=2,
    )

    # BI per stage
    fig_main.add_trace(go.Bar(
        name="BI input", x=_xl, y=[d["bi"] for d in stages_data],
        marker_color="#B0BEC5",
        text=[f"{v:.1f}" for v in [d["bi"] for d in stages_data]],
        textposition="outside", showlegend=False,
    ), row=1, col=3)

    fig_main.update_yaxes(title_text="Dry matter (DM units)", row=1, col=1)
    fig_main.update_yaxes(title_text="BUF (dimensionless)", row=1, col=2)
    fig_main.update_yaxes(title_text="Dry matter (DM units)", row=1, col=3)
    fig_main.update_layout(
        barmode="stack", height=430,
        margin=dict(t=60, b=50, l=60, r=20),
        legend=dict(orientation="h", y=-0.22),
        title_text=f"BUF_RP = {buf_rp:.4f}  (BI₀ = {BI0:.0f})",
    )
    fig_main


@app.cell
def _(BI0, go, stages_data):
    _N = len(stages_data)

    if _N == 0:
        fig_sk = go.Figure()
        fig_sk.update_layout(title="No active stages")
    else:
        _SC = {
            "BBP":  "rgba(21,101,192,0.65)",
            "BE":   "rgba(230,81,0,0.65)",
            "FF":   "rgba(46,125,50,0.65)",
            "UF":   "rgba(106,27,154,0.65)",
            "Lost": "rgba(144,164,174,0.55)",
        }
        _NC = "#455A64"

        # Node indices
        _n_in        = 0
        _n_stg       = list(range(1, _N + 1))
        _n_bbp_final = _N + 1
        _n_be        = _N + 2
        _n_ff        = _N + 3
        _n_uf        = _N + 4
        _n_lost      = _N + 5

        _be_tot   = sum(d["be_abs"]   for d in stages_data)
        _ff_tot   = sum(d["ff_abs"]   for d in stages_data)
        _uf_tot   = sum(d["uf_abs"]   for d in stages_data)
        _lost_tot = sum(d["lost_abs"] for d in stages_data)

        _labels = (
            [f"Input  {BI0:.0f}"]
            + [f"Stage {d['stage']}  BI={d['bi']:.1f}" for d in stages_data]
            + [
                f"BBP (final)  {stages_data[-1]['bbp_abs']:.1f}",
                f"Bioenergy (BE)  {_be_tot:.1f}",
                f"Func. Filling (FF)  {_ff_tot:.1f}",
                f"Biosphere Return (UF)  {_uf_tot:.1f}",
                f"Lost  {_lost_tot:.1f}",
            ]
        )

        _src, _tgt, _val, _col = [], [], [], []

        # Input → Stage 1
        _src.append(_n_in); _tgt.append(_n_stg[0]); _val.append(BI0)
        _col.append("rgba(144,164,174,0.35)")

        for _i, _d in enumerate(stages_data):
            _sn = _n_stg[_i]

            # BBP either cascades to next stage or exits at final
            if _d["bbp_abs"] > 0.01:
                _tn = _n_stg[_i + 1] if _i < _N - 1 else _n_bbp_final
                _src.append(_sn); _tgt.append(_tn); _val.append(_d["bbp_abs"])
                _col.append(_SC["BBP"])

            for _cat, _key, _tn in [
                ("BE",   "be_abs",   _n_be),
                ("FF",   "ff_abs",   _n_ff),
                ("UF",   "uf_abs",   _n_uf),
                ("Lost", "lost_abs", _n_lost),
            ]:
                if _d[_key] > 0.01:
                    _src.append(_sn); _tgt.append(_tn); _val.append(_d[_key])
                    _col.append(_SC[_cat])

        fig_sk = go.Figure(go.Sankey(
            arrangement="snap",
            node=dict(
                label=_labels, pad=18, thickness=20,
                color=_NC, line=dict(color="white", width=0.5),
            ),
            link=dict(source=_src, target=_tgt, value=_val, color=_col),
        ))
        fig_sk.update_layout(
            title_text="Biomass Cascade — Sankey Flow Diagram",
            height=440, margin=dict(t=60, b=20, l=20, r=20),
        )

    fig_sk


@app.cell
def _(mo):
    mo.md("---\n## Step-by-Step Calculation Table")


@app.cell
def _(BI0, buf_rp, mo, stages_data):
    _rows = [
        {
            "Stage": f"Stage {d['stage']}",
            "BI_n": f"{d['bi']:.2f}",
            "BBP %": d["bbp_pct"],
            "BE %":  d["be_pct"],
            "FF %":  d["ff_pct"],
            "UF %":  d["uf_pct"],
            "Lost %":d["lost_pct"],
            "PE_n":  f"{d['pe']:.4f}",
            "BI_n × PE_n": f"{d['contrib']:.2f}",
            "BI_n × PE_n / BI₀": f"{d['contrib'] / BI0:.4f}",
            "BUF_RP cumulative": f"{d['buf_cum'] / BI0:.4f}",
        }
        for d in stages_data
    ]
    mo.vstack([
        mo.ui.table(_rows, selection=None) if _rows else mo.md("*(no active stages)*"),
        mo.md(f"**BUF_RP = {buf_rp:.4f}**"),
    ])


@app.cell
def _(mo):
    mo.md("---\n## Scenario Comparison — All Presets at Fixed Settings")


@app.cell
def _(PRESETS, cutoff_sl, go, make_subplots, mo):
    _cutoff = cutoff_sl.value / 100.0
    _BI0    = 100.0  # always normalised for comparison

    _names, _bufs, _stages_counts = [], [], []

    for _name, _p in PRESETS.items():
        if _name == "Custom":
            continue
        _bi = _BI0
        _buf_acc = 0.0
        _n_active = 0

        for _i, _sp in enumerate(_p["stages"]):
            if _i > 0 and _bi < _cutoff * _BI0:
                break
            _pe = min(_sp["bbp"] + _sp["be"] + _sp["ff"] + _sp["uf"], 100) / 100.0
            _buf_acc += _bi * _pe
            _n_active += 1
            _bi = _bi * _sp["bbp"] / 100.0

        _names.append(_name.split("(")[0].strip()[:30])
        _bufs.append(_buf_acc / _BI0)
        _stages_counts.append(_n_active)

    _BAR_COLORS = ["#1565C0", "#2E7D32", "#E65100", "#6A1B9A", "#B71C1C", "#00838F"]

    _fig_cmp = make_subplots(
        rows=1, cols=2,
        subplot_titles=("BUF_RP by scenario", "Active cascade stages"),
        column_widths=[0.65, 0.35],
    )
    _fig_cmp.add_trace(go.Bar(
        x=_names, y=_bufs, marker_color=_BAR_COLORS[:len(_names)],
        text=[f"{v:.3f}" for v in _bufs], textposition="outside",
        showlegend=False,
    ), row=1, col=1)
    _fig_cmp.add_hline(y=1.0, line_dash="dash", line_color="gray",
                       annotation_text="BUF = 1", row=1, col=1)
    _fig_cmp.add_trace(go.Bar(
        x=_names, y=_stages_counts, marker_color=_BAR_COLORS[:len(_names)],
        text=_stages_counts, textposition="outside",
        showlegend=False,
    ), row=1, col=2)

    _fig_cmp.update_yaxes(title_text="BUF_RP (dimensionless)", row=1, col=1)
    _fig_cmp.update_yaxes(title_text="Stages", row=1, col=2)
    _fig_cmp.update_layout(
        height=380, margin=dict(t=60, b=80, l=60, r=20),
        title_text=f"Preset comparison  (BI₀ = {_BI0:.0f}, cutoff = {cutoff_sl.value:.1f} %)",
        xaxis=dict(tickangle=-20), xaxis2=dict(tickangle=-20),
    )

    mo.vstack([
        _fig_cmp,
        mo.md("""
        **When does BUF exceed 1?**
        Only when material cascades through multiple stages (BBP > 0 at stages 1..N−1).
        In a single-stage system BUF = PE₁ ≤ 1 always.
        The theoretical maximum is unbounded — if BBP = 100 % and PE = 1 at every stage,
        BUF grows without limit until the cascade cutoff terminates it.
        """),
    ])


if __name__ == "__main__":
    app.run()
