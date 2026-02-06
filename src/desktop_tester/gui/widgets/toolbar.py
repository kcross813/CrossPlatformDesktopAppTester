"""Main toolbar with Record, Stop, Play, Save actions."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QToolBar


class MainToolbar(QToolBar):
    """Toolbar with test recording and execution controls."""

    record_clicked = Signal()
    stop_clicked = Signal()
    run_clicked = Signal()
    run_all_clicked = Signal()
    save_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__("Main Toolbar", parent)
        self.setMovable(False)

        # Record
        self.record_action = QAction("Record", self)
        self.record_action.setToolTip("Start recording a new test (Ctrl+R)")
        self.record_action.setShortcut("Ctrl+R")
        self.record_action.triggered.connect(self.record_clicked)
        self.addAction(self.record_action)

        # Stop
        self.stop_action = QAction("Stop", self)
        self.stop_action.setToolTip("Stop recording or test execution")
        self.stop_action.setEnabled(False)
        self.stop_action.triggered.connect(self.stop_clicked)
        self.addAction(self.stop_action)

        self.addSeparator()

        # Run
        self.run_action = QAction("Run Test", self)
        self.run_action.setToolTip("Run the current test (Ctrl+Enter)")
        self.run_action.setShortcut("Ctrl+Return")
        self.run_action.triggered.connect(self.run_clicked)
        self.addAction(self.run_action)

        # Run All
        self.run_all_action = QAction("Run All", self)
        self.run_all_action.setToolTip("Run all tests in the project")
        self.run_all_action.triggered.connect(self.run_all_clicked)
        self.addAction(self.run_all_action)

        self.addSeparator()

        # Save
        self.save_action = QAction("Save", self)
        self.save_action.setToolTip("Save the current test (Ctrl+S)")
        self.save_action.setShortcut("Ctrl+S")
        self.save_action.triggered.connect(self.save_clicked)
        self.addAction(self.save_action)

    def set_recording_state(self, recording: bool) -> None:
        """Update button states for recording mode."""
        self.record_action.setEnabled(not recording)
        self.stop_action.setEnabled(recording)
        self.run_action.setEnabled(not recording)
        self.run_all_action.setEnabled(not recording)

    def set_running_state(self, running: bool) -> None:
        """Update button states for test execution mode."""
        self.record_action.setEnabled(not running)
        self.stop_action.setEnabled(running)
        self.run_action.setEnabled(not running)
        self.run_all_action.setEnabled(not running)
