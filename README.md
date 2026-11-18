<div align="center">
  <img src="assets/musicvault-icon.png" alt="MusicVault application icon" width="104" />
  <h1>MusicVault</h1>
  <p><strong>A focused desktop app for supported YouTube media downloads and Spotify link hand-off.</strong></p>
  <p>Windows 10/11 x64 · macOS Apple Silicon · Python 3.11+</p>
</div>

MusicVault provides a single desktop window for managing permitted YouTube media downloads. Spotify share links are handled separately and opened in Spotify.

## Features

- **YouTube:** queue supported public videos and playlists that you own or are authorized to save, subject to platform rules and availability.
- **Spotify:** validate and open official track, album, artist, or playlist links. Protected streaming tracks are not exported to MP3/WAV files.
- **Formats:** MP3, WAV, FLAC, M4A, AAC, OPUS, and MKV. Lossy audio exports target 320 kbps where supported; source quality remains the limit.
- **Workflow:** playlist opt-in, queue management, progress, cancellation, remembered output folder, and collision-safe filenames.
- **Interface:** black-first theme, YouTube red and Spotify green accents, lightweight button feedback, and animated progress.

MusicVault does not bypass DRM, sign-in walls, private/member-only restrictions, browser sessions, or platform access controls.

## Platform status

| Platform | Current status | Distribution |
| --- | --- | --- |
| Windows 10/11 x64 | Desktop client and installer pipeline verified in CI | Per-user `MusicVault-Setup.exe` |
| macOS Apple Silicon | Experimental desktop build pipeline verified in CI | `.app` + `.dmg`; unsigned and not notarized |
| macOS Intel | Not packaged | Not currently supported as a release artifact |
| Linux | Source/test environment only | No native installer |
| Android | Touch-first UI prototype; desktop-hosted phone UI tests; native deployment blocked by Qt license gate | No APK/AAB |
| iOS/iPadOS | Touch-first UI prototype; desktop-hosted phone UI tests; host Xcode readiness checked | No IPA or simulator app |

The mobile workstream is separate from the desktop downloader. It currently contains a touch-first UI prototype and URL validation only; mobile media downloads are **not enabled**. The desktop downloader's Deno/FFmpeg/yt-dlp pipeline needs platform-specific porting, app-sandbox storage, and background-task work before a mobile build can be called functional. See [mobile workstream](mobile/README.md) and [platform support](docs/platform-support.md).

## Install

### Windows

Use the Windows installer from a trusted project release or the [Windows build workflow](https://github.com/Bhaveek08/MusicVault/actions/workflows/windows-build.yml). The installer is configured to:

- install per-user under `%LOCALAPPDATA%\Programs\MusicVault`;
- create a Start Menu shortcut and offer an optional desktop shortcut;
- keep preferences/logs and the media library outside the install directory;
- uninstall the app without deleting user downloads.

The installer is not code-signed; Windows may show an unknown-publisher warning until signing is configured.

### macOS (Apple Silicon)

The [macOS build workflow](https://github.com/Bhaveek08/MusicVault/actions/workflows/macos-build.yml) creates `MusicVault.app` and a DMG. The current artifact is unsigned and not notarized; wider distribution requires Apple Developer ID signing and notarization.

## Build from source

### Windows x64

Requirements: 64-bit Windows 10/11, Python 3.11+, and Inno Setup 6.

```powershell
winget install --id JRSoftware.InnoSetup -e
scripts\build_windows.bat
```

The script creates a local virtual environment, installs pinned dependencies, runs the 50-pass QA gate, verifies the pinned Deno archive, packages a windowed app, smoke-tests the executable, and builds the guided installer.

### macOS Apple Silicon

Requirements: Apple Silicon Mac, Python 3.11+, Xcode command-line tools, and network access for the checksum-pinned Deno archive.

```bash
bash scripts/build_macos.sh
```

The script runs the 50-pass QA gate, stages Deno from its pinned official release, generates the native app icon, builds and smoke-tests the `.app`, and creates a DMG.

### Development launch (Windows)

```bat
scripts\run_dev_windows.bat
```

## Test and QA

Run the suite once:

```bash
python -m pip install -r requirements-test.txt
python -m pytest -q
```

Run the repeated host QA gate:

```bash
python scripts/run_release_qa.py
```

Set `MUSICVAULT_QA_RUNS` to a number from 1 to 200 to override the default. The runner identifies the host where it executes; repeated host tests are not a substitute for real-device testing. Mobile tests instantiate the Qt Widgets UI at phone dimensions on desktop runners, test tab switching and the preview queue, and check URL policy. They do not test on physical phones or emulators. The [Mobile UI workflow](https://github.com/Bhaveek08/MusicVault/actions/workflows/mobile.yml) also generates four current desktop/mobile UI screenshots as a review artifact. Android deployment is currently blocked by Qt's commercial-license credential gate; iOS target wheels/signing are not provisioned.

## Security model

- HTTPS-only URL validation with strict YouTube and Spotify host allowlists for separate actions.
- Rejects credentials embedded in URLs, lookalike hosts, non-standard ports, malformed IDs, control characters, and oversized inputs.
- User-entered text is not passed to a shell.
- No browser cookies, saved browser sessions, passwords, downloader plugins, or remote JavaScript components.
- Deno is staged from official archives and verified against a pinned SHA-256 digest.
- Frozen builds resolve FFmpeg and Deno only from inside the application bundle.
- Logs are size-limited and redact URLs, authorization headers, cookies, and common token fields.

No desktop application can be guaranteed free of all defects. Keep the OS and trusted releases updated, review third-party notices, and do not run modified or untrusted builds. See [SECURITY.md](SECURITY.md) and [the security model](docs/security-model.md).

## Project structure

```text
.
├── musicvault_app.py             # desktop UI
├── musicvault_core.py            # validation and downloader configuration
├── assets/                       # app icon files
├── installer/                    # Windows installer and version metadata
├── scripts/                      # platform build, staging, dev, QA, and UI preview scripts
├── mobile/                       # mobile UI prototype and deployment config
├── tests/                        # core and mobile UI tests
├── docs/                         # architecture, platform, security, and release docs
└── .github/workflows/             # CI, CodeQL, and platform build workflows
```

## Third-party components

MusicVault uses PySide6-Essentials/Qt for Python, yt-dlp, yt-dlp-ejs, imageio-ffmpeg/FFmpeg, PyInstaller, and Deno. See [THIRD_PARTY_NOTICES.txt](THIRD_PARTY_NOTICES.txt). Review upstream licenses before redistributing binaries. The bundled desktop media runtime adds significant installer size; the app does not install a background service.

## License

No project license has been selected. Public visibility on GitHub does not automatically grant rights to reuse the code. See [LICENSE_STATUS.md](LICENSE_STATUS.md).

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), and the [release process](docs/release-process.md) before proposing changes.
