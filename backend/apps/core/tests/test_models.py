"""Placeholder tests for ``apps.core``.

Real coverage lands with the first feature that touches these models.
"""

from __future__ import annotations


def test_core_app_imports() -> None:
    """Sanity-check that the models module imports cleanly."""
    from apps.core import models  # noqa: F401
