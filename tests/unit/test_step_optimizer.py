"""Tests for the step optimizer."""

import pytest

from desktop_tester.models.step import ActionType, Step
from desktop_tester.recorder.step_optimizer import StepOptimizer


@pytest.fixture
def optimizer():
    return StepOptimizer()


class TestMergeKeystrokes:
    def test_merge_consecutive_chars(self, optimizer):
        steps = [
            Step(id="1", action=ActionType.TYPE_TEXT, text="H"),
            Step(id="2", action=ActionType.TYPE_TEXT, text="e"),
            Step(id="3", action=ActionType.TYPE_TEXT, text="l"),
            Step(id="4", action=ActionType.TYPE_TEXT, text="l"),
            Step(id="5", action=ActionType.TYPE_TEXT, text="o"),
        ]
        result = optimizer.optimize(steps)
        assert len(result) == 1
        assert result[0].action == ActionType.TYPE_TEXT
        assert result[0].text == "Hello"

    def test_no_merge_with_clicks(self, optimizer):
        steps = [
            Step(id="1", action=ActionType.TYPE_TEXT, text="A"),
            Step(id="2", action=ActionType.CLICK, target={"type": "role_title", "value": "X"}),
            Step(id="3", action=ActionType.TYPE_TEXT, text="B"),
        ]
        result = optimizer.optimize(steps)
        assert len(result) == 3
        assert result[0].text == "A"
        assert result[1].action == ActionType.CLICK
        assert result[2].text == "B"

    def test_merge_multiple_groups(self, optimizer):
        steps = [
            Step(id="1", action=ActionType.TYPE_TEXT, text="A"),
            Step(id="2", action=ActionType.TYPE_TEXT, text="B"),
            Step(id="3", action=ActionType.CLICK),
            Step(id="4", action=ActionType.TYPE_TEXT, text="C"),
            Step(id="5", action=ActionType.TYPE_TEXT, text="D"),
        ]
        result = optimizer.optimize(steps)
        assert len(result) == 3
        assert result[0].text == "AB"
        assert result[1].action == ActionType.CLICK
        assert result[2].text == "CD"

    def test_no_merge_multi_char_text(self, optimizer):
        """Multi-character TYPE_TEXT (already merged) should not be re-merged."""
        steps = [
            Step(id="1", action=ActionType.TYPE_TEXT, text="Hello"),
        ]
        result = optimizer.optimize(steps)
        assert len(result) == 1
        assert result[0].text == "Hello"


class TestReassignIds:
    def test_sequential_ids(self, optimizer):
        steps = [
            Step(id="x", action=ActionType.CLICK),
            Step(id="y", action=ActionType.CLICK),
            Step(id="z", action=ActionType.CLICK),
        ]
        result = optimizer.optimize(steps)
        assert result[0].id == "step_1"
        assert result[1].id == "step_2"
        assert result[2].id == "step_3"
