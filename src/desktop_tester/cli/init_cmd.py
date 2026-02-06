"""Implementation of the `desktop-tester init` command."""

from __future__ import annotations

from pathlib import Path

import click

from desktop_tester.models.project import ProjectConfig, TargetApp
from desktop_tester.models.serialization import save_project, save_test_file
from desktop_tester.models.step import ActionType, Step


def execute_init(directory: str, name: str, target: str = "") -> None:
    """Initialize a new DesktopTester project."""
    project_dir = Path(directory)

    if project_dir.exists() and any(project_dir.iterdir()):
        if not click.confirm(f"Directory {project_dir} is not empty. Continue?"):
            return

    # Create config
    config = ProjectConfig(
        name=name,
        target_app=TargetApp(bundle_id=target) if target else TargetApp(),
    )

    # Create directories
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / config.tests_dir).mkdir(exist_ok=True)
    (project_dir / config.fixtures_dir).mkdir(exist_ok=True)
    (project_dir / config.screenshots_dir).mkdir(exist_ok=True)
    (project_dir / config.reports_dir).mkdir(exist_ok=True)

    # Save project config
    save_project(project_dir / "project.yaml", config)

    # Create an example test
    example_steps = [
        Step(
            id="step_1",
            action=ActionType.CLICK,
            description="Click a button",
            target={"type": "role_title", "role": "button", "value": "OK"},
        ),
    ]
    save_test_file(
        project_dir / config.tests_dir / "test_example.yaml",
        name="Example Test",
        steps=example_steps,
        description="An example test to get you started",
        setup=[
            Step(id="setup_1", action=ActionType.LAUNCH_APP, description="Launch app"),
        ],
        teardown=[
            Step(id="teardown_1", action=ActionType.CLOSE_APP, description="Close app"),
        ],
    )

    click.echo(f"\n  Project created: {project_dir}")
    click.echo(f"  Config: {project_dir / 'project.yaml'}")
    click.echo(f"  Tests:  {project_dir / config.tests_dir}")
    click.echo(f"\n  Next steps:")
    click.echo(f"    1. Edit project.yaml to set your target application")
    click.echo(f"    2. Run: desktop-tester gui  (to launch the GUI)")
    click.echo(f"    3. Or:  desktop-tester run {project_dir}  (to run from CLI)\n")
