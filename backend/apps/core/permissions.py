"""Shared DRF permission classes for BudgetApp.

These are cross-cutting guards reused across all domain apps.
"""

from __future__ import annotations

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request


class IsTOTPVerifiedHouseholdMember(IsAuthenticated):
    """Require a fully-authenticated household member with TOTP enrolled.

    Combines three checks:
    1. The request is authenticated (session or token).
    2. The user is assigned to a household.
    3. The user has completed TOTP enrolment (``totp_enforced_at`` is set).

    This permission is applied to every domain-API viewset so that partially-
    enrolled users (who have a session but have not yet confirmed their TOTP
    device) cannot access financial data.
    """

    def has_permission(self, request: Request, view: object) -> bool:
        if not super().has_permission(request, view):
            return False
        user = request.user
        return bool(getattr(user, "household_id", None) and getattr(user, "totp_enforced_at", None))
