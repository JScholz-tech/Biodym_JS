# -*- coding: utf-8 -*-
"""
Pytest Configuration File

This file is automatically loaded by pytest and sets up the necessary
paths and configurations for all tests in the test suite.
"""

import os
import sys

# Get the test directory path
test_dir = os.path.dirname(os.path.abspath(__file__))

# Navigate to the project root directory
project_root = os.path.dirname(test_dir)

# Add project root first so `app` resolves to the real FastAPI package,
# not to any 04_tests/app/ subdirectory.
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Add the source root, then delegate the ODYM/bioDYM framework module dirs to the
# shared helper. (src_path must be on sys.path before `bootstrap` is importable.)
src_path = os.path.join(project_root, "02_src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from bootstrap import setup_paths

setup_paths(project_root)

# Add engine module to path (for submodules)
engine_path = os.path.join(src_path, "engine")
if engine_path not in sys.path:
    sys.path.insert(0, engine_path)

print("Test configuration loaded:")
print(f"  - project_root: {project_root}")
print(f"  - src_path: {src_path}")
print(f"  - engine_path: {engine_path}")