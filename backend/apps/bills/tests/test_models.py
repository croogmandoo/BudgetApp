"""Placeholder tests for ``apps.bills``."""

from __future__ import annotations


def test_bills_app_imports() -> None:
    """Sanity-check that the bill models import cleanly."""
    from apps.bills import models  # noqa: F401
