"""Before/after hooks and event emitter for extensibility."""

from __future__ import annotations

from typing import Callable

from desktop_tester.models.step import Step, StepResult, TestResult


class RunHooks:
    """Simple event system for test run lifecycle hooks."""

    def __init__(self):
        self._hooks: dict[str, list[Callable]] = {
            "before_test": [],
            "after_test": [],
            "before_step": [],
            "after_step": [],
        }

    def on(self, event: str, callback: Callable) -> None:
        """Register a callback for an event."""
        if event in self._hooks:
            self._hooks[event].append(callback)

    def emit(self, event: str, *args, **kwargs) -> None:
        """Trigger all callbacks for an event."""
        for callback in self._hooks.get(event, []):
            try:
                callback(*args, **kwargs)
            except Exception:
                pass  # Hooks should not break test execution
