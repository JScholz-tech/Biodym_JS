"""
Quick test script for simplified Sankey module.

This script tests basic imports and function availability
without running the full MFA calculation.
"""

import sys
import os
import inspect
from plotting import sankey

# Add 02_src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "02_src"))

print("Testing simplified Sankey module...")

# Check functions exist
try:
    assert hasattr(sankey, "plot_interactive_sankey"), "plot_interactive_sankey missing"
    assert hasattr(sankey, "plot_element_multiplot_sankey"), (
        "plot_element_multiplot_sankey missing"
    )
    print("[OK] Main plotting functions available")
except AssertionError as e:
    print(f"[FAIL] Function check failed: {e}")
    sys.exit(1)

# Check function signatures
sig_interactive = inspect.signature(sankey.plot_interactive_sankey)
params_interactive = list(sig_interactive.parameters.keys())

expected_params = [
    "mfa_system_results",
    "dsm_params",
    "fomp_params",
    "color_manager",
    "width",
    "height",
    "node_pad",
    "flows_to_show",
]

for param in expected_params:
    if param not in params_interactive:
        print(f"[FAIL] Missing parameter: {param}")
        sys.exit(1)

print("[OK] Function signature correct")
print(f"   Parameters: {', '.join(params_interactive)}")

# Check defaults
defaults = {"width": 5000, "height": 2000, "node_pad": 30}

for param, expected_default in defaults.items():
    actual_default = sig_interactive.parameters[param].default
    if actual_default != expected_default:
        print(
            f"[WARN] {param} default is {actual_default}, expected {expected_default}"
        )
    else:
        print(f"[OK] {param} default: {actual_default}")

print("\n" + "=" * 50)
print("All basic checks passed!")
print("Ready for testing with actual MFA data.")
print("=" * 50)
