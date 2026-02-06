"""Qt Model for the test explorer tree view."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt
from PySide6.QtGui import QColor


class TestFileItem:
    """A node in the test explorer tree."""

    def __init__(self, name: str, path: Path | None = None, parent: TestFileItem | None = None):
        self.name = name
        self.path = path
        self.parent = parent
        self.children: list[TestFileItem] = []
        self.status: str = ""  # "", "passed", "failed", "error"

    def append_child(self, child: TestFileItem) -> None:
        child.parent = self
        self.children.append(child)

    def child(self, row: int) -> TestFileItem | None:
        if 0 <= row < len(self.children):
            return self.children[row]
        return None

    def child_count(self) -> int:
        return len(self.children)

    def row(self) -> int:
        if self.parent:
            return self.parent.children.index(self)
        return 0


class TestTreeModel(QAbstractItemModel):
    """Model backing the test explorer tree."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._root = TestFileItem("Root")

    def load_project(self, project_dir: Path, tests_dir_name: str = "tests") -> None:
        """Scan the tests directory and build the tree."""
        self.beginResetModel()
        self._root = TestFileItem("Root")

        tests_dir = project_dir / tests_dir_name
        if tests_dir.is_dir():
            project_item = TestFileItem(project_dir.name, project_dir)
            self._root.append_child(project_item)

            for test_file in sorted(tests_dir.glob("*.yaml")):
                item = TestFileItem(test_file.stem, test_file)
                project_item.append_child(item)

        self.endResetModel()

    def index(self, row: int, column: int = 0, parent=QModelIndex()) -> QModelIndex:
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        parent_item = parent.internalPointer() if parent.isValid() else self._root
        child_item = parent_item.child(row)
        if child_item:
            return self.createIndex(row, column, child_item)
        return QModelIndex()

    def parent(self, index: QModelIndex) -> QModelIndex:
        if not index.isValid():
            return QModelIndex()

        child_item: TestFileItem = index.internalPointer()
        parent_item = child_item.parent

        if parent_item is None or parent_item == self._root:
            return QModelIndex()

        return self.createIndex(parent_item.row(), 0, parent_item)

    def rowCount(self, parent=QModelIndex()) -> int:
        parent_item = parent.internalPointer() if parent.isValid() else self._root
        return parent_item.child_count()

    def columnCount(self, parent=QModelIndex()) -> int:
        return 1

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        item: TestFileItem = index.internalPointer()

        if role == Qt.DisplayRole:
            status = ""
            if item.status:
                status = {"passed": " [PASS]", "failed": " [FAIL]", "error": " [ERR]"}.get(
                    item.status, ""
                )
            return item.name + status

        elif role == Qt.ForegroundRole:
            if item.status == "passed":
                return QColor(76, 175, 80)
            elif item.status == "failed":
                return QColor(244, 67, 54)
            elif item.status == "error":
                return QColor(255, 152, 0)
            return None

        elif role == Qt.UserRole:
            return item

        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def set_test_status(self, test_path: Path, status: str) -> None:
        """Update the status of a test file node."""
        self._update_status(self._root, test_path, status)

    def _update_status(self, item: TestFileItem, test_path: Path, status: str) -> bool:
        if item.path and item.path == test_path:
            item.status = status
            return True
        for child in item.children:
            if self._update_status(child, test_path, status):
                return True
        return False

    def get_file_path(self, index: QModelIndex) -> Path | None:
        if not index.isValid():
            return None
        item: TestFileItem = index.internalPointer()
        return item.path
