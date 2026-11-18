<div align="center">
  <img src="assets/musicvault-icon.png" alt="MusicVault application icon" width="104" />
  <h1>MusicVault</h1>
  <p><strong>A focused desktop app for saving supported YouTube media and opening Spotify links.</strong></p>
  <p>Windows 10/11 x64 · macOS Apple Silicon (experimental build) · Python 3.11+</p>
</div>

MusicVault keeps a simple workflow in one window: paste a supported YouTube link, choose an output format, and manage the resulting files in a local queue. Spotify links are handled separately and opened in Spotify.

## What it does

- **YouTube:** queue public videos or playlists that you own or are authorized to save, subject to platform rules and availability.
- **Spotify:** validate and open official track, album, artist, or playlist links. Spotify streaming tracks are not exported as MP3/WAV files; offline listening stays in Spotify.
- **Formats:** MP3, WAV, FLAC, M4A, AAC, OPUS, and MKV. Lossy audio exports target 320 kbps where supported; WAV/FLAC avoid a lossy bitrate cap. The output cannot exceed the quality of the source stream.
- **Workflow:** playlist opt-in, queue management, progress, cancellation, remembered output folder, and collision-safe output names.
- **Interface:** black-first theme, YouTube red and Spotify green accents, short hover/press feedback, and animated progress.

MusicVault does not bypass DRM, sign-in walls, private or member-only restrictions, browser sessions, or platform access controls.

## Platform status

| Platform | Current status | Distribution |
| --- | --- | --- |
| Windows 10/11 x64 | Desktop source and installer pipeline configured | Per-user `MusicVault-Setup.exe` |
| macOS Apple Silicon | Experimental desktop build pipeline configured | `.app` + `.dmg`; unsigned and not notarized |
| macOS Intel | Not packaged | Not currently supported as a release artifact |
| Linux | Source/test environment only | No native installer |
| Android | No mobile client yet | Planned, not supported |
| iOS/iPadOS | No mobile client yet | Planned, not supported |

The current application is a PySide6 desktop client. Android and iOS are separate future implementations, not supported by the desktop executable. A mobile client will need its own UI, file/storage permissions, background-task handling, signing, store-policy review, and device test matrix. See [platform support](docs/platform-support.md).

## Install

### Windows

Use the signed `MusicVault-Setup.exe` from a trusted project release when one is available. The installer is configured to:

- install per-user under `%LOCALAPPDATA%\Programs\MusicVault`;
- create a Start Menu shortcut and offer an optional desktop shortcut;
- keep application settings/logs and the user's media library outside the install directory;
- uninstall the application without deleting the user's downloads.

The packaged GUI is built in windowed mode and does not require Python on the target PC. The current pipeline does not yet sign the installer; Windows may display an unknown-publisher warning until code signing is configured.

### macOS (Apple Silicon)

The build pipeline creates `MusicVault.app` and a DMG. The current artifact is unsigned and not notarized; wider distribution requires Apple Developer ID signing and notarization. Intel Macs are not covered by this build.

## Build from source

### Windows x64

Requirements: 64-bit Windows 10/11, Python 3.11+, and Inno Setup 6.

```powershell
winget install --id JRSoftware.InnoSetup -e
```

Then run `build_windows.bat`. The script creates a local virtual environment, installs pinned dependencies, runs the 50-pass QA gate on that Windows host, verifies the pinned Deno archive, packages a windowed application, smoke-tests the packaged app, and builds the guided installer.

Expected outputs:

```text
dist/ MusicVault-Setup.exe
      MusicVault/                 # app payload installed by the setup program
        MusicVault.exe
        _internal/                # private runtime bundle
```

### macOS Apple Silicon

Requirements: Apple Silicon Mac, Python 3.11+, Xcode command-line tools, and network access for the checksum-pinned Deno archive.

```bash
./build_macos.sh
```

The script runs the same 50-pass QA gate on the Mac host, stages Deno from the pinned official release, generates the native app icon, builds and smoke-tests the `.app`, and creates a DMG.

## Test and QA

Run a single suite:

```bash
python -m pip install -r requirements-test.txt
python -m pytest -q
```

Run the 50-pass host QA gate:

```bash
python run_release_qa.py
```

Set `MUSICVAULT_QA_RUNS` to a number from 1 to 200 to override the default. The report identifies the host where it ran. Repeating a deterministic test suite does not equal testing 50 operating systems or 50 devices. The current project has Windows and macOS desktop CI/build workflows; Android and iOS have no application client and therefore cannot pass mobile tests yet.

The suite covers URL allowlists, malformed links, Spotify hand-off policy, path validation, queue and playlist caps, download option hardening, log redaction, packaged tool lookup, and local FFmpeg encode/decode smoke tests for the supported output formats. It does not prove every remote media URL will download or validate every output file from a live platform transfer.

## Security model

- HTTPS-only URL validation with strict YouTube and Spotify host allowlists for separate actions.
- Rejects credentials embedded in URLs, lookalike hosts, non-standard ports, malformed IDs, control characters, and oversized inputs.
- User-entered text is not passed to a shell.
- No browser cookies, saved browser sessions, passwords, downloader plugins, or remote JavaScript components.
- Deno is staged from official archives and verified against a pinned SHA-256 digest.
- Frozen builds resolve FFmpeg and Deno only from inside the application bundle.
- Log output is size-limited and redacts URLs, authorization headers, cookies, and common token fields.

No desktop application can be guaranteed free of all defects. Keep the OS and trusted releases updated, review third-party notices, and do not run modified or untrusted builds. See [SECURITY.md](SECURITY.md) and [the security model](docs/security-model.md).

## Project layout

```text
.
├── musicvault_app.py
├── musicvault_core.py
├── assets/                       # shared PNG master, Windows ICO, macOS ICNS
├── installer/MusicVault.iss      # Windows per-user installer
├── tests/                        # unit, hardening, media and packaging checks
├── docs/                         # architecture, platform, security and releases
├── build_windows.bat
├── build_macos.sh
├── prepare_windows.ps1
├── prepare_macos.sh
├── run_release_qa.py
└── .github/workflows/            # CI, CodeQL and platform build workflows
```

## Third-party components

MusicVault uses PySide6/Qt for Python, yt-dlp, yt-dlp-ejs, imageio-ffmpeg/FFmpeg, PyInstaller, and Deno. See [THIRD_PARTY_NOTICES.txt](THIRD_PARTY_NOTICES.txt). Review upstream licenses before redistributing binaries. The media runtime increases installer size; the app does not install a background service.

## License

No project license has been selected. Public visibility on GitHub does not automatically grant rights to reuse the code. See [LICENSE_STATUS.md](LICENSE_STATUS.md).

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), and the [release process](docs/release-process.md) before proposing changes.
