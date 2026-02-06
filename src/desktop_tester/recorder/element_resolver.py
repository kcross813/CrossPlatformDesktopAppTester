"""Resolves the UI element under the cursor during recording."""

from __future__ import annotations

from desktop_tester.core.engine import AutomationEngine
from desktop_tester.core.locator import LocatorStrategy, LocatorType
from desktop_tester.models.element_ref import UIElement


class ElementResolver:
    """Identifies the UI element at a screen position and generates locator strategies."""

    def __init__(self, engine: AutomationEngine):
        self._engine = engine

    def resolve(self, x: int, y: int) -> tuple[UIElement | None, LocatorStrategy | None]:
        """Resolve the element at (x, y) and generate the best locator for it.

        Returns (element, locator) or (None, None) if nothing found.
        """
        element = self._engine.get_element_at_point(x, y)
        if element is None:
            return None, None

        locator = self._build_locator(element)
        return element, locator

    def _build_locator(self, element: UIElement) -> LocatorStrategy:
        """Build the best locator strategy for the given element.

        Priority:
        1. accessibility_id (most stable)
        2. role + title
        3. role + label
        4. coordinate (last resort)
        """
        # 1. Try accessibility_id
        if element.identifier:
            return LocatorStrategy(
                type=LocatorType.ACCESSIBILITY_ID,
                value=element.identifier,
                fallback=self._build_fallback(element),
            )

        # 2. Try role + title
        if element.title:
            return LocatorStrategy(
                type=LocatorType.ROLE_AND_TITLE,
                value=element.title,
                role=element.role,
                fallback=self._build_coordinate_fallback(element),
            )

        # 3. Try role + label
        if element.label:
            return LocatorStrategy(
                type=LocatorType.ROLE_AND_LABEL,
                value=element.label,
                role=element.role,
                fallback=self._build_coordinate_fallback(element),
            )

        # 4. Try role + value
        if element.value:
            return LocatorStrategy(
                type=LocatorType.ROLE_AND_TITLE,
                value=element.value,
                role=element.role,
                fallback=self._build_coordinate_fallback(element),
            )

        # 5. Coordinate fallback
        return self._build_coordinate_fallback(element)

    def _build_fallback(self, element: UIElement) -> LocatorStrategy | None:
        """Build a fallback locator (role + title/label)."""
        if element.title:
            return LocatorStrategy(
                type=LocatorType.ROLE_AND_TITLE,
                value=element.title,
                role=element.role,
                fallback=self._build_coordinate_fallback(element),
            )
        if element.label:
            return LocatorStrategy(
                type=LocatorType.ROLE_AND_LABEL,
                value=element.label,
                role=element.role,
            )
        return None

    def _build_coordinate_fallback(self, element: UIElement) -> LocatorStrategy:
        """Build a coordinate-based fallback locator."""
        cx, cy = element.center
        return LocatorStrategy(
            type=LocatorType.COORDINATE,
            value=f"{cx},{cy}",
        )
