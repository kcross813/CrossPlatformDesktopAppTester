"""Executes individual test steps against the automation engine."""

from __future__ import annotations

import time

from desktop_tester.core.engine import AutomationEngine
from desktop_tester.core.locator import LocatorStrategy
from desktop_tester.models.step import ActionType, Step, StepResult
from desktop_tester.runner.assertion_executor import AssertionExecutor
from desktop_tester.runner.context import RunContext


class StepExecutor:
    """Dispatches and executes individual test steps."""

    def __init__(self, engine: AutomationEngine):
        self._engine = engine
        self._assertion_executor = AssertionExecutor(engine)

    def execute(self, step: Step, context: RunContext) -> StepResult:
        """Execute a single step and return the result."""
        start = time.time()

        try:
            if step.action == ActionType.CLICK:
                self._do_click(step, context)
            elif step.action == ActionType.DOUBLE_CLICK:
                self._do_double_click(step, context)
            elif step.action == ActionType.RIGHT_CLICK:
                self._do_right_click(step, context)
            elif step.action == ActionType.TYPE_TEXT:
                self._do_type_text(step, context)
            elif step.action == ActionType.KEY_COMBO:
                self._do_key_combo(step)
            elif step.action == ActionType.CLEAR_FIELD:
                self._do_clear_field(step, context)
            elif step.action == ActionType.ASSERT:
                return self._assertion_executor.evaluate(step)
            elif step.action == ActionType.LAUNCH_APP:
                self._do_launch_app(context)
            elif step.action == ActionType.CLOSE_APP:
                self._do_close_app()
            elif step.action == ActionType.WAIT:
                time.sleep(step.duration or 1.0)
            elif step.action == ActionType.WAIT_FOR_ELEMENT:
                self._do_wait_for_element(step, context)
            elif step.action == ActionType.WAIT_FOR_ELEMENT_GONE:
                self._do_wait_for_element_gone(step, context)
            elif step.action == ActionType.WAIT_FOR_WINDOW:
                self._do_wait_for_window(step, context)
            elif step.action == ActionType.RUN_SCRIPT:
                self._do_run_script(step)
            else:
                return StepResult(
                    step_id=step.id,
                    status="error",
                    duration_ms=(time.time() - start) * 1000,
                    description=step.description,
                    error_message=f"Unknown action: {step.action}",
                )

            duration = (time.time() - start) * 1000

            # Apply slow mode delay
            if context.slow_mode_delay > 0:
                time.sleep(context.slow_mode_delay)

            return StepResult(
                step_id=step.id, status="passed",
                duration_ms=duration, description=step.description,
            )

        except Exception as e:
            duration = (time.time() - start) * 1000
            return StepResult(
                step_id=step.id,
                status="failed",
                duration_ms=duration,
                description=step.description,
                error_message=str(e),
            )

    def _resolve_target(self, step: Step, context: RunContext) -> object:
        """Resolve the target element from a step's locator."""
        if not step.target:
            raise ValueError(f"Step {step.id} has no target defined")
        locator = LocatorStrategy.from_dict(step.target)
        if step.timeout:
            locator.timeout = step.timeout
        elif locator.timeout == 5.0:
            locator.timeout = context.default_timeout
        return self._engine.find_element(locator)

    def _do_click(self, step: Step, context: RunContext) -> None:
        # Dock item clicks can't be resolved inside the target app's tree;
        # treat them as app activation instead.
        if step.target and step.target.get("role") == "dockitem":
            self._engine.launch_app(context.config.target_app)
            return

        element = self._resolve_target(step, context)
        self._engine.click(element)

    def _do_double_click(self, step: Step, context: RunContext) -> None:
        element = self._resolve_target(step, context)
        self._engine.double_click(element)

    def _do_right_click(self, step: Step, context: RunContext) -> None:
        element = self._resolve_target(step, context)
        self._engine.right_click(element)

    def _do_type_text(self, step: Step, context: RunContext) -> None:
        if not step.text:
            raise ValueError(f"Step {step.id} type_text has no text defined")
        if step.target:
            element = self._resolve_target(step, context)
            self._engine.type_text(element, step.text)
        else:
            # No target: type into whatever currently has focus
            self._engine.type_keys(step.text)

    def _do_key_combo(self, step: Step) -> None:
        if not step.keys:
            raise ValueError(f"Step {step.id} key_combo has no keys defined")
        self._engine.key_combo(step.keys)

    def _do_clear_field(self, step: Step, context: RunContext) -> None:
        element = self._resolve_target(step, context)
        # Select all and delete
        self._engine.click(element)
        self._engine.key_combo(["cmd", "a"])
        time.sleep(0.05)
        self._engine.key_combo(["backspace"])

    def _do_launch_app(self, context: RunContext) -> None:
        self._engine.launch_app(context.config.target_app)

    def _do_close_app(self) -> None:
        self._engine.terminate_app()

    def _do_wait_for_element(self, step: Step, context: RunContext) -> None:
        if not step.target:
            raise ValueError(f"Step {step.id} wait_for_element has no target")
        locator = LocatorStrategy.from_dict(step.target)
        timeout = step.timeout or context.default_timeout
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                self._engine.find_element(locator)
                return
            except Exception:
                time.sleep(0.25)
        raise TimeoutError(f"Element not found within {timeout}s")

    def _do_wait_for_element_gone(self, step: Step, context: RunContext) -> None:
        if not step.target:
            raise ValueError(f"Step {step.id} wait_for_element_gone has no target")
        locator = LocatorStrategy.from_dict(step.target)
        locator.timeout = 0.5  # Quick check
        timeout = step.timeout or context.default_timeout
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                self._engine.find_element(locator)
                time.sleep(0.25)
            except Exception:
                return  # Element is gone
        raise TimeoutError(f"Element still present after {timeout}s")

    def _do_wait_for_window(self, step: Step, context: RunContext) -> None:
        title = step.title
        if not title:
            raise ValueError(f"Step {step.id} wait_for_window has no title")
        timeout = step.timeout or context.default_timeout
        deadline = time.time() + timeout
        while time.time() < deadline:
            apps = self._engine.list_running_apps()
            for app in apps:
                if title.lower() in app.get("name", "").lower():
                    # Try to attach
                    try:
                        identifier = app.get("bundle_id") or app.get("name") or str(app.get("pid"))
                        self._engine.attach_to_app(identifier)
                        return
                    except Exception:
                        pass
            time.sleep(0.5)
        raise TimeoutError(f"Window '{title}' not found within {timeout}s")

    def _do_run_script(self, step: Step) -> None:
        if not step.script:
            raise ValueError(f"Step {step.id} run_script has no script defined")
        # Execute in a restricted namespace
        namespace = {
            "engine": self._engine,
            "step": step,
        }
        exec(step.script, namespace)
