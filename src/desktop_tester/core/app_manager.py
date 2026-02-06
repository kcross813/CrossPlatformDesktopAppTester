"""Application lifecycle management."""

from __future__ import annotations

from typing import Optional

from desktop_tester.core.platform_base import PlatformBackend
from desktop_tester.models.project import TargetApp


class AppManager:
    """Manages launching, attaching to, and tracking the target application."""

    def __init__(self, backend: PlatformBackend):
        self._backend = backend
        self._app_ref: Optional[object] = None
        self._target: Optional[TargetApp] = None

    @property
    def app_ref(self) -> object | None:
        return self._app_ref

    @property
    def is_connected(self) -> bool:
        return self._app_ref is not None

    def launch(self, target: TargetApp) -> object:
        """Launch the target application."""
        identifier = target.bundle_id or target.path or target.name
        if not identifier:
            raise ValueError("No application identifier configured in target_app")

        self._target = target
        self._app_ref = self._backend.launch_application(
            identifier, target.launch_args or None
        )
        return self._app_ref

    def attach(self, identifier: str) -> object:
        """Attach to an already-running application."""
        self._app_ref = self._backend.attach_to_application(identifier)
        return self._app_ref

    def launch_or_attach(self, target: TargetApp) -> object:
        """Try to attach first; launch if not running."""
        identifier = target.bundle_id or target.name or target.path
        if not identifier:
            raise ValueError("No application identifier configured in target_app")

        try:
            return self.attach(identifier)
        except Exception:
            return self.launch(target)

    def disconnect(self) -> None:
        """Disconnect from the current application."""
        self._app_ref = None
        self._target = None
