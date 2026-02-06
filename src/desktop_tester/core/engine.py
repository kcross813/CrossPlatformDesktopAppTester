"""AutomationEngine - main facade for all automation operations."""

from __future__ import annotations

from typing import Optional

from desktop_tester.core.app_manager import AppManager
from desktop_tester.core.locator import LocatorStrategy
from desktop_tester.core.platform_base import PlatformBackend
from desktop_tester.models.element_ref import UIElement
from desktop_tester.models.project import TargetApp


class AutomationEngine:
    """Facade for all automation operations against a target app."""

    def __init__(self, backend: PlatformBackend):
        self._backend = backend
        self._app_manager = AppManager(backend)

    @property
    def backend(self) -> PlatformBackend:
        return self._backend

    @property
    def app_manager(self) -> AppManager:
        return self._app_manager

    @property
    def app_ref(self) -> object | None:
        return self._app_manager.app_ref

    def launch_app(self, target: TargetApp) -> None:
        """Launch the target application."""
        self._app_manager.launch(target)

    def attach_to_app(self, identifier: str) -> None:
        """Attach to an already-running application."""
        self._app_manager.attach(identifier)

    def connect_or_launch(self, target: TargetApp) -> None:
        """Attach to the target app if running, otherwise launch it."""
        self._app_manager.launch_or_attach(target)

    def find_element(self, locator: LocatorStrategy) -> UIElement:
        """Find a single UI element matching the locator."""
        if not self._app_manager.is_connected:
            raise RuntimeError("Not connected to any application")
        return self._backend.find_element(self._app_manager.app_ref, locator)

    def find_elements(self, locator: LocatorStrategy) -> list[UIElement]:
        """Find all UI elements matching the locator."""
        if not self._app_manager.is_connected:
            raise RuntimeError("Not connected to any application")
        return self._backend.find_elements(self._app_manager.app_ref, locator)

    def get_element_at_point(self, x: int, y: int) -> UIElement | None:
        """Get the UI element at the given screen coordinates."""
        return self._backend.get_element_at_point(x, y)

    def get_element_text(self, element: UIElement) -> str:
        """Get visible text from an element, including child text."""
        return self._backend.get_element_text(element)

    def click(self, element: UIElement) -> None:
        self._backend.perform_click(element)

    def double_click(self, element: UIElement) -> None:
        self._backend.perform_double_click(element)

    def right_click(self, element: UIElement) -> None:
        self._backend.perform_right_click(element)

    def type_text(self, element: UIElement, text: str) -> None:
        self._backend.perform_type_text(element, text)

    def type_keys(self, text: str) -> None:
        """Type text into the focused element via keyboard events (no target needed)."""
        self._backend.type_keys(text)

    def key_combo(self, keys: list[str]) -> None:
        self._backend.perform_key_combo(keys)

    def take_screenshot(self, region: tuple[int, int, int, int] | None = None) -> bytes:
        return self._backend.take_screenshot(region, app_ref=self._app_manager.app_ref)

    def terminate_app(self) -> None:
        """Gracefully terminate the target application."""
        if self._app_manager.is_connected:
            self._backend.terminate_application(self._app_manager.app_ref)
            self._app_manager.disconnect()

    def list_running_apps(self) -> list[dict]:
        return self._backend.list_running_applications()
