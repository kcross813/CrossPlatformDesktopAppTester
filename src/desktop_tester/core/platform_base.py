"""Abstract base class for platform-specific automation backends."""

from __future__ import annotations

from abc import ABC, abstractmethod

from desktop_tester.core.locator import LocatorStrategy
from desktop_tester.models.element_ref import UIElement


class PlatformBackend(ABC):
    """Interface that each OS backend must implement."""

    # --- Element discovery ---

    @abstractmethod
    def find_element(self, app_ref: object, locator: LocatorStrategy) -> UIElement:
        """Find a single UI element matching the locator.

        Raises ElementNotFoundError if not found within locator.timeout.
        """
        ...

    @abstractmethod
    def find_elements(self, app_ref: object, locator: LocatorStrategy) -> list[UIElement]:
        """Find all UI elements matching the locator."""
        ...

    @abstractmethod
    def get_element_at_point(self, x: int, y: int) -> UIElement | None:
        """Get the UI element at the given screen coordinates."""
        ...

    @abstractmethod
    def get_element_tree(self, app_ref: object, max_depth: int = 10) -> dict:
        """Return the accessibility tree as a nested dict."""
        ...

    def get_focused_element(self, app_ref: object) -> UIElement | None:
        """Get the UI element that currently has keyboard focus.

        Returns None if no element is focused or focus cannot be determined.
        """
        return None

    def get_element_text(self, element: UIElement) -> str:
        """Get the visible text content of an element, including its children.

        For container elements (groups, views), this walks the children to
        collect text from child static_text / text_field elements.
        """
        # Default: use the element's own text fields
        return element.value or element.title or element.label or ""

    # --- Actions ---

    @abstractmethod
    def perform_click(self, element: UIElement) -> None:
        """Perform a left click on the element."""
        ...

    @abstractmethod
    def perform_double_click(self, element: UIElement) -> None:
        """Perform a double click on the element."""
        ...

    @abstractmethod
    def perform_right_click(self, element: UIElement) -> None:
        """Perform a right click on the element."""
        ...

    @abstractmethod
    def perform_type_text(self, element: UIElement, text: str) -> None:
        """Type text into an element."""
        ...

    @abstractmethod
    def perform_key_combo(self, keys: list[str]) -> None:
        """Press a key combination (e.g. ['cmd', 'c'])."""
        ...

    # --- Application management ---

    @abstractmethod
    def launch_application(self, path: str, args: list[str] | None = None) -> object:
        """Launch an application and return an OS-specific app reference."""
        ...

    @abstractmethod
    def attach_to_application(self, identifier: str) -> object:
        """Attach to a running application by name, bundle ID, or PID."""
        ...

    @abstractmethod
    def terminate_application(self, app_ref: object) -> None:
        """Gracefully terminate the application associated with app_ref."""
        ...

    @abstractmethod
    def list_running_applications(self) -> list[dict]:
        """Return list of running apps with name, pid, bundle_id."""
        ...

    def type_keys(self, text: str) -> None:
        """Type text into the currently focused element via keyboard events."""
        for char in text:
            self.perform_key_combo([char])

    # --- Screenshots ---

    @abstractmethod
    def take_screenshot(
        self,
        region: tuple[int, int, int, int] | None = None,
        app_ref: object | None = None,
    ) -> bytes:
        """Capture a screenshot as PNG bytes.

        If *app_ref* is provided, capture only the window(s) belonging to that
        application.  Falls back to full-screen capture when the window cannot
        be identified.
        """
        ...
