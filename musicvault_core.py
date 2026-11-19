"""Security-conscious core helpers for MusicVault.

The application deliberately accepts only public YouTube video/playlist URLs.
It does not read browser cookies, request account credentials, load downloader
plugins, or fetch remote JavaScript components to work around platform controls.
"""
from __future__ import annotations

import math
import os
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

APP_NAME = "MusicVault"
APP_VERSION = "2.0.6"
MAX_URL_LENGTH = 2048
MAX_PLAYLIST_ITEMS = 500
MAX_QUEUE_ITEMS = 100
ALLOWED_YOUTUBE_HOSTS = frozenset({
    "youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com",
    "youtu.be", "www.youtu.be", "youtube-nocookie.com", "www.youtube-nocookie.com",
})
VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
PLAYLIST_ID_RE = re.compile(r"^[A-Za-z0-9_-]{10,80}$")


class SourceValidationError(ValueError):
    """Raised when a URL is not a supported, safe source."""


class UnsupportedServiceError(SourceValidationError):
    """Raised for providers that cannot be exported as local media files."""


class DownloadCancelled(Exception):
    """Raised by the progress hook when the user cancels a download."""


@dataclass(frozen=True)
class ValidatedSource:
    url: str
    provider: str
    source_id: str
    is_playlist: bool
    is_playlist_only: bool



def get_app_data_dir(
    *,
    platform: str | None = None,
    env: dict[str, str] | None = None,
    home: str | os.PathLike[str] | None = None,
) -> Path:
    """Return the conventional per-user application data directory.

    This keeps preferences/logs out of the installation directory so Windows
    updates and uninstall/reinstall cycles do not require write access to
    Program Files and do not accidentally delete the user's media library.
    """
    current_platform = platform or sys.platform
    environment = os.environ if env is None else env
    home_path = Path(home).expanduser() if home is not None else Path.home()
    if current_platform == "win32":
        base = environment.get("LOCALAPPDATA")
        return Path(base).expanduser() if base else home_path / "AppData" / "Local"
    if current_platform == "darwin":
        return home_path / "Library" / "Application Support"
    xdg = environment.get("XDG_DATA_HOME")
    return Path(xdg).expanduser() if xdg else home_path / ".local" / "share"


def _is_spotify_host(host: str) -> bool:
    host = host.lower().rstrip(".")
    return host in {"spotify.com", "www.spotify.com", "spotify.link"} or host.endswith(".spotify.com")


def validate_source_url(raw_url: str) -> ValidatedSource:
    """Validate a user-entered URL and return a minimal source descriptor.

    Deliberately rejects arbitrary websites, credentials, non-HTTPS links,
    nonstandard ports, deceptive host suffixes, and unsupported YouTube paths.
    """
    if not isinstance(raw_url, str):
        raise SourceValidationError("Paste a valid YouTube video or playlist link.")
    value = raw_url.strip()
    if not value:
        raise SourceValidationError("Paste a YouTube video or playlist link first.")
    if len(value) > MAX_URL_LENGTH:
        raise SourceValidationError("That link is unusually long. Paste a normal YouTube link.")
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
        raise SourceValidationError("The link contains invalid control characters.")

    try:
        parsed = urlsplit(value)
        host = (parsed.hostname or "").lower().rstrip(".")
        port = parsed.port
    except ValueError as exc:
        raise SourceValidationError("That link is malformed.") from exc

    if _is_spotify_host(host):
        raise UnsupportedServiceError(
            "Spotify links cannot be exported as MP3/WAV files through Spotify's supported service. "
            "MusicVault will not rip streams or bypass DRM."
        )
    if parsed.scheme.lower() != "https":
        raise SourceValidationError("For safety, MusicVault accepts HTTPS YouTube links only.")
    if parsed.username is not None or parsed.password is not None:
        raise SourceValidationError("Links containing usernames or passwords are not accepted.")
    if port not in (None, 443):
        raise SourceValidationError("Custom URL ports are not accepted.")
    if host not in ALLOWED_YOUTUBE_HOSTS:
        raise SourceValidationError("Only official YouTube video and playlist links are supported.")
    if parsed.fragment:
        # Fragments are not needed to identify a video and should not affect resolution.
        value = value.split("#", 1)[0]
        parsed = urlsplit(value)

    segments = [part for part in parsed.path.split("/") if part]
    try:
        query = parse_qs(parsed.query, keep_blank_values=False, max_num_fields=40)
    except ValueError as exc:
        raise SourceValidationError("The link has too many query parameters.") from exc

    video_id = ""
    playlist_id = ""
    if host in {"youtu.be", "www.youtu.be"}:
        if not segments or not VIDEO_ID_RE.fullmatch(segments[0]):
            raise SourceValidationError("That youtu.be link does not contain a valid video ID.")
        video_id = segments[0]
        playlist_id = _valid_playlist_id(query.get("list", [""])[0])
    elif segments == ["watch"]:
        video_id = query.get("v", [""])[0]
        if video_id and not VIDEO_ID_RE.fullmatch(video_id):
            raise SourceValidationError("That YouTube link has an invalid video ID.")
        playlist_id = _valid_playlist_id(query.get("list", [""])[0])
        if not video_id and not playlist_id:
            raise SourceValidationError("The YouTube watch link is missing its video ID.")
    elif segments == ["playlist"]:
        playlist_id = _valid_playlist_id(query.get("list", [""])[0])
        if not playlist_id:
            raise SourceValidationError("That YouTube playlist link is missing a valid playlist ID.")
    elif len(segments) == 2 and segments[0] in {"shorts", "live", "embed", "v"}:
        video_id = segments[1]
        if not VIDEO_ID_RE.fullmatch(video_id):
            raise SourceValidationError("That YouTube link has an invalid video ID.")
        playlist_id = _valid_playlist_id(query.get("list", [""])[0])
    else:
        raise SourceValidationError("Use a YouTube watch, Shorts, live, embed, youtu.be, or playlist link.")

    source_id = video_id or playlist_id
    # Drop every nonessential query parameter and normalize short/mobile links.
    # This keeps tracking fragments and unexpected query fields away from the extractor.
    if video_id:
        canonical_url = f"https://www.youtube.com/watch?v={video_id}"
        if playlist_id:
            canonical_url += f"&list={playlist_id}"
    else:
        canonical_url = f"https://www.youtube.com/playlist?list={playlist_id}"
    return ValidatedSource(
        url=canonical_url,
        provider="YouTube",
        source_id=source_id,
        is_playlist=bool(playlist_id),
        is_playlist_only=bool(playlist_id and not video_id),
    )


