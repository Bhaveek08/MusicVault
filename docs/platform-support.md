# Platform support and roadmap

## Current support matrix

| Platform | UI/runtime status | Package status | Release status |
| --- | --- | --- | --- |
| Windows 10/11 x64 | PySide6 desktop downloader | Inno Setup per-user installer | Build and packaged smoke test verified in CI; unsigned |
| macOS Apple Silicon | PySide6 desktop downloader | `.app` + `.dmg` | Build and packaged smoke test verified in CI; unsigned and not notarized |
| macOS Intel | Not packaged | None | Not currently supported as a release artifact |
| Linux | PySide6 desktop downloader | Portable `.tar.gz` Actions artifact | Build and packaged smoke test verified in [CI run 44418085251](https://github.com/Bhaveek08/MusicVault/actions/runs/44418085251); not attached to a public release |
| Android | Native Java WebView shell using shared local HTML/CSS/JS; download UI is preview-only | Debug APK installed and rendered the Downloads screen on an Android 15/API 35 emulator in [run 44432988433](https://github.com/Bhaveek08/MusicVault/actions/runs/44432988433); test artifact retained 30 days | Prototype only; not a public release |
| iOS/iPadOS | Native SwiftUI/WKWebView shell using shared local HTML/CSS/JS; download UI is preview-only | Unsigned iOS Simulator app built, installed, and launched in [run 44432988433](https://github.com/Bhaveek08/MusicVault/actions/runs/44432988433); no device IPA | Prototype only; not a public release |

## Desktop distribution

Windows uses a windowed PyInstaller one-folder payload wrapped in an Inno Setup per-user installer. The app installs under the user's local Programs directory; preferences and logs live in OS-specific app data; downloads default to `Music/MusicVault`. Uninstall does not delete user downloads.

macOS uses a native `.app` bundle and DMG for Apple Silicon. The build creates an ICNS asset from the high-resolution PNG master. The current pipeline is unsigned and not notarized; public distribution requires Developer ID signing, hardened runtime configuration as appropriate, and Apple notarization.

## Mobile prototype scope

The native Android and iOS apps are small Java/WebView and SwiftUI/WKWebView shells that load the shared local HTML/CSS/JS. The separate `mobile/app/main.py` PySide6 prototype is used for host-side layout previews and URL-policy tests; it is not the native mobile application. The shared preview queue is local UI state only and does not download media.

Automated URL-policy tests run on desktop CI hosts. Real Qt prototype screenshots are rendered under Xvfb in the Mobile UI workflow; they are not screenshots of the native WebView apps. The desktop downloader currently uses yt-dlp/yt-dlp-ejs, Deno, and FFmpeg. Those are not drop-in mobile dependencies:

- Qt's iOS deploy tool generates an Xcode project using platform-specific PySide6/Shiboken wheels and a Python.xcframework. The tool documentation states that third-party packages are not automatically supported; packages with C extensions need target-specific cross-compilation and app-bundle integration.
- iOS requires sandbox-compliant file access, native sharing/export handling, app lifecycle/background-task design, privacy-purpose strings, provisioning, and App Store review.
- The current Android Gradle workflow builds a debug APK, installs it on an emulator, verifies rendered page text, captures a screenshot, and uploads a temporary test artifact. KVM acceleration fixed the hosted emulator boot issue. The artifact is not a production downloader or Play Store build.
- The iOS workflow builds and launches an unsigned Simulator app and uploads a simulator archive plus project source. This is not a device IPA or App Store build. Device distribution requires provisioning, signing, privacy disclosures, and store review.

Spotify is not offered as a source in any client. Spotify links are rejected if pasted into the YouTube input. YouTube downloads must only be enabled for content the user is permitted to save and where applicable platform rules allow it.

### Third-party source authorization is a release gate

YouTube's [Terms of Service](https://www.youtube.com/t/terms) restrict downloading Service content except where the Service expressly authorizes it, the relevant rights holders give prior written permission, or applicable law permits it. Apple's [App Review Guideline 5.2.3](https://developer.apple.com/app-store/review/guidelines/#intellectual-property) specifically addresses saving, converting, or downloading third-party audio/video and requires explicit authorization from the source. Google Play's [Intellectual Property policy](https://support.google.com/googleplay/android-developer/answer/9888072) prohibits infringement and apps that encourage it. A user's confirmation that they own a video does not, by itself, demonstrate authorization from the source service. Before adding a mobile download engine or submitting a store build, document the authorized source/API pathway; otherwise keep mobile focused on user-imported files and official service handoff.

## Mobile release gates

Before Android or iOS can be called supported:

1. Finish the platform-specific media pipeline, including FFmpeg conversion and a JavaScript challenge runtime where required, without attempting to run arbitrary external executables on iOS.
2. Add app-sandbox file pickers/export flows and platform-specific storage permissions.
3. Implement download lifecycle, resume/cancel semantics, battery/network constraints, and background behaviour.
4. Add physical-device tests for lifecycle, permission denial, storage exhaustion, network interruption, cancellation, and output-file integrity; automate the shared UI interactions on both native clients.
5. Produce signed Android App Bundle and iOS device IPA packages using the native Gradle/Xcode projects, and validate installation on real devices.
6. Complete signing, privacy disclosures, licensing/third-party notices, and store-policy review.

Android and iOS require separate test evidence. The Android emulator screenshot and iOS Simulator screenshot verify the current UI shell only; neither proves downloads work on real phones. Review the platform screenshots in the `MusicVault-Android-emulator-verification` and `MusicVault-iOS-test-build` artifacts from the linked run.
