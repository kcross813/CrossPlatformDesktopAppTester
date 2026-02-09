"""Main application window - 3-panel Cypress-like layout."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from desktop_tester.constants import APP_NAME
from desktop_tester.gui.dialogs.new_project import NewProjectDialog
from desktop_tester.gui.dialogs.new_test import NewTestDialog
from desktop_tester.gui.widgets.app_selector import AppSelectorDialog
from desktop_tester.gui.widgets.code_editor import CodeEditor
from desktop_tester.gui.widgets.results_panel import ResultsPanel
from desktop_tester.gui.widgets.screenshot_viewer import ScreenshotViewer
from desktop_tester.gui.widgets.step_editor import StepEditor
from desktop_tester.gui.widgets.step_list import StepList
from desktop_tester.gui.widgets.test_explorer import TestExplorer
from desktop_tester.gui.widgets.toolbar import MainToolbar
from desktop_tester.models.project import ProjectConfig, TargetApp
from desktop_tester.models.serialization import (
    load_project,
    load_test_file,
    save_project,
    save_test_file,
)
from desktop_tester.models.step import ActionType, Step, StepResult, TestResult


class MainWindow(QMainWindow):
    """Main application window with 3-panel layout."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(1200, 800)

        # State
        self._project_dir: Path | None = None
        self._project_config: ProjectConfig | None = None
        self._current_test_path: Path | None = None
        self._engine = None
        self._recorder = None
        self._runner = None
        self._runner_worker = None
        self._pick_monitor = None  # One-shot NSEvent monitor for element picking

        # --- Build UI ---
        self._setup_toolbar()
        self._setup_central_widget()
        self._setup_menu_bar()
        self._setup_status_bar()

        # Connect signals
        self._connect_signals()

        # Restore last project
        self._restore_last_project()

    def _restore_last_project(self) -> None:
        settings = QSettings("DesktopTester", "DesktopTester")
        last_project = settings.value("last_project_dir")
        if last_project:
            project_dir = Path(last_project)
            if (project_dir / "project.yaml").exists():
                self._load_project(project_dir)

    def _setup_toolbar(self) -> None:
        self._toolbar = MainToolbar(self)
        self.addToolBar(self._toolbar)

    def _setup_central_widget(self) -> None:
        main_splitter = QSplitter(Qt.Horizontal)

        # Left: Test Explorer
        self._test_explorer = TestExplorer()
        main_splitter.addWidget(self._test_explorer)

        # Center: Step List
        self._step_list = StepList()
        main_splitter.addWidget(self._step_list)

        # Right: Detail Panel (tabbed)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self._detail_tabs = QTabWidget()

        # Tab 1: Step Editor
        self._step_editor = StepEditor()
        self._detail_tabs.addTab(self._step_editor, "Step Details")

        # Tab 2: Screenshot Viewer
        self._screenshot_viewer = ScreenshotViewer()
        self._detail_tabs.addTab(self._screenshot_viewer, "Screenshot")

        # Tab 3: Code Editor
        self._code_editor = CodeEditor()
        self._detail_tabs.addTab(self._code_editor, "Code")

        # Tab 4: Results
        self._results_panel = ResultsPanel()
        self._detail_tabs.addTab(self._results_panel, "Results")

        right_layout.addWidget(self._detail_tabs)
        main_splitter.addWidget(right_panel)

        # Splitter proportions: 15% | 45% | 40%
        main_splitter.setSizes([200, 550, 450])
        self.setCentralWidget(main_splitter)

    def _setup_menu_bar(self) -> None:
        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("File")
        file_menu.addAction("New Project...", self._new_project)
        file_menu.addAction("Open Project...", self._open_project)
        file_menu.addSeparator()
        file_menu.addAction("New Test...", self._new_test)
        file_menu.addSeparator()
        file_menu.addAction("Save", self._save_current_test, "Ctrl+S")
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close)

        # Test menu
        test_menu = menu_bar.addMenu("Test")
        test_menu.addAction("Run Current Test", self._run_test, "Ctrl+Return")
        test_menu.addAction("Run All Tests", self._run_all_tests)
        test_menu.addSeparator()
        test_menu.addAction("Record New Test", self._start_recording, "Ctrl+R")
        test_menu.addAction("Stop Recording", self._stop_recording)

        # Tools menu
        tools_menu = menu_bar.addMenu("Tools")
        tools_menu.addAction("Select Target App...", self._select_target_app)

    def _setup_status_bar(self) -> None:
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Ready - Open or create a project to begin")

    def _connect_signals(self) -> None:
        # Toolbar
        self._toolbar.record_clicked.connect(self._start_recording)
        self._toolbar.stop_clicked.connect(self._stop_action)
        self._toolbar.run_clicked.connect(self._run_test)
        self._toolbar.run_all_clicked.connect(self._run_all_tests)
        self._toolbar.save_clicked.connect(self._save_current_test)

        # Test explorer
        self._test_explorer.test_selected.connect(self._load_test_file)
        self._test_explorer.test_deleted.connect(self._on_test_deleted)

        # Step list
        self._step_list.step_selected.connect(self._on_step_selected)
        self._step_list.add_step_requested.connect(self._add_step)
        self._step_list.delete_step_requested.connect(self._delete_step)

        # Step editor
        self._step_editor.pick_element_requested.connect(self._start_element_pick)

    # --- Engine / Recorder / Runner initialization ---

    def _ensure_engine(self) -> bool:
        """Initialize the automation engine if not already done."""
        if self._engine is not None:
            return True

        try:
            from desktop_tester.core import get_platform_backend
            from desktop_tester.core.engine import AutomationEngine
            backend = get_platform_backend()
            self._engine = AutomationEngine(backend)
            return True
        except Exception as e:
            QMessageBox.critical(
                self, "Engine Error",
                f"Failed to initialize automation engine:\n\n{e}\n\n"
                "On macOS, make sure accessibility permissions are enabled in "
                "System Settings > Privacy & Security > Accessibility."
            )
            return False

    def _ensure_recorder(self) -> bool:
        if not self._ensure_engine():
            return False
        if self._recorder is None:
            from desktop_tester.recorder.recorder import RecordingSession
            self._recorder = RecordingSession(self._engine)
            self._recorder.step_recorded.connect(self._on_step_recorded)
        return True

    def _ensure_runner(self) -> bool:
        if not self._ensure_engine():
            return False
        if self._project_dir is None or self._project_config is None:
            QMessageBox.warning(self, "No Project", "Please open a project first.")
            return False
        if self._runner is None:
            from desktop_tester.runner.runner import TestRunner
            self._runner = TestRunner(self._engine, self._project_dir, self._project_config)
            self._runner.test_started.connect(self._on_test_started)
            self._runner.step_started.connect(self._on_run_step_started)
            self._runner.step_completed.connect(self._on_run_step_completed)
            self._runner.test_completed.connect(self._on_test_completed)
        return True

    # --- Project operations ---

    def _new_project(self) -> None:
        apps = self._get_installed_apps()
        dialog = NewProjectDialog(apps=apps, parent=self)
        if dialog.exec() != NewProjectDialog.Accepted:
            return

        project_dir = dialog.project_directory / dialog.project_name.replace(" ", "_").lower()
        project_dir.mkdir(parents=True, exist_ok=True)

        # Build TargetApp from selection or manual text entry
        if dialog.selected_app:
            target_app = TargetApp(
                bundle_id=dialog.selected_app.get("bundle_id", ""),
                name=dialog.selected_app.get("name", ""),
            )
        elif dialog.target_app:
            target_app = TargetApp(bundle_id=dialog.target_app)
        else:
            target_app = TargetApp()

        config = ProjectConfig(
            name=dialog.project_name,
            target_app=target_app,
        )

        # Create directory structure
        (project_dir / config.tests_dir).mkdir(exist_ok=True)
        (project_dir / config.fixtures_dir).mkdir(exist_ok=True)
        (project_dir / config.screenshots_dir).mkdir(exist_ok=True)
        (project_dir / config.reports_dir).mkdir(exist_ok=True)

        save_project(project_dir / "project.yaml", config)

        self._load_project(project_dir)
        self._status_bar.showMessage(f"Created project: {config.name}")

    def _open_project(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Open Project Directory")
        if path:
            self._load_project(Path(path))

    def _load_project(self, project_dir: Path) -> None:
        config_path = project_dir / "project.yaml"
        if not config_path.exists():
            QMessageBox.warning(
                self, "Invalid Project",
                f"No project.yaml found in:\n{project_dir}"
            )
            return

        self._project_dir = project_dir
        self._project_config = load_project(config_path)
        self._runner = None  # Reset runner with new config

        # Remember this project for next launch
        settings = QSettings("DesktopTester", "DesktopTester")
        settings.setValue("last_project_dir", str(project_dir))

        self._test_explorer.load_project(project_dir, self._project_config.tests_dir)
        self.setWindowTitle(f"{APP_NAME} - {self._project_config.name}")

        # Auto-connect to saved target app
        target = self._project_config.target_app
        target_name = target.name or target.bundle_id
        if target_name and self._try_connect_saved_app(launch=False):
            self._status_bar.showMessage(
                f"Opened project: {self._project_config.name} "
                f"(connected to {target.name or target.bundle_id})"
            )
        elif target_name:
            self._status_bar.showMessage(
                f"Opened project: {self._project_config.name} "
                f"(target app '{target_name}' not running)"
            )
        else:
            self._status_bar.showMessage(f"Opened project: {self._project_config.name}")

    # --- Test file operations ---

    def _load_test_file(self, path: Path) -> None:
        """Load a test YAML file into the step list."""
        try:
            test_data = load_test_file(path)
            self._current_test_path = path
            steps = test_data.get("steps", [])
            self._step_list.model.set_steps(steps)
            self._step_list.set_status(
                f"{test_data['name']} - {len(steps)} steps"
            )
            self._results_panel.clear()
            self._step_editor.load_step(None)
            self._code_editor.load_step(None)
            self._screenshot_viewer.clear()
            self._status_bar.showMessage(f"Loaded: {path.name}")
        except Exception as e:
            QMessageBox.warning(self, "Load Error", f"Failed to load test:\n{e}")

    def _new_test(self) -> None:
        if not self._project_dir or not self._project_config:
            QMessageBox.warning(self, "No Project", "Please open a project first.")
            return

        dialog = NewTestDialog(self)
        if dialog.exec() != NewTestDialog.Accepted:
            return

        tests_dir = self._project_dir / self._project_config.tests_dir
        test_path = tests_dir / dialog.filename

        save_test_file(
            test_path,
            name=dialog.test_name,
            steps=[],
            description=dialog.description,
        )

        self._test_explorer.load_project(self._project_dir, self._project_config.tests_dir)
        self._load_test_file(test_path)
        self._status_bar.showMessage(f"Created test: {dialog.test_name}")

    def _save_current_test(self) -> None:
        if not self._current_test_path:
            self._status_bar.showMessage("No test to save")
            return

        steps = self._step_list.model.get_steps()
        save_test_file(
            self._current_test_path,
            name=self._current_test_path.stem.replace("_", " ").title(),
            steps=steps,
        )
        self._status_bar.showMessage(f"Saved: {self._current_test_path.name}")

    def _on_test_deleted(self, path: Path) -> None:
        """Handle a test file being deleted from the explorer."""
        # Refresh the tree
        if self._project_dir and self._project_config:
            self._test_explorer.load_project(
                self._project_dir, self._project_config.tests_dir
            )

        # Clear the editor if the deleted test was the one loaded
        if self._current_test_path and self._current_test_path == path:
            self._current_test_path = None
            self._step_list.model.set_steps([])
            self._step_list.set_status("No test loaded")
            self._step_editor.load_step(None)
            self._code_editor.load_step(None)
            self._results_panel.clear()
            self._screenshot_viewer.clear()

        self._status_bar.showMessage(f"Deleted: {path.name}")

    # --- Step selection ---

    def _on_step_selected(self, row: int) -> None:
        step = self._step_list.model.get_step(row)
        self._step_editor.load_step(step)
        self._code_editor.load_step(step)
        self._screenshot_viewer.clear()

    def _add_step(self) -> None:
        """Add a new blank step to the step list."""
        existing = self._step_list.model.get_steps()
        step_num = len(existing) + 1
        step = Step(
            id=f"step_{step_num}",
            action=ActionType.CLICK,
            description=f"New step {step_num}",
        )
        self._step_list.model.add_step(step)
        self._step_list.set_status(f"{len(existing) + 1} steps")
        # Select the new step and open the editor
        self._on_step_selected(len(existing))
        self._detail_tabs.setCurrentWidget(self._step_editor)

    def _delete_step(self, row: int) -> None:
        """Delete the step at the given row."""
        self._step_list.model.remove_step(row)
        remaining = self._step_list.model.get_steps()
        self._step_list.set_status(f"{len(remaining)} steps")
        self._step_editor.load_step(None)
        self._code_editor.load_step(None)

    # --- Element picking ---

    def _start_element_pick(self) -> None:
        """Enter element-pick mode: the next click in the target app selects an element."""
        import sys
        if sys.platform != "darwin":
            self._step_editor.cancel_pick()
            return

        if not self._ensure_engine():
            self._step_editor.cancel_pick()
            return

        import Cocoa

        self._status_bar.showMessage("Pick mode: click an element in the target app...")

        mask = Cocoa.NSEventMaskLeftMouseDown
        self._pick_monitor = (
            Cocoa.NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
                mask, self._on_element_picked
            )
        )

    def _on_element_picked(self, ns_event) -> None:
        """Handle the pick-mode click: resolve the element and populate the editor."""
        import Cocoa

        # Remove the monitor immediately (one-shot)
        if self._pick_monitor is not None:
            Cocoa.NSEvent.removeMonitor_(self._pick_monitor)
            self._pick_monitor = None

        try:
            # Convert Cocoa coordinates (bottom-left origin) to screen (top-left)
            loc = Cocoa.NSEvent.mouseLocation()
            screen = Cocoa.NSScreen.mainScreen()
            if screen is None:
                self._step_editor.cancel_pick()
                self._status_bar.showMessage("Pick cancelled")
                return
            screen_height = screen.frame().size.height
            x = int(loc.x)
            y = int(screen_height - loc.y)

            # Resolve the element at the click position
            from desktop_tester.recorder.element_resolver import ElementResolver

            resolver = ElementResolver(self._engine)
            element, locator = resolver.resolve(x, y)

            if element is None or locator is None:
                self._step_editor.cancel_pick()
                self._status_bar.showMessage("No element found at that position")
                return

            locator_dict = locator.to_dict()
            # Use get_element_text to walk children for container elements
            element_value = self._engine.get_element_text(element)

            self._step_editor.set_picked_element(locator_dict, element_value)

            desc = element.title or element.label or element.identifier or element.role
            self._status_bar.showMessage(f"Picked: {desc} ({element.role}) = \"{element_value}\"")

        except Exception as e:
            self._step_editor.cancel_pick()
            self._status_bar.showMessage(f"Pick failed: {e}")

    # --- Recording ---

    def _start_recording(self) -> None:
        if not self._ensure_recorder():
            return

        # If no app is connected, try saved config then prompt
        if not self._engine.app_ref:
            if not self._ensure_connected():
                return

        self._step_list.model.set_steps([])
        self._results_panel.clear()
        self._recorder.start()
        self._toolbar.set_recording_state(True)
        self._step_list.set_status("Recording... interact with the target app")
        self._status_bar.showMessage("Recording - click Stop when done")

    def _stop_action(self) -> None:
        """Stop recording or running test."""
        if self._recorder and self._recorder.is_recording:
            self._stop_recording()
        elif self._runner_worker and self._runner_worker.isRunning():
            self._runner.abort()

    def _stop_recording(self) -> None:
        if not self._recorder or not self._recorder.is_recording:
            return

        steps = self._recorder.stop()
        self._step_list.model.set_steps(steps)
        self._toolbar.set_recording_state(False)
        self._step_list.set_status(f"Recorded {len(steps)} steps")
        self._status_bar.showMessage(
            f"Recording complete: {len(steps)} steps. Save with Ctrl+S."
        )

    def _on_step_recorded(self, step: Step) -> None:
        """Called when a new step is captured during recording."""
        self._step_list.model.add_step(step)

    # --- Test execution ---

    def _run_test(self) -> None:
        if not self._current_test_path:
            self._status_bar.showMessage("No test loaded to run")
            return
        if not self._ensure_runner():
            return

        # Connect to target app if needed
        if not self._engine.app_ref:
            if not self._ensure_connected():
                return

        self._step_list.model.clear_results()
        self._results_panel.clear()
        self._toolbar.set_running_state(True)
        self._detail_tabs.setCurrentWidget(self._results_panel)
        self._status_bar.showMessage("Running test...")

        from desktop_tester.runner.runner import TestRunnerWorker
        self._runner_worker = TestRunnerWorker(
            self._runner, [self._current_test_path]
        )
        self._runner_worker.finished.connect(self._on_run_finished)
        self._runner_worker.start()

    def _run_all_tests(self) -> None:
        if not self._project_dir or not self._project_config:
            QMessageBox.warning(self, "No Project", "Please open a project first.")
            return
        if not self._ensure_runner():
            return

        if not self._engine.app_ref:
            if not self._ensure_connected():
                return

        tests_dir = self._project_dir / self._project_config.tests_dir
        test_paths = sorted(tests_dir.glob("*.yaml"))

        if not test_paths:
            self._status_bar.showMessage("No test files found")
            return

        self._results_panel.clear()
        self._toolbar.set_running_state(True)
        self._detail_tabs.setCurrentWidget(self._results_panel)
        self._status_bar.showMessage(f"Running {len(test_paths)} tests...")

        from desktop_tester.runner.runner import TestRunnerWorker
        self._runner_worker = TestRunnerWorker(self._runner, test_paths)
        self._runner_worker.finished.connect(self._on_run_finished)
        self._runner_worker.start()

    def _on_test_started(self, test_name: str, test_path: str) -> None:
        self._results_panel.add_test_header(test_name)
        # Load the test steps into the step list so the command log shows them
        path = Path(test_path)
        try:
            test_data = load_test_file(path)
            self._current_test_path = path
            steps = test_data.get("steps", [])
            self._step_list.model.set_steps(steps)
            self._step_list.model.clear_results()
            self._step_list.set_status(f"Running: {test_name}")
        except Exception:
            pass

    def _on_run_step_started(self, step_id: str) -> None:
        self._step_list.model.set_current_step(step_id)

    def _on_run_step_completed(self, result: StepResult) -> None:
        self._step_list.model.set_step_result(result)
        self._results_panel.add_step_result(result)

        if result.screenshot_path:
            self._screenshot_viewer.load_screenshot(result.screenshot_path)

    def _on_test_completed(self, result: TestResult) -> None:
        self._results_panel.set_test_result(result)
        self._step_list.set_status(
            f"{result.test_name}: {result.status.upper()} ({result.duration_ms:.0f}ms)"
        )

    def _on_run_finished(self) -> None:
        self._toolbar.set_running_state(False)
        if self._runner_worker and self._runner_worker.summary:
            summary = self._runner_worker.summary
            self._results_panel.set_run_summary(summary)

            # Generate HTML report
            report_path = self._generate_html_report(summary)
            if report_path:
                self._status_bar.showMessage(
                    f"Run complete: {summary.passed}/{summary.total} passed "
                    f"({summary.duration_ms:.0f}ms) - Report: {report_path.name}"
                )
            else:
                self._status_bar.showMessage(
                    f"Run complete: {summary.passed}/{summary.total} passed "
                    f"({summary.duration_ms:.0f}ms)"
                )
        else:
            self._status_bar.showMessage("Run complete")

    def _generate_html_report(self, summary) -> Path | None:
        """Generate an HTML report and return the path, or None on failure."""
        if not self._project_dir or not self._project_config:
            return None
        try:
            from datetime import datetime

            from desktop_tester.reporter.reporter import ReportGenerator

            report_dir = self._project_dir / self._project_config.reports_dir
            report_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = report_dir / f"report_{timestamp}.html"

            generator = ReportGenerator()
            generator.generate_html(summary, report_path)
            return report_path
        except Exception:
            return None

    # --- Target app selection ---

    def _get_installed_apps(self) -> list[dict]:
        """Return installed applications, falling back to an empty list."""
        try:
            import sys
            if sys.platform == "darwin":
                from desktop_tester.core.macos_backend import MacOSBackend
                return MacOSBackend.list_installed_applications()
        except Exception:
            pass
        return []

    def _select_target_app(self) -> None:
        if not self._ensure_engine():
            return

        apps = self._engine.list_running_apps()
        dialog = AppSelectorDialog(apps, self)
        if dialog.exec() == AppSelectorDialog.Accepted and dialog.selected_app:
            app = dialog.selected_app
            identifier = app.get("bundle_id") or app.get("name") or str(app.get("pid"))
            try:
                self._engine.attach_to_app(identifier)
                self._status_bar.showMessage(f"Connected to: {app.get('name')}")

                # Save selection to project config
                if self._project_config and self._project_dir:
                    self._project_config.target_app.name = app.get("name", "")
                    self._project_config.target_app.bundle_id = app.get("bundle_id", "")
                    save_project(
                        self._project_dir / "project.yaml", self._project_config
                    )
            except Exception as e:
                QMessageBox.warning(self, "Connection Error", f"Failed to connect:\n{e}")

    def _try_connect_saved_app(self, launch: bool = True) -> bool:
        """Try to connect to the target app saved in the project config.

        If *launch* is True (default), the app will be launched when it is not
        already running.  Returns True if successfully connected.
        """
        if not self._project_config or not self._ensure_engine():
            return False

        target = self._project_config.target_app
        identifier = target.bundle_id or target.name
        if not identifier:
            return False

        try:
            if launch:
                self._engine.connect_or_launch(target)
            else:
                self._engine.attach_to_app(identifier)
            self._status_bar.showMessage(
                f"Connected to: {target.name or identifier}"
            )
            return True
        except Exception:
            return False

    def _ensure_connected(self) -> bool:
        """Ensure we're connected to a target app.

        Tries the saved config first, then falls back to the app selector.
        """
        if self._engine and self._engine.app_ref:
            return True

        # Try saved target app first
        if self._try_connect_saved_app():
            return True

        # Fall back to manual selection
        self._select_target_app()
        return self._engine is not None and self._engine.app_ref is not None
