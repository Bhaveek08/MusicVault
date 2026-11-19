# MusicVault 2.0.4 — QA report

## Release downloads

The [v2.0.4 GitHub Release](https://github.com/Bhaveek08/MusicVault/releases/tag/v2.0.4) provides direct desktop downloads:

| Platform | Asset | Verification | Distribution caveat |
| --- | --- | --- | --- |
| Windows 10/11 x64 | [`MusicVault-Setup.exe`](https://github.com/Bhaveek08/MusicVault/releases/latest/download/MusicVault-Setup.exe) and portable ZIP | Tagged Windows build, packaged smoke test, and Inno Setup compilation passed in [run 44479710634](https://github.com/Bhaveek08/MusicVault/actions/runs/44479710634). | Installer is unsigned. |
| macOS Apple Silicon | [`MusicVault-macos-arm64.dmg`](https://github.com/Bhaveek08/MusicVault/releases/latest/download/MusicVault-macos-arm64.dmg) | App-bundle smoke test and DMG creation passed in [run 44479710360](https://github.com/Bhaveek08/MusicVault/actions/runs/44479710360). | Unsigned and not notarized; Gatekeeper may warn or block it. Intel Macs are not packaged. |
| Linux x86_64 | [`MusicVault-Linux-x86_64.tar.gz`](https://github.com/Bhaveek08/MusicVault/releases/latest/download/MusicVault-Linux-x86_64.tar.gz) | Portable build and packaged GUI smoke test passed in [run 44479710502](https://github.com/Bhaveek08/MusicVault/actions/runs/44479710502). | Host Qt/X11 runtime libraries are required. |
| Android | No production release asset | Debug APK installed and the Downloads page rendered on an Android 15/API 35 emulator in [run 44436830729](https://github.com/Bhaveek08/MusicVault/actions/runs/44436830729). | UI prototype only; no media engine, signed AAB, or Play Store build. |
| iOS/iPadOS | No device-installable release asset | Simulator app built, installed, and launched in [run 44436830729](https://github.com/Bhaveek08/MusicVault/actions/runs/44436830729). | UI prototype only; no media engine, signed device IPA, TestFlight, or App Store build. |

The mobile clients validate links, stage a local preview queue, and hand official Spotify links to Spotify. Mobile downloading is intentionally disabled until a source authorization pathway, platform-compatible engine, sandbox file export, lifecycle behavior, signing, and store review are resolved. Emulator and Simulator checks are not physical-device tests.

## Regression and security checks

For the v2.0.4 source, all 86 pytest cases passed locally and the release QA runner passed 50 consecutive runs on Windows. The previous v2.0.3 six-job [CI run 44478916414](https://github.com/Bhaveek08/MusicVault/actions/runs/44478916414) passed on Windows, macOS 15, and Ubuntu with Python 3.11 and 3.13. The [CodeQL run 44478916468](https://github.com/Bhaveek08/MusicVault/actions/runs/44478916468) also passed for that earlier source revision.

The [Mobile UI run 44478916403](https://github.com/Bhaveek08/MusicVault/actions/runs/44478916403) passed source-policy checks, shared WebView button/error interaction checks on Windows and Ubuntu, and target-readiness checks for the previous source revision. Current desktop UI previews show the visible app window at 1200 × 900; mobile previews are touch-first at 390 × 844.

Test coverage includes strict YouTube and Spotify URL handling, permission and playlist gating, invalid-input errors, clipboard success/failure, folder selection and cancellation, queue capacity and clearing, progress/failure states, download/stop control wiring, authorized-storefront link actions, minimum-height button/card geometry, non-overlapping columns, long-path elision, format selection, output-folder validation, and downloader option constraints. The shared mobile UI tests cover all seven interactive controls and recoverable error cases.

## Limits

- No live media download was tested. Tests do not decode every format, exercise installer upgrade/uninstall on physical systems, or prove every DPI, accessibility, keyboard, and screen-reader path.
- MusicVault does not bypass DRM, private or account-gated content, or browser sessions. A checkbox does not replace service authorization or rights-holder permission.
- Android and iOS are not functional media downloaders or store-ready products. The mobile queue is preview-only.
- Windows and macOS installers are unsigned; macOS is also not notarized. Public distribution may show OS trust warnings.
- No client app can be made cheat-engine-proof. Open-source code can be inspected and modified; obfuscation cannot protect logic running on a user's device.
- A green test suite is evidence for the tested paths, not proof of zero defects or physical-device compatibility.
