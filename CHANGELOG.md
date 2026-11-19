# Changelog

## 2.0.3 — 2026-11-19

- Add the verified Linux x86_64 portable build to versioned GitHub Releases.
- Add direct latest-release download links for Windows, macOS, and Linux.
- Clarify that mobile builds are UI prototypes, not media downloader releases.
- Clarify the source and rights-holder authorization confirmation in the desktop UI.
- Expand desktop interaction coverage for paste, folder selection, queue errors, download, and stop actions.

## 2.0.2 — 2026-11-19

- Align the app, Windows installer, package metadata, and release version.
- Add desktop Qt interaction and window-bound regression tests.
- Clarify current platform packaging and QA evidence.

## Unreleased

- Added a touch-first Android/iOS UI prototype with safe YouTube/Spotify link validation; media downloading is intentionally not enabled in the mobile shell.
- Added host-side mobile source-policy tests and Android/iOS toolchain-readiness checks, while keeping native package status explicit.
- Organized platform scripts under `scripts/` and moved Windows version metadata into `installer/`.
- Reduced the desktop Qt dependency from the full PySide6 bundle to PySide6-Essentials and removed the all-Qt-modules collection flags.

## 2.0.0 — 2026-11-18

- Rebranded the desktop application as MusicVault across the UI, settings, logs, output folders, installers, and documentation.
- Replaced the previous blue/slate styling with a black-first interface and red YouTube / green Spotify accents.
- Added lightweight event-driven button hover/press feedback and a short source-tab transition.
- Created a monochrome vault-and-waveform icon set for the app.
- Changed the release QA gate to 50 complete runs on the host that executes it; the report now states the host limitation.
- Added only prototype mobile UI shells; native downloads and production mobile releases remain unsupported.

## 1.3.0 — 2026-11-18

- Added distinct YouTube and Spotify source tabs; Spotify share links are validated and opened in Spotify, not exported.
- Added platform-specific app-data paths and native Deno lookup for Windows and macOS.
- Switched Windows packaging to a windowed one-folder payload and a per-user Inno Setup installer.
- Added an Apple Silicon macOS `.app`/DMG build pipeline with checksum-pinned Deno staging.
- Added platform support documentation and a deterministic 10,000-input URL fuzz test.

## 1.1.0 — 2026-11-18

- Rebuilt the desktop interface with PySide6 and a single-window layout.
- Added queue management, per-item output formats, progress reporting, and cancellation.
- Added MP3, WAV, FLAC, M4A, AAC, OPUS, and MKV output selections.
- Added strict YouTube URL validation and explicit rejection of Spotify URLs.
- Added playlist and queue limits, safe output-folder checks, and no-overwrite defaults.
- Added log sanitization and restricted packaged tool lookup to the application bundle.
- Added a Windows one-file, windowed build process with a checksummed Deno runtime and packaged smoke test.
- Added a 15-pass automated release QA runner.

## Earlier versions

The initial prototype was distributed under the name SoundDrop. Its history is not represented as a fully traceable Git commit history in this repository.

### Audio quality

- Lossy audio exports target 320 kbps where supported; WAV and FLAC are not constrained by a lossy bitrate setting. Source quality remains the upper limit.