def _valid_playlist_id(value: str) -> str:
    return value if PLAYLIST_ID_RE.fullmatch(value or "") else ""


def validate_output_folder(folder: str | os.PathLike[str]) -> Path:
    """Create/check the chosen output directory with a small write probe."""
    try:
        path = Path(folder).expanduser()
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
        resolved = path.resolve(strict=True)
        if not resolved.is_dir():
            raise OSError("The selected output path is not a folder.")
        # The default delete=True removes the probe even if write/flush raises.
        with tempfile.NamedTemporaryFile(prefix=".musicvault-check-", dir=resolved) as probe:
            probe.write(b"MusicVault folder permission check")
            probe.flush()
        return resolved
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        raise ValueError(f"MusicVault cannot write to that folder: {exc}") from exc


def build_ydl_options(
    *,
    url: str,
    output_dir: str | os.PathLike[str],
    output_format: str,
    include_playlist: bool,
    ffmpeg_location: str | None,
    progress_hook,
    logger,
    deno_path: str | None = None,
) -> dict:
    """Create conservative yt-dlp options. No cookies, plugins or remote code."""
    source = validate_source_url(url)
    # Validate again at the engine boundary; callers other than the GUI must
    # not be able to pass an unwritable or non-directory destination.
    folder = validate_output_folder(output_dir)
    supported = {"MP3", "WAV", "FLAC", "M4A", "AAC", "OPUS", "MKV"}
    fmt = output_format.upper()
    if fmt not in supported:
        raise ValueError("Choose a supported output format.")
    if source.is_playlist_only and not include_playlist:
        raise ValueError("This is a playlist-only link. Enable playlist mode to download it.")

    # Keep output names on one level and let yt-dlp sanitize platform-provided titles.
    output_template = str(folder / "%(title).120s [%(id)s].%(ext)s")
    options = {
        "quiet": True,
        "ignoreconfig": True,
        "no_warnings": True,
        "noprogress": True,
        "ignoreerrors": False,
        "noplaylist": not include_playlist,
        "playlistend": MAX_PLAYLIST_ITEMS,
        "outtmpl": {"default": output_template},
        "paths": {"home": str(folder), "temp": str(folder / ".musicvault-tmp")},
        "windowsfilenames": True,
        "trim_file_name": 140,
        "nooverwrites": True,
        "continuedl": True,
        "retries": 2,
        "fragment_retries": 2,
        "extractor_retries": 1,
        "socket_timeout": 20,
        "concurrent_fragment_downloads": 1,
        "cachedir": False,
        "writedescription": False,
        "writeinfojson": False,
        "writethumbnail": False,
        "writesubtitles": False,
        "writeautomaticsub": False,
        "writeannotations": False,
        "progress_hooks": [progress_hook],
        "logger": logger,
        # Disable third-party plugin loading and remote executable JavaScript components.
        "remote_components": [],
    }
    if ffmpeg_location:
        options["ffmpeg_location"] = ffmpeg_location
    if deno_path:
        options["js_runtimes"] = {"deno": {"path": deno_path}}

    if fmt == "MKV":
        options.update({
            "format": "bestvideo*+bestaudio/best",
            "merge_output_format": "mkv",
            "postprocessors": [{"key": "FFmpegVideoRemuxer", "preferredformat": "mkv"}],
        })
    else:
        audio_postprocessor = {
            "key": "FFmpegExtractAudio",
            "preferredcodec": fmt.lower(),
        }
        # For lossy exports, request a high-quality 320 kbps encode. WAV and
        # FLAC are lossless targets and must not receive a lossy bitrate cap.
        if fmt in {"MP3", "M4A", "AAC", "OPUS"}:
            audio_postprocessor["preferredquality"] = "320"
        options.update({
            "format": "bestaudio/best",
            "postprocessors": [audio_postprocessor],
        })
    return options


