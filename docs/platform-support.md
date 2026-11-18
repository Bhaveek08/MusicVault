# Platform support and roadmap

## Current support matrix

| Platform | UI/runtime status | Package status | Release status |
| --- | --- | --- | --- |
| Windows 10/11 x64 | PySide6 desktop downloader | Inno Setup per-user installer | Build and packaged smoke test verified in CI; unsigned |
| macOS Apple Silicon | PySide6 desktop downloader | `.app` + `.dmg` | Build and packaged smoke test verified in CI; unsigned/notarized |
| macOS Intel | Not packaged | None | Not currently supported as a release artifact |
| Linux | Source/test environment only | None | No native installer |
| Android | Native Java WebView shell using shared local HTML/CSS/JS; download UI is preview-only | Debug APK builds and is uploaded as a 30-day Actions test artifact; latest emulator install smoke test failed with ADB `Broken pipe` after emulator boot timeout | Prototype only; not a public release |
| iOS/iPadOS | Native SwiftUI/WKWebView shell using shared local HTML/CSS/JS; download UI is preview-only | Unsigned iOS Simulator app archive builds and launches in CI; no device IPA | Prototype only; not a public release |

## Desktop distribution

Windows uses a windowed PyInstaller one-folder payload wrapped in an Inno Setup per-user installer. The app installs under the user's local Programs directory; preferences and logs live in OS-specific app data; downloads default to `Music/MusicVault`. Uninstall does not delete user downloads.

macOS uses a native `.app` bundle and DMG for Apple Silicon. The build creates an ICNS asset from the high-resolution PNG master. The current pipeline is unsigned and not notarized; public distribution requires Developer ID signing, hardened runtime configuration as appropriate, and Apple notarization.

## Mobile prototype scope

The native Android and iOS apps are small Java/WebView and SwiftUI/WKWebView shells that load the shared local HTML/CSS/JS. The separate `mobile/app/main.py` PySide6 prototype is used for host-side layout previews and URL-policy tests; it is not the native mobile application. The shared preview queue is local UI state only and does not download media.

Automated URL-policy tests run on desktop CI hosts. Real Qt prototype screenshots are rendered under Xvfb in the Mobile UI workflow; they are not screenshots of the native WebView apps. The desktop downloader currently uses yt-dlp/yt-dlp-ejs, Deno, and FFmpeg. Those are not drop-in mobile dependencies:

- Qt's iOS deploy tool generates an Xcode project using platform-specific PySide6/Shiboken wheels and a Python.xcframework. The tool documentation states that third-party packages are not automatically supported; packages with C extensions need target-specific cross-compilation and app-bundle integration.
- iOS requires sandbox-compliant file access, native sharing/export handling, app lifecycle/background-task design, privacy-purpose strings, provisioning, and App Store review.
- The current Android Gradle workflow builds a debug APK and uploads it as a temporary test artifact. Its emulator smoke test currently fails because the hosted emulator does not become usable before ADB disconnects; KVM acceleration has been enabled to retry this. The artifact is not a production downloader or Play Store build.
- The iOS workflow builds and launches an unsigned Simulator app and uploads a simulator archive plus project source. This is not a device IPA or App Store build. Device distribution requires provisioning, signing, privacy disclosures, and store review.

The mobile scope must preserve the desktop source policy: Spotify share links can open in the official app, but protected Spotify streams must not be exported as local media files. YouTube downloads must only be enabled for content the user is permitted to save and where applicable platform rules allow it.

## Mobile release gates

Before Android or iOS can be called supported:

1. Finish the platform-specific media pipeline, including FFmpeg conversion and a JavaScript challenge runtime where required, without attempting to run arbitrary external executables on iOS.
2. Add app-sandbox file pickers/export flows and platform-specific storage permissions.
3. Implement download lifecycle, resume/cancel semantics, battery/network constraints, and background behaviour.
4. Make the Android emulator smoke test reliable; then add physical-device tests for lifecycle, permission denial, storage exhaustion, network interruption, cancellation, and output-file integrity.
5. Produce signed Android App Bundle and iOS device IPA packages using the native Gradle/Xcode projects, and validate installation on real devices.
6. Complete signing, privacy disclosures, licensing/third-party notices, and store-policy review.

Android and iOS require separate test evidence. Host-side Qt prototype tests, an Android debug APK, and iOS Simulator launch checks do not prove that downloads run correctly on real phones. Review PNG screenshots from the `musicvault-ui-previews` artifact in the Mobile UI workflow.
