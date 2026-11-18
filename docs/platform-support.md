# Platform support and roadmap

## Current support matrix

| Platform | Source/runtime status | Installer status | Release status |
| --- | --- | --- | --- |
| Windows 10/11 x64 | PySide6 desktop client | Inno Setup per-user installer | Build configured; unsigned until code signing is added |
| macOS Apple Silicon | PySide6 desktop client | `.app` + `.dmg` | Experimental; unsigned and not notarized |
| macOS Intel | Not packaged | None | Not currently supported as a release artifact |
| Linux | Python source/testing only | None | No supported installer |
| Android | No mobile client | None | Planned; not supported |
| iOS/iPadOS | No mobile client | None | Planned; not supported |

## Desktop distribution

Windows uses a windowed PyInstaller one-folder payload wrapped in an Inno Setup per-user installer. The app installs under the user's local Programs directory; user preferences and logs live in OS-specific app data; downloads are saved to `Music/MusicVault` by default. Uninstall does not delete user downloads.

macOS uses a native `.app` bundle and DMG for Apple Silicon. The build creates an ICNS asset from the high-resolution PNG master. The current pipeline is unsigned and not notarized; public distribution requires Developer ID signing, hardened runtime configuration as appropriate, and Apple notarization.

## Mobile is a separate implementation phase

The desktop codebase is not an Android or iOS build. It uses PySide6 Widgets, Python yt-dlp APIs, FFmpeg, and Deno. Mobile requires a dedicated client and platform-specific storage APIs, permissions, background-task design, architecture-specific dependencies, signing, store-policy review, and testing on physical devices and emulators/simulators.

The mobile scope must preserve the same source rules: Spotify links can open in the official app, but Spotify streaming tracks are not exported as local media files. YouTube downloads must respect ownership/permission, applicable platform terms, and access restrictions. A mobile build must not be advertised until its permitted use case and distribution route are validated for each store.

## Release qualification requirements

For every target platform, record the OS version, architecture, runner/device type, build identifier, test run ID, and exact pass/fail count. The 50-pass desktop QA command verifies repeated regression runs on the host where it executes. It is not a substitute for mobile application tests or real-device validation.

Before Android or iOS can be called supported, the project needs:

1. A dedicated mobile client and accessibility review.
2. Platform-specific file APIs and lifecycle/background-download design.
3. Dependency provenance, signing, permissions, and privacy disclosures.
4. Emulator/simulator automation plus physical-device tests.
5. Store-policy and distribution review.
6. At least 50 independent regression runs on each platform runner, plus device-specific scenarios and media-file integrity checks.

A successful Android test run does not count as iOS coverage, and vice versa.
