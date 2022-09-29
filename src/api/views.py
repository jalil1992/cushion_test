import json
from datetime import datetime, timedelta

import pytz
import requests
from django.conf import settings
from django.shortcuts import render
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Account, AccountStatus, Transaction, TransactionStatus
from .serializers import AccountSerializer, PaymentCreateRequestSerializer, TransactionCallbackRequestSerializer


class HomeView(APIView):
    """FBV"""

    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        return Response("OK", status=status.HTTP_200_OK)


class AccountListView(generics.ListAPIView):
    permission_classes = (permissions.AllowAny,)
    pagination_class = None
    serializer_class = AccountSerializer
    queryset = Account.objects.all()


class RecalculateAccountsView(APIView):
    permission_classes = (permissions.AllowAny,)

    def patch(self, request):
        time_to_delinquency_seconds = self.request.query_params.get("time_to_delinquency_seconds", 10)
        try:
            time_to_delinquency_seconds = int(time_to_delinquency_seconds)
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        tz = pytz.timezone(settings.TIME_ZONE)
        current_time = datetime.now(tz)
        delinquent_accounts = Account.objects.exclude(negative_since=None).filter(negative_since__lt=current_time - timedelta(seconds=time_to_delinquency_seconds))
        delinquent_accounts.update(status=AccountStatus.delinquent)
        return Response(status=status.HTTP_200_OK)


class PaymentCreateView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serial = PaymentCreateRequestSerializer(data=request.data)
        if not serial.is_valid():
            return Response(serial.error_messages, status=status.HTTP_400_BAD_REQUEST)

        # ip
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        ip = ""
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")

        # check account
        account = Account.objects.filter(id=serial.data["account_id"]).first()
        if account is None:
            return Response("Unknown account", status=status.HTTP_400_BAD_REQUEST)

        # create transaction
        trans: Transaction = Transaction.objects.create(account=account, amount_cents=serial.data["amount_cents"], merchant_name=serial.data["merchant_name"], ip=ip)

        # call payment provider
        url = "https://bxzggmcc.cushionai.com/money_movement/"
        payload = json.dumps({"amount_cents": trans.amount_cents, "account_id": account.id, "merchant_name": trans.merchant_name, "money_movement_id": trans.id, "time_to_settle_seconds": trans.time_to_settle_seconds, "ip": trans.id})
        headers = {"Authorization": "Basic YWRtaW46MjNmM2VlMTMtNjM1ZTgxOWI=", "Content-Type": "application/json"}

        # http request failure
        try:
            response = requests.request("POST", url, headers=headers, data=payload)
        except:
            return Response("Failed to call the payment provider", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if response.status_code != 201:
            return Response(response.text, status=response.status_code)

        # we increase the account balance
        account.balance_cents += trans.amount_cents
        account.save()

        return Response(serial.data, status=status.HTTP_201_CREATED)


class TransactionCallbackView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serial = TransactionCallbackRequestSerializer(data=request.data)
        if not serial.is_valid():
            return Response(serial.error_messages, status=status.HTTP_400_BAD_REQUEST)

        trans: Transaction = Transaction.objects.filter(id=serial.data["money_movement_id"]).first()
        if trans is None:
            return Response("Unknown transaction", status=status.HTTP_400_BAD_REQUEST)

        # check the time_to_settle_seconds
        tz = pytz.timezone(settings.TIME_ZONE)
        current_time = datetime.now(tz)
        if current_time > trans.created_at + timedelta(seconds=trans.time_to_settle_seconds):
            return Response("Called after settle time limit", status=status.HTTP_406_NOT_ACCEPTABLE)

        # all good, now update the user balance and settled balance
        new_status = serial.data["status"]
        new_settled_amount = serial.data["amount_cents"] if new_status == TransactionStatus.posted else 0

        """
        Update user balance and settled balance:
        We could possibly do summing all amounts on the transaction table with the status filter,
        but this will be a serious performance problem later. So we change account settled balance according to the change
        """
        account = trans.account
        if new_status != trans.status:
            if new_status == TransactionStatus.posted:
                account.settled_balance_cents += new_settled_amount
            else:
                if trans.status == TransactionStatus.posted:
                    account.settled_balance_cents -= trans.settled_amount_cents
        else:
            if new_settled_amount != trans.settled_amount_cents:
                account.settled_balance_cents += new_settled_amount - trans.settled_amount_cents

        # check negative settled balance <- this is the only place where settled balance changes
        if account.settled_balance_cents < 0:
            account.negative_since = current_time
        else:
            account.negative_since = None

        account.save()

        # update the status and amount of the transaction
        trans.settled_amount_cents = new_settled_amount
        trans.status = new_status
        trans.save()

        return Response(serial.data, status=status.HTTP_201_CREATED)  # 201 does not make sense here
