"""Tests for data models."""

import pytest

from desktop_tester.models.step import (
    ActionType,
    AssertionType,
    ComparisonOperator,
    Step,
    StepResult,
    TestResult,
    RunSummary,
)
from desktop_tester.models.element_ref import UIElement
from desktop_tester.models.project import ProjectConfig, TargetApp, ProjectSettings


class TestStep:
    def test_create_step(self):
        step = Step(id="step_1", action=ActionType.CLICK, description="Click OK")
        assert step.id == "step_1"
        assert step.action == ActionType.CLICK
        assert step.description == "Click OK"
        assert step.target is None
        assert step.timeout is None
        assert step.continue_on_failure is False

    def test_step_with_target(self):
        step = Step(
            id="step_1",
            action=ActionType.CLICK,
            target={"type": "role_title", "role": "button", "value": "OK"},
        )
        assert step.target["type"] == "role_title"
        assert step.target["role"] == "button"

    def test_step_with_text(self):
        step = Step(
            id="step_1",
            action=ActionType.TYPE_TEXT,
            text="Hello World",
        )
        assert step.text == "Hello World"

    def test_step_with_keys(self):
        step = Step(
            id="step_1",
            action=ActionType.KEY_COMBO,
            keys=["cmd", "c"],
        )
        assert step.keys == ["cmd", "c"]


class TestStepResult:
    def test_create_passed_result(self):
        result = StepResult(step_id="step_1", status="passed", duration_ms=100.5)
        assert result.step_id == "step_1"
        assert result.status == "passed"
        assert result.duration_ms == 100.5
        assert result.error_message is None

    def test_create_failed_result(self):
        result = StepResult(
            step_id="step_1",
            status="failed",
            duration_ms=50.0,
            error_message="Element not found",
        )
        assert result.status == "failed"
        assert result.error_message == "Element not found"


class TestTestResult:
    def test_create_test_result(self):
        result = TestResult(
            test_name="Test 1",
            test_file="test_1.yaml",
            status="passed",
            duration_ms=500.0,
        )
        assert result.test_name == "Test 1"
        assert result.step_results == []


class TestRunSummary:
    def test_default_summary(self):
        summary = RunSummary()
        assert summary.total == 0
        assert summary.passed == 0
        assert summary.failed == 0
        assert summary.test_results == []


class TestUIElement:
    def test_create_element(self):
        el = UIElement(role="button", title="OK", x=100, y=200, width=50, height=30)
        assert el.role == "button"
        assert el.title == "OK"
        assert el.center == (125, 215)
        assert el.bounds == (100, 200, 50, 30)

    def test_to_dict(self):
        el = UIElement(role="button", title="OK", x=10, y=20, width=30, height=40)
        d = el.to_dict()
        assert d["role"] == "button"
        assert d["title"] == "OK"
        assert d["x"] == 10

    def test_element_defaults(self):
        el = UIElement(role="text_field")
        assert el.enabled is True
        assert el.visible is True
        assert el.focused is False


class TestProjectConfig:
    def test_from_dict(self):
        data = {
            "name": "My Project",
            "version": "2.0",
            "description": "Test project",
            "target_app": {"bundle_id": "com.example.app"},
            "settings": {"default_timeout": 10.0, "screenshot_on_failure": False},
            "directories": {"tests": "my_tests"},
        }
        config = ProjectConfig.from_dict(data)
        assert config.name == "My Project"
        assert config.version == "2.0"
        assert config.target_app.bundle_id == "com.example.app"
        assert config.settings.default_timeout == 10.0
        assert config.settings.screenshot_on_failure is False
        assert config.tests_dir == "my_tests"

    def test_to_dict_roundtrip(self):
        config = ProjectConfig(
            name="Test",
            target_app=TargetApp(bundle_id="com.test"),
            settings=ProjectSettings(default_timeout=8.0),
        )
        d = config.to_dict()
        restored = ProjectConfig.from_dict(d)
        assert restored.name == config.name
        assert restored.target_app.bundle_id == config.target_app.bundle_id
        assert restored.settings.default_timeout == config.settings.default_timeout
