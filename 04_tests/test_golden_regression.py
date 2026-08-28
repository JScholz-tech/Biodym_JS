# -*- coding: utf-8 -*-
"""
Golden regression tests over the tracked tutorial case studies (T01…T15).

Each tutorial isolates one engine feature (T04 DSM, T06 FOMP, T09 FlowCap,
T10 BOM assembler, T13 LFG, T15 DSM components, …), so a failure here points
directly at the feature whose numerics changed.

The reference .npz files in 04_tests/golden/ pin the complete numerical
result (all flow and stock arrays) of each tutorial. If a numerical change is
*intentional*, regenerate them with:

    uv run python 04_tests/golden/generate_references.py

and commit the .npz diffs in their own `chore(tests)` commit.
"""

import glob
import os

import numpy as np
import pytest

from golden_utils import collect_full_results, config_file_hash

_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_TESTS_DIR)
GOLDEN_DIR = os.path.join(_TESTS_DIR, "golden")
CASE_STUDIES_DIR = os.path.join(
    _PROJECT_ROOT, "01_data", "01_input", "case_studies"
)
TEMPLATE_XLSM = os.path.join(
    _PROJECT_ROOT,
    "01_data",
    "01_input",
    "template",
    "260503_bioDYM_Systemmanager_template_final.xlsm",
)


#: Tutorials whose pinned reference is known to be wrong, with the reason.
#: A reference is quarantined rather than regenerated when the current numbers
#: are themselves invalid — regenerating would pin the defect instead of the
#: behaviour. Remove the entry together with the config fix, then regenerate.
_QUARANTINED = {
    "T18_Alloying_Element_Accumulation": (
        "Config defect exposed by the _infer_exhaustive_elements contradiction "
        "fix. T18 declares Cu = 100% of DM on the pure-copper input F_05_01 "
        "while every other flow carries Cu as a trace, which previously marked "
        "DM exhaustive; the solver then overwrote DM with Cu on the Recycling "
        "Transformer, pinning DM to Cu and masking a divergence. With DM read "
        "as partial (correct — Fe is untracked), P3's transfer coefficients "
        "give Cu no sink (F_03_00 Cu 1.0, F_03_04 Cu 0.0) while F_05_01 keeps "
        "feeding it, so Cu accumulates without bound: 300 Mg Cu inside 110 Mg "
        "of DM by year 15, and the fixed point no longer converges. The "
        "reference cannot be regenerated until the tutorial gives Cu a sink."
    ),
}


def _tutorial_names():
    pattern = os.path.join(CASE_STUDIES_DIR, "T[0-9][0-9]_*", "config.yaml")
    names = sorted(
        os.path.basename(os.path.dirname(p)) for p in glob.glob(pattern)
    )
    return [
        pytest.param(
            name, marks=pytest.mark.xfail(reason=_QUARANTINED[name], strict=True)
        )
        if name in _QUARANTINED
        else name
        for name in names
    ]


@pytest.mark.parametrize("tutorial", _tutorial_names())
def test_tutorial_golden(tutorial):
    """Deterministic solve of a tutorial must match its pinned reference."""
    yaml_path = os.path.join(CASE_STUDIES_DIR, tutorial, "config.yaml")
    reference_path = os.path.join(GOLDEN_DIR, f"{tutorial}.npz")
    assert os.path.exists(reference_path), (
        f"No golden reference for {tutorial}. Generate it with "
        f"`uv run python 04_tests/golden/generate_references.py` and commit it."
    )

    with np.load(reference_path) as reference:
        # Fixture/reference drift guard: if config.yaml changed since the
        # reference was generated, fail immediately with a clear message
        # instead of surfacing as a numeric mismatch (or worse, silently
        # comparing against a stale fixture). See the T04 FoldedNormal
        # staleness incident (af2b5f9 added a category without regenerating
        # the reference; c15c547 fixed it after main was already broken).
        if "meta/config_hash" in reference.files:
            current_hash = config_file_hash(yaml_path)
            ref_hash = str(reference["meta/config_hash"])
            assert current_hash == ref_hash, (
                f"{tutorial}: config.yaml has changed since its golden reference "
                f"was generated. Regenerate with "
                f"`uv run python 04_tests/golden/generate_references.py`, verify "
                f"the diff is intentional, and commit it in its own "
                f"`test(golden)` commit."
            )

        actual, solver_info = collect_full_results(yaml_path)

        assert solver_info.get("converged") is True, (
            f"{tutorial}: solver did not converge"
        )
        assert bool(reference["meta/converged"]) is True
        ref_keys = {
            k for k in reference.files if not k.startswith("meta/")
        }
        assert set(actual) == ref_keys, (
            f"{tutorial}: result keys changed.\n"
            f"  missing: {sorted(ref_keys - set(actual))}\n"
            f"  extra:   {sorted(set(actual) - ref_keys)}"
        )
        for key in sorted(ref_keys):
            np.testing.assert_allclose(
                actual[key],
                reference[key],
                rtol=1e-9,
                atol=1e-12,
                err_msg=f"{tutorial}: {key} deviates from golden reference",
            )


@pytest.mark.skipif(
    not os.path.exists(TEMPLATE_XLSM), reason="template .xlsm not present"
)
def test_template_excel_smoke():
    """Excel-path smoke test: template workbook runs and converges."""
    import pandas as pd

    import config
    import data_loader
    import system_setup
    from engine import solver

    input_data = pd.read_excel(
        TEMPLATE_XLSM,
        sheet_name=None,
        header=0,
        engine="openpyxl",
        na_values=["N.A.", "NA", "n/a"],
        decimal=",",
    )
    config_obj = config.load_configuration(TEMPLATE_XLSM)
    dims = config.extract_workflow_dimensions(config_obj, input_data)

    model_classification, index_table = system_setup.define_model_scope(
        dims["start_year"],
        dims["end_year"],
        dims["elements"],
        dims["regions"],
        dims["goods"],
        dims["materials"],
        dims["processes"],
    )
    mfa_system = system_setup.initialize_mfa_system(
        model_classification, index_table, unit=config.resolve_unit(config_obj)
    )
    mfa_system, all_excel_data = system_setup.load_and_define_processes(
        mfa_system, input_data, data_loader
    )
    mfa_system, _, flow_tc_map, process_logic_map = (
        system_setup.define_flows_and_parameters(mfa_system, all_excel_data)
    )
    time_vector = mfa_system.IndexTable.Classification["Time"].Items
    mfa_system.ParameterDict.update(
        data_loader.load_tc_parameters(
            all_excel_data, mfa_system.Elements, time_vector
        )
    )
    params = data_loader.load_all_parameters(
        all_excel_data, config_obj, elements=mfa_system.Elements
    )
    data_loader.register_flow_cap_parameters(mfa_system, params["flow_cap"])

    fomp_params = params["fomp"]
    lfg_params = params["lfg"]
    if process_logic_map:
        fomp_params = {
            pid: p
            for pid, p in fomp_params.items()
            if process_logic_map.get(pid) == "FOMP"
        }
        lfg_params = {
            pid: p
            for pid, p in lfg_params.items()
            if process_logic_map.get(pid) == "LFG"
        }

    _, _, solver_info = solver.run_mfa_calculation(
        mfa_system,
        params["dsm"],
        fomp_params,
        config_obj,
        flow_tc_map=flow_tc_map,
        process_logic_map=process_logic_map,
        lfg_params=lfg_params,
        bom_params=params["bom"],
        flow_cap_params=params["flow_cap"],
    )
    assert solver_info.get("converged") is True
