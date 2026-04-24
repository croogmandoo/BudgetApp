"""Round-trip tests for the finances models."""

from __future__ import annotations

from decimal import Decimal

import pytest

from apps.accounts.models import Household, User
from apps.finances.models import (
    Account,
    AccountType,
    Category,
    CategoryKind,
    ImportBatch,
    ImportFormat,
    ImportProfile,
    RolloverMode,
    Rule,
    Transaction,
    TransactionSplit,
    TransactionStatus,
)


@pytest.fixture
def household(db: None) -> Household:
    return Household.objects.create(name="Test household")


@pytest.fixture
def user(household: Household) -> User:
    return User.objects.create_user(username="ada", password="x" * 24, household=household)


def test_account_roundtrip(household: Household) -> None:
    account = Account.objects.create(
        household=household,
        name="Chequing",
        type=AccountType.CHECKING,
        starting_balance=Decimal("1234.56"),
    )
    fetched = Account.objects.get(pk=account.pk)
    assert fetched.starting_balance == Decimal("1234.56")
    assert fetched.currency == "CAD"


def test_category_hierarchy_and_rollover_defaults(household: Household) -> None:
    auto = Category.objects.create(household=household, name="Auto", kind=CategoryKind.EXPENSE)
    fuel = Category.objects.create(
        household=household,
        parent=auto,
        name="Fuel",
        kind=CategoryKind.EXPENSE,
    )
    assert fuel.parent == auto
    assert fuel.is_budgetable is True
    assert fuel.rollover_mode == RolloverMode.CARRY_NEGATIVE


def test_transaction_and_split_roundtrip(household: Household) -> None:
    account = Account.objects.create(household=household, name="Amex", type=AccountType.CREDIT_CARD)
    groceries = Category.objects.create(
        household=household, name="Groceries", kind=CategoryKind.EXPENSE
    )
    household_supplies = Category.objects.create(
        household=household, name="Home supplies", kind=CategoryKind.EXPENSE
    )

    txn = Transaction.objects.create(
        account=account,
        date="2026-04-01",
        amount=Decimal("142.35"),
        payee="COSTCO",
        status=TransactionStatus.CLEARED,
    )
    TransactionSplit.objects.create(
        parent_transaction=txn, category=groceries, amount=Decimal("110.00")
    )
    TransactionSplit.objects.create(
        parent_transaction=txn, category=household_supplies, amount=Decimal("32.35")
    )

    assert txn.splits.count() == 2
    assert sum(s.amount for s in txn.splits.all()) == txn.amount


def test_import_profile_and_batch(household: Household, user: User) -> None:
    profile = ImportProfile.objects.create(
        household=household,
        institution="CIBC",
        format=ImportFormat.CSV,
        mapping_json={"date": "Date", "amount": "Amount"},
    )
    account = Account.objects.create(
        household=household, name="Chequing", type=AccountType.CHECKING
    )
    batch = ImportBatch.objects.create(
        account=account,
        user=user,
        filename="cibc-apr-2026.csv",
        sha256="b" * 64,
        row_count=42,
    )
    assert profile.mapping_json["date"] == "Date"
    assert batch.row_count == 42


def test_rule_defaults(household: Household) -> None:
    rule = Rule.objects.create(
        household=household,
        match_json={"payee_contains": "STARBUCKS"},
        action_json={"set_category": "Coffee"},
    )
    assert rule.enabled is True
    assert rule.priority == 100
