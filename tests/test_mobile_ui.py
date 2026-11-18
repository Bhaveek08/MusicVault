import os
import sys
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from mobile.app.main import MusicVaultMobileWindow, validate_spotify_link, validate_youtube_link

requires_qt_gui = pytest.mark.skipif(
    sys.platform == "darwin",
    reason="Qt 6.12 offscreen Widgets backend crashes at interpreter shutdown on the current macOS CI runner; run these widget tests on Linux/Windows and iOS via the native Xcode path.",
)


@pytest.fixture(scope="session")
def app():
    instance = QApplication.instance() or QApplication([])
    yield instance


@requires_qt_gui
def test_mobile_preview_renders_at_phone_size(app):
    window = MusicVaultMobileWindow()
    window.resize(390, 844)
    window.show()
    app.processEvents()
    assert window.width() == 390
    assert window.youtube_tab.isVisible()
    assert window.spotify_tab.isVisible()
    assert window.scroll.isVisible()
    window.close()


@requires_qt_gui
def test_source_tabs_switch_without_rebuilding_widgets(app):
    window = MusicVaultMobileWindow()
    window.set_source("spotify")
    assert window.pages.currentIndex() == 1
    assert window.spotify_tab.property("active") is True
    window.set_source("youtube")
    assert window.pages.currentIndex() == 0
    assert window.youtube_tab.property("active") is True
    window.close()


@pytest.mark.parametrize(("url", "kind"), [
    ("https://www.youtube.com/watch?v=BaW_jenozKc", "video"),
    ("https://youtu.be/BaW_jenozKc", "video"),
    ("https://www.youtube.com/playlist?list=PL1234567890", "playlist"),
])
def test_mobile_youtube_url_validation(url, kind):
    assert validate_youtube_link(url) == kind


@pytest.mark.parametrize("url", [
    "http://youtube.com/watch?v=BaW_jenozKc",
    "https://youtube.com.evil.example/watch?v=BaW_jenozKc",
    "https://user:pass@youtube.com/watch?v=BaW_jenozKc",
    "javascript:alert(1)",
])
def test_mobile_youtube_rejects_unsafe_links(url):
    with pytest.raises(ValueError):
        validate_youtube_link(url)


@pytest.mark.parametrize("url", [
    "https://open.spotify.com/track/12345678901234567890",
    "https://open.spotify.com/playlist/12345678901234567890",
])
def test_mobile_spotify_link_validation(url):
    assert validate_spotify_link(url) == url


def test_mobile_spotify_rejects_lookalike_hosts():
    with pytest.raises(ValueError):
        validate_spotify_link("https://spotify.com.evil.example/track/123")


@requires_qt_gui
def test_youtube_queue_is_explicitly_preview_only(app):
    window = MusicVaultMobileWindow()
    window.youtube_input.setText("https://youtu.be/BaW_jenozKc")
    window.rights_check.setChecked(True)
    window.add_youtube_preview()
    assert window.queue.count() == 1
    assert "mobile downloading is not enabled" in window.queue_status.text()
    window.close()


@requires_qt_gui
def test_playlist_requires_playlist_toggle(app):
    window = MusicVaultMobileWindow()
    window.youtube_input.setText("https://www.youtube.com/playlist?list=PL1234567890")
    window.rights_check.setChecked(True)
    window.add_youtube_preview()
    assert window.queue.count() == 0
    assert "full playlist" in window.queue_status.text()
    window.close()
