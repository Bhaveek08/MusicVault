# Mobile workstream

This directory contains the first touch-first MusicVault UI shell for Android and iOS.

## Status

- The UI shell is an early prototype. It is not a released Android or iOS app.
- Automated host-side tests check the mobile UI source structure and YouTube/Spotify URL validation. They do not render a native phone UI.
- The preview queue is local UI state only. It does not start a media download.
- The desktop downloader is deliberately not imported into this shell.

## Why downloads are not enabled yet

The desktop app's media path relies on yt-dlp/yt-dlp-ejs, a Deno executable, and FFmpeg. Those components cannot simply be copied into an iOS app bundle. Qt's current iOS deploy tool documents that third-party packages are not yet automatically packaged; Python C extensions need target-specific cross-compilation and native bundling. iOS also requires app-sandbox-compatible media storage and native background task design.

The mobile workstream therefore has a separate entry point with no download engine. It must not be presented as a functional downloader until the complete media pipeline has been ported and validated on real devices.

## Local UI check

Install the pinned desktop runtime dependencies and run:

```bash
python -m pip install -r requirements-test.txt
python -m pytest -q tests/test_mobile_ui.py
python mobile/app/main.py
```

## Native deployment prerequisites

Android deployment uses Qt for Python's `pyside6-android-deploy` tool on a Linux or macOS host, an Android SDK/NDK, and Qt Android wheels for the target ABI.

iOS deployment uses `pyside6-ios-deploy` on macOS with Xcode, a Python.xcframework, and matching PySide6/Shiboken6 wheels for the iOS device or simulator target. The tool generates an Xcode project; Xcode performs the build and signing.

See [Qt for Python Android deployment](https://doc.qt.io/qtforpython-6/deployment/deployment-pyside6-android-deploy.html) and [iOS deployment](https://doc.qt.io/qtforpython-6/deployment/deployment-pyside6-ios-deploy.html).


## UI review screenshots

The Mobile UI workflow generates four PNGs from the real Qt widgets, using the current source code:

- Desktop YouTube tab — 1200 × 820
- Desktop Spotify tab — 1200 × 820
- Mobile YouTube prototype — 390 × 844
- Mobile Spotify prototype — 390 × 844

Open the latest [Mobile UI workflow run](https://github.com/Bhaveek08/MusicVault/actions/workflows/mobile.yml) and download the `musicvault-ui-previews` artifact. These are actual Qt widget renders created under a virtual X11 desktop. They are not Android/iOS device screenshots.

## Current native build blockers

- **Android:** the CI attempt to obtain Qt Android target wheels reached a commercial-license credential gate. No native APK/AAB is generated. The workflow reports this blocker without marking host-side UI tests as failed.
- **iOS:** the CI runner verifies Xcode and the iOS Simulator SDK, but matching target PySide6/Shiboken wheels, app signing and a simulator app build are not yet configured.

## Native test builds

- **Android:** open the android/ folder as a Gradle project in Android Studio, or download the latest `MusicVault-Android-test-build` artifact from [Mobile native builds](https://github.com/Bhaveek08/MusicVault/actions/workflows/mobile-build.yml). Install the `MusicVault-Android-debug.apk` on Android 9 or later. This is an unsigned debug APK for testing, not a Play Store release.
- **iOS:** open `ios/MusicVault.xcodeproj` in Xcode and run the `MusicVault` scheme on an iOS 16+ simulator. The workflow artifact contains a simulator app archive and a standalone Xcode project source bundle. For a real iPhone/iPad, select your Apple Developer Team in Xcode and build/sign locally; the simulator archive is not a device IPA.

Both clients use the same local HTML/CSS/JS UI. They only allow external navigation to official Spotify HTTPS links. Neither client has the yt-dlp/FFmpeg download engine connected.
