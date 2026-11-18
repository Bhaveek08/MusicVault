# MusicVault mobile apps

This directory contains the native Android and iOS shells and the shared mobile interface.

## What is implemented

- **Android:** native Java Activity hosting the bundled interface in an Android WebView.
- **iOS:** SwiftUI app hosting the same bundled interface in WKWebView.
- **Shared UI:** offline HTML/CSS/JavaScript in `mobile/shared/`; the phone platforms use the same layout and client-side validation.
- **Spotify:** validated official Spotify HTTPS share links are handed to the Spotify app or system.
- **YouTube:** links can be validated and staged in a local preview queue.
- **Privacy:** the app interface is packaged locally; it does not load a remote web page as its UI.

## What is not implemented yet

Mobile media downloads are disabled. The desktop media pipeline depends on yt-dlp/yt-dlp-ejs, Deno and FFmpeg. It has not been ported to mobile app sandboxes, storage APIs or background execution. The mobile queue is preview-only and does not download media. Do not treat this test build as a functional mobile downloader.

## Download and test the latest builds

Open the [Mobile native builds workflow](https://github.com/Bhaveek08/MusicVault/actions/workflows/mobile-build.yml), select a successful run, then download:

- `MusicVault-Android-test-build`: debug APK and Android/shared source.
- `MusicVault-Android-emulator-verification`: screenshot captured after the native WebView confirms the shared UI is initialized.
- `MusicVault-iOS-test-build`: iOS Simulator app archive, Xcode project source and simulator screenshot.

CI artifacts are temporary test outputs (30-day retention). The APK is debug-signed for testing, not signed for Play Store release. The iOS app archive targets the iOS Simulator and cannot be installed on a physical iPhone/iPad.

## Install on Android

The Android project declares a minimum API level of 24 (Android 7.0+), subject to the device's installed WebView provider.

1. Download and extract the `MusicVault-Android-test-build` artifact.
2. Transfer `MusicVault-Android-debug.apk` to your phone.
3. Open the APK and allow installation from that file source if Android asks.
4. Launch MusicVault. The YouTube and Spotify tabs should appear; downloads are marked as not connected.

For a USB-connected device with Android Platform Tools installed:

```bash
adb install -r MusicVault-Android-debug.apk
adb shell am start -n com.musicvault.mobile/.MainActivity
```

To build from source, open `mobile/android/` in Android Studio with JDK 17, Android SDK Platform 35 and Gradle 8.9, or run:

```bash
cd mobile/android
gradle --no-daemon assembleDebug
```

The APK is produced at `app/build/outputs/apk/debug/app-debug.apk`.

## Run on iOS

On a Mac with Xcode:

1. Extract `MusicVault-iOS-test-build`.
2. Extract `MusicVault-iOS-Xcode-project.zip`.
3. Open `mobile/ios/MusicVault.xcodeproj` in Xcode.
4. Select the `MusicVault` scheme and an iPhone/iPad simulator, then Run.

The included `MusicVault-iOS-Simulator.app.zip` is a prebuilt simulator app for inspection/testing on the simulator. It is not an iOS device package.

For a physical iPhone/iPad, connect the device, choose your Apple Developer Team in **Signing & Capabilities**, set a bundle identifier that your team controls, then build and run from Xcode. An IPA signed for your device requires your Apple signing identity and provisioning profile; the simulator CI build cannot create that on your behalf.

## End-to-end verification

The native workflow builds the Android debug APK, installs it on an Android emulator, forces SwiftShader software rendering for the hosted emulator, waits for a native WebView readiness signal emitted only after the shared JavaScript initializes and the expected controls/theme are present, and then saves a screenshot. It separately builds the iOS Simulator app, installs it on an iPhone simulator, launches it, and saves a screenshot.

A successful emulator/simulator run verifies the app shell and shared UI—not physical-device behaviour, store signing or media downloading. Test on your actual devices before release.
