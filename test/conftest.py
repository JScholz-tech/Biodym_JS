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

# Add src directory to path
src_path = os.path.join(project_root, "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Add ODYM framework to path
odym_path = os.path.join(
    project_root, "framework", "ODYM-master_20241127", "odym", "modules"
)
if odym_path not in sys.path:
    sys.path.insert(0, odym_path)

# Add bioDYM add-on to path
biodym_addon_path = os.path.join(
    project_root, "framework", "bioDYM_add-on", "modules"
)
if biodym_addon_path not in sys.path:
    sys.path.insert(0, biodym_addon_path)

# Add engine module to path (for submodules)
engine_path = os.path.join(src_path, "engine")
if engine_path not in sys.path:
    sys.path.insert(0, engine_path)

print(f"Test configuration loaded:")
print(f"  - src_path: {src_path}")
print(f"  - odym_path: {odym_path}")
print(f"  - biodym_addon_path: {biodym_addon_path}")
print(f"  - engine_path: {engine_path}")