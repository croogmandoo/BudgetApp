"""First-run bootstrap: create a household and its initial admin user.

Intended usage on a fresh deployment:

    docker compose exec app python manage.py setup_household \\
        --household "Smith household" \\
        --username ada \\
        --email ada@example.com

If ``--password`` is omitted the command reads it from stdin without
echoing. The command is idempotent on the household name: re-running with
the same ``--household`` value reuses the existing household rather than
creating a duplicate.

TOTP is NOT enrolled here by design — the user completes enrolment
through the API on first login, at which point ``totp_enforced_at`` is
set. Until then, login flows (added in M0b) will refuse authentication,
which matches the "TOTP mandatory from day one" decision in SPEC §7.1.
"""

from __future__ import annotations

import getpass
from typing import Any

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.accounts.models import Household, User, UserRole


class Command(BaseCommand):
    help = "Create the initial household and its first admin user."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--household",
            required=True,
            help="Display name for the household (e.g. 'Smith household').",
        )
        parser.add_argument(
            "--username",
            required=True,
            help="Username for the initial admin user.",
        )
        parser.add_argument(
            "--email",
            required=True,
            help="Email for the initial admin user.",
        )
        parser.add_argument(
            "--password",
            default=None,
            help="Optional. If omitted, the command prompts on stdin.",
        )
        parser.add_argument(
            "--base-currency",
            default="CAD",
            help="Household base currency ISO-4217 code. Default: CAD.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        household_name: str = options["household"]
        username: str = options["username"]
        email: str = options["email"]
        password: str | None = options["password"]
        base_currency: str = options["base_currency"]

        iso4217_length = 3
        if len(base_currency) != iso4217_length or not base_currency.isalpha():
            raise CommandError(
                f"--base-currency must be a 3-letter ISO-4217 code, got {base_currency!r}."
            )

        if password is None:
            password = getpass.getpass("Password for the admin user: ")
            confirm = getpass.getpass("Confirm password: ")
            if password != confirm:
                raise CommandError("Passwords did not match.")

        with transaction.atomic():
            household, household_created = Household.objects.get_or_create(
                name=household_name,
                defaults={"base_currency": base_currency.upper()},
            )

            if User.objects.filter(username=username).exists():
                raise CommandError(
                    f"User {username!r} already exists. "
                    "Pick a different --username or edit the user via the admin."
                )

            user = User(
                username=username,
                email=email,
                household=household,
                role=UserRole.ADMIN,
                is_staff=True,
                is_superuser=True,
            )
            try:
                user.set_password(password)
            except ValidationError as exc:
                raise CommandError(f"Password rejected by validators: {exc.messages}") from exc
            user.save()

        self.stdout.write(
            self.style.SUCCESS(
                f"{'Created' if household_created else 'Reused'} household "
                f"{household.name!r} ({household.id})."
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Created admin user {user.username!r} ({user.id}). "
                "TOTP enrolment happens on first login (SPEC §7.1)."
            )
        )
