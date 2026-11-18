"""Interaction and layout regression checks for the desktop Qt window."""
from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
import shiboken6
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QMessageBox, QPushButton, QTabWidget

import musicvault_app
from musicvault_app import MusicVaultWindow


def pytest_unconfigure(_config):
    # PySide6 6.12 can segfault at interpreter shutdown unless the QApplication
    # wrapper is explicitly destroyed after all top-level windows are closed.
    app = QApplication.instance()
    if app is not None:
        app.quit()
        shiboken6.delete(app)


@pytest.fixture
def window(tmp_path, monkeypatch):
    # Keep test preferences isolated from the user's real MusicVault settings.
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(tmp_path))
    app = QApplication.instance() or QApplication(["musicvault-ui-tests"])
    app.setOrganizationName("MusicVaultTests")
    app.setApplicationName("MusicVaultTests")
    instance = MusicVaultWindow()
    instance.output_dir = str(tmp_path)
    instance.show()
    app.processEvents()
    yield instance
    instance.close()
    app.processEvents()
    shiboken6.delete(instance)


@pytest.fixture
def warnings(monkeypatch):
    seen = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: seen.append(args[-1]))
    return seen


def click_button(window, label):
    button = next(button for button in window.findChildren(QPushButton) if button.text() == label and button.isVisible())
    button.click()
    QApplication.processEvents()


def test_empty_window_controls_and_layout_fit_supported_minimum(window):
    window.resize(980, 760)
    QApplication.processEvents()
    root = window.centralWidget()
    assert window.size().width() >= 980
    assert window.size().height() >= 760
    for button in window.findChildren(QPushButton):
        if button.isVisible():
            top_left = button.mapTo(root, button.rect().topLeft())
            assert top_left.x() >= 0
            assert top_left.y() >= 0
            assert top_left.x() + button.width() <= root.width()
            assert top_left.y() + button.height() <= root.height()
    assert not window.download_button.isEnabled()
    assert not window.stop_button.isEnabled()
    assert window.queue_stack.currentIndex() == 0


def test_add_requires_permission_and_valid_source(window, warnings):
    window.url_input.setText("https://youtu.be/BaW_jenozKc")
    click_button(window, "Add to queue")
    assert warnings and "permission" in warnings[-1].lower()
    assert window.queue_list.count() == 0

    window.permission_check.setChecked(True)
    window.url_input.setText("https://evil.example/watch?v=BaW_jenozKc")
    click_button(window, "Add to queue")
    assert "official YouTube" in warnings[-1]
    assert window.queue_list.count() == 0


def test_valid_video_adds_queue_and_clear_finished_removes_completed(window, warnings):
    window.permission_check.setChecked(True)
    window.url_input.setText("https://youtu.be/BaW_jenozKc")
    click_button(window, "Add to queue")
    assert not warnings
    assert window.queue_list.count() == 1
    assert window.download_button.isEnabled()
    assert window.queue_count.text() == "1 ITEMS"

    window._on_done(0, "MP3")
    assert window.queue_list.item(0).text().endswith("Done")
    click_button(window, "Clear finished")
    assert window.queue_list.count() == 0
    assert not window.download_button.isEnabled()
    assert window.queue_stack.currentIndex() == 0


def test_playlist_only_link_requires_playlist_option(window, warnings):
    window.permission_check.setChecked(True)
    window.url_input.setText("https://www.youtube.com/playlist?list=PL1234567890")
    click_button(window, "Add to queue")
    assert "Full playlist" in warnings[-1]
    assert window.queue_list.count() == 0


def test_spotify_tab_and_open_link_action(window, monkeypatch, warnings):
    tabs = window.findChild(QTabWidget, "SourceTabs")
    assert tabs is not None
    tabs.setCurrentIndex(1)
    QApplication.processEvents()
    assert window.statusBar().currentMessage() == "Spotify link hand-off"

    opened = []
    monkeypatch.setattr(musicvault_app.QDesktopServices, "openUrl", lambda url: opened.append(url.toString()) or True)
    window.spotify_input.setText("https://open.spotify.com/track/1234567890123456789012")
    click_button(window, "Open in Spotify")
    assert opened == ["https://open.spotify.com/track/1234567890123456789012"]
    window.spotify_input.setText("https://evil.example/track/1234567890123456789012")
    click_button(window, "Open in Spotify")
    assert warnings and "official Spotify" in warnings[-1]


def test_spotify_open_failure_shows_recoverable_error(window, monkeypatch, warnings):
    window.findChild(QTabWidget, "SourceTabs").setCurrentIndex(1)
    QApplication.processEvents()
    monkeypatch.setattr(musicvault_app.QDesktopServices, "openUrl", lambda _url: False)
    window.spotify_input.setText("https://open.spotify.com/track/1234567890123456789012")
    click_button(window, "Open in Spotify")
    assert "Could not open Spotify" in warnings[-1]


def test_queue_state_updates_progress_and_error(window):
    window.permission_check.setChecked(True)
    window.url_input.setText("https://youtu.be/BaW_jenozKc")
    window.add_to_queue()
    window._on_progress(0, 42, "2.1 MiB/s", "00:30")
    assert window.progress.value() == 42
    assert "2.1 MiB/s" in window.status_label.text()
    assert "42%" in window.queue_list.item(0).text()
    window._on_failed(0, "Network unavailable")
    assert window.queue_list.item(0).text().endswith("Failed")
    window.clear_finished()
    assert window.queue_list.count() == 0


def test_all_export_formats_are_available(window):
    assert [window.format_box.itemText(i) for i in range(window.format_box.count())] == [
        "MP3", "WAV", "FLAC", "M4A", "AAC", "OPUS", "MKV"
    ]

