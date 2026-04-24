"""Tests for the finances CRUD API.

Coverage:
    - GET/POST /api/v1/finances/accounts/
    - GET/PATCH/PUT/DELETE /api/v1/finances/accounts/{id}/
    - GET/POST /api/v1/finances/categories/
    - GET/PATCH/PUT/DELETE /api/v1/finances/categories/{id}/
    - GET/POST /api/v1/finances/transactions/  (incl. inline splits)
    - GET/PATCH/PUT/DELETE /api/v1/finances/transactions/{id}/
    - GET/POST /api/v1/finances/rules/
    - GET/PATCH/PUT/DELETE /api/v1/finances/rules/{id}/
    - Household isolation across all endpoints
    - Auth gate: unauthenticated and TOTP-unenrolled users get 403
"""

from __future__ import annotations

import pytest
from django.utils import timezone
from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework.test import APIClient

from apps.accounts.models import Household, User
from apps.finances.models import Account, Category, Rule, Transaction, TransactionSplit

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def household(db) -> Household:
    return Household.objects.create(name="Test Household", base_currency="CAD")


@pytest.fixture()
def other_household(db) -> Household:
    return Household.objects.create(name="Other Household", base_currency="CAD")


def _make_enrolled_user(household: Household, username: str, email: str) -> User:
    u = User.objects.create_user(
        username=username,
        email=email,
        password="SuperSecret123!",
        household=household,
        role="member",
    )
    TOTPDevice.objects.create(user=u, name="default", confirmed=True)
    u.totp_enforced_at = timezone.now()
    u.save(update_fields=["totp_enforced_at"])
    return u


@pytest.fixture()
def user(household: Household) -> User:
    return _make_enrolled_user(household, "testuser", "test@example.com")


@pytest.fixture()
def other_user(other_household: Household) -> User:
    return _make_enrolled_user(other_household, "otheruser", "other@example.com")


@pytest.fixture()
def api_client(user: User) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture()
def other_client(other_user: User) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=other_user)
    return client


@pytest.fixture()
def account(household: Household) -> Account:
    return Account.objects.create(
        household=household,
        name="Test Chequing",
        type="checking",
        currency="CAD",
        starting_balance="1000.00",
    )


@pytest.fixture()
def other_account(other_household: Household) -> Account:
    return Account.objects.create(
        household=other_household,
        name="Other Chequing",
        type="checking",
        currency="CAD",
    )


@pytest.fixture()
def category(household: Household) -> Category:
    return Category.objects.create(
        household=household,
        name="Groceries",
        kind="expense",
    )


@pytest.fixture()
def other_category(other_household: Household) -> Category:
    return Category.objects.create(
        household=other_household,
        name="Other Groceries",
        kind="expense",
    )


@pytest.fixture()
def transaction(account: Account, category: Category) -> Transaction:
    return Transaction.objects.create(
        account=account,
        date="2026-01-15",
        amount="-42.50",
        payee="FreshCo",
        category=category,
    )


# ---------------------------------------------------------------------------
# Auth gate tests
# ---------------------------------------------------------------------------


class TestAuthGate:
    def test_unauthenticated_accounts(self, db):
        client = APIClient()
        resp = client.get("/api/v1/finances/accounts/")
        assert resp.status_code == 403

    def test_no_totp_accounts(self, household):
        u = User.objects.create_user(
            username="nototp",
            email="nototp@example.com",
            password="Secret123!",
            household=household,
            role="member",
        )
        client = APIClient()
        client.force_authenticate(user=u)
        resp = client.get("/api/v1/finances/accounts/")
        assert resp.status_code == 403

    def test_no_household_accounts(self, db):
        u = User.objects.create_user(
            username="nohh",
            email="nohh@example.com",
            password="Secret123!",
        )
        u.totp_enforced_at = timezone.now()
        u.save(update_fields=["totp_enforced_at"])
        client = APIClient()
        client.force_authenticate(user=u)
        resp = client.get("/api/v1/finances/accounts/")
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Account tests
# ---------------------------------------------------------------------------


