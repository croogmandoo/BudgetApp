"""URL patterns for ``apps.finances`` mounted under ``/api/v1/finances/``."""

from __future__ import annotations

from django.urls import URLPattern, URLResolver, path
from rest_framework.routers import DefaultRouter

from apps.finances.import_views import ImportConfirmView, ImportPreviewView
from apps.finances.views import (
    AccountViewSet,
    CategoryViewSet,
    ImportProfileViewSet,
    RuleViewSet,
    TransactionViewSet,
)

router = DefaultRouter()
router.register("accounts", AccountViewSet, basename="account")
router.register("categories", CategoryViewSet, basename="category")
router.register("transactions", TransactionViewSet, basename="transaction")
router.register("rules", RuleViewSet, basename="rule")
router.register("import-profiles", ImportProfileViewSet, basename="import-profile")

urlpatterns: list[URLPattern | URLResolver] = [
    *router.urls,
    path("imports/preview/", ImportPreviewView.as_view(), name="import-preview"),
    path("imports/confirm/", ImportConfirmView.as_view(), name="import-confirm"),
]
