from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from apps.finances.importers.parser import ParsedRow, _normalize_payee
from apps.finances.models import Transaction


@dataclass
class FuzzyMatch:
    parsed_row: ParsedRow
    matched_transaction_id: str
    match_reason: str


def exact_duplicate_hashes(account_id: str, hashes: list[str]) -> set[str]:
    if not hashes:
        return set()
    return set(
        Transaction.objects.filter(
            account_id=account_id,
            import_hash__in=hashes,
        ).values_list("import_hash", flat=True)
    )


def fuzzy_duplicates(account_id: str, rows: list[ParsedRow]) -> list[FuzzyMatch]:
    if not rows:
        return []

    dates = [r.date for r in rows]
    candidates = list(
        Transaction.objects.filter(
            account_id=account_id,
            date__range=(min(dates) - timedelta(days=1), max(dates) + timedelta(days=1)),
        ).values("id", "date", "amount", "payee")
    )

    results: list[FuzzyMatch] = []
    for row in rows:
        for cand in candidates:
            matched: list[str] = []
            if abs((cand["date"] - row.date).days) <= 1:
                matched.append("date")
            if cand["amount"] == row.amount:
                matched.append("amount")
            if cand["payee"] and _normalize_payee(cand["payee"]).lower() == row.payee.lower():
                matched.append("payee")
            if len(matched) >= 2:  # noqa: PLR2004
                results.append(
                    FuzzyMatch(
                        parsed_row=row,
                        matched_transaction_id=str(cand["id"]),
                        match_reason="+".join(matched),
                    )
                )
                break
    return results
