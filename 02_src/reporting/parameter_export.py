# -*- coding: utf-8 -*-
"""
Parameter overview export for the BioDYM workflow.

Writes a single Excel workbook documenting ALL model input parameters as the
engine actually consumes them (i.e. the parsed parameter dicts, not the raw
input sheets). Every sheet labels each parameter with the paper symbol from
the notation reference, so the workbook doubles as the code<->paper bridge for
a concrete case study. This is the companion overview for systems defined in
the bioDYM SystemDefiner, whose YAML configs are otherwise hard to skim.

Mathematical notation (see bioDYM_mathematical_formulas.md):
    Paper symbol    Code variable / source
    TC_i(t)      <->  mfa_system.ParameterDict[...].Values (per outflow)   §1.2-1.3
    φ_f^e        <->  Flow_E{n}_Fraction[%] (1_1_Definition_Flows)          §2.2
    α_L          <->  fomp "Inflow_fraction_f (Labile pool)"                §3.1
    k_L, k_R     <->  fomp "decay_k1/k2 (...)"                              §3.3
    k_j, DOC_j   <->  lfg fractions "k_j", "DOC_j"                          §4.1
    w_j          <->  lfg fractions "f_input_j"                             §4.1
    ψ            <->  lfg "phi"                                             §4.4
    α_i, μ_i, σ_i <-> dsm inflow_split / lifetimes Mean / StdDev            §5.1-5.5
    κ, λ         <->  dsm lifetimes Shape / Scale (Weibull)                 §5.5-5.6
"""

from datetime import datetime

import numpy as np
import pandas as pd

NOTATION_REF = "Writing project/Monographie/bioDYM_mathematical_formulas.md"

_COLUMNS = ["Symbol", "Code variable", "Process", "Flow", "Value",
            "Unit", "Description", "Ref."]

# FOMP Excel-key -> (symbol, unit, ref, description)
_FOMP_KEY_MAP = {
    "Inflow_fraction_f (Labile pool)": (
        "α_L", "-", "§3.1", "Labile inflow fraction"),
    "decay_k1 (Labile pool)": (
        "k_L", "yr⁻¹", "§3.3", "Labile pool decay constant"),
    "decay_k2 (Recalcitrant pool)": (
        "k_R", "yr⁻¹", "§3.3", "Recalcitrant pool decay constant"),
    "Inflow_fraction_f (Recalcitrant pool)": (
        "1-α_L", "-", "§3.1",
        "IGNORED by the engine - derived as 1-α_L (see memory: FOMP "
        "recalcitrant fraction)"),
    "outflow_id": (
        "F_carbon", "-", "§3.5", "Flow ID receiving the carbon outflow"),
    "outflow_id_2": (
        "F_env", "-", "§3.5",
        "Flow ID receiving the environmental outflow (optional; merged into "
        "the carbon flow if absent)"),
}

# LFG site-parameter key -> (symbol, unit, ref, description)
_LFG_SITE_MAP = {
    "MCF": ("MCF", "-", "§4.4", "Methane correction factor"),
    "DOCf": ("DOC_f", "-", "§4.1", "Decomposable fraction of DOC"),
    "F_CH4": ("F_CH4", "-", "§4.4", "CH4 volume fraction in landfill gas"),
    "OX": ("OX", "-", "§4.4", "Oxidation factor (cover soil)"),
    "phi": ("ψ", "-", "§4.4", "UNFCCC model correction factor"),
    "outflow_ch4_id": ("G_CH4", "-", "§4.4", "Flow ID receiving CH4-carbon"),
    "outflow_co2_id": ("G_CO2", "-", "§4.4", "Flow ID receiving CO2-carbon"),
    "outflow_leachate_id": (
        "F_leachate", "-", "§4.5", "Flow ID receiving leachate water"),
}

# LFG per-fraction key -> (symbol, unit, ref, description)
_LFG_FRACTION_MAP = {
    "k_j": ("k_j", "yr⁻¹", "§4.3", "First-order decay rate of fraction j"),
    "DOC_j": ("DOC_j", "-", "§4.1", "Degradable organic carbon fraction"),
    "f_input_j": ("w_j", "-", "§4.1", "Mass fraction of waste category j"),
    "f_ash_j": ("f_ash,j", "-", "§4.2", "Ash fraction of waste category j"),
}

