#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ "$(uname -s)" != "Linux" || "$(uname -m)" != "x86_64" ]]; then
  echo "This release script targets Linux x86_64." >&2
  exit 2
fi

PYTHON="${PYTHON:-python3}"
"$PYTHON" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,11) else "Python 3.11+ required")'

if [[ ! -d .venv ]]; then
  "$PYTHON" -m venv .venv
fi
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-build.txt -r requirements-test.txt
python scripts/run_release_qa.py

DENO_BIN="$(command -v deno || true)"
if [[ -z "$DENO_BIN" || ! -x "$DENO_BIN" ]]; then
  echo "Deno 2.9.8+ is required. Install it from https://deno.com/ before building." >&2
  exit 3
fi

rm -rf build dist/MusicVault
python -m PyInstaller --noconfirm --clean --onedir --windowed \
  --name MusicVault \
  --add-data "assets/musicvault-icon.png:assets" \
  --add-binary "$DENO_BIN:." \
  --collect-all yt_dlp \
  --collect-all yt_dlp_ejs \
  --collect-all imageio_ffmpeg \
  --hidden-import yt_dlp_ejs \
  musicvault_app.py

APP_DIR="$ROOT/dist/MusicVault"
if [[ ! -x "$APP_DIR/MusicVault" ]]; then
  echo "PyInstaller did not create the MusicVault executable." >&2
  exit 4
fi

mkdir -p "$APP_DIR/share/applications" "$APP_DIR/share/icons/hicolor/256x256/apps"
cp assets/musicvault-icon.png "$APP_DIR/share/icons/hicolor/256x256/apps/musicvault.png"
cat > "$APP_DIR/share/applications/musicvault.desktop" <<'DESKTOP'
[Desktop Entry]
Type=Application
Name=MusicVault
Comment=Local media workspace
Exec=MusicVault
Icon=musicvault
Terminal=false
Categories=AudioVideo;Audio;
DESKTOP

if command -v xvfb-run >/dev/null 2>&1; then
  QT_QPA_PLATFORM=xcb xvfb-run -a "$APP_DIR/MusicVault" --smoke-test
else
  echo "xvfb-run is required for the packaged GUI smoke test." >&2
  exit 5
fi

tar -C "$ROOT/dist" -czf "$ROOT/dist/MusicVault-Linux-x86_64.tar.gz" MusicVault
echo "Linux build complete: dist/MusicVault-Linux-x86_64.tar.gz"
