from pathlib import Path
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from mobile.app.main import MusicVaultMobileWindow
from mobile.app.source_validation import validate_spotify_link, validate_youtube_link


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication(["musicvault-mobile-tests"])
    yield app


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
    "https://www.youtube.com/watch?v=BaW_jenozKc\r",
    "https://www.youtube.com/watch?v=BaW_jenozKc\t",
    "",
    "x" * 3000,
])
def test_youtube_rejects_unsafe_or_malformed_links(url):
    with pytest.raises(ValueError):
        validate_youtube_link(url)


@pytest.mark.parametrize("url", [
    "https://open.spotify.com/track/1234567890123456789012",
    "https://open.spotify.com/album/1234567890123456789012",
    "https://open.spotify.com/playlist/1234567890123456789012",
    "https://open.spotify.com/artist/1234567890123456789012",
    "https://open.spotify.com/show/1234567890123456789012",
    "https://open.spotify.com/episode/1234567890123456789012",
    "https://spotify.link/AbCdEf",
])
def test_spotify_official_share_links(url):
    assert validate_spotify_link(url) == url


@pytest.mark.parametrize("url", [
    "http://open.spotify.com/track/1234567890123456789012",
    "https://spotify.com.evil.example/track/1234567890123456789012",
    "https://evil.example/track/1234567890123456789012",
    "https://user:pass@open.spotify.com/track/1234567890123456789012",
    "https://open.spotify.com:444/track/1234567890123456789012",
    "https://open.spotify.com/not-a-type/1234567890123456789012",
    "https://open.spotify.com/track/short",
    "https://open.spotify.com/track/1234567890123456789012\n",
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


def test_mobile_window_renders_phone_layout(qapp):
    window = MusicVaultMobileWindow()
    window.resize(390, 844)
    window.show()
    qapp.processEvents()
    assert window.width() == 390
    assert window.youtube_tab.isVisible()
    assert window.spotify_tab.isVisible()
    assert window.pages.currentIndex() == 0
    window.close()


def test_mobile_source_tabs_switch(qapp):
    window = MusicVaultMobileWindow()
    window.show()
    window.set_source("spotify")
    qapp.processEvents()
    assert window.pages.currentIndex() == 1
    assert window.spotify_tab.property("active") is True
    window.set_source("youtube")
    qapp.processEvents()
    assert window.pages.currentIndex() == 0
    assert window.youtube_tab.property("active") is True
    window.close()


def test_mobile_preview_queue_requires_permission_and_playlist_opt_in(qapp):
    window = MusicVaultMobileWindow()
    window.youtube_input.setText("https://youtu.be/BaW_jenozKc")
    window.add_youtube_preview()
    assert window.queue.count() == 0
    assert "Confirm" in window.queue_status.text()

    window.rights_check.setChecked(True)
    window.youtube_input.setText("https://www.youtube.com/playlist?list=PL1234567890")
    window.add_youtube_preview()
    assert window.queue.count() == 0
    assert "full playlist" in window.queue_status.text().lower()

    window.playlist_check.setChecked(True)
    window.add_youtube_preview()
    assert window.queue.count() == 1
    assert "mobile downloading is not enabled" in window.queue_status.text()
    window.close()
