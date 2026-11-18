# MusicVault 2.0.0 — QA report

## Automated test matrix

GitHub Actions CI completed successfully for commit `a7be99f9a75fa5a9d99132a8db13fa2c726d1337` on all six combinations:

| Runner | Python | Repeated runs | Result |
| --- | --- | ---: | --- |
| Ubuntu latest | 3.11 | 50 | Passed |
| Ubuntu latest | 3.13 | 50 | Passed |
| Windows latest | 3.11 | 50 | Passed |
| Windows latest | 3.13 | 50 | Passed |
| macOS 15 (Apple Silicon) | 3.11 | 50 | Passed |
| macOS 15 (Apple Silicon) | 3.13 | 50 | Passed |

Each job runs `run_release_qa.py`, which repeats the current pytest suite 50 times and stops on the first failure. The current repository suite contains **33 pytest cases**, including parameterized cases.

- Complete suite runs: **300** (50 on each of six runner/Python combinations)
- Passing test-case executions: **9,900**
- Failed test runs: **0**
- Result: **PASS for the tested source-level behaviours on the listed GitHub-hosted runners**

These are repeated executions of one deterministic suite, not 50 independent devices or 50 independently designed test plans per platform.

## Test coverage

1. Accepted YouTube video and playlist URL forms, and extraction of their video/playlist identifiers.
2. Rejection of unsafe YouTube links including HTTP, deceptive host suffixes, arbitrary hosts, embedded credentials, non-standard ports, unsupported schemes, and oversized inputs.
3. Separation of Spotify from the download engine.
4. Validation of supported official Spotify hand-off links, and rejection of unsafe Spotify links.
5. Per-user application data path selection for Windows and macOS.
6. Creation and basic write access validation for the selected output directory.
7. yt-dlp option construction for MP3, WAV, FLAC, M4A, AAC, OPUS, and MKV.
8. Checks that generated download options do not enable cookie-file access and keep remote components disabled.
9. The current MP3 export quality target (320 kbps).
10. Handling of invalid values in byte-size and ETA display helpers.
11. Application name and version identity.

## Native packaging verification

Both platform-specific GitHub Actions packaging jobs completed successfully for the public repository:

| Platform | Result | Artifact |
| --- | --- | --- |
| Windows x64 | <badge>Build + packaged smoke test passed</badge> | [Download Windows build](https://github.com/Bhaveek08/MusicVault/actions/runs/44306071742/artifacts/14429435283) |
| macOS 15 / Apple Silicon | <badge>Build + packaged smoke test passed</badge> | [Download macOS DMG](https://github.com/Bhaveek08/MusicVault/actions/runs/44306072060/artifacts/14429270149) |

The Windows workflow built a windowed PyInstaller payload, ran the packaged executable with `--smoke-test`, compiled the per-user Inno Setup installer, and uploaded the installer plus payload. The macOS workflow built the Apple Silicon `.app`, ran the packaged offscreen smoke test, created a DMG, and uploaded it.

These workflow artifacts are temporary (currently retained for 14 days). The Windows installer is not code-signed. The macOS build is unsigned and not notarized, so macOS may show a security warning and wider distribution requires Apple Developer ID signing and notarization.

## Platform boundaries

- **Windows 10/11 x64:** desktop source tests and native installer build passed on GitHub Actions.
- **macOS 15 Apple Silicon:** desktop source tests and native app/DMG build passed on GitHub Actions.
- **Linux:** source test matrix passed; no native Linux installer is provided.
- **Android/iOS:** no mobile clients exist in this repository; no mobile build or test is claimed.

The Python test matrix does **not** render or manually interact with the UI, run a live YouTube transfer, validate every downloaded media file, test installer upgrades/uninstalls on a physical user's device, or certify code signing/notarization. The offscreen packaged smoke tests verify app startup and bundled-runtime resolution, not every UI interaction.

## Important limitations

The suite does not prove every public YouTube URL will download. Provider availability, network behaviour, and platform restrictions remain outside the unit-test environment. MusicVault does not bypass DRM, sign-in walls, private/member-only restrictions, or platform access controls. Spotify links are handed off to Spotify; protected streaming tracks are not exported to MP3/WAV files.

The tests check requested output-format option mapping, not a full encode/decode round trip for every format in the committed GitHub suite. A live download and decoded output should be checked before attaching any binary to a permanent public release.

Lossy re-encoding cannot restore information absent from the source. MusicVault requests a 320 kbps target for the formats configured as lossy exports; source quality remains the ceiling. WAV/FLAC are not constrained by a lossy bitrate cap.

No test suite proves an application has zero defects.
