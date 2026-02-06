"""Post-processes recorded steps for cleaner, more maintainable tests."""

from __future__ import annotations

from desktop_tester.models.step import ActionType, Step


class StepOptimizer:
    """Merges and deduplicates raw recorded steps."""

    def optimize(self, steps: list[Step]) -> list[Step]:
        """Run all optimization passes on the step list."""
        steps = self._merge_keystrokes(steps)
        steps = self._remove_redundant_double_clicks(steps)
        steps = self._reassign_ids(steps)
        return steps

    def _merge_keystrokes(self, steps: list[Step]) -> list[Step]:
        """Merge consecutive single-character TYPE_TEXT steps into one."""
        merged: list[Step] = []
        buffer: list[Step] = []

        for step in steps:
            if (step.action == ActionType.TYPE_TEXT
                    and step.text is not None
                    and len(step.text) == 1
                    and step.keys is None):
                buffer.append(step)
            else:
                if buffer:
                    merged.append(self._collapse_type_buffer(buffer))
                    buffer = []
                merged.append(step)

        if buffer:
            merged.append(self._collapse_type_buffer(buffer))

        return merged

    def _collapse_type_buffer(self, buffer: list[Step]) -> Step:
        """Collapse a buffer of single-char TYPE_TEXT steps into one."""
        text = "".join(s.text for s in buffer if s.text)
        return Step(
            id="",
            action=ActionType.TYPE_TEXT,
            description=f'Type "{text}"',
            target=buffer[0].target,
            text=text,
        )

    def _remove_redundant_double_clicks(self, steps: list[Step]) -> list[Step]:
        """If a double-click follows a click at the same target, remove the click."""
        if len(steps) < 2:
            return steps

        result: list[Step] = []
        skip_next = False

        for i in range(len(steps)):
            if skip_next:
                skip_next = False
                continue

            if (i + 1 < len(steps)
                    and steps[i].action == ActionType.CLICK
                    and steps[i + 1].action == ActionType.DOUBLE_CLICK
                    and steps[i].target == steps[i + 1].target):
                # Skip the single click, keep the double click
                skip_next = False  # Don't skip the double click
                continue
            else:
                result.append(steps[i])

        return result

    def _reassign_ids(self, steps: list[Step]) -> list[Step]:
        """Reassign sequential IDs after optimization."""
        for i, step in enumerate(steps, start=1):
            step.id = f"step_{i}"
        return steps
