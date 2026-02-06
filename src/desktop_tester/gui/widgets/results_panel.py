"""Results Panel - shows pass/fail per step with timing, grouped by test."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
    QFrame,
)

from desktop_tester.models.step import StepResult, TestResult, RunSummary

_STATUS_COLORS = {
    "passed": "#4caf50",
    "failed": "#f44336",
    "error": "#ff9800",
    "skipped": "#9e9e9e",
}


class ResultCard(QFrame):
    """A card showing the result of a single step."""

    def __init__(self, result: StepResult, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.StyledPanel)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 6, 8, 6)

        # Status indicator
        color = _STATUS_COLORS.get(result.status, "#9e9e9e")
        indicator = QLabel(result.status.upper())
        indicator.setStyleSheet(
            f"color: {color}; font-weight: bold; font-size: 11px; min-width: 50px;"
        )
        layout.addWidget(indicator)

        # Step ID
        step_label = QLabel(result.step_id)
        step_label.setStyleSheet("color: #aaa; font-size: 12px;")
        layout.addWidget(step_label)

        layout.addStretch()

        # Duration
        duration_label = QLabel(f"{result.duration_ms:.0f}ms")
        duration_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(duration_label)

        # Error message on hover
        if result.error_message:
            self.setToolTip(result.error_message)
        self.setStyleSheet(f"border-left: 3px solid {color}; background-color: #1a1a1a;")


class TestGroup(QWidget):
    """A collapsible group: clickable header + step result cards."""

    def __init__(self, test_name: str, parent=None):
        super().__init__(parent)
        self._collapsed = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # --- Clickable header ---
        self._header = QFrame()
        self._header.setFrameStyle(QFrame.StyledPanel)
        self._header.setCursor(Qt.PointingHandCursor)
        header_layout = QHBoxLayout(self._header)
        header_layout.setContentsMargins(8, 8, 8, 8)

        self._chevron = QLabel("\u25BC")  # ▼
        self._chevron.setStyleSheet("color: #888; font-size: 10px; min-width: 14px;")
        header_layout.addWidget(self._chevron)

        self._name_label = QLabel(test_name)
        self._name_label.setStyleSheet(
            "color: #ddd; font-weight: bold; font-size: 13px;"
        )
        header_layout.addWidget(self._name_label)

        header_layout.addStretch()

        self._status_label = QLabel("RUNNING...")
        self._status_label.setStyleSheet(
            "color: #2196f3; font-weight: bold; font-size: 11px;"
        )
        header_layout.addWidget(self._status_label)

        self._header.setStyleSheet(
            "background-color: #2a2a2a; border-left: 4px solid #2196f3; "
            "margin-top: 6px;"
        )
        # Make the header frame clickable via mouse release event
        self._header.mouseReleaseEvent = self._toggle_collapsed
        layout.addWidget(self._header)

        # --- Steps container ---
        self._steps_container = QWidget()
        self._steps_layout = QVBoxLayout(self._steps_container)
        self._steps_layout.setContentsMargins(0, 0, 0, 0)
        self._steps_layout.setSpacing(2)
        layout.addWidget(self._steps_container)

    def _toggle_collapsed(self, _event=None) -> None:
        self._collapsed = not self._collapsed
        self._steps_container.setVisible(not self._collapsed)
        self._chevron.setText("\u25B6" if self._collapsed else "\u25BC")  # ▶ / ▼

    def add_step_card(self, card: ResultCard) -> None:
        self._steps_layout.addWidget(card)

    def set_result(self, status: str, passed: int, total: int, duration_ms: float) -> None:
        """Update the header with the final test result."""
        color = _STATUS_COLORS.get(status, "#9e9e9e")
        self._status_label.setText(
            f"{status.upper()}  {passed}/{total} steps  ({duration_ms:.0f}ms)"
        )
        self._status_label.setStyleSheet(
            f"color: {color}; font-weight: bold; font-size: 11px;"
        )
        self._header.setStyleSheet(
            f"background-color: #2a2a2a; border-left: 4px solid {color}; "
            f"margin-top: 6px;"
        )


class ResultsPanel(QWidget):
    """Scrollable panel showing test run results grouped by test."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_group: TestGroup | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QLabel("  RESULTS")
        header.setStyleSheet(
            "background-color: #2a2a2a; padding: 8px; font-weight: bold; "
            "font-size: 11px; color: #888; border-bottom: 1px solid #444;"
        )
        layout.addWidget(header)

        # Summary bar
        self._summary_label = QLabel("No results yet")
        self._summary_label.setStyleSheet(
            "padding: 8px; color: #aaa; font-size: 12px; background-color: #222;"
        )
        layout.addWidget(self._summary_label)

        # Scrollable area for result cards
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._results_container = QWidget()
        self._results_layout = QVBoxLayout(self._results_container)
        self._results_layout.setContentsMargins(4, 4, 4, 4)
        self._results_layout.setSpacing(2)
        self._results_layout.addStretch()

        self._scroll.setWidget(self._results_container)
        layout.addWidget(self._scroll)

    def clear(self) -> None:
        """Clear all results."""
        self._current_group = None
        while self._results_layout.count() > 1:
            item = self._results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._summary_label.setText("No results yet")
        self._summary_label.setStyleSheet(
            "padding: 8px; color: #aaa; font-size: 12px; background-color: #222;"
        )

    def add_test_header(self, test_name: str) -> None:
        """Insert a collapsible test group. Subsequent step results appear under it."""
        group = TestGroup(test_name)
        self._results_layout.insertWidget(self._results_layout.count() - 1, group)
        self._current_group = group
        # Auto-scroll to bottom
        self._scroll.verticalScrollBar().setValue(
            self._scroll.verticalScrollBar().maximum()
        )

    def add_step_result(self, result: StepResult) -> None:
        """Add a result card for a completed step."""
        card = ResultCard(result)
        if self._current_group is not None:
            self._current_group.add_step_card(card)
        else:
            # Fallback: no test header yet, add directly
            self._results_layout.insertWidget(self._results_layout.count() - 1, card)
        # Auto-scroll to bottom
        self._scroll.verticalScrollBar().setValue(
            self._scroll.verticalScrollBar().maximum()
        )

    def set_test_result(self, result: TestResult) -> None:
        """Update the current test group header with the final result."""
        passed = sum(1 for r in result.step_results if r.status == "passed")
        total = len(result.step_results)

        if self._current_group is not None:
            self._current_group.set_result(
                result.status, passed, total, result.duration_ms
            )

        # Also update the summary label for single-test runs
        color = _STATUS_COLORS.get(result.status, "#9e9e9e")
        self._summary_label.setText(
            f"  {result.test_name}: {passed}/{total} passed "
            f"({result.duration_ms:.0f}ms)"
        )
        self._summary_label.setStyleSheet(
            f"padding: 8px; color: {color}; font-size: 12px; "
            f"font-weight: bold; background-color: #222;"
        )

    def set_run_summary(self, summary: RunSummary) -> None:
        """Update the summary with a full run summary."""
        color = "#4caf50" if summary.failed == 0 and summary.errors == 0 else "#f44336"
        self._summary_label.setText(
            f"  Tests: {summary.total} | Passed: {summary.passed} | "
            f"Failed: {summary.failed} | Errors: {summary.errors} "
            f"({summary.duration_ms:.0f}ms)"
        )
        self._summary_label.setStyleSheet(
            f"padding: 8px; color: {color}; font-size: 12px; "
            f"font-weight: bold; background-color: #222;"
        )
