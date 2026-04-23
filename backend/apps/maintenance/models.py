"""MaintenanceTask model.

Time-based cadence only in v1 (every N days). Usage-based cadence (e.g.
odometer km) is noted as a stretch goal in SPEC §3.5 and deliberately not
modelled here.
"""

from __future__ import annotations

import uuid

from django.db import models

from apps.accounts.models import Household
from apps.core.models import TimestampedModel


class MaintenanceCadence(models.TextChoices):
    DAYS = "days", "Every N days"
    WEEKS = "weeks", "Every N weeks"
    MONTHS = "months", "Every N months"
    YEARS = "years", "Every N years"


class MaintenanceTask(TimestampedModel):
    """A recurring household upkeep task."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    household = models.ForeignKey(
        Household,
        on_delete=models.CASCADE,
        related_name="maintenance_tasks",
    )
    title = models.CharField(max_length=256)
    cadence = models.CharField(max_length=16, choices=MaintenanceCadence.choices)
    cadence_interval = models.PositiveIntegerField(
        default=1,
        help_text="e.g. 3 + cadence=months = every three months.",
    )
    last_done = models.DateField(null=True, blank=True)
    next_due = models.DateField(null=True, blank=True, db_index=True)
    checklist_json = models.JSONField(default=list, blank=True)
    notes = models.TextField(blank=True)
