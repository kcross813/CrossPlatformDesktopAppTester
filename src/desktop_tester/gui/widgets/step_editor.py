"""Step Editor - form-based editor for a selected test step."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QCheckBox,
)

from desktop_tester.models.step import ActionType, AssertionType, ComparisonOperator, Step


class StepEditor(QWidget):
    """Form-based editor for the currently selected step."""

    step_modified = Signal(object)  # Step
    pick_element_requested = Signal()  # Request to visually pick a UI element

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_step: Step | None = None
        self._updating = False  # Prevent recursive signals

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # Step info group
        info_group = QGroupBox("Step Details")
        info_layout = QFormLayout(info_group)

        self._id_label = QLabel("—")
        info_layout.addRow("ID:", self._id_label)

        self._action_combo = QComboBox()
        for action in ActionType:
            self._action_combo.addItem(action.value, action)
        self._action_combo.currentIndexChanged.connect(self._on_field_changed)
        info_layout.addRow("Action:", self._action_combo)

        self._description_edit = QLineEdit()
        self._description_edit.setPlaceholderText("Step description")
        self._description_edit.textChanged.connect(self._on_field_changed)
        info_layout.addRow("Description:", self._description_edit)

        layout.addWidget(info_group)

        # Target group
        target_group = QGroupBox("Target Element")
        target_layout = QFormLayout(target_group)

        self._target_type_combo = QComboBox()
        self._target_type_combo.addItems([
            "accessibility_id", "role_title", "role_label",
            "text_content", "path", "coordinate",
        ])
        self._target_type_combo.currentIndexChanged.connect(self._on_field_changed)
        target_layout.addRow("Locator:", self._target_type_combo)

        self._target_role_edit = QLineEdit()
        self._target_role_edit.setPlaceholderText("e.g., button")
        self._target_role_edit.textChanged.connect(self._on_field_changed)
        target_layout.addRow("Role:", self._target_role_edit)

        self._target_value_edit = QLineEdit()
        self._target_value_edit.setPlaceholderText("Selector value")
        self._target_value_edit.textChanged.connect(self._on_field_changed)
        target_layout.addRow("Value:", self._target_value_edit)

        self._pick_btn = QPushButton("Pick Element")
        self._pick_btn.setToolTip("Click an element in the target app to select it")
        self._pick_btn.clicked.connect(self._on_pick_clicked)
        target_layout.addRow("", self._pick_btn)

        layout.addWidget(target_group)

        # Parameters group
        params_group = QGroupBox("Parameters")
        params_layout = QFormLayout(params_group)

        self._text_edit = QLineEdit()
        self._text_edit.setPlaceholderText("Text to type")
        self._text_edit.textChanged.connect(self._on_field_changed)
        params_layout.addRow("Text:", self._text_edit)

        self._keys_edit = QLineEdit()
        self._keys_edit.setPlaceholderText("e.g., cmd,c")
        self._keys_edit.textChanged.connect(self._on_field_changed)
        params_layout.addRow("Keys:", self._keys_edit)

        self._timeout_spin = QDoubleSpinBox()
        self._timeout_spin.setRange(0, 120)
        self._timeout_spin.setSingleStep(0.5)
        self._timeout_spin.setSuffix("s")
        self._timeout_spin.valueChanged.connect(self._on_field_changed)
        params_layout.addRow("Timeout:", self._timeout_spin)

        self._continue_check = QCheckBox("Continue on failure")
        self._continue_check.stateChanged.connect(self._on_field_changed)
        params_layout.addRow("", self._continue_check)

        layout.addWidget(params_group)

        # Assertion group (visible only when action is "assert")
        self._assertion_group = QGroupBox("Assertion")
        assertion_layout = QFormLayout(self._assertion_group)

        self._assert_type_combo = QComboBox()
        for at in AssertionType:
            self._assert_type_combo.addItem(at.value, at)
        self._assert_type_combo.currentIndexChanged.connect(self._on_field_changed)
        assertion_layout.addRow("Assert Type:", self._assert_type_combo)

        self._operator_combo = QComboBox()
        for op in ComparisonOperator:
            self._operator_combo.addItem(op.value, op)
        self._operator_combo.currentIndexChanged.connect(self._on_field_changed)
        assertion_layout.addRow("Operator:", self._operator_combo)

        self._expected_edit = QLineEdit()
        self._expected_edit.setPlaceholderText("Expected value")
        self._expected_edit.textChanged.connect(self._on_field_changed)
        assertion_layout.addRow("Expected:", self._expected_edit)

        self._assertion_group.setVisible(False)
        layout.addWidget(self._assertion_group)

        layout.addStretch()

        # Show/hide sections based on action type
        self._action_combo.currentIndexChanged.connect(self._update_field_visibility)

    def load_step(self, step: Step | None) -> None:
        """Populate the editor with a step's data."""
        self._updating = True
        self._current_step = step

        if step is None:
            self._id_label.setText("—")
            self._action_combo.setCurrentIndex(0)
            self._description_edit.clear()
            self._target_type_combo.setCurrentIndex(0)
            self._target_role_edit.clear()
            self._target_value_edit.clear()
            self._text_edit.clear()
            self._keys_edit.clear()
            self._timeout_spin.setValue(5.0)
            self._continue_check.setChecked(False)
            self._assert_type_combo.setCurrentIndex(0)
            self._operator_combo.setCurrentIndex(0)
            self._expected_edit.clear()
            self._assertion_group.setVisible(False)
            self._updating = False
            return

        self._id_label.setText(step.id)

        # Action
        idx = self._action_combo.findData(step.action)
        if idx >= 0:
            self._action_combo.setCurrentIndex(idx)

        self._description_edit.setText(step.description)

        # Target
        if step.target:
            target_type = step.target.get("type", "role_title")
            idx = self._target_type_combo.findText(target_type)
            if idx >= 0:
                self._target_type_combo.setCurrentIndex(idx)
            self._target_role_edit.setText(step.target.get("role", ""))
            self._target_value_edit.setText(step.target.get("value", ""))
        else:
            self._target_type_combo.setCurrentIndex(0)
            self._target_role_edit.clear()
            self._target_value_edit.clear()

        self._text_edit.setText(step.text or "")
        self._keys_edit.setText(",".join(step.keys) if step.keys else "")
        self._timeout_spin.setValue(step.timeout or 5.0)
        self._continue_check.setChecked(step.continue_on_failure)

        # Assertion fields
        if step.assertion:
            assert_type_str = step.assertion.get("type", "")
            idx = self._assert_type_combo.findText(assert_type_str)
            if idx >= 0:
                self._assert_type_combo.setCurrentIndex(idx)
            operator_str = step.assertion.get("operator", "")
            idx = self._operator_combo.findText(operator_str)
            if idx >= 0:
                self._operator_combo.setCurrentIndex(idx)
            self._expected_edit.setText(str(step.assertion.get("expected", "")))
        else:
            self._assert_type_combo.setCurrentIndex(0)
            self._operator_combo.setCurrentIndex(0)
            self._expected_edit.clear()

        self._update_field_visibility()
        self._updating = False

    def _on_field_changed(self) -> None:
        """Called when any field is edited."""
        if self._updating or self._current_step is None:
            return

        step = self._current_step
        step.action = self._action_combo.currentData()
        step.description = self._description_edit.text()

        # Build target dict
        target_value = self._target_value_edit.text().strip()
        if target_value:
            step.target = {
                "type": self._target_type_combo.currentText(),
                "value": target_value,
            }
            role = self._target_role_edit.text().strip()
            if role:
                step.target["role"] = role
        else:
            step.target = None

        step.text = self._text_edit.text() or None
        keys_text = self._keys_edit.text().strip()
        step.keys = [k.strip() for k in keys_text.split(",")] if keys_text else None
        timeout_val = self._timeout_spin.value()
        step.timeout = timeout_val if timeout_val != 5.0 else None
        step.continue_on_failure = self._continue_check.isChecked()

        # Build assertion dict
        if step.action == ActionType.ASSERT:
            assert_type = self._assert_type_combo.currentData()
            operator = self._operator_combo.currentData()
            expected = self._expected_edit.text().strip()
            step.assertion = {
                "type": assert_type.value if assert_type else "",
                "operator": operator.value if operator else "",
            }
            if expected:
                step.assertion["expected"] = expected
        else:
            step.assertion = None

        self.step_modified.emit(step)

    def _on_pick_clicked(self) -> None:
        if self._current_step is None:
            return
        self._pick_btn.setEnabled(False)
        self._pick_btn.setText("Click an element...")
        self.pick_element_requested.emit()

    def set_picked_element(self, locator_dict: dict, element_value: str | None) -> None:
        """Populate target fields from a picked element.

        Called by MainWindow after the user clicks an element in the target app.
        *locator_dict* has keys: type, value, and optionally role.
        *element_value* is the element's current text/value for pre-filling assertions.
        """
        self._pick_btn.setEnabled(True)
        self._pick_btn.setText("Pick Element")

        if self._current_step is None:
            return

        self._updating = True

        # Populate target fields
        target_type = locator_dict.get("type", "role_title")
        idx = self._target_type_combo.findText(target_type)
        if idx >= 0:
            self._target_type_combo.setCurrentIndex(idx)
        self._target_role_edit.setText(locator_dict.get("role", ""))
        self._target_value_edit.setText(locator_dict.get("value", ""))

        # For assertion steps, pre-fill the expected value with current element value
        if self._current_step.action == ActionType.ASSERT and element_value:
            self._expected_edit.setText(element_value)

        self._updating = False
        self._on_field_changed()

    def cancel_pick(self) -> None:
        """Reset the pick button if picking was cancelled."""
        self._pick_btn.setEnabled(True)
        self._pick_btn.setText("Pick Element")

    def _update_field_visibility(self) -> None:
        """Show/hide field groups based on the selected action type."""
        action = self._action_combo.currentData()
        is_assert = action == ActionType.ASSERT
        self._assertion_group.setVisible(is_assert)
