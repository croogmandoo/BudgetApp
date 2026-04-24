"""Accounts, categories, transactions, splits, rules, imports.

Mirrors SPEC §6. Notes on the design choices encoded here:

    - Monetary fields are ``DecimalField(max_digits=14, decimal_places=2)``
      throughout. 14 digits fits 999,999,999,999.99 which is plenty for a
      household and matches Postgres ``numeric(14,2)``.
    - Transactions carry both a native ``amount`` (in the account currency)
      and an optional ``original_currency`` + ``fx_rate`` so USD
      transactions round-trip cleanly into a CAD-primary ledger
      (SPEC §3.1).
    - Rules use JSONB for match / action payloads so new rule primitives
      can land without migrations.
    - Imports are deduplicated on ``import_hash`` computed from
      (account, date, amount, normalized payee).
"""

from __future__ import annotations

import uuid

from django.db import models

from apps.accounts.models import Household, User
from apps.core.models import TimestampedModel


class AccountType(models.TextChoices):
    CHECKING = "checking", "Checking"
    SAVINGS = "savings", "Savings"
    CREDIT_CARD = "credit_card", "Credit card"
    CASH = "cash", "Cash"
    LOAN = "loan", "Loan"
    INVESTMENT = "investment", "Investment (balance-only)"


class Account(TimestampedModel):
    """A bank / card / cash / loan / investment account (balance-only for v1)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name="accounts")
    name = models.CharField(max_length=128)
    type = models.CharField(max_length=16, choices=AccountType.choices)
    institution = models.CharField(max_length=128, blank=True)
    currency = models.CharField(max_length=3, default="CAD")
    starting_balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    closed_at = models.DateTimeField(null=True, blank=True)


class CategoryKind(models.TextChoices):
    INCOME = "income", "Income"
    EXPENSE = "expense", "Expense"
    TRANSFER = "transfer", "Transfer"


class RolloverMode(models.TextChoices):
    CARRY_POSITIVE = "carry_positive", "Carry unspent forward"
    CARRY_NEGATIVE = "carry_negative", "Carry overspend forward"
    RESET = "reset", "Reset to zero each period"


class Category(TimestampedModel):
    """Hierarchical category; also acts as an envelope when budgeted."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name="categories")
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
    )
    name = models.CharField(max_length=128)
    kind = models.CharField(max_length=16, choices=CategoryKind.choices)
    is_budgetable = models.BooleanField(default=True)
    rollover_mode = models.CharField(
        max_length=24,
        choices=RolloverMode.choices,
        default=RolloverMode.CARRY_NEGATIVE,
    )

    class Meta:
        indexes = [
            models.Index(fields=["household", "parent"]),
        ]


class ImportFormat(models.TextChoices):
    CSV = "csv", "CSV"
    OFX = "ofx", "OFX"
    QFX = "qfx", "QFX"
    XLS = "xls", "XLS"


class ImportProfile(TimestampedModel):
    """Declarative per-bank mapping (columns, sign convention, date format)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    household = models.ForeignKey(
        Household,
        on_delete=models.CASCADE,
        related_name="import_profiles",
    )
    institution = models.CharField(max_length=128)
    format = models.CharField(max_length=8, choices=ImportFormat.choices)
    mapping_json = models.JSONField(default=dict)


class ImportBatch(TimestampedModel):
    """One import run against a single account. Used for de-dup + undo."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="import_batches")
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="import_batches")
    filename = models.CharField(max_length=255)
    sha256 = models.CharField(max_length=64)
    row_count = models.PositiveIntegerField(default=0)


class TransactionStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    CLEARED = "cleared", "Cleared"
    VOID = "void", "Void"


class Transaction(TimestampedModel):
    """One posted or pending transaction.

    The ``import_hash`` column is the stable hash of
    (account, date, amount, normalized payee) used for re-upload de-dup
    (SPEC §3.1).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="transactions")
    date = models.DateField(db_index=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    original_currency = models.CharField(max_length=3, blank=True)
    fx_rate = models.DecimalField(max_digits=14, decimal_places=6, null=True, blank=True)
    payee = models.CharField(max_length=256, blank=True)
    memo = models.TextField(blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )
    status = models.CharField(
        max_length=16,
        choices=TransactionStatus.choices,
        default=TransactionStatus.CLEARED,
    )
    import_batch = models.ForeignKey(
        ImportBatch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )
    import_hash = models.CharField(max_length=64, blank=True, db_index=True)
    receipt_attachment_id = models.UUIDField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["account", "date"]),
            models.Index(fields=["category", "date"]),
        ]


class TransactionSplit(TimestampedModel):
    """A child line inside a split transaction."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parent_transaction = models.ForeignKey(
        Transaction,
        on_delete=models.CASCADE,
        related_name="splits",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="splits",
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    memo = models.CharField(max_length=256, blank=True)


class Rule(TimestampedModel):
    """Categorization rule (match payee/memo/amount → set category/tags)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name="rules")
    priority = models.IntegerField(default=100)
    match_json = models.JSONField(default=dict)
    action_json = models.JSONField(default=dict)
    enabled = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["household", "priority"]),
        ]
