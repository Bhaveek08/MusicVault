# Security policy

## Supported versions

Security fixes are currently intended for the latest published MusicVault release. This project is under active development; no long-term support window is promised.

## Reporting a vulnerability

Please do not disclose a suspected vulnerability in a public issue or discussion.

Use GitHub's **Private vulnerability reporting** feature for this repository when it is enabled. If that feature is unavailable, contact the repository owner through a private channel listed on their GitHub profile and include the repository name and a concise description. Do not include real credentials, private media links, or personal data in the initial report.

A useful report includes the affected version/commit, operating system, impact, reproducible steps, and a minimal proof of concept. Give maintainers a reasonable opportunity to investigate and prepare a fix before public disclosure.

## Security boundaries

MusicVault is designed for public YouTube URLs that the user is authorized to save. It does not authenticate to YouTube, access browser cookies, download from Spotify, defeat DRM, or bypass private/member-only/account-gated restrictions. A platform refusal such as HTTP 403 is surfaced rather than circumvented.

The current packaged executable is not code-signed. Download and run software only from a source you trust, and inspect release checksums and third-party notices before redistributing it.
