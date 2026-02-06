"""HTML report generator using Jinja2 templates."""

from __future__ import annotations

import base64
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

from desktop_tester.models.step import RunSummary


class HTMLReporter:
    """Generates self-contained HTML reports."""

    def __init__(self):
        self._env = Environment(
            loader=PackageLoader("desktop_tester", "reporter/templates"),
            autoescape=select_autoescape(["html"]),
        )
        self._env.filters["basename"] = lambda path: Path(path).name if path else ""

    def generate(self, summary: RunSummary, output_path: Path) -> Path:
        """Generate a self-contained HTML report."""
        template = self._env.get_template("report.html.j2")

        # Encode screenshots as base64 for embedding
        screenshot_data: dict[str, str] = {}
        for test_result in summary.test_results:
            for step_result in test_result.step_results:
                if step_result.screenshot_path:
                    screenshot_data[step_result.step_id] = self._encode_screenshot(
                        step_result.screenshot_path
                    )

        html = template.render(
            summary=summary,
            screenshots=screenshot_data,
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html)
        return output_path

    def _encode_screenshot(self, path: str) -> str:
        """Encode a screenshot file as a base64 data URI."""
        try:
            data = Path(path).read_bytes()
            return f"data:image/png;base64,{base64.b64encode(data).decode()}"
        except Exception:
            return ""
