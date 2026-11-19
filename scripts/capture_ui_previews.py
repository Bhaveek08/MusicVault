"""Render desktop and mobile MusicVault UI previews to PNG files."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from PySide6.QtCore import QSize, Qt

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from PySide6.QtGui import QPixmap
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QTabWidget

from musicvault_app import MusicVaultWindow
from mobile.app.main import MusicVaultMobileWindow


def render(widget, output: Path, size: QSize, *, desktop_tab: int | None = None, mobile_source: str | None = None) -> None:
    widget.resize(size)
    if desktop_tab is not None:
        tabs = widget.findChild(QTabWidget, "SourceTabs")
        if tabs is None:
            raise RuntimeError("Desktop source tabs were not found.")
        tabs.setCurrentIndex(desktop_tab)
    if mobile_source is not None:
        widget.set_source(mobile_source)

    widget.show()
    QApplication.processEvents()
    QTest.qWait(450)
    widget.repaint()
    QApplication.processEvents()

    screen = QApplication.primaryScreen()
    image = screen.grabWindow(widget.winId()) if screen is not None else QPixmap()
    if image.isNull():
        raise RuntimeError("Could not capture the visible MusicVault window.")
    if image.size() != widget.size():
        image = image.scaled(
            widget.size(),
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    if not image.save(str(output), "PNG"):
        raise RuntimeError(f"Could not save UI preview to {output}")
    widget.close()


def main() -> int:
    if sys.platform.startswith("linux") and not __import__("os").environ.get("DISPLAY"):
        raise RuntimeError("On Linux, run screenshot capture inside Xvfb (xvfb-run -a).")
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("artifacts/ui-preview"))
    args = parser.parse_args()

    app = QApplication(["musicvault-ui-preview"])
    app.setApplicationName("MusicVault UI Preview")

    desktop_youtube = MusicVaultWindow()
    desktop_youtube.folder_label.set_full_text("~/Music/MusicVault")
    render(desktop_youtube, args.output / "desktop-youtube.png", QSize(1200, 820), desktop_tab=0)

    desktop_spotify = MusicVaultWindow()
    desktop_spotify.folder_label.set_full_text("~/Music/MusicVault")
    render(desktop_spotify, args.output / "desktop-spotify.png", QSize(1200, 820), desktop_tab=1)

    mobile_youtube = MusicVaultMobileWindow()
    render(mobile_youtube, args.output / "mobile-prototype-youtube.png", QSize(390, 844), mobile_source="youtube")

    mobile_spotify = MusicVaultMobileWindow()
    render(mobile_spotify, args.output / "mobile-prototype-spotify.png", QSize(390, 844), mobile_source="spotify")

    print(f"Captured 4 UI previews in {args.output}", flush=True)
    # PySide6 6.12 can SIGBUS during process teardown under hosted Xvfb after
    # the PNGs have been saved. This helper is a one-shot CI process, so skip
    # Qt's unstable global teardown only after every screenshot write succeeded.
    sys.stdout.flush()
    os._exit(0)


if __name__ == "__main__":
    raise SystemExit(main())
