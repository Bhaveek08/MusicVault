# MusicVault 2.0.0 — QA report

## Automated test matrix

The GitHub Actions CI workflow completed successfully for commit `a7be99f9a75fa5a9d99132a8db13fa2c726d1337` on all six combinations:

| Runner | Python | Result |
| --- | --- | --- |
| Ubuntu latest | 3.11 | Passed |
| Ubuntu latest | 3.13 | Passed |
| Windows latest | 3.11 | Passed |
| Windows latest | 3.13 | Passed |
| macOS 15 (Apple Silicon) | 3.11 | Passed |
| macOS 15 (Apple Silicon) | 3.13 | Passed |

Each job runs `run_release_qa.py`, which repeats the same pytest suite 50 times and stops on the first failure. The current suite contains **33 pytest cases** (including parameterized cases).

- Complete suite runs: **300** (50 on each of six runner/Python combinations)
- Passing test-case executions: **9,900**
- Failed test runs: **0**
- Result: **PASS for the tested Python core behaviours on the listed GitHub-hosted runners**

These are repeated executions of one test suite, not 50 independent devices or 50 independently designed test plans per platform.

## What the current suite tests

1. Accepted YouTube video and playlist URL forms, and extraction of their video/playlist identifiers.
2. Rejection of unsafe YouTube links including HTTP, deceptive host suffixes, arbitrary hosts, embedded credentials, non-standard ports, unsupported schemes, and oversized inputs.
3. Separation of Spotify from the download engine.
4. Validation of supported official Spotify hand-off links, and rejection of unsafe Spotify links.
5. Per-user application data path selection for Windows and macOS.
6. Creation and basic write access validation for the selected output directory.
7. yt-dlp option construction for MP3, WAV, FLAC, M4A, AAC, OPUS, and MKV.
8. Checks that the generated download options do not enable cookie-file access and keep remote components disabled.
9. The current MP3 export quality target (320 kbps).
10. Handling of invalid values in byte-size and ETA display helpers.
11. Application name and version identity.

## Packaging / platform validation

- **Windows source tests:** Passed on Windows latest with Python 3.11 and 3.13.
- **macOS source tests:** Passed on macOS 15 Apple Silicon with Python 3.11 and 3.13.
- **Linux source tests:** Passed on Ubuntu latest with Python 3.11 and 3.13.
- **Windows installer build:** A separate GitHub Actions packaging job is enabled on pushes to `main`. Its result must be checked in the Actions run before treating the installer as verified.
- **macOS app/DMG build:** A separate Apple Silicon packaging job is enabled on pushes to `main`. Its result must be checked in the Actions run before treating the app bundle or disk image as verified.
- **Android/iOS:** No mobile clients exist in this repository; no mobile build or test is claimed.

The Python test matrix does **not** render or interact with the Qt UI, run a live YouTube transfer, validate every downloaded media file, test installer upgrades/uninstalls, or certify app signing/notarization. Native packaging workflows include an offscreen app smoke-test stage, but only a completed successful packaging run proves that stage passed.

## Important limitations

The suite does not prove every public YouTube URL will download. Provider availability, network behaviour, and platform restrictions remain outside the unit-test environment. MusicVault does not bypass DRM, sign-in walls, private/member-only restrictions, or platform access controls.

The tests check the requested output-format option mapping, not a full encode/decode round trip for every format. A live download and decoded output should be checked before attaching a release binary to a public release.

Lossy re-encoding cannot restore information absent from the source. MusicVault requests a 320 kbps target for the formats configured as lossy exports; the source stream remains the quality ceiling. WAV/FLAC are not constrained by a lossy bitrate cap.

The macOS packaging pipeline currently targets Apple Silicon and is unsigned/not notarized. The Windows installer is not code-signed. Android/iOS are not implemented. No test suite proves an application has zero defects.
