"""Placeholder tests for ``apps.maintenance``."""

from __future__ import annotations


def test_maintenance_app_imports() -> None:
    """Sanity-check that the maintenance models import cleanly."""
    from apps.maintenance import models  # noqa: F401
