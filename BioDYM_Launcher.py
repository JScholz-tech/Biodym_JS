"""Windows desktop launcher for an existing BioDYM installation."""

from __future__ import annotations

import hashlib
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
import webbrowser
import ctypes
from ctypes import wintypes
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

ROOT = Path(__file__).resolve().parent
INSTALL_ID = hashlib.sha256(str(ROOT).casefold().encode()).hexdigest()[:12]
LOCAL_DATA = Path(os.environ.get("LOCALAPPDATA", tempfile.gettempdir()))
RUNTIME_DIR = LOCAL_DATA / "BioDYM Launcher" / INSTALL_ID
LOG_DIR = RUNTIME_DIR / "logs"
STATE_FILE = RUNTIME_DIR / "services.json"
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
NEW_GROUP = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)

SERVICES = {
    "dashboard": {
        "label": "BioDYM Dashboard",
        "port": 8866,
        "args": [
            "-m",
            "voila",
            "01_BioDYM_Dashboard.ipynb",
            "--port=8866",
            "--no-browser",
        ],
    },
    "systemdefiner": {
        "label": "SystemDefiner",
        "port": 8001,
        "args": ["-m", "systemdefiner"],
    },
}


class Launcher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("BioDYM Launcher")
        self.geometry("540x365")
        self.minsize(500, 345)
        self.processes: dict[str, subprocess.Popen] = {}
        self.logs = {}
        self.cancel_events = {key: threading.Event() for key in SERVICES}
        self.pids, self.process_tokens = self.load_owned_pids()
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
        ttk.Label(frame, text="BioDYM", font=("Segoe UI", 22, "bold")).pack(anchor="w")
        ttk.Label(
            frame,
            text="Start BioDYM without a terminal. The tools open in your browser.",
        ).pack(anchor="w", pady=(2, 18))
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
            return {}, {}
        owned, tokens = {}, {}
        for key, value in stored.items():
            if key not in SERVICES or not isinstance(value, dict):
                continue
            pid, expected = value.get("pid"), value.get("created")
            if not isinstance(pid, int) or not isinstance(expected, int):
                continue
            if self.process_created(pid) == expected:
                owned[key], tokens[key] = pid, expected
        return owned, tokens

    def save_owned_pids(self):
        try:
            RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
            temporary = STATE_FILE.with_suffix(".tmp")
            payload = {
                key: {"pid": pid, "created": self.process_tokens.get(key)}
                for key, pid in self.pids.items()
                if self.process_tokens.get(key) is not None
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
            log = self.logs.pop(key, None)
            if log:
                log.close()
            self.save_owned_pids()
        return False

    def start(self, key):
        service = SERVICES[key]
        port, label = service["port"], service["label"]
        if self.owned_running(key):
            if self.port_open(port):
                webbrowser.open(f"http://127.0.0.1:{port}")
                self.summary.set(f"{label} is already running.")
            else:
                self.summary.set(f"{label} is already starting.")
            return
        if self.port_open(port):
            self.states[key].set("Port conflict")
            messagebox.showerror(
                f"Cannot start {label}",
                f"Port {port} is already used by another application. Close that "
                "application and try again.",
            )
            return
        self.cancel_events[key].clear()
        log = self.open_service_log(key)
        try:
            process = subprocess.Popen(
                [sys.executable, *service["args"]],
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
        self.save_owned_pids()
        self.states[key].set("Starting...")
        self.start_buttons[key].state(["disabled"])
        self.stop_buttons[key].state(["!disabled"])
        self.summary.set(f"Starting {label}; this may take a moment...")
        threading.Thread(
            target=self.wait_ready,
            args=(key, process.pid, self.cancel_events[key]),
            daemon=True,
        ).start()

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
        service = SERVICES[key]
        for _ in range(120):
            if cancel_event.is_set() or self.pids.get(key) != pid:
                return
            process = self.processes.get(key)
            if process and process.poll() is not None:
                self.after(0, lambda: self.start_failed(key, pid))
                return
            if self.port_open(service["port"]):
                self.after(0, lambda: self.ready(key, pid))
                return
            time.sleep(0.5)
        self.after(0, lambda: self.start_failed(key, pid, "Startup timed out."))

    def ready(self, key, pid):
        if self.pids.get(key) != pid or self.cancel_events[key].is_set():
            return
        service = SERVICES[key]
        self.states[key].set("Running")
        self.start_buttons[key].state(["!disabled"])
        self.summary.set(f"{service['label']} is ready.")
        webbrowser.open(f"http://127.0.0.1:{service['port']}")

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
        log = self.logs.pop(key, None)
        if log:
            log.close()
        self.save_owned_pids()

    def stop(self, key):
        service = SERVICES[key]
        if not self.owned_running(key):
            if self.port_open(service["port"]):
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
            port_used = self.port_open(service["port"])
            if owned and port_used:
                state = "Running"
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
