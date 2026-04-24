"""HTTP views for ``apps.finances``.

Scope: account / category / transaction / split CRUD, rule management.
All viewsets are scoped to the authenticated user's household and require
TOTP enrolment (via ``IsTOTPVerifiedHouseholdMember``).
"""

from __future__ import annotations

import uuid
from typing import cast

from rest_framework import viewsets
from rest_framework.request import Request

from apps.accounts.models import User
from apps.core.permissions import IsTOTPVerifiedHouseholdMember
from apps.finances.models import Account, Category, Rule, Transaction
from apps.finances.serializers import (
    AccountSerializer,
    CategorySerializer,
    RuleSerializer,
    TransactionSerializer,
)


def _household_id(request: Request) -> uuid.UUID:
    """Return the household UUID for the authenticated user.

    The ``IsTOTPVerifiedHouseholdMember`` permission guarantees both that the
    user is authenticated and that ``household_id`` is non-null before any
    view method runs.
    """
    user = cast(User, request.user)
    return cast(uuid.UUID, user.household_id)


class AccountViewSet(viewsets.ModelViewSet):  # type: ignore[type-arg]
    serializer_class = AccountSerializer
    permission_classes = [IsTOTPVerifiedHouseholdMember]

    def get_queryset(self):  # type: ignore[override]
        return Account.objects.filter(household_id=_household_id(self.request)).order_by("name")

    def perform_create(self, serializer):  # type: ignore[override]
        user = cast(User, self.request.user)
        serializer.save(household=user.household)


class CategoryViewSet(viewsets.ModelViewSet):  # type: ignore[type-arg]
    serializer_class = CategorySerializer
    permission_classes = [IsTOTPVerifiedHouseholdMember]

    def get_queryset(self):  # type: ignore[override]
        return Category.objects.filter(household_id=_household_id(self.request)).order_by("name")

    def perform_create(self, serializer):  # type: ignore[override]
        user = cast(User, self.request.user)
        serializer.save(household=user.household)


class TransactionViewSet(viewsets.ModelViewSet):  # type: ignore[type-arg]
    serializer_class = TransactionSerializer
    permission_classes = [IsTOTPVerifiedHouseholdMember]

    def get_queryset(self):  # type: ignore[override]
        return (
            Transaction.objects.filter(account__household_id=_household_id(self.request))
            .select_related("account", "category")
            .prefetch_related("splits")
            .order_by("-date", "-created_at")
        )


class RuleViewSet(viewsets.ModelViewSet):  # type: ignore[type-arg]
    serializer_class = RuleSerializer
    permission_classes = [IsTOTPVerifiedHouseholdMember]

    def get_queryset(self):  # type: ignore[override]
        return Rule.objects.filter(household_id=_household_id(self.request)).order_by("priority")

    def perform_create(self, serializer):  # type: ignore[override]
        user = cast(User, self.request.user)
        serializer.save(household=user.household)
