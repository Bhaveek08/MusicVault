"""MusicVault desktop application."""
from __future__ import annotations

import argparse
import os
import sys
import threading
from dataclasses import dataclass

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QThread, QTimer, Qt, Signal
from PySide6.QtGui import QDesktopServices, QIcon
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFileDialog, QFrame, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMessageBox,
    QProgressBar, QPushButton, QTabWidget, QVBoxLayout, QWidget,
)

from musicvault_core import (
    APP_NAME, APP_VERSION, DownloadCancelled, build_ytdlp_options,
    describe_download_error, find_deno, find_ffmpeg, validate_output_folder,
    validate_source_url, validate_spotify_url,
)

AUDIO_FORMATS = ("MP3", "WAV", "FLAC", "M4A", "AAC", "OPUS")
ALL_FORMATS = AUDIO_FORMATS + ("MKV",)


@dataclass(frozen=True)
class Job:
    url: str
    output_format: str
    output_dir: str
    playlist: bool


class Worker(QThread):
    progress = Signal(int, int, str, str)
    done = Signal(int, str)
    failed = Signal(int, str)
    stopped = Signal(int)

    def __init__(self, jobs: list[tuple[int, Job]], cancel: threading.Event):
        super().__init__()
        self.jobs = jobs
        self.cancel = cancel

    def run(self) -> None:
        try:
            import yt_dlp
        except ImportError:
            for index, _ in self.jobs:
                self.failed.emit(index, "The download engine is missing. Reinstall MusicVault.")
            return

        ffmpeg = find_ffmpeg()
        deno = find_deno()
        for index, job in self.jobs:
            if self.cancel.is_set():
                self.stopped.emit(index)
                break
            try:
                def hook(data: dict) -> None:
                    if self.cancel.is_set():
                        raise DownloadCancelled()
                    state = data.get("status")
                    if state == "downloading":
                        downloaded = int(data.get("downloaded_bytes") or 0)
                        total = int(data.get("total_bytes") or data.get("total_bytes_estimate") or 0)
                        percent = min(99, int(downloaded * 100 / total)) if total else 0
                        speed = str(data.get("_speed_str") or "").strip()
                        eta = str(data.get("_eta_str") or "").strip()
                        self.progress.emit(index, percent, speed, eta)
                    elif state == "finished":
                        self.progress.emit(index, 99, "Converting", "")

                options = build_ytdlp_options(
                    url=job.url,
                    output_dir=job.output_dir,
                    output_format=job.output_format,
                    include_playlist=job.playlist,
                    ffmpeg_location=ffmpeg,
                    progress_hook=hook,
                    logger=None,
                    deno_path=deno,
                )
                with yt_dlp.YoutubeDL(options) as downloader:
                    code = downloader.download([job.url])
                if self.cancel.is_set():
                    self.stopped.emit(index)
                elif code == 0:
                    self.done.emit(index, job.output_format)
                else:
                    self.failed.emit(index, "The media provider did not complete this download.")
            except DownloadCancelled:
                self.stopped.emit(index)
                break
            except Exception as exc:
                self.failed.emit(index, describe_download_error(exc))


class MotionButton(QPushButton):
    def __init__(self, label: str, parent=None):
        super().__init__(label, parent)
        self._fade = QPropertyAnimation(self, b"windowOpacity", self)
        self._fade.setDuration(110)
        self._fade.setEasingCurve(QEasingCurve.OutCubic)
        self.pressed.connect(lambda: self._animate(0.82))
        self.released.connect(lambda: self._animate(1.0))

    def _animate(self, value: float) -> None:
        self._fade.stop()
        self._fade.setStartValue(self.windowOpacity())
        self._fade.setEndValue(value)
        self._fade.start()


class MusicVaultWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} — Downloads")
        self.setMinimumSize(780, 590)
        self.resize(980, 700)
        self.jobs: list[Job] = []
        self.worker: Worker | None = None
        self.cancel_event = threading.Event()
        self.output_dir = os.path.join(os.path.expanduser("~"), "Music", APP_NAME)
        self._build_ui()
        self._apply_style()
        self.statusBar().showMessage("Ready")

    def _card(self, title: str) -> tuple[QFrame, QVBoxLayout]:
        card = QFrame()
        card.setObjectName("Card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)
        label = QLabel(title)
        label.setObjectName("SectionTitle")
        layout.addWidget(label)
        return card, layout

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(26, 22, 26, 18)
        outer.setSpacing(16)

        header = QHBoxLayout()
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "musicvault-icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            icon = QLabel()
            icon.setPixmap(QIcon(icon_path).pixmap(42, 42))
            header.addWidget(icon)
        brand = QLabel("MusicVault")
        brand.setObjectName("Brand")
        header.addWidget(brand)
        header.addStretch(1)
        version = QLabel(APP_VERSION)
        version.setObjectName("Version")
        header.addWidget(version)
        outer.addLayout(header)

        tabs = QTabWidget()
        tabs.setObjectName("SourceTabs")
        youtube = QWidget()
        ybox = QVBoxLayout(youtube)
        ybox.setContentsMargins(18, 18, 18, 18)
        ybox.setSpacing(14)

        source_card, source_layout = self._card("YouTube")
        row = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste a YouTube video or playlist link")
        self.url_input.setClearButtonEnabled(True)
        self.url_input.returnPressed.connect(self.add_to_queue)
        row.addWidget(self.url_input, 1)
        paste = MotionButton("Paste")
        paste.setObjectName("SecondaryButton")
        paste.clicked.connect(lambda: self.url_input.setText(QApplication.clipboard().text().strip()))
        row.addWidget(paste)
        source_layout.addLayout(row)

        settings = QHBoxLayout()
        self.format_box = QComboBox()
        self.format_box.addItems(ALL_FORMATS)
        self.format_box.setAccessibleName("Output format")
        settings.addWidget(QLabel("Format"))
        settings.addWidget(self.format_box)
        self.playlist_check = QCheckBox("Full playlist")
        settings.addWidget(self.playlist_check)
        settings.addStretch(1)
        source_layout.addLayout(settings)

        folder_row = QHBoxLayout()
        self.folder_label = QLabel(self.output_dir)
        self.folder_label.setObjectName("PathLabel")
        self.folder_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        folder_row.addWidget(self.folder_label, 1)
        browse = MotionButton("Choose folder")
        browse.setObjectName("SecondaryButton")
        browse.clicked.connect(self.choose_folder)
        folder_row.addWidget(browse)
        source_layout.addLayout(folder_row)

        self.permission_check = QCheckBox("I own this content or have permission to save it.")
        source_layout.addWidget(self.permission_check)
        add_button = MotionButton("Add to queue")
        add_button.setObjectName("YoutubeButton")
        add_button.clicked.connect(self.add_to_queue)
        source_layout.addWidget(add_button, alignment=Qt.AlignRight)
        ybox.addWidget(source_card)

        spotify = QWidget()
        sbox = QVBoxLayout(spotify)
        sbox.setContentsMargins(18, 18, 18, 18)
        sbox.setSpacing(14)
        spotify_card, spotify_layout = self._card("Spotify")
        self.spotify_input = QLineEdit()
        self.spotify_input.setPlaceholderText("Paste a Spotify track, album, artist or playlist link")
        self.spotify_input.returnPressed.connect(self.open_spotify)
        spotify_layout.addWidget(self.spotify_input)
        spotify_actions = QHBoxLayout()
        spotify_paste = MotionButton("Paste")
        spotify_paste.setObjectName("SecondaryButton")
        spotify_paste.clicked.connect(lambda: self.spotify_input.setText(QApplication.clipboard().text().strip()))
        spotify_actions.addWidget(spotify_paste)
        spotify_actions.addStretch(1)
        open_button = MotionButton("Open in Spotify")
        open_button.setObjectName("SpotifyButton")
        open_button.clicked.connect(self.open_spotify)
        spotify_actions.addWidget(open_button)
        spotify_layout.addLayout(spotify_actions)
        sbox.addWidget(spotify_card)
        note = QLabel("Spotify links open in Spotify. Streaming tracks are not exported as MP3 or WAV files.")
        note.setObjectName("Hint")
        note.setWordWrap(True)
        sbox.addWidget(note)
        sbox.addStretch(1)

        tabs.addTab(youtube, "YouTube")
        tabs.addTab(spotify, "Spotify")
        tabs.currentChanged.connect(self._tab_changed)
        outer.addWidget(tabs)

        queue_card, queue_layout = self._card("Downloads")
        count_row = QHBoxLayout()
        self.queue_count = QLabel("0 items")
        self.queue_count.setObjectName("Hint")
        count_row.addWidget(self.queue_count)
        count_row.addStretch(1)
        self.clear_button = MotionButton("Clear finished")
        self.clear_button.setObjectName("TextButton")
        self.clear_button.clicked.connect(self.clear_finished)
        count_row.addWidget(self.clear_button)
        queue_layout.addLayout(count_row)
        self.queue_list = QListWidget()
        self.queue_list.setObjectName("QueueList")
        self.queue_list.setMinimumHeight(150)
        self.queue_list.setMaximumHeight(260)
        queue_layout.addWidget(self.queue_list)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        queue_layout.addWidget(self.progress)
        action_row = QHBoxLayout()
        self.status_label = QLabel("Nothing in motion")
        self.status_label.setObjectName("Hint")
        action_row.addWidget(self.status_label, 1)
        self.stop_button = MotionButton("Stop")
        self.stop_button.setObjectName("StopButton")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_queue)
        action_row.addWidget(self.stop_button)
        self.download_button = MotionButton("Download")
        self.download_button.setObjectName("YoutubeButton")
        self.download_button.clicked.connect(self.start_queue)
        action_row.addWidget(self.download_button)
        queue_layout.addLayout(action_row)
        outer.addWidget(queue_card, 1)

        footer = QLabel("MusicVault")
        footer.setObjectName("Version")
        outer.addWidget(footer, alignment=Qt.AlignRight)

    def _apply_style(self) -> None:
        self.setStyleSheet("""
            QWidget#Root, QMainWindow { background:#080808; color:#F4F4F4; }
            QWidget { color:#F4F4F4; font-family:'Segoe UI',Arial,sans-serif; font-size:10pt; }
            QLabel#Brand { font-size:19pt; font-weight:700; letter-spacing:0.5px; }
            QLabel#Version, QLabel#Hint, QLabel#PathLabel { color:#929292; }
            QLabel#SectionTitle { font-size:12pt; font-weight:650; color:#F6F6F6; }
            QFrame#Card { background:#111111; border:1px solid #242424; border-radius:12px; }
            QLineEdit, QComboBox, QListWidget {
                background:#0C0C0C; border:1px solid #303030; border-radius:8px;
                padding:11px 12px; selection-background-color:#444444;
            }
            QLineEdit:focus, QComboBox:focus { border:1px solid #777777; }
            QComboBox::drop-down { border:0; width:24px; }
            QCheckBox { spacing:9px; color:#C8C8C8; }
            QCheckBox::indicator { width:16px; height:16px; }
            QTabWidget::pane { border:1px solid #242424; border-radius:12px; background:#111111; }
            QTabBar::tab { background:#101010; color:#898989; padding:11px 20px; margin-right:6px;
                           border:1px solid #202020; border-bottom:0; border-top-left-radius:8px; border-top-right-radius:8px; }
            QTabBar::tab:selected { color:#FFFFFF; background:#171717; border-color:#343434; }
            QPushButton { border:0; border-radius:8px; padding:10px 16px; font-weight:600; }
            QPushButton:hover { padding-top:9px; padding-bottom:11px; }
            QPushButton:pressed { padding-top:11px; padding-bottom:9px; }
            QPushButton:disabled { background:#292929; color:#777777; }
            QPushButton#YoutubeButton { background:#D93030; color:#FFFFFF; }
            QPushButton#YoutubeButton:hover { background:#F04444; }
            QPushButton#SpotifyButton { background:#178A45; color:#FFFFFF; }
            QPushButton#SpotifyButton:hover { background:#1DB954; }
            QPushButton#SecondaryButton { background:#242424; color:#E8E8E8; border:1px solid #363636; }
            QPushButton#StopButton { background:#342020; color:#FFB0B0; }
            QPushButton#TextButton { background:transparent; color:#AAAAAA; }
            QListWidget#QueueList { border:0; padding:4px; }
            QListWidget::item { padding:12px; border-bottom:1px solid #252525; }
            QProgressBar { background:#242424; border:0; border-radius:4px; height:8px; text-align:center; }
            QProgressBar::chunk { background:#D93030; border-radius:4px; }
            QStatusBar { color:#929292; }
        """)

    def _tab_changed(self, index: int) -> None:
        accent = "youtube" if index == 0 else "spotify"
        self.statusBar().showMessage("YouTube downloads" if accent == "youtube" else "Spotify link hand-off", 2500)

    def _animate_intro(self) -> None:
        self.setWindowOpacity(0.0)
        self.show()
        self._intro = QPropertyAnimation(self, b"windowOpacity", self)
        self._intro.setDuration(180)
        self._intro.setStartValue(0.0)
        self._intro.setEndValue(1.0)
        self._intro.setEasingCurve(QEasingCurve.OutCubic)
        self._intro.start()

    def choose_folder(self) -> None:
        selected = QFileDialog.getExistingDirectory(self, "Choose download folder", self.output_dir)
        if not selected:
            return
        try:
            self.output_dir = str(validate_output_folder(selected))
            self.folder_label.setText(self.output_dir)
        except Exception as exc:
            QMessageBox.warning(self, APP_NAME, str(exc))

    def add_to_queue(self) -> None:
        try:
            source = validate_source_url(self.url_input.text())
            if not self.permission_check.isChecked():
                raise ValueError("Confirm that you own this content or have permission to save it.")
            if source.is_playlist_only and not self.playlist_check.isChecked():
                raise ValueError("Enable Full playlist for a playlist-only link.")
            if len(self.jobs) >= 100:
                raise ValueError("The queue is full (100 items maximum).")
            folder = str(validate_output_folder(self.output_dir))
            job = Job(source.url, self.format_box.currentText(), folder, self.playlist_check.isChecked())
            self.jobs.append(job)
            item = QListWidgetItem(f"YouTube  ·  {job.output_format}  ·  {source.source_id}  ·  Queued")
            item.setData(Qt.UserRole, len(self.jobs) - 1)
            self.queue_list.addItem(item)
            self.url_input.clear()
            self._update_queue()
            self.statusBar().showMessage("Added to queue", 2500)
        except Exception as exc:
            QMessageBox.warning(self, APP_NAME, str(exc))

    def open_spotify(self) -> None:
        try:
            url = validate_spotify_url(self.spotify_input.text())
            if not QDesktopServices.openUrl(QUrl(url)):
                raise RuntimeError("Could not open Spotify. Check that Spotify or a browser is installed.")
            self.statusBar().showMessage("Opened in Spotify", 3000)
        except Exception as exc:
            QMessageBox.warning(self, APP_NAME, str(exc))

    def _update_queue(self) -> None:
        self.queue_count.setText(f"{len(self.jobs)} items")
        self.download_button.setEnabled(bool(self.jobs) and not self.worker)
        self.clear_button.setEnabled(bool(self.jobs) and not self.worker)

    def start_queue(self) -> None:
        if self.worker or not self.jobs:
            return
        pending = []
        for index, job in enumerate(self.jobs):
            item = self.queue_list.item(index)
            if item and item.text().endswith("Queued"):
                pending.append((index, job))
        if not pending:
            return
        self.cancel_event = threading.Event()
        self.worker = Worker(pending, self.cancel_event)
        self.worker.progress.connect(self._on_progress)
        self.worker.done.connect(self._on_done)
        self.worker.failed.connect(self._on_failed)
        self.worker.stopped.connect(self._on_stopped)
        self.worker.finished.connect(self._on_worker_finished)
        self.download_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status_label.setText("Downloading")
        self.worker.start()

    def stop_queue(self) -> None:
        if self.worker:
            self.cancel_event.set()
            self.stop_button.setEnabled(False)
            self.status_label.setText("Stopping…")

    def _on_progress(self, index: int, value: int, speed: str, eta: str) -> None:
        self.progress.setValue(value)
        self.status_label.setText(" · ".join(part for part in (speed, eta) if part) or "Downloading")
        item = self.queue_list.item(index)
        if item:
            item.setText(f"YouTube  ·  {self.jobs[index].output_format}  ·  {value}%  ·  Downloading")

    def _on_done(self, index: int, fmt: str) -> None:
        item = self.queue_list.item(index)
        if item:
            item.setText(f"YouTube  ·  {fmt}  ·  Done")
        self.progress.setValue(100)

    def _on_failed(self, index: int, message: str) -> None:
        item = self.queue_list.item(index)
        if item:
            item.setText(f"YouTube  ·  {self.jobs[index].output_format}  ·  Failed")
        self.statusBar().showMessage(message, 10000)

    def _on_stopped(self, index: int) -> None:
        item = self.queue_list.item(index)
        if item:
            item.setText(f"YouTube  ·  {self.jobs[index].output_format}  ·  Stopped")

    def _on_worker_finished(self) -> None:
        self.worker = None
        self.stop_button.setEnabled(False)
        self.download_button.setEnabled(bool(self.jobs))
        self.status_label.setText("Ready")
        self.statusBar().showMessage("Queue worker finished", 3000)
        self._update_queue()

    def clear_finished(self) -> None:
        if self.worker:
            return
        retained: list[Job] = []
        for index in range(self.queue_list.count()):
            item = self.queue_list.item(index)
            if item and item.text().endswith("Queued"):
                retained.append(self.jobs[index])
        self.jobs = retained
        self.queue_list.clear()
        for job in self.jobs:
            self.queue_list.addItem(f"YouTube  ·  {job.output_format}  ·  Queued")
        self._update_queue()

    def closeEvent(self, event) -> None:
        if self.worker and self.worker.isRunning():
            self.cancel_event.set()
            self.worker.wait(5000)
        self.settings_sync()
        event.accept()

    def settings_sync(self) -> None:
        # Keep the output path local to the OS user profile; no account is required.
        return


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName(APP_NAME)
    window = MusicVaultWindow()
    if args.smoke_test:
        return 0
    window._animate_intro()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