# Initial-stock parameter-type -> (symbol, unit, ref, description)
_INITIAL_STOCK_MAP = {
    "Basic_Material_Quantity[UoM]": (
        "S_0", "Mg", "§6", "Total initial stock at simulation start"),
    "Cohort_Age_Distribution_Type": (
        "-", "-", "§6.2", "Age distribution of the initial stock (Method B)"),
    "Cohort_Mean_Age[years]": (
        "μ_age", "yr", "§6.2", "Mean age of initial stock items"),
    "Cohort_StdDev_Age[years]": (
        "σ_age", "yr", "§6.2", "StdDev of initial stock item ages"),
    "Cohort_Max_Age[years]": (
        "A_max", "yr", "§6.2", "Maximum age of initial stock items"),
    "Cohort_Decay_Constant[years]": (
        "λ_age", "yr", "§6.2", "Exponential age-distribution scale"),
}

# Known configuration attributes -> (symbol, ref, description)
_CONFIG_MAP = {
    "START_YEAR": ("t = 0", "§0.2", "First simulation year"),
    "END_YEAR": ("t = T", "§0.2", "Last simulation year"),
    "RUN_DSM_CALCULATION": ("-", "§5", "DSM module switch"),
    "RUN_FOMP_CALCULATION": ("-", "§3", "FOMP module switch"),
    "RUN_LFG_CALCULATION": ("-", "§4", "LFG module switch"),
    "RUN_MONTE_CARLO": ("-", "§8", "Monte Carlo switch"),
    "MC_ITERATIONS": ("n", "§8", "Number of Monte Carlo iterations"),
    "MC_SEED": ("-", "§8", "Random seed for reproducible MC sampling"),
    "SOLVER_MAX_ITERATIONS": ("-", "§1.4", "Fixed-point iteration cap"),
    "SOLVER_STRICT": ("-", "§1.4", "Raise instead of warn on non-convergence"),
    "MASS_BALANCE_TOLERANCE": ("ε_rel", "§1.5", "Mass balance tolerance"),
}

_SYMBOL_LEGEND = [
    ("F_f^e(t)", "Mass flow of element e in flow f", "Mg yr⁻¹", "§0.2"),
    ("S_p^e(t)", "Stock of element e in process p", "Mg", "§0.2"),
    ("φ_f^e", "Static content fraction (element per parent element)", "-", "§2.2"),
    ("TC_i(t)", "Transfer coefficient of outflow i", "-", "§1.2-1.3"),
    ("α_L", "FOMP labile inflow fraction", "-", "§3.1"),
    ("k_L, k_R", "FOMP labile / recalcitrant decay constants", "yr⁻¹", "§3.3"),
    ("r_TC(t)", "Carbon-to-dry-matter ratio of FOMP inflow", "-", "§3.4"),
    ("k_j", "LFG decay rate of waste fraction j", "yr⁻¹", "§4.3"),
    ("DOC_j", "Degradable organic carbon fraction of category j", "-", "§4.1"),
    ("DOC_f", "Decomposable fraction of DOC", "-", "§4.1"),
    ("w_j", "Mass fraction of waste category j (code: f_input_j)", "-", "§4.1"),
    ("f_ash,j", "Ash fraction of waste category j", "-", "§4.2"),
    ("MCF", "Methane correction factor", "-", "§4.4"),
    ("F_CH4", "CH4 volume fraction in landfill gas", "-", "§4.4"),
    ("OX", "Oxidation factor (cover soil)", "-", "§4.4"),
    ("ψ", "UNFCCC model correction factor (code: phi)", "-", "§4.4"),
    ("α_i", "DSM inflow split fraction of lifetime category i", "-", "§5.2"),
    ("μ_i, σ_i", "Mean / StdDev of DSM lifetime distribution", "yr", "§5.5"),
    ("κ, λ", "Weibull shape / scale (DSM lifetime)", "-, yr", "§5.5-5.6"),
    ("μ_c", "Mean lifetime of DSM component c", "yr", "§7"),
    ("S_0", "Initial stock at simulation start", "Mg", "§6"),
    ("A_max", "Maximum age of initial stock items", "yr", "§6.2"),
    ("μ_age, σ_age", "Mean / StdDev of initial stock age distribution", "yr", "§6.2"),
    ("λ_age", "Exponential age-distribution scale", "yr", "§6.2"),
]


