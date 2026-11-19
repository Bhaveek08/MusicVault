"""Interaction and layout regression checks for the desktop Qt window."""
from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
import shiboken6
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QFileDialog, QFrame, QMessageBox, QPushButton, QTabWidget

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


def test_desktop_columns_do_not_overlap_at_preview_size(window):
    window.resize(1200, 820)
    QApplication.processEvents()
    root = window.centralWidget()
    tabs = window.findChild(QTabWidget, "SourceTabs")
    queue_card = window.findChild(QFrame, "QueueCard")
    tabs_origin = tabs.mapTo(root, tabs.rect().topLeft())
    queue_origin = queue_card.mapTo(root, queue_card.rect().topLeft())
    assert tabs_origin.x() + tabs.width() <= queue_origin.x()


def test_long_save_path_is_elided_and_available_in_tooltip(window):
    long_path = "C:\\Users\\ADMIN\\Music\\" + "very-long-folder-name\\" * 14 + "MusicVault"
    window.folder_label.set_full_text(long_path)
    QApplication.processEvents()
    assert window.folder_label.full_text == long_path
    assert window.folder_label.toolTip() == long_path
    assert "…" in window.folder_label.text()


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


def test_youtube_paste_button_uses_clipboard(window):
    QApplication.clipboard().setText("https://youtu.be/BaW_jenozKc")
    click_button(window, "Paste")
    assert window.url_input.text() == "https://youtu.be/BaW_jenozKc"


def test_spotify_paste_button_uses_clipboard(window):
    window.findChild(QTabWidget, "SourceTabs").setCurrentIndex(1)
    QApplication.processEvents()
    QApplication.clipboard().setText("https://open.spotify.com/track/1234567890123456789012")
    click_button(window, "Paste")
    assert window.spotify_input.text() == "https://open.spotify.com/track/1234567890123456789012"


def test_change_folder_button_updates_path_and_persists_setting(window, tmp_path, monkeypatch):
    selected = tmp_path / "chosen music"
    monkeypatch.setattr(QFileDialog, "getExistingDirectory", lambda *_args: str(selected))
    click_button(window, "Change")
    assert window.output_dir == str(selected.resolve())
    assert window.folder_label.full_text == str(selected.resolve())
    assert window.settings.value("output_dir") == str(selected.resolve())


def test_change_folder_cancel_keeps_current_path(window, monkeypatch):
    original = window.output_dir
    monkeypatch.setattr(QFileDialog, "getExistingDirectory", lambda *_args: "")
    click_button(window, "Change")
    assert window.output_dir == original


def test_download_and_stop_buttons_drive_queue_worker(window, monkeypatch):
    window.permission_check.setChecked(True)
    window.url_input.setText("https://youtu.be/BaW_jenozKc")
    window.add_to_queue()

    class Signal:
        def connect(self, _callback):
            pass

    class FakeWorker:
        def __init__(self, pending, cancel_event):
            self.pending = pending
            self.cancel_event = cancel_event
            self.progress = Signal()
            self.done = Signal()
            self.failed = Signal()
            self.stopped = Signal()
            self.finished = Signal()
            self.started = False

        def start(self):
            self.started = True

        def isRunning(self):
            return False

    monkeypatch.setattr(musicvault_app, "Worker", FakeWorker)
    click_button(window, "Download")
    assert window.worker.started
    assert window.worker.pending[0][1] is window.jobs[0]
    assert window.stop_button.isEnabled()

    click_button(window, "Stop")
    assert window.cancel_event.is_set()
    assert not window.stop_button.isEnabled()
    assert window.status_label.text() == "Stopping…"


def test_queue_error_states_are_recoverable(window, warnings):
    # Invalid source, missing permission, playlist option, and queue cap all
    # leave the UI usable and avoid creating a phantom queue item.
    window.url_input.setText("not a URL")
    window.add_to_queue()
    assert warnings and window.queue_list.count() == 0

    window.url_input.setText("https://youtu.be/BaW_jenozKc")
    window.add_to_queue()
    assert "permission" in warnings[-1].lower()
    assert window.queue_list.count() == 0

    window.permission_check.setChecked(True)
    window.url_input.setText("https://www.youtube.com/playlist?list=PL1234567890")
    window.add_to_queue()
    assert "Full playlist" in warnings[-1]
    assert window.queue_list.count() == 0

    window.playlist_check.setChecked(True)
    for index in range(100):
        window.url_input.setText(f"https://youtu.be/{index:011d}")
        window.add_to_queue()
    assert window.queue_list.count() == 100
    window.url_input.setText("https://youtu.be/BaW_jenozKc")
    window.add_to_queue()
    assert "queue is full" in warnings[-1].lower()
    assert window.queue_list.count() == 100

