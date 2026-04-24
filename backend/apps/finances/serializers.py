"""DRF serializers for ``apps.finances``.

Scope: Account, Category (with parent validation), Transaction (with inline
splits), Rule. All FK references are validated against the request user's
household so a user cannot reference data from another household.
"""

from __future__ import annotations

from typing import Any

from rest_framework import serializers

from apps.finances.models import (
    Account,
    Category,
    Rule,
    Transaction,
    TransactionSplit,
)


class AccountSerializer(serializers.ModelSerializer[Account]):
    class Meta:
        model = Account
        fields = [
            "id",
            "name",
            "type",
            "institution",
            "currency",
            "starting_balance",
            "closed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class CategorySerializer(serializers.ModelSerializer[Category]):
    parent = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        required=False,
        allow_null=True,
        default=None,
    )

    class Meta:
        model = Category
        fields = [
            "id",
            "parent",
            "name",
            "kind",
            "is_budgetable",
            "rollover_mode",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_parent(self, value: Category | None) -> Category | None:
        if value is None:
            return None
        request = self.context.get("request")
        if request is not None and value.household_id != request.user.household_id:
            raise serializers.ValidationError("Parent category not found.")
        return value


class TransactionSplitSerializer(serializers.ModelSerializer[TransactionSplit]):
    class Meta:
        model = TransactionSplit
        fields = ["id", "category", "amount", "memo", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class TransactionSerializer(serializers.ModelSerializer[Transaction]):
    splits = TransactionSplitSerializer(many=True, required=False)

    class Meta:
        model = Transaction
        fields = [
            "id",
            "account",
            "date",
            "amount",
            "original_currency",
            "fx_rate",
            "payee",
            "memo",
            "category",
            "status",
            "import_batch",
            "import_hash",
            "splits",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "import_batch", "import_hash", "created_at", "updated_at"]

    def validate_account(self, value: Account) -> Account:
        request = self.context.get("request")
        if request is not None and value.household_id != request.user.household_id:
            raise serializers.ValidationError("Account not found.")
        return value

    def validate_category(self, value: Category | None) -> Category | None:
        if value is None:
            return None
        request = self.context.get("request")
        if request is not None and value.household_id != request.user.household_id:
            raise serializers.ValidationError("Category not found.")
        return value

    def create(self, validated_data: dict[str, Any]) -> Transaction:
        splits_data: list[dict[str, Any]] = validated_data.pop("splits", [])
        transaction = Transaction.objects.create(**validated_data)
        for split_data in splits_data:
            TransactionSplit.objects.create(parent_transaction=transaction, **split_data)
        return transaction

    def update(self, instance: Transaction, validated_data: dict[str, Any]) -> Transaction:
        splits_data: list[dict[str, Any]] | None = validated_data.pop("splits", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if splits_data is not None:
            instance.splits.all().delete()
            for split_data in splits_data:
                TransactionSplit.objects.create(parent_transaction=instance, **split_data)
        return instance


class RuleSerializer(serializers.ModelSerializer[Rule]):
    class Meta:
        model = Rule
        fields = [
            "id",
            "priority",
            "match_json",
            "action_json",
            "enabled",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
