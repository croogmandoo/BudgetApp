"""Tests for the auth API endpoints.

Coverage:
    - POST /api/v1/auth/login/
    - POST /api/v1/auth/logout/
    - GET  /api/v1/auth/me/
    - POST /api/v1/auth/totp/enroll/
    - POST /api/v1/auth/totp/confirm/
"""

from __future__ import annotations

import time

import pytest
from django.urls import reverse
from django_otp.oath import TOTP
from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework.test import APIClient

from apps.accounts.models import Household, User

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _current_totp_token(device: TOTPDevice) -> str:
    """Generate the current valid TOTP token for a device.

    Mirrors django-otp's internal verify_token logic using the same
    django_otp.oath.TOTP class so we never need pyotp as a test dep.
    """
    totp = TOTP(device.bin_key, device.step, device.t0, device.digits, device.drift)
    totp.time = time.time()
    return str(totp.token()).zfill(device.digits)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def household(db) -> Household:
    return Household.objects.create(name="Test Household", base_currency="CAD")


@pytest.fixture()
def user(household: Household) -> User:
    """A standard user with no TOTP device enrolled."""
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="SuperSecret123!",
        household=household,
        role="member",
    )


@pytest.fixture()
def admin_user(household: Household) -> User:
    """An admin user with TOTP already enrolled."""
    from django.utils import timezone

    u = User.objects.create_user(
        username="adminuser",
        email="admin@example.com",
        password="AdminPass456!",
        household=household,
        role="admin",
    )
    # Create and confirm a TOTP device, then mark enforcement.
    device = TOTPDevice.objects.create(user=u, name="default", confirmed=True)
    u.totp_enforced_at = timezone.now()
    u.save(update_fields=["totp_enforced_at"])
    u._test_totp_device = device  # stash for token generation in tests
    return u


@pytest.fixture()
def client() -> APIClient:
    return APIClient()


# ---------------------------------------------------------------------------
# URL helpers
# ---------------------------------------------------------------------------


def _login_url() -> str:
    return reverse("auth-login")


def _logout_url() -> str:
    return reverse("auth-logout")


def _me_url() -> str:
    return reverse("auth-me")


def _enroll_url() -> str:
    return reverse("auth-totp-enroll")


def _confirm_url() -> str:
    return reverse("auth-totp-confirm")


# ---------------------------------------------------------------------------
# Login tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_login_bad_credentials_returns_401(client: APIClient) -> None:
    """Wrong email or password → 401."""
    resp = client.post(
        _login_url(),
        {"email": "nobody@example.com", "password": "wrong"},
        format="json",
    )
    assert resp.status_code == 401


@pytest.mark.django_db
def test_login_wrong_password_returns_401(client: APIClient, user: User) -> None:
    """Correct email but wrong password → 401."""
    resp = client.post(
        _login_url(),
        {"email": user.email, "password": "notthepassword"},
        format="json",
    )
    assert resp.status_code == 401


