"""Test Explorer - left sidebar tree view of test files."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from desktop_tester.gui.models.test_tree_model import TestTreeModel


class TestExplorer(QWidget):
    """Left panel: project tree of test files."""

    test_selected = Signal(object)  # Path
    test_deleted = Signal(object)  # Path
    new_project_requested = Signal()
    open_project_requested = Signal()
    new_test_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._model = TestTreeModel()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QLabel("  TEST EXPLORER")
        header.setStyleSheet(
            "background-color: #2a2a2a; padding: 8px; font-weight: bold; "
            "font-size: 11px; color: #888; border-bottom: 1px solid #444;"
        )
        layout.addWidget(header)

        # Action buttons
        btn_style = (
            "QPushButton { background: #2a2a2a; border: 1px solid #444; "
            "color: #ccc; padding: 5px 8px; border-radius: 3px; font-size: 12px; }"
            "QPushButton:hover { background: #3a3a3a; border-color: #58a6ff; }"
        )

        project_row = QHBoxLayout()
        project_row.setContentsMargins(6, 6, 6, 0)
        project_row.setSpacing(4)

        new_project_btn = QPushButton("New Project")
        new_project_btn.setStyleSheet(btn_style)
        new_project_btn.clicked.connect(self.new_project_requested)
        project_row.addWidget(new_project_btn)

        open_project_btn = QPushButton("Open Project")
        open_project_btn.setStyleSheet(btn_style)
        open_project_btn.clicked.connect(self.open_project_requested)
        project_row.addWidget(open_project_btn)

        layout.addLayout(project_row)

        test_row = QHBoxLayout()
        test_row.setContentsMargins(6, 4, 6, 6)
        test_row.setSpacing(4)

        new_test_btn = QPushButton("+ New Test")
        new_test_btn.setStyleSheet(btn_style)
        new_test_btn.clicked.connect(self.new_test_requested)
        test_row.addWidget(new_test_btn)

        layout.addLayout(test_row)

        # Tree view
        self._tree = QTreeView()
        self._tree.setModel(self._model)
        self._tree.setHeaderHidden(True)
        self._tree.setIndentation(16)
        self._tree.doubleClicked.connect(self._on_double_click)
        self._tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._on_context_menu)
        layout.addWidget(self._tree)

    @property
    def model(self) -> TestTreeModel:
        return self._model

    def load_project(self, project_dir: Path, tests_dir: str = "tests") -> None:
        """Load the test files from a project directory."""
        self._model.load_project(project_dir, tests_dir)
        self._tree.expandAll()

    def _on_double_click(self, index) -> None:
        path = self._model.get_file_path(index)
        if path and path.suffix == ".yaml":
            self.test_selected.emit(path)

    def _on_context_menu(self, pos) -> None:
        index = self._tree.indexAt(pos)
        if not index.isValid():
            return
        path = self._model.get_file_path(index)
        if not path or path.suffix != ".yaml":
            return

        menu = QMenu(self)
        delete_action = menu.addAction("Delete Test")
        action = menu.exec(self._tree.viewport().mapToGlobal(pos))
        if action == delete_action:
            self._confirm_delete(path)

    def _confirm_delete(self, path: Path) -> None:
        reply = QMessageBox.question(
            self,
            "Delete Test",
            f"Are you sure you want to delete '{path.name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            path.unlink()
            self.test_deleted.emit(path)
