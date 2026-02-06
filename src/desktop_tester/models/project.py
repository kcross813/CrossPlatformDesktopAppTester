"""Project configuration model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class TargetApp:
    """Configuration for the application under test."""

    path: Optional[str] = None
    bundle_id: Optional[str] = None  # macOS
    name: Optional[str] = None
    launch_args: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TargetApp:
        return cls(
            path=data.get("path"),
            bundle_id=data.get("bundle_id"),
            name=data.get("name"),
            launch_args=data.get("launch_args", []),
        )

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {}
        if self.path:
            d["path"] = self.path
        if self.bundle_id:
            d["bundle_id"] = self.bundle_id
        if self.name:
            d["name"] = self.name
        if self.launch_args:
            d["launch_args"] = self.launch_args
        return d


@dataclass
class ProjectSettings:
    """Project-level settings."""

    screenshot_on_failure: bool = True
    screenshot_on_step: bool = False
    default_timeout: float = 5.0
    retry_count: int = 1
    slow_mode_delay: float = 0.0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProjectSettings:
        return cls(
            screenshot_on_failure=data.get("screenshot_on_failure", True),
            screenshot_on_step=data.get("screenshot_on_step", False),
            default_timeout=data.get("default_timeout", 5.0),
            retry_count=data.get("retry_count", 1),
            slow_mode_delay=data.get("slow_mode_delay", 0.0),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "screenshot_on_failure": self.screenshot_on_failure,
            "screenshot_on_step": self.screenshot_on_step,
            "default_timeout": self.default_timeout,
            "retry_count": self.retry_count,
            "slow_mode_delay": self.slow_mode_delay,
        }


@dataclass
class ProjectConfig:
    """Top-level project configuration (project.yaml)."""

    name: str = "Untitled Project"
    version: str = "1.0"
    description: str = ""
    target_app: TargetApp = field(default_factory=TargetApp)
    settings: ProjectSettings = field(default_factory=ProjectSettings)
    tests_dir: str = "tests"
    fixtures_dir: str = "fixtures"
    screenshots_dir: str = "screenshots"
    reports_dir: str = "reports"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProjectConfig:
        directories = data.get("directories", {})
        return cls(
            name=data.get("name", "Untitled Project"),
            version=data.get("version", "1.0"),
            description=data.get("description", ""),
            target_app=TargetApp.from_dict(data.get("target_app", {})),
            settings=ProjectSettings.from_dict(data.get("settings", {})),
            tests_dir=directories.get("tests", "tests"),
            fixtures_dir=directories.get("fixtures", "fixtures"),
            screenshots_dir=directories.get("screenshots", "screenshots"),
            reports_dir=directories.get("reports", "reports"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "target_app": self.target_app.to_dict(),
            "settings": self.settings.to_dict(),
            "directories": {
                "tests": self.tests_dir,
                "fixtures": self.fixtures_dir,
                "screenshots": self.screenshots_dir,
                "reports": self.reports_dir,
            },
        }