@pytest.mark.django_db
def test_login_disabled_user_returns_403(client: APIClient, user: User) -> None:
    """Disabled account → 403."""
    from django.utils import timezone

    user.disabled_at = timezone.now()
    user.save(update_fields=["disabled_at"])

    resp = client.post(
        _login_url(),
        {"email": user.email, "password": "SuperSecret123!"},
        format="json",
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_login_no_totp_returns_enrollment_required(client: APIClient, user: User) -> None:
    """Successful password login for user with no TOTP → enrollment required flag."""
    resp = client.post(
        _login_url(),
        {"email": user.email, "password": "SuperSecret123!"},
        format="json",
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["totp_enrollment_required"] is True
    assert data["user"]["email"] == user.email
    # Session must be established so the user can proceed to enroll.
    assert "_auth_user_id" in client.session


@pytest.mark.django_db
def test_login_wrong_totp_returns_401(client: APIClient, admin_user: User) -> None:
    """Correct password but wrong TOTP code → 401."""
    resp = client.post(
        _login_url(),
        {"email": admin_user.email, "password": "AdminPass456!", "totp_token": "000000"},
        format="json",
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid authenticator code."


@pytest.mark.django_db
def test_login_correct_totp_returns_200(client: APIClient, admin_user: User) -> None:
    """Correct password + correct TOTP → 200 with user and household."""
    device: TOTPDevice = admin_user._test_totp_device
    token_str = _current_totp_token(device)

    resp = client.post(
        _login_url(),
        {"email": admin_user.email, "password": "AdminPass456!", "totp_token": token_str},
        format="json",
    )
    assert resp.status_code == 200, resp.json()
    data = resp.json()
    assert data["totp_enrollment_required"] is False
    assert data["user"]["email"] == admin_user.email
    assert data["household"]["name"] == "Test Household"
    assert "_auth_user_id" in client.session


# ---------------------------------------------------------------------------
# Logout tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_logout_returns_204_and_clears_session(client: APIClient, user: User) -> None:
    """Authenticated logout → 204, session cleared."""
    client.force_login(user)
    resp = client.post(_logout_url(), format="json")
    assert resp.status_code == 204
    assert "_auth_user_id" not in client.session


@pytest.mark.django_db
def test_logout_unauthenticated_returns_403(client: APIClient) -> None:
    """Unauthenticated logout attempt → 403."""
    resp = client.post(_logout_url(), format="json")
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Me tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_me_returns_current_user(client: APIClient, user: User) -> None:
    """Authenticated GET /me/ returns user data."""
    client.force_login(user)
    resp = client.get(_me_url())
    assert resp.status_code == 200
    data = resp.json()
    assert data["user"]["email"] == user.email
    assert data["user"]["role"] == "member"


@pytest.mark.django_db
def test_me_unauthenticated_returns_403(client: APIClient) -> None:
    """Unauthenticated GET /me/ → 403."""
    resp = client.get(_me_url())
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# TOTP enroll tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_totp_enroll_returns_secret_and_uri(client: APIClient, user: User) -> None:
    """Enrollment returns base32 secret and otpauth URI."""
    client.force_login(user)
    resp = client.post(_enroll_url(), format="json")
    assert resp.status_code == 200
    data = resp.json()
    assert "secret" in data
    assert "otpauth_uri" in data
    assert data["otpauth_uri"].startswith("otpauth://totp/BudgetApp:")
    assert user.email in data["otpauth_uri"]
    # Device should be unconfirmed at this point.
    assert TOTPDevice.objects.filter(user=user, confirmed=False).exists()


@pytest.mark.django_db
def test_totp_enroll_is_idempotent(client: APIClient, user: User) -> None:
    """Calling enroll twice replaces the previous unconfirmed device."""
    client.force_login(user)
    client.post(_enroll_url(), format="json")
    client.post(_enroll_url(), format="json")
    # Only one unconfirmed device should exist.
    assert TOTPDevice.objects.filter(user=user, confirmed=False).count() == 1


# ---------------------------------------------------------------------------
# TOTP confirm tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_totp_confirm_correct_code_returns_200(client: APIClient, user: User) -> None:
    """Correct confirmation code marks device confirmed and sets totp_enforced_at."""
    client.force_login(user)

    # Enroll first.
    enroll_resp = client.post(_enroll_url(), format="json")
    assert enroll_resp.status_code == 200

    # Generate valid token from the device we just created.
    device = TOTPDevice.objects.get(user=user, confirmed=False)
    token_str = _current_totp_token(device)

    confirm_resp = client.post(_confirm_url(), {"totp_token": token_str}, format="json")
    assert confirm_resp.status_code == 200, confirm_resp.json()
    assert confirm_resp.json()["detail"] == "TOTP enrollment complete."

    # Verify DB state.
    user.refresh_from_db()
    assert user.totp_enforced_at is not None
    assert TOTPDevice.objects.filter(user=user, confirmed=True).exists()


@pytest.mark.django_db
def test_totp_confirm_wrong_code_returns_400(client: APIClient, user: User) -> None:
    """Wrong confirmation code → 400."""
    client.force_login(user)
    client.post(_enroll_url(), format="json")

    confirm_resp = client.post(_confirm_url(), {"totp_token": "000000"}, format="json")
    assert confirm_resp.status_code == 400
    assert confirm_resp.json()["detail"] == "Invalid code."


@pytest.mark.django_db
def test_totp_confirm_without_enrollment_returns_400(client: APIClient, user: User) -> None:
    """Calling confirm without prior enroll → 400 with helpful message."""
    client.force_login(user)
    confirm_resp = client.post(_confirm_url(), {"totp_token": "123456"}, format="json")
    assert confirm_resp.status_code == 400
