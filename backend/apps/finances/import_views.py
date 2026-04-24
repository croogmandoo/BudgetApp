from __future__ import annotations

import re
import uuid
from typing import cast

from django.db import transaction as db_transaction
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.core.permissions import IsTOTPVerifiedHouseholdMember
from apps.finances.importers.dedup import exact_duplicate_hashes, fuzzy_duplicates
from apps.finances.importers.parser import parse_file
from apps.finances.importers.rules import apply_rules
from apps.finances.models import Account, ImportBatch, ImportProfile, Transaction

MAX_FILE_BYTES = 10 * 1024 * 1024

_IMPORT_HASH_RE = re.compile(r"^[0-9a-f]{64}$")


def _household_id(request: Request) -> uuid.UUID:
    return cast(uuid.UUID, cast(User, request.user).household_id)


class ImportPreviewView(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [IsTOTPVerifiedHouseholdMember]

    def post(self, request: Request) -> Response:
        account_id = request.data.get("account_id")
        profile_id = request.data.get("profile_id")
        file_obj = request.FILES.get("file")
        if not all([account_id, profile_id, file_obj]):
            return Response(
                {"detail": "account_id, profile_id, and file are required."}, status=400
            )

        hh = _household_id(request)
        try:
            account = Account.objects.get(id=account_id, household_id=hh)
        except Account.DoesNotExist:
            return Response({"detail": "Account not found."}, status=404)
        try:
            profile = ImportProfile.objects.get(id=profile_id, household_id=hh)
        except ImportProfile.DoesNotExist:
            return Response({"detail": "Import profile not found."}, status=404)

        file_size = getattr(file_obj, "size", None)
        if file_size is not None and file_size > MAX_FILE_BYTES:
            return Response({"detail": "File exceeds 10 MB limit."}, status=400)

        ext = file_obj.name.rsplit(".", 1)[-1].lower() if "." in file_obj.name else ""
        fmt = profile.mapping_json.get("file_format", "csv")
        if (fmt == "csv" and ext != "csv") or (fmt == "xls" and ext not in ("xls", "xlsx")):
            return Response(
                {"detail": f"Profile expects {fmt} but uploaded file is .{ext}."}, status=400
            )

        result = parse_file(file_obj, profile, str(account.id))
        all_hashes = [r.import_hash for r in result.rows]
        exact_dupes = exact_duplicate_hashes(str(account.id), all_hashes)
        non_exact = [r for r in result.rows if r.import_hash not in exact_dupes]
        fuzzy = fuzzy_duplicates(str(account.id), non_exact)
        fuzzy_hash_map = {fm.parsed_row.import_hash: fm for fm in fuzzy}

        to_import, exact_out, probable_out = [], [], []
        for row in result.rows:
            d = {
                "row": row.row_num,
                "date": row.date.isoformat(),
                "amount": str(row.amount),
                "payee": row.payee,
                "memo": row.memo,
                "original_currency": row.original_currency,
                "fx_rate": str(row.fx_rate) if row.fx_rate else None,
                "import_hash": row.import_hash,
            }
            if row.import_hash in exact_dupes:
                exact_out.append(d)
            elif row.import_hash in fuzzy_hash_map:
                fm = fuzzy_hash_map[row.import_hash]
                probable_out.append({
                    **d,
                    "matched_transaction_id": fm.matched_transaction_id,
                    "match_reason": fm.match_reason,
                })
            else:
                to_import.append(d)

        return Response({
            "profile_name": profile.institution,
            "total_rows": len(result.rows),
            "to_import": to_import,
            "exact_duplicates": exact_out,
            "probable_duplicates": probable_out,
            "parse_errors": [
                {"row": e.row_num, "reason": e.reason} for e in result.parse_errors
            ],
        })


class ImportConfirmView(APIView):
    permission_classes = [IsTOTPVerifiedHouseholdMember]

    def post(self, request: Request) -> Response:
        data = request.data
        account_id = data.get("account_id")
        profile_id = data.get("profile_id")
        filename = data.get("filename", "")
        file_sha256 = data.get("file_sha256", "")
        transactions = data.get("transactions", [])

        if not all([account_id, profile_id, transactions]):
            return Response(
                {"detail": "account_id, profile_id, and transactions are required."}, status=400
            )

        hh = _household_id(request)
        try:
            account = Account.objects.get(id=account_id, household_id=hh)
        except Account.DoesNotExist:
            return Response({"detail": "Account not found."}, status=404)
        try:
            ImportProfile.objects.get(id=profile_id, household_id=hh)
        except ImportProfile.DoesNotExist:
            return Response({"detail": "Import profile not found."}, status=404)

        user = cast(User, request.user)
        incoming_hashes = []
        validated = []
        for i, t in enumerate(transactions):
            h = t.get("import_hash", "")
            if not isinstance(h, str) or not _IMPORT_HASH_RE.match(h):
                return Response(
                    {"detail": f"transactions[{i}]: invalid or missing import_hash"},
                    status=400,
                )
            date_val = t.get("date")
            amount_val = t.get("amount")
            if not date_val or not amount_val:
                return Response(
                    {"detail": f"transactions[{i}]: date and amount are required"},
                    status=400,
                )
            try:
                from decimal import Decimal as _D
                _D(str(amount_val))
            except Exception:
                return Response(
                    {"detail": f"transactions[{i}]: invalid amount '{amount_val}'"},
                    status=400,
                )
            incoming_hashes.append(h)
            validated.append(t)

        already = exact_duplicate_hashes(str(account.id), incoming_hashes)
        to_create = [t for t in validated if t["import_hash"] not in already]

        with db_transaction.atomic():
            batch = ImportBatch.objects.create(
                account=account,
                user=user,
                filename=filename,
                sha256=file_sha256,
                row_count=len(to_create),
            )
            new_txns = Transaction.objects.bulk_create([
                Transaction(
                    account=account,
                    date=t["date"],
                    amount=t["amount"],
                    payee=t.get("payee", ""),
                    memo=t.get("memo", ""),
                    original_currency=t.get("original_currency", ""),
                    fx_rate=t.get("fx_rate") or None,
                    import_hash=t["import_hash"],
                    import_batch=batch,
                )
                for t in to_create
            ])

        txn_ids = [str(t.id) for t in new_txns]
        try:
            rules_applied = apply_rules(txn_ids, str(hh))
        except Exception:
            rules_applied = 0

        return Response(
            {
                "batch_id": str(batch.id),
                "imported": len(new_txns),
                "rules_applied": rules_applied,
                "skipped_duplicates": len(already),
            },
            status=status.HTTP_201_CREATED,
        )
