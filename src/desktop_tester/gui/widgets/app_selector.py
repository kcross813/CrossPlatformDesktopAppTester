"""Application Selector dialog - lists running applications for targeting."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)


class AppSelectorDialog(QDialog):
    """Dialog for selecting the target application to test."""

    def __init__(self, apps: list[dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Target Application")
        self.setMinimumSize(400, 500)

        self._selected_app: dict | None = None

        layout = QVBoxLayout(self)

        label = QLabel("Select the application to test:")
        label.setStyleSheet("font-size: 14px; padding: 8px;")
        layout.addWidget(label)

        self._list = QListWidget()
        self._list.setStyleSheet("font-size: 13px;")
        for app in apps:
            name = app.get("name", "Unknown")
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, app)
            self._list.addItem(item)

        self._list.itemDoubleClicked.connect(self._on_double_click)
        layout.addWidget(self._list)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @property
    def selected_app(self) -> dict | None:
        return self._selected_app

    def _on_accept(self) -> None:
        current = self._list.currentItem()
        if current:
            self._selected_app = current.data(Qt.UserRole)
        self.accept()

    def _on_double_click(self, item: QListWidgetItem) -> None:
        self._selected_app = item.data(Qt.UserRole)
        self.accept()
