@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Build MusicVault

echo.
echo  M U S I C V A U L T  /  Windows x64 release build
echo ------------------------------------------------

py -c "import struct,sys; sys.exit(0 if sys.version_info >= (3, 11) and struct.calcsize('P') == 8 else 1)"
if errorlevel 1 (
  echo 64-bit Python 3.11 or newer is required. Install it with the Python Launcher enabled.
  if not defined CI pause
  exit /b 1
)

if not exist .venv\Scripts\python.exe (
  py -m venv .venv
  if errorlevel 1 goto :failed
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
if errorlevel 1 goto :failed
python -m pip install -r requirements-build.txt -r requirements-test.txt
if errorlevel 1 goto :failed

echo.
echo Running the MusicVault release QA suite...
python run_release_qa.py
if errorlevel 1 goto :failed

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0prepare_windows.ps1"
if errorlevel 1 goto :failed

if not exist assets\musicvault.ico (
  echo App icon is missing: assets\musicvault.ico
  goto :failed
)
if not exist vendor\deno.exe (
  echo Bundled Deno runtime is missing.
  goto :failed
)

if exist dist\MusicVault rmdir /s /q dist\MusicVault
python -m PyInstaller --noconfirm --clean --onedir --windowed ^
  --name MusicVault ^
  --icon assets\musicvault.ico ^
  --add-data "assets\musicvault-icon.png;assets" ^
  --add-data "assets\musicvault.ico;assets" ^
  --version-file windows_version_info.txt ^
  --add-binary "vendor\deno.exe;." ^
  --collect-all PySide6 ^
  --collect-all shiboken6 ^
  --collect-all yt_dlp BˆKXÛÛXİX[]ÙÙZœÈ‚ˆKXÛÛXİX[[XYÙZ[×Ù™›\YÈ‚ˆKZY[‹Z[\Ü]ÙÙZœÈ‚ˆ]\ÚXİ˜][Ø\œBšYˆ\œ›Ü›]™[HÛİÈ™˜Z[Y‚šYˆ›İ^\İ™\İ]\ÚXÕ˜][]\ÚXÕ˜][™^Hˆ
ˆXÚÈR[œİ[\ˆY›İÜ™X]HH^XİY\XØ][Ûˆ›Û\‹‚ˆÛİÈ™˜Z[YŠB‚™XÚË‚™XÚÈÛ[ÚÙK]\İ[™ÈHXÚØYÙY\XØ][Ûˆ[™[™YÛÛË‹‹‚œÙ]UÔTWÔU“Ô“O[Ù™œØÜ™Y[‚™\İ]\ÚXÕ˜][]\ÚXÕ˜][™^HK\Û[ÚÙK]\İšYˆ\œ›Ü›]™[HÛİÈ™˜Z[YœÙ]UÔTWÔU“Ô“OB‚œÙ]’TĞĞÏH‚™›Üˆ	IT[ˆ
‰T›ÙÜ˜[Qš[\ÊŠIW[››ÈÙ]\—TĞĞË™^Hˆ‰T›ÙÜ˜[Qš[\ÉW[››ÈÙ]\—TĞĞË™^HŠHÈ
ˆYˆ^\İ‰I_™”ˆÙ]’TĞĞÏII_™”‚ŠBšYˆ›İYš[™YTĞĞÈ›ÜˆÙˆ™[[\ÏHˆ	IRH[ˆ
	İÚ\™HTĞĞË™^H—›[	ÊHÈÙ]’TĞĞÏIIRH‚šYˆ›İYš[™YTĞĞÈ
ˆXÚÈ[››ÈÙ]\ˆ\È™\]Z\™YÈÜ™X]HHİZYY[œİ[\‹‚ˆXÚÈ[œİ[]Ú]ˆÚ[™Ù][œİ[KZY””ÛÙØ\™K’[››ÔÙ]\YBˆÛİÈ™˜Z[YŠB‚ˆ‰RTĞĞÉHˆÓÈ™\İˆ[œİ[\—]\ÚXÕ˜][š\ÜÂšYˆ\œ›Ü›]™[HÛİÈ™˜Z[YšYˆ›İ^\İ\İ]\ÚXÕ˜][TÙ]\™^HÛİÈ™˜Z[Y‚™XÚË‚™XÚÈ™[X\ÙHZ[ÛÛ\]N‚™XÚÈ\İ]\ÚXÕ˜][]\ÚXÕ˜][™^HÚ[™İÙY\XØ][Ûˆ^[ØY™XÚÈ\İ]\ÚXÕ˜][TÙ]\™^HİZYYÚ[™İÜÈ[œİ[\‚™XÚË‚™XÚÈH[œİ[\ˆÜ™X]\ÈHİ\Y[HÚÜİ][™Ü[Û˜[HH\ÚİÜÚÜİ]‚™XÚÈ][œİ[È\‹]\Ù\ˆ[™Ù\È›İ™[[İ™HH\Ù\‰ÜÈİÛ›ØYÈÛˆ[š[œİ[‚šYˆ›İYš[™YÒH]\ÙB™^]Øˆ‚™˜Z[Y™XÚË‚™XÚÈZ[˜Z[Yˆ™]šY]ÈH\œ›ÜˆX›İ™NÈ™[X\ÙH\Y˜XİÈX^H™H[˜ÛÛ\]K‚šYˆ›İYš[™YÒH]\ÙB™^]ØˆB