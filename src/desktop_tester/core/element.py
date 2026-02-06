"""Cross-platform UIElement wrapper used by the automation engine."""

# Re-export from models for backward compatibility and convenience.
# The canonical definition lives in models/element_ref.py.
from desktop_tester.models.element_ref import UIElement

__all__ = ["UIElement"]
