"""Round-trip tests and XOR-constraint coverage for projects."""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.db import IntegrityError

from apps.accounts.models import Household
from apps.finances.models import Account, AccountType, Transaction, TransactionStatus
from apps.projects.models import (
    Project,
    ProjectStatus,
    ProjectTask,
    ProjectTaskStatus,
    ProjectTransactionLink,
)


@pytest.fixture
def household(db: None) -> Household:
    return Household.objects.create(name="Test household")


@pytest.fixture
def project(household: Household) -> Project:
    return Project.objects.create(
        household=household,
        name="Finish basement",
        status=ProjectStatus.ACTIVE,
        budget=Decimal("12000"),
    )


@pytest.fixture
def transaction(household: Household) -> Transaction:
    account = Account.objects.create(
        household=household, name="Chequing", type=AccountType.CHECKING
    )
    return Transaction.objects.create(
        account=account,
        date="2026-04-10",
        amount=Decimal("340.12"),
        payee="RONA",
        status=TransactionStatus.CLEARED,
    )


def test_task_and_cost_rollup_shape(project: Project) -> None:
    ProjectTask.objects.create(
        project=project,
        title="Demo",
        status=ProjectTaskStatus.DONE,
        est_cost=Decimal("500"),
        actual_cost=Decimal("450"),
    )
    ProjectTask.objects.create(
        project=project, title="Framing", status=ProjectTaskStatus.IN_PROGRESS
    )
    assert project.tasks.count() == 2


def test_link_targets_project_xor_task(project: Project, transaction: Transaction) -> None:
    task = ProjectTask.objects.create(project=project, title="Demo")

    # Both set => violates the XOR constraint.
    with pytest.raises(IntegrityError):
        ProjectTransactionLink.objects.create(project=project, task=task, transaction=transaction)


def test_link_requires_project_or_task(transaction: Transaction) -> None:
    # Neither set => violates the XOR constraint.
    with pytest.raises(IntegrityError):
        ProjectTransactionLink.objects.create(transaction=transaction)


def test_link_with_project_only(project: Project, transaction: Transaction) -> None:
    link = ProjectTransactionLink.objects.create(project=project, transaction=transaction)
    assert link.task_id is None


def test_link_with_task_only(project: Project, transaction: Transaction) -> None:
    task = ProjectTask.objects.create(project=project, title="Electrical")
    link = ProjectTransactionLink.objects.create(task=task, transaction=transaction)
    assert link.project_id is None
