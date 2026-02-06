"""Tests for YAML serialization."""

import pytest
from pathlib import Path

from desktop_tester.models.step import ActionType, Step
from desktop_tester.models.serialization import (
    dict_to_step,
    step_to_dict,
    load_yaml,
    load_project,
    load_test_file,
    save_test_file,
)


class TestDictToStep:
    def test_click_step(self):
        data = {
            "id": "step_1",
            "action": "click",
            "description": "Click OK",
            "target": {"type": "role_title", "role": "button", "value": "OK"},
        }
        step = dict_to_step(data)
        assert step.id == "step_1"
        assert step.action == ActionType.CLICK
        assert step.target["value"] == "OK"

    def test_type_text_step(self):
        data = {
            "id": "step_2",
            "action": "type_text",
            "text": "Hello",
        }
        step = dict_to_step(data)
        assert step.action == ActionType.TYPE_TEXT
        assert step.text == "Hello"

    def test_assert_step(self):
        data = {
            "id": "step_3",
            "action": "assert",
            "assertion": {
                "type": "element_text",
                "target": {"type": "role_title", "role": "static_text", "value": "5"},
                "operator": "equals",
                "expected": "5",
            },
        }
        step = dict_to_step(data)
        assert step.action == ActionType.ASSERT
        assert step.assertion["type"] == "element_text"

    def test_defaults(self):
        data = {"id": "step_1", "action": "click"}
        step = dict_to_step(data)
        assert step.description == ""
        assert step.screenshot is False
        assert step.continue_on_failure is False
        assert step.timeout is None


class TestStepToDict:
    def test_minimal_step(self):
        step = Step(id="step_1", action=ActionType.CLICK)
        d = step_to_dict(step)
        assert d["id"] == "step_1"
        assert d["action"] == "click"
        assert "text" not in d  # None values omitted
        assert "target" not in d

    def test_full_step(self):
        step = Step(
            id="step_1",
            action=ActionType.TYPE_TEXT,
            description="Type name",
            target={"type": "role_title", "value": "Name"},
            text="John",
            timeout=10.0,
            screenshot=True,
            continue_on_failure=True,
        )
        d = step_to_dict(step)
        assert d["text"] == "John"
        assert d["timeout"] == 10.0
        assert d["screenshot"] is True
        assert d["continue_on_failure"] is True

    def test_roundtrip(self):
        original = Step(
            id="step_1",
            action=ActionType.KEY_COMBO,
            description="Copy",
            keys=["cmd", "c"],
        )
        d = step_to_dict(original)
        restored = dict_to_step(d)
        assert restored.id == original.id
        assert restored.action == original.action
        assert restored.keys == original.keys


class TestLoadProject:
    def test_load_example_project(self, sample_project_yaml):
        config = load_project(sample_project_yaml)
        assert config.name == "Calculator Tests"
        assert config.target_app.bundle_id == "com.apple.calculator"
        assert config.settings.default_timeout == 5.0
        assert config.tests_dir == "tests"


class TestLoadTestFile:
    def test_load_example_test(self, sample_test_yaml):
        data = load_test_file(sample_test_yaml)
        assert data["name"] == "Basic Addition"
        assert len(data["steps"]) == 5
        assert len(data["setup"]) == 3
        assert len(data["teardown"]) == 1

        # Check first step
        step = data["steps"][0]
        assert step.action == ActionType.CLICK
        assert step.description == "Click the 2 button"

        # Check assertion step
        assert_step = data["steps"][4]
        assert assert_step.action == ActionType.ASSERT
        assert assert_step.assertion["type"] == "element_text"


class TestSaveTestFile:
    def test_save_and_reload(self, tmp_path):
        test_path = tmp_path / "test_save.yaml"
        steps = [
            Step(id="step_1", action=ActionType.CLICK, description="Click"),
            Step(id="step_2", action=ActionType.TYPE_TEXT, text="Hello"),
        ]
        save_test_file(test_path, name="Save Test", steps=steps, tags=["smoke"])

        data = load_test_file(test_path)
        assert data["name"] == "Save Test"
        assert len(data["steps"]) == 2
        assert data["steps"][0].action == ActionType.CLICK
        assert data["steps"][1].text == "Hello"
