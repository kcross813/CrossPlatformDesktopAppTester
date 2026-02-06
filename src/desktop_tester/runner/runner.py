"""TestRunner - orchestrates test execution with live progress signals."""

from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal

from desktop_tester.core.engine import AutomationEngine
from desktop_tester.models.project import ProjectConfig
from desktop_tester.models.serialization import load_test_file
from desktop_tester.models.step import RunSummary, Step, StepResult, TestResult
from desktop_tester.runner.context import RunContext
from desktop_tester.runner.hooks import RunHooks
from desktop_tester.runner.step_executor import StepExecutor


class TestRunner(QObject):
    """Executes test files and emits progress signals for the GUI."""

    test_started = Signal(str, str)  # test_name, test_path
    step_started = Signal(str)       # step_id
    step_completed = Signal(object)  # StepResult
    test_completed = Signal(object)  # TestResult
    run_completed = Signal(object)   # RunSummary

    def __init__(self, engine: AutomationEngine, project_dir: Path, config: ProjectConfig):
        super().__init__()
        self._engine = engine
        self._project_dir = project_dir
        self._config = config
        self._step_executor = StepExecutor(engine)
        self._hooks = RunHooks()
        self._abort_requested = False

    @property
    def hooks(self) -> RunHooks:
        return self._hooks

    def abort(self) -> None:
        """Request a graceful abort of the current run."""
        self._abort_requested = True

    def run_test(self, test_path: Path) -> TestResult:
        """Run a single test file."""
        self._abort_requested = False

        # Ensure the target app is connected before each test.
        # A previous test's teardown may have closed the app.
        self._ensure_app_connected()

        test_data = load_test_file(test_path)
        test_name = test_data["name"]

        self.test_started.emit(test_name, str(test_path))
        self._hooks.emit("before_test", test_name)

        context = RunContext(self._project_dir, self._config, test_path)
        step_results: list[StepResult] = []
        overall_status = "passed"
        start_time = time.time()
        started_at = datetime.now().isoformat()

        # Execute setup steps
        for step in test_data.get("setup", []):
            if self._abort_requested:
                overall_status = "error"
                break
            result = self._execute_step(step, context)
            if result.status in ("failed", "error"):
                overall_status = "error"
                step_results.append(result)
                break

        # Execute main steps
        if overall_status == "passed":
            for step in test_data.get("steps", []):
                if self._abort_requested:
                    overall_status = "error"
                    break

                self.step_started.emit(step.id)
                self._hooks.emit("before_step", step)

                result = self._execute_step(step, context)
                step_results.append(result)

                self.step_completed.emit(result)
                self._hooks.emit("after_step", step, result)

                if result.status in ("failed", "error") and not step.continue_on_failure:
                    overall_status = "failed"
                    break

        # Execute teardown steps (always run)
        for step in test_data.get("teardown", []):
            self._execute_step(step, context)

        duration = (time.time() - start_time) * 1000
        test_result = TestResult(
            test_name=test_name,
            test_file=str(test_path),
            status=overall_status,
            duration_ms=duration,
            step_results=step_results,
            started_at=started_at,
            finished_at=datetime.now().isoformat(),
        )

        self.test_completed.emit(test_result)
        self._hooks.emit("after_test", test_result)
        return test_result

    def run_all(self, test_paths: list[Path]) -> RunSummary:
        """Run multiple test files and return a summary."""
        summary = RunSummary(started_at=datetime.now().isoformat())

        for path in test_paths:
            if self._abort_requested:
                break
            result = self.run_test(path)
            summary.test_results.append(result)
            summary.total += 1
            if result.status == "passed":
                summary.passed += 1
            elif result.status == "failed":
                summary.failed += 1
            else:
                summary.errors += 1
            summary.duration_ms += result.duration_ms

        summary.finished_at = datetime.now().isoformat()
        self.run_completed.emit(summary)
        return summary

    def _ensure_app_connected(self) -> None:
        """Reconnect or relaunch the target app if disconnected."""
        if self._engine.app_ref is not None:
            return
        target = self._config.target_app
        identifier = target.bundle_id or target.name
        if not identifier:
            return
        try:
            self._engine.connect_or_launch(target)
        except Exception:
            pass  # Setup steps may handle the launch instead

    def _execute_step(self, step: Step, context: RunContext) -> StepResult:
        """Execute a step with screenshot capture."""
        result = self._step_executor.execute(step, context)

        # Capture screenshot if needed
        should_screenshot = (
            step.screenshot
            or context.screenshot_on_step
            or (result.status == "failed" and context.screenshot_on_failure)
        )
        if should_screenshot:
            try:
                png_bytes = self._engine.take_screenshot()
                if png_bytes:
                    path = context.save_screenshot(step.id, png_bytes)
                    result.screenshot_path = str(path)
            except Exception:
                pass  # Don't fail the step because of screenshot issues

        return result


class TestRunnerWorker(QThread):
    """Wraps TestRunner execution in a QThread for non-blocking GUI."""

    def __init__(self, runner: TestRunner, test_paths: list[Path]):
        super().__init__()
        self._runner = runner
        self._test_paths = test_paths
        self.summary: RunSummary | None = None

    def run(self) -> None:
        if len(self._test_paths) == 1:
            result = self._runner.run_test(self._test_paths[0])
            self.summary = RunSummary(
                total=1,
                passed=1 if result.status == "passed" else 0,
                failed=1 if result.status == "failed" else 0,
                errors=1 if result.status == "error" else 0,
                duration_ms=result.duration_ms,
                test_results=[result],
            )
        else:
            self.summary = self._runner.run_all(self._test_paths)
