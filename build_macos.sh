#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if [[ "$(uname -s)" != "Darwin" || "$(uname -m)" != "arm64" ]]; then
  echo "Build on an Apple Silicon Mac. Intel macOS is not a supported packaged target yet." >&2
  exit 2
fi

python3 -m venv .venv-macos
source .venv-macos/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-build.txt -r requirements-test.txt
python run_release_qa.py
bash ./prepare_macos.sh

if [[ ! -f assets/musicvault.icns ]]; then
  echo "Missing assets/musicvault.icns" >&2
  exit 1
fi
rm -rf build dist/MusicVault.app dist/musicvault-dmg
python -m PyInstaller --noconfirm --clean --onedir --windowed \
  --name MusicVault \
  --icon assets/musicvault.icns \
  --osx-bundle-identifier com.musicvault.desktop \
  --add-data "assets/musicvault-icon.png:assets" \
  --add-data "assets/musicvault.icns:assets" \
  --add-binary "vendor/deno:." \
  --collect-all shiboken6 \
  --collect-all yt_dlp \
  --collect-all yt_dlp_ejs \
  --collect-all imageio_ffmpeg \
  --hidden-import yt_dlp_ejs \
  musicvault_app.py


# This release targets Apple Silicon only. Strip the unused x86_64 slice from
# universal2 Qt and helper binaries to avoid shipping a second architecture.
echo "Thinning universal binaries to Apple Silicon arm64..."
while IFS= read -r -d '' binary; do
  architectures="$(lipo -archs "$binary" 2>/dev/null || true)"
  if [[ " $architectures " == *" arm64 "* && " $architectures " == *" x86_64 "* ]]; then
    temporary="${binary}.arm64"
    lipo "$binary" -thin arm64 -output "$temporary"
    chmod "$(stat -f '%Lp' "$binary")" "$temporary"
    mv "$temporary" "$binary"
  fi
done < <(find dist/MusicVault.app/Contents -type f -print0)

APP_BIN="dist/MusicVault.app/Contents/MacOS/MusicVault"
if [[ ! -x "$APP_BIN" ]]; then
  echo "PyInstaller did not create the expected macOS application bundle." >&2
  exit 1
fi
QT_QPA_PLATFORM=offscreen "$APP_BIN" --smoke-test

mkdir -p dist/musicvault-dmg
cp -R dist/MusicVault.app dist/musicvault-dmg/
ln -s /Applications dist/musicvault-dmg/Applications
hdiutil create -volname "MusicVault" -srcfolder dist/musicvault-dmg \
  -ov -format UDZO dist/MusicVault-macos-arm64.dmg >/dev/null

echo "Created dist/MusicVault-macos-arm64.dmg"
echo "This artifact is not signed or notarized; see docs/platform-support.md before public distribution."
