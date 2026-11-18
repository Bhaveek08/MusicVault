#!/usr/bin/env bash
set -euo pipefail

VERSION="2.9.8"
ASSET="deno-aarch64-apple-darwin.zip"
EXPECTED_SHA256="9f0bf660393da2eaff044cdc7444cb08c73f235849b61d224d825a194ce7c98e"
ROOT="$(cd "$(dirname "$0")" && pwd)"
VENDOR="$ROOT/vendor"
TEMP="$ROOT/.build-deno-macos"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This script must run on macOS." >&2
  exit 2
fi
if [[ "$(uname -m)" != "arm64" ]]; then
  echo "This pinned build currently targets Apple Silicon (arm64); Intel Mac packaging is not yet configured." >&2
  exit 2
fi

mkdir -p "$VENDOR" "$TEMP"
trap 'rm -rf "$TEMP"' EXIT
URL="https://github.com/denoland/deno/releases/download/v${VERSION}/${ASSET}"
curl --fail --location --silent --show-error "$URL" -o "$TEMP/$ASSET"
printf '%s  %s\n' "$EXPECTED_SHA256" "$TEMP/$ASSET" | shasum -a 256 -c -
unzip -q "$TEMP/$ASSET" -d "$TEMP/extracted"
install -m 755 "$TEMP/extracted/deno" "$VENDOR/deno"
"$VENDOR/deno" --version | grep -F "deno $VERSION" >/dev/null

# Build the native macOS icon from the high-resolution shared PNG master.
ICONSET="$ROOT/assets/musicvault.iconset"
rm -rf "$ICONSET"
mkdir -p "$ICONSET"
sips -z 16 16 "$ROOT/assets/musicvault-icon.png" --out "$ICONSET/icon_16x16.png" >/dev/null
sips -z 32 32 "$ROOT/assets/musicvault-icon.png" --out "$ICONSET/icon_16x16@2x.png" >/dev/null
sips -z 32 32 "$ROOT/assets/musicvault-icon.png" --out "$ICONSET/icon_32x32.png" >/dev/null
sips -z 64 64 "$ROOT/assets/musicvault-icon.png" --out "$ICONSET/icon_32x32@2x.png" >/dev/null
sips -z 128 128 "$ROOT/assets/musicvault-icon.png" --out "$ICONSET/icon_128x128.png" >/dev/null
sips -z 256 256 "$ROOT/assets/musicvault-icon.png" --out "$ICONSET/icon_128x128@2x.png" >/dev/null
sips -z 256 256 "$ROOT/assets/musicvault-icon.png" --out "$ICONSET/icon_256x256.png" >/dev/null
sips -z 512 512 "$ROOT/assets/musicvault-icon.png" --out "$ICONSET/icon_256x256@2x.png" >/dev/null
sips -z 512 512 "$ROOT/assets/musicvault-icon.png" --out "$ICONSET/icon_512x512.png" >/dev/null
sips -z 1024 1024 "$ROOT/assets/musicvault-icon.png" --out "$ICONSET/icon_512x512@2x.png" >/dev/null
iconutil -c icns "$ICONSET" -o "$ROOT/assets/musicvault.icns"
rm -rf "$ICONSET"
echo "Generated native MusicVault macOS app icon."

echo "Verified and staged Deno $VERSION for macOS arm64."
