BioDYM Launcher for Windows
===========================

1. Extract all four launcher files into the main BioDYM folder. This is the
   folder containing pyproject.toml and 01_BioDYM_Dashboard.ipynb.
2. BioDYM must already be installed there with uv sync, or in the Conda
   environment named biodym_env.
3. Double-click Start_BioDYM.vbs.

If Windows does not allow VBScript, double-click Start_BioDYM.cmd instead.
The CMD alternative briefly displays a terminal window while starting.

The launcher starts and stops the Dashboard and SystemDefiner. Closing the
launcher lets you either stop both applications or leave them running. A later
launcher session can reconnect to and stop applications that it started.

If an older BioDYM is already running, the launcher identifies it and offers to
stop it and start the current installation, or to open the existing one. It
will only stop a process after confirming that it is BioDYM and asking you.
If an unrelated application uses BioDYM's normal port, the launcher offers to
start safely on the next available port instead.

The launcher displays the current BioDYM version and installation folder so
that different copies can be distinguished. Each service card permanently
shows its active or default port, including alternative ports selected because
another application is already running.

If something does not start, choose Open logs in the launcher. Logs and process
state are stored in your Windows Local AppData folder, not in the BioDYM folder.
When uv is installed, the launcher checks and synchronizes the environment
automatically after BioDYM is updated. An HTTP 500 dashboard error is reported
in the launcher and its detailed notebook traceback is saved in dashboard.log.
Jupyter security, signature, runtime, and IPython files are isolated in the
launcher's Local AppData folder. This avoids failures caused by inaccessible or
company-managed roaming-profile Jupyter files.

Important: do not copy a .venv folder between computers or folder locations.
Run uv sync after placing BioDYM in its final location.
