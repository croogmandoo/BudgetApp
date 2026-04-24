from __future__ import annotations
import io
import uuid
from datetime import date as date_type
from decimal import Decimal

import pytest
import xlwt

from apps.finances.importers.parser import parse_file


RBC_PROFILE_MAPPING = {
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
    "Chequing,00372-5086939,4/10/2026,,E-TRANSFER SENT ALICE,,-127.5,\n"
    "Chequing,00372-5086939,4/13/2026,,PAYROLL DEPOSIT,,2503.42,\n"
)


class _FakeProfile:
    def __init__(self, mapping):
        self.mapping_json = mapping
        self.institution = "RBC Chequing"


def test_rbc_csv_parses_two_rows():
    profile = _FakeProfile(RBC_PROFILE_MAPPING)
    result = parse_file(io.BytesIO(RBC_CSV.encode()), profile, "test-account-id")
    assert len(result.rows) == 2
    assert len(result.parse_errors) == 0


AMEX_PROFILE_MAPPING = {
    "file_format": "xls",
    "skip_rows": 16,
    "date_column": "Date",
    "date_format": "%d %b. %Y",
    "payee_column": "Description",
    "memo_column": "Additional Information",
    "amount_column": "Amount",
    "amount_strip": ["$", ","],
    "sign_convention": "positive_is_debit",
    "fx_rate_column": "Exchange Rate",
    "foreign_amount_column": "Foreign Spend Amount",
}


def _make_amex_xls(rows: list[list]) -> io.BytesIO:
    """Build a minimal Amex-shaped XLS with 16 filler rows then header then data."""
    wb = xlwt.Workbook()
    ws = wb.add_sheet("Sheet1")
    for r in range(16):
        ws.write(r, 0, "")
    headers = ["Date", "Date Processed", "Description", "Cardmember",
               "Amount", "Foreign Spend Amount", "Commission",
               "Exchange Rate", "Merchant", "Merchant Address", "Additional Information"]
    for c, h in enumerate(headers):
        ws.write(16, c, h)
    for r_idx, row in enumerate(rows, start=17):
        for c_idx, val in enumerate(row):
            ws.write(r_idx, c_idx, val)
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


def test_amex_xls_charge_is_negative():
    """A positive Amex charge (positive_is_debit) should be stored as negative."""
    profile = _FakeProfile(AMEX_PROFILE_MAPPING)
    xls = _make_amex_xls([
        ["23 Apr. 2026", "23 Apr. 2026", "UBER EATS TORONTO", "CRAIG", "$27.72",
         "", "", "", "", "", "UBER EATS TORONTO"],
    ])
    result = parse_file(xls, profile, "acct-id")
    assert len(result.rows) == 1
    assert result.rows[0].amount == Decimal("-27.72")


def test_amex_xls_credit_is_positive():
    """A negative Amex entry (credit/refund) should be stored as positive."""
    profile = _FakeProfile(AMEX_PROFILE_MAPPING)
    xls = _make_amex_xls([
        ["17 Apr. 2026", "17 Apr. 2026", "OLDNAVY REFUND", "", "-$61.00",
         "", "", "", "", "", "OLDNAVY REFUND"],
    ])
    result = parse_file(xls, profile, "acct-id")
    assert len(result.rows) == 1
    assert len(result.parse_errors) == 0
    assert result.rows[0].amount == Decimal("61.00")


def test_bad_row_is_skipped_and_reported():
    """A row with an invalid date is skipped; parse_errors contains it."""
    profile = _FakeProfile(RBC_PROFILE_MAPPING)
    bad_csv = (
        "Account Type,Account Number,Transaction Date,Cheque Number,"
        "Description 1,Description 2,CAD$,USD$\n"
        "Chequing,00372,99/99/9999,,BAD DATE,,100,\n"
        "Chequing,00372,4/10/2026,,GOOD ROW,,-50,\n"
    )
    result = parse_file(io.BytesIO(bad_csv.encode()), profile, "acct-id")
    assert len(result.rows) == 1
    assert len(result.parse_errors) == 1
    assert result.parse_errors[0].row_num == 2


