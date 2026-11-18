# Contributing

Thank you for considering a contribution to MusicVault. Keep changes focused, explain the user impact, and preserve the application's conservative source and security boundaries.

## Before opening an issue

- Search existing issues for the same problem.
- Include the MusicVault version, OS version/architecture, and Python version when relevant.
- Include the exact steps to reproduce the problem and the expected versus actual result.
- Remove links, usernames, local paths, tokens, and other private information from logs or screenshots.
- Do not report security vulnerabilities in a public issue; follow [SECURITY.md](SECURITY.md).

## Development setup

MusicVault targets Windows x64 and has an experimental macOS Apple Silicon build. Python 3.11 or newer is required for development and packaging.

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-test.txt
```

Run the application with `python musicvault_app.py` and run tests with:

```powershell
python -m pytest -q
```

To run the release gate locally:

```powershell
python run_release_qa.py
```

## Change guidelines

- Keep URL validation strict. Do not broaden source support without documenting and testing the security implications.
- Do not add browser-cookie extraction, credential collection, arbitrary downloader plugins, remote code loading, or platform-control circumvention.
- Never pass pasted URLs or other untrusted text to a shell command.
- Keep diagnostic messages free of URLs, credentials, cookies, and other sensitive values.
- Preserve safe output handling, playlist/queue bounds, cancellation behavior, and no-overwrite defaults.
- Update documentation, tests, version metadata, and `THIRD_PARTY_NOTICES.txt` when a change affects them.
- Do not commit build outputs, virtual environments, logs, caches, local configuration, or downloaded tool binaries.

## Pull requests

A pull request should include:

1. A concise problem statement and explanation of the chosen change.
2. Tests covering the behavior and relevant failure cases.
3. Documentation updates for user-visible or operational changes.
4. A note about any platform-specific checks not run locally.

Keep one logical change per pull request. Do not describe a feature as tested on a platform unless it was actually run there. Do not claim Android/iOS compatibility based on desktop unit tests.
