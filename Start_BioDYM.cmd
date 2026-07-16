@echo off
setlocal
cd /d "%~dp0"

if not exist "BioDYM_Launcher.py" (
    echo BioDYM_Launcher.py is missing.
    echo Extract all launcher files into the main BioDYM folder.
    pause
    exit /b 1
)

if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" "BioDYM_Launcher.py"
    exit /b 0
)

where uv >nul 2>&1
if not errorlevel 1 (
    uv run pythonw "BioDYM_Launcher.py"
    exit /b
)

where conda >nul 2>&1
if not errorlevel 1 (
    conda run -n biodym_env pythonw "BioDYM_Launcher.py"
    exit /b
)

echo No BioDYM environment was found.
echo Install BioDYM with uv sync or create the biodym_env Conda environment.
pause
exit /b 1
