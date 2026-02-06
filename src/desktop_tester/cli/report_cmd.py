"""Implementation of the `desktop-tester report` command."""

from __future__ import annotations

import json
from pathlib import Path

import click

from desktop_tester.models.step import RunSummary, StepResult, TestResult


def execute_report(results_json: str, fmt: str, output: str) -> None:
    """Generate a report from a JSON results file."""
    results_path = Path(results_json)
    output_path = Path(output)

    with open(results_path, "r") as f:
        data = json.load(f)

    # Reconstruct RunSummary from JSON
    summary = _json_to_summary(data)

    from desktop_tester.reporter.reporter import ReportGenerator

    generator = ReportGenerator()

    if fmt == "html":
        generator.generate_html(summary, output_path)
    elif fmt == "json":
        generator.generate_json(summary, output_path)

    click.echo(f"Report generated: {output_path}")


def _json_to_summary(data: dict) -> RunSummary:
    """Convert a JSON dict back to a RunSummary."""
    test_results = []
    for tr_data in data.get("test_results", []):
        step_results = [
            StepResult(
                step_id=sr.get("step_id", ""),
                status=sr.get("status", ""),
                duration_ms=sr.get("duration_ms", 0),
                error_message=sr.get("error_message"),
                screenshot_path=sr.get("screenshot_path"),
                actual_value=sr.get("actual_value"),
                timestamp=sr.get("timestamp", ""),
            )
            for sr in tr_data.get("step_results", [])
        ]
        test_results.append(TestResult(
            test_name=tr_data.get("test_name", ""),
            test_file=tr_data.get("test_file", ""),
            status=tr_data.get("status", ""),
            duration_ms=tr_data.get("duration_ms", 0),
            step_results=step_results,
            started_at=tr_data.get("started_at", ""),
            finished_at=tr_data.get("finished_at", ""),
        ))

    return RunSummary(
        total=data.get("total", 0),
        passed=data.get("passed", 0),
        failed=data.get("failed", 0),
        errors=data.get("errors", 0),
        skipped=data.get("skipped", 0),
        duration_ms=data.get("duration_ms", 0),
        test_results=test_results,
        started_at=data.get("started_at", ""),
        finished_at=data.get("finished_at", ""),
    )
