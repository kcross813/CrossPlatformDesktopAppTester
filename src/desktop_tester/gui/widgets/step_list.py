"""Step List / Command Log - center panel showing test steps."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListView,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from desktop_tester.gui.models.step_list_model import StepListModel
from desktop_tester.models.step import Step


class StepList(QWidget):
    """Center panel: ordered list of test steps with status."""

    step_selected = Signal(int)  # row index
    add_step_requested = Signal()
    delete_step_requested = Signal(int)  # row index

    def __init__(self, parent=None):
        super().__init__(parent)
        self._model = StepListModel()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QLabel("  COMMAND LOG")
        header.setStyleSheet(
            "background-color: #2a2a2a; padding: 8px; font-weight: bold; "
            "font-size: 11px; color: #888; border-bottom: 1px solid #444;"
        )
        layout.addWidget(header)

        # List view
        self._list_view = QListView()
        self._list_view.setModel(self._model)
        self._list_view.setSpacing(2)
        self._list_view.setStyleSheet("""
            QListView::item {
                padding: 6px 8px;
                border-bottom: 1px solid #2a2a2a;
                font-family: monospace;
                font-size: 13px;
            }
        """)
        self._list_view.clicked.connect(
            lambda idx: self.step_selected.emit(idx.row())
        )
        layout.addWidget(self._list_view)

        # Status bar at bottom
        self._status_bar = QWidget()
        status_layout = QHBoxLayout(self._status_bar)
        status_layout.setContentsMargins(8, 4, 8, 4)

        self._status_label = QLabel("No test loaded")
        self._status_label.setStyleSheet("color: #888; font-size: 12px;")
        status_layout.addWidget(self._status_label)

        status_layout.addStretch()

        add_btn = QPushButton("+ Add Step")
        add_btn.setToolTip("Add a new step")
        add_btn.clicked.connect(self.add_step_requested)
        status_layout.addWidget(add_btn)

        del_btn = QPushButton("Delete Step")
        del_btn.setToolTip("Delete the selected step")
        del_btn.clicked.connect(self._on_delete_clicked)
        status_layout.addWidget(del_btn)

        self._status_bar.setStyleSheet("background-color: #2a2a2a; border-top: 1px solid #444;")
        layout.addWidget(self._status_bar)

    @property
    def model(self) -> StepListModel:
        return self._model

    def selected_row(self) -> int | None:
        """Return the currently selected row index, or None."""
        indexes = self._list_view.selectedIndexes()
        if indexes:
            return indexes[0].row()
        return None

    def _on_delete_clicked(self) -> None:
        row = self.selected_row()
        if row is not None:
            self.delete_step_requested.emit(row)

    def set_status(self, text: str) -> None:
        """Update the status label at the bottom."""
        self._status_label.setText(text)
