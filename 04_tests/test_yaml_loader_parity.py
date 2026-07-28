# -*- coding: utf-8 -*-
"""Parity guard: native YAML loaders vs Excel-style loaders on synthesized sheets.

`02_src/data_loader.py` maintains, for several parameter domains, two
independent implementations that must produce equivalent dicts from the same
YAML config:

| Domain   | Native YAML loader        | Excel-style loader (on yaml_to_excel_dataframes output) |
|----------|---------------------------|---------------------------------------------------------|
| DSM      | load_dsm_from_yaml        | load_dsm_parameters                                     |
| FOMP     | load_fomp_from_yaml       | load_fomp_parameters                                    |
| LFG      | load_lfg_from_yaml        | load_lfg_parameters                                     |
| FlowCap  | load_flow_cap_from_yaml   | load_flow_cap_parameters                                |

`load_all_parameters()` dispatches to the native loader in YAML-only mode;
`00_BioDYM_Workflow.py` and `01_BioDYM_Dashboard.ipynb` (as of v1.3.5) both go
through it. This test is the safety net for the divergence class described in
`07_AI_Coding_Assistance/260722_Plan_DashboardYamlParityRefactor.md` — the
concrete FOMP bug it would have caught was the Excel-style loader silently
falling back to *default decay parameters* because `yaml_to_excel_dataframes()`
synthesized short keys that `load_fomp_parameters` never read.

Assertion contract: for every process present in the Excel-style result, the
native result must have the same process with **equal values on every shared
key**. The native loader is allowed to be a *superset* (it legitimately emits
extra routing fields the Excel-style shim omits, e.g. DSM `output_splits` /
`output_flow_ids`, FOMP `outflow_id_2`). What must never happen is a shared key
carrying a *different value* — that is the exact shape of the original bug.
"""

import re

import numpy as np
import pytest

import data_loader as dl
from pathlib import Path

# Only the tutorial studies are git-tracked and shipped (see .gitignore
# whitelist). Match the shipped whitelist so this test scans the same set on a
# developer machine and in CI, and never trips over local WEEE studies that use
# process-logic types not on public main.
_TRACKED_STUDY_RE = re.compile(r"^T\d{2}[A-Za-z]?_")
_CASE_STUDIES = Path(__file__).parents[1] / "01_data" / "01_input" / "case_studies"

_PAIRS = {
    "dsm": (dl.load_dsm_from_yaml, dl.load_dsm_parameters),
    "fomp": (dl.load_fomp_from_yaml, dl.load_fomp_parameters),
    "lfg": (dl.load_lfg_from_yaml, dl.load_lfg_parameters),
    "flow_cap": (dl.load_flow_cap_from_yaml, dl.load_flow_cap_parameters),
}


def _norm(o):
    """Recursively coerce numpy scalars to Python builtins for stable equality.

    Removes int-vs-np.int64 process-key noise and avoids numpy's ambiguous
    truth-value on element-wise comparisons.
    """
    if isinstance(o, dict):
        return {_norm(k): _norm(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_norm(x) for x in o]
    if isinstance(o, np.generic):
        return o.item()
    return o


def _tracked_studies():
    if not _CASE_STUDIES.is_dir():
        return []
    return [
        f
        for f in sorted(_CASE_STUDIES.iterdir())
        if _TRACKED_STUDY_RE.match(f.name) and (f / "config.yaml").exists()
    ]


@pytest.mark.skipif(not _CASE_STUDIES.is_dir(), reason="case_studies dir missing")
@pytest.mark.parametrize(
    "study", _tracked_studies(), ids=lambda f: f.name
)
def test_native_yaml_matches_excel_style_loader(study):
    yaml_path = str(study / "config.yaml")
    excel = dl.yaml_to_excel_dataframes(yaml_path)

    for domain, (native_loader, excel_loader) in _PAIRS.items():
        native = _norm(native_loader(yaml_path))
        excel_style = _norm(excel_loader(excel))

        for pid, exc_cfg in excel_style.items():
            assert pid in native, (
                f"{study.name}/{domain}: Excel-style loader produced process {pid} "
                f"that the native YAML loader did not."
            )
            nat_cfg = native[pid]
            for key, exc_val in exc_cfg.items():
                assert key in nat_cfg, (
                    f"{study.name}/{domain}/proc {pid}: Excel-style key '{key}' "
                    f"missing from native result."
                )
                assert nat_cfg[key] == exc_val, (
                    f"{study.name}/{domain}/proc {pid}: value divergence on '{key}' "
                    f"— native={nat_cfg[key]!r} vs excel-style={exc_val!r}. This is "
                    f"the Dashboard/Workflow parameter-loading divergence class."
                )
