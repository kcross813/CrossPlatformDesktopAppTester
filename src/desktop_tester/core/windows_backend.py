"""Windows automation backend using pywinauto (stub for Phase 2)."""

from __future__ import annotations

import sys

if sys.platform != "win32":
    raise ImportError("Windows backend can only be imported on Windows")

from desktop_tester.core.locator import LocatorStrategy
from desktop_tester.core.platform_base import PlatformBackend
from desktop_tester.models.element_ref import UIElement


class WindowsBackend(PlatformBackend):
    """Windows implementation using pywinauto UI Automation.

    This is a stub for Phase 2 implementation.
    """

    def find_element(self, app_ref: object, locator: LocatorStrategy) -> UIElement:
        raise NotImplementedError("Windows backend not yet implemented")

    def find_elements(self, app_ref: object, locator: LocatorStrategy) -> list[UIElement]:
        raise NotImplementedError("Windows backend not yet implemented")

    def get_element_at_point(self, x: int, y: int) -> UIElement | None:
        raise NotImplementedError("Windows backend not yet implemented")

    def get_element_tree(self, app_ref: object, max_depth: int = 10) -> dict:
        raise NotImplementedError("Windows backend not yet implemented")

    def perform_click(self, element: UIElement) -> None:
        raise NotImplementedError("Windows backend not yet implemented")

    def perform_double_click(self, element: UIElement) -> None:
        raise NotImplementedError("Windows backend not yet implemented")

    def perform_right_click(self, element: UIElement) -> None:
        raise NotImplementedError("Windows backend not yet implemented")

    def perform_type_text(self, element: UIElement, text: str) -> None:
        raise NotImplementedError("Windows backend not yet implemented")

    def perform_key_combo(self, keys: list[str]) -> None:
        raise NotImplementedError("Windows backend not yet implemented")

    def launch_application(self, path: str, args: list[str] | None = None) -> object:
        raise NotImplementedError("Windows backend not yet implemented")

    def attach_to_application(self, identifier: str) -> object:
        raise NotImplementedError("Windows backend not yet implemented")

    def terminate_application(self, app_ref: object) -> None:
        raise NotImplementedError("Windows backend not yet implemented")

    def list_running_applications(self) -> list[dict]:
        raise NotImplementedError("Windows backend not yet implemented")

    def take_screenshot(
        self,
        region: tuple[int, int, int, int] | None = None,
        app_ref: object | None = None,
    ) -> bytes:
        raise NotImplementedError("Windows backend not yet implemented")
