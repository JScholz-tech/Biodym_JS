from __future__ import annotations

from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel, field_validator, model_validator


class _Referenced(BaseModel):
    """Mixin for parameters that can cite one or more references by cite_key.

    ``refs`` is the current multi-value field; ``ref`` is the legacy single-value
    field, kept and synced for backward compatibility so old configs (and any
    code still reading ``ref``) keep working.
    """

    ref: str = ""  # legacy single cite key
    refs: list[str] = []  # current: list of cite keys (literature and/or assumptions)

    @model_validator(mode="after")
    def _sync_refs(self):
        if not self.refs and self.ref:
            self.refs = [self.ref]
        elif self.refs and not self.ref:
            self.ref = self.refs[0]
        return self


class ProcessLogic(str, Enum):
    input = "Input"
    output = "Output"
    splitter = "Splitter"
    transformer = "Transformer"
    dsm = "DSM"
    dsm_component = "DSM_Component"
    fomp = "FOMP"
    lfg = "LFG"
    bom_assembler = "BOM_Assembler"
    pass_through = "Pass-through"
    flowcap = "FlowCap"


class StockConfig(str, Enum):
    stock = "Stock"
    no_stock = "No_Stock"
    initial_stock_cohort = "Stock_with_InitialStock_Cohort"
    initial_stock_decay = "Stock_with_InitialStock_Decay"


class TCConfig(str, Enum):
    no_tc = "No TC"
    static = "Static"
    dynamic = "Dynamic"


class BufCategory(str, Enum):
    """Biomass-utilisation role (vom Berg et al. 2023, BUF).

    Assigned to a *process* to declare what the process does with the biomass/
    carbon entering it (its inflow is credited to this category). ``BBP`` is the
    only cascading role (the product carries on to a further use); the rest are
    terminal. Outflows to the atmosphere boundary are emissions (derived from the
    graph, reported as released carbon), not a role. ``unset`` defers to the
    analysis layer's auto-classifier (inferred from the process's own logic).
    """

    unset = ""
    bbp = "BBP"  # Bio-based product (cascades)
    be = "BE"  # Bioenergy (terminal)
    ff = "FF"  # Food & Feed (terminal)
    uf = "UF"  # Useful in biosphere — soil/compost (terminal)
    nf = "NF"  # Not useful in biosphere — losses (uncredited)


class FompParams(_Referenced):
    f_labile: float = 0.5
    k_labile: float = 1.0
    k_recalcitrant: float = 0.01
    outflow_id: str = ""
    outflow_id_2: Optional[str] = None


class DsmCategory(BaseModel):
    name: str = "Default"
    inflow_split: float = 1.0
    lifetime_type: str = "Normal"
    lifetime_mean: Optional[float] = None
    lifetime_std: Optional[float] = None
    lifetime_shape: Optional[float] = None
    lifetime_scale: Optional[float] = None
    component_lifetimes: dict[str, float] = {}  # {element_name: mean_lifetime_yr} per category


class DsmComponentItem(BaseModel):
    """One replaceable component tracked by the DSM_Component logic."""
    element: str
    mean_lifetime: float
    sparepart_outflow: str  # flow ID: worn parts → WEEE / recycling
    sparepart_inflow: str   # flow ID: new parts ← storage


class DsmParams(_Referenced):
    categories: list[DsmCategory] = []
    components: list[DsmComponentItem] = []  # only used for DSM_Component logic


class LfgFraction(BaseModel):
    name: str = ""
    k_j: float = 0.1  # decay constant (1/yr)
    doc_j: float = 0.5  # degradable organic carbon fraction
    f_input_j: float = 1.0  # fraction of inflow in this waste category
    f_ash_j: float = 0.05  # ash / inert fraction


class LfgParams(_Referenced):
    mcf: float = 1.0
    doc_f: float = 0.5
    f_ch4: float = 0.5
    ox: float = 0.1
    phi: float = 1.0
    f_capture: float = 0.0
    outflow_ch4_id: str = ""
    outflow_co2_id: str = ""
    outflow_leachate_id: str = ""
    fractions: list[LfgFraction] = []


class FlowCapParams(_Referenced):
    capped_flow_id: str = ""  # flow that receives routed output (up to cap)
    overflow_flow_id: str = ""  # flow that receives excess above cap
    cap_series: dict[int, float] = {}  # {year: cap_value_Mg_per_yr}
    cap_tc_id: str = ""  # optional ParameterDict key for scenario switching


