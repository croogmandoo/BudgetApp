"""Round-trip tests and constraint coverage for budgeting models."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

import pytest
from django.db import IntegrityError

from apps.accounts.models import Household, User
from apps.budgets.models import BudgetAllocation, BudgetPeriod, BudgetTransfer
from apps.finances.models import Category, CategoryKind


@pytest.fixture
def household(db: None) -> Household:
    return Household.objects.create(name="Test household")


@pytest.fixture
def user(household: Household) -> User:
    return User.objects.create_user(username="ada", password="x" * 24, household=household)


@pytest.fixture
def groceries(household: Household) -> Category:
    return Category.objects.create(household=household, name="Groceries", kind=CategoryKind.EXPENSE)


@pytest.fixture
def dining(household: Household) -> Category:
    return Category.objects.create(household=household, name="Dining", kind=CategoryKind.EXPENSE)


def test_period_uniqueness_per_household_month(household: Household) -> None:
    BudgetPeriod.objects.create(household=household, month=dt.date(2026, 4, 1))
    with pytest.raises(IntegrityError):
        BudgetPeriod.objects.create(household=household, month=dt.date(2026, 4, 1))


def test_allocation_uniqueness_per_period_category(
    household: Household, groceries: Category
) -> None:
    period = BudgetPeriod.objects.create(household=household, month=dt.date(2026, 4, 1))
    BudgetAllocation.objects.create(period=period, category=groceries, amount=Decimal("800"))
    with pytest.raises(IntegrityError):
        BudgetAllocation.objects.create(period=period, category=groceries, amount=Decimal("900"))


def test_budget_transfer_records_who_and_when(
    household: Household, user: User, groceries: Category, dining: Category
) -> None:
    period = BudgetPeriod.objects.create(household=household, month=dt.date(2026, 4, 1))
    transfer = BudgetTransfer.objects.create(
        period=period,
        from_category=groceries,
        to_category=dining,
        amount=Decimal("50"),
        user=user,
        memo="date night",
    )
    assert transfer.at is not None
    assert transfer.user == user
    assert transfer.amount == Decimal("50")
