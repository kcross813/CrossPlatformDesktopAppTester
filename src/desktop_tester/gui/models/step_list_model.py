"""Qt Model for the step list view."""

from __future__ import annotations

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt
from PySide6.QtGui import QColor

from desktop_tester.models.step import Step, StepResult


class StepListModel(QAbstractListModel):
    """Model backing the step list / command log view."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._steps: list[Step] = []
        self._results: dict[str, StepResult] = {}
        self._current_step_id: str = ""

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._steps)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self._steps):
            return None

        step = self._steps[index.row()]

        if role == Qt.DisplayRole:
            prefix = f"{index.row() + 1}. "
            result = self._results.get(step.id)
            if result:
                status_icon = {"passed": "[PASS]", "failed": "[FAIL]", "error": "[ERR]",
                               "skipped": "[SKIP]"}.get(result.status, "")
                return f"{prefix}{step.description or step.action.value}  {status_icon}"
            elif step.id == self._current_step_id:
                return f"{prefix}{step.description or step.action.value}  [RUNNING]"
            return f"{prefix}{step.description or step.action.value}"

        elif role == Qt.ForegroundRole:
            result = self._results.get(step.id)
            if result:
                if result.status == "passed":
                    return QColor(76, 175, 80)  # Green
                elif result.status == "failed":
                    return QColor(244, 67, 54)  # Red
                elif result.status == "error":
                    return QColor(255, 152, 0)  # Orange
            if step.id == self._current_step_id:
                return QColor(42, 130, 218)  # Blue
            return None

        elif role == Qt.BackgroundRole:
            if step.id == self._current_step_id:
                return QColor(42, 42, 60)
            return None

        elif role == Qt.UserRole:
            return step

        return None

    def set_steps(self, steps: list[Step]) -> None:
        """Replace all steps."""
        self.beginResetModel()
        self._steps = list(steps)
        self._results.clear()
        self._current_step_id = ""
        self.endResetModel()

    def add_step(self, step: Step) -> None:
        """Append a new step (e.g., during recording)."""
        row = len(self._steps)
        self.beginInsertRows(QModelIndex(), row, row)
        self._steps.append(step)
        self.endInsertRows()

    def remove_step(self, row: int) -> None:
        """Remove a step by row index."""
        if 0 <= row < len(self._steps):
            self.beginRemoveRows(QModelIndex(), row, row)
            removed = self._steps.pop(row)
            self._results.pop(removed.id, None)
            self.endRemoveRows()

    def get_step(self, row: int) -> Step | None:
        if 0 <= row < len(self._steps):
            return self._steps[row]
        return None

    def get_steps(self) -> list[Step]:
        return list(self._steps)

    def set_current_step(self, step_id: str) -> None:
        """Mark a step as currently running."""
        self._current_step_id = step_id
        self.dataChanged.emit(
            self.index(0), self.index(len(self._steps) - 1),
            [Qt.DisplayRole, Qt.ForegroundRole, Qt.BackgroundRole],
        )

    def set_step_result(self, result: StepResult) -> None:
        """Set the result for a completed step."""
        self._results[result.step_id] = result
        # Find the row and emit change
        for i, step in enumerate(self._steps):
            if step.id == result.step_id:
                idx = self.index(i)
                self.dataChanged.emit(idx, idx, [Qt.DisplayRole, Qt.ForegroundRole])
                break

    def clear_results(self) -> None:
        """Clear all results (before a new run)."""
        self._results.clear()
        self._current_step_id = ""
        self.dataChanged.emit(
            self.index(0), self.index(len(self._steps) - 1),
            [Qt.DisplayRole, Qt.ForegroundRole, Qt.BackgroundRole],
        )
