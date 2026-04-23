"""Placeholder tests for ``apps.notifications``."""

from __future__ import annotations


def test_notifications_app_imports() -> None:
    """Sanity-check that the notification models import cleanly."""
    from apps.notifications import models  # noqa: F401
