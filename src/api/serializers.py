from rest_framework import serializers

from .models import Account


class AccountSerializer(serializers.ModelSerializer):
    account_id = serializers.IntegerField(source="id")

    class Meta:
        model = Account
        fields = ["created_at", "balance_cents", "settled_balance_cents", "account_id", "status"]


class PaymentCreateRequestSerializer(serializers.Serializer):
    amount_cents = serializers.IntegerField()
    account_id = serializers.IntegerField()
    merchant_name = serializers.CharField(max_length=200, allow_blank=False)

class TransactionCallbackRequestSerializer(serializers.Serializer):
    amount_cents = serializers.IntegerField()
    money_movement_id = serializers.IntegerField()
    status = serializers.CharField(max_length=32, required=False)
