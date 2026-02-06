"""Core data models for test steps, results, and runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class ActionType(Enum):
    CLICK = "click"
    DOUBLE_CLICK = "double_click"
    RIGHT_CLICK = "right_click"
    TYPE_TEXT = "type_text"
    KEY_COMBO = "key_combo"
    CLEAR_FIELD = "clear_field"
    SELECT_MENU = "select_menu"
    DRAG_DROP = "drag_drop"

    LAUNCH_APP = "launch_app"
    CLOSE_APP = "close_app"
    WAIT_FOR_WINDOW = "wait_for_window"

    WAIT = "wait"
    WAIT_FOR_ELEMENT = "wait_for_element"
    WAIT_FOR_ELEMENT_GONE = "wait_for_element_gone"

    ASSERT = "assert"
    RUN_SCRIPT = "run_script"


class AssertionType(Enum):
    ELEMENT_EXISTS = "element_exists"
    ELEMENT_NOT_EXISTS = "element_not_exists"
    ELEMENT_TEXT = "element_text"
    ELEMENT_VALUE = "element_value"
    ELEMENT_ENABLED = "element_enabled"
    ELEMENT_VISIBLE = "element_visible"
    ELEMENT_COUNT = "element_count"
    SCREENSHOT_MATCH = "screenshot_match"


class ComparisonOperator(Enum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    MATCHES_REGEX = "matches_regex"


@dataclass
class Step:
    """A single step in a test case."""

    id: str
    action: ActionType
    description: str = ""

    # For actions targeting a UI element
    target: Optional[dict[str, Any]] = None

    # Action-specific parameters
    text: Optional[str] = None
    keys: Optional[list[str]] = None
    duration: Optional[float] = None
    title: Optional[str] = None

    # For assertions
    assertion: Optional[dict[str, Any]] = None

    # For custom scripts
    script: Optional[str] = None

    # Metadata
    screenshot: bool = False
    timeout: Optional[float] = None
    continue_on_failure: bool = False


@dataclass
class StepResult:
    """Result of executing a single step."""

    step_id: str
    status: str  # "passed", "failed", "skipped", "error"
    duration_ms: float = 0.0
    description: str = ""
    error_message: Optional[str] = None
    screenshot_path: Optional[str] = None
    actual_value: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class TestResult:
    """Result of executing a full test case."""

    test_name: str
    test_file: str
    status: str  # "passed", "failed", "error"
    duration_ms: float = 0.0
    step_results: list[StepResult] = field(default_factory=list)
    started_at: str = ""
    finished_at: str = ""


@dataclass
class RunSummary:
    """Summary of a complete test run (multiple test files)."""

    total: int = 0
    passed: int = 0
    failed: int = 0
    errors: int = 0
    skipped: int = 0
    duration_ms: float = 0.0
    test_results: list[TestResult] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    finished_at: str = ""
