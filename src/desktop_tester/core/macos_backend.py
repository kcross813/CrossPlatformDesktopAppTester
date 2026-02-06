"""macOS automation backend using pyobjc accessibility APIs."""

from __future__ import annotations

import io
import subprocess
import sys
import time
from typing import Any, Optional

if sys.platform != "darwin":
    raise ImportError("macOS backend can only be imported on macOS")

import Cocoa
import Quartz
from ApplicationServices import (
    AXIsProcessTrusted,
    AXUIElementCopyAttributeValue,
    AXUIElementCopyElementAtPosition,
    AXUIElementCreateApplication,
    AXUIElementCreateSystemWide,
    AXUIElementPerformAction,
    AXUIElementSetAttributeValue,
)
from CoreFoundation import CFRelease
from PIL import Image

from desktop_tester.core.locator import LocatorStrategy, LocatorType
from desktop_tester.core.platform_base import PlatformBackend
from desktop_tester.exceptions import (
    AccessibilityPermissionError,
    ApplicationNotFoundError,
    ElementNotFoundError,
)
from desktop_tester.models.element_ref import UIElement

# Normalized role mapping: macOS AXRole -> our canonical names
_ROLE_MAP = {
    "AXButton": "button",
    "AXTextField": "text_field",
    "AXTextArea": "text_area",
    "AXStaticText": "static_text",
    "AXCheckBox": "checkbox",
    "AXRadioButton": "radio_button",
    "AXComboBox": "combo_box",
    "AXList": "list",
    "AXTable": "table",
    "AXWindow": "window",
    "AXGroup": "group",
    "AXMenuBar": "menu_bar",
    "AXMenuItem": "menu_item",
    "AXMenu": "menu",
    "AXSlider": "slider",
    "AXScrollArea": "scroll_area",
    "AXTabGroup": "tab_group",
    "AXToolbar": "toolbar",
    "AXImage": "image",
    "AXPopUpButton": "popup_button",
    "AXSheet": "sheet",
    "AXDialog": "dialog",
    "AXApplication": "application",
    "AXSplitGroup": "split_group",
    "AXScrollBar": "scroll_bar",
    "AXValueIndicator": "value_indicator",
    "AXLink": "link",
    "AXProgressIndicator": "progress_indicator",
}

# Reverse map for looking up native roles from normalized names
_REVERSE_ROLE_MAP = {v: k for k, v in _ROLE_MAP.items()}

# Key name mapping for key combos
_KEY_MAP = {
    "cmd": 0x37,
    "command": 0x37,
    "shift": 0x38,
    "caps_lock": 0x39,
    "option": 0x3A,
    "alt": 0x3A,
    "control": 0x3B,
    "ctrl": 0x3B,
    "return": 0x24,
    "enter": 0x24,
    "tab": 0x30,
    "space": 0x31,
    "delete": 0x33,
    "backspace": 0x33,
    "escape": 0x35,
    "esc": 0x35,
    "up": 0x7E,
    "down": 0x7D,
    "left": 0x7B,
    "right": 0x7C,
    "f1": 0x7A,
    "f2": 0x78,
    "f3": 0x63,
    "f4": 0x76,
    "f5": 0x60,
    "a": 0x00, "b": 0x0B, "c": 0x08, "d": 0x02, "e": 0x0E,
    "f": 0x03, "g": 0x05, "h": 0x04, "i": 0x22, "j": 0x26,
    "k": 0x28, "l": 0x25, "m": 0x2E, "n": 0x2D, "o": 0x1F,
    "p": 0x23, "q": 0x0C, "r": 0x0F, "s": 0x01, "t": 0x11,
    "u": 0x20, "v": 0x09, "w": 0x0D, "x": 0x07, "y": 0x10,
    "z": 0x06,
    "0": 0x1D, "1": 0x12, "2": 0x13, "3": 0x14, "4": 0x15,
    "5": 0x17, "6": 0x16, "7": 0x1A, "8": 0x1C, "9": 0x19,
}

_MODIFIER_KEYS = {"cmd", "command", "shift", "option", "alt", "control", "ctrl"}


def _ax_attr(element: Any, attr: str) -> Any:
    """Safely read an accessibility attribute, returning None on error."""
    err, value = AXUIElementCopyAttributeValue(element, attr, None)
    if err != 0:
        return None
    return value


