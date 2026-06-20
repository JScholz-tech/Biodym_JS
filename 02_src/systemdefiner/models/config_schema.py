from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, field_validator


class ProcessLogic(str, Enum):
    input = "Input"
    output = "Output"
    splitter = "Splitter"
    transformer = "Transformer"
    dsm = "DSM"
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


class FompParams(BaseModel):
    f_labile: float = 0.5
    k_labile: float = 1.0
    k_recalcitrant: float = 0.01
    outflow_id: str = ""
    outflow_id_2: Optional[str] = None
    ref: str = ""


class DsmCategory(BaseModel):
    name: str = "Default"
    inflow_split: float = 1.0
    lifetime_type: str = "Normal"
    lifetime_mean: Optional[float] = None
    lifetime_std: Optional[float] = None
    lifetime_shape: Optional[float] = None
    lifetime_scale: Optional[float] = None


class DsmParams(BaseModel):
    categories: list[DsmCategory] = []
    ref: str = ""


class LfgFraction(BaseModel):
    name: str = ""
    k_j: float = 0.1          # decay constant (1/yr)
    doc_j: float = 0.5        # degradable organic carbon fraction
    f_input_j: float = 1.0    # fraction of inflow in this waste category
    f_ash_j: float = 0.05     # ash / inert fraction


class LfgParams(BaseModel):
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


class FlowCapParams(BaseModel):
    capped_flow_id: str = ""      # flow that receives routed output (up to cap)
    overflow_flow_id: str = ""    # flow that receives excess above cap
    cap_series: dict[int, float] = {}  # {year: cap_value_Mg_per_yr}
    cap_tc_id: str = ""           # optional ParameterDict key for scenario switching


class FlowDataEntry(BaseModel):
    flow_id: str
    element: str = "material"
    values: dict[int, float] = {}   # {year: value_Mg_per_yr}, sparse — gets interpolated


class BomAssemblyFlow(BaseModel):
    flow_id: str
    output_flow_type: str = ""          # "target_Product", "waste_flow", …
    fractions: dict[str, float] = {}    # element -> fraction (target_Product only)


class BomAssemblyEntry(BaseModel):
    process_id: int
    flows: list[BomAssemblyFlow] = []


class InitialStockEntry(BaseModel):
    """Pre-existing stock present at t=0 for a process whose StockConfig is one
    of the InitialStock variants. Element fractions are absolute (of material),
    matching the engine: stock[element] = material_quantity × fraction."""
    process_id: int
    material_quantity: float = 0.0          # Basic_Material_Quantity[UoM]
    composition: dict[str, float] = {}      # element -> absolute fraction (0–1)
    # Cohort / decay parameters (Stock_with_InitialStock_Cohort / _Decay)
    cohort_age_distribution_type: str = "Normal"
    cohort_mean_age: Optional[float] = None
    cohort_std_age: Optional[float] = None
    cohort_max_age: Optional[int] = None
    cohort_decay_constant: Optional[float] = None
    ref: str = ""


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


class Flow(BaseModel):
    id: str
    name: str
    from_process: int
    to_process: int


class DynamicTCPoint(BaseModel):
    """One time point in a dynamic TC: a year with element-fraction values."""
    year: int
    values: dict[str, float]  # element_name -> fraction (0.0–1.0)


class TransferCoefficient(BaseModel):
    process_id: int
    flow_id: str
    tc_type: str = "static"          # "static" or "dynamic"
    values: dict[str, float] = {}    # static: element -> fraction
    time_series: list[DynamicTCPoint] = []  # dynamic: list of (year, values)
    ref: str = ""                    # cite key from cfg.references


class ModelSettings(BaseModel):
    start_year: int = 2025
    end_year: int = 2125
    elements: list[str] = ["material", "WC", "DM", "TC"]
    unit_of_measurement: str = "Mg"
    hierarchy_level_names: list[str] = ["Product", "Component", "Material", "Element"]

    @field_validator("hierarchy_level_names", mode="before")
    @classmethod
    def pad_level_names(cls, v):
        if not isinstance(v, list):
            v = []
        defaults = ["Product", "Component", "Material", "Element"]
        return (list(v) + defaults)[:4]
    input_file: str = ""
    output_file: str = ""
    run_dsm_calculation: bool = True
    run_fomp_calculation: bool = True
    run_monte_carlo: bool = False
    mc_iterations: int = 1000
    run_scenario_analysis: bool = False
    selected_scenarios: list[str] = ["", "", "", ""]

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


class FlowComposition(BaseModel):
    flow_id: str
    values: dict[str, float] = {}  # element_name -> fraction (0.0–1.0)
    ref: str = ""                   # cite key from cfg.references


class ScenarioModification(BaseModel):
    parameter_name: str = ""
    parameter_type: str = ""   # "Flow","TC","DSM","FOMP","IS", or "" for auto-detect
    operation: str = "replace"  # scenario engine vocabulary: "replace", "multiply", "add"
    new_value: float = 0.0
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    ref: str = ""


class ScenarioDefinition(BaseModel):
    name: str
    modifications: list[ScenarioModification] = []


class McParameter(BaseModel):
    parameter_id: str = ""
    enabled: bool = True                # MC_Parameter_Selection toggle
    distribution: str = "normal"        # uniform | normal | triangular | lognormal
    mean: Optional[float] = None        # normal / lognormal
    std: Optional[float] = None         # normal / lognormal (StdDev)
    min: Optional[float] = None         # uniform / triangular / optional bound
    max: Optional[float] = None         # uniform / triangular / optional bound
    mode: Optional[float] = None        # triangular
    operation: str = "set"              # set | multiply | add
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    flow_group: Optional[str] = None    # MC_Flow_Group (optional)
    ref: str = ""


class ReferenceEntry(BaseModel):
    cite_key: str               # BibTeX cite key from Zotero
    title: str = ""
    authors: str = ""           # formatted author string, e.g. "Bai et al. (2019)"
    year: str = ""
    item_type: str = ""         # article-journal, book, report, …
    doi: str = ""
    note: str = ""              # free-text: which value/table this reference supports


class CaseStudyConfig(BaseModel):
    schema_version: str = "1.0"
    name: str
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
