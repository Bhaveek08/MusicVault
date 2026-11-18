from pathlib import Path

import pytest

from mobile.app.source_validation import validate_spotify_link, validate_youtube_link


@pytest.mark.parametrize(("url", "kind"), [
    ("https://www.youtube.com/watch?v=BaW_jenozKc", "video"),
    ("https://youtu.be/BaW_jenozKc", "video"),
    ("https://www.youtube.com/shorts/BaW_jenozKc", "video"),
    ("https://www.youtube.com/live/BaW_jenozKc", "video"),
    ("https://www.youtube.com/playlist?list=PL1234567890", "playlist"),
])
def test_youtube_link_categories(url, kind):
    assert validate_youtube_link(url) == kind


@pytest.mark.parametrize("url", [
    "http://youtube.com/watch?v=BaW_jenozKc",
    "https://youtube.com.evil.example/watch?v=BaW_jenozKc",
    "https://evil.example/watch?v=BaW_jenozKc",
    "https://user:pass@youtube.com/watch?v=BaW_jenozKc",
    "https://youtube.com:444/watch?v=BaW_jenozKc",
    "javascript:alert(1)",
    "https://www.youtube.com/watch?v=short",
    "https://www.youtube.com/playlist?list=bad",
    "https://www.youtube.com/watch?v=BaW_jenozKc\n",
    "",
    "x" * 3000,
])
def test_youtube_rejects_unsafe_or_malformed_links(url):
    with pytest.raises(ValueError):
        validate_youtube_link(url)


@pytest.mark.parametrize("url", [
    "https://open.spotify.com/track/12345678901234567890",
    "https://open.spotify.com/album/12345678901234567890",
    "https://open.spotify.com/playlist/12345678901234567890",
    "https://open.spotify.com/artist/12345678901234567890",
    "https://open.spotify.com/show/12345678901234567890",
    "https://open.spotify.com/episode/12345678901234567890",
    "https://spotify.link/AbCdEf",
])
def test_spotify_official_share_links(url):
    assert validate_spotify_link(url) == url


@pytest.mark.parametrize("url", [
    "http://open.spotify.com/track/12345678901234567890",
    "https://spotify.com.evil.example/track/12345678901234567890",
    "https://evil.example/track/12345678901234567890",
    "https://user:pass@open.spotify.com/track/12345678901234567890",
    "https://open.spotify.com:444/track/12345678901234567890",
    "https://open.spotify.com/not-a-type/12345678901234567890",
    "https://open.spotify.com/track/short",
    "",
    "x" * 3000,
])
def test_spotify_rejects_unsafe_or_malformed_links(url):
    with pytest.raises(ValueError):
        validate_spotify_link(url)


def test_mobile_ui_source_has_both_provider_sections_and_no_downloader_worker():
    source = Path("mobile/app/main.py").read_text(encoding="utf-8")
    assert 'self._card("YouTube"' in source
    assert 'self._card("Spotify"' in source
    assert "mobile downloading is not enabled" in source
    assert "import yt_dlp" not in source
    assert "subprocess" not in source
