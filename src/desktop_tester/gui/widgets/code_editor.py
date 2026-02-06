"""YAML code view for raw test step editing."""

from __future__ import annotations

import yaml
from PySide6.QtCore import Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QPlainTextEdit, QVBoxLayout, QWidget

from desktop_tester.models.serialization import step_to_dict
from desktop_tester.models.step import Step


class CodeEditor(QWidget):
    """Raw YAML editor for test steps."""

    code_modified = Signal(str)  # YAML string

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._editor = QPlainTextEdit()
        self._editor.setFont(QFont("Menlo", 12))
        self._editor.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1a1a1a;
                color: #d4d4d4;
                border: none;
                padding: 8px;
                selection-background-color: #264f78;
            }
        """)
        self._editor.setTabStopDistance(
            self._editor.fontMetrics().horizontalAdvance(" ") * 2
        )
        self._editor.textChanged.connect(self._on_text_changed)

        layout.addWidget(self._editor)
        self._updating = False

    def load_step(self, step: Step | None) -> None:
        """Display the YAML for a step."""
        self._updating = True
        if step is None:
            self._editor.setPlainText("")
        else:
            step_dict = step_to_dict(step)
            yaml_str = yaml.dump(step_dict, default_flow_style=False, sort_keys=False)
            self._editor.setPlainText(yaml_str)
        self._updating = False

    def load_yaml(self, yaml_str: str) -> None:
        """Load raw YAML text."""
        self._updating = True
        self._editor.setPlainText(yaml_str)
        self._updating = False

    def get_yaml(self) -> str:
        """Get the current YAML text."""
        return self._editor.toPlainText()

    def _on_text_changed(self) -> None:
        if not self._updating:
            self.code_modified.emit(self._editor.toPlainText())