def _row(symbol="", code="", process="", flow="", value="", unit="",
         description="", ref=""):
    """Builds one uniformly keyed sheet row (missing fields stay blank)."""
    return {
        "Symbol": symbol, "Code variable": code, "Process": process,
        "Flow": flow, "Value": value, "Unit": unit,
        "Description": description, "Ref.": ref,
    }


def _scalar(value):
    """Converts numpy scalars to Python; leaves everything else unchanged."""
    if isinstance(value, np.generic):
        return value.item()
    return value


# ─── Sheet builders (each returns a DataFrame; empty DataFrame = skip) ────────

def _build_export_info(mfa_system, source_file):
    time_items = list(mfa_system.IndexTable.Classification["Time"].Items)
    rows = [
        ("Export type", "BioDYM parameter overview (model inputs)"),
        ("Created", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        ("Source input file", str(source_file)),
        ("Simulation horizon", f"{time_items[0]}-{time_items[-1]} "
                               f"({len(time_items)} years)"),
        ("Elements", ", ".join(mfa_system.Elements)),
        ("Processes", len(mfa_system.ProcessList)),
        ("Flows", len(mfa_system.FlowDict)),
        ("Notation reference", NOTATION_REF),
        ("Note", "Values are shown as parsed by the engine loaders - "
                 "they may differ from raw sheet values (e.g. interpolated "
                 "dynamic TCs)."),
    ]
    return pd.DataFrame(rows, columns=["Attribute", "Value"])


def _build_configuration(config_obj):
    attrs = {k: v for k, v in vars(config_obj).items()
             if not k.startswith("_") and not callable(v)}
    # The Config object stores every setting twice (Mixed_Case + UPPERCASE
    # alias); keep one row per setting, preferring the uppercase alias name
    # because the engine guards read those.
    seen_upper = {}
    for key in sorted(attrs, key=lambda k: (k.upper(), k != k.upper())):
        if key.upper() not in seen_upper:
            seen_upper[key.upper()] = key

    rows = []
    for upper_key, key in sorted(seen_upper.items()):
        value = attrs[key]
        if isinstance(value, (pd.DataFrame, pd.Series)):
            value = f"<{type(value).__name__}, not shown>"
        elif isinstance(value, (list, tuple, dict)):
            value = str(value)
        symbol, ref, desc = _CONFIG_MAP.get(upper_key, ("", "", ""))
        rows.append(_row(symbol=symbol, code=key, value=_scalar(value),
                         ref=ref, description=desc))
    return pd.DataFrame(rows, columns=_COLUMNS)


def _build_processes(all_excel_data, process_logic_map):
    proc_df = (all_excel_data or {}).get("2_1_Definition_Processes")
    rows = []
    if proc_df is not None and not proc_df.empty:
        for _, prow in proc_df.iterrows():
            pid = prow.get("Process_ID", prow.get("ID"))
            if pd.isna(pid):
                continue
            pid = int(pid)
            logic = (process_logic_map or {}).get(
                pid, prow.get("Process_Logic", ""))
            rows.append({
                "Process_ID": pid,
                "Name": prow.get("Process_Name", ""),
                "Process_Logic": logic,
                "Stock_Configuration": prow.get("Stock_Configuration", ""),
                "TC_Configuration": prow.get("TC_Configuration", ""),
                "Description": ("System boundary (source and sink)"
                                if logic in ("Input", "Output") else ""),
            })
    elif process_logic_map:
        for pid, logic in sorted(process_logic_map.items()):
            rows.append({"Process_ID": pid, "Name": "", "Process_Logic": logic,
                         "Stock_Configuration": "", "TC_Configuration": "",
                         "Description": ""})
    return pd.DataFrame(rows)


def _build_initial_stock(all_excel_data):
    is_df = (all_excel_data or {}).get("2_4_Initial_Stock")
    rows = []
    if is_df is not None and not is_df.empty:
        for _, srow in is_df.iterrows():
            ptype = str(srow.get("IS_Parameter_type", ""))
            symbol, unit, ref, desc = _INITIAL_STOCK_MAP.get(
                ptype, ("", "", "§6", ""))
            if ptype.startswith("Basic_E") and "Fraction" in ptype:
                symbol, unit, ref = "φ_p^e", "-", "§2.2"
                desc = "Element composition of the initial stock"
            rows.append(_row(
                symbol=symbol, code=ptype,
                process=_scalar(srow.get("Process_ID", "")),
                value=_scalar(srow.get("IS_Parameter_Value", "")),
                unit=unit, description=desc, ref=ref))
    return pd.DataFrame(rows, columns=_COLUMNS)


def _build_flow_composition(all_excel_data, elements):
    flow_df = (all_excel_data or {}).get("1_1_Definition_Flows")
    rows = []
    if flow_df is None or flow_df.empty:
        return pd.DataFrame(rows, columns=_COLUMNS)

    frac_cols = {}  # element name -> column name
    for col in flow_df.columns:
        if col.startswith("Flow_E") and "_Fraction" in col:
            try:
                elem_idx = int(col.split("_")[1][1:]) - 1  # E{n} is 1-based
            except ValueError:
                continue
            if 0 <= elem_idx < len(elements):
                frac_cols[elements[elem_idx]] = col

    for _, frow in flow_df.iterrows():
        fid = frow.get("Flow_ID", "")
        route = ""
        from_p = frow.get("Flow_Output_Process_ID")
        to_p = frow.get("Input_Process_ID")
        if pd.notna(from_p) and pd.notna(to_p):
            route = f"P{int(from_p)} -> P{int(to_p)}"
        for elem, col in frac_cols.items():
            value = frow.get(col)
            if value is None or pd.isna(value):
                continue
            rows.append(_row(
                symbol=f"φ_f^{elem}", code=col, process=route, flow=fid,
                value=_scalar(value), unit="-",
                description=f"Content fraction of {elem} "
                            "(relative to its parent element)",
                ref="§2.2"))
    return pd.DataFrame(rows, columns=_COLUMNS)


def _reverse_flow_tc_map(flow_tc_map):
    """Inverts {flow: {element: param}} to {param: (flow, element)}."""
    reverse = {}
    for flow_name, tc_ids in (flow_tc_map or {}).items():
        if not isinstance(tc_ids, dict):
            continue
        for element, param_name in tc_ids.items():
            if param_name:
                reverse.setdefault(param_name, (flow_name, element))
    return reverse


def _build_transfer_coefficients(tc_params, flow_tc_map, time_vector):
    reverse = _reverse_flow_tc_map(flow_tc_map)
    rows, series = [], {}
    for name, param in sorted((tc_params or {}).items()):
        values = getattr(param, "Values", param)
        flow_name, element = reverse.get(name, ("", ""))
        is_dynamic = isinstance(values, np.ndarray) and values.ndim >= 1
        if is_dynamic:
            symbol = "TC_i(t)" if element in ("", "material") else f"TC_i^{element}(t)"
            value = (f"dynamic: min {np.nanmin(values):.4g}, "
                     f"mean {np.nanmean(values):.4g}, "
                     f"max {np.nanmax(values):.4g}")
            series[name] = np.asarray(values, dtype=float)
        else:
            symbol = "TC_i" if element in ("", "material") else f"TC_i^{element}"
            value = _scalar(values)
        rows.append(_row(
            symbol=symbol, code=name, flow=flow_name, value=value, unit="-",
            description=("Element-specific transfer coefficient (Transformer)"
                         if element not in ("", "material")
                         else "Transfer coefficient")
                        + (" - full series in sheet TC_Time_Series"
                           if is_dynamic else ""),
            ref="§1.2-1.3"))

    tc_df = pd.DataFrame(rows, columns=_COLUMNS)

    series_df = pd.DataFrame()
    if series:
        series_df = pd.DataFrame(series, index=list(time_vector))
        series_df.index.name = "Year"
    return tc_df, series_df


def _build_dsm(dsm_params):
    rows = []
    for pid, params in sorted((dsm_params or {}).items()):
        if not params:
            continue
        lifetimes = params.get("lifetimes", {})
        cat_names = params.get("category_names", [])
        splits = params.get("inflow_split", [])
        types = lifetimes.get("Type", [])
        means = lifetimes.get("Mean", [])
        stds = lifetimes.get("StdDev", [])
        shapes = lifetimes.get("Shape", [])
        scales = lifetimes.get("Scale", [])

        for i, cat in enumerate(cat_names):
            def _at(seq, idx=i):
                return _scalar(seq[idx]) if idx < len(seq) else ""
            lt_type = str(_at(types) or "normal")
            rows.append(_row(
                symbol=f"α_{i + 1}", code="inflow_split", process=pid,
                value=_at(splits), unit="-",
                description=f"Inflow split to category '{cat}'", ref="§5.2"))
            rows.append(_row(
                symbol="-", code="Lifetime_Type", process=pid, value=lt_type,
                description=f"Lifetime distribution of category '{cat}'",
                ref="§5.5"))
            if _at(means) not in ("", 0.0):
                rows.append(_row(
                    symbol=f"μ_{i + 1}", code="Lifetime_Mean", process=pid,
                    value=_at(means), unit="yr",
                    description=f"Mean lifetime, category '{cat}'", ref="§5.5"))
            if _at(stds) not in ("", 0.0):
                rows.append(_row(
                    symbol=f"σ_{i + 1}", code="Lifetime_StdDev", process=pid,
                    value=_at(stds), unit="yr",
                    description=f"Lifetime StdDev, category '{cat}'",
                    ref="§5.5"))
            if _at(shapes) not in ("", None):
                rows.append(_row(
                    symbol="κ", code="Lifetime_Shape", process=pid,
                    value=_at(shapes), unit="-",
                    description=f"Weibull shape, category '{cat}'",
                    ref="§5.5-5.6"))
            if _at(scales) not in ("", None):
                rows.append(_row(
                    symbol="λ", code="Lifetime_Scale", process=pid,
                    value=_at(scales), unit="yr",
                    description=f"Weibull scale, category '{cat}'",
                    ref="§5.5-5.6"))

        if params.get("stock_configuration"):
            rows.append(_row(
                symbol="-", code="stock_configuration", process=pid,
                value=params["stock_configuration"],
                description="Initial-stock handling method", ref="§6"))
        for fid in params.get("output_flow_ids", []):
            rows.append(_row(
                symbol="TC_i", code="output_flow_ids", process=pid, flow=fid,
                description="DSM outflow routing target", ref="§5.4"))
        for comp in params.get("components", []):
            rows.append(_row(
                symbol="μ_c", code="mean_lifetime", process=pid,
                value=_scalar(comp.get("mean_lifetime", "")), unit="yr",
                description=f"Component '{comp.get('element', '?')}' - "
                            f"spare flows {comp.get('sparepart_inflow', '?')} / "
                            f"{comp.get('sparepart_outflow', '?')}",
                ref="§7"))
    return pd.DataFrame(rows, columns=_COLUMNS)


def _build_fomp(fomp_params):
    rows = []
    for pid, params in sorted((fomp_params or {}).items()):
        for key, value in (params or {}).items():
            if value is None:
                continue
            symbol, unit, ref, desc = _FOMP_KEY_MAP.get(
                key, ("", "-", "§3", ""))
            rows.append(_row(symbol=symbol, code=key, process=pid,
                             value=_scalar(value), unit=unit,
                             description=desc, ref=ref))
    return pd.DataFrame(rows, columns=_COLUMNS)


def _build_lfg(lfg_params):
    rows = []
    for pid, params in sorted((lfg_params or {}).items()):
        for key, value in (params or {}).items():
            if key == "fractions" or value is None:
                continue
            symbol, unit, ref, desc = _LFG_SITE_MAP.get(key, ("", "-", "§4", ""))
            rows.append(_row(symbol=symbol, code=key, process=pid,
                             value=_scalar(value), unit=unit,
                             description=desc, ref=ref))
        for frac in (params or {}).get("fractions", []):
            frac_name = frac.get("name", "?")
            for key, value in frac.items():
                if key == "name" or value is None:
                    continue
                symbol, unit, ref, desc = _LFG_FRACTION_MAP.get(
                    key, ("", "-", "§4", ""))
                rows.append(_row(
                    symbol=symbol, code=key, process=pid,
                    value=_scalar(value), unit=unit,
                    description=f"{desc} - fraction '{frac_name}'", ref=ref))
    return pd.DataFrame(rows, columns=_COLUMNS)


def _build_flow_cap(flow_cap_params):
    rows = []
    for pid, params in sorted((flow_cap_params or {}).items()):
        cap_series = (params or {}).get("cap_series", {})
        cap_desc = ""
        if cap_series:
            vals = list(cap_series.values())
            cap_desc = (f"{len(cap_series)} year(s), "
                        f"min {min(vals):.4g}, max {max(vals):.4g} Mg")
        rows.append(_row(
            symbol="-", code="capped_flow_id", process=pid,
            flow=(params or {}).get("capped_flow_id", ""),
            description="Flow limited by the cap"))
        rows.append(_row(
            symbol="-", code="overflow_flow_id", process=pid,
            flow=(params or {}).get("overflow_flow_id", ""),
            description="Flow receiving the excess above the cap"))
        rows.append(_row(
            symbol="-", code="cap_series", process=pid, value=cap_desc,
            unit="Mg", description="Annual cap values"))
        if (params or {}).get("cap_tc_id"):
            rows.append(_row(
                symbol="-", code="cap_tc_id", process=pid,
                value=params["cap_tc_id"],
                description="ParameterDict key (scenario-switchable cap)"))
    return pd.DataFrame(rows, columns=_COLUMNS)


def _build_bom(bom_params):
    rows = []
    for pid, params in sorted((bom_params or {}).items()):
        for key, value in (params or {}).items():
            rows.append(_row(symbol="-", code=str(key), process=pid,
                             value=str(_scalar(value)),
                             description="BOM Assembler configuration"))
    return pd.DataFrame(rows, columns=_COLUMNS)


def _build_uncertainty(uncertainty_params):
    rows = []
    for name, defn in sorted((uncertainty_params or {}).items()):
        detail = {k: v for k, v in (defn or {}).items()}
        dist = detail.pop("distribution", "?")
        rows.append({
            "Parameter": name,
            "Distribution": dist,
            "Mean": detail.pop("mean", ""),
            "StdDev": detail.pop("std", ""),
            "Min": detail.pop("min", ""),
            "Mode": detail.pop("mode", ""),
            "Max": detail.pop("max", ""),
            "Operation": detail.pop("operation", ""),
            "Start_Year": detail.pop("start_year", ""),
            "End_Year": detail.pop("end_year", ""),
            "Other": ", ".join(f"{k}={v}" for k, v in detail.items()),
            "Ref.": "§8.1",
        })
    return pd.DataFrame(rows)


def _build_symbol_legend():
    return pd.DataFrame(
        _SYMBOL_LEGEND, columns=["Symbol", "Meaning", "Unit", "Ref."])


# ─── Writer ───────────────────────────────────────────────────────────────────

def _write_sheet(writer, header_format, sheet_name, df, index=False):
    df.to_excel(writer, sheet_name=sheet_name, index=index)
    worksheet = writer.sheets[sheet_name]
    offset = 1 if index else 0
    if index and df.index.name:
        worksheet.write(0, 0, df.index.name, header_format)
    for col_num, col_name in enumerate(df.columns):
        worksheet.write(0, col_num + offset, str(col_name), header_format)
        width = max(
            [len(str(col_name))]
            + [len(str(v)) for v in df[col_name].head(200)]
        )
        worksheet.set_column(col_num + offset, col_num + offset,
                             min(max(width + 2, 10), 70))
    worksheet.freeze_panes(1, 0)


def export_parameter_overview(
    mfa_system,
    config_obj,
    output_path,
    tc_params=None,
    dsm_params=None,
    fomp_params=None,
    lfg_params=None,
    flow_cap_params=None,
    bom_params=None,
    uncertainty_params=None,
    process_logic_map=None,
    flow_tc_map=None,
    all_excel_data=None,
    source_file="Not specified",
):
    """Exports all model input parameters to one Excel workbook.

    Each sheet covers one parameter domain and labels every entry with the
    paper symbol from the notation reference (bioDYM_mathematical_formulas.md),
    so the workbook serves as a reviewable overview of everything that was
    defined in the SystemDefiner / Excel input.

    Parameters
    ----------
    mfa_system : odym.MFAsystem
        Configured system (Elements, IndexTable, ProcessList, FlowDict).
    config_obj : object
        Configuration object from ``config.load_configuration()`` /
        ``config.load_config_from_yaml()``.
    output_path : str
        Target ``.xlsx`` path; parent folders are created if needed.
    tc_params : dict, optional
        ODYM Parameter objects keyed by TC name (``load_tc_parameters``).
        Falls back to ``mfa_system.ParameterDict`` entries named ``TC*``.
    dsm_params, fomp_params, lfg_params, flow_cap_params, bom_params : dict, optional
        Parsed module parameter dicts keyed by process ID
        (``data_loader.load_all_parameters``).
    uncertainty_params : dict, optional
        Monte Carlo definitions (``load_uncertainty_definitions``).
    process_logic_map : dict, optional
        Process ID -> logic string.
    flow_tc_map : dict, optional
        Flow name -> {element: TC parameter name}; used to attribute TCs
        to their flow and element.
    all_excel_data : dict, optional
        Loaded (or YAML-synthesised) input sheets; used for the process,
        initial-stock, and flow-composition sheets.
    source_file : str, optional
        Input file path recorded in the Export_Info sheet.

    Returns
    -------
    str
        The written output path.
    """
    import os

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    if tc_params is None:
        tc_params = {
            name: param
            for name, param in getattr(mfa_system, "ParameterDict", {}).items()
            if str(name).startswith("TC")
        }

    time_vector = list(mfa_system.IndexTable.Classification["Time"].Items)

    tc_df, tc_series_df = _build_transfer_coefficients(
        tc_params, flow_tc_map, time_vector)

    sheets = [
        ("1_Configuration", _build_configuration(config_obj), False),
        ("2_Processes", _build_processes(all_excel_data, process_logic_map),
         False),
        ("3_Initial_Stock", _build_initial_stock(all_excel_data), False),
        ("4_Flow_Composition",
         _build_flow_composition(all_excel_data, mfa_system.Elements), False),
        ("5_Transfer_Coefficients", tc_df, False),
        ("5b_TC_Time_Series", tc_series_df, True),
        ("6_DSM", _build_dsm(dsm_params), False),
        ("7_FOMP", _build_fomp(fomp_params), False),
        ("8_LFG", _build_lfg(lfg_params), False),
        ("9_FlowCap", _build_flow_cap(flow_cap_params), False),
        ("10_BOM", _build_bom(bom_params), False),
        ("11_Uncertainty", _build_uncertainty(uncertainty_params), False),
        ("12_Symbol_Legend", _build_symbol_legend(), False),
    ]

    info_df = _build_export_info(mfa_system, source_file)
    included = [name for name, df, _ in sheets if not df.empty]
    skipped = [name for name, df, _ in sheets if df.empty]
    info_extra = pd.DataFrame(
        [("Included sheets", ", ".join(included)),
         ("Skipped (no data)", ", ".join(skipped) if skipped else "-")],
        columns=["Attribute", "Value"])
    info_df = pd.concat([info_df, info_extra], ignore_index=True)

    with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
        workbook = writer.book
        header_format = workbook.add_format(
            {"bold": True, "bottom": 2, "bg_color": "#F0F0F0"})
        _write_sheet(writer, header_format, "0_Export_Info", info_df)
        for name, df, with_index in sheets:
            if df.empty:
                continue
            _write_sheet(writer, header_format, name, df, index=with_index)

    n_params = sum(len(df) for name, df, _ in sheets
                   if not df.empty and name != "12_Symbol_Legend")
    print(f"   ✓ Parameter overview: {n_params} entries in "
          f"{len(included)} sheet(s) -> {output_path}")
    return output_path
