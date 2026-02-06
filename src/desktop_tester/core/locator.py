"""Locator strategies for finding UI elements."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


class LocatorType(Enum):
    ACCESSIBILITY_ID = "accessibility_id"
    ROLE_AND_TITLE = "role_title"
    ROLE_AND_LABEL = "role_label"
    PATH = "path"
    TEXT_CONTENT = "text_content"
    IMAGE = "image"
    COORDINATE = "coordinate"


@dataclass
class LocatorStrategy:
    """Defines how to find a UI element, with optional fallback chain."""

    type: LocatorType
    value: str
    role: Optional[str] = None
    index: Optional[int] = None
    timeout: float = 5.0
    fallback: Optional[LocatorStrategy] = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"type": self.type.value, "value": self.value}
        if self.role:
            d["role"] = self.role
        if self.index is not None:
            d["index"] = self.index
        if self.timeout != 5.0:
            d["timeout"] = self.timeout
        if self.fallback:
            d["fallback"] = self.fallback.to_dict()
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LocatorStrategy:
        fallback = None
        if "fallback" in data:
            fallback = cls.from_dict(data["fallback"])
        return cls(
            type=LocatorType(data["type"]),
            value=data["value"],
            role=data.get("role"),
            index=data.get("index"),
            timeout=data.get("timeout", 5.0),
            fallback=fallback,
        )
