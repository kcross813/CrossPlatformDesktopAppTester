"""Report generation facade."""

from __future__ import annotations

from pathlib import Path

from desktop_tester.models.step import RunSummary
from desktop_tester.reporter.html_reporter import HTMLReporter
from desktop_tester.reporter.json_reporter import JSONReporter


class ReportGenerator:
    """Facade for generating reports in various formats."""

    def __init__(self):
        self._html = HTMLReporter()
        self._json = JSONReporter()

    def generate_html(self, summary: RunSummary, output_path: Path) -> Path:
        return self._html.generate(summary, output_path)

    def generate_json(self, summary: RunSummary, output_path: Path) -> Path:
        return self._json.generate(summary, output_path)
