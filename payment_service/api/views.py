import json

import requests
from django.shortcuts import render
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Account, Transaction
from .serializers import AccountSerializer, PaymentCreateRequestSerializer


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
        payload = json.dumps({"amount_cents": trans.amount_cents, "account_id": account.id, "merchant_name": trans.merchant_name, "money_movement_id": trans.id, "time_to_settle_seconds": 10, "ip": trans.id})
        headers = {"Authorization": "Basic YWRtaW46MjNmM2VlMTMtNjM1ZTgxOWI=", "Content-Type": "application/json"}

        # http request failure
        try:
            response = requests.request("POST", url, headers=headers, data=payload)
        except:
            return Response("Failed to call the payment provider", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if response.status_code != 201:
            return Response(response.text, status=response.status_code)

        return Response(serial.data, status=status.HTTP_201_CREATED)
