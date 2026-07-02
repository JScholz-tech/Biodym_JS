# -*- coding: utf-8 -*-
"""
Regenerate the golden reference files for test_golden_regression.py.

Runs every tracked tutorial case study (01_data/01_input/case_studies/T??_*)
through the exact same pipeline the regression test uses (golden_utils) and
stores the complete numerical result per tutorial as 04_tests/golden/<name>.npz.

Regenerating references is an intentional act — only do it when a numerical
change is expected and reviewed (e.g. the seeded-MC migration), and commit the
resulting .npz diffs in their own `chore(tests)` commit.

Usage:
    uv run python 04_tests/golden/generate_references.py
"""

import glob
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_tests_dir = os.path.dirname(_here)
_project_root = os.path.dirname(_tests_dir)

sys.path.insert(0, _project_root)
sys.path.insert(0, os.path.join(_project_root, "02_src"))
from bootstrap import setup_paths  # noqa: E402

setup_paths(_project_root)
sys.path.insert(0, _tests_dir)

import numpy as np  # noqa: E402

from golden_utils import collect_result_arrays, run_case_study_yaml  # noqa: E402

CASE_STUDIES_DIR = os.path.join(
    _project_root, "01_data", "01_input", "case_studies"
)


def tutorial_yaml_paths():
    """All tracked tutorial configs (T01…), sorted by tutorial number."""
    pattern = os.path.join(CASE_STUDIES_DIR, "T[0-9][0-9]_*", "config.yaml")
    return sorted(glob.glob(pattern))


def main():
    failures = []
    for yaml_path in tutorial_yaml_paths():
        name = os.path.basename(os.path.dirname(yaml_path))
        print(f"\n{'=' * 60}\n>>> {name}\n{'=' * 60}")
        try:
            mfa_system, _, solver_info = run_case_study_yaml(yaml_path)
        except Exception as exc:  # keep going — report all failures at the end
            failures.append((name, repr(exc)))
            print(f">>> FAILED: {exc!r}")
            continue

        arrays = collect_result_arrays(mfa_system)
        arrays["meta/converged"] = np.array(bool(solver_info.get("converged")))
        out_path = os.path.join(_here, f"{name}.npz")
        np.savez_compressed(out_path, **arrays)
        print(
            f">>> saved {out_path} "
            f"({len(arrays) - 1} arrays, converged={solver_info.get('converged')})"
        )

    print(f"\n{'=' * 60}")
    if failures:
        print("Tutorials that could NOT be pinned (fix or xfail in the test):")
        for name, err in failures:
            print(f"  - {name}: {err}")
    else:
        print("All tutorials pinned successfully.")


if __name__ == "__main__":
    main()