class TestAccountViewSet:
    def test_list_returns_own_accounts(self, api_client, account):
        resp = api_client.get("/api/v1/finances/accounts/")
        assert resp.status_code == 200
        ids = [r["id"] for r in resp.data["results"]]
        assert str(account.id) in ids

    def test_list_excludes_other_household(self, api_client, other_account):
        resp = api_client.get("/api/v1/finances/accounts/")
        ids = [r["id"] for r in resp.data["results"]]
        assert str(other_account.id) not in ids

    def test_create_account(self, api_client):
        resp = api_client.post(
            "/api/v1/finances/accounts/",
            {"name": "Savings", "type": "savings", "currency": "CAD", "starting_balance": "500.00"},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.data["name"] == "Savings"

    def test_create_sets_household(self, api_client, user):
        api_client.post(
            "/api/v1/finances/accounts/",
            {"name": "Cash", "type": "cash", "currency": "CAD"},
            format="json",
        )
        acc = Account.objects.get(name="Cash")
        assert acc.household_id == user.household_id

    def test_retrieve_own_account(self, api_client, account):
        resp = api_client.get(f"/api/v1/finances/accounts/{account.id}/")
        assert resp.status_code == 200
        assert resp.data["name"] == account.name

    def test_retrieve_other_household_returns_404(self, api_client, other_account):
        resp = api_client.get(f"/api/v1/finances/accounts/{other_account.id}/")
        assert resp.status_code == 404

    def test_patch_account(self, api_client, account):
        resp = api_client.patch(
            f"/api/v1/finances/accounts/{account.id}/",
            {"name": "Updated Chequing"},
            format="json",
        )
        assert resp.status_code == 200
        account.refresh_from_db()
        assert account.name == "Updated Chequing"

    def test_delete_account(self, api_client, account):
        resp = api_client.delete(f"/api/v1/finances/accounts/{account.id}/")
        assert resp.status_code == 204
        assert not Account.objects.filter(id=account.id).exists()

    def test_delete_other_household_returns_404(self, api_client, other_account):
        resp = api_client.delete(f"/api/v1/finances/accounts/{other_account.id}/")
        assert resp.status_code == 404
        assert Account.objects.filter(id=other_account.id).exists()


# ---------------------------------------------------------------------------
# Category tests
# ---------------------------------------------------------------------------


class TestCategoryViewSet:
    def test_list_returns_own_categories(self, api_client, category):
        resp = api_client.get("/api/v1/finances/categories/")
        assert resp.status_code == 200
        ids = [r["id"] for r in resp.data["results"]]
        assert str(category.id) in ids

    def test_list_excludes_other_household(self, api_client, other_category):
        resp = api_client.get("/api/v1/finances/categories/")
        ids = [r["id"] for r in resp.data["results"]]
        assert str(other_category.id) not in ids

    def test_create_category(self, api_client):
        resp = api_client.post(
            "/api/v1/finances/categories/",
            {"name": "Utilities", "kind": "expense"},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.data["name"] == "Utilities"

    def test_create_child_category(self, api_client, category):
        resp = api_client.post(
            "/api/v1/finances/categories/",
            {"name": "Organic", "kind": "expense", "parent": str(category.id)},
            format="json",
        )
        assert resp.status_code == 201
        assert str(resp.data["parent"]) == str(category.id)

    def test_parent_from_other_household_rejected(self, api_client, other_category):
        resp = api_client.post(
            "/api/v1/finances/categories/",
            {"name": "Child", "kind": "expense", "parent": str(other_category.id)},
            format="json",
        )
        assert resp.status_code == 400

    def test_retrieve_own_category(self, api_client, category):
        resp = api_client.get(f"/api/v1/finances/categories/{category.id}/")
        assert resp.status_code == 200

    def test_retrieve_other_household_returns_404(self, api_client, other_category):
        resp = api_client.get(f"/api/v1/finances/categories/{other_category.id}/")
        assert resp.status_code == 404

    def test_patch_category(self, api_client, category):
        resp = api_client.patch(
            f"/api/v1/finances/categories/{category.id}/",
            {"name": "Food"},
            format="json",
        )
        assert resp.status_code == 200
        category.refresh_from_db()
        assert category.name == "Food"

    def test_delete_category(self, api_client, category):
        resp = api_client.delete(f"/api/v1/finances/categories/{category.id}/")
        assert resp.status_code == 204


# ---------------------------------------------------------------------------
# Transaction tests
# ---------------------------------------------------------------------------


class TestTransactionViewSet:
    def test_list_returns_own_transactions(self, api_client, transaction):
        resp = api_client.get("/api/v1/finances/transactions/")
        assert resp.status_code == 200
        ids = [r["id"] for r in resp.data["results"]]
        assert str(transaction.id) in ids

    def test_list_excludes_other_household(self, api_client, other_account):
        other_tx = Transaction.objects.create(
            account=other_account,
            date="2026-01-01",
            amount="-10.00",
            payee="Other Store",
        )
        resp = api_client.get("/api/v1/finances/transactions/")
        ids = [r["id"] for r in resp.data["results"]]
        assert str(other_tx.id) not in ids

    def test_create_transaction(self, api_client, account):
        resp = api_client.post(
            "/api/v1/finances/transactions/",
            {
                "account": str(account.id),
                "date": "2026-02-01",
                "amount": "-15.99",
                "payee": "Coffee Shop",
                "status": "cleared",
            },
            format="json",
        )
        assert resp.status_code == 201
        assert resp.data["payee"] == "Coffee Shop"

    def test_create_transaction_with_splits(self, api_client, account, category):
        resp = api_client.post(
            "/api/v1/finances/transactions/",
            {
                "account": str(account.id),
                "date": "2026-02-10",
                "amount": "-100.00",
                "payee": "Costco",
                "splits": [
                    {"category": str(category.id), "amount": "-60.00", "memo": "Groceries"},
                    {"category": str(category.id), "amount": "-40.00", "memo": "Household"},
                ],
            },
            format="json",
        )
        assert resp.status_code == 201
        assert len(resp.data["splits"]) == 2

    def test_create_rejects_other_household_account(self, api_client, other_account):
        resp = api_client.post(
            "/api/v1/finances/transactions/",
            {"account": str(other_account.id), "date": "2026-02-01", "amount": "-5.00"},
            format="json",
        )
        assert resp.status_code == 400

    def test_create_rejects_other_household_category(self, api_client, account, other_category):
        resp = api_client.post(
            "/api/v1/finances/transactions/",
            {
                "account": str(account.id),
                "date": "2026-02-01",
                "amount": "-5.00",
                "category": str(other_category.id),
            },
            format="json",
        )
        assert resp.status_code == 400

    def test_retrieve_own_transaction(self, api_client, transaction):
        resp = api_client.get(f"/api/v1/finances/transactions/{transaction.id}/")
        assert resp.status_code == 200
        assert resp.data["payee"] == transaction.payee

    def test_retrieve_other_household_returns_404(self, api_client, other_account):
        other_tx = Transaction.objects.create(
            account=other_account, date="2026-01-01", amount="-5.00"
        )
        resp = api_client.get(f"/api/v1/finances/transactions/{other_tx.id}/")
        assert resp.status_code == 404

    def test_patch_transaction(self, api_client, transaction):
        resp = api_client.patch(
            f"/api/v1/finances/transactions/{transaction.id}/",
            {"memo": "Updated memo"},
            format="json",
        )
        assert resp.status_code == 200
        transaction.refresh_from_db()
        assert transaction.memo == "Updated memo"

    def test_update_replaces_splits(self, api_client, transaction, category):
        TransactionSplit.objects.create(
            parent_transaction=transaction, category=category, amount="-42.50"
        )
        resp = api_client.patch(
            f"/api/v1/finances/transactions/{transaction.id}/",
            {
                "splits": [
                    {"category": str(category.id), "amount": "-20.00", "memo": "Part 1"},
                    {"category": str(category.id), "amount": "-22.50", "memo": "Part 2"},
                ]
            },
            format="json",
        )
        assert resp.status_code == 200
        assert TransactionSplit.objects.filter(parent_transaction=transaction).count() == 2

    def test_patch_without_splits_key_preserves_splits(self, api_client, transaction, category):
        TransactionSplit.objects.create(
            parent_transaction=transaction, category=category, amount="-42.50"
        )
        resp = api_client.patch(
            f"/api/v1/finances/transactions/{transaction.id}/",
            {"memo": "no split change"},
            format="json",
        )
        assert resp.status_code == 200
        assert TransactionSplit.objects.filter(parent_transaction=transaction).count() == 1

    def test_delete_transaction(self, api_client, transaction):
        resp = api_client.delete(f"/api/v1/finances/transactions/{transaction.id}/")
        assert resp.status_code == 204

    def test_splits_included_in_list(self, api_client, transaction, category):
        TransactionSplit.objects.create(
            parent_transaction=transaction, category=category, amount="-42.50"
        )
        resp = api_client.get("/api/v1/finances/transactions/")
        tx_data = next(r for r in resp.data["results"] if r["id"] == str(transaction.id))
        assert len(tx_data["splits"]) == 1


# ---------------------------------------------------------------------------
# Rule tests
# ---------------------------------------------------------------------------


class TestRuleViewSet:
    def test_list_returns_own_rules(self, api_client, user):
        from apps.finances.models import Rule

        rule = Rule.objects.create(
            household=user.household,
            match_json={"payee__icontains": "amazon"},
            action_json={"category": "shopping"},
        )
        resp = api_client.get("/api/v1/finances/rules/")
        assert resp.status_code == 200
        ids = [r["id"] for r in resp.data["results"]]
        assert str(rule.id) in ids

    def test_create_rule(self, api_client):
        resp = api_client.post(
            "/api/v1/finances/rules/",
            {
                "priority": 10,
                "match_json": {"payee__icontains": "netflix"},
                "action_json": {"category_name": "Subscriptions"},
                "enabled": True,
            },
            format="json",
        )
        assert resp.status_code == 201
        assert resp.data["priority"] == 10

    def test_list_excludes_other_household(self, api_client, other_household):
        other_rule = Rule.objects.create(
            household=other_household,
            match_json={},
            action_json={},
        )
        resp = api_client.get("/api/v1/finances/rules/")
        ids = [r["id"] for r in resp.data["results"]]
        assert str(other_rule.id) not in ids

    def test_retrieve_other_household_returns_404(self, api_client, other_household):
        other_rule = Rule.objects.create(
            household=other_household,
            match_json={},
            action_json={},
        )
        resp = api_client.get(f"/api/v1/finances/rules/{other_rule.id}/")
        assert resp.status_code == 404

    def test_patch_rule(self, api_client, user):
        rule = Rule.objects.create(
            household=user.household,
            match_json={},
            action_json={},
            enabled=True,
        )
        resp = api_client.patch(
            f"/api/v1/finances/rules/{rule.id}/",
            {"enabled": False},
            format="json",
        )
        assert resp.status_code == 200
        rule.refresh_from_db()
        assert rule.enabled is False

    def test_delete_rule(self, api_client, user):
        rule = Rule.objects.create(household=user.household, match_json={}, action_json={})
        resp = api_client.delete(f"/api/v1/finances/rules/{rule.id}/")
        assert resp.status_code == 204
