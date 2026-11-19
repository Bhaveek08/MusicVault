"""Platform-neutral input validation for the MusicVault mobile UI."""
from __future__ import annotations

import re
from urllib.parse import parse_qs, urlsplit

YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com", "youtu.be"}
VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
PLAYLIST_ID = re.compile(r"^[A-Za-z0-9_-]{10,80}$")


def _parse_official_https_url(value: str, allowed_hosts: set[str], provider: str):
    if not isinstance(value, str) or not value.strip() or len(value) > 2048:
        raise ValueError(f"Paste a valid {provider} link.")
    # Trim clipboard whitespace, then reject control characters embedded inside the URL.
    candidate = value.strip()
    if any(ord(char) < 32 or ord(char) == 127 for char in candidate):
        raise ValueError(f"The {provider} link contains control characters.")
    try:
        parsed = urlsplit(candidate)
        host = (parsed.hostname or "").lower().rstrip(".")
        port = parsed.port
    except ValueError as exc:
        raise ValueError(f"That {provider} link is malformed.") from exc
    if parsed.scheme.lower() != "https" or host not in allowed_hosts:
        raise ValueError(f"Use an official HTTPS {provider} link.")
    if parsed.username or parsed.password or port not in (None, 443):
        raise ValueError(f"That {provider} link contains unsupported URL details.")
    return parsed, host


def validate_youtube_link(value: str) -> str:
    parsed, host = _parse_official_https_url(value, YOUTUBE_HOSTS, "YouTube")
    try:
        query = parse_qs(parsed.query, keep_blank_values=False, max_num_fields=40)
    except ValueError as exc:
        raise ValueError("That YouTube link has too many query fields.") from exc
    parts = [part for part in parsed.path.split("/") if part]
    if host == "youtu.be":
        if not parts or not VIDEO_ID.fullmatch(parts[0]):
            raise ValueError("That shortened YouTube link does not contain a valid video ID.")
        return "video"
    if parts == ["watch"]:
        if not VIDEO_ID.fullmatch(query.get("v", [""])[0]):
            raise ValueError("That YouTube link does not contain a valid video ID.")
        return "video"
    if len(parts) == 2 and parts[0] in {"shorts", "live", "embed", "v"}:
        if not VIDEO_ID.fullmatch(parts[1]):
            raise ValueError("That YouTube link does not contain a valid video ID.")
        return "video"
    if parts == ["playlist"]:
        if not PLAYLIST_ID.fullmatch(query.get("list", [""])[0]):
            raise ValueError("That YouTube playlist link is missing a valid playlist ID.")
        return "playlist"
    raise ValueError("Use a YouTube video or playlist link.")
