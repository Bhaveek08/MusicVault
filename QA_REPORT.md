# MusicVault 2.0.0 — Release QA report

## Summary

- Host: Linux x86_64 sandbox (glibc 2.41)
- Python: 3.13.5
- FFmpeg: 7.1.5
- Consecutive full-suite runs: **50/50**
- Tests per run: **110/110**
- Total passing test executions: **5,500**
- Failed runs: **0**
- Result: **PASS for Linux source and local media regression checks**

## Coverage

The 110-test suite covers:

1. URL allowlists, canonicalization, query parsing, malformed-link rejection and generated URL fuzz inputs.
2. Spotify official-host validation and non-exporting Spotify hand-off.
3. Playlist-only links and the 500-item playlist cap.
4. Queue limits and guarded queue state transitions.
5. Output-folder creation, resolution, permissions and cleanup.
6. Safe output templates, Windows-compatible filenames and collision handling.
7. Best-available source audio selection and 320 kbps targets for lossy exports.
8. WAV/FLAC paths without lossy bitrate caps.
9. MKV audio/video merge and remux option mapping.
10. Downloader isolation: no browser cookies, credentials or plugins.
11. Bundled FFmpeg/Deno path containment and missing-runtime behaviour.
12. Log redaction for URLs, authorization values, cookies and tokens.
13. Progress formatting for normal and invalid numeric values.
14. Static Windows installer flags, app metadata, icons and console suppression.
15. Worker-thread lifecycle, cancellation and shutdown guards.
16. Local FFmpeg encode/decode round trips for advertised audio and MKV formats.
17. Duplicate-method detection and MusicVault branding consistency.
18. Black theme and provider-specific YouTube red / Spotify green accents.
19. Bounded, event-driven button, tab, queue and progress animations.
20. Packaging scripts, CI workflows and publishing helper safety checks.
21. Explicit disclosures that Android/iOS clients do not yet exist.

## Platform boundaries

This report records repeated runs of the same deterministic test suite on **one Linux x86_64 host**. It does not represent testing 50 separate devices or operating systems.

- **Linux:** source tests and local FFmpeg media smoke tests passed.
- **Windows:** a GitHub Actions build workflow is configured, but its runner must complete before Windows is marked tested.
- **macOS Apple Silicon:** a build workflow is configured, but its runner must complete before macOS is marked tested. The current build is unsigned and not notarized.
- **Android/iOS:** no mobile clients exist in this release; no mobile tests are claimed.

PySide6 is not installed in the Linux sandbox. Source syntax, static UI/installer configuration and regression tests were checked, but a rendered Qt window, packaged Windows installer, and macOS app/DMG were not executed here.

The suite uses generated local media for FFmpeg round trips. It does not prove that every remote YouTube URL will download or validate every file produced by a live platform transfer. A real transfer remains subject to platform availability and restrictions.

Lossy re-encoding cannot restore information absent from the source. MusicVault selects the best available source audio and requests 320 kbps for supported lossy exports; source quality remains the ceiling. WAV/FLAC are not constrained by a lossy bitrate cap.

No test suite proves an application has zero defects. Release qualification still requires native platform build, GUI smoke, installer/uninstaller, accessibility and real-device validation.
