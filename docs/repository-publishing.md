# Publishing MusicVault on GitHub

The repository is prepared for GitHub, but the project owner should review its
contents and choose the repository visibility before publishing.

## Recommended repository settings

- Repository name: `musicvault`
- Description: `A desktop app for supported YouTube media downloads and Spotify link hand-off.`
- Topics: `desktop-application`, `python`, `pyside6`, `windows`, `macos`, `yt-dlp`, `ffmpeg`
- Default branch: `main`
- Security: enable private vulnerability reporting when available; keep secret
  scanning and push protection enabled where the account supports them.
- License: no project license has been selected. Do not describe the repository
  as open source until the owner chooses and adds a suitable license.

## Publish from Windows

1. Install Git for Windows and GitHub CLI.
2. Sign in to GitHub CLI with `gh auth login` and follow the browser prompt.
3. Open PowerShell in the project root.
4. Run `./scripts/publish-to-github.ps1`.
5. Review the staged file list and the license notice. Type `PUBLISH` only when
   you are satisfied with the repository name and visibility.

The script uses the GitHub CLI credential store. It does not ask for or write a
personal access token into the project. Pass `-Visibility private` for a private
repository or `-Visibility internal` where the GitHub account supports it.

The script creates a local Git repository and an initial commit only after you
confirm publication. It refuses to continue if an `origin` remote exists or if
a repository with the same name already exists, preventing accidental pushes
to the wrong destination.

## After the first push

- Review the repository description and topics.
- Confirm the Actions workflows run successfully.
- Enable private vulnerability reporting and review branch protection settings.
- Complete the Windows build and GUI validation described in
  [release-process.md](release-process.md).
- Do not attach an executable until the Windows build and packaged smoke test
  have passed on GitHub Actions or a clean Windows machine.
