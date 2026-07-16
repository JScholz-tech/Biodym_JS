"""Regression tests for the platform-neutral BioDYM launcher helpers."""

from pathlib import Path

from launcher_utils import (
    build_service_args,
    build_service_environment,
    find_unwritable_directories,
    parse_listener_pid,
    read_version,
)


ROOT = Path(__file__).resolve().parents[1]


def test_parse_listener_pid_ipv4():
    output = """
      TCP    127.0.0.1:8866       0.0.0.0:0       LISTENING       1234
      TCP    127.0.0.1:8001       0.0.0.0:0       LISTENING       5678
    """
    assert parse_listener_pid(output, 8866) == 1234
    assert parse_listener_pid(output, 8001) == 5678


def test_parse_listener_pid_ipv6_and_missing():
    output = "TCP    [::1]:8867       [::]:0       LISTENING       4321"
    assert parse_listener_pid(output, 8867) == 4321
    assert parse_listener_pid(output, 8866) is None


def test_dashboard_command_uses_selected_port():
    args = build_service_args("dashboard", 8867)
    assert args[:2] == ["-m", "voila"]
    assert "--port=8867" in args


def test_systemdefiner_command_uses_selected_port():
    args = build_service_args("systemdefiner", 8002)
    assert args[:3] == ["-m", "uvicorn", "systemdefiner.main:app"]
    assert args[-2:] == ["--port", "8002"]


def test_launcher_reads_project_version():
    assert read_version(ROOT) != "unknown"


def test_service_environment_isolates_jupyter_files(tmp_path):
    environment, directories = build_service_environment(
        tmp_path, {"EXISTING": "preserved", "JUPYTER_DATA_DIR": "unusable"}
    )

    assert environment["EXISTING"] == "preserved"
    assert environment["JUPYTER_DATA_DIR"] == str(tmp_path / "jupyter" / "data")
    assert environment["JUPYTER_CONFIG_DIR"] == str(tmp_path / "jupyter" / "config")
    assert environment["JUPYTER_RUNTIME_DIR"] == str(tmp_path / "jupyter" / "runtime")
    assert environment["IPYTHONDIR"] == str(tmp_path / "jupyter" / "ipython")
    assert environment["MPLCONFIGDIR"] == str(tmp_path / "matplotlib")
    assert len(directories) == 5


def test_writable_directory_probe(tmp_path):
    writable = tmp_path / "writable"
    not_a_directory = tmp_path / "blocked"
    not_a_directory.write_text("file occupying directory path", encoding="utf-8")

    assert find_unwritable_directories((writable,)) == ()
    assert find_unwritable_directories((writable, not_a_directory)) == (
        not_a_directory,
    )
