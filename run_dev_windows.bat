@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo Run build_windows.bat once to install the development dependencies.
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat
pythonwc musicvault_app.py
