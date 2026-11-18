"""Platform-neutral input validation for the MusicVault mobile UI."""
from __future__ import annotations

import re
from urllib.parse import parse_qs, urlsplit

YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com", "youtu.be"}
SPOTIFY_HOSTS = {"open.spotify.com", "www.spotify.com", "spotify.com", "spotify.link"}
VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
PLAYLIST_ID = re.compile(r"^[A-Za-z0-9_-]{10,80}$")
SPOTIFY_SHORT_ID = re.compile(r"^[A-Za-z0-9_-]{1,100}$")
SPOTIFY_RESOURCE_ID = re.compile(r"^[A-Za-z0-9]{22}$")
SPOTIFY_TYPES = {"track", "album", "artist", "playlist", "show", "episode"}


def _parse_official_https_url(value: str, allowed_hosts: set[str], provider: str):
    if not isinstance(value, str) or not value.strip() or len(value) > 2048:
        raise ValueError(f"Paste a valid {provider} link.")
    # Reject controls before trimming: urlsplit() silently strips CR/LF and TAB.
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise ValueError(f"The {provider} link contains control characters.")
    candidate = value.strip()
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


def validate_spotify_link(value: str) -> str:
    parsed, host = _parse_official_https_url(value, SPOTIFY_HOSTS, "Spotify")
    parts = [part for part in parsed.path.split("/") if part]
    if host == "spotify.link":
        if len(parts) != 1 or not SPOTIFY_SHORT_ID.fullmatch(parts[0]):
            raise ValueError("Paste a valid Spotify short share link.")
        return value.strip()
    if len(parts) != 2 or parts[0] not in SPOTIFY_TYPES or not SPOTIFY_RESOURCE_ID.fullmatch(parts[1]):
        raise ValueError("Paste a Spotify track, album, artist, show, episode or playlist link.")
    return value.strip()
