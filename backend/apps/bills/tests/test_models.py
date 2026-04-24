"""Round-trip tests and uniqueness coverage for bills."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

import pytest
from django.db import IntegrityError

from apps.accounts.models import Household
from apps.bills.models import Bill, BillCadence, BillInstance, BillInstanceStatus


@pytest.fixture
def household(db: None) -> Household:
    return Household.objects.create(name="Test household")


def test_bill_defaults(household: Household) -> None:
    bill = Bill.objects.create(
        household=household,
        name="Hydro",
        payee="BC Hydro",
        amount=Decimal("125.00"),
        cadence=BillCadence.MONTHLY,
        next_due=dt.date(2026, 5, 1),
    )
    assert bill.autopay is False


def test_bill_instance_unique_per_bill_due_date(household: Household) -> None:
    bill = Bill.objects.create(household=household, name="Hydro", cadence=BillCadence.MONTHLY)
    BillInstance.objects.create(
        bill=bill, due_date=dt.date(2026, 5, 1), status=BillInstanceStatus.EXPECTED
    )
    with pytest.raises(IntegrityError):
        BillInstance.objects.create(
            bill=bill, due_date=dt.date(2026, 5, 1), status=BillInstanceStatus.EXPECTED
        )
