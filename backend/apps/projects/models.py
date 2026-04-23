"""Project, ProjectTask, and ProjectTransactionLink models.

Cost rollup: project total = sum(task.actual_cost) + sum(linked.amount).
A transaction can be linked directly to a project or to a specific task
via the same link table — one of ``project`` / ``task`` is set.
See SPEC §3.4 / §6.
"""

from __future__ import annotations

import uuid

from django.db import models

from apps.accounts.models import Household, User
from apps.core.models import TimestampedModel
from apps.finances.models import Transaction


class ProjectStatus(models.TextChoices):
    PLANNED = "planned", "Planned"
    ACTIVE = "active", "Active"
    DONE = "done", "Done"
    ABANDONED = "abandoned", "Abandoned"


class ProjectTaskStatus(models.TextChoices):
    TODO = "todo", "To do"
    IN_PROGRESS = "in_progress", "In progress"
    DONE = "done", "Done"
    BLOCKED = "blocked", "Blocked"


class Project(TimestampedModel):
    """A home project (e.g. "Finish basement")."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name="projects")
    name = models.CharField(max_length=128)
    status = models.CharField(
        max_length=16,
        choices=ProjectStatus.choices,
        default=ProjectStatus.PLANNED,
    )
    budget = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)


class ProjectTask(TimestampedModel):
    """A sub-task of a project."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=256)
    status = models.CharField(
        max_length=16,
        choices=ProjectTaskStatus.choices,
        default=ProjectTaskStatus.TODO,
    )
    est_cost = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    actual_cost = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    assignee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="project_tasks",
    )


class ProjectTransactionLink(TimestampedModel):
    """Link between a project (or task) and a transaction.

    Exactly one of ``project`` / ``task`` should be set; the database
    ``CheckConstraint`` below enforces that invariant.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="transaction_links",
    )
    task = models.ForeignKey(
        ProjectTask,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="transaction_links",
    )
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.CASCADE,
        related_name="project_links",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(project__isnull=False, task__isnull=True)
                    | models.Q(project__isnull=True, task__isnull=False)
                ),
                name="link_targets_project_xor_task",
            ),
        ]
