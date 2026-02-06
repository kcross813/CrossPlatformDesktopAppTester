"""New Test dialog."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
)


class NewTestDialog(QDialog):
    """Dialog for creating a new test file."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Test")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Test name (e.g., Basic Addition)")
        form.addRow("Test Name:", self._name_edit)

        self._filename_edit = QLineEdit()
        self._filename_edit.setPlaceholderText("test_basic_addition")
        form.addRow("Filename:", self._filename_edit)

        self._desc_edit = QLineEdit()
        self._desc_edit.setPlaceholderText("Optional description")
        form.addRow("Description:", self._desc_edit)

        # Auto-fill filename from name
        self._name_edit.textChanged.connect(self._auto_filename)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @property
    def test_name(self) -> str:
        return self._name_edit.text().strip()

    @property
    def filename(self) -> str:
        text = self._filename_edit.text().strip()
        if not text.endswith(".yaml"):
            text += ".yaml"
        return text

    @property
    def description(self) -> str:
        return self._desc_edit.text().strip()

    def _auto_filename(self, name: str) -> None:
        """Auto-generate filename from the test name."""
        slug = name.lower().replace(" ", "_").replace("-", "_")
        slug = "".join(c for c in slug if c.isalnum() or c == "_")
        if slug and not slug.startswith("test_"):
            slug = "test_" + slug
        self._filename_edit.setText(slug)

    def _on_accept(self) -> None:
        if self.test_name:
            self.accept()
