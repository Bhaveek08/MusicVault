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
            QWidget#MobileRoot, QWidget#Page { background:#080808; color:#F5F5F5; }
            QWidget { font-family:'Arial',sans-serif; font-size:14px; }
            QLabel#Brand { color:#FFFFFF; font-size:19px; font-weight:700; }
            QLabel#Eyebrow { color:#818181; font-size:9px; font-weight:700; letter-spacing:1px; }
            QLabel#Mark { background:#171717; border:1px solid #333333; border-radius:12px;
                          color:#FFFFFF; font-weight:800; font-size:15px; }
            QLabel#PreviewBadge { background:#171717; border:1px solid #303030; border-radius:9px;
                                  color:#AAAAAA; padding:6px 9px; font-size:9px; font-weight:700; }
            QLabel#EmptyState { color:#777F8A; background:#0A0B0D; border:1px dashed #303030;
                                border-radius:10px; padding:16px; font-size:12px; }
            QLabel#Hero { font-size:26px; font-weight:750; color:#FFFFFF; }
            QLabel#Hint { color:#999999; font-size:12px; }
            QLabel#CardTitle { color:#F7F7F7; font-size:17px; font-weight:700; }
            QLabel#Footer { color:#707070; font-size:10px; padding:5px 2px; }
            QFrame#Card { background:#121212; border:1px solid #292929; border-radius:16px; }
            QLineEdit, QComboBox, QListWidget#Queue {
                background:#0A0A0A; border:1px solid #333333; border-radius:10px;
                padding:12px; color:#FFFFFF; selection-background-color:#343434;
            }
            QLineEdit:focus, QComboBox:focus { border:1px solid #777777; }
            QComboBox::drop-down { border:0; width:22px; }
            QCheckBox { color:#C8C8C8; spacing:9px; font-size:12px; }
            QCheckBox::indicator { width:17px; height:17px; }
            QPushButton { min-height:42px; border-radius:11px; font-size:13px; font-weight:700; padding:8px 13px; }
            QPushButton#YoutubeTab { background:#171717; color:#AAAAAA; border:1px solid #303030; }
            QPushButton#SpotifyTab { background:#171717; color:#AAAAAA; border:1px solid #303030; }
            QPushButton#YoutubeTab[active="true"] { background:#2A1717; color:#FF7777; border:1px solid #743333; }
            QPushButton#SpotifyTab[active="true"] { background:#132519; color:#58D487; border:1px solid #2E7045; }
            QPushButton#YoutubeButton { background:#D73535; color:white; border:1px solid #E64B4B; }
            QPushButton#YoutubeButton:hover { background:#E54545; }
            QPushButton#YoutubeButton:pressed { background:#B82424; }
            QPushButton#SpotifyButton { background:#168A47; color:white; border:1px solid #229D57; }
            QPushButton#SpotifyButton:hover { background:#1AA354; }
            QPushButton#SpotifyButton:pressed { background:#116B35; }
            QPushButton#SecondaryButton { background:#20252D; color:#DFE5ED; border:1px solid #353D48; }
            QPushButton#SecondaryButton:hover { background:#2A323D; }
            QListWidget#Queue { border:0; padding:3px; }
            QListWidget::item { padding:9px 5px; border-bottom:1px solid #222222; }
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
