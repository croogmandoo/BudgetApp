"""Envelope-budgeting models.

Periods are calendar months in the household's timezone (SPEC §3.2).
``BudgetAllocation`` is unique per (period, category) — a period either
has an allocation for a given category or it doesn't. ``BudgetTransfer``
is the first-class "move money between envelopes" action and is its own
audit record, never a fake transaction.
"""

from __future__ import annotations

import uuid

from django.db import models

from apps.accounts.models import Household, User
from apps.core.models import TimestampedModel
from apps.finances.models import Category


class BudgetPeriod(TimestampedModel):
    """A month-long budgeting period keyed by its first-of-month date."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    household = models.ForeignKey(
        Household,
        on_delete=models.CASCADE,
        related_name="budget_periods",
    )
    month = models.DateField(help_text="First day of the month this period represents.")
    locked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["household", "month"], name="uniq_period_per_month"),
        ]


class BudgetAllocation(TimestampedModel):
    """Amount allocated to a single category in a single period."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    period = models.ForeignKey(
        BudgetPeriod,
        on_delete=models.CASCADE,
        related_name="allocations",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="allocations",
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["period", "category"],
                name="uniq_allocation_per_period_category",
            ),
        ]


class BudgetTransfer(TimestampedModel):
    """An explicit "move money between envelopes" action (SPEC §3.2)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    period = models.ForeignKey(
        BudgetPeriod,
        on_delete=models.CASCADE,
        related_name="transfers",
    )
    from_category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="transfers_out",
    )
    to_category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="transfers_in",
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    memo = models.CharField(max_length=256, blank=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="budget_transfers")
    at = models.DateTimeField(auto_now_add=True)
