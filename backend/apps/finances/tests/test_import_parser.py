from __future__ import annotations
import io
import pytest
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


@pytest.mark.django_db
def test_rbc_csv_parses_two_rows():
    profile = _FakeProfile(RBC_PROFILE_MAPPING)
    result = parse_file(io.BytesIO(RBC_CSV.encode()), profile, "test-account-id")
    assert len(result.rows) == 2
    assert len(result.parse_errors) == 0
