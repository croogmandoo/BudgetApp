"""URL patterns for ``apps.finances`` mounted under ``/api/v1/finances/``."""

from __future__ import annotations

from django.urls import URLPattern, URLResolver
from rest_framework.routers import DefaultRouter

from apps.finances.views import (
    AccountViewSet,
    CategoryViewSet,
    RuleViewSet,
    TransactionViewSet,
)

router = DefaultRouter()
router.register("accounts", AccountViewSet, basename="account")
router.register("categories", CategoryViewSet, basename="category")
router.register("transactions", TransactionViewSet, basename="transaction")
router.register("rules", RuleViewSet, basename="rule")

urlpatterns: list[URLPattern | URLResolver] = router.urls
