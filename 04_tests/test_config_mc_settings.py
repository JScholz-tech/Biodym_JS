# -*- coding: utf-8 -*-
"""Tests that MC_Seed / solver settings flow from YAML config into the engine."""

import config
from engine.mc_simulation import _resolve_mc_seed


def _write_yaml(tmp_path, model_extra=None):
    """Write a minimal case-study YAML; model_extra is a dict merged into model."""
    lines = [
        "schema_version: '1.0'",
        "name: seed_test",
        "model:",
        "  start_year: 2025",
        "  end_year: 2030",
        "  elements: [material, WC, DM, TC]",
        "  unit_of_measurement: Mg",
        "  run_monte_carlo: true",
        "  mc_iterations: 50",
    ]
    for key, value in (model_extra or {}).items():
        lines.append(f"  {key}: {value}")
    lines += ["processes: []", "flows: []", ""]
    p = tmp_path / "config.yaml"
    p.write_text("\n".join(lines), encoding="utf-8")
    return str(p)


def test_yaml_without_settings_uses_defaults(tmp_path):
    cfg = config.load_config_from_yaml(_write_yaml(tmp_path))
    # Defaults surface through the engine resolver
    assert _resolve_mc_seed(cfg) == 42
    assert getattr(cfg, "SOLVER_STRICT") is False
    assert int(getattr(cfg, "SOLVER_MAX_ITERATIONS")) == 30


def test_yaml_integer_seed_is_read(tmp_path):
    yaml_path = _write_yaml(
        tmp_path,
        {"mc_seed": 1234, "solver_strict": "true", "solver_max_iterations": 75},
    )
    cfg = config.load_config_from_yaml(yaml_path)
    assert _resolve_mc_seed(cfg) == 1234
    assert bool(getattr(cfg, "SOLVER_STRICT")) is True
    assert int(getattr(cfg, "SOLVER_MAX_ITERATIONS")) == 75


def test_yaml_random_seed_resolves_to_none(tmp_path):
    yaml_path = _write_yaml(tmp_path, {"mc_seed": "random"})
    cfg = config.load_config_from_yaml(yaml_path)
    assert _resolve_mc_seed(cfg) is None  # unseeded → non-reproducible


def test_config_object_exposes_uppercase_aliases(tmp_path):
    """create_config_object builds MC_SEED etc. from the MC_Seed dict key."""
    yaml_path = _write_yaml(tmp_path, {"mc_seed": 7})
    cfg = config.load_config_from_yaml(yaml_path)
    assert hasattr(cfg, "MC_SEED")
    assert hasattr(cfg, "SOLVER_STRICT")
    assert hasattr(cfg, "SOLVER_MAX_ITERATIONS")
