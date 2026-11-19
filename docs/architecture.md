# Architecture

MusicVault is a local-first PySide6 desktop application. URL policy and media configuration live in a separate core module so security-sensitive decisions can be tested without constructing the UI.

- `musicvault_app.py` owns the window, YouTube input, queue, progress display, user preferences, and worker-thread lifecycle.
- `musicvault_core.py` owns YouTube URL validation, unsupported-source rejection, output-folder validation, yt-dlp options, app-data paths, packaged-tool discovery, log sanitization, and format helpers.
- `installer/MusicVault.iss` defines the Windows per-user installer and shortcuts.
- `prepare_windows.ps1` and `prepare_macos.sh` stage checksum-pinned runtime components.

## Source flow

1. A YouTube link is parsed and validated against an exact HTTPS host allowlist.
2. The user confirms they have permission to save the content.
3. The queue worker invokes yt-dlp with plugins, cookies, credentials, and remote JavaScript components disabled.
4. FFmpeg converts or remuxes the downloaded media into the selected format.
5. Progress and completion are returned to the UI via Qt signals; cancellation uses a thread-safe event.

Spotify is not an app source. Spotify URLs are rejected before they reach the media downloader.

## UI design

The desktop interface uses a black/charcoal base with restrained red accents. Motion is short and event-driven: button hover/press, queue-row fade-in, progress interpolation, and a status pulse only while work is active. No idle animation loop runs when the queue is idle.

## Storage

- Downloads default to `~/Music/MusicVault` (or the platform equivalent) and can be redirected.
- Preferences and redacted logs are stored under the OS-specific application-data directory.
- Uninstall removes installed program files only; it does not delete the user's downloaded media.

## Future mobile clients

Android and iOS are not built from this desktop project. Their UI, file provider integration, background execution, security boundaries, and platform-store requirements need a separate implementation and release gate.
