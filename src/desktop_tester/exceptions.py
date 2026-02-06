"""Custom exception hierarchy for DesktopTester."""


class DesktopTesterError(Exception):
    """Base exception for all DesktopTester errors."""


class ElementNotFoundError(DesktopTesterError):
    """Raised when a UI element cannot be found within the timeout."""

    def __init__(self, locator, timeout: float = 0):
        self.locator = locator
        self.timeout = timeout
        super().__init__(f"Element not found: {locator} (timeout: {timeout}s)")


class ElementTimeoutError(DesktopTesterError):
    """Raised when waiting for an element condition times out."""


class ApplicationNotFoundError(DesktopTesterError):
    """Raised when the target application cannot be found or launched."""


class ApplicationNotRunningError(DesktopTesterError):
    """Raised when trying to interact with an app that is not running."""


class AssertionError(DesktopTesterError):
    """Raised when a test assertion fails."""

    def __init__(self, message: str, expected=None, actual=None):
        self.expected = expected
        self.actual = actual
        super().__init__(message)


class RecordingError(DesktopTesterError):
    """Raised when recording encounters an error."""


class ProjectError(DesktopTesterError):
    """Raised for project configuration errors."""


class PlatformNotSupportedError(DesktopTesterError):
    """Raised when running on an unsupported platform."""


class AccessibilityPermissionError(DesktopTesterError):
    """Raised when accessibility permissions are not granted."""

    def __init__(self):
        super().__init__(
            "Accessibility permissions not granted. "
            "Please enable in System Settings > Privacy & Security > Accessibility."
        )
