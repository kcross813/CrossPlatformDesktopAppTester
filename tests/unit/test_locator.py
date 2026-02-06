"""Tests for locator strategies."""

import pytest

from desktop_tester.core.locator import LocatorStrategy, LocatorType


class TestLocatorStrategy:
    def test_create_basic(self):
        loc = LocatorStrategy(
            type=LocatorType.ROLE_AND_TITLE,
            value="OK",
            role="button",
        )
        assert loc.type == LocatorType.ROLE_AND_TITLE
        assert loc.value == "OK"
        assert loc.role == "button"
        assert loc.timeout == 5.0
        assert loc.fallback is None

    def test_to_dict(self):
        loc = LocatorStrategy(
            type=LocatorType.ACCESSIBILITY_ID,
            value="btnOK",
        )
        d = loc.to_dict()
        assert d["type"] == "accessibility_id"
        assert d["value"] == "btnOK"
        assert "role" not in d
        assert "timeout" not in d  # Default not serialized

    def test_to_dict_with_fallback(self):
        fallback = LocatorStrategy(
            type=LocatorType.COORDINATE,
            value="100,200",
        )
        loc = LocatorStrategy(
            type=LocatorType.ROLE_AND_TITLE,
            value="OK",
            role="button",
            fallback=fallback,
        )
        d = loc.to_dict()
        assert "fallback" in d
        assert d["fallback"]["type"] == "coordinate"

    def test_from_dict(self):
        data = {
            "type": "role_title",
            "value": "OK",
            "role": "button",
            "timeout": 10.0,
        }
        loc = LocatorStrategy.from_dict(data)
        assert loc.type == LocatorType.ROLE_AND_TITLE
        assert loc.value == "OK"
        assert loc.role == "button"
        assert loc.timeout == 10.0

    def test_from_dict_with_fallback(self):
        data = {
            "type": "accessibility_id",
            "value": "btnOK",
            "fallback": {
                "type": "coordinate",
                "value": "100,200",
            },
        }
        loc = LocatorStrategy.from_dict(data)
        assert loc.fallback is not None
        assert loc.fallback.type == LocatorType.COORDINATE
        assert loc.fallback.value == "100,200"

    def test_roundtrip(self):
        original = LocatorStrategy(
            type=LocatorType.ROLE_AND_LABEL,
            value="Submit",
            role="button",
            index=1,
            timeout=8.0,
        )
        d = original.to_dict()
        restored = LocatorStrategy.from_dict(d)
        assert restored.type == original.type
        assert restored.value == original.value
        assert restored.role == original.role
        assert restored.index == original.index
        assert restored.timeout == original.timeout
