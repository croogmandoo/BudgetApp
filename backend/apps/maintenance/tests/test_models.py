"""Round-trip tests for maintenance tasks."""

from __future__ import annotations

import datetime as dt

import pytest

from apps.accounts.models import Household
from apps.maintenance.models import MaintenanceCadence, MaintenanceTask


@pytest.mark.django_db
def test_maintenance_task_roundtrip() -> None:
    household = Household.objects.create(name="Test household")
    task = MaintenanceTask.objects.create(
        household=household,
        title="HVAC filter",
        cadence=MaintenanceCadence.MONTHS,
        cadence_interval=3,
        last_done=dt.date(2026, 1, 15),
        next_due=dt.date(2026, 4, 15),
        checklist_json=["Open utility closet", "Remove old filter", "Install MERV-13"],
    )
    assert task.cadence_interval == 3
    assert len(task.checklist_json) == 3
