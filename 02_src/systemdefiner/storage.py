from __future__ import annotations

import threading
from pathlib import Path

import yaml

from systemdefiner.models.config_schema import CaseStudyConfig

CASE_STUDIES_DIR = Path("01_data/01_input/case_studies")
_locks: dict[str, threading.Lock] = {}
_locks_lock = threading.Lock()


def _lock_for(name: str) -> threading.Lock:
    with _locks_lock:
        if name not in _locks:
            _locks[name] = threading.Lock()
        return _locks[name]


def _config_path(name: str) -> Path:
    return CASE_STUDIES_DIR / name / "config.yaml"


def list_case_studies() -> list[dict]:
    CASE_STUDIES_DIR.mkdir(parents=True, exist_ok=True)
    results = []
    for folder in sorted(CASE_STUDIES_DIR.iterdir()):
        if not folder.is_dir():
            continue
        cfg_file = folder / "config.yaml"
        if not cfg_file.exists():
            continue
        try:
            cfg = load_case_study(folder.name)
            results.append({
                "name": folder.name,
                "elements": ", ".join(cfg.model.elements),
                "processes": len(cfg.processes),
                "flows": len(cfg.flows),
                "modified": cfg_file.stat().st_mtime,
            })
        except Exception:
            results.append({
                "name": folder.name,
                "elements": "—",
                "processes": "?",
                "flows": "?",
                "modified": cfg_file.stat().st_mtime,
            })
    return results


def load_case_study(name: str) -> CaseStudyConfig:
    path = _config_path(name)
    with _lock_for(name):
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    raw.setdefault("name", name)
    return CaseStudyConfig.model_validate(raw)


def save_case_study(config: CaseStudyConfig) -> None:
    path = _config_path(config.name)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = config.model_dump(mode="json")
    text = yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)
    with _lock_for(config.name):
        path.write_text(text, encoding="utf-8")


def delete_case_study(name: str) -> None:
    import shutil
    path = CASE_STUDIES_DIR / name
    if path.exists():
        shutil.rmtree(path)
    with _locks_lock:
        _locks.pop(name, None)


def case_study_exists(name: str) -> bool:
    return _config_path(name).exists()
