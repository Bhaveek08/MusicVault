# MusicVault 2.0.2 — QA report

## Release artifacts

The public [v2.0.2 GitHub Release](https://github.com/Bhaveek08/MusicVault/releases/tag/v2.0.2) contains:

| Platform | Asset | Verification | Distribution caveat |
| --- | --- | --- | --- |
| Windows 10/11 x64 | `MusicVault-Setup.exe`, `MusicVault-Windows-x64.zip` | Windows build, packaged `--smoke-test`, and installer compilation passed in [release workflow 44415036837](https://github.com/Bhaveek08/MusicVault/actions/runs/44415036837). | Installer is unsigned. |
| macOS Apple Silicon | `MusicVault-macos-arm64.dmg` | App-bundle smoke test and DMG creation passed in [macOS workflow 44415984028](https://github.com/Bhaveek08/MusicVault/actions/runs/44415984028). | DMG is unsigned and not notarized; Gatekeeper may warn or block it. Intel Macs are not packaged. |
| Android | No production release asset; CI debug APK available as a 30-day artifact | APK installed and Downloads UI rendered on Android 15/API 35 emulator in [mobile build run 44432988433](https://github.com/Bhaveek08/MusicVault/actions/runs/44432988433). | Preview UI only; no download engine, signed AAB, or Play Store build. |
| iOS/iPadOS | No device-installable release asset; CI Simulator app available as a 30-day artifact | Simulator app built, installed, and launched in [mobile build run 44432988433](https://github.com/Bhaveek08/MusicVault/actions/runs/44432988433). | Preview UI only; no download engine, device IPA, TestFlight, or App Store build. |

The Windows release job and macOS package job are independent. The macOS DMG was attached after its successful build. Release assets are not code-signed by the current pipelines.

## Automated regression matrix

Commit [`7dfc8e4`](https://github.com/Bhaveek08/MusicVault/commit/7dfc8e4e6339898726c08194cb2396a0f907ff81) passed the six-job [CI run 44417329152](https://github.com/Bhaveek08/MusicVault/actions/runs/44417329152) and [CodeQL run 44417329198](https://github.com/Bhaveek08/MusicVault/actions/runs/44417329198):

| Runner | Python | Full-suite repetitions | Result |
| --- | --- | ---: | --- |
| Windows latest | 3.11 | 50 | Passed |
| Windows latest | 3.13 | 50 | Passed |
| Ubuntu latest | 3.11 | 50 | Passed |
| Ubuntu latest | 3.13 | 50 | Passed |
| macOS 15 | 3.11 | 50 | Passed |
| macOS 15 | 3.13 | 50 | Passed |

The suite contains 77 pytest cases, including parameterized cases. CI therefore ran 300 complete suite repetitions (23,100 passing test-case executions). These are repeats of the same deterministic tests, not independent test plans or physical-device trials. The desktop Qt test harness explicitly closes and destroys its windows to avoid a PySide process-exit crash.

## What the tests cover

- Safe YouTube video/playlist and Spotify URL acceptance and rejection.
- Queue permission gating, invalid URL errors, playlist-only handling, valid queue add, completion clearing, queue counts, progress, and failed-job state.
- Spotify tab handoff, valid link opening, invalid-link errors, and open failure recovery.
- Visible desktop button geometry at the configured minimum window size and supported format choices.
- Output folder validation, output option construction, format mapping, helper formatting, and app identity.
- Download option constraints that disable cookies, plugins, and remote components.
- Shared Android/iOS WebView UI: all seven buttons have click handlers; YouTube and Spotify tab switching, paste success/failure, permission and playlist gating, invalid links, queue rendering/cap/clear, and Spotify handoff are exercised by the Node interaction suite.

## Platform and security boundaries

- The desktop app downloads only public YouTube sources accepted by its URL policy and requires the user to confirm they own or may save the content. It does not read browser cookies or export protected Spotify streams.
- The automated tests do not perform live media downloads, decode every output format, test installer upgrades/uninstalls on physical devices, or prove every screenreader, DPI, theme, and keyboard path.
- The Android and iOS UIs remain prototypes. Their appearance or host-side validation does not prove native download, background-task, storage, lifecycle, signing, or store behavior.
- No client application can be made cheat-engine-proof. Obfuscation can raise reverse-engineering effort but cannot secure logic running on a user's device.
- Windows and macOS binaries are currently unsigned; macOS also lacks notarization. Public deployment should add trusted signing/notarization and verify downloaded checksums.
- No test suite proves that software has zero defects.
- Android and iOS UI shells have native simulator/emulator launch evidence, but they are not complete mobile downloaders and have not been validated on physical devices.
