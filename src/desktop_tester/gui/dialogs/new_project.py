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

    def __init__(self, apps: list[dict] | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Project")
        self.setMinimumWidth(500)

        self._project_path: Path | None = None
        self._apps = apps or []
        self._selected_app: dict | None = None

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

        # Target app with select button
        app_row = QHBoxLayout()
        self._target_edit = QLineEdit()
        self._target_edit.setPlaceholderText("Bundle ID or app name (e.g., com.apple.calculator)")
        app_row.addWidget(self._target_edit)
        select_btn = QPushButton("Select...")
        select_btn.clicked.connect(self._select_app)
        select_btn.setEnabled(bool(self._apps))
        app_row.addWidget(select_btn)
        form.addRow("Target App:", app_row)

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

    @property
    def selected_app(self) -> dict | None:
        return self._selected_app

    def _browse_directory(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Project Directory")
        if path:
            self._dir_edit.setText(path)

    def _select_app(self) -> None:
        from desktop_tester.gui.widgets.app_selector import AppSelectorDialog

        dialog = AppSelectorDialog(self._apps, self)
        if dialog.exec() == AppSelectorDialog.Accepted and dialog.selected_app:
            self._selected_app = dialog.selected_app
            bundle_id = self._selected_app.get("bundle_id", "")
            name = self._selected_app.get("name", "")
            self._target_edit.setText(bundle_id or name)

    def _on_accept(self) -> None:
        if self.project_name and self.project_directory:
            self.accept()
