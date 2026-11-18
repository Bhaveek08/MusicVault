# iOS app

This folder contains a native SwiftUI/WKWebView shell. The UI assets are bundled locally from mobile/shared/; external navigation is restricted to official Spotify HTTPS links.

## Build for iOS Simulator

Requirements: Xcode 15 or newer and iOS 16+ Simulator runtime.

```bash
xcodebuild -project MusicVault.xcodeproj -scheme MusicVault \
  -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' \
  -derivedDataPath build CODE_SIGNING_ALLOWED=NO build
```

The app product is build/Build/Products/Debug-iphonesimulator/MusicVault.app.

The [Mobile native builds workflow](https://github.com/Bhaveek08/MusicVault/actions/workflows/mobile-build.yml) builds the simulator app, installs and launches it on an iPhone simulator, captures a screenshot, and uploads both the app archive and a standalone Xcode project source bundle.

## Install on a physical iPhone/iPad

The simulator build cannot be installed on a physical device. Open MusicVault.xcodeproj in Xcode, select your Apple Developer Team under Signing & Capabilities, choose a connected device, then build/run. A signed IPA cannot be produced without your developer team and provisioning profile.

## Current scope

This is an installable UI test build. YouTube links can be validated and queued as previews. Media downloading is not connected to iOS yet. Spotify links are handed off to Spotify. The app uses local bundled assets and allows external navigation only to official Spotify HTTPS hosts.
