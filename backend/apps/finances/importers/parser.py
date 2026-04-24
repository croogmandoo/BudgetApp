from __future__ import annotations

import csv
import hashlib
import io
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.finances.models import ImportProfile


@dataclass
class ParsedRow:
    row_num: int
    date: date
    amount: Decimal
    payee: str
    memo: str
    original_currency: str
    fx_rate: Decimal | None
    import_hash: str


@dataclass
class ParseError:
    row_num: int
    reason: str


@dataclass
class ParseResult:
    rows: list[ParsedRow] = field(default_factory=list)
    parse_errors: list[ParseError] = field(default_factory=list)


def parse_file(file_obj, profile, account_id: str) -> ParseResult:
    m = profile.mapping_json
    if m.get("file_format", "csv") == "xls":
        return _parse_xls(file_obj, m, account_id)
    return _parse_csv(file_obj, m, account_id)


# ---------- internals ----------

def _normalize_payee(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _compute_hash(account_id: str, txn_date: date, amount: Decimal, payee: str) -> str:
    raw = f"{account_id}:{txn_date.isoformat()}:{amount}:{_normalize_payee(payee)}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _strip_amount(value: str, strips: list[str]) -> str:
    for ch in strips:
        value = value.replace(ch, "")
    return value.strip()


def _row_to_parsed(
    row: dict[str, str],
    row_num: int,
    m: dict,
    account_id: str,
) -> ParsedRow:
    date_col = m["date_column"]
    date_fmt = m["date_format"]
    payee_col = m["payee_column"]
    memo_col = m.get("memo_column", "")
    amount_col = m.get("amount_column")
    cad_col = m.get("cad_column")
    usd_col = m.get("usd_column")
    amount_strip = m.get("amount_strip", [])
    sign_convention = m.get("sign_convention", "positive_is_credit")
    fx_col = m.get("fx_rate_column")
    foreign_col = m.get("foreign_amount_column")

    txn_date = datetime.strptime(row[date_col].strip(), date_fmt).date()
    payee = _normalize_payee(row.get(payee_col, ""))
    memo = row.get(memo_col, "").strip() if memo_col else ""

    original_currency = ""
    fx_rate: Decimal | None = None

    if cad_col and usd_col:
        raw_usd = row.get(usd_col, "").strip()
        raw_cad = row.get(cad_col, "").strip()
        if raw_usd:
            raw = _strip_amount(raw_usd, amount_strip)
            original_currency = "USD"
        else:
            raw = _strip_amount(raw_cad, amount_strip)
        amount = Decimal(raw)
    else:
        raw = _strip_amount(row[amount_col], amount_strip)
        amount = Decimal(raw)

    raw_amount = amount
    if sign_convention == "positive_is_debit":
        amount = -amount

    if fx_col and row.get(fx_col, "").strip():
        fx_rate = Decimal(row[fx_col].strip())
    if foreign_col and row.get(foreign_col, "").strip():
        original_currency = "USD"

    return ParsedRow(
        row_num=row_num,
        date=txn_date,
        amount=amount,
        payee=payee,
        memo=memo,
        original_currency=original_currency,
        fx_rate=fx_rate,
        import_hash=_compute_hash(account_id, txn_date, raw_amount, payee),
    )


def _parse_csv(file_obj, m: dict, account_id: str) -> ParseResult:
    encoding = m.get("encoding", "utf-8")
    skip_rows = m.get("skip_rows", 0)

    raw = file_obj.read()
    if isinstance(raw, bytes):
        raw = raw.decode(encoding)

    lines = raw.splitlines()
    lines = lines[skip_rows:]
    reader = csv.DictReader(io.StringIO("\n".join(lines)))

    result = ParseResult()
    for i, row in enumerate(reader, start=skip_rows + 2):
        try:
            result.rows.append(_row_to_parsed(row, i, m, account_id))
        except Exception as exc:
            result.parse_errors.append(ParseError(row_num=i, reason=str(exc)))
    return result


def _parse_xls(file_obj, m: dict, account_id: str) -> ParseResult:
    import xlrd  # noqa: PLC0415

    skip_rows = m.get("skip_rows", 0)
    content = file_obj.read() if hasattr(file_obj, "read") else file_obj
    wb = xlrd.open_workbook(file_contents=content)
    ws = wb.sheet_by_index(0)

    if ws.nrows <= skip_rows:
        return ParseResult()

    headers = [str(ws.cell_value(skip_rows, c)).strip() for c in range(ws.ncols)]

    result = ParseResult()
    for row_idx in range(skip_rows + 1, ws.nrows):
        row_dict = {
            headers[c]: str(ws.cell_value(row_idx, c)).strip()
            for c in range(ws.ncols)
        }
        if not any(row_dict.values()):
            continue
        try:
            result.rows.append(_row_to_parsed(row_dict, row_idx + 1, m, account_id))
        except Exception as exc:
            result.parse_errors.append(ParseError(row_num=row_idx + 1, reason=str(exc)))
    return result
