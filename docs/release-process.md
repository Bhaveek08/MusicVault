# Release process

A source-level test pass is necessary but not sufficient for a desktop release.

## Before tagging

- [ ] Review the diff and update `CHANGELOG.md`.
- [ ] Update `APP_VERSION`, `pyproject.toml`, Windows version metadata, and `installer/MusicVault.iss`.
- [ ] Review pinned runtime/build dependencies and upstream notices.
- [ ] Run `python -m pytest -q` and `python run_release_qa.py`.
- [ ] Run the deterministic URL fuzz suite and review `QA_REPORT.md`.
- [ ] Check that build outputs, virtual environments, caches, local configuration, and secrets are absent from the repository.

## Windows release validation

On a clean Windows 10/11 x64 machine:

- [ ] Install Python 3.11+ and Inno Setup 6.
- [ ] Run `build_windows.bat` from a clean checkout.
- [ ] Confirm the Deno checksum verification succeeds.
- [ ] Confirm the PyInstaller one-folder/windowed build and packaged smoke test pass.
- [ ] Confirm `MusicVault-Setup.exe` compiles and installs without a console window.
- [ ] Check Start Menu and optional desktop shortcuts.
- [ ] Upgrade an earlier install and verify the install directory does not accumulate stale binaries.
- [ ] Uninstall and confirm program files/shortcuts are removed while user downloads and preferences are preserved.
- [ ] Exercise URL validation, YouTube and Spotify tabs, format selection, folder selection, queue addition/removal, cancellation, and clean exit.
- [ ] Test permitted public sample media only where platform rules and rights allow.
- [ ] Scan the installer and record SHA-256. Verify signing status; never claim a signature unless verified.

## macOS release validation

On a clean Apple Silicon Mac:

- [ ] Run `build_macos.sh`.
- [ ] Open the `.app` from the DMG and move it to Applications.
- [ ] Test on a fresh standard user account.
- [ ] Verify the app starts without Terminal, persists preferences under Application Support, and writes downloads only to the selected folder.
- [ ] Test screen sizes, app icon, Finder/Spotlight integration, and uninstallation by removing the app bundle.
- [ ] Verify the code-signing and notarization status before public distribution.

Intel Mac, Linux packaged, Android, and iOS releases remain unsupported until separate builds and tests are added.

## Publishing

- [ ] Publish source only after review of license status and third-party notices.
- [ ] Attach Windows/macOS installers only after the relevant platform validation is complete.
- [ ] Include checksums and release notes.
- [ ] State tested OS versions/architectures and all unverified areas.
- [ ] Never upload signing keys, tokens, local paths, private URLs, or test media.
