"""Aggregator for the versioned ``/api/v1/`` surface.

Each domain app owns its own URL module (``apps.<name>.api_urls``). This file
only wires them together. Adding a new app means:

    1. Drop an ``api_urls.py`` into the app exposing ``urlpatterns``.
    2. Register its prefix here.

Keeping the prefixes shallow (``/api/v1/<noun>/``) keeps the OpenAPI schema
readable and matches SPEC §5.1.
"""

from __future__ import annotations

from django.urls import include, path

urlpatterns = [
    path("accounts/", include("apps.accounts.api_urls")),
    path("core/", include("apps.core.api_urls")),
    path("finances/", include("apps.finances.api_urls")),
    path("budgets/", include("apps.budgets.api_urls")),
    path("bills/", include("apps.bills.api_urls")),
    path("projects/", include("apps.projects.api_urls")),
    path("maintenance/", include("apps.maintenance.api_urls")),
    path("notifications/", include("apps.notifications.api_urls")),
]