def test_rbc_usd_column_sets_original_currency():
    """A non-empty USD$ column means original_currency='USD'."""
    profile = _FakeProfile(RBC_PROFILE_MAPPING)
    usd_csv = (
        "Account Type,Account Number,Transaction Date,Cheque Number,"
        "Description 1,Description 2,CAD$,USD$\n"
        "Chequing,00372,4/10/2026,,AMAZON US,,-134.23,-100.00\n"
    )
    result = parse_file(io.BytesIO(usd_csv.encode()), profile, "acct-id")
    assert result.rows[0].original_currency == "USD"


def test_import_hash_is_stable():
    """Same inputs always produce the same import_hash."""
    profile = _FakeProfile(RBC_PROFILE_MAPPING)
    csv_data = (
        "Account Type,Account Number,Transaction Date,Cheque Number,"
        "Description 1,Description 2,CAD$,USD$\n"
        "Chequing,00372,4/10/2026,,PAYROLL,  ,2503.42,\n"
    )
    r1 = parse_file(io.BytesIO(csv_data.encode()), profile, "acct-id")
    r2 = parse_file(io.BytesIO(csv_data.encode()), profile, "acct-id")
    assert r1.rows[0].import_hash == r2.rows[0].import_hash


# ---------------------------------------------------------------------------
# Dedup tests
# ---------------------------------------------------------------------------

from apps.finances.importers.dedup import exact_duplicate_hashes, fuzzy_duplicates
from apps.finances.importers.parser import ParsedRow
from apps.finances.models import Account, Transaction
from apps.accounts.models import Household


def _make_household():
    return Household.objects.create(name="Test")


def _make_account(household):
    return Account.objects.create(
        household=household, name="Chequing", type="checking", currency="CAD"
    )


def _make_txn(account, txn_date, amount, payee, import_hash=""):
    return Transaction.objects.create(
        account=account,
        date=txn_date,
        amount=amount,
        payee=payee,
        import_hash=import_hash or f"hash-{payee}",
    )


def _parsed_row(txn_date, amount, payee, import_hash="x"):
    return ParsedRow(
        row_num=1,
        date=txn_date,
        amount=Decimal(str(amount)),
        payee=payee,
        memo="",
        original_currency="",
        fx_rate=None,
        import_hash=import_hash,
    )


@pytest.mark.django_db
def test_exact_duplicate_detected():
    hh = _make_household()
    acct = _make_account(hh)
    _make_txn(acct, date_type(2026, 4, 10), Decimal("-50"), "PAYEE", "known-hash")
    result = exact_duplicate_hashes(str(acct.id), ["known-hash", "new-hash"])
    assert result == {"known-hash"}


@pytest.mark.django_db
def test_fuzzy_date_and_amount_match():
    hh = _make_household()
    acct = _make_account(hh)
    _make_txn(acct, date_type(2026, 4, 10), Decimal("-50"), "STARBUCKS", "old-hash")
    row = _parsed_row(date_type(2026, 4, 10), "-50", "STARBUCKS KANATA", "new-hash")
    matches = fuzzy_duplicates(str(acct.id), [row])
    assert len(matches) == 1
    assert "date" in matches[0].match_reason
    assert "amount" in matches[0].match_reason


@pytest.mark.django_db
def test_fuzzy_no_false_positive_one_field():
    hh = _make_household()
    acct = _make_account(hh)
    _make_txn(acct, date_type(2026, 4, 10), Decimal("-50"), "STARBUCKS", "old-hash")
    row = _parsed_row(date_type(2026, 4, 10), "-99.99", "TOTALLY DIFFERENT", "new-hash")
    matches = fuzzy_duplicates(str(acct.id), [row])
    assert len(matches) == 0


