"""Converts raw OS events into test Step models."""

from __future__ import annotations

from desktop_tester.models.element_ref import UIElement
from desktop_tester.models.step import ActionType, Step
from desktop_tester.recorder.event_listener import RawEvent, RawEventType


class EventToStep:
    """Maps a raw input event + resolved UI element to a Step."""

    def __init__(self):
        self._step_counter = 0

    def reset(self) -> None:
        self._step_counter = 0

    def convert(
        self, event: RawEvent, element: UIElement | None, locator_dict: dict | None
    ) -> Step | None:
        """Convert a raw event into a Step.

        Returns None if the event should be ignored.
        """
        self._step_counter += 1
        step_id = f"step_{self._step_counter}"

        if event.event_type == RawEventType.MOUSE_CLICK:
            return self._make_click_step(step_id, event, element, locator_dict)

        elif event.event_type == RawEventType.MOUSE_DOUBLE_CLICK:
            return self._make_double_click_step(step_id, event, element, locator_dict)

        elif event.event_type == RawEventType.MOUSE_RIGHT_CLICK:
            return self._make_right_click_step(step_id, event, element, locator_dict)

        elif event.event_type == RawEventType.KEY_PRESS:
            return self._make_key_step(step_id, event, element, locator_dict)

        return None

    def _make_click_step(
        self, step_id: str, event: RawEvent,
        element: UIElement | None, locator_dict: dict | None
    ) -> Step:
        # Dock item clicks should become launch_app steps
        if element is not None and element.role == "dockitem":
            app_name = element.title or element.label or "Unknown"
            return Step(
                id=step_id,
                action=ActionType.LAUNCH_APP,
                description=f"Launch {app_name}",
            )

        desc = self._describe_element("Click", element)
        return Step(
            id=step_id,
            action=ActionType.CLICK,
            description=desc,
            target=locator_dict,
        )

    def _make_double_click_step(
        self, step_id: str, event: RawEvent,
        element: UIElement | None, locator_dict: dict | None
    ) -> Step:
        desc = self._describe_element("Double-click", element)
        return Step(
            id=step_id,
            action=ActionType.DOUBLE_CLICK,
            description=desc,
            target=locator_dict,
        )

    def _make_right_click_step(
        self, step_id: str, event: RawEvent,
        element: UIElement | None, locator_dict: dict | None
    ) -> Step:
        desc = self._describe_element("Right-click", element)
        return Step(
            id=step_id,
            action=ActionType.RIGHT_CLICK,
            description=desc,
            target=locator_dict,
        )

    def _make_key_step(
        self, step_id: str, event: RawEvent,
        element: UIElement | None, locator_dict: dict | None
    ) -> Step:
        element_suffix = self._element_suffix(element)
        if event.modifiers:
            # Key combo (e.g., Cmd+C)
            keys = list(event.modifiers) + [event.key]
            desc = f'Key combo: {"+".join(keys)}{element_suffix}'
            return Step(
                id=step_id,
                action=ActionType.KEY_COMBO,
                description=desc,
                target=locator_dict,
                keys=keys,
            )
        else:
            # Single character typed
            desc = f'Type "{event.key}"{element_suffix}'
            return Step(
                id=step_id,
                action=ActionType.TYPE_TEXT,
                description=desc,
                target=locator_dict,
                text=event.key,
            )

    def _describe_element(self, verb: str, element: UIElement | None) -> str:
        """Generate a human-readable description of an action on an element."""
        if element is None:
            return verb

        name = element.title or element.label or element.value or element.identifier
        if name:
            return f'{verb} "{name}" ({element.role})'
        return f"{verb} {element.role}"

    def _element_suffix(self, element: UIElement | None) -> str:
        """Generate an ' in "Name" (role)' suffix for an element, or empty string."""
        if element is None:
            return ""

        name = element.title or element.label or element.identifier
        if name:
            return f' in "{name}" ({element.role})'
        if element.role:
            return f" in {element.role}"
        return ""