def _clean_text(text: str) -> str:
    """Strip Unicode control characters (e.g. LTR marks) from element text."""
    import unicodedata
    return "".join(c for c in text if unicodedata.category(c)[0] != "C")


class MacOSBackend(PlatformBackend):
    """macOS implementation using pyobjc Accessibility + Quartz."""

    def __init__(self):
        if not AXIsProcessTrusted():
            raise AccessibilityPermissionError()

    # --- Element discovery ---

    def find_element(self, app_ref: object, locator: LocatorStrategy) -> UIElement:
        deadline = time.time() + locator.timeout
        current_locator: LocatorStrategy | None = locator

        while current_locator is not None:
            while time.time() < deadline:
                result = self._search_element(app_ref, current_locator)
                if result is not None:
                    return result
                time.sleep(0.25)
            # Try fallback locator if available
            current_locator = current_locator.fallback
            if current_locator:
                deadline = time.time() + current_locator.timeout

        raise ElementNotFoundError(locator.to_dict(), locator.timeout)

    def find_elements(self, app_ref: object, locator: LocatorStrategy) -> list[UIElement]:
        results: list[UIElement] = []
        self._search_elements(app_ref, locator, results, max_depth=15)
        return results

    def get_element_at_point(self, x: int, y: int) -> UIElement | None:
        system_wide = AXUIElementCreateSystemWide()
        err, native_element = AXUIElementCopyElementAtPosition(
            system_wide, float(x), float(y), None
        )
        if err != 0 or native_element is None:
            return None
        return self._wrap_native_element(native_element)

    def get_element_text(self, element: UIElement) -> str:
        """Get visible text from an element, walking children if needed."""
        # Try the element's own text first
        direct = _clean_text(str(element.value)) if element.value else None
        if not direct:
            direct = _clean_text(str(element.title)) if element.title else None
        if direct:
            return direct

        # For container elements, walk children to find text
        if element._native_ref is None:
            return element.label or ""
        return self._collect_child_text(element._native_ref, depth=0, max_depth=5)

    def _collect_child_text(self, ax_ref: Any, depth: int, max_depth: int) -> str:
        """Recursively collect text from child elements."""
        if depth > max_depth:
            return ""

        children = _ax_attr(ax_ref, "AXChildren")
        if not children:
            return ""

        parts: list[str] = []
        for child in children:
            role = _ax_attr(child, "AXRole")
            value = _ax_attr(child, "AXValue")
            title = _ax_attr(child, "AXTitle")

            text = None
            if value is not None:
                text = _clean_text(str(value))
            elif title is not None:
                text = _clean_text(str(title))

            if text:
                parts.append(text)
            else:
                # Recurse deeper
                nested = self._collect_child_text(child, depth + 1, max_depth)
                if nested:
                    parts.append(nested)

        return " ".join(parts)

    def get_element_tree(self, app_ref: object, max_depth: int = 10) -> dict:
        return self._build_tree(app_ref, depth=0, max_depth=max_depth)

    # --- Actions ---

    def perform_click(self, element: UIElement) -> None:
        if element._native_ref is not None:
            # Try AX action first
            err = AXUIElementPerformAction(element._native_ref, "AXPress")
            if err == 0:
                return
        # Fallback to CGEvent click
        self._cg_click(element.center)

    def perform_double_click(self, element: UIElement) -> None:
        cx, cy = element.center
        point = Quartz.CGPointMake(cx, cy)
        event = Quartz.CGEventCreateMouseEvent(
            None, Quartz.kCGEventLeftMouseDown, point, Quartz.kCGMouseButtonLeft
        )
        Quartz.CGEventSetIntegerValueField(event, Quartz.kCGMouseEventClickState, 2)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)

        event_up = Quartz.CGEventCreateMouseEvent(
            None, Quartz.kCGEventLeftMouseUp, point, Quartz.kCGMouseButtonLeft
        )
        Quartz.CGEventSetIntegerValueField(event_up, Quartz.kCGMouseEventClickState, 2)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_up)

    def perform_right_click(self, element: UIElement) -> None:
        cx, cy = element.center
        point = Quartz.CGPointMake(cx, cy)
        event_down = Quartz.CGEventCreateMouseEvent(
            None, Quartz.kCGEventRightMouseDown, point, Quartz.kCGMouseButtonRight
        )
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_down)
        event_up = Quartz.CGEventCreateMouseEvent(
            None, Quartz.kCGEventRightMouseUp, point, Quartz.kCGMouseButtonRight
        )
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_up)

    def perform_type_text(self, element: UIElement, text: str) -> None:
        # First try setting the value directly via accessibility
        if element._native_ref is not None:
            err = AXUIElementSetAttributeValue(element._native_ref, "AXValue", text)
            if err == 0:
                return

        # Fallback: click the element first, then type via CGEvents
        self.perform_click(element)
        time.sleep(0.1)
        for char in text:
            self._type_char(char)
            time.sleep(0.02)

    def perform_key_combo(self, keys: list[str]) -> None:
        modifiers: list[str] = []
        regular_keys: list[str] = []

        for key in keys:
            key_lower = key.lower()
            if key_lower in _MODIFIER_KEYS:
                modifiers.append(key_lower)
            else:
                regular_keys.append(key_lower)

        # Build modifier flags
        flags = 0
        for mod in modifiers:
            if mod in ("cmd", "command"):
                flags |= Quartz.kCGEventFlagMaskCommand
            elif mod == "shift":
                flags |= Quartz.kCGEventFlagMaskShift
            elif mod in ("option", "alt"):
                flags |= Quartz.kCGEventFlagMaskAlternate
            elif mod in ("control", "ctrl"):
                flags |= Quartz.kCGEventFlagMaskControl

        for key_name in regular_keys:
            keycode = _KEY_MAP.get(key_name)
            if keycode is None:
                continue
            event_down = Quartz.CGEventCreateKeyboardEvent(None, keycode, True)
            event_up = Quartz.CGEventCreateKeyboardEvent(None, keycode, False)
            if flags:
                Quartz.CGEventSetFlags(event_down, flags)
                Quartz.CGEventSetFlags(event_up, flags)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_down)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_up)

    # --- Application management ---

    def launch_application(self, path: str, args: list[str] | None = None) -> object:
        workspace = Cocoa.NSWorkspace.sharedWorkspace()

        # Try bundle ID first
        if "." in path and "/" not in path:
            # Looks like a bundle ID
            url = workspace.URLForApplicationWithBundleIdentifier_(path)
            if url:
                result = subprocess.run(
                    ["open", "-b", path], capture_output=True, timeout=10
                )
                if result.returncode != 0:
                    raise ApplicationNotFoundError(
                        f"Failed to launch {path}: {result.stderr.decode()}"
                    )
                return self._wait_and_attach(path)

        # Try as a file path
        result = subprocess.run(["open", "-a", path], capture_output=True, timeout=10)
        if result.returncode != 0:
            raise ApplicationNotFoundError(f"Failed to launch {path}: {result.stderr.decode()}")
        return self._wait_and_attach(path)

    def _wait_and_attach(self, identifier: str, timeout: float = 10.0) -> object:
        """Wait for an application to appear and attach to it."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                return self.attach_to_application(identifier)
            except Exception:
                time.sleep(0.5)
        raise ApplicationNotFoundError(
            f"Application '{identifier}' did not become available within {timeout}s"
        )

    def attach_to_application(self, identifier: str) -> object:
        running_apps = Cocoa.NSWorkspace.sharedWorkspace().runningApplications()
        for app in running_apps:
            bid = app.bundleIdentifier()
            name = app.localizedName()
            if bid and bid == identifier:
                return AXUIElementCreateApplication(app.processIdentifier())
            if name and name == identifier:
                return AXUIElementCreateApplication(app.processIdentifier())
            # Also try PID
            if identifier.isdigit() and app.processIdentifier() == int(identifier):
                return AXUIElementCreateApplication(app.processIdentifier())

        raise ApplicationNotFoundError(f"Application not found: {identifier}")

    def terminate_application(self, app_ref: object) -> None:
        # Extract PID from the AXUIElement app ref
        from ApplicationServices import AXUIElementGetPid
        err, pid = AXUIElementGetPid(app_ref, None)
        if err != 0:
            return

        # Find the NSRunningApplication for this PID and terminate it
        running_apps = Cocoa.NSWorkspace.sharedWorkspace().runningApplications()
        for app in running_apps:
            if app.processIdentifier() == pid:
                app.terminate()
                # Wait for it to actually quit
                deadline = time.time() + 5.0
                while time.time() < deadline and not app.isTerminated():
                    time.sleep(0.2)
                return

    def list_running_applications(self) -> list[dict]:
        running_apps = Cocoa.NSWorkspace.sharedWorkspace().runningApplications()
        result = []
        for app in running_apps:
            if app.activationPolicy() == Cocoa.NSApplicationActivationPolicyRegular:
                result.append({
                    "name": str(app.localizedName() or ""),
                    "pid": app.processIdentifier(),
                    "bundle_id": str(app.bundleIdentifier() or ""),
                })
        return sorted(result, key=lambda x: x["name"])

    # --- Screenshots ---

    def take_screenshot(
        self,
        region: tuple[int, int, int, int] | None = None,
        app_ref: object | None = None,
    ) -> bytes:
        # If an app_ref is provided, capture only that application's window
        if app_ref is not None and region is None:
            window_id = self._find_window_id(app_ref)
            if window_id is not None:
                image = Quartz.CGWindowListCreateImage(
                    Quartz.CGRectNull,
                    Quartz.kCGWindowListOptionIncludingWindow,
                    window_id,
                    Quartz.kCGWindowImageBoundsIgnoreFraming,
                )
                if image is not None:
                    return self._cgimage_to_png(image)

        # Fallback: full screen or explicit region
        if region:
            x, y, w, h = region
            rect = Quartz.CGRectMake(x, y, w, h)
        else:
            rect = Quartz.CGRectInfinite

        image = Quartz.CGWindowListCreateImage(
            rect,
            Quartz.kCGWindowListOptionOnScreenOnly,
            Quartz.kCGNullWindowID,
            Quartz.kCGWindowImageDefault,
        )

        if image is None:
            return b""

        return self._cgimage_to_png(image)

    def _find_window_id(self, app_ref: object) -> int | None:
        """Find the main window ID for the application referenced by app_ref."""
        from ApplicationServices import AXUIElementGetPid

        err, pid = AXUIElementGetPid(app_ref, None)
        if err != 0:
            return None

        # Get list of on-screen windows and find one owned by our PID
        window_list = Quartz.CGWindowListCopyWindowInfo(
            Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements,
            Quartz.kCGNullWindowID,
        )
        if window_list is None:
            return None

        for win_info in window_list:
            owner_pid = win_info.get(Quartz.kCGWindowOwnerPID, -1)
            layer = win_info.get(Quartz.kCGWindowLayer, -1)
            if owner_pid == pid and layer == 0:
                return win_info.get(Quartz.kCGWindowNumber)

        return None

    @staticmethod
    def _cgimage_to_png(image: object) -> bytes:
        """Convert a CGImage to PNG bytes."""
        width = Quartz.CGImageGetWidth(image)
        height = Quartz.CGImageGetHeight(image)
        bytes_per_row = Quartz.CGImageGetBytesPerRow(image)
        data_provider = Quartz.CGImageGetDataProvider(image)
        raw_data = Quartz.CGDataProviderCopyData(data_provider)

        # Pass bytes_per_row as stride — CGImage may pad rows for alignment
        pil_image = Image.frombytes(
            "RGBA", (width, height), bytes(raw_data), "raw", "BGRA", bytes_per_row, 1
        )

        buf = io.BytesIO()
        pil_image.save(buf, format="PNG")
        return buf.getvalue()

    # --- Internal helpers ---

    def _wrap_native_element(self, native_ref: Any) -> UIElement:
        """Convert a native AXUIElement to our UIElement."""
        raw_role = _ax_attr(native_ref, "AXRole")
        role_str = str(raw_role) if raw_role else "unknown"
        normalized_role = _ROLE_MAP.get(role_str, role_str.replace("AX", "").lower())

        title = _ax_attr(native_ref, "AXTitle")
        desc = _ax_attr(native_ref, "AXDescription")
        value = _ax_attr(native_ref, "AXValue")
        identifier = _ax_attr(native_ref, "AXIdentifier")
        position = _ax_attr(native_ref, "AXPosition")
        size = _ax_attr(native_ref, "AXSize")
        enabled = _ax_attr(native_ref, "AXEnabled")

        x, y = 0, 0
        w, h = 0, 0
        if position is not None:
            try:
                ax_point = Cocoa.NSPoint()
                Quartz.AXValueGetValue(position, Quartz.kAXValueTypeCGPoint, ax_point)
                x, y = int(ax_point.x), int(ax_point.y)
            except Exception:
                pass
        if size is not None:
            try:
                ax_size = Cocoa.NSSize()
                Quartz.AXValueGetValue(size, Quartz.kAXValueTypeCGSize, ax_size)
                w, h = int(ax_size.width), int(ax_size.height)
            except Exception:
                pass

        return UIElement(
            role=normalized_role,
            title=_clean_text(str(title)) if title else None,
            label=_clean_text(str(desc)) if desc else None,
            value=_clean_text(str(value)) if value else None,
            identifier=str(identifier) if identifier else None,
            x=x, y=y, width=w, height=h,
            enabled=bool(enabled) if enabled is not None else True,
            visible=True,
            _native_ref=native_ref,
        )

    def _search_element(self, ax_ref: object, locator: LocatorStrategy) -> UIElement | None:
        """Search the accessibility tree for a matching element."""
        results: list[UIElement] = []
        self._search_elements(ax_ref, locator, results, max_depth=15)
        if not results:
            return None
        idx = locator.index if locator.index is not None else 0
        if idx < len(results):
            return results[idx]
        return None

    def _search_elements(
        self, ax_ref: object, locator: LocatorStrategy,
        results: list[UIElement], max_depth: int = 15, depth: int = 0
    ) -> None:
        """Recursively search for elements matching the locator."""
        if depth > max_depth:
            return

        element = self._wrap_native_element(ax_ref)

        if self._matches_locator(element, locator):
            results.append(element)

        # Recurse into children
        children = _ax_attr(ax_ref, "AXChildren")
        if children:
            for child in children:
                self._search_elements(child, locator, results, max_depth, depth + 1)

    def _matches_locator(self, element: UIElement, locator: LocatorStrategy) -> bool:
        """Check if a UIElement matches the given locator."""
        if locator.type == LocatorType.ACCESSIBILITY_ID:
            return element.identifier == locator.value

        elif locator.type == LocatorType.ROLE_AND_TITLE:
            role_match = locator.role is None or element.role == locator.role
            # Match against title, value, or label
            value_match = (
                element.title == locator.value
                or element.value == locator.value
                or element.label == locator.value
            )
            return role_match and value_match

        elif locator.type == LocatorType.ROLE_AND_LABEL:
            role_match = locator.role is None or element.role == locator.role
            return role_match and element.label == locator.value

        elif locator.type == LocatorType.TEXT_CONTENT:
            return (
                locator.value in (element.title or "")
                or locator.value in (element.value or "")
                or locator.value in (element.label or "")
            )

        elif locator.type == LocatorType.PATH:
            return element.path == locator.value

        elif locator.type == LocatorType.COORDINATE:
            # Coordinate matching: check if element contains the point
            parts = locator.value.split(",")
            if len(parts) == 2:
                px, py = int(parts[0].strip()), int(parts[1].strip())
                return (
                    element.x <= px <= element.x + element.width
                    and element.y <= py <= element.y + element.height
                )
            return False

        return False

    def _build_tree(self, ax_ref: object, depth: int, max_depth: int) -> dict:
        """Build a dict representation of the accessibility tree."""
        element = self._wrap_native_element(ax_ref)
        node: dict[str, Any] = {
            "role": element.role,
            "title": element.title,
            "label": element.label,
            "value": element.value,
            "identifier": element.identifier,
            "bounds": element.bounds,
        }

        if depth < max_depth:
            children = _ax_attr(ax_ref, "AXChildren")
            if children:
                node["children"] = [
                    self._build_tree(child, depth + 1, max_depth)
                    for child in children
                ]

        return node

    def _cg_click(self, point: tuple[int, int]) -> None:
        """Perform a click via CGEvents at the given coordinates."""
        cx, cy = point
        cg_point = Quartz.CGPointMake(cx, cy)
        event_down = Quartz.CGEventCreateMouseEvent(
            None, Quartz.kCGEventLeftMouseDown, cg_point, Quartz.kCGMouseButtonLeft
        )
        event_up = Quartz.CGEventCreateMouseEvent(
            None, Quartz.kCGEventLeftMouseUp, cg_point, Quartz.kCGMouseButtonLeft
        )
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_down)
        time.sleep(0.05)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_up)

    def _type_char(self, char: str) -> None:
        """Type a single character via CGEvents."""
        # Use CGEventKeyboardSetUnicodeString for reliable character input
        event_down = Quartz.CGEventCreateKeyboardEvent(None, 0, True)
        event_up = Quartz.CGEventCreateKeyboardEvent(None, 0, False)
        Quartz.CGEventKeyboardSetUnicodeString(event_down, len(char), char)
        Quartz.CGEventKeyboardSetUnicodeString(event_up, len(char), char)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_down)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_up)
