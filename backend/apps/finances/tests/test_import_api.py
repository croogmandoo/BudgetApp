from __future__ import annotations

import io
from decimal import Decimal

import pytest
from django.utils import timezone
from django_otp.plugins.otp_totp.models import TOTPDevice

from apps.accounts.models import Household, User
from apps.finances.models import Account, ImportProfile, Transaction

RBC_MAPPING = {
    "file_format": "csv",
    "encoding": "utf-8",
    "skip_rows": 0,
    "date_column": "Transaction Date",
    "date_format": "%m/%d/%Y",
    "payee_column": "Description 1",
    "memo_column": "Description 2",
    "cad_column": "CAD$",
    "usd_column": "USD$",
    "amount_strip": [],
    "sign_convention": "positive_is_credit",
}

RBC_CSV = (
    "Account Type,Account Number,Transaction Date,Cheque Number,"
    "Description 1,Description 2,CAD$,USD$\n"
    "Chequing,00372,4/10/2026,,PAYROLL,,-2503.42,\n"
    "Chequing,00372,4/13/2026,,E-TRANSFER,,127.5,\n"
)


@pytest.fixture
def household():
    return Household.objects.create(name="Test HH")


@pytest.fixture
def user(household):
    u = User.objects.create_user(
        username="test@example.com",
        email="test@example.com",
        password="pass",
        household=household,
        role="member",
    )
    TOTPDevice.objects.create(user=u, name="default", confirmed=True)
    u.totp_enforced_at = timezone.now()
    u.save(update_fields=["totp_enforced_at"])
    return u


@pytest.fixture
def account(household):
    return Account.objects.create(
        household=household, name="RBC Chequing", type="checking", currency="CAD"
    )


@pytest.fixture
def profile(household):
    return ImportProfile.objects.create(
        household=household,
        institution="RBC Chequing",
        format="csv",
        mapping_json=RBC_MAPPING,
    )


@pytest.fixture
def auth_client(user):
    from rest_framework.test import APIClient

    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
def test_preview_returns_rows(auth_client, account, profile):
    f = io.BytesIO(RBC_CSV.encode())
    f.name = "rbc.csv"
    resp = auth_client.post(
        "/api/v1/finances/imports/preview/",
        {"account_id": str(account.id), "profile_id": str(profile.id), "file": f},
        format="multipart",
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_rows"] == 2
    assert len(data["to_import"]) == 2
    assert data["exact_duplicates"] == []
    assert data["parse_errors"] == []


@pytest.mark.django_db
def test_preview_flags_exact_duplicate(auth_client, account, profile):
    from datetime import date

    from apps.finances.importers.parser import _compute_hash

    known_hash = _compute_hash(str(account.id), date(2026, 4, 10), Decimal("-2503.42"), "PAYROLL")
    Transaction.objects.create(
        account=account,
        date=date(2026, 4, 10),
        amount=Decimal("-2503.42"),
        payee="PAYROLL",
        import_hash=known_hash,
    )
    f = io.BytesIO(RBC_CSV.encode())
    f.name = "rbc.csv"
    resp = auth_client.post(
        "/api/v1/finances/imports/preview/",
        {"account_id": str(account.id), "profile_id": str(profile.id), "file": f},
        format="multipart",
    )
    data = resp.json()
    assert len(data["exact_duplicates"]) == 1
    assert len(data["to_import"]) == 1


@pytest.mark.django_db
def test_confirm_creates_transactions(auth_client, account, profile):
    preview_file = io.BytesIO(RBC_CSV.encode())
    preview_file.name = "rbc.csv"
    preview_resp = auth_client.post(
        "/api/v1/finances/imports/preview/",
        {"account_id": str(account.id), "profile_id": str(profile.id), "file": preview_file},
        format="multipart",
    )
    preview_data = preview_resp.json()

    confirm_resp = auth_client.post(
        "/api/v1/finances/imports/confirm/",
        {
            "account_id": str(account.id),
            "profile_id": str(profile.id),
            "filename": "rbc.csv",
            "file_sha256": "abc",
            "transactions": preview_data["to_import"],
        },
        format="json",
    )
    assert confirm_resp.status_code == 201
    data = confirm_resp.json()
    assert data["imported"] == 2
    assert Transaction.objects.filter(account=account).count() == 2


@pytest.mark.django_db
def test_preview_wrong_account_returns_404(auth_client, profile):
    import uuid

    f = io.BytesIO(RBC_CSV.encode())
    f.name = "rbc.csv"
    resp = auth_client.post(
        "/api/v1/finances/imports/preview/",
        {"account_id": str(uuid.uuid4()), "profile_id": str(profile.id), "file": f},
        format="multipart",
    )
    assert resp.status_code == 404


@pytest.mark.django_db
def test_new_household_gets_default_profiles():
    """A freshly created household should have 5 seeded import profiles."""
    hh = Household.objects.create(name="Brand New")
    assert ImportProfile.objects.filter(household=hh).count() == 5


@pytest.mark.django_db
def test_default_profiles_include_rbc_and_amex():
    hh = Household.objects.create(name="Fresh")
    institutions = set(
        ImportProfile.objects.filter(household=hh).values_list("institution", flat=True)
    )
    assert "RBC Chequing" in institutions
    assert "American Express Canada" in institutions
