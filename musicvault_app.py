"""MusicVault desktop application."""
from __future__ import annotations

import argparse
import os
import sys
import threading
import shiboken6
from dataclasses import dataclass

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QSettings, QThread, QTimer, Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QFontMetrics, QIcon
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFileDialog, QFrame, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMessageBox, QStackedWidget,
    QProgressBar, QPushButton, QTabWidget, QVBoxLayout, QWidget, QGraphicsOpacityEffect,
    QSizePolicy,
)

from musicvault_core import (
    APP_NAME, APP_VERSION, DownloadCancelled, build_ydl_options,
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

                options = build_ydl_options(
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
        self._opacity = QGraphicsOpacityEffect(self)
        self._opacity.setOpacity(1.0)
        self.setGraphicsEffect(self._opacity)
        self._fade = QPropertyAnimation(self._opacity, b"opacity", self._opacity)
        self._fade.setDuration(110)
        self._fade.setEasingCurve(QEasingCurve.OutCubic)
        self.pressed.connect(lambda: self._animate(0.82))
        self.released.connect(lambda: self._animate(1.0))

    def _animate(self, value: float) -> None:
        self._fade.stop()
        self._fade.setStartValue(self._opacity.opacity())
        self._fade.setEndValue(value)
        self._fade.start()


class ElidedPathLabel(QLabel):
    """Show long output paths without letting them push over adjacent controls."""

    def __init__(self, text: str, parent=None):
        self.full_text = text
        super().__init__(parent)
        self.setObjectName("PathLabel")
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.setWordWrap(False)
        self.setMinimumWidth(0)
        self.setMinimumHeight(36)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.set_full_text(text)

    def set_full_text(self, text: str) -> None:
        self.full_text = text
        self.setToolTip(text)
        self._update_elided_text()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._update_elided_text()

    def _update_elided_text(self) -> None:
        metrics = QFontMetrics(self.font())
        text = metrics.elidedText(self.full_text, Qt.TextElideMode.ElideMiddle, self.contentsRect().width())
        QLabel.setText(self, text)


class MusicVaultWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} — Downloads")
        self.setMinimumSize(980, 820)
        self.resize(1120, 900)
        self.jobs: list[Job] = []
        self.worker: Worker | None = None
        self.cancel_event = threading.Event()
        self.settings = QSettings(APP_NAME, APP_NAME)
        default_output = os.path.join(os.path.expanduser("~"), "Music", APP_NAME)
        self.output_dir = str(self.settings.value("output_dir", default_output, type=str))
        self._build_ui()
        self._apply_style()
        self.statusBar().showMessage("Ready")

    def _card(self, title: str) -> tuple[QFrame, QVBoxLayout]:
        card = QFrame()
        card.setObjectName("Card")
        card.setProperty("musicVaultCard", True)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(14)
        label = QLabel(title)
        label.setObjectName("SectionTitle")
        layout.addWidget(label)
        return card, layout

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("Root")
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(30, 22, 30, 16)
        outer.setSpacing(19)

        # Compact app header.
        header = QHBoxLayout()
        header.setSpacing(12)
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "musicvault-icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            icon = QLabel()
            icon.setPixmap(QIcon(icon_path).pixmap(42, 42))
            icon.setFixedSize(46, 46)
            header.addWidget(icon)

        brand_stack = QVBoxLayout()
        brand_stack.setSpacing(1)
        brand = QLabel("MusicVault")
        brand.setObjectName("Brand")
        sub = QLabel("MEDIA LIBRARY")
        sub.setObjectName("Eyebrow")
        brand_stack.addWidget(brand)
        brand_stack.addWidget(sub)
        header.addLayout(brand_stack)
        header.addStretch(1)

        local_badge = QLabel("●  ON-DEVICE LIBRARY")
        local_badge.setObjectName("LocalBadge")
        header.addWidget(local_badge)
        version = QLabel(APP_VERSION)
        version.setObjectName("Version")
        header.addWidget(version)
        outer.addLayout(header)

        columns = QHBoxLayout()
        columns.setSpacing(20)

        # Left: source and export controls.
        left_column = QVBoxLayout()
        left_column.setSpacing(18)

        intro = QVBoxLayout()
        intro.setSpacing(6)
        intro_eyebrow = QLabel("YOUR MUSIC, ORGANIZED")
        intro_eyebrow.setObjectName("HeroEyebrow")
        intro.addWidget(intro_eyebrow)
        page_title = QLabel("Downloads")
        page_title.setObjectName("PageTitle")
        intro.addWidget(page_title)
        page_hint = QLabel("A calm home for the audio you’re allowed to keep.")
        page_hint.setObjectName("Hint")
        intro.addWidget(page_hint)
        left_column.addLayout(intro)

        tabs = QTabWidget()
        tabs.setObjectName("SourceTabs")
        tabs.setDocumentMode(True)
        tabs.setMovable(False)

        youtube = QWidget()
        ybox = QVBoxLayout(youtube)
        ybox.setContentsMargins(12, 10, 12, 10)
        ybox.setSpacing(16)

        source_card, source_layout = self._card("YouTube")
        source_card.setObjectName("YouTubeCard")
        source_hint = QLabel("Paste a video or playlist URL")
        source_hint.setObjectName("Hint")
        source_layout.addWidget(source_hint)

        row = QHBoxLayout()
        row.setSpacing(8)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("youtube.com/watch?v=…")
        self.url_input.setClearButtonEnabled(True)
        self.url_input.setMinimumHeight(44)
        self.url_input.setAccessibleName("YouTube video or playlist link")
        self.url_input.returnPressed.connect(self.add_to_queue)
        row.addWidget(self.url_input, 1)

        paste = MotionButton("Paste")
        paste.setObjectName("SecondaryButton")
        paste.setMinimumHeight(44)
        paste.clicked.connect(lambda: self.url_input.setText(QApplication.clipboard().text().strip()))
        row.addWidget(paste)
        source_layout.addLayout(row)

        self.permission_check = QCheckBox("The source and rights holders permit this save.")
        self.permission_check.setObjectName("PermissionCheck")
        source_layout.addWidget(self.permission_check)
        ybox.addWidget(source_card)

        settings_card, settings_layout = self._card("Export settings")
        settings_card.setObjectName("ExportSettingsCard")
        settings_row = QHBoxLayout()
        settings_row.setSpacing(12)

        format_group = QVBoxLayout()
        format_group.setSpacing(6)
        format_label = QLabel("FORMAT")
        format_label.setObjectName("Eyebrow")
        format_group.addWidget(format_label)
        self.format_box = QComboBox()
        self.format_box.addItems(ALL_FORMATS)
        self.format_box.setMinimumHeight(46)
        self.format_box.setAccessibleName("Output format")
        format_group.addWidget(self.format_box)
        settings_row.addLayout(format_group, 1)

        playlist_group = QVBoxLayout()
        playlist_group.setSpacing(6)
        playlist_label = QLabel("PLAYLIST")
        playlist_label.setObjectName("Eyebrow")
        playlist_group.addWidget(playlist_label)
        self.playlist_check = QCheckBox("Full playlist")
        self.playlist_check.setMinimumHeight(46)
        playlist_group.addWidget(self.playlist_check)
        settings_row.addLayout(playlist_group, 1)
        settings_layout.addLayout(settings_row)

        folder_row = QHBoxLayout()
        folder_row.setSpacing(8)
        folder_stack = QVBoxLayout()
        folder_stack.setSpacing(5)
        folder_caption = QLabel("SAVE LOCATION")
        folder_caption.setObjectName("Eyebrow")
        folder_stack.addWidget(folder_caption)
        self.folder_label = ElidedPathLabel(self.output_dir)
        folder_stack.addWidget(self.folder_label)
        folder_row.addLayout(folder_stack, 1)

        browse = MotionButton("Change")
        browse.setObjectName("SecondaryButton")
        browse.setMinimumHeight(44)
        browse.clicked.connect(self.choose_folder)
        folder_row.addWidget(browse, 0, Qt.AlignBottom)
        settings_layout.addLayout(folder_row)

        add_button = MotionButton("Add to queue")
        add_button.setObjectName("YoutubeButton")
        add_button.setMinimumHeight(50)
        add_button.clicked.connect(self.add_to_queue)
        settings_layout.addWidget(add_button)
        settings_card.setMinimumHeight(286)
        ybox.addWidget(settings_card)
        ybox.addStretch(1)

        spotify = QWidget()
        sbox = QVBoxLayout(spotify)
        sbox.setContentsMargins(14, 16, 14, 16)
        sbox.setSpacing(14)

        spotify_card, spotify_layout = self._card("Spotify")
        spotify_card.setObjectName("SpotifyCard")
        spotify_hint = QLabel("Open a track, album, artist or playlist")
        spotify_hint.setObjectName("Hint")
        spotify_layout.addWidget(spotify_hint)
        self.spotify_input = QLineEdit()
        self.spotify_input.setPlaceholderText("open.spotify.com/…")
        self.spotify_input.setClearButtonEnabled(True)
        self.spotify_input.setMinimumHeight(44)
        self.spotify_input.setAccessibleName("Spotify share link")
        self.spotify_input.returnPressed.connect(self.open_spotify)
        spotify_layout.addWidget(self.spotify_input)

        spotify_actions = QHBoxLayout()
        spotify_paste = MotionButton("Paste")
        spotify_paste.setObjectName("SecondaryButton")
        spotify_paste.setMinimumHeight(44)
        spotify_paste.clicked.connect(lambda: self.spotify_input.setText(QApplication.clipboard().text().strip()))
        spotify_actions.addWidget(spotify_paste)
        spotify_actions.addStretch(1)
        open_button = MotionButton("Open in Spotify")
        open_button.setObjectName("SpotifyButton")
        open_button.setMinimumHeight(44)
        open_button.clicked.connect(self.open_spotify)
        spotify_actions.addWidget(open_button)
        spotify_layout.addLayout(spotify_actions)

        note = QLabel("Spotify keeps playback and offline listening in its app. MusicVault can’t export Spotify streams. For files, use an artist-authorized download, such as a Bandcamp purchase or a SoundCloud track with downloads enabled.")
        note.setObjectName("SpotifyNote")
        note.setWordWrap(True)
        spotify_layout.addWidget(note)
        sbox.addWidget(spotify_card)
        sources_card, sources_layout = self._card("Downloadable music")
        sources_hint = QLabel("Get files directly from artists and authorized storefronts.")
        sources_hint.setObjectName("Hint")
        sources_layout.addWidget(sources_hint)
        source_links = QHBoxLayout()
        source_links.setSpacing(8)
        bandcamp_button = MotionButton("Explore Bandcamp")
        bandcamp_button.setObjectName("SecondaryButton")
        bandcamp_button.setMinimumHeight(44)
        bandcamp_button.clicked.connect(lambda: self._open_music_source("https://bandcamp.com/"))
        source_links.addWidget(bandcamp_button)
        soundcloud_button = MotionButton("Explore SoundCloud")
        soundcloud_button.setObjectName("SecondaryButton")
        soundcloud_button.setMinimumHeight(44)
        soundcloud_button.clicked.connect(lambda: self._open_music_source("https://soundcloud.com/"))
        source_links.addWidget(soundcloud_button)
        sources_layout.addLayout(source_links)
        sbox.addWidget(sources_card)
        sbox.addStretch(1)

        tabs.addTab(youtube, "YouTube  ·  authorized sources")
        tabs.addTab(spotify, "Spotify  ·  listening")
        tabs.currentChanged.connect(self._tab_changed)
        left_column.addWidget(tabs, 1)
        columns.addLayout(left_column, 7)

        # Right: live queue and concise format reference.
        right_column = QVBoxLayout()
        right_column.setSpacing(16)

        queue_card, queue_layout = self._card("Download queue")
        queue_card.setObjectName("QueueCard")
        queue_header = QHBoxLayout()
        self.queue_count = QLabel("0 ITEMS")
        self.queue_count.setObjectName("QueueCount")
        queue_header.addWidget(self.queue_count)
        queue_header.addStretch(1)
        self.clear_button = MotionButton("Clear finished")
        self.clear_button.setObjectName("TextButton")
        self.clear_button.clicked.connect(self.clear_finished)
        queue_header.addWidget(self.clear_button)
        queue_layout.addLayout(queue_header)

        self.queue_stack = QStackedWidget()
        self.queue_empty = QLabel("Your queue is clear\n\nAdd an authorized source to get started.")
        self.queue_empty.setObjectName("EmptyState")
        self.queue_empty.setAlignment(Qt.AlignCenter)
        self.queue_empty.setWordWrap(True)
        self.queue_list = QListWidget()
        self.queue_list.setObjectName("QueueList")
        self.queue_list.setMinimumHeight(176)
        self.queue_list.setAccessibleName("Download queue")
        self.queue_stack.addWidget(self.queue_empty)
        self.queue_stack.addWidget(self.queue_list)
        queue_layout.addWidget(self.queue_stack)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(8)
        queue_layout.addWidget(self.progress)

        action_row = QHBoxLayout()
        self.status_label = QLabel("Ready when you are")
        self.status_label.setObjectName("Hint")
        action_row.addWidget(self.status_label, 1)
        self.stop_button = MotionButton("Stop")
        self.stop_button.setObjectName("StopButton")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_queue)
        action_row.addWidget(self.stop_button)
        self.download_button = MotionButton("Download")
        self.download_button.setObjectName("YoutubeButton")
        self.download_button.setEnabled(False)
        self.download_button.clicked.connect(self.start_queue)
        action_row.addWidget(self.download_button)
        queue_layout.addLayout(action_row)
        right_column.addWidget(queue_card, 1)

        formats_card, formats_layout = self._card("Supported formats")
        formats_card.setObjectName("FormatsCard")
        formats_hint = QLabel("Choose the output that fits your library.")
        formats_hint.setObjectName("Hint")
        formats_layout.addWidget(formats_hint)
        format_names = ("MP3", "WAV", "FLAC", "M4A", "AAC", "OPUS", "MKV")
        format_rows = QHBoxLayout()
        format_rows.setSpacing(6)
        for name in format_names:
            pill = QLabel(name)
            pill.setObjectName("FormatPill")
            pill.setAlignment(Qt.AlignCenter)
            format_rows.addWidget(pill)
        formats_layout.addLayout(format_rows)
        right_column.addWidget(formats_card)
        columns.addLayout(right_column, 5)

        outer.addLayout(columns, 1)
        footer = QLabel("MusicVault  ·  Files stay on this device")
        footer.setObjectName("Footer")
        outer.addWidget(footer, alignment=Qt.AlignRight)

    def _apply_style(self) -> None:
        self.setStyleSheet("""
            QMainWindow, QWidget#Root { background:#090B0E; color:#F4F6F8; }
            QWidget { color:#F4F6F8; font-family:'Segoe UI',Arial,sans-serif; font-size:10pt; }
            QLabel#Brand { font-size:20pt; font-weight:760; letter-spacing:0.1px; color:#FFFFFF; }
            QLabel#PageTitle { font-size:28pt; font-weight:760; letter-spacing:-0.6px; color:#FFFFFF; }
            QLabel#HeroEyebrow { color:#E7777E; font-size:8pt; font-weight:750; letter-spacing:1.5px; }
            QLabel#Eyebrow { color:#A8B2C0; font-size:8pt; font-weight:720; letter-spacing:1.1px; }
            QLabel#Version, QLabel#Hint, QLabel#PathLabel, QLabel#Footer { color:#A8B2C0; }
            QLabel#Hint { font-size:10pt; }
            QLabel#Footer { font-size:9pt; }
            QLabel#LocalBadge { background:#14221B; color:#BCE8CB; border:1px solid #315B40;
                                border-radius:12px; padding:10px 14px; font-size:8pt; font-weight:730; }
            QLabel#SectionTitle { font-size:14pt; font-weight:740; color:#F7F8FA; }
            QLabel#QueueCount { color:#B7C1CE; font-size:8pt; font-weight:730; letter-spacing:1px; }
            QLabel#EmptyState { color:#B8C2CF; background:#0D1116; border:1px dashed #343E4B;
                                border-radius:16px; padding:24px; font-size:10pt; }
            QLabel#SpotifyNote { color:#C2CBD6; background:#0F1713; border:1px solid #263B2F;
                                 border-radius:12px; padding:14px; font-size:9pt; }
            QLabel#FormatPill { background:#171E27; border:1px solid #303B49; color:#DDE4EC;
                                border-radius:10px; padding:9px 5px; font-size:9pt; font-weight:720; }
            QFrame[musicVaultCard="true"] { background:#12161C; border:1px solid #28313C; border-radius:19px; }
            QLineEdit, QComboBox, QListWidget {
                background:#0D1116; border:1px solid #303B48; border-radius:12px;
                padding:11px 13px; color:#F4F6F8; selection-background-color:#364354;
            }
            QLineEdit:focus, QComboBox:focus { border:2px solid #899DB6; background:#111720; }
            QLineEdit::placeholder { color:#9AA6B5; }
            QComboBox::drop-down { border:0; width:28px; }
            QCheckBox { spacing:10px; color:#E1E6ED; }
            QCheckBox::indicator { width:19px; height:19px; }
            QCheckBox::indicator:unchecked { background:#0E1218; border:1px solid #748194; border-radius:6px; }
            QCheckBox::indicator:checked { background:#D5DFEC; border:1px solid #D5DFEC; border-radius:6px; }
            QTabWidget#SourceTabs { background:transparent; }
            QTabWidget#SourceTabs::pane { border:0; background:transparent; top:0; }
            QTabWidget#SourceTabs::tab-bar { background:transparent; }
            QTabBar { background:transparent; }
            QTabBar::tab { min-width:112px; color:#AEB9C7; background:#11151B;
                           padding:13px 18px; margin-right:8px; border:1px solid #27303B;
                           border-radius:12px; font-weight:690; }
            QTabBar::tab:selected { color:#FFFFFF; background:#261619; border-color:#714047; }
            QTabBar::tab:hover:!selected { color:#F0F3F6; background:#1A2029; }
            QPushButton { color:#F4F6F8; border:1px solid transparent; border-radius:11px;
                          padding:6px 14px; font-weight:700; min-height:22px; }
            QPushButton:focus { border:2px solid #F4F6F8; }
            QPushButton:disabled { background:#242A33; color:#8C96A4; border-color:#303844; }
            QPushButton#YoutubeButton { background:#D93A44; color:#FFFFFF; border-color:#E75058; }
            QPushButton#YoutubeButton:hover { background:#E64952; }
            QPushButton#YoutubeButton:pressed { background:#BA2D36; }
            QPushButton#SpotifyButton { background:#16864A; color:#FFFFFF; border-color:#29985B; }
            QPushButton#SpotifyButton:hover { background:#1A9654; }
            QPushButton#SecondaryButton { background:#222A35; color:#F0F3F6; border-color:#3B4655; }
            QPushButton#SecondaryButton:hover { background:#2D3744; }
            QPushButton#StopButton { background:#302022; color:#FFC0C0; border-color:#63373C; }
            QPushButton#TextButton { background:transparent; color:#B8C2CE; padding:6px 9px; }
            QPushButton#TextButton:hover { color:#FFFFFF; background:#202630; }
            QListWidget#QueueList { border:0; padding:5px; background:#0E1218; }
            QListWidget::item { padding:13px 11px; border-bottom:1px solid #29323E; }
            QListWidget::item:selected { background:#242D39; border-radius:7px; }
            QProgressBar { background:#252C36; border:0; border-radius:4px; height:8px; }
            QProgressBar::chunk { background:#D93640; border-radius:4px; }
            QStatusBar { color:#A8B2C0; background:#090B0E; border-top:1px solid #202630; }
        """)

    def _tab_changed(self, index: int) -> None:
        self.statusBar().showMessage("YouTube downloads" if index == 0 else "Spotify link hand-off", 2500)

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
            self.settings.setValue("output_dir", self.output_dir)
            self.folder_label.set_full_text(self.output_dir)
        except Exception as exc:
            QMessageBox.warning(self, APP_NAME, str(exc))

    def add_to_queue(self) -> None:
        try:
            source = validate_source_url(self.url_input.text())
            if not self.permission_check.isChecked():
                raise ValueError("Confirm the source permits this save and you have any required rights-holder permission.")
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
            self.queue_stack.setCurrentIndex(1)
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

    def _open_music_source(self, url: str) -> None:
        if not QDesktopServices.openUrl(QUrl(url)):
            QMessageBox.warning(self, APP_NAME, "Could not open your browser. Please try again.")

    def _update_queue(self) -> None:
        self.queue_count.setText(f"{len(self.jobs)} ITEMS")
        if hasattr(self, "queue_stack"):
            self.queue_stack.setCurrentIndex(1 if self.queue_list.count() else 0)
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
        self.queue_stack.setCurrentIndex(1 if self.queue_list.count() else 0)

    def closeEvent(self, event) -> None:
        if self.worker and self.worker.isRunning():
            self.cancel_event.set()
            self.worker.wait(5000)
        self.settings_sync()
        event.accept()

    def settings_sync(self) -> None:
        # QSettings stores this path in the current OS user's application-data area.
        self.settings.setValue("output_dir", self.output_dir)
        self.settings.sync()


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
        # Exercise real widget construction, layout, paint, and deterministic
        # QObject destruction before CPython runs PySide's process-exit cleanup.
        window.show()
        app.processEvents()
        window.close()
        app.processEvents()
        shiboken6.delete(window)
        shiboken6.delete(app)
        return 0
    window._animate_intro()
    exit_code = app.exec()
    window.close()
    app.processEvents()
    shiboken6.delete(window)
    shiboken6.delete(app)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
