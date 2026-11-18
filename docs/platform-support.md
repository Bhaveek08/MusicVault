# Platform support and roadmap

## Current support matrix

| Platform | UI/runtime status | Package status | Release status |
| --- | --- | --- | --- |
| Windows 10/11 x64 | PySide6 desktop downloader | Inno Setup per-user installer | Build and packaged smoke test verified in CI; unsigned |
| macOS Apple Silicon | PySide6 desktop downloader | `.app` + `.dmg` | Build and packaged smoke test verified in CI; unsigned/notarized |
| macOS Intel | Not packaged | None | Not currently supported as a release artifact |
| Linux | Source/test environment only | None | No native installer |
| Android | Touch-first UI prototype; phone-sized Qt UI tests on desktop runners | No APK/AAB; Qt Android deploy tool is blocked by its commercial-license credential gate in CI | Not supported |
| iOS/iPadOS | Touch-first UI prototype; phone-sized Qt UI tests and host Xcode/Simulator SDK check | No IPA or simulator app; target PySide6/Shiboken wheels and signing are not provisioned | Not supported |

## Desktop distribution

Windows uses a windowed PyInstaller one-folder payload wrapped in an Inno Setup per-user installer. The app installs under the user's local Programs directory; preferences and logs live in OS-specific app data; downloads default to `Music/MusicVault`. Uninstall does not delete user downloads.

macOS uses a native `.app` bundle and DMG for Apple Silicon. The build creates an ICNS asset from the high-resolution PNG master. The current pipeline is unsigned and not notarized; public distribution requires Developer ID signing, hardened runtime configuration as appropriate, and Apple notarization.

## Mobile prototype scope

The `mobile/` directory contains a touch-first PySide6 UI prototype and URL validation. Host-side tests instantiate the Qt Widgets window at a phone-sized viewport, switch source tabs, exercise the permission/playlist preview queue, and check YouTube/Spotify URL validation. The Qt offscreen renderer is also used to capture review screenshots. These checks run on desktop CI hosts; they do not execute on an Android device or iOS simulator.

The mobile UI's preview queue is local UI state only. It does not download media. The desktop downloader currently uses yt-dlp/yt-dlp-ejs, Deno, and FFmpeg. Those are not drop-in mobile dependencies:

- Qt's iOS deploy tool generates an Xcode project using platform-specific PySide6/Shiboken wheels and a Python.xcframework. The tool documentation states that third-party packages are not automatically supported; packages with C extensions need target-specific cross-compilation and app-bundle integration.
- iOS requires sandbox-compliant file access, native sharing/export handling, app lifecycle/background-task design, privacy-purpose strings, provisioning, and App Store review.
- The Android deploy attempt reached Qt's target-wheel download step but stopped at the Qt deploy tool's commercial-license credential gate on the public runner. The CI job records this as a known blocker; no APK/AAB or target wheel package is claimed. A package build needs licensed deployment credentials, Android SDK/NDK setup, and emulator/physical-device lifecycle, storage, permission, and network tests.

The mobile scope must preserve the desktop source policy: Spotify share links can open in the official app, but protected Spotify streams must not be exported as local media files. YouTube downloads must only be enabled for content the user is permitted to save and where applicable platform rules allow it.

## Mobile release gates

Before Android or iOS can be called supported:

1. Finish the platform-specific media pipeline, including FFmpeg conversion and a JavaScript challenge runtime where required, without attempting to run arbitrary external executables on iOS.
2. Add app-sandbox file pickers/export flows and platform-specific storage permissions.
3. Implement download lifecycle, resume/cancel semantics, battery/network constraints, and background behaviour.
4. Generate native APK/AAB and iOS simulator/device builds using the official Qt toolchains.
5. Add simulator/emulator tests and physical-device tests for app lifecycle, permission denial, storage exhaustion, network interruption, cancellation, and output-file integrity.
6. Complete signing, privacy disclosures, licensing/third-party notices, and store-policy review.

Android and iOS require separate test evidence. Host-side phone-sized UI tests and deployment-readiness checks are preflight only; they are not evidence that downloads run correctly on a real phone. Review PNG screenshots from the `musicvault-ui-previews` artifact in the Mobile UI workflow.
