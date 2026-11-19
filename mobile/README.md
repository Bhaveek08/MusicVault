# MusicVault mobile clients

## Current status

Android and iOS each have a native container that displays the shared local HTML/CSS/JavaScript UI:

- Android: Java `WebView` with AndroidX `WebViewAssetLoader`.
- iOS: SwiftUI with `WKWebView` and bundled local UI assets.
- `mobile/app/main.py`: a separate PySide6 prototype used for host-side UI previews and tests; it is not the Android/iOS client.

The app's preview queue is only local UI state. Neither native client has a media download engine connected. Do not describe these prototypes as functional mobile downloaders or production store releases.

## Build status

- **Android:** CI builds an unsigned debug APK, installs it on an Android 15/API 35 emulator, verifies that the WebView rendered the Downloads screen, captures a screenshot, and uploads a 30-day Actions artifact. See [successful native build run 44432988433](https://github.com/Bhaveek08/MusicVault/actions/runs/44432988433). There is no signed AAB or Play Store release.
- **iOS:** CI builds, installs, and launches the unsigned iOS Simulator app, then uploads a Simulator archive and Xcode project source. The same run above passed. There is no device IPA, TestFlight build, or App Store release.

## Download and install the Android test APK

Open the [Mobile native builds workflow](https://github.com/Bhaveek08/MusicVault/actions/workflows/mobile-build.yml), choose a successful run, and download the `MusicVault-Android-test-build` artifact. Extract it, then install the debug APK on an Android 7.0+ device with USB debugging enabled:

```bash
adb install -r MusicVault-Android-debug.apk
```

This installs a **UI prototype**. It can validate YouTube links and show preview queue rows. It cannot download media.

## Build the Android shell locally

Requirements: JDK 17, Android SDK platform/build tools 35, and Gradle 8.9.

From the repository root:

```bash
cd mobile/android
gradle assembleDebug
```

The debug APK is written to `app/build/outputs/apk/debug/app-debug.apk`.

## Run the iOS Simulator shell locally

On macOS with Xcode installed, open `ios/MusicVault.xcodeproj`, select the `MusicVault` scheme and an iPhone Simulator, then build and run. For a device build, configure an Apple Developer Team and signing in Xcode. A simulator app archive cannot be installed on an iPhone.

## Security boundaries

The WebViews load bundled local content. The mobile shell does not load remote YouTube pages or execute the desktop downloader, and blocks external navigation. Android's INTERNET permission supports its local HTTPS WebView asset origin; the WebView blocks other network resources, file URL access, mixed content, cleartext traffic, and backup. Neither client requests storage permissions because downloads are not implemented.

## Release requirements still open

Before enabling mobile downloads, implement and test a platform-appropriate media pipeline, file export and permissions, lifecycle and background behavior, resume/cancel behavior, and output integrity. Then add emulator/Simulator and physical-device tests, signed distribution builds, privacy disclosures, and store-policy review. Do not reuse the desktop yt-dlp/Deno/FFmpeg bundle without resolving platform compatibility and service-rule constraints.
