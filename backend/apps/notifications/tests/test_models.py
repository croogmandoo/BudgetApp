"""Round-trip tests and uniqueness coverage for notifications."""

from __future__ import annotations

import pytest
from django.db import IntegrityError

from apps.accounts.models import Household, User
from apps.notifications.models import (
    Notification,
    NotificationChannel,
    NotificationStatus,
    UserChannelPreference,
    Webhook,
)


@pytest.fixture
def household(db: None) -> Household:
    return Household.objects.create(name="Test household")


@pytest.fixture
def user(household: Household) -> User:
    return User.objects.create_user(username="ada", password="x" * 24, household=household)


def test_webhook_secret_is_binary(household: Household) -> None:
    hook = Webhook.objects.create(
        household=household,
        url="https://hooks.example.com/x",
        secret_enc=b"\x00" * 48,
        secret_dek_enc=b"\xff" * 64,
        event_mask=["transaction.imported", "bill.overdue"],
    )
    assert hook.enabled is True
    assert "transaction.imported" in hook.event_mask


def test_notification_defaults_to_pending(household: Household, user: User) -> None:
    note = Notification.objects.create(
        household=household,
        user=user,
        event_type="bill.overdue",
        entity_ref="bill/123",
        payload_json={"bill_name": "Hydro"},
    )
    assert note.status == NotificationStatus.PENDING
    assert note.read_at is None


def test_user_channel_preference_unique(household: Household, user: User) -> None:
    UserChannelPreference.objects.create(
        user=user,
        event_type="maintenance.due",
        channel=NotificationChannel.NTFY,
    )
    with pytest.raises(IntegrityError):
        UserChannelPreference.objects.create(
            user=user,
            event_type="maintenance.due",
            channel=NotificationChannel.NTFY,
        )
