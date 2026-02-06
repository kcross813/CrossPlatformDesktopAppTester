"""YAML serialization and deserialization for test files and project config."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from desktop_tester.models.project import ProjectConfig
from desktop_tester.models.step import ActionType, Step


def load_yaml(path: Path) -> dict[str, Any]:
    """Load and parse a YAML file."""
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}


def save_yaml(path: Path, data: dict[str, Any]) -> None:
    """Write data to a YAML file with clean formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def load_project(path: Path) -> ProjectConfig:
    """Load a project.yaml file into a ProjectConfig."""
    data = load_yaml(path)
    return ProjectConfig.from_dict(data)


def save_project(path: Path, config: ProjectConfig) -> None:
    """Save a ProjectConfig to a project.yaml file."""
    save_yaml(path, config.to_dict())


def dict_to_step(data: dict[str, Any]) -> Step:
    """Convert a YAML step dict to a Step model."""
    return Step(
        id=data.get("id", ""),
        action=ActionType(data["action"]),
        description=data.get("description", ""),
        target=data.get("target"),
        text=data.get("text"),
        keys=data.get("keys"),
        duration=data.get("duration"),
        title=data.get("title"),
        assertion=data.get("assertion"),
        script=data.get("script"),
        screenshot=data.get("screenshot", False),
        timeout=data.get("timeout"),
        continue_on_failure=data.get("continue_on_failure", False),
    )


def step_to_dict(step: Step) -> dict[str, Any]:
    """Convert a Step model to a dict for YAML serialization."""
    d: dict[str, Any] = {
        "id": step.id,
        "action": step.action.value,
    }
    if step.description:
        d["description"] = step.description
    if step.target is not None:
        d["target"] = step.target
    if step.text is not None:
        d["text"] = step.text
    if step.keys is not None:
        d["keys"] = step.keys
    if step.duration is not None:
        d["duration"] = step.duration
    if step.title is not None:
        d["title"] = step.title
    if step.assertion is not None:
        d["assertion"] = step.assertion
    if step.script is not None:
        d["script"] = step.script
    if step.screenshot:
        d["screenshot"] = step.screenshot
    if step.timeout is not None:
        d["timeout"] = step.timeout
    if step.continue_on_failure:
        d["continue_on_failure"] = step.continue_on_failure
    return d


def load_test_file(path: Path) -> dict[str, Any]:
    """Load a test YAML file and parse its steps into Step objects.

    Returns the raw dict with 'setup', 'steps', and 'teardown' keys
    containing lists of Step objects.
    """
    data = load_yaml(path)
    result: dict[str, Any] = {
        "name": data.get("name", path.stem),
        "description": data.get("description", ""),
        "tags": data.get("tags", []),
    }

    for section in ("setup", "steps", "teardown"):
        raw_steps = data.get(section, [])
        result[section] = [dict_to_step(s) for s in raw_steps]

    return result


def save_test_file(path: Path, name: str, steps: list[Step],
                   setup: list[Step] | None = None,
                   teardown: list[Step] | None = None,
                   description: str = "",
                   tags: list[str] | None = None) -> None:
    """Save steps to a YAML test file."""
    data: dict[str, Any] = {"name": name}
    if description:
        data["description"] = description
    if tags:
        data["tags"] = tags
    if setup:
        data["setup"] = [step_to_dict(s) for s in setup]
    data["steps"] = [step_to_dict(s) for s in steps]
    if teardown:
        data["teardown"] = [step_to_dict(s) for s in teardown]

    save_yaml(path, data)
