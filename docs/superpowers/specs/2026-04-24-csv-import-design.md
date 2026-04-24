# CSV / XLS Import Design

**Date:** 2026-04-24
**Scope:** M0 — file-based transaction import for RBC, Amex Canada, CIBC, TD, Scotiabank

---

## Overview

Users upload a bank export file (CSV or XLS) against an account and a pre-seeded import profile. A two-step preview → confirm flow shows what will be imported, flags exact and probable duplicates, and surfaces parse errors before any data is written.

---

## Profile Schema (`ImportProfile.mapping_json`)

Each bank profile is a JSON object stored in the existing `ImportProfile.mapping_json` field. The parser inspects which fields are present to route its logic:

```json
{
  "file_format": "csv",          // "csv" | "xls"
  "encoding": "utf-8-sig",       // csv only; default utf-8
  "skip_rows": 0,                // rows to skip before header
  "date_column": "Transaction Date",
  "date_format": "%m/%d/%Y",
  "payee_column": "Description 1",
  "memo_column": "Description 2",

  // Option A — single signed amount column (Amex, CIBC, TD, Scotia)
  "amount_column": "Amount",
  "amount_strip": ["$", ","],
  "sign_convention": "positive_is_debit",

  // Option B — dual currency columns (RBC)
  "cad_column": "CAD$",
  "usd_column": "USD$",

  // Optional — foreign currency passthrough (Amex)
  "fx_rate_column": "Exchange Rate",
  "foreign_amount_column": "Foreign Spend Amount"
}
```

`sign_convention` values:
- `positive_is_debit` — positive amount = money out (Amex credit card convention)
- `positive_is_credit` — positive amount = money in (RBC chequing convention)

When `cad_column`/`usd_column` are present, `amount_column` is ignored. A non-empty `usd_column` value on a row sets `original_currency="USD"` and stores the CAD equivalent in `amount`.

---

## Seeded Bank Profiles

Five profiles loaded via a data migration into `ImportProfile`. Profiles are household-scoped. The migration creates one copy per existing household; a `post_save` signal on `Household` creation seeds the same five profiles for every new household going forward.

| Institution | Format | Notes |
|---|---|---|
| RBC Chequing | CSV | Dual CAD$/USD$ columns, `M/D/YYYY` date |
| American Express Canada | XLS | `skip_rows: 16`, `DD Mon. YYYY` date, foreign spend columns |
| CIBC Chequing | CSV | **TODO: verify against real export** |
| TD EasyWeb | CSV | **TODO: verify against real export** |
| Scotiabank | CSV | **TODO: verify against real export** |

CIBC, TD, and Scotia profiles are seeded with best-guess column names from public documentation and marked with a `"verified": false` flag in `mapping_json`. The flag is surfaced in the API so the UI can warn the user.

---

## API Endpoints

Both require `IsTOTPVerifiedHouseholdMember`. Registered at `/api/v1/finances/`.

### `POST /imports/preview/`

**Request:** `multipart/form-data` — `file`, `account_id` (UUID), `profile_id` (UUID)

**Response:**
```json
{
  "profile_name": "RBC Chequing",
  "total_rows": 34,
  "to_import": [
    {"row": 2, "date": "2026-04-10", "amount": "-127.50", "payee": "E-TRANSFER SENT STEPHANIE M DENIS", "import_hash": "abc123"}
  ],
  "exact_duplicates": [{"row": 5, "import_hash": "..."}],
  "probable_duplicates": [{"row": 9, "import_hash": "...", "matched_transaction_id": "uuid", "match_reason": "date+amount"}],
  "parse_errors": [{"row": 3, "reason": "invalid date '99/99/9999'"}]
}
```

No data is written. The file is parsed in memory; the raw file is not stored.

### `POST /imports/confirm/`

**Request:** JSON
```json
{
  "account_id": "uuid",
  "profile_id": "uuid",
  "filename": "rbc-april.csv",
  "file_sha256": "abc...",
  "row_hashes": ["abc123", "def456"]
}
```

