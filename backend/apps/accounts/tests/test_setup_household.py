"""Tests for the ``setup_household`` management command."""

from __future__ import annotations

import io

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.accounts.models import Household, User, UserRole


@pytest.mark.django_db
def test_creates_household_and_admin_user() -> None:
    out = io.StringIO()
    call_command(
        "setup_household",
        "--household",
        "Smith household",
        "--username",
        "ada",
        "--email",
        "ada@example.com",
        "--password",
        "correct horse battery staple",
        stdout=out,
    )

    household = Household.objects.get(name="Smith household")
    assert household.base_currency == "CAD"

    user = User.objects.get(username="ada")
    assert user.email == "ada@example.com"
    assert user.household == household
    assert user.role == UserRole.ADMIN
    assert user.is_staff is True
    assert user.is_superuser is True
    assert user.totp_enforced_at is None, (
        "TOTP enrolment happens on first login, not here (SPEC §7.1)."
    )
    assert user.check_password("correct horse battery staple")


@pytest.mark.django_db
def test_reuses_existing_household_by_name() -> None:
    existing = Household.objects.create(name="Shared household", base_currency="USD")

    call_command(
        "setup_household",
        "--household",
        "Shared household",
        "--username",
        "ada",
        "--email",
        "ada@example.com",
        "--password",
        "x" * 24,
    )

    # A second household row was NOT created.
    assert Household.objects.filter(name="Shared household").count() == 1
    ada = User.objects.get(username="ada")
    assert ada.household == existing


@pytest.mark.django_db
def test_refuses_to_overwrite_existing_username() -> None:
    household = Household.objects.create(name="Household")
    User.objects.create_user(username="ada", password="x" * 24, household=household)

    with pytest.raises(CommandError, match="already exists"):
        call_command(
            "setup_household",
            "--household",
            "Household",
            "--username",
            "ada",
            "--email",
            "ada@example.com",
            "--password",
            "x" * 24,
        )


@pytest.mark.django_db
def test_rejects_malformed_base_currency() -> None:
    with pytest.raises(CommandError, match="ISO-4217"):
        call_command(
            "setup_household",
            "--household",
            "h",
            "--username",
            "ada",
            "--email",
            "ada@example.com",
            "--password",
            "x" * 24,
            "--base-currency",
            "CANADIAN",
        )
