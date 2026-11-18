"""MusicVault mobile UI prototype.

This client is deliberately UI-only. The desktop download worker is not imported:
mobile media execution needs a platform-specific FFmpeg/JavaScript runtime port.
"""
from __future__ import annotations

import argparse
import sys

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFrame, QGraphicsOpacityEffect, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QPushButton, QScrollArea,
    QStackedWidget, QVBoxLayout, QWidget,
)

try:
    from .source_validation import validate_spotify_link, validate_youtube_link
except ImportError:  # Direct script invocation during local preview/deployment.
    from source_validation import validate_spotify_link, validate_youtube_link


FORMATS = ("MP3", "WAV", "FLAC", "M4A", "AAC", "OPUS", "MKV")


class AnimatedButton(QPushButton):
    """Brief opacity feedback on touch without a permanently running animation."""
    def __init__(self, label: str, parent=None):
        super().__init__(label, parent)
        self._opacity = QGraphicsOpacityEffect(self)
        self._opacity.setOpacity(1.0)
        self.setGraphicsEffect(self._opacity)
        self._fade = QPropertyAnimation(self._opacity, b"opacity", self._opacity)
        self._fade.setDuration(105)
        self._fade.setEasingCurve(QEasingCurve.OutCubic)
        self.pressed.connect(lambda: self._animate(0.84))
        self.released.connect(lambda: self._animate(1.0))

    def _animate(self, target: float) -> None:
        self._fade.stop()
        self._fade.setStartValue(self._opacity.opacity())
        self._fade.setEndValue(target)
        self._fade.start()


