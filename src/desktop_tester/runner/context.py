"""RunContext - holds state for a test execution run."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from desktop_tester.models.project import ProjectConfig


class RunContext:
    """Execution context for a test run, holding paths, settings, and state."""

    def __init__(self, project_dir: Path, config: ProjectConfig, test_file: Path):
        self.project_dir = project_dir
        self.config = config
        self.test_file = test_file
        self.screenshot_dir = project_dir / config.screenshots_dir
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)

    @property
    def screenshot_on_failure(self) -> bool:
        return self.config.settings.screenshot_on_failure

    @property
    def screenshot_on_step(self) -> bool:
        return self.config.settings.screenshot_on_step

    @property
    def default_timeout(self) -> float:
        return self.config.settings.default_timeout

    @property
    def slow_mode_delay(self) -> float:
        return self.config.settings.slow_mode_delay

    def save_screenshot(self, step_id: str, png_bytes: bytes) -> Path:
        """Save a screenshot and return the file path."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.test_file.stem}_{step_id}_{timestamp}.png"
        path = self.screenshot_dir / filename
        path.write_bytes(png_bytes)
        return path
