"""Evaluates assertion steps."""

from __future__ import annotations

import re
import time
from typing import Any

from desktop_tester.core.engine import AutomationEngine
from desktop_tester.core.locator import LocatorStrategy
from desktop_tester.exceptions import AssertionError as DTAssertionError
from desktop_tester.models.step import AssertionType, ComparisonOperator, Step, StepResult


class AssertionExecutor:
    """Evaluates assertion steps and returns StepResults."""

    def __init__(self, engine: AutomationEngine):
        self._engine = engine

    def evaluate(self, step: Step) -> StepResult:
        """Evaluate an assertion step and return the result."""
        start = time.time()
        assertion = step.assertion
        if not assertion:
            return StepResult(
                step_id=step.id,
                status="error",
                error_message="Assertion step has no assertion definition",
                duration_ms=0,
            )

        assertion_type = AssertionType(assertion["type"])
        # The target locator lives on step.target (set by the element picker / editor).
        # Use it as the canonical source; fall back to assertion["target"] for
        # backwards compatibility with hand-written YAML.
        target = step.target or assertion.get("target")

        try:
            if assertion_type == AssertionType.ELEMENT_EXISTS:
                self._assert_element_exists(target)
            elif assertion_type == AssertionType.ELEMENT_NOT_EXISTS:
                self._assert_element_not_exists(target)
            elif assertion_type == AssertionType.ELEMENT_TEXT:
                actual = self._assert_element_text(target, assertion)
                duration = (time.time() - start) * 1000
                return StepResult(
                    step_id=step.id, status="passed",
                    duration_ms=duration, actual_value=actual,
                )
            elif assertion_type == AssertionType.ELEMENT_VALUE:
                actual = self._assert_element_value(target, assertion)
                duration = (time.time() - start) * 1000
                return StepResult(
                    step_id=step.id, status="passed",
                    duration_ms=duration, actual_value=actual,
                )
            elif assertion_type == AssertionType.ELEMENT_ENABLED:
                self._assert_element_enabled(target, assertion)
            elif assertion_type == AssertionType.ELEMENT_VISIBLE:
                self._assert_element_visible(target, assertion)
            elif assertion_type == AssertionType.ELEMENT_COUNT:
                actual = self._assert_element_count(target, assertion)
                duration = (time.time() - start) * 1000
                return StepResult(
                    step_id=step.id, status="passed",
                    duration_ms=duration, actual_value=str(actual),
                )
            else:
                return StepResult(
                    step_id=step.id, status="error",
                    error_message=f"Unsupported assertion type: {assertion_type}",
                    duration_ms=(time.time() - start) * 1000,
                )

            duration = (time.time() - start) * 1000
            return StepResult(step_id=step.id, status="passed", duration_ms=duration)

        except DTAssertionError as e:
            duration = (time.time() - start) * 1000
            return StepResult(
                step_id=step.id, status="failed",
                duration_ms=duration,
                error_message=str(e),
                actual_value=str(e.actual) if e.actual is not None else None,
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return StepResult(
                step_id=step.id, status="error",
                duration_ms=duration, error_message=str(e),
            )

    def _resolve_target(self, target: dict | None) -> Any:
        """Find the target element from a locator dict."""
        if not target:
            raise DTAssertionError("Assertion missing target")
        locator = LocatorStrategy.from_dict(target)
        return self._engine.find_element(locator)

    def _assert_element_exists(self, target: dict | None) -> None:
        if not target:
            raise DTAssertionError("Assertion missing target")
        locator = LocatorStrategy.from_dict(target)
        try:
            self._engine.find_element(locator)
        except Exception:
            raise DTAssertionError("Expected element to exist, but it was not found")

    def _assert_element_not_exists(self, target: dict | None) -> None:
        if not target:
            raise DTAssertionError("Assertion missing target")
        locator = LocatorStrategy.from_dict(target)
        locator.timeout = 1.0  # Short timeout for "not exists"
        try:
            self._engine.find_element(locator)
            raise DTAssertionError("Expected element to not exist, but it was found")
        except DTAssertionError:
            raise
        except Exception:
            pass  # Element not found — assertion passes

    def _assert_element_text(self, target: dict | None, assertion: dict) -> str:
        element = self._resolve_target(target)
        # Use get_element_text which walks children for container elements
        actual = self._engine.get_element_text(element)
        expected = assertion.get("expected", "")
        operator = ComparisonOperator(assertion.get("operator", "equals"))
        self._compare(actual, expected, operator, "text")
        return actual

    def _assert_element_value(self, target: dict | None, assertion: dict) -> str:
        element = self._resolve_target(target)
        # Use get_element_text which walks children for container elements
        actual = self._engine.get_element_text(element)
        expected = assertion.get("expected", "")
        operator = ComparisonOperator(assertion.get("operator", "equals"))
        self._compare(actual, expected, operator, "value")
        return actual

    def _assert_element_enabled(self, target: dict | None, assertion: dict) -> None:
        element = self._resolve_target(target)
        expected = assertion.get("expected", True)
        if element.enabled != expected:
            raise DTAssertionError(
                f"Expected enabled={expected}, got enabled={element.enabled}",
                expected=expected, actual=element.enabled,
            )

    def _assert_element_visible(self, target: dict | None, assertion: dict) -> None:
        element = self._resolve_target(target)
        expected = assertion.get("expected", True)
        if element.visible != expected:
            raise DTAssertionError(
                f"Expected visible={expected}, got visible={element.visible}",
                expected=expected, actual=element.visible,
            )

    def _assert_element_count(self, target: dict | None, assertion: dict) -> int:
        if not target:
            raise DTAssertionError("Assertion missing target")
        locator = LocatorStrategy.from_dict(target)
        elements = self._engine.find_elements(locator)
        actual = len(elements)
        expected = int(assertion.get("expected", 0))
        operator = ComparisonOperator(assertion.get("operator", "equals"))
        self._compare(str(actual), str(expected), operator, "count")
        return actual

    def _compare(
        self, actual: str, expected: str, operator: ComparisonOperator, field_name: str
    ) -> None:
        """Compare actual vs expected using the given operator."""
        passed = False

        if operator == ComparisonOperator.EQUALS:
            passed = actual == expected
        elif operator == ComparisonOperator.NOT_EQUALS:
            passed = actual != expected
        elif operator == ComparisonOperator.CONTAINS:
            passed = expected in actual
        elif operator == ComparisonOperator.NOT_CONTAINS:
            passed = expected not in actual
        elif operator == ComparisonOperator.STARTS_WITH:
            passed = actual.startswith(expected)
        elif operator == ComparisonOperator.ENDS_WITH:
            passed = actual.endswith(expected)
        elif operator == ComparisonOperator.GREATER_THAN:
            try:
                passed = float(actual) > float(expected)
            except ValueError:
                passed = actual > expected
        elif operator == ComparisonOperator.LESS_THAN:
            try:
                passed = float(actual) < float(expected)
            except ValueError:
                passed = actual < expected
        elif operator == ComparisonOperator.MATCHES_REGEX:
            passed = bool(re.search(expected, actual))

        if not passed:
            raise DTAssertionError(
                f"Assertion failed: {field_name} {operator.value} "
                f"expected '{expected}', got '{actual}'",
                expected=expected, actual=actual,
            )
