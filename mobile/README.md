# Mobile workstream

This directory contains the first touch-first MusicVault UI shell for Android and iOS.

## Status

- The UI shell is an early prototype. It is not a released Android or iOS app.
- Automated desktop-host UI tests check the mobile layout at phone-sized viewports, tab selection, and URL validation.
- The preview queue is local UI state only. It does not start a media download.
- The desktop downloader is deliberately not imported into this shell.

## Why downloads are not enabled yet

The desktop app's media path relies on yt-dlp/yt-dlp-ejs, a Deno executable, and FFmpeg. Those components cannot simply be copied into an iOS app bundle. Qt's current iOS deploy tool documents that third-party packages are not yet automatically packaged; Python C extensions need target-specific cross-compilation and native bundling. iOS also requires app-sandbox-compatible media storage and native background task design.

The mobile workstream therefore has a separate entry point with no download engine. It must not be presented as a functional downloader until the complete media pipeline has been ported and validated on real devices.

## Local UI check

Install the pinned desktop runtime dependencies and run:

```bash
python -m pip install -r requirements-test.txt
QT_QPA_PLATFORM=offscreen python -m pytest -q tests/test_mobile_ui.py
python mobile/app/main.py --smoke-test
```

## Native deployment prerequisites

Android deployment uses Qt for Python's `pyside6-android-deploy` tool on a Linux or macOS host, an Android SDK/NDK, and Qt Android wheels for the target ABI.

iOS deployment uses `pyside6-ios-deploy` on macOS with Xcode, a Python.xcframework, and matching PySide6/Shiboken6 wheels for the iOS device or simulator target. The tool generates an Xcode project; Xcode performs the build and signing.

See [Qt for Python Android deployment](https://doc.qt.io/qtforpython-6/deployment/deployment-pyside6-android-deploy.html) and [iOS deployment](https://doc.qt.io/qtforpython-6/deployment/deployment-pyside6-ios-deploy.html).
