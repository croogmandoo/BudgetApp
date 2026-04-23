"""Root URL configuration for BudgetApp.

Routes:
    - ``/admin/``             Django admin (staff only).
    - ``/api/v1/``            Versioned public REST API (see ``api_urls``).
    - ``/api/schema/``        OpenAPI 3.1 schema (drf-spectacular).
    - ``/api/docs/``          Swagger UI backed by the schema above.
    - ``/healthz``            Liveness probe (no auth, no DB).

The SPA under ``../frontend/`` and external integrators share the same
``/api/v1/`` surface (see SPEC §5.1).
"""

from __future__ import annotations

from django.contrib import admin
from django.http import HttpRequest, HttpResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


def healthz(_request: HttpRequest) -> HttpResponse:
    """Cheap liveness probe used by Docker healthcheck and Compose."""
    return HttpResponse("ok", content_type="text/plain")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("budgetapp.api_urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("healthz", healthz, name="healthz"),
]
