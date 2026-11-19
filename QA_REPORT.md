# MusicVault 2.0.6 — QA report

## Release downloads

The [v2.0.6 GitHub Release](https://github.com/Bhaveek08/MusicVault/releases/tag/v2.0.6) provides direct desktop downloads:

| Platform | Asset | Verification | Distribution caveat |
| --- | --- | --- | --- |
| Windows 10/11 x64 | [`MusicVault-Setup.exe`](https://github.com/Bhaveek08/MusicVault/releases/latest/download/MusicVault-Setup.exe) and [portable ZIP](https://github.com/Bhaveek08/MusicVault/releases/latest/download/MusicVault-Windows-x64.zip) | [Tagged Windows build 44575120326](https://github.com/Bhaveek08/MusicVault/actions/runs/44575120326) passed the 50-pass QA gate, packaging, and upload. The installed v2.0.6 app launched and responded on Windows; its installer SHA-256 matched GitHub's asset digest. | Installer is unsigned. |
| macOS Apple Silicon | [`MusicVault-macos-arm64.dmg`](https://github.com/Bhaveek08/MusicVault/releases/latest/download/MusicVault-macos-arm64.dmg) | [Tagged macOS build 44575120208](https://github.com/Bhaveek08/MusicVault/actions/runs/44575120208) passed and attached the disk image. | Unsigned and not notarized; Gatekeeper may warn or block it. Intel Macs are not packaged. |
| Linux x86_64 | [`MusicVault-Linux-x86_64.tar.gz`](https://github.com/Bhaveek08/MusicVault/releases/latest/download/MusicVault-Linux-x86_64.tar.gz) | [Tagged Linux build 44575120216](https://github.com/Bhaveek08/MusicVault/actions/runs/44575120216) passed its portable build and smoke check, then attached the package. | Host Qt/X11 runtime libraries are required. |
| Android | No production release asset | Debug APK installed and the Downloads page rendered on an Android 15/API 35 emulator in [run 44436830729](https://github.com/Bhaveek08/MusicVault/actions/runs/44436830729). | UI prototype only; no media engine, signed AAB, or Play Store build. |
| iOS/iPadOS | No device-installable release asset | Simulator app built, installed, and launched in [run 44436830729](https://github.com/Bhaveek08/MusicVault/actions/runs/44436830729). | UI prototype only; no media engine, signed device IPA, TestFlight, or App Store build. |

The mobile clients validate YouTube links and stage a local preview queue. Mobile downloading is intentionally disabled until a source authorization pathway, platform-compatible engine, sandbox file export, lifecycle behavior, signing, and store review are resolved. Emulator and Simulator checks are not physical-device tests.

## Regression and security checks

For v2.0.6, all 58 pytest cases passed locally. The six-job [CI run 44573923961](https://github.com/Bhaveek08/MusicVault/actions/runs/44573923961) passed on Windows, macOS 15, and Ubuntu with Python 3.11 and 3.13. [CodeQL run 44573924007](https://github.com/Bhaveek08/MusicVault/actions/runs/44573924007) passed. [Mobile UI run 44573924009](https://github.com/Bhaveek08/MusicVault/actions/runs/44573924009) passed, including the source-policy and interaction checks. [Native mobile build run 44573924123](https://github.com/Bhaveek08/MusicVault/actions/runs/44573924123) passed Android emulator and iOS Simulator build/launch checks.

The v2.0.6 desktop preview shows the app window at 1200 × 900; the mobile prototype preview is touch-first at 390 × 844. Android and iOS native clients remain prototypes, as described above.

Test coverage includes strict YouTube URL handling and Spotify-source rejection, permission and playlist gating, invalid-input errors, clipboard success/failure, folder selection and cancellation, queue capacity and clearing, progress/failure states, download/stop control wiring, minimum-height button/card geometry, non-overlapping columns, long-path elision, format selection, output-folder validation, and downloader option constraints. Shared mobile UI tests cover each remaining interactive control and recoverable error cases.

## Limits

- No live media download was tested. Tests do not decode every format, exercise installer upgrade/uninstall on physical systems, or prove every DPI, accessibility, keyboard, and screen-reader path.
- MusicVault does not bypass DRM, private or account-gated content, or browser sessions. A checkbox does not replace service authorization or rights-holder permission.
- Android and iOS are not functional media downloaders or store-ready products. The mobile queue is preview-only.
- Windows and macOS installers are unsigned; macOS is also not notarized. Public distribution may show OS trust warnings.
- No client app can be made cheat-engine-proof. Open-source code can be inspected and modified; obfuscation cannot protect logic running on a user's device.
- A green test suite is evidence for the tested paths, not proof of zero defects or physical-device compatibility.
