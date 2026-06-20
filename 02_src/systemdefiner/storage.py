from __future__ import annotations

import threading
from pathlib import Path

import yaml

from systemdefiner.models.config_schema import CaseStudyConfig

CASE_STUDIES_DIR = Path("01_data/01_input/case_studies")
_locks: dict[str, threading.Lock] = {}
_locks_lock = threading.Lock()


class CaseStudyNotFound(Exception):
    """Raised when a case study does not exist or its name is unsafe."""

    def __init__(self, name: str):
        self.name = name
        super().__init__(f"Case study '{name}' not found")


def _lock_for(name: str) -> threading.Lock:
    with _locks_lock:
        if name not in _locks:
            _locks[name] = threading.Lock()
        return _locks[name]


def _is_safe_name(name: str) -> bool:
    """Reject names that could escape CASE_STUDIES_DIR (path traversal)."""
    if not name or name in (".", ".."):
        return False
    if "/" in name or "\\" in name or "\0" in name:
        return False
    base = CASE_STUDIES_DIR.resolve()
    try:
        target = (base / name).resolve()
    except (OSError, ValueError):
        return False
    return target.parent == base


def _config_path(name: str) -> Path:
    if not _is_safe_name(name):
        raise ValueError(f"Invalid case-study name: {name!r}")
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
    if not _is_safe_name(name):
        raise CaseStudyNotFound(name)
    path = _config_path(name)
    if not path.exists():
        raise CaseStudyNotFound(name)
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


def clone_case_study(src: str, dst: str) -> None:
    """Copy a case study (config + diagram) to a new name. Raises on bad input."""
    if not _is_safe_name(src) or not _is_safe_name(dst):
        raise ValueError("Invalid case-study name.")
    if not case_study_exists(src):
        raise CaseStudyNotFound(src)
    if case_study_exists(dst):
        raise ValueError(f"Case study '{dst}' already exists.")
    cfg = load_case_study(src)
    cfg.name = dst
    save_case_study(cfg)
    diagram = diagram_path(src)
    if diagram:
        (CASE_STUDIES_DIR / dst).mkdir(parents=True, exist_ok=True)
        (CASE_STUDIES_DIR / dst / diagram.name).write_bytes(diagram.read_bytes())


def delete_case_study(name: str) -> None:
    import shutil
    if not _is_safe_name(name):
        raise ValueError(f"Invalid case-study name: {name!r}")
    path = CASE_STUDIES_DIR / name
    if path.exists():
        shutil.rmtree(path)
    with _locks_lock:
        _locks.pop(name, None)


def case_study_exists(name: str) -> bool:
    if not _is_safe_name(name):
        return False
    return _config_path(name).exists()


# ── Model diagram (user-uploaded image, e.g. a draw.io PNG) ──────────────────
_DIAGRAM_EXTS = {".png", ".jpg", ".jpeg", ".svg", ".gif", ".webp"}


def diagram_path(name: str) -> Path | None:
    """Return the stored diagram image for a study, or None if there isn't one."""
    if not _is_safe_name(name):
        return None
    folder = CASE_STUDIES_DIR / name
    if not folder.is_dir():
        return None
    for p in sorted(folder.glob("diagram.*")):
        if p.suffix.lower() in _DIAGRAM_EXTS:
            return p
    return None


def save_diagram(name: str, filename: str, content: bytes) -> None:
    """Store (replace) the study's diagram image. Raises ValueError on bad input."""
    if not _is_safe_name(name):
        raise ValueError(f"Invalid case-study name: {name!r}")
    ext = Path(filename or "").suffix.lower()
    if ext not in _DIAGRAM_EXTS:
        raise ValueError(f"Unsupported image type '{ext or '(none)'}'. "
                         f"Allowed: {', '.join(sorted(_DIAGRAM_EXTS))}")
    folder = CASE_STUDIES_DIR / name
    folder.mkdir(parents=True, exist_ok=True)
    for p in folder.glob("diagram.*"):   # drop any previous diagram
        p.unlink()
    (folder / f"diagram{ext}").write_bytes(content)


def delete_diagram(name: str) -> None:
    if not _is_safe_name(name):
        return
    folder = CASE_STUDIES_DIR / name
    if folder.is_dir():
        for p in folder.glob("diagram.*"):
            p.unlink()
