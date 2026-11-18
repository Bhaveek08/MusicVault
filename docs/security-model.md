# Security model

## Intended use

MusicVault accepts public YouTube video and playlist URLs that the user owns or is authorized to save, subject to platform rules and availability. It intentionally declines Spotify stream export and private, member-only, age-gated, or account-gated media.

## Assets to protect

- Local files outside the user-selected output directory.
- Local account credentials, browser sessions, cookies, and authentication tokens.
- URLs and media identifiers pasted into the application.
- Integrity of the bundled FFmpeg and Deno executables.

## Controls

- Exact HTTPS hostname allowlist and supported path/ID validation.
- Rejection of URL userinfo, unusual ports, malformed identifiers, control characters, and lookalike hosts.
- No shell execution for URLs or other user input.
- Explicit yt-dlp options with configuration files, cookies, credential flags, plugins, and remote JavaScript components disabled.
- Pinned dependencies and checksum verification for the separately downloaded Deno archive.
- Frozen-build tool-path containment for FFmpeg and Deno.
- Output-directory validation, constrained filename templates, and no-overwrite defaults.
- Redaction and size limits for activity diagnostics; URLs are not intentionally logged.

## Out of scope

MusicVault does not protect against malware or administrator-level compromise on the host, malicious or compromised upstream dependencies, platform-side tracking, an unsafe downloaded media file, or a user deliberately running a modified build. It does not provide sandboxed media decoding or code signing.

## Operational guidance

Use trusted release artifacts, keep Windows updated, review dependency and third-party notices, and scan downloaded files using the security tools appropriate to your environment. Do not paste private or credential-bearing URLs. Report vulnerabilities privately as described in [SECURITY.md](../SECURITY.md).
