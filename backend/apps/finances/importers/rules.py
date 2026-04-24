from __future__ import annotations

from decimal import Decimal

from apps.finances.models import Rule, Transaction


def apply_rules(transaction_ids: list[str], household_id: str) -> int:
    rules = list(Rule.objects.filter(household_id=household_id, enabled=True).order_by("priority"))
    if not rules:
        return 0

    transactions = list(
        Transaction.objects.filter(id__in=transaction_ids, category_id__isnull=True)
    )
    to_save = []
    for txn in transactions:
        for rule in rules:
            if _matches(txn, rule.match_json):
                category_id = rule.action_json.get("set_category")
                if category_id:
                    txn.category_id = category_id
                    to_save.append(txn)
                    break

    if to_save:
        Transaction.objects.bulk_update(to_save, ["category_id"])
    return len(to_save)


def _matches(txn: Transaction, match_json: dict) -> bool:
    if "payee_contains" in match_json:
        if match_json["payee_contains"].lower() not in (txn.payee or "").lower():
            return False
    if "memo_contains" in match_json:
        if match_json["memo_contains"].lower() not in (txn.memo or "").lower():
            return False
    if "amount_gt" in match_json:
        if not (txn.amount > Decimal(str(match_json["amount_gt"]))):
            return False
    if "amount_lt" in match_json:
        if not (txn.amount < Decimal(str(match_json["amount_lt"]))):
            return False
    return True