class FlowDataEntry(_Referenced):
    flow_id: str
    element: str = "material"
    values: dict[int, float] = {}  # {year: value_Mg_per_yr}, sparse — gets interpolated


class BomAssemblyFlow(BaseModel):
    flow_id: str
    output_flow_type: str = ""  # "target_Product", "waste_flow", …
    fractions: dict[str, float] = {}  # element -> fraction (target_Product only)


class BomAssemblyEntry(_Referenced):
    process_id: int
    flows: list[BomAssemblyFlow] = []


class InitialStockEntry(_Referenced):
    """Pre-existing stock present at t=0 for a process whose StockConfig is one
    of the InitialStock variants. Element fractions are absolute (of material),
    matching the engine: stock[element] = material_quantity × fraction."""

    process_id: int
    material_quantity: float = 0.0  # Basic_Material_Quantity[UoM]
    composition: dict[str, float] = {}  # element -> absolute fraction (0–1)
    # Cohort / decay parameters (Stock_with_InitialStock_Cohort / _Decay)
    cohort_age_distribution_type: str = "Normal"
    cohort_mean_age: Optional[float] = None
    cohort_std_age: Optional[float] = None
    cohort_max_age: Optional[int] = None
    cohort_decay_constant: Optional[float] = None


class Process(BaseModel):
    id: int
    name: str
    logic: ProcessLogic = ProcessLogic.splitter
    stock: StockConfig = StockConfig.no_stock
    tc_config: TCConfig = TCConfig.no_tc
    fomp: Optional[FompParams] = None
    dsm: Optional[DsmParams] = None
    lfg: Optional[LfgParams] = None
    flowcap: Optional[FlowCapParams] = None
    expected_inflow_composition: Optional[Dict[str, float]] = None
    # Utilisation-framework role: what this process does with the carbon entering
    # it (its inflow is credited to this category). Blank → auto-classified from
    # the process logic by the analysis layer.
    utilisation_role: BufCategory = BufCategory.unset


class Flow(BaseModel):
    id: str
    name: str
    from_process: int
    to_process: int


class DynamicTCPoint(BaseModel):
    """One time point in a dynamic TC: a year with element-fraction values."""

    year: int
    values: dict[str, float]  # element_name -> fraction (0.0–1.0)


class TransferCoefficient(_Referenced):
    process_id: int
    flow_id: str
    tc_type: str = "static"  # "static" or "dynamic"
    values: dict[str, float] = {}  # static: element -> fraction
    time_series: list[DynamicTCPoint] = []  # dynamic: list of (year, values)


class ModelSettings(BaseModel):
    start_year: int = 2025
    end_year: int = 2125
    elements: list[str] = ["material", "WC", "DM", "TC"]
    unit_of_measurement: str = "Mg"
    # Title shown on the Sankey diagram. Blank → the study name is used.
    sankey_title: str = ""
    hierarchy_level_names: list[str] = ["Product", "Component", "Material", "Element"]

    @field_validator("hierarchy_level_names", mode="before")
    @classmethod
    def pad_level_names(cls, v):
        # Hierarchy depth is user-extensible: the number of levels ("columns"
        # in the editor) is not capped. We only guarantee a sane minimum so the
        # matrix editor always has at least a root + one child level to render.
        MIN_LEVELS = 2
        defaults = ["Product", "Component", "Material", "Element"]
        if not isinstance(v, list):
            v = []
        # Strip blanks but preserve user order and any additional levels.
        names = [str(n).strip() for n in v if str(n).strip()]
        if len(names) < MIN_LEVELS:
            # Backfill from defaults, then generic "Level N" labels if needed.
            for d in defaults:
                if len(names) >= MIN_LEVELS:
                    break
                if d not in names:
                    names.append(d)
            while len(names) < MIN_LEVELS:
                names.append(f"Level {len(names) + 1}")
        return names

    input_file: str = ""
    output_file: str = ""
    run_dsm_calculation: bool = True
    run_fomp_calculation: bool = True
    run_monte_carlo: bool = False
    mc_iterations: int = 1000
    # Monte Carlo RNG seed — an integer for reproducible runs, or "random"
    # for a fresh (non-reproducible) seed each run. Stored as a string so
    # both forms round-trip through the YAML/form cleanly.
    mc_seed: str = "42"
    # Solver controls
    solver_strict: bool = False
    solver_max_iterations: int = 30
    run_scenario_analysis: bool = False
    selected_scenarios: list[str] = ["", "", "", ""]

    @field_validator("mc_seed", mode="before")
    @classmethod
    def normalize_seed(cls, v):
        if v is None:
            return "random"
        return str(v).strip() or "42"

    @field_validator("elements", mode="before")
    @classmethod
    def parse_elements(cls, v):
        if isinstance(v, str):
            return [e.strip() for e in v.split(",") if e.strip()]
        return v

    @field_validator("selected_scenarios", mode="before")
    @classmethod
    def pad_scenarios(cls, v):
        if not isinstance(v, list):
            v = []
        return (v + ["", "", "", ""])[:4]


