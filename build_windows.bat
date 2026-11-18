@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Build MusicVault

echo.
echo MusicVault - Windows x64 release build
echo ======================================

py -c "import struct,sys; sys.exit(0 if sys.version_info >= (3,11) and struct.calcsize('P') == 8 else 1)"
if errorlevel 1 (
  echo 64-bit Python 3.11 or newer is required.
  if not defined CI pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  py -m venv .venv
  if errorlevel 1 goto :failed
)
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
if errorlevel 1 goto :failed
python -m pip install -r requirements-build.txt -r requirements-test.txt
if errorlevel 1 goto :failed

echo.
echo Running the 50-pass release QA gate...
python run_release_qa.py
if errorlevel 1 goto :failed

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0prepare_windows.ps1"
if errorlevel 1 goto :failed

if not exist "assets\musicvault.ico" (
  echo Missing assets\musicvault.ico
  goto :failed
)
if not exist "vendor\deno.exe" (
  echo The verified bundled Deno runtime is missing.
  goto :failed
)

if exist "build" rmdir /s /q "build"
if exist "dist\MusicVault" rmdir /s /q "dist\MusicVault"
python -m PyInstaller --noconfirm --clean --onedir --windowed ^
  --name MusicVault ^
  --icon "assets\musicvault.ico" ^
  --version-file "windows_version_info.txt" ^
  --add-data "assets\musicvault-icon.png;assets" ^
  --add-data "assets\musicvault.ico;assets" ^
  --add-binary "vendor\deno.exe;." ^
  --collect-all PySide6 ^
  --collect-all shiboken6 ^
  --collect-all yt_dlp ^
  --collect-all yt_dlp_ejs ^
  --collect-all imageio_ffmpeg ^
  --hidden-import yt_dlp_ejs ^
  "musicvault_app.py"
if errorlevel 1 goto :failed

if not exist "dist\MusicVault\MusicVault.exe" (
  echo PyInstaller did not create dist\MusicVault\MusicVault.exe
  goto :failed
)

set "QT_QPA_PLATFORM=offscreen"
"dist\MusicVault\MusicVault.exe" --smoke-test
if errorlevel 1 goto :failed
set "QT_QPA_PLATFORM="

set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" (
  echo Inno Setup 6 is required to build the guided installer.
  echo Install it with: winget install --id JRSoftware.InnoSetup -e
  goto :failed
)

"%ISCC%" /O"dist" "installer\MusicVault.iss"
if errorlevel 1 goto :failed
if not exist "dist\MusicVault-Setup.exe" goto :failed

echo.
echo Build complete:
echo   dist\MusicVault-Setup.exe
echo.
echo The installer is per-user and keeps downloads outside the install folder.
if not defined CI pause
exit /b 0

:failed
echo.
echo MusicVault build failed. Review the error above.
if not defined CI pause
exit /b 1