@pytest.mark.django_db
def test_fuzzy_date_plus_one_day_still_matches():
    hh = _make_household()
    acct = _make_account(hh)
    _make_txn(acct, date_type(2026, 4, 10), Decimal("-50"), "PAYEE", "old-hash")
    row = _parsed_row(date_type(2026, 4, 11), "-50", "PAYEE", "new-hash")
    matches = fuzzy_duplicates(str(acct.id), [row])
    assert len(matches) == 1


# ---------------------------------------------------------------------------
# Rules application tests
# ---------------------------------------------------------------------------

from apps.finances.importers.rules import apply_rules
from apps.finances.models import Category, Rule


@pytest.mark.django_db
def test_apply_rules_categorises_by_payee():
    hh = _make_household()
    acct = _make_account(hh)
    cat = Category.objects.create(household=hh, name="Food", kind="expense")
    Rule.objects.create(
        household=hh,
        priority=10,
        match_json={"payee_contains": "STARBUCKS"},
        action_json={"set_category": str(cat.id)},
    )
    txn = _make_txn(acct, date_type(2026, 4, 10), Decimal("-6"), "STARBUCKS KANATA")
    count = apply_rules([str(txn.id)], str(hh.id))
    assert count == 1
    txn.refresh_from_db()
    assert txn.category_id == cat.id


@pytest.mark.django_db
def test_apply_rules_first_match_wins():
    hh = _make_household()
    acct = _make_account(hh)
    cat1 = Category.objects.create(household=hh, name="Food", kind="expense")
    cat2 = Category.objects.create(household=hh, name="Coffee", kind="expense")
    Rule.objects.create(household=hh, priority=10,
        match_json={"payee_contains": "STARBUCKS"}, action_json={"set_category": str(cat1.id)})
    Rule.objects.create(household=hh, priority=20,
        match_json={"payee_contains": "STARBUCKS"}, action_json={"set_category": str(cat2.id)})
    txn = _make_txn(acct, date_type(2026, 4, 10), Decimal("-6"), "STARBUCKS KANATA")
    apply_rules([str(txn.id)], str(hh.id))
    txn.refresh_from_db()
    assert txn.category_id == cat1.id


@pytest.mark.django_db
def test_apply_rules_no_match_leaves_uncategorised():
    hh = _make_household()
    acct = _make_account(hh)
    Rule.objects.create(household=hh, priority=10,
        match_json={"payee_contains": "STARBUCKS"}, action_json={"set_category": str(uuid.uuid4())})
    txn = _make_txn(acct, date_type(2026, 4, 10), Decimal("-6"), "MCDONALDS")
    apply_rules([str(txn.id)], str(hh.id))
    txn.refresh_from_db()
    assert txn.category_id is None


@pytest.mark.django_db
def test_apply_rules_memo_contains():
    hh = _make_household()
    acct = _make_account(hh)
    cat = Category.objects.create(household=hh, name="Bills", kind="expense")
    Rule.objects.create(
        household=hh, priority=10,
        match_json={"memo_contains": "INTERNET"},
        action_json={"set_category": str(cat.id)},
    )
    txn = Transaction.objects.create(
        account=acct, date=date_type(2026, 4, 10), amount=Decimal("-89.99"),
        payee="ROGERS COMM", memo="INTERNET BILL APRIL",
        import_hash="hash-rogers",
    )
    count = apply_rules([str(txn.id)], str(hh.id))
    assert count == 1
    txn.refresh_from_db()
    assert txn.category_id == cat.id


@pytest.mark.django_db
def test_apply_rules_amount_lt():
    hh = _make_household()
    acct = _make_account(hh)
    cat = Category.objects.create(household=hh, name="Small", kind="expense")
    Rule.objects.create(
        household=hh, priority=10,
        match_json={"amount_lt": 0},
        action_json={"set_category": str(cat.id)},
    )
    txn = Transaction.objects.create(
        account=acct, date=date_type(2026, 4, 10), amount=Decimal("-10"),
        payee="COFFEE", import_hash="hash-coffee",
    )
    count = apply_rules([str(txn.id)], str(hh.id))
    assert count == 1
    txn.refresh_from_db()
    assert txn.category_id == cat.id
