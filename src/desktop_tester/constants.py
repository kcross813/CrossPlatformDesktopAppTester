"""App-wide constants and defaults."""

from enum import Enum

APP_NAME = "DesktopTester"
APP_VERSION = "0.1.0"

DEFAULT_TIMEOUT = 5.0
DEFAULT_RETRY_COUNT = 1
DEFAULT_SLOW_MODE_DELAY = 0.0

PROJECT_CONFIG_FILE = "project.yaml"
DEFAULT_TESTS_DIR = "tests"
DEFAULT_FIXTURES_DIR = "fixtures"
DEFAULT_SCREENSHOTS_DIR = "screenshots"
DEFAULT_REPORTS_DIR = "reports"


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"
