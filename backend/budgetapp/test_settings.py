"""Pytest settings module.

Imported by pytest-django (via pyproject.toml's DJANGO_SETTINGS_MODULE)
before the production settings module is loaded. We set the minimum
environment required by ``settings.py`` so the test suite runs
without operators having to populate a ``.env.test`` file, then hand
off to the real settings via ``from .settings import *``.

Production-mode assertions (APP_MASTER_KEY / DATABASE_URL / SECRET_KEY
required outside DEBUG) live in ``settings.py`` and are covered by
dedicated tests added alongside the auth implementation.
"""

from __future__ import annotations

import os

os.environ.setdefault("DJANGO_DEBUG", "1")

# Importing with wildcard is the canonical pattern for override settings
# modules; the surface is Django's and re-exporting every name is the point.
from .settings import *  # noqa: F403
