@echo off
setlocal
set "ROOT=%~dp0.."
cd /d "%ROOT%"
if not exist ".venv\Scripts\python.exe" (
  echo Run scripts\build_windows.bat once to install the development dependencies.
  pause
  exit /b 1
)
call ".venv\Scripts\activate.bat"
pythonw "musicvault_app.py"