class ElementHierarchyRule(BaseModel):
    parent: str
    children: list[str]


class FlowComposition(_Referenced):
    flow_id: str
    values: dict[str, float] = {}  # element_name -> fraction (0.0–1.0)


class ScenarioModification(_Referenced):
    parameter_name: str = ""
    parameter_type: str = ""  # "Flow","TC","DSM","FOMP","IS", or "" for auto-detect
    operation: str = (
        "replace"  # scenario engine vocabulary: "replace", "multiply", "add"
    )
    new_value: float = 0.0
    start_year: Optional[int] = None
    end_year: Optional[int] = None


class ScenarioDefinition(BaseModel):
    name: str
    modifications: list[ScenarioModification] = []


class McParameter(_Referenced):
    parameter_id: str = ""
    enabled: bool = True  # MC_Parameter_Selection toggle
    distribution: str = "normal"  # uniform | normal | triangular | lognormal
    mean: Optional[float] = None  # normal / lognormal
    std: Optional[float] = None  # normal / lognormal (StdDev)
    min: Optional[float] = None  # uniform / triangular / optional bound
    max: Optional[float] = None  # uniform / triangular / optional bound
    mode: Optional[float] = None  # triangular
    operation: str = "set"  # set | multiply | add
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    flow_group: Optional[str] = None  # MC_Flow_Group (optional)


class ReferenceEntry(BaseModel):
    cite_key: str  # BibTeX cite key from Zotero
    title: str = ""
    authors: str = ""  # formatted author string, e.g. "Bai et al. (2019)"
    year: str = ""
    item_type: str = ""  # article-journal, book, report, …
    doi: str = ""
    note: str = ""  # free-text: which value/table this reference supports


class BufAnalysisSettings(BaseModel):
    """Parameters for the cascade-recursive Biomass Utilisation Factor."""

    enabled: bool = False
    # Cascade cutoff: stop propagating a branch when its remaining biomass
    # fraction drops below cutoff × BI₀ (vom Berg et al. 2023).
    cutoff: float = 0.05


class CufAnalysisSettings(BaseModel):
    """Parameters for the Carbon Utilization Factor (bioCUF)."""

    enabled: bool = False
    # Reference horizon (years) for normalising the temporal (tonne-year) metric.
    t_ref: int = 100
    # Whether the fast-decaying FOMP labile pool counts toward "stored" carbon in
    # the tonne-year integral. Default False → only long-residence pools credited.
    include_labile_storage: bool = False


class PathDefinition(BaseModel):
    """A named feedstock cascade (route) for per-chain analysis and comparison.

    Process-set defined: the path is the set of process IDs the route passes
    through. The feedstock entry (flows into the set) and scope (flows leaving
    the set) are derived from the flow graph at analysis time — see
    ``analysis.cascade_graph.path_flows`` — not stored here.
    """

    name: str
    processes: list[int] = []


class AnalysisConfig(BaseModel):
    """Per-study utilisation-framework analysis parameters."""

    buf: BufAnalysisSettings = BufAnalysisSettings()
    cuf: CufAnalysisSettings = CufAnalysisSettings()
    paths: list[PathDefinition] = []


class CaseStudyConfig(BaseModel):
    schema_version: str = "1.0"
    name: str
    description: str = ""  # free-text notes about the study (e.g. tutorial context)
    model: ModelSettings = ModelSettings()
    processes: list[Process] = []
    flows: list[Flow] = []
    transfer_coefficients: list[TransferCoefficient] = []
    element_hierarchy: list[ElementHierarchyRule] = []
    flow_compositions: list[FlowComposition] = []
    flow_data: list[FlowDataEntry] = []
    bom_assembly: list[BomAssemblyEntry] = []
    scenarios: list[ScenarioDefinition] = []
    mc_parameters: list[McParameter] = []
    initial_stocks: list[InitialStockEntry] = []
    references: list[ReferenceEntry] = []
    analysis: AnalysisConfig = AnalysisConfig()
