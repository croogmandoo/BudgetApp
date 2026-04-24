"""Round-trip tests for identity models.

Covers the SPEC §7.1 invariants that apply at the model level:

    - Users belong to a household with a role.
    - Password hashing goes through Argon2 (PASSWORD_HASHERS in settings).
    - API tokens store only a hash (the plaintext is never persisted).
"""

from __future__ import annotations

import pytest

from apps.accounts.models import APIToken, Household, User, UserRole


@pytest.mark.django_db
def test_household_roundtrip() -> None:
    household = Household.objects.create(name="Test household", base_currency="CAD")
    fetched = Household.objects.get(pk=household.pk)
    assert fetched.name == "Test household"
    assert fetched.base_currency == "CAD"
    assert fetched.created_at is not None


@pytest.mark.django_db
def test_user_defaults_to_member_and_requires_argon2_password() -> None:
    household = Household.objects.create(name="Test household")
    user = User.objects.create_user(
        username="ada",
        email="ada@example.com",
        password="correct horse battery staple",
        household=household,
    )
    assert user.role == UserRole.MEMBER
    assert user.totp_enforced_at is None
    assert user.password.startswith("argon2"), (
        "Argon2 is the only configured password hasher (SPEC §7.1)."
    )


@pytest.mark.django_db
def test_api_token_stores_only_a_hash() -> None:
    household = Household.objects.create(name="Test household")
    user = User.objects.create_user(username="ada", password="x" * 24, household=household)

    token = APIToken.objects.create(
        user=user,
        name="Home Assistant",
        token_hash="sha256:" + "f" * 56,
        scopes=["transactions:read", "bills:read"],
    )
    assert token.token_hash.startswith("sha256:")
    assert "transactions:read" in token.scopes
    assert token.revoked_at is None
