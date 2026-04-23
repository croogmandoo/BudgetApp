"""Placeholder tests for ``apps.finances``."""

from __future__ import annotations


def test_finances_app_imports() -> None:
    """Sanity-check that the finance models import cleanly."""
    from apps.finances import models  # noqa: F401
