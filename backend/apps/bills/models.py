"""Bill + BillInstance models.

A ``Bill`` is the template (name, payee, expected amount, cadence, due
day). A ``BillInstance`` is one materialised occurrence (e.g. "August 2026
hydro") with status and an optional link to the paying transaction.
See SPEC §3.3.
"""

from __future__ import annotations

import uuid

from django.db import models

from apps.accounts.models import Household
from apps.core.models import TimestampedModel
from apps.finances.models import Account, Transaction


class BillCadence(models.TextChoices):
    MONTHLY = "monthly", "Monthly"
    QUARTERLY = "quarterly", "Quarterly"
    ANNUAL = "annual", "Annual"
    CUSTOM = "custom", "Custom"


class BillInstanceStatus(models.TextChoices):
    EXPECTED = "expected", "Expected"
    PAID = "paid", "Paid"
    OVERDUE = "overdue", "Overdue"
    SKIPPED = "skipped", "Skipped"


class Bill(TimestampedModel):
    """Recurring obligation template."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name="bills")
    name = models.CharField(max_length=128)
    payee = models.CharField(max_length=256, blank=True)
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Null when the bill is variable.",
    )
    cadence = models.CharField(max_length=16, choices=BillCadence.choices)
    next_due = models.DateField(null=True, blank=True)
    account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name="bills",
        null=True,
        blank=True,
    )
    autopay = models.BooleanField(default=False)


class BillInstance(TimestampedModel):
    """One materialised occurrence of a ``Bill``."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name="instances")
    due_date = models.DateField(db_index=True)
    amount_expected = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    paid_transaction = models.ForeignKey(
        Transaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bill_instances_paid",
    )
    status = models.CharField(
        max_length=16,
        choices=BillInstanceStatus.choices,
        default=BillInstanceStatus.EXPECTED,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["bill", "due_date"],
                name="uniq_instance_per_bill_due",
            ),
        ]
