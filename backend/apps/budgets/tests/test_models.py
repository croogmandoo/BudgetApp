"""Placeholder tests for ``apps.budgets``."""

from __future__ import annotations


def test_budgets_app_imports() -> None:
    """Sanity-check that the budget models import cleanly."""
    from apps.budgets import models  # noqa: F401
