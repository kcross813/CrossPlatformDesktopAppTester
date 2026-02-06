"""Core automation engine."""

from __future__ import annotations

import sys

from desktop_tester.core.platform_base import PlatformBackend
from desktop_tester.exceptions import PlatformNotSupportedError


def get_platform_backend() -> PlatformBackend:
    """Factory: return the appropriate backend for the current OS."""
    if sys.platform == "darwin":
        from desktop_tester.core.macos_backend import MacOSBackend
        return MacOSBackend()
    elif sys.platform == "win32":
        from desktop_tester.core.windows_backend import WindowsBackend
        return WindowsBackend()
    else:
        raise PlatformNotSupportedError(f"Unsupported platform: {sys.platform}")
