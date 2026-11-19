from pathlib import Path

import pytest

from mobile.app.source_validation import validate_youtube_link


@pytest.mark.parametrize(("url", "kind"), [
    ("https://www.youtube.com/watch?v=BaW_jenozKc", "video"),
    ("https://youtu.be/BaW_jenozKc", "video"),
    ("https://www.youtube.com/shorts/BaW_jenozKc", "video"),
    ("https://www.youtube.com/live/BaW_jenozKc", "video"),
    ("https://www.youtube.com/playlist?list=PL1234567890", "playlist"),
])
def test_youtube_link_categories(url, kind):
    assert validate_youtube_link(url) == kind


def test_youtube_input_trims_pasted_whitespace():
    assert validate_youtube_link("  https://youtu.be/BaW_jenozKc\n") == "video"


@pytest.mark.parametrize("url", [
    "http://youtube.com/watch?v=BaW_jenozKc",
    "https://youtube.com.evil.example/watch?v=BaW_jenozKc",
    "https://evil.example/watch?v=BaW_jenozKc",
    "https://user:pass@youtube.com/watch?v=BaW_jenozKc",
    "https://youtube.com:444/watch?v=BaW_jenozKc",
    "javascript:alert(1)",
    "https://www.youtube.com/watch?v=short",
    "https://www.youtube.com/playlist?list=bad",
    "https://www.youtube.com/\nwatch?v=BaW_jenozKc",
    "https://www.youtube.com/watch\tv=BaW_jenozKc",
    "",
    "x" * 3000,
])
def test_youtube_rejects_unsafe_or_malformed_links(url):
    with pytest.raises(ValueError):
        validate_youtube_link(url)


def test_mobile_ui_has_no_spotify_option_or_downloader_worker():
    source = Path("mobile/app/main.py").read_text(encoding="utf-8")
    assert 'self._card("YouTube"' in source
    assert "Spotify" not in source
    html = Path("mobile/shared/index.html").read_text(encoding="utf-8")
    assert "Spotify" not in html
    assert "downloads are not enabled in this mobile build yet" in source.lower()
    assert "import yt_dlp" not in source
    assert "subprocess" not in source
    assert "QDesktopServices" not in source
    assert "Include full playlist" in source
