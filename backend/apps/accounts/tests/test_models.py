"""Placeholder tests for ``apps.accounts``."""

from __future__ import annotations


def test_accounts_app_imports() -> None:
    """Sanity-check that the identity models import cleanly."""
    from apps.accounts import models  # noqa: F401
