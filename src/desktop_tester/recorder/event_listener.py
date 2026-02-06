"""OS-level event hooks for recording mouse and keyboard actions."""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field
from enum import Enum

from PySide6.QtCore import QObject, Signal


class RawEventType(Enum):
    MOUSE_CLICK = "mouse_click"
    MOUSE_DOUBLE_CLICK = "mouse_double_click"
    MOUSE_RIGHT_CLICK = "mouse_right_click"
    KEY_PRESS = "key_press"
    KEY_RELEASE = "key_release"


@dataclass
class RawEvent:
    """A raw OS-level input event."""

    event_type: RawEventType
    timestamp: float
    x: int = 0
    y: int = 0
    button: str = ""
    key: str = ""
    modifiers: list[str] = field(default_factory=list)


class EventListener(QObject):
    """Listens for global mouse and keyboard events.

    On macOS, uses NSEvent global monitors which run on the main thread
    within Qt's event loop — no background threads needed.
    """

    event_captured = Signal(object)  # Emits RawEvent

    def __init__(self):
        super().__init__()
        self._active = False
        self._mouse_monitor = None
        self._key_monitor = None
        self._flags_monitor = None
        self._pressed_modifiers: set[str] = set()

    @property
    def is_active(self) -> bool:
        return self._active

    def start(self) -> None:
        """Start listening for events."""
        if sys.platform != "darwin":
            return
        import Cocoa

        self._active = True
        self._pressed_modifiers.clear()

        # Monitor mouse clicks in other applications
        mouse_mask = (
            Cocoa.NSEventMaskLeftMouseDown
            | Cocoa.NSEventMaskRightMouseDown
        )
        self._mouse_monitor = (
            Cocoa.NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
                mouse_mask, self._on_mouse_event
            )
        )

        # Monitor key presses in other applications
        key_mask = Cocoa.NSEventMaskKeyDown
        self._key_monitor = (
            Cocoa.NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
                key_mask, self._on_key_event
            )
        )

        # Monitor modifier flag changes for tracking held modifiers
        flags_mask = Cocoa.NSEventMaskFlagsChanged
        self._flags_monitor = (
            Cocoa.NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
                flags_mask, self._on_flags_changed
            )
        )

    def stop(self) -> None:
        """Stop listening for events."""
        self._active = False
        if sys.platform != "darwin":
            return
        import Cocoa

        if self._mouse_monitor is not None:
            Cocoa.NSEvent.removeMonitor_(self._mouse_monitor)
            self._mouse_monitor = None
        if self._key_monitor is not None:
            Cocoa.NSEvent.removeMonitor_(self._key_monitor)
            self._key_monitor = None
        if self._flags_monitor is not None:
            Cocoa.NSEvent.removeMonitor_(self._flags_monitor)
            self._flags_monitor = None

    # --- macOS NSEvent callbacks (run on main thread) ---

    def _on_mouse_event(self, ns_event) -> None:
        if not self._active:
            return
        import Cocoa

        # Convert Cocoa coordinates (bottom-left origin) to screen coordinates (top-left)
        loc = Cocoa.NSEvent.mouseLocation()
        screen = Cocoa.NSScreen.mainScreen()
        if screen is None:
            return
        screen_height = screen.frame().size.height
        ix = int(loc.x)
        iy = int(screen_height - loc.y)
        now = time.time()

        event_type_ns = ns_event.type()

        if event_type_ns == Cocoa.NSEventTypeRightMouseDown:
            self.event_captured.emit(RawEvent(
                event_type=RawEventType.MOUSE_RIGHT_CLICK,
                timestamp=now,
                x=ix, y=iy,
                button="right",
            ))
            return

        if event_type_ns == Cocoa.NSEventTypeLeftMouseDown:
            click_count = ns_event.clickCount()
            if click_count >= 2:
                self.event_captured.emit(RawEvent(
                    event_type=RawEventType.MOUSE_DOUBLE_CLICK,
                    timestamp=now,
                    x=ix, y=iy,
                    button="left",
                ))
            else:
                self.event_captured.emit(RawEvent(
                    event_type=RawEventType.MOUSE_CLICK,
                    timestamp=now,
                    x=ix, y=iy,
                    button="left",
                ))

    def _on_key_event(self, ns_event) -> None:
        if not self._active:
            return
        import Cocoa

        key_str = self._key_from_nsevent(ns_event)
        if not key_str:
            return

        # Skip pure modifier presses (handled by _on_flags_changed)
        if key_str in ("cmd", "shift", "alt", "ctrl"):
            return

        self.event_captured.emit(RawEvent(
            event_type=RawEventType.KEY_PRESS,
            timestamp=time.time(),
            key=key_str,
            modifiers=list(self._pressed_modifiers),
        ))

    def _on_flags_changed(self, ns_event) -> None:
        """Track modifier key state."""
        if not self._active:
            return
        import Cocoa

        flags = ns_event.modifierFlags()
        new_mods: set[str] = set()
        if flags & Cocoa.NSEventModifierFlagCommand:
            new_mods.add("cmd")
        if flags & Cocoa.NSEventModifierFlagShift:
            new_mods.add("shift")
        if flags & Cocoa.NSEventModifierFlagOption:
            new_mods.add("alt")
        if flags & Cocoa.NSEventModifierFlagControl:
            new_mods.add("ctrl")
        self._pressed_modifiers = new_mods

    def _key_from_nsevent(self, ns_event) -> str:
        """Extract a normalized key name from an NSEvent."""
        # Try to get the character
        try:
            chars = ns_event.charactersIgnoringModifiers()
            if chars and len(chars) == 1:
                ch = chars[0]
                # Printable character
                if ch.isprintable() and ord(ch) >= 32:
                    return ch.lower() if ch.isalpha() else ch
        except Exception:
            pass

        # Fall back to keyCode mapping
        key_code = ns_event.keyCode()
        return _KEYCODE_MAP.get(key_code, "")


# macOS virtual keyCode → normalized key name
_KEYCODE_MAP = {
    0x24: "return",
    0x30: "tab",
    0x31: "space",
    0x33: "backspace",
    0x35: "escape",
    0x7E: "up",
    0x7D: "down",
    0x7B: "left",
    0x7C: "right",
    0x75: "delete",  # forward delete
    0x73: "home",
    0x77: "end",
    0x74: "page_up",
    0x79: "page_down",
    0x7A: "f1",
    0x78: "f2",
    0x63: "f3",
    0x76: "f4",
    0x60: "f5",
    0x61: "f6",
    0x62: "f7",
    0x64: "f8",
    0x65: "f9",
    0x6D: "f10",
    0x67: "f11",
    0x6F: "f12",
}
