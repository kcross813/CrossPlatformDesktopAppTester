"""JSON report generator."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from desktop_tester.models.step import RunSummary


class JSONReporter:
    """Generates JSON reports from test results."""

    def generate(self, summary: RunSummary, output_path: Path) -> Path:
        """Generate a JSON report file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = asdict(summary)
        output_path.write_text(json.dumps(data, indent=2, default=str))
        return output_path
