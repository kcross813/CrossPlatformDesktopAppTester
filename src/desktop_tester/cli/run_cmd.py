"""Implementation of the `desktop-tester run` command."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import click

from desktop_tester.models.serialization import load_project, load_yaml


def execute_run(
    project_dir: str,
    test_files: tuple[str, ...],
    tags: tuple[str, ...],
    report_format: str,
    output_dir: str | None,
    timeout: float,
    slow_mode: float,
    verbose: bool,
) -> int:
    """Execute tests from the CLI. Returns exit code (0=pass, 1=fail, 2=error)."""
    project_path = Path(project_dir)
    config_path = project_path / "project.yaml"

    if not config_path.exists():
        click.echo(f"Error: No project.yaml found in {project_path}", err=True)
        return 2

    config = load_project(config_path)

    # Override settings from CLI
    if slow_mode > 0:
        config.settings.slow_mode_delay = slow_mode

    # Initialize the automation engine
    try:
        from desktop_tester.core import get_platform_backend
        from desktop_tester.core.engine import AutomationEngine

        backend = get_platform_backend()
        engine = AutomationEngine(backend)
    except Exception as e:
        click.echo(f"Error initializing automation engine: {e}", err=True)
        return 2

    # Discover test files
    tests_dir = project_path / config.tests_dir
    if test_files:
        paths = []
        for t in test_files:
            p = tests_dir / t if not Path(t).is_absolute() else Path(t)
            if not p.suffix:
                p = p.with_suffix(".yaml")
            if p.exists():
                paths.append(p)
            else:
                click.echo(f"Warning: Test file not found: {p}", err=True)
    else:
        paths = sorted(tests_dir.glob("*.yaml"))

    # Filter by tags if specified
    if tags:
        filtered = []
        for p in paths:
            data = load_yaml(p)
            file_tags = set(data.get("tags", []))
            if file_tags & set(tags):
                filtered.append(p)
        paths = filtered

    if not paths:
        click.echo("No test files found to run.", err=True)
        return 2

    click.echo(f"\n  DesktopTester v{config.version}")
    click.echo(f"  Project: {config.name}")
    click.echo(f"  Tests: {len(paths)}")
    click.echo(f"  {'=' * 50}\n")

    # Create runner and run
    from desktop_tester.runner.runner import TestRunner

    runner = TestRunner(engine, project_path, config)

    # Connect verbose output
    if verbose:
        runner.test_started.connect(lambda name: click.echo(f"  Running: {name}"))
        runner.step_completed.connect(
            lambda r: click.echo(
                f"    {r.step_id}: {r.status.upper()} ({r.duration_ms:.0f}ms)"
                + (f" - {r.error_message}" if r.error_message else "")
            )
        )

    runner.test_completed.connect(
        lambda r: click.echo(
            f"  {'PASS' if r.status == 'passed' else 'FAIL'} "
            f"{r.test_name} ({r.duration_ms:.0f}ms)"
        )
    )

    summary = runner.run_all(paths)
    summary.finished_at = datetime.now().isoformat()

    # Generate reports
    report_dir = Path(output_dir) if output_dir else project_path / config.reports_dir
    report_dir.mkdir(parents=True, exist_ok=True)

    from desktop_tester.reporter.reporter import ReportGenerator

    generator = ReportGenerator()

    if report_format in ("html", "both"):
        html_path = report_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        generator.generate_html(summary, html_path)
        click.echo(f"\n  HTML report: {html_path}")

    if report_format in ("json", "both"):
        json_path = report_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        generator.generate_json(summary, json_path)
        click.echo(f"  JSON report: {json_path}")

    # Print summary
    click.echo(f"\n  {'=' * 50}")
    passed_style = "green" if summary.failed == 0 else "red"
    click.echo(
        f"  Tests: {summary.total} | "
        + click.style(f"Passed: {summary.passed}", fg="green") + " | "
        + click.style(f"Failed: {summary.failed}", fg="red" if summary.failed else "green") + " | "
        + f"Errors: {summary.errors}"
    )
    click.echo(f"  Duration: {summary.duration_ms:.0f}ms")
    click.echo(f"  {'=' * 50}\n")

    if summary.failed > 0 or summary.errors > 0:
        return 1
    return 0
