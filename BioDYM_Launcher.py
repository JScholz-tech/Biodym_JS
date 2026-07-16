"""Windows desktop launcher for an existing BioDYM installation."""

from __future__ import annotations

import hashlib
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
import webbrowser
import ctypes
from ctypes import wintypes
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

from launcher_utils import build_service_args, parse_listener_pid, read_version

ROOT = Path(__file__).resolve().parent
INSTALL_ID = hashlib.sha256(str(ROOT).casefold().encode()).hexdigest()[:12]
LOCAL_DATA = Path(os.environ.get("LOCALAPPDATA", tempfile.gettempdir()))
STATE_ROOT = LOCAL_DATA / "BioDYM Launcher"
RUNTIME_DIR = STATE_ROOT / INSTALL_ID
LOG_DIR = RUNTIME_DIR / "logs"
STATE_FILE = RUNTIME_DIR / "services.json"
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
NEW_GROUP = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)

SERVICES = {
    "dashboard": {
        "label": "BioDYM Dashboard",
        "port": 8866,
        "markers": ("biodym", "voila"),
    },
    "systemdefiner": {
        "label": "SystemDefiner",
        "port": 8001,
        "markers": ("biodym", "systemdefiner"),
    },
}


VERSION = read_version(ROOT)


class Launcher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("BioDYM Launcher")
        self.geometry("600x415")
        self.minsize(550, 390)
        self.processes: dict[str, subprocess.Popen] = {}
        self.logs = {}
        self.cancel_events = {key: threading.Event() for key in SERVICES}
        self.pids, self.process_tokens, self.active_ports = self.load_owned_pids()
        self.states = {key: tk.StringVar(value="Checking...") for key in SERVICES}
        self.summary = tk.StringVar(value="Checking the BioDYM installation...")
        self.start_buttons = {}
        self.stop_buttons = {}
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.build_ui()
        self.after(100, self.initial_check)
        self.after(1000, self.refresh)

    def build_ui(self):
        frame = ttk.Frame(self, padding=22)
        frame.pack(fill="both", expand=True)
        ttk.Label(
            frame,
            text=f"BioDYM {VERSION}",
            font=("Segoe UI", 22, "bold"),
        ).pack(anchor="w")
        ttk.Label(
            frame,
            text="Start BioDYM without a terminal. The tools open in your browser.",
        ).pack(anchor="w", pady=(2, 18))
        ttk.Label(
            frame,
            text=f"Installation: {ROOT}",
            foreground="#555555",
            wraplength=540,
        ).pack(anchor="w", pady=(0, 12))
        for key, service in SERVICES.items():
            card = ttk.LabelFrame(frame, text=service["label"], padding=12)
            card.pack(fill="x", pady=5)
            ttk.Label(card, textvariable=self.states[key], width=14).pack(side="left")
            start = ttk.Button(card, text="Start / Open", command=lambda k=key: self.start(k))
            start.pack(side="left", padx=5)
            stop = ttk.Button(card, text="Stop", command=lambda k=key: self.stop(k))
            stop.pack(side="left")
            self.start_buttons[key], self.stop_buttons[key] = start, stop
        buttons = ttk.Frame(frame)
        buttons.pack(fill="x", pady=(14, 5))
        ttk.Button(buttons, text="Start both", command=self.start_all).pack(side="left")
        ttk.Button(buttons, text="Stop all", command=self.stop_all).pack(side="left", padx=6)
        ttk.Button(buttons, text="Open logs", command=self.open_logs).pack(side="right")
        ttk.Label(frame, textvariable=self.summary, wraplength=490).pack(anchor="w", pady=(8, 0))

    def initial_check(self):
        missing = [
            name
            for name in ("pyproject.toml", "01_BioDYM_Dashboard.ipynb", "02_src")
            if not (ROOT / name).exists()
        ]
        if missing:
            self.summary.set("Launcher files are not inside a complete BioDYM folder.")
            messagebox.showerror(
                "Incomplete BioDYM folder",
                "Place all launcher files in the main BioDYM folder. Missing: "
                + ", ".join(missing),
            )
        else:
            self.summary.set("Choose an application to start.")
        self.refresh_service_states()

    @staticmethod
    def port_open(port):
        with socket.socket() as sock:
            sock.settimeout(0.2)
            return sock.connect_ex(("127.0.0.1", port)) == 0

    @staticmethod
    def process_created(pid):
        """Return the Windows process creation token, or None if it is gone."""
        try:
            kernel32 = ctypes.windll.kernel32
            kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
            kernel32.OpenProcess.restype = wintypes.HANDLE
            kernel32.GetProcessTimes.argtypes = [
                wintypes.HANDLE,
                ctypes.POINTER(wintypes.FILETIME),
                ctypes.POINTER(wintypes.FILETIME),
                ctypes.POINTER(wintypes.FILETIME),
                ctypes.POINTER(wintypes.FILETIME),
            ]
            kernel32.GetProcessTimes.restype = wintypes.BOOL
            kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
            handle = kernel32.OpenProcess(0x1000, False, int(pid))
        except (AttributeError, TypeError, ValueError):
            return None
        if not handle:
            return None
        creation, exit_time = wintypes.FILETIME(), wintypes.FILETIME()
        kernel_time, user_time = wintypes.FILETIME(), wintypes.FILETIME()
        try:
            if not kernel32.GetProcessTimes(
                handle,
                ctypes.byref(creation),
                ctypes.byref(exit_time),
                ctypes.byref(kernel_time),
                ctypes.byref(user_time),
            ):
                return None
            return (creation.dwHighDateTime << 32) | creation.dwLowDateTime
        finally:
            kernel32.CloseHandle(handle)

    @classmethod
    def pid_running(cls, pid):
        return cls.process_created(pid) is not None

    def load_owned_pids(self):
        try:
            stored = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return {}, {}, {}
        records = stored.get("services", stored) if isinstance(stored, dict) else {}
        owned, tokens, ports = {}, {}, {}
        for key, value in records.items():
            if key not in SERVICES or not isinstance(value, dict):
                continue
            pid, expected = value.get("pid"), value.get("created")
            if not isinstance(pid, int) or not isinstance(expected, int):
                continue
            if self.process_created(pid) == expected:
                owned[key], tokens[key] = pid, expected
                port = value.get("port", SERVICES[key]["port"])
                ports[key] = port if isinstance(port, int) else SERVICES[key]["port"]
        return owned, tokens, ports

    def save_owned_pids(self):
        try:
            RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
            temporary = STATE_FILE.with_suffix(".tmp")
            services = {
                key: {
                    "pid": pid,
                    "created": self.process_tokens.get(key),
                    "port": self.active_ports.get(key, SERVICES[key]["port"]),
                }
                for key, pid in self.pids.items()
                if self.process_tokens.get(key) is not None
            }
            payload = {
                "install_root": str(ROOT),
                "version": VERSION,
                "services": services,
            }
            temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            temporary.replace(STATE_FILE)
        except OSError:
            # Service operation still works during this session even if Windows
            # prevents persistent state from being saved.
            pass

    def owned_running(self, key):
        pid = self.pids.get(key)
        token = self.process_tokens.get(key)
        if pid and token and self.process_created(pid) == token:
            return True
        if pid:
            self.pids.pop(key, None)
            self.process_tokens.pop(key, None)
            self.processes.pop(key, None)
            self.active_ports.pop(key, None)
            log = self.logs.pop(key, None)
            if log:
                log.close()
            self.save_owned_pids()
        return False

    @staticmethod
    def listener_pid(port):
        try:
            result = subprocess.run(
                ["netstat", "-ano", "-p", "tcp"],
                capture_output=True,
                text=True,
                creationflags=NO_WINDOW,
                timeout=5,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            return None
        return parse_listener_pid(result.stdout, port)

    @staticmethod
    def process_name(pid):
        try:
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {int(pid)}", "/FO", "CSV", "/NH"],
                capture_output=True,
                text=True,
                creationflags=NO_WINDOW,
                timeout=5,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            return ""
        match = re.match(r'"([^"]+)"', result.stdout.strip())
        return match.group(1).casefold() if match else ""

    @staticmethod
    def page_matches_service(key, port):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}", timeout=3) as response:
                content = response.read(250_000).decode("utf-8", errors="ignore").casefold()
        except (OSError, urllib.error.URLError, TimeoutError):
            return False
        markers = SERVICES[key]["markers"]
        return markers[0] in content and any(marker in content for marker in markers[1:])

    @staticmethod
    def http_status(port):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}", timeout=3) as response:
                return response.status
        except urllib.error.HTTPError as exc:
            return exc.code
        except (OSError, urllib.error.URLError, TimeoutError):
            return None

    def registered_instance(self, key, pid, token):
        if not STATE_ROOT.exists():
            return None
        for path in STATE_ROOT.glob("*/services.json"):
            try:
                stored = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError, TypeError):
                continue
            records = stored.get("services", stored) if isinstance(stored, dict) else {}
            record = records.get(key, {})
            if record.get("pid") == pid and record.get("created") == token:
                return {
                    "root": stored.get("install_root", "an older BioDYM folder"),
                    "version": stored.get("version", "unknown"),
                }
        return None

    def identify_listener(self, key, port):
        pid = self.listener_pid(port)
        if not pid:
            return None
        token = self.process_created(pid)
        registered = self.registered_instance(key, pid, token)
        if registered:
            return {"pid": pid, "token": token, "registered": True, **registered}
        python_names = {"python.exe", "pythonw.exe", "uv.exe", "voila.exe"}
        if self.process_name(pid) in python_names and self.page_matches_service(key, port):
            return {
                "pid": pid,
                "token": token,
                "registered": False,
                "root": "another or older BioDYM installation",
                "version": "unknown",
            }
        return None

    def next_free_port(self, preferred):
        for port in range(preferred + 1, preferred + 100):
            if not self.port_open(port):
                return port
        return None

    def start(self, key):
        service = SERVICES[key]
        label = service["label"]
        if self.owned_running(key):
            port = self.active_ports.get(key, service["port"])
            if self.port_open(port):
                webbrowser.open(f"http://127.0.0.1:{port}")
                self.summary.set(f"{label} is already running.")
            else:
                self.summary.set(f"{label} is already starting.")
            return
        port = service["port"]
        if self.port_open(port):
            port = self.resolve_port_conflict(key, port)
            if port is None:
                self.refresh_service_states()
                return
        self.cancel_events[key].clear()
        log = self.open_service_log(key)
        try:
            process = subprocess.Popen(
                [sys.executable, *build_service_args(key, port)],
                cwd=ROOT,
                stdout=log,
                stderr=subprocess.STDOUT,
                creationflags=NO_WINDOW | NEW_GROUP,
            )
        except OSError as exc:
            log.close()
            messagebox.showerror("BioDYM cannot start", str(exc))
            return
        self.processes[key], self.logs[key], self.pids[key] = process, log, process.pid
        self.process_tokens[key] = self.process_created(process.pid)
        self.active_ports[key] = port
        self.save_owned_pids()
        self.states[key].set("Starting...")
        self.start_buttons[key].state(["disabled"])
        self.stop_buttons[key].state(["!disabled"])
        port_note = f" on port {port}" if port != service["port"] else ""
        self.summary.set(f"Starting {label}{port_note}; this may take a moment...")
        threading.Thread(
            target=self.wait_ready,
            args=(key, process.pid, self.cancel_events[key]),
            daemon=True,
        ).start()

    def resolve_port_conflict(self, key, preferred_port):
        service = SERVICES[key]
        label = service["label"]
        existing = self.identify_listener(key, preferred_port)
        if existing:
            location = existing["root"]
            version = existing["version"]
            answer = messagebox.askyesnocancel(
                "Another BioDYM is already running",
                f"An existing {label} is using port {preferred_port}.\n\n"
                f"Version: {version}\nLocation: {location}\n\n"
                "Yes: stop it and start this installation.\n"
                "No: open the existing application.\n"
                "Cancel: do nothing.",
            )
            if answer is None:
                return None
            if not answer:
                webbrowser.open(f"http://127.0.0.1:{preferred_port}")
                self.summary.set(f"Opened the existing {label}.")
                return None
            if not existing["token"] or self.process_created(existing["pid"]) != existing["token"]:
                messagebox.showwarning(
                    "Application changed",
                    "The process using the port changed before it could be stopped. "
                    "No process was terminated.",
                )
                return None
            self.terminate_process_tree(existing["pid"])
            for _ in range(50):
                if not self.port_open(preferred_port):
                    self.summary.set(f"Stopped the existing {label}.")
                    return preferred_port
                time.sleep(0.1)
        alternative = self.next_free_port(preferred_port)
        if not alternative:
            messagebox.showerror(
                f"Cannot start {label}",
                "No available local port was found. Close an existing application and try again.",
            )
            return None
        if messagebox.askyesno(
            f"Port {preferred_port} is unavailable",
            f"Another application is using port {preferred_port}.\n\n"
            f"Start {label} safely on port {alternative} instead?",
        ):
            return alternative
        return None

    def open_service_log(self, key):
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        path = LOG_DIR / f"{key}.log"
        backup = LOG_DIR / f"{key}.previous.log"
        if path.exists() and path.stat().st_size > 2_000_000:
            if backup.exists():
                backup.unlink()
            path.replace(backup)
        log = open(path, "a", encoding="utf-8", buffering=1)
        log.write(f"\n--- Starting {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
        return log

    def wait_ready(self, key, pid, cancel_event):
        port = self.active_ports.get(key, SERVICES[key]["port"])
        server_errors = 0
        for _ in range(120):
            if cancel_event.is_set() or self.pids.get(key) != pid:
                return
            process = self.processes.get(key)
            if process and process.poll() is not None:
                self.after(0, lambda: self.start_failed(key, pid))
                return
            if self.port_open(port):
                status = self.http_status(port)
                if status is not None and status < 400:
                    self.after(0, lambda: self.ready(key, pid))
                    return
                if status is not None and status >= 500:
                    server_errors += 1
                    if server_errors >= 3:
                        detail = (
                            f"{SERVICES[key]['label']} returned HTTP {status} while "
                            "loading. The notebook or application failed during "
                            "startup."
                        )
                        self.after(0, lambda d=detail: self.start_failed(key, pid, d))
                        return
            time.sleep(0.5)
        self.after(0, lambda: self.start_failed(key, pid, "Startup timed out."))

    def ready(self, key, pid):
        if self.pids.get(key) != pid or self.cancel_events[key].is_set():
            return
        service = SERVICES[key]
        port = self.active_ports.get(key, service["port"])
        state = "Running" if port == service["port"] else f"Running :{port}"
        self.states[key].set(state)
        self.start_buttons[key].state(["!disabled"])
        self.summary.set(f"{service['label']} is ready on port {port}.")
        webbrowser.open(f"http://127.0.0.1:{port}")

    def start_failed(self, key, pid, detail=None):
        if self.pids.get(key) != pid or self.cancel_events[key].is_set():
            return
        label = SERVICES[key]["label"]
        if self.pid_running(pid):
            self.terminate_process_tree(pid)
        self.forget_process(key)
        self.states[key].set("Error")
        self.start_buttons[key].state(["!disabled"])
        self.stop_buttons[key].state(["disabled"])
        messagebox.showerror(
            f"{label} did not start",
            f"{detail + ' ' if detail else ''}Open the logs for details:\n{LOG_DIR}",
        )

    def forget_process(self, key):
        self.processes.pop(key, None)
        self.pids.pop(key, None)
        self.process_tokens.pop(key, None)
        self.active_ports.pop(key, None)
        log = self.logs.pop(key, None)
        if log:
            log.close()
        self.save_owned_pids()

    def stop(self, key):
        service = SERVICES[key]
        if not self.owned_running(key):
            port = self.active_ports.get(key, service["port"])
            if self.port_open(port):
                messagebox.showwarning(
                    f"Cannot stop {service['label']}",
                    "This instance was not started by this BioDYM launcher and will not be terminated.",
                )
            self.refresh_service_states()
            return
        self.cancel_events[key].set()
        pid = self.pids[key]
        self.terminate_process_tree(pid)
        self.forget_process(key)
        self.states[key].set("Stopped")
        self.summary.set(f"{service['label']} stopped.")
        self.refresh_service_states()

    def terminate_process_tree(self, pid):
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/T"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=NO_WINDOW,
            check=False,
        )
        for _ in range(20):
            if not self.pid_running(pid):
                break
            time.sleep(0.1)
        if self.pid_running(pid):
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=NO_WINDOW,
                check=False,
            )

    def start_all(self):
        for key in SERVICES:
            self.start(key)

    def stop_all(self):
        for key in SERVICES:
            self.stop(key)

    def refresh_service_states(self):
        for key, service in SERVICES.items():
            owned = self.owned_running(key)
            active_port = self.active_ports.get(key, service["port"])
            port_used = self.port_open(active_port)
            if owned and port_used:
                state = (
                    "Running"
                    if active_port == service["port"]
                    else f"Running :{active_port}"
                )
            elif owned:
                state = "Starting..."
            elif port_used:
                state = "Port conflict"
            elif self.states[key].get() != "Error":
                state = "Stopped"
            else:
                state = "Error"
            self.states[key].set(state)
            self.start_buttons[key].state(["disabled" if owned and not port_used else "!disabled"])
            self.stop_buttons[key].state(["!disabled" if owned else "disabled"])

    def refresh(self):
        self.refresh_service_states()
        self.after(1000, self.refresh)

    def open_logs(self):
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        try:
            os.startfile(LOG_DIR)
        except OSError as exc:
            messagebox.showerror("Cannot open logs", str(exc))

    def close(self):
        running = any(self.owned_running(key) for key in SERVICES)
        if running:
            answer = messagebox.askyesnocancel(
                "Close BioDYM Launcher",
                "Stop the BioDYM applications before closing?\n\n"
                "Yes: stop them.  No: leave them running.",
            )
            if answer is None:
                return
            if answer:
                self.stop_all()
        for log in self.logs.values():
            log.close()
        self.destroy()


if __name__ == "__main__":
    Launcher().mainloop()
