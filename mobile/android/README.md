# Android target

The Android target currently uses the shared touch-first UI prototype in `../app/main.py`.

Status: UI shell and host-side tests only. No APK/AAB is currently published, and downloads are not enabled.

Before calling Android supported, CI must generate and build an arm64-v8a APK/AAB with the official Qt for Python deployment tool, then install it on an emulator and run navigation, rotation, URL validation, app lifecycle, storage-permission, background/resume, and media-output tests.
