"""Platform-neutral helpers shared by the BioDYM Windows launcher and tests."""

from pathlib import Path
from collections.abc import Mapping
import os
import tempfile
import tomllib


def read_version(root: Path) -> str:
    try:
        with open(root / "pyproject.toml", "rb") as handle:
            return tomllib.load(handle)["project"]["version"]
    except (OSError, KeyError, tomllib.TOMLDecodeError):
        return "unknown"


def build_service_args(key: str, port: int) -> list[str]:
    if key == "dashboard":
        return [
            "-m",
            "voila",
            "01_BioDYM_Dashboard.ipynb",
            f"--port={port}",
            "--no-browser",
        ]
    if key == "systemdefiner":
        return [
            "-m",
            "uvicorn",
            "systemdefiner.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ]
    raise KeyError(key)


def parse_listener_pid(netstat_output: str, port: int) -> int | None:
    """Extract the listening PID for a local TCP port from Windows netstat."""
    for line in netstat_output.splitlines():
        columns = line.split()
        if len(columns) < 5 or columns[0].upper() != "TCP":
            continue
        local, state, pid_text = columns[1], columns[3].upper(), columns[4]
        if state != "LISTENING" or not local.endswith(f":{port}"):
            continue
        try:
            return int(pid_text)
        except ValueError:
            continue
    return None


def build_service_environment(
    runtime_dir: Path, base_environment: Mapping[str, str]
) -> tuple[dict[str, str], tuple[Path, ...]]:
    """Return an isolated, writable Jupyter environment for Voilà."""
    jupyter_root = runtime_dir / "jupyter"
    directories = {
        "JUPYTER_CONFIG_DIR": jupyter_root / "config",
        "JUPYTER_DATA_DIR": jupyter_root / "data",
        "JUPYTER_RUNTIME_DIR": jupyter_root / "runtime",
        "IPYTHONDIR": jupyter_root / "ipython",
        "MPLCONFIGDIR": runtime_dir / "matplotlib",
    }
    environment = dict(base_environment)
    environment.update({name: str(path) for name, path in directories.items()})
    return environment, tuple(directories.values())


def find_unwritable_directories(paths: tuple[Path, ...]) -> tuple[Path, ...]:
    """Return directories where BioDYM cannot create and remove a small file."""
    failures = []
    for path in paths:
        test_path = None
        try:
            path.mkdir(parents=True, exist_ok=True)
            descriptor, name = tempfile.mkstemp(prefix=".biodym_write_test_", dir=path)
            os.close(descriptor)
            test_path = Path(name)
            test_path.unlink()
        except OSError:
            failures.append(path)
            if test_path and test_path.exists():
                try:
                    test_path.unlink()
                except OSError:
                    pass
    return tuple(failures)


__all__ = [
    "build_service_args",
    "build_service_environment",
    "find_unwritable_directories",
    "parse_listener_pid",
    "read_version",
]
