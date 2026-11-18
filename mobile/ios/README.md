# iOS target

The iOS target currently uses the shared touch-first UI prototype in `../app/main.py`.

Status: UI shell and host-side tests only. No IPA/App Store package is currently published, and downloads are not enabled.

Before calling iOS supported, CI must generate an Xcode project using matching iOS simulator wheels, build and launch it in an iOS simulator, and later validate a signed device build. Device release additionally requires an Apple Developer Team ID, provisioning, privacy-purpose strings, app-sandbox file handling, background-task design, and App Review qualification.
