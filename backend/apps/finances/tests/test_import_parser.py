from __future__ import annotations
import io
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
