"""RecordingSession orchestrator - ties together event listening, element resolution, and step generation."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from desktop_tester.core.engine import AutomationEngine
from desktop_tester.models.step import Step
from desktop_tester.recorder.element_resolver import ElementResolver
from desktop_tester.recorder.event_listener import EventListener, RawEvent, RawEventType
from desktop_tester.recorder.event_to_step import EventToStep
from desktop_tester.recorder.step_optimizer import StepOptimizer


class RecordingSession(QObject):
    """Orchestrates a recording session.

    Signals:
        step_recorded: Emitted when a new step is captured.
        recording_started: Emitted when recording begins.
        recording_stopped: Emitted when recording ends.
    """

    step_recorded = Signal(object)  # Step
    recording_started = Signal()
    recording_stopped = Signal()

    def __init__(self, engine: AutomationEngine):
        super().__init__()
        self._engine = engine
        self._event_listener = EventListener()
        self._element_resolver = ElementResolver(engine)
        self._event_to_step = EventToStep()
        self._optimizer = StepOptimizer()
        self._steps: list[Step] = []
        self._is_recording = False

        self._event_listener.event_captured.connect(self._on_event)

    @property
    def is_recording(self) -> bool:
        return self._is_recording

    @property
    def steps(self) -> list[Step]:
        return list(self._steps)

    def start(self) -> None:
        """Start recording."""
        self._steps.clear()
        self._event_to_step.reset()
        self._is_recording = True
        self._event_listener.start()
        self.recording_started.emit()

    def stop(self) -> list[Step]:
        """Stop recording and return optimized steps."""
        self._is_recording = False
        self._event_listener.stop()
        self._steps = self._optimizer.optimize(self._steps)
        self.recording_stopped.emit()
        return list(self._steps)

    def _on_event(self, event: RawEvent) -> None:
        """Process a raw event from the event listener.

        NSEvent global monitors already exclude events targeting our own
        application windows, so no own-app filtering is needed.
        """
        if not self._is_recording:
            return

        # Resolve the relevant UI element
        element = None
        locator_dict = None
        if event.event_type in (
            RawEventType.MOUSE_CLICK,
            RawEventType.MOUSE_DOUBLE_CLICK,
            RawEventType.MOUSE_RIGHT_CLICK,
        ):
            element, locator = self._element_resolver.resolve(event.x, event.y)
            if locator:
                locator_dict = locator.to_dict()
        elif event.event_type == RawEventType.KEY_PRESS:
            element, locator = self._element_resolver.resolve_focused()
            if locator:
                locator_dict = locator.to_dict()

        # Convert to step
        step = self._event_to_step.convert(event, element, locator_dict)
        if step is not None:
            self._steps.append(step)
            self.step_recorded.emit(step)