`row_hashes` is the subset of `to_import` hashes the user has chosen to commit (client can deselect probable duplicates). The server re-parses the file using `file_sha256` to verify integrity — if the hash doesn't match the re-parsed file, the request is rejected with 409.

**Response:**
```json
{
  "batch_id": "uuid",
  "imported": 31,
  "rules_applied": 8,
  "skipped_duplicates": 3
}
```

Creates one `ImportBatch`, bulk-inserts `Transaction` rows, then applies household `Rule`s in priority order to uncategorized transactions in the batch.

---

## Parser (`apps/finances/importers/parser.py`)

Single public function:

```python
def parse_file(file_obj, profile: ImportProfile) -> ParseResult:
    ...
```

`ParseResult` is a dataclass:
```python
@dataclass
class ParseResult:
    rows: list[ParsedRow]
    parse_errors: list[ParseError]
```

**CSV path:** `csv.DictReader(file_obj, encoding=profile.mapping_json.get("encoding", "utf-8"))`

**XLS path:** `xlrd.open_workbook(file_contents=file_obj.read())`, skip `skip_rows` rows, build dicts from header row.

Per row: strip amount chars, parse date with `datetime.strptime`, normalize payee (strip + collapse internal whitespace), compute `import_hash = sha256(f"{account_id}:{date}:{amount}:{normalized_payee}")`. Bad rows caught with broad `except Exception` → appended to `parse_errors`, row skipped.

---

## Deduplication (`apps/finances/importers/dedup.py`)

**Exact:** Bulk-fetch `import_hash` set for the account. O(1) lookup per row.

**Fuzzy (probable duplicate):** For rows not exact-matched, query transactions for the account within ±1 day of the row date. For each candidate, count how many of (date, amount, normalized_payee) match. If ≥ 2 match → `probable_duplicate`. `match_reason` records which two fields matched (e.g., `"date+amount"`).

---

## Rule Application (`apps/finances/importers/rules.py`)

After bulk insert on confirm, fetch all enabled household rules ordered by `priority`. For each uncategorized transaction in the batch, evaluate rules in order; first match wins. Supported matchers (read from `match_json`):

- `payee_contains` — case-insensitive substring
- `memo_contains` — case-insensitive substring
- `amount_gt` / `amount_lt` — decimal comparison

Supported actions (from `action_json`):
- `set_category` — set `category_id`

---

## File Layout

```
backend/apps/finances/importers/
    __init__.py
    parser.py
    dedup.py
    rules.py
backend/apps/finances/
    import_views.py
backend/fixtures/
    import_profiles.json
backend/apps/finances/tests/
    test_import_api.py
    fixtures/
        rbc_sample.csv      (scrubbed copy of real export)
        amex_sample.xls     (scrubbed copy of real export)
```

`import_views.py` registers `PreviewView` and `ConfirmView` as APIViews (not ModelViewSets — they have non-standard request shapes). URLs added to existing `api_urls.py`.

---

## Error Handling

- Unknown profile_id or account_id not in household → 404
- File too large (> 10 MB) → 400
- Profile `file_format` doesn't match uploaded file extension → 400 with hint
- All rows are parse errors → 422 with full error list (no partial import)
- `confirm` called with hashes not from a recent preview of the same file → validated via `file_sha256` match

---

## New Dependencies

- `xlrd` — added to `backend/pyproject.toml` production dependencies for XLS parsing. Already available in the dev environment (added during design exploration). No other new dependencies required; `csv` and `hashlib` are stdlib.

---

## Testing

- Unit tests for `parser.py`: RBC CSV round-trip, Amex XLS round-trip, bad-row skipping, sign convention both directions, dual-currency row
- Unit tests for `dedup.py`: exact match, fuzzy 2-of-3 for each combination, no false positives
- API tests for preview endpoint: happy path, all-duplicate upload, parse errors, wrong profile format
- API tests for confirm endpoint: happy path, rules applied, hash mismatch rejected
- Fixtures: scrubbed `rbc_sample.csv` and `amex_sample.xls` checked into `tests/fixtures/`
