"""Meta-test: catch forgotten makemigrations before CI does.

This runs ``makemigrations --check --dry-run`` against the current model
state. If a model is edited without a migration, the test fails with a
clear message explaining how to regenerate.
"""

from __future__ import annotations

import io

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError


@pytest.mark.django_db
def test_migrations_are_up_to_date() -> None:
    try:
        call_command("makemigrations", "--check", "--dry-run", stdout=io.StringIO())
    except SystemExit as exc:
        pytest.fail(
            "Model schema has changes that are not reflected in migrations. "
            "Run `python manage.py makemigrations` and commit the generated "
            f"file(s). Django exit code: {exc.code}"
        )
    except CommandError as exc:
        pytest.fail(f"makemigrations --check raised CommandError: {exc}")
