"""Cross-platform UI element representation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class UIElement:
    """Cross-platform representation of a UI element from accessibility APIs."""

    role: str  # Normalized: "button", "text_field", "window", etc.
    title: Optional[str] = None
    label: Optional[str] = None
    value: Optional[str] = None
    identifier: Optional[str] = None

    # Position and size
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0

    # State
    enabled: bool = True
    visible: bool = True
    focused: bool = False

    # Hierarchy path for robust re-identification
    path: Optional[str] = None  # e.g. "window[0]/group[1]/button[2]"

    # Internal: holds the native OS element reference
    _native_ref: Any = field(default=None, repr=False, compare=False)

    @property
    def center(self) -> tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)

    @property
    def bounds(self) -> tuple[int, int, int, int]:
        return (self.x, self.y, self.width, self.height)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a dict (excluding native ref)."""
        d: dict[str, Any] = {"role": self.role}
        if self.title:
            d["title"] = self.title
        if self.label:
            d["label"] = self.label
        if self.value:
            d["value"] = self.value
        if self.identifier:
            d["identifier"] = self.identifier
        d["x"] = self.x
        d["y"] = self.y
        d["width"] = self.width
        d["height"] = self.height
        d["enabled"] = self.enabled
        d["visible"] = self.visible
        if self.path:
            d["path"] = self.path
        return d
