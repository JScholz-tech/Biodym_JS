"""Platform-neutral helpers shared by the BioDYM Windows launcher and tests."""

from pathlib import Path
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


__all__ = ["build_service_args", "parse_listener_pid", "read_version"]