class MusicVaultMobileWindow(QWidget):
    """Touch-first mobile layout preview shared by Android and iOS builds."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MusicVault")
        self.setObjectName("MobileRoot")
        self.setMinimumSize(320, 560)
        self.resize(390, 844)
        self._build_ui()
        self._apply_style()

    def _card(self, title: str, hint: str | None = None) -> tuple[QFrame, QVBoxLayout]:
        frame = QFrame()
        frame.setObjectName("Card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(11)
        heading = QLabel(title)
        heading.setObjectName("CardTitle")
        layout.addWidget(heading)
        if hint:
            subtitle = QLabel(hint)
            subtitle.setObjectName("Hint")
            subtitle.setWordWrap(True)
            layout.addWidget(subtitle)
        return frame, layout

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(16, 14, 16, 14)
        root_layout.setSpacing(12)

        header = QHBoxLayout()
        mark = QLabel("MV")
        mark.setObjectName("Mark")
        mark.setFixedSize(42, 42)
        mark.setAlignment(Qt.AlignCenter)
        header.addWidget(mark)
        brand_stack = QVBoxLayout()
        brand_stack.setSpacing(1)
        brand = QLabel("MusicVault")
        brand.setObjectName("Brand")
        sub = QLabel("YOUR MUSIC LIBRARY")
        sub.setObjectName("Eyebrow")
        brand_stack.addWidget(brand)
        brand_stack.addWidget(sub)
        header.addLayout(brand_stack)
        header.addStretch(1)
        self.preview_badge = QLabel("BETA")
        self.preview_badge.setObjectName("PreviewBadge")
        header.addWidget(self.preview_badge)
        root_layout.addLayout(header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        page = QWidget()
        page.setObjectName("Page")
        body = QVBoxLayout(page)
        body.setContentsMargins(0, 4, 0, 8)
        body.setSpacing(14)

        title = QLabel("Downloads")
        title.setObjectName("Hero")
        body.addWidget(title)
        lead = QLabel("Add a video or playlist. Choose how to save it.")
        lead.setObjectName("Hint")
        lead.setWordWrap(True)
        body.addWidget(lead)

        tabs = QHBoxLayout()
        tabs.setSpacing(8)
        self.youtube_tab = AnimatedButton("YouTube")
        self.youtube_tab.setObjectName("YoutubeTab")
        self.spotify_tab = AnimatedButton("Spotify")
        self.spotify_tab.setObjectName("SpotifyTab")
        self.youtube_tab.clicked.connect(lambda: self.set_source("youtube"))
        self.spotify_tab.clicked.connect(lambda: self.set_source("spotify"))
        tabs.addWidget(self.youtube_tab, 1)
        tabs.addWidget(self.spotify_tab, 1)
        body.addLayout(tabs)

        self.pages = QStackedWidget()
        self.youtube_page = self._build_youtube_page()
        self.spotify_page = self._build_spotify_page()
        self.pages.addWidget(self.youtube_page)
        self.pages.addWidget(self.spotify_page)
        body.addWidget(self.pages)

        queue_card, queue_layout = self._card("Queue")
        self.queue_stack = QStackedWidget()
        self.queue_empty = QLabel("Nothing queued yet")
        self.queue_empty.setObjectName("EmptyState")
        self.queue_empty.setAlignment(Qt.AlignCenter)
        self.queue_empty.setMinimumHeight(100)
        self.queue = QListWidget()
        self.queue.setObjectName("Queue")
        self.queue.setMinimumHeight(100)
        self.queue.setMaximumHeight(170)
        self.queue_stack.addWidget(self.queue_empty)
        self.queue_stack.addWidget(self.queue)
        queue_layout.addWidget(self.queue_stack)
        self.queue_status = QLabel("Your queue will appear here.")
        self.queue_status.setObjectName("Hint")
        self.queue_status.setWordWrap(True)
        queue_layout.addWidget(self.queue_status)
        body.addWidget(queue_card)

        footer = QLabel("Mobile preview · downloading is not enabled yet")
        footer.setObjectName("Footer")
        footer.setWordWrap(True)
        body.addWidget(footer)
        body.addStretch(1)

        self.scroll.setWidget(page)
        root_layout.addWidget(self.scroll, 1)
        self.set_source("youtube")

    def _build_youtube_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        card, card_layout = self._card("YouTube", "Video or playlist")
        self.youtube_input = QLineEdit()
        self.youtube_input.setObjectName("LinkInput")
        self.youtube_input.setPlaceholderText("Paste YouTube link")
        self.youtube_input.setClearButtonEnabled(True)
        self.youtube_input.setMinimumHeight(46)
        paste_row = QHBoxLayout()
        paste_row.setSpacing(8)
        paste_row.addWidget(self.youtube_input, 1)
        self.youtube_paste = AnimatedButton("Paste")
        self.youtube_paste.setObjectName("SecondaryButton")
        self.youtube_paste.setMinimumHeight(46)
        self.youtube_paste.clicked.connect(lambda: self.youtube_input.setText(QApplication.clipboard().text().strip()))
        paste_row.addWidget(self.youtube_paste)
        card_layout.addLayout(paste_row)

        format_row = QHBoxLayout()
        format_label = QLabel("SAVE AS")
        format_label.setObjectName("Eyebrow")
        format_row.addWidget(format_label)
        format_row.addStretch(1)
        self.format_combo = QComboBox()
        self.format_combo.setObjectName("FormatCombo")
        self.format_combo.addItems(FORMATS)
        format_row.addWidget(self.format_combo)
        card_layout.addLayout(format_row)

        self.playlist_check = QCheckBox("Include full playlist")
        card_layout.addWidget(self.playlist_check)
        self.rights_check = QCheckBox("I can save this content")
        card_layout.addWidget(self.rights_check)

        self.add_button = AnimatedButton("Add to queue")
        self.add_button.setObjectName("YoutubeButton")
        self.add_button.clicked.connect(self.add_youtube_preview)
        card_layout.addWidget(self.add_button)
        layout.addWidget(card)
        return page

    def _build_spotify_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        card, card_layout = self._card("Spotify", "Track, album, artist or playlist")
        self.spotify_input = QLineEdit()
        self.spotify_input.setObjectName("LinkInput")
        self.spotify_input.setPlaceholderText("Paste Spotify link")
        self.spotify_input.setClearButtonEnabled(True)
        self.spotify_input.setMinimumHeight(46)
        paste_row = QHBoxLayout()
        paste_row.setSpacing(8)
        paste_row.addWidget(self.spotify_input, 1)
        self.spotify_paste = AnimatedButton("Paste")
        self.spotify_paste.setObjectName("SecondaryButton")
        self.spotify_paste.setMinimumHeight(46)
        self.spotify_paste.clicked.connect(lambda: self.spotify_input.setText(QApplication.clipboard().text().strip()))
        paste_row.addWidget(self.spotify_paste)
        card_layout.addLayout(paste_row)

        self.open_spotify_button = AnimatedButton("Open in Spotify")
        self.open_spotify_button.setObjectName("SpotifyButton")
        self.open_spotify_button.clicked.connect(self.open_spotify)
        card_layout.addWidget(self.open_spotify_button)
        note = QLabel("Playback and offline listening stay in Spotify. Protected streams are not exported.")
        note.setObjectName("Hint")
        note.setWordWrap(True)
        card_layout.addWidget(note)
        layout.addWidget(card)
        return page

    def set_source(self, source: str) -> None:
        spotify = source == "spotify"
        self.pages.setCurrentIndex(1 if spotify else 0)
        self.youtube_tab.setProperty("active", not spotify)
        self.spotify_tab.setProperty("active", spotify)
        self.youtube_tab.style().unpolish(self.youtube_tab)
        self.youtube_tab.style().polish(self.youtube_tab)
        self.spotify_tab.style().unpolish(self.spotify_tab)
        self.spotify_tab.style().polish(self.spotify_tab)

    def add_youtube_preview(self) -> None:
        try:
            kind = validate_youtube_link(self.youtube_input.text())
            if not self.rights_check.isChecked():
                raise ValueError("Confirm that you can save this content.")
            if kind == "playlist" and not self.playlist_check.isChecked():
                raise ValueError("Turn on full playlist for a playlist-only link.")
            label = f"YouTube · {self.format_combo.currentText()} · {kind.title()}"
            self.queue.addItem(QListWidgetItem(label))
            self.queue_stack.setCurrentIndex(1)
            self.queue_status.setText("Added to preview queue. Downloads are not enabled in this mobile build yet.")
        except ValueError as exc:
            self.queue_status.setText(str(exc))

    def open_spotify(self) -> None:
        try:
            url = validate_spotify_link(self.spotify_input.text())
            opened = QDesktopServices.openUrl(QUrl(url))
            self.queue_status.setText("Opened in Spotify." if opened else "Spotify could not open this link.")
        except ValueError as exc:
            self.queue_status.setText(str(exc))

    def _apply_style(self) -> None:
        self.setStyleSheet("""
            QWidget#MobileRoot, QWidget#Page { background:#0B0D10; color:#F4F6F8; }
            QWidget { color:#F4F6F8; font-family:'Segoe UI',Arial,sans-serif; font-size:14px; }
            QScrollArea, QScrollArea > QWidget > QWidget { background:#0B0D10; border:0; }
            QLabel#Brand { color:#FFFFFF; font-size:19px; font-weight:740; }
            QLabel#Eyebrow { color:#A6B0BD; font-size:11px; font-weight:700; letter-spacing:1px; }
            QLabel#Mark { background:#202630; border:1px solid #37404D; border-radius:14px;
                          color:#FFFFFF; font-weight:800; font-size:15px; }
            QLabel#PreviewBadge { background:#191E26; border:1px solid #3A4553; border-radius:10px;
                                  color:#C0C8D2; padding:7px 10px; font-size:11px; font-weight:700; }
            QLabel#EmptyState { color:#A6B0BD; background:#0F1217; border:1px dashed #3A4553;
                                border-radius:12px; padding:16px; font-size:13px; }
            QLabel#Hero { color:#FFFFFF; font-size:29px; font-weight:760; }
            QLabel#Hint { color:#A6B0BD; font-size:13px; }
            QLabel#CardTitle { color:#F7F8FA; font-size:19px; font-weight:720; }
            QLabel#Footer { color:#A6B0BD; font-size:11px; padding:7px 2px; }
            QFrame#Card { background:#14181F; border:1px solid #2A313C; border-radius:16px; }
            QLineEdit, QComboBox, QListWidget#Queue {
                background:#0F1217; border:1px solid #3A4553; border-radius:11px;
                padding:12px; color:#F4F6F8; selection-background-color:#364354;
            }
            QLineEdit:focus, QComboBox:focus { border:2px solid #8EA0B7; }
            QLineEdit::placeholder { color:#A6B0BD; }
            QComboBox::drop-down { border:0; width:26px; }
            QCheckBox { color:#E2E6EB; spacing:10px; font-size:13px; }
            QCheckBox::indicator { width:20px; height:20px; }
            QCheckBox::indicator:unchecked { background:#0F1217; border:1px solid #718092; border-radius:6px; }
            QCheckBox::indicator:checked { background:#D0DBEA; border:1px solid #D0DBEA; border-radius:6px; }
            QPushButton { min-height:46px; border-radius:11px; font-size:14px; font-weight:700; padding:9px 14px; }
            QPushButton:focus { outline:2px solid #D8E4F2; outline-offset:2px; }\n            QPushButton#YoutubeButton:focus, QPushButton#SpotifyButton:focus, QPushButton#SecondaryButton:focus,\n            QPushButton#StopButton:focus, QPushButton#TextButton:focus, QPushButton#YoutubeTab:focus,\n            QPushButton#SpotifyTab:focus { border:2px solid #F4F6F8; }
            QPushButton#YoutubeTab, QPushButton#SpotifyTab {
                background:#191E26; color:#C0C8D2; border:1px solid #3A4553;
            }
            QPushButton#YoutubeTab[active="true"] { background:#32191D; color:#FFB0B4; border:1px solid #744047; }
            QPushButton#SpotifyTab[active="true"] { background:#14291F; color:#9CE8B9; border:1px solid #356B4B; }
            QPushButton#YoutubeButton { background:#D93640; color:#FFFFFF; border:1px solid #E74D56; }
            QPushButton#YoutubeButton:hover { background:#EA454D; }
            QPushButton#YoutubeButton:pressed { background:#B82C35; }
            QPushButton#SpotifyButton { background:#16864A; color:#FFFFFF; border:1px solid #29985B; }
            QPushButton#SpotifyButton:hover { background:#1A9654; }
            QPushButton#SpotifyButton:pressed { background:#116C3B; }
            QPushButton#SecondaryButton { background:#222832; color:#F0F2F5; border:1px solid #3A4553; }
            QPushButton#SecondaryButton:hover { background:#2B333F; }
            QListWidget#Queue { border:0; padding:4px; }
            QListWidget::item { padding:11px 7px; border-bottom:1px solid #2A313C; }
            QScrollBar:vertical { width:8px; background:#0F1217; margin:4px 0; }
            QScrollBar::handle:vertical { min-height:24px; background:#465160; border-radius:4px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }
        """)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()
    app = QApplication(sys.argv)
    app.setApplicationName("MusicVault Mobile")
    window = MusicVaultMobileWindow()
    if args.smoke_test:
        window.show()
        app.processEvents()
        return 0
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
