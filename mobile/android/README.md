# Android app

This folder contains the native Android WebView shell. It loads the shared offline UI from mobile/shared/ through AndroidX WebViewAssetLoader on the appassets HTTPS origin. The app has the normal INTERNET permission so WebView can use this HTTPS asset origin, but its WebView blocks all non-appassets network resources and only hands official Spotify HTTPS links to the Spotify app or Android link handler.

## Build a debug APK

Requirements: Android Studio or Android SDK, JDK 17, Android platform 35, and Gradle 8.9.

From the repository root:

```bash
cd mobile/android
gradle assembleDebug
```

APK output: app/build/outputs/apk/debug/app-debug.apk.

Install with adb install -r app/build/outputs/apk/debug/app-debug.apk.

The [Mobile native builds workflow](https://github.com/Bhaveek08/MusicVault/actions/workflows/mobile-build.yml) builds this APK and launches it on an Android emulator. Download the MusicVault-Android-test-build artifact to obtain the APK and emulator screenshot.

## Current scope

This is an installable UI test build. YouTube links can be validated and queued as previews. Media downloading is not connected to Android yet. Spotify links are handed off to the Spotify app or Android's link handler. The app requests INTERNET for the local HTTPS WebView asset origin, but does not request storage or media permissions.

## Security

- No remote page content is loaded into the WebView.
- AndroidX WebViewAssetLoader serves app assets through a local HTTPS origin.
- Mixed content, arbitrary external navigation, file URL access, and universal file URL access are disabled.
- External navigation is allowlisted to official Spotify HTTPS hosts.
- Backup and cleartext networking are disabled.
