"""Regression tests for the Windows BioDYM launcher helpers."""

from BioDYM_Launcher import build_service_args, parse_listener_pid, read_version


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
    assert read_version() != "unknown"
