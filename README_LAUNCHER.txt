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

If something does not start, choose Open logs in the launcher. Logs and process
state are stored in your Windows Local AppData folder, not in the BioDYM folder.

Important: do not copy a .venv folder between computers or folder locations.
Run uv sync after placing BioDYM in its final location.