def find_ffmpeg() -> str | None:
    """Locate bundled FFmpeg; packaged builds never execute a PATH substitute."""
    frozen = bool(getattr(sys, "frozen", False))
    try:
        import imageio_ffmpeg  # type: ignore
        candidate = imageio_ffmpeg.get_ffmpeg_exe()
        if candidate and Path(candidate).is_file():
            resolved = Path(candidate).resolve()
            if not frozen:
                return str(resolved)
            bundle = getattr(sys, "_MEIPASS", None)
            if not bundle:
                return None
            bundle_root = Path(bundle).resolve()
            if resolved.is_relative_to(bundle_root):
                return str(resolved)
    except Exception:
        pass
    return None if frozen else shutil.which("ffmpeg")


def deno_executable_name(platform: str | None = None) -> str:
    """Return the native Deno executable name for the current OS."""
    current_platform = platform or sys.platform
    return "deno.exe" if current_platform == "win32" else "deno"


def find_deno() -> str | None:
    """Locate Deno; frozen builds may execute only the copy inside the bundle."""
    executable = deno_executable_name()
    if getattr(sys, "frozen", False):
        bundle = getattr(sys, "_MEIPASS", None)
        if not bundle:
            return None
        bundle_root = Path(bundle).resolve()
        candidate = bundle_root / executable
        try:
            resolved = candidate.resolve(strict=True)
            if resolved.is_file() and resolved.is_relative_to(bundle_root):
                if sys.platform != "win32" and not os.access(resolved, os.X_OK):
                    return None
                return str(resolved)
        except (OSError, RuntimeError, ValueError):
            return None
        return None

    candidate = Path(__file__).resolve().parent / "vendor" / executable
    if candidate.is_file() and (sys.platform == "win32" or os.access(candidate, os.X_OK)):
        return str(candidate.resolve())
    return shutil.which("deno")


def clean_message(value: object, limit: int = 260) -> str:
    """Strip control characters, URLs, and common secret-bearing log fields."""
    text = str(value or "")
    text = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", text)
    # Redact complete header values, including multi-part Authorization schemes
    # and Cookie headers that may contain several semicolon-delimited values.
    text = re.sub(
        r"(?im)\b(authorization|proxy-authorization|cookie|set-cookie)\s*[:=][^\r\n]*",
        r"\1=[redacted]",
        text,
    )
    # Also cover common structured/log-field forms (including quoted JSON keys).
    text = re.sub(
        r"(?i)([\"']?(?:token|password|api[_-]?key)[\"']?\s*[:=]\s*)(?:\"[^\"]*\"|'[^']*'|[^\s,;&}]+)",
        r"\1[redacted]",
        text,
    )
    text = re.sub(r"https?://\S+", "[link]", text)
    text = "".join(ch for ch in text if ch in "\n\t" or ord(ch) >= 32)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max(0, int(limit))]


def describe_download_error(error: object) -> str:
    """Translate common downloader failures into actionable, safe UI copy."""
    message = clean_message(error, 600)
    lowered = message.lower()
    if "403" in lowered or "forbidden" in lowered:
        return (
            "YouTube refused this media request (HTTP 403). This item, account, network, or player path "
            "may be restricted. MusicVault does not bypass sign-in, DRM, or platform access controls. "
            "Check the link and your network, update MusicVault, or try content you are authorized to save."
        )
    if "private video" in lowered or "members-only" in lowered or "sign in" in lowered:
        return "YouTube requires access that MusicVault does not request or store. Use a public item you are allowed to save."
    if "ffmpeg" in lowered or "ffprobe" in lowered:
        return "Media conversion could not start. Reinstall MusicVault or check that its bundled FFmpeg files are intact."
    if "unsupported url" in lowered or "not a valid url" in lowered:
        return "That link is not a supported YouTube video or playlist URL."
    if not message:
        return "The download failed for an unknown reason. Check the link and try again."
    return f"Download failed: {message}"


def format_bytes(value: object) -> str:
    try:
        size = float(value)
    except (TypeError, ValueError, OverflowError):
        return ""
    if not math.isfinite(size) or size < 0:
        return ""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.1f} {unit}"
        size /= 1024
    return ""


def format_eta(value: object) -> str:
    try:
        number = float(value)
        if not math.isfinite(number):
            return ""
        seconds = max(0, int(number))
    except (TypeError, ValueError, OverflowError):
        return ""
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes:02d}:{seconds:02d}"
