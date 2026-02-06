"""New Project wizard dialog."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)


class NewProjectDialog(QDialog):
    """Dialog for creating a new DesktopTester project."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Project")
        self.setMinimumWidth(500)

        self._project_path: Path | None = None

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("My Test Project")
        form.addRow("Project Name:", self._name_edit)

        # Directory picker
        dir_row = QHBoxLayout()
        self._dir_edit = QLineEdit()
        self._dir_edit.setPlaceholderText("Select project directory...")
        dir_row.addWidget(self._dir_edit)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_directory)
        dir_row.addWidget(browse_btn)
        form.addRow("Directory:", dir_row)

        # Target app
        self._target_edit = QLineEdit()
        self._target_edit.setPlaceholderText("Bundle ID or app name (e.g., com.apple.calculator)")
        form.addRow("Target App:", self._target_edit)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @property
    def project_name(self) -> str:
        return self._name_edit.text().strip()

    @property
    def project_directory(self) -> Path | None:
        text = self._dir_edit.text().strip()
        return Path(text) if text else None

    @property
    def target_app(self) -> str:
        return self._target_edit.text().strip()

    def _browse_directory(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Project Directory")
        if path:
            self._dir_edit.setText(path)

    def _on_accept(self) -> None:
        if self.project_name and self.project_directory:
            self.accept()
