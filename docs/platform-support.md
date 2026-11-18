# Platform support and roadmap

## Current support matrix

| Platform | UI/runtime status | Package status | Release status |
| --- | --- | --- | --- |
| Windows 10/11 x64 | PySide6 desktop downloader | Inno Setup per-user installer | Build and packaged smoke test verified in CI; unsigned |
| macOS Apple Silicon | PySide6 desktop downloader | `.app` + `.dmg` | Build and packaged smoke test verified in CI; unsigned/notarized |
| macOS Intel | Not packaged | None | Not currently supported as a release artifact |
| Linux | Source/test environment only | None | No native installer |
| Android | Touch-first UI prototype and host-side tests | Native deploy preflight only; no APK/AAB release | Not supported for media downloads |
| iOS/iPadOS | Touch-first UI prototype and host-side tests | Native deploy preflight only; no IPA/App Store release | Not supported for media downloads |

## Desktop distribution

Windows uses a windowed PyInstaller one-folder payload wrapped in an Inno Setup per-user installer. The app installs under the user's local Programs directory; preferences and logs live in OS-specific app data; downloads default to `Music/MusicVault`. Uninstall does not delete user downloads.

macOS uses a native `.app` bundle and DMG for Apple Silicon. The build creates an ICNS asset from the high-resolution PNG master. The current pipeline is unsigned and not notarized; public distribution requires Developer ID signing, hardened runtime configuration as appropriate, and Apple notarization.

## Mobile prototype scope

The `mobile/` directory contains a touch-first PySide6 UI prototype and URL validation. Host-side tests cover YouTube/Spotify URL validation and static UI structure checks. They do not instantiate or render the Qt Widgets UI because Qt 6.12's offscreen backend crashed at shutdown on the available CI runners. These tests run on desktop CI hosts; they do not execute on an Android device or iOS simulator.

The mobile UI's preview queue is local UI state only. It does not download media. The desktop downloader currently uses yt-dlp/yt-dlp-ejs, Deno, and FFmpeg. Those are not drop-in mobile dependencies:

- Qt's iOS deploy tool generates an Xcode project using platform-specific PySide6/Shiboken wheels and a Python.xcframework. The tool documentation states that third-party packages are not automatically supported; packages with C extensions need target-specific cross-compilation and app-bundle integration.
- iOS requires sandbox-compliant file access, native sharing/export handling, app lifecycle/background-task design, privacy-purpose strings, provisioning, and App Store review.
- Android's arm64 PySide6/Shiboken wheels can be fetched with qtpip. The deploy attempt was blocked by the Qt deploy tool's license-credential gate in CI, so no APK/AAB has been created. A package build still needs Android SDK/NDK setup plus emulator/physical-device lifecycle, storage, permission, and network tests.

The mobile scope must preserve the desktop source policy: Spotify share links can open in the official app, but protected Spotify streams must not be exported as local media files. YouTube downloads must only be enabled for content the user is permitted to save and where applicable platform rules allow it.

## Mobile release gates

Before Android or iOS can be called supported:

1. Finish the platform-specific media pipeline, including FFmpeg conversion and a JavaScript challenge runtime where required, without attempting to run arbitrary external executables on iOS.
2. Add app-sandbox file pickers/export flows and platform-specific storage permissions.
3. Implement download lifecycle, resume/cancel semantics, battery/network constraints, and background behaviour.
4. Generate native APK/AAB and iOS simulator/device builds using the official Qt toolchains.
5. Add simulator/emulator tests and physical-device tests for app lifecycle, permission denial, storage exhaustion, network interruption, cancellation, and output-file integrity.
6. Complete signing, privacy disclosures, licensing/third-party notices, and store-policy review.

Android and iOS require separate test evidence. Host-side UI tests and deployment dry-runs are preflight checks only; they are not evidence that downloads run correctly on a real phone.
