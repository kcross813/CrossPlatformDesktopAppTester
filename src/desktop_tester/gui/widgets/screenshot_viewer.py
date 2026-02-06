"""Screenshot viewer widget."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QScrollArea, QVBoxLayout, QWidget


class ScreenshotViewer(QWidget):
    """Displays screenshots captured during test steps."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        self._image_label = QLabel("No screenshot")
        self._image_label.setAlignment(Qt.AlignCenter)
        self._image_label.setStyleSheet("color: #666; font-size: 12px;")
        scroll.setWidget(self._image_label)
        layout.addWidget(scroll)

    def load_screenshot(self, path: str | Path) -> None:
        """Load and display a screenshot from file."""
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            self._image_label.setText("Failed to load screenshot")
            return

        # Scale to fit width while maintaining aspect ratio
        scaled = pixmap.scaledToWidth(
            min(pixmap.width(), self.width() - 20),
            Qt.SmoothTransformation,
        )
        self._image_label.setPixmap(scaled)

    def load_from_bytes(self, png_bytes: bytes) -> None:
        """Load and display a screenshot from PNG bytes."""
        pixmap = QPixmap()
        pixmap.loadFromData(png_bytes, "PNG")
        if pixmap.isNull():
            self._image_label.setText("Failed to load screenshot")
            return

        scaled = pixmap.scaledToWidth(
            min(pixmap.width(), self.width() - 20),
            Qt.SmoothTransformation,
        )
        self._image_label.setPixmap(scaled)

    def clear(self) -> None:
        """Clear the displayed screenshot."""
        self._image_label.clear()
        self._image_label.setText("No screenshot")
